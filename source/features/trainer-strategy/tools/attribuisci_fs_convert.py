#!/usr/bin/env python3
"""Compose Native Convert and its distinct ARM-return Init into the PP caller.

FSi_FindPath is an explicit raw-FNT output model. The two FSFile objects and
the two invocations of the same Init code retain independent lifetimes.
"""
from pathlib import Path
import importlib.util,struct,types,copy


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


H=load('fs_convert_open_parent',Path(__file__).with_name('attribuisci_fs_open.py'))
A=load('fs_convert_profile',Path(__file__).parents[1]/'test/fs_convert_bench.py');A.bind(H)
R,P,B,T=H.R,H.P,H.B,H.T
need,sha=H.need,H.sha
TOP,DEST,STOP,FILE,ID,ARC=H.TOP,H.DEST,H.STOP,H.FILE,H.ID,H.ARC
ENTRY,END,RETURN,DIR=0x20D8180,0x20D81C0,0x20D828C,TOP-240
INIT,INIT_RETURN,FIND=H.O.ENTRY,0x20D8198,0x20D7FC0
CONVERT_SHA='8455d062eee662f58fefa731950eab06ecedb77279478b2ef41123ab5128d172'
SDK={a:name for a,name in H.SDK.items()if a!=H.CONVERT};SDK[FIND]='FSi_FindPath'
from unicorn.arm_const import UC_ARM_REG_PC


def qualify(model,raw,*args):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
    import unicorn
    need(unicorn.__version__=='2.1.4','Convert false-EQ hook policy requires qualified Unicorn2.1.4')
    q,proof=H.qualify(model,raw,*args)
    view=P.G.S.SHARED.gifts_audit.Arm9View(raw);blob=view.read(ENTRY,64)
    need(sha(blob)==CONVERT_SHA and blob==P.G.piece(model['segments'],ENTRY,64),'Convert raw/decoded identity')
    instructions=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(blob,ENTRY))
    need(len(instructions)==16 and [i.address for i in instructions]==list(range(ENTRY,END,4)) and
         all(i.size==4 for i in instructions),'Convert exact ARM extent')
    need({i.address:i.op_str for i in instructions if i.mnemonic=='bl'}==
         {0x20D8194:'#0x20d7f98',0x20D81A8:'#0x20d7fc0'},'Convert two nested ARM call targets')
    q['fs_convert_code']={i.address:(4,False)for i in instructions}
    proof['native_fs_convert']=dict(ram=hex(ENTRY),bytes=64,sha256=sha(blob),rom_offset=hex(view.offset(ENTRY,64)),
        starts=16,local_directory_bytes=72,new_frame_bytes=88,reader_peak=240,guest_global_peak=560,
        guest_full_bound=608,readonly_guard_global_extent=616,guard_extra8=[TOP-296,TOP-288],
        lower_model='FSi_FindPath; no native path/global/archive state reconstructed')
    return q,proof


