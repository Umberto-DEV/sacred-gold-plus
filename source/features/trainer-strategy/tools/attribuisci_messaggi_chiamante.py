#!/usr/bin/env python3
"""Compose native trainer-message APIs with the complete trainer31 caller.

Private exact ROMs and retained project objects. SDK models remain explicit;
one initialized caller context does not establish natural encounter activation.
"""
from pathlib import Path
import importlib.util,types,struct,copy,json,gzip,mmap,gc,sys
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
U=load('native_message_caller_parent',Path(__file__).with_name('attribuisci_chiamante.py'))
M=load('native_message_producer_parent',Path(__file__).with_name('attribuisci_messaggi.py'))
A=load('native_message_caller_adapter',Path(__file__).parents[1]/'test/caller_message_bench.py')
B,T,P,Q,N,need,sha=U.B,U.T,U.P,U.Q,U.N,U.need,U.sha
OUTER,INNER=U.OUTER,U.INNER
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_CPSR
APIS=(('new_msg',0x200BAF8,0x20733D7),('new_string',0x200BBA0,0x207342B),('copy',0x2026A68,0x2073435),('delete_string',0x2026380,0x207343B),('destroy_msg',0x200BB44,0x2073467))

def bind_message():
 """Copy method bindings, changing only the observer's nested stack origin."""
 need(sha(Path(M.__file__).read_bytes())=='2a00534ad4df6ff15d18a357524daa8aae6f46516efc9dc8b9aff3cee08a46b8','native message observer/service source drift')
 namespace=dict(vars(M));namespace['TOP']=INNER
 class BoundMessage(M.Message):pass
 namespace['Message']=BoundMessage
 for name,method in vars(M.Message).items():
  if isinstance(method,types.FunctionType):
   bound=types.FunctionType(method.__code__,namespace,method.__name__,method.__defaults__,method.__closure__);bound.__kwdefaults__=method.__kwdefaults__;setattr(BoundMessage,name,bound)
 need({k for k in namespace if namespace[k]is not vars(M).get(k)}=={'TOP','Message'},'native message binding changes outside stack/class identity')
 return BoundMessage

def qualify(model,raw,language,objects,strategy_object):
 qualified,proof=U.qualify(model,raw,language,objects,strategy_object);message,locations=M.qualify(model,raw)
 for pc,shape in message.items():need(pc not in qualified['caller_code'] or qualified['caller_code'][pc]==shape,'caller/message shared instruction shape drift')
 qualified['message_code']=message;proof['native_messages']=locations;return qualified,proof

