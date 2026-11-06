"""Class B HG-F17 test on immutable EN/IT V4 candidates, patched in memory."""
from pathlib import Path
import hashlib
import unittest

import ndspy.narc
import ndspy.rom

from sgp131 import battle_animation_facade as facade
from sgp131 import mechanics_stages


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           '5dc89a128aa210a88e768baea65263baeccc2473fe3cc6778e1d7925aa867f7b'),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           '8abbb5b777177ff771d667291905d76a85a8a54d38360f337275e77f3e8c04f6'),
}


class ActualFacadeCandidates(unittest.TestCase):
    def test_exact_candidates_reproduce_overlap_and_fix_only_six_bytes(self):
        for language, (input_sha, output_sha) in V4.items():
            with self.subTest(language=language):
                path = V4_ROOT / f'candidate-v4-{language}.nds'
                if not path.is_file():
                    self.skipTest('immutable V4 candidate unavailable: ' + str(path))
                before = path.read_bytes()
                self.assertEqual(hashlib.sha256(before).hexdigest(), input_sha)

                old_rom = ndspy.rom.NintendoDSRom(before)
                old_member = bytes(ndspy.narc.NARC(
                    old_rom.getFileByName('a/0/1/0')).files[263])
                self.assertEqual(hashlib.sha256(old_member).hexdigest(),
                                 facade.MEMBER_BEFORE_SHA256)
                self.assertEqual(len(facade.read_member_timing(old_member).schedule.overlaps), 5)

                after, receipt = facade.apply(before, language)
                report = facade.verify(before, after, receipt)
                self.assertEqual(hashlib.sha256(after).hexdigest(), output_sha)
                self.assertEqual(receipt['output_sha256'], output_sha)
                self.assertEqual(report['changed_rom_bytes'], 6)
                self.assertEqual(report['overlaps_before'], 5)
                self.assertEqual(report['overlaps_after'], 0)
                self.assertEqual(report['task_durations_before'], [10] * 6)
                self.assertEqual(report['task_durations_after'], [10] * 6)

                new_member = bytes(ndspy.narc.NARC(
                    ndspy.rom.NintendoDSRom(after).getFileByName('a/0/1/0')).files[263])
                self.assertEqual(hashlib.sha256(new_member).hexdigest(),
                                 facade.MEMBER_AFTER_SHA256)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), input_sha)

                stage = mechanics_stages.require_stage('battle-animation-facade')
                regions = stage.regions(before)
                self.assertEqual([(region.start, region.end) for region in regions],
                                 [(offset, offset + 1) for offset in receipt['rom_offsets']])
                mechanics_stages.check_confined(before, after, regions, stage.name)
                self.assertEqual(stage.verify(before, after, receipt), report)

                mutant = bytearray(after)
                mutant[0x200] ^= 1
                mutant = bytes(mutant)
                mutant_receipt = dict(receipt, output_sha256=hashlib.sha256(mutant).hexdigest())
                with self.assertRaisesRegex(ValueError, 'changed ROM offsets'):
                    facade.verify(before, mutant, mutant_receipt)
                with self.assertRaisesRegex(ValueError, 'receipt timing'):
                    facade.verify(before, after, dict(receipt, interval_after=11))


if __name__ == '__main__':
    unittest.main()
