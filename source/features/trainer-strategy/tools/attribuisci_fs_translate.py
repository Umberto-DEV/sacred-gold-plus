#!/usr/bin/env python3
"""Attribute native Translate with one declared value-only default handler."""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,struct,subprocess,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


S=load('translate_qualified_send_cli',Path(__file__).with_name('attribuisci_fs_send_native_callees.py'))
B=load('translate_native_bench',Path(__file__).parents[1]/'test/fs_translate_bench.py')
F=load('translate_fields',Path(__file__).with_name('congela_fs_translate_contract.py'))
L=load('translate_independent_reader',Path(__file__).with_name('rileggi_fs_translate.py'));M=L.C
need,sha,wire,save,read_report=S.need,S.sha,B.wire,S.save,S.read_report
need(sha(Path(S.__file__).read_bytes())=='8f2dd535a8f606a3ff95753d1d0de4fb4cc025a592f52a4e18e46a0618a7efd2','Translate qualified parent CLI drift')
POLICIES=[('normal',False,True),('off',False,False),('early_error',True,True)]
CONFIG_KEYS={'parent_config','recipe_dir','reference','component_receipt','field_contract','report','raw_dir'}
RECIPE=Path(__file__).parents[1]/'sorgenti/fs-translate.S'
COMPILER_SHA='fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'
require_host_budget=S.E.J.N.H.J.H.H.H.H.R.W.require_host_budget


def source_identities():
    ids=S.source_identities()
    for name in(__file__,B.__file__,F.__file__,L.__file__,M.__file__,RECIPE,M.D.C.LOADER):
        p=Path(name);ids[str(p.resolve().relative_to(S.E.J.P.SOURCE))]=sha(p.read_bytes())
    return ids


def read_config(path):
    need(path.stat().st_size<=512*1024,'Translate bounded replay config512KiB');c=json.loads(path.read_bytes())
    need(type(c)is dict and set(c)==CONFIG_KEYS and all(type(v)is str for v in c.values()),'Translate exact replay string keys')
    return{k:Path(v)for k,v in c.items()}


