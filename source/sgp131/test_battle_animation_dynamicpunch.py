"""HG-F20-DP DynamicPunch scheduling regression tests."""
import hashlib
import struct
import unittest

import ndspy.narc

from sgp131 import battle_animation_dynamicpunch as dynamicpunch


def synthetic_member(delay=3):
    member = bytearray(dynamicpunch.MEMBER_SIZE)
    words = {
        0x118: (0x2D, 0x24, 5, 1, 0, 1, 2, 0x108),
        0x138: (0, 2),
        0x140: (0x2D, 0x22, 6, 8, 0, 2, 0x84C, 0xE, 0),
        0x164: (0x2D, 0x44, 5, 5, 0, 1, 6, 0),
        0x184: (0x19, 0x7C9, 0x75, 4, 6),
        0x198: (0, delay),
        0x1A0: (0x2D, 0x24, 5, 4, 0, 1, 10, 0x108),
        0x1C0: (0x32,),
    }
    for offset, values in words.items():
        struct.pack_into('<%dI' % len(values), member, offset, *values)
    return bytes(member)


class DynamicPunchTimingOracle(unittest.TestCase):
    def test_native_shake_and_delay_boundary_reproduce_and_remove_the_drift(self):
        self.assertEqual(
            dynamicpunch.evaluate_shake_offsets(extent_x=1, interval=1, amount=2),
            (1, 0, -1, 0, 1, 0, -1, 0),
        )
        retail = dynamicpunch.evaluate_dynamicpunch_schedule(3)
        fixed = dynamicpunch.evaluate_dynamicpunch_schedule(4)
        self.assertEqual(retail.second_start_tick, 7)
        self.assertEqual(retail.captured_base_x, -1)
        self.assertEqual(retail.final_x, -1)
        self.assertEqual(fixed.second_start_tick, 8)
        self.assertEqual(fixed.captured_base_x, 0)
        self.assertEqual(fixed.final_x, 0)

    def test_exact_member_patch_changes_only_the_second_delay(self):
        member = synthetic_member()
        retail = dynamicpunch.read_member_timing(member)
        patched = dynamicpunch.patch_exact_member(
            member, hashlib.sha256(member).hexdigest())
        fixed = dynamicpunch.read_member_timing(patched)

        self.assertEqual(retail.delay, 3)
        self.assertEqual(retail.schedule.final_x, -1)
        self.assertEqual(fixed.delay, 4)
        self.assertEqual(fixed.schedule.final_x, 0)
        self.assertEqual(
            [index for index, (old, new) in enumerate(zip(member, patched)) if old != new],
            [dynamicpunch.DELAY_VALUE_OFFSET],
        )
        self.assertEqual(member[0x118:0x138], patched[0x118:0x138])
        self.assertEqual(member[0x138:0x13C], patched[0x138:0x13C])
        self.assertEqual(member[0x140:0x198], patched[0x140:0x198])
        self.assertEqual(member[0x1A0:0x1C4], patched[0x1A0:0x1C4])
        with self.assertRaisesRegex(ValueError, 'already patched'):
            dynamicpunch.patch_exact_member(
                patched, hashlib.sha256(member).hexdigest())

    def test_reader_and_patcher_reject_noncanonical_timings_and_foreign_commands(self):
        retail = synthetic_member()
        mutations = {
            'previous Delay': (0x13C, 3, 'first Delay'),
            'Delay opcode': (0x198, 1, 'second Delay'),
            'first shake extent': (0x124, 2, 'first shake'),
            'fade': (0x144, 0x23, 'fade'),
            'background shake': (0x168, 0x45, 'background'),
            'audio': (0x188, 0x7CA, 'audio'),
            'second shake extent': (0x1AC, 5, 'second shake'),
            'second shake target': (0x1BC, 0x100, 'second shake'),
        }
        for name, (offset, value, message) in mutations.items():
            with self.subTest(name=name):
                mutant = bytearray(retail)
                struct.pack_into('<I', mutant, offset, value)
                with self.assertRaisesRegex(ValueError, message):
                    dynamicpunch.read_member_timing(bytes(mutant))

        for delay in (2, 5, 6):
            with self.subTest(delay=delay):
                mutant = synthetic_member(delay)
                with self.assertRaisesRegex(ValueError, 'neither retail nor fixed'):
                    dynamicpunch.read_member_timing(mutant)
                with self.assertRaises(ValueError):
                    dynamicpunch.patch_exact_member(
                        mutant, hashlib.sha256(mutant).hexdigest())

    def test_exact_archive_patch_preserves_facade_and_every_other_member(self):
        members = [bytes(((index * 29 + byte) & 0xFF) for byte in range(3 + index % 5))
                   for index in range(dynamicpunch.MEMBER_COUNT)]
        members[dynamicpunch.MEMBER_INDEX] = synthetic_member()
        members[dynamicpunch.FACADE_MEMBER_INDEX] = bytes(range(251)) * 2 + b'facade'
        archive = ndspy.narc.NARC.fromFilesAndNames(members).save()
        patched = dynamicpunch.patch_exact_archive(
            archive, hashlib.sha256(members[dynamicpunch.MEMBER_INDEX]).hexdigest())

        old_files = [bytes(member) for member in ndspy.narc.NARC(archive).files]
        new_files = [bytes(member) for member in ndspy.narc.NARC(patched).files]
        self.assertEqual(len(patched), len(archive))
        self.assertEqual(len(new_files), dynamicpunch.MEMBER_COUNT)
        self.assertEqual(
            archive[:dynamicpunch.narc_data_offset(archive)],
            patched[:dynamicpunch.narc_data_offset(patched)],
        )
        for index, (old, new) in enumerate(zip(old_files, new_files)):
            if index == dynamicpunch.MEMBER_INDEX:
                self.assertEqual(
                    new,
                    dynamicpunch.patch_exact_member(old, hashlib.sha256(old).hexdigest()),
                )
            else:
                self.assertEqual(new, old)
        self.assertEqual(sum(old != new for old, new in zip(archive, patched)), 1)


if __name__ == '__main__':
    unittest.main()
