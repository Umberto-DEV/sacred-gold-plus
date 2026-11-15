#!/usr/bin/env python3
"""Isolated native Read/Wait/IRQ execution after a declared completion projection.

The full parent receipts and source-derived seven input templates are replayed
without parent CPU execution. No native Send/queue/archive completion is claimed.
"""
from pathlib import Path
import argparse,copy,gc,gzip,importlib.util,json,mmap


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


R=load('wait_read_parent',Path(__file__).with_name('attribuisci_fs_read.py'))
B=load('wait_composed_bench',Path(__file__).parents[1]/'test/fs_wait_bench.py')
L=load('wait_independent_lineage',Path(__file__).with_name('rileggi_fs_wait.py'))
C=L.C
need,sha,save=R.need,R.sha,R.save


def source_identities():
    result=R.source_identities()
    for p in (__file__,B.__file__,C.__file__,L.__file__,L.L.__file__):
        result[str(Path(p).resolve().relative_to(R.H.P.SOURCE))]=sha(Path(p).read_bytes())
    return result


def prepare(rom,language,parent_report,seek_report,objects,strategy_object,recipe_dir):
    result,bodies=R.prepare(rom,language,seek_report,objects,strategy_object)
    parent=json.loads(gzip.decompress(parent_report.read_bytes()))
    need(parent['schema']=='native-fs-read-isolated-v1'and parent['language']==language and
         parent['source_sha256']==R.source_identities(),'Wait parent Read schema/source identities')
    for key,value in result.items():need(parent[key]==json.loads(json.dumps(value)),'Wait parent Read '+key)
    R.require_matrix(parent,bodies)
    need(len(parent['runs'])==49,'Wait requires qualified49 parent runs')
    with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        view=R.H.P.G.S.SHARED.gifts_audit.Arm9View(raw)
        extra={}
        for name,(address,n,digest)in C.BODIES.items():
            blob=view.read(address,n);recovered=L.object_text(recipe_dir/('fs-wait-'+name+'.o'),n,digest)
            need(sha(blob)==digest and recovered==blob,'Wait/IRQ independent ELF and current raw bytes')
            bodies[address]=blob;extra[name]=dict(ram=hex(address),rom_offset=hex(view.offset(address,n)),bytes=n,sha256=digest,
                object_sha256=sha((recipe_dir/('fs-wait-'+name+'.o')).read_bytes()))
    result.update(read_parent_report_sha256=sha(parent_report.read_bytes()),wait_code=extra,
        completion_scope='Source field12 projection stat&~4F/command0/error0; list/queue/archive/thread side effects excluded')
    del parent;gc.collect();return result,bodies


def fixture_for(base,irq):
    need(type(irq)is int and irq in(0,128),'Wait finite initial IRQ bit')
    f=copy.deepcopy(base);f['entry'][15]=(f['entry'][15]&~0x80)|irq
    if irq:f['provenance']['IRQ']='synthetic initial I1 metamorphic input; other parent-derived fields unchanged'
    return f


POLICIES={
    'normal':dict(error_value=0,send_value=1,clobber=False,observe=True,fill=0xA5,irq=0),
    'off':dict(error_value=0,send_value=1,clobber=False,observe=False,fill=0xA5,irq=0),
    'error1':dict(error_value=1,send_value=1,clobber=False,observe=True,fill=0xA5,irq=0),
    'send_false':dict(error_value=0,send_value=0,clobber=False,observe=True,fill=0xA5,irq=0),
    'clobber':dict(error_value=0,send_value=1,clobber=True,observe=True,fill=0xA5,irq=0),
    'fill':dict(error_value=0,send_value=1,clobber=False,observe=True,fill=0x39,irq=0),
    'irq1':dict(error_value=0,send_value=1,clobber=False,observe=True,fill=0xA5,irq=128),
    'irq1_off':dict(error_value=0,send_value=1,clobber=False,observe=False,fill=0xA5,irq=128),
    'irq1_error1':dict(error_value=1,send_value=1,clobber=False,observe=True,fill=0xA5,irq=128),
}


