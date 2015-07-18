FDLog_SCICSG              July 18, 2015      V2015-beta-3-stable

Took a while to get this stable, but I'm not getting errors anymore. 
Tested with two computers. Please note that just because this is 
stable, doesn't mean that this version is 100% working. It's just
not throwing errors or crashing. 

TIME: Precious time.. Still needs to be worked on. I don't believe
it works the way it is. I stopped a program on one computer and 
changed the time and restarted and FDLog pulled the previous offset
from the database. Hmm.... Shouldn't it check anyway? I also want to 
add a function to check for the NIST internet time. This should also 
be authoritative like the gps clock. If there is a time master then
everything should skew to it. There should be checks in place so 
that only those with Internet time or GPS time are a time master. I'm
working on this. 

HELP NEEDED: 
1. I currently have a mouse over event to show those on band. It would 
be nice if this were just a pop up that disappears when the mouse
over event is over. 

2. Change the add new participate window. After entering all the fields
an enter key should save the data and close. If the fields are empty 
and enter key is used, then close. Would also like a checkbox here to 
track if the new participate is youth. This should help us change and 
track the gota scoring. 

3. I would like to see this integrate with Ham Radio Deluxe Free version 
for our digital folks. It would be nice to have FDLog automatically add 
contacts from that program when they are made. 

4. It would be nice if this program was to catch up with Writelog in all 
the automated features it offers. Like cw and voice keying. 

If you think of anything else: Do it. 

Scott 
KD4SIR
 

FDLog_SCICSG              July 12, 2015      V2015-beta-2

I changed the name from SCICSG_FDLog to FDLog_SCICSG. 

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

Scott Hibbs
KD4SIR



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

Scott Hibbs
KD4SIR




FDLOG = Field Day Logging Program                    3/2002 A K Biocca

FDLOG is distributed under the GNU Public License

$Revision: 1.22 $

  This program is designed to support Amateur Radio Field Day Operations by 
providing a robust multiplatform networked distributed logging database and
information service.


Introduction

  This is a complete rewrite of WB6ZQZ's Field Day Logging program. It is nearly 
20 years old (in 2002), but this new version has many new features, 
primary of which is the ability to synchronize the logfile database across 
a network in a peer to peer fashion, avoiding single points of failure. 
The expectation is that a wireless network will be used.

  To run this program you will need to install Python (or not). The development was
done on win2k under Python 2.2-2.7 and Tkinter, but it should be able to run on Linux and
the Mac with most features. Python is available from www.python.org. There is a
directly executable version of FDLog called fdlogexe.zip. This is a larger download
but it works without Python installed. It only works in Windows.

  Networking is required to use the data sync features of the program. A broadcast
is used, so stations on the same subnet running the program will sync databases. 
An authentication code is used, so only stations with the same auth code will be 
able to share data.

  Setting up ad-hoc or peer-peer 802.11 networking is beyond the scope of this 
note. This should be done prior to running the logging software. Note that each
station does need a distinct hostname for proper database synchronization. See
the separate note on wireless networking.

  The computer's clock accuracy is important, so set it before starting the log 
program. This will reduce the amount of correction the internal time sync has
to compensate for. Designate one computer as the master timekeeper (and set
this in FDLog). Then all program time clocks will track that one.

  Getting the latest version of the program on Field Day will at our site is 
handled by a small web server on one of the development machines. Other files 
like Python and FD rules will be available there as well. See the Help/802.11 
note for details. Python 2.2 to 2.7 have been used successfully with the
software.

  Installing the FDLOG program is straightforward - all that is needed is a directory 
with the files in it. The program will create database and log files in this 
directory. Unpack the zipfile in the directory you have chosen. If you want access
to the Field Day rules (a menu item under help) download the ARRL Field Day Rules
package and rename it to 'fdrules.pdf' and add it to the dir. Viewing pdf files requires
Adobe Acrobat, available from www.adobe.com. Launching the pdf file from Python
may only work on win32 systems. The index.htm file contains links to all the
documentation as well, so launching your web browser (double click on index.htm)
provides program-independent access to the docs.

  The FDLOG program is launched by double-clicking on the fdlog.py icon in the 
directory. For convenience you may want to create a shortcut on the desktop.

  Starting the program the first time will ask a few questions as it sets up.

  Visit the help menu 'Help/Getting Started' for further instructions.

Thanks, Alan Biocca, WB6ZQZ at ARRL.net

eof
