# VM Controller API - NSSM Service Uninstallation Script
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VM Controller API - Service Uninstallation" -ForegroundColor Cyan
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

$SERVICE_NAME = "VMControllerAPI"

# Check if service exists
$existingService = Get-Service -Name $SERVICE_NAME -ErrorAction SilentlyContinue

if (-not $existingService) {
    Write-Host "[INFO] Service '$SERVICE_NAME' does not exist" -ForegroundColor Yellow
    Write-Host "Nothing to uninstall." -ForegroundColor Cyan
    pause
    exit 0
}

# Confirm uninstallation
Write-Host "Service '$SERVICE_NAME' found" -ForegroundColor Yellow
Write-Host ""
$response = Read-Host "Are you sure you want to uninstall this service? (Y/N)"

if ($response -ne 'Y' -and $response -ne 'y') {
    Write-Host "Uninstallation cancelled." -ForegroundColor Yellow
    pause
    exit 0
}

# Stop the service
Write-Host ""
Write-Host "Stopping service..." -ForegroundColor Yellow

try {
    nssm stop $SERVICE_NAME
    Write-Host "[OK] Service stopped" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Could not stop service (it may not be running)" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# Remove the service
Write-Host ""
Write-Host "Removing service..." -ForegroundColor Yellow

try {
    nssm remove $SERVICE_NAME confirm
    Write-Host "[OK] Service removed successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to remove service: $_" -ForegroundColor Red
    pause
    exit 1
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Uninstallation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The VM Controller API service has been removed." -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: Log files and configuration have been preserved." -ForegroundColor Yellow
Write-Host ""

pause
