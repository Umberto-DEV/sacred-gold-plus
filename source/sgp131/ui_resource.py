"""Build one UIR2 NARC38 replacement, entirely in memory.

Input is an exact supported V4 ROM and caller-owned, already encoded game
words. This module neither authors/encodes UI copy nor installs a ROM file.
The private packer accepts synthetic parts for ROM-free format tests; it does
not bypass the public entry point's immutable baseline and source-asset pins.
"""
import hashlib
import struct
import zlib
from typing import Dict, Tuple

from ndspy.lz10 import decompress
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from translation.message_codec import Bank, unpack_name
from . import baseline

MEMBER_MAGIC = b'UIR2'
CONFIG_MAGIC = b'URC2'
VERSION = 2
HEADER_BYTES = 128
ASSET_BYTES = 48320
TEXT_DIRECTORY_OFFSET = 48448
TEXT_ENTRY_BYTES = 8
TEXT_FORMAT = 1
ASSET_FORMAT_FLAGS = 7  # 2bpp storage, 2x2 tiles, 16x16 cell; variable advance.
MAX_MEMBER_BYTES = 69632
MAX_TEXT_ENTRIES = 1024
MAX_UNITS_PER_ENTRY = 2048
LANGUAGE_IDS = {'EN': 0, 'IT': 1, 'FR': 2, 'ES': 3, 'DE': 4}
AuthoredText = Dict[int, Tuple[int, ...]]

_SOURCE_HASHES = {
    'frames': 'f3eb794fe2ea3cd436ec7b3582c8b3df7340d11961c9c3a9d7e357e230289a88',
    'font': {'EN': 'e71080936aaa95ad9de8b996345fc98eb5bf537e043597c7826cf7607d4d27ee',
             'IT': 'ed161ec95324432f00e8fa31d40b3ecabc2aadd290667d7a97c118d692375219'},
    'font0': '9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73',
    'widths': '9056ed8029423336c0c7d7cf88c8e04841f09849bf431ce6d1c6ebebd4358e84',
    'glyphs': 'e63ce41723f91f46285dff480b1a66666e1a1f861c644abfa0acd24cf36e3a83',
    'font_palette': 'ab468d27a91147c79335455bfe25e7d7d8995a11fa6c8a61542e8862882216cb',
    'assets': '96490ff4d596a9c21f4a8d8ac7a42a4c7c57834bbfbcd8a7ef0b2a0aed14e102',
    'bank237': {'EN': '3cd76df795a79b5cd5f9129a1fdc4163f72189d9430fcdd9eb7c631b10c1bcee',
                'IT': '4b9c30a450a2bf7ffafbe448865ec2cadeade4af7b328c25c90ccb465d60f594'},
    'species': {'EN': 'fabb04d7ac4913344bfa706100ba0f9cf55681a54055cff58ff3a34dbdb27acf',
                'IT': '38be65aceb381b6277a617e3249a8157e0cb291ceec197bd8690f233810695c5'},
}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _pin(data, key, language):
    expected = _SOURCE_HASHES[key]
    if isinstance(expected, dict):
        expected = expected[language]
    if _sha(data) != expected:
        raise ValueError('unexpected canonical source ' + key)


def _narc(data):
    """Parse chunk sizes and every span without reconstructing old GMIF bytes."""
    if len(data) < 28 or struct.unpack_from('<4sHHIHH', data) != (b'NARC', 0xFFFE, 0x100, len(data), 16, 3):
        raise ValueError('invalid NARC header')
    cursor, chunks = 16, []
    for magic in (b'BTAF', b'BTNF', b'GMIF'):
        if cursor + 8 > len(data):
            raise ValueError('truncated NARC chunk')
        name, size = struct.unpack_from('<4sI', data, cursor)
        if name != magic or size < 8 or size > len(data) - cursor:
            raise ValueError('invalid NARC chunk bounds')
        chunks.append(data[cursor:cursor + size])
        cursor += size
    if cursor != len(data) or len(chunks[0]) < 12:
        raise ValueError('invalid NARC chunk sum')
    count, reserved = struct.unpack_from('<HH', chunks[0], 8)
    if reserved or len(chunks[0]) != 12 + 8 * count:
        raise ValueError('invalid NARC allocation table')
    image = chunks[2][8:]
    spans, end = [], 0
    for index in range(count):
        start, stop = struct.unpack_from('<II', chunks[0], 12 + 8 * index)
        if not end <= start <= stop <= len(image):
            raise ValueError('invalid NARC member bounds/order')
        spans.append((start, stop))
        end = stop
    return chunks, spans, image


