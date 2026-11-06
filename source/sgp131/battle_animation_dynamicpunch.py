"""HG-F20-DP DynamicPunch battle-animation scheduling fix.

The first eight-tick shake leaves the defender at X=-1 on its seventh tick.
Retail starts a second shake at that exact boundary and the second task records
the transient coordinate as its new base.  The authenticated HGSS fix changes
only the intervening Delay from 3 to 4, so the second task records X=0.

Facade owns six other bytes in the same NARC and precedes this stage.  The ROM
producer therefore accepts only Facade's exact archive postimage; the region
declarer also recognizes the cold V4 archive because chain replay asks for the
same physical span on both images.
"""
from dataclasses import dataclass
import hashlib
import struct

import ndspy.narc
import ndspy.rom

from . import battle_animation_facade as facade


MEMBER_SIZE = 496
MEMBER_COUNT = 501
MEMBER_INDEX = 223
FACADE_MEMBER_INDEX = 263
ARCHIVE = facade.ARCHIVE
FILE_ID = facade.FILE_ID
LANGUAGES = facade.LANGUAGES
HEADER_BYTES = facade.HEADER_BYTES

RETAIL_ARCHIVE_SHA256 = facade.ARCHIVE_BEFORE_SHA256
ARCHIVE_BEFORE_SHA256 = facade.ARCHIVE_AFTER_SHA256
ARCHIVE_AFTER_SHA256 = 'afa4fe4657f6963cc3d6f80aa1b9f8ad433ac052e4238241938099f980d7dc63'
MEMBER_BEFORE_SHA256 = 'e481d17db71fd51545f32706d9e76ae0578b0506bae1160dd9f223e64b12fab2'
MEMBER_AFTER_SHA256 = 'e8a3897d1aa878f19bd98b70d96fd2ffd8c718b4c8045560343e60ddd9ad4fba'
FACADE_MEMBER_AFTER_SHA256 = facade.MEMBER_AFTER_SHA256

FIRST_SHAKE_OFFSET = 0x118
FIRST_DELAY_OFFSET = 0x138
FADE_OFFSET = 0x140
BACKGROUND_SHAKE_OFFSET = 0x164
AUDIO_OFFSET = 0x184
DELAY_OPCODE_OFFSET = 0x198
DELAY_VALUE_OFFSET = 0x19C
SECOND_SHAKE_OFFSET = 0x1A0
WAIT_EMITTERS_OFFSET = 0x1C0
RETAIL_DELAY = 3
FIXED_DELAY = 4


@dataclass(frozen=True)
class Schedule:
    first_offsets: tuple
    second_offsets: tuple
    second_start_tick: int
    captured_base_x: int
    final_x: int


@dataclass(frozen=True)
class MemberTiming:
    delay: int
    schedule: Schedule


def evaluate_shake_offsets(extent_x, interval, amount):
    """Execute the state transitions of HGSS ov07_022227A8/D8 for X."""
    values = (extent_x, interval, amount)
    if any(type(value) is not int or value <= 0 for value in values):
        raise ValueError('shake extent, interval and amount must be positive integers')
    current = 0
    pending = -extent_x
    interval_counter = 0
    phase = 0
    remaining = amount
    offsets = []
    while remaining:
        interval_counter += 1
        if interval_counter >= interval:
            interval_counter = 0
            previous = current
            transition = pending
            pending = previous
            current = 0 if transition == 0 else -transition
            phase += 1
            if phase == 4:
                phase = 0
                remaining -= 1
        offsets.append(current)
    return tuple(offsets)


def evaluate_dynamicpunch_schedule(delay):
    """Return the task boundary including Delay's N+1 callback semantics."""
    if type(delay) is not int or delay <= 0:
        raise ValueError('DynamicPunch delay must be a positive integer')
    first = evaluate_shake_offsets(1, 1, 2)
    second = evaluate_shake_offsets(4, 1, 10)
    second_start = (2 + 1) + (delay + 1)
    capture_index = second_start - 1
    captured = first[capture_index] if capture_index < len(first) else 0
    return Schedule(first, second, second_start, captured, captured + second[-1])


