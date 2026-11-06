"""Class B: real EN/IT candidate ROMs, read and patched in memory only.

Inputs default to the balance493 candidates under local/experiments, relative to
the repository root. A missing input skips with a reason; with
SGP_MOVES_REQUIRE_INPUTS=1 it fails instead. A present input with the wrong
sha256 always fails. Nothing is written to disk.
"""
import hashlib
import os
import struct
import unittest
from pathlib import Path

import ndspy.rom

from sgp131 import modern_moves as moves

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / 'local' / 'experiments' / 'balance493-2026-10-28'
INPUTS = {
    'EN': (os.environ.get('SGP_MOVES_ROM_EN') or CANDIDATES / 'candidate-v4-EN.nds',
           '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
    'IT': (os.environ.get('SGP_MOVES_ROM_IT') or CANDIDATES / 'candidate-v4-IT.nds',
           '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'),
}
REQUIRE_INPUTS = os.environ.get('SGP_MOVES_REQUIRE_INPUTS') == '1'
ARCHIVE = 'a/0/1/1'
ARCHIVE_SHA256 = '744e04cad9270122e7961042a5e554461fc56169bd928940878fa465b8d810e4'
FILE_ID = 140
MEMBER = 261
RECORD = 16
ACCURACY = 5

_CACHE = {}


def diff_offsets(before, after, chunk=1 << 20):
    changed = []
    for base in range(0, len(before), chunk):
        end = min(base + chunk, len(before))
        if before[base:end] != after[base:end]:
            changed.extend(i for i in range(base, end) if before[i] != after[i])
    return changed


def archive_slot(data):
    fat_offset = struct.unpack_from('<I', data, 0x48)[0]
    return struct.unpack_from('<II', data, fat_offset + 8 * FILE_ID)


def archive_bytes(data):
    start, end = archive_slot(data)
    return bytes(data[start:end])


def member_offset(archive):
    fatb_size = struct.unpack_from('<I', archive, 0x14)[0]
    fntb = 0x10 + fatb_size
    fimg_data = fntb + struct.unpack_from('<I', archive, fntb + 4)[0] + 8
    return fimg_data + MEMBER * RECORD


def expected_rom_offset(data):
    start, _ = archive_slot(data)
    return start + member_offset(archive_bytes(data)) + ACCURACY


def member_bytes(data):
    archive = archive_bytes(data)
    offset = member_offset(archive)
    return archive[offset:offset + RECORD]


class CandidateRom(unittest.TestCase):
    def rom(self, language):
        path, sha256 = INPUTS[language]
        path = Path(path)
        if not path.is_file():
            reason = f'{language} input ROM not present: {path}'
            if REQUIRE_INPUTS:
                self.fail(reason)
            self.skipTest(reason)
        if language not in _CACHE:
            data = path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), sha256,
                             f'{language} input ROM sha256 mismatch')
            _CACHE[language] = data
        return _CACHE[language]