def _words(words, species=False):
    if not isinstance(words, tuple) or not 1 <= len(words) <= MAX_UNITS_PER_ENTRY:
        raise ValueError('text must be a tuple of 1..2048 units')
    if any(type(w) is not int for w in words) or words[-1] != 65535:
        raise ValueError('text requires integer glyphs and final EOS')
    if any(not (1 <= w <= 509 or (w == 0xE000 and not species)) for w in words[:-1]):
        raise ValueError('text has early EOS or forbidden glyph/control')
    return struct.pack('<%dH' % len(words), *words)


def _authored_bytes(authored):
    """Canonical digest input: ascending IDs, each <u16 ID,u16 units,units*u16>."""
    if not isinstance(authored, dict):
        raise ValueError('authored text must be a dict')
    if any(type(key) is not int or not 1 <= key <= 0xFFF for key in authored):
        raise ValueError('authored ID outside 1..0FFF')
    result = bytearray()
    for key in sorted(authored):
        encoded = _words(authored[key])
        result.extend(struct.pack('<HH', key, len(authored[key])))
        result.extend(encoded)
    return bytes(result)


def _pack_member(language, assets, species, authored, widths_crc):
    _authored_bytes(authored)
    if language not in LANGUAGE_IDS or len(assets) != ASSET_BYTES:
        raise ValueError('invalid resource language or asset size')
    if type(widths_crc) is not int or not 0 <= widths_crc <= 0xFFFFFFFF:
        raise ValueError('invalid widths CRC')
    if not isinstance(species, dict) or set(species) != set(range(1, 494)) or any(type(k) is not int for k in species):
        raise ValueError('resource requires exactly species 1..493')
    for words in species.values():
        _words(words, species=True)
    entries = sorted(list(authored.items()) + [(0x1000 + k, v) for k, v in species.items()])
    count = len(entries)
    if not 493 <= count <= MAX_TEXT_ENTRIES:
        raise ValueError('too many text entries')
    text_start = TEXT_DIRECTORY_OFFSET + TEXT_ENTRY_BYTES * count
    directory, text = bytearray(), bytearray()
    for key, words in entries:
        directory.extend(struct.pack('<HHI', key, len(words), text_start + len(text)))
        text.extend(_words(words))
    length = (text_start + len(text) + 3) & ~3
    if length > MAX_MEMBER_BYTES:
        raise ValueError('UI resource member exceeds 69632-byte cap')
    header = bytearray(HEADER_BYTES)
    struct.pack_into('<4sHH14I', header, 0, MEMBER_MAGIC, VERSION, HEADER_BYTES,
                     length, LANGUAGE_IDS[language], ASSET_BYTES, 20, 128, 608,
                     576, 32, 12288, 32576, 44864, 32, widths_crc, ASSET_FORMAT_FLAGS)
    header[64:96] = hashlib.sha256(assets).digest()
    struct.pack_into('<8I', header, 96, TEXT_DIRECTORY_OFFSET, count, 8 * count,
                     text_start, len(text), TEXT_FORMAT, TEXT_ENTRY_BYTES, 0)
    return bytes(header + assets + directory + text + bytes(length - text_start - len(text)))


