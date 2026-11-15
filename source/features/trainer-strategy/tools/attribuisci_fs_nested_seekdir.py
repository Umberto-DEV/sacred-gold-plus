#!/usr/bin/env python3
"""Attribute zero-model nested SEEKDIR dispatch, separating projected inputs."""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,struct,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


S=load('nested_seekdir_qualified_cli',Path(__file__).with_name('attribuisci_fs_default_findpath.py'))
B=load('nested_seekdir_native_bench',Path(__file__).parents[1]/'test/fs_nested_seekdir_bench.py')
F=load('nested_seekdir_frozen_inputs',Path(__file__).with_name('congela_fs_nested_seekdir_contract.py'))
L=load('nested_seekdir_independent_reader',Path(__file__).with_name('rileggi_fs_nested_seekdir.py'))
need,sha,wire,save,read_report=S.need,S.sha,B.wire,S.save,S.read_report
need(sha(Path(S.__file__).read_bytes())=='6872533f514c0fd43ca6c7fae038626d5edc3fd2c2a43a6275c2b0031b2f4f5f','Nested SEEKDIR qualified CLI drift')
POLICIES=[('normal',False,True),('off',False,False),('clear_sync',True,True)]
CONFIG_KEYS={'parent_config','recipe_dir','reference','component_receipt','field_contract','report','raw_dir'}
SOURCE=S.SOURCE
require_host_budget=S.require_host_budget


def source_identities():
    ids=S.source_identities()
    for name in(__file__,B.__file__,F.__file__,L.__file__):
        p=Path(name);ids[str(p.resolve().relative_to(SOURCE))]=sha(p.read_bytes())
    return ids


def read_config(path):
    need(path.stat().st_size<=512*1024,'Nested SEEKDIR bounded replay config512KiB');c=json.loads(path.read_bytes())
    need(type(c)is dict and set(c)==CONFIG_KEYS and all(type(v)is str for v in c.values()),'Nested SEEKDIR exact replay string keys')
    return{k:Path(v)for k,v in c.items()}


def require_complete_parent(r):
    need(r['schema']=='native-fs-default-findpath-prefix-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        r['probe_only']is False and len(r['fixtures'])==16 and len(r['groups'])==2 and len(r['cases'])==7 and
        len(r['field_holdout'])==56 and len(r['observer_off'])==2 and len(r['counters'])==2 and len(r['lower_fill_controls'])==1,
        'Nested SEEKDIR complete zero-model parent, not probe')


def component_fields(receipt):
    need(receipt['case']=='P79'and receipt['new_CPU_executed']is False and receipt['new_compiler_invoked']is False and
         set(receipt['roms'])=={'EN','IT'},'Nested SEEKDIR offline component receipt')
    previous=None
    for item in receipt['roms'].values():
        regions=item['regions'];need(set(regions)==set(L.COMPONENTS),'Nested SEEKDIR exact code/table/gate set')
        current={}
        for name,(address,n,digest)in L.COMPONENTS.items():
            r=regions[name];body=bytes.fromhex(r['local_hex'])
            need(r['ram']==hex(address)and r['bytes']==n==len(body)and r['sha256']==sha(body)==digest,'Nested SEEKDIR authenticated '+name)
            current[address]=body
        need(item['default_slot2']==dict(ram='0x210e12c',target='0x20d6bec')and
             current[B.ENTRY][-4:]==struct.pack('<I',B.TABLE)and current[B.TABLE][8:12]==struct.pack('<I',B.RETURN),
             'Nested SEEKDIR pool/table/slot2 linkage')
        L.selected(current[B.ENTRY]);need(previous is None or previous==current,'Nested SEEKDIR language equality');previous=current
    return previous


