"""Repair HG-T10: select the Lugia cinematic assets from the scene map.

HeartGold's retail code reads the cartridge version while running the shared
Whirl Islands/Bell Tower cutscene machinery.  Sacred Gold Plus can expose the
opposite-title Lugia scene, so that read selects HeartGold camera resources for
the SoulSilver-authored scene.  This stage makes the decision local and exact:
map 244 uses scene version 8; every other map keeps HeartGold version 7.

The repair rewrites three complete seams inside compressed overlay 2.  It does
not use resident ARM9 space and changes neither ROM geometry nor save data.
"""
import hashlib
import struct

from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi
from sgp12.rom import Rom, bl_decode


LANGUAGES = ('EN', 'IT')
STAGE = 'legendary-scene-version'
OVERLAY_ID = 2
OVERLAY_RAM = 0x02245B80
OVERLAY_BYTES = 58016
COMPRESSED_BYTES = 42700
STATIC_INIT_RANGE = (0x02253D7C, 0x02253D80)

OVERLAY_PREIMAGE_SHA256 = '4309c4c9c28cac8d1aaa2519db059717cbe02dc78ce6500fb27b3345a9881d3b'
OVERLAY_POSTIMAGE_SHA256 = 'c6bd588b571578410cd7a0acef088abd1613b974d6c604acaf16f2fb63bc4093'
COMPRESSED_PREIMAGE_SHA256 = '06a905ad2e60c67ef948eb684e716d4800f9343fe1c8fb6ddca9fa08e865d220'
COMPRESSED_POSTIMAGE_SHA256 = '3032e24e40583cc3af4aeea1bbcad5cc6f32211910e9adafd2885a43e2f20a2f'

LANGUAGE_ANCHOR_FILE = 137
LANGUAGE_ANCHORS = {
    'EN': '60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82',
    'IT': 'edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233',
}

CLEAR_FUNCTION = 0x02250A60
CLEAR_PREIMAGE = bytes.fromhex(
    '38b586b0051c04202821caf52ff8696848626868696a446a0420c8f5cbfa'
    'a060104800786062696a03a8d2f5d1fd03ab221c03cb0c3203c218681060'
    '696a00a8d2f5cefd00ab221c03cb183203c218681060686840682060201c'
    '00f079f806b038bdc0466c560f02')
CLEAR_POSTIMAGE = bytes.fromhex(
    '70b5051c6e6804202821caf52ff87062041c0420696ac8f5cdfaa06007212b'
    '6a1b88f42b00d101316162201c0c30696ad2f5cefd201c1830696ad2f5d1'
    'fd70682060201c00f084f870bdc046c046c046c046c046c046c046c046c0'
    '46c046c046c046c046c046c046')
CLEAR_SELECTOR_OFFSET = 28
CLEAR_CALL_OFFSETS = (10, 22, 48, 58, 68)
CLEAR_CALL_TARGETS = (0x0201AACC, 0x02019014, 0x02023630, 0x02023640,
                      0x02250BB0)

BIRD_FUNCTION = 0x022515A4
BIRD_PREIMAGE = bytes.fromhex(
    '10b5041c0420e421c9f58efa021c05480178101ce030018020690349fef5b6'
    'ff10bdc0466c560f02')
BIRD_POSTIMAGE = bytes.fromhex(
    '10b5041c0420e421c9f58efa021c0721236a1b88f42b00d10131e023d15220'
    '690149fef5b3ff10bd')
BIRD_SELECTOR_OFFSET = 14
BIRD_CALL_OFFSETS = (8, 34)
BIRD_CALL_TARGETS = (0x0201AACC, 0x02050530)
BIRD_TASK_CALL_OFFSET = 34
TASK_MANAGER_CALL = 0x02050530

LUGIA_FUNCTION = 0x02251D06
LUGIA_PREIMAGE = bytes.fromhex('29480078')
LUGIA_POSTIMAGE = bytes.fromhex('0820c046')

PATCHES = (
    (CLEAR_FUNCTION, CLEAR_PREIMAGE, CLEAR_POSTIMAGE),
    (BIRD_FUNCTION, BIRD_PREIMAGE, BIRD_POSTIMAGE),
    (LUGIA_FUNCTION, LUGIA_PREIMAGE, LUGIA_POSTIMAGE),
)


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('Legendary scene version: ' + message)


