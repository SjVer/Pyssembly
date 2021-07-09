LOAD 122 ; "z" ASCII code
PUSH ; use it later to determin
     ; if loop is done

LOAD 97 ; "a" ASCII code

; loop:
PRNC ; print char
CMP ; check if char is "z"
JMIF 12 ; jump if true
INC ; increment char to next
JMP 6; not true so loop again
KILL