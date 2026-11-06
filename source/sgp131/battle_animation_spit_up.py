"""HG-F20-SU: restore Spit Up's exact residual horizontal shake.

The HGSS task applies ten shake samples whose sum is +2, then restores scale
and Y but not X.  This stage changes only the task's existing 34-byte cleanup:
it retains the three original resets and subtracts the deterministic residual
from the current X.  The compressed overlay slot and every container field stay
unchanged.  No save data or resident allocation is involved.
"""
from dataclasses import dataclass
import hashlib
import struct

import ndspy.narc
import ndspy.rom


LANGUAGES = ('EN', 'IT')
OVERLAY_ID = 7
FILE_ID = 7
OVERLAY_BASE = 0x0221BE20
OVERLAY_SIZE = 113312
OVERLAY_SHA256_BEFORE = '245d65b0a3aab0b753d0b45d3532ecb168e4d50d2dd4c3894821f1ccdbad0ad0'
OVERLAY_SHA256_AFTER = 'dd2f0f21549abbe9dfdda98feb1c90642259da3f3933629242c9e46cd7a8af74'
STREAM_SIZE = 78568
STREAM_SHA256_BEFORE = '862001c746e18cd80004e8165056e69a0d763257932b87153bd6c543562a499c'
STREAM_SHA256_AFTER = '3f183e0aa95ee14c3ba4527df6f915d96f117cc711b6879c9808a484164a1070'

TASK = 0x02224CB8
TASK_END = 0x02224E58
TASK_SHA256 = '3a0bbd997e40f736b1f0c6dcf33bc84909c448ae0bb526fad39c4b70d301c897'
WRAPPER = 0x02224E58
WRAPPER_END = 0x02224EF4
WRAPPER_SHA256 = 'a4d456caeeec18cd857e18d2fecddfa0cbaa6edc2db039b07db3af31496860e7'
FUNCTION_TABLE_ENTRY = 0x022365F4
TASK_LITERAL = 0x02224EF0

SCALE_INIT = 0x02222508
SCALE_UPDATE = 0x02222558
SHAKE_UPDATE = 0x022227D8
GROUND_OFFSET = 0x02222674
GET_SCRIPT_VAR = 0x0221C4A8
POKEPIC_SET_ATTR = 0x020087A4
POKEPIC_SET_ATTR_END = 0x02008A50
POKEPIC_SET_ATTR_SHA256 = '3d00f8486503229edf20fc584a734905cd217a3367e6207e760b48c2d24bf956'
POKEPIC_ADD_ATTR = 0x02008C2C
POKEPIC_ADD_ATTR_END = 0x02009062
POKEPIC_ADD_ATTR_SHA256 = 'fd5be4c550ffec07a61f8d6698d488528e6eb039ed30ecca7a5cab63cba4e761'

CLEANUP_ADDRESS = 0x02224E1A
CLEANUP_OFFSET = CLEANUP_ADDRESS - OVERLAY_BASE
CLEANUP_SIZE = 34
CLEANUP_BEFORE = bytes.fromhex(
    '0c210a1cf432e3f5c0fc0d210a1c2069f332e3f5bafc'
    '0222a25e20690121e3f5b4fc')
CLEANUP_AFTER = bytes.fromhex(
    '0c2101221202e3f5c0fc0d21e3f5bdfc01210222a25e'
    'e3f5b8fc00218a1ee3f5f8fe')
CLEANUP_SHA256_BEFORE = 'a3806b7535d0d18fcd917eefd0eda08df1164611f0fc22bf854524653a4f80d0'
CLEANUP_SHA256_AFTER = '11c5d22d6dd5e861fd3cb95bc98154af7cc4198cec73a24b57d9726e715e4473'
CLEANUP_DELTA = 2
LOGICAL_CHANGED_BYTES = 24
COMPRESSED_CHANGED_BYTES = 23365

