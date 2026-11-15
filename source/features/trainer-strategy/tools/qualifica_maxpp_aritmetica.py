#!/usr/bin/env python3
"""Qualify finite MaxPP arithmetic and DIV routing with owned programs.

No ROM or native filesystem code is loaded. Independent hard postconditions
and source arithmetic precede uninterrupted CPU17 execution for every kernel.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
A=load(HERE.parents[1]/'test/arm_thumb_maxpp_oracle.py','owned_MaxPP_arithmetic')
K=load(HERE.with_name('qualifica_interworking_narc.py'),'owned_MaxPP_CPU_runner')
need=A.need


def arm_kernel(words,values,cpsr):
    stop=0x1100;pc=0x1000+4*len(words);words=list(words)+[0xea000000|(((stop-(pc+8))>>2)&0xffffff)]
    pages={0x1000:bytearray(b'\xa5'*4096),0x3000:bytearray(b'\xa5'*4096)}
    A.A.F.put(pages,0x1000,struct.pack('<'+'I'*len(words),*words))
    regs=[0x10000000+i*0x10101 for i in range(13)]+[0x4000,0x1101,cpsr]
    for i,v in values.items():regs[i]=v
    return dict(entry_pc=0x1000,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()}),{},((0x1000,4*len(words)),),stop


def thumb_kernel(words,values,cpsr):
    code={0x1000+2*i:struct.pack('<H',word)for i,word in enumerate(words)}
    code[0x1000+2*len(words)]=bytes.fromhex('7047')
    f,_,_,stop=arm_kernel([],{**values},cpsr)
    pages={a:bytearray(b)for a,b in f['pages'].items()}
    for pc,b in code.items():A.A.F.put(pages,pc,b)
    f['pages']={a:bytes(b)for a,b in pages.items()};return f,code,(),stop


def check(name,kernel,expected):
    f,code,spans,stop=kernel
    predicted=A.run(f,spans,stop,cap=64,thumb_code=code)if f['entry_regs'][15]&32 else A.D.run(f,spans,stop,cap=64)
    for index,value in expected.items():need(predicted['returned'][index]==value,'owned independent arithmetic '+name+'/'+str(index))
    actual=K.execute(f,code,spans,stop)
    for key in('flow','reads','stores','returned','stop_pc','pages'):need(actual[key]==predicted[key],'owned MaxPP differential '+name+'/'+key)
    return dict(name=name,instructions=len(actual['flow']),returned=actual['returned'],reads=len(actual['reads']),stores=len(actual['stores']),
        full16_every_pc=True,all_pages=True,flow_sha256=hashlib.sha256(json.dumps(actual['flow'],sort_keys=True).encode()).hexdigest())


def qualify():
    rows=[]
    arm=(
        ('ADC-Cin1-shifter0',[0xe0b10082],{1:1,2:1},0x2000001f,{0:4,15:0x1f}),
        ('ADC-Cin0-shifter1',[0xe0b10082],{1:0,2:0x80000000},0x1f,{0:0,15:0x4000001f}),
        ('ADC-wrap',[0xe2b00000],{0:0xffffffff},0x2000001f,{0:0,15:0x6000001f}),
        ('ADC-signed-overflow',[0xe2b00000],{0:0x7fffffff},0x2000001f,{0:0x80000000,15:0x9000001f}),
        ('RSB-signed-overflow',[0xe2701000],{0:0x80000000},0x1f,{1:0x80000000,15:0x9000001f}),
        ('RSB-borrow',[0xe2701000],{0:1},0x1f,{1:0xffffffff,15:0x8000001f}),
        ('RSB-predicate-false',[0x02701000],{0:1,1:123},0x2000001f,{0:1,1:123,15:0x2000001f}),
        ('ANDS-rotate-chain',[0xe21c3102,0xe21c3001],{12:0},0x1f,{3:0,15:0x6000001f}))
    for name,words,values,cpsr,expected in arm:rows.append(check(name,arm_kernel(words,values,cpsr),expected))
    thumb=(
        ('LSR24',[0x0e04],{0:0xff000000},0x1000003f,{4:255,15:0x1000003f}),
        ('LSR-zero-means32',[0x0804],{0:0x80000000},0x1000003f,{4:0,15:0x7000003f}),
        ('MUL-low32-CV',[0x4360],{0:0xffffffff,4:2},0x3000003f,{0:0xfffffffe,15:0xb000003f}))
    for name,words,values,cpsr,expected in thumb:rows.append(check(name,thumb_kernel(words,values,cpsr),expected))
    # Same final CPU/pages, one additional MOVS for the clamped input4.
    clamp=[0x2903,0xd900,0x2103,0x2014,0x4360,0x4348]
    for ups in(3,4):rows.append(check('BLS-clamp-'+str(ups),thumb_kernel(clamp,{1:ups,4:15},0x6000003f),{0:900,1:3,15:0x2000003f}))
    need(rows[-2]['returned']==rows[-1]['returned']and rows[-1]['instructions']==rows[-2]['instructions']+1,'owned clamp convergence and distinct source step')
    # Explicit sixth boundary through the effective router, using a tiny
    # synthetic ARM body at its permitted entry and no native DIV instructions.
    entry,stop,sp=0x2073348,0x22f0180,0x23fcffc;pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        A.A.F.put(pages,a,b)
    delta=A.DIV_ENTRY-((entry+4)&~3)
    code={entry:struct.pack('<HH',0xf000|((delta>>12)&0x7ff),0xe800|((delta>>1)&0x7ff)),entry+4:bytes.fromhex('00bd')}
    for a,b in code.items():put(a,b)
    branch=A.DIV_ENTRY+4;word=0xea000000|(((A.DIV_RETURN-(branch+8))>>2)&0xffffff)
    put(A.DIV_ENTRY,struct.pack('<II',0xe2b00000,word));put(A.DIV_RETURN,bytes.fromhex('1eff2fe1'))
    put(sp,struct.pack('<I',stop|1));put(stop,b'\0'*4)
    regs=[0x10000000+i*0x10101 for i in range(13)]+[sp,stop|1,0x6000003f];regs[:2]=[900,100]
    f=dict(entry_pc=entry,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})
    rows.append(check('sixth-DIV-router-BX',(f,code,((A.DIV_ENTRY,8),(A.DIV_RETURN,4)),stop),{0:901,14:0x207334d,15:0x3f}))
    need(len(rows)==14,'fourteen owned MaxPP kernels')
    paths=(HERE,Path(A.__file__),Path(A.D.__file__),Path(K.__file__))
    return dict(schema='native-MaxPP-owned-arithmetic-v1',CPU_model=17,
        scope='Owned synthetic programs; no ROM/native NARC/SDK/DIV body loaded; no ARM946 silicon/timing claim',
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in paths},cases=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents,'private qualification outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh owned MaxPP receipt')
        receipt=qualify()
        with a.json.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Fourteen owned MaxPP arithmetic/router kernels PASS; full16/read/store/all pages')


if __name__=='__main__':main()
