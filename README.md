# FDLog_Enhanced (Now Ported to Python 3)
This is a complete Field Day group contest logging solution!
Download this on all computers (Windows, Mac, Linux including Raspberry Pis) and start logging. 
Visitors sign into the program and log because it is so simple.
All computers have a copy of the database (distributed) and tracks operations so everyone 
can see and co-operate. Tracks Dupes, shows previous contacts, see who is on which radio (node) 
and which band, who is contesting and who is logging, how many contacts they have made etc. 

Log entry is just three simple things : KD4SIR 1D IN 

The last Python 2.7 version is in the release section.   

The code here is now in Python 3 (should be stable) and working toward a 2023 stable release.  

I test on Linux and Windows with a 192.168.x.x network.  
This needs to be tested on different networks and with Macs.

We have added 85 enhancements to the original FDLog so far.

This is the top of the Release Log for FDLog_Enhanced
The release log will have the present back to the beginning of FDLog in 1984. 

Last updated 02Aug2022 Scott Hibbs KD4SIR
scotthibbs at gmail.com (email ideas for enhancements/bugs)

To Do and Ideas: 
		
	* An Information Table node that will allow sign in, show our group score, 
			the top 5 Contestors, the top 5 visitors, Worked All States, NTP server/client as time master etc.
	* Add more scoring: 
			complex gota points, youth, information table, official visitors, 
			max 20 radios, power multipliers, educational activity... 
	* option to auto time out nodes from the band select 15m/30m/45m/1hr
	* Fix so reports another's last contact time - this now reports node last heard on network. 
	* Change natural to battery? or add a battery button?
	* Try showing all sections to the side - marking those worked.
	* Work on Phonetic helper for GOTA station
	* believe prefix check only returns first prefix in the log. Actually there is a note in the code from
		Alan Biocca to fix this as foreign callsigns are not supported properly.
	* Dupe check for requested fills - 2 UNconnected nodes can dupe and both count when connected. 
	  (currently dupe checking is at entry - not on fills)
	* Need to rewrite all the documentation. It's everywhere...
	* Make font size a setting before Tkinker loads? 10,12,14 pt font. 
	* Logs menu gives logs for each mode by band, add setting for "ALL" contacts per mode
	* Should protect from Contestant being on multiple nodes (can't operate two radios at a time) 
	* left arrow act like backspace instead of nothing.
	* QST messages need to allow upper case characters
	* button needed to redraw window. Add row of buttons? Put network row above band buttons? 
	
	Linux to do list: 
		Off buttons keep the red background color when not selected, should turn grey
		on my raspberry pi: pdf files are not found but can be opened.
		on my raspberry pi: read error in file readme.txt


2022_Beta 3.0.3 02Aug2022
 85 Previous contacts on another band/mode will now populate the report as well so that no further typing is needed 
	to log the call again.	- Scott Hibbs kd4sir
		
		
2022_Beta 3.0.2 31Jul2022
		Fixed the GlobalDb() being called twice. 
		Added all the staticmethod decorators that where necessary.
		Removed all the power settings above 100w. 
		Fixed "After QSO edit display log prints all blue and not sorted."
		Added def logwredraw() to reprint the log display window on command.
 84	Ability to reprint the log window with a clean log. A menu item for now, but will be a button later.		
		
		
2022_Beta 3.0.1 21Jul2022
	Fixed edit/delete that became broken. Still needs to be sorted and have this reprint in the correct colors. (Currently all blue)

2022_Beta 3.0 21Jul2022
 83 Thanks to David and his work on B1QUAD/FDLog_Enhanced_python3, I have finished porting this to 
	Python 3. - Scott Hibbs KD4SIR
	
	updated miniweb.py to version 2.0 - now also ported to python 3. - Scott Hibbs kd4sir
		
2022_v2.3 12Jul2022 (Last Python 2.7 version) Released
	Finished python corrections as recommended by pycharm. I learned a ton! I will now test this to see if it is 
	stable for a release - Scott Hibbs KD4SIR 
	
	Updated miniweb.py to version 1.8 - Removed unused import, restructure, beautification.  - Scott Hibbs KD4SIR 

2022_Beta 2.2 10Jul2022
 82 Control-v and Control-c now both work. With the up arrow too. 
	More python corrections. 
	Fixed WAS report (Can't have multiple spaces in this file). 
	Entry window will now always show the bottom line.  

2022_Beta 2.1 09Jul2022
 81 Mouse Copy and Paste now work!! Tested on windows 10, must use the same format as the program entry which 
	is "kd4sir 1d in" or it will reject, also checks dupes, section etc. Keyboard shortcuts 
	(Control c,and v) will be easy to add next. - Thanks to Weo's suggestion (found in code notes probably in the 90's) - Scott Hibbs KD4SIR 08Jul2022    
 79 update: Restructured again. The main program is now located at bottom of the file. All major pycharm errors have
	been corrected.
	
2022_Beta_2 05Jul2022
 80 Found our memory leak - removed unnecessary root.update() and root.deiconify() - Scott Hibbs KD4SIR 03Mar2022    
 79 Major code restructure!! (and updating with pycharm suggestions) Moved main program elements to be more 
	readable. - 05Jul2022  

     Although a different program included with FDLog, I corrected a compatibility issue with Win10 so miniweb.py would work. 
     Changed from blocked port 80 to five fives - 55555. Adding a zip file of this project in the same folder makes it easy to 
	 share accross the same network as computers show up for field day. - Scott

2022_Beta_1.1 (Working toward a stable 2023_Field_Day Release)
 78 All text files converted to Unix EOL Conversion - Curtis E. Mills WE7U 21Jun2019   
 77 W1AW schedule is now a PDF file. - Curtis E. Mills WE7U 20Jun2019    
 76 Changed colors to be less garish: Yellow to gold, orange to dark orange, green to pale green,    
	grey to light grey. - Curtis E. Mills WE7U 21Jun2019    
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