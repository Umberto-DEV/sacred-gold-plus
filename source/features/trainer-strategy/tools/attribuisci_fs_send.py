#!/usr/bin/env python3
"""Attribute isolated native Send4 queue preparation; ExecuteSync is value-only.

No native filesystem completion or integration in the complete caller is claimed.
The accessed archive fields are a declared source fixture, not captured boot state.
"""
from pathlib import Path
import ast,copy,gc,gzip,importlib.util,json,mmap,struct,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('send_qualified_parent_caller',Path(__file__).with_name('attribuisci_fs_find_chiamante.py'))
B=load('send_isolated_source_bench',Path(__file__).parents[1]/'test/fs_send_bench.py')
L=load('send_independent_readback',Path(__file__).with_name('rileggi_fs_send.py'))
P,need,sha,wire=H.P,H.need,H.sha,B.wire
PARENT_SHA='a2c0b332d2d566537fe30b40cd3379576b5d54340a707e49204103d0279b5373'
CAPTURE_SHA='90071ed9a1427119b4d9cb8af295805c678662f393aa1d83b0f5e77eeb2dcfeb'
need(sha(Path(H.__file__).read_bytes())==PARENT_SHA,'Send qualified parent verifier drift')


def source_identities():
    ids=H.source_identities()
    for path in(__file__,B.__file__,L.__file__,L.C.__file__,Path(__file__).parents[1]/'sorgenti/fs-send.S'):
        p=Path(path);ids[str(p.resolve().relative_to(P.SOURCE))]=sha(p.read_bytes())
    return ids


def require_parent_sources(parent,capture_source):
    current=H.source_identities();captured=parent['source_sha256'];key=str(Path(H.__file__).resolve().relative_to(P.SOURCE))
    if wire(current)==wire(captured):return dict(exact_current=True,oracle_only_revision=False)
    need(set(current)==set(captured)and [k for k in current if current[k]!=captured[k]]==[key]and
         captured[key]==CAPTURE_SHA and current[key]==PARENT_SHA and capture_source is not None,
         'Send historical parent requires its exact retained capture source and qualified oracle-only revision')
    old=Path(capture_source).read_bytes();new=Path(H.__file__).read_bytes()
    need(sha(old)==CAPTURE_SHA and sha(new)==PARENT_SHA,'Send authenticated parent capture/current source hashes')
    def split(blob):
        t=ast.parse(blob);nodes=[n for n in t.body if isinstance(n,ast.FunctionDef)and n.name=='require_find']
        need(len(nodes)==1,'Send parent has exactly one revised Find oracle');t.body.remove(nodes[0]);return ast.dump(t,include_attributes=False)
    need(split(old)==split(new),'Send parent producer/composition AST must be unchanged outside require_find')
    return dict(exact_current=False,oracle_only_revision=True,capture_sha256=CAPTURE_SHA,verifier_sha256=PARENT_SHA,
        changed_function='require_find',all_other_module_AST_unchanged=True)


