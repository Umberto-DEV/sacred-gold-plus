"""HG-F18 Strength battle-animation phase fix.

The HGSS task adds the repeating X sequence ``+2, 0, -2, 0`` during the
shrink.  Retail asks for ten frames, whose sum is +2, and the native cleanup
does not restore X.  The authenticated HGSS workaround changes the existing
frame count from 10 to 8, completing two full four-tick cycles with zero drift.
"""
from dataclasses import dataclass
import hashlib
import struct

import ndspy.narc

from . import battle_animation_dynamicpunch as dynamicpunch
from . import battle_animation_facade as facade
from . import battle_animation_helping_hand as helping_hand


MEMBER_SIZE = 288
MEMBER_COUNT = 501
MEMBER_INDEX = 70
FACADE_MEMBER_INDEX = facade.MEMBER_INDEX
DYNAMICPUNCH_MEMBER_INDEX = dynamicpunch.MEMBER_INDEX
HELPING_HAND_MEMBER_INDEX = helping_hand.MEMBER_INDEX
ARCHIVE = facade.ARCHIVE
FILE_ID = facade.FILE_ID
LANGUAGES = facade.LANGUAGES
HEADER_BYTES = facade.HEADER_BYTES

RETAIL_ARCHIVE_SHA256 = facade.ARCHIVE_BEFORE_SHA256
ARCHIVE_BEFORE_SHA256 = helping_hand.ARCHIVE_AFTER_SHA256
ARCHIVE_AFTER_SHA256 = 'b5103eda322503d6980c95c1383d96f0f6683aa5879cb3b179540128dbbc5a51'
MEMBER_BEFORE_SHA256 = 'a5623bc14831c306b226bd7be6df9e6a6752cb99e4ab614006f686a60abc1ba1'
MEMBER_AFTER_SHA256 = '131c2ee0b000aea8444ca5107409af51415491e63009cac0650e7a172b23c7d2'

COMMAND_OFFSET = 0xB8
FRAME_COUNT_OFFSET = 0xCC
RETAIL_FRAMES = 10
FIXED_FRAMES = 8


@dataclass(frozen=True)
class Schedule:
    offsets: tuple
    final_x: int


@dataclass(frozen=True)
class MemberTiming:
    frames: int
    schedule: Schedule


def evaluate_strength_schedule(frames):
    """Return the native four-tick X phase for a bounded frame count."""
    if type(frames) is not int or frames <= 0:
        raise ValueError('Strength frame count must be a positive integer')
    cycle = (2, 0, -2, 0)
    offsets = tuple(cycle[index % len(cycle)] for index in range(frames))
    return Schedule(offsets, sum(offsets))


def read_member_timing(member):
    """Authenticate the Strength task command and its adjacent sound command."""
    member = bytes(member)
    if len(member) != MEMBER_SIZE:
        raise ValueError(f'Strength member must be {MEMBER_SIZE} bytes')
    words = struct.unpack_from('<11I', member, COMMAND_OFFSET)
    if words[:5] != (0x2D, 5, 4, 70, 120) or words[6] != 5:
        raise ValueError('Strength task command differs')
    frames = words[5]
    if frames not in (RETAIL_FRAMES, FIXED_FRAMES):
        raise ValueError('Strength frame count is neither retail nor fixed')
    if words[7:] != (0x16, 0x787, 0xFFFFFF8B, 1):
        raise ValueError('Strength sound command differs')
    return MemberTiming(frames, evaluate_strength_schedule(frames))


def patch_exact_member(member, expected_sha256):
    """Change only the exact Strength shrink frame-count byte."""
    member = bytes(member)
    timing = read_member_timing(member)
    actual = hashlib.sha256(member).hexdigest()
    if actual != expected_sha256:
        if timing.frames == FIXED_FRAMES:
            raise ValueError('Strength member is already patched')
        raise ValueError(f'foreign Strength member sha256 {actual}')
    if timing.frames == FIXED_FRAMES:
        raise ValueError('Strength member is already patched')
    out = bytearray(member)
    struct.pack_into('<I', out, FRAME_COUNT_OFFSET, FIXED_FRAMES)
    out = bytes(out)
    fixed = read_member_timing(out)
    if fixed.schedule.final_x != 0:
        raise ValueError('Strength timing fix failed its position invariant')
    return out


