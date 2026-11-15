#!/usr/bin/env python3
"""Run six native species-name lifetimes inside the exact trainer31 caller.

Private ROMs and retained project objects are required. Six SDK heap/archive
services remain explicit models; natural encounter activation is separate.
"""
from pathlib import Path
import importlib.util,types,struct,copy,json,gzip,mmap,gc,sys

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
V=load('species_full_message_caller',Path(__file__).with_name('attribuisci_messaggi_chiamante.py'))
W=load('species_full_native_names',Path(__file__).with_name('attribuisci_nome_specie.py'))
A=load('species_full_adapter',Path(__file__).parents[1]/'test/caller_species_bench.py')
U,M,B,T,P,Q,N,need,sha=V.U,V.M,V.B,V.T,V.P,V.Q,V.N,V.need,V.sha
OUTER,INNER=V.OUTER,V.INNER
NAME_ARENA,NAME_END,NAME_HANDLE=0x2370000,0x2371000,0x2370800
NAME_TOP=OUTER-496
NATIVE_PINS={'tools/attribuisci_nome_specie.py': '0adc3a077d50c848fba7bc744d53700bbabceff08b6a695decd6b3614a789525', 'test/species_name_bench.py': 'a01b2f95cc6ae8df05c08bc58ff9591196fd3b96efe646296f30d4a9d68dae37'}
for _name,_hash in NATIVE_PINS.items():need(sha((Path(__file__).parents[1]/_name).read_bytes())==_hash,'native species observer/profile source drift')
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_CPSR
NAME_APIS=(('get_species',W.ENTRY,0x206F4B7),('copy',0x2026A68,0x206F4C1),('delete',0x2026380,0x206F4C7))

def qualify(model,raw,language,objects,strategy_object):
 qualified,proof=V.qualify(model,raw,language,objects,strategy_object);names,locations=W.qualify(model,raw);qualified['names']=names;proof['native_species']=locations
 for pc,shape in names['all'].items():
  for old in ('body_code','message_code','caller_code'):
   need(pc not in qualified[old] or qualified[old][pc]==shape,'native species overlap ISA/width drift')
 return qualified,proof

class NativeName(W.Species):
 """Only observer bindings change; no standalone CPU/API runner is called."""
 def __init__(self,driver,species,destination):
  super().__init__(None,driver.qualified['names'],driver.data['names'],species,fill=0,observe=driver.observe)
  self.driver=driver;self.u=self.core.u=driver.u;self.top=NAME_TOP;self.destination=destination
  self.namespace.update(TOP=NAME_TOP-16,ARENA=NAME_ARENA,ARENA_END=NAME_END,HANDLE=NAME_HANDLE,DEST=destination)
  self.core.cursor=NAME_ARENA+32
  namespace=dict(vars(W));namespace.update(TOP=NAME_TOP,INNER=NAME_TOP-16)
  for name in ('scope','step','read','write'):
   method=getattr(W.Species,name);setattr(self,name,types.MethodType(types.FunctionType(method.__code__,namespace,method.__name__,method.__defaults__,method.__closure__),self))
  # Message.step normally invokes a model itself. The caller bench has one
  # callback dispatcher, so its SDK branch counts/guards and defers to that.
  original=self.core.step
  def step(core,u,pc,n,user):
   if pc in M.SDK:
    core.steps+=1;regs=core.regs();sp=regs[13];top=self.namespace['TOP'];need(core.steps<=20000 and top-128<=sp<=top and sp%8==0 and n==2 and regs[15]&32,'nested species SDK boundary encoding/frame');core.max_stack=max(core.max_stack,top-sp);need(driver.name_pending_sdk is None,'single nested species SDK pending');driver.name_pending_sdk=(pc,regs);return
   original(u,pc,n,user)
  self.core.step=types.MethodType(step,self.core)
  self.outer_phase='get_species';self.entry=None;self.destination_before=driver.read_bytes(destination,22).hex()
 def begin(self,regs):
  index=len(self.api);phase,entry,lr=NAME_APIS[index];need(regs[13]==NAME_TOP and regs[14]==lr and regs[15]&32,'actual species outer frame/return caller');need(not self.core.pending and self.driver.name_pending_sdk is None,'species API pending closure')
  if index==0:need(regs[:2]==[self.species,0],'actual constructor species/default heap ABI')
  else:need(regs[0]==self.core.pointer['string'] and (index==2 or regs[1:3]==[self.destination,11]),'actual borrowed species String/capacity/destination ABI')
  self.outer_phase=phase
  if index:self.scope(NAME_TOP,'copy' if phase=='copy' else 'delete_string')
  self.entry=dict(phase=phase,entry=hex(entry),lr=hex(lr),before=regs)
 def finish(self,regs):
  event=self.entry;before=event['before'];need(regs[13]==before[13]==NAME_TOP and regs[4:12]==before[4:12] and regs[15]&32 and self.current_internal is None and not self.core.pending and self.driver.name_pending_sdk is None,'actual species API return context')
  if event['phase']=='get_species':need(regs[0]==self.core.pointer['string'],'actual native species pointer return');self.snapshots['returned_string']=self.read_bytes(regs[0],len(self.core.payload)+10).hex()
  event.update(after=regs,live={hex(p):dict(v) for p,v in self.core.live.items()},handle_live=self.core.handle_live);self.api.append(event);self.entry=None
 def receipt(self):
  c=self.core;need(len(self.api)==3,'three actual species returns before receipt')
  return dict(species=self.species,heap=0,bank=237,fill=0,profile=self.profile,api=self.api,internal=self.internal,snapshots=self.snapshots,models=c.models,native_helpers=c.helpers,native_writes=c.writes,wrapper_writes=self.wrapper_writes,writes=self.writes,observed_pcs=sorted(self.wrapper_seen|c.seen),allocations=[dict(pointer=p,bytes=size,label=label) for p,size,label in c.allocs],live={hex(p):dict(v) for p,v in c.live.items()},handle_live=c.handle_live,temp_deleted=c.temp_deleted,dead_store=c.dead_store,reads=c.reads,canaries=all(self.read_bytes(p-8,8)==b'\xA5'*8 and self.read_bytes(p+size,8)==b'\xA5'*8 for p,size,label in c.allocs),destination=self.destination,destination_before=self.destination_before,destination_hex=self.read_bytes(self.destination,22).hex(),transitions=self.transitions,shadows=self.shadows+c.shadows,instructions=self.steps,max_stack=self.max_stack,same_cpu=c.u is self.driver.u)

