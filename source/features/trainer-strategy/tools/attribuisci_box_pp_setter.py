#!/usr/bin/env python3
"""Prepare/execute/verify original SetBoxMonData(attr58,ValueByte) on owned synthetic inputs.

Three cells: shared encrypted Box input, Value24/23 counterfactual and observer OFF. No private
capture, SDK model, service response, compiler or ROM mutation is needed.
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
B=load(HERE.parents[1]/'test/box_pp_setter_bench.py','box_whole_verifier')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PIN='cb614ad23449d5852b40321dc409c4143872b35c'
REFERENCE={'src/pokemon.c':'1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3',
 'include/pokemon.h':'54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1',
 'include/constants/pokemon.h':'64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74',
 'include/pokemon_types_def.h':'032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d'}


def source_identities():
    found={};seen=set();pending=[B,Q]
    while pending:
        module=pending.pop()
        if id(module)in seen:continue
        seen.add(id(module));path=getattr(module,'__file__',None)
        if not path:continue
        p=Path(path).resolve()
        if SOURCE not in p.parents:continue
        found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
        pending.extend(value for value in vars(module).values()if isinstance(value,types.ModuleType))
    for p in(HERE,):found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
    return dict(sorted(found.items()))


Q=load(HERE.with_name('qualifica_box_pp_setter.py'),'Box_owned_instruction_qualification')


def verify_qualification(path):
    actual=json.loads(path.read_bytes());expected=Q.expected_receipt()
    need(B.wire(actual)==B.wire(expected),'exact completed owned Box instruction qualification/source/full16/flow')
    return dict(file_sha256=R.file_sha(path),source_sha256=expected['source_sha256'],cases=len(expected['cases']))


def prepare(args):
    qualification=verify_qualification(args.qualification)
    receipt,parts=L.prepare(args.rom)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen Box contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned Box source reference')
    for name,digest in REFERENCE.items():need(R.sha((ref/name).read_bytes())==digest,'Box reference drift '+name)
    inputs={name:F.make_input(parts,value)for name,value in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        reference_pin=PIN,reference_files=REFERENCE,original_C_compiler_reconstructed=False,compiler_invoked=False,
        runtime_models=0,retained_CPU_producer_sha256=B.PRODUCER_SHA,owned_instruction_qualification=qualification)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'PP24','PP23','PP24_OFF'},'complete three-cell setter matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='PP24_OFF'),'setter observer cell binding')
        B.require_run(inputs['PP24'if name=='PP24_OFF'else name],raw)
    positive,counter,off=(raws[n]for n in('PP24','PP23','PP24_OFF'))
    for key in('initial','returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(positive[key]==off[key],'setter OFF neutrality '+key)
    first,second=(inputs[n]for n in('PP24','PP23'))
    need(first['entry_regs']==second['entry_regs'],'setter counter identical entry CPU')
    differences=[(base+i,a,b)for base in sorted(first['pages'])for i,(a,b)in enumerate(zip(first['pages'][base],second['pages'][base]))if a!=b]
    need(differences==[(F.VALUE,24,23)],'setter counter only separate Value byte changes')
    def prefix(raw):
        i=next(i for i,x in enumerate(raw['flow'])if x['pc']==0x206f0f6);return raw['flow'][:i+1]
    need(prefix(positive)==prefix(counter),'setter counter identical CPU prefix through Value-load entry')
    need(positive['final_map_sha256']!=counter['final_map_sha256'],'setter counter actual distinct output maps')
    cases=[]
    def altered(name,reason,edit,base=positive,fixture='PP24'):
        raw=copy.deepcopy(base);edit(raw);cases.append((name,inputs[fixture],raw,reason))
    def at(raw,pc):return next(x for x in raw['flow']if x['pc']==pc)['regs']
    altered('return_PP_instead_of_void_residue','source setter full16 void return',lambda x:x['returned'].__setitem__(0,24))
    altered('old_seed63_after_new_key','source setter full16 void return',lambda x:x['returned'].__setitem__(2,0x85732c58))
    altered('entry_LR_instead_of_last_LCG','source setter full16 void return',lambda x:x['returned'].__setitem__(14,F.RETURN|1))
    altered('getter_final_flags_in_setter','source setter full16 void return',lambda x:x['returned'].__setitem__(15,0x3f))
    altered('new_key_not_loaded_from_header','source setter native reads',lambda x:next(v for v in x['reads']if v['pc']==0x206edda).__setitem__('hex','ab02'))
    altered('second_checksum_read_missing','source setter native reads',lambda x:x['reads'].pop(max(i for i,v in enumerate(x['reads'])if v['pc']==0x20725f2)))
    altered('Value_byte_read_missing','source setter native reads',lambda x:x['reads'].pop(next(i for i,v in enumerate(x['reads'])if v['pc']==0x206f0f6)))
    altered('Value_read_from_currentPP','source setter native reads',lambda x:next(v for v in x['reads']if v['pc']==0x206f0f6).__setitem__('address',F.BOX+80))
    altered('PP_store_targets_PPUp','source setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206f0fe).__setitem__('address',F.BOX+84))
    altered('word_width_PP_store','source setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206f0fe).__setitem__('bytes',4))
    altered('untruncated_store_value','source setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206f0fe).__setitem__('value',0x10018))
    altered('PP_store_missing_with_endpoint_intact','source setter native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x206f0fe)))
    altered('old_checksum_stored_in_header','source setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206edd6).__setitem__('value',0x2ab))
    altered('checksum_header_store_missing','source setter native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x206edd6)))
    altered('wrong_checksum_store_preimage','source setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206edd6).__setitem__('before','b402'))
    altered('encrypt_restarts_old_key','source setter native flow',lambda x:[v for v in x['flow']if v['pc']==0x201ff78][64]['regs'].__setitem__(2,0x2ab))
    altered('field_value_shadow','source setter native flow',lambda x:at(x,0x206f0fe).__setitem__(1,23))
    altered('physical_BlockB_fixed_wrong','source setter native flow',lambda x:at(x,0x206f0fe).__setitem__(5,F.BOX+40))
    altered('headerPID_bypassed','source setter native reads',lambda x:x['reads'].pop(next(i for i,v in enumerate(x['reads'])if v['pc']==0x206edf2)))
    altered('transient_attribute_store_missing','source setter native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x206f0fa)))
    altered('first_stack_preimage_forged','source setter native stores',lambda x:x['stores'][0].__setitem__('before','00000000'))
    altered('counter_disguised_as_PP24','source setter full16 void return',lambda x:x.__setitem__('initial',copy.deepcopy(positive['initial'])),counter)
    altered('wrong_instruction_count','source setter counters',lambda x:x.__setitem__('executed_count',3779))
    altered('bool_Value_metadata','complete frozen setter input',lambda x:x['initial'].__setitem__('input_PP',True))
    altered('injected_host_write','zero setter model/runtime host write',lambda x:x['runtime_host_writes'].append(dict(address=F.BOX+6)))
    rejected=[]
    for name,f,raw,reason in cases:
        try:B.require_run(f,raw)
        except ValueError as e:
            need(str(e)==reason,'cause-specific setter forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged setter evidence '+name)
    return dict(OFF_pairs=1,separate_Value_counter_pairs=1,output_checksums=[0x2b4,0x2b3],forgeries=rejected)


def require_completed_report(report,records,bindings,checks):
    need(report['schema']=='native-box-pp-setter-report-v1'and report['mode']=='matrix'and report['CPU_executed']is True and
         report['verdict']=='PASS within encrypted Box136/attribute58/flags0/initialchecksum02AB/PID4000/Value23-24 scope','completed original Box matrix report')
    need(B.wire(report['raw'])==B.wire(records)and B.wire(report['bindings'])==B.wire(bindings)and
         B.wire(report['controls'])==B.wire(checks),'Box original raw hashes/bindings/controls')


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','input-contract','qualification','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists(),'fresh private Box output directory')
        need((a.raw_dir is not None)==(a.mode=='verify'),'raw-dir only and required for verify')
        receipt,inputs,predictions,bindings=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='native-box-pp-setter-prepared-v1',resources=receipt,bindings=bindings,
            predictions={name:dict(instructions=len(x['flow']),reads=len(x['reads']),stores=len(x['stores']),peak=x['native_peak'],checksum=x['checksum'],returned=x['returned'])for name,x in predictions.items()},CPU_executed=False)
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('Full Box setter source/bytes/frozen/math prepared; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in F.MATRIX:
            need(source_identities()==bindings['source_sha256'],'Box source drift before cell')
            if a.mode=='matrix':
                raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw)
            else:raw=json.loads((a.raw_dir/(name+'.json')).read_bytes())
            need(source_identities()==bindings['source_sha256'],'Box source drift after cell')
            raws[name]=raw;B.require_run(inputs[key],raw)
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':
            old=json.loads((a.raw_dir/'prepared.json').read_bytes());need(B.wire(old)==B.wire(prepared),'Box original prepared bindings/predictions')
        checks=controls(raws,inputs)
        if a.mode=='verify':
            old_report=json.loads((a.raw_dir/'report.json').read_bytes())
            require_completed_report(old_report,records,bindings,checks)
        need(source_identities()==bindings['source_sha256'],'Box source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='native-box-pp-setter-report-v1',mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict='PASS within encrypted Box136/attribute58/flags0/initialchecksum02AB/PID4000/Value23-24 scope'))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole native Box '+a.mode+' PASS; three cells, zero models/runtime host writes')


if __name__=='__main__':main()
