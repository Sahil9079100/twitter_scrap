# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TwitterScraper
Build with: pyinstaller TwitterScraper.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

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