class ConvertObserver:
    def __init__(self,driver,reader):
        self.driver,self.reader=driver,reader
        self.active=False;self.inner_active=False
        self.result=dict(entry=None,returned=None,frame_before=None,frame_after=None,flow=[],stores=[],
            ledger_before=None,ledger_after=None,inner_init=dict(entry=None,returned=None,before=None,after=None,
                frame_before=None,frame_after=None,flow=[],stores=[],shadows=[]))
        reader.code={**reader.code,**driver.qualified['fs_convert_code']}
        self.parent_step,self.parent_write,self.base_service=reader.step,reader.write,reader.service
        driver.fs_observer.base_step=types.MethodType(reader_step,reader)
        self.root_step=driver.fs_observer.base_step
        self.native_write=types.MethodType(reader_write,reader)
        reader.step,reader.write,reader.service=self.step,self.write,self.service

    def ledger(self):
        r=self.reader
        return dict(initialized=r.initialized,file=r.file,open=r.open,cursor=r.cursor,path=r.path,
                    archive_sha256=None if r.archive is None else sha(r.archive))

    def step(self,u,pc,n,user):
        r,out=self.reader,self.result;inner=out['inner_init']
        if pc==ENTRY:
            need(out['entry']is None and self.driver.open_observer.active and r.initialized and r.file==FILE and not r.open,
                 'single native Convert inside selected Open')
            self.active=True;out.update(entry=r.regs(),frame_before=r.read_bytes(DIR,240).hex(),ledger_before=self.ledger())
        if self.active and pc==INIT:
            regs=r.regs()
            need(inner['entry']is None and regs[0]==DIR and regs[13:15]==[DIR,INIT_RETURN] and not regs[15]&32,
                 'directory Init is distinct ARM invocation, never the outer file Init')
            self.inner_active=True
            inner.update(entry=regs,before=r.read_bytes(DIR,72).hex(),frame_before=r.read_bytes(DIR,240).hex())
        if self.inner_active and pc==INIT_RETURN:
            inner.update(returned=r.regs(),after=r.read_bytes(DIR,72).hex(),frame_after=r.read_bytes(DIR,240).hex())
            self.inner_active=False
        if self.active and pc==RETURN:
            need(not self.inner_active and inner['returned']is not None,'Convert returns after actual nested Init')
            out.update(returned=r.regs(),frame_after=r.read_bytes(DIR,240).hex(),ledger_after=self.ledger())
            self.active=False
        if self.active:
            if ENTRY<=pc<END:out['flow'].append(dict(pc=hex(pc),regs=r.regs()))
            if self.inner_active:inner['flow'].append(dict(pc=hex(pc),regs=r.regs()))
            # The outer Init observer must not consume this second invocation.
            self.root_step(u,pc,n,user)
            if self.inner_active and pc==0x20D7FB4 and self.driver.convert_variant=='directory_command_zero':
                before=r.regs()
                need(before[0]==DIR and before[1]==14 and before[13:15]==[DIR,INIT_RETURN],
                     'directory-only command shadow after native MOV14')
                u.reg_write(B.R[1],0)
                inner['shadows'].append(dict(pc='0x20d7fb4',before=before,after=r.regs(),
                    reason='inner directory command14 to0 only; outer Init and raw ID source unchanged'))
            return
        self.parent_step(u,pc,n,user)

    def write(self,u,access,address,n,value,user):
        if address<ID:
            need(self.active and DIR<=address and address+n<=ID,'new88 bytes belong only to active Convert')
            pc=u.reg_read(UC_ARM_REG_PC)
            if self.inner_active:
                need(DIR<=address and address+n<=DIR+72,'nested Init writes only its directory object')
                if self.reader.observe:
                    self.result['inner_init']['stores'].append(dict(pc=hex(pc),address=address,bytes=n,
                        before=self.reader.read_bytes(address,n).hex(),value=value,regs=self.reader.regs()))
            else:
                need(pc==ENTRY and DIR+72<=address and address+n<=ID,'Convert has only four native PUSH stores outside Init')
                if self.reader.observe:self.result['stores'].append(dict(pc=hex(pc),address=address,bytes=n,
                    before=self.reader.read_bytes(address,n).hex(),value=value))
            self.native_write(u,access,address,n,value,user);return
        self.parent_write(u,access,address,n,value,user)


class Driver(H.Driver):
    def __init__(self,*args,variant='current',find_value=1,**kwargs):
        need(variant in('current','directory_command_zero')and type(find_value)is int and find_value in(1,2)and
             (variant=='current'or find_value==1),'finite directory Convert controls')
        super().__init__(*args,variant='current',**kwargs)
        self.convert_variant,self.find_value,self.convert_result=variant,find_value,None

    def start_pp(self):
        super().start_pp();regs=self.regs();before=self.read_bytes(0x2000000,0x400000)
        self.convert_observer=ConvertObserver(self,self.pp_reader);self.convert_result=self.convert_observer.result
        need(regs==self.regs()and before==self.read_bytes(0x2000000,0x400000),'Convert attachment changed CPU/RAM')


