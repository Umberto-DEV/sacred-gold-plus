#!/usr/bin/env python3
"""Freeze native NARC caller inputs before arithmetic prediction or CPU.

Only the final destination has a precompleted counterfactual. FILE and parser
locals start untouched; native Thumb/SDK instructions initialize them.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_memory_narc.py'),'native_narc_frozen_resources')
M=load(HERE.with_name('congela_fs_cached_seekdir.py'),'native_narc_sparse_memory')
P,R,need,sha=L.L,L.R,L.need,L.sha
ENTRY,RETURN,DEST=0x2007508,0x22f0180,0x22f0240
FRAME,GUARD=616,56
FILE,LOCAL=R.TOP-112,R.TOP-136
ROOT,PATH=P.L.L.ROOT,L.DATA['narc_path'][0]


def make_input(parts,precompleted=False):
    need(type(precompleted)is bool,'typed native NARC destination projection')
    expected=set(P.COMPONENTS)|{'arc','fat','fnt','root','path','narc_header','narc_member'}|set(L.THUMB)|set(L.DATA)|{'payload_'+hex(a)for a,n in L.WINDOWS}
    need(type(parts)is dict and set(parts)==expected,'exact native NARC parts')
    spans={name:(a,n)for name,(a,n,_)in P.COMPONENTS.items()}
    spans.update({name:item[:2]for name,item in {**L.THUMB,**L.DATA}.items()})
    spans.update(arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(ROOT,12),
        destination=(DEST-16,48),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),gate=(RETURN,4))
    spans.update({'payload_'+hex(a):(P.ARCHIVE_BASE+0x1093800+a,n)for a,n in L.WINDOWS})
    R.require_disjoint(spans);pages={}
    for a,n in spans.values():
        for base in range(a&~4095,(a+n+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
    for name,(a,n,digest)in P.COMPONENTS.items():
        need(len(parts[name])==n and sha(parts[name])==digest,'native SDK component '+name);M.put(pages,a,parts[name])
    for name,item in {**L.THUMB,**L.DATA}.items():
        a,n,digest=item[0],item[1],item[-1]
        need(len(parts[name])==n and sha(parts[name])==digest,'native caller component '+name);M.put(pages,a,parts[name])
    for name,a in(('arc',R.ARC),('fat',R.FAT),('fnt',R.FNT),('root',ROOT)):M.put(pages,a,parts[name])
    arc=bytearray(parts['arc'])
    need(len(arc)==92 and R.u32(arc,28)==7 and R.u32(arc,40)==0 and arc[4:28]==b'\0'*24 and arc[32:40]==b'\0'*8,'quiescent source archive')
    need(R.u32(arc,88)in(0,0x602)and R.u32(arc,72)in(0,0x20d84c4),'source callback/procedure domain')
    projections=[]
    for off,value in((40,P.ARCHIVE_BASE),(72,0x20d7448),(88,R.u32(arc,88)&~0x600)):
        before=arc[off:off+4].hex();struct.pack_into('<I',arc,off,value)
        projections.append(dict(address=R.ARC+off,bytes=4,before_hex=before,after_hex=arc[off:off+4].hex()))
    M.put(pages,R.ARC,arc)
    for relative,n in L.WINDOWS:M.put(pages,P.ARCHIVE_BASE+0x1093800+relative,parts['payload_'+hex(relative)])
    member=parts['narc_member'];need(sha(member)==P.MEMBER_SHA,'exact counterfactual destination member')
    M.put(pages,DEST-16,b'\xd3'*16+(member if precompleted else b'\xa5'*16)+b'\xd3'*16)
    M.put(pages,RETURN,b'\0'*4)
    regs=[DEST,11,310,0x33333303]+[0xb0000000+i*0x010101 for i in range(4,13)]+[R.TOP,RETURN|1,0x6000003f]
    return dict(precompleted_destination=precompleted,entry_pc=ENTRY,entry_regs=regs,archive_projections=projections,pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(precompleted_destination=f['precompleted_destination'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 followed by CPSR; PC separate',archive_projections=f['archive_projections'],
        initial_map_sha256=M.map_digest(pages),pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        archive92_hex=M.read(pages,R.ARC,92).hex(),root12_hex=M.read(pages,ROOT,12).hex(),
        file72_hex=M.read(pages,FILE,72).hex(),frame616_hex=M.read(pages,R.TOP-FRAME,FRAME).hex(),
        guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex(),destination16_hex=M.read(pages,DEST,16).hex(),
        payload_windows=[dict(ram=P.ARCHIVE_BASE+0x1093800+a,hex=M.read(pages,P.ARCHIVE_BASE+0x1093800+a,n).hex())for a,n in L.WINDOWS])


def freeze(receipt,parts):
    paths=(HERE,Path(L.__file__),Path(P.__file__),Path(M.__file__))
    return dict(schema='native-fs-memory-narc-input-v1',source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in paths},
        resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        context_provenance='Native exact ROM caller/code/data with synthetic CPU/stack/destination and explicit memory-archive projections; no natural CARD or CP15 observation',
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,client_file=FILE,
            destination=DEST,stack_top=R.TOP,frame_bytes=FRAME,guard_bytes=GUARD,stop_pc=RETURN,load_TBIT_enabled=True),
        fixtures={'normal':input_record(make_input(parts)),'precompleted_destination':input_record(make_input(parts,True))})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(source!=out and source not in out.parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh frozen output')
        receipt,parts=L.prepare(a.rom,a.snapshot)
        with a.json.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Native NARC normal and precompleted inputs frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
