"""Update version labels and library identity while preserving the native icon."""
import hashlib
import struct
from ndspy._common import crc16
from sgp12 import titolo_versione as previous

# Original 5x7 letterforms, matching the footprint of the previous project label.
GLYPHS = {
    '1': ('00100','01100','00100','00100','00100','00100','11111'),
    '.': ('00000','00000','00000','00000','00000','01100','01100'),
    '3': ('11110','00001','00001','01110','00001','00001','11110'),
    ' ': ('00000',)*7,
    'D': ('11110','10001','10001','10001','10001','10001','11110'),
    'E': ('11111','10000','10000','11110','10000','10000','11111'),
    'V': ('10001','10001','10001','10001','10001','01010','00100'),
}


def pixels():
    canvas = [[0]*48 for _ in range(16)]
    ink = [(i*6+x,y) for i,c in enumerate('V1.3')
           for y,row in enumerate(GLYPHS[c]) for x,value in enumerate(row) if value=='1']
    for x,y in ink: canvas[y+6][x+1]=4
    for x,y in ink: canvas[y+5][x]=14
    return bytes(canvas[y][tile*8+x] | canvas[y][tile*8+x+1]<<4
                 for row in range(2) for tile in range(6)
                 for y in range(row*8,row*8+8) for x in range(0,8,2))


def replace_graphics(graphics, tilemap):
    if (len(graphics)!=3136 or len(tilemap)!=1572 or
        hashlib.sha256(graphics[848:1232]).hexdigest()!=previous.LABEL_SHA or
        tilemap[1446:1458]!=bytes.fromhex('19701a701b701c701d701e70') or
        tilemap[1510:1522]!=bytes.fromhex('1f7020702170227023702470')):
        raise ValueError('1.2.5 title label preimage')
    return graphics[:848]+pixels()+graphics[1232:]


def apply(data):
    parts=previous.membri(data)
    start,graphics=parts[15]
    updated=replace_graphics(graphics,parts[17][1])
    result=data[:start]+updated+data[start+len(graphics):]
    checked=previous.membri(result)
    if checked[15][1]!=updated or checked[17]!=parts[17]:
        raise ValueError('development title readback')
    if result[:start+848]!=data[:start+848] or result[start+1232:]!=data[start+1232:]:
        raise ValueError('changed bytes outside development label')
    return result,{'label':'V1.3','pixel_bytes':384,'save_and_code_unchanged':True}


def update_banner(before):
    """Change the six DS library titles, retaining all icon and palette bytes."""
    if len(before) != 0x840 or before[:2] != b'\x01\x00':
        raise ValueError('unsupported library banner format')
    if struct.unpack_from('<H', before, 2)[0] != crc16(before[0x20:]):
        raise ValueError('library banner checksum preimage')
    old = 'Pokémon HeartGold\nNintendo'.encode('utf-16-le').ljust(256, b'\0')
    new = 'Pokémon Sacred Gold Plus\nNintendo'.encode('utf-16-le').ljust(256, b'\0')
    if any(before[i:i + 256] != old for i in range(0x240, 0x840, 256)):
        raise ValueError('library title preimage')
    result = bytearray(before)
    for offset in range(0x240, 0x840, 256):
        result[offset:offset + 256] = new
    struct.pack_into('<H', result, 2, crc16(result[0x20:]))
    return bytes(result)


def apply_banner(data):
    if len(data) < 0x200:
        raise ValueError('missing DS header')
    offset = struct.unpack_from('<I', data, 0x68)[0]
    if offset < 0x200 or offset + 0x840 > len(data):
        raise ValueError('library banner outside ROM')
    before = data[offset:offset + 0x840]
    updated = update_banner(before)
    result = data[:offset] + updated + data[offset + len(updated):]
    return result, {'title': 'Pokémon Sacred Gold Plus', 'languages': 6,
                    'icon_palette_preserved': result[offset + 0x20:offset + 0x240] == before[0x20:0x240],
                    'banner_sha256': hashlib.sha256(updated).hexdigest(),
                    'save_and_code_unchanged': True}
