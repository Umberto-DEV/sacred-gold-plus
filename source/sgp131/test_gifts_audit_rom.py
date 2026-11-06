"""Class B: real EN/IT V4 candidate images, read and fixed in memory only.

Covers the two gift-script fixes on the cartridge bytes: the six repaired ribbon tails and the party-full guard of the
Eevee gift in member 227, the latter also executed by the cartridge's own script dispatcher (0x0203FD6C) in Unicorn.

Missing inputs skip with a reason; with SGP_GIFT_REQUIRE_INPUTS=1 they FAIL (no skip is acceptable in an acceptance
run). A present input with the wrong sha256 always fails. Nothing is written to disk and no extracted bytes are kept.
"""
import hashlib
import os
from pathlib import Path
import re
import struct
import unittest

import ndspy.narc
import ndspy.rom

from sgp131 import gifts_audit as audit
from sgp131 import gifts_scripts as scripts

ROOT = Path(os.environ['SGP_REPO_ROOT']) if os.environ.get('SGP_REPO_ROOT') else next(
    p for p in Path(__file__).resolve().parents if (p / 'source' / 'run_tests.py').exists())
CANDIDATES = ROOT / 'local' / 'experiments' / 'balance493-2026-10-28'
INPUTS = {
    'EN': (os.environ.get('SGP_GIFT_ROM_EN') or CANDIDATES / 'candidate-v4-EN.nds',
           '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
    'IT': (os.environ.get('SGP_GIFT_ROM_IT') or CANDIDATES / 'candidate-v4-IT.nds',
           '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'),
}
PRET = Path(os.environ.get('SGP_PRET_SOURCE') or ROOT / 'local' / 'tools' / 'pokeheartgold')
REQUIRE_INPUTS = os.environ.get('SGP_GIFT_REQUIRE_INPUTS') == '1'
SIX = (225, 232, 243, 246, 938, 962)
EEVEE_MEMBER = 227
_CACHE = {}


def _missing(message):
    if REQUIRE_INPUTS:
        raise AssertionError('SGP_GIFT_REQUIRE_INPUTS=1 and ' + message)
    raise unittest.SkipTest(message)


def commands():
    if 'commands' not in _CACHE:
        path = PRET / 'tools' / 'py_scripts' / 'scrcmd.json'
        if not path.is_file():
            _missing(f'pinned reference metadata not found: {path}')
        _CACHE['commands'] = audit.load_commands(path)
    return _CACHE['commands']


def image(language):
    if language not in _CACHE:
        path, digest = INPUTS[language]
        path = Path(path)
        if not path.is_file():
            _missing(f'{language} V4 candidate not found: {path}')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise AssertionError(f'{language} candidate sha256 differs from the pinned V4 input')
        _CACHE[language] = data
    return _CACHE[language]


def before(language):
    key = ('before', language)
    if key not in _CACHE:
        _CACHE[key] = audit.audit_rom(image(language), language, commands())
    return _CACHE[key]


def ribbon_image(language):
    """The V4 image with only the six ribbon members replaced (one NARC rewrite), as the old stage did."""
    from sgp13.resources import append_file
    data = image(language)
    rom = ndspy.rom.NintendoDSRom(data)
    file_id = rom.filenames.idOf('a/0/1/2')
    archive = ndspy.narc.NARC(rom.files[file_id])
    recipe, reports = scripts.load_recipe(), []
    for member_id in SIX:
        old = bytes(archive.files[member_id])
        new = scripts.patch_member(old, language, member_id, commands(), recipe)
        reports.append(scripts.verify_member(old, new, commands(), recipe))
        archive.files[member_id] = new
    return append_file(data, file_id, archive.save()), reports


def repaired(language):
    key = ('repaired', language)
    if key not in _CACHE:
        data, reports = ribbon_image(language)
        _CACHE[key] = (data, reports, audit.audit_rom(data, language, commands()))
    return _CACHE[key]


def script_files(data):
    rom = ndspy.rom.NintendoDSRom(data)
    return [bytes(f) for f in ndspy.narc.NARC(rom.getFileByName('a/0/1/2')).files]


def json_copy(value):
    import json
    return json.loads(json.dumps(value))


def reference_trace(member_id):
    """The retail tail, parsed from the pinned pret source and resolved through its own constants."""
    recipe = scripts.load_recipe()
    name = recipe['reference']['files'][str(member_id)]
    text = (PRET / 'files' / 'fielddata' / 'script' / 'scr_seq' / name).read_text()
    constants = {}
    for header in ('sndseq.h', 'flags.h', 'ribbon.h'):
        for match in re.finditer(r'#define\s+(\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b',
                                 (PRET / 'include' / 'constants' / header).read_text()):
            constants[match.group(1)] = int(match.group(2), 0)
    lines = [l.strip() for l in text.splitlines()]
    start = next(i for i, l in enumerate(lines) if l.startswith('GiveRibbon'))
    trace = []
    for line in lines[start:]:
        if not line or line.startswith('@'):
            continue
        parts = line.replace(',', ' ').split()
        mnemonic, operands = parts[0], parts[1:]
        if mnemonic == 'GiveRibbon':
            trace.append(('GiveRibbon', [0x8002, constants[operands[1]]]))
        elif mnemonic in ('PlayFanfare', 'SetFlag'):
            trace.append((mnemonic, [constants[operands[0]]]))
        else:
            trace.append((mnemonic, []))
        if mnemonic == 'End':
            return trace
    raise AssertionError('reference tail has no End')


class GiftAuditRom(unittest.TestCase):
    languages = ('EN', 'IT')

    def setUp(self):
        commands()                                   # skips (or fails with SGP_GIFT_REQUIRE_INPUTS=1) when pret is missing
        for language in ('EN', 'IT'):
            image(language)

    def each(self):
        for language in self.languages:
            with self.subTest(language=language):
                yield language

    def test_original_has_exactly_the_six_known_errors_and_admission_is_refused(self):
        for language in self.each():
            receipt = before(language)
            errors = sorted((e['member'], e['error']) for e in receipt['decode_errors'])
            self.assertEqual(errors, sorted((int(m), f"opcode illegale 2009 a {r['illegal_offset']}")
                                            for m, r in scripts.load_recipe()['members'].items()))
            for error in receipt['decode_errors']:
                self.assertEqual(error['previous'][0][1], 'PlayFanfare 20', error)
            with self.assertRaises(ValueError) as caught:
                audit.require_complete_audit(receipt)
            for member in SIX:
                self.assertIn(f'member {member}: opcode illegale 2009', str(caught.exception))

    def test_native_fanfare_width_and_dispatch_count(self):
        for language in self.each():
            receipt = before(language)
            native, probe = receipt['native'], receipt['native_probe']
            self.assertEqual(native['count'], 853)
            self.assertTrue(all(native[k] for k in ('count_matches', 'dispatcher_matches', 'reader_matches',
                                                    'fanfare_entry_matches', 'fanfare_handler_matches',
                                                    'script_api_matches')))
            self.assertTrue(all(h['matches'] for h in native['handlers'].values()))
            self.assertEqual(native['fanfare_entry'], 0x02049305)
            # the real ScriptReadHalfword and PlayFanfare handler, executed
            self.assertEqual(probe['reader'], {'value': 78, 'advance': 2})
            self.assertEqual(probe['fanfare_handler']['advance'], 2)
            self.assertEqual(probe['fanfare_handler']['operand_resolved'], [20])
            # the real RunScriptCommand on the defective bytes
            tail = probe['defective_tail']
            self.assertEqual((tail['returned'], tail['mode_after'], tail['asserts']), (0, 0, 1))
            self.assertEqual(tail['consumed_bytes'], 6)
            self.assertFalse(tail['reached_close_msg'])

    def test_opcode2009_rejected_without_fake_metadata(self):
        for language in self.each():
            table = commands()
            self.assertEqual(len(table), 853)
            self.assertTrue(table.nome(2009).startswith('ScrCmd_ILLEGALE'))
            self.assertEqual(before(language)['native']['count'], len(table))
            # no definition was added for 2009 anywhere: the repaired image still shows it as non-opcode
            self.assertEqual(repaired(language)[2]['native']['count'], 853)
            self.assertEqual(repaired(language)[2]['native_probe']['defective_tail']['asserts'], 1)

    def test_each_ribbon_tail_maps_all_incoming_edges(self):
        recipe = scripts.load_recipe()
        for language in self.each():
            files = script_files(image(language))
            fixed = script_files(repaired(language)[0])
            for member_id in SIX:
                spec = recipe['members'][str(member_id)]
                site = spec['tail_site']
                old = scripts.decode(files[member_id], commands(), member_id,
                                     (scripts.expected_error(spec),))
                edges = [e for e in scripts.incoming_edges(old) + scripts.entry_edges(old)
                         if site <= e[1] < site + 12]
                # the inherited tail is reached only by falling through from GiveRibbon
                self.assertEqual(edges, [], (member_id, edges))
                new = scripts.decode(fixed[member_id], commands(), member_id)
                self.assertEqual(new.errori, [])
                self.assertEqual(scripts.overlapping_instructions(new), [])
                self.assertEqual(scripts._trace_from(new, spec['ribbon_site']), reference_trace(member_id),
                                 f'member {member_id} does not follow the pret award tail')
                # the retained CloseMsg/ReleaseAll/End and the independent bag-full tail
                self.assertEqual([new.istruzioni[site + o].nome for o in (12, 14, 16)],
                                 ['CloseMsg', 'ReleaseAll', 'End'])
                self.assertEqual(new.istruzioni[site + 18].nome, 'CallStd')
                self.assertEqual(new.istruzioni[site + 18].args, [2009])

    def test_ribbon_message_flow_and_daily_flag_match_the_reference_member(self):
        recipe = scripts.load_recipe()
        for language in self.each():
            files = script_files(image(language))
            for member_id in SIX:
                spec = recipe['members'][str(member_id)]
                old = scripts.decode(files[member_id], commands(), member_id,
                                     (scripts.expected_error(spec),))
                flags = [(i.nome, i.args[0]) for i in old.istruzioni.values()
                         if i.nome in ('CheckFlag', 'SetFlag', 'ClearFlag') and i.args[0] == 2748]
                # the entry still TESTS the daily flag: only the SetFlag was lost with the tail
                self.assertEqual(flags, [('CheckFlag', 2748)], member_id)
                giver = old.istruzioni[spec['ribbon_site']]
                self.assertEqual(giver.args, [0x8002, spec['ribbon']])

    def test_recipe_messages_and_ribbon_equal_the_pret_member(self):
        recipe = scripts.load_recipe()
        constants = {}
        for header in ('ribbon.h',):
            for match in re.finditer(r'#define\s+(\w+)\s+(\d+)\b', (PRET / 'include' / 'constants' / header).read_text()):
                constants[match.group(1)] = int(match.group(2))
        for member_id, spec in recipe['members'].items():
            text = (PRET / 'files' / 'fielddata' / 'script' / 'scr_seq' / recipe['reference']['files'][member_id]).read_text()
            lines = [l.strip() for l in text.splitlines()]
            at = next(i for i, l in enumerate(lines) if l.startswith('GiveRibbon'))
            self.assertEqual(constants[lines[at].replace(',', ' ').split()[2]], spec['ribbon'], member_id)
            boxes = [int(l.split(',')[1]) for l in lines[at - 3:at] if l.startswith('MsgBoxExtern')]
            self.assertEqual(boxes, spec['messages'], member_id)
            self.assertTrue(lines[at - 4].startswith('GetStdMsgNaix'), member_id)

    def test_the_pinned_handler_prologue_is_verified_and_a_different_body_must_not_pass(self):
        for language in self.each():
            handlers = before(language)['native']['handlers']
            self.assertEqual(sorted(handlers), ['137'])
            for op, handler in handlers.items():
                self.assertTrue(handler['matches'] and handler['prologue_matches'], (op, handler))
        guards = audit.load_guards()
        changed = json_copy(guards)
        changed['handlers']['137']['prologue_sha256'] = '0' * 64
        receipt = audit.audit_rom(image('EN'), 'EN', commands(), guards=changed, probe=False)
        self.assertFalse(receipt['native']['handlers']['137']['prologue_matches'])
        for name in ('read_halfword', 'var_pointer'):
            changed = json_copy(guards)
            changed['script_api'][name]['prologue_sha256'] = '0' * 64
            receipt = audit.audit_rom(image('EN'), 'EN', commands(), guards=changed, probe=False)
            self.assertFalse(receipt['native']['script_api_matches'], name)
        self.assertTrue(before('EN')['native']['script_api_matches'] and before('IT')['native']['script_api_matches'])

    def test_repaired_audit_is_complete(self):
        for language in self.each():
            data, reports, receipt = repaired(language)
            self.assertEqual(receipt['decode_errors'], [])
            self.assertIsNone(audit.require_complete_audit(receipt))
            self.assertEqual(receipt['members'], before(language)['members'])
            for r in reports:
                self.assertEqual(r['output_bytes'] - r['input_bytes'], 6)
                self.assertEqual(r['instructions_after'] - r['instructions_before'], 6)

    def test_all_entries_and_movements_of_the_ribbon_members_survive(self):
        recipe = scripts.load_recipe()
        for language in self.each():
            files, fixed = script_files(image(language)), script_files(repaired(language)[0])
            self.assertEqual(len(files), len(fixed))
            self.assertEqual([i for i, (a, b) in enumerate(zip(files, fixed)) if a != b], list(SIX))
            for member_id in SIX:
                spec = recipe['members'][str(member_id)]
                site = spec['tail_site']
                shift = lambda o: o + 6 if o >= site + 6 else o
                old = scripts.decode(files[member_id], commands(), member_id, (scripts.expected_error(spec),))
                new = scripts.decode(fixed[member_id], commands(), member_id)
                self.assertEqual(new.entry, [shift(e) for e in old.entry])
                self.assertEqual(new.dati_movimento, {shift(m) for m in old.dati_movimento})
                for start in old.dati_movimento:
                    end = scripts.movement_end(files[member_id], start)
                    self.assertEqual(fixed[member_id][shift(start):shift(start) + end - start],
                                     files[member_id][start:end])
                old_calls = sorted((i.off, i.args[0]) for i in old.istruzioni.values() if i.nome == 'CallStd')
                new_calls = sorted((i.off, i.args[0]) for i in new.istruzioni.values() if i.nome == 'CallStd')
                self.assertTrue(set((shift(o), a) for o, a in old_calls) <= set(new_calls))

    def test_ribbon_repair_changes_nothing_but_the_six_members(self):
        for language in self.each():
            data, _, _ = repaired(language)
            original, updated = ndspy.rom.NintendoDSRom(image(language)), ndspy.rom.NintendoDSRom(data)
            file_id = original.filenames.idOf('a/0/1/2')
            self.assertEqual([i for i, (a, b) in enumerate(zip(original.files, updated.files)) if a != b], [file_id])
            self.assertEqual((updated.arm9, updated.arm7, updated.iconBanner),
                             (original.arm9, original.arm7, original.iconBanner))
            # whole header, except what appending a resource must change: used ROM size, capacity, CRC
            volatile = set(range(0x14, 0x15)) | set(range(0x80, 0x84)) | set(range(0x15E, 0x160))
            self.assertEqual([i for i in range(0x200) if image(language)[i] != data[i] and i not in volatile], [])

    def test_unknown_opcode_in_unrelated_member_blocks_admission(self):
        from sgp13.resources import append_file
        for language in self.each():
            data = repaired(language)[0]
            rom = ndspy.rom.NintendoDSRom(data)
            file_id = rom.filenames.idOf('a/0/1/2')
            archive = ndspy.narc.NARC(rom.files[file_id])
            member = scripts.decode(bytes(archive.files[3]), commands(), 3)
            # turn one reachable instruction of member 3 into an opcode the native table cannot dispatch
            mutated = bytearray(archive.files[3])
            first = min(member.istruzioni)
            mutated[first:first + 2] = struct.pack('<H', 4000)
            archive.files[3] = bytes(mutated)
            bad = append_file(data, file_id, archive.save())
            receipt = audit.audit_rom(bad, language, commands(), probe=False)
            self.assertTrue(any(e['member'] == 3 for e in receipt['decode_errors']))
            with self.assertRaisesRegex(ValueError, 'member 3: opcode illegale 4000'):
                audit.require_complete_audit(receipt | {'native_probe': repaired(language)[2]['native_probe']})


# ---------------------------------------------------------------------------------------------------------------------
# the Eevee party guard (member 227)

EXPECTED_PARTY_FULL = {'EN': 'Your party is full!', 'IT': 'La tua squadra è completa!'}
REAL_HANDLERS = ('End', 'GoTo', 'GoToIf', 'SetVar', 'CopyVar', 'CompareVarToValue')   # run as the cartridge's own code
SCRATCH = 0x02300000
CTX, FIELD, VARS, SCRIPT, TRAP, STACK = (SCRATCH + o for o in (0x0, 0x400, 0x1000, 0x4000, 0x8000, 0x1F000))
SENTINEL = 0x7A5A
VAR_POINTER = 0x02040374


def member227(language):
    return script_files(image(language))[EEVEE_MEMBER]


def _module(path, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_message_text(language, bank_index, message_index):
    """A retail message decoded with the repo's codec and the pinned pret charmap (test-side only)."""
    source = ROOT / 'source'
    codec = _module(source / 'translation' / 'message_codec.py', 'gift_test_message_codec')
    encoder = _module(source / 'features' / 'options' / 'tools' / 'codifica_testo.py', 'gift_test_text_encoder')
    table, _ = encoder.carica_charmap(PRET / 'charmap.txt')
    reverse = {value: key for key, value in table.items()}
    rom = ndspy.rom.NintendoDSRom(image(language))
    bank = codec.Bank(bytes(ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[bank_index]))
    return ''.join(reverse[w] for w in bank.words[message_index][:-1])


class Target(int):
    """A member offset a relative operand points at."""


def moved(events, boundary, added):
    """The events of the V4 member with the targets of relative operands shifted as the insertion shifts them."""
    return [(name, tuple(Target(a + added if a >= boundary else a) if isinstance(a, Target) else a for a in args))
            for name, args in events]


class Dispatch:
    """The cartridge's own RunScriptCommand (0x0203FD6C) running a script member in Unicorn.

    Executed as the cartridge's code: the dispatcher, ScriptReadHalfword, and the handlers of End, GoTo, GoToIf, SetVar,
    CopyVar and CompareVarToValue. Seamed (declared): ScriptGetVarPointer (variables live in a scratch page) and the
    handlers of every other command the member uses, which only record (name, operands) after consuming the operands
    with the widths of the pinned command table and return FALSE (a text box or fade would wait; here it does not).
    GetPartyCount writes `party`; GetMenuChoice writes `choice`; GiveMon writes 1 into its result variable.
    Not executed: text boxes, fades, the give itself, the nickname screen (Android).
    """

    def __init__(self, language, member, entry_offset, party, choice=0):
        from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB, Uc
        self.uc_hook, self.language = UC_HOOK_CODE, language
        self.guards = audit.load_guards()
        view = audit.Arm9View(image(language))
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x00120000)
        self.uc.mem_write(0x02000000, view.read(0x02000000, view.segments[0][2]))
        self.uc.mem_map(SCRATCH, 0x20000)
        self.uc.mem_write(TRAP, b'\x00\xbe')
        self.table = audit._addr(self.guards['command_table']['address'])
        self.count = view.u32(audit._addr(self.guards['command_table']['count_address']))
        self.party, self.choice, self.events, self.asserts = party, choice, [], 0
        self.cmds = commands()
        self.names = {name: op for op, name in enumerate(self.cmds.nomi)}
        decoded = scripts.decode(member, self.cmds, EEVEE_MEMBER)
        used = {ins.op for ins in decoded.istruzioni.values()}
        real = {self.names[n] for n in REAL_HANDLERS}
        self.entry_of = {}
        for op in sorted(used - real):
            entry = view.u32(self.table + 4 * op) & ~1
            assert entry not in {view.u32(self.table + 4 * r) & ~1 for r in real}, 'seam shares a real handler'
            self.entry_of.setdefault(entry, []).append(op)
        mapped = set()
        for address in self.entry_of:
            page = address & ~0xFFF
            if not view.has(address) and page not in mapped:      # overlay-owned handler: an empty page, never executed
                self.uc.mem_map(page, 0x1000)
                mapped.add(page)
            self.uc.hook_add(UC_HOOK_CODE, self._seam, begin=address, end=address)
        for address in (VAR_POINTER, audit._addr(self.guards['dispatcher']['assert_routine'])):
            self.uc.hook_add(UC_HOOK_CODE, self._world, begin=address, end=address)
        self.uc.mem_write(VARS, struct.pack('<H', SENTINEL) * 0x40)
        self.uc.mem_write(SCRIPT, member)
        self.uc.mem_write(CTX, bytes(0x90))
        self.uc.mem_write(CTX + 1, b'\x01')
        self.uc.mem_write(CTX + 8, struct.pack('<I', SCRIPT + entry_offset))
        self.uc.mem_write(CTX + 0x5C, struct.pack('<I', self.table))
        self.uc.mem_write(CTX + 0x60, struct.pack('<I', self.count))
        self.uc.mem_write(CTX + 0x80, struct.pack('<I', FIELD))

    def _return(self, value):
        from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0
        self.uc.reg_write(UC_ARM_REG_R0, value)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def slot(self, var):
        return VARS + 2 * (var - 0x8000) if 0x8000 <= var <= 0x803F else VARS + 0x7E

    def var(self, number):
        return struct.unpack('<H', bytes(self.uc.mem_read(self.slot(number), 2)))[0]

    def put(self, number, value):
        self.uc.mem_write(self.slot(number), struct.pack('<H', value))

    def _world(self, uc, address, size, user):
        from unicorn.arm_const import UC_ARM_REG_R1
        if address == VAR_POINTER:
            self._return(self.slot(uc.reg_read(UC_ARM_REG_R1)))
        else:
            self.asserts += 1
            self._return(0)

    def _seam(self, uc, address, size, user):
        sd = scripts.decoder()
        pointer = struct.unpack('<I', bytes(uc.mem_read(CTX + 8, 4)))[0]
        op = struct.unpack('<H', bytes(uc.mem_read(pointer - 2, 2)))[0]
        assert op in self.entry_of[address], 'handler entry reached for an unexpected opcode'
        kinds, extra = self.cmds.arg_list(op, None)
        assert extra is None
        args, cursor = [], pointer
        for kind in kinds:
            width = kind if isinstance(kind, int) else sd.ARG_SIZES[kind]
            value = int.from_bytes(bytes(uc.mem_read(cursor, width)), 'little')
            cursor += width
            # a relative operand is recorded as the member offset it points at (it moves when bytes are inserted)
            args.append(Target(((cursor + value) & 0xFFFFFFFF) - SCRIPT) if kind in sd.RELATIVE else value)
        uc.mem_write(CTX + 8, struct.pack('<I', cursor))
        name = self.cmds.nome(op)
        self.events.append((name, tuple(args)))
        if name == 'GetPartyCount':
            self.put(args[0], self.party)
        elif name == 'GetMenuChoice':
            self.put(args[0], self.choice)
        elif name == 'GiveMon':
            self.put(args[5], 1)
        self._return(0)

    def run(self):
        from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_SP
        self.uc.reg_write(UC_ARM_REG_R0, CTX)
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_LR, TRAP | 1)
        self.uc.emu_start(audit._addr(self.guards['dispatcher']['address']) | 1, TRAP, count=2_000_000)
        assert self.uc.reg_read(UC_ARM_REG_PC) == TRAP, 'the dispatcher did not return'
        self.returned = self.uc.reg_read(UC_ARM_REG_R0)
        self.mode = bytes(self.uc.mem_read(CTX + 1, 1))[0]
        return self

    def names_run(self):
        return [name for name, _ in self.events]


