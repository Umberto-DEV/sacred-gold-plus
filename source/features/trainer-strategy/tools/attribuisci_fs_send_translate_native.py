#!/usr/bin/env python3
"""Attribute one native Send/Translate context with a value-only default model."""
from pathlib import Path
import copy,gc,importlib.util,json,struct,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


T=load('send_translate_qualified_cli',Path(__file__).with_name('attribuisci_fs_translate.py'))
B=load('send_translate_native_bench',Path(__file__).parents[1]/'test/fs_send_translate_native_bench.py')
F=load('send_translate_frozen_fields',Path(__file__).with_name('congela_fs_send_translate_contract.py'))
need,sha,wire,save,read_report=T.need,T.sha,B.wire,T.save,T.read_report
need(sha(Path(T.__file__).read_bytes())=='0d585e143f77bf2a351401bcd752595fbfc880d175ed25218fe1fd9fac6c50fc','Send Translate qualified CLI drift')
POLICIES=T.POLICIES
CONFIG_KEYS={'parent_config','field_contract','report','raw_dir'}
SOURCE=T.S.E.J.P.SOURCE
require_host_budget=T.require_host_budget


def source_identities():
    ids=T.source_identities()
    for name in(__file__,B.__file__,F.__file__):
        p=Path(name);ids[str(p.resolve().relative_to(SOURCE))]=sha(p.read_bytes())
    return ids


def read_config(path):
    need(path.stat().st_size<=512*1024,'Send Translate bounded replay config512KiB');c=json.loads(path.read_bytes())
    need(type(c)is dict and set(c)==CONFIG_KEYS and all(type(v)is str for v in c.values()),'Send Translate exact replay string keys')
    return{k:Path(v)for k,v in c.items()}


def require_complete_parent(r):
    need(r['schema']=='native-fs-translate-isolated-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
         r['probe_only']is False and len(r['fixtures'])==16 and len(r['groups'])==4 and len(r['cases'])==12 and
         len(r['observer_off'])==4 and len(r['field_holdout'])==48 and len(r['counters'])==4,
         'Send Translate complete isolated parent, not a probe')


def share_groups(fixtures,bodies):
    groups=[];keys=[]
    for f in fixtures:
        image=B.initial_memory(f,bodies);key=(wire(f['entry']),image,f['translated_result'])
        if key not in keys:
            keys.append(key);groups.append(dict(ordinal=len(keys)-1,representative=f,members=[],initial_ram_sha256=sha(image),
                model_policy=dict(default_result=f['translated_result'],preserve_other_registers_and_CPSR=True)))
        groups[keys.index(key)]['members'].append(dict(language=f['language'],ordinal=f['ordinal']))
    return groups


def prepare(parent_config):
    c=T.read_config(parent_config);r=read_report(c['report']);require_complete_parent(r)
    tf,bodies,pp,tg,send_report=T.prepare(c['parent_config'],c['recipe_dir'],c['reference'],c['component_receipt'])
    T.check_contract(c['field_contract'],tf,send_report,c['component_receipt'])
    T.require_report(r,tf,bodies,pp,tg,c['field_contract'],c['raw_dir'])
    fixtures=[f['parent_send_fixture']for f in tf];images=[]
    for f,child in zip(fixtures,tf):
        old={a:bodies[a][:n]for a,(n,_)in B.H.BODIES.items()}
        before=B.H.initial_memory(f,old);image=B.initial_memory(f,bodies)
        need(sha(before)==child['observed_before_Send_whole_sha256'],'Send Translate actual initial Send before overlays')
        g=next(g for g in tg if dict(language=child['language'],ordinal=child['ordinal'])in g['members'])
        row=next(x['result']for x in r['cases']if x['group']==g['ordinal']and x['label']=='normal')
        boundary=B.boundaries(f,bodies)
        need(boundary==dict(translate_entry=row['before_whole_ram_sha256'],translate_return=row['whole_ram_sha256']),
             'Send Translate commuting overlays and source prefix match actual isolated whole boundaries')
        overlays=[]
        for a in(B.TRANSLATE,B.T.TABLE,B.DEFAULT):
            n=len(bodies[a]);x=before[a-B.BASE:a-B.BASE+n];y=image[a-B.BASE:a-B.BASE+n]
            overlays.append(dict(ram=hex(a),bytes=n,changed_bytes=sum(u!=v for u,v in zip(x,y)),before_sha256=sha(x),after_sha256=sha(y)))
        images.append(dict(language=f['language'],ordinal=f['ordinal'],actual_parent_initial_whole_sha256=sha(before),
            combined_initial_whole_sha256=sha(image),actual_isolated_boundary_hashes=boundary,overlays=overlays))
    groups=share_groups(fixtures,bodies)
    proof=dict(parent_report_sha256=sha(c['report'].read_bytes()),parent_config_sha256=sha(parent_config.read_bytes()),parent_proof=pp,
        parent_raw_semantically_replayed_without_CPU=True,image_receipts=images,
        grouping=dict(literal_CPU_RAM_and_external_default_policy=True,sha256_for_reporting_only=True,groups=len(groups),origins=len(fixtures)),
        memory=dict(instruction_bytes=sum(n for n,_ in B.NATIVE_BODIES.values()),literal_pool_bytes=4,table_bytes=36,
            intercepted_default_bytes=4,frame=416,guard=56,native_peak=136,new_fill_bytes=0,callback_limit=B.LIMIT),
        limits=['One declared default FSResult model; no native default/ID/property/card/async effects',
                'Actual isolated whole boundaries rechecked in combined source derivation and actual guest; not a natural filesystem'])
    return fixtures,bodies,proof,groups,send_report,c['report']


