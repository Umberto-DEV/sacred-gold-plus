#!/usr/bin/env python3
"""Attribute empty-archive Next from native checkpoints through its original bridge."""
from pathlib import Path
import copy,gc,importlib.util,json,mmap,sys,types


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('next_qualified_composition_cli',Path(__file__).with_name('attribuisci_release_wakeup.py'))
B=load('next_empty_archive_bench',Path(__file__).parents[1]/'test/fs_next_bench.py')
L=load('next_independent_reader',Path(__file__).with_name('rileggi_fs_next.py'))
P,need,sha,wire,save,read_report=H.P,H.need,H.sha,B.wire,H.save,H.read_report
need(sha(Path(H.__file__).read_bytes())=='6117bbfbb51e905931dff9f641b582c567a94355adad00e9a88f5c614008fe6a','Next qualified parent CLI drift')
share_groups=types.FunctionType(H.share_groups.__code__,{**H.share_groups.__globals__,'B':B})
CONFIG_KEYS={'parent_config','field_contract','report','raw_dir'}
POLICIES=[('normal',{}),('off',dict(observe=False)),('fill39',dict(fill=0x39)),('not_running',dict(not_running=True))]


def source_identities():
    ids=H.source_identities()
    for path in(__file__,B.__file__,L.__file__,L.C.__file__,Path(__file__).parents[1]/'sorgenti/fs-next.S'):
        p=Path(path);ids[str(p.resolve().relative_to(P.SOURCE))]=sha(p.read_bytes())
    return ids


def read_config(path):
    need(path.stat().st_size<=512*1024,'Next bounded composition replay config512KiB')
    c=json.loads(path.read_bytes());need(type(c)is dict and set(c)==CONFIG_KEYS and all(type(v)is str for v in c.values()),'Next exact composition replay string keys')
    return {k:Path(v)for k,v in c.items()}


