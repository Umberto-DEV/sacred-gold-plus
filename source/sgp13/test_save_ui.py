"""Class A: execute original compiled callbacks with native ABI seams."""
from pathlib import Path
import struct
import tempfile
import unittest

from sgp13 import save_ui

DATA = 0x02280000
INPUT = 0x021d110c
STACK = 0x023ff000
STOP = 0x023ef000


class Callbacks:
    def __init__(self, blob, symbols, result=0):
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn import arm_const as reg
        self.reg = reg
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.mu.mem_map(0x02000000, 0x400000)
        self.mu.mem_write(0x0225dce8, blob)
        self.symbols = symbols
        self.result = result
        self.events = []
        self.put(DATA + 0x1c, DATA + 0x100)
        self.put(DATA + 0x38, DATA + 0x200)
        self.put(DATA + 0x44, DATA + 0x300)
        self.put(DATA + 0x64, DATA + 0x400)
        self.put(DATA + 0x68, DATA + 0x500)
        self.mu.hook_add(UC_HOOK_CODE, self.hook)

    def put(self, address, value):
        self.mu.mem_write(address, struct.pack('<I', value))

    def get(self, address):
        return struct.unpack('<I', self.mu.mem_read(address, 4))[0]

    def hook(self, uc, address, size, user):
        addresses = {0x021f43e8: 'save', 0x021f2ff0: 'movement', 0x0200f450: 'icon',
                     0x0201d978: 'fill', 0x0200bba0: 'message',
                     0x0202ad3c: 'delay', 0x020200a8: 'print'}
        if address not in addresses:
            return
        args = tuple(uc.reg_read(r) for r in (self.reg.UC_ARM_REG_R0,
                     self.reg.UC_ARM_REG_R1, self.reg.UC_ARM_REG_R2, self.reg.UC_ARM_REG_R3))
        sp = uc.reg_read(self.reg.UC_ARM_REG_SP)
        assert sp % 8 == 0, 'native call stack must be eight-byte aligned'
        self.events.append((addresses[address], args, struct.unpack('<III', uc.mem_read(sp, 12))))
        value = {'save': self.result, 'message': DATA + 0x600, 'delay': 7, 'print': 99}.get(addresses[address], 0)
        uc.reg_write(self.reg.UC_ARM_REG_R0, value)
        uc.reg_write(self.reg.UC_ARM_REG_PC, uc.reg_read(self.reg.UC_ARM_REG_LR))

    def call(self, name):
        self.mu.reg_write(self.reg.UC_ARM_REG_R0, DATA)
        self.mu.reg_write(self.reg.UC_ARM_REG_SP, STACK)
        self.mu.reg_write(self.reg.UC_ARM_REG_LR, STOP | 1)
        self.mu.reg_write(self.reg.UC_ARM_REG_R4, 0x44444444)
        self.mu.reg_write(self.reg.UC_ARM_REG_R5, 0x55555555)
        self.mu.reg_write(self.reg.UC_ARM_REG_R6, 0x66666666)
        self.mu.reg_write(self.reg.UC_ARM_REG_R7, 0x77777777)
        for number in (8, 9, 10, 11):
            self.mu.reg_write(getattr(self.reg, 'UC_ARM_REG_R' + str(number)), number * 0x11111111)
        self.mu.emu_start(self.symbols[name], STOP, count=10000)
        assert self.mu.reg_read(self.reg.UC_ARM_REG_PC) == STOP
        assert self.mu.reg_read(self.reg.UC_ARM_REG_SP) == STACK
        for register, expected in ((self.reg.UC_ARM_REG_R4, 0x44444444),
                                   (self.reg.UC_ARM_REG_R5, 0x55555555),
                                   (self.reg.UC_ARM_REG_R6, 0x66666666),
                                   (self.reg.UC_ARM_REG_R7, 0x77777777)):
            assert self.mu.reg_read(register) == expected
        for number in (8, 9, 10, 11):
            assert self.mu.reg_read(getattr(self.reg, 'UC_ARM_REG_R' + str(number))) == number * 0x11111111
        return self.mu.reg_read(self.reg.UC_ARM_REG_R0)

    def input(self, held=0, edge=0, touch=0, touch_edge=0):
        self.put(INPUT + 0x44, held)
        self.put(INPUT + 0x48, edge)
        self.mu.mem_write(INPUT + 0x64, struct.pack('<HH', touch_edge, touch))