def prepare(rom,language,parent_report,capture_source,objects,strategy_object,read_recipe,wait_recipe,find_recipe,recipe_dir):
    parent=H.N.read_report(parent_report);revision=require_parent_sources(parent,capture_source)
    need(parent['schema']=='trainer31-native-fs-find-caller-v1'and parent['language']==language and
         parent['cpu_executed']is True and parent['probe_only']is False and wire(parent['recipes'])==wire(H.RECIPES)and
         wire(parent['namespace_bindings'])==wire(H.BINDINGS),'Send parent complete matrix/source recipe receipt')
    need(wire([(r['plus'],r['seed'])for r in parent['positives']])==wire([(p,s)for p in(0,1)for s in(0x12345678,0x12345679)]),
         'Send four distinct actual parent cells')
    model=P.G.S.SHARED.read_current(rom,language);fixtures=[]
    with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        q,parent_proof=H.qualify(model,raw,language,objects,strategy_object,read_recipe,wait_recipe,find_recipe)
        need(wire(parent_proof)==wire(parent['proof'])and wire(parent['input'])==wire(model['record']),
             'Send parent exact image and independently reconstructed proof')
        data=H.resources(model,raw,language);view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
        bodies={address:view.read(address,n)for address,(n,digest)in B.BODIES.items()}
        obj=recipe_dir/'fs-send-command.o';receipt=json.loads((recipe_dir/'manifesto.json').read_bytes())
        need(bodies[B.ENTRY]==P.G.piece(model['segments'],B.ENTRY,420)==L.object_text(obj,420,B.BODY_SHA),
             'Send independent physical/decoded/recovered ELF agreement')
        need(receipt['builder_sha256']==sha(Path(L.C.__file__).read_bytes())and
             receipt['recipe_sha256']==sha((Path(__file__).parents[1]/'sorgenti/fs-send.S').read_bytes())and
             wire(receipt['source_recipe'])==wire(L.C.RECIPE)and receipt['objects']['command']['object_sha256']==sha(obj.read_bytes())and
             receipt['reference']['pin']==L.C.D.C.PIN and receipt['reference']['layout_passed']is True and
             receipt['reference']['layout_assertions']==L.C.LAYOUT and len(receipt['reference']['header_sha256'])==18 and
             receipt['reference']['source_sha256']=='4cc68728ca70d26fb620e996493b7b7ef259d07d8150aab607957851a502e587'and
             receipt['recipe_is_recovered']is True and receipt['original_compiler_reconstructed']is False,
             'Send authenticated recipe/compiler/original header-layout receipt')
        for ordinal,r in enumerate(parent['positives']):
            H.require_case(r,data,q);out=r['find'];service=out['services'][0];p=r['pp_reader']
            guard=bytes.fromhex(p['stack_guard_before']);frame=bytes.fromhex(service['frame_before'])
            need(len(guard)==56 and p['stack_guard_before']==p['stack_guard_after']and len(frame)==280 and
                 service==H.F.predict(out['fixture'])['services'][0],
                 'Send actual native Find service preimage, not pre-Find fixture or modeled output')
            f=dict(ordinal=ordinal,plus=r['plus'],seed=r['seed'],entry=service['entry'],frame=(guard[-24:]+frame).hex(),
                archive_before=B.ARCHIVE.hex(),provenance=dict(entry='Actual complete native Find→Send4 entry16',
                    frame='Actual Send280 plus24 preceding preserved guard bytes',archive='Declared92-byte source fixture with flag3/noActivate/empty list; not boot state',
                    natural_capture=False,parent_report_sha256=sha(parent_report.read_bytes())))
            B.check_fixture(f);B.initial_memory(f,bodies,0xA5);fixtures.append(f)
        proof=dict(parent_report_sha256=sha(parent_report.read_bytes()),parent_source_revision=revision,parent_input=model['record'],
            parent_positive_cells=4,parent_semantic_replay_without_CPU=True,parent_proof=parent_proof,
            components=[dict(ram=hex(a),rom_offset=hex(view.offset(a,n)),bytes=n,sha256=d)for a,(n,d)in B.BODIES.items()],
            recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=receipt,
            source_fixture=dict(archive=hex(B.ARC),archive_bytes=92,flag=3,proc_flag=0,list_empty=True,natural_boot=False),
            frame=dict(SP=hex(B.SP),isolated_frame=304,native_additional_stack=24,future_parent_peak=624,old_parent_bound=608,
                parent_integration_qualified=False),model_scope='ExecuteSync return value only; no ID delivery/Translate/Release/Next/completion')
    del model;gc.collect();return fixtures,bodies,proof


save=H.C.write_private


def require_off_pair(on,off,bodies):
    B.require_result(on,bodies);B.require_result(off,bodies)
    need(on['observe']is True and off['observe']is False and all(off[k]==[]for k in('flow','stores','reads')),'Send OFF transcript domain')
    a={k:v for k,v in on.items()if k not in('observe','flow','stores','reads')};b={k:v for k,v in off.items()if k not in('observe','flow','stores','reads')}
    need(wire(a)==wire(b),'Send OFF exact whole RAM and functional registers with no projection')
    return dict(neutral=True,whole_ram_sha256=on['whole_ram_sha256'],projection_bytes=0)


