#!/usr/bin/env python3
"""Prepare/execute/verify original CalcMonChecksum on owned synthetic inputs.

Five cells: pattern, odd size, overflow, zero and observer OFF. No private
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
B=load(HERE.parents[1]/'test/mon_checksum_bench.py','checksum_whole_verifier')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PIN='cb614ad23449d5852b40321dc409c4143872b35c'
REFERENCE={'src/pokemon.c':'1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3',
 'include/pokemon.h':'54a8f712af315e66776464ed2507e8970270524aa5b16ea8e610762b742ee1a1'}


def source_identities():
    found={};seen=set();pending=[B]
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


def prepare(args):
    receipt,parts=L.prepare(args.rom)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen checksum contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned checksum source reference')
    for name,digest in REFERENCE.items():need(R.sha((ref/name).read_bytes())==digest,'checksum reference drift '+name)
    inputs={name:F.make_input(parts,size,overflow)for name,(size,overflow)in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        reference_pin=PIN,reference_files=REFERENCE,original_C_compiler_reconstructed=False,compiler_invoked=False,
        runtime_models=0,retained_CPU_producer_sha256=B.PRODUCER_SHA)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'Pattern128','Odd129','Overflow128','Zero0','Pattern128_OFF'},'complete five-cell checksum matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='Pattern128_OFF'),'checksum observer cell binding')
        B.require_run(inputs['Pattern128'if name=='Pattern128_OFF'else name],raw)
    positive,odd,overflow,zero,off=(raws[n]for n in('Pattern128','Odd129','Overflow128','Zero0','Pattern128_OFF'))
    for key in('returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(positive[key]==off[key],'checksum OFF neutrality '+key)
    need(positive['initial']==off['initial'],'checksum OFF same complete input')
    need([r['returned'][0]for r in(positive,odd,overflow,zero)]==[0xfc0,0xfc0,0xffc0,0],'native checksum four source results')
    need(positive['initial']['initial_map_sha256']==odd['initial']['initial_map_sha256'],'checksum odd same initial memory')
    need(positive['initial']['entry_regs'][:1]+positive['initial']['entry_regs'][2:]==odd['initial']['entry_regs'][:1]+odd['initial']['entry_regs'][2:],'checksum odd only logical size R1 changes')
    for key in('returned','final_pages','final_map_sha256','reads','stores'):
        need(B.wire(positive[key])==B.wire(odd[key]),'checksum odd exact final/access convergence '+key)
    need(positive['flow']!=odd['flow'],'checksum real odd-size prefix retained')
    def joined(raw):
        i=next(i for i,x in enumerate(raw['flow'])if x['pc']==0x20725f6);return raw['flow'][i:]
    need(joined(positive)==joined(odd),'checksum odd full16 join after first ADDS r2')
    left=next(x for x in positive['flow']if x['pc']==0x20725f0)['regs']
    right=next(x for x in odd['flow']if x['pc']==0x20725f0)['regs']
    need(left[15]^right[15]==0x20000000,'checksum odd true LSRS carry difference')
    need(all(x['pc']!=0x20725f2 for x in zero['reads']),'zero checksum no input read')
    cases=[]
    def altered(name,reason,edit,base=positive,fixture='Pattern128'):
        raw=copy.deepcopy(base);edit(raw);cases.append((name,inputs[fixture],raw,reason))
    altered('byte_sum_instead_of_halfwords','source checksum full16 return ABI',lambda x:x['returned'].__setitem__(0,0x1fc0))
    altered('big_endian_sum','source checksum full16 return ABI',lambda x:x['returned'].__setitem__(0,0xd000))
    altered('overflow32_not_u16','source checksum full16 return ABI',lambda x:x['returned'].__setitem__(0,0x3fffc0),overflow,'Overflow128')
    altered('deferred_truncation_with_final_intact','source checksum native flow',lambda x:[v for v in x['flow']if v['pc']==0x20725fe][1]['regs'].__setitem__(3,0x1fffe),overflow,'Overflow128')
    altered('missing_halfword_read','source checksum native reads',lambda x:x['reads'].pop(0))
    altered('extra_odd_trailing_halfword','source checksum native reads',lambda x:x['reads'].append(dict(pc=0x20725f2,address=F.BUF+128,bytes=2,hex='5ad3')),odd,'Odd129')
    altered('odd_size_camouflage','source checksum native flow',lambda x:x.__setitem__('initial',copy.deepcopy(positive['initial'])),odd)
    altered('last_CMP_flags_instead_of_ADDS','source checksum full16 return ABI',lambda x:x['returned'].__setitem__(15,0x6000003f))
    altered('cipher_LR_in_checksum','source checksum full16 return ABI',lambda x:x['returned'].__setitem__(14,0x201ff59))
    altered('signed_R1_overflow','source checksum full16 return ABI',lambda x:x['returned'].__setitem__(1,-4194304),overflow,'Overflow128')
    altered('zero_input_read','source checksum native reads',lambda x:x['reads'].append(dict(pc=0x20725f2,address=F.BUF,bytes=2,hex='0001')),zero,'Zero0')
    altered('wrong_saved_preimage','source checksum native stores',lambda x:x['stores'][0].__setitem__('before','00000000'))
    altered('readonly_payload_write','source checksum native stores',lambda x:x['stores'].append(dict(pc=0x20725e8,address=F.BUF,bytes=4,before='00010203',value=17)))
    altered('skipped_loop_with_result_intact','source checksum native flow',lambda x:x['flow'].pop(next(i for i,v in enumerate(x['flow'])if v['pc']==0x20725f2)))
    altered('bool_logical_size_metadata','complete frozen checksum input',lambda x:x['initial'].__setitem__('input_size',True))
    altered('wrong_iteration_counter','source checksum counters',lambda x:x.__setitem__('executed_count',528))
    rejected=[]
    for name,f,raw,reason in cases:
        try:B.require_run(f,raw)
        except ValueError as e:
            need(str(e)==reason,'cause-specific checksum forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged checksum evidence '+name)
    return dict(OFF_pairs=1,odd_size_pairs=1,overflow_cases=1,zero_cases=1,odd_full16_join_pc=0x20725f6,
        results=[0xfc0,0xfc0,0xffc0,0],forgeries=rejected)


def require_completed_report(report,records,bindings,checks):
    need(report['schema']=='native-mon-checksum-report-v1'and report['mode']=='matrix'and report['CPU_executed']is True and
         report['verdict']=='PASS within owned129byte/four size-data profiles/native checksum scope','completed original checksum matrix report')
    need(B.wire(report['raw'])==B.wire(records)and B.wire(report['bindings'])==B.wire(bindings)and
         B.wire(report['controls'])==B.wire(checks),'checksum original raw hashes/bindings/controls')


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','input-contract','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists(),'fresh private checksum output directory')
        need((a.raw_dir is not None)==(a.mode=='verify'),'raw-dir only and required for verify')
        receipt,inputs,predictions,bindings=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='native-mon-checksum-prepared-v1',resources=receipt,bindings=bindings,
            predictions={name:dict(instructions=len(x['flow']),reads=len(x['reads']),stores=len(x['stores']),peak=x['native_peak'],checksum=x['checksum'],returned=x['returned'])for name,x in predictions.items()},CPU_executed=False)
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('Checksum source/bytes/frozen/math prepared; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in(('Pattern128','Pattern128',True),('Odd129','Odd129',True),('Overflow128','Overflow128',True),('Zero0','Zero0',True),('Pattern128_OFF','Pattern128',False)):
            need(source_identities()==bindings['source_sha256'],'checksum source drift before cell')
            if a.mode=='matrix':
                raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw)
            else:raw=json.loads((a.raw_dir/(name+'.json')).read_bytes())
            need(source_identities()==bindings['source_sha256'],'checksum source drift after cell')
            raws[name]=raw;B.require_run(inputs[key],raw)
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':
            old=json.loads((a.raw_dir/'prepared.json').read_bytes());need(B.wire(old)==B.wire(prepared),'checksum original prepared bindings/predictions')
        checks=controls(raws,inputs)
        if a.mode=='verify':
            old_report=json.loads((a.raw_dir/'report.json').read_bytes())
            require_completed_report(old_report,records,bindings,checks)
        need(source_identities()==bindings['source_sha256'],'checksum source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='native-mon-checksum-report-v1',mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict='PASS within owned129byte/four size-data profiles/native checksum scope'))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole native checksum '+a.mode+' PASS; five cells, zero models/runtime host writes')


if __name__=='__main__':main()
