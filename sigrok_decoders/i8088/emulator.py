class ModRM:
    def __init__(self, modrm_byte):
        self.byte = modrm_byte
        self.mod = (modrm_byte & 0b11000000) >> 6
        self.reg = (modrm_byte & 0b00111000) >> 3
        self.rm  =  modrm_byte & 0b00000111

    def decode(self):
        return {
            'mod': self.mod,
            'reg': self.reg,
            'rm': self.rm
        }

    def __str__(self):
        mod_str = "mod: {}".format(self.mod)
        reg_str = "reg/opcode: {}".format(self.reg)
        rm_str  = "r/m: {}".format(self.rm)

        return "{}, {}, {}".format(mod_str, reg_str, rm_str)

class Emulator:
    def __init__(self):
        self.opcode = 0

        self.cs_is_valid = False
        self._cs = 0
        self.ip = 0

    def execute(self, bytes, reads):
        '''
        Executes the given list of 'bytes' as an instruction, utilizing the list of 
        bytes 'reads' as memory read operands, if required.

        Returns: boolean representing whether the queue should be adjusted on return.
        '''
        if len(bytes) == 0:
            return False
        
        opcode = bytes[0]
        if opcode == 0x0E:
            # PUSH CS - no flow control, but exposes CS
            return False
        elif opcode == 0x9A or opcode == 0xEA:
            # CALLF / JMPF
            self.cs_is_valid = False

            if len(bytes) < 5:
                raise ValueError("{:02X} too short".format(opcode))
            
            # Read CS from immediate.
            self._cs = bytes[3] | (bytes[4] << 8)
            self.cs_is_valid = True
            return True
        elif opcode in [0xCC, 0xCD, 0xCE]:
            # INT3, INT, INTO
            self.cs_is_valid = False
            if len(reads) < 4:
                raise ValueError("int ivr failure")
            
            self._cs = reads[2] | (reads[3] << 8)
            self.cs_is_valid = True
            return True
        elif opcode == 0xCF:
            
            self.cs_is_valid = False
            # IRET
            if len(reads) < 6:
                raise ValueError("iret pop failure")

            self._cs = reads[2] | (reads[3] << 8)
            self.cs_is_valid = True
            return True
        elif opcode == 0xEA:
            # JMPF
            self.cs_is_valid = False
            return True
        
        elif opcode == 0xFF:
            # Group opcode. Need to parse modrm.
            if len(bytes) < 2:
                raise ValueError("group opcode with no modrm")
            
            # Get the opcode extension.
            op_ext = ModRM(bytes[1]).decode()['reg']

            if op_ext == 3 or op_ext == 5:
                # CALLF or JMPF
                self.cs_is_valid = False
                return True

        elif opcode in [0xC8, 0xC9, 0xCA, 0xCB]:
            # RETF of some sort
            self.cs_is_valid = False
            return True

        return False
    
    def interrupt(self, _iv, reads):

        if len(reads) < 4:
            raise ValueError("int with no isr address")

        self._cs = reads[2] | (reads[3] << 8)
        self.cs_is_valid = True

    def cs(self):
        if self.cs_is_valid:
            return self._cs
        else:
            return None
        