def patch_exact_archive(raw, expected_member_sha256):
    raw = bytes(raw)
    _data, spans = facade._narc_layout(raw)
    if len(spans) != MEMBER_COUNT:
        raise ValueError(f'Strength archive needs {MEMBER_COUNT} members')
    start, end = spans[MEMBER_INDEX]
    if end - start != MEMBER_SIZE:
        raise ValueError(f'Strength member {MEMBER_INDEX} must be {MEMBER_SIZE} bytes')
    patched_member = patch_exact_member(raw[start:end], expected_member_sha256)
    out = bytearray(raw)
    out[start:end] = patched_member
    return bytes(out)


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _predecessor_hashes(combined):
    return {
        FACADE_MEMBER_INDEX: (facade.MEMBER_AFTER_SHA256 if combined
                              else facade.MEMBER_BEFORE_SHA256),
        DYNAMICPUNCH_MEMBER_INDEX: (dynamicpunch.MEMBER_AFTER_SHA256 if combined
                                    else dynamicpunch.MEMBER_BEFORE_SHA256),
        HELPING_HAND_MEMBER_INDEX: (helping_hand.MEMBER_AFTER_SHA256 if combined
                                    else helping_hand.MEMBER_BEFORE_SHA256),
    }


def patch_archive(raw):
    """Patch only the exact Facade+DynamicPunch+Helping Hand successor."""
    raw = bytes(raw)
    digest = _sha256(raw)
    if digest == ARCHIVE_AFTER_SHA256:
        raise ValueError('Strength archive is already patched')
    if digest in (RETAIL_ARCHIVE_SHA256, facade.ARCHIVE_AFTER_SHA256,
                  dynamicpunch.ARCHIVE_AFTER_SHA256):
        raise ValueError('Strength animation predecessor missing')
    if digest != ARCHIVE_BEFORE_SHA256:
        raise ValueError(f'foreign Strength archive sha256 {digest}')
    files = ndspy.narc.NARC(raw).files
    for index, expected in _predecessor_hashes(True).items():
        if _sha256(bytes(files[index])) != expected:
            raise ValueError('Strength animation predecessor member differs')
    out = patch_exact_archive(raw, MEMBER_BEFORE_SHA256)
    if _sha256(out) != ARCHIVE_AFTER_SHA256:
        raise ValueError('Strength archive postimage differs')
    return out


def _rom_archive(data):
    return facade._rom_archive(data)


