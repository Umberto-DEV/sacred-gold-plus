"""Read-only advance-width check of the authenticated Training menus."""
import argparse
import hashlib
import json
import mmap
from pathlib import Path
import struct
import sys

from ndspy import fnt, narc
from sgp12.blz import ndspy_decomprimi_sicuro, blz_verifica_ndspy, BLZ_MAX_DECOMPRESSA
from sgp12.rom import Rifiuto
from sgp131 import guide_content, portable
from localization.messages import _TEXT
from translation.message_codec import Bank, encode_text

FONT_SHA = '7bdadd0f2ed2507b34f002ad17117a532423ab474c46d499388eb551e785296a'
NATIVE_PINS = (
    (0x020FAD00 + 749 * 4, 16, '6b2fcdb101de39c5154f80f5bc584681995460c491e2fafe03e7eca553caeb03'),
    (0x020400AC, 60, 'b3e2ba119e38757a85f31b512e0b4a8112004476f134a6ab4352b421a86586d4'),
    (0x0203FD18, 256, '5b92ed1fd456aa0e52a1a5c6685820be68db4bfaffe1ecad65a5fbd484d45a9c'),
    (0x02041770, 124, '4919c29ec1856bf42e65633130b6c8001dd80cadb1f9b4c4ced23a00313953c1'),
    (0x020477F8, 282, '4e58ac5407830f866fa73a958eb385417261ce2c251b1f500513e732ec7d2dfe'),
)
OVERLAY1_SHA = 'c5ed85217408f3bceea034b1f60bb78c6ec711840a136ddc6fa88339d0682f3b'
OVERLAY_SHA = 'c998ec2bebbb5efa66e49080dbafd5c0fc3124b5ceb7cf90cee50af1524dbf86'
TEMPLATE = bytes.fromhex('0502010c040480000512010c0404b0000502070c0404e0000512070c0404100105020d0c0404400105120d0c040470010512130c0404a001')
ROWS = ((385, (60, 61, 62, 63, 64, 65, 29), 238),
        (557, (51, 52, 53, 54, 55, 56, 20), 858),
        (630, (42, 43, 44, 45, 46, 47, 11), 942))
KEYS = [f'm:385:{i}' for i in ROWS[0][1]]
SERVICE6_ROWS = ((557, (12, 15, 16, 17, 18, 19), 858),
                 (630, (3, 6, 7, 8, 9, 10), 942))
SERVICE6_KEYS = [f'm:385:{i}' for i in (21, 24, 25, 26, 27, 28)]
SERVICE6_TEMPLATE_SHA = '59ae4cb24de5aee5b4decb2d2500bac73879e0ea0f0d01f21b8b64b0094de4f0'



def digest(data):
    return hashlib.sha256(data).hexdigest()


def extent(rom, off, size, label):
    if off < 0 or size <= 0 or off > len(rom) or size > len(rom) - off:
        raise ValueError('invalid ' + label + ' extent')
    return rom[off:off + size]


def fat_file(rom, fid):
    fa, size = struct.unpack_from('<2I', rom, 0x48)
    extent(rom, fa, size, 'FAT')
    if size % 8 or not isinstance(fid, int) or not 0 <= fid < size // 8:
        raise ValueError('invalid FAT file ID or size')
    a, b = struct.unpack_from('<2I', rom, fa + fid * 8)
    if a > b or b > len(rom):
        raise ValueError('invalid FAT file extent')
    return rom[a:b]


def resource(rom, name):
    fo, fs = struct.unpack_from('<2I', rom, 0x40)
    fnt_bytes = extent(rom, fo, fs, 'FNT')
    try:
        fid = fnt.load(fnt_bytes).idOf(name)
    except (AssertionError, RuntimeError, IndexError, struct.error) as exc:
        raise ValueError('invalid FNT') from exc
    if fid is None:
        raise ValueError('missing resource ' + name)
    return fat_file(rom, fid)


def archive(raw):
    try:
        return narc.NARC(raw)
    except (AssertionError, RuntimeError, IndexError, struct.error) as exc:
        raise ValueError('invalid NARC') from exc


