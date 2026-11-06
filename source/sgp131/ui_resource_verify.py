"""Independently read back UIR2 bytes against the canonical input and caller text.

No compiler import, layout helper, receipt or recompile-to-compare authorizes
output. Numeric schema rules are intentionally restated here. Generic source
NARC and message codecs are allowed; output structure is read directly.
"""
import hashlib
import struct
import zlib

from ndspy import fnt
from ndspy.lz10 import decompress
from ndspy.narc import NARC
from translation.message_codec import Bank, unpack_name
from . import baseline


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _archive(raw):
    _require(len(raw) >= 28, 'short archive')
    _require(raw[:8] == b'NARC\xfe\xff\x00\x01', 'archive magic/version')
    _require(struct.unpack_from('<IHH', raw, 8) == (len(raw), 16, 3), 'archive size/header')
    offset, blocks = 16, []
    for name in (b'BTAF', b'BTNF', b'GMIF'):
        _require(offset + 8 <= len(raw), 'archive truncated block')
        size = int.from_bytes(raw[offset + 4:offset + 8], 'little')
        _require(raw[offset:offset + 4] == name and 8 <= size <= len(raw) - offset, 'archive block bounds')
        blocks.append((offset, size))
        offset += size
    _require(offset == len(raw), 'archive hidden tail')
    table_start, table_bytes = blocks[0]
    _require(table_bytes >= 12, 'short allocation table')
    count, reserved = struct.unpack_from('<HH', raw, table_start + 8)
    _require(reserved == 0 and table_bytes == 12 + 8 * count, 'allocation count/size')
    data_start = blocks[2][0] + 8
    image = raw[data_start:]
    spans, previous = [], 0
    for index in range(count):
        start, end = struct.unpack_from('<II', raw, table_start + 12 + index * 8)
        _require(previous <= start <= end <= len(image), 'member span/order')
        spans.append((start, end))
        previous = end
    return spans, raw[blocks[1][0]:blocks[1][0] + blocks[1][1]], image, data_start


def _expected_text(species, authored):
    _require(isinstance(authored, dict), 'authored mapping required')
    _require(all(type(k) is int and 1 <= k <= 4095 for k in authored), 'authored key domain')
    _require(isinstance(species, dict) and all(type(k) is int for k in species)
             and set(species) == set(range(1, 494)), 'exact species set required')
    expected, canonical = {}, bytearray()
    for key, words in list(authored.items()) + [(4096 + k, v) for k, v in species.items()]:
        _require(isinstance(words, tuple) and 1 <= len(words) <= 2048, 'expected text length')
        _require(all(type(w) is int for w in words) and words[-1] == 65535, 'expected EOS/type')
        _require(all(1 <= w <= 509 or (w == 57344 and key < 4096) for w in words[:-1]), 'expected glyph domain')
        expected[key] = words
    _require(493 <= len(expected) <= 1024, 'expected entry count')
    for key in sorted(authored):
        words = authored[key]
        canonical.extend(struct.pack('<HH', key, len(words)))
        canonical.extend(struct.pack('<%dH' % len(words), *words))
    return expected, bytes(canonical)


