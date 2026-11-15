#!/usr/bin/env python3
"""Attribute native relative FindPath with captured caller inputs, in isolated CPUs.

A declared BSS root fixture and Send4 ID model do not establish boot, native
FindPathCommand/queue/card completion, or integration in the complete caller.
"""
from pathlib import Path
import copy,gc,gzip,importlib.util,json,mmap,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('find_complete_caller_parent',Path(__file__).with_name('attribuisci_fs_read_chiamante.py'))
B=load('find_native_profile',Path(__file__).parents[1]/'test/fs_find_bench.py')
L=load('find_independent_readback',Path(__file__).with_name('rileggi_fs_find.py'))
P,need,sha=H.P,H.need,H.sha
PARENT_SHA='0ec5cd58a22098274f4c1661f363c88f48864d10ef0e5bcb33a9fe155c92c11f'
need(sha(Path(H.__file__).read_bytes())==PARENT_SHA,'Find complete caller parent drift')


def source_identities():
    result=H.source_identities()
    for p in(__file__,B.__file__,L.__file__,L.C.__file__,L.C.RECIPE if isinstance(L.C.RECIPE,Path)else Path(__file__).parents[1]/'sorgenti/fs-find.S'):
        path=Path(p);result[str(path.resolve().relative_to(P.SOURCE))]=sha(path.read_bytes())
    return result


def wire(value):
    """Canonical JSON containers, preserving bool/int/float distinctions."""
    return json.dumps(value,sort_keys=True,separators=(',',':'))


def read_report(path):
    need(path.stat().st_size<=8*1024**2,'Find bounded stored parent report')
    if path.suffix=='.gz':
        with gzip.open(path,'rb')as fd:blob=fd.read(32*1024**2+1)
    else:blob=path.read_bytes()
    need(len(blob)<=32*1024**2,'Find bounded expanded parent report');return json.loads(blob)


