"""Catalogue migration and generated Action Replay contract, without a ROM."""
import unittest
import xml.etree.ElementTree as ET
from selector import update_catalogue, selector_code, LEGACY_SPECIES_CODES


class SelectorTest(unittest.TestCase):
    def test_replaces_classic_folder_preserving_other_codes_and_identity(self):
        source = '<codelist><game><gameid>IPKE 19D1EEBB</gameid><folder><name>40 - old</name><cheat><name>old</name><codes>94000130 FCFF0000</codes></cheat></folder><folder><name>49 - levels</name><cheat><name>level</name><codes>other code</codes></cheat></folder></game></codelist>'
        source = source.replace('94000130 FCFF0000', sorted(LEGACY_SPECIES_CODES)[0])
        source = source.replace('</cheat></folder><folder>', '</cheat><cheat><name>Maximum IVs</name><codes>1206E012 0000201F</codes></cheat></folder><folder>')
        result = update_catalogue(source, 'EN')
        root = ET.fromstring(result)
        self.assertEqual(root.findtext('game/gameid'), 'IPKE 19D1EEBB')
        self.assertEqual(len(root.findall('game/folder')), 2)
        self.assertEqual(root.findall('game/folder')[1].findtext('cheat/codes'), 'other code')
        self.assertEqual(update_catalogue(result, 'EN'), result)
        code = root.findtext('game/folder/cheat/codes')
        self.assertEqual(code, selector_code(25, 5))
        self.assertNotIn('<enabled', result)
        self.assertEqual(root.findall('game/folder')[0].findall('cheat')[1].findtext('codes'), '1206E012 0000201F')

    def test_code_contract(self):
        for species in range(1, 494):
            for level in (1, 100):
                code = selector_code(species, level)
                self.assertEqual(len(code.split()), 28)
                self.assertEqual(code.count('52246C94 28038800'), 2)
                self.assertNotIn('0000DCF', code)
        for species, level in ((0, 5), (494, 5), (25, 0), (25, 101)):
            with self.assertRaises(ValueError):
                selector_code(species, level)

    def test_rejects_wrong_game_and_ambiguous_catalogue(self):
        with self.assertRaises(ValueError):
            update_catalogue('<codelist><game><gameid>NOPE 00000000</gameid></game></codelist>', 'IT')


if __name__ == '__main__':
    unittest.main()
