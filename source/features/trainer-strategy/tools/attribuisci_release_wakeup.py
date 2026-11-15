#!/usr/bin/env python3
"""Attribute native Release/Wakeup in one CPU; explicit same-code bypass falsifier."""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,sys,types


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


J=load('composition_qualified_wakeup_cli',Path(__file__).with_name('attribuisci_os_wakeup.py'))
B=load('composition_source_bench',Path(__file__).parents[1]/'test/fs_release_wakeup_bench.py')
P,need,sha,wire,save=J.P,J.need,J.sha,B.wire,J.save
need(sha(Path(J.__file__).read_bytes())=='5cbc79d62e41ef9ee21ec8f2ebc04e65d71efb58b0b03d5c088ee05b6d882ea1','Composition qualified Wakeup CLI drift')
read_report=J.H.H.H.H.N.read_report
share_groups=types.FunctionType(J.groups_for.__code__,{**vars(J),'B':B})
CONFIG_KEYS={'parent_config','recipe_dir','field_contract','report','raw_dir'}
POLICIES=[('normal',{}),('off',dict(observe=False)),('fill39',dict(fill=0x39)),('bypass',dict(bypass_wakeup=True))]


def source_identities():
    ids=J.source_identities()
    for path in(__file__,B.__file__):
        p=Path(path);ids[str(p.resolve().relative_to(P.SOURCE))]=sha(p.read_bytes())
    return ids


def read_config(path):
    need(path.stat().st_size<=512*1024,'Composition bounded Wakeup replay config512KiB')
    c=json.loads(path.read_bytes());need(type(c)is dict and set(c)==CONFIG_KEYS and all(type(v)is str for v in c.values()),
        'Composition exact Wakeup replay string keys')
    return {k:Path(v)for k,v in c.items()}


def require_complete_wakeup(r):
    need(r['schema']=='native-os-wakeup-isolated-v1'and r['cpu_executed']is True and
        r['compiler_invoked']is False and r['probe_only']is False,'Composition requires a complete native Wakeup campaign, not a probe')
    count=len(r['groups'])
    need(count>0 and len(r['fixtures'])==16 and len(r['cases'])==count*len(J.POLICIES)and
        len(r['field_holdout'])==16*len(J.POLICIES)and len(r['observer_off'])==count,'Composition complete parent cell/OFF/field grid')


def prepare(parent_config):
    c=read_config(parent_config);wr=read_report(c['report']);require_complete_wakeup(wr)
    wf,wb,wp,wg=J.prepare(c['parent_config'],c['recipe_dir'])
    J.require_report(wr,wf,wb,wp,wg,c['field_contract'],c['raw_dir']);parent=J.read_config(c['parent_config'])
    fixtures=[];bodies=None;proofs={};baselines={}
    for language in('EN','IT'):
        cell=parent[language];path=Path(cell['report']);r=read_report(path);digest=sha(path.read_bytes())
        need(digest==wp[language]['parent_report_sha256'],'Composition qualified Release report identity')
        rom=Path(cell['prepare']['rom']);model=P.G.S.SHARED.read_current(rom,language)
        with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            view=P.G.S.SHARED.gifts_audit.Arm9View(raw);code={a:view.read(a,n)for a,(n,d)in B.BODIES.items()}
            for a,(n,d)in B.BODIES.items():
                need(code[a]==P.G.piece(model['segments'],a,n)and sha(code[a])==d,'Composition physical/decoded native body')
                if a in wb:need(code[a]==wb[a],'Composition retained qualified Wakeup/IRQ body')
            release_obj=Path(cell['prepare']['recipe_dir'])/'fs-release-command.o'
            need(code[B.ENTRY]==J.L.object_text(release_obj,92,B.E.BODY_SHA),'Composition independent retained Release ELF92')
            need(view.read(B.RETURN,4)==bytes.fromhex('080094e5'),'Composition original ExecuteSync return-fetch LDR')
            need(bodies is None or bodies==code,'Composition dual-ROM code equality before shared execution');bodies=code
            for i,f in enumerate(r['fixtures']):
                row=r['cases'][i*6]['result'];guard=bytes.fromhex(row['guard_before']);w=next(x for x in wf if(x['language'],x['ordinal'])==(language,i))
                need(row['guard_before']==row['guard_after']and len(guard)==56 and
                    w['captured_parent_guard56']==guard.hex()and w['entry']==row['services'][0]['entry']and
                    all(w[k]==f[k]for k in('plus','seed','translated_result')),'Composition actual source/guard/Wakeup boundary binding')
                item=dict(f,language=language,ordinal=i,frame=(guard[-24:]+bytes.fromhex(f['frame'])).hex(),captured_parent_guard56=guard.hex(),
                    provenance=dict(parent_report_sha256=digest,wakeup_report_sha256=sha(c['report'].read_bytes()),natural_capture=False,
                        input='Original actual Release entry, not reconstructed from a Wakeup return'))
                B.check_fixture(item);fixtures.append(item);baselines[(language,i)]=row
            proofs[language]=dict(parent_input=model['record'],components=[dict(ram=hex(a),rom_offset=hex(view.offset(a,n)),bytes=n,sha256=d)for a,(n,d)in B.BODIES.items()],
                release_report_sha256=digest,qualified_wakeup_proof=wp[language])
        del model;gc.collect()
    proof=dict(wakeup_report_sha256=sha(c['report'].read_bytes()),wakeup_config_sha256=sha(parent_config.read_bytes()),
        wakeup_report_semantic_replayed_without_CPU=True,languages=proofs,
        grouping='Unmodified qualified whole-image equality helper with only its bench binding changed',
        frame=dict(isolated=352,native_peak=40,future_parent_peak=672,old_parent_bound=608,parent_integration_qualified=False))
    return fixtures,bodies,proof,share_groups(fixtures,bodies),baselines


