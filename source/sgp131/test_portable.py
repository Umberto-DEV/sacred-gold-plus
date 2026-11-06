"""Portable box: host-side checks that need no ROM (pins file, ABI parity, trampoline encoding,
compiled payload measurements). Evidence level: host Python (+ clang compile); nothing here runs
ARM code and nothing here is Android evidence.

  PYTHONPATH=source python -m unittest sgp131.test_portable -v
"""
import hashlib
import json
import os
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import capstone

from sgp131 import portable
from sgp131.test_ui import nonproduction_native_compiler_contract
from sgp131 import test_controls as _test_controls

sys.path.insert(0, str(portable.FEATURE / 'test'))
import portable_bench as pb  # noqa: E402

FEATURE = portable.FEATURE
CHARMAP = portable.SOURCE.parent / 'local' / 'tools' / 'pokeheartgold' / 'charmap.txt'


def u32_fields(header, struct_name):
    """Field names, in order, of an all-u32 C struct typedef in abi.h (offset = 4 * index)."""
    body = re.search(r'typedef struct %s \{(.*?)\} %s;' % (struct_name, struct_name), header, re.S).group(1)
    names = []
    for line in body.splitlines():
        match = re.match(r'\s*u32 (\w+)(\[(\d+)\])?;', line)
        if match:
            names += [match.group(1)] * (int(match.group(3)) if match.group(3) else 1)
    return names