class Driver(V.Driver):
 composition=V
 latest=None
 def __init__(self,*args,**kwargs):
  name_variant=kwargs.pop('variant','current');need(name_variant in ('current','omit_name_free','skip_name_destroy','wrong_name_bank','name_high_level_stub'),'finite species composition variant');super().__init__(*args,variant='current',**kwargs);self.name_variant=name_variant;Driver.latest=self;self.species_name_controller=None;self.name_active=False;self.name_results=[];self.name_dispatch=[];self.name_pending_sdk=None;self.names_code_live=False
 def configure(self,cpu,implementations,events,state,handles):
  result=super().configure(cpu,implementations,events,state,handles)
  for pc,name in M.SDK.items():
   parent=result[name]
   def dispatch(u,pc=pc,name=name,parent=parent):
    if self.name_active:
     need(u is self.u is self.species_name_controller.core.u and self.name_pending_sdk==(pc,self.regs()),'single species owner/SDK entry context');self.name_pending_sdk=None;self.species_name_controller.core.service(pc);self.name_dispatch.append(dict(slot=len(self.name_results),pc=hex(pc),name=name,owner='species_heap0'))
    else:
     if self.stage=='ctor' and name in ('Heap_Free','NARC_ReadFromMember','NARC_Delete'):need(not NAME_ARENA<=self.regs()[0]<NAME_END,'constructor SDK cannot borrow name object/handle')
     parent(u)
   result[name]=dispatch
  return result
 def prepare(self,cpu):
  super().prepare(cpu);cpu.mem_write(NAME_ARENA,b'\xD3'*(NAME_END-NAME_ARENA))
  for pc,(n,thumb) in self.qualified['names']['all'].items():need(self.read_bytes(pc,n)==P.G.piece(self.bench.segments,pc,n),'native species code overwritten before full caller')
  self.names_code_live=True
  if self.name_variant=='name_high_level_stub':cpu.mem_write(W.ENTRY,b'\x70\x47');self.shadows.append(dict(pc=hex(W.ENTRY),kind='post-qualification species stub overwrite'))
 def name_spans(self):return sorted(set((a['pointer']-8,a['pointer']+a['bytes']+8) for r in self.name_results for a in r['allocations']))
 def collect_body(self):return collect_message_body(self)
 def step(self,u,pc,n,user):
  if self.name_active and pc==int(self.species_name_controller.entry['lr'],16)&~1:
   self.species_name_controller.finish(self.regs());self.name_active=False
   if len(self.species_name_controller.api)==3:self.name_results.append(self.species_name_controller.receipt());self.species_name_controller=None
  if self.stage=='ctor':
   if pc==W.ENTRY:
    need(self.species_name_controller is None and len(self.name_results)<6 and (not self.observe or self.audit.pending_service is None),'no concurrent species or constructor SDK owner');need(self.read_bytes(pc,2)==P.G.piece(self.bench.segments,pc,2),'native species live entry bytes drift');species=W.SPECIES[len(self.name_results)];dest=self.word(self.regs()[13]+8);self.species_name_controller=NativeName(self,species,dest)
    if len(self.name_results)==5 and self.name_variant in ('omit_name_free','skip_name_destroy'):self.species_name_controller.variant='omit_string_free' if self.name_variant=='omit_name_free' else 'skip_destroy'
    if len(self.name_results)==0 and self.name_variant=='wrong_name_bank':self.species_name_controller.variant='wrong_bank'
   if self.species_name_controller is not None and pc in {x[1] for x in NAME_APIS} and not self.name_active:
    need(pc==NAME_APIS[len(self.species_name_controller.api)][1],'species actual API order');self.species_name_controller.begin(self.regs());self.name_active=True
  if self.name_active:
   self.steps+=1;sp=self.regs()[13];need(self.steps<=3000000 and OUTER-608<=sp<=INNER,'native species/full caller stack budget');self.max_stack=max(self.max_stack,OUTER-sp)
   self.species_name_controller.step(u,pc,n,user);return
  super().step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.name_active:self.species_name_controller.read(u,access,address,n,value,user);return
  super().read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  if self.name_active:self.species_name_controller.write(u,access,address,n,value,user);return
  super().write(u,access,address,n,value,user)

