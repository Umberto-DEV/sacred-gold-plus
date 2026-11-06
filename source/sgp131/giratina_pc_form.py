"""Repair HG-F16: Giratina form changes made from the PC leave party stats stale.

Overlay 14 deliberately operates on ``BoxPokemon`` records.  Party slots are
also exposed to it as their embedded BoxPokemon, so changing the Griseous Orb
updates Giratina's form and ability but skips the party-stat recalculation.
The repair reconciles party Giratina through the existing retail helper before
``PCBox_Exit`` releases its work structure.  No save layout or ROM geometry is
changed.
"""
import hashlib
import struct

from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi
from sgp12.rom import Rom


LANGUAGES = ('EN', 'IT')
STAGE = 'giratina-pc-form'
OVERLAY_ID = 14
OVERLAY_RAM = 0x021E5900
OVERLAY_BYTES = 0x13A80
COMPRESSED_BYTES = 51584
OVERLAY_PREIMAGE_SHA256 = 'd515fb04f06371d854ae5ecaed717ceb8338afde422f497bb3dc8590cc81ead5'
OVERLAY_POSTIMAGE_SHA256 = '39981ee7a81c78093e8b6b31b793a7bd9d482b57440ffe94612f798234146e4e'
COMPRESSED_PREIMAGE_SHA256 = 'e5db4442151504e0ca97ff52b8585c2fc64f1eb1532b8c9334744fd06d21a273'
COMPRESSED_POSTIMAGE_SHA256 = '85b374d5dba3bc983aa03f99bf2968db8cd637d1314ff6305e2f7a68b8de6306'

PCBOX_EXIT = 0x021E5988
PCBOX_EXIT_OFFSET = PCBOX_EXIT - OVERLAY_RAM
EXIT_PREIMAGE = bytes.fromhex('10b5041c21f680fc')
EXIT_POSTIMAGE = bytes.fromhex('004b184765931f02')
TRAMPOLINE = 0x021F9364
TRAMPOLINE_OFFSET = TRAMPOLINE - OVERLAY_RAM
TRAMPOLINE_PREIMAGE = bytes(28)
TRAMPOLINE_POSTIMAGE = bytes.fromhex(
    '10b5041c'          # push {r4,lr}; adds r4,r0,#0
    '0df692ff'          # bl OverlayManager_GetData
    '01b480680021'      # save work; party=work+8; force_origin=FALSE
    '78f6e3fc'          # bl Party_UpdateAllGiratina_DistortionWorld
    '01bc00490847'      # restore work; literal jump to displaced continuation
    '91591e02')         # 0x021E5991 (Thumb)
STATIC_INIT_RANGE = (0x021F9360, 0x021F9364)
PADDING_RANGE = (TRAMPOLINE, OVERLAY_RAM + OVERLAY_BYTES)

LANGUAGE_ANCHOR_FILE = 137
LANGUAGE_ANCHORS = {
    'EN': '60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82',
    'IT': 'edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233',
}


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('Giratina PC form: ' + message)


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
        raise ValueError('Giratina PC form: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')
    return start, end


def _overlay(data, *, require_preimage):
    try:
        rom = Rom(data)
        entry, stream, image = rom.immagine_overlay(OVERLAY_ID)
        fat = rom.voce_fat(entry['file_id'])
    except (ValueError, struct.error, IndexError) as error:
        raise ValueError('Giratina PC form: overlay geometry') from error
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
    if require_preimage:
        _need(_sha(stream) == COMPRESSED_PREIMAGE_SHA256,
              'compressed overlay preimage differs')
        _need(_sha(image) == OVERLAY_PREIMAGE_SHA256,
              'overlay preimage differs')
    return rom, entry, fat, stream, image


def patch_overlay_image(image):
    """Return the exact decompressed overlay successor, refusing every drift."""
    image = bytes(image)
    _need(len(image) == OVERLAY_BYTES
          and _sha(image) == OVERLAY_PREIMAGE_SHA256,
          'overlay preimage differs')
    _need(image[PCBOX_EXIT_OFFSET:PCBOX_EXIT_OFFSET + len(EXIT_PREIMAGE)]
          == EXIT_PREIMAGE, 'PCBox_Exit preimage differs')
    _need(image[TRAMPOLINE_OFFSET:TRAMPOLINE_OFFSET + len(TRAMPOLINE_PREIMAGE)]
          == TRAMPOLINE_PREIMAGE, 'trampoline padding preimage differs')
    out = bytearray(image)
    out[PCBOX_EXIT_OFFSET:PCBOX_EXIT_OFFSET + len(EXIT_POSTIMAGE)] = EXIT_POSTIMAGE
    out[TRAMPOLINE_OFFSET:TRAMPOLINE_OFFSET + len(TRAMPOLINE_POSTIMAGE)] = (
        TRAMPOLINE_POSTIMAGE)
    out = bytes(out)
    _need(_sha(out) == OVERLAY_POSTIMAGE_SHA256, 'overlay postimage differs')
    return out


