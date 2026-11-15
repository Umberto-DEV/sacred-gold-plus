#!/usr/bin/env python3
"""Verify one ExecuteSync context with native callees and declared Translate model."""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,sys


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


J=load('native_sync_parent_cli',Path(__file__).with_name('attribuisci_fs_exec_sync_join.py'))
B=load('native_sync_bench',Path(__file__).parents[1]/'test/fs_exec_sync_native_callees_bench.py')
F=load('native_sync_freezer',Path(__file__).with_name('congela_fs_exec_sync_native_contract.py'))
need,sha,wire,save,read_report=J.need,J.sha,B.wire,J.save,J.read_report
need(sha(Path(J.__file__).read_bytes())=='6e7728f3544fcd69629d004f2a1d4cc76d9a15f34aa5333e3e5215ac143875de',
     'NativeSync qualified parent CLI drift')
POLICIES=[('normal',False,True),('off',False,False),('bypass_wake',True,True)]


def source_identities():
    ids=J.source_identities()
    for name in(__file__,B.__file__,F.__file__):
        p=Path(name);ids[str(p.resolve().relative_to(J.P.SOURCE))]=sha(p.read_bytes())
    return ids


def history(parent_config):
    """Resolve existing replay contracts; never infer private folder names."""
    c=J.read_config(parent_config);n=J.read_parent_config(c['parent_config'])
    q=J.N.read_config(n['parent_config']);w=J.N.H.read_config(q['parent_config'])
    release=J.N.H.J.read_config(w['parent_config'])
    paths=dict(join_report=c['report'],next_report=n['report'],composition_report=q['report'])
    settings={}
    for language in('EN','IT'):
        item=release[language]['prepare'];settings[language]=item
        e=J.N.H.J.H.read_parent_config(Path(item['parent_config']),Path(item['rom']),language)
        paths['exec_'+language.lower()]=Path(item['parent_report'])
        paths['send_'+language.lower()]=e['parent_report']
    return c,paths,settings


def share_groups(fixtures,bodies):
    groups=[];keys=[]
    for f in fixtures:
        image=B.initial_memory(f,bodies);key=(wire(f['entry']),image,f['translated_result'])
        if key not in keys:
            keys.append(key);groups.append(dict(ordinal=len(keys)-1,representative=f,members=[],initial_ram_sha256=sha(image),
                model_policy=dict(result=f['translated_result'],preserve_other_registers=True)))
        groups[keys.index(key)]['members'].append(dict(language=f['language'],ordinal=f['ordinal']))
    return groups


def require_complete_parent(r):
    need(r['schema']=='native-fs-exec-sync-join-isolated-v1'and r['cpu_executed']is True and
         r['compiler_invoked']is False and r['probe_only']is False,'NativeSync complete parent Join, not probe')
    n=len(r['groups'])
    need(n>0 and len(r['fixtures'])==16 and len(r['cases'])==n*2 and len(r['field_holdout'])==32 and
         len(r['observer_off'])==n and len(r['error_pairs'])==2,'NativeSync complete parent raw/OFF/field/error grid')


