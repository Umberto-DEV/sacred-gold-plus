#!/usr/bin/env python3
"""Attribute the original stored-error/POP join after an actual native NextNULL."""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


N=load('sync_join_qualified_next_cli',Path(__file__).with_name('attribuisci_fs_next.py'))
B=load('sync_join_native_bench',Path(__file__).parents[1]/'test/fs_exec_sync_join_bench.py')
F=load('sync_join_frozen_fields',Path(__file__).with_name('congela_fs_exec_sync_join_contract.py'))
P,need,sha,wire,save,read_report=N.P,N.need,N.sha,B.wire,N.save,N.read_report
need(sha(Path(N.__file__).read_bytes())=='e4b61c14484e8bfd49b0683c2d41b2d8df88a7cbd811b6d1c543baaba05ed488','Join qualified parent CLI drift')
CONFIG_KEYS={'parent_config','field_contract','report','raw_dir'}
PARENT_CONFIG_KEYS=CONFIG_KEYS|{'recipe_dir'}
POLICIES=[('normal',True),('off',False)]


def source_identities():
    ids=N.source_identities()
    for name in(__file__,B.__file__,F.__file__):
        p=Path(name);ids[str(p.resolve().relative_to(P.SOURCE))]=sha(p.read_bytes())
    return ids


def read_config(path):
    need(path.stat().st_size<=512*1024,'Join bounded replay config512KiB');c=json.loads(path.read_bytes())
    need(type(c)is dict and set(c)==CONFIG_KEYS and all(type(v)is str for v in c.values()),'Join exact replay string keys')
    return {k:Path(v)for k,v in c.items()}


def read_parent_config(path):
    need(path.stat().st_size<=512*1024,'Join bounded native Next config512KiB');c=json.loads(path.read_bytes())
    need(type(c)is dict and set(c)==PARENT_CONFIG_KEYS and all(type(v)is str for v in c.values()),'Join exact native Next replay string keys')
    return {k:Path(v)for k,v in c.items()}


