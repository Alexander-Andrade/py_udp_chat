import sys
from PeerModel import PeerModel

def on_msg_come(frame):
    print(frame)

def on_peerlist_update(peer_addrs, peer_info):
    print(peer_addrs)

if __name__ == '__main__':
   peer_model = PeerModel(sys.argv[1], sys.argv[2],on_message_come = on_msg_come, on_peerlist_update=on_peerlist_update) 
   peer_model.check_nickname('rufus')
   peer_model.join_group()
