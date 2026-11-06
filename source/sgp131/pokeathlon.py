"""Preserve the full Pokéathlon all-medals count in the room summary.

The native counter returns a ``u16`` in the range 0..493.  Overlay 99 stored
that value at byte offset 0x16 of a 0x1C-byte temporary summary and reloaded it
as a byte.  Offsets 0x1A..0x1B are padding: move the field there and use
``strh``/``ldrh``.  The save block and every persistent identifier stay
unchanged; only the transient heap summary becomes wide enough.
"""
import hashlib


OVERLAY_ID = 99
OVERLAY_BASE = 0x021E5900
OVERLAY_SIZE = 0x4D00
WRITER_FUNCTION = (0x021E6FD0, 0x021E7060)
WRITER_SHA256 = '6fea8a896d771f307a2ae086294d7432ee7868102e1aeece2680f1caa84a879f'
ACCESSOR_FUNCTION = (0x021E7078, 0x021E7088)
ACCESSOR_SHA256 = '3ed4fcce7299940a0247cfa349bc90c1d97bf1ca9939b13037367f932768d1c0'
OVERLAY_SHA256 = 'f023a8d147f246f542e9ed9479360189197251514efca0f7b28c36aedae9991f'
PATCHES = (
    (0x021E703A, bytes.fromhex('a075'), bytes.fromhex('6083')),  # strb +0x16 -> strh +0x1A
    (0x021E7082, bytes.fromhex('a07d'), bytes.fromhex('608b')),  # ldrb +0x16 -> ldrh +0x1A
)
LANGUAGES = ('EN', 'IT')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _function(image, span):
    return bytes(image[span[0] - OVERLAY_BASE:span[1] - OVERLAY_BASE])


def _changed(before, after):
    return [index for index, (old, new) in enumerate(zip(before, after)) if old != new]


def _apply(image):
    result = bytearray(image)
    for address, _, replacement in PATCHES:
        at = address - OVERLAY_BASE
        result[at:at + len(replacement)] = replacement
    return bytes(result)


def patch_overlay(image, *, writer_sha256=WRITER_SHA256,
                  accessor_sha256=ACCESSOR_SHA256):
    if not isinstance(image, (bytes, bytearray, memoryview)):
        raise TypeError('overlay 99 image must be bytes')
    image = bytes(image)
    if len(image) != OVERLAY_SIZE:
        raise ValueError('overlay 99 image size %#x differs from %#x'
                         % (len(image), OVERLAY_SIZE))
    for address, preimage, _ in PATCHES:
        at = address - OVERLAY_BASE
        if image[at:at + len(preimage)] != preimage:
            raise ValueError('Pokéathlon summary preimage does not match at %#x' % address)
    if _sha(_function(image, WRITER_FUNCTION)) != writer_sha256:
        raise ValueError('Pokéathlon summary writer differs from the pinned build')
    if _sha(_function(image, ACCESSOR_FUNCTION)) != accessor_sha256:
        raise ValueError('Pokéathlon summary accessor differs from the pinned build')
    result = _apply(image)
    return result, {
        'sites': [{'address': address, 'preimage': old.hex(),
                   'replacement': new.hex()} for address, old, new in PATCHES],
        'summary_offset_before': 0x16,
        'summary_offset_after': 0x1A,
        'summary_width_before': 1,
        'summary_width_after': 2,
        'changed_offsets': _changed(image, result),
        'writer_sha256_before': _sha(_function(image, WRITER_FUNCTION)),
        'writer_sha256_after': _sha(_function(result, WRITER_FUNCTION)),
        'accessor_sha256_before': _sha(_function(image, ACCESSOR_FUNCTION)),
        'accessor_sha256_after': _sha(_function(result, ACCESSOR_FUNCTION)),
        'overlay_sha256_before': _sha(image),
        'overlay_sha256_after': _sha(result),
    }


