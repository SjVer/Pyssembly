from ctypes import c_ubyte as cbyte
from enum import Enum
import sys
from typing import Callable

def ln(): return sys._getframe().f_back.f_lineno

class Chunk:
    def __init__(self):
        self.size: int = 0
        self.bytes: list[cbyte] = []

    def write(self, byte: cbyte):
        # if not isinstance(byte, cbyte):
            # raise ValueError(
                # "Chunk.write() takes a cbyte, not a " + str(type(byte)))
        self.size += 1
        self.bytes.append(byte)

class Ins:#truction
    def __init__(self, byte: cbyte, *args):
        self.byte = cbyte(byte)
        # list with arg types
        self.args = args
        self.argc = len(args)

class Instruct(Enum):
    NOI  = Ins(0)
    PUSH = Ins(1)
    POP  = Ins(2)
    LOAD = Ins(3, float)
    ADD  = Ins(4)
    SUB  = Ins(5)
    MUL  = Ins(6)
    DIV  = Ins(7)
    NEG  = Ins(8)
    INPT = Ins(9)
    PRNT = Ins(10)
    PRNC = Ins(11)
    CMP  = Ins(12)
    JMP  = Ins(13, int)
    JMIF = Ins(14, int)
    CALL = Ins(15, int)
    CAIF = Ins(16, int)
    RET  = Ins(17)
    INC  = Ins(18)
    DEC  = Ins(19)
    PUSB = Ins(20, int)
    GETB = Ins(21, int)
    KILL = Ins(66)

def geninstructdict():
    ret = {}
    for op in Instruct:
        ret['_'+str(op.value.byte.value)] = op.name
    print('{')
    for op in ret:
        print('\t\''+op+'\': '+ret[op]+',')
    print('}')
if __name__ == "__main__":
    geninstructdict()