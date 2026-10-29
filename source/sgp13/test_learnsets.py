"""Synthetic learnset transformations; no cartridge table is distributed."""
import hashlib
import struct
import unittest

import ndspy.narc
import ndspy.fnt
import ndspy.rom

from sgp13 import learnsets
from sgp13.learnsets import add_moves, decode, patch_archive


def packed(*pairs):
    return b''.join(struct.pack('<H', level * 512 + move) for level, move in pairs) + b'\xff\xff'


def digest(data):
    return hashlib.sha256(data).hexdigest()


class LearnsetTests(unittest.TestCase):
    def test_addition_keeps_existing_same_level_order(self):
        before = packed((1, 1), (5, 2), (5, 3), (20, 4))
        after = add_moves(before, [{'level': 5, 'move': 8}])
        self.assertEqual(after, packed((1, 1), (5, 2), (5, 3), (5, 8), (20, 4)))
        self.assertEqual(before, packed((1, 1), (5, 2), (5, 3), (20, 4)))

    def test_twenty_entries_and_terminator_fit_reminder_allocation(self):
        before = packed(*[(i, i) for i in range(1, 20)])
        after = add_moves(before, [{'level': 20, 'move': 20}])
        self.assertEqual(len(after), 42)
        self.assertEqual(after[-2:], b'\xff\xff')
        with self.assertRaisesRegex(ValueError, 'capacity'):
            add_moves(after, [{'level': 21, 'move': 21}])

    def test_decode_accepts_zero_alignment_but_not_hidden_entries_after_terminator(self):
        self.assertEqual(decode(packed((1, 5)) + b'\0\0'), [(1, 5)])
        with self.assertRaises(ValueError):
            decode(packed((1, 5)) + b'\x05\x02')

    def test_invalid_or_unsorted_input_and_invalid_additions_are_rejected(self):
        for raw in (b'', b'\0', b'\x01\x02', packed((5, 1), (1, 2)),
                    packed((0, 1)), packed((1, 0)), packed((101, 1))):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                decode(raw)
        for addition in ({'level': 0, 'move': 1}, {'level': 101, 'move': 1},
                         {'level': 1, 'move': 0}, {'level': 1, 'move': 468},
                         {'level': True, 'move': 3}, {'level': 1, 'move': 2.5}):
            with self.subTest(addition=addition), self.assertRaises(ValueError):
                add_moves(packed((1, 1)), [addition])

    def test_duplicate_pair_or_empty_addition_is_rejected(self):
        for changes in ([], [{'level': 1, 'move': 1}],
                        [{'level': 3, 'move': 2}, {'level': 3, 'move': 2}]):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                add_moves(packed((1, 1)), changes)

    def test_duplicate_source_pair_is_rejected_without_deduplicating(self):
        source = packed((1, 1), (5, 2), (5, 2))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            decode(source)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            add_moves(source, [{'level': 6, 'move': 3}])


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        archive = ndspy.narc.NARC()
        self.members = [packed((1, 1)), packed((1, 2), (5, 3)), packed((1, 4))]
        archive.files = self.members
        self.raw = archive.save()
        self.changes = [{'species': 1, 'source_sha256': digest(self.members[1]),
                         'additions': [{'level': 3, 'move': 8}]}]

    def test_only_named_member_changes_and_reapplication_is_refused(self):
        after, report = patch_archive(self.raw, self.changes, digest(self.raw))
        files = ndspy.narc.NARC(after).files
        self.assertEqual(files, [self.members[0], packed((1, 2), (3, 8), (5, 3)),
                                 self.members[2]])
        self.assertEqual(ndspy.narc.NARC(self.raw).files, self.members)
        self.assertEqual(report[0]['species'], 1)
        self.assertEqual(report[0]['added'], [{'level': 3, 'move': 8}])
        with self.assertRaisesRegex(ValueError, 'archive preimage'):
            patch_archive(after, self.changes, digest(self.raw))

    def test_foreign_member_hash_cannot_partially_patch_archive(self):
        changes = self.changes + [{'species': 2, 'source_sha256': '0' * 64,
                                  'additions': [{'level': 4, 'move': 9}]}]
        with self.assertRaisesRegex(ValueError, 'member preimage'):
            patch_archive(self.raw, changes, digest(self.raw))
        self.assertEqual(ndspy.narc.NARC(self.raw).files, self.members)

    def test_duplicate_or_out_of_bounds_member_is_rejected(self):
        with self.assertRaises(ValueError):
            patch_archive(self.raw, self.changes * 2, digest(self.raw))
        for species in (-1, 3, True):
            with self.subTest(species=species), self.assertRaises(ValueError):
                patch_archive(self.raw, [{**self.changes[0], 'species': species}], digest(self.raw))


