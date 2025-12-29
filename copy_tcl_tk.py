#!/usr/bin/env python3
"""
Tcl/Tk Copy Script for PyInstaller Bundling

Run this script ONCE on Windows before building the exe.
It copies the Tcl/Tk data directories into build_assets/tcl/

Usage:
    python copy_tcl_tk.py

This script:
1. Locates the Tcl/Tk directories from your Python installation
2. Copies them to build_assets/tcl/tcl8.6 and build_assets/tcl/tk8.6
3. Verifies the copy was successful
"""

import os
import sys
import shutil
import tkinter


def find_tcl_tk_source():
    """
    Find the Tcl/Tk source directories from the current Python installation.
    
    Returns:
        tuple: (tcl_dir, tk_dir) paths or (None, None) if not found
    """
    # Get Python installation directory
    python_dir = sys.prefix
    print(f"[INFO] Python installation: {python_dir}")
    print(f"[INFO] tkinter module: {tkinter.__file__}")
    
    # Standard location for Windows Python
    tcl_base = os.path.join(python_dir, 'tcl')
    
    tcl_dir = None
    tk_dir = None
    
    # Look for tcl8.6 and tk8.6
    if os.path.isdir(tcl_base):
        for name in os.listdir(tcl_base):
            full_path = os.path.join(tcl_base, name)
            if name.startswith('tcl8') and os.path.isdir(full_path):
                tcl_dir = full_path
                print(f"[FOUND] Tcl directory: {tcl_dir}")
            elif name.startswith('tk8') and os.path.isdir(full_path):
                tk_dir = full_path
                print(f"[FOUND] Tk directory: {tk_dir}")
    
    # Fallback: Try to get from tkinter itself
    if not tcl_dir or not tk_dir:
        print("[INFO] Trying fallback: querying tkinter directly...")
        try:
            root = tkinter.Tk()
            root.withdraw()  # Hide the window
            
            tcl_library = root.tk.exprstring('$tcl_library')
            tk_library = root.tk.exprstring('$tk_library')
            root.destroy()
            
            if tcl_library and os.path.isdir(tcl_library):
                tcl_dir = tcl_library
                print(f"[FOUND] Tcl directory (from tkinter): {tcl_dir}")
            if tk_library and os.path.isdir(tk_library):
                tk_dir = tk_library
                print(f"[FOUND] Tk directory (from tkinter): {tk_dir}")
        except Exception as e:
            print(f"[WARNING] Could not query tkinter: {e}")
    
    return tcl_dir, tk_dir


def verify_tcl_directory(path):
    """Verify that a Tcl directory is valid (contains init.tcl)."""
    if not path or not os.path.isdir(path):
        return False
    init_tcl = os.path.join(path, 'init.tcl')
    return os.path.isfile(init_tcl)


def verify_tk_directory(path):
    """Verify that a Tk directory is valid (contains tk.tcl)."""
    if not path or not os.path.isdir(path):
        return False
    tk_tcl = os.path.join(path, 'tk.tcl')
    return os.path.isfile(tk_tcl)


def copy_directory(src, dst):
    """Copy a directory, removing destination first if it exists."""
    if os.path.exists(dst):
        print(f"[INFO] Removing existing: {dst}")
        shutil.rmtree(dst)
    
    print(f"[COPY] {src}")
    print(f"    -> {dst}")
    shutil.copytree(src, dst)
    
    # Count files copied
    file_count = sum(len(files) for _, _, files in os.walk(dst))
    print(f"[OK] Copied {file_count} files")


def main():
    print("=" * 60)
    print("  Tcl/Tk Copy Script for PyInstaller")
    print("=" * 60)
    print()
    
    # Get script directory (project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    build_assets = os.path.join(script_dir, 'build_assets', 'tcl')
    
    # Create build_assets/tcl if it doesn't exist
    os.makedirs(build_assets, exist_ok=True)
    
    # Find Tcl/Tk source directories
    tcl_src, tk_src = find_tcl_tk_source()
    
    # Validate Tcl
    if not verify_tcl_directory(tcl_src):
        print()
        print("[ERROR] Could not find valid Tcl directory!")
        print("        Expected init.tcl inside the Tcl folder.")
        print()
        print("Possible causes:")
        print("  - Using MS Store Python (not supported)")
        print("  - Using Anaconda/Miniconda (not supported)")
        print("  - Corrupted Python installation")
        print()
        print("Solution: Install standard Python from python.org")
        sys.exit(1)
    
    # Validate Tk
    if not verify_tk_directory(tk_src):
        print()
        print("[ERROR] Could not find valid Tk directory!")
        print("        Expected tk.tcl inside the Tk folder.")
        sys.exit(1)
    
    print()
    
    # Define destination paths
    tcl_dst = os.path.join(build_assets, 'tcl8.6')
    tk_dst = os.path.join(build_assets, 'tk8.6')
    
    # Copy directories
    print("[STEP] Copying Tcl/Tk to build_assets...")
    print()
    
    copy_directory(tcl_src, tcl_dst)
    copy_directory(tk_src, tk_dst)
    
    print()
    
    # Final verification
    print("[STEP] Verifying copied files...")
    
    tcl_init = os.path.join(tcl_dst, 'init.tcl')
    tk_init = os.path.join(tk_dst, 'tk.tcl')
    
    if os.path.isfile(tcl_init) and os.path.isfile(tk_init):
        print("[OK] init.tcl found in tcl8.6")
        print("[OK] tk.tcl found in tk8.6")
        print()
        print("=" * 60)
        print("  SUCCESS! Tcl/Tk files are ready for bundling.")
        print("=" * 60)
        print()
        print("Next step: Run the build script")
        print("  .\\build_windows.bat")
        print("  or")
        print("  .\\build_windows.ps1")
    else:
        print("[ERROR] Verification failed!")
        if not os.path.isfile(tcl_init):
            print(f"        Missing: {tcl_init}")
        if not os.path.isfile(tk_init):
            print(f"        Missing: {tk_init}")
        sys.exit(1)


if __name__ == '__main__':
    main()
