#!/usr/bin/env python3
"""Read the finite original move-u16 setter and its unexecuted complete caller."""
from pathlib import Path
import argparse
import importlib.util
import json
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
P=load(HERE.with_name('rileggi_box_pp_setter.py'),'move_retained_setter_reader')
R,need,sha=P.R,P.need,P.sha
THUMB={name:item for name,item in P.THUMB.items()if name!='internal_leaf58_return'}
THUMB['internal_leaf54_return']=(0x206f0e4,16,8,'4f920065b56cd91bd9ecf53c4862b154f56e8dc91164dcbfe79c0caab2c1e8a5')
DATA=dict(P.DATA)
CALLER=(0x20714f0,66,29,'241d632c25e2e2130111d57bd97d01fa3e0c3085fcd88383e7ea4fc0ef01c5e4')
read=types.FunctionType(P.read.__code__,{**P.read.__globals__,'THUMB':{**THUMB,'static_caller':CALLER},'DATA':DATA},argdefs=P.read.__defaults__)
thumb_code=types.FunctionType(P.thumb_code.__code__,{**P.thumb_code.__globals__,'THUMB':THUMB},argdefs=P.thumb_code.__defaults__)


def prepare(rom,it_rom=None):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    receipt,parts=read(rom,R.EN)
    if it_rom:
        it,other=read(it_rom,R.IT);need(other==parts,'current Italian move setter/caller identity');receipt['Italian_readback']=it
    caller=parts.pop('static_caller');ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(caller,CALLER[0]))
    need(len(ins)==29 and sum(i.size for i in ins)==66,'complete static move caller starts')
    calls=[(i.address,i.op_str)for i in ins if i.mnemonic=='bl']
    need(calls==[(0x20714fe,'#0x206ed70'),(0x207150a,'#0x206e640'),(0x2071516,'#0x207332c'),(0x2071526,'#0x206ed70')],
         'static move setter/getter/MaxPP/PP setter targets')
    receipt['static_caller']=dict(**receipt['components'].pop('static_caller'),executed=False,calls=calls)
    need(int.from_bytes(parts['attribute_table'][108:110],'little')==0x2a6,'native move dispatch row54')
    need(R.u32(parts['decrypt_wrapper_pool'],0)==0x201ff71 and R.u32(parts['decrypt_alias_pool'],0)==0x201ff45
         and R.u32(parts['table_literal'],0)==0x20ff733,'move retained tail pointers/unaligned data table')
    thumb_code(parts)
    return dict(schema='native-box-move-setter-resources-v1',**receipt,CPU_executed=False,compiler_invoked=False,
                original_C_compiler_reconstructed=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private move readback')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Move setter328code/528data plus66static caller bytes read back; no CPU/compiler')


if __name__=='__main__':main()
