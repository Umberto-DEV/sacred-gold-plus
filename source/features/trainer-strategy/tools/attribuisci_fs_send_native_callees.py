#!/usr/bin/env python3
"""Verify complete finite Send with native callees and an explicit Translate model."""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,sys


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


E=load('native_send_qualified_exec_cli',Path(__file__).with_name('attribuisci_fs_exec_sync_native_callees.py'))
B=load('native_send_source_bench',Path(__file__).parents[1]/'test/fs_send_native_callees_bench.py')
F=load('native_send_fields',Path(__file__).with_name('congela_fs_send_native_contract.py'))
need,sha,wire,save,read_report=E.need,E.sha,B.wire,E.save,E.read_report
need(sha(Path(E.__file__).read_bytes())=='3cf361c3ea3a266323cbb100a7bad45fe65121fe1fb5065e621e5062e1a50be2',
     'NativeSend qualified parent CLI drift')
POLICIES=E.POLICIES


def source_identities():
    ids=E.source_identities()
    for name in(__file__,B.__file__,F.__file__):
        p=Path(name);ids[str(p.resolve().relative_to(E.J.P.SOURCE))]=sha(p.read_bytes())
    return ids


def require_complete_parent(r):
    need(r['schema']=='native-fs-exec-sync-native-callees-v1'and r['cpu_executed']is True and
         r['compiler_invoked']is False and r['probe_only']is False,'NativeSend complete native parent, not probe')
    n=len(r['groups'])
    need(n>0 and len(r['fixtures'])==16 and len(r['cases'])==n*3 and len(r['field_holdout'])==32 and
         len(r['observer_off'])==n and len(r['counters'])==16,'NativeSend complete parent raw/OFF/field/counter grid')


def share_groups(fixtures,bodies):
    groups=[];keys=[]
    for f in fixtures:
        image=B.initial_memory(f,bodies);key=(wire(f['entry']),image,f['translated_result'])
        if key not in keys:
            keys.append(key);groups.append(dict(ordinal=len(keys)-1,representative=f,members=[],initial_ram_sha256=sha(image),
                model_policy=dict(result=f['translated_result'],preserve_other_registers=True)))
        groups[keys.index(key)]['members'].append(dict(language=f['language'],ordinal=f['ordinal']))
    return groups


