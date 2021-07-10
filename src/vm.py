from ctypes import c_ubyte as cbyte
from chunk import Instruct
from operations import opfuncs

class VM:
    def __init__(self):
        # bytecode
        self.bytes: list = None
        self.ic: int = 0
        
        self.killed = False
        self.output = ""

        # stack
        self.stack = []
        self.max_stack_size = 255

        # register
        self.a: float = 0
        self.r: int = 0
        self.f: bool = False

    def configure(self, cbytes):
        self.bytes = cbytes

    @property
    def ip(self):
        if self.bytes and self.bytes != []:
            if len(self.bytes) - 1 < self.ic:
                return None
            return self.bytes[self.ic]
        return None

    @property
    def instruct(self):
        for op in Instruct:
            # print(op.name, op.value.byte, self.ip)
            if op.value.byte.value == self.ip.value:
                return op.name
        # if self.ip == Instruct.KILL.value.byte:
            # return Instruct.KILL.name
        return "NONE"

    def push(self):
        """pushes the value in the register onto the stack"""
        if len(self.stack)+1 > self.max_stack_size:
            print("Error: Stack overflow, push failed")
        else:
            self.stack.append(self.a)

    def pop(self):
        """pops a value off the stack and puts it in the register"""
        if len(self.stack) > 0:
            self.a = self.stack.pop()
       
    def displayInstruct(self):
        print("instruction:",self.ic+1, end=' ')
        if self.instruct or True:
            print(self.instruct)
        else: print("")
        
    def displayData(self):
        print("registers: a:"+str(self.a)+'  r:'+str(self.r+2 if self.r else 0)+'  f:'+str(self.f)+'')
        print("stack:",self.stack,"("+str(len(self.stack))+' items)')
    
    def printResult(self, debug=False):
        if self.output:
            print(self.output.strip('\n')+'\n')
        elif debug:
            print("")
        
    def interpret(self, debug: bool = False):
        
        try:
            if self.bytes == [] or not self.bytes:
                raise ValueError("VM's bytes must be set first")
            
            self.ic = 0
            self.killed = False
            
            while self.ip != None and not self.killed:
                try: funcname = '_'+str(self.ip.value)
                except AttributeError: funcname = '_'+str(self.ip)
                
                if not funcname in opfuncs:
                    raise RuntimeError(f"Invalid operation \"{funcname}\"")
                
                if debug:
                    # print("")
                    self.displayInstruct()
                    
                self.output = opfuncs[funcname](self)
                self.ic += 1

                if debug: self.displayData()
                self.printResult(debug)
            
            if not self.killed:
                while True: pass
            elif debug: print("KILLED")
            # else:
                # self.displayInstruct()
                
        except KeyboardInterrupt:
            print("KeyboardInterupt")
            return