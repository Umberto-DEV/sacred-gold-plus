"""Zero-model nested SEEKDIR dispatch to the stopped original default gate.

clear_sync is a declared input derivative, not an actual parent state or service
policy. It can converge in final RAM/CPU while leaving native temporal evidence.
"""
from pathlib import Path
import importlib.util,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('nested_seekdir_qualified_default',Path(__file__).with_name('fs_default_findpath_bench.py'))
need,sha,wire=H.need,H.sha,H.wire
need(sha(Path(H.__file__).read_bytes())=='0314497a959e71fe2119f85fdd135e8bfc3a92abe387a14bacdaf0639eb71e19','Nested SEEKDIR qualified parent oracle drift')
T=H.H.T;ALU=T.ALU
TOP,FILE,ARC,BASE,SIZE,REGS=H.TOP,H.FILE,H.ARC,H.BASE,H.SIZE,H.REGS
ENTRY,RETURN,FRAME,POOL,TABLE=0x20D68C0,0x20D6BEC,TOP-544,0x20D6A4C,0x210E124
GATE_SHA='cb2450f37bd96fdbd6b5ca0da7f783e6a195e37f754014852618c0f6593e4d89'
BODIES={**H.BODIES,RETURN:(4,GATE_SHA)}
SITES=tuple(range(ENTRY,0x20D6904,4))+tuple(range(0x20D6968,0x20D6984,4))


def check_fixture(f):
    parent=H.predict(f['parent_default_fixture'])
    need(ALU.u32s(f['entry'])and wire(f['entry'])==wire(parent['returned'])and
         f['entry'][:2]==[FILE,2]and f['entry'][13:16]==[TOP-520,0x20D6DCC,0x6000001F],
         'Nested SEEKDIR actual stopped input, parameter2 not stored command4')
    frame,archive,guard=bytes.fromhex(f['frame']),bytes.fromhex(f['archive_before']),bytes.fromhex(f['guard'])
    need(len(frame)==544 and len(guard)==56 and frame[24:].hex()==parent['frame_after']and
         frame[:24].hex()==parent['guard_after'][-48:]and guard[24:].hex()==parent['guard_after'][:64]and
         archive.hex()==parent['archive_after'],'Nested SEEKDIR actual parent windows and guard promotion')
    need(struct.unpack_from('<3I',frame,FILE-FRAME+12)==(0x45,4,2)and struct.unpack_from('<I',archive,28)[0]==0x213,
         'Nested SEEKDIR canonical command4/busy2/active outer flag')
    return frame,archive,guard


def projection(f,clear_sync):
    need(type(clear_sync)is bool,'Nested SEEKDIR typed clear-sync input projection')
    return[dict(owner='archive',address=ARC+28,bytes=4,before='13020000',after='13000000',stage='before CPU') ]if clear_sync else[]


