"""Finite Translate oracle and collector with an explicit default-handler model.

The selected native path uses a value-only default handler model. early_error
is an explicit negative service write, not an SDK failure or a natural state.
"""
from pathlib import Path
import importlib.util,struct


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


H=load('translate_qualified_send_source',Path(__file__).with_name('fs_send_native_callees_bench.py'))
need,sha,wire,ALU=H.need,H.sha,H.wire,H.E.B
need(sha(Path(H.__file__).read_bytes())=='c647263e7292e20a69cc47fdf157ada17abfc29b38dc383f89bc8db26fba8d98','Translate qualified parent oracle drift')
TOP,FILE,ARC,FRAME,BASE,SIZE,REGS=H.TOP,H.FILE,H.ARC,H.FRAME,H.BASE,H.SIZE,H.REGS
ENTRY,END,POOL,TABLE,DEFAULT,RETURN=0x20D68C0,0x20D6A4C,0x20D6A4C,0x210E124,0x20D6DB0,0x20D7754
MODEL_SCOPE='FSResult value-only default handler; no native handler/ID/property/card effects; other registers/CPSR preserved as declared policy'
BODY_SHA='f1df0f035e516cdfff9df4668530ca636f88b9a1a70d86804b9671c8bce7341a'
CODE_SHA='9c42ca76b2fa192199ad1687f07ea9bcf54a90f5b6fe950c6fd9cbb641fb719d'
TABLE_SHA='a2a3fe2a981c9967141752f3228d54c59d73c639339443bbe0ef04f13319d287'
DEFAULT_GATE_SHA='462b796a6c11d4277cd269fd03b7c46c2e0de0394c8071aa4a7a8d079be7bb87'
BODIES={**H.BODIES,ENTRY:(400,BODY_SHA),TABLE:(36,TABLE_SHA),DEFAULT:(4,DEFAULT_GATE_SHA)}


def check_fixture(f):
    need(ALU.u32s(f['entry'])and f['entry']==[FILE,4,0x2000001F,FILE+48,FILE,0,FILE,16,FILE,
         0x99999902,0xAAAAAA03,0xBBBBBB04,0,TOP-312,RETURN,0x2000001F],'Translate actual full16 finite sync entry')
    need(type(f['default_result'])is int and f['default_result']in(0,1),'Translate FSResult0/1, not BOOL or PROC_ASYNC')
    need(type(f['frame'])is type(f['archive_before'])is type(f['guard'])is str,'Translate exact byte strings')
    frame=bytes.fromhex(f['frame']);arc=bytes.fromhex(f['archive_before'])
    need(len(frame)==416 and arc==H.E.E.ARCHIVE and f['guard']=='a5'*56,'Translate observed frame416/linked archive92/guard56')
    for offset,value in((0,ARC+32),(4,0),(8,ARC),(12,0x45),(16,4),(20,2),(24,0),(28,0),
                         (48,ARC),(52,0),(56,0),(60,H.S.PATH),(64,0),(68,H.S.ID)):
        need(struct.unpack_from('<I',frame,FILE-FRAME+offset)[0]==value,'Translate actual linked BUSY2 file and command4/SYNC')
    return frame,arc