ARCHIVE = 'a/0/1/0'
ARCHIVE_FILE_ID = 139
MEMBER_COUNT = 501
MEMBER_INDEX = 255
MEMBER_SIZE = 368
MEMBER_SHA256 = '28d4fb404caca847f694c33900fa57dda1ec2e4c521528fbd356ce9bb7966521'
SCRIPT_CALL_OFFSET = 0xC4
SCRIPT_CALL = (0x2D, 0x35, 5, 70, 120, 10, 5, 15)

SHAKE_DELTAS = (2, 0, -2, 0, 2, 0, -2, 0, 2, 0)
TRANSITIONS = ((10, 0, 1), (26, 1, 2), (32, 2, 3), (33, 3, 4))


@dataclass(frozen=True)
class RuntimeEvidence:
    initial_x: int
    cleanup_delta: int
    shake_deltas: tuple
    final_x: int
    ticks: int
    transitions: tuple


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def evaluate_runtime(initial_x, cleanup_delta):
    """Small independent oracle for the exact task schedule."""
    _need(type(initial_x) is int, 'Spit Up initial X')
    _need(type(cleanup_delta) is int and cleanup_delta >= 0,
          'Spit Up cleanup delta')
    return RuntimeEvidence(
        initial_x, cleanup_delta, SHAKE_DELTAS,
        initial_x + sum(SHAKE_DELTAS) - cleanup_delta,
        34, TRANSITIONS)


def cleanup_postimage(delta):
    """Return the reviewed cleanup or live subtract-one/three test mutants."""
    _need(type(delta) is int and delta in (1, 2, 3),
          'Spit Up cleanup delta must be 1, 2 or 3')
    encoding = {1: b'\x4a\x1e', 2: b'\x8a\x1e', 3: b'\xca\x1e'}[delta]
    return CLEANUP_AFTER[:0x1C] + encoding + CLEANUP_AFTER[0x1E:]


def _arm_bytes(arm9, address, size):
    for section in arm9.sections:
        start = section.ramAddress
        end = start + len(section.data)
        if start <= address and address + size <= end:
            offset = address - start
            return bytes(section.data[offset:offset + size])
    raise ValueError('Spit Up ARM9 function is outside loaded sections')


def _guard_shared(rom, image):
    """Authenticate callers and exact native assumptions shared by both images."""
    _need(len(image) == OVERLAY_SIZE, 'Spit Up overlay size')
    task = image[TASK - OVERLAY_BASE:TASK_END - OVERLAY_BASE]
    wrapper = image[WRAPPER - OVERLAY_BASE:WRAPPER_END - OVERLAY_BASE]
    cleanup_in_task = CLEANUP_ADDRESS - TASK
    if task[cleanup_in_task:cleanup_in_task + CLEANUP_SIZE] == CLEANUP_AFTER:
        retail_task = (task[:cleanup_in_task] + CLEANUP_BEFORE
                       + task[cleanup_in_task + CLEANUP_SIZE:])
        _need(_sha(retail_task) == TASK_SHA256, 'Spit Up task identity')
    else:
        _need(_sha(task) == TASK_SHA256, 'Spit Up task identity')
    # The wrapper is untouched and is the sole native owner of this task.
    _need(_sha(wrapper) == WRAPPER_SHA256, 'Spit Up wrapper identity')
    table = FUNCTION_TABLE_ENTRY - OVERLAY_BASE
    literal = TASK_LITERAL - OVERLAY_BASE
    _need(image[table:table + 4] == struct.pack('<I', WRAPPER | 1),
          'Spit Up function-table entry')
    _need(image[literal:literal + 4] == struct.pack('<I', TASK | 1),
          'Spit Up task literal')

    from sgp12.blz import ndspy_load_arm9_sicuro
    arm9 = ndspy_load_arm9_sicuro(rom)
    setattr = _arm_bytes(
        arm9, POKEPIC_SET_ATTR, POKEPIC_SET_ATTR_END - POKEPIC_SET_ATTR)
    _need(_sha(setattr) == POKEPIC_SET_ATTR_SHA256,
          'Spit Up Pokepic_SetAttr preimage')
    addattr = _arm_bytes(
        arm9, POKEPIC_ADD_ATTR, POKEPIC_ADD_ATTR_END - POKEPIC_ADD_ATTR)
    _need(_sha(addattr) == POKEPIC_ADD_ATTR_SHA256,
          'Spit Up Pokepic_AddAttr preimage')

    archive_id = rom.filenames.idOf(ARCHIVE)
    _need(archive_id == ARCHIVE_FILE_ID, 'Spit Up animation archive file ID')
    members = ndspy.narc.NARC(rom.files[archive_id]).files
    _need(len(members) == MEMBER_COUNT, 'Spit Up animation member count')
    member = bytes(members[MEMBER_INDEX])
    _need(len(member) == MEMBER_SIZE and _sha(member) == MEMBER_SHA256,
          'Spit Up member preimage')
    _need(struct.unpack_from('<8I', member, SCRIPT_CALL_OFFSET) == SCRIPT_CALL,
          'Spit Up script command preimage')
    callers = []
    for index, raw_member in enumerate(members):
        for offset in range(0, len(raw_member) - 7, 4):
            if struct.unpack_from('<II', raw_member, offset) == (0x2D, 0x35):
                callers.append((index, offset))
    _need(callers == [(MEMBER_INDEX, SCRIPT_CALL_OFFSET)],
          'Spit Up function 0x35 caller set')


