"""Finite empty-queue OS_WakeupThread oracle; native IRQ leaves, no scheduler model.

The parent frame and guard are copied from authenticated Release observations.
Only the new 24 lower guard bytes are declared fill, not historical evidence.
"""
from pathlib import Path
import struct
import importlib.util


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


W=load('wakeup_qualified_release_helpers',Path(__file__).with_name('fs_release_bench.py'))
S,B,need,sha=W.S,W.B,W.need,W.sha
need(sha(Path(W.__file__).read_bytes())=='d70f834dc38c21cd4d460556a1552fae6107f7f4aa41e209d72fd6a1f4f9837a','Wakeup qualified Release helper drift')
ENTRY,END,RETURN,DISABLE,RESTORE=0x20D1ECC,0x20D1F34,0x20D68B4,S.DISABLE,S.RESTORE
TOP,FILE,ARC,ID,PATH=W.TOP,W.FILE,W.ARC,W.ID,W.PATH
SP,FRAME,BASE,SIZE,REGS=TOP-328,TOP-352,W.BASE,W.SIZE,W.REGS
QUEUE=FILE+24
BODY_SHA='25c7d621d6b4d855be6828b9ec8d98162df8ecdda5a22db405caf344aa4102db'
archive=bytearray(W.ARCHIVE);struct.pack_into('<I',archive,36,0);ARCHIVE=bytes(archive);del archive
BODIES={ENTRY:(104,BODY_SHA),DISABLE:S.BODIES[DISABLE],RESTORE:S.BODIES[RESTORE]}
wire=W.wire


def check_fixture(f):
    value=f['translated_result'];r=f['entry']
    need(type(value)is int and value in(0,1)and B.u32s(r),'Wakeup strict translated result and entry16 unsigned32')
    need(r==[QUEUE,0,0x2000001F,FILE+48,value,FILE,0,16,FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
             0,SP,RETURN,0x6000009F],'Wakeup actual Release empty-queue I1 input')
    need(type(f['frame'])is type(f['archive_before'])is type(f['captured_parent_guard56'])is str,'Wakeup hex preimages')
    frame,archive,guard=map(bytes.fromhex,(f['frame'],f['archive_before'],f['captured_parent_guard56']))
    need(len(frame)==352 and archive==ARCHIVE and len(guard)==56,'Wakeup frame352/archive92/parent guard56')
    need(frame[:24]==guard[-24:],'Wakeup new stack24 comes from actual parent guard tail')
    for off,x in((0,0),(4,0),(8,ARC),(12,0),(16,4),(20,value),(24,0),(28,0),
                  (48,ARC),(52,0),(56,0),(60,PATH),(64,0),(68,ID)):
        need(struct.unpack_from('<I',frame,FILE-FRAME+off)[0]==x,'Wakeup post-Release file/ARG/empty queue preimage')
    return frame,archive,guard


def guard_before(f,fill):
    _,_,guard=check_fixture(f)
    need(type(fill)is int and fill in(0xA5,0x39),'Wakeup strict declared lower guard fill')
    return bytes([fill])*24+guard[:32]


def predict(f):
    frame,archive,_=check_fixture(f);frame=bytearray(frame);r=list(f['entry']);flow=[];stores=[];reads=[];pc=ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def word(address):
        need(FRAME<=address and address+4<=TOP,'Wakeup source word belongs to stack frame')
        blob=bytes(frame[address-FRAME:address-FRAME+4]);reads.append(dict(pc=hex(pc),address=address,bytes=4,hex=blob.hex()))
        return int.from_bytes(blob,'little')
    def store(address,value):
        i=address-FRAME;stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(frame[i:i+4]).hex(),value=value))
        struct.pack_into('<I',frame,i,value)
    def call(address,target):
        at(address);r[14]=address+4;S.native_irq(r,at,target)
    at(ENTRY);r[13]-=24
    for j,index in enumerate((3,4,5,6,7,14)):store(r[13]+4*j,r[index])
    at(0x20D1ED0);r[7]=r[0]
    call(0x20D1ED4,DISABLE)
    at(0x20D1ED8);r[1]=word(r[7])
    at(0x20D1EDC);r[6]=r[0]
    at(0x20D1EE0);r[15]=B.cmp(r[1],0,r[15])
    at(0x20D1EE4);need(r[15]&(1<<30),'Wakeup empty queue branch, no thread or scheduler activation')
    at(0x20D1F28);r[0]=r[6]
    call(0x20D1F2C,RESTORE)
    at(0x20D1F30);saved=[word(r[13]+4*j)for j in range(6)];r[3:8]=saved[:5];r[13]+=24
    need(saved[-1]==RETURN and(len(flow),len(stores),len(reads))==(21,6,7),'Wakeup original return and finite native transcript')
    return dict(flow=flow,stores=stores,reads=reads,services=[],returned=r,frame_after=frame.hex(),
        archive_after=archive.hex(),native_peak=24,steps=22,unique_native_starts=21,stop=hex(RETURN))


