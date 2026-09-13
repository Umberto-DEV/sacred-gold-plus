import copy
from pathlib import Path
import struct
import unittest

from ndspy import _common, code, rom
from native_image import reserve_itcm, replace_arm9, secure_area_crc


def main_fixture():
    data = bytearray(0x111860)
    data[0x88B40:0x88B48] = bytes.fromhex('70b56d4a051ca95c')
    data[0x8D178:0x8D180] = bytes.fromhex('38b586b000231021')
    struct.pack_into('<I', data, 0xD2C68, 0x01FF8620)
    main = code.MainCodeFile.fromSections([
        code.MainCodeFile.Section(data, 0x02000000, 0, implicit=True),
        code.MainCodeFile.Section(bytes(0x620), 0x01FF8000, 0),
        code.MainCodeFile.Section(bytes(0x60), 0x027E0000, 0x20),
    ], 0x02000000)
    main.codeSettingsOffs = 0xBA0
    return main


class NativeImageTests(unittest.TestCase):
    def test_itcm_reservation_keeps_existing_code_and_dtcm(self):
        main = main_fixture()
        old = copy.deepcopy(main)
        reserve_itcm(main, b'\x01\x20\x70\x47' * 19, 0x01FF8621, 0x01FF8625)
        self.assertEqual(main.sections[1].data[:0x620], old.sections[1].data)
        self.assertEqual(main.sections[1].data[0x620:0x620 + 76], b'\x01\x20\x70\x47' * 19)
        self.assertEqual(main.sections[2].data, old.sections[2].data)
        self.assertEqual(main.sections[2].bssSize, 0x20)
        self.assertEqual(struct.unpack_from('<I', main.sections[0].data, 0xD2C68)[0], 0x01FF8680)
        allowed = (set(range(0x88B40, 0x88B48)) | set(range(0x8D178, 0x8D180))
                   | set(range(0xD2C68, 0xD2C6C)))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(
            old.sections[0].data, main.sections[0].data))))

    def test_bad_hook_or_arena_is_rejected_before_any_change(self):
        for offset in [0x88B40, 0x8D178, 0xD2C68]:
            main = main_fixture()
            main.sections[0].data[offset] ^= 1
            before = copy.deepcopy(main)
            with self.assertRaises(ValueError):
                reserve_itcm(main, bytes(100), 0x01FF8621, 0x01FF8625)
            self.assertEqual(main.sections[0].data, before.sections[0].data)
            self.assertEqual(main.sections[1].data, before.sections[1].data)

    def test_wrong_section_or_oversize_payload_is_rejected(self):
        for mode in ['bss', 'address', 'oversize', 'entry', 'stats-entry']:
            main = main_fixture()
            if mode == 'bss': main.sections[1].bssSize = 4
            if mode == 'address': main.sections[1].ramAddress += 4
            with self.assertRaises(ValueError):
                reserve_itcm(main, bytes(0x4000 if mode == 'oversize' else 100),
                             0x01FF9001 if mode == 'entry' else 0x01FF8621,
                             0x01FF9001 if mode == 'stats-entry' else 0x01FF8625)

    def test_arm9_replacement_preserves_other_rom_sections(self):
        nds = rom.NintendoDSRom()
        nds.arm9 = b'A' * 0x12000
        nds.arm9PostData = bytes.fromhex('2106c0de0000000000000000')
        nds.arm7 = b'B' * 512
        source = nds.save()
        new = b'A' * 0x800 + b'C' * (0x10000 - 0x800)
        output = replace_arm9(source, new)
        parsed = rom.NintendoDSRom(output)
        self.assertEqual(parsed.arm9, new)
        self.assertEqual(parsed.arm9PostData, nds.arm9PostData)
        self.assertEqual(parsed.arm7, nds.arm7)
        self.assertEqual(len(output), len(source))

    def test_arm9_growth_cannot_overwrite_following_rom_data(self):
        nds = rom.NintendoDSRom()
        nds.arm9 = b'A' * 0x12000
        nds.arm7 = b'B' * 512
        source = nds.save()
        with self.assertRaises(ValueError):
            replace_arm9(source, b'C' * 0x14000)

    def test_secure_crc_delta_matches_an_independent_encrypted_prefix(self):
        clear, encrypted = b'C' * 0x800, b'E' * 0x800
        old, new = b'A' * 0x3800, b'B' * 0x3800
        self.assertEqual(secure_area_crc(clear + old, clear + new,
                         _common.crc16(encrypted + old)), _common.crc16(encrypted + new))
        with self.assertRaises(ValueError):
            secure_area_crc(clear + old, encrypted + new, 0)


if __name__ == '__main__':
    unittest.main()