def overlay(rom, index, expected_layout=None):
    off, size = struct.unpack_from('<2I', rom, 0x50)
    table = extent(rom, off, size, 'overlay table')
    if size % 32:
        raise ValueError('invalid overlay table size')
    rows = [struct.unpack_from('<8I', table, p) for p in range(0, size, 32)]
    rows = [row for row in rows if row[0] == index]
    if len(rows) != 1:
        raise ValueError('missing or duplicate overlay')
    row = rows[0]
    if expected_layout is not None and (row[1], row[3], row[4], row[5]) != expected_layout:
        raise ValueError('unqualified overlay load layout')
    if row[7] >> 24 not in (0, 1):
        raise ValueError('unsupported overlay flags')
    if not 0 < row[2] <= BLZ_MAX_DECOMPRESSA:
        raise ValueError('invalid overlay RAM size')
    raw = fat_file(rom, row[6])
    compressed = bool(row[7] >> 24 & 1)
    if compressed:
        if (row[7] & 0xffffff) != len(raw):
            raise ValueError('compressed overlay size mismatch')
        try:
            if blz_verifica_ndspy(raw, row[2]) is None:
                raise ValueError('invalid compressed overlay trailer')
            data = ndspy_decomprimi_sicuro(raw, row[2])
        except (Rifiuto, AssertionError, RuntimeError, IndexError, struct.error) as exc:
            raise ValueError('invalid compressed overlay: ' + str(exc)) from exc
    else:
        if len(raw) != row[2]:
            raise ValueError('raw overlay size mismatch')
        data = raw
    if len(data) != row[2]:
        raise ValueError('decoded overlay size mismatch')
    return row[1], data


def font_widths(raw):
    if len(raw) < 16:
        raise ValueError('truncated font header')
    _, start, count, width, height, _, _ = struct.unpack_from('<3I4B', raw)
    if not count or start < 16 or start + count > len(raw):
        raise ValueError('truncated font width metadata')
    if not width or not height or height > 32:
        raise ValueError('unexpected font geometry')
    return raw[start:start + count]


def measure(words, widths, chars, commands, limit=96):
    if not words or words[-1] != 0xffff or 0xffff in words[:-1]:
        raise ValueError('invalid terminator')
    decoded = _TEXT.render(words, chars, commands)
    if decoded['compressed_name'] or decoded['controls'] or decoded['unknown_codes'] or decoded['malformed_controls']:
        raise ValueError('unknown glyph or unsupported control')
    if any(code not in chars or not 0 < code <= len(widths) for code in words[:-1]):
        raise ValueError('glyph outside font')
    # Newline/control tokens must not masquerade as ordinary glyphs.
    if any(c in decoded['text'] for c in ('\\n', '\\r', '\\f', '\n', '\r', '\f')):
        raise ValueError('line control not allowed')
    advance = sum(widths[code - 1] for code in words[:-1])
    return {'text': decoded['text'], 'advance_px': advance, 'limit_px': limit,
            'margin_px': limit - advance, 'fits_advance': advance <= limit}


def aliases(banks, count=7):
    canonical = banks[0]
    if not banks or len(canonical) != count or any(len(bank) != count for bank in banks):
        raise ValueError('incomplete aliases')
    if any(bank != canonical for bank in banks[1:]):
        raise ValueError('alias mismatch')
    return canonical


def check_native_chain(rom):
    segments = portable.arm9_segments(rom)
    for address, size, expected in NATIVE_PINS:
        if digest(portable.read_ram(rom, segments, address, size)) != expected:
            raise ValueError('unqualified native menu chain at %#x' % address)
    _, data = overlay(rom, 1, (0x021E5900, 0x3C020, 0x02209810, 0x02209814))
    if digest(data) != OVERLAY1_SHA:
        raise ValueError('unqualified native menu overlay')


def check_renderer(rom, profile='stat7'):
    base, data = overlay(rom, 27, (0x02259F80, 0, 0x0225D46C, 0x0225D470))
    if digest(data) != OVERLAY_SHA:
        raise ValueError('unqualified renderer overlay')
    def span(address, size):
        at = address - base
        if at < 0 or at + size > len(data):
            raise ValueError('overlay address outside image')
        return data[at:at + size]
    if profile == 'stat7':
        valid_template = (span(0x0225D2F8, 56) == TEMPLATE and
                          span(0x0225D4B8 + 5 * 4, 4) == struct.pack('<I', 0x0225D2F8))
    elif profile == 'service6':
        valid_template = (digest(span(0x0225D2C8, 48)) == SERVICE6_TEMPLATE_SHA and
                          span(0x0225D4B8 + 4 * 4, 4) == struct.pack('<I', 0x0225D2C8))
    else:
        raise ValueError('unsupported menu profile')
    if not valid_template or span(0x0225C6C2, 2) != bytes.fromhex('0421'):
        raise ValueError('renderer geometry/font mismatch')


