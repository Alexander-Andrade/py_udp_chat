import struct
from FrameType import*
import pickle
from socket import*


class Frame:
    #frame: type(B), data(var_len)
    def __init__(self,**kwargs):
        self.frame = kwargs.get('frame',b'')
        if self.frame != b'':
            self.unpack()
        else:
            self.type = kwargs.get('type',FrameType.Data)
            self.data = kwargs.get('data',b'')
            
    def pack(self):
        self.frame = struct.pack('!B', self.type.value)
        if self.data:
            self.frame += pickle.dumps(self.data)
        return self.frame
         
    def unpack(self, frame=None):
        if frame:
            self.frame = frame
        header_size = struct.calcsize('!B')
        type_val= struct.unpack('!B',self.frame[:header_size])
        self.type = FrameType(type_val)
        bytes_data = self.frame[header_size:]
        if len(bytes_data):
            self.data = pickle.loads(bytes_data)
        return(self.type, self.data)

    def __repr__(self):
            return 'Frame (type={}, data={})'.format(self.type, self.data)

    def __bytes__(self):
        return self.frame if self.frame != b'' else self.pack()

    

    
        
    