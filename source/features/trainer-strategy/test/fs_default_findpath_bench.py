"""Native default FindPath prefix: no filesystem service or result model.

prepush is an explicit host fault after the entry snapshot, before native PUSH.
lower_fill changes only the104 newly exposed bytes before the guest starts.
"""
from pathlib import Path
import importlib.util,struct


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('default_findpath_qualified_send_translate',Path(__file__).with_name('fs_send_translate_native_bench.py'))
need,sha,wire=H.need,H.sha,H.wire
need(sha(Path(H.__file__).read_bytes())=='8ec8fe0d028ab9416ba07697421808bde65d4bf678301b2687930c5b6f270477','Default FindPath qualified parent oracle drift')
TOP,FILE,ARC,BASE,SIZE,REGS=H.TOP,H.FILE,H.ARC,H.BASE,H.SIZE,H.REGS
ENTRY,RETURN,FRAME=0x20D6DB0,0x20D68C0,TOP-520
OWNER_SHA='70727f66b05763ecfc2b1819f4580f5e0aa029b4cd6cc269776d722fa560e63e'
PREFIX_SHA='e2b54d82ad94489b669926c98c67c430df38f882e24e68ae646f660686de0233'
BODIES={**H.BODIES,ENTRY:(484,OWNER_SHA)}
SAVED=(3,4,5,6,7,8,9,10,14)


def policies(prepush,lower_fill):
    need(type(prepush)is bool and(lower_fill is None or type(lower_fill)is int and lower_fill==0x39),
         'Default FindPath typed host-fault and lower-fill policies')


def check_fixture(f):
    parent=f['parent_send_fixture'];cp=H.predict(parent)['checkpoints']['default_entry']
    need(wire(f['entry'])==wire(cp['regs'])and f['entry'][:2]==[FILE,ENTRY]and
         f['entry'][13:16]==[TOP-336,0x20D6984,0x6000001F],'Default FindPath actual full16 before native PUSH')
    frame,archive,guard=bytes.fromhex(f['frame']),bytes.fromhex(f['archive_before']),bytes.fromhex(f['guard'])
    need(len(frame)==520 and len(guard)==56 and frame[104:].hex()==cp['frame']and archive.hex()==cp['archive']and
         frame[48:104].hex()==parent['guard'],'Default FindPath retained captured windows and derived extra104')
    need(struct.unpack_from('<3I',frame,FILE-FRAME+12)==(0x45,4,2)and struct.unpack_from('<I',archive,28)[0]==0x213,
         'Default FindPath outer command4/busy2 and nested active archive')
    return frame,archive,guard


def predict(f,prepush=False,lower_fill=None):
    policies(prepush,lower_fill);original,archive,guard=check_fixture(f);frame=bytearray(original);r=list(f['entry'])
    if lower_fill is not None:frame[:48]=bytes([lower_fill])*48;guard=bytes([lower_fill])*56
    initial=frame.hex();flow=[];stores=[];reads=[];host_stores=[]
    checkpoints=dict(entry=dict(pc=hex(ENTRY),regs=list(r),frame=initial,archive=archive.hex()))
    def at(pc):flow.append(dict(pc=hex(pc),regs=list(r)))
    def save(address,value,events):
        i=address-FRAME;need(148<=i<184,'Default FindPath source saved36 owner')
        events.append(dict(pc=hex(ENTRY),address=address,bytes=4,before=frame[i:i+4].hex(),value=value))
        struct.pack_into('<I',frame,i,value)
    if prepush:
        for j,index in enumerate(SAVED):save(r[13]-36+4*j,r[index],host_stores)
    at(ENTRY);r[13]-=36
    for j,index in enumerate(SAVED):save(r[13]+4*j,r[index],stores)
    at(0x20D6DB4);r[13]-=148
    at(0x20D6DB8);r[9]=r[0]
    at(0x20D6DBC);address=r[9]+60;i=address-FRAME
    reads.append(dict(pc='0x20d6dbc',address=address,bytes=4,hex=frame[i:i+4].hex()));r[5]=struct.unpack_from('<I',frame,i)[0]
    at(0x20D6DC0);r[1]=2
    at(0x20D6DC4);address=r[9]+64;i=address-FRAME
    reads.append(dict(pc='0x20d6dc4',address=address,bytes=4,hex=frame[i:i+4].hex()));r[6]=struct.unpack_from('<I',frame,i)[0]
    at(0x20D6DC8);r[14]=0x20D6DCC
    checkpoints['nested_translate_entry']=dict(pc=hex(RETURN),regs=list(r),frame=frame.hex(),archive=archive.hex())
    need(frame[:148].hex()==initial[:296]and frame[184:].hex()==initial[368:],'Default FindPath uninitialized locals and other fields untouched')
    return dict(flow=flow,stores=stores,reads=reads,services=[],model_stores=[],host_stores=host_stores,checkpoints=checkpoints,
        returned=r,frame_before=initial,frame_after=frame.hex(),archive_before=archive.hex(),archive_after=archive.hex(),
        guard_before=guard.hex(),guard_after=guard.hex(),steps=8,native_peak=184,unique_native_starts=7,stop=hex(RETURN))