def _expect_words(member, offset, expected, label):
    actual = struct.unpack_from('<%dI' % len(expected), member, offset)
    if actual != tuple(expected):
        raise ValueError(f'DynamicPunch {label} command differs')


def read_member_timing(member):
    """Authenticate the two shakes and every intervening scheduling command."""
    member = bytes(member)
    if len(member) != MEMBER_SIZE:
        raise ValueError(f'DynamicPunch member must be {MEMBER_SIZE} bytes')
    _expect_words(member, FIRST_SHAKE_OFFSET,
                  (0x2D, 0x24, 5, 1, 0, 1, 2, 0x108), 'first shake')
    _expect_words(member, FIRST_DELAY_OFFSET, (0, 2), 'first Delay')
    _expect_words(member, FADE_OFFSET,
                  (0x2D, 0x22, 6, 8, 0, 2, 0x84C, 0xE, 0), 'fade')
    _expect_words(member, BACKGROUND_SHAKE_OFFSET,
                  (0x2D, 0x44, 5, 5, 0, 1, 6, 0), 'background shake')
    _expect_words(member, AUDIO_OFFSET, (0x19, 0x7C9, 0x75, 4, 6), 'audio')
    if struct.unpack_from('<I', member, DELAY_OPCODE_OFFSET)[0] != 0:
        raise ValueError('DynamicPunch second Delay opcode differs')
    delay = struct.unpack_from('<I', member, DELAY_VALUE_OFFSET)[0]
    if delay not in (RETAIL_DELAY, FIXED_DELAY):
        raise ValueError('DynamicPunch delay is neither retail nor fixed')
    _expect_words(member, SECOND_SHAKE_OFFSET,
                  (0x2D, 0x24, 5, 4, 0, 1, 10, 0x108), 'second shake')
    _expect_words(member, WAIT_EMITTERS_OFFSET, (0x32,), 'emitter wait')
    return MemberTiming(delay, evaluate_dynamicpunch_schedule(delay))


def patch_exact_member(member, expected_sha256):
    """Patch one exact retail DynamicPunch member and reject every other shape."""
    member = bytes(member)
    timing = read_member_timing(member)
    actual = hashlib.sha256(member).hexdigest()
    if actual != expected_sha256:
        if timing.delay == FIXED_DELAY:
            raise ValueError('DynamicPunch member is already patched')
        raise ValueError(f'foreign DynamicPunch member sha256 {actual}')
    if timing.delay != RETAIL_DELAY:
        raise ValueError('DynamicPunch member is already patched')
    out = bytearray(member)
    struct.pack_into('<I', out, DELAY_VALUE_OFFSET, FIXED_DELAY)
    out = bytes(out)
    fixed = read_member_timing(out)
    if fixed.schedule.captured_base_x != 0 or fixed.schedule.final_x != 0:
        raise ValueError('DynamicPunch timing fix failed its position invariant')
    return out


def narc_data_offset(raw):
    return facade._narc_layout(raw)[0]


def patch_exact_archive(raw, expected_member_sha256):
    """Patch member 223 in place without rebuilding or normalizing the NARC."""
    raw = bytes(raw)
    _data, spans = facade._narc_layout(raw)
    if len(spans) != MEMBER_COUNT:
        raise ValueError(f'DynamicPunch archive needs {MEMBER_COUNT} members')
    start, end = spans[MEMBER_INDEX]
    if end - start != MEMBER_SIZE:
        raise ValueError(f'DynamicPunch member {MEMBER_INDEX} must be {MEMBER_SIZE} bytes')
    patched_member = patch_exact_member(raw[start:end], expected_member_sha256)
    out = bytearray(raw)
    out[start:end] = patched_member
    return bytes(out)


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def patch_archive(raw):
    """Patch only the exact Facade successor used by the production pipeline."""
    raw = bytes(raw)
    digest = _sha256(raw)
    if digest == ARCHIVE_AFTER_SHA256:
        raise ValueError('DynamicPunch archive is already patched')
    if digest == RETAIL_ARCHIVE_SHA256:
        raise ValueError('DynamicPunch Facade predecessor missing')
    if digest != ARCHIVE_BEFORE_SHA256:
        raise ValueError(f'foreign DynamicPunch archive sha256 {digest}')
    files = ndspy.narc.NARC(raw).files
    if _sha256(bytes(files[FACADE_MEMBER_INDEX])) != FACADE_MEMBER_AFTER_SHA256:
        raise ValueError('DynamicPunch Facade member preimage differs')
    out = patch_exact_archive(raw, MEMBER_BEFORE_SHA256)
    if _sha256(out) != ARCHIVE_AFTER_SHA256:
        raise ValueError('DynamicPunch archive postimage differs')
    return out


