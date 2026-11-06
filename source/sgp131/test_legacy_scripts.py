"""Class B: execute decoded, pinned cartridge bytecode in a deliberately small Python model.

This is not ARM, the game, a save test or an emulator. UI/scheduling commands are
recorded only; Bag APIs use explicit scenario inputs. Unsupported commands fail.
The standard 2009/2033 calls use real member-3 bytecode, not assumed returns.
Set SGP_LEGACY_BASELINE=1 to run the desired behavior against inherited bytes.
"""
import hashlib
import copy
import os
from pathlib import Path
import struct
import unittest

import ndspy.narc
import ndspy.rom

from sgp131 import gifts_audit, gifts_scripts as GS

ROOT = Path(__file__).resolve().parents[2]
ROM_HASHES = {'EN': '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
              'IT': '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'}
CACHE = {}


def inputs(language):
    if language not in CACHE:
        path = Path(os.environ.get('SGP_LEGACY_ROM_' + language) or ROOT / 'local' / 'experiments' /
                    'balance493-2026-10-28' / ('candidate-v4-' + language + '.nds'))
        pret = Path(os.environ.get('SGP_PRET_SOURCE') or ROOT / 'local' / 'tools' / 'pokeheartgold')
        metadata = pret / 'tools' / 'py_scripts' / 'scrcmd.json'
        if not path.is_file() or not metadata.is_file():
            reason = 'legacy V4 cartridge or pinned command metadata unavailable'
            if os.environ.get('SGP_LEGACY_REQUIRE_INPUTS') == '1':
                raise AssertionError(reason)
            raise unittest.SkipTest(reason)
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != ROM_HASHES[language]:
            raise AssertionError('legacy candidate identity differs from pinned V4')
        rom = ndspy.rom.NintendoDSRom(data)
        raw = [bytes(x) for x in ndspy.narc.NARC(rom.getFileByName('a/0/1/2')).files]
        commands = gifts_audit.load_commands(metadata)
        if commands.metadata_sha256 != 'fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a':
            raise AssertionError('legacy command metadata differs from pinned reference')
        CACHE[language] = (data, raw, commands)
    return CACHE[language]


def candidate(raw, language, member, commands):
    if os.environ.get('SGP_LEGACY_BASELINE') == '1':
        return raw
    from sgp131 import legacy_scripts
    return legacy_scripts.patch_member(raw, language, member, commands)


