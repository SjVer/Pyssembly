#def NL: PUSH, LOAD '\n', PRNC, POP

LODA {0, 1, 2, 3} ; load int array
PRNA ; print array
NL

LODA "this is actually an array!" ; load string

PRNA ; print array
NL
PRNS ; print string
NL

; NVAR myArr
NEWA ; new array
; PUVA myArr

PRNA ; empty array
NL

PUSA 123 ; appends 123 to the array
PUSA 0x0f
PUSA 0x1c
POPA ; pops last value from the array onto the stack
POPA
SWAP
PRNT ; prints 15
SWAP

NL

PUSA 1
PUSA 2
PUSA 3

SPLT ; splits array onto the stack
JOIN ; joins stack to one array
PRNA

NL
CLST ; clear stack

KILL