class PinsFile(unittest.TestCase):
    def setUp(self):
        self.pins = portable.abi()

    def test_en_it_pins_are_identical_and_well_formed(self):
        self.assertTrue(self.pins['en_it_identical'])
        self.assertEqual(self.pins['languages']['EN'], self.pins['languages']['IT'])
        self.assertEqual(self.pins['v4_inputs'], portable.V4_SHA256)
        for name, span in self.pins['languages']['EN']['spans'].items():
            self.assertRegex(span['sha256'], r'^[0-9a-f]{64}$', name)
            self.assertGreater(span['bytes'], 0, name)

    def test_pinned_hooks_match_the_installer_constants(self):
        spans = self.pins['languages']['EN']['spans']
        self.assertEqual(spans['state1_bl']['address'], portable.STATE1_BL)
        self.assertEqual(spans['launch_bl']['address'], portable.LAUNCH_BL)
        self.assertEqual(spans['print32_bl']['address'], portable.PRINT32_BL)
        self.assertEqual(spans['callback_entry12']['hex'], portable.CALLBACK_BEFORE.hex())
        self.assertEqual(spans['callback_entry12']['address'], portable.CALLBACK)
        self.assertEqual(spans['state1_bl']['hex'], '00f034f9')
        natives = self.pins['languages']['EN']['natives']
        self.assertEqual(natives['PartyMenu_Subtask_MainNormal']['address'], 0x02079308)
        self.assertEqual(natives['FieldSystem_LaunchApplication']['address'], 0x0203DFB4)
        self.assertEqual(natives['PartyMenu_PrintMessageOnWindowEx']['address'], 0x0207DA64)
        self.assertEqual(natives['TaskManager_GetFieldSystem']['address'], portable.GET_FIELD_SYSTEM)
        offsets = self.pins['offsets']
        self.assertEqual(offsets['PartyMenu.args'], 0x654)
        self.assertEqual(offsets['StartMenu.exitTaskEnvironment'], 0x380)
        self.assertEqual(offsets['PartyMenuArgs.size'], 0x44)
        self.assertEqual(offsets['PCBoxArgs.size'], 0x0C)

    def test_runtime_uses_only_pinned_offsets_and_natives(self):
        text = (FEATURE / 'runtime.c').read_text() + (FEATURE / 'party_ui.c').read_text()
        pins = self.pins
        for macro, key in (('PARTY_ARGS', 'PartyMenu.args'), ('PARTY_INDEX', 'PartyMenu.partyMonIndex'),
                           ('OWNER_EXIT_ENV', 'StartMenu.exitTaskEnvironment'), ('OWNER_EXIT_FUNC', 'StartMenu.exitTaskFunc'),
                           ('OWNER_CHECK_DATA', 'StartMenu.fieldMoveCheckData'), ('OWNER_FLAGS', 'StartMenu.inhibitIconFlags'),
                           ('OWNER_STATE', 'StartMenu.state_u16'), ('PARTY_BUTTON_ANIM', 'PartyMenu.buttonAnim.active'),
                           ('ARGS_FIELD', 'PartyMenuArgs.fieldSystem'), ('ARGS_CHECK', 'PartyMenuArgs.fieldMoveCheckData'),
                           ('ARGS_CONTEXT', 'PartyMenuArgs.context'), ('ARGS_SLOT', 'PartyMenuArgs.partySlot'),
                           ('ARGS_ACTION', 'PartyMenuArgs.selectedAction'), ('FIELD_SAVE', 'FieldSystem.saveData'),
                           ('FIELD_AVATAR', 'FieldSystem.playerAvatar'), ('FIELD_MENU_INPUT', 'FieldSystem.menuInputState'),
                           ('AVATAR_STATE', 'PlayerAvatar.state'), ('FIELD_TASKMAN', 'FieldSystem.taskman'),
                           ('FIELD_LOAD_TYPE', 'FieldSystem.mapLoadType'), ('FIELD_FRONTIER', 'FieldSystem.frontierFsys'),
                           ('FIELD_LINK_RULESET', 'FieldSystem.linkBattleRuleset'), ('PARTY_WINDOW32', 'PartyMenu.windows32'),
                           ('SYS_HELD_RAW', 'gSystem.heldKeysRaw'), ('SYS_NEW_RAW', 'gSystem.newKeysRaw'), ('SYS_NEW', 'gSystem.newKeys'),
                           ('SYS_TOUCH_X', 'gSystem.touchX'), ('SYS_TOUCH_Y', 'gSystem.touchY'),
                           ('SYS_TOUCH_NEW', 'gSystem.touchNew'), ('SYS_TOUCH_HELD', 'gSystem.touchHeld')):
            found = re.search(r'#define %s 0x([0-9A-Fa-f]+)u' % macro, text)
            self.assertIsNotNone(found, macro)
            self.assertEqual(int(found.group(1), 16), pins['offsets'][key], macro)
        self.assertEqual(int(re.search(r'#define SYS_BASE 0x([0-9A-F]+)u', text).group(1), 16), pins['ram']['gSystem'])
        natives = {n['address'] | 1: name for name, n in pins['languages']['EN']['natives'].items()}
        for match in re.finditer(r'#define N_(\w+) 0x([0-9A-F]{8})u', text):
            if match.group(1) in ('NATIVE_CALLBACK',):
                continue
            address = int(match.group(2), 16)
            self.assertIn(address, natives, 'native %s %#x is not pinned' % (match.group(1), address))

    def test_overlay14_pin_and_ordinary_context_natives_are_pinned(self):
        pins = self.pins
        self.assertEqual(pins['overlay14']['address'], 0x021E5900)
        self.assertRegex(pins['overlay14']['head16_hex'], r'^[0-9a-f]{32}$')
        natives = pins['languages']['EN']['natives']
        self.assertEqual(natives['Save_VarsFlags_Get']['address'], 0x020503D0)
        self.assertEqual(natives['Save_VarsFlags_CheckHaveFollower']['address'], 0x02066644)

    def test_FieldMove_InitCheckData_is_never_called(self):
        text = (FEATURE / 'runtime.c').read_text() + (FEATURE / 'party_ui.c').read_text()
        code = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        self.assertNotIn('refresh_field_data', code, 'the reserved word is not read by any code path')
        self.assertNotIn('FieldMove', code)


