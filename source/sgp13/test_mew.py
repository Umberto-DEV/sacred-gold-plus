"""Synthetic script relocation and guarded external metadata, without game bytes."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from sgp13 import mew
from sgp13.build import source_snapshot


class Relocation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Only the commands used by this hand-written fixture have semantics.
        # The real public decoder consumes this synthetic metadata table.
        rows = [{'name': 'Unused', 'args': [], 'is_abs_branch': True} for _ in range(853)]
        for op, name, args, stop in (
            (0, 'Nop', [], False), (2, 'End', [], True),
            (22, 'GoTo', ['addr'], True), (26, 'Call', ['script'], False),
            (31, 'ClearFlag', ['flag'], False),
            (94, 'ApplyMovement', ['object2', 'movement'], False),
            (95, 'WaitMovement', [], False), (97, 'ReleaseAll', [], False)):
            rows[op] = {'name': name, 'args': args, 'is_abs_branch': stop}
        path = Path(self.temp.name) / 'commands.json'
        path.write_text(json.dumps({'commands': rows}))
        self.commands = mew.decoder().Comandi(path)

    def fixture(self):
        # Entries10 and36. Forward Call→36, backward Call→10; GoTo→34.
        # Movements at54 and60; FE is deliberately only two bytes at EOF.
        return (struct.pack('<IIH', 6, 28, 0xFD13)
                + struct.pack('<HHI', 94, 13, 36)
                + struct.pack('<HH', 31, 0x3FC8)
                + struct.pack('<HI', 26, 8)
                + struct.pack('<HIH', 22, 0, 2)
                + struct.pack('<HHI', 94, 14, 16)
                + struct.pack('<HHIH', 97, 26, (-42) & 0xFFFFFFFF, 2)
                + struct.pack('<HHHH', 0x21, 1, 0xFE, 0xFE))

    def test_one_coordinate_transform_preserves_forward_backward_and_movement_targets(self):
        # Omitting an insertion from any relative displacement must fail.
        raw = self.fixture()
        result = mew.insert_waits(raw, self.commands, (18, 44))
        self.assertEqual(len(result), 66)
        parsed = mew.decoder().Membro(0, result, self.commands).cammina()
        self.assertEqual(parsed.errori, [])
        self.assertEqual(parsed.entry, [10, 38])
        self.assertEqual(struct.unpack_from('<H', result, 18)[0], 95)
        self.assertEqual(struct.unpack_from('<H', result, 46)[0], 95)
        self.assertEqual(parsed.istruzioni[24].rami, [(0, 38, 'script')])
        self.assertEqual(parsed.istruzioni[50].rami, [(0, 10, 'script')])
        self.assertEqual(parsed.istruzioni[30].rami, [(0, 36, 'addr')])
        self.assertEqual(parsed.istruzioni[10].rami, [(1, 58, 'movement')])
        self.assertEqual(parsed.istruzioni[38].rami, [(1, 64, 'movement')])
        self.assertEqual(result[58:], raw[54:])
        self.assertEqual(parsed.istruzioni[20].args, [0x3FC8])
        self.assertEqual(parsed.istruzioni[48].nome, 'ReleaseAll')
        self.assertEqual(parsed.riassembla(), (True, None))

    def test_two_byte_movement_terminator_at_end_is_preserved(self):
        raw = self.fixture()
        result = mew.insert_waits(raw, self.commands, (18, 44))
        self.assertEqual(result[-2:], b'\xfe\0')
        self.assertEqual(result[58:64], b'\x21\0\x01\0\xfe\0')

    def test_missing_or_truncated_movement_terminator_is_rejected(self):
        raw = self.fixture()
        for malformed in (raw[:-1], raw[:-2], raw[:-2] + b'\x21\0'):
            with self.subTest(length=len(malformed)):
                with self.assertRaisesRegex(ValueError, 'movement'):
                    mew.insert_waits(malformed, self.commands, (18, 44))

    def test_invalid_insertion_or_duplicate_site_is_rejected(self):
        for sites in ((), (18, 18), (44, 18), (19,), (10,), (34,)):
            with self.subTest(sites=sites):
                with self.assertRaises(ValueError):
                    mew.insert_waits(self.fixture(), self.commands, sites)

    def test_bad_header_opcode_and_relative_target_are_rejected(self):
        raw = self.fixture()
        variants = [b'\xff' * 4 + raw[4:], raw[:10] + b'\xff\xff' + raw[12:]]
        invalid = bytearray(raw)
        struct.pack_into('<I', invalid, 24, 0x7FFFFFFF)
        variants.append(bytes(invalid))
        for malformed in variants:
            with self.subTest(prefix=malformed[:12]):
                with self.assertRaises(ValueError):
                    mew.insert_waits(malformed, self.commands, (18, 44))

    def test_foreign_member_or_language_never_reaches_relocation(self):
        for language in ('EN', 'IT', 'FR'):
            with self.subTest(language=language):
                with self.assertRaisesRegex(ValueError, 'preimage|language'):
                    mew.patch_member(self.fixture(), language, self.commands)


class Metadata(unittest.TestCase):
    def test_missing_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(FileNotFoundError, 'scrcmd'):
                mew.load_commands(Path(d) / 'scrcmd.json')

    def test_foreign_metadata_is_rejected_before_decoding(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'scrcmd.json'
            path.write_text('{"commands": []}')
            with self.assertRaisesRegex(ValueError, 'metadata SHA-256'):
                mew.load_commands(path)

    def test_effective_decoder_is_part_of_build_source_snapshot(self):
        snapshot = source_snapshot()
        path = Path(__file__).resolve().parents[1] / 'features/borsa/tools/scr_disasm.py'
        self.assertEqual(snapshot['features/borsa/tools/scr_disasm.py'],
                         hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
