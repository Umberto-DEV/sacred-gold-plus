#!/usr/bin/env python3
"""Prepare/execute/verify whole MaxPP with native NARC, SDK and signed DIV.

Five cells exercise PP-Up clamp and a declared PP1 input. There is no duplicate
probe, historical capture mode, quotient service or runtime state reinjection.
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
D=load(HERE.with_name('attribuisci_pp_memory.py'),'MaxPP_retained_verification')
B=load(HERE.parents[1]/'test/maxpp_memory_bench.py','MaxPP_whole_native_bench')
C=load(HERE.with_name('compila_s32_div.py'),'MaxPP_source_comparison_builder')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PARENT_SHA='a7ec1ad70fc0e8f363d1e327dc866b981b11135e8d1d5a40231fc2189ba7b090'


def source_identities():
    ids=D.source_identities()
    paths=(HERE,Path(B.__file__),Path(B.A.__file__),Path(B.A.D.__file__),Path(F.__file__),Path(L.__file__),Path(C.__file__),C.RECIPE,HERE.with_name('qualifica_maxpp_aritmetica.py'))
    ids.update({str(p.relative_to(SOURCE)):R.sha(p.read_bytes())for p in paths});return ids


def verify_div_recipe(directory,reference):
    directory=Path(directory);m=json.loads((directory/'manifesto.json').read_bytes())
    need(m['schema']=='native-s32-div-recipe-v1'and m['builder_sha256']==R.sha(Path(C.__file__).read_bytes())and
         m['recipe_sha256']==R.sha(C.RECIPE.read_bytes()),'exact DIV recipe/builder identity')
    need(m['qualified_helper_sha256']==C.PARENT_SHA and R.sha(Path(C.C.__file__).read_bytes())==C.PARENT_SHA and
         m['loader_sha256']==R.sha(C.C.C.LOADER.read_bytes())and m['compiler_sha256']==C.C.CC_SHA,'DIV qualified compiler/loader provenance')
    need(m['source_pin']==C.PIN and m['source_sha256']==C.SOURCES and m['source_instructions']==131 and
         len(m['commands'])==1 and m['commands'][0]['exit_code']==0,'completed one-object DIV compilation')
    for name,digest in C.SOURCES.items():need(R.sha((reference/name).read_bytes())==digest,'DIV source dependency drift')
    lines=C.source_body((reference/'lib/MSL_C/src/msl_fp_runtime.c').read_text())
    need(lines==C.recipe_body(C.RECIPE.read_text())and m['canonical_source_sha256']==R.sha(('\n'.join(lines)+'\n').encode()),'MSL instruction-for-instruction recovered recipe')
    need(m['recipe_is_recovered']is True and m['original_C_codegen_reconstructed']is False and m['ROM_produced']is False and m['CPU_executed']is False,'DIV recipe scope')
    blob,obj=C.read_object(directory/'s32_div.o');need(obj==m['object'],'DIV compiled object receipt')
    return m,obj


def prepare(args):
    need(R.sha(Path(D.__file__).read_bytes())==PARENT_SHA,'qualified whole PP verifier drift')
    receipt,parts=L.prepare(args.rom)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen four-profile MaxPP contract')
    q=D.D.D;ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==q.PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned MaxPP reference')
    dependencies={**q.SDK_FILES,'src/filesystem.c':L.L.L.SOURCE_SHA,'src/move.c':L.L.SOURCE_SHA,**C.SOURCES}
    for name,digest in dependencies.items():need(R.sha((ref/name).read_bytes())==digest,'MaxPP reference dependency drift '+name)
    for name,digest in q.RECIPE_FILES.items():need(R.sha((SOURCE/name).read_bytes())==digest,'MaxPP retained recipe drift '+name)
    objects=json.loads(args.objects.read_bytes())
    need(type(objects)is dict and set(objects)==set(q.SYMBOLS)and all(type(p)is str for p in objects.values()),'exact thirty SDK ELF paths')
    generic=q.D.D.verify_objects
    proof=types.FunctionType(generic.__code__,{**vars(q.D.D),'L':q.L,'SYMBOLS':q.SYMBOLS})(objects,parts)
    sdk=q.verify_recipe(args.recipe_dir,ref)
    for name in q.C.BODIES:need(proof[name]['object_sha256']==sdk['objects'][name]['object_sha256'],'SDK retained ELF/source receipt '+name)
    div,div_obj=verify_div_recipe(args.div_recipe,ref)
    need(parts['signed_div']==C.read_object(args.div_recipe/'s32_div.o')[0],'installed current DIV / recompiled ELF readback')
    inputs={name:F.make_input(parts,ups,pp)for name,(ups,pp)in F.PROFILES.items()}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        objects_sha256=R.file_sha(args.objects),ELF=proof,SDK_pin=q.PIN,reference_files=dependencies,
        retained_recipe_manifest_sha256=R.file_sha(args.recipe_dir/'manifesto.json'),
        division_recipe_manifest_sha256=R.file_sha(args.div_recipe/'manifesto.json'),division_ELF=div_obj,
        compiler_origin='Authenticated recovered-assembly recipe; original MWC/Thumb objects missing',project_driver_mapped=False)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    names={'Up3','Up0','Up4','Up3_OFF','PP1Up3'};need(set(raws)==names,'complete five-cell MaxPP matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='Up3_OFF'),'MaxPP OFF observation binding')
        B.require_run(inputs['Up3'if name=='Up3_OFF'else name],raw)
    positive,off,clamp,counter=raws['Up3'],raws['Up3_OFF'],raws['Up4'],raws['PP1Up3']
    need([raws[x]['returned'][0]for x in('Up3','Up0','Up4','PP1Up3')]==[24,15,24,1],'native whole MaxPP mathematical results')
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(positive[key])==B.wire(off[key]),'MaxPP OFF neutrality '+key)
        need(B.wire(positive[key])==B.wire(clamp[key]),'MaxPP clamp final CPU/map convergence '+key)
    need(positive['initial']==off['initial']and positive['initial']!=clamp['initial'],'MaxPP clamp argument provenance')
    need(positive['initial']['initial_map_sha256']==clamp['initial']['initial_map_sha256'],'clamp same initial memory')
    need(clamp['executed_count']==positive['executed_count']+1 and
         sum(x['pc']==0x2073334 for x in clamp['flow'])==1 and not any(x['pc']==0x2073334 for x in positive['flow']),'one actual clamp MOVS, no trace normalization')
    def joined(raw):
        i=next(i for i,x in enumerate(raw['flow'])if x['pc']==0x2073338);return raw['flow'][i:]
    need(joined(positive)==joined(clamp)and positive['reads']==clamp['reads']and positive['stores']==clamp['stores'],'complete native context converges after clamp and argument setup')
    rd=[i for i,(a,b)in enumerate(zip(positive['reads'],counter['reads']))if a!=b]
    wr=[i for i,(a,b)in enumerate(zip(positive['stores'],counter['stores']))if a!=b]
    need(rd==[1583,1734]and wr==[1215],'MaxPP before-CPU causal PP read/copy differences')
    left={x['ram']:bytes.fromhex(x['hex'])for x in positive['final_pages']};right={x['ram']:bytes.fromhex(x['hex'])for x in counter['final_pages']}
    need(left.keys()==right.keys(),'MaxPP same mapped page owners')
    delta=sorted((a+i,x,y)for a in left for i,(x,y)in enumerate(zip(left[a],right[a]))if x!=y)
    need(delta==sorted(((F.SDK.MEMBER_SOURCE+6,15,1),(F.DEST+6,15,1))),'MaxPP final source/buffer PP-only byte differences')
    cases=[]
    forged=copy.deepcopy(clamp);i=next(i for i,x in enumerate(forged['flow'])if x['pc']==0x2073334);del forged['flow'][i]
    cases.append(('missing_clamp_step',inputs['Up4'],forged,'source MaxPP native flow'))
    forged=copy.deepcopy(positive);i=next(i for i,x in enumerate(forged['flow'])if x['pc']==B.A.DIV_ENTRY);del forged['flow'][i]
    cases.append(('missing_DIV_entry',inputs['Up3'],forged,'source MaxPP native flow'))
    forged=copy.deepcopy(positive);next(x for x in forged['flow']if x['pc']==B.A.DIV_RETURN)['regs'][0]=0
    cases.append(('constant_zero_quotient',inputs['Up3'],forged,'source MaxPP native flow'))
    forged=copy.deepcopy(positive);next(x for x in forged['flow']if x['pc']==0x20f2b5c)['regs'][15]^=0x20000000
    cases.append(('wrong_ADC_carry_context',inputs['Up3'],forged,'source MaxPP native flow'))
    forged=copy.deepcopy(positive);forged['returned'][0]=15
    cases.append(('wrong_scalar',inputs['Up3'],forged,'source MaxPP full16 return ABI'))
    forged=copy.deepcopy(counter);forged['initial']=copy.deepcopy(positive['initial'])
    cases.append(('PP_input_camouflage',inputs['Up3'],forged,'source MaxPP counters'))
    forged=copy.deepcopy(counter);forged['returned'][1]=0
    cases.append(('wrong_remainder',inputs['PP1Up3'],forged,'source MaxPP full16 return ABI'))
    forged=copy.deepcopy(counter);del forged['reads'][1734]
    cases.append(('missing_PP_leaf_read',inputs['PP1Up3'],forged,'source MaxPP native reads'))
    forged=copy.deepcopy(counter);forged['stores'][1215]['value']=positive['stores'][1215]['value']
    cases.append(('wrong_PP_copy_word',inputs['PP1Up3'],forged,'source MaxPP native stores'))
    forged=copy.deepcopy(counter);del forged['stores'][1215]
    cases.append(('missing_PP_copy_word',inputs['PP1Up3'],forged,'source MaxPP native stores'))
    rejected=[]
    for label,f,forged,reason in cases:
        try:B.require_run(f,forged)
        except ValueError as e:need(str(e)==reason,'MaxPP forgery rejected at declared check '+label);rejected.append(dict(name=label,reason=reason))
        else:raise ValueError('MaxPP evidence forgery accepted '+label)
    return dict(OFF_pairs=1,clamp_pairs=1,PP_input_pairs=1,native_results=[24,15,24,1],clamp_extra_steps=1,
        read_differences=rd,store_differences=wr,PP_final_byte_differences=delta,forgeries=rejected)


def save(path,value):
    with Path(path).open('x')as f:json.dump(value,f,indent=2);f.write('\n')


def verify_existing(directory,receipt,inputs,bindings):
    report=json.loads((directory/'report.json').read_bytes())
    need(report.get('schema')=='native-MaxPP-memory-report-v1'and report['mode']=='matrix'and report['CPU_executed']is True,'completed MaxPP matrix report')
    need(B.wire(report['resources'])==B.wire(receipt)and B.wire(report['bindings'])==B.wire(bindings),'existing MaxPP source/resource/recipe binding')
    names=['Up3','Up0','Up4','Up3_OFF','PP1Up3'];need([x['name']for x in report['raw']]==names,'exact ordered MaxPP raw manifest')
    raws={}
    for row in report['raw']:
        need(row['file']==row['name']+'.json','bounded MaxPP raw filename')
        path=directory/row['file'];need(not path.is_symlink()and R.file_sha(path)==row['sha256'],'MaxPP raw identity')
        raw=json.loads(path.read_bytes());B.require_run(inputs['Up3'if row['name']=='Up3_OFF'else row['name']],raw);raws[row['name']]=raw
    evidence=controls(raws,inputs);need(B.wire(evidence)==B.wire(report['controls']),'existing MaxPP control verdict')
    return dict(verified_report_sha256=R.file_sha(directory/'report.json'),raw_files=len(raws),controls=evidence,CPU_executed=False,compiler_invoked=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','matrix','verify'),required=True)
    for name in('rom','objects','recipe-dir','div-recipe','reference','input-contract','out-dir'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        need((a.mode=='verify')==(a.raw_dir is not None),'--raw-dir required only in verify mode')
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents,'private MaxPP output outside source')
        need(not a.out_dir.exists()and not a.out_dir.is_symlink(),'fresh private MaxPP output directory')
        receipt,inputs,predictions,bindings=prepare(a);a.out_dir.mkdir(parents=True)
        report=dict(schema='native-MaxPP-memory-report-v1',mode=a.mode,resources=receipt,bindings=bindings,CPU_executed=False,raw=[])
        save(a.out_dir/'prepared.json',report)
        if a.mode=='prepare':print('Whole MaxPP source/ELF/frozen profiles prepared, no CPU/compiler');return
        if a.mode=='verify':save(a.out_dir/'verification.json',verify_existing(a.raw_dir,receipt,inputs,bindings));print('MaxPP raw verified, no CPU/compiler');return
        save(a.out_dir/'SOURCE-BEFORE-CPU.json',source_identities());raws={}
        for name in('Up3','Up0','Up4','Up3_OFF','PP1Up3'):
            key='Up3'if name=='Up3_OFF'else name;f=inputs[key]
            raw=B.run(f,B.observation_policy(predictions[key]),observe=name!='Up3_OFF')
            path=a.out_dir/(name+'.json');save(path,raw) # Raw precedes every verdict.
            B.require_run(f,raw);raws[name]=raw
            report['raw'].append(dict(name=name,file=path.name,sha256=R.file_sha(path)))
            need(source_identities()==bindings['source_sha256'],'MaxPP source changed during execution')
        report['CPU_executed']=True;report['controls']=controls(raws,inputs)
        report['verdict']='PASS within whole MaxPP / explicit memory archive / fixed argument domain';save(a.out_dir/'report.json',report)
    except(ValueError,OSError,EOFError,subprocess.SubprocessError)as e:p.exit(2,str(e)+'\n')
    print('MaxPP matrix PASS; original native arithmetic/FS and zero service models/runtime host writes')


if __name__=='__main__':main()
