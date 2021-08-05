#offset 32800

; demonstration of PUSB and GETB
GETB 2 ; gets byte at next instruction (1)
PUSH
LOAD 0
PUSB 7 ; pushes NOI to next instruction
PRNT ; will be replaced by NOI
KILL