def bindings():
 collect_constructor,p1=A.rewrite(U,'Driver.collect_body',[(";need(P.masked_hash(a.before,ignored)",";ignored+=self.name_spans();need(P.masked_hash(a.before,ignored)",1)],{'__source_kind__':'caller'})
 collect_message,p2=A.rewrite(V,'Driver.collect_body',[("super().collect_body()","collect_constructor(self)",1)],{'collect_constructor':collect_constructor})
 run,p3=A.rewrite(V,'run_case',[("]+[(p-8,p+size+8) for p,size,label in message.allocs]","]+[(p-8,p+size+8) for p,size,label in message.allocs]+driver.name_spans()",1),("(M.ARENA,M.ARENA_END)]","(M.ARENA,M.ARENA_END),(NAME_ARENA,NAME_END)]",1),("return dict(language=language,plus=plus","return dict(names=driver.name_results,name_dispatch=driver.name_dispatch,names_code_live=driver.names_code_live,language=language,plus=plus",1)],{'Driver':Driver,'A':A,'NAME_ARENA':NAME_ARENA,'NAME_END':NAME_END})
 require,p4=A.rewrite(V,'require_case',[("r['body']['instructions']+r['message']['instructions']+158","r['body']['instructions']+r['message']['instructions']+sum(x['instructions'] for x in r['names'])+158",1),("dict(parent=U,factory=None)","dict(parent=U,composition=V,factory=None)",1)],{'V':V,'A':types.SimpleNamespace(adapt=A.adapt,constructor_result=V.A.constructor_result,constructor_evidence=V.A.constructor_evidence)})
 return collect_message,run,require,[p1,p2,p3,p4]
collect_message_body,run_case,require_parent,RECIPES=bindings()

