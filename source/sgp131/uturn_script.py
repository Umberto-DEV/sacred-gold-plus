"""HG-B05 outgoing held-item snapshot for the retail pivot subscript.

The script records the effective (Klutz/Embargo-aware) flinch hold effect and
its modifier after pivot item processing but before the battler slot is
replaced.  The native late consumer owns and clears the marked scratch word.
This producer changes one NARC member in memory and never writes a ROM or save.
"""
import hashlib
import struct

import ndspy.rom

from . import archives

NAME = 'uturn-item-snapshot'
ARCHIVE = 'a/0/0/1'
FILE_ID = 130
MEMBER = 175
MEMBERS = 297
INSERT_AT = 0x3C
ARCHIVE_SHA256 = '4bdd8f93da7831add2db84671be9cc4c5d3ab2f981c391f3f84ad4b451cc08aa'
AFTER_ARCHIVE_SHA256 = '231361fe79c605abef41c24bbf6fac9138aae2464c8d1be39780121a3e4d4dce'
BEFORE_SHA256 = 'b1c159eaba419c3ab00dc6f904037abbe8ecc67c1416f4ac4ab0baf59eb5e2f1'
AFTER_SHA256 = 'eaa254c435e16397b233c8f3e796f1655003358e4252bcc57352f3ca89b58c9a'
BEFORE_BYTES = 696
AFTER_BYTES = 800

# UpdateVar SET marker; CheckItemHoldEffect HAVE attacker/flinch; skip or pack
# effect 56 + (raw modifier << 8). CheckItemHoldEffect is the effective getter;
# GetItemEffectParam is reached only when that check succeeds.
INSERT = struct.pack(
    '<26I',
    50, 7, 68, 1 << 16,
    166, 0, 1, 56, 2,
    59, 15,
    50, 10, 68, 56,
    168, 1, 9,
    50, 14, 9, 8,
    57, 10, 68, 9,
)
BRANCHES = ((0x08, 0xAA, 0xC4), (0x18, 0xA6, 0xC0))


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def patch_member(before):
    """Insert the snapshot and relocate only the two branches to final End."""
    _need(type(before) is bytes and len(before) == BEFORE_BYTES,
          'U-turn pivot member size/type')
    _need(_sha(before) == BEFORE_SHA256,
          'U-turn pivot member differs from pinned V4')
    prefix = bytearray(before[:INSERT_AT])
    for offset, old, new in BRANCHES:
        _need(struct.unpack_from('<I', prefix, offset)[0] == old,
              'U-turn pivot branch preimage differs')
        struct.pack_into('<I', prefix, offset, new)
    after = bytes(prefix) + INSERT + before[INSERT_AT:]
    _need(len(after) == AFTER_BYTES and _sha(after) == AFTER_SHA256,
          'U-turn pivot snapshot digest')
    return after


def derive(base, language, charmap=None):
    """Declare member 175 of the exact V4 battle-script archive."""
    _need(type(base) is bytes and language in ('EN', 'IT'),
          'U-turn snapshot producer arguments')
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(ARCHIVE)
    _need(fid == FILE_ID, 'U-turn archive file ID differs from pinned V4')
    raw = bytes(rom.files[fid])
    _need(_sha(raw) == ARCHIVE_SHA256,
          'U-turn archive differs from pinned V4')
    members = archives.members(raw)
    _need(len(members) == MEMBERS, 'U-turn archive member count')
    replacement = patch_member(members[MEMBER])
    return archives.ArchiveDelta.make(
        ARCHIVE, fid, NAME, raw, {MEMBER: replacement},
        {'archive_sha256': ARCHIVE_SHA256,
         'member_before_sha256': BEFORE_SHA256,
         'member_after_sha256': AFTER_SHA256})


@archives._guarded
def check(index, before, after, language):
    """Rebuild the exact insertion and prove the shifted complement."""
    _need(type(index) is int and index == MEMBER and language in ('EN', 'IT'),
          'U-turn snapshot checker identity')
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == BEFORE_BYTES and len(after) == AFTER_BYTES,
          'U-turn snapshot checker member size/type')
    _need(_sha(before) == BEFORE_SHA256 and _sha(after) == AFTER_SHA256,
          'U-turn snapshot checker member digest')
    _need(after == patch_member(before),
          'U-turn snapshot checker reconstruction')
    _need(after[INSERT_AT:INSERT_AT + len(INSERT)] == INSERT,
          'U-turn snapshot checker command sequence')
    _need(after[INSERT_AT + len(INSERT):] == before[INSERT_AT:],
          'U-turn snapshot checker shifted complement')
    for offset, old, new in BRANCHES:
        _need(struct.unpack_from('<I', before, offset)[0] == old
              and struct.unpack_from('<I', after, offset)[0] == new,
              'U-turn snapshot checker branch relocation')


PRODUCERS = {NAME: derive}
CHECKERS = {NAME: check}