def predict(f,clear_sync=False):
    projected=projection(f,clear_sync);original,arc,guard=check_fixture(f)
    frame,archive=bytearray(original),bytearray(arc);r=list(f['entry']);flow=[];reads=[];stores=[];pc=ENTRY
    if clear_sync:struct.pack_into('<I',archive,28,0x13)
    initial_arc=archive.hex();checkpoints=dict(entry=dict(pc=hex(ENTRY),regs=list(r),frame=frame.hex(),archive=initial_arc))
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def owner(address):
        if FRAME<=address and address+4<=TOP:return frame,address-FRAME
        need(ARC<=address and address+4<=ARC+92,'Nested SEEKDIR source word owner');return archive,address-ARC
    def word(address):
        if address==POOL:blob=struct.pack('<I',TABLE)
        elif address==TABLE+8:blob=struct.pack('<I',RETURN)
        else:m,i=owner(address);blob=bytes(m[i:i+4])
        reads.append(dict(pc=hex(pc),address=address,bytes=4,hex=blob.hex()));return int.from_bytes(blob,'little')
    def store(address,value):
        m,i=owner(address);stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(m[i:i+4]).hex(),value=value))
        struct.pack_into('<I',m,i,value)
    def tst(value,mask):
        x=value&mask;r[15]=(r[15]&0x1FFFFFFF)|(x&0x80000000)|(int(x==0)<<30)|(r[15]&(1<<29))
    at(ENTRY);r[13]-=24
    for j,index in enumerate((4,5,6,7,8,14)):store(r[13]+4*j,r[index])
    at(0x20D68C4);r[8]=r[0]
    at(0x20D68C8);r[0]=word(r[8]+12)
    at(0x20D68CC);r[5]=word(r[8]+8)
    at(0x20D68D0);r[7]=r[1]
    at(0x20D68D4);r[1]=1
    at(0x20D68D8);tst(r[0],4)
    at(0x20D68DC);r[6]=r[1]<<r[7]
    at(0x20D68E0)
    if r[15]&(1<<30):r[1]=0
    at(0x20D68E4);r[0]=word(r[5]+28)
    at(0x20D68E8);r[15]=ALU.cmp(r[1],0,r[15])
    at(0x20D68EC)
    if not r[15]&(1<<30):r[0]|=0x200
    at(0x20D68F0)
    if r[15]&(1<<30):r[0]|=0x100
    at(0x20D68F4);checkpoints['before_flag_store']=dict(pc=hex(pc),regs=list(r),frame=frame.hex(),archive=archive.hex());store(r[5]+28,r[0])
    at(0x20D68F8);r[0]=word(r[5]+88)
    at(0x20D68FC);tst(r[0],r[6])
    at(0x20D6900);need(r[15]&(1<<30),'Nested SEEKDIR proc_flag0 skips callbacks')
    at(0x20D6968);r[4]=7
    at(0x20D696C);r[15]=ALU.cmp(r[4],7,r[15])
    at(0x20D6970);need(r[15]&(1<<30),'Nested SEEKDIR default fallback')
    at(0x20D6974);r[1]=word(POOL)
    at(0x20D6978);r[0]=r[8]
    at(0x20D697C);r[1]=word(r[1]+4*r[7])
    at(0x20D6980);need(r[1]==RETURN,'Nested SEEKDIR real slot2 target');r[14]=0x20D6984
    checkpoints['default_entry']=dict(pc=hex(RETURN),regs=list(r),frame=frame.hex(),archive=archive.hex())
    need(tuple(int(e['pc'],16)for e in flow)==SITES and len(stores)==7 and len(reads)==6,'Nested SEEKDIR finite source transcript')
    return dict(flow=flow,stores=stores,reads=reads,services=[],model_stores=[],host_stores=[],input_projection=projected,checkpoints=checkpoints,
        returned=r,frame_before=original.hex(),frame_after=frame.hex(),archive_before=initial_arc,archive_after=archive.hex(),
        guard_before=guard.hex(),guard_after=guard.hex(),steps=25,native_peak=24,unique_native_starts=24,stop=hex(RETURN))


def parent_memory(f,bodies):
    frame,archive,guard=check_fixture(f);need(set(bodies)==set(BODIES),'Nested SEEKDIR exact retained component set')
    for a,(n,digest)in BODIES.items():
        need(type(bodies[a])is bytes and len(bodies[a])==n and sha(bodies[a])==digest,'Nested SEEKDIR authenticated component')
    old={a:bodies[a]for a in H.BODIES};parent=f['parent_default_fixture'];image=bytearray(H.initial_memory(parent,old))
    need(sha(image)==f['observed_parent_before_whole_sha256'],'Nested SEEKDIR observed parent BEFORE whole image')
    want=H.predict(parent);stores=f['parent_native_stores'];need(len(stores)==9 and wire(stores)==wire(want['stores']),
        'Nested SEEKDIR actual/source nine PUSH writes')
    for w in stores:
        i=w['address']-BASE;need(w['bytes']==4 and 0<=i<=SIZE-4 and image[i:i+4].hex()==w['before'],'Nested SEEKDIR actual parent preimage')
        struct.pack_into('<I',image,i,w['value'])
    need(sha(image)==f['observed_parent_after_whole_sha256']and image[FRAME-BASE:TOP-BASE]==frame and
         image[FRAME-BASE-56:FRAME-BASE]==guard and image[ARC-BASE:ARC-BASE+92]==archive,
         'Nested SEEKDIR reconstructed observed AFTER image and24 added guard bytes')
    return bytes(image)