def prepare(parent_config):
    c,paths,settings=history(parent_config);r=read_report(c['report'])
    require_complete_parent(r)
    jf,jb,jp,jg=J.prepare(c['parent_config']);J.check_contract(c['field_contract'],jf,jp)
    J.require_report(r,jf,jb,jp,jg,c['field_contract'],c['raw_dir'])
    bodies=None;components={}
    for language,item in settings.items():
        rom=Path(item['rom']);e=J.N.H.J.H.read_parent_config(Path(item['parent_config']),rom,language)
        obj=e['recipe_dir']/'fs-exec-sync-command.o'
        need(sha(obj.read_bytes())=='768a6e34e5cf2ce6535446110482f27edf3c39c3bd3105956c8037e5049bd011','NativeSync original ExecuteSync ELF identity')
        text=J.N.L.object_text(obj,68,B.E.BODY_SHA);model=J.P.G.S.SHARED.read_current(rom,language)
        with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            view=J.P.G.S.SHARED.gifts_audit.Arm9View(raw);gate=view.read(B.TRANSLATE,4)
            need(view.read(B.ENTRY,68)==J.P.G.piece(model['segments'],B.ENTRY,68)==text and
                 gate==J.P.G.piece(model['segments'],B.TRANSLATE,4)and sha(gate)==B.TRANSLATE_GATE_SHA,
                 'NativeSync physical/decoded/ELF wrapper and intercepted original Translate gate')
            send=view.read(B.S.ENTRY,420)
            need(send==J.P.G.piece(model['segments'],B.S.ENTRY,420)and sha(send)==B.S.BODY_SHA,
                 'NativeSync retained original Send body independently read back')
            code={a:jb[a]for a in B.BODIES if a not in(B.ENTRY,B.TRANSLATE,B.S.ENTRY)}
            code.update({B.ENTRY:text,B.TRANSLATE:gate,B.S.ENTRY:send})
            need(bodies is None or code==bodies,'NativeSync dual-language component equality');bodies=code
            components[language]=dict(input=model['record'],elf_sha256=sha(obj.read_bytes()),
                wrapper=dict(ram=hex(B.ENTRY),rom_offset=hex(view.offset(B.ENTRY,68)),bytes=68,sha256=B.E.BODY_SHA),
                retained_send=dict(ram=hex(B.S.ENTRY),rom_offset=hex(view.offset(B.S.ENTRY,420)),bytes=420,sha256=sha(send)),
                intercepted_translate=dict(ram=hex(B.TRANSLATE),rom_offset=hex(view.offset(B.TRANSLATE,4)),bytes=4,sha256=sha(gate),
                    original_instruction_executed=False))
        del model;gc.collect()
    fixtures=[];image_receipts=[]
    reports={k:read_report(p)for k,p in paths.items()}
    for prior in jf:
        language=prior['language'];sr=F.flat(reports['send_'+language.lower()],prior['plus'],prior['seed'],'normal')
        boundary=F.send_boundary(sr)
        f={k:prior[k]for k in('language','ordinal','plus','seed','translated_result')}
        f.update(entry=boundary['checkpoint_regs'],captured304=sr['services'][0]['frame_before'],captured_guard56=sr['guard_after'],
            archive_before=sr['services'][0]['archive_before'],parent_whole_ram_sha256=boundary['derived_boundary_whole_ram_sha256'],
            send_fixture=sr['fixture'],provenance=dict(send_report_sha256=sha(paths['send_'+language.lower()].read_bytes()),
                whole_sha_is_readonly_transfer=True,whole_sha_captured_at_boundary=False,natural_capture=False))
        parent=B.parent_memory(f,bodies);initial=B.initial_memory(f,bodies)
        changes=[]
        for address in(*B.NATIVE_BODIES,B.TRANSLATE):
            length=len(bodies[address]);a=parent[address-B.BASE:address-B.BASE+length];b=initial[address-B.BASE:address-B.BASE+length]
            changes.append(dict(ram=hex(address),bytes=length,changed_bytes=sum(x!=y for x,y in zip(a,b)),
                before_sha256=sha(a),after_sha256=sha(b)))
        image_receipts.append(dict(language=language,ordinal=f['ordinal'],parent_whole_sha256=sha(parent),
            initial_whole_sha256=sha(initial),code_overlays=changes))
        fixtures.append(f)
    groups=share_groups(fixtures,bodies)
    proof=dict(parent_report_sha256=sha(c['report'].read_bytes()),parent_config_sha256=sha(parent_config.read_bytes()),
        parent_proof=jp,parent_raw_semantically_replayed_without_CPU=True,components=components,
        historical_reports={k:dict(path=str(p),sha256=sha(p.read_bytes()))for k,p in paths.items()},
        grouping=dict(literal_CPU_RAM_and_external_model_policy=True,sha256_for_reporting_only=True,groups=len(groups),origins=len(fixtures)),
        image_receipts=image_receipts,
        memory=dict(parent_reconstructed_equals_readonly_transferred_observed_digest=True,source_filled_extra_bytes=112,
            frame=416,guard=56,peak_relative_to_entry=112,retained_send_bytes=420,native_components_bytes=840,intercepted_translate_bytes=4),
        limits=['Translate error4/R0 projection only; original Translate instruction not executed',
                'Not full Send, Async, natural filesystem/card/thread/SAVE/hardware'])
    return fixtures,bodies,proof,groups,paths


