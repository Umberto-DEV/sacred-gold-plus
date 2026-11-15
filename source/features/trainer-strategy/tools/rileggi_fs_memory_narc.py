#!/usr/bin/env python3
"""Read exact native NARC caller, path row and seven tiny payload windows.

Reuses the qualified cached FS resource reader. The four Thumb spans have no
recovered C compiler provenance; physical and independently decoded bytes do.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_memory_read.py'),'narc_memory_parent_resources')
R,need,sha=L.R,L.need,L.sha
THUMB={
 'thumb_wrapper':(0x2007508,22,10,'35f4ac50be98a10b0c0ebd562ed4d45e5bdffa88ca7ff0134f0c09090a8df196'),
 'thumb_first':(0x200732c,98,42,'0f2890f6d5c533785bd464399a496a780ab21162dabc4829f3c878c5049f379c'),
 'thumb_mid':(0x2007392,98,43,'5353169e22ee79de93dfe32d757e89feea1ef586b9fba01e30fdf6dc2fdbbf47'),
 'thumb_last':(0x20073f8,20,8,'7740a174f812ba014226329d5680a4a9cff0cb216fc4c37180ab3392adba6262')}
DATA={
 'narc_pool':(0x2007520,4,'ee48acbcb107da0b1d1af8eda167ab79e113683b28f1f143aa88b068a82806e4'),
 'narc_row':(0x210f23c,4,'47f17c887161032c5c95017ed0bd91bdca7c0715613dd1a46e63c6bf67233a8e'),
 'narc_path':(0x210f198,8,'039cf62fb6583b2cf76af0d848e60c215a239786e95fe2d4b43fc2cb2394c86f')}
WINDOWS=((0xc,2),(0x14,4),(0x18,2),(0xed8,4),(0x9cc,4),(0x9d0,4),(0x224c,16))
SOURCE_SHA='ee526fc2835b2c2259dd393087fb1a5ca036dbf467bcfbd7735b1476819c869d'


def physical(rom):
    import ndspy.code
    rows={};parts={}
    with Path(rom).open('rb')as f:
        header=f.read(512);offset,base,size=(R.u32(header,x)for x in(0x20,0x28,0x2c))
        f.seek(offset);arm9=f.read(size);need(len(arm9)==size,'complete bounded ARM9')
        decoded=ndspy.code.MainCodeFile(arm9,base)
        for name,item in {**THUMB,**DATA}.items():
            a,n,digest=item[0],item[1],item[-1]
            need(base<=a and a+n<=base+size,'initialized native reader extent')
            physical_offset=offset+a-base;f.seek(physical_offset);b=f.read(n)
            sections=[s for s in decoded.sections if s.ramAddress<=a and a+n<=s.ramAddress+len(s.data)]
            need(len(sections)==1,'unique independently decoded reader section')
            s=sections[0];need(b==s.data[a-s.ramAddress:a-s.ramAddress+n]and sha(b)==digest,'physical/decoded native reader '+name)
            parts[name]=b;rows[name]=dict(ram=a,rom_offset=physical_offset,bytes=n,sha256=digest,independent_ARM9=True)
        payload=[]
        for relative,n in WINDOWS:
            pos=0x1093800+relative;f.seek(pos);b=f.read(n);need(len(b)==n,'complete tiny NARC read')
            parts['payload_'+hex(relative)]=b
            payload.append(dict(file_offset=relative,rom_offset=pos,ram=L.ARCHIVE_BASE+pos,bytes=n,sha256=sha(b)))
    # Header/BTAF/BTNF/member properties are independently checked by L.prepare.
    expected=(bytes.fromhex('1000'),bytes.fromhex('c40e0000'),bytes.fromhex('d701'),bytes.fromhex('10000000'),bytes.fromhex('60130000'),bytes.fromhex('70130000'))
    need(tuple(parts['payload_'+hex(a)]for a,n in WINDOWS[:-1])==expected,'finite native parser metadata36')
    need(sha(parts['payload_0x224c'])==L.MEMBER_SHA,'exact final member16')
    need(struct.unpack('<I',parts['narc_pool'])[0]+11*4==DATA['narc_row'][0]and
         struct.unpack('<I',parts['narc_row'])[0]==DATA['narc_path'][0]and parts['narc_path']==b'a/0/1/1\0','actual table row11/path/pool')
    return parts,rows,payload


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    starts={}
    for name,(a,n,count,digest)in THUMB.items():
        b=parts[name];need(len(b)==n and sha(b)==digest,'exact native Thumb span '+name)
        instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a))
        need(len(instructions)==count and sum(i.size for i in instructions)==n,'ordinary Thumb decoding '+name)
        for i in instructions:
            need(i.address not in starts,'disjoint Thumb instruction starts');starts[i.address]=bytes(i.bytes)
    need(len(starts)==103 and len(starts[0x20073fe])==4 and 0x2007400 not in starts,'whole BLX pair crossing7400')
    return starts


def prepare(rom,snapshot=None,it_rom=None):
    receipt,parts=L.prepare(rom,snapshot,it_rom);extra,rows,payload=physical(rom);parts.update(extra)
    if it_rom:
        it,_,ip=physical(it_rom);need(extra==it and payload==ip,'fresh IT Thumb/data/windows identity')
    code=thumb_code(parts)
    return dict(schema='native-fs-memory-narc-resources-v1',parent=receipt,native_reader=rows,payload_windows=payload,
        Thumb_starts=len(code),Thumb_bytes=238,source_candidate_sha256=SOURCE_SHA,
        project_driver=False,compiler_invoked=False,CPU_executed=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('rom','json'):p.add_argument('--'+key,type=Path,required=True)
    for key in('snapshot','it-rom'):p.add_argument('--'+key,type=Path)
    a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(source!=out and source not in out.parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh resource receipt')
        receipt,_=prepare(a.rom,a.snapshot,a.it_rom)
        with a.json.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Native Thumb103, row11 and seven owned windows36 authenticated; no CPU/compiler')


if __name__=='__main__':main()
