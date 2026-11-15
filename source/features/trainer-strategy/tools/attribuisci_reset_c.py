#!/usr/bin/env python3
"""Prepare, execute or CPU-free reverify a scoped original-C/LLVM comparison.

Requires the authenticated native Reset baseline produced by attribuisci_mon_reset.
The baseline is rejudged from saved raw; its CPU is never run by this command.
Compilation is a separate explicit command, never an implicit verification step.
"""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import subprocess
import types


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
B=load(HERE.parents[1]/'test/reset_c_bench.py','compiled_Reset_verifier')
E=load(HERE.parents[1]/'test/reset_c_equivalence.py','compiled_Reset_semantic_projection')
N=load(HERE.with_name('attribuisci_mon_reset.py'),'compiled_Reset_native_baseline_verifier')
Q=load(HERE.with_name('qualifica_reset_c_frame.py'),'compiled_Reset_owned_frame_identity')
F,R,M,need=B.F,B.R,B.M,B.need
CACHE=HERE.parents[1]/'test/reset-c-frame-qualification.json'
CACHE_SHA='e97bcf402366e526ac126dd44d3d49654d7756e63068881cc13abba5dedec8c5'
VERDICT='PASS within alternative LLVM ResetC290/ownedMon236/move310/slot0/flags0/PID4000/Up3-or0 semantic scope'


def source_identities():
    seen=set();found={};pending=[B,E,N,Q]
    while pending:
        module=pending.pop()
        if id(module)in seen:continue
        seen.add(id(module));path=getattr(module,'__file__',None)
        if not path:continue
        p=Path(path).resolve()
        if SOURCE not in p.parents:continue
        found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
        pending.extend(v for v in vars(module).values()if isinstance(v,types.ModuleType))
    for p in(HERE,CACHE):found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
    return dict(sorted(found.items()))


def frame_qualification(path):
    need(R.file_sha(CACHE)==CACHE_SHA,'pinned completed owned C frame qualification')
    expected=json.loads(CACHE.read_bytes());actual=json.loads(Path(path).read_bytes())
    need(B.wire(actual)==B.wire(expected),'exact owned C frame qualification receipt')
    need(expected['source_sha256']==Q.source_ids(),'current owned frame transitive source identities')
    return dict(sha256=R.file_sha(path),CPU_runs=2,owned_instructions=18,ROM_loaded=False)


def summaries(predictions):
    return {name:dict(instructions=len(x['flow']),ARM=x['ARM_count'],Thumb=x['Thumb_count'],reads=len(x['reads']),stores=len(x['stores']),
        peak=x['native_peak'],returned=x['returned'],output_Mon_sha256=x['output_Mon_sha256'],causal=x['causal'])for name,x in predictions.items()}


def require_native_controls(report,checks):
    need(B.wire(report.get('controls'))==B.wire(checks),'retained native report controls revalidated')


