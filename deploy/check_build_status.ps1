# VM Controller - Build/Run Status Checker
# Shows:
# 1) Source version (deploy/version.txt)
# 2) Latest EXE in dist/
# 3) Running vm_controller.exe process (if any)
# 4) Whether running process matches latest build

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path $PSScriptRoot -Parent
$versionFile = Join-Path $PSScriptRoot "version.txt"
$distDir = Join-Path $projectRoot "dist"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "VM Controller - Build Status" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Project: $projectRoot" -ForegroundColor Gray

# 1) Source version
$sourceVersion = "(missing)"
if (Test-Path $versionFile) {
    $sourceVersion = (Get-Content $versionFile -Raw).Trim()
}

Write-Host ""
Write-Host "[1] Source Version" -ForegroundColor Yellow
Write-Host "version.txt: $sourceVersion" -ForegroundColor White

# 2) Dist executable(s)
Write-Host ""
Write-Host "[2] Dist Artifacts" -ForegroundColor Yellow

if (-not (Test-Path $distDir)) {
    Write-Host "dist folder not found: $distDir" -ForegroundColor Red
    Write-Host ""
    Write-Host "No build artifacts found. Build first:" -ForegroundColor Yellow
    Write-Host "  ./.venv/Scripts/python -m PyInstaller --onefile --name vm_controller --clean --noconfirm --add-data \"deploy/version.txt;.\" controller_api.py" -ForegroundColor White
    exit 0
}

$distExecutables = Get-ChildItem -Path $distDir -Filter "*.exe" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

if (-not $distExecutables -or $distExecutables.Count -eq 0) {
    Write-Host "No .exe found in dist folder." -ForegroundColor Red
    exit 0
}

$latestExe = $distExecutables[0]

Write-Host "Latest: $($latestExe.FullName)" -ForegroundColor Green
Write-Host "Updated: $($latestExe.LastWriteTime)" -ForegroundColor White
Write-Host "Size:    $([Math]::Round($latestExe.Length / 1MB, 2)) MB" -ForegroundColor White

if ($distExecutables.Count -gt 1) {
    Write-Host ""
    Write-Host "Other EXEs in dist:" -ForegroundColor Gray
    foreach ($exe in $distExecutables | Select-Object -Skip 1) {
        Write-Host "  - $($exe.Name) | $($exe.LastWriteTime)" -ForegroundColor Gray
    }
}

# 3) Running process
Write-Host ""
Write-Host "[3] Running Process" -ForegroundColor Yellow

$running = Get-Process -Name "vm_controller" -ErrorAction SilentlyContinue

if (-not $running) {
    Write-Host "No running vm_controller.exe process found." -ForegroundColor Yellow
    Write-Host "Status: Not running" -ForegroundColor Yellow
    exit 0
}

# Handle multiple processes; prefer the newest process start time
$proc = $running | Sort-Object StartTime -Descending | Select-Object -First 1

Write-Host "Process ID:   $($proc.Id)" -ForegroundColor White
Write-Host "Started at:   $($proc.StartTime)" -ForegroundColor White
Write-Host "Running path: $($proc.Path)" -ForegroundColor White

# 4) Comparison
Write-Host ""
Write-Host "[4] Latest Check" -ForegroundColor Yellow

$latestPath = [System.IO.Path]::GetFullPath($latestExe.FullName)
$runningPath = $null

if ($proc.Path) {
    $runningPath = [System.IO.Path]::GetFullPath($proc.Path)
}

if (-not $runningPath) {
    Write-Host "Cannot read running process path (permission issue)." -ForegroundColor Yellow
    Write-Host "Tip: Run this script in an elevated PowerShell if needed." -ForegroundColor Yellow
    exit 0
}

if ($runningPath -ieq $latestPath) {
    Write-Host "OK: Running process is the latest dist EXE." -ForegroundColor Green
} else {
    Write-Host "WARNING: Running process is NOT the latest dist EXE." -ForegroundColor Red
    Write-Host "Latest dist:  $latestPath" -ForegroundColor White
    Write-Host "Running now:  $runningPath" -ForegroundColor White
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan