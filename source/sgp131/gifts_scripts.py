"""Guarded script-member rewriting for the two gift-script fixes.

Two bug fixes of the inherited scripts, nothing else (the delivery of gifts to PC boxes was abandoned):
(1) the repair of six ribbon-award tails (below); (2) the party-full guard of the Eevee gift of member 227
(`transform_party_guard`, at the end of this module).

One coordinate transformation, driven by explicit byte edits in the ORIGINAL
member coordinates, rewrites the entry table and every relative operand the
public decoder (`features/borsa/tools/scr_disasm.py`, never modified) can see.
A branch that lands inside a replaced interior is refused; so is any
instruction that straddles an edit, any overlapping edit, and any replacement
that itself carries a relative operand.

The first product recipe is the repair of six inherited ribbon-award tails.
Each of members 225/232/243/246/938/962 contains, right after `GiveRibbon`, the 12 bytes
`4E00 1400 D907 3500 6100 0200`: opcode 78 (`PlayFanfare`) read together with the next word
`1400` as its operand 20, then the halfword `D907` = 2009. The editor had spliced the `CallStd 2009`
of the "bag is full" tail (`1400 D907` is exactly that command) over the real award tail and left
the `4E00` in front of it. The native dispatcher refuses opcode 2009 (the command table has 853
entries), so the award scene stops before `CloseMsg`/`ReleaseAll`. The retail reference tail
(pret `scr_seq_*.s`, same ribbon, same message flow, same daily flag that the
member still tests at its entry) is

    PlayFanfare SEQ_ME_ITEM; WaitFanfare; SetFlag FLAG_DAILY_GOT_SHOCK_RIBBON;
    WaitButton; CloseMsg; ReleaseAll; End

The inherited bytes already hold `CloseMsg; ReleaseAll; End` right behind the
stray halfword, so the minimal repair replaces only those 6 bytes with the 12
bytes of the first four commands (net +6 bytes). Nothing else changes except
the relocation implied by the six extra bytes.
"""
import hashlib
import json
from pathlib import Path
import struct

from sgp13 import mew

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_PATH = Path(__file__).resolve().parent / 'data' / 'gifts-claims.json'
ARCHIVE = 'a/0/1/2'
RIBBON_MEMBERS = (225, 232, 243, 246, 938, 962)
OP_END, OP_CALLSTD = 2, 20
OP_SETFLAG, OP_WAITBUTTON, OP_CLOSEMSG = 30, 50, 53
OP_PLAYFANFARE, OP_WAITFANFARE, OP_RELEASEALL = 78, 79, 97
OP_GIVERIBBON = 481
ILLEGAL_STD_OPERAND = 2009
RIBBON_VAR = 0x8002


def decoder():
    return mew.decoder()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_recipe(path=CLAIMS_PATH):
    """The public ribbon-repair recipe (hashes and numbers only, no game bytes)."""
    document = json.loads(Path(path).read_text(encoding='utf-8'))
    recipe = document['ribbon_tails']
    if set(recipe['members']) != {str(m) for m in RIBBON_MEMBERS}:
        raise ValueError('ribbon recipe does not list exactly the six known members')
    return recipe


def _op(opcode):
    return struct.pack('<H', opcode)


def _arg(value):
    return struct.pack('<H', value)


def replacement_bytes(recipe):
    """PlayFanfare <sound>; WaitFanfare; SetFlag <daily>; WaitButton (12 bytes)."""
    ref = recipe['reference']
    return (_op(OP_PLAYFANFARE) + _arg(ref['sound']) + _op(OP_WAITFANFARE)
            + _op(OP_SETFLAG) + _arg(ref['daily_flag']) + _op(OP_WAITBUTTON))


# --------------------------------------------------------------------------
# generic decoding helpers

def decode(raw, commands, member_id=0, allowed_errors=()):
    """Decode a member; every decoder error must be listed in allowed_errors."""
    member = decoder().Membro(member_id, bytes(raw), commands).cammina()
    unexpected = [e for e in member.errori if e not in allowed_errors]
    if (not member.header_valido or not member.entry
            or any(entry < member.header_end for entry in member.entry) or unexpected
            or member.riassembla()[0] is not True):
        raise ValueError('script member decoding failed: ' + '; '.join(unexpected or member.errori
                                                                       or ['invalid header']))
    return member


def overlapping_instructions(member):
    """Instruction pairs whose byte ranges overlap: a branch into an interior."""
    result, previous = [], None
    for offset in sorted(member.istruzioni):
        ins = member.istruzioni[offset]
        if previous is not None and offset < previous.fine:
            result.append((previous.off, offset))
        previous = ins if previous is None or ins.fine > previous.fine else previous
    return result


