#!/usr/bin/env python3
"""Freeze two owned cipher inputs, without predicting or executing the cipher."""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_mon_cipher.py'),'cipher_frozen_code')
M=load(HERE.with_name('congela_fs_cached_seekdir.py'),'cipher_sparse_memory_helpers')
R,need,sha=L.R,L.need,L.sha
ENTRY,RETURN=0x20725d8,0x22f0180
BUF,GLOBAL=0x22f0400,0x21d15a8
FRAME,GUARD=40,56
PROFILES={'SeedFC0':0xfc0,'SeedFC1':0xfc1}


def make_input(parts,seed=0xfc0):
    need(type(seed)is int and seed in PROFILES.values(),'typed finite cipher seed')
    pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(buffer=(BUF-16,160),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),stop=(RETURN,4),global_sentinel=(GLOBAL,4))
    for name,item in {**L.THUMB,**L.DATA}.items():
        a,n,digest=item[0],item[1],item[-1];b=parts[name]
        need(type(b)is bytes and len(b)==n and sha(b)==digest,'exact frozen cipher '+name);regions[name]=(a,n);put(a,b)
    R.require_disjoint(regions)
    put(BUF-16,b'\xd3'*16+bytes(range(128))+b'\xd3'*16)
    put(R.TOP-FRAME-GUARD,b'\xa5'*(FRAME+GUARD));put(RETURN,bytes(4));put(GLOBAL,struct.pack('<I',0xdec0adde))
    regs=[BUF,128,seed]+[0xb0000000+i*0x010101 for i in range(3,13)]+[R.TOP,RETURN|1,0x6000003f]
    return dict(input_seed=seed,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages']
    return dict(input_seed=f['input_seed'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],register_format='R0..R14 then CPSR; PC separate',
        data_provenance='Owned bytes(range(128)); arbitrary API seed, not a validated BoxMon or native checksum',
        plaintext_sha256=sha(M.read(pages,BUF,128)),initial_map_sha256=M.map_digest(pages),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        frame40_hex=M.read(pages,R.TOP-FRAME,FRAME).hex(),guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex(),
        buffer_guard16_before=M.read(pages,BUF-16,16).hex(),buffer_guard16_after=M.read(pages,BUF+128,16).hex(),
        global_sentinel_hex=M.read(pages,GLOBAL,4).hex())


def freeze(receipt,parts):
    return dict(schema='native-mon-cipher-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(M.__file__))},
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,stack_top=R.TOP,frame_bytes=FRAME,guard_bytes=GUARD,buffer=BUF,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,seed))for name,seed in PROFILES.items()})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private cipher input')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Two owned pattern/seed cipher fixtures frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
