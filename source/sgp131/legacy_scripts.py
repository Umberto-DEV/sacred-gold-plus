"""Pinned, pure repairs of inherited script members 93, 141, 237, 757, 874 and 932.

SG-09 changes only the Full Heal quantity (436 -> 1). SG-08 restores the
existing friend hide flag before WhiteOut, leaving the retry variable alone.
SG-15 gives only an eligible, matching, unrewarded Lati priority over the
Regigigas dialogue. SG-15b checks native Bag space before either Enigma gift;
failure uses the existing standard2009 message and leaves the reward pending.
Kurt now keeps a completed Apricorn Ball batch when the Bag cannot accept it,
using the script's existing failure message and clearing the batch only after
the normal successful give path.
Pryce's TM07 remains pending when the Plus Bag accepts the request but discards
the saturated item, and a later talk retries it after capacity is available.
Kate's direct-interaction path now distinguishes the pre-battle state from the
reward and completed states instead of showing the post-battle apology before
the coordinate-triggered fight.

No save layout, flag identifier or migration changes. Native execution and
save compatibility require separate runtime validation. All transformations
use the existing guarded relocation; the read-back below does not invoke the
writer or its edit recipe and checks every surviving byte/relative target.
"""
import hashlib
import struct

from sgp131 import gifts_scripts as G

