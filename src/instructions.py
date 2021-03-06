import os
from pickle import NEWFALSE
from bitsnbytes import Byte
from enum import Enum
from typing import Callable, List

from inspect import currentframe


def formatlist_items(arr: list, lenght: int) -> list:
    if len(arr) > lenght:
        arr = arr[len(arr)-lenght:]
        arr.insert(0,'...')
    return arr

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
def OP_STSI(self):
    self.a = len(self.stack)
    if self.debug: print('│ >>> getting stack size')
def OP_SWAP(self):
    old_a = self.a
    self.a = self.pop(doreturn=True)
    self.push(value=old_a, doreturn=True)
    if self.debug: print('│ >>> swapped register with stack top')

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

def OP_NEWA(self):
    key = len(self.ptr_pool) + 1
    self.ptr_pool[key] = []
    self.a = key
    if self.debug: print('│ >>> created new array with pointer',key)
def OP_PUSA(self):
    self.ic += 1
    val = self.get_constant(self.ip.to_int())
    self.get_array(self.a).append(val)
    if self.debug: print('│ >>> appended',val,'to array')
def OP_POPA(self):
    # self.ic += 1
    val = self.get_array(self.a).pop()
    self.stack.append(val)
    if self.debug: print('│ >>> popped',val,'from array onto stack')
def OP_SPLT(self):
    olda = self.a
    for item in self.get_array(self.a):
        self.a = item
        self.push()
    self.a = olda
    if self.debug: print('│ >>> split array',
        formatlist_items(self.get_array(self.a), 10),'onto the stack')
def OP_JOIN(self):
    key = len(self.ptr_pool) + 1
    self.a = key
    arr = []
    for item in self.stack:
        arr.append(item)
    self.ptr_pool[key] = arr
    if self.debug: print('│ >>> joined stack as array')

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

def OP_OPEF(self):
    self.ic += 1
    name = ''.join([chr(x) for x in self.get_array(self.get_constant(self.ip.to_int()))])
    self.ic += 1

    # nibble represents mode:
    # 0b1111
    #   │││└ binary=0 text=1
    #   ││└ append
    #   │└ write
    #   └ read
    
    mode = self.get_constant(self.ip.to_int())
    if mode < 0x0 or mode > 0xf:
        # invalid mode
        return("RuntimeError: invalid file mode "+str(bin(mode)))
    bits = [int(x) for x in bin(mode)[2:]]
    while len(bits) < 4:
        bits.insert(0, 0)

    if bits[:3] == [0,0,0]:
        return("RuntimeError: invalid file mode 0b"+ ''.join([str(x) for x in bits]) +\
             ' (at least read, write or append)')

    modestr = str()
    if bits[0]: # read
        modestr = 'r'

    if bits[1]: # write
        if bits[0]: modestr = 'r+' # also read
        else: modestr = 'w' # just write
    
    elif bits[2]: # append (skipped if already writing)
        if bits[0]: modestr = 'a+' # also read
        else: modestr = 'a' # just append
    
    if not bits[3]: # binary mode
        modestr = modestr.replace('+', 'b+') if '+' in modestr else modestr + 'b'
    
    # opening n shit
    try:
        key = len(self.file_pool) + 1
        self.file_pool[key] = open(self.translate_filename(name), modestr)
        if self.debug: print('│ >>> opening file',name,'with mode',modestr,'with pointer',key)
        self.a = key
    except FileNotFoundError:
        if self.debug: print('│ >>> failed to open file',name,'(file not found)')
def OP_CLOF(self):
    self.ic += 1
    key = int(self.get_constant(self.ip.to_int()))
    if key in self.file_pool:
        self.file_pool[key].close()
        self.file_pool.pop(key)
        if self.debug: print('│ >>> closing file with pointer',key)
    elif self.debug: print('│ >>> failed to close file with pointer',key,'(not in file pool)')
def OP_SEKF(self):
    self.ic += 1
    key = int(self.get_constant(self.ip.to_int()))
    self.ic += 1
    pos = int(self.get_constant(self.ip.to_int()))
    if key in self.file_pool:
        self.file_pool[key].seek(pos)
        if self.debug: print('│ >>> seeking to',pos,'in file with pointer',key)
def OP_WRTF(self):
    self.ic += 1
    key = int(self.get_constant(self.ip.to_int()))
    self.ic += 1
    text = ''.join([chr(x) for x in self.get_array(self.get_constant(self.ip.to_int()))])
    if key in self.file_pool and self.file_pool[key].writable():
        self.file_pool[key].write(text)
        if self.debug: print('│ >>> writing "'+text+'" to file with pointer',key)
    elif self.debug: print('│ >>> failed to write to file with pointer',key)
