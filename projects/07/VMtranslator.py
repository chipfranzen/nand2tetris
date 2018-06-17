#!/usr/bin/env python3
import argparse
from glob import glob
import os
import re

VALID_ARITHMETIC = ['add', 'sub', 'neg', 'eq', 'gt', 'lt', 'and', 'or', 'not']
UNARY_OPS = ['not', 'neg']
BINARY_OPS = ['add', 'sub', 'and', 'or']
COMP_OPS = ['eq', 'gt', 'lt']
BASE_SEGMENTS = ['local', 'argument', 'this', 'that']
base_seg_dict = {
    'local': 'LCL',
    'argument': 'ARG',
    'this': 'THIS',
    'that': 'THAT',
    'pointer': '3',
    'temp': '5'
}

class CodeWriter(object):
    def __init__(self, outfile):
        self.outfile = open(outfile, mode='w')

    def close(self):
        self.outfile.close()

    def set_file_name(self, file_name):
        if '/' in file_name:
            file_name = file_name.split('/')[-1]
        self.file_name = file_name.rstrip('.vm')

    def write_arithmetic(self, cmd, cmd_number):
        lines = []
        lines.append('@SP') # get stack pointer
        lines.append('AM=M-1') # point A to first item in stack
        if cmd in UNARY_OPS:
            if cmd == 'not':
                lines.append('M=!M') # not first stack item
            elif cmd == 'neg':
                lines.append('M=-M') # negate first stack item
            else:
                raise
        else:
            lines.append('D=M') # store first item in stack at D
            lines.append('@SP')
            lines.append('AM=M-1') # move down the stack
            if cmd in BINARY_OPS:
                if cmd == 'and':
                    lines.append('M=D&M') # and operands
                elif cmd == 'add':
                    lines.append('M=D+M') # add operands
                elif cmd == 'sub':
                    lines.append('M=M-D') # sub operands
                elif cmd == 'or':
                    lines.append('M=D|M') # or operands
                else:
                    raise
            elif cmd in COMP_OPS:
                lines.append('D=D-M') # sub the two stack items, ready for comparison
                lines.append(f'@RETURN_TRUE_{cmd_number}')
                if cmd == 'eq':
                    lines.append('D;JEQ')
                elif cmd == 'lt':
                    lines.append('D;JGT')
                elif cmd == 'gt':
                    lines.append('D;JLT')
                lines.append('@SP') 
                lines.append('A=M')
                lines.append('M=0') # return False if jump fails
                lines.append(f'@CONTINUE_{cmd_number}')
                lines.append('0;JMP') # skip return true
                lines.append(f'(RETURN_TRUE_{cmd_number})')
                lines.append('@SP') # recover the location of the stack pointer
                lines.append('A=M')
                lines.append('M=1') # return true if jump succeeds
                lines.append('M=-M')
                lines.append(f'(CONTINUE_{cmd_number})')
        lines.append('@SP')
        lines.append('M=M+1') # move stack pointer to empty cell
        self.outfile.write('\n'.join(lines) + '\n')

    def write_push_pop(self, cmd):
        lines = []
        print(cmd)
        words = cmd.split(' ')
        assert len(words) == 3, 'push/pop commands must have exactly 3 words.'
        command_type, mem_segment, address = words
        if command_type == 'push':
            if mem_segment == 'constant':
                lines.append(f'@{address}') # load constant
                lines.append('D=A') # hold constant in D
            elif mem_segment == 'static':
                lines.append(f'@{self.file_name}.{address}')
                lines.append('D=M')
            else:
                seg_base = base_seg_dict[mem_segment]
                lines.append(f'@{seg_base}') # get address of segment base
                if mem_segment in BASE_SEGMENTS:
                    lines.append('D=M')
                else:
                    lines.append('D=A')
                lines.append(f'@{address}') # get address within segment
                lines.append('A=D+A')
                lines.append('D=M') # get value at segment address
            lines.append('@SP') # access stack pointer
            lines.append('A=M') # point A to stack location
            lines.append('M=D') # set stack head to value
            lines.append('@SP') # access stack pointer again
            lines.append('M=M+1') # increment stack pointer
        else:
            assert command_type == 'pop', f'Command {command_type} not recognized.'
            lines.append('@SP')
            lines.append('AM=M-1') # get address of stack head and decrement stack head pointer
            lines.append('D=M') # get value at stack head
            if mem_segment == 'static':
                lines.append(f'@{self.file_name}.{address}')
            else:
                seg_base = base_seg_dict[mem_segment]
                lines.append(f'@{seg_base}')
                if mem_segment in BASE_SEGMENTS:
                    lines.append('A=M')
                for _ in range(int(address)):
                    lines.append('A=A+1')
            lines.append('M=D')
        self.outfile.write('\n'.join(lines) + '\n')