def _rom_archive(data):
    return facade._rom_archive(data)


def apply(data, language):
    """Apply HG-F20-DP in memory after Facade and return an exact receipt."""
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
    archive_offset = member_start + DELAY_VALUE_OFFSET
    rom_offset = start + archive_offset
    receipt = {
        'schema': 1,
        'stage': 'battle-animation-dynamicpunch',
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
        'delay_before': RETAIL_DELAY,
        'delay_after': FIXED_DELAY,
    }
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    """Re-read the ROM, NARC and schedule independently from the producer."""
    before, after = bytes(before), bytes(after)
    if receipt.get('schema') != 1 or receipt.get('stage') != 'battle-animation-dynamicpunch':
        raise ValueError('DynamicPunch receipt schema or stage differs')
    if receipt.get('language') not in LANGUAGES:
        raise ValueError('DynamicPunch receipt language differs')
    if _sha256(before) != receipt.get('input_sha256'):
        raise ValueError('DynamicPunch receipt input identity differs')
    if _sha256(after) != receipt.get('output_sha256'):
        raise ValueError('DynamicPunch receipt output identity differs')
    if len(before) != len(after) or before[:HEADER_BYTES] != after[:HEADER_BYTES]:
        raise ValueError('DynamicPunch changed ROM length or header')

    old_rom, old_id, old_start, old_end, old_archive = _rom_archive(before)
    new_rom, new_id, new_start, new_end, new_archive = _rom_archive(after)
    if (old_id, old_start, old_end) != (new_id, new_start, new_end):
        raise ValueError('DynamicPunch archive FAT identity changed')
    if receipt.get('file_id') != old_id or receipt.get('rom_slot') != [old_start, old_end]:
        raise ValueError('DynamicPunch archive FAT identity differs from receipt')
    if len(old_rom.files) != len(new_rom.files):
        raise ValueError('DynamicPunch NitroFS file count changed')
    for index, (old_file, new_file) in enumerate(zip(old_rom.files, new_rom.files)):
        if index != old_id and old_file != new_file:
            raise ValueError(f'DynamicPunch changed unrelated NitroFS file {index}')
    if (_sha256(old_archive) != ARCHIVE_BEFORE_SHA256
            or _sha256(new_archive) != ARCHIVE_AFTER_SHA256):
        raise ValueError('DynamicPunch archive preimage or postimage differs')

    old_data, old_spans = facade._narc_layout(old_archive)
    new_data, new_spans = facade._narc_layout(new_archive)
    if old_data != new_data or old_spans != new_spans or len(old_spans) != MEMBER_COUNT:
        raise ValueError('DynamicPunch NARC geometry changed')
    old_files = ndspy.narc.NARC(old_archive).files
    new_files = ndspy.narc.NARC(new_archive).files
    for index, (old_member, new_member) in enumerate(zip(old_files, new_files)):
        if index != MEMBER_INDEX and old_member != new_member:
            raise ValueError(f'DynamicPunch changed unrelated NARC member {index}')
    old_member = bytes(old_files[MEMBER_INDEX])
    new_member = bytes(new_files[MEMBER_INDEX])
    if (_sha256(old_member) != MEMBER_BEFORE_SHA256
            or _sha256(new_member) != MEMBER_AFTER_SHA256):
        raise ValueError('DynamicPunch member preimage or postimage differs')
    if (_sha256(bytes(old_files[FACADE_MEMBER_INDEX])) != FACADE_MEMBER_AFTER_SHA256
            or bytes(old_files[FACADE_MEMBER_INDEX]) != bytes(new_files[FACADE_MEMBER_INDEX])):
        raise ValueError('DynamicPunch changed or lost the Facade predecessor')

    retail = read_member_timing(old_member)
    fixed = read_member_timing(new_member)
    if retail.delay != RETAIL_DELAY or retail.schedule.final_x != -1:
        raise ValueError('DynamicPunch retail drift reproduction differs')
    if fixed.delay != FIXED_DELAY or fixed.schedule.final_x != 0:
        raise ValueError('DynamicPunch fixed position invariant differs')

    member_start = old_spans[MEMBER_INDEX][0]
    archive_offset = member_start + DELAY_VALUE_OFFSET
    rom_offset = old_start + archive_offset
    changed = facade._changed_offsets(before, after)
    if changed != [rom_offset]:
        raise ValueError(f'DynamicPunch changed ROM offsets {changed[:12]}, expected {[rom_offset]}')
    if receipt.get('archive_offset') != archive_offset or receipt.get('rom_offset') != rom_offset:
        raise ValueError('DynamicPunch changed offset differs from receipt')
    if receipt.get('archive_data_offset') != old_data or receipt.get('member') != MEMBER_INDEX:
        raise ValueError('DynamicPunch NARC identity differs from receipt')
    if (receipt.get('archive_sha256_before') != ARCHIVE_BEFORE_SHA256
            or receipt.get('archive_sha256_after') != ARCHIVE_AFTER_SHA256
            or receipt.get('member_sha256_before') != MEMBER_BEFORE_SHA256
            or receipt.get('member_sha256_after') != MEMBER_AFTER_SHA256
            or receipt.get('delay_before') != RETAIL_DELAY
            or receipt.get('delay_after') != FIXED_DELAY):
        raise ValueError('DynamicPunch receipt timing or hash pins differ')

    return {
        'rom_length': len(after),
        'changed_rom_bytes': len(changed),
        'rom_offset': rom_offset,
        'nitrofs_files_unchanged': len(old_rom.files) - 1,
        'archive_members_unchanged': MEMBER_COUNT - 1,
        'delay_before': retail.delay,
        'delay_after': fixed.delay,
        'second_start_tick_before': retail.schedule.second_start_tick,
        'second_start_tick_after': fixed.schedule.second_start_tick,
        'captured_base_x_before': retail.schedule.captured_base_x,
        'captured_base_x_after': fixed.schedule.captured_base_x,
        'final_x_before': retail.schedule.final_x,
        'final_x_after': fixed.schedule.final_x,
        'facade_member_preserved': True,
    }


