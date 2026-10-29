"""Guarded personal deltas; private ROM tests exercise actual native stat code."""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

import ndspy.fnt
import ndspy.narc
import ndspy.rom

from sgp13 import learnsets, species


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def personal():
    raw = bytearray(range(44))
    raw[:6] = bytes([50, 60, 70, 80, 90, 100])
    raw[22:24] = bytes([68, 0])
    return bytes(raw)


def service_bench(bench_type, module, *args):
    """Keep the existing OS/NARC seams, scoped to their service entry points.

    All other native instructions execute without a per-instruction Python
    callback. Get/SetMonData, CreateMon and recalculation are never seamed.
    """
    from unittest.mock import patch
    from unicorn import Uc, UC_HOOK_CODE
    services = (0x0201AA8C, 0x0201AACC, 0x0201AB0C, 0x02007508,
                0x02007524, 0x02007544, 0x0200757C, 0x0202551C,
                0x0201FF98, 0x0202877C, 0x02028758, 0x02040374,
                0x0202D18C, 0x020147DC, 0x0200BFCC, 0x0200C1D4,
                0x021F2208, 0x0200BF8C, 0x023DCA98, 0x020272C8,
                0x023EEC00, 0x0200BCDC, 0x0203DFE0, 0x02028EA8,
                0x02028E9C, 0x02028F84, 0x02074904, 0x02074640,
                0x02074644, 0x023EE008, 0x023EE004, 0x023EE000,
                0x02074524, 0x02247A18)
    def engine(*values, **kwargs):
        mu = Uc(*values, **kwargs)
        add = mu.hook_add
        def hook(kind, callback, *values, **kwargs):
            if kind == UC_HOOK_CODE and not kwargs.get('begin'):
                handles = [add(kind, callback, *values, begin=a, end=a)
                           for a in services]
                return handles[0]
            return add(kind, callback, *values, **kwargs)
        mu.hook_add = hook
        return mu
    with patch.object(module, 'Uc', engine):
        return bench_type(*args)


