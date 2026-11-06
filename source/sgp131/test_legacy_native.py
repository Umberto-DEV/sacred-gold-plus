"""Bounded real-input composition checks; no persistent ROMs or save access."""
import copy
import hashlib
import os
from pathlib import Path
import unittest

from . import (bag_alloc, fishing, gb_sounds_evolution, igt, legacy_native,
               mechanics_stages, plus_save, pokegear_autocull, soul_dew,
               victory_road_fly, wonder_card)
from .ui_verify import Image

ROOT = Path(__file__).resolve().parents[2]


class NativeComposition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = {lang: ROOT / f'local/experiments/balance493-2026-10-28/candidate-v4-{lang}.nds'
                 for lang in ('EN', 'IT')}
        if not all(p.is_file() for p in paths.values()):
            if os.environ.get('SGP_LEGACY_REQUIRE_INPUTS') == '1':
                raise AssertionError('legacy native checks require both canonical V4 inputs')
            raise unittest.SkipTest('legacy native checks require both canonical V4 inputs')
        from .baseline import identify
        cls.images = {lang: path.read_bytes() for lang, path in paths.items()}
        for lang, data in cls.images.items():
            assert identify(data) == lang

    def test_combined_owner_actual_regions_and_independent_reader(self):
        for language, before in self.images.items():
            after, receipt = legacy_native.apply(before, language)
            result = legacy_native.verify(before, after, receipt)
            self.assertTrue(result['ok'])
            self.assertEqual(len(after), len(before))
            self.assertEqual(after[:0x200], before[:0x200])
            regions = mechanics_stages.REGISTRY['legacy'].regions(before)
            self.assertEqual(len(regions), 18)
            self.assertEqual(sorted(r.end-r.start for r in regions),
                             [2, 4, 4, 4, 4, 8, 28, 32, 32, 32, 36, 54, 56, 62,
                              80, 736, 42700, 53576])
            self.assertEqual(Image(after).arm(igt.SITE, 2), b'\x02\xd9')
            self.assertEqual(Image(after).arm(bag_alloc.ENTRY, len(bag_alloc.POSTIMAGE)),
                             bag_alloc.POSTIMAGE)
            self.assertEqual(Image(after).arm(soul_dew.GETTER, len(soul_dew.HOOK_POSTIMAGE)),
                             soul_dew.HOOK_POSTIMAGE)
            self.assertEqual(Image(after).arm(soul_dew.SLOT, soul_dew.SLOT_BYTES),
                             soul_dew.SLOT_POSTIMAGE)
            self.assertEqual(Image(after).arm(wonder_card.SLOT, wonder_card.SLOT_BYTES),
                             wonder_card.SLOT_POSTIMAGE)
            self.assertEqual(Image(after).arm(gb_sounds_evolution.SLOT,
                                              gb_sounds_evolution.SLOT_BYTES),
                             gb_sounds_evolution.SLOT_POSTIMAGE)
            self.assertEqual(Image(after).arm(pokegear_autocull.SLOT,
                                              pokegear_autocull.SLOT_BYTES),
                             pokegear_autocull.SLOT_POSTIMAGE)
            installed = Image(after).arm(plus_save.BASE, plus_save.CAPACITY)
            self.assertEqual(hashlib.sha256(installed).hexdigest(), plus_save.POSTIMAGE_SHA256)
            self.assertEqual(hashlib.sha256(installed[:plus_save.PAYLOAD_BYTES]).hexdigest(),
                             plus_save.PAYLOAD_SHA256)
            self.assertEqual(installed[plus_save.PAYLOAD_BYTES:],
                             bytes(plus_save.CAPACITY - plus_save.PAYLOAD_BYTES))
            for overlay in (2, 101):
                _, _, image = fishing._read(after, overlay)
                address, _, patch = fishing.WINDOWS[overlay]
                base = fishing.OVERLAYS[overlay][0]
                self.assertEqual(image[address-base:address-base+len(patch)], patch)
            _entry, _stream, map_image = fishing._read(after, 101)
            gate = victory_road_fly.GATE_OFFSET
            self.assertEqual(map_image[gate:gate + victory_road_fly.GATE_BYTES],
                             victory_road_fly.GATE_POSTIMAGE)
            self.assertEqual([step['stage'] for step in receipt['steps']],
                             ['legacy-lullaby', 'legacy-fishing',
                              'victory-road-fly', 'soul-dew',
                              'wonder-card-decoration-guard',
                              'gb-sounds-evolution', 'pokegear-autocull',
                              'legacy-igt', 'plus-save', 'bag-allocation'])
            for changes in ({'output_sha256': '0'*64}, {'language': 'FR'}):
                with self.assertRaises(ValueError):
                    legacy_native.verify(before, after, dict(receipt, **changes))
            broken = copy.deepcopy(receipt)
            broken['steps'][2], broken['steps'][3] = broken['steps'][3], broken['steps'][2]
            with self.assertRaises(ValueError):
                legacy_native.verify(before, after, broken)
            broken = copy.deepcopy(receipt)
            broken['steps'][5]['slot_postimage_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                legacy_native.verify(before, after, broken)
            broken = copy.deepcopy(receipt)
            broken['steps'][8]['postimage_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                legacy_native.verify(before, after, broken)
            broken = copy.deepcopy(receipt)
            broken['steps'][9]['postimage_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                legacy_native.verify(before, after, broken)
            bad = bytearray(after)
            bad[0x15E] ^= 1
            with self.assertRaises(ValueError):
                legacy_native.verify(before, bytes(bad), receipt)


if __name__ == '__main__':
    unittest.main()
