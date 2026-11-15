"""Finite native Release/IRQ oracle; empty Wakeup remains a value-only model.

The stale-error control is a declared input projection, not natural Translate state.
Release is void. Its residual R0 must not be interpreted as filesystem success.
"""
from pathlib import Path
import importlib.util,json,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


E=load('release_qualified_execute_helpers',Path(__file__).with_name('fs_exec_sync_bench.py'))
S,B,need,sha=E.S,E.B,E.need,E.sha
need(sha(Path(E.__file__).read_bytes())=='e10f36d1cb56cd6af303256ec5e20601a47ede7dcf557eb781fbf480de3c848f','Release qualified ExecuteSync helper drift')
ENTRY,END,RETURN,WAKE,DISABLE,RESTORE=0x20D6864,0x20D68C0,0x20D7760,0x20D1ECC,S.DISABLE,S.RESTORE
TOP,FILE,ARC,ID,PATH=E.TOP,E.FILE,E.ARC,E.ID,E.PATH
SP,FRAME,BASE,SIZE,REGS=TOP-312,TOP-328,E.BASE,E.SIZE,E.REGS
ARCHIVE=E.ARCHIVE
BODY_SHA='658daf608846bdeca5f8d48b8b0ea7d46280ebcd2ef783fce8b5f9e12735f568'
wire=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'))
MODEL_SCOPE='Empty queue value-only model; no native Wakeup/IRQ/thread/scheduler effects or RAM writes'


def check_fixture(f):
    value=f['translated_result'];r=f['entry']
    need(type(value)is int and value in(0,1)and B.u32s(r),'Release actual unsigned32 entry and strict translated result')
    need(r==[FILE,value,0x2000001F,FILE+48,FILE,0,FILE,16,FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
             0,SP,RETURN,0x2000001F],'Release actual ExecuteSync caller I0 entry')
    need(type(f['frame'])is type(f['archive_before'])is str,'Release exact hex preimages')
    frame,archive=bytes.fromhex(f['frame']),bytes.fromhex(f['archive_before'])
    need(len(frame)==328 and archive==ARCHIVE,'Release frame328 and actual isolated running linked archive92')
    for off,x in((0,ARC+32),(4,0),(8,ARC),(12,0x45),(16,4),(20,value),(24,0),(28,0),
                  (48,ARC),(52,0),(56,0),(60,PATH),(64,0),(68,ID)):
        need(struct.unpack_from('<I',frame,FILE-FRAME+off)[0]==x,'Release actual linked file command4/translated error/empty Wakeup queue')
    return frame,archive


def policy(wake_value,clobber,stale_error):
    need(type(wake_value)is int and wake_value in(0,0xFFFFFFFF)and type(clobber)is type(stale_error)is bool,
         'Release strict finite void-Wakeup/clobber/stale-input policy')
    return dict(wake_value=wake_value,clobber=clobber,stale_error=stale_error)


def input_frame(f,stale_error):
    frame,archive=check_fixture(f);frame=bytearray(frame)
    need(type(stale_error)is bool,'Release strict input projection')
    if stale_error:struct.pack_into('<I',frame,FILE-FRAME+20,2)
    return frame,bytearray(archive)


