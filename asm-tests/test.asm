#offset 32800

#const i VIDEO: -32799
#const i PIXEL_START: 3; -8198

LOAD 1
PUSB VIDEO ; turn on display

NVAR curPixel
LOAD PIXEL_START
PUVA curPixel

LOAD 0b00011100 ; green
PUSB curPixel
INCV curPixel
KILL
; JMP 12