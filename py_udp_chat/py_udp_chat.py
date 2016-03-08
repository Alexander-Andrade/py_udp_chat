from socket import*
import sys
import struct

class Peer:

    def __init__(self,group,port):
        self.nickname = ''
        self.port = int(port)
        self.group = group
        #for joininig and unjoining to the group
        self.mreq = b''
        self.net_interface = first_private_network_interface()
        self.sock = socket(AF_INET,SOCK_DGRAM,IPPROTO_UDP)
        self.__join_group(self.sock)
        self.sock.bind((self.net_interface,port))
        #join group
       
    @staticmethod
    def first_private_network_interface():
        addrInfoList = getaddrinfo('',None,AF_INET)
        #stay only private network interfaces
        priv_interfs = [addr_info[4][0] for addr_info in addrInfoList if addr_info[4][0].startswith('192.168.')]
        return min(priv_interfs)     

    def __join_group(self,sock):
        self.mreq = inet_aton(self.group) + inet_aton(self.net_interface)
        sock.setsockopt(SOL_IP,IP_ADD_MEMBERSHIP,self.mreq)
        sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        #default
        self.sock.setsockopt(IPPROTO_IP,IP_MULTICAST_TTL,struct.pack('B',1))

    def __unjoin_group(self,sock):
        self.sock.setsockopt(SOL_IP,IP_DROP_MEMBERSHIP,self.mreq)

    def group_send(self,msg):
        self.sock.sendto(msg,0,(self.group,self.port))

    def send(self,msg,addr):
        self.sock.sendto(msg,0,addr)

    def recv(self,num):
        return self.sock.recvfrom(num)

    def __del__(self):
        self.__unjoin_group(self.sock)
        self.sock.close()

if __name__=='__main__':
    peer = Peer('224.0.0.1',6000)
    peer.group_send(b'hello')
    del peer