#!/usr/bin/env python3
"""Prepare/execute/verify original GetBoxMonData(attr62,NULL) on owned synthetic inputs.

Three cells: encrypted Box PP-Up3, Box-preserving PP-Up1 and observer OFF. No private
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
B=load(HERE.parents[1]/'test/box_ppup_bench.py','box_whole_verifier')
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


Q=load(HERE.with_name('qualifica_box_ppup.py'),'Box_owned_instruction_qualification')


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
    inputs={name:F.make_input(parts,ups)for name,ups in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        reference_pin=PIN,reference_files=REFERENCE,original_C_compiler_reconstructed=False,compiler_invoked=False,
        runtime_models=0,retained_CPU_producer_sha256=B.PRODUCER_SHA,owned_instruction_qualification=qualification)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'PPUp3','PPUp1','PPUp3_OFF'},'complete three-cell Box matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='PPUp3_OFF'),'Box observer cell binding')
        B.require_run(inputs['PPUp3'if name=='PPUp3_OFF'else name],raw)
    positive,counter,off=(raws[n]for n in('PPUp3','PPUp1','PPUp3_OFF'))
    for key in('initial','returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(positive[key]==off[key],'Box OFF neutrality '+key)
    need(positive['returned'][0]==3 and counter['returned'][0]==1 and positive['returned'][1:]==counter['returned'][1:],
         'Box counter only returned R0 changes')
    one,two=(inputs[n]for n in('PPUp3','PPUp1'))
    need(one['entry_regs']==two['entry_regs'],'Box counter identical entry CPU')
    def differences(left,right):
        need(set(left)==set(right),'Box same mapped pages')
        return [(base+i,a,b)for base in sorted(left)for i,(a,b)in enumerate(zip(left[base],right[base]))if a!=b]
    need(differences(one['pages'],two['pages'])==[(F.BOX+10,one['pages'][(F.BOX+10)&~4095][(F.BOX+10)&4095],two['pages'][(F.BOX+10)&~4095][(F.BOX+10)&4095]),
         (F.BOX+84,one['pages'][(F.BOX+84)&~4095][(F.BOX+84)&4095],two['pages'][(F.BOX+84)&~4095][(F.BOX+84)&4095])],
         'Box counter only two ciphertext bytes change')
    need(all(a^b==2 for _,a,b in differences(one['pages'],two['pages'])),'Box checksum-preserving XOR2 pair')
    final=lambda raw:{x['ram']:bytes.fromhex(x['hex'])for x in raw['final_pages']}
    diff=differences(final(positive),final(counter))
    need([a for a,_,_ in diff]==[F.BOX+10,F.BOX+84,R.TOP-52]and diff[-1][1:]==(3,1),
         'Box exact final pair two ciphertext bytes plus dead saved PP-Up')
    cases=[]
    def altered(name,reason,edit,base=positive,fixture='PPUp3'):
        raw=copy.deepcopy(base);edit(raw);cases.append((name,inputs[fixture],raw,reason))
    def at(raw,pc):return next(x for x in raw['flow']if x['pc']==pc)['regs']
    altered('return_currentPP15','source Box full16 return',lambda x:x['returned'].__setitem__(0,15))
    altered('wrong_LR_after_encrypt','source Box full16 return',lambda x:x['returned'].__setitem__(14,F.RETURN|1))
    altered('wrong_final_flags','source Box full16 return',lambda x:x['returned'].__setitem__(15,0x6000003f))
    altered('field_load_R0_instead_of_R4','source Box native flow',lambda x:at(x,0x206e988).__setitem__(4,0))
    altered('normalized_attribute62_not0','source Box native flow',lambda x:at(x,0x206e984).__setitem__(0,62))
    altered('wrong_BlockB_pointer','source Box native flow',lambda x:at(x,0x206e986).__setitem__(6,F.BOX+40))
    altered('headerPID_not_loaded','source Box native reads',lambda x:x['reads'].pop(next(i for i,v in enumerate(x['reads'])if v['pc']==0x206e6ac)))
    altered('field_reads_currentPP','source Box native reads',lambda x:next(v for v in x['reads']if v['pc']==0x206e986).__setitem__('address',F.BOX+80))
    altered('checksum_reads_ciphertext','source Box native reads',lambda x:next(v for v in x['reads']if v['pc']==0x20725f2).__setitem__('hex',M.read(inputs['PPUp3']['pages'],F.BOX+8,2).hex()))
    altered('skip_transient_normalized_store','source Box native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x206e982)))
    altered('wrong_normalized_store_preimage','source Box native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206e982).__setitem__('before','00000000'))
    altered('skip_decrypt_write_final_intact','source Box native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x201ff5e)))
    altered('seed_store_at_parent_TOPminus8','source Box native stores',lambda x:next(v for v in x['stores']if v['pc']==0x201ff84).__setitem__('address',R.TOP-8))
    altered('stack_reset_between_phases','source Box native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206e6a0).__setitem__('before','a5a5a5a5'))
    altered('counter_disguised_as_normal','source Box full16 return',lambda x:x.__setitem__('initial',copy.deepcopy(positive['initial'])),counter)
    altered('wrong_instruction_count','source Box counters',lambda x:x.__setitem__('executed_count',3258))
    altered('bool_counter_metadata','complete frozen Box input',lambda x:x['initial'].__setitem__('input_PPUp',True))
    altered('injected_runtime_host_write','zero Box model/runtime host write',lambda x:x['runtime_host_writes'].append(dict(address=F.BOX+8)))
    rejected=[]
    for name,f,raw,reason in cases:
        try:B.require_run(f,raw)
        except ValueError as e:
            need(str(e)==reason,'cause-specific Box forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged Box evidence '+name)
    return dict(OFF_pairs=1,checksum_preserving_counter_pairs=1,results=[3,1],forgeries=rejected)


def require_completed_report(report,records,bindings,checks):
    need(report['schema']=='native-box-ppup-report-v1'and report['mode']=='matrix'and report['CPU_executed']is True and
         report['verdict']=='PASS within encrypted Box136/attribute62/flags0/checksum02AB/PID4000 scope','completed original Box matrix report')
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
        prepared=dict(schema='native-box-ppup-prepared-v1',resources=receipt,bindings=bindings,
            predictions={name:dict(instructions=len(x['flow']),reads=len(x['reads']),stores=len(x['stores']),peak=x['native_peak'],checksum=x['checksum'],returned=x['returned'])for name,x in predictions.items()},CPU_executed=False)
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('Full Box getter source/bytes/frozen/math prepared; no CPU/compiler');return
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
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='native-box-ppup-report-v1',mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict='PASS within encrypted Box136/attribute62/flags0/checksum02AB/PID4000 scope'))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole native Box '+a.mode+' PASS; three cells, zero models/runtime host writes')


if __name__=='__main__':main()
