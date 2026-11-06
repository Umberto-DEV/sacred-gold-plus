"""Fuocofatuo (move 261) accuracy 75 -> 85 in the NitroFS move archive.

The patch changes exactly one byte: the accuracy byte of member 261 inside the
NitroFS archive 'a/0/1/1' (file id 140 in the reference candidates). The archive
keeps its length and no NARC is rebuilt. Nothing else in the ROM changes: the
NDS header, FAT, ARM9, ARM7, overlays, banner and every other file keep their
bytes. Both native readers see the new value: the per-member read used by the
move summary and GetMoveAttr, and the contiguous read from member 0 used by
LoadMoveTbl.
"""
import hashlib
import struct

import ndspy.narc
import ndspy.rom

ARCHIVE = 'a/0/1/1'
MEMBER = 261
MEMBER_COUNT = 471
RECORD = 16
ACCURACY = 5
OLD_ACCURACY = 75
NEW_ACCURACY = 85
MEMBER_BEFORE = bytes.fromhex('a70002000a4b0f000000001611010000')
MEMBER_BEFORE_SHA256 = '2d633a94844cddd9a581ce6e5ece1d8d0373eabd7168510465b9bee3df2c5709'
MEMBER_AFTER = MEMBER_BEFORE[:ACCURACY] + bytes([NEW_ACCURACY]) + MEMBER_BEFORE[ACCURACY + 1:]
LANGUAGES = ('EN', 'IT')
# LoadMoveTbl reads contiguously from member 0 for move IDs 0..467.
MOVE_TABLE_BYTES = 468 * RECORD
HEADER_BYTES = 0x200
FAT_FIELD = 0x48


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _layout(raw):
    """Return the FIMG member-data offset of a NARC of 471 contiguous 16-byte members.

    Raises ValueError for anything else: not a NARC, truncated or padded file,
    wrong member count, or members that are not contiguous 16-byte records.
    """
    # The game archive has the big-endian byte-order mark (FE FF, 00 01); ndspy
    # writes the little-endian mark (FF FE, 01 00). Both are accepted; the data
    # blocks are little-endian in either case.
    if len(raw) < 0x1C or raw[:4] != b'NARC' or raw[4:6] not in (b'\xfe\xff', b'\xff\xfe'):
        raise ValueError('not a NARC archive')
    if raw[6:8] not in (b'\x00\x01', b'\x01\x00'):
        raise ValueError('not a NARC archive: unexpected version')
    size, header, blocks = struct.unpack_from('<IHH', raw, 8)
    if header != 0x10 or blocks != 3:
        raise ValueError('not a NARC archive: unexpected header')
    if size != len(raw):
        raise ValueError(f'archive truncated or padded: header says {size} bytes, got {len(raw)}')
    magic, btaf_size, count = struct.unpack_from('<4sII', raw, 0x10)
    if magic != b'BTAF':
        raise ValueError('not a NARC archive: missing BTAF block')
    if count != MEMBER_COUNT:
        raise ValueError(f'expected {MEMBER_COUNT} members, found {count}')
    if btaf_size != 12 + 8 * count:
        raise ValueError('malformed NARC file allocation block')
    btnf = 0x10 + btaf_size
    if raw[btnf:btnf + 4] != b'BTNF':
        raise ValueError('not a NARC archive: missing BTNF block')
    gmif = btnf + struct.unpack_from('<I', raw, btnf + 4)[0]
    if raw[gmif:gmif + 4] != b'GMIF':
        raise ValueError('not a NARC archive: missing GMIF block')
    data = gmif + 8
    for index in range(count):
        start, end = struct.unpack_from('<II', raw, 0x1C + 8 * index)
        if start != RECORD * index or end - start != RECORD:
            raise ValueError(f'members must be {RECORD} bytes and contiguous: member {index}')
    if data + RECORD * count > len(raw):
        raise ValueError('archive truncated: member data is missing')
    return data


def _fat_slot(data, file_id):
    """Return the (start, end) ROM offsets of a file from the header FAT."""
    fat_offset, fat_length = struct.unpack_from('<II', data, FAT_FIELD)
    if 8 * file_id + 8 > fat_length:
        raise ValueError(f'file id {file_id} is outside the ROM FAT')
    start, end = struct.unpack_from('<II', data, fat_offset + 8 * file_id)
    if not start <= end <= len(data):
        raise ValueError(f'file id {file_id} slot is outside the ROM')
    return start, end


def _changed_offsets(before, after, chunk=1 << 20):
    changed = []
    for base in range(0, len(before), chunk):
        end = min(base + chunk, len(before))
        if before[base:end] != after[base:end]:
            changed.extend(i for i in range(base, end) if before[i] != after[i])
    return changed


def patch_move_archive(raw):
    """Return the archive with member 261 accuracy 75 -> 85, changing one byte in place."""
    data = _layout(raw)
    offset = data + MEMBER * RECORD
    member = bytes(raw[offset:offset + RECORD])
    if member == MEMBER_AFTER:
        raise ValueError('archive already patched: member 261 accuracy is 85')
    if _sha256(member) != MEMBER_BEFORE_SHA256 or member[ACCURACY] != OLD_ACCURACY:
        raise ValueError(f'foreign member 261: sha256 {_sha256(member)}')
    out = bytearray(raw)
    out[offset + ACCURACY] = NEW_ACCURACY
    return bytes(out)


