#!/usr/bin/env python3
"""Unit tests for hgss_text.py. Uses source/translation/message_codec.py
only to build synthetic banks (cipher round-trip already tested there); no ROM
or charmap.txt is opened. No narrative game text is used, only single letters."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'translation'))
import hgss_text as ht  # noqa: E402
import message_codec as mc  # noqa: E402

CHARS = {1: 'a', 2: 'b', 3: 'c'}
COMMANDS = {0x0201: 'PAUSE'}


class ReadBankRawTest(unittest.TestCase):
    def test_round_trips_through_the_real_cipher(self):
        messages = [[1, 2, 3, ht.TERMINATOR], [ht.TERMINATOR]]
        bank = mc.Bank.from_words(messages, key=1234)
        raw = bank.save()
        decoded = ht.read_bank_raw(raw)
        self.assertEqual(decoded, messages)


class RenderTest(unittest.TestCase):
    def test_plain_text_and_terminator(self):
        result = ht.render([1, 2, 3, ht.TERMINATOR], CHARS, COMMANDS)
        self.assertEqual(result['text'], 'abc')
        self.assertEqual(result['unknown_codes'], [])
        self.assertEqual(result['malformed_controls'], [])

    def test_unknown_code_is_flagged_not_hidden(self):
        result = ht.render([1, 99, ht.TERMINATOR], CHARS, COMMANDS)
        self.assertEqual(result['unknown_codes'], [99])
        self.assertIn('<0063>', result['text'])

    def test_named_control_renders_and_is_tracked(self):
        words = [ht.CONTROL_MARKER, 0x0201, 1, 5, 1, ht.TERMINATOR]
        result = ht.render(words, CHARS, COMMANDS)
        self.assertEqual(result['text'], '{PAUSE:5}a')
        self.assertEqual(result['controls'], [[0x0201, [5]]])

    def test_truncated_control_is_reported_malformed(self):
        words = [ht.CONTROL_MARKER, 0x0201, 3, 1, ht.TERMINATOR]
        result = ht.render(words, CHARS, COMMANDS)
        self.assertTrue(result['malformed_controls'])

    def test_missing_terminator_is_reported(self):
        result = ht.render([1, 2], CHARS, COMMANDS)
        self.assertTrue(any(m['reason'] == 'missing terminator' for m in result['malformed_controls']))


if __name__ == '__main__':
    unittest.main()
