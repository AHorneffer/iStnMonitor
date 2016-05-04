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
IPin=""
IPto="129.16.208.180"	#Simon
UDP_PORT=6070 #For istnEvn service
MULTICAST_ADDRESS = 0xe0010104
MULTICAST_PORT = 4242
MULTICAST_GROUP = ('224.1.1.04', MULTICAST_PORT)
isLogging=True
logfilename='/home/tobia/lofar/logs/StnStatusLatest.log'
#End configurable variables


import socket
import struct

SHAME_BLOCK_HEAD = '16siiii'
name = 'LOFAR_SE607'
size = 0
version = 0
timestamp = 0
flag = 0
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
    #Process status lines
    status_lns = message.splitlines()
    #Get iStnStatus version
    (version_heading, version) = status_lns[0].split(': ')
    if version == '1.2':
        (environ_ln, switch_ln, swlevel_ln
        ) = status_lns[1:4]
    if version == '2.0':
       (environ_ln, switch_ln, swlevel_ln, bmctluser_ln
        ) = status_lns[1:5]
    #Process environment state line
    (timestamp, station_keyval, ECvers_keyval, cab3temp_keyval, cab3hum_keyval
    , heater_keyval, fourty8V_keyval, LCU_keyval, lightning_keyval
    ) = environ_ln.split(',')
    
    #Start creating status dict
    status = {}
    keyvalsep = ': '
    #LOFAR iStnStatus version
    status['version'] = version
    #Environment
    status['time'] =     timestamp
    (station_key,  status['station']) =  station_keyval.split(keyvalsep)
    (ECvers_key,   status['ECvers']) =   ECvers_keyval.split(keyvalsep)
    (cab3temp_key, status['cab3temp']) = cab3temp_keyval.split(keyvalsep)
    (cab3hum_key,  status['cab3hum']) =  cab3hum_keyval.split(keyvalsep)
    (heater_key,   status['heater']) =   heater_keyval.split(keyvalsep)
    (fourty8V_key, status['48V']) =      fourty8V_keyval.split(keyvalsep)
    (LCU_key,      status['LCU']) =      LCU_keyval.split(keyvalsep)
    (lightning_key,status['lightning']) =lightning_keyval.split(keyvalsep)
    #Switch state
    (switch_key, status['switch']) = switch_ln.split(keyvalsep)
    #SW level
    (swlevel_key, status['swlevel']) = swlevel_ln.split(keyvalsep)
    #Beamctl User
    (bmctluser_key, status['beamctl']) = bmctluser_ln.split(keyvalsep)
    return status

def stnstat2shamecast(stnstatdict):
    """Convert intl station status in dict form to a shame cast (OSO event
    monitor broadcasting framework) block."""
    pass


while True:
    message, addr = sockin.recvfrom( 1*1024 ) # buffer size is 1024 bytes
    
    if isLogging:
        f=open(logfilename, 'w')
        f.write("Latest message:\n")
        f.write(message)
        f.close()
        stnstatdict = stnstat2dict(message)
        print stnstatdict
        
    if message[0:4] == "TEST":
        print "Testing:"
        print message
    if RELAYSTNSTAT:
        sockout.sendto(message,(IPto,UDP_PORT))
    if SHAMECAST:
    #Multicast
        stnstatdict = stnstat2dict(message)
        stnstatshm = stnstat2shamecast(stnstatdict)
        sockmout.sendto(stnstatshm, MULTICAST_GROUP)

