"""Accent-row geometry and identity guards, without game files."""
import struct
import unittest
from . import keyboard

class KeyboardTests(unittest.TestCase):
    def test_each_locale_has_two_terminated_thirteen_key_rows(self):
        chars = {c: i + 1 for i, c in enumerate(sorted(set(''.join(sum(keyboard.ACCENTS.values(), ())))))}
        for locale in ('FR', 'ES', 'DE'):
            rows = keyboard.rows(locale, lambda text: [chars[c] for c in text] + [65535])
            self.assertEqual([len(row) for row in rows], [28, 28])
            self.assertEqual([struct.unpack('<14H', row)[-1] for row in rows], [65535, 65535])
        with self.assertRaises(ValueError): keyboard.rows('JP', lambda _: [])

    def test_pointer_or_preimage_mismatch_refuses_without_partial_write(self):
        locations = {0x020F5670: 0, 0x02110504: 4, 0x02110518: 8,
                     0x02101E2C: 12, 0x02101F60: 40}
        original = bytearray(68); original[0] = 2
        struct.pack_into('<II', original, 4, 0x02101E2C, 0x02101F60)
        original[12:40] = original[40:68] = keyboard.PREIMAGE
        encode = lambda text: [1] * len(text) + [65535]
        result = keyboard.apply(bytes(original), lambda address, size: locations[address], 'FR', encode)
        self.assertEqual(result[0], 2)
        self.assertNotEqual(result[12:40], original[12:40])
        for position in (0, 4, 12, 40):
            changed = original.copy(); changed[position] ^= 1
            with self.assertRaises(ValueError): keyboard.apply(bytes(changed), lambda a, n: locations[a], 'DE', encode)
        self.assertEqual(original[12:40], keyboard.PREIMAGE)
