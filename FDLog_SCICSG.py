#!/usr/bin/python 
# Added by Art Miller KC7SDA May/5/2017
# NOTE for Linux users: you must convert the line endings from windows to linux
import os
import time
import string
import thread
import threading
import socket
import hashlib
import random
import calendar
import sqlite3
from Tkinter import Tk, END, NORMAL, DISABLED, re, sys, Toplevel, Frame, Label, Entry, Button, \
W, EW, E, NONE, NSEW, NS, StringVar, Radiobutton, Tk, Menu, Menubutton, Text, Scrollbar, Checkbutton, RAISED, IntVar


# This needs to be tested on different networks and cross platform before released.
# 
# KD4SIR - Will probably work on copy/paste functionality
# KC7SDA - Will check network and platform compatibility and upper/lower case entry 



# 2019_Beta_1
#
# + added python path shebang so program can run from command line - Art Miller KC7SDA Jul/1/2018
# + Corrected code as suggested by pylint - Scott Hibbs KD4SIR Jun/28/2018
# + Streamlined the networking section of the code - netmask removed. Art Miller KC7SDA Jul/1/2018
# + Allowed upper case entry for several settings. Art Miller KC7SDA Jul/1/2018
# + After an edit, the log window is redrawn to show only valid log entries. Scott Hibbs KD4SIR Jul/3/2018
# + Removed unused code and comments - Scott Hibbs KD4SIR Jul/3/2018
# + Up arrow will now retype the last entry (just in case enter was hit instead of space) - Scott Hibbs KD4SIR Jul/06/2018




# Originally "WB6ZQZ's Field Day Logging Program" written in 1984.
# Alan Biocca (as WB6ZQZ) ported it to python with GNU in 2002. 
# Our code starts from: 
# FDLog 1-149-2 2011/07/11
# Copyright 2002-2013 by Alan Biocca (W6AKB) (www.fdlog.info)
# FDLog is distributed under the GNU Public License
# Additional code included from FDLog v4-1-152i 2014/05/26
# Some code modified from FDLog v4-1-153d Febuary 2017

# Forked & Repository Project
# FDLog_Enhanced at Github.com
# Copyright 2014-2018 South Central Indiana Communications Support Group
# 
# Our Goals are twofold:
#       1: Improve on fdlog faster with open and directed collaboration.
#               This is now on github as FDLog_Enhanced.
#       2: Increase user friendlyness (GUI) and inter-operability with other GNU programs.
#               Future: Adding interoperability with other programs such as HRDeluxe Free,
#               FLDigi, Rigserve etc if we can?

prog = 'FDLog_SCICSG v2017_Field_Day2 \n' \
       'Copyright 2017 by South Central Indiana Communications Support Group \n' \
       'FDLog_SCICSG is under the GNU Public License v2 without warranty. \n' \
       'The original license file is in the folder. \n'
print prog

about = """

FDLog_Enhanced can be found on www.github.com
GNU Public License V2 - in program folder.
Copyright 2018 South Central Indiana Communications Support Group
Visit us at www.scicsg.org
Your donations are appreciated to support Amateur Radio.

"""

version = "v18"
fontsize = 14
fontinterval = 2
typeface = 'Courier 10 pitch'

fdfont = (typeface, fontsize)  # regular fixed width font
fdmfont = (typeface, fontsize + fontinterval)  # medium  fixed width font
fdbfont = (typeface, fontsize + fontinterval * 2)  # large   fixed width font


# Known Bug List
#
# some foreign callsigns not supported properly
#   8a8xx
#   need to change the way this works
#   define a suffix as trailing letters
#   prefix as anything ending in digits
#   bring down a previous suffix with a character such as ' or .
#
#

#  Scott Hibbs KD4SIR 10/2/13
#  Removed Release Log that was here into a text file.

#  Scott Hibbs KD4SIR 5/11/14
#  Removed the key help that was here into a text file.

#  Scott A Hibbs KD4SIR 7/25/2013
#  Removed the getting started text that was here into a text file.


def fingerprint():
    t = open('FDLog_SCICSG.py').read()
    h = hashlib.md5()
    h.update(t)
    print " FDLog_SCICSG Fingerprint", h.hexdigest()


fingerprint()


def ival(s):
    """return value of leading int"""
    r = 0
    if s != "":
        mm = re.match(r' *(-?[0-9]*)', s)
        if mm and mm.group(1):
            r = int(mm.group(1))
    return r


class clock_class:
    level = 9  # my time quality level
    offset = 0  # my time offset from system clock, add to system time, sec
    adjusta = 0  # amount to adjust clock now (delta)
    errors = 0  # current error sum wrt best source, in total seconds
    errorn = 0  # number of time values in errors sum
    srclev = 10  # current best time source level
    lock = threading.RLock()  # sharing lock

    def update(self):
        """periodic clock update every 30 seconds"""
        #  Add line to get tmast variable (self.offset=float(gd.get('tmast',0)) from global database
        self.lock.acquire()  # take semaphore
        if node == string.lower(gd.getv('tmast')):
            if self.level != 0: print "Time Master"
            self.offset = 0
            self.level = 0
        else:
            if self.errorn > 0:
                error = float(self.errors) / self.errorn
            else:
                error = 0
            self.adjusta = error
            err = abs(error)
            if (err <= 2) & (self.errorn > 0) & (self.srclev < 9):
                self.level = self.srclev + 1
            else:
                self.level = 9
            if self.srclev > 8: self.adjusta = 0  # require master to function
            if abs(self.adjusta) > 1:
                print "Adjusting Clock %.1f S, src level %d, total offset %.1f S, at %s" % \
                      (self.adjusta, self.level, self.offset + self.adjusta, now())
            self.srclev = 10
        self.lock.release()  # release sem
        ## Add line to put the offset time in global database (gd.put('tmast',self.offset))

    def calib(self, fnod, stml, td):
        "process time info in incoming pkt"
        if fnod == node:
            return
        self.lock.acquire()  # take semaphore
        #    print "time fm",fnod,"lev",stml,"diff",td
        stml = int(stml)
        if stml < self.srclev:
            self.errors, self.errorn = 0, 0
            self.srclev = stml
        if stml == self.srclev:
            self.errorn += 1
            self.errors += td
        self.lock.release()  # release sem

    def adjust(self):
        "adjust the clock each second as needed"
        rate = 0.75931  # delta seconds per second
        adj = self.adjusta
        if abs(adj) < 0.001: return
        if adj > rate:
            adj = rate
        elif adj < -rate:
            adj = -rate
        self.offset += adj
        ## or self.offset = float(database.get('tmast',0)) instead of the line above.
        self.adjusta -= adj
        print "Slewing clock", adj, "to", self.offset


mclock = clock_class()

# kc7sda - code cleanup and modify (refactor), added wfd support
def initialize():
    k = "" # keyboard input
    z = "" # answer counter
    kfd = 0 # FD indicator to skip questions
    print "\n \n"
    print "For the person in Charge of Logging:"
    print "*** ONLY ONE PERSON CAN DO THIS ***"
    print "Do you need to set up the event? Y or N"    
    print "       if in doubt select N"
    while z != "1":
        k = string.lower(string.strip(sys.stdin.readline())[:1])
        if k == "y": z = "1"
        if k == "n": z = '1'
        if z != "1": print "Press Y or N please"    
    if k == "y":
        # Field Day or VHF contest
        z = ""
        print "Which contest is this?"
        print "F = FD, W = WFD, and V = VHF"
        while z != "1":
            k = string.lower(string.strip(sys.stdin.readline())[:1])
            if k == "f": z = "1"
            if k == "w": z = "1"
            if k == "v": z = '1'
            if z != "1": print "Press F, W or V please"
        if k == "f":
            kfd = 1 #used later to skip grid square question.SAH
            globDb.put('contst', "FD")
            qdb.globalshare('contst', "FD")  # global to db
            renew_title()
            print "Have a nice Field Day!"
        if k == "w":
            kfd = 2 #used later to skip grid square question.SAH
            globDb.put('contst', "WFD")
            qdb.globalshare('contst', "WFD")  # global to db
            renew_title()
            print "Have a nice Field Day!"
        if k == "v":
            globDb.put('contst', "VHF")
            qdb.globalshare('contst', "VHF")  # global to db
            renew_title()
            print "Enjoy the VHF contest!"
        # Name of the club or group
        print "What is the name of your club or group?"
        k = string.strip(sys.stdin.readline())
        while k == "":
            print "Please type the name of your club or group"
            k = string.strip(sys.stdin.readline())
        globDb.put('grpnam', k)
        qdb.globalshare('grpnam', k)  # global to db
        renew_title()
        print k, "is a nice name."
        # Club Call
        print "What will be your club call?"
        k = string.strip(sys.stdin.readline())
        while k == "":
            print "Please type the club call."
            k = string.strip(sys.stdin.readline())
        globDb.put('fdcall', k)
        qdb.globalshare('fdcall', k)  # global to db
        renew_title()
        print k, "will be the club call."
        # Gota Call
        if kfd == 1:
            print "What will be your GOTA call?"
            k = string.strip(sys.stdin.readline())
            while k == "":
                print "Please type the GOTA call. (if none type none)"
                k = string.strip(sys.stdin.readline())
            else:
                globDb.put('gcall', k)
                qdb.globalshare('gcall', k)  # global to db
                renew_title()
                print k, "will be the GOTA call."
        # Class
        print "What will be your class? (like 2A)"
        k = string.strip(sys.stdin.readline())
        while k == "":
            print "Please type the class."
            k = string.strip(sys.stdin.readline())
        else:
            globDb.put('class', k)
            qdb.globalshare('class', k)  # global to db
            renew_title()
            print k, "will be the class."
        # Section
        print "What will be your section? (like IN-Indiana)"
        k = string.strip(sys.stdin.readline())
        while k == "":
            print "Please type the section (like KY-Kentucky)."
            k = string.strip(sys.stdin.readline())
        else:
            globDb.put('sect', k)
            qdb.globalshare('sect', k)  # global to db
            renew_title()
            print k, "will be the section."
        if kfd == 0:
            # grid square
            print "What will be your grid square? (if none type none)"
            k = string.strip(sys.stdin.readline())
            while k == "":
                print "Please type the grid square. (For FD type none)"
                k = string.strip(sys.stdin.readline())
                k = k.upper() # kc7sda = changed the init so the grid square will be cap
            else:
                globDb.put('grid', k)
                qdb.globalshare('grid', k)  # global to db
                renew_title()
                print k, "will be the grid."
        if kfd !=2:
            #questions for vhf and fd, skip for wfd
            # Public Place
            z = ""
            print "Will the location be in a public place?"
            print "Y = yes and N = no"
            while z != "1":
                k = string.lower(string.strip(sys.stdin.readline())[:1])
                if k == "y": z = "1"
                if k == "n": z = '1'
                if z == "" : print "Press Y or N please"
            if k == "y":
                globDb.put('public', "A public location")
                qdb.globalshare('public', "A public location")  # global to db
                renew_title()
                print "Enjoy the public place."
            if k == "n":
                globDb.put('public', "")
                qdb.globalshare('public', "")  # global to db
                renew_title()
                print "maybe next year..."
            # Info Booth
            z = ""
            print "Will you have an info booth?"
            print "Y = yes and N = no"
            while z != "1":
                k = string.lower(string.strip(sys.stdin.readline())[:1])
                if k == "y": z = "1"
                if k == "n": z = '1'
                if z == "" : print "Press Y or N please"
            if k == "y":
                globDb.put('infob', "1")
                qdb.globalshare('infob', "1")  # global to db
                renew_title()
                print "Love information tables!"
            if k == "n":
                globDb.put('infob', "0")
                qdb.globalshare('infob', "0")  # global to db
                renew_title()
                print "An information table is easy points"
        #Time Master - oh yeah the big question
        z = ""
        print "\n It is recommended that the first computer"
        print "set up should also be the time master."
        print "\n IS THIS COMPUTER TIME CORRECT??? \n"
        print "Will this computer be the time master?"
        print "Y = yes and N = no"
        while z != "1":
            k = string.lower(string.strip(sys.stdin.readline())[:1])
            if k == "y": z = "1"
            if k == "n": z = '1'
            if z == "" : print "Press Y or N please"
        if k == "y":
            globDb.put('tmast', node)
            qdb.globalshare('tmast', node)  # global to db
            renew_title()
            print "Time travels to you!"
        if k == "n":
            pass                
    return


def exin(op):
    """extract Operator or Logger initials"""
    r = ""
    m = re.match(r'([a-z0-9]{2,3})', op)
    if m:
        r = m.group(1)
    return r


# sqlite database upgrade
# sqlite3.connect(":memory:", check_same_thread = False)
# I found this online to correct thread errors with sql locking to one thread only.
# I'm pretty sure I emailed this fix to Alan Biocca over a year ago. :(
# Scott Hibbs 7/5/2015


class SQDB:
    def __init__(self):
        self.dbPath = logdbf[0:-4] + '.sq3'
        print "Using database", self.dbPath
        self.sqdb = sqlite3.connect(self.dbPath, check_same_thread=False)  # connect to the database
        # Have to add FALSE here to get this stable - Scott Hibbs 7/17/2015
        self.sqdb.row_factory = sqlite3.Row  # namedtuple_factory
        self.curs = self.sqdb.cursor()  # make a database connection cursor
        sql = "create table if not exists qjournal(src text,seq int,date text,band " \
              "text,call text,rept text,powr text,oper text,logr text,primary key (src,seq))"
        self.curs.execute(sql)
        self.sqdb.commit()

    def readlog(self):  # ,srcId,srcIdx):            # returns list of log journal items
        print "Loading log journal from sqlite database"
        sql = "select * from qjournal"
        result = self.curs.execute(sql)
        nl = []
        for r in result:
            # print dir(r)
            nl.append("|".join(('q', r['src'], str(r['seq']), r['date'], r['band'], r['call'], r['rept'], r['powr'],
                                r['oper'], r['logr'], '')))
        # print nl
        return nl

    # Removed next(self) function. There is no self.result
    # and nothing calls sqdb.next() -Scott Hibbs 07/27/2015

    # def next(self):  # get next item from db in text format
    #     n = self.result
    #     nl = "|".join(n.src, n['seq'], n['date'], n['band'], n['call'], n['rept'], n['powr'], n['oper'], n['logr'])
    #     return nl

    def log(self, n):  # add item to journal logfile table (and other tables...)
        parms = (n.src, n.seq, n.date, n.band, n.call, n.rept, n.powr, n.oper, n.logr)
        sqdb = sqlite3.connect(self.dbPath)  # connect to the database
        #        self.sqdb.row_factory = sqlite3.Row   # namedtuple_factory
        curs = sqdb.cursor()  # make a database connection cursor
        # start commit, begin transaction
        sql = "insert into qjournal (src,seq,date,band,call,rept,powr,oper,logr) values (?,?,?,?,?,?,?,?,?)"
        curs.execute(sql, parms)
        # sql = "insert into qsos values (src,seq,date,band,call,sfx,rept,powr,oper,logr),(?,?,?,?,?,?,?,?,?,?)"
        # self.cur(sql,parms)
        # update qso count, scores? or just use q db count? this doesn't work well for different weights
        # update sequence counts for journals?
        sqdb.commit()  # do the commit
        if n.band == '*QST':
            print("QST\a " + n.rept+" -"+n.logr)  # The "\a" emits the beep sound for QST


class qsodb:
    byid = {}  # qso database by src.seq
    bysfx = {}  # call list by suffix.band
    hiseq = {}  # high sequence number by node
    lock = threading.RLock()  # sharing lock

    def new(self, source):
        n = qsodb()
        n.src = source  # source id
        return n

    def tolog(self):  # make log file entry
        sqdb.log(self)  # to database
        self.lock.acquire()  # and to ascii journal file as well
        fd = file(logdbf, "a")
        fd.write("\nq|%s|%s|%s|%s|%s|%s|%s|%s|%s|" % \
                 (self.src, self.seq,
                  self.date, self.band, self.call, self.rept,
                  self.powr, self.oper, self.logr))
        fd.close()
        self.lock.release()

    def ldrec(self, line):  # load log entry fm text
        (dummy, self.src, self.seq,
         self.date, self.band, self.call, self.rept,
         self.powr, self.oper, self.logr, dummy) = string.split(line, '|')
        self.seq = int(self.seq)
        self.dispatch('logf')

    def loadfile(self):
        print "Loading Log File"
        i, s, log = 0, 0, []
        global sqdb # setup sqlite database connection
        sqdb = SQDB()
        log = sqdb.readlog()  # read the database
        for ln in log:
            if ln[0] == 'q':  # qso db line 
                r = qdb.new(0)
                try:
                    r.ldrec(ln)
                    i += 1
                except ValueError, e:
                    print "  error, item skipped: ", e
                    print "    in:", ln
                    s += 1
                    # sqdb.log(r)
                    #  push a copy from the file into the
                    # database (temporary for transition)
        if i == 0 and s == 1:
            print "Log file not found, must be new"
            initialize()  # Set up routine - Scott Hibbs 7/26/2015
        else:
            print "  ", i, "Records Loaded,", s, "Errors"
        if i == 0:
            initialize()

    def cleanlog(self):
        """return clean filtered dictionaries of the log"""
        d, c, g = {}, {}, {}
        fdstart, fdend = gd.getv('fdstrt'), gd.getv('fdend')
        self.lock.acquire()
        for i in self.byid.values():  # copy, index by node, sequence
            k = "%s|%s" % (i.src, i.seq)
            d[k] = i
        self.lock.release()
        for i in d.keys():  # process deletes
            if d.has_key(i):
                iv = d[i]
                if iv.rept[:5] == "*del:":
                    dummy, st, sn, dummy = iv.rept.split(':')  # extract deleted id
                    k = "%s|%s" % (st, sn)
                    if k in d.keys():
                        #  print iv.rept,; iv.pr()
                        del (d[k])  # delete it
                        # else: print "del target missing",iv.rept
                    del (d[i])
        for i in d.keys():  # filter time window
            iv = d[i]
            if iv.date < fdstart or iv.date > fdend:
                # print "discarding out of date range",iv.date,iv.src,iv.seq
                del (d[i])
        for i in d.values():  # re-index by call-band
            dummy, dummy, dummy, dummy, call, dummy, dummy = self.qparse(i.call)  # extract call (not /...)
            k = "%s-%s" % (call, i.band)
            # filter out noncontest entries
            if ival(i.powr) == 0 and i.band[0] != '*': continue
            if i.band == 'off': continue
            if i.band[0] == '*': continue  # rm special msgs
            if i.src == 'gotanode':
                g[k] = i  # gota is separate dup space
            else:
                c[k] = i
        return (d, c, g)  # Deletes processed, fully Cleaned
        # by id, call-bnd, gota by call-bnd

    def prlogln(self, s):
        "convert log item to print format"
        # note that edit and color read data from the editor so
        # changing columns matters to these other functions.
        if s.band == '*QST':
            ln = "%8s %5s %-41s %-3s %-3s %4s %s" % \
                 (s.date[4:11], s.band, s.rept[:41], s.oper, s.logr, s.seq, s.src)
        elif s.band == '*set':
            ln = "%8s %5s %-11s %-29s %-3s %-3s %4s %s" % \
                 (s.date[4:11], s.band, s.call[:10], s.rept[:29], s.oper, s.logr, s.seq, s.src)
        elif s.rept[:5] == '*del:':
            ln = "%8s %5s %-7s %-33s %-3s %-3s %4s %s" % \
                 (s.date[4:11], s.band, s.call[:7], s.rept[:33], s.oper, s.logr, s.seq, s.src)
        else:
            ln = "%8s %5s %-11s %-24s %4s %-3s %-3s %4s %s" % \
                 (s.date[4:11], s.band, s.call[:11], s.rept[:24], s.powr, s.oper, s.logr, s.seq, s.src)
        return ln


    def prlog(self):
        "print log in time order"
        l = self.filterlog("")
        for i in l:
            print i

    def pradif(self):
        "print clean log in adif format"
        pgm = "FDLog_SCICSG (https://github.com/scotthibbs/FDLog_Enhanced)"
        print "<PROGRAMID:%d>%s" % (len(pgm), pgm)
        dummy, n, g = self.cleanlog()
        for i in n.values() + g.values():
            dat = "20%s" % i.date[0:6]
            tim = i.date[7:11]
            cal = i.call
            bnd = "%sm" % i.band[:-1]
            mod = i.band[-1:]
            if mod == 'p':
                mod = 'SSB'
            elif mod == 'c':
                mod = 'CW'
            elif mod == 'd':
                mod = 'RTTY'
            com = i.rept
            print "<QSO_DATE:8>%s" % (dat)
            print "<TIME_ON:4>%s" % (tim)
            print "<CALL:%d>%s" % (len(cal), cal)
            print "<BAND:%d>%s" % (len(bnd), bnd)
            print "<MODE:%d>%s" % (len(mod), mod)
            print "<QSLMSG:%d>%s" % (len(com), com)
            print "<EOR>"
            print

    def vhf_cabrillo(self):
        "output VHF contest cabrillo QSO data"
        band_map = {'6': '50', '2': '144', '220': '222', '440': '432', '900': '902', '1200': '1.2G'}
        dummy, n, dummy = self.cleanlog()
        mycall = string.upper(gd.getv('fdcall'))
        mygrid = gd.getv('grid')
        l = []
        print "QSO: freq  mo date       time call              grid   call              grid "
        for i in n.values():  # + g.values(): no gota in vhf
            freq = "%s" % i.band[:-1]  # band
            if freq in band_map: freq = band_map[freq]
            mod = i.band[-1:]  # mode
            if mod == "c": mod = "CW"
            if mod == "p": mod = "PH"
            if mod == "d": mod = "RY"
            date = "20%2s-%2s-%2s" % (i.date[0:2], i.date[2:4], i.date[4:6])
            tim = i.date[7:11]
            call = i.call
            grid = ''
            if '/' in call:  # split off grid from call
                call, grid = call.split('/')
            l.append("%sQSO: %-5s %-2s %-10s %4s %-13s     %-6s %-13s     %-6s" % (
                i.date, freq, mod, date, tim, mycall, mygrid, call, grid))
        l.sort()  # sort data with prepended date.time
        for i in l: print i[13:]  # rm sort key date.time
