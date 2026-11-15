#!/usr/bin/env python3
"""Freeze whole Reset inputs; its two Value words are written by native code.

Reuses the owned encrypted Mon and explicit ROM-derived memory archive. The
entire712-byte frame starts untouched; no precompleted PP or inter-call reset.
"""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
L=load(HERE.with_name('rileggi_mon_reset.py'),'Reset_frozen_reader')
P=load(HERE.with_name('congela_box_move_caller.py'),'Reset_retained_archive_fixture')
MON=load(HERE.with_name('congela_mon_ppup_setter.py'),'Reset_retained_owned_Mon')
R,M,need,sha=L.R,P.M,L.need,L.sha
ENTRY,RETURN,BOX=0x20714b0,P.RETURN,P.BOX
FRAME,GUARD=712,56
CHILD_TOP=R.TOP-24
ZERO_VALUE,RESET_PP_VALUE=R.TOP-24,R.TOP-20
MOVE_VALUE,PP_VALUE=R.TOP-36,R.TOP-56
FILE1,LOCAL1,DEST1=R.TOP-208,R.TOP-232,R.TOP-96
FILE2,LOCAL2,DEST2=R.TOP-176,R.TOP-200,R.TOP-64
PROFILES=dict(P.PROFILES);MATRIX=P.MATRIX


def make_input(parts,ups=3):
    mon,_,_=MON.owned_mon(ups)
    need(type(parts)is dict and set(L.NEW_THUMB)|set(L.NEW_DATA)<=set(parts),'complete new Reset components')
    base={n:b for n,b in parts.items()if n not in L.NEW_THUMB and n not in L.NEW_DATA}
    f=P.make_input(base,ups);pages={a:bytearray(b)for a,b in f['pages'].items()}
    def put(a,b):
        for start in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(start,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(mon=(BOX-16,268),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),stop=(RETURN,4),
        archive=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(P.P.ROOT,12))
    regions.update({n:item[:2]for n,item in{**L.THUMB,**L.DATA}.items()})
    regions.update({'sdk_'+n:item[:2]for n,item in P.P.SDK.COMPONENTS.items()});regions['division']=L.C.MX.DIV[:2]
    regions.update({'payload_'+hex(a):(P.P.SDK.ARCHIVE_BASE+0x1093800+a,n)for a,n in P.P.NARC.WINDOWS})
    R.require_disjoint(regions)
    for name,item in{**L.NEW_THUMB,**L.NEW_DATA}.items():
        a,n,digest=item[0],item[1],item[-1];blob=parts[name]
        need(type(blob)is bytes and len(blob)==n and sha(blob)==digest,'frozen Reset component '+name);put(a,blob)
    put(BOX-16,b'\xd3'*16+mon+b'\xd3'*16)
    need(M.read(pages,R.TOP-FRAME-GUARD,FRAME+GUARD)==b'\xa5'*(FRAME+GUARD),'Reset frame/Value words initially untouched')
    regs=[BOX,310,0]+[0xb0000000+i*0x10101 for i in range(3,13)]+[R.TOP,RETURN|1,0x6000003f]
    f.update(resource_parts=parts,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})
    return f


def input_record(f):
    pages=f['pages'];need(f['input_PP']==15 and f['payload_projections']==[],'Reset original PP15 unprojected')
    mon,boxplain,party=MON.owned_mon(f['input_Up'])
    return dict(input_Up=f['input_Up'],input_move=310,input_slot=0,input_PP=15,entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 then CPSR; PC separate',
        data_provenance='Owned checksum-encrypted Box128/PID-encrypted party100; exact ROM PP15 member and explicit memory archive; no save/player input',
        resource_parts_sha256={n:sha(b)for n,b in sorted(f['resource_parts'].items())},
        mon236_sha256=sha(mon),Box_plaintext128_sha256=sha(boxplain),party_plaintext100_sha256=sha(party),
        party_ciphertext100_sha256=sha(mon[136:]),initial_Box_key=0x2a8+f['input_Up'],party_key=0x4000,
        archive_projections=f['archive_projections'],payload_projections=f['payload_projections'],
        original_member_sha256=P.P.SDK.MEMBER_SHA,initial_map_sha256=M.map_digest(pages),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        archive92_hex=M.read(pages,R.ARC,92).hex(),root12_hex=M.read(pages,P.P.ROOT,12).hex(),
        frame712_sha256=sha(M.read(pages,R.TOP-FRAME,FRAME)),guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex(),
        native_Reset_Value_words_initial_hex=M.read(pages,ZERO_VALUE,8).hex(),
        mon_guard16_before=M.read(pages,BOX-16,16).hex(),mon_guard16_after=M.read(pages,BOX+236,16).hex(),
        payload_windows=[dict(ram=P.P.SDK.ARCHIVE_BASE+0x1093800+a,hex=M.read(pages,P.P.SDK.ARCHIVE_BASE+0x1093800+a,n).hex())for a,n in P.P.NARC.WINDOWS])


def freeze(receipt,parts):
    return dict(schema='native-Mon-Reset-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(P.__file__),Path(MON.__file__))},
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=65536,spare_return_callback_required=True,timeout_us=1000000,
            stack_top=R.TOP,frame_bytes=FRAME,guard_bytes=GUARD,mon=BOX,mon_bytes=236,
            native_Reset_Zero_Value=ZERO_VALUE,native_Reset_PP_Value=RESET_PP_VALUE,Box_move_Value=MOVE_VALUE,Box_PP_Value=PP_VALUE,
            first_MaxPP_FILE=FILE1,first_MaxPP_parser=LOCAL1,first_MaxPP_buffer=DEST1,
            second_MaxPP_FILE=FILE2,second_MaxPP_parser=LOCAL2,second_MaxPP_buffer=DEST2,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,ups))for name,ups in PROFILES.items()},
        matrix=[dict(name=name,input_profile=key,observed=observe)for name,key,observe in MATRIX])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not out.is_symlink(),'fresh private Reset input')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Owned Mon236/Reset guest Value words/whole712 frame and three-call plan frozen; no oracle/CPU/compiler')


if __name__=='__main__':main()
