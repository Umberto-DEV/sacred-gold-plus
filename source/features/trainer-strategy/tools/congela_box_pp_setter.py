#!/usr/bin/env python3
"""Freeze a shared owned encrypted Box and two Value bytes, no oracle or CPU."""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_box_pp_setter.py'),'setter_frozen_reader')
G=load(HERE.with_name('congela_box_ppup.py'),'setter_retained_owned_Box')
R,M,need,sha=L.R,G.M,L.need,L.sha
ENTRY,RETURN,BOX,VALUE=0x206ed70,0x22f0180,0x22f0000,0x22f0200
FRAME,GUARD=136,56
PROFILES={'PP24':24,'PP23':23}
MATRIX=(('PP24','PP24',True),('PP23','PP23',True),('PP24_OFF','PP24',False))


def make_input(parts,value=24):
    need(type(value)is int and value in(23,24),'finite owned setter Value byte')
    need(type(parts)is dict and set(parts)==set(L.THUMB)|set(L.DATA),'exact setter execution code/data parts')
    box,_=G.owned_box(3);pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(box=(BOX-16,168),value=(VALUE-16,33),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),stop=(RETURN,4))
    for name,item in {**L.THUMB,**L.DATA}.items():
        a,n,digest=item[0],item[1],item[-1];b=parts[name]
        need(type(b)is bytes and len(b)==n and sha(b)==digest,'frozen setter component '+name)
        regions[name]=(a,n);put(a,b)
    R.require_disjoint(regions)
    put(BOX-16,b'\xd3'*16+box+b'\xd3'*16);put(VALUE-16,b'\xd3'*16+bytes([value])+b'\xd3'*16)
    put(R.TOP-FRAME-GUARD,b'\xa5'*(FRAME+GUARD));put(RETURN,bytes(4))
    regs=[BOX,58,VALUE]+[0xb0000000+i*0x010101 for i in range(3,13)]+[R.TOP,RETURN|1,0x6000003f]
    return dict(input_PP=value,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    p=f['pages']
    return dict(input_PP=f['input_PP'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 then CPSR; PC separate',data_provenance='Owned synthetic encrypted Box136 plus separate Value byte; no save/player data',
        storage136_sha256=sha(M.read(p,BOX,136)),value_hex=M.read(p,VALUE,1).hex(),initial_map_sha256=M.map_digest(p),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(p.items())],
        frame136_hex=M.read(p,R.TOP-136,136).hex(),guard56_hex=M.read(p,R.TOP-192,56).hex(),
        box_guard16_before=M.read(p,BOX-16,16).hex(),box_guard16_after=M.read(p,BOX+136,16).hex(),
        value_guard16_before=M.read(p,VALUE-16,16).hex(),value_guard16_after=M.read(p,VALUE+1,16).hex())


def freeze(receipt,parts):
    return dict(schema='native-box-pp-setter-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(G.__file__))},
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,predictor_cap=4096,
                    stack_top=R.TOP,frame_bytes=136,guard_bytes=56,box=BOX,storage_bytes=136,value=VALUE,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,value))for name,value in PROFILES.items()},
        matrix=[dict(name=name,input_profile=key,observed=observe)for name,key,observe in MATRIX])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(source not in out.parents and out!=source and not out.exists()and not out.is_symlink(),'fresh private setter input')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Two owned Value inputs/shared encrypted Box136/three-call plan frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
