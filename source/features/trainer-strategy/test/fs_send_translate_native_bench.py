"""One continuous native Send/Translate path with a declared default model.

The oracle composes source transitions from the initial Send fixture. It never
uses a captured postimage as input; inherited model effects are replaced.
"""
from pathlib import Path
import importlib.util,struct


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


T=load('send_translate_qualified_translate',Path(__file__).with_name('fs_translate_bench.py'))
H,need,sha,wire=T.H,T.need,T.sha,T.wire
need(sha(Path(T.__file__).read_bytes())=='af888c8f217aeee9bbcf182955e5ed854a1b9afdad843859e5cf88c7460224bf','Send Translate qualified Translate oracle drift')
TOP,FILE,ARC,FRAME,BASE,SIZE,REGS=T.TOP,T.FILE,T.ARC,T.FRAME,T.BASE,T.SIZE,T.REGS
ENTRY,RETURN,TRANSLATE,DEFAULT=H.ENTRY,H.RETURN,T.ENTRY,T.DEFAULT
BODIES=T.BODIES
NATIVE_BODIES={**H.NATIVE_BODIES,TRANSLATE:(396,T.CODE_SHA)}
PHASES={H.E.ENTRY:'exec_entry',TRANSLATE:'translate_entry',T.RETURN:'translate_return',H.E.R.ENTRY:'release_entry',
    H.E.Q.WAKE:'wake_entry',0x20D68B4:'wake_return',0x20D7760:'release_return',H.E.N.NEXT:'next_entry',
    H.E.J.ENTRY:'next_return',H.E.RETURN:'send_pop',RETURN:'final',DEFAULT:'default_entry',
    0x20D6984:'default_return',0x20D6A40:'before_error_store'}
LIMIT=384


def check_fixture(f):
    return H.check_fixture(f)


def predict(f,early_error=False):
    initial,arc=check_fixture(f);need(type(early_error)is bool,'Send Translate strict early-error policy')
    parent=H.predict(f);cp=parent['checkpoints']['translate_entry']
    child=T.predict(dict(entry=cp['regs'],frame=cp['frame'],archive_before=cp['archive'],
                         guard=f['guard'],default_result=f['translated_result']),early_error)
    need(len(parent['flow'])==221 and parent['flow'][93]['pc']==hex(T.RETURN)and
         parent['flow'][96]['pc']==hex(H.E.R.ENTRY),'Send Translate source splice boundaries')
    r=list(child['returned']);bridge=[]
    for pc in(0x20D7754,0x20D7758,0x20D775C):
        bridge.append(dict(pc=hex(pc),regs=list(r)))
        if pc==0x20D7754:r[1]=r[0]
        elif pc==0x20D7758:r[0]=r[4]
        else:r[14]=0x20D7760
    need(r==parent['flow'][96]['regs'],'Send Translate native bridge restores Release input')
    flow=parent['flow'][:93]+child['flow']+bridge+parent['flow'][96:]
    stores=parent['stores'][:17]+child['stores']+parent['stores'][17:]
    reads=parent['reads'][:14]+child['reads']+parent['reads'][14:]
    # Recompute all preimages in causal order. Translate saved24 is later
    # overwritten by Release/Wakeup; the six changed preimages remain evidence.
    frame,archive=bytearray(initial),bytearray(arc);actual=[];changed=[];checkpoints={};applied=False
    def owner(address,n):
        if FRAME<=address and address+n<=TOP:return frame,address-FRAME
        if ARC<=address and address+n<=ARC+92:return archive,address-ARC
        if address==T.POOL and n==4:return struct.pack('<I',T.TABLE),0
        if address==T.TABLE+16 and n==4:return struct.pack('<I',DEFAULT),0
        raise ValueError('Send Translate source word owner')
    for event in flow+[dict(pc=hex(RETURN),regs=parent['returned'])]:
        pc=event['pc'];address=int(pc,16)
        if address==0x20D6984:
            need(not applied,'Send Translate one declared default return');applied=True
            for w in child['model_stores']:
                m,i=owner(w['address'],4);need(m[i:i+4].hex()==w['before'],'Send Translate explicit model preimage')
                struct.pack_into('<I',m,i,w['value'])
        if address==DEFAULT:raise ValueError('Send Translate model must not enter native flow')
        if address in PHASES:
            checkpoints[PHASES[address]]=dict(pc=pc,regs=event['regs'],frame=frame.hex(),archive=archive.hex())
        # default_entry is intercepted, therefore not in native flow.
        if address==0x20D6980:
            checkpoints['default_entry']=child['checkpoints']['default_entry']
        for rd in reads:
            if rd['pc']==pc:
                m,i=owner(rd['address'],rd['bytes']);need(bytes(m[i:i+rd['bytes']]).hex()==rd['hex'],
                    'Send Translate source native read preimage')
        for index,w in enumerate(stores):
            if w['pc']==pc:
                m,i=owner(w['address'],w['bytes']);need(isinstance(m,bytearray),'Send Translate writable source owner')
                before=bytes(m[i:i+4]).hex()
                if before!=w['before']:changed.append(index)
                actual.append(dict(w,before=before));struct.pack_into('<I',m,i,w['value'])
    need(applied and changed==[26,27,28,29,39,40],'Send Translate six source-derived late preimage differences')
    need(frame.hex()==parent['frame_after']and archive.hex()==parent['archive_after'],
         'Send Translate all final memory fields converge, without runtime masks')
    for name in('default_return','before_error_store','translate_return'):
        want=child['checkpoints']['final'if name=='translate_return'else name]
        need(wire(checkpoints[name])==wire(want),'Send Translate isolated source checkpoint '+name)
    need((len(flow),len({e['pc']for e in flow}),len(actual),len(reads))==(260,216,50,68),
         'Send Translate finite combined source transcript')
    return dict(flow=flow,stores=actual,reads=reads,services=child['services'],model_stores=child['model_stores'],
        checkpoints=checkpoints,returned=parent['returned'],frame_before=initial.hex(),frame_after=frame.hex(),
        archive_before=arc.hex(),archive_after=archive.hex(),steps=262,native_peak=136,unique_native_starts=216,stop=hex(RETURN))


