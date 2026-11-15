#!/usr/bin/env python3
"""Read Translate instruction selection, slot2 and the new stopped SeekDir gate."""
from pathlib import Path
import argparse,gc,importlib.util,mmap,struct

path=Path(__file__).with_name('rileggi_fs_translate.py')
s=importlib.util.spec_from_file_location('nested_seekdir_qualified_reader',path)
L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
P,C,need,sha,object_text=L.P,L.C,L.need,L.sha,L.object_text
SITES=tuple(range(0x20D68C0,0x20D6904,4))+tuple(range(0x20D6968,0x20D6984,4))
SELECTED_SHA='10afa067cfbc14c45d16e8126e4976e7510861f37de05ab644101947d558fe42'
GATE_SHA='cb2450f37bd96fdbd6b5ca0da7f783e6a195e37f754014852618c0f6593e4d89'
COMPONENTS={'code_and_pool':(0x20D68C0,400,C.BODIES['command'][2]),'table':(0x210E124,36,C.TABLE_SHA),
            'default_gate':(0x20D6BEC,4,GATE_SHA)}


def selected(body):
    need(type(body)is bytes and len(body)==400 and sha(body[:396])==C.CODE_SHA,'Nested SEEKDIR exact Translate instructions')
    result=b''.join(body[a-0x20D68C0:a-0x20D68C0+4]for a in SITES)
    need(len(result)==96 and sha(result)==SELECTED_SHA,'Nested SEEKDIR selected24 ARM identity')
    return result


def analyze(paths,language,recipe_dir=None):
    obj=None if recipe_dir is None else recipe_dir/'fs-translate-command.o'
    recovered=None if obj is None else object_text(obj,400,C.BODIES['command'][2]);rows=[]
    for role in('retail','base11','v4','r4'):
        model=P.G.S.SHARED.read_current(paths[role],language)if role=='r4'else P.G.S.SHARED.read_image(paths[role],language,role)
        with paths[role].open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            body=P.G.piece(model['segments'],0x20D68C0,400);instructions=selected(body)
            pool=struct.unpack_from('<I',body,396)[0];table=P.G.piece(model['segments'],pool,36)
            target=struct.unpack_from('<I',table,8)[0];gate=P.G.piece(model['segments'],target,4);offsets={}
            need(sha(table)==C.TABLE_SHA and target==0x20D6BEC and sha(gate)==GATE_SHA,'Nested SEEKDIR historical slot2 and original gate')
            if role in('v4','r4'):
                view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
                for name,a,n,blob in(('code_and_pool',0x20D68C0,400,body),('table',pool,36,table),('default_gate',target,4,gate)):
                    need(view.read(a,n)==blob,'Nested SEEKDIR independent physical/decoded '+name);offsets[name]=hex(view.offset(a,n))
            need(role!='r4'or sha(body)==C.BODIES['command'][2]and pool==0x210E124,'Nested SEEKDIR exact current whole400/pool')
            rows.append(dict(role=role,input=model['record'],component=dict(ram='0x20d68c0',rom_offset=offsets.get('code_and_pool'),
                bytes=400,sha256=sha(body),whole_equal_to_current=sha(body)==C.BODIES['command'][2],code396_sha256=sha(body[:396]),
                selected_instruction_bytes=96,selected_PC_count=24,selected_sha256=sha(instructions),
                whole_equal_to_recipe=None if recovered is None else body==recovered),
                table=dict(ram=hex(pool),rom_offset=offsets.get('table'),bytes=36,sha256=sha(table),slot2_ram=hex(pool+8),target=hex(target)),
                default_gate=dict(ram=hex(target),rom_offset=offsets.get('default_gate'),bytes=4,sha256=sha(gate),executed=False)))
        del model;gc.collect();L.L.H.H.R.W.require_host_budget()
    return dict(schema='native-fs-nested-seekdir-lineage-v1',language=language,images=rows,cpu_executed=False,compiler_invoked=False,
        tool_sha256=sha(Path(__file__).read_bytes()),recipe_object_sha256=None if obj is None else sha(obj.read_bytes()),
        limits=['Selected instruction bytes are two ranges within the400-byte recipe, not a new contiguous payload',
                'Retail Italian pool relocation remains; no global address shift or historical activation inferred',
                'Gate is read back only; no native SeekDir body, result, FNT or card access qualified'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('retail','base','v4','rom','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--recipe-dir',type=Path);a=p.parse_args()
    try:r=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language,a.recipe_dir);L.L.H.save(a.json,r)
    except ValueError as error:p.exit(2,str(error)+'\n')
    print(a.language,'nested SEEKDIR instruction/table/gate lineage read without new CPU/compiler')


if __name__=='__main__':main()