class AbiHeader(unittest.TestCase):
    def test_python_and_c_layouts_agree(self):
        header = (FEATURE / 'abi.h').read_text()
        state = u32_fields(header, 'SgpBoxState')
        config = u32_fields(header, 'SgpBoxConfig')
        self.assertEqual({name: 4 * state.index(name) for name in dict.fromkeys(state)}, portable.STATE_OFFSETS)
        self.assertEqual(4 * len(state), portable.STATE_BYTES)
        names = [n for n in dict.fromkeys(config) if n != 'reserved']
        self.assertIn('context_proof', names)
        self.assertEqual({name: 4 * config.index(name) for name in names}, portable.CONFIG_OFFSETS)
        self.assertEqual(4 * len(config), portable.CONFIG_BYTES)

    def test_record_never_holds_a_pokemon_pointer(self):
        header = (FEATURE / 'abi.h').read_text()
        body = re.search(r'typedef struct SgpBoxState \{(.*?)\} SgpBoxState;', header, re.S).group(1)
        self.assertNotRegex(body.lower(), r'pokemon\s*\*|pokemon\s+\w+|boxpokemon')
        self.assertEqual(set(re.findall(r'u32 (\w+);', body)), set(portable.STATE_OFFSETS))

    def test_state_layout_in_runtime_matches(self):
        runtime = (FEATURE / 'runtime.c').read_text()
        self.assertIn('.word 0x31425053', runtime)       # state magic
        self.assertIn('.word 0x31434253,0,0,0,0,3,0,0', runtime)   # config magic and defaults (all words off, mask 3)
        self.assertIn('extern u8 sgp_box_area[96];', runtime)
        self.assertEqual(portable.STATE_BYTES + portable.CONFIG_BYTES, 96)


class Text(unittest.TestCase):
    def test_label_words_are_the_charmap_codes_of_R_colon_space_B_o_x(self):
        if not CHARMAP.is_file():
            reason = 'pret charmap not present: %s' % CHARMAP
            if os.environ.get('SGP_PORTABLE_REQUIRE_INPUTS') == '1':
                self.fail(reason)
            self.skipTest(reason)
        codes = {}
        for line in CHARMAP.read_text(encoding='utf8').splitlines():
            if '=' in line and not line.startswith('//'):
                key, value = line.lstrip().split('=', 1)
                if len(key) == 4:
                    codes.setdefault(value, int(key, 16))
        expected = [codes[c] for c in 'R: Box']
        source = (FEATURE / 'party_ui.c').read_text()
        words = re.search(r'\.hword (0x[0-9A-F]{4}(?:,0x[0-9A-F]{4})*),0xFFFF', source).group(1)
        self.assertEqual([int(w, 16) for w in words.split(',')], expected)
        self.assertIn('.hword 6,6\\n.word 0xB6F8D2EC', source)      # maxsize, size, String magic


class Trampoline(unittest.TestCase):
    ADDRESS, GATE = 0x023E0000, 0x023E0101

    def disassemble(self, code, base):
        md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
        return [(i.address - base, i.mnemonic, i.op_str) for i in md.disasm(code, base)]

    def test_displaced_instructions_and_resume_are_instruction_aware(self):
        code = portable.callback_trampoline(self.ADDRESS, self.GATE)
        self.assertEqual(len(code), portable.TRAMPOLINE_BYTES)
        ins = self.disassemble(code[:0x24], self.ADDRESS)
        mnemonics = [m for _o, m, _ in ins]
        self.assertEqual(mnemonics, ['push', 'ldr', 'blx', 'cmp', 'beq', 'movs', 'pop', 'pop', 'mov', 'push', 'sub', 'adds',
                                     'bl', 'adds', 'ldr', 'bx', 'mov'])
        # the displaced span is the original five instructions, the BL re-encoded for its new address
        self.assertEqual(code[0x12:0x18], portable.CALLBACK_BEFORE[:6])
        self.assertEqual(code[0x1C:0x1E], portable.CALLBACK_BEFORE[10:12])
        from sgp12.rom import bl_decode
        self.assertNotEqual(code[0x18:0x1C], portable.CALLBACK_BEFORE[6:10], 'a verbatim BL copy would call the wrong target')
        self.assertEqual(bl_decode(self.ADDRESS + 0x18, code[0x18:0x1C]), portable.GET_FIELD_SYSTEM)
        self.assertEqual(bl_decode(portable.CALLBACK + 6, portable.CALLBACK_BEFORE[6:10]), portable.GET_FIELD_SYSTEM)
        literals = struct.unpack_from('<II', code, 0x24)
        self.assertEqual(literals, (self.GATE, (portable.CALLBACK + 12) | 1), 'resumes at +12, never inside the BL at +8')
        self.assertNotEqual(literals[1], (portable.CALLBACK + 8) | 1)

    def test_ldr_literals_reach_their_words(self):
        code = portable.callback_trampoline(self.ADDRESS, self.GATE)
        for offset, literal in ((0x02, 0x24), (0x1E, 0x28)):
            halfword = struct.unpack_from('<H', code, offset)[0]
            self.assertEqual(halfword & 0xF800, 0x4800)
            self.assertEqual(((self.ADDRESS + offset + 4) & ~3) + (halfword & 0xFF) * 4, self.ADDRESS + literal)

    def test_trampoline_requires_alignment_and_a_thumb_gate(self):
        for address, gate in ((self.ADDRESS + 2, self.GATE), (self.ADDRESS, self.GATE - 1)):
            with self.assertRaises(ValueError):
                portable.callback_trampoline(address, gate)

    def test_callback_hook_is_eight_bytes_and_loads_the_trampoline(self):
        hook = portable.callback_hook(0x023E0200)
        self.assertEqual(len(hook), 8)
        self.assertEqual(hook[:4].hex(), '004b1847')       # ldr r3,[pc,#0]; bx r3
        self.assertEqual(struct.unpack_from('<I', hook, 4)[0], 0x023E0201)
        self.assertEqual(portable.CALLBACK % 4, 0, 'literal addressing requires a 4-aligned entry')


