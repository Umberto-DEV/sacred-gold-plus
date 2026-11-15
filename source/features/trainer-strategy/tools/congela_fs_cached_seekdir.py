#!/usr/bin/env python3
"""Freeze explicit isolated SeekDir inputs before the source oracle or CPU.

No execution outcome is captured by this contract. precompleted_prop is a
separate initial input projection, never an actual natural-caller claim.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


R=load(Path(__file__).with_name('rileggi_fs_cached_resources.py'),'cached_freeze_resources')
need,sha=R.need,R.sha
ENTRY,RETURN=0x020D6BEC,0x020D749C


def wire(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)


def map_digest(pages):
    import hashlib
    h=hashlib.sha256()
    for address,blob in sorted(pages.items()):
        h.update(struct.pack('<II',address,len(blob)));h.update(blob)
    return h.hexdigest()


def read(pages,address,size):
    need(type(size)is int and size>0,'read size')
    output=bytearray()
    while size:
        base=address&~4095;offset=address-base;n=min(size,4096-offset)
        need(base in pages,'unmapped fixture address')
        output.extend(pages[base][offset:offset+n]);address+=n;size-=n
    return bytes(output)


def put(pages,address,blob):
    while blob:
        base=address&~4095;offset=address-base;n=min(len(blob),4096-offset)
        need(base in pages,'unmapped fixture write')
        pages[base][offset:offset+n]=blob[:n];blob=blob[n:];address+=n


def make_input(parts,own_id=0,precompleted=False):
    need(type(own_id)is int and own_id in(0,1) and type(precompleted)is bool,'typed finite fixture input')
    need(set(parts)==set(R.COMPONENTS)|{'arc','fat','fnt'},'exact resource set')
    spans={name:(a,n)for name,(a,n,_)in R.COMPONENTS.items()}
    spans.update(arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),
                 file=(R.FILE-16,104),stack=(R.TOP-128,128),gate=(RETURN,4))
    R.require_disjoint(spans)
    pages={}
    for address,size in spans.values():
        for base in range(address&~4095,(address+size+4095)&~4095,4096):
            pages.setdefault(base,bytearray(b'\xa5'*4096))
    for name,(a,n,expected)in R.COMPONENTS.items():
        need(len(parts[name])==n and sha(parts[name])==expected,'fixture code identity '+name)
        put(pages,a,parts[name])
    for name,address in(('arc',R.ARC),('fat',R.FAT),('fnt',R.FNT)):put(pages,address,parts[name])
    # The synthetic return sentinel is stopped by the code hook before execution.
    put(pages,RETURN,b'\x00\x00\x00\x00')
    file=bytearray(72)
    for offset,value in((8,R.ARC),(12,45),(16,4),(20,2),(48,R.ARC)):
        struct.pack_into('<I',file,offset,value)
    struct.pack_into('<H',file,52,own_id);file[32:48]=b'\xa5'*16
    if precompleted:
        start,index,parent=struct.unpack_from('<IHH',parts['fnt'],own_id*8)
        file[32:48]=struct.pack('<IHHII',R.ARC,own_id,index,R.FNT+start,parent&0xfff)
    put(pages,R.FILE-16,b'\xd3'*16+file+b'\xd3'*16)
    regs=[R.FILE]+[0xB0000000+i*0x010101 for i in range(1,13)]+[R.TOP,RETURN,0x6000001f]
    return dict(own_id=own_id,precompleted_prop=precompleted,entry_pc=ENTRY,entry_regs=regs,
                pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(own_id=f['own_id'],precompleted_prop=f['precompleted_prop'],
        entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 followed by CPSR; PC is separate',
        initial_map_sha256=map_digest(pages),page_bytes=4096,
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        file72_hex=read(pages,R.FILE,72).hex(),archive92_hex=read(pages,R.ARC,92).hex(),
        frame72_hex=read(pages,R.TOP-72,72).hex(),guard56_hex=read(pages,R.TOP-128,56).hex())


def freeze(receipt,parts):
    fixtures={'root':make_input(parts),'root_precompleted':make_input(parts,precompleted=True),
              'directory1':make_input(parts,own_id=1)}
    return dict(schema='native-fs-cached-seekdir-input-v1',
        source_identities={Path(__file__).name:sha(Path(__file__).read_bytes()),Path(R.__file__).name:sha(Path(R.__file__).read_bytes())},
        resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        resource_provenance=receipt['resource_provenance'],
        context_provenance='Entirely synthetic CPU/FSFile/stack/pages except authenticated resource slices; not a natural caller',
        policy=dict(models=0,runtime_host_writes=0,native_instruction_cap=256,timeout_us=1000000,
                    file=R.FILE,stack_top=R.TOP,frame_bytes=72,guard_bytes=56,stop_pc=RETURN),
        fixtures={name:input_record(f)for name,f in fixtures.items()})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        source=Path(__file__).resolve().parents[3]
        need(a.json.resolve()!=source and source not in a.json.resolve().parents,'private frozen output must be outside source')
        need(not a.json.exists() and not a.json.is_symlink(),'fresh frozen input output required')
        receipt,parts=R.prepare(a.rom,a.snapshot)
        with a.json.open('x')as out:out.write(json.dumps(freeze(receipt,parts),indent=2)+'\n')
    except(ValueError,OSError,EOFError)as error:p.exit(2,str(error)+'\n')
    print('Three explicit isolated inputs frozen, no oracle/compiler/CPU')


if __name__=='__main__':main()
