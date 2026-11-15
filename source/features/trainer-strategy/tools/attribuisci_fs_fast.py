#!/usr/bin/env python3
"""Native OpenFast fields and spilled aggregate inside the complete PP caller.

FSi_SendCommand is a declared archive-opening model, not native filesystem state.
"""
from pathlib import Path
import importlib.util,struct,types,copy


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('fs_fast_convert_parent',Path(__file__).with_name('attribuisci_fs_convert.py'))
A=load('fs_fast_profile',Path(__file__).parents[1]/'test/fs_fast_bench.py');A.bind(H)
R,P,B,T,need,sha=H.R,H.P,H.B,H.T,H.need,H.sha
TOP,DEST,STOP,FILE,ID,ARC,DIR=H.TOP,H.DEST,H.STOP,H.FILE,H.ID,H.ARC,H.DIR
ENTRY,END,RETURN,SEND,SP=0x20D8208,0x20D8278,0x20D82A4,0x20D7788,TOP-176
FAST_SHA='465013782ef4760fff5100c626a4ddc63e8611d1517a1b9bc105b23092638bd9'
SDK={a:n for a,n in H.SDK.items()if a!=ENTRY};SDK[SEND]='FSi_SendCommand'
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
BINDINGS=[]


def binding(fn,namespace):
    BINDINGS.append(dict(parent_source_sha256=A.PARENT_SHA256,function=fn.__qualname__,code_unchanged=True,
        namespace=sorted(namespace)))
    return A.clone(fn,namespace)


def qualify(model,raw,*args):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
    q,proof=H.qualify(model,raw,*args);view=P.G.S.SHARED.gifts_audit.Arm9View(raw);blob=view.read(ENTRY,112)
    need(sha(blob)==FAST_SHA and blob==P.G.piece(model['segments'],ENTRY,112),'Fast raw/decoded identity')
    code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(blob,ENTRY))
    need(len(code)==28 and [i.address for i in code]==list(range(ENTRY,END,4))and
        {i.address:i.op_str for i in code if i.mnemonic=='bl'}=={0x20D8240:'#0x20d7788'},'Fast ARM extent and Send target')
    q['fs_fast_code']={i.address:(4,False)for i in code}
    proof['native_fs_fast']=dict(ram=hex(ENTRY),rom_offset=hex(view.offset(ENTRY,112)),bytes=112,sha256=sha(blob),
        starts=28,fast_frame=24,reader_peak=240,global_guest_peak=560,full_bound=608,
        file_fields=[8,48,52,12],model='FSi_SendCommand command6; no native archive/card/thread state')
    return q,proof


