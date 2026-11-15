#!/usr/bin/env python3
"""Compose qualified native Read/Wait/IRQ into the complete selected PP caller.

Find/Send remain declared boundaries. Source-owned RAM witnesses and exact ABI
contexts are required; original callers, game defaults and ROMs are untouched.
"""
from pathlib import Path
import ast,copy,gc,gzip,hashlib,importlib.util,json,mmap,struct,types


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


W=load('read_caller_wait_parent',Path(__file__).with_name('attribuisci_fs_wait.py'))
H=W.R.H
A=load('read_caller_profile',Path(__file__).parents[1]/'test/fs_read_caller_bench.py')
R,P,B,T,need,sha=H.R,H.P,H.B,H.T,H.need,H.sha
TOP,DEST,STOP,FILE,ID,ARC,DIR=H.TOP,H.DEST,H.STOP,H.FILE,H.ID,H.ARC,H.DIR
READ,SEND=W.B.WRAPPER,W.B.SEND
PAGE=DIR&~4095
SEEK_PIN='5ce9e421b4dd786274d0a524d9bcba6ae6711bb1b2808d7cc2bde8277f9028f7'
WAIT_PIN='9e1d80fb11021b76820619229928524eea7773aa5d8bf8e90db5b28c22e4eb61'
WAIT_BENCH_PIN='8001a0c8e071d8d200b16334c92862ffcc9f89950fdd9c3f596da5b174f63bc1'
need(sha(Path(H.__file__).read_bytes())==SEEK_PIN and sha(Path(W.__file__).read_bytes())==WAIT_PIN and
     sha(Path(W.B.__file__).read_bytes())==WAIT_BENCH_PIN,'Read caller qualified parents drift')
SDK={pc:name for pc,name in H.SDK.items()if pc!=READ}
RECIPES=[];BINDINGS=[]
from unicorn.arm_const import UC_ARM_REG_PC


def derive(module,function,edits,namespace,kind):
    pins=dict(fs_seek_caller=SEEK_PIN,fs_close_caller='2886dfb1262c4e091254bc56fbc020997e03f7fabcbbf460da1362a4932ebefc',
        narc_reader='f21c05e1c12c8d7b77a5a18796c1a1da081ab5e3a0ae90b9856e5b2a8e29d42d',
        message_caller='f326503b432d74296c4983ae52dfe50a3a9298df2ce21acf4697a783c3a50632')
    function,recipe=types.FunctionType(W.B.E.rewrite.__code__,{**vars(W.B.E),'PINS':pins})(
        module,function,edits,{**namespace,'__source_kind__':kind})
    RECIPES.append(recipe);return function


def binding(fn,namespace):
    BINDINGS.append(dict(parent_source_sha256=SEEK_PIN,function=fn.__qualname__,namespace=sorted(namespace),code_unchanged=True))
    return H.A.clone(fn,namespace)


root_step=binding(H.root_step,dict(SDK=SDK))
close_service=derive(H.H,'CloseObserver.service',[
    ("struct.pack('<II',16,14)","struct.pack('<II',16,0)",1),
    ("r.read_bytes(FILE+48,8)==struct.pack('<II',ARC,140)",
     "r.read_bytes(FILE+48,12)==struct.pack('<III',DEST,oracle['member_bytes'],oracle['member_bytes'])and r.read_bytes(FILE+20,4)==bytes(4)",1)],{},'fs_close_caller')


def source_identities():
    result=W.source_identities()
    for p in(__file__,A.__file__):result[str(Path(p).resolve().relative_to(P.SOURCE))]=sha(Path(p).read_bytes())
    return result


def qualify(model,raw,language,objects,strategy_object,read_recipe,wait_recipe):
    from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB
    q,proof=H.qualify(model,raw,language,objects,strategy_object)
    view=P.G.S.SHARED.gifts_audit.Arm9View(raw);components=[];extra={}
    roles=[('read-'+name,values,read_recipe/('fs-read-'+name+'.o'))for name,values in W.R.C.BODIES.items()]+[
        ('wait-'+name,values,wait_recipe/('fs-wait-'+name+'.o'))for name,values in W.C.BODIES.items()]
    for name,(address,n,digest),obj in roles:
        blob=view.read(address,n)
        need(blob==P.G.piece(model['segments'],address,n)and sha(blob)==digest and
             W.L.object_text(obj,n,digest)==blob,'Read caller independent raw/decoded/recovered ELF '+name)
        count=12 if name=='read-wrapper'else n
        code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(blob[:count],address))
        need(len(code)==count//4,'Read caller ARM extent without literal execution')
        extra.update({i.address:(4,False)for i in code})
        components.append(dict(role=name,ram=hex(address),rom_offset=hex(view.offset(address,n)),bytes=n,sha256=digest,
            object_sha256=sha(obj.read_bytes()),instruction_bytes=count))
    allowed=set(range(W.B.CORE,W.B.CORE+124,4))|{READ,READ+4,READ+8}|W.B.EXTRA_CODE
    need(len(allowed)==65 and allowed<=set(extra),'Read caller qualified65 native starts')
    q['fs_read_caller_code']={pc:extra[pc]for pc in allowed}
    blob=view.read(0x2007352,0xB6);decoded=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,0x2007352))
    q['fs_parser_bridge']={i.address:bytes(i.bytes)for i in decoded}
    need(all(q['header_code'].get(i.address)==(i.size,True)for i in decoded if i.address!=0x200738E and i.address!=0x20073F4),
         'Read caller Thumb bridge belongs to qualified parser code')
    proof['native_read_wait_in_caller']=dict(components=components,source_subset='Retained native HGSS SDK, no new insertion',
        binary_starts=len(extra),executed_native_starts=65,forecast_reader_hooks=732,forecast_reader_seen=266,
        forecast_native_writes=169,frame_peak=240,read_nested_frame=48,global_peak=560,full_stack_bound=608,
        parser_bridge_sha256=sha(blob),SDK_models=dict(Find=1,Send=9),
        model_scope='Send0 payload/pos/completion12 only; native release/list/queue/archive/card effects excluded')
    return q,proof


