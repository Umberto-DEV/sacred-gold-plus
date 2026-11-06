"""Class B: complete authored EN/IT UIR1 compile/readback, in RAM only.

SGP131_BASE_EN/IT (or SGP_UI_RESOURCE_EN/IT) and SGP_PRET_SOURCE or
SGP131_UI_COPY_CHARMAP supply immutable private inputs. Missing inputs skip
explicitly; SGP_UI_COPY_REQUIRE_INPUTS=1 requires both. No extracted text/font,
ROM, save, replacement NARC or renderer output is written.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from translation.message_codec import Bank, unpack_name
from . import ui_copy, ui_resource, ui_resource_verify

SOURCE = Path(__file__).resolve().parents[1]
PINS = {'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
        'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136)}
CHARMAP_SHA = '58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded'
WIDTHS_SHA = '9056ed8029423336c0c7d7cf88c8e04841f09849bf431ce6d1c6ebebd4358e84'


def digest(path):
    state = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            state.update(block)
    return state.hexdigest()


class CanonicalCopyTests(unittest.TestCase):
    def _check(self, language):
        configured = os.environ.get('SGP131_BASE_' + language) or os.environ.get('SGP_UI_RESOURCE_' + language)
        pret = os.environ.get('SGP_PRET_SOURCE')
        charmap = os.environ.get('SGP131_UI_COPY_CHARMAP') or (str(Path(pret) / 'charmap.txt') if pret else None)
        if not configured or not charmap or not Path(configured).is_file() or not Path(charmap).is_file():
            message = 'missing canonical ' + language + ' ROM / pinned external charmap for UI copy'
            if os.environ.get('SGP_UI_COPY_REQUIRE_INPUTS') == '1':
                self.fail(message)
            self.skipTest(message)
        path, charmap = Path(configured), Path(charmap)
        original_hash = digest(path)
        self.assertEqual((original_hash, path.stat().st_size), PINS[language])
        self.assertEqual(digest(charmap), CHARMAP_SHA)
        spec = importlib.util.spec_from_file_location('authored_copy_native_codec', SOURCE / 'features/options/tools/codifica_testo.py')
        codec = importlib.util.module_from_spec(spec); spec.loader.exec_module(codec)
        table, _ = codec.carica_charmap(charmap)
        def encode(text):
            return codec.codifica(text, table)
        v4 = path.read_bytes()
        native = NintendoDSRom(v4)
        font = bytes(NARC(native.getFileByName('a/0/1/6')).files[0])
        self.assertEqual(hashlib.sha256(font).hexdigest(), '9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73')
        widths = font[struct.unpack_from('<I', font, 4)[0]:]
        self.assertEqual((len(widths), hashlib.sha256(widths).hexdigest()), (509, WIDTHS_SHA))
        catalogue = ui_copy.load_catalogue((SOURCE / 'sgp131/data/ui-copy.json').read_text())
        # Pure helper and accepted compiler/readback perform no filesystem I/O.
        with patch('builtins.open', side_effect=AssertionError('UI copy API file I/O')):
            authored, geometry = ui_copy.encode_catalogue(catalogue, language, encode, widths)
            replacement, receipt = ui_resource.compile_resource(v4, authored)
            verified = ui_resource_verify.verify_resource(v4, replacement, authored)
        self.assertEqual(verified, receipt)
        self.assertLessEqual(receipt['member_bytes'], 69632)
        self.assertEqual(receipt['species_entries'], 493)
        self.assertEqual(receipt['asset_bytes'], 48320)
        self.assertEqual(receipt['authored_entries'], 144)
        self.assertEqual(receipt['species_text_bytes'], 8172)
        self.assertEqual(receipt['authored_text_bytes'], geometry['authored_text_bytes'])
        self.assertEqual(receipt['member_bytes'], (60564 + geometry['authored_budget_bytes'] + 3) & ~3)
        self.assertEqual(receipt['widths_crc32'], 0x885AB7FC)
        self.assertEqual(ui_copy.c_header(catalogue), (SOURCE / 'features/settings-ui/catalog.h').read_text())
        # Separate directory parser and old species decoder: all493 survive exactly.
        member = bytes(NARC(replacement).files[51])
        count = struct.unpack_from('<I', member, 100)[0]
        directory = [struct.unpack_from('<HHI', member, 48448 + 8 * i) for i in range(count)]
        self.assertEqual([k for k, _, _ in directory], list(range(1, 145)) + list(range(4097, 4590)))
        expected_names = Bank(NARC(native.getFileByName('a/0/2/7')).files[237]).words
        longest_species = 0
        for identity, units, offset in directory:
            actual = struct.unpack_from('<%dH' % units, member, offset)
            if identity >= 4097:
                self.assertEqual(actual, tuple(unpack_name(expected_names[identity - 4096])))
                self.assertTrue(all(1 <= word <= 509 for word in actual[:-1]))
                longest_species = max(longest_species, sum(widths[word - 1] for word in actual[:-1]))
            else:
                self.assertEqual(actual, authored[identity])
                entry = catalogue['entries'][identity - 1]
                line_count, glyphs, pixels = 1, 0, 0
                actual_widths = []
                for word in actual:
                    if word in (0xE000, 65535):
                        self.assertLessEqual(glyphs, 128)
                        self.assertLessEqual(pixels, 232)
                        actual_widths.append(pixels); glyphs = pixels = 0
                        if word == 0xE000: line_count += 1
                    else:
                        self.assertTrue(1 <= word <= 509)
                        glyphs += 1; pixels += widths[word - 1]
                self.assertEqual(actual_widths, geometry['entries'][entry['name']]['line_widths'])
                self.assertLessEqual(line_count, 4 if entry['role'] == 'preview_info' else 7 if entry['role'] in ('body', 'info') else 1)
        names = ui_copy.ids(catalogue)
        def native_width(name):
            return sum(widths[w - 1] for w in authored[names[name]][:-1])
        for name in ('UNAVAILABLE', 'EMPTY', 'METHOD', 'NO_TARGET', 'PRO', 'CHARGE'):
            entry = geometry['entries']['NOTICE_' + name]
            self.assertEqual(entry['role'], 'context')
            self.assertEqual(len(entry['line_widths']), 1)
            self.assertLessEqual(entry['line_widths'][0], 200)
        preview_widths = geometry['entries']['PREVIEW_TEXT']['line_widths']
        self.assertLessEqual(len(preview_widths), 2)
        self.assertTrue(all(width <= 200 for width in preview_widths), preview_widths)
        # Long species and the current method share ordinary label/arrows geometry.
        self.assertLessEqual(34 + native_width('ROW_TARGET') + longest_species, 240)
        self.assertLessEqual(longest_species + 8, 232)
        self.assertLessEqual(34 + native_width('STATUS_METHOD') + max(native_width(n) for n in catalogue['methods']), 240)
        for label, value in [('STATUS_SUCCESSES', '40'), ('STATUS_ODDS', '1/4096'), ('STATUS_STEPS', '40/40')]:
            self.assertLessEqual(native_width(label) + 8 + sum(widths[w - 1] for w in encode(value)[:-1]), 232)
        # Native row labels start at local x17. Alternatives need a13px gap
        # before their first tile; each tile is glyph advance+7px and the
        # intervening gap is3px. The last tile ends at exclusive x224, leaving
        # room for the right arrow at228..232 and the shell inset through235.
        for row, plan in zip(catalogue['rows'], geometry['rows']):
            expected = 17 + native_width(row['label']) + 13 + sum(native_width(n) + 7 for n in row['values']) + 3 * (len(row['values']) - 1)
            self.assertEqual(plan['all_required_px'], expected)
            self.assertLessEqual(plan['required_px'], 224)
        self.assertEqual(geometry['rows'][10]['presentation'], 'selector')
        self.assertEqual(digest(path), original_hash)
        self.assertEqual(digest(charmap), CHARMAP_SHA)
        print(json.dumps(dict(language=language, receipt=receipt, geometry=geometry,
                              longest_species_px=longest_species, inputs_unchanged=True,
                              all_493_species_checked=True, generated_files=0), sort_keys=True))

    def test_english_full_catalogue_compiles_with_all_species(self):
        self._check('EN')

    def test_italian_full_catalogue_compiles_with_all_species(self):
        self._check('IT')


if __name__ == '__main__':
    unittest.main()
