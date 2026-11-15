#!/usr/bin/env python3
"""Freeze full Open inputs and two causal projections before oracle/CPU."""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_cached_open.py'),'open_frozen_resources')
M=load(HERE.with_name('congela_fs_cached_seekdir.py'),'open_sparse_memory')
R,need,sha=L.R,L.need,L.sha
ENTRY,RETURN,FILE=0x020D8278,0x022F0180,R.FILE
FRAME,GUARD=480,56
PROFILES=('normal','precompleted_prop','fat_size_equal')


def make_input(parts,profile='normal'):
    need(type(profile)is str and profile in PROFILES and set(parts)==set(L.COMPONENTS)|{'arc','fat','fnt','root','path'},'exact typed Open resources/profile')
    spans={name:(a,n)for name,(a,n,_)in L.COMPONENTS.items()}
    spans.update(arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(L.L.ROOT,12),path=(L.L.PATH,8),
        client=(FILE-16,104),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),gate=(RETURN,4))
    R.require_disjoint(spans);pages={}
    for address,size in spans.values():
        for base in range(address&~4095,(address+size+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
    for name,(a,n,digest)in L.COMPONENTS.items():
        need(type(parts[name])is bytes and len(parts[name])==n and sha(parts[name])==digest,'Open code identity '+name);M.put(pages,a,parts[name])
    for name,a in(('arc',R.ARC),('fat',R.FAT),('fnt',R.FNT),('root',L.L.ROOT),('path',L.L.PATH)):M.put(pages,a,parts[name])
    arc=bytearray(parts['arc']);need(len(arc)==92 and R.u32(arc,28)==7 and arc[4:28]==b'\0'*24 and arc[32:40]==b'\0'*8,'quiescent ARC7/empty lists/queues')
    before=R.u32(arc,88);need(before in(0,0x602),'natural or synthetic archive procedure mask')
    struct.pack_into('<I',arc,88,before&~0x600)
    if profile=='fat_size_equal':struct.pack_into('<I',arc,48,140*8)
    M.put(pages,R.ARC,arc)
    client=bytearray(b'\xa5'*72)
    for off in(0,4,8,12,24,28):struct.pack_into('<I',client,off,0)
    struct.pack_into('<I',client,16,14) # Explicit source-initialized precondition, not a captured Init.
    if profile=='precompleted_prop':client[32:48]=struct.pack('<4I',140,0x1093800,0x109645c,0x1093800)
    M.put(pages,FILE-16,b'\xd3'*16+client+b'\xd3'*16);M.put(pages,RETURN,b'\0'*4)
    regs=[FILE,L.L.PATH]+[0xB0000000+i*0x010101 for i in range(2,13)]+[R.TOP,RETURN,0x6000001f]
    return dict(profile=profile,entry_pc=ENTRY,entry_regs=regs,
        archive_proc_projection=dict(address=R.ARC+88,bytes=4,before_hex=parts['arc'][88:92].hex(),after_hex=arc[88:92].hex()),
        archive_fat_size_projection=dict(address=R.ARC+48,bytes=4,before_hex=parts['arc'][48:52].hex(),after_hex=arc[48:52].hex()),
        pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(profile=f['profile'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],register_format='R0..R14 followed by CPSR; PC separate',
        archive_proc_projection=f['archive_proc_projection'],archive_fat_size_projection=f['archive_fat_size_projection'],
        initial_map_sha256=M.map_digest(pages),pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        client_file72_hex=M.read(pages,FILE,72).hex(),archive92_hex=M.read(pages,R.ARC,92).hex(),
        root12_hex=M.read(pages,L.L.ROOT,12).hex(),path8_hex=M.read(pages,L.L.PATH,8).hex(),
        frame480_hex=M.read(pages,R.TOP-FRAME,FRAME).hex(),guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex())


def freeze(receipt,parts):
    paths=(HERE,Path(L.__file__),Path(L.L.__file__),Path(L.L.L.__file__),Path(R.__file__),Path(M.__file__))
    return dict(schema='native-fs-cached-open-input-v1',source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in paths},
        resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        resource_provenance=receipt['parent']['parent']['parent_resource_receipt']['resource_provenance'],root_provenance=receipt['parent']['root'],
        context_provenance='Synthetic CPU/stack/pages and source-initialized client; exact resources; initial proc and optional FAT-size projections; not natural card protocol',
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,
            client_file=FILE,stack_top=R.TOP,frame_bytes=FRAME,guard_bytes=GUARD,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,name))for name in PROFILES})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);a=p.parse_args()
    try:
        source=HERE.parents[3];need(source!=a.json.resolve()and source not in a.json.resolve().parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh frozen output required');receipt,parts=L.prepare(a.rom,a.snapshot)
        with a.json.open('x')as out:out.write(json.dumps(freeze(receipt,parts),indent=2)+'\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Three complete Open inputs frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