def select_scene_version(map_id):
    """Mirror the installed Thumb selector for test and evidence readers."""
    return 8 if (int(map_id) & 0xFFFF) == 244 else 7


def _decode_calls(function, code, offsets):
    return tuple(bl_decode(function + offset, code[offset:offset + 4])
                 for offset in offsets)


def decode_clear_calls(code):
    return _decode_calls(CLEAR_FUNCTION, bytes(code), CLEAR_CALL_OFFSETS)


def decode_bird_calls(code):
    return _decode_calls(BIRD_FUNCTION, bytes(code), BIRD_CALL_OFFSETS)


def _selector_is_exact(code, offset):
    # movs r1,#7; ldr r3,[r4/r5,#0x20]; ldrh r3,[r3]; cmp r3,#244;
    # bne +0; adds r1,#1
    return (code[offset:offset + 2] == bytes.fromhex('0721')
            and code[offset + 6:offset + 8] == bytes.fromhex('f42b')
            and code[offset + 8:offset + 10] == bytes.fromhex('00d1')
            and code[offset + 10:offset + 12] == bytes.fromhex('0131'))


def check_clear_postimage(code):
    code = bytes(code)
    return (code == CLEAR_POSTIMAGE
            and _selector_is_exact(code, CLEAR_SELECTOR_OFFSET)
            and decode_clear_calls(code) == CLEAR_CALL_TARGETS)


def check_bird_postimage(code):
    code = bytes(code)
    return (code == BIRD_POSTIMAGE
            and _selector_is_exact(code, BIRD_SELECTOR_OFFSET)
            and decode_bird_calls(code) == BIRD_CALL_TARGETS)


def check_lugia_postimage(code):
    return bytes(code) == LUGIA_POSTIMAGE


def _language_anchor(data, language):
    try:
        fat, fat_bytes = struct.unpack_from('<II', data, 0x48)
        _need(fat_bytes % 8 == 0 and fat_bytes // 8 > LANGUAGE_ANCHOR_FILE,
              'language anchor FAT')
        entry = fat + LANGUAGE_ANCHOR_FILE * 8
        _need(0 <= fat <= entry and entry + 8 <= len(data),
              'language anchor FAT')
        start, end = struct.unpack_from('<II', data, entry)
        _need(0 <= start < end <= len(data), 'language anchor extent')
    except (struct.error, TypeError):
        raise ValueError('Legendary scene version: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')
    return start, end


def _overlay(data, expected=None):
    try:
        rom = Rom(data)
        entry, stream, image = rom.immagine_overlay(OVERLAY_ID)
        fat = rom.voce_fat(entry['file_id'])
    except (ValueError, struct.error, IndexError) as error:
        raise ValueError('Legendary scene version: overlay geometry') from error
    _need(entry['id'] == OVERLAY_ID and entry['file_id'] == OVERLAY_ID,
          'overlay identity')
    _need(entry['ram'] == OVERLAY_RAM and entry['ram_size'] == OVERLAY_BYTES
          and entry['bss_size'] == 0, 'overlay RAM geometry')
    _need(entry['compresso'] and entry['dim_compressa'] == COMPRESSED_BYTES,
          'overlay compression geometry')
    _need((entry['static_init_start'], entry['static_init_end'])
          == STATIC_INIT_RANGE, 'overlay static initializer range')
    _need(fat['bytes'] == COMPRESSED_BYTES and len(stream) == COMPRESSED_BYTES,
          'overlay FAT extent')
    if expected == 'pre':
        _need(_sha(stream) == COMPRESSED_PREIMAGE_SHA256,
              'compressed overlay preimage differs')
        _need(_sha(image) == OVERLAY_PREIMAGE_SHA256, 'overlay preimage differs')
    elif expected == 'post':
        _need(_sha(stream) == COMPRESSED_POSTIMAGE_SHA256,
              'compressed overlay postimage differs')
        _need(_sha(image) == OVERLAY_POSTIMAGE_SHA256, 'overlay postimage differs')
    return rom, entry, fat, stream, image


def _slice(image, address, size):
    offset = address - OVERLAY_RAM
    _need(0 <= offset <= len(image) - size, 'patch address outside overlay')
    return offset


