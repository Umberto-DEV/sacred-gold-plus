#!/usr/bin/env python3
"""Attribute native Release/IRQ from authenticated ExecuteSync service preimages.

Empty Wakeup is a value-only model. Stale-error is an explicit input projection,
not natural Translate state. Release is void; its residual R0 is not a BOOL.
"""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('release_qualified_execute_cli',Path(__file__).with_name('attribuisci_fs_exec_sync.py'))
B=load('release_source_bench',Path(__file__).parents[1]/'test/fs_release_bench.py')
L=load('release_independent_reader',Path(__file__).with_name('rileggi_fs_release.py'))
P,need,sha,wire,save=H.P,H.need,H.sha,B.wire,H.save
need(sha(Path(H.__file__).read_bytes())=='835dd29fd7a07fe5c2160b19764c14cf4db23fb8ac03f925f40a820a824eac49','Release qualified ExecuteSync verifier drift')
PREPARE_KEYS={'rom','language','parent_report','find_parent_report','capture_source','objects','strategy_object',
    'read_recipe','wait_recipe','find_recipe','send_recipe','recipe_dir'}
POLICIES=[('normal',{}),('off',dict(observe=False)),('stale_error2',dict(stale_error=True)),
    ('void_ones',dict(wake_value=0xFFFFFFFF)),('clobber',dict(clobber=True)),('fill39',dict(fill=0x39))]


def source_identities():
    ids=H.source_identities()
    for path in(__file__,B.__file__,L.__file__,L.C.__file__,Path(__file__).parents[1]/'sorgenti/fs-release.S'):
        p=Path(path);ids[str(p.resolve().relative_to(P.SOURCE))]=sha(p.read_bytes())
    return ids


def read_parent_config(path,rom,language):
    need(path.stat().st_size<=512*1024,'Release bounded parent config512KiB')
    config=json.loads(path.read_bytes());c=config[language]['prepare']
    need(type(c)is dict and set(c)==PREPARE_KEYS and c['language']==language and type(c['language'])is str,
         'Release exact ExecuteSync prepare keys/language')
    for key,value in c.items():
        need(type(value)is str or(key=='capture_source'and value is None),'Release parent config path/language must be string or optional null source')
    need(Path(c['rom']).resolve()==rom.resolve(),'Release parent config exact selected ROM path')
    return {k:v if k=='language'else None if v is None else Path(v)for k,v in c.items()}


def check_parent(parent,language,fixtures,bodies,proof):
    need(parent['schema']=='native-fs-exec-sync-isolated-v1'and parent['language']==language and
         parent['cpu_executed']is True and parent['probe_only']is False and
         wire(parent['source_sha256'])==wire(H.source_identities())and wire(parent['proof'])==wire(proof)and
         wire(parent['fixtures'])==wire(fixtures),'Release exact parent identity/source/fixtures/proof')
    need(len(parent['cases'])==32 and len(parent['observer_off'])==len(parent['counters'])==4,'Release complete ExecuteSync parent matrix')
    for i,f in enumerate(fixtures):
        group=parent['cases'][i*8:(i+1)*8]
        for cell,(label,options)in zip(group,H.POLICIES):
            r=cell['result'];p=dict(result=0,void_value=0,clobber=False,release_error=None)
            p.update({k:v for k,v in options.items()if k in p})
            need(cell['label']==label and wire(r['fixture'])==wire(f)and
                 wire((r['policy'],r['observe'],r['fill']))==wire((p,options.get('observe',True),options.get('fill',0xA5))),
                 'Release exact parent policy/cell grid')
            H.B.require_result(r,bodies)
        normal,off,counter=group[0]['result'],group[1]['result'],group[3]['result']
        need(wire(parent['observer_off'][i])==wire(dict(ordinal=i,proof=H.require_off_pair(normal,off,bodies)))and
             wire(parent['counters'][i])==wire(dict(ordinal=i,rejection=H.counter_rejection(counter,normal,bodies),policy_disguised=True)),
             'Release parent OFF/counter receipts authenticated')


