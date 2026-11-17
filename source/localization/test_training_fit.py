"""Synthetic tests: no game font, text, ROM, or advance values."""
import struct
import json
import io
import contextlib
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from localization import training_fit as fit

class TrainingFitTest(unittest.TestCase):
    def setUp(self):
        self.chars = {1: 'A', 2: 'B'}
        self.widths = bytes([48, 49])

    def test_bound_inclusive(self):
        self.assertTrue(fit.measure([1, 1, 0xffff], self.widths, self.chars, {})['fits_advance'])
        self.assertFalse(fit.measure([1, 2, 0xffff], self.widths, self.chars, {})['fits_advance'])

    def test_unknown_glyph_and_control_rejected(self):
        for words in ([3, 0xffff], [0xfffe, 42, 0, 0xffff], [1], [1, 0xffff, 1, 0xffff]):
            with self.subTest(words=words), self.assertRaises(ValueError):
                fit.measure(words, self.widths, self.chars, {})

    def test_truncated_font_metadata(self):
        for raw in (b'', struct.pack('<3I4B', 16, 16, 3, 8, 16, 2, 2) + b'\x01\x02'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                fit.font_widths(raw)

    def test_alias_mismatch(self):
        bank = [[1, 0xffff] for _ in range(7)]
        mismatch = [list(x) for x in bank]
        mismatch[4] = [2, 0xffff]
        self.assertEqual(fit.aliases([bank, bank, bank]), bank)
        with self.assertRaises(ValueError):
            fit.aliases([bank, mismatch, bank])

    def test_installed_overflow_not_hidden_by_catalogue(self):
        # All bytes and glyph widths are synthetic; the three aliases are equal.
        font = struct.pack('<3I4B', 16, 16, 2, 8, 16, 2, 2) + self.widths
        bank = SimpleNamespace(words=[[1, 1, 1, 0xffff] for _ in range(100)])
        archives = {
            'a/0/1/6': SimpleNamespace(files=[None] * 4 + [font]),
            'a/0/2/7': SimpleNamespace(files=[b'bank'] * 631),
            'a/0/1/2': SimpleNamespace(files=[SimpleNamespace(count=lambda _: 3)] * 943),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / 'rom'; rom.write_bytes(b'synthetic')
            charmap = root / 'charmap'; charmap.write_bytes(b'synthetic')
            cat = root / 'catalogue.json'
            cat.write_text(json.dumps({'language': 'DE', 'strings': {k: 'A' for k in fit.KEYS}}))
            identity = {'language': 'DE', 'rom_sha256': fit.digest(b'synthetic')}
            with patch.object(fit.guide_content, 'CHARMAP_SHA256', fit.digest(b'synthetic')), \
                 patch.object(fit, 'check_renderer'), \
                 patch.object(fit, 'check_native_chain'), \
                 patch.object(fit, 'FONT_SHA', fit.digest(font)), \
                 patch.object(fit._TEXT, 'load_charmap', return_value=(self.chars, {})), \
                 patch.object(fit, 'resource', side_effect=lambda _rom, name: name), \
                 patch.object(fit, 'archive', side_effect=lambda name: archives[name]), \
                 patch.object(fit, 'Bank', return_value=bank):
                report = fit.run(rom, charmap, identity, 'DE', cat)
            self.assertFalse(report['installed']['all_fit_advance'])
            self.assertTrue(report['catalogue_proposal']['all_fit_advance'])

    def test_service6_script_requires_one_correct_menu(self):
        rows = fit.SERVICE6_ROWS[0][1]
        payload = struct.pack('<H4BH', 750, 1, 1, 0, 1, 0x800c)
        payload += b''.join(struct.pack('<4H', 751, row, 255, value)
                            for value, row in enumerate(rows))
        payload += struct.pack('<H', 752)
        fit.check_script(payload, rows, 'service6')
        with self.assertRaisesRegex(ValueError, 'mapping'):
            fit.check_script(payload * 3, rows, 'service6')
        with self.assertRaisesRegex(ValueError, 'mapping'):
            fit.check_script(payload.replace(struct.pack('<H', 0x800c), struct.pack('<H', 0x8008), 1), rows, 'service6')

    def test_service6_installed_overflow_not_hidden(self):
        font = struct.pack('<3I4B', 16, 16, 2, 8, 16, 2, 2) + self.widths
        bank = SimpleNamespace(words=[[1, 1, 1, 0xffff] for _ in range(100)])
        archives = {
            'a/0/1/6': SimpleNamespace(files=[None] * 4 + [font]),
            'a/0/2/7': SimpleNamespace(files=[b'bank'] * 631),
            'a/0/1/2': SimpleNamespace(files=[SimpleNamespace(count=lambda _: 1)] * 943),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom = root / 'rom'; rom.write_bytes(b'synthetic')
            charmap = root / 'charmap'; charmap.write_bytes(b'synthetic')
            cat = root / 'catalogue.json'
            cat.write_text(json.dumps({'language': 'DE', 'strings': {k: 'A' for k in fit.SERVICE6_KEYS}}))
            identity = {'language': 'DE', 'rom_sha256': fit.digest(b'synthetic')}
            with patch.object(fit.guide_content, 'CHARMAP_SHA256', fit.digest(b'synthetic')), \
                 patch.object(fit, 'check_renderer'), patch.object(fit, 'check_native_chain'), \
                 patch.object(fit, 'FONT_SHA', fit.digest(font)), \
                 patch.object(fit._TEXT, 'load_charmap', return_value=(self.chars, {})), \
                 patch.object(fit, 'resource', side_effect=lambda _rom, name: name), \
                 patch.object(fit, 'archive', side_effect=lambda name: archives[name]), \
                 patch.object(fit, 'Bank', return_value=bank):
                report = fit.run(rom, charmap, identity, 'DE', cat, 'service6')
            self.assertEqual(report['profile'], 'service6')
            self.assertFalse(report['installed']['all_fit_advance'])
            self.assertTrue(report['catalogue_proposal']['all_fit_advance'])
            self.assertEqual([r['key'] for r in report['installed']['rows']], fit.SERVICE6_KEYS)

    def test_service6_template_mismatch_rejected(self):
        base = 0x02259f80
        data = bytearray(0x4000)
        template = b'A' * 48
        data[0x0225d2c8 - base:0x0225d2c8 - base + 48] = template
        struct.pack_into('<I', data, 0x0225d4c8 - base, 0x0225d2c8)
        data[0x0225c6c2 - base:0x0225c6c2 - base + 2] = bytes.fromhex('0421')
        with patch.object(fit, 'OVERLAY_SHA', fit.digest(data)), \
             patch.object(fit, 'SERVICE6_TEMPLATE_SHA', fit.digest(template)), \
             patch.object(fit, 'overlay', return_value=(base, bytes(data))):
            fit.check_renderer(b'', 'service6')
        data[0x0225d2c8 - base] ^= 1
        with patch.object(fit, 'OVERLAY_SHA', fit.digest(data)), \
             patch.object(fit, 'SERVICE6_TEMPLATE_SHA', fit.digest(template)), \
             patch.object(fit, 'overlay', return_value=(base, bytes(data))):
            with self.assertRaisesRegex(ValueError, 'geometry'):
                fit.check_renderer(b'', 'service6')

    def test_language_fails_before_rom_access(self):
        with self.assertRaisesRegex(ValueError, 'language mismatch'):
            fit.run('absent', 'absent', {'language': 'IT'}, 'DE')

    def test_fat_fnt_and_overlay_bounds(self):
        from ndspy import fnt
        name = fnt.save(fnt.Folder(files=['own']))
        data = bytearray(512)
        struct.pack_into('<4I', data, 0x40, 128, len(name), 256, 0)
        data[128:128 + len(name)] = name
        struct.pack_into('<2I', data, 256, 300, 303)
        data[300:303] = b'OWN'
        with self.assertRaises(ValueError): fit.resource(data, 'own')
        struct.pack_into('<I', data, 0x4c, 8)
        self.assertEqual(fit.resource(data, 'own'), b'OWN')
        with self.assertRaises(ValueError): fit.fat_file(data, 1)
        struct.pack_into('<2I', data, 0x50, 180, 32)
        struct.pack_into('<8I', data, 180, 27, 0x2200000, 1, 0, 0, 0, 0, 0)
        with self.assertRaisesRegex(ValueError, 'size'): fit.overlay(data, 27)
        struct.pack_into('<I', data, 188, 3)
        self.assertEqual(fit.overlay(data, 27)[1], b'OWN')
        struct.pack_into('<I', data, 208, 0x01000003)
        with patch.object(fit, 'ndspy_decomprimi_sicuro') as decode:
            with self.assertRaises(ValueError): fit.overlay(data, 27)
            decode.assert_not_called()

    def test_compressed_overlay_uses_preflight_and_exact_size(self):
        data = bytearray(512)
        struct.pack_into('<2I', data, 0x48, 256, 8)
        struct.pack_into('<2I', data, 0x50, 128, 32)
        struct.pack_into('<8I', data, 128, 27, 0x2200000, 10, 0, 0, 0, 0, 0x01000008)
        struct.pack_into('<2I', data, 256, 300, 308)
        data[300:308] = b'synthetic'
        with patch.object(fit, 'blz_verifica_ndspy', return_value=10) as preflight, \
             patch.object(fit, 'ndspy_decomprimi_sicuro', return_value=b'A' * 10) as decode:
            self.assertEqual(fit.overlay(data, 27)[1], b'A' * 10)
            preflight.assert_called_once(); decode.assert_called_once()

    def test_overlay_load_layout_mutations_rejected(self):
        data = bytearray(512)
        struct.pack_into('<2I', data, 0x48, 256, 8)
        struct.pack_into('<2I', data, 0x50, 128, 32)
        struct.pack_into('<8I', data, 128, 27, 100, 3, 4, 105, 109, 0, 0)
        struct.pack_into('<2I', data, 256, 300, 303)
        data[300:303] = b'OWN'
        layout = (100, 4, 105, 109)
        self.assertEqual(fit.overlay(data, 27, layout)[1], b'OWN')
        for field in (1, 3, 4, 5):
            with self.subTest(field=field):
                mutated = bytearray(data)
                struct.pack_into('<I', mutated, 128 + 4 * field, 999)
                with self.assertRaisesRegex(ValueError, 'layout'):
                    fit.overlay(mutated, 27, layout)
        struct.pack_into('<I', data, 128 + 28, 0x02000000)
        with self.assertRaisesRegex(ValueError, 'flags'):
            fit.overlay(data, 27, layout)

    def test_decoder_parser_error_is_rejected(self):
        data = bytearray(512)
        struct.pack_into('<2I', data, 0x48, 256, 8)
        struct.pack_into('<2I', data, 0x50, 128, 32)
        struct.pack_into('<8I', data, 128, 27, 0x2200000, 10, 0, 0, 0, 0, 0x01000008)
        struct.pack_into('<2I', data, 256, 300, 308)
        with patch.object(fit, 'blz_verifica_ndspy', return_value=10), \
             patch.object(fit, 'ndspy_decomprimi_sicuro', side_effect=RuntimeError('malformed')):
            with self.assertRaisesRegex(ValueError, 'invalid compressed overlay'):
                fit.overlay(data, 27)

    def test_charmap_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'map'; path.write_bytes(b'own')
            with self.assertRaisesRegex(ValueError, 'charmap'):
                fit.run('absent', path, {'language': 'DE', 'rom_sha256': 'a' * 64}, 'DE')

    def test_malformed_narc_becomes_value_error(self):
        from ndspy import narc
        archive = bytearray(narc.NARC.fromFilesAndNames([b'OWN']).save())
        archive[16:20] = b'NOPE'
        with self.assertRaisesRegex(ValueError, 'invalid NARC'): fit.archive(archive)

    def test_cli_identity_nonobject_json_error(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'identity'; path.write_text('[]')
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = fit.main(['--rom', 'absent', '--charmap', 'absent', '--identity', str(path), '--language', 'DE'])
            self.assertEqual(status, 2)
            self.assertEqual(json.loads(out.getvalue())['status'], 'error')

    def test_bad_rom_hash(self):
        with tempfile.TemporaryDirectory() as d:
            rom = Path(d) / 'rom'; rom.write_bytes(b'own')
            charmap = Path(d) / 'map'; charmap.write_bytes(b'own')
            with patch.object(fit.guide_content, 'CHARMAP_SHA256', fit.digest(b'own')), \
                 patch.object(fit._TEXT, 'load_charmap', return_value=({}, {})):
                with self.assertRaisesRegex(ValueError, 'ROM SHA-256 mismatch'):
                    fit.run(rom, charmap, {'language':'DE', 'rom_sha256':'a' * 64}, 'DE')

    def test_native_handler_mutation_rejected(self):
        expected = b'own handler'
        with patch.object(fit, 'NATIVE_PINS', ((100, len(expected), fit.digest(expected)),)), \
             patch.object(fit.portable, 'arm9_segments', return_value=[]), \
             patch.object(fit.portable, 'read_ram', return_value=b'bad handler'), \
             patch.object(fit, 'overlay') as get_overlay:
            with self.assertRaisesRegex(ValueError, 'native menu chain'):
                fit.check_native_chain(b'')
            get_overlay.assert_not_called()

    def test_unqualified_renderer_rejected(self):
        with patch.object(fit, 'overlay', return_value=(0, b'own synthetic bytes')):
            with self.assertRaisesRegex(ValueError, 'renderer'):
                fit.check_renderer(b'')

if __name__ == '__main__':
    unittest.main()