class Driver(U.Driver):
 parent=U
 latest=None
 def __init__(self,bench,qualified,data,plus,seed,*,poison=0xC7,observe=True,variant='current'):
  need(variant in ('current','omit_temp_free','omit_msg_free','wrong_read_destination','high_level_stub'),'finite native-message caller variant')
  super().__init__(bench,qualified,data,plus,seed,poison=poison,observe=observe)
  self.variant=variant;Driver.latest=self;self.message=bind_message()(None,qualified['message_code'],data['message'],31,heap_fill=0xC7,observe=observe,variant='omit_temp_free' if variant=='omit_temp_free' else 'wrong_read_destination' if variant=='wrong_read_destination' else 'current');self.message_active=False;self.message_api=[];self.message_entry=None;self.message_snapshots={};self.pending_sdk=None;self.native_message_live_bytes=False;self.dispatch=[];self.shadows=[];self.message_across_constructor=None
 def factory(self,*args):
  u=super().factory(*args);self.message.u=u;return u
 def configure(self,cpu,implementations,events,state,handles):
  need(cpu is self.u is self.message.u,'message and constructor must share one CPU');self.events,self.backend_state,self.backend_handle_cache=events,state,handles;result=dict(implementations)
  for pc,name in M.SDK.items():
   original=implementations[name]
   def dispatch(u,pc=pc,name=name,original=original):
    need(u is self.u,'SDK dispatch CPU identity')
    if self.message_active:
     need(self.pending_sdk==(pc,self.regs()),'single native-message SDK dispatch/entry context');self.pending_sdk=None;self.message.service(pc);self.sync_lifetime();self.dispatch.append(dict(owner='message',pc=hex(pc),name=name))
    else:
     need(self.stage=='ctor','heap/NARC service outside declared owner stage')
     if name in ('Heap_Free','NARC_ReadFromMember','NARC_Delete'):need(not M.ARENA<=self.regs()[0]<M.ARENA_END,'constructor cannot borrow message allocation/handle')
     original(u)
   result[name]=dispatch
  return result
 def prepare(self,cpu):
  super().prepare(cpu);cpu.mem_write(M.ARENA,b'\xD3'*(M.ARENA_END-M.ARENA))
  # B.run has installed SDK stubs by now. The high-level bodies must still
  # match every authenticated ordinary instruction, not merely their prologues.
  for pc,(size,thumb) in self.qualified['message_code'].items():need(self.read_bytes(pc,size)==P.G.piece(self.bench.segments,pc,size),'high-level native message code overwritten before caller entry')
  self.native_message_live_bytes=True
  if self.variant=='high_level_stub':cpu.mem_write(0x200BAF8,b'\x70\x47');self.shadows.append(dict(pc='0x200baf8',kind='post-qualification high-level stub overwrite'))
 def sync_lifetime(self):
  ptr=self.message.pointer;self.msg_live=ptr.get('msg') in self.message.live;self.string_live=ptr.get('string') in self.message.live;self.string_created='string'in ptr
  self.outer_frees=sum(x['name']=='Heap_Free' and x.get('label')=='string' for x in self.message.models)
  self.destroy_calls=sum(x['name']=='NARC_Delete' for x in self.message.models)
 def start_message(self,regs):
  index=len(self.message_api);need(index<5,'native message API count');phase,entry,lr=APIS[index];ptr=self.message.pointer
  need(self.read_bytes(entry,2)==P.G.piece(self.bench.segments,entry,2),'native message live entry bytes drift')
  expected=([1,27,729,11],[ptr.get('msg'),31],[ptr.get('string'),Q.NAME,8],[ptr.get('string')],[ptr.get('msg')])[index]
  need(regs[:len(expected)]==expected and regs[13]==INNER and regs[14]==lr and regs[15]&32 and self.stage==('suffix' if index==4 else 'prefix'),'actual caller native-message API entry ABI/activation')
  need(not self.message.pending and not self.pending_sdk,'native message previous helper/service closure');self.message.phase=phase;self.message_active=True;self.message_entry=dict(phase=phase,entry=hex(entry),lr=hex(lr),before=regs)
 def finish_message(self,regs):
  event=self.message_entry;before=event['before'];need(regs[13]==before[13]==INNER and regs[4:12]==before[4:12] and regs[15]&32 and not self.message.pending and not self.pending_sdk,'actual caller native-message API return ABI')
  self.sync_lifetime();phase=event['phase'];ptr=self.message.pointer
  if phase=='new_msg':need(regs[0]==ptr['msg'],'native MsgData pointer result');self.message_snapshots['msg']=self.read_bytes(regs[0],12).hex()
  if phase=='new_string':need(regs[0]==ptr['string'],'native String pointer result');self.message_snapshots['string']=self.read_bytes(regs[0],2*len(self.message.words)+10).hex()
  if phase=='copy':self.message_snapshots['destination']=self.read_bytes(Q.NAME,16).hex()
  event.update(after=regs,live={hex(p):dict(v) for p,v in self.message.live.items()},handle_live=self.message.handle_live);self.message_api.append(event);self.message_active=False;self.message_entry=None
 def prefix_proof(self):
  tail=bytes([self.poison])*32;source=self.header+tail;expected=bytearray(source);expected[20:20+len(self.name)]=self.name
  need(self.read_bytes(Q.LOCAL,52)==source and self.read_bytes(Q.TRAINER,52)==bytes(expected),'native-message caller local20/untouched32/packed name provenance')
  ptr=self.message.pointer;expected_live={ptr['msg']}|({ptr['temp']} if self.variant=='omit_temp_free' else set());need(self.msg_live and not self.string_live and self.outer_frees==1 and self.message.handle_live and set(self.message.live)==expected_live and self.message.temp_deleted==(self.variant!='omit_temp_free'),'native message prefix lifetime')
  need(self.read_bytes(ptr['msg'],12).hex()==self.message_snapshots['msg'] and self.read_bytes(ptr['string'],2*len(self.message.words)+10)==b'\xDD'*(2*len(self.message.words)+10),'native MsgData survives; freed String poisoned before constructor')
  need(not self.pending and len(self.structure_writes)==13 and len(self.message_api)==4,'native-message prefix native store/API closure')
  return dict(trainer_hex=bytes(expected).hex(),local_source52=source.hex(),structure_writes=copy.deepcopy(self.structure_writes),calls=copy.deepcopy(self.caller_calls),msg_live=self.msg_live,string_live=self.string_live,outer_frees=self.outer_frees,message_live={hex(p):dict(v) for p,v in self.message.live.items()},handle_live=self.message.handle_live)
 def collect_body(self):
  body=super().collect_body();pointer=self.message.pointer;after=self.read_bytes(pointer['msg'],12).hex();need(after==self.message_snapshots['msg'] and self.message.handle_live and pointer['msg']in self.message.live,'constructor must preserve live native MsgData/handle')
  self.message_across_constructor=dict(before=self.message_snapshots['msg'],after=after,live={hex(p):dict(v) for p,v in self.message.live.items()},handle_live=self.message.handle_live,string_freed_sha256=sha(self.read_bytes(pointer['string'],2*len(self.message.words)+10)),temporary_sha256=sha(self.read_bytes(pointer['temp'],2*len(self.message.words))));return body
 def step(self,u,pc,n,user):
  if self.message_active and pc==int(self.message_entry['lr'],16)&~1:self.finish_message(self.regs())
  if not self.message_active and self.stage in ('prefix','suffix') and pc in {x[1] for x in APIS}:
   need(len(self.message_api)<5 and pc==APIS[len(self.message_api)][1],'native-message API order');self.start_message(self.regs())
  if self.message_active:
   self.steps+=1;sp=u.reg_read(UC_ARM_REG_SP);need(self.steps<=3000000 and OUTER-608<=sp<=INNER,'composed message stack/instruction bound');self.max_stack=max(self.max_stack,OUTER-sp)
   if pc in self.qualified['caller_code']:self.caller_pcs.add(pc)
   if pc in M.SDK:
    # B's sole SDK callback owns model writes. Calling Message.step here
    # would execute its service a second time.
    self.message.steps+=1;need(self.message.steps<=20000 and INNER-128<=sp<=INNER and sp%8==0 and n==2 and u.reg_read(UC_ARM_REG_CPSR)&32 and self.pending_sdk is None,'nested native-message SDK hook contract');self.message.max_stack=max(self.message.max_stack,INNER-sp);self.pending_sdk=(pc,self.regs());return
   if self.variant=='omit_msg_free' and pc==0x200BB66:self.shadows.append(dict(pc=hex(pc),kind='skip native MsgData free BL'));u.reg_write(UC_ARM_REG_PC,0x200BB6B)
   self.message.step(u,pc,n,user);return
  if self.stage=='prefix' and pc==B.ENTRY:
   regs=self.regs();ptr=self.message.pointer;need(regs[:3]==[B.SETUP,1,11] and regs[13]==INNER and regs[14]==0x2073445 and regs[4:12]==[B.SETUP+4,Q.NAME,ptr['string'],1]+list(N.COOKIES[4:]),'actual constructor ABI after native trainer String destruction');self.prefix=self.prefix_proof();self.ctor_entry=regs;self.body_events_start=len(self.events);self.transition('ctor')
  super().step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.message_active:self.message.read(u,access,address,n,value,user);return
  super().read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  if self.message_active:self.message.write(u,access,address,n,value,user);return
  super().write(u,access,address,n,value,user)