# kc7sda - added support for winter field day, this outputs the cabrillo format that is posted on their website. 
    def winter_fd(self):
        "output Winter Field day QSO data in cabrillo format:"
        #vars:
        band_map = {'160': '1800', '80': '3500', '40': '7000', '20': '14000','15': '21000','10': '28000','6': '50', '2': '144', '220': '222', '440': '432', '900': '902', '1200': '1.2G'}
        dummy, n, dummy = self.cleanlog()
        l = []
        mycall = string.upper(gd.getv('fdcall'))
        mycat = gd.getv('class')
        mystate, mysect = gd.getv('sect').split("-")
        #number of tx
        txnum = mycat[:-1]
        #data crunching:
        
        #QSO log generation:
        for i in n.values():
            freq = "%s" % i.band[:-1]  # band
            #if freq in band_map: freq = band_map[freq]
            mod = i.band[-1:]  # mode
            if mod == "c": mod = "CW"
            if mod == "p": mod = "PH"
            if mod == "d": mod = "DI" # per 2019 rules
            date = "20%2s-%2s-%2s" % (i.date[0:2], i.date[2:4], i.date[4:6])
            #date = "%2s-%2s-20%2s" % (i.date[2:4], i.date[4:6], i.date[0:2])
            tim = i.date[7:11]
            call = i.call
            cat, sect = i.rept.split(" ")
            if '/' in call:  # split off grid from call
                call, grid = call.split('/')
            #cabrillo example: QSO:  40 DI 2019-01-19 1641 KC7SDA        1H  WWA    KZ9ZZZ        1H  NFL   
            l.append("%sQSO:  %-5s %-2s %-10s %4s %-10s %-2s  %-5s %-10s %-2s  %-5s" % (
                i.date,freq, mod, date, tim, mycall, mycat, mysect, call, cat, sect))
        l.sort()  # sort data with prepended date.time
        
        #check operator (single or multi op):
        cat_op = ""
        if len(participants) > 1:
            cat_op = "MULTI-OP"
        else:
            cat_op = "SINGLE-OP"
            
        #check fixed or portable?
        
        #tx power:
        
        #calls for ops:
        ops_calls_list = []
        #print(participants)
        #participants: {u'am': u'am, art miller, kc7sda, 37, '}
        for i in participants.values():
            dummy, dummy, cs, dummy, dummy = i.split(", ")
            ops_calls_list.append(string.upper(cs))
        ops_calls = ', '.join(ops_calls_list)
        
        #output
        print "Winter field day Cabrillo output"
        print "START-OF-LOG: 3.0"
        print "Created-By: FDLog_SCICSG (https://github.com/scotthibbs/FDLog_Enhanced)"
        print "CONTEST: WFD "
        print "CALLSIGN: " + mycall
        print "LOCATION: " + mystate
        print "ARRL-SECTION: " + mysect
        print "CATEGORY-OPERATOR: " + cat_op
        print "CATEGORY-STATION: " #fixed or portable
        print "CATEGORY_TRANSMITTER: " + txnum # how many transmitters
        print "CATEGORY_POWER: LOW" #qrp low or high
        print "CATEGORY_ASSISTED: NON-ASSISTED" #assisted or non-assisted
        print "CATEGORY-BAND: ALL" # leave for wfd
        print "CATEGORY-MODE: MIXED" #leave for wfd
        print "CATEGORY-OVERLAY: OVER-50" # leave for wfd
        print "SOAPBOX: " #fill in?
        print "CLAIMED-SCORE: " #figure out score and add
        print "OPERATORS: " + ops_calls #agregate the ops
        print "NAME: " + gd.getv('fmname')
        print "ADDRESS: " + gd.getv('fmad1')
        print "ADDRESS-CITY: " + gd.getv('fmcity')
        print "ADDRESS-STATE: " + gd.getv('fmst')
        print "ADDRES-POSTALCODE: " + gd.getv('fmzip') #zip
        print "ADDRESS-COUNTRY: USA" # hard coded for now, possibly change later
        print "EMAIL: " + gd.getv('fmem') #email address
        #print log:
        for i in l: print i[13:]  # rm sort key date.time
        print "END-OF-LOG:"

    def filterlog(self, filt):
        """list filtered (by bandm) log in time order, nondup valid q's only"""
        l = []
        dummy, n, g = self.cleanlog()
        for i in n.values() + g.values():
            if filt == "" or re.match('%s$' % filt, i.band):
                l.append(i.prlogln(i))
        l.sort()
        return l

    def filterlog2(self, filt):
        "list filtered (by bandm) log in time order, including special msgs"
        l = []
        m, dummy, dummy = self.cleanlog()
        for i in m.values():
            if filt == "" or re.match('%s$' % filt, i.band):
                l.append(i.prlogln(i))
        l.sort()
        return l

    def filterlogst(self, filt):
        "list filtered (by nod) log in time order, including special msgs"
        l = []
        m, dummy, dummy = self.cleanlog()
        for i in m.values():
            if re.match('%s$' % filt, i.src):
                l.append(i.prlogln(i))
        l.sort()
        return l

    def qsl(self, time, call, bandmod, report):
        "log a qsl"
        return self.postnewinfo(time, call, bandmod, report)

    def qst(self, msg):
        "put a qst in database + log"
        return self.postnewinfo(now(), '', '*QST', msg)

    def globalshare(self, name, value):
        "put global var set in db + log"
        return self.postnewinfo(now(), name, '*set', value)

    def postnewinfo(self, time, call, bandmod, report):
        "post new locally generated info"
        # s = self.new(node)
        #        s.date,s.call,s.band,s.rept,s.oper,s.logr,s.powr =
        #            time,call,bandmod,report,exin(operator),exin(logger),power
        # s.seq = -1
        return self.postnew(time, call, bandmod, report, exin(operator),
                            exin(logger), power)
        # s.dispatch('user') # removed in 152i

    def postnew(self, time, call, bandmod, report, oper, logr, powr):
        "post new locally generated info"
        s = self.new(node)
        s.date, s.call, s.band, s.rept, s.oper, s.logr, s.powr = time, call, bandmod, report, oper, logr, powr
        s.seq = -1
        return s.dispatch('user')

    def delete(self, nod, seq, reason):
        "remove a Q by creating a delete record"
        #        print "del",nod,seq
        a, dummy, dummy = self.cleanlog()
        k = "%s|%s" % (nod, seq)
        if a.has_key(k) and a[k].band[0] != '*':  # only visible q
            tm, call, bandmod = a[k].date, a[k].call, a[k].band
            rept = "*del:%s:%s:%s" % (nod, seq, reason)
            s = self.new(node)
            s.date, s.call, s.band, s.rept, s.oper, s.logr, s.powr = \
                now(), call, bandmod, rept, exin(operator), exin(logger), 0
            s.seq = -1
            s.dispatch('user')
            txtbillb.insert(END, " DELETE Successful %s %s %s\n" % (tm, call, bandmod))
            logw.configure(state=NORMAL)
            logw.delete(0.1,END)
            logw.insert(END, "\n")
            # Redraw the logw text window (on delete) to only show valid calls in the log. 
            # This avoids confusion by only listing items in the log to edit in the future.
            # Scott Hibbs KD4SIR - July 3, 2018
            l = []
            for i in sorted(a.values()):
                if i.seq == seq:
                    continue
                else:
                    l.append(logw.insert(END, "\n"))
                    if nod == node:
                        l.append(logw.insert(END, i.prlogln(i), "b"))    
                    else:
                        l.append(logw.insert(END, i.prlogln(i)))
                        l.append(logw.insert(END, "\n"))
            logw.insert(END, "\n")
            logw.configure(state=DISABLED)
        else:
            txtbillb.insert(END, " DELETE Ignored [%s,%s] Not Found\n" % (nod, seq))
            topper()

    def todb(self):
        """"Q record object to db"""
        r = None
        self.lock.acquire()
        current = self.hiseq.get(self.src, 0)
        self.seq = int(self.seq)
        if self.seq == current + 1:  # filter out dup or nonsequential
            self.byid["%s.%s" % (self.src, self.seq)] = self
            self.hiseq[self.src] = current + 1
            ##            if debug: print "todb:",self.src,self.seq
            r = self
        elif self.seq == current:
            if debug: print "dup sequence log entry ignored"
        else:
            print "out of sequence log entry ignored", self.seq, current + 1
        self.lock.release()
        return r

    def pr(self):
        """"print Q record object"""
        sms.prmsg(self.prlogln(self))

    def dispatch(self, src):
        """"process new db rec (fm logf,user,net) to where it goes"""
        self.lock.acquire()
        self.seq = int(self.seq)
        if self.seq == -1:  # assign new seq num
            self.seq = self.hiseq.get(self.src, 0) + 1
        r = self.todb()
        self.lock.release()
        if r:  # if new
            self.pr()
            if src != 'logf': self.tolog()
            if src == 'user': net.bc_qsomsg(self.src, self.seq)
            if self.band == '*set':
                m = gd.setv(r.call, r.rept, r.date)
                if not m: r = None
            else:
                self.logdup()
        return r

    def bandrpt(self):
        """band report q/band pwr/band, q/oper q/logr q/station"""
        qpb, ppb, qpop, qplg, qpst, tq, score, maxp = {}, {}, {}, {}, {}, 0, 0, 0
        cwq, digq, fonq = 0, 0, 0
        qpgop, gotaq, nat, sat = {}, 0, [], []
        dummy, c, g = self.cleanlog()
        for i in c.values() + g.values():
            if re.search('sat', i.band): sat.append(i)
            if 'n' in i.powr: nat.append(i)
            # stop ignoring above 100 q's per oper per new gota rules. 6/05 akb
            # GOTA q's stop counting over 400 (500 in 2009)
            if i.src == 'gotanode':  # analyze gota limits
                qpgop[i.oper] = qpgop.get(i.oper, 0) + 1
                qpop[i.oper] = qpop.get(i.oper, 0) + 1
                qplg[i.logr] = qplg.get(i.logr, 0) + 1
                qpst[i.src] = qpst.get(i.src, 0) + 1
                if gotaq >= 500: continue  # stop over 500 total
                gotaq += 1
                tq += 1
                score += 1
                if 'c' in i.band:
                    cwq += 1
                    score += 1
                    qpb['gotac'] = qpb.get('gotac', 0) + 1
                    ppb['gotac'] = max(ppb.get('gotac', 0), ival(i.powr))
                if 'd' in i.band:
                    digq += 1
                    score += 1
                    qpb['gotad'] = qpb.get('gotad', 0) + 1
                    ppb['gotad'] = max(ppb.get('gotad', 0), ival(i.powr))
                if 'p' in i.band:
                    fonq += 1
                    qpb['gotap'] = qpb.get('gotap', 0) + 1
                    ppb['gotap'] = max(ppb.get('gotap', 0), ival(i.powr))
                continue
            qpb[i.band] = qpb.get(i.band, 0) + 1
            ppb[i.band] = max(ppb.get(i.band, 0), ival(i.powr))
            maxp = max(maxp, ival(i.powr))
            qpop[i.oper] = qpop.get(i.oper, 0) + 1
            qplg[i.logr] = qplg.get(i.logr, 0) + 1
            qpst[i.src] = qpst.get(i.src, 0) + 1
            score += 1
            tq += 1
            if 'c' in i.band:
                score += 1  # extra cw and dig points
                cwq += 1
            if 'd' in i.band:
                score += 1
                digq += 1
            if 'p' in i.band:
                fonq += 1
        return (qpb, ppb, qpop, qplg, qpst, tq, score, maxp, cwq, digq, fonq, qpgop, gotaq, nat, sat)

    def bands(self):
        """ .ba command band status station on, q/band, xx needs upgd"""
        # This function from 152i
        qpb, tmlq, dummy = {}, {}, {}
        self.lock.acquire()
        for i in self.byid.values():
            if ival(i.powr) < 1: continue
            if i.band == 'off': continue
            v = 1
            if i.rept[:5] == '*del:': v = -1
            qpb[i.band] = qpb.get(i.band, 0) + v  # num q's
            tmlq[i.band] = max(tmlq.get(i.band, ''), i.date)  # time of last (latest) q
        self.lock.release()
        print
        print "Stations this node is hearing:"
        # scan for stations on bands
        for s in net.si.nodes.values():  # xx
            # print dir(s)
            print s.nod, s.host, s.ip, s.stm
            # nod[s.bnd] = s.nod_on_band()
            # print "%8s %4s %18s %s"%(s.nod,s.bnd,s.msc,s.stm)
            # s.stm,s.nod,seq,s.bnd,s.msc
            # i.tm,i.fnod,i.fip,i.stm,i.nod,i.seq,i.bnd,i.msc
        d = {}
        print
        print "Node Info"
        print "--node-- band --opr lgr pwr----- last"
        for t in net.si.nodinfo.values():
            dummy, dummy, age = d.get(t.nod, ('', '', 9999))
            if age > t.age: d[t.nod] = (t.bnd, t.msc, t.age)
        for t in d:
            print "%8s %4s %-18s %4s" % (t, d[t][0], d[t][1], d[t][2])  # t.bnd,t.msc,t.age)
        print
        print "  band -------- cw ----- ------- dig ----- ------- fon -----"
        print "          nod  Q's  tslq    nod  Q's  tslq    nod  Q's  tslq"
        #      xxxxxx yyyyyy xxxx xxxxx yyyyyy xxxx xxxxx yyyyyy xxxx xxxxx
        t1 = now()
        for b in (160, 80, 40, 20, 15, 10, 6, 2, 220, 440, 900, 1200, 'Sat'):
            print "%6s" % b,
            for m in 'cdp':
                bm = "%s%s" % (b, m)
                # be nice to do min since q instead of time of last q --- DONE
                t2 = tmlq.get(bm, '')  # time since last Q minutes
                if t2 == '':
                    tdif = ''
                else:
                    tdif = int(tmsub(t1, t2) / 60.)
                    tmin = tdif % 60
                    tdhr = tdif / 60
                    if tdhr > 99: tdhr = 99
                    tdif = tdhr * 100 + tmin
                    #    if tdif > 9999: tdif = 9999
                    #    tdif = str(int(tdif))           # be nice to make this hhmm instead of mmmm
                #  t = "" # time of latest Q hhmm
                #  m = re.search(r"([0-9]{4})[0-9]{2}$",tmlq.get(bm,''))
                #  if m: t = m.group(1)
                nob = net.si.nod_on_band(bm)  # node now on band
                if len(nob) == 0:
                    nob = ''  # list take first item if any
                else:
                    nob = nob[0]
                print "%6s %4s %5s" % \
                      (nob[0:6], qpb.get(bm, ''), tdif),  # was t
                #    (nod.get(bm,'')[0:5],qpb.get(bm,''),t),
            print

    def sfx2call(self, suffix, band):
        """return calls w suffix on this band"""
        return self.bysfx.get(suffix + '.' + band, [])

    def qparse(self, line):
        """"qso/call/partial parser"""
        # check for valid input at each keystroke
        # return status, time, extended call, base call, suffix, report
        # stat: 0 invalid, 1 partial, 2 suffix, 3 prefix, 4 call, 5 full qso
        # example --> :12.3456 wb4ghj/ve7 2a sf Steve in CAN
        stat, tm, pfx, sfx, call, xcall, rept = 0, '', '', '', '', '', ''
        # break into basic parts: time, call, report
        m = re.match(r'(:([0-9.]*)( )?)?(([a-z0-9/]+)( )?)?([0-9a-zA-Z ]*)$', line)
        if m:
            tm = m.group(2)
            xcall = m.group(5)
            rept = m.group(7)
            stat = 0
            if m.group(1) > '' or xcall > '': stat = 1
            ##            print; print "tm [%s] xcall [%s] rept [%s]"%(tm,xcall,rept)
            if tm > '':
                stat = 0
                m = re.match(r'([0-3]([0-9]([.]([0-5]([0-9]([0-5]([0-9])?)?)?)?)?)?)?$', tm)
                if m:
                    stat = 1  # at least partial time
            if xcall > '':
                stat = 0  # invalid unless something matches
                m = re.match(r'([a-z]+)$', xcall)
                if m:
                    stat = 2  # suffix
                    sfx = xcall
                m = re.match(r'([0-9]+)$', xcall)
                if m:
                    stat = 2  # suffix
                    sfx = xcall
                m = re.match(r'([a-z]+[0-9]+)$', xcall)
                if m:
                    stat = 3  # prefix
                    pfx = xcall
                m = re.match(r'([0-9]+[a-z]+)$', xcall)
                if m:
                    stat = 3  # prefix
                    pfx = xcall
                m = re.match(r'(([a-z]+[0-9]+)([a-z]+))(/[0-9a-z]*)?$', xcall)
                if m:
                    stat = 4  # whole call
                    call = m.group(1)
                    pfx = m.group(2)
                    sfx = m.group(3)
                m = re.match(r'(([0-9]+[a-z]+)([0-9]+))(/[0-9a-z]*)?$', xcall)
                if m:
                    stat = 4  # whole call
                    call = m.group(1)
                    pfx = m.group(2)
                    sfx = m.group(3)
                if (stat == 4) & (rept > ''):
                    stat = 0
                    m = re.match(r'[0-9a-zA-Z]+[0-9a-zA-Z ]*$', rept)
                    if m:
                        stat = 5  # complete qso
                if len(xcall) > 12: stat = 0  # limit lengths
                if len(pfx) > 5: stat = 0
                if len(sfx) > 3: stat = 0
                if tm:  # if forced time exists
                    if len(tm) < 7:  # it must be complete
                        stat = 0
                        #        print "stat[%s] time[%s] pfx[%s] sfx[%s] call[%s] xcall[%s] rpt[%s]"%\
                        #              (stat,tm,pfx,sfx,call,xcall,rept)
        return (stat, tm, pfx, sfx, call, xcall, rept)

    def dupck(self, wcall, band):
        """check for duplicate call on this band"""
        dummy, dummy, dummy, sfx, call, xcall, dummy = self.qparse(wcall)
        if gd.getv('contst').upper() == "VHF":
            return xcall in self.sfx2call(sfx, band)  # vhf contest
        return call in self.sfx2call(sfx, band)  # field day

    # Added function to test against participants like dupes Scott Hibbs KD4SIR Jan/29/2017
    # Added function to test against call and gota call like dupes Scott Hibbs KD4SIR Mar/23/2017
    def partck(self, wcall):
        """ check for participants to act as dupes in this event"""
        dummy, dummy, dummy, dummy, call, xcall, dummy = self.qparse(wcall)
        l = []
        for i in participants.values():
            l.append(i)
            dummy, dummy, dcall, dummy, dummy = string.split(i, ', ')
            if dcall == xcall:
                # to debug: print ("%s dcall matches %s xcall" % (dcall, xcall))
                if gd.getv('contst').upper() == "VHF":
                    return xcall  # vhf contest
                return call # field day
            if dcall == call:
                #to debug: print ("%s dcall matches %s call" % (dcall, call))
                if gd.getv('contst').upper() == "VHF":
                    return xcall # vhf contest
                return call # field day

    def logdup(self):
        """enter into dup log"""
        dummy, dummy, dummy, sfx, dummy, xcall, dummy = self.qparse(self.call)
        #        print call,sfx,self.band
        key = sfx + '.' + self.band
        self.lock.acquire()
        if self.rept[:5] == "*del:":
            self.redup()
        else:
            # duplog everything with nonzero power, or on band off (test)
            if (self.band == 'off') | (ival(self.powr) > 0):
                # dup only if Q and node type match (gota/not)
                if (node == 'gotanode') == (self.src == 'gotanode'):
                    if self.bysfx.has_key(key):  # add to suffix db
                        self.bysfx[key].append(xcall)
                    else:
                        self.bysfx[key] = [xcall]
                        #                else: print "node type mismatch",node,self.src
        self.lock.release()

    def redup(self):
        """rebuild dup db"""
        dummy, c, g = self.cleanlog()
        self.lock.acquire()
        #        print self.bysfx
        qsodb.bysfx = {}
        for i in c.values() + g.values():
            #            print i.call,i.band
            i.logdup()
        self.lock.release()
        #        print qsodb.bysfx

    def wasrpt(self):
        """worked all states report"""
        sectost, stcnt, r, e = {}, {}, [], []
        try:
            fd = file("Arrl_sect.dat", "r")  # read section data
            while 1:
                ln = fd.readline()  # read a line and put in db
                if not ln: break
                # if ln == "": continue
                if ln[0] == '#': continue
                try:
                    sec, st, dummy, dummy = string.split(ln, None, 3)
                    sectost[sec] = st
                    stcnt[st] = 0
                #                    print sec,st,desc
                except ValueError, e:
                    print "rd arrl sec dat err, itm skpd: ", e
            fd.close()
        except IOError, e:
            print "io error during arrl section data file load", e
        a, dummy, dummy = self.cleanlog()
        for i in a.values():
            sect, state = "", ""
            if i.rept[:1] == '*': continue
            if i.band[0] == '*': continue
            if i.band == 'off': continue
            if i.powr == '0': continue
            m = re.match(r' *[0-9]+[a-fiohA-FIOH] +([A-Za-z]{2,4})', i.rept)
            if m:
                sect = m.group(1)
                sect = string.upper(sect)
                state = sectost.get(sect, "")
                #                print "sec",sect,"state",state
                if state: stcnt[state] += 1
            if not state:
                #                print "section not recognized in:\n  %s"%i.prlogln()
                #                print "sec",sect,"state",state
                e.append(i.prlogln(i))
        h, n = [], []  # make have and need lists
        for i in stcnt.keys():
            if i != "--":
                if stcnt[i] == 0:
                    n.append("%s" % i)
                else:
                    h.append("%s" % i)
        n.sort()
        r.append("Worked All States Report\n%s Warning(s) Below\nNeed %s States:" % (len(e), len(n)))
        for i in n:
            r.append(i)
        h.sort()
        r.append("\nHave %s States:" % len(h))
        for i in h:
            r.append("%s %s" % (i, stcnt[i]))
        if len(e) > 0:
            r.append("\nWarnings - Cannot Discern US Section in Q(s):\n")
            for i in e:
                r.append(i)
        return r