def read_components(parent_config):
    need(sys.flags.optimize==0,'Nested SEEKDIR checks require normal assertions');require_host_budget()
    p78=S.read_config(parent_config);p77=S.S.read_config(p78['parent_config']);tc=S.S.T.read_config(p77['parent_config'])
    c=S.S.T.S.E.J.read_config(tc['parent_config']);p=S.S.T.S.E.J.read_config(c['parent_config'])
    _,_,settings=S.S.T.S.E.history(p['parent_config']);receipt=dict(case='P79',new_CPU_executed=False,new_compiler_invoked=False,roms={})
    for language,item in settings.items():
        path=Path(item['rom']);model=L.P.G.S.SHARED.read_current(path,language)
        with path.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            view=L.P.G.S.SHARED.gifts_audit.Arm9View(raw);regions={}
            for name,(address,n,digest)in L.COMPONENTS.items():
                body=view.read(address,n);need(body==L.P.G.piece(model['segments'],address,n)and sha(body)==digest,
                    'Nested SEEKDIR physical/decoded '+name)
                regions[name]=dict(ram=hex(address),rom_offset=hex(view.offset(address,n)),bytes=n,sha256=digest,local_hex=body.hex())
            receipt['roms'][language]=dict(input=model['record'],regions=regions,default_slot2=dict(ram='0x210e12c',target='0x20d6bec'))
        del model;gc.collect()
    components=component_fields(receipt);require_host_budget();return receipt,components


def require_recipe(recipe_dir,reference):
    body,recipe=S.S.T.require_recipe(recipe_dir,reference)
    need(body==L.object_text(recipe_dir/'fs-translate-command.o',400,L.C.BODIES['command'][2]),'Nested SEEKDIR retained independent ELF')
    L.selected(body)
    text=(reference/'lib/NitroSDK/src/fs/FS_command_default.c').read_text()
    definition=L.C.F.definition_source(text,'FSResult','FSi_SeekDirCommand')
    need(sha(definition.encode())=='707757982ff12c7b16ea554997052c18a15e9a5ac1c64eb16c354e526f73e74e','Nested SEEKDIR original default definition')
    return body,recipe


def share_groups(fixtures,bodies):
    groups=[];keys=[]
    for f in fixtures:
        image=B.initial_memory(f,bodies);key=(wire(f['entry']),image)
        if key not in keys:
            keys.append(key);groups.append(dict(ordinal=len(keys)-1,representative=f,members=[],initial_ram_sha256=sha(image),models=0))
        groups[keys.index(key)]['members'].append(dict(language=f['language'],ordinal=f['ordinal']))
    return groups