def require_name(r,data,qualified,expected):
 fields=expected['fields'];species=fields['species'];fill=0;control=None;TOP=NAME_TOP;INNER=NAME_TOP-16
 order=B.PERMUTATIONS[((fields['pid']>>13)&31)%24];blocks=[B.ARENA+136+32*order.index(i) for i in range(4)];DEST=blocks[2]
 need(r['species']==species and r['heap']==0 and r['bank']==237 and r['fill']==0 and r['same_cpu']is True and not r['shadows'],'native species caller receipt domain/identity')
 need(r['profile']==W.A.profile(W.M)[2],'native species SDK finite profile authentication')
 record=data['oracle']['records'][str(species)];words=record['words'];payload=N.words_bytes(words);n=len(words);length=2*n;k=((species+1)*596947+n*18749)&65535;offset=record['entry_bank_offset'];m,s=NAME_ARENA+32,NAME_ARENA+64;t=s+((length+33)&~7);h=NAME_HANDLE;cookies=[0,blocks[1],blocks[3],blocks[0]]+list(N.COOKIES[4:]);c4,c5,c6,c7=cookies[:4];tail=cookies[4:];cookie3=fields['otid']&65535
 allocs=[dict(pointer=m,bytes=12,label='msg'),dict(pointer=s,bytes=length+10,label='string'),dict(pointer=t,bytes=length,label='temp')];need(r['allocations']==allocs and r['live']=={} and r['handle_live']is False and r['reads']==3 and r['temp_deleted']is True and r['dead_store']is True and r['canaries']is True,'species object ownership/canary/frozen global state')
 string=struct.pack('<HHI',n,n-1,N.MAGIC)+payload+bytes([fill])*2;need(r['snapshots']==dict(msg=struct.pack('<HHHHI',1,0,27,237,h).hex(),string=string.hex(),returned_string=string.hex()),'native species Msg/String fields and unchanged returned String')
 dest=payload+bytes(22-length);need(r['destination']==DEST and r['destination_before']==bytes(22).hex() and r['destination_hex']==dest.hex(),'species native copy exact EOS/prefix/untouched destination tail')
 need(r['instructions']==233+34*n and r['instructions']<=20000 and r['max_stack']==96 and r['observed_pcs']==sorted(qualified['all']) and len(r['observed_pcs'])==244,'species exact native PC/hook/frame coverage')
 live=lambda *labels:{hex(a['pointer']):dict(label=a['label'],bytes=a['bytes']) for a in allocs if a['label']in labels}
 api_specs=(('get_species',W.ENTRY,0x206F4B7,[species,0,3,cookie3],[s,65535,n-1,cookie3],cookies,0x200BB6B,live('string')),('copy',0x2026A68,0x206F4C1,[s,DEST,11,cookie3],[DEST,s+8+length,0,0xFFFFFFFF],[s]+cookies[1:],0x2026A99,live('string')),('delete',0x2026380,0x206F4C7,[s,s+8+length,0,0xFFFFFFFF],[s,N.MAGIC,0,0xFFFFFFFF],[s]+cookies[1:],0x20263A1,{}))
 need(len(r['api'])==3,'three actual species caller API returns')
 for event,(phase,entry,lr,before4,after4,saved,last_lr,alive) in zip(r['api'],api_specs):
  before,after=event['before'],event['after'];need(event['phase']==phase and event['entry']==hex(entry) and event['lr']==hex(lr) and len(before)==len(after)==16 and before[:4]==before4 and before[4:12]==after[4:12]==saved and before[13]==after[13]==TOP and before[14]==lr and after[14]==last_lr and before[15]&32 and after[15]&32 and event['live']==alive and event['handle_live']is False,'source-derived species actual caller ABI/lifetime')
  need(after[:4]==after4,'source-derived species defined native/residual registers')
 internal_specs=(('new_msg',0x200BAF8,0x200BCED,[1,27,237,0],[species,c5,c6,c7],[m,0,237,0],0x200BB35,live('msg'),True),('new_string',0x200BBA0,0x200BCF7,[m,species,237,0],[species,m,c6,c7],[s,65535,n-1,0],0x200BAB1,live('msg','string'),True),('destroy_msg',0x200BB44,0x200BCFF,[m,65535,n-1,0],[s,m,c6,c7],[None,65535,n-1,0],0x200BB6B,live('string'),False))
 need(len(r['internal'])==3,'species three actual internal message APIs')
 for event,(phase,entry,lr,args,context,after4,last_lr,alive,handle) in zip(r['internal'],internal_specs):
  before,after=event['before'],event['after'];need(event['phase']==phase and event['entry']==hex(entry) and event['lr']==hex(lr) and len(before)==len(after)==16 and before[:4]==args and before[4:12]==after[4:12]==context+tail and before[13]==after[13]==INNER and before[14]==lr and after[14]==last_lr and before[15]&32 and after[15]&32 and event['live']==alive and event['handle_live']is handle,'species native wrapper internal ABI/lifetime order')
  need(all(value is None or after[i]==value for i,value in enumerate(after4)),'species internal defined pointer/register source binding')
 transitions=r['transitions'];need(len(transitions)==5 and [(x['top'],x['phase']) for x in transitions]==[(INNER,'new_msg'),(INNER,'new_string'),(INNER,'destroy_msg'),(TOP,'copy'),(TOP,'delete_string')] and all(x['neutral']is True for x in transitions),'species observer nested/outer stack scopes')
 need([x['regs'] for x in transitions]==[x['before'] for x in r['internal']]+[r['api'][1]['before'],r['api'][2]['before']],'species scope transition uses actual untouched CPU context')
 specs=(('Heap_AllocAtEnd',0x200BB0B,INNER-24,[0,12,237,0],[species,1,27,237],m,'msg'),('NARC_New',0x200BB35,INNER-24,[27,0,237,0],[m,1,27,237],h,None),('NARC_ReadFromMember',0x200BA11,INNER-56,[h,237,0,4],[species,0,c6,h],None,None),('NARC_ReadFromMember',0x200BA2B,INNER-56,[h,237,4+8*species,8],[species,0,c6,h],None,None),('Heap_Alloc',0x2026363,INNER-64,[0,length+10,0xD00E,8],[n,0,c6,h],s,'string'),('Heap_AllocAtEnd',0x200BA63,INNER-56,[0,length,0xD00E,8],[species,0,length,h],t,'temp'),('NARC_ReadFromMember',0x200BA75,INNER-56,[h,237,offset,length],[species,t,length,h],None,None),('Heap_Free',0x200BAB1,INNER-56,[t,65535,n-1,k],[0,t,length,h],None,'temp'),('NARC_Delete',0x200BB65,INNER-8,[h,65535,n-1,0],[m,m,c6,c7],None,None),('Heap_Free',0x200BB6B,INNER-8,[m,65535,n-1,0],[m,m,c6,c7],None,'msg'),('Heap_Free',0x20263A1,TOP-8,[s,N.MAGIC,0,0xFFFFFFFF],[s,c5,c6,c7],None,'string'))
 need(len(r['models'])==11,'species SDK exact source order/count');reads=0
 for event,(name,lr,sp,args,context,result,label) in zip(r['models'],specs):
  pc=next(a for a,v in M.SDK.items() if v==name);need(event['name']==name and event['pc']==hex(pc) and event['lr']==hex(lr) and event['sp']==event['return_sp']==sp and event['args']==args and event['saved']==event['return_saved']==context+tail,'species SDK source-derived ABI and preserved context')
  if result is not None:need(event['result_r0']==result,'species modeled pointer result')
  elif control is not None:need(event['result_r0']==control,'species declared void-R0 control')
  if label:
   alloc=next(a for a in allocs if a['label']==label);need(event['label']==label and event['pointer']==alloc['pointer'] and event['bytes']==alloc['bytes'],'species SDK allocation/free owner')
   if name!='Heap_Free':need(event['output_sha256']==sha(bytes([fill])*alloc['bytes']),'species heap initial fill provenance')
  if name=='NARC_New':need(event['opaque_handle']==h and event['native_object_layout_modeled']is False,'species opaque NARC model boundary')
  if name=='NARC_Delete':need(event['opaque_handle']==h,'species single NARC destruction')
  if name=='NARC_ReadFromMember':
   pos,size=args[2:];digest=sha(data['bank'][pos:pos+size]);need(event['read_index']==reads and event['offset']==pos and event['bytes']==size and event['destination']==(INNER-36,INNER-44,t)[reads] and event['raw_sha256']==event['delivered_sha256']==digest,'species exact encrypted read index/slice/destination');reads+=1
 helpers=(('lazy producer',0x200B9F8,0x200BBC7,INNER-8,[h,237,species,0],[species,m,c6,c7],s),('String_New',0x2026354,0x200BA51,INNER-56,[n,0,0xD00E,8],[species,0,c6,h],s),('CopyU16ArrayToStringN',0x2026A04,0x200BAAB,INNER-56,[s,t,n,k],[0,t,length,h],None),('ARM memcpy',0x20E5AD8,0x2026A35,INNER-80,[s+8,t,length,k],[n,s,length,t],s+8),('ARM memcpy',0x20E5AD8,0x2026A99,TOP-16,[DEST,s+8,length,cookie3],[11,s+8,DEST,c7],DEST))
 need(len(r['native_helpers'])==5,'species five actual nested helpers')
 for event,(name,entry,lr,sp,args,context,result) in zip(r['native_helpers'],helpers):
  need(event['name']==name and event['entry']==hex(entry) and event['lr']==hex(lr) and event['sp']==event['return_sp']==sp and event['args']==args and event['saved']==event['return_saved']==context+tail,'species actual native helper ABI/return')
  if result is not None:need(event['result_r0']==result,'species defined native helper pointer return')
 expected=[]
 def store(pc,address,size,value,phase):expected.append(dict(pc=hex(pc),address=address,bytes=size,value=value,phase=phase))
 def push(pc,base,values,phase):
  for i,value in enumerate(values):store(pc,base+4*i,4,value,phase)
 push(W.ENTRY,TOP-16,[cookie3,c4,c5,0x206F4B7],'get_species')
 push(0x200BAF8,INNER-24,[0,species,c5,c6,c7,0x200BCED],'new_msg');store(0x200BB04,INNER-24,4,0,'new_msg')
 for pc,address,size,value in ((0x200BB34,m+8,4,h),(0x200BB36,m,2,1),(0x200BB38,m+4,2,27),(0x200BB3C,m+6,2,237),(0x200BB3E,m+2,2,0)):store(pc,address,size,value,'new_msg')
 push(0x200BBA0,INNER-8,[0,0x200BCF7],'new_string');push(0x200B9F8,INNER-32,[0,species,m,c6,c7,0x200BBC7],'new_string')
 for pc,address,value in ((0x200BA02,INNER-56,INNER-36),(0x200BA0A,INNER-52,237),(0x200BA1C,INNER-56,INNER-44),(0x200BA42,INNER-44,offset),(0x200BA4A,INNER-40,n)):store(pc,address,4,value,'new_string')
 push(0x2026354,INNER-64,[species,0x200BA51],'new_string')
 for pc,address,size,value in ((0x2026368,s+4,4,N.MAGIC),(0x202636A,s,2,n),(0x202636E,s+2,2,0),(0x2026372,s+8,2,65535)):store(pc,address,size,value,'new_string')
 store(0x200BA50,INNER-48,4,s,'new_string');store(0x200BA66,INNER-56,4,t,'new_string')
 for i,value in enumerate(words):store(0x200BA8E,t+2*i,2,value,'new_string')
 push(0x2026A04,INNER-80,[k,0,t,length,h,0x200BAAB],'new_string')
 for i,value in enumerate(payload):store(0x20E5AEC,s+8+i,1,value if value<128 else value|0xFFFFFF00,'new_string')
 store(0x2026A4C,s+2,2,n-1,'new_string');push(0x200BB44,INNER-8,[s,0x200BCFF],'destroy_msg');push(0x2026A68,TOP-16,[s,c5,c6,0x206F4C1],'copy')
 for i,value in enumerate(payload):store(0x20E5AEC,DEST+i,1,value if value<128 else value|0xFFFFFF00,'copy')
 push(0x2026380,TOP-8,[s,0x206F4C7],'delete_string');store(0x2026398,s+4,4,N.MAGIC+1,'delete_string')
 need(r['writes']==expected,'species entire ordered native wrapper/stack/decrypt/object/copy/destructor writes')
 need(r['wrapper_writes']==[{k:v for k,v in e.items() if k!='phase'} for e in expected[:4]] and r['native_writes']==expected[4:],'species retained component write transcripts')


