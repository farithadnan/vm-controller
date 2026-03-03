import os
import hmac
import json
import hashlib
import subprocess
import base64
from typing import Optional, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Windows DPAPI for encryption
try:
    import win32crypt  # type: ignore
except ImportError:
    win32crypt = None


# ==============================
#  Credentials Manager
# ==============================
class CredentialsManager:
    """Manage encrypted credentials storage using Windows DPAPI."""

    def __init__(self, creds_file: str = "config/credentials.dat"):
        # Ensure config directory exists
        os.makedirs(os.path.dirname(creds_file), exist_ok=True)
        self.creds_file = creds_file

    def encrypt_data(self, data: str) -> str:
        """Encrypt data using Windows DPAPI."""
        if win32crypt is None:
            # Fallback: base64 encoding (not secure, but works without pywin32)
            return base64.b64encode(data.encode()).decode()

        encrypted = win32crypt.CryptProtectData(
            data.encode('utf-8'),
            'VM Controller Credentials',
            None, None, None, 0
        )
        return base64.b64encode(encrypted).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using Windows DPAPI."""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())

            if win32crypt is None:
                # Fallback: base64 decoding
                return encrypted_bytes.decode()

            _, decrypted = win32crypt.CryptUnprotectData(
                encrypted_bytes, None, None, None, 0
            )
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {e}")

    def save_credentials(self, api_key: str, hmac_secret: str, allow_ips: list):
        """Save encrypted credentials to file."""
        credentials = {
            'api_key': api_key,
            'hmac_secret': hmac_secret,
            'allow_ips': allow_ips,
            'created_at': datetime.now(timezone.utc).isoformat()
        }

        json_data = json.dumps(credentials)
        encrypted = self.encrypt_data(json_data)

        with open(self.creds_file, 'w') as f:
            f.write(encrypted)

    def load_credentials(self) -> dict:
        """Load and decrypt credentials from file."""
        if not os.path.exists(self.creds_file):
            return None

        try:
            with open(self.creds_file, 'r') as f:
                encrypted = f.read()

            json_data = self.decrypt_data(encrypted)
            return json.loads(json_data)
        except Exception as e:
            print(f"Warning: Could not load credentials: {e}")
            return None

    def credentials_exist(self) -> bool:
        """Check if credentials file exists."""
        return os.path.exists(self.creds_file)


# ==============================
#  Configuration Class
# ==============================
class Config:
    """Configuration management class."""
    def __init__(self, creds_manager: Optional[CredentialsManager] = None):
        # Try .env first (for development)
        load_dotenv()

        self.api_key = os.getenv("API_KEY")
        self.hmac_secret = os.getenv("HMAC_SECRET")
        allow_ip_raw = os.getenv("ALLOW_IP", "")

        # If .env doesn't have credentials, try encrypted storage
        if not self.api_key and creds_manager:
            creds = creds_manager.load_credentials()
            if creds:
                self.api_key = creds['api_key']
                self.hmac_secret = creds['hmac_secret']
                self.allow_ip = creds['allow_ips']
            else:
                raise ValueError("No credentials found")
        else:
            # Support comma-separated IPs from .env
            self.allow_ip = [ip.strip() for ip in allow_ip_raw.split(",") if ip.strip()] if allow_ip_raw else []

        self.log_dir = "logs"

        self._validate()
        self._ensure_log_dir()

    def _validate(self):
        """Validate required configuration."""
        if not self.api_key:
            raise ValueError("API_KEY must be set in .env file")
        if not self.hmac_secret:
            raise ValueError("HMAC_SECRET must be set in .env file")

    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist."""
        os.makedirs(self.log_dir, exist_ok=True)

    @property
    def audit_log_path(self) -> str:
        return f"{self.log_dir}/audit.log"

    @property
    def app_log_path(self) -> str:
        return f"{self.log_dir}/app.log"


