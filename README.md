# FDLog_Enhanced (Python 3)

This Field Day logging program may be better than what you use. 
Download this on all computers (Windows, Mac, Linux including Raspberry Pis) and start logging.
Visitors sign in and log because it is so simple. GOTA is integrated (separate dupes of course) on same network.
All computers (even GOTA) have a copy of the database (distributed) and tracks operations so everyone
can see and co-operate. Tracks Dupes, shows previous contacts, see who is on which radio (node)
and which band, who is contesting and who is logging. Displays number of contacts and how many log entries made. 
Has an inactivity timer and can auto log off a band to make it available for others. 
QST messages can be sent to all nodes. Full CW interface and many extras.

Log entry is just three simple things : KD4SIR 1D IN

## Quick Start

```bash
# Interactive mode (prompts for node name and auth key)
python FDLog_Enhanced.py

# Command-line mode (no prompts - useful for scripting/automation)
python FDLog_Enhanced.py --node station1 --auth 26

# GOTA station
python FDLog_Enhanced.py --node gota --auth 26

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
- Node names are automatically padded to 8 characters with random letters for uniqueness

## Installation

**Option 1: Download Standalone Executable (Easiest)**
- Download `FDLog_Enhanced.exe` (Windows) or `FDLog_Enhanced` (Mac/Linux) from Releases
- No Python installation needed - just run it!

**Option 2: Run from Source**
```bash
# Install Python 3.8+ from python.org
# Install dependencies:
pip install -r requirements.txt

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

The executable will be created in the `dist/` folder. Distribute this single file to users.

**Build outputs:**
- Windows: `dist/FDLog_Enhanced.exe` and main folder
- Linux/Mac: `dist/FDLog_Enhanced`

The last Python 2.7 version is in the release section.   

This is the top of the Release Log which has the present 
back to the beginning of FDLog in 1984. 

We have added 111 enhancements to the original FDLog so far.

Scott Hibbs at gmail.com (email ideas for enhancements/bugs)

To Do and Ideas:

	Linux to do list:
		(none currently)

v2026_Beta 4.1.2 - CW Added, Power limits, and Audio update

	+ Fixed viewtextf() path resolution for Linux/Raspberry Pi:
		- Text files now found correctly regardless of working directory
		- Added UTF-8 encoding for cross-platform compatibility

	111 Added Sound toggle checkbox (off by default):
		- Audio notifications for duplicate contacts
		- Audio notifications for QST messages
		- Default off for digital mode compatibility

	+ Fixed cross-platform file opening for PDFs and text files:
		- Works on Windows, macOS, Linux, and Raspberry Pi
		- Uses system default application (xdg-open on Linux)

	+ Improved error handling in CW keying module:
		- Replaced 20 bare except: clauses with specific exceptions
		- Better debugging and error diagnostics

	110 Added class-based power limits per ARRL Field Day 2026 rules:
		- Classes A, B, C: 500 watts PEP maximum
		- Classes D, E, F: 100 watts PEP maximum
		- Power is automatically capped based on your configured class
		- Updated Power menu with class-appropriate options:
			- 0 Watts
			- 5 Watts (QRP)
			- 100 Watts (Class D/E/F max)
			- 500 Watts (Class A/B/C max)
			- Alt/Nat options for 5W, 100W, and 500W (rule 7.3.8)

	109 Added Natural/Alternate Power countdown display:
		- Shows progress toward 100-point bonus (5 QSOs required)
		- Displays "Nat: X/5" next to Natural checkbox
		- Gold background while working toward goal
		- Green background with checkmark when bonus achieved

	108 The CW keying interface has been fully implemented.
		New file: cw_keying.py - Contains all CW keying classes
		Features Implemented
			Serial keying via DTR or RTS
			Winkeyer support (K1EL protocol)
			CAT keying for Flex SmartSDR and Icom 7300/7610
			F1-F12 macros with variable substitution ({MYCALL}, {CALL}, {RST}, {CLASS}, {SECT})
			PTT control with configurable lead-in/tail timing
			Speed control via PgUp/PgDn (2 WPM increments)
			ESC key aborts transmission
			CW status display in main window
			Settings persistence via globDb
		
2026_4.1.1 20Jan2026 Claude Code Updates 

	107 Fixed oldest bug from 1984. The program could not handle international
	    callsigns. Using https://github.com/scotthibbs/Call_Sign_Parser_and_Lookup 
		Claude Code was able to fix this bug. 
	+ WAS Map Fix - Now opens even when no states have been worked (shows blank map)
	+ Fixed Font changes to be more robust (some fonts were being missed)
	106 Network Dupe Checking - Automatic duplicate detection during network fills:
		- Detects when two disconnected nodes worked the same station on the same band
		- Compares timestamps and keeps the oldest contact
		- Deletes the newer duplicate automatically
		- Delete markers propagate across the network

