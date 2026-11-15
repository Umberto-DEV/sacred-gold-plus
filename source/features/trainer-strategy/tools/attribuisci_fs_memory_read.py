#!/usr/bin/env python3
"""Prepare/execute/CPU-free verify the five-API memory-archive Read chain.

Three recovered native comparisons and a project caller compose27 retained SDK
objects. Exact text verifies bytes; compiler origin has its own build receipts.
No natural CARD protocol, payload model or host phase reinjection is implied.
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
D=load(HERE.with_name('attribuisci_fs_cached_open.py'),'open_qualified_retained_verifier')
B=load(HERE.parents[1]/'test/fs_memory_read_bench.py','cached_open_native_bench')
C=load(HERE.with_name('compila_fs_memory_read.py'),'cached_open_comparison_builder')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PIN,SDK_FILES=D.PIN,D.SDK_FILES
PARENT_SHA='16ead32f2f60b809fc0a0c6938662d04cfb93847d29e97d41404f943ccfc3494'
SYMBOLS={**D.SYMBOLS,**{'read_wrapper': 'native_fs_read_wrapper_recipe', 'read_core': 'native_fs_read_core_recipe', 'wait': 'native_fs_wait_core_recipe', 'seek': 'native_fs_seek_recipe', 'close': 'native_fs_close_recipe', 'read_command': 'native_fs_cached_read_command', 'read_callback': 'native_fs_cached_read_callback', 'close_command': 'native_fs_cached_close_command'}}
RECIPE_FILES={**D.RECIPE_FILES,**{'features/trainer-strategy/tools/compila_fs_read.py': '92b0d052f87f456050fce873f0b0552a33abc42017c00afffa535a1951dc9788', 'features/trainer-strategy/sorgenti/fs-read.S': '0ff59bcb61aee13bae38d72e886b5d18faed2f4bca53ad989e10f14c2ab3bc06', 'features/trainer-strategy/tools/compila_fs_wait.py': '2607383e21b39eb42aee854ffccb1be787ae7247f4d3699ad0e515206124c476', 'features/trainer-strategy/sorgenti/fs-wait.S': '5c61122523eb40339ccdf137555a7811e439a361f74983974e9329aa3e36b430', 'features/trainer-strategy/tools/compila_fs_seek.py': 'ae02304ab07bd1e01ebbb6285b9a2fb0c62e86716f737654268f8f99ccebf647', 'features/trainer-strategy/sorgenti/fs-seek.S': 'b491ee8b52a541b7948d745b295a35053a3805519417d5ef4781bfc6fb77421d', 'features/trainer-strategy/tools/compila_fs_close.py': 'f13f9cb2d204300b845712491b36007253b812e07ad911ae30b78904e5c7aca8', 'features/trainer-strategy/sorgenti/fs-close.S': '45259a690d36b886d2ecdcbec5ecff2c180b0aef9ae3b37143437f0c3533cd7f'}}
SDK_FILES={**D.SDK_FILES,**C.SOURCES}


def source_identities():
    ids=D.source_identities()
    paths=(HERE,Path(B.__file__),Path(F.__file__),Path(L.__file__),Path(C.__file__),C.RECIPE,C.DRIVER_RECIPE)
    ids.update({str(p.relative_to(SOURCE)):R.sha(p.read_bytes())for p in paths})
    ids.update({name:R.sha((SOURCE/name).read_bytes())for name in RECIPE_FILES})
    return ids


def verify_recipe(directory,reference):
    directory=Path(directory);m=json.loads((directory/'manifesto.json').read_bytes())
    need(m['schema']=='native-fs-memory-read-recipe-v1'and m['builder_sha256']==R.sha(Path(C.__file__).read_bytes())and
         m['recipe_sha256']==R.sha(C.RECIPE.read_bytes())and m['driver_recipe_sha256']==R.sha(C.DRIVER_RECIPE.read_bytes())and m['resource_reader_sha256']==R.sha(Path(L.__file__).read_bytes()),'new recovered recipe/source/reader identity')
    need(m['parent_builder_sha256']==C.PARENT_SHA and R.sha(Path(C.C.__file__).read_bytes())==C.PARENT_SHA and
         m['compiler_sha256']==C.C.CC_SHA and m['layout_passed']is True and all(x['exit_code']==0 for x in m['commands']),'authenticated compiler/layout receipt')
    need(m['layout_helper_sha256']==R.sha(Path(C.C.C.__file__).read_bytes())and m['loader_sha256']==R.sha(C.C.C.LOADER.read_bytes())and m['source_sha256']==C.SOURCES,'layout/helper/source provenance')
    for rel,digest in {**m['source_sha256'],**m['header_sha256']}.items():need(R.sha((reference/rel).read_bytes())==digest,'new recipe SDK dependency drift')
    C.objects(directory)
    return m


def prepare(args):
    need(R.sha(Path(D.__file__).read_bytes())==PARENT_SHA,'qualified retained verifier drift')
    receipt,parts=L.prepare(args.rom,args.snapshot)
    driver,driver_receipt=F.load_driver(args.recipe_dir)
    frozen=json.loads(args.input_contract.read_bytes());need(B.wire(frozen)==B.wire(F.freeze(receipt,parts,driver,driver_receipt)),'exact frozen source/input/resource contract')
    ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned SDK reference')
    for name,digest in SDK_FILES.items():need(R.sha((ref/name).read_bytes())==digest,'SDK source/header drift '+name)
    for name,digest in RECIPE_FILES.items():need(R.sha((SOURCE/name).read_bytes())==digest,'retained recipe/builder drift '+name)
    objects=json.loads(args.objects.read_bytes())
    # The parent generic ELF loop accepts explicit component/symbol metadata;
    # its code is pinned and unchanged, not copied or executed as a producer.
    need(type(objects)is dict and set(objects)==set(SYMBOLS)and all(type(p)is str for p in objects.values()),'exact thirty named native ELF paths')
    verify=types.FunctionType(D.D.verify_objects.__code__,{**vars(D.D),'L':L,'SYMBOLS':SYMBOLS})
    proof=verify(objects,parts);manifest=verify_recipe(args.recipe_dir,ref)
    for name in C.BODIES:need(proof[name]['object_sha256']==manifest['objects'][name]['object_sha256'],'new ELF / completed recipe receipt '+name)
    inputs={'normal':F.make_input(parts,driver),'precompleted_buffers':F.make_input(parts,driver,True)};predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        objects_sha256=R.file_sha(args.objects),ELF=proof,SDK_pin=PIN,SDK_files=SDK_FILES,
        recipe_manifest_sha256=R.file_sha(args.recipe_dir/'manifesto.json'),project_driver=driver_receipt)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'normal','normal_OFF','precompleted_buffers'},'complete three-run memory Read matrix')
    need(all(raw['observed']is(name!='normal_OFF')for name,raw in raws.items()),'OFF observation binding')
    for name,raw in raws.items():B.require_run(inputs['normal'if name=='normal_OFF'else name],raw)
    normal,off,projected=(raws[name]for name in('normal','normal_OFF','precompleted_buffers'))
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(normal[key])==B.wire(off[key]),'OFF neutrality '+key)
        need(B.wire(normal[key])==B.wire(projected[key]),'convergent initial buffer projection '+key)
    need(normal['initial']==off['initial']and normal['initial']!=projected['initial'],'initial buffer projection provenance')
    for key in('flow','reads'):need(normal[key]==projected[key],'same source route '+key)
    differences=[i for i,(a,b)in enumerate(zip(normal['stores'],projected['stores']))if a!=b]
    need(differences==[760,761,762,763,837,838,839,840],'eight native payload writer preimages')
    forged=copy.deepcopy(projected);forged['initial']=copy.deepcopy(normal['initial'])
    try:B.require_run(inputs['normal'],forged)
    except ValueError as error:need(str(error)=='source native stores','camouflage specifically native stores')
    else:raise ValueError('camouflaged precompleted payload accepted')
    for index in differences:
        altered=copy.deepcopy(normal);del altered['stores'][index]
        try:B.require_run(inputs['normal'],altered)
        except ValueError as error:need(str(error)=='source native stores','deleted native writer specifically rejected')
        else:raise ValueError('deleted native payload writer accepted')
    return dict(OFF_pairs=1,convergent_buffer_pairs=1,different_store_preimages=differences,
        camouflage_rejected='source native stores',deleted_writer_rejections=differences,
        original_ROM_instructions=4252,project_caller_instructions=27,API_results=[1,16,1,16,1])


def save(path,value):
    with Path(path).open('x')as stream:stream.write(json.dumps(value,indent=2)+'\n')


def verify_existing(directory,receipt,inputs,bindings):
    report=json.loads((directory/'report.json').read_bytes())
    need(report.get('schema')=='native-fs-memory-read-report-v1','native report schema')
    need(report['mode']in('probe','matrix') and report['CPU_executed']is True,'existing native report domain')
    need(B.wire(report['resources'])==B.wire(receipt)and B.wire(report['bindings'])==B.wire(bindings),'existing native resource/source/recipe binding')
    names=['normal']if report['mode']=='probe'else['normal','normal_OFF','precompleted_buffers']
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
        report=dict(schema='native-fs-memory-read-report-v1',mode=args.mode,resources=receipt,bindings=bindings,CPU_executed=False,raw=[])
        save(args.out_dir/'prepared.json',report)
        if args.mode=='prepare':print('Prepared and predicted, no CPU/compiler');return
        if args.mode=='verify':
            save(args.out_dir/'verification.json',verify_existing(args.raw_dir,receipt,inputs,bindings));print('Existing raw verified; no CPU/compiler');return
        save(args.out_dir/'SOURCE-BEFORE-CPU.json',source_identities())
        names=('normal',)if args.mode=='probe'else('normal','normal_OFF','precompleted_buffers');raws={}
        for name in names:
            key='normal'if name=='normal_OFF'else name;f=inputs[key]
            raw=B.run(f,B.observation_policy(predictions[key]),observe=name!='normal_OFF')
            path=args.out_dir/(name+'.json');save(path,raw) # Always before verdict.
            B.require_run(f,raw);raws[name]=raw
            report['raw'].append(dict(name=name,file=path.name,sha256=R.file_sha(path)))
            need(source_identities()==bindings['source_sha256'],'runtime source changed during native execution')
        report['CPU_executed']=True;report['controls']=None if args.mode=='probe'else controls(raws,inputs)
        report['verdict']='PASS within declared isolated memory Read scope';save(args.out_dir/'report.json',report)
    except(ValueError,OSError,EOFError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print(args.mode,'PASS; full API chain returned, zero models/runtime host writes')


if __name__=='__main__':main()