def movement_end(raw, start):
    cursor = start
    while cursor + 2 <= len(raw):
        if struct.unpack_from('<H', raw, cursor)[0] == 0xFE:
            return cursor + 2
        if cursor + 4 > len(raw):
            break
        cursor += 4
    raise ValueError('movement has no complete FE terminator')


def incoming_edges(member):
    """Every explicit relative edge as (source_instruction, destination, kind)."""
    edges = []
    for ins in member.istruzioni.values():
        for _, destination, kind in ins.rami:
            edges.append((ins.off, destination, kind))
    return edges


def entry_edges(member):
    return [(f'entry{index}', destination, 'entry') for index, destination in enumerate(member.entry)]


# --------------------------------------------------------------------------
# the one coordinate transformation

class Edit:
    """Replace raw[start:end] (old coordinates) with `data`."""

    def __init__(self, start, end, data, fixups=()):
        """`fixups`: (offset inside data, target) pairs for the 4-byte relative operands of the inserted
        commands. A target is ('old', offset in the ORIGINAL member) or ('edit', Edit, offset inside that
        edit's data); both are resolved after the one coordinate transformation, so no address is guessed."""
        if not 0 <= start <= end:
            raise ValueError('invalid edit bounds')
        self.start, self.end, self.data = start, end, bytes(data)
        self.fixups = tuple(fixups)

    @property
    def delta(self):
        return len(self.data) - (self.end - self.start)


def _check_edits(raw, edits):
    ordered = sorted(edits, key=lambda e: (e.start, e.end))
    for previous, current in zip(ordered, ordered[1:]):
        if current.start < previous.end:
            raise ValueError('overlapping edits')
    for edit in ordered:
        if edit.end > len(raw):
            raise ValueError('edit outside the member')
    return ordered


def coordinate_map(edits):
    """old offset -> new offset; interior offsets of a replaced range are refused."""
    ordered = sorted(edits, key=lambda e: (e.start, e.end))

    def mapping(offset):
        total = 0
        for edit in ordered:
            if edit.start < offset < edit.end:
                raise ValueError(f'branch into replaced interior at {offset:#x} '
                                 f'(edit {edit.start:#x}..{edit.end:#x})')
            if edit.end <= offset:
                total += edit.delta
        return offset + total
    return mapping


def _check_replacement(data, commands, fixup_offsets=()):
    """The inserted bytes must be whole commands; a relative operand is allowed only at a declared fixup."""
    sd = decoder()
    cursor = 0
    while cursor < len(data):
        if cursor + 2 > len(data):
            raise ValueError('replacement ends inside a command')
        op = struct.unpack_from('<H', data, cursor)[0]
        if op >= len(commands):
            raise ValueError('replacement contains an opcode outside the command table')
        args, extra = commands.arg_list(op, None)
        if extra is not None:
            raise ValueError('replacement command with variable operands is not supported')
        cursor += 2
        for kind in args:
            if kind in sd.RELATIVE and cursor not in fixup_offsets:
                raise ValueError('replacement carries a relative operand')
            cursor += kind if isinstance(kind, int) else sd.ARG_SIZES[kind]
        if cursor > len(data):
            raise ValueError('replacement ends inside a command')


def unreachable_relative_operands(member, raw):
    """Relative commands that sit in bytes the walk never reached (dead code, outside movement data).

    The coordinate transformation only rewrites decoded instructions, so a dead command whose operand
    would cross an edit could not be relocated. Each uncovered gap is scanned linearly from its start and
    the scan stops at the first byte that does not decode: nothing is guessed.
    """
    saved = list(member.errori)
    moves = [(s, movement_end(raw, s)) for s in member.dati_movimento]
    found = []
    for start, end in member.regioni_scoperte():
        position = start
        while position < end:
            if any(a <= position < b for a, b in moves):
                break
            ins = member._decodifica(position)
            if ins is None or ins.fine > end:
                break
            if ins.rami:
                found.append((ins.off, [d for _, d, _ in ins.rami]))
            position = ins.fine
    member.errori[:] = saved
    return found


