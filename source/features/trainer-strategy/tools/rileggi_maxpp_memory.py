#!/usr/bin/env python3
"""Authenticate whole MaxPP Thumb and its signed division ARM body.

The current images have plain initialized ARM9 windows. Historical compressed
images require identifying and decoding the stored ARM9 owner separately.
"""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_pp_memory.py'),'MaxPP_original_PP_resources')
R,need,sha=L.R,L.need,L.sha
MAXPP=(0x207332c,40,18,'9a0f4b0193e9ec2c4fcffddf1526daf9a9bb23262051e5b6b6e986ffcba6ec9f')
DIV=(0x20f2998,524,'e8183a62ffe6a54210cd7d025b01431ff792025c1b45a0e8537abd8cec16ccfb')


def physical(rom):
    import ndspy.code,ndspy.codeCompression
    parts={};rows={}
    with Path(rom).open('rb')as f:
        h=f.read(512);off,base,size=(R.u32(h,x)for x in(0x20,0x28,0x2c))
        need(size<=4*1024**2,'bounded MaxPP ARM9 owner');f.seek(off);stored=f.read(size)
        need(len(stored)==size and ndspy.codeCompression.decompress(stored)==stored,'current MaxPP plain ARM9 physical mapping')
        decoded=ndspy.code.MainCodeFile(stored,base)
        for name,item in(('maxpp',MAXPP),('signed_div',DIV)):
            a,n,digest=item[0],item[1],item[-1];need(base<=a and a+n<=base+size,'current MaxPP initialized window')
            pos=off+a-base;f.seek(pos);b=f.read(n)
            owners=[s for s in decoded.sections if s.ramAddress<=a and a+n<=s.ramAddress+len(s.data)]
            need(len(owners)==1,'unique decoded MaxPP owner');s=owners[0]
            need(b==s.data[a-s.ramAddress:a-s.ramAddress+n]and sha(b)==digest,'physical/decoded MaxPP identity '+name)
            parts[name]=b;rows[name]=dict(ram=a,rom_offset=pos,bytes=n,sha256=digest,independent_ARM9=True,compression='plain')
    return parts,rows


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code=L.thumb_code(parts);a,n,count,digest=MAXPP;b=parts['maxpp']
    need(len(b)==n and sha(b)==digest,'complete MaxPP Thumb identity')
    ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a))
    need(len(ins)==count and sum(i.size for i in ins)==n,'ordinary MaxPP18 Thumb starts')
    for i in ins:
        need(i.address not in code,'disjoint MaxPP/child Thumb starts');code[i.address]=bytes(i.bytes)
    need(len(code)==146,'complete MaxPP/PP/NARC146 ordinary Thumb starts')
    return code


def prepare(rom,it_rom=None):
    # This case adds arithmetic/stack/clamp coverage in the already qualified
    # ROM-derived memory resource mode; it acquires no second capture mode.
    receipt,parts=L.prepare(rom,None,it_rom);extra,rows=physical(rom);parts.update(extra)
    if it_rom:need(physical(it_rom)[0]==extra,'fresh Italian MaxPP/DIV byte identity')
    code=thumb_code(parts)
    return dict(schema='native-MaxPP-memory-resources-v1',parent=receipt,new_components=rows,
        native_Thumb_starts=len(code),division_ARM_starts=131,resource_mode='ROM-derived memory archive',
        CPU_executed=False,compiler_invoked=False,original_Thumb_C_compiler_reconstructed=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents,'private MaxPP output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh MaxPP resource output')
        receipt,_=prepare(a.rom,a.it_rom)
        with a.json.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Original MaxPP40/DIV524 authenticated with PP/NARC/SDK resources; no CPU/compiler')


if __name__=='__main__':main()
