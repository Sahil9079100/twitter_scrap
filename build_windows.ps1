<#
.SYNOPSIS
    Build TwitterScraper Windows executable using PyInstaller.

.DESCRIPTION
    This script:
    1. Creates a fresh virtual environment
    2. Installs all dependencies
    3. Builds the .exe using PyInstaller
    4. Outputs the exe to the dist/ folder

.NOTES
    Run from PowerShell:  .\build_windows.ps1
    Requires: Python 3.9+ installed and in PATH
#>

param(
    [switch]$Debug,      # Build with console window visible for debugging
    [switch]$Clean       # Clean build artifacts before building
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TwitterScraper Windows Build Script  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found in PATH. Please install Python 3.9+ and try again." -ForegroundColor Red
    exit 1
}

# Clean previous builds if requested
if ($Clean) {
    Write-Host "[INFO] Cleaning previous build artifacts..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path ".build_venv") { Remove-Item -Recurse -Force ".build_venv" }
}

# Create virtual environment for build
$venvPath = ".build_venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
. $activateScript

# Upgrade pip
Write-Host "[INFO] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

Write-Host "[INFO] Dependencies installed successfully." -ForegroundColor Green

# Build exe
Write-Host ""
Write-Host "[INFO] Building executable..." -ForegroundColor Yellow

if ($Debug) {
    Write-Host "[DEBUG] Building with console window enabled for debugging..." -ForegroundColor Magenta
    # Modify spec temporarily for debug build
    pyinstaller --clean --noconfirm `
        --onefile `
        --name "TwitterScraper" `
        --add-data "$(python -c 'import customtkinter; print(customtkinter.__path__[0])');customtkinter" `
        --hidden-import customtkinter `
        --hidden-import yt_dlp `
        --hidden-import ijson `
        --hidden-import ijson.backends.python `
        --hidden-import PIL `
        --hidden-import reportlab `
        --hidden-import selenium `
        --hidden-import undetected_chromedriver `
        --console `
        panel.py
} else {
    # Use spec file for production build
    pyinstaller --clean --noconfirm TwitterScraper.spec
}

# Check if build succeeded
$exePath = Join-Path "dist" "TwitterScraper.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executable: $exePath" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To run: double-click the exe or run from terminal:" -ForegroundColor Yellow
    Write-Host "  .\dist\TwitterScraper.exe" -ForegroundColor White
    Write-Host ""
    Write-Host "Config/logs will be saved to:" -ForegroundColor Yellow
    Write-Host "  %APPDATA%\TwitterScraper\" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "[ERROR] Build failed - exe not found at $exePath" -ForegroundColor Red
    Write-Host "Check the output above for errors." -ForegroundColor Red
    exit 1
}

# Deactivate venv
deactivate
