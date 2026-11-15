#!/usr/bin/env python3
"""Prepare/run/rejudge the first type3 trainer move slot through native callees.

Stops before the first loop branch, not at a function return. Two owned Mon
inputs share the exact record108 and explicit memory archive; no constructor,
phase bridge, service model, ROM mutation or compiler is used.
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
B=load(HERE.parents[1]/'test/trainer_move_prefix_bench.py','whole_type3_prefix_verifier')
D=load(HERE.with_name('attribuisci_box_move_caller.py'),'type3_retained_recipes_and_limits')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
REPORT_SCHEMA='native-trainer-first-move-prefix-report-v1'
VERDICT='PASS within type3 first-slot prefix3A22-to-3A40 before BLT/record31/move310/own Mon PP-Up3-0/memory-archive scope'
TRAINER_REFERENCE={'src/trainer_data.c':'2e5232c4989f6f2752087bf46579e8207b90b2e5abf65f04dac72e2b03496803',
 'include/trainer_data.h':'6498920abbabd2f06ba85ee822b31e6059e604de5044ae2e2d8f332399742f3d'}
verify_qualification=D.verify_qualification


def source_identities():
    found={};seen=set();pending=[B,D]
    while pending:
        module=pending.pop()
        if id(module)in seen:continue
        seen.add(id(module));path=getattr(module,'__file__',None)
        if not path:continue
        p=Path(path).resolve()
        if SOURCE not in p.parents:continue
        found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
        pending.extend(v for v in vars(module).values()if isinstance(v,types.ModuleType))
    for p in(HERE,D.CACHE,L.BAG_TOOL):found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
    return dict(sorted(found.items()))


def source_input_controls(parts):
    cases=[]
    for name,reason in(('fat','first-slot cached FAT/FNT identities'),('fnt','first-slot cached FAT/FNT identities'),('root','first-slot FS root identity')):
        changed=dict(parts);blob=bytearray(changed[name]);blob[-1]^=1;changed[name]=bytes(blob)
        f=F.make_input(changed,3);need(f==F.make_input(f['resource_parts'],3),'canonical-relative cache input control')
        try:B.predict(f)
        except ValueError as e:need(str(e)==reason,'cause-specific cached input control '+name);cases.append(dict(resource=name,reason=str(e)))
        else:raise ValueError('accepted changed cached resource '+name)
    return dict(canonical_relative_inputs=3,source_loop_expected=False,CPU_executed=False,forgeries=cases)


def prepare(args):
    qualification=verify_qualification(args.qualification);receipt,parts=L.prepare(args.rom)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen type3 prefix contract')
    recipes=D.authenticate_recipes(args,parts)
    for name,digest in TRAINER_REFERENCE.items():need(R.file_sha(args.reference/name)==digest,'trainer source dependency '+name)
    cache_controls=source_input_controls(parts)
    inputs={name:F.make_input(parts,ups)for name,ups in F.PROFILES.items()};predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),recipes=recipes,
        trainer_reference_files=TRAINER_REFERENCE,original_C_compiler_reconstructed=False,compiler_invoked=False,runtime_models=0,
        retained_CPU_producer_sha256=B.C.PARENT_SHA,owned_limit_qualification=qualification,source_input_controls=cache_controls,
        entry_context='Explicit owned prefix fixture, not a lossless captured continuation',stop_is_function_return=False)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs,predictions):
    need(set(raws)=={'Up3','Up0','Up3_OFF'},'complete three-cell first-slot prefix matrix')
    for name,raw in raws.items():
        key='Up3'if name=='Up3_OFF'else name
        need(raw['observed']is(name!='Up3_OFF'),'first-slot observer cell binding');B.require_run(inputs[key],raw,predictions[key])
    positive,counter,off=(raws[n]for n in('Up3','Up0','Up3_OFF'))
    for key in('initial','returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(B.wire(positive[key])==B.wire(off[key]),'first-slot OFF neutrality '+key)
    need(inputs['Up3']['entry_regs']==inputs['Up0']['entry_regs'],'first-slot counter same entry CPU')
    need([predictions[n]['causal']['PP']for n in('Up3','Up0')]==[24,15],'first-slot source causal PP results')
    need([predictions[n]['causal']['cursor']for n in('Up3','Up0')]==[F.RECORD+2]*2,'first-slot same cursor advance')
    rejected=[]
    def altered(name,reason,edit,profile='Up3'):
        forged=copy.deepcopy(raws[profile]);edit(forged)
        try:B.require_run(inputs[profile],forged,predictions[profile])
        except ValueError as e:need(str(e)==reason,'cause-specific first-slot forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged first-slot evidence '+name)
    def reg(raw,pc):return next(v for v in raw['flow']if v['pc']==pc)['regs']
    def remove(raw,key,pc):raw[key].pop(next(i for i,v in enumerate(raw[key])if v['pc']==pc))
    def item(raw,key,pc):return next(v for v in raw[key]if v['pc']==pc)
    altered('old_Box_return_R0','source first-slot prefix gate full16',lambda x:x['returned'].__setitem__(0,0xb3a0))
    altered('slot_index_not_advanced','source first-slot prefix gate full16',lambda x:x['returned'].__setitem__(7,0))
    altered('gate_R3_instead_native_BL_return','source first-slot prefix gate full16',lambda x:x['returned'].__setitem__(3,F.RETURN|1))
    altered('old_Box_final_flags','source first-slot prefix gate full16',lambda x:x['returned'].__setitem__(15,0x6000003f))
    altered('IP_cookie_restored','source first-slot prefix gate full16',lambda x:x['returned'].__setitem__(12,inputs['Up3']['entry_regs'][12]))
    altered('record_pointer_type1_frame','source first-slot native reads',lambda x:item(x,'reads',0x2073a22).__setitem__('address',F.SP+0x50))
    altered('record_move_type1_offset6','source first-slot native reads',lambda x:item(x,'reads',0x2073a2c).__setitem__('address',F.RECORD+6))
    altered('record_second_move_offset10','source first-slot native reads',lambda x:item(x,'reads',0x2073a2c).__setitem__('address',F.RECORD+10))
    altered('missing_record_halfword_read','source first-slot native reads',lambda x:remove(x,'reads',0x2073a2c))
    altered('missing_actual_cursor_reload','source first-slot native reads',lambda x:remove(x,'reads',0x2073a28))
    altered('veneer_uses_cipher_literal','source first-slot native reads',lambda x:item(x,'reads',0x20714e8).__setitem__('address',0x20725dc))
    altered('missing_veneer_literal_read','source first-slot native reads',lambda x:remove(x,'reads',0x20714e8))
    altered('cursor_precompleted_firststore_missing','source first-slot native stores',lambda x:remove(x,'stores',0x2073a26))
    altered('cursor_advance_store_missing','source first-slot native stores',lambda x:remove(x,'stores',0x2073a3c))
    altered('cursor_advance_wrong_value','source first-slot native stores',lambda x:item(x,'stores',0x2073a3c).__setitem__('value',F.RECORD+4))
    altered('old_direct_cookie_PPspill_before','source first-slot native stores',lambda x:item(x,'stores',0x207151c).__setitem__('before','03'))
    altered('first_cursor_wrong_preimage','source first-slot native stores',lambda x:item(x,'stores',0x2073a26).__setitem__('before','a5a5a5a5'))
    altered('missing_idempotent_move_writer','source first-slot native stores',lambda x:remove(x,'stores',0x206f0f0))
    altered('missing_idempotent_PPwriter_Up0','source first-slot native stores',lambda x:remove(x,'stores',0x206f0fe),'Up0')
    altered('missing_actual_PPspill','source first-slot native stores',lambda x:remove(x,'stores',0x207151c))
    altered('old_checksum_header_key','source first-slot native stores',lambda x:[v for v in x['stores']if v['pc']==0x206edd6][-1].__setitem__('value',0x2ab))
    altered('missing_native_slot_initialization','source first-slot native flow',lambda x:remove(x,'flow',0x2073a24))
    altered('missing_first_slot_BL','source first-slot native flow',lambda x:remove(x,'flow',0x2073a32))
    altered('missing_veneer_LDR','source first-slot native flow',lambda x:remove(x,'flow',0x20714e8))
    altered('veneer_R3_not_actual_target','source first-slot native flow',lambda x:reg(x,0x20714f0).__setitem__(3,inputs['Up3']['entry_regs'][3]))
    altered('wrong_native_BL_link','source first-slot native flow',lambda x:reg(x,0x20714e8).__setitem__(14,F.RETURN|1))
    altered('old_direct_entry_SP','source first-slot native flow',lambda x:reg(x,0x20714f0).__setitem__(13,F.TOP))
    altered('missing_cursor_add_instruction','source first-slot native flow',lambda x:remove(x,'flow',0x2073a3a))
    altered('missing_final_CMP','source first-slot native flow',lambda x:remove(x,'flow',0x2073a3e))
    altered('MaxPP_argument_fake_zero','source first-slot native flow',lambda x:reg(x,0x207332c).__setitem__(1,0))
    altered('DIV_quotient_faked','source first-slot native flow',lambda x:reg(x,B.A.BASE.DIV_RETURN).__setitem__(0,0))
    altered('missing_actual_PPUp_read','source first-slot native reads',lambda x:remove(x,'reads',0x206e986))
    altered('source_PP15_faked_as1','source first-slot native reads',lambda x:item(x,'reads',0x2073390).__setitem__('hex','01'))
    altered('host_Value_pointer','source first-slot native flow',lambda x:reg(x,0x2071526).__setitem__(2,F.RECORD))
    altered('wrong_metadata_type','complete frozen first-slot prefix input',lambda x:x['initial'].__setitem__('input_Up',True))
    altered('wrong_map_digest','source first-slot final map hash',lambda x:x.__setitem__('final_map_sha256','0'*64))
    altered('tail100_byte_changed','source first-slot all final pages',lambda x:next(p for p in x['final_pages']if p['ram']==F.BOX&~4095).__setitem__('hex',
        next(p for p in x['final_pages']if p['ram']==F.BOX&~4095)['hex'][:272]+'00'+next(p for p in x['final_pages']if p['ram']==F.BOX&~4095)['hex'][274:]))
    altered('host_phase_write','zero first-slot model/runtime host write',lambda x:x['runtime_host_writes'].append(dict(address=F.SP+0x5c)))
    altered('service_model','zero first-slot model/runtime host write',lambda x:x['models'].append('SetMove'))
    altered('child_return_camouflaged_as_stop','native first-slot fault-free stop PC',lambda x:x.__setitem__('stop_pc',0x2073a36))
    altered('endpoint_without_stop_callback','caller observed return-gate callback',lambda x:x.__setitem__('stopped',False))
    altered('fault_with_good_endpoint','native first-slot fault-free stop PC',lambda x:x.__setitem__('fault','interrupted'))
    altered('callback_count_truncated','caller complete native instruction/gate counters',lambda x:x.__setitem__('callback_count',x['executed_count']))
    altered('bool_instruction_count','typed first-slot prefix counters/PC',lambda x:x.__setitem__('executed_count',True))
    forged=copy.deepcopy(counter);forged['initial']=copy.deepcopy(positive['initial'])
    try:B.require_run(inputs['Up3'],forged,predictions['Up3'])
    except ValueError as e:need(str(e)=='caller complete native instruction/gate counters','counter camouflage exact first-slot rejection');rejected.append(dict(name='Up0_disguised_as_Up3',reason=str(e)))
    else:raise ValueError('accepted Up0 camouflage')
    return dict(OFF_pairs=1,PPUp_counter_pairs=1,native_PP_results=[24,15],native_cursor=F.RECORD+2,native_slot_index=1,
        prefix_calls=3,stop_is_function_return=False,forgeries=rejected)


def require_completed_report(report,records,bindings,checks):
    need(report['schema']==REPORT_SCHEMA and report['mode']=='matrix'and report['CPU_executed']is True and report['verdict']==VERDICT,'completed original first-slot matrix report')
    need(B.wire(report['raw'])==B.wire(records)and B.wire(report['bindings'])==B.wire(bindings)and B.wire(report['controls'])==B.wire(checks),'first-slot original raw hashes/bindings/controls')


def save(path,value,compact=False):
    with Path(path).open('x')as f:json.dump(value,f,indent=None if compact else 2,separators=(',',':')if compact else None);f.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','objects','recipe-dir','div-recipe','input-contract','qualification','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists()and not out.is_symlink(),'fresh private first-slot output')
        need((a.raw_dir is not None)==(a.mode=='verify'),'raw-dir only and required for verify')
        receipt,inputs,predictions,bindings=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='native-trainer-first-move-prefix-prepared-v1',resources=receipt,bindings=bindings,CPU_executed=False,
            predictions={n:dict(instructions=len(x['flow']),reads=len(x['reads']),stores=len(x['stores']),peak=x['native_peak'],returned=x['returned'],causal=x['causal'])for n,x in predictions.items()})
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('First-slot prefix source/bytes/recipes/owned state prepared; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in F.MATRIX:
            need(source_identities()==bindings['source_sha256'],'first-slot source drift before cell')
            if a.mode=='matrix':raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw,compact=True)
            else:
                path=a.raw_dir/(name+'.json');need(not path.is_symlink(),'regular first-slot raw file');raw=json.loads(path.read_bytes())
            need(source_identities()==bindings['source_sha256'],'first-slot source drift after cell');raws[name]=raw;B.require_run(inputs[key],raw,predictions[key])
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':need(B.wire(json.loads((a.raw_dir/'prepared.json').read_bytes()))==B.wire(prepared),'first-slot original prepared binding')
        checks=controls(raws,inputs,predictions)
        if a.mode=='verify':require_completed_report(json.loads((a.raw_dir/'report.json').read_bytes()),records,bindings,checks)
        need(source_identities()==bindings['source_sha256'],'first-slot source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema=REPORT_SCHEMA,mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict=VERDICT))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('First-slot prefix '+a.mode+' PASS; stops before branch, three cells, no models/runtime host writes')


if __name__=='__main__':main()