def runtime_bindings():
    write,p1=A.rewrite(H,R,'Reader.write',[('TOP-136<=address','TOP-240<=address',1)],dict(TOP=TOP),'narc_reader')
    step,p2=A.rewrite(H,R,'Reader.step',[('TOP-192<=sp','TOP-240<=sp',1)],dict(TOP=TOP,SDK=SDK),'narc_reader')
    snapshot,p3=A.rewrite(H,R,'Reader.run',A.edits(H.O.H.RECIPES[1])+[
        ('((TOP-192,192),(DEST,size))','((TOP-296,296),(DEST,size))',1),
        ('self.read_bytes(TOP-192,56)==self.before[TOP-192-0x2000000:TOP-136-0x2000000]',
         'self.read_bytes(TOP-296,56)==self.before[TOP-296-0x2000000:TOP-240-0x2000000]',1)],
        dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=H.H.COOKIES,neighbors_before=H.H.neighbors_before),'narc_reader')
    finish,p4=A.rewrite(H,H.O.H,'Driver.finish_pp',A.edits(H.RECIPES[2])+[
        ('stack_guard_before=r.before[TOP-208-0x2000000:TOP-152-0x2000000].hex()',
         'stack_guard_before=r.before[TOP-296-0x2000000:TOP-240-0x2000000].hex()',1),
        ('stack_guard_after=self.read_bytes(TOP-208,56).hex()','stack_guard_after=self.read_bytes(TOP-296,56).hex()',1),
        ('stack_guard_range=[TOP-208,TOP-152]','stack_guard_range=[TOP-296,TOP-240]',1),
        ('self.pp_result.update(stack152_before=',
         'self.pp_result.update(stack240_before=r.before[TOP-240-0x2000000:TOP-0x2000000].hex(),stack240_after=self.read_bytes(TOP-240,240).hex(),stack152_before=',1)],
        dict(TOP=TOP,pp_snapshot=snapshot),'pp_caller')
    run,p5=A.rewrite(H,H.H.V,'run_case',A.edits(H.RECIPES[3])+[
        ('open_fast_value=1):','open_fast_value=1,find_value=1):',1),
        ('open_fast_value=open_fast_value)','open_fast_value=open_fast_value,find_value=find_value)',1),
        ('return dict(fs_open=',
         'return dict(convert=driver.convert_result,find_value=driver.find_value,guard8_global_before=driver.before[TOP-296-0x2000000:TOP-288-0x2000000].hex(),guard8_global_after=ram[TOP-296-0x2000000:TOP-288-0x2000000].hex(),fs_open=',1)],
        dict(Driver=Driver,A=H.H.A,TOP=TOP,NAME_ARENA=H.H.X.NAME_ARENA,NAME_END=H.H.X.NAME_END),'message_caller')
    service,p6=A.rewrite(H,H,'OpenObserver.service',[
        ('if pc not in (CONVERT, FAST): return self.base_service(pc)','if pc != FIND: return self.base_service(pc)',1),
        ('sp == ID','sp == DIR',1),('if pc == CONVERT:','if pc == FIND:',1),
        ('args[0] == ID and args[1] == 0x210F198','args[0] == DIR and args[1] == 0x210F198 and args[2] == ID and args[3] == 0',1),
        ('SDK[CONVERT]','SDK[FIND]',1),('result = 1','result = self.driver.find_value',1),
        ('entry=before)','entry=before, dir_before_hex=r.read_bytes(DIR,72).hex())',1)],
        dict(TOP=TOP,DIR=DIR,ID=ID,FILE=FILE,ARC=ARC,SDK=SDK,FIND=FIND),'fs_open_caller')
    return write,step,snapshot,finish,run,service,[p1,p2,p3,p4,p5,p6]


reader_write,reader_step,pp_snapshot,Driver.finish_pp,run_case,ConvertObserver.service,RECIPES=runtime_bindings()


def expected_inner(entry,command=14):
    need(command in(0,14),'finite inner Init field value')
    regs=list(entry);flow=[]
    for pc in range(INIT,INIT+40,4):
        flow.append(dict(pc=hex(pc),regs=list(regs)))
        if pc==INIT:regs[2]=0
        if pc==0x20D7FB0:regs[1]=14
        if pc==0x20D7FB4 and command==0:regs[1]=0
    return dict(entry=list(entry),flow=flow,returned=regs)