def run_case(model,raw,language,qualified,data,plus=1,seed=0x12345678,*,poison=0xC7,observe=True,variant='current'):
 need(sys.flags.optimize==0,'run without Python -O');bench,_=T.bench_image(model,raw,language,qualified['module']);driver=Driver(bench,qualified,data,plus,seed,poison=poison,observe=observe,variant=variant);gc.collect();run,adapter=A.adapt(B,driver);need(B.STACK_TOP==OUTER,'message caller starts with restored observer stack scope')
 try:result=run(bench,31,driver=driver,plus=plus,seed=seed,max_instructions=3000000)
 finally:B.STACK_TOP=OUTER
 need(len(driver.api_calls)==3 and len(driver.message_api)==5 and not driver.message_active and driver.pending_sdk is None and driver.ctor_return is not None and driver.stage=='getter','complete native-message caller API return')
 need(not driver.pending and not driver.message.pending and result['end']['sp']==OUTER and result['end']['r'][4:12]==list(N.COOKIES),'caller native helper/return closure')
 ram=result.pop('ram');message=driver.message;allocations=[dict(pointer=p,bytes=size,label=label) for p,size,label in message.allocs];canaries=all(driver.read_bytes(p-8,8)==b'\xA5'*8 and driver.read_bytes(p+size,8)==b'\xA5'*8 for p,size,label in message.allocs)
 ignored=[(OUTER-608,OUTER),(Q.TRAINER,Q.TRAINER+52),(B.SETUP,B.SETUP+4),(B.ARENA-8,driver.backend_state['arena']+8),(B.REGISTRY,B.REGISTRY+64),(0x23DA044,0x23DA048),(P.MODULE,P.MODULE+2048),(B.PARTIES+0x1000,B.PARTIES+0x1000+0x5B0),(0x21D15A8,0x21D15AC),(0x21D421C,0x21D421C+404),(0x23D8708,0x23D870C)]+[(p-8,p+size+8) for p,size,label in message.allocs]
 frozen=P.masked_hash(driver.before,ignored);need(frozen==P.masked_hash(ram,ignored),'native-message full caller unrelated RAM changed')
 msg=dict(api=driver.message_api,snapshots=driver.message_snapshots,models=message.models,native_helpers=message.helpers,native_writes=message.writes,observed_pcs=sorted(message.seen),allocations=allocations,live={hex(p):dict(v) for p,v in message.live.items()},handle_live=message.handle_live,reads=message.reads,temp_deleted=message.temp_deleted,dead_store=message.dead_store,canaries=canaries,shadows=message.shadows,instructions=message.steps,max_stack=message.max_stack,dispatch=driver.dispatch,native_code_live_before_entry=driver.native_message_live_bytes,same_cpu=True,heap_fill=message.fill,across_constructor=driver.message_across_constructor)
 return dict(language=language,plus=plus,seed=seed,poison=poison,observe=observe,variant=variant,cpu_model=driver.cpu_model,adapter=adapter,api_calls=driver.api_calls,ctor_entry=driver.ctor_entry,ctor_return=driver.ctor_return,prefix=driver.prefix,body=driver.body,caller_pcs=sorted(driver.caller_pcs),caller_calls=driver.caller_calls,caller_writes=driver.caller_writes,or_writes=driver.or_writes,services=driver.services,transitions=driver.transitions,instructions=driver.steps,max_stack=driver.max_stack,end=result['end'],seed_after=result['seed_after'],mon_hex=[x.hex() for x in result['mons']],decoded=[T.M.decode(x) for x in result['mons']],header=list(result['party_header']),plus_hits=driver.word(0x23D8708),stack_canary=result['stack_canary'],functional_ram_sha256=P.masked_hash(ram,[(OUTER-608,OUTER),(B.ARENA-8,driver.backend_state['arena']+8),(M.ARENA,M.ARENA_END)]),unrelated_ram_sha256=frozen,events=result['events'],overlay=result['overlay'],message=msg,shadows=driver.shadows)

