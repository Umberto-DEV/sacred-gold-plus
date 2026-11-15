#!/usr/bin/env python3
"""Qualify six owned ANDS/LDRB-register kernels without original ROM code."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
A=load(HERE.parents[1]/'test/arm_thumb_substruct_oracle.py','owned_substruct_arithmetic')
T=load(HERE.with_name('qualifica_maxpp_aritmetica.py'),'substruct_owned_fixture_helper')
need=A.need


def qualify():
    cases=(
        ('ANDS-N-CV',0x4020,{0:0x80000003,4:0x80000001},0x3000003f,{}, {0:0x80000001,15:0xb000003f}),
        ('ANDS-Z-CV',0x4020,{0:0x80000000,4:1},0x3000003f,{}, {0:0,15:0x7000003f}),
        ('LDRB-unaligned-FF',0x5c30,{6:0x3000,0:3},0xb000003f,{0x3003:255}, {0:255,15:0xb000003f}),
        ('LDRB-destination-base',0x5c40,{0:0x3000,1:15},0x7000003f,{0x300f:128}, {0:128,15:0x7000003f}),
        ('LDRB-all-aliases',0x5c49,{1:0x1801},0x1000003f,{0x3002:254}, {1:254,15:0x1000003f}),
        ('LDRB-address-wrap32',0x5c30,{6:0xffffffff,0:0x3002},0xf000003f,{0x3001:129}, {0:129,15:0xf000003f}))
    rows=[]
    for name,word,values,flags,data,expected in cases:
        f,code,spans,stop=T.thumb_kernel([word],values,flags)
        pages={a:bytearray(b)for a,b in f['pages'].items()}
        for a,value in data.items():A.A.F.put(pages,a,bytes([value]))
        f['pages']={a:bytes(b)for a,b in pages.items()}
        prediction=A.run(f,spans,stop,cap=64,thumb_code=code)
        for i,value in expected.items():need(prediction['returned'][i]==value,'owned substructure hard postcondition '+name)
        actual=T.K.execute(f,code,spans,stop)
        for key in('flow','reads','stores','returned','stop_pc','pages'):need(actual[key]==prediction[key],'owned substructure differential '+name+'/'+key)
        rows.append(dict(name=name,instructions=len(actual['flow']),reads=len(actual['reads']),stores=len(actual['stores']),
            full16_every_pc=True,all_pages=True,returned=actual['returned'],flow_sha256=hashlib.sha256(json.dumps(actual['flow'],sort_keys=True).encode()).hexdigest()))
    return dict(schema='native-mon-substructure-owned-kernels-v1',CPU_model=17,
        scope='Six owned synthetic kernels, no ROM/GetSubstruct/table loaded; no ARM946 timing or silicon claim',
        source_sha256={str(p.relative_to(HERE.parents[3])):hashlib.sha256(p.read_bytes()).hexdigest()for p in(HERE,Path(A.__file__),Path(T.__file__),Path(T.K.__file__))},cases=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private substructure qualification')
        receipt=qualify()
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Six owned ANDS/LDRB kernels PASS: full16, byte access and all pages')


if __name__=='__main__':main()
