#!/usr/bin/env python3
"""Qualify an owned continuous guest dispatch driver with no ROM input.

prepare freezes source-derived expectations; execute runs two owned cells;
verify rejudges saved raw without a CPU or compiler invocation.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
B=load(HERE.parents[1]/'test/shellbell_dispatch_bench.py','owned_dispatch_qualification_bench')
BUILD=B.BUILD
need,sha,save=B.need,BUILD.sha,BUILD.save_new


def identities():
    seen=set();pending=[B,BUILD];found={str(HERE.relative_to(SOURCE)):sha(HERE.read_bytes())}
    while pending:
        module=pending.pop()
        if id(module)in seen:continue
        seen.add(id(module));path=getattr(module,'__file__',None)
        if not path:continue
        path=Path(path).resolve()
        if SOURCE not in path.parents:continue
        found[str(path.relative_to(SOURCE))]=sha(path.read_bytes())
        pending.extend(value for value in vars(module).values()if isinstance(value,types.ModuleType))
    for path in(BUILD.ASM,SOURCE/'features/native-core/tools/carica_text.py',SOURCE/'sgp13/compiler.py'):
        found[str(path.relative_to(SOURCE))]=sha(path.read_bytes())
    return dict(sorted(found.items()))


def authenticate(build):
    build=Path(build).resolve();recipe=json.loads((build/'source-before-compiler.json').read_bytes());receipt=json.loads((build/'compiler-receipt.json').read_bytes())
    need(BUILD.exact(recipe,BUILD.prepare(build)),'current protected source/compiler/recipe identity')
    expected=[recipe['compiler']['path'],*BUILD.FLAGS,'-c',str(BUILD.ASM),'-o',str(build/'dispatch.o')]
    need(BUILD.exact(receipt['argv'],expected)and type(receipt['exit_code'])is int and receipt['exit_code']==0 and type(receipt['driver_invocations'])is int and receipt['driver_invocations']==1 and type(receipt['timeout_s'])is int and receipt['timeout_s']==30 and receipt['log_truncated']is False,'one authenticated owned compiler invocation')
    need(sha((build/'compiler.stdout').read_bytes())==receipt['stdout_sha256']and sha((build/'compiler.stderr').read_bytes())==receipt['stderr_sha256']and not(build/'compiler.stderr').read_bytes(),'compiler log binding')
    need((build/'dispatch.o').stat().st_size<=1024**2,'bounded owned object')
    data=(build/'dispatch.o').read_bytes();text,symbols,readback=BUILD.inspect_object(data)
    need(BUILD.exact(readback,json.loads((build/'readback.json').read_text()))and text==(build/'dispatch.bin').read_bytes(),'exact ELF/readback/text binding')
    return text,dict(object_sha256=sha(data),text_sha256=sha(text),source_sha256=recipe['source_sha256'],readback_sha256=sha((build/'readback.json').read_bytes()))


def prediction(build):
    text,compiled=authenticate(build);k=B.kernel(text);p=B.forecast(k);bindings=identities()
    metadata=dict(schema='owned-ShellBell-dispatch-qualification-v1',compiled=compiled,source_sha256=bindings,entry_pc=k[0]['entry_pc'],entry_regs=k[0]['entry_regs'],initial_map_sha256=B.M.map_digest(k[0]['pages']),
        source_steps=32,callback_count=33,cap=64,source_only_BLX_extension='R3 with odd Thumb target; LR=(pc+2)|1',producer_delta='two literal integer caps reduced65536 to64',
        frame_bytes=16,reads=10,stores=6,flow_sha256=B.Q.digest(p['flow']),reads_sha256=B.Q.digest(p['reads']),stores_sha256=B.Q.digest(p['stores']),returned=p['returned'],final_map_sha256=B.M.map_digest(p['pages']),
        CPU_executed=False,ROM_opened=False,original_game_APIs_executed=False)
    return k,p,metadata


def counterproofs(raw,p):
    changes=[]
    def reject(name,edit):
        altered=copy.deepcopy(raw);edit(altered)
        try:B.check_raw(altered,p,True)
        except ValueError:changes.append(dict(name=name,rejected=True))
        else:raise ValueError('owned raw forgery accepted '+name)
    reject('wrong_BLX_LR',lambda r:r['flow'][12]['regs'].__setitem__(14,r['flow'][12]['regs'][14]^2))
    reject('missing_second_command_store',lambda r:r['stores'].pop())
    reject('wrong_stack_preimage',lambda r:r['stores'][0].__setitem__('before','00000000'))
    reject('wrong_table_read',lambda r:r['reads'][2].__setitem__('address',r['reads'][2]['address']+4))
    reject('missing_return_callback',lambda r:r.__setitem__('callback_count',32))
    reject('same_return_wrong_page',lambda r:r['final_pages'][0].__setitem__('hex','00'+r['final_pages'][0]['hex'][2:]))
    return changes


def run(mode,build,out,raw_dir=None):
    out=Path(out).resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists(),'fresh private qualification output');out.mkdir(parents=True)
    k,p,before=prediction(build);save(out/'source-before-CPU.json',before)
    if mode=='prepare':return before
    rows=[];actual={}
    if mode=='verify':
        need(raw_dir is not None,'saved raw required for verify');raw_dir=Path(raw_dir)
        need(BUILD.exact(json.loads((raw_dir/'source-before-CPU.json').read_text()),before),'frozen owned raw input/source contract')
    for observe in(True,False):
        label='ON'if observe else'OFF';need(identities()==before['source_sha256'],'owned source drift before cell')
        if mode=='execute':
            raw=B.execute(k,p,observe);save(out/('raw-'+label+'.json'),raw)
        else:raw=json.loads((raw_dir/('raw-'+label+'.json')).read_bytes())
        rows.append(B.check_raw(raw,p,observe));actual[label]=raw
        need(identities()==before['source_sha256'],'owned source drift after cell')
    need(BUILD.exact(actual['ON']['returned'],actual['OFF']['returned'])and BUILD.exact(actual['ON']['final_pages'],actual['OFF']['final_pages']),'owned observer ON/OFF endpoint neutrality')
    controls=counterproofs(actual['ON'],p);save(out/'counterproofs.json',controls)
    result=dict(schema='owned-ShellBell-dispatch-qualification-v1',mode=mode,compiled=before['compiled'],source_sha256=before['source_sha256'],rows=rows,
        counterproofs=controls,ROM_opened=False,original_game_APIs_executed=False,compiler_invoked=False,CPU_executed=mode=='execute',
        limits=['Owned code/table/context only','No original BattleContext_Main, game controller, ordinary successful boundary, healing, SAVE or hardware claim','Owned pass does not open the native probe gate'])
    save(out/'qualification.json',result);return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','execute','verify'),required=True)
    p.add_argument('--build-dir',type=Path,required=True);p.add_argument('--out-dir',type=Path,required=True);p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    if (a.mode=='verify')!=(a.raw_dir is not None):p.error('--raw-dir is required only in verify mode')
    try:run(a.mode,a.build_dir,a.out_dir,a.raw_dir)
    except(ValueError,OSError)as e:p.exit(1,str(e)+'\n')
    print('Owned dispatch '+a.mode+' completed; no ROM or original game API.')


if __name__=='__main__':main()
