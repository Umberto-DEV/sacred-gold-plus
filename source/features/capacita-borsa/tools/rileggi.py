"""Independent postimage reader: no import or call of the applicator."""
import hashlib,json,struct,tempfile
from pathlib import Path
from sgp12.rom import Arm9,Rom,esigi,posizioni_diverse

def rileggi(prima,dopo,build_dir):
    before,after=bytes(prima),bytes(dopo)
    esigi(len(before)==len(after),'CAPACITY READER: ROM length changed')
    build=Path(build_dir);man=json.loads((build/'manifesto.json').read_text())
    blob=(build/'blob.bin').read_bytes()
    esigi(man['blob']=={'byte':len(blob),'sha256':hashlib.sha256(blob).hexdigest()},'CAPACITY READER: build mismatch')
    hooks=[(0x2078188,'new',False),(0x20781a0,'init',False),(0x20781b4,'copy',False),
      (0x20781c4,'registered1',False),(0x20781d0,'registered2',False),
      (0x20781dc,'register',False),(0x2078208,'unregister',False),
      (0x2078240,'pocket',True),(0x20784c4,'not_empty',False),
      (0x2078644,'view',False),(0x2078724,'slot',False),(0x207879c,'get',False),
      (0x2077b5c,'move',True),(0x2027ad4,'load',False),(0x2027c18,'save',False)]
    allowed=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'check.nds';path.write_bytes(after);arm=Arm9(path)
        esigi(arm.leggi(0x23dbf00,0x2c00)==blob+bytes(0x2c00-len(blob)),'CAPACITY READER: code/state changed')
        allowed.append((arm.off(0x23dbf00),arm.off(0x23dbf00)+0x2c00))
        for address,name,preserve in hooks:
            size=16 if preserve else 8;raw=arm.leggi(address,size)
            expected=(0xb408,0x4b02,0x469c,0xbc08,0x4760,0x46c0) if preserve else (0x4b00,0x4718)
            esigi(struct.unpack('<'+'H'*len(expected),raw[:-4])==expected,'CAPACITY READER: ABI veneer '+name)
            target=struct.unpack('<I',raw[-4:])[0]
            esigi(target==int(man['simboli']['sgp_cap_'+name],16)|1,'CAPACITY READER: target '+name)
            esigi(target&1 and 0x23dbf00 <= (target&~1) < 0x23dbf00+len(blob),'CAPACITY READER: target outside code')
            off=arm.off(address);allowed.append((off,off+size))
    r0,r1=Rom(before),Rom(after)
    i0,_,v0=r0.immagine_overlay(15);i1,_,v1=r1.immagine_overlay(15)
    esigi(i0==i1,'CAPACITY READER: y9 changed')
    f0=r0.voce_fat(i0['file_id']);f1=r1.voce_fat(i1['file_id'])
    esigi(f0==f1,'CAPACITY READER: FAT changed')
    allowed.append((f1['inizio'],f1['fine']))
    esigi(all(any(lo<=p<hi for lo,hi in allowed) for p in posizioni_diverse(before,after)),'CAPACITY READER: write outside declared ranges')
    words={0x21f95f4:(4,0xf38),0x21fa004:(4,0xd40),0x22001c0:(4,0xd40),
           0x21fa022:(2,0x2cfc),0x21fa03c:(2,0x2cfc)}
    for a,r in [(0x21f9f50,1),(0x21f9fac,1),(0x21fa00a,6),(0x21fa02a,6),(0x21fd746,1),
                (0x21ff43e,2),(0x21ff45e,2),(0x21ff47a,2),(0x21ff536,2)]:words[a]=(2,0x2000+r*256+0x95)
    edited=set()
    for address,(n,value) in words.items():
        off=address-i1['ram'];esigi(int.from_bytes(v1[off:off+n],'little')==value,'CAPACITY READER: UI layout at %#x'%address)
        edited.update(range(off,off+n))
    for address in (0x22008b0,0x22008c8):
        off=address-i1['ram'];esigi(v1[off:off+8]==bytes([252,42,30,102,66,12,30,60]),'CAPACITY READER: pocket counts')
        edited.update(range(off,off+8))
    esigi(all(p in edited for p in posizioni_diverse(v0,v1)),'CAPACITY READER: unrelated UI edit')
    return {'strumento':'capacita_borsa.rilettore_indipendente','esito':'VERDE','ganci':len(hooks),'tasche':8,'rom_bytes':len(after)}
