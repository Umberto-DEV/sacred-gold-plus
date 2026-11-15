#!/usr/bin/env python3
"""Qualify four owned STRB immediate kernels before native Box setter runs."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
A=load(HERE.parents[1]/'test/arm_thumb_box_setter_oracle.py','owned_setter_arithmetic')
T=load(HERE.with_name('qualifica_maxpp_aritmetica.py'),'setter_owned_fixture_helper')
need=A.need


def page_digest(pages):
    return hashlib.sha256(b''.join(struct.pack('<I',a)+bytes(b)for a,b in sorted(pages.items()))).hexdigest()


def owned_cases():
    specs=(('STRB-actual-unscaled-low8',0x7201,{0:0x3001,1:0x87654318},0xb800003f,0x3009,24),
           ('STRB-imm31-lowFF',0x77c1,{0:0x3000,1:0x1234ffff},0x7000003f,0x301f,255),
           ('STRB-base-source-alias31',0x77ff,{7:0x3003},0x9000003f,0x3022,3),
           ('STRB-wrap32',0x7201,{0:0xfffffff8,1:0x123456fe},0x6000003f,0,254))
    rows=[]
    for name,word,values,flags,address,value in specs:
        f,code,spans,stop=T.thumb_kernel([word],values,flags)
        pages={a:bytearray(b)for a,b in f['pages'].items()}
        if address==0:pages[0]=bytearray(b'\xa5'*4096)
        f['pages']={a:bytes(b)for a,b in pages.items()}
        stores=[dict(pc=0x1000,address=address,bytes=1,before='a5',value=value)]
        pages[address&~4095][address&4095]=value;final={a:bytes(b)for a,b in pages.items()}
        returned=list(f['entry_regs']);flow=[dict(pc=a,regs=returned)for a in(0x1000,0x1002)]
        rows.append((name,f,code,spans,stop,returned,flow,stores,final))
    return rows


def expected_receipt():
    rows=[]
    for name,f,code,spans,stop,returned,flow,stores,final in owned_cases():
        rows.append(dict(name=name,instructions=2,reads=0,stores=1,full16_every_pc=True,all_pages=True,
            returned=returned,flow_sha256=hashlib.sha256(json.dumps(flow,sort_keys=True).encode()).hexdigest(),
            stores_sha256=hashlib.sha256(json.dumps(stores,sort_keys=True).encode()).hexdigest(),
            final_pages_address_prefix_sha256=page_digest(final)))
    return dict(schema='native-box-pp-setter-owned-kernels-v1',CPU_model=17,
        scope='Four owned synthetic STRB programs; no ROM/setter loaded; no ARM946 silicon or timing claim',
        source_sha256={str(p.relative_to(HERE.parents[3])):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in(HERE,Path(A.__file__),Path(T.__file__),Path(T.K.__file__))},cases=rows)


def qualify():
    for name,f,code,spans,stop,returned,flow,stores,final in owned_cases():
        prediction=A.run(f,spans,stop,cap=64,thumb_code=code)
        need(prediction['returned']==returned and prediction['flow']==flow,'independent owned setter registers/flow '+name)
        need(prediction['reads']==[]and prediction['stores']==stores and prediction['pages']==final,
             'independent owned setter byte/preimage/neighbors '+name)
        actual=T.K.execute(f,code,spans,stop)
        for key in('flow','reads','stores','returned','stop_pc','pages'):
            need(actual[key]==prediction[key],'owned setter differential '+name+'/'+key)
    return expected_receipt()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private setter qualification')
        receipt=qualify()
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Four owned STRB kernels PASS: full16/flow/byte preimage and all pages')


if __name__=='__main__':main()
