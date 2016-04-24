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
        self.on_peerset_update_callback = kwargs.get('on_peerlist_update')
        self.nickname = ''
        self.peers = dict()
        self.responded_peers = set()
        self.resp_peers_lock = threading.RLock()
        self.peers_lock = threading.RLock()
        self.peer_update_lock = threading.RLock()
        #time to wait reply from peer
        self.reply_time = kwargs.get('reply_time',3)
        self.n_send_attempts = kwargs.get('n_send_attempts',3)
        self.lighthouse_honks_span = kwargs.get('lighthouse_honks_span', 7)
        self.peer_live_check_span = kwargs.get('peer_live_check_span', 10)
        self.actions = {FrameType.Data : self.handle_data,
                        FrameType.GreetingRequest : self.handle_greeting_reguest,
                        FrameType.GreetingReply : self.handle_greeting_reply,
                        FrameType.Nickname : self.hanlde_nickname_reply,
                        FrameType.Leaving : self.handle_leaving,
                        FrameType.LifeCheckRequest : self.handle_live_check_request, 
                        FrameType.Alive : self.handle_alive_reply} 
                        
        #self.stop_sending_thread_event = threading.Event()  
        #self.frame_sending_thread = threading.Thread(target=self.frame_sending_routine,args=(self.stop_sending_thread_event,))
        self.priv_sock_thread = threading.Thread(target=self.sock_routine, args=(self.private_sock,))
        self.group_sock_thread = threading.Thread(target=self.sock_routine, args=(self.group_sock,))
        self.lighthouse_thread = threading.Thread(target=self.lighthouse_honk_routine)
        self.peer_alive_check_thread = threading.Thread(target=self.peer_alive_check_routine)

    def __group_sock_config(self):
        #can listen a busy port 
        self.group_sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
        self.group_sock.bind((self.interf_ip,self.group_port))
        self.group_sock.join_group(self.group, self.interf_ip)
        #self.group_sock.disab_multicast_loop()

    def __private_sock_config(self):
        #let to chose free port
        self.private_sock.bind((self.interf_ip, 0))
        self.priv_addr = self.private_sock.getsockname()
        self.priv_port = self.priv_addr[1]

  
    def __force_to_live_sygnals(self, peers_addrs):
        for peer_addr in peers_addrs:
            self.private_sock.send_frame_to(Frame(type=FrameType.LifeCheckRequest), peer_addr, lock_fl=True)

    def __safely_find_silent_peers(self, peers_addrs):
        with self.resp_peers_lock, self.peers_lock:
            return peers_addrs.difference(self.responded_peers)

    def __safely_del_silent_peers(self, silent_peers_addrs):
        with self.peers_lock:
            for silent_peer_addr in silent_peers_addrs:
                        del self.peers[silent_peer_addr]

    def __safely_update_peerlist(self):
        with self.peer_update_lock:
            self.on_peerset_update_callback(set(self.peers.values()))

    def peer_alive_check_routine(self):
        peers_addrs = set()
        silent_peers_addrs = set()
        while True:
            time.sleep(self.peer_live_check_span)
            with self.peers_lock:
                peers_addrs = set(self.peers.keys())
            if not peers_addrs.issubset(self.responded_peers):
                silent_peers_addrs = self.__safely_find_silent_peers(peers_addrs)
                self.__force_to_live_sygnals(silent_peers_addrs)
                time.sleep(self.reply_time)
                silent_peers_addrs = self.__safely_find_silent_peers(peers_addrs)
                print('{} leaved silently'.format(silent_peers_addrs))
                self.__safely_del_silent_peers(silent_peers_addrs)
                self.__safely_update_peerlist()
            with self.resp_peers_lock:
                self.responded_peers.clear()
           
            
    def isFrameFilteredByAddr(self, addr, frame):
        #not to get frames from yourself
        return addr == self.priv_addr 

    def sock_routine(self, sock):
        print('sock routine started', flush=True)
        while True:
            frame,addr = sock.recv_frame_from()
            if not self.isFrameFilteredByAddr(addr, frame):
                print('{} -> {}'.format(addr, frame))
                with self.resp_peers_lock:
                    self.responded_peers.add(addr)
                self.actions[frame.type](frame, addr) 

    def lighthouse_honk_routine(self):
        while True:
            self.private_sock.send_frame_to(Frame(type=FrameType.Alive), self.group_addr, lock_fl=True)
            time.sleep(self.lighthouse_honks_span)



    def handle_data(self, frame, addr):
        nickname = self.peers.get(addr)
        with self.peer_update_lock:
            self.on_message_come_callback(frame.data, nickname)

    def handle_greeting_reply(self, frame, addr):
        pass

    def handle_live_check_request(self, frame, addr):
        self.private_sock.send_frame_to(Frame(type=FrameType.Alive), self.group_addr, lock_fl=True)

    def handle_alive_reply(self, frame, addr):
        #it handles upper
        pass

    def handle_greeting_reguest(self, frame, addr):
        #send self peer-list as greeting reply
        #set timeout and listen bus, if enother peer managed first
        reply_after_delay = random.uniform(0, self.reply_time)   
        #listen bus with timeout
        self.group_sock.settimeout(reply_after_delay)
        try:
            self.group_sock.recv_frame_from(type=FrameType.GreetingReply)
        except OSError as e:
            peers_with_itself = self.peers.copy()
            peers_with_itself.update({self.priv_addr : self.nickname})
            self.private_sock.send_frame_to(Frame(type=FrameType.GreetingReply, data=peers_with_itself), self.group_addr, lock_fl=True)
        finally:
            self.group_sock.settimeout(None)
        
    def registrate_peer(self, addr, nickname):
        with self.peers_lock:
            self.peers[addr] = nickname

    def hanlde_nickname_reply(self, frame, addr):
        self.registrate_peer(addr, frame.data)
        self.__safely_update_peerlist()

    def handle_leaving(self, frame, addr):
        self.peers.pop(addr, None)
        self.__safely_update_peerlist()




    def set_nickname(self, chose_nickname_dial_callback):
        self.peers = self.get_peers_dict()
        nicknames= set(self.peers.values())
        self.on_peerset_update_callback(nicknames)
        proposed_nickname = ''
        while True:       
            chosen_nickname = chose_nickname_dial_callback(proposed_nickname)
            if chosen_nickname in nicknames:     
                proposed_nickname = chosen_nickname + '0'
            else:
                self.nickname = chosen_nickname
                print('nickname : {}'.format(self.nickname))
                self.private_sock.send_frame_to(Frame(type=FrameType.Nickname, data=self.nickname), self.group_addr)
                break
           
    def get_peers_dict(self):
        attempts = 0
        while attempts < self.n_send_attempts:
           self.private_sock.send_frame_to(Frame(type=FrameType.GreetingRequest), self.group_addr)
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

    def __find_peeraddr_by_nick(self,nickname):
        for addr,nick in self.peers.items():
            if nick == nickname:
                return addr

    def send_message(self, message, nickname):
        addr = self.__find_peeraddr_by_nick(nickname) if nickname else self.group_addr
        self.private_sock.send_frame_to(Frame(type=FrameType.Data, data=message), addr, lock_fl=True)



    def join_group(self):
        self.priv_sock_thread.start()
        self.group_sock_thread.start()
        self.lighthouse_thread.start()
        self.peer_alive_check_thread.start()


                                     