class RomStageTests(unittest.TestCase):
    def setUp(self):
        archive = ndspy.narc.NARC()
        archive.files = [packed((1, 1)), packed((1, 2), (5, 3))]
        self.original_members = list(archive.files)
        rom = ndspy.rom.NintendoDSRom()
        rom.arm9 = b'ARM9' * 256
        rom.arm7 = b'ARM7' * 128
        rom.iconBanner = bytes(0x840)
        # a/0/{0/2,1/1,3/3}, with an unrelated file in the root.
        rom.filenames = ndspy.fnt.Folder(folders=[('a', ndspy.fnt.Folder(folders=[
            ('0', ndspy.fnt.Folder(folders=[
                ('0', ndspy.fnt.Folder(files=['2'], firstID=0)),
                ('1', ndspy.fnt.Folder(files=['1'], firstID=1)),
                ('3', ndspy.fnt.Folder(files=['3'], firstID=2))]))]))],
            files=['untouched'], firstID=3)
        rom.files = [b'private personal fixture', b'private moves fixture',
                     archive.save(), b'unrelated resource']
        self.before = rom.save() + b'opaque original trailer'
        self.spec = {'schema': 1, 'preimages': {
            path: digest(rom.getFileByName(path))
            for path in ('a/0/0/2', 'a/0/1/1', 'a/0/3/3')},
            'changes': [{'species': 1, 'source_sha256': digest(archive.files[1]),
                         'additions': [{'level': 3, 'move': 8}]}]}

    def test_install_preserves_other_files_executables_and_opaque_bytes(self):
        after, report = learnsets.apply(self.before, self.spec)
        old = ndspy.rom.NintendoDSRom(self.before)
        new = ndspy.rom.NintendoDSRom(after)
        self.assertEqual(new.files[:2], old.files[:2])
        self.assertEqual(new.files[3:], old.files[3:])
        self.assertEqual((new.arm9, new.arm7, new.iconBanner),
                         (old.arm9, old.arm7, old.iconBanner))
        self.assertEqual(ndspy.narc.NARC(new.files[2]).files,
                         [self.original_members[0], packed((1, 2), (3, 8), (5, 3))])
        fat = struct.unpack_from('<I', self.before, 0x48)[0]
        permitted = {0x14, 0x15e, 0x15f} | set(range(0x80, 0x84)) | set(range(fat + 16, fat + 24))
        self.assertTrue(all(a == b or index in permitted
                            for index, (a, b) in enumerate(zip(self.before, after))))
        self.assertEqual(report['archive_output_sha256'], digest(new.files[2]))
        self.assertEqual(report['changes'][0]['species'], 1)
        with self.assertRaisesRegex(ValueError, 'preimage'):
            learnsets.apply(after, self.spec)

    def test_foreign_personal_moves_or_learnsets_are_rejected_before_patch(self):
        for path in self.spec['preimages']:
            rom = ndspy.rom.NintendoDSRom(self.before)
            rom.setFileByName(path, rom.getFileByName(path) + b'foreign')
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'preimage'):
                learnsets.apply(rom.save(), self.spec)

    def test_missing_semantic_guard_or_wrong_schema_is_rejected(self):
        incomplete = {**self.spec, 'preimages': dict(self.spec['preimages'])}
        del incomplete['preimages']['a/0/1/1']
        for spec in (incomplete, {**self.spec, 'schema': 2}):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                learnsets.apply(self.before, spec)


if __name__ == '__main__':
    unittest.main()
