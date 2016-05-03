#!/usr/bin/python

#This script runs on the Gateway PC and
#relays UDP packets from LCU on one ethernet port
#to an external computer.
#
#Tobia Carozzi 2012-10-30
#
#Edit following lines for your particular network configuration.

#LCU_IP="192.168.154.1"		#se607c
#IPout="129.16.208.120"	#heid eth0
IPin="192.168.154.201"	#heid eth1
IPto="129.16.208.180"	#Simon
#IPto="129.16.208.105"	#blid
UDP_PORT=6070

import socket

#Inbound
sockin = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP
sockin.bind( (IPin,UDP_PORT) )

#outbound
sockout = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP

isLogging=True
logfilename='/home/tobia/lofar/logs/StnStatusLatest.log'

while True:
    message, addr = sockin.recvfrom( 1024 ) # buffer size is 1024 bytes
    if isLogging:
       f=open(logfilename, 'w')
       f.write("Latest message:\n")
       f.write(message)
       f.close()

    if message[0:4] == "TEST":
       print "Testing:"
       print message
    else:
       sockout.sendto(message,(IPto,UDP_PORT))
