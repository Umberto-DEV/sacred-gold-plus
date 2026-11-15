"""ROM-free contract for the final project-owned version label."""
import hashlib
import unittest
from . import identity, mechanics_stages as ms

class FinalIdentity(unittest.TestCase):
    def test_final_title_is_a_registered_stage(self):
        self.assertIn('identity', ms.IMPLEMENTED)
        self.assertEqual(ms.ORDER[-1], 'identity')

    def test_reviewed_label_fits_existing_tiles(self):
        self.assertEqual(identity.LABEL, 'V1.3.3')
        self.assertEqual(len(identity.pixels()), 384)
        self.assertEqual(hashlib.sha256(identity.pixels()).hexdigest(),
                         '8dc3639ecb62410ba1af62370e8632df298f328f1b48ffbcd9124a70bff7ea1b')
        self.assertTrue(all((b & 15) in (0, 4, 14) and b >> 4 in (0, 4, 14) for b in identity.pixels()))

if __name__ == '__main__':
    unittest.main()