def expected_convert(r,entry=None,command=14):
    need(type(r['find_value'])is int and r['find_value']in(1,2)and type(r['pp_clobber'])is bool,
         'finite Find return/volatile policy')
    original=[ID,0x210F198,0,0,FILE,310,H.H.MON,0]+list(H.H.N.COOKIES[4:])+[0,ID,RETURN,0x1F]
    need(entry is None or list(entry)==original,'Convert entry follows actual Open call context')
    regs=list(original);flow=[];inner=None;find=None
    for pc in range(ENTRY,END,4):
        flow.append(dict(pc=hex(pc),regs=list(regs)))
        if pc==ENTRY:regs[13]-=16
        elif pc==0x20D8184:regs[13]-=72
        elif pc==0x20D8188:regs[5]=ID
        elif pc==0x20D818C:regs[0]=DIR
        elif pc==0x20D8190:regs[4]=0x210F198
        elif pc==0x20D8194:
            regs[14]=INIT_RETURN;inner=expected_inner(regs,command);regs[:]=inner['returned']
        elif pc==0x20D8198:regs[0]=DIR
        elif pc==0x20D819C:regs[1]=0x210F198
        elif pc==0x20D81A0:regs[2]=ID
        elif pc==0x20D81A4:regs[3]=0
        elif pc==0x20D81A8:
            regs[14]=0x20D81AC;before=list(regs)
            if r['pp_clobber']:
                for i in(1,2,3,12):regs[i]=0xA5000000+i
                regs[15]=0xA000001F
            regs[0]=r['find_value'];find=dict(pc=hex(FIND),entry=before,returned=list(regs))
        elif pc==0x20D81AC:regs[15]=0x2000001F
        elif pc==0x20D81B0:regs[0]=1
        elif pc==0x20D81B4:pass # EQ is false after nonzero Find CMP; observation is not an effect.
        elif pc==0x20D81B8:regs[13]+=72
        elif pc==0x20D81BC:
            regs[3:6]=original[3:6];regs[13]+=16
    return dict(entry=original,flow=flow,inner=inner,find=find,returned=regs)


def context_bindings():
    outer,p1=A.rewrite(H,H.O,'require_init',A.edits(H.INIT_RECIPE)+[
        ("p['models'][0]['name'] == 'FS_ConvertPathToFileID'","p['models'][0]['name'] == 'FSi_FindPath'",1),
        ("p['models'][0]['args'][2] == 0","p['models'][0]['args'][2] == ID",1),
        ('real R2 zero reaches native Open and lower Convert','real R2 zero reaches native Open; native Convert passes ID to Find',1)],
        dict(ID=ID),'fs_init_caller')
    predicted,p2=A.rewrite(H,H,'expected_open',[
        ('regs[14] = 0x20D828C; lower(CONVERT, 1)',
         "regs[14] = 0x20D828C; converted=expected_convert(r,regs);calls.append(converted['find']);regs[:]=converted['returned']",1)],
        dict(expected_convert=expected_convert),'fs_open_caller')
    opened,p3=A.rewrite(H,H,'require_open',[
        ('[TOP - 208, ID]','[TOP - 296, DIR]',1),
        ("['FS_ConvertPathToFileID', 'FS_OpenFileFast']","['FSi_FindPath', 'FS_OpenFileFast']",1),
        ("('FS_InitFile', 'FS_OpenFile')","('FS_InitFile', 'FS_OpenFile', 'FS_ConvertPathToFileID')",1)],
        dict(require_init_native=outer,expected_open=predicted,DIR=DIR),'fs_open_caller')
    return outer,predicted,opened,[p1,p2,p3]


require_outer_init,predict_open,require_open,CONTEXT_RECIPES=context_bindings()
require_parent_off,OFF_RECIPE=A.rewrite(H,H,'require_off_pair',[],dict(require_open=require_open),'fs_open_caller')