def verify_images(before, after):
    if len(before) != OVERLAY_SIZE or len(after) != OVERLAY_SIZE:
        raise ValueError('overlay 99 image size differs')
    expected, _ = patch_overlay(
        before,
        writer_sha256=_sha(_function(before, WRITER_FUNCTION)),
        accessor_sha256=_sha(_function(before, ACCESSOR_FUNCTION)))
    if bytes(after) != expected:
        raise ValueError('overlay 99 differs from the two declared Pokéathlon halfwords')
    changed = _changed(before, after)
    return {'changed_offsets': changed, 'changed_bytes': len(changed),
            'overlay_sha256_before': _sha(before),
            'overlay_sha256_after': _sha(after)}


def apply(data, language):
    from sgp12.overlay import applica
    from sgp12.rom import Rom
    if language not in LANGUAGES:
        raise ValueError('unknown language %r; expected EN or IT' % (language,))
    data = bytes(data)
    entry, _, original = Rom(data).immagine_overlay(OVERLAY_ID)
    if (entry['ram'], entry['ram_size'], entry['file_id']) != \
            (OVERLAY_BASE, OVERLAY_SIZE, OVERLAY_ID):
        raise ValueError('overlay 99 placement differs from the supported Plus build')
    expected, details = patch_overlay(original)
    result, writer = applica(
        data, OVERLAY_ID,
        [(address, preimage) for address, preimage, _ in PATCHES],
        [{'addr': address, 'pre': preimage, 'post': replacement}
         for address, preimage, replacement in PATCHES])
    if Rom(result).immagine_overlay(OVERLAY_ID)[2] != expected:
        raise ValueError('overlay 99 readback differs from the verified Pokéathlon patch')
    receipt = {'stage': 'pokeathlon', 'language': language,
               'input_sha256': _sha(data), 'output_sha256': _sha(result),
               'patch': details, 'writer': writer}
    receipt['verification'] = verify(data, result, receipt)
    return result, receipt


def verify(before, after, receipt):
    from sgp12.blz import blz_comprimi_ottimo
    from sgp12.rom import Rom
    from . import ui_verify
    if len(before) != len(after):
        raise ValueError('Pokéathlon stage changed ROM length')
    old, new = ui_verify.Image(before), ui_verify.Image(after)
    if old.records != new.records or old.files != new.files:
        raise ValueError('Pokéathlon stage changed y9 or FAT geometry')
    if before[:0x200] != after[:0x200]:
        raise ValueError('Pokéathlon stage changed the cartridge header')
    start, end = old.files[OVERLAY_ID]
    restored = bytearray(after)
    restored[start:end] = before[start:end]
    if bytes(restored) != before:
        raise ValueError('Pokéathlon stage changed bytes outside overlay 99')
    before_image = Rom(before).immagine_overlay(OVERLAY_ID)[2]
    after_image = Rom(after).immagine_overlay(OVERLAY_ID)[2]
    logical = verify_images(before_image, after_image)
    canonical = blz_comprimi_ottimo(after_image, bersaglio=end - start)
    if canonical != after[start:end]:
        raise ValueError('overlay 99 BLZ stream is not the canonical fixed-size output')
    if not isinstance(receipt, dict) or receipt.get('input_sha256') != _sha(before) \
            or receipt.get('output_sha256') != _sha(after):
        raise ValueError('Pokéathlon receipt hashes differ from the ROMs')
    writer = receipt.get('writer', {})
    if writer.get('ingresso_sha256') != _sha(before) \
            or writer.get('uscita_sha256') != _sha(after):
        raise ValueError('overlay writer receipt hashes differ from the ROMs')
    return {'ok': True, 'logical_changed_bytes': logical['changed_bytes'],
            'overlay_sha256_before': logical['overlay_sha256_before'],
            'overlay_sha256_after': logical['overlay_sha256_after'],
            'compressed_bytes': end - start,
            'rom_sha256_before': _sha(before), 'rom_sha256_after': _sha(after)}