def _container(data):
    """Read overlay 7 using the reviewed BLZ decoder and exact container rows."""
    from sgp12.blz import ndspy_decomprimi_sicuro, ndspy_load_overlays_sicuri

    data = bytes(data)
    rom = ndspy.rom.NintendoDSRom(data)
    fat, fat_size = struct.unpack_from('<II', data, 0x48)
    y9, y9_size = struct.unpack_from('<II', data, 0x50)
    _need(y9_size >= (OVERLAY_ID + 1) * 32 and y9 + y9_size <= len(data),
          'Spit Up y9 bounds')
    row = struct.unpack_from('<8I', data, y9 + OVERLAY_ID * 32)
    _need(row[0] == OVERLAY_ID
          and row[1:4] == (OVERLAY_BASE, OVERLAY_SIZE, 0)
          and row[6] == FILE_ID,
          'Spit Up overlay placement')
    _need(fat_size >= (FILE_ID + 1) * 8 and fat + fat_size <= len(data),
          'Spit Up FAT bounds')
    start, end = struct.unpack_from('<II', data, fat + FILE_ID * 8)
    _need(0 <= start < end <= len(data)
          and end - start == STREAM_SIZE
          and row[7] >> 24 & 1
          and row[7] & 0xFFFFFF == end - start,
          'Spit Up compressed slot')
    stream = bytes(data[start:end])
    _need(bytes(rom.files[FILE_ID]) == stream,
          'Spit Up parsed stream differs from FAT slot')
    image = bytes(ndspy_decomprimi_sicuro(stream, OVERLAY_SIZE))
    loaded = bytes(ndspy_load_overlays_sicuri(rom, [OVERLAY_ID])[
        OVERLAY_ID].data)
    _need(image == loaded,
          'Spit Up overlay decoders disagree')
    return rom, start, end, stream, image


def _guard_before(rom, stream, image):
    cleanup = image[CLEANUP_OFFSET:CLEANUP_OFFSET + CLEANUP_SIZE]
    if cleanup == CLEANUP_AFTER or _sha(stream) == STREAM_SHA256_AFTER:
        raise ValueError('Spit Up overlay is already patched')
    _need(_sha(stream) == STREAM_SHA256_BEFORE,
          'Spit Up compressed preimage hash')
    _need(_sha(image) == OVERLAY_SHA256_BEFORE,
          'Spit Up overlay preimage hash')
    _need(cleanup == CLEANUP_BEFORE and _sha(cleanup) == CLEANUP_SHA256_BEFORE,
          'Spit Up cleanup preimage')
    _need(_sha(image[TASK - OVERLAY_BASE:TASK_END - OVERLAY_BASE]) == TASK_SHA256,
          'Spit Up task preimage hash')
    _guard_shared(rom, image)


