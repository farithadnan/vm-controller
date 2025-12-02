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
- **IP address filtering**
- **Audit logs for every action**
- **JSON logs for programmatic use**
- **Safe PowerShell execution with optional `-Confirm:$false`**

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

The script automatically creates a logs directory:

```md
logs/
 ├─ audit.log   (forensic record of all actions)
 └─ app.log     (structured application events)
```

`audit.log` example:

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
---

# 🔒 Authentication Details

**API Key (required)** - Client must send as its header request:

```sh
x-api-key: YOUR_API_KEY
```

**HMAC Signing (Recommended)** - Signature formula:

```sh
signature = HEX( HMAC_SHA256( HMAC_SECRET, body + timestamp ) )
```

Client must send:

```md
x-signature: <hex-hmac>
x-timestamp: <unix timestamp or ISO>
```
If HMAC is enabled in `.env`, both headers are required.

---

# 📡 API Endpoints

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

**Headers required**: *None* (you can lock this down if you)

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
  "output": "VM restarted"
}
```