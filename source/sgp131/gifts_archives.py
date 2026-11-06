"""The gift-script fixes as a PRODUCER of archive member deltas (sgp131.archives), not as an appender.

After the UI stage nothing may append an archive (the UI seeds bind FAT 156 and the ROM length). The gift module therefore
expresses its effect as one `ArchiveDelta` producer, run on the pristine V4 with its own writer and re-read by its own
checker:
  gifts-scripts   a/0/1/2   the six repaired ribbon tails + the party-full guard of the Eevee gift (member 227)
Nothing else: no message bank (the guard reads the cartridge's own party-full string through MsgBoxExtern), no ARM9 byte, no
reserve memory. A member the Guide audits (a/0/1/2: 131, 132, 152, 196, 890) is REFUSED by the producer itself, before
`archives.check_against` sees it. The checker re-derives every member from the V4 member with the pure functions of
`gifts_scripts` and requires byte equality, so a producer cannot slip foreign bytes in.
Registration is done by `archives.register_owner_producers` (lazy, either import order).
"""
import hashlib
import os
from pathlib import Path

import ndspy.narc
import ndspy.rom

from sgp131 import archives, gifts_audit, gifts_scripts as S
from sgp13.resources import append_file

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = 'gifts-scripts'
SCRIPT_ARCHIVE = 'a/0/1/2'
MESSAGE_ARCHIVE = 'a/0/2/7'


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _pret():
    return Path(os.environ.get('SGP_PRET_SOURCE') or ROOT / 'local' / 'tools' / 'pokeheartgold')


def _commands():
    path = _pret() / 'tools' / 'py_scripts' / 'scrcmd.json'
    _need(path.is_file(), 'the pret script command table is required')
    commands = gifts_audit.load_commands(path)
    _need(commands.metadata_sha256 == gifts_audit.load_claims()['metadata_sha256'], 'the command table differs from the pinned one')
    return commands


def script_members():
    """The a/0/1/2 members the producer replaces: the six ribbon tails and the Eevee gift."""
    members = set(S.RIBBON_MEMBERS) | {S.load_guard_recipe()['member']}
    _need(not members & set(archives.GUIDE_SCRIPT_MEMBERS), 'the Guide audits these script members: the gifts may not touch them')
    return sorted(members)


def _scripts_after(before_by_member, commands, language):
    """{member: new bytes} computed from the V4 members with the pure functions of the gift module."""
    recipe, guard = S.load_recipe(), S.load_guard_recipe()
    out = {member: S.patch_member(before_by_member[member], language, member, commands, recipe)
           for member in S.RIBBON_MEMBERS}
    member = guard['member']
    _need(member not in out, 'a member is both a ribbon tail and the Eevee gift')
    out[member] = S.transform_party_guard(before_by_member[member], language, commands, guard)
    return out


def _check_native_message(rom, language):
    """The guard reads a native retail string from its bank: that bank must be the pinned V4 one."""
    message = S.load_guard_recipe()['message']
    bank = bytes(ndspy.narc.NARC(rom.getFileByName(MESSAGE_ARCHIVE)).files[message['bank']])
    _need(hashlib.sha256(bank).hexdigest() == message['bank_sha256'][language],
          'the native party-full message bank differs from the pinned V4 bank')


# ------------------------------------------------------------------ gifts-scripts

def apply_scripts(data, language):
    """Owner stage on a V4 image: returns (image, receipt). The image is only a vehicle for `archives.derive`."""
    commands = _commands()
    members = script_members()
    rom = ndspy.rom.NintendoDSRom(bytes(data))
    _check_native_message(rom, language)
    fid = rom.filenames.idOf(SCRIPT_ARCHIVE)
    archive = ndspy.narc.NARC(rom.files[fid])
    before = {m: bytes(archive.files[m]) for m in members}
    after = _scripts_after(before, commands, language)
    for member, raw in after.items():
        archive.files[member] = raw
    image = append_file(bytes(data), fid, archive.save())
    return image, {'members': members,
                   'before_sha256': {str(m): hashlib.sha256(before[m]).hexdigest() for m in members},
                   'after_sha256': {str(m): hashlib.sha256(after[m]).hexdigest() for m in members}}


def verify_scripts(before, after, receipt):
    rom_a, rom_b = ndspy.rom.NintendoDSRom(bytes(before)), ndspy.rom.NintendoDSRom(bytes(after))
    fid = rom_a.filenames.idOf(SCRIPT_ARCHIVE)
    old, new = archives.members(rom_a.files[fid]), archives.members(rom_b.files[fid])
    changed = [i for i, (x, y) in enumerate(zip(old, new)) if x != y]
    _need(changed == receipt['members'], 'the script stage changed members other than the declared ones')


def derive_gifts_scripts(base, language, charmap=None):
    return archives.derive(base, language, SCRIPTS, SCRIPT_ARCHIVE, apply_scripts, verify_scripts)


@archives._guarded
def check_scripts(index, before, after, language):
    """Member level restatement: the member is a ribbon tail or the Eevee gift, and `after` is exactly what the pure
    functions give for the V4 member, which also passes the independent read-back of its fix."""
    commands = _commands()
    _need(type(index) is int and type(before) is bytes and type(after) is bytes and language in ('EN', 'IT'), 'gift member arguments')
    _need(index not in archives.GUIDE_SCRIPT_MEMBERS, 'the Guide audits this script member')
    guard = S.load_guard_recipe()
    if index in S.RIBBON_MEMBERS:
        recipe = S.load_recipe()
        _need(S.patch_member(before, language, index, commands, recipe) == after, 'ribbon member differs from the pinned repair')
        S.verify_member(before, after, commands, recipe)
        return
    _need(index == guard['member'], 'member %d is neither a ribbon tail nor the Eevee gift' % index)
    _need(S.transform_party_guard(before, language, commands, guard) == after, 'Eevee member differs from its pinned guard')
    S.verify_party_guard(before, after, commands, guard)


PRODUCERS = {SCRIPTS: derive_gifts_scripts}
CHECKERS = {SCRIPTS: check_scripts}