def require_complete_parent(r):
    need(r['schema']=='native-fs-next-isolated-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        r['probe_only']is False,'Join requires complete native Next, not a probe')
    n=len(r['groups']);need(n>0 and len(r['fixtures'])==16 and len(r['cases'])==n*4 and
        len(r['field_holdout'])==64 and len(r['observer_off'])==len(r['counters'])==n,'Join complete parent raw/OFF/counter/field grid')


def share_groups(fixtures,bodies):
    groups=[];keys=[]
    for f in fixtures:
        image=B.initial_memory(f,bodies);key=(wire(f['entry']),image)
        if key not in keys:
            keys.append(key);groups.append(dict(ordinal=len(keys)-1,representative=f,members=[],initial_ram_sha256=sha(image)))
        groups[keys.index(key)]['members'].append(dict(language=f['language'],ordinal=f['ordinal']))
    return groups


def prepare(parent_config):
    c=read_parent_config(parent_config);r=read_report(c['report']);require_complete_parent(r)
    nf,nb,np,ng=N.prepare(c['parent_config'],c['recipe_dir']);N.check_contract(c['field_contract'],nf)
    N.require_report(r,nf,nb,np,ng,c['field_contract'],c['raw_dir'])
    # c.parent_config is the Release/Wakeup config. Walk its existing qualified
    # chain, rather than substituting paths from a developer's directory layout.
    composition=N.read_config(c['parent_config']);wake=N.H.read_config(composition['parent_config'])
    release=N.H.J.read_config(wake['parent_config'])
    bodies=None;components={}
    for language in('EN','IT'):
        settings=release[language]['prepare'];rom=Path(settings['rom'])
        ancestor=N.H.J.H.read_parent_config(Path(settings['parent_config']),rom,language)
        obj=ancestor['recipe_dir']/'fs-exec-sync-command.o'
        need(sha(obj.read_bytes())=='768a6e34e5cf2ce6535446110482f27edf3c39c3bd3105956c8037e5049bd011','Join retained ExecuteSync ELF identity')
        text=N.L.object_text(obj,68,'44b2f23b47f01552bd478420b9a14ae0fc2ed6013e7d551d5112075264a43d55')
        model=P.G.S.SHARED.read_current(rom,language)
        with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
            need(view.read(0x20D7744,68)==P.G.piece(model['segments'],0x20D7744,68)==text,'Join physical/decoded/full ELF68 agreement')
            tail=view.read(B.ENTRY,32);gate=view.read(B.RETURN,4)
            need(tail==text[36:]and tail==P.G.piece(model['segments'],B.ENTRY,32)and sha(tail)==B.TAIL_SHA and
                gate==P.G.piece(model['segments'],B.RETURN,4)and sha(gate)==B.GATE_SHA,'Join original tail32 and stopped Send gate4')
            code={**nb,B.ENTRY:tail,B.RETURN:gate};need(bodies is None or bodies==code,'Join dual-ROM code equality');bodies=code
            components[language]=dict(input=model['record'],elf_sha256=sha(obj.read_bytes()),
                tail=dict(ram=hex(B.ENTRY),rom_offset=hex(view.offset(B.ENTRY,32)),bytes=32,sha256=B.TAIL_SHA),
                stopped_gate=dict(ram=hex(B.RETURN),rom_offset=hex(view.offset(B.RETURN,4)),bytes=4,sha256=B.GATE_SHA))
        del model;gc.collect()
    fixtures=[];digest=sha(c['report'].read_bytes())
    for f in nf:
        member=dict(language=f['language'],ordinal=f['ordinal']);g=next(g for g in ng if member in g['members'])
        row=r['cases'][g['ordinal']*4]['result']
        need(row['halt_pc']==hex(B.ENTRY)and row['observe']is True and row['fill']==0xA5,'Join actual normal native Next checkpoint')
        item={k:f[k]for k in('language','ordinal','plus','seed','translated_result')}
        item.update(entry=row['returned'],frame=row['frame_after'],guard=row['guard_after'],archive_before=row['archive_after'],
            parent_fixture=f,parent_whole_ram_sha256=row['whole_ram_sha256'],
            provenance=dict(parent_report_sha256=digest,parent_group=g['ordinal'],natural_capture=False))
        B.parent_memory(item,bodies);fixtures.append(item)
    groups=share_groups(fixtures,bodies)
    proof=dict(parent_report_sha256=digest,parent_report_path=str(c['report']),parent_config_sha256=sha(parent_config.read_bytes()),parent_proof=np,
        parent_raw_semantically_replayed_without_CPU=True,components=components,
        grouping=dict(literal_CPU_and_RAM_equality=True,sha256_for_reporting_only=True,groups=len(groups),origins=len(fixtures)),
        memory=dict(parent_reconstructed_equals_observed_digest=True,new_tail_bytes=28,new_stopped_gate_bytes=4,
                    new_fill_bytes=0,frame=416,guard=56,new_stack_allocation=0,all_guest_writes_forbidden=True),
        limits=['Isolated native suffix only; original Send POP stopped, full caller not qualified',
                'No new compiler, Async, natural filesystem completion or hardware observation'])
    return fixtures,bodies,proof,groups


def field_contract(cell,f,row):
    need(all(type(cell[k])is type(f[k])and cell[k]==f[k]for k in('language','ordinal','plus','seed','translated_result'))and
        cell['parent_report_sha256']==f['provenance']['parent_report_sha256']and cell['parent_group']==f['provenance']['parent_group']and
        wire(cell['checkpoint_regs'])==wire(f['entry'])and cell['checkpoint_pc']==hex(B.ENTRY)and
        cell['parent_whole_ram_sha256']==f['parent_whole_ram_sha256'],'Join frozen parent identity/checkpoint')
    need(wire(row['entry'])==wire(cell['checkpoint_regs'])and wire(row['returned'])==wire(cell['expected_returned'])and
        row['halt_pc']==cell['expected_return_pc']==hex(B.RETURN),'Join frozen actual entry/returned fields')
    for name,frozen in(('frame','frame416_sha256'),('guard','guard56_sha256'),('archive','archive92_sha256')):
        need(sha(bytes.fromhex(row[name+'_before']))==sha(bytes.fromhex(row[name+'_after']))==cell[frozen],
             'Join frozen unchanged '+name)
    need(cell['expected_memory_unchanged']is True and row['before_whole_ram_sha256']==row['whole_ram_sha256'],
         'Join frozen whole RAM unchanged after authenticated overlay')
    return dict(passed=True,returned=row['returned'],frame416_sha256=cell['frame416_sha256'],
                native_activation_proved_by_this_comparator=False)


def check_contract(path,fixtures,proof):
    need(path.stat().st_size<=128*1024,'Join bounded frozen contract128KiB');c=json.loads(path.read_bytes())
    parent=Path(proof['parent_report_path'])
    need(sha(parent.read_bytes())==proof['parent_report_sha256']and wire(c)==wire(F.freeze(parent)),
         'Join frozen export differs from actual earlier checkpoint fields')
    need(c['schema']=='native-fs-exec-sync-join-prospective-fields-v1'and len(c['cells'])==16 and
        {(x['language'],x['ordinal'])for x in c['cells']}=={(f['language'],f['ordinal'])for f in fixtures},'Join complete frozen16')
    for f in fixtures:
        cell=next(x for x in c['cells']if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        predicted=B.predict(f);row=dict(entry=f['entry'],returned=predicted['returned'],halt_pc=hex(B.RETURN),
            frame_before=f['frame'],frame_after=f['frame'],guard_before=f['guard'],guard_after=f['guard'],
            archive_before=f['archive_before'],archive_after=f['archive_before'],before_whole_ram_sha256='same',whole_ram_sha256='same')
        field_contract(cell,f,row)
        need(cell['parent_report_sha256']==proof['parent_report_sha256'],'Join frozen actual parent receipt binding')
    return c['cells']


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies)
    need(normal['observe']is True and off['observe']is False,'Join actual ON/OFF domains')
    need(wire({k:v for k,v in normal.items()if k not in('observe','flow','reads')})==
         wire({k:v for k,v in off.items()if k not in('observe','flow','reads')}),'Join exact OFF CPU/whole-RAM neutrality, no projection')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def error_pair(success,failure,bodies):
    B.require_result(success,bodies);B.require_result(failure,bodies)
    need(success['fixture']['translated_result']==0 and failure['fixture']['translated_result']==1 and
        success['entry']==failure['entry']and success['observe']is failure['observe']is True,'Join observed error0/1 with same actual NextNULL CPU')
    a,b=success['reads'],failure['reads']
    need(a[1:]==b[1:]and {k:v for k,v in a[0].items()if k!='hex'}=={k:v for k,v in b[0].items()if k!='hex'}and
        a[0]['hex']=='00000000'and b[0]['hex']=='01000000','Join same actual readset except stored error value')
    disguised=copy.deepcopy(failure);disguised['fixture']=success['fixture']
    for key in('frame_before','frame_after','archive_before','archive_after','guard_before','guard_after','before_whole_ram_sha256','whole_ram_sha256'):
        disguised[key]=success[key]
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='Join source-derived returned','Join metadata disguise rejected on native returned context')
        return dict(rejection=str(error),next_R0_equal=0,other_reads_equal=True,native_BOOLs=[success['returned'][0],failure['returned'][0]],
                    initial_RAMs_not_claimed_byteidentical=True)
    raise ValueError('Join stored-error failure accepted as success')