def authenticate_native_baseline(args):
    native_args=types.SimpleNamespace(**{**vars(args),'input_contract':args.native_input_contract})
    receipt,inputs,predictions,bindings=N.prepare(native_args)
    directory=args.native_raw_dir;prepared=json.loads((directory/'prepared.json').read_bytes())
    expected=dict(schema='native-Mon-Reset-prepared-v1',resources=receipt,bindings=bindings,CPU_executed=False,predictions=summaries(predictions))
    need(B.wire(prepared)==B.wire(expected),'retained native prepared source/input/recipe/forecast bindings')
    report=json.loads((directory/'report.json').read_bytes())
    need(report['schema']=='native-Mon-Reset-report-v1'and report['mode']=='matrix'and report['CPU_executed']is True
         and report['verdict']==N.VERDICT and B.wire(report['bindings'])==B.wire(bindings),'completed retained native report identity')
    records=[];projections={};endpoints={};raws={}
    for name,key,observe in N.F.MATRIX:
        path=directory/(name+'.json');need(path.stat().st_size<=16*1024**2,'bounded retained native raw')
        raw=json.loads(path.read_bytes());need(raw['observed']is observe,'retained native observer cell')
        N.B.require_run(inputs[key],raw,predictions[key]);raws[name]=raw
        records.append(dict(name=name,file=name+'.json',sha256=R.file_sha(path)))
        if observe:projections[name]=E.project(N.B,inputs[key],raw,compiled=False)
        endpoints[name]={k:raw[k]for k in('initial','returned','stop_pc','executed_count','read_count','store_count','final_map_sha256')}
    need(B.wire(records)==B.wire(report['raw']),'retained native raw file hash receipt')
    need(B.wire(endpoints['Up3'])==B.wire(endpoints['Up3_OFF']),'retained native OFF neutrality')
    require_native_controls(report,N.controls(raws,inputs,predictions))
    return projections,dict(prepared_sha256=R.file_sha(directory/'prepared.json'),report_sha256=R.file_sha(directory/'report.json'),
        raw=records,full_native_raw_rejudged=True,native_report_controls_recomputed=True,native_CPU_rerun=False,native_source_sha256=bindings['source_sha256'])


def input_controls(parts):
    def forbidden(*args,**kwargs):raise RuntimeError('SOURCE_LOOP_FORBIDDEN')
    old=B.A.run;rows=[]
    try:
        B.A.run=forbidden
        for name,reason in(('fat','compiled C exact cached tables'),('fnt','compiled C exact cached tables'),('root','compiled C exact FS root')):
            changed=dict(parts);blob=bytearray(changed[name]);blob[-1]^=1;changed[name]=bytes(blob)
            f=F.make_input(changed,3)
            try:B.predict(f)
            except ValueError as e:need(str(e)==reason,'compiled C cache forgery cause');rows.append(dict(resource=name,reason=str(e)))
            else:raise ValueError('accepted compiled C cached-input drift')
    finally:B.A.run=old
    return dict(source_loop_executed=False,CPU_executed=False,forgeries=rows)


def prepare(args):
    qualification=N.verify_qualification(args.qualification);frame=frame_qualification(args.frame_qualification)
    baseline,baseline_binding=authenticate_native_baseline(args)
    receipt,parts=F.prepare(args.rom,args.build_dir,args.reference,args.heartgold_ref)
    contract=F.freeze(receipt,parts);need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(contract),'exact frozen compiled C contract')
    # N.prepare has already authenticated every retained SDK/DIV object recipe.
    negative=input_controls(parts);inputs={name:F.make_input(parts,v)for name,v in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        resources_receipt_sha256=contract['resources_receipt_sha256'],native_baseline=baseline_binding,
        original_C_body_compiled=True,original_MWC_codegen_reconstructed=False,compiler_invoked_by_this_command=False,
        owned_limit_qualification=qualification,owned_frame_qualification=frame,source_input_controls=negative)
    return receipt,inputs,predictions,bindings,baseline