def require_message(r,data,qualified):
 """Source-derived nested ABI oracle; no synthetic standalone API receipt."""
 msg=r['message'];record=data['message']['oracle']['records']['31'];words=record['words'];payload=N.words_bytes(words);n=len(words);length=2*n;offset=record['entry_bank_offset'];m,s=M.ARENA+32,M.ARENA+64;t=s+((length+33)&~7);h=M.HANDLE;k=(32*596947+n*18749)&65535;tail=list(N.COOKIES[4:]);c5,c6,c7=N.COOKIES[1:4]
 need(msg['same_cpu']is True and msg['native_code_live_before_entry']is True and msg['heap_fill']==0xC7 and not msg['shadows'] and msg['canaries']is True and msg['live']=={} and msg['handle_live']is False and msg['reads']==3 and msg['temp_deleted']is True and msg['dead_store']is True,'nested message native identity/lifetime/bounds')
 allocations=[dict(pointer=m,bytes=12,label='msg'),dict(pointer=s,bytes=length+10,label='string'),dict(pointer=t,bytes=length,label='temp')];need(msg['allocations']==allocations,'nested message isolated allocation sequence')
 expected_dest=payload+bytes([r['poison']])*(16-length);need(msg['snapshots']==dict(msg=struct.pack('<HHHHI',1,11,27,729,h).hex(),string=(struct.pack('<HHI',n,n-1,N.MAGIC)+payload+b'\xC7\xC7').hex(),destination=expected_dest.hex()),'nested native MsgData/String/payload/spare/destination')
 need(msg['observed_pcs']==sorted(qualified['message_code']) and len(msg['observed_pcs'])==228 and msg['instructions']==217+34*n and msg['max_stack']==80,'nested message exact native PC/path/frame coverage')
 live=lambda *labels:{hex(x['pointer']):dict(label=x['label'],bytes=x['bytes']) for x in allocations if x['label']in labels}
 need(msg['across_constructor']==dict(before=msg['snapshots']['msg'],after=msg['snapshots']['msg'],live=live('msg'),handle_live=True,string_freed_sha256=sha(b'\xDD'*(length+10)),temporary_sha256=sha(b'\xDD'*length)),'native message live/dead objects preserved across actual constructor')
 args4=([1,27,729,11],[m,31,0,Q.TRAINER+48],[s,Q.NAME,8,Q.TRAINER+48],[s,s+8+length,0,0xFFFFFFFF],[m,1,2,0xFFFFFFFF])
 saved=([Q.SAVE,c5,c6,c7],[B.SETUP+4,Q.NAME,Q.LOCAL+48,1],[B.SETUP+4,Q.NAME,s,1],[B.SETUP+4,Q.NAME,s,1],[B.SETUP+16,B.SETUP+0x10C,s,4])
 after_regs=([m,11,729,11],[s,65535,n-1,Q.TRAINER+48],[Q.NAME,s+8+length,0,0xFFFFFFFF],[s,N.MAGIC,0,0xFFFFFFFF],[m,1,2,0xFFFFFFFF]);last_lrs=(0x200BB35,0x200BAB1,0x2026A99,0x20263A1,0x200BB6B);lives=(live('msg'),live('msg','string'),live('msg','string'),live('msg'),{})
 need(len(msg['api'])==5,'nested five real caller message APIs')
 for event,(phase,entry,lr),args,context,after,last_lr,alive in zip(msg['api'],APIS,args4,saved,after_regs,last_lrs,lives):
  before,end=event['before'],event['after'];need(event['phase']==phase and event['entry']==hex(entry) and event['lr']==hex(lr) and len(before)==len(end)==16 and before[:4]==args and end[:4]==after and before[4:12]==end[4:12]==list(context)+tail and before[13]==end[13]==INNER and before[14]==lr and end[14]==last_lr and before[15]&32 and end[15]&32 and event['live']==alive and event['handle_live']is(phase!='destroy_msg'),'nested message actual caller ABI/return/lifetime')
 # Teardown R2/R3 must come from the actual native constructor, whose final
 # Party_AddMon/copy path leaves R2=2 and whose POP restores incoming R3.
 need(r['ctor_entry'][3]==r['ctor_return']['regs'][3]==0xFFFFFFFF and r['ctor_return']['regs'][2]==2 and r['body']['native_calls'][-1]['result'][2]==2 and r['body']['seed_calls'][-1]['args'][2]==2,'native constructor residual registers reach message teardown')
 services=(('Heap_AllocAtEnd',0x200BB0B,24,[11,12,729,11],[Q.SAVE,1,27,729],m,'msg'),('NARC_New',0x200BB35,24,[27,11,729,11],[m,1,27,729],h,None),('NARC_ReadFromMember',0x200BA11,56,[h,729,0,4],[31,11,Q.LOCAL+48,h],h,None),('NARC_ReadFromMember',0x200BA2B,56,[h,729,252,8],[31,11,Q.LOCAL+48,h],h,None),('Heap_Alloc',0x2026363,64,[11,length+10,0xD00E,8],[n,11,Q.LOCAL+48,h],s,'string'),('Heap_AllocAtEnd',0x200BA63,56,[11,length,0xD00E,8],[31,11,length,h],t,'temp'),('NARC_ReadFromMember',0x200BA75,56,[h,729,offset,length],[31,t,length,h],h,None),('Heap_Free',0x200BAB1,56,[t,65535,n-1,k],[0,t,length,h],t,'temp'),('Heap_Free',0x20263A1,8,[s,N.MAGIC,0,0xFFFFFFFF],[s,Q.NAME,s,1],s,'string'),('NARC_Delete',0x200BB65,8,[h,1,2,0xFFFFFFFF],[m,B.SETUP+0x10C,s,4],h,None),('Heap_Free',0x200BB6B,8,[m,1,2,0xFFFFFFFF],[m,B.SETUP+0x10C,s,4],m,'msg'))
 need(len(msg['models'])==11 and len(msg['dispatch'])==11,'nested sole SDK implementation count');reads=0
 for event,dispatch,(name,lr,depth,args,context,result,label) in zip(msg['models'],msg['dispatch'],services):
  pc=next(a for a,v in M.SDK.items() if v==name);need(event['name']==name and event['pc']==hex(pc) and event['lr']==hex(lr) and event['args']==args and event['sp']==event['return_sp']==INNER-depth and event['saved']==event['return_saved']==list(context)+tail and event['result_r0']==result and dispatch==dict(owner='message',pc=hex(pc),name=name),'nested SDK exact dispatch/ABI/model policy')
  if label:
   alloc=next(a for a in allocations if a['label']==label);need(event['label']==label and event['pointer']==alloc['pointer'] and event['bytes']==alloc['bytes'],'nested SDK allocation/free owner')
   if name!='Heap_Free':need(event['output_sha256']==sha(b'\xC7'*alloc['bytes']),'nested SDK allocation fill')
  if name=='NARC_New':need(event['opaque_handle']==h and event['native_object_layout_modeled']is False,'nested opaque native FS boundary')
  if name=='NARC_Delete':need(event['opaque_handle']==h,'nested single live NARC closure')
  if name=='NARC_ReadFromMember':
   pos,size=args[2:];digest=sha(data['message']['bank'][pos:pos+size]);need(event['read_index']==reads and event['offset']==pos and event['bytes']==size and event['destination']==(INNER-36,INNER-44,t)[reads] and event['raw_sha256']==event['delivered_sha256']==digest,'nested exact encrypted slice/destination');reads+=1
 helpers=(('lazy producer',0x200B9F8,0x200BBC7,8,[h,729,31,11],saved[1],s),('String_New',0x2026354,0x200BA51,56,[n,11,0xD00E,8],[31,11,Q.LOCAL+48,h],s),('CopyU16ArrayToStringN',0x2026A04,0x200BAAB,56,[s,t,n,k],[0,t,length,h],None),('ARM memcpy',0x20E5AD8,0x2026A35,80,[s+8,t,length,k],[n,s,length,t],s+8),('ARM memcpy',0x20E5AD8,0x2026A99,16,[Q.NAME,s+8,length,Q.TRAINER+48],[8,s+8,Q.NAME,1],Q.NAME))
 need(len(msg['native_helpers'])==5,'nested native helper count')
 for event,(name,entry,lr,depth,args,context,result) in zip(msg['native_helpers'],helpers):
  need(event['name']==name and event['entry']==hex(entry) and event['lr']==hex(lr) and event['args']==args and event['sp']==event['return_sp']==INNER-depth and event['saved']==event['return_saved']==list(context)+tail,'nested native helper actual ABI')
  if result is not None:need(event['result_r0']==result,'nested defined native pointer return')
 expected=[]
 def store(pc,address,size,value,phase):expected.append(dict(pc=hex(pc),address=address,bytes=size,value=value,phase=phase))
 def push(pc,depth,values,phase):
  for i,value in enumerate(values):store(pc,INNER-depth+4*i,4,value,phase)
 push(0x200BAF8,24,[11]+list(saved[0])+[0x20733D7],'new_msg');store(0x200BB04,INNER-24,4,11,'new_msg')
 for pc,address,size,value in ((0x200BB34,m+8,4,h),(0x200BB36,m,2,1),(0x200BB38,m+4,2,27),(0x200BB3C,m+6,2,729),(0x200BB3E,m+2,2,11)):store(pc,address,size,value,'new_msg')
 push(0x200BBA0,8,[Q.TRAINER+48,0x207342B],'new_string');push(0x200B9F8,32,[11]+list(saved[1])+[0x200BBC7],'new_string')
 for pc,address,value in ((0x200BA02,INNER-56,INNER-36),(0x200BA0A,INNER-52,729),(0x200BA1C,INNER-56,INNER-44),(0x200BA42,INNER-44,offset),(0x200BA4A,INNER-40,n)):store(pc,address,4,value,'new_string')
 push(0x2026354,64,[31,0x200BA51],'new_string')
 for pc,address,size,value in ((0x2026368,s+4,4,N.MAGIC),(0x202636A,s,2,n),(0x202636E,s+2,2,0),(0x2026372,s+8,2,65535)):store(pc,address,size,value,'new_string')
 store(0x200BA50,INNER-48,4,s,'new_string');store(0x200BA66,INNER-56,4,t,'new_string')
 for i,value in enumerate(words):store(0x200BA8E,t+2*i,2,value,'new_string')
 push(0x2026A04,80,[k,0,t,length,h,0x200BAAB],'new_string')
 for i,value in enumerate(payload):store(0x20E5AEC,s+8+i,1,value if value<128 else value|0xFFFFFF00,'new_string')
 store(0x2026A4C,s+2,2,n-1,'new_string');push(0x2026A68,16,list(saved[2][:3])+[0x2073435],'copy')
 for i,value in enumerate(payload):store(0x20E5AEC,Q.NAME+i,1,value if value<128 else value|0xFFFFFF00,'copy')
 push(0x2026380,8,[B.SETUP+4,0x207343B],'delete_string');store(0x2026398,s+4,4,N.MAGIC+1,'delete_string');push(0x200BB44,8,[B.SETUP+16,0x2073467],'destroy_msg')
 need(msg['native_writes']==expected,'nested complete native Msg stack/decrypt/object/copy/destructor write transcript')