2026_beta 4.1.0 19Jan2026 Claude Code Updates
	
	105 Info Table Node added:
		- Node selection: Type "info" to launch the information table display
		- Header: Club name, FD Call, GOTA Call (if set), and current time
		- Score panel: Total score with CW/Digital/Phone breakdown
		- Leaderboards: Top 5 Contestants and Top 5 Loggers
		- Progress tracking: Worked All States (X/50) and Sections (X/84)
		- Visitor registration: Green button that opens the full participant dialog
		- Auto-refresh: Updates every 10 seconds
		
	104 Phonetic Alphabet Display - Added at the bottom of the GUI with:
		- Radio buttons: Callsign (default), CQ, QRZ
		- Shows appropriate phonetic response format
		- Uses GOTA call for gotanode, FD call for others
	
2026_beta 4.0.1 19Jan2026 Claude Code updates

	103 Added Worked All Sections map and log report

	+ Consolidated font functions
     - Replaced 10 separate font functions (fntcourier10, fntcourier11, etc.)
       with single set_font(face, size) function
     - Updated menu commands to use lambda: set_font("Courier", 12)
     - Font changes no longer print "-Call-Class-Sect-" repeatedly

	+ Fixed WAS Map crash
     - Fixed get_have_states() ValueError when parsing report
     - Map now displays correctly with contacted states colored

	102 Added command-line arguments
     - --node, -n : Station node name (e.g., station1, gota)
     - --auth, -a : Authentication key (e.g., 24 for 2024)
     - --help, -h : Show help
     - Example: python FDLog_Enhanced.py --node station1 --auth 24

	101 Added requirements.txt
     - Lists dependencies: pandas, plotly
     - Install with: pip install -r requirements.txt

	100 Added PyInstaller build system
     - build.py : Build script
     - FDLog_Enhanced.spec : PyInstaller configuration
     - Creates standalone 43MB executable
     - Users don't need Python installed

		Fixed fingerprint() for standalone builds
		- Handles FileNotFoundError when running as bundled exe
		- Displays "(standalone build)" instead of hash

		NEW FILES CREATED:
		- requirements.txt
		- build.py
		- FDLog_Enhanced.spec
		- FDLog_Enhanced.exe (43MB standalone executable)

2023_beta 4.0.0 03Dec2023   
	NOT COMPATIBLE WITH PREVIOUS VERSIONS  
	Contestant Tracking - stable  
	
 95 fixed the ability to edit participants. Can't delete/edit initials by design.      
 96 Nodes send "user" packets which communicate the contestant, logger, and band.   
 97 Contestants are now tracked and maintained by each node.    
 98 Nodes can't select a contestant that is currently working a node (current or another node).  
