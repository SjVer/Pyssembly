#offset 8200

NVAR curPixel ; declaration

LOAD PIXEL_START
PUVA curPixel ; push to var

LOAD 0
LOVA curPixel ; load content of var

DVAR curPixel ; delete/free var

KILL