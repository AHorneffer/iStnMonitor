#!/usr/bin/python

## Script for aggregating station status information which is broadcast on UDP.
## Inspired by (and partially borrowed from) A. Horneffers "isEcStatus.py" code.
## T. Carozzi 30 Sep 2013 (25 Jan 2012) (TobiaC)
## Modified by A. Horneffer 2013--2017
## 

#Please edit stnStatMon_config according to your taste and LCU network setup
from stnStatMon_config import *

GW_PC_UDP_PORT=6070 #Port for istn service (If you edit this you will need to update port on clients)

#Paths to various lofar commands (please include the trailing "/"):
OPERATIONSPATH="/opt/operations/bin/"
#OPERATIONSPATH="/usr/local/bin/"
LOFARBINPATH="/opt/lofar/bin/"

import sys
import socket
import struct
import time
from subprocess import Popen, PIPE
import datetime
from parse_rspctl import parse_rspctl_status, parse_rspctl_rcu
from parse_tbbctl import parse_tbbctl_status

VERSION = '2.3' # version of this script

status={}


def pathtoISSTATUS():
    """Determine path to ISSTATUS script."""
    lcuSWver = get_lofar_sw_ver()
    change1 = (1, 16, 0)
    change2 = (2, 17, 6)
    changelatest = change2
    if   lcuSWver >= changelatest:
        STATIONTESTPATH='/opt/lofar/sbin/'
        ISSTATUSPY='status.py'
    elif lcuSWver >= change1 and lcuSWver < change2:
        STATIONTESTPATH='/opt/lofar/sbin/'
        ISSTATUSPY='isStatus.py'
    elif lcuSWver <  change1:
        STATIONTESTPATH='/opt/stationtest/test/envcontroltest/'
        ISSTATUSPY='isStatus.py'
    else:
        print "Cannot determine version of path"
        exit(1)
        
    return STATIONTESTPATH+ISSTATUSPY


def get_isStatus():
    ISSTATUSscript = pathtoISSTATUS()
    #Environmental control status:
    ECstatOut=Popen(
           ISSTATUSscript,
           stdout=PIPE).communicate()[0]
    ECstatOutLns= ECstatOut.splitlines()
    status['station']=ECstatOutLns[1].split()[0]
    status['version']=ECstatOutLns[1].split()[2][1:-1]
    status['time']=time.mktime(time.strptime(ECstatOutLns[2].lstrip().rstrip()))
    key=''
    for lineNr in range(4,10):
        (desc,val)=ECstatOutLns[lineNr].split('=')
        description=desc.rstrip()
        value=val.lstrip()
        #The output labels from isStatus.py were changed 21 June 2013.
        #Effectively the string "cab3" was removed. I changed the
        #matching condition to the output, but not the subsequent
        #naming so as to not have to change anything downstream from here.
        if description == 'temperature':
           key='cab3temp'
           value=float(value)
        elif description == 'humidity':
           key='cab3hum'
           value=float(value)
        elif description == 'heater state':
           key='heater'
        elif description == 'power 48V state':
           key='48V'
        elif description == 'power LCU state':
           key='LCU'
        elif description == 'lightning state':
           key='lightning'
        status[key]=value


def get_lofar_sw_ver():
    ps_out=Popen(
           [LOFARBINPATH+'swlevel','-V'],
           stdout=PIPE).communicate()[0]
    verstr=ps_out.split('-')[-1]
    ver_maj, ver_min, ver_pat = [int(ver.strip()) for ver in verstr.split('_')]
    return ver_maj, ver_min, ver_pat