def predict(f,wake_value=0,clobber=False,stale_error=False):
    policy(wake_value,clobber,stale_error);frame,archive=input_frame(f,stale_error);before=frame.hex();r=list(f['entry'])
    flow=[];stores=[];reads=[];services=[];pc=ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def owned(address):
        if FRAME<=address and address+4<=FRAME+328:return frame,address-FRAME
        need(ARC<=address and address+4<=ARC+92,'Release source word owner');return archive,address-ARC
    def word(address):
        memory,i=owned(address);blob=bytes(memory[i:i+4]);reads.append(dict(pc=hex(pc),address=address,bytes=4,hex=blob.hex()))
        return int.from_bytes(blob,'little')
    def store(address,value):
        memory,i=owned(address);stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(memory[i:i+4]).hex(),value=value))
        struct.pack_into('<I',memory,i,value)
    def call(address,target):
        at(address);r[14]=address+4;S.native_irq(r,at,target)
    at(ENTRY);r[13]-=16
    for j,index in enumerate((4,5,6,14)):store(r[13]+4*j,r[index])
    at(0x20D6868);r[5]=r[0]
    at(0x20D686C);r[4]=r[1]
    call(0x20D6870,DISABLE)
    at(0x20D6874);r[1]=word(r[5])
    at(0x20D6878);r[6]=r[0]
    at(0x20D687C);r[0]=word(r[5]+4)
    at(0x20D6880);r[15]=B.cmp(r[1],0,r[15])
    at(0x20D6884);need(not r[15]&(1<<30),'Release prev nonNULL source sentinel');store(r[1]+4,r[0])
    at(0x20D6888);r[15]=B.cmp(r[0],0,r[15])
    at(0x20D688C);need(r[15]&(1<<30),'Release nextNULL false STRNE hook')
    at(0x20D6890);r[0]=0
    at(0x20D6894);store(r[5],r[0])
    at(0x20D6898);store(r[5]+4,r[0])
    at(0x20D689C);r[1]=word(r[5]+12)
    at(0x20D68A0);r[0]=r[5]+24
    at(0x20D68A4);r[1]&=~0x4F
    at(0x20D68A8);store(r[5]+12,r[1])
    at(0x20D68AC);store(r[5]+20,r[4])
    at(0x20D68B0);r[14]=0x20D68B4;native=list(r);frame_before=frame.hex();archive_before=archive.hex()
    need(native[0]==FILE+24 and frame[FILE-FRAME+24:FILE-FRAME+32]==bytes(8),'Release empty Wakeup source ABI/preimage')
    r=B.boundary_regs(r,wake_value,clobber)
    services.append(dict(pc=hex(WAKE),entry=native,returned=list(r),result_r0=wake_value,frame_before=frame_before,
        frame_after=frame.hex(),archive_before=archive_before,archive_after=archive.hex(),writes=[],model_scope=MODEL_SCOPE))
    at(0x20D68B4);r[0]=r[6]
    call(0x20D68B8,RESTORE)
    at(0x20D68BC);saved=[word(r[13]+4*j)for j in range(4)];r[4:7]=saved[:3];r[13]+=16
    need(saved[-1]==RETURN and(len(flow),len(stores),len(reads))==(34,9,7),'Release original return and finite source transcript')
    return dict(flow=flow,stores=stores,reads=reads,services=services,returned=r,frame_before=before,frame_after=frame.hex(),
        archive_after=archive.hex(),native_peak=16,steps=36,unique_native_starts=34,stop=hex(RETURN))


BODIES={ENTRY:(92,BODY_SHA),DISABLE:S.BODIES[DISABLE],RESTORE:S.BODIES[RESTORE]}


def initial_memory(f,bodies,fill,stale_error):
    frame,archive=input_frame(f,stale_error)
    need(type(fill)is int and fill in(0xA5,0x39)and set(bodies)==set(BODIES),'Release finite code/fill inputs')
    before=bytearray(bytes([fill])*SIZE)
    for address,(n,digest)in BODIES.items():
        body=bodies[address];need(type(body)is bytes and len(body)==n and sha(body)==digest,'Release exact qualified native component')
        before[address-BASE:address-BASE+n]=body
    before[FRAME-BASE:FRAME-BASE+328]=frame;before[ARC-BASE:ARC-BASE+92]=archive
    # Original ExecuteSync LDR fetch gate, stopped before execution.
    before[RETURN-BASE:RETURN-BASE+4]=struct.pack('<I',0xE5940008)
    before[WAKE-BASE:WAKE-BASE+4]=struct.pack('<I',0xE1A00000)
    return bytes(before)


def read_allowed(pc,address,n):
    return n==4 and address%4==0 and({0x20D6874:FILE,0x20D687C:FILE+4,0x20D689C:FILE+12}.get(pc)==address or
        (pc==0x20D68BC and FRAME<=address<FRAME+16))


