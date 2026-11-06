"""SG-BAG-FOREIGN successor-stage contracts."""
import tempfile
import unittest
from pathlib import Path

from sgp12.rom import Arm9

from . import bag_foreign as B
from .test_legacy_scripts import inputs


class BagForeignStage(unittest.TestCase):
    def test_compiler_keeps_save_entry_and_exact_compartment(self):
        with tempfile.TemporaryDirectory(prefix='bag-foreign-test-') as work:
            installed, report = B.compile_successor(Path(work))
        self.assertEqual(len(installed), B.CAPACITY)
        self.assertEqual(report['bytes'], B.PAYLOAD_BYTES)
        self.assertEqual(report['payload_sha256'], B.PAYLOAD_SHA256)
        self.assertEqual(report['installed_sha256'], B.POSTIMAGE_SHA256)
        self.assertEqual(report['training_save'], B.TRAINING_SAVE)
        self.assertEqual(report['training_native_save'], B.TRAINING_NATIVE_SAVE)
        self.assertEqual(report['training_shiny_bind'], B.TRAINING_SHINY_BIND)
        self.assertEqual(report['training_shiny_access'], B.TRAINING_SHINY_ACCESS)
        self.assertEqual(report['storage_ready'], B.STORAGE_READY)
        self.assertEqual(report['entry_patch'], B.ENTRY_PATCH.hex())
        self.assertTrue(report['public_abi_preserved'])

    def test_en_it_replace_only_training_code_and_replay(self):
        for language in B.LANGUAGES:
            before = inputs(language)[0]
            with tempfile.TemporaryDirectory(prefix='bag-foreign-test-') as work:
                after, receipt = B.apply(before, language, work_dir=Path(work))
            with self.subTest(language=language):
                self.assertEqual(len(after), len(before))
                self.assertTrue(B.verify(before, after, receipt)['ok'])
                old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
                self.assertEqual(old.leggi(B.HOOK, len(B.HOOK_BYTES)),
                                 new.leggi(B.HOOK, len(B.HOOK_BYTES)))
                at = old.off(B.BASE, B.CAPACITY)
                restored = bytearray(after)
                restored[at:at + B.CAPACITY] = before[at:at + B.CAPACITY]
                self.assertEqual(bytes(restored), before)

    def test_preimage_output_and_receipt_mutants_fail_closed(self):
        before = inputs('EN')[0]
        damaged = bytearray(before)
        at = Arm9.from_bytes(before).off(B.BASE, 1)
        damaged[at] ^= 1
        with tempfile.TemporaryDirectory(prefix='bag-foreign-test-') as work:
            with self.assertRaisesRegex(ValueError, 'preimage'):
                B.apply(bytes(damaged), 'EN', work_dir=Path(work))
            after, receipt = B.apply(before, 'EN', work_dir=Path(work))
        damaged = bytearray(after)
        damaged[0] ^= 1
        with self.assertRaisesRegex(ValueError, 'outside'):
            B.verify(before, bytes(damaged), receipt)
        forged = dict(receipt, bag_blob_unchanged=False)
        with self.assertRaisesRegex(ValueError, 'receipt'):
            B.verify(before, after, forged)


if __name__ == '__main__':
    unittest.main()
