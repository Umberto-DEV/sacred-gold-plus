"""HG-F17 Facade battle-animation timing fix.

Facade starts six ten-frame scale/restore tasks only eight frames apart in the
retail HGSS member.  The producer below will preserve each task and move the
five inter-task delays, plus the matching looped-sound interval, from 8 to 10.
ROM and NARC application is added only behind exact preimage checks.
"""
from dataclasses import dataclass
import hashlib
import struct

import ndspy.narc
import ndspy.rom


MEMBER_SIZE = 744
MEMBER_COUNT = 501
MEMBER_INDEX = 263
ARCHIVE = 'a/0/1/0'
FILE_ID = 139
ARCHIVE_BEFORE_SHA256 = '8c70a493396554ac109c2969d5ff8c71eef27f9e62431177cee191b31d2f9729'
ARCHIVE_AFTER_SHA256 = '8d9e854012576553cd17848971b9f192946ebe027febb586d9d72e0a006d35a3'
MEMBER_BEFORE_SHA256 = '1f9cd6b0880ff6551e112d7cf65858b2957453bf28825984334863af71feebbd'
MEMBER_AFTER_SHA256 = 'a8963c0292c3496bdce0ebe3afd5a9ee7d9ad81d3fc55d543de8b7b897f8b8bd'
LANGUAGES = ('EN', 'IT')
HEADER_BYTES = 0x200
FAT_FIELD = 0x48
SOUND_COMMAND_OFFSET = 0xD8
SOUND_INTERVAL_OFFSET = 0xE4
SCALE_FLAGS_OFFSETS = (0x138, 0x16C, 0x1C4, 0x1F8, 0x250, 0x284)
DELAY_VALUE_OFFSETS = (0x140, 0x174, 0x1CC, 0x200, 0x258)
RETAIL_INTERVAL = 8
FIXED_INTERVAL = 10


@dataclass(frozen=True)
class Schedule:
    starts: tuple
    ends: tuple
    overlaps: tuple
    sound_interval: int


@dataclass(frozen=True)
class MemberTiming:
    durations: tuple
    inter_task_delays: tuple
    sound_interval: int
    schedule: Schedule


def evaluate_schedule(durations, inter_task_delays, sound_interval):
    """Return the frame schedule for sequentially launched asynchronous tasks."""
    durations = tuple(durations)
    delays = tuple(inter_task_delays)
    if not durations or len(delays) != len(durations) - 1:
        raise ValueError('Facade needs one fewer inter-task delay than tasks')
    if any(type(value) is not int or value <= 0 for value in durations + delays):
        raise ValueError('Facade durations and delays must be positive integers')
    if type(sound_interval) is not int or sound_interval <= 0:
        raise ValueError('Facade sound interval must be a positive integer')

    starts = [0]
    for delay in delays:
        starts.append(starts[-1] + delay)
    ends = [start + duration for start, duration in zip(starts, durations)]
    overlaps = tuple((index, index + 1) for index in range(len(starts) - 1)
                     if starts[index + 1] < ends[index])
    return Schedule(tuple(starts), tuple(ends), overlaps, sound_interval)


def read_member_timing(member):
    """Read the six Facade scale tasks and their launch/audio intervals."""
    member = bytes(member)
    if len(member) != MEMBER_SIZE:
        raise ValueError(f'Facade member must be {MEMBER_SIZE} bytes')
    sound = struct.unpack_from('<IIIII', member, SOUND_COMMAND_OFFSET)
    if sound[:3] != (0x19, 0x7EA, 0xFFFFFF8B) or sound[4] != 6:
        raise ValueError('Facade sound command preimage differs')

    durations = []
    for offset in SCALE_FLAGS_OFFSETS:
        packed = struct.unpack_from('<I', member, offset)[0]
        scale_frames, restore_frames = packed & 0xFFFF, packed >> 16
        if (scale_frames, restore_frames) != (5, 5):
            raise ValueError('Facade scale/restore task duration differs')
        durations.append(scale_frames + restore_frames)

    delays = []
    for offset in DELAY_VALUE_OFFSETS:
        if struct.unpack_from('<I', member, offset - 4)[0] != 0:
            raise ValueError('Facade Delay command preimage differs')
        delays.append(struct.unpack_from('<I', member, offset)[0])
    if len(set(delays)) != 1 or delays[0] not in (RETAIL_INTERVAL, FIXED_INTERVAL):
        raise ValueError('Facade delay values are neither the retail nor fixed schedule')
    if sound[3] != delays[0]:
        raise ValueError('Facade sound interval differs from the task schedule')

    schedule = evaluate_schedule(tuple(durations), tuple(delays), sound[3])
    return MemberTiming(tuple(durations), tuple(delays), sound[3], schedule)