class SaveUiCallbacks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='sgp-save-ui-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.blob, cls.symbols = save_ui.compile_native(cls.temp.name)

    def test_native_bool_selects_failure_or_success_without_other_data_mutation(self):
        for result, expected in ((0, 16), (1, 13)):
            with self.subTest(result=result):
                b = Callbacks(self.blob, self.symbols, result)
                before = bytearray(b.mu.mem_read(DATA, 0x6c))
                self.assertEqual(b.call('sgp_saveui_save'), 0)
                struct.pack_into('<I', before, 12, expected)
                self.assertEqual(bytes(b.mu.mem_read(DATA, 0x6c)), bytes(before))
                self.assertEqual([event[0] for event in b.events], ['save'])
                self.assertEqual(b.events[0][1][0], DATA + 0x100)

    def test_failure_retires_resources_and_prints_owned_string_with_native_abi(self):
        b = Callbacks(self.blob, self.symbols)
        self.assertEqual(b.call('sgp_saveui_failure'), 0)
        self.assertEqual([event[0] for event in b.events],
                         ['movement', 'icon', 'fill', 'message', 'delay', 'print'])
        self.assertEqual(b.events[0][1][0], DATA + 0x500)
        self.assertEqual(b.events[1][1][0], DATA + 0x400)
        self.assertEqual(b.events[3][1][:2], (DATA + 0x200, 117))
        self.assertEqual(b.events[-1][1], (DATA + 0x4c, 1, DATA + 0x600, 0))
        self.assertEqual(b.events[-1][2], (0, 7, 0))
        self.assertEqual([b.get(DATA + offset) for offset in (12, 16, 20, 0x5c, 0x60, 0x64, 0x68)],
                         [2, 17, 0, DATA + 0x600, 99, 0, 0])

    def test_ack_requires_release_fresh_a_b_or_touch_and_final_release(self):
        for button in ('A', 'B', 'touch'):
            with self.subTest(button=button):
                b = Callbacks(self.blob, self.symbols)
                for _ in range(80):
                    b.input(held=3, edge=3, touch=1, touch_edge=1)
                    self.assertEqual(b.call('sgp_saveui_ack'), 0)
                self.assertEqual(b.get(DATA + 20), 0)
                b.input()
                self.assertEqual(b.call('sgp_saveui_ack'), 0)
                self.assertEqual(b.get(DATA + 20), 1)
                for _ in range(80):
                    b.input(held=0x400, edge=0x400)
                    self.assertEqual(b.call('sgp_saveui_ack'), 0)
                self.assertEqual(b.get(DATA + 20), 1)
                b.input(held=1 if button == 'A' else 2 if button == 'B' else 0,
                        edge=1 if button == 'A' else 2 if button == 'B' else 0,
                        touch=int(button == 'touch'), touch_edge=int(button == 'touch'))
                self.assertEqual(b.call('sgp_saveui_ack'), 0)
                self.assertEqual(b.get(DATA + 20), 2)
                for _ in range(40):
                    self.assertEqual(b.call('sgp_saveui_ack'), 0)
                b.input()
                self.assertEqual(b.call('sgp_saveui_ack'), 1)
                self.assertEqual(b.events, [])

    def test_append_retains_existing_message_ids_and_encrypted_payloads(self):
        from translation.message_codec import Bank
        original = Bank.from_words([[0x12b + i % 26, 65535] for i in range(117)], 53262).save()
        result = save_ui.append_message(original, [0x13d, 0xe000, 0x145, 65535])
        self.assertEqual(Bank(result).words[:117], Bank(original).words)
        self.assertEqual(len(Bank(result).words), 118)
        for index in range(117):
            key = (765 * (index + 1) * 53262) & 65535
            key |= key << 16
            old_off, old_size = struct.unpack_from('<II', original, 4 + index * 8)
            new_off, new_size = struct.unpack_from('<II', result, 4 + index * 8)
            self.assertEqual(old_size ^ key, new_size ^ key)
            n = (old_size ^ key) * 2
            self.assertEqual(original[old_off ^ key:(old_off ^ key) + n],
                             result[new_off ^ key:(new_off ^ key) + n])
        with self.assertRaisesRegex(ValueError, 'preimage'):
            save_ui.append_message(result, [65535])


if __name__ == '__main__':
    unittest.main()
