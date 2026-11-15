#!/usr/bin/env python3
"""Prepare, execute or CPU-free verify the finite complete cached FindPath case."""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import subprocess


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
B=load(HERE.parents[1]/'test/fs_cached_findpath_bench.py','cached_find_native_bench')
C=load(HERE.with_name('compila_fs_cached_findpath.py'),'cached_find_native_build')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
SOURCE=HERE.parents[3]
TRANSLATE_BUILDER=HERE.with_name('compila_fs_translate.py')
TRANSLATE_RECIPE=HERE.parents[1]/'sorgenti/fs-translate.S'


def source_identities():
    paths=[HERE,Path(B.__file__),Path(B.A.__file__),Path(F.__file__),Path(L.__file__),Path(R.__file__),Path(M.__file__),
        Path(C.__file__),Path(C.C.__file__),Path(C.C.C.__file__),C.C.C.LOADER,C.RECIPE,C.C.RECIPE,TRANSLATE_BUILDER,TRANSLATE_RECIPE]
    return {str(path.relative_to(SOURCE)):R.sha(path.read_bytes())for path in paths}


def verify_recipe(directory,builder,reader,reference):
    directory=Path(directory);manifest=json.loads((directory/'manifesto.json').read_bytes())
    need(manifest['builder_sha256']==R.sha(Path(builder.__file__).read_bytes())and
         manifest['recipe_sha256']==R.sha(builder.RECIPE.read_bytes())and
         manifest['resource_reader_sha256']==R.sha(Path(reader.__file__).read_bytes()),'recipe source/reader identity')
    need(manifest['compiler_sha256']==C.C.CC_SHA and manifest['layout_passed']is True and
         all(x['exit_code']==0 for x in manifest['commands']),'completed authenticated recipe/layout')
    need(manifest['source_sha256']==C.C.SOURCES and
         manifest['layout_helper_sha256']==R.sha(Path(C.C.C.__file__).read_bytes())and
         manifest['loader_sha256']==R.sha(C.C.C.LOADER.read_bytes()),'recipe source/helper provenance')
    for relative,digest in {**manifest['source_sha256'],**manifest['header_sha256']}.items():
        need(R.sha((reference/relative).read_bytes())==digest,'original SDK source/header drift')
    blobs=builder.objects(directory)
    for name in blobs:need(manifest['objects'][name]['object_sha256']==R.file_sha(directory/(name+'.o')),'retained ELF identity '+name)
    if builder is C:need(manifest['parent_builder_sha256']==C.PARENT_SHA,'pinned shared builder identity')
    return blobs,R.file_sha(directory/'manifesto.json')


def verify_translate(directory,reference):
    directory=Path(directory);manifest=json.loads((directory/'manifesto.json').read_bytes())
    need(manifest['builder_sha256']==R.sha(TRANSLATE_BUILDER.read_bytes())and
         manifest['recipe_sha256']==R.sha(TRANSLATE_RECIPE.read_bytes())and
         manifest['compiler_sha256']==C.C.CC_SHA and manifest['loader_sha256']==R.sha(C.C.C.LOADER.read_bytes()),'retained Translate recipe identity')
    ref=manifest['reference'];need(ref['pin']==C.C.C.PIN and ref['layout_passed']is True and
        all(x['exit_code']==0 for x in manifest['commands']),'retained Translate original layout')
    need(ref['source_sha256']==R.sha((reference/'lib/NitroSDK/src/fs/FS_command.c').read_bytes()),'Translate source drift')
    for relative,digest in ref['header_sha256'].items():need(R.sha((reference/relative).read_bytes())==digest,'Translate header drift')
    need(manifest['private_header_sha256']==R.sha((reference/'lib/NitroSDK/src/fs/fs_private.h').read_bytes()),'Translate private header drift')
    loader=C.load(C.C.C.LOADER,'cached_find_retained_text')
    obj=directory/'fs-translate-command.o';symbol='native_fs_translate_command_recipe'
    blob,symbols=loader.load_text(obj.read_bytes(),0x20d68c0,(symbol,))
    need(symbols[symbol]==0x20d68c0 and len(blob)==400 and R.sha(blob)==L.NEW['translate'][2]and
         manifest['objects']['command']['object_sha256']==R.file_sha(obj),'retained Translate ELF entry/bytes')
    return blob,R.file_sha(directory/'manifesto.json')


