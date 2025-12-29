# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TwitterScraper

IMPORTANT: Before building, run copy_tcl_tk.py to copy Tcl/Tk files!

Build with:
    pyinstaller --clean --noconfirm TwitterScraper.spec

This spec file uses EXPLICIT paths for Tcl/Tk bundling.
No auto-detection. No hooks. Just deterministic bundling.
"""

import os
import sys

# =============================================================================
# EXPLICIT TCL/TK PATHS (CRITICAL - DO NOT MODIFY)
# =============================================================================
# These paths point to pre-copied Tcl/Tk directories in build_assets/
# The destination names MUST be exactly '_tcl_data' and '_tk_data'
# PyInstaller's pyi_rth_tkinter hook expects these exact names

SCRIPT_DIR = os.path.dirname(os.path.abspath(SPEC))

tcl_src = os.path.join(SCRIPT_DIR, 'build_assets', 'tcl', 'tcl8.6')
tk_src = os.path.join(SCRIPT_DIR, 'build_assets', 'tcl', 'tk8.6')

# Verify Tcl/Tk directories exist before building
if not os.path.isdir(tcl_src):
    print(f"[ERROR] Tcl directory not found: {tcl_src}")
    print("[ERROR] Run 'python copy_tcl_tk.py' first!")
    sys.exit(1)

if not os.path.isdir(tk_src):
    print(f"[ERROR] Tk directory not found: {tk_src}")
    print("[ERROR] Run 'python copy_tcl_tk.py' first!")
    sys.exit(1)

# Verify init.tcl exists (critical file)
tcl_init = os.path.join(tcl_src, 'init.tcl')
if not os.path.isfile(tcl_init):
    print(f"[ERROR] init.tcl not found in Tcl directory!")
    print(f"[ERROR] Expected: {tcl_init}")
    sys.exit(1)

print(f"[SPEC] Tcl source: {tcl_src}")
print(f"[SPEC] Tk source: {tk_src}")

# =============================================================================
# DATA FILES
# =============================================================================
# Critical: Destination names MUST be '_tcl_data' and '_tk_data'
# These are hardcoded in PyInstaller's pyi_rth_tkinter runtime hook

datas = [
    (tcl_src, '_tcl_data'),
    (tk_src, '_tk_data'),
]

# Add customtkinter data files (themes, assets)
try:
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    datas.append((ctk_path, 'customtkinter'))
    print(f"[SPEC] CustomTkinter: {ctk_path}")
except ImportError:
    print("[WARNING] customtkinter not installed")

# Add certifi certificates (for HTTPS requests)
try:
    import certifi
    cert_dir = os.path.dirname(certifi.where())
    datas.append((cert_dir, 'certifi'))
    print(f"[SPEC] Certifi: {cert_dir}")
except ImportError:
    print("[WARNING] certifi not installed")

print(f"[SPEC] Total data entries: {len(datas)}")

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================
hiddenimports = [
    # Tkinter core (required)
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.font',
    '_tkinter',
    
    # CustomTkinter
    'customtkinter',
    
    # PIL/Pillow
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    
    # yt-dlp
    'yt_dlp',
    
    # ijson
    'ijson',
    'ijson.backends',
    'ijson.backends.python',
    
    # reportlab (PDF generation)
    'reportlab',
    'reportlab.platypus',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.pdfbase',
    'reportlab.pdfgen',
    
    # Selenium
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.common',
    'selenium.webdriver.common.by',
    'selenium.webdriver.common.keys',
    'selenium.webdriver.support',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.chrome',
    
    # undetected-chromedriver
    'undetected_chromedriver',
    
    # Network
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    
    # websockets
    'websockets',
]

print(f"[SPEC] Hidden imports: {len(hiddenimports)}")

# =============================================================================
# ANALYSIS
# =============================================================================
a = Analysis(
    ['panel.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],          # No custom hooks - we handle everything explicitly
    hooksconfig={},
    runtime_hooks=[],      # No runtime hooks needed
    excludes=[
        'matplotlib',
        'numpy', 
        'scipy', 
        'pandas',
        'PyQt5', 
        'PyQt6', 
        'PySide2', 
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# =============================================================================
# BUNDLE (ONEDIR MODE - for testing)
# =============================================================================
# Use --onedir first to verify the bundle is correct
# Only switch to --onefile after onedir works

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],                    # Empty for onedir mode
    exclude_binaries=True, # Required for onedir mode
    name='TwitterScraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,          # Keep True for debugging, change to False for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TwitterScraper',
)
