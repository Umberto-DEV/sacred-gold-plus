"""Project-owned V.1.2.5 pixels in unused tiles of the upper title screen.

Only title NARC members 15 (graphics) and 17 (map) change in place. Existing
logo, palettes, animation, code, file sizes and save data stay intact. The
credit gains the missing descender that made "by" read as "bu".
"""
import struct
from ndspy import fnt
from .rom import esigi, posizioni_diverse, sha

# Small original 5x7 glyphs; these are our label, not extracted game graphics.
GLIFI = {
    'V': ('10001','10001','10001','10001','10001','01010','00100'),
    '.': ('00000','00000','00000','00000','00000','01100','01100'),
    '1': ('00100','01100','00100','00100','00100','00100','11111'),
    '2': ('01110','10001','00001','00010','00100','01000','11111'),
    '5': ('11111','10000','10000','11110','00001','10001','11110'),
}
ORIGINALI = {
    15: '144f13ba71bdacada8eaa824d54eed83550ea0f844c513150a7d0e6277a17fe5',
    17: '849671d31ebe2e8e61317ed0f3142a6b071ef00bd153539fce4bb56a725ddd6b',
}


def etichetta():
    pixels = [[0]*48 for _ in range(16)]
    ink = [(i*6+x,y) for i,c in enumerate('V.1.2.5')
           for y,row in enumerate(GLIFI[c]) for x,p in enumerate(row) if p=='1']
    for x,y in ink: pixels[y+6][x+1]=4  # existing palette: black shadow
    for x,y in ink: pixels[y+5][x]=14    # existing palette: warm white
    return bytes(pixels[y][tile*8+x] | (pixels[y][tile*8+x+1]<<4)
                 for row in range(2) for tile in range(6) for y in range(row*8,row*8+8) for x in range(0,8,2))


def disegna(gfx, tilemap):
    esigi(len(gfx)==3136 and len(tilemap)==1572 and
          gfx[:4]==b'RGCN' and tilemap[:4]==b'RCSN', 'layout titolo inatteso')
    cells=struct.unpack_from('<768H',tilemap,36)
    esigi(not any(gfx[48+25*32:48+38*32]), 'tile versione non vuoti')
    esigi(not any(25 <= (c&1023) < 38 for c in cells), 'tile versione gia referenziati')
    esigi(not any(cells[705:711]+cells[737:743]), 'destinazione versione non vuota')
    esigi(cells[762]==0x740d, 'tile del credito by inatteso')
    g,m=bytearray(gfx),bytearray(tilemap)
    g[848:1232]=etichetta()
    for row in range(2):
        for i in range(6):struct.pack_into('<H',m,36+(705+32*row+i)*2,0x7000+25+6*row+i)
    # Tile 13 is shared. Clone it so only the final letter of 'by' changes.
    # Its screen cell is horizontally flipped: these three pixels complete y.
    clone=bytearray(gfx[48+13*32:48+14*32])
    for pixel in (37,46,47):
        shift=4*(pixel%2);j=pixel//2
        clone[j]=(clone[j] & ~(15<<shift)) | (14<<shift)
    g[1232:1264]=clone
    struct.pack_into('<H',m,1560,0x7425)
    return bytes(g),bytes(m)


def rileggi_membri(prima_g, prima_m, dopo_g, dopo_m):
    """Independent read-back: label pixels, twelve map cells and the credit tile."""
    esigi(len(prima_g)==len(dopo_g)==3136 and len(prima_m)==len(dopo_m)==1572,
          'dimensioni titolo cambiate')
    esigi(prima_g[:848]==dopo_g[:848] and prima_g[1264:]==dopo_g[1264:],
          'grafica fuori dalla versione alterata')
    allowed_map=set(range(1446,1458)) | set(range(1510,1522)) | {1560,1561}
    esigi(set(posizioni_diverse(prima_m,dopo_m)) <= allowed_map,
          'mappa fuori dalla versione/credito alterata')
    esigi(sha(dopo_g[848:1232]) == LABEL_SHA, 'pixel della versione mancanti o errati')
    esigi(dopo_m[1446:1458] == bytes.fromhex('19701a701b701c701d701e70') and
          dopo_m[1510:1522] == bytes.fromhex('1f7020702170227023702470') and
          dopo_m[1560:1562] == bytes.fromhex('2574'), 'mappa versione/credito errata')
    for pixel in range(64):
        old=(prima_g[464+pixel//2] >> (4*(pixel%2)))&15
        new=(dopo_g[1232+pixel//2] >> (4*(pixel%2)))&15
        esigi(new==(14 if pixel in (37,46,47) else old), 'discendente y errato')
    return {'esito':'VERDE','testo':'V.1.2.5','schermo':'superiore',
            'rettangolo_px':[8,176,48,16], 'baseline_testi_y':187,
            'credito':'Developed by A FAN'}


def membri(rom):
    fo,fn=struct.unpack_from('<II',rom,0x40)
    fid=fnt.load(rom[fo:fo+fn]).idOf('a/0/4/6')
    esigi(fid is not None,'NARC del titolo assente')
    fat=struct.unpack_from('<I',rom,0x48)[0]
    start,end=struct.unpack_from('<II',rom,fat+8*fid)
    narc=rom[start:end]
    esigi(narc[:4]==b'NARC','archivio titolo inatteso')
    off,count=struct.unpack_from('<HH',narc,12);sections={}
    for _ in range(count):
        size=struct.unpack_from('<I',narc,off+4)[0]
        esigi(size>=8 and off+size<=len(narc),'sezione NARC invalida')
        sections[narc[off:off+4]]=off;off+=size
    result={}
    for index in (15,17):
        a,b=struct.unpack_from('<II',narc,sections[b'BTAF']+12+8*index)
        absolute=start+sections[b'GMIF']+8+a
        result[index]=(absolute,rom[absolute:absolute+b-a])
    return result


def applica(rom):
    parts=membri(rom)
    for i,(_,data) in parts.items():esigi(sha(data)==ORIGINALI[i], 'titolo precedente inatteso')
    g,m=disegna(parts[15][1],parts[17][1]);out=bytearray(rom)
    for i,data in ((15,g),(17,m)):
        p=parts[i][0];out[p:p+len(data)]=data
    return bytes(out)


def rileggi(prima,dopo):
    a,b=membri(prima),membri(dopo)
    for i in (15,17):
        esigi(a[i][0]==b[i][0] and sha(a[i][1])==ORIGINALI[i], 'titolo di base/posizione errati')
    report=rileggi_membri(a[15][1],a[17][1],b[15][1],b[17][1])
    allowed=set(range(a[15][0]+848,a[15][0]+1264)) | set(range(a[17][0]+1446,a[17][0]+1458)) | set(range(a[17][0]+1510,a[17][0]+1522)) | {a[17][0]+1560,a[17][0]+1561}
    esigi(len(prima)==len(dopo) and set(posizioni_diverse(prima,dopo))<=allowed,
          'modifica fuori dalla grafica versione')
    return report

# SHA of the reviewed project-owned 48x16 label, independent of the writer.
LABEL_SHA = 'ffc55b09a27125dacb6e1e927e3342b6ebebf6281e853895b176efadff9dd2f8'
