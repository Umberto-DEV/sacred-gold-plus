"""HG-B07: persist delayed Pressure PP before a manual switch can reload it.

Counter, Mirror Coat, Magic Coat, Snatch and Metal Burst can debit the second
Pressure PP after the ordinary party-copy command has already been emitted.
Each successful path receives one existing ``UpdateMonData ADD status, 0``
command: status is unchanged, while the authentic command performs the missing
BattleMon-to-PartyMon copy.  This module only declares five pinned NARC member
replacements in memory; it never writes a ROM or save.
"""
import hashlib
import struct

import ndspy.rom

from . import archives


EFFECT_NAME = 'pressure-switch-effects'
SUBSCRIPT_NAME = 'pressure-switch-subscripts'
EFFECT_ARCHIVE = 'a/0/3/0'
SUBSCRIPT_ARCHIVE = 'a/0/0/1'
ARCHIVES = {
    EFFECT_ARCHIVE: {
        'file_id': 159,
        'members': 277,
        'sha256': 'a26d5906856068e60e16ac0e311852ac5f9b48d5e7cde43cdca69f1a72207382',
        'producer': EFFECT_NAME,
    },
    SUBSCRIPT_ARCHIVE: {
        'file_id': 130,
        'members': 297,
        'sha256': '4bdd8f93da7831add2db84671be9cc4c5d3ab2f981c391f3f84ad4b451cc08aa',
        'producer': SUBSCRIPT_NAME,
    },
}

SYNC_ATTACKER = (52, 8, 1, 52, 0)
SYNC_DEFENDER = (52, 8, 2, 52, 0)
SYNC_MSG_TEMP = (52, 8, 0xFF, 52, 0)

