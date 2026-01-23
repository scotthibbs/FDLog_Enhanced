#!/usr/bin/env python3
"""
Reset script for FDLog_Enhanced - clears data files and rebuilds exe.

This script:
1. Deletes all .sq3 database files
2. Deletes all .fdd log journal files
3. Deletes fdlog.dat persistent config (NOT Arrl_sect.dat)
4. Deletes FDLog_Enhanced.exe
5. Runs build.py to create fresh exe

Usage:
    python reset.py

Author: Scott Hibbs KD4SIR
"""

import os
import glob
import subprocess
import sys

def main():
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    print("=" * 50)
    print("FDLog_Enhanced Reset Script")
    print("=" * 50)
    print()

    # Confirm with user
    print("This will DELETE all data files and rebuild the exe:")
    print("  - All *.sq3 database files")
    print("  - All *.fdd log journal files")
    print("  - FDLog_Enhanced.exe")
    print()
    print()
    response = input("Are you sure? (yes/no): ").strip().lower()

    if response != 'yes':
        print("\nReset cancelled.")
        return

    print()
    deleted_count = 0

    # Delete .sq3 files
    for f in glob.glob("*.sq3"):
        try:
            os.remove(f)
            print(f"  Deleted: {f}")
            deleted_count += 1
        except Exception as e:
            print(f"  Error deleting {f}: {e}")

    # Delete .fdd files
    for f in glob.glob("*.fdd"):
        try:
            os.remove(f)
            print(f"  Deleted: {f}")
            deleted_count += 1
        except Exception as e:
            print(f"  Error deleting {f}: {e}")

    # Delete exe
    if os.path.exists("FDLog_Enhanced.exe"):
        try:
            os.remove("FDLog_Enhanced.exe")
            print("  Deleted: FDLog_Enhanced.exe")
            deleted_count += 1
        except Exception as e:
            print(f"  Error deleting FDLog_Enhanced.exe: {e}")

    print()
    print(f"Deleted {deleted_count} file(s).")
    print()

    # Ask about rebuild
    response = input("Rebuild exe now? (yes/no): ").strip().lower()

    if response == 'yes':
        print()
        print("Running build.py...")
        print()
        result = subprocess.run([sys.executable, "build.py"])
        if result.returncode == 0:
            print()
            print("=" * 50)
            print("Reset and rebuild complete!")
            print("=" * 50)
        else:
            print()
            print("Build failed. Check errors above.")
    else:
        print()
        print("=" * 50)
        print("Reset complete! Run 'python build.py' to rebuild exe.")
        print("=" * 50)

if __name__ == '__main__':
    main()