def _guard_after(rom, stream, image):
    cleanup = image[CLEANUP_OFFSET:CLEANUP_OFFSET + CLEANUP_SIZE]
    _need(_sha(stream) == STREAM_SHA256_AFTER,
          'Spit Up compressed postimage hash')
    _need(_sha(image) == OVERLAY_SHA256_AFTER,
          'Spit Up overlay postimage hash')
    _need(cleanup == CLEANUP_AFTER and _sha(cleanup) == CLEANUP_SHA256_AFTER,
          'Spit Up cleanup postimage')
    _guard_shared(rom, image)


def patch_overlay(image):
    """Patch the exact retail logical overlay without touching its geometry."""
    image = bytes(image)
    _need(len(image) == OVERLAY_SIZE, 'Spit Up overlay size')
    cleanup = image[CLEANUP_OFFSET:CLEANUP_OFFSET + CLEANUP_SIZE]
    if cleanup == CLEANUP_AFTER:
        raise ValueError('Spit Up overlay is already patched')
    _need(_sha(image) == OVERLAY_SHA256_BEFORE,
          'Spit Up overlay preimage hash')
    _need(cleanup == CLEANUP_BEFORE, 'Spit Up cleanup preimage')
    out = (image[:CLEANUP_OFFSET] + CLEANUP_AFTER
           + image[CLEANUP_OFFSET + CLEANUP_SIZE:])
    _need(_sha(out) == OVERLAY_SHA256_AFTER,
          'Spit Up logical postimage hash')
    return out


def verify_logical_images(before, after):
    before, after = bytes(before), bytes(after)
    _need(len(before) == len(after) == OVERLAY_SIZE,
          'Spit Up logical overlay length')
    _need(before[CLEANUP_OFFSET:CLEANUP_OFFSET + CLEANUP_SIZE] == CLEANUP_BEFORE,
          'Spit Up logical cleanup preimage')
    _need(after[CLEANUP_OFFSET:CLEANUP_OFFSET + CLEANUP_SIZE] == CLEANUP_AFTER,
          'Spit Up logical cleanup postimage')
    _need(before[:CLEANUP_OFFSET] == after[:CLEANUP_OFFSET]
          and before[CLEANUP_OFFSET + CLEANUP_SIZE:]
          == after[CLEANUP_OFFSET + CLEANUP_SIZE:],
          'Spit Up logical bytes outside cleanup')
    changed = sum(old != new for old, new in zip(before, after))
    _need(changed == LOGICAL_CHANGED_BYTES,
          'Spit Up logical changed-byte count')


