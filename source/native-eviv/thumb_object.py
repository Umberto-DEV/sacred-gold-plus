"""Load only the bounded, self-contained Thumb .text emitted by Clang.

No general ELF linker: reject other executable sections, external symbols and
relocation types. Runtime never consumes the ELF or this host-side helper.
"""
import struct
from native_image import require


def load_text(data, address):
    require(len(data) >= 52 and data[:7] == b'\x7fELF\x01\x01\x01',
            'Expected a complete little-endian ELF32 header')
    header = struct.unpack_from('<HHIIIIIHHHHHH', data, 16)
    require(header[0] == 1 and header[1] == 40, 'Expected a relocatable ARM object')
    shoff, shsize, shnum, shnames = header[5], header[10], header[11], header[12]
    require(shsize == 40 and shoff >= 52 and 0 <= shnames < shnum
            and shoff + shsize * shnum <= len(data), 'Invalid section table')
    sections = [struct.unpack_from('<10I', data, shoff + i * shsize) for i in range(shnum)]
    def content(section):
        start, size = section[4:6]
        require(start + size <= len(data), 'Section outside object')
        return data[start:start + size]
    def string(table, index):
        require(0 <= index < len(table), 'String index outside table')
        end = table.find(b'\0', index)
        require(end >= 0, 'Unterminated ELF string')
        return table[index:end].decode('ascii')
    names = content(sections[shnames])
    labels = [string(names, s[0]) for s in sections]
    require(labels.count('.text') == 1, 'Expected one .text section')
    text_index = labels.index('.text')
    for i, section in enumerate(sections):
        require(not (section[2] & 2 and section[5] and i != text_index
                     and labels[i] != '.ARM.exidx'), 'Unexpected allocated section: ' + labels[i])
    result = bytearray(content(sections[text_index]))
    symbols, symbol_names = {}, {}
    for index, section in enumerate(sections):
        if section[1] != 2:
            continue
        require(section[9] == 16 and section[5] % 16 == 0 and section[6] < shnum,
                'Invalid symbol table')
        symbols[index] = list(struct.iter_unpack('<IIIBBH', content(section)))
        strings = content(sections[section[6]])
        for symbol in symbols[index]:
            name = string(strings, symbol[0])
            if name and symbol[5] == text_index:
                symbol_names[name] = address + symbol[1]
    for section in sections:
        require(not (section[1] == 4 and section[7] == text_index),
                'RELA text relocations are unsupported')
        if section[1] != 9 or section[7] != text_index:
            continue
        require(section[9] == 8 and section[5] % 8 == 0 and section[6] in symbols,
                'Invalid relocation table')
        for offset, info in struct.iter_unpack('<II', content(section)):
            require(info >> 8 < len(symbols[section[6]]), 'Relocation symbol outside table')
            symbol = symbols[section[6]][info >> 8]
            require(symbol[5] == text_index, 'External relocation is forbidden')
            require(info & 255 == 10 and offset + 4 <= len(result), 'Only Thumb BL relocation supported')
            hi, lo = struct.unpack_from('<HH', result, offset)
            require(hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800, 'Expected Thumb-1 BL')
            addend = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
            if addend & 0x400000:
                addend -= 0x800000
            delta = (symbol[1] & ~1) + addend - offset
            require(delta % 2 == 0 and -0x400000 <= delta < 0x400000, 'Thumb BL out of range')
            struct.pack_into('<HH', result, offset, 0xF000 | ((delta >> 12) & 0x7FF),
                             0xF800 | ((delta >> 1) & 0x7FF))
    require('eviv_hook' in symbol_names, 'Missing Thumb entry')
    return bytes(result), symbol_names