def relocate(raw, commands, edits, member_id=0, allowed_errors=()):
    """Apply edits and relocate the entry table and all decoded relative operands.

    The old image is decoded once (errors listed in `allowed_errors` are the
    known defects the edit repairs). Instructions that overlap an edit vanish
    with it; an instruction straddling an edit boundary, or a replacement that
    would itself need relocation, is refused.
    """
    raw = bytes(raw)
    ordered = _check_edits(raw, edits)
    old = decode(raw, commands, member_id, allowed_errors)
    mapping = coordinate_map(ordered)
    sd = decoder()
    for offset, destinations in unreachable_relative_operands(old, raw):
        for edit in ordered:
            crossing = offset < edit.start and any(d >= edit.end for d in destinations) or \
                offset >= edit.end and any(d < edit.start for d in destinations)
            if crossing and edit.delta:
                raise ValueError(f'unreachable command at {offset:#x} has a relative operand across an edit '
                                 'and cannot be relocated')
    for edit in ordered:
        for ins in old.istruzioni.values():
            overlaps = ins.off < edit.end and ins.fine > edit.start
            contained = edit.start <= ins.off and ins.fine <= edit.end
            if overlaps and not contained and edit.end > edit.start:
                raise ValueError(f'instruction at {ins.off:#x} straddles edit {edit.start:#x}..{edit.end:#x}')
        _check_replacement(edit.data, commands, {offset for offset, _ in edit.fixups})
    chunks, cursor = [], 0
    for edit in ordered:
        chunks.extend((raw[cursor:edit.start], edit.data))
        cursor = edit.end
    chunks.append(raw[cursor:])
    result = bytearray(b''.join(chunks))
    for index, entry in enumerate(old.entry):
        struct.pack_into('<I', result, 4 * index, (mapping(entry) - (4 * index + 4)) & 0xFFFFFFFF)
    removed = [(e.start, e.end) for e in ordered if e.end > e.start]

    def vanishes(ins):
        return any(start <= ins.off < end for start, end in removed)

    for ins in old.istruzioni.values():
        if vanishes(ins):
            continue
        cursor = ins.off + 2
        for value, kind in zip(ins.args, ins.tipi):
            size = kind if isinstance(kind, int) else sd.ARG_SIZES[kind]
            if kind in sd.RELATIVE:
                destination = (value + cursor + size) & 0xFFFFFFFF
                relative = (mapping(destination) - (mapping(cursor) + size)) & 0xFFFFFFFF
                struct.pack_into('<I', result, mapping(cursor), relative)
            cursor += size
    for edit in ordered:
        placed = mapping(edit.start) - (edit.delta if edit.start == edit.end else 0)
        for offset, target in edit.fixups:
            if target[0] == 'old':
                destination = mapping(target[1])
            elif target[0] == 'edit':
                other = target[1]
                destination = mapping(other.start) - (other.delta if other.start == other.end else 0) + target[2]
            else:
                raise ValueError('unknown fixup target')
            struct.pack_into('<I', result, placed + offset, (destination - (placed + offset + 4)) & 0xFFFFFFFF)
    return bytes(result), mapping, old


# --------------------------------------------------------------------------
# ribbon-tail recipe

def _member_recipe(recipe, member_id):
    try:
        return recipe['members'][str(member_id)]
    except KeyError:
        raise ValueError(f'member {member_id} is not part of the ribbon recipe') from None


def expected_error(member_recipe):
    return f"opcode illegale {ILLEGAL_STD_OPERAND} a {member_recipe['illegal_offset']}"


def locate_tail(raw, old, member_recipe, recipe):
    """Prove the exact inherited shape of the defective award tail."""
    site = member_recipe['tail_site']
    giver = old.istruzioni.get(member_recipe['ribbon_site'])
    if giver is None or giver.op != OP_GIVERIBBON or giver.fine != site:
        raise ValueError('ribbon tail: GiveRibbon does not end exactly at the tail site')
    if giver.args != [RIBBON_VAR, member_recipe['ribbon']]:
        raise ValueError('ribbon tail: ribbon constant or target variable differs from the recipe')
    play = old.istruzioni.get(site)
    bad = bytes.fromhex(recipe['inherited_tail_hex'])
    if (play is None or play.op != OP_PLAYFANFARE or raw[site:site + 6] != bad
            or play.args != [recipe['inherited_sound']]):
        raise ValueError('ribbon tail: inherited PlayFanfare/stray-halfword bytes differ')
    if struct.unpack_from('<H', raw, site + 4)[0] != ILLEGAL_STD_OPERAND:
        raise ValueError('ribbon tail: stray halfword is not 2009')
    kept = bytes.fromhex(recipe['kept_continuation_hex'])
    if raw[site + 6:site + 6 + len(kept)] != kept:
        raise ValueError('ribbon tail: CloseMsg/ReleaseAll/End continuation differs')
    after = old.istruzioni.get(site + 6 + len(kept))
    if after is None or after.op != OP_CALLSTD or after.args != [ILLEGAL_STD_OPERAND]:
        raise ValueError('ribbon tail: the independently reached bag-full CallStd tail is missing')
    # the message flow before the ribbon must be the reference one
    lead = [old.istruzioni[o] for o in sorted(old.istruzioni) if o < member_recipe['ribbon_site']][-4:]
    m0, m1 = member_recipe['messages']
    if ([i.nome for i in lead] != ['GetStdMsgNaix', 'MsgBoxExtern', 'BufferMonSpeciesName', 'MsgBoxExtern']
            or [i.args for i in lead] != [[0, 0x800C], [0x800C, m0], [0, RIBBON_VAR], [0x800C, m1]]
            or lead[-1].fine != member_recipe['ribbon_site']):
        raise ValueError('ribbon tail: message lead-in differs from the reference flow')
    # every explicit edge into the defective 6 bytes or the retained continuation
    # must be accounted for; only the fallthrough from GiveRibbon exists today.
    for source, destination, kind in incoming_edges(old) + entry_edges(old):
        if site < destination < site + 6:
            raise ValueError(f'ribbon tail: branch into replaced interior at {destination:#x}')
    return site