def initial_memory(f,bodies,clear_sync=False):
    projection(f,clear_sync);image=bytearray(parent_memory(f,bodies));image[RETURN-BASE:RETURN-BASE+4]=bodies[RETURN]
    need(sha(bodies[ENTRY][:396])==T.CODE_SHA and bodies[ENTRY][-4:]==struct.pack('<I',TABLE)and
         bodies[TABLE][8:12]==struct.pack('<I',RETURN),'Nested SEEKDIR code/pool/slot2 linkage')
    if clear_sync:struct.pack_into('<I',image,ARC+28-BASE,0x13)
    return bytes(image)


def read_allowed(pc,address,n):
    fields={0x20D68C8:FILE+12,0x20D68CC:FILE+8,0x20D68E4:ARC+28,0x20D68F8:ARC+88,0x20D6974:POOL,0x20D697C:TABLE+8}
    return n==4 and fields.get(pc)==address


def write_allowed(pc,address,n):
    return n==4 and address%4==0 and((pc==ENTRY and TOP-544<=address<TOP-520)or(pc==0x20D68F4 and address==ARC+28))


def run(f,bodies,clear_sync=False,observe=True):
    """Execute24 original ARM instructions; never execute the selected handler."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
    projected=projection(f,clear_sync);need(type(observe)is bool and unicorn.__version__=='2.1.4','Nested SEEKDIR strict observation/Unicorn2.1.4')
    before=initial_memory(f,bodies,clear_sync);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Nested SEEKDIR qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda a,n:bytes(u.mem_read(a,n))
    entry=regs();flow=[];stores=[];reads=[];checkpoints={};seen=set();steps=peak=0;returned=fault=None
    phases={ENTRY:'entry',0x20D68F4:'before_flag_store',RETURN:'default_entry'}
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=64,'Nested SEEKDIR bounded64 callbacks')
        peak=max(peak,entry[13]-regs()[13])
        if pc in phases:
            name=phases[pc];need(name not in checkpoints,'Nested SEEKDIR single checkpoint visit')
            checkpoints[name]=dict(pc=hex(pc),regs=regs(),frame=read(FRAME,544).hex(),archive=read(ARC,92).hex())
        if pc==RETURN:
            need(read(pc,4)==bodies[RETURN],'Nested SEEKDIR original stopped SeekDir PUSH');returned=regs();u.emu_stop();return
        need(pc in SITES and n==4 and not regs()[15]&32 and read(pc,4)==bodies[ENTRY][pc-ENTRY:pc-ENTRY+4],
             'Nested SEEKDIR selected24 original ARM PCs, no callback/pool/default-body execution')
        seen.add(pc)
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'Nested SEEKDIR exact native word read owner')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'Nested SEEKDIR native PUSH24/flag store only')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_READ,word);u.hook_add(UC_HOOK_MEM_WRITE,write)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=64)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=dict(clear_sync=clear_sync),observe=observe,entry=entry,returned=returned,flow=flow,stores=stores,reads=reads,
        services=[],model_stores=[],host_stores=[],input_projection=projected,checkpoints=checkpoints,steps=steps,native_peak=peak,
        observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),
        frame_before=before[FRAME-BASE:TOP-BASE].hex(),frame_after=read(FRAME,544).hex(),archive_before=before[ARC-BASE:ARC-BASE+92].hex(),
        archive_after=read(ARC,92).hex(),guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    f=row['fixture'];need(type(row['observe'])is bool and type(row['policy'])is dict and set(row['policy'])=={'clear_sync'},
                         'Nested SEEKDIR exact observation/projection fields')
    want=predict(f,**row['policy']);before=initial_memory(f,bodies,**row['policy']);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected={k:want[k]for k in('returned','services','model_stores','host_stores','input_projection','checkpoints','steps','native_peak',
                               'frame_before','frame_after','archive_before','archive_after','guard_before','guard_after')}
    expected.update(entry=f['entry'],observed_pcs=sorted(SITES),cpu_model=17,fault=None,halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),
                    before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for k in('flow','reads','stores'):expected[k]=want[k]if row['observe']else[]
    for k,v in expected.items():need(wire(row[k])==wire(v),'Nested SEEKDIR source-derived '+k)
    return True
