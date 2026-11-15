"""Seven original ExecuteSync instructions from an observed native NextNULL return.

No modeled callee or host guest-state mutation. Original Send POP is a stop gate.
"""
from pathlib import Path
import importlib.util,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


N=load('sync_join_qualified_next',Path(__file__).with_name('fs_next_bench.py'))
need,sha=N.need,N.sha
need(sha(Path(N.__file__).read_bytes())=='60b415a1dd98a1f29c48f2aadbc35612bf8ca0db81bf61aaba315c68630ecca5','Join qualified parent bench drift')
TOP,FILE,ARC,BASE,SIZE,REGS=N.TOP,N.FILE,N.ARC,N.BASE,N.SIZE,N.REGS
SP,FRAME,ENTRY,END,RETURN=TOP-312,TOP-416,0x20D7768,0x20D7788,0x20D7928
PCS=(ENTRY,0x20D776C,0x20D7774,0x20D7778,0x20D777C,0x20D7780,0x20D7784)
TAIL_SHA='3b188a965b586c94c24e280668f3906c9e22c9f1a70f8ef5b9bed035008f7f87'
GATE_SHA='8e0f1d53fab1ae8a8a53c4fbaa1c4b34b5fe18c8cb9857fb1dfacf5292204134'
BODIES={**N.BODIES,ENTRY:(32,TAIL_SHA),RETURN:(4,GATE_SHA)}
wire=N.wire


def check_fixture(f):
    r=f['entry'];need(N.B.u32s(r)and r==[0,0x6000009F,0x6000001F,FILE+48,FILE,0,FILE,16,FILE,
        0x99999902,0xAAAAAA03,0xBBBBBB04,0,SP,0x20D76A4,0x6000001F],'Join actual native NextNULL full16, not old modeled volatiles')
    need(all(type(f[k])is str for k in('frame','guard','archive_before','parent_whole_ram_sha256')),
        'Join exact byte/hash strings')
    frame,guard,archive=(bytes.fromhex(f[k])for k in('frame','guard','archive_before'))
    need((len(frame),len(guard),len(archive))==(416,56,92),'Join actual parent frame416/guard56/archive92')
    value=f['translated_result'];need(type(value)is int and value in(0,1),'Join finite stored error type')
    need(struct.unpack_from('<I',frame,FILE-FRAME+20)[0]==value and
        struct.unpack_from('<I',frame,FILE-FRAME+8)[0]==ARC and
        struct.unpack_from('<2I',frame,104)==(ARC,RETURN),'Join stored error/actual archive pointer/saved POP pair')
    return frame,guard,archive


def predict(f):
    frame,guard,archive=check_fixture(f);r=list(f['entry']);flow=[];reads=[];pc=ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def word(address):
        need(FRAME<=address and address+4<=TOP,'Join source read owner');offset=address-FRAME
        blob=frame[offset:offset+4];reads.append(dict(pc=hex(pc),address=address,bytes=4,hex=blob.hex()));return int.from_bytes(blob,'little')
    at(ENTRY);r[15]=N.B.cmp(r[0],0,r[15])
    at(0x20D776C);need(r[15]&(1<<30),'Join NextNULL branch, no Async')
    at(0x20D7774);r[0]=word(r[4]+20)
    at(0x20D7778);r[15]=N.B.cmp(r[0],0,r[15])
    at(0x20D777C)
    if r[15]&(1<<30):r[0]=1
    at(0x20D7780)
    if not r[15]&(1<<30):r[0]=0
    at(0x20D7784);saved=word(r[13]);target=word(r[13]+4);r[4]=saved;r[13]+=8
    need(target==RETURN and len(flow)==7 and len(reads)==3,'Join original POP and finite read transcript')
    return dict(flow=flow,reads=reads,stores=[],services=[],returned=r,steps=8,native_peak=0,
                frame_before=f['frame'],frame_after=f['frame'],archive_before=f['archive_before'],archive_after=f['archive_before'])


def parent_memory(f,bodies):
    check_fixture(f);need(set(bodies)==set(BODIES),'Join exact retained and new code/gate set')
    for address,(n,digest)in BODIES.items():
        need(type(bodies[address])is bytes and len(bodies[address])==n and sha(bodies[address])==digest,'Join authenticated code component')
    old={a:bodies[a]for a in N.BODIES}
    image=bytearray(N.initial_memory(f['parent_fixture'],old,0xA5,False))
    image[FRAME-BASE:TOP-BASE]=bytes.fromhex(f['frame'])
    image[ARC-BASE:ARC-BASE+92]=bytes.fromhex(f['archive_before'])
    need(sha(bytes(image))==f['parent_whole_ram_sha256'],'Join reconstruction equals actual Next whole-RAM digest')
    need(image[FRAME-56-BASE:FRAME-BASE]==bytes.fromhex(f['guard']),'Join observed guard matches parent image')
    return bytes(image)


def initial_memory(f,bodies):
    image=bytearray(parent_memory(f,bodies))
    need(image[ENTRY-BASE:ENTRY-BASE+4]==bodies[ENTRY][:4],'Join retains the original parent CMP gate')
    image[ENTRY-BASE:END-BASE]=bodies[ENTRY];image[RETURN-BASE:RETURN-BASE+4]=bodies[RETURN]
    return bytes(image)


def run(f,bodies,observe=True):
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
    need(type(observe)is bool and unicorn.__version__=='2.1.4','Join strict observer and qualified Unicorn2.1.4')
    before=initial_memory(f,bodies);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Join qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();flow=[];reads=[];seen=set();steps=0;returned=None;fault=None
    def step(uc,pc,n,_):
        nonlocal steps,returned
        steps+=1;need(steps<=16,'Join bounded instruction count')
        if pc==RETURN:
            need(read(pc,4)==bodies[RETURN],'Join original Send stopped gate');returned=regs();u.emu_stop();return
        need(pc in PCS and n==4 and not regs()[15]&32 and read(pc,4)==bodies[ENTRY][pc-ENTRY:pc-ENTRY+4],
             'Join original allowed native instruction, no Async')
        seen.add(pc)
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def load_word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC)
        need(n==4 and((pc==0x20D7774 and address==FILE+20)or(pc==0x20D7784 and address in(SP,SP+4))),
             'Join native read PC/word owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    def write(uc,access,address,n,value,_):
        raise ValueError('Join forbids every guest write')
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_READ,load_word);u.hook_add(UC_HOOK_MEM_WRITE,write)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=16)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,observe=observe,entry=entry,returned=returned,flow=flow,reads=reads,stores=[],services=[],
        steps=steps,native_peak=0,observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,
        halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),
        frame_before=before[FRAME-BASE:TOP-BASE].hex(),frame_after=read(FRAME,416).hex(),
        archive_before=before[ARC-BASE:ARC-BASE+92].hex(),archive_after=read(ARC,92).hex(),
        guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    f=row['fixture'];want=predict(f);need(type(row['observe'])is bool,'Join strict observation')
    before=initial_memory(f,bodies)
    expected=dict(entry=f['entry'],returned=want['returned'],stores=[],services=[],steps=8,native_peak=0,
        observed_pcs=sorted(PCS),cpu_model=17,fault=None,halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),
        frame_before=f['frame'],frame_after=f['frame'],archive_before=f['archive_before'],archive_after=f['archive_before'],
        guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=before[FRAME-56-BASE:FRAME-BASE].hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(before))
    for key in('flow','reads'):expected[key]=want[key]if row['observe']else[]
    for key,value in expected.items():need(wire(row[key])==wire(value),'Join source-derived '+key)
    return True
