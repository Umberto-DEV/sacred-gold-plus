#!/usr/bin/env python3
"""Authenticate the original GetMoveAttr PP path above native NARC/SDK.

New initialized Thumb/data windows are read physically and through ndspy ARM9.
Only the selected leaf is admitted; the other move properties remain data or
unqualified code, including the adjacent MaxPP/division path.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_memory_narc.py'),'pp_original_NARC_resources')
R,need,sha=L.R,L.need,L.sha
THUMB={
 'move_attr':(0x2073314,24,10,'3b28368c5ddcffb86f982fba1d4767e00586e0cb8cf50ec7b3cd71dd56a2359d'),
 'load_move':(0x20733b0,10,5,'a67a2fad71f627a5023490d31e0162de64a66eb5799f8be758a0d73c27f1a90e'),
 'move_dispatch':(0x2073354,16,8,'c37bf3289ada9a8e00932e13329776690e3b04d917d49d036de887425f973d66'),
 'move_pp':(0x2073390,4,2,'7423cd12fbe46937d5346c65380d51ee2353e51f5ecfe268960864d3725eb54a')}
DATA={
 'move_table':(0x2073364,24,'1d652784a4fc754fd28dba22a70ee575feebbe65dc2dadc1aa56690a04b3134f'),
 'move_literal':(0x20733bc,4,'7c077a9160f0ef35be4dc9f35a6450fb911be9ed8fab707af0a24c5859bdfabc')}
SOURCE_SHA='e9adae2d57511a89ec5cc52ebb5741172a5d90123d02d33be66143ddf210e7b2'


def physical(rom):
    import ndspy.code
    parts={};rows={}
    with Path(rom).open('rb')as f:
        h=f.read(512);offset,base,size=(R.u32(h,x)for x in(0x20,0x28,0x2c))
        f.seek(offset);arm9=f.read(size);need(len(arm9)==size,'complete bounded ARM9')
        decoded=ndspy.code.MainCodeFile(arm9,base)
        for name,item in {**THUMB,**DATA}.items():
            a,n,digest=item[0],item[1],item[-1];need(base<=a and a+n<=base+size,'initialized PP window')
            pos=offset+a-base;f.seek(pos);b=f.read(n)
            owners=[s for s in decoded.sections if s.ramAddress<=a and a+n<=s.ramAddress+len(s.data)]
            need(len(owners)==1,'unique decoded PP owner');s=owners[0]
            need(b==s.data[a-s.ramAddress:a-s.ramAddress+n]and sha(b)==digest,'physical/decoded PP identity '+name)
            parts[name]=b;rows[name]=dict(ram=a,rom_offset=pos,bytes=n,sha256=digest,independent_ARM9=True)
    need(struct.unpack('<I',parts['move_literal'])[0]==0x2007509 and
         struct.unpack_from('<H',parts['move_table'],10)[0]==42,'exact reader tail pointer and PP switch offset')
    return parts,rows


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code=L.thumb_code(parts)
    for name,(a,n,count,digest)in THUMB.items():
        b=parts[name];need(len(b)==n and sha(b)==digest,'exact PP span '+name)
        ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a))
        need(len(ins)==count and sum(i.size for i in ins)==n,'ordinary PP Thumb decode')
        for i in ins:
            need(i.address not in code,'disjoint PP/NARC code');code[i.address]=bytes(i.bytes)
    need(len(code)==128,'finite NARC/PP128 starts')
    need(not any(a<=pc<a+n for a,n,digest in DATA.values()for pc in code),'PP switch/pool excluded from instructions')
    return code


def prepare(rom,snapshot=None,it_rom=None):
    receipt,parts=L.prepare(rom,snapshot,it_rom);extra,rows=physical(rom);parts.update(extra)
    if it_rom:need(physical(it_rom)[0]==extra,'fresh Italian PP windows identity')
    code=thumb_code(parts)
    return dict(schema='native-PP-memory-resources-v1',parent=receipt,PP_components=rows,Thumb_starts=len(code),
        new_Thumb_bytes=54,new_data_bytes=28,source_candidate_sha256=SOURCE_SHA,original_member_bytes=16,
        original_PP_value=15,input_projection_included=False,CPU_executed=False,compiler_invoked=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    for k in('snapshot','it-rom'):p.add_argument('--'+k,type=Path)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh PP resource receipt')
        receipt,_=prepare(a.rom,a.snapshot,a.it_rom)
        with a.json.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Original PP getter54 code/28 data and parent NARC/SDK authenticated; no CPU/compiler')


if __name__=='__main__':main()