def require_matrix(report,bodies):
    need(report['cpu_executed']is True and len(report['fixtures'])==7 and len(report['runs'])==63,
         'Wait finite nine-policy seven-input matrix')
    grouped={}
    for row in report['runs']:
        kind,r=row['kind'],row['result'];need(kind in POLICIES,'Wait known policy')
        policy=POLICIES[kind];ordinal=r['fixture']['ordinal']
        need(type(ordinal)is int and 0<=ordinal<7,'Wait fixture ordinal')
        need(r['fixture']==fixture_for(report['fixtures'][ordinal],policy['irq'])and
             r['policy']==dict(error=policy['error_value'],send=policy['send_value'],clobber=policy['clobber'])and
             r['observe']==policy['observe']and r['fill']==policy['fill'],'Wait fixture/policy binding')
        B.require_result(r,bodies);grouped.setdefault(kind,[]).append(r)
    need(set(grouped)==set(POLICIES)and all([r['fixture']['ordinal']for r in rows]==list(range(7))for rows in grouped.values()),
         'Wait distinct ordered policy/input grid')
    for i,normal in enumerate(grouped['normal']):
        for name in('off','send_false'):
            r=grouped[name][i];need(all(r[k]==normal[k]for k in('returned','frame_after','destination_after','whole_ram_sha256')),
                'Wait OFF/SendFALSE neutral finite return and memory')
        irq=grouped['irq1'][i];off=grouped['irq1_off'][i]
        need(all(irq[k]==off[k]for k in('returned','frame_after','destination_after','whole_ram_sha256')),'Wait I1 OFF neutral')
        need(all(irq[k]==normal[k]for k in('frame_after','destination_after','whole_ram_sha256'))and
             irq['returned'][15]==normal['returned'][15]|0x80 and
             irq['returned'][2]==normal['returned'][2]|0x80,'Wait I1 restored, identical memory with different control ABI')
        for name,base in(('error1',normal),('irq1_error1',irq)):
            error=grouped[name][i];need(error['returned'][0]==0xFFFFFFFF and base['returned'][0]==base['fixture']['entry'][2]and
                error['destination_after']==base['destination_after'],'Wait native error return after same payload')
            a=bytearray.fromhex(error['frame_after']);b=bytes.fromhex(base['frame_after']);offset=B.FILE+20-B.FRAME
            need(a[offset:offset+4]==b'\x01\0\0\0'and b[offset:offset+4]==b'\0'*4,'Wait error1 actual field')
            a[offset:offset+4]=b[offset:offset+4];need(a==b,'Wait error counter frame differs in one word only')
    return True


def analyze(rom,language,parent_report,seek_report,objects,strategy_object,recipe_dir,raw_dir,prepare_only=False):
    import unicorn
    need(unicorn.__version__=='2.1.4','Wait IRQ capability is qualified for Unicorn2.1.4 only')
    sources=source_identities();prepared,bodies=prepare(rom,language,parent_report,seek_report,objects,strategy_object,recipe_dir)
    result=dict(schema='native-fs-wait-isolated-v1',language=language,source_sha256=sources,**prepared,
        cpu_model=17,cpu_name='UC_CPU_ARM_CORTEX_A15',unicorn=unicorn.__version__,recipes=B.RECIPES,
        cpu_executed=False,runs=[],limits=[
            'Same isolated Read CPU extended through nonbusy Wait and IRQ leaves, not the complete original parent caller',
            'Declared completion stat/command/error projection; native Send/list/queue/archive/thread completion excluded',
            'IRQ CPSR instruction semantics under model17, not ARM9 silicon/timing/interrupt injection',
            'Finite seven positive lengths; no busy Wait, SleepThread, owner ExecuteSync, async/EOF/negative/overflow coverage',
            'Original MW build provenance, natural activation and physical SAVE/cold/hardware remain open'])
    if not prepare_only:
        need(not raw_dir.exists()and not raw_dir.is_symlink()and R.H.P.SOURCE not in raw_dir.resolve().parents,
             'fresh private raw directory')
        raw_dir.mkdir(parents=True)
        for kind,policy in POLICIES.items():
            for base in prepared['fixtures']:
                f=fixture_for(base,policy['irq']);kwargs={k:v for k,v in policy.items()if k!='irq'}
                r=B.run(f,bodies,**kwargs);save(raw_dir/(kind+'-'+str(base['ordinal'])+'.json.gz'),r)
                B.require_result(r,bodies);result['runs'].append(dict(kind=kind,result=r))
            print(language,'native Wait/IRQ',kind,'seven inputs verified',flush=True)
        result['cpu_executed']=True;require_matrix(result,bodies)
    need(source_identities()==sources,'Wait sources changed during run');return result


