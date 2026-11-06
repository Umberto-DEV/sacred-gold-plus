"""Repair the Victory Road Fly-marker highlight while preserving its name.

Victory Road's flypoint is labelled with ``MAP_VICTORY_ROAD_1F`` but warps to
``MAP_ROUTE_26``.  The selection animation passes the label ID to a regional
gate whose exceptions cover Route 26 and Indigo Plateau.  At the marker's
coordinate (28, 7), the ordinary classifier says Kanto, so a Johto caller can
fly there but never sees the selected animation.

The replacement gate recognizes the two shared-border fly coordinates
``(28, 6..7)`` and otherwise tail-calls the original region comparison.  Its
two callers already resolve a real flypoint before entering the gate.  The
flypoint table, displayed name, destination, save flags and ROM geometry stay
unchanged.
"""
import hashlib
import struct

from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi
from sgp12.rom import Rom


LANGUAGES = ('EN', 'IT')
STAGE = 'victory-road-fly'
OVERLAY_ID = 101
OVERLAY_RAM = 0x021E7740
OVERLAY_BYTES = 0x13BC0
COMPRESSED_BYTES = 53576
STATIC_INIT_RANGE = (0x021FB2AC, 0x021FB2B0)

GATE = 0x021EA804
GATE_OFFSET = GATE - OVERLAY_RAM
GATE_BYTES = 24
GATE_PREIMAGE = bytes.fromhex(
    '08b53a2901d01e2901d1012008bd111c1a1cfff7e5ff08bd')
GATE_POSTIMAGE = bytes.fromhex(
    '1c2a02d1'          # x != 28 -> ordinary region comparison
    '991f012902d9'      # x == 28 and unsigned(y - 6) <= 1 -> shared border
    '111c1a1ce7e7'      # tail-call the original region comparison
    '01207047'          # return TRUE for (28,6) and (28,7)
    'c046c046')         # preserve the 24-byte function span

FLYPOINT_TABLE = 0x021F79B4
VICTORY_INDEX = 26
FLYPOINT_BYTES = 14
VICTORY_ROW = bytes.fromhex('7c001e0021ff1c07000021000000')

# V4 supports the direct regression.  The second profile is the exact output
# of the existing legacy/fishing owner and is the production-chain predecessor.
PROFILES = {
    '825338c36a2f638006f66c89f357e248e01bef8ce3d86e9761ac94a5ca0e4581': {
        'name': 'v4',
        'compressed_pre': 'b5f02ee2c3cccf3a43fa1946bd96587191dc7f3f252c899170172be604bfb61e',
        'logical_post': '6eec60196affa08756f63697c9a750cb7dfb18d754288b7dd697c00d19df7a5d',
        'compressed_post': '79d76b05202317c30852ff12f3ca360246529687f89d13b26c8ee4ffcef36bc4',
    },
    'ac46edbae629b06ab66f4ce375a4375500c49f9487dcf4ca78c72c1b109b423e': {
        'name': 'legacy-fishing',
        'compressed_pre': '6ebaeab1faf8e96899b0ec457edbb3b1b12136c64f9d9a17750c6322d629193e',
        'logical_post': 'e7fa1b6cc5abac3eda341e2bfa1103665a064b7e28ff20f307e787311c371b72',
        'compressed_post': 'b78b568e51fb4d43e2ad2f05e8e61ab09f2f1da308b8247d84d7d925f767f9ce',
    },
}

LANGUAGE_ANCHOR_FILE = 137
LANGUAGE_ANCHORS = {
    'EN': '60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82',
    'IT': 'edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233',
}


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('Victory Road Fly: ' + message)


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
        raise ValueError('Victory Road Fly: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')
    return start, end


def _read_overlay(data):
    try:
        rom = Rom(data)
        entry, stream, image = rom.immagine_overlay(OVERLAY_ID)
        fat = rom.voce_fat(entry['file_id'])
    except (ValueError, struct.error, IndexError) as error:
        raise ValueError('Victory Road Fly: overlay geometry') from error
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
    return rom, entry, fat, bytes(stream), bytes(image)


def _preimage(data):
    rom, entry, fat, stream, image = _read_overlay(data)
    profile = PROFILES.get(_sha(image))
    _need(profile is not None, 'overlay preimage differs')
    _need(_sha(stream) == profile['compressed_pre'],
          'compressed overlay preimage differs')
    _need(image[GATE_OFFSET:GATE_OFFSET + GATE_BYTES] == GATE_PREIMAGE,
          'region-gate preimage differs')
    row = FLYPOINT_TABLE - OVERLAY_RAM + VICTORY_INDEX * FLYPOINT_BYTES
    _need(image[row:row + FLYPOINT_BYTES] == VICTORY_ROW,
          'Victory Road flypoint row differs')
    return rom, entry, fat, stream, image, profile


def _patch_image(image, profile):
    out = bytearray(image)
    out[GATE_OFFSET:GATE_OFFSET + GATE_BYTES] = GATE_POSTIMAGE
    out = bytes(out)
    _need(_sha(out) == profile['logical_post'],
          'overlay postimage differs')
    return out


