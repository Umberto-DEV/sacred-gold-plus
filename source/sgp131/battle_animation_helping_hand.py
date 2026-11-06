"""HG-F20-HH Helping Hand battle-animation scheduling fix.

Retail places ``Delay 1`` immediately after a two-iteration loop.  The second
shake is therefore launched seven ticks after the first and records the first
task's transient X=-1 as its own base.  Moving the existing Delay into the loop
spaces the launches nine ticks apart and preserves X=0.

Facade and DynamicPunch own earlier bytes in the same NARC.  The production
writer accepts only their exact combined postimage; region declaration also
recognises the cold V4 archive because chain replay starts from that image.
"""
from dataclasses import dataclass
import hashlib
import struct

import ndspy.narc

from . import battle_animation_dynamicpunch as dynamicpunch
from . import battle_animation_facade as facade


MEMBER_SIZE = 428
MEMBER_COUNT = 501
MEMBER_INDEX = 270
FACADE_MEMBER_INDEX = facade.MEMBER_INDEX
DYNAMICPUNCH_MEMBER_INDEX = dynamicpunch.MEMBER_INDEX
ARCHIVE = facade.ARCHIVE
FILE_ID = facade.FILE_ID
LANGUAGES = facade.LANGUAGES
HEADER_BYTES = facade.HEADER_BYTES

RETAIL_ARCHIVE_SHA256 = facade.ARCHIVE_BEFORE_SHA256
ARCHIVE_BEFORE_SHA256 = dynamicpunch.ARCHIVE_AFTER_SHA256
ARCHIVE_AFTER_SHA256 = '476aaa7699161d395478fd4f7475fdaeebae52a27ba342d611cebb13875ff6ab'
MEMBER_BEFORE_SHA256 = 'd37bcb64e72d860522cb2c037d0ab037414af9543616d76b1708bbef66adc942'
MEMBER_AFTER_SHA256 = 'f824c040cbc13737c730d4b984493d5bc02758e6e7887a5399267546aea8adc2'
FACADE_MEMBER_AFTER_SHA256 = facade.MEMBER_AFTER_SHA256
DYNAMICPUNCH_MEMBER_AFTER_SHA256 = dynamicpunch.MEMBER_AFTER_SHA256

BEGIN_LOOP_OFFSET = 0x09C
LOOP_MOVE_RIGHT_OFFSET = 0x0A4
LOOP_SHAKE_OFFSET = 0x0BC
LOOP_DELAY3_OFFSET = 0x0DC
LOOP_MOVE_LEFT_OFFSET = 0x0E4
LOOP_DELAY2_OFFSET = 0x0FC
LOOP_SOUND_OFFSET = 0x104
LOOP_BOUNDARY_OFFSET = 0x110
POST_MOVE_RIGHT_OFFSET = 0x11C
POST_SHAKE_OFFSET = 0x134
POST_DELAY3_OFFSET = 0x154
POST_MOVE_LEFT_OFFSET = 0x15C
POST_DELAY1_OFFSET = 0x174
POST_FADE_OFFSET = 0x17C
WAIT_TASKS_OFFSET = 0x19C
CLEANUP_OFFSET = 0x1A0
RETAIL_BOUNDARY = (3, 0, 1)  # EndLoop; Delay 1
FIXED_BOUNDARY = (0, 1, 3)   # Delay 1; EndLoop


@dataclass(frozen=True)
class Schedule:
    shake_offsets: tuple
    shake_start_ticks: tuple
    captured_base_x: tuple
    final_x: int


@dataclass(frozen=True)
class MemberTiming:
    delay_inside_loop: bool
    schedule: Schedule


