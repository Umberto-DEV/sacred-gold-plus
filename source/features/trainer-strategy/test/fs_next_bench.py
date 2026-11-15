"""Finite empty-archive Next oracle from the observed Release/Wakeup checkpoint.

not_running is a declared initial archive-word projection, not a host action in
the guest. The parent408 captured bytes and live caller312 remain distinct.
"""
from pathlib import Path
import importlib.util,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


Q=load('next_qualified_release_wakeup',Path(__file__).with_name('fs_release_wakeup_bench.py'))
S,B,need,sha=Q.S,Q.B,Q.need,Q.sha
need(sha(Path(Q.__file__).read_bytes())=='686827668602b8fed70fd42c179edbf9e5180adae1703255eb9377d8f8c294e2','Next qualified parent bench drift')
ENTRY,NEXT,END,RETURN=0x20D7760,0x20D749C,0x20D76B0,0x20D7768
DISABLE,RESTORE=S.DISABLE,S.RESTORE
TOP,FILE,ARC,ID,PATH=Q.TOP,Q.FILE,Q.ARC,Q.ID,Q.PATH
SP,FRAME,CAPTURED_BASE,BASE,SIZE,REGS=TOP-312,TOP-416,TOP-408,Q.BASE,Q.SIZE,Q.REGS
ARCHIVE=Q.W.ARCHIVE
BODY_SHA='d3785eb030614f3050cb9ef747e3a173e534c40ef5ffa3d75c95acd6fa778e9c'
BRIDGE_SHA='b28aff89430ec51b1e3f555180a3bd25dfde0b309462f6d3994bf77a52a0afb0'
BODIES={**Q.BODIES,NEXT:(532,BODY_SHA),ENTRY:(8,BRIDGE_SHA)}
EXECUTED_BODIES={a:BODIES[a]for a in(NEXT,DISABLE,RESTORE,ENTRY)}
wire=Q.wire


def check_fixture(f):
    value=f['translated_result'];r=f['entry']
    need(type(value)is int and value in(0,1)and B.u32s(r),'Next typed actual checkpoint16/result')
    need(r==[0x80,0x6000009F,0x6000001F,FILE+48,FILE,0,FILE,16,FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
        0,SP,0x20D68BC,0x6000001F],'Next actual native Release/Wakeup return checkpoint, I0')
    need(type(f['captured408'])is type(f['archive_before'])is type(f['parent_whole_ram_sha256'])is str,'Next exact captured byte/hash strings')
    captured=bytes.fromhex(f['captured408']);archive=bytes.fromhex(f['archive_before'])
    need(len(captured)==408 and archive==ARCHIVE and len(f['parent_whole_ram_sha256'])==64,'Next captured408/actual archive92/parent digest')
    for off,x in((0,0),(4,0),(8,ARC),(12,0),(16,4),(20,value),(24,0),(28,0),
                 (48,ARC),(52,0),(56,0),(60,PATH),(64,0),(68,ID)):
        need(struct.unpack_from('<I',captured,FILE-CAPTURED_BASE+off)[0]==x,'Next actual post-Release file and empty queue')
    need(struct.unpack_from('<8I',captured,64)==(FILE,0,16,0x20D68B4,FILE,0,FILE,ENTRY),'Next actual dead-stack32 preimages')
    return captured,archive


def guard_before(fill):
    need(type(fill)is int and fill in(0xA5,0x39),'Next strict localized new64 fill');return bytes([fill])*56


def input_state(f,not_running,fill):
    captured,archive=check_fixture(f);guard_before(fill);need(type(not_running)is bool,'Next strict not-running initial projection')
    frame=bytearray(bytes([fill])*8+captured);archive=bytearray(archive)
    if not_running:struct.pack_into('<I',archive,28,3)
    return frame,archive


