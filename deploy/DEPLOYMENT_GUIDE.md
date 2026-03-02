# VM Controller Deployment Guide (Simple)

This guide is focused on 3 things only:
1. Build executable
2. Run/deploy it
3. Verify what version is running

README is quick-start only; deployment details are maintained here.

---

## A) Build executable (recommended)

From project root:

```powershell
cd deploy
powershell -ExecutionPolicy Bypass -File .\build.ps1 -VersionType patch
```

What this does:
- bumps `deploy/version.txt`
- builds exe with PyInstaller
- creates:
  - `dist/vm_controller.exe` (latest)
  - `dist/vm_controller-x.y.z.exe` (versioned copy)
  - `dist/version_history.txt`

If you need minor/major bump:

```powershell
.\build.ps1 -VersionType minor
.\build.ps1 -VersionType major
```

---

## B) Manual build (only if needed)

```powershell
.\.venv\Scripts\python -m PyInstaller --onefile --name vm_controller --clean --noconfirm --add-data "deploy/version.txt;." controller_api.py
```

Important:
- manual build does **not** auto-update `deploy/version.txt`
- update version yourself if you use this path

---

## C) Run the executable

```powershell
.\dist\vm_controller.exe
```

Then open:
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

---

## D) Install as Windows service (optional)

Use this only if you want auto-start/restart:

```powershell
cd deploy
powershell -ExecutionPolicy Bypass -File .\install_service.ps1
```

Uninstall:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_service.ps1
```

---

## E) Know what is latest vs running

Use the status checker:

```powershell
powershell -ExecutionPolicy Bypass -File deploy\check_build_status.ps1
```

It shows:
- version in `deploy/version.txt`
- newest exe in `dist/`
- currently running `vm_controller.exe` path
- whether running exe matches latest build

---

## F) Folder meanings (quick)

- `deploy/` scripts and version files
- `build/` temporary build artifacts (safe to clean)
- `dist/` final `.exe` files

---

## G) Suggested release routine

1. Branch: `release/exe-vX.Y.Z`
2. Update code
3. Run tests: `pytest tests/ -v`
4. Build: `deploy/build.ps1`
5. Check: `deploy/check_build_status.ps1`
6. Smoke test: `dist/vm_controller.exe` + `/health`
7. Ship `dist/vm_controller-X.Y.Z.exe`