class BytecodeModel:
    """Bounded model of only the opcodes reached by these scenarios; no target execution.

    Given APIs: lead species, game version, badge, battle outcome, Bag space and
    current quantity. Bag capacity behavior is the scenario oracle, not a native
    implementation. The model's log records the actual decoded API operands.
    """
    UI = {'PlaySE', 'LockAll', 'FacePlayer', 'BufferPlayersName', 'BufferMonSpeciesName',
          'ApplyMovement', 'WaitMovement', 'WaitButton', 'CloseMsg', 'ReleaseAll',
          'ScrCmd_452', 'ScrCmd_453', 'PlayCry', 'WaitSE', 'FadeScreen', 'PlayFanfare',
          'WaitFanfare', 'BufferItemName', 'BufferItemNamePlural', 'BufferPocketName',
          'GenderMsgBox', 'TouchscreenMenuHide', 'TouchscreenMenuShow',
          'RegisterGearNumber'}

    def __init__(self, raw, commands, member, *, flags=(), variables=None, lead=380,
                 version=7, badge=False, won=False, space=True, quantity=0,
                 capacity=999, menu=1):
        self.commands, self.member = commands, member
        self.members = {m: GS.decode(b, commands, m) for m, b in raw.items()}
        self.flags, self.vars = set(flags), dict(variables or {})
        self.lead, self.version, self.badge, self.won = lead, version, badge, won
        self.space, self.quantity, self.capacity, self.menu = space, quantity, capacity, menu
        self.cmp, self.log, self.stack, self.hidden = -1, [], [], []
        self.gives, self.requests, self.messages = [], [], []
        self.whiteout_flags = None

    def value(self, operand):
        return self.vars.get(operand, 0) if operand >= 0x4000 else operand

    def condition(self, code):
        return {0: self.cmp < 0, 1: self.cmp == 0, 2: self.cmp > 0,
                3: self.cmp <= 0, 4: self.cmp >= 0, 5: self.cmp != 0}[code]

    def run(self, start=None, stop_on=(), steps=1500):
        self.pc = self.members[self.member].entry[0] if start is None else start
        for _ in range(steps):
            ins = self.members[self.member].istruzioni.get(self.pc)
            if ins is None:
                raise AssertionError(f'model PC {self.member}:{self.pc:#x} outside decoded code')
            name, args = ins.nome, ins.args
            self.log.append((self.member, ins.off, name, list(args)))
            if name in stop_on:
                return self
            self.pc = ins.fine
            target = ins.rami[0][1] if ins.rami else None
            if name == 'End':
                if not self.stack:
                    return self
                self.member, self.pc = self.stack.pop()
            elif name == 'WhiteOut':
                self.whiteout_flags = set(self.flags)
                return self
            elif name == 'GoTo':
                self.pc = target
            elif name in ('Call', 'CallIf'):
                if name == 'Call' or self.condition(args[0]):
                    self.stack.append((self.member, self.pc))
                    self.pc = target
            elif name == 'GoToIf':
                if self.condition(args[0]):
                    self.pc = target
            elif name == 'Return':
                self.member, self.pc = self.stack.pop()
            elif name == 'CheckFlag':
                self.cmp = 0 if args[0] in self.flags else -1
            elif name == 'SetFlag':
                self.flags.add(args[0])
            elif name == 'ClearFlag':
                self.flags.discard(args[0])
            elif name in ('CompareVarToValue', 'CompareVarToVar'):
                # pret ScrCmd_CompareVarToVar dereferences BOTH operands before Compare.
                a = self.value(args[0])
                b = self.value(args[1]) if name == 'CompareVarToVar' else args[1]
                self.cmp = (a > b) - (a < b)
            elif name == 'SetVar':
                self.vars[args[0]] = args[1]
            elif name == 'CopyVar':
                self.vars[args[0]] = self.value(args[1])
            elif name == 'CheckBattleWon':
                self.vars[args[0]] = int(self.won)
            elif name == 'TrainerBattle':
                pass  # outcome is supplied independently, not simulated
            elif name == 'CheckBadge':
                self.vars[args[1]] = int(self.badge)
            elif name == 'GetGameVersion':
                self.vars[args[0]] = self.version
            elif name == 'GetPartyLeadAlive':
                self.vars[args[0]] = 0
            elif name == 'GetPartyMonSpecies':
                self.vars[args[1]] = self.lead
            elif name == 'GetMenuChoice':
                self.vars[args[0]] = self.menu
            elif name == 'GetItemPocket':
                self.vars[args[1]] = 7 if self.value(args[0]) == 536 else 0
            elif name == 'GetItemQuantity':
                self.vars[args[1]] = self.quantity
            elif name == 'HasSpaceForItem':
                self.requests.append((self.value(args[0]), self.value(args[1])))
                self.vars[args[2]] = int(self.space)
            elif name == 'GiveItem':
                item, qty = self.value(args[0]), self.value(args[1])
                added = min(qty, max(0, self.capacity - self.quantity)) if self.space else 0
                self.quantity += added
                self.gives.append((item, qty, added))
                self.vars[args[2]] = int(added > 0)
                self.vars[0x800A] = int(added < qty)
            elif name == 'HidePerson':
                self.hidden.append(self.value(args[0]))
            elif name == 'NPCMsg':
                self.messages.append((self.member, args[0]))
            elif name == 'MsgBoxExtern':
                self.messages.append((self.value(args[0]), self.value(args[1])))
            elif name == 'CallStd':
                standard = args[0]
                if standard == 2001:
                    continue  # item-ball bookkeeping is opaque; HidePerson/GiveItem observed separately
                if standard not in (2009, 2033):
                    raise AssertionError(f'unsupported standard {standard}')
                self.stack.append((self.member, self.pc))
                self.member, self.pc = 3, self.members[3].entry[standard - 2000]
            elif name == 'RestartCurrentScript':
                pass  # model serializes the standard context; its End resumes caller
            elif name == 'ItemIsTMOrHM':
                self.vars[args[1]] = 0
            elif name not in self.UI:
                raise AssertionError(f'unsupported model opcode {name} at {self.member}:{ins.off:#x}')
        raise AssertionError('model step budget exhausted')


