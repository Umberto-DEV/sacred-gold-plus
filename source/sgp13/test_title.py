import unittest
import struct
from sgp13 import title
from sgp12 import titolo_versione as previous

class TitleTests(unittest.TestCase):
    def input(self):
        g=bytearray(b'g'*3136);g[848:1232]=previous.etichetta()
        m=bytearray(1572);m[1446:1458]=bytes.fromhex('19701a701b701c701d701e70');m[1510:1522]=bytes.fromhex('1f7020702170227023702470')
        return bytes(g),bytes(m)

    def test_only_previous_project_label_pixels_change(self):
        g,m=self.input();new=title.replace_graphics(g,m)
        self.assertEqual(len(new),len(g));self.assertEqual(new[:848],g[:848]);self.assertEqual(new[1232:],g[1232:])
        self.assertNotEqual(new[848:1232],g[848:1232]);self.assertEqual(len(title.pixels()),384)
        self.assertTrue(all((b&15) in (0,4,14) and b>>4 in (0,4,14) for b in title.pixels()))

    def test_unknown_pixels_or_map_are_rejected(self):
        g,m=self.input()
        with self.assertRaises(ValueError):title.replace_graphics(g[:900]+b'X'+g[901:],m)
        with self.assertRaises(ValueError):title.replace_graphics(g,bytes(1572))

class BannerTests(unittest.TestCase):
    @staticmethod
    def crc(data):
        value = 0xffff
        for byte in data:
            value ^= byte
            for _ in range(8):
                value = (value >> 1) ^ (0xa001 if value & 1 else 0)
        return value

    def fixture(self):
        banner = bytearray(0x840)
        struct.pack_into('<H', banner, 0, 1)
        banner[0x20:0x240] = bytes(range(256)) * 2 + bytes(range(32))
        text = 'Pokémon HeartGold\nNintendo'.encode('utf-16-le')
        for offset in range(0x240, 0x840, 0x100):
            banner[offset:offset + len(text)] = text
        struct.pack_into('<H', banner, 2, self.crc(banner[0x20:]))
        return bytes(banner)

    def test_library_name_changes_in_every_language_without_losing_icon(self):
        self.assertTrue(callable(getattr(title, 'update_banner', None)),
                        'builder has no guarded library identity update')
        before = self.fixture()
        after = title.update_banner(before)
        self.assertEqual(len(after), len(before))
        self.assertEqual(after[:2], before[:2])
        self.assertEqual(after[4:0x240], before[4:0x240])
        for offset in range(0x240, 0x840, 0x100):
            slot = after[offset:offset + 0x100]
            self.assertEqual(slot.decode('utf-16-le').rstrip('\0'),
                             'Pokémon Sacred Gold Plus\nNintendo')
        self.assertEqual(struct.unpack_from('<H', after, 2)[0], self.crc(after[0x20:]))

    def test_invalid_banner_is_rejected_without_changing_input(self):
        self.assertTrue(callable(getattr(title, 'update_banner', None)))
        good = self.fixture()
        cases = [good[:-1], b'\x02' + good[1:], good[:50] + b'X' + good[51:]]
        foreign = bytearray(good)
        foreign[0x240:0x242] = b'X\0'
        struct.pack_into('<H', foreign, 2, self.crc(foreign[0x20:]))
        cases.append(bytes(foreign))
        for data in cases:
            with self.subTest(data=data[:4]):
                snapshot = bytes(data)
                with self.assertRaises(ValueError):
                    title.update_banner(data)
                self.assertEqual(data, snapshot)

    def test_rom_patch_is_confined_to_banner_and_rejects_bad_pointers(self):
        header = bytearray(0x400)
        struct.pack_into('<I', header, 0x68, 0x400)
        before = bytes(header) + self.fixture() + b'unchanged executable and files'
        after, report = title.apply_banner(before)
        self.assertEqual(after[:0x400], before[:0x400])
        self.assertEqual(after[0xc40:], before[0xc40:])
        self.assertTrue(report['icon_palette_preserved'])
        for offset in (0, 0x1ff, len(before) - 0x83f, 0xffffffff):
            bad = bytearray(before)
            struct.pack_into('<I', bad, 0x68, offset)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                title.apply_banner(bytes(bad))

if __name__=='__main__':unittest.main()
