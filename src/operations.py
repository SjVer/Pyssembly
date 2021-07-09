def checkAddress(self, dest: int): return dest in range(len(self.bytes))

def NOI(self): return None
def PUSH(self): self.push()
def POP(self): self.pop()
def LOAD(self):
    self.ic += 1
    self.a = self.ip
def ADD(self):
    self.pop()
    a = self.a
    self.pop()
    b = self.a
    self.a = a + b
def SUB(self):
    self.pop()
    a = self.a
    self.pop()
    b = self.a
    self.a = a - b
def MUL(self):
    self.pop()
    a = self.a
    self.pop()
    b = self.a
    self.a = a * b
def DIV(self):
    self.pop()
    a = self.a
    self.pop()
    b = self.a
    self.a = a / b
def NEG(self): self.a = -self.a
def INPT(self):
    inp = input()
    try: value = float(inp)
    except ValueError: value = 0
    self.a = value
def PRNT(self): return str(self.a)
def PRNC(self): return chr(int(self.a))
def CMP(self): self.f = self.a == self.stack[-1]
def JMP(self):
    self.ic += 1
    dest = int(self.ip)
    if not checkAddress(self, dest):
        print("Jump to address "+str(dest)+" failed")
    else:
        self.ic = dest-2
def JMIF(self):
    self.ic += 1
    dest = int(self.ip)
    if not self.f: return
    if not checkAddress(self, dest):
        print("Jump to address "+str(dest)+" failed")
    else:
        self.ic = dest-2
def CALL(self):
    self.ic += 1
    dest = int(self.ip)
    if not checkAddress(self, dest):
        print("Call to address "+str(dest)+" failed")
    else:
        self.r = self.ic
        self.ic = dest-2
def CAIF(self):
    self.ic += 1
    if not self.f: return
    dest = int(self.ip)
    if not checkAddress(self, dest):
        print("Call to address "+str(dest)+" failed")
    else:
        self.r = self.ic
        self.ic = dest-2
def RET(self):
    dest = self.r
    if not checkAddress(self, dest):
        print("Return to address "+str(dest)+" failed")
    else:
        self.ic = self.r
def INC(self): self.a += 1
def DEC(self): self.a -= 1 if self.a > 0 else 0
def KILL(self):
    self.stack = []
    self.a = 0
    self.r = 0
    self.f = False
    self.killed = True


opfuncs = {
    '_0': NOI,
    '_1': PUSH,
    '_2': POP,
    '_3': LOAD,
    '_4': ADD,
    '_5': SUB,
    '_6': MUL,
    '_7': DIV,
    '_8': NEG,
    '_9': INPT,
    '_10': PRNT,
    '_11': PRNC,
    '_12': CMP,
    '_13': JMP,
    '_14': JMIF,
    '_15': CALL,
    '_16': CAIF,
    '_17': RET,
    '_18': INC,
    '_19': DEC,
    '_66': KILL,
}