class RealLegacyPaths(unittest.TestCase):
    def fixture(self, language, member, repaired=True, **kwargs):
        _, raw, commands = inputs(language)
        selected = candidate(raw[member], language, member, commands) if repaired else raw[member]
        return BytecodeModel({member: selected, 3: raw[3]}, commands, member, **kwargs)

    def test_pickup_requests_one_full_heal_in_both_languages(self):
        # A wrong operand is observed at the actual HasSpaceForItem boundary.
        for language in ('EN', 'IT'):
            vm = self.fixture(language, 141).run(start=0x862, stop_on=('HasSpaceForItem',))
            ins = vm.log[-1]
            with self.subTest(language=language):
                self.assertEqual((vm.value(ins[3][0]), vm.value(ins[3][1])), (27, 1))

    def test_pickup_space_and_stack_saturation_keep_the_existing_bag_contract(self):
        # A changed request larger than one, a give despite no slot or a lost HidePerson is observable.
        for language in ('EN', 'IT'):
            for quantity in (0, 563, 564, 900, 998, 999):
                vm = self.fixture(language, 141, quantity=quantity).run(start=0x862, stop_on=('ItemIsTMOrHM',))
                with self.subTest(language=language, quantity=quantity):
                    self.assertEqual(vm.requests, [(27, 1)])
                    self.assertEqual(vm.gives, [(27, 1, 0 if quantity == 999 else 1)])
                    self.assertEqual(len(vm.hidden), 1)
            vm = self.fixture(language, 141, space=False).run(start=0x862)
            with self.subTest(language=language, no_slot=True):
                self.assertEqual((vm.gives, vm.hidden), ([], []))
                self.assertIn((141, 4), vm.messages)  # item balls use their own bank199 Bag-full row

    def test_each_loss_branch_hides_friend_before_whiteout_and_keeps_retry(self):
        # Forgetting any of the three loss edges or moving SetFlag after WhiteOut fails.
        for language in ('EN', 'IT'):
            for start in (0x338, 0x3DD, 0x4E0):
                vm = self.fixture(language, 93, variables={0x40F8: 0}, won=False).run(start=start)
                with self.subTest(language=language, battle=hex(start)):
                    self.assertIsNotNone(vm.whiteout_flags)
                    self.assertIn(712, vm.whiteout_flags)
                    self.assertEqual(vm.vars[0x40F8], 0)
                    self.assertEqual(vm.flags, {712})

    def test_regigigas_does_not_preempt_a_matching_unrewarded_lati(self):
        # This fails on the inherited early branch to NPCMsg23.
        for language in ('EN', 'IT'):
            for version, species in ((7, 380), (8, 381)):
                vm = self.fixture(language, 757, flags={16313, 16284, 775},
                                  lead=species, version=version).run()
                with self.subTest(language=language, version=version):
                    self.assertEqual(vm.gives, [(536, 1, 1)])
                    self.assertIn(16312, vm.flags)
                    self.assertNotIn((757, 23), vm.messages)

    def test_bag_full_keeps_enigma_reward_pending_in_both_lati_branches(self):
        # The inherited CallStd2033 loses the gift and then sets the once flag.
        for language in ('EN', 'IT'):
            for version, species in ((7, 380), (8, 381)):
                vm = self.fixture(language, 757, flags={16313, 16284}, lead=species,
                                  version=version, space=False).run()
                with self.subTest(language=language, version=version):
                    self.assertNotIn(16312, vm.flags)
                    self.assertEqual(vm.gives, [])
                    self.assertIn((3, 27), vm.messages)  # actual standard2009 native bag-full message

    def test_reward_is_given_once_and_retry_after_bag_full_remains_possible(self):
        for language in ('EN', 'IT'):
            vm = self.fixture(language, 757, flags={16313, 16284, 775}, space=False).run()
            retry = self.fixture(language, 757, flags=vm.flags).run()
            again = self.fixture(language, 757, flags=retry.flags).run()
            with self.subTest(language=language):
                self.assertEqual(retry.gives, [(536, 1, 1)])
                self.assertEqual(again.gives, [])
                self.assertIn((757, 23), again.messages)

    def test_other_regigigas_states_retain_the_original_dialogue_and_battle_offer(self):
        # Reordering 3FCA/3FB8 unconditionally would break this matrix.
        for language in ('EN', 'IT'):
            for extra in (set(), {16330}, {16312}, {16330, 16312}):
                for version, matching in ((7, 380), (8, 381)):
                    for lead in (0, 1, 380, 381):
                        for badge in (False, True):
                            if not extra and lead == matching:
                                continue
                            flags = {16313, 16284, 775} | extra
                            old = self.fixture(language, 757, repaired=False, flags=flags, lead=lead,
                                               badge=badge, version=version).run()
                            new = self.fixture(language, 757, flags=flags, lead=lead,
                                               badge=badge, version=version).run()
                            with self.subTest(language=language, extra=extra, lead=lead, badge=badge, version=version):
                                self.assertEqual((new.messages, new.gives, new.flags), (old.messages, old.gives, old.flags))

    def test_lati_then_regigigas_also_preserves_the_completed_reward(self):
        for language in ('EN', 'IT'):
            rewarded = self.fixture(language, 757, flags={16313, 16284}).run()
            later = self.fixture(language, 757, flags=rewarded.flags | {775}, badge=True).run()
            with self.subTest(language=language):
                self.assertEqual(rewarded.gives, [(536, 1, 1)])
                self.assertEqual(later.gives, [])
                self.assertIn((757, 23), later.messages)
                self.assertIn((757, 24), later.messages)

    def test_introduction_and_hoenn_gift_still_precede_lati_priority(self):
        for language in ('EN', 'IT'):
            for flags in (set(), {775}, {16313}, {16313, 775}):
                old = self.fixture(language, 757, repaired=False, flags=flags).run(stop_on=('NPCMsg',))
                new = self.fixture(language, 757, flags=flags).run(stop_on=('NPCMsg',))
                with self.subTest(language=language, flags=flags):
                    self.assertEqual(old.log[-1][2:], new.log[-1][2:])
                    self.assertEqual(old.flags, new.flags)

    def test_without_regigigas_nonreward_dialogues_are_identical(self):
        for language in ('EN', 'IT'):
            for extra in (set(), {16330}, {16312}, {16330, 16312}):
                for lead in (1, 381):
                    flags = {16313, 16284} | extra
                    old = self.fixture(language, 757, repaired=False, flags=flags, lead=lead).run()
                    new = self.fixture(language, 757, flags=flags, lead=lead).run()
                    with self.subTest(language=language, flags=flags, lead=lead):
                        self.assertEqual((new.messages, new.gives, new.flags), (old.messages, old.gives, old.flags))

    def test_old_bag_full_path_attempts_the_give_and_consumes_the_once_flag(self):
        # SG-15b root: real standard2033 bytecode overwrites GiveItem's result with GetItemPocket.
        vm = self.fixture('EN', 757, repaired=False, flags={16313, 16284}, space=False).run()
        self.assertEqual(vm.gives, [(536, 1, 0)])
        self.assertIn(16312, vm.flags)
        names = [name for member, _, name, _ in vm.log if member == 3]
        self.assertIn('GiveItem', names)
        self.assertIn('GetItemPocket', names)
        self.assertNotIn('HasSpaceForItem', names)

    def test_kurt_bag_full_preserves_the_completed_batch_and_success_still_delivers(self):
        for language in ('EN', 'IT'):
            variables = {0x8004: 17, 0x8000: 50}
            old = self.fixture(language, 874, repaired=False, space=False,
                               variables=variables, quantity=950).run(
                start=0x1BA, stop_on=('ClearKurtApricorn',))
            fixed = self.fixture(language, 874, space=False,
                                 variables=variables, quantity=950).run(start=0x1BA)
            success = self.fixture(language, 874, space=True,
                                   variables=variables, quantity=949).run(
                start=0x1BA, stop_on=('ClearKurtApricorn',))
            with self.subTest(language=language):
                self.assertEqual(old.gives, [(old.value(0x8004), old.value(0x8000), 0)])
                self.assertEqual(old.log[-1][2], 'ClearKurtApricorn')
                self.assertEqual(fixed.gives, [])
                self.assertIn((874, 9), fixed.messages)
                self.assertNotIn('ClearKurtApricorn', [row[2] for row in fixed.log])
                self.assertEqual(success.log[-1][2], 'ClearKurtApricorn')
                self.assertEqual(success.gives[-1], (17, 50, 50))
                self.assertEqual(success.quantity, 999)

    def test_pryce_tm07_saturation_keeps_the_reward_pending_in_both_blocks(self):
        for language in ('EN', 'IT'):
            for old_start, fixed_start in ((0x8C, 0xAA), (0x14A, 0x182)):
                old = self.fixture(language, 932, repaired=False, space=True,
                                   quantity=99, capacity=99).run(start=old_start)
                fixed = self.fixture(language, 932, space=True,
                                     quantity=99, capacity=99).run(start=fixed_start)
                with self.subTest(language=language, start=hex(old_start)):
                    self.assertEqual(old.gives, [(334, 1, 0)])
                    self.assertIn(210, old.flags)
                    self.assertEqual(old.vars[0x800A], 0,
                                     'standard 2033 clears the transient discard marker')
                    self.assertEqual(fixed.gives, [])
                    self.assertNotIn(210, fixed.flags)
                    self.assertIn((3, 27), fixed.messages)

    def test_pryce_retry_after_freeing_one_tm_slot_delivers_once(self):
        for language in ('EN', 'IT'):
            pending = self.fixture(language, 932, badge=True, space=True,
                                   quantity=99, capacity=99).run(start=0x23)
            retry = self.fixture(language, 932, badge=True, flags=pending.flags,
                                 space=True, quantity=98, capacity=99).run(start=0x23)
            again = self.fixture(language, 932, badge=True, flags=retry.flags,
                                 space=True, quantity=98, capacity=99).run(
                                     start=0x23, stop_on=('NPCMsg',))
            with self.subTest(language=language):
                self.assertNotIn(210, pending.flags)
                self.assertEqual(retry.gives, [(334, 1, 1)])
                self.assertEqual(retry.quantity, 99)
                self.assertIn(210, retry.flags)
                self.assertEqual(again.gives, [])
                self.assertEqual(again.log[-1][3], [5])


