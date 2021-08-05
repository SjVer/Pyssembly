from typing import Any, Dict, List
import typing
from instructions import Instruct
from bitsnbytes import Byte, bits_to_int, int_to_bits #, split_bits, int_to_bits, float_to_IEEE754
# from hashtable import HashTable
import pickle, os
from copy import deepcopy
from time import sleep
from PIL import Image

class CompilationError(Exception):
    def __init__(self, msg=None):
        if (not msg) or (msg == ""):
            msg == "Error: Invalid operation"
        else:
            msg = "Error: " + msg
        super().__init__(msg)

class Compiler:
    def __init__(self, binpath: str, poolpath: str, ptr_poolpath: str, op_binpath: str):
        self.code: str = ""
        self.instructs: list[str] = []
        self.bytecode = []

        self.macros = {}
        self.consts = {}
        self.vars = {}
        self.pool: Dict[int:Any] = {}
        self.ptr_pool: Dict[int:list] = {}
        
        self.address_offset = 0
        # self.hashtable = HashTable()
        # self.instructs_dict: Dict[int:str] = {}
        
        self.bytecode_bin_path = binpath
        self.pool_bin_path = poolpath
        self.ptr_pool_bin_path = ptr_poolpath
        self.instructs_bin_path = op_binpath

    def getInstruct(self, text: str):
        for instruct in Instruct:
            # print(text, instruct.name)
            # if text.startswith(instruct.name):
            if text == instruct.name:
                return instruct
        return False

    def generate_key(self, value: Any, ptr: bool = False):
        if ptr:
            for key in self.ptr_pool:
                if self.ptr_pool[key] == value:
                    return key
            return len(self.ptr_pool) + 1
        else:
            for key in self.pool:
                if self.pool[key] == value:
                    return key
            return len(self.pool) + 1
        
    def add_to_pool(self, value, ptr: bool = False):
        key = self.generate_key(value, ptr)
        if ptr:
            pkey = self.generate_key(key)
            self.pool[pkey] = key
            self.ptr_pool[key] = value
            return pkey
        else:
            self.pool[key] = value
            return key

    def handlearg(self, arg: str, argtype: type, offset_s: bool, can_be_var: bool = True):
        # print(); print(arg, argtype, offset_s, can_be_var)
        # print('handling arg',arg,'supposedly of type',argtype,end='')

        isconst = False
        if arg in self.consts:
            arg = self.consts[arg][0]
            isconst = True

        if arg in self.vars:
            argtype = id

        # print(' but now of type',argtype)

        try:
            if argtype == float:
                value = float(arg)
                if offset_s and not isconst:
                    value += self.address_offset
                
                key = self.add_to_pool(value)
                return Byte(key)
            
            elif argtype == int:
                value = int(arg)
                if offset_s and not isconst:
                    value += self.address_offset
                
                key = self.add_to_pool(value)
                return Byte(key)
            
            elif argtype == id:
                # variable
                value = str(arg)
                self.vars[value] = 0 # dummy value
                key = self.add_to_pool(value)
                return Byte(key)
            
            elif argtype == list and arg[0] == '{':
                # list
                inlist = arg[1:-1].split(',')
                vlist = list()
                for item in inlist:
                    if not item.isnumeric(): raise ValueError
                    vlist.append(int(item) + (self.address_offset if offset_s else 0))
                
                key = self.add_to_pool(vlist, True)
                return Byte(key)

            elif argtype == list or argtype == str:
                # string
                if not arg.isascii():
                    print('string contains non-ascii characters')
                    raise ValueError

                charlist = [ord(char) for char in list(arg)]

                key = self.add_to_pool(charlist, True)
                return Byte(key)

            else:
                print('unimplemented type',argtype)
                raise ValueError

        except ValueError as e:
            raise CompilationError("Invalid argument "+str(arg)+' (needs to be of type '+\
                str(argtype.__name__)+')')#, not of type '+str(type(arg).__name__)+')')

    def expandMacro(self, macro: str):
        name = macro.split(':')[0]
        content = macro.replace(name+':','')
        if not name or not content: raise CompilationError("Invalid macro \""+macro+"\"")
        lines = [x.strip() for x in content.split(',')]
        
        # tempchunk, instructs = self.compile(lines=lines, returninstructs=True)
        tempcomp = deepcopy(self)
        tempcomp.compile(lines, False)
        self.pool = tempcomp.pool

        self.macros[name] = tempcomp.bytecode
        # self.macros[name] = {
        #     "bytes": tempcomp.bytecode,
        #     "instructs": instructs
        # }
        # print(self.macros[name])

    def write_binaries(self):

        for f in [self.bytecode_bin_path, self.pool_bin_path,
            self.ptr_pool_bin_path, self.instructs_bin_path]:
            if not os.path.exists(os.path.dirname(f)):
                os.makedirs(os.path.dirname(f))

        with open(self.bytecode_bin_path, 'wb') as f:
            # bytearr = bytearray()
            f.write(bytearray([byte.to_int() for byte in self.bytecode]))
        
        with open(self.pool_bin_path, 'wb') as f:
            pickle.dump(self.pool, f)
        with open(self.ptr_pool_bin_path, 'wb') as f:
            pickle.dump(self.ptr_pool, f)
        with open(self.instructs_bin_path, 'wb') as f:
            opdict = {}
            for op in Instruct:
                opdict[op.value.byte.to_int()] = op.name
            pickle.dump(opdict, f)

    def compile(self, lines=None, do_format: bool = True):
        
        try:
            self.bytecode = []
            
            # if returninstructs: instructs = []
            lines = self.code.replace('\\n', 'FAKENEWLINEHERE')\
                .replace('\\', '\n')\
                .replace('FAKENEWLINEHERE', '\\n')\
                .split('\n') if not lines else lines
            
            for line in lines:
                
                # ignore empty lines and comments n shit
                line = line.split(';')[0].strip()
                if not line: continue
                
                while "'" in line:
                    # expect a char
                    try:
                        char = line.split("'")[1]
                        realchar = bytes(char, "utf-8").decode("unicode_escape")
                        if len(realchar) != 1: raise TypeError
                        line = line.replace("'"+char+"'", str(ord(realchar)))
                    except TypeError:
                        raise CompilationError("Invalid char \'"+char+"\'")
                
                # replace hex with int
                if '0x' in line:
                    try:
                        hexstr = '0x' + line.split('0x')[1].strip()
                        line = line.replace(hexstr, str(eval(hexstr)))
                    except Exception:
                        raise CompilationError("Invalid hexadecimal \""+hexstr+'"')

                if '0b' in line:
                    try:
                        binstr = '0b' + line.split('0b')[1].strip()
                        line = line.replace(binstr, str(eval(binstr)))
                    except Exception:
                        # print(e)
                        raise CompilationError("Invalid binary \""+binstr+'"')

                # get macro
                if line.startswith("#def "):
                    # marco
                    macro = line[5:]
                    self.expandMacro(macro)
                    continue
                    
                # get offset
                elif line.startswith("#offset "):
                    try:
                        self.address_offset = int(line.replace('#offset ', ''))
                    except ValueError:
                        raise CompilationError("Invalid offset: \""+line.replace("#offset ", '')+'"')
                    continue
            
                # get variable
                elif line.startswith("#const "):
                    try:
                        type_and_name = line.replace("#const ", '').split(':')[0].strip()
                        typ = type_and_name.split(' ')[0]
                        name = type_and_name.split(' ')[1]
                        
                        if typ == 'i':
                            value = int(line.replace("#const ", '').split(':')[1].strip())
                        elif typ == 'f':
                            value = float(line.replace("#const ", '').split(':')[1].strip())
                        self.consts[name] = [value, type(value)]
                    except ValueError:
                        raise CompilationError("Invalid constant declaration: \""+line.replace("#var  ", '')+'"')
                    continue

                    # print("\n",line)

                # get instruction
                instruct_str = line.split(' ')[0]
                instruct = self.getInstruct(instruct_str)

                # print(instruct,line)
                
                # check macro
                if instruct_str in self.macros:
                    # for byte, text in zip(
                    #     self.macros[instruct_str]["bytes"],
                    #     self.macros[instruct_str]["instructs"]
                    #     ):
                    for byte in self.macros[instruct_str]:
                        self.bytecode.append(byte)
                        # self.instructs.append(text)
                    continue
                        
                # check instruction
                elif not instruct:
                    raise CompilationError("Invalid instruction \""+instruct_str+\
                        ('" after instruction '+self.instructs[-1] if len(self.instructs)>0 else '"'))
                
                # if returninstructs: instructs.append(instruct_str)
                # else: self.instructs.append(instruct_str)
                self.instructs.append(instruct_str)
                # write instruction
                self.bytecode.append(instruct.value.byte)

                # handle args
                opargc = instruct.value.argc
                opargs = instruct.value.args
                offs_s = instruct.value.offset_sensitive
                if opargc > 0:
                    
                    # get args
                    args = list()
                    part = None
                    i = 0
                    parts = line.split(' ')[1:]
                    while i < len(parts) and parts:
                        part = parts[i]

                        # str
                        if part[0] == '"':
                            text = str()
                            # text = part[1:] if part[-1] != '"' else part[1:-1]
                            # i += 1
                            # part = parts[i]
                            while part[-1] != '"':
                                text += ' ' + part
                                i += 1
                                part = parts[i]
                            part = text + ' ' + part
                            part = part.strip().strip('"')
                        
                        # arr
                        elif part[0] == '{':
                            text = str()
                            # i += 1
                            # part = parts[i]
                            while part[-1] != '}':
                                text += part
                                i += 1
                                part = parts[i]
                            part = text + part

                        args.append(part)
                        i += 1
                
                    # print(args)

                    if len(args) != opargc:
                        raise CompilationError(
                            "Invalid amount of arguments at instruction "+\
                                self.instructs[-1] + " (expected "+\
                                str(opargc)+' but got '+str(len(args))+')')
                        
                    for arg, arc in zip(args, range(opargc)):
                        # if returninstructs: instructs.append(arg)
                        # else: self.instructs.append(arg)
                        self.instructs.append(arg)
                        
                        # print('\n\n',arg, opargs[arc], offs_s)
                        self.bytecode.append(self.handlearg(arg, opargs[arc], offs_s))


            if do_format: print('compiled prgm: '+' '.join([str(x.to_int()) for x in self.bytecode]))

            if do_format:
                self.format_bytecode()
            self.write_binaries()
            # if returninstructs: return instructs
            return

        except CompilationError as e:
            print(e)
            return False

    def format_bytecode(self):
        # format chunk for vm
        
        oldbytes = self.bytecode
        newbytes = []

        # on/off byte
        newbytes.append(Byte(0x01))
        # display on/off byte
        newbytes.append(Byte(0x00))
        # flip buffer with display byte
        newbytes.append(Byte(0x00))
        # pixel bytes
        for _ in range(128*128*2):
            newbytes.append(Byte(0x00))
        
        # pad to 32800
        while len(newbytes) < 32800:# - 1:
            newbytes.append(Byte(0x00)) 

        # print('uchunk:',oldchunk.bytes)
        # exit(1)

        # append program to formatted chunk
        for byte in oldbytes:
            newbytes.append(byte)

        self.bytecode = newbytes

    @staticmethod
    def compile_image(input_image: str, output_file: str):
        if not os.path.isfile(input_image):
            raise CompilationError('file '+str(input_image)+' not found')
        eightbit_list = list(Image.open(input_image).getdata())
        
        # convert to 8bit
        for i in range(len(eightbit_list)):

            nr = int_to_bits(eightbit_list[i][0] * 7 / 255, length=3)
            ng = int_to_bits(eightbit_list[i][1] * 7 / 255, length=3)
            nb = int_to_bits(eightbit_list[i][2] * 3 / 255, length=2)

            newval = bits_to_int(nr + ng + nb)
            eightbit_list[i] = newval
        
        # insert with and height in begin (only one byte cuz max dimensions are 128x128 anyway)
        w, h = Image.open(input_image).size
        eightbit_list.insert(0, h)
        eightbit_list.insert(0, w)

        bytearr = bytearray(eightbit_list)
        with open(output_file, 'wb') as f:
            f.write(bytearr)