def patch_member(raw, language, member_id, commands, recipe):
    """Return the repaired member; raise ValueError on any foreign state."""
    raw = bytes(raw)
    member_recipe = _member_recipe(recipe, member_id)
    if language not in member_recipe['preimage_sha256']:
        raise ValueError('unsupported ribbon repair language')
    if sha256(raw) != member_recipe['preimage_sha256'][language]:
        raise ValueError(f'ribbon member {member_id} preimage does not match; foreign or already patched input')
    old = decode(raw, commands, member_id, (expected_error(member_recipe),))
    if set(old.errori) != {expected_error(member_recipe)}:
        raise ValueError('ribbon member must show exactly the one known decoder error before repair')
    site = locate_tail(raw, old, member_recipe, recipe)
    edit = Edit(site, site + 6, replacement_bytes(recipe))
    result, _, _ = relocate(raw, commands, [edit], member_id, (expected_error(member_recipe),))
    report = verify_member(raw, result, commands, recipe)
    if report['member'] != member_id:
        raise ValueError('ribbon repair verification identified a different member')
    return result


def _expected_trace(recipe, member_recipe):
    ref = recipe['reference']
    return [('GiveRibbon', [RIBBON_VAR, member_recipe['ribbon']]), ('PlayFanfare', [ref['sound']]),
            ('WaitFanfare', []), ('SetFlag', [ref['daily_flag']]), ('WaitButton', []),
            ('CloseMsg', []), ('ReleaseAll', []), ('End', [])]


def _trace_from(member, start):
    trace, cursor = [], start
    while cursor in member.istruzioni:
        ins = member.istruzioni[cursor]
        trace.append((ins.nome, list(ins.args)))
        if member.cmds.is_abs_branch(ins.op):
            return trace
        cursor = ins.fine
    raise ValueError('trace leaves decoded code')