def OP_REAF(self):
    self.ic += 1
    key = int(self.get_constant(self.ip.to_int()))
    self.ic += 1
    length = int(self.get_constant(self.ip.to_int()))
    if key in self.file_pool and self.file_pool[key].readable():
        arg = [length] if length else [] 
        text = self.file_pool[key].read(*arg)
        textarr = [ord(char) if isinstance(char, str) else char for char in text]
        # textarr.reverse()
        ptr = len(self.ptr_pool) + 1
        self.ptr_pool[ptr] = textarr
        self.a = ptr
        if self.debug: print('│ >>> reading from file with pointer',key,'to array with pointer',ptr)

def OP_MAKF(self):
    self.ic += 1
    name = ''.join([chr(x) for x in self.get_array(self.get_constant(self.ip.to_int()))])
    open(self.translate_filename(name), 'a').close()
    if self.debug: print('│ >>> touched file',name)
def OP_DELF(self):
    self.ic += 1
    name = ''.join([chr(x) for x in self.get_array(self.get_constant(self.ip.to_int()))])
    os.remove(self.translate_filename(name))
    if self.debug: print('│ >>> deleted file',name)

def OP_CLST(self):
    self.stack = []
    if self.debug: print('│ >>> clearing stack')
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
        self.func: Callable = None

sln = ln()+2
class Instruct(Enum):
    NOI     = Ins(ln(sln),  False)
    # stack
    PUSH    = Ins(ln(sln),  False)
    POP     = Ins(ln(sln),  False)
    LOAD    = Ins(ln(sln),  False, float)
    LODA    = Ins(ln(sln),  False, list)
    STSI    = Ins(ln(sln),  False)
    SWAP    = Ins(ln(sln),  False)
    # arithmetic
    ADD     = Ins(ln(sln),  False)
    SUB     = Ins(ln(sln),  False)
    MUL     = Ins(ln(sln),  False)
    DIV     = Ins(ln(sln),  False)
    NEG     = Ins(ln(sln),  False)
    # io
    INPT    = Ins(ln(sln),  False)
    PRNT    = Ins(ln(sln),  False)
    PRNC    = Ins(ln(sln),  False)
    PRNS    = Ins(ln(sln),  False)
    PRNA    = Ins(ln(sln),  False)
    # control flow
    CMP     = Ins(ln(sln),  False)
    JMP     = Ins(ln(sln),  True,  int)
    JMIF    = Ins(ln(sln),  True,  int)
    JIFN    = Ins(ln(sln),  True,  int)
    CALL    = Ins(ln(sln),  True,  int)
    CAIF    = Ins(ln(sln),  True,  int)
    CIFN    = Ins(ln(sln),  True,  int)
    RET     = Ins(ln(sln),  False)
    # register manipulation
    INC     = Ins(ln(sln),  False)
    DEC     = Ins(ln(sln),  False)
    # array
    NEWA    = Ins(ln(sln),  False)
    PUSA    = Ins(ln(sln),  False, int)
    POPA    = Ins(ln(sln),  False)
    SPLT    = Ins(ln(sln),  False)
    JOIN    = Ins(ln(sln),  False)
    # byte manipulation
    PUSB    = Ins(ln(sln),  True,  int)
    GETB    = Ins(ln(sln),  True,  int)
    # variable
    NVAR    = Ins(ln(sln),  False, id)
    DVAR    = Ins(ln(sln),  False, id)
    PUVA    = Ins(ln(sln),  False, id)
    LOVA    = Ins(ln(sln),  False, id)
    INCV    = Ins(ln(sln),  False, id)
    DECV    = Ins(ln(sln),  False, id)
    # file io
    OPEF    = Ins(ln(sln),  False, str, int)
    CLOF    = Ins(ln(sln),  False, int)
    SEKF    = Ins(ln(sln),  False, int, int)
    WRTF    = Ins(ln(sln),  False, int, str)
    REAF    = Ins(ln(sln),  False, int, int)
    MAKF    = Ins(ln(sln),  False, str)
    DELF    = Ins(ln(sln),  False, str)
    #RENF    = Ins(ln(sln),  False, int, str)
    #GFID    = Ins(ln(sln),  False, str, int)
    # misc.
    CLST    = Ins(ln(sln),  False)
    WAIT    = Ins(ln(sln),  False, float)
    POLL    = Ins(ln(sln),  False)
    KILL    = Ins(ln(sln),  False)

def getinstruct(byteval: int):
    for instruct in Instruct:
        if instruct.value.byte == byteval:
            return instruct
    return False

for op in Instruct:
    if 'OP_'+op.name not in locals():
        raise NotImplementedError(op.name)
    op.value.func = eval('OP_'+op.name)
# print('\n'.join([op.name +' '+str(op.value.byte.to_int()) for op in Instruct]))