def initial_memory(f,bodies):
    need(set(bodies)==set(BODIES),'Send Translate exact component set')
    for a,(n,digest)in BODIES.items():
        need(type(bodies[a])is bytes and len(bodies[a])==n and sha(bodies[a])==digest,'Send Translate authenticated component')
    old={a:bodies[a][:n]for a,(n,_)in H.BODIES.items()}
    image=bytearray(H.initial_memory(f,old))
    for a in(TRANSLATE,T.TABLE,DEFAULT):image[a-BASE:a-BASE+len(bodies[a])]=bodies[a]
    need(sha(bodies[TRANSLATE][:396])==T.CODE_SHA and bodies[TRANSLATE][-4:]==struct.pack('<I',T.TABLE)and
         bodies[T.TABLE][16:20]==struct.pack('<I',DEFAULT),'Send Translate code/pool/table/default linkage')
    return bytes(image)


def boundaries(f,bodies,early_error=False):
    """Derive whole identities from initial RAM and ordered source writes."""
    before=initial_memory(f,bodies);image=bytearray(before);want=predict(f,early_error);out={}
    def apply(w):
        i=w['address']-BASE;need(w['bytes']==4 and 0<=i<=SIZE-4 and image[i:i+4].hex()==w['before'],
                               'Send Translate source whole write preimage')
        struct.pack_into('<I',image,i,w['value'])
    for w in want['stores'][:17]:apply(w)
    out['translate_entry']=sha(image)
    for event in want['flow'][93:132]:
        if event['pc']=='0x20d6984':
            for w in want['model_stores']:apply(w)
        for w in want['stores'][17:26]:
            if w['pc']==event['pc']:apply(w)
    out['translate_return']=sha(image)
    return out


