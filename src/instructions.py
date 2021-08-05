from bitsnbytes import Byte
from enum import Enum
from typing import List

from inspect import currentframe

def ln(offset=0): return currentframe().f_back.f_lineno - offset

def checkAddress(self, dest: int): return dest in range(len(self.bytes))

def OP_NOI(self):
    return
def OP_PUSH(self):
    self.push()
    if self.debug: print('│ >>> pushing',self.a)
def OP_POP(self):
    self.pop()
    if self.debug: print('│ >>> popping',self.a)
def OP_LOAD(self):
    self.ic += 1
    self.a = self.get_constant(self.ip.to_int())
    if self.debug: print('│ >>> loading',self.a,'from constant pool')
def OP_LODA(self):
    self.ic += 1
    ptr = self.get_constant(self.ip.to_int())
    if self.debug:
        arr = self.get_array(ptr)
        print('│ >>> loaded array',arr,'with pointer',ptr)
    self.a = ptr

def OP_ADD(self):
    self.pop()
    a = self.a
    self.pop()
    b = self.a
    self.a = a + b
    if self.debug: print('│ >>> adding',a,'and',b)
def OP_SUB(self):
    self.pop()
    a = self.a
    self.pop()
    b = self.a
    self.a = a - b
    if self.debug: print('│ >>> subtracting',a,'and',b)
def OP_MUL(self):
    self.pop()
    a = self.a
    self.pop()
    b = self.a
    self.a = a * b
    if self.debug: print('│ >>> multiplying',a,'by',b)
def OP_DIV(self):
    self.pop()
    a = self.a
    self.pop()
    b = self.a
    self.a = a / b
    if self.debug: print('│ >>> dividing',a,'by',b)
def OP_NEG(self):
    if self.debug: print('│ >>> negating',self.a)
    self.a = -self.a

def OP_INPT(self):
    inp = input()
    try: value = float(inp)
    except ValueError: value = 0
    self.a = value
    if self.debug: print('│ >>> read input',self.a)
def OP_PRNT(self):
    if self.debug: print('│ >>> printing',self.a)
    return str(int(self.a) if int(self.a) == self.a else self.a)
def OP_PRNC(self):
    if self.debug: print('│ >>> printing character')
    return chr(int(self.a))
def OP_PRNA(self):
    # ptr = self.a
    arr = self.get_array(self.a)
    if self.debug: print('│ >>> printing array',arr)
    return '{'+str(arr)[1:-1].replace(' ','')+'}'
def OP_PRNS(self):
    arr = self.get_array(self.a)
    string = ''.join([chr(x) for x in arr])
    if self.debug: print('│ >>> printing string',string)
    return string

def OP_CMP(self):
    self.f = self.a == self.stack[-1]
    if self.debug:
            print('│ >>> comparing',self.a,'with',self.stack[-1])
def OP_JMP(self):
    self.ic += 1
    dest = self.get_constant(self.ip.to_int())
    if not checkAddress(self, dest):
        return("RuntimeError: Jump to address "+str(dest)+" failed")
    else:
        if self.debug: print('│ >>> jumping to address',dest)
        self.ic = dest-1
def OP_JMIF(self):
    self.ic += 1
    dest = self.get_constant(self.ip.to_int())
    # self.ic += 1
    if not self.f:
        if self.debug:
            print('│ >>> not jumping to address', dest)
        return
    if not checkAddress(self, dest):
        return("RuntimeError: Jump to address "+str(dest)+" failed")
    else:
        if self.debug: print('│ >>> jumping to address',dest)
        self.ic = dest-1
def OP_JIFN(self):
    self.ic += 1
    dest = self.get_constant(self.ip.to_int())
    # self.ic += 1
    if self.f:
        if self.debug:
            print('│ >>> not jumping to address', dest)
        return
    if not checkAddress(self, dest):
        return("RuntimeError: Jump to address "+str(dest)+" failed")
    else:
        if self.debug: print('│ >>> jumping to address',dest)
        self.ic = dest-1