def predict(f,early_error=False):
    original,arc=check_fixture(f);need(type(early_error)is bool,'Translate strict early_error counter')
    frame,archive=bytearray(original),bytearray(arc);r=list(f['entry'])
    flow=[];reads=[];stores=[];services=[];model_stores=[];checkpoints={};pc=ENTRY
    def at(address):
        nonlocal pc
        pc=address;flow.append(dict(pc=hex(pc),regs=list(r)))
    def owner(address):
        if FRAME<=address and address+4<=TOP:return frame,address-FRAME
        need(ARC<=address and address+4<=ARC+92,'Translate source word owner');return archive,address-ARC
    def word(address):
        if address==POOL:blob=struct.pack('<I',TABLE)
        elif address==TABLE+16:blob=struct.pack('<I',DEFAULT)
        else:
            memory,i=owner(address);blob=bytes(memory[i:i+4])
        reads.append(dict(pc=hex(pc),address=address,bytes=4,hex=blob.hex()));return int.from_bytes(blob,'little')
    def store(address,value,events=None,target=None):
        memory,i=owner(address);event=dict(pc=hex(pc if target is None else target),address=address,bytes=4,
            before=bytes(memory[i:i+4]).hex(),value=value)
        (stores if events is None else events).append(event);struct.pack_into('<I',memory,i,value)
    def tst(value,mask):
        x=value&mask;r[15]=(r[15]&0x1FFFFFFF)|(x&0x80000000)|(int(x==0)<<30)|(r[15]&(1<<29))
    def checkpoint(name,address):
        checkpoints[name]=dict(pc=hex(address),regs=list(r),frame=frame.hex(),archive=archive.hex())
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
    at(0x20D68F4);store(r[5]+28,r[0])
    at(0x20D68F8);r[0]=word(r[5]+88)
    at(0x20D68FC);tst(r[0],r[6])
    at(0x20D6900);need(r[15]&(1<<30),'Translate proc_flag0 skips callback switch')
    at(0x20D6968);r[4]=7
    at(0x20D696C);r[15]=ALU.cmp(r[4],7,r[15])
    at(0x20D6970);need(r[15]&(1<<30),'Translate default fallback selected')
    at(0x20D6974);r[1]=word(POOL)
    at(0x20D6978);r[0]=r[8]
    at(0x20D697C);r[1]=word(r[1]+4*r[7])
    at(0x20D6980);need(r[1]==DEFAULT,'Translate actual default table target');r[14]=0x20D6984
    checkpoint('default_entry',DEFAULT);incoming=list(r);before=frame.hex();archive_before=archive.hex();writes=[]
    if early_error:store(FILE+20,f['default_result'],writes,DEFAULT)
    model_stores.extend(writes);r[0]=f['default_result']
    services.append(dict(pc=hex(DEFAULT),entry=incoming,returned=list(r),result_r0=r[0],writes=writes,
        frame_before=before,frame_after=frame.hex(),archive_before=archive_before,archive_after=archive.hex(),
        model_scope=MODEL_SCOPE,early_error=early_error))
    checkpoint('default_return',0x20D6984)
    at(0x20D6984);r[4]=r[0]
    at(0x20D6988);r[15]=ALU.cmp(r[4],6,r[15])
    at(0x20D698C);need(not r[15]&(1<<30),'Translate excludes PROC_ASYNC')
    at(0x20D6A00);r[0]=word(r[8]+12)
    at(0x20D6A04);tst(r[0],4)
    at(0x20D6A08)
    if not r[15]&(1<<30):r[0]=1
    at(0x20D6A0C)
    if r[15]&(1<<30):r[0]=0
    at(0x20D6A10);r[15]=ALU.cmp(r[0],0,r[15])
    at(0x20D6A14);need(not r[15]&(1<<30),'Translate sync path excludes native Release')
    at(0x20D6A34);r[0]=word(r[5]+28)
    at(0x20D6A38);r[0]&=~0x200
    at(0x20D6A3C);store(r[5]+28,r[0])
    checkpoint('before_error_store',0x20D6A40)
    at(0x20D6A40);store(r[8]+20,r[4])
    at(0x20D6A44);r[0]=r[4]
    at(0x20D6A48);saved=[word(r[13]+4*j)for j in range(6)];r[4:9]=saved[:5];r[13]+=24
    need(saved[-1]==RETURN,'Translate original saved PC, not current LR');checkpoint('final',RETURN)
    need((len(flow),len({e['pc']for e in flow}),len(stores),len(reads))==(39,39,9,14),'Translate finite source transcript')
    return dict(flow=flow,reads=reads,stores=stores,services=services,model_stores=model_stores,checkpoints=checkpoints,
        returned=r,frame_before=f['frame'],frame_after=frame.hex(),archive_before=f['archive_before'],archive_after=archive.hex(),
        steps=41,native_peak=24,unique_native_starts=39,stop=hex(RETURN))


def parent_memory(f,bodies):
    frame,archive=check_fixture(f);need(set(bodies)==set(BODIES),'Translate exact retained/new component set')
    for address,(n,digest)in BODIES.items():
        need(type(bodies[address])is bytes and len(bodies[address])==n and sha(bodies[address])==digest,'Translate authenticated component')
    old={a:bodies[a][:n]for a,(n,_)in H.BODIES.items()}
    image=bytearray(H.initial_memory(f['parent_send_fixture'],old))
    need(sha(bytes(image))==f['observed_before_Send_whole_sha256'],'Translate authenticated observed-before P75 Send image')
    source=H.predict(f['parent_send_fixture']);stores=f['prefix_stores']
    need(len(stores)==17 and wire(stores)==wire(source['stores'][:17]),'Translate raw/source seventeen prefix writes')
    for w in stores:
        offset=w['address']-BASE
        need(w['bytes']==4 and 0<=offset<=SIZE-4 and image[offset:offset+4].hex()==w['before'],'Translate actual prefix write preimage')
        struct.pack_into('<I',image,offset,w['value'])
    cp=source['checkpoints']['translate_entry']
    need(wire(cp['regs'])==wire(f['entry'])and cp['frame']==f['frame']and cp['archive']==f['archive_before'],
         'Translate source prefix reaches actual full entry/window')
    need(image[FRAME-BASE:TOP-BASE]==frame and image[ARC-BASE:ARC-BASE+92]==archive and
         image[FRAME-BASE-56:FRAME-BASE].hex()==f['guard'],'Translate complete derived checkpoint windows')
    need(sha(bytes(image))==f['derived_boundary_whole_sha256'],'Translate boundary digest is forward-derived, not a new capture')
    return bytes(image)


