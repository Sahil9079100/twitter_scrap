# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TwitterScraper (ONEFILE MODE)

IMPORTANT: 
1. First test with TwitterScraper.spec (onedir mode)
2. Only use this after onedir mode works correctly

Build with:
    pyinstaller --clean --noconfirm TwitterScraper_onefile.spec
"""

import os
import sys

# =============================================================================
# EXPLICIT TCL/TK PATHS (CRITICAL - DO NOT MODIFY)
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(SPEC))

tcl_src = os.path.join(SCRIPT_DIR, 'build_assets', 'tcl', 'tcl8.6')
tk_src = os.path.join(SCRIPT_DIR, 'build_assets', 'tcl', 'tk8.6')

# Verify Tcl/Tk directories exist
if not os.path.isdir(tcl_src):
    print(f"[ERROR] Tcl directory not found: {tcl_src}")
    print("[ERROR] Run 'python copy_tcl_tk.py' first!")
    sys.exit(1)

if not os.path.isdir(tk_src):
    print(f"[ERROR] Tk directory not found: {tk_src}")
    print("[ERROR] Run 'python copy_tcl_tk.py' first!")
    sys.exit(1)

tcl_init = os.path.join(tcl_src, 'init.tcl')
if not os.path.isfile(tcl_init):
    print(f"[ERROR] init.tcl not found!")
    sys.exit(1)

print(f"[SPEC] Tcl source: {tcl_src}")
print(f"[SPEC] Tk source: {tk_src}")

# =============================================================================
# DATA FILES
# =============================================================================
datas = [
    (tcl_src, '_tcl_data'),
    (tk_src, '_tk_data'),
]

try:
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    datas.append((ctk_path, 'customtkinter'))
    print(f"[SPEC] CustomTkinter: {ctk_path}")
except ImportError:
    print("[WARNING] customtkinter not installed")

try:
    import certifi
    cert_dir = os.path.dirname(certifi.where())
    datas.append((cert_dir, 'certifi'))
except ImportError:
    pass

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================
hiddenimports = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.font', '_tkinter', 'customtkinter',
    'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL._tkinter_finder',
    'yt_dlp', 'ijson', 'ijson.backends', 'ijson.backends.python',
    'reportlab', 'reportlab.platypus', 'reportlab.lib', 'reportlab.pdfbase',
    'selenium', 'selenium.webdriver', 'selenium.webdriver.common',
    'selenium.webdriver.support', 'selenium.webdriver.chrome',
    'undetected_chromedriver', 'requests', 'urllib3', 'certifi', 'websockets',
]

# =============================================================================
# ANALYSIS
# =============================================================================
a = Analysis(
    ['panel.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'PyQt5', 'PyQt6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# =============================================================================
# BUNDLE (ONEFILE MODE)
# =============================================================================
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,            # Include binaries for onefile
    a.zipfiles,            # Include zipfiles for onefile
    a.datas,               # Include datas for onefile
    [],
    name='TwitterScraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,         # No console for release
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
