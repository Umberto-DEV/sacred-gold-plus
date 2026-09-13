#!/usr/bin/env python3
"""Carica la sola `.text` di un oggetto ARM rilocabile, con gli stessi vincoli
della 1.1 (`source/native-eviv/thumb_object.py`, da cui questo file
deriva riga per riga): nessun linker, nessuna sezione allocata oltre `.text`,
nessun simbolo esterno, nessuna rilocazione che non sia una BL Thumb interna.

Differenza dall'originale: l'entrata obbligatoria non è `eviv_hook` ma l'elenco
passato dal chiamante, e vengono restituiti anche i simboli per il manifesto.
"""
import struct


def require(value, message):
    if not value:
        raise ValueError(message)


def load_text(data, address, entries=()):
    require(len(data) >= 52 and data[:7] == b'\x7fELF\x01\x01\x01',
            'Atteso un ELF32 little-endian completo')
    header = struct.unpack_from('<HHIIIIIHHHHHH', data, 16)
    require(header[0] == 1 and header[1] == 40, 'Atteso un oggetto ARM rilocabile')
    shoff, shsize, shnum, shnames = header[5], header[10], header[11], header[12]
    require(shsize == 40 and shoff >= 52 and 0 <= shnames < shnum
            and shoff + shsize * shnum <= len(data), 'Tabella delle sezioni non valida')
    sections = [struct.unpack_from('<10I', data, shoff + i * shsize) for i in range(shnum)]

    def content(section):
        start, size = section[4:6]
        require(start + size <= len(data), 'Sezione fuori dall\'oggetto')
        return data[start:start + size]

    def string(table, index):
        require(0 <= index < len(table), 'Indice di stringa fuori tabella')
        end = table.find(b'\0', index)
        require(end >= 0, 'Stringa ELF non terminata')
        return table[index:end].decode('ascii')

    names = content(sections[shnames])
    labels = [string(names, s[0]) for s in sections]
    require(labels.count('.text') == 1, 'Attesa una sola sezione .text')
    text_index = labels.index('.text')
    for i, section in enumerate(sections):
        require(not (section[2] & 2 and section[5] and i != text_index
                     and labels[i] != '.ARM.exidx'),
                'Sezione allocata inattesa: ' + labels[i] + ' — nessuna costante può stare fuori da .text')
    result = bytearray(content(sections[text_index]))
    symbols, symbol_names = {}, {}
    for index, section in enumerate(sections):
        if section[1] != 2:
            continue
        require(section[9] == 16 and section[5] % 16 == 0 and section[6] < shnum,
                'Tabella dei simboli non valida')
        symbols[index] = list(struct.iter_unpack('<IIIBBH', content(section)))
        strings = content(sections[section[6]])
        for symbol in symbols[index]:
            name = string(strings, symbol[0])
            if name and symbol[5] == text_index:
                symbol_names[name] = address + symbol[1]
            # SHN_UNDEF (0) con nome = simbolo esterno: vietato.
            require(not (name and symbol[5] == 0 and symbol[3] & 0xF0),
                    'Simbolo esterno vietato: ' + name)
    for section in sections:
        require(not (section[1] == 4 and section[7] == text_index),
                'Rilocazioni RELA su .text non supportate')
        if section[1] != 9 or section[7] != text_index:
            continue
        require(section[9] == 8 and section[5] % 8 == 0 and section[6] in symbols,
                'Tabella di rilocazione non valida')
        for offset, info in struct.iter_unpack('<II', content(section)):
            require(info >> 8 < len(symbols[section[6]]), 'Simbolo di rilocazione fuori tabella')
            symbol = symbols[section[6]][info >> 8]
            require(symbol[5] == text_index, 'Rilocazione esterna vietata')
            require(info & 255 == 10 and offset + 4 <= len(result),
                    'Ammessa solo la rilocazione BL Thumb (R_ARM_THM_CALL)')
            hi, lo = struct.unpack_from('<HH', result, offset)
            require(hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800, 'Attesa una BL Thumb-1')
            addend = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
            if addend & 0x400000:
                addend -= 0x800000
            delta = (symbol[1] & ~1) + addend - offset
            require(delta % 2 == 0 and -0x400000 <= delta < 0x400000, 'BL Thumb fuori portata')
            struct.pack_into('<HH', result, offset, 0xF000 | ((delta >> 12) & 0x7FF),
                             0xF800 | ((delta >> 1) & 0x7FF))
    for name in entries:
        require(name in symbol_names, 'Entrata Thumb assente: ' + name)
    return bytes(result), symbol_names