# ==============================
#  Log Manager Class
# ==============================
class LogManager:
    """Manages all logging operations."""

    def __init__(self, config: Config):
        self.config = config

    def write_audit(self, action: str, vm: str, ip: str, status: str, details: str = ""):
        """Write audit log entry for VM operations."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "vm": vm,
            "client_ip": ip,
            "status": status,
            "details": details,
        }
        self._write_to_file(self.config.audit_log_path, log_entry)

    def write_app_log(self, data: dict):
        """Write application log entry."""
        if "timestamp" not in data:
            data["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._write_to_file(self.config.app_log_path, data)

    def log_request_entry(self, request: Request, status: str = "received", details: str = ""):
        """Log request at entry point before any verification."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
            "status": status,
            "details": details,
        }
        self._write_to_file(self.config.app_log_path, log_entry)

    def get_history(self, vm_name: Optional[str] = None, limit: int = 10) -> List[dict]:
        """Read audit log history."""
        try:
            with open(self.config.audit_log_path, "r", encoding="utf-8") as f:
                logs = [json.loads(line) for line in f if line.strip()]

            # Filter by VM if specified
            if vm_name:
                logs = [log for log in logs if log.get("vm") == vm_name]

            # Return most recent entries
            return logs[-limit:][::-1]  # Reverse to show newest first
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error reading history: {e}")
            return []

    def _write_to_file(self, filepath: str, data: dict):
        """Private method to write JSON to file."""
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")


# ==============================
#  Hyper-V Manager Class
# ==============================
class HyperVManager:
    """Manages Hyper-V virtual machine operations."""

    def __init__(self):
        pass

    def get_all_vm_names(self) -> List[str]:
        """Get list of all VM names from Hyper-V."""
        # Optimized: (Get-VM).Name is much faster than piping
        result = self._run_powershell("(Get-VM).Name")
        if not result or "Error:" in result:
            return []
        return [vm.strip() for vm in result.splitlines() if vm.strip()]

    def get_vm_state(self, vm_name: str) -> dict:
        """Get VM state information."""
        # Optimized state retrieval
        state_cmd = f'(Get-VM -Name "{vm_name}").State.ToString()'
        state = self._run_powershell(state_cmd)

        if "Error:" in state:
            state = "Unknown"

        return {
            "vm_name": vm_name,
            "state": state
        }

    def get_vm_details(self, vm_name: str) -> dict:
        """Get detailed VM information."""
        # Optimized comprehensive VM details command
        details_cmd = f'''
        $vm = Get-VM -Name "{vm_name}"
        $vmInfo = @{{
            State = $vm.State.ToString()
            CPUUsage = $vm.CPUUsage
            MemoryAssigned = [math]::Round($vm.MemoryAssigned / 1GB, 2)
            MemoryDemand = [math]::Round($vm.MemoryDemand / 1GB, 2)
            Uptime = $vm.Uptime.ToString()
            ProcessorCount = $vm.ProcessorCount
            Generation = $vm.Generation.ToString()
        }}
        $vmInfo | ConvertTo-Json
        '''

        result = self._run_powershell(details_cmd)

        try:
            if "Error:" in result:
                raise ValueError(result)

            details = json.loads(result)

            # Get network adapter info (IP address) - this can be slow, adding separate try/catch
            ip_address = "Not available"
            try:
                ip_cmd = f'(Get-VMNetworkAdapter -VMName "{vm_name}").IPAddresses[0]'
                ip_result = self._run_powershell(ip_cmd, timeout=10)
                if ip_result and "Error:" not in ip_result:
                    ip_address = ip_result.strip()
            except:
                pass

            return {
                "vm_name": vm_name,
                "state": details.get("State", "Unknown"),
                "cpu": f"{details.get('ProcessorCount', 'N/A')} cores",
                "cpu_usage": f"{details.get('CPUUsage', 0)}%",
                "memory": f"{details.get('MemoryAssigned', 0)} GB",
                "memory_demand": f"{details.get('MemoryDemand', 0)} GB",
                "uptime": details.get("Uptime", "N/A"),
                "generation": details.get("Generation", "N/A"),
                "ip_address": ip_address
            }
        except Exception as e:
            # Fallback to basic info if anything fails
            state_info = self.get_vm_state(vm_name)
            return {
                "vm_name": vm_name,
                "state": state_info.get("state", "Unknown"),
                "details": f"Extended details unavailable: {str(e)}"
            }

    def validate_vm_exists(self, vm_name: str) -> bool:
        """Check if a VM exists."""
        # Using specific Get-VM name check is faster than listing all
        check_cmd = f'if (Get-VM -Name "{vm_name}" -ErrorAction SilentlyContinue) {{ "True" }} else {{ "False" }}'
        exists = self._run_powershell(check_cmd)

        if exists.strip() != "True":
            vm_list = self.get_all_vm_names()
            raise HTTPException(
                status_code=404,
                detail=f"VM '{vm_name}' not found. Available VMs: {', '.join(vm_list)}"
            )
        return True

    def start_vm(self, vm_name: str) -> str:
        """Start a virtual machine."""
        return self._run_powershell(f'Start-VM -Name "{vm_name}"', force_no_confirm=True)

    def stop_vm(self, vm_name: str) -> str:
        """Stop (shutdown) a virtual machine."""
        return self._run_powershell(f'Stop-VM -Name "{vm_name}" -Force', force_no_confirm=True)

    def restart_vm(self, vm_name: str) -> str:
        """Restart a virtual machine."""
        return self._run_powershell(f'Restart-VM -Name "{vm_name}" -Force', force_no_confirm=True)

    def _run_powershell(self, cmd: str, force_no_confirm: bool = False, timeout: int = 45) -> str:
        """Execute PowerShell commands safely with a timeout."""
        full_cmd = cmd
        if force_no_confirm:
            full_cmd = f"{cmd} -Confirm:$false"

        try:
            # Added -NonInteractive and timeout to prevent hangs
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", full_cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout.strip() or result.stderr.strip()
            return output
        except subprocess.TimeoutExpired:
            return f"Error: PowerShell command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {str(e)}"


