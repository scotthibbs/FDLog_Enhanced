#!/bin/bash
# FDLog Enhanced - macOS Build Launcher
# Double-click this file in Finder to build FDLog_Enhanced_mac
#
# FIRST TIME ONLY: Right-click > Open (macOS may block double-click)
# If blocked: System Settings > Privacy & Security > "Open Anyway"

# Go to the folder this script lives in
cd "$(dirname "$0")"

echo "============================================"
echo " FDLog Enhanced - macOS Build"
echo "============================================"
echo ""

# Search for python3 in all common macOS install locations
PYTHON3=""
for candidate in \
    /usr/bin/python3 \
    /usr/local/bin/python3 \
    /opt/homebrew/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.10/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.9/bin/python3
do
    if [ -x "$candidate" ]; then
        PYTHON3="$candidate"
        break
    fi
done

if [ -z "$PYTHON3" ]; then
    echo "ERROR: Python 3 is not installed (or could not be found)."
    echo ""
    echo "To fix:"
    echo "  1. Open Safari"
    echo "  2. Go to: https://www.python.org/downloads/"
    echo "  3. Click the big yellow 'Download Python' button"
    echo "  4. Open the downloaded .pkg file and follow the installer"
    echo "  5. Double-click build_mac.command again when done"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

echo "Python found: $($PYTHON3 --version) at $PYTHON3"
echo ""

# Run the build using the python3 we found
$PYTHON3 build.py

echo ""
read -p "Press Enter to close this window..."
