"""HG-B04: repair the inherited Pursuit KO field-condition corruption.

The producer declares one same-size battle-script member replacement.  The
shared archive writer applies it once; this module never writes a ROM or save.
"""
import hashlib
import struct

import ndspy.rom

from . import archives

NAME = 'pursuit-script'
ARCHIVE = 'a/0/0/1'
FILE_ID = 130
MEMBER = 153
MEMBERS = 297
OFFSET = 0x394
ARCHIVE_SHA256 = '4bdd8f93da7831add2db84671be9cc4c5d3ab2f981c391f3f84ad4b451cc08aa'
AFTER_ARCHIVE_SHA256 = '3a97b07341f55ad115d13ae118d4b40b53183b6f47c6bb9449b75cda6a09bee9'
BEFORE_SHA256 = '3fd14b1cdb5402a844a364ffb232095f32ebfeda8f6d2c8069cfc0f4551db73f'
AFTER_SHA256 = '65fd4a9c4cbbd188ade46193f1337708e30196f8c74be329e6441b6bcc4c5f0f'
BEFORE = struct.pack('<4I', 57, 18, 7, 43)
AFTER = struct.pack('<4I', 57, 7, 18, 43)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def patch_member(before):
    """Return the canonical two-byte repair, refusing every foreign preimage."""
    _need(type(before) is bytes and len(before) == 960, 'Pursuit member size/type')
    _need(_sha(before) == BEFORE_SHA256, 'Pursuit member differs from pinned V4')
    _need(before[OFFSET:OFFSET + len(BEFORE)] == BEFORE,
          'Pursuit restore command differs from pinned V4')
    after = before[:OFFSET] + AFTER + before[OFFSET + len(BEFORE):]
    _need(_sha(after) == AFTER_SHA256, 'Pursuit repaired member digest')
    return after


def derive(base, language, charmap=None):
    """Declare member 153 of the exact V4 battle-script archive."""
    _need(type(base) is bytes and language in ('EN', 'IT'), 'Pursuit producer arguments')
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(ARCHIVE)
    _need(fid == FILE_ID, 'Pursuit archive file ID differs from pinned V4')
    raw = bytes(rom.files[fid])
    _need(_sha(raw) == ARCHIVE_SHA256, 'Pursuit archive differs from pinned V4')
    members = archives.members(raw)
    _need(len(members) == MEMBERS, 'Pursuit archive member count')
    replacement = patch_member(members[MEMBER])
    return archives.ArchiveDelta.make(
        ARCHIVE, fid, NAME, raw, {MEMBER: replacement},
        {'archive_sha256': ARCHIVE_SHA256, 'member_before_sha256': BEFORE_SHA256,
         'member_after_sha256': AFTER_SHA256})


@archives._guarded
def check(index, before, after, language):
    """Prove the exact endpoint and the complement outside the command."""
    _need(type(index) is int and index == MEMBER and language in ('EN', 'IT'),
          'Pursuit checker identity')
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after) == 960, 'Pursuit checker member size/type')
    _need(_sha(before) == BEFORE_SHA256 and _sha(after) == AFTER_SHA256,
          'Pursuit checker member digest')
    _need(before[OFFSET:OFFSET + len(BEFORE)] == BEFORE
          and after[OFFSET:OFFSET + len(AFTER)] == AFTER,
          'Pursuit checker command endpoints')
    _need(before[:OFFSET] == after[:OFFSET]
          and before[OFFSET + len(BEFORE):] == after[OFFSET + len(AFTER):],
          'Pursuit checker bytes outside restore command')
    _need([i for i, pair in enumerate(zip(before, after)) if pair[0] != pair[1]]
          == [OFFSET + 4, OFFSET + 8], 'Pursuit checker changed-byte set')


PRODUCERS = {NAME: derive}
CHECKERS = {NAME: check}
