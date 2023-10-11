
import unittest
from disasm import Disassembler

class TestIntel8088Disassembler(unittest.TestCase):

    def setUp(self):
        self.disassembler = Disassembler()

    def test_decode(self):

        for i in range(255):

            instruction_bytes = [i, 4]
            result = self.disassembler.disassemble(instruction_bytes)
            print("{:02X}:{}".format(i, result))

    def test_NOP_instruction(self):
        instruction_bytes = [0x90]
        result = self.disassembler.disassemble(instruction_bytes)
        self.assertEqual(result, "NOP")

if __name__ == "__main__":
    unittest.main()


