#offset 32800

#const i VIDEO: 1
#const i PIXEL_START: 3

LOAD 1
PUSB VIDEO  ; turn on display by setting the second
            ; byte to 1

NVAR curPixel

#def DRAWPXL: PUSB curPixel, WAIT 0.2; 4

LOAD PIXEL_START
PUVA curPixel

LOAD 0b00011100 ; green
DRAWPXL
INCV curPixel
DRAWPXL
INCV curPixel
DRAWPXL

LOAD PIXEL_START
PUVA curPixel

LOAD 0 ; black
DRAWPXL
INCV curPixel
DRAWPXL
INCV curPixel
DRAWPXL

JMP 6