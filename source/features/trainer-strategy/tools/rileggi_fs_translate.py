#!/usr/bin/env python3
"""Read Translate ELF and ROM lineage, separating instructions/pool/table/gate."""
from pathlib import Path
import argparse,gc,importlib.util,mmap,struct


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


L=load('translate_qualified_elf_reader',Path(__file__).with_name('rileggi_fs_read.py'))
C=load('translate_recovered_builder',Path(__file__).with_name('compila_fs_translate.py'))
P,need,sha=L.P,L.need,L.sha
need(sha(Path(L.__file__).read_bytes())=='f7991b5bf8b38df910470c503f26ff4ccb994b6bcc5f90ebf7a88867f161fd71','Translate independent ELF reader drift')
object_text=L.object_text
DEFAULT_GATE_SHA='462b796a6c11d4277cd269fd03b7c46c2e0de0394c8071aa4a7a8d079be7bb87'


def split_extent(body):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
    need(type(body)is bytes and len(body)==400 and sha(body)==C.BODIES['command'][2],'Translate exact whole400 including pool')
    need(sha(body[:396])==C.CODE_SHA and struct.unpack_from('<I',body,396)[0]==0x210E124,'Translate code396 and literal pointer')
    code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body[:396],0x20D68C0))
    need(len(code)==99 and sum(i.size for i in code)==396 and code[-1].address==0x20D6A48 and code[-1].mnemonic=='pop',
         'Translate complete instruction extent excludes literal')
    return code


def analyze(paths,language,recipe_dir=None):
    address,n,digest=C.BODIES['command'];obj=None if recipe_dir is None else recipe_dir/'fs-translate-command.o'
    recovered=None if obj is None else object_text(obj,n,digest);rows=[]
    for role in('retail','base11','v4','r4'):
        model=P.G.S.SHARED.read_current(paths[role],language)if role=='r4'else P.G.S.SHARED.read_image(paths[role],language,role)
        with paths[role].open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            body=P.G.piece(model['segments'],address,n);physical=None
            if role in('v4','r4'):
                view=P.G.S.SHARED.gifts_audit.Arm9View(raw);need(view.read(address,n)==body,'Translate physical/decoded whole extent')
                physical=hex(view.offset(address,n))
            matched=sha(body)==digest;code=split_extent(body)if matched else None
            pool=struct.unpack_from('<I',body,396)[0];table=P.G.piece(model['segments'],pool,36)
            slot4=struct.unpack_from('<I',table,16)[0];gate=P.G.piece(model['segments'],slot4,4)
            data_physical={}
            if role in('v4','r4'):
                for name,a,size,blob in(('pool',address+396,4,body[396:]),('table',pool,36,table),('default_gate',slot4,4,gate)):
                    need(view.read(a,size)==blob,'Translate physical/decoded '+name);data_physical[name]=hex(view.offset(a,size))
            need(role!='r4'or(matched and pool==0x210E124 and sha(table)==C.TABLE_SHA and slot4==0x20D6DB0 and sha(gate)==DEFAULT_GATE_SHA),
                 'Translate exact current code/data/default target')
            rows.append(dict(role=role,input=model['record'],component=dict(ram=hex(address),rom_offset=physical,bytes=n,sha256=sha(body),
                equal_to_current=matched,equal_to_recipe=None if recovered is None else body==recovered,instruction_bytes=396,literal_pool_bytes=4,
                ARM_starts=None if code is None else len(code),code_sha256=sha(body[:396]),
                calls=[]if code is None else[dict(pc=hex(i.address),mnemonic=i.mnemonic,target=i.op_str)for i in code if i.mnemonic in('bl','blx')]),
                data=dict(pool=dict(ram=hex(address+396),rom_offset=data_physical.get('pool'),value=hex(pool)),
                    table=dict(ram=hex(pool),rom_offset=data_physical.get('table'),bytes=36,sha256=sha(table)),
                    default_slot4=dict(ram=hex(pool+16),target=hex(slot4)),
                    default_gate=dict(ram=hex(slot4),rom_offset=data_physical.get('default_gate'),bytes=4,sha256=sha(gate),executed=False))))
        del model;gc.collect();L.H.H.R.W.require_host_budget()
    return dict(schema='native-fs-translate-lineage-v1',language=language,images=rows,cpu_executed=False,compiler_invoked=False,
        tool_sha256=sha(Path(__file__).read_bytes()),recipe_object_sha256=None if obj is None else sha(obj.read_bytes()),
        limits=['Source/ELF/code/data correspondence only; no native Translate/default handler activation proved here',
                'Unmatched historical bodies retain their revision identity, not automatically attributed',
                'Original Metrowerks C codegen and compressed historical physical offsets not reconstructed'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('retail','base','v4','rom','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--recipe-dir',type=Path);a=parser.parse_args()
    try:
        result=analyze(dict(retail=a.retail,base11=a.base,v4=a.v4,r4=a.rom),a.language,a.recipe_dir);L.H.save(a.json,result)
    except ValueError as error:parser.exit(2,str(error)+'\n')
    print(a.language,'Translate lineage and pool/table/default gate read without guest CPU')


if __name__=='__main__':main()
