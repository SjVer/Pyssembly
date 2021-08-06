;create file
MAKF "\rootfs\home\test.txt"

; open file
NVAR file
OPEF "\rootfs\home\test.txt" 0b1101
PUVA file

; write to file
WRTF file "test test!"

; seek start of file
SEKF file 0

; read file
REAF file 0
; the 0 means all of file
PRNS

CLOF file

CLST
SPLT ; split array to ints in stack

DELF "\rootfs\home\test.txt"
KILL