def parent_memory(f,bodies):
    frame,archive,guard=check_fixture(f);need(set(bodies)==set(BODIES),'Default FindPath exact retained component set')
    for a,(n,digest)in BODIES.items():
        need(type(bodies[a])is bytes and len(bodies[a])==n and sha(bodies[a])==digest,'Default FindPath authenticated component')
    old={a:bodies[a][:n]for a,(n,_)in H.BODIES.items()};image=bytearray(H.initial_memory(f['parent_send_fixture'],old))
    need(sha(image)==f['observed_before_Send_whole_sha256'],'Default FindPath observed-before Send whole image')
    want=H.predict(f['parent_send_fixture']);stores=f['prefix_stores']
    need(len(stores)==24 and wire(stores)==wire(want['stores'][:24]),'Default FindPath actual/source native prefix24')
    for w in stores:
        i=w['address']-BASE;need(w['bytes']==4 and 0<=i<=SIZE-4 and image[i:i+4].hex()==w['before'],'Default FindPath upstream native preimage')
        struct.pack_into('<I',image,i,w['value'])
    need(sha(image)==f['derived_boundary_whole_sha256']and image[FRAME-BASE:TOP-BASE]==frame and
         image[FRAME-BASE-56:FRAME-BASE]==guard and image[ARC-BASE:ARC-BASE+92]==archive,
         'Default FindPath forward-derived whole checkpoint and added104, not fill or capture')
    return bytes(image)


def initial_memory(f,bodies,lower_fill=None):
    policies(False,lower_fill);image=bytearray(parent_memory(f,bodies));image[ENTRY-BASE:ENTRY-BASE+484]=bodies[ENTRY]
    need(sha(bodies[ENTRY][:28])==PREFIX_SHA,'Default FindPath compiled prefix agrees with retained owner')
    if lower_fill is not None:image[FRAME-56-BASE:FRAME+48-BASE]=bytes([lower_fill])*104
    return bytes(image)


def read_allowed(pc,address,n):
    return n==4 and((pc==0x20D6DBC and address==FILE+60)or(pc==0x20D6DC4 and address==FILE+64))


def write_allowed(pc,address,n):
    return pc==ENTRY and n==4 and address%4==0 and TOP-372<=address<TOP-336


def run(f,bodies,prepush=False,lower_fill=None,observe=True):
    """Run seven original instructions; stop before nested Translate executes."""
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
    policies(prepush,lower_fill);need(type(observe)is bool and unicorn.__version__=='2.1.4','Default FindPath strict observation/Unicorn2.1.4')
    before=initial_memory(f,bodies,lower_fill);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Default FindPath qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda a,n:bytes(u.mem_read(a,n))
    entry=regs();flow=[];stores=[];reads=[];host_stores=[];checkpoints={};seen=set();steps=peak=0;returned=fault=None
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=32,'Default FindPath bounded32 callbacks')
        peak=max(peak,entry[13]-regs()[13])
        if pc in(ENTRY,RETURN):
            phase='entry'if pc==ENTRY else'nested_translate_entry';need(phase not in checkpoints,'Default FindPath single boundary visit')
            checkpoints[phase]=dict(pc=hex(pc),regs=regs(),frame=read(FRAME,520).hex(),archive=read(ARC,92).hex())
        if pc==RETURN:
            need(read(pc,4)==bodies[RETURN][:4],'Default FindPath original stopped Translate PUSH');returned=regs();u.emu_stop();return
        need(ENTRY<=pc<ENTRY+28 and(pc-ENTRY)%4==0 and n==4 and not regs()[15]&32 and read(pc,4)==bodies[ENTRY][pc-ENTRY:pc-ENTRY+4],
             'Default FindPath seven original ARM instructions, no body tail or nested execution')
        if pc==ENTRY and prepush:
            # After recording the actual entry, without changing SP, PC or CPU.
            for j,index in enumerate(SAVED):
                address=entry[13]-36+4*j;value=entry[index]
                host_stores.append(dict(pc=hex(ENTRY),address=address,bytes=4,before=read(address,4).hex(),value=value))
                u.mem_write(address,struct.pack('<I',value))
        seen.add(pc)
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'Default FindPath exact two native word reads')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'Default FindPath native PUSH saved36 only')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_READ,word);u.hook_add(UC_HOOK_MEM_WRITE,write)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=32)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=dict(prepush=prepush,lower_fill=lower_fill),observe=observe,entry=entry,returned=returned,
        flow=flow,stores=stores,reads=reads,services=[],model_stores=[],host_stores=host_stores,checkpoints=checkpoints,steps=steps,
        native_peak=peak,observed_pcs=sorted(seen),cpu_model=u.ctl_get_cpu_model(),fault=fault,halt_regs=regs(),
        halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),frame_before=before[FRAME-BASE:TOP-BASE].hex(),frame_after=read(FRAME,520).hex(),
        archive_before=before[ARC-BASE:ARC-BASE+92].hex(),archive_after=read(ARC,92).hex(),guard_before=before[FRAME-56-BASE:FRAME-BASE].hex(),
        guard_after=read(FRAME-56,56).hex(),before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    f=row['fixture'];need(type(row['observe'])is bool and type(row['policy'])is dict and set(row['policy'])=={'prepush','lower_fill'},
                         'Default FindPath exact observation/policy fields')
    want=predict(f,**row['policy']);before=initial_memory(f,bodies,row['policy']['lower_fill']);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after'])
    expected={k:want[k]for k in('returned','services','model_stores','host_stores','checkpoints','steps','native_peak','frame_before','frame_after',
                                'archive_before','archive_after','guard_before','guard_after')}
    expected.update(entry=f['entry'],observed_pcs=list(range(ENTRY,ENTRY+28,4)),cpu_model=17,fault=None,
        halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for k in('flow','reads','stores'):expected[k]=want[k]if row['observe']else[]
    for k,v in expected.items():need(wire(row[k])==wire(v),'Default FindPath source-derived '+k)
    return True
