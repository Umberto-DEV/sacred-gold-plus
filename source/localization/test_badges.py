"""Badge composition contracts using original synthetic Nitro graphics only."""
import hashlib
import struct
import unittest

from ndspy import fnt, lz10
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom

from . import badges


def synthetic_badge(width):
    """Two original 1D sprite components: 32x16, then optional 16x16."""
    size = width * 16 // 2
    header = struct.pack('<4sHHIHH4sIHHIIIII', b'RGCN', 0xFEFF, 0x101,
                         48 + size, 16, 1, b'RAHC', 32 + size,
                         0xFFFF, 0xFFFF, 3, 16, 0, size, 24)
    # The changing border pattern catches accidental raster/sprite-order writes.
    pixels = [[(x + 3 * y) % 16 for x in range(width)] for y in range(16)]
    return header + pack_sprite(pixels, width)


def pack_sprite(pixels, width):
    values = []
    for begin, columns in ((0, 4), (32, 2)) if width == 48 else ((0, 4),):
        for tile_y in range(2):
            for tile_x in range(columns):
                for y in range(8):
                    for x in range(8):
                        values.append(pixels[tile_y * 8 + y][begin + tile_x * 8 + x])
    return bytes(values[i] | values[i + 1] << 4 for i in range(0, len(values), 2))


def unpack_sprite(raw, width):
    # Independent component reconstruction, rather than the painter's address helper.
    values = [n for b in raw[48:] for n in (b & 15, b >> 4)]
    pixels = [[0] * width for _ in range(16)]
    cursor = 0
    for begin, columns in ((0, 4), (32, 2)) if width == 48 else ((0, 4),):
        for tile_y in range(2):
            for tile_x in range(columns):
                for y in range(8):
                    pixels[tile_y * 8 + y][begin + tile_x * 8:begin + tile_x * 8 + 8] = values[cursor:cursor + 8]
                    cursor += 8
    return pixels


def synthetic_rom(game_code=b'IPKE'):
    image = NintendoDSRom()
    image.name = b'POKEMON SG'
    image.idCode = game_code
    archives = []
    for width, count, index in ((32, 346, 236), (48, 124, 123)):
        archive = NARC()
        archive.files = [b'synthetic unrelated member'] * count
        archive.files[index] = lz10.compress(synthetic_badge(width))
        archives.append(archive.save())
    image.filenames = fnt.Folder([('a', fnt.Folder([('0', fnt.Folder([
        ('0', fnt.Folder([], ['8'], 0)), ('6', fnt.Folder([], ['8'], 1))
    ], [], 0))], [], 0))], [], 0)
    image.files = archives
    return image.save()


class BadgeTests(unittest.TestCase):
    def test_localized_text_cannot_change_header_border_or_palette_indices(self):
        for width, background, ink, shadow, rectangle in (
                (32, 10, 15, 14, (2, 2, 30, 13)),
                (48, 7, 14, 15, (6, 3, 42, 13))):
            before = synthetic_badge(width)
            old = unpack_sprite(before, width)
            for label in ('FÉE', 'FEE', 'HADA'):
                with self.subTest(width=width, label=label):
                    after = badges._paint(before, width, label)
                    self.assertEqual(after[:48], before[:48])
                    self.assertEqual(len(after), len(before))
                    new = unpack_sprite(after, width)
                    left, top, right, bottom = rectangle
                    changes = 0
                    for y in range(16):
                        for x in range(width):
                            if left <= x < right and top <= y < bottom:
                                self.assertIn(new[y][x], (background, ink, shadow))
                                changes += new[y][x] != old[y][x]
                            else:
                                self.assertEqual(new[y][x], old[y][x], (x, y))
                    self.assertGreater(changes, 70)

    def test_hada_crosses_the_32_pixel_component_without_scrambling_final_a(self):
        pixels = unpack_sprite(badges._paint(synthetic_badge(48), 48, 'HADA'), 48)
        # Hand-derived final A: its top, sides and middle bar cross into component2.
        self.assertEqual(pixels[5][32:38], [7, 14, 14, 14, 14, 7])
        self.assertEqual(pixels[6][32:38], [14, 14, 15, 15, 14, 14])
        self.assertEqual(pixels[8][32:38], [14] * 6)

    def test_french_acute_accent_is_visible_without_changing_german_baseline(self):
        for width, x, y, background, ink in ((32, 16, 2, 10, 15), (48, 23, 3, 7, 14)):
            french = unpack_sprite(badges._paint(synthetic_badge(width), width, 'FÉE'), width)
            german = unpack_sprite(badges._paint(synthetic_badge(width), width, 'FEE'), width)
            self.assertEqual(french[y][x], ink)
            self.assertEqual(german[y][x], background)
            self.assertNotEqual(french, german)

    def test_compression_and_1d_pixel_layout_round_trip(self):
        for width in (32, 48):
            before = synthetic_badge(width)
            for label in ('FÉE', 'FEE', 'HADA'):
                compressed = badges._compose(lz10.compress(before), width, label)
                self.assertEqual(compressed[0], 0x10)
                after = bytes(lz10.decompress(compressed))
                self.assertEqual(after[:48], before[:48])
                self.assertEqual(pack_sprite(unpack_sprite(after, width), width), after[48:])
        with self.assertRaisesRegex(ValueError, 'storage'):
            badges._compose(synthetic_badge(32), 32, 'FEE')

    def test_foreign_locale_and_font_fallback_are_rejected(self):
        for locale in ('EN', 'IT', 'de', '', None):
            with self.subTest(locale=locale), self.assertRaisesRegex(ValueError, 'locale'):
                badges.localize_badges(b'', locale)
        for label in ('FAIRY', 'FEE ', 'Hada', ''):
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, 'label'):
                badges._paint(synthetic_badge(32), 32, label)

    def test_unknown_ncgr_layout_cannot_be_painted(self):
        for offset in (8, 12, 16, 20, 28, 40, 44):
            data = bytearray(synthetic_badge(32))
            data[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaisesRegex(ValueError, 'layout'):
                badges._paint(bytes(data), 32, 'FEE')

    def test_real_api_refuses_unpinned_member_even_in_a_matching_english_header(self):
        core = synthetic_rom()
        before = hashlib.sha256(core).digest()
        with self.assertRaisesRegex(ValueError, 'preimage'):
            badges.localize_badges(core, 'DE')
        self.assertEqual(hashlib.sha256(core).digest(), before)
        with self.assertRaisesRegex(ValueError, 'identity'):
            badges.localize_badges(synthetic_rom(b'IPKF'), 'FR')


if __name__ == '__main__':
    unittest.main()
