#!/usr/bin/env python3
"""Authenticate complete Box move caller, selected Box branches and MaxPP/SDK.

This reader merges existing exact physical/ndspy readers. It executes no CPU
code and no compiler, and returns no inferred caller state or synthesized PP.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
MX=load(HERE.with_name('rileggi_maxpp_memory.py'),'caller_MaxPP_resources')
F87=load(HERE.with_name('congela_maxpp_memory.py'),'caller_MaxPP_resource_specs')
BOX=load(HERE.with_name('rileggi_box_move_setter.py'),'caller_move_setter_resources')
GET=load(HERE.with_name('rileggi_box_ppup.py'),'caller_Box_getter_resources')
PP=load(HERE.with_name('rileggi_box_pp_setter.py'),'caller_PP_setter_resources')
R,need,sha=MX.R,MX.need,MX.sha
GET_NAMES=('getter_before_check','getter_valid','internal_prefix','internal_dispatch','internal_leaf62','internal_return')
BOX_THUMB={**BOX.THUMB,**{'get_'+n:GET.THUMB[n]for n in GET_NAMES},
           'set_pp_leaf':PP.THUMB['internal_leaf58_return'],'move_caller':BOX.CALLER}
BOX_DATA={**BOX.DATA,'get_attribute_table':GET.DATA['attribute_table']}
THUMB={**F87.NARC.THUMB,**F87.P.L.THUMB,'maxpp':MX.MAXPP,**BOX_THUMB}
DATA={**F87.NARC.DATA,**F87.P.L.DATA,**BOX_DATA}
SDK_CODE_SPANS=tuple((a,n-F87.SDK.POOLS.get(name,0))for name,(a,n,d)in F87.SDK.COMPONENTS.items()if name!='default_table')
CODE_SPANS=SDK_CODE_SPANS+(MX.DIV[:2],)
read_box=types.FunctionType(BOX.read.__code__,{**BOX.read.__globals__,'THUMB':BOX_THUMB,'DATA':BOX_DATA},argdefs=BOX.read.__defaults__)


def merge_unique(*groups):
    result={}
    for group in groups:
        need(type(group)is dict and all(type(k)is str and type(v)is bytes for k,v in group.items()),'typed named caller byte parts')
        for key,value in group.items():
            need(key not in result,'duplicate caller part '+key);result[key]=value
    return result


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code={}
    for name,(a,n,count,digest)in THUMB.items():
        b=parts[name];need(type(b)is bytes and len(b)==n and sha(b)==digest,'exact composed Thumb '+name)
        ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a))
        need(len(ins)==count and sum(i.size for i in ins)==n,'complete composed Thumb starts '+name)
        for i in ins:need(i.address not in code,'disjoint composed Thumb code');code[i.address]=bytes(i.bytes)
    need(len(code)==420 and sum(len(b)for b in code.values())==924,'caller420Thumbstarts/924codebytes')
    return code


def prepare(rom,it_rom=None):
    max_receipt,max_parts=MX.prepare(rom,it_rom)
    box_receipt,box_parts=read_box(rom,R.EN)
    if it_rom:
        it,other=read_box(it_rom,R.IT);need(other==box_parts,'fresh Italian complete Box caller/children identity')
        box_receipt['Italian_readback']=it
    parts=merge_unique(max_parts,box_parts)
    for table,row,want in(('attribute_table',54,0x2a6),('attribute_table',58,0x2b6),('get_attribute_table',62,0x286)):
        need(int.from_bytes(parts[table][2*row:2*row+2],'little')==want,'actual composed dispatch '+table+'/'+str(row))
    regions={name:item[:2]for name,item in{**THUMB,**DATA}.items()}
    regions.update({'sdk_'+name:item[:2]for name,item in F87.SDK.COMPONENTS.items()});regions['division']=MX.DIV[:2]
    R.require_disjoint(regions);thumb_code(parts)
    return dict(schema='native-box-move-caller-resources-v1',MaxPP=max_receipt,Box=box_receipt,
        Thumb_code_bytes=924,Thumb_starts=420,SDK_ARM_starts=sum(n for a,n in SDK_CODE_SPANS)//4,DIV_ARM_starts=131,
        source_sha256={str(p.relative_to(HERE.parents[3])):sha(p.read_bytes())for p in(HERE,Path(MX.__file__),Path(BOX.__file__),Path(GET.__file__),Path(PP.__file__))},
        resource_mode='Explicit ROM-derived memory archive; original PP15 member, no PP1 projection',
        original_Thumb_C_compiler_reconstructed=False,CPU_executed=False,compiler_invoked=False),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private complete caller resources')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Complete caller/Box/MaxPP/NARC/30SDK/DIV resources authenticated; no CPU/compiler')


if __name__=='__main__':main()