def write_allowed(pc,address,n):
    return n==4 and address%4==0 and({0x20D6884:ARC+36,0x20D6894:FILE,0x20D6898:FILE+4,0x20D68A8:FILE+12,0x20D68AC:FILE+20}.get(pc)==address or
        (pc==ENTRY and FRAME<=address<FRAME+16))


def run(f,bodies,wake_value=0,clobber=False,stale_error=False,observe=True,fill=0xA5):
    """Collect one Release call, retaining the declared initial projection separately."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
    p=policy(wake_value,clobber,stale_error);need(type(observe)is bool,'Release strict observer')
    need(unicorn.__version__=='2.1.4','Release qualified Unicorn2.1.4')
    before=initial_memory(f,bodies,fill,stale_error);u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    need(u.ctl_get_cpu_model()==17,'Release qualified CPU17 instruction semantics')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();frame_before=read(FRAME,328).hex();flow=[];stores=[];reads=[];services=[];seen=set();steps=0;peak=0;returned=None;fault=None
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=80,'Release bounded instruction count')
        if pc==RETURN:returned=regs();u.emu_stop();return
        if pc==WAKE:
            native=regs();lr=native[14]
            need(native[0]==FILE+24 and native[13]==FRAME and lr==0x20D68B4 and n==4 and not native[15]&32 and native[15]&128,
                 'Release actual empty Wakeup queue/SP/LR/ARM/IRQ-disabled ABI')
            need(read(FILE+24,8)==bytes(8)and struct.unpack('<6I',read(FILE,24))==(0,0,ARC,0,4,f['translated_result'])and
                 struct.unpack('<3I',read(ARC+28,12))==(0x13,0,0),'Release native completion fields and empty queue before modeled Wakeup')
            native_frame=read(FRAME,328).hex();archive=read(ARC,92).hex();new=B.boundary_regs(native,wake_value,clobber)
            for reg,value in zip(REGS,new):u.reg_write(reg,value)
            services.append(dict(pc=hex(pc),entry=native,returned=regs(),result_r0=wake_value,frame_before=native_frame,
                frame_after=read(FRAME,328).hex(),archive_before=archive,archive_after=read(ARC,92).hex(),writes=[],model_scope=MODEL_SCOPE))
            u.reg_write(UC_ARM_REG_PC,lr);return
        selected=next(((a,b)for a,b in bodies.items()if a<=pc<a+len(b)),None)
        need(selected is not None and(pc-selected[0])%4==0 and n==4 and not regs()[15]&32,'Release native ARM component whitelist')
        a,body=selected;need(read(pc,4)==body[pc-a:pc-a+4],'Release live native instruction identity')
        seen.add(pc);peak=max(peak,SP-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'Release native write PC/word/stack owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    def load_word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'Release native read PC/word/stack owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,load_word)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=80)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=p,observe=observe,fill=fill,entry=entry,returned=returned,flow=flow,stores=stores,reads=reads,services=services,
        steps=steps,native_peak=peak,observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),
        stop=hex(RETURN),frame_before=frame_before,frame_after=read(FRAME,328).hex(),archive_after=read(ARC,92).hex(),
        guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    r=row;f=r['fixture'];check_fixture(f);need(type(r['observe'])is bool,'Release strict observer receipt')
    p=r['policy'];need(wire(p)==wire(policy(**p)),'Release exact policy fields')
    want=predict(f,**p);before=initial_memory(f,bodies,r['fill'],p['stale_error']);after=bytearray(before)
    after[FRAME-BASE:FRAME-BASE+328]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected=dict(entry=f['entry'],returned=want['returned'],services=want['services'],steps=36,native_peak=16,
        observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),
        frame_before=want['frame_before'],frame_after=want['frame_after'],archive_after=want['archive_after'],
        guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=before[FRAME-56-BASE:FRAME-BASE].hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for key in('flow','stores','reads'):expected[key]=want[key]if r['observe']else[]
    for key,value in expected.items():need(wire(r[key])==wire(value),'Release source-derived '+key)
    return True
