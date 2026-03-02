# VM Controller Build Script with Auto-Versioning
# Usage: .\build.ps1 -VersionType [major|minor|patch]

param(
    [ValidateSet('major', 'minor', 'patch')]
    [string]$VersionType = 'patch'
)

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "VM Controller - Build & Deploy" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$projectRoot = Split-Path $PSScriptRoot -Parent
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonExe = $pythonCmd.Source
    } else {
        Write-Host "[ERROR] Python not found (.venv or PATH)" -ForegroundColor Red
        exit 1
    }
}

# Read current version
$versionFile = Join-Path $PSScriptRoot "version.txt"
if (Test-Path $versionFile) {
    $currentVersion = Get-Content $versionFile -Raw
    $currentVersion = $currentVersion.Trim()
} else {
    $currentVersion = "1.0.0"
}

# Parse version
$versionParts = $currentVersion -split '\.'
$major = [int]$versionParts[0]
$minor = [int]$versionParts[1]
$patch = [int]$versionParts[2]

Write-Host "Current version: $currentVersion" -ForegroundColor Yellow

# Increment version
switch ($VersionType) {
    'major' {
        $major++
        $minor = 0
        $patch = 0
    }
    'minor' {
        $minor++
        $patch = 0
    }
    'patch' {
        $patch++
    }
}

$newVersion = "$major.$minor.$patch"
Write-Host "New version:     $newVersion" -ForegroundColor Green

# Update version file
Set-Content -Path $versionFile -Value $newVersion -NoNewline

Write-Host "`nUpdating version.txt..." -ForegroundColor Cyan

# Build folders at project root
$distFolder = Join-Path $projectRoot "dist"
$buildFolder = Join-Path $projectRoot "build"

# Copy version to dist for tracking
if (-not (Test-Path $distFolder)) {
    New-Item -ItemType Directory -Path $distFolder -Force | Out-Null
}

# Create version history
$historyFile = Join-Path $distFolder "version_history.txt"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $historyFile -Value "$newVersion - Built on $timestamp"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Building executable..." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Find spec file (prefer deploy/, fallback project root)
$deploySpec = Join-Path $PSScriptRoot "vm_controller.spec"
$rootSpec = Join-Path $projectRoot "vm_controller.spec"

if (Test-Path $deploySpec) {
    $specFile = $deploySpec
} elseif (Test-Path $rootSpec) {
    $specFile = $rootSpec
} else {
    Write-Host "Spec file not found. Creating one from controller_api.py..." -ForegroundColor Yellow
    Push-Location $projectRoot
    & $pythonExe -m PyInstaller --onefile --name vm_controller --specpath $projectRoot --add-data "deploy/version.txt;." controller_api.py --noconfirm
    $specGenExitCode = $LASTEXITCODE
    Pop-Location
    if ($specGenExitCode -ne 0) {
        Write-Host "[ERROR] Failed to generate spec file" -ForegroundColor Red
        exit 1
    }
    if (Test-Path $rootSpec) {
        $specFile = $rootSpec
    } else {
        Write-Host "[ERROR] Failed to create vm_controller.spec" -ForegroundColor Red
        exit 1
    }
}

# Build with PyInstaller
Push-Location $projectRoot
& $pythonExe -m PyInstaller $specFile --noconfirm --clean --distpath $distFolder --workpath $buildFolder
$buildExitCode = $LASTEXITCODE
Pop-Location

if ($buildExitCode -eq 0) {
    $latestExe = Join-Path $distFolder "vm_controller.exe"
    $versionedExe = Join-Path $distFolder "vm_controller-$newVersion.exe"

    if (Test-Path $latestExe) {
        Copy-Item -Path $latestExe -Destination $versionedExe -Force
    }

    Write-Host "`n============================================================" -ForegroundColor Green
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "`nVersion:  $newVersion" -ForegroundColor White
    Write-Host "Latest:   $distFolder\vm_controller.exe" -ForegroundColor White
    Write-Host "Tagged:   $distFolder\vm_controller-$newVersion.exe" -ForegroundColor White
    Write-Host "History:  $historyFile" -ForegroundColor White
    Write-Host "`n============================================================`n" -ForegroundColor Green
} else {
    Write-Host "`n============================================================" -ForegroundColor Red
    Write-Host "Build failed!" -ForegroundColor Red
    Write-Host "============================================================`n" -ForegroundColor Red
    exit 1
}