def _append_member(original, member):
    chunks, spans, image = _narc(original)
    if len(original) != 35372 or len(spans) != 51 or len(image) != 34912 or len(chunks[1]) != 16:
        raise ValueError('unexpected original NARC38 geometry')
    if not 128 <= len(member) <= MAX_MEMBER_BYTES or len(member) % 4:
        raise ValueError('invalid appended member length')
    allocation = (struct.pack('<4sIHH', b'BTAF', 428, 52, 0) + chunks[0][12:]
                  + struct.pack('<II', 34912, 34912 + len(member)))
    return (struct.pack('<4sHHIHH', b'NARC', 0xFFFE, 0x100, 35380 + len(member), 16, 3)
            + allocation + chunks[1] + struct.pack('<4sI', b'GMIF', 34920 + len(member))
            + image + member)


def _native_ball(raw):
    if _sha(raw) != 'fa5f2defea95ffb41ef5e408c85e5f8767e0da08df07c31345a8f4b8c320073a':
        raise ValueError('unexpected native battle archive')
    # The immutable native battle archive has noncanonical GMIF size metadata;
    # ndspy reads its FAT member bounds. Exact archive+member pins gate extraction.
    members = NARC(raw).files
    pins = ((246, '9905393b4ea6c1f5442f4c1b1375e5a4410105bb95bd28433e92602aa4fbc570'),
            (28, '84f5d8c16f1635fe696859087350bbb04a6d49a7efa2fdc9b52d181f78f2b1db'),
            (43, '56ec9bac0baed0d8a13403fc5677d362a0c8ec2e60dacafa8e2a1516ce2533b9'))
    for index, digest in pins:
        if _sha(members[index]) != digest: raise ValueError('unexpected native ball member')
    chars, screen = decompress(members[28]), decompress(members[43])
    if (_sha(chars), _sha(screen)) != ('385bc7cee3327b0f6e0509821564ff7ff18bdf277cac187374478da48666370e', '2bd8ab82d47f5c07c95b13a526bd6d47120483b72f7138d5d3e4affb8fb55bc5'):
        raise ValueError('unexpected native ball decode')
    tiles, mapping, palette = chars[48:32816], screen[36:2084], members[246][40:72]
    entries = struct.unpack('<1024H', mapping)
    indices = sorted({entry & 1023 for entry in entries})
    if len(indices) != 46 or any(entry >> 12 for entry in entries):
        raise ValueError('unexpected native ball geometry')
    remap = {tile: index for index, tile in enumerate(indices)}
    compact = (b''.join(tiles[tile*32:tile*32+32] for tile in indices)
               + struct.pack('<1024H', *(remap[e & 1023] | (e & 0xFC00) for e in entries)) + palette)
    if len(compact) != 3552 or _sha(compact) != 'c0af1b047d21fa879f58f8ecc7db324b3d3f1a5125720a5e33876dadac3633da':
        raise ValueError('unexpected compact native ball')
    return compact


