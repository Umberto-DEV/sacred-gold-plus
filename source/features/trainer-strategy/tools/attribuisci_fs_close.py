#!/usr/bin/env python3
"""Native Close cleanup with distinct open6/close8 SendCommand model roles.

Native LR/R1/flags propagate through the actual parser and borrowed PP caller.
"""
from pathlib import Path
import importlib.util,struct,types,copy


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('fs_close_fast_parent',Path(__file__).with_name('attribuisci_fs_fast.py'))
A=load('fs_close_profile',Path(__file__).parents[1]/'test/fs_close_bench.py');A.bind(H)
R,P,B,T,need,sha=H.R,H.P,H.B,H.T,H.need,H.sha
TOP,DEST,STOP,FILE,ID,ARC,DIR=H.TOP,H.DEST,H.STOP,H.FILE,H.ID,H.ARC,H.DIR
ENTRY,END,RETURN,SEND,SP=0x20D82C0,0x20D82FC,0x2007408,H.SEND,TOP-144
CLOSE_SHA='b6264f39c82988fab2b720bff3277219d7d9bb14d4ed0abe768d4f1f561b2e26'
SDK={a:n for a,n in H.SDK.items()if a!=ENTRY}
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_CPSR
BINDINGS=[]


def binding(fn,namespace):
    BINDINGS.append(dict(parent_source_sha256=A.PARENT_SHA256,function=fn.__qualname__,code_unchanged=True,namespace=sorted(namespace)))
    return A.clone(fn,namespace)


def qualify(model,raw,*args):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
    q,proof=H.qualify(model,raw,*args);view=P.G.S.SHARED.gifts_audit.Arm9View(raw);blob=view.read(ENTRY,60)
    need(sha(blob)==CLOSE_SHA and blob==P.G.piece(model['segments'],ENTRY,60),'Close raw/decoded identity')
    code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(blob,ENTRY))
    need(len(code)==15 and [i.address for i in code]==list(range(ENTRY,END,4))and
        {i.address:i.op_str for i in code if i.mnemonic=='bl'}=={0x20D82CC:'#0x20d7788'},'Close ARM extent and Send target')
    q['fs_close_code']={i.address:(4,False)for i in code}
    proof['native_fs_close']=dict(ram=hex(ENTRY),rom_offset=hex(view.offset(ENTRY,60)),bytes=60,sha256=sha(blob),
        starts=15,close_frame=8,reader_peak=240,guest_global_peak=560,full_bound=608,
        file_fields=[8,16,12],send_command=8,model='Send closes only host ledger; native cleanup remains observed')
    return q,proof


