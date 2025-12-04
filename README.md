# VM Controller (Hyper-V Remote VM Control API )

A lightweight, secure FastAPI service that allows you to remotely start, stop, restart, and list Hyper-V virtual machines running on **Computer B**.

This API is designed for a setup where:

- **Computer A** (client machine or chatbot agent)  
  needs to remotely control Hyper-V VMs.

- **Computer B** (server machine)  
  hosts the VMs and exposes **this secured API** on your LAN.

This service integrates:
- API Key verification  
- Optional IP allow-listing  
- HMAC-signed requests  
- Audit logging + structured JSON logs  
- Safe PowerShell execution (no prompts)

---

# ✨ Features

- **List all Hyper-V VMs**
- **Start a VM**
- **Shutdown a VM (force)**
- **Restart a VM (force)**
- **API Key authentication**
- **HMAC SHA-256 signature validation**
- **IP address filtering (applied to all endpoints)**
- **Request logging at entry point (before authentication)**
- **Audit logs for every action**
- **JSON logs for programmatic use**
- **Safe PowerShell execution with optional `-Confirm:$false`**
- **Middleware-based security architecture**
- **Dependency injection for clean code**

---

# 🖥️ Architecture Overview

```md
Computer A (Client)
|
| → HTTPS / LAN Request
| - API Key Header
| - HMAC Signature (Body + Timestamp)
v
Computer B (Hyper-V Host Running FastAPI Server)
|
→ Executes PowerShell commands safely
```


This design removes the need to expose PowerShell Remoting or SMB shares and gives you a simple REST interface instead — perfect for automation, bots, or monitoring tools.

---

# ⚙️ Requirements on Computer B

- Windows 10/11 or Windows Server running **Hyper-V**
- Python 3.10+
- `pip install fastapi uvicorn python-dotenv`
- PowerShell available in PATH
- Script must be run with permissions to control VMs
- Might need to make port `8000` available to your LAN.

---

# 📂 Project Files

```
vm-controller/
├── controller_api.py              # Original procedural version
├── README.md                      # This file
├── .env                          # Configuration (create this)
└── logs/                         # Auto-created
    ├── audit.log                 # VM operation logs
    └── app.log                   # Request/application logs
```

---

# 🔐 `.env` Configuration

Create a file named `.env` in the same directory as the script:

```env
API_KEY=your-super-secret-api-key
HMAC_SECRET=your-hmac-secret
ALLOW_IP=192.168.x.x
```

## Meaning of each:

| Variable      | Purpose                                                                     |
| ------------- | --------------------------------------------------------------------------- |
| `API_KEY`     | Client must send `x-api-key` header. Prevents unauthorized access.          |
| `HMAC_SECRET` | Secret for SHA-256 request signing. Prevents tampering/replay attacks.      |
| `ALLOW_IP`    | Optional. Only allow requests from this IP address. Leave blank to disable. |


---

# 🚀 Running the Server

This project includes **two versions** of the same API:

## Option 1: Original (Procedural)
```sh
uvicorn controller_api:app --host 0.0.0.0 --port 8000
```
**Use when**: Learning, quick prototyping, simple deployment

## Option 2: Refactored (Object-Oriented)
```sh
uvicorn controller_api_refactored:app --host 0.0.0.0 --port 8000
```
**Use when**: Production, team projects, extensive testing needed

Both versions have **identical functionality**. See `OOP_REFACTORING_GUIDE.md` for details.

---

# 📦 Deployment

## Deployment Options

### Option 1: Windows Service (Recommended for Production)
Runs as a Windows service with auto-restart, auto-start on boot, and better reliability:
```powershell
cd deploy
powershell -ExecutionPolicy Bypass -File install_service.ps1
```

### Option 2: Standalone Executable
Create a portable `.exe` file that can run without Python installed:
```powershell
cd deploy
pyinstaller vm_controller.spec
# Output: deploy/dist/vm_controller/vm_controller.exe
```

### 📖 Complete Guide
For detailed instructions, troubleshooting, and all deployment methods, see:
**[Deployment Guide](deploy/DEPLOYMENT_GUIDE.md)**

The guide covers:
- ✅ Windows Service installation (NSSM) - auto-start, auto-restart
- ✅ Creating standalone executables (PyInstaller) - portable, no Python needed
- ✅ Startup configuration (Task Scheduler, Startup folder)
- ✅ Service management and troubleshooting
- ✅ Remote access configuration