def predict(f,not_running=False,fill=0xA5):
    frame,archive=input_state(f,not_running,fill);before=frame.hex();archive_before=archive.hex();r=list(f['entry'])
    flow=[];stores=[];reads=[];pc=ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def owned(address):
        if FRAME<=address and address+4<=TOP:return frame,address-FRAME
        need(ARC<=address and address+4<=ARC+92,'Next source word owner');return archive,address-ARC
    def word(address):
        memory,i=owned(address);blob=bytes(memory[i:i+4]);reads.append(dict(pc=hex(pc),address=address,bytes=4,hex=blob.hex()))
        return int.from_bytes(blob,'little')
    def store(address,value):
        memory,i=owned(address);stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(memory[i:i+4]).hex(),value=value))
        struct.pack_into('<I',memory,i,value)
    def call(address,target):
        at(address);r[14]=address+4;S.native_irq(r,at,target)
    def tst(address,index,mask):
        at(address);need(mask in(0x20,0x40,8,16,0x400),'Next finite TST masks')
        x=r[index]&mask;carry=0 if mask==0x400 else r[15]&(1<<29)
        r[15]=(r[15]&0x1FFFFFFF)|(x&0x80000000)|(int(x==0)<<30)|carry
    def bool_moves(ne_pc,eq_pc):
        at(ne_pc)
        if not r[15]&(1<<30):r[0]=1
        at(eq_pc)
        if r[15]&(1<<30):r[0]=0
    def cmp(address,index):at(address);r[15]=B.cmp(r[index],0,r[15])
    at(ENTRY);r[0]=word(r[4]+8)
    at(ENTRY+4);r[14]=RETURN;incoming=list(r)
    at(NEXT);r[13]-=32
    for j,index in enumerate((3,4,5,6,7,8,9,14)):store(r[13]+4*j,r[index])
    at(0x20D74A0);r[13]-=72
    at(0x20D74A4);r[6]=r[0]
    call(0x20D74A8,DISABLE)
    at(0x20D74AC);r[1]=word(r[6]+28)
    at(0x20D74B0);r[4]=r[0]
    tst(0x20D74B4,1,0x20);bool_moves(0x20D74B8,0x20D74BC);cmp(0x20D74C0,0)
    at(0x20D74C4);need(r[15]&(1<<30),'Next no cancellation branch')
    at(0x20D7530);r[0]=word(r[6]+28)
    tst(0x20D7534,0,0x40);bool_moves(0x20D7538,0x20D753C);cmp(0x20D7540,0);at(0x20D7544)
    at(0x20D7548);r[0]=word(r[6]+28)
    tst(0x20D754C,0,8);bool_moves(0x20D7550,0x20D7554);cmp(0x20D7558,0);at(0x20D755C)
    at(0x20D7560);r[5]=word(r[6]+36)
    cmp(0x20D7564,5);at(0x20D7568);need(r[15]&(1<<30),'Next actual empty list')
    at(0x20D7620);r[0]=word(r[6]+28)
    tst(0x20D7624,0,16);bool_moves(0x20D7628,0x20D762C);cmp(0x20D7630,0);at(0x20D7634)
    if not r[15]&(1<<30):
        at(0x20D7638);r[0]=word(r[6]+28)
        at(0x20D763C);r[0]&=~16
        at(0x20D7640);store(r[6]+28,r[0])
        at(0x20D7644);r[0]=word(r[6]+88)
        tst(0x20D7648,0,0x400);at(0x20D764C);need(r[15]&(1<<30),'Next no IDLE callback proc_flag88')
    at(0x20D766C);r[0]=word(r[6]+28)
    tst(0x20D7670,0,0x40);bool_moves(0x20D7674,0x20D7678);cmp(0x20D767C,0);at(0x20D7680)
    at(0x20D769C);r[0]=r[4]
    call(0x20D76A0,RESTORE)
    at(0x20D76A4);r[0]=0
    at(0x20D76A8);r[13]+=72
    at(0x20D76AC);saved=[word(r[13]+4*j)for j in range(8)];r[3:10]=saved[:7];r[13]+=32
    count=56 if not_running else 62
    need(saved[-1]==RETURN and(len(flow),len(stores),len(reads))==(count,8 if not_running else 9,15 if not_running else 17),
        'Next finite transcript and original return')
    return dict(flow=flow,stores=stores,reads=reads,services=[],incoming_next=incoming,returned=r,frame_before=before,frame_after=frame.hex(),
        archive_before=archive_before,archive_after=archive.hex(),native_peak=104,steps=count+1,unique_native_starts=count,stop=hex(RETURN))


def parent_memory(f,bodies):
    """Reconstruct the earlier observed whole image, requiring its actual digest."""
    captured,archive=check_fixture(f);need(set(bodies)==set(BODIES),'Next exact retained/new code components')
    for address,(n,digest)in BODIES.items():
        body=bodies[address];need(type(body)is bytes and len(body)==n and sha(body)==digest,'Next authenticated component bytes')
    image=bytearray(bytes([0xA5])*SIZE)
    for address,(n,digest)in Q.BODIES.items():image[address-BASE:address-BASE+n]=bodies[address]
    image[CAPTURED_BASE-BASE:TOP-BASE]=captured;image[ARC-BASE:ARC-BASE+92]=archive
    image[ENTRY-BASE:ENTRY-BASE+4]=bodies[ENTRY][:4]
    need(sha(bytes(image))==f['parent_whole_ram_sha256'],'Next reconstruction equals actual earlier whole-RAM digest')
    return bytes(image)


