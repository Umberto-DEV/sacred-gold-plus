#!/usr/bin/env python3
"""Attribute native ExecuteSync68 with explicit Translate/Release/Next projections.

Isolated instruction semantics only; no native completion, ID delivery or full caller.
Requires exact authenticated Send and Find caller reports with their local inputs.
"""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,sys


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('exec_sync_qualified_send',Path(__file__).with_name('attribuisci_fs_send.py'))
B=load('exec_sync_source_bench',Path(__file__).parents[1]/'test/fs_exec_sync_bench.py')
L=load('exec_sync_independent_reader',Path(__file__).with_name('rileggi_fs_exec_sync.py'))
P,need,sha,wire,save=H.P,H.need,H.sha,B.wire,H.save
need(sha(Path(H.__file__).read_bytes())=='49c8ee1f7eb38b1d2e879e040fae7789868cbaa13817fa25e659c61f5ecc4f6f','ExecuteSync qualified Send verifier drift')
POLICIES=[('normal',{}),('off',dict(observe=False)),('translate_failure',dict(result=1)),
    ('release_error_fault',dict(release_error=1)),('void_ones',dict(void_value=0xFFFFFFFF)),
    ('void_file',dict(void_value=B.FILE)),('clobber',dict(clobber=True)),('fill39',dict(fill=0x39))]
SEND_POLICIES=[('normal',1,False,True,0xA5),('off',1,False,False,0xA5),('false',0,False,True,0xA5),
    ('truthy2',2,False,True,0xA5),('clobber',1,True,True,0xA5),('fill39',1,False,True,0x39)]


def source_identities():
    ids=H.source_identities()
    for path in(__file__,B.__file__,L.__file__,L.C.__file__,Path(__file__).parents[1]/'sorgenti/fs-exec-sync.S'):
        p=Path(path);ids[str(p.resolve().relative_to(P.SOURCE))]=sha(p.read_bytes())
    return ids


def check_parent(parent,language,fixtures,bodies,proof):
    need(parent['schema']=='native-fs-send-isolated-v1'and parent['language']==language and parent['cpu_executed']is True and
         parent['probe_only']is False and wire(parent['source_sha256'])==wire(H.source_identities())and
         wire(parent['proof'])==wire(proof)and wire(parent['fixtures'])==wire(fixtures),'ExecuteSync exact authenticated Send report/source/proof')
    need(len(parent['cases'])==24 and len(parent['observer_off'])==len(parent['counters'])==4,'ExecuteSync complete parent matrix')
    for i,f in enumerate(fixtures):
        group=parent['cases'][i*6:(i+1)*6]
        for cell,(label,value,clobber,observe,fill)in zip(group,SEND_POLICIES):
            r=cell['result'];need(cell['label']==label and wire(r['fixture'])==wire(f)and
                wire((r['policy'],r['observe'],r['fill']))==wire((dict(execute=value,clobber=clobber),observe,fill)),
                'ExecuteSync exact parent policy/cell grid')
            H.B.require_result(r,bodies)
        normal,off,counter=[x['result']for x in group[:3]]
        need(wire(parent['observer_off'][i])==wire(dict(ordinal=i,proof=H.require_off_pair(normal,off,bodies)))and
             wire(parent['counters'][i])==wire(dict(ordinal=i,rejection=H.counter_rejection(counter,normal,bodies),policy_disguised=True)),
             'ExecuteSync authenticated parent OFF and counter receipts')


