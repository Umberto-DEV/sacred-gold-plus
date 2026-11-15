"""Finite ExecuteSync composition; Translate is one explicit error-field model.

The pure oracle composes authenticated source predictors, never their RAM
builders or CPU collectors. Counter Wakeup preimages are checked against their
own source-derived state rather than accepted by weakening the parent oracle.
"""
from pathlib import Path
import importlib.util,struct,types


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


J=load('native_sync_qualified_join',Path(__file__).with_name('fs_exec_sync_join_bench.py'))
N,Q=J.N,J.N.Q
R,E=Q.E,Q.E.E
S,B,need,sha=E.S,E.B,E.need,E.sha
need(sha(Path(J.__file__).read_bytes())=='bd0f038c6b6c94faa9a4090f3165e14402adeafc166560640e4d9d9defb286f1',
     'NativeSync qualified Join predictor drift')
TOP,FILE,ARC,BASE,SIZE,REGS=E.TOP,E.FILE,E.ARC,E.BASE,E.SIZE,E.REGS
ENTRY,RETURN,FRAME,TRANSLATE=E.ENTRY,E.RETURN,TOP-416,E.TRANSLATE
wire=E.wire
NATIVE_BODIES={ENTRY:(68,E.BODY_SHA),R.ENTRY:R.BODIES[R.ENTRY],Q.WAKE:Q.BODIES[Q.WAKE],
    N.NEXT:N.BODIES[N.NEXT],S.DISABLE:S.BODIES[S.DISABLE],S.RESTORE:S.BODIES[S.RESTORE]}
TRANSLATE_GATE_SHA='e506f1b7eb5c3563131ed686a9d777e4e9c799db0c7793becade44d0afd6048c'
BODIES={**NATIVE_BODIES,S.ENTRY:S.BODIES[S.ENTRY],TRANSLATE:(4,TRANSLATE_GATE_SHA)}


def check_fixture(f):
    need(type(f['translated_result'])is int and f['translated_result']in(0,1),'NativeSync typed model result')
    need(all(type(f[k])is str for k in('captured304','captured_guard56','archive_before','parent_whole_ram_sha256')),
         'NativeSync exact input byte/hash strings')
    captured,guard=(bytes.fromhex(f[k])for k in('captured304','captured_guard56'))
    digest=f['parent_whole_ram_sha256']
    need(len(captured)==304 and guard==b'\xa5'*56 and len(digest)==64 and
         all(c in '0123456789abcdef'for c in digest),'NativeSync finite captured304/A5 guard56/parent digest')
    E.check_fixture(dict(f,frame=(guard[-8:]+captured).hex()))
    return b'\xa5'*56+guard+captured,bytes.fromhex(f['archive_before'])


def next_predictor(expected,normal,bypass):
    """Reuse exactly the parent code, replacing only its prestate validator.

    A zero digest is an internal shape sentinel for the old checker, which does
    not authenticate memory. It is never exposed as checkpoint provenance.
    Both complete wire states are bound here; counter bytes are not normalized.
    """
    need(type(bypass)is bool,'NativeSync typed counter policy')
    keys=('entry','captured408','archive_before','translated_result','profile')
    def validate_shape(f):return N.check_fixture(dict(f,parent_whole_ram_sha256='0'*64))
    validate_shape(normal)
    need(normal['profile']=='normal' and expected['profile']==('bypass_wake'if bypass else'normal'),
         'NativeSync declared source prestate profile')
    reference=wire({k:expected[k]for k in keys})
    def checker(f):
        need(wire({k:f[k]for k in keys})==reference,'NativeSync exact source-derived Next prestate')
        if not bypass:return validate_shape(f)
        return bytes.fromhex(f['captured408']),bytes.fromhex(f['archive_before'])
    setup_globals=dict(N.input_state.__globals__,check_fixture=checker)
    setup=types.FunctionType(N.input_state.__code__,setup_globals,N.input_state.__name__,
                             N.input_state.__defaults__,N.input_state.__closure__)
    predict_globals=dict(N.predict.__globals__,input_state=setup)
    predict=types.FunctionType(N.predict.__code__,predict_globals,N.predict.__name__,
                               N.predict.__defaults__,N.predict.__closure__)
    return predict,setup


def release_prestate(f,initial,exec_prediction):
    service=exec_prediction['services'][1]
    return dict(entry=service['entry'],frame=(initial[64:104]+bytes.fromhex(service['frame_before'])).hex(),
        captured_parent_guard56=initial[32:88].hex(),archive_before=service['archive_before'],
        translated_result=f['translated_result'])


def next_prestate(f,initial,release,profile):
    frame=initial[:64]+bytes.fromhex(release['frame_after'])
    return dict(entry=release['returned'],captured408=frame[8:].hex(),archive_before=release['archive_after'],
                translated_result=f['translated_result'],profile=profile)