def check_script(blob, rows, profile):
    if profile == 'stat7':
        values, var, expected_count = (0, 1, 2, 4, 5, 3, 255), 0x8008, 3
    elif profile == 'service6':
        values, var, expected_count = tuple(range(6)), 0x800c, 1
    else:
        raise ValueError('unsupported menu profile')
    if len(rows) != len(values):
        raise ValueError('incomplete script mapping')
    payload = struct.pack('<H4BH', 750, 1, 1, 0, 1, var)
    payload += b''.join(struct.pack('<4H', 751, row, 255, value)
                        for row, value in zip(rows, values))
    payload += struct.pack('<H', 752)
    if blob.count(payload) != expected_count:
        raise ValueError('menu script mapping mismatch')



def run(rom, charmap, identity, language, catalogue=None, profile='stat7'):
    if profile not in ('stat7', 'service6'):
        raise ValueError('unsupported menu profile')
    rows_spec, keys = (ROWS, KEYS) if profile == 'stat7' else (SERVICE6_ROWS, SERVICE6_KEYS)
    if not isinstance(identity, dict):
        raise ValueError('identity must be an object')
    expected = identity.get('rom_sha256', '')
    if language not in ('EN', 'IT', 'FR', 'ES', 'DE') or identity.get('language') != language:
        raise ValueError('identity language mismatch')
    if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
        raise ValueError('identity requires lowercase SHA-256')
    charmap_hash = digest(Path(charmap).read_bytes())
    if charmap_hash != guide_content.CHARMAP_SHA256:
        raise ValueError('charmap SHA-256 mismatch')
    chars, commands = _TEXT.load_charmap(charmap)
    with open(rom, 'rb') as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as image:
        if digest(image) != expected:
            raise ValueError('ROM SHA-256 mismatch')
        check_native_chain(image)
        check_renderer(image, profile)
        fonts = archive(resource(image, 'a/0/1/6'))
        raw = fonts.files[4]
        if digest(raw) != FONT_SHA:
            raise ValueError('unqualified font4')
        widths = font_widths(raw)
        messages = archive(resource(image, 'a/0/2/7'))
        scripts = archive(resource(image, 'a/0/1/2'))
        banks = []
        for bank, rows, script in rows_spec:
            check_script(scripts.files[script], rows, profile)
            bank_words = Bank(messages.files[bank]).words
            banks.append([bank_words[row] for row in rows])
        words = aliases(banks, len(keys))
        installed = [dict(key=key, **measure(w, widths, chars, commands)) for key, w in zip(keys, words)]
        result = {'schema': 'training-fit/1', 'profile': profile, 'language': language, 'rom_sha256': expected,
                  'charmap_sha256': charmap_hash,
                  'font4_sha256': FONT_SHA, 'overlay1_sha256': OVERLAY1_SHA, 'overlay27_sha256': OVERLAY_SHA,
                  'installed': {'rows': installed, 'all_fit_advance': all(r['fits_advance'] for r in installed)},
                  'ink_bounds': 'not measured', 'identity_note': 'language is asserted by the supplied identity'}
        if catalogue is not None:
            content = Path(catalogue).read_bytes()
            cat = json.loads(content)
            if not isinstance(cat, dict) or not isinstance(cat.get('strings'), dict):
                raise ValueError('catalogue must be an object with strings')
            if cat.get('language') != language:
                raise ValueError('catalogue language mismatch')
            proposed = [dict(key=key, **measure(encode_text(cat['strings'][key], chars, commands), widths, chars, commands)) for key in keys]
            result['catalogue_proposal'] = {'sha256': digest(content), 'rows': proposed,
                                           'all_fit_advance': all(r['fits_advance'] for r in proposed)}
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True)
    parser.add_argument('--charmap', required=True)
    parser.add_argument('--identity', required=True, help='JSON with language and rom_sha256')
    parser.add_argument('--language', required=True)
    parser.add_argument('--profile', choices=('stat7', 'service6'), default='stat7')
    parser.add_argument('--catalogue', help='optional catalogue proposal; does not replace installed check')
    args = parser.parse_args(argv)
    try:
        result = run(args.rom, args.charmap, json.loads(Path(args.identity).read_text()), args.language, args.catalogue, args.profile)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(not result['installed']['all_fit_advance'] or
                   ('catalogue_proposal' in result and not result['catalogue_proposal']['all_fit_advance']))
    except (ValueError, KeyError, IndexError, OSError, struct.error, TypeError, Rifiuto) as exc:
        print(json.dumps({'schema': 'training-fit/1', 'status': 'error', 'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
