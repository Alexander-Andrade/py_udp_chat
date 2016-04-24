from tkinter import*
import tkinter.ttk as ttk    #ovveride tkinter widgets
from PeerModel import PeerModel
from PeerInfo import PeerInfo

class NicknameDial(Toplevel):

    def __init__(self, **kwargs):
        super().__init__()
        self.nickname = kwargs.get('text','')
        #widgets for dialogues
        self.geometry('200x70')
        self.nick_entry = ttk.Entry(self)
        self.nick_entry.insert(0,self.nickname)
        self.nick_entry.pack()
        self.nick_entry.focus_set()
        #self.transient()
         #set all events to dial
        self.grab_set()   
        self.nick_label = ttk.Label(self,text='nickname',font='Arial 8')
        self.nick_label.pack()
        self.apply_btn = ttk.Button(self, text='Apply', command=self.on_apply_btn_press)
        self.apply_btn.pack()
        self.protocol('WM_DELETE_WINDOW', self.__close_dial)
        self.bind('<Return>', self.on_apply_btn_press)
        self.wait_window(self)

    def __close_dial(self):
        self.destroy()
        self.quit()

    def on_apply_btn_press(self, event=None):
        self.nickname = self.nick_entry.get()
        self.__close_dial()
        


class PeerView(ttk.Frame):

    def __init__(self, master, peer_model):
        super().__init__(master);
        self.pack(fill=BOTH, expand=YES)
        #model
        self.peer_model = peer_model
        #list of the peers
        self.__config_peer_listview()
        self.__config_msf_frame()
        #current nick
        self.selected_peer_nick = ''
        self.peers_dict = dict()
        self.__init_peer_dict()

    def __init_peer_dict(self):
        self.peers_dict['group'] = PeerInfo()

    def show_own_nickname(self):
        self.master.title(self.peer_model.nickname)

    def __config_peer_listview(self):
        self.peers_listview = ttk.Treeview(self, selectmode="extended", columns=('nickname','online'))
        self.peers_listview.column('#0',stretch=NO,width=0)
        self.peers_listview.column('nickname',stretch=YES, width=100)
        self.peers_listview.heading('nickname', text='nickname')
        self.peers_listview.column('online',stretch=YES, width=100)
        self.peers_listview.heading('online', text='online')
        self.peers_listview.pack(side='right', fill=BOTH, expand=YES)
        self.peers_listview.bind('<Double-1>',self.on_peer_listview_click)

    def __config_msf_frame(self):
        #frame to view and edit mesages
        self.msg_frame = ttk.Frame(self)
        self.peer_history = Text(self.msg_frame, height=20, font='times 12', wrap=WORD)
        #read only (history)
        #!!!switch to -> config(state=NORMAL) to modify through delete(), insert()
        self.peer_history.config(state=DISABLED)
        self.msg_text = Text(self.msg_frame, font='times 12', wrap=WORD)
        self.send_btn = ttk.Button(self.msg_frame, text='send', command=self.on_msg_send)
        self.send_btn.pack(side='bottom',fill=X,expand=YES)
        self.peer_history.pack(side='top', expand=YES,fill=BOTH)
        self.msg_text.pack(expand=YES,fill=BOTH)
        self.msg_frame.pack(side='left', fill=BOTH, expand=YES)

    def get_sending_string(self):
        return self.msg_text.get(1.0, END)

    def clr_msg_text(self):
        self.msg_text.delete(1.0, END)

    def replace_history(self,new_hist_str):
        old_history_str = self.peer_history.get(1.0, END)
        #allow to modify history
        self.peer_history.config(state = NORMAL)
        self.peer_history.delete(1.0, END)
        self.peer_history.insert(END, new_hist_str)
        #deny to modify history
        self.peer_history.config(state = DISABLED)
        return old_history_str

    def update_history(self,new_msg):
        self.peer_history.config(state = NORMAL)
        self.peer_history.insert(END,new_msg)
        self.peer_history.config(state = DISABLED)
        #return updated history string
        return self.peer_history.get(1.0, END)
      
    def switch_to_current_history(self, nickname):
        cur_hist = self.peers_dict[self.selected_peer_nick].history
        self.replace_history(cur_hist)
     
    def __add_peer_to_listview(self,peer_nick):
        self.peers_listview.insert('','end',values=(peer_nick,'online'))
        self.peers_listview.update()

    def on_peer_listview_click(self,event):
        #get selected row (peer)
        item = self.peers_listview.identify('item',event.x ,event.y)
        print('click on item {}'.format(self.peers_listview.item(item,'values')))
        try:
            self.selected_peer_nick = self.peers_listview.item(item,'values')[0]
            #show his history
            self.switch_to_current_history()
        except IndexError as e:
            pass
      
    '''
    def del_peer_from_listview(self,peer_nick):
        for item in self.peers_listview.get_children():
            if(self.peers_listview.item(item, 'values')[0] == peer_nick):
                self.peers_listview.delete(item)
                self.peers_listview.update()
                break
    '''
    def on_msg_send(self):
        msg = self.get_sending_string()
        self.clr_msg_text()
        #save msg to history
        self.peers_dict[self.selected_peer_nick].history += '{} <- {}'.format(self.selected_peer_nick, msg) 
        self.replace_history(self.peers_dict[self.selected_peer_nick].history)
        self.peer_model.send_message(msg, self.selected_peer_nick)

    def on_msg_come(self, message, nickname):
        self.peers_dict[nickname].history += '{} -> {}'.format(message, nickname)

    def __clear_listview(self):
        #tree.delete(*tree.get_children())
        for peer in self.peers_listview.get_children():
            self.peers_listview.delete(peer)    

    def __update_peers_listview(self, new_nicknames):
        for item in self.peers_listview.get_children():
            view_peer_info = self.peers_listview.item(item, 'values')
            #is online col
            view_peer_info[1] = 'online' if self.peers_dict[view_peer_info[0]] == True else 'offline'
        for new_nick in new_nicknames:
            self.peers_listview.insert('','end',values=(new_nick,'online'))
        self.peers_listview.update()

    def __update_peers_dict(self, nicknames_online, new_nicknames):
        #set presence flag in old peers
        for nickname, peer_info in self.peers_dict.items():
           peer_info.is_online = (nickname in nicknames_online)
        #add new peers
        for nickname in new_nicknames:
            self.peers_dict[nickname] = PeerInfo

    def on_peerlist_update(self, nicknames_online):
        new_nicknames = nicknames_online.difference(set(self.peers_dict.values()))
        self.__update_peers_dict(nicknames_online, new_nicknames)
        self.__update_peers_listview(new_nicknames)
