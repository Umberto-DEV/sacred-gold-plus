"""Guarded, additive level-up moves; game records are supplied privately.

The reminder allocates 42 bytes in the supported native games. Keep each edited
member at no more than 20 moves plus its terminator. NARC alignment belongs
outside the member: padding a 42-byte record to 44 would overrun that buffer.
"""
import hashlib
import json
from pathlib import Path
import struct

import ndspy.narc
import ndspy.rom

ARCHIVE = 'a/0/3/3'
GUARDS = ('a/0/0/2', 'a/0/1/1', ARCHIVE)


def load_specification():
    return json.loads((Path(__file__).parent / 'data/learnset-changes.json').read_text())


def _pair(level, move):
    if type(level) is not int or not 1 <= level <= 100:
        raise ValueError('learnset level must be an integer in 1..100')
    if type(move) is not int or not 1 <= move <= 467:
        raise ValueError('learnset move must be an integer in 1..467')
    return level, move


def decode(raw):
    """Read a terminated, level-ordered member, allowing zero alignment bytes."""
    if not raw or len(raw) % 2:
        raise ValueError('incomplete learnset member')
    words = struct.unpack('<' + 'H' * (len(raw) // 2), raw)
    try:
        end = words.index(0xffff)
    except ValueError as exc:
        raise ValueError('learnset terminator missing') from exc
    if any(words[end + 1:]):
        raise ValueError('nonzero data after learnset terminator')
    pairs = [_pair(word >> 9, word & 511) for word in words[:end]]
    if len(set(pairs)) != len(pairs):
        raise ValueError('duplicate source learnset pair')
    if any(a[0] > b[0] for a, b in zip(pairs, pairs[1:])):
        raise ValueError('learnset levels are not ordered')
    return pairs


def add_moves(raw, additions):
    """Insert new pairs after existing entries at the same level, without removal."""
    original = decode(raw)
    additions = list(additions)
    if not additions:
        raise ValueError('empty learnset addition')
    new = [_pair(entry['level'], entry['move']) for entry in additions]
    if len(set(new)) != len(new) or set(new).intersection(original):
        raise ValueError('duplicate learnset addition')
    if len(original) + len(new) > 20:
        raise ValueError('learnset exceeds the reminder capacity')
    # Stable sorting preserves every original same-level relationship and puts
    # new moves after the original entries, so level-up offers are predictable.
    pairs = sorted(original + new, key=lambda pair: pair[0])
    result = b''.join(struct.pack('<H', level * 512 + move) for level, move in pairs)
    return result + b'\xff\xff'


def patch_archive(raw_archive, changes, expected_sha256):
    """Validate all preimages before returning one changed archive and receipts."""
    if hashlib.sha256(raw_archive).hexdigest() != expected_sha256:
        raise ValueError('learnset archive preimage mismatch')
    archive = ndspy.narc.NARC(raw_archive)
    original = list(archive.files)
    changes = list(changes)
    if not changes:
        raise ValueError('empty learnset patch')
    replacements, report = {}, []
    for change in changes:
        species = change['species']
        if type(species) is not int or not 1 <= species < len(original):
            raise ValueError('learnset member index outside supported archive')
        if species in replacements:
            raise ValueError('duplicate learnset member')
        before = original[species]
        before_hash = hashlib.sha256(before).hexdigest()
        if before_hash != change['source_sha256']:
            raise ValueError(f'learnset member preimage mismatch: {species}')
        after = add_moves(before, change['additions'])
        replacements[species] = after
        report.append({'species': species, 'added': change['additions'],
                       'before_sha256': before_hash,
                       'after_sha256': hashlib.sha256(after).hexdigest(),
                       'before_bytes': len(before), 'after_bytes': len(after)})
    for species, replacement in replacements.items():
        archive.files[species] = replacement
    result = archive.save()
    checked = ndspy.narc.NARC(result).files
    if len(checked) != len(original):
        raise ValueError('learnset member count changed')
    for index, member in enumerate(checked):
        if member != replacements.get(index, original[index]):
            raise ValueError(f'learnset member readback failed: {index}')
    return result, report


def apply(data, specification=None):
    """Patch only the guarded learnset resource, leaving saved Pokémon untouched.

    Personal and move-table preimages pin the semantics used by the balance
    measurements. The caller must rebuild from a supported original; applying
    this stage again is an error, not an attempt to infer an unknown base.
    """
    from .resources import append_file
    spec = load_specification() if specification is None else specification
    if spec.get('schema') != 1 or set(spec.get('preimages', {})) != set(GUARDS):
        raise ValueError('learnset specification requires schema 1 and all semantic guards')
    rom = ndspy.rom.NintendoDSRom(data)
    for path in GUARDS:
        if hashlib.sha256(rom.getFileByName(path)).hexdigest() != spec['preimages'][path]:
            raise ValueError(f'learnset semantic preimage mismatch: {path}')
    file_id = rom.filenames.idOf(ARCHIVE)
    encoded, changes = patch_archive(rom.files[file_id], spec['changes'],
                                     spec['preimages'][ARCHIVE])
    result = append_file(data, file_id, encoded)
    check = ndspy.rom.NintendoDSRom(result)
    if len(check.files) != len(rom.files) or any(
            a != b for index, (a, b) in enumerate(zip(rom.files, check.files))
            if index != file_id):
        raise ValueError('learnset stage changed an unrelated NitroFS file')
    if (check.arm9, check.arm7, check.iconBanner) != (rom.arm9, rom.arm7, rom.iconBanner):
        raise ValueError('learnset stage changed native executable/banner data')
    if check.files[file_id] != encoded:
        raise ValueError('installed learnset archive readback failed')
    return result, {'preimages': spec['preimages'], 'changes': changes,
                    'archive_output_sha256': hashlib.sha256(encoded).hexdigest(),
                    'other_files_and_native_executables_unchanged': True}
