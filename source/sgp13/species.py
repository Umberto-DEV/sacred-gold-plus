"""Guarded authored species deltas; no saved Pokémon data is rewritten.

The personal table is global: wilds, player Pokémon after native stat
recalculation, and trainers in both modes share these changes. Trainer parties
with explicit moves do not acquire additions from the separate learnset stage.
Kricketune gains Technician in its empty second slot; Meganium's second slot
uses Natural Cure for new Pokémon. Existing saved ability bytes, including
Meganium's original Overgrow, remain authoritative. This stage neither refreshes
cached party stats nor promises new moves without ordinary level-up/reminder access.
"""
import hashlib
import json
from pathlib import Path

import ndspy.narc
import ndspy.rom

ARCHIVE = 'a/0/0/2'
GUARDS = (ARCHIVE, 'a/0/1/1')
RECORD_BYTES = 44


def validate_audit(audit, personal_changes, learnset_changes):
    """Check authored coverage and references without duplicating game tables."""
    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def ids(rows):
        if not isinstance(rows, list):
            raise ValueError('balance audit/specification rows must be lists')
        result = set()
        for row in rows:
            index = row.get('species') if isinstance(row, dict) else None
            if type(index) is not int or not 1 <= index <= 493 or index in result:
                raise ValueError('balance audit/specification species must be unique IDs 1..493')
            result.add(index)
        return result

    if (not isinstance(audit, dict) or type(audit.get('schema')) is not int or
            audit['schema'] != 1 or audit.get('analysis_only') is not True or
            audit.get('stats_order') != ['HP', 'Atk', 'Def', 'Spe', 'SpA', 'SpD']):
        raise ValueError('balance audit requires schema 1, authored analysis and native stats order')
    source = audit.get('source')
    if not isinstance(source, dict) or not all(text(source.get(k)) for k in ('name', 'version', 'url')):
        raise ValueError('balance audit requires source and version citation')
    rows = audit.get('decisions')
    if ids(rows) != set(range(1, 494)):
        raise ValueError('balance audit requires complete species 1..493 coverage')
    expected = {'personal': ids(personal_changes), 'learnset': ids(learnset_changes)}
    for row in rows:
        index = row['species']
        if not all(text(row.get(k)) for k in ('name', 'role', 'reason', 'remaining_weakness', 'risk')):
            raise ValueError(f'balance audit requires meaningful authored fields: {index}')
        strengths = row.get('strengths')
        if not isinstance(strengths, list) or not strengths or not all(text(v) for v in strengths):
            raise ValueError(f'balance audit requires authored strengths: {index}')
        decision = row.get('decision')
        if decision not in ('retain', 'retain_prior', 'improve'):
            raise ValueError(f'unknown balance audit decision: {index}')
        reference = row.get('redux_reference')
        if ('redux_reference' not in row or
                (reference is not None and not text(reference))):
            raise ValueError(f'balance audit requires intervention provenance: {index}')
        patches = row.get('patches')
        if (not isinstance(patches, dict) or set(patches) != set(expected) or
                any(type(patches[k]) is not bool or patches[k] != (index in expected[k])
                    for k in expected)):
            raise ValueError(f'balance audit patch references mismatch specifications: {index}')
        if (decision == 'retain') != (not any(patches.values())):
            raise ValueError(f'balance audit decision falsely describes patched/retained species: {index}')
    return True


def load_specification():
    root = Path(__file__).parent / 'data'
    spec = json.loads((root / 'species-changes.json').read_text())
    learned = json.loads((root / 'learnset-changes.json').read_text())
    audit = json.loads((root / 'balance-audit.json').read_text())
    validate_audit(audit, spec['changes'], learned['changes'])
    return spec


