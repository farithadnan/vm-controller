# VM Controller Build Script with Auto-Versioning
# Usage: .\build.ps1 [major|minor|patch]

param(
    [ValidateSet('major', 'minor', 'patch')]
    [string]$VersionType = 'patch'
)

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "VM Controller - Build & Deploy" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

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

# Copy version to dist for tracking
$distFolder = Join-Path $PSScriptRoot "dist"
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

# Build with PyInstaller
pyinstaller vm_controller.spec --noconfirm --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n============================================================" -ForegroundColor Green
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "`nVersion:  $newVersion" -ForegroundColor White
    Write-Host "Location: $distFolder\vm_controller.exe" -ForegroundColor White
    Write-Host "History:  $historyFile" -ForegroundColor White
    Write-Host "`n============================================================`n" -ForegroundColor Green
} else {
    Write-Host "`n============================================================" -ForegroundColor Red
    Write-Host "Build failed!" -ForegroundColor Red
    Write-Host "============================================================`n" -ForegroundColor Red
    exit 1
}
