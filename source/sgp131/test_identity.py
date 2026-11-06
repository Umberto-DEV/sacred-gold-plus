"""ROM-free contract for the final project-owned version label."""
import hashlib
import unittest
from . import identity, mechanics_stages as ms

class FinalIdentity(unittest.TestCase):
    def test_final_title_is_a_registered_stage(self):
        self.assertIn('identity', ms.IMPLEMENTED)
        self.assertEqual(ms.ORDER[-1], 'identity')

    def test_reviewed_label_fits_existing_tiles(self):
        self.assertEqual(identity.LABEL, 'V1.3.1')
        self.assertEqual(len(identity.pixels()), 384)
        self.assertEqual(hashlib.sha256(identity.pixels()).hexdigest(),
                         '060f3451ec15a1fbccedef6cc5577a1a1f466e337c4b3e94181d3d4d97fed450')
        self.assertTrue(all((b & 15) in (0, 4, 14) and b >> 4 in (0, 4, 14) for b in identity.pixels()))

if __name__ == '__main__':
    unittest.main()