def prepare(rom,language,parent_report,find_parent_report,capture_source,objects,strategy_object,read_recipe,wait_recipe,find_recipe,send_recipe,recipe_dir):
    parent=H.H.N.read_report(parent_report)
    fixtures,send_bodies,send_proof=H.prepare(rom,language,find_parent_report,capture_source,objects,strategy_object,read_recipe,wait_recipe,find_recipe,send_recipe)
    check_parent(parent,language,fixtures,send_bodies,send_proof)
    model=P.G.S.SHARED.read_current(rom,language);out=[]
    with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        view=P.G.S.SHARED.gifts_audit.Arm9View(raw);body=view.read(B.ENTRY,68);bodies={B.ENTRY:body}
        obj=recipe_dir/'fs-exec-sync-command.o';receipt=json.loads((recipe_dir/'manifesto.json').read_bytes());ref=receipt['reference']
        need(body==P.G.piece(model['segments'],B.ENTRY,68)==L.object_text(obj,68,B.BODY_SHA),
             'ExecuteSync physical/decoded/recovered ELF68 agreement')
        need(view.read(B.RETURN,4)==bytes.fromhex('f880bde8'),'ExecuteSync original Send return-fetch instruction')
        need(receipt['schema']=='native-fs-exec-sync-recipe-v1'and receipt['builder_sha256']==sha(Path(L.C.__file__).read_bytes())and
             receipt['recipe_sha256']==sha((Path(__file__).parents[1]/'sorgenti/fs-exec-sync.S').read_bytes())and
             wire(receipt['source_recipe'])==wire(L.C.RECIPE)and receipt['objects']['command']['object_sha256']==sha(obj.read_bytes())and
             receipt['recipe_is_recovered']is True and receipt['original_compiler_reconstructed']is False and
             ref['pin']==L.C.D.C.PIN and ref['layout_passed']is True and ref['layout_assertions']==L.C.LAYOUT and len(ref['header_sha256'])==18 and
             ref['source_sha256']=='d359268374ed97b359e4344a820c892382fd23f8923d2895a828175662ae3f2d'and
             ref['function_body_sha256']==dict(FSi_ExecuteSyncCommand='9edfebc8b0b6fdb346ed1d348c6db3eb6d0484332f4ea2c885d59f5817766799')and
             receipt['success_inline_source']['definition_sha256']=='d0750073e8e967e089376bacd26c528ffaa514f208d1f7bc81a9e888719b1003',
             'ExecuteSync authenticated recovered recipe/source/header-layout receipt')
        for i in range(4):
            r=parent['cases'][i*6]['result'];service=r['services'][0];guard=bytes.fromhex(r['guard_before'])
            need(len(guard)==56 and r['guard_before']==r['guard_after']and service['frame_before']==service['frame_after']and
                 service['archive_before']==service['archive_after'],'ExecuteSync exact parent value-only service preimage')
            f=dict(ordinal=i,plus=fixtures[i]['plus'],seed=fixtures[i]['seed'],entry=service['entry'],
                frame=(guard[-8:]+bytes.fromhex(service['frame_before'])).hex(),archive_before=service['archive_before'],
                provenance=dict(entry='Actual isolated native Send→ExecuteSync entry16',frame='Actual ExecuteSync304 plus8 preceding preserved parent guard bytes',
                    archive='Actual isolated Send source fixture after native queue preparation; not natural boot archive',
                    natural_capture=False,parent_report_sha256=sha(parent_report.read_bytes())))
            B.initial_memory(f,bodies,0xA5);out.append(f)
        proof=dict(parent_report_sha256=sha(parent_report.read_bytes()),parent_positive_cells=4,parent_semantic_replay_without_CPU=True,
            parent_proof=send_proof,parent_input=model['record'],components=[dict(ram=hex(B.ENTRY),rom_offset=hex(view.offset(B.ENTRY,68)),bytes=68,sha256=B.BODY_SHA)],
            recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=receipt,
            frame=dict(SP=hex(B.SP),isolated_frame=312,native_additional_stack=8,future_parent_peak=632,old_parent_bound=608,parent_integration_qualified=False),
            model_scope=B.SCOPES,completion_qualified=False)
    del model;gc.collect();return out,bodies,proof


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies)
    need(normal['observe']is True and off['observe']is False,'ExecuteSync actual ON/OFF observer domains')
    a={k:v for k,v in normal.items()if k not in('observe','flow','stores','reads')}
    b={k:v for k,v in off.items()if k not in('observe','flow','stores','reads')}
    need(wire(a)==wire(b),'ExecuteSync OFF exact registers/wholeRAM no projection')
    return dict(neutral=True,whole_ram_sha256=normal['whole_ram_sha256'],projection_bytes=0)


def counter_rejection(counter,normal,bodies):
    B.require_result(counter,bodies);B.require_result(normal,bodies)
    baseline=dict(result=0,void_value=0,clobber=False,release_error=None)
    fault={**baseline,'release_error':1}
    need(wire(normal['policy'])==wire(baseline)and wire(counter['policy'])==wire(fault)and
         normal['observe']is counter['observe']is True and
         wire(normal['fill'])==wire(counter['fill'])==wire(0xA5)and
         all(wire(counter[k])==wire(normal[k])for k in('fixture','entry','before_whole_ram_sha256')),
         'ExecuteSync counter requires same prestate and baseline policy except Release error fault')
    a,b=bytes.fromhex(normal['frame_after']),bytes.fromhex(counter['frame_after'])
    need([i for i,(x,y)in enumerate(zip(a,b))if x!=y]==[B.FILE-B.FRAME+20]and
         counter['archive_after']==normal['archive_after'],
         'ExecuteSync counter final RAM delta only stored error byte')
    need(counter['policy']['release_error']==1 and counter['policy']['result']==0 and counter['returned'][0]==0 and normal['returned'][0]==1 and
         counter['services'][0]==normal['services'][0]and counter['services'][1]['entry']==normal['services'][1]['entry'],
         'ExecuteSync Release fault: unchanged Translate success and Release argument, actual stored-error BOOL0')
    disguised=copy.deepcopy(counter);disguised['policy']['release_error']=None
    # Match declared model metadata to the ordinary case; retain actual native result/reads.
    disguised['services']=copy.deepcopy(normal['services'])
    try:B.require_result(disguised,bodies)
    except ValueError as error:return str(error)
    raise ValueError('ExecuteSync stored-error failure accepted after positive metadata disguise')


