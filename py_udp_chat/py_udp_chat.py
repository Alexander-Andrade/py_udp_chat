import sys
from PeerModel import PeerModel

def on_msg_come(frame, addr, nickname):
    print(frame)

def on_peerlist_update(peer_addrs):
    print('update list')
    

if __name__ == '__main__':
   '''
   peer_model = PeerModel(sys.argv[1], 
                          sys.argv[2],on_message_come = on_msg_come, on_peerlist_update=on_peerlist_update,
                          peer_live_check_span=1
                          ) 
   peer_model.check_nickname('rufus')
   peer_model.join_group()
   peer_model.responded_peers.add(10)
   peer_model.group_sock_thread.join()
   
   
   '''

   d = dict()
   d['q'] = 6
   dd = (d.copy())
   dd.update({'v':7})
   print(dd)


  