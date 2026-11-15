#!/usr/bin/env python3
"""Authenticate the complete Reset caller, two Mon leaves and retained SDK.

Adds the real Reset56, veneer4/literal4 and selected Mon148 bytes to the
qualified Box/MaxPP resource reader. No trainer record, CPU or compiler.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
C=load(HERE.with_name('rileggi_box_move_caller.py'),'Reset_retained_Box_MaxPP_resources')
MON=load(HERE.with_name('rileggi_mon_ppup_setter.py'),'Reset_retained_Mon_resources')
OLD=load(HERE.with_name('rileggi_box_move_lineage.py'),'Reset_qualified_BL_decoder')
R,need,sha=C.R,C.need,C.sha
NEW_THUMB={**MON.NEW_THUMB,
 'reset':(0x20714b0,56,24,'3e8f6c199fa28d8ecedf54d8ec64dff4e87489670785ccf96e3d34c3de4e579f'),
 'mon_veneer':(0x20714e8,4,2,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c')}
NEW_DATA={'mon_target':(0x20714ec,4,'1546a4580bb2146c10d9a99c44c9a226821a7cf8955b67aa4b3437ac10536a15')}
THUMB={**C.THUMB,**NEW_THUMB};DATA={**C.DATA,**NEW_DATA}
CODE_SPANS,SDK_CODE_SPANS=C.CODE_SPANS,C.SDK_CODE_SPANS
read_new=types.FunctionType(C.BOX.read.__code__,{**C.BOX.read.__globals__,'THUMB':NEW_THUMB,
    'DATA':{**NEW_DATA,**{n:C.DATA[n]for n in('wrapper_pool','lcg_pool')}}},argdefs=C.BOX.read.__defaults__)


def validate_targets(parts):
    body=parts['reset'];need(type(body)is bytes and len(body)==56,'complete Reset56 code')
    targets=[OLD.bl_target(0x20714b0+i,body[i:i+4])for i in(10,26,34,48)]
    need(targets==[0x20714e8,0x206ec40,0x207332c,0x206ec40],'Reset four actual BL targets')
    need(parts['mon_veneer']==bytes.fromhex('004b1847')and parts['mon_target']==bytes.fromhex('f1140702'),'Reset actual Thumb veneer/literal')
    table=parts['attribute_table'];need(type(table)is bytes and len(table)==376,'complete Reset setter table')
    for attr,target in((58,0x206f0f4),(62,0x206f104)):
        need(0x206ee3e+int.from_bytes(table[2*attr:2*attr+2],'little',signed=True)==target,'Reset distinct setter row '+str(attr))
    return targets


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code=C.thumb_code(parts)
    for name,(a,n,count,digest)in NEW_THUMB.items():
        blob=parts[name];need(type(blob)is bytes and len(blob)==n and sha(blob)==digest,'exact Reset/Mon selected code '+name)
        instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,a))
        need(len(instructions)==count and sum(i.size for i in instructions)==n,'complete Reset selected starts '+name)
        for i in instructions:need(i.address not in code,'disjoint Reset Thumb starts');code[i.address]=bytes(i.bytes)
    need(len(code)==512 and sum(len(b)for b in code.values())==1132,'Reset512Thumbstarts/1132codebytes')
    return code


def prepare(rom,it_rom=None):
    retained,parts=C.prepare(rom,it_rom);receipt,new=read_new(rom,R.EN)
    if it_rom:
        it,other=read_new(it_rom,R.IT);need(other==new,'fresh Italian Reset/Mon selected byte identity');receipt['Italian_readback']=it
    for name in('wrapper_pool','lcg_pool'):need(new.pop(name)==parts[name],'Reset retained cipher literal agreement '+name)
    combined=C.merge_unique(parts,new);targets=validate_targets(combined);code=thumb_code(combined)
    regions={n:item[:2]for n,item in{**THUMB,**DATA}.items()}
    regions.update({'sdk_'+n:item[:2]for n,item in C.F87.SDK.COMPONENTS.items()});regions['division']=C.MX.DIV[:2]
    R.require_disjoint(regions)
    return dict(schema='native-Mon-Reset-resources-v1',retained=retained,new_components=receipt,
        Thumb_starts=len(code),Thumb_bytes=1132,new_Thumb_starts=92,new_Thumb_bytes=208,new_literal_bytes=4,
        actual_Reset_BL_targets=targets,SDK_ARM_starts=retained['SDK_ARM_starts'],DIV_ARM_starts=131,
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(C.__file__),Path(MON.__file__),Path(OLD.__file__))},
        original_C_codegen_reconstructed=False,CPU_executed=False,compiler_invoked=False,
        scope='Complete Reset/Box/Mon62/Mon58/MaxPP/SDK selected bytes; no native caller state or natural activation inferred'),combined


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not out.is_symlink(),'fresh private Reset resources')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Reset/Mon/Box/MaxPP/SDK selected1132ThumbB512starts authenticated; no CPU/compiler')


if __name__=='__main__':main()