def require_case(r,data,qualified):
 need(r['variant']=='current' and r['observe']is True and type(r['plus'])is int and r['plus']in (0,1) and r['seed']in (0x12345678,0x12345679) and type(r['poison'])is int and r['poison']in (0xC7,0x39) and r['cpu_model']==17 and not r['shadows'],'native-message caller accepted fixture domain');bind_message()
 expected_adapter=A.adapt(B,type('ProofOnly',(),dict(parent=U,factory=None))())[1];need(r['adapter']==expected_adapter,'native-message caller effective adapter/oracle identity')
 apis=r['api_calls'];need(len(apis)==3 and [a['begin'] for a in apis]==['0x201fd39','0x20733c1','0x201fd2d'] and all(a['actual_end']==a['requested_end']==hex(B.SENTINEL) for a in apis),'actual outer native setter/caller/getter API returns')
 need(apis[0]['entry'][0]==apis[0]['end'][0]==r['seed'] and apis[0]['end'][13]==OUTER and apis[1]['entry'][:3]==[B.SETUP,Q.SAVE,11] and apis[1]['entry'][4:12]==list(N.COOKIES) and apis[1]['entry'][13]==OUTER and apis[1]['entry'][14]==B.SENTINEL|1,'native caller initialized outer ABI')
 need(apis[1]['end'][:13]==r['end']['r'] and apis[1]['end'][13]==r['end']['sp']==OUTER and r['end']['r'][4:12]==list(N.COOKIES) and apis[2]['end'][0]==r['seed_after']==r['seed'],'native caller return/seed/callee-saved context')
 s=M.ARENA+64;entry,returned=r['ctor_entry'],r['ctor_return'];need(entry[:4]==[B.SETUP,1,11,0xFFFFFFFF] and entry[13]==INNER and entry[14]==0x2073445 and entry[4:12]==[B.SETUP+4,Q.NAME,s,1]+list(N.COOKIES[4:]) and returned['pc']=='0x2073444' and returned['regs'][13]==INNER and returned['regs'][4:12]==entry[4:12],'actual constructor nested ABI through native String lifetime')
 need([t['stage'] for t in r['transitions']]==['ctor','suffix'] and all(t['neutral']is True for t in r['transitions']) and r['transitions'][0]['regs']==entry and r['transitions'][1]['regs']==returned['regs'],'neutral same-context caller/constructor transitions')
 prep=r['prefix'];header=bytes.fromhex(data['preparation']['header_hex']);source=header+bytes([r['poison']])*32;payload=N.words_bytes(data['message']['oracle']['records']['31']['words']);expected=bytearray(source);expected[20:20+len(payload)]=payload;stores=[dict(pc='0x2073406' if i<12 else '0x207340e',address=Q.TRAINER+4*i,bytes=4,value=v) for i,v in enumerate(struct.unpack('<13I',source))]
 need(prep['trainer_hex']==expected.hex() and prep['local_source52']==source.hex() and prep['structure_writes']==stores and prep['calls']==r['caller_calls'] and prep['msg_live']is True and prep['string_live']is False and prep['outer_frees']==1 and prep['message_live']=={hex(M.ARENA+32):dict(label='msg',bytes=12)} and prep['handle_live']is True,'native prepared Trainer and message ownership at constructor entry')
 calls=r['caller_calls'];need(len(calls)==3 and [c['pc'] for c in calls]==['0x202a960','0x202a9a8','0x20735d8'] and all(c['sp']==c['return_sp']==INNER and c['saved']==c['return_saved'] and len(c['saved'])==8 for c in calls),'native save/header helper ABI/order')
 need(calls[0]['args'][0]==Q.SAVE and calls[0]['result_r0']==Q.MISC and calls[1]['args'][0]==Q.MISC and calls[1]['result_r0']==Q.MISC+0x270 and calls[2]['args'][:2]==[31,Q.LOCAL] and calls[2]['result_r0']==B.LOADER_RESULT,'source-derived native Save/header boundary')
 need(len(r['services'])==1 and r['services'][0]['name']=='ReadWholeNarcMemberByIdPair' and r['services'][0]['pc']=='0x2007508' and r['services'][0]['args'][:3]==[Q.LOCAL,55,31] and r['services'][0]['sp']==INNER and r['services'][0]['lr']=='0x20733fd','sole outer raw header SDK model')
 or_store=dict(pc='0x207345e',address=B.SETUP,bytes=4,value=1);need(r['or_writes']==[or_store] and r['caller_writes']==stores+[or_store] and r['caller_pcs']==sorted(qualified['caller_code']) and len(r['caller_pcs'])==138,'native caller complete stores/unchanged-value OR/PC coverage')
 need(type(r['instructions'])is int and r['instructions']==r['body']['instructions']+r['message']['instructions']+158 and r['instructions']<=3000000 and r['max_stack']==608 and r['stack_canary']is True,'native caller finite total instruction/frame bound')
 A.constructor_result(r,data,qualified);A.constructor_evidence(r,data,qualified);require_message(r,data,qualified)

