#!/usr/bin/env python3
"""Qualify the owned eight-word volatile-slot frame on the retained interpreter.

No new ISA or instruction cap is introduced. This tiny domain check isolates
the compiled caller's PUSH/POP mask and two overwritten saved volatile slots.
It contains no ROM input, compiler invocation or native game API.
"""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3];TEST=HERE.parents[1]/'test'
A=load(TEST/'arm_thumb_mon_reset_oracle.py','owned_C_frame_source')
C=load(TEST/'mon_reset_cpu.py','owned_C_frame_CPU')
Q=load(HERE.with_name('qualifica_box_move_caller.py'),'owned_C_frame_retained_producer_binding')
need,M,digest=Q.need,Q.M,Q.digest
execute=types.FunctionType(Q.execute.__code__,{**Q.execute.__globals__,'C':C},argdefs=Q.execute.__defaults__)
PARENT_SHA='82932767324749607c66d8cf59254aba24ada36a21459c26a53b0f4525c36901'


def kernel():
    words=(0xb5fe,0x0014,0x000e,0x0005,0x2700,0x9701,0x200f,0x9002,0xbdfe)
    code={0x1000+i*2:struct.pack('<H',word)for i,word in enumerate(words)}
    pages={0x1000:bytearray(b'\xa5'*4096),0x3000:bytearray(b'\xa5'*4096)}
    for pc,blob in code.items():M.put(pages,pc,blob)
    regs=[0xa0000000+i*0x10101 for i in range(13)]+[0x4000,0x1101,0x6000003f];regs[:3]=[0x3000,310,0]
    return dict(entry_pc=0x1000,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()}),code,(),0x1100


def hard_forecast(k):
    """Nine scalar full16 entries and fixed ordered accesses, no ISA interpreter."""
    f,code,spans,stop=k;need(k==kernel(),'exact owned frame kernel')
    initial=f['entry_regs'];r=list(initial);flow=[]
    for i in range(9):
        flow.append(dict(pc=0x1000+2*i,regs=list(r)))
        if i==0:r[13]=0x3fe0
        elif i==1:r[4]=0;r[15]=0x6000003f
        elif i==2:r[6]=310;r[15]=0x2000003f
        elif i==3:r[5]=0x3000;r[15]=0x2000003f
        elif i==4:r[7]=0;r[15]=0x6000003f
        elif i==6:r[0]=15;r[15]=0x2000003f
        elif i==8:r[1:8]=[310,0,15,*initial[4:8]];r[13]=0x4000
    saved=[initial[i]for i in(1,2,3,4,5,6,7,14)]
    stores=[dict(pc=0x1000,address=0x3fe0+4*i,bytes=4,before='a5a5a5a5',value=value)for i,value in enumerate(saved)]
    stores.extend((dict(pc=0x100a,address=0x3fe4,bytes=4,before='00000000',value=0),
                   dict(pc=0x100e,address=0x3fe8,bytes=4,before=struct.pack('<I',initial[3]).hex(),value=15)))
    final_saved=list(saved);final_saved[1:3]=[0,15]
    reads=[dict(pc=0x1010,address=0x3fe0+4*i,bytes=4,hex=struct.pack('<I',value).hex())for i,value in enumerate(final_saved)]
    pages={a:bytearray(b)for a,b in f['pages'].items()};M.put(pages,0x3fe0,struct.pack('<8I',*final_saved))
    need(M.read(pages,0x3fd0,16)==b'\xa5'*16,'owned lower stack guard')
    return dict(flow=flow,reads=reads,stores=stores,returned=r,stop_pc=stop,native_peak=32,pages={a:bytes(b)for a,b in pages.items()})


def source_forecast(k):
    need(Q.hashlib.sha256(Path(Q.__file__).read_bytes()).hexdigest()==PARENT_SHA,'retained owned producer binding')
    A.source_identity_guard();C.source_identity_guard()
    f,code,spans,stop=k;p=A.run(f,spans,stop,thumb_code=code)
    need(p==hard_forecast(k),'owned scalar full16/access/preimage/pages forecast')
    return p