def field_contract(cell,f,row):
    return F.compare(cell,f,row)


def check_contract(path,fixtures,send_report,translate_report,bodies):
    need(path.stat().st_size<=256*1024,'Send Translate bounded frozen contract256KiB');c=json.loads(path.read_bytes())
    need(wire(c)==wire(F.freeze(send_report,translate_report))and len(c['cells'])==16,'Send Translate actual parents bound to frozen contract')
    for f in fixtures:
        cell=next(x for x in c['cells']if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        for early in(False,True):
            want=B.predict(f,early)
            for phase,digest in B.boundaries(f,bodies,early).items():want['checkpoints'][phase]['whole_ram_sha256']=digest
            field_contract(cell,f,dict(want,entry=f['entry'],halt_pc=hex(B.RETURN),guard_before=f['guard'],guard_after=f['guard']))
    return c['cells']


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies);need(normal['observe']is True and off['observe']is False,'Send Translate actual observer domains')
    excluded=('observe','flow','reads','stores')
    need(wire({k:v for k,v in normal.items()if k not in excluded})==wire({k:v for k,v in off.items()if k not in excluded}),
         'Send Translate exact OFF CPU/RAM/model/checkpoint neutrality')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def counter(normal,early,bodies):
    B.require_result(normal,bodies);B.require_result(early,bodies)
    need(normal['policy']==dict(early_error=False)and early['policy']==dict(early_error=True)and normal['observe']is early['observe']is True,
        'Send Translate actual early_error counter domains')
    for key in('entry','returned','frame_before','frame_after','archive_before','archive_after','guard_before','guard_after','before_whole_ram_sha256',
               'whole_ram_sha256','flow','reads','steps','native_peak','observed_pcs'):
        need(wire(normal[key])==wire(early[key]),'Send Translate counter converges '+key)
    need(normal['model_stores']==[]and len(early['model_stores'])==1,'Send Translate positive0RAM vsnegative1hostwrite')
    differences=[i for i,(a,b)in enumerate(zip(normal['stores'],early['stores']))if wire(a)!=wire(b)]
    need(differences==[25],'Send Translate only native error-store preimage differs')
    a,b=normal['stores'][25],early['stores'][25]
    need(a['pc']==b['pc']=='0x20d6a40'and a['before']=='02000000'and b['before']==struct.pack('<I',a['value']).hex()and
        {k:v for k,v in a.items()if k!='before'}=={k:v for k,v in b.items()if k!='before'},'Send Translate native writer temporal preimage')
    disguised=copy.deepcopy(early);disguised['policy']=normal['policy'];disguised['services']=normal['services']
    disguised['model_stores']=normal['model_stores'];disguised['checkpoints']=normal['checkpoints']
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='Send Translate source-derived stores','Send Translate disguise rejected on actual native stores')
        return dict(final_CPU_and_entire_RAM_equal=True,native_flow_and_reads_equal=True,earlier_fields_accept_both=True,
            actual_native_error_store_before=[a['before'],b['before']],host_writes=[0,1],disguised_rejection=str(error))
    raise ValueError('Send Translate early host writer accepted as native-only assignment')