def apply(data, language):
    """Patch the move archive inside a ROM image; return (patched ROM, receipt).

    The archive is written back into its own FAT slot with the same length, so
    exactly one ROM byte changes. The result is checked by verify() before it is
    returned.
    """
    if language not in LANGUAGES:
        raise ValueError(f'unknown language {language!r}: expected EN or IT')
    data = bytes(data)
    file_id = ndspy.rom.NintendoDSRom(data).filenames.idOf(ARCHIVE)
    if file_id is None:
        raise ValueError(f'{ARCHIVE} not found in ROM')
    start, end = _fat_slot(data, file_id)
    archive = data[start:end]
    patched = patch_move_archive(archive)
    offset = _layout(archive) + MEMBER * RECORD + ACCURACY
    out = bytearray(data)
    out[start:end] = patched
    out = bytes(out)
    receipt = {
        'language': language,
        'file_id': file_id,
        'archive': ARCHIVE,
        'rom_slot': [start, end],
        'rom_offset': start + offset,
        'archive_offset': offset,
        'member': MEMBER,
        'byte_index': ACCURACY,
        'before': OLD_ACCURACY,
        'after': NEW_ACCURACY,
        'input_sha256': _sha256(data),
        'output_sha256': _sha256(out),
        'archive_sha256_before': _sha256(archive),
        'archive_sha256_after': _sha256(patched),
        'member_sha256_before': MEMBER_BEFORE_SHA256,
        'member_sha256_after': _sha256(MEMBER_AFTER),
    }
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    """Re-read both ROM images independently; raise ValueError on any deviation.

    Checks equal length and an unchanged header; that the only changed ROM byte is
    the receipt offset, which covers ARM9, ARM7, overlays, banner, FAT and every
    other file; that every other NitroFS file and archive member is identical;
    that member 261 moved only byte 5 from 75 to 85; and that the FAT read and the
    contiguous member-0 read both give 85.
    """
    if len(before) != len(after):
        raise ValueError('ROM length changed')
    if before[:HEADER_BYTES] != after[:HEADER_BYTES]:
        raise ValueError('ROM header changed')
    changed = _changed_offsets(before, after)

    rom_before = ndspy.rom.NintendoDSRom(before)
    rom_after = ndspy.rom.NintendoDSRom(after)
    file_id = rom_before.filenames.idOf(ARCHIVE)
    if file_id is None or file_id != receipt.get('file_id') or rom_after.filenames.idOf(ARCHIVE) != file_id:
        raise ValueError('archive file id differs from receipt')
    start, end = _fat_slot(before, file_id)
    if _fat_slot(after, file_id) != (start, end) or [start, end] != receipt.get('rom_slot'):
        raise ValueError('FAT slot differs from receipt')
    if len(rom_before.files) != len(rom_after.files):
        raise ValueError('NitroFS file count changed')
    for index, (old, new) in enumerate(zip(rom_before.files, rom_after.files)):
        if index != file_id and old != new:
            raise ValueError(f'NitroFS file {index} changed')

    old_archive = rom_before.files[file_id]
    new_archive = rom_after.files[file_id]
    if old_archive != before[start:end] or new_archive != after[start:end]:
        raise ValueError('FAT slot does not hold the archive')
    data_start = _layout(old_archive)
    if _layout(new_archive) != data_start:
        raise ValueError('archive data offset changed')

    old_members = ndspy.narc.NARC(old_archive).files
    new_members = ndspy.narc.NARC(new_archive).files
    if len(old_members) != MEMBER_COUNT or len(new_members) != MEMBER_COUNT:
        raise ValueError('archive member count differs')
    for index, (old, new) in enumerate(zip(old_members, new_members)):
        if index != MEMBER and old != new:
            raise ValueError(f'archive member {index} changed')
    old_member = old_members[MEMBER]
    new_member = new_members[MEMBER]
    if (_sha256(old_member) != MEMBER_BEFORE_SHA256 or old_member[ACCURACY] != OLD_ACCURACY
            or new_member[ACCURACY] != NEW_ACCURACY
            or new_member[:ACCURACY] + new_member[ACCURACY + 1:]
            != old_member[:ACCURACY] + old_member[ACCURACY + 1:]):
        raise ValueError('member 261 differs from the expected 75 -> 85 change')

    contiguous = new_archive[data_start:data_start + MOVE_TABLE_BYTES]
    if contiguous != b''.join(new_members)[:MOVE_TABLE_BYTES]:
        raise ValueError('contiguous member read differs from the FAT member read')
    fat_read = new_members[MEMBER][ACCURACY]
    battle_read = contiguous[MEMBER * RECORD + ACCURACY]
    if fat_read != NEW_ACCURACY or battle_read != NEW_ACCURACY:
        raise ValueError(f'resident read {fat_read} and battle read {battle_read} must both be 85')

    rom_offset = start + data_start + MEMBER * RECORD + ACCURACY
    if receipt.get('rom_offset') != rom_offset or changed != [rom_offset]:
        raise ValueError(f'changed ROM bytes {changed[:5]} differ from receipt offset {rom_offset}')
    if before[rom_offset] != OLD_ACCURACY or after[rom_offset] != NEW_ACCURACY:
        raise ValueError('ROM accuracy byte is not 75 -> 85')
    return {
        'rom_length': len(after),
        'header_unchanged': True,
        'changed_rom_bytes': len(changed),
        'rom_offset': rom_offset,
        'file_id': file_id,
        'rom_slot': [start, end],
        'member': MEMBER,
        'accuracy_before': OLD_ACCURACY,
        'accuracy_after': NEW_ACCURACY,
        'fat_read_after': fat_read,
        'contiguous_read_after': battle_read,
        'nitrofs_files_unchanged': len(rom_before.files) - 1,
        'archive_members_unchanged': MEMBER_COUNT - 1,
    }
