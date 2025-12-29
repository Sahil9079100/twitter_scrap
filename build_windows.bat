@echo off
REM ============================================
REM TwitterScraper Windows Build Script (Batch)
REM ============================================
REM
REM Usage: 
REM   build_windows.bat           (build onedir for testing)
REM   build_windows.bat onefile   (build single exe for release)
REM   build_windows.bat clean     (clean build artifacts first)
REM
REM IMPORTANT: Run copy_tcl_tk.py ONCE before first build!
REM
REM Requires: Python 3.9+ from python.org (NOT MS Store, NOT Anaconda)

setlocal enabledelayedexpansion

echo ========================================
echo   TwitterScraper Windows Build Script
echo ========================================
echo.

REM Check for arguments
set "ONEFILE_MODE=0"
set "CLEAN_MODE=0"
if /i "%1"=="onefile" set "ONEFILE_MODE=1"
if /i "%1"=="clean" set "CLEAN_MODE=1"
if /i "%2"=="onefile" set "ONEFILE_MODE=1"
if /i "%2"=="clean" set "CLEAN_MODE=1"

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo [ERROR] Install Python 3.9+ from python.org
    echo [ERROR] DO NOT use MS Store Python or Anaconda!
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Found: %PYVER%

REM Check if Tcl/Tk has been copied
if not exist "build_assets\tcl\tcl8.6\init.tcl" (
    echo.
    echo [ERROR] Tcl/Tk files not found!
    echo [ERROR] Run this command first:
    echo.
    echo     python copy_tcl_tk.py
    echo.
    exit /b 1
)
echo [OK] Tcl/Tk files found in build_assets

REM Clean if requested
if "%CLEAN_MODE%"=="1" (
    echo [INFO] Cleaning previous build artifacts...
    if exist build rmdir /s /q build
    if exist dist rmdir /s /q dist
    if exist .build_venv rmdir /s /q .build_venv
)

REM Create virtual environment
if not exist .build_venv (
    echo [INFO] Creating virtual environment...
    python -m venv .build_venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .build_venv\Scripts\activate.bat

REM Upgrade pip and install dependencies
echo [INFO] Installing dependencies...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

echo [INFO] Dependencies installed successfully.
echo.

REM Build exe
if "%ONEFILE_MODE%"=="1" (
    echo [INFO] Building ONEFILE executable (release mode)...
    pyinstaller --clean --noconfirm TwitterScraper_onefile.spec
    
    if exist dist\TwitterScraper.exe (
        echo.
        echo ========================================
        echo   BUILD SUCCESSFUL! (ONEFILE)
        echo ========================================
        echo.
        echo Executable: dist\TwitterScraper.exe
        echo.
        echo This is the release build - single file, no console.
    ) else (
        echo [ERROR] Build failed!
        exit /b 1
    )
) else (
    echo [INFO] Building ONEDIR executable (test mode)...
    pyinstaller --clean --noconfirm TwitterScraper.spec
    
    if exist dist\TwitterScraper\TwitterScraper.exe (
        echo.
        echo ========================================
        echo   BUILD SUCCESSFUL! (ONEDIR)
        echo ========================================
        echo.
        echo Executable: dist\TwitterScraper\TwitterScraper.exe
        echo.
        echo NEXT STEPS:
        echo   1. Test the exe by running it
        echo   2. Verify _tcl_data and _tk_data folders exist in dist\TwitterScraper\
        echo   3. If it works, build release with: build_windows.bat onefile
    ) else (
        echo [ERROR] Build failed!
        exit /b 1
    )
)

REM Deactivate venv
call deactivate

endlocal
