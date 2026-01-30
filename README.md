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
Has an inactivity timer and can auto log off a band to make it available for others.    
(So when KD4SIR falls asleep on 20p, you can take the band!)      
QST messages can be sent to all nodes (even GOTA) or one node.    
Full CW interface, and even a voice keyer (text to speech or recorded)    
WSJT-X integration - QSOs logged in WSJT-X (FT8/FT4) automatically appear in FDLog.   
JS8Call with WSJT-X supported.       
Fldigi Two-Way Integration.   
N3FJP API Integration
&nbsp;&nbsp;&nbsp;&nbsp;- TCP client pulls QSOs from N3FJP
&nbsp;&nbsp;&nbsp;&nbsp;- TCP server lets N3FJP-compatible programs send QSOs to FDLog.
Hamlib rigctld Rig Control Integration for 200+ rigs support

Log entry is just three simple things : KD4SIR 1D IN

## Quick Start for the IT Guy of the Group

Make sure you have Python 3.8+ with pip installed   
and make sure your time is absolutely correct on the computer.   
Node names should reflect the radio or location.  
the info node and gota node must have these names.   
Download and extract the zip file in a folder.   
Run the build.py program which creates the executable for pc/mac/linux    
named "FDlog_Enhanced". Run it (FDlog_Enhanced).    
When asked:   
&nbsp;&nbsp;&nbsp;&nbsp; "For the person in Charge of Logging:   
&nbsp;&nbsp;&nbsp;&nbsp; *** ONLY ONE PERSON CAN DO THIS ***   
&nbsp;&nbsp;&nbsp;&nbsp; Do you need to set up the event? Y or N"   
THIS IS YOU, only you should say YES. 
Just answer questions about the contest.   
This computer should be the 'Time Master' (only one)   
Your admin pin will allow only you to edit participants with log entries.   
(ie: After working 2 hours, Scotty would like to be Scott in the log)   
When asked "Do you need to deploy this program to other computers?"     
This will create a zip file and start an http file server (miniweb.py)   
Note the ip address and port. (example: 192.168.1.58:55555)   
Go to each computer with python 3.8+ on the same network.    
Navigate to to the above address.   
Download the zip and extract to a folder.. run build.py       
Run the executable - these computers say no to the setup question.   
To make sure you have a complete log, the time master should be the last to shut down for the event.    

**Notes:**
- All participants can sign in at any node. (check in every visitor you see -age is for youths)   
- All nodes on the same network must use the same auth key     
&nbsp;&nbsp; (last two digits of contest year) to communicate   
&nbsp;&nbsp; this allows for one node to test separately from others using 'tst' auth        
- Node names are automatically padded or trunked to 8 characters with random letters for uniqueness   
- if a node goes down (power/network/shutdown) restart will remember it's node name, just enter the auth to continue.   
&nbsp;&nbsp; it will automatically get fills from the other nodes.   
   
Please see the Release Log which has all the changes from the present 
back to the beginning of FDLog in 1984. 

Scott Hibbs at gmail.com (email ideas for enhancements/bugs)

Scott Hibbs KD4SIR




