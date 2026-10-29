"""Native address preservation and rejection gates for the successor reserve."""
import os
from pathlib import Path
import struct
import unittest

import ndspy.code
import ndspy.rom

from sgp13 import space


RAM = 0x02000000
OLD = 0x023D8000
NEW = 0x023C8000
ARENA = 0x020D2BB0


def synthetic_code():
    code = ndspy.code.MainCodeFile(bytes(0xE0000), RAM)
    code.codeSettingsOffs = 0xBA0
    data = bytearray(code.sections[0].data)
    struct.pack_into('<I', data, ARENA - RAM, OLD)
    struct.pack_into('<II', data, 0xBA0 + 0x1C, 0xDEC00621, 0x2106C0DE)
    code.sections[0].data = data
    code.sections += [ndspy.code.MainCodeFile.Section(b'ITCM' * 128, 0x01FF8000, 0),
                      ndspy.code.MainCodeFile.Section(b'old!' * 8192, OLD, 0)]
    return code.save()


class SpaceTests(unittest.TestCase):
    def test_lower_reserve_preserves_existing_ram_bytes_and_itcm(self):
        before = ndspy.code.MainCodeFile(synthetic_code(), RAM)
        after = ndspy.code.MainCodeFile(space.expand_arm9(synthetic_code()), RAM)
        self.assertEqual(len(after.sections), len(before.sections))
        self.assertEqual(after.sections[1].data, before.sections[1].data)
        self.assertEqual(after.sections[-1].ramAddress, NEW)
        self.assertEqual(after.sections[-1].data[OLD - NEW:], before.sections[-1].data)
        self.assertEqual(struct.unpack_from('<I', after.sections[0].data, ARENA - RAM)[0], NEW)
        self.assertEqual(after.sections[-1].data[:16], struct.pack('<4I', *range(0xCA5A1900, 0xCA5A1904)))

    def test_prior_development_guard_addresses_remain_fixed(self):
        region = ndspy.code.MainCodeFile(space.expand_arm9(synthetic_code()), RAM).sections[-1]
        self.assertEqual(region.data[0x8000:0x8010],
                         struct.pack('<4I', *range(0xCA5A1700, 0xCA5A1704)))
        self.assertEqual(region.data[0xff00:0x10000],
                         b''.join(struct.pack('<I', 0xCA5A1800 | i) for i in range(64)))
        self.assertEqual(region.data[0x7f00:0x8000],
                         b''.join(struct.pack('<I', 0xCA5A1A00 | i) for i in range(64)))

    def test_overlay_bss_reaching_new_heap_boundary_is_rejected(self):
        rom = ndspy.rom.NintendoDSRom()
        rom.arm9 = synthetic_code()
        rom.arm9RamAddress = RAM
        rom.arm7 = b'ARM7' * 128
        rom.files = [bytes(16)]
        rom.arm9OverlayTable = struct.pack('<8I', 2, NEW - 16, 16, 4, 0, 0, 0, 0)
        with self.assertRaisesRegex(ValueError, 'overlay.*overlap'):
            space.expand_rom(rom.save())

    def test_wrong_arena_preimage_rejected(self):
        data = bytearray(synthetic_code())
        struct.pack_into('<I', data, ARENA - RAM, OLD - 4)
        with self.assertRaisesRegex(ValueError, 'arena'):
            space.expand_arm9(data)

    def test_overlapping_autoload_section_rejected(self):
        code = ndspy.code.MainCodeFile(synthetic_code(), RAM)
        code.sections.insert(2, ndspy.code.MainCodeFile.Section(bytes(32), NEW + 0x100, 0))
        with self.assertRaisesRegex(ValueError, 'overlap'):
            space.expand_arm9(code.save())

    def test_reapplication_rejected(self):
        expanded = space.expand_arm9(synthetic_code())
        with self.assertRaises(ValueError):
            space.expand_arm9(expanded)

    def test_repack_preserves_file_ids_and_contents(self):
        rom = ndspy.rom.NintendoDSRom()
        rom.arm9 = synthetic_code()
        rom.arm9RamAddress = RAM
        rom.arm7 = b'ARM7' * 128
        rom.files = [b'first-file', b'second-file' * 17]
        before = rom.save()
        after = ndspy.rom.NintendoDSRom(space.expand_rom(before))
        self.assertEqual(after.files, rom.files)
        self.assertEqual(after.arm7, rom.arm7)
        self.assertEqual(after.arm9OverlayTable, rom.arm9OverlayTable)

    def test_unindexed_tail_and_original_file_order_are_preserved(self):
        rom = ndspy.rom.NintendoDSRom()
        rom.arm9 = synthetic_code()
        rom.arm9RamAddress = RAM
        rom.arm7 = b'ARM7' * 128
        rom.files = [b'first-file', b'second-file' * 17]
        tail = b'opaque original trailing bytes'
        before = bytearray(rom.save() + tail)
        fat = struct.unpack_from('<I', before, 0x48)[0]
        first_end, second_start = struct.unpack_from('<II', before, fat + 4)
        self.assertGreater(second_start - first_end, 8)
        before[first_end:first_end + 8] = b'gap-test'
        output = space.expand_rom(before)
        self.assertTrue(output.endswith(tail))
        self.assertEqual(output[first_end + 0x10000:first_end + 0x10008], b'gap-test')
        self.assertEqual(len(output), len(before) + 0x10000)
        self.assertEqual(struct.unpack_from('<I', output, 0x30)[0],
                         struct.unpack_from('<I', before, 0x30)[0] + 0x10000)


@unittest.skipUnless(os.environ.get('SGP13_BASE_DIR'), 'needs private 1.2.5 inputs')
class RealRomTests(unittest.TestCase):
    def test_both_languages_preserve_all_files_and_existing_reserve(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                source = Path(os.environ['SGP13_BASE_DIR']) / f'sgp-1.2.5-{language}.nds'
                raw = source.read_bytes()
                self.assertEqual(space.identify(raw), language)
                before = ndspy.rom.NintendoDSRom(raw)
                after = ndspy.rom.NintendoDSRom(space.expand_rom(raw))
                self.assertEqual(after.files, before.files)
                self.assertEqual(after.arm7, before.arm7)
                self.assertEqual(after.arm9OverlayTable, before.arm9OverlayTable)
                self.assertEqual(after.loadArm9().sections[-1].data[0x10000:],
                                 before.loadArm9().sections[-1].data)


if __name__ == '__main__':
    unittest.main()