class ReadObserver:
    def __init__(self,driver,reader):
        self.driver,self.reader=driver,reader;self.active=False;self.current=None;self.result=[];self.bridge=[]
        self.parent_step,self.parent_write,self.parent_read,self.base_service=reader.step,reader.write,reader.read,reader.service
        self.root_step=types.MethodType(root_step,reader);self.root_write=driver.convert_observer.native_write
        reader.code={**reader.code,**driver.qualified['fs_read_caller_code']}
        driver.seek_observer.base_service=types.MethodType(close_service,driver.close_observer)
        reader.step,reader.write,reader.read,reader.service=self.step,self.write,self.read,self.service
        self.before=None;self.full_pair=None

    def step(self,u,pc,n,user):
        r=self.reader
        if self.active and pc==(self.current['entry'][14]&~1):
            before=self.before;after=r.read_bytes(0x2000000,0x400000);a=PAGE-0x2000000;b=a+4096
            outside_before=before[:a]+before[b:];outside_after=after[:a]+after[b:]
            self.current.update(returned=r.regs(),frame_after=r.read_bytes(DIR,240).hex(),
                destination_after=r.read_bytes(self.current['entry'][1],self.current['entry'][2]).hex(),
                page_after=after[a:b].hex(),outside_before_sha256=sha(outside_before),outside_after_sha256=sha(outside_after),
                outside_unchanged=outside_before==outside_after,after_ram_sha256=sha(after),cursor_after=r.cursor)
            if not self.result[:-1]and self.driver.retain_full_read_witness:self.full_pair=(before,after)
            self.before=None;self.active=False
        if 0x2007352<=pc<0x2007408:self.bridge.append(dict(pc=hex(pc),regs=r.regs()))
        if pc==READ:
            need(not self.active and len(self.result)<7 and r.initialized and r.open and r.file==FILE,
                 'Read caller exactly seven initialized open native Read lifetimes')
            entry=r.regs();nbytes=entry[2]
            need(entry[0]==FILE and 0<nbytes<=16,'Read caller finite actual file/length')
            frame=r.read_bytes(DIR,240);destination=r.read_bytes(entry[1],nbytes)
            self.before=r.read_bytes(0x2000000,0x400000);a=PAGE-0x2000000
            f=dict(ordinal=len(self.result),caller_lr=hex(entry[14]),entry=entry,frame=frame.hex(),
                destination_before=destination.hex(),payload='',position=r.cursor,
                provenance=dict(registers='Actual complete caller entry16, not inverted model metadata',
                    frame='Actual240-byte pre-read frame',original_natural_capture=False))
            # Validate geometry/ownership with a bounded placeholder; actual raw
            # bytes are selected later from native ARG/pos at Send0.
            test=dict(f,payload=bytes(nbytes).hex());W.B.check_fixture(test)
            self.current=dict(fixture=f,entry=entry,returned=None,frame_before=frame.hex(),frame_after=None,
                destination_before=destination.hex(),destination_after=None,page_before=self.before[a:a+4096].hex(),page_after=None,
                before_ram_sha256=sha(self.before),after_ram_sha256=None,flow=[],stores=[],reads=[],services=[],completion=[],
                model_index=len(r.models),cursor_before=r.cursor,cursor_after=None,policy=dict(error=0,send=self.driver.read_send_value,clobber=r.clobber),native_peak=0)
            self.result.append(self.current);self.active=True
        if self.active:
            sp=r.regs()[13];self.current['native_peak']=max(self.current['native_peak'],self.current['entry'][13]-sp)
            if pc in self.driver.qualified['fs_read_caller_code']:
                self.current['flow'].append(dict(pc=hex(pc),regs=r.regs()))
            self.root_step(u,pc,n,user);return
        self.parent_step(u,pc,n,user)

    def write(self,u,access,address,n,value,user):
        if not self.active:return self.parent_write(u,access,address,n,value,user)
        pc=u.reg_read(UC_ARM_REG_PC);sp=self.current['entry'][13]
        allowed=(pc==W.B.CORE and sp-24<=address<sp)or(pc==W.B.WAIT and sp-48<=address<sp-24)or(
            (pc,address)in((0x20D8118,FILE+48),(0x20D8130,FILE+52),(0x20D8138,FILE+56),(0x20D814C,FILE+12)))
        need(allowed and n==4,'Read caller native word owner/PC')
        if self.reader.observe:self.current['stores'].append(dict(pc=hex(pc),address=address,bytes=n,
            before=self.reader.read_bytes(address,n).hex(),value=value))
        self.root_write(u,access,address,n,value,user)

    def read(self,u,access,address,n,value,user):
        if not self.active:return self.parent_read(u,access,address,n,value,user)
        pc=u.reg_read(UC_ARM_REG_PC)
        need(W.B.read_allowed(pc,address,n,self.current['fixture']),'Read caller native field/pool/saved-frame read owner')
        self.current['reads'].append(dict(pc=hex(pc),address=address,bytes=n,hex=self.reader.read_bytes(address,n).hex()))

    def service(self,pc):
        if pc!=SEND or not self.active:return self.base_service(pc)
        r,u=self.reader,self.reader.u;out=self.current;before=r.regs();sp,lr=before[13:15];g=self.driver.qualified['fs_file_geometry']
        need(before[0:2]==[FILE,0]and sp==TOP-160 and lr==0x20D8158 and not before[15]&32 and
             r.open and r.archive==r.data['11']['raw'],'Read Send0 exact actual ABI and open archive')
        dst,original,n=struct.unpack('<3I',r.read_bytes(FILE+48,12));fid,top,bottom,pos=struct.unpack('<4I',r.read_bytes(FILE+32,16))
        need((fid,top,bottom)==(g['file_id'],g['top'],g['bottom'])and pos==top+r.cursor and
             original==n==out['entry'][2]and dst==out['entry'][1]and 0<n<=16 and n<=bottom-pos,
             'Read Send0 consumes actual native ARG/physical position and complete bounded slice')
        need(DIR<=dst and dst+n<=FILE or DEST<=dst and dst+n<=DEST+16,'Read Send0 finite owned destination')
        frame_before=r.read_bytes(DIR,240).hex();position=r.cursor;blob=r.archive[position:position+n]
        need(len(blob)==n,'Read Send0 complete independent raw slice')
        r.read_count+=1;u.mem_write(dst,blob);r.cursor+=n;u.mem_write(FILE+44,struct.pack('<I',top+r.cursor))
        after_regs=W.B.B.boundary_regs(before,self.driver.read_send_value,r.clobber)
        for reg,val in zip(W.B.B.REGS,after_regs):u.reg_write(reg,val)
        event=dict(name=SDK[SEND],pc=hex(pc),args=before[:4],sp=sp,lr=hex(lr),saved=before[4:12],entry=before,
            cursor_before=position,open_before=True,position=position,destination=dst,requested_bytes=n,delivered_bytes=n,
            delivered_sha256=sha(blob),result_r0=self.driver.read_send_value,return_sp=sp,return_saved=after_regs[4:12],
            return_volatile=[after_regs[i]for i in(1,2,3,12)],cursor_after=r.cursor,open_after=True,returned=r.regs(),
            command=0,path=r.path,archive_sha256=sha(r.archive),opaque_archive_token=ARC,file_id=fid,
            frame_before=frame_before,frame_after=r.read_bytes(DIR,240).hex())
        out['fixture']['payload']=blob.hex()
        out['services'].append(dict(pc=hex(pc),entry=before,returned=r.regs(),frame_before=frame_before,
            frame_after=event['frame_after'],result=self.driver.read_send_value))
        error=int(self.driver.read_variant=='first_error1'and len(self.result)==1)
        out['policy']['error']=error;W.B.complete_guest(u,r.regs,out['completion'],error)
        r.models.append(event);u.reg_write(UC_ARM_REG_PC,lr)


