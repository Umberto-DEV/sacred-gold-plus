"""Repair the two transposed Ghost multipliers in the Plus damage chart.

Sacred Gold Plus carries a dense 18-by-18 chart in overlay 18.  Its Ghost to
Dragon cell contains 5 (half damage) while Ghost to Dark contains 10 (neutral),
the reverse of the intended modern chart.  Only the multiplier byte of those
two records changes; the three special records after the matrix, overlay
geometry and save data stay untouched.
"""
import hashlib


OVERLAY_ID = 18
OVERLAY_BASE = 0x021E5900
OVERLAY_SIZE = 0x16940
CHART_ADDRESS = 0x021FBE60
CHART_OFFSET = CHART_ADDRESS - OVERLAY_BASE
MATRIX_RECORDS = 18 * 18 - 2  # Normal/Fighting -> Ghost follow the marker for Scrappy.
TRAILER_RECORDS = 3
CHART_SHA256 = '5333d63fc8f855a92975aa413da488e25b4d07d36ef968ba0b7f1f894bc80121'
OVERLAY_SHA256 = '26746890b5bbfba1bc5a82f3fea8fac383f76a56799977e45910a033fa3c4463'
GHOST_DRAGON = 0x16704
GHOST_DARK = 0x16707
PATCHES = (
    (GHOST_DRAGON + 2, bytes([5]), bytes([10])),
    (GHOST_DARK + 2, bytes([10]), bytes([5])),
)
LANGUAGES = ('EN', 'IT')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def overlay(data):
    from sgp12.rom import Rom
    entry, _, image = Rom(bytes(data)).immagine_overlay(OVERLAY_ID)
    if (entry['ram'], entry['ram_size']) != (OVERLAY_BASE, OVERLAY_SIZE):
        raise ValueError('overlay 18 placement differs from the supported Plus build')
    return bytes(image)


def rows(image):
    """Return the 324 matrix records and the three pre-terminator controls."""
    image = bytes(image)
    if len(image) != OVERLAY_SIZE:
        raise ValueError('overlay 18 image size differs')
    records = []
    offset = CHART_OFFSET
    while offset < len(image) and image[offset] != 0xFF:
        if offset + 3 > len(image):
            raise ValueError('modern type chart is truncated')
        records.append(tuple(image[offset:offset + 3]))
        offset += 3
    if offset >= len(image) or image[offset:offset + 3] != b'\xff\xff\xff':
        raise ValueError('modern type chart terminator differs')
    expected = MATRIX_RECORDS + TRAILER_RECORDS
    if len(records) != expected:
        raise ValueError('modern type chart record count differs')
    return records[:MATRIX_RECORDS], records[MATRIX_RECORDS:]


def _chart_bytes(image):
    end = CHART_OFFSET + (MATRIX_RECORDS + TRAILER_RECORDS) * 3 + 1
    return bytes(image[CHART_OFFSET:end])


def patch_overlay(image, *, overlay_sha256=OVERLAY_SHA256,
                  chart_sha256=CHART_SHA256):
    image = bytes(image)
    matrix, trailer = rows(image)
    if _sha(image) != overlay_sha256:
        raise ValueError('overlay 18 differs from the pinned Plus build')
    if _sha(_chart_bytes(image)) != chart_sha256:
        raise ValueError('modern type chart differs from the pinned Plus build')
    by_pair = {(attack, defend): multiplier for attack, defend, multiplier in matrix}
    if by_pair.get((7, 16)) != 5 or by_pair.get((7, 17)) != 10:
        raise ValueError('Ghost multiplier preimages differ')
    if trailer != [(0xFE, 0xFE, 0), (0, 7, 0), (1, 7, 0)]:
        raise ValueError('modern type chart control records differ')
    result = bytearray(image)
    for offset, before, after in PATCHES:
        if result[offset:offset + 1] != before:
            raise ValueError('Ghost multiplier byte differs at %#x' % offset)
        result[offset:offset + 1] = after
    result = bytes(result)
    changed = [i for i, (old, new) in enumerate(zip(image, result)) if old != new]
    return result, {
        'changed_offsets': changed,
        'cells': [
            {'attack': 7, 'defend': 16, 'before': 5, 'after': 10},
            {'attack': 7, 'defend': 17, 'before': 10, 'after': 5},
        ],
        'overlay_sha256_before': _sha(image),
        'overlay_sha256_after': _sha(result),
        'chart_sha256_before': _sha(_chart_bytes(image)),
        'chart_sha256_after': _sha(_chart_bytes(result)),
    }


def apply(data, language):
    from sgp12.overlay import applica
    if language not in LANGUAGES:
        raise ValueError('unknown language %r; expected EN or IT' % (language,))
    data = bytes(data)
    before_image = overlay(data)
    expected, details = patch_overlay(before_image)
    edits = []
    for offset, preimage, replacement in PATCHES:
        address = OVERLAY_BASE + offset
        edits.append({'addr': address, 'pre': preimage, 'post': replacement})
    result, writer = applica(
        data, OVERLAY_ID,
        [(item['addr'], item['pre']) for item in edits], edits)
    if overlay(result) != expected:
        raise ValueError('overlay 18 readback differs from the verified chart patch')
    receipt = {'stage': 'damage-chart', 'language': language,
               'input_sha256': _sha(data), 'output_sha256': _sha(result),
               'patch': details, 'writer': writer}
    receipt['verification'] = verify(data, result, receipt)
    return result, receipt


def verify(before, after, receipt):
    from sgp12.blz import blz_comprimi_ottimo
    from . import ui_verify
    before, after = bytes(before), bytes(after)
    if len(before) != len(after):
        raise ValueError('damage-chart stage changed ROM length')
    old, new = ui_verify.Image(before), ui_verify.Image(after)
    if old.records != new.records or old.files != new.files:
        raise ValueError('damage-chart stage changed y9 or FAT geometry')
    if before[:0x200] != after[:0x200]:
        raise ValueError('damage-chart stage changed the cartridge header')
    file_id = old.records[OVERLAY_ID][6]
    start, end = old.files[file_id]
    restored = bytearray(after)
    restored[start:end] = before[start:end]
    if bytes(restored) != before:
        raise ValueError('damage-chart stage changed bytes outside overlay 18')
    before_image, after_image = overlay(before), overlay(after)
    expected, details = patch_overlay(before_image)
    if after_image != expected:
        raise ValueError('damage-chart output differs from the two declared cells')
    canonical = blz_comprimi_ottimo(after_image, bersaglio=end - start)
    if canonical != after[start:end]:
        raise ValueError('overlay 18 BLZ stream is not canonical fixed-size output')
    if not isinstance(receipt, dict) or receipt.get('input_sha256') != _sha(before) \
            or receipt.get('output_sha256') != _sha(after):
        raise ValueError('damage-chart receipt hashes differ from the ROMs')
    writer = receipt.get('writer', {})
    if writer.get('ingresso_sha256') != _sha(before) \
            or writer.get('uscita_sha256') != _sha(after):
        raise ValueError('overlay writer receipt hashes differ from the ROMs')
    return {'ok': True, 'logical_changed_bytes': len(details['changed_offsets']),
            'overlay_sha256_before': details['overlay_sha256_before'],
            'overlay_sha256_after': details['overlay_sha256_after'],
            'compressed_bytes': end - start}


def span(data):
    from . import ui_verify
    image = ui_verify.Image(bytes(data))
    file_id = image.records[OVERLAY_ID][6]
    return image.files[file_id]
