"""Update only the existing project-owned title label to the development version."""
import hashlib
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
    ink = [(i*6+x,y) for i,c in enumerate('1.3 DEV')
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
    return result,{'label':'1.3 DEV','pixel_bytes':384,'save_and_code_unchanged':True}
