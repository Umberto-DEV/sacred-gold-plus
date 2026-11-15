#!/usr/bin/env python3
"""Attribute the native default FindPath prefix with zero service models."""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,struct,subprocess,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


S=load('default_findpath_qualified_cli',Path(__file__).with_name('attribuisci_fs_send_translate_native.py'))
B=load('default_findpath_native_bench',Path(__file__).parents[1]/'test/fs_default_findpath_bench.py')
F=load('default_findpath_frozen_input',Path(__file__).with_name('congela_fs_default_findpath_contract.py'))
L=load('default_findpath_independent_reader',Path(__file__).with_name('rileggi_fs_default_findpath.py'));M=L.C
need,sha,wire,save,read_report=S.need,S.sha,B.wire,S.save,S.read_report
need(sha(Path(S.__file__).read_bytes())=='736f705ed610a7d548934edb30b3349917fbe6006416e4dfdf9b6a105f0af1e6','Default FindPath qualified CLI drift')
POLICIES=[('normal',False,None,True),('off',False,None,False),('prepush',True,None,True)]
CONFIG_KEYS={'parent_config','recipe_dir','reference','component_receipt','field_contract','report','raw_dir'}
RECIPE=Path(__file__).parents[1]/'sorgenti/fs-default-findpath-prefix.S'
COMPILER_SHA=S.T.COMPILER_SHA
SOURCE=S.SOURCE
require_host_budget=S.require_host_budget


def source_identities():
    ids=S.source_identities()
    for name in(__file__,B.__file__,F.__file__,L.__file__,M.__file__,RECIPE):
        p=Path(name);ids[str(p.resolve().relative_to(SOURCE))]=sha(p.read_bytes())
    return ids


def read_config(path):
    need(path.stat().st_size<=512*1024,'Default FindPath bounded replay config512KiB');c=json.loads(path.read_bytes())
    need(type(c)is dict and set(c)==CONFIG_KEYS and all(type(v)is str for v in c.values()),'Default FindPath exact replay string keys')
    return{k:Path(v)for k,v in c.items()}


def require_complete_parent(r):
    need(r['schema']=='native-fs-send-translate-native-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        r['probe_only']is False and len(r['fixtures'])==16 and len(r['groups'])==4 and len(r['cases'])==12 and
        len(r['field_holdout'])==48 and len(r['observer_off'])==4 and len(r['counters'])==4,'Default FindPath complete native parent, not probe')


def component_fields(receipt):
    need(receipt['case']=='P78'and receipt['new_CPU_executed']is False and receipt['new_compiler_invoked']is False and
         set(receipt['roms'])=={'EN','IT'},'Default FindPath offline component receipt')
    previous=None
    for item in receipt['roms'].values():
        r=item['region'];body=bytes.fromhex(r['local_hex'])
        need(r['ram']==hex(B.ENTRY)and r['bytes']==len(body)==484 and r['sha256']==sha(body)==B.OWNER_SHA,
             'Default FindPath exact retained owner484')
        need(r['prefix']['bytes']==28 and r['prefix']['sha256']==sha(body[:28])==B.PREFIX_SHA and
             bytes.fromhex(r['prefix']['local_hex'])==body[:28],'Default FindPath exact compiled prefix28')
        need(previous is None or previous==body,'Default FindPath current language equality');previous=body
    return previous


def read_components(parent_config):
    require_host_budget();cfg=S.read_config(parent_config);tc=S.T.read_config(cfg['parent_config'])
    c=S.T.S.E.J.read_config(tc['parent_config']);p=S.T.S.E.J.read_config(c['parent_config'])
    _,_,settings=S.T.S.E.history(p['parent_config']);receipt=dict(case='P78',new_CPU_executed=False,new_compiler_invoked=False,roms={})
    for language,item in settings.items():
        path=Path(item['rom']);model=L.P.G.S.SHARED.read_current(path,language)
        with path.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            view=L.P.G.S.SHARED.gifts_audit.Arm9View(raw);body=view.read(B.ENTRY,484)
            need(body==L.P.G.piece(model['segments'],B.ENTRY,484)and sha(body)==B.OWNER_SHA,'Default FindPath physical/decoded owner')
            code=L.split_prefix(body[:28]);r=dict(ram=hex(B.ENTRY),rom_offset=hex(view.offset(B.ENTRY,484)),bytes=484,
                sha256=sha(body),local_hex=body.hex(),prefix=dict(bytes=28,sha256=sha(body[:28]),local_hex=body[:28].hex(),
                instructions=[dict(pc=hex(x.address),mnemonic=x.mnemonic,operands=x.op_str)for x in code],stop=hex(B.RETURN),
                return_lr='0x20d6dcc',stack=184,saved_bytes=36,uninitialized_local_bytes=148))
            receipt['roms'][language]=dict(input=model['record'],region=r)
        del model;gc.collect()
    body=component_fields(receipt);require_host_budget();return receipt,body