class CloseObserver:
    def __init__(self,driver,reader):
        self.driver,self.reader,self.active=driver,reader,False
        self.result=dict(entry=None,returned=None,frame_before=None,frame_after=None,file_before=None,file_after=None,
            flow=[],stores=[],shadows=[],ledger_before=None,ledger_after=None)
        self.parent_step,self.parent_write,self.base_service=reader.step,reader.write,reader.service
        self.root_step=types.MethodType(root_step,reader);self.root_write=driver.convert_observer.native_write
        reader.code={**reader.code,**driver.qualified['fs_close_code']}
        reader.step,reader.write,reader.service=self.step,self.write,self.service

    def step(self,u,pc,n,user):
        r,out=self.reader,self.result
        if pc==ENTRY:
            need(out['entry']is None and not self.driver.fast_observer.active and r.open and r.file==FILE,
                'single selected Close after seven reads and native Fast')
            self.active=True;out.update(entry=r.regs(),frame_before=r.read_bytes(DIR,240).hex(),
                file_before=r.read_bytes(FILE,72).hex(),ledger_before=self.driver.convert_observer.ledger())
        if self.active and pc==RETURN:
            out.update(returned=r.regs(),frame_after=r.read_bytes(DIR,240).hex(),file_after=r.read_bytes(FILE,72).hex(),
                ledger_after=self.driver.convert_observer.ledger());self.active=False
        if self.active:
            if ENTRY<=pc<END:out['flow'].append(dict(pc=hex(pc),regs=r.regs()))
            self.root_step(u,pc,n,user)
            if pc==0x20D82DC and self.driver.close_variant=='arc_not_cleared':
                before=r.regs();need(before[0]==0 and before[4]==FILE and before[13:15]==[SP,0x20D82D0]and not r.open,
                    'Close arc-only shadow after successful modeled close')
                u.reg_write(B.R[0],ARC);out['shadows'].append(dict(pc=hex(pc),before=before,after=r.regs(),
                    reason='R0 zero to original archive token only before native FILE.arc store; host ledger remains closed'))
            return
        self.parent_step(u,pc,n,user)

    def write(self,u,access,address,n,value,user):
        if self.active:
            pc=u.reg_read(UC_ARM_REG_PC)
            need((SP<=address and address+n<=TOP-136)or(FILE<=address and address+n<=FILE+72),
                'Close writes only its saved pair and live file')
            if self.reader.observe:self.result['stores'].append(dict(pc=hex(pc),address=address,bytes=n,
                before=self.reader.read_bytes(address,n).hex(),value=value))
            self.root_write(u,access,address,n,value,user);return
        self.parent_write(u,access,address,n,value,user)

    def service(self,pc):
        if pc!=SEND or not self.active:return self.base_service(pc)
        r,u=self.reader,self.reader.u;before=r.regs();args=before[:4];sp,lr=before[13:15]
        resource=r.data['11'];oracle=resource['oracle']
        need(sp==SP and lr==0x20D82D0 and not before[15]&32 and r.initialized and r.file==FILE and
            args[0:2]==[FILE,8]and r.path=='a/0/1/1'and r.open and r.archive==resource['raw']and
            r.cursor==oracle['member_archive_offset']+oracle['member_bytes']and r.read_count==7 and
            r.read_bytes(FILE+8,4)==struct.pack('<I',ARC)and r.read_bytes(FILE+12,8)==struct.pack('<II',16,14)and
            r.read_bytes(FILE+48,8)==struct.pack('<II',ARC,140),
            'Send close8 sees actual native file, complete read cursor and open lifetime')
        event=dict(name=SDK[SEND],pc=hex(pc),args=args,sp=sp,lr=hex(lr),saved=before[4:12],cursor_before=r.cursor,
            open_before=True,entry=before,path=r.path,archive_bytes=len(r.archive),archive_sha256=sha(r.archive),
            native_FSFile_layout_modeled=False,opaque_archive_token=ARC,file_id=140,
            file_before_hex=r.read_bytes(FILE,72).hex(),command=8)
        r.open=False
        if r.clobber:
            for i in(1,2,3,12):u.reg_write(B.R[i],0xA5000000+i)
            u.reg_write(UC_ARM_REG_CPSR,(u.reg_read(UC_ARM_REG_CPSR)&0x0FFFFFFF)|0xA0000000)
        u.reg_write(B.R[0],self.driver.close_value);u.reg_write(UC_ARM_REG_PC,lr);after=r.regs()
        need(after[13]==sp and after[4:12]==before[4:12]and not after[15]&32 and
            r.read_bytes(FILE,72).hex()==event['file_before_hex'],'Send close ARM return without invented guest cleanup')
        event.update(result_r0=self.driver.close_value,return_sp=after[13],return_saved=after[4:12],
            return_volatile=[after[i]for i in(1,2,3,12)],cursor_after=r.cursor,open_after=False,returned=after)
        r.models.append(event)


class Driver(H.Driver):
    def __init__(self,*args,variant='current',close_value=1,**kwargs):
        need(variant in('current','arc_not_cleared')and type(close_value)is int and close_value in(1,2)and
            (variant=='current'or close_value==1),'finite Close controls')
        super().__init__(*args,variant='current',**kwargs)
        self.close_variant,self.close_value,self.close_result=variant,close_value,None

    def start_pp(self):
        super().start_pp();regs=self.regs();before=self.read_bytes(0x2000000,0x400000)
        self.close_observer=CloseObserver(self,self.pp_reader);self.close_result=self.close_observer.result
        need(regs==self.regs()and before==self.read_bytes(0x2000000,0x400000),'Close attachment changed guest state')