# ==============================
#  Security Validator Class
# ==============================
class SecurityValidator:
    """Handles all security validation logic."""

    def __init__(self, config: Config):
        self.config = config

    def verify_api_key(self, x_api_key: Optional[str]):
        """Verify API key from request header."""
        if not x_api_key or not hmac.compare_digest(x_api_key, self.config.api_key):
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key")

    def verify_hmac_signature(self, signature: Optional[str], timestamp: Optional[str], raw_body: bytes):
        """Verify HMAC-SHA256 signature."""
        if not self.config.hmac_secret:
            return  # HMAC disabled

        if not signature or not timestamp:
            raise HTTPException(
                status_code=401,
                detail="Missing signature: x-signature and x-timestamp headers required"
            )

        # Ensure body is treated as empty bytes if None
        message = (raw_body or b'') + timestamp.encode()
        expected = hmac.new(
            self.config.hmac_secret.encode(),
            message,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise HTTPException(
                status_code=401,
                detail="Invalid HMAC signature: Request may be tampered"
            )

    def verify_ip(self, client_ip: str) -> bool:
        """Verify client IP against whitelist (supports multiple IPs)."""
        if self.config.allow_ip:  # If whitelist is configured
            if client_ip not in self.config.allow_ip:
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: IP {client_ip} not in allowed list"
                )
        return True

    async def verify_authentication(
        self,
        x_api_key: Optional[str] = Header(None),
        x_signature: Optional[str] = Header(None),
        x_timestamp: Optional[str] = Header(None),
        request: Request = None
    ):
        """
        Complete authentication verification.
        Combines API key and HMAC signature validation.
        """
        self.verify_api_key(x_api_key)

        raw_body = await request.body()
        self.verify_hmac_signature(x_signature, x_timestamp, raw_body)

        return True


# ==============================
#  Middleware Class
# ==============================
class IPVerificationMiddleware(BaseHTTPMiddleware):
    """Middleware to verify IP and log all requests at entry point."""

    def __init__(self, app, log_manager: LogManager, security_validator: SecurityValidator):
        super().__init__(app)
        self.log_manager = log_manager
        self.security_validator = security_validator

    async def dispatch(self, request: Request, call_next):
        # Log request at entry point
        self.log_manager.log_request_entry(
            request,
            "received",
            f"Headers: {dict(request.headers)}"
        )

        # Verify IP if configured
        try:
            self.security_validator.verify_ip(request.client.host)
        except HTTPException as e:
            self.log_manager.log_request_entry(
                request,
                "rejected",
                f"IP {request.client.host} not in whitelist"
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )

        # Process request
        response = await call_next(request)
        return response