def require_recipe(recipe_dir,reference):
    need(reference is not None,'Default FindPath original pinned reference is required for header/source authentication')
    reference=reference.resolve()
    need(Path(subprocess.check_output(['git','-C',str(reference),'rev-parse','--show-toplevel'],text=True).strip()).resolve()==reference and
        subprocess.check_output(['git','-C',str(reference),'rev-parse','HEAD'],text=True).strip()==M.D.C.PIN and
        not subprocess.check_output(['git','-C',str(reference),'status','--porcelain']), 'Default FindPath clean standalone pinned reference')
    r=json.loads((recipe_dir/'manifesto.json').read_bytes())
    need(r['schema']=='native-fs-default-findpath-prefix-recipe-v1'and r['builder_sha256']==sha(Path(M.__file__).read_bytes())and
         r['recipe_sha256']==sha(RECIPE.read_bytes())and r['loader_sha256']==sha(Path(M.D.C.LOADER).read_bytes())and
         r['compiler_sha256']==COMPILER_SHA and r['rewrite_engine_sha256']==sha(Path(M.E.__file__).read_bytes()),'Default FindPath recipe/compiler/source identity')
    need(len(r['commands'])==2 and {x['label']for x in r['commands']}=={'command','layout'},'Default FindPath assembly and original-header commands required')
    for command in r['commands']:
        argv=command['argv'];need(command['exit_code']==0 and argv[1:4]==['--target=armv5te-none-eabi','-mcpu=arm946e-s','-marm']and
            sha(Path(argv[0]).read_bytes())==COMPILER_SHA and sha((recipe_dir/(command['label']+'.log')).read_bytes())==command['log_sha256'],
            'Default FindPath authenticated compiler/flags/exit/log')
    need((recipe_dir/'layout.c').read_text()==M.LAYOUT and r['reference']['pin']==M.D.C.PIN and r['reference']['layout_passed']is True and
        len(r['reference']['header_sha256'])==18,'Default FindPath original layout/18-header stage')
    for name,digest in r['reference']['header_sha256'].items():need(sha((reference/name).read_bytes())==digest,'Default FindPath header drift '+name)
    source=reference/'lib/NitroSDK/src/fs/FS_command_default.c'
    need(r['reference']['source_sha256']==sha(source.read_bytes())and
         r['reference']['function_body_sha256']['FSi_FindPathCommand']==sha(M.F.definition_source(source.read_text(),'FSResult','FSi_FindPathCommand').encode()),
         'Default FindPath original C definition identity')
    obj=recipe_dir/'fs-default-findpath-command.o';body=L.object_text(obj,28,B.PREFIX_SHA);L.split_prefix(body)
    need(r['objects']['command']['object_sha256']==sha(obj.read_bytes())and r['objects']['command']['ram']==hex(B.ENTRY),
         'Default FindPath retained ELF receipt and entry')
    return body,r


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
    pf,pb,pp,pg,sp,tp=S.prepare(c['parent_config']);S.check_contract(c['field_contract'],pf,sp,tp,pb)
    S.require_report(r,pf,pb,pp,pg,c['field_contract'],c['raw_dir'])
    receipt,body=read_components(parent_config);old=read_report(component_receipt);need(component_fields(old)==body,'Default FindPath receipt matches current owner')
    for language,item in receipt['roms'].items():
        current,prior=item['region'],old['roms'][language]['region']
        need(current['rom_offset']==prior['rom_offset']and item['input']['sha256']==old['roms'][language]['input']['sha256']and
             item['input']['bytes']==old['roms'][language]['input']['bytes'],'Default FindPath current component identity/physical position')
    compiled,recipe=require_recipe(recipe_dir,reference);need(compiled==body[:28],'Default FindPath ELF matches installed prefix')
    bodies={**pb,B.ENTRY:body};fixtures=[];images=[]
    for parent in pf:
        member=dict(language=parent['language'],ordinal=parent['ordinal']);g=next(g for g in pg if member in g['members'])
        row=next(x['result']for x in r['cases']if x['group']==g['ordinal']and x['label']=='normal');inp=F.prefix_state(row)
        source=S.B.predict(parent);stores=row['stores'][:24];need(wire(stores)==wire(source['stores'][:24]),'Default FindPath actual/source24 writes')
        image=bytearray(S.B.initial_memory(parent,pb));need(sha(image)==row['before_whole_ram_sha256'],'Default FindPath actual Send initial image')
        for w in stores:
            i=w['address']-B.BASE;need(image[i:i+4].hex()==w['before'],'Default FindPath actual prefix preimage');struct.pack_into('<I',image,i,w['value'])
        cp=row['checkpoints']['default_entry'];need(wire(cp)==wire(source['checkpoints']['default_entry']),'Default FindPath source delivered actual full entry')
        lo,hi=B.FRAME-B.BASE,B.TOP-B.BASE
        f={k:parent[k]for k in('language','ordinal','plus','seed')}
        f.update(entry=cp['regs'],frame=bytes(image[lo:hi]).hex(),archive_before=cp['archive'],guard=bytes(image[lo-56:lo]).hex(),
            parent_send_fixture=parent,prefix_stores=stores,observed_before_Send_whole_sha256=row['before_whole_ram_sha256'],
            derived_boundary_whole_sha256=sha(image),provenance=dict(parent_group=g['ordinal'],parent_report_sha256=sha(c['report'].read_bytes()),
                default_entry_whole_observed=False,additional104='Derived from authenticated whole parent; no new fill'))
        before=B.parent_memory(f,bodies);initial=B.initial_memory(f,bodies);a=before[B.ENTRY-B.BASE:B.ENTRY-B.BASE+484];b=body
        images.append(dict(language=f['language'],ordinal=f['ordinal'],input=inp,derived_default_boundary_whole_sha256=sha(before),
            initial_whole_sha256=sha(initial),additional104_sha256=sha(bytes.fromhex(f['guard'])+bytes.fromhex(f['frame'])[:48]),
            overlay=dict(ram=hex(B.ENTRY),bytes=484,changed_bytes=sum(x!=y for x,y in zip(a,b)),before_sha256=sha(a),after_sha256=sha(b))))
        fixtures.append(f)
    groups=share_groups(fixtures,bodies)
    proof=dict(parent_report_sha256=sha(c['report'].read_bytes()),parent_config_sha256=sha(parent_config.read_bytes()),parent_proof=pp,
        parent_raw_semantically_replayed_without_CPU=True,recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=recipe,
        components=receipt,component_receipt_sha256=sha(component_receipt.read_bytes()),image_receipts=images,
        grouping=dict(literal_CPU_RAM_only=True,models=0,ancestral_result_is_not_external_policy=True,groups=len(groups),origins=len(fixtures)),
        memory=dict(default_boundary_forward_derived=True,new_whole_capture=False,prefix_native_writes=24,compiled_bytes=28,retained_owner_bytes=484,
            native_instruction_bytes=28,frame=520,guard=56,additional_derived_bytes=104,native_peak=184,new_fill_bytes=0),
        limits=['Only prefix to stopped nested Translate; no default result or natural filesystem',
                'Positive no host writes/models; prepush fault and lower39 control explicitly separate'])
    return fixtures,bodies,proof,groups,c['report']


