"""HG-F17 Facade timing regression tests.

The first test is deliberately independent of ROM data: it states the frame
invariant that the production reader and producer must preserve.
"""
import hashlib
import struct
import unittest

import ndspy.narc

from sgp131 import battle_animation_facade as facade


def synthetic_member():
    member = bytearray(744)
    struct.pack_into('<IIIII', member, 0xD8, 0x19, 0x7EA, 0xFFFFFF8B, 8, 6)
    for offset in (0x138, 0x16C, 0x1C4, 0x1F8, 0x250, 0x284):
        struct.pack_into('<I', member, offset, 0x00050005)
    for offset in (0x140, 0x174, 0x1CC, 0x200, 0x258):
        struct.pack_into('<II', member, offset - 4, 0, 8)
    return bytes(member)


class FacadeTimingOracle(unittest.TestCase):
    def test_retail_schedule_overlaps_but_root_cause_fix_does_not(self):
        retail = facade.evaluate_schedule(
            durations=(10, 10, 10, 10, 10, 10),
            inter_task_delays=(8, 8, 8, 8, 8),
            sound_interval=8,
        )
        fixed = facade.evaluate_schedule(
            durations=(10, 10, 10, 10, 10, 10),
            inter_task_delays=(10, 10, 10, 10, 10),
            sound_interval=10,
        )

        self.assertEqual(retail.starts, (0, 8, 16, 24, 32, 40))
        self.assertEqual(retail.ends, (10, 18, 26, 34, 42, 50))
        self.assertEqual(retail.overlaps, ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5)))
        self.assertEqual(fixed.starts, (0, 10, 20, 30, 40, 50))
        self.assertEqual(fixed.ends, (10, 20, 30, 40, 50, 60))
        self.assertEqual(fixed.overlaps, ())
        self.assertEqual(fixed.sound_interval, 10)

    def test_member_reader_and_exact_patcher_remove_only_the_overlap(self):
        flag_offsets = (0x138, 0x16C, 0x1C4, 0x1F8, 0x250, 0x284)
        delay_offsets = (0x140, 0x174, 0x1CC, 0x200, 0x258)
        member = synthetic_member()

        retail = facade.read_member_timing(member)
        patched = facade.patch_exact_member(member, hashlib.sha256(member).hexdigest())
        fixed = facade.read_member_timing(patched)

        self.assertEqual(retail.durations, (10, 10, 10, 10, 10, 10))
        self.assertEqual(retail.inter_task_delays, (8, 8, 8, 8, 8))
        self.assertEqual(retail.schedule.overlaps,
                         ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5)))
        self.assertEqual(fixed.durations, retail.durations)
        self.assertEqual(fixed.inter_task_delays, (10, 10, 10, 10, 10))
        self.assertEqual(fixed.schedule.overlaps, ())
        self.assertEqual(fixed.sound_interval, 10)
        self.assertEqual(
            [index for index, (old, new) in enumerate(zip(member, patched)) if old != new],
            [0xE4, 0x140, 0x174, 0x1CC, 0x200, 0x258],
        )
        for offset in flag_offsets:
            self.assertEqual(patched[offset:offset + 4], member[offset:offset + 4])
        with self.assertRaisesRegex(ValueError, 'already patched'):
            facade.patch_exact_member(patched, hashlib.sha256(member).hexdigest())

    def test_member_reader_refuses_foreign_timing_shape(self):
        member = synthetic_member()

        mutations = {
            'wrong sound opcode': (0xD8, 0x18, 'sound command'),
            'wrong task duration': (0x138, 0x00060005, 'scale/restore'),
            'wrong delay opcode': (0x13C, 1, 'Delay command'),
            'wrong delay value': (0x140, 9, 'delay values'),
        }
        for name, (offset, value, pattern) in mutations.items():
            with self.subTest(name=name):
                foreign = bytearray(member)
                struct.pack_into('<I', foreign, offset, value)
                with self.assertRaisesRegex(ValueError, pattern):
                    facade.read_member_timing(bytes(foreign))

    def test_shortened_workaround_and_partial_ports_are_negative_controls(self):
        retail = synthetic_member()
        cases = {}

        shortened = bytearray(retail)
        for offset in (0x138, 0x16C, 0x1C4, 0x1F8, 0x250, 0x284):
            struct.pack_into('<I', shortened, offset, 0x00040004)
        cases['2016 shortened-task workaround'] = (bytes(shortened), 'scale/restore')

        delay_only = bytearray(retail)
        for offset in (0x140, 0x174, 0x1CC, 0x200, 0x258):
            struct.pack_into('<I', delay_only, offset, 10)
        cases['delay without synchronized audio'] = (bytes(delay_only), 'sound interval')

        sound_only = bytearray(retail)
        struct.pack_into('<I', sound_only, 0xE4, 10)
        cases['audio without task delay'] = (bytes(sound_only), 'sound interval')

        for name, (member, pattern) in cases.items():
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, pattern):
                facade.read_member_timing(member)

    def test_exact_archive_patch_preserves_container_and_other_members(self):
        members = [bytes(((index * 17 + byte) & 0xFF) for byte in range(3 + index % 7))
                   for index in range(501)]
        members[263] = synthetic_member()
        archive = ndspy.narc.NARC.fromFilesAndNames(members).save()
        patched = facade.patch_exact_archive(
            archive, hashlib.sha256(members[263]).hexdigest())

        old_files = [bytes(member) for member in ndspy.narc.NARC(archive).files]
        new_files = [bytes(member) for member in ndspy.narc.NARC(patched).files]
        self.assertEqual(len(patched), len(archive))
        self.assertEqual(archive[:facade.narc_data_offset(archive)],
                         patched[:facade.narc_data_offset(patched)])
        self.assertEqual(len(new_files), 501)
        for index, (old, new) in enumerate(zip(old_files, new_files)):
            if index == 263:
                self.assertEqual(new, facade.patch_exact_member(
                    old, hashlib.sha256(old).hexdigest()))
            else:
                self.assertEqual(new, old)
        self.assertEqual(sum(old != new for old, new in zip(archive, patched)), 6)


if __name__ == '__main__':
    unittest.main()
