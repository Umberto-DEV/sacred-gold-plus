import struct
import unittest

from sgp13 import content


class ContentTests(unittest.TestCase):
    def test_wrap_respects_pixel_width_and_page_limit_without_losing_words(self):
        paragraphs = ['- One two three four five six seven eight nine ten.'] * 5
        pages = content.paginate(paragraphs, lambda text: len(text) * 8, reference=1455)
        lines = [line for page in pages for line in page['lines']]
        self.assertEqual(' '.join(lines), ' '.join(paragraphs))
        self.assertTrue(all(1 <= len(page['lines']) <= 7 for page in pages))
        self.assertTrue(all(len(line) * 8 <= 208 for line in lines))
        self.assertTrue(all(page['reference'] == 1455 for page in pages))

    def test_paragraph_that_fits_screen_is_not_split_to_fill_previous_page(self):
        pages = content.paginate([' '.join(['a'] * 12), ' '.join(['b'] * 6)],
                                 lambda text: len(text) * 52)
        self.assertEqual([p['lines'] for p in pages], [['a a'] * 6, ['b b'] * 3])

    def test_exact_seven_lines_and_next_paragraph_are_separate(self):
        pages = content.paginate([' '.join(['a'] * 14), 'b b'],
                                 lambda text: len(text) * 52)
        self.assertEqual([p['lines'] for p in pages], [['a a'] * 7, ['b b']])

    def test_long_paragraph_continues_without_token_loss(self):
        paragraphs = [' '.join(['a'] * 20), ' '.join(['b'] * 6)]
        pages = content.paginate(paragraphs, lambda text: len(text) * 52)
        self.assertEqual([p['lines'] for p in pages],
                         [['a a'] * 7, ['a a'] * 3 + ['b b'] * 3])
        self.assertEqual([word for p in pages for line in p['lines'] for word in line.split()],
                         ['a'] * 20 + ['b'] * 6)
        self.assertTrue(all(line for p in pages for line in p['lines']))

    def test_reference_preserved_on_all_semantic_pages(self):
        pages = content.paginate([' '.join(['a'] * 12), ' '.join(['b'] * 6),
                                  ' '.join(['c'] * 20)],
                                 lambda text: len(text) * 52, reference=1467)
        self.assertEqual([len(p['lines']) for p in pages], [6, 3, 7, 3])
        self.assertEqual([p['reference'] for p in pages], [1467] * 4)

    def test_empty_paragraphs_never_emit_blank_pages_or_lines(self):
        self.assertEqual(content.paginate([' ', 'a', '', ' b  '], len),
                         [dict(lines=['a', 'b'], reference=0)])
        with self.assertRaisesRegex(ValueError, 'empty'):
            content.paginate(['', '  '], len)

    def test_unbreakable_long_word_rejected(self):
        with self.assertRaisesRegex(ValueError, 'word'):
            content.paginate(['X' * 80], lambda text: len(text) * 8)

    def test_evolution_uses_actual_record_and_localized_item_name(self):
        records = [bytes(44)] * 494
        records[64] = struct.pack('<HHH', 7, 467, 65) + bytes(38)
        names = lambda kind, index: {'pokemon': {64: 'Kadabra', 65: 'Alakazam'},
                                    'item': {467: 'Sfera Patto'}}[kind][index]
        entries = content.evolution_entries(records, names, 'IT', lambda s: len(s) * 5, {1467})
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['id'], 64)
        self.assertEqual(entries[0]['pages'][0]['reference'], 1467)
        text = ' '.join(line for p in entries[0]['pages'] for line in p['lines'])
        self.assertIn('Sfera Patto', text)
        self.assertIn('Alakazam', text)

    def test_unknown_or_truncated_evolution_records_fail_instead_of_guessing(self):
        records = [bytes(44)] * 494
        for record in (b'bad', struct.pack('<HHH', 99, 0, 65) + bytes(38)):
            records[64] = record
            with self.assertRaises(ValueError):
                content.evolution_entries(records, lambda k, n: str(n), 'EN', len, set())

    def test_zero_beauty_requirement_is_plain_level_up(self):
        text = content.evolution_description(15, 0, lambda k, n: str(n), 'EN')
        self.assertEqual(text, 'Level up.')


if __name__ == '__main__':
    unittest.main()