# ==============================
#  Initialize FastAPI app
# ==============================
app = FastAPI(
    title="VM Controller API",
    description="Remote control for Hyper-V virtual machines with state monitoring",
    version="3.1.0",
    lifespan=None
)


# ==============================
#  Initialize Components
# ==============================
config = None
log_manager = None
hyperv_manager = None
security_validator = None

def initialize_components(creds_manager: Optional[CredentialsManager] = None):
    """Initialize global components."""
    global config, log_manager, hyperv_manager, security_validator
    config = Config(creds_manager=creds_manager)
    log_manager = LogManager(config)
    hyperv_manager = HyperVManager()
    security_validator = SecurityValidator(config)

    # Add middleware after components are initialized
    if not any(isinstance(m, IPVerificationMiddleware) for m in app.user_middleware):
        app.add_middleware(
            IPVerificationMiddleware,
            log_manager=log_manager,
            security_validator=security_validator
        )

# Try to initialize with .env if available
if os.path.exists(".env"):
    initialize_components()


# ==============================
#  Authentication Dependency
# ==============================
async def verify_authentication(
    x_api_key: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None),
    request: Request = None
):
    """FastAPI Dependency for authentication."""
    return await security_validator.verify_authentication(
        x_api_key, x_signature, x_timestamp, request
    )


