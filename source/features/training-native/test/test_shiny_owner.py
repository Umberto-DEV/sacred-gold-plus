"""Compiled persistence owner: shiny access shares the existing safe save writer.

Native/OS seams are the same as test_save_composition. These tests exercise the
production admission, wire codec, owner reset and composed Bag/training writer.
"""
import struct
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R1
import test_save_composition as fixture
from test_save_composition import STATE, SAVE, ARGS, BAG_ADDRESSES


class ShinyOwner(unittest.TestCase):
    setUpClass = classmethod(fixture.SaveComposition.setUpClass.__func__)
    bench = fixture.SaveComposition.bench

    def access(self, b, data=None):
        self.assertIn('training_shiny_access', b.symbols,
                      'compiled owner must expose checked shiny persistence access')
        fs, out = ARGS + 0x2100, ARGS + 0x500
        b.put(fs + 12, SAVE)
        b.mu.mem_write(out, data if data is not None else b'X' * 16)
        result = b.call(b.symbols['training_shiny_access'], fs, out, int(data is not None))
        return result, bytes(b.mu.mem_read(out, 16))

    def test_first_read_admits_once_without_flash_writes_or_policy_change(self):
        b = self.bench()
        self.assertEqual(self.access(b), (1, bytes(16)))
        count = len(b.reads)
        self.assertGreater(count, 0)
        self.assertEqual(self.access(b), (1, bytes(16)))
        self.assertEqual(len(b.reads), count)
        self.assertEqual(b.writes, [])
        self.assertEqual(bytes(b.mu.mem_read(STATE + 40, 1)), b'\0')
        self.assertEqual(b.u32(STATE + 8), 0)

    def test_shiny_alone_keeps_training_inactive_and_historical_rewards_unclaimed(self):
        b = self.bench()
        def badge(uc, address, size, user):
            if address == 0x02028F98:
                b.ret(int(uc.reg_read(UC_ARM_REG_R1) == 0))
        b.mu.hook_add(UC_HOOK_CODE, badge)
        self.assertEqual(self.access(b), (1, bytes(16)))
        self.assertEqual(b.service(0), 7)  # training remains explicitly unactivated
        self.assertEqual(bytes(b.mu.mem_read(STATE + 32 + 32, 12)), bytes(12))
        self.assertEqual(b.save(), 2)
        record = bytes(b.flash[0x71000:0x71100])
        self.assertEqual(record[14:16], b'\x01\0')  # v2 shiny-only marker
        self.assertEqual(b.service(1, arg=0), 0)
        self.assertEqual(b.u32(STATE + 8), 1)
        # Initial training activation still delivers its existing historical reward.
        self.assertEqual(bytes(b.mu.mem_read(STATE + 32 + 40, 2)), b'\x02\0')

    def test_foreign_or_unreadable_destinations_refuse_without_mutation(self):
        for address in (*BAG_ADDRESSES, 0x31000, 0x71000):
            b = self.bench()
            b.flash[address:address + 8] = b'FOREIGN!'
            before = bytes(b.mu.mem_read(STATE, 4096))
            self.assertEqual(self.access(b), (0, b'X' * 16))
            self.assertEqual(bytes(b.mu.mem_read(STATE, 4096)), before)
            self.assertEqual(b.writes, [])
        b = self.bench(); b.fail_address = 0x70200
        self.assertEqual(self.access(b), (0, b'X' * 16))

    def test_write_preserves_training_and_persists_inside_existing_owned_record(self):
        b = self.bench(); b.activate(2)
        # Existing counters are unrelated to the new extension.
        b.put(STATE + 32 + 16, 12345)
        prior = bytes(b.mu.mem_read(STATE + 32, 208))
        value = struct.pack('<IHBBB7x', 0x12345678, 132, 20, 1, 1)
        self.assertEqual(self.access(b, value), (1, value))
        self.assertEqual(bytes(b.mu.mem_read(STATE + 32, 208)), prior)
        self.assertEqual(self.access(b), (1, value))
        self.assertEqual(b.save(), 2)
        record = bytes(b.flash[0x71000:0x71100])
        self.assertEqual(record[:8], b'TNR1\x02\0\0\x01')
        self.assertEqual(record[224:240], value)
        self.assertEqual(record[16], 2)
        self.assertTrue(all(a in (*BAG_ADDRESSES, 0x71400, 0x71000, 0x71200)
                            for a, _ in b.writes))

    def test_invalid_write_does_not_activate_or_replace_any_state(self):
        for value in (struct.pack('<IHBBB7x', 0, 494, 0, 1, 0),
                      struct.pack('<IHBBB7x', 0, 19, 41, 1, 0),
                      struct.pack('<IHBBB7x', 0, 19, 1, 0, 0),
                      struct.pack('<IHBBB7x', 1, 0, 0, 0, 0), bytes([1]) * 16):
            b = self.bench(); before = bytes(b.mu.mem_read(STATE, 4096))
            self.assertEqual(self.access(b, value), (0, value))
            self.assertEqual(bytes(b.mu.mem_read(STATE, 4096)), before)
            self.assertEqual(b.writes, [])

    def test_new_game_same_pointer_resets_previous_journal_and_admission(self):
        b = self.bench()
        value = struct.pack('<IHBBB7x', 1234, 132, 40, 1, 1)
        self.assertEqual(self.access(b, value), (1, value))
        self.assertIn('training_shiny_bind', b.symbols)
        b.call(b.symbols['training_shiny_bind'], SAVE, 1)
        b.flash[0x70000:0x70008] = b'FOREIGN!'
        self.assertEqual(self.access(b), (0, b'X' * 16))
        self.assertEqual(b.u32(STATE + 8), 0)
