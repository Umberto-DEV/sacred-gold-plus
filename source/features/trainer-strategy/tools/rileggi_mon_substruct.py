#!/usr/bin/env python3
"""Read the exact original substructure code from owned current EN/IT ROMs.

No whole ROM is loaded. Plain ARM9 physical bytes must agree with an independent
ndspy decode; the assertion BL, padding and neighboring functions are excluded from code.
"""
from pathlib import Path
import argparse
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
R=load(HERE.with_name('rileggi_fs_cached_resources.py'),'substructure_exact_rom_reader_helpers')
need,sha=R.need,R.sha
THUMB={
 'prefix':(0x2072608,20,10,'426d3165503db1e38d2178aebc8b6e747de61d32df1fb4ce671fb3b662a2a108'),
 'lookup':(0x2072620,14,7,'1e669de78867533449de32f097484d90e484fc145a2a57c0d2640bd9d0c34991')}
DATA={
 'table_literal':(0x2072630,4,'bdd9e387f769acd6c58a3637a6ebb45bc5cd102462572d8d4ee0416e0a3d81fb'),
 'offsets':(0x20ff733,128,'13df5d291eb7b8276c065d7033d8044a9b430df77c05d04069cd3438e54b179a')}


def source_offsets(text):
    import re
    marker='PokemonDataBlock *GetSubstruct(BoxPokemon *boxMon, u32 pid, u8 which) {'
    need(type(text)is str and text.count(marker)==1,'one bounded GetSubstruct C definition')
    body=text.split(marker,1)[1].split('\n}\n',1)[0]
    need(body.count('static const u8 offsets[32][4] = {')==1 and
         body.count('pid = ((pid & 0x3E000) >> 13);')==1 and body.count('GF_ASSERT(which <= 3);')==1 and
         body.count('boxMon->dataBlocks + offsets[pid][which]')==1,'GetSubstruct source selector/guard/return recipe')
    table=body.split('static const u8 offsets[32][4] = {',1)[1].split('};',1)[0]
    pattern=r'\{\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)\s*\}'
    rows=[tuple(int(v,16)for v in row)for row in re.findall(pattern,table)]
    need(not re.sub(r'[\s,]','',re.sub(pattern,'',table))and len(rows)==32,'exact source array32x4, no extra expressions')
    need(all(sorted(row)==[0,32,64,96]for row in rows)and len(set(rows[:24]))==24 and rows[24:]==rows[:8],'source24permutations plus8repeats')
    return bytes(v for row in rows for v in row)


def read(rom,identity):
    import ndspy.code,ndspy.codeCompression
    digest,size=identity;rom=Path(rom)
    need(rom.stat().st_size==size and R.file_sha(rom)==digest,'exact substructure ROM identity')
    parts={};rows={}
    with rom.open('rb')as f:
        h=f.read(512);off,entry,base,stored_size=(R.u32(h,x)for x in(0x20,0x24,0x28,0x2c))
        need(h[12:16]==b'IPKE'and h[30]==0 and(off,entry,base,stored_size)==(0x4000,0x2000800,0x2000000,0x12b8e4),'current substructure ARM9 header')
        f.seek(off);stored=f.read(stored_size)
        need(len(stored)==stored_size and ndspy.codeCompression.decompress(stored)==stored,'plain initialized ARM9 only')
        decoded=ndspy.code.MainCodeFile(stored,base)
        for name,item in {**THUMB,**DATA}.items():
            a,n,d=item[0],item[1],item[-1];need(base<=a and a+n<=base+stored_size,'substructure initialized owner')
            pos=off+a-base;f.seek(pos);b=f.read(n)
            owners=[s for s in decoded.sections if s.ramAddress<=a and a+n<=s.ramAddress+len(s.data)]
            need(len(owners)==1,'one decoded substructure owner');owner=owners[0]
            need(sha(b)==d and b==owner.data[a-owner.ramAddress:a-owner.ramAddress+n],'physical/decoded substructure identity '+name)
            parts[name]=b;rows[name]=dict(ram=a,rom_offset=pos,bytes=n,sha256=d,kind='code'if name in THUMB else'data',compression='plain',independent_ARM9=True)
    need(R.u32(parts['table_literal'],0)==0x20ff733,'literal preserves unaligned data pointer')
    return dict(ROM=dict(sha256=digest,bytes=size,game_code='IPKE',revision=0),ARM9=dict(rom_offset=off,ram=base,bytes=stored_size),components=rows),parts


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code={}
    for name,(a,n,count,digest)in THUMB.items():
        b=parts[name];need(type(b)is bytes and len(b)==n and sha(b)==digest,'complete substructure code '+name)
        ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a));need(len(ins)==count and sum(i.size for i in ins)==n,'substructure Thumb starts '+name)
        for i in ins:need(i.address not in code,'disjoint substructure starts');code[i.address]=bytes(i.bytes)
    need(len(code)==17,'seventeen substructure Thumb starts');return code


def prepare(rom,it_rom=None):
    receipt,parts=read(rom,R.EN)
    if it_rom:
        it,other=read(it_rom,R.IT);need(parts==other,'fresh current Italian substructure identity');receipt['Italian_readback']=it
    thumb_code(parts)
    return dict(schema='native-mon-substructure-resources-v1',**receipt,CPU_executed=False,compiler_invoked=False,original_C_compiler_reconstructed=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private substructure receipt')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('GetSubstruct34 code bytes/132 data bytes, exact physical/decoded readback; no CPU/compiler')


if __name__=='__main__':main()
