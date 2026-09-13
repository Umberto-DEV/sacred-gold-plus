"""Read-only Oak heap/video/font and genuine new-save observations."""
import hashlib
import struct
from pathlib import Path
from native_image import require


def reader(path):
    ram = Path(path).read_bytes()
    require(len(ram) == 0x400000, 'Wrong MainRAM extent')
    def view(address, size):
        require(0x02000000 <= address <= 0x02400000-size, 'Read outside MainRAM')
        return ram[address-0x02000000:address-0x02000000+size]
    def word(address): return struct.unpack('<I', view(address, 4))[0]
    def half(address): return struct.unpack('<H', view(address, 2))[0]
    return view, word, half


def heap(path, ident=80):
    view, word, half = reader(path)
    require(ident < half(0x021D1598), 'Missing heap ID')
    indices, handles = word(0x021D1594), word(0x021D1584)
    index = view(indices+ident, 1)[0]
    require(index < half(0x021D159C) and index != half(0x021D159E), 'Invalid heap index')
    address = word(handles+4*index)
    require(word(address) == 0x45585048, 'Not an expanded heap')
    start, end = word(address+0x18), word(address+0x1c)
    require(address+0x38 <= start <= end <= 0x02400000, 'Bad heap extent')
    lists = {}
    for name, offset, signature in [('free', 0x24, 0x4652), ('used', 0x2c, 0x5544)]:
        node, tail, previous, seen, blocks = word(address+offset), word(address+offset+4), 0, set(), []
        while node:
            require(node not in seen and start <= node < end-16 and node % 4 == 0, 'Bad heap node')
            seen.add(node)
            require(half(node) == signature and word(node+8) == previous, 'Bad heap signature/link')
            require(node+16+word(node+4) <= end, 'Heap block exceeds extent')
            blocks.append([node, view(node, 16).hex()])
            previous, node = node, word(node+12)
        require(previous == tail, 'Bad heap tail')
        lists[name] = blocks
    return {'address': address, 'header': view(address, 0x38).hex(), 'lists': lists,
            'counter': half(word(0x021D1590)+ident*2)}


def font(path):
    view, word, _ = reader(path)
    work = word(0x0211188C)
    data = word(work+0x9C)
    return {'work': view(work, 188), 'font0': view(data, 128),
            'colors': view(0x021D1F6E, 6), 'lookup': view(0x021D1F94, 512)}


def oak(path):
    view, word, _ = reader(path)
    require(word(0x021D110C) == 0x021E5BCD, 'Not Oak callback')
    data = word(0x021D1110)
    bg = word(data+0x18)
    require(word(data) == word(bg) == 80, 'Not Oak heap80 data/BG')
    return {'data': data, 'callback': view(0x021D110C, 8),
            'inner_state': word(data+0xC), 'bg': view(bg, 0x168),
            'map': view(word(bg+0xB8), 2048), 'font': font(path)}


def saved_fields(path):
    view, word, _ = reader(path)
    base = word(0x021D2228)
    view(base, 0x2330c)
    fields = {}
    for idx, name, size, keep in [(1, 'options_profile_coins', 48, 38), (2, 'party', 1460, 1456),
            (3, 'bag', 1952, 1948), (4, 'vars_flags', 1104, 1100), (6, 'pokedex', 836, 832),
            (41, 'all_pc_members', 74496, 0x12000)]:
        ident, actual, offset, crc, slot = struct.unpack('<IIIHH', view(base+0x23014+idx*16, 16))
        require((ident, actual, slot) == (idx, size, int(idx == 41)), 'Save array schema differs')
        fields[name] = view(base+0x10+offset, keep)
    return fields


def field_hashes(fields):
    return {name: hashlib.sha256(value).hexdigest() for name, value in fields.items()}


def identity(path):
    fields = saved_fields(path)
    profile = fields['options_profile_coins']
    view, word, _ = reader(path)
    base = word(0x021D2228)
    return {'save_header': list(struct.unpack('<III', view(base, 12))),
            'profile_bytes': profile.hex(), 'party_count': struct.unpack_from('<I', fields['party'], 4)[0],
            'fields_sha256': field_hashes(fields)}
