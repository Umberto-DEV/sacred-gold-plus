"""Message composition contracts, using newly authored synthetic text only."""
import unittest
from ndspy.narc import NARC
from translation.message_codec import Bank, encode_text, unpack_name
from . import messages

CHARS = {ord(c): c for c in ' HELONWUaelo123!'}
COMMANDS = {0x100: 'NAME'}


def archive(texts):
    value = NARC()
    value.files = [Bank.from_words([encode_text(s, CHARS, COMMANDS) for s in texts], 42).save()]
    return value.save()


class MessageCompositionTests(unittest.TestCase):
    def test_shared_imperial_height_formatter_is_not_replaced_by_empty_retail(self):
        def image(formatter):
            value = NARC()
            value.files = [Bank.from_words([], 42).save() for _ in range(803)]
            rows = [[65535] for _ in range(176)]
            rows[175] = encode_text(formatter, CHARS, COMMANDS)
            value.files[802] = Bank.from_words(rows, 42).save()
            return value.save()
        core = image('{NAME:1}')
        output, report = messages.translate_messages(core, core, image(''), {}, CHARS, COMMANDS)
        self.assertEqual(Bank(NARC(output).files[802]).words[175],
                         encode_text('{NAME:1}', CHARS, COMMANDS))
        self.assertEqual(report['counts']['protected'], 1)

    def compose(self, strings):
        return messages.translate_messages(archive(['HELLO', 'NEW']), archive(['Hello', 'Hello']),
                                           archive(['Hallo', 'Hallo']), strings, CHARS, COMMANDS)

    def test_official_donor_is_used_for_style_only_edits(self):
        output, report = self.compose({'m:0:1': 'NEU'})
        words = Bank(NARC(output).files[0]).words
        self.assertEqual(words, [encode_text('Hallo', CHARS, COMMANDS), encode_text('NEU', CHARS, COMMANDS)])
        self.assertEqual(report['counts'], {'retail': 0, 'retail-style': 1, 'authored': 1})

    def test_missing_custom_translation_cannot_fall_back_to_english(self):
        with self.assertRaisesRegex(ValueError, 'm:0:1'):
            self.compose({})

    def test_changed_variable_arguments_are_rejected(self):
        core = archive(['NEW {NAME:1}'])
        original = archive(['Hello {NAME:1}'])
        donor = archive(['Hallo {NAME:1}'])
        with self.assertRaisesRegex(ValueError, 'control'):
            messages.translate_messages(core, original, donor, {'m:0:0': 'NEU {NAME:2}'}, CHARS, COMMANDS)


if __name__ == '__main__':
    unittest.main()
