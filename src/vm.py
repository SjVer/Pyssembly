import time, sys, os, pickle
from time import sleep, time
from typing import Any, Dict, List
from bitsnbytes import Byte, bits_to_int
from random import randint

from instructions import *
from hashtable import HashTable

import threading

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

# VM BYTES FORMAT:
# 1 : on or off
# 2 : display on or off
# 3 - 4098 : pixels of display (64 * 64) indexed per row
# 4099 : start of program

class VM:
    def __init__(self):
        
        self.rootdir = str()
        
        # bytecode
        self.bytes: list = None
        self.pool: Dict[int:Any] = dict()
        self.ic: int = 0
        
        # flags
        self.killed = False
        self.debug = False

        # stack
        self.stack = []
        self.MAX_STACK_SIZE = 20
        self.ret_stack: List[int] = []
        self.MAX_RET_STACK_SIZE = 20

        # registers
        self.a: float = 0
        self.f: bool = False

        # hash table
        self.hashtable = HashTable()

        # terminal
        self.output = ""

        # display
        self.display = None
        self.video_changes_buffer = {} # pixels of prevous frame (key: tuple of x and y, value: bool if same as previous frame)
        # self.video_pixels_buffer = {} # last drawn pixels (key: tuple of x and y, value: rgb tuple)

        # CONSTANTS
        self.ISALIVE_BYTE = 0
        self.DISPLAY_BYTE = 1
        self.DISPLAY_FLIP = 2
        self.PIXELS_START = 3
        self.DISPLAY_SIZE = 128
        self.INIT_DISPLAY_SCALE = 5
        self.PRGM_START = 32800

    def configure(self, rootdir: str, debug: bool, slow: bool):
        self.rootdir = rootdir
        self.debug = debug
        self.slow = slow

        # load boot files n shit
        with open(os.path.join(self.rootdir, 'boot', 'kernel.bin'), 'rb') as f:
            ints = [x for x in f.read()]
            self.bytes = [Byte(x) for x in ints]
        
        with open(os.path.join(self.rootdir, 'boot', 'kernel-pool.bin'), 'rb') as f:
            self.pool = pickle.load(f)

        # print([byte.to_int() for byte in self.bytes])
        # print(self.pool)

    # STATUS STUFF

    @property
    def alive(self) -> bool:
        return bool(self.bytes[0])

    @property
    def display_on(self) -> bool:
        return bool(self.bytes[1])

    # @profile
    def poll(self) -> None:
        
        # poll display
        if not self.display and self.display_on:
            self.startdisplay()
        elif self.display and not self.display_on:
            self.enddisplay()
        
        # # update display
        if self.display_on:
            self.updatedisplay()

            # poll pygame events
            for event in pg.event.get():
                
                if event.type == pg.QUIT:
                    # byte 2 determines if display is on or off
                    self.bytes[1] = Byte(0)
                
                elif event.type == pg.VIDEORESIZE:
                    self.resetdisplay()

        # poll aliveness
        if not self.alive:
            if self.display_on:
                self.enddisplay()
            # if self.debug:
                # print("\nKILLED")
            # sys.exit()
        
    # DISPLAY STUFF

    def getpixel(self, row: int, column: int) -> Byte:
        return self.bytes[self.PIXELS_START + column*self.DISPLAY_SIZE + row]

    def setpixel(self, row: int, column: int, byte: Byte) -> None:
        # print(row, column, self.PIXELS_START + row*64+column, len(self.bytes), self.PIXELS_START + 64*64)
        self.bytes[self.PIXELS_START + column*self.DISPLAY_SIZE + row] = byte
        self.video_changes_buffer[(row, column)] = False

    def prunepixel(self, row: int, column: int) -> None:
        self.video_changes_buffer[(column, row)] = False
        # print('pixel ('+str(row)+','+str(column)+') pruned ('+str(self.PIXELS_START+column*64+row)+')')

    def address_to_pixel(self, address: int) -> tuple:
        if address in range(self.PIXELS_START, 
            self.PIXELS_START + self.DISPLAY_SIZE * self.DISPLAY_SIZE - 1):
            address -= self.PIXELS_START    
            column = address % self.DISPLAY_SIZE
            row = address // self.DISPLAY_SIZE
            # self.prunepixel(row, column)
            return (row, column)

    def startdisplay(self):
        pg.init()
        self.display = pg.display.set_mode(
            [self.DISPLAY_SIZE * self.INIT_DISPLAY_SCALE,
                self.DISPLAY_SIZE * self.INIT_DISPLAY_SCALE],
            pg.RESIZABLE, pg.DOUBLEBUF)
        pg.event.set_allowed([pg.QUIT, pg.VIDEORESIZE])
        pg.display.set_caption("Pyssembly VM")
    
    # @profile
    def updatedisplay(self):
        width, height = self.display.get_size()
        width /= self.DISPLAY_SIZE; height /= self.DISPLAY_SIZE

        r = range(self.DISPLAY_SIZE)
        m3 = 225/7
        m2 = 225/3

        hasdrawn = False
        # firstpixel = None
        # lastpixel = None

        for y in r:
            for x in r:

                # if (x, y) in self.video_changes_buffer and self.video_changes_buffer[(x, y)]:
                if not self.video_changes_buffer.get((x, y)):
                    
                    if not hasdrawn:
                        hasdrawn = True
                        firstpixel = (x*width, y*width)

                    bits = self.getpixel(x, y).to_list()
                    
                    # byte: rrrgggbb 
                    rgb = (
                        bits_to_int(bits[:3]) * m3,
                        bits_to_int(bits[3:6]) * m3,
                        bits_to_int(bits[6:8]) * m2,
                    )
                    # add 1 to width and height to avoid black lines
                    pg.draw.rect(self.display, rgb, (x*width, y*height, width + 1, height + 1))
        
                    self.video_changes_buffer[(x, y)] = True
                    lastpixel = (x*width+width+1, y*height+height+1)

        if hasdrawn:
            rect = pg.Rect(firstpixel[0], firstpixel[1], lastpixel[0], lastpixel[1])
            pg.display.update(rect)
            # print('update')
        # pg.display.flip()

    def resetdisplay(self):
        self.video_changes_buffer = {}

    def enddisplay(self):
        self.display = None
        pg.quit()

    # INSTRUCTION STUFF

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
            if op.value.byte == self.ip:
            # if op.value.byte.value == self.ip.value:
                return op.name
        # if self.ip == Instruct.KILL.value.byte:
            # return Instruct.KILL.name
        return "NONE"

    # STACK STUFF

    def push(self):
        """pushes the value in the register onto the stack"""
        if len(self.stack)+1 > self.MAX_STACK_SIZE:
            print("Error: Stack overflow, push failed")
        else:
            self.stack.append(self.a)

    def pop(self):
        """pops a value off the stack and puts it in the register"""
        if len(self.stack) > 0:
            self.a = self.stack.pop()

    def push_ret(self, dest: int):
        """pushes a return address onto the stack"""
        if len(self.ret_stack)+1 > self.MAX_RET_STACK_SIZE:
            print("Error: Max call depth reached, failed to push return address")
        else:
            self.ret_stack.append(dest)

    def pop_ret(self):
        """pops the last return address off the stack and returns it"""
        if len(self.ret_stack) > 0:
            return self.ret_stack.pop()
        return 0

    # TERMINAL STUFF

    def displayInstruct(self):
        # 0000 INST
        print("┌ instruction", f"{self.ic:04}",
              hex(self.ip.to_int()), end=' ')
        if self.instruct or True:
            print(self.instruct)
        else: print("")
        
    def displayData(self):
        # print("registers: a:"+str(self.a)+'  r:'+str(self.r+2 if self.r else 0)+'  f:'+str(self.f)+'')
        # print(f'{"┌" if self.repl else "│"} alive:',self.bytes[0].to_int(),
        
        print(f'│ alive:',self.bytes[0].to_int(), 'display:', self.bytes[1].to_int())
        
        # [0000] [0000] [0]
        # print(f'{"┌" if self.repl else "│"} '+\
        print('│ registers: '+\
              ''.join([f'[{x}] ' for x in [f'{self.a:05}',
            #   f'{self.r if self.r else 0:04}', int(self.f)]]))
              int(self.f)]]))

        print("│ call stack: {"+', '.join(str(x) for x in self.ret_stack)+'} (' +\
            str(len(self.ret_stack))+f' item{"s" if len(self.ret_stack) != 1 else ""})')
        # {0000, 0000, 0000} (0 items)
        print("└ stack: {"+', '.join(f'{x:04}' for x in self.stack)+"} (" +
              str(len(self.stack))+f' item{"s" if len(self.stack) != 1 else ""})')
    
    def printResult(self):
        # print("printing result",self.output != None,self.output)
        if self.output != None:
            # print(self.output, end='')
            print(self.output.strip('\n') if self.output != "\n" else "\n", end='', flush=True)
        if self.debug:
            print("")
        
    # INTERPRETING STUFF

    def get_constant(self, index: int, can_be_var: bool = True):
        if index not in self.pool:
            return False
        
        value = self.pool[index]
        if can_be_var and isinstance(value, str) and self.hashtable.find(value):
            # is var
            return self.hashtable.find(value)

        return value

    # @profile
    def run(self):
        try:
            if self.bytes == [] or not self.bytes:
                raise ValueError("VM's bytes must be set first")

            self.ic = self.PRGM_START

            lastop = None
            while self.ip != None and self.alive:

                # print(self.hashtable.buckets)
                # print(self.ic, self.ip.to_int())
                if self.slow: sleep(.5)

                # t1 = time()
                # print(self.pool)

                try: funcid = self.ip.to_int()
                except AttributeError: funcid = self.ip
                
                if not getinstruct(funcid):
                    # raise RuntimeError(f"Invalid operation \"{funcid}\"")
                    print(f"RuntimeError: Invalid operation \"{funcid}\"")
                    print("Traceback: ")
                    for index, byte in zip(
                        [x for x in range(self.ic-2, self.ic+2)],
                        self.bytes[self.ic-2:self.ic+2]):
                        print(('   ' if index != self.ic else '-> ')+\
                            str(index).rjust(4, '0'),byte.to_int() if isinstance(byte, Byte) else byte)
                    
                    print('last succesfull operation:',lastop)
                    print('first byte of program:',self.bytes[self.PRGM_START])
                    sys.exit(1)
                
                if self.debug:
                    # print("")
                    self.displayInstruct()
                
                executeAfter = False
                # print(funcid)
                # print(getinstruct(funcid), self.bytes[self.ic+1])
                
                self.output = eval('OP_'+getinstruct(funcid).name)(self)
                
                if isinstance(self.output, list):
                    if self.output[0] == "sleep":
                        executeAfter = f"sleep({self.output[1]})"
                    self.output = None
                
                self.ic += 1

                if self.debug: self.displayData()
                self.printResult()
                self.poll()
                if executeAfter: eval(executeAfter)

                lastop = getinstruct(funcid).name

                # print('elapsed:',time()-t1)

            if self.alive:
                while True: pass
            elif self.debug: print("KILLED")
            # else:
                # self.videoInstruct()
                
        except KeyboardInterrupt:
            print("KeyboardInterupt")
            return

if __name__ == "__main__":
    vm = VM()
    vm.startdisplay()
    vm.bytes=[Byte(i % 0xff) for i in range(vm.PIXELS_START + vm.DISPLAY_SIZE**2 + 30)]
    vm.bytes[:3] = [Byte(1), Byte(1)]

    for i in range(vm.DISPLAY_SIZE):
        vm.setpixel(i, 0, Byte(0xff))
        vm.setpixel(0, i, Byte(0xff))
        vm.setpixel(i, vm.DISPLAY_SIZE-1, Byte(0xff))
        vm.setpixel(vm.DISPLAY_SIZE-1, i, Byte(0xff))

    for i in range(1000):

        for i in range(50):
            x, y = vm.address_to_pixel(randint(vm.PIXELS_START, vm.DISPLAY_SIZE**2))
            vm.setpixel(x, y, Byte(randint(0, 255)))

        vm.poll()