def predict(f,bypass_wakeup=False):
    initial,archive=check_fixture(f);need(type(bypass_wakeup)is bool,'NativeSync strict Wakeup bypass policy')
    ep=E.predict(dict(f,frame=initial[104:].hex()),result=f['translated_result'])
    rf=release_prestate(f,initial,ep);normal=Q.predict(rf)
    release=Q.predict(rf,bypass_wakeup=True)if bypass_wakeup else normal
    normal_nf=next_prestate(f,initial,normal,'normal')
    nf=next_prestate(f,initial,release,'bypass_wake'if bypass_wakeup else'normal')
    next_source,_=next_predictor(nf,normal_nf,bypass_wakeup);np=next_source(nf)
    jf=dict(entry=np['returned'],frame=np['frame_after'],guard='a5'*56,archive_before=np['archive_after'],
            translated_result=f['translated_result'],parent_whole_ram_sha256='0'*64)
    jp=J.predict(jf)
    translate=dict(ep['services'][0])
    for key in('frame_before','frame_after'):translate[key]=(initial[:104]+bytes.fromhex(translate[key])).hex()
    services=[translate]
    for service in release['services']:
        service=dict(service)
        for key in('frame_before','frame_after'):service[key]=(initial[:64]+bytes.fromhex(service[key])).hex()
        services.append(service)
    checkpoints={}
    def checkpoint(name,pc,regs,frame,arc):
        need(len(bytes.fromhex(frame))==416 and len(bytes.fromhex(arc))==92,'NativeSync checkpoint full owner windows')
        checkpoints[name]=dict(pc=hex(pc),regs=list(regs),frame=frame,archive=arc)
    checkpoint('translate_entry',TRANSLATE,translate['entry'],translate['frame_before'],translate['archive_before'])
    checkpoint('translate_return',0x20D7754,translate['returned'],translate['frame_after'],translate['archive_after'])
    checkpoint('release_entry',R.ENTRY,rf['entry'],translate['frame_after'],rf['archive_before'])
    boundary=release['boundaries'][0]
    checkpoint('wake_entry',Q.WAKE,boundary['entry'],(initial[:64]+bytes.fromhex(boundary['frame_before'])).hex(),boundary['archive_before'])
    checkpoint('wake_return',0x20D68B4,boundary['returned'],(initial[:64]+bytes.fromhex(boundary['frame_after'])).hex(),boundary['archive_after'])
    checkpoint('release_return',0x20D7760,release['returned'],(initial[:64]+bytes.fromhex(release['frame_after'])).hex(),release['archive_after'])
    checkpoint('next_entry',N.NEXT,np['incoming_next'],(initial[:64]+bytes.fromhex(release['frame_after'])).hex(),release['archive_after'])
    checkpoint('next_return',J.ENTRY,np['returned'],np['frame_after'],np['archive_after'])
    checkpoint('final',RETURN,jp['returned'],jp['frame_after'],jp['archive_after'])
    flow=ep['flow'][:7]+release['flow']+np['flow']+jp['flow']
    stores=ep['stores']+release['stores']+np['stores']
    reads=ep['reads'][:1]+release['reads']+np['reads']+jp['reads']
    unique=len({event['pc']for event in flow})
    expected=(110,99,20,28)if bypass_wakeup else(131,109,26,35)
    need((len(flow),unique,len(stores),len(reads))==expected,'NativeSync finite source transcript')
    return dict(flow=flow,stores=stores,reads=reads,services=services,model_stores=translate['writes'],
        checkpoints=checkpoints,returned=jp['returned'],frame_before=initial.hex(),frame_after=jp['frame_after'],
        archive_before=archive.hex(),archive_after=jp['archive_after'],next_prestate=nf,
        steps=len(flow)+len(services)+1,native_peak=112,unique_native_starts=unique,stop=hex(RETURN))


def parent_memory(f,bodies):
    initial,archive=check_fixture(f)
    need(set(bodies)==set(BODIES),'NativeSync exact six native/retained Send/Translate gate chunks')
    for address,(n,digest)in BODIES.items():
        need(type(bodies[address])is bytes and len(bodies[address])==n and sha(bodies[address])==digest,
             'NativeSync authenticated code component')
    image=bytearray(S.initial_memory(f['send_fixture'],{a:bodies[a]for a in S.BODIES},0xA5))
    image[TOP-304-BASE:TOP-BASE]=bytes.fromhex(f['captured304'])
    image[ARC-BASE:ARC-BASE+92]=archive
    need(sha(bytes(image))==f['parent_whole_ram_sha256'],'NativeSync readonly-transferred observed Send whole image')
    need(image[FRAME-BASE:TOP-BASE]==initial and image[FRAME-56-BASE:FRAME-BASE]==b'\xa5'*56,
         'NativeSync source-filled extra112 bytes and captured old360 bytes agree with parent digest')
    return bytes(image)