root_step=binding(H.root_step,dict(SDK=SDK))
run_case,RUN_RECIPE=A.rewrite(H,H.H.H.H.V,'run_case',A.edits(H.RUN_RECIPE)+[
    ('send_value=1):','send_value=1,close_value=1):',1),
    ('send_value=send_value)','send_value=send_value,close_value=close_value)',1),
    ('return dict(fs_fast=','return dict(fs_close=driver.close_result,close_value=driver.close_value,fs_fast=',1)],
    dict(Driver=Driver,A=H.H.H.H.A,TOP=TOP,NAME_ARENA=H.H.H.H.X.NAME_ARENA,NAME_END=H.H.H.H.X.NAME_END),'message_caller')


def expected_close(r,data,arc=0):
    need(arc in(0,ARC)and type(r['close_value'])is int and r['close_value']in(1,2)and type(r['pp_clobber'])is bool,
        'finite Close field and backend policy')
    o=data['pp_reader']['11']['oracle'];clobber=r['pp_clobber'];v=[0xA5000000+i for i in(1,2,3,12)]
    start=[FILE,v[0]if clobber else DEST,v[1]if clobber else o['member_bytes'],v[2]if clobber else 0,
        o['btaf']+12,310,o['btnf'],o['btnf_bytes']]+list(H.H.H.H.N.COOKIES[4:])+[
        v[3]if clobber else 0,TOP-136,0x2007409,0xA000001F if clobber else 0x2000001F]
    regs=list(start);flow=[];send=None
    for pc in range(ENTRY,END,4):
        flow.append(dict(pc=hex(pc),regs=list(regs)))
        if pc==ENTRY:regs[13]-=8
        elif pc==0x20D82C4:regs[1]=8
        elif pc==0x20D82C8:regs[4]=FILE
        elif pc==0x20D82CC:
            regs[14]=0x20D82D0;before=list(regs)
            if clobber:
                for i in(1,2,3,12):regs[i]=0xA5000000+i
                regs[15]=0xA000001F
            regs[0]=r['close_value'];send=dict(pc=hex(SEND),entry=before,returned=list(regs))
        elif pc==0x20D82D0:regs[15]=0x2000001F
        elif pc==0x20D82D4:regs[0]=0
        elif pc==0x20D82DC:regs[0]=arc
        elif pc==0x20D82E0:regs[0]=14
        elif pc==0x20D82E8:regs[1]=16
        elif pc==0x20D82EC:regs[0]=1
        elif pc==0x20D82F0:regs[1]&=~48
        elif pc==0x20D82F8:regs[4]=start[4];regs[13]+=8;regs[15]|=32
    return dict(entry=start,flow=flow,send=send,returned=regs)


def native_binding():
    edits=A.edits(H.NATIVE_RECIPE)+[
        ('end[14]==0x2007409','end[14]==0x20D82D0',1),
        ('[1,volatile[0] if clobber else DEST,volatile[1] if clobber else size,cookie3]',
         '[1,0,volatile[1] if clobber else size,cookie3]',1),
        ('end[15]==(0xA000003F if clobber else 0x2000003F)','end[15]==0x2000003F',1),
        ("('FS_CloseFile',0x2007409,volatile[:2] if clobber else [DEST,size],[o['btaf']+12,310,o['btnf'],o['btnf_bytes']],None)",
         "('FSi_SendCommand',0x20D82D0,[8,volatile[1] if clobber else size],[file,310,o['btnf'],o['btnf_bytes']],None)",1),
        ("name!='FSi_SendCommand'","lr!=0x20D8244",1),
        ("else FAST_VALUE if name=='FSi_SendCommand'","else CLOSE_VALUE if lr==0x20D82D0 else FAST_VALUE if name=='FSi_SendCommand'",1),
        ("else SP if name=='FSi_SendCommand' else local","else SP if lr==0x20D8244 else CLOSE_SP if lr==0x20D82D0 else local",1),
        ("elif name=='FSi_SendCommand':need(","elif name=='FSi_SendCommand' and lr==0x20D8244:need(",1),
        ("elif name=='FS_CloseFile':opened=False",
         "elif name=='FSi_SendCommand' and lr==0x20D82D0:need(event['command']==8,'Close role uses command8');opened=False",1),
        ('store(0x20073EE,local+20,4,size)',
         "store(0x20073EE,local+20,4,size)\n push(0x20D82C0,CLOSE_SP,[o['btaf']+12,0x2007409])\n for pc,offset,value in ((0x20D82DC,8,CLOSE_ARC),(0x20D82E4,16,14),(0x20D82F4,12,0)):store(pc,file+offset,4,value)",1),
        ('len(expected)==33+len(STORES)+len(INNER_STORES)','len(expected)==38+len(STORES)+len(INNER_STORES)',1)]
    return A.rewrite(H,R,'require_case',edits,
        dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=H.H.H.H.COOKIES,IP=H.H.H.H.IP,
            STORES=H.H.H.O.STORES,INNER_STORES=H.H.H.O.STORES,SDK=SDK,DIR=DIR,ID=ID,SP=H.SP,CLOSE_SP=SP,
            ARC=ARC,FAST_VALUE=1,FIND_VALUE=1,STATUS=16,CLOSE_VALUE=1,CLOSE_ARC=0,
            EXPECTED_HOOKS=212,EXPECTED_PC_COUNT=187),'narc_reader')


