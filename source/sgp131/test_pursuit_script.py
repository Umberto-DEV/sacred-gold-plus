"""HG-B04: the inherited Pursuit KO script must restore the fainted battler.

These tests operate on the pinned V4 battle-script archive.  They do not write
a cartridge or a save and do not claim a rendered/link battle.
"""
import hashlib
import struct
import unittest

import ndspy.rom

from sgp131 import archives, mechanics_stages
from sgp131.test_legacy_scripts import inputs


class PursuitScriptDelta(unittest.TestCase):
    @staticmethod
    def archive(data):
        rom = ndspy.rom.NintendoDSRom(data)
        fid = rom.filenames.idOf('a/0/0/1')
        return fid, bytes(rom.files[fid])

    def test_both_languages_replace_only_the_canonical_two_bytes(self):
        from sgp131 import pursuit_script as P
        records = []
        for language in ('EN', 'IT'):
            data = inputs(language)[0]
            fid, raw = self.archive(data)
            self.assertEqual((fid, len(raw), hashlib.sha256(raw).hexdigest()),
                             (130, 53904, P.ARCHIVE_SHA256))
            old = archives.members(raw)
            delta = P.derive(data, language)
            self.assertEqual((delta.archive, delta.file_id, delta.producers()),
                             ('a/0/0/1', fid, ['pursuit-script']))
            self.assertEqual([row.index for row in delta.members], [153])
            before, after = old[153], delta.members[0].after
            self.assertEqual((len(before), hashlib.sha256(before).hexdigest()),
                             (960, P.BEFORE_SHA256))
            self.assertEqual(hashlib.sha256(after).hexdigest(), P.AFTER_SHA256)
            self.assertEqual(struct.unpack_from('<4I', before, P.OFFSET),
                             (57, 18, 7, 43))
            self.assertEqual(struct.unpack_from('<4I', after, P.OFFSET),
                             (57, 7, 18, 43))
            self.assertEqual([i for i, pair in enumerate(zip(before, after))
                              if pair[0] != pair[1]], [P.OFFSET + 4, P.OFFSET + 8])
            P.check(153, before, after, language)
            records.append(delta.record())
        self.assertEqual(records[0], records[1])

    def test_archive_roundtrip_keeps_geometry_name_block_and_other_members(self):
        from sgp131 import pursuit_script as P
        data = inputs('EN')[0]
        delta = P.derive(data, 'EN')
        resolve, file = archives.from_cartridge(data)
        old_raw = file(delta.file_id)
        old_members = archives.members(old_raw)
        self.assertEqual(archives.check_against((delta,), resolve, file), (delta,))
        rebuilt = archives.apply_members(old_raw, delta.replacements())
        self.assertEqual((len(rebuilt), hashlib.sha256(rebuilt).hexdigest()),
                         (53904, P.AFTER_ARCHIVE_SHA256))
        self.assertEqual(archives._geometry(rebuilt)[1],
                         bytes.fromhex('42544e46100000000400000000000100'))
        self.assertEqual(archives._geometry(rebuilt)[1], archives._geometry(old_raw)[1])
        report = archives.verify_members(old_raw, rebuilt, delta.replacements())
        self.assertEqual(report, {'members': 297, 'changed': [153]})
        new_members = archives.members(rebuilt)
        self.assertTrue(all(a == b for i, (a, b) in enumerate(zip(old_members, new_members))
                            if i != 153))
        archives.check_semantics(delta, old_raw, rebuilt, 'EN')
        replay = archives.rederive(data, 'EN', None, [delta.record()])
        self.assertEqual([item.record() for item in replay], [delta.record()])

    def test_writer_and_checker_fail_closed_on_reapply_and_mutants(self):
        from sgp131 import pursuit_script as P
        data = inputs('EN')[0]
        _, raw = self.archive(data)
        before = archives.members(raw)[153]
        after = P.patch_member(before)
        with self.assertRaises(ValueError):
            P.patch_member(after)
        for at in (0, P.OFFSET, P.OFFSET + 4, P.OFFSET + 8,
                   P.OFFSET + 12, len(before) - 1):
            foreign = bytearray(before)
            foreign[at] ^= 1
            with self.subTest(writer_preimage=at), self.assertRaises(ValueError):
                P.patch_member(bytes(foreign))
        hostile = []
        for at in (0, P.OFFSET, P.OFFSET + 4, P.OFFSET + 8,
                   P.OFFSET + 12, len(after) - 1):
            mutant = bytearray(after)
            mutant[at] ^= 1
            hostile.append(bytes(mutant))
        hostile.extend((before, after + b'\0', after[:-1]))
        for mutant in hostile:
            with self.subTest(length=len(mutant), digest=hashlib.sha256(mutant).hexdigest()), \
                    self.assertRaises(ValueError):
                P.check(153, before, mutant, 'EN')
        for args in ((152, before, after, 'EN'), (153, before + b'\0', after, 'EN'),
                     (153, before, after, 'FR')):
            with self.assertRaises(ValueError):
                P.check(*args)

    def test_field_mask_control_matrix_distinguishes_bug_from_restore(self):
        """Independent command model: the fixed tuple never writes fieldCondition."""
        original = (57, 18, 7, 43)
        corrected = (57, 7, 18, 43)

        def execute(command, field, saved, fainted=99):
            _, operation, destination, source = command
            values = {7: field, 18: fainted, 43: saved}
            if operation == 7:
                values[destination] = values[source]
            elif operation == 18:
                values[destination] = max(values[destination] - values[source], 0)
            else:
                raise AssertionError(operation)
            return values[7], values[18]

        fields = (0, 1, 2, 4, 8, 0x10, 0x20, 0x40, 0x80,
                  5 << 8, 5 << 12, 1 << 15, 5 << 16, (1 << 7) | (5 << 16))
        for saved in (0, 1, 3):
            for field in fields:
                with self.subTest(saved=saved, field=field):
                    self.assertEqual(execute(corrected, field, saved), (field, saved))
                    self.assertEqual(execute(original, field, saved),
                                     (max(field - saved, 0), 99))

    def test_legacy_stage_owns_the_fix_once(self):
        stage = mechanics_stages.require_stage('legacy')
        self.assertIn('pursuit-script', stage.archive_producers)
        self.assertEqual(stage.archive_producers.count('pursuit-script'), 1)


if __name__ == '__main__':
    unittest.main()
