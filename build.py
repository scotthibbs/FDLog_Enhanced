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
    FDLog_Enhanced.exe       (Windows)
    FDLog_Enhanced_linux     (Linux)
    FDLog_Enhanced_mac       (macOS)
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

def check_macos_tools():
    """On macOS, verify Xcode Command Line Tools are installed (needed by PyInstaller)."""
    if sys.platform != 'darwin':
        return
    result = subprocess.run(['xcode-select', '-p'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Xcode CLT: OK ({result.stdout.strip()})")
        return
    print("Xcode Command Line Tools not found - required for building on macOS.")
    print("Launching installer dialog...")
    subprocess.run(['xcode-select', '--install'])
    print()
    print("A dialog box has appeared asking to install Developer Tools.")
    print("Click 'Install' and wait for it to finish (may take a few minutes).")
    print("Then run build.py again.")
    print()
    input("Press Enter to exit...")
    sys.exit(0)


def check_macos_tkinter():
    """On macOS, verify Tkinter works and try to fix it if not."""
    if sys.platform != 'darwin':
        return
    try:
        import tkinter
        print("Tkinter: OK")
        return
    except ImportError:
        pass

    print("Tkinter not found - this is required for FDLog to run.")
    print("Attempting to install via Homebrew...")

    brew = subprocess.run(['which', 'brew'], capture_output=True, text=True)
    if brew.returncode != 0:
        print()
        print("ERROR: Homebrew is not installed and Tkinter is missing.")
        print("Fix option 1 (easiest):")
        print("  Re-install Python from https://www.python.org/downloads/")
        print("  (The official python.org installer includes Tkinter)")
        print()
        print("Fix option 2:")
        print("  Install Homebrew from https://brew.sh then run:")
        print("  brew install python-tk")
        print()
        input("Press Enter to exit...")
        sys.exit(1)

    # Detect python version for brew package name
    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    pkg = f"python-tk@{ver}"
    print(f"Running: brew install {pkg}")
    result = subprocess.run(['brew', 'install', pkg])
    if result.returncode != 0:
        print(f"brew install failed. Try manually: brew install {pkg}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Verify again
    try:
        import tkinter
        print("Tkinter: now OK")
    except ImportError:
        print("Tkinter still not available after install.")
        print("Try re-installing Python from https://www.python.org/downloads/")
        input("Press Enter to exit...")
        sys.exit(1)


def check_dependencies():
    """Check if required dependencies are installed."""
    # macOS checks first
    check_macos_tools()
    check_macos_tkinter()

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

    # Run PyInstaller — stream output live so it doesn't look frozen
    print("\nRunning PyInstaller...")
    log_path = os.path.join(script_dir, 'build_log.txt')
    print(f"(Full output also saved to: {log_path})\n")
    proc = subprocess.Popen(
        [sys.executable, '-m', 'PyInstaller', '--clean', 'FDLog_Enhanced.spec'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    with open(log_path, 'w') as log_file:
        for line in proc.stdout:
            print(line, end='')
            log_file.write(line)
    proc.wait()

    if proc.returncode == 0:
        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)

        # Copy exe to main directory with platform-specific name
        import shutil
        if sys.platform == 'win32':
            exe_name = 'FDLog_Enhanced.exe'
            dst = exe_name
        elif sys.platform == 'darwin':
            exe_name = 'FDLog_Enhanced'
            dst = 'FDLog_Enhanced_mac'
        else:
            exe_name = 'FDLog_Enhanced'
            dst = 'FDLog_Enhanced_linux'
        src = os.path.join('dist', exe_name)
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
        # Re-show error lines so they're visible after all the scrolled output
        try:
            with open(log_path) as lf:
                err_lines = [ln.rstrip() for ln in lf
                             if 'ERROR' in ln.upper()]
            if err_lines:
                print("\nError lines from build_log.txt:")
                for ln in err_lines[-10:]:
                    print("  " + ln)
        except Exception:
            pass
        return False
    return True

if __name__ == '__main__':
    ok = False
    try:
        ok = build()
    except SystemExit:
        pass  # exit paths above already explained themselves
    except BaseException:
        # BaseException so even KeyboardInterrupt/odd failures can't close
        # the console window before the user reads the error
        import traceback
        traceback.print_exc()
    if not ok:
        print("\nBUILD DID NOT COMPLETE - see errors above.")
    try:
        input("\nPress Enter to exit...")
    except EOFError:
        pass  # no console attached - nothing to hold open
