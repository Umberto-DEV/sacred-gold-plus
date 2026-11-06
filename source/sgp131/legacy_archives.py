"""The legacy script repairs as member deltas, consumed before the UI writes archives.

Derivation returns ArchiveDelta directly: no ROM writer, append or disk output.
The caller registers PRODUCERS/CHECKERS with the single shared archive owner.
"""
import hashlib
import os
from pathlib import Path
import struct

import ndspy.narc
import ndspy.rom

from sgp131 import archives, gifts_audit, gifts_scripts, legacy_scripts as S

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = 'legacy-scripts'
SCRIPT_ARCHIVE = S.ARCHIVE
EVENTS = 'legacy-events'
EVENT_ARCHIVE = 'a/0/3/2'
POISON_FOLLOWER = 'poison-follower-script'
POISON_MEMBER = 3
POISON_ENTRY = 3
POISON_ENTRY_WORD = 12
POISON_OLD_TARGET = 0x584
POISON_NEW_TARGET = 0x586
POISON_AFTER = 'dfa20a576037c76ebb542c15659db3a6ecd509cf2b881f263c3a341603b151af'
POISON_EXECUTABLE_SHA256 = '80c23cd164585f4e667dbb518ad221a230e7c97876c2933ab59b6994387d1191'
EVENT_ARCHIVE_SHA256 = '5c1bcd8688639c400488f16e60f221feeb93f8861479a05fcbc61f212f49bfdd'
# member: (background row, script, x, z, exact V4 member, exact repaired member)
EVENT_CASES = {
    71: (7, 19, 433, 454,
         '34d3bcb4ce86604e0394d7ca080f110d5d99f97b894bd59dbb980d106a23b899',
         '26a846a7c65b3bf54f0a679aac3a5f28146952bc2022a83eb0ef23a79114632b'),
    440: (5, 14, 50, 24,
          '57cd8e053cc2c14f35ad0991aa13e74a6bf4ee6de3e1974c3c9008c3c5533b4d',
          'f42f955f317805addf6738eb7d9735bf0d75e8e3f31566a1fdebac0d919de2cc'),
}
STANDARD_PREIMAGE = 'fdde73cfa414a6e773f15b1ba04c9e1615669eda1ea3a73250c17b869f70e98a'
MESSAGE_PREIMAGES = {'EN': '7e646990ae5c944d3b1f6b3adc99ff81a9a64bae18945b7fc05b73986c985d0f',
                     'IT': '70d7e8a3f43fcf04f277726f698df4d853e4577f4e682d59f1addd61a3005398'}


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _commands():
    pret = Path(os.environ.get('SGP_PRET_SOURCE') or ROOT / 'local' / 'tools' / 'pokeheartgold')
    path = pret / 'tools' / 'py_scripts' / 'scrcmd.json'
    _need(path.is_file(), 'legacy pinned script command metadata is required')
    commands = gifts_audit.load_commands(path)
    _need(commands.metadata_sha256 == S.METADATA_SHA256, 'legacy command table differs from pinned reference')
    return commands


def script_members():
    _need(not set(S.MEMBERS) & set(archives.GUIDE_SCRIPT_MEMBERS), 'legacy may not change Guide-audited members')
    return sorted(S.MEMBERS)


def _space_keys(raw, commands):
    """Match the installed Bag wrapper's offset/FNV32-window fingerprint, not an API name alone."""
    parsed, result = gifts_scripts.decode(raw, commands, 757), []
    for ins in parsed.istruzioni.values():
        if ins.nome != 'HasSpaceForItem':
            continue
        digest = 0x811C9DC5
        for byte in raw[max(0, ins.fine - 32):ins.fine]:
            digest = ((digest ^ byte) * 0x01000193) & 0xFFFFFFFF
        result.append((ins.off << 16) | (digest & 0xFFFF))
    _need(len(result) == 2, 'legacy Enigma repair must have exactly two Bag checks')
    return sorted(result)


