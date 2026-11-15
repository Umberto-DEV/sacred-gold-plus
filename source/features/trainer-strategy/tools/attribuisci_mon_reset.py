#!/usr/bin/env python3
"""Prepare/execute/reverify the whole native move/PP-Up Reset on owned inputs.

Three original API cells, no phase bridge or compiler. Verify only rejudges
saved evidence; the optional ndspy/Capstone readers remain required.
"""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import types
import subprocess


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve();SOURCE=HERE.parents[3]
B=load(HERE.parents[1]/'test/mon_reset_bench.py','whole_Reset_verifier')
P=load(HERE.with_name('attribuisci_box_move_caller.py'),'Reset_retained_recipe_authentication')
Q=load(HERE.with_name('qualifica_mon_reset_limits.py'),'Reset_completed_owned_limit_qualification')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
CACHE=HERE.parents[1]/'test/mon-reset-limit-qualification.json'
CACHE_SHA='cf284c16a1ea1e9b53793d4c806476351b0c2e291aa17ad5f89af865ffbda2c4'
VERDICT='PASS within whole Reset/ownedMon236/move310/slot0/flags0/checksum-valid/PID4000/Up3-or0 scope'


def source_identities():
    seen=set();found={};pending=[B,P,Q]
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
    need(R.file_sha(CACHE)==CACHE_SHA,'pinned completed Reset owned64k cache')
    expected=json.loads(CACHE.read_bytes());actual=json.loads(Path(path).read_bytes())
    need(B.wire(expected)==B.wire(actual),'exact completed Reset owned64k qualification')
    for name,digest in expected['source_sha256'].items():need(R.file_sha(SOURCE/name)==digest,'Reset qualified source drift '+name)
    return dict(file_sha256=R.file_sha(path),source_sha256=expected['source_sha256'],cases=6)


def input_controls(parts):
    def forbidden(*args,**kwargs):raise RuntimeError('SOURCE_LOOP_FORBIDDEN')
    old=B.A.run;rows=[]
    try:
        B.A.run=forbidden
        for name,reason in(('fat','Reset exact cached table identities'),('fnt','Reset exact cached table identities'),('root','Reset exact FS root identity')):
            changed=dict(parts);blob=bytearray(changed[name]);blob[-1]^=1;changed[name]=bytes(blob)
            f=F.make_input(changed,3);need(f==F.make_input(f['resource_parts'],3),'canonical-relative Reset mutated input')
            try:B.predict(f)
            except ValueError as e:
                need(str(e)==reason,'Reset input forgery cause '+name);rows.append(dict(resource=name,canonical_relative_parts=True,rejected_before_source_loop=True,reason=str(e)))
            else:raise ValueError('accepted Reset cached-data drift '+name)
    finally:B.A.run=old
    return dict(source_loop_executed=False,CPU_executed=False,forgeries=rows)


