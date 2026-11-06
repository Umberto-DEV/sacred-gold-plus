"""Class B: complete title-only byte preservation on both canonical inputs."""
import os
from pathlib import Path
import unittest
from . import baseline, identity
from sgp12 import titolo_versione as container

class IdentityCartridges(unittest.TestCase):
    def test_only_label_changes_and_mutated_complement_is_refused(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                path = os.environ.get('SGP131_BASE_' + language)
                if not path:
                    if os.environ.get('SGP131_REQUIRE_INPUTS') == '1':
                        self.fail('missing canonical V4 ' + language)
                    self.skipTest('canonical V4 inputs required')
                before = Path(path).read_bytes()
                self.assertEqual(baseline.identify(before), language)
                after, receipt = identity.apply(before, language)
                at = container.membri(before)[15][0] + 848
                self.assertEqual(after[:at], before[:at])
                self.assertEqual(after[at + 384:], before[at + 384:])
                self.assertEqual(identity.verify(before, after, receipt)['label'], 'V1.3.1')
                corrupted = bytearray(after)
                corrupted[at - 1] ^= 1
                with self.assertRaises(ValueError):
                    identity.verify(before, bytes(corrupted), receipt)
                with self.assertRaises(ValueError):
                    identity.apply(after, language)

if __name__ == '__main__':
    unittest.main()