class Compile(unittest.TestCase):
    def setUp(self):
        host = nonproduction_native_compiler_contract(portable)
        host.__enter__()
        self.addCleanup(host.__exit__, None, None, None)

    def test_payload_is_measured_deterministic_and_relocatable(self):
        with tempfile.TemporaryDirectory() as work:
            first, symbols1, receipt1 = portable.compile_native(work, 0x023E0000)
            second, symbols2, receipt2 = portable.compile_native(work, 0x023E4000)
        self.assertEqual(receipt1['object_sha256'], receipt2['object_sha256'], 'one object, any base')
        self.assertEqual(len(first), len(second))
        self.assertLessEqual(len(first), 4096, 'code + state + label budget')
        self.assertLessEqual(receipt1['stack_max'], 96)
        for name in portable.ENTRIES:
            self.assertIn(name, symbols1)
            self.assertEqual(symbols2[name] - symbols1[name], 0x4000, name)
        for name in portable.ENTRIES:
            if name != 'sgp_box_area':
                self.assertEqual(symbols1[name] & 1, 1, 'Thumb entry ' + name)
        self.assertEqual(symbols1['sgp_box_area'], 0x023E0000, 'record is the first object of the compartment')

    def test_base_must_be_explicit_aligned_and_in_main_ram(self):
        with tempfile.TemporaryDirectory() as work:
            for bad in (0x023E0002, 0x01FF8000, 0x02400000, None, '0x023E0000'):
                with self.assertRaises(ValueError):
                    portable.compile_native(work, bad)
        with self.assertRaises(ValueError):
            portable.prepare(b'', 'EN', tempfile.gettempdir(), allocation=None, preimage_sha256='0' * 64)
        with self.assertRaises(TypeError):
            portable.prepare(b'', 'EN', tempfile.gettempdir(), base=0x023D4E10, preimage_sha256='0' * 64)   # the free-form base is gone

    def test_measure_reports_the_compartment_size(self):
        with tempfile.TemporaryDirectory() as work:
            measured = portable.measure(work)
            blob, _, receipt = portable.compile_native(work, 0x023E0000)
        self.assertEqual(measured['bytes'], ((len(blob) + 3) & ~3) + portable.TRAMPOLINE_BYTES)
        self.assertEqual(measured['code_bytes'], len(blob))
        self.assertEqual(measured['stack_max'], receipt['stack_max'])



CANDIDATE = hashlib.sha256(b'the inert candidate ROM that was captured').hexdigest()
MEASURED = {'sha256': hashlib.sha256(b'evidence package').hexdigest(), 'origin': 'Android capture, campaign receipt',
            'status': 'measured', 'capture_file': 'captures/portable.json', 'build_id': 'candidate-example',
            'capture_rom_sha256': CANDIDATE, 'language': 'EN'}


