# VM Controller API

Simple FastAPI server to control Hyper-V VMs remotely.

---

## What this project does

- List VMs
- Get VM state/details
- Start / shutdown / restart VMs
- Protect requests with API key + HMAC
- Log requests and VM actions

---

## 1) Quick setup (Windows)

From project root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.sample .env
```

Edit `.env`:

```env
API_KEY=your_api_key_here
HMAC_SECRET=your_hmac_secret_here
ALLOW_IP=
```

Notes:
- `ALLOW_IP` empty = allow any IP
- Use strong random values for `API_KEY` and `HMAC_SECRET`

---

## 2) Run in development

```powershell
python controller_api.py
```

or

```powershell
uvicorn controller_api:app --host 0.0.0.0 --port 8000
```

Check:
- Health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`

---

## 3) Test in development

Install test deps (if needed):

```powershell
pip install pytest pytest-asyncio pytest-cov httpx
```

Run tests:

```powershell
pytest tests/ -v
```

Run with coverage:

```powershell
pytest tests/ --cov=controller_api --cov-report=html
```

---

## 4) Build and deployment

README keeps this section short on purpose.

Use this guide as the single source of truth for build/deploy/release:

- `deploy/DEPLOYMENT_GUIDE.md`

Quick command to check build/run status:

```powershell
powershell -ExecutionPolicy Bypass -File deploy\check_build_status.ps1
```

---

## API auth (for bot/client)

Protected endpoints require headers:

- `x-api-key`
- `x-signature`
- `x-timestamp`

Signature formula:

```text
HEX(HMAC_SHA256(HMAC_SECRET, body + timestamp))
```

---

## Project folders (important)

- `deploy/` → scripts + version metadata
- `build/` → temporary PyInstaller files
- `dist/` → final executables
- `logs/` → app and audit logs

---

## Daily workflow (recommended)

1. Create branch: `release/exe-vX.Y.Z`
2. Make code changes
3. Run `pytest`
4. Follow `deploy/DEPLOYMENT_GUIDE.md` to build and deploy
5. Run `deploy/check_build_status.ps1`
6. Test `dist/vm_controller.exe`