def _patches():
    return [
        {'address': PCBOX_EXIT, 'before': EXIT_PREIMAGE.hex(),
         'after': EXIT_POSTIMAGE.hex()},
        {'address': TRAMPOLINE, 'before': TRAMPOLINE_PREIMAGE.hex(),
         'after': TRAMPOLINE_POSTIMAGE.hex()},
    ]


def apply(data, language):
    """Install HG-F16 in memory on an exact overlay-14 predecessor."""
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    rom, entry, fat, stream, image = _overlay(data, require_preimage=True)
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
        'patches': _patches(),
        'static_init_range': list(STATIC_INIT_RANGE),
        'padding_range': list(PADDING_RANGE),
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = _verify(data, out, receipt, unsealed=True)
    return out, receipt


def _verify(before, after, receipt, *, unsealed):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'ROM geometry')
    old_rom, old_entry, old_fat, old_stream, old_image = _overlay(
        before, require_preimage=True)
    new_rom, new_entry, new_fat, new_stream, new_image = _overlay(
        after, require_preimage=False)
    _need(old_entry == new_entry and old_fat == new_fat,
          'FAT/y9 overlay identity changed')
    _need(_sha(new_stream) == COMPRESSED_POSTIMAGE_SHA256
          and _sha(new_image) == OVERLAY_POSTIMAGE_SHA256,
          'installed overlay postimage differs')
    _need(blz_decomprimi(new_stream, OVERLAY_BYTES) == new_image,
          'installed BLZ round-trip differs')
    _need(new_image[PCBOX_EXIT_OFFSET:PCBOX_EXIT_OFFSET + len(EXIT_POSTIMAGE)]
          == EXIT_POSTIMAGE, 'installed PCBox_Exit hook differs')
    _need(new_image[TRAMPOLINE_OFFSET:TRAMPOLINE_OFFSET + len(TRAMPOLINE_POSTIMAGE)]
          == TRAMPOLINE_POSTIMAGE, 'installed trampoline differs')

    restored_image = bytearray(new_image)
    restored_image[PCBOX_EXIT_OFFSET:PCBOX_EXIT_OFFSET + len(EXIT_PREIMAGE)] = EXIT_PREIMAGE
    restored_image[TRAMPOLINE_OFFSET:TRAMPOLINE_OFFSET + len(TRAMPOLINE_PREIMAGE)] = (
        TRAMPOLINE_PREIMAGE)
    _need(bytes(restored_image) == old_image,
          'logical bytes changed outside declared seams')
    restored_rom = bytearray(after)
    restored_rom[old_fat['inizio']:old_fat['fine']] = old_stream
    _need(bytes(restored_rom) == before,
          'ROM bytes changed outside compressed overlay slot')

    logical_changed = sum(a != b for a, b in zip(old_image, new_image))
    physical_changed = sum(a != b for a, b in zip(old_stream, new_stream))
    report = {
        'ok': True,
        'overlay_id': OVERLAY_ID,
        'changed_logical_bytes': logical_changed,
        'changed_rom_bytes': physical_changed,
        'changed_regions': [[old_fat['inizio'], old_fat['fine']]],
        'party_reconciled_before_pc_cleanup': True,
        'force_origin': False,
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
        'patches': _patches(),
        'static_init_range': list(STATIC_INIT_RANGE),
        'padding_range': list(PADDING_RANGE),
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
    """Fail closed on identity, receipt, geometry or confinement drift."""
    return _verify(before, after, receipt, unsealed=False)


def changed_regions(data):
    """Declare the exact physical BLZ slot rewritten by this stage."""
    data = bytes(data)
    _rom, _entry, fat, _stream, _image = _overlay(data, require_preimage=True)
    return ((fat['inizio'], fat['fine']),)