class Driver(H.Driver):
    latest=None
    def __init__(self,*args,variant='current',read_send_value=1,retain_full_read_witness=False,**kwargs):
        need(variant in('current','first_error1')and type(read_send_value)is int and read_send_value in(0,1),
             'Read caller finite variant and separate Send0 return policy')
        super().__init__(*args,variant='current',**kwargs)
        self.read_variant,self.read_send_value=variant,read_send_value
        self.retain_full_read_witness=retain_full_read_witness;self.read_result=None;self.parser_flow=None
        Driver.latest=self

    def start_pp(self):
        super().start_pp();regs=self.regs();before=self.read_bytes(0x2000000,0x400000)
        self.read_observer=ReadObserver(self,self.pp_reader);self.read_result=self.read_observer.result;self.parser_flow=self.read_observer.bridge
        need(regs==self.regs()and before==self.read_bytes(0x2000000,0x400000),'Read caller observer attachment is CPU/RAM neutral')


run_case=derive(H.PP.V,'run_case',H.A.edits(H.RUN_RECIPE)+[
    ('close_value=1):','close_value=1,read_send_value=1,retain_full_read_witness=False):',1),
    ('close_value=close_value)','close_value=close_value,read_send_value=read_send_value,retain_full_read_witness=retain_full_read_witness)',1),
    ('return dict(seek=','return dict(read_calls=driver.read_result,parser_flow=driver.parser_flow,read_send_value=driver.read_send_value,seek=',1)],
    dict(Driver=Driver,A=H.PP.A,TOP=TOP,NAME_ARENA=H.PP.X.NAME_ARENA,NAME_END=H.PP.X.NAME_END),'message_caller')


# Exact context changes from the now-native Read return; first Seek remains
# before any Read. Entry IP of the outer whole-member API remains zero.
expected_seek=derive(H,'expected_seek',[
    ('0xA5000003 if clobber else 0','0xA5000003 if clobber and index==0 else 0',1),
    ('0xA500000C if clobber else 0','0xA500000C if clobber else (0 if index==0 else 0x20D8104)',1)],{},'fs_seek_caller')
expected_close=derive(H.H,'expected_close',[
    ("v[0]if clobber else DEST,v[1]if clobber else o['member_bytes'],v[2]if clobber else 0",
     '0x6000009F,0x6000001F,0',1),
    ('v[3]if clobber else 0,TOP-136','v[3]if clobber else 0x20D8104,TOP-136',1),
    ('0xA000001F if clobber else 0x2000001F','0x2000001F',1)],{},'fs_close_caller')


