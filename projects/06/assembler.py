import sys
import os

class Parser:
    def __init__(self, filename):
        self.file = open(f"{filename}", "r")
    
    def hasMoreLines(self, line):
        return line
    
    # Reads the next instruction from the input, and makes it the current instruction
    def advance(self):
        line = self.file.readline().strip()
        if (not line):
            line = line = self.file.readline().strip()
        return line

    # Returns the type of the current instruction
    def instructionType(self, instruction):
        if (instruction[0] == '@'):
            return "A_INSTRUCTION"
        if (instruction[0] == '(' and instruction[-1] == ')'):
            return "L_INSTRUCTION"
        return "C_INSTRUCTION"
    
    # If the current instruction is (xxx), returns the symbol xxx
    # If the current instruction is @xxx, returns the symbol or decimal xxx (as string)
    def symbol(self, instruction):
        return instruction.strip("@()")
    
    #Returns the symbolic dest part of the current
    def dest(self, instruction):
        if ('=' in instruction):
            line = instruction.split('=')[0]
            return line
        return "null"
    
    # Returns the symbolic comp part of the current C-instruction
    def comp(self, instruction):
        if (';' in instruction):
            line = instruction.split(';')[0]
            if ('=' in line):
                line = line.split('=')[1]
            return line
        if ('=' in instruction):
            line = instruction.split('=')[1]
            return line
        return ""
    
    # Returns the symbolic jump part of the current C-instruction
    def jump(self, instruction):
        if (';' in instruction):
            return instruction.split(';')[1]
        return "null"
    
class Code:
    c_table = {'0': "0101010",
               '1': "0111111",
               '-1': "0111010",
               'D': "0001100", 
               'A': "0110000", 'M': "1110000",
               '!D': "0001101",
               '!A': "0110001", '!M': "1110001",
               '-D': "0001111",
               '-A': "0110011", '-M': "1110011",
               'D+1': "0011111",
               'A+1': "0110111", 'M+1': "1110111",
               'D-1': "0001110",
               'A-1': "0110010", 'M-1': "1110010",
               'D+A': "0000010", 'D+M': "1000010",
               'D-A': "0010011", 'D-M': "1010011",
               'A-D': "0000111", 'M-D': "1000111",
               'D&A': "0000000", 'D&M': "1000000",
               'D|A': "0010101", 'D|M': "1010101"}
    
    d_table = {'null': "000", 'M': "001", 'D': "010", 'DM': "011",
               'A': "100", 'AM': "101", 'AD': "110", 'ADM': "111",
               'MD': "011", 'MA': "101", 'DA': "110"}
    
    j_table = {'null': "000", 'JGT': "001", 'JEQ': "010", 'JGE': "011",
               'JLT': "100", 'JNE': "101", 'JLE': "110", 'JMP': "111"}
    
    # Returns the binary code of the dest mnemonic
    def dest(self, instruction):
        return self.d_table[instruction] 

    # Returns the binary code of the comp mnemonic
    def comp(self, instruction):
        return self.c_table[instruction]

    # Returns the binary code of the jump mnemonic
    def jump(self, instruction):
        return self.j_table[instruction]

class SymbolTable:
    def __init__(self):
        self.symtable = {'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4,
                         'R5': 5, 'R6': 6, 'R7': 7, 'R8': 8, 'R9': 9,
                         'R10': 10, 'R11': 11, 'R12': 12, 'R13': 13,
                         'R14': 14, 'R15': 15,
                         'SCREEN': 16384, 'KBD': 24576, 'SP': 0, 'LCL': 1,
                         'ARG': 2, 'THIS': 3, 'THAT': 4, 'LOOP': 4, 'STOP': 18}
    
    # Adds <symbol,address> to the table (dictionary/hashmap)
    def addEntry(self, symbol, address):
        self.symtable[symbol] = address
    
    # Does the symbol table contain the given symbol?
    def contains(self, symbol):
        return symbol in self.symtable
    
    # Returns the address associated with the symbol
    def getAddress(self, symbol):
        return self.symtable[symbol]

class HackAssembler:
    def __init__(self, filename):
        self.parser = Parser(filename)
        self.code = Code()
        self.symboltable = SymbolTable()
        self.name = os.path.splitext(filename)[0]
        self.output = open(f"{self.name}.hack", "w")

    # Adds labels to our symbol table for first pass
    def add_labels(self):
        line_num = -1
        while line := self.parser.advance():
            if (line[0] != '/' and self.parser.instructionType(line) == "L_INSTRUCTION"):
                label = self.parser.symbol(line)
                self.symboltable.addEntry(label, line_num+1)
            elif (line[0] != '/'):
                line_num += 1

    def assemble(self):
        variable_address = 16
        while line := self.parser.advance():
            if (line[0] != '/'):
                # Remove any comments and whitespace on the same line as the code
                line = line.split("//")[0].strip()
                line_type = self.parser.instructionType(line)

                if (line_type == "A_INSTRUCTION"):
                    instruction = self.parser.symbol(line)
                    if not instruction.isnumeric() and not self.symboltable.contains(instruction):
                        self.symboltable.addEntry(instruction, variable_address)
                        variable_address += 1
                    if self.symboltable.contains(instruction):
                        instruction = self.symboltable.getAddress(instruction)
                    self.output.write("{0:016b}".format(int(instruction)) + '\n')

                elif (line_type == "C_INSTRUCTION"):
                    dest = self.parser.dest(line)
                    comp = self.parser.comp(line)
                    jump = self.parser.jump(line)
                    instruction = "111" + self.code.comp(comp) + self.code.dest(dest) + self.code.jump(jump) + '\n'
                    self.output.write(instruction)
                else:
                    continue

    def reset(self):
        self.parser.file.seek(0)

    def close(self):
        self.parser.file.close()
        self.output.close()

def main():
    n = len(sys.argv)
    if (n != 2):
        print("Usage: assember.py asm_file")
        return 1
    if (".asm" not in sys.argv[1]):
        print("Usage: assember.py asm_file")
        return 2
    
    hack = HackAssembler(sys.argv[1])

    # First Pass
    hack.add_labels()
    # Go back to top of file
    hack.reset()
    # Second Pass
    hack.assemble()
    # Close files
    hack.close()
    return 0

if __name__ == "__main__":
    main()