def prepare(rom,language,parent_report,objects,strategy_object,read_recipe,wait_recipe,recipe_dir):
    parent=read_report(parent_report)
    need(parent['schema']=='trainer31-native-fs-read-caller-v1'and parent['language']==language and
         parent['cpu_executed']is True and parent['probe_only']is False and
         parent['source_sha256']==H.source_identities()and parent['recipes']==H.RECIPES and
         parent['namespace_bindings']==H.BINDINGS,'Find authenticated complete caller receipt/source/recipe domain')
    need([(r['plus'],r['seed'])for r in parent['positives']]==[(p,s)for p in(0,1)for s in(0x12345678,0x12345679)],
         'Find four distinct source parent cells')
    model=P.G.S.SHARED.read_current(rom,language);fixtures=[]
    with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        q,parent_proof=H.qualify(model,raw,language,objects,strategy_object,read_recipe,wait_recipe)
        need(wire(parent_proof)==wire(parent['proof'])and wire(parent['input'])==wire(model['record']),
             'Find parent proof and exact input match independent current readback')
        data=H.H.resources(model,raw,language);view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
        body=view.read(B.ENTRY,324)
        need(body==P.G.piece(model['segments'],B.ENTRY,324)==L.object_text(recipe_dir/'fs-find-path.o',324,L.C.BODIES['path'][2]),
             'Find independent physical/decoded/ELF body')
        recipe_manifest=recipe_dir/'manifesto.json';receipt=json.loads(recipe_manifest.read_bytes())
        need(receipt['builder_sha256']==sha(Path(L.C.__file__).read_bytes())and
             receipt['recipe_sha256']==sha((Path(__file__).parents[1]/'sorgenti/fs-find.S').read_bytes())and
             receipt['source_recipe']==L.C.RECIPE and receipt['objects']['path']['object_sha256']==sha((recipe_dir/'fs-find-path.o').read_bytes())and
             receipt['reference']['pin']==L.C.D.C.PIN and receipt['reference']['layout_passed']is True and
             receipt['recipe_is_recovered']is True and receipt['original_compiler_reconstructed']is False,
             'Find original-header/layout/compiler recipe receipt tied to current object and project source')
        off9=struct.unpack_from('<I',raw,0x20)[0];params=struct.unpack_from('<9I',raw,off9+0xBA0)
        need(struct.unpack_from('<I',body,320)[0]==B.CURRENT and params[3]<=B.CURRENT and B.CURRENT+12<=params[4]and
             not view.has(B.CURRENT,12),'Find literal identifies BSS with no initialized-ROM mapping')
        fnt_off,fnt_n=struct.unpack_from('<2I',raw,0x40)
        need(0<fnt_n<=1024**2 and fnt_off+fnt_n<=len(raw),'Find bounded actual FNT extent')
        fnt=bytes(raw[fnt_off:fnt_off+fnt_n]);need(view.read(B.PATH,8)==b'a/0/1/1\0','Find actual readonly caller path')
        for ordinal,r in enumerate(parent['positives']):
            H.require_case(r,data,q)
            p=r['pp_reader'];event=p['models'][0];before=next(x['regs']for x in r['convert']['flow']if x['pc']=='0x20d81a8')
            entry=list(before);entry[14]=0x20D81AC
            need(entry==event['entry']and B.B.u32s(entry),'Find actual model entry equals original native Convert BL context')
            frame=bytes.fromhex(r['convert']['inner_init']['frame_after']);guard=bytes.fromhex(p['stack_guard_before'])
            need(len(guard)==56 and len(frame)==240 and guard.hex()==p['stack_guard_after']and
                 frame[:72].hex()==event['dir_before_hex'],'Find preserved lower guard and actual pre-Find directory frame')
            f=dict(ordinal=ordinal,plus=r['plus'],seed=r['seed'],entry=entry,frame=(guard[-40:]+frame).hex(),path='a/0/1/1',
                current_dir=struct.pack('<3I',B.ARC,0,0).hex(),file_id=data['pp_reader']['11']['oracle']['file_id'],
                destination_before=event['before_hex'],provenance=dict(entry='Actual P64 model entry16; original Convert BL checked',
                    frame='Last40 of actual preserved guard56 plus actual Init frame240; no intervening writes',
                    current_dir='Declared source first-archive root12 fixture, not captured boot/runtime state',
                    natural_capture=False,parent_report_sha256=sha(parent_report.read_bytes())))
            B.check_fixture(f);B.require_fnt(f,fnt);fixtures.append(f)
        proof=dict(recipe_receipt_sha256=sha(recipe_manifest.read_bytes()),recipe_receipt=receipt,parent_input=model['record'],parent_report_sha256=sha(parent_report.read_bytes()),
            parent_positive_cells=4,parent_semantic_replay_without_CPU=True,parent_source_sha256=PARENT_SHA,
            component=dict(ram=hex(B.ENTRY),rom_offset=hex(view.offset(B.ENTRY,324)),bytes=324,instruction_bytes=320,
                sha256=sha(body),object_sha256=sha((recipe_dir/'fs-find-path.o').read_bytes())),
            global_input=dict(address=hex(B.CURRENT),bytes=12,kind='BSS',static_start=hex(params[3]),static_end=hex(params[4]),
                initialized_ROM_mapping=False,source_derived_root_fixture=True,boot_observed=False),
            FNT=dict(rom_offset=hex(fnt_off),bytes=fnt_n,sha256=sha(fnt),path='a/0/1/1',file_id=140),
            frame=dict(api_SP=hex(B.DIR),isolated_frame=280,native_additional_stack=40,
                future_parent_global_peak=600,old_global_bound=608,parent_integration_qualified=False))
    del model;gc.collect();return fixtures,body,fnt,proof


def save(path,value):
    need(not path.exists()and not path.is_symlink()and P.SOURCE not in path.resolve().parents,
         'Find fresh private output outside source required')
    payload=json.dumps(value,separators=(',',':')).encode();need(len(payload)<=32*1024**2,'Find expanded output budget')
    blob=gzip.compress(payload,mtime=0)if path.suffix=='.gz'else payload;need(len(blob)<=8*1024**2,'Find stored output budget')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb')as fd:fd.write(blob)


def require_off_pair(on,off,body,fnt):
    B.require_result(on,body,fnt);B.require_result(off,body,fnt)
    need(on['observe']is True and off['observe']is False,'Find actual paired OFF domain')
    ignored={'observe','flow','stores','reads'}
    need({k:v for k,v in on.items()if k not in ignored}=={k:v for k,v in off.items()if k not in ignored},
         'Find OFF complete registers/models/frame/whole RAM equal without any projection')
    return True


def counter_rejection(counter,normal,body,fnt):
    B.require_result(counter,body,fnt);B.require_result(normal,body,fnt)
    need(counter['policy']==dict(send=0,clobber=False)and normal['policy']==dict(send=1,clobber=False)and
         counter['fixture']==normal['fixture']and counter['returned'][0]==0 and normal['returned'][0]==1 and
         all(counter[k]==normal[k]for k in('frame_after','destination_after','whole_ram_sha256','current_dir_after','path_after')),
         'Find native FALSE return after identical ID8 delivery and whole RAM')
    disguised=copy.deepcopy(counter);disguised['policy']['send']=1
    try:B.require_result(disguised,body,fnt)
    except ValueError as error:return str(error)
    raise ValueError('Find FALSE counter accepted as positive after policy disguise')