def prepare(parent_config):
    c=E.J.read_config(parent_config);r=read_report(c['report']);require_complete_parent(r)
    ef,eb,ep,eg,old_paths=E.prepare(c['parent_config']);E.check_contract(c['field_contract'],ef,old_paths)
    E.require_report(r,ef,eb,ep,eg,c['field_contract'],c['raw_dir'])
    _,_,settings=E.history(c['parent_config']);bodies=None;components={}
    for language,item in settings.items():
        rom=Path(item['rom']);model=E.J.P.G.S.SHARED.read_current(rom,language)
        with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            view=E.J.P.G.S.SHARED.gifts_audit.Arm9View(raw);gate=view.read(B.RETURN,4)
            need(gate==E.J.P.G.piece(model['segments'],B.RETURN,4)==B.STOP_GATE and sha(gate)==B.BODIES[B.RETURN][1],
                 'NativeSend original Find stopped gate physical/decoded/known instruction')
            code={**eb,B.RETURN:gate};need(bodies is None or code==bodies,'NativeSend dual-language code equality');bodies=code
            components[language]=dict(input=model['record'],stopped_Find_gate=dict(ram=hex(B.RETURN),
                rom_offset=hex(view.offset(B.RETURN,4)),bytes=4,sha256=sha(gate),executed=False))
        del model;gc.collect()
    paths=dict(send_en=old_paths['send_en'],send_it=old_paths['send_it'],native_report=c['report'])
    sr={language:read_report(paths['send_'+language.lower()])for language in('EN','IT')}
    fixtures=[];images=[]
    for parent in ef:
        language=parent['language'];row=F.F.flat(sr[language],parent['plus'],parent['seed'],'normal')
        before,_=F.send_input(row);original=row['fixture']
        f={k:parent[k]for k in('language','ordinal','plus','seed','translated_result')}
        f.update(entry=original['entry'],frame=original['frame'],guard=row['guard_before'],archive_before=original['archive_before'],
            parent_whole_ram_sha256=before['before_whole_ram_sha256'],provenance=dict(send_ordinal=original['ordinal'],
                send_report_sha256=sha(paths['send_'+language.lower()].read_bytes()),whole_sha_captured_at_Send_entry=True,
                whole_sha_is_readonly_transfer=False,ancestral_frame=original['provenance'],natural_capture=False))
        prior=B.parent_memory(f,bodies);initial=B.initial_memory(f,bodies);changes=[]
        for address in(*B.E.NATIVE_BODIES,B.TRANSLATE):
            n=len(bodies[address]);a=prior[address-B.BASE:address-B.BASE+n];b=initial[address-B.BASE:address-B.BASE+n]
            changes.append(dict(ram=hex(address),bytes=n,changed_bytes=sum(x!=y for x,y in zip(a,b)),before_sha256=sha(a),after_sha256=sha(b)))
        images.append(dict(language=language,ordinal=f['ordinal'],observed_Send_before_whole_sha256=sha(prior),
            initial_whole_sha256=sha(initial),code_overlays=changes))
        fixtures.append(f)
    groups=share_groups(fixtures,bodies)
    proof=dict(parent_report_sha256=sha(c['report'].read_bytes()),parent_config_sha256=sha(parent_config.read_bytes()),parent_proof=ep,
        parent_raw_semantically_replayed_without_CPU=True,components=components,image_receipts=images,
        historical_reports={k:dict(path=str(p),sha256=sha(p.read_bytes()))for k,p in paths.items()},
        grouping=dict(literal_CPU_RAM_and_external_model_policy=True,sha256_for_reporting_only=True,groups=len(groups),origins=len(fixtures)),
        memory=dict(parent_equals_observed_before_digest=True,readonly_transfer=False,source_filled_extra_bytes=112,
            initial304_contains_caller280_plus_preserved_predecessor_guard24=True,frame=416,guard=56,peak_relative_to_Send_entry=136,
            native_components_bytes=1260,intercepted_translate_bytes=4),
        limits=['One explicit Translate error4/R0 projection; original Translate instruction not executed',
                'Original Find ADD at return is stopped; higher caller/natural filesystem/card/thread/SAVE/hardware excluded'])
    return fixtures,bodies,proof,groups,paths


def field_contract(cell,f,row):
    need(all(type(cell[k])is type(f[k])and cell[k]==f[k]for k in('language','ordinal','plus','seed','translated_result')),
         'NativeSend frozen origin and model policy')
    inp=cell['input']
    need(wire(inp['checkpoint_regs'])==wire(f['entry'])and inp['before_whole_ram_sha256']==f['parent_whole_ram_sha256']and
         inp['whole_sha_captured_at_Send_entry']is True and inp['whole_sha_is_readonly_transfer']is False and
         inp['frame304_sha256']==sha(bytes.fromhex(f['frame']))and inp['guard56_sha256']==sha(bytes.fromhex(f['guard']))and
         inp['archive92_sha256']==sha(bytes.fromhex(f['archive_before'])),'NativeSend frozen actual BEFORE provenance')
    need(wire(row['entry'])==wire(f['entry'])and wire(row['model_stores'])==wire([cell['translate_host_write']]),
         'NativeSend frozen actual entry and model ledger')
    need(set(row['checkpoints'])==set(cell['checkpoints'])and len(cell['checkpoints'])==11,'NativeSend exact eleven checkpoint phases')
    for phase,want in cell['checkpoints'].items():
        actual=row['checkpoints'][phase]
        need(actual['pc']==want['pc']and wire(actual['regs'])==wire(want['regs'])and
             sha(bytes.fromhex(actual['frame']))==want['frame416_sha256']and
             sha(bytes.fromhex(actual['archive']))==want['archive92_sha256'],'NativeSend frozen '+phase)
    final=cell['checkpoints']['final']
    need(final['derived_from_readonly_POP']is True and final['observed_in_new_composition']is False and
         row['halt_pc']==final['pc']and wire(row['returned'])==wire(final['regs']),'NativeSend labeled final projection matches actual return')
    need(sha(bytes.fromhex(row['guard_before']))==sha(bytes.fromhex(row['guard_after']))==cell['final_guard56_sha256'],
         'NativeSend frozen unchanged lower guard')
    return dict(passed=True,phases=11,final_expectation_was_readonly_POP_projection=True,activation_proved_by_this_comparator=False)