def synthetic_raw(p,observe):
    """Pure tests only: explicitly fabricated source-shaped input, no evidence."""
    return copy.deepcopy(dict(fault=None,stopped=True,observed=observe,models=[],runtime_host_writes=[],
        stop_pc=p['stop_pc'],returned=p['returned'],executed_count=9,callback_count=10,
        ARM_count=0,Thumb_count=9,unique_executed_starts=9,read_count=8,store_count=10,stack_peak=32,
        final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(p['pages'].items())],final_map_sha256=M.map_digest(p['pages']),
        flow=p['flow']if observe else[],reads=p['reads']if observe else[],stores=p['stores']if observe else[]))


def check_raw(raw,p,observe):
    need(type(observe)is bool and raw['observed']is observe,'owned frame observer binding')
    C.require_completion(raw,9)
    expected=synthetic_raw(p,observe)
    for key,value in expected.items():need(raw[key]==value,'owned frame exact '+key)
    return dict(observed=observe,instructions=9,callbacks=10,full16_all_steps=observe,reads=8,stores=10,stack_bytes=32,
        returned=raw['returned'],final_map_sha256=raw['final_map_sha256'],all_pages=True,
        flow_sha256=digest(p['flow']),flow_hash_scope='source forecast; native rows compared only when observer ON')


def source_ids():
    seen=set();pending=[A,C,Q];found={str(HERE.relative_to(SOURCE)):Q.hashlib.sha256(HERE.read_bytes()).hexdigest()}
    while pending:
        module=pending.pop()
        if id(module)in seen:continue
        seen.add(id(module));path=getattr(module,'__file__',None)
        if not path:continue
        path=Path(path).resolve()
        if SOURCE not in path.parents:continue
        found[str(path.relative_to(SOURCE))]=Q.hashlib.sha256(path.read_bytes()).hexdigest()
        pending.extend(v for v in vars(module).values()if isinstance(v,types.ModuleType))
    return dict(sorted(found.items()))


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def qualify(out):
    k=kernel();p=source_forecast(k);bindings=source_ids()
    save(out/'source-before-CPU.json',dict(schema='owned-Reset-C-frame-forecast-v1',source_sha256=bindings,
        entry=k[0]['entry_regs'],instructions=9,callbacks=10,reads=8,stores=10,stack_bytes=32,
        flow_sha256=digest(p['flow']),reads_sha256=digest(p['reads']),stores_sha256=digest(p['stores']),
        returned=p['returned'],final_map_sha256=M.map_digest(p['pages']),CPU_executed=False))
    rows=[]
    for observe in(True,False):
        need(source_ids()==bindings,'owned frame source drift before CPU')
        raw=execute(k,p,observe);name='ON'if observe else'OFF'
        save(out/('raw-'+name+'.json'),raw)  # Preserve observations before judging.
        rows.append(check_raw(raw,p,observe))
        need(source_ids()==bindings,'owned frame source drift after CPU')
    need(rows[0]['returned']==rows[1]['returned']and rows[0]['final_map_sha256']==rows[1]['final_map_sha256'],'owned frame OFF neutrality')
    result=dict(schema='owned-Reset-C-frame-qualification-v1',CPU_model=17,CPU_runs=2,ROM_loaded=False,compiler_invoked=False,
        source_sha256=bindings,cases=rows,scope='Owned volatile-slot stack domain only; retained ISA/caps unchanged, not C guest or DS timing evidence')
    save(out/'qualification.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',type=Path,required=True);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not a.out_dir.is_symlink(),'fresh private frame qualification directory')
        out.mkdir(parents=True);qualify(out)
    except(ValueError,OSError,KeyError)as e:p.exit(2,str(e)+'\n')
    print('Two owned9-instruction volatile-slot frame cells PASS; no ROM, compiler or C guest')


if __name__=='__main__':main()
