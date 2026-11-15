#!/usr/bin/env python3
"""Authenticate cached EN filesystem resources without a ROM model or CPU.

Inputs remain private. The JSON receipt contains identities and addresses,
never extracted table contents. The optional IT comparison does not transfer
EN RAM/FAT or claim a natural Italian caller.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import struct

EN = ('2e30d6960bb059615fca7527700d86f8282e82ccbe99bf62e22f027453dc3d3d',152786844)
IT = ('13ebac02bdea3036511773587e6603ce6834e25f4b13d1a4662c3e954bfd5d4a',159029760)
SNAPSHOT_SHA = '28903b369f17bd56ab12949ec66f60b323839d1bb431d4f8e0bf384d2e026c7e'
FAT_SHA = '51bb4a3635df58a8bf5d2ee3f33d778e891a23bda1e4be54b75169d9f28b5b0a'
FNT_SHA = '80816c1f6829d388b81d53fa9b5eb5fd65dbef654c8fb03e0735cad714b03afe'
ARC = 0x021E3654
FAT = 0x023BE580
FNT = 0x023BF588
FILE = 0x022F0000
TOP = 0x023FD000
COMPONENTS = {
    'seekdir':(0x020D6BEC,152,'3b0c0a3721993fdf50396c8cf2102e1ea43f92149f4f763586d919e21d680f81'),
    'read_table':(0x020D6AA0,192,'0119efeea4f6d4bdf200624a7ff9c3cee2790fee1e8f8ea8592420ed4aaebf92'),
    'read_memory':(0x020D7484,24,'b433aaee1c510f86a113d1fe9b857435b6f615e96df11f285c1e8991d6eae0a0'),
    'copy':(0x020D4A50,384,'369b6f2e559f13da0a9ba7a741ebf8ca3213db866a8f4eb97460809d8b54b86e'),
}


def need(condition, message):
    if not condition:raise ValueError(message)


def sha(blob):return hashlib.sha256(blob).hexdigest()


def file_sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(65536),b''):digest.update(chunk)
    return digest.hexdigest()


def u32(blob, offset):return struct.unpack_from('<I',blob,offset)[0]


def require_disjoint(regions):
    spans=[]
    for name,(start,size) in regions.items():
        need(type(start)is int and type(size)is int and 0<=start<2**32 and
             0<size<=2**32-start,'invalid range '+name)
        spans.append((start,start+size,name))
    spans.sort()
    for left,right in zip(spans,spans[1:]):
        need(left[1]<=right[0],f'overlap {left[2]} / {right[2]}')


def extract_snapshot(path,regions,expected_size,expected_sha,base=0x02000000):
    """Hash a bounded decompressed input and retain only requested slices."""
    need(type(expected_size)is int and 0<expected_size<=4*1024**2,'snapshot size bound')
    need(Path(path).is_file() and Path(path).stat().st_size<=8*1024**2,'compressed input budget')
    for name,(start,size) in regions.items():
        need(type(start)is int and type(size)is int and size>0 and
             base<=start and start+size<=base+expected_size,'snapshot range '+name)
    result={name:bytearray() for name in regions};digest=hashlib.sha256();offset=0
    with gzip.open(path,'rb') as stream:
        while True:
            chunk=stream.read(min(65536,expected_size-offset+1))
            if not chunk:break
            need(offset+len(chunk)<=expected_size,'snapshot exceeds expected size')
            digest.update(chunk)
            for name,(address,size) in regions.items():
                begin=max(address-base,offset);end=min(address-base+size,offset+len(chunk))
                if begin<end:result[name].extend(chunk[begin-offset:end-offset])
            offset+=len(chunk)
    need(offset==expected_size,'snapshot short size')
    need(digest.hexdigest()==expected_sha,'snapshot SHA256 mismatch')
    return {name:bytes(blob) for name,blob in result.items()}


def inspect_tables(header,arc,fat,fnt,rom_size):
    """Check SDK cache relations and root metadata; not a full FNT parser."""
    need(len(header)==512 and len(arc)==92,'header/ARC size')
    fat_off,fat_size=u32(header,0x48),u32(header,0x4c)
    fnt_off,fnt_size=u32(header,0x40),u32(header,0x44)
    need(len(fat)==fat_size and fat_size>0 and fat_size%8==0 and len(fnt)==fnt_size and fnt_size>=8,'table size')
    need(fat_off+fat_size<=rom_size and fnt_off+fnt_size<=rom_size,'table physical bounds')
    need(arc[:4]==b'rom\0' and u32(arc,28)==7,'registered loaded cached ARC flags')
    need(u32(arc,40)==0,'absolute ROM base')
    need(u32(arc,60)==fat_off and u32(arc,64)==fnt_off,'ARC backup offsets')
    need(u32(arc,48)==fat_size and u32(arc,56)==fnt_size,'ARC table size')
    fat_ram,fnt_ram=u32(arc,44),u32(arc,52)
    need(fat_ram+fat_size==fnt_ram,'cached tables contiguous')
    aligned=(u32(arc,68)+31)&~31
    need(aligned==fat_ram,'cache load alignment')
    need(0x02000000<=fat_ram<fnt_ram and fnt_ram+fnt_size<=0x02400000,'cache RAM range')
    need(u32(arc,80)==0x020D7484,'absolute memory table callback')
    require_disjoint({'fat':(fat_ram,fat_size),'fnt':(fnt_ram,fnt_size)})
    for i in range(0,len(fat),8):
        start,end=struct.unpack_from('<II',fat,i)
        need(start<=end<=rom_size,'FAT file bounds')
    start,first,count=struct.unpack_from('<IHH',fnt)
    need(0<count<=0x1000 and start==8*count and start<fnt_size,'root directory count/start')
    overlays=0
    for offset in (0x50,0x58):
        table_off,table_size=struct.unpack_from('<II',header,offset)
        need(table_size%32==0 and table_off+table_size<=rom_size,'overlay table bounds')
        overlays+=table_size//32
    need(first==overlays and first<=fat_size//8,'root first file / overlay count')
    return dict(root=dict(start=start,first_file=first,directory_count=count),
                load_alignment=aligned,fat_ram=fat_ram,fnt_ram=fnt_ram,
                fat_offset=fat_off,fnt_offset=fnt_off,fat_bytes=fat_size,fnt_bytes=fnt_size,
                table_func=u32(arc,80),read_func=u32(arc,72))


def read_rom(path,identity):
    path=Path(path);digest,size=identity
    need(path.stat().st_size==size and file_sha(path)==digest,'exact ROM identity')
    with path.open('rb') as stream:
        h=stream.read(512);arm_off,arm_ram,arm_size=u32(h,0x20),u32(h,0x28),u32(h,0x2c)
        need(h[12:16]==b'IPKE' and h[30]==0 and arm_off==0x4000 and arm_ram==0x02000000,'ROM header identity/mapping')
        parts={};offsets={}
        for name,(address,length,expected) in COMPONENTS.items():
            need(arm_ram<=address and address+length<=arm_ram+arm_size,'component inside ARM9')
            offset=arm_off+address-arm_ram;stream.seek(offset);blob=stream.read(length)
            need(len(blob)==length and sha(blob)==expected,'physical component '+name)
            parts[name]=blob;offsets[name]=offset
        for name,offset_pos in (('fat',0x48),('fnt',0x40)):
            offset,length=struct.unpack_from('<II',h,offset_pos)
            need(0<length<=65536 and offset+length<=size,'table bounded ROM read')
            stream.seek(offset);parts[name]=stream.read(length)
    return h,parts,dict(sha256=digest,bytes=size,game_code='IPKE',revision=0,
                        arm9=dict(rom_offset=arm_off,ram=arm_ram,bytes=arm_size),component_offsets=offsets)


def prepare(rom,snapshot=None,it_rom=None):
    header,parts,identity=read_rom(rom,EN)
    regions={name:(a,n) for name,(a,n,_) in COMPONENTS.items()}
    regions.update(arc=(ARC,92),fat=(FAT,4104),fnt=(FNT,2902))
    if snapshot is None:
        # A reproducible isolated fixture, explicitly not captured runtime state.
        arc=bytearray(92);arc[:4]=b'rom\0'
        values={28:7,44:FAT,48:len(parts['fat']),52:FNT,56:len(parts['fnt']),
                60:u32(header,0x48),64:u32(header,0x40),68:FAT,80:0x020D7484}
        for offset,value in values.items():struct.pack_into('<I',arc,offset,value)
        natural={**parts,'arc':bytes(arc)}
        provenance=dict(mode='ROM-derived tables and synthetic ARC',natural_state=False)
    else:
        natural=extract_snapshot(snapshot,regions,4194304,SNAPSHOT_SHA)
        provenance=dict(mode='authenticated historical EN MainRAM',natural_state=True,
            compressed_sha256=file_sha(snapshot),bytes=4194304,sha256=SNAPSHOT_SHA,
            format='MainRAM only; no DTCM or natural SeekDir entry')
    for name in parts:need(natural[name]==parts[name],'natural/ROM bytes '+name)
    need(sha(natural['fat'])==FAT_SHA and sha(natural['fnt'])==FNT_SHA,'natural table identities')
    tables=inspect_tables(header,natural['arc'],natural['fat'],natural['fnt'],identity['bytes'])
    need(tables['root']==dict(start=368,first_file=129,directory_count=46),'exact root identity')
    arena={'arc':(ARC,92),'fat':(FAT,4104),'fnt':(FNT,2902),
           'file_with_guards':(FILE-16,104),'stack_and_guard':(TOP-128,128)}
    arena.update({name:(a,n)for name,(a,n,_)in COMPONENTS.items()})
    require_disjoint(arena)
    receipt=dict(schema='native-fs-cached-resources-v1',tool_sha256=sha(Path(__file__).read_bytes()),
        ROM=identity,resource_provenance=provenance,tables=tables,
        natural_regions={name:dict(ram=a,bytes=n,sha256=sha(natural[name])) for name,(a,n)in regions.items()},
        synthetic_arenas={name:dict(ram=a,bytes=n) for name,(a,n)in arena.items()if name in('file_with_guards','stack_and_guard')},
        cpu_executed=False,compiler_invoked=False,
        limits=['Root metadata/cache identity only; no complete filesystem semantics or natural caller',
                'Physical ARM9 windows agree with authenticated runtime RAM; decoder checked separately',
                'Synthetic CPU/File/stack arenas are not an observed allocation or DTCM image'])
    if it_rom:
        _,it_parts,it_id=read_rom(it_rom,IT)
        need(it_parts['fnt']==natural['fnt'],'IT FNT identity')
        for name in COMPONENTS:need(it_parts[name]==parts[name],'IT code identity '+name)
        receipt['IT_comparison']=dict(ROM=it_id,fnt_equal=True,code_equal=True,
            fat_equal=it_parts['fat']==natural['fat'],fat_sha256=sha(it_parts['fat']),natural_IT_state=False)
    return receipt,natural


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--snapshot',type=Path,
        help='Optional exact historical MainRAM gzip; omitted means ROM-derived synthetic ARC')
    p.add_argument('--it-rom',type=Path);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        need(not a.json.exists() and not a.json.is_symlink(),'fresh receipt output required')
        receipt,_=prepare(a.rom,a.snapshot,a.it_rom)
        with a.json.open('x') as out:out.write(json.dumps(receipt,indent=2)+'\n')
    except (ValueError,OSError,EOFError) as error:p.exit(2,str(error)+'\n')
    print('ROM resources authenticated; see resource_provenance for captured/synthetic ARC; no CPU/compiler')


if __name__=='__main__':main()