def check_contract(path,fixtures,paths):
    need(path.stat().st_size<=256*1024,'NativeSend bounded frozen contract256KiB');contract=json.loads(path.read_bytes())
    need(wire(contract)==wire(F.freeze(paths))and len(contract['cells'])==16,'NativeSend frozen historical report binding')
    for f in fixtures:
        cell=next(x for x in contract['cells']if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        predicted=B.predict(f)
        field_contract(cell,f,dict(predicted,entry=f['entry'],guard_before=f['guard'],guard_after=f['guard'],halt_pc=hex(B.RETURN)))
    return contract['cells']


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies)
    need(normal['observe']is True and off['observe']is False,'NativeSend actual observer domains')
    excluded=('observe','flow','stores','reads')
    need(wire({k:v for k,v in normal.items()if k not in excluded})==wire({k:v for k,v in off.items()if k not in excluded}),
         'NativeSend exact OFF CPU/RAM/model/checkpoint neutrality')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def counter(normal,bypass,bodies,cell,f):
    B.require_result(normal,bodies);B.require_result(bypass,bodies)
    need(normal['policy']==dict(bypass_wakeup=False)and bypass['policy']==dict(bypass_wakeup=True)and
         normal['before_whole_ram_sha256']==bypass['before_whole_ram_sha256']and normal['returned']==bypass['returned']and
         normal['archive_after']==bypass['archive_after'],'NativeSend same-code/input counter converges public output')
    a,b=(bytes.fromhex(row['frame_after'])for row in(normal,bypass))
    need([i for i,(x,y)in enumerate(zip(a,b))if x!=y]==list(range(64,72)),'NativeSend counter exact eight residual bytes after Send POP')
    try:field_contract(cell,f,bypass)
    except ValueError as error:field_rejection=str(error)
    else:raise ValueError('NativeSend bypass accepted by frozen fields')
    disguised=copy.deepcopy(bypass);disguised['policy']=normal['policy'];disguised['services']=normal['services'];disguised['checkpoints']=normal['checkpoints']
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='Send native source-derived steps','NativeSend disguised bypass rejected on actual fetch count');rejection=str(error)
    else:raise ValueError('NativeSend disguised bypass accepted as native Wakeup')
    return dict(field_rejection=field_rejection,activation_rejection=rejection,public_output_equal=True,final_frame_differing_offsets=list(range(64,72)),
        normal_native_steps=221,bypass_native_steps=200)