def prepare(parent_config,recipe_dir,reference,component_receipt):
    c=S.read_config(parent_config);r=read_report(c['report']);require_complete_parent(r)
    pf,pb,pp,pg,pr=S.prepare(c['parent_config'],c['recipe_dir'],c['reference'],c['component_receipt']);S.check_contract(c['field_contract'],pf,pr)
    S.require_report(r,pf,pb,pp,pg,c['field_contract'],c['raw_dir'])
    receipt,components=read_components(parent_config);old=read_report(component_receipt);need(component_fields(old)==components,'Nested SEEKDIR receipt equals current components')
    for language,item in receipt['roms'].items():
        prior=old['roms'][language];need(item['input']['sha256']==prior['input']['sha256']and item['input']['bytes']==prior['input']['bytes'],
             'Nested SEEKDIR current exact input identity')
        for name,region in item['regions'].items():need(region['rom_offset']==prior['regions'][name]['rom_offset'],'Nested SEEKDIR physical location')
    compiled,recipe=require_recipe(recipe_dir,reference);need(compiled==components[B.ENTRY],'Nested SEEKDIR ELF matches current whole400')
    for a,body in components.items():need(a not in pb or pb[a]==body,'Nested SEEKDIR retained component equality')
    bodies={**pb,**components};fixtures=[];images=[]
    for parent in pf:
        member=dict(language=parent['language'],ordinal=parent['ordinal']);g=next(g for g in pg if member in g['members'])
        row=next(x['result']for x in r['cases']if x['group']==g['ordinal']and x['label']=='normal');inp=F.after_state(row)
        image=bytearray(S.B.initial_memory(parent,pb));need(sha(image)==row['before_whole_ram_sha256'],'Nested SEEKDIR actual parent BEFORE image')
        need(wire(row['stores'])==wire(S.B.predict(parent)['stores']),'Nested SEEKDIR actual/source nine native PUSH words')
        for w in row['stores']:
            i=w['address']-B.BASE;need(image[i:i+4].hex()==w['before'],'Nested SEEKDIR actual parent preimage');struct.pack_into('<I',image,i,w['value'])
        need(sha(image)==row['whole_ram_sha256'],'Nested SEEKDIR reconstructed observed parent AFTER hash')
        lo,hi=B.FRAME-B.BASE,B.TOP-B.BASE;f={k:parent[k]for k in('language','ordinal','plus','seed')}
        f.update(entry=row['returned'],frame=bytes(image[lo:hi]).hex(),archive_before=row['archive_after'],guard=bytes(image[lo-56:lo]).hex(),
            parent_default_fixture=parent,parent_native_stores=row['stores'],observed_parent_before_whole_sha256=row['before_whole_ram_sha256'],
            observed_parent_after_whole_sha256=row['whole_ram_sha256'],provenance=dict(parent_group=g['ordinal'],parent_report_sha256=sha(c['report'].read_bytes()),
                parent_after_whole_hash_observed=True,parent_after_RAM_blob_available=False,new24_guard='Whole-derived; no new fill'))
        before=B.parent_memory(f,bodies);initial=B.initial_memory(f,bodies);a=before[B.RETURN-B.BASE:B.RETURN-B.BASE+4];b=components[B.RETURN]
        fixtures.append(f);images.append(dict(language=f['language'],ordinal=f['ordinal'],input=inp,observed_parent_after_whole_sha256=sha(before),
            initial_whole_sha256=sha(initial),new_guard24_sha256=sha(bytes.fromhex(f['guard'])[:24]),
            overlay=dict(ram=hex(B.RETURN),bytes=4,changed_bytes=sum(x!=y for x,y in zip(a,b)),before_sha256=sha(a),after_sha256=sha(b))))
    groups=share_groups(fixtures,bodies)
    proof=dict(parent_report_sha256=sha(c['report'].read_bytes()),parent_config_sha256=sha(parent_config.read_bytes()),parent_proof=pp,
        parent_raw_semantically_replayed_without_CPU=True,recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=recipe,
        components=receipt,component_receipt_sha256=sha(component_receipt.read_bytes()),image_receipts=images,
        grouping=dict(literal_CPU_RAM_only=True,models=0,groups=len(groups),origins=len(fixtures)),
        memory=dict(parent_after_hash_observed=True,parent_after_blob_available=False,actual_parent_writes=9,compiled_bytes=400,
            selected_instruction_bytes=96,selected_native_PCs=24,stopped_new_gate_bytes=4,frame=544,guard=56,new_derived_guard_bytes=24,native_peak=24,new_fill_bytes=0),
        limits=['Only nested dispatch to stopped default; no SeekDir body/result or natural filesystem',
                'Clear-sync is a declared input derivative rejected by strict actual-input comparison'])
    return fixtures,bodies,proof,groups,c['report']