def native_binding():
    edits=A.edits(H.NATIVE_RECIPE)+[
        ("r['max_stack']==152","r['max_stack']==240",1),
        ("('FS_ConvertPathToFileID',0x20D828C,[path,0],[file,310,c6,c7],None)",
         "('FSi_FindPath',0x20D81AC,[path,ID],[path,ID,c6,c7],None)",1),
        ("ID if name=='FS_ConvertPathToFileID' else file","DIR if name=='FSi_FindPath' else file",1),
        ("ID if name in ('FS_ConvertPathToFileID','FS_OpenFileFast') else local",
         "DIR if name=='FSi_FindPath' else ID if name=='FS_OpenFileFast' else local",1),
        ("volatile[2] if clobber and index else 0","volatile[2] if clobber and index and name!='FS_OpenFileFast' else 0",1),
        ("result=FAST_VALUE if name=='FS_OpenFileFast' else read[2] if read else 1",
         "result=FIND_VALUE if name=='FSi_FindPath' else FAST_VALUE if name=='FS_OpenFileFast' else read[2] if read else 1",1),
        ("if name=='FS_ConvertPathToFileID':","if name=='FSi_FindPath':",1),
        ('push(0x20D8278,TOP-144,[path,0x2007353])',
         "push(0x20D8278,TOP-144,[path,0x2007353])\n push(0x20D8180,TOP-168,[0,file,310,0x20D828C])\n for pc,offset,value in INNER_STORES:store(pc,DIR+offset,4,value)",1),
        ('len(expected)==19+len(STORES)','len(expected)==23+len(STORES)+len(INNER_STORES)',1),
        ("stack=bytearray.fromhex(r['stack152_before']);need(len(stack)==152,'actual extended reader stack preimage size')",
         "stack=bytearray.fromhex(r['stack240_before']);need(len(stack)==240,'actual directory reader stack preimage size')",1),
        ('(local-16)','(local-104)',4),
        ("struct.pack_into('<I',stack,36,size)","struct.pack_into('<I',stack,124,size)",1),
        ("r['stack152_after']==stack.hex()","r['stack240_after']==stack.hex()",1)]
    return A.rewrite(H,R,'require_case',edits,
        dict(TOP=TOP,DEST=DEST,STOP=STOP,COOKIES=H.H.COOKIES,IP=H.H.IP,STORES=H.O.STORES,
             INNER_STORES=H.O.STORES,SDK=SDK,DIR=DIR,ID=ID,ARC=ARC,FAST_VALUE=1,FIND_VALUE=1,
             EXPECTED_HOOKS=169,EXPECTED_PC_COUNT=144),'narc_reader')


require_native,NATIVE_RECIPE=native_binding()


def require_readonly_guard(r):
    p=r['pp_reader']
    need(p['stack_guard_range']==[TOP-296,DIR]and
         len(bytes.fromhex(p['stack_guard_before']))==len(bytes.fromhex(p['stack_guard_after']))==56 and
         p['stack_guard_before']==p['stack_guard_after'],'Directory guard56 is an unchanged actual preimage')
    need(r['guard8_global_before']==p['stack_guard_before'][:16]==p['stack_guard_after'][:16]==r['guard8_global_after']and
         len(bytes.fromhex(r['guard8_global_before']))==8,
         'Eight readonly guard bytes remain outside unchanged608 global projection')
    return True


