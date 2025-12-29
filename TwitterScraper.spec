# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for TwitterScraper
Build with: pyinstaller --clean --noconfirm TwitterScraper.spec

This spec file handles all edge cases for bundling:
- Tcl/Tk data files (required for tkinter)
- CustomTkinter themes and assets
- All hidden imports
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# =============================================================================
# FIND TCL/TK DATA DIRECTORIES (ROBUST METHOD)
# =============================================================================
def find_tcl_tk():
    """
    Find Tcl/Tk data directories from multiple possible locations.
    Returns list of (source_path, dest_path) tuples.
    """
    result = []
    python_dir = sys.prefix
    
    print(f"[SPEC] Python prefix: {python_dir}")
    
    # Common locations for Tcl/Tk on Windows
    search_paths = [
        # Standard Python installation
        (os.path.join(python_dir, 'tcl', 'tcl8.6'), 'tcl8.6'),
        (os.path.join(python_dir, 'tcl', 'tk8.6'), 'tk8.6'),
        (os.path.join(python_dir, 'tcl', 'tcl8'), 'tcl8'),
        (os.path.join(python_dir, 'tcl', 'tk8'), 'tk8'),
        # Anaconda/Miniconda
        (os.path.join(python_dir, 'Library', 'lib', 'tcl8.6'), 'tcl8.6'),
        (os.path.join(python_dir, 'Library', 'lib', 'tk8.6'), 'tk8.6'),
        (os.path.join(python_dir, 'Library', 'lib', 'tcl8'), 'tcl8'),
        (os.path.join(python_dir, 'Library', 'lib', 'tk8'), 'tk8'),
        # Some virtual env setups - check parent
        (os.path.join(os.path.dirname(python_dir), 'tcl', 'tcl8.6'), 'tcl8.6'),
        (os.path.join(os.path.dirname(python_dir), 'tcl', 'tk8.6'), 'tk8.6'),
    ]
    
    for src, dest in search_paths:
        if os.path.isdir(src):
            result.append((src, dest))
            print(f"[SPEC] Found Tcl/Tk: {src} -> {dest}")
    
    # Try to get from tkinter directly as fallback
    if not result:
        try:
            import tkinter
            root = tkinter.Tk()
            tcl_lib = root.tk.exprstring('$tcl_library')
            tk_lib = root.tk.exprstring('$tk_library')
            root.destroy()
            
            if tcl_lib and os.path.isdir(tcl_lib):
                dest = os.path.basename(tcl_lib)
                result.append((tcl_lib, dest))
                print(f"[SPEC] Found from tkinter: {tcl_lib} -> {dest}")
            if tk_lib and os.path.isdir(tk_lib):
                dest = os.path.basename(tk_lib)
                result.append((tk_lib, dest))
                print(f"[SPEC] Found from tkinter: {tk_lib} -> {dest}")
        except Exception as e:
            print(f"[SPEC] Warning: Could not get Tcl/Tk from tkinter: {e}")
    
    return result

def find_tcl_tk_dlls():
    """Find Tcl/Tk DLLs that need to be included."""
    result = []
    python_dir = sys.prefix
    
    dll_paths = [
        os.path.join(python_dir, 'DLLs'),
        os.path.join(python_dir, 'Library', 'bin'),
        python_dir,
    ]
    
    for dll_dir in dll_paths:
        if os.path.isdir(dll_dir):
            for f in os.listdir(dll_dir):
                fl = f.lower()
                if (fl.startswith(('tcl8', 'tk8', 'tcl9', 'tk9')) and 
                    fl.endswith(('.dll', '.pyd'))):
                    src = os.path.join(dll_dir, f)
                    result.append((src, '.'))
                    print(f"[SPEC] Found DLL: {src}")
    
    return result

tcl_tk_data = find_tcl_tk()
tcl_tk_dlls = find_tcl_tk_dlls()

