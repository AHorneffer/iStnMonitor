#!/usr/bin/python

#This script runs on the Gateway PC and
#relays UDP packets from LCU on one ethernet port
#to an external computer.
#
#Tobia Carozzi 2012-10-30
#
#Edit following lines for your particular network configuration.
RELAYSTNSTAT = False
SHAMECAST = False
IPin="192.168.154.201"	#heid eth1
IPto="129.16.208.180"	#Simon
UDP_PORT=6070 #For istnEvn service
MULTICAST_ADDRESS = 0xe0010104
MULTICAST_PORT = 4242
MULTICAST_GROUP = ('224.1.1.04', MULTICAST_PORT)
isLogging=True
logfilename='/home/tobia/lofar/logs/StnStatusLatest.log'
#End configurable variables


import socket
from struct import pack

SHAME_BLOCK_HEAD = '16siiii'
lofar_sbh = struct.pack(SHAME_BLOCK_HEAD, name, size, version, timestamp, flag)
#struct SHAME_BLOCK {
#  char name[16];
#  int size;
#  int version;
#  int timestamp;
#  int flag;
#  struct MyData myData;
#} block;

#Inbound
sockin = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP
sockin.bind( (IPin,UDP_PORT) )

#outbound
sockout = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP

#multicast-out
sockmout = socket.socket( socket.AF_INET, # Internet
                      socket.SOCK_DGRAM ) # UDP
# Set the time-to-live for messages to 1 so they do not go past the
# local network segment.
ttl = struct.pack('b', 1)
sockmout.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)


def stnstat2dict(message):
    """Convert intl station status in the form of an string (as used as message
    between server and cacti client) to a python dict."""
    pass #Not implemented yet


def stnstat2shamecast(stnstatdict):
    """Convert intl station status in dict form to a shame cast (OSO event
    monitor broadcasting framework) block."""
    pass


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
    if RELAY2CACTICLI:
        sockout.sendto(message,(IPto,UDP_PORT))
    if SHAMECAST:
    #Multicast
        stnstatdict = stnstat2dict(message)
        stnstatshm = stnstat2shamecast(stnstatdict)
        sockmout.sendto(stnstatshm, MULTICAST_GROUP)