def evaluate_helping_hand_schedule(delay_inside_loop):
    """Execute loop/Delay timing and the overlapping X writes."""
    if type(delay_inside_loop) is not bool:
        raise ValueError('Helping Hand loop placement must be boolean')
    shake = dynamicpunch.evaluate_shake_offsets(1, 1, 2)
    loop_interval = (3 + 1) + (2 + 1) + ((1 + 1) if delay_inside_loop else 0)
    outside_delay = 0 if delay_inside_loop else 1 + 1
    starts = (0, loop_interval, loop_interval * 2 + outside_delay)

    current = 0
    captured = []
    active = []
    last_tick = starts[-1] + len(shake) - 1
    for tick in range(last_tick + 1):
        if tick in starts:
            captured.append(current)
            active.append((tick, current))
        for start, base in active:
            index = tick - start
            if 0 <= index < len(shake):
                current = base + shake[index]
    return Schedule(shake, starts, tuple(captured), current)


def _expect_words(member, offset, expected, label):
    actual = struct.unpack_from('<%dI' % len(expected), member, offset)
    if actual != tuple(expected):
        raise ValueError(f'Helping Hand {label} command differs')


def read_member_timing(member):
    """Authenticate the complete loop and the following explicit shake."""
    member = bytes(member)
    if len(member) != MEMBER_SIZE:
        raise ValueError(f'Helping Hand member must be {MEMBER_SIZE} bytes')
    _expect_words(member, BEGIN_LOOP_OFFSET, (2, 2), 'BeginLoop')
    _expect_words(member, LOOP_MOVE_RIGHT_OFFSET,
                  (0x2D, 0x34, 3, 2, 12, 0x102), 'loop move right')
    _expect_words(member, LOOP_SHAKE_OFFSET,
                  (0x2D, 0x24, 5, 1, 0, 1, 2, 0x104), 'loop shake')
    _expect_words(member, LOOP_DELAY3_OFFSET, (0, 3), 'loop Delay 3')
    _expect_words(member, LOOP_MOVE_LEFT_OFFSET,
                  (0x2D, 0x34, 3, 2, 0xFFFFFFF4, 0x102), 'loop move left')
    _expect_words(member, LOOP_DELAY2_OFFSET, (0, 2), 'loop Delay 2')
    _expect_words(member, LOOP_SOUND_OFFSET, (0x16, 0x7F3, 0), 'loop sound')
    boundary = struct.unpack_from('<III', member, LOOP_BOUNDARY_OFFSET)
    if boundary not in (RETAIL_BOUNDARY, FIXED_BOUNDARY):
        raise ValueError('Helping Hand loop boundary differs')
    _expect_words(member, POST_MOVE_RIGHT_OFFSET,
                  (0x2D, 0x34, 3, 2, 12, 0x102), 'post-loop move right')
    _expect_words(member, POST_SHAKE_OFFSET,
                  (0x2D, 0x24, 5, 1, 0, 1, 2, 0x104), 'post-loop shake')
    _expect_words(member, POST_DELAY3_OFFSET, (0, 3), 'post-loop Delay 3')
    _expect_words(member, POST_MOVE_LEFT_OFFSET,
                  (0x2D, 0x34, 3, 2, 0xFFFFFFF4, 0x102), 'post-loop move left')
    _expect_words(member, POST_DELAY1_OFFSET, (0, 1), 'post-loop Delay 1')
    _expect_words(member, POST_FADE_OFFSET,
                  (0x2D, 0x22, 5, 4, 0, 2, 0x3EB, 8), 'post-loop fade')
    _expect_words(member, WAIT_TASKS_OFFSET, (1,), 'task wait')
    _expect_words(member, CLEANUP_OFFSET, (0x50, 0, 4), 'cleanup')
    inside = boundary == FIXED_BOUNDARY
    return MemberTiming(inside, evaluate_helping_hand_schedule(inside))


