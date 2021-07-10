; demonstration of PUSB and GETB
GETB 3 ; gets 1
PUSH
LOAD 66
PUSB 8 ; pushes KILL to next instruction
NOI ; will be changed to KILL
PRNT ; won't be reached