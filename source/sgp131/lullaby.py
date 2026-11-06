"""Saturate Lullaby's unsigned subtraction instead of amplifying low rates.

The original u8 conversion after SUBS turns 20-25 into 251, capped to 100.
Reuse the pure radio getter's first result, replacing its redundant second
call with the guarded subtraction. Keep the common cap at its original address.
The retained shifts help the BLZ stream fit its original slot exactly.
R0 is dead before the following argument-free LCRandom call, which reloads it.
No save data, reserve allocation, container field or overlay length changes.
"""
import hashlib
import struct

BASE, SIZE = 0x02245B80, 0xE2A0
START, END = 0x02247568, 0x0224760E
SITE = 0x022475D4
FUNCTION_SHA256 = '046812ab4798bf0e73dd39bd46b952d768a05fabf526cf932fa974fd4467a86e'
BEFORE = bytes.fromhex('0af06efe022802d1193c2006040e642c00d96424')
AFTER = bytes.fromhex('022804d1193c02d200242006040e642c00d96424')
RADIO_START, RADIO_END = 0x022522B4, 0x02252338
RADIO_SHA256 = 'd6a8e1224748bbeed9865b96fc8ff814e01511bcd2ab07cfa4f978a89482b132'
SOUND_GETTER = bytes.fromhex('014800687047c046e0051d02')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _guard(image, function_sha256):
    _need(len(image) == SIZE, 'Lullaby overlay size')
    at = SITE - BASE
    _need(image[at:at+20] == BEFORE, 'Lullaby preimage changed or already patched')
    _need(_sha(image[START-BASE:END-BASE]) == function_sha256, 'Lullaby function preimage hash')


def patch_overlay(image, *, function_sha256=FUNCTION_SHA256):
    image = bytes(image)
    _guard(image, function_sha256)
    at = SITE - BASE
    return image[:at] + AFTER + image[at+20:]


def verify_images(before, after, *, function_sha256=FUNCTION_SHA256):
    """Read back the changed instructions and independently check their complement."""
    _guard(before, function_sha256)
    _need(len(after) == SIZE, 'Lullaby output overlay size')
    at = SITE - BASE
    _need(after[at:at+20] == AFTER, 'Lullaby replacement instructions')
    _need(before[:at] == after[:at] and before[at+20:] == after[at+20:],
          'Lullaby logical bytes changed outside the instruction window')


def _read(data):
    """Container view read without the overlay writer or its receipt."""
    import ndspy.codeCompression
    from sgp12.blz import ndspy_decomprimi_sicuro
    from sgp12.rom import Rom
    fat, fat_bytes = struct.unpack_from('<II', data, 0x48)
    y9, y9_bytes = struct.unpack_from('<II', data, 0x50)
    _need(y9_bytes >= 3*32 and y9+3*32 <= len(data), 'overlay 2 table bounds')
    row = struct.unpack_from('<8I', data, y9+2*32)
    _need(row[0] == 2 and row[1:4] == (BASE, SIZE, 0) and row[6] == 2,
          'overlay 2 placement')
    _need(fat_bytes >= 24 and fat+24 <= len(data), 'overlay 2 FAT bounds')
    start, end = struct.unpack_from('<II', data, fat+16)
    _need(0 <= start < end <= len(data) and row[7] >> 24 & 1
          and row[7] & 0xFFFFFF == end-start, 'overlay 2 compressed slot')
    encoded = bytes(data[start:end])
    image = bytes(ndspy_decomprimi_sicuro(encoded, SIZE))
    _need(image == Rom(data).immagine_overlay(2)[2], 'overlay 2 decoders disagree')
    _need(_sha(image[RADIO_START-BASE:RADIO_END-BASE]) == RADIO_SHA256,
          'radio getter differs from the reviewed pure getter')
    from .ui_verify import Image
    _need(Image(data).arm(0x02004A20, len(SOUND_GETTER)) == SOUND_GETTER,
          'sound sequence getter differs from the reviewed load-only getter')
    return start, end, image


def apply(data, language):
    from sgp12.blz import blz_comprimi_ottimo
    _need(language in ('EN', 'IT'), 'Lullaby language')
    data = bytes(data)
    start, end, image = _read(data)
    patched = patch_overlay(image)
    stream = blz_comprimi_ottimo(patched, bersaglio=end-start)
    _need(len(stream) == end-start, 'Lullaby stream does not fit the unchanged FAT slot')
    out = data[:start] + stream + data[end:]
    receipt = {'stage': 'legacy-lullaby', 'language': language,
               'input_sha256': _sha(data), 'output_sha256': _sha(out)}
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    from sgp12.blz import blz_comprimi_ottimo
    start, end, old = _read(before)
    new_start, new_end, new = _read(after)
    _need((start, end) == (new_start, new_end) and len(before) == len(after),
          'Lullaby changed cartridge geometry')
    _need(before[:start] == after[:start] and before[end:] == after[end:],
          'Lullaby changed bytes outside overlay 2')
    verify_images(old, new)
    _need(after[start:end] == blz_comprimi_ottimo(new, bersaglio=end-start),
          'Lullaby noncanonical compressed stream')
    _need(isinstance(receipt, dict) and receipt.get('language') in ('EN', 'IT')
          and receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after), 'Lullaby receipt identity')
    return {'ok': True, 'slot': [start, end],
            'logical_changed_bytes': sum(a != b for a, b in zip(BEFORE, AFTER)),
            'container_unchanged': True, 'decoders_agree': True}