def field_contract(cell,f,row):
    return F.compare_input(cell,f,row)


def check_contract(path,fixtures,parent_report):
    need(path.stat().st_size<=256*1024,'Default FindPath bounded frozen contract256KiB');c=json.loads(path.read_bytes())
    need(wire(c)==wire(F.freeze(parent_report))and len(c['cells'])==16,'Default FindPath frozen actual parent binding')
    for f in fixtures:
        cell=next(x for x in c['cells']if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        for prepush,fill in((False,None),(True,None),(False,0x39)):
            want=B.predict(f,prepush,fill);field_contract(cell,f,dict(want,entry=f['entry']))
    return c['cells']


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies);need(normal['observe']is True and off['observe']is False,'Default FindPath OFF domains')
    excluded=('observe','flow','reads','stores')
    need(wire({k:v for k,v in normal.items()if k not in excluded})==wire({k:v for k,v in off.items()if k not in excluded}),
         'Default FindPath full OFF CPU/RAM/checkpoint neutrality')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def counter(normal,fault,bodies):
    B.require_result(normal,bodies);B.require_result(fault,bodies)
    need(normal['policy']==dict(prepush=False,lower_fill=None)and fault['policy']==dict(prepush=True,lower_fill=None)and
         normal['observe']is fault['observe']is True,'Default FindPath actual prepush counter domains')
    for key in('entry','returned','frame_before','frame_after','archive_before','archive_after','guard_before','guard_after',
               'before_whole_ram_sha256','whole_ram_sha256','flow','reads','steps','native_peak','checkpoints'):
        need(wire(normal[key])==wire(fault[key]),'Default FindPath counter converges '+key)
    need(normal['host_stores']==[]and len(fault['host_stores'])==9 and normal['services']==fault['services']==[],
         'Default FindPath zero service models and explicit0/9 host stores')
    differences=[i for i,(a,b)in enumerate(zip(normal['stores'],fault['stores']))if wire(a)!=wire(b)]
    need(differences==list(range(9)),'Default FindPath all nine native PUSH preimages differ')
    for a,b in zip(normal['stores'],fault['stores']):
        need({k:v for k,v in a.items()if k!='before'}=={k:v for k,v in b.items()if k!='before'}and
             b['before']==struct.pack('<I',a['value']).hex(),'Default FindPath host prewrite temporal evidence')
    disguised=copy.deepcopy(fault);disguised['policy']=normal['policy'];disguised['host_stores']=normal['host_stores']
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='Default FindPath source-derived stores','Default FindPath disguise rejected on native stores')
        return dict(final_CPU_and_entire_RAM_equal=True,initial_CPU_and_RAM_equal=True,models=0,host_writes=[0,9],
            native_store_preimage_differences=differences,disguised_rejection=str(error))
    raise ValueError('Default FindPath host prepush accepted as native-only preparation')


