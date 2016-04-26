import sys
from tkinter import*
import tkinter.ttk as ttk    #ovveride tkinter widgets
from PeerModel import PeerModel
from PeerView import PeerView, NicknameDial
from PeerInfo import PeerInfo

def get_nickname_from_dial(proposed_nickname):
    nick_dial = NicknameDial(text=proposed_nickname)
    return nick_dial.nickname

if __name__ == '__main__':
    root = Tk()
    peer_model = PeerModel(sys.argv[1], sys.argv[2], reply_time=1,
                           peer_live_check_span=10, lighthouse_honks_span=7)
    peer_view = PeerView(master=root, peer_model=peer_model)
    peer_model.on_message_come_callback = peer_view.on_msg_come
    peer_model.on_peerset_update_callback = peer_view.on_peerlist_update
    peer_model.set_nickname(get_nickname_from_dial)
    peer_model.join_group()  
    peer_view.master.geometry('800x600')
    peer_view.show_own_nickname()
    peer_view.mainloop()
    
    

  