# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TwitterScraper
Build with: pyinstaller TwitterScraper.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# =============================================================================
# FIX FOR TKINTER TCL/TK DATA FILES
# =============================================================================
import tkinter
import _tkinter

# Find Tcl/Tk data directories
TCL_LIBRARY = os.environ.get('TCL_LIBRARY', '')
TK_LIBRARY = os.environ.get('TK_LIBRARY', '')

# Try to find from tkinter if env vars not set
if not TCL_LIBRARY or not TK_LIBRARY:
    try:
        root = tkinter.Tk()
        TCL_LIBRARY = root.tk.exprstring('$tcl_library')
        TK_LIBRARY = root.tk.exprstring('$tk_library')
        root.destroy()
    except:
        pass

# Build tcl/tk data paths
tcl_tk_datas = []
if TCL_LIBRARY and os.path.isdir(TCL_LIBRARY):
    tcl_tk_datas.append((TCL_LIBRARY, '_tcl_data'))
if TK_LIBRARY and os.path.isdir(TK_LIBRARY):
    tcl_tk_datas.append((TK_LIBRARY, '_tk_data'))

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================

# Collect hidden imports for libraries that dynamically import modules
hiddenimports = [
    # Tkinter (required for customtkinter)
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    '_tkinter',
    # CustomTkinter
    'customtkinter',
    # Other dependencies
    'yt_dlp',
    'ijson',
    'ijson.backends',
    'ijson.backends.python',
    'PIL',
    'PIL.Image',
    'PIL._tkinter_finder',
    'reportlab',
    'reportlab.platypus',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.units',
    'reportlab.lib.enums',
    'reportlab.platypus.doctemplate',
    'reportlab.platypus.flowables',
    'reportlab.platypus.paragraph',
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.common',
    'selenium.webdriver.common.by',
    'selenium.webdriver.common.keys',
    'selenium.webdriver.support',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'undetected_chromedriver',
]

# Collect all submodules for complex packages
hiddenimports += collect_submodules('customtkinter')
hiddenimports += collect_submodules('reportlab')

# Collect data files for customtkinter (themes, assets)
datas = collect_data_files('customtkinter')

# Add Tcl/Tk data directories
datas += tcl_tk_datas

a = Analysis(
    ['panel.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TwitterScraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging (shows console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add path to .ico file if you have one: icon='icon.ico'
)