def OP_CALL(self):
    self.ic += 1
    dest = self.get_constant(self.ip.to_int())
    # self.ic += 1
    if not checkAddress(self, dest):
        return("RuntimeError: Call to address "+str(dest)+" failed")
    else:
        if self.debug: print('│ >>> jumping to address',dest)
        self.push_ret(self.ic)
        self.ic = dest-1
def OP_CAIF(self):
    self.ic += 1
    dest = self.get_constant(self.ip.to_int())
    # self.ic += 1
    if not self.f:
        if self.debug:
            print('│ >>> not calling address',dest)
        return
    if not checkAddress(self, dest):
        return("RuntimeError: Call to address "+str(dest)+" failed")
    else:
        if self.debug: print('│ >>> calling address',dest)
        self.ret_push(self.ic)
        self.ic = dest-1
def OP_CIFN(self):
    self.ic += 1
    dest = self.get_constant(self.ip.to_int())
    # self.ic += 1
    if self.f:
        if self.debug:
            print('│ >>> not calling address',dest)
        return
    if not checkAddress(self, dest):
        return("RuntimeError: Call to address "+str(dest)+" failed")
    else:
        if self.debug: print('│ >>> calling address',dest)
        self.ret_push(self.ic)
        self.ic = dest-1
def OP_RET(self):
    dest = self.pop_ret()
    if not checkAddress(self, dest):
        return("RuntimeError: Return to address "+str(dest)+" failed")
    else:
        if self.debug: print('│ >>> returning to address',dest+1)
        self.ic = dest

def OP_INC(self):
    self.a += 1
    if self.debug: print('│ >>> incrementing')
def OP_DEC(self):
    self.a -= 1 if self.a > 0 else 0
    if self.debug: print('│ >>> decrementing')
def OP_PUSB(self):
    self.ic += 1
    dest = int(self.get_constant(self.ip.to_int()))
    if not checkAddress(self, dest):
        return("RuntimeError: Push byte to address "+str(dest)+" failed")
    else:
        # print(int(self.a))
        if not (int(self.a) >= 0x00 and int(self.a) <= 0xff):
            return("RuntimeError: Push byte to address "+str(int(self.a))+' failed')

        if self.debug:
            print('│ >>> pushing byte', Byte(self.a).to_hex(),'to', dest)
                
        self.bytes[dest] = Byte(int(self.a))
        if self.address_to_pixel(dest):
            row, column = self.address_to_pixel(dest)
            self.prunepixel(row, column)
def OP_GETB(self):
    self.ic += 1
    dest = self.get_constant(self.ip.to_int())
    if not checkAddress(self, dest):
        return("RuntimeError: Get byte from address "+str(dest)+" failed")
    else:
        self.a = self.bytes[dest-1].to_int()
    if self.debug: print('│ >>> getting byte', self.a,'from', dest)

def OP_NVAR(self):
    self.ic += 1
    varname = self.get_constant(self.ip.to_int(), False)
    # self.ic -= 1
    # print('nvar',varname)
    if self.debug: print('│ >>> creating new variable',varname)
    self.hashtable.insert(varname, 0)
def OP_DVAR(self):
    self.ic += 1
    varname = self.get_constant(self.ip.to_int(), False)
    # self.ic -= 1
    # print('dvar',varname)
    if self.debug: print('│ >>> deleting variable',varname)
    self.hashtable.remove(varname)
def OP_PUVA(self):
    self.ic += 1
    varname = self.get_constant(self.ip.to_int(), False)
    # self.ic -= 1
    # print('puva',varname)
    if self.debug: print('│ >>> pushing',self.a,'to variable',varname)
    self.hashtable.replace(varname, self.a)