def require_complete_parent(r):
    need(r['schema']=='native-fs-send-native-callees-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        r['probe_only']is False,'Translate complete native Send parent, not probe')
    n=len(r['groups']);need(n>0 and len(r['fixtures'])==16 and len(r['cases'])==n*3 and len(r['field_holdout'])==32 and
        len(r['observer_off'])==n and len(r['counters'])==16,'Translate complete parent raw/OFF/field/counter grid')


def read_components(parent_config):
    need(sys.flags.optimize==0,'Translate checks require normal Python assertions')
    require_host_budget()
    c=S.E.J.read_config(parent_config);p=S.E.J.read_config(c['parent_config'])
    _,_,settings=S.E.history(p['parent_config']);receipt=dict(case='P76',new_CPU_executed=False,new_compiler_invoked=False,roms={})
    code=None
    for language,item in settings.items():
        rom=Path(item['rom']);model=S.E.J.P.G.S.SHARED.read_current(rom,language)
        with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            view=S.E.J.P.G.S.SHARED.gifts_audit.Arm9View(raw);regions={}
            for name,(address,n,digest)in F.COMPONENTS.items():
                body=view.read(address,n)
                need(body==S.E.J.P.G.piece(model['segments'],address,n)and sha(body)==digest,'Translate independent physical/decoded '+name)
                regions[name]=dict(ram=hex(address),rom_offset=hex(view.offset(address,n)),bytes=n,sha256=digest,local_hex=body.hex())
            receipt['roms'][language]=dict(input=model['record'],regions=regions,default_slot4=dict(ram='0x210e134',target='0x20d6db0'))
            current={B.ENTRY:bytes.fromhex(regions['code_and_pool']['local_hex']),B.TABLE:bytes.fromhex(regions['table']['local_hex']),
                     B.DEFAULT:bytes.fromhex(regions['default_gate']['local_hex'])}
            need(code is None or code==current,'Translate current EN/IT code/data equality');code=current
        del model;gc.collect()
    F.component_fields(receipt);require_host_budget();return receipt,code


def require_recipe(recipe_dir,reference):
    need(reference is not None,'Translate original pinned reference is required for header/source authentication')
    reference=reference.resolve()
    need(Path(subprocess.check_output(['git','-C',str(reference),'rev-parse','--show-toplevel'],text=True).strip()).resolve()==reference and
        subprocess.check_output(['git','-C',str(reference),'rev-parse','HEAD'],text=True).strip()==M.D.C.PIN and
        not subprocess.check_output(['git','-C',str(reference),'status','--porcelain']), 'Translate clean standalone pinned reference')
    r=json.loads((recipe_dir/'manifesto.json').read_bytes())
    need(r['schema']=='native-fs-translate-recipe-v1'and r['builder_sha256']==sha(Path(M.__file__).read_bytes())and
         r['recipe_sha256']==sha(RECIPE.read_bytes())and r['loader_sha256']==sha(Path(M.D.C.LOADER).read_bytes())and
         r['compiler_sha256']==COMPILER_SHA and r['rewrite_engine_sha256']==sha(Path(M.E.__file__).read_bytes()),'Translate recipe/compiler/source identity')
    need(len(r['commands'])==2 and {x['label']for x in r['commands']}=={'command','layout'},'Translate assembly and original-header commands required')
    for command in r['commands']:
        argv=command['argv'];need(command['exit_code']==0 and argv[1:4]==['--target=armv5te-none-eabi','-mcpu=arm946e-s','-marm']and
            sha(Path(argv[0]).read_bytes())==COMPILER_SHA and sha((recipe_dir/(command['label']+'.log')).read_bytes())==command['log_sha256'],
            'Translate authenticated compiler/flags/exit/log')
    need((recipe_dir/'layout.c').read_text()==M.LAYOUT and r['reference']['pin']==M.D.C.PIN and r['reference']['layout_passed']is True and
        len(r['reference']['header_sha256'])==18,'Translate original layout/18-header stage')
    for name,digest in r['reference']['header_sha256'].items():need(sha((reference/name).read_bytes())==digest,'Translate header drift '+name)
    source=reference/'lib/NitroSDK/src/fs/FS_command.c'
    need(r['reference']['source_sha256']==sha(source.read_bytes())and
         r['reference']['function_body_sha256']['FSi_TranslateCommand']==sha(M.F.definition_source(source.read_text(),'FSResult','FSi_TranslateCommand').encode()),
         'Translate original C definition identity')
    table=reference/r['default_table_source']['path'];text=table.read_text()
    a=text.index('FSResult (*const fsi_default_command[])(FSFile *) = {');b=text.index('\n};',a)+4
    need(r['default_table_source']['sha256']==sha(table.read_bytes())and r['default_table_source']['declaration_sha256']==sha(text[a:b].encode())and
         r['private_header_sha256']==sha((reference/'lib/NitroSDK/src/fs/fs_private.h').read_bytes()),'Translate default declaration/private source identity')
    obj=recipe_dir/'fs-translate-command.o';body=L.object_text(obj,400,B.BODY_SHA);L.split_extent(body)
    need(r['objects']['command']['object_sha256']==sha(obj.read_bytes())and r['objects']['command']['ram']==hex(B.ENTRY),
         'Translate retained ELF receipt and entry')
    return body,r


def share_groups(fixtures,bodies):
    groups=[];keys=[]
    for f in fixtures:
        image=B.initial_memory(f,bodies);key=(wire(f['entry']),image,f['default_result'])
        if key not in keys:
            keys.append(key);groups.append(dict(ordinal=len(keys)-1,representative=f,members=[],initial_ram_sha256=sha(image),
                model_policy=dict(default_result=f['default_result'],preserve_other_registers_and_CPSR=True)))
        groups[keys.index(key)]['members'].append(dict(language=f['language'],ordinal=f['ordinal']))
    return groups


def prepare(parent_config,recipe_dir,reference,component_receipt):
    c=S.E.J.read_config(parent_config);r=read_report(c['report']);require_complete_parent(r)
    pf,pb,pp,pg,paths=S.prepare(c['parent_config']);S.check_contract(c['field_contract'],pf,paths)
    S.require_report(r,pf,pb,pp,pg,c['field_contract'],c['raw_dir'])
    receipt,components=read_components(parent_config);old_receipt=read_report(component_receipt);F.component_fields(old_receipt)
    for language,item in receipt['roms'].items():
        need(wire(item['regions'])==wire(old_receipt['roms'][language]['regions'])and
             item['default_slot4']==old_receipt['roms'][language]['default_slot4'],'Translate offline receipt matches fresh physical/decoded bytes')
    body,recipe=require_recipe(recipe_dir,reference);need(body==components[B.ENTRY],'Translate ELF equals installed current bytes')
    bodies={**pb,**components};fixtures=[];images=[]
    for parent in pf:
        member=dict(language=parent['language'],ordinal=parent['ordinal']);g=next(g for g in pg if member in g['members'])
        row=next(x['result']for x in r['cases']if x['group']==g['ordinal']and x['label']=='normal');input_fields=F.prefix_state(row)
        frame=bytes.fromhex(row['frame_before']);arc=bytes.fromhex(row['archive_before'])
        image=bytearray(S.B.initial_memory(parent,pb));need(sha(bytes(image))==row['before_whole_ram_sha256'],'Translate actual parent initial whole image')
        for w in row['stores'][:17]:
            offset=w['address']-B.BASE;need(image[offset:offset+4].hex()==w['before'],'Translate actual upstream preimage');struct.pack_into('<I',image,offset,w['value'])
        f={k:parent[k]for k in('language','ordinal','plus','seed')}
        s=row['services'][0];f.update(default_result=parent['translated_result'],entry=s['entry'],frame=s['frame_before'],guard=row['guard_before'],
            archive_before=s['archive_before'],parent_send_fixture=parent,prefix_stores=row['stores'][:17],
            observed_before_Send_whole_sha256=row['before_whole_ram_sha256'],derived_boundary_whole_sha256=sha(bytes(image)),
            provenance=dict(parent_group=g['ordinal'],parent_report_sha256=sha(c['report'].read_bytes()),boundary_whole_observed=False,
                method='Observed-before Send plus17 actual/source-matched native writes, before any host write'))
        before=B.parent_memory(f,bodies);initial=B.initial_memory(f,bodies)
        deltas=[]
        for address in(B.ENTRY,B.TABLE,B.DEFAULT):
            n=len(bodies[address]);a=before[address-B.BASE:address-B.BASE+n];b=initial[address-B.BASE:address-B.BASE+n]
            deltas.append(dict(ram=hex(address),bytes=n,changed_bytes=sum(x!=y for x,y in zip(a,b)),before_sha256=sha(a),after_sha256=sha(b)))
        fixtures.append(f);images.append(dict(language=f['language'],ordinal=f['ordinal'],input=input_fields,
            derived_boundary_whole_sha256=f['derived_boundary_whole_sha256'],initial_whole_sha256=sha(initial),overlays=deltas))
    groups=share_groups(fixtures,bodies)
    proof=dict(parent_report_sha256=sha(c['report'].read_bytes()),parent_config_sha256=sha(parent_config.read_bytes()),parent_proof=pp,
        parent_raw_semantically_replayed_without_CPU=True,recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=recipe,
        components=receipt,component_receipt_sha256=sha(component_receipt.read_bytes()),image_receipts=images,
        grouping=dict(literal_CPU_RAM_and_external_default_policy=True,sha256_for_reporting_only=True,groups=len(groups),origins=len(fixtures)),
        memory=dict(boundary_forward_derived_from_observed_before=True,new_whole_capture=False,prefix_native_writes=17,
            instruction_bytes=396,literal_pool_bytes=4,table_bytes=36,intercepted_default_bytes=4,frame=416,guard=56,native_peak=24,new_fill_bytes=0),
        limits=['Default value-only model0RAM; callback/async/non-sync/default native/higher caller/SAVE/hardware excluded',
                'Earlier model fields exclude native R1/LR/saved24; separate full native oracle checks them'])
    return fixtures,bodies,proof,groups,c['report']


def field_contract(cell,f,row):
    need(all(type(cell[k])is type(f[k])and cell[k]==f[k]for k in('language','ordinal','plus','seed','default_result')),'Translate frozen origin/default policy')
    inp=cell['input'];need(wire(inp['entry'])==wire(f['entry'])and inp['frame416_sha256']==sha(bytes.fromhex(f['frame']))and
        inp['archive92_sha256']==sha(bytes.fromhex(f['archive_before']))and inp['guard56_sha256']==sha(bytes.fromhex(f['guard']))and
        inp['observed_before_Send_whole_sha256']==f['observed_before_Send_whole_sha256']and inp['prefix_stores_sha256']==sha(wire(f['prefix_stores']).encode())and
        inp['boundary_whole_sha_observed']is False,'Translate frozen actual input and forward provenance')
    need(wire(row['entry'])==wire(f['entry'])and row['halt_pc']==cell['expected_return_pc']==hex(B.RETURN),'Translate frozen actual entry/return PC')
    need(wire(F.stable_registers(row['returned']))==wire(cell['expected_stable_registers'])and row['returned'][0]==cell['expected_FSResult'],
         'Translate earlier stable registers and FSResult, not BOOL')
    need(wire(F.stable_frame(row['frame_after']))==wire(cell['expected_stable_frame_spans'])and
         sha(bytes.fromhex(row['archive_after']))==cell['expected_final_archive92_sha256'],'Translate earlier stable frame/archive fields')
    need(sha(bytes.fromhex(row['guard_before']))==sha(bytes.fromhex(row['guard_after']))==inp['guard56_sha256'],'Translate frozen unchanged guard')
    return dict(passed=True,stable_registers=14,excluded_volatile_indices=[1,14],excluded_native_saved24=True,
        writer_or_activation_proved_here=False,old_fields_can_accept_early_error=True)


def check_contract(path,fixtures,parent_report,component_receipt):
    need(path.stat().st_size<=256*1024,'Translate bounded frozen contract256KiB');c=json.loads(path.read_bytes())
    need(wire(c)==wire(F.freeze(parent_report,component_receipt))and len(c['cells'])==16,'Translate frozen parent/component binding')
    for f in fixtures:
        cell=next(x for x in c['cells']if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        for early in(False,True):
            p=B.predict(f,early);field_contract(cell,f,dict(p,entry=f['entry'],halt_pc=hex(B.RETURN),guard_before=f['guard'],guard_after=f['guard']))
    return c['cells']


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies);need(normal['observe']is True and off['observe']is False,'Translate actual observer domains')
    excluded=('observe','flow','reads','stores')
    need(wire({k:v for k,v in normal.items()if k not in excluded})==wire({k:v for k,v in off.items()if k not in excluded}),
         'Translate exact OFF CPU/RAM/model/checkpoint neutrality')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def counter(normal,early,bodies):
    B.require_result(normal,bodies);B.require_result(early,bodies)
    need(normal['policy']==dict(early_error=False)and early['policy']==dict(early_error=True)and normal['observe']is early['observe']is True,
        'Translate actual early_error counter domains')
    for key in('entry','returned','frame_before','frame_after','archive_before','archive_after','guard_before','guard_after','before_whole_ram_sha256',
               'whole_ram_sha256','flow','reads','steps','native_peak','observed_pcs'):
        need(wire(normal[key])==wire(early[key]),'Translate counter converges '+key)
    need(normal['model_stores']==[]and len(early['model_stores'])==1,'Translate positive0RAM vsnegative1hostwrite')
    differences=[i for i,(a,b)in enumerate(zip(normal['stores'],early['stores']))if wire(a)!=wire(b)]
    need(differences==[8],'Translate only last native error-store preimage differs')
    a,b=normal['stores'][8],early['stores'][8]
    need(a['pc']==b['pc']=='0x20d6a40'and a['before']=='02000000'and b['before']==struct.pack('<I',a['value']).hex()and
        {k:v for k,v in a.items()if k!='before'}=={k:v for k,v in b.items()if k!='before'},'Translate native writer temporal preimage')
    disguised=copy.deepcopy(early);disguised['policy']=normal['policy'];disguised['services']=normal['services']
    disguised['model_stores']=normal['model_stores'];disguised['checkpoints']=normal['checkpoints']
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='Translate source-derived stores','Translate disguise rejected on actual native stores')
        return dict(final_CPU_and_entire_RAM_equal=True,native_flow_and_reads_equal=True,earlier_fields_accept_both=True,
            actual_native_error_store_before=[a['before'],b['before']],host_writes=[0,1],disguised_rejection=str(error))
    raise ValueError('Translate early host writer accepted as native-only assignment')