def _verify_parts(original, replacement, language, assets, species, authored, widths_crc):
    expected, authored_source = _expected_text(species, authored)
    _require(language in ('EN', 'IT') and len(assets) == 48320, 'expected language/assets')
    _require(type(widths_crc) is int and 0 <= widths_crc <= 0xFFFFFFFF, 'expected widths CRC')
    old_spans, old_names, old_image, old_base = _archive(original)
    spans, names, image, base = _archive(replacement)
    _require(len(original) == 35372 and len(old_spans) == 51 and old_base == 460
             and len(old_names) == 16 and len(old_image) == 34912, 'original NARC38 geometry')
    _require(len(spans) == 52 and base == 468 and names == old_names, 'replacement prefix geometry')
    _require(spans[:51] == old_spans, 'old allocation entries changed')
    _require(image[:34912] == old_image, 'old GMIF bytes changed')
    for (a, b), (c, d) in zip(old_spans, spans[:51]):
        _require(old_image[a:b] == image[c:d], 'old member changed')
    _require(spans[51] == (34912, len(image)), 'new member span/hidden tail')
    member = image[34912:]
    length = len(member)
    _require(128 <= length <= 69632 and length % 4 == 0 and len(replacement) == 35380 + length,
             'complete member cap/alignment')
    lang = 0 if language == 'EN' else 1
    fixed = (b'UIR2', 2, 128, length, lang, 48320, 20, 128, 608, 576, 32,
             12288, 32576, 44864, 32, widths_crc, 7)
    _require(struct.unpack_from('<4sHH14I', member) == fixed, 'member fixed header')
    _require(member[128:48448] == assets, 'asset slice differs from input')
    _require(member[64:96] == hashlib.sha256(assets).digest(), 'asset SHA label')
    directory, count, table_bytes, data, data_bytes, text_format, entry_bytes, reserved = struct.unpack_from('<8I', member, 96)
    _require(directory == 48448 and 493 <= count <= 1024 and count == len(expected), 'text directory/count')
    _require(table_bytes == count * 8 and data == directory + table_bytes, 'text table size/offset')
    _require(data_bytes > 0 and data_bytes % 2 == 0 and data <= length
             and data_bytes <= length - data, 'text data bounds')
    end = data + data_bytes
    _require(length == (end + 3) // 4 * 4 and member[end:] in (b'', b'\0\0'), 'padding/hidden text')
    _require((text_format, entry_bytes, reserved) == (1, 8, 0), 'text format/reserved')
    previous, cursor, found = 0, data, set()
    for index in range(count):
        key, units, offset = struct.unpack_from('<HHI', member, directory + index * 8)
        _require(key > previous and key in expected, 'text key domain/order/coverage')
        _require(1 <= units <= 2048 and offset % 2 == 0 and offset == cursor, 'text units/contiguity')
        _require(offset <= end and units * 2 <= end - offset, 'text slice bounds')
        words = struct.unpack_from('<%dH' % units, member, offset)
        _require(words[-1] == 65535 and all(1 <= w <= 509 or w == 57344 for w in words[:-1]), 'text glyph/EOS')
        _require(words == expected[key], 'text differs from canonical species or authored words')
        cursor += units * 2
        previous = key
        found.add(key)
    _require(found == set(expected) and cursor == end, 'missing species/authored entry or hidden string')
    species_bytes = sum(len(v) * 2 for v in species.values())
    authored_bytes = sum(len(v) * 2 for v in authored.values())
    _require(data_bytes == species_bytes + authored_bytes, 'text total bytes')
    prefix_crc, member_crc = zlib.crc32(replacement[:468]), zlib.crc32(member)
    fields = dict(magic=0x32435255, version=2, language=lang, narc_bytes=len(replacement), prefix_bytes=468,
                  member_index=51, member_offset=35380, member_bytes=length, asset_bytes=48320,
                  prefix_crc32=prefix_crc, member_crc32=member_crc, widths_crc32=widths_crc,
                  glyph_count=509, glyph_bytes=64, schema_flags=7, reserved=0)
    return dict(language=language, member_bytes=length, narc_bytes=len(replacement), text_entries=count,
                species_entries=493, authored_entries=len(authored), text_directory_bytes=table_bytes,
                species_text_bytes=species_bytes, authored_text_bytes=authored_bytes, text_data_bytes=data_bytes,
                padding_bytes=length - end, budget_remaining=69632 - length, asset_bytes=48320,
                authored_glyph_sha256=_digest(authored_source), asset_sha256=_digest(assets),
                asset_crc32=zlib.crc32(assets), prefix_crc32=prefix_crc, member_crc32=member_crc,
                widths_crc32=widths_crc, member_sha256=_digest(member), narc_sha256=_digest(replacement),
                config_fields=fields, config_hex=struct.pack('<16I', *fields.values()).hex())


def _read_canonical(v4, language):
    """Use the input FAT and FNT, independently of the compiler's ROM parser."""
    fnt_at, fnt_size, fat_at, fat_size = struct.unpack_from('<4I', v4, 0x40)
    _require(fat_size == 4104 and fnt_size == 2902, 'source filesystem shape')
    filenames = fnt.load(v4[fnt_at:fnt_at + fnt_size])
    source = {}
    for label, path, file_id in (('frames', 'a/0/3/8', 167), ('font', 'a/0/1/6', 145), ('messages', 'a/0/2/7', 156), ('battle', 'a/0/0/7', 136)):
        _require(filenames.idOf(path) == file_id, 'source file ID')
        start, stop = struct.unpack_from('<II', v4, fat_at + 8 * file_id)
        _require(0 <= start <= stop <= len(v4), 'source FAT bounds')
        source[label] = v4[start:stop]
    pins = {
        'battle': 'fa5f2defea95ffb41ef5e408c85e5f8767e0da08df07c31345a8f4b8c320073a',
        'frames': 'f3eb794fe2ea3cd436ec7b3582c8b3df7340d11961c9c3a9d7e357e230289a88',
        'font': ('e71080936aaa95ad9de8b996345fc98eb5bf537e043597c7826cf7607d4d27ee' if language == 'EN' else
                 'ed161ec95324432f00e8fa31d40b3ecabc2aadd290667d7a97c118d692375219'),
    }
    for key, digest in pins.items():
        _require(_digest(source[key]) == digest, 'canonical source ' + key)
    frame_members = NARC(source['frames']).files
    font_members = NARC(source['font']).files
    _require(len(frame_members) == 51 and len(font_members) == 11, 'source archive counts')
    font0 = bytes(font_members[0])
    _require(len(font0) == 33101 and font0[:16].hex() == '10000000507f0000fd01000010100202', 'font0 shape')
    glyphs, widths = font0[16:32592], font0[32592:]
    font_palette = bytes(font_members[7][40:72])
    _require(len(font_members[7]) == 90 and font_members[7][:4] == b'RLCN', 'font palette shape')
    graphics = []
    for index in range(20):
        tiles = frame_members[index + 2]
        palette = frame_members[index + 26]
        _require(len(tiles) == 640 and tiles[:4] == b'RGCN' and len(palette) == 552 and palette[:4] == b'RLCN', 'frame shape')
        graphics.extend((bytes(tiles[48:624]), bytes(palette[40:72])))
    native = NARC(source['battle']).files
    for index, digest in ((246, '9905393b4ea6c1f5442f4c1b1375e5a4410105bb95bd28433e92602aa4fbc570'),
                           (28, '84f5d8c16f1635fe696859087350bbb04a6d49a7efa2fdc9b52d181f78f2b1db'),
                           (43, '56ec9bac0baed0d8a13403fc5677d362a0c8ec2e60dacafa8e2a1516ce2533b9')):
        _require(_digest(native[index]) == digest, 'native ball member pin')
    characters = decompress(native[28])[48:32816]
    screen = struct.unpack('<1024H', decompress(native[43])[36:2084])
    tile_ids = sorted(set(value & 1023 for value in screen))
    _require(len(tile_ids) == 46 and all(value < 4096 for value in screen), 'native ball geometry')
    compact_tiles = b''.join(characters[index*32:(index+1)*32] for index in tile_ids)
    compact_map = [tile_ids.index(value & 1023) + (value & 3072) for value in screen]
    compact = compact_tiles + struct.pack('<1024H', *compact_map) + bytes(native[246][40:72])
    _require(_digest(compact) == 'c0af1b047d21fa879f58f8ecc7db324b3d3f1a5125720a5e33876dadac3633da', 'native ball compact pin')
    # Independent pixel equality includes all 256x256 pixels and both flip bits.
    for position in range(65536):
        y, x = divmod(position, 256)
        old, new = screen[(y//8)*32+x//8], compact_map[(y//8)*32+x//8]
        samples = []
        for entry, tiles in ((old, characters), (new, compact_tiles)):
            px = 7-x%8 if entry & 1024 else x%8
            py = 7-y%8 if entry & 2048 else y%8
            samples.append((tiles[(entry & 1023)*32+py*4+px//2] >> (4*(px%2))) & 15)
        _require(samples[0] == samples[1], 'native ball pixel equality')
    assets = b''.join(graphics) + glyphs + font_palette + compact
    banks = NARC(source['messages']).files
    _require(len(banks) == 830, 'message archive count')
    bank = bytes(banks[237])
    decoded = Bank(bank).words
    _require(len(decoded) == 496, 'species bank count')
    species = {i: tuple(unpack_name(decoded[i])) for i in range(1, 494)}
    expanded = b''.join(struct.pack('<%dH' % len(species[i]), *species[i]) for i in range(1, 494))
    measured = dict(font0=font0, glyphs=glyphs, widths=widths, font_palette=font_palette,
                    assets=assets, bank237=bank, species=expanded)
    expected_hashes = {
        'font0': '9a17de3036f4aac8540163e560a60d83b7facde78d0ec41e688374fdbf669e73',
        'glyphs': 'e63ce41723f91f46285dff480b1a66666e1a1f861c644abfa0acd24cf36e3a83',
        'widths': '9056ed8029423336c0c7d7cf88c8e04841f09849bf431ce6d1c6ebebd4358e84',
        'font_palette': 'ab468d27a91147c79335455bfe25e7d7d8995a11fa6c8a61542e8862882216cb',
        'assets': '96490ff4d596a9c21f4a8d8ac7a42a4c7c57834bbfbcd8a7ef0b2a0aed14e102',
        'bank237': ('3cd76df795a79b5cd5f9129a1fdc4163f72189d9430fcdd9eb7c631b10c1bcee' if language == 'EN' else
                    '4b9c30a450a2bf7ffafbe448865ec2cadeade4af7b328c25c90ccb465d60f594'),
        'species': ('fabb04d7ac4913344bfa706100ba0f9cf55681a54055cff58ff3a34dbdb27acf' if language == 'EN' else
                    '38be65aceb381b6277a617e3249a8157e0cb291ceec197bd8690f233810695c5'),
    }
    for key, expected in expected_hashes.items():
        _require(_digest(measured[key]) == expected, 'canonical source ' + key)
    _require(len(expanded) == 8172 and zlib.crc32(widths) == 0x885AB7FC, 'source text/width measures')
    hashes = {key: _digest(value) for key, value in source.items()}
    hashes.update({key: _digest(value) for key, value in measured.items() if key != 'assets'})
    hashes['rom'] = _digest(v4)
    return source['frames'], assets, species, zlib.crc32(widths), hashes


def verify_resource(v4: bytes, replacement: bytes, authored: dict) -> dict:
    """Read/validate replacement without trusting any compiler receipt."""
    language = baseline.identify(v4)
    original, assets, species, widths_crc, hashes = _read_canonical(v4, language)
    report = _verify_parts(original, replacement, language, assets, species, authored, widths_crc)
    report['source_sha256'] = hashes
    return report
