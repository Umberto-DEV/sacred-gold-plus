"""Compose localized Fairy badges without importing retail artwork into source.

The small letterforms below are original 5x7 bitmaps. Only the label rectangle
is repainted; the caller's borders, palette selection, Nitro metadata and 1D
sprite component order remain intact. The public entry point admits only the
two exact audited Plus members and never writes a ROM.
"""
import hashlib
import struct

from ndspy import lz10
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom


_LABELS = {'FR': 'FÉE', 'ES': 'HADA', 'DE': 'FEE'}
_MEMBERS = {
    ('a/0/0/8', 236): (32, 346,
        '5b8d2e7ec57cc2475f07ed5459ac9575c6f31ae0a0a42edad0129f2680ca7d3d',
        '9a8643adc770d2d0aad9ac76c6504917836d9930dec34d42e8f405b09b50689a'),
    ('a/0/6/8', 123): (48, 124,
        '0b1a3a4c73b304fdd4a3c839149bcaf9b0db980003013f53d2158cb1e02a7cd6',
        'f83a078084b1ffbf83c07e3040fb6996558dd01f305a3581fd62c2d5e4078d63'),
}

# Original letterforms, not sampled from a ROM or a proprietary game font.
_FONT = {
    'A': ('01110', '10001', '10001', '11111', '10001', '10001', '10001'),
    'D': ('11110', '10001', '10001', '10001', '10001', '10001', '11110'),
    'E': ('11111', '10000', '10000', '11110', '10000', '10000', '11111'),
    'F': ('11111', '10000', '10000', '11110', '10000', '10000', '10000'),
    'H': ('10001', '10001', '10001', '11111', '10001', '10001', '10001'),
}


def _paint(raw, width, label):
    """Paint a decoded 4bpp badge in its existing 32+16-pixel sprite layout."""
    if label not in _LABELS.values():
        raise ValueError('unsupported badge label')
    payload_size = width * 8
    if (width not in (32, 48) or len(raw) != 48 + payload_size
            or raw[:4] != b'RGCN' or raw[16:20] != b'RAHC'
            or struct.unpack_from('<I', raw, 8)[0] != len(raw)
            or struct.unpack_from('<HH', raw, 12) != (16, 1)
            or struct.unpack_from('<I', raw, 20)[0] != len(raw) - 16
            or struct.unpack_from('<I', raw, 28)[0] != 3
            or struct.unpack_from('<II', raw, 40) != (payload_size, 24)):
        raise ValueError('unsupported badge NCGR layout')

    if width == 32:
        rectangle = (2, 2, 30, 13)
        background, ink, shadow, baseline, bold, advance, gap = 10, 15, 14, 4, 1, 6, 1
    else:
        rectangle = (6, 3, 42, 13)
        background, ink, shadow, baseline, bold, advance, gap = 7, 14, 15, 5, 2, 8, 2
    result = bytearray(raw)

    def put(x, y, value):
        # A wide badge comprises one 32x16 sprite followed by one 16x16 sprite.
        # Six tiles per raster row would scramble the second component.
        tile = (y // 8) * 4 + x // 8 if x < 32 else 8 + (y // 8) * 2 + (x - 32) // 8
        offset = 48 + tile * 32 + (y % 8) * 4 + (x % 8) // 2
        shift = 4 * (x % 2)
        result[offset] = (result[offset] & ~(15 << shift)) | (value << shift)

    left, top, right, bottom = rectangle
    for y in range(top, bottom):
        for x in range(left, right):
            put(x, y, background)

    text_width = len(label) * advance - gap + 1  # includes the one-pixel shadow
    start = (width - text_width) // 2
    points = set()
    for index, letter in enumerate(label):
        glyph = _FONT['E' if letter == 'É' else letter]
        strokes = {(x, y) for y, row in enumerate(glyph)
                   for x, value in enumerate(row) if value == '1'}
        if letter == 'É':
            strokes.update(((3, -2), (2, -1)))
        for x, y in strokes:
            points.update((start + index * advance + x + dx, baseline + y)
                          for dx in range(bold))
    if any(not (left <= x < right - 1 and top <= y < bottom - 1) for x, y in points):
        raise ValueError('badge label exceeds its text rectangle')
    for x, y in points:
        put(x + 1, y + 1, shadow)
    for x, y in points:
        put(x, y, ink)
    return bytes(result)


def _compose(member, width, label):
    if member[:1] != b'\x10':
        raise ValueError('badge storage must remain LZ10')
    try:
        decoded = bytes(lz10.decompress(member))
    except (ValueError, IndexError, struct.error) as error:
        raise ValueError('invalid badge LZ10 storage') from error
    painted = _paint(decoded, width, label)
    compressed = bytes(lz10.compress(painted))
    if bytes(lz10.decompress(compressed)) != painted:
        raise ValueError('badge compression readback mismatch')
    return compressed


def localize_badges(core: bytes, locale: str) -> dict[tuple[str, int], bytes]:
    """Return the two hash-guarded Fairy NCGR replacements for FR, ES or DE.

    Admission pins are on compressed and decoded member identities. The input
    ROM and its palette members are never modified. Other game data may already
    have been composed, provided these audited English-core badges are intact.
    """
    if not isinstance(locale, str) or locale not in _LABELS:
        raise ValueError('unsupported badge locale')
    if not isinstance(core, bytes):
        raise ValueError('badge core identity requires ROM bytes')
    try:
        rom = NintendoDSRom(core)
    except (ValueError, IndexError, struct.error) as error:
        raise ValueError('invalid badge core identity') from error
    if bytes(rom.idCode) != b'IPKE' or bytes(rom.name) != b'POKEMON SG':
        raise ValueError('badge core identity must remain English Plus')

    admitted = {}
    for key, (width, count, expected, decoded_expected) in _MEMBERS.items():
        path, index = key
        try:
            archive = NARC(rom.getFileByName(path))
            if len(archive.files) != count:
                raise ValueError('member count')
            member = bytes(archive.files[index])
        except (ValueError, IndexError, KeyError, struct.error) as error:
            raise ValueError(f'badge core preimage missing: {path}:{index}') from error
        if hashlib.sha256(member).hexdigest() != expected:
            raise ValueError(f'badge core preimage mismatch: {path}:{index}')
        if hashlib.sha256(lz10.decompress(member)).hexdigest() != decoded_expected:
            raise ValueError(f'badge decoded preimage mismatch: {path}:{index}')
        admitted[key] = (member, width)
    return {key: _compose(member, width, _LABELS[locale])
            for key, (member, width) in admitted.items()}
