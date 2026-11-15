#!/usr/bin/env python3
"""Attribute empty-queue Wakeup from Release receipts, grouping identical CPU images.

Two ROM readbacks remain independent. Shared guest executions are permitted only
after complete initialized 4MiB images and entry registers compare byte-for-byte.
"""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('wakeup_qualified_release_cli',Path(__file__).with_name('attribuisci_fs_release.py'))
B=load('wakeup_source_bench',Path(__file__).parents[1]/'test/os_wakeup_bench.py')
L=load('wakeup_independent_reader',Path(__file__).with_name('rileggi_os_wakeup.py'))
P,need,sha,wire,save=H.P,H.need,H.sha,B.wire,H.save
need(sha(Path(H.__file__).read_bytes())=='9c04a582e7d0982ad499f66cd36365b09b3d9332050eb6aef2306276197a29db','Wakeup qualified Release CLI drift')
PREPARE_KEYS={'rom','language','parent_report','parent_config','recipe_dir'}
POLICIES=[('normal',{}),('off',dict(observe=False)),('fill39',dict(fill=0x39))]


def source_identities():
    ids=H.source_identities()
    for path in(__file__,B.__file__,L.__file__,L.C.__file__,Path(__file__).parents[1]/'sorgenti/os-wakeup.S'):
        p=Path(path);ids[str(p.resolve().relative_to(P.SOURCE))]=sha(p.read_bytes())
    return ids


def read_config(path):
    need(path.stat().st_size<=512*1024,'Wakeup bounded parent config512KiB')
    c=json.loads(path.read_bytes());need(type(c)is dict and set(c)=={'EN','IT'},'Wakeup exact EN/IT config')
    for language,cell in c.items():
        need(type(cell)is dict and set(cell)=={'prepare','report','raw_dir'},'Wakeup parent replay cell keys')
        p=cell['prepare'];need(type(p)is dict and set(p)==PREPARE_KEYS and p['language']==language and
            all(type(v)is str for v in p.values())and type(cell['report'])is str and type(cell['raw_dir'])is str,
            'Wakeup exact Release prepare keys/string paths/language')
    return c


def check_parent(parent,language,fixtures,bodies,proof):
    need(parent['schema']=='native-fs-release-isolated-v1'and parent['language']==language and
         parent['cpu_executed']is True and parent['probe_only']is False and
         wire(parent['source_sha256'])==wire(H.source_identities())and wire(parent['proof'])==wire(proof)and
         wire(parent['fixtures'])==wire(fixtures),'Wakeup authenticated Release identity/source/fixtures/proof')
    need(len(parent['cases'])==48 and len(parent['observer_off'])==len(parent['counters'])==8,'Wakeup complete Release grid')
    for i,f in enumerate(fixtures):
        group=parent['cases'][i*6:(i+1)*6]
        for cell,(label,options)in zip(group,H.POLICIES):
            r=cell['result'];p=dict(wake_value=0,clobber=False,stale_error=False)
            p.update({k:v for k,v in options.items()if k in p})
            need(cell['label']==label and wire(r['fixture'])==wire(f)and
                wire((r['policy'],r['observe'],r['fill']))==wire((p,options.get('observe',True),options.get('fill',0xA5))),
                'Wakeup parent exact cell/policy grid')
            H.B.require_result(r,bodies)
        normal,off,counter=(group[j]['result']for j in(0,1,2))
        need(wire(parent['observer_off'][i])==wire(dict(ordinal=i,proof=H.require_off_pair(normal,off,bodies)))and
             wire(parent['counters'][i])==wire(dict(ordinal=i,rejection=H.counter_rejection(counter,normal,bodies),policy_disguised=True)),
             'Wakeup authenticated parent OFF and nonvacuous stale-error controls')


def check_recipe_provenance(receipt,parent_receipt):
    """Bind declarations to qualified parent/header identities, not just map length."""
    need(receipt['reference']['header_sha256']==parent_receipt['reference']['header_sha256']and
        receipt['compiler_sha256']==parent_receipt['compiler_sha256']==
        'fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'and
        receipt['compiler_version']==parent_receipt['compiler_version'],'Wakeup qualified header map/compiler receipt identities')
    need(wire(receipt['layout_abi_compatibility'])==wire(dict(flag='-mabi=apcs-gnu',u64_queried_alignment=8,
        CPContext_bytes=28,CPContext_alignment=4,OSContext_bytes=100,OSContext_alignment=4,
        installed_thread_offsets=dict(state=100,queue=120,link_prev=124,link_next=128),
        meaning='Pinned-header compatibility with installed offsets; original MW compiler/flags and C binary not reconstructed',
        default_eabi_probe_invoked=False,nonempty_thread_runtime_qualified=False)),'Wakeup complete APCS layout compatibility declaration')
    need(wire(receipt['queue_inline_source'])==wire(dict(path='lib/include/nitro/os/common/thread_shared.h',
        sha256='c5912e365f7a55ab466f1c4db082a5fa9ca1222d69b1709b16bac256369123e2',
        definition_sha256='86451bbc5ac1556f6b1b6a6e7a1cb70e3dad1048a9b7ff0772f5e64147ba4369',
        activation='Expanded in full body but skipped on the qualified empty-head path')),'Wakeup original inline queue initializer identity')


