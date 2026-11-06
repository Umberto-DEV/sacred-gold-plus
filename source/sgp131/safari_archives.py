"""SG-01a, SG-01b and SG-02 as one guarded script-member delta.

The repair never appends a second archive after the UI.  It derives member 260
from the exact V4 a/0/1/2 preimage, moves the three stale CloseMsg commands,
appends the 23-byte first-bridge height guard, retargets the final-admin loss
to the shared WhiteOut, and lets ``archives`` merge this
disjoint member with the existing gift and legacy producers before the UI
writes and seeds the cartridge once.
"""
import hashlib
import os
from pathlib import Path

import ndspy.rom

from sgp131 import archives, gifts_audit, safari_defeat_whiteout as W
from sgp131 import safari_lifetime as S


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = 'safari-scripts'


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _commands():
    pret = Path(os.environ.get('SGP_PRET_SOURCE') or
                ROOT / 'local/tools/pokeheartgold')
    path = pret / 'tools/py_scripts/scrcmd.json'
    _need(path.is_file(), 'Safari pinned script command metadata is required')
    commands = gifts_audit.load_commands(path)
    _need(commands.metadata_sha256 == S.COMMANDS_SHA256,
          'Safari command table differs from pinned metadata')
    return commands


def derive_safari_scripts(base, language, charmap=None):
    """Return the one member delta; no cartridge or save is written."""
    _need(type(base) is bytes and language in ('EN', 'IT'),
          'Safari producer arguments')
    commands = _commands()
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(S.SCRIPT_ARCHIVE)
    original = bytes(rom.files[fid])
    members = archives.members(original)
    _need(S.SCRIPT_MEMBER not in archives.GUIDE_SCRIPT_MEMBERS,
          'the Guide audits the Safari script member')
    before = members[S.SCRIPT_MEMBER]
    lifetime = S.repair_member(before, commands)
    after = W.repair_member(lifetime, commands)
    lifetime_receipt = S.verify_repair(before, lifetime, commands)
    defeat_receipt = W.verify_repair(lifetime, after, commands)
    return archives.ArchiveDelta.make(
        S.SCRIPT_ARCHIVE, fid, SCRIPTS, original,
        {S.SCRIPT_MEMBER: after},
        {'before_sha256': lifetime_receipt['before_sha256'],
         'sg01a_sg02_sha256': lifetime_receipt['after_sha256'],
         'after_sha256': defeat_receipt['after_sha256'],
         'metadata_sha256': S.COMMANDS_SHA256})


@archives._guarded
def check_scripts(index, before, after, language):
    """Independent member-level admission used by archives.check_semantics."""
    _need(type(index) is int and index == S.SCRIPT_MEMBER
          and type(before) is bytes and type(after) is bytes
          and language in ('EN', 'IT'), 'Safari checker arguments')
    commands = _commands()
    lifetime = S.repair_member(before, commands)
    lifetime_result = S.verify_repair(before, lifetime, commands)
    defeat_result = W.verify_repair(lifetime, after, commands)
    _need(lifetime_result['member'] == defeat_result['member'] == index
          and hashlib.sha256(lifetime).hexdigest() == S.REPAIRED_SCRIPT_SHA256
          and hashlib.sha256(after).hexdigest() == W.AFTER_SHA256,
          'Safari checker result differs')


PRODUCERS = {SCRIPTS: derive_safari_scripts}
CHECKERS = {SCRIPTS: check_scripts}
