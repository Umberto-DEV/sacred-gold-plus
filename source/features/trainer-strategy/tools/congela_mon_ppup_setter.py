#!/usr/bin/env python3
"""Freeze owned Mon236: checksum-encrypted Box128 and PID-encrypted party100."""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
L=load(HERE.with_name('rileggi_mon_ppup_setter.py'),'frozen_Mon_reader')
Q=load(HERE.with_name('qualifica_mon_party100.py'),'frozen_owned_party100_math')
G=load(HERE.with_name('congela_box_move_caller.py'),'retained_owned_Box_math')
R,M,need,sha=L.R,Q.M,L.need,L.sha
ENTRY,RETURN,BOX,VALUE=0x206ec40,0x22f0180,0x22f0000,0x22f0200
FRAME,GUARD=144,56
PROFILES={'Up3':3,'Up0':0}
MATRIX=(('Up3','Up3',True),('Up0','Up0',True),('Up3_OFF','Up3',False))


def owned_mon(ups):
    box,plain=G.owned_box(ups)
    party=Q.owned_plaintext();encrypted,seeds=Q.crypt100(party,0x4000)
    return box+encrypted,plain,party


def make_input(parts,ups=3):
    mon,_,_=owned_mon(ups)
    need(type(parts)is dict and set(parts)==set(L.THUMB)|set(L.DATA),'exact Mon code/data namespace')
    pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(mon=(BOX-16,268),value=(VALUE-16,36),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),stop=(RETURN,4))
    for name,item in{**L.THUMB,**L.DATA}.items():
        a,n,digest=item[0],item[1],item[-1];blob=parts[name]
        need(type(blob)is bytes and len(blob)==n and sha(blob)==digest,'frozen Mon component '+name)
        regions[name]=(a,n);put(a,blob)
    R.require_disjoint(regions)
    put(BOX-16,b'\xd3'*16+mon+b'\xd3'*16);put(VALUE-16,b'\xd3'*16+bytes(4)+b'\xd3'*16)
    put(R.TOP-FRAME-GUARD,b'\xa5'*(FRAME+GUARD));put(RETURN,bytes(4))
    need(set(pages)=={0x201f000,0x206e000,0x206f000,0x2072000,0x20ff000,0x22ef000,0x22f0000,0x23fc000},'eight owner pages including before-Mon guard')
    regs=[BOX,62,VALUE]+[0xb0000000+i*0x10101 for i in range(3,13)]+[R.TOP,RETURN|1,0x6000003f]
    return dict(input_Up=ups,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    p=f['pages'];mon,boxplain,partyplain=owned_mon(f['input_Up'])
    return dict(input_Up=f['input_Up'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 then CPSR; PC separate',
        data_provenance='New owned synthetic Mon236; Box128 checksum cipher and party100 PID cipher; no save/player/retail payload',
        mon236_sha256=sha(mon),Box_plaintext128_sha256=sha(boxplain),party_plaintext100_sha256=sha(partyplain),
        party_ciphertext100_sha256=sha(mon[136:]),initial_Box_key=0x2a8+f['input_Up'],party_key=0x4000,
        value_word_hex=M.read(p,VALUE,4).hex(),initial_map_sha256=M.map_digest(p),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(p.items())],
        frame144_hex=M.read(p,R.TOP-FRAME,FRAME).hex(),guard56_hex=M.read(p,R.TOP-FRAME-GUARD,GUARD).hex(),
        mon_guard16_before=M.read(p,BOX-16,16).hex(),mon_guard16_after=M.read(p,BOX+236,16).hex(),
        value_guard16_before=M.read(p,VALUE-16,16).hex(),value_guard16_after=M.read(p,VALUE+4,16).hex())


def freeze(receipt,parts):
    return dict(schema='native-Mon-PPUp-setter-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(Q.__file__),Path(G.__file__))},
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,predictor_cap=8192,
            stack_top=R.TOP,frame_bytes=FRAME,guard_bytes=GUARD,mon=BOX,mon_bytes=236,value=VALUE,value_bytes=4,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,ups))for name,ups in PROFILES.items()},
        matrix=[dict(name=name,input_profile=key,observed=observe)for name,key,observe in MATRIX])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not out.is_symlink(),'fresh private Mon input')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Two owned Mon236 inputs/four cipher phases/three-call plan frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