def patch_exact_member(member, expected_sha256):
    """Apply the root-cause timing fix to one exact Facade member."""
    member = bytes(member)
    timing = read_member_timing(member)
    actual = hashlib.sha256(member).hexdigest()
    if actual != expected_sha256:
        if timing.inter_task_delays == (FIXED_INTERVAL,) * 5:
            raise ValueError('Facade member is already patched')
        raise ValueError(f'foreign Facade member sha256 {actual}')
    if timing.inter_task_delays != (RETAIL_INTERVAL,) * 5:
        raise ValueError('Facade member is already patched')

    out = bytearray(member)
    for offset in (SOUND_INTERVAL_OFFSET,) + DELAY_VALUE_OFFSETS:
        struct.pack_into('<I', out, offset, FIXED_INTERVAL)
    out = bytes(out)
    fixed = read_member_timing(out)
    if fixed.durations != timing.durations or fixed.schedule.overlaps:
        raise ValueError('Facade timing fix failed its schedule invariant')
    return out


def _narc_layout(raw):
    """Return (member-data offset, member spans) for an exact, bounded NARC."""
    raw = bytes(raw)
    if len(raw) < 0x24 or raw[:4] != b'NARC' or raw[4:6] not in (b'\xfe\xff', b'\xff\xfe'):
        raise ValueError('Facade archive is not a NARC')
    declared, header_size, blocks = struct.unpack_from('<IHH', raw, 8)
    if declared != len(raw) or header_size != 0x10 or blocks != 3:
        raise ValueError('Facade NARC header or length differs')
    magic, btaf_size, count = struct.unpack_from('<4sII', raw, 0x10)
    if magic != b'BTAF' or btaf_size != 12 + count * 8:
        raise ValueError('Facade NARC allocation table differs')
    if 0x10 + btaf_size + 8 > len(raw):
        raise ValueError('Facade NARC allocation table is truncated')
    btnf = 0x10 + btaf_size
    if raw[btnf:btnf + 4] != b'BTNF':
        raise ValueError('Facade NARC name table is absent')
    btnf_size = struct.unpack_from('<I', raw, btnf + 4)[0]
    gmif = btnf + btnf_size
    if gmif + 8 > len(raw) or raw[gmif:gmif + 4] != b'GMIF':
        raise ValueError('Facade NARC member data is absent')
    gmif_size = struct.unpack_from('<I', raw, gmif + 4)[0]
    if gmif + gmif_size != len(raw) or gmif_size < 8:
        raise ValueError('Facade NARC member-data length differs')
    data = gmif + 8
    payload_size = gmif_size - 8
    spans = []
    previous_end = 0
    for index in range(count):
        start, end = struct.unpack_from('<II', raw, 0x1C + index * 8)
        if not previous_end <= start <= end <= payload_size:
            raise ValueError(f'Facade NARC member {index} bounds differ')
        spans.append((data + start, data + end))
        previous_end = end
    return data, tuple(spans)


def narc_data_offset(raw):
    return _narc_layout(raw)[0]


def patch_exact_archive(raw, expected_member_sha256):
    """Patch member 263 in place; never rebuild or normalize the NARC."""
    raw = bytes(raw)
    _data, spans = _narc_layout(raw)
    if len(spans) != MEMBER_COUNT:
        raise ValueError(f'Facade archive needs {MEMBER_COUNT} members')
    start, end = spans[MEMBER_INDEX]
    if end - start != MEMBER_SIZE:
        raise ValueError(f'Facade member {MEMBER_INDEX} must be {MEMBER_SIZE} bytes')
    patched_member = patch_exact_member(raw[start:end], expected_member_sha256)
    out = bytearray(raw)
    out[start:end] = patched_member
    return bytes(out)


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _fat_slot(data, file_id):
    fat_offset, fat_length = struct.unpack_from('<II', data, FAT_FIELD)
    if file_id < 0 or file_id * 8 + 8 > fat_length:
        raise ValueError(f'Facade file id {file_id} is outside the ROM FAT')
    start, end = struct.unpack_from('<II', data, fat_offset + file_id * 8)
    if not 0 <= start <= end <= len(data):
        raise ValueError('Facade archive FAT slot is outside the ROM')
    return start, end


