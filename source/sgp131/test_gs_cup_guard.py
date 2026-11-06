"""HG-F08: exact GS special-list/League-guard script component reproducer.

The independent behavior oracle is the annotated contemporary video linked in
``docs/known-bugs-hgss.md``: after merely viewing the GS Cup special-Pokemon
list, Will's guard must still execute his normal step-aside movement.  This
small interpreter executes decoded cartridge commands only; it is not an
emulator, rendered UI, save test or native-input playthrough.
"""
import hashlib
import importlib.util
import os
import unittest

from sgp131 import archives, gifts_scripts as scripts
from sgp131.test_legacy_scripts import inputs


VIEWER_MEMBER = 4
GUARD_MEMBER = 819
TEMP_4005 = 0x4005
PREIMAGES = {
    VIEWER_MEMBER: '6ddaf0ae4e954d4ec90cd783247ceb46a914a8f56d3184b86c75ef9f5cc208fb',
    GUARD_MEMBER: '5c89e5608b01f59a6ffcaff54286301ae0e27f4a166357333a8f239ee35b39ea',
}
SPECIAL_SPECIES = (150, 249, 250, 382, 383, 384, 483, 484, 487)


def candidate(raw, language, commands):
    """Use inherited bytes for the explicit RED oracle, otherwise the repair when present."""
    if os.environ.get('SGP_GS_CUP_BASELINE') == '1' or \
            importlib.util.find_spec('sgp131.gs_cup_guard') is None:
        return raw
    from sgp131 import gs_cup_guard
    return gs_cup_guard.patch_member(raw, language, commands)


class ScriptModel:
    """Bounded model of the real commands reached by the list and guard paths."""

    UI = {
        'PlaySE', 'LockAll', 'FacePlayer', 'TouchscreenMenuShow',
        'TouchscreenMenuHide', 'BufferPlayersName', 'BufferSpeciesName',
        'NPCMsg', 'WaitButton', 'CloseMsg', 'ReleaseAll', 'WaitMovement',
    }

    def __init__(self, viewer, guard, commands, *, seen=(), variables=None, facing=2):
        self.members = {
            VIEWER_MEMBER: scripts.decode(viewer, commands, VIEWER_MEMBER),
            GUARD_MEMBER: scripts.decode(guard, commands, GUARD_MEMBER),
        }
        self.seen = set(seen)
        self.vars = dict(variables or {})
        self.facing = facing
        self.comparison = -1
        self.messages = []
        self.movements = []
        self.trace = []

    def value(self, operand):
        return self.vars.get(operand, 0) if operand >= 0x4000 else operand

    def condition(self, code):
        return {
            0: self.comparison < 0,
            1: self.comparison == 0,
            2: self.comparison > 0,
            3: self.comparison <= 0,
            4: self.comparison >= 0,
            5: self.comparison != 0,
        }[code]

    def run(self, member, start, *, stop=None, budget=160):
        pc = start
        for _ in range(budget):
            if pc == stop:
                return self
            ins = self.members[member].istruzioni.get(pc)
            if ins is None:
                raise AssertionError(f'model PC outside decoded member {member}:{pc:#x}')
            name, args = ins.nome, ins.args
            self.trace.append((member, ins.off, name, list(args)))
            pc = ins.fine
            target = ins.rami[0][1] if ins.rami else None
            if name == 'SetVar':
                self.vars[args[0]] = args[1]
            elif name == 'CheckMonSeen':
                self.vars[args[1]] = int(args[0] in self.seen)
            elif name == 'CompareVarToValue':
                a, b = self.value(args[0]), args[1]
                self.comparison = (a > b) - (a < b)
            elif name == 'GoToIf':
                if self.condition(args[0]):
                    pc = target
            elif name == 'GoTo':
                pc = target
            elif name == 'GetPlayerFacing':
                self.vars[args[0]] = self.facing
            elif name == 'ApplyMovement':
                self.movements.append((args[0], target))
            elif name == 'NPCMsg':
                self.messages.append(args[0])
            elif name == 'End':
                return self
            elif name not in self.UI:
                raise AssertionError(f'unsupported opcode {name} at {member}:{ins.off:#x}')
        raise AssertionError('model step budget exhausted')