# archive/index -> before bytes, after bytes, before SHA, after SHA
IDENTITIES = {
    (EFFECT_ARCHIVE, 89): (24, 44,
        '91ec5bf633f548c9d664bbb0affae5c4b5b86c9b1d92fe38eda5477f5d0c1554',
        '2b718ea1d3b1b97ba6f60fe828121152f494ddd2345737bf5aa1241867fb9959'),
    (EFFECT_ARCHIVE, 144): (24, 44,
        'fc19e9888789e491c8cfd80dcf646aab4f6a1195c4d573c58866037fa7511c88',
        '4bbb8bad26252b35bd44d1816edb04c39f178f2c4e49eda0dda5593460b0da0d'),
    (EFFECT_ARCHIVE, 227): (48, 68,
        'aa9b2b112d24996465122f8126840765910fff1b02df55758921e44572b9b4c2',
        '822bd719488011e36fc6c854198d924bcfdf518da735ca06ee699f181c1f6b19'),
    (SUBSCRIPT_ARCHIVE, 139): (72, 92,
        '2ae643e8964525154b04686d72379e9889cad72ba90dfb0faf96f2207f28577a',
        'f1408fb6e82e5430bdd16f696d5d68c4f930e2e23725c78c8ad938c386e47804'),
    (SUBSCRIPT_ARCHIVE, 146): (232, 252,
        '6b04238b8138556a891b579393c82d18262109c7526815abc9a4c5c45a0f055f',
        '2f8f0705793991ca0bb812337400c33bd07939926edaa6f0589fb7ef4ebb7548'),
}


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _words(data):
    _need(len(data) % 4 == 0, 'Pressure script alignment')
    return struct.unpack('<%dI' % (len(data) // 4), data)


def _pack(values):
    values = tuple(values)
    return struct.pack('<%dI' % len(values), *values)


def patch_member(archive, index, before):
    """Insert exactly one no-op status update on the authenticated success path."""
    identity = IDENTITIES.get((archive, index))
    _need(identity is not None, 'foreign Pressure script member')
    before_bytes, after_bytes, before_sha, after_sha = identity
    _need(type(before) is bytes and len(before) == before_bytes,
          'Pressure script member size/type')
    _need(_sha(before) == before_sha,
          'Pressure script member differs from pinned V4')
    old = _words(before)
    if (archive, index) == (EFFECT_ARCHIVE, 89):
        _need(old == (50, 10, 6, 2048, 90, 224),
              'Counter effect preimage differs')
        new = old[:-1] + SYNC_ATTACKER + old[-1:]
    elif (archive, index) == (EFFECT_ARCHIVE, 144):
        _need(old == (50, 10, 6, 2048, 91, 224),
              'Mirror Coat effect preimage differs')
        new = old[:-1] + SYNC_ATTACKER + old[-1:]
    elif (archive, index) == (EFFECT_ARCHIVE, 227):
        _need(old == (147, 5, 50, 10, 6, 2048, 224,
                      50, 10, 10, 64, 224),
              'Metal Burst effect preimage differs')
        # The failure displacement skips over both the original success tail
        # and this insertion; only a successful TryMetalBurst synchronizes.
        new = old[:6] + SYNC_ATTACKER + old[6:]
    elif (archive, index) == (SUBSCRIPT_ARCHIVE, 139):
        _need(old[12] == 131 and old[-1] == 224,
              'Magic Coat reflection preimage differs')
        # Before command 131 exchanges attacker/target, DEFENDER is the
        # reflector whose move PP CheckIgnorePressure just changed.
        new = old[:12] + SYNC_DEFENDER + old[12:]
    elif (archive, index) == (SUBSCRIPT_ARCHIVE, 146):
        _need(old[:4] == (17, 14, 30, 15) and old[-1] == 224,
              'Snatch subscript preimage differs')
        # At subscript entry battlerIdTemp is the snatcher.  Synchronize before
        # subsequent script commands exchange the message battler variables.
        new = old[:4] + SYNC_MSG_TEMP + old[4:]
    else:  # defensive: IDENTITIES and the implementation must stay in lockstep
        raise ValueError('unimplemented Pressure script member')
    after = _pack(new)
    _need(len(after) == after_bytes and _sha(after) == after_sha,
          'Pressure repaired member digest')
    return after


def _derive(base, language, archive):
    _need(type(base) is bytes and language in ('EN', 'IT'),
          'Pressure producer arguments')
    info = ARCHIVES[archive]
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(archive)
    _need(fid == info['file_id'],
          'Pressure archive file ID differs from pinned V4')
    raw = bytes(rom.files[fid])
    _need(_sha(raw) == info['sha256'],
          'Pressure archive differs from pinned V4')
    members = archives.members(raw)
    _need(len(members) == info['members'],
          'Pressure archive member count')
    replacements = {
        index: patch_member(owner, index, members[index])
        for owner, index in IDENTITIES if owner == archive
    }
    return archives.ArchiveDelta.make(
        archive, fid, info['producer'], raw, replacements,
        {'archive_sha256': info['sha256'],
         'members_sha256': _sha(b''.join(replacements.values()))})


def derive_effects(base, language, charmap=None):
    return _derive(base, language, EFFECT_ARCHIVE)


def derive_subscripts(base, language, charmap=None):
    return _derive(base, language, SUBSCRIPT_ARCHIVE)


def _check_for(archive, index, before, after, language):
    """Reconstruct one archive-bound member and reject every foreign endpoint."""
    identity = IDENTITIES.get((archive, index))
    _need(type(index) is int and identity is not None
          and language in ('EN', 'IT'), 'Pressure checker identity')
    before_bytes, after_bytes, before_sha, after_sha = identity
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == before_bytes and len(after) == after_bytes,
          'Pressure checker member size/type')
    _need(_sha(before) == before_sha and _sha(after) == after_sha,
          'Pressure checker member digest')
    _need(after == patch_member(archive, index, before),
          'Pressure checker reconstruction')


@archives._guarded
def check_effects(index, before, after, language):
    _check_for(EFFECT_ARCHIVE, index, before, after, language)


@archives._guarded
def check_subscripts(index, before, after, language):
    _check_for(SUBSCRIPT_ARCHIVE, index, before, after, language)


@archives._guarded
def check(index, before, after, language):
    """Convenience checker for direct tests; owner registration stays archive-bound."""
    matches = [archive for archive, member in IDENTITIES if member == index]
    _need(len(matches) == 1, 'Pressure checker identity')
    _check_for(matches[0], index, before, after, language)


PRODUCERS = {
    EFFECT_NAME: derive_effects,
    SUBSCRIPT_NAME: derive_subscripts,
}
CHECKERS = {
    EFFECT_NAME: check_effects,
    SUBSCRIPT_NAME: check_subscripts,
}