def require_off_pair(observed,off):
 need(observed['observe']is True and off['observe']is False and observed['variant']==off['variant']=='current' and off['body']is None and off['message']['native_writes']==[] and off['message']['across_constructor']is None,'paired native-message caller OFF domain')
 fields=('language','plus','seed','poison','cpu_model','adapter','api_calls','ctor_entry','ctor_return','prefix','caller_pcs','caller_calls','or_writes','services','instructions','max_stack','end','seed_after','mon_hex','decoded','header','plus_hits','stack_canary','functional_ram_sha256','unrelated_ram_sha256','events','overlay','shadows')
 need(all(json.dumps(observed[k],sort_keys=True)==json.dumps(off[k],sort_keys=True) for k in fields),'native-message caller OFF/ON functional context differs')
 need([t['stage'] for t in observed['transitions']]==[t['stage'] for t in off['transitions']]==['ctor','suffix'] and all(a['regs']==b['regs'] and a['neutral']is True and b['neutral']is True for a,b in zip(observed['transitions'],off['transitions'])) and observed['transitions'][0]['ram_sha256']==off['transitions'][0]['ram_sha256'],'native-message OFF/ON transition context/entry RAM differs')
 select=lambda m:{k:v for k,v in m.items() if k not in ('native_writes','across_constructor')}
 need(json.dumps(select(observed['message']),sort_keys=True)==json.dumps(select(off['message']),sort_keys=True),'native-message producer OFF/ON functional evidence differs')
 return dict(neutral=True,scope='same complete caller/native-message APIs,6packets,prepared Trainer,seed,SDK dispatch and declared global RAM; stack/constructor heap/message scratch excluded from digest and separately guarded',functional_ram_sha256=observed['functional_ram_sha256'],party_sha256=sha(b''.join(bytes.fromhex(x) for x in observed['mon_hex'])))

