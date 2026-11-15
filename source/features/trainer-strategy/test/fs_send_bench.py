"""Finite Send4 idle source oracle with declared archive and value-only completion boundary.

The archive fixture and queue preparation do not establish natural SDK state.
ExecuteSync is not executed here; linked/busy/error2 state intentionally remains.
"""
from pathlib import Path
import importlib.util,json,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


F=load('send_qualified_find_helpers',Path(__file__).with_name('fs_find_bench.py'))
B,need,sha=F.B,F.need,F.sha
need(sha(Path(F.__file__).read_bytes())=='09f9685bd75c48f0e836a65181a56443abf7e8bd839bd1744f1dcbadc43aa893','Send qualified input/register helper drift')
ENTRY,END,EXECUTE,DISABLE,RESTORE,RETURN=0x20D7788,0x20D792C,0x20D7744,0x20D3A38,0x20D3A4C,0x20D80F8
TOP,FILE,ARC,ID,PATH=F.TOP,F.DIR,F.ARC,F.ID,F.PATH
SP,FRAME,BASE,SIZE,REGS=TOP-280,TOP-304,F.BASE,F.SIZE,F.REGS
ARCHIVE=bytes(28)+struct.pack('<I',3)+bytes(60)
BODY_SHA='ca74d4ff51db8cb32a7d6235e6b4d453554d65ac6162dc4092b7f285d0e4051a'
wire=lambda value:json.dumps(value,sort_keys=True,separators=(',',':'))


def check_fixture(f):
    r=f['entry'];need(B.u32s(r),'Send actual entry16 unsigned32')
    need(r==[FILE,4,0,FILE+48,1,0,ID,PATH,FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,0,SP,RETURN,0x6000001F],
         'Send finite actual native Find caller input, command4 and SYS I0')
    need(type(f['frame'])is type(f['archive_before'])is str,'Send byte preimages are hex strings')
    frame=bytes.fromhex(f['frame']);archive=bytes.fromhex(f['archive_before'])
    need(len(frame)==304 and archive==ARCHIVE,'Send exact actual frame304 and declared idle/noActivate archive92')
    i=FILE-FRAME
    for off,value in((0,0),(4,0),(8,ARC),(12,0),(16,14),(24,0),(28,0),
                      (48,ARC),(52,0),(56,0),(60,PATH),(64,0),(68,ID)):
        need(struct.unpack_from('<I',frame,i+off)[0]==value,'Send actual initialized directory fields/ARG and empty links')
    return frame,archive


def native_irq(r,at,address):
    """The qualified P63 five/six ARM instructions; no data-memory or stack effects."""
    need(address in(DISABLE,RESTORE),'Send only qualified IRQ leaves')
    if address==DISABLE:
        at(address);r[0]=r[15]
        at(address+4);r[1]=r[0]|0x80
        at(address+8);r[15]=(r[15]&~0xFF)|(r[1]&0xFF)
        at(address+12);r[0]&=0x80
        at(address+16)
    else:
        at(address);r[1]=r[15]
        at(address+4);r[2]=r[1]&~0x80
        at(address+8);r[2]|=r[0]
        at(address+12);r[15]=(r[15]&~0xFF)|(r[2]&0xFF)
        at(address+16);r[0]=r[1]&0x80
        at(address+20)