def field_contract(cell,f,row):
    need(all(type(cell[k])is type(f[k])and cell[k]==f[k]for k in('language','ordinal','plus','seed','translated_result')),
         'NativeSync frozen origin and model policy')
    inp=cell['input']
    need(wire(inp['checkpoint_regs'])==wire(f['entry'])and inp['derived_boundary_whole_ram_sha256']==f['parent_whole_ram_sha256']and
         inp['frame304_sha256']==sha(bytes.fromhex(f['captured304']))and inp['guard56_sha256']==sha(bytes.fromhex(f['captured_guard56']))and
         inp['archive92_sha256']==sha(bytes.fromhex(f['archive_before'])),'NativeSync frozen input provenance')
    need(wire(row['entry'])==wire(f['entry'])and wire(row['model_stores'])==wire([cell['translate_host_write']]),
         'NativeSync frozen actual input and model ledger')
    for phase,want in cell['checkpoints'].items():
        actual=row['checkpoints'][phase];frame=bytes.fromhex(actual['frame'])
        need(actual['pc']==want['pc']and wire(actual['regs'])==wire(want['regs'])and
             sha(frame[-want['frame_bytes']:])==want['frame_sha256']and
             sha(bytes.fromhex(actual['archive']))==want['archive92_sha256'],'NativeSync frozen '+phase)
    need(sha(bytes.fromhex(row['guard_before']))==sha(bytes.fromhex(row['guard_after']))==cell['final_guard56_sha256'],
         'NativeSync frozen lower guard')
    return dict(passed=True,phases=9,activation_proved_by_this_comparator=False)


def check_contract(path,fixtures,paths):
    need(path.stat().st_size<=256*1024,'NativeSync bounded frozen contract256KiB');contract=json.loads(path.read_bytes())
    need(wire(contract)==wire(F.freeze(paths))and len(contract['cells'])==16,'NativeSync frozen historical reports binding')
    for f in fixtures:
        cell=next(x for x in contract['cells']if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        prediction=B.predict(f);field_contract(cell,f,dict(prediction,entry=f['entry'],guard_before='a5'*56,guard_after='a5'*56))
    return contract['cells']


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies)
    need(normal['observe']is True and off['observe']is False,'NativeSync actual observer domains')
    excluded=('observe','flow','stores','reads')
    need(wire({k:v for k,v in normal.items()if k not in excluded})==wire({k:v for k,v in off.items()if k not in excluded}),
         'NativeSync exact OFF CPU/RAM/model/checkpoint neutrality')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def counter(normal,bypass,bodies,cell,f):
    B.require_result(normal,bodies);B.require_result(bypass,bodies)
    need(normal['policy']==dict(bypass_wakeup=False)and bypass['policy']==dict(bypass_wakeup=True)and
         normal['before_whole_ram_sha256']==bypass['before_whole_ram_sha256']and normal['returned']==bypass['returned']and
         normal['archive_after']==bypass['archive_after'],'NativeSync same-code/input counter converges public output')
    a,b=(bytes.fromhex(row['frame_after'])for row in(normal,bypass))
    need([i for i,(x,y)in enumerate(zip(a,b))if x!=y]==list(range(64,72)),'NativeSync counter exact eight residual stack bytes')
    try:field_contract(cell,f,bypass)
    except ValueError as error:field_rejection=str(error)
    else:raise ValueError('NativeSync bypass accepted by frozen checkpoints')
    disguised=copy.deepcopy(bypass);disguised['policy']=normal['policy'];disguised['services']=normal['services']
    disguised['checkpoints']=normal['checkpoints']
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='NativeSync source-derived steps','NativeSync disguised bypass rejected on actual fetch count')
        activation_rejection=str(error)
    else:raise ValueError('NativeSync disguised bypass accepted as native Wakeup')
    return dict(field_rejection=field_rejection,activation_rejection=activation_rejection,public_output_equal=True,
        final_frame_differing_offsets=list(range(64,72)),normal_native_steps=131,bypass_native_steps=110)


