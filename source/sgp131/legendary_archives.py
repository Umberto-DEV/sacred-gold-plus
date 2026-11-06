"""Archive producer/checker for the local HG-T10 member-21 guard."""
import hashlib
import os
from pathlib import Path

import ndspy.rom

from . import archives, gifts_audit, legendary_scenes as S


ROOT = Path(__file__).resolve().parents[2]
PRODUCER = 'legendary-scenes-scripts'


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _commands():
    pret = Path(os.environ.get('SGP_PRET_SOURCE') or ROOT / 'local/tools/pokeheartgold')
    path = pret / 'tools/py_scripts/scrcmd.json'
    _need(path.is_file(), 'legendary-scenes pinned script command metadata is required')
    commands = gifts_audit.load_commands(path)
    _need(commands.metadata_sha256 == S.METADATA_SHA256,
          'legendary-scenes command metadata differs from pinned reference')
    return commands


def derive_scripts(base, language, charmap=None):
    """Derive the one member delta from immutable V4 bytes; never write a ROM."""
    _need(type(base) is bytes and language in ('EN', 'IT'),
          'legendary-scenes producer arguments')
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(S.ARCHIVE)
    original = bytes(rom.files[fid])
    members = archives.members(original)
    _need(hashlib.sha256(members[S.MEMBER]).hexdigest() == S.PREIMAGE_SHA256,
          'legendary-scenes member 21 differs from pinned V4')
    replacement = S.patch_member(members[S.MEMBER], _commands())
    return archives.ArchiveDelta.make(
        S.ARCHIVE, fid, PRODUCER, original, {S.MEMBER: replacement},
        {'metadata_sha256': S.METADATA_SHA256,
         'member_preimage_sha256': S.PREIMAGE_SHA256,
         'member_postimage_sha256': S.POSTIMAGE_SHA256})


@archives._guarded
def check_scripts(index, before, after, language):
    """Re-derive exact bytes and independently read back the guarded member."""
    _need(type(index) is int and index == S.MEMBER and type(before) is bytes
          and type(after) is bytes and language in ('EN', 'IT'),
          'legendary-scenes checker arguments')
    commands = _commands()
    _need(S.patch_member(before, commands) == after,
          'legendary-scenes member differs from pinned repair')
    S.verify_member(before, after, commands)


PRODUCERS = {PRODUCER: derive_scripts}
CHECKERS = {PRODUCER: check_scripts}
