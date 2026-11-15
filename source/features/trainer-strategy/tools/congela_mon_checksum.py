#!/usr/bin/env python3
"""Freeze four owned checksum inputs before prediction or execution."""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_mon_checksum.py'),'checksum_frozen_code')
M=load(HERE.with_name('congela_fs_cached_seekdir.py'),'checksum_sparse_memory_helpers')
R,need,sha=L.R,L.need,L.sha
ENTRY,RETURN,BUF=0x20725e8,0x22f0180,0x22f0400
FRAME,GUARD=8,56
PROFILES={'Pattern128':(128,False),'Odd129':(129,False),'Overflow128':(128,True),'Zero0':(0,False)}


def make_input(parts,size=128,overflow=False):
    need(type(size)is int and type(overflow)is bool and(size,overflow)in PROFILES.values(),'typed finite checksum profile')
    pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(buffer=(BUF-16,161),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),stop=(RETURN,4))
    for name,(a,n,count,digest)in L.THUMB.items():
        b=parts[name];need(type(b)is bytes and len(b)==n and sha(b)==digest,'exact frozen checksum code')
        regions[name]=(a,n);put(a,b)
    R.require_disjoint(regions)
    storage=(b'\xff'*128 if overflow else bytes(range(128)))+b'\x5a'
    put(BUF-16,b'\xd3'*16+storage+b'\xd3'*16);put(R.TOP-FRAME-GUARD,b'\xa5'*(FRAME+GUARD));put(RETURN,bytes(4))
    regs=[BUF,size]+[0xb0000000+i*0x010101 for i in range(2,13)]+[R.TOP,RETURN|1,0x6000003f]
    return dict(input_size=size,overflow_input=overflow,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(input_size=f['input_size'],overflow_input=f['overflow_input'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],register_format='R0..R14 then CPSR; PC separate',
        data_provenance='Owned storage129: pattern128 or FF128, followed by5A; opaque bytes, not BoxMon/save data',
        storage129_sha256=sha(M.read(pages,BUF,129)),initial_map_sha256=M.map_digest(pages),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        frame8_hex=M.read(pages,R.TOP-8,8).hex(),guard56_hex=M.read(pages,R.TOP-64,56).hex(),
        buffer_guard16_before=M.read(pages,BUF-16,16).hex(),buffer_guard16_after=M.read(pages,BUF+129,16).hex(),trailing_byte_hex=M.read(pages,BUF+128,1).hex())


def freeze(receipt,parts):
    return dict(schema='native-mon-checksum-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(M.__file__))},
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,predictor_cap=1024,stack_top=R.TOP,frame_bytes=8,guard_bytes=56,buffer=BUF,storage_bytes=129,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,size,overflow))for name,(size,overflow)in PROFILES.items()})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private checksum input')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Four owned checksum fixtures frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