def prepare(rom,language,parent_report,parent_config,recipe_dir):
    config=read_parent_config(parent_config,rom,language);parent=H.H.H.N.read_report(parent_report)
    fixtures,execute_bodies,execute_proof=H.prepare(**config);check_parent(parent,language,fixtures,execute_bodies,execute_proof)
    model=P.G.S.SHARED.read_current(rom,language);out=[]
    with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        view=P.G.S.SHARED.gifts_audit.Arm9View(raw);bodies={a:view.read(a,n)for a,(n,d)in B.BODIES.items()}
        obj=recipe_dir/'fs-release-command.o';receipt=json.loads((recipe_dir/'manifesto.json').read_bytes());ref=receipt['reference']
        need(bodies[B.ENTRY]==P.G.piece(model['segments'],B.ENTRY,92)==L.object_text(obj,92,B.BODY_SHA),
             'Release physical/decoded/recovered ELF92 agreement')
        need(view.read(B.RETURN,4)==bytes.fromhex('080094e5'),'Release original ExecuteSync return-fetch LDR')
        for address,role in((B.DISABLE,'disable'),(B.RESTORE,'restore')):
            n,d=B.BODIES[address];need(bodies[address]==P.G.piece(model['segments'],address,n)==
                L.object_text(config['wait_recipe']/('fs-wait-'+role+'.o'),n,d),'Release independently retained qualified IRQ ELF/readback')
        need(receipt['schema']=='native-fs-release-recipe-v1'and receipt['builder_sha256']==sha(Path(L.C.__file__).read_bytes())and
             receipt['recipe_sha256']==sha((Path(__file__).parents[1]/'sorgenti/fs-release.S').read_bytes())and
             wire(receipt['source_recipe'])==wire(L.C.RECIPE)and receipt['objects']['command']['object_sha256']==sha(obj.read_bytes())and
             receipt['recipe_is_recovered']is True and receipt['original_compiler_reconstructed']is False and
             ref['pin']==L.C.D.C.PIN and ref['layout_passed']is True and ref['layout_assertions']==L.C.LAYOUT and len(ref['header_sha256'])==18 and
             ref['source_sha256']=='07333027376e89d3ecc243b0022d089f9c3153cfe4226ef433e086cbe9777e60'and
             ref['function_body_sha256']==dict(FSi_ReleaseCommand='9c23fd8514c97f05b746bf4c52b9258302f8ab15192c48c334dc69a78887373c')and
             receipt['list_inline_source']['sha256']=='b3abfe01ae14a8b64fd68372a4e0646f975373dd296626d4396ffc113c3a122c',
             'Release authenticated recipe/source/inline/header-layout receipt')
        for i,f in enumerate(fixtures):
            for value,index in((0,0),(1,2)):
                r=parent['cases'][i*8+index]['result'];service=r['services'][1];guard=bytes.fromhex(r['guard_before'])
                need(len(guard)==56 and r['guard_before']==r['guard_after']and service['entry'][1]==value,
                     'Release actual source-backed parent service result and preserved guard')
                item=dict(ordinal=len(out),plus=f['plus'],seed=f['seed'],translated_result=value,entry=service['entry'],
                    frame=(guard[-16:]+bytes.fromhex(service['frame_before'])).hex(),archive_before=service['archive_before'],
                    provenance=dict(entry='Actual isolated ExecuteSync→Release entry16 after modeled Translate result/error projection',
                        frame='Actual Release312 plus16 preserved preceding parent guard bytes',natural_capture=False,
                        archive='Actual isolated source fixture; not natural boot archive',parent_report_sha256=sha(parent_report.read_bytes())))
                B.initial_memory(item,bodies,0xA5,False);out.append(item)
        proof=dict(parent_report_sha256=sha(parent_report.read_bytes()),parent_config_sha256=sha(parent_config.read_bytes()),
            parent_positive_cells=4,parent_release_inputs=8,parent_semantic_replay_without_CPU=True,parent_proof=execute_proof,parent_input=model['record'],
            components=[dict(ram=hex(a),rom_offset=hex(view.offset(a,n)),bytes=n,sha256=d)for a,(n,d)in B.BODIES.items()],
            recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=receipt,
            frame=dict(SP=hex(B.SP),isolated_frame=328,native_additional_stack=16,future_parent_peak=648,old_parent_bound=608,parent_integration_qualified=False),
            model_scope=B.MODEL_SCOPE,completion_qualified=False)
    del model;gc.collect();return out,bodies,proof


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies)
    need(normal['observe']is True and off['observe']is False,'Release actual ON/OFF domains')
    a={k:v for k,v in normal.items()if k not in('observe','flow','stores','reads')};b={k:v for k,v in off.items()if k not in('observe','flow','stores','reads')}
    need(wire(a)==wire(b),'Release OFF exact registers/model records/whole RAM without projection')
    return dict(neutral=True,whole_ram_sha256=normal['whole_ram_sha256'],projection_bytes=0)