def require_convert(r,data,command=14):
    need(command in(14,0)and r['open_fast_value']==1,'finite directory observer context')
    out,p=r['convert'],r['pp_reader'];expected=expected_convert(r,command=command)
    require_open(r,data)
    need(out['entry']==expected['entry']and out['returned']==expected['returned']and out['flow']==expected['flow'],
         'Convert full native flow, aggregate pointer, R3 restore and ARM return')
    initial=bytes.fromhex(p['stack240_before']);final=bytes.fromhex(p['stack240_after'])
    need(len(initial)==len(final)==240 and initial[88:].hex()==p['stack152_before']and
         final[88:].hex()==p['stack152_after'],'Convert full240 and inherited152 views agree')
    open_before=bytes.fromhex(r['fs_open']['frame_before']);before=bytearray(initial[:88]+open_before)
    before[96:104]=struct.pack('<II',0x210F198,0x2007353)
    saved=struct.pack('<4I',0,FILE,310,RETURN);init_before=bytearray(before);init_before[72:88]=saved
    directory=bytearray(before[:72]);stores=[]
    inner_expected=expected['inner'];vectors={e['pc']:e['regs']for e in inner_expected['flow']}
    for pc,offset,value in H.O.STORES:
        value=command if pc==0x20D7FB4 else value
        regs=list(vectors[hex(pc)])
        if pc==0x20D7FB4 and command==0:regs[1]=0
        stores.append(dict(pc=hex(pc),address=DIR+offset,bytes=4,before=bytes(directory[offset:offset+4]).hex(),
                           value=value,regs=regs))
        struct.pack_into('<I',directory,offset,value)
    init_after=bytearray(init_before);init_after[:72]=directory
    after=bytearray(init_after);after[88:96]=struct.pack('<II',ARC,140)
    inner=out['inner_init']
    need(inner['entry']==inner_expected['entry']and inner['returned']==inner_expected['returned']and
         inner['flow']==inner_expected['flow']and inner['before']==bytes(before[:72]).hex()and
         inner['after']==directory.hex()and inner['frame_before']==init_before.hex()and
         inner['frame_after']==init_after.hex(),
         'Second Init own72/44preserved/full240 and full16 ARM invocation identity')
    need(inner['stores']==(stores if r['observe']else[]),'Second Init seven actual directory word stores')
    push=[dict(pc=hex(ENTRY),address=DIR+72+4*i,bytes=4,before=bytes(before[72+4*i:76+4*i]).hex(),value=value)
          for i,value in enumerate((0,FILE,310,RETURN))]
    need(out['frame_before']==before.hex()and out['frame_after']==after.hex()and
         out['stores']==(push if r['observe']else[]),'Convert four native saved words and exact frame240 lifetime')
    first=p['models'][0]
    need(first['name']=='FSi_FindPath'and first['entry']==expected['find']['entry']and
         first['returned']==expected['find']['returned']and first['dir_before_hex']==directory.hex(),
         'Find model sees initialized local directory and actual output pointer')
    need(out['ledger_before']==dict(initialized=True,file=FILE,open=False,cursor=None,path=None,archive_sha256=None)and
         out['ledger_after']==dict(initialized=True,file=FILE,open=False,cursor=None,path='a/0/1/1',archive_sha256=None),
         'Directory Init and Find do not replace the outer file or open an archive')
    require_readonly_guard(r)
    shadows=[]
    if command==0:
        pre=vectors['0x20d7fb4'];post=list(pre);post[1]=0
        shadows=[dict(pc='0x20d7fb4',before=pre,after=post,
            reason='inner directory command14 to0 only; outer Init and raw ID source unchanged')]
    need(inner['shadows']==shadows,'Directory-only finite command shadow; never outer Init')
    return True


def require_case(r,data,q):
    need(r['variant']=='current'and r['pp_shadows']==[]and 'pp_expected_slot0'not in data,
         'positive Convert has no directory value shadow')
    require_convert(r,data)
    H.H.require_pp_context(r,data)
    code={**q['header_code'],**q['fs_init_code'],**{pc:v for pc,v in q['fs_open_code'].items()if pc<0x20D82B4},
          **q['fs_convert_code']}
    native=A.clone(require_native,dict(FIND_VALUE=r['find_value']))
    native(r['pp_reader'],data['pp_reader'],code,T.expected(data['constructor'],r['plus'])[0]['ot_draws'][-1])
    H.H.require_earlier(r,data,q)
    return True


def require_off_pair(on,off,data):
    parent=require_parent_off(on,off,data)
    require_convert(on,data);require_convert(off,data)
    need(on['variant']==off['variant']=='current'and on['find_value']==off['find_value']==1 and
         on['observe']is True and off['observe']is False,'Directory OFF finite control domain')
    a,b=on['convert'],off['convert'];inner_a,inner_b=a['inner_init'],b['inner_init']
    need(b['stores']==inner_b['stores']==[]and
         {k:v for k,v in a.items()if k not in('stores','inner_init')}==
         {k:v for k,v in b.items()if k not in('stores','inner_init')}and
         {k:v for k,v in inner_a.items()if k!='stores'}=={k:v for k,v in inner_b.items()if k!='stores'}and
         all(on[k]==off[k]for k in('guard8_global_before','guard8_global_after')),
         'Directory OFF exact240/72/ARM ABI/Init invocations/guard8 equal; only native store logs differ')
    return dict(neutral=True,parent=parent,scope='Native ConvertPUSH16/innerInit28 and modeled callerID8 equal OFF/ON; '
        'actual240-byte frame/56-byte guard and unmasked global8 protected; inherited heap1124 only')


