import struct
from enum import Enum, unique
#type of service message
@unique
class MsgTOS(Enum):
    Data = 0
    Identification = 1
    PeersList = 2

class Packet:
   
    def __init__(self,**kwargs):
        #type of service message
        self.msg_tos = kwargs.get('tos',MsgTOS.Data)
        self.data = kwargs.get('data',b'')
        self.packet = kwargs.get('packet',b'')


    def pack(self):
        self.packet = struct.pack('B',self.msg_tos.value) + self.data
        return self.packet

    def unpack(self):
        self.data =  self.packet[1:]
        tos_size = struct.calcsize('B')
        self.msg_tos = MsgTOS(struct.unpack('B',self.packet[0:tos_size])[0])
        return (self.msg_tos,self.data)