def require_report(r,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(r['schema']=='native-fs-translate-isolated-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        type(r['probe_only'])is bool and r['source_sha256']==source_identities()and wire(r['fixtures'])==wire(fixtures)and wire(r['proof'])==wire(proof)and
        wire(r['groups'])==wire(groups)and r['field_contract_sha256']==sha(contract_path.read_bytes()),'Translate replay source/input/proof/group binding')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];held=[];off=[];counters=[];names=[]
    for g in(groups[:1]if r['probe_only']else groups):
        normal=None
        for label,early,observe in(POLICIES[:1]if r['probe_only']else POLICIES):
            p=raw_dir/('%d-%s.json.gz'%(g['ordinal'],label));names.append(p.name);row=read_report(p)
            need(wire(row['fixture'])==wire(g['representative'])and row['policy']==dict(early_error=early)and row['observe']is observe,'Translate exact raw policy/member')
            B.require_result(row,bodies);cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            elif label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            else:counters.append(dict(group=g['ordinal'],proof=counter(normal,row,bodies)))
            for member in g['members']:
                f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(names),'Translate exact raw set')
    for key,value in(('cases',cases),('field_holdout',held),('observer_off',off),('counters',counters)):
        need(wire(r[key])==wire(value),'Translate authenticated '+key)
    return True


