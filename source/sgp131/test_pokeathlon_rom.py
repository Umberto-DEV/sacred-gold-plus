"""Real-ROM pipeline checks for the Pokéathlon friendship summary fix."""
import hashlib
from pathlib import Path
import unittest

import ndspy.rom

from sgp12.rom import Rom
from . import pokeathlon as p


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}


class PokeathlonRomPipelineTests(unittest.TestCase):
    def test_real_v4_candidates_patch_only_overlay99_and_verify(self):
        for language, identity in V4.items():
            with self.subTest(language=language):
                path = EXPERIMENT / f'candidate-v4-{language}.nds'
                if not path.is_file():
                    self.skipTest('immutable V4 candidate is unavailable: ' + str(path))
                before = path.read_bytes()
                self.assertEqual((hashlib.sha256(before).hexdigest(), len(before)), identity)
                old_entry, old_stream, old_image = Rom(before).immagine_overlay(p.OVERLAY_ID)
                after, receipt = p.apply(before, language)
                new_entry, new_stream, new_image = Rom(after).immagine_overlay(p.OVERLAY_ID)
                self.assertEqual(old_entry, new_entry)
                self.assertEqual(len(old_stream), len(new_stream))
                self.assertEqual(hashlib.sha256(new_stream).hexdigest(),
                                 'e6c157762956be2e9d5f5fae3670f91727b3b7a578430939839b1c57cca337f9')
                self.assertEqual(hashlib.sha256(new_image).hexdigest(),
                                 '96e060c646878088735e201290efc83a1081fda3b0e86e55b8a13e85cd106a0c')
                report = p.verify(before, after, receipt)
                self.assertTrue(report['ok'])
                self.assertEqual(report['logical_changed_bytes'], 4)
                parsed_before = ndspy.rom.NintendoDSRom(before)
                parsed_after = ndspy.rom.NintendoDSRom(after)
                self.assertEqual(len(parsed_before.files), len(parsed_after.files))
                for index, (old_file, new_file) in enumerate(
                        zip(parsed_before.files, parsed_after.files)):
                    if index != p.OVERLAY_ID:
                        self.assertEqual(old_file, new_file, index)
                expected, _ = p.patch_overlay(old_image)
                self.assertEqual(new_image, expected)

    def test_receipt_and_unrelated_changes_are_refused(self):
        path = EXPERIMENT / 'candidate-v4-EN.nds'
        if not path.is_file():
            self.skipTest('immutable V4 candidate is unavailable: ' + str(path))
        before = path.read_bytes()
        after, receipt = p.apply(before, 'EN')
        forged = {**receipt, 'output_sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'receipt'):
            p.verify(before, after, forged)
        damaged = bytearray(after)
        damaged[0x201] ^= 1
        forged = {**receipt, 'output_sha256': hashlib.sha256(damaged).hexdigest(),
                  'writer': {**receipt['writer'],
                             'uscita_sha256': hashlib.sha256(damaged).hexdigest()}}
        with self.assertRaisesRegex(ValueError, 'outside'):
            p.verify(before, bytes(damaged), forged)


if __name__ == '__main__':
    unittest.main()