def ran(language, member, party, choice=0, entry=442):
    return Dispatch(language, member, entry, party, choice).run()


def fixed227(language):
    key = ('fixed227', language)
    if key not in _CACHE:
        _CACHE[key] = scripts.transform_party_guard(member227(language), language, commands())
    return _CACHE[key]


def entry_offset(member):
    return scripts.decode(member, commands(), EEVEE_MEMBER).entry[11]


class PartyGuardSite(unittest.TestCase):
    """What the guard is built from: the V4 member, the retail reference and the native message."""

    def setUp(self):
        commands()                                   # skips (or fails with SGP_GIFT_REQUIRE_INPUTS=1) when pret is missing
        for language in ('EN', 'IT'):
            image(language)

    def test_the_v4_member_is_the_pinned_one_and_has_the_unguarded_give(self):
        recipe = scripts.load_guard_recipe()
        for language in ('EN', 'IT'):
            raw = member227(language)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), recipe['preimage_sha256'][language])
            old = scripts.decode(raw, commands(), EEVEE_MEMBER)
            self.assertEqual(old.entry[recipe['entry']], recipe['entry_offset'])
            give = old.istruzioni[recipe['give_site']]
            self.assertEqual((give.nome, give.args), ('GiveMon', [recipe['species'], recipe['level'], 0, 0, 0,
                                                                  recipe['result_var']]))
            count = old.istruzioni[recipe['party_count_site']]
            self.assertEqual((count.nome, count.args, count.fine), ('GetPartyCount', [recipe['party_var']],
                                                                    recipe['give_site']))
            # the defect: no compare against the party limit anywhere in the member
            self.assertEqual([i.off for i in old.istruzioni.values()
                              if i.nome == 'CompareVarToValue' and i.args[1] == recipe['limit']], [])

    def test_the_defect_is_real_on_the_unmodified_member(self):
        """With a full party the V4 script still gives, sets the flag and hides the NPC: the Eevee is lost."""
        for language in ('EN', 'IT'):
            raw = member227(language)
            for choice in (0, 1):
                with self.subTest(language=language, choice=choice):
                    run = ran(language, raw, party=6, choice=choice, entry=entry_offset(raw))
                    self.assertIn(('GiveMon', (133, 5, 0, 0, 0, 0x800C)), run.events)
                    self.assertIn(('SetFlag', (16220,)), run.events)
                    self.assertIn(('HidePerson', (15,)), run.events)

    def test_the_retail_reference_has_the_same_shape(self):
        recipe = scripts.load_guard_recipe()
        text = (PRET / 'files' / 'fielddata' / 'script' / 'scr_seq' / recipe['reference']['file']).read_text()
        lines = [l.strip() for l in text.splitlines()]
        start = lines.index('GetPartyCount VAR_SPECIAL_x8005')
        self.assertEqual(lines[start:start + 3], ['GetPartyCount VAR_SPECIAL_x8005', 'Compare VAR_SPECIAL_x8005, 6',
                                                  'GoToIfEq _00DE'])
        full = lines.index('_00DE:')
        self.assertEqual(lines[full + 1:full + 5], ['NPCMsg msg_0586_T25R0401_00004', 'WaitButton', 'CloseMsg',
                                                    'ReleaseAll'])
        self.assertEqual(lines[full + 5], 'End')
        # the retail message is "can't carry any more Pokemon"; the cartridge's own party-full string is used instead
        self.assertEqual(recipe['limit'], 6)

    def test_the_message_is_a_native_retail_string_with_the_exact_meaning(self):
        recipe = scripts.load_guard_recipe()
        message = recipe['message']
        for language in ('EN', 'IT'):
            rom = ndspy.rom.NintendoDSRom(image(language))
            bank = bytes(ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[message['bank']])
            self.assertEqual(hashlib.sha256(bank).hexdigest(), message['bank_sha256'][language])
            self.assertEqual(native_message_text(language, message['bank'], message['index']),
                             EXPECTED_PARTY_FULL[language])