class Parser(object):
    def __init__(self, infile):
        with open(infile) as f:
            self.lines = f.readlines()
        self._process_commands()
        self.reset()

    def advance(self):
        assert self.has_more_commands()
        self.current_command = self.commands[self.command_counter]
        self.command_counter += 1

    def arg1(self):
        cur = self.current_command
        cmd_type = self.command_type()
        assert cmd_type != 'C_RETURN', '`arg1` should not be called with command `return`.'
        if cmd_type == 'C_ARITHMETIC':
            return cur
        else:
            args = re.split(r'\s', cur)
            return cur[1]

    def arg2(self):
        cur = self.current_command
        cmd_type = self.command_type()
        valid_cmd_types = ['C_PUSH', 'C_POP', 'C_FUNCTION', 'C_CALL']
        assert cmd_type in valid_cmd_types, f'Command `{cur}` not of type in {valid_cmd_types}.'
        args = re.split(r'\s', cur)
        return cur[2]

    def command_type(self):
        cur = self.current_command
        for op in VALID_ARITHMETIC:
            if op == cur:
                return 'C_ARITHMETIC'
        if cur.startswith('push '):
            return 'C_PUSH'
        elif cur.startswith('pop '):
            return 'C_POP'
        elif cur.startswith('label '):
            return 'C_LABEL'
        elif cur.startswith('goto '):
            return 'C_GOTO'
        elif cur.startswith('if-goto '):
            return 'C_IF'
        elif cur.startswith('function '):
            return 'C_FUNCTION'
        elif cur == 'return':
            return 'C_RETURN'
        elif cur.startswith('call '):
            return 'C_CALL'
        else:
            raise SyntaxError(f'Invalid command: {cur}')

    def has_more_commands(self):
        if self.command_counter >= self.n_commands:
            return False
        else:
            return True

    def _process_commands(self):
        commands = []
        for line in self.lines:
            line = line.strip()
            if '//' in line:
                index = line.find('//')
                line = line[:index]
            if not (line.startswith('//') or line == ''):
                commands.append(line)
        self.commands = commands
        self.n_commands = len(self.commands)

    def reset(self):
        self.command_counter = 0
        self.current_command = None
        self.line_number = 0

def check_infiles(infiles):
    if len(infiles) > 1:
        assert all(infile.endswith('.vm') for infile in infiles), 'All infiles must be .vm files.'
    elif not infiles[0].endswith('.vm'):
        assert os.path.isdir(infiles[0]), 'Infiles must be a directory or a list of .vm files.'
        infiles = glob(os.path.join(infiles[0], '*.vm'))
    return infiles

def main(infiles):
    infiles = check_infiles(infiles)
    print(f'Translating the following files: ', *infiles, sep='\n\t')
    outfile = infiles[0].replace('.vm', '.asm')
    code_writer = CodeWriter(outfile)
    for i, infile in enumerate(infiles):
        parser = Parser(infile)
        code_writer.set_file_name(infile)
        while parser.has_more_commands():
            parser.advance()
            print(parser.current_command)
            if parser.command_type() in ['C_PUSH', 'C_POP']:
                code_writer.write_push_pop(parser.current_command)
            elif parser.command_type() is 'C_ARITHMETIC':
                command_ix = f'{i}_{parser.command_counter}'
                code_writer.write_arithmetic(parser.current_command, command_ix)
    code_writer.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', nargs='+', help='File(s) or directory to translate.')
    args = parser.parse_args()
    main(args.infiles)