class ProofBinding(unittest.TestCase):
    """C3: a measured proof is tied to the language and to the inert candidate ROM that was captured."""

    def check(self, proof, language='EN', candidate=CANDIDATE, synthetic=False):
        return portable._proof(proof, synthetic, language, candidate)

    def test_a_measured_proof_bound_to_the_candidate_and_language_is_accepted(self):
        self.assertEqual(self.check(MEASURED)['accepted_as'], 'measured')
        self.assertIsNone(self.check(None))

    def test_candidate_mismatch_language_mismatch_and_missing_fields_are_refused(self):
        other = hashlib.sha256(b'another ROM').hexdigest()
        cases = {'other candidate': (MEASURED, 'EN', other, 'another ROM'),
                 'no candidate': (MEASURED, 'EN', None, 'candidate_sha256'),
                 'malformed candidate': (MEASURED, 'EN', 'ABC', 'candidate_sha256'),
                 'other language': (MEASURED, 'IT', CANDIDATE, 'another language'),
                 'proof of the other language': (dict(MEASURED, language='IT'), 'EN', CANDIDATE, 'another language')}
        for name, (proof, language, candidate, message) in cases.items():
            with self.subTest(name), self.assertRaisesRegex(ValueError, message):
                self.check(proof, language, candidate)
        for lacking in ('capture_file', 'capture_rom_sha256', 'build_id', 'language'):
            with self.subTest(lacking=lacking), self.assertRaisesRegex(ValueError, 'exactly'):
                self.check({k: v for k, v in MEASURED.items() if k != lacking})

    def test_a_synthetic_proof_needs_the_test_flag_and_a_candidate(self):
        synthetic = {'sha256': MEASURED['sha256'], 'origin': 'unit test fixture', 'status': 'synthetic'}
        with self.assertRaisesRegex(ValueError, 'tests only'):
            self.check(synthetic)
        self.assertEqual(self.check(synthetic, synthetic=True)['accepted_as'], 'synthetic-for-test')
        with self.assertRaisesRegex(ValueError, 'candidate_sha256'):
            self.check(synthetic, candidate=None, synthetic=True)
        with self.assertRaisesRegex(ValueError, 'another language'):
            self.check(dict(synthetic, language='IT'), synthetic=True)