def analyze(rom,language,parent_report,find_parent_report,capture_source,objects,strategy_object,read_recipe,wait_recipe,find_recipe,send_recipe,recipe_dir,
            raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'ExecuteSync strict nonoptimized exclusive modes')
    H.H.R.W.require_host_budget();sources=source_identities()
    fixtures,bodies,proof=prepare(rom,language,parent_report,find_parent_report,capture_source,objects,strategy_object,read_recipe,wait_recipe,find_recipe,send_recipe,recipe_dir)
    report=dict(schema='native-fs-exec-sync-isolated-v1',language=language,source_sha256=sources,proof=proof,fixtures=fixtures,
        cpu_executed=False,compiler_invoked=False,probe_only=probe,limits=['Native68 wrapper only; Translate/Release/Next are incomplete explicit field models',
            'Release-error counter is declared model fault, not natural SDK error',
            'Actual isolated Send entry/frame/archive; not boot state, full caller or filesystem completion/ID delivery',
            'Frame312/future global632 exceeds608; no expanded caller ownership mask',
            'Unicorn2.1.4 CPU17 Cortex-A15 instruction semantics, not ARM946 silicon/timing/IRQ delivery'])
    if not prepare_only:
        need(raw_dir is not None and not raw_dir.exists()and not raw_dir.is_symlink()and P.SOURCE not in raw_dir.resolve().parents,'ExecuteSync fresh private raw directory')
        raw_dir.mkdir(parents=True);cases=[];off=[];counters=[];serial=0
        for f in(fixtures[:1]if probe else fixtures):
            normal=None
            for label,options in(POLICIES[:1]if probe else POLICIES):
                serial+=1;row=B.run(f,bodies,**options);save(raw_dir/('%02d-%d-%s.json.gz'%(serial,f['ordinal'],label)),row)
                B.require_result(row,bodies);cases.append(dict(label=label,result=row))
                if label=='normal':normal=row
                elif label=='off':off.append(dict(ordinal=f['ordinal'],proof=require_off_pair(normal,row,bodies)))
                elif label=='release_error_fault':counters.append(dict(ordinal=f['ordinal'],rejection=counter_rejection(row,normal,bodies),policy_disguised=True))
                elif label in('void_ones','void_file','clobber'):
                    need(row['frame_after']==normal['frame_after']and row['archive_after']==normal['archive_after']and row['whole_ram_sha256']==normal['whole_ram_sha256'],
                         'ExecuteSync void/clobber controls preserve whole RAM')
                print(language,f['ordinal'],label,'raw saved and source verified',flush=True)
        report.update(cpu_executed=True,cases=cases,observer_off=off,counters=counters)
    need(source_identities()==sources,'ExecuteSync sources changed during analysis');H.H.R.W.require_host_budget();return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('rom','parent-report','find-parent-report','objects','strategy-object','read-recipe','wait-recipe','find-recipe','send-recipe','recipe-dir','json'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--parent-source',type=Path);p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--raw-dir',type=Path)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and P.SOURCE not in a.json.resolve().parents,'ExecuteSync fresh private report outside source')
        report=analyze(a.rom,a.language,a.parent_report,a.find_parent_report,a.parent_source,a.objects,a.strategy_object,a.read_recipe,a.wait_recipe,
            a.find_recipe,a.send_recipe,a.recipe_dir,a.raw_dir,a.prepare_only,a.probe);save(a.json,report)
    except ValueError as error:p.exit(2,str(error)+'\n')
    print(a.language,'ExecuteSync prepared without CPU'if a.prepare_only else'ExecuteSync isolated wrapper verified; native completion excluded')


if __name__=='__main__':main()