def require_case(r,data,qualified):
 require_parent(r,data,qualified)
 need(r['names_code_live']is True and len(r['names'])==6 and len(r['name_dispatch'])==66,'six native species lifetimes/sole SDK dispatch')
 need(not any(e['name']=='GetSpeciesName' for e in r['body']['models']) and not any(e[0]=='name' for e in r['events']),'no modeled species producer or phantom constructor allocation')
 for slot,(name,record) in enumerate(zip(r['names'],T.expected(data['constructor'],r['plus']))):
  require_name(name,data['names'],qualified['names'],record)
  need(r['name_dispatch'][slot*11:(slot+1)*11]==[dict(slot=slot,pc=e['pc'],name=e['name'],owner='species_heap0') for e in name['models']],'separate species SDK dispatch exactly once')
 need(sum(n['instructions'] for n in r['names'])==3098 and all(n['max_stack']==96 for n in r['names']),'six species exact native steps and local frames')
 return True

def name_functional(r):
 result=copy.deepcopy({k:v for k,v in r.items() if k not in ('writes','native_writes','wrapper_writes')})
 for transition in result['transitions']:transition.pop('ram_sha256')
 return result

def require_off_pair(on,off):
 proof=V.require_off_pair(on,off)
 need(on['names_code_live']is off['names_code_live']is True and on['name_dispatch']==off['name_dispatch'] and len(on['names'])==len(off['names'])==6,'native species paired OFF owners/coverage')
 for a,b in zip(on['names'],off['names']):
  need(b['writes']==b['native_writes']==b['wrapper_writes']==[],'native species OFF has no native store logs')
  need(name_functional(a)==name_functional(b),'native species complete OFF/ON context/models/objects differ')
 return dict(neutral=True,parent=proof,names='all six API/internal ABI, decrypted String/copy, ownership, SDK dispatch and scope contexts identical; native write logs disabled; raw scope RAM hashes excluded for inherited constructor scratch, neutral transitions retained')