def _patch_record():
    return {'address': GATE, 'before': GATE_PREIMAGE.hex(),
            'after': GATE_POSTIMAGE.hex()}


def apply(data, language):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    _rom, entry, fat, stream, image, profile = _preimage(data)
    patched = _patch_image(image, profile)
    encoded = blz_comprimi_ottimo(patched, bersaglio=COMPRESSED_BYTES)
    _need(len(encoded) == COMPRESSED_BYTES
          and _sha(encoded) == profile['compressed_post'],
          'compressed overlay postimage differs')
    _need(blz_decomprimi(encoded, OVERLAY_BYTES) == patched,
          'compressed overlay does not round-trip')

    out = bytearray(data)
    out[fat['inizio']:fat['fine']] = encoded
    out = bytes(out)
    receipt = {
        'schema': 1,
        'stage': STAGE,
        'language': language,
        'profile': profile['name'],
        'input_sha256': _sha(data),
        'output_sha256': _sha(out),
        'overlay_id': OVERLAY_ID,
        'file_id': entry['file_id'],
        'rom_slot': [fat['inizio'], fat['fine']],
        'ram_address': OVERLAY_RAM,
        'decompressed_bytes': OVERLAY_BYTES,
        'compressed_bytes': COMPRESSED_BYTES,
        'overlay_preimage_sha256': _sha(image),
        'overlay_postimage_sha256': profile['logical_post'],
        'compressed_preimage_sha256': _sha(stream),
        'compressed_postimage_sha256': profile['compressed_post'],
        'patch': _patch_record(),
        'victory_row_sha256': _sha(VICTORY_ROW),
        'displayed_name_unchanged': True,
        'warp_destination_unchanged': True,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = _verify(data, out, receipt, unsealed=True)
    return out, receipt


def _verify(before, after, receipt, *, unsealed):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'ROM geometry')
    _old_rom, old_entry, old_fat, old_stream, old_image, profile = _preimage(before)
    _new_rom, new_entry, new_fat, new_stream, new_image = _read_overlay(after)
    _need(old_entry == new_entry and old_fat == new_fat,
          'FAT/y9 overlay identity changed')
    _need(_sha(new_stream) == profile['compressed_post']
          and _sha(new_image) == profile['logical_post'],
          'installed overlay postimage differs')
    _need(blz_decomprimi(new_stream, OVERLAY_BYTES) == new_image,
          'installed BLZ round-trip differs')
    _need(new_image[GATE_OFFSET:GATE_OFFSET + GATE_BYTES] == GATE_POSTIMAGE,
          'installed region gate differs')
    row = FLYPOINT_TABLE - OVERLAY_RAM + VICTORY_INDEX * FLYPOINT_BYTES
    _need(new_image[row:row + FLYPOINT_BYTES] == VICTORY_ROW,
          'display name or warp destination changed')

    restored_image = bytearray(new_image)
    restored_image[GATE_OFFSET:GATE_OFFSET + GATE_BYTES] = GATE_PREIMAGE
    _need(bytes(restored_image) == old_image,
          'logical bytes changed outside the region gate')
    restored_rom = bytearray(after)
    restored_rom[old_fat['inizio']:old_fat['fine']] = old_stream
    _need(bytes(restored_rom) == before,
          'ROM bytes changed outside compressed overlay slot')

    report = {
        'ok': True,
        'profile': profile['name'],
        'changed_logical_bytes': sum(a != b for a, b in zip(old_image, new_image)),
        'changed_rom_bytes': sum(a != b for a, b in zip(old_stream, new_stream)),
        'johto_victory_highlight_admitted': True,
        'indigo_control_preserved': True,
        'ordinary_region_gate_preserved': True,
        'displayed_name_unchanged': True,
        'warp_destination_unchanged': True,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    required = {
        'schema': 1,
        'stage': STAGE,
        'profile': profile['name'],
        'input_sha256': _sha(before),
        'output_sha256': _sha(after),
        'overlay_id': OVERLAY_ID,
        'file_id': old_entry['file_id'],
        'rom_slot': [old_fat['inizio'], old_fat['fine']],
        'ram_address': OVERLAY_RAM,
        'decompressed_bytes': OVERLAY_BYTES,
        'compressed_bytes': COMPRESSED_BYTES,
        'overlay_preimage_sha256': _sha(old_image),
        'overlay_postimage_sha256': profile['logical_post'],
        'compressed_preimage_sha256': _sha(old_stream),
        'compressed_postimage_sha256': profile['compressed_post'],
        'patch': _patch_record(),
        'victory_row_sha256': _sha(VICTORY_ROW),
        'displayed_name_unchanged': True,
        'warp_destination_unchanged': True,
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


def changed_regions(data):
    _rom, _entry, fat, _stream, _image, _profile = _preimage(bytes(data))
    return ((fat['inizio'], fat['fine']),)
