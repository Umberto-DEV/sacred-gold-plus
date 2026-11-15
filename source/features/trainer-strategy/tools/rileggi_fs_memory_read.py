#!/usr/bin/env python3
"""Authenticate memory-archive Read components and two owned NARC windows.

Only small metadata/payload slices are read; no complete archive is extracted.
The memory payload configuration is explicit, separate from natural CARD I/O.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_cached_open.py'),'read_parent_resources')
R,need,sha=L.R,L.need,L.sha
RETAINED={'close': (34439872,
           60,
           'b6264f39c82988fab2b720bff3277219d7d9bb14d4ed0abe768d4f1f561b2e26'),
 'read_core': (34439428,
               124,
               '10e97eb8d4fed727a55cf2ac3f9851ff0abd332b427a67189ad13b5b9d4008ae'),
 'read_wrapper': (34440140,
                  16,
                  '501741a75e11deaadaf8bd6856124771f09fa272502e3fa6752c1340d19c0aa3'),
 'seek': (34440156,
          108,
          '99e8a8db572238f5c2aa23d35ddfe505843277a0623dedfe207c2d5872236747'),
 'wait': (34439932,
          192,
          '74a4b27bab72e380afd92fbdf9cae9b524f24641668dae54a2af802184caf167')}
NEW={
 'read_command':(0x020D6B94,44,'a28edc117522c9993df5831add97fc2e04ddc068c75ede7da505e73b72cfdd76'),
 'read_callback':(0x020D7448,28,'f5075f0378cb58f5f03c91e634ac04828ffd4f545c9b59316d833a04d3feb86e'),
 'close_command':(0x020D73E8,8,'6dcd5e75586fe6683156c0d559d4827b73bd48d501fa5781a1c6099aacd7c877')}
EXTRA={**RETAINED,**NEW}
COMPONENTS={**L.COMPONENTS,**EXTRA}
POOLS={**L.POOLS,'read_wrapper':4}
CODE_SPANS=tuple((a,n-POOLS.get(name,0))for name,(a,n,_)in COMPONENTS.items()if name!='default_table')
DRIVER,DRIVER_CODE,DRIVER_BYTES=0x022F0800,108,116
HEADER_DEST,MEMBER_DEST,RESULT=0x022F0200,0x022F0240,0x022F0280
HEADER_SOURCE,MEMBER_SOURCE,ARCHIVE_BASE=0x02310020,0x0231226c,0x0127c820
HEADER_SHA='6ee74f5eec705d828dc93263a65dbbf260a9bbaa561e8c35d1b6caaa5bc1ff47'
MEMBER_SHA='85ac8d2ffc1e263ba41dfed64ea9b07613bd3fe76e8a68ef13e93394179dc5c8'


def narc_metadata(read,file_start,file_size,member=310):
    """Read bounded metadata independently; do not load an entire NARC object."""
    need(all(type(x)is int for x in(file_start,file_size,member))and file_start>=0 and
         16<=file_size<=1024**2 and 0<=member<65536,'typed bounded NARC selection')
    windows=[]
    def piece(offset,n):
        need(type(offset)is int and type(n)is int and 0<=offset and 0<n<=16 and offset+n<=file_size,'NARC physical slice bounds')
        blob=read(file_start+offset,n);need(type(blob)is bytes and len(blob)==n,'complete NARC physical slice')
        windows.append(dict(rom_offset=file_start+offset,bytes=n,sha256=sha(blob)));return blob
    header=piece(0,16);magic,bom,version,total,header_size,blocks=struct.unpack('<4sHHIHH',header)
    need(magic==b'NARC'and bom==0xfffe and version==0x100 and total==file_size and header_size==16 and blocks==3,'NARC header identity/layout')
    btaf=piece(16,12);magic,btaf_size,count,reserved=struct.unpack('<4sIHH',btaf)
    need(magic==b'BTAF'and reserved==0 and 0<count<=65535 and member<count and btaf_size==12+count*8,'NARC BTAF count/size/member')
    start,end=struct.unpack('<II',piece(28+member*8,8));need(start<=end,'NARC member order')
    btnf_offset=16+btaf_size;magic,btnf_size=struct.unpack('<4sI',piece(btnf_offset,8))
    need(magic==b'BTNF'and btnf_size>=8,'NARC BTNF layout')
    gmif_offset=btnf_offset+btnf_size;magic,gmif_size=struct.unpack('<4sI',piece(gmif_offset,8))
    need(magic==b'GMIF'and gmif_size>=8 and gmif_offset+gmif_size==file_size and end<=gmif_size-8,'NARC GMIF/member extent')
    offset=gmif_offset+8+start;need(end-start==16,'finite sixteen-byte member')
    payload=piece(offset,16)
    return dict(member=member,member_count=count,btaf_offset=16,btaf_size=btaf_size,btnf_offset=btnf_offset,
        btnf_size=btnf_size,gmif_offset=gmif_offset,gmif_size=gmif_size,member_start=start,member_end=end,
        member_file_offset=offset,member_bytes=16,physical_reads=windows),header,payload


def physical(rom):
    pieces={};rows={}
    with Path(rom).open('rb')as f:
        h=f.read(512);off,ram,size=R.u32(h,0x20),R.u32(h,0x28),R.u32(h,0x2c)
        for name,(a,n,digest)in EXTRA.items():
            need(ram<=a and a+n<=ram+size,'initialized Read component bounds '+name)
            pos=off+a-ram;f.seek(pos);blob=f.read(n)
            need(len(blob)==n and sha(blob)==digest,'physical Read component '+name)
            pieces[name]=blob;rows[name]=dict(ram=a,rom_offset=pos,bytes=n,sha256=digest)
        f.seek(R.u32(h,0x48)+140*8);start,end=struct.unpack('<II',f.read(8))
        need((start,end)==(0x1093800,0x109645c),'actual owned file140 FAT extent')
        def read(pos,n):f.seek(pos);return f.read(n)
        meta,header,payload=narc_metadata(read,start,end-start)
    need(meta['member_file_offset']==0x224c and meta['member_count']==471 and sha(header)==HEADER_SHA and sha(payload)==MEMBER_SHA,'exact owned NARC header/member identities')
    need(ARCHIVE_BASE+start==HEADER_SOURCE and ARCHIVE_BASE+start+meta['member_file_offset']==MEMBER_SOURCE,'nonwrapping memory archive translation')
    pieces.update(narc_header=header,narc_member=payload)
    return pieces,rows,meta


def prepare(rom,snapshot=None,it_rom=None):
    parent,parts=L.prepare(rom,snapshot,it_rom);extra,rows,meta=physical(rom);parts.update(extra)
    if snapshot:
        slices=R.extract_snapshot(snapshot,{k:(a,n)for k,(a,n,_)in EXTRA.items()},4194304,R.SNAPSHOT_SHA)
        need(all(slices[k]==parts[k]for k in EXTRA),'Read native snapshot/current ROM code')
    if it_rom:
        it,_,it_meta=physical(it_rom);need(it==extra and it_meta==meta,'IT native code/NARC32 and metadata identity')
    need(R.u32(parts['default_table'],0)==0x20d6b94 and R.u32(parts['default_table'],32)==0x20d73e8,'actual Read0/Close8 default targets')
    return dict(schema='native-fs-memory-read-resources-v1',tool_sha256=sha(HERE.read_bytes()),parent=parent,
        extra_components=rows,narc_metadata=meta,
        payload_provenance='Tiny slices of the owned exact ROM; mapped synthetic memory archive, not captured CARD delivery',
        payload_slices=dict(header=dict(ram=HEADER_SOURCE,bytes=16,sha256=HEADER_SHA),member=dict(ram=MEMBER_SOURCE,bytes=16,sha256=MEMBER_SHA)),
        native_component_bytes=4672,project_driver_included=False,cpu_executed=False,compiler_invoked=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        source=HERE.parents[3];need(source!=a.json.resolve()and source not in a.json.resolve().parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh receipt output required');receipt,_=prepare(a.rom,a.snapshot,a.it_rom)
        with a.json.open('x')as out:out.write(json.dumps(receipt,indent=2)+'\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Native Read components and owned NARC32 authenticated; no CPU/compiler or entire archive extraction')


if __name__=='__main__':main()