def derive_legacy_scripts(base, language, charmap=None):
    """In-memory V4 -> six guarded member replacements; this never appends an archive."""
    _need(type(base) is bytes and language in ('EN', 'IT'), 'legacy producer arguments')
    commands, members = _commands(), script_members()
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(SCRIPT_ARCHIVE)
    original = bytes(rom.files[fid])
    scripts = archives.members(original)
    _need(hashlib.sha256(scripts[3]).hexdigest() == STANDARD_PREIMAGE,
          'legacy standard2009/2033 member differs from pinned V4')
    bank = bytes(ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[40])
    _need(hashlib.sha256(bank).hexdigest() == MESSAGE_PREIMAGES[language],
          'legacy native Bag-full message bank differs from pinned V4')
    replacements = {m: S.patch_member(scripts[m], language, m, commands) for m in members}
    # New HasSpace commands must take the wrapper's native path. A matching
    # permissive key could otherwise acknowledge saturation without delivery.
    table = set(struct.unpack('<120I', gifts_audit.Arm9View(base).read(0x023DB300, 120 * 4)))
    keys = _space_keys(replacements[757], commands)
    _need(not set(keys) & table, 'legacy Enigma space guard collides with a permissive Bag key')
    return archives.ArchiveDelta.make(SCRIPT_ARCHIVE, fid, SCRIPTS, original, replacements,
                                     {'metadata_sha256': S.METADATA_SHA256,
                                      'standard_member_sha256': STANDARD_PREIMAGE,
                                      'message_bank_sha256': MESSAGE_PREIMAGES[language]})


def _patch_poison_follower(raw, commands):
    """Enter std_survive_poisoning at LockAll, leaving its old ScrCmd_609 bytes unreachable."""
    _need(type(raw) is bytes and hashlib.sha256(raw).hexdigest() == STANDARD_PREIMAGE,
          'poison follower standard-script member differs from pinned V4')
    parsed = gifts_scripts.decode(raw, commands, POISON_MEMBER)
    _need(len(parsed.entry) > POISON_ENTRY and parsed.entry[POISON_ENTRY] == POISON_OLD_TARGET,
          'poison survival entry differs from pinned V4')
    _need(struct.unpack_from('<i', raw, POISON_ENTRY_WORD)[0]
          == POISON_OLD_TARGET - (POISON_ENTRY_WORD + 4),
          'poison survival entry word differs from pinned V4')
    _need(struct.unpack_from('<HH', raw, POISON_OLD_TARGET) == (609, 96),
          'poison survival no longer starts with ScrCmd_609 then LockAll')

    after = bytearray(raw)
    struct.pack_into('<i', after, POISON_ENTRY_WORD,
                     POISON_NEW_TARGET - (POISON_ENTRY_WORD + 4))
    after = bytes(after)
    _need(hashlib.sha256(after).hexdigest() == POISON_AFTER,
          'poison follower repaired member digest')
    return after


def _poison_executable_sha256(base):
    """Bind the script repair to the diagnosed native reset/wait/cleanup implementation."""
    view = gifts_audit.Arm9View(base)
    chunks = [view.read(address, size) for address, size in (
        (0x020FB684, 4),   # command-table row 609 -> ScrCmd_609
        (0x020FAE80, 4),   # command-table row 96 -> LockAll
        (0x02046E5C, 36),  # ScrCmd_609
        (0x02041D40, 56),  # LockAll through the follower wait decision
        (0x020659CC, 128),  # sub_020659CC forced follower reset
        (0x020629CC, 240),  # jump step, including native vector cleanup
    )]
    from sgp12.blz import ndspy_load_overlays_sicuri
    rom = ndspy.rom.NintendoDSRom(base)
    overlay = ndspy_load_overlays_sicuri(rom, [1])[1]
    start, end = 0x021F7704 - overlay.ramAddress, 0x021F771C - overlay.ramAddress
    _need(0 <= start < end <= len(overlay.data), 'poison follower overlay cleanup window')
    chunks.append(bytes(overlay.data[start:end]))
    digest = hashlib.sha256(b''.join(chunks)).hexdigest()
    _need(digest == POISON_EXECUTABLE_SHA256,
          'poison follower executable contract differs from diagnosed V4')
    return digest


def derive_poison_follower(base, language, charmap=None):
    """One entry-table word; archive geometry and every script instruction stay byte-equal."""
    _need(type(base) is bytes and language in ('EN', 'IT'), 'poison follower producer arguments')
    commands = _commands()
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(SCRIPT_ARCHIVE)
    original = bytes(rom.files[fid])
    scripts = archives.members(original)
    replacement = _patch_poison_follower(scripts[POISON_MEMBER], commands)
    executable = _poison_executable_sha256(base)
    return archives.ArchiveDelta.make(
        SCRIPT_ARCHIVE, fid, POISON_FOLLOWER, original,
        {POISON_MEMBER: replacement},
        {'metadata_sha256': S.METADATA_SHA256,
         'standard_member_sha256': STANDARD_PREIMAGE,
         'executable_contract_sha256': executable})


def _background(raw, row):
    """Read one bounded 20-byte background record from a complete event member."""
    _need(type(raw) is bytes and len(raw) >= 4, 'legacy event member bytes')
    count = struct.unpack_from('<I', raw)[0]
    _need(count <= 1024 and type(row) is int and 0 <= row < count
          and 4 + count * 20 <= len(raw), 'legacy background row geometry')
    return struct.unpack_from('<HHiiiH2x', raw, 4 + row * 20)