class FastObserver:
    def __init__(self,driver,reader):
        self.driver,self.reader,self.active=driver,reader,False
        self.result=dict(entry=None,returned=None,frame_before=None,frame_after=None,file_before=None,file_after=None,
            flow=[],stores=[],reads=[],shadows=[],ledger_before=None,ledger_after=None)
        self.parent_step,self.parent_write,self.parent_read,self.base_service=reader.step,reader.write,reader.read,reader.service
        self.root_step=types.MethodType(root_step,reader);self.root_write=driver.convert_observer.native_write
        reader.code={**reader.code,**driver.qualified['fs_fast_code']}
        reader.step,reader.write,reader.read,reader.service=self.step,self.write,self.read,self.service

    def step(self,u,pc,n,user):
        r,out=self.reader,self.result
        if pc==ENTRY:
            need(out['entry']is None and self.driver.open_observer.active and not r.open and r.file==FILE,
                'single selected Fast inside Open after native Convert')
            self.active=True;out.update(entry=r.regs(),frame_before=r.read_bytes(DIR,240).hex(),
                file_before=r.read_bytes(FILE,72).hex(),ledger_before=self.driver.convert_observer.ledger())
        if self.active and pc==RETURN:
            out.update(returned=r.regs(),frame_after=r.read_bytes(DIR,240).hex(),file_after=r.read_bytes(FILE,72).hex(),
                ledger_after=self.driver.convert_observer.ledger());self.active=False
        if self.active:
            if ENTRY<=pc<END:out['flow'].append(dict(pc=hex(pc),regs=r.regs()))
            self.root_step(u,pc,n,user)
            if pc==0x20D8268 and self.driver.fast_variant=='status_zero':
                before=r.regs();need(before[0]==1 and before[1]==16 and before[4]==FILE and before[13:15]==[SP,0x20D8244],
                    'Fast status-only shadow after native ORR/BIC and successful Send')
                u.reg_write(B.R[1],0);out['shadows'].append(dict(pc=hex(pc),before=before,after=r.regs(),
                    reason='R1 status16 to0 only before native FILE.stat store; Send ledger remains open'))
            return
        self.parent_step(u,pc,n,user)

    def write(self,u,access,address,n,value,user):
        if self.active:
            pc=u.reg_read(UC_ARM_REG_PC)
            need((SP<=address and address+n<=ID)or(FILE<=address and address+n<=FILE+72),
                'Fast writes only24 saved bytes and its live file')
            if self.reader.observe:self.result['stores'].append(dict(pc=hex(pc),address=address,bytes=n,
                before=self.reader.read_bytes(address,n).hex(),value=value))
            self.root_write(u,access,address,n,value,user);return
        self.parent_write(u,access,address,n,value,user)

    def read(self,u,access,address,n,value,user):
        pc=u.reg_read(UC_ARM_REG_PC)
        if self.active and pc in(0x20D8210,0x20D8234):
            self.result['reads'].append(dict(pc=hex(pc),address=address,bytes=n,hex=self.reader.read_bytes(address,n).hex()))
        self.parent_read(u,access,address,n,value,user)

    def service(self,pc):
        if pc!=SEND:return self.base_service(pc)
        r,u=self.reader,self.reader.u;before=r.regs();args=before[:4];sp,lr=before[13:15]
        need(self.active and sp==SP and lr==0x20D8244 and not before[15]&32 and r.initialized and r.file==FILE and
            args[:3]==[FILE,6,140]and r.path=='a/0/1/1'and not r.open and r.archive is None and
            r.read_bytes(ID,8)==struct.pack('<II',ARC,140)and
            r.read_bytes(FILE+8,4)==struct.pack('<I',ARC)and r.read_bytes(FILE+48,8)==struct.pack('<II',ARC,140),
            'Send command6 sees native Fast file fields and actual spilled aggregate')
        choices=[v for v in r.data.values()if v['path']==r.path];need(len(choices)==1,'Send raw archive identity')
        event=dict(name=SDK[SEND],pc=hex(pc),args=args,sp=sp,lr=hex(lr),saved=before[4:12],
            cursor_before=r.cursor,open_before=r.open,entry=before,path=r.path,archive_bytes=len(choices[0]['raw']),
            archive_sha256=sha(choices[0]['raw']),native_FSFile_layout_modeled=False,opaque_archive_token=ARC,file_id=140,
            file_before_hex=r.read_bytes(FILE,72).hex())
        r.archive=choices[0]['raw'];r.open=True;r.cursor=0
        if r.clobber:
            for i in(1,2,3,12):u.reg_write(B.R[i],0xA5000000+i)
            u.reg_write(UC_ARM_REG_CPSR,(u.reg_read(UC_ARM_REG_CPSR)&0x0FFFFFFF)|0xA0000000)
        u.reg_write(B.R[0],self.driver.send_value);u.reg_write(UC_ARM_REG_PC,lr);after=r.regs()
        need(after[13]==sp and after[4:12]==before[4:12]and not after[15]&32 and
            r.read_bytes(FILE,72).hex()==event['file_before_hex'],'Send ARM return preserves guest file and callee-saved state')
        event.update(result_r0=self.driver.send_value,return_sp=after[13],return_saved=after[4:12],
            return_volatile=[after[i]for i in(1,2,3,12)],cursor_after=0,open_after=True,returned=after)
        r.models.append(event)


