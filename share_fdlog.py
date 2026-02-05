"""
Create a distribution zip of the FDLog_Enhanced project and serve it over the network.

Usage: python share_fdlog.py

This script:
  1. Creates a zip of the project source and data files in the share/ directory
  2. Starts miniweb to serve the share/ directory on the LAN
"""

import os
import sys
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARE_DIR = os.path.join(SCRIPT_DIR, "share")
ZIP_NAME = "FDLog_Enhanced.zip"
FOLDER_IN_ZIP = "FDLog_Enhanced"

# Files to include in the distribution zip
INCLUDE_FILES = [
    "FDLog_Enhanced.py",
    "cw_keying.py",
    "parser.py",
    "build.py",
    "share_fdlog.py",
    "miniweb.py",
    "FDLog Icon.ico",
    "FDLog Icon.png",
    "reset.py",
    "FDLog_Enhanced.spec",
    "requirements.txt",
    "cty.dat",
    "Arrl_sections_ref.txt",
    "ARRL_Band_Plans.txt",
    "Manual.txt",
    "Keyhelp.txt",
    "NTS_eg.txt",
    "Releaselog.txt",
    "README.md",
    "README.txt",
    "License.txt",
    "Bands.pdf",
    "Rules.pdf",
    "W1AW.pdf",
]

# Directories to include (recursively)
INCLUDE_DIRS = [
    "tests",
]

# Pre-built executables to include if found (built via build.py on each platform)
EXECUTABLE_FILES = [
    "FDLog_Enhanced.exe",       # Windows
    "FDLog_Enhanced_linux",     # Linux
    "FDLog_Enhanced_mac",       # macOS
]


def create_zip():
    """Create the distribution zip file in the share/ directory."""
    os.makedirs(SHARE_DIR, exist_ok=True)
    zip_path = os.path.join(SHARE_DIR, ZIP_NAME)

    print(f"Creating {ZIP_NAME}...")
    missing = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in INCLUDE_FILES:
            filepath = os.path.join(SCRIPT_DIR, filename)
            if os.path.isfile(filepath):
                zf.write(filepath, os.path.join(FOLDER_IN_ZIP, filename))
                print(f"  + {filename}")
            else:
                missing.append(filename)

        # Include pre-built executables for each platform if available
        exe_found = 0
        for filename in EXECUTABLE_FILES:
            filepath = os.path.join(SCRIPT_DIR, filename)
            if os.path.isfile(filepath):
                zf.write(filepath, os.path.join(FOLDER_IN_ZIP, filename))
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                print(f"  + {filename}  ({size_mb:.1f} MB)")
                exe_found += 1
        if not exe_found:
            print("  (no executables found - run build.py to create them)")

        for dirname in INCLUDE_DIRS:
            dirpath = os.path.join(SCRIPT_DIR, dirname)
            if os.path.isdir(dirpath):
                for root, dirs, files in os.walk(dirpath):
                    # Skip __pycache__
                    dirs[:] = [d for d in dirs if d != "__pycache__"]
                    for f in files:
                        fullpath = os.path.join(root, f)
                        arcname = os.path.join(FOLDER_IN_ZIP, os.path.relpath(fullpath, SCRIPT_DIR))
                        zf.write(fullpath, arcname)
                        print(f"  + {os.path.relpath(fullpath, SCRIPT_DIR)}")

    if missing:
        print(f"\n  Missing (skipped): {', '.join(missing)}")

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"\nCreated: {zip_path} ({size_mb:.1f} MB)\n")


def main():
    create_zip()

    sys.path.insert(0, SCRIPT_DIR)
    import miniweb
    miniweb.serve(directory=SHARE_DIR)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
    input("\nPress Enter to exit...")
