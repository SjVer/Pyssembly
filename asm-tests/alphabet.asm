#offset 8200

LOAD 'z' ; "z" ASCII code
PUSH ; use it later to determin
     ; if loop is done

LOAD 'a' ; "a" ASCII code

; loop:
PRNC ; print char
CMP ; check if char is "z"
JMIF 11 ; jump if true
INC ; increment char to next
JMP 5; not true so loop again

LOAD '\n'
PRNC ; print newline
KILL