#!/usr/bin/env python3
"""Authenticate the complete cached Convert composition and its actual path.

Owned exact ROM required; snapshot optional. No CPU, compiler or ROM model.
Root is BSS: snapshot provenance or explicit synthetic initialization only.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_cached_findpath.py'),'convert_parent_reader')
R,need,sha=L.R,L.need,L.sha
ROOT,PATH=0x021E362C,0x0210F198
PATH_BYTES=b'a/0/1/1\0'
ROOT_SHA='d706e4423ea8e7dbdf21ba2d4805ce434739559758815b35de6b0257ddb4e567'
NEW={
 'init':(0x020D7F98,40,'131f15b7db06da746cb03744ffda8f5453b1c6c2fbdf8f0dacab41326e10421f'),
 'convert':(0x020D8180,64,'8455d062eee662f58fefa731950eab06ecedb77279478b2ef41123ab5128d172'),
 'find':(0x020D7FC0,324,'baf1c233ca8efcaa3ca58e996fe2f01e437fad5753dca7bbe1e6e782dd9abcf8'),
 'send':(0x020D7788,420,'ca74d4ff51db8cb32a7d6235e6b4d453554d65ac6162dc4092b7f285d0e4051a'),
 'execute':(0x020D7744,68,'44b2f23b47f01552bd478420b9a14ae0fc2ed6013e7d551d5112075264a43d55'),
 'release':(0x020D6864,92,'658daf608846bdeca5f8d48b8b0ea7d46280ebcd2ef783fce8b5f9e12735f568'),
 'wakeup':(0x020D1ECC,104,'25c7d621d6b4d855be6828b9ec8d98162df8ecdda5a22db405caf344aa4102db'),
 'next':(0x020D749C,532,'d3785eb030614f3050cb9ef747e3a173e534c40ef5ffa3d75c95acd6fa778e9c'),
 'disable':(0x020D3A38,20,'a8cdb747f9936730571b220bb9570615892665b120713ffc59b1cb2d7dee76ff'),
 'restore':(0x020D3A4C,24,'46b5111b6fad094dfff177dca974d33b477cb72772ecfe95b74b1c7f656bc4fd')}
COMPONENTS={**L.COMPONENTS,**NEW}
# Exactly the retained recipe pools, never admitted as instruction addresses.
POOLS={'seekdir':4,'read_dir':4,'translate':4,'find':4}
CODE_SPANS=tuple((a,n-POOLS.get(name,0))for name,(a,n,_)in COMPONENTS.items()if name!='default_table')


def physical(rom):
    pieces={};rows={}
    with Path(rom).open('rb')as stream:
        h=stream.read(512);off,ram,size=R.u32(h,0x20),R.u32(h,0x28),R.u32(h,0x2c)
        for name,(a,n,digest)in {**NEW,'path':(PATH,8,sha(PATH_BYTES))}.items():
            need(ram<=a and a+n<=ram+size,'initialized ARM9 bounds '+name)
            at=off+a-ram;stream.seek(at);blob=stream.read(n)
            need(len(blob)==n and sha(blob)==digest,'physical Convert component '+name)
            pieces[name]=blob;rows[name]=dict(ram=a,rom_offset=at,bytes=n,sha256=digest)
        stream.seek(off+0xba0);settings=stream.read(36)
    need(len(settings)==36 and struct.unpack_from('<II',settings,28)==(0xdec00621,0x2106c0de),'authenticated ARM9 code settings magic')
    begin,end=struct.unpack_from('<II',settings,12)
    need((begin,end)==(0x02111860,0x021e5900)and begin<=ROOT and ROOT+12<=end,'Root BSS descriptor containment')
    return pieces,rows,dict(code_settings_rom_offset=off+0xba0,code_settings_sha256=sha(settings),bss_start=begin,bss_end=end,root_physical_offset=None)


def prepare(rom,snapshot=None,it_rom=None):
    parent,parts=L.prepare(rom,snapshot,it_rom)
    extra,rows,loader=physical(rom);parts.update(extra)
    root=struct.pack('<IHHI',R.ARC,0,0,0)
    if snapshot:
        slices=R.extract_snapshot(snapshot,{**{k:(a,n)for k,(a,n,_)in NEW.items()},'root':(ROOT,12),'path':(PATH,8)},4194304,R.SNAPSHOT_SHA)
        need(all(slices[k]==parts[k]for k in NEW)and slices['path']==PATH_BYTES,'snapshot/ROM new code/path')
        root=slices['root']
    need(sha(root)==ROOT_SHA,'exact root BSS initialization')
    parts['root']=root
    if it_rom:
        it,_,it_loader=physical(it_rom);need(it==extra and it_loader['bss_start']==loader['bss_start']and it_loader['bss_end']==loader['bss_end'],'IT Convert initialized bytes/BSS bounds')
    meta=L.resolve_path(parts['fnt'],PATH_BYTES[:-1]);lengths=[x['bytes']for x in meta['table_reads']]
    need(meta['file_id']==140 and meta['directory_ids']==[0,1,2,4]and len(lengths)==20 and
         (lengths.count(8),lengths.count(1),lengths.count(2))==(4,12,4),'independent actual path140 metadata')
    fat=struct.unpack_from('<II',parts['fat'],140*8);need(fat==(0x01093800,0x0109645c),'actual file140 FAT extent')
    return dict(schema='native-fs-cached-convert-resources-v1',tool_sha256=sha(HERE.read_bytes()),
        parent=parent,new_components=rows,loader=loader,path_metadata=meta,file140=dict(rom_start=fat[0],rom_end=fat[1],bytes=fat[1]-fat[0]),
        root=dict(ram=ROOT,bytes=12,sha256=sha(root),provenance='authenticated historical EN MainRAM BSS'if snapshot else'explicit synthetic initialization, not captured boot'),
        total_component_bytes=3740,cpu_executed=False,compiler_invoked=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        source=HERE.parents[3];need(source!=a.json.resolve()and source not in a.json.resolve().parents,'private receipt outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh output required');receipt,_=prepare(a.rom,a.snapshot,a.it_rom)
        with a.json.open('x')as out:out.write(json.dumps(receipt,indent=2)+'\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Full Convert code/path/BSS provenance and FNT140 authenticated; no CPU/compiler')


if __name__=='__main__':main()
