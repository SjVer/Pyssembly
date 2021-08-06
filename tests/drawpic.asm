#offset 32800
#const i DISPLAY: 1
#const i PIXEL_START: 3
#const i PIXEL_END: 32792

LOAD 1
PUSB DISPLAY

; load bitmap
NVAR bitmapfile
OPEF "\rootfs\.bitmaps\home.bin" 0b1000
PUVA bitmapfile
REAF bitmapfile 0
CLOF bitmapfile
SPLT

; pop dimension bytes
POP
POP

NVAR curPixel
LOAD PIXEL_START
PUVA curPixel

; loop
PUSH
LOAD PIXEL_END
PUSH
LOVA curPixel
CMP
JMIF 43
POP
POP
POP
PUSB curPixel
INCV curPixel
JMP 25

; end
LODA "done!"
PRNS
LOAD '\n'
PRNC
INPT
WAIT 60
KILL