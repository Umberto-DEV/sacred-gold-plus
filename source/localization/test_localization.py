"""Focused admission and donor-selection regressions, without game fixtures."""
import hashlib
import struct
import unittest
from ndspy import fnt
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from translation.message_codec import Bank

from . import inventory


class AdmissionTests(unittest.TestCase):
    def image(self):
        data = bytearray(512)
        data[12:16] = b'IPKD'
        return bytes(data)

    def contracts(self, data, **changes):
        return {'DE': dict(bytes=512, sha256=hashlib.sha256(data).hexdigest(),
                           game_code='IPKD', revision=0, **changes)}

    def test_changed_bytes_cannot_inherit_a_recognized_header(self):
        data = self.image()
        self.assertEqual(inventory.identify(data, self.contracts(data)), 'DE')
        with self.assertRaisesRegex(ValueError, 'identity'):
            inventory.identify(data[:-1] + b'X', self.contracts(data))

    def test_hash_match_does_not_override_revision_or_language(self):
        for offset, value in ((15, ord('F')), (30, 1)):
            data = bytearray(self.image())
            data[offset] = value
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, 'header'):
                inventory.identify(bytes(data), self.contracts(data))

    def test_bad_fat_extent_is_rejected(self):
        data = bytearray(1024)
        struct.pack_into('<IIII', data, 0x20, 512, 0, 0, 4)
        struct.pack_into('<IIII', data, 0x30, 516, 0, 0, 4)
        struct.pack_into('<II', data, 0x48, 520, 8)
        struct.pack_into('<II', data, 520, 1020, 1025)
        with self.assertRaisesRegex(ValueError, 'FAT'):
            inventory.check_layout(bytes(data), check_crc=False)


class DonorSelectionTests(unittest.TestCase):
    def test_archive_count_change_requires_explicit_review(self):
        original = NARC()
        original.files = [b'original synthetic graphic']
        donor = NARC()
        donor.files = [b'localized synthetic graphic', b'new member']
        rows = inventory._member_rows(original.save(), original.save(), donor.save())
        self.assertEqual(rows[0]['action'], 'review')

    def test_owned_guide_member_and_anonymous_overlay_are_not_message_donors(self):
        def image(words, *, guide=False, overlay=b'original code'):
            archive = NARC()
            archive.files = [Bank.from_words([words], 42).save()]
            if guide:
                archive.files.append(b'SGG1' + bytes(16))
            rom = NintendoDSRom()
            rom.filenames = fnt.Folder([('a', fnt.Folder([('0', fnt.Folder([
                ('2', fnt.Folder([], ['7'], 0))], [], 0))], [], 0))], [], 0)
            rom.files = [archive.save(), overlay]
            return rom.save()
        original = image([1, 65535])
        core = image([1, 65535], guide=True)
        donor = image([2, 65535], overlay=b'localized code')
        report = inventory.inventory(core, {'EN': original, 'DE': donor})
        self.assertEqual(report['binary_message_members'], [1])
        self.assertEqual(report['locales']['DE']['changed_messages'], [])
        self.assertEqual(report['locales']['DE']['resources'], [])

    def test_only_unchanged_retail_messages_may_be_imported(self):
        self.assertEqual(inventory.message_action([1, 65535], [1, 65535], [2, 65535]), 'retail')
        self.assertEqual(inventory.message_action([3, 65535], [1, 65535], [2, 65535]), 'authored')
        self.assertEqual(inventory.message_action([3, 65535], None, None), 'authored')

    def test_missing_donor_for_unchanged_message_is_a_gap(self):
        with self.assertRaisesRegex(ValueError, 'donor'):
            inventory.message_action([1, 65535], [1, 65535], None)


if __name__ == '__main__':
    unittest.main()
