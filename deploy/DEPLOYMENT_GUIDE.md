# Converting to Executable & Running on Startup

## 🎯 Two Approaches

### Option 1: PyInstaller (Standalone Executable)
Create a single .exe file that can run anywhere

### Option 2: NSSM (Service Manager) - **RECOMMENDED**
Run as a Windows service (more reliable, auto-restart, runs before login)

---

## 📦 Option 1: PyInstaller Executable

### Step 1: Install PyInstaller
```powershell
pip install pyinstaller
```

### Step 2: Create Spec File
I've created `vm_controller.spec` for you. This handles all dependencies.

### Step 3: Build the Executable
```powershell
# Navigate to deploy directory
cd <your-project-path>\deploy

# Build with spec file
pyinstaller vm_controller.spec

# Output will be in deploy/dist/vm_controller/vm_controller.exe
```

### Step 4: Test the Executable
```powershell
cd dist\vm_controller
.\vm_controller.exe

# Note: The executable expects .env file in its directory
# Copy .env from project root if needed:
# Copy-Item "..\..\..\..env" -Destination ".env"
```

### Step 5: Add to Windows Startup

#### Method A: Startup Folder (Current User)
```powershell
# Create shortcut in startup folder
$projectPath = "<your-project-path>"  # e.g., C:\Projects\vm-controller
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\VM Controller.lnk")
$Shortcut.TargetPath = "$projectPath\deploy\dist\vm_controller\vm_controller.exe"
$Shortcut.WorkingDirectory = "$projectPath\deploy\dist\vm_controller"
$Shortcut.Save()
```

#### Method B: Task Scheduler (Runs as Administrator)
```powershell
# Run this PowerShell as Administrator
$projectPath = "<your-project-path>"  # e.g., C:\Projects\vm-controller
$action = New-ScheduledTaskAction -Execute "$projectPath\deploy\dist\vm_controller\vm_controller.exe" -WorkingDirectory "$projectPath\deploy\dist\vm_controller"
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

### Recommended: NSSM Service

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
nssm set VMControllerAPI Application "C:\Path\To\Python\python.exe"
nssm restart VMControllerAPI
```

### Permission Errors
```powershell
# Make sure running as Administrator
# Make sure .env file has correct API_KEY and HMAC_SECRET
# Make sure Hyper-V permissions are set
```

### Port Already in Use
```powershell
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

| Feature | PyInstaller | NSSM Service |
|---------|-------------|--------------|
| **Auto-start** | After login | Before login |
| **Restart on crash** | No | Yes |
| **Logging** | Manual | Automatic |
| **Management** | Manual | Windows Services |
| **Installation** | Complex | Simple |
| **Updates** | Rebuild exe | Just restart |
| **Best for** | Portable apps | Server/Production |

**Recommendation**: Use **NSSM** for production/server use. Use **PyInstaller** if you need a portable executable.

---

## 🎯 Final Checklist

After installation:
- [ ] Service shows as "Running" in Services
- [ ] Can access http://localhost:8000/
- [ ] Can access http://localhost:8000/health
- [ ] Logs are being written to logs/ directory
- [ ] Service survives reboot (restart computer and check)
- [ ] API responds to authenticated requests

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
