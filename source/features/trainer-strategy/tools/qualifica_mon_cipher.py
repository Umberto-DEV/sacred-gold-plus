#!/usr/bin/env python3
"""Qualify eight owned cipher instruction kernels, without native ROM code."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
A=load(HERE.parents[1]/'test/arm_thumb_cipher_oracle.py','owned_cipher_arithmetic')
T=load(HERE.with_name('qualifica_maxpp_aritmetica.py'),'cipher_owned_fixture_helper')
need=A.need


def qualify():
    cases=(
        ('EOR-N-CV',[0x4048],{0:0x80000000,1:1},0x3000003f,{0:0x80000001,15:0xb000003f}),
        ('EOR-Z-CV',[0x4048],{0:42,1:42},0x3000003f,{0:0,15:0x7000003f}),
        ('LDR-scaled-word',[0x68c8],{1:0x3000},0x3000003f,{0:0xcafebabe,15:0x3000003f}),
        ('STR-scaled-word',[0x60c8],{0:0xdeadbeef,1:0x3000},0x3000003f,{0:0xdeadbeef,15:0x3000003f}),
        ('EQ-taken',[0xd000,0x2007],{0:0x1234},0x6000003f,{0:0x1234,15:0x6000003f}),
        ('EQ-skipped',[0xd000,0x2007],{0:0x1234},0x2000003f,{0:7,15:0x2000003f}),
        ('LO-taken',[0xd300,0x2007],{0:0x1234},0x3f,{0:0x1234,15:0x3f}),
        ('LO-skipped',[0xd300,0x2007],{0:0x1234},0x2000003f,{0:7,15:0x2000003f}))
    rows=[]
    for name,words,values,flags,expected in cases:
        f,code,spans,stop=T.thumb_kernel(words,values,flags)
        pages={a:bytearray(b)for a,b in f['pages'].items()};A.A.F.put(pages,0x300c,bytes.fromhex('bebafeca'))
        f['pages']={a:bytes(b)for a,b in pages.items()}
        prediction=A.run(f,spans,stop,cap=64,thumb_code=code)
        for i,value in expected.items():need(prediction['returned'][i]==value,'owned cipher hard postcondition '+name)
        if name=='STR-scaled-word':need(A.A.F.read(prediction['pages'],0x300c,4)==bytes.fromhex('efbeadde'),'owned scaled store result')
        actual=T.K.execute(f,code,spans,stop)
        for key in('flow','reads','stores','returned','stop_pc','pages'):need(actual[key]==prediction[key],'owned cipher differential '+name+'/'+key)
        rows.append(dict(name=name,instructions=len(actual['flow']),reads=len(actual['reads']),stores=len(actual['stores']),
            full16_every_pc=True,all_pages=True,returned=actual['returned'],flow_sha256=hashlib.sha256(json.dumps(actual['flow'],sort_keys=True).encode()).hexdigest()))
    return dict(schema='native-mon-cipher-owned-kernels-v1',CPU_model=17,
        scope='Eight owned synthetic kernels, no ROM/cipher/LCG body loaded; no ARM946 timing or hardware claim',
        source_sha256={str(p.relative_to(HERE.parents[3])):hashlib.sha256(p.read_bytes()).hexdigest()for p in(HERE,Path(A.__file__),Path(T.__file__),Path(T.K.__file__))},cases=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents and not out.exists()and not out.is_symlink(),'fresh private cipher qualification')
        receipt=qualify()
        with out.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Eight owned cipher arithmetic kernels PASS: full16, accesses and all pages')


if __name__=='__main__':main()