def prepare(args):
    qualification=verify_qualification(args.qualification);receipt,parts=L.prepare(args.rom)
    contract=F.freeze(receipt,parts)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(contract),'exact frozen whole Reset contract')
    recipes=P.authenticate_recipes(args,parts);negative_inputs=input_controls(parts)
    inputs={name:F.make_input(parts,ups)for name,ups in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        frozen_EN_resources_receipt_sha256=contract['resources_receipt_sha256'],
        resources_receipt_scope='Fresh EN-only readback used by freeze and prepare; supplemental EN+IT audit is a separate receipt',
        recipes=recipes,original_C_compiler_reconstructed=False,compiler_invoked=False,runtime_models=0,
        retained_CPU_producer_sha256=B.C.PARENT_SHA,local_CPU_producer_sha256=R.file_sha(Path(B.C.__file__)),
        owned_limit_qualification=qualification,source_input_controls=negative_inputs)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs,predictions):
    need(set(raws)=={'Up3','Up0','Up3_OFF'},'complete three-cell Reset matrix')
    for name,raw in raws.items():
        key='Up3'if name=='Up3_OFF'else name
        need(raw['observed']is(name!='Up3_OFF'),'Reset observer cell binding');B.require_run(inputs[key],raw,predictions[key])
    positive,counter,off=(raws[n]for n in('Up3','Up0','Up3_OFF'))
    for key in('initial','returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(B.wire(positive[key])==B.wire(off[key]),'Reset OFF neutrality '+key)
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(positive[key])==B.wire(counter[key]),'Reset convergent endpoint '+key)
    need(positive['executed_count']==counter['executed_count']+29 and positive['ARM_count']==counter['ARM_count']+29,'Reset native first-DIV branch difference')
    rejected=[]
    def altered(name,reason,edit,base=positive,fixture='Up3'):
        raw=copy.deepcopy(base);edit(raw)
        try:B.require_run(inputs[fixture],raw,predictions[fixture])
        except ValueError as e:
            need(str(e)==reason,'cause-specific Reset forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged Reset evidence '+name)
    def reg(raw,pc,index=0):return[v['regs']for v in raw['flow']if v['pc']==pc][index]
    def store(raw,pc,index=0):return[v for v in raw['stores']if v['pc']==pc][index]
    def read(raw,pc,index=0):return[v for v in raw['reads']if v['pc']==pc][index]
    def camouflage(raw):
        raw['initial']=copy.deepcopy(positive['initial'])
        for k in('executed_count','ARM_count','unique_executed_starts','callback_count'):raw[k]=positive[k]
    def skip_first_Mon(raw):
        end=next(i for i,x in enumerate(raw['flow'])if x['pc']==0x20714ce)
        start=max(i for i,x in enumerate(raw['flow'][:end])if x['pc']==0x206ec40)
        del raw['flow'][start:end]
    def second_FILE_A5(raw):
        x=next(v for v in raw['stores'][2784:]if v['address']==F.FILE2+48 and v['bytes']==4);x['before']='a5a5a5a5'
    altered('void_return_faked_PP15','source Reset full16 void return',lambda x:x['returned'].__setitem__(0,15))
    altered('return_R3_faked_STOPodd','source Reset full16 void return',lambda x:x['returned'].__setitem__(3,F.RETURN|1))
    altered('DIV_IP_cookie_restored','source Reset full16 void return',lambda x:x['returned'].__setitem__(12,inputs['Up3']['entry_regs'][12]))
    altered('entry_LR_restored','source Reset full16 void return',lambda x:x['returned'].__setitem__(14,F.RETURN|1))
    altered('wrong_return_flags','source Reset full16 void return',lambda x:x['returned'].__setitem__(15,0x3f))
    altered('counter_camouflage_even_counts_forged','source Reset native flow',camouflage,counter)
    altered('skip_idempotent_Mon62_same_endpoint','source Reset native flow',skip_first_Mon,counter,'Up0')
    altered('party_payload_passes_omitted','source Reset native stores',lambda x:x.__setitem__('stores',[v for v in x['stores']if not(F.BOX+136<=v['address']<F.BOX+236)]))
    altered('Mon_seed_uses_Box_depth','source Reset native stores',lambda x:next(v for v in x['stores']if v['pc']==0x201ff84 and v['address']==R.TOP-48).__setitem__('address',R.TOP-80))
    altered('intermediate_key2B1_skipped','source Reset native stores',lambda x:store(x,0x206ecbe).__setitem__('value',0x2b4))
    altered('zero_word_store_omitted','source Reset native stores',lambda x:x['stores'].remove(store(x,0x20714c2)))
    altered('zero_word_narrowed_to_byte','source Reset native stores',lambda x:store(x,0x20714c2).update(bytes=1,before='a5'))
    altered('zero_word_precompleted_preimage','source Reset native stores',lambda x:store(x,0x20714c2).__setitem__('before','00000000'))
    altered('PP_word_store_omitted','source Reset native stores',lambda x:x['stores'].remove(store(x,0x20714d8)))
    altered('PP_word_value24_after_Reset','source Reset native stores',lambda x:store(x,0x20714d8).__setitem__('value',24))
    altered('PP_word_consumer_uses_Box_spill','source Reset native reads',lambda x:read(x,0x206f0f6,-1).__setitem__('address',F.PP_VALUE))
    altered('PP_word_consumer_reads_four_bytes','source Reset native reads',lambda x:read(x,0x206f0f6,-1).update(bytes=4,hex='0f000000'))
    altered('second_PP_store_old_preimage','source Reset native stores',lambda x:store(x,0x206f0fe,-1).__setitem__('before','0f'))
    altered('Mon58_leaf_uses_Box_SP','source Reset native flow',lambda x:reg(x,0x206f0fe,-1).__setitem__(13,R.TOP-176))
    altered('second_MaxPP_uses_Up3','source Reset native flow',lambda x:reg(x,0x20714d2).__setitem__(1,3))
    altered('second_DIV_return_faked15','source Reset native flow',lambda x:reg(x,B.BOX.A.BASE.DIV_RETURN,1).__setitem__(0,15))
    altered('second_memory_callback_uses_first_buffer','source Reset native flow',lambda x:reg(x,0x20d7448,13).__setitem__(1,F.DEST1))
    altered('second_FILE_preimage_normalized_A5','source Reset native stores',second_FILE_A5)
    altered('second_NARC_callback_omitted','source Reset native flow',lambda x:x['flow'].remove([v for v in x['flow']if v['pc']==0x20d7448][-1]))
    altered('second_PP15_buffer_read_omitted','source Reset native reads',lambda x:x['reads'].remove(read(x,0x2073390,1)))
    altered('Mon62_Valuewrong_lowbyte','source Reset native reads',lambda x:read(x,0x206f106).__setitem__('hex','03'))
    altered('return_gate_not_observed','caller observed return-gate callback',lambda x:x.__setitem__('stopped',False))
    altered('bool_instruction_count','typed Reset counters/PC',lambda x:x.__setitem__('ARM_count',False))
    altered('bool_input_metadata','complete frozen Reset input',lambda x:x['initial'].__setitem__('input_Up',True))
    altered('runtime_model_injected','zero Reset model/runtime host write',lambda x:x['models'].append('constantPP15'))
    altered('runtime_host_write_injected','zero Reset model/runtime host write',lambda x:x['runtime_host_writes'].append(dict(address=F.RESET_PP_VALUE)))
    altered('OFF_trace_injected','Reset OFF no observation projections',lambda x:x['flow'].append(copy.deepcopy(positive['flow'][0])),off)
    return dict(OFF_pairs=1,convergent_counter_endpoints=1,first_DIV_extra_steps=29,child_calls_per_Reset=4,
        cipher_payload_stores=840,local_seed_stores=840,checksum_reads=576,forgeries=rejected)


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','objects','recipe-dir','div-recipe','input-contract','qualification','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not a.out_dir.is_symlink(),'fresh private Reset output directory')
        need((a.raw_dir is not None)==(a.mode=='verify'),'raw-dir only and required for verify')
        receipt,inputs,predictions,bindings=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='native-Mon-Reset-prepared-v1',resources=receipt,bindings=bindings,CPU_executed=False,
            predictions={name:dict(instructions=len(x['flow']),ARM=x['ARM_count'],Thumb=x['Thumb_count'],reads=len(x['reads']),stores=len(x['stores']),
                peak=x['native_peak'],returned=x['returned'],output_Mon_sha256=x['output_Mon_sha256'],causal=x['causal'])for name,x in predictions.items()})
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('Whole Reset source/bytes/frozen/recipes/contextual math prepared; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in F.MATRIX:
            need(source_identities()==bindings['source_sha256'],'Reset source drift before cell')
            if a.mode=='matrix':
                raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw)
            else:raw=json.loads((a.raw_dir/(name+'.json')).read_bytes())
            need(source_identities()==bindings['source_sha256'],'Reset source drift after cell')
            raws[name]=raw;B.require_run(inputs[key],raw,predictions[key])
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':need(B.wire(json.loads((a.raw_dir/'prepared.json').read_bytes()))==B.wire(prepared),'Reset original prepared bindings/predictions')
        checks=controls(raws,inputs,predictions)
        if a.mode=='verify':
            old=json.loads((a.raw_dir/'report.json').read_bytes())
            need(old['schema']=='native-Mon-Reset-report-v1'and old['mode']=='matrix'and old['CPU_executed']is True and old['verdict']==VERDICT,'completed original Reset report')
            need(B.wire(old['raw'])==B.wire(records)and B.wire(old['bindings'])==B.wire(bindings)and B.wire(old['controls'])==B.wire(checks),'Reset original raw hashes/bindings/controls')
        need(source_identities()==bindings['source_sha256'],'Reset source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='native-Mon-Reset-report-v1',mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict=VERDICT))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole native Reset '+a.mode+' PASS; three cells, four child calls per Reset, zero models/runtime host writes')


if __name__=='__main__':main()
