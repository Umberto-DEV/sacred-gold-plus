#!/usr/bin/env python3
"""Prepare/execute/verify the original NARC caller with native SDK internals.

Requires the thirty qualified SDK comparison objects and their P84 recipe.
No project caller is mapped or executed. Verification imports no CPU backend.
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
D=load(HERE.with_name('attribuisci_fs_memory_read.py'),'narc_retained_SDK_verification')
B=load(HERE.parents[1]/'test/fs_memory_narc_bench.py','narc_native_memory_bench')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PARENT_SHA='d7cced092dd68c09413bf8f94bf568842415487409de6802a201fcc966a5132c'


def source_identities():
    ids=D.source_identities()
    paths=(HERE,Path(B.__file__),Path(B.A.__file__),Path(F.__file__),Path(L.__file__),HERE.with_name('qualifica_interworking_narc.py'))
    ids.update({str(p.relative_to(SOURCE)):R.sha(p.read_bytes())for p in paths})
    return ids


def prepare(args):
    need(R.sha(Path(D.__file__).read_bytes())==PARENT_SHA,'qualified SDK verifier drift')
    receipt,parts=L.prepare(args.rom,args.snapshot)
    frozen=json.loads(args.input_contract.read_bytes())
    need(B.wire(frozen)==B.wire(F.freeze(receipt,parts)),'exact frozen native NARC contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==D.PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned SDK/game reference')
    dependencies={**D.SDK_FILES,'src/filesystem.c':L.SOURCE_SHA}
    for name,digest in dependencies.items():need(R.sha((ref/name).read_bytes())==digest,'native reference source/header drift '+name)
    for name,digest in D.RECIPE_FILES.items():need(R.sha((SOURCE/name).read_bytes())==digest,'retained recipe/builder drift '+name)
    objects=json.loads(args.objects.read_bytes())
    need(type(objects)is dict and set(objects)==set(D.SYMBOLS)and all(type(p)is str for p in objects.values()),'exact thirty named native ELF paths')
    generic=D.D.D.verify_objects
    proof=types.FunctionType(generic.__code__,{**vars(D.D.D),'L':D.L,'SYMBOLS':D.SYMBOLS})(objects,parts)
    recipe=D.verify_recipe(args.recipe_dir,ref)
    for name in D.C.BODIES:need(proof[name]['object_sha256']==recipe['objects'][name]['object_sha256'],'native new ELF/recipe receipt '+name)
    inputs={'normal':F.make_input(parts),'precompleted_destination':F.make_input(parts,True)}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        objects_sha256=R.file_sha(args.objects),ELF=proof,SDK_pin=D.PIN,SDK_files=dependencies,
        recipe_manifest_sha256=R.file_sha(args.recipe_dir/'manifesto.json'),
        project_driver_mapped=False,native_Thumb_compiler_origin='Original Metrowerks/object missing; C candidate and exact installed bytes separately identified')
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'normal','normal_OFF','precompleted_destination'},'complete native NARC matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='normal_OFF'),'OFF observation binding')
        B.require_run(inputs['normal'if name=='normal_OFF'else name],raw)
    normal,off,projected=(raws[x]for x in('normal','normal_OFF','precompleted_destination'))
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(normal[key])==B.wire(off[key]),'OFF neutrality '+key)
        need(B.wire(normal[key])==B.wire(projected[key]),'convergent destination projection '+key)
    need(normal['initial']==off['initial']and normal['initial']!=projected['initial'],'initial destination projection provenance')
    for key in('flow','reads'):need(normal[key]==projected[key],'same native route '+key)
    differences=[i for i,(a,b)in enumerate(zip(normal['stores'],projected['stores']))if a!=b]
    expected=[i for i,e in enumerate(B.predict(inputs['normal'])['stores'])if e['pc']==0x20d4b7c and F.DEST<=e['address']<F.DEST+16]
    need(len(expected)==4 and differences==expected,'four native final member writer preimages')
    forged=copy.deepcopy(projected);forged['initial']=copy.deepcopy(normal['initial'])
    try:B.require_run(inputs['normal'],forged)
    except ValueError as e:need(str(e)=='source native stores','camouflage rejection at writer transcript')
    else:raise ValueError('camouflaged precompleted destination accepted')
    for index in expected:
        altered=copy.deepcopy(normal);del altered['stores'][index]
        try:B.require_run(inputs['normal'],altered)
        except ValueError as e:need(str(e)=='source native stores','deleted writer rejection at transcript')
        else:raise ValueError('deleted native member writer accepted')
    return dict(OFF_pairs=1,convergent_destination_pairs=1,different_store_preimages=differences,
        camouflage_rejections=1,deleted_writer_rejections=expected,original_ROM_instructions=6262,ARM_instructions=6159,Thumb_instructions=103)


def save(path,value):
    with Path(path).open('x')as f:json.dump(value,f,indent=2);f.write('\n')


def verify_existing(directory,receipt,inputs,bindings):
    report=json.loads((directory/'report.json').read_bytes())
    need(report.get('schema')=='native-fs-memory-narc-report-v1'and report['mode']in('probe','matrix')and report['CPU_executed']is True,'native completed report')
    need(B.wire(report['resources'])==B.wire(receipt)and B.wire(report['bindings'])==B.wire(bindings),'existing resource/source/recipe binding')
    names=['normal']if report['mode']=='probe'else['normal','normal_OFF','precompleted_destination']
    need([x['name']for x in report['raw']]==names,'exact ordered raw manifest')
    raws={}
    for row in report['raw']:
        need(row['file']==row['name']+'.json','bounded raw filename')
        path=directory/row['file'];need(not path.is_symlink()and R.file_sha(path)==row['sha256'],'raw identity')
        raw=json.loads(path.read_bytes());B.require_run(inputs['normal'if row['name']=='normal_OFF'else row['name']],raw);raws[row['name']]=raw
    evidence=None if report['mode']=='probe'else controls(raws,inputs)
    need(B.wire(evidence)==B.wire(report['controls']),'existing control verdict')
    return dict(verified_report_sha256=R.file_sha(directory/'report.json'),raw_files=len(raws),controls=evidence,CPU_executed=False,compiler_invoked=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('prepare','probe','matrix','verify'),required=True)
    for name in('rom','objects','recipe-dir','reference','input-contract','out-dir'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        need((a.mode=='verify')==(a.raw_dir is not None),'--raw-dir required only in verify mode')
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents,'private output outside source')
        need(not a.out_dir.exists()and not a.out_dir.is_symlink(),'fresh private output directory')
        receipt,inputs,predictions,bindings=prepare(a);a.out_dir.mkdir(parents=True)
        report=dict(schema='native-fs-memory-narc-report-v1',mode=a.mode,resources=receipt,bindings=bindings,CPU_executed=False,raw=[])
        save(a.out_dir/'prepared.json',report)
        if a.mode=='prepare':print('Native caller prepared/predicted, no CPU/compiler');return
        if a.mode=='verify':save(a.out_dir/'verification.json',verify_existing(a.raw_dir,receipt,inputs,bindings));print('Raw verified, no CPU/compiler');return
        save(a.out_dir/'SOURCE-BEFORE-CPU.json',source_identities())
        names=('normal',)if a.mode=='probe'else('normal','normal_OFF','precompleted_destination');raws={}
        for name in names:
            key='normal'if name=='normal_OFF'else name;f=inputs[key]
            raw=B.run(f,B.observation_policy(predictions[key]),observe=name!='normal_OFF')
            path=a.out_dir/(name+'.json');save(path,raw) # Save raw before verdict.
            B.require_run(f,raw);raws[name]=raw
            report['raw'].append(dict(name=name,file=path.name,sha256=R.file_sha(path)))
            need(source_identities()==bindings['source_sha256'],'source changed during execution')
        report['CPU_executed']=True;report['controls']=None if a.mode=='probe'else controls(raws,inputs)
        report['verdict']='PASS within native NARC reader / hybrid memory archive scope';save(a.out_dir/'report.json',report)
    except(ValueError,OSError,EOFError,subprocess.SubprocessError)as e:p.exit(2,str(e)+'\n')
    print(a.mode,'PASS; native original caller and SDK, zero models/runtime host writes')


if __name__=='__main__':main()