def counter_rejection(counter,normal,bodies):
    B.require_result(counter,bodies);B.require_result(normal,bodies)
    need(wire(normal['policy'])==wire(dict(wake_value=0,clobber=False,stale_error=False))and
         wire(counter['policy'])==wire(dict(wake_value=0,clobber=False,stale_error=True))and normal['observe']is counter['observe']is True and
         wire(normal['fill'])==wire(counter['fill'])==wire(0xA5)and
         all(wire(counter[k])==wire(normal[k])for k in('fixture','entry','returned','frame_after','archive_after','whole_ram_sha256','flow','reads','services')),
         'Release stale-input pair same authenticated ABI/policy/output except declared old-error projection')
    a,b=bytes.fromhex(normal['frame_before']),bytes.fromhex(counter['frame_before'])
    need([i for i,(x,y)in enumerate(zip(a,b))if x!=y]==[B.FILE-B.FRAME+20]and
         [i for i,(x,y)in enumerate(zip(normal['stores'],counter['stores']))if wire(x)!=wire(y)]==[8]and
         counter['stores'][8]['before']=='02000000'and counter['stores'][8]['value']==counter['fixture']['translated_result'],
         'Release stale error2 must be overwritten by actual native STR from R1-derived R4')
    disguised=copy.deepcopy(counter);disguised['policy']['stale_error']=False
    # Even forged initial-input metadata must not conceal the retained native store preimage.
    disguised['frame_before']=normal['frame_before'];disguised['before_whole_ram_sha256']=normal['before_whole_ram_sha256']
    try:B.require_result(disguised,bodies)
    except ValueError as error:return str(error)
    raise ValueError('Release stale input accepted after positive metadata disguise')


def analyze(rom,language,parent_report,parent_config,recipe_dir,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Release strict nonoptimized exclusive modes')
    H.H.H.R.W.require_host_budget();sources=source_identities();fixtures,bodies,proof=prepare(rom,language,parent_report,parent_config,recipe_dir)
    report=dict(schema='native-fs-release-isolated-v1',language=language,source_sha256=sources,proof=proof,fixtures=fixtures,
        cpu_executed=False,compiler_invoked=False,probe_only=probe,limits=['Native Release/IRQ only; empty Wakeup value-only model, not native thread/scheduler work',
            'Stale error2 is declared input projection, not naturally captured Translate state',
            'Release is void; residual R0=128 is not filesystem BOOL/success',
            'Frame328/future global648 exceeds608; no full caller/guard expansion/natural completion/ID delivery',
            'Unicorn2.1.4 CPU17 Cortex-A15 instruction semantics, not ARM946 silicon/timing/IRQ delivery'])
    if not prepare_only:
        need(raw_dir is not None and not raw_dir.exists()and not raw_dir.is_symlink()and P.SOURCE not in raw_dir.resolve().parents,'Release fresh private raw directory')
        raw_dir.mkdir(parents=True);cases=[];off=[];counters=[];serial=0
        for f in(fixtures[:1]if probe else fixtures):
            normal=None
            for label,options in(POLICIES[:1]if probe else POLICIES):
                serial+=1;row=B.run(f,bodies,**options);save(raw_dir/('%02d-%d-%s.json.gz'%(serial,f['ordinal'],label)),row)
                B.require_result(row,bodies);cases.append(dict(label=label,result=row))
                if label=='normal':normal=row
                elif label=='off':off.append(dict(ordinal=f['ordinal'],proof=require_off_pair(normal,row,bodies)))
                elif label=='stale_error2':counters.append(dict(ordinal=f['ordinal'],rejection=counter_rejection(row,normal,bodies),policy_disguised=True))
                elif label=='void_ones':need(row['returned']==normal['returned']and row['whole_ram_sha256']==normal['whole_ram_sha256'],'Release ignores void Wakeup R0')
                elif label=='clobber':need(row['whole_ram_sha256']==normal['whole_ram_sha256'],'Release volatile clobber changes no RAM')
                print(language,f['ordinal'],label,'raw saved and source verified',flush=True)
        report.update(cpu_executed=True,cases=cases,observer_off=off,counters=counters)
    need(source_identities()==sources,'Release sources changed during analysis');H.H.H.R.W.require_host_budget();return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('rom','parent-report','parent-config','recipe-dir','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--raw-dir',type=Path)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and P.SOURCE not in a.json.resolve().parents,'Release fresh private report outside source')
        report=analyze(a.rom,a.language,a.parent_report,a.parent_config,a.recipe_dir,a.raw_dir,a.prepare_only,a.probe);save(a.json,report)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print(a.language,'Release prepared without CPU'if a.prepare_only else'Release isolated void wrapper verified; thread completion excluded')


if __name__=='__main__':main()
