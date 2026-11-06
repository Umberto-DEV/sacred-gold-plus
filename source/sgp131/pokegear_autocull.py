"""Cull Pokégear map markers on signed X as well as Y.

The inherited overlay-101 culler only checks Y.  Its three private callers
already own signed map coordinates, but pass only Y and an unrelated loop
index.  Reusing the 36-byte function window for the complete signed check makes
the canonical BLZ stream four bytes too large.  This producer keeps the three
call sites and overlay slot fixed, turns the old function into a tail
trampoline, and places the proved 36-byte implementation in the reviewed ARM9
reserve.  No overlay, FAT, y9, ROM or save geometry changes.
"""
import hashlib
import struct

from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi
from sgp12.rom import Arm9, Rom, bl_decode, bl_thumb


LANGUAGES = ('EN', 'IT')
STAGE = 'pokegear-autocull'

OVERLAY_ID = 101
OVERLAY_RAM = 0x021E7740
OVERLAY_BYTES = 0x13BC0
COMPRESSED_BYTES = 53576
STATIC_INIT_RANGE = (0x021FB2AC, 0x021FB2B0)

AUTOCULL = 0x021EC920
AUTOCULL_BYTES = 36
AUTOCULL_PREIMAGE = bytes.fromhex(
    '08b5417800290cd0d82a01dc002a04da006a002137f67cff08bd'
    '006a012137f677ff08bd')

CALLER_PATCHES = {
    0x021EC828: (bytes.fromhex('0a27'), bytes.fromhex('0427')),
    0x021EC83C: (bytes.fromhex('c25f'), bytes.fromhex('c288')),
    0x021EC83E: (bytes.fromhex('291c'), bytes.fromhex('c15f')),
    0x021EC8E4: (bytes.fromhex('291c'), bytes.fromhex('c046')),
    0x021EC95C: (bytes.fromhex('0627'), bytes.fromhex('0427')),
    0x021EC964: (bytes.fromhex('c25f'), bytes.fromhex('c15f')),
    0x021EC966: (bytes.fromhex('211c'), bytes.fromhex('c288')),
}
CALLS = {
    0x021EC840: bytes.fromhex('00f06ef8'),
    0x021EC8E8: bytes.fromhex('00f01af8'),
    0x021EC968: bytes.fromhex('fff7daff'),
}

SLOT = 0x023D8AC8
SLOT_BYTES = 36
SLOT_PREIMAGE = bytes(SLOT_BYTES)
DRAW_FLAG = 0x02024830
FREE_TAIL = SLOT + SLOT_BYTES
FREE_TAIL_BYTES = 20
NEXT_OWNER = 0x023D8B00
NEXT_OWNER_PREFIX = bytes.fromhex('f0b587b0274a1168491c116001210902')


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('Pokégear AutoCull: ' + message)


def _slot_payload():
    payload = bytearray.fromhex(
        '08b54378002b0ad00731054b8b4200214941c72a00d90021006a'
        '0000000008bd0e010000')
    payload[26:30] = bl_thumb(SLOT + 26, DRAW_FLAG)
    payload = bytes(payload)
    _need(len(payload) == SLOT_BYTES, 'resident payload length')
    _need(bl_decode(SLOT + 26, payload[26:30]) == DRAW_FLAG,
          'resident draw-flag branch')
    return payload


SLOT_POSTIMAGE = _slot_payload()
SLOT_POST_SHA256 = '773bc351811fdd121dfa80d745bf45cb330f038b21e54caa756498fafb27ed1f'
TRAMPOLINE_POSTIMAGE = (
    bytes.fromhex('004b1847') + struct.pack('<I', SLOT | 1)
    + bytes(AUTOCULL_BYTES - 8)
)
TRAMPOLINE_POST_SHA256 = 'd276b611a216e628d0f296603e8208de83612d6cbcc7921f3e0bb473df532dd6'

OVERLAY_PRE_SHA256 = 'e7fa1b6cc5abac3eda341e2bfa1103665a064b7e28ff20f307e787311c371b72'
STREAM_PRE_SHA256 = 'b78b568e51fb4d43e2ad2f05e8e61ab09f2f1da308b8247d84d7d925f767f9ce'
OVERLAY_POST_SHA256 = '4ad17ca990cb750938203d2e4a368fd418cf9fb9d9d83ed22328678fc3d552bb'
STREAM_POST_SHA256 = 'cf4ff51d846bdb40cfa22af40516d8db6286bd9bcb3630ee18cf60886e92aac9'