def field_contract(cell,f,row):
    """Previous native caller-output invariants; no new composed predictor call."""
    need(cell['language']==f['language']and type(cell['ordinal'])is int and cell['ordinal']==f['ordinal']and
        all(type(cell[k])is int and cell[k]==f[k]for k in('plus','seed','translated_result'))and
        wire(cell['entry'])==wire(f['entry'])and cell['parent_report_sha256']==f['provenance']['parent_report_sha256'],
        'Composition earlier identity/entry binding')
    before=bytes.fromhex(f['frame'])[24:];after=bytes.fromhex(row['frame_after'])[24:]
    need(len(before)==len(after)==328 and sha(before)==cell['frame328_before_sha256']and sha(after)==cell['expected_frame328_after_sha256'],
        'Composition earlier caller-frame328 contract')
    need(sha(bytes.fromhex(f['archive_before']))==cell['archive92_before_sha256']and
        len(bytes.fromhex(row['archive_after']))==92 and sha(bytes.fromhex(row['archive_after']))==cell['expected_archive92_after_sha256'],
        'Composition earlier archive92 contract')
    need(B.B.u32s(row['returned'])and wire(row['returned'])==wire(cell['expected_returned'])and
        row['halt_pc']==cell['expected_halt_pc']==hex(B.RETURN),'Composition earlier full16/original return contract')
    i=B.FILE+24-(B.FRAME+24)
    need(cell['queue8_after']==after[i:i+8].hex()==bytes(8).hex(),'Composition earlier queue8 contract')
    return dict(passed=True,caller_frame328_sha256=sha(after),archive92_sha256=sha(bytes.fromhex(row['archive_after'])),
        returned=row['returned'],native_activation_proved_by_this_comparator=False)


def check_contract(path,fixtures,baselines):
    need(path.stat().st_size<=128*1024,'Composition bounded earlier contract128KiB')
    c=json.loads(path.read_bytes());cells=c['cells']
    need(c['schema']=='native-release-wakeup-prospective-composition-fields-v1'and len(cells)==16 and
        {(x['language'],x['ordinal'])for x in cells}=={(f['language'],f['ordinal'])for f in fixtures},'Composition complete frozen cell set')
    for f in fixtures:
        cell=next(x for x in cells if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        old=baselines[(f['language'],f['ordinal'])];wake=old['services'][0]['entry']
        need(wire(cell['wake_entry'])==wire(wake)and wire(cell['native_stack24_words'])==wire([wake[i]for i in(3,4,5,6,7,14)])and
            cell['stack24_preimage']==f['frame'][:48],'Composition captured nested stack preimage and source words')
        independent=dict(old,frame_after=f['frame'][:48]+old['frame_after'])
        field_contract(cell,f,independent)
    return cells


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies)
    need(normal['observe']is True and off['observe']is False,'Composition actual ON/OFF domains')
    need(wire({k:v for k,v in normal.items()if k not in('observe','flow','stores','reads')})==
        wire({k:v for k,v in off.items()if k not in('observe','flow','stores','reads')}),'Composition OFF exact CPU/RAM without projection')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def counter_rejection(counter,normal,bodies):
    B.require_result(counter,bodies);B.require_result(normal,bodies)
    need(wire(counter['policy'])==wire(dict(bypass_wakeup=True))and wire(normal['policy'])==wire(dict(bypass_wakeup=False))and
        counter['observe']is normal['observe']is True and counter['fill']==normal['fill']==0xA5 and
        all(wire(counter[k])==wire(normal[k])for k in('fixture','entry','returned','archive_after','before_whole_ram_sha256')),
        'Composition same initialized code/image and caller CPU/archive output for bypass control')
    a,b=bytes.fromhex(counter['frame_after']),bytes.fromhex(normal['frame_after'])
    changed=[i for i,(x,y)in enumerate(zip(a,b))if x!=y]
    need(a[24:]==b[24:]and a[:24]==bytes.fromhex(counter['fixture']['frame'])[:24]and changed and
        all(i<24 for i in changed)and counter['whole_ram_sha256']!=normal['whole_ram_sha256'],
        'Composition bypass misses only the new native stack24 state writes under the same code')
    disguised=copy.deepcopy(counter);disguised['policy']['bypass_wakeup']=False
    disguised['services']=[];disguised['boundaries']=copy.deepcopy(normal['boundaries'])
    # Hide explicit model metadata, but retain actual native steps/flow/stack evidence.
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='Composition source-derived steps','Composition bypass rejected for native activation, not superficial model metadata')
        return dict(rejection=str(error),policy_and_model_metadata_disguised=True,caller_results_equal=True,
            same_initial_whole_ram_sha256=normal['before_whole_ram_sha256'],state_diff_frame_offsets=changed)
    raise ValueError('Composition bypass accepted as a native positive')


