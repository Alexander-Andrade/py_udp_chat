import sys
from PeerModel import PeerModel


if __name__ == '__main__':
   peer_model = PeerModel(sys.argv[1], sys.argv[2]) 
   peer_model.check_nickname('rufus')
    