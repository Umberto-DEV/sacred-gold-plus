#!/usr/bin/env python3
"""Freeze the original PP getter's stack and separately identified data input.

The owned ROM receipt remains unchanged. A PP1 counterfactual projects one
source-memory byte before entry; no register or runtime output is replaced.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_pp_memory.py'),'PP_frozen_resources')
P=load(HERE.with_name('congela_fs_memory_narc.py'),'PP_parent_frozen')
R,M,need,sha=L.R,P.M,L.need,L.sha
ENTRY,RETURN,DEST=0x2073314,P.RETURN,R.TOP-24
FRAME,GUARD=640,56
FILE,LOCAL=R.TOP-136,R.TOP-160
ROOT,PATH=P.ROOT,P.PATH


def make_input(parts,pp=15):
    need(type(pp)is int and pp in(15,1),'typed PP15/PP1 input domain')
    expected=set(P.P.COMPONENTS)|{'arc','fat','fnt','root','path','narc_header','narc_member'}|set(L.L.THUMB)|set(L.L.DATA)|{'payload_'+hex(a)for a,n in L.L.WINDOWS}|set(L.THUMB)|set(L.DATA)
    need(type(parts)is dict and set(parts)==expected,'exact PP input components')
    spans={name:(a,n)for name,(a,n,digest)in P.P.COMPONENTS.items()}
    spans.update({name:item[:2]for name,item in{**L.L.THUMB,**L.L.DATA,**L.THUMB,**L.DATA}.items()})
    spans.update(arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(ROOT,12),
        stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),gate=(RETURN,4))
    spans.update({'payload_'+hex(a):(P.P.ARCHIVE_BASE+0x1093800+a,n)for a,n in L.L.WINDOWS})
    R.require_disjoint(spans);pages={}
    for a,n in spans.values():
        for base in range(a&~4095,(a+n+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
    for name,(a,n,digest)in P.P.COMPONENTS.items():
        need(len(parts[name])==n and sha(parts[name])==digest,'exact PP native SDK '+name);M.put(pages,a,parts[name])
    for name,item in{**L.L.THUMB,**L.L.DATA,**L.THUMB,**L.DATA}.items():
        a,n,digest=item[0],item[1],item[-1]
        need(len(parts[name])==n and sha(parts[name])==digest,'exact PP native code/data '+name);M.put(pages,a,parts[name])
    for name,a in(('arc',R.ARC),('fat',R.FAT),('fnt',R.FNT),('root',ROOT)):M.put(pages,a,parts[name])
    arc=bytearray(parts['arc'])
    need(len(arc)==92 and R.u32(arc,28)==7 and R.u32(arc,40)==0 and arc[4:28]==b'\0'*24 and arc[32:40]==b'\0'*8,'quiescent PP source archive')
    need(R.u32(arc,88)in(0,0x602)and R.u32(arc,72)in(0,0x20d84c4),'source PP callback/procedure domain')
    archive_projections=[]
    for off,value in((40,P.P.ARCHIVE_BASE),(72,0x20d7448),(88,R.u32(arc,88)&~0x600)):
        before=arc[off:off+4].hex();struct.pack_into('<I',arc,off,value)
        archive_projections.append(dict(address=R.ARC+off,bytes=4,before_hex=before,after_hex=arc[off:off+4].hex()))
    M.put(pages,R.ARC,arc)
    for a,n in L.L.WINDOWS:M.put(pages,P.P.ARCHIVE_BASE+0x1093800+a,parts['payload_'+hex(a)])
    member=parts['narc_member'];need(sha(member)==P.P.MEMBER_SHA and member[6]==15,'original owned member/PP identity')
    projections=[]
    if pp==1:
        address=P.P.MEMBER_SOURCE+6;M.put(pages,address,b'\x01')
        projections.append(dict(address=address,bytes=1,before_hex='0f',after_hex='01',reason='Declared input memory counterfactual; original owned ROM unchanged'))
    M.put(pages,RETURN,b'\0'*4)
    regs=[310,5]+[0xb0000000+i*0x010101 for i in range(2,13)]+[R.TOP,RETURN|1,0x6000003f]
    return dict(input_PP=pp,entry_pc=ENTRY,entry_regs=regs,archive_projections=archive_projections,payload_projections=projections,pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(input_PP=f['input_PP'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 followed by CPSR; PC separate',archive_projections=f['archive_projections'],payload_projections=f['payload_projections'],
        original_member_sha256=P.P.MEMBER_SHA,projected_member16_hex=M.read(pages,P.P.MEMBER_SOURCE,16).hex(),
        projected_member_sha256=sha(M.read(pages,P.P.MEMBER_SOURCE,16)),initial_map_sha256=M.map_digest(pages),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        archive92_hex=M.read(pages,R.ARC,92).hex(),root12_hex=M.read(pages,ROOT,12).hex(),
        frame640_hex=M.read(pages,R.TOP-FRAME,FRAME).hex(),guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex(),
        payload_windows=[dict(ram=P.P.ARCHIVE_BASE+0x1093800+a,hex=M.read(pages,P.P.ARCHIVE_BASE+0x1093800+a,n).hex())for a,n in L.L.WINDOWS])


def freeze(receipt,parts):
    paths=(HERE,Path(L.__file__),Path(L.L.__file__),Path(P.__file__),Path(M.__file__))
    return dict(schema='native-PP-memory-input-v1',source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in paths},
        resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        context_provenance='Native getter/NARC/SDK with synthetic entry/stack and explicit memory archive; PP1 is a separately declared input-memory projection',
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,stack_top=R.TOP,
            frame_bytes=FRAME,guard_bytes=GUARD,client_file=FILE,native_buffer=DEST,stop_pc=RETURN,load_TBIT_enabled=True),
        fixtures={'normal':input_record(make_input(parts)),'PP1':input_record(make_input(parts,1))})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh frozen PP output')
        receipt,parts=L.prepare(a.rom,a.snapshot)
        with a.json.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('PP15/PP1 source memory frozen with native stack buffers; no oracle/CPU/compiler')


if __name__=='__main__':main()
