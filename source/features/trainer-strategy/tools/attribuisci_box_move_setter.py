#!/usr/bin/env python3
"""Prepare/execute/verify original SetBoxMonData(attr54,ValueU16) on owned synthetic inputs.

Three cells: shared encrypted Box input, move310/311 counterfactual and observer OFF. No private
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
B=load(HERE.parents[1]/'test/box_move_setter_bench.py','box_whole_verifier')
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


Q=load(HERE.with_name('qualifica_box_move_setter.py'),'Box_owned_instruction_qualification')


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
    need(set(raws)=={'Move310','Move311','Move310_OFF'},'complete three-cell move setter matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='Move310_OFF'),'move setter observer cell binding')
        B.require_run(inputs['Move310'if name=='Move310_OFF'else name],raw)
    positive,counter,off=(raws[n]for n in('Move310','Move311','Move310_OFF'))
    for key in('initial','returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(positive[key]==off[key],'move setter OFF neutrality '+key)
    first,second=(inputs[n]for n in('Move310','Move311'))
    need(first['entry_regs']==second['entry_regs'],'move counter identical entry CPU')
    differences=[(base+i,a,b)for base in sorted(first['pages'])for i,(a,b)in enumerate(zip(first['pages'][base],second['pages'][base]))if a!=b]
    need(differences==[(F.VALUE,0x36,0x37)],'move counter only low Value byte changes; high01 remains')
    def prefix(raw):
        i=next(i for i,x in enumerate(raw['flow'])if x['pc']==0x206f0e6);return raw['flow'][:i+1]
    need(prefix(positive)==prefix(counter),'move counter identical CPU prefix through LDRH entry')
    final={x['ram']:bytes.fromhex(x['hex'])for x in positive['final_pages']}
    need(M.read(final,F.BOX,136)==M.read(first['pages'],F.BOX,136),'move310 idempotent complete Box')
    need(positive['final_map_sha256']!=counter['final_map_sha256'],'move counter distinct output maps')
    cases=[]
    def altered(name,reason,edit,base=positive,fixture='Move310'):
        raw=copy.deepcopy(base);edit(raw);cases.append((name,inputs[fixture],raw,reason))
    def at(raw,pc):return next(x for x in raw['flow']if x['pc']==pc)['regs']
    def byte_store(raw):
        x=next(v for v in raw['stores']if v['pc']==0x206f0f0);x.update(bytes=1,before='36',value=0x36)
    altered('return_move_not_void_residue','source move setter full16 void return',lambda x:x['returned'].__setitem__(0,310))
    altered('old_seed63_after_new_key','source move setter full16 void return',lambda x:x['returned'].__setitem__(2,0x85732c58),counter,'Move311')
    altered('entry_LR_instead_last_LCG','source move setter full16 void return',lambda x:x['returned'].__setitem__(14,F.RETURN|1))
    altered('writer_flags_not_final_flags','source move setter full16 void return',lambda x:x['returned'].__setitem__(15,0x4000003f))
    altered('old_header_key_reload','source move setter native reads',lambda x:next(v for v in x['reads']if v['pc']==0x206edda).__setitem__('hex','ab02'),counter,'Move311')
    altered('second_checksum_read_missing','source move setter native reads',lambda x:x['reads'].pop(max(i for i,v in enumerate(x['reads'])if v['pc']==0x20725f2)))
    altered('Value_halfword_read_missing','source move setter native reads',lambda x:x['reads'].pop(next(i for i,v in enumerate(x['reads'])if v['pc']==0x206f0e6)))
    altered('Value_read_width1','source move setter native reads',lambda x:next(v for v in x['reads']if v['pc']==0x206f0e6).update(bytes=1,hex='36'))
    altered('wellformed_STRB_same_idempotent_endpoint','source move setter native stores',byte_store)
    altered('move_store_width4','source move setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206f0f0).__setitem__('bytes',4))
    altered('move_store_targets_PP','source move setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206f0f0).__setitem__('address',F.BOX+80))
    altered('idempotent_move_store_missing','source move setter native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x206f0f0)))
    altered('idempotent_header_store_missing','source move setter native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x206edd6)))
    altered('old_checksum_header_store','source move setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206edd6).__setitem__('value',0x2ab),counter,'Move311')
    altered('move_preimage_forged','source move setter native stores',lambda x:next(v for v in x['stores']if v['pc']==0x206f0f0).__setitem__('before','0f00'))
    altered('first_stack_preimage_forged','source move setter native stores',lambda x:x['stores'][0].__setitem__('before','00000000'))
    altered('writer_SP_legacy_before_ADDSP','source move setter native flow',lambda x:at(x,0x206f0f0).__setitem__(13,R.TOP-120))
    altered('writer_R0_pointer_not_offset','source move setter native flow',lambda x:at(x,0x206f0f0).__setitem__(0,F.BOX+72))
    altered('writer_flags_legacy_PP','source move setter native flow',lambda x:at(x,0x206f0f0).__setitem__(15,0x3f))
    altered('encrypt_restarts_old_key','source move setter native flow',lambda x:[v for v in x['flow']if v['pc']==0x201ff78][64]['regs'].__setitem__(2,0x2ab),counter,'Move311')
    altered('headerPID_bypassed','source move setter native reads',lambda x:x['reads'].pop(next(i for i,v in enumerate(x['reads'])if v['pc']==0x206edf2)))
    altered('transient_normalized_attr_store_missing','source move setter native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x206f0ea)))
    altered('counter_disguised_as_move310','source move setter full16 void return',lambda x:x.__setitem__('initial',copy.deepcopy(positive['initial'])),counter)
    altered('wrong_instruction_count','source move setter counters',lambda x:x.__setitem__('executed_count',3779))
    altered('bool_move_metadata','complete frozen move setter input',lambda x:x['initial'].__setitem__('input_move',True))
    altered('injected_host_write','zero move setter model/runtime host write',lambda x:x['runtime_host_writes'].append(dict(address=F.BOX+72)))
    rejected=[]
    for name,f,raw,reason in cases:
        try:B.require_run(f,raw)
        except ValueError as e:
            need(str(e)==reason,'cause-specific move forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged move setter evidence '+name)
    return dict(OFF_pairs=1,Value_u16_counter_pairs=1,idempotent_move_and_header_stores=2,output_checksums=[0x2ab,0x2ac],forgeries=rejected)


def require_completed_report(report,records,bindings,checks):
    need(report['schema']=='native-box-move-setter-report-v1'and report['mode']=='matrix'and report['CPU_executed']is True and
         report['verdict']=='PASS within encrypted Box136/attribute54/flags0/initialchecksum02AB/PID4000/Value310-311 scope','completed original Box matrix report')
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
        prepared=dict(schema='native-box-move-setter-prepared-v1',resources=receipt,bindings=bindings,
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
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='native-box-move-setter-report-v1',mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict='PASS within encrypted Box136/attribute54/flags0/initialchecksum02AB/PID4000/Value310-311 scope'))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole native Box '+a.mode+' PASS; three cells, zero models/runtime host writes')


if __name__=='__main__':main()