def positive_code(q):
    return {**q['header_code'],**q['fs_init_code'],
        **{pc:v for pc,v in q['fs_open_code'].items()if pc<0x20D82B4},**q['fs_convert_code']}


def names_with_only_second_scope_removed(names):
    result=copy.deepcopy(names)
    need(len(result)==6 and len(result[1]['transitions'])==5,'six names and five second-name scope checkpoints')
    for transition in result[1]['transitions'][:2]:
        need(len(transition['ram_sha256'])==64,'second-name actual RAM digest shape')
        del transition['ram_sha256']
    return result


def counter_record(r,data,q):
    disguised=copy.deepcopy(r);disguised['variant']='current';disguised['convert']['inner_init']['shadows']=[]
    try:require_case(disguised,data,q)
    except ValueError as error:
        return dict(variant=r['variant'],result=r,rejection=str(error),tag_disguised=True)
    raise ValueError('Directory command counter accepted')


def require_counter(counter,normal,data,q):
    require_case(normal,data,q);r=counter['result']
    need(counter['variant']==r['variant']=='directory_command_zero'and r['plus']==normal['plus']==1 and
         r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and
         r['observe']is True and r['pp_clobber']is False and r['find_value']==normal['find_value']==1 and
         r['open_fast_value']==normal['open_fast_value']==1,'Directory counter finite fixture and lower model policy')
    require_convert(r,data,0);H.H.require_pp_context(r,data)
    a,b=normal['pp_reader'],r['pp_reader']
    allowed={'models','native_writes','ram_sha256','stack240_after','projected_ram_sha256'}
    need({k:v for k,v in a.items()if k not in allowed}=={k:v for k,v in b.items()if k not in allowed}and
         r['fs_init']==normal['fs_init']and r['fs_open']==normal['fs_open']and r['pp_binding']==normal['pp_binding'],
         'Directory counter exact shared prestate, outer Init, Open, legacy frames and return context')
    directory=bytearray.fromhex(a['models'][0]['dir_before_hex']);struct.pack_into('<I',directory,16,0)
    models=copy.deepcopy(a['models']);models[0]['dir_before_hex']=directory.hex()
    need(b['models']==models,'Only modeled Find directory command input differs; ID transport unchanged')
    writes=copy.deepcopy(a['native_writes']);indices=[i for i,e in enumerate(writes)if int(e['pc'],16)==0x20D7FB4 and e['address']==DIR+16]
    need(len(indices)==1,'one inner command store, distinct from outer Init')
    writes[indices[0]]['value']=0
    frame=bytearray.fromhex(a['stack240_after']);struct.pack_into('<I',frame,16,0)
    need(b['native_writes']==writes and b['stack240_after']==frame.hex()and
         b['ram_sha256']!=a['ram_sha256']and b['projected_ram_sha256']!=a['projected_ram_sha256'],
         'Directory counter one native command word and phase frame differ; no digest equality inferred')
    native=A.clone(require_native,dict(INNER_STORES=tuple((pc,o,0 if pc==0x20D7FB4 else v)for pc,o,v in H.O.STORES)))
    native(b,data['pp_reader'],positive_code(q),T.expected(data['constructor'],1)[0]['ot_draws'][-1])
    replay=copy.deepcopy(r);replay['variant']='current';H.H.require_earlier(replay,data,q)
    need(all(r[k]==normal[k]for k in('instructions','mon_hex','prefix','seed_after','pp_flow','pp_stores','pp_checkpoint',
         'raw_ram_sha256','functional_ram_sha256','guard8_global_before','guard8_global_after'))and
         names_with_only_second_scope_removed(r['names'])==names_with_only_second_scope_removed(normal['names']),
         'Directory command mutation retains caller outputs and whole final RAM; only first two second-name scope hashes may differ')
    actual=counter_record(r,data,q)
    need(counter['tag_disguised']is True and counter['rejection']==actual['rejection']==
         'Convert full native flow, aggregate pointer, R3 restore and ARM return',
         'Directory counter specifically rejected as a disguised positive native flow')
    return True


