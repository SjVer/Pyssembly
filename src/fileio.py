from ctypes import c_ubyte as cbyte
from chunk import Instruct

def writeBinary(path: str, cbytes: list):
    arr = []
    for byte in cbytes:
        if isinstance(byte, cbyte):
            arr.append(byte.value)
        
        elif isinstance(byte, float) and int(byte) == byte:
            # format: [254, amount of digits, digits]
            istr = str(byte).split('.')[0]
            arr.append(254)
            arr.append(len(istr))
            for i in istr: arr.append(int(i))
            
        elif isinstance(byte, float):
            # format: [225, amount of digits before dot, 
            #          amount of digits after dot,
            #          digits before dot, digits after dot]
            fstr = str(byte)
            arr.append(255)
            arr.append(len(fstr.split('.')[0]))
            arr.append(len(fstr.split('.')[1]))
            for i in fstr.split('.')[0]: arr.append(int(i))
            for i in fstr.split('.')[1]: arr.append(int(i))
        
        else:
            raise ValueError("cbytes list can only contain cbytes ints and floats")
    
    # clamp bytes between 0 and 225
    for i in range(len(arr)): arr[i] = max(min(arr[i], 255), 0)
    
    bytearr = bytearray(arr)
    with open(path, 'wb') as f:
        f.write(bytearr)
        
def readBinary(path: str):
    with open(path, 'rb') as f:
        rawbytearr = [x for x in f.read()]
    
    # get all instructions with arguments and their types
    arginstructs = {}
    for op in Instruct:
        if op.value.argc > 0:
            arginstructs[op.value.byte.value] = op.value.args 
    
    bytearr = []
    # convert raw bytes into proper vm-able bytes
    i = 0
    
    # temp function to handle floats
    def appendfloat(i):
        len1 = rawbytearr[i]
        i += 1
        len2 = rawbytearr[i]
        i += 1
        
        fstr = ""
        for _ in range(len1):
            fstr += str(rawbytearr[i])
            i += 1
        fstr += '.'
        for _ in range(len2):
            fstr += str(rawbytearr[i])
            i += 1
        bytearr.append(float(fstr))
        return i
    def appendint(i):
        ilen = rawbytearr[i]
        istr = ""
        i += 1
        for _ in range(ilen):
            istr += str(rawbytearr[i])
            i += 1
        bytearr.append(float(istr))
        return i
        
    while i < len(rawbytearr):
        if rawbytearr[i] == 254:
            # int coming up
            i += 1
            i = appendint(i)
        
        elif rawbytearr[i] == 255:
            # float comin up
            i += 1
            i = appendfloat(i)
        
        elif rawbytearr[i] in arginstructs:
            # instruction with args
            op = rawbytearr[i]
            bytearr.append(cbyte(op))
            i += 2
            for argtype in arginstructs[op]:
                if argtype == int or \
                    (argtype == float and rawbytearr[i-1]==254):
                    i = appendint(i)
                elif argtype == float:
                    i = appendfloat(i)
        
        else:
            bytearr.append(cbyte(rawbytearr[i]))
            i += 1
    
    return bytearr