class node_info:
    """Threads and networking section"""
    nodes = {}
    nodinfo = {}
    # rembcast = {}
    #  This was not remarked out of the 2015_stable version
    #  Scott Hibbs 7/3/2015
    lock = threading.RLock()  # reentrant sharing lock

    def sqd(self, src, seq, t, b, c, rp, p, o, l):
        """process qso data fm net into db"""  # excessive cohesion?
        s = qdb.new(src)
        s.seq, s.date, s.call, s.band, s.rept, s.oper, s.logr, s.powr = \
            seq, t, c, b, rp, o, l, p
        s.dispatch('net')

    def netnum(self, ip, mask):
        """extract net number"""
        i, m, r = [], [], {}
        i = string.split(ip, '.')
        m = string.split(mask, '.')
        for n in (0, 1, 2, 3):
            r[n] = ival(i[n]) & ival(m[n])
        return "%s.%s.%s.%s" % (r[0], r[1], r[2], r[3])

    def ssb(self, pkt_tm, host, sip, nod, stm, stml, ver, td):
        """process status broadcast (first line)"""
        self.lock.acquire()
        if not self.nodes.has_key(nod):  # create if new
            self.nodes[nod] = node_info()
            if nod != node:
                print "New Node Heard", host, sip, nod, stm, stml, ver, td
        i = self.nodes[nod]
        #        if debug: print "ssb before assign",i.nod,i.stm,i.bnd
        i.ptm, i.nod, i.host, i.ip, i.stm, i.age = \
            pkt_tm, nod, host, sip, stm, 0
        self.lock.release()
        #   if debug:
        #  print "ssb:",pkt_tm,host,sip,nod,stm,stml,ver,td

    def sss(self, pkt_tm, fnod, sip, nod, seq, bnd, msc, age):
        """process node status bcast (rest of bcast lines)"""
        self.lock.acquire()
        key = "%s-%s" % (fnod, nod)
        if not self.nodinfo.has_key(key):
            self.nodinfo[key] = node_info()  # create new
            #            if debug: print "sss: new nodinfo instance",key
        i = self.nodinfo[key]
        i.tm, i.fnod, i.fip, i.nod, i.seq, i.bnd, i.msc, i.age = \
            pkt_tm, fnod, sip, nod, seq, bnd, msc, int(age)
        self.lock.release()
        #        if debug: print "sss:",i.age,i.nod,i.seq,i.bnd

    def age_data(self):
        """increment age and delete old band"""
        # updates from 152i
        t = now()[7:]  # time hhmmss
        self.lock.acquire()
        for i in self.nodinfo.values():
            if i.age < 999:
                i.age += 1
                # if debug: print "ageing nodinfo",i.fnod,i.nod,i.bnd,i.age
            if i.age > 55 and i.bnd:
                print t, "age out info from", i.fnod, "about", i.nod, "on", i.bnd, "age", i.age
                i.bnd = ""
        for i in self.nodes.values():
            if i.age < 999: i.age += 1
        self.lock.release()

    def fill_requests_list(self):
        """return list of fills needed"""
        r = []
        self.lock.acquire()
        for i in self.nodinfo.values():  # for each node
            j = qdb.hiseq.get(i.nod, 0)
            if int(i.seq) > j:  # if they have something we need
                r.append((i.fip, i.nod, j + 1))  # add req for next to list
                # if debug: print "req fm",i.fip,"for",i.nod,i.seq,"have",j+1
        self.lock.release()
        return r  # list of (addr,src,seq)

    def node_status_list(self):
        """return list of node status tuples"""
        sum = {}  # summary dictionary
        self.lock.acquire()
        i = node_info()  # update our info
        i.nod, i.bnd, i.age = node, band, 0
        i.msc = "%s %s %sW" % (exin(operator), exin(logger), power)
        sum[node] = i
        for i in qdb.hiseq.keys():  # insure all db nod on list
            if not sum.has_key(i):  # add if new
                j = node_info()
                j.nod, j.bnd, j.msc, j.age = i, '', '', 999
                sum[i] = j
                # if debug: print "adding nod fm db to list",i
        for i in self.nodinfo.values():  # browse bcast data
            if not sum.has_key(i.nod):
                j = node_info()
                j.nod, j.bnd, j.msc, j.age = i.nod, '', '', 999
                sum[i.nod] = j
            j = sum[i.nod]  # collect into summary
            #            if debug:
            #                print "have",      j.nod,j.age,j.bnd,j.msc
            #                print "inspecting",i.nod,i.age,i.bnd,i.msc
            if i.age < j.age:  # keep latest wrt src time
                #                if debug:
                #                    print "updating",j.nod,j.age,j.bnd,j.msc,\
                #                                "to",      i.age,i.bnd,i.msc
                j.bnd, j.msc, j.age = i.bnd, i.msc, i.age
        self.lock.release()
        r = []  # form the list (xx return sum?)
        for s in sum.values():
            seq = qdb.hiseq.get(s.nod, 0)  # reflect what we have in our db
            if seq or s.bnd:  # only report interesting info
                r.append((s.nod, seq, s.bnd, s.msc, s.age))
        return r  # list of (nod,seq,bnd,msc,age)

    def nod_on_band(self, band):
        """return list of nodes on this band"""
        r = []
        for s in self.node_status_list():
            # print s[0],s[2] # (nod,seq,bnd,msc,age)
            if band == s[2]:
                r.append(s[0])
        return r

    def nod_on_bands(self):
        """return dictionary of list of nodes indexed by band and counts"""
        r, hf, vhf, gotanode = {}, 0, 0, 0
        for s in self.node_status_list():
            #            print s[0],s[2]
            if not r.has_key(s[2]):
                r[s[2]] = []
            r[s[2]].append(s[0])
            if s[2] == 'off' or s[2] == "": continue
            if s[0] == 'gotanode':
                gotanode += 1
            else:
                b = ival(s[2])
                if b > 8 or b < 200: hf += 1
                if b < 8 or b > 200: vhf += 1
        return r, hf, vhf, gotanode


class netsync:
    """network database synchronization"""
	# removed netmask - it isn't used anywhere in the program from what I can tell (do a search for 'netmask' this is the only place you find it)
	# re-coded the ip address calculation to smooth it out and make it cross platform compatible. - Art Miller KC7SDA Jul/01/2018
    #netmask = '255.255.255.0'
    rem_adr = ""  # remote bc address
    authkey = hashlib.md5()
    pkts_rcvd, fills, badauth_rcvd, send_errs = 0, 0, 0, 0
    hostname = socket.gethostname()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
            s.connect(("8.8.8.8", 53))
            my_addr = s.getsockname()[0]
    except:
            my_addr = '127.0.0.1'
    finally:
            s.close()
    print "\n IP address is:  %s\n" % my_addr
    bc_addr = re.sub(r'[0-9]+$', '255', my_addr)  # calc bcast addr
    si = node_info()  # node info

    def setport(self, useport):
        """set net port"""
        self.port = useport
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # send socket
        self.skt.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Erics linux fix
        self.skt.bind((self.my_addr, self.port + 1))

    def setauth(self, newauth):
        """set authentication key code base, copy on use"""
        global authk
        authk = newauth
        seed = "2004070511111akb"  # change when protocol changes

        # self.authkey = md5.new(newauth+seed)
        self.authkey = hashlib.md5(newauth + seed)

    def auth(self, msg):
        """calc authentication hash"""
        h = self.authkey.copy()
        h.update(msg)
        return h.hexdigest()

    def ckauth(self, msg):
        """check authentication hash"""
        h, m = msg.split('\n', 1)
        #        print h; print self.auth(m); print
        return h == self.auth(m)

    def sndmsg(self, msg, addr):
        """send message to address list"""
        if authk != "" and node != "":
            amsg = self.auth(msg) + '\n' + msg
            addrlst = []
            if addr == 'bcast':
                addrlst.append(self.bc_addr)
            else:
                addrlst.append(addr)
            for a in addrlst:
                if a == "": continue
                if a == '0.0.0.0': continue
                if debug: print "send to ", a; print msg
                try:
                    self.skt.sendto(amsg, (a, self.port))
                except socket.error, e:
                    self.send_errs += 1
                    print "error, pkt xmt failed %s %s [%s]" % (now(), e.args, a)

    def send_qsomsg(self, nod, seq, destip):
        """send q record"""
        key = nod + '.' + str(seq)
        if qdb.byid.has_key(key):
            i = qdb.byid[key]
            msg = "q|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" % \
                  (i.src, i.seq, i.date, i.band, i.call, i.rept, i.powr, i.oper, i.logr)
            self.sndmsg(msg, destip)

    def bc_qsomsg(self, nod, seq):
        """broadcast new q record"""
        self.send_qsomsg(nod, seq, self.bc_addr)

    def bcast_now(self):
        msg = "b|%s|%s|%s|%s|%s|%s\n" % \
              (self.hostname, self.my_addr, node, now(), mclock.level, version)
        for i in self.si.node_status_list():
            msg += "s|%s|%s|%s|%s|%s\n" % i  # nod,seq,bnd,msc,age
            # if debug: print i
        self.sndmsg(msg, 'bcast')  # broadcast it

    def fillr(self):
        """filler thread requests missing database records"""
        time.sleep(0.2)
        if debug: print "filler thread starting"

        while 1:
            time.sleep(.1)  # periodically check for fills
            if debug: time.sleep(1)  # slow for debug
            r = self.si.fill_requests_list()
            self.fills = len(r)
            if self.fills:
                p = random.randrange(0, len(r))  # randomly select one
                c = r[p]
                msg = "r|%s|%s|%s\n" % (self.my_addr, c[1], c[2])  # (addr,src,seq)
                self.sndmsg(msg, c[0])
                print "req fill", c

    def rcvr(self):
        """receiver thread processes incoming packets"""
        if debug: print "receiver thread starting"
        r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        r.bind(('', self.port))
        while 1:
            msg, addr = r.recvfrom(800)
            if addr[0] != self.my_addr:
                self.pkts_rcvd += 1
            # if authk == "": continue             # skip till auth set
            pkt_tm = now()
            host, sip, fnod, stm = '', '', '', ''
            if debug: print "rcvr: %s: %s" % (addr, msg),  # xx
            if not self.ckauth(msg):  # authenticate packet
                # if debug: sms.prmsg("bad auth from: %s"%addr)
                print "bad auth from:", addr
                self.badauth_rcvd += 1
            else:
                lines = msg.split('\n')  # decode lines
                for line in lines[1:-1]:  # skip auth hash, blank at end
                    #                    if debug: sms.prmsg(line)
                    fields = line.split('|')
                    if fields[0] == 'b':  # status bcast
                        host, sip, fnod, stm, stml, ver = fields[1:]
                        td = tmsub(stm, pkt_tm)
                        self.si.ssb(pkt_tm, host, sip, fnod, stm, stml, ver, td)
                        mclock.calib(fnod, stml, td)
                        if abs(td) >= tdwin:
                            print 'Incoming packet clock error', td, host, sip, fnod, pkt_tm
                        if showbc:
                            print "bcast", host, sip, fnod, ver, pkt_tm, td
                    elif fields[0] == 's':  # source status
                        nod, seq, bnd, msc, age = fields[1:]
                        # if debug: print pkt_tm,fnod,sip,stm,nod,seq,bnd,msc
                        self.si.sss(pkt_tm, fnod, sip, nod, seq, bnd, msc, age)
                    elif fields[0] == 'r':  # fill request
                        destip, src, seq = fields[1:]
                        # if debug: print destip,src,seq
                        self.send_qsomsg(src, seq, destip)
                    elif fields[0] == 'q':  # qso data
                        src, seq, stm, b, c, rp, p, o, l = fields[1:]
                        # if debug: print src,seq,stm,b,c,rp,p,o,l
                        self.si.sqd(src, seq, stm, b, c, rp, p, o, l)
                    else:
                        sms.prmsg("msg not recognized %s" % addr)

    def start(self):
        """launch all threads"""
        #        global node
        print "This host:", self.hostname, "IP:", self.my_addr, "Mask:", self.bc_addr
        #        if (self.hostname > "") & (node == 's'):
        #            node = self.hostname             # should filter chars
        #        print "Node ID:",node
        print "Launching threads"
        #        thread.start_new_thread(self.bcastr,())
        thread.start_new_thread(self.fillr, ())
        thread.start_new_thread(self.rcvr, ())
        if debug:
            print "threads launched"
        time.sleep(0.5)  # let em print
        print "Startup complete"


