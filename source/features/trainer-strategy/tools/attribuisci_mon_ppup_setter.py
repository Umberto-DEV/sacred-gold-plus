#!/usr/bin/env python3
"""Prepare/execute/reverify full native SetMonData62 on owned encrypted Mon236.

Three cells: Up3 to0, idempotent Up0 to0, and observer OFF. Verify reuses raw
evidence without invoking Unicorn or a compiler; optional ROM readers remain
required. All output directories must be fresh and outside the public source.
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
B=load(HERE.parents[1]/'test/mon_ppup_setter_bench.py','Mon_complete_verifier')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
Q=F.Q
PIN='cb614ad23449d5852b40321dc409c4143872b35c'
REFERENCE={'src/pokemon.c':'1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3',
 'include/pokemon.h':'54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1',
 'include/constants/pokemon.h':'64d5d0cee8001830298ec7175c1863165ffccdf037685a51ea27037273187c74',
 'include/pokemon_types_def.h':'032888003b7a68733dedb83d55decc43cc4202b6ca66b284f62256aacb02e24d'}
VERDICT='PASS within owned Mon236/attribute62/flags0/checksum-valid/PID4000/Up3-or0-to0 scope'


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
        pending.extend(v for v in vars(module).values()if isinstance(v,types.ModuleType))
    found[str(HERE.relative_to(SOURCE))]=R.sha(HERE.read_bytes());return dict(sorted(found.items()))


def verify_qualification(path):
    expected=Q.expected_receipt();actual=json.loads(path.read_bytes())
    need(B.wire(actual)==B.wire(expected),'exact completed owned100 qualification/source/full16/flow')
    return dict(file_sha256=R.file_sha(path),source_sha256=expected['source_sha256'],cases=len(expected['cases']))


def prepare(args):
    qualification=verify_qualification(args.qualification);receipt,parts=L.prepare(args.rom)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen Mon contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned Mon source reference')
    for name,digest in REFERENCE.items():need(R.sha((ref/name).read_bytes())==digest,'Mon reference drift '+name)
    inputs={name:F.make_input(parts,ups)for name,ups in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),reference_pin=PIN,
        reference_files=REFERENCE,original_C_compiler_reconstructed=False,compiler_invoked=False,runtime_models=0,
        retained_CPU_producer_sha256=B.PRODUCER_SHA,owned100_qualification=qualification)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'Up3','Up0','Up3_OFF'},'complete three-cell Mon matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='Up3_OFF'),'Mon observer cell binding')
        B.require_run(inputs['Up3'if name=='Up3_OFF'else name],raw)
    positive,counter,off=(raws[n]for n in('Up3','Up0','Up3_OFF'))
    for key in('initial','returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(positive[key]==off[key],'Mon OFF neutrality '+key)
    for key in('returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(positive[key]==counter[key],'Mon convergent counter endpoint/count '+key)
    need(positive['initial']!=counter['initial']and positive['flow']!=counter['flow']and positive['stores']!=counter['stores'],'Mon counter separated by input/transient evidence')
    rejected=[]
    def altered(name,reason,edit,base=positive,fixture='Up3'):
        raw=copy.deepcopy(base);edit(raw)
        try:B.require_run(inputs[fixture],raw)
        except ValueError as e:
            need(str(e)==reason,'cause-specific Mon forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged Mon evidence '+name)
    def flow(raw,pc):return next(x['regs']for x in raw['flow']if x['pc']==pc)
    def store(raw,pc):return next(x for x in raw['stores']if x['pc']==pc)
    def read(raw,pc):return next(x for x in raw['reads']if x['pc']==pc)
    altered('void_return_PPUp_zero','source Mon full16 void return',lambda x:x['returned'].__setitem__(0,0))
    altered('old_Box_wrapper_return_R3','source Mon full16 void return',lambda x:x['returned'].__setitem__(3,0x206ede5))
    altered('entry_LR_instead_last_LCG','source Mon full16 void return',lambda x:x['returned'].__setitem__(14,F.RETURN|1))
    altered('wrong_final_flags','source Mon full16 void return',lambda x:x['returned'].__setitem__(15,0x3f))
    altered('same_count_counter_disguised_as_positive','source Mon native flow',lambda x:x.__setitem__('initial',copy.deepcopy(positive['initial'])),counter)
    altered('party_roundtrip_both_payload_phases_omitted','source Mon native stores',lambda x:x.__setitem__('stores',[s for s in x['stores']if not(F.BOX+136<=s['address']<F.BOX+236)]))
    altered('party_roundtrip_reads_omitted','source Mon native reads',lambda x:x.__setitem__('reads',[s for s in x['reads']if not(F.BOX+136<=s['address']<F.BOX+236)]))
    altered('party_wrong_checksum_key','source Mon native flow',lambda x:flow(x,0x20725e0).__setitem__(2,0x2ab))
    altered('party_decrypt_preimage_forged','source Mon native stores',lambda x:next(s for s in x['stores']if s['pc']==0x201ff5e).__setitem__('before','0000'))
    altered('party_first_seed_preimage_forged','source Mon native stores',lambda x:store(x,0x201ff84).__setitem__('before','ab020000'))
    altered('party_seed_write_missing','source Mon native stores',lambda x:x['stores'].pop(next(i for i,s in enumerate(x['stores'])if s['pc']==0x201ff84)))
    altered('PPUp_byte_store_missing','source Mon native stores',lambda x:x['stores'].pop(next(i for i,s in enumerate(x['stores'])if s['pc']==0x206f10e)))
    altered('PP_field_instead_PPUp','source Mon native stores',lambda x:store(x,0x206f10e).__setitem__('address',F.BOX+80))
    altered('PPUp_halfword_not_byte','source Mon native stores',lambda x:store(x,0x206f10e).update(bytes=2,before='0300'))
    altered('old_Box_leaf_SP','source Mon native flow',lambda x:flow(x,0x206f10e).__setitem__(13,R.TOP-120))
    altered('Valueword_read_four_bytes','source Mon native reads',lambda x:read(x,0x206f106).update(bytes=4,hex='00000000'))
    altered('new_checksum_reload_oldkey','source Mon native reads',lambda x:read(x,0x206ecc2).__setitem__('hex','ab02'))
    altered('header_store_missing','source Mon native stores',lambda x:x['stores'].pop(next(i for i,s in enumerate(x['stores'])if s['pc']==0x206ecbe)))
    altered('header_store_oldkey','source Mon native stores',lambda x:store(x,0x206ecbe).__setitem__('value',0x2ab))
    altered('extra_callback_count','source Mon counters',lambda x:x.__setitem__('callback_count',5827))
    altered('bool_count','typed Mon counters/PC',lambda x:x.__setitem__('ARM_count',False))
    altered('bool_fixture_Up','complete frozen Mon input',lambda x:x['initial'].__setitem__('input_Up',True))
    altered('injected_runtime_write','zero Mon model/runtime host write',lambda x:x['runtime_host_writes'].append(dict(address=F.BOX+84)))
    altered('OFF_trace_injected','Mon OFF no observation projections',lambda x:x['flow'].append(copy.deepcopy(positive['flow'][0])),off)
    return dict(OFF_pairs=1,convergent_counter_pairs=1,cipher_phases=4,party_payload_stores=100,Box_payload_stores=128,local_seed_stores=228,forgeries=rejected)


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','input-contract','qualification','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(SOURCE not in out.parents and out!=SOURCE and not out.exists()and not a.out_dir.is_symlink(),'fresh private Mon output directory')
        need((a.raw_dir is not None)==(a.mode=='verify'),'raw-dir only and required for verify')
        receipt,inputs,predictions,bindings=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='native-Mon-PPUp-setter-prepared-v1',resources=receipt,bindings=bindings,CPU_executed=False,
            predictions={name:dict(instructions=len(x['flow']),reads=len(x['reads']),stores=len(x['stores']),peak=x['native_peak'],
                checksum=x['checksum'],returned=x['returned'],output_Mon_sha256=x['output_Mon_sha256'],final_frame_sha256=x['final_frame_sha256'])for name,x in predictions.items()})
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('Full Mon62 source/bytes/frozen/math prepared; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in F.MATRIX:
            need(source_identities()==bindings['source_sha256'],'Mon source drift before cell')
            if a.mode=='matrix':
                raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw)
            else:raw=json.loads((a.raw_dir/(name+'.json')).read_bytes())
            need(source_identities()==bindings['source_sha256'],'Mon source drift after cell')
            raws[name]=raw;B.require_run(inputs[key],raw)
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':need(B.wire(json.loads((a.raw_dir/'prepared.json').read_bytes()))==B.wire(prepared),'Mon original prepared bindings/predictions')
        checks=controls(raws,inputs)
        if a.mode=='verify':
            old=json.loads((a.raw_dir/'report.json').read_bytes())
            need(old['schema']=='native-Mon-PPUp-setter-report-v1'and old['mode']=='matrix'and old['CPU_executed']is True and old['verdict']==VERDICT,'completed original Mon report')
            need(B.wire(old['raw'])==B.wire(records)and B.wire(old['bindings'])==B.wire(bindings)and B.wire(old['controls'])==B.wire(checks),'Mon original raw hashes/bindings/controls')
        need(source_identities()==bindings['source_sha256'],'Mon source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='native-Mon-PPUp-setter-report-v1',mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict=VERDICT))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole native Mon '+a.mode+' PASS; three cells, four cipher phases, zero models/runtime host writes')


if __name__=='__main__':main()
