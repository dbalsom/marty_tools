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
        mod_str = f"mod: {self.mod}"
        reg_str = f"reg/opcode: {self.reg}"
        rm_str  = f"r/m: {self.rm}"

        return f"{mod_str}, {reg_str}, {rm_str}"

class Emulator:
    def __init__(self):
        self.opcode = 0

        self.cs_is_valid = False
        self.cs = 0
        self.ip = 0

    def execute(self, bytes):
        if len(bytes) == 0:
            return
        
        opcode = bytes[0]

        if opcode == 0x9A or opcode == 0xEA:
            # CALLF / JMPF
            self.cs_is_valid = False

            if len(bytes) < 5:
                raise ValueError("{:02X} too short".format(opcode))
            
            # Read CS from immediate.
            self.cs = bytes[3] | (bytes[4] << 8)
            self.cs_is_valid = True
            
        if opcode in [0xCC, 0xCD, 0xCE]:
            # INT3, INT, INTO
            self.cs_is_valid = False
        if opcode == 0xCF:

            self.cs_is_valid = False
        if opcode == 0xEA:
            # JMPF
            self.cs_is_valid = False
        
        if opcode == 0xFF:
            # Group opcode. Need to parse modrm.
            if len(bytes) < 2:
                raise ValueError("group opcode with no modrm")
            
            # Get the opcode extension.
            op_ext = ModRM(bytes[1]).decode()['reg']

            if op_ext == 3 or op_ext == 5:
                # CALLF or JMPF
                self.cs_is_valid = False

        if opcode in [0xC8, 0xC9, 0xCA, 0xCB]:
            # RETF of some sort
            self.cs_is_valid = False

    def cs(self):
        return (self.cs_is_valid, self.cs)