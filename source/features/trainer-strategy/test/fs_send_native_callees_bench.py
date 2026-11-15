"""One finite Send/ExecuteSync context with one explicit Translate projection.

The oracle composes source transitions. Initial RAM authentication starts at
Send BEFORE its native preparation, never from a future ExecuteSync image.
"""
from pathlib import Path
import importlib.util,struct


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


E=load('send_native_qualified_exec',Path(__file__).with_name('fs_exec_sync_native_callees_bench.py'))
S,need,sha,wire=E.S,E.need,E.sha,E.wire
need(sha(Path(E.__file__).read_bytes())=='c242040a9a92ec2ba6b23bfa6fb954a3c17df66a62e39df3f5bc74845d4133e4','Send native qualified ExecuteSync bench drift')
TOP,FILE,ARC,BASE,SIZE,REGS=E.TOP,E.FILE,E.ARC,E.BASE,E.SIZE,E.REGS
ENTRY,RETURN,FRAME,TRANSLATE=S.ENTRY,S.RETURN,TOP-416,E.TRANSLATE
NATIVE_BODIES={**E.NATIVE_BODIES,S.ENTRY:S.BODIES[S.ENTRY]}
STOP_GATE=struct.pack('<I',0xE28DD00C)
BODIES={**E.BODIES,RETURN:(4,sha(STOP_GATE))}


def check_fixture(f):
    frame,archive=S.check_fixture(f)
    need(type(f['translated_result'])is int and f['translated_result']in(0,1),'Send native typed Translate result')
    need(type(f['guard'])is type(f['parent_whole_ram_sha256'])is str,'Send native exact guard/hash strings')
    digest=f['parent_whole_ram_sha256']
    need(f['guard']=='a5'*56 and len(digest)==64 and all(c in'0123456789abcdef'for c in digest),
         'Send native finite A5 guard and BEFORE digest')
    # The first24 bytes are preserved predecessor guard, not A5 fill. Their
    # exact identity is authenticated with the entire captured BEFORE image.
    need(struct.unpack_from('<I',frame,FILE-(TOP-304)+20)[0]==0,'Send native initial error0, not future busy state')
    return b'\xa5'*112+frame,archive


def predict(f,bypass_wakeup=False):
    initial,archive=check_fixture(f);need(type(bypass_wakeup)is bool,'Send native strict negative policy')
    parent=S.predict(f);service=parent['services'][0]
    # This zero digest is only a legacy pure-checker shape sentinel. It is not
    # an image identity, and neither image authentication nor exported provenance.
    child=dict(entry=service['entry'],captured304=service['frame_before'],captured_guard56=f['guard'],
        archive_before=service['archive_before'],translated_result=f['translated_result'],parent_whole_ram_sha256='0'*64)
    native=E.predict(child,bypass_wakeup)
    r=list(native['returned']);frame=bytes.fromhex(native['frame_after']);saved=struct.unpack_from('<6I',frame,112)
    need(saved[-1]==RETURN and r[13]==TOP-304,'Send native original saved POP target/SP')
    pop=dict(pc='0x20d7928',regs=list(r));reads=[]
    for i in range(6):reads.append(dict(pc='0x20d7928',address=r[13]+4*i,bytes=4,hex=frame[112+4*i:116+4*i].hex()))
    r[3:8]=saved[:5];r[13]+=24
    phases=dict(exec_entry=dict(pc=hex(E.ENTRY),regs=service['entry'],frame=native['frame_before'],archive=service['archive_before']))
    for name,c in native['checkpoints'].items():phases['send_pop'if name=='final'else name]=c
    phases['final']=dict(pc=hex(RETURN),regs=r,frame=native['frame_after'],archive=native['archive_after'])
    flow=parent['flow'][:-1]+native['flow']+[pop]
    stores=parent['stores']+native['stores'];reads=parent['reads'][:-6]+native['reads']+reads
    unique=len({event['pc']for event in flow});counts=(200,167,35,47)if bypass_wakeup else(221,177,41,54)
    need((len(flow),unique,len(stores),len(reads))==counts,'Send native finite source transcript')
    return dict(flow=flow,stores=stores,reads=reads,services=native['services'],model_stores=native['model_stores'],checkpoints=phases,
        returned=r,frame_before=initial.hex(),frame_after=native['frame_after'],archive_before=archive.hex(),archive_after=native['archive_after'],
        steps=len(flow)+len(native['services'])+1,native_peak=136,unique_native_starts=unique,stop=hex(RETURN))


def parent_memory(f,bodies):
    frame,archive=check_fixture(f);need(set(bodies)==set(BODIES),'Send native exact original code/gate chunks')
    for address,(n,digest)in BODIES.items():
        need(type(bodies[address])is bytes and len(bodies[address])==n and sha(bodies[address])==digest,'Send native authenticated code bytes')
    image=S.initial_memory(f,{a:bodies[a]for a in S.BODIES},0xA5)
    need(sha(image)==f['parent_whole_ram_sha256'],'Send native observed BEFORE whole image, no readonly transfer')
    need(image[FRAME-BASE:TOP-BASE]==frame and image[FRAME-56-BASE:FRAME-BASE]==b'\xa5'*56 and
         image[ARC-BASE:ARC-BASE+92]==archive,'Send native ancestral/fill windows match observed initial image')
    return image


