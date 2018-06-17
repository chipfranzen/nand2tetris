// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.
    @R0
    D=M     // D = R0
    @i
    M=D     // i = R0
    @R2
    M=0     // initialize result = 0
(LOOP)
    @i      // load i
    D=M     // D = i
    @END
    D;JLE   // if i <= 0, goto END
    @R1
    D=M
    @R2
    M=D+M   // add R1 to the running mul
    @i
    M=M-1   // decrement i
    @LOOP
    0;JMP   // goto LOOP
(END)
    @END
    0;JMP   // infinite loop