def predict(f,value=1,clobber=False):
    frame,archive=check_fixture(f);frame,archive=bytearray(frame),bytearray(archive);r=list(f['entry'])
    need(type(value)is int and value in(0,1,2)and type(clobber)is bool,'Send finite strict ExecuteSync value/clobber policy')
    flow=[];reads=[];stores=[];services=[];pc=ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def owned(address):
        if FRAME<=address and address+4<=FRAME+304:return frame,address-FRAME
        need(ARC<=address and address+4<=ARC+92,'Send source-owned frame/archive word access');return archive,address-ARC
    def read(address):
        memory,i=owned(address);blob=bytes(memory[i:i+4]);reads.append(dict(pc=hex(pc),address=address,bytes=4,hex=blob.hex()))
        return int.from_bytes(blob,'little')
    def store(address,value):
        memory,i=owned(address);stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(memory[i:i+4]).hex(),value=value))
        struct.pack_into('<I',memory,i,value)
    def tst(value,mask):
        # Encoded immediates1FC/200 have a nonzero rotation and shifter carry0.
        # Other exercised masks use rotation0 and preserve C; V is unchanged.
        need(mask in(0x80,0x1FC,8,16,0x200,4),'Send admitted TST masks')
        x=value&mask;carry=0 if mask in(0x1FC,0x200)else r[15]&(1<<29)
        r[15]=(r[15]&0x1FFFFFFF)|(x&0x80000000)|(int(x==0)<<30)|carry
    def cmp(a,b):r[15]=B.cmp(a,b,r[15])
    def call(pc,target):
        at(pc);r[14]=pc+4;native_irq(r,at,target)

    at(ENTRY);r[13]-=24
    for j,index in enumerate((3,4,5,6,7,14)):store(r[13]+4*j,r[index])
    at(0x20D778C);r[6]=r[0]
    at(0x20D7790);r[4]=read(r[6]+8)
    at(0x20D7794);r[2]=1
    at(0x20D7798);store(r[6]+16,r[1])
    at(0x20D779C);r[0]=2
    at(0x20D77A0);store(r[6]+20,r[0])
    at(0x20D77A4);r[0]=read(r[6]+12)
    at(0x20D77A8);r[7]=r[2]<<r[1]
    at(0x20D77AC);r[0]|=1
    at(0x20D77B0);store(r[6]+12,r[0])
    call(0x20D77B4,DISABLE)
    at(0x20D77B8);r[1]=read(r[4]+28)
    at(0x20D77BC);r[5]=r[0]
    at(0x20D77C0);tst(r[1],128)
    at(0x20D77C4);need(r[15]&(1<<30),'Send no archive-unloading gate')
    at(0x20D77E4);tst(r[7],0x1FC)
    at(0x20D77E8);r[0]=read(r[6]+12)
    at(0x20D77EC);r[0]|=4
    at(0x20D77F0);store(r[6]+12,r[0])
    at(0x20D77F4);r[1]=read(r[6])
    at(0x20D77F8);r[2]=read(r[6]+4)
    at(0x20D77FC);cmp(r[1],0)
    at(0x20D7800);need(r[15]&(1<<30),'Send source prevNULL falseSTRNE')
    at(0x20D7804);cmp(r[2],0)
    at(0x20D7808);r[0]=r[4]+32
    at(0x20D780C);need(r[15]&(1<<30),'Send source nextNULL falseSTRNE')
    at(0x20D7810);r[1]=read(r[0]+4)
    at(0x20D7814);cmp(r[1],0)
    at(0x20D7818);need(r[15]&(1<<30),'Send empty-list branch, no traversal')
    at(0x20D782C);store(r[0]+4,r[6])
    at(0x20D7830);store(r[6],r[0])
    at(0x20D7834);r[1]=0
    at(0x20D7838);store(r[6]+4,r[1])
    at(0x20D783C);r[0]=read(r[4]+28)
    at(0x20D7840);tst(r[0],8)
    at(0x20D7844);need(r[15]&(1<<30),'Send false suspended MOVNE')
    at(0x20D7848);cmp(r[1],0)
    at(0x20D784C)
    at(0x20D7850);r[0]=read(r[4]+28)
    at(0x20D7854);tst(r[0],16)
    at(0x20D7858);need(r[15]&(1<<30),'Send false running MOVNE')
    at(0x20D785C);r[0]=0
    at(0x20D7860);cmp(r[0],0)
    at(0x20D7864)
    at(0x20D7868);r[1]=read(r[4]+28)
    at(0x20D786C);r[0]=r[5]
    at(0x20D7870);r[1]|=16
    at(0x20D7874);store(r[4]+28,r[1])
    call(0x20D7878,RESTORE)
    at(0x20D787C);r[0]=read(r[4]+88)
    at(0x20D7880);tst(r[0],0x200)
    at(0x20D7884);need(r[15]&(1<<30),'Send noActivate callback gate')
    call(0x20D7898,DISABLE)
    at(0x20D789C);r[1]=read(r[6]+12)
    at(0x20D78A0);r[1]|=0x40
    at(0x20D78A4);store(r[6]+12,r[1])
    at(0x20D78A8);r[1]=read(r[6]+12)
    at(0x20D78AC);tst(r[1],4)
    at(0x20D78B0);r[1]=1
    at(0x20D78B4);need(not r[15]&(1<<30),'Send sync true, false MOVEQ')
    at(0x20D78B8);cmp(r[1],0)
    at(0x20D78BC)
    call(0x20D78D4,RESTORE)
    at(0x20D78D8)
    at(0x20D7920);r[0]=r[6]
    at(0x20D7924);r[14]=0x20D7928
    before=list(r);r=B.boundary_regs(r,value,clobber)
    services.append(dict(pc=hex(EXECUTE),entry=before,returned=list(r),result=value,
        frame_before=frame.hex(),frame_after=frame.hex(),archive_before=archive.hex(),archive_after=archive.hex(),
        model_scope='Return value only; no ExecuteSync/Translate/Release/Next/completion effects'))
    at(0x20D7928)
    saved=[read(r[13]+4*j)for j in range(6)]
    r[3:8]=saved[:5];r[13]+=24;need(saved[-1]==RETURN,'Send original saved ARM return')
    need((len(flow),len(stores),len(reads))==(90,15,19),'Send finite native source transcript extents')
    return dict(flow=flow,stores=stores,reads=reads,services=services,returned=r,frame_after=frame.hex(),
        archive_after=archive.hex(),native_peak=24,steps=92,unique_native_starts=len({e['pc']for e in flow}),stop=hex(RETURN))