class global_data:
    """Global data stored in the journal"""
    byname = {}

    def new(self, name, desc, defaultvalue, okgrammar, maxlen):
        i = global_data()  # create
        i.name = name  # set
        i.val = defaultvalue
        i.okg = okgrammar
        i.maxl = maxlen
        i.ts = ""
        i.desc = desc
        self.byname[name] = i
        return i

    def setv(self, name, value, timestamp):
        if node == "":
            txtbillb.insert(END, "error - no node id\n")
            return
        if name[:2] == 'p:':  # set oper/logr
            i = self.byname.get(name, self.new(name, '', '', '', 0))
        else:
            if not self.byname.has_key(name):  # new
                return "error - invalid global data name: %s" % name
            i = self.byname[name]
            if len(value) > i.maxl:  # too long
                return "error - value too long: %s = %s" % (name, value)
            if name == 'grid':
                value = value.upper() # kc7sda - added to properly format grid (ie CN88 not cn88)
            if not re.match(i.okg, value):  # bad grammar
                return "set error - invalid value: %s = %s" % (name, value)
        if timestamp > i.ts:  # timestamp later?
            i.val = value
            i.ts = timestamp
            if name[:2] == 'p:':
                ini, name, dummy, dummy, dummy = string.split(value, ', ')
                participants[ini] = value
                if name == 'delete':
                    del (participants[ini])
                buildmenus()
                # else: print "set warning - older value discarded"

    def getv(self, name):
        if not self.byname.has_key(name):  # new
            return "get error - global data name %s not valid" % name
        return self.byname[name].val

    def sethelp(self):
        l = ["   Set Commands\n   For the Logging Guru In Charge\n   eg: .set <parameter> <value>\n"]  # spaced for sort
        for i in self.byname.keys():
            if i[:2] != 'p:':  # skip ops in help display
                l.append("  %-6s  %-43s  '%s'" % (i, self.byname[i].desc, self.byname[i].val))
        l.sort()
        viewtextl(l)

# kc7sda - modifed  the sect setting regex to accept both lower and upper case
# kc7sda - added additional form fields (also fixed 'from' to 'form') for wfd NOTE: set commands have a max length of 6!
gd = global_data()
for name, desc, default, okre, maxlen in (
        ('class', '<n><A-F>       FD class (eg 2A)', '2A', r'[1-9][0-9]?[a-fihoA-FIHO]$', 3),
        ('contst', '<text>         Contest (FD,WFD,VHF)', 'FD', r'fd|FD|wfd|WFD|vhf|VHF$', 3),
        ('fdcall', '<CALL>         FD call', '', r'[a-zA-Z0-9]{3,6}$', 6),
        ('gcall', '<CALL>         GOTA call', '', r'[a-zA-Z0-9]{3,6}$', 6),
        ('sect', '<CC-Ccccc...>  ARRL section', '<section>', r'[a-zA-Z]{2,3}-[a-zA-Z ]{2,20}$', 24),
        ('grid', '<grid>         VHF grid square', '', r'[A-Z]{2}[0-9]{2}$', 4),
        ('grpnam', '<text>         group name', '', r'[A-Za-z0-9 #.:-]{4,35}$', 35),
        ('fmcall', '<CALL>         entry form call', '', r'[a-zA-Z0-9]{3,6}$', 6),
        ('fmname', '<name>         entry form name', '', r'[A-Za-z0-9 .:-]{0,35}$', 35),
        ('fmad1', '<text>         entry form address line 1', '', r'[A-Za-z0-9 #.,:-]{0,35}$', 35),
        ('fmad2', '<text>         entry form address line 2', '', r'[A-Za-z0-9 #.,:-]{0,35}$', 35),
        ('fmst', '<text>         entry form state', '', r'[a-z]{2,3}$', 3),
        ('fmcity', '<text>         entry form city', '', r'[A-Za-z]{2,35}$', 35),
        ('fmzip', '<text>         entry form zip code', '', r'[0-9]{5}$', 6),
        ('fmem', '<text>         entry form email', '', r'[A-Za-z0-9@.:-]{0,35}$', 35),
        ('public', '<text>         public location desc', '', r'[A-Za-z0-9@.: -]{0,35}$', 35),
        ('infob', '0/1            public info booth', '0', r'[0-1]$', 1),
        ('svego', '<name>         govt official visitor name', '', r'[A-Za-z., -]{0,35}$', 35),
        ('svroa', '<name>         agency site visitor name', '', r'[A-Za-z., -]{0,35}$', 35),
        ('youth', '<n>            participating youth', '0', r'[0-9]{1,2}$', 2),
        ('websub', '0/1            web submission bonus', '0', r'[0-1]$', 1),
        ('psgen', '0/1            using generator power', '0', r'[0-1]$', 1),
        ('pscom', '0/1            using commercial power', '0', r'[0-1]$', 1),
        ('psbat', '0/1            using battery power', '0', r'[0-1]$', 1),
        ('psoth', '<text>         desc of other power', '', r'[A-Za-z0-9.: -]{0,35}$', 35),
        ('fdstrt', 'yymmdd.hhmm    FD start time (UTC)', '020108.1800', r'[0-9.]{11}$', 11),
        ('fdend', 'yymmdd.hhmm    FD end time (UTC)', '990629.2100', r'[0-9.]{11}$', 11),
        ('tmast', '<text>         Time Master Node', '', r'[A-Za-z0-9-]{0,8}$', 8)):
    gd.new(name, desc, default, okre, maxlen)


class syncmsg:
    """synchronous message printing"""
    lock = threading.RLock()
    msgs = []

    def prmsg(self, msg):
        """put message in queue for printing"""
        self.lock.acquire()
        self.msgs.append(msg)
        self.lock.release()

    def prout(self):
        """get message from queue for printing"""
        # Check to see if the log window has been deleted           
        self.lock.acquire()
        while self.msgs:
            logw.configure(state=NORMAL)
            logw.see(END)
            nod = self.msgs[0][70:81]  # color local entries  
            seq = self.msgs[0][65:69].strip()
            seq = int(seq)
            stn = self.msgs[0][69:].strip()
            if nod == node:
                # Added a check to see if in the log to print blue or not - Scott Hibbs June 26, 2018
                bid, dummy, dummy = qdb.cleanlog()  # get a clean log
                stnseq = stn +"|"+str(seq)
                if stnseq in bid:
                    logw.insert(END, "%s\n" % self.msgs[0], "b")
                else:
                    logw.insert(END, "%s\n" % self.msgs[0])
            logw.configure(state=DISABLED)
            del self.msgs[0]
        self.lock.release()


# global functions

def now():
    """return current time in standard string format"""
    # n = time.localtime(time.time())
    n = time.gmtime(time.time() + mclock.offset)  # time in gmt utc
    # offset to correct to master
    t = time.strftime("%y%m%d.%H%M%S", n)  # compact version YY
    return t

def tmtofl(a):
    """time to float in seconds, allow milliseconds"""
    # Reworked in 152i
    #    return time.mktime((2000+int(a[0:2]),int(a[2:4]),int(a[4:6]),\
    #                       int(a[7:9]),int(a[9:11]),int(a[11:13]),0,0,0))
    return calendar.timegm((2000 + int(a[0:2]), int(a[2:4]), int(a[4:6]),
                            int(a[7:9]), int(a[9:11]), float(a[11:]), 0, 0, 0))

def tmsub(a, b):
    """time subtract in seconds"""
    return tmtofl(a) - tmtofl(b)


class GlobalDb:
    """new sqlite globals database fdlog.sq3 replacing globals file"""
    def __init__(self):
        self.dbPath = globf[0:-4] + '.sq3'
        print "  Using local value database", self.dbPath
        self.sqdb = sqlite3.connect(self.dbPath, check_same_thread=False)  # connect to the database
        # Have to add FALSE here to get this stable. - Scott Hibbs 7/17/2015
        self.sqdb.row_factory = sqlite3.Row  # row factory
        self.curs = self.sqdb.cursor()  # make a database connection cursor
        sql = "create table if not exists global(nam text,val text,primary key(nam))"
        self.curs.execute(sql)
        self.sqdb.commit()
        self.cache = {}  # use a cache to reduce db i/o

    def get(self, name, default):
        if name in self.cache:
            # print "reading from globCache",name
            return self.cache[name]
        sql = "select * from global where nam == ?"
        results = self.curs.execute(sql, (name,))
        value = default
        for result in results:
            value = result['val']
            # print "reading from globDb", name, value
            self.cache[name] = value
        return value

    def put(self, name, value):
        now = self.get(name, 'zzzzz')
        # print now,str(value),now==str(value)
        if str(value) == now: return  # skip write if same
        sql = "replace into global (nam,val) values (?,?)"
        self.curs.execute(sql, (name, value))
        self.sqdb.commit()
        # print "writing to globDb", name, value
        self.cache[name] = str(value)


def loadglob():
    """load persistent local config to global vars from file"""
    # updated from 152i
    global globDb, node, operator, logger, power, tdwin, debug, authk, timeok
    globDb = GlobalDb()
    node = globDb.get('node', '')
    operator = globDb.get('operator', '')
    logger = globDb.get('logger', '')
    power = globDb.get('power', '0')
    authk = globDb.get('authk', 'tst')
    tdwin = int(globDb.get('tdwin', 5))  # 152i changed from 10 to 5
    debug = int(globDb.get('debug', 0))
    timeok = int(globDb.get('timeok', 0))
    netsync.rem_host = globDb.get('remip', '0.0.0.0')
    if debug: print "  debug:", debug


def saveglob():
    """save persistent local config global vars to file"""
    globDb.put('node', node)
    globDb.put('operator', operator)
    globDb.put('logger', logger)
    globDb.put('power', power)
    globDb.put('authk', authk)
    globDb.put('tdwin', tdwin)
    globDb.put('debug', debug)
    globDb.put('timeok', timeok)
    #    fd = file(globf,"w")
    #    fd.write("|%s|%s|%s|%s|%s|%s|%s|"%(node,operator,logger,power,\
    #                                       authk,tdwin,debug))
    #    fd.close()


# contest log section
def getfile(fn):
    """get file contents"""
    data = ""
    try:
        fd = file(fn, "r")
        data = fd.read()
        fd.close()
    except:
        pass
    if data != "":
        print "Found file", fn
        # print data
    return data


participants = {}


def contestlog(pr):
    """generate contest entry and log forms"""
    w1aw_msg = getfile("w1aw_msg.txt")  # w1aw bulletin copy
    # National Traffic System Messages
    nts_orig_msg = getfile("nts_msg.txt")  # status message
    nts_msg_relay = []
    for i in range(0, 10):  # relayed messages
        fn = "nts_rly%d.txt" % i
        msg = getfile(fn)
        if msg != "":
            nts_msg_relay.append(msg)
    media_copy = getfile("media.txt")  # media activity
    soapbox = getfile("soapbox.txt")  # soapbox commentary
    fd_call = string.upper(gd.getv('fdcall'))  # prep data
    xmttrs = ival(gd.getv('class'))
    gota_call = string.upper(gd.getv('gcall'))
    if xmttrs < 2:
        gota_call = ""
    if pr == 0:
        return  # only define variables return
    # output the entry, adif & cabrillo log file
    datime = now()
    dummy, bycall, gotabycall = qdb.cleanlog()  # get a clean log
    qpb, ppb, qpop, qplg, qpst, dummy, dummy, maxp, cwq, digq, fonq, qpgop, gotaq, nat, sat = \
        qdb.bandrpt()  # and count it
    print "..",
    sys.stdout = file(logfile, "w")  # redirect output to file
    print "Field Day 20%s Entry Form" % datime[:2]
    print
    print "Date Prepared:              %s UTC" % datime[:-2]
    print
    print "1.  Field Day Call:         %s" % fd_call
    if gota_call != "":
        print "    GOTA Station Call:      %s" % gota_call
    print "2.  Club or Group Name:     %s" % gd.getv('grpnam')
    print "3.  Number of Participants: %s" % len(participants)
    print "4.  Transmitter Class:      %s" % xmttrs
    print "5.  Entry Class:            %s" % string.upper(gd.getv('class'))[-1:]
    print
    print "6.  Power Sources Used:"
    if int(gd.getv('psgen')) > 0:
        print "      Generator"
    if int(gd.getv('pscom')) > 0:
        print "      Commercial"
    if int(gd.getv('psbat')) > 0:
        print "      Battery"
    # add solar! xx
    if gd.getv('psoth') != '':
        print "      Other: %s" % (gd.getv('psoth'))
    print
    print "7.  ARRL Section:           %s" % gd.getv('sect')
    print
    print "8.  Total CW QSOs:      %4s  Points: %5s" % (cwq, cwq * 2)
    print "9.  Total Digital QSOs: %4s  Points: %5s" % (digq, digq * 2)
    print "10. Total Phone QSOs:   %4s  Points: %5s" % (fonq, fonq)
    qsop = cwq * 2 + digq * 2 + fonq
    print "11. Total QSO Points:                 %5s" % qsop
    print "12. Max Power Used:     %4s  Watts" % maxp
    powm = 5
    if int(gd.getv('psgen')) > 0 or int(gd.getv('pscom')) > 0: powm = 2
    if maxp > 5:
        powm = 2
    if maxp > 150:
        powm = 1
    if maxp > 1500:
        powm = 0
    print "13. Power Multiplier:                  x %2s" % powm
    qso_scor = qsop * powm
    print "14. Claimed QSO Score:                %5s" % qso_scor
    print
    print "15. Bonus Points:"
    tot_bonus = 0
    emerg_powr_bp = 0
    if gd.getv('pscom') == '0':
        emerg_powr_bp = 100 * xmttrs
        if emerg_powr_bp > 2000:
            emerg_powr_bp = 2000
        tot_bonus += emerg_powr_bp
        print "   %4s 100%s Emergency Power (%s xmttrs)" % (emerg_powr_bp, '%', xmttrs)
    media_pub_bp = 0
    if media_copy > "":
        media_pub_bp = 100
        tot_bonus += media_pub_bp
        print "    %3s Media Publicity (copy below)" % media_pub_bp
    public_bp = 0
    public_place = gd.getv('public')
    if public_place != "":
        public_bp = 100
        tot_bonus += public_bp
        print "    %3s Set-up in a Public Place (%s)" % (public_bp, public_place)
    info_booth_bp = 0
    if int(gd.getv('infob')) > 0 and public_bp > 0:
        info_booth_bp = 100
        tot_bonus += info_booth_bp
        print "    %3s Information Booth (photo included)" % info_booth_bp
    nts_orig_bp = 0
    if nts_orig_msg > "":
        nts_orig_bp = 100
        tot_bonus += nts_orig_bp
        print "    %3s NTS message Originated to ARRL SM/SEC (copy below)" % nts_orig_bp
    n = len(nts_msg_relay)
    nts_msgs_bp = 10 * n
    if nts_msgs_bp > 100:
        nts_msgs_bp = 100
    if nts_msgs_bp > 0:
        tot_bonus += nts_msgs_bp
        print "    %3s Formal NTS messages handled (%s) (copy below)" % (nts_msgs_bp, n)
    sat_qsos = len(sat)
    sat_bp = 0
    if sat_qsos > 0:
        sat_bp = 100
        tot_bonus += sat_bp
        print "    %3s Satellite QSO Completed (%s/1) (list below)" % (sat_bp, sat_qsos)
    natural_q = len(nat)
    natural_bp = 0
    if natural_q >= 5:
        natural_bp = 100
        tot_bonus += natural_bp
        print "    %3s Five Alternate power QSOs completed (%s/5) (list below)" % (natural_bp, natural_q)
    w1aw_msg_bp = 0
    if len(w1aw_msg) > 30:  # ignore short file place holder 152i
        w1aw_msg_bp = 100
        tot_bonus += w1aw_msg_bp
        print "    %3s W1AW FD Message Received (copy below)" % (w1aw_msg_bp)
    site_visited_ego_bp = 0
    if gd.getv('svego') > "":
        site_visited_ego_bp = 100
        tot_bonus += site_visited_ego_bp
        print "    %3s Site Visited by elected govt officials (%s)" % (site_visited_ego_bp, gd.getv('svego'))
    site_visited_roa_bp = 0
    if gd.getv('svroa') > "":
        site_visited_roa_bp = 100
        tot_bonus += site_visited_roa_bp
        print "    %3s Site Visited by representative of agency (%s)" % (site_visited_roa_bp, gd.getv('svroa'))
    gota_max_bp = 0
    if gotaq >= 100:
        gota_max_bp = 100
        tot_bonus += gota_max_bp
        print "    %3s GOTA Station 100 QSOs bonus achieved" % (gota_max_bp)
    youth_bp = 0
    if int(gd.getv('youth')) > 0:
        youth_bp = 20 * int(gd.getv('youth'))
        if youth_bp > 5 * 20:
            youth_bp = 5 * 20
        tot_bonus += youth_bp
        print "    %3s Youth Participation Bonus" % (youth_bp)
    # keep this last
    web_sub_bp = 0
    if gd.getv('websub') == "1":
        web_sub_bp = 50
        tot_bonus += web_sub_bp
        print "    %3s Web Submission Bonus" % (web_sub_bp)
    print
    print "    Total Bonus Points Claimed: %5s" % tot_bonus
    print
    tot_scor = qso_scor + tot_bonus
    print "    Total Claimed Score:        %5s" % tot_scor
    print
    print "16. We have observed all competition rules as well as all regulations"
    print "    for amateur radio in our country. Our report is correct and true"
    print "    to the best of our knowledge. We agree to be bound by the decisions"
    print "    of the ARRL Awards Committee."
    print
    print "Submitted By:"
    print
    print "    Date:     %s UTC" % datime[:-2]
    print "    Call:     %s" % string.upper(gd.getv('fmcall'))
    print "    Name:     %s" % gd.getv('fmname')
    print "    Address:  %s" % gd.getv('fmad1')
    print "    Address:  %s" % gd.getv('fmad2')
    print "    Email:    %s" % gd.getv('fmem')
    print
    print
    print "Field Day Call: %s" % string.upper(fd_call)
    print
    print "17. QSO Breakdown by Band and Mode"
    print
    print "        ----CW----  --Digital-  ---Phone--"
    print "  Band  QSOs   PWR  QSOs   PWR  QSOs   PWR"
    print
    qsobm, pwrbm = {}, {}
    for b in (160, 80, 40, 20, 15, 10, 6, 2, 220, 440, 1200, 'sat', 'gota'):
        if b == 'gota' and gota_call == "":
            continue
        print "%6s" % b,
        for m in 'cdp':
            bm = "%s%s" % (b, m)
            print "%5s %5s" % (qpb.get(bm, 0), ppb.get(bm, 0)),
            qsobm[m] = qsobm.get(m, 0) + qpb.get(bm, 0)
            pwrbm[m] = max(pwrbm.get(m, 0), ppb.get(bm, 0))
        print
    print
    print "Totals",
    print "%5s %5s" % (qsobm['c'], pwrbm['c']),
    print "%5s %5s" % (qsobm['d'], pwrbm['d']),
    print "%5s %5s" % (qsobm['p'], pwrbm['p'])
    print
    print
    if gota_call:
        print "18. Callsigns and QSO counts of GOTA Operators"
        print
        print "      Call  QSOs"
        for i in qpgop.keys():
            print "    %6s   %3s" % (i, qpgop[i])
        print "    %6s   %3s" % ("Total", gotaq)
        print
        print
    print "Dupe Lists sorted by Band, Mode and Call:"
    print
    print "  Main Station(s) Dupe List (%s)" % fd_call
    l = []
    for i in bycall.values():
        l.append("    %4s %s" % (i.band, i.call))
    l.sort()
    b2, n = "", 0
    for i in l:
        b, c = i.split()
        if (b == b2) & (n < 5):  # same band, 5 per line
            print "%-10s" % c,
            n += 1
        else:
            print
            print "    %4s   %-10s" % (b, c),
            b2 = b
            n = 1
    print
    print
    print
    if gota_call > "":
        print "  GOTA Station Dupe List (%s)" % gota_call
        l = []
        for i in gotabycall.values():
            l.append("    %4s %s" % (i.band, i.call))
        l.sort()
        b2, n = "", 0
        for i in l:
            b, c = i.split()
            if (b == b2) & (n < 5):  # same band
                print "%-10s" % c,
                n += 1
            else:
                print
                print "    %4s   %-10s" % (b, c),
                b2 = b
                n = 1
        print
        print
        print
    if w1aw_msg != "":
        print "W1AW FD Message Copy"
        print
        print "%s" % w1aw_msg
        print
        print
    if nts_orig_msg != "":
        print "Originated NTS Message"
        print
        print nts_orig_msg
        print
        print
    if len(nts_msg_relay) > 0:
        print "RELAYED NTS Messages"
        print
        for i in nts_msg_relay:
            print i
            print
        print
    if media_copy != "":
        print "Media Copy"
        print
        print media_copy
        print
        print
    if len(nat) > 0:
        print "Natural Power QSOs (show first 10 logged)"
        print
        l = []
        for i in nat:
            ln = "%8s %5s %-10s %-18s %4s %-6s %-6s %4s %s" % \
                 (i.date[4:11], i.band, i.call, i.rept[:18], i.powr, i.oper, i.logr, i.seq, i.src)
            l.append(ln)
        l.sort()
        j = 0
        for i in l:
            print i
            j += 1
            if j > 9:
                break
        print
        print
    if len(sat) > 0:
        print "Satellite QSOs (show 5)"
        print
        l = []
        for i in sat:
            ln = "%8s %5s %-10s %-18s %4s %-6s %-6s %4s %s" % \
                 (i.date[4:11], i.band, i.call, i.rept[:18], i.powr, i.oper, i.logr, i.seq, i.src)
            l.append(ln)
        l.sort()
        j = 0
        for i in l:
            print i
            j += 1
            if j > 4:
                break
        print
        print
    if soapbox != "":
        print "Soapbox Comments"
        print
        print soapbox
        print
        print
    print "Logging and Reporting Software Used:\n"
    print prog
    print "===================== CLIP HERE ============================"
    print
    print "(do not include below in ARRL submission)"
    print
    print "Submission Notes"
    print """
    email files as attachments to FieldDay@arrl.org within 30 days!!!
    web entry at www.b4h.net/cabforms
        fdlog.log log file, less log detail below 'CLIP HERE'
        proof of bonus points, as needed:
            public info booth picture, visitor list, info
            visiting officials pictures
            media visiting pictures
            natural power pictures
            demo stations pictures
        plus other interesting pictures
    """
    print "Participant List"
    print
    l = []
    for i in participants.values():
        l.append(i)
    l.sort()
    n = 0
    for i in l:
        n += 1
        print "  %4s %s" % (n, i)
    print
    print
    print "QSO breakdown by Station"
    print
    for i in qpst.keys():
        print "  %4s %s" % (qpst[i], i)
    print
    print
    print "QSO breakdown by Operator"
    print
    for i in qpop.keys():
        print "  %4s %s" % (qpop[i], i)
    print
    print
    print "QSO breakdown by Logger"
    print
    for i in qplg.keys():
        print "  %4s %s" % (qplg[i], i)
    print
    print
    print "Worked All States during FD Status"
    print
    r = qdb.wasrpt()
    for i in r:
        print i
    print
    print
    print "Detailed Log"
    print
    print "  Date Range", gd.getv('fdstrt'), "-", gd.getv('fdend'), "UTC"
    print
    qdb.prlog()
    print
    print
    print "ADIF Log"
    print
    qdb.pradif()
    print
    print "VHF Cabrillo"
    print
    qdb.vhf_cabrillo()
    print
    print
    print "Winter Field day"
    print
    qdb.winter_fd()
    print
    print "eof"
    sys.stdout = sys.__stdout__  # revert print to console
    print
    print "entry and log written to file", logfile

