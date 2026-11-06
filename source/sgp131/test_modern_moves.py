"""Class A: synthetic NitroFS move archive for the Fuocofatuo accuracy guard.

No ROM is read. Member 261 carries the reference record; every other member is
deterministic pseudo-random data. Expected values are written out here rather
than imported from the module under test.
"""
import random
import struct
import unittest

import ndspy.narc

from sgp131 import modern_moves as moves

MEMBERS = 471
MEMBER = 261
RECORD = 16
ACCURACY = 5
REFERENCE = bytes.fromhex('a70002000a4b0f000000001611010000')
PATCHED = REFERENCE[:ACCURACY] + bytes([85]) + REFERENCE[ACCURACY + 1:]


def synthetic_members(seed=261):
    rng = random.Random(seed)
    members = [bytes(rng.randrange(256) for _ in range(RECORD)) for _ in range(MEMBERS)]
    members[MEMBER] = REFERENCE
    return members


def build_narc(members):
    return ndspy.narc.NARC.fromFilesAndNames(list(members)).save()


def data_start(raw):
    """Offset of the FIMG member data, read straight from the NARC header."""
    fatb_size = struct.unpack_from('<I', raw, 0x14)[0]
    fntb = 0x10 + fatb_size
    fntb_size = struct.unpack_from('<I', raw, fntb + 4)[0]
    return fntb + fntb_size + 8


def record(member):
    effect, category, power, kind, accuracy, pp, chance = struct.unpack_from('<HBBBBBB', member, 0)
    return {'effect': effect, 'category': category, 'power': power, 'type': kind,
            'accuracy': accuracy, 'pp': pp, 'chance': chance, 'tail': member[8:]}


class SyntheticMoveArchive(unittest.TestCase):
    def setUp(self):
        self.members = synthetic_members()
        self.raw = build_narc(self.members)
        self.assertEqual(ndspy.narc.NARC(self.raw).files[MEMBER], REFERENCE)

    def test_wisp_accuracy_is_85_with_all_other_fields_unchanged(self):
        out = moves.patch_move_archive(self.raw)
        member = ndspy.narc.NARC(out).files[MEMBER]
        self.assertEqual(record(member)['accuracy'], 85)
        expected = dict(record(REFERENCE), accuracy=85)
        self.assertEqual(record(member), expected)
        self.assertEqual(len(out), len(self.raw))
        changed = [i for i in range(len(self.raw)) if self.raw[i] != out[i]]
        self.assertEqual(changed, [data_start(self.raw) + MEMBER * RECORD + ACCURACY])

    def test_all_other_members_unchanged(self):
        out = moves.patch_move_archive(self.raw)
        files = ndspy.narc.NARC(out).files
        self.assertEqual(len(files), MEMBERS)
        for index, (new, old) in enumerate(zip(files, self.members)):
            if index != MEMBER:
                self.assertEqual(new, old, f'member {index} changed')

    def test_foreign_truncated_and_already_patched_preimage_refuse(self):
        foreign_byte = bytearray(self.members[MEMBER])
        foreign_byte[6] = 0x10
        foreign_accuracy = bytearray(REFERENCE)
        foreign_accuracy[ACCURACY] = 74
        cases = {
            'foreign pp byte': (self.narc_with_member(bytes(foreign_byte)), 'foreign member 261'),
            'foreign accuracy 74': (self.narc_with_member(bytes(foreign_accuracy)), 'foreign member 261'),
            'truncated archive': (self.raw[:-1], 'truncated'),
            'already patched preimage': (self.narc_with_member(PATCHED), 'already patched'),
        }
        for name, (raw, pattern) in cases.items():
            with self.subTest(case=name):
                with self.assertRaisesRegex(ValueError, pattern):
                    moves.patch_move_archive(raw)

    def test_structure_guards_refuse_non_narc_wrong_count_and_member_size(self):
        cases = {
            'not a NARC': (b'\x00' * len(self.raw), 'not a NARC'),
            'wrong member count': (build_narc(self.members[:MEMBERS - 1]), 'expected 471 members'),
            'member not 16 bytes': (self.narc_with_odd_member(), 'members must be 16 bytes'),
        }
        for name, (raw, pattern) in cases.items():
            with self.subTest(case=name):
                with self.assertRaisesRegex(ValueError, pattern):
                    moves.patch_move_archive(raw)

    def test_resident_summary_and_battle_cache_agree(self):
        out = moves.patch_move_archive(self.raw)
        narc = ndspy.narc.NARC(out)
        resident = narc.files[MEMBER][ACCURACY]
        start = data_start(out)
        contiguous = out[start:start + 468 * RECORD]
        battle = contiguous[MEMBER * RECORD + ACCURACY]
        self.assertEqual(resident, 85)
        self.assertEqual(battle, 85)
        self.assertEqual(b''.join(narc.files)[:468 * RECORD], contiguous)

    def test_unknown_language_refused_before_any_rom_is_read(self):
        for language in ('FR', 'en', '', None):
            with self.subTest(language=language):
                with self.assertRaisesRegex(ValueError, 'language'):
                    moves.apply(b'', language)

    def narc_with_member(self, member):
        members = list(self.members)
        members[MEMBER] = member
        return build_narc(members)

    def narc_with_odd_member(self):
        members = list(self.members)
        members[5] = bytes(17)
        return build_narc(members)


if __name__ == '__main__':
    unittest.main()