LANGUAGE_ANCHOR_FILE = 137
LANGUAGE_ANCHORS = {
    'EN': '60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82',
    'IT': 'edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233',
}


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
        raise ValueError('Pokégear AutoCull: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')


def _read_overlay(data):
    try:
        rom = Rom(data)
        entry, stream, image = rom.immagine_overlay(OVERLAY_ID)
        fat = rom.voce_fat(entry['file_id'])
    except (ValueError, struct.error, IndexError) as error:
        raise ValueError('Pokégear AutoCull: overlay geometry') from error
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


def _caller_records(which):
    return [{'address': address, 'bytes': pair[which].hex()}
            for address, pair in sorted(CALLER_PATCHES.items())]


def _guard_overlay(image, *, post=False):
    _need(type(image) is bytes and len(image) == OVERLAY_BYTES,
          'overlay logical geometry')
    expected = OVERLAY_POST_SHA256 if post else OVERLAY_PRE_SHA256
    _need(_sha(image) == expected, 'overlay %simage differs' % ('post' if post else 'pre'))
    for address, (before, after) in CALLER_PATCHES.items():
        at = address - OVERLAY_RAM
        _need(image[at:at + len(before)] == (after if post else before),
              'caller patch differs at %#x' % address)
    for address, call in CALLS.items():
        at = address - OVERLAY_RAM
        _need(image[at:at + 4] == call
              and bl_decode(address, call) == AUTOCULL,
              'private call differs at %#x' % address)
    at = AUTOCULL - OVERLAY_RAM
    _need(image[at:at + AUTOCULL_BYTES]
          == (TRAMPOLINE_POSTIMAGE if post else AUTOCULL_PREIMAGE),
          'AutoCull function differs')


def _patch_overlay(image):
    _guard_overlay(image)
    out = bytearray(image)
    for address, (_before, after) in CALLER_PATCHES.items():
        at = address - OVERLAY_RAM
        out[at:at + len(after)] = after
    at = AUTOCULL - OVERLAY_RAM
    out[at:at + AUTOCULL_BYTES] = TRAMPOLINE_POSTIMAGE
    out = bytes(out)
    _guard_overlay(out, post=True)
    return out


def _guard_resident(arm, *, post=False):
    from . import gb_sounds_evolution
    _need(arm.leggi(gb_sounds_evolution.SLOT,
                    gb_sounds_evolution.SLOT_BYTES)
          == gb_sounds_evolution.SLOT_POSTIMAGE,
          'preceding GB Sounds owner differs')
    _need(arm.leggi(SLOT, SLOT_BYTES)
          == (SLOT_POSTIMAGE if post else SLOT_PREIMAGE),
          'resident %simage differs' % ('post' if post else 'pre'))
    _need(arm.leggi(FREE_TAIL, FREE_TAIL_BYTES) == bytes(FREE_TAIL_BYTES),
          'remaining free tail changed')
    _need(arm.leggi(NEXT_OWNER, len(NEXT_OWNER_PREFIX)) == NEXT_OWNER_PREFIX,
          'following owner changed')


def _preimage(data):
    rom, entry, fat, stream, image = _read_overlay(data)
    _need(_sha(stream) == STREAM_PRE_SHA256, 'compressed overlay preimage differs')
    _guard_overlay(image)
    arm = Arm9.from_bytes(data)
    _guard_resident(arm)
    return rom, entry, fat, stream, image, arm