def prepare(args):
    receipt,parts=L.prepare(args.rom,args.snapshot)
    frozen=json.loads(args.input_contract.read_bytes())
    need(B.wire(frozen)==B.wire(F.freeze(receipt,parts)),'exact frozen source/input/resource contract')
    reference=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(reference),'rev-parse','HEAD'],text=True).strip()==C.C.C.PIN and
         not subprocess.check_output(['git','-C',str(reference),'status','--porcelain']),'clean pinned SDK reference')
    new,new_hash=verify_recipe(args.recipe_dir,C,L,reference)
    cached,cached_hash=verify_recipe(args.cached_recipe_dir,C.C,C.C.R,reference)
    translate,translate_hash=verify_translate(args.translate_recipe_dir,reference)
    for name,blob in {**cached,**new,'translate':translate}.items():need(parts[name]==blob,'installed bytes / recovered ELF '+name)
    inputs={'normal':F.make_input(parts),'precompleted_result':F.make_input(parts,True)}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        recipe_manifest_sha256=new_hash,cached_recipe_manifest_sha256=cached_hash,translate_recipe_manifest_sha256=translate_hash)
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'normal','normal_OFF','precompleted_result'},'complete three-run control matrix')
    need(all(raw['observed']is(name!='normal_OFF')for name,raw in raws.items()),'OFF observation binding')
    for name,raw in raws.items():B.require_run(inputs['normal'if name=='normal_OFF'else name],raw)
    normal,off,projected=raws['normal'],raws['normal_OFF'],raws['precompleted_result']
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(normal[key])==B.wire(off[key]),'OFF neutrality '+key)
        need(B.wire(normal[key])==B.wire(projected[key]),'convergent initial result projection '+key)
    need(normal['initial']==off['initial'] and normal['initial']!=projected['initial'],'input projection provenance')
    for key in('flow','reads'):need(normal[key]==projected[key],'same source route '+key)
    differences=[i for i,(a,b)in enumerate(zip(normal['stores'],projected['stores']))if a!=b]
    need(differences==[419,420],'two native result writer preimages')
    forged=copy.deepcopy(projected);forged['initial']=copy.deepcopy(normal['initial'])
    try:B.require_run(inputs['normal'],forged)
    except ValueError as error:need(str(error)=='source native stores','camouflage specifically native stores')
    else:raise ValueError('camouflaged precompleted result accepted')
    for index in(419,420):
        altered=copy.deepcopy(normal);del altered['stores'][index]
        try:B.require_run(inputs['normal'],altered)
        except ValueError as error:need(str(error)=='source native stores','deleted result writer specifically rejected')
        else:raise ValueError('deleted result writer accepted')
    return dict(OFF_pairs=1,convergent_result_pairs=1,different_store_preimages=differences,
        camouflage_rejected='source native stores',deleted_writer_rejections=[419,420])


def save(path,value):
    with Path(path).open('x')as stream:stream.write(json.dumps(value,indent=2)+'\n')


def verify_existing(directory,receipt,inputs,bindings):
    report=json.loads((directory/'report.json').read_bytes())
    need(report.get('schema')=='native-fs-cached-findpath-report-v1','native report schema')
    need(report['mode']in('probe','matrix') and report['CPU_executed']is True,'existing native report domain')
    need(B.wire(report['resources'])==B.wire(receipt)and B.wire(report['bindings'])==B.wire(bindings),'existing native resource/source/recipe binding')
    names=['normal']if report['mode']=='probe'else['normal','normal_OFF','precompleted_result']
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
    for name in('rom','recipe-dir','cached-recipe-dir','translate-recipe-dir','reference','input-contract','out-dir'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--raw-dir',type=Path);args=p.parse_args()
    try:
        need((args.mode=='verify')==(args.raw_dir is not None),'--raw-dir required only in verify mode')
        need(args.out_dir.resolve()!=SOURCE and SOURCE not in args.out_dir.resolve().parents,'private raw output outside source required')
        need(not args.out_dir.exists()and not args.out_dir.is_symlink(),'fresh private output directory required')
        receipt,inputs,predictions,bindings=prepare(args)
        args.out_dir.mkdir(parents=True)
        report=dict(schema='native-fs-cached-findpath-report-v1',mode=args.mode,resources=receipt,bindings=bindings,CPU_executed=False,raw=[])
        save(args.out_dir/'prepared.json',report)
        if args.mode=='prepare':print('Prepared and predicted, no CPU/compiler');return
        if args.mode=='verify':
            save(args.out_dir/'verification.json',verify_existing(args.raw_dir,receipt,inputs,bindings));print('Existing raw verified; no CPU/compiler');return
        save(args.out_dir/'SOURCE-BEFORE-CPU.json',source_identities())
        names=('normal',)if args.mode=='probe'else('normal','normal_OFF','precompleted_result');raws={}
        for name in names:
            key='normal'if name=='normal_OFF'else name;f=inputs[key]
            raw=B.run(f,B.observation_policy(predictions[key]),observe=name!='normal_OFF')
            path=args.out_dir/(name+'.json');save(path,raw) # Always before verdict.
            B.require_run(f,raw);raws[name]=raw
            report['raw'].append(dict(name=name,file=path.name,sha256=R.file_sha(path)))
            need(source_identities()==bindings['source_sha256'],'runtime source changed during native execution')
        report['CPU_executed']=True;report['controls']=None if args.mode=='probe'else controls(raws,inputs)
        report['verdict']='PASS within declared isolated cached FindPath scope';save(args.out_dir/'report.json',report)
    except(ValueError,OSError,EOFError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print(args.mode,'PASS; full native FindPath returned, zero models/runtime host writes')


if __name__=='__main__':main()