def native_prefix():
    """The unchanged46 source-owned writes before the first Seek/Read.

    This is the prefix of the authenticated P61 native recipe. Each component's
    full frame/ABI oracle is retained separately through require_fast.
    """
    expected=[];local=TOP-136;path=0x210F198
    c4,c5,c6,c7=H.PP.COOKIES[:4]
    def store(pc,address,n,value):expected.append(dict(pc=hex(pc),address=address,bytes=n,value=value))
    def push(pc,address,values):
        for i,value in enumerate(values):store(pc,address+4*i,4,value)
    push(R.ENTRY,TOP-12,[0x2007509,c4,STOP|1]);store(0x2007512,TOP-16,4,0)
    push(R.HELPER,TOP-40,[0,44,c5,c6,c7,0x200751B])
    for pc,offset,n,value in((0x2007334,0,4,DEST),(0x2007336,20,4,0),(0x2007338,16,4,0),
            (0x200733A,12,4,0),(0x200733E,8,2,0),(0x2007344,4,4,0)):store(pc,local+offset,n,value)
    for pc,offset,value in H.I.STORES:store(pc,FILE+offset,4,value)
    push(0x20D8278,TOP-144,[path,0x2007353])
    push(0x20D8180,TOP-168,[0,FILE,310,0x20D828C])
    for pc,offset,value in H.I.STORES:store(pc,DIR+offset,4,value)
    push(0x20D8208,TOP-168,[FILE,ARC,140,0]);push(0x20D820C,H.F.SP,[FILE,0x20D82A4])
    for pc,offset,value in((0x20D822C,8,ARC),(0x20D8230,48,ARC),(0x20D823C,52,140),(0x20D8268,12,16)):
        store(pc,FILE+offset,4,value)
    need(len(expected)==46,'Read caller immutable native prefix size');return expected


def require_register_vectors(value):
    """Reject bool/float aliases in recorded full unsigned32 CPU vectors."""
    if isinstance(value,dict):
        for key,item in value.items():
            if key in('entry','returned','original_entry','regs')and isinstance(item,list):
                need(W.B.B.u32s(item),'Read caller actual registers must be unsigned32 integers')
            require_register_vectors(item)
    elif isinstance(value,list):
        for item in value:require_register_vectors(item)


def require_read_call(call,fixture,observe,error,send,clobber):
    """Check one actual contextual Read against source dataflow and page bytes.

    The outside-page assertion is a captured byte comparison, not an independent
    full-RAM readback. A retained full pair can independently repeat that check.
    """
    require_register_vectors(call);require_register_vectors(fixture)
    need(type(error)is int and type(send)is int and type(clobber)is bool and
         all(type(call['policy'][k])is int for k in('error','send'))and type(call['policy']['clobber'])is bool,
         'Read caller strict completion policy types')
    need(type(observe)is bool and call['policy']==dict(error=error,send=send,clobber=clobber),
         'Read caller explicit source completion/Send/clobber policy')
    need(all(call['fixture'][k]==fixture[k]for k in('ordinal','entry','frame','destination_before','payload','position')),
         'Read caller fixture bound to preceding source state and independent raw payload')
    want=W.B.predict(fixture,error,send,clobber)
    need(call['entry']==fixture['entry']and call['frame_before']==fixture['frame']and
         call['destination_before']==fixture['destination_before'],'Read caller exact contextual preimage')
    for key in('returned','frame_after','destination_after','services','completion','native_peak'):
        need(call[key]==want[key],'Read caller source '+key)
    need(call['flow']==[dict(pc=pc,regs=regs)for pc,regs in want['flow'].items()],
         'Read caller exact65 native full-register contexts including false instructions')
    need(call['stores']==(want['stores']if observe else[]),'Read caller exact16 native stores or OFF transcript')
    W.B.require_reads(call,fixture,want)
    before,after=bytes.fromhex(call['page_before']),bytes.fromhex(call['page_after'])
    a=DIR-PAGE;dst,n=fixture['entry'][1:3];b=dst-PAGE
    need(before[a:a+240].hex()==fixture['frame']and before[b:b+n].hex()==fixture['destination_before'],
         'Read caller page witnesses bind both preimages')
    A.require_page(before,after,bytes.fromhex(want['frame_after']),dst,bytes.fromhex(fixture['payload']))
    need(call['outside_unchanged']is True and call['outside_before_sha256']==call['outside_after_sha256']and
         len(call['outside_before_sha256'])==64,'Read caller actual outside-page byte comparison and matching digests')
    return want


