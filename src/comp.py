from chunk import Chunk, Instruct
from ctypes import c_ubyte as cbyte

class CompilationError(Exception):
    def __init__(self, msg=None):
        if (not msg) or (msg == ""):
            msg == "Error: Invalid operation"
        else:
            msg = "Error: " + msg
        super().__init__(msg)

class Compiler:
    def __init__(self):
        self.code = ""
        self.lines = []
        # chunk = None
        
    def getInstruct(self, text: str):
        for instruct in Instruct:
            if text.startswith(instruct.name):
                return instruct
        return False

    def handlearg(self, arg: str, argtype: type):
        try:
            value = argtype(arg)
        except ValueError:
            raise CompilationError
        finally:
            return value

    def compile(self, chunk=None):
        if not chunk:
            # raise CompilationError("chunk must be set first")
            chunk = Chunk()
        
        self.lines = self.code.split('\n')
        
        # ignore comments
        line = 0
        while True:
            if line not in range(len(self.lines)):
                break
            self.lines[line] = self.lines[line].split(';')[0].strip()
            if self.lines[line] == "":
                del self.lines[line]
                line += 1
            line += 1
        
        for line in self.lines:
            instruct = self.getInstruct(line.split(' ')[0])
            if not instruct:
                raise CompilationError("Invalid instruction \""+line.split(' ')[0]+'"')
            
            chunk.write(instruct.value.byte)

            opargc = instruct.value.argc
            opargs = instruct.value.args
            
            if opargc > 0:
                args = line.split(' ')[1:]
            
                if len(args) != opargc:
                    raise CompilationError(
                        "Invalid amount of arguments (expected "+\
                            str(opargc)+')')
                    
                for arg, arc in zip(args, range(opargc)):
                    chunk.write(self.handlearg(arg, opargs[arc]))
        
        return chunk
                
                