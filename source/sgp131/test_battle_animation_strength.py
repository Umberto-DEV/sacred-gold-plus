"""HG-F18 Strength battle-animation timing regression tests."""
import hashlib
import struct
import unittest

import ndspy.narc

from sgp131 import battle_animation_strength as strength


def synthetic_member(frames=10):
    member = bytearray(strength.MEMBER_SIZE)
    struct.pack_into(
        '<11I', member, strength.COMMAND_OFFSET,
        0x2D, 5, 4, 70, 120, frames, 5,
        0x16, 0x787, 0xFFFFFF8B, 1,
    )
    return bytes(member)


class StrengthTimingOracle(unittest.TestCase):
    def test_real_four_tick_phase_explains_8_9_10_11_frame_results(self):
        expected = {
            8: ((2, 0, -2, 0, 2, 0, -2, 0), 0),
            9: ((2, 0, -2, 0, 2, 0, -2, 0, 2), 2),
            10: ((2, 0, -2, 0, 2, 0, -2, 0, 2, 0), 2),
            11: ((2, 0, -2, 0, 2, 0, -2, 0, 2, 0, -2), 0),
        }
        for frames, (offsets, drift) in expected.items():
            with self.subTest(frames=frames):
                schedule = strength.evaluate_strength_schedule(frames)
                self.assertEqual(schedule.offsets, offsets)
                self.assertEqual(schedule.final_x, drift)

    def test_exact_member_patch_changes_only_the_frame_count_byte(self):
        member = synthetic_member()
        retail = strength.read_member_timing(member)
        patched = strength.patch_exact_member(
            member, hashlib.sha256(member).hexdigest())
        fixed = strength.read_member_timing(patched)
        self.assertEqual((retail.frames, retail.schedule.final_x), (10, 2))
        self.assertEqual((fixed.frames, fixed.schedule.final_x), (8, 0))
        self.assertEqual(
            [i for i, pair in enumerate(zip(member, patched)) if pair[0] != pair[1]],
            [strength.FRAME_COUNT_OFFSET],
        )
        with self.assertRaisesRegex(ValueError, 'already patched'):
            strength.patch_exact_member(
                patched, hashlib.sha256(member).hexdigest())

    def test_reader_rejects_foreign_shape_and_unqualified_frame_counts(self):
        retail = synthetic_member()
        mutations = {
            'dispatcher': (0xB8, 0x2C, 'task command'),
            'function': (0xBC, 6, 'task command'),
            'argument count': (0xC0, 5, 'task command'),
            'first parameter': (0xC4, 71, 'task command'),
            'second parameter': (0xC8, 119, 'task command'),
            'tail parameter': (0xD0, 6, 'task command'),
            'sound': (0xD8, 0x788, 'sound command'),
        }
        for name, (offset, value, message) in mutations.items():
            with self.subTest(name=name):
                mutant = bytearray(retail)
                struct.pack_into('<I', mutant, offset, value)
                with self.assertRaisesRegex(ValueError, message):
                    strength.read_member_timing(bytes(mutant))
        for frames in (7, 9, 11, 12):
            with self.subTest(frames=frames):
                with self.assertRaisesRegex(ValueError, 'neither retail nor fixed'):
                    strength.read_member_timing(synthetic_member(frames))

    def test_exact_archive_patch_preserves_every_other_member(self):
        members = [bytes(((index * 17 + byte) & 0xFF)
                         for byte in range(2 + index % 9))
                   for index in range(strength.MEMBER_COUNT)]
        members[strength.MEMBER_INDEX] = synthetic_member()
        archive = ndspy.narc.NARC.fromFilesAndNames(members).save()
        patched = strength.patch_exact_archive(
            archive, hashlib.sha256(members[strength.MEMBER_INDEX]).hexdigest())
        old_files = [bytes(member) for member in ndspy.narc.NARC(archive).files]
        new_files = [bytes(member) for member in ndspy.narc.NARC(patched).files]
        self.assertEqual(len(patched), len(archive))
        for index, (old, new) in enumerate(zip(old_files, new_files)):
            if index == strength.MEMBER_INDEX:
                self.assertEqual(
                    new,
                    strength.patch_exact_member(old, hashlib.sha256(old).hexdigest()),
                )
            else:
                self.assertEqual(new, old)
        self.assertEqual(sum(old != new for old, new in zip(archive, patched)), 1)


if __name__ == '__main__':
    unittest.main()