def require_report(report,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(report['schema']=='native-fs-exec-sync-native-callees-v1'and report['cpu_executed']is True and
         report['compiler_invoked']is False and type(report['probe_only'])is bool and report['source_sha256']==source_identities()and
         wire(report['fixtures'])==wire(fixtures)and wire(report['proof'])==wire(proof)and wire(report['groups'])==wire(groups)and
         report['field_contract_sha256']==sha(contract_path.read_bytes()),'NativeSync replay source/provenance/groups/contract binding')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];held=[];off=[];counters=[];names=[]
    for g in(groups[:1]if report['probe_only']else groups):
        normal=None
        for label,bypass,observe in(POLICIES[:1]if report['probe_only']else POLICIES):
            path=raw_dir/('%d-%s.json.gz'%(g['ordinal'],label));names.append(path.name);row=read_report(path)
            need(wire(row['fixture'])==wire(g['representative'])and row['policy']==dict(bypass_wakeup=bypass)and row['observe']is observe,
                 'NativeSync exact raw member/policy/observer')
            B.require_result(row,bodies);cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            for member in g['members']:
                f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                if bypass:counters.append(dict(group=g['ordinal'],member=member,proof=counter(normal,row,bodies,cell,f)))
                else:held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(names),'NativeSync exact raw set')
    for key,value in(('cases',cases),('observer_off',off),('field_holdout',held),('counters',counters)):
        need(wire(report[key])==wire(value),'NativeSync authenticated '+key)
    return True


def analyze(parent_config,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'NativeSync strict modes')
    need(prepare_only or raw_dir is not None,'NativeSync execution requires private raw directory')
    J.N.H.J.H.H.H.H.R.W.require_host_budget();sources=source_identities();fixtures,bodies,proof,groups,paths=prepare(parent_config)
    cells=check_contract(contract_path,fixtures,paths)
    report=dict(schema='native-fs-exec-sync-native-callees-v1',source_sha256=sources,fixtures=fixtures,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['One explicit Translate error4/R0 model; not native Translate, directory ID/prop, card or thread work',
                'CPU17 Cortex-A15 semantics, not ARM946 timing/IRQ delivery; Send POP stopped, Async/full caller/SAVE/hardware excluded',
                'Boundary whole SHA derived across reviewed readonly model/POP;112 extra input bytes source-filled and digest-verified',
                'Known bodies/inputs; frozen historical fields predate new oracle/guest, not a blind experiment'])
    if not prepare_only:
        need(not raw_dir.exists()and not raw_dir.is_symlink()and J.P.SOURCE not in raw_dir.resolve().parents,'NativeSync fresh private raw output')
        raw_dir.mkdir(parents=True);cases=[];off=[];held=[];counters=[]
        for g in(groups[:1]if probe else groups):
            normal=None
            for label,bypass,observe in(POLICIES[:1]if probe else POLICIES):
                gc.collect();row=B.run(g['representative'],bodies,bypass,observe)
                save(raw_dir/('%d-%s.json.gz'%(g['ordinal'],label)),row);B.require_result(row,bodies)
                cases.append(dict(group=g['ordinal'],label=label,result=row))
                if label=='normal':normal=row
                elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
                for member in g['members']:
                    f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                    cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    if bypass:counters.append(dict(group=g['ordinal'],member=member,proof=counter(normal,row,bodies,cell,f)))
                    else:held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
                print(g['ordinal'],label,'one-context raw saved and checked',flush=True)
        report.update(cpu_executed=True,cases=cases,observer_off=off,field_holdout=held,counters=counters)
        require_report(report,fixtures,bodies,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'NativeSync runtime source changed');J.N.H.J.H.H.H.H.R.W.require_host_budget();return report


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','field-contract','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--raw-dir',type=Path);mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=parser.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and J.P.SOURCE not in a.json.resolve().parents,'NativeSync fresh private output')
        need(a.raw_dir is None or(a.json.resolve()!=a.raw_dir.resolve()and a.raw_dir.resolve()not in a.json.resolve().parents),
             'NativeSync report must be outside the exact raw directory')
        report=analyze(a.parent_config,a.field_contract,a.raw_dir,a.prepare_only,a.probe);save(a.json,report)
    except(ValueError,KeyError,TypeError)as error:parser.exit(2,str(error)+'\n')
    print('Prepared without CPU'if a.prepare_only else'Finite ExecuteSync and native callees verified; Translate remains modeled')


if __name__=='__main__':main()