def require_counter(c,normal,data,qualified):
 variant=c['variant'];need(variant in ('omit_name_free','skip_name_destroy','wrong_name_bank','name_high_level_stub'),'finite composed species counter')
 if c['completed']:
  need(variant in ('omit_name_free','skip_name_destroy') and c['tag_disguised']is True,'completed species leak counter domain');r=c['result'];need(len(r['names'])==len(normal['names'])==6,'counter requires all six native name lifetimes');last=r['names'][-1];good=normal['names'][-1];n=data['names']['oracle']['records']['94']['raw_words'];s=NAME_ARENA+64;m=NAME_ARENA+32
  need(r['mon_hex']==normal['mon_hex'] and r['header']==normal['header'] and r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['message']==normal['message'] and r['unrelated_ram_sha256']==normal['unrelated_ram_sha256'] and last['destination_hex']==good['destination_hex'] and last['snapshots']==good['snapshots'] and all(name_functional(a)==name_functional(b) for a,b in zip(r['names'][:-1],normal['names'][:-1])),'same complete party/name/seed/frozen state leak counter premise')
  if variant=='omit_name_free':need(last['live']=={hex(s):dict(label='string',bytes=2*n+10)} and last['handle_live']is False and len(last['models'])==10 and len(last['internal'])==3 and last['instructions']==good['instructions']-1 and last['dead_store']is True and last['shadows']==[dict(pc='0x202639c',kind='skip native String free BL')],'last native name dead-magic String leak cause')
  else:need(last['live']=={hex(m):dict(label='msg',bytes=12)} and last['handle_live']is True and len(last['models'])==9 and len(last['internal'])==2 and last['instructions']==good['instructions']-15 and last['shadows']==[dict(pc='0x200bcfa',kind='skip native MsgData destruction BL')],'last native name live MsgData/NARC leak cause')
  delta=1 if variant=='omit_name_free' else 15
  expected_models=good['models'][:-1] if variant=='omit_name_free' else good['models'][:8]+good['models'][10:]
  expected_dispatch=normal['name_dispatch'][:55]+[dict(slot=5,pc=e['pc'],name=e['name'],owner='species_heap0') for e in expected_models]
  need(r['instructions']==normal['instructions']-delta and last['models']==expected_models and r['name_dispatch']==expected_dispatch and len(r['name_dispatch'])==(65 if variant=='omit_name_free' else 64),'last-only leak exact SDK dispatch and global step delta')
  disguised=copy.deepcopy(r);disguised['variant']='current';disguised['names'][-1]['shadows']=[]
  try:require_case(disguised,data,qualified)
  except ValueError as e:need(str(e)==c['rejection']=='six native species lifetimes/sole SDK dispatch','native species leak counter exact oracle rejection')
  else:raise ValueError('same-party native species leak accepted')
 else:
  need(variant in ('wrong_name_bank','name_high_level_stub') and c['stage']=='ctor' and c['constructor_entered']is True and c['party_count']==0 and c['names_completed']==0 and c['top_after_exception']==hex(OUTER),'native species early counter actual constructor context')
  if variant=='wrong_name_bank':need(c['pc']=='0x200782c' and c['rejection']=='native NARC encrypted-slice ABI/destination' and c['name_phase']=='get_species' and c['name_internal']==1 and c['name_reads']==0 and len(c['name_models'])==2 and c['name_shadows']==[dict(pc='0x200bce8',kind='native bank argument shadow',before=237,after=729)],'native species wrong bank causal first encrypted read refusal')
  else:need(c['pc']==hex(W.ENTRY) and c['rejection']=='native species live entry bytes drift' and c['name_phase']is None and c['name_models']==[] and c['shadows']==[dict(pc=hex(W.ENTRY),kind='post-qualification species stub overwrite')],'native species live body stub refused before entry')

