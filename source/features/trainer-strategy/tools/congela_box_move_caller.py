#!/usr/bin/env python3
"""Freeze two owned Box inputs and the whole caller entry, no oracle or CPU.

PP-Up alone changes in plaintext. HeldItem is zero in both; the corresponding
checksum/cipher changes are consequences, without the old compensation field.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_box_move_caller.py'),'caller_frozen_reader')
P=L.F87
R,M,need,sha=L.R,P.M,L.need,L.sha
ENTRY,RETURN,BOX=0x20714f0,0x22f0180,0x22f0000
FRAME,GUARD=688,56
MOVE_VALUE,PP_VALUE,FILE,LOCAL,DEST=(R.TOP-n for n in(12,32,184,208,72))
PROFILES={'Up3':3,'Up0':0}
MATRIX=(('Up3','Up3',True),('Up0','Up0',True),('Up3_OFF','Up3',False))
BOX_SHA={3:'f88425686bc184b9f50a004384b16518c09f785cf190112595938e3220c72cf1',
         0:'3fd3c211d9881a296ca06df38cb96762a52c895c1b3a6d37d1d5d599cb7a0cee'}


def owned_box(ups):
    need(type(ups)is int and ups in(0,3),'finite own caller PP-Up domain')
    plain=bytearray(128);struct.pack_into('<HH',plain,0,355,0)
    struct.pack_into('<H',plain,64,310);plain[72]=15;plain[76]=ups
    key=sum(x[0]for x in struct.iter_unpack('<H',plain))&65535;seed=key;cipher=bytearray()
    for value, in struct.iter_unpack('<H',plain):
        seed=(seed*1103515245+24691)&0xffffffff;cipher.extend(struct.pack('<H',value^(seed>>16)))
    box=struct.pack('<IHH',0x4000,0,key)+cipher
    need(key==0x2a8+ups and sha(box)==BOX_SHA[ups],'independent owned caller Box digest/key')
    return box,bytes(plain)


def make_input(parts,ups=3):
    box,_=owned_box(ups)
    need(type(parts)is dict,'typed complete caller byte parts')
    maxparts={name:b for name,b in parts.items()if name not in L.BOX_THUMB and name not in L.BOX_DATA}
    f=P.make_input(maxparts,3,15);pages={a:bytearray(b)for a,b in f['pages'].items()}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    regions=dict(box=(BOX-16,168),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),stop=(RETURN,4),
                 arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(P.ROOT,12))
    regions.update({name:item[:2]for name,item in{**L.THUMB,**L.DATA}.items()})
    regions.update({'sdk_'+name:item[:2]for name,item in P.SDK.COMPONENTS.items()});regions['division']=L.MX.DIV[:2]
    regions.update({'payload_'+hex(a):(P.SDK.ARCHIVE_BASE+0x1093800+a,n)for a,n in P.NARC.WINDOWS})
    R.require_disjoint(regions)
    for name,item in{**L.BOX_THUMB,**L.BOX_DATA}.items():
        a,n,digest=item[0],item[1],item[-1];b=parts[name]
        need(type(b)is bytes and len(b)==n and sha(b)==digest,'frozen composed Box component '+name);put(a,b)
    need(set(parts)==set(maxparts)|set(L.BOX_THUMB)|set(L.BOX_DATA),'complete caller part namespace')
    put(BOX-16,b'\xd3'*16+box+b'\xd3'*16)
    need(M.read(pages,R.TOP-FRAME-GUARD,FRAME+GUARD)==b'\xa5'*(FRAME+GUARD),'caller complete initial untouched stack/guard')
    regs=[BOX,310,0]+[0xb0000000+i*0x010101 for i in range(3,13)]+[R.TOP,RETURN|1,0x6000003f]
    f.update(resource_parts=parts,input_Up=ups,input_move=310,input_slot=0,entry_pc=ENTRY,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})
    return f


def input_record(f):
    pages=f['pages'];need(f['input_PP']==15 and f['payload_projections']==[],'unprojected original PP15 member')
    return dict(input_Up=f['input_Up'],input_move=f['input_move'],input_slot=f['input_slot'],input_PP=15,
        entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],register_format='R0..R14 then CPSR; PC separate',
        data_provenance='Owned encrypted Box136; original PP15 ROM member; explicit memory archive; no save/player data',
        resource_parts_sha256={n:sha(b)for n,b in sorted(f['resource_parts'].items())},
        storage136_sha256=sha(M.read(pages,BOX,136)),initial_key=int.from_bytes(M.read(pages,BOX+6,2),'little'),
        archive_projections=f['archive_projections'],payload_projections=f['payload_projections'],
        original_member_sha256=P.SDK.MEMBER_SHA,initial_map_sha256=M.map_digest(pages),
        pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        archive92_hex=M.read(pages,R.ARC,92).hex(),root12_hex=M.read(pages,P.ROOT,12).hex(),
        frame688_sha256=sha(M.read(pages,R.TOP-FRAME,FRAME)),guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex(),
        box_guard16_before=M.read(pages,BOX-16,16).hex(),box_guard16_after=M.read(pages,BOX+136,16).hex(),
        payload_windows=[dict(ram=P.SDK.ARCHIVE_BASE+0x1093800+a,hex=M.read(pages,P.SDK.ARCHIVE_BASE+0x1093800+a,n).hex())for a,n in P.NARC.WINDOWS])


def freeze(receipt,parts):
    return dict(schema='native-box-move-caller-input-v1',resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),
        source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(L.__file__),Path(P.__file__))},
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=32768,spare_callback_required=True,timeout_us=1000000,
            stack_top=R.TOP,frame_bytes=FRAME,guard_bytes=GUARD,box=BOX,move_Value=MOVE_VALUE,PP_Value=PP_VALUE,
            client_file=FILE,parser_local=LOCAL,native_buffer=DEST,stop_pc=RETURN),
        fixtures={name:input_record(make_input(parts,ups))for name,ups in PROFILES.items()},
        matrix=[dict(name=name,input_profile=key,observed=observe)for name,key,observe in MATRIX])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(source not in out.parents and out!=source and not out.exists()and not out.is_symlink(),'fresh private caller input')
        receipt,parts=L.prepare(a.rom)
        with out.open('x')as f:json.dump(freeze(receipt,parts),f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Two caller inputs/three-call plan frozen; no standalone Value, oracle, CPU or compiler')


if __name__=='__main__':main()