class PartyGuardRom(unittest.TestCase):
    languages = ('EN', 'IT')

    def setUp(self):
        commands()                                   # skips (or fails with SGP_GIFT_REQUIRE_INPUTS=1) when pret is missing
        for language in ('EN', 'IT'):
            image(language)

    def each(self):
        for language in self.languages:
            with self.subTest(language=language):
                yield language

    def test_the_fixed_member_passes_its_independent_read_back_and_is_the_only_change(self):
        recipe = scripts.load_guard_recipe()
        for language in self.each():
            raw, fixed = member227(language), fixed227(language)
            report = scripts.verify_party_guard(raw, fixed, commands(), recipe)
            self.assertEqual(len(fixed) - len(raw), 34)
            self.assertEqual((report['inserted_bytes'], report['block_bytes']), (20, 14))
            new = scripts.decode(fixed, commands(), EEVEE_MEMBER)
            self.assertEqual((new.errori, scripts.overlapping_instructions(new)), ([], []))
            guard = [(new.istruzioni[a].nome, new.istruzioni[a].args[:2]) for a in (450, 454, 460)]
            self.assertEqual(guard[:2], [('GetPartyCount', [recipe['party_var']]),
                                         ('CompareVarToValue', [recipe['party_var'], recipe['limit']])])
            self.assertEqual(new.istruzioni[460].nome, 'GoToIf')
            self.assertEqual(new.istruzioni[460].args[0], 1)                   # EQ, as the retail GoToIfEq

    def test_with_five_or_fewer_the_path_adds_only_count_and_duplicate_player_buffer(self):
        for language in self.each():
            raw, fixed = member227(language), fixed227(language)
            for party in range(6):
                for choice in (0, 1):
                    old = ran(language, raw, party, choice, entry_offset(raw))
                    new = ran(language, fixed, party, choice, entry_offset(fixed))
                    with self.subTest(party=party, choice=choice):
                        expected = moved(old.events, 450, 20)
                        self.assertEqual(new.events, expected[:3] + [('GetPartyCount', (0x8005,)),
                                                                   ('BufferPlayersName', (0,))] + expected[3:])
                        self.assertEqual((new.returned, new.mode, new.asserts), (0, 0, 0))
                        self.assertEqual([new.var(v) for v in range(0x8000, 0x8010)],
                                         [old.var(v) for v in range(0x8000, 0x8010)])
                        self.assertIn(('GiveMon', (133, 5, 0, 0, 0, 0x800C)), new.events)
                        self.assertIn(('SetFlag', (16220,)), new.events)

    def test_with_a_full_party_the_script_says_so_gives_nothing_and_returns_the_control(self):
        message = scripts.load_guard_recipe()['message']
        for language in self.each():
            fixed = fixed227(language)
            for choice in (0, 1):
                run = ran(language, fixed, 6, choice, entry_offset(fixed))
                with self.subTest(choice=choice):
                    self.assertEqual(run.events, [
                        ('PlaySE', (1500,)), ('LockAll', ()), ('FacePlayer', ()), ('GetPartyCount', (0x8005,)),
                        ('MsgBoxExtern', (message['bank'], message['index'])), ('WaitButton', ()), ('CloseMsg', ()),
                        ('ReleaseAll', ())])
                    self.assertEqual((run.returned, run.mode, run.asserts), (0, 0, 0))     # End: stopped, no assert
                    names = run.names_run()
                    for forbidden in ('GiveMon', 'SetFlag', 'HidePerson', 'NicknameInput', 'BufferPlayersName', 'NPCMsg',
                                      'PlayFanfare', 'FadeScreen'):
                        self.assertNotIn(forbidden, names)
                    self.assertEqual(run.var(0x8005), 6)
                    self.assertEqual([run.var(v) for v in range(0x8000, 0x8010) if v != 0x8005],
                                     [SENTINEL] * 15, 'no other script variable is touched')

    def test_the_refusal_is_repeatable(self):
        """Nothing persistent is written, so talking again with a free slot delivers the Eevee as before."""
        for language in self.each():
            fixed = fixed227(language)
            refused = ran(language, fixed, 6, 0, entry_offset(fixed))
            self.assertFalse({'SetFlag', 'HidePerson', 'GiveMon'} & set(refused.names_run()))
            delivered = ran(language, fixed, 5, 0, entry_offset(fixed))
            self.assertIn(('SetFlag', (16220,)), delivered.events)

    def test_only_the_eevee_entry_can_reach_the_give_and_the_other_entries_are_untouched(self):
        for language in self.each():
            raw, fixed = member227(language), fixed227(language)
            old, new = scripts.decode(raw, commands(), EEVEE_MEMBER), scripts.decode(fixed, commands(), EEVEE_MEMBER)
            for index, (a, b) in enumerate(zip(old.entry, new.entry)):
                if index == 11:
                    continue
                for count in (5, 6):
                    one = ran(language, raw, count, 0, a)
                    two = ran(language, fixed, count, 0, b)
                    with self.subTest(entry=index, party=count):
                        self.assertEqual(two.events, moved(one.events, 450, 20))