class SpeciesTests(unittest.TestCase):
    def setUp(self):
        self.members = [personal(), personal(), personal()]
        archive = ndspy.narc.NARC(); archive.files = self.members
        self.raw = archive.save()
        self.changes = [{'species': 1, 'source_sha256': digest(self.members[1]),
                         'stats': [65, 66, 77, 88, 99, 110], 'abilities': [68, 101]}]

    def test_only_stats_and_ability_slots_change_without_reordering_members(self):
        result, report = species.patch_archive(self.raw, self.changes, digest(self.raw))
        files = ndspy.narc.NARC(result).files
        expected = bytearray(self.members[1]); expected[:6] = bytes([65, 66, 77, 88, 99, 110])
        expected[22:24] = bytes([68, 101])
        self.assertEqual(files, [self.members[0], bytes(expected), self.members[2]])
        self.assertEqual(report[0]['species'], 1)
        self.assertEqual(report[0]['before_sha256'], digest(self.members[1]))
        self.assertEqual(report[0]['after_sha256'], digest(bytes(expected)))
        self.assertEqual(ndspy.narc.NARC(self.raw).files, self.members)
        self.assertTrue(species.verify_archive(self.raw, result, self.changes))
        with self.assertRaisesRegex(ValueError, 'archive preimage'):
            species.patch_archive(result, self.changes, digest(self.raw))

    def test_all_preimages_are_checked_before_replacement(self):
        changes = self.changes + [{**self.changes[0], 'species': 2, 'source_sha256': '0' * 64}]
        with self.assertRaisesRegex(ValueError, 'member preimage'):
            species.patch_archive(self.raw, changes, digest(self.raw))
        self.assertEqual(ndspy.narc.NARC(self.raw).files, self.members)

    def test_invalid_records_indices_values_and_empty_patches_are_rejected(self):
        variants = [[], self.changes * 2]
        for field, values in [('species', [0, -1, 3, True]),
                              ('stats', [[0] * 6, [256] * 6, [True] * 6, [50] * 5]),
                              ('abilities', [[0, 0], [68, 124], [True, 0], [68]])]:
            variants += [[{**self.changes[0], field: value}] for value in values]
        for changes in variants:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                species.patch_archive(self.raw, changes, digest(self.raw))
        for size in (43, 45):
            archive = ndspy.narc.NARC(self.raw); archive.files[1] = bytes(size)
            raw = archive.save()
            with self.subTest(size=size), self.assertRaisesRegex(ValueError, '44'):
                species.patch_archive(raw, [{**self.changes[0], 'source_sha256': digest(bytes(size))}], digest(raw))

    def test_noop_and_form_record_edits_are_rejected(self):
        noop = [{**self.changes[0], 'stats': list(self.members[1][:6]),
                 'abilities': list(self.members[1][22:24])}]
        with self.assertRaisesRegex(ValueError, 'no permitted field'):
            species.patch_archive(self.raw, noop, digest(self.raw))
        archive = ndspy.narc.NARC(); archive.files = [personal()] * 495
        raw = archive.save()
        with self.assertRaisesRegex(ValueError, 'index'):
            species.patch_archive(raw, [{**self.changes[0], 'species': 494}], digest(raw))

    def test_readback_detects_untouched_fields_members_count_and_wrong_edits(self):
        result, _ = species.patch_archive(self.raw, self.changes, digest(self.raw))
        for member, offset in ((0, 0), (1, 6), (1, 21), (1, 24), (1, 43), (1, 0), (1, 23)):
            archive = ndspy.narc.NARC(result)
            raw = bytearray(archive.files[member]); raw[offset] ^= 1; archive.files[member] = bytes(raw)
            with self.subTest(member=member, offset=offset), self.assertRaises(ValueError):
                species.verify_archive(self.raw, archive.save(), self.changes)
        archive = ndspy.narc.NARC(result); archive.files.append(personal())
        with self.assertRaisesRegex(ValueError, 'count'):
            species.verify_archive(self.raw, archive.save(), self.changes)

    def rom(self):
        rom = ndspy.rom.NintendoDSRom()
        rom.arm9 = b'ARM9' * 256; rom.arm7 = b'ARM7' * 128; rom.iconBanner = bytes(0x840)
        rom.filenames = ndspy.fnt.Folder(folders=[('a', ndspy.fnt.Folder(folders=[
            ('0', ndspy.fnt.Folder(folders=[
                ('0', ndspy.fnt.Folder(files=['2'], firstID=0)),
                ('1', ndspy.fnt.Folder(files=['1'], firstID=1))]))]))], files=['untouched'], firstID=2)
        rom.files = [self.raw, b'move semantics', b'unrelated learnsets/resources']
        spec = {'schema': 1, 'preimages': {'a/0/0/2': digest(self.raw), 'a/0/1/1': digest(rom.files[1])},
                'changes': self.changes}
        return rom.save() + b'opaque trailer', spec

    def test_rom_stage_preserves_other_files_native_code_and_original_opaque_bytes(self):
        before, spec = self.rom()
        result, report = species.apply(before, spec)
        old = ndspy.rom.NintendoDSRom(before); new = ndspy.rom.NintendoDSRom(result)
        self.assertEqual(new.files[1:], old.files[1:])
        self.assertEqual((new.arm9, new.arm7, new.iconBanner), (old.arm9, old.arm7, old.iconBanner))
        fat = struct.unpack_from('<I', before, 0x48)[0]
        permitted = {0x14, 0x15e, 0x15f} | set(range(0x80, 0x84)) | set(range(fat, fat + 8))
        self.assertTrue(all(a == b or i in permitted for i, (a, b) in enumerate(zip(before, result))))
        self.assertEqual(report['archive_output_sha256'], digest(new.files[0]))
        with self.assertRaisesRegex(ValueError, 'preimage'):
            species.apply(result, spec)

    def test_foreign_semantics_and_incomplete_specification_are_rejected(self):
        before, spec = self.rom()
        for path in spec['preimages']:
            rom = ndspy.rom.NintendoDSRom(before); rom.setFileByName(path, rom.getFileByName(path) + b'foreign')
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'preimage'):
                species.apply(rom.save(), spec)
        bad = copy.deepcopy(spec); del bad['preimages']['a/0/1/1']
        for variant in (bad, {**spec, 'schema': 2}):
            with self.assertRaises(ValueError):
                species.apply(before, variant)