def _changed_offsets(before, after, chunk=1 << 20):
    if len(before) != len(after):
        raise ValueError('Facade images differ in length')
    changed = []
    for base in range(0, len(before), chunk):
        end = min(base + chunk, len(before))
        if before[base:end] == after[base:end]:
            continue
        changed.extend(index for index in range(base, end)
                       if before[index] != after[index])
    return changed


def patch_archive(raw):
    """Patch only the authenticated retail archive."""
    raw = bytes(raw)
    digest = _sha256(raw)
    if digest == ARCHIVE_AFTER_SHA256:
        raise ValueError('Facade archive is already patched')
    if digest != ARCHIVE_BEFORE_SHA256:
        raise ValueError(f'foreign Facade archive sha256 {digest}')
    out = patch_exact_archive(raw, MEMBER_BEFORE_SHA256)
    if _sha256(out) != ARCHIVE_AFTER_SHA256:
        raise ValueError('Facade archive postimage differs')
    return out


def _rom_archive(data):
    rom = ndspy.rom.NintendoDSRom(data)
    file_id = rom.filenames.idOf(ARCHIVE)
    if file_id != FILE_ID:
        raise ValueError(f'Facade archive file id is {file_id}, expected {FILE_ID}')
    start, end = _fat_slot(data, file_id)
    archive = bytes(rom.files[file_id])
    if archive != data[start:end]:
        raise ValueError('Facade parsed archive differs from its FAT slot')
    return rom, file_id, start, end, archive


