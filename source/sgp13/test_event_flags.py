"""Class A: compiled event storage; native services are explicit seams.

Private-cartridge native Check/Set/Clear, script/coordinate consumers and the
Continue caller are Class B in test_event_flags_rom. These tests contain only
our code and synthetic data.
"""
import struct
import tempfile
import unittest
from sgp13 import event_flags
from sgp131.test_ui import nonproduction_native_compiler_contract

STATE, SAVE, CHATOT = 0x02280000, 0x02290000, 0x022A0000
STOP, STACK, DELEGATE = 0x023EF000, 0x023FF000, 0x023D1000
FAMILY_IDS = tuple(range(0x612E, 0x613A)) + tuple(range(0x619E, 0x61AA))
FAMILY_FLAGS = (0x3F03, 0x3F06, 0x3F07, 0x3F09, 0x3F0A, 0x3F0B,
                0x3F0C, 0x3F0D, 0x3F0E, 0x3F0F, 0x3F10, 0x3F11,
                0x3F12, 0x3F13, 0x3F14, 0x3F15, 0x3F16, 0x3F17,
                0x3F1D, 0x3F1E, 0x3F1F, 0x3F26, 0x3F27, 0x3F28)
CHATOT_OFFSETS = tuple(range(0x1CC, 0x1E4, 2)) + tuple(range(0x2AC, 0x2C4, 2))


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
        self.result, self.reload, self.reload_chatot = 1, None, None
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
            assert a == SAVE and b in (4, 18)
            result = STATE if b == 4 else CHATOT
        elif address == DELEGATE:
            assert a == SAVE
            self.events.append('load')
            if self.reload is not None:
                self.mu.mem_write(STATE, self.reload)
            if self.reload_chatot is not None:
                self.mu.mem_write(CHATOT, self.reload_chatot)
            result = self.result
        else:
            return
        uc.reg_write(self.reg.UC_ARM_REG_R0, result)
        uc.reg_write(self.reg.UC_ARM_REG_PC, uc.reg_read(self.reg.UC_ARM_REG_LR))

    def call(self, name, *args):
        for i in range(4):
            self.mu.reg_write(getattr(self.reg, 'UC_ARM_REG_R' + str(i)), args[i] if i < len(args) else 0)
        self.mu.reg_write(self.reg.UC_ARM_REG_SP, STACK)
        self.mu.reg_write(self.reg.UC_ARM_REG_LR, STOP | 1)
        self.mu.emu_start(self.symbols[name], STOP, count=10000)
        if self.events[-1:] != ['reset']:
            assert self.mu.reg_read(self.reg.UC_ARM_REG_PC) == STOP
            assert self.mu.reg_read(self.reg.UC_ARM_REG_SP) == STACK
        return self.mu.reg_read(self.reg.UC_ARM_REG_R0)

    def read(self):
        return bytes(self.mu.mem_read(STATE, 0x1000))

    def chatot(self):
        return bytes(self.mu.mem_read(CHATOT, 1004))


def expected_bank(legacy, chatot):
    bank = bytearray(legacy)
    for flag, offset in zip(FAMILY_FLAGS, CHATOT_OFFSETS):
        byte, bit = divmod(flag - 0x3F00, 8)
        if struct.unpack_from('<H', chatot, offset)[0]:
            bank[byte] |= 1 << bit
        else:
            bank[byte] &= ~(1 << bit)
    return bytes(bank)


