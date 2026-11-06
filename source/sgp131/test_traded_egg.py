"""HG-T12: the hatch palette must use the final hatcher OT."""
import importlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

from sgp12.rom import bl_decode


CASES = (
    # breeder OT, hatcher OT, PID, animation before, required after
    (0, 0x100, 0, True, False),
    (0, 0x100, 0x100, False, True),
    (0, 0x100, 0x200, False, False),
    (0, 0, 0, True, True),             # non-traded control
)


def stage(test):
    spec = importlib.util.find_spec('sgp131.traded_egg')
    test.assertIsNotNone(spec, 'HG-T12 production stage is absent')
    return importlib.import_module('sgp131.traded_egg')


class TradedEggPatchTests(unittest.TestCase):
    def test_four_ot_pid_cases_replace_only_the_palette_classification(self):
        module = stage(self)
        for breeder, hatcher, pid, before, expected in CASES:
            with self.subTest(breeder=breeder, hatcher=hatcher, pid=pid):
                self.assertEqual(module.plus_is_shiny(breeder, pid), before)
                self.assertEqual(module.plus_is_shiny(hatcher, pid), expected)
                normal_palette = 0x104
                breeder_palette = normal_palette | int(before)
                self.assertEqual(
                    module.final_palette_id(breeder_palette, hatcher, pid),
                    normal_palette | int(expected))

    def test_native_payload_has_one_entry_three_real_calls_and_preserves_budget(self):
        module = stage(self)
        with tempfile.TemporaryDirectory(prefix='traded-egg-test-') as scratch:
            payload, report = module.compile_native(Path(scratch))
        self.assertEqual(len(payload), module.PAYLOAD_BYTES)
        self.assertEqual(report['bytes'], module.PAYLOAD_BYTES)
        self.assertEqual(report['entry'], module.HELPER_ADDRESS | 1)
        self.assertEqual(report['call_targets'], [
            module.GET_SPRITE_IDS, module.GET_MON_DATA, module.IS_SHINY])
        self.assertEqual(report['stack_delta'], 0)
        self.assertEqual(report['preserved_registers'], ['r4', 'r5', 'r6', 'r7'])

    def test_overlay_patch_retargets_only_the_guarded_sprite_call_and_appends_helper(self):
        module = stage(self)
        image = bytearray((index * 29 + 3) & 0xFF
                          for index in range(module.OVERLAY_SIZE))
        seam = module.CALL_SITE - module.OVERLAY_BASE
        image[seam:seam + 4] = module.CALL_PREIMAGE
        with tempfile.TemporaryDirectory(prefix='traded-egg-test-') as scratch:
            payload, _ = module.compile_native(Path(scratch))
        after, report = module.patch_overlay(
            bytes(image), payload, overlay_sha256=None, context_sha256=None)
        self.assertEqual(len(after), module.OVERLAY_SIZE + module.PAYLOAD_BYTES)
        self.assertEqual(after[:seam], image[:seam])
        self.assertEqual(after[seam + 4:module.OVERLAY_SIZE], image[seam + 4:])
        self.assertEqual(after[module.OVERLAY_SIZE:], payload)
        self.assertEqual(bl_decode(module.CALL_SITE, after[seam:seam + 4]),
                         module.HELPER_ADDRESS)
        self.assertEqual(report['old_target'], module.GET_SPRITE_IDS)
        self.assertEqual(report['new_target'], module.HELPER_ADDRESS)

    def test_preimage_repeat_and_unrelated_mutants_fail_closed(self):
        module = stage(self)
        image = bytearray((index * 31 + 11) & 0xFF
                          for index in range(module.OVERLAY_SIZE))
        seam = module.CALL_SITE - module.OVERLAY_BASE
        image[seam:seam + 4] = module.CALL_PREIMAGE
        with tempfile.TemporaryDirectory(prefix='traded-egg-test-') as scratch:
            payload, _ = module.compile_native(Path(scratch))
        after, _ = module.patch_overlay(
            bytes(image), payload, overlay_sha256=None, context_sha256=None)
        damaged = bytearray(image)
        damaged[seam] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage'):
            module.patch_overlay(bytes(damaged), payload,
                                 overlay_sha256=None, context_sha256=None)
        with self.assertRaisesRegex(ValueError, 'preimage|size'):
            module.patch_overlay(after, payload,
                                 overlay_sha256=None, context_sha256=None)
        damaged = bytearray(after)
        damaged[0] ^= 1
        with self.assertRaises(ValueError):
            module.verify_images(bytes(image), bytes(damaged), payload)


if __name__ == '__main__':
    unittest.main()
