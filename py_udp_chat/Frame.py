import struct
from FrameType import*
import pickle
from socket import*


class Frame:
    #frame: type(B),src_port(H),data(var_len)
    def __init__(self,**kwargs):
        self.frame = kwargs.get('frame',b'')
        if self.frame != b'':
            self.unpack()
        else:
            self.type = kwargs.get('type',FrameType.Data)
            self.src_port = kwargs.get('src_port')
            if not self.src_port: raise ValueError('src_port was not provided')
            self.data = kwargs.get('data',b'')
            
    def pack(self):
        self.frame = struct.pack('!BH', self.type.value, self.src_port)
        if self.data:
            self.frame += pickle.dumps(self.data)
        return self.frame
         
    def unpack(self, frame=None):
        if frame:
            self.frame = frame
        header_size = struct.calcsize('!BH')
        type_val, self.src_port = struct.unpack('!BH',self.frame[:header_size])
        self.type = FrameType(type_val)
        bytes_data = self.frame[header_size:]
        if len(bytes_data):
            self.data = pickle.loads(bytes_data)
        return(self.type, self.src_port, self.data)

    def __repr__(self):
            return 'Frame (type={}, src_port={},data={})'.format(self.type, self.src_port, self.data)

    def __bytes__(self):
        return self.frame if self.frame != b'' else self.pack()

    

    
        
    