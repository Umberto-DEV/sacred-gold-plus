#!/usr/bin/env python3
"""Read the finite original encrypted Box PP-Up getter route, current EN/IT.

Retains the physical/ndspy ARM9 reader, current ROM identities and cipher
literal checks. Jump tables and unexercised assert/default routes are data or
excluded; they must never be decoded as permitted instructions.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
C=load(HERE.with_name('rileggi_mon_cipher.py'),'box_cipher_reader')
S=load(HERE.with_name('rileggi_mon_substruct.py'),'box_substructure_reader')
K=load(HERE.with_name('rileggi_mon_checksum.py'),'box_checksum_reader')
R,need,sha=C.R,C.need,C.sha
THUMB={**C.THUMB,**S.THUMB,**K.THUMB,
 'getter_before_check':(0x206e640,44,20,'94d6f681ec0c88a47bdffe0182a02c4708484fbc15e4b53558211b72c37eb591'),
 'getter_valid':(0x206e67c,36,16,'08b1c2815cc37d8524a1050a35f22d2434f980dfcf261b0309196379e3f0cef3'),
 'internal_prefix':(0x206e6a0,72,32,'309f123580189aa70099164b6fa2c484f390b54000cc9451932872057ee049b4'),
 'internal_dispatch':(0x206e6ea,12,6,'24b7c5eec85fa2487665f7a48d8de8643c17493b1de9f2a5bd5f5b3b3e7b2510'),
 'internal_leaf62':(0x206e97e,12,6,'2a7b6501c97854be547aa8c93d2975061395b4369a51a053312229e6f6cdf33b'),
 'internal_return':(0x206ec36,6,3,'137230d072c7eca5a8d6a25855af75a84edc89b985876ee421b9667d53942621'),
 'decrypt_wrapper':(0x20725e0,4,2,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c'),
 'decrypt_alias':(0x201ff70,4,2,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c')}
DATA={**C.DATA,**S.DATA,
 'decrypt_wrapper_pool':(0x20725e4,4,'777b3f69c8b59a74a66765635e7c7cddbc3a889ac265fe240a287c024d0f7b1f'),
 'decrypt_alias_pool':(0x201ff74,4,'addb0b46183eaf47ceb6aa0a83de80a6d516b55d32e16827649719e287b9243f'),
 'attribute_table':(0x206e6f6,376,'be62e943e6963975954d7195c2f02162c3d8d92a6ba6de69416c3c3d1e843f97')}
read=types.FunctionType(C.read.__code__,{**C.read.__globals__,'THUMB':THUMB,'DATA':DATA},argdefs=C.read.__defaults__)


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code={}
    for name,(a,n,count,digest)in THUMB.items():
        b=parts[name];need(type(b)is bytes and len(b)==n and sha(b)==digest,'Box code '+name)
        ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a))
        need(len(ins)==count and sum(i.size for i in ins)==n,'complete Box Thumb starts '+name)
        for i in ins:need(i.address not in code,'disjoint Box code');code[i.address]=bytes(i.bytes)
    need(len(code)==153 and sum(len(b)for b in code.values())==324,'finite Box153starts/324codebytes')
    return code


def prepare(rom,it_rom=None):
    receipt,parts=read(rom,R.EN)
    if it_rom:
        other,p=read(it_rom,R.IT);need(p==parts,'fresh Italian Box route identity');receipt['Italian_readback']=other
    need(R.u32(parts['decrypt_wrapper_pool'],0)==0x201ff71 and R.u32(parts['decrypt_alias_pool'],0)==0x201ff45,
         'native two-hop decrypt tail pointers retain Thumb bit')
    need(R.u32(parts['table_literal'],0)==0x20ff733,'unaligned GetSubstruct data pointer')
    need(int.from_bytes(parts['attribute_table'][124:126],'little')==0x286,'attribute62 real dispatch row')
    thumb_code(parts)
    return dict(schema='native-box-ppup-resources-v1',**receipt,CPU_executed=False,compiler_invoked=False,
                original_C_compiler_reconstructed=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(source not in out.parents and out!=source and not out.exists()and not out.is_symlink(),'fresh private Box readback')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Box getter324 code/528 data bytes physically and independently read back; no CPU/compiler')


if __name__=='__main__':main()