def check_contract(path,fixtures,parent_report):
    need(path.stat().st_size<=256*1024,'Nested SEEKDIR bounded frozen contract256KiB');c=json.loads(path.read_bytes())
    need(wire(c)==wire(F.freeze(parent_report))and len(c['cells'])==16,'Nested SEEKDIR frozen actual parent binding')
    for f in fixtures:
        cell=next(x for x in c['cells']if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        for clear in(False,True):
            row=dict(B.predict(f,clear),entry=f['entry'],policy=dict(clear_sync=clear))
            if clear:F.compare_projection(cell,f,row)
            else:F.compare_input(cell,f,row)
    return c['cells']


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies);need(normal['observe']is True and off['observe']is False,'Nested SEEKDIR OFF domains')
    excluded=('observe','flow','reads','stores')
    need(wire({k:v for k,v in normal.items()if k not in excluded})==wire({k:v for k,v in off.items()if k not in excluded}),
         'Nested SEEKDIR exact OFF CPU/RAM/checkpoint neutrality')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def counter(normal,projected,bodies):
    B.require_result(normal,bodies);B.require_result(projected,bodies)
    need(normal['policy']==dict(clear_sync=False)and projected['policy']==dict(clear_sync=True)and normal['observe']is projected['observe']is True,
         'Nested SEEKDIR actual clear-sync input control')
    for key in('entry','returned','frame_before','frame_after','archive_after','guard_before','guard_after','whole_ram_sha256','steps','native_peak','observed_pcs'):
        need(wire(normal[key])==wire(projected[key]),'Nested SEEKDIR projected final convergence '+key)
    need(normal['before_whole_ram_sha256']!=projected['before_whole_ram_sha256']and normal['archive_before']!=projected['archive_before']and
         normal['input_projection']==[]and len(projected['input_projection'])==1 and normal['host_stores']==projected['host_stores']==[],
         'Nested SEEKDIR true input derivative, no runtime host writes')
    flows=[i for i,(a,b)in enumerate(zip(normal['flow'],projected['flow']))if wire(a)!=wire(b)]
    reads=[i for i,(a,b)in enumerate(zip(normal['reads'],projected['reads']))if wire(a)!=wire(b)]
    stores=[i for i,(a,b)in enumerate(zip(normal['stores'],projected['stores']))if wire(a)!=wire(b)]
    need(flows==[10,11]and reads==[2]and stores==[6],'Nested SEEKDIR exact temporal differences despite same counts')
    a,b=normal['stores'][6],projected['stores'][6]
    need(a['pc']==b['pc']=='0x20d68f4'and a['before']=='13020000'and b['before']=='13000000'and
         {k:v for k,v in a.items()if k!='before'}=={k:v for k,v in b.items()if k!='before'},'Nested SEEKDIR idempotent flag writer preimage')
    disguised=copy.deepcopy(projected)
    for key in('policy','input_projection','archive_before','before_whole_ram_sha256','checkpoints'):disguised[key]=normal[key]
    try:B.require_result(disguised,bodies)
    except ValueError as error:need(str(error)=='Nested SEEKDIR source-derived flow','Nested SEEKDIR input/checkpoint camouflage exposes native CPU contexts')
    else:raise ValueError('Nested SEEKDIR disguised input accepted as actual')
    disguised['flow']=normal['flow'];disguised['reads']=normal['reads']
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='Nested SEEKDIR source-derived stores','Nested SEEKDIR forged CPU/read transcript still exposes native preimage')
        return dict(initial_CPU_equal=True,initial_RAM_different=True,final_CPU_and_entire_RAM_equal=True,models=0,runtime_host_writes=0,
            native_context_differences=flows,native_read_differences=reads,native_store_preimage_differences=stores,
            input_and_checkpoint_camouflage_rejected_on='flow',after_CPU_and_read_transcript_forgery_rejected_on='stores')
    raise ValueError('Nested SEEKDIR changed native preimage accepted')


def member_proofs(g,label,row,fixtures,cells):
    records=[]
    for member in g['members']:
        f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
        cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
        proof=F.compare_projection(cell,f,row)if label=='clear_sync'else F.compare_input(cell,f,row)
        records.append(dict(group=g['ordinal'],label=label,member=member,proof=proof))
    return records


def require_report(r,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(r['schema']=='native-fs-nested-seekdir-dispatch-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
         type(r['probe_only'])is bool and r['source_sha256']==source_identities()and wire(r['fixtures'])==wire(fixtures)and wire(r['proof'])==wire(proof)and
         wire(r['groups'])==wire(groups)and r['field_contract_sha256']==sha(contract_path.read_bytes()),'Nested SEEKDIR replay source/input/proof/group binding')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];held=[];rejected=[];off=[];counters=[];names=[]
    for g in(groups[:1]if r['probe_only']else groups):
        normal=None
        for label,clear,observe in(POLICIES[:1]if r['probe_only']else POLICIES):
            name='%d-%s.json.gz'%(g['ordinal'],label);names.append(name);row=read_report(raw_dir/name)
            need(wire(row['fixture'])==wire(g['representative'])and row['policy']==dict(clear_sync=clear)and row['observe']is observe,
                 'Nested SEEKDIR raw representative and requested projection')
            B.require_result(row,bodies);cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            else:counters.append(dict(group=g['ordinal'],proof=counter(normal,row,bodies)))
            (rejected if clear else held).extend(member_proofs(g,label,row,fixtures,cells))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(names),'Nested SEEKDIR exact raw set')
    for key,value in(('cases',cases),('field_holdout',held),('projected_input_rejections',rejected),('observer_off',off),('counters',counters)):
        need(wire(r[key])==wire(value),'Nested SEEKDIR authenticated '+key)
    return True


