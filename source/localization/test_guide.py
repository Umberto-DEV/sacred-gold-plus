"""Evolution localization preserves native conditions and parameter meaning."""
import unittest
from . import guide


class EvolutionTextTests(unittest.TestCase):
    def test_held_item_trade_uses_the_requested_item(self):
        calls = []
        def names(kind, number):
            calls.append((kind, number))
            return 'Testitem'
        self.assertEqual(guide.evolution_description(6, 55, names, 'DE'),
                         'Mit getragenem Item Testitem tauschen.')
        self.assertEqual(calls, [('item', 55)])

    def test_zero_beauty_parameter_is_plain_level_up(self):
        names = lambda kind, number: 'X'
        self.assertEqual(guide.evolution_description(15, 0, names, 'FR'), 'Monter de niveau.')
        self.assertIn('170', guide.evolution_description(15, 170, names, 'FR'))

    def test_unknown_evolution_method_cannot_be_described_as_level_up(self):
        with self.assertRaisesRegex(ValueError, 'method'):
            guide.evolution_description(99, 5, lambda *args: 'X', 'ES')


if __name__ == '__main__':
    unittest.main()