def require_report(r,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(r['schema']=='native-fs-exec-sync-join-isolated-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        type(r['probe_only'])is bool and r['source_sha256']==source_identities()and wire(r['fixtures'])==wire(fixtures)and
        wire(r['proof'])==wire(proof)and wire(r['groups'])==wire(groups)and r['field_contract_sha256']==sha(contract_path.read_bytes()),
        'Join replay metadata/source/fixtures/proof/groups/contract binding')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];off=[];held=[];paths=[];normals={}
    for g in(groups[:1]if r['probe_only']else groups):
        normal=None
        for label,observe in(POLICIES[:1]if r['probe_only']else POLICIES):
            path=raw_dir/('%d-%s.json.gz'%(g['ordinal'],label));paths.append(path.name);row=read_report(path)
            need(wire(row['fixture'])==wire(g['representative'])and row['observe']is observe,'Join replay actual representative/observer')
            B.require_result(row,bodies);cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row;normals[(g['representative']['plus'],g['representative']['translated_result'])]=row
            else:off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            for member in g['members']:
                f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
    pairs=[]if r['probe_only']else[dict(plus=plus,proof=error_pair(normals[(plus,0)],normals[(plus,1)],bodies))for plus in(0,1)]
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(paths),'Join exact raw set')
    for key,value in(('cases',cases),('observer_off',off),('field_holdout',held),('error_pairs',pairs)):
        need(wire(r[key])==wire(value),'Join replay authenticated '+key)
    return True