def require_complete_parent(r):
    need(r['schema']=='native-release-wakeup-composed-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        r['probe_only']is False,'Next requires complete native composition, not a probe')
    n=len(r['groups']);need(n>0 and len(r['fixtures'])==16 and len(r['cases'])==n*len(H.POLICIES)and
        len(r['field_holdout'])==16*len(H.POLICIES)and len(r['observer_off'])==len(r['counters'])==n,'Next complete parent raw/OFF/counter/field grid')


def check_recipe(receipt,parent_receipt,obj):
    ref=receipt['reference']
    need(receipt['schema']=='native-fs-next-recipe-v1'and receipt['builder_sha256']==sha(Path(L.C.__file__).read_bytes())and
        receipt['recipe_sha256']==sha((Path(__file__).parents[1]/'sorgenti/fs-next.S').read_bytes())and wire(receipt['source_recipe'])==wire(L.C.RECIPE)and
        receipt['objects']['command']['object_sha256']==sha(obj.read_bytes())and receipt['recipe_is_recovered']is True and
        receipt['original_compiler_reconstructed']is False and ref['pin']==L.C.D.C.PIN and ref['layout_passed']is True and
        ref['layout_assertions']==L.C.LAYOUT and len(ref['header_sha256'])==18 and ref['header_sha256']==parent_receipt['reference']['header_sha256']and
        receipt['compiler_sha256']==parent_receipt['compiler_sha256']=='fc5e3cbba6ad54059295cad716aacb05ace8235f5f7a6031f1d8c15d24bd6d66'and
        receipt['compiler_version']==parent_receipt['compiler_version'],'Next source/rewrite/ELF/header/compiler/layout recipe identity')
    need(ref['source_sha256']=='d359268374ed97b359e4344a820c892382fd23f8923d2895a828175662ae3f2d'and
        ref['function_body_sha256']==dict(FSi_NextCommand='3a6aa7886dc38416168646a09ce716fc12e68ef77737186854a71dedbd335b39'),
        'Next original source function identity')
    need(wire(receipt['archive_inline_source'])==wire(dict(path='lib/include/nitro/fs/archive.h',
        sha256='0c7fa797839d7112af12c5a467c6fda878621b4bb5ce8b273c9df4ebadfdbe9e',definition_sha256={
            'FSi_IsArchiveCanceling':'42cae786fb2f8b206f3b57cac30d46b28b232ca01e208c9736c56f280f1357ad',
            'FSi_IsArchiveSuspending':'6587c3c7c50a77e30e6aa9649aceeff7dccb4a1790e79261c7db1af96e0b54a0',
            'FS_IsArchiveSuspended':'7e5d8e67dbd9f9b6a3287987414b93c983306b92319c8b6d69e6104f600a2f7b',
            'FSi_IsArchiveRunning':'06336d881b7b67e4dc3200a222a4775dae469fec10d0ec4253c591ad6933dfa9'}))and
        wire(receipt['sync_inline_source'])==wire(dict(path='lib/include/nitro/fs/file.h',
            sha256='4e874cfbaa77f546b6f69473ef8bd24afdaab082c5a99f0bb16c37d41f24598f',
            definition_sha256='2a8c863ae0b4cfdbc2aa8bf1fc4edb628ef1341a76baf226eb3015e1e7a13fd5')),'Next pinned archive/file inline identities')


def prepare(parent_config,recipe_dir):
    c=read_config(parent_config);r=read_report(c['report']);require_complete_parent(r)
    pf,pb,pp,pg,baselines=H.prepare(c['parent_config']);H.check_contract(c['field_contract'],pf,baselines)
    H.require_report(r,pf,pb,pp,pg,c['field_contract'],c['raw_dir'])
    wake_config=H.read_config(c['parent_config']);release_config=H.J.read_config(wake_config['parent_config'])
    fixtures=[];bodies=None;components={};obj=recipe_dir/'fs-next-command.o';receipt=json.loads((recipe_dir/'manifesto.json').read_bytes())
    for language in('EN','IT'):
        release=release_config[language]['prepare'];rom=Path(release['rom']);model=P.G.S.SHARED.read_current(rom,language)
        check_recipe(receipt,pp['languages'][language]['qualified_wakeup_proof']['recipe_receipt'],obj)
        ancestor=H.J.H.read_parent_config(Path(release['parent_config']),rom,language)
        old_elf=L.object_text(ancestor['recipe_dir']/'fs-exec-sync-command.o',68,'44b2f23b47f01552bd478420b9a14ae0fc2ed6013e7d551d5112075264a43d55')
        with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
            view=P.G.S.SHARED.gifts_audit.Arm9View(raw);code={a:view.read(a,n)for a,(n,d)in B.BODIES.items()}
            for a,(n,d)in B.BODIES.items():
                need(code[a]==P.G.piece(model['segments'],a,n)and sha(code[a])==d,'Next physical/decoded component identity')
                if a in pb:need(code[a]==pb[a],'Next exact retained parent component')
            need(code[B.NEXT]==L.object_text(obj,532,B.BODY_SHA)and code[B.ENTRY]==old_elf[28:36]and
                view.read(B.RETURN,4)==P.G.piece(model['segments'],B.RETURN,4)==old_elf[36:40]==bytes.fromhex('000050e3'),
                'Next independent ELF532/original bridge8/CMP return gate')
            need(bodies is None or bodies==code,'Next dual-ROM component equality before sharing CPU images');bodies=code
            for f in(f for f in pf if f['language']==language):
                member=dict(language=language,ordinal=f['ordinal']);g=next(g for g in pg if member in g['members']);row=r['cases'][g['ordinal']*4]['result']
                need(row['fill']==0xA5 and row['halt_pc']==hex(B.ENTRY)and row['guard_before']==row['guard_after'],'Next actual parent normal checkpoint and unchanged captured guard')
                item=dict(language=language,ordinal=f['ordinal'],plus=f['plus'],seed=f['seed'],translated_result=f['translated_result'],entry=row['returned'],
                    captured408=row['guard_after']+row['frame_after'],archive_before=row['archive_after'],parent_whole_ram_sha256=row['whole_ram_sha256'],
                    provenance=dict(parent_report_sha256=sha(c['report'].read_bytes()),parent_group=g['ordinal'],natural_capture=False,
                        observed='Actual parent return checkpoint7760, frame352 and guard56',
                        additional64='Source-reconstructed/wholeSHA-verified parent bytes, not a separately captured raw span'))
                B.parent_memory(item,code);fixtures.append(item)
            components[language]=dict(parent_input=model['record'],components=[dict(ram=hex(a),rom_offset=hex(view.offset(a,n)),bytes=n,sha256=d)for a,(n,d)in B.BODIES.items()])
        del model;gc.collect()
    proof=dict(parent_report_sha256=sha(c['report'].read_bytes()),parent_config_sha256=sha(parent_config.read_bytes()),parent_proof=pp,
        parent_complete_raw_semantically_replayed_without_CPU=True,components=components,recipe_receipt_sha256=sha((recipe_dir/'manifesto.json').read_bytes()),recipe_receipt=receipt,
        frame=dict(captured_parent=408,isolated=416,native_peak=104,new_local_prefix=8,new_guard=56,additional64_provenance='Reconstructed parent image matches actual whole-RAM hash',
            fill39_projection_bytes=64,future_parent_peak=736,old_parent_bound=608,parent_integration_qualified=False))
    return fixtures,bodies,proof,share_groups(fixtures,bodies)


def field_contract(cell,f,row):
    need(cell['language']==f['language']and type(cell['ordinal'])is int and cell['ordinal']==f['ordinal']and
        all(type(cell[k])is int and cell[k]==f[k]for k in('plus','seed','translated_result'))and
        cell['parent_report_sha256']==f['provenance']['parent_report_sha256']and type(cell['parent_group'])is int and cell['parent_group']==f['provenance']['parent_group']and
        wire(cell['checkpoint_regs'])==wire(f['entry'])and cell['checkpoint_pc']==hex(B.ENTRY),'Next frozen parent identity/entry binding')
    captured=bytes.fromhex(f['captured408']);after=bytes.fromhex(row['frame_after'])
    need(sha(captured[56:])==cell['parent_frame352_sha256']and sha(captured[:56])==cell['parent_guard56_sha256']and
        sha(bytes.fromhex(f['archive_before']))==cell['parent_archive92_sha256']and f['parent_whole_ram_sha256']==cell['parent_whole_ram_sha256'],
        'Next frozen parent byte/hash binding')
    need(len(after)==416 and sha(after[104:])==cell['expected_live_caller312_sha256']==sha(captured[96:]),'Next frozen live caller312 invariant')
    need(len(bytes.fromhex(row['archive_after']))==92 and sha(bytes.fromhex(row['archive_after']))==cell['expected_archive92_after_sha256'],
        'Next frozen archive92 state, not NULL alone')
    need(B.B.u32s(row['incoming_next'])and wire(row['incoming_next'])==wire(cell['expected_next_entry'])and B.B.u32s(row['returned'])and
        type(cell['expected_R0'])is int and row['returned'][0]==cell['expected_R0']==0 and
        wire(cell['callee_saved_indices'])==wire([*range(4,12),13])and all(row['returned'][i]==f['entry'][i]for i in cell['callee_saved_indices'])and
        row['returned'][15]&0xFF==0x1F and type(cell['expected_I_bit'])is int and cell['expected_I_bit']==0 and
        row['halt_pc']==cell['expected_return_pc']==hex(B.RETURN),'Next frozen actual bridge/NULL/IRQ/callee-saved/original return')
    return dict(passed=True,live_caller312_sha256=sha(after[104:]),archive92_sha256=sha(bytes.fromhex(row['archive_after'])),native_running_store_proved_by_this_comparator=False)


def check_contract(path,fixtures):
    need(path.stat().st_size<=128*1024,'Next bounded earlier contract128KiB');c=json.loads(path.read_bytes());cells=c['cells']
    need(c['schema']=='native-fs-next-empty-prospective-fields-v1'and len(cells)==16 and
        {(x['language'],x['ordinal'])for x in cells}=={(f['language'],f['ordinal'])for f in fixtures},'Next complete frozen cell set')
    for f in fixtures:
        cell=next(x for x in cells if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
        incoming=list(f['entry']);incoming[0]=B.ARC;incoming[14]=B.RETURN
        arc=bytearray.fromhex(f['archive_before']);arc[28:32]=(3).to_bytes(4,'little');returned=list(f['entry']);returned[0]=0
        synthetic=dict(frame_after=(bytes([0xA5])*8+bytes.fromhex(f['captured408'])).hex(),archive_after=arc.hex(),incoming_next=incoming,returned=returned,halt_pc=hex(B.RETURN))
        field_contract(cell,f,synthetic)
    return cells


def require_off_pair(normal,off,bodies):
    B.require_result(normal,bodies);B.require_result(off,bodies)
    need(normal['observe']is True and off['observe']is False,'Next actual ON/OFF domains')
    need(wire({k:v for k,v in normal.items()if k not in('observe','flow','stores','reads')})==
        wire({k:v for k,v in off.items()if k not in('observe','flow','stores','reads')}),'Next OFF identical whole RAM/CPU without projection')
    return dict(neutral=True,projection_bytes=0,whole_ram_sha256=normal['whole_ram_sha256'])


def counter_rejection(counter,normal,bodies):
    B.require_result(counter,bodies);B.require_result(normal,bodies)
    need(wire(counter['policy'])==wire(dict(not_running=True))and wire(normal['policy'])==wire(dict(not_running=False))and
        counter['observe']is normal['observe']is True and counter['fill']==normal['fill']==0xA5,'Next actual finite native not-running input pair')
    difference={'policy','steps','flow','stores','reads','observed_pcs','archive_before','before_whole_ram_sha256'}
    need(wire({k:v for k,v in counter.items()if k not in difference})==wire({k:v for k,v in normal.items()if k not in difference}),
        'Next not-running pair converges every caller output, frame and absolute whole-RAM hash')
    a,b=bytes.fromhex(normal['archive_before']),bytes.fromhex(counter['archive_before'])
    need([i for i,(x,y)in enumerate(zip(a,b))if x!=y]==[28]and(a[28],b[28])==(0x13,3)and
        counter['stores']==normal['stores'][:8]and normal['stores'][-1]['pc']=='0x20d7640'and
        normal['stores'][-1]['address']==B.ARC+28 and normal['stores'][-1]['before']=='13000000'and normal['stores'][-1]['value']==3,
        'Next declared one-byte initial projection and actual conditional RUNNING-clear store')
    disguised=copy.deepcopy(counter);disguised['policy']['not_running']=False
    disguised['archive_before']=normal['archive_before'];disguised['before_whole_ram_sha256']=normal['before_whole_ram_sha256']
    try:B.require_result(disguised,bodies)
    except ValueError as error:
        need(str(error)=='Next source-derived steps','Next negative fails the actual native path, not just input metadata')
        return dict(rejection=str(error),policy_and_initial_metadata_disguised=True,whole_ram_and_full16_equal=True,
            initial_archive_changed_offsets=[28],normal_running_store_observed=True,counter_running_store_observed=False)
    raise ValueError('Next inactive RUNNING branch accepted as the positive original input')


def require_report(r,fixtures,bodies,proof,groups,contract_path,raw_dir):
    need(r['schema']=='native-fs-next-isolated-v1'and r['cpu_executed']is True and r['compiler_invoked']is False and
        type(r['probe_only'])is bool and r['source_sha256']==source_identities()and wire(r['fixtures'])==wire(fixtures)and
        wire(r['proof'])==wire(proof)and wire(r['groups'])==wire(groups)and r['field_contract_sha256']==sha(contract_path.read_bytes()),
        'Next replay metadata/source/fixtures/proof/groups/contract binding')
    cells=json.loads(contract_path.read_bytes())['cells'];cases=[];off=[];counters=[];held=[];paths=[];serial=0
    for g in(groups[:1]if r['probe_only']else groups):
        normal=None
        for label,options in(POLICIES[:1]if r['probe_only']else POLICIES):
            serial+=1;path=raw_dir/('%02d-%d-%s.json.gz'%(serial,g['ordinal'],label));paths.append(path.name);row=read_report(path)
            B.require_result(row,bodies)
            need(wire(row['fixture'])==wire(g['representative'])and
                wire((row['policy'],row['observe'],row['fill']))==wire((dict(not_running=options.get('not_running',False)),
                    options.get('observe',True),options.get('fill',0xA5))),'Next replay actual representative/policy grid')
            cases.append(dict(group=g['ordinal'],label=label,result=row))
            if label=='normal':normal=row
            if label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
            if label=='not_running':counters.append(dict(group=g['ordinal'],proof=counter_rejection(row,normal,bodies)))
            for member in g['members']:
                f=next(x for x in fixtures if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
    need(sorted(p.name for p in raw_dir.iterdir())==sorted(paths),'Next exact raw set')
    for key,value in(('cases',cases),('observer_off',off),('counters',counters),('field_holdout',held)):
        need(wire(r[key])==wire(value),'Next replay authenticated '+key)
    return True


def analyze(parent_config,recipe_dir,contract_path,raw_dir=None,prepare_only=False,probe=False):
    need(sys.flags.optimize==0 and type(prepare_only)is type(probe)is bool and not(prepare_only and probe),'Next strict exclusive modes')
    need(prepare_only or raw_dir is not None,'Next execution requires a fresh private raw directory')
    H.J.H.H.H.H.R.W.require_host_budget();sources=source_identities();fixtures,bodies,proof,groups=prepare(parent_config,recipe_dir)
    cells=check_contract(contract_path,fixtures)
    report=dict(schema='native-fs-next-isolated-v1',source_sha256=sources,fixtures=fixtures,proof=proof,groups=groups,
        field_contract_sha256=sha(contract_path.read_bytes()),cpu_executed=False,compiler_invoked=False,probe_only=probe,
        limits=['Actual native parent return checkpoint plus original two-instruction bridge; not complete upstream ExecuteSync or constructor/caller',
            'Empty list and no cancel/suspend/IDLE callback only; proc_flag88 is distinct from proc84 and archive flag28',
            'Extra64 bytes are reconstructed/wholeSHA-verified parent memory, not separately captured raw span; fill39 changes only64',
            'not_running is a declared initial archive-word projection; no host state writes during guest; not a natural SDK error',
            'Frame416/global736 exceeds old608 caller ownership bound; no old mask expansion/natural boot/card/save/hardware claim',
            'Recovered assembly/pinned counterpart, not original MW C build; CPU17 instruction semantics, not ARM946 timing/IRQ delivery'])
    if not prepare_only:
        need(raw_dir is not None and not raw_dir.exists()and not raw_dir.is_symlink()and P.SOURCE not in raw_dir.resolve().parents,'Next fresh private raw output')
        raw_dir.mkdir(parents=True);cases=[];off=[];counters=[];held=[];serial=0
        for g in(groups[:1]if probe else groups):
            normal=None
            for label,options in(POLICIES[:1]if probe else POLICIES):
                gc.collect();serial+=1;row=B.run(g['representative'],bodies,**options)
                save(raw_dir/('%02d-%d-%s.json.gz'%(serial,g['ordinal'],label)),row);B.require_result(row,bodies)
                cases.append(dict(group=g['ordinal'],label=label,result=row))
                if label=='normal':normal=row
                if label=='off':off.append(dict(group=g['ordinal'],proof=require_off_pair(normal,row,bodies)))
                if label=='not_running':counters.append(dict(group=g['ordinal'],proof=counter_rejection(row,normal,bodies)))
                for member in g['members']:
                    f=next(x for x in fixtures if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                    held.append(dict(group=g['ordinal'],label=label,member=member,proof=field_contract(cell,f,row)))
                print(g['ordinal'],label,'raw saved; native Next and earlier field invariants checked',flush=True)
        report.update(cpu_executed=True,cases=cases,observer_off=off,counters=counters,field_holdout=held)
        require_report(report,fixtures,bodies,proof,groups,contract_path,raw_dir)
    need(source_identities()==sources,'Next runtime source changed');H.J.H.H.H.H.R.W.require_host_budget();return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in('parent-config','recipe-dir','field-contract','json'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--raw-dir',type=Path);mode=p.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only',action='store_true');mode.add_argument('--probe',action='store_true');a=p.parse_args()
    try:
        need(not a.json.exists()and not a.json.is_symlink()and P.SOURCE not in a.json.resolve().parents,'Next fresh private prepared output')
        r=analyze(a.parent_config,a.recipe_dir,a.field_contract,a.raw_dir,a.prepare_only,a.probe);save(a.json,r)
    except(ValueError,KeyError,TypeError)as error:p.exit(2,str(error)+'\n')
    print('Next prepared without CPU'if a.prepare_only else'Next empty-archive native path verified; callbacks and full caller excluded')


if __name__=='__main__':main()
