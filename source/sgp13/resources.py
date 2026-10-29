"""Append changed resources while keeping original cartridge layout and IDs."""
import struct

from sgp12.rom import crc16


def append_file(data, file_id, payload):
    """Return a new DS image with one FAT member appended on a 512-byte boundary.

    The old body stays intact, including padding and unindexed trailing bytes.
    This is a build-time operation: native cached FAT data must be loaded by a
    cold boot of the resulting cartridge, never edited in a running emulator.
    """
    if len(data) < 0x200 or data[0x12] != 0:
        raise ValueError('expected a complete ordinary DS header')
    if not payload:
        raise ValueError('empty resource payload')
    fat, fat_size = struct.unpack_from('<II', data, 0x48)
    if fat < 0x200 or fat_size % 8 or fat + fat_size > len(data):
        raise ValueError('invalid FAT directory bounds')
    if not isinstance(file_id, int) or not 0 <= file_id < fat_size // 8:
        raise ValueError('file ID is outside the FAT')
    entry = fat + file_id * 8
    old_start, old_end = struct.unpack_from('<II', data, entry)
    if not 0x200 <= old_start <= old_end <= len(data):
        raise ValueError('invalid original resource bounds')
    start = (len(data) + 511) & ~511
    end = start + len(payload)
    if end > 0x20000000:
        raise ValueError('resource would exceed a 512 MiB DS cartridge')
    used = struct.unpack_from('<I', data, 0x80)[0]
    if used > len(data):
        raise ValueError('declared cartridge length exceeds available bytes')
    result = bytearray(data)
    result.extend(b'\xff' * (start - len(result)))
    result.extend(payload)
    struct.pack_into('<II', result, entry, start, end)
    struct.pack_into('<I', result, 0x80, end)
    capacity = result[0x14]
    if capacity > 12:
        raise ValueError('invalid DS cartridge capacity')
    while end > (0x20000 << capacity):
        capacity += 1
    result[0x14] = capacity
    struct.pack_into('<H', result, 0x15e, crc16(result[:0x15e]))
    return bytes(result)