def require_timeline(r,data,q):
    """Chronological source/byte oracle: Open → five Seek/seven Read → Close."""
    for value in(r['read_calls'],r['seek'],r['fs_close'],r['parser_flow'],r['pp_reader']['models']):require_register_vectors(value)
    H.require_fast(r,data)
    p=r['pp_reader'];models=p['models'];g=data['fs_geometry'];resource=data['pp_reader']['11'];raw=resource['raw']
    need(len(models)==10 and len(r['seek'])==5 and len(r['read_calls'])==7 and
         r['send_value']==r['find_value']==r['open_fast_value']==1 and r['pp_shadows']==[],
         'Read caller exact ten boundaries, five Seek, seven Read and unchanged earlier policies')
    need(r['variant']in('current','first_error1')and type(r['read_send_value'])is int and r['read_send_value']in(0,1),
         'Read caller finite whole-case policy')
    current=bytearray.fromhex(r['fs_fast']['frame_after']);regs=list(r['fs_open']['returned'])
    pc=0x2007352;bridge_flow=[];writes=native_prefix();seek_index=read_index=0;cursor=0

    def apply_stores(stores):
        for event in stores:
            i=event['address']-DIR;n=event['bytes']
            need(0<=i and i+n<=240 and event['before']==bytes(current[i:i+n]).hex(),
                 'Read caller temporal native write preimage')
            current[i:i+n]=event['value'].to_bytes(n,'little')
            writes.append({k:v for k,v in event.items()if k!='before'})

    for _ in range(13):
        bridge=A.advance_bridge(q['fs_parser_bridge'],pc,regs,current)
        bridge_flow.extend(bridge['flow']);apply_stores(bridge['stores'])
        need(current.hex()==bridge['frame'],'Read caller native Thumb frame delta')
        entry=bridge['entry'];target=bridge['target'];pc=bridge['next_pc']
        if target==H.ENTRY:
            call=r['seek'][seek_index];want=expected_seek(r,data,seek_index,entry)
            need(call['entry']==call['original_entry']==entry and call['shadows']==[]and
                 call['flow']==want['flow']and call['returned']==want['returned'],
                 'Read caller exact Seek entry including incoming flags, origin and native return')
            need(call['frame_before']==current.hex()and call['file_before']==bytes(current[FILE-DIR:FILE-DIR+72]).hex()and
                 call['cursor_before']==cursor==want['previous'],'Read caller Seek temporal preimage/cursor')
            reads=[dict(pc=hex(a),address=b,bytes=4,hex=struct.pack('<I',v).hex())for a,b,v in(
                (0x20D83F8,FILE+36,g['top']),(0x20D8424,FILE+36,g['top']),(0x20D8430,FILE+40,g['bottom']))]
            need(call['reads']==reads,'Read caller three source-owned Seek loads')
            stores=[dict(pc='0x20d843c',address=FILE+44,bytes=4,
                before=bytes(current[FILE+44-DIR:FILE+48-DIR]).hex(),value=g['top']+want['offset'])]
            need(call['stores']==(stores if r['observe']else[]),'Read caller one native Seek position store')
            apply_stores(stores);cursor=want['offset']
            need(call['frame_after']==current.hex()and call['file_after']==bytes(current[FILE-DIR:FILE-DIR+72]).hex()and
                 call['cursor_after']==cursor,'Read caller Seek complete frame and guest-derived cursor')
            regs=want['returned'];seek_index+=1
        elif target==READ:
            call=r['read_calls'][read_index];dst,n=entry[1:3];position,destination,size=H.read_specs(data)[read_index]
            need((cursor,dst,n)==(position,destination,size),'Read caller raw slice independently selected from archive oracle')
            i=dst-DIR
            before=bytes(current[i:i+n]).hex()if 0<=i and i+n<=240 else p['destination_before']
            fixture=dict(ordinal=read_index,entry=entry,frame=current.hex(),destination_before=before,
                         payload=raw[position:position+n].hex(),position=position)
            error=int(r['variant']=='first_error1'and read_index==0)
            want=require_read_call(call,fixture,r['observe'],error,r['read_send_value'],r['pp_clobber'])
            need(call['model_index']==read_index+2 and call['cursor_before']==cursor and call['cursor_after']==cursor+n,
                 'Read caller provider occurrence and actual ledger cursor')
            service=want['services'][0];model=models[read_index+2]
            need(model['name']==SDK[SEND]and model['pc']==hex(SEND)and model['command']==0 and
                 model['entry']==service['entry']and model['returned']==service['returned']and
                 model['args']==service['entry'][:4]and model['sp']==model['return_sp']==service['entry'][13]and
                 model['lr']==hex(service['entry'][14])and model['saved']==model['return_saved']==service['entry'][4:12]and
                 model['return_volatile']==[service['returned'][j]for j in(1,2,3,12)]and
                 model['result_r0']==r['read_send_value']and model['frame_before']==service['frame_before']and
                 model['frame_after']==service['frame_after'],'Read caller exact Send0 native ABI and before-completion frame')
            need(model['position']==model['cursor_before']==position and model['cursor_after']==position+n and
                 model['destination']==dst and model['requested_bytes']==model['delivered_bytes']==n and
                 model['delivered_sha256']==sha(raw[position:position+n])and model['open_before']is True and
                 model['open_after']is True and model['path']==resource['oracle']['path']and
                 model['archive_sha256']==sha(raw)and model['opaque_archive_token']==ARC and model['file_id']==140,
                 'Read caller Send0 complete bounded raw delivery and opaque archive lifetime')
            # Native writes and model writes interleave. Never apply Find's dead
            # ID buffer after later Read PUSH spills have reused those bytes.
            writes.extend({k:v for k,v in e.items()if k!='before'}for e in want['stores'])
            current[:]=bytes.fromhex(want['frame_after']);cursor+=n;regs=want['returned'];read_index+=1
        else:
            need(target==H.H.ENTRY and seek_index==5 and read_index==7,'Read caller finite final Close gate')
            out=r['fs_close'];want=expected_close(r,data)
            need(entry==want['entry']==out['entry']and out['flow']==want['flow']and out['returned']==want['returned']and
                 out['shadows']==[],'Read caller exact Close source bridge/native contexts without register forcing')
            prior_file=bytes(current[FILE-DIR:FILE-DIR+72])
            need(out['frame_before']==current.hex()and out['file_before']==prior_file.hex(),
                 'Read caller Close receives final Read frame and actual ARG/error/status')
            stores=[]
            for addrpc,address,value in[(H.H.ENTRY,H.H.SP+4*j,v)for j,v in enumerate((entry[4],0x2007409))]+[
                (a,FILE+off,v)for a,off,v in((0x20D82DC,8,0),(0x20D82E4,16,14),(0x20D82F4,12,0))]:
                event=dict(pc=hex(addrpc),address=address,bytes=4,before=bytes(current[address-DIR:address-DIR+4]).hex(),value=value)
                stores.append(event);apply_stores([event])
            need(out['stores']==(stores if r['observe']else[])and out['file_after']==H.H.cleanup_file(prior_file).hex()and
                 out['frame_after']==current.hex(),'Read caller five Close stores and other60 file bytes preserved')
            model=models[9]
            need(model['name']==SDK[SEND]and model['command']==8 and model['entry']==want['send']['entry']and
                 model['returned']==want['send']['returned']and model['file_before_hex']==prior_file.hex(),
                 'Read caller command8 sees the actual post-Read native context')
            ledger=dict(initialized=True,file=FILE,open=True,cursor=cursor,path=resource['oracle']['path'],archive_sha256=sha(raw))
            need(out['ledger_before']==ledger and out['ledger_after']==dict(ledger,open=False),
                 'Read caller one final Close changes only declared host open state')
            break
    else:raise ValueError('Read caller thirteen-gate finite source timeline')
    need(r['parser_flow']==bridge_flow,'Read caller complete source Thumb bridge contexts including incoming NZCV')
    need(p['native_writes']==(writes if r['observe']else[])and len(writes)==169,
         'Read caller entire chronological169 native stores')
    need(p['stack240_after']==current.hex()and p['stack152_after']==bytes(current[ID-DIR:]).hex()and
         p['stack_frame_hex']==bytes(current[TOP-136-DIR:]).hex(),'Read caller final three linked stack extents')
    # The sole retained P61 projection is the Open property input. Read position
    # and completion are now witnessed at their actual Send0 occurrences.
    project=r['fs_projection'];need(project['geometry']==g and len(project['events'])==1,
         'Read caller no obsolete modeled Read property events')
    start=bytearray.fromhex(r['fs_fast']['frame_before'])
    for a,v in[(TOP-168+4*j,v)for j,v in enumerate((FILE,ARC,140,0))]+[(H.F.SP+4*j,v)for j,v in enumerate((FILE,0x20D82A4))]+[
        (FILE+off,v)for off,v in((8,ARC),(48,ARC),(52,140))]:struct.pack_into('<I',start,a-DIR,v)
    after=H.checked_projection(project['events'][0],'open-property-input',FILE+32,H.prop_bytes(g),start,1,models[1])
    struct.pack_into('<I',after,FILE+12-DIR,16)
    need(after.hex()==r['fs_fast']['frame_after'],'Read caller first property projection precedes native Fast status store')
    return True


