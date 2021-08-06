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
		self.instructs_dict: Dict[int: str] = dict()

		# bytecode
		self.bytes: list = None
		self.pool: Dict[int:Any] = dict()
		self.ptr_pool: Dict[int:list] = dict()
		self.file_pool: Dict[int:'file'] = dict()
		self.ic: int = 0

		# flags
		self.killed = False
		self.debug = False

		# stack
		self.stack = []
		self.MAX_STACK_SIZE = 255**2
		self.ret_stack: List[int] = []
		self.MAX_RET_STACK_SIZE = 255

		# registers
		self.a: float = 0
		self.f: bool = False

		# hash table
		self.hashtable = HashTable()

		# terminal
		self.output = ""

		# display
		self.display: pg.Surface = None
		self.video_changes_buffer: List[tuple] = []
		self.buffer_display: pg.Surface = None
		self.pgclock = pg.time.Clock()

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

		with open(os.path.join(self.rootdir, 'boot', 'pool.bin'), 'rb') as f:
			self.pool = pickle.load(f)

		with open(os.path.join(self.rootdir, 'boot', 'arrays.bin'), 'rb') as f:
			self.ptr_pool = pickle.load(f)

		with open(os.path.join(self.rootdir, 'boot', 'instructions.bin'), 'rb') as f:
			self.instructs_dict = pickle.load(f)

		# print([byte.to_int() for byte in self.bytes])
		# print(self.pool)

	# STATUS STUFF

	@property
	def alive(self) -> bool:
		return bool(self.bytes[0])

	@property
	def display_on(self) -> bool:
		return bool(self.bytes[1])

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

	# FILE STUFF
	def translate_filename(self, filename) -> str:
		*dirs, basename = filename.split('\\')
		return os.path.join(self.rootdir, *dirs, basename)

	# DISPLAY STUFF

	def getpixel(self, row: int, column: int) -> Byte:
		return self.bytes[self.PIXELS_START + column*self.DISPLAY_SIZE + row]

	def setpixel(self, row: int, column: int, byte: Byte) -> None:
		# print(row, column, self.PIXELS_START + row*64+column, len(self.bytes), self.PIXELS_START + 64*64)
		self.bytes[self.PIXELS_START + column*self.DISPLAY_SIZE + row] = byte
		# self.video_changes_buffer[(row, column)] = False
		self.video_changes_buffer.append((row, column))

	def prunepixel(self, row: int, column: int) -> None:
		# self.video_changes_buffer[(column, row)] = False
		self.video_changes_buffer.append((column, row))

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
		# pg.event.set_allowed([pg.QUIT, pg.VIDEORESIZE])
		self.buffer_display = pg.Surface(
			(self.DISPLAY_SIZE, self.DISPLAY_SIZE))
		pg.display.set_caption("Pyssembly VM")

	def updatedisplay(self):
		m3 = 225/7
		m2 = 225/3
		hasdrawn = False

		for x, y in self.video_changes_buffer:

			if not hasdrawn:
				hasdrawn = True
				# firstpixel = (x*width, y*width)
				firstpixel = (x, y)

			bits = self.getpixel(x, y).to_list()
			# bits = [int(x) for x in str(self.getpixel(x, y))]

			# byte: rrrgggbb
			rgb = (
				bits_to_int(bits[:3]) * m3,
				bits_to_int(bits[3:6]) * m3,
				bits_to_int(bits[6:8]) * m2,
			)
			self.buffer_display.set_at((x, y), rgb)

			self.video_changes_buffer.remove((x, y))
			lastpixel = (x+1, y+1)

		if hasdrawn:
			m1 = self.display.get_width() / self.DISPLAY_SIZE
			m2 = self.display.get_height() / self.DISPLAY_SIZE
			rect = pg.Rect(firstpixel[0]*m1, firstpixel[1]*m2, lastpixel[0]*m1, lastpixel[1]*m2)

			self.display.blit(
				pg.transform.scale(self.buffer_display, self.display.get_size()), (0, 0))
			pg.display.update(rect)
			
		# pg.display.flip()

	def resetdisplay(self):
		self.display.fill((0,0,0))
		self.display.blit(
			pg.transform.scale(self.buffer_display, self.display.get_size()), (0, 0))
		pg.display.update()
		self.video_changes_buffer = []

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

	def getinstruct(self, opcode):
		name = self.instructs_dict[opcode]
		for op in Instruct:
			if op.name == name:
				return op

	# STACK STUFF

	def push(self, value = 0, doreturn: bool = False):
		"""pushes the value in the register onto the stack"""
		if len(self.stack)+1 > self.MAX_STACK_SIZE:
			print("Error: Stack overflow, push failed")
		else:
			self.stack.append(self.a if not doreturn else value)

	def pop(self, doreturn: bool = False):
		"""pops a value off the stack and puts it in the register"""
		if len(self.stack) > 0:
			if doreturn: return self.stack.pop()
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
			  hex(self.ip.to_int()), f"{self.ip.to_int():02}", end=' ')
		if self.instruct or True:
			print(self.instruct)
		else:
			print("")

	def displayData(self):
		# print("registers: a:"+str(self.a)+'  r:'+str(self.r+2 if self.r else 0)+'  f:'+str(self.f)+'')
		# print(f'{"┌" if self.repl else "│"} alive:',self.bytes[0].to_int(),

		print(f'│ alive:', self.bytes[0].to_int(),
			  'display:', self.bytes[1].to_int())

		# [0000] [0000] [0]
		# print(f'{"┌" if self.repl else "│"} '+\
		print('│ registers: ' +
			  ''.join([f'[{x}] ' for x in [f'{self.a:05}',
										   #   f'{self.r if self.r else 0:04}', int(self.f)]]))
										   int(self.f)]]))

		print("│ call stack: {"+', '.join(str(x) for x in formatlist_items(self.ret_stack, 10))+'} (' +
			  str(len(self.ret_stack))+f' item{"s" if len(self.ret_stack) != 1 else ""})')


		# {0000, 0000, 0000} (0 items)
		# print("└ stack: {"+', '.join(f'{x:04}' for x in self.stack)+"} (" +
		print("└ stack: {"+', '.join(f'{x:04}' if not isinstance(x, str) else x for x in \
			formatlist_items(self.stack, 10))+"} (" +
			  str(len(self.stack))+f' item{"s" if len(self.stack) != 1 else ""})')

	def printResult(self):
		# print("printing result",self.output != None,self.output)
		if self.output != None:
			# print(self.output, end='')
			print(self.output.strip('\n') if self.output !=
				  "\n" else "\n", end='', flush=True)
			if self.debug: print()
		if self.debug:
			print("")

	# INTERPRETING STUFF

	def get_constant(self, index: int, can_be_var: bool = True):
		if index not in self.pool:
			return 0

		value = self.pool[index]
		if can_be_var and isinstance(value, str) and self.hashtable.find(value):
			# is var
			return self.hashtable.find(value)

		return value

	def get_array(self, index: int):
		if index not in self.ptr_pool:
			return []

		arr = self.ptr_pool[index]
		# if can_be_var and isinstance(value, str) and self.hashtable.find(value):
			# is var
			# return self.hashtable.find(value)

		return arr

	def sleep(self, time) -> None: sleep(time)

	# @profile
	def run(self):
		try:
			if self.bytes == [] or not self.bytes:
				raise ValueError("VM's bytes must be set first")

			self.ic = self.PRGM_START


			if self.debug:
				# print(' '.join([str(x.to_int()) for x in self.bytes]))
				print()
				# print('\n'.join([op.name +' '+str(op.value.byte.to_int()) for op in Instruct]))
				print('pool:',self.pool)
				print('arrays:',self.ptr_pool)
				print('first byte:',self.ip.to_int())
				print()


			lastop = None
			while self.ip != None and self.alive:

				# print(self.hashtable.buckets)
				# print(self.ic, self.ip.to_int())
				if self.slow:
					sleep(.5)

				# t1 = time()
				# print(self.pool)

				# try:
				funcid = self.ip.to_int()
				# except AttributeError:
					# funcid = self.ip
				
				if not self.getinstruct(funcid):
					# raise RuntimeError(f"Invalid operation \"{funcid}\"")
					print(f"RuntimeError: Invalid operation \"{funcid}\"")
					print("Traceback: ")
					for index, byte in zip(
							[x for x in range(self.ic-2, self.ic+2)],
							self.bytes[self.ic-2:self.ic+2]):
						print(('   ' if index != self.ic else '-> ') +
							  str(index).rjust(4, '0'), byte.to_int() if isinstance(byte, Byte) else byte)

					print('last succesfull operation:', lastop)
					print('first byte of program:',
						  self.bytes[self.PRGM_START])
					sys.exit(1)

				if self.debug:
					# print("")
					self.displayInstruct()

				executeAfter = False
				# print(funcid)
				# print(getinstruct(funcid), self.bytes[self.ic+1])

				# self.output = eval('OP_'+self.getinstruct(funcid).name)(self)
				self.output = self.getinstruct(funcid).value.func(self)

				if isinstance(self.output, list):
					if self.output[0] == "sleep":
						# executeAfter = f"sleep({self.output[1]})"
						executeAfter = self.sleep
						executeAfterArgs = [self.output[1]]
					self.output = None

				self.ic += 1

				if self.debug:
					self.displayData()
				self.printResult()
				self.poll()
				if executeAfter:
					# eval(executeAfter)
					executeAfter(*executeAfterArgs)

				lastop = self.getinstruct(funcid).name
				# self.pgclock.tick(60)

				# print('elapsed:',time()-t1)

			if self.alive:
				while True:
					pass
			elif self.debug:
				print("KILLED")
			# else:
			  # self.videoInstruct()

		except KeyboardInterrupt:
			print("KeyboardInterupt")
			return


if __name__ == "__main__":
	vm = VM()
	vm.startdisplay()
	vm.bytes = [Byte(i % 0xff)
				for i in range(vm.PIXELS_START + vm.DISPLAY_SIZE**2 + 30)]
	vm.bytes[:3] = [Byte(1), Byte(1)]

	for i in range(vm.DISPLAY_SIZE):
		vm.setpixel(i, 0, Byte(0xff))
		vm.setpixel(0, i, Byte(0xff))
		vm.setpixel(i, vm.DISPLAY_SIZE-1, Byte(0xff))
		vm.setpixel(vm.DISPLAY_SIZE-1, i, Byte(0xff))

	for i in range(1000):

		for i in range(50):
			x, y = vm.address_to_pixel(
				randint(vm.PIXELS_START, vm.DISPLAY_SIZE**2))
			vm.setpixel(x, y, Byte(randint(0, 255)))

		vm.poll()