def apply(data, language):
    if language not in LANGUAGES:
        raise ValueError(f'unknown language {language!r}: expected EN or IT')
    data = bytes(data)
    _rom, file_id, start, end, archive = _rom_archive(data)
    patched_archive = patch_archive(archive)
    out = bytearray(data)
    out[start:end] = patched_archive
    out = bytes(out)

    data_offset, spans = facade._narc_layout(archive)
    member_start, _member_end = spans[MEMBER_INDEX]
    archive_offset = member_start + FRAME_COUNT_OFFSET
    rom_offset = start + archive_offset
    receipt = {
        'schema': 1,
        'stage': 'battle-animation-strength',
        'language': language,
        'archive': ARCHIVE,
        'file_id': file_id,
        'rom_slot': [start, end],
        'archive_data_offset': data_offset,
        'member': MEMBER_INDEX,
        'archive_offset': archive_offset,
        'rom_offset': rom_offset,
        'input_sha256': _sha256(data),
        'output_sha256': _sha256(out),
        'archive_sha256_before': ARCHIVE_BEFORE_SHA256,
        'archive_sha256_after': ARCHIVE_AFTER_SHA256,
        'member_sha256_before': MEMBER_BEFORE_SHA256,
        'member_sha256_after': MEMBER_AFTER_SHA256,
        'frames_before': RETAIL_FRAMES,
        'frames_after': FIXED_FRAMES,
    }
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    before, after = bytes(before), bytes(after)
    if receipt.get('schema') != 1 or receipt.get('stage') != 'battle-animation-strength':
        raise ValueError('Strength receipt schema or stage differs')
    if receipt.get('language') not in LANGUAGES:
        raise ValueError('Strength receipt language differs')
    if _sha256(before) != receipt.get('input_sha256'):
        raise ValueError('Strength receipt input identity differs')
    if _sha256(after) != receipt.get('output_sha256'):
        raise ValueError('Strength receipt output identity differs')
    if len(before) != len(after) or before[:HEADER_BYTES] != after[:HEADER_BYTES]:
        raise ValueError('Strength changed ROM length or header')

    old_rom, old_id, old_start, old_end, old_archive = _rom_archive(before)
    new_rom, new_id, new_start, new_end, new_archive = _rom_archive(after)
    if (old_id, old_start, old_end) != (new_id, new_start, new_end):
        raise ValueError('Strength archive FAT identity changed')
    if receipt.get('file_id') != old_id or receipt.get('rom_slot') != [old_start, old_end]:
        raise ValueError('Strength archive FAT identity differs from receipt')
    if len(old_rom.files) != len(new_rom.files):
        raise ValueError('Strength NitroFS file count changed')
    for index, (old_file, new_file) in enumerate(zip(old_rom.files, new_rom.files)):
        if index != old_id and old_file != new_file:
            raise ValueError(f'Strength changed unrelated NitroFS file {index}')
    if (_sha256(old_archive) != ARCHIVE_BEFORE_SHA256
            or _sha256(new_archive) != ARCHIVE_AFTER_SHA256):
        raise ValueError('Strength archive preimage or postimage differs')

    old_data, old_spans = facade._narc_layout(old_archive)
    new_data, new_spans = facade._narc_layout(new_archive)
    if old_data != new_data or old_spans != new_spans or len(old_spans) != MEMBER_COUNT:
        raise ValueError('Strength NARC geometry changed')
    old_files = ndspy.narc.NARC(old_archive).files
    new_files = ndspy.narc.NARC(new_archive).files
    for index, (old_member, new_member) in enumerate(zip(old_files, new_files)):
        if index != MEMBER_INDEX and old_member != new_member:
            raise ValueError(f'Strength changed unrelated NARC member {index}')
    old_member = bytes(old_files[MEMBER_INDEX])
    new_member = bytes(new_files[MEMBER_INDEX])
    if (_sha256(old_member) != MEMBER_BEFORE_SHA256
            or _sha256(new_member) != MEMBER_AFTER_SHA256):
        raise ValueError('Strength member preimage or postimage differs')
    for index, expected in _predecessor_hashes(True).items():
        if (_sha256(bytes(old_files[index])) != expected
                or bytes(old_files[index]) != bytes(new_files[index])):
            raise ValueError('Strength changed or lost an animation predecessor')

    retail = read_member_timing(old_member)
    fixed = read_member_timing(new_member)
    if retail.frames != RETAIL_FRAMES or retail.schedule.final_x != 2:
        raise ValueError('Strength retail drift reproduction differs')
    if fixed.frames != FIXED_FRAMES or fixed.schedule.final_x != 0:
        raise ValueError('Strength fixed position invariant differs')

    member_start = old_spans[MEMBER_INDEX][0]
    archive_offset = member_start + FRAME_COUNT_OFFSET
    rom_offset = old_start + archive_offset
    changed = facade._changed_offsets(before, after)
    if changed != [rom_offset]:
        raise ValueError(f'Strength changed ROM offsets {changed[:12]}, expected {[rom_offset]}')
    if receipt.get('archive_offset') != archive_offset or receipt.get('rom_offset') != rom_offset:
        raise ValueError('Strength changed offset differs from receipt')
    if receipt.get('archive_data_offset') != old_data or receipt.get('member') != MEMBER_INDEX:
        raise ValueError('Strength NARC identity differs from receipt')
    if (receipt.get('archive_sha256_before') != ARCHIVE_BEFORE_SHA256
            or receipt.get('archive_sha256_after') != ARCHIVE_AFTER_SHA256
            or receipt.get('member_sha256_before') != MEMBER_BEFORE_SHA256
            or receipt.get('member_sha256_after') != MEMBER_AFTER_SHA256
            or receipt.get('frames_before') != RETAIL_FRAMES
            or receipt.get('frames_after') != FIXED_FRAMES):
        raise ValueError('Strength receipt timing or hash pins differ')
    return {
        'rom_length': len(after),
        'changed_rom_bytes': len(changed),
        'rom_offset': rom_offset,
        'nitrofs_files_unchanged': len(old_rom.files) - 1,
        'archive_members_unchanged': MEMBER_COUNT - 1,
        'frames_before': retail.frames,
        'frames_after': fixed.frames,
        'offsets_before': list(retail.schedule.offsets),
        'offsets_after': list(fixed.schedule.offsets),
        'final_x_before': retail.schedule.final_x,
        'final_x_after': fixed.schedule.final_x,
        'predecessor_members_preserved': True,
    }


def changed_regions(data):
    data = bytes(data)
    _rom, _file_id, start, _end, archive = _rom_archive(data)
    digest = _sha256(archive)
    if digest not in (RETAIL_ARCHIVE_SHA256, ARCHIVE_BEFORE_SHA256):
        raise ValueError('Strength regions require retail or combined predecessor')
    _data, spans = facade._narc_layout(archive)
    if len(spans) != MEMBER_COUNT:
        raise ValueError(f'Strength archive needs {MEMBER_COUNT} members')
    member_start, member_end = spans[MEMBER_INDEX]
    if member_end - member_start != MEMBER_SIZE:
        raise ValueError('Strength member size differs')
    files = ndspy.narc.NARC(archive).files
    if _sha256(bytes(files[MEMBER_INDEX])) != MEMBER_BEFORE_SHA256:
        raise ValueError('Strength member preimage differs')
    for index, expected in _predecessor_hashes(digest == ARCHIVE_BEFORE_SHA256).items():
        if _sha256(bytes(files[index])) != expected:
            raise ValueError('Strength animation region predecessor differs')
    offset = start + member_start + FRAME_COUNT_OFFSET
    return ((offset, offset + 1),)
