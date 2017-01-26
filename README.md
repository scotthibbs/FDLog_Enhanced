# FDLog_Enhanced
A Stable Field Day Logging program for Amateur (Ham) Radio using a wireless network to distribute the database and coordinate operations. 

Beta 5 coming real soon!! (Jan 26, 2017)

FDLog_SCICSG             Jun 27, 2016      notes on Field Day 2016
*******************************************************************
Our group (5A) used the stable version from last year as the 4 beta versions were not completed. This was our fifth year or so 
using this software, so we learned a few things because we knew what to look for. <br /><br />
     * For years we couldn't figure out why the program stops inputing data. Usually rebooting helped. Turns out the program
       doesn't allow capital letters. This makes sense for dupes etc. When the caps lock is accidently pushed the program 
       freezes. This will be fixed. (Thanks to WW9A for finding this!) <br />
     * Edited entries are counting in the operator contact count given by the program. (Thanks to K9JAJ!) <br />
     * Really need to place the mouse over data about which operators are on what bands to a temporary pop up.<br />
     * One operator's firewall started up and blocked outgoing data (receive only). Once corrected his data was sent to others. 
       It didn't seem to be a big deal that his data wasn't synced right away since his time was correct. Should we continue the 
       "ultra" precise time function in beta? <br /><br />
Anyway, I was ready to use another program for this field day since I wasn't ready with updates, but my group liked the program
and wanted to use last years edition. I now have renewed excitement to continue adding functionality to this program.

BTW, I'm not a programmer.. I've had to learn python... You can help more than I can. I got a list of things I want to do.
Please help. Scott KD4SIR

FDLog_SCICSG             Sep 3, 2015      notes on beta 4 (unreleased) 
**********************************************************************
Major overhaul to the clock feature underway. Before the GUI displays and right after the log is checked/loaded. If the log is new it will ask if you need to set up the event. After a series of questions (name, club call etc) it will check for an accurate time source (gps or internet), if found it will ask to set this first computer as time master. Clock skewing till take place before the gui displays. If you don't set up the event, the program will check for a time master and then skew the clock once a time broadcast is received. Once the time is accurate, it will display the gui.

I got it roughly written except for the skewing...
Again your help is needed!
Scott

FDLog_SCICSG              July 18, 2015      V2015-beta-3
************************************************************
This is stable but is not 100% working. At least it doesn't crash
anymore. 

The big fix was getting sqlite to accept multiple threads and getting
the updates from the original fdlog to work within the Enhanced GUI
that we use without throwing an error. 

In beta 4, we will make everything work. We will make a "set up"
routine that will help the first user set up the event and be the
time master. Still looking at the new clock function... Once done
with time, we will move to more challenges. 

Your help is so needed. Please contact me for a list...
Scott KD4SIR

FDLog_SCICSG              July 12, 2015      V2015-beta-2
***************************************************************
I changed the name from SCICSG_FDLog to FDLog_SCICSG. Went from a 
fork to a repository. 

The code here is the combined code from our v2015-beta-1 and 
Alan Biocca's latest v4-1-152i 2014/05/26. This version actually
had the updated clock function. But it also added tcp/udp.

I chose not to bring in his code for tcp/udp to this version. I don't
think it adds to the programs primary function. I don't see operators
connecting over the internet. The 152i still has to broken sqlite and
with the tcp/udp it is further broken at the moment. 

New in this version is the new clock function. Alan's solution is to 
make a gps clock to coincide with the program. FDLog now looks for 
this clock before starting. I don't see hams building a gps clock
to make a program function better. I'm leaving it in for now. 
 
My next task is to make this stable. Then we will evaluate sqlite, and
maybe by then we will have a working tcp/udp version to evaluate as well. 

I am in need of volunteers to expand this program. 

1. I would like to see this integrate with Ham Radio Deluxe Free version 
for our digital folks. It would be nice to have FDLog automatically add 
contacts from that program when they are made. 

2. It would be nice if this program was to catch up with Writelog in all 
the automated features it offers. Like cw and voice keying first. 

At this rate we will have a great Field Day stable version for 2016.

Scott Hibbs KD4SIR

(This is from my previous fork)
SCICSG_FDLog              July 3, 2015      V2015-beta-1
*************************************************************************
The code here is the combined code from the 2015 field day stable version
with the enhancements and the latest non-stable beta version from 1-152-n. 
I am going to work out the kinks to make it stable and then work on 
making improvements. 

I am in need of volunteers to expand this program. 

1. I would like to see this integrate with Ham Radio Deluxe Free version 
for our digital folks. It would be nice to have FDLog automatically add 
contacts from that program when they are made. 

2. It would be nice if this program was to catch up with Writelog in all 
the automated features it offers. Like cw and voice keying first. 

OH, I'm doing my version numbering different. I'd like to see a stable
release issued every year. So we will start with v2015-beta-1 etc. Then in 
May we issue v2016-stable... 

Scott Hibbs KD4SIR