def analyze(parent_config,recipe_dir,reference,component_receipt,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Nested SEEKDIR strict modes')
    need(prepare_only or raw_dir is not None,'Nested SEEKDIR requires private raw directory');require_host_budget();sources=source_identities()
    fs,bs,proof,groups,parent=prepare(parent_config,recipe_dir,reference,component_receipt);cells=check_contract(contract_path,fs,parent)
    r=dict(schema='native-fs-nested-seekdir-dispatch-v1',source_sha256=sources,fixtures=fs,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['Zero service models; stops before default SeekDir executes or returns a result',
            'Actual normal/OFF inputs and deliberately projected clear-sync inputs have distinct frozen verdicts',
            'Observed parent AFTER hash authenticates reconstructed RAM; new24 guard bytes not parent window capture',
            'CPU17 Cortex-A15 semantics, not ARM946 timing/IRQ; FNT/card/natural filesystem/higher caller/SAVE/hardware excluded'])
    if not prepare_only:
        need(not raw_dir.exists()and not raw_dir.is_symlink()and SOURCE not in raw_dir.resolve().parents,'Nested SEEKDIR fresh private raw output')
        raw_dir.mkdir(parents=True);cases=[];held=[];rejected=[];off=[];counters=[]
        for g in(groups[:1]if probe else groups):
            normal=None
            for label,clear,observe in(POLICIES[:1]if probe else POLICIES):
                gc.collect();row=B.run(g['representative'],bs,clear,observe);save(raw_dir/('%d-%s.json.gz'%(g['ordinal'],label)),row);B.require_result(row,bs)
                cases.append(dict(group=g['ordinal'],label=label,result=row))
                if label=='normal':normal=row
                elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bs)))
                else:counters.append(dict(group=g['ordinal'],proof=counter(normal,row,bs)))
                (rejected if clear else held).extend(member_proofs(g,label,row,fs,cells))
                print(g['ordinal'],label,'nested SEEKDIR raw saved and checked',flush=True)
        r.update(cpu_executed=True,cases=cases,field_holdout=held,projected_input_rejections=rejected,observer_off=off,counters=counters)
        require_report(r,fs,bs,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'Nested SEEKDIR source drift');require_host_budget();return r


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','json'):p.add_argument('--'+name,type=Path,required=True)
    for name in('recipe-dir','reference','component-receipt','field-contract','raw-dir'):p.add_argument('--'+name,type=Path)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--export-components',action='store_true');mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and SOURCE not in a.json.resolve().parents,'Nested SEEKDIR fresh private report')
        need(a.raw_dir is None or(a.json.resolve()!=a.raw_dir.resolve()and a.raw_dir.resolve()not in a.json.resolve().parents),'Nested SEEKDIR report outside exact raw directory')
        if a.export_components:r,_=read_components(a.parent_config)
        else:
            need(all(x is not None for x in(a.recipe_dir,a.reference,a.component_receipt,a.field_contract)),'Nested SEEKDIR recipe/reference/component receipt/field contract required')
            r=analyze(a.parent_config,a.recipe_dir,a.reference,a.component_receipt,a.field_contract,a.raw_dir,a.prepare_only,a.probe)
        save(a.json,r)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print('Components exported without compiler/CPU'if a.export_components else'Prepared without CPU'if a.prepare_only else'Native nested SEEKDIR dispatch verified; selected handler remains unexecuted')


if __name__=='__main__':main()
