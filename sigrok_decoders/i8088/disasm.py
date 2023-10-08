

class Disassembler:
    def __init__(self):
        self.mnemonics = [
            ("ADD", 0),
            ("PUSH", 0),
            ("POP", 0),
            ("OR", 0),
            ("ADC", 0),
            ("SBB", 0),
            ("AND", 0),
            ("ES", 0),
            ("DAA", 0),
            ("SUB", 0),
            ("CS", 0),
            ("DAS", 0),
            ("XOR", 0),
            ("SS", 0),
            ("AAA", 0),
            ("CMP", 0),
            ("DS", 0),
            ("AAS", 0),
            ("INC", 0),
            ("DEC", 0),
            ("JO", 0),
            ("JNO", 0),
            ("JB", 0),
            ("JNB", 0),
            ("JZ", 0),
            ("JNZ", 0),
            ("JBE", 0),
            ("JNBE", 0),
            ("JS", 0),
            ("JNS", 0),
            ("JP", 0),
            ("JNP", 0),
            ("JL", 0),
            ("JNL", 0),
            ("JLE", 0),
            ("JNLE", 0),
            ("TEST", 0),
            ("XCHG", 0),
            ("MOV", 0),
            ("LEA", 0),
            ("CBW", 0),
            ("CWD", 0),
            ("CALLF", 0),
            ("PUSHF", 0),
            ("POPF", 0),
            ("SAHF", 0),
            ("LAHF", 0),
            ("MOVSB", 0),
            ("MOVSW", 0),
            ("CMPSB", 0),
            ("CMPSW", 0),
            ("STOSB", 0),
            ("STOSW", 0),
            ("LODSB", 0),
            ("LODSW", 0),
            ("SCASB", 0),
            ("SCASW", 0),
            ("RETN", 0),
            ("LES", 0),
            ("LDS", 0),
            ("RETF", 0),
            ("INT", 0),
            ("INTO", 0),
            ("IRET", 0),
            ("ROL", 0),
            ("ROR", 0),
            ("RCL", 0),
            ("RCR", 0),
            ("SHL", 0),
            ("SHR", 0),
            ("SAR", 0),
            ("AAM", 0),
            ("AMX", 0),
            ("AAD", 0),
            ("ADX", 0),
            ("XLAT", 0),
            ("LOOPNE", 0),
            ("LOOPE", 0),
            ("LOOP", 0),
            ("JCXZ", 0),
            ("IN", 0),
            ("OUT", 0),
            ("CALL", 0),
            ("JMP", 0),
            ("JMPF", 0),
            ("LOCK", 0),
            ("REPNZ", 0),
            ("REP", 0),
            ("REPZ", 0),
            ("HLT", 0),
            ("CMC", 0),
            ("NOT", 0),
            ("NEG", 0),
            ("MUL", 0),
            ("IMUL", 0),
            ("DIV", 0),
            ("IDIV", 0),
            ("CLC", 0),
            ("STC", 0),
            ("CLI", 0),
            ("STI", 0),
            ("CLD", 0),
            ("STD", 0),
            ("WAIT", 0),
            ("INVAL", 0),
            ("GRP1", 1),
            ("GRP2A", 2),
            ("GRP3", 3),
            ("GRP4", 4),
            ("GRP5", 5),
            ("GRP2B", 6),
            ("NOP", 0),
        ]
        self.grp_mnemonics = [
            [
                "ADD",
                "OR",
                "ADC",
                "SBB",
                "AND",
                "SUB",
                "XOR",
                "CMP"
            ],[ 
                "ROL",
                "ROR",
                "RCL",
                "RCR",  
                "SHL",
                "SHR",
                "SETMO",
                "SAR"
            ],[
                "ROL",
                "ROR",
                "RCL",
                "RCR",
                "SHL",
                "SHR",
                "SETMOC",
                "SAR"
            ],[
              "TEST",
              "TEST",
              "NOT",
              "NEG",
              "MUL",
              "IMUL",
              "DIV",
              "IDIV",
            ],[
                "INC",
                "DEC",
                "INVAL",
                "INVAL",
                "INVAL",
                "INVAL",
                "INVAL",
                "INVAL"
            ],[
                "INC",
                "DEC",
                "CALL",
                "CALLF",
                "JMP",
                "JMPF",
                "PUSH",
                "INVAL"
            ]
        ]

        self.opcode_refs = [
            0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 3, 3, 3, 3, 1, 2,
            4, 4, 4, 4, 4, 4, 1, 2, 5, 5, 5, 5, 5, 5, 1, 2,
            6, 6, 6, 6, 6, 6, 7, 8, 9, 9, 9, 9, 9, 9, 10, 11, 
            12, 12, 12, 12, 12, 12, 13, 14, 15, 15, 15, 15, 15, 15, 16, 17,
            18, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 19, 19,
            1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2,
            20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
            20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
            105, 105, 105, 105, 36, 36, 37, 37, 38, 38, 38, 38, 38, 39, 38, 2,
            111, 37, 37, 37, 37, 37, 37, 37, 40, 41, 42, 103, 43, 44, 45, 46,
            38, 38, 38, 38, 47, 48, 49, 50, 36, 36, 51, 52, 53, 54, 55, 56,
            38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38, 38,
            57, 57, 57, 57, 58, 59, 38, 38, 60, 60, 60, 60, 61, 61, 62, 63,
            106, 106, 110, 110, 71, 73, 104, 75, 104, 104, 104, 104, 104, 104, 104, 104,
            76, 77, 78, 79, 80, 80, 81, 81, 82, 83, 84, 83, 80, 80, 81, 81,
            85, 104, 86, 87, 89, 90, 107, 107, 97, 98, 99, 100, 101, 102, 108, 109 
        ]

    def lookup_opcode(self, byte, modrm=None):
        if not (isinstance(byte, int) and 0 <= byte <= 255):
            raise ValueError("Expected a byte (0-255), got: {}".format(byte))

        op_tuple = self.mnemonics[self.opcode_refs[byte]]

        if op_tuple[1] > 0:
            # Group opcode.
            if modrm is None:
                raise ValueError("Group opcode with no modrm")
            
            op_ext = (modrm >> 3) & 0x07
            return self.grp_mnemonics[op_tuple[1]-1][op_ext]    
        else:
            return op_tuple[0]
        
    def disassemble(self, code_bytes):
        if len(code_bytes) == 0:
            return "nul"
        elif len(code_bytes) == 1:
            return self.lookup_opcode(code_bytes[0])
        else:
            return self.lookup_opcode(code_bytes[0], code_bytes[1])