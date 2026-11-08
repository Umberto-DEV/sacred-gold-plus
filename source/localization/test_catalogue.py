"""Localized footer segmentation must preserve native button meaning."""
import unittest
from . import catalogue


class FooterTests(unittest.TestCase):
    def test_translated_multiword_labels_keep_button_boundaries(self):
        text, runs = catalogue.footer_runs('Haut/Bas Déplacer A Choisir B Annuler', ('A', 'B'))
        self.assertEqual(text, 'Haut/Bas Déplacer  A Choisir  B Annuler')
        self.assertEqual(runs, [dict(key='', text='Haut/Bas Déplacer'),
                                dict(key='A', text='A'), dict(key='', text='Choisir'),
                                dict(key='B', text='B'), dict(key='', text='Annuler')])

    def test_changed_button_mapping_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'button'):
            catalogue.footer_runs('A Choisir X Annuler', ('A', 'B'))


if __name__ == '__main__':
    unittest.main()