def prepare_language(cell,language,recipe_dir):
    config={k:v if k=='language'else Path(v)for k,v in cell['prepare'].items()}
    parent_path=Path(cell['report']);parent=H.H.H.H.N.read_report(parent_path)
    fixtures,release_bodies,release_proof=H.prepare(**config);check_parent(parent,language,fixtures,release_bodies,release_proof)
    model=P.G.S.SHARED.read_current(config['rom'],language);out=[]
    with config['rom'].open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        view=P.G.S.SHARED.gifts_audit.Arm9View(raw);bodies={a:view.read(a,n)for a,(n,d)in B.BODIES.items()}
        obj=recipe_dir/'os-wakeup-command.o';receipt=json.loads((recipe_dir/'manifesto.json').read_bytes());ref=receipt['reference']
        check_recipe_provenance(receipt,release_proof['recipe_receipt'])
        need(bodies[B.ENTRY]==P.G.piece(model['segments'],B.ENTRY,104)==L.object_text(obj,104,B.BODY_SHA),
             'Wakeup physical/decoded/recovered ELF104 agreement')
        need(view.read(B.RETURN,4)==bytes.fromhex('0600a0e1'),'Wakeup actual Release MOV return-fetch gate')
        ancestor=H.read_parent_config(config['parent_config'],config['rom'],language)
        for address,role in((B.DISABLE,'disable'),(B.RESTORE,'restore')):
            n,d=B.BODIES[address];need(bodies[address]==release_bodies[address]==P.G.piece(model['segments'],address,n)==
                L.object_text(ancestor['wait_recipe']/('fs-wait-'+role+'.o'),n,d),'Wakeup retained qualified IRQ readback/ELF')
        need(receipt['schema']=='native-os-wakeup-recipe-v1'and receipt['builder_sha256']==sha(Path(L.C.__file__).read_bytes())and
            receipt['recipe_sha256']==sha((Path(__file__).parents[1]/'sorgenti/os-wakeup.S').read_bytes())and
            wire(receipt['source_recipe'])==wire(L.C.RECIPE)and receipt['objects']['command']['object_sha256']==sha(obj.read_bytes())and
            receipt['recipe_is_recovered']is True and receipt['original_compiler_reconstructed']is False and
            ref['pin']==L.C.D.C.PIN and ref['layout_passed']is True and ref['layout_assertions']==L.C.LAYOUT and len(ref['header_sha256'])==18 and
            ref['source_sha256']=='eb91f80067f2aa05ef0e17d31c3c5c77aec256e7ce1e4e3e2211da1572723ed5'and
            ref['function_body_sha256']==dict(OS_WakeupThread='7ba9fe60d6218f8c3bbbd0799e628d4453d8e9f79ba6291a541946b22a5c0f40')and
            receipt['layout_abi_compatibility']['flag']=='-mabi=apcs-gnu'and
            receipt['layout_abi_compatibility']['u64_queried_alignment']==8,'Wakeup original-source/header/APCS recipe receipt')
        for i,f in enumerate(fixtures):
            row=parent['cases'][i*6]['result'];s=row['services'][0];guard=bytes.fromhex(row['guard_before'])
            need(s['pc']==hex(B.ENTRY)and s['frame_before']==s['frame_after']and s['archive_before']==s['archive_after']and
                s['writes']==[]and len(guard)==56 and row['guard_before']==row['guard_after'],'Wakeup actual empty model boundary/preimage/guard')
            item=dict(language=language,ordinal=i,plus=f['plus'],seed=f['seed'],translated_result=f['translated_result'],entry=s['entry'],
                frame=(guard[-24:]+bytes.fromhex(s['frame_before'])).hex(),archive_before=s['archive_before'],captured_parent_guard56=guard.hex(),
                provenance=dict(parent_report_sha256=sha(parent_path.read_bytes()),natural_capture=False,
                    frame='Actual Release328 plus24 preceding captured guard bytes; new lower guard24 is declared fill'))
            B.check_fixture(item);out.append(item)
        proof=dict(parent_report_sha256=sha(parent_path.read_bytes()),parent_semantic_replay_without_CPU=True,parent_proof=release_proof,
            parent_input=model['record'],components=[dict(ram=hex(a),rom_offset=hex(view.offset(a,n)),bytes=n,sha256=d)for a,(n,d)in B.BODIES.items()],
            recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=receipt,
            frame=dict(isolated_frame=352,native_additional_stack=24,future_parent_peak=672,old_parent_bound=608,parent_integration_qualified=False))
    del model;gc.collect();return out,bodies,proof


