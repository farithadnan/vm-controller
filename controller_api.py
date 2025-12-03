import os
import hmac
import json
import hashlib
import subprocess
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Request


# ==============================
#  Load environment variables
# ==============================
load_dotenv()
API_KEY = os.getenv("API_KEY")
HMAC_SECRET = os.getenv("HMAC_SECRET")
ALLOW_IP = os.getenv("ALLOW_IP")

if not API_KEY:
    raise ValueError("API_KEY must be set in .env file")
if not HMAC_SECRET:
    raise ValueError("HMAC_SECRET must be set in .env file")

app = FastAPI(
    title="VM Controller API",
    description="Remote control for Hyper-V virtual machines",
    version="1.0.0"
)

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

AUDIT_LOG_FILE = f"{LOG_DIR}/audit.log"
APP_LOG_FILE = f"{LOG_DIR}/app.log"


# ==============================
#  Logging utilities
# ==============================
def write_audit(action: str, vm: str, ip: str, status: str, details: str = ""):
    """Write audit log entry."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "vm": vm,
        "client_ip": ip,
        "status": status,
        "details": details,
    }
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


def write_json_log(data: dict):
    """Write application log entry."""
    with open(APP_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")

# ==============================
#  Helper to run PowerShell (no prompts)
# ==============================
def run_powershell(cmd: str, force_no_confirm: bool = False) -> str:
    """
    Runs PowerShell commands safely.
    If force_no_confirm=True, append -Confirm:$false to commands that support it.
    """
    full_cmd = cmd
    if force_no_confirm:
        full_cmd = f"{cmd} -Confirm:$false"

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", full_cmd],
        capture_output=True,
        text=True
    )

    output = result.stdout.strip() or result.stderr.strip()
    return output


# ==============================
#  Get VM List
# ==============================
def get_all_vm_names() -> list:
    """Get list of all VM names from Hyper-V."""
    result = run_powershell("Get-VM | Select-Object -ExpandProperty Name")
    if not result:
        return []
    return [vm.strip() for vm in result.splitlines() if vm.strip()]


# ==============================
#  Verify API key
# ==============================
def verify_key(x_api_key: Optional[str]):
    """Verify API key from request header."""
    if not x_api_key or not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API key")


# ==============================
#  Verify IP (optional)
# ==============================
def verify_ip(request: Request):
    """Verify client IP address if ALLOW_IP is configured."""
    if ALLOW_IP:
        client_ip = request.client.host
        if client_ip != ALLOW_IP:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: IP {client_ip} not allowed"
            )


# ==============================
#  Verify HMAC signature
# ==============================
def verify_hmac_signature(signature: Optional[str], timestamp: Optional[str], raw_body: bytes):
    """
    Verify HMAC-SHA256 signature.
    signature = hex(HMAC_SHA256(secret, raw_body + timestamp))
    """
    if not HMAC_SECRET:
        return  # HMAC disabled

    if not signature or not timestamp:
        raise HTTPException(
            status_code=401,
            detail="Missing signature: x-signature and x-timestamp headers required"
        )

    message = raw_body + timestamp.encode()
    expected = hmac.new(
        HMAC_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid HMAC signature: Request may be tampered"
        )


# ==============================
#  Verify VM exists
# ==============================
def validate_vm(vm_name: str):
    """Verify that VM exists."""
    vm_list = get_all_vm_names()
    if vm_name not in vm_list:
        raise HTTPException(
            status_code=404,
            detail=f"VM '{vm_name}' not found. Available VMs: {', '.join(vm_list)}"
        )



# ==============================
#  API ENDPOINTS
# ==============================
@app.get("/")
def root():
    """API root endpoint."""
    return {
        "service": "VM Controller API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "list_vms": "GET /vm/list",
            "start_vm": "POST /vm/{vm_name}/start",
            "stop_vm": "POST /vm/{vm_name}/shutdown",
            "restart_vm": "POST /vm/{vm_name}/restart",
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        vms = get_all_vm_names()
        return {
            "status": "healthy",
            "vm_count": len(vms),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/vm/list")
def list_vms(request: Request):
    """
    List all VMs.
    
    No authentication required for listing (modify if needed).
    """
    try:
        vms = get_all_vm_names()
        write_json_log({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "list",
            "client_ip": request.client.host,
            "result": vms
        })
        return {"vms": vms}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list VMs: {str(e)}"
        )


@app.post("/vm/{vm_name}/shutdown")
async def shutdown_vm(
    vm_name: str,
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None)
):
    """
    Shutdown (stop) a VM.
    
    Requires:
    - x-api-key header
    - x-signature header (HMAC)
    - x-timestamp header
    """
    try:
        verify_ip(request)
        verify_key(x_api_key)

        raw_body = await request.body()
        verify_hmac_signature(x_signature, x_timestamp, raw_body)

        validate_vm(vm_name)

        output = run_powershell(f'Stop-VM -Name "{vm_name}" -Force', force_no_confirm=True)

        write_audit("shutdown", vm_name, request.client.host, "ok", output)
        write_json_log({
            "action": "shutdown",
            "vm": vm_name,
            "ip": request.client.host,
            "output": output
        })

        return {
            "vm": vm_name,
            "action": "shutdown",
            "output": output,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        write_audit("shutdown", vm_name, request.client.host, "error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to shutdown VM: {str(e)}"
        )


@app.post("/vm/{vm_name}/start")
async def start_vm(
    vm_name: str,
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None)
):
    """
    Start a VM.
    
    Requires:
    - x-api-key header
    - x-signature header (HMAC)
    - x-timestamp header
    """
    try:
        verify_ip(request)
        verify_key(x_api_key)

        raw_body = await request.body()
        verify_hmac_signature(x_signature, x_timestamp, raw_body)

        validate_vm(vm_name)

        output = run_powershell(f'Start-VM -Name "{vm_name}"', force_no_confirm=True)

        write_audit("start", vm_name, request.client.host, "ok", output)
        write_json_log({
            "action": "start",
            "vm": vm_name,
            "ip": request.client.host,
            "output": output
        })

        return {
            "vm": vm_name,
            "action": "start",
            "output": output,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        write_audit("start", vm_name, request.client.host, "error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start VM: {str(e)}"
        )


@app.post("/vm/{vm_name}/restart")
async def restart_vm(
    vm_name: str,
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None)
):
    """
    Restart a VM.
    
    Requires:
    - x-api-key header
    - x-signature header (HMAC)
    - x-timestamp header
    """
    try:
        verify_ip(request)
        verify_key(x_api_key)

        raw_body = await request.body()
        verify_hmac_signature(x_signature, x_timestamp, raw_body)

        validate_vm(vm_name)

        output = run_powershell(f'Restart-VM -Name "{vm_name}" -Force', force_no_confirm=True)

        write_audit("restart", vm_name, request.client.host, "ok", output)
        write_json_log({
            "action": "restart",
            "vm": vm_name,
            "ip": request.client.host,
            "output": output
        })

        return {
            "vm": vm_name,
            "action": "restart",
            "output": output,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        write_audit("restart", vm_name, request.client.host, "error", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restart VM: {str(e)}"
        )


# ==============================
#  Startup message
# ==============================
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    print("=" * 60)
    print("VM Controller API Started")
    print("=" * 60)
    print(f"API Key configured: {'✓' if API_KEY else '✗'}")
    print(f"HMAC Secret configured: {'✓' if HMAC_SECRET else '✗'}")
    print(f"IP Whitelisting: {'Enabled (' + ALLOW_IP + ')' if ALLOW_IP else 'Disabled'}")
    print(f"Logging directory: {LOG_DIR}")
    print("=" * 60)
    
    # Test VM access
    try:
        vms = get_all_vm_names()
        print(f"✓ Hyper-V access verified - {len(vms)} VMs found")
        if vms:
            print(f"  Available VMs: {', '.join(vms)}")
    except Exception as e:
        print(f"✗ Hyper-V access error: {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)