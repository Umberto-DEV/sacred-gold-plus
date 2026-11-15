"""Bounded title update in the existing 29-entry onboarding text bank."""
import struct

ADDRESS = 0x023DA800
SIZE = 1008
COUNT = 29
TITLE_ID = 20
TITLE = 'Sacred Gold Plus V1.3.3'
OLD_CORE_TITLE = 'Sacred Gold Plus V1.3'
OLD_REGIONAL_TITLE = 'Sacred Gold Plus V1.3.2'


def pack(strings):
    if len(strings) != COUNT:
        raise ValueError('onboarding string count')
    out = bytearray(COUNT * 2)
    seen = {}
    for i, raw in enumerate(strings):
        if type(raw) is not bytes or len(raw) < 2 or len(raw) % 2 or raw[-2:] != b'\xff\xff':
            raise ValueError('onboarding string geometry')
        if raw not in seen:
            seen[raw] = len(out)
            out.extend(raw)
        struct.pack_into('<H', out, 2*i, seen[raw])
    if len(out) > SIZE:
        raise ValueError('onboarding bank overflow')
    return bytes(out) + bytes(SIZE - len(out))


def parse(bank):
    if type(bank) is not bytes or len(bank) != SIZE:
        raise ValueError('onboarding bank size')
    strings = []
    for i in range(COUNT):
        off = struct.unpack_from('<H', bank, 2*i)[0]
        if off < COUNT * 2 or off % 2 or off >= SIZE:
            raise ValueError('onboarding offset')
        end = off
        while end < SIZE and bank[end:end+2] != b'\xff\xff':
            end += 2
        if end >= SIZE:
            raise ValueError('onboarding terminator')
        strings.append(bank[off:end+2])
    if pack(strings) != bank:
        raise ValueError('onboarding noncanonical bank or suffix')
    return strings


def _encoded(text, encode):
    words = encode(text)
    if not words or len(words) > 64 or words[-1] != 0xFFFF or 0xFFFF in words[:-1]:
        raise ValueError('onboarding title geometry')
    return struct.pack('<%dH' % len(words), *words)


def transform(before, encode, measure):
    strings = parse(before)
    if strings[TITLE_ID] != _encoded(OLD_CORE_TITLE, encode):
        raise ValueError('onboarding old title differs')
    title = _encoded(TITLE, encode)
    if measure(encode(TITLE)) > 204:
        raise ValueError('onboarding title width')
    strings[TITLE_ID] = title
    return pack(strings)


def verify_transition(before, after, encode, old_title):
    old, new = parse(before), parse(after)
    if old[TITLE_ID] != _encoded(old_title, encode) or new[TITLE_ID] != _encoded(TITLE, encode):
        raise ValueError('onboarding title identity')
    if any(old[i] != new[i] for i in range(COUNT) if i != TITLE_ID):
        raise ValueError('onboarding foreign strings')
    return True
