# VM Controller API - NSSM Service Installation Script
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VM Controller API - Service Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Configuration
$SERVICE_NAME = "VMControllerAPI"
$DISPLAY_NAME = "VM Controller API"
$DESCRIPTION = "FastAPI service for controlling Hyper-V virtual machines"
$PROJECT_DIR = Split-Path $PSScriptRoot -Parent
$LOG_DIR = Join-Path $PROJECT_DIR "logs"

# Ensure logs directory exists
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
    Write-Host "[OK] Created logs directory" -ForegroundColor Green
}

# Get Python executable path
Write-Host "Detecting Python installation..." -ForegroundColor Yellow
try {
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
    Write-Host "[OK] Found Python at: $pythonPath" -ForegroundColor Green
    
    # Verify Python version
    $pythonVersion = & python --version 2>&1
    Write-Host "    Version: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Python not found in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and add it to PATH" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if NSSM is installed
Write-Host ""
Write-Host "Checking for NSSM..." -ForegroundColor Yellow
$nssmPath = Get-Command nssm -ErrorAction SilentlyContinue

if (-not $nssmPath) {
    Write-Host "[INFO] NSSM not found. Installing..." -ForegroundColor Yellow
    
    try {
        # Download NSSM
        $nssmZip = Join-Path $env:TEMP "nssm.zip"
        $nssmExtract = Join-Path $env:TEMP "nssm"
        
        Write-Host "Downloading NSSM..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri "https://nssm.cc/release/nssm-2.24.zip" -OutFile $nssmZip -UseBasicParsing
        
        Write-Host "Extracting NSSM..." -ForegroundColor Cyan
        Expand-Archive -Path $nssmZip -DestinationPath $nssmExtract -Force
        
        Write-Host "Installing NSSM to System32..." -ForegroundColor Cyan
        Copy-Item "$nssmExtract\nssm-2.24\win64\nssm.exe" -Destination "C:\Windows\System32\" -Force
        
        # Cleanup
        Remove-Item $nssmZip -Force
        Remove-Item $nssmExtract -Recurse -Force
        
        Write-Host "[OK] NSSM installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to install NSSM: $_" -ForegroundColor Red
        Write-Host "Please download manually from: https://nssm.cc/download" -ForegroundColor Yellow
        pause
        exit 1
    }
} else {
    Write-Host "[OK] NSSM is already installed" -ForegroundColor Green
}

# Check if service already exists
Write-Host ""
Write-Host "Checking for existing service..." -ForegroundColor Yellow
$existingService = Get-Service -Name $SERVICE_NAME -ErrorAction SilentlyContinue

if ($existingService) {
    Write-Host "[INFO] Service '$SERVICE_NAME' already exists" -ForegroundColor Yellow
    $response = Read-Host "Do you want to reinstall? (Y/N)"
    
    if ($response -eq 'Y' -or $response -eq 'y') {
        Write-Host "Stopping and removing existing service..." -ForegroundColor Cyan
        nssm stop $SERVICE_NAME
        nssm remove $SERVICE_NAME confirm
        Start-Sleep -Seconds 2
        Write-Host "[OK] Existing service removed" -ForegroundColor Green
    } else {
        Write-Host "Installation cancelled." -ForegroundColor Yellow
        pause
        exit 0
    }
}

# Install the service
Write-Host ""
Write-Host "Installing service..." -ForegroundColor Yellow

try {
    # Install service
    $appParams = "-m uvicorn controller_api:app --host 0.0.0.0 --port 8000"
    nssm install $SERVICE_NAME $pythonPath $appParams
    
    # Set working directory
    nssm set $SERVICE_NAME AppDirectory $PROJECT_DIR
    
    # Set environment
    nssm set $SERVICE_NAME AppEnvironmentExtra "PYTHONUNBUFFERED=1"
    
    # Set logging
    $stdoutLog = Join-Path $LOG_DIR "service_output.log"
    $stderrLog = Join-Path $LOG_DIR "service_error.log"
    nssm set $SERVICE_NAME AppStdout $stdoutLog
    nssm set $SERVICE_NAME AppStderr $stderrLog
    
    # Rotate logs (10MB)
    nssm set $SERVICE_NAME AppStdoutCreationDisposition 4
    nssm set $SERVICE_NAME AppStderrCreationDisposition 4
    nssm set $SERVICE_NAME AppRotateFiles 1
    nssm set $SERVICE_NAME AppRotateOnline 1
    nssm set $SERVICE_NAME AppRotateBytes 10485760
    
    # Set startup type
    nssm set $SERVICE_NAME Start SERVICE_AUTO_START
    
    # Set restart policy
    nssm set $SERVICE_NAME AppExit Default Restart
    nssm set $SERVICE_NAME AppRestartDelay 5000
    
    # Set display name and description
    nssm set $SERVICE_NAME DisplayName $DISPLAY_NAME
    nssm set $SERVICE_NAME Description $DESCRIPTION
    
    Write-Host "[OK] Service installed successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to install service: $_" -ForegroundColor Red
    pause
    exit 1
}

# Start the service
Write-Host ""
Write-Host "Starting service..." -ForegroundColor Yellow

try {
    nssm start $SERVICE_NAME
    Start-Sleep -Seconds 3
    
    $serviceStatus = nssm status $SERVICE_NAME
    
    if ($serviceStatus -eq "SERVICE_RUNNING") {
        Write-Host "[OK] Service started successfully!" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Service status: $serviceStatus" -ForegroundColor Yellow
        Write-Host "Check logs for details:" -ForegroundColor Cyan
        Write-Host "  Output: $stdoutLog" -ForegroundColor Cyan
        Write-Host "  Errors: $stderrLog" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[ERROR] Failed to start service: $_" -ForegroundColor Red
    Write-Host "Check logs for details:" -ForegroundColor Cyan
    Write-Host "  Output: $stdoutLog" -ForegroundColor Cyan
    Write-Host "  Errors: $stderrLog" -ForegroundColor Cyan
}

# Verify API is responding
Write-Host ""
Write-Host "Verifying API response..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] API is responding!" -ForegroundColor Green
        Write-Host "    URL: http://localhost:8000" -ForegroundColor Cyan
    }
} catch {
    Write-Host "[WARNING] Could not verify API response" -ForegroundColor Yellow
    Write-Host "The service may still be starting up. Check status in a moment." -ForegroundColor Cyan
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service Name: $SERVICE_NAME" -ForegroundColor Cyan
Write-Host "Status: $(nssm status $SERVICE_NAME)" -ForegroundColor Cyan
Write-Host "API URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  nssm status $SERVICE_NAME     - Check status" -ForegroundColor White
Write-Host "  nssm start $SERVICE_NAME      - Start service" -ForegroundColor White
Write-Host "  nssm stop $SERVICE_NAME       - Stop service" -ForegroundColor White
Write-Host "  nssm restart $SERVICE_NAME    - Restart service" -ForegroundColor White
Write-Host "  nssm remove $SERVICE_NAME     - Remove service" -ForegroundColor White
Write-Host ""
Write-Host "Logs Location:" -ForegroundColor Yellow
Write-Host "  $LOG_DIR" -ForegroundColor White
Write-Host ""
Write-Host "The service will start automatically on Windows boot." -ForegroundColor Green
Write-Host ""

pause