def verify_member(before, after, commands, recipe):
    """Independent read-back: decode both images and compare semantics and bytes."""
    before, after = bytes(before), bytes(after)
    digest = sha256(before)
    owner = sorted({(int(m), l) for m, r in recipe['members'].items()
                    for l, h in r['preimage_sha256'].items() if h == digest})
    if not owner or len({m for m, _ in owner}) != 1:
        raise ValueError('verify_member: the before image is not a known ribbon preimage')
    member_id, language = owner[0][0], [l for _, l in owner]
    member_recipe = _member_recipe(recipe, member_id)
    old = decode(before, commands, member_id, (expected_error(member_recipe),))
    new = decode(after, commands, member_id)
    if new.errori or overlapping_instructions(new):
        raise ValueError('repaired member still has decoder errors or overlapping instructions')
    site = member_recipe['tail_site']
    delta = len(replacement_bytes(recipe)) - 6
    if len(after) != len(before) + delta:
        raise ValueError('repaired member length is not original + replacement delta')

    def shift(offset):
        if site < offset < site + 6:
            raise ValueError('interior offset has no image')
        return offset + (delta if offset >= site + 6 else 0)

    if new.entry != [shift(e) for e in old.entry]:
        raise ValueError('entry table does not map through the single coordinate transformation')
    sd = decoder()
    kept = 0
    for ins in old.istruzioni.values():
        if site <= ins.off < site + 6:
            continue
        other = new.istruzioni.get(shift(ins.off))
        if other is None or (other.op, other.tipi) != (ins.op, ins.tipi):
            raise ValueError(f'instruction at {ins.off:#x} did not survive')
        if other.rami != [(i, shift(d), k) for i, d, k in ins.rami]:
            raise ValueError(f'relative targets of {ins.off:#x} were not remapped')
        if any(a != b for a, b, k in zip(ins.args, other.args, ins.tipi) if k not in sd.RELATIVE):
            raise ValueError(f'non-relative operands of {ins.off:#x} changed')
        kept += 1
    # bytes outside the replaced range, the entry words and relative operand fields
    # are byte-for-byte identical; movement bytes included.
    mask_before, mask_after = bytearray(before), bytearray(after)
    for index in range(len(old.entry)):
        mask_before[4 * index:4 * index + 4] = bytes(4)
        mask_after[4 * index:4 * index + 4] = bytes(4)
    for ins in old.istruzioni.values():
        if site <= ins.off < site + 6:
            continue
        cursor = ins.off + 2
        for value, kind in zip(ins.args, ins.tipi):
            size = kind if isinstance(kind, int) else sd.ARG_SIZES[kind]
            if kind in sd.RELATIVE:
                mask_before[cursor:cursor + size] = bytes(size)
                mask_after[shift(cursor):shift(cursor) + size] = bytes(size)
            cursor += size
    if mask_before[:site] != mask_after[:site] or mask_before[site + 6:] != mask_after[site + 6 + delta:]:
        raise ValueError('bytes outside the replaced tail changed')
    moved = {start: movement_end(before, start) for start in old.dati_movimento}
    if new.dati_movimento != {shift(s) for s in old.dati_movimento}:
        raise ValueError('movement targets were not remapped')
    for start, end in moved.items():
        if after[shift(start):shift(start) + end - start] != before[start:end]:
            raise ValueError('movement bytes changed')
    ribbon = new.istruzioni[member_recipe['ribbon_site']]
    if _trace_from(new, ribbon.off) != _expected_trace(recipe, member_recipe):
        raise ValueError('ribbon award trace differs from the reference tail')
    # incoming edges: the only way in is the GiveRibbon fall-through; entries and
    # branch targets that were valid before still land on instruction starts.
    for source, destination, kind in incoming_edges(new):
        if destination not in new.istruzioni and kind != 'movement':
            raise ValueError('a branch target is not an instruction start')
    return {
        'member': member_id, 'language': language,
        'preimage_sha256': digest, 'output_sha256': sha256(after),
        'input_bytes': len(before), 'output_bytes': len(after),
        'old_errors': old.errori, 'new_errors': new.errori,
        'instructions_before': len(old.istruzioni), 'instructions_after': len(new.istruzioni),
        'instructions_preserved': kept, 'entries': len(new.entry),
        'trace': [name for name, _ in _trace_from(new, ribbon.off)],
        'uncovered_bytes_before': sum(b - a for a, b in old.regioni_scoperte()),
        'uncovered_bytes_after': sum(b - a for a, b in new.regioni_scoperte()),
    }



# --------------------------------------------------------------------------
# the party-full guard of the Eevee gift (member 227)

def load_guard_recipe(path=CLAIMS_PATH):
    """The pinned recipe of the Eevee party guard (hashes and numbers only)."""
    return json.loads(Path(path).read_text(encoding='utf-8'))['party_guard']


_OP_NAMES = {}


def _names(commands):
    key = id(commands)
    if key not in _OP_NAMES:
        _OP_NAMES[key] = {name: index for index, name in enumerate(commands.nomi)}
    return _OP_NAMES[key]


def assemble(commands, name, *args):
    """One command from its name; operands are packed by the command table's own sizes."""
    sd = decoder()
    op = _names(commands)[name]
    kinds, _ = commands.arg_list(op, None)
    if len(kinds) != len(args):
        raise ValueError(f'{name} takes {len(kinds)} operands')
    out = _op(op)
    for kind, value in zip(kinds, args):
        size = kind if isinstance(kind, int) else sd.ARG_SIZES[kind]
        out += int(value).to_bytes(size, 'little')
    return out


TERMINATORS = ('End', 'GoTo', 'Return')
COND_EQ = 1                       # GoToIf condition of the retail GoToIfEq
GUARD_LEAD_INS = ('BufferPlayersName', 'NPCMsg')     # the only commands between the guard and the original party count


def _successors(ins, commands):
    out = [dest for _, dest, kind in ins.rami if kind in ('script', 'addr')]
    if commands.nome(ins.op) not in TERMINATORS:
        out.append(ins.fine)
    return out


