from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'proofs/cheat-functional'))
from inspect_test_mon import inspect


def fixture():
    ram = bytearray(0x400000)
    struct.pack_into('<I', ram, 0x11186C, 0x02010000)
    at = 0x1D080
    struct.pack_into('<II', ram, at, 6, 2)
    for slot in range(2):
        box = bytearray(128)
        struct.pack_into('<H', box, 0, 152)
        box[16:22] = bytes([slot + 1] * 6)
        checksum = sum(struct.unpack('<64H', box)) & 65535
        party = bytearray(100)
        party[4] = 5
        mon = struct.pack('<IHH', 0, 3, checksum) + box + party
        ram[at + 8 + slot * 236:at + 8 + (slot + 1) * 236] = mon
    return bytes(ram)


class PartyReaderTests(unittest.TestCase):
    def test_explicit_slot_reads_its_own_values(self):
        ram = fixture()
        a = inspect(ram, expected_count=2, slot=0)
        b = inspect(ram, expected_count=2, slot=1)
        self.assertEqual(a['EVs_HP_Atk_Def_Spe_SpA_SpD'], [1] * 6)
        self.assertEqual(b['EVs_HP_Atk_Def_Spe_SpA_SpD'], [2] * 6)
        self.assertEqual(b['address'] - a['address'], 236)

    def test_original_default_still_requires_exactly_one_member(self):
        with self.assertRaises(ValueError):
            inspect(fixture())

    def test_mismatch_and_outside_slot_are_rejected(self):
        for count, slot in [(1, 0), (2, -1), (2, 2), (0, 0), (7, 0)]:
            with self.assertRaises(ValueError):
                inspect(fixture(), expected_count=count, slot=slot)


if __name__ == '__main__':
    unittest.main()
