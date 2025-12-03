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

Start the API on Computer B:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or make it a Windows service using NSSM.

---

# 📁 Logs

The script automatically creates a logs directory with two types of logs:

```md
logs/
 ├─ audit.log   (forensic record of all VM actions)
 └─ app.log     (request entry logs + application events)
```

## `audit.log` - VM Action Logs

Records all VM operations (start, stop, restart):

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

---

# 🏗️ Architecture & Best Practices

This API follows FastAPI best practices:

## Middleware Pattern
- **`IPVerificationMiddleware`**: Handles IP whitelisting and request logging for all endpoints automatically
- Executes before any endpoint logic
- Logs rejected requests with reasons

## Dependency Injection
- **`verify_authentication`**: Reusable dependency for API key + HMAC validation
- Applied to protected endpoints via `Depends()`
- Eliminates code duplication across endpoints

## Benefits
- **DRY (Don't Repeat Yourself)**: Security logic defined once, applied everywhere
- **Maintainability**: Changes to auth logic only need updates in one place
- **Separation of Concerns**: Middleware handles cross-cutting concerns, dependencies handle authentication
- **Testability**: Each component can be tested independently

---

# 🔄 Changelog

## v2.0.0 (Current)

### Added
- Middleware-based IP verification for all endpoints (/, /health, /vm/list, VM control endpoints)
- Request logging at entry point before authentication
- Dependency injection for authentication to eliminate repetitive code
- Enhanced logging with request status tracking

### Changed
- Refactored authentication flow using FastAPI dependencies
- IP verification now automatic via middleware
- Improved log structure with entry-point tracking

### Benefits
- Cleaner, more maintainable code
- Better security visibility (all requests logged at entry)
- Follows FastAPI best practices