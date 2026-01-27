#!/usr/bin/env python3
"""
Build script for FDLog_Enhanced standalone executable.

This script builds a standalone executable using PyInstaller that includes
Python and all dependencies - users just download and run.

Usage:
    python build.py

Requirements:
    pip install pyinstaller

Output:
    dist/FDLog_Enhanced.exe (Windows)
    dist/FDLog_Enhanced (Linux/Mac)
"""

import subprocess
import sys
import os

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        return True

def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    # Map of import name to pip package name
    packages = {
        'pandas': 'pandas',
        'plotly': 'plotly',
        'serial': 'pyserial',  # CW keying support
    }
    for import_name, pip_name in packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print(f"Installing missing dependencies: {missing}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)

def build():
    """Build the executable."""
    print("=" * 50)
    print("Building FDLog_Enhanced standalone executable")
    print("=" * 50)

    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Check dependencies
    check_pyinstaller()
    check_dependencies()

    # Run PyInstaller
    print("\nRunning PyInstaller...")
    result = subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        'FDLog_Enhanced.spec'
    ])

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)

        # Copy exe to main directory for easy access
        import shutil
        exe_name = 'FDLog_Enhanced.exe' if sys.platform == 'win32' else 'FDLog_Enhanced'
        src = os.path.join('dist', exe_name)
        dst = exe_name
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"\nExecutable copied to: {dst}")
            print("(Also available in dist/ folder)")

        print("\nTo distribute:")
        print("  1. Zip the entire FDLog_Enhanced folder")
        print("  2. Users extract and run the .exe")
        print("\nThe exe must be in the same folder as the data files")
    else:
        print("\nBuild failed. Check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    build()