BODIES={ENTRY:(420,BODY_SHA),DISABLE:(20,'a8cdb747f9936730571b220bb9570615892665b120713ffc59b1cb2d7dee76ff'),
        RESTORE:(24,'46b5111b6fad094dfff177dca974d33b477cb72772ecfe95b74b1c7f656bc4fd')}


def initial_memory(f,bodies,fill):
    frame,archive=check_fixture(f)
    need(type(fill)is int and fill in(0xA5,0x39)and set(bodies)==set(BODIES),'Send finite isolated preimage and qualified components')
    before=bytearray(bytes([fill])*SIZE)
    for address,(n,digest)in BODIES.items():
        body=bodies[address];need(type(body)is bytes and len(body)==n and sha(body)==digest,'Send exact native code component')
        before[address-BASE:address-BASE+n]=body
    before[FRAME-BASE:FRAME-BASE+304]=frame;before[ARC-BASE:ARC-BASE+92]=archive
    # Original Find return instruction: fetch gate only, stopped before execution.
    before[RETURN-BASE:RETURN-BASE+4]=struct.pack('<I',0xE28DD00C)
    # Our own NOP at the modeled entry; no native ExecuteSync instruction executes.
    before[EXECUTE-BASE:EXECUTE-BASE+4]=struct.pack('<I',0xE1A00000)
    return bytes(before)


def read_allowed(pc,address,n):
    if n!=4 or address%4:return False
    fields={0x20D7790:FILE+8,0x20D77A4:FILE+12,0x20D77B8:ARC+28,0x20D77E8:FILE+12,
        0x20D77F4:FILE,0x20D77F8:FILE+4,0x20D7810:ARC+36,0x20D783C:ARC+28,
        0x20D7850:ARC+28,0x20D7868:ARC+28,0x20D787C:ARC+88,0x20D789C:FILE+12,0x20D78A8:FILE+12}
    return fields.get(pc)==address or(pc==0x20D7928 and FRAME<=address<FRAME+24)


def write_allowed(pc,address,n):
    if n!=4 or address%4:return False
    fields={0x20D7798:FILE+16,0x20D77A0:FILE+20,0x20D77B0:FILE+12,0x20D77F0:FILE+12,
        0x20D782C:ARC+36,0x20D7830:FILE,0x20D7838:FILE+4,0x20D7874:ARC+28,0x20D78A4:FILE+12}
    return fields.get(pc)==address or(pc==ENTRY and FRAME<=address<FRAME+24)


