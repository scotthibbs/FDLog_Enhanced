#!/usr/bin/env python3
"""
Reset script for FDLog_Enhanced - clears data files, optionally rebuilds exe.

This script:
1. Deletes all .sq3 database files
2. Deletes all .fdd log journal files
3. Optionally deletes FDLog_Enhanced.exe and rebuilds via build.py

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

    # Optionally delete data files
    print("Delete all data files?")
    print("  - All *.sq3 database files")
    print("  - All *.fdd log journal files")
    print()
    response = input("Delete data files? (yes/no): ").strip().lower()

    if response == 'yes':
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

        print()
        print(f"Deleted {deleted_count} data file(s).")
    else:
        print("\nData files kept.")

    print()

    # Optionally delete exe and rebuild
    exe_paths = ["FDLog_Enhanced.exe", os.path.join("dist", "FDLog_Enhanced.exe")]
    exe_exists = any(os.path.exists(p) for p in exe_paths)

    response = input("Delete the exe and rebuild? (yes/no): ").strip().lower()
    if response == 'yes':
        if exe_exists:
            for p in exe_paths:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                        print(f"  Deleted: {p}")
                    except Exception as e:
                        print(f"  Error deleting {p}: {e}")
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
        print("Done!")
        print("=" * 50)

if __name__ == '__main__':
    main()
