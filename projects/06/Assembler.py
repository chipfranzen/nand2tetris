#!/usr/bin/env python3
import argparse

class Parser(object):
    def __init__(self, infile):
        with open(infile) as f:
            self.lines = f.readlines()
        self._process_commands()
        self.reset()
        self.valid_dests = ['M', 'D', 'MD', 'A', 'AM', 'AD', 'ADM']
        self.valid_comps = ['0', '1', '-1', 'D', 'A', '!D', '!A', '-D', '-A', 'D+1', 'A+1', 'D-1',
                            'A-1', 'D+A', 'D-A', 'A-D', 'D&A', 'D|A', 'M', '!M', '-M', 'M+1',
                            'M-1', 'D+M', 'D-M', 'M-D', 'D&M', 'D|M']
        self.valid_jump_comps = ['0', 'D']

    def advance(self):
        self.current_command = self.commands[self.command_counter]
        self.command_counter += 1
        if self.command_type() is not 'L_COMMAND':
            self.line_number += 1

    def command_type(self):
        if self.current_command.startswith('@'):
            return 'A_COMMAND'
        elif self.current_command.startswith('('):
            return 'L_COMMAND'
        else:
            return 'C_COMMAND'

    def comp(self):
        assert self.command_type() is 'C_COMMAND', 'comp() only valid with C_COMMAND'
        cmd = self.current_command
        if '=' not in cmd:
            comp = cmd.split(';')[0]
            assert comp in self.valid_jump_comps, 'For jmp commands, comparison must be D or 0'
            return comp
        else:
            comp = cmd.split('=')[1]
            assert comp in self.valid_comps, f'Invalid computation {comp}. Must be in {self.valid_comps}.'
            return comp

    def dest(self):
        assert self.command_type() is 'C_COMMAND', 'dest() only valid with C_COMMAND'
        cmd = self.current_command
        if '=' not in cmd:
            return None
        else:
            dest = cmd.split('=')[0]
            assert dest in self.valid_dests, f'Invalid destination {dest}. Must be in {self.valid_dests}.'
            return dest

    def jump(self):
        assert self.command_type() is 'C_COMMAND', 'jump() only valid with C_COMMAND'
        cmd = self.current_command
        if '='in cmd:
            return None
        else:
            jmp = cmd.split(';')[1]
            return jmp

    def has_more_commands(self):
        if self.command_counter >= self.n_commands:
            return False
        else:
            return True

    def _process_commands(self):
        commands = []
        for line in self.lines:
            line = line.strip()
            if ' ' in line:
                index = line.find(' ')
                line = line[:index]
            if not (line.startswith('//') or line == ''):
                commands.append(line)
        self.commands = commands
        self.n_commands = len(self.commands)

    def reset(self):
        self.command_counter = 0
        self.current_command = None
        self.line_number = 0

    def symbol(self):
        assert self.command_type() is not 'C_COMMAND', f'Command {self.current_command} is a C_COMMAND. Cannot call `symbol()`'
        return self.current_command.strip('@()')

class SymbolTable(object):
    def __init__(self):
        self.table = {
                'SP': 0,
                'LCL': 1,
                'ARG': 2,
                'THIS': 3,
                'THAT': 4,
                'SCREEN': 16384,
                'KBD': 24567
                }
        for i in range(16):
            I = str(i)
            self.table['R' + I] = i
        self.next_address = 16

    def add_entry(self, symbol, address):
        self.table[symbol] = address

    def contains(self, symbol):
        if symbol in self.table.keys():
            return True
        else:
            return False

    def get_address(self, symbol):
        if self.contains(symbol):
            return self.table[symbol]
        else:
            symbol_address = self.next_address
            self.table[symbol] = symbol_address
            self.next_address += 1
            return symbol_address

# comp module
def comp(mnemonic):
    comp_dict = {
            '0': '0101010',
            '1': '0111111',
            '-1': '0111010',
            'D': '0001100',
            'A': '0110000',
            'M': '1110000',
            '!D': '0001101',
            '!A': '0110001',
            '!M': '1110001',
            '-D': '0001111',
            '-A': '0110011',
            '-M': '1110011',
            'D+1': '0011111',
            'A+1': '0110111',
            'M+1': '1110111',
            'D-1': '0001110',
            'A-1': '0110010',
            'M-1': '1110010',
            'D+A': '0000010',
            'D+M': '1000010',
            'D-A': '0010011',
            'D-M': '1010011',
            'A-D': '0000111',
            'M-D': '1000111',
            'D&A': '0000000',
            'D&M': '1000000',
            'D|A': '0010101',
            'D|M': '1010101'
            }
    return comp_dict[mnemonic]

def dest(mnemonic):
    bits = ['0', '0', '0']
    if mnemonic is None:
        return ''.join(bits)
    if 'A' in mnemonic:
        bits[0] = '1'
    if 'D' in mnemonic:
        bits[1] = '1'
    if 'M' in mnemonic:
        bits[2] = '1'
    return ''.join(bits)

def jump(mnemonic):
    jump_dict = {
            None: '000',
            'JGT': '001',
            'JEQ': '010',
            'JGE': '011',
            'JLT': '100',
            'JNE': '101',
            'JLE': '110',
            'JMP': '111'
            }
    return jump_dict[mnemonic]

# misc funcs
def address_to_instruction(address):
    return bin(int(address))[2:].rjust(16, '0')

def main(infile):
    assert '.asm' in infile, 'Filetype not recognized. Should be `.asm` Hack assembly program.'
    parser = Parser(infile)
    sym_table = SymbolTable()
    # first pass
    while parser.has_more_commands():
        parser.advance()
        if parser.command_type() == 'L_COMMAND':
            sym = parser.symbol()
            sym_table.add_entry(sym, parser.line_number)
    print(sym_table.table)

    # second pass
    parser.reset()
    outlines = []
    while parser.has_more_commands():
        parser.advance()
        print(f'\ncommand: {parser.command_counter}\nline: {parser.line_number}')
        print(parser.current_command, parser.command_type())
        if parser.command_type() is not 'C_COMMAND':
            print(f'\t{parser.symbol()}')
            if parser.command_type() is 'A_COMMAND':
                sym = parser.symbol()
                try:
                    address = int(sym)
                except ValueError:
                    address = sym_table.get_address(sym)
                instruction = address_to_instruction(address)
                outlines.append(instruction)
        else:
            print(f'\tdest: {parser.dest()}\n\tcomp: {parser.comp()}\n\tjump: {parser.jump()}')
            c1 = comp(parser.comp())
            c2 = dest(parser.dest())
            c3 = jump(parser.jump())
            instruction = '111' + c1 + c2 + c3
            outlines.append(instruction)
    outfile = infile.replace('.asm', '.hack')
    print(*outlines, sep='\n')
    with open(outfile, mode='w') as f:
        f.writelines('\n'.join(outlines) + '\n')
    print(f'wrote to {outfile}')

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('infile', help='File to translate from assembly.')
    args = arg_parser.parse_args()
    main(args.infile)
