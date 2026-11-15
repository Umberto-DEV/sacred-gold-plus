#!/usr/bin/env python3
"""Read the finite native Box PP setter route and its static move caller.

Current exact EN/IT ROMs only. The caller is authenticated but excluded from
the execution fixture; jump tables remain data and all error leaves excluded.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
P=load(HERE.with_name('rileggi_box_ppup.py'),'setter_retained_box_reader')
R,need,sha=P.R,P.need,P.sha
THUMB={**P.C.THUMB,**P.S.THUMB,**P.K.THUMB,
 'decrypt_wrapper':P.THUMB['decrypt_wrapper'],'decrypt_alias':P.THUMB['decrypt_alias'],
 'setter_before_check':(0x206ed70,44,20,'53acd545c111ee51a5f83580b2170664e73d4b313c28b1f5fc7a587a3cdfbdeb'),
 'setter_valid':(0x206edba,44,19,'87d29463274cb7305fa4013331e2b39644e1660de7c1ef4b4c7d64123a85d4e3'),
 'internal_prefix':(0x206ede8,70,31,'a0a536f377fdc4f126ffb6777eab009dd12a91952af247d7fef4e7cbc38d0741'),
 'internal_dispatch':(0x206ee30,12,6,'24b7c5eec85fa2487665f7a48d8de8643c17493b1de9f2a5bd5f5b3b3e7b2510'),
 'internal_leaf58_return':(0x206f0f4,16,8,'c7ea46cc0aa29cacf23d9c24f99a622124919eff60bd008a85896056b8f630ae')}
DATA={**P.DATA,'attribute_table':(0x206ee3c,376,'fd895513256dc971df570f3f9f8bc069c9f41bb58da799241a4eadf5aa6aa2bf')}
CALLER=(0x2071512,26,11,'47456def46a6a888550aacbb7c4a496a10aa92d15b1f96f8c3e6ddd71c1c3c9d')
read=types.FunctionType(P.read.__code__,{**P.read.__globals__,'THUMB':{**THUMB,'static_caller':CALLER},'DATA':DATA},argdefs=P.read.__defaults__)


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code={}
    for name,(a,n,count,digest)in THUMB.items():
        b=parts[name];need(type(b)is bytes and len(b)==n and sha(b)==digest,'Box setter code '+name)
        ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a))
        need(len(ins)==count and sum(i.size for i in ins)==n,'complete setter Thumb starts '+name)
        for i in ins:need(i.address not in code,'disjoint setter code');code[i.address]=bytes(i.bytes)
    need(len(code)==154 and sum(len(b)for b in code.values())==328,'setter154starts/328codebytes')
    return code


def prepare(rom,it_rom=None):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    receipt,parts=read(rom,R.EN)
    if it_rom:
        it,other=read(it_rom,R.IT);need(other==parts,'current Italian setter/caller identity');receipt['Italian_readback']=it
    caller=parts.pop('static_caller');ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(caller,CALLER[0]))
    need(len(ins)==11 and sum(i.size for i in ins)==26,'static move caller complete starts')
    calls=[(i.address,i.op_str)for i in ins if i.mnemonic=='bl']
    need(calls==[(0x2071516,'#0x207332c'),(0x2071526,'#0x206ed70')],'static MaxPP and setter caller targets')
    receipt['static_caller']=dict(**receipt['components'].pop('static_caller'),executed=False,calls=calls)
    need(int.from_bytes(parts['attribute_table'][116:118],'little')==0x2b6,'native setter dispatch row58')
    need(R.u32(parts['decrypt_wrapper_pool'],0)==0x201ff71 and R.u32(parts['decrypt_alias_pool'],0)==0x201ff45
         and R.u32(parts['table_literal'],0)==0x20ff733,'setter retained tail pointers and unaligned data table')
    thumb_code(parts)
    return dict(schema='native-box-pp-setter-resources-v1',**receipt,CPU_executed=False,compiler_invoked=False,
                original_C_compiler_reconstructed=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private setter readback')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Setter328code/528data bytes plus26static caller bytes read back; no CPU/compiler')


if __name__=='__main__':main()
