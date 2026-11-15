#!/usr/bin/env python3
"""Read the exact original cipher code/pools from owned current EN/IT ROMs.

No whole ROM is loaded. Plain ARM9 physical bytes must agree with an independent
ndspy decode; padding and the decrypt wrappers are excluded from code.
"""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
R=load(HERE.with_name('rileggi_fs_cached_resources.py'),'cipher_exact_rom_reader_helpers')
need,sha=R.need,R.sha
THUMB={
 'wrapper':(0x20725d8,4,2,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c'),
 'core':(0x201ff44,42,20,'389a3db4659cbf730872a30ec4eeb8f15ae258996b4ce043a334c380ead71f4e'),
 'lcg':(0x201ff78,22,11,'9c5bf64dc199aee1c4481c4aec6d3bf09ef61fa500f29bd47075fcc4b89070f4')}
DATA={
 'wrapper_pool':(0x20725dc,4,'addb0b46183eaf47ceb6aa0a83de80a6d516b55d32e16827649719e287b9243f'),
 'lcg_pool':(0x201ff90,8,'42aeea4e30dc4ac2f58e42de0ca7a7fefdd62bc97bd04a867406a09a06c16e1a')}


def read(rom,identity):
    import ndspy.code,ndspy.codeCompression
    digest,size=identity;rom=Path(rom)
    need(rom.stat().st_size==size and R.file_sha(rom)==digest,'exact cipher ROM identity')
    parts={};rows={}
    with rom.open('rb')as f:
        h=f.read(512);off,entry,base,stored_size=(R.u32(h,x)for x in(0x20,0x24,0x28,0x2c))
        need(h[12:16]==b'IPKE'and h[30]==0 and(off,entry,base,stored_size)==(0x4000,0x2000800,0x2000000,0x12b8e4),'current cipher ARM9 header')
        f.seek(off);stored=f.read(stored_size)
        need(len(stored)==stored_size and ndspy.codeCompression.decompress(stored)==stored,'plain initialized ARM9 only')
        decoded=ndspy.code.MainCodeFile(stored,base)
        for name,item in {**THUMB,**DATA}.items():
            a,n,d=item[0],item[1],item[-1];need(base<=a and a+n<=base+stored_size,'cipher initialized owner')
            pos=off+a-base;f.seek(pos);b=f.read(n)
            owners=[s for s in decoded.sections if s.ramAddress<=a and a+n<=s.ramAddress+len(s.data)]
            need(len(owners)==1,'one decoded cipher owner');owner=owners[0]
            need(sha(b)==d and b==owner.data[a-owner.ramAddress:a-owner.ramAddress+n],'physical/decoded cipher identity '+name)
            parts[name]=b;rows[name]=dict(ram=a,rom_offset=pos,bytes=n,sha256=d,kind='code'if name in THUMB else'data',compression='plain',independent_ARM9=True)
    need(R.u32(parts['wrapper_pool'],0)==0x201ff45 and [R.u32(parts['lcg_pool'],i)for i in(0,4)]==[0x41c64e6d,0x6073],'original cipher literal values')
    return dict(ROM=dict(sha256=digest,bytes=size,game_code='IPKE',revision=0),ARM9=dict(rom_offset=off,ram=base,bytes=stored_size),components=rows),parts


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code={}
    for name,(a,n,count,digest)in THUMB.items():
        b=parts[name];need(type(b)is bytes and len(b)==n and sha(b)==digest,'complete cipher code '+name)
        ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a));need(len(ins)==count and sum(i.size for i in ins)==n,'cipher Thumb starts '+name)
        for i in ins:need(i.address not in code,'disjoint cipher starts');code[i.address]=bytes(i.bytes)
    need(len(code)==33,'thirty-three cipher Thumb starts');return code


def prepare(rom,it_rom=None):
    receipt,parts=read(rom,R.EN)
    if it_rom:
        it,other=read(it_rom,R.IT);need(parts==other,'fresh current Italian cipher identity');receipt['Italian_readback']=it
    thumb_code(parts)
    return dict(schema='native-mon-cipher-resources-v1',**receipt,CPU_executed=False,compiler_invoked=False,original_C_compiler_reconstructed=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private cipher receipt')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Cipher68 code bytes/12 pool bytes, exact physical/decoded readback; no CPU/compiler')


if __name__=='__main__':main()
