"""HG-F08: clear the GS-list accumulator before returning to its confirmation menu.

Member 4 uses map-temporary x4005 while it prints the nine eligible legendary
species.  Member 819 independently uses x4005 as Will's guard-movement latch.
The one viewer exit is repaired; the guard, every other ruleset and every save
identifier remain untouched.
"""
import hashlib

import ndspy.rom

from . import archives, gifts_audit, gifts_scripts as G


MEMBER = 4
GUARD_MEMBER = 819
TEMP_4005 = 0x4005
TEARDOWN_GOTO = 0x8E5
CLEAR_BLOCK = 0x8EB
CLEAR_GOTO = 0x8F1
PREIMAGE_SHA256 = '6ddaf0ae4e954d4ec90cd783247ceb46a914a8f56d3184b86c75ef9f5cc208fb'
GUARD_SHA256 = '5c89e5608b01f59a6ffcaff54286301ae0e27f4a166357333a8f239ee35b39ea'
METADATA_SHA256 = 'fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a'
NAME = 'gs-cup-guard'
ARCHIVE = 'a/0/1/2'
FILE_ID = 141
MEMBERS = 965
ARCHIVE_SHA256 = '100e07c998935ca05f1ae291fdcc6b68a769448b07fa3f81f44e1c1a77242d4b'
AFTER_SHA256 = 'e556ac6c627066bd6048657fd419401f931ed8ccff321b21ab5f82a47dc7a773'
AFTER_ARCHIVE_SHA256 = '58ee1822f922d49293346bca8b192892c098d2351bda423ff1cd56e107dab94e'


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _preimage(raw, language, commands):
    _need(type(raw) is bytes and language in ('EN', 'IT'), 'GS Cup viewer arguments')
    _need(len(commands) == 853 and getattr(commands, 'metadata_sha256', None) == METADATA_SHA256,
          'GS Cup command metadata differs from the pinned reference')
    _need(_sha(raw) == PREIMAGE_SHA256, 'GS Cup viewer differs from the pinned V4 preimage')
    parsed = G.decode(raw, commands, MEMBER)
    _need(not G.overlapping_instructions(parsed), 'GS Cup viewer preimage overlaps instructions')
    _need(parsed.istruzioni[0x780].nome == 'SetVar'
          and parsed.istruzioni[0x780].args == [TEMP_4005, 0],
          'GS Cup viewer accumulator initialization changed')
    _need([parsed.istruzioni[site].args for site in
           (0x7A4, 0x7C8, 0x7EC, 0x810, 0x834, 0x858, 0x87C, 0x8A0, 0x8C4)]
          == [[TEMP_4005, 1]] * 9, 'GS Cup viewer species accumulator writes changed')
    _need(parsed.istruzioni[0x8CA].args == [TEMP_4005, 1]
          and parsed.istruzioni[0x8D0].rami[0][1] == 0x8E0
          and parsed.istruzioni[0x8DA].rami[0][1] == 0x8E3
          and parsed.istruzioni[0x8E0].fine == 0x8E3
          and parsed.istruzioni[0x8E3].nome == 'TouchscreenMenuHide'
          and parsed.istruzioni[0x8E3].fine == TEARDOWN_GOTO
          and parsed.istruzioni[TEARDOWN_GOTO].rami[0][1] == 0x682,
          'GS Cup viewer no longer has one diagnosed teardown')
    _need(not [edge for edge in G.incoming_edges(parsed) + G.entry_edges(parsed)
               if edge[1] == CLEAR_BLOCK]
          and raw[CLEAR_BLOCK:0x8F9] == bytes.fromhex(
              '29000580000016000e0000000200'),
          'GS Cup pinned unreachable cleanup block changed')
    return parsed


def patch_member(raw, language, commands):
    """Route the common viewer teardown through an equal-size cleanup block."""
    before = _preimage(raw, language, commands)
    to_clear = G.Edit(TEARDOWN_GOTO, CLEAR_BLOCK, G.assemble(commands, 'GoTo', 0),
                      ((2, ('old', CLEAR_BLOCK)),))
    clear = G.Edit(CLEAR_BLOCK, CLEAR_GOTO, G.assemble(commands, 'SetVar', TEMP_4005, 0))
    to_menu = G.Edit(CLEAR_GOTO, 0x8F7, G.assemble(commands, 'GoTo', 0),
                     ((2, ('old', 0x682)),))
    after, _, _ = G.relocate(raw, commands, [to_clear, clear, to_menu], MEMBER)
    verify_member(raw, after, language, commands, before)
    return after