# setup for phonetics printout  ## Added by Scott Hibbs KD4SIR to get phonetics on bottom of gui?
# d = {"a":"alpha ","b":"bravo ","c":"charlie ","d":"delta ","e":"echo ", \
#     "f":"foxtrot ","g":"golf ","h":"hotel ","i":"india ","j":"juliett ", \
#     "k":"kilo ","l":"lima ","m":"mike ","n":"november ","o":"oscar ", \
#     "p":"papa ","q":"quebec ","r":"romeo ","s":"sierra ","t":"tango ", \
#     "u":"uniform ","v":"victor ","w":"whiskey ","x":"x-ray ","y":"yankee ", \
#     "z":"zulu ","-":"dash ", "/":"dash ", "0":"Zero ", "1":"One ", "2":"Two ", "3":"Three ", \
#     "4":"Four ", "5":"Five ", "6":"Six ", "7":"Seven ", "8":"Eight ", "9":"Nine "}
# phonetics = "ab9cde" #string.lower(gd.getv('fdcall'))
# let:char = d
# phocall = ""
# for char in phonetics:
#    if char in d:
#        phocall = phocall.join(char)

# band set buttons
# this can be customized -Only here customizing this in program will break from compatibility with
# original fdlog.py -Scott Hibbs Oct/13/2013
bands = ('160', '80', '40', '20', '15', '10', '6', '2', '220', '440', '900', '1200', 'sat', 'off')
modes = ('c', 'd', 'p')
bandb = {}  # band button handles


def bandset(b):
    global band, tmob
    if node == "":
        b = 'off'
        txtbillb.insert(END, "err - no node\n")
    if operator == "":
        b = 'off'
        txtbillb.insert(END, "err - no Operator\n")
    if b != 'off':
        s = net.si.nod_on_band(b)
        if s: txtbillb.insert(END, " Already on [%s]: %s\n" % (b, s))
    txtbillb.see(END)
    if band != b: tmob = now()  # reset time on band
    band = b
    bandb[b].select()
    renew_title()

def bandoff():
    """ To set the band to off"""
    bandset('off')


# new participant setup
class NewParticipantDialog():
    """ this is the new participant window that pops up"""

    def dialog(self):
        if node == "":
            txtbillb.insert(END, "err - no node\n")
            return
        s = NewParticipantDialog()
        s.t = Toplevel(root)
        s.t.transient(root)
        s.t.title('SCICSG_FDLOG Add New Participant')
        fr1 = Frame(s.t)
        fr1.grid(row=0, column=0)
        Label(fr1, text='Initials   ', font=fdbfont).grid(row=0, column=0, sticky=W)
        s.initials = Entry(fr1, width=3, font=fdbfont, validate='focusout', validatecommand=s.lookup)
        s.initials.grid(row=0, column=1, sticky=W)
        s.initials.focus()
        Label(fr1, text='Name', font=fdbfont).grid(row=1, column=0, sticky=W)
        s.name = Entry(fr1, width=20, font=fdbfont)
        s.name.grid(row=1, column=1, sticky=W)
        Label(fr1, text='Call', font=fdbfont).grid(row=2, column=0, sticky=W)
        s.call = Entry(fr1, width=6, font=fdbfont)
        s.call.grid(row=2, column=1, sticky=W)
        Label(fr1, text='Age', font=fdbfont).grid(row=3, column=0, sticky=W)
        s.age = Entry(fr1, width=2, font=fdbfont)
        s.age.grid(row=3, column=1, sticky=W)
        Label(fr1, text='Vstr Title', font=fdbfont).grid(row=4, column=0, sticky=W)
        s.vist = Entry(fr1, width=20, font=fdbfont)
        s.vist.grid(row=4, column=1, sticky=W)
        fr2 = Frame(s.t)
        fr2.grid(row=1, column=0, sticky=EW, pady=3)
        fr2.grid_columnconfigure((0, 1), weight=1)
        Label(fr2, text='Save=<Enter>', font=fdbfont).grid(row=3, column=0, sticky=W)
        #Button(fr2, text='Save', font=fdbfont, command=s.applybtn) .grid(row=3, column=1, sticky=EW, padx=3)
        Button(fr2, text='Close', font=fdbfont, command=s.quitbtn) .grid(row=3, column=2, sticky=EW, padx=3)
        # Bound enter key to save entries - Scott Hibbs KD4SIR Mar/30/2017
        s.t.bind('<Return>', lambda event: s.applybtn)

    def lookup(self):
        # constrain focus to initials until they are ok
        initials = string.lower(self.initials.get())
        if not re.match(r'[a-zA-Z]{2,3}$', initials):
            # self.initials.delete(0,END)
            self.initials.configure(bg='gold')
            self.initials.focus()
        else:
            self.initials.configure(bg='white')
            dummy, name, call, age, vist = string.split(participants.get(initials, ', , , , '), ', ')
            self.name.delete(0, END)
            self.name.insert(END, name)
            self.call.delete(0, END)
            self.call.insert(END, call)
            self.age.delete(0, END)
            if age == 0:
                pass
            else:
                self.age.insert(END, age)
            self.vist.delete(0, END)
            if vist == "":
                pass
            else:
                self.vist.insert(END, vist)
        return 1
    
    @property   #This added so I can use the <Return> binding -Scott Hibbs KD4SIR Mar/30/2017
    def applybtn(self):
        global participants
        # print "store"
        initials = self.initials.get().lower()
        name = self.name.get()
        call = string.lower(self.call.get())
        age = string.lower(self.age.get())
        vist = string.lower(self.vist.get())
        self.initials.configure(bg='white')
        self.name.configure(bg='white')
        self.call.configure(bg='white')
        self.age.configure(bg='white')
        self.vist.configure(bg='white')
        if not re.match(r'[a-zA-Z]{2,3}$', initials):
            txtbillb.insert(END, "error in initials\n")
            txtbillb.see(END)
            topper()
            self.initials.focus()
            self.initials.configure(bg='gold')
        elif not re.match(r'[A-Za-z ]{4,20}$', name):
            txtbillb.insert(END, "error in name\n")
            txtbillb.see(END)
            topper()
            self.name.focus()
            self.name.configure(bg='gold')
        elif not re.match(r'([a-zA-Z0-9]{3,6})?$', call):
            txtbillb.insert(END, "error in call\n")
            txtbillb.see(END)
            topper()
            self.call.focus()
            self.call.configure(bg='gold')
        elif not re.match(r'([0-9]{1,2})?$', age):
            txtbillb.insert(END, "error in age\n")
            txtbillb.see(END)
            topper()
            self.age.focus()
            self.age.configure(bg='gold')
        elif not re.match(r'([a-zA-Z0-9]{4,20})?$', vist):
            txtbillb.insert(END, "error in title\n")
            txtbillb.see(END)
            topper()
            self.vist.focus()
            self.vist.configure(bg='gold')
        else:
            # Enter the Participant in the dictionary
            initials
            nam = "p:%s" % initials
            v = "%s, %s, %s, %s, %s" % (initials, name, call, age, vist)
            participants[initials] = v
            dummy = qdb.globalshare(nam, v)  # store + bcast
            txtbillb.insert(END, "\a New Participant Entered.")
            print "\a"
            txtbillb.see(END)
            topper()
            self.initials.delete(0, END)
            self.name.delete(0, END)
            self.call.delete(0, END)
            self.age.delete(0, END)
            self.vist.delete(0, END)
            self.initials.focus()
            buildmenus()

    def quitbtn(self):
        self.t.destroy()


newpart = NewParticipantDialog()
# property dialogs


cf = {}


def renew_title():
    """renew title and various, called at 10 second rate"""
    if node == 'gotanode':
        call = string.upper(gd.getv('gcall'))
    else:
        call = string.upper(gd.getv('fdcall'))
    clas = string.upper(gd.getv('class'))
    sec = gd.getv('sect')
    t = now()
    sob = tmsub(t, tmob)
    mob = sob / 60
    h = mob / 60
    m = mob % 60
    # Added port to the heading - Scott Hibbs KD4SIR Jan/27/2017
    root.title('  FDLOG_SCICSG %s %s %s (Node: %s Time on Band: %d:%02d) %s:%s UTC %s/%s Port:%s' % \
               (call, clas, sec, node, h, m, t[-6:-4], t[-4:-2], t[2:4], t[4:6], port_base))
    net.bcast_now()  # this is periodic bcast...

def setnode(new):
    global node
    bandoff()
    node = string.lower(new)
    qdb.redup()
    renew_title()
    lblnode.configure(text="My Node: %s" % node, font=fdfont, foreground='royalblue', background='lightgrey')
    # Had to add the above so that the new lblnode could be updated. - Scott Hibbs KD4SIR Mar/28/2017

def applyprop(e=''):
    """apply property"""
    global operator, logger, power, node
    new = cf['e'].get()
    if re.match(cf['vre'], new):
        #        if   cf['lab'] == 'Operator': operator = new
        #        elif cf['lab'] == 'Logger':   logger = new
        #        elif cf['lab'] == 'Power':    power = new
        if cf['lab'] == 'Node':
            setnode(new)
        #        elif cf['lab'] == 'AuthKey':  reauth(new)    #net.setauth(new)
        else:
            print 'error, no such var'
        saveglob()
        renew_title()
        cf['p'].destroy()
    else:
        print 'bad syntax', new

def pdiag(label, value, valid_re, wid):
    "property dialog box"
    cf['p'] = Toplevel(root)
    cf['p'].transient(root)
    Label(cf['p'], text=label, font=fdbfont).grid(sticky=E, pady=20)
    if label == 'AuthKey':
        cf['e'] = Entry(cf['p'], width=wid, font=fdbfont, show='*')
    else:
        cf['e'] = Entry(cf['p'], width=wid, font=fdbfont)
    cf['e'].grid(row=0, column=1, sticky=W)
    cf['e'].insert(END, value)
    Button(cf['p'], text="Apply", command=applyprop, font=fdbfont) \
        .grid(sticky=W, padx=20)
    Button(cf['p'], text="Cancel", command=cf['p'].destroy, font=fdbfont) \
        .grid(padx=20, pady=20, row=1, column=1, sticky=E)
    cf['vre'] = valid_re
    cf['lab'] = label
    cf['e'].bind('<Return>', applyprop)
    cf['p'].bind('<Escape>', lambda e: (cf['p'].destroy()))
    cf['e'].focus()

def noddiag():
    pdiag('Node', node, r'[A-Za-z0-9-]{1,8}$', 8)
    #def authdiag():
    #    pdiag('AuthKey',authk,r'.{3,12}$',12)


# view textdocs

def viewprep(ttl=''):
    "view preparation core code"
    w = Toplevel(root)
    ##    w.transient(root)
    w.title("FDLOG_SCICSG - %s" % ttl)
    t = Text(w, takefocus=0, height=20, width=85, font=fdfont, \
             wrap=NONE, setgrid=1)
    s = Scrollbar(w, command=t.yview)
    t.configure(yscrollcommand=s.set)
    t.grid(row=0, column=0, sticky=NSEW)
    s.grid(row=0, column=1, sticky=NS)
    w.grid_rowconfigure(0, weight=1)
    w.grid_columnconfigure(0, weight=1)
    t.bind('<KeyPress>', kevent)
    return t


def viewtextv(txt, ttl=''):
    "view text variable"
    w = viewprep(ttl)
    w.insert(END, txt)
    w.configure(state=DISABLED)


def viewtextl(l, ttl=''):
    "view text list"
    w = viewprep(ttl)
    for i in l:
        w.insert(END, "%s\n" % i)
    w.configure(state=DISABLED)


def viewtextf(fn, ttl=''):
    "view text file"
    if ttl == "": ttl = "file %s" % fn
    try:
        fd = file(fn, 'r')
        l = fd.read()
        viewtextv(l, ttl)
        fd.close()
    except:
        viewtextv("read error on file %s" % fn)


def viewlogf(bandm):
    "view log filtered by bandmode"
    lg = qdb.filterlog2(bandm)
    viewtextl(lg, "Log Filtered for %s" % bandm)


def viewlogfs(nod):
    "view log filtered by node"
    lg = qdb.filterlogst(nod)
    viewtextl(lg, "Log Filtered for %s" % nod)

def viewwasrpt():
    r = qdb.wasrpt()
    viewtextl(r, "Worked All States Report")


def updatebb():
    """update band buttons"""
    # Added Who's on the bands functionality with a mouse over event - KD4SIR Scott A Hibbs Oct/13/2013
    # Tried and tried to get wof to return only one result for the mouse over. If you can, you're awesome! -Scott
    global wof
    r, cl, vh, go = net.si.nod_on_bands()
    anytext = "VHF "


    def whosonfirst(event):
        # Cleaned up whos on band (with section of .ba report) - KD4SIR Scott Hibbs Mar/23/2017 
        d = {}
        txtbillb.insert(END,"\n--node-- band opr lgr pwr  ----- last\n")
        for t in net.si.nodinfo.values():
            dummy, dummy, age = d.get(t.nod, ('', '', 9999))
            if age > t.age: d[t.nod] = (t.bnd, t.msc, t.age)
        for t in d:
            txtbillb.insert(END,"%8s %4s %-18s %4s\n" % (t, d[t][0], d[t][1], d[t][2]))  # t.bnd,t.msc,t.age)
        topper()
        txtbillb.see(END)



    def whosonsecond(event):
        global wof
        wof = ""
		#tkMessageBox.destroy

    for i in bands:
        dummy = 0
        for j in modes:
            bm = "%s%s" % (i, j)
            if i == 'off':
                continue
            bc = 'lightgray'
            sc = 'white'
            n = len(r.get(bm, ''))
            bandb[bm].bind("<Enter>", lambda e: None)
            bandb[bm].bind("<Leave>", lambda e: None)
            if n == 0:
                bc = 'lightgrey'
                bandb[bm].bind("<Enter>", lambda e: None)
                bandb[bm].bind("<Leave>", lambda e: None)
            elif n == 1:
                bc = 'gold'
                bandb[bm].bind("<Enter>", whosonfirst)
                bandb[bm].bind("<Leave>", whosonsecond)
            else:
                bc = 'darkorange'; sc = 'red'
                bandb[bm].bind("<Enter>", whosonfirst)
                bandb[bm].bind("<Leave>", whosonsecond)
            bandb[bm].configure(background=bc, selectcolor=sc)

    cltg = ival(gd.getv('class'))  # class target
    if cltg > 1:
        vhfree = 1  # handle free vhf xmttr
        ts = cl - vhfree
        if vh == 0:
            ts = cl
        else:
            ts = cl - vhfree
        if ts <= -1:
            ts = 0
    else:
        vhfree = 0
        ts = cl
    #ts = cl + max(0, vh-vhfree)  # total sta = class + excess vhf stations
    # Fixed VHF to reflect a free transmitter and warn if two vhf rigs are used. - Scott Hibbs KD4SIR 5/14/2014
    clc = 'gold'
    if ts == cltg:
        clc = 'palegreen'
    if ts > cltg:
        clc = 'pink2'
    bandb['Class'].configure(text='Class %s/%s' % (ts, cltg), background=clc)

    vhc = 'gold'
    if vh - vhfree == 0:
        vhc = 'palegreen'  # for 1D Class correction KD4SIR
        anytext = "VHF "
    if vh < 0:
        vhc = 'pink2'
        anytext = "VHF "
    if vh > vhfree:
        vhc = 'darkorange'  # 2 vhf is okay, only 1 is free...
        anytext = "VHF taking HF "
    bandb['VHF'].configure(text='%s%s/%s' % (anytext, vh, vhfree), background=vhc)

    if cltg > 1:
        gotatg = 1
    else:
        gotatg = 0
    goc = 'gold'
    if go == gotatg: goc = 'palegreen'
    if go > gotatg: goc = 'pink2'
    bandb['GOTA'].configure(text='GOTA %s/%s' % (go, gotatg), background=goc)

