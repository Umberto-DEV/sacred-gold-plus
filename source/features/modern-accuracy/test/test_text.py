"""Class A: Keen Eye description text, no ROM, no retail text.

Everything here runs on a synthetic charmap, synthetic glyph advances and a
synthetic 124-row message bank, so it proves the structure and the refusals
of `text.py` only. Window geometry and the real font are Class B
(`test_text_rom.py`).
"""
import hashlib
import importlib.util
import string
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2]
sys.path.insert(0, str(SOURCE))
from translation.message_codec import Bank  # noqa: E402

spec = importlib.util.spec_from_file_location('modern_accuracy_text', HERE.parent / 'text.py')
text = importlib.util.module_from_spec(spec)
sys.modules['modern_accuracy_text'] = text
spec.loader.exec_module(text)

NEWLINE = 0xE000
TERMINATOR = 0xFFFF
TABLE = {c: 0x100 + i for i, c in enumerate(string.ascii_letters + string.digits + ' .,;')}
TABLE['’'] = 0x1B3
TABLE['\n'] = NEWLINE
WIDTH = 5          # synthetic advance for every glyph
WIDTHS = bytes([WIDTH]) * 509


def encode(value):
    unknown = sorted({c for c in value if c not in TABLE})
    if unknown:
        raise ValueError('unmapped ' + ''.join(unknown))
    return [TABLE[c] for c in value] + [TERMINATOR]


def row_hash(words):
    return hashlib.sha256(struct.pack('<%dH' % len(words), *words)).hexdigest()


def synthetic_bank(old_row='Old synthetic one.\nOld synthetic two.', rows=124, key=0x1234):
    messages = []
    for index in range(rows):
        messages.append([(index * 7 + n) % 300 + 1 for n in range(5 + index % 7)] + [TERMINATOR])
    if rows > text.ROW:
        messages[text.ROW] = encode(old_row)
    return Bank.from_words(messages, key=key).save()


class DescriptionTextTests(unittest.TestCase):
    def test_both_languages_are_two_plain_lines(self):
        self.assertEqual(sorted(text.DESCRIPTIONS), ['EN', 'IT'])
        for language, value in text.DESCRIPTIONS.items():
            with self.subTest(language=language):
                lines = value.split('\n')
                self.assertEqual(len(lines), 2)
                for line in lines:
                    self.assertEqual(line, line.strip())
                    self.assertTrue(line)
                    self.assertNotIn('  ', line)
                self.assertTrue(lines[-1].endswith('.'))
                self.assertNotIn("'", value)          # the ROM uses the typographic apostrophe
                self.assertTrue(all(c in string.ascii_letters + ' .\n’' for c in value), value)

    def test_both_meanings_without_overpromising(self):
        en, it = text.DESCRIPTIONS['EN'].lower(), text.DESCRIPTIONS['IT'].lower()
        self.assertIn('accuracy', en)
        self.assertIn('evasion', en)
        self.assertIn('ignores', en)
        self.assertIn('precisione', it)
        self.assertIn('elusione', it)
        self.assertIn('ignora', it)
        self.assertIn('cali', it)
        # Items, weather and abilities that act on evasion are not promised away.
        for word in ('sand', 'veil', 'snow', 'cloak', 'weather', 'item', 'always', 'immune', 'all evasion',
                     'sabbia', 'neve', 'meteo', 'strument', 'sempre', 'immun'):
            self.assertNotIn(word, en)
            self.assertNotIn(word, it)

    def test_new_row_is_not_the_pinned_retail_row(self):
        for language, value in text.DESCRIPTIONS.items():
            self.assertNotEqual(row_hash(encode(value)), text.PREIMAGE_SHA256[language])