def initial_memory(f,bodies):
    image=bytearray(parent_memory(f,bodies))
    for address in(ENTRY,TABLE,DEFAULT):image[address-BASE:address-BASE+len(bodies[address])]=bodies[address]
    need(sha(bodies[ENTRY][:396])==CODE_SHA and bodies[ENTRY][-4:]==struct.pack('<I',TABLE)and
         bodies[TABLE][16:20]==struct.pack('<I',DEFAULT),'Translate code/pool/table/default linkage')
    need(image[RETURN-BASE:RETURN-BASE+4]==bodies[H.E.ENTRY][RETURN-H.E.ENTRY:RETURN-H.E.ENTRY+4],
         'Translate retained original ExecuteSync stopped MOV')
    return bytes(image)


def read_allowed(pc,address,n):
    fields={0x20D68C8:FILE+12,0x20D68CC:FILE+8,0x20D68E4:ARC+28,0x20D68F8:ARC+88,
        0x20D6974:POOL,0x20D697C:TABLE+16,0x20D6A00:FILE+12,0x20D6A34:ARC+28}
    return n==4 and address%4==0 and(fields.get(pc)==address or(pc==0x20D6A48 and TOP-336<=address<TOP-312))


def write_allowed(pc,address,n):
    return n==4 and address%4==0 and((pc==ENTRY and TOP-336<=address<TOP-312)or
        (pc in(0x20D68F4,0x20D6A3C)and address==ARC+28)or(pc==0x20D6A40 and address==FILE+20))


