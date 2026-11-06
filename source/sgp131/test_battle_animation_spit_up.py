"""HG-F20-SU pure-oracle and exact cleanup tests."""
import unittest

from sgp131 import battle_animation_spit_up as spit_up


class SpitUpOracle(unittest.TestCase):
    def test_retail_accumulates_two_but_cleanup_delta_two_preserves_base_x(self):
        for base_x in (0, 1, 100, 253):
            with self.subTest(base_x=base_x):
                retail = spit_up.evaluate_runtime(base_x, cleanup_delta=0)
                fixed = spit_up.evaluate_runtime(base_x, cleanup_delta=2)
                self.assertEqual(retail.shake_deltas,
                                 (2, 0, -2, 0, 2, 0, -2, 0, 2, 0))
                self.assertEqual(retail.final_x, base_x + 2)
                self.assertEqual(fixed.final_x, base_x)
                self.assertEqual(fixed.ticks, 34)
                self.assertEqual(fixed.transitions,
                                 ((10, 0, 1), (26, 1, 2),
                                  (32, 2, 3), (33, 3, 4)))

    def test_subtract_one_and_three_are_live_negative_controls(self):
        for base_x in (0, 1, 100, 253):
            self.assertEqual(
                spit_up.evaluate_runtime(base_x, cleanup_delta=1).final_x,
                base_x + 1)
            self.assertEqual(
                spit_up.evaluate_runtime(base_x, cleanup_delta=3).final_x,
                base_x - 1)

        self.assertEqual(spit_up.cleanup_postimage(1)[0x1C:0x1E],
                         bytes.fromhex('4a1e'))
        self.assertEqual(spit_up.cleanup_postimage(2), spit_up.CLEANUP_AFTER)
        self.assertEqual(spit_up.cleanup_postimage(3)[0x1C:0x1E],
                         bytes.fromhex('ca1e'))
        with self.assertRaisesRegex(ValueError, 'cleanup delta'):
            spit_up.cleanup_postimage(0)

    def test_logical_patcher_is_fail_closed_for_foreign_or_already_fixed_images(self):
        with self.assertRaisesRegex(ValueError, 'overlay size'):
            spit_up.patch_overlay(b'')
        foreign = bytearray(spit_up.OVERLAY_SIZE)
        foreign[spit_up.CLEANUP_OFFSET:
                spit_up.CLEANUP_OFFSET + spit_up.CLEANUP_SIZE] = spit_up.CLEANUP_BEFORE
        with self.assertRaisesRegex(ValueError, 'overlay preimage hash'):
            spit_up.patch_overlay(bytes(foreign))


if __name__ == '__main__':
    unittest.main()
