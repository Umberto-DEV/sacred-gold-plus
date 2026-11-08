"""Field dialogue wrapping preserves the native two-row printer contract."""
from pathlib import Path
import struct
import tempfile
import unittest

try:
    from . import geometry
except ImportError:
    geometry = None


class FieldGeometryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(geometry, 'bounded field dialogue layout is missing')
        self.context = geometry.Context(frozenset({123, 385, 3}), len,
                                        {1: 5, 3: 5, 6: 5, 8: 5, 31: 5, 0: 5},
                                        numeric_width=3, stat_width=4, limit=12)

    def test_wrap_uses_newline_then_scroll_and_keeps_every_word(self):
        before = 'one two three four five six seven'
        after = geometry.layout(123, before, self.context)
        self.assertEqual(after, r'one two\nthree four\ffive six\fseven')
        self.assertEqual(geometry.check(123, before, after, self.context)['max_width_px'], 10)

    def test_existing_clear_pages_stay_between_the_same_words(self):
        before = r'one two three four\rred blue green white'
        self.assertEqual(geometry.layout(123, before, self.context),
                         r'one two\nthree four\rred blue\ngreen white')

    def test_third_explicit_newline_becomes_scroll_without_losing_blank_rows(self):
        before = r'one\ntwo\nthree\r\none'
        after = geometry.layout(123, before, self.context)
        self.assertEqual(after, r'one\ntwo\fthree\r\none')
        geometry.check(123, before, after, self.context)

    def test_colour_and_question_commands_keep_exact_order_and_arguments(self):
        before = 'one {COLOR:2}two three{COLOR:0} four{YESNO:0}'
        after = geometry.layout(123, before, self.context)
        self.assertEqual(after, r'one {COLOR:2}two\nthree{COLOR:0} four{YESNO:0}')
        geometry.check(123, before, after, self.context)
        for bad in (after.replace('{COLOR:2}', '{COLOR:3}'), after.replace('three', 'other'),
                    after.replace(r'\n', r'\r')):
            with self.assertRaisesRegex(ValueError, 'content|clear|command'):
                geometry.check(123, before, bad, self.context)

    def test_variable_width_is_reserved_before_the_native_expansion(self):
        before = 'hello {STRVAR_1:3:0,0}! end'
        after = geometry.layout(123, before, self.context)
        self.assertEqual(after, r'hello {STRVAR_1:3:0,0}!\nend')
        geometry.check(123, before, after, self.context)
        with self.assertRaisesRegex(ValueError, 'width'):
            geometry.check(123, before, before, self.context)

    def test_training_integer_fraction_and_stat_name_have_proven_separate_bounds(self):
        before = '{STRVAR_1:1}: {STRVAR_1:2}/{STRVAR_1:3} EV'
        after = geometry.layout(385, before, self.context, message=83)
        self.assertEqual(after, r'{STRVAR_1:1}:\n{STRVAR_1:2}/{STRVAR_1:3} EV')
        geometry.check(385, before, after, self.context, message=83)

    def test_training_copies_use_their_actual_bank_base_not_the_catalogue_alias(self):
        context = geometry.Context(frozenset({385, 557, 630}), len,
                                   {0: 20, 1: 20}, 3, 4, limit=12)
        text = '{STRVAR_1:1}: {STRVAR_1:2}/{STRVAR_1:3} EV'
        for bank, base in ((385, 20), (557, 11), (630, 2)):
            with self.subTest(bank=bank):
                result = geometry.layout(bank, text, context, message=base+63)
                self.assertEqual(result, r'{STRVAR_1:1}:\n{STRVAR_1:2}/{STRVAR_1:3} EV')
                self.assertEqual(geometry.layout(bank, 'a very long menu choice', context,
                                                message=base+1), 'a very long menu choice')

    def test_nonfield_banks_and_mixed_native_formats_are_unchanged(self):
        examples = [(750, 'long move name which exceeds the field window', None),
                    (123, 'Item{CURSOR_X:90}500 coins', None),
                    (123, '{SIZE:200}large text{SIZE:100}', None),
                    (3, 'long battle text with a Pokemon', 18),
                    (385, 'a long scrolling-menu choice', 21)]
        for bank, text, message in examples:
            with self.subTest(bank=bank, text=text):
                self.assertEqual(geometry.layout(bank, text, self.context, message=message), text)
                self.assertEqual(geometry.check(bank, text, text, self.context, message=message)['status'],
                                 'outside-scope')

    def test_known_shared_field_tablet_is_layout_owned(self):
        self.assertEqual(geometry.layout(3, 'one two three four', self.context, message=1),
                         r'one two\nthree four')

    def test_unknown_variable_semantics_are_outside_scope_instead_of_guessing(self):
        text = 'one two {STRVAR_1:99:0,0} three four'
        self.assertEqual(geometry.layout(123, text, self.context), text)
        self.assertEqual(geometry.check(123, text, text, self.context)['status'], 'outside-scope')

    def test_repeated_layout_keeps_existing_scroll_waits_and_is_stable(self):
        before = r'one two three four\ffive six seven\rred blue green white'
        after = geometry.layout(123, before, self.context)
        self.assertIn(r'three four\f', after)
        self.assertEqual(geometry.layout(123, after, self.context), after)

    def test_word_overflow_cannot_be_hidden_by_splitting_a_variable_or_a_name(self):
        with self.assertRaisesRegex(ValueError, 'word'):
            geometry.layout(123, 'unbreakablelongword', self.context)

    def test_readback_rejects_three_unscrolled_rows_and_horizontal_overflow(self):
        with self.assertRaisesRegex(ValueError, 'row'):
            geometry.check(123, r'one\ntwo\nthree', r'one\ntwo\nthree', self.context)
        with self.assertRaisesRegex(ValueError, 'width'):
            geometry.check(123, 'one two three four', 'one two three four', self.context)

    def test_map_headers_use_only_the_u16_message_field_in_all_540_records(self):
        headers = bytearray(540 * 24)
        for index in range(540):
            struct.pack_into('<HH', headers, index * 24 + 8, 999, 123)
        struct.pack_into('<H', headers, 539 * 24 + 10, 385)
        self.assertEqual(geometry.field_banks(bytes(headers)), frozenset({123, 385}))
        with self.assertRaisesRegex(ValueError, 'header'):
            geometry.field_banks(bytes(headers[:-1]))

    def test_context_refuses_an_unpinned_external_charmap_before_reading_a_rom(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'charmap.txt'
            path.write_text('not the production codec')
            with self.assertRaisesRegex(ValueError, 'charmap'):
                geometry.context_from_rom(b'not a ROM', path)


if __name__ == '__main__':
    unittest.main()
