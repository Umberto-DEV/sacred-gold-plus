"""Finite ExecuteSync wrapper with explicit, incomplete callee field projections.

Only this68-byte native wrapper is attributed. Translate/Release/Next are models;
no directory resolution, ID delivery, native completion, IRQ or thread work occurs.
"""
from pathlib import Path
import importlib.util,json,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


S=load('exec_sync_qualified_send_helpers',Path(__file__).with_name('fs_send_bench.py'))
need,sha,B=S.need,S.sha,S.B
need(sha(Path(S.__file__).read_bytes())=='a8f19c5c3ca7741566253df326e97cfb1e15b69708ec8f2b02d94c87819c54d0','ExecuteSync qualified Send helper drift')
ENTRY,END,RETURN,TRANSLATE,RELEASE,NEXT=0x20D7744,0x20D7788,0x20D7928,0x20D68C0,0x20D6864,0x20D749C
TOP,FILE,ARC,ID,PATH=S.TOP,S.FILE,S.ARC,S.ID,S.PATH
SP,FRAME,BASE,SIZE,REGS=TOP-304,TOP-312,S.BASE,S.SIZE,S.REGS
BODY_SHA='44b2f23b47f01552bd478420b9a14ae0fc2ed6013e7d551d5112075264a43d55'
archive=bytearray(S.ARCHIVE);struct.pack_into('<I',archive,28,0x13);struct.pack_into('<I',archive,36,FILE);ARCHIVE=bytes(archive)
wire=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'))
SCOPES={TRANSLATE:'error4 projection only; no native translation/default command/ID/prop/IRQ work',
    RELEASE:'unlink/stat/error projection only; no native Release/IRQ/wakeup work; command preserved',
    NEXT:'empty-archive running-flag projection and NULL only; no native Next/IRQ/callback work'}


def check_fixture(f):
    r=f['entry'];need(B.u32s(r),'ExecuteSync unsigned32 actual entry16')
    need(r==[FILE,0x2000009F,0x2000001F,FILE+48,ARC,0,FILE,16,FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
             0,SP,RETURN,0x2000001F],'ExecuteSync finite actual Send caller I0 input')
    need(type(f['frame'])is type(f['archive_before'])is str,'ExecuteSync exact hex preimages')
    frame,archive=bytes.fromhex(f['frame']),bytes.fromhex(f['archive_before'])
    need(len(frame)==312 and archive==ARCHIVE,'ExecuteSync frame312 and actual isolated Send archive92 state')
    for off,value in((0,ARC+32),(4,0),(8,ARC),(12,0x45),(16,4),(20,2),(24,0),(28,0),
                      (48,ARC),(52,0),(56,0),(60,PATH),(64,0),(68,ID)):
        need(struct.unpack_from('<I',frame,FILE-FRAME+off)[0]==value,'ExecuteSync actual linked busy file command4/error2/ARG')
    return frame,archive


def policy(result,void_value,clobber,release_error):
    need(type(result)is int and result in(0,1)and type(void_value)is int and void_value in(0,FILE,0xFFFFFFFF)and
         type(clobber)is bool and(release_error is None or(type(release_error)is int and release_error==1 and result==0)),
         'ExecuteSync finite typed FSResult/void/clobber and declared Release fault policy')
    return dict(result=result,void_value=void_value,clobber=clobber,release_error=release_error)


