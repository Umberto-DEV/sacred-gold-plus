#!/usr/bin/env python3
"""Freeze owned encrypted Box136 fixtures and a three-call plan, no oracle/CPU."""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_box_ppup.py'),'box_frozen_reader')
M=load(HERE.with_name('congela_fs_cached_seekdir.py'),'box_sparse_memory_helpers')
R,need,sha=L.R,L.need,L.sha
ENTRY,RETURN,BOX=0x206e640,0x22f0180,0x22f0000
FRAME,GUARD=64,56
PROFILES={'PPUp3':3,'PPUp1':1}
MATRIX=(('PPUp3','PPUp3',True),('PPUp1','PPUp1',True),('PPUp3_OFF','PPUp3',False))


def owned_box(ups):
    need(type(ups)is int and ups in(1,3),'finite owned Box PP-Up')
    plain=bytearray(128)
    struct.pack_into('<HH',plain,0,355,3-ups)
    struct.pack_into('<H',plain,64,310);plain[72]=15;plain[76]=ups
    checksum=sum(x[0]for x in struct.iter_unpack('<H',plain))&65535
    need(checksum==0x2ab,'counterfixture preserves checksum/key')
    seed=checksum;cipher=bytearray()
    for value, in struct.iter_unpack('<H',plain):
        seed=(seed*1103515245+24691)&0xffffffff;cipher.extend(struct.pack('<H',value^(seed>>16)))
    box=struct.pack('<IHH',0x4000,0,checksum)+cipher
    expected={3:'f88425686bc184b9f50a004384b16518c09f785cf190112595938e3220c72cf1',
              1:'bd5ede160c2f5a32955e35ccdd7f249e4f8398e03cad93325c80b14f9aa630e2'}
    need(sha(box)==expected[ups],'independent frozen Box136 digest')
    return box,bytes(plain)


def make_input(parts,ups=3):
    box,plain=owned_box(ups)
    need(type(parts)is dict and set(parts)==set(L.THUMB)|set(L.DATA),'exact Box code/data parts')
    pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(box=(BOX-16,168),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),stop=(RETURN,4))
    for name,item in {**L.THUMB,**L.DATA}.items():
        a,n,digest=item[0],item[1],item[-1];b=parts[name]
        need(type(b)is bytes and len(b)==n and sha(b)==digest,'frozen Box component '+name)
        regions[name]=(a,n);put(a,b)
    R.require_disjoint(regions)
    put(BOX-16,b'\xd3'*16+box+b'\xd3'*16);put(R.TOP-FRAME-GUARD,b'\xa5'*(FRAME+GUARD));put(RETURN,bytes(4))
    regs=[BOX,62,0]+[0xb0000000+i*0x010101 for i in range(3,13)]+[R.TOP,RETURN|1,0x6000003f]
    return dict(input_PPUp=ups,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    p=f['pages']
    return dict(input_PPUp=f['input_PPUp'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 then CPSR; PC separate',data_provenance='Owned synthetic encrypted Box136, not a save or proof of a legalized player Pokemon',
        storage136_sha256=sha(M.read(p,BOX,136)),initial_map_sha256=M.map_digest(p),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(p.items())],
        frame64_hex=M.read(p,R.TOP-64,64).hex(),guard56_hex=M.read(p,R.TOP-120,56).hex(),
        box_guard16_before=M.read(p,BOX-16,16).hex(),box_guard16_after=M.read(p,BOX+136,16).hex())


def freeze(receipt,parts):
    return dict(schema='native-box-ppup-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(M.__file__))},
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,predictor_cap=4096,
                    stack_top=R.TOP,frame_bytes=64,guard_bytes=56,box=BOX,storage_bytes=136,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,ups))for name,ups in PROFILES.items()},
        matrix=[dict(name=name,input_profile=key,observed=observe)for name,key,observe in MATRIX])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(source not in out.parents and out!=source and not out.exists()and not out.is_symlink(),'fresh private Box input')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Two owned encrypted Box136 inputs/three-call plan frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