def run(f,bodies,value=1,clobber=False,observe=True,fill=0xA5):
    """Collect one isolated call; semantic evaluation must follow raw preservation."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
    need(unicorn.__version__=='2.1.4','Send qualified Unicorn2.1.4 hook semantics')
    need(type(value)is int and value in(0,1,2)and type(clobber)is type(observe)is bool,'Send finite collector policy')
    before=initial_memory(f,bodies,fill);u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    need(u.ctl_get_cpu_model()==17,'Send qualified CPU17 instruction semantics')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,val in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,val)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    entry=regs();flow=[];stores=[];reads=[];services=[];seen=set();steps=0;peak=0;returned=None;fault=None
    def read(address,n):return bytes(u.mem_read(address,n))
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=128,'Send isolated bounded instruction count')
        if pc==RETURN:
            returned=regs();u.emu_stop();return
        if pc==EXECUTE:
            native=regs();sp,lr=native[13:15]
            need(native[0]==FILE and sp==FRAME and lr==0x20D7928 and n==4 and not native[15]&32,
                 'Send actual ExecuteSync file/SP/LR/ARM boundary')
            need(struct.unpack('<6I',read(FILE,24))==(ARC+32,0,ARC,0x45,4,2)and
                 struct.unpack('<3I',read(ARC+28,12))==(0x13,0,FILE)and read(ARC+84,8)==bytes(8),
                 'Send actual linked busy synchronous file, running archive and no callback')
            frame_before=read(FRAME,304).hex();archive_before=read(ARC,92).hex()
            new=B.boundary_regs(native,value,clobber)
            for reg,val in zip(REGS,new):u.reg_write(reg,val)
            services.append(dict(pc=hex(pc),entry=native,returned=regs(),result=value,
                frame_before=frame_before,frame_after=read(FRAME,304).hex(),archive_before=archive_before,archive_after=read(ARC,92).hex(),
                model_scope='Return value only; no ExecuteSync/Translate/Release/Next/completion effects'))
            u.reg_write(UC_ARM_REG_PC,lr);return
        selected=next(((a,b)for a,b in bodies.items()if a<=pc< a+len(b)),None)
        need(selected is not None and(pc-selected[0])%4==0 and n==4 and not regs()[15]&32,
             'Send native ARM whitelist, never another helper/callback/sleep branch')
        a,body=selected;need(read(pc,4)==body[pc-a:pc-a+4],'Send live native instruction identity')
        seen.add(pc);peak=max(peak,SP-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def write(uc,access,address,n,val,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'Send native word PC/field/stack write owner')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=val))
    def load_word(uc,access,address,n,val,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'Send native word PC/field/saved-stack read owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_WRITE,write);u.hook_add(UC_HOOK_MEM_READ,load_word)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=128)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    result=dict(fixture=f,policy=dict(execute=value,clobber=clobber),observe=observe,fill=fill,entry=entry,
        returned=returned,flow=flow,stores=stores,reads=reads,services=services,steps=steps,native_peak=peak,
        observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,halt_regs=regs(),
        halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),frame_after=read(FRAME,304).hex(),archive_after=read(ARC,92).hex(),
        guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return result


def require_result(result,bodies):
    r=result;f=r['fixture'];check_fixture(f)
    need(type(r['observe'])is bool and type(r['policy']['execute'])is int and r['policy']['execute']in(0,1,2)and
         type(r['policy']['clobber'])is bool,'Send strict observer/value/clobber receipt types')
    want=predict(f,r['policy']['execute'],r['policy']['clobber']);before=initial_memory(f,bodies,r['fill']);after=bytearray(before)
    after[FRAME-BASE:FRAME-BASE+304]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected=dict(entry=f['entry'],returned=want['returned'],services=want['services'],steps=92,native_peak=24,
        observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,
        halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),frame_after=want['frame_after'],archive_after=want['archive_after'],
        guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=before[FRAME-56-BASE:FRAME-BASE].hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for key in('flow','stores','reads'):expected[key]=want[key]if r['observe']else[]
    for key,value in expected.items():need(wire(r[key])==wire(value),'Send source-derived '+key)
    return True