class IndependentReadBack(unittest.TestCase):
    def setUp(self):
        from sgp131 import legacy_scripts
        self.module = legacy_scripts
        _, self.raw, self.commands = inputs('EN')

    def fixed(self, member):
        return self.module.patch_member(self.raw[member], 'EN', member, self.commands)

    def test_foreign_and_already_repaired_members_cannot_be_repaired_again(self):
        for member in (93, 141, 757, 874, 932):
            for raw in (self.raw[member] + b'\0', self.fixed(member)):
                with self.subTest(member=member), self.assertRaisesRegex(ValueError, 'preimage'):
                    self.module.patch_member(raw, 'EN', member, self.commands)
        for language, member in (('FR', 93), ('EN', 890), ('EN', '93')):
            with self.subTest(language=language, member=member), self.assertRaises(ValueError):
                self.module.patch_member(self.raw[93], language, member, self.commands)

    def test_every_entry_relative_edge_and_complementary_byte_is_guarded(self):
        for member in (93, 141, 757, 874, 932):
            good = self.fixed(member)
            self.module.verify_member(self.raw[member], good, 'EN', member, self.commands)
            decoded = GS.decode(good, self.commands, member)
            relative = next(ins for ins in decoded.istruzioni.values() if ins.rami and ins.nome == 'GoToIf')
            for label, mutate in (
                ('entry table', lambda b: b.__setitem__(0, b[0] ^ 1)),
                ('movement or uncovered tail', lambda b: b.__setitem__(-1, b[-1] ^ 1)),
                ('branch operand', lambda b: b.__setitem__(relative.off + 3, b[relative.off + 3] ^ 2)),
                ('trailing byte', lambda b: b.extend(b'\0')),
                ('truncated', lambda b: b.__delitem__(-1)),
            ):
                altered = bytearray(good)
                mutate(altered)
                with self.subTest(member=member, mutant=label), self.assertRaises(ValueError):
                    self.module.verify_member(self.raw[member], bytes(altered), 'EN', member, self.commands)

    def test_loss_edge_cannot_skip_the_new_cleanup_even_if_it_targets_valid_code(self):
        good = bytearray(self.fixed(93))
        # Original loss branch at34A: point to the real, valid WhiteOut at557, skipping SetFlag.
        struct.pack_into('<I', good, 0x34D, 0x557 - 0x351)
        parsed = GS.decode(bytes(good), self.commands, 93)
        self.assertEqual(parsed.istruzioni[0x34A].rami[0][1], 0x557)
        with self.assertRaisesRegex(ValueError, 'relative target'):
            self.module.verify_member(self.raw[93], bytes(good), 'EN', 93, self.commands)

    def test_lati_and_space_guard_mutations_fail_independent_semantic_matching(self):
        good = self.fixed(757)
        parsed = GS.decode(good, self.commands, 757)
        sites = [i.off + 2 for i in parsed.istruzioni.values()
                 if i.nome == 'HasSpaceForItem'] + [0x39]
        for site in sites:
            bad = bytearray(good)
            bad[site] ^= 1
            with self.subTest(site=hex(site)), self.assertRaises(ValueError):
                self.module.verify_member(self.raw[757], bytes(bad), 'EN', 757, self.commands)

    def test_kurt_space_guard_mutations_fail_independent_semantic_matching(self):
        good = self.fixed(874)
        parsed = GS.decode(good, self.commands, 874)
        guard = next(i for i in parsed.istruzioni.values()
                     if i.nome == 'CompareVarToValue' and i.args == [0x800C, 0])
        for site in (guard.off + 2, guard.fine + 3):
            bad = bytearray(good)
            bad[site] ^= 1
            with self.subTest(site=hex(site)), self.assertRaises(ValueError):
                self.module.verify_member(self.raw[874], bytes(bad), 'EN', 874, self.commands)

    def test_pryce_quantity_retry_and_once_flag_mutations_fail_readback(self):
        good = self.fixed(932)
        parsed = GS.decode(good, self.commands, 932)
        quantity = [i for i in parsed.istruzioni.values()
                    if i.nome == 'GetItemQuantity' and i.args == [334, 0x800C]]
        checks = [i for i in parsed.istruzioni.values()
                  if i.nome == 'CompareVarToValue' and i.args == [0x800C, 99]]
        once = [i for i in parsed.istruzioni.values()
                if i.nome in ('CheckFlag', 'SetFlag') and i.args == [210]]
        self.assertEqual((len(quantity), len(checks), len(once)), (2, 2, 3))
        for ins in (*quantity, *checks, *once):
            bad = bytearray(good)
            bad[ins.off + 2] ^= 1
            with self.subTest(command=ins.nome, site=hex(ins.off)), self.assertRaises(ValueError):
                self.module.verify_member(self.raw[932], bytes(bad), 'EN', 932, self.commands)

    def test_a_different_metadata_identity_is_not_accepted(self):
        commands = copy.copy(self.commands)
        commands.metadata_sha256 = '0' * 64
        with self.assertRaisesRegex(ValueError, 'metadata'):
            self.module.patch_member(self.raw[93], 'EN', 93, commands)

    def test_all_movement_targets_preserve_the_native_halfword_alignment(self):
        # ApplyMovement hands its pointer directly to a reader using LDRH, not ScriptReadHalfword.
        for language in ('EN', 'IT'):
            _, raw, commands = inputs(language)
            for member in (93, 141, 757, 874, 932):
                before = GS.decode(raw[member], commands, member)
                after = GS.decode(self.module.patch_member(raw[member], language, member, commands), commands, member)
                with self.subTest(language=language, member=member):
                    self.assertTrue(all(p % 2 == 0 for p in before.dati_movimento))
                    self.assertTrue(all(p % 2 == 0 for p in after.dati_movimento),
                                    f'unaligned native movement pointers: {sorted(after.dati_movimento)}')

    def test_the_actual_native_movement_reader_uses_halfwords_at_the_target_pointer(self):
        from sgp131.gifts_audit import Arm9View
        data, _, _ = inputs('EN')
        view = Arm9View(data)
        # Actual instructions: LDRH r1,[r1]; LDRH r1,[r3,#2]; LDRH r1,[r3,#4].
        self.assertEqual(view.read(0x020622E8, 2), bytes.fromhex('0988'))
        self.assertEqual(view.read(0x0206231C, 2), bytes.fromhex('5988'))
        self.assertEqual(view.read(0x0206232E, 2), bytes.fromhex('9988'))
        self.assertEqual(view.u32(0x020FAD00 + 4 * 94), 0x02041B05)
        # ApplyMovement: load script_ptr, add the decoded offset, pass directly to Create.
        self.assertEqual(view.read(0x02041B46, 10), bytes.fromhex('a968381c891920f062fb'))

    def test_compare_var_to_var_dereferences_both_real_bytecode_operands(self):
        # The existing member93 instruction at5BF compares VAR4001 against x800C.
        for a, b, result in ((380, 380, 0), (380, 381, -1), (381, 380, 1)):
            vm = BytecodeModel({93: self.raw[93]}, self.commands, 93,
                               variables={0x4001: a, 0x800C: b}).run(start=0x5BF, stop_on=('GoToIf',))
            with self.subTest(a=a, b=b):
                self.assertEqual(vm.cmp, result)

    def test_temp8002_has_no_live_consumer_in_old_steven_or_the_called_standards(self):
        # A value that the new gate overwrites must never carry old save/scene state downstream.
        for member, starts in ((757, None), (3, (9, 33))):
            parsed = GS.decode(self.raw[member], self.commands, member)
            entries = parsed.entry if starts is None else [parsed.entry[i] for i in starts]
            reachable = GS.forward_reach(parsed, self.commands, entries)
            self.assertFalse([(o, parsed.istruzioni[o].testo()) for o in reachable
                              if 0x8002 in parsed.istruzioni[o].args])

    def test_version_gate_preserves_all_non_seven_values_of_the_original_branch(self):
        for version in (0, 6, 7, 8, 65535):
            for lead in (380, 381):
                vm = RealLegacyPaths().fixture('EN', 757, flags={16313, 16284, 775},
                                               version=version, lead=lead).run()
                with self.subTest(version=version, lead=lead):
                    self.assertEqual(bool(vm.gives), lead == (380 if version == 7 else 381))

    def test_an_apply_movement_edge_cannot_target_an_odd_address(self):
        good = bytearray(self.fixed(757))
        parsed = GS.decode(bytes(good), self.commands, 757)
        movement = next(i for i in parsed.istruzioni.values() if i.nome == 'ApplyMovement')
        # The relative operand is after opcode+object; corrupt only its destination parity.
        relative_at = movement.off + 4
        value = struct.unpack_from('<I', good, relative_at)[0]
        struct.pack_into('<I', good, relative_at, (value + 1) & 0xFFFFFFFF)
        with self.assertRaises(ValueError):
            self.module.verify_member(self.raw[757], bytes(good), 'EN', 757, self.commands)


if __name__ == '__main__':
    unittest.main()