def updateqct():
    "update contact count"
    #function reworked in time for field day 2014. - Scott Hibbs KD4SIR
    dummy, dummy, qpop, qplg, dummy, dummy, dummy, dummy, cwq, digq, fonq, dummy, gotaq, dummy, dummy = \
        qdb.bandrpt()  # xx reduce processing here
    for i, j in (('FonQ', 'Phone %5s' % fonq),
                 ('CW/D', 'CW&Dig %4s' % (cwq + digq)),
                 ('GOTAq', 'GOTA %6s' % gotaq)):
        bandb[i].configure(text=j, background='lightgrey')
        # Update for the operator OpQ - KD4SIR for fd 2014
        if operator == "":
            coin2 = "Operator"
            opmb.config(text=coin2, background='pink2')
            opds.config(text="<Select Operator>", background='pink2')
        else:
            coin = exin(operator)
            if coin in qpop:
                coin2 = qpop['%s' % coin]
                opmb.config(text='ConQ %2s' % coin2, background='lightgrey')
                opds.config(text=operator, background='lightgrey')
            else:
                coin2 = "0"
                opmb.config(text='ConQ %2s' % coin2, background='lightgrey')
                opds.config(text=operator, background='lightgrey')
        # Update for the logger LoQ - KD4SIR for fd 2014
        if logger == "":
            coil2 = "Logger"
            logmb.config(text=coil2, background='pink2')
            logds.config(text="<Select Logger>", background='pink2')
        else:
            coil = exin(logger)
            if coil in qplg:
                coil2 = qplg['%s' % coil]
                logmb.config(text='LogQ %2s' % coil2, background='lightgrey')
                logds.config(text=logger, background='lightgrey')
            else:
                coil2 = "0"
                logmb.config(text='LogQ %2s' % coil2, background='lightgrey')
                logds.config(text=logger, background='lightgrey')
    t = ""  # check for net config trouble
    if net.fills: t = "NEED FILL"
    if net.badauth_rcvd:
        net.badauth_rcvd = 0
        t = "AUTH FAIL"
    if net.pkts_rcvd:
        net.pkts_rcvd = 0
    else:
        t = "Alone? Not receiving data from others."
    if net.send_errs:
        t = "SEND FAIL - Not sending data to others."; net.send_errs = 0
    if authk == '':
        t = "NO AUTHKEY SELECTED"
    if node == '':
        t = "NO NODE SELECTED"
    if t:
        lblnet.configure(text=t, background='gold')
    else:
        lblnet.configure(text="Network OK", background='lightgrey')

def BandButtons(w):
    "create band buttons"
    global sv
    a = 0
    sv = StringVar()
    sv.set(band)
    mac = os.name == 'posix'  # detect the mac added 152i
    for i in bands:
        b = 0
        for j in modes:
            bm = "%s%s" % (i, j)
            if i == 'off':
                bm = 'off'
                # indicatoron = 0 makes square button with text inside but doesn't work well on mac, with value 1 it makes a
                # circle alongside the text and works on both so detect mac and change it for mac only
                bandb[bm] = Radiobutton(master=w, text=bm, font=fdfont, background='lightgrey', indicatoron=mac, \
                                        variable=sv, value=bm, selectcolor='pink2',
                                        command=lambda b=bm: (bandset(b)))
            else:
                bandb[bm] = Radiobutton(master=w, text=bm, font=fdfont, background='pink2', indicatoron=mac, \
                                        variable=sv, value=bm, selectcolor='white',
                                        command=lambda b=bm: (bandset(b)))
            bandb[bm].grid(row=b, column=a, sticky=NSEW)
            b += 1
        a += 1
    for i, j, dummy in (('Class', 0, 5),
                     ('VHF', 1, 13),
                     ('GOTA', 2, 9)):
        bandb[i] = Button(w, text=i, font=fdfont)
        bandb[i].grid(row=j, column=a, sticky=NSEW)
    w.grid_columnconfigure(a, weight=1)
    a += 1
    for i, j in (('FonQ', 0),
                 ('CW/D', 1),
                 ('GOTAq', 2)):
        bandb[i] = Button(w, text=i, font=fdfont)
        bandb[i].grid(row=j, column=a, sticky=NSEW)
    w.grid_columnconfigure(a, weight=1)


def rndlet():
    return chr(random.randrange(ord('a'), ord('z') + 1))


def rnddig():
    return chr(random.randrange(ord('0'), ord('9') + 1))


def testqgen(n):
    # Scott A Hibbs KD4SIR 07/25/2013
    # added if authk protection so that .testqgen only operates with a 'tst' database.
    # no funny business with the contest log
    if authk == "tst":
        while n:
            call = rndlet() + rndlet() + rnddig() + rndlet() + rndlet() + rndlet()
            rpt = rnddig() + rndlet() + ' ' + rndlet() + rndlet() + ' testQ'
            print call, rpt
            n -= 1
            qdb.qsl(now(), call, band, rpt)
            time.sleep(0.1)
    else:
        txtbillb.insert(END, "This command only available while testing with tst.")


# global section, main program
# setup persistent globals before GUI

suffix = ""
call = ""
band = "off"
power = "0"
operator = ""
logger = ""
age = 0
vist = ""
node = ""
authk = ""
port_base = 7373
tmob = now()  # time started on band in min
tdwin = 10  # time diff window on displaying node clock diffs
showbc = 0  # show broadcasts
debug = 0
logdbf = "fdlog.fdd"  # persistent file copy of log database
logfile = "fdlog.log"  # printable log file (contest entry)
globf = "fdlog.dat"  # persistent global file
kbuf = ""  # keyboard line buffer
goBack = "" # needed to print the last line entered with up arrow - Scott Hibbs KD4SIR Jul/05/2018
loadglob()  # load persistent globals from file
print
if node == "":
    # Revised 4/19/2014 for 8 characters so the log lines up nicely. - Scott Hibbs KD4SIR
    print "  Enter the station name"
    print "  Please be 7 characters! (I will add letters to be unique)"
    print "  (Use 'gota' for get on the air station)"
    #    print "  (Previous Node ID: '%s')"%node
    print "  (7 characters}"
    k = string.lower(string.strip(sys.stdin.readline())[:8])
    if len(k) == 8:
        print "That's to many.. (Marc? is that you?)" # Thanks to Marc Fountain K9MAF for the correction. Mar/23/2017
        k = k[:7]
    z = len(k)
    if k != 'gota':
        while z != 7:
            if k == 'gota':
                print "please restart the program."
                sys.exit()
            else:              
                if z < 4:
                    print "um yeah.. 7 characters....    (restart if your gota)"
                    k = string.lower(string.strip(sys.stdin.readline())[:8])
                    z = len(k)
                else:
                    for z in range(z, 7):
                        print "close enough (Ken? is that you?)"
                        k = k + random.choice('abcdefghijklmnopqrstuvwxyz')
                        print k
                        z = len(k)
                        ## 1. if there is more than four characters
                        ## 2. add the rest with randoms
                    
        else:
            print "Thank You!!"
            node = k + random.choice('abcdefghijklmnopqrstuvwxyz')
            print
    else:
        print "Thank You for being gota!!"
        node = 'gotanode'
        print
print "Using Node ID: '%s' " % node
print
# get auth key  auth xxxpppzzz..  fdlogxxx.fdd  port ppp   hashkey (all)
# allow user to select new one, or re-use previous
print "Enter Authentication Key (Return to re-use previous '%s')" % authk
print "  (use 'tst' for testing, two digit year for contest):"
k = string.strip(sys.stdin.readline())
if k != "":
    print "New Key entered, Operator and Logger cleared"
    authk = k
    operator = ""
    logger = ""
    print
print "Using Authentication Key: '%s'" % authk
print "Using", authk[0:3], "for setting port, file"
port_offset = ival(authk[3:6]) * 7
if port_offset == 0: port_offset = ival(authk[0:3]) * 7
# for each char in port_offset:  xxx
# port_offset = ((port_offset << 3) + (char & 15)) & 0x0fff
port_base += port_offset
print "Using Network Port:", port_base
logdbf = "fdlog%s.fdd" % (authk[0:3])
print "Writing Log Journal file:", logdbf
print "Starting Network"
net = netsync()  # setup net
net.setport(port_base)
net.setauth(authk)
print "Saving Persistent Configuration in", globf
saveglob()
print "Time Difference Window (tdwin):", tdwin, "seconds"
print "Starting GUI setup"
root = Tk()  # setup Tk GUI
# root.withdraw()  # This was removed in the last beta without explaination - sah 7/3/2015
menu = Menu(root)
root.config(menu=menu)
filemenu = Menu(menu, tearoff=0)
menu.add_cascade(label="File", menu=filemenu)
filemenu.add_command(label="Save Entry File", command=lambda: contestlog(1))
filemenu.add_command(label="PreView Saved Entry File",
                     command=lambda: viewtextf('fdlog.log'))
filemenu.add_command(label="View Log Data File",
                     command=lambda: viewtextf(logdbf))
filemenu.add_command(label="Exit", command=root.quit)
propmenu = Menu(menu, tearoff=0)
menu.add_cascade(label="Properties", menu=propmenu)
propmenu.add_command(label="Set Node ID", command=noddiag)
propmenu.add_command(label="Add Participants", command=newpart.dialog)
logmenu = Menu(menu, tearoff=0)
menu.add_cascade(label="Logs", menu=logmenu)
logmenu.add_command(label='Full Log', command=lambda: viewlogf(""))
logmenu.add_command(label='QSTs', command=lambda: viewlogf(r"[*]QST"))
logmenu.add_command(label='GOTA', command=lambda: viewlogfs("gota"))
logmenu.add_command(label='WAS', command=viewwasrpt)
for j in modes:
    m = Menu(logmenu, tearoff=0)
    if j == 'c':
        lab = 'CW'
    elif j == 'd':
        lab = 'Digital'
    elif j == 'p':
        lab = 'Phone'
    logmenu.add_cascade(label=lab, menu=m)
    for i in bands:
        if i == 'off': continue
        bm = "%s%s" % (i, j)
        m.add_command(label=bm, command=lambda x=bm: (viewlogf(x)))
#  Added Resources Menu Item to clean up the menu. - Apr/16/2014 Scott Hibbs
resourcemenu = Menu(menu, tearoff=0)
menu.add_cascade(label="Resources", menu=resourcemenu)
# Changed this from fdrules to just Rules to get away from fd name in file folder - Scott Hibbs KD4SIR Mar/28/2017
resourcemenu.add_command(label="ARRL FD Rules (pdf)", command=lambda: os.startfile('Rules.pdf'))
# Changed this to a .dat file to remove the duplicate txt file - Scott Hibbs KD4SIR Mar/28/2017
resourcemenu.add_command(label="ARRL Sections", command=lambda: viewtextf('Arrl_sect.dat', 'ARRL Sections'))
resourcemenu.add_command(label="ARRL Band Chart (pdf)", command=lambda: os.startfile('Bands.pdf'))
resourcemenu.add_command(label="ARRL Band Plan", command=lambda: viewtextf('ARRL_Band_Plans.txt', "ARRL Band Plan"))
# This is not needed with the band chart giving the same info - Scott Hibbs KD4SIR Mar/28/2017 
#resourcemenu.add_command(label="FD Frequency List", command=lambda: viewtextf('frequencies.txt', "FD Frequency List"))
# Removed the propagation report. We don't use it. - Mar/29/2017 Scott Hibbs KD4SIR 
#resourcemenu.add_command(label="Propagation Info", command=lambda: viewtextf('propagation.txt', "Propagation Info"))
# Created a W1AW menu - Scott Hibbs KD4SIR Mar/28/2017
W1AWmenu = Menu(menu, tearoff=0)
menu.add_cascade(label="W1AW", menu=W1AWmenu)
W1AWmenu.add_command(label="W1AW Schedule", command=lambda: viewtextf('w1aw.txt', 'W1AW Schedule'))
W1AWmenu.add_command(label="NTS Message", command=lambda: os.startfile('NTS_eg.txt'))


# Time Conversion Chart

tzchart = """
 UTC       PDT  CDT  EDT
 GMT  PST  CST  EST
"""
for g in range(0, 2400, 100):
    p = g - 800
    if (p < 0): p += 2400
    c = p + 100
    if (c < 0): c += 2400
    e = c + 100
    if (e < 0): e += 2400
    x = e + 100
    if (x < 0): x += 2400
    tzchart += "%04d %04d %04d %04d %04d\n" % (g, p, c, e, x)
resourcemenu.add_command(label="Time Conversion Chart", command=lambda: viewtextv(tzchart, "Time Conversion Chart"))
helpmenu = Menu(menu, tearoff=0)
menu.add_cascade(label="Help", menu=helpmenu)
# Basically reworked the whole menu section. - Scott A Hibbs KD4SIR 7/25/13
# Removed duplicate help sources and files. Rewrote documentation - Scott Hibbs Mar/31/2017
# Renamed fdlogman to Manual to give distance from name of program - Scott Hibbs KD4SIR Mar/29/2017
# Removed "getting started" from code to external text file. - Scott A Hibbs KD4SIR 7/25/13
# Removed Wireless Network as it is not needed - Scott Hibbs KD4SIR Mar/29/2017
helpmenu.add_command(label="Quick Help", command=lambda: viewtextf('Keyhelp.txt'))
helpmenu.add_command(label="Set Commands", command=gd.sethelp)
helpmenu.add_command(label="The Manual", command=lambda: viewtextf('Manual.txt', "Manual"))
helpmenu.add_command(label="Release Log", command=lambda: viewtextf('Releaselog.txt'))
helpmenu.add_command(label="GitHub ReadMe", command=lambda: viewtextf('readme.txt'))
helpmenu.add_command(label="About SCICSG_FDLOG", command=lambda: viewtextv(about, "About"))

# Band Buttons
f1 = Frame(root, bd=1)
BandButtons(f1)
f1.grid(row=0, columnspan=2, sticky=NSEW)


def testcmd(name, rex, value):
    """set global from command, return value and change status"""
    global kbuf
    value = default  # added in 152i
    s = "%s +(%s)$" % (name, rex)
    m = re.match(s, kbuf)
    if m:
        value = m.group(1)
        txtbillb.insert(END, "\n%s set to %s\n" % (name, value))
        kbuf = ""
    return value, default != value

def setoper(op):
    "set operator"
    global operator
    # print "setoper",op
    ini, name, call, age, vist = string.split(op, ', ')
    operator = "%s: %s, %s, %s, %s" % (ini, name, call, age, vist)
    # Adding red to the display - KD4SIR
    ocolor = 'lightgrey'
    opds.config(text=operator, background=ocolor)
    opmb.config(background='gold')
    saveglob()


def setlog(logr):
    """set logger"""
    global logger
    # print "setlog",logr
    ini, name, call, age, vist = string.split(logr, ', ')
    logger = "%s: %s, %s, %s, %s" % (ini, name, call, age, vist)
    lcolor = 'lightgrey'
    logds.config(text=logger, background=lcolor)
    logmb.config(background='gold')
    saveglob()


f1b = Frame(root, bd=0)  # oper logger power and network windows
#  Changed the color of the user buttons to red until assigned - KD4SIR Scott Hibbs 7/14/2013
ocolor = 'pink2'
lcolor = 'pink2'
pcolor = 'pink2'
# Add "who" button to display messagebox with operators on band when clicked.
# Determined that this is not needed now that the mouse over report is cleaner.
#opwho = Menubutton(f1b, text='WHO ', font=fdfont, relief='raised',
#                   background='lightgrey', foreground='royalblue')
#opwho.grid(row=0, column=0, sticky=NSEW)

# Operator
opmb = Menubutton(f1b,text='Operator',font=fdfont,relief='raised', background=ocolor)
opmb.grid(row=0,column=1,sticky=NSEW)
opmu = Menu(opmb,tearoff=0)
opmb.config(menu=opmu,direction='below')
opmu.add_command(label="Add New Operator",command=newpart.dialog)
opds = Menubutton(f1b, text='<select Operator>',font=fdfont,relief='raised',background=ocolor)
opds.grid(row=0,column=0,sticky=NSEW)
opdsu = Menu(opds,tearoff=0)
opds.config(menu=opdsu,direction='below')
f1b.grid_columnconfigure(0,weight=1)
# Logger
logmb = Menubutton(f1b,text="Logger",font=fdfont,relief='raised',background=lcolor)
logmb.grid(row=0,column=4,sticky=NSEW)
logmu = Menu(logmb,tearoff=0)
logmb.config(menu=logmu,direction='below')
logmu.add_command(label="Add New Logger",command=newpart.dialog)
logds = Menubutton(f1b,text='<Select Logger>',font=fdfont,relief='raised',background=lcolor)
logds.grid(row=0,column=3,sticky=NSEW)
f1b.grid_columnconfigure(3,weight=1)
logdsu = Menu(logds,tearoff=0)
logds.config(menu=logdsu,direction='below')
logdsu.add_command(label="Add New Logger",command=newpart.dialog)

def buildmenus():
    opdsu.delete(0, END)
    logdsu.delete(0, END)
    l = participants.values()
    l.sort()
    for i in l:
        # I had to take out the $ which looks for the end of value - Scott Hibbs KD4SIR 2/12/2017
        # Decided non-hams can be in operator field but will check for license before logging - Scott Hibbs KD4SIR Mar/29/2017
        # m = re.match(r'[a-z0-9]+, [a-zA-Z ]+, ([a-z0-9]+)',i)
        #if m: opdsu.add_command(label=i, command=lambda n=i: (setoper(n)))
        opdsu.add_command(label=i, command=lambda n=i: (setoper(n)))
        logdsu.add_command(label=i, command=lambda n=i: (setlog(n)))
    opdsu.add_command(label="Add New Operator", command=newpart.dialog)
    logdsu.add_command(label="Add New Logger", command=newpart.dialog)