def analyze(rom,language,parent_report,objects,strategy_object,read_recipe,wait_recipe,recipe_dir,raw_dir=None,prepare_only=False,probe=False):
    H.R.W.require_host_budget();sources=source_identities()
    fixtures,body,fnt,proof=prepare(rom,language,parent_report,objects,strategy_object,read_recipe,wait_recipe,recipe_dir)
    result=dict(schema='native-fs-find-isolated-v1',language=language,proof=proof,source_sha256=sources,fixtures=fixtures,
                cpu_executed=False,compiler_invoked=False,root_fixture_is_declared=True,parent_integration=False)
    if not prepare_only:
        need(raw_dir is not None and not raw_dir.exists()and P.SOURCE not in raw_dir.resolve().parents,
             'Find fresh private raw directory before guest required');raw_dir.mkdir(parents=True)
        cases=[];counters=[];grid=[('normal',{}),('off',dict(observe=False)),('send0',dict(send_value=0)),
            ('send2',dict(send_value=2)),('clobber',dict(clobber=True)),('fill39',dict(fill=0x39))]
        selected=[fixtures[2]]if probe else fixtures
        for f in selected:
            normal=None
            for label,kwargs in grid[:1]if probe else grid:
                observed=B.run(f,body,fnt,**kwargs)
                save(raw_dir/('%d-%s.json.gz'%(f['ordinal'],label)),observed)
                B.require_result(observed,body,fnt);cases.append(dict(ordinal=f['ordinal'],label=label,result=observed))
                if label=='normal':normal=observed
                elif label=='off':require_off_pair(normal,observed,body,fnt)
                elif label=='send0':counters.append(dict(ordinal=f['ordinal'],rejection=counter_rejection(observed,normal,body,fnt),policy_disguised=True))
                else:need(observed['frame_after']==normal['frame_after']and observed['destination_after']==normal['destination_after'],
                          'Find control retains all frame/ID bytes')
            print(language,'Find fixture',f['ordinal'],'raw then source oracles verified',flush=True)
        result.update(cpu_executed=True,probe_only=probe,cases=cases,counters=counters,
            limits=['Isolated copied actual caller inputs, not complete parent CPU or natural activation',
                'BSS root12 declared from source initialization; native boot and FSArchive not reconstructed',
                'Send4 resolves actual ARG path via raw FNT and writes ID8 only; native command/error/queue/card completion excluded',
                '320 ARM instruction bytes plus data-only literal4; no original MW compiler history',
                'Relative a/0/1/1/file-result only; absolute/colon/directory/archive lookup branches unexercised',
                'Unicorn2.1.4 CPU17 Cortex-A15 instruction semantics, not ARM946 silicon/timing/IRQ delivery'])
    need(source_identities()==sources,'Find sources changed during execution');H.R.W.require_host_budget();return result


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('rom','parent-report','objects','strategy-object','read-recipe','wait-recipe','recipe-dir','raw-dir'):
        p.add_argument('--'+name,type=Path)
    p.add_argument('--language',choices=('EN','IT'));p.add_argument('--json',type=Path,required=True)
    modes=p.add_mutually_exclusive_group()
    modes.add_argument('--prepare-only',action='store_true');modes.add_argument('--probe',action='store_true')
    modes.add_argument('--conditional-capability',action='store_true',help='own four-instruction CMPNE qualification; no ROM required')
    a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and P.SOURCE not in a.json.resolve().parents,'Find fresh private report required')
        if a.conditional_capability:
            need(a.raw_dir is not None and not a.raw_dir.exists()and P.SOURCE not in a.raw_dir.resolve().parents,'Find fresh private capability raw directory')
            a.raw_dir.mkdir(parents=True);rows=B.collect_conditional_capability();save(a.raw_dir/'cmpne.json.gz',rows)
            B.require_conditional(rows);result=dict(schema='native-fs-find-conditional-v1',rows=rows,source_sha256=source_identities(),compiler_invoked=False)
        else:
            need(a.language and all(getattr(a,name)for name in('rom','parent_report','objects','strategy_object','read_recipe','wait_recipe','recipe_dir')),
                 'Find ROM/language/parent report/project objects and recovered recipes required')
            result=analyze(a.rom,a.language,a.parent_report,a.objects,a.strategy_object,a.read_recipe,a.wait_recipe,a.recipe_dir,
                           a.raw_dir,a.prepare_only,a.probe)
        save(a.json,result)
    except ValueError as error:p.exit(2,str(error)+'\n')
    print('Find source/ROM verification finished; qualified scope recorded')


if __name__=='__main__':main()
