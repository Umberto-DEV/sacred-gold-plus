import hashlib
import unittest

from ndspy import lz10
from ui_resource import normalize_donor


class UIResourceTests(unittest.TestCase):
    def setUp(self):
        self.original = b'RCSN' + bytes(60)
        self.translated = b'RCSN' + bytes(50) + b'1234567890'
        self.packed = lz10.compress(self.translated)
        self.transform = {'kind': 'lz10-decompress', 'after_sha256': hashlib.sha256(self.translated).hexdigest()}

    def test_compatible_uncompressed_resource(self):
        self.assertEqual(normalize_donor(self.original, self.translated), self.translated)

    def test_unreviewed_storage_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_donor(self.original, self.packed)

    def test_explicit_decompression_retains_uncompressed_loader_contract(self):
        self.assertEqual(normalize_donor(self.original, self.packed, self.transform), self.translated)

    def test_transform_hash_and_storage_guards(self):
        for source, donor, spec in [(self.packed, self.packed, self.transform),
                                    (self.original, self.translated, self.transform),
                                    (self.original, self.packed, {'kind': 'lz10-decompress', 'after_sha256': '0' * 64})]:
            with self.assertRaises(ValueError):
                normalize_donor(source, donor, spec)

    def test_resource_type_cannot_change_silently(self):
        with self.assertRaises(ValueError):
            normalize_donor(self.original, b'RGCN' + bytes(60))
        with self.assertRaises(ValueError):
            normalize_donor(lz10.compress(self.original), lz10.compress(b'RGCN' + bytes(60)))


if __name__ == '__main__':
    unittest.main()