def apply(data, language):
    """Apply HG-F17 in memory and return the image plus an exact receipt."""
    if language not in LANGUAGES:
        raise ValueError(f'unknown language {language!r}: expected EN or IT')
    data = bytes(data)
    _rom, file_id, start, end, archive = _rom_archive(data)
    patched_archive = patch_archive(archive)
    out = bytearray(data)
    out[start:end] = patched_archive
    out = bytes(out)

    data_offset, spans = _narc_layout(archive)
    member_start, _member_end = spans[MEMBER_INDEX]
    member_offsets = tuple(member_start + offset for offset in
                           (SOUND_INTERVAL_OFFSET,) + DELAY_VALUE_OFFSETS)
    rom_offsets = tuple(start + offset for offset in member_offsets)
    receipt = {
        'schema': 1,
        'stage': 'battle-animation-facade',
        'language': language,
        'archive': ARCHIVE,
        'file_id': file_id,
        'rom_slot': [start, end],
        'archive_data_offset': data_offset,
        'member': MEMBER_INDEX,
        'archive_offsets': list(member_offsets),
        'rom_offsets': list(rom_offsets),
        'input_sha256': _sha256(data),
        'output_sha256': _sha256(out),
        'archive_sha256_before': ARCHIVE_BEFORE_SHA256,
        'archive_sha256_after': ARCHIVE_AFTER_SHA256,
        'member_sha256_before': MEMBER_BEFORE_SHA256,
        'member_sha256_after': MEMBER_AFTER_SHA256,
        'interval_before': RETAIL_INTERVAL,
        'interval_after': FIXED_INTERVAL,
    }
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    """Independently re-read the ROM, NARC member and schedule invariant."""
    before, after = bytes(before), bytes(after)
    if receipt.get('schema') != 1 or receipt.get('stage') != 'battle-animation-facade':
        raise ValueError('Facade receipt schema or stage differs')
    if receipt.get('language') not in LANGUAGES:
        raise ValueError('Facade receipt language differs')
    if _sha256(before) != receipt.get('input_sha256'):
        raise ValueError('Facade receipt input identity differs')
    if _sha256(after) != receipt.get('output_sha256'):
        raise ValueError('Facade receipt output identity differs')
    if len(before) != len(after) or before[:HEADER_BYTES] != after[:HEADER_BYTES]:
        raise ValueError('Facade changed ROM length or header')

    old_rom, old_id, old_start, old_end, old_archive = _rom_archive(before)
    new_rom, new_id, new_start, new_end, new_archive = _rom_archive(after)
    if (old_id, old_start, old_end) != (new_id, new_start, new_end):
        raise ValueError('Facade archive FAT identity changed')
    if receipt.get('file_id') != old_id or receipt.get('rom_slot') != [old_start, old_end]:
        raise ValueError('Facade archive FAT identity differs from receipt')
    if len(old_rom.files) != len(new_rom.files):
        raise ValueError('Facade NitroFS file count changed')
    for index, (old_file, new_file) in enumerate(zip(old_rom.files, new_rom.files)):
        if index != old_id and old_file != new_file:
            raise ValueError(f'Facade changed unrelated NitroFS file {index}')
    if (_sha256(old_archive) != ARCHIVE_BEFORE_SHA256
            or _sha256(new_archive) != ARCHIVE_AFTER_SHA256):
        raise ValueError('Facade archive preimage or postimage differs')

    old_data, old_spans = _narc_layout(old_archive)
    new_data, new_spans = _narc_layout(new_archive)
    if old_data != new_data or old_spans != new_spans or len(old_spans) != MEMBER_COUNT:
        raise ValueError('Facade NARC geometry changed')
    old_files = ndspy.narc.NARC(old_archive).files
    new_files = ndspy.narc.NARC(new_archive).files
    for index, (old_member, new_member) in enumerate(zip(old_files, new_files)):
        if index != MEMBER_INDEX and old_member != new_member:
            raise ValueError(f'Facade changed unrelated NARC member {index}')
    old_member = bytes(old_files[MEMBER_INDEX])
    new_member = bytes(new_files[MEMBER_INDEX])
    if _sha256(old_member) != MEMBER_BEFORE_SHA256 or _sha256(new_member) != MEMBER_AFTER_SHA256:
        raise ValueError('Facade member preimage or postimage differs')
    retail = read_member_timing(old_member)
    fixed = read_member_timing(new_member)
    if retail.schedule.overlaps != ((0, 1), (1, 2), (2, 3), (3, 4), (4, 5)):
        raise ValueError('Facade retail overlap reproduction differs')
    if fixed.schedule.overlaps or fixed.durations != retail.durations:
        raise ValueError('Facade fixed schedule invariant differs')

    member_start = old_spans[MEMBER_INDEX][0]
    archive_offsets = [member_start + offset for offset in
                       (SOUND_INTERVAL_OFFSET,) + DELAY_VALUE_OFFSETS]
    rom_offsets = [old_start + offset for offset in archive_offsets]
    changed = _changed_offsets(before, after)
    if changed != rom_offsets:
        raise ValueError(f'Facade changed ROM offsets {changed[:12]}, expected {rom_offsets}')
    if receipt.get('archive_offsets') != archive_offsets or receipt.get('rom_offsets') != rom_offsets:
        raise ValueError('Facade changed offsets differ from receipt')
    if receipt.get('archive_data_offset') != old_data or receipt.get('member') != MEMBER_INDEX:
        raise ValueError('Facade NARC identity differs from receipt')
    if (receipt.get('archive_sha256_before') != ARCHIVE_BEFORE_SHA256
            or receipt.get('archive_sha256_after') != ARCHIVE_AFTER_SHA256
            or receipt.get('member_sha256_before') != MEMBER_BEFORE_SHA256
            or receipt.get('member_sha256_after') != MEMBER_AFTER_SHA256
            or receipt.get('interval_before') != RETAIL_INTERVAL
            or receipt.get('interval_after') != FIXED_INTERVAL):
        raise ValueError('Facade receipt timing or hash pins differ')

    return {
        'rom_length': len(after),
        'changed_rom_bytes': len(changed),
        'rom_offsets': rom_offsets,
        'nitrofs_files_unchanged': len(old_rom.files) - 1,
        'archive_members_unchanged': MEMBER_COUNT - 1,
        'task_durations_before': list(retail.durations),
        'task_durations_after': list(fixed.durations),
        'overlaps_before': len(retail.schedule.overlaps),
        'overlaps_after': len(fixed.schedule.overlaps),
        'sound_interval_before': retail.sound_interval,
        'sound_interval_after': fixed.sound_interval,
    }


def changed_regions(data):
    """Return the six exact one-byte ROM spans owned by this stage."""
    data = bytes(data)
    _rom, _file_id, start, _end, archive = _rom_archive(data)
    if _sha256(archive) != ARCHIVE_BEFORE_SHA256:
        raise ValueError('Facade regions require the retail archive preimage')
    _data, spans = _narc_layout(archive)
    member_start = spans[MEMBER_INDEX][0]
    return tuple((start + member_start + offset, start + member_start + offset + 1)
                 for offset in (SOUND_INTERVAL_OFFSET,) + DELAY_VALUE_OFFSETS)
