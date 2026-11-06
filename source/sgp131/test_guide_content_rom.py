"""Class B: whole pinned V4 EN/IT graph, legacy reproduction, immutable inputs.

Set SGP131_BASE_EN/IT and SGP_PRET_SOURCE (external pinned pret checkout), or
SGP131_GUIDE_CHARMAP. Missing inputs explicitly skip per language; setting
SGP131_GUIDE_CONTENT_REQUIRE_INPUTS=1 makes them fail. All extracted content and
successor bytes remain in RAM; no ROM, save or extracted asset is written.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import tempfile
import unicodedata
import unittest

import ndspy.narc
import ndspy.rom

from sgp13 import content as legacy
from sgp131 import guide_content as successor

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256,
           113534, '71e3bc3bba6a6ddaeb38ea47184619ace5ae718ac34601821a5576db4e474e3d'),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136,
           119048, 'fe193a7ea1205c5b6a7ca85160db6b803f2044748e3a05b710983f16cb1f44ce'),
}
GROUPS = {2480: [480, 481, 482], 2483: [483, 484, 487], 2377: [377, 378, 379],
          2243: [243, 244, 245], 2250: [250, 249], 2383: [383, 382, 384],
          2380: [380, 381], 3001: [1, 4, 7], 3002: [252, 255, 258],
          3003: [387, 390, 393], 3004: [152, 155, 158], 3005: [149, 248, 373, 376, 445],
          1453: [488], 1458: [485]}


def digest(path):
    state = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            state.update(chunk)
    return state.hexdigest()


def independent_order(name, identity):
    # Separate oracle, deliberately not successor.sort_key.
    folded = unicodedata.normalize('NFKD', name.casefold())
    sex = tuple({'♀': 'female', '♂': 'male'}[c] for c in folded if c in '♀♂')
    letters = ''.join(' ' if unicodedata.category(c)[0] == 'P' else c for c in folded
                      if not unicodedata.combining(c) and c not in "'’‘ʼ♀♂")
    return ' '.join(letters.split()), sex, unicodedata.normalize('NFKC', name).casefold(), identity


class CanonicalContentTests(unittest.TestCase):
    def _check(self, language):
        configured = os.environ.get('SGP131_BASE_' + language)
        pret = os.environ.get('SGP_PRET_SOURCE')
        charmap = os.environ.get('SGP131_GUIDE_CHARMAP') or (str(Path(pret) / 'charmap.txt') if pret else None)
        missing = []
        if not configured or not Path(configured).is_file(): missing.append('SGP131_BASE_' + language)
        if not charmap or not Path(charmap).is_file(): missing.append('SGP_PRET_SOURCE / SGP131_GUIDE_CHARMAP')
        if missing:
            message = 'canonical Guide inputs missing: ' + ', '.join(missing)
            if os.environ.get('SGP131_GUIDE_CONTENT_REQUIRE_INPUTS') == '1': self.fail(message)
            self.skipTest(message)
        path, charmap = Path(configured), Path(charmap)
        source_paths = [ROOT / 'source/sgp13' / p for p in ('content.py', 'guide.py', 'data/guide.json')]
        source_paths += [successor.PROSE, successor.SUBJECTS_PATH, Path(successor.__file__), charmap]
        before = {str(p): digest(p) for p in source_paths + [path]}
        pin, size, legacy_size, legacy_hash = PINS[language]
        self.assertEqual((before[str(path)], path.stat().st_size), (pin, size))
        rom = ndspy.rom.NintendoDSRom.fromFile(path)
        installed = ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[829]
        old_before, _ = legacy.build_from_rom(path, language, charmap)
        self.assertEqual(old_before, installed)
        self.assertEqual((len(old_before), hashlib.sha256(old_before).hexdigest()), (legacy_size, legacy_hash))
        old_graph = successor.read_content(old_before)
        with tempfile.TemporaryDirectory(prefix='sgp131-guide-readback-') as directory:
            blob, receipt = successor.build_from_rom(path, language, charmap)
            again, again_receipt = successor.build_from_rom(path, language, charmap)
            self.assertEqual((blob, receipt), (again, again_receipt))
            self.assertEqual(list(Path(directory).iterdir()), [])
        actual = successor.read_content(blob)
        self.assertEqual([c['id'] for c in actual], [4, 1, 3, 2])
        self.assertEqual([len(c['entries']) for c in actual], [6, 229, 76, 156])
        self.assertEqual(receipt['records'], 467)
        self.assertEqual(receipt['covered_special_species'], 64)
        self.assertEqual(len(receipt['aliases']), 38)
        self.assertEqual(receipt['cap'], 131072)
        self.assertLess(len(blob), 131072)
        names, records, encode, measure = successor.load_inputs(path, language, charmap)
        del records
        prose = json.loads(successor.PROSE.read_text())
        byid = {e['id']: e for c in actual for e in c['entries']}
        oldbyid = {e['id']: e for c in old_graph for e in c['entries']}
        intended_ids = set(oldbyid) | {5000 + s for members in GROUPS.values() for s in members}
        self.assertEqual(set(byid), intended_ids)
        # Every actual evolution rule keeps its pages/links; only its exact name loses the numeric prefix.
        evolution_ids = [e['id'] for e in actual[1]['entries']]
        old_evolutions = next(c for c in old_graph if c['id'] == 1)['entries']
        self.assertEqual(set(evolution_ids), {e['id'] for e in old_evolutions})
        for entry in old_evolutions:
            self.assertEqual(byid[entry['id']]['title'], tuple(encode(names('pokemon', entry['id']))))
            self.assertEqual(byid[entry['id']]['pages'], entry['pages'])
        self.assertEqual(evolution_ids, sorted(evolution_ids, key=lambda i: independent_order(names('pokemon', i), i)))
        def expand(value):
            return re.sub(r'\{(pokemon|item|move|map):(\d+)\}',
                          lambda m: names(m[1], int(m[2])), value)
        display = {e['id']: names('pokemon', e['id']) for e in old_evolutions}
        # Every authored paragraph, page reference and title is checked from source, independent of make_categories.
        words = 0
        for category in prose['categories']:
            packed_cat = next(c for c in actual if c['id'] == category['id'])
            self.assertEqual(packed_cat['title'], tuple(encode(category['title'][language])))
            if category['id'] in (2, 4):
                self.assertEqual([e['id'] for e in packed_cat['entries']], [e['id'] for e in category['entries']])
            for entry in category['entries']:
                title = display[entry['id']] = expand(entry['title'][language])
                self.assertEqual(byid[entry['id']]['title'], tuple(encode(title)))
                expected_pages = []
                expected_words = []
                for page in entry['pages']:
                    paragraphs = [expand(s) for s in page[language]]
                    expected_words.extend(tuple(encode(w)) for p in paragraphs for w in p.split())
                    for p in legacy.paginate(paragraphs, measure, page.get('reference', 0)):
                        expected_pages.append(dict(lines=[tuple(encode(s)) for s in p['lines']], reference=p['reference']))
                self.assertEqual(byid[entry['id']]['pages'], expected_pages)
                # Independently split native encoded lines at the native encoded space; counts/words cannot disappear.
                actual_words = []
                space = encode(' ')[0]
                for page in byid[entry['id']]['pages']:
                    for line in page['lines']:
                        token = []
                        for code in line:
                            if code in (space, 65535):
                                self.assertTrue(token)
                                actual_words.append(tuple(token + [65535])); token = []
                            else: token.append(code)
                self.assertEqual(actual_words, expected_words)
                words += len(actual_words)
        # All group names are retained; every explicit member alias has its native localized title and exact canonical pages.
        for target, members in GROUPS.items():
            for species in members:
                alias = 5000 + species
                display[alias] = names('pokemon', species)
                self.assertEqual(byid[alias]['title'], tuple(encode(display[alias])))
                self.assertEqual(byid[alias]['pages'], byid[target]['pages'])
        special_ids = [e['id'] for e in actual[2]['entries']]
        self.assertEqual(special_ids, sorted(special_ids, key=lambda i: independent_order(display[i], i)))
        self.assertTrue(all(1 <= len(e['pages']) <= 255 for e in byid.values()))
        self.assertTrue(all(1 <= len(p['lines']) <= 7 for e in byid.values() for p in e['pages']))
        self.assertEqual(receipt['visible_pages'], sum(len(e['pages']) for e in byid.values()))
        self.assertEqual(receipt['visible_links'], sum(bool(p['reference']) for e in byid.values() for p in e['pages']))
        for e in byid.values():
            for p in e['pages']:
                self.assertTrue(not p['reference'] or p['reference'] in byid)
        # Each alias title has distinct entry/row identity even though the immutable page-table offset is shared.
        nc = struct.unpack_from('<H', blob, 8)[0]
        raw_entries = [struct.unpack_from('<HHHHII', blob, 12 + nc * 12 + i * 16) for i in range(467)]
        packed = {e[0]: e for e in raw_entries}
        for target, members in GROUPS.items():
            for species in members:
                self.assertEqual(packed[5000 + species][5], packed[target][5])
        self.assertLessEqual(receipt['max_title_width'], 208)
        self.assertLessEqual(receipt['max_body_width'], 208)
        old_after, _ = legacy.build_from_rom(path, language, charmap)
        self.assertEqual(old_after, old_before)
        self.assertEqual({str(p): digest(p) for p in source_paths + [path]}, before)
        print(json.dumps(dict(language=language, receipt=receipt, legacy_bytes=legacy_size,
                              legacy_sha256=legacy_hash, legacy_before_after_identical=True,
                              original_inputs_unchanged=True, canonical_authored_words_checked=words), sort_keys=True))

    def test_canonical_english(self):
        self._check('EN')

    def test_canonical_italian(self):
        self._check('IT')


if __name__ == '__main__':
    unittest.main()