def lower_pair(normal,filled,bodies):
    B.require_result(normal,bodies);B.require_result(filled,bodies)
    need(normal['policy']==dict(prepush=False,lower_fill=None)and filled['policy']==dict(prepush=False,lower_fill=0x39),
         'Default FindPath actual lower104 fill control')
    for key in('entry','returned','flow','stores','reads','steps','native_peak','archive_before','archive_after','services','host_stores'):
        need(wire(normal[key])==wire(filled[key]),'Default FindPath lower104-neutral '+key)
    for key in('frame_before','frame_after'):
        a,b=bytes.fromhex(normal[key]),bytes.fromhex(filled[key]);need(a[48:]==b[48:]and b[:48]==b'9'*48,'Default FindPath only added local48 changed')
    need(filled['guard_before']==filled['guard_after']=='39'*56 and normal['before_whole_ram_sha256']!=filled['before_whole_ram_sha256']and
         normal['whole_ram_sha256']!=filled['whole_ram_sha256'],'Default FindPath true104-byte input derivative, no whole-hash normalization')
    return dict(execution_neutral=True,changed_input_bytes=104,whole_RAM_hashes_differ=True,no_claim_of_captured_lower104=True)


def group_policies(g,probe):
    return POLICIES[:1]if probe else POLICIES+([('lower39',False,0x39,True)]if g['ordinal']==0 else[])