require_native,NATIVE_RECIPE=native_binding()
parent_case,PARENT_CASE_RECIPE=A.rewrite(H,H.H,'require_case',A.edits(H.PARENT_CASE_RECIPE)+[
    ("**q['fs_fast_code']}","**q['fs_fast_code'],**q['fs_close_code']}",1)],
    dict(require_convert=H.require_convert,require_native=require_native),'fs_convert_caller')
parent_positive=binding(H.require_case,dict(parent_case=parent_case,require_native=require_native))


def close_code(q):return {**H.fast_code(q),**q['fs_close_code']}


def cleanup_file(blob,arc=0):
    out=bytearray(blob);need(len(out)==72 and arc in(0,ARC),'Close FSFile preimage and arc domain')
    for offset,value in((8,arc),(16,14),(12,0)):struct.pack_into('<I',out,offset,value)
    return bytes(out)


def require_close(r,data,arc=0):
    need(r['send_value']==r['find_value']==r['open_fast_value']==1,'Close preserves earlier backend policies')
    out,p=r['fs_close'],r['pp_reader'];want=expected_close(r,data,arc)
    need(out['entry']==want['entry']and out['returned']==want['returned']and out['flow']==want['flow'],
        'Close complete native cleanup, conditional effects and residual LR/R1/flags flow')
    H.require_fast(r,data)
    before=bytearray.fromhex(r['fs_fast']['frame_after']);resource=data['pp_reader']['11'];raw=resource['raw']
    for event in p['models']:
        if event['name']=='FS_ReadFile'and event['destination']!=DEST:
            a=event['destination']-DIR;n=event['delivered_bytes'];blob=raw[event['position']:event['position']+n]
            before[a:a+n]=blob
    struct.pack_into('<I',before,TOP-116-DIR,resource['oracle']['member_bytes'])
    prior_file=bytes(before[FILE-DIR:FILE-DIR+72]);after=bytearray(before);stores=[]
    sequence=[(ENTRY,SP+4*i,v)for i,v in enumerate((want['entry'][4],0x2007409))]+[
        (pc,FILE+off,value)for pc,off,value in((0x20D82DC,8,arc),(0x20D82E4,16,14),(0x20D82F4,12,0))]
    for pc,address,value in sequence:
        i=address-DIR;stores.append(dict(pc=hex(pc),address=address,bytes=4,before=bytes(after[i:i+4]).hex(),value=value))
        struct.pack_into('<I',after,i,value)
    need(out['frame_before']==before.hex()and out['frame_after']==p['stack240_after']==after.hex()and
        out['file_before']==prior_file.hex()and out['file_after']==cleanup_file(prior_file,arc).hex(),
        'Close reuses dead Open saved pair and changes exactly three file words; other60 bytes preserved')
    need(out['stores']==(stores if r['observe']else[]),'Close two saved words and three native stores including idempotent command14')
    model=p['models'][-1]
    need(model['name']=='FSi_SendCommand'and model['command']==8 and model['entry']==want['send']['entry']and
        model['returned']==want['send']['returned']and model['file_before_hex']==prior_file.hex(),
        'Close second Send role sees native Fast state and full actual ARM command8 context')
    ledger=dict(initialized=True,file=FILE,open=True,cursor=resource['oracle']['member_archive_offset']+resource['oracle']['member_bytes'],
        path='a/0/1/1',archive_sha256=sha(raw));closed=dict(ledger,open=False)
    need(out['ledger_before']==ledger and out['ledger_after']==closed,'Send close changes only host open lifetime, retains resource and cursor')
    shadows=[]
    if arc==ARC:
        pre=next(e['regs']for e in want['flow']if e['pc']=='0x20d82dc');post=list(pre);post[0]=ARC
        shadows=[dict(pc='0x20d82dc',before=pre,after=post,
            reason='R0 zero to original archive token only before native FILE.arc store; host ledger remains closed')]
    need(out['shadows']==shadows,'Close finite arc-only shadow before native store and after modeled close')
    return True


