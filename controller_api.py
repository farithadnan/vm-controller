import os
import hmac
import json
import hashlib
import subprocess
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

app = FastAPI()

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

AUDIT_LOG_FILE = f"{LOG_DIR}/audit.log"
APP_LOG_FILE = f"{LOG_DIR}/app.log"


# ==============================
#  Logging utilities
# ==============================
def write_audit(action, vm, ip, status, details=""):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "vm": vm,
        "client_ip": ip,
        "status": status,
        "details": details,
    }
    with open(AUDIT_LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def write_json_log(data):
    with open(APP_LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")


# ==============================
#  Helper to run PowerShell (no prompts)
# ==============================
def run_powershell(cmd, force_no_confirm=False):
    """
    Runs PowerShell commands safely.
    If force_no_confirm=True, append -Confirm:$false ONLY to commands that support it.
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
def get_all_vm_names():
    result = run_powershell("Get-VM | Select-Object -ExpandProperty Name")
    if not result:
        return []
    return [vm.strip() for vm in result.splitlines() if vm.strip()]


# ==============================
#  Verify API key
# ==============================
def verify_key(x_api_key: str):
    if not hmac.compare_digest(x_api_key or "", API_KEY or ""):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ==============================
#  Verify IP (optional)
# ==============================
def verify_ip(request: Request):
    if ALLOW_IP:
        client_ip = request.client.host
        if client_ip != ALLOW_IP:
            raise HTTPException(status_code=403, detail="Forbidden: IP not allowed")


# ==============================
#  Verify HMAC signature
# ==============================
def verify_hmac_signature(signature, timestamp, raw_body):
    """
    signature = hex(HMAC_SHA256(secret, raw_body + timestamp))
    """

    if not HMAC_SECRET:
        return  # HMAC disabled

    if not signature or not timestamp:
        raise HTTPException(status_code=401, detail="Missing signature")

    message = raw_body + timestamp.encode()
    expected = hmac.new(
        HMAC_SECRET.encode(),
        message,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid HMAC signature")


# ==============================
#  Verify VM exists
# ==============================
def validate_vm(vm_name: str):
    vm_list = get_all_vm_names()
    if vm_name not in vm_list:
        raise HTTPException(status_code=404, detail=f"VM '{vm_name}' not found")


# ==============================
#  API ENDPOINTS
# ==============================

@app.get("/vm/list")
def list_vms(request: Request):
    vms = get_all_vm_names()
    write_json_log({
        "timestamp": datetime.utcnow().isoformat(),
        "action": "list",
        "client_ip": request.client.host,
        "result": vms
    })
    return {"vms": vms}


@app.post("/vm/{vm_name}/shutdown")
async def shutdown_vm(vm_name: str, request: Request,
                      x_api_key: str = Header(None),
                      x_signature: str = Header(None),
                      x_timestamp: str = Header(None)):

    verify_ip(request)
    verify_key(x_api_key)

    raw_body = await request.body()
    verify_hmac_signature(x_signature, x_timestamp, raw_body)

    validate_vm(vm_name)

    output = run_powershell(f'Stop-VM -Name "{vm_name}" -Force', force_no_confirm=True)

    write_audit("shutdown", vm_name, request.client.host, "ok", output)
    write_json_log({"action": "shutdown", "vm": vm_name, "ip": request.client.host, "output": output})

    return {"vm": vm_name, "action": "shutdown", "output": output}


@app.post("/vm/{vm_name}/start")
async def start_vm(vm_name: str, request: Request,
                   x_api_key: str = Header(None),
                   x_signature: str = Header(None),
                   x_timestamp: str = Header(None)):

    verify_ip(request)
    verify_key(x_api_key)

    raw_body = await request.body()
    verify_hmac_signature(x_signature, x_timestamp, raw_body)

    validate_vm(vm_name)

    output = run_powershell(f'Start-VM -Name "{vm_name}"', force_no_confirm=True)

    write_audit("start", vm_name, request.client.host, "ok", output)
    write_json_log({"action": "start", "vm": vm_name, "ip": request.client.host, "output": output})

    return {"vm": vm_name, "action": "start", "output": output}


@app.post("/vm/{vm_name}/restart")
async def restart_vm(vm_name: str, request: Request,
                     x_api_key: str = Header(None),
                     x_signature: str = Header(None),
                     x_timestamp: str = Header(None)):

    verify_ip(request)
    verify_key(x_api_key)

    raw_body = await request.body()
    verify_hmac_signature(x_signature, x_timestamp, raw_body)

    validate_vm(vm_name)

    output = run_powershell(f'Restart-VM -Name "{vm_name}" -Force', force_no_confirm=True)

    write_audit("restart", vm_name, request.client.host, "ok", output)
    write_json_log({"action": "restart", "vm": vm_name, "ip": request.client.host, "output": output})

    return {"vm": vm_name, "action": "restart", "output": output}