def aggregateInfo():
    """Aggregate information from various sources into a useful iStnMon status.
       The result is in the 'status' global variable."""
    #Get the isStatus status.
    get_isStatus()
    
    if True:
      #Station switch status:
      StnSwtchstatOut=Popen(
           [OPERATIONSPATH+'getstationmode'],
           stdout=PIPE).communicate()[0]
      StnSwtchstatOutLns= StnSwtchstatOut.splitlines()
      status['switch']=StnSwtchstatOutLns[0].split()[-1]
    if True:
      #Software level:
      swlstatOut=Popen(
           [LOFARBINPATH+'swlevel','-S'],
           stdout=PIPE).communicate()[0]
      swlstatOutLns= swlstatOut.splitlines()
      status['softwareLevel']=int(swlstatOutLns[0].split()[0])
    if CHECK_BC_USER:
      #beamctl user:
      bc_user = who_beamctl()
      status['beamctl']=bc_user
    if CHECK_NUM_LOGINS:
      #number of logged-in users
      woutput = Popen('w | wc', shell=True,
                      stdout=PIPE).communicate()[0].split()[0]
      status['allUsers'] = int(woutput)-2
      woutputuser = Popen('w | grep user[0-9] | wc', shell=True,
                          stdout=PIPE).communicate()[0].split()[0]
      status['localUsers'] = int(woutputuser)
    if CHECK_RSP_STATS and (status['softwareLevel'] >= 2):
      #status of the RSP boards
      statoutput = Popen(LOFARBINPATH+'rspctl --status', shell=True,
                         stdout=PIPE,stderr=PIPE).communicate()[0]
      status['rspstat'] = parse_rspctl_status(statoutput)
      rcuoutput = Popen(LOFARBINPATH+'rspctl --rcu', shell=True,
                        stdout=PIPE,stderr=PIPE).communicate()[0]
      status['rcumodes'] = parse_rspctl_rcu(rcuoutput)
    if CHECK_TBB_STATS and (status['softwareLevel'] >= 2):
      #status of the TBBs
      tbbstatoutput = Popen('/opt/lofar/bin/tbbctl --status', shell=True,
                         stdout=PIPE,stderr=PIPE).communicate()[0]
      status['tbbstat'] = parse_tbbctl_status(tbbstatoutput)


def who_beamctl():
    ps_out=Popen(
           ['/bin/ps', '-Cbeamctl', '--no-headers', '-ouser'],
           stdout=PIPE).communicate()[0]
    ps_out_lns = ps_out.splitlines()
    if len(ps_out_lns) == 0:
        bc_user = 'None'
    else:
        bc_user = ps_out_lns[0]
    return bc_user


def printInfo():
    print status['station']
    print status['version']
    print status['time']
    print status['cab3temp']
    print status['cab3hum']
    print status['heater']
    print status['48V']
    print status['LCU']
    print status['lightning']
    if CHECK_BC_USER:
      print status['beamctl']
    if status.has_key('rcumodes'):
      print "Text output of rcumodes not implemented yet"
    if status.has_key('rspstat'):
      print "Text output of RSP status not implemented yet"
    if status.has_key('tbbstat'):  
      print "Text output of TBB status not implemented yet"

