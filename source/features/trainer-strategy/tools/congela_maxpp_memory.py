#!/usr/bin/env python3
"""Freeze four MaxPP argument/data profiles before source prediction or CPU.

Reuses the uninitialized PP stack/pages, adds original MaxPP/DIV code, and
declares the larger stack owner. Native prologues compute all child buffers.
"""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_maxpp_memory.py'),'MaxPP_frozen_resources')
P=load(HERE.with_name('congela_pp_memory.py'),'MaxPP_uninitialized_PP_pages')
R,M,need,sha=L.R,P.M,L.need,L.sha
SDK,NARC=P.P.P,P.L.L
ENTRY,RETURN=L.MAXPP[0],P.RETURN
FRAME,GUARD=656,56
DEST,FILE,LOCAL=R.TOP-40,R.TOP-152,R.TOP-176
ROOT,PATH=P.ROOT,P.PATH
PROFILES={'Up3':(3,15),'Up0':(0,15),'Up4':(4,15),'PP1Up3':(3,1)}


def make_input(parts,ups=3,pp=15):
    need(type(ups)is int and type(pp)is int and(ups,pp)in PROFILES.values(),'typed finite MaxPP argument/data profiles')
    need(type(parts)is dict and 'maxpp'in parts and 'signed_div'in parts,'complete MaxPP new code parts')
    f=P.make_input({name:b for name,b in parts.items()if name not in('maxpp','signed_div')},pp)
    pages={a:bytearray(b)for a,b in f['pages'].items()}
    for name,item in(('maxpp',L.MAXPP),('signed_div',L.DIV)):
        a,n,digest=item[0],item[1],item[-1]
        need(len(parts[name])==n and sha(parts[name])==digest,'exact MaxPP frozen code '+name)
        for base in range(a&~4095,(a+n+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,parts[name])
    # All newly owned stack bytes were already untouched page-fill; never
    # rewrite a result or manufacture a FILE property as a phase input.
    need(M.read(pages,R.TOP-FRAME-GUARD,FRAME+GUARD)==b'\xa5'*(FRAME+GUARD),'MaxPP larger uninitialized stack/guard')
    R.require_disjoint(dict(stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),maxpp=L.MAXPP[:2],division=L.DIV[:2],
        fat=(R.FAT,4104),fnt=(R.FNT,2902),arc=(R.ARC,92),root=(ROOT,12)))
    regs=[310,ups]+[0xb0000000+i*0x010101 for i in range(2,13)]+[R.TOP,RETURN|1,0x6000003f]
    f.update(input_Up=ups,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})
    return f


def input_record(f):
    pages=f['pages']
    return dict(input_Up=f['input_Up'],input_PP=f['input_PP'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 followed by CPSR; PC separate',archive_projections=f['archive_projections'],payload_projections=f['payload_projections'],
        original_member_sha256=SDK.MEMBER_SHA,projected_member16_hex=M.read(pages,SDK.MEMBER_SOURCE,16).hex(),
        projected_member_sha256=sha(M.read(pages,SDK.MEMBER_SOURCE,16)),initial_map_sha256=M.map_digest(pages),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        archive92_hex=M.read(pages,R.ARC,92).hex(),root12_hex=M.read(pages,ROOT,12).hex(),
        frame656_hex=M.read(pages,R.TOP-FRAME,FRAME).hex(),guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex(),
        payload_windows=[dict(ram=SDK.ARCHIVE_BASE+0x1093800+a,hex=M.read(pages,SDK.ARCHIVE_BASE+0x1093800+a,n).hex())for a,n in NARC.WINDOWS])


def freeze(receipt,parts):
    paths=(HERE,Path(L.__file__),Path(P.__file__))
    return dict(schema='native-MaxPP-memory-input-v1',source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in paths},
        resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        context_provenance='Original MaxPP/PP/NARC/SDK/DIV with synthetic API entry/stack and explicit ROM-derived memory archive; PP1 separately projected before entry',
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,stack_top=R.TOP,
            frame_bytes=FRAME,guard_bytes=GUARD,native_buffer=DEST,client_file=FILE,stop_pc=RETURN,load_TBIT_enabled=True),
        fixtures={name:input_record(make_input(parts,ups,pp))for name,(ups,pp)in PROFILES.items()})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents,'private frozen MaxPP output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh MaxPP frozen output')
        receipt,parts=L.prepare(a.rom)
        with a.json.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Four complete MaxPP argument/data inputs frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
