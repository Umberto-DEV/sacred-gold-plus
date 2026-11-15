#!/usr/bin/env python3
"""Freeze memory-archive input after caller compilation, before oracle/CPU.

The project caller is part of the input, not code extracted from the cartridge.
Its source plan precedes compilation. No host register/memory phase bridge.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
L=load(HERE.with_name('rileggi_fs_memory_read.py'),'memory_read_frozen_resources')
C=load(HERE.with_name('compila_fs_memory_read.py'),'memory_read_caller_identity')
M=load(HERE.with_name('congela_fs_cached_seekdir.py'),'memory_read_sparse_memory')
R,need,sha=L.R,L.need,L.sha
ENTRY,RETURN,FILE=L.DRIVER,0x022F0180,R.FILE
FRAME,GUARD=504,56


def load_driver(directory):
    directory=Path(directory);m=json.loads((directory/'manifesto.json').read_bytes())
    need(m['schema']=='native-fs-memory-read-recipe-v1'and m['builder_sha256']==sha(Path(C.__file__).read_bytes())and
         m['recipe_sha256']==sha(C.RECIPE.read_bytes())and m['driver_recipe_sha256']==sha(C.DRIVER_RECIPE.read_bytes()),'compiled caller/native recipe source identity')
    need(m['compiler_sha256']==C.C.CC_SHA and m['layout_passed']is True and all(x['exit_code']==0 for x in m['commands']),'completed authenticated compiler/layout receipt')
    loader=load(C.C.C.LOADER,'memory_read_freeze_driver_loader')
    obj=directory/'driver.o';blob,symbols=loader.load_text(obj.read_bytes(),ENTRY,('sgp_test_memory_narc_driver',))
    need(len(blob)==116 and symbols['sgp_test_memory_narc_driver']==ENTRY and
         sha(blob)==m['driver']['text_sha256']and R.file_sha(obj)==m['driver']['object_sha256'],'project caller ELF text/entry/file')
    need(struct.unpack_from('<II',blob,108)==(L.RESULT,0x224c),'project caller literal pool')
    return blob,dict(manifest_sha256=R.file_sha(directory/'manifesto.json'),driver=m['driver'])


def make_input(parts,driver,precompleted=False):
    need(type(precompleted)is bool and set(parts)==set(L.COMPONENTS)|{'arc','fat','fnt','root','path','narc_header','narc_member'},'exact typed memory-archive input')
    need(type(driver)is bytes and len(driver)==116,'compiled project caller116')
    spans={name:(a,n)for name,(a,n,_)in L.COMPONENTS.items()}
    root,path=L.L.L.ROOT,L.L.L.PATH
    spans.update(arc=(R.ARC,92),fat=(R.FAT,4104),fnt=(R.FNT,2902),root=(root,12),path=(path,8),
        client=(FILE-16,104),header_dest=(L.HEADER_DEST-16,48),member_dest=(L.MEMBER_DEST-16,48),result=(L.RESULT-16,52),
        header_source=(L.HEADER_SOURCE-16,48),member_source=(L.MEMBER_SOURCE-16,48),
        caller=(ENTRY,116),stack=(R.TOP-FRAME-GUARD,FRAME+GUARD),gate=(RETURN,4))
    R.require_disjoint(spans);pages={}
    for a,n in spans.values():
        for base in range(a&~4095,(a+n+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
    for name,(a,n,digest)in L.COMPONENTS.items():
        need(type(parts[name])is bytes and len(parts[name])==n and sha(parts[name])==digest,'memory Read native identity '+name);M.put(pages,a,parts[name])
    for name,a in(('arc',R.ARC),('fat',R.FAT),('fnt',R.FNT),('root',root),('path',path)):M.put(pages,a,parts[name])
    arc=bytearray(parts['arc']);need(len(arc)==92 and R.u32(arc,28)==7 and R.u32(arc,40)==0 and arc[4:28]==b'\0'*24 and arc[32:40]==b'\0'*8,'quiescent source ARC7/base0/empty lists')
    need(R.u32(arc,88)in(0,0x602)and R.u32(arc,72)in(0,0x20d84c4),'natural or declared synthetic original procedure/read pointer')
    projections=[]
    for off,value in((40,L.ARCHIVE_BASE),(72,0x20d7448),(88,R.u32(arc,88)&~0x600)):
        before=arc[off:off+4].hex();struct.pack_into('<I',arc,off,value)
        projections.append(dict(address=R.ARC+off,bytes=4,before_hex=before,after_hex=arc[off:off+4].hex()))
    M.put(pages,R.ARC,arc)
    client=bytearray(b'\xa5'*72)
    for off in(0,4,8,12,24,28):struct.pack_into('<I',client,off,0)
    struct.pack_into('<I',client,16,14);M.put(pages,FILE-16,b'\xd3'*16+client+b'\xd3'*16)
    for name,source,destination,digest in(('narc_header',L.HEADER_SOURCE,L.HEADER_DEST,L.HEADER_SHA),('narc_member',L.MEMBER_SOURCE,L.MEMBER_DEST,L.MEMBER_SHA)):
        need(len(parts[name])==16 and sha(parts[name])==digest,'owned NARC payload slice '+name)
        M.put(pages,source-16,b'\xd3'*16+parts[name]+b'\xd3'*16)
        M.put(pages,destination-16,b'\xd3'*16+(parts[name]if precompleted else b'\xa5'*16)+b'\xd3'*16)
    M.put(pages,L.RESULT-16,b'\xd3'*16+b'\xa5'*20+b'\xd3'*16)
    M.put(pages,ENTRY,driver);M.put(pages,RETURN,b'\0'*4)
    regs=[FILE,path,L.HEADER_DEST,L.MEMBER_DEST]+[0xB0000000+i*0x010101 for i in range(4,13)]+[R.TOP,RETURN,0x6000001f]
    return dict(precompleted_buffers=precompleted,entry_pc=ENTRY,entry_regs=regs,archive_projections=projections,
        pages={a:bytes(b)for a,b in pages.items()})


def input_record(f):
    pages=f['pages'];root,path=L.L.L.ROOT,L.L.L.PATH
    return dict(precompleted_buffers=f['precompleted_buffers'],entry_pc=f['entry_pc'],entry_regs=f['entry_regs'],
        register_format='R0..R14 followed by CPSR; PC separate',archive_projections=f['archive_projections'],
        initial_map_sha256=M.map_digest(pages),pages=[dict(ram=a,bytes=len(b),sha256=sha(b))for a,b in sorted(pages.items())],
        client_file72_hex=M.read(pages,FILE,72).hex(),archive92_hex=M.read(pages,R.ARC,92).hex(),root12_hex=M.read(pages,root,12).hex(),path8_hex=M.read(pages,path,8).hex(),
        header_source16_hex=M.read(pages,L.HEADER_SOURCE,16).hex(),member_source16_hex=M.read(pages,L.MEMBER_SOURCE,16).hex(),
        header_dest16_hex=M.read(pages,L.HEADER_DEST,16).hex(),member_dest16_hex=M.read(pages,L.MEMBER_DEST,16).hex(),result20_hex=M.read(pages,L.RESULT,20).hex(),
        frame504_hex=M.read(pages,R.TOP-FRAME,FRAME).hex(),guard56_hex=M.read(pages,R.TOP-FRAME-GUARD,GUARD).hex())


def freeze(receipt,parts,driver,driver_receipt):
    paths=(HERE,Path(L.__file__),Path(L.L.__file__),Path(L.L.L.__file__),Path(L.L.L.L.__file__),Path(R.__file__),Path(M.__file__),Path(C.__file__),C.RECIPE,C.DRIVER_RECIPE)
    return dict(schema='native-fs-memory-read-input-v1',source_identities={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in paths},
        resources_receipt_sha256=sha((json.dumps(receipt,indent=2)+'\n').encode()),project_driver=driver_receipt,
        resource_provenance=receipt['parent']['parent']['parent']['parent_resource_receipt']['resource_provenance'],
        context_provenance='Synthetic project caller/CPU/client/stack/pages; exact resource slices; hybrid memory-payload ARC projections, not natural CARD protocol',
        policy=dict(models=0,runtime_host_writes=0,instruction_cap=8192,timeout_us=1000000,client_file=FILE,
            header_destination=L.HEADER_DEST,member_destination=L.MEMBER_DEST,result_vector=L.RESULT,
            stack_top=R.TOP,frame_bytes=FRAME,guard_bytes=GUARD,stop_pc=RETURN),
        fixtures={'normal':input_record(make_input(parts,driver)),'precompleted_buffers':input_record(make_input(parts,driver,True))})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in('rom','recipe-dir','json'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);a=p.parse_args()
    try:
        source=HERE.parents[3];need(source!=a.json.resolve()and source not in a.json.resolve().parents,'private output outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh frozen output required')
        receipt,parts=L.prepare(a.rom,a.snapshot);driver,dr=load_driver(a.recipe_dir)
        with a.json.open('x')as out:out.write(json.dumps(freeze(receipt,parts,driver,dr),indent=2)+'\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Two complete memory-archive inputs frozen after caller build; no oracle/CPU')


if __name__=='__main__':main()