def patch_exact_member(member, expected_sha256):
    """Move the exact existing Delay into the loop without changing length."""
    member = bytes(member)
    timing = read_member_timing(member)
    actual = hashlib.sha256(member).hexdigest()
    if actual != expected_sha256:
        if timing.delay_inside_loop:
            raise ValueError('Helping Hand member is already patched')
        raise ValueError(f'foreign Helping Hand member sha256 {actual}')
    if timing.delay_inside_loop:
        raise ValueError('Helping Hand member is already patched')
    out = bytearray(member)
    struct.pack_into('<III', out, LOOP_BOUNDARY_OFFSET, *FIXED_BOUNDARY)
    out = bytes(out)
    fixed = read_member_timing(out)
    if fixed.schedule.captured_base_x != (0, 0, 0) or fixed.schedule.final_x != 0:
        raise ValueError('Helping Hand timing fix failed its position invariant')
    return out


def narc_data_offset(raw):
    return facade._narc_layout(raw)[0]


def patch_exact_archive(raw, expected_member_sha256):
    """Patch member 270 in place without rebuilding the NARC."""
    raw = bytes(raw)
    _data, spans = facade._narc_layout(raw)
    if len(spans) != MEMBER_COUNT:
        raise ValueError(f'Helping Hand archive needs {MEMBER_COUNT} members')
    start, end = spans[MEMBER_INDEX]
    if end - start != MEMBER_SIZE:
        raise ValueError(f'Helping Hand member {MEMBER_INDEX} must be {MEMBER_SIZE} bytes')
    patched_member = patch_exact_member(raw[start:end], expected_member_sha256)
    out = bytearray(raw)
    out[start:end] = patched_member
    return bytes(out)


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def patch_archive(raw):
    """Patch only the exact Facade+DynamicPunch archive successor."""
    raw = bytes(raw)
    digest = _sha256(raw)
    if digest == ARCHIVE_AFTER_SHA256:
        raise ValueError('Helping Hand archive is already patched')
    if digest in (RETAIL_ARCHIVE_SHA256, facade.ARCHIVE_AFTER_SHA256):
        raise ValueError('Helping Hand animation predecessor missing')
    if digest != ARCHIVE_BEFORE_SHA256:
        raise ValueError(f'foreign Helping Hand archive sha256 {digest}')
    files = ndspy.narc.NARC(raw).files
    if _sha256(bytes(files[FACADE_MEMBER_INDEX])) != FACADE_MEMBER_AFTER_SHA256:
        raise ValueError('Helping Hand Facade member preimage differs')
    if _sha256(bytes(files[DYNAMICPUNCH_MEMBER_INDEX])) != DYNAMICPUNCH_MEMBER_AFTER_SHA256:
        raise ValueError('Helping Hand DynamicPunch member preimage differs')
    out = patch_exact_archive(raw, MEMBER_BEFORE_SHA256)
    if _sha256(out) != ARCHIVE_AFTER_SHA256:
        raise ValueError('Helping Hand archive postimage differs')
    return out


def _rom_archive(data):
    return facade._rom_archive(data)


