"""Class B HG-F20-DP test on immutable EN/IT V4 candidates, in memory."""
from pathlib import Path
import hashlib
import unittest

import ndspy.narc
import ndspy.rom

from sgp131 import battle_animation_dynamicpunch as dynamicpunch
from sgp131 import battle_animation_facade as facade
from sgp131 import mechanics_stages


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           '5dc89a128aa210a88e768baea65263baeccc2473fe3cc6778e1d7925aa867f7b',
           '102e5fca155807a5bde6e0b534901b6314c187f8a30672acf1a9db147a0abc73'),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           '8abbb5b777177ff771d667291905d76a85a8a54d38360f337275e77f3e8c04f6',
           '0fc63429cad6a33d0d76204f2ed1c2c96abcbdb8cd98f1fc22df0ebbca635d98'),
}


class ActualDynamicPunchCandidates(unittest.TestCase):
    def test_facade_successor_reproduces_drift_and_fixes_only_one_more_byte(self):
        for language, (input_sha, facade_sha, output_sha) in V4.items():
            with self.subTest(language=language):
                path = V4_ROOT / f'candidate-v4-{language}.nds'
                if not path.is_file():
                    self.skipTest('immutable V4 candidate unavailable: ' + str(path))
                before = path.read_bytes()
                self.assertEqual(hashlib.sha256(before).hexdigest(), input_sha)
                with self.assertRaisesRegex(ValueError, 'Facade predecessor missing'):
                    dynamicpunch.apply(before, language)

                after_facade, _facade_receipt = facade.apply(before, language)
                self.assertEqual(hashlib.sha256(after_facade).hexdigest(), facade_sha)
                old_archive = bytes(ndspy.rom.NintendoDSRom(after_facade).getFileByName(
                    dynamicpunch.ARCHIVE))
                self.assertEqual(hashlib.sha256(old_archive).hexdigest(),
                                 dynamicpunch.ARCHIVE_BEFORE_SHA256)
                old_files = ndspy.narc.NARC(old_archive).files
                self.assertEqual(hashlib.sha256(bytes(old_files[263])).hexdigest(),
                                 facade.MEMBER_AFTER_SHA256)
                retail = dynamicpunch.read_member_timing(bytes(old_files[223]))
                self.assertEqual(retail.schedule.final_x, -1)

                after, receipt = dynamicpunch.apply(after_facade, language)
                report = dynamicpunch.verify(after_facade, after, receipt)
                self.assertEqual(hashlib.sha256(after).hexdigest(), output_sha)
                self.assertEqual(receipt['output_sha256'], output_sha)
                self.assertEqual(report['changed_rom_bytes'], 1)
                self.assertEqual(report['rom_offset'], 17235080)
                self.assertEqual(report['second_start_tick_before'], 7)
                self.assertEqual(report['second_start_tick_after'], 8)
                self.assertEqual(report['captured_base_x_before'], -1)
                self.assertEqual(report['captured_base_x_after'], 0)
                self.assertEqual(report['final_x_before'], -1)
                self.assertEqual(report['final_x_after'], 0)
                self.assertTrue(report['facade_member_preserved'])

                new_archive = bytes(ndspy.rom.NintendoDSRom(after).getFileByName(
                    dynamicpunch.ARCHIVE))
                new_files = ndspy.narc.NARC(new_archive).files
                self.assertEqual(hashlib.sha256(new_archive).hexdigest(),
                                 dynamicpunch.ARCHIVE_AFTER_SHA256)
                self.assertEqual(hashlib.sha256(bytes(new_files[223])).hexdigest(),
                                 dynamicpunch.MEMBER_AFTER_SHA256)
                self.assertEqual(bytes(new_files[263]), bytes(old_files[263]))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), input_sha)

                stage = mechanics_stages.require_stage('battle-animation-dynamicpunch')
                cold_regions = stage.regions(before)
                predecessor_regions = stage.regions(after_facade)
                self.assertEqual(cold_regions, predecessor_regions)
                self.assertEqual([(region.start, region.end) for region in predecessor_regions],
                                 [(17235080, 17235081)])
                mechanics_stages.check_confined(
                    after_facade, after, predecessor_regions, stage.name)
                self.assertEqual(stage.verify(after_facade, after, receipt), report)

                no_ui_writes = lambda *_args: None
                staged_facade, wrapped_facade = mechanics_stages.run_stage(
                    'battle-animation-facade', before, language,
                    invariants=no_ui_writes)
                staged_final, wrapped_dynamicpunch = mechanics_stages.run_stage(
                    'battle-animation-dynamicpunch', staged_facade, language,
                    invariants=no_ui_writes)
                self.assertEqual((staged_facade, staged_final), (after_facade, after))

                def exact_cold_image(image):
                    self.assertEqual(image, before)
                    return {'cold_v4_reconstructed': True}

                replay = mechanics_stages.verify_chain(
                    before, staged_final,
                    ['battle-animation-facade', 'battle-animation-dynamicpunch'],
                    [wrapped_facade, wrapped_dynamicpunch], exact_cold_image,
                    invariants=no_ui_writes,
                )
                self.assertEqual(replay['stages'],
                                 ['battle-animation-facade',
                                  'battle-animation-dynamicpunch'])

                mutant = bytearray(after)
                mutant[0x300] ^= 1
                mutant = bytes(mutant)
                mutant_receipt = dict(
                    receipt, output_sha256=hashlib.sha256(mutant).hexdigest())
                with self.assertRaisesRegex(ValueError, 'changed ROM offsets'):
                    dynamicpunch.verify(after_facade, mutant, mutant_receipt)
                with self.assertRaisesRegex(ValueError, 'receipt timing'):
                    dynamicpunch.verify(
                        after_facade, after, dict(receipt, delay_after=5))


if __name__ == '__main__':
    unittest.main()
