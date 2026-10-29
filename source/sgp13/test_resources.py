"""Resource growth must not repack unrelated files or opaque cartridge bytes."""
import struct
import unittest

import ndspy.rom

from sgp12.rom import crc16
from sgp13.resources import append_file


class ResourceTests(unittest.TestCase):
    def fixture(self):
        rom = ndspy.rom.NintendoDSRom()
        rom.arm9 = b'ARM9' * 256
        rom.arm7 = b'ARM7' * 128
        rom.files = [b'original first', b'original second']
        return rom.save() + b'unindexed cartridge trailer'

    def test_append_preserves_all_bytes_except_declared_header_and_fat(self):
        before = self.fixture()
        payload = b'new resource' * 67
        after = append_file(before, 1, payload)
        fat = struct.unpack_from('<I', before, 0x48)[0]
        start, end = struct.unpack_from('<II', after, fat + 8)
        self.assertGreaterEqual(start, len(before))
        self.assertEqual(start % 512, 0)
        self.assertEqual(after[start:end], payload)
        self.assertEqual(len(after), end)
        self.assertEqual(ndspy.rom.NintendoDSRom(after).files,
                         [b'original first', payload])
        permitted = {0x14, 0x15e, 0x15f} | set(range(0x80, 0x84)) | set(range(fat + 8, fat + 16))
        self.assertTrue(all(a == b or i in permitted
                            for i, (a, b) in enumerate(zip(before, after))))
        self.assertEqual(struct.unpack_from('<H', after, 0x15e)[0], crc16(after[:0x15e]))
        self.assertEqual(struct.unpack_from('<I', after, 0x80)[0], len(after))

    def test_bad_file_id_and_truncated_directory_are_rejected(self):
        before = self.fixture()
        for file_id in (-1, 2, 999):
            with self.subTest(file_id=file_id), self.assertRaises(ValueError):
                append_file(before, file_id, b'x')
        broken = bytearray(before)
        struct.pack_into('<I', broken, 0x48, len(broken) - 4)
        with self.assertRaises(ValueError):
            append_file(broken, 0, b'x')

    def test_truncated_member_and_empty_payload_are_rejected(self):
        before = bytearray(self.fixture())
        fat = struct.unpack_from('<I', before, 0x48)[0]
        struct.pack_into('<I', before, fat + 12, len(before) + 1)
        with self.assertRaises(ValueError):
            append_file(before, 1, b'x')
        with self.assertRaises(ValueError):
            append_file(self.fixture(), 0, b'')


if __name__ == '__main__':
    unittest.main()
