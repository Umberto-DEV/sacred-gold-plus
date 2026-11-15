#!/usr/bin/env python3
"""Authenticate full Mon setter62, direct Box-internal bridge and crypto data.

The outer Box setter is excluded: this API owns both decrypt/encrypt phases
and delegates directly to SetBoxMonDataInternal. No SDK/NARC/CPU/compiler.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
P=load(HERE.with_name('rileggi_box_move_setter.py'),'Mon_setter_retained_Box_primitive_specs')
R,need,sha=P.R,P.need,P.sha
REMOVE={'setter_before_check','setter_valid','internal_leaf54_return'}
NEW_THUMB={
 'mon_before_check':(0x206ec40,56,25,'6cded28002cfd750a2903885dcb4627fa1969d1de3ed1c2079ab693aaa1a90ad'),
 'mon_valid':(0x206ec96,56,24,'7b2697d0c60d02b6c6835a729be7f5a8067c057a1b8b4f3d8162ae05c37d4d80'),
 'mon_internal_prefix':(0x206ecd0,12,6,'75c36c185d829eb7b6073e76a996fbd4c23ff9892e02e25889c3edb6171bcaf5'),
 'mon_internal_default':(0x206ed68,8,3,'37e1977db75a19437664645e5fdfe726c9a95c62142fc876dafe1278360efb8b'),
 'internal_leaf62_return':(0x206f104,16,8,'4e884e4675f5ff764b97c8e5f3cbcdc614dc031912a2aca6be481ef6711eaf6c')}
THUMB={**{n:x for n,x in P.THUMB.items()if n not in REMOVE},**NEW_THUMB}
DATA=dict(P.DATA)
read=types.FunctionType(P.read.__code__,{**P.read.__globals__,'THUMB':THUMB,'DATA':DATA},argdefs=P.read.__defaults__)


def thumb_code(parts):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    code={}
    for name,(a,n,count,digest)in THUMB.items():
        b=parts[name];need(type(b)is bytes and len(b)==n and sha(b)==digest,'exact selected Mon setter code '+name)
        instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,a))
        need(len(instructions)==count and sum(i.size for i in instructions)==n,'complete Mon setter Thumb starts '+name)
        for i in instructions:need(i.address not in code,'disjoint Mon setter Thumb starts');code[i.address]=bytes(i.bytes)
    need(len(code)==173 and sum(len(b)for b in code.values())==372,'selected372B/173Thumbstarts')
    return code


def prepare(rom,it_rom=None):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
    receipt,parts=read(rom,R.EN)
    if it_rom:
        it,other=read(it_rom,R.IT);need(parts==other,'fresh Italian Mon setter/crypto/table identity');receipt['Italian_readback']=it
    code=thumb_code(parts);R.require_disjoint({n:item[:2]for n,item in{**THUMB,**DATA}.items()})
    row=int.from_bytes(parts['attribute_table'][124:126],'little',signed=True)
    need(row==0x2c6 and 0x206ee3e+row==0x206f104,'actual setter row62 signed target')
    instructions=[i for pc,b in code.items()for i in Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(b,pc)]
    calls=[(i.address,i.op_str)for i in instructions if i.mnemonic=='bl'and 0x206ec40<=i.address<0x206ed70]
    need(calls==[(0x206ec58,'#0x20725e0'),(0x206ec64,'#0x20725e0'),(0x206ec6e,'#0x20725e8'),
        (0x206ec9c,'#0x206ecd0'),(0x206ecb0,'#0x20725d8'),(0x206ecba,'#0x20725e8'),(0x206ecc8,'#0x20725d8'),(0x206ed6a,'#0x206ede8')],
        'actual Mon decrypt/checksum/internal/default/encrypt calls')
    need(not any(a<=0x206ed70<a+n for a,n,count,digest in THUMB.values()),'outer Box wrapper not concatenated')
    return dict(schema='native-Mon-PPUp-setter-resources-v1',**receipt,Thumb_code_bytes=372,Thumb_starts=173,new_code_bytes=148,new_Thumb_starts=66,
        native_calls=calls,setter_attribute=62,setter_table_row_ram=0x206eeb8,setter_table_row_bytes=2,setter_table_row_signed=row,
        native_party_bytes=100,native_Box_payload_bytes=128,original_C_codegen_reconstructed=False,CPU_executed=False,compiler_invoked=False,
        source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes())for p in(HERE,Path(P.__file__))},
        scope='Flags0/checksum-valid selected Mon setter62 path; assertions/other attributes/native compiler reconstruction excluded'),parts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in('rom','json'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--it-rom',type=Path);a=p.parse_args()
    try:
        out=a.json.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private Mon setter resource receipt')
        receipt,_=prepare(a.rom,a.it_rom)
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError,EOFError)as e:p.exit(2,str(e)+'\n')
    print('Complete Mon setter62 selected Thumb173/code372 and crypto/data authenticated; no CPU/compiler')


if __name__=='__main__':main()
