#!/usr/bin/env python3
"""Prepare/execute/CPU-free verify full cached Open and a finite FAT failure.

Compose previously qualified functions with two new comparison objects. Exact
text verifies bytes; retain original build receipts for compiler provenance.
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


HERE=Path(__file__).resolve()
SOURCE=HERE.parents[3]
D=load(HERE.with_name('attribuisci_fs_cached_convert.py'),'open_qualified_retained_verifier')
B=load(HERE.parents[1]/'test/fs_cached_open_bench.py','cached_open_native_bench')
C=load(HERE.with_name('compila_fs_cached_open.py'),'cached_open_comparison_builder')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PIN,SDK_FILES=D.PIN,D.SDK_FILES
PARENT_SHA='c4738fb1bb4e63c56a95b0c9a8eb054609b07c517d173d4971bce270fb053b70'
SYMBOLS={**D.SYMBOLS,'open':'native_fs_open_recipe','fast':'native_fs_fast_recipe',
    'fast_command':'native_fs_cached_fast_command','direct_command':'native_fs_cached_direct_command'}
RECIPE_FILES={**D.RECIPE_FILES}
RECIPE_FILES.update({'features/trainer-strategy/tools/compila_fs_open.py': 'e804541b4a4cb44ef0d906424bc2f77fea6cc774b8f9897a27a4315d9dc2fa6b', 'features/trainer-strategy/sorgenti/fs-open.S': '106cc7ef25b579a3506275b6b188052c216c51fcf9e3207c4258d008a7e0868b', 'features/trainer-strategy/tools/compila_fs_fast.py': 'ae00fd72bdd13e9278e4c8a94bef2010b83e5b4beaf61357c1fa957890d66cfc', 'features/trainer-strategy/sorgenti/fs-fast.S': '05a121c32f77fc02192827be122d488641682d10805232c532c65f322b6c69d6'})


def source_identities():
    ids=D.source_identities()
    paths=(HERE,Path(B.__file__),Path(F.__file__),Path(L.__file__),Path(C.__file__),C.RECIPE)
    ids.update({str(p.relative_to(SOURCE)):R.sha(p.read_bytes())for p in paths})
    ids.update({name:R.sha((SOURCE/name).read_bytes())for name in RECIPE_FILES})
    return ids


def verify_recipe(directory,reference):
    directory=Path(directory);m=json.loads((directory/'manifesto.json').read_bytes())
    need(m['schema']=='native-fs-cached-open-recipe-v1'and m['builder_sha256']==R.sha(Path(C.__file__).read_bytes())and
         m['recipe_sha256']==R.sha(C.RECIPE.read_bytes())and m['resource_reader_sha256']==R.sha(Path(L.__file__).read_bytes()),'new recovered recipe/source/reader identity')
    need(m['parent_builder_sha256']==C.PARENT_SHA and R.sha(Path(C.C.__file__).read_bytes())==C.PARENT_SHA and
         m['compiler_sha256']==C.C.CC_SHA and m['layout_passed']is True and all(x['exit_code']==0 for x in m['commands']),'authenticated compiler/layout receipt')
    need(m['layout_helper_sha256']==R.sha(Path(C.C.C.__file__).read_bytes())and m['loader_sha256']==R.sha(C.C.C.LOADER.read_bytes())and m['source_sha256']==C.C.SOURCES,'layout/helper/source provenance')
    for rel,digest in {**m['source_sha256'],**m['header_sha256']}.items():need(R.sha((reference/rel).read_bytes())==digest,'new recipe SDK dependency drift')
    C.objects(directory)
    return m


def prepare(args):
    need(R.sha(Path(D.__file__).read_bytes())==PARENT_SHA,'qualified retained verifier drift')
    receipt,parts=L.prepare(args.rom,args.snapshot)
    frozen=json.loads(args.input_contract.read_bytes());need(B.wire(frozen)==B.wire(F.freeze(receipt,parts)),'exact frozen source/input/resource contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned SDK reference')
    for name,digest in SDK_FILES.items():need(R.sha((ref/name).read_bytes())==digest,'SDK source/header drift '+name)
    for name,digest in RECIPE_FILES.items():need(R.sha((SOURCE/name).read_bytes())==digest,'retained recipe/builder drift '+name)
    objects=json.loads(args.objects.read_bytes())
    # The parent generic ELF loop accepts explicit component/symbol metadata;
    # its code is pinned and unchanged, not copied or executed as a producer.
    verify=types.FunctionType(D.verify_objects.__code__,{**vars(D),'L':L,'SYMBOLS':SYMBOLS})
    proof=verify(objects,parts);manifest=verify_recipe(args.recipe_dir,ref)
    for name in C.BODIES:need(proof[name]['object_sha256']==manifest['objects'][name]['object_sha256'],'new ELF / completed recipe receipt '+name)
    inputs={name:F.make_input(parts,name)for name in F.PROFILES};predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        objects_sha256=R.file_sha(args.objects),ELF=proof,SDK_pin=PIN,SDK_files=SDK_FILES,
        recipe_manifest_sha256=R.file_sha(args.recipe_dir/'manifesto.json'))
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'normal','normal_OFF','precompleted_prop','fat_size_equal'},'complete four-run control matrix')
    need(all(raw['observed']is(name!='normal_OFF')for name,raw in raws.items()),'OFF observation binding')
    for name,raw in raws.items():B.require_run(inputs['normal'if name=='normal_OFF'else name],raw)
    normal,off,projected,failed=(raws[name]for name in('normal','normal_OFF','precompleted_prop','fat_size_equal'))
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(normal[key])==B.wire(off[key]),'OFF neutrality '+key)
        need(B.wire(normal[key])==B.wire(projected[key]),'convergent initial property projection '+key)
    need(normal['initial']==off['initial']and normal['initial']!=projected['initial'],'initial property projection provenance')
    for key in('flow','reads'):need(normal[key]==projected[key],'same source route '+key)
    differences=[i for i,(a,b)in enumerate(zip(normal['stores'],projected['stores']))if a!=b]
    need(differences==[682,683,684,685],'four native Direct property writer preimages')
    forged=copy.deepcopy(projected);forged['initial']=copy.deepcopy(normal['initial'])
    try:B.require_run(inputs['normal'],forged)
    except ValueError as error:need(str(error)=='source native stores','camouflage specifically native stores')
    else:raise ValueError('camouflaged precompleted property accepted')
    for index in differences:
        altered=copy.deepcopy(normal);del altered['stores'][index]
        try:B.require_run(inputs['normal'],altered)
        except ValueError as error:need(str(error)=='source native stores','deleted native writer specifically rejected')
        else:raise ValueError('deleted native Direct writer accepted')
    need(failed['returned'][0]==0 and failed['native_count']==3053,'native equality bounds failure returns FALSE')
    boundary=next(i for i,x in enumerate(normal['flow'])if x['pc']==0x20d7354)
    need(failed['flow'][:boundary+1]==normal['flow'][:boundary+1],'same actual lookup until native FAT-size read')
    need(not any(x['pc']==0x20d73c0 for x in failed['flow']),'no Direct activation after bounds failure')
    return dict(OFF_pairs=1,convergent_property_pairs=1,different_store_preimages=differences,
        camouflage_rejected='source native stores',deleted_writer_rejections=differences,
        native_fat_size_equal_failure=True,common_prefix_before_FAT_size_read=boundary+1)


def save(path,value):
    with Path(path).open('x')as stream:stream.write(json.dumps(value,indent=2)+'\n')


def verify_existing(directory,receipt,inputs,bindings):
    report=json.loads((directory/'report.json').read_bytes())
    need(report.get('schema')=='native-fs-cached-open-report-v1','native report schema')
    need(report['mode']in('probe','matrix') and report['CPU_executed']is True,'existing native report domain')
    need(B.wire(report['resources'])==B.wire(receipt)and B.wire(report['bindings'])==B.wire(bindings),'existing native resource/source/recipe binding')
    names=['normal']if report['mode']=='probe'else['normal','normal_OFF','precompleted_prop','fat_size_equal']
    need([x['name']for x in report['raw']]==names,'exact ordered raw manifest')
    raws={}
    for row in report['raw']:
        need(row['file']==row['name']+'.json','local raw filename')
        path=directory/row['file'];need(not path.is_symlink()and R.file_sha(path)==row['sha256'],'raw file identity')
        raw=json.loads(path.read_bytes());B.require_run(inputs['normal'if row['name']=='normal_OFF'else row['name']],raw);raws[row['name']]=raw
    evidence=None if report['mode']=='probe'else controls(raws,inputs)
    need(B.wire(evidence)==B.wire(report['controls']),'existing control verdict')
    return dict(verified_report_sha256=R.file_sha(directory/'report.json'),raw_files=len(raws),controls=evidence,CPU_executed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','probe','matrix','verify'),required=True)
    for name in('rom','objects','recipe-dir','reference','input-contract','out-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--raw-dir',type=Path);args=p.parse_args()
    try:
        need((args.mode=='verify')==(args.raw_dir is not None),'--raw-dir required only in verify mode')
        need(args.out_dir.resolve()!=SOURCE and SOURCE not in args.out_dir.resolve().parents,'private raw output outside source required')
        need(not args.out_dir.exists()and not args.out_dir.is_symlink(),'fresh private output directory required')
        receipt,inputs,predictions,bindings=prepare(args)
        args.out_dir.mkdir(parents=True)
        report=dict(schema='native-fs-cached-open-report-v1',mode=args.mode,resources=receipt,bindings=bindings,CPU_executed=False,raw=[])
        save(args.out_dir/'prepared.json',report)
        if args.mode=='prepare':print('Prepared and predicted, no CPU/compiler');return
        if args.mode=='verify':
            save(args.out_dir/'verification.json',verify_existing(args.raw_dir,receipt,inputs,bindings));print('Existing raw verified; no CPU/compiler');return
        save(args.out_dir/'SOURCE-BEFORE-CPU.json',source_identities())
        names=('normal',)if args.mode=='probe'else('normal','normal_OFF','precompleted_prop','fat_size_equal');raws={}
        for name in names:
            key='normal'if name=='normal_OFF'else name;f=inputs[key]
            raw=B.run(f,B.observation_policy(predictions[key]),observe=name!='normal_OFF')
            path=args.out_dir/(name+'.json');save(path,raw) # Always before verdict.
            B.require_run(f,raw);raws[name]=raw
            report['raw'].append(dict(name=name,file=path.name,sha256=R.file_sha(path)))
            need(source_identities()==bindings['source_sha256'],'runtime source changed during native execution')
        report['CPU_executed']=True;report['controls']=None if args.mode=='probe'else controls(raws,inputs)
        report['verdict']='PASS within declared isolated cached Open scope';save(args.out_dir/'report.json',report)
    except(ValueError,OSError,EOFError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print(args.mode,'PASS; full native Open returned, zero models/runtime host writes')


if __name__=='__main__':main()
