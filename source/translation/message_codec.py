#!/usr/bin/env python3
"""Gen IV message codec with exact preservation of untouched bank data.

Format reference: pret/pokeheartgold tools/msgenc, revision
0985e8718df4f25e64d6507d89c0c97c0d288981. No game text is embedded here.
"""
import struct


def _words(value):
    result = list(value)
    if not result or result[-1] != 0xFFFF:
        raise ValueError('Message must end with FFFF')
    if any(not isinstance(w, int) or not 0 <= w <= 0xFFFF for w in result):
        raise ValueError('Message contains a value outside 16 bits')
    return result


def unpack_name(words):
    words = _words(words)
    if words[0] != 0xF100:
        return words
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
                return result + [0xFFFF]
            result.append(code)
    raise ValueError('Packed name has no terminator')


def pack_name(words):
    words = _words(words)
    if any(w >= 0x1FF for w in words[:-1]):
        raise ValueError('Packed names only support glyphs below 01FF')
    result = [0xF100]
    accumulator = bits = 0
    for code in words[:-1]:
        accumulator |= code << bits
        bits += 9
        if bits >= 15:
            bits -= 15
            result.append(accumulator & 0x7FFF)
            accumulator >>= 15
    if bits > 1:
        result.append((accumulator | (0xFFFF << bits)) & 0x7FFF)
    return result + [0xFFFF]


def encode_text(text, characters, commands):
    """Encode the audit's literal token notation, including STRVAR variants."""
    reverse = {}
    for code, token in characters.items():
        # Only a duplicated full-width z exists in the supplied charmap.
        # Untouched retail messages retain their raw words instead of relying
        # on a text round-trip through this ambiguous glyph.
        reverse.setdefault(token, code)
    command_ids = {name: code for code, name in commands.items()}
    tokens = {}
    for token in sorted(reverse, key=len, reverse=True):
        if token:
            tokens.setdefault(token[0], []).append(token)
    result = []
    cursor = 0
    while cursor < len(text):
        if text[cursor] == '{':
            end = text.find('}', cursor + 1)
            if end < 0:
                raise ValueError('Unclosed control token')
            parts = text[cursor + 1:end].split(':')
            name = parts.pop(0)
            if name in command_ids:
                command = command_ids[name]
            elif name.startswith('CMD_'):
                command = int(name[4:], 16)
            else:
                raise ValueError(f'Unknown control: {name}')
            if name.startswith('STRVAR_') and len(parts) == 2:
                variant = int(parts.pop(0))
                if not 0 <= variant <= 255:
                    raise ValueError('STRVAR subtype outside one byte')
                command |= variant
            if len(parts) > 1:
                raise ValueError('Too many control separators')
            args = [int(n) for n in parts[0].split(',')] if parts and parts[0] else []
            if not 0 <= command <= 0xFFFF or any(not 0 <= n <= 0xFFFF for n in args):
                raise ValueError('Control value outside 16 bits')
            result.extend([0xFFFE, command, len(args), *args])
            cursor = end + 1
        else:
            for token in tokens.get(text[cursor], []):
                if token and text.startswith(token, cursor):
                    result.append(reverse[token])
                    cursor += len(token)
                    break
            else:
                raise ValueError(f'Unencodable character at {cursor}: {text[cursor:cursor+12]!r}')
    return result + [0xFFFF]


class Bank:
    def __init__(self, raw):
        self._original = bytes(raw)
        if len(raw) < 4:
            raise ValueError('Truncated bank header')
        count, self.key = struct.unpack_from('<HH', raw)
        if 4 + count * 8 > len(raw):
            raise ValueError('Truncated allocation table')
        self.words = []
        for index in range(count):
            key = (765 * (index + 1) * self.key) & 0xFFFF
            key |= key << 16
            offset, length = struct.unpack_from('<II', raw, 4 + index * 8)
            offset ^= key
            length ^= key
            if offset < 4 + count * 8 or offset + length * 2 > len(raw):
                raise ValueError(f'Message {index} exceeds bank bounds')
            encrypted = struct.unpack_from(f'<{length}H', raw, offset)
            seed = ((index + 1) * 596947) & 0xFFFF
            words = []
            for word in encrypted:
                words.append(word ^ seed)
                seed = (seed + 18749) & 0xFFFF
            self.words.append(_words(words))
        self._initial = [w.copy() for w in self.words]

    @classmethod
    def from_words(cls, messages, key=0):
        if not isinstance(key, int) or not 0 <= key <= 0xFFFF:
            raise ValueError('Bank key must fit 16 bits')
        obj = cls.__new__(cls)
        obj.key = key
        obj.words = [_words(m) for m in messages]
        if len(obj.words) > 0xFFFF:
            raise ValueError('Too many messages')
        obj._original = None
        obj._initial = None
        return obj

    def replace(self, index, words):
        self.words[index] = _words(words)

    def save(self):
        if self._original is not None and self.words == self._initial:
            return self._original
        messages = [_words(m) for m in self.words]
        header = bytearray(struct.pack('<HH', len(messages), self.key))
        payload = bytearray()
        offset = 4 + 8 * len(messages)
        for index, words in enumerate(messages):
            table_key = (765 * (index + 1) * self.key) & 0xFFFF
            table_key |= table_key << 16
            header.extend(struct.pack('<II', offset ^ table_key, len(words) ^ table_key))
            seed = ((index + 1) * 596947) & 0xFFFF
            encrypted = []
            for word in words:
                encrypted.append(word ^ seed)
                seed = (seed + 18749) & 0xFFFF
            payload.extend(struct.pack(f'<{len(encrypted)}H', *encrypted))
            offset += len(encrypted) * 2
        return bytes(header + payload)