class EventFlags(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        host = nonproduction_native_compiler_contract(event_flags)
        host.__enter__()
        cls.addClassCleanup(host.__exit__, None, None, None)
        cls.temp = tempfile.TemporaryDirectory(prefix='event-flags-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.blob, cls.symbols = event_flags.compile_native(cls.temp.name)

    def test_new_game_lazy_snapshot_clears_family_bits_and_publishes_v2_last(self):
        m = Runtime(self.blob, self.symbols)
        before = bytearray((i * 37 + 11) % 256 for i in range(0x1000))
        before[0x2BC:0x2E0] = bytes(36)
        m.mu.mem_write(STATE, bytes(before))
        self.assertEqual(m.call('sgp_event_flags_get', STATE, 0x3F00), STATE + 0x2C0)
        expected = bytearray(before)
        expected[0x2BC:0x2E0] = b'HF02' + expected_bank(before[0xAC0:0xAE0], bytes(1004))
        self.assertEqual(m.read(), expected)
        self.assertEqual(m.writes[-1], (STATE + 0x2BC, 4, 0x32304648))
        m.writes.clear()
        for flag in range(0x3F00, 0x4000):
            self.assertEqual(m.call('sgp_event_flags_get', STATE, flag),
                             STATE + 0x2C0 + (flag - 0x3F00) // 8)
        m.mu.mem_write(STATE + 0xAC0, bytes(32))
        m.call('sgp_event_flags_get', STATE, 0x3FFF)
        self.assertEqual(m.writes, [])
        self.assertEqual(m.read()[0x2BC:0x2E0], expected[0x2BC:0x2E0])

    def test_new_game_family_access_before_high_flag_initializes_bank(self):
        for first in ('get', 'set'):
            with self.subTest(first=first):
                m = Runtime(self.blob, self.symbols)
                state = bytearray(0x1000)
                state[0xAC0:0xAE0] = bytes((i * 7 + 1) % 256 for i in range(32))
                m.mu.mem_write(STATE, bytes(state))
                if first == 'get':
                    self.assertEqual(m.call('sgp_event_vars_get', STATE, 0x6130), 0)
                else:
                    self.assertEqual(m.call('sgp_event_vars_set', STATE, 0x6130, 2), 1)
                self.assertEqual(m.events, [])
                after = m.read()
                self.assertEqual(after[0x2BC:0x2C0], b'HF02')
                expected = bytearray(expected_bank(state[0xAC0:0xAE0], bytes(1004)))
                if first == 'set':
                    bit = FAMILY_FLAGS[FAMILY_IDS.index(0x6130)] - 0x3F00
                    expected[bit // 8] |= 1 << (bit & 7)
                self.assertEqual(after[0x2C0:0x2E0], expected)
                self.assertEqual(after[0xAC0:0xAE0], state[0xAC0:0xAE0])
                self.assertEqual(m.call('sgp_event_vars_get', STATE, 0x6130),
                                 0 if first == 'get' else 2)

    def test_new_game_family_access_respects_foreign_ownership(self):
        for tag in (b'HF01', b'HF03', b'FORE'):
            for first in ('get', 'set'):
                with self.subTest(tag=tag, first=first):
                    m = Runtime(self.blob, self.symbols)
                    m.mu.mem_write(STATE + 0x2BC, tag + bytes(32))
                    before = m.read()
                    if first == 'get':
                        m.call('sgp_event_vars_get', STATE, 0x6130)
                    else:
                        m.call('sgp_event_vars_set', STATE, 0x6130, 2)
                    self.assertEqual(m.events, ['reset'])
                    self.assertEqual(m.read(), before)
                    self.assertEqual(m.writes, [])

    def test_successful_load_migrates_zero_and_hf01_from_exact_chatot_once(self):
        chatot = bytearray((i * 29 + 7) % 256 for i in range(1004))
        for index, offset in enumerate(CHATOT_OFFSETS):
            struct.pack_into('<H', chatot, offset, 0 if index % 3 == 0 else 0x8888)
        for tag in (bytes(4), b'HF01'):
            with self.subTest(tag=tag):
                m = Runtime(self.blob, self.symbols)
                state = bytearray((i * 37 + 11) % 256 for i in range(0x1000))
                bank = bytes((i * 13 + 5) % 256 for i in range(32))
                state[0x2BC:0x2E0] = tag + (bank if tag == b'HF01' else bytes(32))
                m.reload, m.reload_chatot = bytes(state), bytes(chatot)
                self.assertEqual(m.call('sgp_event_flags_load', SAVE), 1)
                source = bank if tag == b'HF01' else state[0xAC0:0xAE0]
                self.assertEqual(m.read()[0x2BC:0x2E0], b'HF02' + expected_bank(source, chatot))
                self.assertEqual(m.chatot(), bytes(chatot))
                self.assertEqual(m.writes[-1], (STATE + 0x2BC, 4, 0x32304648))
                first = m.read()[0x2BC:0x2E0]
                m.writes.clear()
                m.reload, m.reload_chatot = m.read(), bytes([0xFF]) * 1004
                self.assertEqual(m.call('sgp_event_flags_load', SAVE), 1)
                self.assertEqual(m.read()[0x2BC:0x2E0], first)
                self.assertEqual(m.writes, [])

    def test_family_get_set_is_boolean_and_never_writes_chatot(self):
        m = Runtime(self.blob, self.symbols)
        m.mu.mem_write(STATE + 0x2BC, b'HF02' + bytes(32))
        chatot = bytes((i * 17 + 9) % 256 for i in range(1004))
        m.mu.mem_write(CHATOT, chatot)
        for variable in FAMILY_IDS:
            self.assertEqual(m.call('sgp_event_vars_get', STATE, variable), 0)
            self.assertEqual(m.call('sgp_event_vars_set', STATE, variable, 2), 1)
            self.assertEqual(m.call('sgp_event_vars_get', STATE, variable), 2)
            self.assertEqual(m.call('sgp_event_vars_set', STATE, variable, 0), 1)
            self.assertEqual(m.call('sgp_event_vars_get', STATE, variable), 0)
        self.assertEqual(m.chatot(), chatot)
        self.assertEqual(m.call('sgp_event_vars_get', STATE, 0x612D), 0xFFFF)
        self.assertEqual(m.call('sgp_event_vars_set', STATE, 0x612D, 2), 0)
        self.assertEqual(m.call('sgp_event_vars_set', STATE, 0x612E, 1), 0)

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
        for tag in (b'HF03', b'HF00', b'FORE'):
            m = Runtime(self.blob, self.symbols)
            m.mu.mem_write(STATE + 0x2BC, tag)
            self.assertEqual(m.call('sgp_event_flags_load', SAVE), 0)
            self.assertEqual(m.events, [])
            self.assertEqual(m.writes, [])

    def test_failure_is_propagated_without_migration(self):
        for tag in (b'HF01', bytes(4), b'HF02'):
            m = Runtime(self.blob, self.symbols)
            m.reload = bytes(0x2BC) + tag + bytes(0x1000 - 0x2C0)
            m.result = 0
            self.assertEqual(m.call('sgp_event_flags_load', SAVE), 0)
            self.assertEqual(m.events, ['load'])
            self.assertEqual(m.writes, [])
            self.assertEqual(m.read(), m.reload)

    def test_archive_reservation_guard_catches_allocated_ids_at_any_alignment(self):
        for variable in range(0x415E, 0x4170):
            for alignment in (0, 1):
                with self.assertRaisesRegex(ValueError, 'reservation'):
                    event_flags.guard_archive_members('synthetic', [bytes(4), bytes(alignment) + struct.pack('<H', variable)])
        for flag in FAMILY_FLAGS:
            for alignment in (0, 1):
                with self.assertRaisesRegex(ValueError, 'family bit'):
                    event_flags.guard_archive_members('synthetic', [bytes(4), bytes(alignment) + struct.pack('<H', flag)])
        event_flags.guard_archive_members('synthetic', [b'', b'X', struct.pack('<HH', 0x415D, 0x4170)])


if __name__ == '__main__':
    unittest.main()
