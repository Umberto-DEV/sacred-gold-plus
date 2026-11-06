"""Read-only audit of the gift-script fixes: the native dispatch facts behind the six ribbon tails.

`audit_rom` never writes anything. It reads the script archive and the ARM9 of one in-memory
cartridge image and reports

* the native command dispatcher facts (table, count, fanfare handler width, rejection of
  out-of-range opcodes), including an ARM execution probe of the real routines inside Unicorn;
* every script member's decode state, with every decoder error and every overlapping instruction;
* the award trace of each repaired ribbon tail.

The party-full guard of the Eevee gift (member 227) has its own independent read-back in
`gifts_scripts.verify_party_guard`, and its execution proof in test_gifts_audit_rom (cartridge dispatcher in Unicorn).

`require_complete_audit` is the admission gate: it raises ValueError (naming the member) on any
decode error, on a native fact that differs from the pinned guards, or on a ribbon tail that is not
repaired. The gift-delivery census (84 delivery sites, event bindings) went away with the abandoned
delivery-to-boxes feature.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from sgp13 import mew
from sgp131 import gifts_scripts as scripts
from sgp12.rom import valida_layout_arm9

DATA = Path(__file__).resolve().parent / 'data'
GUARDS_PATH = DATA / 'gifts-native-guards.json'
CLAIMS_PATH = DATA / 'gifts-claims.json'
SCRIPT_ARCHIVE = 'a/0/1/2'
SCHEMA = 2

# stack of the native probe lives in a scratch page outside the cartridge map
SCRATCH = 0x02300000
TRAP = 0x02301000


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_guards(path=GUARDS_PATH):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load_claims(path=CLAIMS_PATH):
    """The pinned recipes (ribbon tails, accepted overlap, party guard)."""
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load_commands(path):
    """Pinned scrcmd.json, with its digest attached for the receipt."""
    commands, digest = mew.load_commands(path)
    commands.metadata_sha256 = digest
    return commands


# --------------------------------------------------------------------------
# ARM9 view of an in-memory cartridge image (same walk as sgp12.rom.Arm9)

class Arm9View:
    def __init__(self, data):
        if len(data) < 0x200:
            raise ValueError('not a DS image')
        self.raw = data
        off9, ram9, size9 = struct.unpack_from('<III', data, 0x20)[0], struct.unpack_from('<I', data, 0x28)[0], \
            struct.unpack_from('<I', data, 0x2C)[0]
        self.off9, self.ram9, self.size9 = off9, ram9, size9
        _t0, _t1, _d0, _sections, self.segments = valida_layout_arm9(
            data, off9, ram9, size9)

    def offset(self, address, length=1):
        for base, offset, size in self.segments:
            if base <= address and address + length <= base + size:
                return offset + (address - base)
        raise KeyError(f'{address:#010x}+{length} is not inside a static ARM9 segment')

    def read(self, address, length):
        start = self.offset(address, length)
        return bytes(self.raw[start:start + length])

    def u32(self, address):
        return struct.unpack('<I', self.read(address, 4))[0]

    def has(self, address, length=1):
        try:
            self.offset(address, length)
            return True
        except KeyError:
            return False


def _addr(text):
    return int(text, 16) if isinstance(text, str) else int(text)


# --------------------------------------------------------------------------
# native facts and the executed ARM probe

def native_facts(view, guards, rom=None):
    """Compare the cartridge against the pinned dispatch facts."""
    table = _addr(guards['command_table']['address'])
    count = view.u32(_addr(guards['command_table']['count_address']))
    literals = struct.unpack('<2I', view.read(_addr(guards['command_table']['init_literal_address']), 8))
    dispatcher = guards['dispatcher']
    reader = guards['script_read_halfword']
    fan = guards['fanfare']
    facts = {
        'table_address': table, 'count': count,
        'init_literals': list(literals),
        'init_literals_match': list(literals) == [_addr(x) for x in guards['command_table']['init_literals']],
        'dispatcher_sha256': sha256(view.read(_addr(dispatcher['address']), dispatcher['bytes'])),
        'reader_sha256': sha256(view.read(_addr(reader['address']), reader['bytes'])),
        'fanfare_entry': view.u32(table + 4 * fan['opcode']),
        'fanfare_handler_sha256': sha256(view.read(_addr(fan['handler']), fan['bytes'])),
        'handlers': {},
    }
    facts['count_matches'] = count == guards['command_table']['count']
    facts['dispatcher_matches'] = facts['dispatcher_sha256'] == dispatcher['sha256']
    facts['reader_matches'] = facts['reader_sha256'] == reader['sha256']
    facts['fanfare_entry_matches'] = facts['fanfare_entry'] == _addr(fan['entry'])
    facts['fanfare_handler_matches'] = facts['fanfare_handler_sha256'] == fan['sha256']
    api = guards['script_api']
    facts['script_api_matches'] = all(
        sha256(view.read(_addr(api[name]['address']), 16)) == api[name]['prologue_sha256']
        for name in ('read_halfword', 'var_pointer'))
    for op, handler in guards['handlers'].items():
        entry = view.u32(table + 4 * int(op))
        facts['handlers'][op] = {'name': handler['name'], 'entry': entry,
                                 'matches': entry == _addr(handler['entry']),
                                 'prologue_matches': _prologue_matches(view, rom, handler, entry)}
    return facts


def _prologue_matches(view, rom, handler, entry):
    """16 bytes at the handler entry: same address with a different body must not pass (static ARM9 only)."""
    address = entry & ~1
    return view.has(address, 16) and sha256(view.read(address, 16)) == handler['prologue_sha256']


def reached_close_msg(consumed_bytes):
    """opcode 78 (2) + operand (2) + refused halfword 2009 (2) = 6; reading CloseMsg would make it >= 8."""
    return consumed_bytes >= 8


def native_probe(view, guards):
    """Run the REAL ScriptReadHalfword, PlayFanfare handler and RunScriptCommand.

    Only the OS (assert/var-resolve/sound) is seamed; every other instruction is
    the cartridge's own. The script is the defective award tail:
    `PlayFanfare 20` followed by the stray halfword 2009.
    """
    from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB, Uc
    from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1,
                                   UC_ARM_REG_SP)

    mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    base, size = 0x02000000, 0x00120000
    mu.mem_map(base, size)
    static = view.read(base, view.segments[0][2])
    mu.mem_write(base, static)
    mu.mem_map(SCRATCH, 0x4000)
    mu.mem_write(TRAP, b'\x00\xbe')

    dispatcher = _addr(guards['dispatcher']['address'])
    reader = _addr(guards['script_read_halfword']['address'])
    handler = _addr(guards['fanfare']['handler'])
    assert_address = _addr(guards['dispatcher']['assert_routine'])
    resolve_address, sound_address = _addr(guards['fanfare']['callees'][1]), _addr(guards['fanfare']['callees'][2])
    table = _addr(guards['command_table']['address'])
    count = view.u32(_addr(guards['command_table']['count_address']))
    ctx, script, fieldsys = SCRATCH, SCRATCH + 0x200, SCRATCH + 0x400
    events = {'assert': 0, 'resolve': [], 'sound': 0, 'trap': 0}

    def hook(uc, address, length, user):
        if address == assert_address:
            events['assert'] += 1
        elif address == resolve_address:
            events['resolve'].append(uc.reg_read(UC_ARM_REG_R1))
        elif address == sound_address:
            events['sound'] += 1
        else:
            return
        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    mu.hook_add(UC_HOOK_CODE, hook)

    def fresh(script_bytes, mode=1):
        mu.mem_write(ctx, bytes(0x90))
        mu.mem_write(script, bytes(0x40))
        mu.mem_write(script, script_bytes)
        mu.mem_write(ctx + 1, bytes([mode]))
        mu.mem_write(ctx + 8, struct.pack('<I', script))
        mu.mem_write(ctx + 0x5C, struct.pack('<I', table))
        mu.mem_write(ctx + 0x60, struct.pack('<I', count))
        mu.mem_write(ctx + 0x80, struct.pack('<I', fieldsys))
        events['assert'], events['resolve'], events['sound'] = 0, [], 0

    def call(address, r0):
        mu.reg_write(UC_ARM_REG_R0, r0)
        mu.reg_write(UC_ARM_REG_SP, SCRATCH + 0x3F00)
        mu.reg_write(UC_ARM_REG_LR, TRAP | 1)
        mu.emu_start(address | 1, TRAP, count=100000)
        if mu.reg_read(UC_ARM_REG_PC) != TRAP:
            raise AssertionError('probe did not return')
        return mu.reg_read(UC_ARM_REG_R0)

    pointer = lambda: struct.unpack('<I', bytes(mu.mem_read(ctx + 8, 4)))[0]
    mode = lambda: bytes(mu.mem_read(ctx + 1, 1))[0]
    defective = struct.pack('<HHHHHH', 78, 20, 2009, 53, 97, 2)

    fresh(defective)
    value = call(reader, ctx)
    reader_probe = {'value': value, 'advance': pointer() - script}

    fresh(struct.pack('<HH', 20, 2009))
    call(handler, ctx)
    handler_probe = {'advance': pointer() - script, 'operand_resolved': list(events['resolve']),
                     'sound_calls': events['sound']}

    fresh(defective)
    returned = call(dispatcher, ctx)
    dispatch_probe = {
        'returned': returned, 'mode_after': mode(), 'asserts': events['assert'],
        'operand_resolved': list(events['resolve']), 'sound_calls': events['sound'],
        'consumed_bytes': pointer() - script,
        'reached_close_msg': False,
    }
    # opcode 78 (2) + its operand (2) + the refused halfword 2009 (2) = 6 bytes; CloseMsg would make it 8.
    dispatch_probe['reached_close_msg'] = reached_close_msg(dispatch_probe['consumed_bytes'])
    return {'reader': reader_probe, 'fanfare_handler': handler_probe, 'defective_tail': dispatch_probe}


# --------------------------------------------------------------------------
# archives

def _archives(data):
    import ndspy.narc
    import ndspy.rom
    rom = ndspy.rom.NintendoDSRom(data)
    return rom, ndspy.narc.NARC(rom.getFileByName(SCRIPT_ARCHIVE)).files


# --------------------------------------------------------------------------
# the audit

def audit_rom(data, language, commands, claims=None, guards=None, probe=True):
    """Return the complete read-only receipt for one cartridge image."""
    claims = claims or load_claims()
    guards = guards or load_guards()
    if language not in ('EN', 'IT'):
        raise ValueError('unsupported language')
    view = Arm9View(data)
    rom, files = _archives(data)
    receipt = {
        'schema': SCHEMA, 'language': language,
        'rom_sha256': sha256(data), 'rom_bytes': len(data),
        'metadata_sha256': getattr(commands, 'metadata_sha256', None),
        'metadata_commands': len(commands),
        'guards_sha256': sha256(json.dumps(guards, sort_keys=True).encode()),
        'claims_sha256': sha256(json.dumps(claims, sort_keys=True).encode()),
        'native': native_facts(view, guards, rom),
    }
    if probe:
        receipt['native_probe'] = native_probe(view, guards)
    decode_errors, overlaps, members = [], [], {'event': 0, 'init': 0, 'other': []}
    decoded = {}
    for member_id, raw in enumerate(files):
        raw = bytes(raw)
        member = mew.decoder().Membro(member_id, raw, commands).cammina()
        if member.tipo == 'init':
            members['init'] += 1
            continue
        if member.tipo != 'evento':
            members['other'].append(member_id)
            decode_errors.append({'member': member_id, 'error': 'header not recognized', 'offset': None,
                                  'previous': []})
            continue
        members['event'] += 1
        for error in member.errori:
            offset = int(error.rsplit(' ', 1)[-1]) if error.rsplit(' ', 1)[-1].isdigit() else None
            previous = [(hex(o), i.testo()) for o, i in sorted(member.istruzioni.items())
                        if offset is not None and i.fine <= offset][-1:]
            decode_errors.append({'member': member_id, 'error': error, 'offset': offset,
                                  'previous': previous})
        for first, second in scripts.overlapping_instructions(member):
            overlaps.append({'member': member_id, 'first': first, 'second': second,
                             'member_sha256': sha256(raw), 'accepted': _overlap_accepted(
                                 claims, member_id, sha256(raw), first, second)})
        decoded[member_id] = member
    receipt.update({
        'members': {'event': members['event'], 'init': members['init'], 'unrecognized': members['other'],
                    'total': len(files)},
        'decode_errors': decode_errors, 'overlapping_instructions': overlaps,
        'ribbon_tails': _ribbon_state(decoded, claims),
    })
    return receipt


def _overlap_accepted(claims, member_id, digest, first, second):
    for allowance in claims.get('accepted_overlaps', ()):
        if (allowance['member'] == member_id and digest in allowance['preimage_sha256'].values()
                and [first, second] in allowance['pairs']):
            return True
    return False


def _ribbon_state(decoded, claims):
    """Per ribbon member: errors left, and whether the award trace is the reference one."""
    recipe = claims['ribbon_tails']
    result = {}
    for key, member_recipe in recipe['members'].items():
        member = decoded.get(int(key))
        state = {'errors': list(member.errori) if member else ['missing'], 'trace_ok': False}
        if member is not None:
            site = member.istruzioni.get(member_recipe['ribbon_site'])
            try:
                if site is not None and site.op == scripts.OP_GIVERIBBON and not member.errori:
                    state['trace_ok'] = scripts._trace_from(member, site.off) == \
                        scripts._expected_trace(recipe, member_recipe)
            except ValueError:
                pass
        result[key] = state
    return result


# --------------------------------------------------------------------------
# admission gate

def _fail(problems):
    if problems:
        raise ValueError('gift audit is not complete: ' + '; '.join(problems))


def require_complete_audit(receipt):
    """Raise ValueError naming every blocker; return None when nothing blocks."""
    problems = []
    native = receipt.get('native', {})
    for key in ('count_matches', 'dispatcher_matches', 'reader_matches', 'fanfare_entry_matches',
                'fanfare_handler_matches', 'script_api_matches'):
        if not native.get(key):
            problems.append(f'native fact {key} differs from the pinned guards')
    for op, handler in native.get('handlers', {}).items():
        if not handler['matches']:
            problems.append(f"command table entry {op} ({handler['name']}) differs from the pinned guard")
        elif not handler.get('prologue_matches'):
            problems.append(f"handler {op} ({handler['name']}) has a different body at the pinned entry")
    probe = receipt.get('native_probe')
    if probe is None:
        problems.append('native ARM probe was not executed')
    else:
        if (probe['reader']['advance'] != 2 or probe['reader']['value'] != 78
                or probe['fanfare_handler']['advance'] != 2
                or probe['fanfare_handler']['operand_resolved'] != [20]):
            problems.append('PlayFanfare does not consume exactly one halfword (the operand 20)')
        tail = probe['defective_tail']
        if (tail['asserts'] != 1 or tail['mode_after'] != 0 or tail['returned'] != 0
                or tail['consumed_bytes'] != 6 or tail['reached_close_msg']):
            problems.append('native dispatch does not reject opcode 2009')
    for error in receipt.get('decode_errors', []):
        problems.append(f"member {error['member']}: {error['error']}")
    for overlap in receipt.get('overlapping_instructions', []):
        if overlap.get('accepted'):
            continue
        problems.append(f"member {overlap['member']}: overlapping instructions at "
                        f"{overlap['first']:#x}/{overlap['second']:#x}")
    if receipt.get('members', {}).get('unrecognized'):
        problems.append('unrecognized script members ' + str(receipt['members']['unrecognized']))
    for key, state in receipt.get('ribbon_tails', {}).items():
        if state['errors'] or not state['trace_ok']:
            problems.append(f'ribbon tail of member {key} is not repaired')
    _fail(problems)


def summarize(receipt):
    return {key: receipt[key] for key in ('language', 'rom_sha256', 'members')} | {
        'decode_errors': [f"{e['member']}:{e['error']}" for e in receipt['decode_errors']]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True)
    parser.add_argument('--language', required=True, choices=('EN', 'IT'))
    parser.add_argument('--commands', required=True, help='pinned tools/py_scripts/scrcmd.json')
    parser.add_argument('--report', required=True, help='small JSON receipt (the only file written)')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args(argv)
    data = Path(args.rom).read_bytes()
    receipt = audit_rom(data, args.language, load_commands(args.commands))
    Path(args.report).write_text(json.dumps(receipt, indent=1) + '\n')
    print(json.dumps(summarize(receipt), indent=1))
    if args.require_complete:
        try:
            require_complete_audit(receipt)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