def require_report(report,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(report['schema']=='native-fs-send-native-callees-v1'and report['cpu_executed']is True and report['compiler_invoked']is False and
         type(report['probe_only'])is bool and report['source_sha256']==source_identities()and wire(report['fixtures'])==wire(fixtures)and
         wire(report['proof'])==wire(proof)and wire(report['groups'])==wire(groups)and report['field_contract_sha256']==sha(contract_path.read_bytes()),
         'NativeSend replay source/provenance/groups/contract binding')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];held=[];off=[];counters=[];names=[]
    for g in(groups[:1]if report['probe_only']else groups):
        normal=None
        for label,bypass,observe in(POLICIES[:1]if report['probe_only']else POLICIES):
            path=raw_dir/('%d-%s.json.gz'%(g['ordinal'],label));names.append(path.name);row=read_report(path)
            need(wire(row['fixture'])==wire(g['representative'])and row['policy']==dict(bypass_wakeup=bypass)and row['observe']is observe,
                 'NativeSend exact raw member/policy/observer')
            B.require_result(row,bodies);cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            for member in g['members']:
                f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                if bypass:counters.append(dict(group=g['ordinal'],member=member,proof=counter(normal,row,bodies,cell,f)))
                else:held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(names),'NativeSend exact raw set')
    for key,value in(('cases',cases),('observer_off',off),('field_holdout',held),('counters',counters)):
        need(wire(report[key])==wire(value),'NativeSend authenticated '+key)
    return True


def analyze(parent_config,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'NativeSend strict modes')
    need(prepare_only or raw_dir is not None,'NativeSend execution requires private raw directory')
    E.J.N.H.J.H.H.H.H.R.W.require_host_budget();sources=source_identities();fs,bs,proof,groups,paths=prepare(parent_config)
    cells=check_contract(contract_path,fs,paths)
    report=dict(schema='native-fs-send-native-callees-v1',source_sha256=sources,fixtures=fs,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['One explicit Translate error4/R0 model; native translation/ID/prop/IS_SYNC/card/thread not proved',
                'Original Find ADD stopped; higher caller/natural filesystem/SAVE/hardware excluded',
                'CPU17 Cortex-A15 semantics, not ARM946 timing or IRQ delivery; global736 exceeds old608 bound',
                'Initial whole identity observed before Send; frame304 preserves caller280 and predecessor guard24',
                'Known inputs/bodies; frozen historical fields and derived POP predate new oracle/guest, not blind'])
    if not prepare_only:
        need(not raw_dir.exists()and not raw_dir.is_symlink()and E.J.P.SOURCE not in raw_dir.resolve().parents,'NativeSend fresh private raw output')
        raw_dir.mkdir(parents=True);cases=[];off=[];held=[];counters=[]
        for g in(groups[:1]if probe else groups):
            normal=None
            for label,bypass,observe in(POLICIES[:1]if probe else POLICIES):
                gc.collect();row=B.run(g['representative'],bs,bypass,observe);save(raw_dir/('%d-%s.json.gz'%(g['ordinal'],label)),row)
                B.require_result(row,bs);cases.append(dict(group=g['ordinal'],label=label,result=row))
                if label=='normal':normal=row
                elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bs)))
                for member in g['members']:
                    f=next(f for f in fs if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                    cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    if bypass:counters.append(dict(group=g['ordinal'],member=member,proof=counter(normal,row,bs,cell,f)))
                    else:held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
                print(g['ordinal'],label,'complete Send raw saved and checked',flush=True)
        report.update(cpu_executed=True,cases=cases,observer_off=off,field_holdout=held,counters=counters)
        require_report(report,fs,bs,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'NativeSend source changed');E.J.N.H.J.H.H.H.H.R.W.require_host_budget();return report


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','field-contract','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--raw-dir',type=Path);mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=parser.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and E.J.P.SOURCE not in a.json.resolve().parents,'NativeSend fresh private output')
        need(a.raw_dir is None or(a.json.resolve()!=a.raw_dir.resolve()and a.raw_dir.resolve()not in a.json.resolve().parents),
             'NativeSend report must be outside exact raw directory')
        report=analyze(a.parent_config,a.field_contract,a.raw_dir,a.prepare_only,a.probe);save(a.json,report)
    except(ValueError,KeyError,TypeError)as error:parser.exit(2,str(error)+'\n')
    print('Prepared without CPU'if a.prepare_only else'Finite complete Send verified; Translate remains explicitly modeled')


if __name__=='__main__':main()