def run(f,bodies,early_error=False,observe=True):
    import unicorn
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR,UC_ARM_REG_R0
    need(type(early_error)is type(observe)is bool and unicorn.__version__=='2.1.4','Translate strict policies/Unicorn2.1.4')
    before=initial_memory(f,bodies);u=Uc(UC_ARCH_ARM,UC_MODE_ARM);need(u.ctl_get_cpu_model()==17,'Translate qualified CPU17')
    u.mem_map(BASE,SIZE);u.mem_write(BASE,before);u.reg_write(UC_ARM_REG_CPSR,f['entry'][15])
    for reg,value in zip(REGS[:-1],f['entry'][:-1]):u.reg_write(reg,value)
    regs=lambda:[u.reg_read(reg)for reg in REGS]
    read=lambda address,n:bytes(u.mem_read(address,n))
    entry=regs();flow=[];reads=[];stores=[];services=[];model_stores=[];checkpoints={};seen=set()
    steps=peak=0;returned=fault=None
    phases={DEFAULT:'default_entry',0x20D6984:'default_return',0x20D6A40:'before_error_store',RETURN:'final'}
    def step(uc,pc,n,_):
        nonlocal steps,peak,returned
        steps+=1;need(steps<=64,'Translate bounded instruction count')
        if pc in phases:
            phase=phases[pc];need(phase not in checkpoints,'Translate single checkpoint visit')
            checkpoints[phase]=dict(pc=hex(pc),regs=regs(),frame=read(FRAME,416).hex(),archive=read(ARC,92).hex())
        if pc==RETURN:
            need(read(pc,4)==bodies[H.E.ENTRY][RETURN-H.E.ENTRY:RETURN-H.E.ENTRY+4],'Translate original stopped caller MOV')
            returned=regs();u.emu_stop();return
        if pc==DEFAULT:
            incoming=regs();need(not services and n==4 and read(pc,4)==bodies[DEFAULT]and incoming[:2]==[FILE,DEFAULT]and
                incoming[13:15]==[TOP-336,0x20D6984]and incoming[15]==0x6000001F,'Translate actual default gate/ABI, not wrapper Find')
            fb,ab=read(FRAME,416).hex(),read(ARC,92).hex();writes=[]
            need(read(FILE+20,4)==struct.pack('<I',2)and read(ARC+28,4)==struct.pack('<I',0x213),'Translate native pre-service transient/busy fields')
            if early_error:
                event=dict(pc=hex(pc),address=FILE+20,bytes=4,before=read(FILE+20,4).hex(),value=f['default_result'])
                writes.append(event);model_stores.append(event);u.mem_write(FILE+20,struct.pack('<I',f['default_result']))
            u.reg_write(UC_ARM_REG_R0,f['default_result'])
            services.append(dict(pc=hex(pc),entry=incoming,returned=regs(),result_r0=f['default_result'],writes=writes,
                frame_before=fb,frame_after=read(FRAME,416).hex(),archive_before=ab,archive_after=read(ARC,92).hex(),
                model_scope=MODEL_SCOPE,early_error=early_error))
            u.reg_write(UC_ARM_REG_PC,incoming[14]);return
        need(ENTRY<=pc<END and(pc-ENTRY)%4==0 and n==4 and not regs()[15]&32 and
             read(pc,4)==bodies[ENTRY][pc-ENTRY:pc-ENTRY+4],'Translate native instruction whitelist, no pool/callback/async helper')
        seen.add(pc);peak=max(peak,entry[13]-regs()[13])
        if observe:flow.append(dict(pc=hex(pc),regs=regs()))
    def word(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(read_allowed(pc,address,n),'Translate read PC/owner including literal/table')
        if observe:reads.append(dict(pc=hex(pc),address=address,bytes=n,hex=read(address,n).hex()))
    def write(uc,access,address,n,value,_):
        pc=uc.reg_read(UC_ARM_REG_PC);need(write_allowed(pc,address,n),'Translate native write PC/owner, no readonly table/pool writes')
        if observe:stores.append(dict(pc=hex(pc),address=address,bytes=n,before=read(address,n).hex(),value=value))
    u.hook_add(UC_HOOK_CODE,step);u.hook_add(UC_HOOK_MEM_READ,word);u.hook_add(UC_HOOK_MEM_WRITE,write)
    try:u.emu_start(ENTRY,BASE+SIZE,timeout=1000000,count=64)
    except Exception as error:fault=dict(type=type(error).__name__,message=str(error))
    after=read(BASE,SIZE)
    row=dict(fixture=f,policy=dict(early_error=early_error),observe=observe,entry=entry,returned=returned,flow=flow,reads=reads,stores=stores,
        services=services,model_stores=model_stores,checkpoints=checkpoints,steps=steps,native_peak=peak,observed_pcs=sorted(seen),
        cpu_model=u.ctl_get_cpu_model(),fault=fault,halt_regs=regs(),halt_pc=hex(u.reg_read(UC_ARM_REG_PC)),stop=hex(RETURN),
        frame_before=before[FRAME-BASE:TOP-BASE].hex(),frame_after=read(FRAME,416).hex(),archive_before=before[ARC-BASE:ARC-BASE+92].hex(),
        archive_after=read(ARC,92).hex(),guard_before=before[FRAME-BASE-56:FRAME-BASE].hex(),guard_after=read(FRAME-56,56).hex(),
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(after))
    del u;return row


def require_result(row,bodies):
    f=row['fixture'];need(type(row['observe'])is bool and type(row['policy'])is dict and set(row['policy'])=={'early_error'},
                         'Translate strict observation/policy')
    want=predict(f,**row['policy']);before=initial_memory(f,bodies);after=bytearray(before)
    after[FRAME-BASE:TOP-BASE]=bytes.fromhex(want['frame_after']);after[ARC-BASE:ARC-BASE+92]=bytes.fromhex(want['archive_after'])
    expected={k:want[k]for k in('returned','services','model_stores','checkpoints','steps','native_peak','frame_before','frame_after','archive_before','archive_after')}
    expected.update(entry=f['entry'],observed_pcs=sorted({int(e['pc'],16)for e in want['flow']}),cpu_model=17,fault=None,
        halt_regs=want['returned'],halt_pc=hex(RETURN),stop=hex(RETURN),guard_before=f['guard'],guard_after=f['guard'],
        before_whole_ram_sha256=sha(before),whole_ram_sha256=sha(bytes(after)))
    for k in('flow','reads','stores'):expected[k]=want[k]if row['observe']else[]
    for k,v in expected.items():need(wire(row[k])==wire(v),'Translate source-derived '+k)
    return True
