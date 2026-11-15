"""Compose qualified Release/Wakeup source predictions without a context bridge.

Normal execution has four native bodies. The explicit bypass is a falsification
control in the same code image, not an alternative native implementation.
"""
from pathlib import Path
import importlib.util


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


W=load('release_wakeup_qualified_empty',Path(__file__).with_name('os_wakeup_bench.py'))
E,S,B,need,sha=W.W,W.S,W.B,W.need,W.sha
need(sha(Path(W.__file__).read_bytes())=='5ddb3c01357359d20a1c450cd2de93f70162d8445214db96f2464a92c26d8af1','Composition qualified Wakeup predictor drift')
ENTRY,RETURN,WAKE=E.ENTRY,E.RETURN,W.ENTRY
TOP,FILE,ARC,ID,PATH=E.TOP,E.FILE,E.ARC,E.ID,E.PATH
SP,FRAME,BASE,SIZE,REGS=E.SP,W.FRAME,E.BASE,E.SIZE,E.REGS
BODIES={**E.BODIES,WAKE:W.BODIES[WAKE]}
wire=E.wire


def release_fixture(f):
    need(type(f['frame'])is type(f['captured_parent_guard56'])is str,'Composition exact frame/guard hex')
    frame,guard=bytes.fromhex(f['frame']),bytes.fromhex(f['captured_parent_guard56'])
    need(len(frame)==352 and len(guard)==56 and frame[:24]==guard[-24:],'Composition frame352/captured stack24 preimage')
    return dict(f,frame=frame[24:].hex())


def check_fixture(f):
    parent=release_fixture(f);_,archive=E.check_fixture(parent)
    return bytes.fromhex(f['frame']),archive,bytes.fromhex(f['captured_parent_guard56'])


def guard_before(f,fill):
    _,_,guard=check_fixture(f)
    need(type(fill)is int and fill in(0xA5,0x39),'Composition strict lower guard fill')
    return bytes([fill])*24+guard[:32]


def predict(f,bypass_wakeup=False):
    frame,archive,guard=check_fixture(f);need(type(bypass_wakeup)is bool,'Composition strict bypass MODEL policy')
    parent=E.predict(release_fixture(f));service=parent['services'][0]
    child=dict(f,entry=service['entry'],frame=(frame[:24]+bytes.fromhex(service['frame_before'])).hex(),archive_before=service['archive_before'])
    W.check_fixture(child)
    if bypass_wakeup:
        flow=parent['flow'];stores=parent['stores'];reads=parent['reads'];new_stack=frame[:24]
        child_return=service['returned'];steps=36;peak=16
    else:
        native=W.predict(child);child_return=native['returned'];new_stack=bytes.fromhex(native['frame_after'])[:24]
        split=next(i for i,e in enumerate(parent['flow'])if e['pc']=='0x20d68b0')+1
        flow=parent['flow'][:split]+native['flow'];r=list(child_return)
        def at(address):flow.append(dict(pc=hex(address),regs=list(r)))
        at(0x20D68B4);r[0]=r[6]
        at(0x20D68B8);r[14]=0x20D68BC;S.native_irq(r,at,E.RESTORE)
        need(r==parent['flow'][-1]['regs'],'Composition native epilogue converges full registers before original POP')
        flow.append(parent['flow'][-1]);stores=parent['stores']+native['stores']
        reads=parent['reads'][:3]+native['reads']+parent['reads'][3:];steps=56;peak=40
        need((len(flow),len(stores),len(reads),len({e['pc']for e in flow}))==(55,15,14,44),'Composition finite source transcript')
    boundary=dict(pc=hex(WAKE),native=not bypass_wakeup,entry=service['entry'],returned=child_return,
        frame_before=child['frame'],frame_after=(new_stack+bytes.fromhex(service['frame_after'])).hex(),
        archive_before=service['archive_before'],archive_after=service['archive_after'])
    services=[dict(boundary,writes=[],model_scope='Declared same-code bypass control; no native Wakeup effects')]if bypass_wakeup else[]
    return dict(flow=flow,stores=stores,reads=reads,services=services,boundaries=[boundary],returned=parent['returned'],
        frame_before=f['frame'],frame_after=(new_stack+bytes.fromhex(parent['frame_after'])).hex(),archive_after=parent['archive_after'],
        steps=steps,native_peak=peak,unique_native_starts=len({e['pc']for e in flow}),stop=hex(RETURN))