def counter_rejection(counter,normal,bodies):
    B.require_result(counter,bodies);B.require_result(normal,bodies)
    need(counter['policy']['execute']==0 and normal['policy']['execute']==1 and counter['returned'][0]==0 and normal['returned'][0]==1 and
         all(counter[k]==normal[k]for k in('fixture','entry','frame_after','archive_after','whole_ram_sha256')),
         'Send FALSE counter same native queue/state/fullRAM and genuinely different API return')
    disguised=copy.deepcopy(counter);disguised['policy']['execute']=1;disguised['services'][0]['result']=1
    try:B.require_result(disguised,bodies)
    except ValueError as error:return str(error)
    raise ValueError('Send FALSE boundary accepted as success after metadata disguise')


def analyze(rom,language,parent_report,capture_source,objects,strategy_object,read_recipe,wait_recipe,find_recipe,recipe_dir,
            raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),
         'Send nonoptimized Python and mutually exclusive strict modes required')
    H.R.W.require_host_budget();sources=source_identities()
    fixtures,bodies,proof=prepare(rom,language,parent_report,capture_source,objects,strategy_object,read_recipe,wait_recipe,find_recipe,recipe_dir)
    result=dict(schema='native-fs-send-isolated-v1',language=language,source_sha256=sources,proof=proof,fixtures=fixtures,
        cpu_executed=False,compiler_invoked=False,probe_only=probe,limits=['Isolated command4 idle/noActivate/empty-list source fixture only',
            'Actual native caller entry/frame, but new declared archive92 is not captured boot/installed archive state',
            'ExecuteSync value-only boundary; native file remains linked/busy/error2 and archive running',
            'Frame304/future global624 exceeds preceding608; no complete-caller integration qualified',
            'Unicorn2.1.4 CPU17 Cortex-A15 instruction semantics, not ARM946 silicon/timing/IRQ delivery'])
    if not prepare_only:
        need(raw_dir is not None and not raw_dir.exists()and not raw_dir.is_symlink()and P.SOURCE not in raw_dir.resolve().parents,'Send fresh private raw directory required before CPU')
        raw_dir.mkdir(parents=True);cases=[];off=[];counters=[];serial=0
        for f in(fixtures[:1]if probe else fixtures):
            normal=None
            policies=[('normal',{})]if probe else[('normal',{}),('off',dict(observe=False)),('false',dict(value=0)),
                ('truthy2',dict(value=2)),('clobber',dict(clobber=True)),('fill39',dict(fill=0x39))]
            for label,policy in policies:
                serial+=1;row=B.run(f,bodies,**policy)
                save(raw_dir/('%02d-%d-%s.json.gz'%(serial,f['ordinal'],label)),row)
                B.require_result(row,bodies);cases.append(dict(label=label,result=row))
                if label=='normal':normal=row
                elif label=='off':off.append(dict(ordinal=f['ordinal'],proof=require_off_pair(normal,row,bodies)))
                elif label=='false':counters.append(dict(ordinal=f['ordinal'],rejection=counter_rejection(row,normal,bodies),policy_disguised=True))
                elif label in('truthy2','clobber'):
                    need(row['frame_after']==normal['frame_after']and row['archive_after']==normal['archive_after']and
                         row['whole_ram_sha256']==normal['whole_ram_sha256'],'Send value/clobber control changes no queue RAM')
                print(language,f['ordinal'],label,'raw saved and source verified',flush=True)
        result.update(cpu_executed=True,cases=cases,observer_off=off,counters=counters)
    need(source_identities()==sources,'Send sources changed during preparation/execution');H.R.W.require_host_budget();return result


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('rom','parent-report','objects','strategy-object','read-recipe','wait-recipe','find-recipe','recipe-dir','json'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--parent-source',type=Path);p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--raw-dir',type=Path)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true')
    a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and P.SOURCE not in a.json.resolve().parents,'Send fresh private report outside source required')
        result=analyze(a.rom,a.language,a.parent_report,a.parent_source,a.objects,a.strategy_object,a.read_recipe,a.wait_recipe,a.find_recipe,
            a.recipe_dir,a.raw_dir,a.prepare_only,a.probe);save(a.json,result)
    except ValueError as error:p.exit(2,str(error)+'\n')
    print(a.language,'Send prepared without CPU'if a.prepare_only else'Send isolated source case verified; completion excluded')


if __name__=='__main__':main()
