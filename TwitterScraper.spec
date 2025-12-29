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
    'customtkinter',
    'yt_dlp',
    'ijson',
    'ijson.backends',
    'ijson.backends.python',
    'PIL',
    'PIL.Image',
    'reportlab',
    'reportlab.platypus',
    'reportlab.lib',
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.common',
    'selenium.webdriver.support',
    'undetected_chromedriver',
]

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
