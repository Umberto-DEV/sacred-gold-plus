#!/usr/bin/env python3
"""Shared, self-contained decoder for the HGSS/Plus message archive (a/0/2/7).

Written for SGP-1.2-LINGUA-01 (12 September 2026) so `estrai_banchi.py` and
`controlla_it.py` share one decode path instead of duplicating
`source/translation/audit_localization.py`'s `render()`.

Unlike `audit_localization.py`, this module does NOT require a
`pret/pokeheartgold` checkout: it only needs `charmap.txt` (a character-code
mapping table, not extracted game text) which the caller supplies a path to.
The cipher/packing logic matches
`source/translation/message_codec.py` exactly (see that file for the
authoritative round-trip codec used by the release builder); this module only
reads and renders to text, it never writes a bank.
"""
from __future__ import annotations

import struct
from pathlib import Path
from typing import Optional

CONTROL_MARKER = 0xFFFE
TERMINATOR = 0xFFFF


def load_charmap(charmap_path) -> tuple[dict, dict]:
    """Parse a pret/pokeheartgold-style charmap.txt. Returns (chars, commands):
    chars: {code: single-glyph-or-escape text}; commands: {code: command name}."""
    chars, commands = {}, {}
    for line in Path(charmap_path).read_text(encoding='utf-8').splitlines():
        line = line.split('//')[0].lstrip()
        if not line or '=' not in line:
            continue
        code_text, text = line.split('=', 1)
        code = int(code_text, 16)
        if text.startswith('{') and text.endswith('}'):
            commands[code] = text[1:-1]
        else:
            chars[code] = text
    return chars, commands


def unpack_name(words):
    """Expand an F100-prefixed 9-bit packed name back to normal-width codes.
    Returns (expanded_words, was_packed)."""
    if not words or words[0] != 0xF100:
        return words, False
    accumulator = bits = 0
    result = []
    for word in words[1:]:
        accumulator |= (word & 0x7FFF) << bits
        bits += 15
        while bits >= 9:
            code = accumulator & 0x1FF
            accumulator >>= 9
            bits -= 9
            if code == 0x1FF:
                return result + [TERMINATOR], True
            result.append(code)
    raise ValueError('Packed name has no terminator')


def render(words, chars: dict, commands: dict) -> dict:
    """Decode one message's word stream to a display-notation string plus
    structural metadata. Mirrors audit_localization.render()'s output shape:
    {'text', 'controls', 'unknown_codes', 'malformed_controls', 'normalized'}.
    Control tokens render as '{NAME:arg,arg}' or '{CMD_XXXX:...}'; STRVAR
    families render as '{STRVAR_N:variant,args}'."""
    words, compressed = unpack_name(words)
    text, controls, unknown, normalized, malformed = [], [], [], [], []
    i = 0
    while i < len(words):
        code = words[i]
        normalized.append(code)
        i += 1
        if code == TERMINATOR:
            break
        if code == CONTROL_MARKER:
            if i + 2 > len(words):
                malformed.append({'word_index': i - 1, 'reason': 'truncated control header'})
                normalized.extend(words[i:])
                text.append('{INVALID_CONTROL_HEADER}')
                break
            command, argc = words[i:i + 2]
            args = words[i + 2:i + 2 + argc]
            if len(args) != argc:
                malformed.append({'word_index': i - 1, 'reason': 'truncated control arguments',
                                   'command': command, 'declared_arguments': argc,
                                   'remaining_words': len(words) - i - 2})
                normalized.extend(words[i:])
                text.append('{INVALID_CONTROL:' + ','.join(f'{w:04X}' for w in words[i:]) + '}')
                break
            normalized.extend([command, argc, *args])
            controls.append([command, args])
            name = commands.get(command)
            if not name and command & 0xFF00 in (0x100, 0x300, 0x400, 0x3400):
                name = f'STRVAR_{command >> 8:X}:{command & 255}'
            text.append('{' + (name or f'CMD_{command:04X}') +
                        (':' if args else '') + ','.join(map(str, args)) + '}')
            i += 2 + argc
        elif code in chars:
            text.append(chars[code])
        else:
            unknown.append(code)
            text.append(f'<{code:04X}>')
    if not normalized or normalized[-1] != TERMINATOR:
        malformed.append({'word_index': len(normalized), 'reason': 'missing terminator'})
    return {
        'text': ''.join(text), 'controls': controls, 'unknown_codes': unknown,
        'malformed_controls': malformed, 'normalized': normalized, 'compressed_name': compressed,
    }


def read_bank_raw(data: bytes):
    """Decrypt one bank's messages to raw word-lists (no rendering). Same
    cipher as message_codec.Bank; kept independent here so this module has
    no import-time dependency on the translation/ package."""
    count, key = struct.unpack_from('<HH', data)
    if 4 + 8 * count > len(data):
        raise ValueError('Truncated allocation table')
    messages = []
    for index in range(count):
        table_key = (765 * (index + 1) * key) & 0xFFFF
        table_key |= table_key << 16
        offset, size = struct.unpack_from('<II', data, 4 + 8 * index)
        offset ^= table_key
        size ^= table_key
        if offset < 4 + 8 * count or offset + size * 2 > len(data):
            raise ValueError(f'Message {index} exceeds bank bounds')
        encrypted = struct.unpack_from(f'<{size}H', data, offset)
        seed = ((index + 1) * 596947) & 0xFFFF
        words = []
        for word in encrypted:
            words.append(word ^ seed)
            seed = (seed + 18749) & 0xFFFF
        messages.append(words)
    return messages


def read_bank(data: bytes, chars: dict, commands: dict):
    """Decrypt and render every message in one bank NARC member."""
    return [render(words, chars, commands) for words in read_bank_raw(data)]