(can't operate two radios, but can be control operator of two radios - aka the logger)   
 99 Added a "Contestants Working" button that will show who is working at each node.   
__The off buttons keeping the red color when not selected is the nature of tkinter for linux.
	There is no fix for this. Bug removed.  

2022_Beta 3.1.3 13Aug2022    
	Mouse over better update
	
__ Bug fix: Mouse over bands (wof function) erronously remembered all previous bands. (minor) -KD4SIR     
__ Mouse over, enhancement #6 and 34, now shows the node on the band/mode instead of all of them. -KD4SIR   
__ fixed bug to reject 0 power contacts from getting into the log (python 2 to 3 fix) - KD4SIR   
   
2022_Beta 3.1.2 10Aug2022   
	Inactivity timer update
	
__ Timer label (#91) modified to show minutes of inactivity while on band.  
94 Inactivity feature: ".set kick 30" command will now set thirty minutes to kick a user off the band without activity. The default is 10 minutes. Set to 0 to turn this feature off.  


2022_Beta 3.1.1 09Aug2022   
    Font update

 93 Added a "Font" menu that will redraw the program in Courier or Consolas (shlash zero) fonts with sizes between 10-14. 
 Needs testing on Linux and Mac - Scott Hibbs KD4SIR   

2022_Beta 3.1.0 06Aug2022   
	Major update and rearrangement of the GUI

__ Moved main program code to be more readable, grouped all the grids together.  
 86 The log window will now reprint when it recieves a deleteq record from another node. - Scott Hibbs KD4SIR   
 87 left arrow act like backspace instead of nothing. - Scott Hibbs KD4SIR
__ QST messages now allow upper case characters in them.  
 88 Added an "All CW", "All Digital" and "All Phone" log choice in the logs menu - Scott Hibbs KD4SIR   
 89 CW and Digital scores are now separated instead of adding together. - Scott Hibbs KD4SIR  
 90 Moved the network status label (enhancement #3) and node id under the menu and above the band selection. Also put the port number with the node id - Scott Hibbs KD4SIR  
 91 Timer label added showing "Time Away" (red) if band is off or "Time on Band" (grey). Also cleaned up the title to program name, class report and section, and current time. - Scott Hibbs KD4SIR  
__  Cleaned up the Contestant and Logger label to just show the initials and name - Scott Hibbs KD4SIR  
__  tweaked enhancements 8, 9, and 10 (individual scores) to be more readable.   
 92 Added a row to the GUI for function buttons like redraw log window etc.  
__  Enhancement 84 now has a button in the "function button" row to redraw the log window instead of a menu.
 

2022_Beta 3.0.3 02Aug2022  
 85 Previous contacts on another band/mode will now populate the report as well so that no further typing is needed to log the call again.	- Scott Hibbs kd4sir  
				
2022_Beta 3.0.2 31Jul2022  
__ Fixed the GlobalDb() being called twice.   
__ Added all the staticmethod decorators that where necessary.  
__ Removed all the power settings above 100w.   
__ Fixed "After QSO edit display log prints all blue and not sorted."
__ Added def logwredraw() to reprint the log display window on command.  
 84	Ability to reprint the log window with a clean log. A menu item for now, but will be a button later. - Scott Hibbs KD4SIR    
 
 2022_Beta 3.0.1 21Jul2022  
__ Fixed edit/deleteq that became broken. Still needs to be sorted and have this reprint in the correct colors. (Currently all blue) -Scott

2022_Beta 3.0 21Jul2022  
 83 Thanks to David and his work on B1QUAD/FDLog_Enhanced_python3, I have finished porting this to Python 3. - Scott Hibbs KD4SIR  
	
	updated miniweb.py to version 2.0 - now also ported to python 3. - Scott Hibbs kd4sir
		
2022_v2.3 12Jul2022 (Last Python 2.7 version) Released  
__ Finished python corrections as recommended by pycharm. I learned a ton! I will now test this to see if it is stable for a release - Scott Hibbs KD4SIR   
	
	Updated miniweb.py to version 1.8 - Removed unused import, restructure, beautification.  - Scott Hibbs KD4SIR 

2022_Beta 2.2 10Jul2022  
 82 Control-v and Control-c now both work. With the up arrow too. - Scott Hibbs KD4SIR   
__ More python corrections.   
__ Fixed WAS report (Can't have multiple spaces in this file).   
__ Entry window will now always show the bottom line.  - Scott  

2022_Beta 2.1 09Jul2022  
 81 Mouse Copy and Paste now work!! Tested on windows 10, must use the same format as the program entry which is "kd4sir 1d in" or it will reject, also checks dupes, section etc. Keyboard shortcuts - Scott Hibbs KD4SIR  
__ (Control c,and v) will be easy to add next. - Thanks to Weo's suggestion (found in code notes probably in the 90's) - Scott Hibbs KD4SIR 08Jul2022    
 79 update: Restructured again. The main program is now located at bottom of the file. All major pycharm errors have been corrected. - Scott Hibbs KD4SIR  
	
2022_Beta_2 05Jul2022  
 80 Found our memory leak - removed unnecessary root.update() and root.deiconify() - Scott Hibbs KD4SIR 03Mar2022    
 79 Major code restructure!! (and updating with pycharm suggestions) Moved main program elements to be more readable. - Scott Hibbs KD4SIR  

     Although a different program included with FDLog, I corrected a compatibility issue with Win10 so miniweb.py would work. 
     Changed from blocked port 80 to five fives - 55555. Adding a zip file of this project in the same folder makes it easy to 
	 share accross the same network as computers show up for field day. - Scott

2022_Beta_1.1 (Working toward a stable 2023_Field_Day Release)  
 78 All text files converted to Unix EOL Conversion - Curtis E. Mills WE7U 21Jun2019   
 77 W1AW schedule is now a PDF file. - Curtis E. Mills WE7U 20Jun2019      
 76 Changed colors to be less garish: Yellow to gold, orange to dark orange, green to pale green, grey to light grey. - Curtis E. Mills WE7U 21Jun2019    
 75 Spell check and comment cleanup - Curtis E. Mills WE7U 25Jun2019 and Scott Hibbs 18Jun2022     
 74 Added reminder that the space bar will check prefix, suffix and calls for dupes.    
 73 Changed New Participant window to be more user freindly - Curtis E. Mills WE7U 25Jun2019   
 72 Worked on other bands and dupe checking responses are nicer and are more readable, also reminds to up arrow.      
 71 Fixed dupe checking against club call and gota call that could have been entered with upper case and missed.   
 70 Changed the file name from FDLog_SCICSG to FDLog_Enhanced.   
	Two reasons, it's slightly confusing and I moved away from this awesome group of hams. :(    
 
2019_Beta_1 (posted on github, not tested)
 69 Winter Field Day update added - -Art Miller KC7SDA   
 68 Found and fixed memory leak (updatebb() method.bind) -Art Miller KC7SDA   
 67 Cleaned whitespace code (ie all revision history moved to readme file) -Art Miller KC7SDA   
 66 added python path shebang so program can run from command line - Art Miller KC7SDA Jul/1/2018   
 65 Corrected code as suggested by pylint - Scott Hibbs KD4SIR Jun/28/2018   
 64 Streamlined the networking section of the code - netmask removed. Art Miller KC7SDA Jul/1/2018   
 63 Allowed upper case entry for several settings. Art Miller KC7SDA Jul/1/2018   
 62 After an edit, the log window is redrawn to show only valid log entries. Scott Hibbs KD4SIR Jul/3/2018   
 61 Removed unused code and comments - Scott Hibbs KD4SIR Jul/3/2018   
 60 Up arrow will now retype the last entry (just in case enter was hit instead of space) - Scott Hibbs KD4SIR Jul/06/2018   

Continued in releaselog.txt


Scott Hibbs KD4SIR




