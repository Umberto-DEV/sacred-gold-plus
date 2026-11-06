"""HG-F20-HH Helping Hand scheduling regression tests."""
import hashlib
import struct
import unittest

import ndspy.narc

from sgp131 import battle_animation_helping_hand as helping_hand


def synthetic_member(*, fixed=False):
    member = bytearray(helping_hand.MEMBER_SIZE)
    words = {
        0x09C: (2, 2),
        0x0A4: (0x2D, 0x34, 3, 2, 12, 0x102),
        0x0BC: (0x2D, 0x24, 5, 1, 0, 1, 2, 0x104),
        0x0DC: (0, 3),
        0x0E4: (0x2D, 0x34, 3, 2, 0xFFFFFFF4, 0x102),
        0x0FC: (0, 2),
        0x104: (0x16, 0x7F3, 0),
        0x110: ((0, 1, 3) if fixed else (3, 0, 1)),
        0x11C: (0x2D, 0x34, 3, 2, 12, 0x102),
        0x134: (0x2D, 0x24, 5, 1, 0, 1, 2, 0x104),
        0x154: (0, 3),
        0x15C: (0x2D, 0x34, 3, 2, 0xFFFFFFF4, 0x102),
        0x174: (0, 1),
        0x17C: (0x2D, 0x22, 5, 4, 0, 2, 0x3EB, 8),
        0x19C: (1,),
        0x1A0: (0x50, 0, 4),
    }
    for offset, values in words.items():
        struct.pack_into('<%dI' % len(values), member, offset, *values)
    return bytes(member)


class HelpingHandTimingOracle(unittest.TestCase):
    def test_retail_loop_reuses_a_transient_base_but_fixed_loop_does_not(self):
        retail = helping_hand.evaluate_helping_hand_schedule(False)
        fixed = helping_hand.evaluate_helping_hand_schedule(True)
        self.assertEqual(retail.shake_start_ticks, (0, 7, 16))
        self.assertEqual(retail.captured_base_x, (0, -1, -1))
        self.assertEqual(retail.final_x, -1)
        self.assertEqual(fixed.shake_start_ticks, (0, 9, 18))
        self.assertEqual(fixed.captured_base_x, (0, 0, 0))
        self.assertEqual(fixed.final_x, 0)

    def test_exact_member_patch_moves_delay_inside_loop_and_changes_three_bytes(self):
        member = synthetic_member()
        retail = helping_hand.read_member_timing(member)
        patched = helping_hand.patch_exact_member(
            member, hashlib.sha256(member).hexdigest())
        fixed = helping_hand.read_member_timing(patched)

        self.assertFalse(retail.delay_inside_loop)
        self.assertEqual(retail.schedule.final_x, -1)
        self.assertTrue(fixed.delay_inside_loop)
        self.assertEqual(fixed.schedule.final_x, 0)
        self.assertEqual(
            [index for index, pair in enumerate(zip(member, patched))
             if pair[0] != pair[1]],
            [0x110, 0x114, 0x118],
        )
        self.assertEqual(member[:0x110], patched[:0x110])
        self.assertEqual(member[0x11C:], patched[0x11C:])
        with self.assertRaisesRegex(ValueError, 'already patched'):
            helping_hand.patch_exact_member(
                patched, hashlib.sha256(member).hexdigest())

    def test_reader_rejects_partial_reorders_and_foreign_commands(self):
        retail = synthetic_member()
        mutations = {
            'loop count': (0x0A0, 3, 'BeginLoop'),
            'loop move': (0x0A8, 0x35, 'loop move right'),
            'loop shake': (0x0C0, 0x25, 'loop shake'),
            'Delay 3': (0x0E0, 4, 'loop Delay 3'),
            'loop move left': (0x0F4, 0xFFFFFFF3, 'loop move left'),
            'Delay 2': (0x100, 1, 'loop Delay 2'),
            'sound': (0x108, 0x7F4, 'loop sound'),
            'post-loop shake': (0x138, 0x25, 'post-loop shake'),
            'post-loop Delay 3': (0x158, 4, 'post-loop Delay 3'),
            'post-loop Delay 1': (0x178, 2, 'post-loop Delay 1'),
        }
        for name, (offset, value, message) in mutations.items():
            with self.subTest(name=name):
                mutant = bytearray(retail)
                struct.pack_into('<I', mutant, offset, value)
                with self.assertRaisesRegex(ValueError, message):
                    helping_hand.read_member_timing(bytes(mutant))

        for words in ((0, 3, 1), (3, 1, 0), (0, 1, 0), (3, 0, 2)):
            with self.subTest(words=words):
                mutant = bytearray(retail)
                struct.pack_into('<III', mutant, 0x110, *words)
                with self.assertRaisesRegex(ValueError, 'loop boundary'):
                    helping_hand.read_member_timing(bytes(mutant))

    def test_exact_archive_patch_preserves_every_other_member(self):
        members = [bytes(((index * 31 + byte) & 0xFF)
                         for byte in range(3 + index % 7))
                   for index in range(helping_hand.MEMBER_COUNT)]
        members[helping_hand.MEMBER_INDEX] = synthetic_member()
        members[helping_hand.FACADE_MEMBER_INDEX] = b'facade predecessor'
        members[helping_hand.DYNAMICPUNCH_MEMBER_INDEX] = b'dynamic predecessor'
        archive = ndspy.narc.NARC.fromFilesAndNames(members).save()
        patched = helping_hand.patch_exact_archive(
            archive, hashlib.sha256(members[helping_hand.MEMBER_INDEX]).hexdigest())

        old_files = [bytes(member) for member in ndspy.narc.NARC(archive).files]
        new_files = [bytes(member) for member in ndspy.narc.NARC(patched).files]
        self.assertEqual(len(patched), len(archive))
        self.assertEqual(
            archive[:helping_hand.narc_data_offset(archive)],
            patched[:helping_hand.narc_data_offset(patched)],
        )
        for index, (old, new) in enumerate(zip(old_files, new_files)):
            if index == helping_hand.MEMBER_INDEX:
                self.assertEqual(
                    new,
                    helping_hand.patch_exact_member(
                        old, hashlib.sha256(old).hexdigest()),
                )
            else:
                self.assertEqual(new, old)
        self.assertEqual(sum(old != new for old, new in zip(archive, patched)), 3)


if __name__ == '__main__':
    unittest.main()
