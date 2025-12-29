# Custom PyInstaller hook for tkinter
# This ensures Tcl/Tk data files are properly bundled

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = ['tkinter', 'tkinter.ttk', 'tkinter.filedialog', '_tkinter']
datas = []

def get_tcl_tk_paths():
    """Find Tcl/Tk data directories from multiple possible locations."""
    paths = []
    
    # Method 1: From environment variables
    tcl_lib = os.environ.get('TCL_LIBRARY')
    tk_lib = os.environ.get('TK_LIBRARY')
    if tcl_lib and os.path.isdir(tcl_lib):
        paths.append((tcl_lib, 'tcl'))
    if tk_lib and os.path.isdir(tk_lib):
        paths.append((tk_lib, 'tk'))
    
    # Method 2: From Python's sys.prefix (most common on Windows)
    python_dir = sys.prefix
    tcl_dirs = [
        os.path.join(python_dir, 'tcl', 'tcl8.6'),
        os.path.join(python_dir, 'tcl', 'tk8.6'),
        os.path.join(python_dir, 'Lib', 'tkinter'),
        os.path.join(python_dir, 'Library', 'lib', 'tcl8.6'),
        os.path.join(python_dir, 'Library', 'lib', 'tk8.6'),
    ]
    
    for d in tcl_dirs:
        if os.path.isdir(d):
            base = os.path.basename(d)
            paths.append((d, base))
    
    # Method 3: Try to get from tkinter itself
    try:
        import tkinter
        root = tkinter.Tk()
        tcl_library = root.tk.exprstring('$tcl_library')
        tk_library = root.tk.exprstring('$tk_library')
        root.destroy()
        
        if tcl_library and os.path.isdir(tcl_library):
            paths.append((tcl_library, 'tcl8.6'))
        if tk_library and os.path.isdir(tk_library):
            paths.append((tk_library, 'tk8.6'))
    except Exception:
        pass
    
    return paths

datas = get_tcl_tk_paths()