def forward_reach(member, commands, starts, cut=()):
    """Instruction offsets reachable from `starts` over fall-through and explicit branches. The edges (source,
    destination) listed in `cut` are not followed."""
    cut, seen, work = set(cut), set(), list(starts)
    while work:
        at = work.pop()
        if at in seen or at not in member.istruzioni:
            continue
        seen.add(at)
        work.extend(d for d in _successors(member.istruzioni[at], commands) if (at, d) not in cut)
    return seen


def _effect_sites(member, commands, recipe):
    """The persistent effects of the gift: the give, the flag that records it and the hide of the NPC, plus the
    nickname offer that addresses the new party slot."""
    sites = set()
    for at, ins in member.istruzioni.items():
        name = commands.nome(ins.op)
        if (name == 'GiveMon' and at == recipe['give_site']) or name == 'NicknameInput' \
                or (name == 'SetFlag' and ins.args == [recipe['effects']['flag']]) \
                or (name == 'HidePerson' and ins.args == [recipe['effects']['hide_person']]):
            sites.add(at)
    return sites


def _guard_parts(commands, recipe):
    """(guard bytes with a zero branch operand, offset of that operand, refusal block bytes)."""
    a = assemble
    party, limit, message = recipe['party_var'], recipe['limit'], recipe['message']
    head = a(commands, 'GetPartyCount', party) + a(commands, 'CompareVarToValue', party, limit)
    # BUG-131-01: +17 would make the member's native u16 movement tables odd.
    # Repeat the immediately following original player-name buffer on success
    # only. Its 3 bytes make the insertion +20 without affecting refusal.
    guard = head + a(commands, 'GoToIf', COND_EQ, 0) + a(commands, 'BufferPlayersName', 0)
    block = (a(commands, 'MsgBoxExtern', message['bank'], message['index']) + a(commands, 'WaitButton')
             + a(commands, 'CloseMsg') + a(commands, 'ReleaseAll') + a(commands, 'End'))
    return guard, len(head) + 3, block


def _check_guard_site(old, raw, commands, recipe):
    """Prove the exact V4 shape the guard is built for; every deviation is a refusal."""
    member = recipe['member']
    insert, count_site, give_site, var = recipe['insert_at'], recipe['party_count_site'], recipe['give_site'], \
        recipe['party_var']
    entry = old.entry[recipe['entry']] if recipe['entry'] < len(old.entry) else None
    if entry != recipe['entry_offset']:
        raise ValueError('party guard: the gift entry is not at the pinned offset')
    cursor, lead = entry, []
    for name in recipe['lead_in']:
        ins = old.istruzioni.get(cursor)
        if ins is None or commands.nome(ins.op) != name or ins.rami:
            raise ValueError('party guard: the entry does not open with the pinned lead-in commands')
        lead.append(ins)
        cursor = ins.fine
    if cursor != insert:
        raise ValueError('party guard: the insertion point is not right after the lead-in')
    buffer = old.istruzioni.get(insert)
    if buffer is None or buffer.nome != 'BufferPlayersName' or buffer.args != [0]:
        raise ValueError('party guard: success must repeat the immediate original player-name buffer 0')
    for source, destination, kind in incoming_edges(old) + entry_edges(old):
        if destination == insert:
            raise ValueError('party guard: a branch or entry targets the insertion point and would skip the guard')
    count, give = old.istruzioni.get(count_site), old.istruzioni.get(give_site)
    if count is None or commands.nome(count.op) != 'GetPartyCount' or count.args != [var] or count.fine != give_site:
        raise ValueError('party guard: the original party count is not the pinned GetPartyCount just before the give')
    if (give is None or commands.nome(give.op) != 'GiveMon'
            or give.args != [recipe['species'], recipe['level'], 0, 0, 0, recipe['result_var']]):
        raise ValueError('party guard: the give is not the pinned Eevee GiveMon')
    # the original count is the first write of the variable the guard borrows: nothing between reads it or branches
    cursor = insert
    while cursor != count_site:
        ins = old.istruzioni.get(cursor)
        if (ins is None or commands.nome(ins.op) not in GUARD_LEAD_INS or ins.rami or var in ins.args):
            raise ValueError('party guard: the code between the guard and the original party count is not plain text')
        cursor = ins.fine
    if [i for i in old.istruzioni.values()
            if commands.nome(i.op) == 'CompareVarToValue' and i.args[1:2] == [recipe['limit']]]:
        raise ValueError('party guard: a party-limit compare already exists in the member')
    effects = _effect_sites(old, commands, recipe)
    if give_site not in effects:
        raise ValueError('party guard: the give is not among the effect sites')
    for index, other in enumerate(old.entry):
        if index != recipe['entry'] and effects & forward_reach(old, commands, [other]):
            raise ValueError(f'party guard: entry {index} reaches the gift effects and would bypass the guard')
    if not effects & forward_reach(old, commands, [entry]):
        raise ValueError('party guard: the gift entry does not reach the effects')
    return effects