def groups_for(fixtures,bodies):
    """Literal whole-image comparisons, not digest-only grouping or fixture labels."""
    groups=[];images=[]
    for f in fixtures:
        image=B.initial_memory(f,bodies,0xA5);key=(f['entry'],B.ENTRY,17,'2.1.4')
        match=next((i for i,(old,k)in enumerate(images)if key==k and image==old),None)
        if match is None:
            match=len(groups);images.append((image,key));groups.append(dict(ordinal=match,representative=f,members=[],
                initialized_bytes=len(image),initial_image_sha256=sha(image),literal_full_image_equality=True,entry=f['entry'],cpu_model=17,unicorn='2.1.4'))
        groups[match]['members'].append(dict(language=f['language'],ordinal=f['ordinal']))
    return groups


def field_contract(cell,f,row):
    """Earlier invariant comparator; does not call the new native predictor."""
    need(cell['language']==f['language']and type(cell['ordinal'])is int and cell['ordinal']==f['ordinal']and
         wire(cell['entry'])==wire(f['entry'])and all(type(cell[k])is int and cell[k]==f[k]for k in('plus','seed','translated_result'))and
         cell['parent_report_sha256']==f['provenance']['parent_report_sha256'],'Wakeup frozen identity binding')
    before=bytes.fromhex(f['frame'])[24:];after=bytes.fromhex(row['frame_after'])[24:]
    archive=bytes.fromhex(f['archive_before']);out=bytes.fromhex(row['archive_after']);regs=row['returned']
    need(cell['caller_frame_bytes']==328 and len(before)==len(after)==328 and
         sha(before)==cell['caller_frame_before_sha256']and sha(after)==cell['expected_caller_frame_after_sha256'],
         'Wakeup frozen caller-frame328 invariant')
    need(cell['archive_bytes']==92 and len(archive)==len(out)==92 and sha(archive)==cell['archive_before_sha256']and
         sha(out)==cell['expected_archive_after_sha256'],'Wakeup frozen archive92 invariant')
    i=B.QUEUE-(B.FRAME+24)
    need(cell['input_queue_address']==B.QUEUE and cell['input_queue8']==before[i:i+8].hex()==after[i:i+8].hex()==bytes(8).hex(),
         'Wakeup frozen queue8 invariant')
    need(B.B.u32s(regs)and all(regs[i]==f['entry'][i]for i in(*range(4,12),13))and
         regs[15]&0xFF==f['entry'][15]&0xFF and row['halt_pc']==hex(B.RETURN),'Wakeup frozen callee-saved/SP/control/return invariants')
    return dict(passed=True,caller_frame328_sha256=sha(after),archive92_sha256=sha(out),
        volatile_changes=[dict(register=i,before=f['entry'][i],after=regs[i])for i in(0,1,2,3,12,14,15)if regs[i]!=f['entry'][i]],
        native_activation_proved_by_this_comparator=False)


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies)
    need(normal['observe']is True and off['observe']is False,'Wakeup actual ON/OFF domains')
    need(wire({k:v for k,v in normal.items()if k not in('observe','flow','stores','reads')})==
         wire({k:v for k,v in off.items()if k not in('observe','flow','stores','reads')}),'Wakeup OFF whole RAM/CPU exact without projection')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def prepare(parent_config,recipe_dir):
    config=read_config(parent_config);all_fixtures=[];proofs={};bodies=None
    for language in('EN','IT'):
        f,b,p=prepare_language(config[language],language,recipe_dir)
        need(bodies is None or bodies==b,'Wakeup both ROM native component bytes equal before sharing guest')
        bodies=b;all_fixtures.extend(f);proofs[language]=p
    return all_fixtures,bodies,proofs,groups_for(all_fixtures,bodies)