# power
def ckpowr():
    global power
    pwr = ival(pwrnt.get())
    if pwr < 0:
        pwr = "0"
    elif pwr > 1500:
        pwr = "1500"
    pwrnt.delete(0, END)
    pwrnt.insert(END, pwr)
    if natv.get():
        pwr = "%sn" % pwr
    else:
        pwr = "%s" % pwr
    power = pwr
    if power == "0":
        pcolor = 'pink2'
        pwrmb.config(background=pcolor)
        pwrnt.config(background=pcolor)
        powcb.config(background=pcolor)
        powlbl.config(background=pcolor)
    else:
        pcolor = 'lightgray'
        pwrmb.config(background=pcolor)
        pwrnt.config(background=pcolor)
        powcb.config(background=pcolor)
        powlbl.config(background=pcolor)
    if power == "0n":
        pcolor = 'pink2'
        pwrmb.config(background=pcolor)
        pwrnt.config(background=pcolor)
        powcb.config(background=pcolor)
        powlbl.config(background=pcolor)
    else:
        pcolor == 'lightgray'
        pwrmb.config(background=pcolor)
        pwrnt.config(background=pcolor)
        powcb.config(background=pcolor)
        powlbl.config(background=pcolor)
    print 'power', power
    return 1


def setpwr(p):
    global power
    pwr = ival(p)
    pwrnt.delete(0, END)
    pwrnt.insert(END, pwr)
    if p[-1:] == 'n':
        powcb.select()
    else:
        powcb.deselect()
    power = p
    if power == "0":
        pcolor = 'pink2'
        pwrmb.config(background=pcolor)
        pwrnt.config(background=pcolor)
        powcb.config(background=pcolor)
        powlbl.config(background=pcolor)
    else:
        pcolor = 'lightgray'
        pwrmb.config(background=pcolor)
        pwrnt.config(background=pcolor)
        powcb.config(background=pcolor)
        powlbl.config(background=pcolor)
    if power == "0n":
        pcolor = 'pink2'
        pwrmb.config(background=pcolor)
        pwrnt.config(background=pcolor)
        powcb.config(background=pcolor)
        powlbl.config(background=pcolor)
    else:
        pcolor == 'lightgray'
        pwrmb.config(background=pcolor)
        pwrnt.config(background=pcolor)
        powcb.config(background=pcolor)
        powlbl.config(background=pcolor)

        
pwrmb = Menubutton(f1b, text="Power", font=fdfont, relief='raised',
                   background=pcolor)
pwrmb.grid(row=0, column=6, sticky=NSEW)
pwrmu = Menu(pwrmb, tearoff=0)
pwrmb.config(menu=pwrmu, direction='below')
# rearranged this menu - Scott Hibbs Mar/23/2017
pwrmu.add_command(label='     0 Watts', command=lambda: (setpwr('0')))
pwrmu.add_command(label='     5 Watts', command=lambda: (setpwr('5')))
pwrmu.add_command(label='    50 Watts', command=lambda: (setpwr('50')))
pwrmu.add_command(label='  100 Watts', command=lambda: (setpwr('100')))
pwrmu.add_command(label='  150 Watts', command=lambda: (setpwr('150')))
pwrmu.add_command(label='  200 Watts', command=lambda: (setpwr('200')))
pwrmu.add_command(label='  500 Watts', command=lambda: (setpwr('500')))
pwrmu.add_command(label='1000 Watts', command=lambda: (setpwr('1000')))
pwrmu.add_command(label='1500 Watts', command=lambda: (setpwr('1500')))
pwrmu.add_command(label='     5W Natural', command=lambda: (setpwr('5n')))
pwrmu.add_command(label='   50W Natural', command=lambda: (setpwr('50n')))
pwrmu.add_command(label=' 100W Natural', command=lambda: (setpwr('100n')))
pwrmu.add_command(label=' 150W Natural', command=lambda: (setpwr('150n')))
pwrnt = Entry(f1b, width=4, font=fdfont, background=pcolor, validate='focusout', validatecommand=ckpowr)
pwrnt.grid(row=0, column=7, sticky=NSEW)
powlbl = Label(f1b, text="W", font=fdfont, background=pcolor)
powlbl.grid(row=0, column=8, sticky=NSEW)
natv = IntVar()
powcb = Checkbutton(f1b, text="Natural", variable=natv, command=ckpowr,
                    font=fdfont, relief='raised', background=pcolor)
powcb.grid(row=0, column=9, sticky=NSEW)
setpwr(power)
f1b.grid(row=1, columnspan=2, sticky=NSEW)
# Added Network label - KD4SIR Scott Hibbs Oct 4, 2013
# Added Node label - KD4SIR Scott Hibbs Oct/13/2013
# Added wof label - KD4SIR Scott Hibbs Jan/19/2017
# Added port label - KD4SIR Scott Hibbs Jan/19/2017
# Network window
lblnet = Label(f1b, text="Network Status", font=fdfont, foreground='royalblue', background='gold')
lblnet.grid(row=2, column=0, columnspan=9, sticky=NSEW)
# Node window
lblnode = Label(f1b, text="My Node: %s" % node, font=fdfont, foreground='royalblue', background='lightgrey')
lblnode.grid(row=2, column=9, columnspan=1, sticky=NSEW)
# Whos on First Window to display operators on bands
# lblwof = Label(f1b, text="", font=fdfont, foreground='royalblue', background='lightgrey')
# lblwof.grid(row=2, column=0, columnspan=9, sticky=NSEW)
# Port window
# lblport = Label(f1b, text="Port: %s" % port_base, font=fdfont, foreground='royalblue', background='lightgrey')
# lblport.grid(row=3, column=9, columnspan=1, sticky=NSEW)
# log window
logw = Text(root, takefocus=0, height=11, width=80, font=fdmfont,
            background='lightgrey', wrap=NONE, setgrid=1)
# logw.configure(cursor='arrow')
scroll = Scrollbar(root, command=logw.yview, background='lightgrey')
logw.configure(yscrollcommand=scroll.set)
logw.grid(row=2, column=0, sticky=NSEW)
scroll.grid(row=2, column=1, sticky=NS)
root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)
# txtbillb = dialog window
txtbillb = Text(root, takefocus=1, height=10, width=80, font=fdmfont,
                wrap=NONE, setgrid=1, background='lightgrey')
scrollt = Scrollbar(root, command=txtbillb.yview)
txtbillb.configure(yscrollcommand=scrollt.set)
txtbillb.grid(row=3, column=0, sticky=NSEW)
scrollt.grid(row=3, column=1, sticky=NS)
root.grid_rowconfigure(3, weight=1)
logw.tag_config("b", foreground="royalblue")
logw.insert(END, "          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n", ("b"))
logw.insert(END, "                            DATABASE DISPLAY WINDOW\n", ("b"))
logw.insert(END, "          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n", ("b"))
logw.insert(END, "%s\n" % prog, ("b"))
#     Add a bottom window for station information
# f1c = Frame(root, bd=1)
# f1c.grid(row=4,columnspan=4,sticky=NSEW)
#     Add entry box for entering data
# entqsl = Entry(f1c,font=fdfont,background='lightgrey')
# entqsl.grid(row=4,column=0,sticky=NSEW)
# txtentry = Text(f1c,takefocus=1,height=2,width=39,font=fdmfont,\
# wrap=NONE,setgrid=1)
# txtentry.grid(row=4,column=4,sticky=NSEW)
# root.grid_rowconfigure(4,weight=1)
# txtentry.insert(END,"Call-Class-Sect- \n")
# fth2lbl = Label(f1c,text="-\n<",font=fdfont,background='lightgrey')
# fth2lbl.grid(row=4,column=3,sticky=NSEW)
# Phonetics box
# fthw2 = Text(f1c,takefocus=0,height=2,width=40,font=fdmfont,\
#            background='lightgrey',wrap=NONE,setgrid=1)
# fthw2.configure(cursor='arrow')
# fthw2.grid(row=4,column=2,sticky=NSEW)
# root.grid_rowconfigure(4,weight=1)
# fthw2.insert(END,"phonetics box")
# txtentry.insert(END,"\n")
# startup
contestlog(0)  # define globals
buildmenus()
sms = syncmsg()  # setup sync message service
qdb = qsodb()  # init qso database
qdb.loadfile()  # read log file
print "Showing GUI"
print
if node == gd.getv('tmast'):
    print "This Node is the TIME MASTER!!"
    print "THIS COMPUTER'S CLOCK BETTER BE RIGHT (preferably GPS locked)"
    print "User should Insure that system time is within 1 second of the"
    print "  correct time and that the CORRECT TIMEZONE is selected (in the OS)"
    print
else:
    print "User should Insure that System Time is within a few seconds of the"
    print "  correct time and that the CORRECT TIMEZONE is selected (in the OS)"
print "To change system time, stop FDLog, change the time or zone, then restart"
print
# These root commands were removed without an explanation in the beta.
# but I'm leaving them in. sah 7/3/2015
root.update()
root.deiconify()
net.start()  # start threads
renew_title()
txtbillb.insert(END, "          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n", ("b"))
txtbillb.insert(END, "                              Dialogue Window\n", ("b"))
txtbillb.insert(END, "          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n", ("b"))
txtbillb.insert(END, "Please select the Operator, Logger, Power and Band/Mode in pink above.\n\n")
txtbillb.insert(END, "-Call-Class-Sect- \n")
txtbillb.config(insertwidth=3)
txtbillb.focus_set()


def topper():
    """This will reset the display for input. Added Jul/01/2016 KD4SIR Scott Hibbs"""
    txtbillb.insert(END, "\n")
    txtbillb.insert(END, "-Call-Class-Sect- \n")


def showthiscall(call):
    "show the log entries for this call"
    p = call.split('/')
    #    print p[0]
    findany = 0
    m, dummy, dummy = qdb.cleanlog()
    #    print m.values()
    for i in m.values():
        #        print i.call
        q = i.call.split('/')
        if p[0] == q[0]:
            if findany == 0: txtbillb.insert(END, "\n")
            txtbillb.insert(END, "%s\n" % i.prlogln(i))
            findany = 1
    return findany


# added this to take out the keyhelp from the code. - Scott Hibbs
def mhelp():
    viewtextf('Keyhelp.txt')

secName = {}

def readSections():
    """this will read the Arrl_sect.dat file for sections"""
    # This modified from Alan Biocca version 153d - Scott Hibbs Feb/6/2017
    try:
        fd = file("Arrl_sect.dat","r")  # read section data
        while 1:
            ln = fd.readline().strip()          # read a line and put in db
            if not ln: break
            if ln[0] == '#': continue
            try:
                sec, dummy, dummy, dummy = string.split(ln,None,3)
                secName[sec] = sec
            except ValueError,e:
                print "rd arrl sec dat err, itm skpd: ",e
        fd.close()
    except IOError,e:
        print "read error during readSections", e

readSections()


def proc_key(ch):
    "process keystroke"
    global kbuf, power, operator, logger, debug, band, node, suffix, tdwin, goBack  # timeok
    testq = 0
    if ch == '?' and (kbuf == "" or kbuf[0] != '#'):  # ? for help
        mhelp()
        return
    # Adding a statement to check for uppercase. Previously unresponsive while capped locked. - Scott Hibbs Jul/01/2016
    # Thanks to WW9A Brian Smith for pointing out that the program isn't randomly frozen and not requiring a restart.
    if ch.isupper():
        txtbillb.insert(END, " LOWERCAPS PLEASE \n")
        kbuf = ""
        topper()
        return
    if ch == '\r':  # return, may be cmd or log entry
        if kbuf[:1] == '#':
            qdb.qst(kbuf[1:])
            kbuf = ""
            txtbillb.insert(END, '\n')
            return
        # check for valid commands
        if re.match(r'[.]h$', kbuf):  # help request
            m = """
                .band 160/80/40/20/15/10/6/2/220/440/900/1200/sat c/d/p
                .off               change band to off
                .pow <dddn>        power level in integer watts (suffix n for natural)
                .node <call-n>     set id of this log node
                .testq <n>         generate n test qsos (only in test mode)
                .tdwin <sec>       display node bcasts exceeding this time skew
                .st                this station status
                .re                summary band report
                .ba                station band report
                .pr                generate entry and log files"""
            viewtextv(m, 'Command Help')
            kbuf = ""
            txtbillb.insert(END, '\n')
            return
        # This section was reworked and added from 152i
        pwr, s = testcmd(".pow", r"[0-9]{1,4}n?", power)
        if s is True:
            power = pwr
            setpwr(power)
        netsync.rem_host, s = testcmd('.remip', r'([0-9]{1,3}[.]){3}[0-9]{1,3}', netsync.rem_host)
        if s: globDb.put('remip', netsync.rem_host)
        # This change was made below for debug, tdwin, and testq
        # Scott Hibbs 7/16/2015
        v, s = testcmd(".debug", r"[0-9]+", debug)
        if s is True: debug = int(v)
        v, s = testcmd(".tdwin", r"[0-9]{1,3}", tdwin)
        if s is True: tdwin = int(v)
        v, s = testcmd(".testq", r"[0-9]{1,2}", testq)
        if s is True: testq = int(v)
        if testq: testqgen(testq)
        saveglob()
        renew_title()
        m = re.match(r"[.]set ([a-z0-9]{3,6}) (.*)$", kbuf)
        if m:
            name, val = m.group(1, 2)
            r = gd.setv(name, val, now())
            if r:
                txtbillb.insert(END, "\n%s\n" % r)
            else:
                txtbillb.insert(END, "\n")
                qdb.globalshare(name, val)  # global to db
            kbuf = ""
            renew_title()
            return
        m = re.match(r"[.]band (((160|80|40|20|15|10|6|2|220|440|900|1200|sat)[cdp])|off)", kbuf)
        if m:
            print
            nb = m.group(1)
            kbuf = ""
            txtbillb.insert(END, "\n")
            bandset(nb)
            return
        if re.match(r'[.]off$', kbuf):
            bandoff()
            kbuf = ""
            txtbillb.insert(END, "\n")
            return
        if re.match(r'[.]ba$', kbuf):
            qdb.bands()
            kbuf = ""
            txtbillb.insert(END, "\n")
            return
        if re.match(r'[.]pr$', kbuf):
            contestlog(1)
            txtbillb.insert(END, " Entry/Log File Written\n")
            txtbillb.insert(END, "\n")
            kbuf = ""
            return
        p = r'[.]edit ([a-z0-9]{1,6})'
        if re.match(p, kbuf):
            m = re.match(p, kbuf)
            call = m.group(1)
            #  qdb.delete(nod,seq,reason)
            kbuf = ""
            txtbillb.insert(END, "To edit: click on the log entry\n")
            return
        #Found that .node needed fixing. Reworked - Scott Hibbs Mar/28/2017
        if re.match(r'[.]node', kbuf):
            if band != 'off':
                txtbillb.insert(END, "\nSet band off before changing node id\n")
                kbuf = ""
                return
            else:
                nde, s = testcmd(".node", r"[a-z0-9-]{1,8}", node)
                if s is True:
                    node = nde
                    setnode(node)
            kbuf = ""
            txtbillb.insert(END, "\n")
            topper()                
            return
        if re.match(r'[.]st$', kbuf):  # status  xx mv to gui
            print
            print
            print "FD Call   %s" % string.upper(gd.getv('fdcall'))
            print "GOTA Call %s" % string.upper(gd.getv('gcall'))
            print "FD Report %s %s" % (string.upper(gd.getv('class')), gd.getv('sect'))
            print "Band      %s" % band
            print "Power     %s" % power
            print "Operator  %s" % operator
            print "Logger    %s" % logger
            print "Node      %s" % node
            if authk != "" and node != "":
                print "Net       enabled"
            else:
                print "Net       disabled"
            print
            kbuf = ""
            txtbillb.insert(END, "\n")
            return
        if re.match(r'[.]re$', kbuf):  # report  xx mv to gui
            print
            print "  band  cw q   pwr dig q   pwr fon q   pwr"
            qpb, ppb, dummy, dummy, dummy, tq, score, maxp, dummy, dummy, dummy, dummy, dummy, dummy, dummy = qdb.bandrpt()
            for b in (160, 80, 40, 20, 15, 10, 6, 2, 220, 440, 1200, 'sat', 'gota'):
                print "%6s" % b,
                for m in 'cdp':
                    bm = "%s%s" % (b, m)
                    print "%5s %5s" % (qpb.get(bm, 0), ppb.get(bm, 0)),
                print
            print
            print "%s total Qs, %s QSO points," % (tq, score),
            print maxp, "watts maximum power"
            kbuf = ""
            txtbillb.insert(END, "\n")
            topper()
            return
        if kbuf and kbuf[0] == '.':  # detect invalid command
            txtbillb.insert(END, " Invalid Command\n")
            kbuf = ""
            txtbillb.insert(END, "\n")
            topper()
            return
        # check for valid contact
        if (ch == '\r'):
            stat, ftm, dummy, sfx, call, xcall, rept = qdb.qparse(kbuf)
            goBack = "%s %s" % (call, rept)# for the up arrow enhancement - Scott Hibbs KD4SIR Jul/5/2018
            if stat == 5:  # whole qso parsed
                kbuf = ""
                if len(node) < 3:
                    txtbillb.insert(END, " ERROR, set .node <call> before logging\n")
                    topper()
                elif qdb.dupck(xcall, band):  # dup check
                    txtbillb.insert(END, "\n\n ***DUPE*** on band %s ***DUPE***\n" % band)
                    topper()
                elif qdb.partck(xcall): # Participant check
                    txtbillb.insert(END, "\n Participant - not allowed \n")
                    topper()
                elif xcall == string.lower(gd.getv('fdcall')):
                    txtbillb.insert(END, "\n That's us - not allowed \n")
                    topper()
                elif xcall == string.lower(gd.getv('gcall')):
                    txtbillb.insert(END, "\n That's us - not allowed \n")
                    topper()
                else:
                    # Added database protection against no band, no power,
                    # no op, and no logger -- KD4SIR Scott Hibbs Jul/15/2013
                    # Added warning against 1D to 1D contacts being
                    # logged but not counting points -- KD4SIR Scott Hibbs Oct/13/2013
                    # Checking Operator or Logger has a license - Scott Hibbs Mar/28/2017
                    legal = 0
                    if re.match(r'[a-z :]+ [a-zA-Z ]+, ([a-z0-9]+)',operator):
                        #print "%s has a license" % operator
                        legal = legal + 1
                    if re.match(r'[a-z :]+ [a-zA-Z ]+, ([a-z0-9]+)',logger):
                        #print "%s has a license" % logger
                        legal = legal + 1
                    if legal == 0:
                        txtbillb.insert(END, "\n\n  The Operator or the logger needs a license.\n")
                        txtbillb.insert(END, "  Please Try Again\n")
                        topper()
                        return
                    # checking for band, power, operator or logger
                    em = ''
                    if band == "off": em += " Band "
                    if power == 0: em += " Power "
                    if len(operator) < 2: em += " Operator "
                    if len(logger) < 2: em += " Logger "
                    if em != '':
                        txtbillb.insert(END, " - WARNING: ( %s ) NOT SET" % em)
                        txtbillb.insert(END, "  Please Try Again\n")
                        topper()
                        return
                    if em == '':
                        # This checks 1D to 1D contacts
                        clas = string.upper(gd.getv('class'))
                        rept1 = string.upper(rept)
                        if clas == '1D':
                            if clas in rept1:
                                txtbillb.insert(END, "\n 1D to 1D contacts are logged, but zero points! \n")
                                topper()
                        # kc7sda - check the report for valid fd or wfd classes:
                        # note according to the cheat sheet, \d is a digit
                        reptclass, dummy = rept.split(" ")
                        m = ""
                        if gd.getv('contst') == "fd":
                            # field day, report in: #+a-f
                            m = re.match(r'[\d][a-fA-F]', rept)
                        elif gd.getv('contst') == "wfd":
                            # WFD
                            m = re.match(r'[\d][ihoIHO]', rept)
                        else:
                            # vhf or other contest
                            # allow everything
                            m = "something"
                        if m == None: # match failed, do not allow and abort logging
                            txtbillb.insert(END, " - ERROR: Bad exchange ( %s ) Please Try Again\n" % rept)
                            topper()
                            return
                        # Check for valid section in report added by Scott Hibbs Feb/6/2017
                        aaaaa = len(rept1)
                        #print "aaaaa is %s" % aaaaa
                        rept2 = rept1[3:aaaaa].strip()
                        #print "rept2 is %s" % rept2
                        if rept2 in secName:
                            pass
                        else:
                            print "\n Use one of these for the section:"
                            kk = ""
                            nx = 0
                            ny = 0
                            for k in sorted(secName):
                                if ny == 0:
                                    kk += "\n  "
                                    ny = ny + 1
                                kk += str(k) + ", "
                                nx = nx + 1
                                if nx == 17:  # how many sections to the line
                                    ny = ny + 1
                                    if ny < 6:  # last line gets the rest
                                        kk += "\n  "
                                        nx = 0
                            print kk
                            #print('\n'.join("{} : {}".format(k, v) for k, v in secName.items()))
                            txtbillb.insert(END, kk)
                            txtbillb.insert(END, "\n  Please try one of the sections above.")
                            topper()
                            return
                        # The entry is good and ready to log
                        txtbillb.insert(END, " - QSL!  May I have another?")
                        txtbillb.insert(END, "\n")
                        topper()
                        tm = now()
                        if ftm:  # force timestamp
                            tm = tm[0:4] + ftm[0:8] + tm[11:]  # yymmdd.hhmmss
                        qdb.qsl(tm, xcall, band, rept)
            elif stat == 4:
                kbuf = ""
                # Added participant check here too - Feb/12/2017 -Scott Hibbs 
                if qdb.partck(xcall): # Participant check
                    txtbillb.insert(END, "\n Participant - not allowed \n")
                    topper()
                elif showthiscall(call) == 0:
                    txtbillb.insert(END, " none found\n")
                    topper()
            return
    if ch == '\x1b':  # escape quits this input line
        txtbillb.insert(END, " ESC -aborted line-\n")
        topper()
        kbuf = ""
        return
    if ch == '\b':  # backspace erases char
        if kbuf != "":
            kbuf = kbuf[0:-1]
            txtbillb.delete('end - 2 chars')
        return
    if ch == '\u1p':  # up arrow reprints the input line - Scott Hibbs KD4SIR Jul/5/2018
        if goBack != "":
            if kbuf == "":
                txtbillb.insert(END, goBack) #print goBack info
                kbuf = goBack
            else: 
                return
        else:
            kbuf = ""
        return
    if ch == ' ':  # space, check for prefix/suffix/call
        stat, tm, dummy, sfx, call, xcall, rept = qdb.qparse(kbuf)
        if stat == 2:  # suffix, dup check
            suffix = kbuf
            kbuf = ""
            r = qdb.sfx2call(suffix, band)
            if not r: r = 'None'
            txtbillb.insert(END, ": %s on band '%s'\n" % (r, band))
            return
        if stat == 3:  # prefix, combine w suffix
            stat, tm, dummy, sfx, call, xcall, rept = qdb.qparse(kbuf + suffix)
            if stat == 4:  # whole call
                kbuf += suffix
                txtbillb.insert(END, sfx)  # fall into call dup ck
        if stat == 4:  # whole call, dup chk
            if qdb.dupck(xcall, band):
                txtbillb.insert(END, "\n\n ***DUPE*** on band %s ***DUPE***" % band)
                showthiscall(call)
                kbuf = ""
                topper()
            elif qdb.partck(xcall): # Participant check
                txtbillb.insert(END, "\n Participant - not allowed \n")
                showthiscall(call)
                kbuf = ""
                topper()
            else:
                kbuf += ' '
                txtbillb.insert(END, ch)
                if showthiscall(call):  # shows the previous contacts with this station
                    txtbillb.insert(END, "%s " % xcall)
            return
    buf = kbuf + ch  # echo & add legal char to kbd buf
    if len(buf) < 50:
        if buf[0] == '.':
            if re.match(r'[ a-zA-Z0-9.,/@-]{0,45}$', ch):
                kbuf = buf
                txtbillb.insert(END, ch)
        elif buf[0] == '#':
            if re.match(r'#[ a-zA-Z0-9.,?/!@$;:+=%&()-]{0,40}$', buf):
                kbuf = buf
                txtbillb.insert(END, ch)
        else:
            stat, tm, dummy, sfx, call, xcall, rept = qdb.qparse(buf)
            if stat > 0 and len(buf) < 50:
                kbuf = buf
                txtbillb.insert(END, ch)