def initial_memory(f,bodies,fill):
    frame,archive,_=check_fixture(f);guard=guard_before(f,fill)
    need(set(bodies)==set(BODIES),'Wakeup exact three native components')
    before=bytearray(bytes([fill])*SIZE)
    for address,(n,digest)in BODIES.items():
        body=bodies[address];need(type(body)is bytes and len(body)==n and sha(body)==digest,'Wakeup qualified native code identity')
        before[address-BASE:address-BASE+n]=body
    before[FRAME-BASE:TOP-BASE]=frame;before[ARC-BASE:ARC-BASE+92]=archive
    before[FRAME-56-BASE:FRAME-BASE]=guard
    # Actual Release MOV r0,r6; fetch gate only, stopped before execution.
    before[RETURN-BASE:RETURN-BASE+4]=bytes.fromhex('0600a0e1')
    return bytes(before)


def read_allowed(pc,address,n):
    return n==4 and address%4==0 and((pc==0x20D1ED8 and address==QUEUE)or
        (pc==0x20D1F30 and FRAME<=address<FRAME+24))


def write_allowed(pc,address,n):
    return n==4 and address%4==0 and pc==ENTRY and FRAME<=address<FRAME+24


def run(f,bodies,observe=True,fill=0xA5):
    """Observe unmodified installed code; no host service or in-guest state writes."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
    need(type(observe)is bool and unicorn.__version__=='2.1.4','Wakeup strict observer and qualified Unicorn2.1.4')
    before=initial_memory(f,bodies,fill);u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    need(u.ctl_get_cpu_model()==17,'Wakeup qualified CPU17 instruction semantics')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();flow=[];stores=[];reads=[];seen=set();steps=0;peak=0;returned=None;fault=None
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=40,'Wakeup bounded instruction count')
        if pc==RETURN:returned=regs();u.emu_stop();return
        selected=next(((a,b)for a,b in bodies.items()if a<=pc<a+len(b)),None)
        need(selected is not None and(pc-selected[0])%4==0 and n==4 and not regs()[15]&32,'Wakeup native ARM whitelist')
        a,body=selected;need(read(pc,4)==body[pc-a:pc-a+4],'Wakeup live instruction identity')
        seen.add(pc);peak=max(peak,SP-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'Wakeup native write PC/word/stack owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    def load_word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'Wakeup native read PC/word/stack owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,load_word)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=40)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,observe=observe,fill=fill,entry=entry,returned=returned,flow=flow,stores=stores,reads=reads,services=[],
        steps=steps,native_peak=peak,observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,halt_regs=regs(),
        halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),frame_before=before[FRAME-BASE:TOP-BASE].hex(),
        frame_after=read(FRAME,352).hex(),archive_after=read(ARC,92).hex(),guard_before=guard_before(f,fill).hex(),
        guard_after=read(FRAME-56,56).hex(),before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    r=row;f=r['fixture'];check_fixture(f);need(type(r['observe'])is bool,'Wakeup strict observer receipt')
    want=predict(f);before=initial_memory(f,bodies,r['fill']);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after'])
    expected=dict(entry=f['entry'],returned=want['returned'],services=[],steps=22,native_peak=24,
        observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,halt_regs=want['returned'],
        halt_pc=hex(RETURN),stop=hex(RETURN),frame_before=f['frame'],frame_after=want['frame_after'],archive_after=f['archive_before'],
        guard_before=guard_before(f,r['fill']).hex(),guard_after=guard_before(f,r['fill']).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for key in('flow','stores','reads'):expected[key]=want[key]if r['observe']else[]
    for key,value in expected.items():need(wire(r[key])==wire(value),'Wakeup source-derived '+key)
    return True