def initial_memory(f,bodies):
    image=bytearray(parent_memory(f,bodies))
    for address in(*NATIVE_BODIES,TRANSLATE):image[address-BASE:address-BASE+len(bodies[address])]=bodies[address]
    need(image[RETURN-BASE:RETURN-BASE+4]==bodies[S.ENTRY][-4:],'NativeSync retained original stopped Send POP')
    return bytes(image)


def check_wake_bypass_input(incoming,bypass_wakeup,services):
    need(bypass_wakeup is True and services==1 and incoming[0]==FILE+24 and
         incoming[13:15]==[TOP-328,0x20D68B4],'NativeSync negative Wakeup model actual queue/SP/LR')


def run(f,bodies,bypass_wakeup=False,observe=True):
    """One CPU from7744 to7928; one positive host field projection only."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR,UC_ARM_REG_R0
    need(type(bypass_wakeup)is type(observe)is bool and unicorn.__version__=='2.1.4','NativeSync strict policies/Unicorn2.1.4')
    before=initial_memory(f,bodies);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'NativeSync qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();flow=[];stores=[];reads=[];services=[];model_stores=[];checkpoints={};seen=set()
    steps=peak=0;returned=fault=None
    phases={TRANSLATE:'translate_entry',0x20D7754:'translate_return',R.ENTRY:'release_entry',Q.WAKE:'wake_entry',
            0x20D68B4:'wake_return',0x20D7760:'release_return',N.NEXT:'next_entry',J.ENTRY:'next_return',RETURN:'final'}
    def model(pc):
        incoming=regs();fb=read(FRAME,416).hex();ab=read(ARC,92).hex();writes=[]
        if pc==TRANSLATE:
            need(not services and incoming[:2]==[FILE,4]and incoming[13:15]==[TOP-312,0x20D7754]and
                 read(pc,4)==bodies[TRANSLATE]and read(FILE+20,4)==b'\x02\0\0\0',
                 'NativeSync sole Translate projection input and original intercepted gate')
            value=f['translated_result'];event=dict(pc=hex(pc),address=FILE+20,bytes=4,before=read(FILE+20,4).hex(),value=value)
            writes.append(event);model_stores.append(event);u.mem_write(FILE+20,struct.pack('<I',value))
            scope=E.SCOPES[TRANSLATE]
        else:
            check_wake_bypass_input(incoming,bypass_wakeup,len(services))
            value=0;scope='Declared same-code bypass control; no native Wakeup effects'
        u.reg_write(UC_ARM_REG_R0,value)
        service=dict(pc=hex(pc),entry=incoming,returned=regs(),frame_before=fb,frame_after=read(FRAME,416).hex(),
            archive_before=ab,archive_after=read(ARC,92).hex(),writes=writes,model_scope=scope)
        if pc==TRANSLATE:service['result_r0']=value
        else:service['native']=False
        services.append(service);u.reg_write(UC_ARM_REG_PC,incoming[14])
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=256,'NativeSync bounded instruction count')
        if pc in phases:
            phase=phases[pc];need(phase not in checkpoints,'NativeSync single visit of each checkpoint')
            checkpoints[phase]=dict(pc=hex(pc),regs=regs(),frame=read(FRAME,416).hex(),archive=read(ARC,92).hex())
        if pc==RETURN:
            need(read(pc,4)==bodies[S.ENTRY][-4:],'NativeSync original stopped Send POP');returned=regs();u.emu_stop();return
        if pc==TRANSLATE or(bypass_wakeup and pc==Q.WAKE):model(pc);return
        selected=next(((a,bodies[a])for a in NATIVE_BODIES if a<=pc<a+len(bodies[a])),None)
        need(selected is not None and n==4 and(pc-selected[0])%4==0 and not regs()[15]&32,'NativeSync admitted ARM native instruction')
        a,body=selected;need(read(pc,4)==body[pc-a:pc-a+4],'NativeSync live instruction identity')
        seen.add(pc);peak=max(peak,TOP-304-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC)
        need(any(m.write_allowed(pc,address,n)for m in(E,R,Q.W,N)),'NativeSync native store PC/owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    def word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC)
        need(any(m.read_allowed(pc,address,n)for m in(E,R,Q.W,N)),'NativeSync native read PC/owner')
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
                         'NativeSync strict observation/policy fields')
    want=predict(f,**row['policy']);before=initial_memory(f,bodies);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected={key:want[key]for key in('returned','services','model_stores','checkpoints','steps','native_peak',
        'frame_before','frame_after','archive_before','archive_after')}
    expected.update(entry=f['entry'],observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,
        halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),guard_before='a5'*56,guard_after='a5'*56,
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for key in('flow','stores','reads'):expected[key]=want[key]if row['observe']else[]
    for key,value in expected.items():need(wire(row[key])==wire(value),'NativeSync source-derived '+key)
    return True
