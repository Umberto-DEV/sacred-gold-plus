"""HG-B05: the pivot script must snapshot the outgoing effective item."""
import hashlib
import struct
import unittest

import ndspy.rom

from sgp131 import archives, pursuit_script
from sgp131.test_legacy_scripts import inputs


class UTurnScriptDelta(unittest.TestCase):
    @staticmethod
    def archive(data):
        rom = ndspy.rom.NintendoDSRom(data)
        return bytes(rom.files[rom.filenames.idOf('a/0/0/1')])

    def test_both_languages_insert_the_guarded_snapshot_once(self):
        from sgp131 import uturn_script as U
        records = []
        for language in ('EN', 'IT'):
            data = inputs(language)[0]
            raw = self.archive(data)
            before = archives.members(raw)[175]
            delta = U.derive(data, language)
            self.assertEqual(delta.producers(), ['uturn-item-snapshot'])
            self.assertEqual([row.index for row in delta.members], [175])
            after = delta.members[0].after
            self.assertEqual((len(before), hashlib.sha256(before).hexdigest()),
                             (696, U.BEFORE_SHA256))
            self.assertEqual((len(after), hashlib.sha256(after).hexdigest()),
                             (800, U.AFTER_SHA256))
            self.assertEqual(struct.unpack_from('<I', after, 8)[0], 0xC4)
            self.assertEqual(struct.unpack_from('<I', after, 0x18)[0], 0xC0)
            self.assertEqual(after[U.INSERT_AT:U.INSERT_AT + len(U.INSERT)], U.INSERT)
            U.check(175, before, after, language)
            records.append(delta.record())
        self.assertEqual(records[0], records[1])

    def test_snapshot_commands_encode_effective_item_and_modifier(self):
        from sgp131 import uturn_script as U
        words = struct.unpack('<26I', U.INSERT)
        self.assertEqual(words, (
            50, 7, 68, 1 << 16,
            166, 0, 1, 56, 2,
            59, 15,
            50, 10, 68, 56,
            168, 1, 9,
            50, 14, 9, 8,
            57, 10, 68, 9,
        ))

        def execute(*, effective, modifier):
            snapshot = 1 << 16
            if effective == 56:  # CheckItemHoldEffect respects Klutz/Embargo.
                snapshot |= 56
                snapshot |= modifier << 8
            return snapshot

        self.assertEqual(execute(effective=56, modifier=10), 0x10A38)
        self.assertEqual(execute(effective=0, modifier=10), 0x10000)
        self.assertEqual(execute(effective=56, modifier=11), 0x10B38)

    def test_archive_merge_is_disjoint_from_pursuit_repair(self):
        from sgp131 import uturn_script as U
        data = inputs('EN')[0]
        raw = self.archive(data)
        merged = archives.normalize((pursuit_script.derive(data, 'EN'),
                                     U.derive(data, 'EN')))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].producers(),
                         ['pursuit-script', 'uturn-item-snapshot'])
        self.assertEqual([row.index for row in merged[0].members], [153, 175])
        rebuilt = archives.apply_members(raw, merged[0].replacements())
        self.assertEqual(archives.verify_members(raw, rebuilt, merged[0].replacements()),
                         {'members': 297, 'changed': [153, 175]})

    def test_writer_and_checker_reject_reapply_and_mutants(self):
        from sgp131 import uturn_script as U
        data = inputs('EN')[0]
        before = archives.members(self.archive(data))[175]
        after = U.patch_member(before)
        with self.assertRaises(ValueError):
            U.patch_member(after)
        for at in (0, 8, 0x18, U.INSERT_AT, len(after) - 1):
            mutant = bytearray(after)
            mutant[at] ^= 1
            with self.subTest(at=at), self.assertRaises(ValueError):
                U.check(175, before, bytes(mutant), 'EN')


if __name__ == '__main__':
    unittest.main()
