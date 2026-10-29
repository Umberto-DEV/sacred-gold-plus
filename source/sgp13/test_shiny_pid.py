"""Synthetic PID contracts; no cartridge, save, native RNG or game data."""
import unittest

from sgp13.shiny_pid import is_shiny, transform_pid


class ClassifierTests(unittest.TestCase):
    def test_legacy_classifier_keeps_saved_xor_8_through_254_shiny(self):
        # Restoring the retail threshold would silently deshiny old specimens.
        for value, expected in ((0, True), (7, True), (8, True), (254, True),
                                (255, False), (256, False), (65535, False)):
            with self.subTest(xor=value):
                self.assertIs(is_shiny(value << 16, 0), expected)

    def test_final_ot_and_both_pid_halves_participate_in_classification(self):
        for value, expected in ((7, True), (254, True), (255, False)):
            pid = ((0xa55a ^ 0x1234 ^ value) << 16) | 0x1234
            self.assertIs(is_shiny(pid, 0xa55a), expected)


class TransformTests(unittest.TestCase):
    def test_full_width_pid_inputs_preserve_invariants(self):
        for pid in (0, 0xffffffff, 0x80000000, 0x12345678, 0xffff00ff):
            for ot_fold in (0, 0xffff, 0x8000, 0x1234):
                for outcome in (False, True):
                    result = transform_pid(pid, ot_fold, shiny=outcome, seed=1535)
                    self.assertEqual(result % 25, pid % 25)
                    self.assertEqual(result & 255, pid & 255)
                    xor = (result >> 16) ^ (result & 65535) ^ ot_fold
                    self.assertTrue(xor < 8 if outcome else xor >= 255)
                    self.assertGreaterEqual(result, 0)
                    self.assertLessEqual(result, 0xffffffff)

    def test_nonshiny_correction_handles_both_ends_without_changing_high_half(self):
        # Adding 25 unconditionally would overflow at the upper byte boundary.
        for x in range(256):
            for low_byte in (0, 1, 127, 255):
                for ot_fold in (0, 255, 0x1234, 65535):
                    for value in (0, 7, 8, 254):
                        low = (x << 8) | low_byte
                        pid = ((ot_fold ^ low ^ value) << 16) | low
                        result = transform_pid(pid, ot_fold, shiny=False, seed=0)
                        observed_xor = (result >> 16) ^ (result & 65535) ^ ot_fold
                        self.assertGreaterEqual(observed_xor, 255)
                        self.assertEqual(result >> 16, pid >> 16)
                        self.assertEqual(result & 255, low_byte)
                        self.assertEqual(result % 25, pid % 25)
                        self.assertEqual(abs(result - pid), 6400)

    def test_existing_nonshiny_candidate_is_unchanged(self):
        for value in (255, 256, 65535):
            pid = ((0x1234 ^ 0xabcd ^ value) << 16) | 0xabcd
            for seed in (0, 2047):
                self.assertEqual(transform_pid(pid, 0x1234, shiny=False, seed=seed), pid)

    def test_selected_shiny_preserves_nature_and_every_gender_ability_threshold(self):
        # Full low-byte equality covers all native ratios, not one assumed sex.
        for low_byte in (0, 1, 30, 31, 62, 63, 126, 127, 190, 191, 253, 254, 255):
            for nature in range(25):
                # 21 is the inverse of 256 modulo 25.
                pid = low_byte + 256 * ((nature - low_byte) * 21 % 25)
                for ot_fold in (0, 1, 255, 0x1234, 65535):
                    for seed in (0, 1024, 2047):
                        result = transform_pid(pid, ot_fold, shiny=True, seed=seed)
                        self.assertEqual(result & 255, low_byte)
                        self.assertEqual(result % 25, nature)
                        self.assertLess((result >> 16) ^ (result & 65535) ^ ot_fold, 8)
                        self.assertGreaterEqual(result, 0)
                        self.assertLessEqual(result, 0xffffffff)

    def test_search_wraps_and_accepts_the_157th_candidate(self):
        self.assertEqual(transform_pid(1, 0, shiny=True, seed=2047), 1)
        # Independent reduced-domain witness: indices 562..717 fail, 718 passes.
        self.assertEqual(transform_pid(0, 0x1200, shiny=True, seed=562), 0x4b065900)

    def test_wurmple_future_branch_follows_final_pid_and_preserves_actual_ability(self):
        # For OT fold FFFF, nature 12 + even parity forces shiny high%10 >= 5.
        # The original uncreated Cute Charm candidate would evolve the other way.
        result = transform_pid(12, 65535, shiny=True, seed=0)
        self.assertEqual(result % 25, 12)
        self.assertEqual(result & 255, 12)
        self.assertGreaterEqual((result >> 16) % 10, 5)
        self.assertLess((result >> 16) ^ (result & 65535) ^ 65535, 8)

    def test_every_reduced_class_has_a_match_within_157_probes_from_any_start(self):
        largest_gap = 0
        for ot_high in range(256):
            positions = [[] for _ in range(25)]
            for index in range(2048):
                x, s = divmod(index, 8)
                # Algebraic residue proof, independent of the production PID builder.
                residue = (6 * x + 16 * (x ^ ot_high) + 11 * s) % 25
                positions[residue].append(index)
            for nature, matches in enumerate(positions):
                self.assertTrue(matches, (ot_high, nature))
                gaps = [(end - start, start, end)
                        for start, end in zip(matches, matches[1:] + [matches[0] + 2048])]
                gap, before, expected = max(gaps)
                largest_gap = max(largest_gap, gap)
                self.assertLessEqual(gap, 157, (ot_high, nature))
                # Exercise the implementation at every reduced class's worst start.
                pid = 256 * (nature * 21 % 25)
                result = transform_pid(pid, ot_high << 8, shiny=True, seed=(before + 1) % 2048)
                actual_index = ((result >> 8) & 255) * 8 + ((result >> 16) & 7)
                self.assertEqual(actual_index, expected % 2048)
                self.assertEqual(result % 25, nature)
                self.assertEqual(result & 255, 0)
        self.assertEqual(largest_gap, 157)


class InputContractTests(unittest.TestCase):
    def test_pid_and_fold_must_be_unsigned_values_of_the_documented_width(self):
        for args in ((-1, 0), (1 << 32, 0), (True, 0), (1.0, 0),
                     (0, -1), (0, 1 << 16), (0, False), (0, '123')):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    is_shiny(*args)
                for outcome in (False, True):
                    with self.assertRaises(ValueError):
                        transform_pid(*args, shiny=outcome, seed=0)

    def test_lottery_outcome_is_boolean_and_seed_is_an_explicit_valid_offset(self):
        for outcome in (None, 0, 1, 'shiny'):
            with self.subTest(outcome=outcome), self.assertRaises(ValueError):
                transform_pid(0, 0, shiny=outcome, seed=0)
        for seed in (-1, 2048, True, 0.5, None):
            for outcome in (False, True):
                with self.subTest(seed=seed, outcome=outcome), self.assertRaises(ValueError):
                    transform_pid(0, 0, shiny=outcome, seed=seed)


if __name__ == '__main__':
    unittest.main()
