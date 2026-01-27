# FDLog_Enhanced (Python 3)

This Field Day logging program may be better than what you use. 

Download this on all computers (Windows, Mac, Linux including Raspberry Pis) and start logging.

Contestors are those operating a radio (only one). Loggers are those entering on the computer.   
One of them must have a license. A control operator may oversee multiple contestors if added as a logger.   
Thus everything is tracked even the control operator for each contact.    
GOTA is integrated (separate dupes of course) on same network.   
INFO Node keeps score on the information table (allows sign in).   
All computers (even GOTA) have a copy of the database (distributed) - no lost data.    
Program keeps track of who is at which radio and on which band. No asking around...   
Tracks Dupes (with GOTA separate), shows previous contacts (even for GOTA), WAS and Worked all sections.    
Displays number of contacts and how many log entries made for each person.    
Has an inactivity timer and can auto log off a band to make it available for others. So when Scott   
falls asleep, you can take the band!   
QST messages can be sent to all nodes (even GOTA) or one node.    
Full CW interface and many many extras.   

Log entry is just three simple things : KD4SIR 1D IN

## Quick Start

```bash
# Interactive mode (prompts for node name and auth key)
python FDLog_Enhanced.py

# Command-line mode (no prompts - useful for scripting/automation)
python FDLog_Enhanced.py --node station1 --auth 26

# GOTA or INFO station
python FDLog_Enhanced.py --node gota --auth 26
python FDLog_Enhanced.py --node info --auth 26

# Show help
python FDLog_Enhanced.py --help
```

## Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--node` | `-n` | Station node name (7 characters, e.g., `station1`, `station2`, `gota`) |
| `--auth` | `-a` | Authentication key (use two-digit year for contests, e.g., `26` for 2026, or `tst` for testing) |
| `--help` | `-h` | Show help message |

**Notes:**
- If `--node` is not provided and no saved node exists, you'll be prompted interactively
- If `--auth` is not provided and no saved auth key exists, you'll be prompted interactively
- All nodes on the same network must use the same `--auth` key to communicate
- Node names are automatically padded or trunked to 8 characters with random letters for uniqueness

## Installation

**Option 1: Download Standalone Executable (Easiest)**
- Download `FDLog_Enhanced.exe` (Windows) or `FDLog_Enhanced` (Mac/Linux) from Releases
- No Python installation needed - just run it!
- You will need all the supporting files in the main folder.
  
**Option 2: Run from Source**
```bash
# Install Python 3.8+ from python.org
# Install dependencies:
pip install -r requirements.txt
- again you will need the supporting files in the main folder.
# Run:
python FDLog_Enhanced.py
```

## Building Standalone Executables

To create a standalone executable that users can run without Python:

```bash
# Install build dependencies
pip install pyinstaller

# Run the build script
python build.py

# Or manually with PyInstaller
pyinstaller FDLog_Enhanced.spec
```

The executable will be created in the `dist/` folder. Move this to the main folder. 

**Build outputs:**
- Windows: `dist/FDLog_Enhanced.exe` and main folder
- Linux/Mac: `dist/FDLog_Enhanced`

Please see the Release Log which has all the changes from the present 
back to the beginning of FDLog in 1984. 

Scott Hibbs at gmail.com (email ideas for enhancements/bugs)

Scott Hibbs KD4SIR