def OP_LOVA(self):
    self.ic += 1
    varname = self.get_constant(self.ip.to_int(), False)
    # self.ic -= 1
    # print('lova',varname)
    self.a = self.hashtable.find(varname)
    if self.debug: print('│ >>> loading',self.a,'from variable',varname)
def OP_INCV(self):
    self.ic += 1
    varname = self.get_constant(self.ip.to_int(), False)
    if self.debug: print('│ >>> incrementing variable',varname)
    self.hashtable.replace(varname, self.hashtable.find(varname)+1)
def OP_DECV(self):
    self.ic += 1
    varname = self.get_constant(self.ip.to_int(), False)
    if self.debug: print('│ >>> decrementing variable',varname)
    self.hashtable.replace(varname, self.hashtable.find(varname)-1)

def OP_POLL(self):
    self.poll()
    if self.debug: print('│ >>> polling')
def OP_WAIT(self):
    self.ic += 1
    sec = self.get_constant(self.ip.to_int())
    if self.debug: print('│ >>> sleeping for',sec,'seconds')
    return ["sleep", sec]
def OP_KILL(self):
    self.bytes[0] = Byte(0)
    if self.debug: print('│ >>> killing')

class Ins:#truction
    def __init__(self, byte: Byte, offset_sensitive, *args):  # Byte, *args):
        # self.byte = Byte(byte)
        self.byte = Byte(byte)
        # list with arg types
        self.args = args
        self.argc = len(args)
        self.offset_sensitive = offset_sensitive

sln = ln()+3
class Instruct(Enum):
    NOI     = Ins(ln(sln-1),   False)
    # stack
    PUSH    = Ins(ln(sln+0),   False)
    POP     = Ins(ln(sln+0),   False)
    LOAD    = Ins(ln(sln+0),   False, float)
    LODA    = Ins(ln(sln+0),   False, list)
    # arithmetic
    ADD     = Ins(ln(sln+1),   False)
    SUB     = Ins(ln(sln+1),   False)
    MUL     = Ins(ln(sln+1),   False)
    DIV     = Ins(ln(sln+1),   False)
    NEG     = Ins(ln(sln+1),   False)
    # io
    INPT    = Ins(ln(sln+2),   False)
    PRNT    = Ins(ln(sln+2),   False)
    PRNC    = Ins(ln(sln+2),   False)
    PRNS    = Ins(ln(sln+2),   False)
    PRNA    = Ins(ln(sln+2),   False)
    # control flow
    CMP     = Ins(ln(sln+3),   False)
    JMP     = Ins(ln(sln+3),   True,  int)
    JMIF    = Ins(ln(sln+3),   True,  int)
    JIFN    = Ins(ln(sln+3),   True,  int)
    CALL    = Ins(ln(sln+3),   True,  int)
    CAIF    = Ins(ln(sln+3),   True,  int)
    CIFN    = Ins(ln(sln+3),   True,  int)
    RET     = Ins(ln(sln+3),   False)
    # register manipulation
    INC     = Ins(ln(sln+4),   False)
    DEC     = Ins(ln(sln+4),   False)
    # byte manipulation
    PUSB    = Ins(ln(sln+5),   True,  int)
    GETB    = Ins(ln(sln+5),   True,  int)
    # variable
    NVAR    = Ins(ln(sln+6),   False, id)
    DVAR    = Ins(ln(sln+6),   False, id)
    PUVA    = Ins(ln(sln+6),   False, id)
    LOVA    = Ins(ln(sln+6),   False, id)
    INCV    = Ins(ln(sln+6),   False, id)
    DECV    = Ins(ln(sln+6),   False, id)
    # misc.
    WAIT    = Ins(ln(sln+7),   False, float)
    POLL    = Ins(ln(sln+7),   False)
    KILL    = Ins(ln(sln+7),   False)

def getinstruct(byteval: int):
    for instruct in Instruct:
        if instruct.value.byte == byteval:
            return instruct
    return False

# print('\n'.join([op.name +' '+str(op.value.byte.to_int()) for op in Instruct]))