def initial_memory(f,bodies,fill,not_running=False):
    input_state(f,not_running,fill);image=bytearray(parent_memory(f,bodies))
    image[NEXT-BASE:END-BASE]=bodies[NEXT];image[ENTRY-BASE:RETURN-BASE]=bodies[ENTRY]
    image[RETURN-BASE:RETURN-BASE+4]=bytes.fromhex('000050e3')
    # Localized metamorphic variation, entirely below the separately captured408.
    image[FRAME-56-BASE:CAPTURED_BASE-BASE]=bytes([fill])*64
    if not_running:struct.pack_into('<I',image,ARC-BASE+28,3)
    return bytes(image)


def read_allowed(pc,address,n):
    words={ENTRY:FILE+8,0x20D74AC:ARC+28,0x20D7530:ARC+28,0x20D7548:ARC+28,0x20D7560:ARC+36,
        0x20D7620:ARC+28,0x20D7638:ARC+28,0x20D7644:ARC+88,0x20D766C:ARC+28}
    return n==4 and address%4==0 and(words.get(pc)==address or(pc==0x20D76AC and FRAME+72<=address<FRAME+104))


def write_allowed(pc,address,n):
    return n==4 and address%4==0 and((pc==NEXT and FRAME+72<=address<FRAME+104)or(pc==0x20D7640 and address==ARC+28))


def run(f,bodies,not_running=False,observe=True,fill=0xA5):
    """Execute the original bridge and Next/IRQ only; zero in-guest host state writes."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
    need(type(observe)is bool and unicorn.__version__=='2.1.4','Next strict observer and qualified Unicorn2.1.4')
    before=initial_memory(f,bodies,fill,not_running);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Next qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();incoming=None;flow=[];stores=[];reads=[];seen=set();steps=0;peak=0;returned=None;fault=None
    def step(uc,pc,n,_):
        nonlocal incoming,steps,peak,returned
        steps+=1;need(steps<=128,'Next bounded instruction count')
        if pc==RETURN:returned=regs();u.emu_stop();return
        if pc==NEXT:
            need(incoming is None,'Next single actual bridge delivery');incoming=regs()
            need(incoming[0]==ARC and incoming[13]==SP and incoming[14]==RETURN and incoming[15]&0xFF==0x1F,
                'Next actual original bridge pointer/SP/LR/I0/SYS/ARM ABI')
        selected=next(((a,bodies[a])for a in EXECUTED_BODIES if a<=pc<a+len(bodies[a])),None)
        need(selected is not None and(pc-selected[0])%4==0 and n==4 and not regs()[15]&32,'Next native executed-code whitelist')
        a,body=selected;need(read(pc,4)==body[pc-a:pc-a+4],'Next live instruction identity')
        seen.add(pc);peak=max(peak,SP-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'Next native PC/word/write owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    def load_word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'Next native PC/word/read owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,load_word)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=128)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=dict(not_running=not_running),observe=observe,fill=fill,entry=entry,incoming_next=incoming,returned=returned,
        flow=flow,stores=stores,reads=reads,services=[],steps=steps,native_peak=peak,observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),
        fault=fault,halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),frame_before=before[FRAME-BASE:TOP-BASE].hex(),
        frame_after=read(FRAME,416).hex(),archive_before=before[ARC-BASE:ARC-BASE+92].hex(),archive_after=read(ARC,92).hex(),
        guard_before=guard_before(fill).hex(),guard_after=read(FRAME-56,56).hex(),before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    r=row;f=r['fixture'];check_fixture(f)
    need(type(r['observe'])is bool and type(r['policy'])is dict and set(r['policy'])=={'not_running'},'Next strict observation/policy fields')
    want=predict(f,**r['policy'],fill=r['fill']);before=initial_memory(f,bodies,r['fill'],r['policy']['not_running']);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected=dict(entry=f['entry'],incoming_next=want['incoming_next'],returned=want['returned'],services=[],steps=want['steps'],native_peak=104,
        observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),
        frame_before=want['frame_before'],frame_after=want['frame_after'],archive_before=want['archive_before'],archive_after=want['archive_after'],
        guard_before=guard_before(r['fill']).hex(),guard_after=guard_before(r['fill']).hex(),before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for key in('flow','stores','reads'):expected[key]=want[key]if r['observe']else[]
    for key,value in expected.items():need(wire(r[key])==wire(value),'Next source-derived '+key)
    return True