def native_guards():
    source=Path(R.__file__).read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='require_case')
    parent=ast.get_source_segment(source,node)
    for before,after,count in H.A.edits(H.NATIVE_RECIPE):
        need(parent.count(before)==count,'Read caller inherited guard recipe occurrence');parent=parent.replace(before,after)
    tail=parent[parent.index(' # Tuple: API'):]
    # All pre-existing domain/ownership/stack/saved-register/rng guards remain.
    # Only the obsolete modeled-Read tail is replaced by require_timeline.
    return derive(R,'require_case',H.A.edits(H.NATIVE_RECIPE)+[
        (tail,' return True',1),
        ("r['observe']is True","type(r['observe'])is bool",1),
        ('volatile[1] if clobber else size','volatile[1] if clobber else 0x6000001F',1),
        ('volatile[3] if clobber else IP','volatile[3] if clobber else 0x20D8104',1),
        ],{**H.require_native.__globals__,'EXPECTED_HOOKS':732,'EXPECTED_PC_COUNT':266},'narc_reader')


require_native=native_guards()


def complete_code(q):return{**H.seek_code(q),**q['fs_read_caller_code']}


def require_case(r,data,q,allow_error=False):
    need(r['variant']==('first_error1'if allow_error else'current')and r['pp_shadows']==[],
         'Read caller positive/counter variant and no register shadows')
    require_timeline(r,data,q);H.PP.require_pp_context(r,data)
    native=H.A.clone(require_native,dict(CLOSE_VALUE=r['close_value']))
    native(r['pp_reader'],data['pp_reader'],complete_code(q),T.expected(data['constructor'],r['plus'])[0]['ot_draws'][-1])
    if allow_error:
        replay=dict(r,variant='current');H.PP.require_earlier(replay,data,q)
    else:H.PP.require_earlier(r,data,q)
    return True