class Driver(H.Driver):
    def __init__(self,*args,variant='current',send_value=1,**kwargs):
        need(variant in('current','status_zero')and type(send_value)is int and send_value in(1,2)and
            (variant=='current'or send_value==1),'finite Fast controls')
        super().__init__(*args,variant='current',**kwargs)
        self.fast_variant,self.send_value,self.fast_result=variant,send_value,None

    def start_pp(self):
        super().start_pp();regs=self.regs();before=self.read_bytes(0x2000000,0x400000)
        self.fast_observer=FastObserver(self,self.pp_reader);self.fast_result=self.fast_observer.result
        need(regs==self.regs()and before==self.read_bytes(0x2000000,0x400000),'Fast attachment changed guest state')


root_step=binding(H.reader_step,dict(SDK=SDK))
run_case,RUN_RECIPE=A.rewrite(H,H.H.H.V,'run_case',A.edits(H.RECIPES[4])+[
    ('find_value=1):','find_value=1,send_value=1):',1),
    ('find_value=find_value)','find_value=find_value,send_value=send_value)',1),
    ('return dict(convert=','return dict(fs_fast=driver.fast_result,send_value=driver.send_value,convert=',1)],
    dict(Driver=Driver,A=H.H.H.A,TOP=TOP,NAME_ARENA=H.H.H.X.NAME_ARENA,NAME_END=H.H.H.X.NAME_END),'message_caller')


def expected_fast(r,entry=None,status=16):
    need(type(r['send_value'])is int and r['send_value']in(1,2)and status in(0,16),'finite Fast result/status policy')
    start=[FILE,ARC,140,0,FILE,310,H.H.H.MON,0]+list(H.H.H.N.COOKIES[4:])+[0xA500000C if r['pp_clobber'] else 0,ID,RETURN,0x2000001F]
    need(entry is None or list(entry)==start,'Fast by-value entry follows native Open LDM')
    regs=list(start);flow=[];send=None
    for pc in range(ENTRY,END,4):
        flow.append(dict(pc=hex(pc),regs=list(regs)))
        if pc in(ENTRY,0x20D820C):regs[13]-=16 if pc==ENTRY else 8
        elif pc==0x20D8210:regs[1]=ARC
        elif pc==0x20D8214:regs[4]=FILE
        elif pc==0x20D8218:regs[15]=0x2000001F
        elif pc==0x20D8234:regs[2]=140
        elif pc==0x20D8238:regs[1]=6
        elif pc==0x20D8240:
            regs[14]=0x20D8244;before=list(regs)
            if r['pp_clobber']:
                for i in(1,2,3,12):regs[i]=0xA5000000+i
                regs[15]=0xA000001F
            regs[0]=r['send_value'];send=dict(pc=hex(SEND),entry=before,returned=list(regs))
        elif pc==0x20D8244:regs[15]=0x2000001F
        elif pc==0x20D8258:regs[1]=0
        elif pc==0x20D825C:regs[0]=1
        elif pc==0x20D8260:regs[1]|=16
        elif pc==0x20D8264:regs[1]&=~32
        elif pc==0x20D8268:regs[1]=status
        elif pc==0x20D826C:regs[4]=start[4];regs[14]=RETURN;regs[13]+=8
        elif pc==0x20D8270:regs[13]+=16
    return dict(entry=start,flow=flow,send=send,returned=regs)


def file_after(blob,status=16):
    out=bytearray(blob);need(len(out)==72,'FSFile72 preimage')
    for offset,value in((8,ARC),(48,ARC),(52,140),(12,status)):struct.pack_into('<I',out,offset,value)
    return bytes(out)


def open_after(blob,status=16):
    out=bytearray(blob);need(len(out)==152,'Open152 postimage')
    out[FILE-ID:FILE-ID+72]=file_after(out[FILE-ID:FILE-ID+72],status)
    return bytes(out)