def predict(f,result=0,void_value=0,clobber=False,release_error=None):
    before,arc=check_fixture(f);frame,archive=bytearray(before),bytearray(arc);r=list(f['entry'])
    policy(result,void_value,clobber,release_error);flow=[];stores=[];reads=[];services=[];pc=ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def owned(address):
        if FRAME<=address and address+4<=FRAME+312:return frame,address-FRAME
        need(ARC<=address and address+4<=ARC+92,'ExecuteSync owned frame/archive word');return archive,address-ARC
    def word(address):
        memory,i=owned(address);blob=bytes(memory[i:i+4]);reads.append(dict(pc=hex(pc),address=address,bytes=4,hex=blob.hex()))
        return int.from_bytes(blob,'little')
    def store(address,value,target=None,events=None):
        memory,i=owned(address);event=dict(pc=hex(pc if target is None else target),address=address,bytes=4,
            before=bytes(memory[i:i+4]).hex(),value=value)
        (stores if events is None else events).append(event);struct.pack_into('<I',memory,i,value)
    def model(target):
        native=list(r);frame_before=frame.hex();archive_before=archive.hex();writes=[]
        if target==TRANSLATE:
            need(native[:2]==[FILE,4],'Translate modeled actual file/command ABI')
            store(FILE+20,result,target,writes);value=result
        elif target==RELEASE:
            need(native[:2]==[FILE,result],'Release modeled actual file/translated-result ABI')
            error=result if release_error is None else release_error
            for address,value in((ARC+36,0),(FILE,0),(FILE+4,0),(FILE+12,0),(FILE+20,error)):
                store(address,value,target,writes)
            value=void_value
        else:
            need(target==NEXT and native[0]==ARC,'Next modeled actual archive ABI')
            store(ARC+28,3,target,writes);value=0
        r[:]=B.boundary_regs(r,value,clobber)
        services.append(dict(pc=hex(target),entry=native,returned=list(r),result_r0=value,
            frame_before=frame_before,frame_after=frame.hex(),archive_before=archive_before,archive_after=archive.hex(),
            writes=writes,model_scope=SCOPES[target]))
    at(ENTRY);r[13]-=8
    for j,index in enumerate((4,14)):store(r[13]+4*j,r[index])
    at(0x20D7748);r[4]=r[0]
    at(0x20D774C);r[1]=word(r[4]+16)
    at(0x20D7750);r[14]=0x20D7754;model(TRANSLATE)
    at(0x20D7754);r[1]=r[0]
    at(0x20D7758);r[0]=r[4]
    at(0x20D775C);r[14]=0x20D7760;model(RELEASE)
    at(0x20D7760);r[0]=word(r[4]+8)
    at(0x20D7764);r[14]=0x20D7768;model(NEXT)
    at(0x20D7768);r[15]=B.cmp(r[0],0,r[15])
    at(0x20D776C);need(r[15]&(1<<30),'ExecuteSync NextNULL, Async body excluded')
    at(0x20D7774);r[0]=word(r[4]+20)
    at(0x20D7778);r[15]=B.cmp(r[0],0,r[15])
    at(0x20D777C)
    if r[15]&(1<<30):r[0]=1
    at(0x20D7780)
    if not r[15]&(1<<30):r[0]=0
    at(0x20D7784);r[4]=word(r[13]);target=word(r[13]+4);r[13]+=8
    need(target==RETURN and(len(flow),len(stores),len(reads))==(16,2,5),'ExecuteSync finite source extent and original ARM return')
    return dict(flow=flow,stores=stores,reads=reads,services=services,returned=r,frame_after=frame.hex(),archive_after=archive.hex(),
        native_peak=8,steps=20,unique_native_starts=16,stop=hex(RETURN))


def initial_memory(f,bodies,fill):
    frame,archive=check_fixture(f)
    need(type(fill)is int and fill in(0xA5,0x39)and set(bodies)=={ENTRY},'ExecuteSync finite code/fill domain')
    body=bodies[ENTRY];need(type(body)is bytes and len(body)==68 and sha(body)==BODY_SHA,'ExecuteSync exact68 native bytes')
    before=bytearray(bytes([fill])*SIZE);before[ENTRY-BASE:END-BASE]=body
    before[FRAME-BASE:FRAME-BASE+312]=frame;before[ARC-BASE:ARC-BASE+92]=archive
    # Original Send POP fetch gate, stopped before executing it.
    before[RETURN-BASE:RETURN-BASE+4]=struct.pack('<I',0xE8BD80F8)
    for target in(TRANSLATE,RELEASE,NEXT):before[target-BASE:target-BASE+4]=struct.pack('<I',0xE1A00000)
    return bytes(before)


def read_allowed(pc,address,n):
    return n==4 and address%4==0 and({0x20D774C:FILE+16,0x20D7760:FILE+8,0x20D7774:FILE+20}.get(pc)==address or
        (pc==0x20D7784 and address in(FRAME,FRAME+4)))


def write_allowed(pc,address,n):
    return n==4 and address%4==0 and pc==ENTRY and address in(FRAME,FRAME+4)


