"""Final V1.3.2 title in the existing project-owned 48x16 pixel slot.

No archive growth, executable, header, library icon or persistent data changes.
The previous V1.3 pixels and exact title map are required before replacement.
"""
import hashlib
from sgp12 import titolo_versione as container
from sgp13 import title as previous

LABEL = 'V1.3.2'
LABEL_SHA256 = 'eb340a9c119115296bb308c23c30bd9ff77ffb49877e7d0e83f306d8c0b8ba99'
GLYPHS = dict(previous.GLYPHS, **{
    '2': ('11110', '00001', '00001', '11110', '10000', '10000', '11111'),
})

def _sha(data):
    return hashlib.sha256(data).hexdigest()

def pixels():
    canvas = [[0] * 48 for _ in range(16)]
    ink = [(i * 6 + x, y) for i, char in enumerate(LABEL)
           for y, row in enumerate(GLYPHS[char]) for x, value in enumerate(row) if value == '1']
    for x, y in ink:
        canvas[y + 6][x + 1] = 4
    for x, y in ink:
        canvas[y + 5][x] = 14
    return bytes(canvas[y][tile * 8 + x] | canvas[y][tile * 8 + x + 1] << 4
                 for row in range(2) for tile in range(6)
                 for y in range(row * 8, row * 8 + 8) for x in range(0, 8, 2))

def span(data):
    parts = container.membri(data)
    graphics, tilemap = parts[15][1], parts[17][1]
    if (len(graphics) != 3136 or len(tilemap) != 1572
            or graphics[848:1232] != previous.pixels()
            or tilemap[1446:1458] != bytes.fromhex('19701a701b701c701d701e70')
            or tilemap[1510:1522] != bytes.fromhex('1f7020702170227023702470')):
        raise ValueError('V1.3 title preimage')
    return parts[15][0] + 848, 384

def apply(data, language):
    if type(data) is not bytes or language not in ('EN', 'IT'):
        raise ValueError('immutable ROM and supported language required')
    at, size = span(data)
    after = data[:at] + pixels() + data[at + size:]
    receipt = {'schema': 1, 'stage': 'identity', 'language': language, 'label': LABEL,
               'offset': at, 'bytes': size, 'input_sha256': _sha(data), 'output_sha256': _sha(after),
               'pixel_sha256': _sha(after[at:at + size])}
    verify(data, after, receipt)
    return after, receipt

def verify(before, after, receipt):
    at, size = span(before)
    if (len(after) != len(before) or after[:at] != before[:at]
            or after[at + size:] != before[at + size:]
            or _sha(after[at:at + size]) != LABEL_SHA256):
        raise ValueError('identity changed bytes outside the final label or wrong pixels')
    expected = {'schema': 1, 'stage': 'identity', 'language': receipt.get('language'), 'label': LABEL,
                'offset': at, 'bytes': size, 'input_sha256': _sha(before), 'output_sha256': _sha(after),
                'pixel_sha256': _sha(after[at:at + size])}
    if expected['language'] not in ('EN', 'IT') or receipt != expected:
        raise ValueError('identity receipt mismatch')
    return dict(expected, static_verified=True, save_and_code_unchanged=True)
