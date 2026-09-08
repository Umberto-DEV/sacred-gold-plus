"""Append replacements to a DS image without relocating existing code or files."""
import hashlib
import struct

from ndspy import _common, rom


def append_files(source, replacements, reuse_existing=False):
    source = bytes(source)
    if not replacements:
        return source, []
    if len(source) < 0x200:
        raise ValueError('Truncated DS header')
    fat_start, fat_size = struct.unpack_from('<II', source, 0x48)
    if fat_start < 0x200 or fat_size % 8 or fat_start + fat_size > len(source):
        raise ValueError('Invalid file allocation table')
    parsed = rom.NintendoDSRom(source)
    extents = [struct.unpack_from('<II', source, fat_start + i * 8) for i in range(fat_size // 8)]
    selected = []
    for name, data in replacements.items():
        index = parsed.filenames.idOf(name)
        if index is None or not 0 <= index < fat_size // 8:
            raise ValueError(f'File is absent from NitroFS: {name}')
        start, end = struct.unpack_from('<II', source, fat_start + index * 8)
        if not fat_start + fat_size <= start <= end <= len(source):
            raise ValueError(f'Invalid source extent: {name}')
        selected.append((index, name, start, end, bytes(data)))
    result = bytearray(source)
    changes = []
    for index, name, start, end, data in sorted(selected):
        reuse = reuse_existing and len(data) <= end - start
        if reuse_existing and not reuse:
            # Only existing uniform 00/FF padding to this 512-byte boundary is
            # reusable. A neighbouring file or non-padding byte forbids growth.
            new_end = start + len(data)
            boundary = min((end + 511) & ~511, len(source))
            overlaps = any(i != index and start < other_end and new_end > other_start
                           for i, (other_start, other_end) in enumerate(extents))
            gap = source[end:new_end]
            padding = gap == bytes(len(gap)) or gap == b'\xFF' * len(gap)
            reuse = new_end <= boundary and not overlaps and padding
        if reuse:
            new_start = start
            result[start:start + len(data)] = data
        else:
            result.extend(b'\xFF' * ((-len(result)) % 512))
            new_start = len(result)
            result.extend(data)
        new_end = new_start + len(data)
        entry = fat_start + index * 8
        struct.pack_into('<II', result, entry, new_start, new_end)
        changes.append({'file': name, 'file_id': index, 'fat_entry': entry,
                        'old_start': start, 'old_end': end, 'new_start': new_start,
                        'new_end': new_end, 'reused_extent': reuse,
                        'sha256': hashlib.sha256(data).hexdigest()})
    capacity = result[0x14]
    while len(result) > (0x20000 << capacity):
        capacity += 1
    if capacity > 12:
        raise ValueError('Output exceeds 512 MiB DS cartridge limit')
    result[0x14] = capacity
    struct.pack_into('<I', result, 0x80, len(result))
    struct.pack_into('<H', result, 0x15E, _common.crc16(result[:0x15E]))
    return bytes(result), changes