def source_identities():
 result=U.source_identities()
 for path in (__file__,M.__file__,A.__file__):result[str(Path(path).resolve().relative_to(P.SOURCE))]=sha(Path(path).read_bytes())
 return result

def require_counter(counter,normal,data,qualified):
 variant=counter['variant'];need(variant in ('omit_temp_free','omit_msg_free','wrong_read_destination','high_level_stub'),'native-message caller counter domain')
 if counter['completed']:
  need(variant in ('omit_temp_free','omit_msg_free') and counter['tag_disguised']is True,'native-message completed counter domain');r=counter['result'];need(r['variant']==variant and r['mon_hex']==normal['mon_hex'] and r['prefix']['trainer_hex']==normal['prefix']['trainer_hex'] and r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['message']['canaries']is True,'same-whole-party/Trainer/seed/RAM counter premise')
  alloc=r['message']['allocations'];label='temp' if variant=='omit_temp_free' else 'msg';a=next(a for a in alloc if a['label']==label);need(r['message']['live']=={hex(a['pointer']):dict(label=label,bytes=a['bytes'])} and r['message']['handle_live']is False,'counter isolated leaked allocation/closed NARC')
  if variant=='omit_temp_free':need(r['message']['temp_deleted']is False and r['message']['shadows']==[dict(pc='0x200baac',kind='skip native free/delete BL',next_pc='0x200bab0')] and r['shadows']==[],'counter actual temporary free omission')
  else:need(r['message']['temp_deleted']is True and r['message']['shadows']==[] and r['shadows']==[dict(pc='0x200bb66',kind='skip native MsgData free BL')],'counter actual final MsgData free omission')
  need(r['instructions']==normal['instructions']-1 and r['message']['instructions']==normal['message']['instructions']-1,'counter exact skipped SDK call path count')
  disguised=copy.deepcopy(r);disguised['variant']='current';disguised['shadows']=[];disguised['message']['shadows']=[]
  try:require_case(disguised,data,qualified)
  except ValueError as e:need(str(e)==counter['rejection'],'counter expected pure replay cause')
  else:raise ValueError('native-message caller counter evidence accepted')
 else:
  need(variant in ('wrong_read_destination','high_level_stub') and counter['stage']=='prefix' and counter['constructor_entered']is False and counter['party_count']==0 and counter['top_after_exception']==hex(OUTER),'counter actual pre-constructor stage/context')
  if variant=='wrong_read_destination':need(counter['pc']=='0x200782c' and counter['rejection']=='native NARC encrypted-slice ABI/destination' and counter['message_phase']=='new_string' and counter['message_api_completed']==1 and counter['message_reads']==2 and len(counter['message_models'])==6 and len(counter['message_shadows'])==1 and counter['message_shadows'][0]['kind']=='stack argument','counter actual encrypted read destination refusal')
  else:need(counter['pc']=='0x200baf8' and counter['rejection']=='native message live entry bytes drift' and counter['message_phase']is None and counter['message_api_completed']==0 and counter['message_reads']==0 and counter['message_models']==[] and counter['shadows']==[dict(pc='0x200baf8',kind='post-qualification high-level stub overwrite')],'counter actual live native-body overwrite refusal')