def context_bindings():
    predicted,p1=A.rewrite(H,H.H,'expected_open',A.edits(H.CONTEXT_RECIPES[1])+[
        ("regs[14] = 0x20D82A4; lower(FAST, r['open_fast_value'])",
         "regs[14] = 0x20D82A4; fast=expected_fast(r,regs,status=0 if r['variant']=='status_zero' else 16);calls.append(fast['send']);regs[:]=fast['returned']",1)],
         dict(expected_convert=H.expected_convert,expected_fast=expected_fast),'fs_open_caller')
    opened,p2=A.rewrite(H,H.H,'require_open',A.edits(H.CONTEXT_RECIPES[2])+[
        ("['FSi_FindPath', 'FS_OpenFileFast']","['FSi_FindPath', 'FSi_SendCommand']",1),
        ("('FS_InitFile', 'FS_OpenFile', 'FS_ConvertPathToFileID')",
         "('FS_InitFile', 'FS_OpenFile', 'FS_ConvertPathToFileID', 'FS_OpenFileFast')",1),
        ("after = struct.pack('<II', ARC, 140) + struct.pack('<II', 0x210F198, 0x2007353) + before[16:]",
         "after = open_after(struct.pack('<II', ARC, 140) + struct.pack('<II', 0x210F198, 0x2007353) + before[16:],0 if r['variant']=='status_zero' else 16)",1),
        ('Open exact by-value ID8 and saved pair8; original frame136 unchanged',
         'Open exact by-value ID8/saved pair8 and four native Fast file fields',1)],
         dict(require_init_native=H.require_outer_init,expected_open=predicted,DIR=DIR,open_after=open_after),'fs_open_caller')
    converted=binding(H.require_convert,dict(require_open=opened))
    return predicted,opened,converted,[p1,p2]


predict_open,require_open,require_convert,CONTEXT_RECIPES=context_bindings()
parent_off=binding(H.require_parent_off,dict(require_open=require_open))
convert_off=binding(H.require_off_pair,dict(require_parent_off=parent_off,require_convert=require_convert))


def native_binding():
    edits=A.edits(H.NATIVE_RECIPE)+[
        ('FS_OpenFileFast','FSi_SendCommand',5),
        ("('FSi_SendCommand',0x20D82A4,[ARC,140],[file,310,c6,c7],None)",
         "('FSi_SendCommand',0x20D8244,[6,140],[file,310,c6,c7],None)",1),
        ("else ID if name=='FSi_SendCommand' else local","else SP if name=='FSi_SendCommand' else local",1),
        ("for pc,offset,value in INNER_STORES:store(pc,DIR+offset,4,value)",
         "for pc,offset,value in INNER_STORES:store(pc,DIR+offset,4,value)\n push(0x20D8208,TOP-168,[file,ARC,140,0])\n push(0x20D820C,SP,[file,0x20D82A4])\n for pc,offset,value in ((0x20D822C,8,ARC),(0x20D8230,48,ARC),(0x20D823C,52,140),(0x20D8268,12,STATUS)):store(pc,file+offset,4,value)",1),
        ('len(expected)==23+len(STORES)+len(INNER_STORES)','len(expected)==33+len(STORES)+len(INNER_STORES)',1)]
    return A.rewrite(H,R,'require_case',edits,
        dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=H.H.H.COOKIES,IP=H.H.H.IP,STORES=H.H.O.STORES,
            INNER_STORES=H.H.O.STORES,SDK=SDK,DIR=DIR,ID=ID,SP=SP,ARC=ARC,FAST_VALUE=1,FIND_VALUE=1,STATUS=16,
            EXPECTED_HOOKS=197,EXPECTED_PC_COUNT=172),'narc_reader')


