from enum import Enum,unique

@unique
class FrameType(Enum):
    Data = 0
    GreetingRequest = 1
    GreetingReply = 2
    Nickname = 3
    Leaving = 4
    LifeCheckRequest = 5
    Alive = 6