# FDLog_Enhanced
FDLog_SCICSG is an upgraded fdlog with lots of extras. Ongoing project - your help is needed.

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
Scott
KD4SIR

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

Scott Hibbs
KD4SIR

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

Scott Hibbs
KD4SIR


