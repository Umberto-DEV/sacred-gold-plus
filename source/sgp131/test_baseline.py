import hashlib
import unittest
from unittest.mock import patch
from . import baseline

EN = b'EN synthetic baseline'
IT = b'IT synthetic baseline'
PINS = {hashlib.sha256(EN).hexdigest(): 'EN', hashlib.sha256(IT).hexdigest(): 'IT'}


class BaselineTests(unittest.TestCase):
    def test_exact_legacy_pins(self):
        self.assertEqual(baseline.INPUT_HASHES, {
            '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90': 'EN',
            '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156': 'IT'})

    def test_exact_identity_and_rejects_near_match(self):
        with patch.dict(baseline.INPUT_HASHES, PINS, clear=True):
            self.assertEqual(baseline.identify(EN), 'EN')
            self.assertEqual(baseline.identify(IT), 'IT')
            with self.assertRaisesRegex(ValueError, 'exact supported'):
                baseline.identify(EN + b'!')