def initial_memory(f,bodies):
    image=bytearray(parent_memory(f,bodies))
    for address in(*E.NATIVE_BODIES,TRANSLATE):image[address-BASE:address-BASE+len(bodies[address])]=bodies[address]
    need(image[RETURN-BASE:RETURN-BASE+4]==bodies[RETURN]==STOP_GATE,'Send native retained original Find stopped ADD')
    return bytes(image)


def run(f,bodies,bypass_wakeup=False,observe=True):
    """Execute original native instructions in one CPU; no checkpoint reinjection."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR,UC_ARM_REG_R0
    need(type(bypass_wakeup)is type(observe)is bool and unicorn.__version__=='2.1.4','Send native strict policies/Unicorn2.1.4')
    before=initial_memory(f,bodies);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Send native qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();flow=[];stores=[];reads=[];services=[];model_stores=[];checkpoints={};seen=set()
    steps=peak=0;returned=fault=None
    phases={E.ENTRY:'exec_entry',TRANSLATE:'translate_entry',0x20D7754:'translate_return',E.R.ENTRY:'release_entry',E.Q.WAKE:'wake_entry',
        0x20D68B4:'wake_return',0x20D7760:'release_return',E.N.NEXT:'next_entry',E.J.ENTRY:'next_return',E.RETURN:'send_pop',RETURN:'final'}
    def model(pc):
        incoming=regs();fb=read(FRAME,416).hex();ab=read(ARC,92).hex();writes=[]
        if pc==TRANSLATE:
            need(not services and incoming[:2]==[FILE,4]and incoming[13:15]==[TOP-312,0x20D7754]and
                 read(pc,4)==bodies[TRANSLATE]and read(FILE+20,4)==b'\x02\0\0\0','Send native sole Translate boundary/gate')
            value=f['translated_result'];event=dict(pc=hex(pc),address=FILE+20,bytes=4,before=read(FILE+20,4).hex(),value=value)
            writes.append(event);model_stores.append(event);u.mem_write(FILE+20,struct.pack('<I',value));scope=E.E.SCOPES[TRANSLATE]
        else:
            E.check_wake_bypass_input(incoming,bypass_wakeup,len(services));value=0
            scope='Declared same-code bypass control; no native Wakeup effects'
        u.reg_write(UC_ARM_REG_R0,value)
        service=dict(pc=hex(pc),entry=incoming,returned=regs(),frame_before=fb,frame_after=read(FRAME,416).hex(),
            archive_before=ab,archive_after=read(ARC,92).hex(),writes=writes,model_scope=scope)
        if pc==TRANSLATE:service['result_r0']=value
        else:service['native']=False
        services.append(service);u.reg_write(UC_ARM_REG_PC,incoming[14])
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=256,'Send native bounded instruction count')
        if pc in phases:
            phase=phases[pc];need(phase not in checkpoints,'Send native single checkpoint visit')
            checkpoints[phase]=dict(pc=hex(pc),regs=regs(),frame=read(FRAME,416).hex(),archive=read(ARC,92).hex())
        if pc==RETURN:
            need(read(pc,4)==bodies[RETURN],'Send native original stopped Find ADD');returned=regs();u.emu_stop();return
        if pc==TRANSLATE or(bypass_wakeup and pc==E.Q.WAKE):model(pc);return
        selected=next(((a,bodies[a])for a in NATIVE_BODIES if a<=pc<a+len(bodies[a])),None)
        need(selected is not None and n==4 and(pc-selected[0])%4==0 and not regs()[15]&32,'Send native admitted ARM instruction')
        a,body=selected;need(read(pc,4)==body[pc-a:pc-a+4],'Send native live instruction identity')
        seen.add(pc);peak=max(peak,entry[13]-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    owners=(S,E.E,E.R,E.Q.W,E.N)
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(any(m.write_allowed(pc,address,n)for m in owners),'Send native store PC/owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    def word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(any(m.read_allowed(pc,address,n)for m in owners),'Send native read PC/owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,word)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=256)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=dict(bypass_wakeup=bypass_wakeup),observe=observe,entry=entry,returned=returned,
        flow=flow,stores=stores,reads=reads,services=services,model_stores=model_stores,checkpoints=checkpoints,
        steps=steps,native_peak=peak,observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,
        halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),
        frame_before=before[FRAME-BASE:TOP-BASE].hex(),frame_after=read(FRAME,416).hex(),
        archive_before=before[ARC-BASE:ARC-BASE+92].hex(),archive_after=read(ARC,92).hex(),
        guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    f=row['fixture'];need(type(row['observe'])is bool and type(row['policy'])is dict and set(row['policy'])=={'bypass_wakeup'},
        'Send native strict observation/policy fields')
    want=predict(f,**row['policy']);before=initial_memory(f,bodies);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected={key:want[key]for key in('returned','services','model_stores','checkpoints','steps','native_peak',
        'frame_before','frame_after','archive_before','archive_after')}
    expected.update(entry=f['entry'],observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,
        halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),guard_before=f['guard'],guard_after=f['guard'],
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for key in('flow','stores','reads'):expected[key]=want[key]if row['observe']else[]
    for key,value in expected.items():need(wire(row[key])==wire(value),'Send native source-derived '+key)
    return True
