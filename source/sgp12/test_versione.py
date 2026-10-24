"""Persistent release title and strict data-only update contract; no game assets."""
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from . import versione as v
from .rom import Rifiuto, sha

BUILD = Path(__file__).parent / 'build'
# Own text payloads only. Reconstruct the previous release's title patch.
def bank(language):
    raw = bytearray((BUILD / 'opzioni' / ('testi-' + language + '.bin')).read_bytes())
    title = json.loads((BUILD / 'manutenzione/versione.json').read_text())['titolo'][language]
    p = title['offset']
    raw[p:p + len(bytes.fromhex(title['prima']))] = bytes.fromhex(title['dopo'])
    return bytes(raw)


def text_at(raw, index):
    pos = int.from_bytes(raw[index*2:index*2+2], 'little')
    chars = []
    while pos + 2 <= len(raw):
        c = int.from_bytes(raw[pos:pos+2], 'little')
        pos += 2
        if c == 0xffff:
            return tuple(chars)
        chars.append(c)
    raise AssertionError('unterminated title')


def title_codes():
    codes = {' ': 0x1de, '.': 0x1ae}
    codes.update({chr(65+i): 0x12b+i for i in range(26)})
    codes.update({chr(97+i): 0x145+i for i in range(26)})
    codes.update({str(i): 0x121+i for i in range(10)})
    return tuple(codes[c] for c in 'Sacred Gold Plus 1.2.5')


class VersionTitleTests(unittest.TestCase):
    def test_both_screens_show_current_version_in_both_languages(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                old = bank(language)
                new = v.aggiorna_testi(old, language)
                self.assertEqual(len(new), len(old))
                self.assertEqual(text_at(new, 0), title_codes())
                self.assertEqual(text_at(new, 20), title_codes())
                for index in set(range(29)) - {0, 20}:
                    self.assertEqual(text_at(new, index), text_at(old, index))
                self.assertEqual(v.verifica_testi(old, new, language)['esito'], 'VERDE')

    def test_rejects_damaged_wrong_language_or_already_updated_bank(self):
        original = bank('EN')
        bad = bytearray(original)
        bad[6] ^= 1
        for raw, lang in ((bytes(bad), 'EN'), (original[:-1], 'EN'),
                          (original, 'IT'), (original, 'XX'),
                          (v.aggiorna_testi(original, 'EN'), 'EN')):
            with self.subTest(language=lang, size=len(raw)):
                with self.assertRaises(Rifiuto):
                    v.aggiorna_testi(raw, lang)

    def test_independent_reader_rejects_missing_menu_title_and_extra_changes(self):
        old = bank('IT')
        good = v.aggiorna_testi(old, 'IT')
        bad_alias = old[:2] + good[2:]
        bad_version = bytearray(good)
        pos = int.from_bytes(old[40:42], 'little')
        bad_version[pos:pos+44] = old[pos:pos+44]
        bad_padding = bytearray(good)
        bad_padding[-1] ^= 1
        for bad in (old, bad_alias, bytes(bad_version), bytes(bad_padding), good+b'!'):
            with self.assertRaises(Rifiuto):
                v.verifica_testi(old, bad, 'IT')

    def test_whole_image_preserves_save_code_header_canary_and_every_other_byte(self):
        # Synthetic NDS layout with one autoload section containing our own text.
        header = bytearray(0x400)
        arm = bytearray(0xc10 + 1024)
        struct.pack_into('<4I', header, 0x20, 0x400, 0x02000000, 0x02000000, len(arm))
        struct.pack_into('<3I', arm, 0xba0, 0x02000c00, 0x02000c0c, 0x02000c10)
        struct.pack_into('<3I', arm, 0xc00, 0x023da800, 1024, 0)
        arm[0xc10:0xc10+1008] = bank('EN')
        arm[-16:] = b'untouched-canary'
        from ndspy import fnt, narc
        from .test_titolo_versione import fixture
        gfx, tilemap = fixture()
        names = fnt.Folder([('a', fnt.Folder([('0', fnt.Folder([
            ('4', fnt.Folder([], ['6'], 0))], [], 0))], [], 0))], [], 0)
        names_raw = fnt.save(names)
        header[0x200:0x200+len(names_raw)] = names_raw
        archive = narc.NARC()
        archive.files = [b'']*18
        archive.files[15], archive.files[17] = gfx, tilemap
        payload = archive.save()
        start = len(header) + len(arm)
        struct.pack_into('<4I', header, 0x40, 0x200, len(names_raw), 0x300, 8)
        struct.pack_into('<II', header, 0x300, start, start+len(payload))
        old = bytes(header + arm) + payload + b'unchanged save machinery and game data'
        with patch.dict(v.ROM_AMMESSE, {sha(old): 'EN'}), patch.dict(
                v.titolo_versione.ORIGINALI, {15: sha(gfx), 17: sha(tilemap)}):
            new, report = v.applica(old)
            self.assertEqual(report['versione'], '1.2.5')
            self.assertEqual(v.rileggi(old, new)['esito'], 'VERDE')
            start = 0x400 + 0xc10
            self.assertEqual(old[:start], new[:start])
            without_graphics = v.titolo_versione.applica(old)
            self.assertEqual(without_graphics[start+1008:], new[start+1008:])
            damaged = bytearray(new)
            damaged[-1] ^= 1
            with self.assertRaises(Rifiuto):
                v.rileggi(old, bytes(damaged))

    def test_unrecognised_rom_is_refused(self):
        with self.assertRaises(Rifiuto):
            v.applica(b'not a ROM')

    def test_final_stage_is_in_public_verifier(self):
        from .verifica import ORDINE_STADI
        self.assertEqual(ORDINE_STADI[-2:], ('manutenzione', 'versione'))
