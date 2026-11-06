"""Class B: Keen Eye description on the real V4 EN/IT images, in memory only.

Inputs (read-only, hash-checked first):
  SGP_TEXT_ROM_EN / SGP_TEXT_ROM_IT   default local/experiments/balance493-2026-10-28/candidate-v4-{EN,IT}.nds
  SGP_TEXT_CHARMAP                    default $SGP_PRET_SOURCE/charmap.txt, else local/tools/pokeheartgold/charmap.txt
A missing input skips with a reason; SGP_TEXT_REQUIRE_INPUTS=1 turns that into a failure.
No ROM, extracted text or font is written anywhere by this suite.
"""
import hashlib
import importlib.util
import json
import os
import struct
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2]
ROOT = SOURCE.parent
sys.path.insert(0, str(SOURCE))
from ndspy.narc import NARC  # noqa: E402
from ndspy.rom import NintendoDSRom  # noqa: E402
from translation.message_codec import Bank  # noqa: E402

spec = importlib.util.spec_from_file_location('modern_accuracy_text', HERE.parent / 'text.py')
text = importlib.util.module_from_spec(spec)
sys.modules['modern_accuracy_text'] = text
spec.loader.exec_module(text)

PINS = {'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
        'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136)}
BANK_SHA = {'EN': 'c6c40b2832958298285582a17c59f21eeef83b58d01dd5ae9822e3bebf5d9ba0',
            'IT': '87a052877cbcc90ee2dbee81de9cf1ab2551c61777b2df97f491b4b43dc6af5c'}
FONT_SHA = '9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73'
WIDTHS_SHA = '9056ed8029423336c0c7d7cf88c8e04841f09849bf431ce6d1c6ebebd4358e84'
DEFAULT_ROM = ROOT / 'local/experiments/balance493-2026-10-28/candidate-v4-{}.nds'


def digest(path):
    state = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            state.update(block)
    return state.hexdigest()


def charmap_path():
    configured = os.environ.get('SGP_TEXT_CHARMAP')
    if configured:
        return Path(configured)
    pret = os.environ.get('SGP_PRET_SOURCE')
    return Path(pret) / 'charmap.txt' if pret else ROOT / 'local/tools/pokeheartgold/charmap.txt'


def narc_of(data):
    rom = NintendoDSRom(data)
    file_id = rom.filenames.idOf(text.ARCHIVE)
    return rom, file_id, NARC(rom.files[file_id])


class KeenEyeTextRomTests(unittest.TestCase):
    def inputs(self, language):
        rom = Path(os.environ.get('SGP_TEXT_ROM_' + language) or str(DEFAULT_ROM).format(language))
        charmap = charmap_path()
        if not rom.is_file() or not charmap.is_file():
            message = 'missing V4 %s ROM (%s) or pinned charmap (%s)' % (language, rom, charmap)
            if os.environ.get('SGP_TEXT_REQUIRE_INPUTS') == '1':
                self.fail(message)
            self.skipTest(message)
        before_hash = digest(rom)
        self.assertEqual((before_hash, rom.stat().st_size), PINS[language])
        self.assertEqual(digest(charmap), text.CHARMAP_SHA256)
        return rom, charmap, before_hash

    def run_language(self, language):
        rom_path, charmap, before_hash = self.inputs(language)
        data = rom_path.read_bytes()
        _, file_id, narc = narc_of(data)
        old_bank = bytes(narc.files[text.BANK])
        self.assertEqual(hashlib.sha256(old_bank).hexdigest(), BANK_SHA[language])
        old_words = Bank(old_bank).words
        self.assertEqual(len(old_words), 124)
        # The retail row is exactly the pinned one (hash only; no retail text is stored in git).
        self.assertEqual(text.row_sha256(old_words[text.ROW]), text.PREIMAGE_SHA256[language])

        after, receipt = text.apply(data, language, charmap)
        self.assertTrue(after != data, 'apply returned the image unchanged')
        self.assertEqual(digest(rom_path), before_hash)            # the input file is untouched

        # Row 51 is the expected text, decoded by the independent reader and the inverse charmap.
        _, after_id, after_narc = narc_of(after)
        self.assertEqual(after_id, file_id)
        new_bank = bytes(after_narc.files[text.BANK])
        table, inverse = text.load_charmap(charmap)
        new_words = text.decode_row(new_bank, text.ROW)
        self.assertEqual(new_words, Bank(new_bank).words[text.ROW])
        self.assertEqual(''.join(inverse[w] for w in new_words[:-1]), text.DESCRIPTIONS[language])
        self.assertNotEqual(new_words, old_words[text.ROW])

        # Every other row and every other NARC member is byte-identical.
        for index in range(124):
            if index != text.ROW:
                self.assertEqual(text.decode_row(new_bank, index), old_words[index], index)
                a, b = text.row_span(old_bank, index), text.row_span(new_bank, index)
                self.assertTrue(old_bank[a[0]:a[1]] == new_bank[b[0]:b[1]], 'encrypted row %d changed' % index)
        self.assertEqual(len(after_narc.files), len(narc.files))
        for index, member in enumerate(narc.files):
            if index != text.BANK:
                self.assertTrue(bytes(after_narc.files[index]) == bytes(member), 'NARC member %d changed' % index)
        self.assertEqual(Bank(old_bank).key, Bank(new_bank).key)

        # Window facts re-read from the shipped bytes, and the measures that depend on them.
        self.assertEqual(receipt['windows']['summary_skills']['template'], [1, 0, 19, 19, 4, 13, 0x25D])
        self.assertEqual(receipt['windows']['battle_summary_skills']['templates'],
                         [[5, 1, 11, 18, 4, 13, 0x15F], [5, 1, 11, 18, 4, 13, 0x277]])
        self.assertEqual(receipt['font']['sha256'], FONT_SHA)
        self.assertEqual(receipt['font']['widths_sha256'], WIDTHS_SHA)
        self.assertEqual(receipt['line_count'], 2)
        self.assertLessEqual(max(receipt['lines_px']), 144)
        self.assertLessEqual(max(receipt['lines_px']), receipt['retail_ceiling_px'])
        self.assertEqual(receipt['retail_ceiling_px'], 136)
        for window in receipt['windows'].values():
            self.assertTrue(window['fits'])
            self.assertEqual(window['lines'], 2)
            self.assertLessEqual(max(receipt['lines_px']), window['usable_px'])
        self.assertLessEqual(len(new_words), 127)

        # The independent verifier agrees, and refuses tampering.
        verified = text.verify(data, after, receipt, charmap_path=charmap)
        self.assertEqual(verified['language'], language)
        self.assertEqual(verified['rows_identical'], 123)
        self.assertEqual(verified['members_identical'], len(narc.files) - 1)
        self.assertEqual(verified['bytes_changed_outside_expected'], 0)
        tampered = bytearray(after)
        tampered[0x300000] ^= 1
        with self.assertRaises((ValueError, AssertionError)):
            text.verify(data, bytes(tampered), receipt, charmap_path=charmap)
        wrong = dict(receipt, new_sha256='0' * 64)
        with self.assertRaises((ValueError, AssertionError)):
            text.verify(data, after, wrong, charmap_path=charmap)
        with self.assertRaises((ValueError, AssertionError)):
            text.verify(after, after, receipt, charmap_path=charmap)

        # Refusals on the real image: already patched, foreign language, wrong preimage.
        with self.assertRaises(ValueError):
            text.apply(after, language, charmap)
        other = 'IT' if language == 'EN' else 'EN'
        with self.assertRaises(ValueError):
            text.apply(data, other, charmap)                       # this row is not the other language's retail row
        self.assertEqual(digest(rom_path), before_hash)
        print(json.dumps(dict(language=language, receipt=receipt, input_unchanged=True), sort_keys=True))

    def test_english(self):
        self.run_language('EN')

    def test_italian(self):
        self.run_language('IT')

    def test_font_line_pitch_and_spacing_read_from_arm9(self):
        """sFontInfos[0] at ARM9 0x020F56D8: max width 11, height 16, letter and
        line spacing 0 -- the pitch and spacing the width/line checks assume."""
        from sgp12.rom import Arm9
        for language in ('EN', 'IT'):
            rom_path, _, _ = self.inputs(language)
            info = Arm9(rom_path).leggi(0x020F56D8, 8)
            self.assertEqual(info.hex(), '0b10000000010f02', language)
            self.assertEqual((info[1], info[2], info[3]), (16, 0, 0))


if __name__ == '__main__':
    unittest.main()