def run(f,bodies,early_error=False,observe=True):
    """One CPU from original Send entry to original stopped Find ADD."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR,UC_ARM_REG_R0
    need(type(early_error)is type(observe)is bool and unicorn.__version__=='2.1.4','Send Translate typed policies/Unicorn2.1.4')
    before=initial_memory(f,bodies);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Send Translate qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();flow=[];stores=[];reads=[];services=[];model_stores=[];checkpoints={};seen=set()
    steps=peak=0;returned=fault=None
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=LIMIT,'Send Translate bounded384 callbacks, expected262')
        if pc in PHASES:
            phase=PHASES[pc];need(phase not in checkpoints,'Send Translate single checkpoint visit')
            cp=dict(pc=hex(pc),regs=regs(),frame=read(FRAME,416).hex(),archive=read(ARC,92).hex())
            if phase in('translate_entry','translate_return'):cp['whole_ram_sha256']=sha(read(BASE,SIZE))
            checkpoints[phase]=cp
        if pc==RETURN:
            need(read(pc,4)==bodies[RETURN],'Send Translate original stopped Find ADD');returned=regs();u.emu_stop();return
        if pc==DEFAULT:
            incoming=regs();need(not services and n==4 and read(pc,4)==bodies[DEFAULT]and incoming[:2]==[FILE,DEFAULT]and
                incoming[13:15]==[TOP-336,0x20D6984]and incoming[15]==0x6000001F,'Send Translate sole default model ABI/gate')
            fb,ab=read(FRAME,416).hex(),read(ARC,92).hex();writes=[]
            need(read(FILE+20,4)==struct.pack('<I',2)and read(ARC+28,4)==struct.pack('<I',0x213),
                 'Send Translate native busy/transient before default')
            if early_error:
                event=dict(pc=hex(pc),address=FILE+20,bytes=4,before=read(FILE+20,4).hex(),value=f['translated_result'])
                writes.append(event);model_stores.append(event);u.mem_write(FILE+20,struct.pack('<I',f['translated_result']))
            u.reg_write(UC_ARM_REG_R0,f['translated_result'])
            services.append(dict(pc=hex(pc),entry=incoming,returned=regs(),result_r0=f['translated_result'],writes=writes,
                frame_before=fb,frame_after=read(FRAME,416).hex(),archive_before=ab,archive_after=read(ARC,92).hex(),
                model_scope=T.MODEL_SCOPE,early_error=early_error))
            u.reg_write(UC_ARM_REG_PC,incoming[14]);return
        selected=next(((a,count)for a,(count,_)in NATIVE_BODIES.items()if a<=pc<a+count),None)
        need(selected is not None and n==4 and(pc-selected[0])%4==0 and not regs()[15]&32,'Send Translate native ARM whitelist, no pool/table')
        a,_=selected;need(read(pc,4)==bodies[a][pc-a:pc-a+4],'Send Translate live original instruction')
        seen.add(pc);peak=max(peak,entry[13]-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    owners=(H.S,H.E.E,H.E.R,H.E.Q.W,H.E.N,T)
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(any(m.write_allowed(pc,address,n)for m in owners),'Send Translate native write PC/owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    def word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(any(m.read_allowed(pc,address,n)for m in owners),'Send Translate read PC/owner including literal/table')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,word)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=LIMIT)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=dict(early_error=early_error),observe=observe,entry=entry,returned=returned,flow=flow,stores=stores,reads=reads,
        services=services,model_stores=model_stores,checkpoints=checkpoints,steps=steps,native_peak=peak,observed_pcs=sorted(seen),
        cpu_model=u.ctl_get_cpu_model(),fault=fault,halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),
        frame_before=before[FRAME-BASE:TOP-BASE].hex(),frame_after=read(FRAME,416).hex(),archive_before=before[ARC-BASE:ARC-BASE+92].hex(),
        archive_after=read(ARC,92).hex(),guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    f=row['fixture'];need(type(row['observe'])is bool and type(row['policy'])is dict and set(row['policy'])=={'early_error'},
                         'Send Translate strict observation/policy')
    want=predict(f,**row['policy']);before=initial_memory(f,bodies);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    for phase,digest in boundaries(f,bodies,**row['policy']).items():want['checkpoints'][phase]['whole_ram_sha256']=digest
    expected={k:want[k]for k in('returned','services','model_stores','checkpoints','steps','native_peak','frame_before','frame_after','archive_before','archive_after')}
    expected.update(entry=f['entry'],observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,
        halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),guard_before=f['guard'],guard_after=f['guard'],
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for k in('flow','reads','stores'):expected[k]=want[k]if row['observe']else[]
    for k,v in expected.items():need(wire(row[k])==wire(v),'Send Translate source-derived '+k)
    return True