def analyze(rom,language,objects,strategy_object):
 sources=source_identities();model=P.G.S.SHARED.read_current(rom,language);positives=[];guards=[];off_cases=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  qualified,proof=qualify(model,raw,language,objects,strategy_object);data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31),message=M.resources(raw))
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    result=run_case(model,raw,language,qualified,data,plus,seed);require_case(result,data,qualified);positives.append(result);print(language,'native message caller',plus,hex(seed),'verified',flush=True)
   off=run_case(model,raw,language,qualified,data,plus,observe=False);off_cases.append(dict(result=off,proof=require_off_pair(positives[-2],off)))
  normal=next(r for r in positives if r['plus']==1 and r['seed']==0x12345678);guard=run_case(model,raw,language,qualified,data,poison=0x39);require_case(guard,data,qualified);need(guard['mon_hex']==normal['mon_hex'] and guard['message']['snapshots']['string']==normal['message']['snapshots']['string'],'stack poison cannot alter native message String or complete party');guards.append(guard)
  for variant in ('omit_temp_free','omit_msg_free','wrong_read_destination','high_level_stub'):
   try:result=run_case(model,raw,language,qualified,data,variant=variant)
   except ValueError as e:
    d=Driver.latest;need(d is not None and hasattr(d,'u') and B.STACK_TOP==OUTER,'counter initialized CPU/observer scope');count=d.word(B.PARTIES+0x1000+4);counter=dict(variant=variant,completed=False,rejection=str(e),stage=d.stage,pc=hex(d.u.reg_read(UC_ARM_REG_PC)),constructor_entered=d.ctor_entry is not None,party_count=count,top_after_exception=hex(B.STACK_TOP),message_phase=d.message.phase,message_api_completed=len(d.message_api),message_reads=d.message.reads,message_models=d.message.models,message_shadows=d.message.shadows,shadows=d.shadows)
   else:
    disguised=copy.deepcopy(result);disguised['variant']='current';disguised['shadows']=[];disguised['message']['shadows']=[]
    try:require_case(disguised,data,qualified)
    except ValueError as e:counter=dict(variant=variant,completed=True,rejection=str(e),result=result,tag_disguised=True)
    else:raise ValueError('native-message caller negative accepted: '+variant)
   require_counter(counter,normal,data,qualified);counters.append(counter)
  summary=T.resource_summary(data['constructor'],[r['body'] for r in positives+guards]);need(source_identities()==sources,'native-message caller source drift during campaign')
 return dict(schema='trainer31-native-message-caller-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,resources=dict(preparation=data['preparation'],constructor=summary,message=data['message']['oracle']),positives=positives,guards=guards,observer_off=off_cases,counters=counters,compiler_invoked=False,limits=['Initialized caller31 IDs[0,31,0,0],battleType1,heap11,Plus0/1,cap100,2seeds,2stackpoisons,heapfillC7 only','Six message SDK heap/NARC models, constructor SDK/overlay FS and species-name model remain explicit boundaries','Sparse SaveData is a readonly synthetic fixture, not raw-save/Continue/SAVE/hardware coverage','Native message and constructor run in the same CPU/RAM without a context or packet bridge','Original native MW and old Plus compiler/object reconstruction unavailable; retained project objects and byte readback have separate proofs','No natural encounter,otherIDs/rival/multi-ID/error/allocator failure,whole battle,renderer or physical timing claim'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'native-message caller inputs must exist');result=analyze(args.rom,args.language,args.objects,args.strategy_object);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024**2,'expanded native-message caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024**2,'stored native-message caller report budget');args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'finite native-message/caller composition verified; native SDK bodies and natural encounters remain separate')

if __name__=='__main__':main()