# =============================================================================
# HIDDEN IMPORTS
# =============================================================================
hiddenimports = [
    # Tkinter core
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.font',
    'tkinter.colorchooser',
    'tkinter.commondialog',
    'tkinter.simpledialog',
    '_tkinter',
    
    # CustomTkinter
    'customtkinter',
    
    # PIL/Pillow with Tk support
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
    
    # reportlab
    'reportlab',
    'reportlab.platypus',
    'reportlab.platypus.doctemplate',
    'reportlab.platypus.flowables',
    'reportlab.platypus.paragraph',
    'reportlab.platypus.tables',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.units',
    'reportlab.lib.enums',
    'reportlab.pdfbase',
    'reportlab.pdfbase.pdfmetrics',
    'reportlab.pdfbase.ttfonts',
    'reportlab.pdfgen',
    'reportlab.pdfgen.canvas',
    
    # Selenium
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.common',
    'selenium.webdriver.common.by',
    'selenium.webdriver.common.keys',
    'selenium.webdriver.support',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'selenium.webdriver.chrome',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    
    # undetected-chromedriver
    'undetected_chromedriver',
    
    # Network/HTTP
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    
    # websockets (used by selenium/uc)
    'websockets',
    'websockets.client',
    'websockets.legacy',
    'websockets.legacy.client',
]

# Collect all submodules for complex packages
print("[SPEC] Collecting submodules...")
hiddenimports += collect_submodules('customtkinter')
hiddenimports += collect_submodules('reportlab')
hiddenimports += collect_submodules('yt_dlp')

# Remove duplicates
hiddenimports = list(set(hiddenimports))
print(f"[SPEC] Total hidden imports: {len(hiddenimports)}")

# =============================================================================
# DATA FILES
# =============================================================================
datas = []

# Add Tcl/Tk data directories
datas += tcl_tk_data

# Add customtkinter data files (themes, assets)
print("[SPEC] Collecting customtkinter data...")
datas += collect_data_files('customtkinter')

# Add certifi certificates (for HTTPS requests)
try:
    import certifi
    cert_path = certifi.where()
    cert_dir = os.path.dirname(cert_path)
    datas.append((cert_dir, 'certifi'))
    print(f"[SPEC] Added certifi: {cert_dir}")
except ImportError:
    print("[SPEC] Warning: certifi not found")

print(f"[SPEC] Total data entries: {len(datas)}")

# =============================================================================
# BINARIES
# =============================================================================
binaries = tcl_tk_dlls

# =============================================================================
# RUNTIME HOOKS - Set TCL/TK paths at runtime
# =============================================================================
# Create a runtime hook to set environment variables
runtime_hook_content = '''
import os
import sys

# Set Tcl/Tk environment variables for frozen app
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    
    # Try different possible locations
    tcl_candidates = ['tcl8.6', 'tcl8', 'tcl']
    tk_candidates = ['tk8.6', 'tk8', 'tk']
    
    for tcl in tcl_candidates:
        tcl_path = os.path.join(base_path, tcl)
        if os.path.isdir(tcl_path):
            os.environ['TCL_LIBRARY'] = tcl_path
            break
    
    for tk in tk_candidates:
        tk_path = os.path.join(base_path, tk)
        if os.path.isdir(tk_path):
            os.environ['TK_LIBRARY'] = tk_path
            break
'''

runtime_hook_path = os.path.join(os.path.dirname(os.path.abspath('panel.py')), 'pyi_rth_tkpath.py')
with open(runtime_hook_path, 'w') as f:
    f.write(runtime_hook_content)
print(f"[SPEC] Created runtime hook: {runtime_hook_path}")

# =============================================================================
# ANALYSIS
# =============================================================================
a = Analysis(
    ['panel.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[runtime_hook_path],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',  # Unused heavy packages
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',    # Other GUI frameworks
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# =============================================================================
# BUNDLE
# =============================================================================
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
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
