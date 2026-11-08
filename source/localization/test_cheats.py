"""Latest-only project cheat catalogues: identity, static gates and localization."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

try:
    from localization import cheats
except ImportError:
    cheats = None


class ProjectCheatTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(cheats, 'current localized project cheat generator missing')

    def test_all_five_catalogues_have_every_required_localized_field(self):
        for locale in ('EN', 'IT', 'FR', 'ES', 'DE'):
            words = cheats.load_words(locale)
            self.assertEqual(set(words), cheats.REQUIRED)
            for name in cheats.CODES:
                self.assertTrue(words[name + '.name'].strip())
                self.assertTrue(words[name + '.note'].strip())

    def test_preimage_checks_bind_region_and_complete_context(self):
        specification = [('ARM9:0', 0x02000002, 2, hashlib.sha256(b'AB').hexdigest())]
        self.assertTrue(cheats.check_context(specification, [('ARM9:0', 0x02000000, b'xxABxx')]))
        self.assertFalse(cheats.check_context(specification, [('overlay:2', 0x02000000, b'xxABxx')]))
        self.assertFalse(cheats.check_context(specification, [('ARM9:0', 0x02000000, b'xxACxx')]))

    def test_money_is_omitted_and_mismatched_code_is_not_relabelled_verified(self):
        accepted, omitted = cheats.select_codes([])
        self.assertFalse(accepted)
        self.assertEqual(omitted['money'], 'runtime')
        self.assertEqual(omitted['fast_text'], 'preimage')

    def test_static_hash_match_does_not_bypass_the_original_equality_guard(self):
        address = 0x0200FA78
        native = b'\x0c\x9a' + bytes(36)
        def admit(raw):
            contexts = {'transitions': [('ARM9:0', address, len(raw), hashlib.sha256(raw).hexdigest())]}
            with patch.dict(cheats.CONTEXTS, contexts, clear=True):
                return cheats.select_codes([('ARM9:0', address, raw)])
        accepted, omitted = admit(native)
        self.assertEqual(accepted, ['transitions'])
        self.assertEqual(omitted, {'money': 'runtime'})
        accepted, omitted = admit(b'\x0c\x9b' + native[2:])
        self.assertEqual(accepted, [])
        self.assertEqual(omitted['transitions'], 'preimage')

    def test_seven_project_streams_retain_original_words_and_order(self):
        # Digest of the seven independently supplied project MCH streams,
        # normalized to ASCII spaces, one stream per line, no final newline.
        digest = hashlib.sha256('\n'.join(cheats.CODES.values()).encode('ascii')).hexdigest()
        self.assertEqual(digest, '6e0175b5206089772ee2f0c7196d812fdd465e68c81c229e8b56e17b611c6766')

    def test_mch_respects_native_parser_line_and_description_limits(self):
        # melonDS ARCodeFile::Load reads 1024-byte lines and 255-byte DESC
        # fields. Long translated prose must stay in comments/README.
        with tempfile.TemporaryDirectory() as work:
            for locale in ('EN', 'IT', 'FR', 'ES', 'DE'):
                identity = dict(version='1.3.2', locale=locale, gameid='IPKE 12345678', sha256='a' * 64)
                paths = cheats.emit(locale, identity, list(cheats.CONTEXTS), {'money': 'runtime'}, Path(work)/locale)
                lines = next(p for p in paths if p.suffix == '.mch').read_bytes().splitlines()
                for line in lines:
                    self.assertLessEqual(len(line), 1022, (locale, line))
                    if line.startswith(b'DESC '):
                        self.assertLessEqual(len(line[5:]), 255, (locale, line))

    def test_wrong_whole_rom_hash_fails_before_output_creation(self):
        cfg = {'version': '1.3.2', 'targets': {'EN': {'sha256': '0' * 64, 'bytes': 512}}}
        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / 'new'
            with self.assertRaisesRegex(ValueError, 'identity'):
                cheats.generate('EN', bytes(512), output, contract=cfg)
            self.assertFalse(output.exists())

    def test_three_formats_are_localized_current_and_initially_off(self):
        identity = dict(version='1.3.2', locale='ES', gameid='IPKE 12345678', sha256='a' * 64)
        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / 'new'
            paths = cheats.emit('ES', identity, ['transitions'], {'money': 'runtime'}, output)
            self.assertEqual({p.suffix for p in paths}, {'.xml', '.mch', '.txt'})
            xml = ET.parse(next(p for p in paths if p.suffix == '.xml')).getroot()
            self.assertEqual(xml.findtext('game/gameid'), 'IPKE 12345678')
            self.assertEqual(xml.findtext('game/folder/cheat/name'), 'Transiciones rápidas')
            self.assertEqual(xml.findtext('game/folder/cheat/codes'),
                             '9200FA78 00009A0C 1200FA78 00002200 1200FA9C 00002200 D2000000 00000000')
            mch = next(p for p in paths if p.suffix == '.mch').read_text()
            self.assertIn('CODE 0 Transiciones rápidas', mch)
            self.assertIn('IPKE 12345678', mch)
            self.assertIn('a' * 64, next(p for p in paths if p.suffix == '.xml').read_text())
            readme = next(p for p in paths if p.suffix == '.txt').read_text()
            self.assertIn('a' * 64, readme)
            self.assertNotIn('1.2.3', readme)
            before = {p: p.read_bytes() for p in paths}
            with self.assertRaises(FileExistsError):
                cheats.emit('ES', identity, ['transitions'], {}, output)
            self.assertEqual(before, {p: p.read_bytes() for p in paths})

    def test_final_identity_uses_header_bytes_not_locale_filename(self):
        header = bytearray(512); header[12:16] = b'IPKE'
        self.assertEqual(cheats.game_id(bytes(header)), 'IPKE 22AC71AE')


if __name__ == '__main__':
    unittest.main()
