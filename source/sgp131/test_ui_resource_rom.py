"""Class B: canonical EN/IT inputs read in place; replacement NARC stays in RAM.

Use SGP131_BASE_EN/IT (or SGP_UI_RESOURCE_EN/IT). Missing inputs give one named
skip per language; SGP_UI_RESOURCE_REQUIRE_INPUTS=1 makes them failures. No
ROM, extracted asset, decoded name, workbench slot or candidate is written.
The small encoded labels below are original test strings, not final UI copy.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from . import ui_resource as compiler, ui_resource_verify as readback


PINS = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}
OWNED_LABELS = {1: (43, 44, 45, 65535), 7: (46, 0xE000, 47, 48, 65535)}


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


class RealResourceTests(unittest.TestCase):
    def _language(self, language):
        configured = os.environ.get('SGP_UI_RESOURCE_' + language) or os.environ.get('SGP131_BASE_' + language)
        if not configured:
            message = 'SGP_UI_RESOURCE_' + language + ' / SGP131_BASE_' + language + ' missing for canonical resource test'
            if os.environ.get('SGP_UI_RESOURCE_REQUIRE_INPUTS') == '1':
                self.fail(message)
            self.skipTest(message)
        path = Path(configured)
        self.assertTrue(path.is_file())
        before = file_digest(path)
        self.assertEqual((before, path.stat().st_size), PINS[language])
        v4 = path.read_bytes()
        snapshots = {}
        try:
            with tempfile.TemporaryDirectory(prefix='sgp131-ui-resource-') as directory:
                for labels in ({}, OWNED_LABELS):
                    with self.subTest(language=language, authored_entries=len(labels)):
                        # Even a legitimate source may not open or write files inside the API.
                        with patch('builtins.open', side_effect=AssertionError('resource API file I/O')):
                            replacement, receipt = compiler.compile_resource(v4, labels)
                            verified = readback.verify_resource(v4, replacement, labels)
                        self.assertEqual(receipt, verified)
                        self.assertIsInstance(replacement, bytes)
                        self.assertEqual(receipt['source_sha256']['rom'], before)
                        self.assertEqual(receipt['species_entries'], 493)
                        self.assertEqual(receipt['species_text_bytes'], 8172)
                        self.assertEqual(receipt['text_directory_bytes'], 3944 + 8 * len(labels))
                        self.assertEqual(receipt['asset_sha256'], '96490ff4d596a9c21f4a8d8ac7a42a4c7c57834bbfbcd8a7ef0b2a0aed14e102')
                        self.assertEqual(receipt['asset_crc32'], 0x0FB91FA3)
                        self.assertEqual(receipt['widths_crc32'], 0x885AB7FC)
                        self.assertEqual(receipt['member_bytes'], 60564 if not labels else 60600)
                        self.assertEqual(receipt['budget_remaining'], 9068 if not labels else 9032)
                        fields = struct.unpack('<16I', bytes.fromhex(receipt['config_hex']))
                        self.assertEqual(fields[9:12], (zlib.crc32(replacement[:468]), zlib.crc32(replacement[35380:]), 0x885AB7FC))
                        self.assertEqual(len(NARC(replacement).files), 52)
                        # Independent older text decoder: every species, with no text output.
                        source_rom = NintendoDSRom(v4)
                        bank = NARC(source_rom.files[source_rom.filenames.idOf('a/0/2/7')]).files[237]
                        spec = importlib.util.spec_from_file_location('ui_resource_audit_text', Path(__file__).parents[1] / 'quality-audit' / 'hgss_text.py')
                        audit = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(audit)
                        old_words = audit.read_bank_raw(bank)
                        member = replacement[35380:]
                        n = struct.unpack_from('<I', member, 100)[0]
                        entries = {k: (units, at) for k, units, at in
                                   (struct.unpack_from('<HHI', member, 48448 + i * 8) for i in range(n))}
                        for species in range(1, 494):
                            units, at = entries[4096 + species]
                            actual = struct.unpack_from('<%dH' % units, member, at)
                            self.assertEqual(actual, tuple(audit.unpack_name(old_words[species])[0]))
                        # Corruption retains the unchanged asset SHA and can have fresh CRC metadata.
                        units, at = entries[4097]
                        for offset, value in ((at, 1 if member[at:at + 2] != b'\x01\0' else 2),
                                              (12, 1 if language == 'EN' else 0)):
                            mutant = bytearray(replacement)
                            struct.pack_into('<H' if offset == at else '<I', mutant, 35380 + offset, value)
                            forged_crc = zlib.crc32(mutant[35380:])
                            forged_config = list(fields)
                            forged_config[10] = forged_crc
                            self.assertEqual(struct.unpack('<16I', struct.pack('<16I', *forged_config))[10], forged_crc)
                            with self.assertRaises(ValueError):
                                readback.verify_resource(v4, bytes(mutant), labels)
                        if labels:
                            _, text_at = entries[1]
                            mutant = bytearray(replacement)
                            struct.pack_into('<H', mutant, 35380 + text_at, 44)
                            with self.assertRaisesRegex(ValueError, 'text differs'):
                                readback.verify_resource(v4, bytes(mutant), labels)
                        snapshots[str(len(labels))] = receipt
                        self.assertEqual(list(Path(directory).iterdir()), [])
                # Test the private source validation independently of the whole-ROM gate.
                # Mutating each actual source file must fail its own source pin in both implementations.
                fat_at = struct.unpack_from('<I', v4, 0x48)[0]
                for source_id in (167, 145, 156):
                    source_start = struct.unpack_from('<I', v4, fat_at + source_id * 8)[0]
                    foreign = bytearray(v4)
                    # Inside the bank payload rather than the NARC structure for messages.
                    at = source_start + (len(source_rom.files[156]) - 4 if source_id == 156 else 48)
                    if source_id == 156:
                        # Locate bank237 precisely so its independent identity pin rejects it.
                        archive = v4[source_start:struct.unpack_from('<I', v4, fat_at + source_id * 8 + 4)[0]]
                        table_size = struct.unpack_from('<I', archive, 20)[0]
                        names_start = 16 + table_size
                        names_size = struct.unpack_from('<I', archive, names_start + 4)[0]
                        image_base = names_start + names_size + 8
                        bank_at = struct.unpack_from('<I', archive, 28 + 237 * 8)[0]
                        at = source_start + image_base + bank_at + 4000
                    foreign[at] ^= 1
                    with self.subTest(source_id=source_id):
                        with self.assertRaisesRegex(ValueError, 'source'):
                            compiler._source(bytes(foreign), language)
                        with self.assertRaisesRegex(ValueError, 'source'):
                            readback._read_canonical(bytes(foreign), language)
                other_language = 'IT' if language == 'EN' else 'EN'
                with self.assertRaisesRegex(ValueError, 'source font'):
                    compiler._source(v4, other_language)
                with self.assertRaisesRegex(ValueError, 'source font'):
                    readback._read_canonical(v4, other_language)
                for index in (0, 0x1000, len(v4) - 1):
                    foreign = bytearray(v4)
                    foreign[index] ^= 1
                    with self.assertRaisesRegex(ValueError, 'exact supported'):
                        compiler.compile_resource(bytes(foreign), OWNED_LABELS)
                    with self.assertRaisesRegex(ValueError, 'exact supported'):
                        readback.verify_resource(bytes(foreign), replacement, OWNED_LABELS)
                self.assertEqual(hashlib.sha256(v4).hexdigest(), before)
        finally:
            self.assertEqual(file_digest(path), before, 'original canonical ROM changed')
        print(json.dumps({'language': language, 'input_sha256': before, 'input_bytes': len(v4),
                          'input_unchanged': True, 'output_files': 0, 'scratch_empty': True,
                          'receipts': snapshots}, sort_keys=True))

    def test_en_canonical_resource_readback(self):
        self._language('EN')

    def test_it_canonical_resource_readback(self):
        self._language('IT')
