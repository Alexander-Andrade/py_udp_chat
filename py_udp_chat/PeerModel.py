import threading
import struct
import time
import random
import math
from socket import*
from FrameType import FrameType
from net_interface import*
from MixedSocket import MixedSocket
from Frame import Frame
from PeerInfo import PeerInfo
                                            
def random_port(str_num_type,min=0):
    return random.randrange(min, 2 << (int(struct.calcsize(str_num_type)*8 - 1)))

class PeerModel:

    def __init__(self,group,group_port,**kwargs):
        self.group_port = int(group_port)
        self.group = group
        self.group_addr = (self.group, self.group_port)
        self.interf_ip = interface_ip()
        self.group_sock = MixedSocket(AF_INET,SOCK_DGRAM,IPPROTO_UDP)
        #can listen a busy port 
        self.group_sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        self.group_sock.bind((self.interf_ip,self.group_port))
        self.group_sock.join_group(self.group, self.interf_ip)
        self.group_sock.disab_multicast_loop()
        self.priv_port = random_port('H',self.group_port)
        self.private_sock = MixedSocket(AF_INET,SOCK_DGRAM,IPPROTO_UDP)
        self.priv_addr = (self.interf_ip, self.priv_port)
        self.private_sock.bind(self.priv_addr)
        #view collback on message come event
        self.target = kwargs.get('target')
        #key = nickname,  value = private address of peers
        self.peer_addrs = dict()
        #key = nickname, value = history, online mark
        self.peers_info = dict()
        #time to wait reply from peer
        self.reply_time = 3
        self.n_send_attempts = 3
        self.actions = {FrameType.Data : self.handle_data,
                        FrameType.GreetingRequest : self.handle_greeting_reguest,
                        FrameType.GreetingReply : self.handle_greeting_reply,
                        FrameType.Leaving : self.handle_leaving,
                        FrameType.LifeCheckRequest : self.handle_live_check_request, 
                        FrameType.LifeCheckReply : self.handle_live_check_reply} 
                        
        #self.stop_sending_thread_event = threading.Event()  
        #self.frame_sending_thread = threading.Thread(target=self.frame_sending_routine,args=(self.stop_sending_thread_event,))
        self.priv_port_thread = threading.Thread(target=self.)
        self.group_port_thread = threading.Thread()

    def get_priv_port(self, self.target)


    def send_frame_togroup(self,sock,**kwargs):
        sock.send_frame_to(Frame(src_port=self.priv_port, **kwargs), self.group)

    def handle_data(self, frame):
        #skip data
        pass

    def reg_unknown_peer(self,peer):
        if peer not in self.peers:
            self.peers.append(peer)
    
    def stop_sending_thread(self):
        self.stop_sending_thread_event.clear()

    def resume_sending_thread(self):
        self.stop_sending_thread_event.set()

    def handle_live_check_request(self):
        pass

    def handle_live_check_reply(self):
        pass

    def handle_greeting_reguest(self, frame):
        #stop sending data, it overflows udp receive buffer
        self.stop_sending_thread()
        peer = frame.src_addr
        self.reg_unknown_peer(peer)
        #send self peer-list as greeting reply
        #set timeout and listen bus, if enother peer managed first
        reply_after_delay = random.uniform(0, self.max_greeting_reply_time)   
        #listen bus with timeout
        self.group_sock.settimeout(reply_after_delay)
        try:
            self.group_sock.recv_frame_from(type=FrameType.GreetingReply)
        except OSError as e:
            #this host is first-> send peers-list to the private peer socket (frame.data contains private peer socket)
            self.group_sock.send_frame_to(Frame(dst_addr=peer, src_addr=self.host_as_peer, type=FrameType.GreetingReply, data=self.peers+[self.host_as_peer]),(self.group,self.group_port))
        finally:
            self.group_sock.settimeout(None)
        self.resume_sending_thread()

    def handle_greeting_reply(self, frame):
        #get peers-list from other peer 
        self.peers.extend( frame.data )
        #remove self from peer-list
        self.peers.remove(self.host_as_peer)
        #began sending to peers 
        self.resume_sending_thread()


    def handle_leaving(self, frame):
        if peer in self.peers:
            self.peers.remove(frame.src_addr)

         
    def am_i_recepient(self, frame):
        pass

    def offer_new_nickname(self, old_nickname):
        new_nickname = old_nickname
        while self.peer_addrs.get(new_nickname):
           new_nickname += "0"
        return new_nickname 

    def check_nickname(self,nickname):
        attempts = 0
        while attempts < self.n_send_attempts:
           self.private_sock.send_frame_to(Frame(src_port=self.priv_port, type=FrameType.GreetingRequest, data=nickname), self.group_addr)
           #waiting peer list
           self.group_sock.settimeout(self.reply_time)
           try:
               frame, priv_src_addr = self.group_sock.recv_frame_from()
               #success
               self.peer_addrs = frame.data
               if self.peer_addrs.get(nickname):
                   #nickname is not unique, may change it
                   #to offer new nickname
                   return self.offer_new_nickname(nickname)
               break
           except OSError as e:
               attempts += 1
           finally:
               self.group_sock.settimeout(None)
        return "" # alone peer or/and correct nickname