def controls(raws,inputs,predictions,baseline):
    need(set(raws)=={'Up3','Up0','Up3_OFF'},'three compiled C evidence cells')
    projections={}
    for name,key,observe in F.MATRIX:
        raw=raws[name];need(raw['observed']is observe,'compiled C observer cell');B.require_run(inputs[key],raw,predictions[key])
        if observe:projections[name]=E.project(B,inputs[key],raw,compiled=True)
    positive,counter,off=(raws[n]for n in('Up3','Up0','Up3_OFF'))
    for key in('initial','returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(B.wire(positive[key])==B.wire(off[key]),'compiled C OFF neutrality '+key)
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(positive[key])==B.wire(counter[key]),'compiled C convergent endpoint '+key)
    need(positive['ARM_count']==counter['ARM_count']+29 and positive['executed_count']==counter['executed_count']+29,'compiled C first DIV branch difference')
    semantic=E.require_equal(need,B.wire,baseline,projections);rejected=[]
    def altered(name,reason,edit,base=positive,fixture='Up3'):
        raw=copy.deepcopy(base);edit(raw)
        try:B.require_run(inputs[fixture],raw,predictions[fixture])
        except ValueError as e:need(str(e)==reason,'compiled C forgery cause '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged compiled C raw '+name)
    def reg(raw,pc,index=0):return[x['regs']for x in raw['flow']if x['pc']==pc][index]
    def store(raw,pc,index=0):return[x for x in raw['stores']if x['pc']==pc][index]
    def read(raw,pc,index=0):return[x for x in raw['reads']if x['pc']==pc][index]
    def skip_mon(raw):
        end=next(i for i,x in enumerate(raw['flow'])if x['pc']==F.BASE+52)
        start=max(i for i,x in enumerate(raw['flow'][:end])if x['pc']==0x206ec40);del raw['flow'][start:end]
    altered('old_native_schema_relabelled','compiled C raw schema',lambda x:x.__setitem__('schema','native-Mon-Reset-raw-v1'))
    altered('POP_R1_normalized_to_native_zero','compiled C full16 return',lambda x:x['returned'].__setitem__(1,0))
    altered('POP_R3_normalized_to_native_ECCD','compiled C full16 return',lambda x:x['returned'].__setitem__(3,0x206eccd))
    altered('DIV_IP_cookie_restored','compiled C full16 return',lambda x:x['returned'].__setitem__(12,inputs['Up3']['entry_regs'][12]))
    altered('entry_LR_restored','compiled C full16 return',lambda x:x['returned'].__setitem__(14,F.RETURN|1))
    altered('wrong_return_flags','compiled C full16 return',lambda x:x['returned'].__setitem__(15,0x3f))
    altered('zero_idempotent_STR_omitted','compiled C complete native stores',lambda x:x['stores'].remove(store(x,F.BASE+38)))
    altered('zero_preimage_faked_A5','compiled C complete native stores',lambda x:store(x,F.BASE+38).__setitem__('before','a5a5a5a5'))
    altered('PP_preimage_faked_A5','compiled C complete native stores',lambda x:store(x,F.BASE+60).__setitem__('before','a5a5a5a5'))
    altered('PP_word_narrowed','compiled C complete native stores',lambda x:store(x,F.BASE+60).update(bytes=1,before='03'))
    altered('PP_word_value24','compiled C complete native stores',lambda x:store(x,F.BASE+60).__setitem__('value',24))
    altered('zero_word_lowbyte3','compiled C complete native reads',lambda x:read(x,0x206f106).__setitem__('hex','03'))
    altered('PP_consumer_wrong_Value','compiled C complete native reads',lambda x:read(x,0x206f0f6,-1).__setitem__('address',F.PP_VALUE))
    altered('Mon_seed_uses_Box_depth','compiled C complete native stores',lambda x:next(v for v in x['stores']if v['pc']==0x201ff84 and v['address']==R.TOP-56).__setitem__('address',R.TOP-88))
    altered('intermediate_2B1_skipped','compiled C complete native stores',lambda x:store(x,0x206ecbe).__setitem__('value',0x2b4))
    altered('party_passes_omitted','compiled C complete native stores',lambda x:x.__setitem__('stores',[v for v in x['stores']if not(F.BOX+136<=v['address']<F.BOX+236)]))
    altered('old_Reset_fetch_injected','compiled C complete native flow',lambda x:x['flow'][0].__setitem__('pc',0x20714b0))
    altered('first_Box_R7_wrongly_zeroed','compiled C complete native flow',lambda x:reg(x,0x20714f0).__setitem__(7,0))
    altered('second_Max_R3_old_residue','compiled C complete native flow',lambda x:reg(x,0x207332c,1).__setitem__(3,0x206eccd))
    altered('second_Max_Up3','compiled C complete native flow',lambda x:reg(x,0x207332c,1).__setitem__(1,3))
    altered('second_Max_old_flags','compiled C complete native flow',lambda x:reg(x,0x207332c,1).__setitem__(15,0x4000003f))
    altered('second_PP_old_SP','compiled C complete native flow',lambda x:reg(x,0x206f0fe,-1).__setitem__(13,R.TOP-152))
    altered('thunk_literal_read_omitted','compiled C complete native reads',lambda x:x['reads'].remove(read(x,F.BASE)))
    altered('second_PP15_read_omitted','compiled C complete native reads',lambda x:x['reads'].remove(read(x,0x2073390,1)))
    altered('second_callback_first_buffer','compiled C complete native flow',lambda x:reg(x,0x20d7448,13).__setitem__(1,F.DEST1))
    altered('skip_idempotent_Mon62_same_endpoint','compiled C complete native flow',skip_mon,counter,'Up0')
    altered('return_gate_unobserved','caller observed return-gate callback',lambda x:x.__setitem__('stopped',False))
    altered('bool_ARM_count','typed compiled C counts/PC',lambda x:x.__setitem__('ARM_count',False))
    altered('bool_input_Up','compiled C input/backend binding',lambda x:x['initial'].__setitem__('input_Up',True))
    altered('host_model','compiled C return with zero host model/write',lambda x:x['models'].append('PP15'))
    altered('host_Value_write','compiled C return with zero host model/write',lambda x:x['runtime_host_writes'].append(F.ZERO_VALUE))
    altered('OFF_trace_injected','compiled C OFF no trace projections',lambda x:x['flow'].append(copy.deepcopy(positive['flow'][0])),off)
    return dict(OFF_pairs=1,convergent_counter_endpoints=1,first_DIV_extra_steps=29,forgeries=rejected,
        semantic_equivalence=semantic,semantic_projections=projections)


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','heartgold-ref','build-dir','objects','recipe-dir','div-recipe','input-contract','qualification','native-input-contract','native-raw-dir','out-dir'):
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--frame-qualification',type=Path,default=CACHE);p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not a.out_dir.is_symlink(),'fresh private C attribution output')
        need((a.raw_dir is not None)==(a.mode=='verify'),'C raw-dir only and required for verify')
        receipt,inputs,predictions,bindings,baseline=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='compiled-Reset-C-prepared-v1',resources=receipt,bindings=bindings,CPU_executed=False,predictions=summaries(predictions))
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('C source/ELF/native baseline/frozen fixture/forecast ready; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in F.MATRIX:
            need(source_identities()==bindings['source_sha256'],'compiled C source drift before cell')
            if a.mode=='matrix':
                raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw)
            else:
                path=a.raw_dir/(name+'.json');need(path.stat().st_size<=16*1024**2,'bounded compiled C saved raw');raw=json.loads(path.read_bytes())
            need(source_identities()==bindings['source_sha256'],'compiled C source drift after cell')
            B.require_run(inputs[key],raw,predictions[key]);raws[name]=raw
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':need(B.wire(json.loads((a.raw_dir/'prepared.json').read_bytes()))==B.wire(prepared),'compiled C saved prepared binding')
        checks=controls(raws,inputs,predictions,baseline)
        if a.mode=='verify':
            old=json.loads((a.raw_dir/'report.json').read_bytes())
            need(old['schema']=='compiled-Reset-C-report-v1'and old['mode']=='matrix'and old['CPU_executed']is True and old['verdict']==VERDICT,'completed C candidate report')
            need(B.wire(old['raw'])==B.wire(records)and B.wire(old['bindings'])==B.wire(bindings)and B.wire(old['controls'])==B.wire(checks),'compiled C saved raw/bindings/controls')
        need(source_identities()==bindings['source_sha256'],'compiled C source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='compiled-Reset-C-report-v1',mode=a.mode,
            CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict=VERDICT))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Compiled Reset C '+a.mode+' PASS; scoped native equivalence, three C cells, no original Reset CPU rerun')


if __name__=='__main__':main()