def patch_overlay_image(image):
    """Return the exact overlay-2 successor, rejecting every preimage drift."""
    image = bytes(image)
    _need(len(image) == OVERLAY_BYTES and _sha(image) == OVERLAY_PREIMAGE_SHA256,
          'overlay preimage differs')
    out = bytearray(image)
    for address, before, after in PATCHES:
        _need(len(before) == len(after), 'patch changes logical geometry')
        offset = _slice(image, address, len(before))
        _need(image[offset:offset + len(before)] == before,
              'patch preimage differs at %#x' % address)
        out[offset:offset + len(after)] = after
    out = bytes(out)
    _need(_sha(out) == OVERLAY_POSTIMAGE_SHA256, 'overlay postimage differs')
    _need(check_clear_postimage(out[_slice(out, CLEAR_FUNCTION, len(CLEAR_POSTIMAGE)):
                                    _slice(out, CLEAR_FUNCTION, len(CLEAR_POSTIMAGE))
                                    + len(CLEAR_POSTIMAGE)]),
          'clear-bell postimage differs')
    _need(check_bird_postimage(out[_slice(out, BIRD_FUNCTION, len(BIRD_POSTIMAGE)):
                                   _slice(out, BIRD_FUNCTION, len(BIRD_POSTIMAGE))
                                   + len(BIRD_POSTIMAGE)]),
          'bird-approach postimage differs')
    _need(check_lugia_postimage(out[_slice(out, LUGIA_FUNCTION, len(LUGIA_POSTIMAGE)):
                                    _slice(out, LUGIA_FUNCTION, len(LUGIA_POSTIMAGE))
                                    + len(LUGIA_POSTIMAGE)]),
          'Lugia postimage differs')
    return out


def _patch_rows():
    return [{'address': address, 'before': before.hex(), 'after': after.hex()}
            for address, before, after in PATCHES]


