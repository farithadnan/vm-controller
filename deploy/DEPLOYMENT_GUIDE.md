# Converting to Executable & Running on Startup

## 🎯 Two Approaches

### Option 1: PyInstaller (Standalone Executable)
Create a single .exe file that can run anywhere

### Option 2: NSSM (Service Manager) - **RECOMMENDED**
Run as a Windows service (more reliable, auto-restart, runs before login)

---

## 📦 Option 1: PyInstaller Executable

### Quick Build (Recommended)

**The easiest way to build:** Just run the automated build script!

```powershell
# Navigate to deploy directory
cd <your-project-path>\deploy

# Build with automatic version increment (patch: 1.0.0 → 1.0.1)
.\build.ps1

# Or specify version type:
.\build.ps1 -VersionType patch   # 1.0.1 → 1.0.2
.\build.ps1 -VersionType minor   # 1.0.2 → 1.1.0
.\build.ps1 -VersionType major   # 1.1.0 → 2.0.0

# Output: deploy/dist/vm_controller.exe (single portable file)
```

**What the build script does automatically:**
- ✅ Increments version number (semantic versioning)
- ✅ Updates `version.txt`
- ✅ Logs build history with timestamps
- ✅ Runs PyInstaller with optimized settings
- ✅ Creates single portable `.exe` (no dependencies needed)
- ✅ Shows colored build progress

**Build Output:**
- `dist/vm_controller.exe` - Single portable executable
- `dist/version_history.txt` - Build history log
- `version.txt` - Current version number

### Manual Build (Advanced)

If you need to build manually:

```powershell
# Install PyInstaller (first time only)
pip install pyinstaller

# Build with spec file
cd <your-project-path>\deploy
pyinstaller vm_controller.spec --noconfirm --clean
```

**Note:** You'll see warnings during build - these are normal and safe:
- ⚠️ `api-ms-win-crt-*.dll` not found → Ignore (built into Windows)
- ⚠️ Other DLL warnings → Safe to ignore

As long as you see `Build successful!` at the end, the executable is working fine.

### Test the Executable
```powershell
cd dist
.\vm_controller.exe

# First run: Interactive setup will prompt for credentials
# - API_KEY (can auto-generate)
# - HMAC_SECRET (can auto-generate)
# - ALLOW_IPS (comma-separated, or * for all)

# Credentials are encrypted and saved to config/credentials.dat
# Logs will be saved to data/logs/
```

**Folder structure after first run:**
```
vm_controller.exe       # Single portable executable
├── config/
│   └── credentials.dat # Encrypted credentials (Windows DPAPI)
└── data/
    └── logs/
        ├── app.log     # Application logs
        └── audit.log   # VM operation audit trail
```

### Add to Windows Startup

#### Method A: Startup Folder (Current User)
```powershell
# Create shortcut in startup folder
$exePath = "C:\Path\To\vm_controller.exe"  # Update with your exe location
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\VM Controller.lnk")
$Shortcut.TargetPath = $exePath
$Shortcut.WorkingDirectory = Split-Path $exePath
$Shortcut.Save()
```

#### Method B: Task Scheduler (Runs as Administrator)
```powershell
# Run this PowerShell as Administrator
$exePath = "C:\Path\To\vm_controller.exe"  # Update with your exe location
$workingDir = Split-Path $exePath
$action = New-ScheduledTaskAction -Execute $exePath -WorkingDirectory $workingDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "VM Controller API" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "VM Controller API Service"
```

To verify it was created:

```powershell
# Open the Startup folder to see the shortcut
explorer "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"
```

To remove it later (if needed):

```powershell
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\VM Controller.lnk"
```



---

## 🔧 Option 2: NSSM Windows Service (RECOMMENDED)

### Why NSSM is Better:
- ✅ Automatic restart on failure
- ✅ Runs before user login
- ✅ Better logging
- ✅ Easy start/stop/restart
- ✅ No console window

