@echo off
REM ============================================
REM TwitterScraper Windows Build Script (Batch)
REM ============================================
REM
REM Usage: build_windows.bat
REM        build_windows.bat debug   (builds with console visible)
REM        build_windows.bat clean   (cleans build artifacts first)
REM
REM Requires: Python 3.9+ in PATH

setlocal enabledelayedexpansion

echo ========================================
echo   TwitterScraper Windows Build Script
echo ========================================
echo.

REM Check for arguments
set "DEBUG_MODE=0"
set "CLEAN_MODE=0"
if /i "%1"=="debug" set "DEBUG_MODE=1"
if /i "%1"=="clean" set "CLEAN_MODE=1"
if /i "%2"=="debug" set "DEBUG_MODE=1"
if /i "%2"=="clean" set "CLEAN_MODE=1"

REM Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Please install Python 3.9+ and try again.
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Found: %PYVER%

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
echo [INFO] Building executable...

if "%DEBUG_MODE%"=="1" (
    echo [DEBUG] Building with console window enabled...
    pyinstaller --clean --noconfirm --onefile --name "TwitterScraper" --console ^
        --hidden-import tkinter ^
        --hidden-import tkinter.ttk ^
        --hidden-import tkinter.filedialog ^
        --hidden-import _tkinter ^
        --hidden-import customtkinter ^
        --hidden-import yt_dlp ^
        --hidden-import ijson ^
        --hidden-import ijson.backends.python ^
        --hidden-import PIL ^
        --hidden-import PIL._tkinter_finder ^
        --hidden-import reportlab ^
        --hidden-import selenium ^
        --hidden-import undetected_chromedriver ^
        --collect-all customtkinter ^
        panel.py
) else (
    pyinstaller --clean --noconfirm TwitterScraper.spec
)

REM Check if build succeeded
if exist dist\TwitterScraper.exe (
    echo.
    echo ========================================
    echo   BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable: dist\TwitterScraper.exe
    echo.
    echo To run: double-click the exe or run from terminal:
    echo   dist\TwitterScraper.exe
    echo.
    echo Config/logs will be saved to:
    echo   %%APPDATA%%\TwitterScraper\
) else (
    echo.
    echo [ERROR] Build failed - exe not found at dist\TwitterScraper.exe
    echo Check the output above for errors.
    exit /b 1
)

REM Deactivate venv
call deactivate

endlocal
