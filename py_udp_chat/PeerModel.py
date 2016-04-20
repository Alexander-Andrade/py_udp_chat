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


class PeerModel:

    def __init__(self,group,group_port,**kwargs):
        self.group_port = int(group_port)
        self.group = group
        self.group_addr = (self.group, self.group_port)
        self.interf_ip = interface_ip()
        self.group_sock = MixedSocket(AF_INET,SOCK_DGRAM,IPPROTO_UDP)
        self.__group_sock_config()
        self.private_sock = MixedSocket(AF_INET,SOCK_DGRAM,IPPROTO_UDP)
        self.__private_sock_config()
        #view collback on message come event
        self.on_message_come_callback = kwargs.get('on_message_come')
        self.on_peerlist_update_callback = kwargs.get('on_peerlist_update')
        #key = nickname,  value = private address of peers
        self.peer_addrs = dict()
        #key = nickname, value = history, online mark
        self.peers_info = dict()
        self.responded_peers = set()
        self.resp_peers_lock = threading.Lock()
        #time to wait reply from peer
        self.reply_time = 3
        self.n_send_attempts = 3
        self.lighthouse_honks_span = kwargs.get('lighthouse_honks_span', 7)
        self.peer_live_check_span = kwargs.get('peer_live_check_span', 10)
        self.actions = {FrameType.Data : self.handle_data,
                        FrameType.GreetingRequest : self.handle_greeting_reguest,
                        FrameType.GreetingReply : self.handle_greeting_reply,
                        FrameType.Leaving : self.handle_leaving,
                        FrameType.LifeCheckRequest : self.handle_live_check_request, 
                        FrameType.Alive : self.handle_alive_reply} 
                        
        #self.stop_sending_thread_event = threading.Event()  
        #self.frame_sending_thread = threading.Thread(target=self.frame_sending_routine,args=(self.stop_sending_thread_event,))
        self.priv_sock_thread = threading.Thread(target=self.sock_routine)
        self.group_sock_thread = threading.Thread(target=self.sock_routine)
        self.lighthouse_thread = threading.Thread(target=self.lighthouse_honk_routine)
        self.peer_alive_check_thread = threading.Thread(target=self.peer_alive_check_routine)

    def __group_sock_config(self):
        #can listen a busy port 
        self.group_sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        self.group_sock.bind((self.interf_ip,self.group_port))
        self.group_sock.join_group(self.group, self.interf_ip)
        self.group_sock.disab_multicast_loop()

    def __private_sock_config(self):
        #let to chose free port
        self.private_sock.bind((self.interf_ip, 0))
        self.priv_addr = self.private_sock.getsockname()
        self.priv_port = self.priv_addr[1]

  
    def peer_alive_check_routine(self):
        while True:
            self.resp_peers_lock.acquire()
            self.peer_addrs = [peer for peer in self.peer_addrs if peer in self.responded_peers]   
            self.on_peerlist_update_callback(self.peer_addrs, self.peers_info)
            self.resp_peers_lock.release()
            time.sleep(self.peer_live_check_span)
            
    def sock_routine(self):
        while True:
            frame,addr = self.private_sock.recv_frame_from()
            self.resp_peers_lock.acquire()
            self.responded_peers.add(addr)
            self.resp_peers_lock.release()
            self.actions[frame.type](frame) 


    def lighthouse_honk_routine(self):
        while True:
            self.group_sock.send_frame_to(Frame(type=FrameType.Alive), self.group_addr)
            time.sleep(self.lighthouse_honks_span)

    def handle_data(self, frame):
        #transfer data to view
        self.on_message_come_callback(frame.data)

    def reg_unknown_peer(self,peer):
        if peer not in self.peers:
            self.peers.append(peer)
    
    def stop_sending_thread(self):
        self.stop_sending_thread_event.clear()

    def resume_sending_thread(self):
        self.stop_sending_thread_event.set()

    def handle_live_check_request(self):
        pass

    def handle_alive_reply(self):
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
            self.group_sock.send_frame_to(Frame(dst_addr=peer, src_addr=self.host_as_peer, type=FrameType.GreetingReply, data=self.peers+[self.host_as_peer]),self.group_addr)
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
           self.private_sock.send_frame_to(Frame(type=FrameType.GreetingRequest, data=nickname), self.group_addr)
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


    def join_group(self):
        self.priv_sock_thread.start()
        self.group_sock_thread.start()
        self.lighthouse_thread.start()
        self.peer_alive_check_thread.start()


                                     