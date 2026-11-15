#!/usr/bin/env python3
"""Read default FindPath owner/prefix and the independent ELF without execution."""
from pathlib import Path
import argparse,gc,importlib.util,mmap,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


L=load('default_findpath_elf_reader',Path(__file__).with_name('rileggi_fs_translate.py'))
C=load('default_findpath_recovered_builder',Path(__file__).with_name('compila_fs_default_findpath.py'))
P,need,sha,object_text=L.P,L.need,L.sha,L.object_text


def split_prefix(body):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
    address,n,digest=C.BODIES['command'];need(type(body)is bytes and len(body)==n and sha(body)==digest,'Default FindPath exact prefix28')
    code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body,address))
    need(len(code)==7 and sum(x.size for x in code)==28 and code[-1].mnemonic=='bl','Default FindPath seven ARM instructions')
    word=struct.unpack_from('<I',body,24)[0];delta=word&0xffffff
    if delta&0x800000:delta-=0x1000000
    need(word>>24==0xeb and address+24+8+4*delta==0x20D68C0,'Default FindPath original nested Translate BL')
    return code


def analyze(paths,language,recipe_dir=None):
    address,n,digest=C.BODIES['command'];obj=None if recipe_dir is None else recipe_dir/'fs-default-findpath-command.o'
    recovered=None if obj is None else object_text(obj,n,digest);rows=[]
    for role in('retail','base11','v4','r4'):
        model=P.G.S.SHARED.read_current(paths[role],language)if role=='r4'else P.G.S.SHARED.read_image(paths[role],language,role)
        with paths[role].open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            body=P.G.piece(model['segments'],address,484);prefix=body[:n];physical=None
            if role in('v4','r4'):
                view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(view.read(address,484)==body,'Default FindPath physical/decoded owner')
                physical=hex(view.offset(address,484))
            matched=sha(prefix)==digest
            if matched:split_prefix(prefix)
            need(role!='r4'or(matched and sha(body)==C.OWNER_SHA),'Default FindPath exact current prefix and owner')
            rows.append(dict(role=role,input=model['record'],component=dict(ram=hex(address),rom_offset=physical,
                owner_bytes=484,owner_sha256=sha(body),owner_equal_to_current=sha(body)==C.OWNER_SHA,
                prefix_bytes=n,prefix_sha256=sha(prefix),prefix_equal_to_current=matched,
                prefix_equal_to_recipe=None if recovered is None else prefix==recovered,
                prefix_ARM_starts=7 if matched else None,execution_proved=False)))
        del model;gc.collect();L.L.H.H.R.W.require_host_budget()
    return dict(schema='native-fs-default-findpath-prefix-lineage-v1',language=language,images=rows,cpu_executed=False,compiler_invoked=False,
        tool_sha256=sha(Path(__file__).read_bytes()),recipe_object_sha256=None if obj is None else sha(obj.read_bytes()),
        limits=['Only prefix28 reconstructed; full owner484 readback is separate, not full C code generation',
                'No filesystem/default completion or historical/native activation proved here',
                'Compressed historical physical offsets omitted when not independently established'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('retail','base','v4','rom','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--recipe-dir',type=Path);a=p.parse_args()
    try:r=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language,a.recipe_dir);L.L.H.save(a.json,r)
    except ValueError as error:p.exit(2,str(error)+'\n')
    print(a.language,'default FindPath owner and prefix read independently; no new CPU/compiler')


if __name__=='__main__':main()
