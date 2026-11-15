#!/usr/bin/env python3
"""Qualify local64k Reset limits on six owned programs, with no ROM code.

Retained owned kernels and full16 scalar loop formulas are reused unchanged.
Only the bounded predictor/producer bindings change. Earlier caps stay intact.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3];TEST=HERE.parents[1]/'test'
A=load(TEST/'arm_thumb_mon_reset_oracle.py','owned_Reset64k_source')
C=load(TEST/'mon_reset_cpu.py','owned_Reset64k_CPU')
Q=load(HERE.with_name('qualifica_box_move_caller.py'),'retained_owned_limit_kernels')
need,M,digest=Q.need,Q.M,Q.digest
PARENT_SHA='82932767324749607c66d8cf59254aba24ada36a21459c26a53b0f4525c36901'
execute=types.FunctionType(Q.execute.__code__,{**Q.execute.__globals__,'C':C},argdefs=Q.execute.__defaults__)
compare=types.FunctionType(Q.compare.__code__,{**Q.compare.__globals__,'A':A,'C':C,'execute':execute},argdefs=Q.compare.__defaults__)
compare.__kwdefaults__=Q.compare.__kwdefaults__


def source_ids():
    return {str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(HERE,Path(A.__file__),Path(C.__file__),Path(Q.__file__))}


def qualify():
    need(hashlib.sha256(Path(Q.__file__).read_bytes()).hexdigest()==PARENT_SHA,'retained owned limit kernel/formula identity')
    A.source_identity_guard();C.source_identity_guard();rows=[]
    f,code,spans,stop=long=Q.loop_kernel(20000);expected=list(f['entry_regs']);expected[0]=0
    try:A.BASE.run(f,spans,stop,thumb_code=code)
    except ValueError as e:need(str(e)=='mixed instruction budget','unchanged32k rejects owned40001')
    else:raise ValueError('parent32k unexpectedly widened')
    for observe in(True,False):rows.append(compare('long40001-'+('ON'if observe else'OFF'),long,observe=observe,hard_steps=40001,hard_return=expected))
    need(rows[0]['returned']==rows[1]['returned']and rows[0]['flow_sha256']==rows[1]['flow_sha256']and rows[0]['final_map_sha256']==rows[1]['final_map_sha256'],'long owned64k OFF neutrality')
    arm=Q.arm_kernel();expected=list(arm[0]['entry_regs']);expected[0]=901;expected[13]+=4;expected[14]=0x207334d;expected[15]=0x3f
    rows.append(compare('tinyARM-residual65535',arm,hard_steps=5,hard_return=expected))
    base=Q.A.BASE
    primitive=A.run.__globals__['select_arm'](base.DIV_ENTRY,arm[0]['entry_regs'],arm[2])[0]
    try:primitive.run(dict(entry_pc=base.DIV_ENTRY,entry_regs=arm[0]['entry_regs'],pages=arm[0]['pages']),((base.DIV_ENTRY,524),),base.DIV_RETURN,cap=65535)
    except ValueError as e:need('cap'in str(e),'unchanged ARM primitive rejects residual65535')
    else:raise ValueError('old ARM cap unexpectedly widened')
    for extra,gate in((False,True),(True,False)):
        kernel=Q.loop_kernel(32767,extra);expected=list(kernel[0]['entry_regs']);expected[0]=0
        if extra:expected[1]=0
        rows.append(compare('boundary'+str(65535+int(extra)),kernel,observe=False,gate=gate,hard_steps=65535+int(extra),hard_return=expected))
    f,_,_,stop=Q.loop_kernel(1);pages={a:bytearray(b)for a,b in f['pages'].items()};M.put(pages,0x1000,bytes.fromhex('fee7'));f['pages']={a:bytes(b)for a,b in pages.items()};code={0x1000:bytes.fromhex('fee7')}
    try:A.run(f,(),stop,thumb_code=code)
    except ValueError as e:need(str(e)=='mixed instruction budget','owned64k source infinite loop bounded')
    else:raise ValueError('source loop not bounded')
    stub=dict(flow=[dict(pc=0x1000,regs=f['entry_regs'])],reads=[],stores=[]);raw=execute((f,code,(),stop),stub,False)
    need(raw['fault']is None and raw['stopped']is False and raw['executed_count']==raw['callback_count']==65536 and raw['stop_pc']==0x1000,'owned CPU64k loop no synthetic stop')
    need(raw['returned']==f['entry_regs']and raw['final_map_sha256']==M.map_digest(f['pages'])and raw['final_pages']==[dict(ram=a,hex=b.hex())for a,b in sorted(f['pages'].items())]and raw['models']==raw['runtime_host_writes']==[]and raw['read_count']==raw['store_count']==0 and raw['flow']==raw['reads']==raw['stores']==[],'owned64k loop fullCPU/maps/OFF')
    rows.append(dict(name='infinite-cap-OFF',instructions=65536,callbacks=65536,stopped=False,returned=raw['returned'],all_pages=True))
    return dict(schema='native-Mon-Reset-owned-limits-v1',CPU_model=17,CPU_runs=6,ROM_loaded=False,compiler_invoked=False,
        local_cap=65536,unchanged_parent_cap=32768,unchanged_ARM_cap=8192,
        scope='Owned synthetic code only; OFF flow hashes are source forecasts, not native per-instruction observations; no new ISA, ROM or DS timing claim',
        source_sha256=source_ids(),cases=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    try:
        out=a.json.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not out.is_symlink(),'fresh private owned64k qualification')
        result=qualify()
        with out.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
    except(ValueError,OSError)as e:p.exit(2,str(e)+'\n')
    print('Six owned64k limit cells PASS: long ON/OFF, tinyARM,65535/65536 gate, bounded loop; no ROM')


if __name__=='__main__':main()