### Step 1: Download NSSM
```powershell
# Download NSSM
Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "$env:TEMP\nssm.zip"

# Extract
Expand-Archive -Path "$env:TEMP\nssm.zip" -DestinationPath "$env:TEMP\nssm" -Force

# Copy to system directory (64-bit)
Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" -Destination "C:\Windows\System32\"
```

### Step 2: Get Python Path
```powershell
# Get your Python executable path
python -c "import sys; print(sys.executable)"
# Example output: C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe
```

### Step 3: Install Service
```powershell
# Run PowerShell as Administrator

# Navigate to project directory
cd <your-project-path>

# Get Python path dynamically
$pythonPath = (Get-Command python).Source

# Install the service
nssm install VMControllerAPI "$pythonPath" "-m uvicorn controller_api:app --host 0.0.0.0 --port 8000"

# Set working directory
nssm set VMControllerAPI AppDirectory "<your-project-path>"

# Set environment file
nssm set VMControllerAPI AppEnvironmentExtra ":PYTHONUNBUFFERED=1"

# Set logging (replace <your-project-path> with actual path)
$projectPath = "<your-project-path>"  # e.g., C:\Projects\vm-controller
nssm set VMControllerAPI AppStdout "$projectPath\logs\service_output.log"
nssm set VMControllerAPI AppStderr "$projectPath\logs\service_error.log"

# Set to start automatically
nssm set VMControllerAPI Start SERVICE_AUTO_START

# Set restart policy (restart on failure)
nssm set VMControllerAPI AppExit Default Restart
nssm set VMControllerAPI AppRestartDelay 5000

# Set display name and description
nssm set VMControllerAPI DisplayName "VM Controller API"
nssm set VMControllerAPI Description "FastAPI service for controlling Hyper-V virtual machines"

# Start the service
nssm start VMControllerAPI
```

### Step 4: Manage the Service
```powershell
# Check status
nssm status VMControllerAPI

# Start service
nssm start VMControllerAPI

# Stop service
nssm stop VMControllerAPI

# Restart service
nssm restart VMControllerAPI

# Remove service (if needed)
nssm remove VMControllerAPI confirm
```

### Alternative: Use Windows Services UI
```powershell
# Open Services manager
services.msc

# Find "VM Controller API"
# Right-click → Properties
# Set Startup type: Automatic
# Click Start
```

---

## 🔍 Verify Service is Running

### Check Service Status
```powershell
Get-Service -Name VMControllerAPI
```

### Check if API is Responding
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

### Check Logs
```powershell
# Service logs
Get-Content "C:\Users\Administrator\Desktop\Projects\vm-controller\logs\service_output.log" -Tail 20

# Application logs
Get-Content "C:\Users\Administrator\Desktop\Projects\vm-controller\logs\app.log" -Tail 20
```

---

## 📝 NSSM Service Installation Script

I've created `install_service.ps1` for easy installation. Just run:

```powershell
# Run as Administrator
powershell -ExecutionPolicy Bypass -File install_service.ps1
```

---
## 🚀 Quick Start Guide

### Fastest Way: Build Executable

1. **Build the executable** (automated with versioning)
   ```powershell
   cd <your-project-path>\deploy
   .\build.ps1
   ```

2. **Run the executable**
   ```powershell
   cd dist
   .\vm_controller.exe
   ```

3. **First-time setup** (interactive prompts)
   - Enter API_KEY (or press Enter to auto-generate)
   - Enter HMAC_SECRET (or press Enter to auto-generate)
   - Enter ALLOW_IPS (comma-separated IPs, or * for all)

4. **Access the API**
   ```
   http://localhost:8000/docs
   ```

Done! Your API is running. To make it start automatically, see the startup methods below.

### Alternative: NSSM Service (For Auto-Start)