def initial_memory(f,bodies,fill):
    frame,archive,_=check_fixture(f);guard=guard_before(f,fill)
    need(set(bodies)==set(BODIES),'Composition exact four native bodies')
    image=bytearray(bytes([fill])*SIZE)
    for address,(n,digest)in BODIES.items():
        body=bodies[address];need(type(body)is bytes and len(body)==n and sha(body)==digest,'Composition qualified code identity')
        image[address-BASE:address-BASE+n]=body
    image[FRAME-BASE:TOP-BASE]=frame;image[ARC-BASE:ARC-BASE+92]=archive
    image[FRAME-56-BASE:FRAME-BASE]=guard
    # Actual ExecuteSync LDR fetch; stopped before execution.
    image[RETURN-BASE:RETURN-BASE+4]=bytes.fromhex('080094e5')
    return bytes(image)


def run(f,bodies,bypass_wakeup=False,observe=True,fill=0xA5):
    """One actual Release context; normal path has no modeled callee/state writes."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR,UC_ARM_REG_R0
    need(type(bypass_wakeup)is type(observe)is bool and unicorn.__version__=='2.1.4','Composition strict policies/Unicorn2.1.4')
    before=initial_memory(f,bodies,fill);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Composition qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();flow=[];stores=[];reads=[];services=[];boundaries=[];pending=None;seen=set();steps=0;peak=0;returned=None;fault=None
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned,pending
        steps+=1;need(steps<=80,'Composition bounded native instruction count')
        if pc==RETURN:returned=regs();u.emu_stop();return
        if pc==0x20D68B4:
            need(pending is not None,'Composition actual Wakeup return requires its incoming boundary')
            boundaries.append(dict(pending,returned=regs(),frame_after=read(FRAME,352).hex(),archive_after=read(ARC,92).hex()));pending=None
        if pc==WAKE:
            need(pending is None and not boundaries,'Composition exactly one actual nested Wakeup')
            actual=regs();child=dict(f,entry=actual,frame=read(FRAME,352).hex(),archive_before=read(ARC,92).hex());W.check_fixture(child)
            need(n==4 and read(pc,4)==bodies[WAKE][:4],'Composition original native Wakeup entry instruction, including bypass control')
            pending=dict(pc=hex(WAKE),native=not bypass_wakeup,entry=actual,frame_before=child['frame'],archive_before=child['archive_before'])
            if bypass_wakeup:
                # Falsifier only: same initialized code, explicit return-only model.
                u.reg_write(UC_ARM_REG_R0,0);u.reg_write(UC_ARM_REG_PC,actual[14])
                services.append(dict(pending,returned=regs(),frame_after=read(FRAME,352).hex(),archive_after=read(ARC,92).hex(),
                    writes=[],model_scope='Declared same-code bypass control; no native Wakeup effects'))
                return
        selected=next(((a,b)for a,b in bodies.items()if a<=pc<a+len(b)),None)
        need(selected is not None and(pc-selected[0])%4==0 and n==4 and not regs()[15]&32,'Composition native ARM whitelist')
        a,body=selected;need(read(pc,4)==body[pc-a:pc-a+4],'Composition live native instruction bytes')
        seen.add(pc);peak=max(peak,SP-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(E.write_allowed(pc,address,n)or W.write_allowed(pc,address,n),'Composition native PC/word/write owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    def load_word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(E.read_allowed(pc,address,n)or W.read_allowed(pc,address,n),'Composition native PC/word/read owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,load_word)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=80)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=dict(bypass_wakeup=bypass_wakeup),observe=observe,fill=fill,entry=entry,returned=returned,flow=flow,stores=stores,
        reads=reads,services=services,boundaries=boundaries,steps=steps,native_peak=peak,observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),
        fault=fault,halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),frame_before=f['frame'],frame_after=read(FRAME,352).hex(),
        archive_after=read(ARC,92).hex(),guard_before=guard_before(f,fill).hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    r=row;f=r['fixture'];check_fixture(f)
    need(type(r['observe'])is bool and type(r['policy'])is dict and set(r['policy'])=={'bypass_wakeup'},'Composition strict observation/policy fields')
    want=predict(f,**r['policy']);before=initial_memory(f,bodies,r['fill']);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected=dict(entry=f['entry'],returned=want['returned'],services=want['services'],boundaries=want['boundaries'],steps=want['steps'],native_peak=want['native_peak'],
        observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),
        frame_before=f['frame'],frame_after=want['frame_after'],archive_after=want['archive_after'],guard_before=guard_before(f,r['fill']).hex(),
        guard_after=guard_before(f,r['fill']).hex(),before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for key in('flow','stores','reads'):expected[key]=want[key]if r['observe']else[]
    for key,value in expected.items():need(wire(r[key])==wire(value),'Composition source-derived '+key)
    return True
