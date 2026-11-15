#!/usr/bin/env python3
"""Qualify seven owned SUBS/branch/high-ADD kernels before the native getter."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
A=load(HERE.parents[1]/'test/arm_thumb_box_oracle.py','owned_box_arithmetic')
T=load(HERE.with_name('qualifica_maxpp_aritmetica.py'),'box_owned_fixture_helper')
need=A.need


def owned_cases():
    specs=(('SUBS-zero-imm0',0x3800,{0:0},0x9000003f,{0:0,15:0x6000003f}),
           ('SUBS-borrow',0x3801,{0:0},0x7000003f,{0:0xffffffff,15:0x8000003f}),
           ('SUBS-signed-overflow',0x3801,{0:0x80000000},0x6000003f,{0:0x7fffffff,15:0x3000003f}),
           ('SUBS-rd7-imm255',0x3fff,{7:255},0x9000003f,{7:0,15:0x6000003f}))
    rows=[]
    for name,word,values,flags,updates in specs:
        f,code,spans,stop=T.thumb_kernel([word],values,flags)
        returned=list(f['entry_regs'])
        for i,value in updates.items():returned[i]=value
        flow=[dict(pc=0x1000,regs=f['entry_regs']),dict(pc=0x1002,regs=returned)]
        rows.append((name,f,code,spans,stop,returned,flow))
    f,code,spans,stop=T.thumb_kernel([0xe001,0x4770,0x2000,0xe7fc],{},0xb000003f)
    returned=list(f['entry_regs']);flow=[dict(pc=a,regs=returned)for a in(0x1000,0x1006,0x1002)]
    rows.append(('B-forward-backward',f,code,spans,stop,returned,flow))
    f,code,spans,stop=T.thumb_kernel([0x4478],{0:124},0xb000003f)
    returned=list(f['entry_regs']);returned[0]=0x1080
    rows.append(('ADD-r0-PC',f,code,spans,stop,returned,
                 [dict(pc=0x1000,regs=f['entry_regs']),dict(pc=0x1002,regs=returned)]))
    f,code,spans,stop=T.thumb_kernel([0x4487,0x2000],{0:0},0xb000003f)
    returned=list(f['entry_regs'])
    rows.append(('ADD-PC-r0-retains-Thumb',f,code,spans,stop,returned,
                 [dict(pc=0x1000,regs=returned),dict(pc=0x1004,regs=returned)]))
    return rows


def expected_receipt():
    rows=[]
    for name,f,code,spans,stop,returned,flow in owned_cases():
        rows.append(dict(name=name,instructions=len(flow),reads=0,stores=0,full16_every_pc=True,all_pages=True,
            returned=returned,flow_sha256=hashlib.sha256(json.dumps(flow,sort_keys=True).encode()).hexdigest()))
    return dict(schema='native-box-ppup-owned-kernels-v1',CPU_model=17,
        scope='Seven owned synthetic kernels; no ROM/Box getter loaded; no ARM946 silicon or timing claim',
        source_sha256={str(p.relative_to(HERE.parents[3])):hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in(HERE,Path(A.__file__),Path(T.__file__),Path(T.K.__file__))},cases=rows)


def qualify():
    for name,f,code,spans,stop,returned,flow in owned_cases():
        prediction=A.run(f,spans,stop,cap=64,thumb_code=code)
        need(prediction['returned']==returned and prediction['flow']==flow,'independent owned Box postcondition '+name)
        need(prediction['pages']==f['pages']and prediction['reads']==prediction['stores']==[],'owned Box no access/write '+name)
        actual=T.K.execute(f,code,spans,stop)
        for key in('flow','reads','stores','returned','stop_pc','pages'):
            need(actual[key]==prediction[key],'owned Box differential '+name+'/'+key)
    return expected_receipt()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private Box qualification')
        receipt=qualify()
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Seven owned SUBS/B/high-ADD kernels PASS: hard full16/flow and all pages')


if __name__=='__main__':main()