def require_off_pair(on,off,data,q):
    require_case(on,data,q);require_timeline(off,data,q)
    native=H.A.clone(require_native,dict(CLOSE_VALUE=off['close_value']))
    native(off['pp_reader'],data['pp_reader'],complete_code(q),T.expected(data['constructor'],off['plus'])[0]['ot_draws'][-1])
    # OFF intentionally omits the constructor's body ledger. Its inherited
    # paired oracle checks actual functional state and exact1124-byte projection;
    # a positive-only ledger check cannot be applied to that absent log.
    parent=H.PP.require_off_pair(on,off,data)
    need(on['parser_flow']==off['parser_flow']and on['fs_projection']==off['fs_projection']and
         on['read_send_value']==off['read_send_value']==1,'Read caller OFF identical source bridge and model projection')
    for key in('seek','read_calls'):
        need(len(on[key])==len(off[key]),'Read caller OFF complete paired calls')
        for a,b in zip(on[key],off[key]):
            ignored={'stores'}
            if key=='read_calls':ignored|={'before_ram_sha256','after_ram_sha256','outside_before_sha256','outside_after_sha256'}
            need(b['stores']==[]and {k:v for k,v in a.items()if k not in ignored}=={k:v for k,v in b.items()if k not in ignored},
                 'Read caller OFF same actual API/frame/page/native/Send/completion state')
    for key in('fs_init','fs_open','convert','fs_fast','fs_close'):
        a,b=copy.deepcopy(on[key]),copy.deepcopy(off[key])
        need(b['stores']==[],'Read caller OFF component stores disabled');a.pop('stores');b.pop('stores')
        if key=='convert':
            need(b['inner_init']['stores']==[],'Read caller OFF nested Init stores disabled')
            a['inner_init'].pop('stores');b['inner_init'].pop('stores')
        need(a==b,'Read caller OFF preceding and final component contexts unchanged')
    return dict(neutral=True,parent=parent,scope='Whole final and phase1124 projections inherited unchanged; exact source frames/pages/functional Read context, no new RAM mask')


def counter_record(r,data,q):
    require_case(r,data,q,allow_error=True)
    disguised=copy.deepcopy(r);disguised['variant']='current'
    # Hide policy metadata as well: positive rejection must use actual native
    # evidence, not a tag that merely states which counter was requested.
    disguised['read_calls'][0]['policy']['error']=0
    try:require_case(disguised,data,q)
    except ValueError as error:return dict(variant=r['variant'],result=r,rejection=str(error),tag_disguised=True,policy_disguised=True)
    raise ValueError('Read caller native error counter accepted as success')


def require_counter(counter,normal,data,q):
    require_case(normal,data,q);r=counter['result'];require_case(r,data,q,allow_error=True)
    need(r['variant']=='first_error1'and r['plus']==normal['plus']==1 and r['seed']==normal['seed']==0x12345678 and
         r['poison']==normal['poison']==0xC7 and r['observe']is True and r['pp_clobber']is False and
         r['read_send_value']==normal['read_send_value']==r['close_value']==normal['close_value']==1,
         'Read caller first error-only finite counter contract')
    need(r['read_calls'][0]['returned'][0]==0xFFFFFFFF and normal['read_calls'][0]['returned'][0]==2 and
         r['read_calls'][0]['destination_after']==normal['read_calls'][0]['destination_after']and
         r['read_calls'][0]['cursor_after']==normal['read_calls'][0]['cursor_after'],
         'Read caller genuine native failure return despite identical delivered bytes/cursor')
    second=copy.deepcopy(normal['seek'][1])
    for key in('frame_before','frame_after'):
        image=bytearray.fromhex(second[key]);struct.pack_into('<I',image,FILE+20-DIR,1);second[key]=image.hex()
    for key in('file_before','file_after'):
        image=bytearray.fromhex(second[key]);struct.pack_into('<I',image,20,1);second[key]=image.hex()
    need(r['seek'][1]==second and r['seek'][2:]==normal['seek'][2:]and r['fs_close']==normal['fs_close']and
         all(r[k]==normal[k]for k in('mon_hex','prefix','seed_after','pp_flow','pp_stores','pp_checkpoint',
             'raw_ram_sha256','functional_ram_sha256')),
         'Read caller ignored error result washes at next source bridge and final outputs/RAM equal')
    need(r['read_calls'][1]['frame_after']==normal['read_calls'][1]['frame_after']and
         r['read_calls'][1]['returned']==normal['read_calls'][1]['returned']and r['read_calls'][2:]==normal['read_calls'][2:],
         'Read caller second completion resets error field and all later complete Read evidence agrees')
    actual=counter_record(r,data,q)
    need(counter['tag_disguised']is counter['policy_disguised']is True and counter['rejection']==actual['rejection'],
         'Read caller disguised counter independently rejected on observed evidence')
    return True


def write_private(path,value):
    need(not path.exists()and not path.is_symlink()and P.SOURCE not in path.resolve().parents,
         'Read caller fresh private output outside source required')
    blob=json.dumps(value,separators=(',',':')).encode();need(len(blob)<=32*1024**2,'Read caller expanded output budget')
    blob=gzip.compress(blob,mtime=0)if path.suffix=='.gz'else blob
    need(len(blob)<=8*1024**2,'Read caller stored output budget')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb')as fd:fd.write(blob)