1. **Download NSSM** (if not already installed)
   ```powershell
   Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile "$env:TEMP\nssm.zip"
   Expand-Archive -Path "$env:TEMP\nssm.zip" -DestinationPath "$env:TEMP\nssm" -Force
   Copy-Item "$env:TEMP\nssm\nssm-2.24\win64\nssm.exe" -Destination "C:\Windows\System32\"
   ```

2. **Run the installation script as Administrator**
   ```powershell
   cd <your-project-path>\deploy
   powershell -ExecutionPolicy Bypass -File install_service.ps1
   ```

3. **Verify it's running**
   ```powershell
   Get-Service VMControllerAPI
   Invoke-WebRequest -Uri "http://localhost:8000/health"
   ```

Done! Your API will now start automatically on Windows boot.
Done! Your API will now start automatically on Windows boot.

---

## 🛠️ Troubleshooting

### Service Won't Start
```powershell
# Check service status
nssm status VMControllerAPI

# Check error logs
Get-Content "logs\service_error.log" -Tail 50

# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Try running manually first
python -m uvicorn controller_api:app --host 0.0.0.0 --port 8000
```

### Python Not Found
```powershell
# Find Python executable
Get-Command python | Select-Object -ExpandProperty Source

# Update service with correct path
## 📊 Comparison

| Feature | PyInstaller | NSSM Service |
|---------|-------------|--------------|
| **Build Process** | ✅ Automated script | Manual setup |
| **Portability** | ✅ Single .exe file | Requires Python |
| **Version Tracking** | ✅ Automatic | Manual |
| **Auto-start** | After login | Before login |
| **Restart on crash** | No | ✅ Yes |
| **Logging** | Built-in (data/logs/) | Service logs |
| **Management** | Manual | Windows Services |
| **Installation** | ✅ Just run .exe | Requires NSSM |
| **Updates** | ✅ `.\build.ps1` | Restart service |
| **Best for** | ✅ **Recommended** | Production servers |

**Recommendation**: Use **PyInstaller** for easy deployment with automated builds and version tracking. Use **NSSM** only if you need service-level features (auto-restart, system service).
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or change port in service
nssm set VMControllerAPI AppParameters "-m uvicorn controller_api:app --host 0.0.0.0 --port 8001"
nssm restart VMControllerAPI
```

---

## 📊 Comparison
## 🔄 Updating the Application

When you update your code:

### PyInstaller Executable:
```powershell
# Navigate to deploy folder
cd <your-project-path>\deploy

# Rebuild with automatic version increment
.\build.ps1               # Patch: 1.0.1 → 1.0.2
.\build.ps1 -VersionType minor  # Minor: 1.0.2 → 1.1.0
.\build.ps1 -VersionType major  # Major: 1.1.0 → 2.0.0

# New executable in dist/vm_controller.exe
# Replace old executable with new one
# Restart if running
```

### NSSM Service:
```powershell
# Stop service
nssm stop VMControllerAPI

# Update your code
git pull  # or rebuild executable

# Start service
nssm start VMControllerAPI
```

**Version History:** Check `dist/version_history.txt` to see all builds with timestamps. ] API responds to authenticated requests

---

## 🔄 Updating the Service

When you update your code:

### NSSM Service:
```powershell
# Stop service
nssm stop VMControllerAPI

# Update your code
git pull  # or make changes

# Start service
nssm start VMControllerAPI
```

### PyInstaller Executable:
```powershell
# Rebuild
pyinstaller vm_controller.spec

# Replace old executable
# Restart via Task Scheduler or startup folder
```

---

## 📱 Remote Access

To access from other computers:

1. **Allow through firewall**
   ```powershell
   New-NetFirewallRule -DisplayName "VM Controller API" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   ```

2. **Update ALLOW_IP in .env if needed**
   ```
   ALLOW_IP=  # Leave empty to allow all (or set specific IP)
   ```

3. **Access from other computer**
   ```
   http://<server-ip>:8000/
   ```