def apply(data, language):
    """Install HG-T10 on an exact formal-candidate overlay predecessor."""
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    _rom, entry, fat, stream, image = _overlay(data, 'pre')
    patched_image = patch_overlay_image(image)
    encoded = blz_comprimi_ottimo(patched_image, bersaglio=COMPRESSED_BYTES)
    _need(len(encoded) == COMPRESSED_BYTES
          and _sha(encoded) == COMPRESSED_POSTIMAGE_SHA256,
          'compressed overlay postimage differs')
    _need(blz_decomprimi(encoded, OVERLAY_BYTES) == patched_image,
          'compressed overlay does not round-trip')
    out = bytearray(data)
    out[fat['inizio']:fat['fine']] = encoded
    out = bytes(out)
    receipt = {
        'schema': 1,
        'stage': STAGE,
        'language': language,
        'input_sha256': _sha(data),
        'output_sha256': _sha(out),
        'overlay_id': OVERLAY_ID,
        'file_id': entry['file_id'],
        'rom_slot': [fat['inizio'], fat['fine']],
        'ram_address': OVERLAY_RAM,
        'decompressed_bytes': OVERLAY_BYTES,
        'compressed_bytes': COMPRESSED_BYTES,
        'overlay_preimage_sha256': OVERLAY_PREIMAGE_SHA256,
        'overlay_postimage_sha256': OVERLAY_POSTIMAGE_SHA256,
        'compressed_preimage_sha256': COMPRESSED_PREIMAGE_SHA256,
        'compressed_postimage_sha256': COMPRESSED_POSTIMAGE_SHA256,
        'selector': {'lugia_map_id': 244, 'lugia_scene_version': 8,
                     'default_scene_version': 7},
        'patches': _patch_rows(),
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = _verify(data, out, receipt, unsealed=True)
    return out, receipt


def _verify(before, after, receipt, *, unsealed):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'ROM geometry')
    _old_rom, old_entry, old_fat, old_stream, old_image = _overlay(before, 'pre')
    _new_rom, new_entry, new_fat, new_stream, new_image = _overlay(after, 'post')
    _need(old_entry == new_entry and old_fat == new_fat,
          'FAT/y9 overlay identity changed')
    _need(blz_decomprimi(new_stream, OVERLAY_BYTES) == new_image,
          'installed BLZ round-trip differs')

    restored_image = bytearray(new_image)
    for address, old, new in PATCHES:
        offset = _slice(new_image, address, len(new))
        _need(new_image[offset:offset + len(new)] == new,
              'installed postimage differs at %#x' % address)
        restored_image[offset:offset + len(old)] = old
    _need(bytes(restored_image) == old_image,
          'logical bytes changed outside declared seams')
    restored_rom = bytearray(after)
    restored_rom[old_fat['inizio']:old_fat['fine']] = old_stream
    _need(bytes(restored_rom) == before,
          'ROM bytes changed outside compressed overlay slot')

    report = {
        'ok': True,
        'overlay_id': OVERLAY_ID,
        'changed_logical_bytes': sum(a != b for a, b in zip(old_image, new_image)),
        'changed_rom_bytes': sum(a != b for a, b in zip(old_stream, new_stream)),
        'changed_regions': [[old_fat['inizio'], old_fat['fine']]],
        'lugia_map_id': 244,
        'lugia_scene_version': 8,
        'hooh_and_default_scene_version': 7,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    required = {
        'schema': 1,
        'stage': STAGE,
        'input_sha256': _sha(before),
        'output_sha256': _sha(after),
        'overlay_id': OVERLAY_ID,
        'file_id': old_entry['file_id'],
        'rom_slot': [old_fat['inizio'], old_fat['fine']],
        'ram_address': OVERLAY_RAM,
        'decompressed_bytes': OVERLAY_BYTES,
        'compressed_bytes': COMPRESSED_BYTES,
        'overlay_preimage_sha256': OVERLAY_PREIMAGE_SHA256,
        'overlay_postimage_sha256': OVERLAY_POSTIMAGE_SHA256,
        'compressed_preimage_sha256': COMPRESSED_PREIMAGE_SHA256,
        'compressed_postimage_sha256': COMPRESSED_POSTIMAGE_SHA256,
        'selector': {'lugia_map_id': 244, 'lugia_scene_version': 8,
                     'default_scene_version': 7},
        'patches': _patch_rows(),
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    allowed = set(required) | {'language'}
    if not unsealed:
        allowed.add('verification')
    _need(isinstance(receipt, dict) and set(receipt) == allowed
          and receipt.get('language') in LANGUAGES
          and (unsealed or receipt.get('verification') == report)
          and all(receipt.get(key) == value for key, value in required.items()),
          'receipt identity')
    _language_anchor(before, receipt.get('language'))
    return report


def verify(before, after, receipt):
    return _verify(before, after, receipt, unsealed=False)


def peel(after):
    """Remove this stage from an exact postimage and recover its predecessor."""
    _rom, _entry, fat, _stream, image = _overlay(bytes(after), 'post')
    restored = bytearray(image)
    for address, old, new in PATCHES:
        offset = _slice(image, address, len(new))
        _need(image[offset:offset + len(new)] == new,
              'peel postimage differs at %#x' % address)
        restored[offset:offset + len(old)] = old
    restored = bytes(restored)
    _need(_sha(restored) == OVERLAY_PREIMAGE_SHA256,
          'peeled overlay preimage differs')
    encoded = blz_comprimi_ottimo(restored, bersaglio=COMPRESSED_BYTES)
    _need(len(encoded) == COMPRESSED_BYTES
          and _sha(encoded) == COMPRESSED_PREIMAGE_SHA256,
          'peeled compressed preimage differs')
    out = bytearray(after)
    out[fat['inizio']:fat['fine']] = encoded
    out = bytes(out)
    _overlay(out, 'pre')
    return out


def overlay_file_span(data):
    _rom, _entry, fat, _stream, _image = _overlay(bytes(data), None)
    return fat['inizio'], fat['fine']


def changed_regions(data):
    # Declarations are also read from the immutable V4 during independent
    # chain replay.  The UI stage later rewrites overlay 2 before this writer,
    # so geometry belongs here while exact preimage identity stays in apply().
    _rom, _entry, fat, _stream, _image = _overlay(bytes(data), None)
    return ((fat['inizio'], fat['fine']),)


def spans(data):
    start, end = changed_regions(data)[0]
    return ((start, end, 'overlay 2 legendary scene-version selectors'),)