require_native,NATIVE_RECIPE=native_binding()
parent_case,PARENT_CASE_RECIPE=A.rewrite(H,H,'require_case',[
    ("**q['fs_convert_code']}","**q['fs_convert_code'],**q['fs_fast_code']}",1)],
    dict(require_convert=require_convert,require_native=require_native),'fs_convert_caller')


def fast_code(q):return {**H.positive_code(q),**q['fs_fast_code']}


def require_fast(r,data,status=16):
    need(status in(0,16)and r['find_value']==r['open_fast_value']==1,'Fast finite composed lower policies')
    out=r['fs_fast'];p=r['pp_reader'];want=expected_fast(r,status=status)
    need(out['entry']==want['entry']and out['returned']==want['returned']and out['flow']==want['flow'],
        'Fast complete native aggregate, status, conditional effects and ARM return flow')
    require_convert(r,data)
    before=bytes.fromhex(r['convert']['frame_after']);after=bytearray(before)
    values=[FILE,RETURN,FILE,ARC,140,0];after[SP-DIR:ID-DIR]=struct.pack('<6I',*values)
    prior_file=before[FILE-DIR:FILE-DIR+72];after[FILE-DIR:FILE-DIR+72]=file_after(prior_file,status)
    need(out['frame_before']==before.hex()and out['frame_after']==after.hex()and
        out['file_before']==prior_file.hex()and out['file_after']==file_after(prior_file,status).hex(),
        'Fast24 reuses dead Convert directory tail/saved words; exact four live FSFile fields')
    stores=[];image=bytearray(before)
    sequence=[(ENTRY,TOP-168+4*i,v)for i,v in enumerate((FILE,ARC,140,0))]+[
        (0x20D820C,SP+4*i,v)for i,v in enumerate((FILE,RETURN))]+[
        (pc,FILE+offset,v)for pc,offset,v in((0x20D822C,8,ARC),(0x20D8230,48,ARC),(0x20D823C,52,140),(0x20D8268,12,status))]
    for pc,address,value in sequence:
        i=address-DIR;stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(image[i:i+4]).hex(),value=value))
        struct.pack_into('<I',image,i,value)
    need(image==after and out['stores']==(stores if r['observe']else[]),'Fast ordered six spill and four field native stores')
    reads=[dict(pc=hex(pc),address=SP+offset,bytes=4,hex=struct.pack('<I',value).hex())
        for pc,offset,value in((0x20D8210,12,ARC),(0x20D8234,16,140))]
    need(out['reads']==reads,'Fast native loads consume spilled by-value archive and file ID')
    model=p['models'][1];send_file=bytearray(prior_file)
    for offset,value in((8,ARC),(48,ARC),(52,140)):struct.pack_into('<I',send_file,offset,value)
    need(model['name']=='FSi_SendCommand'and model['entry']==want['send']['entry']and
        model['returned']==want['send']['returned']and model['file_before_hex']==send_file.hex(),
        'Send observes actual three native aggregate fields before native status update')
    need(out['ledger_before']==r['convert']['ledger_after']and out['ledger_after']==r['fs_open']['ledger_after'],
        'Only modeled Send opens host archive; native file layout effects remain distinct')
    shadows=[]
    if status==0:
        pre=next(e['regs']for e in want['flow']if e['pc']=='0x20d8268');post=list(pre);post[1]=0
        shadows=[dict(pc='0x20d8268',before=pre,after=post,
            reason='R1 status16 to0 only before native FILE.stat store; Send ledger remains open')]
    need(out['shadows']==shadows,'Fast finite status-only shadow after actual ORR/BIC')
    return True


def require_case(r,data,q):
    need(r['variant']=='current','positive Fast has no status shadow')
    require_fast(r,data);native=A.clone(require_native,dict(FAST_VALUE=r['send_value']))
    parent=A.clone(parent_case,dict(require_native=native));parent(r,data,q)
    return True