def run(f,bodies,result=0,void_value=0,clobber=False,release_error=None,observe=True,fill=0xA5):
    """Collect native wrapper and declared field models; save raw before evaluating."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
    p=policy(result,void_value,clobber,release_error);need(type(observe)is bool,'ExecuteSync strict observer')
    need(unicorn.__version__=='2.1.4','ExecuteSync qualified Unicorn2.1.4')
    before=initial_memory(f,bodies,fill);u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    need(u.ctl_get_cpu_model()==17,'ExecuteSync qualified CPU17 instruction semantics')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    word=lambda address:int.from_bytes(read(address,4),'little')
    entry=regs();flow=[];stores=[];reads=[];services=[];seen=set();steps=0;peak=0;returned=None;fault=None
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=64,'ExecuteSync bounded instruction count')
        if pc==RETURN:returned=regs();u.emu_stop();return
        if pc in(TRANSLATE,RELEASE,NEXT):
            native=regs();lr=native[14]
            need(n==4 and native[13]==FRAME and not native[15]&32,'ExecuteSync model ARM/SP ABI')
            need(pc==(TRANSLATE,RELEASE,NEXT)[len(services)]and lr=={TRANSLATE:0x20D7754,RELEASE:0x20D7760,NEXT:0x20D7768}[pc],
                 'ExecuteSync model sequence and actual native LR')
            frame_before=read(FRAME,312).hex();archive_before=read(ARC,92).hex();writes=[]
            def put(address,value):
                need(address in{TRANSLATE:{FILE+20},RELEASE:{ARC+36,FILE,FILE+4,FILE+12,FILE+20},NEXT:{ARC+28}}[pc],
                     'ExecuteSync declared model field owner')
                writes.append(dict(pc=hex(pc),address=address,bytes=4,before=read(address,4).hex(),value=value))
                u.mem_write(address,struct.pack('<I',value))
            if pc==TRANSLATE:
                need(native[:2]==[FILE,4]and word(FILE+16)==4 and word(FILE+20)==2,'ExecuteSync actual Translate command/error prestate')
                put(FILE+20,result);value=result
            elif pc==RELEASE:
                need(native[:2]==[FILE,result]and word(FILE+20)==result and
                     [word(FILE+off)for off in(0,4,8,12,16)]==[ARC+32,0,ARC,0x45,4]and word(ARC+36)==FILE,
                     'ExecuteSync actual Release result/linked synchronous file')
                put(ARC+36,word(FILE+4));put(FILE,0);put(FILE+4,0);put(FILE+12,word(FILE+12)&~0x4F)
                put(FILE+20,result if release_error is None else release_error);value=void_value
            else:
                need(native[0]==ARC and word(ARC+36)==0 and word(ARC+28)==0x13,'ExecuteSync actual Next archive/empty list')
                put(ARC+28,word(ARC+28)&~16);value=0
            new=B.boundary_regs(native,value,clobber)
            for reg,val in zip(REGS,new):u.reg_write(reg,val)
            services.append(dict(pc=hex(pc),entry=native,returned=regs(),result_r0=value,frame_before=frame_before,
                frame_after=read(FRAME,312).hex(),archive_before=archive_before,archive_after=read(ARC,92).hex(),writes=writes,model_scope=SCOPES[pc]))
            u.reg_write(UC_ARM_REG_PC,lr);return
        need(ENTRY<=pc<END and(pc-ENTRY)%4==0 and n==4 and not regs()[15]&32,'ExecuteSync native ARM whitelist')
        need(read(pc,4)==bodies[ENTRY][pc-ENTRY:pc-ENTRY+4],'ExecuteSync live native code identity')
        seen.add(pc);peak=max(peak,SP-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def write(uc,access,address,n,val,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'ExecuteSync native write owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=val))
    def load_word(uc,access,address,n,val,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'ExecuteSync native read owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,load_word)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=64)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=p,observe=observe,fill=fill,entry=entry,returned=returned,flow=flow,stores=stores,reads=reads,
        services=services,steps=steps,native_peak=peak,observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,
        halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),frame_after=read(FRAME,312).hex(),archive_after=read(ARC,92).hex(),
        guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    r=row;f=r['fixture'];check_fixture(f);need(type(r['observe'])is bool,'ExecuteSync strict observer receipt')
    p=r['policy'];need(wire(p)==wire(policy(**p)),'ExecuteSync exact policy fields')
    want=predict(f,**p);before=initial_memory(f,bodies,r['fill']);after=bytearray(before)
    after[FRAME-BASE:FRAME-BASE+312]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected=dict(entry=f['entry'],returned=want['returned'],services=want['services'],steps=20,native_peak=8,
        observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),
        frame_after=want['frame_after'],archive_after=want['archive_after'],guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),
        guard_after=before[FRAME-56-BASE:FRAME-BASE].hex(),before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for key in('flow','stores','reads'):expected[key]=want[key]if r['observe']else[]
    for key,value in expected.items():need(wire(r[key])==wire(value),'ExecuteSync source-derived '+key)
    return True
