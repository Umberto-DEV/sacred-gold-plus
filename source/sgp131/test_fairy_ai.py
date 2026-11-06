"""Class A contracts for the SG-AI01 resident Fairy helper."""
import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from sgp12.rom import bl_decode
from sgp131 import fairy_ai as stage


ADDRESSES = (0x023D746C, 0x023D0000, 0x023DF000)


def synthetic_overlay():
    image = bytearray(stage.OVERLAY_SIZE)
    for address, context in stage.CONTEXTS:
        offset = address - stage.OVERLAY_BASE
        image[offset:offset + len(context)] = context
    return bytes(image)


class SeamEncoding(unittest.TestCase):
    def test_both_seams_target_their_distinct_entries(self):
        for address in ADDRESSES:
            seams = stage.seam_bytes(address)
            self.assertEqual(set(seams), {stage.FLAGS_SITE, stage.SCALAR_SITE})
            self.assertEqual(bl_decode(stage.FLAGS_SITE, seams[stage.FLAGS_SITE]), address)
            self.assertEqual(bl_decode(stage.SCALAR_SITE, seams[stage.SCALAR_SITE]),
                             address + stage.SCALAR_OFFSET)

    def test_addresses_outside_the_exact_geometry_are_refused(self):
        for address in (0x023D746E, 0x01FFFFFF, 0x02400000, -4, '0x023D746C'):
            with self.assertRaises(ValueError):
                stage.seam_bytes(address)

    def test_patch_changes_only_two_calls_and_the_loop_backedge(self):
        before = synthetic_overlay()
        after, receipt = stage.patch_overlay(before, ADDRESSES[0])
        changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
        declared = {address - stage.OVERLAY_BASE + i
                    for address in (stage.FLAGS_SITE, stage.SCALAR_SITE)
                    for i in range(4)}
        declared.add(0x02252138 - stage.OVERLAY_BASE)
        self.assertEqual(set(changed), declared)
        self.assertEqual(receipt['changed_offsets'], changed)
        branch = int.from_bytes(after[0x02252138 - stage.OVERLAY_BASE:
                                      0x0225213A - stage.OVERLAY_BASE], 'little')
        displacement = (branch & 255) - 256
        self.assertEqual(0x0225213C + 2 * displacement, 0x022520CC)
        for address, seam in stage.seam_bytes(ADDRESSES[0]).items():
            offset = address - stage.OVERLAY_BASE
            self.assertEqual(after[offset:offset + 4], seam)
        with self.assertRaises(ValueError):
            stage.patch_overlay(after, ADDRESSES[0])
        mutant = bytearray(before)
        mutant[stage.FLAGS_SITE - stage.OVERLAY_BASE - 1] ^= 1
        with self.assertRaises(ValueError):
            stage.patch_overlay(bytes(mutant), ADDRESSES[0])

    def test_changed_loop_tail_or_backedge_is_refused(self):
        before = synthetic_overlay()
        for address in (0x0225212E, 0x02252130, 0x02252132,
                        0x02252134, 0x02252136, 0x02252138):
            mutant = bytearray(before)
            mutant[address - stage.OVERLAY_BASE] ^= 1
            with self.subTest(address=hex(address)), self.assertRaises(ValueError):
                stage.patch_overlay(bytes(mutant), ADDRESSES[0])


class Admission(unittest.TestCase):
    def test_apply_refuses_without_exact_zero_preimage_slot(self):
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'reserve slot'):
                stage.apply_code(b'', 'EN', Path(work))
        good = stage.slot_contract(ADDRESSES[0], stage.PAYLOAD_BYTES)
        self.assertEqual(good['preimage_sha256'], hashlib.sha256(bytes(stage.PAYLOAD_BYTES)).hexdigest())
        for bad in (dict(good, name=''), dict(good, bytes=147),
                    dict(good, preimage_sha256='0' * 64), dict(good, start=good['start'] + 2)):
            with self.assertRaises(ValueError):
                stage._check_slot(bad)

    def test_unknown_language_refused_before_rom_parsing(self):
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'language'):
                stage.apply_code(b'', 'FR', Path(work),
                                 slot=stage.slot_contract(ADDRESSES[0], stage.PAYLOAD_BYTES))


class Compiler(unittest.TestCase):
    def setUp(self):
        if shutil.which('clang') is None:
            if os.environ.get('SGP_CI') == '1':
                self.fail('clang required under SGP_CI=1')
            self.skipTest('clang unavailable')

    def test_payload_is_exactly_148_bytes_at_the_fixed_slot(self):
        with tempfile.TemporaryDirectory() as work:
            payload, receipt = stage.compile_native(Path(work), stage.DEFAULT_SLOT)
            self.assertEqual(os.listdir(work), [])
        self.assertEqual(len(payload), stage.PAYLOAD_BYTES)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), stage.PAYLOAD_SHA256)
        self.assertEqual(receipt['entries']['flags'], stage.DEFAULT_SLOT | 1)
        self.assertEqual(receipt['entries']['scalar'],
                         stage.DEFAULT_SLOT + stage.SCALAR_OFFSET | 1)
        self.assertEqual(receipt['native_apply_targets'], [stage.NATIVE_APPLY] * 2)
        self.assertEqual(stage._payload_semantics(payload), {
            'bytes': 148, 'fairy_pairs': 12, 'native_apply_calls': 2,
            'entries': [0, stage.SCALAR_OFFSET],
        })
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'fixed slot'):
                stage.compile_native(Path(work), ADDRESSES[1])

    def test_payload_reader_rejects_table_and_call_mutants(self):
        with tempfile.TemporaryDirectory() as work:
            payload, receipt = stage.compile_native(Path(work), ADDRESSES[0])
        table = payload.index(stage.PACKED_CODES)
        wrong_table = bytearray(payload)
        wrong_table[table] ^= 1
        call = receipt['apply_call_offsets'][0]
        wrong_call = bytearray(payload)
        wrong_call[call] ^= 1
        for mutant in (bytes(wrong_table), bytes(wrong_call), payload[:-2]):
            with self.assertRaises(ValueError):
                stage._payload_semantics(mutant)


if __name__ == '__main__':
    unittest.main()
