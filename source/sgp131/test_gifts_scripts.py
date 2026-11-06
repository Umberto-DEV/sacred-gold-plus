"""ROM-free contracts of the guarded script rewriting used for gift delivery.

Everything here is a hand-written synthetic member over a synthetic command
table that has semantics only for the commands the fixture uses. The real
cartridge members are covered by test_gifts_audit_rom (Class B).
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

from sgp13 import mew
from sgp131 import gifts_scripts as gs

OPS = {
    'Nop': (0, [], False), 'End': (2, [], True), 'CallStd': (20, ['stdscr'], False),
    'GoTo': (22, ['script'], True), 'Call': (26, ['script'], False),
    'GoToIf': (28, ['condition', 'script'], False), 'SetFlag': (30, ['flag'], False),
    'CheckFlag': (32, ['flag'], False), 'WaitButton': (50, [], False), 'CloseMsg': (53, [], False),
    'PlayFanfare': (78, ['sound'], False), 'WaitFanfare': (79, [], False),
    'ApplyMovement': (94, ['object2', 'movement'], False), 'WaitMovement': (95, [], False),
    'ReleaseAll': (97, [], False), 'BufferMonSpeciesName': (193, [1, 'var'], False),
    'GetStdMsgNaix': (438, ['var', 'var'], False), 'MsgBoxExtern': (440, ['var', 'var'], False),
    'GiveRibbon': (481, ['var', 'ribbon'], False), 'SetVar': (41, ['var', 2], False),
    # liveness fixtures (real operation numbers): subroutines, the bridge opcode and a shared-variable context
    'Return': (27, [], True), 'CallIf': (29, ['condition', 'script'], False), 'RunScript': (19, [2], False),
    'CopyVar': (42, ['var', 'var'], False), 'NopVar490': (490, ['var'], False),
    'CompareVarToValue': (17, ['var', 2], False),
    'RestartCurrentScript': (21, [], False), 'ScriptOverlayCmd': (784, [1, 1], False),
    'SpecialMartBuy': (276, [], False), 'StartBattleRegulationMenuTask': (485, [], False),
    # party-guard fixtures (real operation numbers)
    'PlaySE': (73, ['sound'], False), 'LockAll': (96, [], False), 'FacePlayer': (104, [], False),
    'NPCMsg': (45, ['message'], False), 'BufferPlayersName': (190, [1], False), 'HidePerson': (101, ['object2'], False),
    'GetPartyCount': (332, ['var'], False), 'NicknameInput': (173, ['var', 'var'], False),
    'GiveMon': (137, ['species', 'var', 'var', 'var', 'var', 'var'], False), 'GetMenuChoice': (748, ['var'], False),
}
SIZES = {'stdscr': 2, 'script': 4, 'movement': 4, 'condition': 1, 'flag': 2, 'sound': 2,
         'object2': 2, 'var': 2, 'ribbon': 2, 'message': 1, 'species': 2}


def make_commands(directory, count=853):
    rows = [{'name': 'Unused', 'args': [], 'is_abs_branch': True} for _ in range(count)]
    for name, (op, args, stop) in OPS.items():
        rows[op] = {'name': name, 'args': args, 'is_abs_branch': stop}
    path = Path(directory) / 'commands.json'
    path.write_text(json.dumps({'commands': rows}))
    return mew.decoder().Comandi(path)


class Assembler:
    """Tiny two-pass assembler: ('Name', arg...) tuples, ('label', name), ('raw', bytes)."""

    def __init__(self, entries):
        self.entries = entries
        self.items = []

    def add(self, *item):
        self.items.append(item)
        return self

    def build(self):
        labels, size = {}, 0
        for item in self.items:
            if item[0] == 'label':
                labels[item[1]] = size
            elif item[0] == 'raw':
                size += len(item[1])
            else:
                op, args, _ = OPS[item[0]]
                size += 2 + sum(SIZES[k] if isinstance(k, str) else k for k in args)
        header_end = 4 * len(self.entries) + 2
        out = bytearray()
        for item in self.items:
            if item[0] == 'label':
                continue
            if item[0] == 'raw':
                out += item[1]
                continue
            op, kinds, _ = OPS[item[0]]
            out += struct.pack('<H', op)
            for kind, value in zip(kinds, item[1:]):
                width = SIZES[kind] if isinstance(kind, str) else kind
                if kind in ('script', 'movement'):
                    here = len(out) + 4
                    value = (labels[value] - here) & 0xFFFFFFFF
                out += int(value).to_bytes(width, 'little')
        table = b''.join(struct.pack('<I', (header_end + labels[name]) - (4 * i + 4))
                         for i, name in enumerate(self.entries))
        # label offsets above are body-relative; relative operands only need differences
        return table + struct.pack('<H', 0xFD13) + bytes(out)


def ribbon_fixture(ribbon=60, sound=20, branch_interior=False, extra_branch_to_close=True,
                   bag_tail=True, second_error=False, messages=(32, 34), dead_goto=None):
    a = Assembler(['start', 'award_entry', 'other'])
    a.add('label', 'start').add('CheckFlag', 2748).add('GoToIf', 1, 'done')
    if branch_interior:
        a.add('GoToIf', 1, 'interior')
    a.add('GoTo', 'award')
    a.add('label', 'done').add('End')
    a.add('label', 'award').add('label', 'award_entry')
    a.add('GetStdMsgNaix', 0, 0x800C).add('MsgBoxExtern', 0x800C, messages[0])
    a.add('BufferMonSpeciesName', 0, 0x8002).add('MsgBoxExtern', 0x800C, messages[1])
    a.add('GiveRibbon', 0x8002, ribbon)
    a.add('label', 'tail').add('PlayFanfare', sound)
    a.add('label', 'interior').add('raw', struct.pack('<H', 2009))
    a.add('label', 'close').add('CloseMsg').add('ReleaseAll').add('End')
    if bag_tail:
        a.add('label', 'bag').add('CallStd', 2009).add('CloseMsg').add('ReleaseAll').add('End')
    a.add('label', 'other')
    if extra_branch_to_close:
        a.add('GoToIf', 1, 'close').add('Call', 'bag' if bag_tail else 'done')
    if second_error:
        a.add('raw', struct.pack('<H', 2010))
    a.add('ApplyMovement', 255, 'move').add('WaitMovement').add('GoTo', 'tail').add('End')
    if dead_goto:
        a.add('GoTo', dead_goto)          # never reached by any entry
    a.add('label', 'move').add('raw', struct.pack('<HHHH', 0x21, 1, 0xFE, 0xFE))
    raw = a.build()
    return raw, a


def fixture_recipe(raw, member=7, ribbon=60, messages=(32, 34), sound=20):
    """Recipe for the synthetic member, with offsets measured on the fixture itself."""
    commands_dir = tempfile.TemporaryDirectory()
    commands = make_commands(commands_dir.name)
    old = mew.decoder().Membro(member, raw, commands).cammina()
    illegal = int([e for e in old.errori if ' 2009 ' in e][0].rsplit(' ', 1)[-1])
    tail = illegal - 4
    giver = [i for i in old.istruzioni.values() if i.fine == tail][0]
    commands_dir.cleanup()
    return {
        'reference': {'sound': 1185, 'daily_flag': 2748},
        'inherited_tail_hex': struct.pack('<HHH', 78, sound, 2009).hex(),
        'inherited_sound': sound,
        'kept_continuation_hex': struct.pack('<HHH', 53, 97, 2).hex(),
        'members': {str(member): {
            'preimage_sha256': {'EN': hashlib.sha256(raw).hexdigest()},
            'illegal_offset': illegal, 'tail_site': tail, 'ribbon_site': giver.off,
            'ribbon': ribbon, 'messages': list(messages)}},
    }


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.commands = make_commands(self.temp.name)
        self.raw, self.asm = ribbon_fixture()
        self.recipe = fixture_recipe(self.raw)
        self.member = self.recipe['members']['7']

    def decode(self, raw, allowed=()):
        return gs.decode(raw, self.commands, 7, allowed)


class Relocation(Base):
    def tail_edit(self):
        return gs.Edit(self.member['tail_site'], self.member['tail_site'] + 6, gs.replacement_bytes(self.recipe))

    def test_fixture_has_exactly_the_one_known_decoder_error(self):
        old = mew.decoder().Membro(7, self.raw, self.commands).cammina()
        self.assertEqual(old.errori, [f"opcode illegale 2009 a {self.member['illegal_offset']}"])

    def test_one_coordinate_transformation_remaps_entries_branches_and_movement(self):
        result, mapping, old = gs.relocate(self.raw, self.commands, [self.tail_edit()], 7,
                                           (f"opcode illegale 2009 a {self.member['illegal_offset']}",))
        new = self.decode(result)
        site = self.member['tail_site']
        self.assertEqual(len(result), len(self.raw) + 6)
        self.assertEqual(new.entry, [mapping(e) for e in old.entry])
        # an entry past the edit shifts by exactly the delta; before it stays
        self.assertEqual(new.entry[0], old.entry[0])
        self.assertEqual(new.entry[1], old.entry[1])
        for ins in old.istruzioni.values():
            if site <= ins.off < site + 6:
                continue
            other = new.istruzioni[mapping(ins.off)]
            self.assertEqual(other.rami, [(i, mapping(d), k) for i, d, k in ins.rami])
        movement = next(iter(old.dati_movimento))
        self.assertEqual(result[mapping(movement):mapping(movement) + 8], self.raw[movement:movement + 8])

    def test_branch_into_replaced_interior_refuses(self):
        raw, _ = ribbon_fixture(branch_interior=True)
        recipe = fixture_recipe(raw)
        with self.assertRaisesRegex(ValueError, 'interior'):
            gs.patch_member(raw, 'EN', 7, self.commands, recipe)

    def test_generic_relocation_refuses_a_branch_into_the_replaced_interior_without_the_recipe(self):
        raw, _ = ribbon_fixture(branch_interior=True)
        recipe = fixture_recipe(raw)
        member = recipe['members']['7']
        edit = gs.Edit(member['tail_site'], member['tail_site'] + 6, gs.replacement_bytes(recipe))
        with self.assertRaisesRegex(ValueError, 'interior'):
            gs.relocate(raw, self.commands, [edit], 7, (gs.expected_error(member),))
        mapping = gs.coordinate_map([edit])
        for offset in range(edit.start + 1, edit.end):
            with self.assertRaisesRegex(ValueError, 'interior'):
                mapping(offset)
        self.assertEqual(mapping(edit.start), edit.start)
        self.assertEqual(mapping(edit.end), edit.end + 6)

    def test_recipe_scan_refuses_an_interior_edge_even_if_relocation_were_lenient(self):
        raw, _ = ribbon_fixture(branch_interior=True)
        recipe = fixture_recipe(raw)
        member = recipe['members']['7']
        old = mew.decoder().Membro(7, raw, self.commands).cammina()
        with self.assertRaisesRegex(ValueError, 'interior'):
            gs.locate_tail(raw, old, member, recipe)

    def test_branch_to_replaced_start_and_retained_continuation_are_mapped(self):
        raw, asm = ribbon_fixture(extra_branch_to_close=True)
        recipe = fixture_recipe(raw)
        result = gs.patch_member(raw, 'EN', 7, self.commands, recipe)
        new = self.decode(result)
        old = mew.decoder().Membro(7, raw, self.commands).cammina()
        site = recipe['members']['7']['tail_site']
        # GoTo tail (the movement-script loop) must land on the new PlayFanfare; GoToIf close on CloseMsg
        targets = {(ins.nome, d) for ins in new.istruzioni.values() for _, d, k in ins.rami if k == 'script'}
        self.assertIn(('GoTo', site), targets)
        self.assertIn(('GoToIf', site + 12), targets)
        self.assertEqual(new.istruzioni[site].nome, 'PlayFanfare')
        self.assertEqual(new.istruzioni[site + 12].nome, 'CloseMsg')
        self.assertEqual(len(old.errori), 1)

    def test_dead_command_with_a_relative_operand_across_the_edit_refuses_instead_of_going_stale(self):
        # an unreachable GoTo behind the edit that points before it: the walk never sees it, so the
        # transformation could not rewrite it. It must be refused, not silently left with a stale operand.
        raw, _ = ribbon_fixture(dead_goto='award')
        recipe = fixture_recipe(raw)
        with self.assertRaisesRegex(ValueError, 'unreachable command'):
            gs.patch_member(raw, 'EN', 7, self.commands, recipe)
        # a dead command whose operand does NOT cross the edit shifts with its target and is harmless
        raw, _ = ribbon_fixture(dead_goto='move')
        recipe = fixture_recipe(raw)
        gs.patch_member(raw, 'EN', 7, self.commands, recipe)

    def test_overlapping_edits_refuse(self):
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            gs.relocate(self.raw, self.commands, [gs.Edit(10, 14, b'\0\0'), gs.Edit(12, 16, b'\0\0')], 7,
                        (f"opcode illegale 2009 a {self.member['illegal_offset']}",))

    def test_instruction_straddling_an_edit_refuses(self):
        site = self.member['ribbon_site']
        with self.assertRaisesRegex(ValueError, 'straddles'):
            gs.relocate(self.raw, self.commands, [gs.Edit(site + 2, site + 8, b'\0\0')], 7,
                        (f"opcode illegale 2009 a {self.member['illegal_offset']}",))

    def test_replacement_with_relative_operand_refuses(self):
        replacement = struct.pack('<HI', 22, 0)
        with self.assertRaisesRegex(ValueError, 'relative operand'):
            gs.relocate(self.raw, self.commands,
                        [gs.Edit(self.member['tail_site'], self.member['tail_site'] + 6, replacement)], 7,
                        (f"opcode illegale 2009 a {self.member['illegal_offset']}",))

    def test_unexpected_decoder_error_refuses_relocation(self):
        raw, _ = ribbon_fixture(second_error=True)
        with self.assertRaisesRegex(ValueError, 'decoding failed'):
            gs.relocate(raw, self.commands, [self.tail_edit()], 7,
                        (f"opcode illegale 2009 a {self.member['illegal_offset']}",))


class RibbonRecipe(Base):
    def patched(self):
        return gs.patch_member(self.raw, 'EN', 7, self.commands, self.recipe)

    def test_synthetic_tail_becomes_the_reference_award_trace(self):
        new = self.decode(self.patched())
        ribbon = new.istruzioni[self.member['ribbon_site']]
        trace = gs._trace_from(new, ribbon.off)
        self.assertEqual([n for n, _ in trace], ['GiveRibbon', 'PlayFanfare', 'WaitFanfare', 'SetFlag',
                                                'WaitButton', 'CloseMsg', 'ReleaseAll', 'End'])
        self.assertEqual(trace[1][1], [1185])
        self.assertEqual(trace[3][1], [2748])
        self.assertEqual(new.errori, [])

    def test_report_describes_a_net_six_byte_change_and_no_collateral(self):
        result = self.patched()
        report = gs.verify_member(self.raw, result, self.commands, self.recipe)
        self.assertEqual(report['output_bytes'] - report['input_bytes'], 6)
        self.assertEqual(report['language'], ['EN'])
        # the synthetic CloseMsg/ReleaseAll/End are already reachable through a branch: +3 only
        self.assertEqual(report['instructions_after'] - report['instructions_before'], 3)
        self.assertEqual(report['new_errors'], [])
        self.assertEqual(len(report['old_errors']), 1)

    def test_every_incoming_edge_of_the_synthetic_tail_is_accounted_for(self):
        old = mew.decoder().Membro(7, self.raw, self.commands).cammina()
        site = self.member['tail_site']
        edges = [e for e in gs.incoming_edges(old) + gs.entry_edges(old) if site <= e[1] < site + 12]
        # explicit edges: the movement-loop GoTo to the tail start and GoToIf to the retained close
        self.assertEqual(sorted((d - site) for _, d, _ in edges), [0, 6])

    def test_foreign_and_already_patched_input_refused(self):
        changed = bytearray(self.raw)
        changed[-1] ^= 1
        for raw in (self.patched(), bytes(changed)):
            with self.assertRaisesRegex(ValueError, 'preimage'):
                gs.patch_member(raw, 'EN', 7, self.commands, self.recipe)
        with self.assertRaisesRegex(ValueError, 'not part of the ribbon recipe'):
            gs.patch_member(self.raw, 'EN', 8, self.commands, self.recipe)
        with self.assertRaisesRegex(ValueError, 'language'):
            gs.patch_member(self.raw, 'IT', 7, self.commands, self.recipe)

    def test_recipe_mismatches_each_refuse(self):
        mutations = {
            'ribbon': lambda r: r['members']['7'].update(ribbon=61),
            'sound': lambda r: r.update(inherited_sound=21),
            'site': lambda r: r['members']['7'].update(tail_site=r['members']['7']['tail_site'] + 2),
            'messages': lambda r: r['members']['7'].update(messages=[1, 2]),
            'continuation': lambda r: r.update(kept_continuation_hex='3500610002ff'),
        }
        for name, mutate in mutations.items():
            recipe = copy.deepcopy(self.recipe)
            mutate(recipe)
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    gs.patch_member(self.raw, 'EN', 7, self.commands, recipe)

    def test_missing_bag_full_tail_refuses(self):
        raw, _ = ribbon_fixture(bag_tail=False)
        recipe = fixture_recipe(raw)
        with self.assertRaisesRegex(ValueError, 'bag-full'):
            gs.patch_member(raw, 'EN', 7, self.commands, recipe)

    def test_unrelated_second_decoder_error_blocks_the_repair(self):
        raw, _ = ribbon_fixture(second_error=True)
        recipe = fixture_recipe(raw)
        with self.assertRaises(ValueError):
            gs.patch_member(raw, 'EN', 7, self.commands, recipe)

    def test_verify_member_catches_each_class_of_wrong_output(self):
        good = self.patched()
        site = self.member['tail_site']
        flag_at = site + 2 + 2 + 2 + 2 + 2  # PlayFanfare(4) WaitFanfare(2) SetFlag opcode(2)
        mutants = {
            'wrong daily flag': lambda b: b.__setitem__(slice(flag_at, flag_at + 2), struct.pack('<H', 2749)),
            'wrong sound': lambda b: b.__setitem__(slice(site + 2, site + 4), struct.pack('<H', 1186)),
            'entry not remapped': lambda b: b.__setitem__(slice(4, 8), struct.pack('<I', 0)),
            'movement byte changed': lambda b: b.__setitem__(len(b) - 3, b[-3] ^ 1),
            'nonrelative operand changed': lambda b: b.__setitem__(slice(site - 4, site - 2), struct.pack('<H', 61)),
            'truncated': lambda b: b.__delitem__(slice(len(b) - 1, len(b))),
        }
        for name, mutate in mutants.items():
            data = bytearray(good)
            mutate(data)
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    gs.verify_member(self.raw, bytes(data), self.commands, self.recipe)

    def test_unknown_before_image_is_not_verifiable(self):
        with self.assertRaisesRegex(ValueError, 'not a known ribbon preimage'):
            gs.verify_member(self.raw + b'\0', self.patched(), self.commands, self.recipe)


def guard_fixture(bypass=False, branch_to_insert=False, existing_guard=False, reads_var=False, no_face=False,
                  dead_goto=False, second_error=False, odd_lead=False, buffer_slot=0):
    """A synthetic Eevee-like member: lead-in, text, GetPartyCount, GiveMon, a nickname branch and an unrelated entry."""
    a = Assembler(['npc', 'other'])
    a.add('label', 'npc').add('PlaySE', 1500).add('LockAll')
    if not no_face:
        a.add('FacePlayer')
    a.add('label', 'lead').add('BufferPlayersName', buffer_slot).add('NPCMsg', 1).add('NPCMsg', 2)
    if reads_var:
        a.add('CopyVar', 0x800C, 0x8005)
    if odd_lead:
        a.add('SetFlag', 77)
    a.add('label', 'count').add('GetPartyCount', 0x8005)
    a.add('GiveMon', 133, 5, 0, 0, 0, 0x800C).add('PlayFanfare', 1187).add('WaitFanfare').add('NPCMsg', 3)
    a.add('GetMenuChoice', 0x800C).add('CompareVarToValue', 0x800C, 0).add('GoToIf', 1, 'nick')
    a.add('HidePerson', 15).add('SetFlag', 16220).add('ReleaseAll').add('End')
    a.add('label', 'nick').add('NicknameInput', 0x8005, 0x4000).add('HidePerson', 15).add('SetFlag', 16220)
    a.add('ReleaseAll').add('End')
    a.add('label', 'other').add('SetFlag', 100).add('ApplyMovement', 255, 'move').add('WaitMovement')
    if existing_guard:
        a.add('CompareVarToValue', 0x8005, 6)          # a party-limit compare somewhere in the member
    if second_error:
        a.add('raw', struct.pack('<H', 2010))
    if bypass:
        a.add('GoTo', 'count')
    if branch_to_insert:
        a.add('GoTo', 'lead')
    a.add('End')
    if dead_goto:
        a.add('GoTo', 'npc')          # never reached: its operand points before the insertion
    a.add('label', 'move').add('raw', struct.pack('<HHHH', 0x21, 1, 0xFE, 0xFE))
    # Test-only .balign2: the native movement reader consumes u16 commands.
    # An odd source fixture would be invalid before the production transform.
    if a.build().rfind(struct.pack('<HHHH', 0x21, 1, 0xFE, 0xFE)) % 2:
        a.items.insert(-2, ('raw', b'\0'))
    return a.build(), a


def model_party_gift(raw, commands, entry, count, choice, player_name='PLAYER'):
    """Decode actual instructions; model only the Eevee path, never ARM/heap/UI.

    Count, menu choice and player name are supplied by the scenario. Message
    snapshots prove the duplicate buffer is idempotent at the point of use.
    GiveMon records arguments/result only, not a real Pokémon or saved party.
    """
    parsed, variables = gs.decode(raw, commands, 227), {0x8005: 0xA55A, 0x800C: 0xA55A, 0x4000: 0xA55A}
    buffers, messages, effects, calls = {0: 'untouched'}, [], [], []
    pc, comparison = parsed.entry[entry], -1
    quiet = {'PlaySE', 'LockAll', 'FacePlayer', 'PlayFanfare', 'WaitFanfare', 'WaitButton',
             'CloseMsg', 'ReleaseAll', 'FadeScreen', 'WaitFade', 'WaitSE',
             'TouchscreenMenuHide', 'TouchscreenMenuShow'}
    for _ in range(200):
        ins = parsed.istruzioni[pc]
        name, args, pc = ins.nome, ins.args, ins.fine
        calls.append((name, list(args)))
        if name == 'End':
            return {'variables': variables, 'buffers': buffers, 'messages': messages,
                    'effects': effects, 'calls': calls}
        if name == 'GetPartyCount':
            variables[args[0]] = count
        elif name == 'CompareVarToValue':
            comparison = variables[args[0]] - args[1]
        elif name == 'GoToIf':
            if args[0] != 1:
                raise AssertionError('unsupported non-equality condition in Eevee model')
            if comparison == 0:
                pc = ins.rami[0][1]
        elif name == 'SetVar':
            variables[args[0]] = args[1]
        elif name == 'BufferPlayersName':
            buffers[args[0]] = player_name
        elif name in ('NPCMsg', 'MsgBoxExtern'):
            messages.append((name, list(args), dict(buffers)))
        elif name == 'GiveMon':
            effects.append((name, list(args)))
            variables[args[-1]] = 1
        elif name == 'GetMenuChoice':
            variables[args[0]] = choice
        elif name == 'NicknameInput':
            effects.append((name, [variables[a] for a in args]))
        elif name in ('SetFlag', 'HidePerson'):
            effects.append((name, list(args)))
        elif name not in quiet:
            raise AssertionError('unsupported Eevee model opcode ' + name)
    raise AssertionError('Eevee model exceeded its bound')


def guard_recipe(raw, commands, **overrides):
    old = mew.decoder().Membro(7, raw, commands).cammina()
    named = lambda name: sorted(i.off for i in old.istruzioni.values() if i.nome == name)
    recipe = {
        'member': 7, 'preimage_sha256': {'EN': hashlib.sha256(raw).hexdigest()},
        'entry': 0, 'entry_offset': old.entry[0], 'insert_at': named('BufferPlayersName')[0],
        'lead_in': ['PlaySE', 'LockAll', 'FacePlayer'],
        'party_count_site': named('GetPartyCount')[0], 'give_site': named('GiveMon')[0],
        'party_var': 0x8005, 'species': 133, 'level': 5, 'limit': 6, 'result_var': 0x800C,
        'effects': {'flag': 16220, 'hide_person': 15},
        'message': {'bank': 25, 'index': 39},
    }
    recipe.update(overrides)
    return recipe


class GuardBase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.commands = make_commands(self.temp.name)

    def fixture(self, **kw):
        raw, _ = guard_fixture(**kw)
        return raw, guard_recipe(raw, self.commands)

    def names(self, member, start):
        """Command names along the fall-through from `start` up to the first terminator."""
        out, cursor = [], start
        while cursor in member.istruzioni:
            ins = member.istruzioni[cursor]
            out.append(ins.nome)
            if ins.nome in gs.TERMINATORS:
                break
            cursor = ins.fine
        return out


class PartyGuard(GuardBase):
    def fixed(self, **kw):
        raw, recipe = self.fixture(**kw)
        return raw, recipe, gs.transform_party_guard(raw, 'EN', self.commands, recipe)

    def test_the_guard_and_the_refusal_block_preserve_alignment_and_cost_34_bytes(self):
        raw, recipe, result = self.fixed()
        new = gs.decode(result, self.commands, 7)
        self.assertEqual(len(result), len(raw) + 34)
        at = recipe['insert_at']
        self.assertEqual(self.names(new, new.entry[0])[:7], ['PlaySE', 'LockAll', 'FacePlayer', 'GetPartyCount',
                                                              'CompareVarToValue', 'GoToIf', 'BufferPlayersName'])
        compare, jump = new.istruzioni[at + 4], new.istruzioni[at + 10]
        self.assertEqual((compare.args, jump.args[0]), ([0x8005, 6], 1))                       # EQ, as the retail GoToIfEq
        block = jump.rami[0][1]
        self.assertEqual(block, len(raw) + 20)
        self.assertEqual(self.names(new, block), ['MsgBoxExtern', 'WaitButton', 'CloseMsg', 'ReleaseAll', 'End'])
        self.assertEqual(new.istruzioni[block].args, [25, 39])

    def test_every_original_command_survives_in_order_and_the_other_entry_is_remapped(self):
        raw, recipe, result = self.fixed()
        old, new = gs.decode(raw, self.commands, 7), gs.decode(result, self.commands, 7)
        at = recipe['insert_at']
        shift = lambda o: o + 20 if o >= at else o
        self.assertEqual(new.entry, [shift(e) for e in old.entry])
        for ins in old.istruzioni.values():
            other = new.istruzioni[shift(ins.off)]
            self.assertEqual((other.op, other.tipi), (ins.op, ins.tipi))
            self.assertEqual(other.rami, [(i, shift(d), k) for i, d, k in ins.rami])
        movement = next(iter(old.dati_movimento))
        self.assertEqual(result[shift(movement):shift(movement) + 8], raw[movement:movement + 8])
        report = gs.verify_party_guard(raw, result, self.commands, recipe)
        self.assertEqual((report['inserted_bytes'], report['block_bytes']), (20, 14))
        self.assertEqual(report['instructions_after'] - report['instructions_before'], 9)
        self.assertTrue(all(p % 2 == 0 for p in new.dati_movimento))

    def test_the_effects_are_unreachable_when_the_guard_success_edge_is_cut(self):
        raw, recipe, result = self.fixed()
        new = gs.decode(result, self.commands, 7)
        goto = new.istruzioni[recipe['insert_at'] + 10]
        effects = gs._effect_sites(new, self.commands, {**recipe, 'give_site': recipe['give_site'] + 20})
        self.assertEqual(len(effects), 6)         # the give, the nickname offer, two hides and two flags
        self.assertFalse(effects & gs.forward_reach(new, self.commands, new.entry, cut=[(goto.off, goto.fine)]))
        self.assertTrue(effects <= gs.forward_reach(new, self.commands, new.entry))

    def test_the_other_entry_is_untouched(self):
        raw, recipe, result = self.fixed()
        old, new = gs.decode(raw, self.commands, 7), gs.decode(result, self.commands, 7)
        self.assertEqual(self.names(old, old.entry[1]), self.names(new, new.entry[1]))

    def test_foreign_already_patched_and_unsupported_input_is_refused(self):
        raw, recipe, result = self.fixed()
        changed = bytearray(raw)
        changed[-1] ^= 1
        for label, data, language, message in (('already patched', result, 'EN', 'preimage does not match'),
                                                ('changed byte', bytes(changed), 'EN', 'preimage does not match'),
                                                ('language', raw, 'IT', 'unsupported')):
            with self.subTest(label), self.assertRaisesRegex(ValueError, message):
                gs.transform_party_guard(data, language, self.commands, recipe)
        wrong = guard_recipe(raw, self.commands, preimage_sha256={'EN': '0' * 64})     # right member, wrong pinned hash
        with self.assertRaisesRegex(ValueError, 'preimage does not match'):
            gs.transform_party_guard(raw, 'EN', self.commands, wrong)

    def test_every_deviation_of_the_site_is_refused_by_its_own_rule(self):
        cases = {
            'no FacePlayer in the lead-in': (dict(no_face=True), 'lead-in|insertion point'),
            'a branch targets the insertion point': (dict(branch_to_insert=True), 'targets the insertion point'),
            'an existing party-limit compare': (dict(existing_guard=True), 'already exists'),
            'a command that reads the borrowed variable': (dict(reads_var=True), 'plain text'),
            'a persistent command between guard and count': (dict(odd_lead=True), 'plain text'),
            'another entry reaches the give': (dict(bypass=True), 'would bypass the guard'),
            'the immediate original buffer is another slot': (dict(buffer_slot=1), 'immediate original player-name buffer'),
        }
        for label, (kw, message) in cases.items():
            raw, _ = guard_fixture(**kw)
            recipe = guard_recipe(raw, self.commands)
            with self.subTest(label), self.assertRaisesRegex(ValueError, message):
                gs.transform_party_guard(raw, 'EN', self.commands, recipe)

    def test_every_recipe_number_is_checked_against_the_member(self):
        raw, recipe = self.fixture()
        mutations = {
            'entry offset': dict(entry_offset=recipe['entry_offset'] + 2),
            'insertion point': dict(insert_at=recipe['insert_at'] + 3),
            'lead-in': dict(lead_in=['PlaySE', 'FacePlayer', 'LockAll']),
            'count site': dict(party_count_site=recipe['party_count_site'] + 4),
            'give site': dict(give_site=recipe['give_site'] + 2),
            'party variable': dict(party_var=0x8004),
            'species': dict(species=134),
            'level': dict(level=6),
            'result variable': dict(result_var=0x800B),
            'entry index': dict(entry=1),
        }
        for label, override in mutations.items():
            with self.subTest(label), self.assertRaises(ValueError):
                gs.transform_party_guard(raw, 'EN', self.commands, guard_recipe(raw, self.commands, **override))

    def test_a_lead_in_command_that_reads_the_borrowed_variable_is_refused_by_the_variable_rule(self):
        """Only the variable rule can refuse: the command kind is allowed for this test, its operand is the variable."""
        raw, recipe = self.fixture(reads_var=True)
        with mock.patch.object(gs, 'GUARD_LEAD_INS', gs.GUARD_LEAD_INS + ('CopyVar',)):
            with self.assertRaisesRegex(ValueError, 'plain text'):
                gs.transform_party_guard(raw, 'EN', self.commands, recipe)
        # the same member is accepted when the lead-in is plain text again
        plain, plain_recipe = self.fixture()
        gs.transform_party_guard(plain, 'EN', self.commands, plain_recipe)

    def test_the_read_back_alone_catches_a_path_around_the_guard(self):
        """Only the control-flow proof can refuse: the site rules are switched off for a member with a bypassing entry."""
        raw, recipe = self.fixture(bypass=True)
        with mock.patch.object(gs, '_check_guard_site', lambda *a: None):
            with self.assertRaisesRegex(ValueError, 'unguarded path leads to the gift effects'):
                gs.transform_party_guard(raw, 'EN', self.commands, recipe)

    def test_a_dead_command_whose_operand_crosses_the_insertion_is_refused_not_left_stale(self):
        raw, recipe = self.fixture(dead_goto=True)
        with self.assertRaisesRegex(ValueError, 'unreachable command'):
            gs.transform_party_guard(raw, 'EN', self.commands, recipe)

    def test_a_member_with_another_decoder_error_is_refused(self):
        raw, recipe = self.fixture(second_error=True)
        with self.assertRaises(ValueError):
            gs.transform_party_guard(raw, 'EN', self.commands, recipe)

    def test_the_independent_read_back_catches_each_class_of_wrong_output(self):
        raw, recipe, good = self.fixed()
        at = recipe['insert_at']
        block = len(raw) + 20
        tail = len(good)
        mutants = {
            'limit 5 instead of 6': lambda b: b.__setitem__(slice(at + 8, at + 10), struct.pack('<H', 5)),
            'compare of another variable': lambda b: b.__setitem__(slice(at + 6, at + 8), struct.pack('<H', 0x8004)),
            'count of another variable': lambda b: b.__setitem__(slice(at + 2, at + 4), struct.pack('<H', 0x8004)),
            'branch on NE': lambda b: b.__setitem__(at + 12, 5),
            'branch to the wrong place': lambda b: b.__setitem__(slice(at + 13, at + 17), struct.pack('<I', 0)),
            'duplicate buffer uses another slot': lambda b: b.__setitem__(at + 19, 1),
            'message index': lambda b: b.__setitem__(slice(block + 4, block + 6), struct.pack('<H', 40)),
            'message bank': lambda b: b.__setitem__(slice(block + 2, block + 4), struct.pack('<H', 24)),
            'block without WaitButton': lambda b: b.__setitem__(slice(block + 6, block + 8), struct.pack('<H', 53)),
            'block ends in ReleaseAll': lambda b: b.__setitem__(slice(tail - 2, tail), struct.pack('<H', 97)),
            'truncated': lambda b: b.__delitem__(slice(tail - 1, tail)),
            'trailing byte': lambda b: b.extend(b'\0'),
            'entry not remapped': lambda b: b.__setitem__(slice(4, 8), struct.pack('<I', 0)),
            'original byte changed': lambda b: b.__setitem__(at + 20, b[at + 20] ^ 1),
            'movement byte changed': lambda b: b.__setitem__(slice(tail - 3, tail - 2), bytes([b[tail - 3] ^ 1])),
        }
        for label, mutate in mutants.items():
            data = bytearray(good)
            mutate(data)
            with self.subTest(label), self.assertRaises(ValueError):
                gs.verify_party_guard(raw, bytes(data), self.commands, recipe)

    def test_the_read_back_refuses_a_block_that_something_else_branches_to(self):
        """Only this rule can refuse: one extra edge into the block is injected into the edge list the read-back sees."""
        raw, recipe, good = self.fixed()
        block = len(raw) + 20
        real = gs.incoming_edges
        with mock.patch.object(gs, 'incoming_edges', lambda member: real(member) + [(0, block, 'script')]):
            with self.assertRaisesRegex(ValueError, 'reachable by something other'):
                gs.verify_party_guard(raw, good, self.commands, recipe)
        gs.verify_party_guard(raw, good, self.commands, recipe)

    def test_the_read_back_does_not_use_the_writers_guard_bytes_or_lengths(self):
        raw, recipe, good = self.fixed()
        with mock.patch.object(gs, '_guard_parts', side_effect=AssertionError('writer unavailable to checker')):
            result = gs.verify_party_guard(raw, good, self.commands, recipe)
        self.assertEqual(result['inserted_bytes'], 20)

    def test_the_success_only_buffer_is_identical_to_the_immediate_original(self):
        raw, recipe, good = self.fixed()
        at = recipe['insert_at']
        self.assertEqual(good[at + 17:at + 20], raw[at:at + 3])
        for count in range(7):
            old = model_party_gift(raw, self.commands, 0, count, 0)
            new = model_party_gift(good, self.commands, 0, count, 0)
            with self.subTest(count=count):
                if count < 6:
                    for key in ('variables', 'buffers', 'messages', 'effects'):
                        self.assertEqual(new[key], old[key])
                    self.assertEqual(sum(name == 'BufferPlayersName' for name, _ in new['calls']), 2)
                else:
                    self.assertEqual(new['effects'], [])
                    self.assertEqual(new['buffers'], {0: 'untouched'})
                    self.assertFalse(any(name == 'BufferPlayersName' for name, _ in new['calls']))

    def test_unknown_before_image_is_not_verifiable(self):
        raw, recipe, good = self.fixed()
        with self.assertRaisesRegex(ValueError, 'pinned preimage'):
            gs.verify_party_guard(raw + b'\0', good, self.commands, recipe)


class PublishedGuardRecipe(unittest.TestCase):
    def test_the_published_recipe_is_the_eevee_of_member_227(self):
        recipe = gs.load_guard_recipe()
        self.assertEqual((recipe['member'], recipe['entry'], recipe['entry_offset'], recipe['insert_at']),
                         (227, 11, 442, 450))
        self.assertEqual((recipe['party_count_site'], recipe['give_site']), (471, 475))
        self.assertEqual(recipe['preimage_sha256']['EN'], recipe['preimage_sha256']['IT'])
        self.assertEqual((recipe['message']['bank'], recipe['message']['index']), (25, 39))
        self.assertEqual((recipe['effects'], recipe['limit']), ({'flag': 16220, 'hide_person': 15}, 6))


class PublishedRecipe(unittest.TestCase):
    def test_recipe_pins_six_members_and_reference_tail_encoding(self):
        recipe = gs.load_recipe()
        self.assertEqual(sorted(recipe['members'], key=int), ['225', '232', '243', '246', '938', '962'])
        self.assertEqual(gs.replacement_bytes(recipe).hex(), '4e00a1044f001e00bc0a3200')
        self.assertEqual(recipe['inherited_tail_hex'], '4e001400d907')
        for key, member in recipe['members'].items():
            self.assertEqual(member['tail_site'] + 4, member['illegal_offset'], key)
            self.assertEqual(member['ribbon_site'] + 6, member['tail_site'], key)
            self.assertEqual(set(member['preimage_sha256']), {'EN', 'IT'})
            self.assertTrue(all(len(h) == 64 for h in member['preimage_sha256'].values()))

    def test_published_recipe_contains_no_game_bytes_beyond_the_defect_pattern(self):
        text = (Path(gs.__file__).parent / 'data' / 'gifts-claims.json').read_text()
        document = json.loads(text)
        self.assertLessEqual(len(text), 60_000)
        self.assertEqual(document['ribbon_tails']['kept_continuation_hex'], '350061000200')


class NoFakeOpcode(unittest.TestCase):
    def test_opcode2009_is_never_defined_by_the_metadata_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, '853'):
                make_commands(directory, count=854)
            commands = make_commands(directory)
            self.assertEqual(len(commands), 853)
            self.assertTrue(commands.nome(2009).startswith('ScrCmd_ILLEGALE'))
            member = Assembler(['a']).add('label', 'a').add('PlayFanfare', 20).add('raw', struct.pack('<H', 2009)).build()
            parsed = mew.decoder().Membro(0, member, commands).cammina()
            self.assertEqual(len(parsed.errori), 1)
            self.assertIn('2009', parsed.errori[0])


if __name__ == '__main__':
    unittest.main()