def transform_party_guard(raw, language, commands, recipe=None):
    """Insert the retail party-full guard at the pinned point of the Eevee entry of member 227.

        GetPartyCount v; CompareVarToValue v, 6; GoToIf EQ -> FULL;
        BufferPlayersName 0                                              (20 bytes, right after FacePlayer)
        FULL: MsgBoxExtern <native party-full message>; WaitButton; CloseMsg; ReleaseAll; End      (14 bytes, appended)

    The message is the cartridge's own "party is full" string, read through MsgBoxExtern from its bank, so no message bank
    changes. Nothing persistent runs on the refusal path: no give, no flag, no hide, no nickname offer; the event stays
    repeatable. Below the limit the extra BufferPlayersName 0 duplicates the immediate original command. The +20
    insertion preserves the halfword alignment required by native movement readers (BUG-131-01).
    Returns the new member bytes; raises ValueError on any foreign input.
    """
    raw = bytes(raw)
    recipe = recipe or load_guard_recipe()
    if language not in recipe['preimage_sha256']:
        raise ValueError('unsupported party guard language')
    if sha256(raw) != recipe['preimage_sha256'][language]:
        raise ValueError('party guard: member preimage does not match; foreign or already patched input')
    old = decode(raw, commands, recipe['member'])
    _check_guard_site(old, raw, commands, recipe)
    guard, operand, block = _guard_parts(commands, recipe)
    block_edit = Edit(len(raw), len(raw), block)
    guard_edit = Edit(recipe['insert_at'], recipe['insert_at'], guard, fixups=[(operand, ('edit', block_edit, 0))])
    result, _, _ = relocate(raw, commands, [guard_edit, block_edit], recipe['member'])
    verify_party_guard(raw, result, commands, recipe)
    return result


