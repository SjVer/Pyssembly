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
        self.code: str = ""
        self.instructs: list[str] = []
        self.macros = {}
        
    def getInstruct(self, text: str):
        for instruct in Instruct:
            # if text.startswith(instruct.name):
            if text == instruct.name:
                return instruct
        return False

    def handlearg(self, arg: str, argtype: type):
        try:
            value = argtype(arg)
        except ValueError:
            raise CompilationError
        finally:
            return value

    def expandMacro(self, macro: str):
        name = macro.split(':')[0]
        content = macro.replace(name+':','')
        if not name or not content: raise CompilationError("Invalid macro \""+macro+"\"")
        lines = [x.strip() for x in content.split(',')]
        
        tempchunk, instructs = self.compile(lines=lines, returninstructs=True)
        self.macros[name] = {
            "bytes": tempchunk.bytes,
            "instructs": instructs
        }

    def compile(self, chunk=None, lines=None, returninstructs=False):
        if not chunk:
            # raise CompilationError("chunk must be set first")
            chunk = Chunk()
        
        if returninstructs: instructs = []
        lines = self.code.split('\n') if not lines else lines
        
        for line in lines:
            
            # ignore empty lines and comments n shit
            line = line.split(';')[0].strip()
            if not line: continue
            
            # get macro
            if line.startswith("#def "):
                # marco
                macro = line[5:]
                self.expandMacro(macro)
                continue
                
            # get instruction
            instruct_str = line.split(' ')[0]
            instruct = self.getInstruct(instruct_str)
            
            # check macro
            if instruct_str in self.macros:
                for byte, text in zip(
                    self.macros[instruct_str]["bytes"],
                    self.macros[instruct_str]["instructs"]
                    ):
                    chunk.write(byte)
                    self.instructs.append(text)
                continue
                    
            # check instruction
            elif not instruct:
                raise CompilationError("Invalid instruction \""+instruct_str+\
                    ('" after instruction '+self.instructs[-1] if len(self.instructs)>0 else '"'))
            
            if returninstructs: instructs.append(instruct_str)
            else: self.instructs.append(instruct_str)
            # write instruction
            chunk.write(instruct.value.byte)

            # handle args
            opargc = instruct.value.argc
            opargs = instruct.value.args
            if opargc > 0:
                args = line.split(' ')[1:]
            
                if len(args) != opargc:
                    raise CompilationError(
                        "Invalid amount of arguments at instruction "+\
                            self.instructs[-1] + " (expected "+\
                            str(opargc)+')')
                    
                for arg, arc in zip(args, range(opargc)):
                    if returninstructs: instructs.append(arg)
                    else: self.instructs.append(arg)
                    chunk.write(self.handlearg(arg, opargs[arc]))
        
        if returninstructs: return (chunk, instructs)
        return chunk