class BalanceAuditTests(unittest.TestCase):
    def setUp(self):
        self.audit = {
            'schema': 1, 'analysis_only': True,
            'stats_order': ['HP', 'Atk', 'Def', 'Spe', 'SpA', 'SpD'],
            'source': {'name': 'Authored reference', 'version': '1.4.1',
                       'url': 'https://example.org/reference'},
            'decisions': [
                {'species': i, 'name': f'Species {i}', 'role': 'Native role',
                 'decision': 'retain', 'reason': 'Its current niche remains useful.',
                 'strengths': ['Distinct native utility'],
                 'remaining_weakness': 'Requires team support.',
                 'redux_reference': None, 'risk': 'No incremental intervention.',
                 'patches': {'personal': False, 'learnset': False}}
                for i in range(1, 494)]}
        self.audit['decisions'][21].update(
            decision='improve', redux_reference='Individually adapted reference.',
            patches={'personal': True, 'learnset': False})
        self.audit['decisions'][357].update(
            decision='retain_prior', patches={'personal': False, 'learnset': True})
        self.personal = [{'species': 22}]
        self.learned = [{'species': 358}]

    def validate(self, audit=None, personal=None, learned=None):
        self.assertTrue(callable(getattr(species, 'validate_audit', None)), 'authored audit validator is required')
        return species.validate_audit(
            self.audit if audit is None else audit,
            self.personal if personal is None else personal,
            self.learned if learned is None else learned)

    def test_complete_authored_coverage_accepts_prior_and_new_interventions(self):
        self.assertTrue(self.validate())

    def test_missing_duplicate_bool_and_out_of_range_species_are_rejected(self):
        for rows in (self.audit['decisions'][:-1],
                     self.audit['decisions'] + [self.audit['decisions'][0]]):
            bad = copy.deepcopy(self.audit); bad['decisions'] = rows
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                self.validate(bad)
        for value in (True, False, 0, 494, '1'):
            bad = copy.deepcopy(self.audit); bad['decisions'][0]['species'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.validate(bad)

    def test_authored_fields_and_provenance_cannot_be_empty_or_malformed(self):
        for key in ('name', 'role', 'reason', 'remaining_weakness', 'risk'):
            for value in ('', '   ', None, []):
                bad = copy.deepcopy(self.audit); bad['decisions'][21][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.validate(bad)
        for key, value in (('strengths', []), ('strengths', [' ']),
                           ('decision', 'skip'), ('redux_reference', ' '),
                           ('patches', {'personal': 1, 'learnset': False})):
            bad = copy.deepcopy(self.audit); bad['decisions'][21][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.validate(bad)
        for key, value in (('source', {}), ('stats_order', ['HP'] * 6),
                           ('analysis_only', False), ('schema', True)):
            bad = copy.deepcopy(self.audit); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.validate(bad)

    def test_patch_sets_and_decisions_must_tell_the_truth(self):
        for index, key, value in ((21, 'decision', 'retain'),
                                  (0, 'decision', 'improve'),
                                  (0, 'decision', 'retain_prior'),
                                  (21, 'patches', {'personal': False, 'learnset': False}),
                                  (0, 'patches', {'personal': True, 'learnset': False}),
                                  (357, 'patches', {'personal': False, 'learnset': False})):
            bad = copy.deepcopy(self.audit); bad['decisions'][index][key] = value
            with self.subTest(index=index, key=key), self.assertRaises(ValueError):
                self.validate(bad)
        for value in (True, 0, 494):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.validate(personal=[{'species': value}])
        with self.assertRaises(ValueError):
            self.validate(personal=self.personal * 2)
        with self.assertRaises(ValueError):
            self.validate(learned=[])

    def test_default_specification_load_requires_matching_authored_audit(self):
        # Removing the default validator would admit this deliberately false claim.
        from unittest.mock import patch
        audit_path = Path(species.__file__).parent / 'data/balance-audit.json'
        self.assertTrue(audit_path.is_file(), 'default specification requires authored audit')
        audit = json.loads(audit_path.read_text())
        real_read = Path.read_text
        audit['decisions'][21]['decision'] = 'retain'
        def read(path, *args, **kwargs):
            if path.name == 'balance-audit.json':
                return json.dumps(audit)
            return real_read(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read), self.assertRaises(ValueError):
            species.load_specification()

    def test_reviewed_new_species_and_learnset_values_reach_public_specs(self):
        changes = {c['species']: c for c in species.load_specification()['changes']}
        self.assertIn(28, changes, 'approved Sandslash intervention must be installed')
        self.assertEqual(changes[28]['stats'], [85, 100, 110, 65, 45, 65])
        self.assertEqual(changes[154]['abilities'], [65, 30])
        self.assertEqual(changes[262]['stats'], [70, 110, 70, 85, 60, 60])
        self.assertEqual(changes[411]['stats'], [70, 72, 168, 30, 47, 138])
        self.assertNotIn(428, changes, 'Whitney risk review declined the Lopunny stat import')
        learned = {c['species']: c['additions'] for c in learnsets.load_specification()['changes']}
        self.assertIn({'level': 46, 'move': 105}, learned[346])
        self.assertIn({'level': 43, 'move': 303}, learned[199])
        self.assertNotIn(97, learned)


@unittest.skipUnless(os.environ.get('SGP13_BASE_DIR'), 'private 1.2.5 EN/IT bases not supplied')
class ActualTableTests(unittest.TestCase):
    def test_both_languages_match_guards_and_all_additive_moves_survive_readback(self):
        outputs = []
        for language in ('EN', 'IT'):
            data = (Path(os.environ['SGP13_BASE_DIR']) / f'sgp-1.2.5-{language}.nds').read_bytes()
            original = ndspy.rom.NintendoDSRom(data)
            learned, receipt = learnsets.apply(data)
            result, report = species.apply(learned)
            updated = ndspy.rom.NintendoDSRom(result)
            audit = json.loads((Path(species.__file__).parent / 'data/balance-audit.json').read_text())
            for kind, rows in (('learnset', receipt['changes']), ('personal', report['changes'])):
                self.assertEqual({c['species'] for c in rows},
                                 {r['species'] for r in audit['decisions'] if r['patches'][kind]})
            before_personal = ndspy.narc.NARC(original.getFileByName(species.ARCHIVE)).files
            after_personal = ndspy.narc.NARC(updated.getFileByName(species.ARCHIVE)).files
            personal_ids = {c['species'] for c in report['changes']}
            self.assertEqual(len(before_personal), len(after_personal))
            for index, (old, new) in enumerate(zip(before_personal, after_personal)):
                if index in personal_ids:
                    self.assertNotEqual(new, old)
                    self.assertEqual(new[6:22], old[6:22])
                    self.assertEqual(new[24:], old[24:])
                else:
                    self.assertEqual(new, old)
            before_learned = ndspy.narc.NARC(original.getFileByName(learnsets.ARCHIVE)).files
            after_learned = ndspy.narc.NARC(updated.getFileByName(learnsets.ARCHIVE)).files
            learned_ids = {c['species'] for c in receipt['changes']}
            self.assertEqual(len(before_learned), len(after_learned))
            for index, (old, new) in enumerate(zip(before_learned, after_learned)):
                self.assertEqual(new == old, index not in learned_ids)
            for change in learnsets.load_specification()['changes']:
                old = learnsets.decode(ndspy.narc.NARC(original.getFileByName(learnsets.ARCHIVE)).files[change['species']])
                new = learnsets.decode(ndspy.narc.NARC(updated.getFileByName(learnsets.ARCHIVE)).files[change['species']])
                self.assertEqual([pair for pair in new if pair in old], old)
                self.assertLessEqual(len(new), 20)
                for addition in change['additions']:
                    self.assertIn((addition['level'], addition['move']), new)
            outputs.append([updated.getFileByName(path) for path in ('a/0/0/2', 'a/0/1/1', 'a/0/3/3')])
        self.assertEqual(*outputs)

    def test_actual_native_initial_moves_at_addition_and_later_levels(self):
        # Native constructor must skip a repeated move while it is still known,
        # rather than selecting the final four level-up rows blindly.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'features/shiny/test'))
        from test_native_constructor import ConstructorBench, bm
        from sgp13 import shiny, shiny_core
        critical = {(346, 54): [133, 246, 380, 105],
                    (310, 58): [435, 422, 46, 268],
                    (402, 14): [117, 210, 450, 141],
                    (470, 43): [202, 348, 427, 387]}
        with tempfile.TemporaryDirectory() as temp:
            blob, symbols = shiny.compile_native(temp)
            core, cs = shiny_core.compile_native(temp)
            for language in ('EN', 'IT'):
                data = (Path(os.environ['SGP13_BASE_DIR']) / f'sgp-1.2.5-{language}.nds').read_bytes()
                data, _ = learnsets.apply(data); data, _ = species.apply(data)
                path = Path(temp) / f'{language}.nds'; path.write_bytes(data)
                b = service_bench(ConstructorBench, bm, path, temp, blob, symbols, core, cs)
                for change in learnsets.load_specification()['changes']:
                    index = change['species']
                    pairs = learnsets.decode(b.member(33, index))
                    levels = {a['level'] for a in change['additions']}
                    levels |= {min(100, level + 10) for level in levels} | {100}
                    levels |= {level for sid, level in critical if sid == index}
                    for level in sorted(levels):
                        known = []
                        for learned_at, move in pairs:
                            if learned_at <= level and move not in known:
                                known = (known + [move])[-4:]
                        expected = critical.get((index, level), known + [0] * (4 - len(known)))
                        b.heap = 0x02300000
                        b.call(0x0206DE38, bm.MON, index, level, 32, 1, 0x12345678, 1, b.ot)
                        with self.subTest(language=language, species=index, level=level):
                            self.assertEqual([b.get(field) for field in (54, 55, 56, 57)], expected)
                self.assertEqual(b.assertions, 0)

    def test_meganium_native_new_slots_and_continue_preserve_saved_ability_identity(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'features/shiny/test'))
        from test_native_constructor import ConstructorBench, bm
        from sgp13 import shiny, shiny_core
        with tempfile.TemporaryDirectory() as temp:
            blob, symbols = shiny.compile_native(temp)
            core, cs = shiny_core.compile_native(temp)
            for language in ('EN', 'IT'):
                data = (Path(os.environ['SGP13_BASE_DIR']) / f'sgp-1.2.5-{language}.nds').read_bytes()
                data, _ = species.apply(data)
                path = Path(temp) / f'{language}.nds'; path.write_bytes(data)
                b = service_bench(ConstructorBench, bm, path, temp, blob, symbols, core, cs)
                for pid, ability in ((0x12345678, 65), (0x12345679, 30)):
                    b.heap = 0x02300000
                    b.call(0x0206DE38, bm.MON, 154, 50, 32, 1, pid, 1, b.ot)
                    with self.subTest(language=language, pid=pid):
                        self.assertEqual(b.get(10), ability)
                # Original 1.2.5 only supplies Overgrow65; saved65 must stay65
                # even with an odd PID that would now select Natural Cure30.
                # Ability102 is an additional synthetic identity-preservation
                # case, not evidence of a legacy Leaf Guard fixture.
                original = ndspy.rom.NintendoDSRom((Path(os.environ['SGP13_BASE_DIR']) /
                           f'sgp-1.2.5-{language}.nds').read_bytes())
                self.assertEqual(list(ndspy.narc.NARC(original.getFileByName(species.ARCHIVE)).files[154][22:24]), [65, 0])
                for saved_ability in (65, 102):
                    b.set(10, saved_ability)
                    before_box = bytes(b.mu.mem_read(bm.MON, 136))
                    fields = (0, 5, 6, 7, 8, 10, 54, 55, 56, 57, 70, 71, 72, 73, 74, 75)
                    before = [b.get(field) for field in fields]
                    b.party_count = 1
                    for _ in range(2):
                        b.call(symbols['sgp_shiny_continue'], 0)
                        with self.subTest(language=language, saved_ability=saved_ability):
                            self.assertEqual([b.get(field) for field in fields], before)
                            self.assertEqual(bytes(b.mu.mem_read(bm.MON, 136)), before_box)
                self.assertEqual(b.assertions, 0)

    def test_native_stat_recalculation_uses_patched_table_at_20_30_50(self):
        # Omitting any stat byte, swapping Spe/SpA, or bypassing the actual
        # archive loader must fail this test. Formula is an independent oracle.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'features/training-native/test'))
        import native_bench
        from native_bench import Bench, MON
        spec = species.load_specification()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); report = root / 'symbols.json'
            report.write_text(json.dumps({'symbols': {'training_native_save': 0x023ef100}}))
            for language in ('EN', 'IT'):
                data = (Path(os.environ['SGP13_BASE_DIR']) / f'sgp-1.2.5-{language}.nds').read_bytes()
                result, _ = species.apply(data); path = root / f'{language}.nds'; path.write_bytes(result)
                b = service_bench(Bench, native_bench, path, report)
                for change in spec['changes']:
                    for level in (20, 30, 50):
                        for evs in ([0] * 6, [128, 128, 0, 0, 0, 0], [252, 252, 0, 4, 0, 0]):
                            b.heap = 0x02300000; b.make_mon(change['species'], level)
                            b.set(0, 0)  # Hardy, neutral nature; fixed legal identity.
                            for i in range(6): b.set(70 + i, 15); b.set(13 + i, evs[i])
                            identity = [b.get(i) for i in (0, 7, 5, 8, 10, 6, 70, 71, 72, 73, 74, 75, 13, 14, 15, 16, 17, 18)]
                            b.call(0x0206E250, MON)
                            expected = [(2 * base + 15 + evs[i] // 4) * level // 100 + (level + 10 if i == 0 else 5)
                                        for i, base in enumerate(change['stats'])]
                            with self.subTest(language=language, species=change['species'], level=level, evs=evs):
                                self.assertEqual([b.get(i) for i in (164, 165, 166, 167, 168, 169)], expected)
                                self.assertEqual([b.get(i) for i in (0, 7, 5, 8, 10, 6, 70, 71, 72, 73, 74, 75, 13, 14, 15, 16, 17, 18)], identity)
                self.assertEqual(b.assertions, 0)


if __name__ == '__main__':
    unittest.main()
