"""Focused synthetic contracts for candidate-derived localized player manuals."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile
import unittest
import zlib

try:
    from distribution import reference_docs as docs
except ImportError:
    docs = None


def pdf_ascii_text(raw):
    """Read ASCII drawing strings from ReportLab's independently decoded streams."""
    strings = []
    for match in re.finditer(rb'stream\r?\n(.*?)endstream', raw, re.S):
        payload = match[1].strip()
        try:
            if payload.endswith(b'~>'):
                payload = base64.a85decode(payload, adobe=True)
            payload = zlib.decompress(payload)
        except (ValueError, zlib.error):
            continue
        if b'BT' not in payload:
            continue
        for token in re.findall(rb'\(((?:\\.|[^\\)])*)\)', payload):
            def unescape(found):
                code = found[1]
                return bytes([int(code, 8)]) if code[:1].isdigit() else code
            strings.append(re.sub(rb'\\([0-7]{1,3}|.)', unescape, token))
    return b''.join(strings)


class ReferenceDocumentTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(docs, 'candidate-derived manual renderer is missing')

    def test_evolution_rows_preserve_parameters_and_reject_unknown_methods(self):
        records = [bytes(44) for _ in range(494)]
        records[64] = struct.pack('<HHH', 6, 467, 65) + bytes(38)
        self.assertEqual(docs.parse_evolutions(records), [(64, 0, 6, 467, 65)])
        records[64] = struct.pack('<HHH', 99, 4, 65) + bytes(38)
        with self.assertRaisesRegex(ValueError, 'evolution'):
            docs.parse_evolutions(records)

    def test_reader_preserves_native_duplicate_learnset_pairs(self):
        personal = [bytes(44) for _ in range(494)]
        learnsets = [b'\xff\xff' for _ in range(494)]
        learnsets[67] = struct.pack('<3H', 512 + 1, 512 + 1, 65535)
        self.assertEqual(docs.parse_species(personal, learnsets)[66]['learnset'], ((1, 1), (1, 1)))

    def test_native_learnset_order_is_preserved_even_when_levels_decrease(self):
        self.assertEqual(docs.decode_learnset(struct.pack('<3H', 10 * 512 + 1, 512 + 2, 65535)),
                         ((10, 1), (1, 2)))

    def test_encounters_use_map_header_bank_and_section_not_name_order(self):
        headers = bytearray(24 * 2)
        headers[0], headers[24] = 1, 0
        headers[18], headers[42] = 33, 44
        a, b = bytearray(196), bytearray(196)
        a[0] = b[0] = 20
        a[8] = 7
        b[8] = 9
        struct.pack_into('<H', a, 20, 25)
        struct.pack_into('<H', b, 20, 133)
        rows = docs.parse_encounters([bytes(a), bytes(b)], bytes(headers))
        self.assertIn((0, 33, 1, 0, 0, 0, 133, 9, 9, 20), rows)
        self.assertIn((1, 44, 0, 0, 0, 0, 25, 7, 7, 20), rows)
        self.assertFalse(any(row[6] == 0 for row in rows))
        with self.assertRaisesRegex(ValueError, 'bank'):
            docs.parse_encounters([bytes(a)], bytes(headers))

    def test_night_fishing_zero_is_not_a_species_or_override(self):
        h = bytearray(24); h[18] = 8
        bank = bytearray(196); bank[4] = 15
        struct.pack_into('<BBH', bank, 0x94 + 12, 10, 20, 25)
        rows = docs.parse_encounters([bytes(bank)], bytes(h))
        self.assertIn((0, 8, 0, 4, -1, 3, 25, 10, 20, 15), rows)
        self.assertFalse(any(row[3] == 11 for row in rows))
        struct.pack_into('<H', bank, 0xC0, 133)
        self.assertIn((0, 8, 0, 11, 2, 3, 133, 10, 20, 15),
                      docs.parse_encounters([bytes(bank)], bytes(h)))

    def test_selector_weights_are_measured_from_instructions_not_assumed(self):
        image = struct.pack('<6H', 0x2850, 0xD201, 0x2000, 0x4770, 0x2001, 0x4770)
        self.assertEqual(docs.native_selector_weights(image, 0x02240000, {'test': (0x02240000, 2)}),
                         {'test': (80, 20)})
        changed = struct.pack('<H', 0x2814) + image[2:]
        self.assertEqual(docs.native_selector_weights(changed, 0x02240000, {'test': (0x02240000, 2)}),
                         {'test': (20, 80)})

    def test_headbutt_uses_map_ids_and_validates_tree_coordinate_extent(self):
        header = bytearray(24); header[18] = 7
        raw = bytearray(100); struct.pack_into('<HH', raw, 0, 1, 0)
        struct.pack_into('<HBB', raw, 4, 25, 5, 7)
        self.assertEqual(docs.parse_headbutt([bytes(raw)], bytes(header)), [(0, 7, 0, 0, 25, 5, 7)])
        with self.assertRaisesRegex(ValueError, 'Headbutt'):
            docs.parse_headbutt([bytes(raw[:-1])], bytes(header))

    def test_bug_contest_preserves_national_day_set_and_slot_rate(self):
        raw = bytearray()
        for index in range(40):
            threshold = (80, 60, 50, 40, 30, 20, 15, 10, 5, 0)[index % 10]
            raw += struct.pack('<HBBBB2x', 133 if index == 39 else 25, 12, 19, threshold, 50)
        rows = docs.parse_contest(bytes(raw))
        self.assertEqual(rows[-1], (3, 9, 133, 12, 19, 5, 50))
        self.assertEqual(sum(row[5] for row in rows if row[0] == 3), 100)

    def test_safari_bonus_conditions_are_points_and_keep_stored_priority(self):
        raw = bytearray(8); raw[0] = 1
        for method in range(5):
            raw += struct.pack('<HH', 25, 10) * 30
            if method == 0:
                raw += struct.pack('<HH', 133, 20) * 3
                raw += bytes([1, 4, 2, 8])
        rows = docs.parse_safari([bytes(raw)])
        self.assertIn((0, 0, 2, 0, 1, 133, 20, (1, 4, 2, 8)), rows)
        self.assertEqual(len(rows), 153)
        with self.assertRaisesRegex(ValueError, 'Safari'):
            docs.parse_safari([bytes(raw[:-1])])

    def test_trainer_formats_keep_item_form_and_exact_level_table(self):
        headers, parties = [], []
        for kind in range(4):
            header = bytearray(20); header[0] = kind; header[1] = 2; header[3] = 1
            member = bytearray(struct.pack('<BBHH', 200, 0x21, 50, 25 | (2 << 10)))
            if kind & 2: member += struct.pack('<H', 80)
            if kind & 1: member += struct.pack('<4H', 1, 2, 3, 4)
            member += struct.pack('<H', 17)
            headers.append(bytes(header)); parties.append(bytes(member))
        levels = bytes(min(100, i + 7) for i in range(256))
        rows = docs.parse_trainers(headers, parties, levels)
        for kind, row in enumerate(rows):
            mon = row['party'][0]
            self.assertEqual((mon['species'], mon['form'], mon['level'], mon['plus_level']),
                             (25, 2, 50, 57))
            self.assertEqual(mon['item'], 80 if kind & 2 else 0)
            self.assertEqual(mon['moves'], (1, 2, 3, 4) if kind & 1 else ())
        with self.assertRaisesRegex(ValueError, 'party'):
            docs.parse_trainers(headers, [b'bad'] + parties[1:], levels)

    def test_installed_strategy_moves_require_the_exact_party_preimage(self):
        header = bytes([3, 2, 0, 6]) + bytes(16)
        party = struct.pack('<BBHHH4HH', 200, 0, 50, 25, 80, 1, 2, 3, 4, 0) * 6
        config = (struct.pack('<IHH', 0x31544753, 1, 1)
                  + struct.pack('<HHIIBBBB', 0, 0, 0xDDCA0F0D, 0xBD4A6489, 3, 6, 108, 1)
                  + struct.pack('<4H', 8, 1, 5, 0))
        row = docs.parse_trainers([header], [party], strategy=config)[0]['party'][0]
        self.assertEqual(row['moves'], (1, 2, 3, 4))
        self.assertEqual(row['plus_moves'], (5, 2, 3, 4))
        with self.assertRaisesRegex(ValueError, 'preimage'):
            docs.parse_trainers([header], [bytes([0]) + party[1:]], strategy=config)

    def test_trainer_header_count_excludes_unused_archive_records(self):
        header = bytes([0, 2, 0, 1]) + bytes(16)
        mon = struct.pack('<BBHHH', 100, 0, 20, 25, 0)
        rows = docs.parse_trainers([header], [mon + mon])
        self.assertEqual(len(rows[0]['party']), 1)
        self.assertEqual(rows[0]['unused_records'], 1)

    def test_numeric_rows_do_not_depend_on_translated_names_or_guide_wrapping(self):
        left = dict(species=[dict(id=1, stats=(1, 2, 3, 4, 5, 6))], evolutions=[],
                    encounters=[], trainers=[], names={'pokemon': ['A']},
                    guide=[dict(id=3, entries=[dict(id=100, title='A', pages=[dict(lines=['A'], reference=0)])])])
        right = copy.deepcopy(left)
        right['names']['pokemon'] = ['B']
        right['guide'][0]['entries'][0].update(title='B', pages=[dict(lines=['Long', 'B'], reference=0)])
        self.assertEqual(docs.normalized_rows(left), docs.normalized_rows(right))
        right['species'][0]['stats'] = (2, 2, 3, 4, 5, 6)
        self.assertNotEqual(docs.normalized_rows(left), docs.normalized_rows(right))

    def test_every_locale_document_catalogue_is_complete_without_fallback(self):
        for locale in ('EN', 'IT', 'FR', 'ES', 'DE'):
            values = docs.load_documents(locale)
            self.assertEqual(len(values), 114)
            del values['d:news:27']
            with self.assertRaisesRegex(ValueError, 'missing'):
                docs.validate_documents(values)

    def test_bad_target_identity_is_rejected_before_creating_outputs(self):
        cfg = dict(version='1.3.2', targets={'EN': dict(sha256='0' * 64, bytes=4)},
                   sources=[dict(id='retail', label='Retail', sha256=hashlib.sha256(b'base').hexdigest(), bytes=4)],
                   routes_by_target={'EN': ['retail']}, schema=2)
        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / 'new'
            with self.assertRaisesRegex(ValueError, 'candidate'):
                docs.render_manuals('EN', b'test', b'base', Path('unused'), cfg, output)
            self.assertFalse(output.exists())
        cfg['targets']['EN']['sha256'] = hashlib.sha256(b'test').hexdigest()
        cfg['sources'][0]['id'] = '../bad'
        cfg['routes_by_target']['EN'] = ['../bad']
        with self.assertRaisesRegex(ValueError, 'source ID'):
            docs.validate_inputs('EN', b'test', b'base', cfg)

    def test_reference_requires_matching_clean_retail_even_when_plus_is_recognized(self):
        cfg = dict(version='1.3.2', targets={'EN':dict(sha256=hashlib.sha256(b'test').hexdigest(),bytes=4)},
                   sources=[dict(id=identity,label=identity,sha256=hashlib.sha256(raw).hexdigest(),bytes=4)
                            for identity,raw in [('clean-us',b'base'),('plus-1.3.1-en',b'plus')]],
                   routes_by_target={'EN':['clean-us','plus-1.3.1-en']})
        docs.validate_inputs('EN',b'test',b'base',cfg)
        with self.assertRaisesRegex(ValueError,'matching clean retail'):
            docs.validate_inputs('EN',b'test',b'plus',cfg)

    def test_native_pkmn_ligature_and_fullwidth_symbols_have_readable_pdf_text(self):
        self.assertEqual(docs.pdf_text('₧₦ Trainer ＆ Nidoran♀ / Nidoran♂'),
                         'Pokémon Trainer & Nidoran(F) / Nidoran(M)')

    def test_nine_pdf_outputs_include_localized_titles_and_refuse_overwrite(self):
        facts = dict(names={'pokemon': ['Zero', 'Sample'], 'type': ['Type'],
                            'ability': ['None'], 'stat': ['HP', 'Atk', 'Def', 'Spe', 'SpA', 'SpD'],
                            'item': ['None'], 'move': ['None'], 'map': ['Location'],
                            'trainer': ['Name'], 'class': ['Class'], 'radio': ['Radio', 'One', 'Two'],
                            'swarm': ['Swarm']}, species=[dict(id=1, stats=(1,2,3,4,5,6), types=(0,0),
                            abilities=(0,0), learnset=())], evolutions=[], encounters=[], trainers=[],
                     guide=[dict(id=i, title='Category', entries=[dict(id=100+i, title='Sample',
                            pages=[dict(lines=['Sample content'], reference=0)])]) for i in (1,2,3,4)])
        cfg = dict(version='1.3.2', schema=2, targets={'ES': dict(sha256='a'*64, bytes=5)},
                   sources=[dict(id='base', label='Original', sha256='b'*64, bytes=4)], routes_by_target={'ES':['base']})
        with tempfile.TemporaryDirectory() as work:
            out = Path(work) / 'manuals'
            paths = docs.render_facts('ES', facts, facts, cfg, out)
            self.assertEqual(len(paths), 9)
            self.assertEqual(len({p.name for p in paths}), 9)
            text = pdf_ascii_text(paths[0].read_bytes())
            self.assertIn(b'instalaci', text.lower())
            self.assertIn(b'Patch/base.xdelta', text)
            self.assertIn(b'a' * 64, text)
            before = {p: p.read_bytes() for p in paths}
            with self.assertRaises(FileExistsError):
                docs.render_facts('ES', facts, facts, cfg, out)
            self.assertEqual(before, {p: p.read_bytes() for p in paths})


if __name__ == '__main__':
    unittest.main()
