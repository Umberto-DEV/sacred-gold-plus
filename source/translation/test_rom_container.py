import struct
import unittest

from ndspy import _common, fnt, rom

from rom_container import append_files


def fixture():
    image = rom.NintendoDSRom()
    image.name = b'TEST'
    image.nintendoLogo = bytes(156)
    image.arm9 = b'ARM9' * 128
    image.arm7 = b'ARM7' * 128
    image.filenames = fnt.Folder(files=['first.dat', 'keep.dat'])
    image.files = [b'old data', b'must remain identical']
    return image.save()


class ContainerTests(unittest.TestCase):
    def test_append_preserves_other_files_and_code(self):
        source = fixture()
        result, changes = append_files(source, {'first.dat': b'new data' * 150})
        parsed = rom.NintendoDSRom(result)
        self.assertEqual(parsed.getFileByName('first.dat'), b'new data' * 150)
        self.assertEqual(parsed.getFileByName('keep.dat'), b'must remain identical')
        self.assertEqual(parsed.arm9, rom.NintendoDSRom(source).arm9)
        self.assertEqual(parsed.arm7, rom.NintendoDSRom(source).arm7)
        self.assertEqual(changes[0]['new_start'] % 512, 0)
        self.assertEqual(struct.unpack_from('<I', result, 0x80)[0], len(result))
        self.assertEqual(struct.unpack_from('<H', result, 0x15E)[0], _common.crc16(result[:0x15E]))
        allowed = set(range(0x80, 0x84)) | {0x14, 0x15E, 0x15F}
        allowed.update(range(changes[0]['fat_entry'], changes[0]['fat_entry'] + 8))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(source, result))))

    def test_unknown_file_and_corrupt_fat_are_rejected(self):
        source = fixture()
        with self.assertRaises(ValueError):
            append_files(source, {'missing.dat': b'new'})
        damaged = bytearray(source)
        struct.pack_into('<I', damaged, 0x48, len(source) + 100)
        with self.assertRaises(ValueError):
            append_files(damaged, {'first.dat': b'new'})

    def test_empty_patch_is_byte_identical(self):
        source = fixture()
        self.assertEqual(append_files(source, {}), (source, []))

    def test_reuse_keeps_existing_offset_and_other_file(self):
        source = fixture()
        result, changes = append_files(source, {'first.dat': b'short'}, reuse_existing=True)
        self.assertEqual(len(result), len(source))
        self.assertEqual(changes[0]['old_start'], changes[0]['new_start'])
        parsed = rom.NintendoDSRom(result)
        self.assertEqual(parsed.getFileByName('first.dat'), b'short')
        self.assertEqual(parsed.getFileByName('keep.dat'), b'must remain identical')

    def test_reuse_growth_never_overwrites_next_file(self):
        source = fixture()
        result, changes = append_files(source, {'first.dat': bytes(2000)}, reuse_existing=True)
        self.assertGreaterEqual(changes[0]['new_start'], len(source))
        self.assertEqual(rom.NintendoDSRom(result).getFileByName('keep.dat'), b'must remain identical')

    def test_small_growth_reuses_only_uniform_padding(self):
        for padding in (0, 255, 123):
            source = bytearray(fixture())
            fat = struct.unpack_from('<I', source, 0x48)[0]
            start, end = struct.unpack_from('<II', source, fat)
            source[end:end + 4] = bytes([padding]) * 4
            result, changes = append_files(source, {'first.dat': b'new data++++'}, reuse_existing=True)
            if padding in (0, 255):
                self.assertEqual(changes[0]['new_start'], start)
                self.assertEqual(len(result), len(source))
            else:
                self.assertGreaterEqual(changes[0]['new_start'], len(source))
                self.assertEqual(result[end:end + 4], bytes([padding]) * 4)
            self.assertEqual(rom.NintendoDSRom(result).getFileByName('keep.dat'), b'must remain identical')

    def test_capacity_grows_only_when_needed(self):
        source = bytearray(fixture())
        source[0x14] = 0
        result, _ = append_files(source, {'first.dat': bytes(140000)})
        self.assertEqual(result[0x14], 1)
        self.assertLessEqual(len(result), 0x20000 << result[0x14])


if __name__ == '__main__':
    unittest.main()
