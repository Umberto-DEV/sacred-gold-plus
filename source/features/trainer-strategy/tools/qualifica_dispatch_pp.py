#!/usr/bin/env python3
"""Qualify the finite PP dispatch additions using ten owned CPU17 kernels.

No ROM, SDK service, compiler or peripheral is loaded. Source arithmetic and
hard postconditions precede every independent uninterrupted CPU run.
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
A=load(HERE.parents[1]/'test/arm_thumb_pp_oracle.py','owned_pp_arithmetic')
K=load(HERE.with_name('qualifica_interworking_narc.py'),'owned_pp_cpu_runner')
need=A.need


def fixture(code,regs,*,data=None,cpsr=0x6000003f):
    pages={0x1000:bytearray(b'\xa5'*4096),0x3000:bytearray(b'\xa5'*4096)}
    for pc,b in code.items():A.A.F.put(pages,pc,b)
    for a,b in(data or {}).items():A.A.F.put(pages,a,b)
    full=[0x10000000+i*0x10101 for i in range(13)]+[0x4000,0x1101,cpsr]
    for r,value in regs.items():full[r]=value
    return dict(entry_pc=min(code),entry_regs=full,pages={a:bytes(b)for a,b in pages.items()})


def check(label,f,code,value,*,r1=None,flags=None):
    predicted=A.run(f,(),0x1100,cap=64,thumb_code=code)
    need(predicted['returned'][0]==value,'owned PP independent scalar')
    if r1 is not None:need(predicted['returned'][1]==r1,'owned PP independent arithmetic')
    if flags is not None:need(predicted['returned'][15]==flags,'owned PP independent flags')
    actual=K.execute(f,code,(),0x1100)
    for key in('flow','reads','stores','returned','stop_pc','pages'):
        need(actual[key]==predicted[key],'owned PP differential '+key)
    return dict(name=label,instructions=len(actual['flow']),returned=actual['returned'],reads=len(actual['reads']),
        stores=len(actual['stores']),full16_every_pc=True,all_pages=True,
        flow_sha256=hashlib.sha256(json.dumps(actual['flow'],sort_keys=True).encode()).hexdigest())


def qualify():
    rows=[]
    # Register-PC source at1006 reads100A, not1008. Target-PC at100E keeps T.
    words=(0x290b,0xd829,0x1849,0x4479,0x88c9,0x0409,0x1409,0x448f)
    code={0x1000+2*i:struct.pack('<H',word)for i,word in enumerate(words)}
    code.update({0x103c:bytes.fromhex('8079'),0x103e:bytes.fromhex('7047')})
    for pp in(15,1):
        f=fixture(code,{0:0x3000,1:5},data={0x101a:struct.pack('<H',42),0x3006:bytes([pp])})
        rows.append(check('full-owned-dispatch-PP'+str(pp),f,code,pp,r1=42,flags=0x3f))
    for value,word,result,flags in((0x80010000,0x1409,0xffff8001,0x9000003f),
                                   (0x00010000,0x1409,1,0x1000003f),
                                   (0x80000001,0x1009,0xffffffff,0xb000003f)):
        code={0x1000:struct.pack('<H',word),0x1002:bytes.fromhex('7047')}
        f=fixture(code,{0:7,1:value},cpsr=0x1000003f)
        rows.append(check('ASR-'+hex(value)+'-'+hex(word),f,code,7,r1=result,flags=flags))
    for cpsr,take in((0x2000003f,True),(0x6000003f,False),(0x3f,False),(0x8000003f,False)):
        code={0x1000:bytes.fromhex('01d8'),0x1002:bytes.fromhex('0120'),0x1004:bytes.fromhex('7047'),
              0x1006:bytes.fromhex('0220'),0x1008:bytes.fromhex('7047')}
        f=fixture(code,{},cpsr=cpsr)
        rows.append(check('BHI-'+hex(cpsr),f,code,2 if take else 1,flags=cpsr&0x3fffffff))
    code={0x1000:bytes.fromhex('1847')};f=fixture(code,{0:7,3:0x1101,14:0x12345678},cpsr=0xb000003f)
    row=check('BX-r3-tail',f,code,7,flags=0xb000003f)
    need(row['returned'][14]==0x12345678,'owned BX tail does not link');rows.append(row)
    need(len(rows)==10,'ten finite owned PP kernels')
    return dict(schema='native-PP-dispatch-qualification-v1',CPU_model=17,
        scope='Owned programs only; no native NARC/FS activation or ARM946 timing/CP15 claim',
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in(HERE,Path(A.__file__),Path(A.P.__file__),Path(K.__file__))},cases=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        out=a.json.resolve();source=HERE.parents[3]
        need(out!=source and source not in out.parents,'private qualification outside source')
        need(not a.json.exists()and not a.json.is_symlink(),'fresh qualification output')
        receipt=qualify()
        with a.json.open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Ten owned PP dispatch/tail/ASR/BHI kernels PASS, full16/read/store/all pages')


if __name__=='__main__':main()