ARCHIVE = 'a/0/1/2'
MEMBERS = (93, 141, 237, 757, 874, 932)
METADATA_SHA256 = 'fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a'
PREIMAGES = {
    93: '99681fdf303533d7eae6bf06ef672a5b947ee1a2b4a3261a7929bfe363d051e0',
    141: '4d95a52d22458f98d14cf09d30fc50b28a0a72cfe91012e3796a7a3de0a0630a',
    237: '3a038af0fa5797f18ec350982e5850c0d9ba875f34f77026182fd2c6f5bf3040',
    757: 'c223b9665a411c9d99a1e73a5857d87931ec41a24a126ad288f55c3bfd1b4b69',
    874: 'a642101464263fc8271bad7bf35f4f298bcb3c705a98657481b4da3c067e88a9',
    932: 'b4bbc075b7ff7e8f42f73e1e9b080770d2a7083e3c9ae001b579ff227882d9a5',
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _before(raw, language, member, commands):
    _need(type(raw) is bytes and language in ('EN', 'IT') and type(member) is int and member in MEMBERS,
          'legacy member arguments')
    _need(len(commands) == 853 and getattr(commands, 'metadata_sha256', None) == METADATA_SHA256,
          'legacy command metadata differs from the pinned reference')
    _need(hashlib.sha256(raw).hexdigest() == PREIMAGES[member],
          'legacy member preimage differs: foreign or already repaired input')
    return G.decode(raw, commands, member)


def _edit(commands, start, end, rows):
    """Assemble one replacement; explicit ('old', offset) and ('label', name) targets only."""
    data, labels, targets = bytearray(), {}, []
    sd = G.decoder()
    for row in rows:
        if row[0] == 'label':
            labels[row[1]] = len(data)
            continue
        name, args = row[0], list(row[1:])
        encoded = G.assemble(commands, name, *(0 if isinstance(a, tuple) else a for a in args))
        op = struct.unpack_from('<H', encoded)[0]
        kinds, _ = commands.arg_list(op, None)
        cursor = len(data) + 2
        for arg, kind in zip(args, kinds):
            if isinstance(arg, tuple):
                _need(kind in sd.RELATIVE, 'legacy target on a non-relative operand')
                targets.append((cursor, arg))
            cursor += kind if isinstance(kind, int) else sd.ARG_SIZES[kind]
        data.extend(encoded)
    edit = G.Edit(start, end, bytes(data))
    edit.fixups = tuple((at, ('edit', edit, labels[target[1]]) if target[0] == 'label' else target)
                        for at, target in targets)
    return edit


def patch_member(raw, language, member, commands):
    """Return repaired bytes; never accepts an unpinned or already patched member."""
    old = _before(raw, language, member, commands)
    if member == 237:
        # Direct interaction preserves FacePlayer, then dispatches the three
        # valid sister states.  State 1 joins the existing pre-battle path
        # after its straight-approach movement; state 2 retries the reward;
        # states 0 and 3 retain the apology and join the existing shared
        # message cleanup.  The six-byte growth is even, preserving native
        # movement halfword alignment while relocation retargets later code.
        direct = _edit(commands, 0x299, 0x2BF, [
            ('PlaySE', 1500), ('LockAll',), ('FacePlayer',),
            ('CompareVarToValue', 0x4097, 1),
            ('GoToIf', 1, ('old', 0x1E1)),
            ('CompareVarToValue', 0x4097, 2),
            ('GoToIf', 1, ('old', 0x553)),
            ('NPCMsg', 32),
            ('GoToIf', 5, ('old', 0x538)),
        ])
        result, _, _ = G.relocate(raw, commands, [direct], member)
    elif member == 141:
        _need(old.istruzioni[0x868].nome == 'SetVar' and old.istruzioni[0x868].args == [0x8009, 436],
              'legacy pickup quantity instruction differs')
        result = bytearray(raw)
        struct.pack_into('<H', result, 0x86C, 1)
        result = bytes(result)
    elif member == 93:
        edit = _edit(commands, 0x553, 0x555, [('SetFlag', 712), ('WhiteOut',)])
        result, _, _ = G.relocate(raw, commands, [edit], member)
    elif member == 757:
        priority = _edit(commands, 0x37, 0x42, [
            ('CheckFlag', 775), ('GoToIf', 0, ('old', 0x42)),
            ('CheckFlag', 16330), ('GoToIf', 1, ('old', 0x458)),
            ('CheckFlag', 16312), ('GoToIf', 1, ('old', 0x458)),
            ('SetVar', 0x8002, 380),
            ('GetGameVersion', 0x800C), ('CompareVarToValue', 0x800C, 7),
            ('GoToIf', 1, ('label', 'check-species')), ('SetVar', 0x8002, 381),
            ('label', 'check-species'),
            ('GetPartyLeadAlive', 0x8000), ('GetPartyMonSpecies', 0x8000, 0x8001),
            ('CompareVarToVar', 0x8001, 0x8002), ('GoToIf', 1, ('old', 0x49D)),
            ('GoTo', ('old', 0x458)),
        ])
        edits = [priority]
        for site in (0x69C, 0x6DC):
            edits.append(_edit(commands, site, site + 4, [
                ('HasSpaceForItem', 0x8004, 0x8005, 0x800C),
                ('CompareVarToValue', 0x800C, 1), ('GoToIf', 1, ('label', 'give')),
                ('CallStd', 2009), ('CloseMsg',), ('ReleaseAll',), ('End',),
                ('label', 'give'), ('CallStd', 2033),
            ]))
        result, _, _ = G.relocate(raw, commands, edits, member)
    elif member == 874:
        guard = _edit(commands, 0x1C2, 0x1C8, [
            ('CompareVarToValue', 0x800C, 0),
            ('GoToIf', 1, ('old', 0x1F9)),
            # The second, semantically redundant branch keeps every following
            # native movement pointer halfword-aligned after relocation.
            ('GoToIf', 5, ('label', 'has-space')),
            ('label', 'has-space'),
            ('CopyVar', 0x8005, 0x8000),
        ])
        result, _, _ = G.relocate(raw, commands, [guard], member)
    else:
        # If the Glacier Badge is already owned, FLAG_GOT_TM07_FROM_PRYCE
        # decides whether to keep the old dialogue or retry the reward.  The
        # first no-op conditional preserves halfword alignment of native
        # movement pointers after relocation.
        badge_retry = _edit(commands, 0x2F, 0x36, [
            ('GoToIf', 1, ('label', 'check-reward')),
            ('GoTo', ('old', 0x36)),
            ('label', 'check-reward'),
            ('GoToIf', 5, ('label', 'check-flag')),
            ('label', 'check-flag'),
            ('CheckFlag', 210),
            ('GoToIf', 1, ('old', 0x12E)),
            ('GoTo', ('old', 0x14A)),
        ])

        def delivery(site):
            # Standard 2033 consumes and clears x800A before returning, so the
            # caller cannot inspect that transient discard marker.  Query the
            # actual TM quantity first and reuse the existing Bag-full cleanup
            # at the exact Plus cap.  The conditional-to-next-instruction keeps
            # relocation parity even without altering the comparison result.
            return _edit(commands, site, site + 8, [
                ('GetItemQuantity', 334, 0x800C),
                ('GoToIf', 5, ('label', 'check-result')),
                ('label', 'check-result'),
                ('CompareVarToValue', 0x800C, 99),
                ('GoToIf', 1, ('old', 0x1A0)),
                ('CallStd', 2033),
                ('SetFlag', 210),
            ])

        result, _, _ = G.relocate(
            raw, commands, [badge_retry, delivery(0xBC), delivery(0x17A)], member)
    verify_member(raw, result, language, member, commands)
    return result


def _sequence(parsed, start, expected):
    """Read-back matcher: names, literal operands and destinations, no assembling."""
    cursor = start
    for name, operands, target in expected:
        ins = parsed.istruzioni.get(cursor)
        _need(ins is not None and ins.nome == name, f'legacy read-back command at {cursor:#x}')
        kinds = ins.tipi
        literal = [a for a, k in zip(ins.args, kinds) if k not in G.decoder().RELATIVE]
        _need(literal == operands, f'legacy read-back operands at {cursor:#x}')
        _need([d for _, d, _ in ins.rami] == ([] if target is None else [target]),
              f'legacy read-back branch at {cursor:#x}')
        cursor = ins.fine
    return cursor


def _preserved(before, after, old, new, replacements):
    """Independent coordinate/read-back proof, including uncovered bytes and movements.

    Each row is (old start, old end, actual new block length). The verifier
    supplies these from independently checked instruction sequences.
    """
    def shift(offset):
        _need(not any(a < offset < b for a, b, _ in replacements),
              'legacy read-back target enters replaced interior')
        return offset + sum(n - (b - a) for a, b, n in replacements if b <= offset)

    _need(len(after) == len(before) + sum(n - (b - a) for a, b, n in replacements),
          'legacy read-back length')
    _need(new.entry == [shift(x) for x in old.entry], 'legacy read-back entry targets')
    _need(all(p % 2 == 0 for p in old.dati_movimento) and all(p % 2 == 0 for p in new.dati_movimento)
          and {shift(p) for p in old.dati_movimento} == new.dati_movimento,
          'legacy native movement targets must preserve halfword alignment')
    mask_old, mask_new = bytearray(before), bytearray(after)
    for i in range(len(old.entry)):
        mask_old[4 * i:4 * i + 4] = bytes(4)
        mask_new[4 * i:4 * i + 4] = bytes(4)
    survived = 0
    for ins in old.istruzioni.values():
        if any(a <= ins.off < b for a, b, _ in replacements):
            continue
        other = new.istruzioni.get(shift(ins.off))
        _need(other is not None and (other.op, other.tipi) == (ins.op, ins.tipi),
              f'legacy read-back lost instruction at {ins.off:#x}')
        _need(other.rami == [(i, shift(d), k) for i, d, k in ins.rami],
              f'legacy read-back relative target at {ins.off:#x}')
        cursor = ins.off + 2
        for a, b, kind in zip(ins.args, other.args, ins.tipi):
            size = kind if isinstance(kind, int) else G.decoder().ARG_SIZES[kind]
            if kind in G.decoder().RELATIVE:
                mask_old[cursor:cursor + size] = bytes(size)
                at = shift(cursor)
                mask_new[at:at + size] = bytes(size)
            else:
                _need(a == b, f'legacy read-back changed unrelated operand at {ins.off:#x}')
            cursor += size
        survived += 1
    for a, b, n in reversed(replacements):
        at = shift(a)
        del mask_old[a:b]
        del mask_new[at:at + n]
    _need(mask_old == mask_new, 'legacy read-back changed complementary bytes')
    return survived


def verify_member(before, after, language, member, commands):
    """Decode both images; prove inserted semantics, every old edge and complementary byte."""
    old = _before(before, language, member, commands)
    _need(type(after) is bytes, 'legacy after image type')
    new = G.decode(after, commands, member)
    _need(not G.overlapping_instructions(new), 'legacy after image has overlapping instructions')
    if member == 237:
        end = _sequence(new, 0x299, [
            ('PlaySE', [1500], None), ('LockAll', [], None),
            ('FacePlayer', [], None),
            ('CompareVarToValue', [0x4097, 1], None),
            ('GoToIf', [1], 0x1E1),
            ('CompareVarToValue', [0x4097, 2], None),
            ('GoToIf', [1], 0x559),
            ('NPCMsg', [32], None),
            ('GoToIf', [5], 0x53E),
        ])
        _need(end == 0x2C5 and len(after) == len(before) + 6,
              'legacy Kate direct-interaction width')
        _need(new.entry == [offset + (6 if offset >= 0x2BF else 0)
                            for offset in old.entry],
              'legacy Kate entry relocation changed')
        replacements = [(0x299, 0x2BF, 0x2C5 - 0x299)]
    elif member == 141:
        _need(len(after) == len(before), 'legacy pickup member length')
        _need(after[:0x86C] == before[:0x86C] and after[0x86E:] == before[0x86E:]
              and struct.unpack_from('<H', after, 0x86C)[0] == 1,
              'legacy pickup changed bytes other than 436 -> 1')
        _need(new.entry == old.entry and new.istruzioni[0x868].args == [0x8009, 1],
              'legacy pickup API quantity or entry changed')
        replacements = [(0x868, 0x86E, 6)]
    elif member == 93:
        end = _sequence(new, 0x553, [('SetFlag', [712], None), ('WhiteOut', [], None)])
        _need(end == 0x559, 'legacy friend cleanup width')
        replacements = [(0x553, 0x555, 6)]
    elif member == 757:
        # Independent widths: the new priority sequence occupies 91 bytes; each
        # space-check/error/standard-call block occupies 35 bytes.
        delta_priority, delta_gift = 91 - 11, 35 - 4

        def shift(x):
            return x + (delta_priority if x >= 0x42 else 0) + \
                (delta_gift if x >= 0x6A0 else 0) + (delta_gift if x >= 0x6E0 else 0)

        start = 0x37
        # The species-check label is 62 bytes from the priority block start.
        end = _sequence(new, start, [
            ('CheckFlag', [775], None), ('GoToIf', [0], shift(0x42)),
            ('CheckFlag', [16330], None), ('GoToIf', [1], shift(0x458)),
            ('CheckFlag', [16312], None), ('GoToIf', [1], shift(0x458)),
            ('SetVar', [0x8002, 380], None),
            ('GetGameVersion', [0x800C], None), ('CompareVarToValue', [0x800C, 7], None),
            ('GoToIf', [1], start + 62), ('SetVar', [0x8002, 381], None),
            ('GetPartyLeadAlive', [0x8000], None), ('GetPartyMonSpecies', [0x8000, 0x8001], None),
            ('CompareVarToVar', [0x8001, 0x8002], None), ('GoToIf', [1], shift(0x49D)),
            ('GoTo', [], shift(0x458)),
        ])
        _need(end - start == 91, 'legacy Lati priority width')
        replacements = [(0x37, 0x42, 91)]
        for site in (0x69C, 0x6DC):
            at = shift(site)
            end = _sequence(new, at, [
                ('HasSpaceForItem', [0x8004, 0x8005, 0x800C], None),
                ('CompareVarToValue', [0x800C, 1], None), ('GoToIf', [1], at + 31),
                ('CallStd', [2009], None), ('CloseMsg', [], None),
                ('ReleaseAll', [], None), ('End', [], None), ('CallStd', [2033], None),
            ])
            _need(end - at == 35, 'legacy Bag guard width')
            replacements.append((site, site + 4, 35))
    elif member == 874:
        end = _sequence(new, 0x1C2, [
            ('CompareVarToValue', [0x800C, 0], None),
            ('GoToIf', [1], 0x20D),
            ('GoToIf', [5], 0x1D6),
            ('CopyVar', [0x8005, 0x8000], None),
        ])
        _need(end == 0x1DC, 'legacy Kurt Bag guard width')
        _need(new.istruzioni[0x20D].nome == 'NPCMsg'
              and new.istruzioni[0x20D].args == [9], 'legacy Kurt failure target')
        replacements = [(0x1C2, 0x1C8, 26)]
    else:
        replacements = [(0x2F, 0x36, 37), (0xBC, 0xC4, 34), (0x17A, 0x182, 34)]

        def shift(offset):
            return offset + sum(n - (b - a) for a, b, n in replacements if b <= offset)

        end = _sequence(new, 0x2F, [
            ('GoToIf', [1], 0x3C),
            ('GoTo', [], shift(0x36)),
            ('GoToIf', [5], 0x43),
            ('CheckFlag', [210], None),
            ('GoToIf', [1], shift(0x12E)),
            ('GoTo', [], shift(0x14A)),
        ])
        _need(end == 0x54, 'legacy Pryce badge retry width')
        for site in (0xBC, 0x17A):
            at = shift(site)
            end = _sequence(new, at, [
                ('GetItemQuantity', [334, 0x800C], None),
                ('GoToIf', [5], at + 13),
                ('CompareVarToValue', [0x800C, 99], None),
                ('GoToIf', [1], shift(0x1A0)),
                ('CallStd', [2033], None),
                ('SetFlag', [210], None),
            ])
            _need(end - at == 34, 'legacy Pryce delivery guard width')
    survived = _preserved(before, after, old, new, replacements)
    return {'member': member, 'before_sha256': hashlib.sha256(before).hexdigest(),
            'after_sha256': hashlib.sha256(after).hexdigest(), 'bytes_added': len(after) - len(before),
            'surviving_instructions': survived, 'entry_count': len(new.entry),
            'verification': 'independent decoded branches and complementary bytes; no ARM execution'}