def _patch_event_member(raw, index):
    _need(index in EVENT_CASES, 'legacy event member identity')
    row, script, x, z, before_sha, after_sha = EVENT_CASES[index]
    _need(hashlib.sha256(raw).hexdigest() == before_sha, 'legacy event member differs from pinned V4')
    _need(_background(raw, row) == (script, 2, x, z, 0, 0),
          'legacy interaction is not the pinned hidden-item-shaped record')
    at = 4 + row * 20 + 2
    after = raw[:at] + struct.pack('<H', 1) + raw[at + 2:]
    _need(hashlib.sha256(after).hexdigest() == after_sha, 'legacy event repair digest')
    return after


def derive_legacy_events(base, language, charmap=None):
    """Reclassify two Plus interactions; scripts, coordinates and true hidden items stay byte-equal."""
    _need(type(base) is bytes and language in ('EN', 'IT'), 'legacy event producer arguments')
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(EVENT_ARCHIVE)
    original = bytes(rom.files[fid])
    _need(hashlib.sha256(original).hexdigest() == EVENT_ARCHIVE_SHA256,
          'legacy event archive differs from pinned V4')
    members = archives.members(original)
    replacements = {index: _patch_event_member(members[index], index) for index in sorted(EVENT_CASES)}
    return archives.ArchiveDelta.make(
        EVENT_ARCHIVE, fid, EVENTS, original, replacements,
        {'archive_sha256': EVENT_ARCHIVE_SHA256})


@archives._guarded
def check_scripts(index, before, after, language):
    """Re-derive exact bytes and independently re-read all edges/complementary bytes."""
    _need(type(index) is int and index in script_members() and type(before) is bytes
          and type(after) is bytes and language in ('EN', 'IT'), 'legacy checker arguments')
    commands = _commands()
    _need(S.patch_member(before, language, index, commands) == after,
          'legacy member differs from pinned repair')
    S.verify_member(before, after, language, index, commands)


@archives._guarded
def check_events(index, before, after, language):
    """Independently require the one halfword repair and its exact semantic endpoints."""
    _need(type(index) is int and index in EVENT_CASES and type(before) is bytes
          and type(after) is bytes and language in ('EN', 'IT'), 'legacy event checker arguments')
    row, script, x, z, before_sha, after_sha = EVENT_CASES[index]
    _need(hashlib.sha256(before).hexdigest() == before_sha
          and hashlib.sha256(after).hexdigest() == after_sha, 'legacy event member digest')
    _need(_background(before, row) == (script, 2, x, z, 0, 0)
          and _background(after, row) == (script, 1, x, z, 0, 0), 'legacy event semantic endpoints')
    at = 4 + row * 20 + 2
    _need(after[:at] + after[at + 2:] == before[:at] + before[at + 2:],
          'legacy event repair changed bytes outside the type halfword')


@archives._guarded
def check_poison_follower(index, before, after, language):
    """Independently require the one entry-word retarget and its decoded endpoints."""
    _need(index == POISON_MEMBER and type(before) is bytes and type(after) is bytes
          and language in ('EN', 'IT'), 'poison follower checker arguments')
    commands = _commands()
    _need(_patch_poison_follower(before, commands) == after,
          'poison follower member differs from pinned repair')
    _need(len(after) == len(before)
          and after[:POISON_ENTRY_WORD] == before[:POISON_ENTRY_WORD]
          and after[POISON_ENTRY_WORD + 4:] == before[POISON_ENTRY_WORD + 4:],
          'poison follower repair changed bytes outside the entry word')
    old = gifts_scripts.decode(before, commands, POISON_MEMBER)
    new = gifts_scripts.decode(after, commands, POISON_MEMBER)
    _need(old.entry[POISON_ENTRY] == POISON_OLD_TARGET
          and new.entry[POISON_ENTRY] == POISON_NEW_TARGET
          and old.entry[:POISON_ENTRY] + old.entry[POISON_ENTRY + 1:]
          == new.entry[:POISON_ENTRY] + new.entry[POISON_ENTRY + 1:],
          'poison follower entry-table semantics')
    _need(struct.unpack_from('<HH', after, POISON_OLD_TARGET) == (609, 96),
          'poison follower instruction bytes changed')


PRODUCERS = {SCRIPTS: derive_legacy_scripts, EVENTS: derive_legacy_events,
             POISON_FOLLOWER: derive_poison_follower}
CHECKERS = {SCRIPTS: check_scripts, EVENTS: check_events,
            POISON_FOLLOWER: check_poison_follower}