def require_case(r,data,q):
    need(r['variant']=='current'and r['pp_shadows']==[],'positive Close has no arc shadow')
    require_close(r,data);native=A.clone(require_native,dict(CLOSE_VALUE=r['close_value']))
    parent=A.clone(parent_positive,dict(require_native=native));parent(r,data,q)
    return True


def require_off_pair(on,off,data):
    parent=H.require_off_pair(on,off,data);require_close(on,data);require_close(off,data)
    need(on['close_value']==off['close_value']==1 and off['fs_close']['stores']==[]and
        {k:v for k,v in on['fs_close'].items()if k!='stores'}=={k:v for k,v in off['fs_close'].items()if k!='stores'},
        'Close OFF actual file cleanup/saved pair/ARMThumb flow equal; only native store log disabled')
    return dict(neutral=True,parent=parent,scope='ClosePUSH8/three native file words equal OFF/ON; same240/guard/global608/heap1124 projections')


def source_identities():
    result=H.source_identities()
    for p in(__file__,A.__file__):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
    return result


def counter_record(r,data,q):
    disguised=copy.deepcopy(r);disguised['variant']='current';disguised['fs_close']['shadows']=[]
    try:require_case(disguised,data,q)
    except ValueError as error:return dict(variant=r['variant'],result=r,rejection=str(error),tag_disguised=True)
    raise ValueError('Close arc counter accepted')


def require_counter(counter,normal,data,q):
    require_case(normal,data,q);r=counter['result']
    need(counter['variant']==r['variant']=='arc_not_cleared'and r['plus']==normal['plus']==1 and
        r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['observe']is True and
        r['pp_clobber']is False and r['close_value']==normal['close_value']==1 and r['pp_shadows']==[],
        'Close counter finite fixture and arc-only shadow after modeled closure')
    require_close(r,data,ARC);H.H.H.H.require_pp_context(r,data)
    a,b=normal['pp_reader'],r['pp_reader'];allowed={'native_writes','stack_frame_hex','ram_sha256','stack240_after','stack152_after','projected_ram_sha256'}
    need({k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in b.items()if k not in allowed}and
        all(r[k]==normal[k]for k in('fs_init','convert','fs_open','fs_fast','pp_binding')),
        'Close counter preserves full prestate, both Send roles, all earlier native owners and return ABI')
    writes=copy.deepcopy(a['native_writes']);indices=[i for i,e in enumerate(writes)if e['pc']=='0x20d82dc'and e['address']==FILE+8]
    need(len(indices)==1,'one Close native archive clear store');writes[indices[0]]['value']=ARC
    need(b['native_writes']==writes,'Close counter one native arc word store differs')
    for key,base in(('stack240_after',DIR),('stack152_after',ID),('stack_frame_hex',TOP-136)):
        frame=bytearray.fromhex(a[key]);struct.pack_into('<I',frame,FILE+8-base,ARC)
        need(b[key]==frame.hex(),'Close counter one archive word across three linked final frames')
    need(b['ram_sha256']!=a['ram_sha256']and b['projected_ram_sha256']!=a['projected_ram_sha256'],
        'Close counter phase RAM exposes uncleared archive without added projection')
    native=A.clone(require_native,dict(CLOSE_ARC=ARC));native(b,data['pp_reader'],close_code(q),T.expected(data['constructor'],1)[0]['ot_draws'][-1])
    replay=copy.deepcopy(r);replay['variant']='current';H.H.H.H.require_earlier(replay,data,q)
    need(all(r[k]==normal[k]for k in('instructions','mon_hex','prefix','seed_after','pp_flow','pp_stores','pp_checkpoint',
        'names','raw_ram_sha256','functional_ram_sha256','guard8_global_before','guard8_global_after')),
        'Close counter retains complete PP flow, all names and whole final RAM despite missing native cleanup')
    actual=counter_record(r,data,q)
    need(counter['tag_disguised']is True and counter['rejection']==actual['rejection']==
        'Close complete native cleanup, conditional effects and residual LR/R1/flags flow',
        'Close counter specifically rejected as disguised positive native flow')
    return True

