"""ROM-free contracts for the explicit successor Guide compiler."""
import copy
import struct
import unittest

from sgp131 import guide_content as content
from sgp13 import guide


def encode(text):
    return [ord(c) for c in text] + [65535]


def fixture():
    return [dict(id=i, title=str(i), entries=[dict(id=i * 100, title='Group',
            pages=[dict(lines=['shared words'], reference=0)])]) for i in (1, 2, 3, 4)]


class SuccessorTests(unittest.TestCase):
    def test_packer_rejects_non_glyph_native_words_before_readback(self):
        # Direct compiler-boundary assertion prevents the independent reader's
        # rejection from masking a missing packer check.
        for code in (0, 510, 0xE000, 0x25BD, 0xFFFE):
            with self.subTest(code=code):
                invalid_encoder = lambda text: [code, 65535]
                with self.assertRaises(ValueError):
                    content._words('authored', invalid_encoder, len)
                with self.assertRaises(ValueError):
                    content.build_content(fixture()[:1], invalid_encoder, len)

    def test_reader_rejects_non_glyph_words_in_independently_assembled_bytes(self):
        # Recomputed plain bytes bypass the packer, its encoder, and its checks.
        for code in (0, 510, 0xE000, 0x25BD, 0xFFFE):
            blob = (struct.pack('<4sIHH', b'SGG1', 56, 1, 1)
                    + struct.pack('<HHII', 1, 1, 0, 40)
                    + struct.pack('<HHHHII', 1, 1, 1, 0, 40, 52)
                    + struct.pack('<HH', code, 65535)
                    + struct.pack('<HHI', 1, 0, 40)
                    + struct.pack('<I', 44))
            with self.subTest(code=code), self.assertRaises(ValueError):
                content.read_content(blob)

    def test_single_line_glyph_boundaries_remain_valid_in_both_paths(self):
        for code in (1, 509):
            with self.subTest(code=code):
                encoder = lambda text: [code, 65535]
                self.assertEqual(content._words('authored', encoder, len), (code, 65535))
                packed = content.build_content(fixture()[:1], encoder, len)
                self.assertEqual(content.read_content(packed),
                                 content.encoded_graph(fixture()[:1], encoder))
                plain = (struct.pack('<4sIHH', b'SGG1', 56, 1, 1)
                         + struct.pack('<HHII', 1, 1, 0, 40)
                         + struct.pack('<HHHHII', 1, 1, 1, 0, 40, 52)
                         + struct.pack('<HH', code, 65535)
                         + struct.pack('<HHI', 1, 0, 40)
                         + struct.pack('<I', 44))
                actual = content.read_content(plain)
                self.assertEqual(actual[0]['title'], (code, 65535))
                self.assertEqual(actual[0]['entries'][0]['pages'][0]['lines'], [(code, 65535)])

    def test_alphabetical_access_ignores_numeric_ids_accents_and_case(self):
        rows = [(1, 'Zulu'), (90, 'Éclair'), (2, 'alpha'), (50, 'E\u0301CLAIR')]
        self.assertEqual([i for i, name in sorted(rows, key=lambda r: content.sort_key(r[1], r[0]))],
                         [2, 50, 90, 1])

    def test_explicit_alias_keeps_canonical_group_and_reorders_categories(self):
        cats = fixture()
        cats[0]['entries'][0]['id'] = 1
        arranged = content.arrange_categories(cats, lambda i: {1: 'Zed', 2: 'Alpha'}[i], {2: 300})
        self.assertEqual([c['id'] for c in arranged], [4, 1, 3, 2])
        special = next(c for c in arranged if c['id'] == 3)['entries']
        self.assertEqual([(e['id'], e['title']) for e in special], [(5002, 'Alpha'), (300, 'Group')])
        self.assertEqual(special[0]['pages'], special[1]['pages'])

    def test_identical_entries_share_immutable_page_tables(self):
        cats = fixture()[:1]
        cats[0]['entries'].append(copy.deepcopy(cats[0]['entries'][0]))
        cats[0]['entries'][1]['id'] = 101
        blob = content.build_content(cats, encode, len)
        self.assertEqual(struct.unpack_from('<I', blob, 24 + 12)[0],
                         struct.unpack_from('<I', blob, 40 + 12)[0])

    def test_punctuation_sex_suffix_and_stable_ties_remain_distinct(self):
        names = ['Porygon-Z', 'Nidoran♂', 'Mr. Mime', 'Farfetch’d', 'Ho-oh',
                 'Nidoran♀', 'Farfetch\'d', 'Porygon', 'MR MIME']
        ordered = sorted(names, key=lambda s: content.sort_key(s, 1))
        self.assertEqual(ordered, ["Farfetch'd", 'Farfetch’d', 'Ho-oh', 'MR MIME',
                                  'Mr. Mime', 'Nidoran♀', 'Nidoran♂', 'Porygon', 'Porygon-Z'])
        self.assertLess(content.sort_key('same', 1), content.sort_key('same', 2))

    def test_aliases_reject_missing_destinations_collisions_and_input_mutation(self):
        cats = fixture()
        cats[0]['entries'][0]['id'] = 1
        before = copy.deepcopy(cats)
        for mapping in ({2: 999}, {2: 300, 5002: 300}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                content.arrange_categories(cats, lambda i: str(i), mapping)
        cats[1]['entries'][0]['id'] = 5002
        with self.assertRaisesRegex(ValueError, 'collision'):
            content.arrange_categories(cats, lambda i: str(i), {2: 300})
        cats = before
        content.arrange_categories(cats, lambda i: str(i), {2: 300})
        self.assertEqual(cats, before)

    def test_all_approved_subjects_use_explicit_ids_and_unique_destinations(self):
        expected = {2480: [480, 481, 482], 2483: [483, 484, 487],
                    2377: [377, 378, 379], 2243: [243, 244, 245], 2250: [250, 249],
                    2383: [383, 382, 384], 2380: [380, 381], 3001: [1, 4, 7],
                    3002: [252, 255, 258], 3003: [387, 390, 393],
                    3004: [152, 155, 158], 3005: [149, 248, 373, 376, 445],
                    1453: [488], 1458: [485]}
        self.assertEqual(content.ALIASES, {s: target for target, species in expected.items() for s in species})
        cats = fixture()
        cats[0]['entries'][0]['id'] = 50
        cats[1]['entries'] = [dict(id=i, title='Item', pages=[dict(lines=['item'], reference=0)])
                              for i in (1453, 1458)]
        cats[2]['entries'] = [dict(id=i, title='Original group', pages=[dict(lines=[str(i)], reference=0)])
                              for i in expected if i not in (1453, 1458)]
        out = content.arrange_categories(cats, lambda i: 'Species ' + str(i))
        rows = next(c['entries'] for c in out if c['id'] == 3)
        self.assertEqual(len(rows), 50)
        byid = {e['id']: e for c in out for e in c['entries']}
        for target, species in expected.items():
            for s in species:
                self.assertEqual(byid[5000 + s]['pages'], byid[target]['pages'])
                self.assertEqual(byid[5000 + s]['title'], 'Species ' + str(s))

    def test_sharing_keys_include_reference_order_and_encoded_glyphs(self):
        cats = fixture()[:1]
        cats[0]['entries'] = [dict(id=i, title=str(i), pages=[dict(lines=lines, reference=ref)])
                              for i, lines, ref in [(1, ['a', 'b'], 1), (2, ['a', 'b'], 2),
                                                    (3, ['b', 'a'], 1), (4, ['a', 'b'], 1)]]
        blob = content.build_content(cats, encode, len)
        tables = [struct.unpack_from('<I', blob, 24 + 16 * i + 12)[0] for i in range(4)]
        self.assertEqual(tables[0], tables[3])
        self.assertEqual(len(set(tables)), 3)
        self.assertEqual(content.read_content(blob), content.encoded_graph(cats, encode))
        shifted = content.build_content(cats, lambda s: [w + 1 for w in encode(s)[:-1]] + [65535], len)
        self.assertNotEqual(blob, shifted)

    def test_page_order_and_first_last_lines_survive_sharing(self):
        cats = fixture()[:1]
        cats[0]['entries'][0]['pages'] = [dict(lines=[str(i)] * 7, reference=100) for i in range(255)]
        blob = content.build_content(cats, encode, len)
        out = content.read_content(blob)[0]['entries'][0]['pages']
        self.assertEqual(len(out), 255)
        self.assertEqual(out[0]['lines'][0], tuple(encode('0')))
        self.assertEqual(out[-1]['lines'][-1], tuple(encode('254')))

    def test_width_eos_page_and_content_budget_fail_closed(self):
        cats = fixture()[:1]
        for field, value in [('title', 'x' * 209), ('title', '')]:
            bad = copy.deepcopy(cats); bad[0][field] = value
            with self.assertRaises(ValueError): content.build_content(bad, encode, len)
        for words in ([1], [65535, 1, 65535], [1] * 128 + [65535], [-1, 65535]):
            with self.subTest(words=words[:3]), self.assertRaises(ValueError):
                content.build_content(cats, lambda s: words, len)
        for pages in ([], [dict(lines=[], reference=0)], [dict(lines=['a'] * 8, reference=0)],
                      [dict(lines=['a'], reference=0)] * 256):
            bad = copy.deepcopy(cats); bad[0]['entries'][0]['pages'] = pages
            with self.assertRaises(ValueError): content.build_content(bad, encode, len)
        big = fixture()[:1]
        big[0]['entries'] = [dict(id=i, title=str(i), pages=[dict(lines=[f'{i:04d}' + 'x' * 96], reference=0)])
                             for i in range(1, 1000)]
        with self.assertRaisesRegex(ValueError, '128 KiB'):
            content.build_content(big, encode, len)

    def test_independent_readback_rejects_malicious_offsets_lengths_and_links(self):
        blob = content.build_content(fixture()[:1], encode, len)
        table = struct.unpack_from('<I', blob, 36)[0]
        page = struct.unpack_from('<I', blob, table)[0]
        line = struct.unpack_from('<I', blob, page + 4)[0]
        mutations = [(36, '<I', 0), (table, '<I', table), (page, '<H', 8),
                     (page + 2, '<H', 999), (line, '<H', 65535), (28, '<H', 0),
                     (24, '<H', 400), (30, '<H', 1)]
        intended = content.encoded_graph(fixture()[:1], encode)
        for offset, fmt, value in mutations:
            bad = bytearray(blob); struct.pack_into(fmt, bad, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError):
                content.verify_content(bad, intended)
        for bad in (blob[:-1], blob + b'garbage', blob + b'\0\0\0\0'):
            bad = bytearray(bad); struct.pack_into('<I', bad, 4, len(bad))
            with self.assertRaises(ValueError): content.read_content(bad)
        bad = bytearray(blob); bad[line:line + 2 * 13] = b'\x01\x00' * 13
        with self.assertRaises(ValueError): content.verify_content(bad, intended)

    def test_wrapping_preserves_paragraph_words_all_references_and_empty_policy(self):
        paragraphs = ['', ' '.join(['alpha'] * 60), ' beta gamma ', '']
        pages = content.paginate(paragraphs, lambda s: len(s) * 8, 100)
        self.assertEqual([w for p in pages for line in p['lines'] for w in line.split()],
                         ['alpha'] * 60 + ['beta', 'gamma'])
        self.assertTrue(all(p['reference'] == 100 and 1 <= len(p['lines']) <= 7 for p in pages))
        self.assertTrue(all(0 < len(s) * 8 <= 208 for p in pages for s in p['lines']))
        with self.assertRaises(ValueError): content.paginate(['', ' '], len)
        with self.assertRaises(ValueError): content.paginate(['a' * 209], len)

    def test_legacy_builder_stays_unshared_and_independent(self):
        cats = fixture()[:1]
        cats[0]['entries'].append(dict(id=101, title='Group', pages=copy.deepcopy(cats[0]['entries'][0]['pages'])))
        new = content.build_content(cats, encode, len)
        old = guide.build_content(cats, encode, len)
        self.assertLess(len(new), len(old))
        self.assertEqual(content.read_content(new), content.read_content(old))


if __name__ == '__main__':
    unittest.main()
