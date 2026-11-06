"""Synthetic format regressions; contains no extracted game strings."""
import struct
import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_localization
import message_codec
from message_codec import Bank, encode_text, pack_name, unpack_name


CHARS = {ord(c): c for c in 'Ciao èàéìòù!12, '}
CHARS.update({0xE000: r'\n', 0x25BC: r'\r', 0x25BD: r'\f'})
COMMANDS = {0x0100: 'STRVAR_1', 0x0205: 'ALN_CENTER', 0xFF00: 'COLOR'}


def overlapping_bank():
    raw = bytearray(22)
    struct.pack_into('<HH', raw, 0, 2, 0)
    struct.pack_into('<II', raw, 4, 20, 1)
    struct.pack_into('<II', raw, 12, 20, 1)
    struct.pack_into('<H', raw, 20, 0)
    return bytes(raw)


class CodecTests(unittest.TestCase):
    def test_accented_text_and_variable(self):
        words = encode_text(r'Ciao!\n{STRVAR_1:3:0,0} è {COLOR:2}1{COLOR:0}', CHARS, COMMANDS)
        self.assertEqual(words[:6], [67, 105, 97, 111, 33, 0xE000])
        self.assertIn([0xFFFE, 0x103, 2, 0, 0], [words[i:i+5] for i in range(len(words))])
        self.assertEqual(words[-1], 0xFFFF)

    def test_bank_cipher_and_untouched_bytes(self):
        messages = [[67, 105, 97, 111, 0xFFFF], [0xFFFE, 0x205, 0, 49, 0xFFFF]]
        raw = Bank.from_words(messages, key=0xBEEF).save()
        loaded = Bank(raw)
        self.assertEqual(loaded.words, messages)
        self.assertEqual(loaded.save(), raw)
        self.assertNotIn(struct.pack('<5H', *messages[0]), raw)

    def test_base_strvar_and_typed_strvar_are_distinct(self):
        self.assertEqual(encode_text('{STRVAR_1:1,0}', CHARS, COMMANDS), [0xFFFE, 0x100, 2, 1, 0, 0xFFFF])
        self.assertEqual(encode_text('{STRVAR_1:1:0,0}', CHARS, COMMANDS), [0xFFFE, 0x101, 2, 0, 0, 0xFFFF])

    def test_replacement_keeps_other_messages_and_count(self):
        original = [[67, 0xFFFF], [105, 0xFFFF], [97, 0xFFFF]]
        bank = Bank(Bank.from_words(original, key=37).save())
        bank.replace(1, [49, 50, 0xFFFF])
        got = Bank(bank.save())
        self.assertEqual(got.words, [original[0], [49, 50, 0xFFFF], original[2]])
        self.assertEqual(got.key, 37)

    def test_name_packing_handles_all_bit_boundaries(self):
        for length in range(1, 31):
            words = [67, 105, 97, 111] * length + [0xFFFF]
            self.assertEqual(unpack_name(pack_name(words)), words)
        self.assertRaises(ValueError, pack_name, [0xE000, 0xFFFF])

    def test_invalid_input_is_rejected(self):
        self.assertRaises(ValueError, encode_text, '{COLOR:65536}', CHARS, COMMANDS)
        self.assertRaises(ValueError, encode_text, '{MISSING}', CHARS, COMMANDS)
        self.assertRaises(ValueError, encode_text, '☃', CHARS, COMMANDS)
        self.assertRaises(ValueError, Bank, b'\x01\x00\x00\x00')
        self.assertRaises(ValueError, Bank.from_words, [[67]], 0)

    def test_existing_malformed_controls_can_be_preserved_losslessly(self):
        # A maintenance tool must not silently rewrite unrelated malformed data.
        words = [[0xFFFE, 0x205, 0x122, 0xFFFF]]
        raw = Bank.from_words(words, 42).save()
        self.assertEqual(Bank(raw).words, words)
        self.assertEqual(Bank(raw).save(), raw)

    def test_overlapping_extents_are_rejected_before_message_decode(self):
        decoder = mock.Mock(return_value=[0xFFFF])
        with mock.patch.object(message_codec, '_words', decoder):
            with self.assertRaisesRegex(ValueError, 'overlap'):
                Bank(overlapping_bank())
        decoder.assert_not_called()

    def test_localization_audit_rejects_overlapping_extents(self):
        with mock.patch.object(audit_localization, 'render', return_value={}):
            with self.assertRaisesRegex(ValueError, 'overlap'):
                audit_localization.read_bank(overlapping_bank())

    def test_message_count_budget_precedes_allocation_table_walk(self):
        raw = struct.pack('<HH', message_codec.MAX_MESSAGES + 1, 0)
        with self.assertRaisesRegex(ValueError, 'count'):
            Bank(raw)


if __name__ == '__main__':
    unittest.main()