def apply(data, language):
    """Apply HG-F20-HH in memory after Facade and DynamicPunch."""
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
    archive_offsets = [member_start + offset for offset in
                       (LOOP_BOUNDARY_OFFSET, LOOP_BOUNDARY_OFFSET + 4,
                        LOOP_BOUNDARY_OFFSET + 8)]
    rom_offsets = [start + offset for offset in archive_offsets]
    receipt = {
        'schema': 1,
        'stage': 'battle-animation-helping-hand',
        'language': language,
        'archive': ARCHIVE,
        'file_id': file_id,
        'rom_slot': [start, end],
        'archive_data_offset': data_offset,
        'member': MEMBER_INDEX,
        'archive_offsets': archive_offsets,
        'rom_offsets': rom_offsets,
        'input_sha256': _sha256(data),
        'output_sha256': _sha256(out),
        'archive_sha256_before': ARCHIVE_BEFORE_SHA256,
        'archive_sha256_after': ARCHIVE_AFTER_SHA256,
        'member_sha256_before': MEMBER_BEFORE_SHA256,
        'member_sha256_after': MEMBER_AFTER_SHA256,
        'boundary_before': list(RETAIL_BOUNDARY),
        'boundary_after': list(FIXED_BOUNDARY),
    }
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    """Re-read ROM, NARC, loop commands and schedule independently."""
    before, after = bytes(before), bytes(after)
    if receipt.get('schema') != 1 or receipt.get('stage') != 'battle-animation-helping-hand':
        raise ValueError('Helping Hand receipt schema or stage differs')
    if receipt.get('language') not in LANGUAGES:
        raise ValueError('Helping Hand receipt language differs')
    if _sha256(before) != receipt.get('input_sha256'):
        raise ValueError('Helping Hand receipt input identity differs')
    if _sha256(after) != receipt.get('output_sha256'):
        raise ValueError('Helping Hand receipt output identity differs')
    if len(before) != len(after) or before[:HEADER_BYTES] != after[:HEADER_BYTES]:
        raise ValueError('Helping Hand changed ROM length or header')

    old_rom, old_id, old_start, old_end, old_archive = _rom_archive(before)
    new_rom, new_id, new_start, new_end, new_archive = _rom_archive(after)
    if (old_id, old_start, old_end) != (new_id, new_start, new_end):
        raise ValueError('Helping Hand archive FAT identity changed')
    if receipt.get('file_id') != old_id or receipt.get('rom_slot') != [old_start, old_end]:
        raise ValueError('Helping Hand archive FAT identity differs from receipt')
    if len(old_rom.files) != len(new_rom.files):
        raise ValueError('Helping Hand NitroFS file count changed')
    for index, (old_file, new_file) in enumerate(zip(old_rom.files, new_rom.files)):
        if index != old_id and old_file != new_file:
            raise ValueError(f'Helping Hand changed unrelated NitroFS file {index}')
    if (_sha256(old_archive) != ARCHIVE_BEFORE_SHA256
            or _sha256(new_archive) != ARCHIVE_AFTER_SHA256):
        raise ValueError('Helping Hand archive preimage or postimage differs')

    old_data, old_spans = facade._narc_layout(old_archive)
    new_data, new_spans = facade._narc_layout(new_archive)
    if old_data != new_data or old_spans != new_spans or len(old_spans) != MEMBER_COUNT:
        raise ValueError('Helping Hand NARC geometry changed')
    old_files = ndspy.narc.NARC(old_archive).files
    new_files = ndspy.narc.NARC(new_archive).files
    for index, (old_member, new_member) in enumerate(zip(old_files, new_files)):
        if index != MEMBER_INDEX and old_member != new_member:
            raise ValueError(f'Helping Hand changed unrelated NARC member {index}')
    old_member = bytes(old_files[MEMBER_INDEX])
    new_member = bytes(new_files[MEMBER_INDEX])
    if (_sha256(old_member) != MEMBER_BEFORE_SHA256
            or _sha256(new_member) != MEMBER_AFTER_SHA256):
        raise ValueError('Helping Hand member preimage or postimage differs')
    for index, digest in ((FACADE_MEMBER_INDEX, FACADE_MEMBER_AFTER_SHA256),
                          (DYNAMICPUNCH_MEMBER_INDEX, DYNAMICPUNCH_MEMBER_AFTER_SHA256)):
        if (_sha256(bytes(old_files[index])) != digest
                or bytes(old_files[index]) != bytes(new_files[index])):
            raise ValueError('Helping Hand changed or lost an animation predecessor')

    retail = read_member_timing(old_member)
    fixed = read_member_timing(new_member)
    if retail.delay_inside_loop or retail.schedule.final_x != -1:
        raise ValueError('Helping Hand retail drift reproduction differs')
    if not fixed.delay_inside_loop or fixed.schedule.final_x != 0:
        raise ValueError('Helping Hand fixed position invariant differs')

    member_start = old_spans[MEMBER_INDEX][0]
    archive_offsets = [member_start + offset for offset in
                       (LOOP_BOUNDARY_OFFSET, LOOP_BOUNDARY_OFFSET + 4,
                        LOOP_BOUNDARY_OFFSET + 8)]
    rom_offsets = [old_start + offset for offset in archive_offsets]
    changed = facade._changed_offsets(before, after)
    if changed != rom_offsets:
        raise ValueError(f'Helping Hand changed ROM offsets {changed[:12]}, expected {rom_offsets}')
    if receipt.get('archive_offsets') != archive_offsets or receipt.get('rom_offsets') != rom_offsets:
        raise ValueError('Helping Hand changed offsets differ from receipt')
    if receipt.get('archive_data_offset') != old_data or receipt.get('member') != MEMBER_INDEX:
        raise ValueError('Helping Hand NARC identity differs from receipt')
    if (receipt.get('archive_sha256_before') != ARCHIVE_BEFORE_SHA256
            or receipt.get('archive_sha256_after') != ARCHIVE_AFTER_SHA256
            or receipt.get('member_sha256_before') != MEMBER_BEFORE_SHA256
            or receipt.get('member_sha256_after') != MEMBER_AFTER_SHA256
            or receipt.get('boundary_before') != list(RETAIL_BOUNDARY)
            or receipt.get('boundary_after') != list(FIXED_BOUNDARY)):
        raise ValueError('Helping Hand receipt timing or hash pins differ')

    return {
        'rom_length': len(after),
        'changed_rom_bytes': len(changed),
        'rom_offsets': rom_offsets,
        'nitrofs_files_unchanged': len(old_rom.files) - 1,
        'archive_members_unchanged': MEMBER_COUNT - 1,
        'shake_start_ticks_before': list(retail.schedule.shake_start_ticks),
        'shake_start_ticks_after': list(fixed.schedule.shake_start_ticks),
        'captured_base_x_before': list(retail.schedule.captured_base_x),
        'captured_base_x_after': list(fixed.schedule.captured_base_x),
        'final_x_before': retail.schedule.final_x,
        'final_x_after': fixed.schedule.final_x,
        'facade_member_preserved': True,
        'dynamicpunch_member_preserved': True,
    }