def require_report(report,fixtures,bodies,proof,groups,contract_path,raw_dir):
    """CPU-free replay binding raw records, independent fields and exact grid."""
    r=report;need(r['schema']=='native-os-wakeup-isolated-v1'and r['cpu_executed']is True and
        r['compiler_invoked']is False and type(r['probe_only'])is bool and
        r['source_sha256']==source_identities()and wire(r['fixtures'])==wire(fixtures)and
        wire(r['proof'])==wire(proof)and wire(r['groups'])==wire(groups)and
        r['field_contract_sha256']==sha(contract_path.read_bytes()),'Wakeup replay exact identity/source/proof/fixtures/groups/contract')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];off=[];held=[];paths=[];serial=0
    selected=groups[:1]if r['probe_only']else groups
    for g in selected:
        normal=None
        for label,options in(POLICIES[:1]if r['probe_only']else POLICIES):
            serial+=1;path=raw_dir/('%02d-%d-%s.json.gz'%(serial,g['ordinal'],label));paths.append(path.name)
            row=H.H.H.H.N.read_report(path);B.require_result(row,bodies)
            need(wire(row['fixture'])==wire(g['representative'])and type(row['observe'])is bool and
                wire((row['observe'],row['fill']))==wire((options.get('observe',True),options.get('fill',0xA5))),
                'Wakeup replay raw representative/policy binding')
            cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            if label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            for member in g['members']:
                mf=next(x for x in fixtures if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                c=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(c,mf,row)))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(paths),'Wakeup replay exact raw record set')
    for key,value in(('cases',cases),('observer_off',off),('field_holdout',held)):
        need(wire(r[key])==wire(value),'Wakeup replay authenticated '+key)
    return True


def analyze(parent_config,recipe_dir,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Wakeup strict exclusive modes')
    H.H.H.H.R.W.require_host_budget();sources=source_identities();fixtures,bodies,proof,groups=prepare(parent_config,recipe_dir)
    need(contract_path.stat().st_size<=128*1024,'Wakeup bounded earlier field contract128KiB')
    contract=json.loads(contract_path.read_bytes());cells=contract['cells']
    need(contract['schema']=='os-wakeup-empty-prospective-field-contract-v1'and len(cells)==16 and
         {(c['language'],c['ordinal'])for c in cells}=={(f['language'],f['ordinal'])for f in fixtures},'Wakeup complete earlier contract cell set')
    for f in fixtures:
        c=next(c for c in cells if(c['language'],c['ordinal'])==(f['language'],f['ordinal']))
        # Validate frozen preconditions without deriving a native expected result.
        field_contract(c,f,dict(frame_after=f['frame'],archive_after=f['archive_before'],returned=f['entry'],halt_pc=hex(B.RETURN)))
    report=dict(schema='native-os-wakeup-isolated-v1',source_sha256=sources,proof=proof,fixtures=fixtures,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['Empty queue I1 only; no thread removal/reschedule/full caller or natural completion',
                'Shared runs represent literal identical 4MiB CPU images, not independent trials or blind holdouts',
                'Frame352/global672 exceeds old608 caller bound; no parent mask expansion',
                'Recovered assembly, not original MW C rebuild; CPU17 instruction semantics, not ARM946 hardware/timing'])
    if not prepare_only:
        need(raw_dir is not None and not raw_dir.exists()and not raw_dir.is_symlink()and P.SOURCE not in raw_dir.resolve().parents,'Wakeup fresh private raw directory')
        raw_dir.mkdir(parents=True);cases=[];off=[];held=[];serial=0
        for g in(groups[:1]if probe else groups):
            f=g['representative'];normal=None
            for label,options in(POLICIES[:1]if probe else POLICIES):
                serial+=1;r=B.run(f,bodies,**options);save(raw_dir/('%02d-%d-%s.json.gz'%(serial,g['ordinal'],label)),r)
                B.require_result(r,bodies);cases.append(dict(group=g['ordinal'],label=label,result=r))
                if label=='normal':normal=r
                if label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,r,bodies)))
                for member in g['members']:
                    mf=next(x for x in fixtures if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    c=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(c,mf,r)))
                print(g['ordinal'],label,'native raw saved, source and earlier field contract checked',flush=True)
        report.update(cpu_executed=True,cases=cases,observer_off=off,field_holdout=held)
        require_report(report,fixtures,bodies,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'Wakeup sources changed during analysis');H.H.H.H.R.W.require_host_budget();return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','recipe-dir','field-contract','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);mode=p.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and P.SOURCE not in a.json.resolve().parents,'Wakeup fresh private report outside source')
        r=analyze(a.parent_config,a.recipe_dir,a.field_contract,a.raw_dir,prepare_only=a.prepare_only,probe=a.probe);save(a.json,r)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print('Wakeup prepared without CPU'if a.prepare_only else'Empty Wakeup native path verified; thread/scheduler and full caller excluded')


if __name__=='__main__':main()
