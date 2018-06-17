// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(START)
    @i
    M=0
    @KBD    // read keyboard input
    D=M
    @FILL_LOOP
    D;JNE   // if D != 0, goto FILL
(CLEAR_LOOP)
    @i
    D=M
    @SCREEN
    A=D+A
    M=0
    @i
    MD=M+1
    @8192
    D=A-D
    @START
    D;JLE   // if i <= 0, listen for a new keypress
    @CLEAR_LOOP
    0;JMP   // continue clearing the lines
(FILL_LOOP)
    @i
    D=M
    @SCREEN
    A=D+A
    M=-1
    @i
    MD=M+1
    @8192
    D=A-D
    @START
    D;JLE   // if i <= 0, listen for a new keypress
    @FILL_LOOP
    0;JMP   // continue clearing the lines