def changed_regions(data):
    """Return the three stable one-byte spans on cold V4 or exact predecessor."""
    data = bytes(data)
    _rom, _file_id, start, _end, archive = _rom_archive(data)
    digest = _sha256(archive)
    if digest not in (RETAIL_ARCHIVE_SHA256, ARCHIVE_BEFORE_SHA256):
        raise ValueError('Helping Hand regions require retail or combined predecessor')
    _data, spans = facade._narc_layout(archive)
    if len(spans) != MEMBER_COUNT:
        raise ValueError(f'Helping Hand archive needs {MEMBER_COUNT} members')
    member_start, member_end = spans[MEMBER_INDEX]
    if member_end - member_start != MEMBER_SIZE:
        raise ValueError('Helping Hand member size differs')
    files = ndspy.narc.NARC(archive).files
    if _sha256(bytes(files[MEMBER_INDEX])) != MEMBER_BEFORE_SHA256:
        raise ValueError('Helping Hand member preimage differs')
    expected_facade = (facade.MEMBER_BEFORE_SHA256 if digest == RETAIL_ARCHIVE_SHA256
                       else FACADE_MEMBER_AFTER_SHA256)
    expected_dynamic = (dynamicpunch.MEMBER_BEFORE_SHA256 if digest == RETAIL_ARCHIVE_SHA256
                        else DYNAMICPUNCH_MEMBER_AFTER_SHA256)
    if _sha256(bytes(files[FACADE_MEMBER_INDEX])) != expected_facade:
        raise ValueError('Helping Hand Facade region predecessor differs')
    if _sha256(bytes(files[DYNAMICPUNCH_MEMBER_INDEX])) != expected_dynamic:
        raise ValueError('Helping Hand DynamicPunch region predecessor differs')
    return tuple((start + member_start + offset, start + member_start + offset + 1)
                 for offset in (LOOP_BOUNDARY_OFFSET, LOOP_BOUNDARY_OFFSET + 4,
                                LOOP_BOUNDARY_OFFSET + 8))
