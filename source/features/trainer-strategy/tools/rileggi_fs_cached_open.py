#!/usr/bin/env python3
"""Read the complete cached Open components and independent FAT metadata.

No payload or CPU is read/executed. Reuse exact Convert resources and explicit
BSS provenance; the client FSFile and native stack will be a new fixture.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_cached_convert.py'),'open_parent_resources')
R,need,sha=L.R,L.need,L.sha
NEW={
 'open':(0x020D8278,72,'844c19c244efe83b1be9dd83f73da60917d201793d237d72cf0a429ca9158a2d'),
 'fast':(0x020D8208,112,'465013782ef4760fff5100c626a4ddc63e8611d1517a1b9bc105b23092638bd9'),
 'fast_command':(0x020D7340,128,'b8f19fba6a413a29a20b56c8a6d404d3eae2dd4282424fa398e0dc986f91bee4'),
 'direct_command':(0x020D73C0,40,'88d89e44e514c13c621af01ddd078a8fc112dcbce021ebd2d90b1ef53788bfaf')}
COMPONENTS={**L.COMPONENTS,**NEW}
POOLS=L.POOLS
CODE_SPANS=tuple((a,n-POOLS.get(name,0))for name,(a,n,_)in COMPONENTS.items()if name!='default_table')


def fat_metadata(fat,file_id,declared_size):
    """Finite ID140 contract, including the native strict-start bounds check.

    Not an arbitrary archive validator: source accepts size > index*8, without
    checking size >= index*8+8. The actual authenticated FAT is fully present.
    """
    need(type(fat)is bytes and type(file_id)is int and file_id==140 and
         type(declared_size)is int and 0<=declared_size<=len(fat),'typed finite FAT140 metadata')
    offset=file_id*8
    if declared_size<=offset:return dict(success=False,file_id=file_id,offset=offset,FSResult=1)
    need(offset+8<=len(fat),'physical FAT record bounds')
    top,bottom=struct.unpack_from('<II',fat,offset);need(top<=bottom,'FAT extent order')
    return dict(success=True,file_id=file_id,offset=offset,FSResult=0,top=top,bottom=bottom,bytes=bottom-top)


def physical(rom):
    pieces={};rows={}
    with Path(rom).open('rb')as f:
        h=f.read(512);off,ram,size=R.u32(h,0x20),R.u32(h,0x28),R.u32(h,0x2c)
        for name,(a,n,digest)in NEW.items():
            need(ram<=a and a+n<=ram+size,'initialized Open component bounds '+name)
            pos=off+a-ram;f.seek(pos);b=f.read(n)
            need(len(b)==n and sha(b)==digest,'physical Open component '+name)
            pieces[name]=b;rows[name]=dict(ram=a,rom_offset=pos,bytes=n,sha256=digest)
    return pieces,rows


def prepare(rom,snapshot=None,it_rom=None):
    parent,parts=L.prepare(rom,snapshot,it_rom);extra,rows=physical(rom);parts.update(extra)
    if snapshot:
        slices=R.extract_snapshot(snapshot,{k:(a,n)for k,(a,n,_)in NEW.items()},4194304,R.SNAPSHOT_SHA)
        need(slices==extra,'new Open snapshot/ROM components')
    if it_rom:need(physical(it_rom)[0]==extra,'IT Open code identity')
    need((R.u32(parts['default_table'],24),R.u32(parts['default_table'],28))==(0x20d7340,0x20d73c0),'default table Fast6/Direct7 targets')
    meta=fat_metadata(parts['fat'],140,len(parts['fat']))
    need((meta['top'],meta['bottom'])==(0x1093800,0x109645c),'actual FAT140 extent')
    return dict(schema='native-fs-cached-open-resources-v1',tool_sha256=sha(HERE.read_bytes()),parent=parent,
        new_components=rows,file_metadata=meta,total_component_bytes=4092,cpu_executed=False,compiler_invoked=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        source=HERE.parents[3];need(source!=a.json.resolve()and source not in a.json.resolve().parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh receipt output required');receipt,_=prepare(a.rom,a.snapshot,a.it_rom)
        with a.json.open('x')as out:out.write(json.dumps(receipt,indent=2)+'\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Full Open components and cached FAT140 metadata verified; no CPU/compiler/payload')


if __name__=='__main__':main()
