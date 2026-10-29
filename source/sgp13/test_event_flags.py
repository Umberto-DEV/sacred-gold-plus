"""Class A: compiled high-bank getter/load guard; native services are seams.

Private-cartridge native Check/Set/Clear and overlay36 integration are Class B
in test_event_flags_rom. These tests contain only our code and synthetic data.
"""
import struct
import tempfile
import unittest
from sgp13 import event_flags

STATE, SAVE, STOP, STACK, DELEGATE = 0x02280000, 0x02290000, 0x023EF000, 0x023FF000, 0x023D1000


class Runtime:
    def __init__(self, blob, symbols):
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
        from unicorn import arm_const as reg
        self.reg = reg
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.mu.mem_map(0x02000000, 0x400000)
        self.mu.mem_write(event_flags.BASE, blob)
        self.mu.mem_write(event_flags.CONFIG, struct.pack('<I', DELEGATE | 1))
        self.symbols, self.events, self.writes = symbols, [], []
        self.result, self.reload = 1, None
        self.mu.hook_add(UC_HOOK_CODE, self.hook)
        self.mu.hook_add(UC_HOOK_MEM_WRITE, self.write)

    def write(self, uc, access, address, size, value, user):
        if STATE <= address < STATE + 0x1000:
            self.writes.append((address, size, value))

    def hook(self, uc, address, size, user):
        a, b = [uc.reg_read(r) for r in (self.reg.UC_ARM_REG_R0, self.reg.UC_ARM_REG_R1)]
        if address == 0x020D3B84:
            assert a == 0
            self.events.append('reset'); self.mu.emu_stop(); return
        if address == 0x020272C8:
            assert (a, b) == (SAVE, 4)
            result = STATE
        elif address == DELEGATE:
            assert a == SAVE
            self.events.append('load')
            if self.reload is not None: self.mu.mem_write(STATE, self.reload)
            result = self.result
        else:
            return
        uc.reg_write(self.reg.UC_ARM_REG_R0, result)
        uc.reg_write(self.reg.UC_ARM_REG_PC, uc.reg_read(self.reg.UC_ARM_REG_LR))

    def call(self, name, *args):
        for i in range(4): self.mu.reg_write(getattr(self.reg, 'UC_ARM_REG_R'+str(i)), args[i] if i < len(args) else 0)
        self.mu.reg_write(self.reg.UC_ARM_REG_SP, STACK)
        self.mu.reg_write(self.reg.UC_ARM_REG_LR, STOP | 1)
        self.mu.emu_start(self.symbols[name], STOP, count=10000)
        if self.events[-1:] != ['reset']:
            assert self.mu.reg_read(self.reg.UC_ARM_REG_PC) == STOP
            assert self.mu.reg_read(self.reg.UC_ARM_REG_SP) == STACK
        return self.mu.reg_read(self.reg.UC_ARM_REG_R0)

    def read(self):
        return bytes(self.mu.mem_read(STATE, 0x1000))


class EventFlags(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='event-flags-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.blob, cls.symbols = event_flags.compile_native(cls.temp.name)

    def test_complete_legacy_snapshot_tag_published_last_and_correct_pointer(self):
        for flag in range(0x3F00, 0x4000):
            m = Runtime(self.blob, self.symbols)
            before = bytearray((i * 37 + 11) % 256 for i in range(0x1000))
            before[0x2BC:0x2E0] = bytes(36)
            m.mu.mem_write(STATE, bytes(before))
            self.assertEqual(m.call('sgp_event_flags_get', STATE, flag), STATE + 0x2C0 + (flag - 0x3F00) // 8)
            expected = bytearray(before)
            expected[0x2BC:0x2E0] = b'HF01' + before[0xAC0:0xAE0]
            self.assertEqual(m.read(), expected)
            self.assertEqual(m.writes[-1], (STATE + 0x2BC, 4, 0x31304648))
            self.assertEqual(len(m.writes), 33)
            m.writes.clear()
            m.mu.mem_write(STATE + 0xAC0, bytes(32))
            m.call('sgp_event_flags_get', STATE, flag)
            self.assertEqual(m.writes, [])
            self.assertEqual(m.read()[0x2BC:0x2E0], expected[0x2BC:0x2E0])

    def test_foreign_tail_and_future_version_are_readonly_refusals(self):
        for offset in range(36):
            m = Runtime(self.blob, self.symbols)
            m.mu.mem_write(STATE + 0x2BC + offset, b'X')
            before = m.read()
            self.assertEqual(m.call('sgp_event_flags_valid', STATE), 0)
            m.call('sgp_event_flags_get', STATE, 0x3FC8)
            self.assertEqual(m.events, ['reset'])
            self.assertEqual(m.read(), before)
            self.assertEqual(m.writes, [])
        for tag in (b'HF02', b'HF00', b'FORE'):
            m = Runtime(self.blob, self.symbols)
            m.mu.mem_write(STATE + 0x2BC, tag)
            self.assertEqual(m.call('sgp_event_flags_load', SAVE), 0)
            self.assertEqual(m.events, [])
            self.assertEqual(m.writes, [])

    def test_reload_is_checked_and_failure_is_propagated_without_migration(self):
        for tag, result, expected in ((b'HF01', 1, 1), (bytes(4), 1, 1),
                                       (b'HF02', 1, 0), (b'FORE', 1, 0), (bytes(4), 0, 0)):
            m = Runtime(self.blob, self.symbols)
            m.reload = bytes(0x2BC) + tag + bytes(0x1000 - 0x2C0)
            m.result = result
            self.assertEqual(m.call('sgp_event_flags_load', SAVE), expected)
            self.assertEqual(m.events, ['load'])
            self.assertEqual(m.writes, [])
            self.assertEqual(m.read(), m.reload)

    def test_archive_reservation_guard_catches_all_allocated_ids_at_any_alignment(self):
        for variable in range(0x415E, 0x4170):
            for alignment in (0, 1):
                with self.assertRaisesRegex(ValueError, 'reservation'):
                    event_flags.guard_archive_members('synthetic', [bytes(4), bytes(alignment) + struct.pack('<H', variable)])
        event_flags.guard_archive_members('synthetic', [b'', b'X', struct.pack('<HH', 0x415D, 0x4170)])


if __name__ == '__main__':
    unittest.main()