class GsCupGuardComponent(unittest.TestCase):
    def exact(self, language, repaired):
        _, raw, commands = inputs(language)
        viewer = candidate(raw[VIEWER_MEMBER], language, commands) if repaired else raw[VIEWER_MEMBER]
        return raw, commands, viewer

    def test_exact_en_it_members_authenticate_and_decode_the_diagnosed_flow(self):
        members = {}
        for language in ('EN', 'IT'):
            _, raw, commands = inputs(language)
            members[language] = (raw[VIEWER_MEMBER], raw[GUARD_MEMBER])
            with self.subTest(language=language):
                for member in (VIEWER_MEMBER, GUARD_MEMBER):
                    self.assertEqual(hashlib.sha256(raw[member]).hexdigest(), PREIMAGES[member])
                    self.assertFalse(scripts.overlapping_instructions(
                        scripts.decode(raw[member], commands, member)))
                self.assertEqual(scripts.decode(raw[GUARD_MEMBER], commands, GUARD_MEMBER).entry[8],
                                 0x17F)
        self.assertEqual(members['EN'], members['IT'])

    def test_inherited_special_list_sets_the_guard_latch_and_skips_movement(self):
        """Reproducer: removing the viewer write or guard predicate must break this RED oracle."""
        for language in ('EN', 'IT'):
            raw, commands, _ = self.exact(language, repaired=False)
            vm = ScriptModel(raw[VIEWER_MEMBER], raw[GUARD_MEMBER], commands,
                             seen={SPECIAL_SPECIES[0]})
            vm.run(VIEWER_MEMBER, 0x778, stop=0x682)
            self.assertEqual(vm.vars[TEMP_4005], 1)
            vm.run(GUARD_MEMBER, 0x17F)
            with self.subTest(language=language):
                self.assertEqual(vm.movements, [])
                self.assertIn(6, vm.messages)

    def test_repaired_viewer_teardown_clears_its_accumulator_before_guard_entry(self):
        """Production break caught: omitting the teardown clear leaves x4005=1 and no movement."""
        for language in ('EN', 'IT'):
            raw, commands, viewer = self.exact(language, repaired=True)
            for species in SPECIAL_SPECIES:
                vm = ScriptModel(viewer, raw[GUARD_MEMBER], commands, seen={species})
                vm.run(VIEWER_MEMBER, 0x778, stop=0x682)
                with self.subTest(language=language, species=species):
                    self.assertEqual(vm.vars[TEMP_4005], 0)
                    self.assertIn(27, vm.messages)
                vm.run(GUARD_MEMBER, 0x17F)
                self.assertEqual(vm.movements, [(8, 0x634)])

    def test_omission_empty_list_and_map_reset_controls_still_move_the_guard(self):
        for language in ('EN', 'IT'):
            raw, commands, viewer = self.exact(language, repaired=True)
            cases = []
            cases.append(ScriptModel(viewer, raw[GUARD_MEMBER], commands))
            empty = ScriptModel(viewer, raw[GUARD_MEMBER], commands)
            empty.run(VIEWER_MEMBER, 0x778, stop=0x682)
            self.assertIn(28, empty.messages)
            cases.append(empty)
            reset = ScriptModel(viewer, raw[GUARD_MEMBER], commands,
                                variables={TEMP_4005: 1})
            reset.vars[TEMP_4005] = 0  # ClearTempFieldEventData on ordinary map load.
            cases.append(reset)
            for index, vm in enumerate(cases):
                vm.run(GUARD_MEMBER, 0x17F)
                with self.subTest(language=language, control=index):
                    self.assertEqual(vm.movements, [(8, 0x634)])