def kevent(event):
    "keyboard event handler"
    global goBack
    ##    print "event '%s' '%s' '%s'"%(event.type,event.keysym,event.keysym_num)
    k = event.keysym_num
    if 31 < k < 123:  # space to z
        proc_key(chr(event.keysym_num))
    elif k == 65362:  # up arrow
        proc_key('\u1p')
    elif k == 65288:  # backspace
        proc_key('\b')
    elif k == 65307:  # ESC
        proc_key('\x1b')
    elif k == 65293:  # return
        proc_key('\r')
    txtbillb.see(END)  # insure that it stays in view
    return "break"  # prevent further processing on kbd events


def focevent(e):
    txtbillb.mark_set('insert', END)
    return "break"


class Edit_Dialog(Toplevel):
    """edit log entry dialog"""
    """Added functionality to check for dupes and change the title to show the error - Scott Hibbs Jul/02/2016"""
    # Had to add variables for each text box to know if they changed to do dupe check.
    global editedornot 
    editedornot = StringVar
    crazytxt = StringVar()
    crazytxt.set('Edit Log Entry')
    crazyclr = StringVar()
    crazyclr.set('lightgrey')
    crazylbl = Label

    def __init__(self, parent, node, seq):
        s = '%s.%s' % (node, seq)
        self.node, self.seq = node, seq
        if qdb.byid[s].band[0] == '*': return
        top = self.top = Toplevel(parent)
        # Toplevel.__init__(self,parent)
        # self.transient(parent)     # avoid showing as separate item
        self.crazytxt.set('Edit Log Entry')
        self.crazyclr.set('lightgrey')
        self.crazylbl = tl = Label(top, text=self.crazytxt.get(), font=fdbfont, bg=self.crazyclr.get(), relief=RAISED)
        # tl = Label(top, text='Edit Log Entry', font=fdbfont, bg='lightgrey', relief=RAISED)
        tl.grid(row=0, columnspan=2, sticky=EW)
        tl.grid_columnconfigure(0, weight=1)
        Label(top, text='Date', font=fdbfont).grid(row=1, sticky=W)
        # Label(top,text='Time',font=fdbfont).grid(row=2,sticky=W)
        Label(top, text='Band', font=fdbfont).grid(row=3, sticky=W)
        # Label(top,text='Mode',font=fdbfont).grid(row=4,sticky=W)
        Label(top, text='Call', font=fdbfont).grid(row=5, sticky=W)
        Label(top, text='Report', font=fdbfont).grid(row=6, sticky=W)
        Label(top, text='Power', font=fdbfont).grid(row=7, sticky=W)
        # Label(top,text='Natural',font=fdbfont).grid(row=8,sticky=W)
        Label(top, text='Operator', font=fdbfont).grid(row=9, sticky=W)
        Label(top, text='Logger', font=fdbfont).grid(row=10, sticky=W)
        self.de = Entry(top, width=13, font=fdbfont)
        self.de.grid(row=1, column=1, sticky=W, padx=3, pady=2)
        self.de.insert(0, qdb.byid[s].date)
        self.chodate = qdb.byid[s].date
        self.be = Entry(top, width=5, font=fdbfont)
        self.be.grid(row=3, column=1, sticky=W, padx=3, pady=2)
        # self.be.configure(bg='gold') #test yes works
        self.be.insert(0, qdb.byid[s].band)
        self.choband = qdb.byid[s].band
        self.ce = Entry(top, width=11, font=fdbfont)
        self.ce.grid(row=5, column=1, sticky=W, padx=3, pady=2)
        self.ce.insert(0, qdb.byid[s].call)
        self.chocall = qdb.byid[s].call
        self.re = Entry(top, width=24, font=fdbfont)
        self.re.grid(row=6, column=1, sticky=W, padx=3, pady=2)
        self.re.insert(0, qdb.byid[s].rept)
        self.chorept = qdb.byid[s].rept
        self.pe = Entry(top, width=5, font=fdbfont)
        self.pe.grid(row=7, column=1, sticky=W, padx=3, pady=2)
        self.pe.insert(0, qdb.byid[s].powr)
        self.chopowr = qdb.byid[s].powr
        self.oe = Entry(top, width=3, font=fdbfont)
        self.oe.grid(row=9, column=1, sticky=W, padx=3, pady=2)
        self.oe.insert(0, qdb.byid[s].oper)
        self.chooper = qdb.byid[s].oper
        self.le = Entry(top, width=3, font=fdbfont)
        self.le.grid(row=10, column=1, sticky=W, padx=3, pady=2)
        self.le.insert(0, qdb.byid[s].logr)
        self.chologr = qdb.byid[s].logr
        bf = Frame(top)
        bf.grid(row=11, columnspan=2, sticky=EW, pady=2)
        bf.grid_columnconfigure((0, 1, 2), weight=1)
        db = Button(bf, text=' Delete ', font=fdbfont, command=self.dele)
        db.grid(row=1, sticky=EW, padx=3)
        sb = Button(bf, text=' Save ', font=fdbfont, command=self.submit)
        sb.grid(row=1, column=1, sticky=EW, padx=3)
        qb = Button(bf, text=' Quit ', font=fdbfont, command=self.quitb)
        qb.grid(row=1, column=2, sticky=EW, padx=3)
        # self.wait_window(top)

    def submit(self):
        """submit edits"""
        global editedornot
        error = 0
        changer = 0 # 0 = no change. 1= change except band and call. 2 = change in call or band
        t = self.de.get().strip()  # date time
        if self.chodate != t:
            #print "The date has changed."
            changer = 1
        self.de.configure(bg='white')
        m = re.match(r'[0-9]{6}\.[0-9]{4,6}$', t)
        if m:
            newdate = t + '00'[:13 - len(t)]
            #print newdate
        else:
            self.de.configure(bg='gold')
            error += 1
        t = self.be.get().strip()  # band mode
        if self.choband != t:
            #print "the band has changed"
            changer = 2
        self.be.configure(bg='white')
        m = re.match(r'(160|80|40|20|15|10|6|2|220|440|900|1200|sat)[cdp]$', t)
        if m:
            newband = t
            #print newband
        else:
            self.be.configure(bg='gold')
            error += 1
        t = self.ce.get().strip()  # call
        if self.chocall != t:
            #print "the call has changed"
            changer = 2
        self.ce.configure(bg='white')
        m = re.match(r'[a-z0-9/]{3,11}$', t)
        if m:
            newcall = t
            #print newcall
        else:
            self.ce.configure(bg='gold')
            error += 1
        t = self.re.get().strip()  # report
        if self.chorept != t:
            print "the section is not verified - please check."
            changer = 1
        self.re.configure(bg='white')
        m = re.match(r'.{4,24}$', t)
        if m:
            newrept = t
            #print newrept
        else:
            self.re.configure(bg='gold')
            error += 1
        t = self.pe.get().strip().lower()  # power
        if self.chopowr != t:
            #print "the power has changed."
            changer = 1
        self.pe.configure(bg='white')
        m = re.match(r'[0-9]{1,4}n?$', t)
        if m:
            newpowr = t
            #print newpowr
        else:
            self.pe.configure(bg='gold')
            error += 1
        t = self.oe.get().strip().lower()  # operator
        if self.chooper != t:
            #print "the Operator has changed."
            changer = 1
        self.oe.configure(bg='white')
        if participants.has_key(t):
            newopr = t
            #print newopr
        else:
            self.oe.configure(bg='gold')
            error += 1
        t = self.le.get().strip().lower()  # logger
        if self.chologr != t:
            #print "the logger has changed."
            changer = 1
        self.le.configure(bg='white')
        if participants.has_key(t):
            newlogr = t
            #print newlogr
        else:
            self.le.configure(bg='gold')
            error += 1
        if error == 0:
            # There was no dupe check on the edited qso info. This was added. Scott Hibbs Jul/01/2016
            if changer == 0:
                print 'Nothing changed. No action performed.'
                self.crazytxt.set('nothing changed?')
                self.crazyclr.set('pink2')
                self.crazylbl.configure(bg=self.crazyclr.get(), text=self.crazytxt.get())
                error += 1
            if changer == 1:
                # delete and enter new data because something other than band or call has changed. 
                # print "no errors, enter data"
                reason = "edited"
                qdb.delete(self.node, self.seq, reason)
                qdb.postnew(newdate, newcall, newband, newrept, newopr, newlogr, newpowr)
                self.top.destroy()
                txtbillb.insert(END, " EDIT Successful\n")
                topper()
            if changer == 2:
                #band or call changed so check for dupe before submitting to log.
                if qdb.dupck(newcall, newband):  # dup check for new data
                    print 'Edit is a DUPE. No action performed.'
                    self.crazytxt.set("This is a DUPE")
                    self.crazyclr.set('pink2')
                    self.crazylbl.configure(bg=self.crazyclr.get(), text=self.crazytxt.get())
                    error += 1
                else:
                    # delete and enter new data
                    # print "no errors, enter data"
                    reason = "edited"
                    qdb.delete(self.node, self.seq, reason)
                    qdb.postnew(newdate, newcall, newband, newrept, newopr, newlogr, newpowr)
                    self.top.destroy()
                    editedornot = "1"
                    txtbillb.insert(END, " EDIT Successful\n")
                    topper()

    def dele(self):
        print "delete entry"
        reason = 'deleteclick'
        qdb.delete(self.node, self.seq, reason)
        self.top.destroy()

    def quitb(self):
        print 'quit - edit aborted'
        self.top.destroy()


def edit_dialog(node, seq):
    'edit log entry'
    dummy = Edit_Dialog(root, node, seq)

    
def log_select(e):
    'process mouse left-click on log window'
    #    print e.x,e.y
    t = logw.index("@%d,%d" % (e.x, e.y))
    #    print t
    line, dummy = t.split('.')
    line = int(line)
    #    print line
    logtext = logw.get('%d.0' % line, '%d.82' % line)
    # print logtext
    dummy = logtext[0:8].strip()
    seq = logtext[65:69].strip()
    bxnd = logtext[8:14].strip()
    cxll = logtext[15:22].strip()
    #  In case user clicks on a deleted log entry Feb/2/2017 Scott Hibbs
    baddd = logtext[23:24].strip()
    if baddd == '*':
        print "Can't edit a delete entry"
        return 'break'
    if len(seq) == 0: return 'break'
    #    In case user clicks on tildes - May/11/2014 Scott Hibbs
    if seq == '~~~~': return 'break'
    # fixed clicking on the copywrite line gave a valueerror - Feb/12/2017 Scott Hibbs
    try:
        seq = int(seq)
        stn = logtext[69:].strip()
        if len(stn) == 0: return 'break'
    except ValueError:
        return 'break'
    print stn, seq, bxnd, cxll
    if stn == node:  # only edit my own Q's
        # Also check to make sure the call isn't previously deleted. Jul/02/2016 KD4SIR Scott Hibbs
        if qdb.dupck(cxll, bxnd):
            # Now we check to see if the entry is still in the log. Mar/31/2017 KD4SIR Scott Hibbs
            bid, dummy, dummy = qdb.cleanlog()  # get a clean log
            stnseq = stn +"|"+str(seq)
            if stnseq in bid:
                edit_dialog(stn, seq)
            else:
                print "Previously edited contact - Not in the log."
                return
        else:
            print "This is not a log entry."
    else:
        print "Cannot edit another person's contact."
    return 'break'

updatect = 0


# This function updated from 152i
def update():
    "timed updater"
    global updatect
    root.after(1000, update)  # reschedule early for reliability
    sms.prout()  # 1 hz items
    updatebb()
    net.si.age_data()
    mclock.adjust()
    #   if mclock.level == 0:  # time master broadcasts time more frequently
    #   net.bcast_time()
    updatect += 1
    # if (updatect % 5) == 0:         # 5 sec
    # net.bcast_now()
    if (updatect % 10) == 0:  # 10 sec
        updateqct()  # this updates rcv packet fail
        renew_title()  # this sends status broadcast
    if (updatect % 30) == 0:  # 30 sec
        mclock.update()
    if updatect > 59:  # 60 sec
        updatect = 0
root.bind('<ButtonRelease-1>', focevent)
txtbillb.bind('<KeyPress>', kevent)
logw.bind('<KeyPress>', kevent)  # use del key for?xx
logw.bind('<Button-1>', log_select)  # start of log edit
root.after(1000, update)  # 1 hz activity
root.mainloop()  # gui up
print "\nShutting down"
# the end was updated from 152i
band = 'off'  # gui down, xmt band off, preparing to quit
net.bcast_now()  # push band out
time.sleep(0.2)
saveglob()  # save globals
print "  globals saved"
print "\n\nFDLog is shut down, you should close this console window now"
time.sleep(0.5)
# os._exit(1)  # kill the process somehow?
exit(1)

# Suggestions/To Do:
#
#  Grab out of order entry from Alan Biocca's FDLog. 
#
#  Change Participant entry so the name is on top. (It's odd to ask their initials first.) Scott 2018 Field Day notes
#
#  Would love another file to use for the "InfoNode" computer. Scott 2017 Field Day notes
        # It will allow visitors/participants to log in
        # It will show top 5 operators and top 5 loggers
        # It will show worked all states
        # Provide info on Amateur Radio (video and/or short articles to print?)
        # Provide info on the local club
        # fool-proof - no logging from this node.
#
#  add node list display after db read during startup?
#
#  add phonetic alphabet display (started: some code commented out) 2016 Field Day notes
#
#  Weo suggested making Control-C text copy/paste work. (suggestion from original group - FDLog)
#
#  Tried and tried to get wof (whoseonfirst) to return only one value for the mouse over.
#    I don't have the python skilz... If you can awesome!!! -Scott Mar/18/2017
#
# eof