def require_report(r,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(r['schema']=='native-fs-default-findpath-prefix-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
         type(r['probe_only'])is bool and r['source_sha256']==source_identities()and wire(r['fixtures'])==wire(fixtures)and
         wire(r['proof'])==wire(proof)and wire(r['groups'])==wire(groups)and r['field_contract_sha256']==sha(contract_path.read_bytes()),
         'Default FindPath replay source/input/proof/group binding')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];held=[];off=[];counters=[];lower=[];names=[]
    for g in(groups[:1]if r['probe_only']else groups):
        normal=None
        for label,prepush,fill,observe in group_policies(g,r['probe_only']):
            name='%d-%s.json.gz'%(g['ordinal'],label);names.append(name);row=read_report(raw_dir/name)
            need(wire(row['fixture'])==wire(g['representative'])and row['policy']==dict(prepush=prepush,lower_fill=fill)and row['observe']is observe,
                 'Default FindPath raw representative and requested policy')
            B.require_result(row,bodies);cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            elif label=='prepush':counters.append(dict(group=g['ordinal'],proof=counter(normal,row,bodies)))
            else:lower.append(dict(group=g['ordinal'],proof=lower_pair(normal,row,bodies)))
            for member in g['members']:
                f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(names),'Default FindPath exact raw set')
    for key,value in(('cases',cases),('field_holdout',held),('observer_off',off),('counters',counters),('lower_fill_controls',lower)):
        need(wire(r[key])==wire(value),'Default FindPath authenticated '+key)
    return True


def analyze(parent_config,recipe_dir,reference,component_receipt,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Default FindPath strict modes')
    need(prepare_only or raw_dir is not None,'Default FindPath requires private raw directory');require_host_budget();sources=source_identities()
    fs,bs,proof,groups,parent=prepare(parent_config,recipe_dir,reference,component_receipt);cells=check_contract(contract_path,fs,parent)
    r=dict(schema='native-fs-default-findpath-prefix-v1',source_sha256=sources,fixtures=fs,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['Prefix stops before nested Translate; no FSResult/default completion/natural filesystem',
            'Zero service models; prepush is explicit host fault, lower39 is an input derivative',
            'Entry whole identity and additional104 bytes forward-derived, not a new boundary capture',
            'CPU17 Cortex-A15 semantics, not ARM946 timing/IRQ delivery; higher caller/SAVE/hardware excluded'])
    if not prepare_only:
        need(not raw_dir.exists()and not raw_dir.is_symlink()and SOURCE not in raw_dir.resolve().parents,'Default FindPath fresh private raw output')
        raw_dir.mkdir(parents=True);cases=[];held=[];off=[];counters=[];lower=[]
        for g in(groups[:1]if probe else groups):
            normal=None
            for label,prepush,fill,observe in group_policies(g,probe):
                gc.collect();row=B.run(g['representative'],bs,prepush,fill,observe);save(raw_dir/('%d-%s.json.gz'%(g['ordinal'],label)),row);B.require_result(row,bs)
                cases.append(dict(group=g['ordinal'],label=label,result=row))
                if label=='normal':normal=row
                elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bs)))
                elif label=='prepush':counters.append(dict(group=g['ordinal'],proof=counter(normal,row,bs)))
                else:lower.append(dict(group=g['ordinal'],proof=lower_pair(normal,row,bs)))
                for member in g['members']:
                    f=next(f for f in fs if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                    cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
                print(g['ordinal'],label,'default FindPath prefix raw saved and checked',flush=True)
        r.update(cpu_executed=True,cases=cases,field_holdout=held,observer_off=off,counters=counters,lower_fill_controls=lower)
        require_report(r,fs,bs,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'Default FindPath source drift');require_host_budget();return r


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','json'):p.add_argument('--'+name,type=Path,required=True)
    for name in('recipe-dir','reference','component-receipt','field-contract','raw-dir'):p.add_argument('--'+name,type=Path)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--export-components',action='store_true');mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and SOURCE not in a.json.resolve().parents,'Default FindPath fresh private report')
        need(a.raw_dir is None or(a.json.resolve()!=a.raw_dir.resolve()and a.raw_dir.resolve()not in a.json.resolve().parents),'Default FindPath report outside exact raw directory')
        if a.export_components:r,_=read_components(a.parent_config)
        else:
            need(all(x is not None for x in(a.recipe_dir,a.reference,a.component_receipt,a.field_contract)),'Default FindPath recipe/reference/component receipt/field contract required')
            r=analyze(a.parent_config,a.recipe_dir,a.reference,a.component_receipt,a.field_contract,a.raw_dir,a.prepare_only,a.probe)
        save(a.json,r)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print('Components exported without CPU/compiler'if a.export_components else'Prepared without CPU'if a.prepare_only else'Native default FindPath prefix verified; nested filesystem remains excluded')


if __name__=='__main__':main()
