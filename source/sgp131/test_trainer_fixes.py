"""SG-TR02 trainer-party repair, written before the implementation."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest

import ndspy.narc
import ndspy.rom
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

from . import build, mechanics_stages as M, trainer_fixes as T
from .test_legacy_scripts import inputs
from sgp12.rom import Arm9, bl_decode


BENCH_PATH = Path(__file__).resolve().parents[1] / 'features/rematch-variants/test/constructor_bench.py'
BENCH_SPEC = importlib.util.spec_from_file_location('trainer_fixes_constructor_bench', BENCH_PATH)
if BENCH_SPEC is None or BENCH_SPEC.loader is None:
    raise RuntimeError('cannot load the real trainer constructor bench')
CONSTRUCTOR_BENCH = importlib.util.module_from_spec(BENCH_SPEC)
BENCH_SPEC.loader.exec_module(CONSTRUCTOR_BENCH)


def levels(member):
    if len(member) % 8:
        raise ValueError('default-moves trainer member geometry')
    return [struct.unpack_from('<H', member, offset + 2)[0]
            for offset in range(0, len(member), 8)]


class WadeArchiveRepair(unittest.TestCase):
    @staticmethod
    def source(language):
        data = inputs(language)[0]
        rom = ndspy.rom.NintendoDSRom(data)
        fid = rom.filenames.idOf(T.ARCHIVE)
        return data, fid, bytes(rom.files[fid])

    def test_only_wades_first_two_selected_members_are_swapped(self):
        outputs = []
        for language in ('EN', 'IT'):
            _, _, raw = self.source(language)
            old = ndspy.narc.NARC(raw).files
            patched, receipt = T.patch_archive(raw)
            new = ndspy.narc.NARC(patched).files
            with self.subTest(language=language):
                self.assertEqual(len(new), len(old))
                self.assertEqual([i for i, (a, b) in enumerate(zip(old, new)) if a != b],
                                 [460, 461])
                self.assertEqual(bytes(new[461]), bytes(old[460]))
                self.assertEqual(bytes(new[460]), bytes(old[461]))
                self.assertEqual(levels(new[461]), [46, 46, 46, 46])
                self.assertEqual(levels(new[460]), [52, 52, 52, 52])
                self.assertEqual(levels(new[512]), [68, 68, 68, 68])
                self.assertEqual(receipt['changed_members'], [460, 461])
                self.assertEqual(receipt['archive_sha256_after'], T.ARCHIVE_AFTER_SHA256)
            outputs.append(hashlib.sha256(patched).hexdigest())
        self.assertEqual(outputs[0], outputs[1])

    def test_wrong_archive_and_reapplication_are_refused(self):
        _, _, raw = self.source('EN')
        corrupted = bytearray(raw)
        corrupted[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'archive differs'):
            T.patch_archive(bytes(corrupted))
        patched, _ = T.patch_archive(raw)
        with self.assertRaises(ValueError):
            T.patch_archive(patched)


class WadeWholeRomRepair(unittest.TestCase):
    def test_en_it_apply_and_independent_verify_change_only_declared_repairs(self):
        hashes = []
        expected = {
            'EN': '618855acc18dce359f2d9f75dc9735622240bccbfc03e130828e4f956d2169c7',
            'IT': '3dda0cfd8b04b7f9e1e6bf26e990c5cf63ad37606e747ec47d9bcf35679243cb',
        }
        for language in ('EN', 'IT'):
            before, fid, raw = WadeArchiveRepair.source(language)
            after, receipt = T.apply(before, language)
            report = T.verify(before, after, receipt)
            old = ndspy.rom.NintendoDSRom(before)
            new = ndspy.rom.NintendoDSRom(after)
            with self.subTest(language=language):
                self.assertEqual(len(after), len(before))
                self.assertEqual(receipt['file_id'], fid)
                self.assertEqual(report['changed_files'], [fid])
                self.assertEqual(report['form_stats']['calc_mon_stats'], 0x0206E250)
                self.assertEqual(report['form_stats']['update_mon_ability'], 0x020722D4)
                self.assertEqual(bytes(old.files[fid]), raw)
                self.assertEqual(
                    [i for i, (a, b) in enumerate(zip(old.files, new.files)) if a != b],
                    [fid],
                )
                self.assertEqual(hashlib.sha256(after).hexdigest(), expected[language])
            hashes.append(receipt['archive_sha256_after'])
        self.assertEqual(hashes[0], hashes[1])

    def test_receipt_or_unrelated_rom_mutation_is_refused(self):
        before, _, _ = WadeArchiveRepair.source('EN')
        after, receipt = T.apply(before, 'EN')
        forged = dict(receipt, output_sha256='0' * 64)
        with self.assertRaises(ValueError):
            T.verify(before, after, forged)
        mutated = bytearray(after)
        mutated[0x200] ^= 1
        with self.assertRaises(ValueError):
            T.verify(before, bytes(mutated), receipt)


class TrainerAlternateFormStatsRepair(unittest.TestCase):
    HELPER = 0x02073AE4
    CALC_MON_STATS = 0x0206E250
    UPDATE_MON_ABILITY = 0x020722D4
    MON_HAS_MOVE = 0x02071754
    CALLERS = (0x0207373C, 0x02073846, 0x0207393C, 0x02073A5A)

    def test_shared_post_form_helper_refreshes_ability_and_stats_before_friendship(self):
        decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for language in ('EN', 'IT'):
            before = inputs(language)[0]
            after, _receipt = T.apply(before, language)
            arm = Arm9.from_bytes(after)
            helper = arm.leggi(self.HELPER, 0x32)
            instructions = list(decoder.disasm(helper, self.HELPER))
            calls = [(insn.address, int(insn.op_str[1:], 16))
                     for insn in instructions if insn.mnemonic == 'bl']
            with self.subTest(language=language):
                self.assertEqual(len(helper), 0x32)
                self.assertEqual(instructions[-3].address, 0x02073B10)
                self.assertEqual(instructions[-3].mnemonic, 'pop')
                self.assertEqual(calls, [
                    (0x02073AE8, self.UPDATE_MON_ABILITY),
                    (0x02073AEE, self.CALC_MON_STATS),
                    (0x02073AF6, self.MON_HAS_MOVE),
                    (0x02073B0C, 0x0206EC40),
                ])
                self.assertEqual([bl_decode(site, arm.leggi(site, 4))
                                  for site in self.CALLERS], [self.HELPER] * 4)

    def test_helper_preimage_and_patched_call_mutants_are_refused(self):
        for language in ('EN', 'IT'):
            before = inputs(language)[0]
            mutant = bytearray(before)
            arm = Arm9.from_bytes(bytes(mutant))
            offset = arm.off(self.HELPER, 1)
            mutant[offset] ^= 1
            with self.subTest(language=language, mutant='preimage'):
                with self.assertRaisesRegex(ValueError, 'helper differs'):
                    T.apply(bytes(mutant), language)
            after, receipt = T.apply(before, language)
            mutant = bytearray(after)
            arm = Arm9.from_bytes(bytes(mutant))
            offset = arm.off(self.HELPER + 4, 1)
            mutant[offset] ^= 1
            with self.subTest(language=language, mutant='patched-call'):
                with self.assertRaisesRegex(ValueError, 'declared result'):
                    T.verify(before, bytes(mutant), receipt)


class TrainerAlternateFormAbilityRepair(unittest.TestCase):
    HORTON_STATS = (
        (124, 79, 138, 92, 124, 126),
        (124, 79, 138, 92, 124, 126),
        (124, 79, 138, 92, 124, 126),
        (124, 79, 119, 123, 124, 109),
        (124, 79, 138, 92, 124, 126),
    )

    @staticmethod
    def bench(language):
        before = inputs(language)[0]
        after, _receipt = T.apply(before, language)
        archives = CONSTRUCTOR_BENCH.Archives(after)
        return CONSTRUCTOR_BENCH.Bench(after, archives, language)

    @staticmethod
    def party_stats(raw, pid):
        party = CONSTRUCTOR_BENCH._decrypt(raw[136:236], pid)
        _hp, max_hp, attack, defense, speed, spatk, spdef = struct.unpack_from('<7H', party, 6)
        return max_hp, attack, defense, speed, spatk, spdef

    @staticmethod
    def single_member(species, form, ability_slot):
        override = 0x10 if ability_slot == 0 else 0x20
        return struct.pack('<BBHHH', 255, override, 50, species | (form << 10), 0)

    @staticmethod
    def single_header():
        header = bytearray(52)
        header[0], header[1], header[3] = 0, 6, 1
        return bytes(header)

    def test_real_horton_fan_uses_motor_drive_and_keeps_fixed_form_stats(self):
        for language in ('EN', 'IT'):
            bench = self.bench(language)
            first = bench.run(396, plus=0)
            replay = bench.run(396, plus=0)
            with self.subTest(language=language):
                self.assertEqual(first['mons'], replay['mons'])
                self.assertEqual(first['party_header'], (6, 5))
                self.assertEqual([mon['form'] for mon in first['decoded']], [1, 2, 3, 4, 5])
                self.assertEqual([mon['pid'] for mon in first['decoded']], [2685832] * 5)
                self.assertEqual([mon['ability'] for mon in first['decoded']], [26, 26, 26, 78, 26])
                self.assertEqual([mon['checksum_ok'] for mon in first['decoded']], [True] * 5)
                self.assertEqual([mon['friendship'] for mon in first['decoded']], [255] * 5)
                self.assertEqual(first['misalign'], [])
                self.assertTrue(first['stack_canary'])
                self.assertEqual(
                    [self.party_stats(raw, mon['pid'])
                     for raw, mon in zip(first['mons'], first['decoded'])],
                    list(self.HORTON_STATS),
                )

    def test_real_constructor_resolves_both_wormadam_ability_slots_by_form(self):
        cases = (
            (0, 0, 107),
            (0, 1, 102),
            (1, 0, 107),
            (1, 1, 8),
            (2, 0, 107),
            (2, 1, 5),
        )
        header = self.single_header()
        for language in ('EN', 'IT'):
            bench = self.bench(language)
            for form, ability_slot, expected in cases:
                member = self.single_member(413, form, ability_slot)
                first = bench.run(248, plus=0, buffer=member, trainer_data=header)
                replay = bench.run(248, plus=0, buffer=member, trainer_data=header)
                mon = first['decoded'][0]
                with self.subTest(language=language, form=form, ability_slot=ability_slot):
                    self.assertEqual(first['mons'], replay['mons'])
                    self.assertEqual(first['party_header'], (6, 1))
                    self.assertEqual((mon['species'], mon['form']), (413, form))
                    self.assertEqual(mon['pid'] & 1, ability_slot)
                    self.assertEqual(mon['ability'], expected)
                    self.assertTrue(mon['checksum_ok'])
                    self.assertEqual(mon['friendship'], 255)
                    self.assertEqual(first['misalign'], [])
                    self.assertTrue(first['stack_canary'])

    def test_frustration_still_sets_zero_friendship_after_form_refresh(self):
        header = bytearray(self.single_header())
        header[0] = 1
        member = struct.pack(
            '<BBHH4HH',
            255, 0x10, 50, 479 | (4 << 10),
            218, 85, 86, 87, 0,
        )
        for language in ('EN', 'IT'):
            bench = self.bench(language)
            run = bench.run(248, plus=0, buffer=member, trainer_data=bytes(header))
            mon = run['decoded'][0]
            with self.subTest(language=language):
                self.assertEqual((mon['form'], mon['ability'], mon['friendship']), (4, 78, 0))
                self.assertTrue(mon['checksum_ok'])
                self.assertEqual(run['misalign'], [])
                self.assertTrue(run['stack_canary'])


class Registration(unittest.TestCase):
    def test_stage_is_between_legacy_and_runtime_features(self):
        self.assertIn('trainer-fixes', M.IMPLEMENTED)
        self.assertLess(M.ORDER.index('legacy'), M.ORDER.index('legendary-scene-version'))
        self.assertLess(M.ORDER.index('legendary-scene-version'), M.ORDER.index('trainer-fixes'))
        self.assertLess(M.ORDER.index('trainer-fixes'), M.ORDER.index('controls'))
        stage = M.require_stage('trainer-fixes')
        self.assertFalse(stage.archive_only)
        self.assertIsNone(stage.slot)

    def test_acceptance_requires_the_wade_progression(self):
        prior = build.REQUIRED_CASES['legendary-scene-version']
        cases = build.REQUIRED_CASES['trainer-fixes']
        self.assertEqual(cases[:len(prior)], prior)
        self.assertIn('trainer_wade_rematches_increase_46_52_68', cases)
        self.assertIn('trainer_alternate_forms_stats_all_formats_and_turn_order', cases)
        self.assertEqual(build.REQUIRED_CASES['controls'][:len(cases)], cases)


if __name__ == '__main__':
    unittest.main()
