#offset 8200

; demonstration of PUSB and GETB
GETB 2 ; gets byte at next instruction (1)
PUSH
LOAD 66
PUSB 7 ; pushes KILL to next instruction
NOI ; will be changed to KILL
PRNT ; won't be reached