def apply(data, language):
    """Apply HG-F20-SU in memory and return the image and exact receipt."""
    from sgp12.blz import blz_comprimi_ottimo

    _need(type(data) is bytes and language in LANGUAGES,
          'Spit Up arguments/language')
    rom, start, end, stream, image = _container(data)
    _guard_before(rom, stream, image)
    patched = patch_overlay(image)
    encoded = blz_comprimi_ottimo(patched, bersaglio=end - start)
    _need(type(encoded) is bytes and len(encoded) == end - start,
          'Spit Up compressed postimage length')
    _need(_sha(encoded) == STREAM_SHA256_AFTER,
          'Spit Up compressed postimage differs')
    out = data[:start] + encoded + data[end:]
    receipt = {
        'schema': 1,
        'stage': 'battle-animation-spit-up',
        'language': language,
        'overlay': OVERLAY_ID,
        'file_id': FILE_ID,
        'rom_slot': [start, end],
        'logical_offset': CLEANUP_OFFSET,
        'runtime_address': CLEANUP_ADDRESS,
        'cleanup_delta': CLEANUP_DELTA,
        'input_sha256': _sha(data),
        'output_sha256': _sha(out),
        'stream_sha256_before': STREAM_SHA256_BEFORE,
        'stream_sha256_after': STREAM_SHA256_AFTER,
        'overlay_sha256_before': OVERLAY_SHA256_BEFORE,
        'overlay_sha256_after': OVERLAY_SHA256_AFTER,
        'cleanup_sha256_before': CLEANUP_SHA256_BEFORE,
        'cleanup_sha256_after': CLEANUP_SHA256_AFTER,
    }
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    """Re-read both images, the logical complement and canonical BLZ stream."""
    from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi

    before, after = bytes(before), bytes(after)
    _need(isinstance(receipt, dict)
          and receipt.get('schema') == 1
          and receipt.get('stage') == 'battle-animation-spit-up'
          and receipt.get('language') in LANGUAGES,
          'Spit Up receipt schema/stage/language')
    _need(receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after),
          'Spit Up receipt ROM identity')

    old_rom, start, end, old_stream, old_image = _container(before)
    new_rom, new_start, new_end, new_stream, new_image = _container(after)
    _guard_before(old_rom, old_stream, old_image)
    _guard_after(new_rom, new_stream, new_image)
    _need(len(before) == len(after) and (start, end) == (new_start, new_end),
          'Spit Up cartridge geometry')
    _need(before[:start] == after[:start] and before[end:] == after[end:],
          'Spit Up changed bytes outside overlay 7')
    verify_logical_images(old_image, new_image)
    _need(new_stream == blz_comprimi_ottimo(new_image, bersaglio=end - start),
          'Spit Up noncanonical compressed stream')
    _need(blz_decomprimi(new_stream, OVERLAY_SIZE) == new_image,
          'Spit Up postimage is not in-place BLZ decodable')

    physical = [index for index, (old, new) in enumerate(
        zip(old_stream, new_stream)) if old != new]
    _need(len(physical) == COMPRESSED_CHANGED_BYTES,
          'Spit Up compressed changed-byte count')
    _need((physical[0], physical[-1]) == (0x992, 0x132E0),
          'Spit Up compressed changed-byte extent')

    exact = {
        'overlay': OVERLAY_ID,
        'file_id': FILE_ID,
        'rom_slot': [start, end],
        'logical_offset': CLEANUP_OFFSET,
        'runtime_address': CLEANUP_ADDRESS,
        'cleanup_delta': CLEANUP_DELTA,
        'stream_sha256_before': STREAM_SHA256_BEFORE,
        'stream_sha256_after': STREAM_SHA256_AFTER,
        'overlay_sha256_before': OVERLAY_SHA256_BEFORE,
        'overlay_sha256_after': OVERLAY_SHA256_AFTER,
        'cleanup_sha256_before': CLEANUP_SHA256_BEFORE,
        'cleanup_sha256_after': CLEANUP_SHA256_AFTER,
    }
    for key, value in exact.items():
        _need(receipt.get(key) == value,
              'Spit Up receipt correction/hash/placement differs')

    return {
        'ok': True,
        'rom_slot': [start, end],
        'logical_changed_bytes': LOGICAL_CHANGED_BYTES,
        'compressed_changed_bytes': len(physical),
        'compressed_first_changed_offset': physical[0],
        'compressed_last_changed_offset': physical[-1],
        'cleanup_delta': CLEANUP_DELTA,
        'callers': [[MEMBER_INDEX, SCRIPT_CALL_OFFSET]],
        'container_unchanged': True,
        'loader_agrees': True,
        'postimage_in_place_decode': True,
        'arm9_accessors_pinned': True,
    }


def changed_regions(data):
    """Own the complete compressed overlay slot; BLZ changes are nonlocal."""
    data = bytes(data)
    rom, start, end, stream, image = _container(data)
    _guard_before(rom, stream, image)
    return ((start, end),)
