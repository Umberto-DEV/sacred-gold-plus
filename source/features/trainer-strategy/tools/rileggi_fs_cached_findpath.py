#!/usr/bin/env python3
"""Read exact FindPath components and independently resolve a cached FNT path.

No CPU/compiler, ROM model, extracted file tree or payload read. The parser is
a finite metadata oracle, not a replacement for native filesystem execution.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
R=load(HERE.with_name('rileggi_fs_cached_resources.py'),'cached_find_resources')
need,sha=R.need,R.sha
NEW={
 'findpath':(0x020D6DB0,484,'70727f66b05763ecfc2b1819f4580f5e0aa029b4cd6cc269776d722fa560e63e'),
 'read_dir':(0x020D6C84,300,'15628ccff63ff271734323992030e598370935f555f17feac61e4c01071c088b'),
 'strnicmp':(0x020D6A50,80,'65b5093eaafd96f6f77545aee4103cde48dfd8686795e820c3add61f5fb15c0f'),
 'translate':(0x020D68C0,400,'f1df0f035e516cdfff9df4668530ca636f88b9a1a70d86804b9671c8bce7341a'),
 'default_table':(0x0210E124,36,'a2a3fe2a981c9967141752f3228d54c59d73c639339443bbe0ef04f13319d287')}
COMPONENTS={**R.COMPONENTS,**NEW}
PATH=b'a/0/0/0'


def resolve_path(fnt,path):
    """Resolve a normalized finite file path with ASCII-insensitive names.

    Return independent logical table reads and final directory metadata. No
    byte/halfword ARM access, source opcode count or natural caller is implied.
    """
    need(type(fnt)is bytes and type(path)is bytes and 8<=len(fnt)<=65536,'typed bounded FNT/path')
    need(0<len(path)<=127 and b'\0'not in path,'normalized path bytes')
    segments=path.split(b'/')
    need(all(x and x not in(b'.',b'..')for x in segments),'normalized path segments')
    count=struct.unpack_from('<H',fnt,6)[0]
    need(0<count<=4096 and count*8<len(fnt),'FNT directory count bounds')
    reads=[];directory=0;visited=[];names=[];selected=[]
    def piece(offset,size):
        need(size>0 and 0<=offset and offset+size<=len(fnt),'FNT logical read bounds')
        reads.append(dict(offset=offset,bytes=size));return fnt[offset:offset+size]
    def fold(name):return bytes(x+32 if 65<=x<=90 else x for x in name)
    for level,segment in enumerate(segments):
        need(directory<count,'FNT directory ID bounds')
        visited.append(directory)
        start,index,parent=struct.unpack('<IHH',piece(directory*8,8))
        need(count*8<=start<len(fnt),'FNT directory subtable bounds')
        cursor=start
        while True:
            tag=piece(cursor,1)[0];cursor+=1;length=tag&127
            need(length>0,'FNT file not found')
            name=piece(cursor,length);cursor+=length;is_dir=bool(tag&128)
            child=None
            if is_dir:
                child=struct.unpack('<H',piece(cursor,2))[0]&0xfff;cursor+=2
                need(child<count,'FNT directory ID bounds')
            entry_id=index
            if not is_dir:index+=1
            if fold(name)==fold(segment)and is_dir==(level<len(segments)-1):break
        names.append(name.decode('ascii'))
        selected.append(dict(own_id=directory,start=start,index_before=entry_id,
                             parent_raw=parent,name=name.decode('ascii'),is_directory=is_dir,
                             child_id=child,cursor_after=cursor))
        if is_dir:directory=child
        else:
            return dict(file_id=entry_id,directory_ids=visited,selected_names=names,selected_entries=selected,
                        directory_property=dict(own_id=directory,index=index,offset=cursor,parent=parent&0xfff),
                        table_reads=reads)
    raise ValueError('FNT file not found')


def extra_components(rom,header):
    pieces={};rows={}
    arm_off,arm_ram,arm_size=R.u32(header,0x20),R.u32(header,0x28),R.u32(header,0x2c)
    with Path(rom).open('rb')as stream:
        for name,(address,size,digest)in NEW.items():
            need(arm_ram<=address and address+size<=arm_ram+arm_size,'ARM9 component bounds '+name)
            offset=arm_off+address-arm_ram;stream.seek(offset);blob=stream.read(size)
            need(len(blob)==size and sha(blob)==digest,'FindPath exact physical component '+name)
            pieces[name]=blob;rows[name]=dict(ram=address,rom_offset=offset,bytes=size,sha256=digest)
    return pieces,rows


def prepare(rom,snapshot=None,it_rom=None):
    parent,parts=R.prepare(rom,snapshot,it_rom)
    with Path(rom).open('rb')as stream:header=stream.read(512)
    extra,rows=extra_components(rom,header);parts.update(extra)
    if snapshot:
        actual=R.extract_snapshot(snapshot,{name:(a,n)for name,(a,n,_)in NEW.items()},4194304,R.SNAPSHOT_SHA)
        need(actual==extra,'FindPath natural RAM/current ROM components')
    if it_rom:
        with Path(it_rom).open('rb')as stream:it_header=stream.read(512)
        it_extra,_=extra_components(it_rom,it_header);need(it_extra==extra,'IT FindPath code/table identity')
    path=resolve_path(parts['fnt'],PATH)
    need(path['file_id']==129 and path['directory_ids']==[0,1,2,3]and len(path['table_reads'])==15,'exact selected FNT path/15calls')
    lengths=[x['bytes']for x in path['table_reads']]
    need((lengths.count(8),lengths.count(1),lengths.count(2))==(4,8,3),'exact FNT read lengths')
    need(path['directory_property']==dict(own_id=3,index=130,offset=487,parent=2),'exact final source directory metadata')
    return dict(schema='native-fs-cached-findpath-resources-v1',tool_sha256=sha(HERE.read_bytes()),
        parent_resource_receipt=parent,new_components=rows,path=PATH.decode('ascii'),path_metadata=path,
        total_component_bytes=sum(n for _,n,_ in COMPONENTS.values()),cpu_executed=False,compiler_invoked=False,
        limits=['Path metadata source oracle only; no native FindPath caller observed',
                'Logical table reads do not describe MI_CpuCopy8 adjacent halfword accesses',
                'IT is a byte comparison; no natural EN RAM/FAT state is transferred']),parts


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--it-rom',type=Path);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        source=HERE.parents[3]
        need(source!=a.json.resolve()and source not in a.json.resolve().parents,'private receipt outside source required')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh receipt output required')
        receipt,_=prepare(a.rom,a.snapshot,a.it_rom)
        with a.json.open('x')as out:out.write(json.dumps(receipt,indent=2)+'\n')
    except(ValueError,OSError,EOFError,UnicodeError)as error:p.exit(2,str(error)+'\n')
    print('Exact FindPath components and independent cached path metadata verified; no CPU/compiler')


if __name__=='__main__':main()
