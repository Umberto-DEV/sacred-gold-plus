#!/usr/bin/env python3
"""Prepare/execute/verify one original BoxMonSetMoveInSlot lifecycle.

Owned PP-Up3/0 inputs and an observer-OFF cell share move310,slot0,heldItem0.
All original callees execute in one CPU context; no phase bridge or compiler.
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
B=load(HERE.parents[1]/'test/box_move_caller_bench.py','caller_whole_verifier')
D=load(HERE.with_name('attribuisci_maxpp_memory.py'),'caller_retained_recipe_verifiers')
S=load(HERE.with_name('attribuisci_box_move_setter.py'),'caller_retained_Box_source_specs')
Q=load(HERE.with_name('qualifica_box_move_caller.py'),'caller_owned_limit_qualification')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
CACHE=HERE.parents[1]/'test/box-caller-limit-qualification.json'
CACHE_SHA='2194ec04baa7483c80a13510aaa46373b9780591068989a2474a0d4caad6d2f7'
REPORT_SCHEMA='native-box-move-caller-report-v1'
VERDICT='PASS within BoxMonSetMoveInSlot encrypted flags0/PID4000/move310/slot0/PP-Up3-0/memory-archive scope'


def source_identities():
    found={};seen=set();pending=[B,D,S,Q]
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


def verify_qualification(path):
    need(R.file_sha(CACHE)==CACHE_SHA,'pinned owned caller qualification cache')
    expected=json.loads(CACHE.read_bytes());actual=json.loads(Path(path).read_bytes())
    need(B.wire(actual)==B.wire(expected),'exact completed owned caller limit qualification')
    for name,digest in expected['source_sha256'].items():need(R.file_sha(SOURCE/name)==digest,'owned caller qualified source drift')
    return dict(file_sha256=R.file_sha(path),source_sha256=expected['source_sha256'],cases=len(expected['cases']))


def authenticate_recipes(args,parts):
    q=D.D.D.D;ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==q.PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned caller SDK/Box source reference')
    deps={**q.SDK_FILES,'src/filesystem.c':D.L.L.L.SOURCE_SHA,'src/move.c':D.L.L.SOURCE_SHA,**D.C.SOURCES,**S.REFERENCE}
    for name,digest in deps.items():need(R.file_sha(ref/name)==digest,'caller reference dependency drift '+name)
    for name,digest in q.RECIPE_FILES.items():need(R.file_sha(SOURCE/name)==digest,'caller retained recipe drift '+name)
    objects=json.loads(args.objects.read_bytes())
    need(type(objects)is dict and set(objects)==set(q.SYMBOLS)and all(type(p)is str for p in objects.values()),'exact caller30SDK ELF paths')
    generic=q.D.D.verify_objects
    proof=types.FunctionType(generic.__code__,{**vars(q.D.D),'L':q.L,'SYMBOLS':q.SYMBOLS})(objects,parts)
    sdk=q.verify_recipe(args.recipe_dir,ref)
    for name in q.C.BODIES:need(proof[name]['object_sha256']==sdk['objects'][name]['object_sha256'],'caller SDK ELF/source receipt '+name)
    div,obj=D.verify_div_recipe(args.div_recipe,ref)
    need(parts['signed_div']==D.C.read_object(args.div_recipe/'s32_div.o')[0],'caller installed DIV/reconstructed ELF readback')
    return dict(source_pin=q.PIN,reference_files=deps,ELF=proof,division_ELF=obj,
        objects_sha256=R.file_sha(args.objects),SDK_recipe_manifest_sha256=R.file_sha(args.recipe_dir/'manifesto.json'),
        DIV_recipe_manifest_sha256=R.file_sha(args.div_recipe/'manifesto.json'),
        compiler_origin='Retained authenticated LLVM recovered assembly; original MWC/Thumb C objects missing',compiler_invoked=False)


def prepare(args):
    qualification=verify_qualification(args.qualification);receipt,parts=L.prepare(args.rom)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen whole caller contract')
    recipes=authenticate_recipes(args,parts)
    inputs={name:F.make_input(parts,ups)for name,ups in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        recipes=recipes,original_C_compiler_reconstructed=False,compiler_invoked=False,runtime_models=0,
        retained_CPU_producer_sha256=B.C.PARENT_SHA,owned_limit_qualification=qualification)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs,predictions):
    need(set(raws)=={'Up3','Up0','Up3_OFF'},'complete three-cell caller matrix')
    for name,raw in raws.items():
        key='Up3'if name=='Up3_OFF'else name
        need(raw['observed']is(name!='Up3_OFF'),'caller observer cell binding');B.require_run(inputs[key],raw,predictions[key])
    positive,counter,off=(raws[n]for n in('Up3','Up0','Up3_OFF'))
    for key in('initial','returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(B.wire(positive[key])==B.wire(off[key]),'caller OFF neutrality '+key)
    need(inputs['Up3']['entry_regs']==inputs['Up0']['entry_regs'],'caller counter same CPU entry')
    plain3=F.owned_box(3)[1];plain0=F.owned_box(0)[1]
    need([(i,a,b)for i,(a,b)in enumerate(zip(plain3,plain0))if a!=b]==[(76,3,0)],'caller counter only semantic PP-Up change')
    need([predictions[n]['causal']['PP']for n in('Up3','Up0')]==[24,15],'caller native source causal PP answers')
    # Clone only one raw at a time; every negative control compares the entire
    # native transcript and all mapped pages against the pre-CPU prediction.
    rejected=[]
    def altered(name,reason,edit,profile='Up3'):
        forged=copy.deepcopy(raws[profile]);edit(forged)
        try:B.require_run(inputs[profile],forged,predictions[profile])
        except ValueError as e:
            need(str(e)==reason,'cause-specific caller forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged caller evidence '+name)
    def reg(raw,pc):return next(x for x in raw['flow']if x['pc']==pc)['regs']
    def remove(raw,key,pc):raw[key].pop(next(i for i,x in enumerate(raw[key])if x['pc']==pc))
    altered('void_return_faked_as_PP','source caller full16 void return',lambda x:x['returned'].__setitem__(0,24))
    altered('old_setter_R3_residue','source caller full16 void return',lambda x:x['returned'].__setitem__(3,0x206ede5))
    altered('IP_cookie_restored_after_DIV','source caller full16 void return',lambda x:x['returned'].__setitem__(12,inputs['Up3']['entry_regs'][12]))
    altered('entry_LR_restored','source caller full16 void return',lambda x:x['returned'].__setitem__(14,F.RETURN|1))
    altered('wrong_final_T_bit','source caller full16 void return',lambda x:x['returned'].__setitem__(15,0x6000001f))
    altered('getter_bypassed_constant','source caller native flow',lambda x:reg(x,0x206e986).__setitem__(0,24))
    altered('MaxPP_Up_argument_faked','source caller native flow',lambda x:reg(x,0x207332c).__setitem__(1,0))
    altered('DIV_quotient_faked','source caller native flow',lambda x:reg(x,B.A.BASE.DIV_RETURN).__setitem__(0,0))
    altered('missing_DIV_return','source caller native flow',lambda x:remove(x,'flow',B.A.BASE.DIV_RETURN))
    altered('missing_call_instruction','source caller native flow',lambda x:remove(x,'flow',0x2071516))
    altered('standalone_stack_for_setter','source caller native flow',lambda x:reg(x,0x206ed70).__setitem__(13,R.TOP))
    altered('host_Value_pointer','source caller native flow',lambda x:reg(x,0x2071526).__setitem__(2,0x22f0200))
    altered('missing_PPUp_read','source caller native reads',lambda x:remove(x,'reads',0x206e986))
    altered('wrong_PPUp_read','source caller native reads',lambda x:next(v for v in x['reads']if v['pc']==0x206e986).__setitem__('hex','00'))
    altered('wrong_PP15_read','source caller native reads',lambda x:next(v for v in x['reads']if v['pc']==0x2073390).__setitem__('hex','01'))
    altered('missing_stack_PP_read','source caller native reads',lambda x:remove(x,'reads',0x206f0f6))
    altered('missing_idempotent_move_write','source caller native stores',lambda x:remove(x,'stores',0x206f0f0))
    altered('missing_native_stack_PP_writer','source caller native stores',lambda x:remove(x,'stores',0x207151c))
    altered('missing_final_PP_writer','source caller native stores',lambda x:remove(x,'stores',0x206f0fe))
    altered('missing_idempotent_PP_writer_Up0','source caller native stores',lambda x:remove(x,'stores',0x206f0fe),'Up0')
    altered('caller_stack_byte_wrong_preimage','source caller native stores',lambda x:next(v for v in x['stores']if v['pc']==0x207151c).__setitem__('before','00'))
    altered('final_header_key_disconnected','source caller native stores',lambda x:[v for v in x['stores']if v['pc']==0x206edd6][-1].__setitem__('value',0x2ab))
    altered('wrong_initial_metadata_type','complete frozen caller input',lambda x:x['initial'].__setitem__('input_Up',True))
    altered('synthetic_host_write','zero caller model/runtime host write',lambda x:x['runtime_host_writes'].append(dict(address=F.PP_VALUE)))
    altered('synthetic_service_model','zero caller model/runtime host write',lambda x:x['models'].append('MaxPP'))
    altered('endpoint_without_gate','caller observed return-gate callback',lambda x:x.__setitem__('stopped',False))
    altered('fault_with_good_endpoint','native caller fault-free return PC',lambda x:x.__setitem__('fault','interrupted'))
    altered('truncated_callback_count','caller complete native instruction/gate counters',lambda x:x.__setitem__('callback_count',x['executed_count']))
    altered('read_count_bool','typed caller counters/PC',lambda x:x.__setitem__('read_count',True))
    altered('final_map_digest_forged','source caller final map hash',lambda x:x.__setitem__('final_map_sha256','0'*64))
    altered('unrelated_final_page_byte_forged','source caller all final pages',lambda x:x['final_pages'][0].__setitem__('hex','00'+x['final_pages'][0]['hex'][2:]))
    forged=copy.deepcopy(counter);forged['initial']=copy.deepcopy(positive['initial'])
    try:B.require_run(inputs['Up3'],forged,predictions['Up3'])
    except ValueError as e:
        need(str(e)=='caller complete native instruction/gate counters','Up0 camouflage rejected at exact counter proof')
        rejected.append(dict(name='Up0_disguised_as_Up3',reason=str(e)))
    else:raise ValueError('accepted counter input camouflage')
    return dict(OFF_pairs=1,PPUp_counter_pairs=1,native_results=[24,15],initial_keys=[0x2ab,0x2a8],final_keys=[0x2b4,0x2a8],
        uninterrupted_calls=3,models=0,runtime_host_writes=0,forgeries=rejected)


def require_completed_report(report,records,bindings,checks):
    need(report['schema']==REPORT_SCHEMA and report['mode']=='matrix'and report['CPU_executed']is True and report['verdict']==VERDICT,'completed original caller matrix report')
    need(B.wire(report['raw'])==B.wire(records)and B.wire(report['bindings'])==B.wire(bindings)and B.wire(report['controls'])==B.wire(checks),'caller original raw hashes/bindings/controls')


def save(path,value,compact=False):
    with Path(path).open('x')as f:json.dump(value,f,indent=None if compact else 2,separators=(',',':')if compact else None);f.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','objects','recipe-dir','div-recipe','input-contract','qualification','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private caller output directory')
        need((a.raw_dir is not None)==(a.mode=='verify'),'raw-dir only and required for verify')
        receipt,inputs,predictions,bindings=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='native-box-move-caller-prepared-v1',resources=receipt,bindings=bindings,CPU_executed=False,
            predictions={name:dict(instructions=len(x['flow']),reads=len(x['reads']),stores=len(x['stores']),peak=x['native_peak'],returned=x['returned'],causal=x['causal'])for name,x in predictions.items()})
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('Whole caller source/recipe/bytes/frozen causal forecast prepared; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in F.MATRIX:
            need(source_identities()==bindings['source_sha256'],'caller source drift before cell')
            if a.mode=='matrix':
                raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw,compact=True)
            else:
                path=a.raw_dir/(name+'.json');need(not path.is_symlink(),'regular original caller raw');raw=json.loads(path.read_bytes())
            need(source_identities()==bindings['source_sha256'],'caller source drift after cell')
            raws[name]=raw;B.require_run(inputs[key],raw,predictions[key])
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':need(B.wire(json.loads((a.raw_dir/'prepared.json').read_bytes()))==B.wire(prepared),'caller original prepared binding')
        checks=controls(raws,inputs,predictions)
        if a.mode=='verify':require_completed_report(json.loads((a.raw_dir/'report.json').read_bytes()),records,bindings,checks)
        need(source_identities()==bindings['source_sha256'],'caller source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema=REPORT_SCHEMA,mode=a.mode,CPU_executed=a.mode=='matrix',
            bindings=bindings,raw=records,controls=checks,verdict=VERDICT))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole caller '+a.mode+' PASS; three cells/one context per call, zero models/runtime host writes')


if __name__=='__main__':main()
