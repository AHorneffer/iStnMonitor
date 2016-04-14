#!/usr/bin/python
#LOFAR station monitoring UDP client v1.1
#Receives updates in UDP packets and enters these into RRD files using rrdtool
#
#Simon Casey
#Onsala Space Observatory
#
#
#Revision history
#v1.0	2012-10-12	Initial release
#v1.1	2013-04-03	Added '-t' to rrdupdate to ensure correct field order

import socket, rrdtool, re, sys

STN_string="se607ec"
UDP_PORT=6070

RRD_FILE_env="/var/lib/cacti/rra/xxxxx_environment.rrd"
RRD_FILE_status="/var/lib/cacti/rra/xxxxx_status.rrd"
LOG_FILE="/tmp/xxxxx.log"

#DS order: Temperature:Humidity:Heater:48V:LCU:Lightning:Switch:Software Level
#LCU_Fields="Cab3 Temp", "Cab3 Hum", "Heater", "48V", "LCU", "Lightning", "Switch", "Software Level"

ENV_order = "Temperature:Humidity"
STATUS_order = "Heater:48V:LCU:Lightning:SWLevel:Switch"

sockin = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP
sockin.bind( ("",UDP_PORT) )

while True:
    message, addr = sockin.recvfrom( 1024 ) # buffer size is 1024 bytes
    print "received message:", message
    sys.stdout.flush()
    f=open(LOG_FILE,'a')
    f.write(message+"\n")
    f.close()
    message +='\n'

    try:
        if re.search('Station: *(.+?)[,\n]', message).group(1) == STN_string or re.search('Station: *(.+?)[,\n]', message).group(1) == 'Unknown':
            L_Temp=re.search('Cab3 Temp: *(.+?)C,', message).group(1)
            L_Hum=re.search('Cab3 Hum: *(.+?)%,', message).group(1)
            if re.search('Heater: *(.+?)[,\n]', message).group(1) == 'ON':
                L_Heater="2"
            else: L_Heater="0"
            if re.search('48V: *(.+?)[,\n]', message).group(1) == 'ON':
                L_48V="1"
            else: L_48V="0"
            if re.search('LCU: *(.+?)[,\n]', message).group(1) == 'ON':
                L_LCU="3"
            else: L_LCU="0"
            print L_LCU
            if re.search('Lightning: *(.+)[,\n]', message).group(1) == 'N.A.':
                L_Lightning="0"
            else: L_Lightning="4"
            
            if re.search('Switch: *(.+?)[,\n]', message).group(1) == 'ilt':
                L_Switch="1"
            else: L_Switch="0"
            L_SwL = re.search('Software Level: *(.+?)[,\n]', message).group(1)
            
            print L_Temp + ':' + L_Hum + ':' + L_Heater + ':' + L_48V + ':' + L_LCU + ':' + L_Lightning + ':' + L_Switch + ':' + L_SwL
            
            sys.stdout.flush()
            try:
                rrdtool.update(RRD_FILE_env, '-t', ENV_order, 'N:' + L_Temp + ':' + L_Hum)
            except:
                print "Error updaing " + RRD_FILE_env
            try:
                rrdtool.update(RRD_FILE_status, '-t', STATUS_order, 'N:' + L_Heater + ':' + L_48V + ':' + L_LCU + ':' + L_Lightning + ':' + L_SwL + ':' + L_Switch)
            except:
                print "Error updating " + RRD_FILE_status

            print "Finished update"
            sys.stdout.flush()
    except:
        print "Error performing update"
