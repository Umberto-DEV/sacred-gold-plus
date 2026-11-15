"""Finite onboarding bank and locale contract tests."""
import unittest
from localization import native_text


class OnboardingVersion(unittest.TestCase):
    def test_regional_active_title_is_current_but_inert_title_is_historical(self):
        for locale in ('FR', 'ES', 'DE'):
            with self.subTest(locale=locale):
                strings = native_text.onboarding_strings(locale)
                self.assertEqual(strings['c_titolo'], 'Sacred Gold Plus V1.3.3')
                self.assertEqual(strings['p_titolo'], 'Sacred Gold Plus V1.3.2')

    def test_bank_repack_preserves_other_ids_and_rejects_corruption(self):
        from sgp131 import onboarding_version as V
        import struct
        encode = lambda s: [ord(c) for c in s] + [0xFFFF]
        strings = {k: 'x'+str(i) for i, k in enumerate(native_text.ONBOARDING_IDS)}
        strings['p_titolo'] = strings['c_titolo'] = 'Sacred Gold Plus V1.3'
        old = native_text.pack_onboarding(strings, encode, lambda words: len(words)*5)
        new = V.transform(old, encode, lambda words: len(words)*5)
        before, after = V.parse(old), V.parse(new)
        self.assertEqual(after[20], struct.pack('<%dH' % len(encode(V.TITLE)), *encode(V.TITLE)))
        self.assertEqual([v for i,v in enumerate(before) if i != 20],
                         [v for i,v in enumerate(after) if i != 20])
        self.assertEqual(before[0], after[0])
        V.verify_transition(old, new, encode, 'Sacred Gold Plus V1.3')
        odd_offset = b'\x01\x00' + new[2:]
        nonzero_suffix = new[:-1] + b'\x01'
        self.assertEqual(len(odd_offset), V.SIZE)
        self.assertEqual(len(nonzero_suffix), V.SIZE)
        for broken in (new[:-1], odd_offset, nonzero_suffix):
            with self.subTest(broken=broken[:2]), self.assertRaises(ValueError):
                V.verify_transition(old, broken, encode, 'Sacred Gold Plus V1.3')
        bad = bytearray(new); bad[struct.unpack_from('<H',bad,2)[0]] ^= 1
        with self.assertRaises(ValueError):
            V.verify_transition(old, bytes(bad), encode, 'Sacred Gold Plus V1.3')
        with self.assertRaises(ValueError):
            V.verify_transition(old, old, encode, 'Sacred Gold Plus V1.3')
        with self.assertRaises(ValueError):
            V.transform(old, encode, lambda words: 205)
        bad_offset = bytearray(new); struct.pack_into('<H', bad_offset, 0, 1006)
        bad_offset[1006:1008] = b'\0\0'
        with self.assertRaises(ValueError):
            V.parse(bytes(bad_offset))
        with self.assertRaises(ValueError):
            V.pack([bytes(1000) + b'\xff\xff'] * 29)
        def long_encode(text):
            return ([1] * 64 + [0xFFFF]) if text == V.TITLE else encode(text)
        with self.assertRaises(ValueError):
            V.transform(old, long_encode, lambda words: 1)

    def test_onboarding_bank_cannot_be_granted_to_mechanical_stage(self):
        from sgp131 import mechanics_stages as ms
        row = {'name': 'injected', 'start': 0x023DA800, 'bytes': 1, 'capacity': 1024}
        with self.assertRaisesRegex(ms.CompositionError, 'overlaps UI-written bytes'):
            ms.reserve_grants(b'', 'test', 'injected', [row])

    def test_new_source_is_pinned(self):
        import hashlib
        from pathlib import Path
        from sgp131 import ui_compile
        path = Path(ui_compile.SOURCE) / 'sgp131/onboarding_version.py'
        self.assertEqual(ui_compile.SOURCE_PINS['sgp131/onboarding_version.py'],
                         hashlib.sha256(path.read_bytes()).hexdigest())
