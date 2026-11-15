#!/usr/bin/env python3
"""Prepare/replay a complete isolated cached SeekDir with owned exact ROM input."""
from pathlib import Path
import argparse
import copy
import importlib.util
import json
import subprocess


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


HERE=Path(__file__).resolve()
B=load(HERE.parents[1]/'test/fs_cached_seekdir_bench.py','cached_seekdir_native_bench')
C=load(HERE.with_name('compila_fs_cached_seekdir.py'),'cached_seekdir_native_recipe')
F,R,need=B.F,B.R,B.need


def source_identities():
    paths=[HERE,Path(B.__file__),Path(F.__file__),Path(R.__file__),Path(C.__file__),Path(C.C.__file__),C.RECIPE,C.C.LOADER]
    return {str(p.relative_to(C.SOURCE)):R.sha(p.read_bytes())for p in paths}


def prepare(rom,snapshot,recipe_dir,reference,contract):
    receipt,parts=R.prepare(rom,snapshot)
    frozen=json.loads(Path(contract).read_bytes())
    need(F.wire(frozen)==F.wire(F.freeze(receipt,parts)),'exact frozen input/source/resource contract')
    manifest=json.loads((Path(recipe_dir)/'manifesto.json').read_bytes())
    need(manifest['builder_sha256']==R.sha(Path(C.__file__).read_bytes())and
         manifest['recipe_sha256']==R.sha(C.RECIPE.read_bytes())and
         manifest['layout_helper_sha256']==R.sha(Path(C.C.__file__).read_bytes())and
         manifest['loader_sha256']==R.sha(C.C.LOADER.read_bytes()),'retained recipe source drift')
    need(manifest['compiler_sha256']==C.CC_SHA and manifest['layout_passed']is True and
         all(x['exit_code']==0 for x in manifest['commands']),'authenticated completed recipe/layout')
    reference=Path(reference).resolve()
    need(subprocess.check_output(['git','-C',str(reference),'rev-parse','HEAD'],text=True).strip()==C.C.PIN and
         not subprocess.check_output(['git','-C',str(reference),'status','--porcelain']),'current clean pinned SDK')
    need(manifest['source_sha256']==C.SOURCES,'recorded original source identities')
    for rel,digest in {**C.SOURCES,**manifest['header_sha256']}.items():need(R.sha((reference/rel).read_bytes())==digest,'original source/header drift '+rel)
    code=C.objects(recipe_dir)
    for name,blob in code.items():
        need(parts[name]==blob and manifest['objects'][name]['object_sha256']==R.sha((Path(recipe_dir)/(name+'.o')).read_bytes()),'native bytes/retained ELF '+name)
    inputs={'root':F.make_input(parts),'root_precompleted':F.make_input(parts,precompleted=True),'directory1':F.make_input(parts,own_id=1)}
    return receipt,inputs,dict(input_contract_sha256=R.file_sha(contract),recipe_manifest_sha256=R.file_sha(Path(recipe_dir)/'manifesto.json'),source_sha256=source_identities())


def require_controls(raws,inputs):
    need(set(raws)=={'root','root_OFF','root_precompleted','directory1'},'complete finite control matrix')
    need(all(raws[name]['observed']is (name!='root_OFF')for name in raws),'OFF observation binding')
    for name,raw in raws.items():B.require_run(inputs['root'if name=='root_OFF'else name],raw)
    root,off,projected=raws['root'],raws['root_OFF'],raws['root_precompleted']
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(F.wire(root[key])==F.wire(off[key]),'OFF neutrality '+key)
        need(F.wire(root[key])==F.wire(projected[key]),'convergent projection '+key)
    need(root['initial']==off['initial'] and root['initial']!=projected['initial'],'OFF/projection initial distinction')
    for key in('flow','reads'):need(root[key]==projected[key],'convergent source '+key)
    diff=[i for i,(a,b)in enumerate(zip(root['stores'],projected['stores']))if a!=b]
    need(diff==[21,22,23,26],'four causal property preimages')
    forged=copy.deepcopy(projected);forged['initial']=copy.deepcopy(root['initial'])
    try:B.require_run(inputs['root'],forged)
    except ValueError as error:need(str(error)=='source native stores','camouflage must fail specifically on native stores')
    else:raise ValueError('camouflaged projection accepted')
    rejections=[]
    for index in(21,22,23,24,25,26):
        altered=copy.deepcopy(root);del altered['stores'][index]
        try:B.require_run(inputs['root'],altered)
        except ValueError as error:need(str(error)=='source native stores','missing writer rejection site');rejections.append(index)
        else:raise ValueError('missing property writer accepted')
    return dict(OFF_pairs=1,convergent_projection_pairs=1,different_store_preimages=diff,
                camouflaged_projection_rejected='source native stores',deleted_writer_rejections=rejections)


def save(path,value):
    with Path(path).open('x')as stream:stream.write(json.dumps(value,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('prepare','probe','matrix'),required=True)
    for name in('rom','recipe-dir','reference','input-contract','out-dir'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);a=p.parse_args()
    try:
        need(a.out_dir.resolve()!=C.SOURCE and C.SOURCE not in a.out_dir.resolve().parents,'private raw output must be outside source')
        need(not a.out_dir.exists() and not a.out_dir.is_symlink(),'fresh private output directory required')
        receipt,inputs,bindings=prepare(a.rom,a.snapshot,a.recipe_dir,a.reference,a.input_contract)
        a.out_dir.mkdir(parents=True)
        report=dict(schema='native-fs-cached-seekdir-report-v1',mode=a.mode,resources=receipt,bindings=bindings,raw=[],CPU_executed=False)
        save(a.out_dir/'prepared.json',report)
        if a.mode=='prepare':print('Prepared, source/recipe/input authenticated without CPU');return
        save(a.out_dir/'SOURCE-BEFORE-CPU.json',source_identities())
        names=('root',)if a.mode=='probe'else('root','root_OFF','root_precompleted','directory1')
        raws={}
        for name in names:
            f=inputs['root'if name=='root_OFF'else name]
            raw=B.run(f,observe=name!='root_OFF')
            path=a.out_dir/(name+'.json');save(path,raw) # raw before any verdict
            B.require_run(f,raw);raws[name]=raw
            report['raw'].append(dict(name=name,file=path.name,sha256=R.file_sha(path)))
            need(source_identities()==bindings['source_sha256'],'runtime source changed during guest')
        report['CPU_executed']=True
        report['controls']=None if a.mode=='probe'else require_controls(raws,inputs)
        report['verdict']='PASS within declared isolated cached scope'
        save(a.out_dir/'report.json',report)
    except (ValueError,OSError,EOFError,subprocess.SubprocessError)as error:p.exit(2,str(error)+'\n')
    print(a.mode,'PASS; original native function returned with zero model/host writes; raw saved first')


if __name__=='__main__':main()
