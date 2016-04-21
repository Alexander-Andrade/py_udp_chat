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
        self.nickname = ''
        self.peers = dict()
        self.responded_peers = set()
        self.resp_peers_lock = threading.Lock()
        self.peers_lock = threading.Lock()
        #time to wait reply from peer
        self.reply_time = 3
        self.n_send_attempts = 3
        self.lighthouse_honks_span = kwargs.get('lighthouse_honks_span', 7)
        self.peer_live_check_span = kwargs.get('peer_live_check_span', 10)
        self.actions = {FrameType.Data : self.handle_data,
                        FrameType.GreetingRequest : self.handle_greeting_reguest,
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
            print('peer check pending...')
            if set(self.peers.keys()) != self.responded_peers:
                self.peers_lock.acquire()
                self.peers = dict(peer for peer in self.peers if peer[0] in self.responded_peers)   
                self.peers_lock.release()
                self.on_peerlist_update_callback(self.peers)
                self.resp_peers_lock.acquire()
                self.responded_peers.clear()
                self.resp_peers_lock.release()
            time.sleep(self.peer_live_check_span)
            
    def sock_routine(self):
        while True:
            frame,addr = self.private_sock.recv_frame_from()
            self.resp_peers_lock.acquire()
            self.responded_peers.add(addr)
            self.resp_peers_lock.release()
            self.actions[frame.type](frame, addr) 

    def registrate_new_peer(self, frame, addr):
        nickname = frame.data
        self.peers[addr] = nickname

    def lighthouse_honk_routine(self):
        while True:
            self.group_sock.send_frame_to(Frame(type=FrameType.Alive), self.group_addr)
            time.sleep(self.lighthouse_honks_span)

    def handle_data(self, frame, addr):
        nickname = self.peers.get(addr)
        self.on_message_come_callback(frame.data, addr, nickname)

    def handle_live_check_request(self, frame, addr):
        pass

    def handle_alive_reply(self, frame, addr):
        pass

    def handle_greeting_reguest(self, frame, addr):
        self.registrate_new_peer(frame, addr)
        #send self peer-list as greeting reply
        #set timeout and listen bus, if enother peer managed first
        reply_after_delay = random.uniform(0, self.reply_time)   
        #listen bus with timeout
        self.group_sock.settimeout(reply_after_delay)
        try:
            self.group_sock.recv_frame_from(type=FrameType.GreetingReply)
        except OSError as e:
            peers_with_itself = self.peers.copy()
            peers_with_itself.update({self.priv_addr : self.nick})
            self.group_sock.send_frame_to(Frame(type=FrameType.GreetingReply, data=peers_with_itself), self.group_addr)
        finally:
            self.group_sock.settimeout(None)
        

    def handle_leaving(self, frame, addr):
        self.peers_lock.acquire()
        self.peers.pop(addr, None)
        self.peera_lock.release()
        self.on_peerlist_update_callback(self.peers)

    def set_nickname(self, chose_nickname_dial_callback):
        self.peers = self.get_peers_dict()
        nicknames= list(self.peers.values())
        proposed_nickname = ''
        while True:
            chosen_nickname = chose_nickname_dial_callback(proposed_nickname)
            if chosen_nickname in nicknames:     
                proposed_nickname = chosen_nickname + '0'
            else:
                self.nickname = chosen_nickname
                break
           
    def get_peers_dict(self):
        attempts = 0
        while attempts < self.n_send_attempts:
           self.private_sock.send_frame_to(Frame(type=FrameType.GreetingRequest, data=nickname), self.group_addr)
           #waiting peer list
           self.group_sock.settimeout(self.reply_time)
           try:
               frame, addr = self.group_sock.recv_frame_from(type=FrameType.GreetingReply)
               #success
               return frame.data
           except OSError as e:
               attempts += 1
           finally:
               self.group_sock.settimeout(None)
        return dict()

    def join_group(self):
        self.priv_sock_thread.start()
        self.group_sock_thread.start()
        self.lighthouse_thread.start()
        self.peer_alive_check_thread.start()


                                     