#!/usr/bin/env python3
"""Freeze complete Convert input before oracle or CPU; no phase bridging."""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_cached_convert.py'),'convert_frozen_resources')
M=load(HERE.with_name('congela_fs_cached_seekdir.py'),'convert_sparse_memory')
R,need,sha=L.R,L.need,L.sha
ENTRY,RETURN,RESULT,FILE=0x020D8180,0x022F0180,0x022F0140,R.TOP-88
FRAME,GUARD=464,56


def make_input(parts,precompleted=False):
    need(type(precompleted)is bool and set(parts)==set(L.COMPONENTS)|{'arc','fat','fnt','root','path'},'typed exact Convert resources')
    spans={name:(a,n)for name,(a,n,_)in L.COMPONENTS.items()}
    spans.update(arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(L.ROOT,12),path=(L.PATH,8),
        result=(RESULT-16,40),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),gate=(RETURN,4))
    R.require_disjoint(spans);pages={}
    for address,size in spans.values():
        for base in range(address&~4095,(address+size+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
    for name,(address,size,digest)in L.COMPONENTS.items():
        need(type(parts[name])is bytes and len(parts[name])==size and sha(parts[name])==digest,'Convert code identity '+name)
        M.put(pages,address,parts[name])
    for name,address in(('arc',R.ARC),('fat',R.FAT),('fnt',R.FNT),('root',L.ROOT),('path',L.PATH)):M.put(pages,address,parts[name])
    arc=bytearray(parts['arc']);need(len(arc)==92 and R.u32(arc,28)==7 and arc[4:28]==b'\0'*24 and arc[32:40]==b'\0'*8,'quiescent registered archive7/emptyqueues/list')
    before=R.u32(arc,88);need(before in(0,0x602),'explicit natural or synthetic proc bits')
    after=before&~0x600;struct.pack_into('<I',arc,88,after);M.put(pages,R.ARC,arc)
    result=struct.pack('<II',R.ARC,140)if precompleted else b'\xa5'*8
    M.put(pages,RESULT-16,b'\xd3'*16+result+b'\xd3'*16)
    M.put(pages,RETURN,b'\0'*4) # Outer synthetic sentinel; Next749C remains authentic.
    regs=[RESULT,L.PATH]+[0xB0000000+i*0x010101 for i in range(2,13)]+[R.TOP,RETURN,0x6000001f]
    return dict(precompleted_result=precompleted,entry_pc=ENTRY,entry_regs=regs,
        archive_proc_projection=dict(address=R.ARC+88,bytes=4,before_hex=parts['arc'][88:92].hex(),after_hex=arc[88:92].hex()),
        pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(precompleted_result=f['precompleted_result'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 followed by CPSR; PC separate',archive_proc_projection=f['archive_proc_projection'],
        initial_map_sha256=M.map_digest(pages),pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        scratch_file72_hex=M.read(pages,FILE,72).hex(),archive92_hex=M.read(pages,R.ARC,92).hex(),
        root12_hex=M.read(pages,L.ROOT,12).hex(),path8_hex=M.read(pages,L.PATH,8).hex(),result8_hex=M.read(pages,RESULT,8).hex(),
        frame464_hex=M.read(pages,R.TOP-FRAME,FRAME).hex(),guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex())


def freeze(receipt,parts):
    paths=(HERE,Path(L.__file__),Path(L.L.__file__),Path(R.__file__),Path(M.__file__))
    return dict(schema='native-fs-cached-convert-input-v1',source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in paths},
        resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        resource_provenance=receipt['parent']['parent_resource_receipt']['resource_provenance'],root_provenance=receipt['root'],
        context_provenance='Synthetic CPU/stack/output/pages; exact resource slices; proc ACTIVATE/IDLE bits removed before entry; not natural card protocol',
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,
            scratch_file=FILE,path=L.PATH,result=RESULT,stack_top=R.TOP,frame_bytes=FRAME,guard_bytes=GUARD,stop_pc=RETURN),
        fixtures={'normal':input_record(make_input(parts)),'precompleted_result':input_record(make_input(parts,True))})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);a=p.parse_args()
    try:
        source=HERE.parents[3];need(source!=a.json.resolve()and source not in a.json.resolve().parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh frozen output required');receipt,parts=L.prepare(a.rom,a.snapshot)
        with a.json.open('x')as out:out.write(json.dumps(freeze(receipt,parts),indent=2)+'\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Two complete Convert inputs frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
