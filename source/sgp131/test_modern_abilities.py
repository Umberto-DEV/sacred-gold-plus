"""Class A: Keen Eye stage contracts without game data.

The compiler test needs the pinned clang; without it the test skips, and
SGP_CI=1 turns that skip into a failure as in the rest of the Class A runner.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from sgp12.rom import bl_decode
from sgp131 import modern_abilities as stage

ADDRESSES = (0x023DF000, 0x02390000, 0x023C8000)


class SeamEncoding(unittest.TestCase):
    def test_seam_targets_slot_and_compares_one(self):
        for address in ADDRESSES:
            seam = stage.seam_bytes(address)
            self.assertEqual(len(seam), 6)
            self.assertEqual(bl_decode(stage.SITE, seam[:4]), address)
            self.assertEqual(seam[4:], b'\x01\x28')  # CMP r0, #1

    def test_misaligned_and_out_of_range_addresses_refused(self):
        for address in (0x023DF002, 0x023DF001, 0x01FF8000, 0x02400000, 0x02700000, -4, '0x023DF000'):
            with self.assertRaises(ValueError):
                stage.seam_bytes(address)

    def test_patch_refuses_foreign_or_truncated_image(self):
        with self.assertRaises(ValueError):
            stage.patch_overlay(bytes(0x1000), ADDRESSES[0])
        with self.assertRaises(ValueError):
            stage.patch_overlay(bytes(0x37380), ADDRESSES[0])


class Admission(unittest.TestCase):
    def test_apply_refuses_without_assigned_slot(self):
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'reserve slot'):
                stage.apply(b'', 'EN', Path(work))
            with self.assertRaisesRegex(ValueError, 'reserve slot'):
                stage.apply(b'', 'EN', Path(work), slot={'start': ADDRESSES[0]})

    def test_apply_refuses_unknown_language_and_bad_slots(self):
        good = {'name': 'modern-accuracy.code', 'start': ADDRESSES[0], 'bytes': 32,
                'preimage_sha256': '0' * 64}
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'language'):
                stage.apply(b'', 'FR', Path(work), slot=good, charmap='x')
            for bad in (dict(good, start=good['start'] + 2), dict(good, bytes=0), dict(good, name=''),
                        dict(good, start=0x02800000)):
                with self.assertRaises(ValueError):
                    stage.apply(b'', 'EN', Path(work), slot=bad, charmap='x')


class Compiler(unittest.TestCase):
    def setUp(self):
        if shutil.which('clang') is None:
            if os.environ.get('SGP_CI') == '1':
                self.fail('clang required under SGP_CI=1')
            self.skipTest('clang unavailable')

    def test_payload_pinned_position_independent_and_within_budget(self):
        with tempfile.TemporaryDirectory() as work:
            payloads = [stage.compile_native(Path(work), address) for address in ADDRESSES]
            self.assertEqual(os.listdir(work), [], 'compiler scratch removed')
        for (payload, receipt), address in zip(payloads, ADDRESSES):
            self.assertEqual(payload, payloads[0][0])
            self.assertLessEqual(len(payload), stage.PAYLOAD_BUDGET)
            self.assertEqual(receipt['entry'], address | 1)
            self.assertLessEqual(receipt['stack_bytes'], 8)
            self.assertEqual(stage._payload_semantics(payload), {'getter_calls': 1, 'abilities': [51, 109]})

    def test_semantic_reader_rejects_altered_payload(self):
        with tempfile.TemporaryDirectory() as work:
            payload, _ = stage.compile_native(Path(work), ADDRESSES[0])
        no_keen_eye = payload.replace(bytes([0x33, 0x38]), bytes([0x34, 0x38]))
        self.assertNotEqual(no_keen_eye, payload)
        wrong_getter = payload[:-4] + (stage.GETTER + 5).to_bytes(4, 'little')
        for altered in (no_keen_eye, wrong_getter):
            with self.assertRaises(ValueError):
                stage._payload_semantics(altered)


if __name__ == '__main__':
    unittest.main()
