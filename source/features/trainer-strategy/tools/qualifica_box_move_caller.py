#!/usr/bin/env python3
"""Qualify local caller limits using owned programs, never ROM instructions.

The uninterrupted CPU body is the new fixed-cap producer. Long loops, the
retained DIV router and the final fetch gate have independent postconditions.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();TEST=HERE.parents[1]/'test'
A=load(TEST/'arm_thumb_box_caller_oracle.py','owned_caller_limit_source')
C=load(TEST/'box_move_caller_cpu.py','owned_caller_limit_CPU')
need=A.need;M=C.P.M


def wire(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def digest(value):return hashlib.sha256(wire(value).encode()).hexdigest()


def loop_kernel(iterations,extra=False):
    code={0x1000:struct.pack('<H',0x3801),0x1002:struct.pack('<H',0xd1fd),0x1004:bytes.fromhex('0021'if extra else'7047')}
    if extra:code[0x1006]=bytes.fromhex('7047')
    pages={0x1000:bytearray(b'\xa5'*4096),0x3000:bytearray(b'\xa5'*4096)}
    for pc,b in code.items():M.put(pages,pc,b)
    regs=[0x10000000+i*0x10101 for i in range(13)]+[0x4000,0x1101,0x6000003f];regs[0]=iterations
    return dict(entry_pc=0x1000,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()}),code,(),0x1100


def arm_kernel():
    entry,stop,sp=0x2073348,0x22f0180,0x23fcffc;pages={}
    def put(a,b):
        for base in range(a&~4095,(a+len(b)+4095)&~4095,4096):pages.setdefault(base,bytearray(b'\xa5'*4096))
        M.put(pages,a,b)
    base=A.BASE;delta=base.DIV_ENTRY-((entry+4)&~3)
    code={entry:struct.pack('<HH',0xf000|((delta>>12)&0x7ff),0xe800|((delta>>1)&0x7ff)),entry+4:bytes.fromhex('00bd')}
    for a,b in code.items():put(a,b)
    branch=base.DIV_ENTRY+4;word=0xea000000|(((base.DIV_RETURN-(branch+8))>>2)&0xffffff)
    put(base.DIV_ENTRY,struct.pack('<II',0xe2b00000,word));put(base.DIV_RETURN,bytes.fromhex('1eff2fe1'))
    put(sp,struct.pack('<I',stop|1));put(stop,b'\0'*4)
    regs=[0x10000000+i*0x10101 for i in range(13)]+[sp,stop|1,0x6000003f];regs[:2]=[900,100]
    f=dict(entry_pc=entry,entry_regs=regs,pages={a:bytes(b)for a,b in pages.items()})
    return f,code,((base.DIV_ENTRY,8),(base.DIV_RETURN,4)),stop


def execute(kernel,predicted,observe):
    f,code,spans,stop=kernel
    specs={str(pc):(pc,len(b),1,'owned')for pc,b in code.items()}
    reader=types.SimpleNamespace(THUMB=specs,thumb_code=lambda parts:{int(n):b for n,b in parts.items()})
    fixture=types.SimpleNamespace(ENTRY=f['entry_pc'],RETURN=stop,
        input_record=lambda x:dict(entry_pc=x['entry_pc'],entry_regs=x['entry_regs'],initial_map_sha256=M.map_digest(x['pages'])))
    run=C.bind(fixture=fixture,reader=reader,memory=M,stack_top=f['entry_regs'][13],code_spans=spans)
    policy=dict(code_starts=frozenset((x['pc'],bool(x['regs'][15]&32))for x in predicted['flow']),
        read_sites=frozenset((x['pc'],x['address'],x['bytes'])for x in predicted['reads']),
        write_sites=frozenset((x['pc'],x['address'],x['bytes'])for x in predicted['stores']))
    return run(f,policy,observe)


def compare(name,kernel,*,observe=True,gate=True,hard_steps=None,hard_return=None):
    f,code,spans,stop=kernel;before=digest({str(a):b.hex()for a,b in f['pages'].items()})
    p=A.run(f,spans,stop,thumb_code=code)
    need(hard_steps is None or len(p['flow'])==hard_steps,'owned hard instruction count '+name)
    need(hard_return is None or p['returned']==hard_return,'owned hard full16 return '+name)
    if f['entry_pc']==0x1000:
        iterations=f['entry_regs'][0];extra=0x1006 in code;index=0
        r=list(f['entry_regs'])
        for i in range(iterations):
            need(p['flow'][index]==dict(pc=0x1000,regs=list(r)),'owned loop hard full16 SUBS entry '+name);index+=1
            r[0]-=1;r[15]=0x6000003f if r[0]==0 else 0x2000003f
            need(p['flow'][index]==dict(pc=0x1002,regs=list(r)),'owned loop hard full16 BNE entry '+name);index+=1
        if extra:
            need(p['flow'][index]==dict(pc=0x1004,regs=list(r)),'owned loop hard MOVS entry '+name);index+=1;r[1]=0
        need(p['flow'][index]==dict(pc=0x1006 if extra else 0x1004,regs=list(r))and index+1==len(p['flow']),'owned loop hard BX entry '+name)
        need(p['reads']==p['stores']==[]and p['pages']==f['pages'],'owned loop no memory effects '+name)
    raw=execute(kernel,p,observe)
    need(raw['fault']is None and raw['models']==raw['runtime_host_writes']==[],'owned uninterrupted no-model execution '+name)
    need(raw['stopped']is gate and raw['stop_pc']==stop,'owned actual gate '+name)
    need(raw['executed_count']==len(p['flow'])and raw['callback_count']==len(p['flow'])+int(gate),'owned callback counts '+name)
    need(raw['returned']==p['returned']and raw['stack_peak']==p['native_peak'],'owned full16/stack '+name)
    need(raw['read_count']==len(p['reads'])and raw['store_count']==len(p['stores']),'owned access counters '+name)
    need(raw['final_pages']==[dict(ram=a,hex=b.hex())for a,b in sorted(p['pages'].items())]and raw['final_map_sha256']==M.map_digest(p['pages']),'owned all final pages '+name)
    for key in('flow','reads','stores'):need(raw[key]==(p[key]if observe else[]),'owned complete observation '+name+'/'+key)
    need(before==digest({str(a):b.hex()for a,b in f['pages'].items()}),'owned input immutability '+name)
    if gate:C.require_completion(raw,len(p['flow']))
    else:
        try:C.require_completion(raw,len(p['flow']))
        except ValueError:pass
        else:raise ValueError('unobserved boundary accepted')
    return dict(name=name,instructions=len(p['flow']),callbacks=raw['callback_count'],stopped=gate,observed=observe,
        returned=raw['returned'],flow_sha256=digest(p['flow']),final_map_sha256=raw['final_map_sha256'],full16_all_steps=observe,all_pages=True)


def qualify():
    rows=[];f,code,spans,stop=long=loop_kernel(5000)
    expected=list(f['entry_regs']);expected[0]=0
    try:A.P.run(f,spans,stop,thumb_code=code)
    except ValueError as e:need(str(e)=='mixed instruction budget','old outer cap must reject long owned loop')
    else:raise ValueError('old cap unexpectedly widened')
    for observe in(True,False):rows.append(compare('long10001-'+('ON'if observe else'OFF'),long,observe=observe,hard_steps=10001,hard_return=expected))
    need(rows[0]['returned']==rows[1]['returned']and rows[0]['flow_sha256']==rows[1]['flow_sha256']and rows[0]['final_map_sha256']==rows[1]['final_map_sha256'],'long OFF neutrality')
    arm=arm_kernel();expected=list(arm[0]['entry_regs']);expected[0]=901;expected[13]+=4;expected[14]=0x207334d;expected[15]=0x3f
    rows.append(compare('tinyARM-residual32768',arm,hard_steps=5,hard_return=expected))
    # Widening only the outer cap would send a residual >8192 into unchanged ARM.
    try:A.P.run.__globals__['select_arm'](A.BASE.DIV_ENTRY,arm[0]['entry_regs'],arm[2])[0].run(
        dict(entry_pc=A.BASE.DIV_ENTRY,entry_regs=arm[0]['entry_regs'],pages=arm[0]['pages']),
        ((A.BASE.DIV_ENTRY,524),),A.BASE.DIV_RETURN,cap=32767)
    except ValueError as e:need('cap'in str(e),'unchanged ARM primitive still rejects oversized residual')
    else:raise ValueError('old ARM cap unexpectedly widened')
    for extra,gate in((False,True),(True,False)):
        kernel=loop_kernel(16383,extra);expected=list(kernel[0]['entry_regs']);expected[0]=0
        if extra:expected[1]=0
        rows.append(compare('boundary'+str(32767+int(extra)),kernel,observe=False,gate=gate,hard_steps=32767+int(extra),hard_return=expected))
    f,_,_,stop=loop_kernel(1);pages={a:bytearray(b)for a,b in f['pages'].items()};M.put(pages,0x1000,bytes.fromhex('fee7'));f['pages']={a:bytes(b)for a,b in pages.items()};code={0x1000:bytes.fromhex('fee7')}
    try:A.run(f,(),stop,thumb_code=code)
    except ValueError as e:need(str(e)=='mixed instruction budget','owned source infinite loop bounded')
    else:raise ValueError('source loop not bounded')
    stub=dict(flow=[dict(pc=0x1000,regs=f['entry_regs'])],reads=[],stores=[])
    raw=execute((f,code,(),stop),stub,False)
    need(raw['fault']is None and raw['stopped']is False and raw['executed_count']==raw['callback_count']==32768 and raw['stop_pc']==0x1000,'owned CPU loop fixed cap/no synthetic stop')
    need(raw['returned']==f['entry_regs']and raw['final_map_sha256']==M.map_digest(f['pages'])and raw['final_pages']==[dict(ram=a,hex=b.hex())for a,b in sorted(f['pages'].items())]and raw['models']==raw['runtime_host_writes']==[]and raw['read_count']==raw['store_count']==0 and raw['flow']==raw['reads']==raw['stores']==[],'owned caploop full CPU/maps/OFF')
    rows.append(dict(name='infinite-cap-OFF',instructions=32768,callbacks=32768,stopped=False,returned=raw['returned'],all_pages=True))
    paths=(HERE,Path(A.__file__),Path(C.__file__))
    return dict(schema='native-box-move-caller-owned-limits-v1',CPU_model=17,CPU_runs=6,ROM_loaded=False,compiler_invoked=False,
        scope='Owned synthetic code only; no new ISA/ROM corpus; no ARM946 hardware or timing claim',
        source_sha256={str(p.relative_to(HERE.parents[3])):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths},cases=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink(),'fresh owned limit qualification output');result=qualify()
        with a.json.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Six owned CPU runs: long ON/OFF, tiny ARM, two return boundaries, capped loop')


if __name__=='__main__':main()
