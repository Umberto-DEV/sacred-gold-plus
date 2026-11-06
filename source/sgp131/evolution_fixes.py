"""Pinned repairs for four malformed Plus evolution parameters.

The producer returns member deltas only.  The shared archive owner applies them
once, and the UI compiler consumes the same replacements when it builds the
in-game Guide so player-facing rules cannot diverge from battle data.
"""
import hashlib
import struct

import ndspy.rom

from . import archives

NAME = 'evolution-fixes'
ARCHIVE = 'a/0/3/4'
ARCHIVE_SHA256 = 'fad0200a3e7e56c0bf3a4ce4487937de16598cc4ba71b3741d8741bc3b890322'

# member: (before triple, repaired triple, exact before member, exact after member)
CASES = {
    349: ((15, 0, 350), (15, 170, 350),
          '4a41dd74894a11cd3fe74a7146bce61a44ba68ed3d8b0c8fa5f263c11a2cb8e9',
          'c698513958db0dc0ee678cfb043c30339371bb4a2e869e30543b7a77e90730bc'),
    412: ((23, 0, 413), (23, 20, 413),
          '00a2f8ed5e6cbc0aad153aed6d4a44f3d0185ca79544fee51c9c27a65aee3adc',
          'e561912db66035c2440f12e46b25b29d851a909ead90a82083da675c57c993e2'),
    415: ((23, 0, 416), (23, 21, 416),
          '2f2a7ba69054b67eaf17fa384b761b79995824f7a0521d3365225b94f84d9ec2',
          '004cdf4dc0f449708d2298bb1734e2155f14f20c43b19d7320fde3bbec94821a'),
    458: ((21, 100, 226), (21, 223, 226),
          '9d28b6d7c1d42c1a7514861215d87e2b9653e44e6ce85904f631930c9cadac0b',
          '7f6f85aaa3a5051c537684135f2c899a3532cf227cf5e9cdbfcd0afdf51aeb34'),
}


def _need(ok, reason):
    if not ok:
        raise ValueError(reason)


def _repair(index, before):
    _need(type(index) is int and index in CASES and type(before) is bytes,
          'evolution member identity')
    old, new, before_sha, after_sha = CASES[index]
    _need(len(before) == 44 and hashlib.sha256(before).hexdigest() == before_sha,
          'evolution member differs from pinned V4')
    _need(struct.unpack_from('<3H', before) == old, 'evolution record differs from pinned V4')
    after = before[:2] + struct.pack('<H', new[1]) + before[4:]
    _need(struct.unpack_from('<3H', after) == new
          and hashlib.sha256(after).hexdigest() == after_sha, 'evolution repair digest')
    return after


def derive(base, language, charmap=None):
    """Return the four exact threshold/party-species repairs for canonical V4."""
    _need(type(base) is bytes and language in ('EN', 'IT'), 'evolution producer arguments')
    rom = ndspy.rom.NintendoDSRom(base)
    fid = rom.filenames.idOf(ARCHIVE)
    original = bytes(rom.files[fid])
    _need(hashlib.sha256(original).hexdigest() == ARCHIVE_SHA256,
          'evolution archive differs from pinned V4')
    members = archives.members(original)
    replacements = {index: _repair(index, members[index]) for index in sorted(CASES)}
    return archives.ArchiveDelta.make(
        ARCHIVE, fid, NAME, original, replacements, {'archive_sha256': ARCHIVE_SHA256})


@archives._guarded
def check(index, before, after, language):
    """Require the exact semantic endpoint and forbid every unrelated byte edit."""
    _need(type(index) is int and index in CASES and type(before) is bytes
          and type(after) is bytes and language in ('EN', 'IT'), 'evolution checker arguments')
    old, new, before_sha, after_sha = CASES[index]
    _need(hashlib.sha256(before).hexdigest() == before_sha
          and hashlib.sha256(after).hexdigest() == after_sha, 'evolution member digest')
    _need(struct.unpack_from('<3H', before) == old
          and struct.unpack_from('<3H', after) == new, 'evolution semantic endpoints')
    _need(after[:2] + after[4:] == before[:2] + before[4:],
          'evolution repair changed bytes outside the parameter halfword')


PRODUCERS = {NAME: derive}
CHECKERS = {NAME: check}
