#!/usr/bin/env python3
"""Freeze 129 distinct GetSubstruct contexts and a 130-call matrix, no oracle."""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_mon_substruct.py'),'substruct_frozen_code')
M=load(HERE.with_name('congela_fs_cached_seekdir.py'),'substruct_sparse_memory_helpers')
R,need,sha=L.R,L.need,L.sha
ENTRY,RETURN,BOX=0x2072608,0x22f0180,0x22f0400
FRAME,GUARD=16,56
PROFILES={f'R{row:02d}W{which}':(row<<13,which)for row in range(32)for which in range(4)}
PROFILES['IgnoredPID_R03W1']=(0x80006001,1)
MATRIX=tuple((name,name,True)for name in PROFILES)+(('R03W1_OFF','R03W1',False),)


def make_input(parts,pid=0,which=0):
    need(type(pid)is int and type(which)is int and(pid,which)in PROFILES.values(),'typed finite GetSubstruct PID/which profile')
    need(type(parts)is dict and set(parts)==set(L.THUMB)|set(L.DATA),'exact GetSubstruct code/data parts')
    pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(box=(BOX-16,168),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),stop=(RETURN,4))
    for name,item in {**L.THUMB,**L.DATA}.items():
        a,n,digest=item[0],item[1],item[-1];b=parts[name]
        need(type(b)is bytes and len(b)==n and sha(b)==digest,'exact frozen GetSubstruct '+name)
        regions[name]=(a,n);put(a,b)
    R.require_disjoint(regions)
    put(BOX-16,b'\xd3'*16+b'\xa5'*136+b'\xd3'*16);put(R.TOP-FRAME-GUARD,b'\xa5'*(FRAME+GUARD));put(RETURN,bytes(4))
    regs=[BOX,pid,which]+[0xb0000000+i*0x010101 for i in range(3,13)]+[R.TOP,RETURN|1,0x6000003f]
    return dict(input_PID=pid,input_which=which,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(input_PID=f['input_PID'],input_which=f['input_which'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],register_format='R0..R14 then CPSR; PC separate',
        data_provenance='Owned opaque136B A5 storage; API PID is separate from unexamined Box header, not a validated Pokemon',
        storage136_sha256=sha(M.read(pages,BOX,136)),initial_map_sha256=M.map_digest(pages),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        frame16_hex=M.read(pages,R.TOP-16,16).hex(),guard56_hex=M.read(pages,R.TOP-72,56).hex(),
        box_guard16_before=M.read(pages,BOX-16,16).hex(),box_guard16_after=M.read(pages,BOX+136,16).hex())


def freeze(receipt,parts):
    need(len(PROFILES)==129 and len(MATRIX)==130,'finite GetSubstruct domain cardinality')
    return dict(schema='native-mon-substructure-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(M.__file__))},
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,predictor_cap=64,stack_top=R.TOP,frame_bytes=16,guard_bytes=56,box=BOX,storage_bytes=136,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,pid,which))for name,(pid,which)in PROFILES.items()},
        matrix=[dict(name=name,input_profile=key,observed=observe)for name,key,observe in MATRIX])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private GetSubstruct input')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('129 distinct GetSubstruct inputs/130-call plan frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