class MeasureTests(unittest.TestCase):
    def test_measure_sums_advances_per_line_and_ignores_the_terminator(self):
        words = encode('abc\nabcdef')
        self.assertEqual(text.measure(words, WIDTHS), [3 * WIDTH, 6 * WIDTH])

    def test_measure_uses_the_glyph_index_minus_one(self):
        widths = bytearray(WIDTHS)
        widths[0x100 - 1] = 9
        widths[0x101 - 1] = 3
        self.assertEqual(text.measure([0x100, 0x101, TERMINATOR], bytes(widths)), [12])

    def test_unknown_glyph_control_and_bad_terminator_are_refused(self):
        for words in ([510, TERMINATOR], [0, TERMINATOR], [0xFFFE, 1, 0, TERMINATOR],
                      [0x100], [0x100, TERMINATOR, 0x100, TERMINATOR]):
            with self.subTest(words=words):
                with self.assertRaises(ValueError):
                    text.measure(words, WIDTHS)

    def test_fit_report_covers_both_real_windows(self):
        report = text.fit_report(encode('abc\nabc'), WIDTHS)
        self.assertEqual(sorted(report['windows']), ['battle_summary_skills', 'summary_skills'])
        self.assertEqual(report['lines'], [3 * WIDTH, 3 * WIDTH])
        self.assertTrue(report['fits'])
        for window in report['windows'].values():
            self.assertTrue(window['fits'])
            self.assertEqual(window['lines'], 2)

    def test_line_wider_than_narrowest_window_is_refused(self):
        limit = text.WINDOWS['battle_summary_skills']['usable_px']
        self.assertEqual(limit, 144)
        ok = 'a' * (limit // WIDTH)
        too_wide = 'a' * (limit // WIDTH + 1)
        self.assertTrue(text.fit_report(encode(ok + '\nb'), WIDTHS)['fits'])
        with self.assertRaises(ValueError):
            text.fit_report(encode(too_wide + '\nb'), WIDTHS)

    def test_third_line_and_oversized_string_are_refused(self):
        with self.assertRaises(ValueError):
            text.fit_report(encode('a\nb\nc'), WIDTHS)
        with self.assertRaises(ValueError):
            text.fit_report(encode('a' * 130), bytes([1]) * 509)

    def test_window_constants_come_from_the_native_templates(self):
        summary = text.WINDOWS['summary_skills']
        battle = text.WINDOWS['battle_summary_skills']
        self.assertEqual((summary['width_px'], summary['height_px'], summary['text_x']), (152, 32, 3))
        self.assertEqual((battle['width_px'], battle['height_px'], battle['text_x']), (144, 32, 0))
        self.assertEqual(summary['usable_px'], 149)
        self.assertEqual(battle['usable_px'], 144)


class PatchBankTests(unittest.TestCase):
    def patch(self, language='EN', raw=None, **extra):
        raw = synthetic_bank() if raw is None else raw
        old_hash = row_hash(Bank(raw).words[text.ROW])
        return raw, text.patch_bank(raw, language, encode, expected_sha=old_hash, widths=WIDTHS, **extra)

    def test_row_51_becomes_the_expected_description(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                raw, (patched, receipt) = self.patch(language)
                words = Bank(patched).words
                self.assertEqual(words[text.ROW], encode(text.DESCRIPTIONS[language]))
                self.assertNotEqual(patched, raw)
                self.assertEqual(receipt['row'], text.ROW)
                self.assertEqual(receipt['language'], language)
                self.assertEqual(receipt['new_sha256'], row_hash(words[text.ROW]))
                self.assertEqual(receipt['bank_bytes_after'], len(patched))
                self.assertEqual(receipt['bank_bytes_before'], len(raw))

    def test_every_other_row_is_identical_decoded_and_encrypted(self):
        raw, (patched, receipt) = self.patch('IT')
        before, after = Bank(raw), Bank(patched)
        self.assertEqual(after.key, before.key)
        self.assertEqual(len(after.words), len(before.words))
        for index, (b, a) in enumerate(zip(before.words, after.words)):
            if index != text.ROW:
                self.assertEqual(a, b, index)
        self.assertEqual(receipt['rows_identical'], 123)
        # Encrypted payload bytes of every other row are copied verbatim.
        for index in range(124):
            if index != text.ROW:
                start, end = text.row_span(raw, index)
                new_start, new_end = text.row_span(patched, index)
                self.assertEqual(patched[new_start:new_end], raw[start:end], index)

    def test_measures_are_in_the_receipt(self):
        _, (_, receipt) = self.patch('EN')
        expected = [len(line) * WIDTH for line in text.DESCRIPTIONS['EN'].split('\n')]
        self.assertEqual(receipt['lines_px'], expected)
        self.assertEqual(receipt['line_count'], 2)
        self.assertEqual(sorted(receipt['windows']), ['battle_summary_skills', 'summary_skills'])
        self.assertTrue(all(w['fits'] for w in receipt['windows'].values()))

    def test_wrong_foreign_or_truncated_preimage_is_refused(self):
        raw = synthetic_bank()
        with self.assertRaises(ValueError):          # default pin is the retail row, not this one
            text.patch_bank(raw, 'EN', encode, widths=WIDTHS)
        with self.assertRaises(ValueError):
            text.patch_bank(raw, 'EN', encode, expected_sha='0' * 64, widths=WIDTHS)
        with self.assertRaises(ValueError):
            text.patch_bank(synthetic_bank(old_row='Other.\nText.'), 'EN', encode,
                            expected_sha=row_hash(Bank(raw).words[text.ROW]), widths=WIDTHS)
        with self.assertRaises(ValueError):
            text.patch_bank(raw[:-2], 'EN', encode, expected_sha=row_hash(Bank(raw).words[text.ROW]), widths=WIDTHS)
        with self.assertRaises(ValueError):
            text.patch_bank(synthetic_bank(rows=123), 'EN', encode, expected_sha='0' * 64, widths=WIDTHS)

    def test_already_patched_bank_is_refused(self):
        raw = synthetic_bank()
        old_hash = row_hash(Bank(raw).words[text.ROW])
        patched, _ = text.patch_bank(raw, 'EN', encode, expected_sha=old_hash, widths=WIDTHS)
        with self.assertRaises(ValueError):
            text.patch_bank(patched, 'EN', encode, expected_sha=old_hash, widths=WIDTHS)
        with self.assertRaises(ValueError):
            text.patch_bank(patched, 'EN', encode, expected_sha=row_hash(encode(text.DESCRIPTIONS['EN'])), widths=WIDTHS)

    def test_non_canonical_layout_is_refused(self):
        raw = synthetic_bank()
        old_hash = row_hash(Bank(raw).words[text.ROW])
        with self.assertRaises(ValueError):          # trailing padding would be dropped silently
            text.patch_bank(raw + b'\x00\x00', 'EN', encode, expected_sha=old_hash, widths=WIDTHS)

    def test_language_and_width_inputs_are_checked(self):
        raw = synthetic_bank()
        old_hash = row_hash(Bank(raw).words[text.ROW])
        for language in ('FR', 'en', '', None):
            with self.assertRaises(ValueError):
                text.patch_bank(raw, language, encode, expected_sha=old_hash, widths=WIDTHS)
        with self.assertRaises(ValueError):
            text.patch_bank(raw, 'EN', encode, expected_sha=old_hash, widths=bytes([40]) * 509)
        with self.assertRaises(ValueError):
            text.patch_bank(raw, 'EN', encode, expected_sha=old_hash, widths=WIDTHS[:-1])

    def test_unmapped_character_is_refused_not_replaced(self):
        raw = synthetic_bank()
        old_hash = row_hash(Bank(raw).words[text.ROW])
        reduced = dict(TABLE)
        del reduced['’']
        def strict(value):
            if any(c not in reduced for c in value):
                raise ValueError('unmapped')
            return [reduced[c] for c in value] + [TERMINATOR]
        with self.assertRaises(ValueError):
            text.patch_bank(raw, 'IT', strict, expected_sha=old_hash, widths=WIDTHS)

    def test_independent_row_decoder_matches_the_codec(self):
        raw = synthetic_bank()
        bank = Bank(raw)
        for index in (0, 1, 50, 51, 52, 123):
            self.assertEqual(text.decode_row(raw, index), bank.words[index])
        with self.assertRaises(ValueError):
            text.decode_row(raw, 124)


class LoadersTests(unittest.TestCase):
    def test_charmap_hash_is_pinned_and_checked(self):
        self.assertEqual(text.CHARMAP_SHA256, '58861d34f40623fd2a9b29c10a79ee2ec872182285a288381759a3b251412ded')
        with self.assertRaises((ValueError, OSError)):
            text.load_charmap(HERE / 'does-not-exist.txt')

    def test_crc16_matches_the_known_check_value(self):
        self.assertEqual(text.crc16(b'123456789'), 0x4B37)


if __name__ == '__main__':
    unittest.main()