def require_off_pair(on,off,data):
    parent=convert_off(on,off,data);require_fast(on,data);require_fast(off,data)
    need(on['send_value']==off['send_value']==1 and off['fs_fast']['stores']==[]and
        {k:v for k,v in on['fs_fast'].items()if k!='stores'}=={k:v for k,v in off['fs_fast'].items()if k!='stores'},
        'Fast OFF retains all file fields, spilled words, register flow and actual memory; only store log disabled')
    return dict(neutral=True,parent=parent,scope='NativeFast24 spill/fourFSFile words equal OFF/ON; no new mask or allocation')


def source_identities():
    result=H.source_identities()
    for p in(__file__,A.__file__):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
    return result


def counter_record(r,data,q):
    disguised=copy.deepcopy(r);disguised['variant']='current';disguised['fs_fast']['shadows']=[]
    try:require_case(disguised,data,q)
    except ValueError as error:return dict(variant=r['variant'],result=r,rejection=str(error),tag_disguised=True)
    raise ValueError('Fast status counter accepted')


def require_counter(counter,normal,data,q):
    require_case(normal,data,q);r=counter['result']
    need(counter['variant']==r['variant']=='status_zero'and r['plus']==normal['plus']==1 and
        r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['observe']is True and
        r['pp_clobber']is False and r['send_value']==normal['send_value']==1 and r['pp_shadows']==[],
        'Fast counter finite original fixture and status-only policy')
    require_fast(r,data,0);H.H.H.require_pp_context(r,data)
    a,b=normal['pp_reader'],r['pp_reader'];allowed={'native_writes','stack_frame_hex','ram_sha256','stack240_after','stack152_after','projected_ram_sha256'}
    need({k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in b.items()if k not in allowed}and
        r['fs_init']==normal['fs_init']and r['convert']==normal['convert']and r['pp_binding']==normal['pp_binding'],
        'Fast counter same complete prestate, all models and outer Init/Convert observations')
    writes=copy.deepcopy(a['native_writes']);indices=[i for i,e in enumerate(writes)if e['pc']=='0x20d8268'and e['address']==FILE+12]
    need(len(indices)==1,'one native Fast file status store');writes[indices[0]]['value']=0
    need(b['native_writes']==writes,'Fast counter changes only one native status store value')
    for key,base in(('stack240_after',DIR),('stack152_after',ID),('stack_frame_hex',TOP-136)):
        frame=bytearray.fromhex(a[key]);struct.pack_into('<I',frame,FILE+12-base,0)
        need(b[key]==frame.hex(),'Fast counter exact one status word across linked frame views')
    need(b['ram_sha256']!=a['ram_sha256']and b['projected_ram_sha256']!=a['projected_ram_sha256'],
        'Fast counter phase RAM differs despite unchanged final caller output')
    native=A.clone(require_native,dict(STATUS=0));native(b,data['pp_reader'],fast_code(q),T.expected(data['constructor'],1)[0]['ot_draws'][-1])
    replay=copy.deepcopy(r);replay['variant']='current';H.H.H.require_earlier(replay,data,q)
    need(all(r[k]==normal[k]for k in('instructions','mon_hex','prefix','seed_after','pp_flow','pp_stores','pp_checkpoint',
        'names','raw_ram_sha256','functional_ram_sha256','guard8_global_before','guard8_global_after')),
        'Fast status counter retains all names and whole final RAM without any added projection')
    actual=counter_record(r,data,q)
    need(counter['tag_disguised']is True and counter['rejection']==actual['rejection']==
        'Fast complete native aggregate, status, conditional effects and ARM return flow',
        'Fast status counter specifically rejected when disguised as positive')
    return True

