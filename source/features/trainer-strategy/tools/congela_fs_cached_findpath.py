#!/usr/bin/env python3
"""Freeze isolated complete FindPath inputs before oracle/compiler/CPU."""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_cached_findpath.py'),'cached_find_frozen_resources')
F=load(HERE.with_name('congela_fs_cached_seekdir.py'),'cached_find_qualified_memory')
R,need,sha=L.R,L.need,L.sha
ENTRY,RETURN,PATH,RESULT=0x020D6DB0,0x020D6F94,0x022F0100,0x022F0140


def make_input(parts,precompleted=False):
    need(type(precompleted)is bool and set(parts)==set(L.COMPONENTS)|{'arc','fat','fnt'},'exact typed FindPath resources/input')
    spans={name:(a,n)for name,(a,n,_)in L.COMPONENTS.items()}
    spans.update(arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),
        file=(R.FILE-16,104),path=(PATH-16,40),result=(RESULT-16,40),stack=(R.TOP-336,336),gate=(RETURN,4))
    R.require_disjoint(spans);pages={}
    for address,size in spans.values():
        for base in range(address&~4095,(address+size+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
    for name,(address,size,digest)in L.COMPONENTS.items():
        need(type(parts[name])is bytes and len(parts[name])==size and sha(parts[name])==digest,'FindPath code/data identity '+name)
        F.put(pages,address,parts[name])
    for name,address in(('arc',R.ARC),('fat',R.FAT),('fnt',R.FNT)):F.put(pages,address,parts[name])
    arc=bytearray(parts['arc']);need(len(arc)==92 and R.u32(arc,28)==7,'original cached archive input')
    need(R.u32(arc,88)&(4|8)==0,'no routed proc callback for commands2/3')
    struct.pack_into('<I',arc,28,0x17);F.put(pages,R.ARC,arc)
    file=bytearray(72)
    for offset,value in((8,R.ARC),(12,0x45),(16,4),(20,2),(48,R.ARC),(60,PATH),(68,RESULT)):
        struct.pack_into('<I',file,offset,value)
    file[32:48]=b'\xa5'*16
    F.put(pages,R.FILE-16,b'\xd3'*16+file+b'\xd3'*16)
    F.put(pages,PATH-16,b'\xd3'*16+L.PATH+b'\0'+b'\xd3'*16)
    result=struct.pack('<II',R.ARC,L.resolve_path(parts['fnt'],L.PATH)['file_id'])if precompleted else b'\xa5'*8
    F.put(pages,RESULT-16,b'\xd3'*16+result+b'\xd3'*16)
    F.put(pages,RETURN,b'\0'*4) # Synthetic stop sentinel, never executed.
    regs=[R.FILE]+[0xB0000000+i*0x010101 for i in range(1,13)]+[R.TOP,RETURN,0x6000001f]
    return dict(precompleted_result=precompleted,entry_pc=ENTRY,entry_regs=regs,
        archive_flag_projection=dict(address=R.ARC+28,bytes=4,before_hex=parts['arc'][28:32].hex(),after_hex=arc[28:32].hex()),
        pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(precompleted_result=f['precompleted_result'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 followed by CPSR; PC separate',archive_flag_projection=f['archive_flag_projection'],
        initial_map_sha256=F.map_digest(pages),pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        file72_hex=F.read(pages,R.FILE,72).hex(),archive92_hex=F.read(pages,R.ARC,92).hex(),
        path8_hex=F.read(pages,PATH,8).hex(),result8_hex=F.read(pages,RESULT,8).hex(),
        frame280_hex=F.read(pages,R.TOP-280,280).hex(),guard56_hex=F.read(pages,R.TOP-336,56).hex())


def freeze(receipt,parts):
    return dict(schema='native-fs-cached-findpath-input-v1',
        source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(R.__file__),Path(F.__file__))},
        resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        resource_provenance=receipt['parent_resource_receipt']['resource_provenance'],
        context_provenance='Synthetic CPU/File/path/result/stack/pages; authentic resources where declared; archive flag7 to17 is an initial projection',
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,
            file=R.FILE,path=PATH,result=RESULT,stack_top=R.TOP,frame_bytes=280,guard_bytes=56,stop_pc=RETURN),
        fixtures={'normal':input_record(make_input(parts)),'precompleted_result':input_record(make_input(parts,True))})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        source=HERE.parents[3]
        need(a.json.resolve()!=source and source not in a.json.resolve().parents,'private frozen output outside source required')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh frozen output required')
        receipt,parts=L.prepare(a.rom,a.snapshot)
        with a.json.open('x')as out:out.write(json.dumps(freeze(receipt,parts),indent=2)+'\n')
    except(ValueError,OSError,EOFError,UnicodeError)as error:p.exit(2,str(error)+'\n')
    print('Two complete isolated FindPath inputs frozen; no oracle/compiler/CPU')


if __name__=='__main__':main()