def analyze(rom,language,objects,strategy_object,read_recipe,wait_recipe,raw_dir=None,readback_only=False,probe=False):
    import unicorn
    R.W.require_host_budget();sources=source_identities();model=P.G.S.SHARED.read_current(rom,language)
    if not readback_only:
        need(raw_dir is not None and not raw_dir.exists()and P.SOURCE not in raw_dir.resolve().parents,
             'Read caller fresh private raw directory required before CPU')
        raw_dir.mkdir(parents=True)
    with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
        q,proof=qualify(model,raw,language,objects,strategy_object,read_recipe,wait_recipe)
        result=dict(schema='trainer31-native-fs-read-caller-v1',language=language,input=model['record'],source_sha256=sources,
            proof=proof,recipes=RECIPES,namespace_bindings=BINDINGS,cpu_executed=False,compiler_invoked=False,
            conditional_policy=dict(unicorn_version=unicorn.__version__,cpu_model=17,cpu_name='Cortex-A15',
                native_instruction_semantics=True,ARM946_silicon_or_timing=False,Read_hooks=65,all_reader_hooks=732))
        if not readback_only:
            data=H.resources(model,raw,language);serial=0
            def run(label,plus=1,seed=0x12345678,**kwargs):
                nonlocal serial
                serial+=1;path=raw_dir/('%02d-%s.json.gz'%(serial,label))
                try:
                    observed=run_case(model,raw,language,q,data,plus,seed,**kwargs)
                except Exception as error:
                    driver=Driver.latest
                    partial=dict(label=label,completed=False,error_type=type(error).__name__,error=str(error),
                        stage=getattr(driver,'stage',None),regs=driver.regs()if driver is not None else None,
                        read_calls=getattr(driver,'read_result',None),parser_flow=getattr(driver,'parser_flow',None))
                    write_private(path,partial);raise
                write_private(path,dict(label=label,completed=True,result=observed))
                # The full pair is retained for one representative first Read;
                # its hashes are already bound to the raw call before any oracle.
                pair=Driver.latest.read_observer.full_pair
                if pair is not None:
                    for suffix,blob in zip(('before','after'),pair):
                        with(raw_dir/(label+'-first-read-'+suffix+'.bin.gz')).open('xb')as f:f.write(gzip.compress(blob,mtime=0))
                    Driver.latest.read_observer.full_pair=None
                print(language,label,'raw saved before oracle',flush=True);return observed
            positives=[];off=[];guards=[];controls=[];counters=[]
            grid=[(1,0x12345678)]if probe else[(p,s)for p in(0,1)for s in(0x12345678,0x12345679)]
            for plus,seed in grid:
                observed=run('positive-%d-%08x'%(plus,seed),plus,seed,retain_full_read_witness=(serial==0))
                require_case(observed,data,q);positives.append(observed)
                print(language,'full native Read caller verified',plus,hex(seed),flush=True)
            normal=next(r for r in positives if r['plus']==1 and r['seed']==0x12345678)
            if not probe:
                for plus in(0,1):
                    observed=run('off-'+str(plus),plus,observe=False)
                    baseline=next(r for r in positives if r['plus']==plus and r['seed']==0x12345678)
                    off.append(dict(result=observed,proof=require_off_pair(baseline,observed,data,q)))
                observed=run('fill39',poison=0x39);require_case(observed,data,q)
                need(observed['mon_hex']==normal['mon_hex'],'Read caller alternate preimage preserves party');guards.append(observed)
                for label,kwargs in(('clobber',dict(pp_clobber=True)),('close2',dict(close_value=2)),('read-send0',dict(read_send_value=0))):
                    observed=run(label,**kwargs);require_case(observed,data,q)
                    need(all(observed[k]==normal[k]for k in('mon_hex','prefix','seed_after','functional_ram_sha256','raw_ram_sha256')),
                         'Read caller declared lower-boundary control preserves party/seed/final RAM');controls.append(observed)
                observed=run('first-error1',variant='first_error1');counter=counter_record(observed,data,q)
                require_counter(counter,normal,data,q);counters.append(counter)
            result.update(cpu_executed=True,probe_only=probe,positives=positives,observer_off=off,guards=guards,
                volatile_controls=controls,counters=counters,resources=dict(pp=data['pp_reader']['11']['oracle']),
                limits=['Initialized trainer31/PP310 complete caller only, not natural/full-battle/UI/SAVE/cold/hardware',
                    'Native Init/Open/Convert/Fast/Seek/Read/Wait/IRQ/Close; Find1 and Send9 are explicit models',
                    'Send0 payload/pos plus completion12 projection only; real queue/archive/card/thread/release excluded',
                    'Original native compiler/objects unavailable; recovered exact ARM recipes are separate evidence',
                    'Frame240/global560 within inherited608; exact page4096 Read witnesses; no enlarged RAM or OFF1124 masks',
                    'Outside-page digests accompany actual byte comparison; one first-Read full pair permits independent replay',
                    'Error1 is declared completion input with successful raw delivery; not a naturally occurring filesystem failure',
                    'Unicorn CPU17 Cortex-A15 instruction semantics, no ARM946 hardware or timing claim'])
        need(source_identities()==sources,'Read caller sources changed during execution');R.W.require_host_budget()
    return result


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in('rom','objects','strategy-object','read-recipe','wait-recipe','json'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--language',choices=('EN','IT'),required=True)
    parser.add_argument('--raw-dir',type=Path)
    parser.add_argument('--readback-only',action='store_true')
    parser.add_argument('--probe',action='store_true',help='one positive full caller, with raw evidence saved before checks')
    args=parser.parse_args()
    try:
        need(not args.json.exists()and not args.json.is_symlink()and P.SOURCE not in args.json.resolve().parents,
             'Read caller fresh private report outside source required')
        result=analyze(args.rom,args.language,args.objects,args.strategy_object,args.read_recipe,args.wait_recipe,
                       args.raw_dir,args.readback_only,args.probe)
        write_private(args.json,result)
    except ValueError as error:parser.exit(2,str(error)+'\n')
    print(args.language,'Read caller readback verified'if args.readback_only else'Read caller verified; scope recorded')


if __name__=='__main__':main()