def analyze(rom, language, objects, strategy_object, readback_only=False):
    import mmap, unicorn
    R.W.require_host_budget(); sources = source_identities()
    model = P.G.S.SHARED.read_current(rom, language)
    with rom.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
        q, proof = qualify(model,raw,language,objects,strategy_object)
        result = dict(schema='trainer31-native-fs-fast-v1',language=language,input=model['record'],
            source_sha256=sources,proof=proof,recipes=[RUN_RECIPE,*CONTEXT_RECIPES,NATIVE_RECIPE,PARENT_CASE_RECIPE],namespace_bindings=BINDINGS,cpu_executed=False,
            conditional_policy=dict(unicorn_version=unicorn.__version__,cpu_model=17,
                false_EQ_hook=True,fast_false_EQ_hooks=8,scope='code-hook delivery; false ARM effects remain suppressed'))
        if not readback_only:
            data = H.H.O.resources(model,raw,language)
            positives, guards, controls, off, counters = [], [], [], [], []
            for plus in (0,1):
                for seed in (0x12345678,0x12345679):
                    r = run_case(model,raw,language,q,data,plus,seed)
                    require_case(r,data,q); positives.append(r)
                    print(language,'native Fast caller',plus,hex(seed),'verified',flush=True)
                r = run_case(model,raw,language,q,data,plus,0x12345678,observe=False)
                off.append(dict(result=r,proof=require_off_pair(positives[-2],r,data)))
            normal = next(r for r in positives if r['plus']==1 and r['seed']==0x12345678)
            r = run_case(model,raw,language,q,data,1,0x12345678,poison=0x39)
            require_case(r,data,q); need(r['mon_hex']==normal['mon_hex'],'Fast alternate preimage fill changes party'); guards.append(r)
            for kwargs in (dict(pp_clobber=True),dict(send_value=2)):
                r = run_case(model,raw,language,q,data,1,0x12345678,**kwargs)
                require_case(r,data,q)
                need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and
                     r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and
                     r['pp_reader']['ram_sha256']==normal['pp_reader']['ram_sha256'],
                     'Fast lower volatile/noncanonical truthy policy preserves output and phase RAM')
                controls.append(r)
            r = run_case(model,raw,language,q,data,1,0x12345678,variant='status_zero')
            counter = counter_record(r,data,q); require_counter(counter,normal,data,q); counters.append(counter)
            result.update(cpu_executed=True,positives=positives,guards=guards,volatile_controls=controls,
                observer_off=off,counters=counters,resources=dict(pp=data['pp_reader']['11']['oracle']),
                limits=['Initialized trainer31 caller and selected custom PP310 Open only',
                        'Native Init/Open/Convert/Fast wrappers; FindPath/SendCommand plus Seek/Read/Close are explicit models',
                        'Opaque ARC token is not native FSArchive state; no invented FSFile fields',
                        'Counter changes only native FILE.stat16 to0 after successful modeled Send, not an SDK command failure',
                        'Exact240-byte frame/56-byte actual guard including8 unmasked readonly bytes; guestglobal560 within608; heap1124B OFF projection only',
                        'Recovered assembly bytes do not reconstruct original SDK compiler provenance',
                        'No natural encounter/full battle/UI/SAVE/cold/hardware or performance claim'])
        need(source_identities()==sources,'Fast sources changed during campaign'); R.W.require_host_budget()
    return result


def main():
    import argparse,json,gzip
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('rom','objects','strategy-object','json'): parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True)
    parser.add_argument('--readback-only',action='store_true')
    args = parser.parse_args()
    try:
        need(not args.json.exists() and not args.json.is_symlink() and P.SOURCE not in args.json.resolve().parents,
             'fresh private output outside source required')
        result = analyze(args.rom,args.language,args.objects,args.strategy_object,args.readback_only)
        payload = json.dumps(result,separators=(',',':')).encode(); need(len(payload)<=32*1024**2,'Fast expanded report budget')
        blob = gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload
        need(len(blob)<=8*1024**2,'Fast stored report budget')
        args.json.parent.mkdir(parents=True,exist_ok=True)
        with args.json.open('xb')as f:f.write(blob)
    except ValueError as error: parser.exit(2,str(error)+'\n')
    print(args.language,'Fast readback verified' if args.readback_only else 'native Fast caller and explicit lower models verified')


if __name__=='__main__':main()