def apply(data, language):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    _rom, entry, fat, stream, image, arm = _preimage(data)
    patched = _patch_overlay(image)
    encoded = blz_comprimi_ottimo(patched, bersaglio=COMPRESSED_BYTES)
    _need(len(encoded) == COMPRESSED_BYTES
          and _sha(encoded) == STREAM_POST_SHA256,
          'compressed overlay postimage differs')
    _need(blz_decomprimi(encoded, OVERLAY_BYTES) == patched,
          'compressed overlay does not round-trip')

    out = bytearray(data)
    out[fat['inizio']:fat['fine']] = encoded
    arm = Arm9.from_bytes(bytes(out))
    _guard_resident(arm)
    arm.scrivi(SLOT, SLOT_POSTIMAGE)
    out = bytes(arm.raw)
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
        'overlay_preimage_sha256': OVERLAY_PRE_SHA256,
        'overlay_postimage_sha256': OVERLAY_POST_SHA256,
        'compressed_preimage_sha256': _sha(stream),
        'compressed_postimage_sha256': STREAM_POST_SHA256,
        'callers_before': _caller_records(0),
        'callers_after': _caller_records(1),
        'autocull_address': AUTOCULL,
        'autocull_preimage_sha256': _sha(AUTOCULL_PREIMAGE),
        'trampoline_postimage_sha256': TRAMPOLINE_POST_SHA256,
        'slot_address': SLOT,
        'slot_bytes': SLOT_BYTES,
        'slot_preimage_sha256': _sha(SLOT_PREIMAGE),
        'slot_postimage_sha256': SLOT_POST_SHA256,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = _verify(data, out, receipt, unsealed=True)
    return out, receipt


def _verify(before, after, receipt, *, unsealed):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'ROM geometry')
    _old_rom, old_entry, old_fat, old_stream, old_image, old_arm = _preimage(before)
    _new_rom, new_entry, new_fat, new_stream, new_image = _read_overlay(after)
    _need(old_entry == new_entry and old_fat == new_fat,
          'FAT/y9 overlay identity changed')
    _need(_sha(new_stream) == STREAM_POST_SHA256
          and _sha(new_image) == OVERLAY_POST_SHA256,
          'installed overlay postimage differs')
    _need(blz_decomprimi(new_stream, OVERLAY_BYTES) == new_image,
          'installed BLZ round-trip differs')
    _guard_overlay(new_image, post=True)
    new_arm = Arm9.from_bytes(after)
    _guard_resident(new_arm, post=True)

    restored_image = bytearray(new_image)
    for address, (old, _new) in CALLER_PATCHES.items():
        at = address - OVERLAY_RAM
        restored_image[at:at + len(old)] = old
    at = AUTOCULL - OVERLAY_RAM
    restored_image[at:at + AUTOCULL_BYTES] = AUTOCULL_PREIMAGE
    _need(bytes(restored_image) == old_image,
          'logical bytes changed outside callers and AutoCull')

    restored = bytearray(after)
    restored[old_fat['inizio']:old_fat['fine']] = old_stream
    slot_at = old_arm.off(SLOT, SLOT_BYTES)
    restored[slot_at:slot_at + SLOT_BYTES] = SLOT_PREIMAGE
    _need(bytes(restored) == before,
          'ROM bytes changed outside overlay and resident slot')

    report = {
        'ok': True,
        'changed_logical_bytes': sum(a != b for a, b in zip(old_image, new_image)),
        'changed_rom_bytes': sum(a != b for a, b in zip(before, after)),
        'signed_x_bounds': [-7, 263],
        'y_bounds': [0, 199],
        'auto_cull_disable_preserved': True,
        'private_call_targets_preserved': True,
        'overlay_slot_unchanged': True,
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
        'overlay_preimage_sha256': OVERLAY_PRE_SHA256,
        'overlay_postimage_sha256': OVERLAY_POST_SHA256,
        'compressed_preimage_sha256': _sha(old_stream),
        'compressed_postimage_sha256': STREAM_POST_SHA256,
        'callers_before': _caller_records(0),
        'callers_after': _caller_records(1),
        'autocull_address': AUTOCULL,
        'autocull_preimage_sha256': _sha(AUTOCULL_PREIMAGE),
        'trampoline_postimage_sha256': TRAMPOLINE_POST_SHA256,
        'slot_address': SLOT,
        'slot_bytes': SLOT_BYTES,
        'slot_preimage_sha256': _sha(SLOT_PREIMAGE),
        'slot_postimage_sha256': SLOT_POST_SHA256,
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


def spans(data):
    _rom, _entry, fat, _stream, _image, arm = _preimage(bytes(data))
    slot = arm.off(SLOT, SLOT_BYTES)
    return ((fat['inizio'], fat['fine']), (slot, slot + SLOT_BYTES))