class CandidateMoveRom(CandidateRom):
    def test_archive_identity_and_file_id(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                data = self.rom(language)
                self.assertEqual(ndspy.rom.NintendoDSRom(data).filenames.idOf(ARCHIVE), FILE_ID)
                self.assertEqual(hashlib.sha256(archive_bytes(data)).hexdigest(), ARCHIVE_SHA256)

    def test_apply_and_verify_changes_exactly_one_rom_byte(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                data = self.rom(language)
                expected = expected_rom_offset(data)
                out, receipt = moves.apply(data, language)
                self.assertEqual(diff_offsets(data, out), [expected])
                self.assertEqual(data[expected], 75)
                self.assertEqual(out[expected], 85)
                self.assertEqual(receipt['rom_offset'], expected)
                self.assertEqual(len(out), len(data))
                self.assertEqual(out[:0x200], data[:0x200])
                proof = moves.verify(data, out, receipt)
                self.assertEqual(proof['changed_rom_bytes'], 1)
                self.assertEqual(proof['accuracy_after'], 85)

    def test_pp_and_max_pp_across_pp_up_unchanged(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                data = self.rom(language)
                out, _ = moves.apply(data, language)
                before = member_bytes(data)
                after = member_bytes(out)
                self.assertEqual(after[6], 15)
                self.assertEqual(before[6], after[6])
                pp = after[6]
                max_pp = [pp + pp * 20 * ups // 100 for ups in range(4)]
                self.assertEqual(max_pp, [15, 18, 21, 24])

    def test_effect_category_and_type_unchanged(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                data = self.rom(language)
                out, _ = moves.apply(data, language)
                before = member_bytes(data)
                after = member_bytes(out)
                self.assertEqual(struct.unpack_from('<H', after, 0)[0], 167)
                self.assertEqual(after[4], 10)
                self.assertEqual(after[2], before[2])
                self.assertEqual(after[4], before[4])

    def test_reapplication_on_patched_rom_is_refused(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                data = self.rom(language)
                out, _ = moves.apply(data, language)
                with self.assertRaisesRegex(ValueError, 'already patched'):
                    moves.apply(out, language)

    def test_other_member_byte_altered_is_refused(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                data = bytearray(self.rom(language))
                data[expected_rom_offset(bytes(data)) + 1] ^= 0x01
                with self.assertRaisesRegex(ValueError, 'foreign member 261'):
                    moves.apply(bytes(data), language)

    def test_verify_rejects_unrecorded_extra_change(self):
        data = self.rom('EN')
        out, receipt = moves.apply(data, 'EN')
        tampered = bytearray(out)
        tampered[expected_rom_offset(data) + 1] ^= 0x01
        with self.assertRaises(ValueError):
            moves.verify(data, bytes(tampered), receipt)


class NativeAccuracyCheck(CandidateRom):
    """Run the real overlay 12 accuracy check on the battle cache built from
    the archive (contiguous read, as LoadMoveTbl does). Boundaries are those of
    features/modern-accuracy/test/accuracy_bench.py; CPU coverage only."""

    def bench(self, language):
        import sys
        tests = ROOT / 'source' / 'features' / 'modern-accuracy' / 'test'
        if str(tests) not in sys.path:
            sys.path.insert(0, str(tests))
        import accuracy_bench
        data = self.rom(language)
        patched, _ = moves.apply(data, language)
        path = Path(INPUTS[language][0])
        image = accuracy_bench.overlay_image(data)
        self.assertEqual(image, accuracy_bench.overlay_image(patched), 'overlay 12 untouched by the data stage')
        tables = [accuracy_bench.move_table(archive_bytes(rom)) for rom in (data, patched)]
        return accuracy_bench, accuracy_bench.Bench(path, image), tables

    def test_wisp_hits_75_then_85_of_100_residues_same_rng_calls(self):
        for language in ('EN', 'IT'):
            ab, b, (old, new) = self.bench(language)
            outcomes = []
            for table in (old, new):
                row = []
                for residue in range(100):
                    missed, seen = b.run({'move': MEMBER, 'move_table': table}, residue)
                    self.assertTrue(seen['preserved'])
                    self.assertEqual([c for c in seen['calls'] if c[0] == 'random'], [('random',)])
                    row.append(not missed)
                outcomes.append(row)
            self.assertEqual(sum(outcomes[0]), 75, language)
            self.assertEqual(sum(outcomes[1]), 85, language)
            changed = [r for r in range(100) if outcomes[0][r] != outcomes[1][r]]
            self.assertEqual(changed, list(range(75, 85)), language)

    def test_stage_scaling_uses_85(self):
        table = [(33, 100), (36, 100), (43, 100), (50, 100), (60, 100), (75, 100), (1, 1),
                 (133, 100), (166, 100), (2, 1), (233, 100), (133, 50), (3, 1)]
        for language in ('EN', 'IT'):
            ab, b, (old, new) = self.bench(language)
            for stage in range(13):
                for table_bytes, accuracy in ((old, 75), (new, 85)):
                    case = {'move': MEMBER, 'move_table': table_bytes, 'eva': {1: 12 - stage}}
                    seen = b.run(case, 0)[1]
                    num, den = table[stage]
                    self.assertEqual(seen['hit_chance'], accuracy * num // den, (language, stage, accuracy))

    def test_native_battle_loader_reads_468_contiguous_records_of_archive_11(self):
        """LoadMoveTbl (ARM9 0x02073300) = ReadFromNarcMemberByIdPair(dest, 11,
        0, 0, 0x75 << 6): NARC 11 is a/0/1/1, member 0, offset 0, 468 * 16 bytes.
        Battle init (overlay 12, 0x0224868E) passes ctx + 0x3DE, the base the
        accuracy check indexes. Pinned instruction bytes, not a pret assumption."""
        from sgp12.rom import Arm9, Rom, bl_decode
        for language in ('EN', 'IT'):
            self.rom(language)  # skips/fails before any read when the input is absent
            arm = Arm9(Path(INPUTS[language][0]))
            self.assertEqual(arm.leggi(0x02073300, 0x14).hex(),
                             '08b57521890100220091' '0b21131c94f727f908bd', language)
            entry, _, image = Rom(self.rom(language)).immagine_overlay(12)
            at = 0x0224868E - entry['ram']
            self.assertEqual(image[at:at + 2], bytes.fromhex('0648'))  # ldr r0, [pc, #0x18]
            literal = ((0x0224868E + 4) & ~3) + 0x18 - entry['ram']
            self.assertEqual(struct.unpack_from('<I', image, literal)[0], 0x3DE)
            self.assertEqual(bl_decode(0x02248692, image[at + 4:at + 8]), 0x02073300)
            self.assertEqual(0x75 << 6, 468 * RECORD)
            self.assertEqual(moves.MOVE_TABLE_BYTES, 468 * RECORD)

    def test_other_moves_in_battle_cache_unchanged(self):
        for language in ('EN', 'IT'):
            ab, b, (old, new) = self.bench(language)
            diff = [i for i in range(len(old)) if old[i] != new[i]]
            self.assertEqual(diff, [MEMBER * RECORD + ACCURACY], language)


if __name__ == '__main__':
    unittest.main()
