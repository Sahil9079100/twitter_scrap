<#
.SYNOPSIS
    Build TwitterScraper Windows executable using PyInstaller.

.DESCRIPTION
    This script:
    1. Verifies Tcl/Tk files are present (run copy_tcl_tk.py first!)
    2. Creates a virtual environment
    3. Installs all dependencies
    4. Builds the .exe using PyInstaller

.NOTES
    Run from PowerShell:
      .\build_windows.ps1           (build onedir for testing)
      .\build_windows.ps1 -OneFile  (build single exe for release)
      .\build_windows.ps1 -Clean    (clean first)

    IMPORTANT: Run copy_tcl_tk.py ONCE before first build!
    
    Requires: Python 3.9+ from python.org (NOT MS Store, NOT Anaconda)
#>

param(
    [switch]$OneFile,    # Build single exe (use after onedir works)
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
    Write-Host "[ERROR] Python not found in PATH." -ForegroundColor Red
    Write-Host "[ERROR] Install Python 3.9+ from python.org" -ForegroundColor Red
    Write-Host "[ERROR] DO NOT use MS Store Python or Anaconda!" -ForegroundColor Red
    exit 1
}

# Check if Tcl/Tk has been copied
$tclInit = "build_assets\tcl\tcl8.6\init.tcl"
if (-not (Test-Path $tclInit)) {
    Write-Host ""
    Write-Host "[ERROR] Tcl/Tk files not found!" -ForegroundColor Red
    Write-Host "[ERROR] Run this command first:" -ForegroundColor Red
    Write-Host ""
    Write-Host "    python copy_tcl_tk.py" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
Write-Host "[OK] Tcl/Tk files found in build_assets" -ForegroundColor Green

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
Write-Host ""

# Build exe
if ($OneFile) {
    Write-Host "[INFO] Building ONEFILE executable (release mode)..." -ForegroundColor Yellow
    pyinstaller --clean --noconfirm TwitterScraper_onefile.spec
    
    $exePath = "dist\TwitterScraper.exe"
    if (Test-Path $exePath) {
        $exeSize = (Get-Item $exePath).Length / 1MB
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  BUILD SUCCESSFUL! (ONEFILE)" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Executable: $exePath" -ForegroundColor Cyan
        Write-Host "Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "This is the release build - single file, no console." -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] Build failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[INFO] Building ONEDIR executable (test mode)..." -ForegroundColor Yellow
    pyinstaller --clean --noconfirm TwitterScraper.spec
    
    $exePath = "dist\TwitterScraper\TwitterScraper.exe"
    if (Test-Path $exePath) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  BUILD SUCCESSFUL! (ONEDIR)" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Executable: $exePath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "NEXT STEPS:" -ForegroundColor Yellow
        Write-Host "  1. Test the exe by running it" -ForegroundColor White
        Write-Host "  2. Verify _tcl_data and _tk_data folders exist in dist\TwitterScraper\" -ForegroundColor White
        Write-Host "  3. If it works, build release with: .\build_windows.ps1 -OneFile" -ForegroundColor White
    } else {
        Write-Host "[ERROR] Build failed!" -ForegroundColor Red
        exit 1
    }
}

# Deactivate venv
deactivate