def sendstatus(isUDP=True,isSendTest=False,isLogged=True):
        date = time.localtime(status['time'])
        outstring = "LOFAR_STN_STATUS (version): %s" % VERSION
        outstring += "\n"
        outstring += "%4d-%02d-%02d-%02d:%02d:%02d, "%(
            date.tm_year, date.tm_mon, date.tm_mday,
            date.tm_hour,  date.tm_min, date.tm_sec)
        #Environmental control status:
        outstring += "Station: %s, "%status['station']
        outstring += "ECvers: %s, "%status['version']
        outstring += "Cab3 Temp: %.2fC, "%status['cab3temp']
        outstring += "Cab3 Hum: %.2f%%, "%status['cab3hum']
        outstring += "Heater: %s, "%status['heater']
        outstring += "48V: %s, "%status['48V']
        outstring += "LCU: %s, "%status['LCU']
        outstring += "Lightning: %s"%status['lightning']
        #The switch status:
        outstring += "\n"
        outstring += "Switch: %s" % status['switch']
        #The switch status:
        outstring += "\n"
        outstring += "Software Level: %s" % status['softwareLevel']
        if CHECK_BC_USER:
          #Who is using beamctl:
          outstring += "\n"
          outstring += "beamctl User: %s" % status['beamctl']
        if CHECK_NUM_LOGINS:
          #Logged in users:
          outstring += "\n"
          outstring += "All Users: %s " % status['allUsers']
          outstring += "Local Users: %s " % status['localUsers']
        if status.has_key('rcumodes'):
          #rcumodes
          outstring += "\n"
          outstring += "RCUmodes -1:%d 0:%d 1:%d 2:%d 3:%d 4:%d 5:%d 6:%d 7:%d"\
              % (status['rcumodes']['-1'], status['rcumodes']['0'], \
                     status['rcumodes']['1'], status['rcumodes']['2'], \
                     status['rcumodes']['3'], status['rcumodes']['4'], \
                     status['rcumodes']['5'], status['rcumodes']['6'], \
                     status['rcumodes']['7'],)
        if status.has_key('rspstat'):
          outstring += "\n"
          outstring +="RSPtemps PCBmean: %.2fC, BPmean: %.2fC, APmean: %.2fC\n" \
              % (status['rspstat']['PCBtempmean'], \
                     status['rspstat']['BPtempmean'], \
                     status['rspstat']['APtempmean'])
          outstring += "RSPtemps PCBmax: %.2fC, BPmax: %.2fC, APmax: %.2fC\n" \
              % (status['rspstat']['PCBtempmax'], \
                     status['rspstat']['BPtempmax'], \
                     status['rspstat']['APtempmax'])
          outstring += "RSPtemps PCBmin: %.2fC, BPmin: %.2fC, APmin: %.2fC\n" \
              % (status['rspstat']['PCBtempmin'], \
                     status['rspstat']['BPtempmin'], \
                     status['rspstat']['APtempmin'])
          outstring += "RSPvolt V1.2: %.2f, V2.5: %.2f, V3.3: %.2f\n" \
              % (status['rspstat']['volt12mean'], \
                     status['rspstat']['volt25mean'], \
                     status['rspstat']['volt33mean'])
          outstring += "RSPvoltMax V1.2: %.2f, V2.5: %.2f, V3.3: %.2f\n" \
              % (status['rspstat']['volt12max'], \
                     status['rspstat']['volt25max'], \
                     status['rspstat']['volt33max'])
          outstring += "RSPvoltMin V1.2: %.2f, V2.5: %.2f, V3.3: %.2f" \
              % (status['rspstat']['volt12min'], \
                     status['rspstat']['volt25min'], \
                     status['rspstat']['volt33min'])
        if status.has_key('tbbstat'):
            outstring += "\n"
            outstring +="Bad-TBBs: %d, Good-TBBs: %d\n" \
                % (status['tbbstat']['badTBBs'], \
                       status['tbbstat']['goodlines'])
            outstring +="TBBtemps PCBmean: %.2fC, TPmean: %.2fC, MPmean: %.2fC\n" \
                % (status['tbbstat']['PCBtempmean'], \
                       status['tbbstat']['TPtempmean'], \
                       status['tbbstat']['MPtempmean'])
            outstring += "TBBtemps PCBmax: %.2fC, TPmax: %.2fC, MPmax: %.2fC\n" \
                % (status['tbbstat']['PCBtempmax'], \
                       status['tbbstat']['TPtempmax'], \
                       status['tbbstat']['MPtempmax'])
            outstring += "TBBtemps PCBmin: %.2fC, TPmin: %.2fC, MPmin: %.2fC\n" \
                % (status['tbbstat']['PCBtempmin'], \
                       status['tbbstat']['TPtempmin'], \
                       status['tbbstat']['MPtempmin'])
            outstring += "TBBvolt V1.2: %.2f, V2.5: %.2f, V3.3: %.2f\n" \
                % (status['tbbstat']['volt12mean'], \
                       status['tbbstat']['volt25mean'], \
                       status['tbbstat']['volt33mean'])
            outstring += "TBBvoltMax V1.2: %.2f, V2.5: %.2f, V3.3: %.2f\n" \
                % (status['tbbstat']['volt12max'], \
                       status['tbbstat']['volt25max'], \
                       status['tbbstat']['volt33max'])
            outstring += "TBBvoltMin V1.2: %.2f, V2.5: %.2f, V3.3: %.2f" \
                % (status['tbbstat']['volt12min'], \
                       status['tbbstat']['volt25min'], \
                       status['tbbstat']['volt33min'])

        if isSendTest:
           outstring="TEST "+outstring
   
        if isUDP:
           UDP_IP=GW_PC_UDP_IP
           UDP_PORT=GW_PC_UDP_PORT

           sock = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP
           sock.sendto( outstring, (UDP_IP, UDP_PORT) )
           if isLogged:
              print outstring 
        else:
           print outstring


from optparse import OptionParser
if __name__ == "__main__":
   parser = OptionParser()
   parser.add_option("-p", "--print",dest="prntout",
                  action="store_true",default=False,
                  help="just print status messages to stdout (no UDP)")
   (options, args) = parser.parse_args()

   aggregateInfo()
   #printInfo()
   sendstatus(isUDP= not( options.prntout))
