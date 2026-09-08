"""Read-only message decoder used by the release builder.

The cipher and name packing follow pret/pokeheartgold msgenc.
No CLI, file writer or retail catalogue export is included.
"""

import struct

NAMES = {'US':'Pokemon - HeartGold Version.nds', 'IT':'Pokemon - Versione Oro HeartGold.nds', 'SG':'Pokemon - Sacred Gold Plus.nds'}

PRET = None
CHARMAP, COMMANDS = {}, {}

def mapping():
    chars, commands = {}, {}
    for line in (PRET/'charmap.txt').read_text().splitlines():
        line = line.split('//')[0].lstrip()
        if not line or '=' not in line:
            continue
        code, text = line.split('=', 1)
        code = int(code, 16)
        if text.startswith('{') and text.endswith('}'):
            commands[code] = text[1:-1]
        else:
            chars[code] = text
    return chars, commands

def expand_name(words):
    if not words or words[0] != 0xF100:
        return words, False
    packed, bitcount, result = 0, 0, []
    for word in words[1:]:
        packed |= (word & 0x7FFF) << bitcount
        bitcount += 15
        while bitcount >= 9:
            code = packed & 0x1FF
            packed >>= 9
            bitcount -= 9
            if code == 0x1FF:
                return result + [0xFFFF], True
            result.append(code)
    raise ValueError('Compressed name missing terminator')

def render(words):
    words, compressed = expand_name(words)
    text, controls, unknown, normalized, malformed = [], [], [], [], []
    i = 0
    while i < len(words):
        c = words[i]
        normalized.append(c)
        i += 1
        if c == 0xFFFF:
            break
        if c == 0xFFFE:
            if i + 2 > len(words):
                malformed.append({'word_index':i-1,'reason':'truncated control header'})
                normalized.extend(words[i:])
                text.append('{INVALID_CONTROL_HEADER}')
                break
            command, count = words[i:i+2]
            args = words[i+2:i+2+count]
            if len(args) != count:
                malformed.append({'word_index':i-1,'reason':'truncated control arguments','command':command,'declared_arguments':count,'remaining_words':len(words)-i-2})
                normalized.extend(words[i:])
                text.append('{INVALID_CONTROL:'+','.join(f'{w:04X}' for w in words[i:])+'}')
                break
            normalized.extend([command, count, *args])
            controls.append([command, args])
            name = COMMANDS.get(command)
            if not name and command & 0xFF00 in (0x100, 0x300, 0x400, 0x3400):
                name = f'STRVAR_{command>>8:X}:{command&255}'
            text.append('{' + (name or f'CMD_{command:04X}') + (':' if args else '') + ','.join(map(str,args)) + '}')
            i += 2 + count
        elif c in CHARMAP:
            text.append(CHARMAP[c])
        else:
            unknown.append(c)
            text.append(f'<{c:04X}>')
    assert normalized[-1] == 0xFFFF, 'Missing string terminator'
    return {'text': ''.join(text), 'controls': controls, 'unknown_codes': unknown,'malformed_controls':malformed,
            'normalized': normalized, 'compressed_name': compressed}

def read_bank(data):
    count, key = struct.unpack_from('<HH', data)
    assert 4 + 8*count <= len(data)
    messages = []
    for index in range(count):
        table_key = (765*(index+1)*key) & 0xFFFF
        table_key |= table_key << 16
        offset, size = struct.unpack_from('<II',data,4+8*index)
        offset ^= table_key
        size ^= table_key
        assert offset >= 4 + 8*count and offset+size*2 <= len(data), (index, offset, size, len(data))
        encrypted = struct.unpack_from(f'<{size}H',data,offset)
        seed = ((index+1)*596947)&0xFFFF
        words = []
        for word in encrypted:
            words.append(word ^ seed)
            seed = (seed + 18749)&0xFFFF
        messages.append(render(words))
    return messages
