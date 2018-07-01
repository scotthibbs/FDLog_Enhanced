# FDLog_Enhanced
This is a complete Field Day group logging solution!
Download this on all computers (Windows, Mac, Linux including Raspberry Pis) and start logging. 
Have everyone sign in when they visit. We have our visitors log for us because it is so simple.

Log entry is just three simple things : KD4SIR 1D IN

Tracks Dupes, shows previous contacts, see who is on which radio and which band, 
who is contesting and who is logging, how many contacts they have made etc. 
It shares the database to all computers and tracks operations so everyone can see and co-operate.   

Download a stable release from the release section to enjoy! 

The code here is what is in progress and not stable for release yet. 

Currently working on: 

    KD4SIR - Redrawing the log window after a log edit so that an edited contact is no longer blue.
    KC7SDA - reworking the network section and fixing the upper and lower case bug.


*******************************************************************
FDLog_SCICSG             Jun 25, 2018               v2017-FD              

There were no changes made in 2018. I fully intended to use N1MM 
and give up on this project since most of the programming is over my head. 
However, N1MM setup was harder than this program and I ran out of 
time to set up all the computers with radio control and voice 
keying, plus setup like time settings etc... So the night before, 
we used this FDLOG_Enhanced from 2017. 

So, I'M BACK!!! And I got a list of more enhancements! I can't wait!

*******************************************************************
FDLog_SCICSG             Apr 9, 2017               v2017-FD

This is our stable 2017 Field Day Release. 

Found this didn't work on many versions of Linux. 
Ubuntu (including Mint, Desbian, Raspian etc) all gave the
loopback address in the program. This is fixed - You can now 
use your Raspberry Pi on Field Day! 

Please send your feedback to scotthibbs at gmail. 
Scott Hibbs KD4SIR Apr/9/2017

*******************************************************************
FDLog_SCICSG             Apr 1, 2017               v2017-beta-7

This will become our stable 2017 Field Day Release. 

I am in need of someone to double check that it works correctly
using a Mac and/or a Linux pc. 

I have checked it with Windows 10, Windows 7 and using various 
versions of python from 2.7.5 to the current release of 2.7.13. 

I'm proud and excited to see it in action this field day. Hope
you like it. 

Scott Hibbs KD4SIR Apr/1/2017

*******************************************************************
FDLog_SCICSG             Apr 1, 2017               v2017-beta-6

2017-beta-6 (unreleased)
  + Fixed who's on the bands reporting - now nice print out (from .ba report). 
  + Fixed freezing for the gota station.. gota is now gotanode.
  + Changed clock slew to a bigger number (0.75931) 
  + Class reporting should be correct now. Free VHF too. (reworked)
  + Protected against putting the fdcall and gota call in the log. 
  + Fixed the .node command - discovered it was broken.
  + Updated all the documentation files. 
  + Removed the wireless information menu - no longer needed.
  + Removed the propagation report. (Anyone use it?)
  + Removed duplicate arrl_sect.txt file needed by program. 
  + Removed frequency.txt file needed by program - arrl band chart gives same info.
  + Changed names of some of the files for simplicity 
  + Created a W1AW menu with the schedule and the NTS message file.
  + Operator now called Contestant. This allows non-hams to operate with a control operator.
  + Contestant or Logger needs a license to enter a QSO.
  + "Add New Participant" window uses the Enter key to save.
  + Can not edit previously EDITED log entries. 

Scott Hibbs KD4SIR Apr/1/2017

*******************************************************************
FDLog_SCICSG             Feb 15, 2017               v2017-beta-5

 * Added age and visitor tracking for each participant. 
 * Added participant check after an enter key for a call
 * Changed clock slew rate to a more odd number (.39571)

  ^ Will work on making sure the latest log entry is populated
  when editing the database. 

Scott Hibbs KD4SIR Feb/15/2017

*******************************************************************
FDLog_SCICSG             Feb 08, 2017               v2017-beta-4

This is v2017-beta-4 (stable needs testing)

This version ends the debate on a popup or another window opening
the who's on band information. I tried a pop up but it was simply
annoying. I placed a button to push this information but mousing 
over was the same thing. I didn't like the raw output of the 
information so I made it pretty to look at. Now I like it. 

I also cleaned up the wrong section dialogue so that it prints a 
nice clean list of sections to chose again.

Scott Hibbs KD4SIR Feb/8/2017

*******************************************************************
FDLog_SCICSG             Feb 06, 2017               v2017-beta-3

 This is v2017-beta-3 (stable needs testing)

 Now checks for valid arrl sections.
     Thanks to Alan Biocca W6AKB
     this was modified from his 153d version of FDLog.

 Please note the arrl_sect.dat file has been updated for this 
 version to work correctly. 

 Scott Hibbs KD4SIR Feb/6/2017

