"""Independent finite examples for probability calculations, without game data."""
from fractions import Fraction as F
from itertools import product
import unittest

from sgp13.balance_math import attack_distribution, encounter_cdf, ko_probability


class AttackDistributionTests(unittest.TestCase):
    def test_roll_multiplicity_is_preserved(self):
        # Deduplicating rolls would change the rare high roll from 1/16 to 1/2.
        result = attack_distribution([30] * 15 + [80], [160], F(1), F(0))
        self.assertEqual(result, {30: F(15, 16), 80: F(1, 16)})

    def test_misses_and_criticals_are_distinct_weighted_branches(self):
        result = attack_distribution([20, 30], [40, 60], F(9, 10), F(1, 16))
        self.assertEqual(result, {0: F(1, 10), 20: F(27, 64),
                                 30: F(27, 64), 40: F(9, 320), 60: F(9, 320)})
        self.assertEqual(sum(result.values()), 1)

    def test_immunity_and_miss_mass_coalesce(self):
        self.assertEqual(attack_distribution([0], [0], F(9, 10), F(1, 16)),
                         {0: F(1)})

    def test_invalid_rolls_and_probabilities_are_rejected(self):
        for rolls in ([], [-1], [1.5], [True]):
            with self.subTest(rolls=rolls), self.assertRaises(ValueError):
                attack_distribution(rolls, [2], F(1), F(0))
        for probability in (F(-1, 10), F(11, 10), 0.9, True):
            with self.subTest(probability=probability), self.assertRaises(ValueError):
                attack_distribution([1], [2], probability, F(0))


class KnockoutTests(unittest.TestCase):
    def test_exhaustive_weighted_sequences_with_one_use_healing(self):
        # Enumerate equally likely tickets, including two distinct miss tickets.
        # This oracle never merges states or calls attack_distribution.
        tickets = (0, 0, 2, 5, 8)
        distribution = {0: F(2, 5), 2: F(1, 5), 5: F(1, 5), 8: F(1, 5)}
        for hp, attempts, healing in product((3, 7, 9), range(1, 5), (0, 3)):
            for threshold in (hp // 2, hp):
                knocked_out = 0
                for sequence in product(tickets, repeat=attempts):
                    remaining, berry_used = hp, False
                    for damage in sequence:
                        if damage == 0:
                            continue
                        remaining -= damage
                        if remaining <= 0:
                            knocked_out += 1
                            break
                        if not berry_used and remaining <= threshold:
                            remaining = min(hp, remaining + healing)
                            berry_used = True
                with self.subTest(hp=hp, attempts=attempts, healing=healing,
                                  threshold=threshold):
                    self.assertEqual(ko_probability(distribution, hp, attempts,
                                                    berry_heal=healing,
                                                    berry_threshold=threshold),
                                     F(knocked_out, len(tickets) ** attempts))

    def test_two_required_hits_at_ninety_percent(self):
        self.assertEqual(ko_probability({0: F(1, 10), 60: F(9, 10)}, 100, 2),
                         F(81, 100))

    def test_three_attempts_match_binomial_probability_of_two_hits(self):
        # 3*p^2*(1-p) + p^3, independently derived from the binomial formula.
        self.assertEqual(ko_probability({0: F(1, 10), 60: F(9, 10)}, 100, 3),
                         F(243, 250))

    def test_one_use_berry_changes_two_hit_threshold(self):
        distribution = {0: F(1, 10), 60: F(9, 10)}
        self.assertEqual(ko_probability(distribution, 100, 2, berry_heal=25,
                                        berry_threshold=50), 0)
        self.assertEqual(ko_probability(distribution, 100, 3, berry_heal=25,
                                        berry_threshold=50), F(729, 1000))

    def test_lethal_hit_is_absorbing_and_cannot_trigger_healing(self):
        self.assertEqual(ko_probability({100: F(1)}, 100, 1, berry_heal=100,
                                        berry_threshold=50), 1)

    def test_berry_only_activates_once(self):
        # 100 -> 40 -> 100 -> 40 -> KO; a reusable berry blocks KO.
        self.assertEqual(ko_probability({60: F(1)}, 100, 3, berry_heal=100,
                                        berry_threshold=50), 1)

    def test_zero_damage_cannot_knock_out_or_consume_attemptless_probability(self):
        self.assertEqual(ko_probability({0: F(1)}, 100, 100), 0)
        self.assertEqual(ko_probability({100: F(1)}, 100, 0), 0)
        self.assertEqual(ko_probability({0: F(1)}, 0, 0), 1)

    def test_duplicate_roll_probability_changes_ko_probability(self):
        distribution = attack_distribution([30] * 15 + [80], [160], F(1), F(0))
        # Only two low rolls fail: 1 - (15/16)^2.
        self.assertEqual(ko_probability(distribution, 100, 2), F(31, 256))

    def test_invalid_inputs_are_not_silently_normalized(self):
        cases = [({}, 100, 1), ({1: F(1, 2)}, 100, 1),
                 ({-1: F(1)}, 100, 1), ({1: 0.5, 2: 0.5}, 100, 1),
                 ({1: F(1)}, -1, 1), ({1: F(1)}, 100, -1)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                ko_probability(*args)


class EncounterTests(unittest.TestCase):
    def test_independent_fixed_and_changing_probabilities(self):
        self.assertEqual(encounter_cdf([]), 0)
        self.assertEqual(encounter_cdf([F(1, 2), F(1, 4)]), F(5, 8))
        self.assertEqual(encounter_cdf([F(1, 512)] * 2), F(1023, 262144))
        self.assertEqual(encounter_cdf([F(0), F(1)]), 1)

    def test_invalid_later_probability_is_checked_even_after_certain_success(self):
        with self.assertRaises(ValueError):
            encounter_cdf([F(1), F(2)])


if __name__ == '__main__':
    unittest.main()