def require_report(r,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(r['schema']=='native-fs-send-translate-native-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        type(r['probe_only'])is bool and r['source_sha256']==source_identities()and wire(r['fixtures'])==wire(fixtures)and wire(r['proof'])==wire(proof)and
        wire(r['groups'])==wire(groups)and r['field_contract_sha256']==sha(contract_path.read_bytes()),'Send Translate replay source/input/proof/group binding')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];held=[];off=[];counters=[];names=[]
    for g in(groups[:1]if r['probe_only']else groups):
        normal=None
        for label,early,observe in(POLICIES[:1]if r['probe_only']else POLICIES):
            p=raw_dir/('%d-%s.json.gz'%(g['ordinal'],label));names.append(p.name);row=read_report(p)
            need(wire(row['fixture'])==wire(g['representative'])and row['policy']==dict(early_error=early)and row['observe']is observe,'Send Translate exact raw policy/member')
            B.require_result(row,bodies);cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            else:counters.append(dict(group=g['ordinal'],proof=counter(normal,row,bodies)))
            for member in g['members']:
                f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(names),'Send Translate exact raw set')
    for key,value in(('cases',cases),('field_holdout',held),('observer_off',off),('counters',counters)):
        need(wire(r[key])==wire(value),'Send Translate authenticated '+key)
    return True


def analyze(parent_config,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Send Translate strict modes')
    need(prepare_only or raw_dir is not None,'Send Translate requires private raw directory')
    require_host_budget();sources=source_identities()
    fs,bs,proof,groups,send_report,translate_report=prepare(parent_config)
    cells=check_contract(contract_path,fs,send_report,translate_report,bs)
    r=dict(schema='native-fs-send-translate-native-v1',source_sha256=sources,fixtures=fs,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['One explicit default-handler model, positive0RAM; no native default body/ID/property/card effects',
            'Old stable fields may accept early_error; native stores/preimages identify the writer separately',
            'Combined boundary actual whole hashes must equal prior isolated actual observations; full16/frame416 without masks',
            'CPU17 Cortex-A15 semantics, not ARM946 timing/IRQ; callback/async/non-sync/higher caller/SAVE/hardware excluded'])
    if not prepare_only:
        need(not raw_dir.exists()and not raw_dir.is_symlink()and SOURCE not in raw_dir.resolve().parents,'Send Translate fresh private raw output')
        raw_dir.mkdir(parents=True);cases=[];held=[];off=[];counters=[]
        for g in(groups[:1]if probe else groups):
            normal=None
            for label,early,observe in(POLICIES[:1]if probe else POLICIES):
                gc.collect();row=B.run(g['representative'],bs,early,observe);save(raw_dir/('%d-%s.json.gz'%(g['ordinal'],label)),row);B.require_result(row,bs)
                cases.append(dict(group=g['ordinal'],label=label,result=row))
                if label=='normal':normal=row
                elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bs)))
                else:counters.append(dict(group=g['ordinal'],proof=counter(normal,row,bs)))
                for member in g['members']:
                    f=next(f for f in fs if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                    cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
                print(g['ordinal'],label,'native Send Translate raw saved and checked',flush=True)
        r.update(cpu_executed=True,cases=cases,field_holdout=held,observer_off=off,counters=counters)
        require_report(r,fs,bs,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'Send Translate source drift');require_host_budget();return r


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','field-contract','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and SOURCE not in a.json.resolve().parents,'Send Translate fresh private report outside source')
        need(a.raw_dir is None or(a.json.resolve()!=a.raw_dir.resolve()and a.raw_dir.resolve()not in a.json.resolve().parents),
             'Send Translate report outside exact raw directory')
        r=analyze(a.parent_config,a.field_contract,a.raw_dir,a.prepare_only,a.probe);save(a.json,r)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print('Prepared without CPU'if a.prepare_only else'Native Send/Translate verified; default handler remains explicitly modeled')


if __name__=='__main__':main()
