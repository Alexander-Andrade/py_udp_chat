from socket import*
import sys
import struct
import time
import sched
from threading import*
import random
from packet import*


def enabsock_recv_timeout(self,timeOutSec):
    if sys.platform.startswith('win'):
        timeval = timeOutSec * 1000
    elif sys.platform.startswith('linux'):
        sock.setsockopt(SOL_SOCKET, SO_RCVTIMEO, struct.pack("LL", timeOutSec, 0))

def disabsock_recv_timeout(self):
    if sys.platform.startswith('win'):
        timeval = 0
    elif sys.platform.startswith('linux'):
        sock.setsockopt(SOL_SOCKET, SO_RCVTIMEO, struct.pack("LL",0,0))


class Peer:

    def __init__(self,group,port):
        self.nickname = ''
        self.port = int(port)
        self.group = group
        #for joininig and unjoining to the group
        self.mreq = b''
        self.net_interface = Peer.first_private_network_interface()
        self.group_sock = socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP)
        self.group_sock.bind((self.net_interface,port))
        self.send_sock = socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP)
        self.__join_group(self.group_sock)
        self.peers = set()
        self.n_attempts = 3
        self.timeout = 10
       
    @staticmethod
    def first_private_network_interface():
        addrInfoList = getaddrinfo('',None,AF_INET)
        #stay only private network interfaces
        priv_interfs = [addr_info[4][0] for addr_info in addrInfoList if addr_info[4][0].startswith('192.168.')]
        return min(priv_interfs)     

    def __join_group(self,sock):
        #mreq = struct.pack('4sl',inet_aton(self.group),INADDR_ANY)
        self.mreq = struct.pack('4s4s',inet_aton(self.group),inet_aton(self.net_interface))
        sock.setsockopt(IPPROTO_IP,IP_ADD_MEMBERSHIP,self.mreq)
        sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        #default
        self.sock.setsockopt(IPPROTO_IP,IP_MULTICAST_TTL,struct.pack('b',1))

    def __unjoin_group(self,sock):
        self.sock.setsockopt(SOL_IP,IP_DROP_MEMBERSHIP,self.mreq)

    def group_send(self,msg):
        self.sock.sendto(msg,(self.group,self.port))

    def send(self,msg,addr):
        self.sock.sendto(msg,addr)

    def recv(self,num):
        return self.sock.recvfrom(num)

    def identify_peers(self, nickname):
        self.nickname = nickname
        #send multicast Identification packet with nickname? chosen by you  
        ident_pack = Packet(tos=MsgTOS.Identification,data=self.nickname)  
        ident_pack.pack()
        #initiat timeout = 2 sec, then growing exponentially
        time_out = 2 
        for i in range(self.n_attempts):
            self.send_sock.sendto(ident_pack.packet, (self.group,self.port))
            self.group_sock.timeout(time_out)
            self.group_sock.recvfrom(1024)
                

    def __del__(self):
        self.__unjoin_group(self.sock)
        self.sock.close()

if __name__=='__main__':
    '''
    peer = Peer('224.3.29.71',6000)
    print(peer.recv(1024))
    del peer
    '''
    '''
    random.seed()
    for i in range(10):
        print(random.uniform(0.0,10.0))
    '''

   
    