class GsCupGuardArchiveDelta(unittest.TestCase):
    def test_producer_checker_preserve_archive_geometry_and_replay_in_both_languages(self):
        from sgp131 import gs_cup_guard as repair
        self.assertTrue(hasattr(repair, 'derive') and hasattr(repair, 'check'),
                        'the GS Cup repair still lacks its archive producer/checker')
        records = []
        for language in ('EN', 'IT'):
            data, raw, _ = inputs(language)
            delta = repair.derive(data, language)
            self.assertEqual((delta.archive, delta.producers(), [row.index for row in delta.members]),
                             ('a/0/1/2', ['gs-cup-guard'], [VIEWER_MEMBER]))
            row = delta.members[0]
            self.assertEqual((row.before_sha256, len(row.after), hashlib.sha256(row.after).hexdigest()),
                             (PREIMAGES[VIEWER_MEMBER], 3928,
                              'e556ac6c627066bd6048657fd419401f931ed8ccff321b21ab5f82a47dc7a773'))
            resolve, file = archives.from_cartridge(data)
            old_archive = file(delta.file_id)
            rebuilt = archives.apply_members(old_archive, delta.replacements())
            with self.subTest(language=language):
                self.assertEqual((len(old_archive), len(rebuilt)), (452112, 452112))
                self.assertEqual(archives._geometry(old_archive)[1], archives._geometry(rebuilt)[1])
                self.assertEqual(archives.verify_members(old_archive, rebuilt, delta.replacements()),
                                 {'members': len(raw), 'changed': [VIEWER_MEMBER]})
                self.assertEqual(archives.members(rebuilt)[GUARD_MEMBER], raw[GUARD_MEMBER])
                repair.check(VIEWER_MEMBER, raw[VIEWER_MEMBER], row.after, language)
                archives.check_semantics(delta, old_archive, rebuilt, language)
                replay = archives.rederive(data, language, None, [delta.record()])
                self.assertEqual([item.record() for item in replay], [delta.record()])
            records.append(delta.record())
        self.assertEqual(records[0], records[1])

    def test_writer_checker_and_replay_reject_reapplication_mutants_and_foreign_identity(self):
        from sgp131 import gs_cup_guard as repair
        self.assertTrue(hasattr(repair, 'derive') and hasattr(repair, 'check'))
        data, raw, commands = inputs('EN')
        before = raw[VIEWER_MEMBER]
        after = repair.patch_member(before, 'EN', commands)
        with self.assertRaises(ValueError):
            repair.patch_member(after, 'EN', commands)
        for at in (0, 0x780, 0x8E7, 0x8EE, 0x8F3, len(before) - 1):
            foreign = bytearray(before)
            foreign[at] ^= 1
            with self.subTest(writer_mutant=hex(at)), self.assertRaises(ValueError):
                repair.patch_member(bytes(foreign), 'EN', commands)
        for at in (0, 0x780, 0x8E7, 0x8EE, 0x8F3, len(after) - 1):
            mutant = bytearray(after)
            mutant[at] ^= 1
            with self.subTest(checker_mutant=hex(at)), self.assertRaises(ValueError):
                repair.check(VIEWER_MEMBER, before, bytes(mutant), 'EN')
        for args in ((GUARD_MEMBER, before, after, 'EN'),
                     (VIEWER_MEMBER, before + b'\0', after, 'EN'),
                     (VIEWER_MEMBER, before, after, 'FR')):
            with self.assertRaises(ValueError):
                repair.check(*args)
        delta = repair.derive(data, 'EN')
        record = delta.record()
        record['members'][0]['after_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            archives.rederive(data, 'EN', None, [record])

    def test_stage_owns_the_archive_repair_once(self):
        from sgp131 import mechanics_stages
        producers = mechanics_stages.require_stage('legacy').archive_producers
        self.assertEqual(producers.count('gs-cup-guard'), 1)


if __name__ == '__main__':
    unittest.main()