*******************************************************************
FDLog_SCICSG             Feb 04, 2017               v2017-beta-2

This is v2017-beta-2 (should be stable)
This will be tested to see if it will be our 2017 stable version for field day this year.

  * Fixed the Class not updating when clicking on an HF band
  * Removed bug that would not allow edits if the call and band are the same.
     Now can't edit a deleted log entry, and can't edit unless it is in the log.
      -- Need to display the latest log entry if an entry has been edited previously.
  * Removed the extra lines or labels in the qui for the port and for the list of nodes on
     on each band. - reverted back to the way it was for now but added the port
     to the header.

Next item to work on will be the popup that will show the station on the band clicked.

- Scott Feb, 4, 2017

*******************************************************************
FDLog_SCICSG             Jan 30, 2017      v2017-beta-1 with bugs

This is v2017-beta-1
  Obviously, I never released v2015-beta-5 which is what this is. There were no releases 
  in 2016, as we used the previous stable version. 

The unreleased 2015Beta4 and 2015Beta4.1 turned out to be a "time" bridge to far. During 
FD2016 one of the computers was receiving but was not sending. Since that computer had 
the time within a minute there were no conflicts with the database. This happens a lot, 
computers in and out of the network and no serious consequences. Which made me think that 
there was no need for hyper-accurate time devices or synch routines. So, beta 5 will revert
back to a simple time master like before. Internet time will probably be kept.. 
but our focus will be on new features.

Working on these items:
   *  Adding a Dupe check when editing qsos. Thanks to K9JAJ Jeff Jones for the idea.
        Bug: This will not let you edit details if the call and band are the same.
   *  At some point I broke the Class updating by one when clicking on an HF band. 
   *  Added a line in the gui to place the port and users on bands in, but changed my mind.
        If there are a lot of users it will not fit on this line. popup or back to the bottom. 
       Still need to remove it. 

 Items that need testing with 2017-beta-1
   *  Prevented the ability to edit previously deleted log entries. Thanks to K9JAJ Jeff Jones.
   *  Adding a statement to check for uppercase. Previously unresponsive while capped locked.
       Thanks to WW9A Brian Smith for pointing out that the program isn't randomly freezing.
   *  Made the -Call-Class-Sect- persistently above the input line. Thanks to K9MAF Mark Fountain.
   *  Added the port number to the header. - Requested by K9MAF Mark Fountain.
   *  "wa6nhc 5/2013 suggests precluding site operators from being logged as Q's"
       Done. Added the ability to "dupe check" participants outside the dupe log. Thanks WA6NHC
Please help. Scott KD4SIR

*******************************************************************
FDLog_SCICSG             Jun 27, 2016      notes on Field Day 2016

Our group (5A) used the stable version from last year as the 4 beta versions were not completed. This was our fifth year or so 
using this software, so we learned a few things because we knew what to look for. <br /><br />
     * For years we couldn't figure out why the program stops inputing data. Usually rebooting helped. Turns out the program
       doesn't allow capital letters. This makes sense for dupes etc. When the caps lock is accidently pushed the program 
       freezes. This will be fixed. (Thanks to WW9A for finding this!) <br />
     * Edited entries are counting in the operator contact count given by the program. (Thanks to K9JAJ!) <br />
     * Really need to place the mouse over data about which operators are on what bands to a temporary pop up.<br />
     * One operator's firewall started up and blocked outgoing data (he was receive only). 
        Once corrected his data was sent to others. It didn't seem to be a big deal that his data wasn't synced right away 
        since his time was correct. Should we continue the "ultra" precise time function in beta 4? <br /><br />
Anyway, I was ready to use another program for this field day since I wasn't ready with updates, but my group liked the program
and wanted to use last years edition. I now have renewed excitement to continue adding functionality to this program.

BTW, I'm not a programmer.. I've had to learn python... You can help more than I can. I got a list of things I want to do.
Please help. Scott KD4SIR

*******************************************************************
FDLog_SCICSG             Sep 3, 2015      notes on beta 4 (unreleased) 

Major overhaul to the clock feature underway. Before the GUI displays and right after the log is checked/loaded. If the log is new it will ask if you need to set up the event. After a series of questions (name, club call etc) it will check for an accurate time source (gps or internet), if found it will ask to set this first computer as time master. Clock skewing till take place before the gui displays. If you don't set up the event, the program will check for a time master and then skew the clock once a time broadcast is received. Once the time is accurate, it will display the gui.

I got it roughly written except for the skewing...
Again your help is needed!
Scott

*******************************************************************
FDLog_SCICSG              July 18, 2015      V2015-beta-3

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

*******************************************************************
FDLog_SCICSG              July 12, 2015      V2015-beta-2

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

*******************************************************************
(This is from my previous fork)
SCICSG_FDLog              July 3, 2015      V2015-beta-1

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
