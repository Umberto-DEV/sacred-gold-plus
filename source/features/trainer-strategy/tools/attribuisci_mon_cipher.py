#!/usr/bin/env python3
"""Prepare/execute/verify original MonEncryptSegment on owned synthetic inputs.

Three cells: normal seed, observer OFF and one seed counterfactual. No private
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
B=load(HERE.parents[1]/'test/mon_cipher_bench.py','cipher_whole_verifier')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PIN='cb614ad23449d5852b40321dc409c4143872b35c'
REFERENCE={
 'src/pokemon.c':'1d784ece4650b84e426a437ee20e4a926475fc20ef761e67440d0c0136548fa3',
 'src/math_util.c':'ed76da9a0792494d7b22a029d903db402f5c2cec06212870e0337205be747612',
 'include/math_util.h':'566b25991e94325aea5d19143f559efd67606a32efb2abb48e5457f439960318'}


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
    for p in(HERE,HERE.with_name('qualifica_mon_cipher.py')):found[str(p.relative_to(SOURCE))]=R.sha(p.read_bytes())
    return dict(sorted(found.items()))


def prepare(args):
    receipt,parts=L.prepare(args.rom)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen cipher contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned cipher source reference')
    for name,digest in REFERENCE.items():need(R.sha((ref/name).read_bytes())==digest,'cipher reference drift '+name)
    inputs={name:F.make_input(parts,seed)for name,seed in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        reference_pin=PIN,reference_files=REFERENCE,original_C_compiler_reconstructed=False,compiler_invoked=False,
        runtime_models=0,retained_CPU_producer_sha256=B.PRODUCER_SHA)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'SeedFC0','SeedFC0_OFF','SeedFC1'},'complete three-cell cipher matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='SeedFC0_OFF'),'cipher observer cell binding')
        B.require_run(inputs['SeedFC0'if name=='SeedFC0_OFF'else name],raw)
    positive,off,counter=raws['SeedFC0'],raws['SeedFC0_OFF'],raws['SeedFC1']
    for key in('returned','stop_pc','final_map_sha256','final_pages','executed_count','read_count','store_count'):
        need(positive[key]==off[key],'cipher OFF neutrality '+key)
    need(positive['initial']==off['initial'],'cipher OFF same complete input')
    need(positive['initial']['initial_map_sha256']==counter['initial']['initial_map_sha256'],'cipher seed-only initial memory unchanged')
    need(positive['initial']['entry_regs'][:2]+positive['initial']['entry_regs'][3:]==counter['initial']['entry_regs'][:2]+counter['initial']['entry_regs'][3:],'cipher seed-only entry R2 delta')
    need([x['pc']for x in positive['flow']]==[x['pc']for x in counter['flow']],'cipher seed same instruction route')
    left={x['ram']:bytes.fromhex(x['hex'])for x in positive['final_pages']};right={x['ram']:bytes.fromhex(x['hex'])for x in counter['final_pages']}
    need(left.keys()==right.keys(),'cipher counter same mapped owners')
    delta=sorted(a+i for a in left for i,(x,y)in enumerate(zip(left[a],right[a]))if x!=y)
    need(delta and all(F.BUF<=a<F.BUF+128 or R.TOP-8<=a<R.TOP-4 for a in delta),'cipher seed changes only buffer and local seed')
    cases=[]
    def altered(name,reason,edit,base=positive,fixture='SeedFC0'):
        x=copy.deepcopy(base);edit(x);cases.append((name,inputs[fixture],x,reason))
    def context(raw,pc):return next(x for x in raw['flow']if x['pc']==pc)['regs']
    altered('missing_seed_store','source cipher native stores',lambda x:x['stores'].pop(next(i for i,v in enumerate(x['stores'])if v['pc']==0x201ff84)))
    altered('skipped_XOR_with_output_intact','source cipher native flow',lambda x:context(x,0x201ff5e).__setitem__(0,0x0100))
    altered('key_before_advance','source cipher native flow',lambda x:context(x,0x201ff58).__setitem__(0,0))
    altered('low16_key','source cipher native flow',lambda x:context(x,0x201ff88).__setitem__(0,0x9533))
    altered('wrong_endian_payload_word','source cipher native stores',lambda x:next(v for v in x['stores']if v['pc']==0x201ff5e).__setitem__('value',0x53f2))
    altered('wrong_iteration_count','source cipher counters',lambda x:x.__setitem__('executed_count',1313))
    altered('R2_seed64_instead_of63','source cipher full16 return ABI',lambda x:x['returned'].__setitem__(2,0x40fabc00))
    altered('R3_cookie_instead_of_POP_return','source cipher full16 return ABI',lambda x:x['returned'].__setitem__(3,inputs['SeedFC0']['entry_regs'][3]))
    altered('LR_stop_instead_of_native_BL','source cipher full16 return ABI',lambda x:x['returned'].__setitem__(14,F.RETURN|1))
    altered('global_RNG_write','source cipher native stores',lambda x:x['stores'].append(dict(pc=0x201ff84,address=F.GLOBAL,bytes=4,before='dead c0de'.replace(' ',''),value=17)))
    altered('missing_literal_read','source cipher native reads',lambda x:x['reads'].pop(0))
    altered('wrong_seed_metadata','complete frozen cipher input',lambda x:x['initial'].__setitem__('input_seed',0xfc1))
    altered('seed_counter_camouflage','source cipher full16 return ABI',lambda x:x.__setitem__('initial',copy.deepcopy(positive['initial'])),base=counter)
    rejected=[]
    for name,f,raw,reason in cases:
        try:B.require_run(f,raw)
        except ValueError as e:
            need(str(e)==reason,'cause-specific cipher forgery '+name+': '+str(e));rejected.append(dict(name=name,reason=str(e)))
        else:raise ValueError('accepted forged cipher evidence '+name)
    return dict(OFF_pairs=1,seed_counter_pairs=1,final_different_bytes=len(delta),
        different_byte_owners=['owned buffer128','local stack seed4'],forgeries=rejected)


def require_completed_report(report,records,bindings,checks):
    need(report['schema']=='native-mon-cipher-report-v1'and report['mode']=='matrix'and report['CPU_executed']is True and
         report['verdict']=='PASS within owned128byte/seedFC0-FC1/native cipher scope','completed original cipher matrix report')
    need(B.wire(report['raw'])==B.wire(records)and B.wire(report['bindings'])==B.wire(bindings)and
         B.wire(report['controls'])==B.wire(checks),'cipher original raw hashes/bindings/controls')


def save(path,value):
    with path.open('x')as out:json.dump(value,out,indent=2);out.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for n in('rom','reference','input-contract','out-dir'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents and not out.exists(),'fresh private cipher output directory')
        need((a.raw_dir is not None)==(a.mode=='verify'),'raw-dir only and required for verify')
        receipt,inputs,predictions,bindings=prepare(a);out.mkdir(parents=True)
        prepared=dict(schema='native-mon-cipher-prepared-v1',resources=receipt,bindings=bindings,
            predictions={name:dict(instructions=len(x['flow']),reads=len(x['reads']),stores=len(x['stores']),peak=x['native_peak'],ciphertext_sha256=x['ciphertext_sha256'],returned=x['returned'])for name,x in predictions.items()},CPU_executed=False)
        save(out/'prepared.json',prepared)
        if a.mode=='prepare':print('Cipher source/bytes/frozen/math prepared; no CPU/compiler');return
        raws={};records=[]
        for name,key,observe in(('SeedFC0','SeedFC0',True),('SeedFC0_OFF','SeedFC0',False),('SeedFC1','SeedFC1',True)):
            need(source_identities()==bindings['source_sha256'],'cipher source drift before cell')
            if a.mode=='matrix':
                raw=B.run(inputs[key],B.observation_policy(predictions[key]),observe);save(out/(name+'.json'),raw)
            else:raw=json.loads((a.raw_dir/(name+'.json')).read_bytes())
            need(source_identities()==bindings['source_sha256'],'cipher source drift after cell')
            raws[name]=raw;B.require_run(inputs[key],raw)
            records.append(dict(name=name,file=name+'.json',sha256=R.file_sha((out if a.mode=='matrix'else a.raw_dir)/(name+'.json'))))
        if a.mode=='verify':
            old=json.loads((a.raw_dir/'prepared.json').read_bytes());need(B.wire(old)==B.wire(prepared),'cipher original prepared bindings/predictions')
        checks=controls(raws,inputs)
        if a.mode=='verify':
            old_report=json.loads((a.raw_dir/'report.json').read_bytes())
            require_completed_report(old_report,records,bindings,checks)
        need(source_identities()==bindings['source_sha256'],'cipher source drift before report')
        save(out/('verification.json'if a.mode=='verify'else'report.json'),dict(schema='native-mon-cipher-report-v1',mode=a.mode,CPU_executed=a.mode=='matrix',bindings=bindings,raw=records,controls=checks,verdict='PASS within owned128byte/seedFC0-FC1/native cipher scope'))
    except(ValueError,OSError,KeyError,EOFError,subprocess.CalledProcessError)as e:p.exit(2,str(e)+'\n')
    print('Whole native cipher '+a.mode+' PASS; three cells, zero models/runtime host writes')


if __name__=='__main__':main()
