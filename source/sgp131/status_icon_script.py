"""HG-B06: preserve persistent healthbar icons on volatile ability cures.

The retail ability-cure script clears the healthbar icon before deciding
whether it is curing a persistent status or only confusion/infatuation.  This
producer moves the volatile dispatch before that visual command and duplicates
the existing 30-frame wait in those two branches.  It changes one NARC member
in memory and never writes a ROM or save.
"""
import hashlib
import struct

import ndspy.rom

from . import archives


NAME = 'status-icon-script'
ARCHIVE = 'a/0/0/1'
FILE_ID = 130
MEMBER = 221
MEMBERS = 297
ARCHIVE_SHA256 = '4bdd8f93da7831add2db84671be9cc4c5d3ab2f981c391f3f84ad4b451cc08aa'
AFTER_ARCHIVE_SHA256 = 'd2ced8383c3c65f8776c80d834853cb4f8168be6fdcfdf052104c2b8c697da2e'
BEFORE_SHA256 = '98e64a247591a4e9f85c9b9977ac9f9f601bdfb9cdc6700be320e106202a30b4'
AFTER_SHA256 = '9c21a7f046bc8faf2d0a9d00a9ae23ac7574bf44805485a54b3c635d23a63b5f'
BEFORE_BYTES = 236
AFTER_BYTES = 252

HEAD = (
    (66, 255, 0),
    (30, 30),
    (32, 0, 22, 0, 17),
    (32, 0, 22, 5, 24),
    (32, 0, 22, 6, 26),
)


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _words(data):
    _need(len(data) % 4 == 0, 'status-icon script alignment')
    return struct.unpack('<%dI' % (len(data) // 4), data)


def patch_member(before):
    """Dispatch messages 5/6 before the icon clear and preserve their waits."""
    _need(type(before) is bytes and len(before) == BEFORE_BYTES,
          'status-icon member size/type')
    _need(_sha(before) == BEFORE_SHA256,
          'status-icon member differs from pinned V4')
    old = _words(before)
    _need((old[7:10], old[10:12], old[12:17], old[17:22], old[22:27])
          == HEAD, 'status-icon control-flow preimage differs')
    new = (old[:7]
           + old[17:21] + (34,)
           + old[22:26] + (38,)
           + old[7:10]
           + old[10:12]
           + old[12:16] + (7,)
           + old[27:32] + (59, 28)
           + old[34:44] + (59, 16)
           + old[10:12] + old[46:51] + (59, 7)
           + old[10:12] + old[53:58] + old[58:])
    after = struct.pack('<%dI' % len(new), *new)
    _need(len(after) == AFTER_BYTES and _sha(after) == AFTER_SHA256,
          'status-icon repaired member digest')
    return after


def derive(base, language, charmap=None):
    """Declare the exact member-221 replacement for either pinned V4 input."""
    _need(type(base) is bytes and language in ('EN', 'IT'),
          'status-icon producer arguments')
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(ARCHIVE)
    _need(fid == FILE_ID, 'status-icon archive file ID differs from pinned V4')
    raw = bytes(rom.files[fid])
    _need(_sha(raw) == ARCHIVE_SHA256,
          'status-icon archive differs from pinned V4')
    members = archives.members(raw)
    _need(len(members) == MEMBERS, 'status-icon archive member count')
    replacement = patch_member(members[MEMBER])
    return archives.ArchiveDelta.make(
        ARCHIVE, fid, NAME, raw, {MEMBER: replacement},
        {'archive_sha256': ARCHIVE_SHA256,
         'member_before_sha256': BEFORE_SHA256,
         'member_after_sha256': AFTER_SHA256})


@archives._guarded
def check(index, before, after, language):
    """Rebuild the full branch graph and reject every foreign postimage."""
    _need(type(index) is int and index == MEMBER and language in ('EN', 'IT'),
          'status-icon checker identity')
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == BEFORE_BYTES and len(after) == AFTER_BYTES,
          'status-icon checker member size/type')
    _need(_sha(before) == BEFORE_SHA256 and _sha(after) == AFTER_SHA256,
          'status-icon checker member digest')
    _need(after == patch_member(before),
          'status-icon checker reconstruction')
    words = _words(after)
    _need(words[7:12] == (32, 0, 22, 5, 34)
          and words[12:17] == (32, 0, 22, 6, 38)
          and words[17:22] == (66, 255, 0, 30, 30)
          and words[22:27] == (32, 0, 22, 0, 7),
          'status-icon checker dispatch head')
    _need(words[46:48] == words[55:57] == (30, 30),
          'status-icon checker volatile waits')
    _need(words[-1] == 224, 'status-icon checker endpoint')


PRODUCERS = {NAME: derive}
CHECKERS = {NAME: check}