def changed_regions(data):
    """Return the stable one-byte span on either cold V4 or Facade output."""
    data = bytes(data)
    _rom, _file_id, start, _end, archive = _rom_archive(data)
    digest = _sha256(archive)
    if digest not in (RETAIL_ARCHIVE_SHA256, ARCHIVE_BEFORE_SHA256):
        raise ValueError('DynamicPunch regions require retail or Facade archive preimage')
    _data, spans = facade._narc_layout(archive)
    if len(spans) != MEMBER_COUNT:
        raise ValueError(f'DynamicPunch archive needs {MEMBER_COUNT} members')
    member_start, member_end = spans[MEMBER_INDEX]
    if member_end - member_start != MEMBER_SIZE:
        raise ValueError('DynamicPunch member size differs')
    files = ndspy.narc.NARC(archive).files
    if _sha256(bytes(files[MEMBER_INDEX])) != MEMBER_BEFORE_SHA256:
        raise ValueError('DynamicPunch member preimage differs')
    expected_facade = (facade.MEMBER_BEFORE_SHA256 if digest == RETAIL_ARCHIVE_SHA256
                       else FACADE_MEMBER_AFTER_SHA256)
    if _sha256(bytes(files[FACADE_MEMBER_INDEX])) != expected_facade:
        raise ValueError('DynamicPunch Facade region predecessor differs')
    offset = start + member_start + DELAY_VALUE_OFFSET
    return ((offset, offset + 1),)