def source_identities():
 paths={P.SOURCE/name for name in set(V.source_identities())|set(W.source_identities())}|{Path(__file__),Path(A.__file__)}
 return {str(p.resolve().relative_to(P.SOURCE)):sha(p.read_bytes()) for p in sorted(paths)}

def analyze(rom,language,objects,strategy_object):
 W.require_host_budget();sources=source_identities();model=P.G.S.SHARED.read_current(rom,language);positive=[];guards=[];off=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  qualified,proof=qualify(model,raw,language,objects,strategy_object);data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31),message=M.resources(raw),names=W.resources(raw))
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,qualified,data,plus,seed);require_case(r,data,qualified);positive.append(r);print(language,'native species full caller',plus,hex(seed),'verified',flush=True)
   r=run_case(model,raw,language,qualified,data,plus,observe=False);off.append(dict(result=r,proof=require_off_pair(positive[-2],r)))
  normal=next(r for r in positive if r['plus']==1 and r['seed']==0x12345678);r=run_case(model,raw,language,qualified,data,poison=0x39);require_case(r,data,qualified);need(r['mon_hex']==normal['mon_hex'] and [n['snapshots'] for n in r['names']]==[n['snapshots'] for n in normal['names']],'native species caller stack poison independence');guards.append(r)
  for variant in ('omit_name_free','skip_name_destroy','wrong_name_bank','name_high_level_stub'):
   try:r=run_case(model,raw,language,qualified,data,variant=variant)
   except ValueError as e:
    d=Driver.latest;name=d.species_name_controller;need(d is not None and B.STACK_TOP==OUTER,'counter CPU initialized and observer scope restored');c=dict(variant=variant,completed=False,rejection=str(e),stage=d.stage,pc=hex(d.u.reg_read(UC_ARM_REG_PC)),constructor_entered=d.ctor_entry is not None,party_count=d.word(B.PARTIES+0x1000+4),names_completed=len(d.name_results),top_after_exception=hex(B.STACK_TOP),name_phase=name.outer_phase if name else None,name_internal=len(name.internal) if name else 0,name_reads=name.core.reads if name else 0,name_models=name.core.models if name else [],name_shadows=name.shadows if name else [],shadows=d.shadows)
   else:
    disguised=copy.deepcopy(r);disguised['variant']='current';disguised['names'][-1]['shadows']=[]
    try:require_case(disguised,data,qualified)
    except ValueError as e:c=dict(variant=variant,completed=True,rejection=str(e),result=r,tag_disguised=True)
    else:raise ValueError('native species counter accepted '+variant)
   require_counter(c,normal,data,qualified);counters.append(c)
  need(source_identities()==sources,'native species caller sources changed during campaign');summary=T.resource_summary(data['constructor'],[r['body'] for r in positive+guards]);W.require_host_budget()
 return dict(schema='trainer31-native-species-caller-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,resources=dict(preparation=data['preparation'],constructor=summary,message=data['message']['oracle'],names=data['names']['oracle']),positives=positive,guards=guards,observer_off=off,counters=counters,compiler_invoked=False,limits=['One initialized trainer31 caller/Plus0,1/two seeds/two stack fills/default0 name heap; six species only','Heap/NARC SDK six services, other constructor SDK and overlay filesystem remain models','No original native compiler reconstruction, natural encounter, allocator failure, battle renderer, raw-save or hardware proof','One CPU and actual caller frames throughout; no packet/context bridge; name heap separate from trainer-message and constructor arenas'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'native species caller inputs must exist');result=analyze(args.rom,args.language,args.objects,args.strategy_object);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024**2,'expanded species caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024**2,'stored species caller report budget');W.require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'finite native species/caller composition verified; SDK bodies and natural encounter remain separate')
if __name__=='__main__':main()