# ==============================
#  Lifespan Event Handler
# ==============================
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Handle startup and shutdown events."""
    print("=" * 60)
    print("VM Controller API Started (Enhanced Version)")
    print("=" * 60)
    print(f"API Key configured: {'✓' if config.api_key else '✗'}")
    print(f"HMAC Secret configured: {'✓' if config.hmac_secret else '✗'}")
    print(f"IP Whitelisting: {'Enabled (' + ', '.join(config.allow_ip) + ')' if config.allow_ip else 'Disabled'}")
    print(f"Logging directory: {config.log_dir}")

    try:
        vms = hyperv_manager.get_all_vm_names()
        print(f"✓ Hyper-V access verified - {len(vms)} VMs found")
        if vms:
            print(f"  Available VMs: {', '.join(vms)}")
    except Exception as e:
        print(f"✗ Hyper-V access error: {e}")

    print("=" * 60)
    print("NEW ENDPOINTS AVAILABLE:")
    print("  • GET  /vm/{vm_name}/state    - Get VM state")
    print("  • GET  /vm/{vm_name}/details  - Get VM details")
    print("  • GET  /vm/history            - Get action history")
    print("  • GET  /vm/{vm_name}/history  - Get VM-specific history")
    print("=" * 60)
    yield

app.router.lifespan_context = lifespan


# ==============================
#  API ENDPOINTS (Optimized: Removed 'async' from blocking calls)
# ==============================
@app.get("/")
def root(request: Request):
    return {
        "service": "VM Controller API",
        "version": "3.1.0",
        "status": "running"
    }

@app.get("/health")
def health_check(request: Request):
    try:
        vms = hyperv_manager.get_all_vm_names()
        return {
            "status": "healthy",
            "vm_count": len(vms),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/vm/list")
def list_vms(
    request: Request,
    authenticated: bool = Depends(verify_authentication)
):
    """List all VMs (Synchronous for threadpool handling)."""
    try:
        vms = hyperv_manager.get_all_vm_names()
        log_manager.write_app_log({
            "action": "list",
            "client_ip": request.client.host,
            "status": "success",
            "result": vms
        })
        return {"vms": vms}
    except Exception as e:
        log_manager.write_app_log({
            "action": "list",
            "client_ip": request.client.host,
            "status": "error",
            "details": str(e)
        })
        raise HTTPException(status_code=500, detail=f"Failed to list VMs: {str(e)}")

@app.get("/vm/{vm_name}/state")
def get_vm_state(
    vm_name: str,
    request: Request,
    authenticated: bool = Depends(verify_authentication)
):
    """Get VM state (Synchronous for threadpool handling)."""
    try:
        hyperv_manager.validate_vm_exists(vm_name)
        state_info = hyperv_manager.get_vm_state(vm_name)

        log_manager.write_app_log({
            "action": "get_state",
            "vm": vm_name,
            "client_ip": request.client.host,
            "status": "success",
            "state": state_info["state"]
        })

        return state_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vm/{vm_name}/details")
def get_vm_details(
    vm_name: str,
    request: Request,
    authenticated: bool = Depends(verify_authentication)
):
    """Get detailed VM info (Synchronous for threadpool handling)."""
    try:
        hyperv_manager.validate_vm_exists(vm_name)
        return hyperv_manager.get_vm_details(vm_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vm/history")
def get_all_history(
    request: Request,
    limit: int = 10,
    authenticated: bool = Depends(verify_authentication)
):
    history = log_manager.get_history(vm_name=None, limit=limit)
    formatted_history = []
    for entry in history:
        formatted_history.append({
            "timestamp": entry.get("timestamp", "N/A"),
            "user": entry.get("client_ip", "Unknown"),
            "action": entry.get("action", "unknown"),
            "vm_name": entry.get("vm", "N/A"),
            "success": entry.get("status") == "ok"
        })
    return {"history": formatted_history}

@app.post("/vm/{vm_name}/shutdown")
def shutdown_vm(
    vm_name: str,
    request: Request,
    authenticated: bool = Depends(verify_authentication)
):
    try:
        hyperv_manager.validate_vm_exists(vm_name)
        output = hyperv_manager.stop_vm(vm_name)
        log_manager.write_audit("shutdown", vm_name, request.client.host, "ok", output)
        return {"vm": vm_name, "action": "shutdown", "output": output, "status": "success"}
    except Exception as e:
        log_manager.write_audit("shutdown", vm_name, request.client.host, "error", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vm/{vm_name}/start")
def start_vm(
    vm_name: str,
    request: Request,
    authenticated: bool = Depends(verify_authentication)
):
    try:
        hyperv_manager.validate_vm_exists(vm_name)
        output = hyperv_manager.start_vm(vm_name)
        log_manager.write_audit("start", vm_name, request.client.host, "ok", output)
        return {"vm": vm_name, "action": "start", "output": output, "status": "success"}
    except Exception as e:
        log_manager.write_audit("start", vm_name, request.client.host, "error", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vm/{vm_name}/restart")
def restart_vm(
    vm_name: str,
    request: Request,
    authenticated: bool = Depends(verify_authentication)
):
    try:
        hyperv_manager.validate_vm_exists(vm_name)
        output = hyperv_manager.restart_vm(vm_name)
        log_manager.write_audit("restart", vm_name, request.client.host, "ok", output)
        return {"vm": vm_name, "action": "restart", "output": output, "status": "success"}
    except Exception as e:
        log_manager.write_audit("restart", vm_name, request.client.host, "error", str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import sys

    def get_version() -> str:
        """Get version from bundled or source version file."""
        try:
            if hasattr(sys, '_MEIPASS'):
                version_file = os.path.join(sys._MEIPASS, 'version.txt')
            else:
                version_file = os.path.join(os.path.dirname(__file__), 'deploy', 'version.txt')

            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception:
            pass
        return "1.0.0"

    def interactive_setup(creds_manager: CredentialsManager) -> dict:
        """Interactive setup to collect credentials on first run."""
        print("\n" + "=" * 70)
        print("VM CONTROLLER - FIRST-TIME SETUP")
        print("=" * 70)
        print("\nWelcome! Let's configure your VM Controller API.\n")
        print("Your credentials will be encrypted and stored securely using")
        print("Windows Data Protection API (DPAPI).\n")
        print("=" * 70 + "\n")

        print("[1] API KEY")
        print("-" * 70)
        print("This key is used to authenticate API requests.")
        print("Recommended: Leave empty to generate a secure random key.\n")
        api_key = input("Enter API_KEY (or press Enter for auto-generate): ").strip()
        if not api_key:
            import secrets
            api_key = secrets.token_hex(32)
            print(f"✓ Generated: {api_key}\n")
        else:
            print(f"✓ Using your key: {api_key}\n")

        print("[2] HMAC SECRET")
        print("-" * 70)
        print("This secret is used to sign and verify requests.")
        print("Recommended: Leave empty to generate a secure random secret.\n")
        hmac_secret = input("Enter HMAC_SECRET (or press Enter for auto-generate): ").strip()
        if not hmac_secret:
            import secrets
            hmac_secret = secrets.token_hex(32)
            print(f"✓ Generated: {hmac_secret}\n")
        else:
            print(f"✓ Using your secret: {hmac_secret}\n")

        print("[3] IP WHITELIST")
        print("-" * 70)
        print("Restrict API access to specific IP addresses (optional).\n")
        print("Examples:")
        print("  • Single IP:    192.168.1.10")
        print("  • Multiple IPs: 192.168.1.10,192.168.1.20,10.0.0.5")
        print("  • All IPs:      Leave empty (not recommended for production)\n")
        allow_ip_input = input("Enter allowed IPs (comma-separated or empty): ").strip()

        allow_ips = [ip.strip() for ip in allow_ip_input.split(",") if ip.strip()]

        if allow_ips:
            print(f"[OK] Allowed IPs: {', '.join(allow_ips)}\n")
        else:
            print("[WARNING] All IPs are allowed (any IP can access the API)\n")

        print("=" * 70)
        print("SAVING CONFIGURATION")
        print("=" * 70)
        print("\nEncrypting and saving credentials...")

        try:
            creds_manager.save_credentials(api_key, hmac_secret, allow_ips)
            print("[SUCCESS] Credentials saved successfully!\n")
        except Exception as e:
            print(f"[ERROR] Error saving credentials: {e}\n")
            input("Press Enter to exit...")
            sys.exit(1)

        print("=" * 70)
        print("CONFIGURATION SUMMARY")
        print("=" * 70)
        print(f"\n  API_KEY:     {api_key}")
        print(f"  HMAC_SECRET: {hmac_secret}")
        if allow_ips:
            print(f"  ALLOWED_IPS: {', '.join(allow_ips)}")
        else:
            print(f"  ALLOWED_IPS: (all IPs allowed)")
        print("\n" + "=" * 70)
        print("[IMPORTANT] Save these credentials in a secure location!")
        print("=" * 70)
        print("\nYour credentials are encrypted in: config/credentials.dat")
        print("This file is tied to your Windows user account.")
        print("\nTo reset credentials: Delete config/credentials.dat and restart.\n")
        print("=" * 70)
        input("\nPress Enter to continue...")

        return {
            'api_key': api_key,
            'hmac_secret': hmac_secret,
            'allow_ips': allow_ips
        }

    try:
        version = get_version()
        print("=" * 70)
        print(f"VM CONTROLLER API v{version}")
        print("=" * 70)
        print(f"Working directory: {os.getcwd()}")

        creds_manager = CredentialsManager()

        if not creds_manager.credentials_exist() and not os.path.exists(".env"):
            print("\n[WARNING] No credentials found. Starting first-time setup...\n")
            interactive_setup(creds_manager)
            print("\n[OK] Setup complete!")
        elif creds_manager.credentials_exist():
            print("[OK] Encrypted credentials found (config/credentials.dat)")
        elif os.path.exists(".env"):
            print("[OK] Configuration file found (.env)")
        else:
            print("[WARNING] No credentials found (.env or encrypted credentials missing)")

        print("\nChecking Hyper-V availability...")
        test_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Command Get-VM"],
            capture_output=True,
            text=True
        )

        if test_result.returncode != 0:
            print("[WARNING] Hyper-V PowerShell module not found")
            print("          API will start, but VM operations may fail")
        else:
            print("[OK] Hyper-V PowerShell module available")

        print("\n" + "=" * 70)
        print("Starting API server...")
        print("=" * 70)
        print("\n  URL:  http://0.0.0.0:8000")
        print("  Docs: http://localhost:8000/docs")
        print("\n  Press CTRL+C to stop")
        print("=" * 70 + "\n")

        initialize_components(creds_manager=creds_manager)
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Server stopped by user")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print("[FATAL ERROR]")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print(f"Type: {type(e).__name__}")
        print("=" * 70)
