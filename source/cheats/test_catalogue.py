import unittest
from catalogue import remove_obsolete_overlay_patch, OBSOLETE_OVERLAY_PATCH
import xml.etree.ElementTree as ET


class CatalogueTest(unittest.TestCase):
    def test_removes_only_the_exact_incompatible_patch(self):
        text = ('<codelist><game><folder><name>01 - compatibility</name>'
                '<cheat><name>old</name><codes>' + OBSOLETE_OVERLAY_PATCH + '</codes></cheat>'
                '<cheat><name>other</name><codes>520DDDC8 1AFFFFFC</codes></cheat>'
                '</folder></game></codelist>')
        result = remove_obsolete_overlay_patch(text)
        self.assertEqual(ET.fromstring(result).findtext('game/folder/cheat/name'), 'other')
        self.assertEqual(len(ET.fromstring(result).findall('game/folder/cheat')), 1)
        self.assertEqual(result, remove_obsolete_overlay_patch(result))