def analyze(parent_config,recipe_dir,reference,component_receipt,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Translate strict modes')
    need(prepare_only or raw_dir is not None,'Translate requires private raw directory')
    S.E.J.N.H.J.H.H.H.H.R.W.require_host_budget();sources=source_identities()
    fs,bs,proof,groups,parent_report=prepare(parent_config,recipe_dir,reference,component_receipt)
    cells=check_contract(contract_path,fs,parent_report,component_receipt)
    r=dict(schema='native-fs-translate-isolated-v1',source_sha256=sources,fixtures=fs,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['One explicit default-handler model, positive0RAM; no native default body/ID/property/card effects',
            'Old stable fields may accept early_error; native stores/preimages identify the writer separately',
            'Boundary forward-derived, not a new whole capture; native R1/LR/saved24 independently source-checked',
            'CPU17 Cortex-A15 semantics, not ARM946 timing/IRQ; callback/async/non-sync/higher caller/SAVE/hardware excluded'])
    if not prepare_only:
        need(not raw_dir.exists()and not raw_dir.is_symlink()and S.E.J.P.SOURCE not in raw_dir.resolve().parents,'Translate fresh private raw output')
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
                print(g['ordinal'],label,'native Translate raw saved and checked',flush=True)
        r.update(cpu_executed=True,cases=cases,field_holdout=held,observer_off=off,counters=counters)
        require_report(r,fs,bs,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'Translate source drift');S.E.J.N.H.J.H.H.H.H.R.W.require_host_budget();return r


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','json'):p.add_argument('--'+name,type=Path,required=True)
    for name in('recipe-dir','reference','component-receipt','field-contract','raw-dir'):p.add_argument('--'+name,type=Path)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--export-components',action='store_true');mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and S.E.J.P.SOURCE not in a.json.resolve().parents,'Translate fresh private report outside source')
        need(a.raw_dir is None or(a.json.resolve()!=a.raw_dir.resolve()and a.raw_dir.resolve()not in a.json.resolve().parents),'Translate report outside exact raw directory')
        if a.export_components:r,_=read_components(a.parent_config)
        else:
            need(all(x is not None for x in(a.recipe_dir,a.reference,a.component_receipt,a.field_contract)),'Translate recipe/reference/component receipt/field contract required')
            r=analyze(a.parent_config,a.recipe_dir,a.reference,a.component_receipt,a.field_contract,a.raw_dir,a.prepare_only,a.probe)
        save(a.json,r)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print('Components exported without compiler/CPU'if a.export_components else'Prepared without CPU'if a.prepare_only else'Native Translate verified; default handler remains explicitly modeled')


if __name__=='__main__':main()