def source_identities():
    result=H.source_identities()
    for p in(__file__,A.__file__):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
    return result

def analyze(rom, language, objects, strategy_object, readback_only=False):
    import mmap, unicorn
    R.W.require_host_budget(); sources = source_identities()
    model = P.G.S.SHARED.read_current(rom, language)
    with rom.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
        q, proof = qualify(model,raw,language,objects,strategy_object)
        result = dict(schema='trainer31-native-fs-convert-v1',language=language,input=model['record'],
            source_sha256=sources,proof=proof,recipes=RECIPES+CONTEXT_RECIPES+[NATIVE_RECIPE,OFF_RECIPE],cpu_executed=False,
            conditional_policy=dict(unicorn_version=unicorn.__version__,cpu_model=17,
                false_EQ_hook=True,scope='code-hook delivery; false ARM effects remain suppressed'))
        if not readback_only:
            data = H.O.resources(model,raw,language)
            positives, guards, controls, off, counters = [], [], [], [], []
            for plus in (0,1):
                for seed in (0x12345678,0x12345679):
                    r = run_case(model,raw,language,q,data,plus,seed)
                    require_case(r,data,q); positives.append(r)
                    print(language,'native Convert caller',plus,hex(seed),'verified',flush=True)
                r = run_case(model,raw,language,q,data,plus,0x12345678,observe=False)
                off.append(dict(result=r,proof=require_off_pair(positives[-2],r,data)))
            normal = next(r for r in positives if r['plus']==1 and r['seed']==0x12345678)
            r = run_case(model,raw,language,q,data,1,0x12345678,poison=0x39)
            require_case(r,data,q); need(r['mon_hex']==normal['mon_hex'],'Convert alternate preimage fill changes party'); guards.append(r)
            for kwargs in (dict(pp_clobber=True),dict(find_value=2)):
                r = run_case(model,raw,language,q,data,1,0x12345678,**kwargs)
                require_case(r,data,q)
                need(r['mon_hex']==normal['mon_hex'] and r['prefix']==normal['prefix'] and
                     r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and
                     r['pp_reader']['ram_sha256']==normal['pp_reader']['ram_sha256'],
                     'Convert lower volatile/noncanonical truthy policy preserves output and phase RAM')
                controls.append(r)
            r = run_case(model,raw,language,q,data,1,0x12345678,variant='directory_command_zero')
            counter = counter_record(r,data,q); require_counter(counter,normal,data,q); counters.append(counter)
            result.update(cpu_executed=True,positives=positives,guards=guards,volatile_controls=controls,
                observer_off=off,counters=counters,resources=dict(pp=data['pp_reader']['11']['oracle']),
                limits=['Initialized trainer31 caller and selected custom PP310 Open only',
                        'Native Init/Open/Convert wrappers; FindPath/OpenFast plus Seek/Read/Close are explicit models',
                        'Opaque ARC token is not native FSArchive state; no invented FSFile fields',
                        'Counter changes only inner directory command14 to0; opaque Find model still returns ID, not native SDK failure',
                        'Exact240-byte frame/56-byte actual guard including8 unmasked readonly bytes; guestglobal560 within608; heap1124B OFF projection only',
                        'Recovered assembly bytes do not reconstruct original SDK compiler provenance',
                        'No natural encounter/full battle/UI/SAVE/cold/hardware or performance claim'])
        need(source_identities()==sources,'Convert sources changed during campaign'); R.W.require_host_budget()
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
        payload = json.dumps(result,separators=(',',':')).encode(); need(len(payload)<=32*1024**2,'Convert expanded report budget')
        blob = gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload
        need(len(blob)<=8*1024**2,'Convert stored report budget')
        args.json.parent.mkdir(parents=True,exist_ok=True)
        with args.json.open('xb')as f:f.write(blob)
    except ValueError as error: parser.exit(2,str(error)+'\n')
    print(args.language,'Convert readback verified' if args.readback_only else 'native Convert caller and explicit lower models verified')


if __name__=='__main__':main()