---

# 📁 Logs

The script automatically creates a logs directory with **two separate log files** for different purposes:

```md
logs/
 ├─ audit.log   (forensic record of VM operations only)
 └─ app.log     (all API requests and application events)
```

## Understanding the Two Logging Methods

### 🎯 `write_audit()` → `audit.log`

**Purpose**: Compliance and forensic tracking of **VM state changes only**

**When to use**: Only logs actual VM operations (start, stop, restart)

**Why separate?**: 
- Legal/compliance requirements to track infrastructure changes
- Audit who changed what VM and when
- Separate from general access logs for security analysis

**Example entry**:

```json
{
  "timestamp": "2025-01-01T12:00:00Z",
  "action": "restart",
  "vm": "UbuntuVM",
  "client_ip": "192.168.1.20",
  "status": "ok",
  "details": "Restarting machine"
}
```

## `app.log` - Request & Application Logs

**New Feature**: Logs every request at entry point (before authentication):

```json
{
  "timestamp": "2025-12-03T10:30:15.123456",
  "method": "POST",
  "path": "/vm/UbuntuVM/start",
  "client_ip": "192.168.1.20",
  "status": "received",
  "details": "Headers: {...}"
}
```

Also logs IP rejections:

```json
{
  "timestamp": "2025-12-03T10:31:00.000000",
  "method": "GET",
  "path": "/vm/list",
  "client_ip": "192.168.1.99",
  "status": "rejected",
  "details": "IP 192.168.1.99 not in whitelist"
}
```

---

# 🔒 Security Architecture

## Three-Layer Security Model

### 1. **Middleware Layer (All Endpoints)**
- **IP Whitelisting**: Automatically applied to all endpoints via middleware
- **Request Logging**: Every request is logged at entry point before any processing
- No manual verification needed in endpoint code

### 2. **Authentication Layer (Protected Endpoints)**
Applied automatically via dependency injection to `/vm/list`, `/start`, `/shutdown`, `/restart`:

**API Key (required)** - Client must send header:

```sh
x-api-key: YOUR_API_KEY
```

**HMAC Signing (required)** - Signature formula:

```sh
signature = HEX( HMAC_SHA256( HMAC_SECRET, body + timestamp ) )
```

Client must send:

```md
x-signature: <hex-hmac>
x-timestamp: <unix timestamp or ISO>
```

### 3. **Authorization Layer**
- VM existence validation
- Audit logging of all actions

---

# 📡 API Endpoints

## Health Check

Request:

```bash
GET /health
```

Response:

```json
{
  "status": "healthy",
  "vm_count": 3,
  "timestamp": "2025-12-03T10:30:00.000000"
}
```

**Security**: IP whitelisting applied (if configured)

---

## List all VMs

Request:

```bash
GET /vm/list
```

Required Headers:

```md
x-api-key: <API_KEY>
x-signature: <HMAC>
x-timestamp: <timestamp>
```

Response:

```json
{
  "vms": ["Windows10", "UbuntuServer", "TestVM"]
}
```

**Security**: Full authentication required (API key + HMAC signature + IP whitelisting)

---

## Start a VM

Request:

```bash
POST /vm/{vm_name}/start
```

Required Headers:

```md
x-api-key: <API_KEY>
x-signature: <HMAC>
x-timestamp: <timestamp>
```

Body:

```bash
# RAW
{}
```

Response

```json
{
  "vm": "UbuntuServer",
  "action": "start",
  "output": "VM started successfully"
}
```
---

## Shutdown a VM

Request:

```bash
POST /vm/{vm_name}/shutdown
```

Required Headers:

```md
x-api-key: <API_KEY>
x-signature: <HMAC>
x-timestamp: <timestamp>
```

Body:

```bash
# RAW
{}
```

Response:

```json
{
  "vm": "Windows10",
  "action": "shutdown",
  "output": "VM stopped"
}
```

---

## Restart a VM

Request:

```bash
POST /vm/{vm_name}/restart
```

Required Headers:

```md
x-api-key: <API_KEY>
x-signature: <HMAC>
x-timestamp: <timestamp>
```

Body:

```bash
# RAW
{}
```

Response:

```json
{
  "vm": "TestVM",
  "action": "restart",
  "output": "VM restarted",
  "status": "success"
}
```
