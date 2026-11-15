#!/usr/bin/env python3
"""Prepare/execute/verify the whole original PP getter with native NARC/SDK.

The PP1 profile changes one declared input-memory byte. It never patches the
ROM, forces R0, substitutes an SDK response or reinjects state between calls.
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
D=load(HERE.with_name('attribuisci_fs_memory_narc.py'),'PP_retained_verification')
B=load(HERE.parents[1]/'test/pp_memory_bench.py','PP_complete_native_bench')
F,L,R,M,need=B.F,B.L,B.R,B.M,B.need
PARENT_SHA='e24fb7cfcd2a62cccdc3d27692ce2c6035c18a853c864ea570223ca7169339df'


def source_identities():
    ids=D.source_identities()
    paths=(HERE,Path(B.__file__),Path(B.A.__file__),Path(F.__file__),Path(L.__file__),HERE.with_name('qualifica_dispatch_pp.py'))
    ids.update({str(p.relative_to(SOURCE)):R.sha(p.read_bytes())for p in paths});return ids


def prepare(args):
    need(R.sha(Path(D.__file__).read_bytes())==PARENT_SHA,'qualified NARC verifier drift')
    receipt,parts=L.prepare(args.rom,args.snapshot)
    need(B.wire(json.loads(args.input_contract.read_bytes()))==B.wire(F.freeze(receipt,parts)),'exact frozen PP contract')
    q=D.D;ref=args.reference.resolve()
    need(subprocess.check_output(['git','-C',str(ref),'rev-parse','HEAD'],text=True).strip()==q.PIN and
         not subprocess.check_output(['git','-C',str(ref),'status','--porcelain']),'clean pinned PP SDK/game reference')
    dependencies={**q.SDK_FILES,'src/filesystem.c':L.L.SOURCE_SHA,'src/move.c':L.SOURCE_SHA}
    for name,digest in dependencies.items():need(R.sha((ref/name).read_bytes())==digest,'PP source/header drift '+name)
    for name,digest in q.RECIPE_FILES.items():need(R.sha((SOURCE/name).read_bytes())==digest,'PP retained recipe drift '+name)
    objects=json.loads(args.objects.read_bytes())
    need(type(objects)is dict and set(objects)==set(q.SYMBOLS)and all(type(p)is str for p in objects.values()),'exact thirty PP native ELF paths')
    generic=q.D.D.verify_objects
    proof=types.FunctionType(generic.__code__,{**vars(q.D.D),'L':q.L,'SYMBOLS':q.SYMBOLS})(objects,parts)
    recipe=q.verify_recipe(args.recipe_dir,ref)
    for name in q.C.BODIES:need(proof[name]['object_sha256']==recipe['objects'][name]['object_sha256'],'PP native ELF/recipe receipt '+name)
    inputs={'normal':F.make_input(parts),'PP1':F.make_input(parts,1)}
    predictions={name:B.predict(f)for name,f in inputs.items()}
    bindings=dict(source_sha256=source_identities(),input_contract_sha256=R.file_sha(args.input_contract),
        objects_sha256=R.file_sha(args.objects),ELF=proof,SDK_pin=q.PIN,SDK_files=dependencies,
        recipe_manifest_sha256=R.file_sha(args.recipe_dir/'manifesto.json'),project_driver_mapped=False,
        native_Thumb_compiler_origin='Original Metrowerks/object missing; source candidates and installed bytes separately identified')
    return receipt,inputs,predictions,bindings


def controls(raws,inputs):
    need(set(raws)=={'normal','normal_OFF','PP1'},'complete PP matrix')
    for name,raw in raws.items():
        need(raw['observed']is(name!='normal_OFF'),'PP OFF observation binding')
        B.require_run(inputs['normal'if name=='normal_OFF'else name],raw)
    normal,off,counter=(raws[x]for x in('normal','normal_OFF','PP1'))
    for key in('returned','stop_pc','final_map_sha256','final_pages'):
        need(B.wire(normal[key])==B.wire(off[key]),'PP OFF neutrality '+key)
    need(normal['initial']==off['initial']and normal['initial']!=counter['initial'],'PP input projection provenance')
    need(normal['returned'][0]==15 and counter['returned'][0]==1 and normal['returned'][1:]==counter['returned'][1:],'PP scalar depends on input, other final context preserved')
    need([x['pc']for x in normal['flow']]==[x['pc']for x in counter['flow']],'PP input projection preserves code path')
    for key in('reads','stores'):
        need([(x['pc'],x['address'],x['bytes'])for x in normal[key]]==[(x['pc'],x['address'],x['bytes'])for x in counter[key]],'PP projection preserves access route '+key)
    read_diff=[i for i,(a,b)in enumerate(zip(normal['reads'],counter['reads']))if a!=b]
    store_diff=[i for i,(a,b)in enumerate(zip(normal['stores'],counter['stores']))if a!=b]
    need(read_diff==[1583,1734]and store_diff==[1211],'before-CPU source forecast PP data access differences')
    need([(normal['reads'][i]['pc'],normal['reads'][i]['address'],normal['reads'][i]['bytes'])for i in read_diff]==[(0x20d4b78,F.P.P.MEMBER_SOURCE+4,4),(0x2073390,F.DEST+6,1)],'copy reads the PP word then getter reads the PP byte')
    need((normal['stores'][1211]['pc'],normal['stores'][1211]['address'],normal['stores'][1211]['bytes'])==(0x20d4b7c,F.DEST+4,4),'PP source-dependent native copy writer')
    left={x['ram']:bytes.fromhex(x['hex'])for x in normal['final_pages']};right={x['ram']:bytes.fromhex(x['hex'])for x in counter['final_pages']}
    need(left.keys()==right.keys(),'same PP page owners')
    delta=sorted((base+i,a,b)for base in left for i,(a,b)in enumerate(zip(left[base],right[base]))if a!=b)
    need(delta==sorted(((F.P.P.MEMBER_SOURCE+6,15,1),(F.DEST+6,15,1))),'only source input and native buffer PP bytes differ finally')
    cases=[]
    forged=copy.deepcopy(counter);forged['initial']=copy.deepcopy(normal['initial']);cases.append(('input_camouflage',inputs['normal'],forged,'source full16 PP return ABI'))
    forged=copy.deepcopy(counter);forged['returned'][0]=15;cases.append(('scalar_camouflage',inputs['PP1'],forged,'source full16 PP return ABI'))
    forged=copy.deepcopy(counter);forged['reads'][1734]['hex']='0f';cases.append(('wrong_leaf_read',inputs['PP1'],forged,'source PP native reads'))
    forged=copy.deepcopy(counter);del forged['reads'][1734];cases.append(('missing_leaf_read',inputs['PP1'],forged,'source PP native reads'))
    forged=copy.deepcopy(counter);forged['stores'][1211]['value']=normal['stores'][1211]['value'];cases.append(('wrong_copy_word',inputs['PP1'],forged,'source PP native stores'))
    forged=copy.deepcopy(counter);del forged['stores'][1211];cases.append(('missing_copy_word',inputs['PP1'],forged,'source PP native stores'))
    rejected=[]
    for label,f,forged,reason in cases:
        try:B.require_run(f,forged)
        except ValueError as e:need(str(e)==reason,'PP forgery rejected at declared check '+label);rejected.append(dict(name=label,reason=reason))
        else:raise ValueError('PP forgery accepted '+label)
    return dict(OFF_pairs=1,PP_input_pairs=1,native_scalar_results=[15,1],read_differences=read_diff,store_differences=store_diff,
        final_byte_differences=delta,forgeries=rejected,original_ROM_instructions=6287,ARM_instructions=6159,Thumb_instructions=128)


def save(path,value):
    with Path(path).open('x')as f:json.dump(value,f,indent=2);f.write('\n')


def verify_existing(directory,receipt,inputs,bindings):
    report=json.loads((directory/'report.json').read_bytes())
    need(report.get('schema')=='native-PP-memory-report-v1'and report['mode']in('probe','matrix')and report['CPU_executed']is True,'PP completed report')
    need(B.wire(report['resources'])==B.wire(receipt)and B.wire(report['bindings'])==B.wire(bindings),'existing PP resource/source/recipe binding')
    names=['normal']if report['mode']=='probe'else['normal','normal_OFF','PP1']
    need([x['name']for x in report['raw']]==names,'exact ordered PP raw manifest')
    raws={}
    for row in report['raw']:
        need(row['file']==row['name']+'.json','bounded PP raw filename')
        path=directory/row['file'];need(not path.is_symlink()and R.file_sha(path)==row['sha256'],'PP raw identity')
        raw=json.loads(path.read_bytes());B.require_run(inputs['normal'if row['name']=='normal_OFF'else row['name']],raw);raws[row['name']]=raw
    evidence=None if report['mode']=='probe'else controls(raws,inputs)
    need(B.wire(evidence)==B.wire(report['controls']),'existing PP control verdict')
    return dict(verified_report_sha256=R.file_sha(directory/'report.json'),raw_files=len(raws),controls=evidence,CPU_executed=False,compiler_invoked=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=('prepare','probe','matrix','verify'),required=True)
    for name in('rom','objects','recipe-dir','reference','input-contract','out-dir'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--snapshot',type=Path);p.add_argument('--raw-dir',type=Path);a=p.parse_args()
    try:
        need((a.mode=='verify')==(a.raw_dir is not None),'--raw-dir required only in verify mode')
        out=a.out_dir.resolve();need(out!=SOURCE and SOURCE not in out.parents,'private PP output outside source')
        need(not a.out_dir.exists()and not a.out_dir.is_symlink(),'fresh private PP output directory')
        receipt,inputs,predictions,bindings=prepare(a);a.out_dir.mkdir(parents=True)
        report=dict(schema='native-PP-memory-report-v1',mode=a.mode,resources=receipt,bindings=bindings,CPU_executed=False,raw=[])
        save(a.out_dir/'prepared.json',report)
        if a.mode=='prepare':print('Whole PP getter prepared/predicted, no CPU/compiler');return
        if a.mode=='verify':save(a.out_dir/'verification.json',verify_existing(a.raw_dir,receipt,inputs,bindings));print('PP raw verified, no CPU/compiler');return
        save(a.out_dir/'SOURCE-BEFORE-CPU.json',source_identities())
        names=('normal',)if a.mode=='probe'else('normal','normal_OFF','PP1');raws={}
        for name in names:
            key='normal'if name=='normal_OFF'else name;f=inputs[key]
            raw=B.run(f,B.observation_policy(predictions[key]),observe=name!='normal_OFF')
            path=a.out_dir/(name+'.json');save(path,raw) # Preserve before verdict.
            B.require_run(f,raw);raws[name]=raw
            report['raw'].append(dict(name=name,file=path.name,sha256=R.file_sha(path)))
            need(source_identities()==bindings['source_sha256'],'PP source changed during execution')
        report['CPU_executed']=True;report['controls']=None if a.mode=='probe'else controls(raws,inputs)
        report['verdict']='PASS within whole native PP getter / hybrid memory archive scope';save(a.out_dir/'report.json',report)
    except(ValueError,OSError,EOFError,subprocess.SubprocessError)as e:p.exit(2,str(e)+'\n')
    print(a.mode,'PASS; original PP getter, zero service models/runtime host writes')


if __name__=='__main__':main()