def _source(v4, language):
    rom = NintendoDSRom(v4)
    files = {}
    for label, path, expected_id in (('frames', 'a/0/3/8', 167), ('font', 'a/0/1/6', 145),
                                     ('messages', 'a/0/2/7', 156), ('battle', 'a/0/0/7', 136)):
        if rom.filenames.idOf(path) != expected_id:
            raise ValueError('unexpected source file ID for ' + path)
        files[label] = bytes(rom.files[expected_id])
    _pin(files['frames'], 'frames', language)
    _pin(files['font'], 'font', language)
    _, spans, image = _narc(files['frames'])
    if len(spans) != 51:
        raise ValueError('unexpected frame member count')
    frames = [image[a:b] for a, b in spans]
    _, spans, image = _narc(files['font'])
    if len(spans) != 11:
        raise ValueError('unexpected font member count')
    fonts = [image[a:b] for a, b in spans]
    font = fonts[0]
    if len(font) != 33101 or font[:16] != bytes.fromhex('10000000507f0000fd01000010100202'):
        raise ValueError('unexpected font0 shape')
    _pin(font, 'font0', language)
    glyphs, widths = font[16:0x7F50], font[0x7F50:]
    _pin(glyphs, 'glyphs', language)
    _pin(widths, 'widths', language)
    assets = bytearray()
    for i in range(20):
        tile, palette = frames[i + 2], frames[i + 26]
        if len(tile) != 640 or tile[:4] != b'RGCN' or len(palette) != 552 or palette[:4] != b'RLCN':
            raise ValueError('unexpected native frame shape')
        assets.extend(tile[0x30:0x270])
        assets.extend(palette[0x28:0x48])
    if len(fonts[7]) != 90 or fonts[7][:4] != b'RLCN':
        raise ValueError('unexpected font palette shape')
    font_palette = fonts[7][0x28:0x48]
    _pin(font_palette, 'font_palette', language)
    assets.extend(glyphs + font_palette + _native_ball(files['battle']))
    assets = bytes(assets)
    _pin(assets, 'assets', language)
    _, spans, image = _narc(files['messages'])
    if len(spans) != 830:
        raise ValueError('unexpected message bank count')
    a, b = spans[237]
    bank = image[a:b]
    _pin(bank, 'bank237', language)
    decoded = Bank(bank).words
    if len(decoded) != 496:
        raise ValueError('unexpected species bank count')
    species = {i: tuple(unpack_name(decoded[i])) for i in range(1, 494)}
    expanded = b''.join(_words(species[i], species=True) for i in range(1, 494))
    _pin(expanded, 'species', language)
    if len(expanded) != 8172:
        raise ValueError('unexpected expanded species size')
    source_hashes = {key: _sha(value) for key, value in files.items()}
    source_hashes.update(rom=_sha(v4), font0=_sha(font), glyphs=_sha(glyphs), widths=_sha(widths),
                         font_palette=_sha(font_palette), bank237=_sha(bank), species=_sha(expanded))
    return files['frames'], assets, species, zlib.crc32(widths), source_hashes


def _receipt(replacement, language, assets, species, authored, widths_crc):
    member = replacement[35380:]
    count = 493 + len(authored)
    species_bytes = sum(len(v) * 2 for v in species.values())
    authored_bytes = sum(len(v) * 2 for v in authored.values())
    config_names = ('magic', 'version', 'language', 'narc_bytes', 'prefix_bytes', 'member_index',
                    'member_offset', 'member_bytes', 'asset_bytes', 'prefix_crc32', 'member_crc32',
                    'widths_crc32', 'glyph_count', 'glyph_bytes', 'schema_flags', 'reserved')
    config = (0x32435255, 2, LANGUAGE_IDS[language], len(replacement), 468, 51, 35380,
              len(member), 48320, zlib.crc32(replacement[:468]), zlib.crc32(member), widths_crc, 509, 64, 7, 0)
    return dict(language=language, member_bytes=len(member), narc_bytes=len(replacement),
                text_entries=count, species_entries=493, authored_entries=len(authored),
                text_directory_bytes=count * 8, species_text_bytes=species_bytes,
                authored_text_bytes=authored_bytes, text_data_bytes=species_bytes + authored_bytes,
                padding_bytes=len(member) - (48448 + count * 8 + species_bytes + authored_bytes),
                budget_remaining=69632 - len(member), asset_bytes=48320,
                authored_glyph_sha256=_sha(_authored_bytes(authored)), asset_sha256=_sha(assets),
                asset_crc32=zlib.crc32(assets), prefix_crc32=config[9], member_crc32=config[10],
                widths_crc32=widths_crc, member_sha256=_sha(member), narc_sha256=_sha(replacement),
                config_fields=dict(zip(config_names, config)), config_hex=struct.pack('<16I', *config).hex())


def compile_resource(v4: bytes, authored: AuthoredText) -> Tuple[bytes, dict]:
    """Return replacement NARC38 bytes and metadata; never write a file."""
    language = baseline.identify(v4)
    # Reject caller text before extracting/copying canonical resources.
    _authored_bytes(authored)
    original, assets, species, widths_crc, hashes = _source(v4, language)
    member = _pack_member(language, assets, species, authored, widths_crc)
    replacement = _append_member(original, member)
    receipt = _receipt(replacement, language, assets, species, authored, widths_crc)
    receipt['source_sha256'] = hashes
    return replacement, receipt
