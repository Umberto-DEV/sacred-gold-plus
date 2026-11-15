"""Build-time bottle-cap art: stable defaults and bounded palette variants."""
import hashlib
import struct
import unittest

from sgp13.training import cap_graphics


class CapGraphicsTests(unittest.TestCase):
    def containers(self):
        return b'RGCN' + bytes(556), b'RLCN' + bytes(548)

    def test_default_art_and_palette_remain_stable(self):
        character, palette = self.containers()
        tile, colors = cap_graphics(character, palette)
        self.assertEqual(hashlib.sha256(tile[48:]).hexdigest(),
                         '5a8e6bdb58adfbae0ea38d184afbe50f26e732d019ff0772cc94dbbeb263bca8')
        self.assertEqual(struct.unpack('<4H', colors[40:48]),
                         (0, 0x18C6, 0x4E73, 0x7FFF))
        self.assertEqual(colors[48:], bytes(504))
        self.assertEqual(tile[:48], character[:48])
        self.assertEqual(colors[:40], palette[:40])
        self.assertEqual((len(tile), len(colors)), (560, 552))

    def test_opt_in_variant_changes_only_silver_middle_color(self):
        character, palette = self.containers()
        before = cap_graphics(character, palette)
        after = cap_graphics(character, palette, silver_mid_color=0x4E74)
        self.assertEqual(after[0], before[0])
        self.assertEqual([i for i, (a, b) in enumerate(zip(before[1], after[1]))
                          if a != b], [44])
        self.assertEqual(struct.unpack_from('<H', after[1], 44)[0], 0x4E74)
        self.assertEqual(cap_graphics(character, palette, True),
                         cap_graphics(character, palette, True,
                                      silver_mid_color=0x4E74))

    def test_invalid_colors_and_containers_fail_without_mutating_inputs(self):
        character, palette = map(bytearray, self.containers())
        original = bytes(character), bytes(palette)
        for value in (-1, 0x8000, 65535, True, 1.5, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                cap_graphics(character, palette, silver_mid_color=value)
        for bad_char, bad_palette in ((character[:-1], palette),
                                      (character, palette[:-1]),
                                      (bytes(560), palette)):
            with self.assertRaises(ValueError):
                cap_graphics(bad_char, bad_palette)
        self.assertEqual((bytes(character), bytes(palette)), original)


if __name__ == '__main__':
    unittest.main()