def analyze(parent_config,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Join strict exclusive modes')
    need(prepare_only or raw_dir is not None,'Join execution requires fresh private raw directory')
    N.H.J.H.H.H.H.R.W.require_host_budget();sources=source_identities();fixtures,bodies,proof,groups=prepare(parent_config)
    cells=check_contract(contract_path,fixtures,proof)
    report=dict(schema='native-fs-exec-sync-join-isolated-v1',source_sha256=sources,fixtures=fixtures,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['Native suffix only after copied actual NextNULL; not same-CPU upstream composition, original Send POP or full caller',
                'All parent bytes retained; only tail28/gate4 added before execution; no new fill or host guest-state writes',
                'CPU17 Cortex-A15 instruction semantics, not ARM946 timing, IRQ delivery, natural filesystem/card or save/hardware',
                'Known inputs/body inspected; frozen fields predate predictor/guest, not a blind experiment'])
    if not prepare_only:
        need(not raw_dir.exists()and not raw_dir.is_symlink()and P.SOURCE not in raw_dir.resolve().parents,'Join fresh private raw output')
        raw_dir.mkdir(parents=True);cases=[];off=[];held=[];normals={}
        for g in(groups[:1]if probe else groups):
            normal=None
            for label,observe in(POLICIES[:1]if probe else POLICIES):
                gc.collect();row=B.run(g['representative'],bodies,observe);save(raw_dir/('%d-%s.json.gz'%(g['ordinal'],label)),row)
                B.require_result(row,bodies);cases.append(dict(group=g['ordinal'],label=label,result=row))
                if label=='normal':normal=row;normals[(g['representative']['plus'],g['representative']['translated_result'])]=row
                else:off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
                for member in g['members']:
                    f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                    cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
                print(g['ordinal'],label,'original join raw saved and checked',flush=True)
        report.update(cpu_executed=True,cases=cases,observer_off=off,field_holdout=held,
            error_pairs=[]if probe else[dict(plus=plus,proof=error_pair(normals[(plus,0)],normals[(plus,1)],bodies))for plus in(0,1)])
        require_report(report,fixtures,bodies,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'Join runtime source changed');N.H.J.H.H.H.H.R.W.require_host_budget();return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','field-contract','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);mode=p.add_mutually_exclusive_group();mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and P.SOURCE not in a.json.resolve().parents,'Join fresh private output')
        r=analyze(a.parent_config,a.field_contract,a.raw_dir,a.prepare_only,a.probe);save(a.json,r)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print('Join prepared without CPU'if a.prepare_only else'Original stored-error join verified; Send return and full caller excluded')


if __name__=='__main__':main()