def verify_member(before, after, language, commands, old=None):
    """Independent decoded read-back of the insertion, all edges and complementary bytes."""
    old = old or _preimage(before, language, commands)
    _need(type(after) is bytes and len(after) == len(before),
          'GS Cup repaired member size/type')
    new = G.decode(after, commands, MEMBER)
    _need(not G.overlapping_instructions(new), 'GS Cup repaired member overlaps instructions')
    clear = new.istruzioni.get(CLEAR_BLOCK)
    _need(clear is not None and clear.nome == 'SetVar' and clear.args == [TEMP_4005, 0]
          and clear.fine == CLEAR_GOTO, 'GS Cup teardown clear is absent or changed')
    _need(new.istruzioni[0x8E3].nome == 'TouchscreenMenuHide'
          and new.istruzioni[TEARDOWN_GOTO].rami[0][1] == CLEAR_BLOCK
          and new.istruzioni[CLEAR_GOTO].rami[0][1] == 0x682
          and after[0x8F7:0x8F9] == bytes.fromhex('0200'),
          'GS Cup teardown no longer returns to the confirmation menu')
    _need(new.entry == old.entry, 'GS Cup entry table changed')
    _need(old.dati_movimento == new.dati_movimento
          and all(x % 2 == 0 for x in set(old.dati_movimento) | set(new.dati_movimento)),
          'GS Cup native movement geometry changed')

    decoder = G.decoder()
    mask_before, mask_after = bytearray(before), bytearray(after)
    replaced = ((TEARDOWN_GOTO, CLEAR_BLOCK), (CLEAR_BLOCK, CLEAR_GOTO), (CLEAR_GOTO, 0x8F7))
    survived = 0
    for ins in old.istruzioni.values():
        if any(start <= ins.off < end for start, end in replaced):
            continue
        other = new.istruzioni.get(ins.off)
        _need(other is not None and (other.op, other.tipi) == (ins.op, ins.tipi),
              f'GS Cup instruction did not survive at {ins.off:#x}')
        _need(other.rami == ins.rami,
              f'GS Cup relative target changed at {ins.off:#x}')
        _need(all(first == second for first, second, kind in zip(ins.args, other.args, ins.tipi)
                  if kind not in decoder.RELATIVE),
              f'GS Cup non-relative operand changed at {ins.off:#x}')
        survived += 1
    for start, end in replaced:
        mask_before[start:end] = bytes(end - start)
        mask_after[start:end] = bytes(end - start)
    _need(mask_before == mask_after, 'GS Cup repair changed complementary bytes')
    _need(survived == len(old.istruzioni) - 1, 'GS Cup repair lost decoded instructions')
    _need(_sha(after) == AFTER_SHA256, 'GS Cup repaired member digest')
    return {'member': MEMBER, 'clear_block': CLEAR_BLOCK, 'member_bytes': len(after),
            'before_sha256': _sha(before), 'after_sha256': _sha(after),
            'surviving_instructions': survived}


def _commands():
    """Load only the authenticated command table already used by the script owners."""
    from pathlib import Path
    import os
    root = Path(__file__).resolve().parents[2]
    pret = Path(os.environ.get('SGP_PRET_SOURCE') or root / 'local' / 'tools' / 'pokeheartgold')
    commands = gifts_audit.load_commands(pret / 'tools' / 'py_scripts' / 'scrcmd.json')
    _need(commands.metadata_sha256 == METADATA_SHA256,
          'GS Cup command table differs from the pinned reference')
    return commands


def derive(base, language, charmap=None):
    """Declare the one same-size member replacement; never write a ROM or save."""
    _need(type(base) is bytes and language in ('EN', 'IT'), 'GS Cup producer arguments')
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(ARCHIVE)
    _need(fid == FILE_ID, 'GS Cup archive file ID differs from the pinned V4')
    raw = bytes(rom.files[fid])
    _need(_sha(raw) == ARCHIVE_SHA256, 'GS Cup script archive differs from the pinned V4')
    members = archives.members(raw)
    _need(len(members) == MEMBERS and _sha(members[GUARD_MEMBER]) == GUARD_SHA256,
          'GS Cup member count or guard oracle differs from the pinned V4')
    replacement = patch_member(members[MEMBER], language, _commands())
    return archives.ArchiveDelta.make(
        ARCHIVE, fid, NAME, raw, {MEMBER: replacement},
        {'archive_sha256': ARCHIVE_SHA256, 'metadata_sha256': METADATA_SHA256,
         'viewer_before_sha256': PREIMAGE_SHA256, 'viewer_after_sha256': AFTER_SHA256,
         'guard_member_sha256': GUARD_SHA256})


@archives._guarded
def check(index, before, after, language):
    """Re-derive the exact endpoint and independently read every surviving byte/edge."""
    _need(type(index) is int and index == MEMBER and language in ('EN', 'IT'),
          'GS Cup checker identity')
    _need(type(before) is bytes and type(after) is bytes
          and _sha(before) == PREIMAGE_SHA256 and _sha(after) == AFTER_SHA256,
          'GS Cup checker member identity')
    commands = _commands()
    _need(patch_member(before, language, commands) == after,
          'GS Cup checker differs from the canonical writer')
    verify_member(before, after, language, commands)


PRODUCERS = {NAME: derive}
CHECKERS = {NAME: check}