class AllocationReceipt(unittest.TestCase):
    """The compartment base is accepted only from a reserve.allocate receipt checked against the policy in force."""

    def check(self, **override):
        return portable.check_allocation(pb.declared_allocation('EN', **override), 'EN')

    def test_the_declared_double_is_accepted_and_the_real_policy_refuses_it(self):
        with pb.declared_reserve():
            row = self.check()
        self.assertEqual(row, {'name': portable.SLOT_NAME, 'parent': 'test.declared-parent', 'start': pb.SLOT_START,
                               'bytes': pb.SLOT_BYTES, 'capacity': pb.SLOT_BYTES})
        with pb.real_reserve(), self.assertRaisesRegex(ValueError, 'policy in force'):
            self.check()

    def test_the_real_policy_cannot_grant_the_slot_yet(self):
        """portable-box.runtime sits under field-guide.code, a conditional owner: even a receipt carrying the
        real policy digest is refused (INTEGRATION.md asks Codex to lift the condition)."""
        policy, digest = portable._reserve_policy()
        forged = pb.declared_allocation('EN', policy_version=policy['version'], policy_sha256=digest)
        forged['assignments'][0].update(parent='field-guide.code')
        with self.assertRaisesRegex(ValueError, 'conditional'):
            portable.check_allocation(forged, 'EN')

    def test_every_forgery_of_a_good_receipt_is_refused(self):
        start, size = pb.SLOT_START, pb.SLOT_BYTES
        base = pb.declared_allocation('EN')
        row = base['assignments'][0]
        cases = {
            'policy digest': dict(policy_sha256='1' * 64), 'policy version': dict(policy_version='sgp131-resident-5'),
            'schema': dict(schema=2), 'language': dict(language='IT'), 'input is not a V4': dict(input_sha256='2' * 64),
            'input of the other language': dict(input_sha256=next(h for h, l in pb.INPUT_HASHES.items() if l == 'IT')),
            'installed': dict(installed=True), 'authorized': dict(installation_authorized=True),
            'not reserved': dict(address_reserved=False), 'audit hash': dict(audit_sha256='zz'),
            'name not requested': dict(requested={'other.slot': size}),
            'unknown slot': dict(requested={portable.SLOT_NAME: size, 'nobody.slot': 4}),
            'size over capacity': dict(requested={portable.SLOT_NAME: size + 4}, assignments=[dict(row, bytes=size + 4)]),
            'start moved': dict(assignments=[dict(row, start=start + 4)]),
            'start in a hook region': dict(assignments=[dict(row, start=0x0203E500)]),
            'bytes differ from the request': dict(assignments=[dict(row, bytes=size - 4)]),
            'capacity': dict(assignments=[dict(row, capacity=size * 2)]), 'parent': dict(assignments=[dict(row, parent='x')]),
            'extra assignment': dict(assignments=[row, dict(row, name='x')]), 'no assignment': dict(assignments=[]),
        }
        with pb.declared_reserve():
            for name, override in cases.items():
                with self.subTest(name), self.assertRaises(ValueError):
                    portable.check_allocation(dict(base, **override), 'EN')
            for field in list(base):
                broken = dict(base)
                del broken[field]
                with self.subTest(missing=field), self.assertRaises(ValueError):
                    portable.check_allocation(broken, 'EN')
            for junk in (None, [], 'receipt', {**base, 'extra': 1}):
                with self.subTest(junk=type(junk).__name__), self.assertRaises(ValueError):
                    portable.check_allocation(junk, 'EN')

    def test_a_slot_outside_the_reserve_range_is_refused_even_under_a_policy_that_names_it(self):
        def outside():
            part = {'name': portable.SLOT_NAME, 'kind': 'payload', 'start': 0x0203E500, 'bytes': 3024}
            return ({'version': pb.TEST_POLICY_VERSION, 'conditional_parents': [],
                     'subdivisions': [{'parent': 'test.declared-parent', 'parts': [part]}]}, pb.TEST_POLICY_SHA256)
        from unittest import mock
        allocation = pb.declared_allocation('EN', size=3024, assignments=[{
            'name': portable.SLOT_NAME, 'parent': 'test.declared-parent', 'start': 0x0203E500, 'bytes': 3024, 'capacity': 3024}])
        with mock.patch.object(portable, '_reserve_policy', outside), self.assertRaisesRegex(ValueError, 'outside the reserve'):
            portable.check_allocation(allocation, 'EN')

    def test_the_declared_slot_is_the_one_of_the_product_map(self):
        policy = json.loads((portable.SOURCE / 'sgp131/data/reserve-map.json').read_text())
        parts = {part['name']: part for e in policy['subdivisions'] for part in e['parts']}
        self.assertEqual((parts[portable.SLOT_NAME]['start'], parts[portable.SLOT_NAME]['bytes']), (pb.SLOT_START, pb.SLOT_BYTES))
        self.assertLessEqual(pb.PORTABLE_SIZE, pb.SLOT_BYTES, 'the measured compartment fits the slot the map reserves')


class UiComposition(unittest.TestCase):
    """The pinned intervals and hook sites never overlap what sgp131/ui.py writes (read-only check)."""

    def test_pins_and_hooks_are_clear_of_the_ui_writes(self):
        rows = [(name, span['address'], span['bytes']) for name, span in portable.abi()['languages']['EN']['spans'].items()]
        rows += [(name, native['address'], native['prefix_bytes']) for name, native in portable.abi()['languages']['EN']['natives'].items()]
        rows += [('literal ' + address, int(address, 16), 4) for address in portable.abi()['literals']]
        rows += [('compartment', pb.SLOT_START, pb.SLOT_BYTES)]
        self.assertGreater(len(rows), 30)
        for name, start, size in rows:
            for ui_name, ui_start, ui_size in _test_controls.Intervals.UI_WRITES:
                with self.subTest(pin=name, ui=ui_name):
                    self.assertTrue(start + size <= ui_start or ui_start + ui_size <= start,
                                    '%s %#x+%d overlaps the UI write %s' % (name, start, size, ui_name))


class ReceiptHygiene(unittest.TestCase):
    def test_no_process_state_is_written_by_the_code(self):
        source = (portable.SOURCE / 'sgp131/portable.py').read_text()
        for word in ('SOURCE_READY_FOR_REVIEW', 'ANDROID_ACCEPTED', "'android'", 'not run'):
            self.assertNotIn(word, source, word)


if __name__ == '__main__':
    unittest.main()