def irq_capability(rom,language,raw_dir):
    import unicorn
    need(unicorn.__version__=='2.1.4','IRQ capability requires Unicorn2.1.4')
    need(not raw_dir.exists()and not raw_dir.is_symlink()and R.H.P.SOURCE not in raw_dir.resolve().parents,
         'fresh private IRQ raw directory')
    sources=source_identities();model=R.H.P.G.S.SHARED.read_current(rom,language);record=model['record'];bodies={}
    with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        view=R.H.P.G.S.SHARED.gifts_audit.Arm9View(raw)
        for name in('disable','restore'):
            address,n,digest=C.BODIES[name];blob=view.read(address,n)
            need(sha(blob)==digest,'IRQ current raw body identity');bodies[address]=blob
    del model;gc.collect();raw_dir.mkdir(parents=True);rows=[]
    for flags in(0,6,10,15):
        for fiq in(0,64):
            for irq in(0,128):
                cpsr=(flags<<28)|fiq|irq|0x1F
                for observe in(True,False):
                    r=B.run_irq_pair(cpsr,bodies,observe);save(raw_dir/(str(cpsr)+'-'+str(observe)+'.json.gz'),r);rows.append(r)
    B.require_irq_rows(rows,bodies)
    need(sources==source_identities(),'IRQ sources changed during execution')
    return dict(schema='native-irq-leaf-capability-v1',input=record,language=language,
        source_sha256=sources,unicorn=unicorn.__version__,cpu_model=17,cpu_name='UC_CPU_ARM_CORTEX_A15',
        rows=rows,passed=True,limits='Privileged SYS isolated leaves only; no IRQ injection, ARM9 timing, hardware or Wait execution')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('rom','parent-report','seek-report','objects','strategy-object','recipe-dir','json'):
        p.add_argument('--'+name,type=Path,required=name in('rom','json'))
    p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--raw-dir',type=Path)
    group=p.add_mutually_exclusive_group();group.add_argument('--prepare-only',action='store_true')
    group.add_argument('--irq-capability',action='store_true');a=p.parse_args()
    try:
        need(a.prepare_only or a.raw_dir is not None,'--raw-dir required for CPU execution')
        need(not a.json.exists()and not a.json.is_symlink()and R.H.P.SOURCE not in a.json.resolve().parents,
             'fresh private JSON output')
        if a.irq_capability:result=irq_capability(a.rom,a.language,a.raw_dir)
        else:
            need(all(getattr(a,n)is not None for n in('parent_report','seek_report','objects','strategy_object','recipe_dir')),
                 '--parent-report/--seek-report/--objects/--strategy-object/--recipe-dir required for Read/Wait')
            result=analyze(a.rom,a.language,a.parent_report,a.seek_report,a.objects,a.strategy_object,a.recipe_dir,a.raw_dir,a.prepare_only)
        save(a.json,result)
    except ValueError as e:p.exit(2,str(e)+'\n')
    print(a.language,'IRQ leaf capability verified'if a.irq_capability else'Wait inputs prepared without CPU'if a.prepare_only else'native isolated Wait/IRQ matrix verified')


if __name__=='__main__':main()