def _validated_changes(members, changes):
    changes = list(changes)
    if not changes:
        raise ValueError('empty species patch')
    seen = set()
    for change in changes:
        index = change['species']
        if type(index) is not int or not 1 <= index <= 493 or index >= len(members):
            raise ValueError('species member index outside supported archive')
        if index in seen:
            raise ValueError('duplicate species member')
        seen.add(index)
        record = members[index]
        if len(record) != RECORD_BYTES:
            raise ValueError(f'personal record must be 44 bytes: {index}')
        if hashlib.sha256(record).hexdigest() != change['source_sha256']:
            raise ValueError(f'species member preimage mismatch: {index}')
        stats, abilities = change['stats'], change['abilities']
        if len(stats) != 6 or any(type(v) is not int or not 1 <= v <= 255 for v in stats):
            raise ValueError('species requires six integer base stats in 1..255')
        if (len(abilities) != 2 or
                any(type(v) is not int or not 0 <= v <= 123 for v in abilities) or
                abilities[0] == 0):
            raise ValueError('species requires two native ability slots, first nonzero')
        if stats == list(record[:6]) and abilities == list(record[22:24]):
            raise ValueError(f'species edit changes no permitted field: {index}')
    return changes


def verify_archive(before, after, changes):
    """Independently read every member and enforce the permitted byte boundary."""
    original = ndspy.narc.NARC(before).files
    updated = ndspy.narc.NARC(after).files
    if len(original) != len(updated):
        raise ValueError('species member count changed')
    changes = _validated_changes(original, changes)
    by_index = {change['species']: change for change in changes}
    for index, (old, new) in enumerate(zip(original, updated)):
        if index not in by_index:
            if new != old:
                raise ValueError(f'untouched species member changed: {index}')
            continue
        change = by_index[index]
        if (len(new) != 44 or list(new[:6]) != change['stats'] or
                list(new[22:24]) != change['abilities'] or
                new[6:22] != old[6:22] or new[24:] != old[24:]):
            raise ValueError(f'species member readback failed: {index}')
    return True


def patch_archive(raw_archive, changes, expected_sha256):
    """Validate the entire archive and each record before replacing any byte."""
    if hashlib.sha256(raw_archive).hexdigest() != expected_sha256:
        raise ValueError('species archive preimage mismatch')
    archive = ndspy.narc.NARC(raw_archive)
    changes = _validated_changes(archive.files, changes)
    receipts = []
    for change in changes:
        index = change['species']; old = archive.files[index]
        new = bytearray(old)
        new[:6] = bytes(change['stats'])
        new[22:24] = bytes(change['abilities'])
        archive.files[index] = bytes(new)
        receipts.append({'species': index,
                         'before_stats': list(old[:6]), 'after_stats': list(new[:6]),
                         'before_abilities': list(old[22:24]), 'after_abilities': list(new[22:24]),
                         'before_sha256': hashlib.sha256(old).hexdigest(),
                         'after_sha256': hashlib.sha256(new).hexdigest()})
    result = archive.save()
    verify_archive(raw_archive, result, changes)
    return result, receipts


def apply(data, specification=None):
    """Install personal deltas without touching moves, learnsets or save bytes.

    The separate additive learnset stage runs first and guards its own archive.
    Personal and move-table preimages are still unchanged at this boundary.
    Applying this stage again or to an unknown base is refused.
    """
    from .resources import append_file
    spec = load_specification() if specification is None else specification
    if spec.get('schema') != 1 or set(spec.get('preimages', {})) != set(GUARDS):
        raise ValueError('species specification requires schema 1 and all semantic guards')
    rom = ndspy.rom.NintendoDSRom(data)
    for path in GUARDS:
        if hashlib.sha256(rom.getFileByName(path)).hexdigest() != spec['preimages'][path]:
            raise ValueError(f'species semantic preimage mismatch: {path}')
    file_id = rom.filenames.idOf(ARCHIVE)
    encoded, changes = patch_archive(rom.files[file_id], spec['changes'], spec['preimages'][ARCHIVE])
    result = append_file(data, file_id, encoded)
    check = ndspy.rom.NintendoDSRom(result)
    if len(check.files) != len(rom.files) or any(
            a != b for index, (a, b) in enumerate(zip(rom.files, check.files)) if index != file_id):
        raise ValueError('species stage changed an unrelated NitroFS file')
    if (check.arm9, check.arm7, check.iconBanner) != (rom.arm9, rom.arm7, rom.iconBanner):
        raise ValueError('species stage changed native executable/banner data')
    if check.files[file_id] != encoded:
        raise ValueError('installed species archive readback failed')
    verify_archive(rom.files[file_id], check.files[file_id], spec['changes'])
    return result, {'preimages': spec['preimages'], 'changes': changes,
                    'archive_output_sha256': hashlib.sha256(encoded).hexdigest(),
                    'other_files_and_native_executables_unchanged': True}