def verify_party_guard(before, after, commands, recipe=None):
    """Independent read-back of a guarded member against its V4 image: structure, byte accounting and control flow."""
    before, after = bytes(before), bytes(after)
    recipe = recipe or load_guard_recipe()
    member = recipe['member']
    if sha256(before) not in recipe['preimage_sha256'].values():
        raise ValueError('verify_party_guard: the before image is not the pinned preimage')
    old, new = decode(before, commands, member), decode(after, commands, member)
    if new.errori or overlapping_instructions(new):
        raise ValueError('guarded member has decoder errors or overlapping instructions')
    # Read-back is independent of _guard_parts: four decoded guard commands (20)
    # and five refusal commands (14), not lengths/bytes returned by the writer.
    insert, added, block_bytes = recipe['insert_at'], 20, 14
    if len(after) != len(before) + added + block_bytes:
        raise ValueError('guarded member length is not original + guard + refusal block')
    block_at = len(before) + added

    def shift(offset):
        return offset + added if offset >= insert else offset

    if new.entry != [shift(e) for e in old.entry]:
        raise ValueError('entry table does not map through the single coordinate transformation')
    buffer = old.istruzioni.get(insert)
    if buffer is None or buffer.nome != 'BufferPlayersName' or buffer.args != [0]:
        raise ValueError('party guard: success must repeat the immediate original player-name buffer 0')
    # The fourth command runs only on success and repeats the original buffer.
    names = [('GetPartyCount', [recipe['party_var']]), ('CompareVarToValue', [recipe['party_var'], recipe['limit']]),
             ('GoToIf', [COND_EQ, block_at]), ('BufferPlayersName', [0])]
    cursor, goto = insert, None
    for name, args in names:
        ins = new.istruzioni.get(cursor)
        shown = [ins.args[0], block_at] if ins is not None and name == 'GoToIf' else (ins.args if ins else None)
        if ins is None or ins.nome != name or shown != args:
            raise ValueError(f'guard command {name} differs from the reference')
        if name == 'GoToIf':
            goto = ins
        cursor = ins.fine
    if cursor != insert + added or after[insert + 17:insert + 20] != before[insert:buffer.fine]:
        raise ValueError('guard bytes differ from the reference')
    if goto.rami != [(1, block_at, 'script')]:
        raise ValueError('the guard branch does not target the refusal block')
    # the refusal block: five commands, closed, ending the member, reached only by the guard branch
    expected = [('MsgBoxExtern', [recipe['message']['bank'], recipe['message']['index']]), ('WaitButton', []),
                ('CloseMsg', []), ('ReleaseAll', []), ('End', [])]
    cursor, block_offsets = block_at, []
    for name, args in expected:
        ins = new.istruzioni.get(cursor)
        if ins is None or ins.nome != name or ins.args != args or ins.rami:
            raise ValueError(f'refusal block command {name} differs from the reference')
        block_offsets.append(cursor)
        cursor = ins.fine
    if cursor != len(after) or cursor - block_at != block_bytes:
        raise ValueError('the refusal block is not the last bytes of the member')
    if [e for e in incoming_edges(new) + entry_edges(new) if e[1] in block_offsets] != \
            [(goto.off, block_at, 'script')]:
        raise ValueError('the refusal block is reachable by something other than the guard branch')
    if forward_reach(new, commands, [block_at]) != set(block_offsets):
        raise ValueError('the refusal block leaves its five commands')
    # every original instruction survives with its operands and remapped branches; nothing else is new
    sd = decoder()
    for ins in old.istruzioni.values():
        other = new.istruzioni.get(shift(ins.off))
        if other is None or (other.op, other.tipi) != (ins.op, ins.tipi):
            raise ValueError(f'instruction at {ins.off:#x} did not survive')
        if other.rami != [(i, shift(d), k) for i, d, k in ins.rami]:
            raise ValueError(f'relative targets of {ins.off:#x} were not remapped')
        if any(a != b for a, b, k in zip(ins.args, other.args, ins.tipi) if k not in sd.RELATIVE):
            raise ValueError(f'non-relative operands of {ins.off:#x} changed')
    if set(new.istruzioni) != {shift(o) for o in old.istruzioni} | {insert, insert + 4, insert + 10, insert + 17} | set(block_offsets):
        raise ValueError('the guarded member holds instructions that are neither original nor the guard')
    # byte accounting outside the guard and the block: only the entry words and relative operands may differ
    mask_before, mask_after = bytearray(before), bytearray(after)
    for index in range(len(old.entry)):
        mask_before[4 * index:4 * index + 4] = bytes(4)
        mask_after[4 * index:4 * index + 4] = bytes(4)
    for ins in old.istruzioni.values():
        cursor = ins.off + 2
        for value, kind in zip(ins.args, ins.tipi):
            size = kind if isinstance(kind, int) else sd.ARG_SIZES[kind]
            if kind in sd.RELATIVE:
                mask_before[cursor:cursor + size] = bytes(size)
                mask_after[shift(cursor):shift(cursor) + size] = bytes(size)
            cursor += size
    if mask_before[:insert] != mask_after[:insert] or mask_before[insert:] != mask_after[insert + added:block_at]:
        raise ValueError('bytes outside the guard and the refusal block changed')
    if new.dati_movimento != {shift(s) for s in old.dati_movimento}:
        raise ValueError('movement targets were not remapped')
    if any(s % 2 for s in old.dati_movimento | new.dati_movimento):
        raise ValueError('native movement targets must preserve halfword alignment')
    for start in old.dati_movimento:
        end = movement_end(before, start)
        if after[shift(start):shift(start) + end - start] != before[start:end]:
            raise ValueError('movement bytes changed')
    # control flow: with the guard's success edge cut, no entry reaches a persistent effect of the gift
    effects = _effect_sites(new, commands, {**recipe, 'give_site': shift(recipe['give_site'])})
    if {shift(o) for o in _effect_sites(old, commands, recipe)} != effects:
        raise ValueError('the effect sites of the guarded member differ from the original ones')
    open_reach = forward_reach(new, commands, new.entry, cut=[(goto.off, goto.fine)])
    if effects & open_reach:
        raise ValueError('an unguarded path leads to the gift effects: it does not pass the guard success edge')
    if not effects <= forward_reach(new, commands, new.entry):
        raise ValueError('the guard cut off a gift effect on the success path')
    return {'member': member, 'preimage_sha256': sha256(before), 'output_sha256': sha256(after),
            'input_bytes': len(before), 'output_bytes': len(after), 'inserted_bytes': added,
            'block_bytes': block_bytes, 'guard_offset': insert, 'block_offset': block_at,
            'instructions_before': len(old.istruzioni), 'instructions_after': len(new.istruzioni),
            'guarded_effects': sorted(effects)}