def require_report(r,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(r['schema']=='native-release-wakeup-composed-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        type(r['probe_only'])is bool and r['source_sha256']==source_identities()and wire(r['fixtures'])==wire(fixtures)and
        wire(r['proof'])==wire(proof)and wire(r['groups'])==wire(groups)and r['field_contract_sha256']==sha(contract_path.read_bytes()),
        'Composition replay metadata/source/fixtures/proof/groups/earlier contract')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];off=[];counters=[];held=[];paths=[];serial=0
    for g in(groups[:1]if r['probe_only']else groups):
        normal=None
        for label,options in(POLICIES[:1]if r['probe_only']else POLICIES):
            serial+=1;path=raw_dir/('%02d-%d-%s.json.gz'%(serial,g['ordinal'],label));paths.append(path.name);row=read_report(path)
            B.require_result(row,bodies)
            need(wire(row['fixture'])==wire(g['representative'])and
                wire((row['policy'],row['observe'],row['fill']))==wire((dict(bypass_wakeup=options.get('bypass_wakeup',False)),
                    options.get('observe',True),options.get('fill',0xA5))),'Composition replay actual representative/policy grid')
            cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            if label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            if label=='bypass':counters.append(dict(group=g['ordinal'],proof=counter_rejection(row,normal,bodies)))
            for member in g['members']:
                f=next(x for x in fixtures if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(paths),'Composition exact raw set')
    for key,value in(('cases',cases),('observer_off',off),('counters',counters),('field_holdout',held)):
        need(wire(r[key])==wire(value),'Composition replay authenticated '+key)
    return True


def analyze(parent_config,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Composition strict exclusive modes')
    need(prepare_only or raw_dir is not None,'Composition execution requires a fresh private raw directory')
    J.H.H.H.H.R.W.require_host_budget();sources=source_identities();fixtures,bodies,proof,groups,baselines=prepare(parent_config)
    cells=check_contract(contract_path,fixtures,baselines)
    report=dict(schema='native-release-wakeup-composed-v1',source_sha256=sources,fixtures=fixtures,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['Actual isolated original Release entry; no full initialized constructor/caller composition or natural boot/card completion',
            'Empty queue only; thread/scheduler excluded; frame352/global672 exceeds old608 ownership bound',
            'Bypass is a declared same-code return-only MODEL falsifier, not a native implementation or SDK failure',
            'Four full-image equivalence classes represent16 provenance links, not16 independent trials or blind data',
            'Recovered recipes/pinned source counterparts, not original MW C reconstruction; CPU17 semantics, not ARM946 hardware/timing'])
    if not prepare_only:
        need(raw_dir is not None and not raw_dir.exists()and not raw_dir.is_symlink()and P.SOURCE not in raw_dir.resolve().parents,'Composition fresh private raw output')
        raw_dir.mkdir(parents=True);cases=[];off=[];counters=[];held=[];serial=0
        for g in(groups[:1]if probe else groups):
            normal=None
            for label,options in(POLICIES[:1]if probe else POLICIES):
                gc.collect();serial+=1;row=B.run(g['representative'],bodies,**options)
                save(raw_dir/('%02d-%d-%s.json.gz'%(serial,g['ordinal'],label)),row);B.require_result(row,bodies)
                cases.append(dict(group=g['ordinal'],label=label,result=row))
                if label=='normal':normal=row
                if label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
                if label=='bypass':counters.append(dict(group=g['ordinal'],proof=counter_rejection(row,normal,bodies)))
                for member in g['members']:
                    f=next(x for x in fixtures if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
                print(g['ordinal'],label,'raw saved, composed source and earlier caller-output contract checked',flush=True)
        report.update(cpu_executed=True,cases=cases,observer_off=off,counters=counters,field_holdout=held)
        require_report(report,fixtures,bodies,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'Composition source changed during execution');J.H.H.H.H.R.W.require_host_budget();return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','field-contract','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);mode=p.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and P.SOURCE not in a.json.resolve().parents,'Composition fresh private output')
        r=analyze(a.parent_config,a.field_contract,a.raw_dir,a.prepare_only,a.probe);save(a.json,r)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print('Release/Wakeup prepared without CPU'if a.prepare_only else'Release/Wakeup empty path composed natively; full caller and scheduling excluded')


if __name__=='__main__':main()