def analyze(rom, language, objects, strategy_object, readback_only=False):
    import mmap, unicorn
    R.W.require_host_budget(); sources = source_identities()
    model = P.G.S.SHARED.read_current(rom, language)
    with rom.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
        q, proof = qualify(model,raw,language,objects,strategy_object)
        result = dict(schema='trainer31-native-fs-close-v1',language=language,input=model['record'],
            source_sha256=sources,proof=proof,recipes=[RUN_RECIPE,NATIVE_RECIPE,PARENT_CASE_RECIPE],namespace_bindings=BINDINGS,cpu_executed=False,
            conditional_policy=dict(unicorn_version=unicorn.__version__,cpu_model=17,
                false_EQ_hook=True,fast_false_EQ_hooks=8,close_false_EQ_hooks=1,scope='code-hook delivery; false ARM effects remain suppressed'))
        if not readback_only:
            data = H.H.H.O.resources(model,raw,language)
            positives, guards, controls, off, counters = [], [], [], [], []
            for plus in (0,1):
                for seed in (0x12345678,0x12345679):
                    r = run_case(model,raw,language,q,data,plus,seed)
                    require_case(r,data,q); positives.append(r)
                    print(language,'native Close caller',plus,hex(seed),'verified',flush=True)
                r = run_case(model,raw,language,q,data,plus,0x12345678,observe=False)
                off.append(dict(result=r,proof=require_off_pair(positives[-2],r,data)))
            normal = next(r for r in positives if r['plus']==1 and r['seed']==0x12345678)
            r = run_case(model,raw,language,q,data,1,0x12345678,poison=0x39)
            require_case(r,data,q); need(r['mon_hex']==normal['mon_hex'],'Close alternate preimage fill changes party'); guards.append(r)
            for kwargs in (dict(pp_clobber=True),dict(close_value=2)):
                r = run_case(model,raw,language,q,data,1,0x12345678,**kwargs)
                require_case(r,data,q)
                need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and
                     r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and
                     r['pp_reader']['ram_sha256']==normal['pp_reader']['ram_sha256'],
                     'Close lower volatile/noncanonical truthy policy preserves output and phase RAM')
                controls.append(r)
            r = run_case(model,raw,language,q,data,1,0x12345678,variant='arc_not_cleared')
            counter = counter_record(r,data,q); require_counter(counter,normal,data,q); counters.append(counter)
            result.update(cpu_executed=True,positives=positives,guards=guards,volatile_controls=controls,
                observer_off=off,counters=counters,resources=dict(pp=data['pp_reader']['11']['oracle']),
                limits=['Initialized trainer31 caller and selected custom PP310 Open only',
                        'Native Init/Open/Convert/Fast/Close wrappers; FindPath/SendCommand plus Seek/Read are explicit models',
                        'Opaque ARC token is not native FSArchive state; no invented FSFile fields',
                        'Counter leaves native FILE.arc uncleared after successful modeled close8, not an SDK command failure',
                        'Exact240-byte frame/56-byte actual guard including8 unmasked readonly bytes; guestglobal560 within608; heap1124B OFF projection only',
                        'Recovered assembly bytes do not reconstruct original SDK compiler provenance',
                        'No natural encounter/full battle/UI/SAVE/cold/hardware or performance claim'])
        need(source_identities()==sources,'Close sources changed during campaign'); R.W.require_host_budget()
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
        payload = json.dumps(result,separators=(',',':')).encode(); need(len(payload)<=32*1024**2,'Close expanded report budget')
        blob = gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload
        need(len(blob)<=8*1024**2,'Close stored report budget')
        args.json.parent.mkdir(parents=True,exist_ok=True)
        with args.json.open('xb')as f:f.write(blob)
    except ValueError as error: parser.exit(2,str(error)+'\n')
    print(args.language,'Close readback verified' if args.readback_only else 'native Close caller and explicit lower models verified')


if __name__=='__main__':main()
