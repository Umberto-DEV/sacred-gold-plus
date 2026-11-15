#!/usr/bin/env python3
"""Follow trainer31 caller preparation, native constructor and caller return.

Private exact ROMs and retained project objects only. SDK boundaries remain
explicit models. One CPU/context executes the complete initialized caller API.
"""
from pathlib import Path
import importlib.util,json,mmap,struct,sys,copy,gzip,gc
s=importlib.util.spec_from_file_location('caller_preparation_dependency',Path(__file__).with_name('attribuisci_preparazione.py'));Q=importlib.util.module_from_spec(s);s.loader.exec_module(Q)
N,T,P,B=Q.N,Q.N.T,Q.P,Q.B;need,sha=Q.need,Q.sha
s=importlib.util.spec_from_file_location('qualified_caller_adapter',Path(__file__).parents[1]/'test/caller_bench.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
from unicorn import Uc,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_CPU_ARM_CORTEX_A15,UC_ARM_REG_CPSR,UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_LR
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
OUTER=Q.TOP
INNER=OUTER-96
SUFFIX=(0x2073454,0x207346A,'19832b95df15aaa5b3f36e27c8ea99ac5ee179bbf9c8678819bf0ee84080aa54')

def qualify(model,raw,language,objects,strategy_object):
 body_code,body_data,module,body_proof=T.qualify(model,raw,language,objects,strategy_object,trainer=31);caller,caller_proof=Q.qualify(model,raw);view=P.G.S.SHARED.gifts_audit.Arm9View(raw);a,b,digest=SUFFIX;blob=view.read(a,b-a);need(sha(blob)==digest and blob==P.G.piece(model['segments'],a,b-a),'caller suffix exact readback');ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,a));need(sum(i.size for i in ins)==22 and len(ins)==10,'caller suffix decoded starts')
 for i in ins:need(i.address not in caller,'caller suffix code overlap');caller[i.address]=(i.size,True)
 caller_proof.append(dict(ram=hex(a),bytes=b-a,sha256=digest,rom_offset=hex(view.offset(a,b-a)),kind='native caller suffix'))
 return dict(body_code=body_code,body_data=body_data,module=module,caller_code=caller),dict(constructor=body_proof,caller=caller_proof)

class Driver:
 """Stage observers around the unchanged constructor bench SDK backends."""
 latest=None
 save_pointer=Q.SAVE
 def __init__(self,bench,qualified,data,plus,seed,*,poison=0xC7,observe=True,variant='current'):
  need(type(plus)is int and plus in (0,1) and seed in (0x12345678,0x12345679) and type(poison)is int and poison in (0xC7,0x39) and type(observe)is bool and variant in ('current','omit_or','leak_msg','wrong_restore_seed','omit_prefix_free','wrong_last_move','wrong_ctor_sp','phase_mutation') and (observe or variant=='current'),'full caller fixture domain');Driver.latest=self
  self.bench,self.qualified,self.data=bench,qualified,data;self.plus,self.seed,self.poison,self.observe,self.variant=plus,seed,poison,observe,variant;self.stage='boot';self.steps=0;self.max_stack=0;self.api_calls=[];self.services=[];self.outer_models=[];self.caller_calls=[];self.pending=[];self.caller_pcs=set();self.caller_writes=[];self.structure_writes=[];self.or_writes=[];self.transitions=[];self.msg_live=False;self.string_live=False;self.string_created=False;self.outer_frees=0;self.destroy_calls=0;self.ctor_entry=None;self.ctor_return=None;self.body=None;self.prefix=None;self.before=None;self.msg=struct.pack('<HHHHI',1,11,27,729,Q.OPAQUE_NARC);self.string=B.pack_species_string(data['preparation']['name']['words']);self.header=bytes.fromhex(data['preparation']['header_hex']);self.name=N.words_bytes(data['preparation']['name']['words']);self.audit=T.Actual(bench,31,plus=plus,seed=seed);self.audit.mon_allowed=qualified['body_code'];self.audit.mon_data=qualified['body_data'];self.audit.poison=False;self.audit.cookies=False;self.audit.game_variant=variant if variant in T.variants_for(31) else 'current';self.audit.full_variant=self.audit.game_variant
 def regs(self):return [self.u.reg_read(r) for r in B.R]+[self.u.reg_read(UC_ARM_REG_SP),self.u.reg_read(UC_ARM_REG_LR),self.u.reg_read(UC_ARM_REG_CPSR)]
 def read_bytes(self,a,n):return bytes(self.u.mem_read(a,n))
 def word(self,a):return struct.unpack('<I',self.read_bytes(a,4))[0]
 def factory(self,*args):
  self.u=u=Uc(*args);self.cpu_model=u.ctl_get_cpu_model();need(self.cpu_model==UC_CPU_ARM_CORTEX_A15,'qualified original constructor-bench CPU model');u.reg_write(UC_ARM_REG_CPSR,0x3F);self.audit.uc=u;original=u.emu_start
  def call(begin,end,*args,**kwargs):
   number=len(self.api_calls);need(number<3 and begin==(0x201FD39,0x20733C1,0x201FD2D)[number] and end==B.SENTINEL,'actual outer API sequence')
   if number==1:
    for i,v in enumerate(N.COOKIES,4):u.reg_write(B.R[i],v)
    self.stage='prefix';self.before=self.read_bytes(0x2000000,0x400000)
   elif number==2:self.stage='getter'
   entry=self.regs();original(begin,end,*args,**kwargs);self.api_calls.append(dict(begin=hex(begin),requested_end=hex(end),actual_end=hex(u.reg_read(UC_ARM_REG_PC)),entry=entry,end=self.regs()))
  u.emu_start=call;u.hook_add(UC_HOOK_CODE,self.step);u.hook_add(UC_HOOK_MEM_READ,self.read);u.hook_add(UC_HOOK_MEM_WRITE,self.write);return u
 def configure(self,cpu,implementations,events,state,handles):
  need(cpu is self.u,'single caller CPU');self.events,self.backend_state,self.backend_handle_cache=events,state,handles;result=dict(implementations);original_free=result['Heap_Free']
  def outer_free(u):
   if self.stage=='ctor':return original_free(u)
   need(self.stage=='prefix' and u.reg_read(B.R[0])==Q.STRING and self.string_live and self.word(Q.STRING+4)==0xB6F8D2ED,'outer native String invalidation before free');self.string_live=False;self.outer_frees+=1
  def new_msg(u):
   need(self.stage=='prefix' and self.regs()[:4]==[1,27,729,11] and not self.msg_live,'outer message allocation ABI');self.model_write(Q.MSG,self.msg,'MsgData with opaque lazy NARC');self.msg_live=True;u.reg_write(B.R[0],Q.MSG)
  def new_string(u):
   need(self.stage=='prefix' and self.regs()[:2]==[Q.MSG,31] and self.msg_live and not self.string_created,'outer raw packed name ABI');self.model_write(Q.STRING,self.string,'raw packed trainer31 String');self.string_created=self.string_live=True;u.reg_write(B.R[0],Q.STRING)
  def destroy_msg(u):
   need(self.stage=='suffix' and self.regs()[0]==Q.MSG and self.msg_live and not self.string_live,'outer message destruction ABI/lifetime');self.destroy_calls+=1
   if self.variant!='leak_msg':self.msg_live=False
  result.update(Heap_Free=outer_free,CallerNewMsgData=new_msg,CallerNewString=new_string,CallerDestroyMsgData=destroy_msg);return result
 def model_write(self,address,blob,reason):self.u.mem_write(address,blob);self.outer_models.append(dict(address=address,bytes=len(blob),sha256=sha(blob),reason=reason))
 def prepare(self,cpu):
  need(cpu is self.u and not self.api_calls,'caller fixtures must precede every API');setup=bytearray([0xA5])*0x200;struct.pack_into('<I',setup,0,1)
  for i in range(4):struct.pack_into('<I',setup,4+4*i,B.PARTIES+0x1000*i);struct.pack_into('<I',setup,0x18+4*i,31 if i==1 else 0)
  cpu.mem_write(B.SETUP,bytes(setup));cpu.mem_write(OUTER-608,bytes([self.poison])*608);cpu.mem_write(Q.TABLE,struct.pack('<I',0x100));cpu.mem_write(Q.MSG-16,bytes([0xD3])*0x140)
 def transition(self,stage):
  before_regs=self.regs();before_ram=sha(self.read_bytes(0x2000000,0x400000));self.stage=stage;B.STACK_TOP=INNER if stage=='ctor' else OUTER
  if self.variant=='phase_mutation' and stage=='ctor':self.u.reg_write(B.R[0],before_regs[0]^4)
  need(before_regs==self.regs() and before_ram==sha(self.read_bytes(0x2000000,0x400000)),'stage observer changed CPU/RAM');self.transitions.append(dict(stage=stage,regs=before_regs,ram_sha256=before_ram,neutral=True))
 def prefix_proof(self):
  tail=bytes([self.poison])*32;source=self.header+tail;expected=bytearray(source);expected[20:20+len(self.name)]=self.name;need(self.read_bytes(Q.LOCAL,52)==source and self.read_bytes(Q.TRAINER,52)==bytes(expected),'full caller preparation raw20/stack32/packed name');need(self.msg_live and self.string_created and not self.string_live and self.outer_frees==1 and self.read_bytes(Q.MSG,12)==self.msg and self.read_bytes(Q.STRING,len(self.string))==self.string[:4]+struct.pack('<I',0xB6F8D2ED)+self.string[8:],'full caller prefix message/String lifetime');need(not self.pending and len(self.caller_calls)==6 and len(self.structure_writes)==13,'full caller preparation helper/store coverage')
  return dict(trainer_hex=self.read_bytes(Q.TRAINER,52).hex(),local_source52=source.hex(),calls=copy.deepcopy(self.caller_calls),structure_writes=copy.deepcopy(self.structure_writes),services=copy.deepcopy(self.services),msg_live=self.msg_live,string_live=self.string_live,outer_frees=self.outer_frees)
 def collect_body(self):
  a=self.audit;need(not a.pending_native and a.pending_service is None and not a.extra_pending,'constructor helpers must close before caller suffix');need(not a.live and not a.handles,'constructor allocations must close before caller suffix');ram=self.read_bytes(0x2000000,0x400000);ignored=[(INNER-512,INNER),(B.REGISTRY,B.REGISTRY+64),(0x23DA044,0x23DA048),(P.MODULE,P.MODULE+2048),(B.PARTIES+0x1000,B.PARTIES+0x1000+0x5B0),(B.ARENA-8,a.next_arena),(0x21D15A8,0x21D15AC),(0x21D421C,0x21D421C+404),(0x23D8708,0x23D870C)];need(P.masked_hash(a.before,ignored)==P.masked_hash(ram,ignored),'constructor changed unrelated caller RAM');canaries=all(self.read_bytes(p-8,8)==b'\xA5'*8 and self.read_bytes(p+n,8)==b'\xA5'*8 for p,n in a.allocs+a.alloc_canaries)
  mons=[self.read_bytes(B.PARTIES+0x1000+8+236*i,236) for i in range(6)]
  return dict(mon_hex=[x.hex() for x in mons],decoded=[T.M.decode(x) for x in mons],end=self.ctor_return,seed_after=self.word(0x21D15A8),header=list(struct.unpack('<II',self.read_bytes(B.PARTIES+0x1000,8))),prefix_transition=a.prefix_transition,seam=a.seam,reader_calls=a.reader,unloads=a.unloads,prefix_models=a.models,models=a.mon_models,native_calls=a.native_calls,creation_inputs=a.creation_inputs,pid_overrides=a.pid_overrides,seed_calls=a.restores,additions=a.additions_all,capsule_calls=a.capsule_calls,post_form_calls=a.post_form_calls,extra_calls=a.extra_calls,buffer_writes=a.buffer_writes,buffer_reads=a.buffer_reads,buffer_before_free=a.buffer_before_free,globals=a.full_globals,instructions=a.instructions,max_stack=a.max_stack,live=a.live,handles=a.handles,canaries=canaries,plus_hits=self.word(0x23D8708),critical=a.critical,code=[dict(ram=hex(pc),bytes=n,thumb=t) for pc,n,t in sorted(a.mon_code)],events=copy.deepcopy(self.events[self.body_events_start:]),game_shadows=a.game_shadows+a.full_shadows,unrelated_ram_unchanged=True)
 def step(self,u,pc,n,_):
  self.steps+=1;sp=u.reg_read(UC_ARM_REG_SP);need(self.steps<=3000000 and OUTER-608<=sp<=OUTER and sp%4==0,'composed caller instruction/stack budget');self.max_stack=max(self.max_stack,OUTER-sp)
  # Full register snapshots are needed at API/stage boundaries, not at every
  # constructor instruction. Existing constructor observers own their snapshots.
  if self.stage=='ctor' and pc!=0x2073444:
   if self.observe:self.audit.step(u,pc,n,_)
   else:
    shape=self.qualified['body_code'].get(pc,self.audit.allowed.get(pc));thumb=bool(u.reg_read(UC_ARM_REG_CPSR)&32);sdk=pc in B.STUBS and n==2 and thumb;fs=pc in (B.FS_INFO,B.FS_IMAGE,B.FS_START,B.FS_UNLOAD);need(shape==(n,thumb) or sdk or fs,'OFF constructor outside qualified width/ISA or declared SDK boundary')
   return
  regs=self.regs()
  if self.stage in ('boot','getter'):
   starts=(0x201FD38,0x201FD3A,0x201FD3C) if self.stage=='boot' else (0x201FD2C,0x201FD2E,0x201FD30);need(pc in starts and n==2 and regs[15]&32,'outer native RNG API PC/ISA');return
  if self.stage=='prefix' and pc==B.ENTRY:
   if self.variant=='wrong_ctor_sp':u.reg_write(UC_ARM_REG_SP,INNER-8);regs=self.regs()
   need(regs[:3]==[B.SETUP,1,11] and regs[13]==INNER and regs[14]==0x2073445 and regs[4:12]==[B.SETUP+4,Q.NAME,Q.STRING,1]+list(N.COOKIES[4:]),'full caller actual nested constructor ABI');self.prefix=self.prefix_proof();self.ctor_entry=regs;self.body_events_start=len(self.events);self.transition('ctor')
  if self.stage=='ctor':
   if pc==0x2073444:
    need(regs[13]==self.ctor_entry[13] and regs[4:12]==self.ctor_entry[4:12],'constructor must preserve actual caller context');self.ctor_return=dict(regs=regs,pc=hex(pc));self.body=self.collect_body() if self.observe else None;self.transition('suffix')
   else:
    if self.observe:self.audit.step(u,pc,n,_)
    else:need(pc in self.qualified['body_code'] or pc in self.audit.allowed or pc in B.STUBS or pc in (B.FS_INFO,B.FS_IMAGE,B.FS_START,B.FS_UNLOAD),'OFF constructor outside qualified domain')
    return
  while self.pending and pc==int(self.pending[-1]['lr'],16)&~1:
   event=self.pending.pop();event.update(return_sp=sp,return_saved=regs[4:12],result_r0=regs[0]);need(event['sp']==sp and event['saved']==regs[4:12],'caller native helper return ABI')
  if pc in Q.SERVICES or pc==0x200BB44:
   names={**Q.SERVICES,0x200BB44:'DestroyMsgData'};self.services.append(dict(name=names[pc],pc=hex(pc),args=regs[:4],sp=sp,lr=hex(regs[14])));need(sp%8==0 and n==2 and regs[15]&32,'outer SDK model SP/Thumb boundary ABI')
   if pc==0x2007508:need(regs[:3]==[Q.LOCAL,55,31] and regs[14]==0x20733FD,'native header forward ABI')
   return
  need(self.qualified['caller_code'].get(pc)==(n,bool(regs[15]&32)),'caller prefix/suffix outside qualified code/ISA');self.caller_pcs.add(pc)
  if pc==0x207345E and self.variant=='omit_or':u.reg_write(UC_ARM_REG_PC,0x2073461);return
  if pc in (0x202A960,0x202A9A8,0x20735D8,0x2026A68,0x2026380,0x20E5AD8):
   if pc==0x2026A68:need(regs[:3]==[Q.STRING,Q.NAME,8],'actual native packed copy ABI')
   event=dict(pc=hex(pc),args=regs[:4],sp=sp,lr=hex(regs[14]),saved=regs[4:12]);self.caller_calls.append(event);self.pending.append(event)
 def read(self,u,access,address,n,value,_):
  if self.stage=='ctor':
   if self.observe:self.audit.read(u,access,address,n,value,_)
   return
  if self.stage in ('boot','getter'):
   need((0x21D15A8<=address and address+n<=0x21D15AC) or any(a<=address and address+n<=a+4 for a in (0x201FD34,0x201FD40)),'outer RNG API read');return
  inside=lambda a,size:a<=address and address+n<=a+size
  need(inside(OUTER-128,128) or inside(B.SETUP,0x200) or inside(Q.TABLE,4) or self.string_live and inside(Q.STRING,len(self.string)) or any(inside(a,size) for a,size,_ in Q.POOLS+N.POOLS),'caller read outside owned inputs/stack/pools')
 def write(self,u,access,address,n,value,_):
  pc=u.reg_read(UC_ARM_REG_PC)
  if self.stage=='ctor':
   if OUTER-4096<=address<OUTER:need(OUTER-608<=address and address+n<=INNER,'constructor stack writes must preserve caller frame')
   if self.observe:self.audit.write(u,access,address,n,value,_)
   return
  if self.stage in ('boot','getter'):need(self.stage=='boot' and (pc,address,n)==(0x201FD3A,0x21D15A8,4),'outer RNG API write');return
  inside=lambda a,size:a<=address and address+n<=a+size
  stack=inside(OUTER-128,128);structure=pc in (0x2073406,0x207340E) and inside(Q.TRAINER,52) and n==4;name=pc==0x20E5AEC and inside(Q.NAME,len(self.name)) and n==1;dead=(pc,address,n,value)==(0x2026398,Q.STRING+4,4,0xB6F8D2ED);or_store=(pc,address,n,value)==(0x207345E,B.SETUP,4,1);need(stack or structure or name or dead or or_store,'caller write outside owned fields/stack');event=dict(pc=hex(pc),address=address,bytes=n,value=value)
  if structure:self.structure_writes.append(event)
  if or_store:self.or_writes.append(event)
  if self.observe and not stack:self.caller_writes.append(event)

def run_case(model,raw,language,qualified,data,plus=1,seed=0x12345678,*,poison=0xC7,observe=True,variant='current'):
 need(sys.flags.optimize==0,'run without Python -O: inherited SDK model assertions are required');bench,_=T.bench_image(model,raw,language,qualified['module']);driver=Driver(bench,qualified,data,plus,seed,poison=poison,observe=observe,variant=variant);gc.collect();run,proof=A.adapt(B,driver);need(B.STACK_TOP==OUTER,'constructor observer scope must start restored')
 try:result=run(bench,31,driver=driver,plus=plus,seed=seed,max_instructions=3000000)
 finally:B.STACK_TOP=OUTER
 need(len(driver.api_calls)==3 and driver.ctor_entry is not None and driver.ctor_return is not None and driver.stage=='getter','complete caller and separate getter APIs');need(result['end']['sp']==OUTER and result['end']['r'][4:12]==list(N.COOKIES),'outer caller return saved registers');need(not driver.pending,'caller helper return closure');ram=result.pop('ram');need(driver.before is not None,'caller frozen baseline');ignored=[(OUTER-608,OUTER),(Q.TRAINER,Q.TRAINER+52),(Q.MSG,Q.MSG+12),(Q.STRING,Q.STRING+len(driver.string)),(B.SETUP,B.SETUP+4),(B.ARENA-8,driver.backend_state['arena']+8),(B.REGISTRY,B.REGISTRY+64),(0x23DA044,0x23DA048),(P.MODULE,P.MODULE+2048),(B.PARTIES+0x1000,B.PARTIES+0x1000+0x5B0),(0x21D15A8,0x21D15AC),(0x21D421C,0x21D421C+404),(0x23D8708,0x23D870C)];frozen=P.masked_hash(driver.before,ignored);need(frozen==P.masked_hash(ram,ignored),'full caller unrelated RAM changed')
 return dict(language=language,cpu_model=driver.cpu_model,plus=plus,seed=seed,poison=poison,observe=observe,variant=variant,adapter=proof,api_calls=driver.api_calls,ctor_entry=driver.ctor_entry,ctor_return=driver.ctor_return,prefix=driver.prefix,body=driver.body,caller_pcs=sorted(driver.caller_pcs),caller_calls=driver.caller_calls,caller_writes=driver.caller_writes,or_writes=driver.or_writes,services=driver.services,outer_models=driver.outer_models,msg_live=driver.msg_live,string_live=driver.string_live,outer_frees=driver.outer_frees,destroy_calls=driver.destroy_calls,transitions=driver.transitions,instructions=driver.steps,max_stack=driver.max_stack,end=result['end'],seed_after=result['seed_after'],mon_hex=[x.hex() for x in result['mons']],decoded=[T.M.decode(x) for x in result['mons']],header=list(result['party_header']),plus_hits=driver.word(0x23D8708),stack_canary=result['stack_canary'],functional_ram_sha256=P.masked_hash(ram,[(OUTER-608,OUTER),(B.ARENA-8,driver.backend_state['arena']+8)]),unrelated_ram_sha256=frozen,events=result['events'],overlay=result['overlay'])

def require_case(r,data,qualified):
 """Validate the composed caller contract; no synthetic direct-Ctor APIs."""
 need(r['variant']=='current' and r['observe'] is True and type(r['plus'])is int and r['plus'] in (0,1) and r['seed'] in (0x12345678,0x12345679) and type(r['cpu_model'])is int and r['cpu_model']==UC_CPU_ARM_CORTEX_A15,'full caller accepted fixture domain');expected_adapter=A.adapt(B,type('ProofOnly',(),dict(factory=None))())[1];need(r['adapter']==expected_adapter,'qualified caller adapter receipt');api=r['api_calls'];need(len(api)==3 and [x['begin'] for x in api]==['0x201fd39','0x20733c1','0x201fd2d'] and all(x['actual_end']==x['requested_end']==hex(B.SENTINEL) for x in api),'three actual outer API returns');need(api[0]['entry'][0]==api[0]['end'][0]==r['seed'] and api[0]['end'][13]==OUTER,'actual initial native seed setter');need(api[1]['entry'][:3]==[B.SETUP,Q.SAVE,11] and api[1]['entry'][4:12]==list(N.COOKIES) and api[1]['entry'][13]==OUTER and api[1]['entry'][14]==B.SENTINEL|1,'actual outer caller entry fixture');need(api[1]['end'][:13]==r['end']['r'] and api[1]['end'][13]==r['end']['sp']==OUTER and r['end']['r'][4:12]==list(N.COOKIES) and api[2]['end'][0]==r['seed_after']==r['seed'],'caller return precedes separate native seed getter')
 entry,returned=r['ctor_entry'],r['ctor_return'];need(entry[:3]==[B.SETUP,1,11] and entry[13]==INNER and entry[14]==0x2073445 and entry[4:12]==[B.SETUP+4,Q.NAME,Q.STRING,1]+list(N.COOKIES[4:]) and returned['pc']=='0x2073444' and returned['regs'][13]==INNER and returned['regs'][4:12]==entry[4:12],'actual nested constructor entry/return ABI');need([x['stage'] for x in r['transitions']]==['ctor','suffix'] and all(x['neutral'] for x in r['transitions']) and r['transitions'][0]['regs']==entry and r['transitions'][1]['regs']==returned['regs'],'observer phase continuity');need(not r['msg_live'] and not r['string_live'] and r['outer_frees']==r['destroy_calls']==1,'complete outer resource lifetime');need(r['or_writes']==[dict(pc='0x207345e',address=B.SETUP,bytes=4,value=1)],'actual native final OR store even when value is unchanged');need(set(r['caller_pcs'])==set(qualified['caller_code']) and len(r['caller_pcs'])==138 and 0<r['instructions']<=3000000 and 112<=r['max_stack']<=608 and r['stack_canary'],'composed caller coverage/stack budget')
 prep=data['preparation'];prefix=r['prefix'];raw_header=bytes.fromhex(prep['header_hex']);payload=N.words_bytes(prep['name']['words']);source=raw_header+bytes([r['poison']])*32;expected=bytearray(source);expected[20:20+len(payload)]=payload;need(prefix['trainer_hex']==expected.hex() and prefix['local_source52']==source.hex() and prefix['msg_live'] and not prefix['string_live'] and prefix['outer_frees']==1,'native upstream raw20/stack32/name provenance');copy_stores=[dict(pc='0x2073406' if i<12 else '0x207340e',address=Q.TRAINER+4*i,bytes=4,value=v) for i,v in enumerate(struct.unpack('<13I',source))];need(prefix['structure_writes']==copy_stores,'complete native upstream 52B stores')
 calls=prefix['calls'];need(len(calls)==6 and [c['pc'] for c in calls]==['0x202a960','0x202a9a8','0x20735d8','0x2026a68','0x20e5ad8','0x2026380'],'upstream helper sequence');need(all(c['sp']==c['return_sp'] and c['saved']==c['return_saved'] for c in calls),'upstream helper return ABI');need(calls[0]['args'][0]==Q.SAVE and calls[0]['result_r0']==Q.MISC and calls[1]['args'][0]==Q.MISC and calls[1]['result_r0']==Q.MISC+0x270 and calls[2]['args'][:2]==[31,Q.LOCAL] and calls[3]['args'][:3]==[Q.STRING,Q.NAME,8] and calls[4]['args'][:3]==[Q.NAME,Q.STRING+8,len(payload)] and calls[5]['args'][0]==Q.STRING,'upstream source/raw ABI');need([e['name'] for e in r['services']]==['NewMsgDataFromNarc','ReadWholeNarcMemberByIdPair','NewString_ReadMsgData','Heap_Free','DestroyMsgData'] and r['services'][-1]['args'][0]==Q.MSG and r['services'][-1]['lr']=='0x2073467','outer modeled services and destroy call');need(r['events'][0]==['read',55,31,Q.LOCAL,20] or tuple(r['events'][0])==('read',55,31,Q.LOCAL,20),'existing raw reader backend exact header extent')
 body=r['body'];need(body is not None and body['end']==returned and body['header']==r['header']==[6,6] and body['mon_hex']==r['mon_hex'] and len(r['mon_hex'])==len(r['decoded'])==6,'one native complete party through caller return');want=T.expected(data['constructor'],r['plus']);need(body['seed_after']==r['seed'] and body['plus_hits']==r['plus_hits']==6 and not body['live'] and not body['handles'] and body['canaries'] and body['unrelated_ram_unchanged'] and body['max_stack']<=512,'constructor lifetime/seed/canary/stack bounds');need(body['reader_calls']==body['unloads']==1 and body['prefix_transition']['buffer_hex']==data['constructor']['record']['before'] and body['prefix_transition']['seed']==r['seed'] and body['prefix_transition']['observer_neutral'],'native constructor raw prefix and neutral transition');party=bytes.fromhex(data['constructor']['record']['after']) if r['plus'] else data['constructor']['party'];need(body['buffer_before_free']==party.hex() and body['buffer_writes']==([dict(pc='0x23d619a',offset=i,bytes=1,value=v) for i,v in enumerate(party)] if r['plus'] else []),'actual one-time strategy buffer commit')
 for packet,reported,record in zip(r['mon_hex'],r['decoded'],want):
  raw=bytes.fromhex(packet);need(len(raw)==236,'complete native packet width');decoded=T.M.decode(raw);need(decoded==reported and decoded['checksum_ok'],'independent native packet decode/checksum');decoded['capsule_hex']=B._decrypt(raw[136:],struct.unpack_from('<I',raw)[0])[76:100].hex();need(all(decoded[k]==v for k,v in record['fields'].items()),'source-derived full native Pokemon fields')
 need(len(body['creation_inputs'])==len(body['pid_overrides'])==len(body['additions'])==6 and len(body['seed_calls'])==7 and len(body['post_form_calls'])==24,'six native constructions/copies and helper groups')
 for record,create,pid,addition in zip(want,body['creation_inputs'],body['pid_overrides'],body['additions']):
  fields=record['fields'];slot=record['slot'];need(create['args']==[B.ARENA+128,fields['species'],fields['level'],record['iv']] and create['stack']==[1,fields['pid'],2,0] and create['sp']==INNER-152 and create['lr']=='0x2073a17','actual nested-frame CreateMon arguments');need(pid['after_gender']==record['pid_gender'] and pid['args'][3]==INNER-152+0x7C,'actual native persistent PID state');need(addition==dict(count=slot+1,sp=INNER-152,mon_hex=r['mon_hex'][slot],party_slot_sha256=sha(bytes.fromhex(r['mon_hex'][slot]))),'native six actual PartyAdd copies')
 for event,value in zip(body['seed_calls'],[x['class_seed'] for x in want]+[r['seed']]):need(event['args'][0]==event['result'][0]==event['after_seed']==value,'source-derived actual reseed and restoration')
 need([e['lr'] for e in body['seed_calls']]==['0x20739c3']*6+['0x2073a95'],'actual constructor reseed callers')
 for event in body['native_calls']+body['post_form_calls']+body['capsule_calls']+body['pid_overrides']+body['seed_calls']+body['extra_calls']:need(event['sp']==event['return_sp'] and event['saved']==event['return_saved'] and event['return_pc']==int(event['lr'],16)&~1,'all nested native helper return ABI')
 native=iter(body['native_calls']);consumed=0
 def next_call():
  nonlocal consumed
  try:event=next(native)
  except StopIteration:raise ValueError('incomplete native constructor call sequence')
  consumed+=1;return event
 for record in want:
  state=record['class_seed'];fields=record['fields'];slot=record['slot']
  for after in record['class_draws']:
   event=next_call();need(event['entry']=='0x201fd44' and event['lr']=='0x20739d3' and event['before_seed']==state and event['after_seed']==after and event['result'][0]==after>>16,'actual complete class RNG draws');state=after
  event=next_call();need(event['entry']=='0x206de38' and event['args']==[B.ARENA+128,fields['species'],fields['level'],record['iv']] and event['lr']=='0x2073a17','actual native CreateMon caller')
  for i,after in enumerate(record['ot_draws']):
   event=next_call();need(event['entry']=='0x201fd44' and event['lr']==('0x206df13' if i%2==0 else '0x206df19') and event['before_seed']==state and event['after_seed']==after and event['result'][0]==after>>16,'actual native anti-shiny OTID draws');state=after
  event=next_call();need(event['entry']=='0x206ec40' and event['args'][:3]==[B.ARENA+128,6,B.ARENA+18*slot+6] and event['lr']=='0x2073a23','native held item source pointer')
  for move_slot,move in enumerate(fields['moves']):
   event=next_call();need(event['entry']=='0x20714e8' and event['args'][:3]==[B.ARENA+128,move,move_slot] and event['lr']=='0x2073a37','all actual native move setters')
  for entry,lr in (('0x2072a44','0x2073a4f'),('0x206ec40','0x2073a59'),('0x2073ae4','0x2073a5f'),('0x2074524','0x2073a69')):
   event=next_call();need(event['entry']==entry and event['lr']==lr,'native capsule/form/postform/PartyAdd sequence')
   if entry=='0x2072a44':need(event['args'][:3]==[record['capsule'],B.ARENA+128,11] and event['result'][0]==int(record['capsule']!=0),'native capsule ID/BOOL')
   if entry=='0x2074524':need(event['args'][:2]==[B.PARTIES+0x1000,B.ARENA+128] and event['result'][0]==1,'actual native PartyAdd BOOL')
 need(consumed==len(body['native_calls']),'no extra native constructor calls');need(len(body['capsule_calls'])==2 and [x['lr'] for x in body['capsule_calls']]==['0x2072a81','0x2072a8b'] and body['capsule_calls'][0]['value_hex']=='01000000' and body['capsule_calls'][1]['value_hex']==want[-1]['fields']['capsule_hex'],'actual capsule14 setters and raw slice');need(not body['game_shadows'],'accepted installed constructor must have no game counter shadows');require_evidence(r,data,qualified,want,source,copy_stores,payload);return True

def require_evidence(r,all_data,qualified,want,source,copy_stores,name_payload):
 """Bind every retained helper/resource ledger to raw inputs and native calls."""
 body,data=r['body'],all_data['constructor'];prefix=r['prefix'];extra=body['extra_calls'];position=0
 need(len(extra)==(37 if r['plus'] else 31),'complete constructor extra observer count')
 def next_extra(entry):
  nonlocal position
  need(position<len(extra),'missing extra helper');event=extra[position];position+=1;need(event['entry']==entry,'extra native helper order');return event
 event=next_extra('0x20735f8');need(event['args'][0]==72 and event['result'][0]==0 and event['return_pc']==0x2073650,'native class-table consumer')
 for record in want:
  slot=record['slot'];event=next_extra('0x20f2998');need(event['args'][:2]==[data['party'][18*slot]*31,255] and event['result'][:2]==list(divmod(data['party'][18*slot]*31,255)) and event['return_pc']==0x20739F6,'native source difficulty/IV division')
  event=next_extra('0x23d602c');need(event['args']==[B.ARENA,31,0x603,r['plus']] and event['stack0']==0x23D6600 and event['result'][0]==int(r['plus']==1 and slot==0) and event['return_pc']==0x23D621C and event['slot']==slot,'native strategy/config/once-only core')
  event=next_extra('0x23d61c4');need(event['args'][:3]==[B.SETUP,52,B.ARENA] and event['return_pc']==0x23D6234 and event['slot']==slot,'native strategy wrapper caller')
  if r['plus']:
   event=next_extra('0x23d8100');need(event['args'][:3]==[B.ARENA,18,6] and event['result'][0]==29 and event['return_pc']==0x23D816A,'native six-opponent maximum')
  event=next_extra('0x23d8134');need(event['args'][:3]==[record['base'],B.ARENA,0x603] and event['result'][0]==record['fields']['level'] and event['return_pc']==0x23D81AC,'inherited native level/table semantics')
  event=next_extra('0x23d6228');need(event['result']==[B.ARENA+128,record['fields']['species'],record['fields']['level'],record['iv']<<24] and event['return_pc']==0x2073A10 and event['nzcv']==0,'strategy hook actual live ABI/flags')
 need(position==len(extra),'no extra unbound native helpers')
 for slot,record in enumerate(want):
  for event,entry,lr in zip(body['post_form_calls'][4*slot:4*slot+4],('0x20722d4','0x206e250','0x2071754','0x206ec40'),('0x2073aed','0x2073af3','0x2073afb','0x2073b11')):need(event['entry']==entry and event['lr']==lr and event['args'][0]==B.ARENA+128,'complete owned post-form native chain')
  has=body['post_form_calls'][4*slot+2];setter=body['post_form_calls'][4*slot+3];need(has['args'][1]==218 and has['result'][0]==int(218 in record['fields']['moves']) and setter['args'][1]==9 and setter['value_byte']==record['fields']['friendship'],'native move218/friendship source semantics');pid=body['pid_overrides'][slot];before_seed=r['seed'] if slot==0 else want[slot-1]['ot_draws'][-1];need(pid['args']==[record['fields']['species'],0,0,INNER-152+0x7C] and pid['sp']==INNER-152 and pid['lr']=='0x20739ab' and pid['before_gender']==pid['after_gender']==0x88 and pid['before_seed']==pid['after_seed']==before_seed,'native PID source/previous state binding')
 need([event['args'][1] for event in body['capsule_calls']]==[162,171] and all(event['args'][0]==B.ARENA+128 for event in body['capsule_calls']),'native capsule setters attribute IDs');move_reads=[e for e in body['buffer_reads'] if e['pc']=='0x2073a2c'];need(move_reads==[dict(pc='0x2073a2c',offset=18*i+8+2*j,bytes=2,value=record['fields']['moves'][j]) for i,record in enumerate(want) for j in range(4)],'all24 native edited-buffer move loads')
 code=body['code'];need(type(code)is list and len(code)>0 and len({e['ram'] for e in code})==len(code) and all(qualified['body_code'].get(int(e['ram'],16))==(e['bytes'],e['thumb']) for e in code),'constructor observed code must bind qualified instruction starts/width/ISA');pcs={int(e['ram'],16) for e in code};need({0x207363E,0x2073A0C,0x206DE38,0x2073A32,0x2074524,0x2073A90,0x2073A96,0x23D602C}<=pcs,'constructor required body/strategy/return starts')
 prefix_models=body['prefix_models'];need([e['name'] for e in prefix_models]==['Heap_Alloc','Heap_Alloc']+['0x20d88c0']*4+['0x20d8a48','0x20d8b6c','ReadWholeNarcMemberByIdPair','0x20d88c0','0x20d8db4'] and prefix_models[0]['args'][:2]==[11,108] and prefix_models[1]['args'][:2]==[11,236] and prefix_models[8]['args'][:3]==[B.ARENA,56,31],'native prefix allocations/raw-reader/FS service order');need(body['critical']==[dict(pc=hex(pc),address=hex(address),bytes=4,value=value) for pc,address,value in ((0x200702E,B.REGISTRY+4,1),(0x2007030,B.REGISTRY,126),(0x23DA3E2,0x23DA044,1),(0x2006F78,B.REGISTRY+4,0))] and [list(x) for x in r['overlay']['registry']]==[[126,0]]+[[0,0]]*7,'native overlay registry load/unload lifetime')
 live={B.ARENA:108,B.ARENA+128:236};handles={};events=[['alloc',11,108,B.ARENA],['alloc',11,236,B.ARENA+128],['read',56,31,B.ARENA,108]];next_pointer=B.ARENA+384
 for event in body['models']:
  kind,args=event['name'],event['args'];need(event['sp']==event['return_sp'] and event['saved']==event['return_saved'] and 'result'in event,'SDK modeled return ABI')
  if kind in ('Heap_Alloc','Heap_AllocAtEnd','GetSpeciesName'):
   pointer=event['result'];need(pointer==event['pointer']==next_pointer and pointer not in live and pointer not in handles,'unique sequential SDK allocation');image=B.pack_species_string(data['names'][str(args[0])]) if kind=='GetSpeciesName' else bytes(args[1]);need(event['bytes']==len(image) and event['output_pointer']==pointer and event['output_sha256']==sha(image),'modeled allocation image from raw species/name input');next_pointer+=(len(image)+23)&~7;live[pointer]=len(image);events.append(['name',args[0],args[1],pointer] if kind=='GetSpeciesName' else ['alloc',args[0],args[1],pointer])
  elif kind=='Heap_Free':need(args[0] in live and live.pop(args[0])==event['bytes'],'single exact live SDK free');events.append(['free',args[0]])
  elif kind=='ReadWholeNarcMemberByIdPair':
   need(args[1] in data['archives'],'raw SDK archive domain');payload=data['archives'][args[1]][args[2]];need(event['bytes']==len(payload) and event['sha256']==event['output_sha256']==sha(payload) and event['output_pointer']==args[0],'independent raw SDK readback');need(any(p<=args[0] and args[0]+len(payload)<=p+size for p,size in live.items()) or args[0]==0x21D421C and args[1]==3 and len(payload)==404 or args[1]==11 and len(payload)==16 and args[0]==event['sp'] and event['return_pc']==0x2073320 and INNER-512<=args[0] and args[0]+16<=INNER,'raw SDK read live destination');events.append(['read',args[1],args[2],args[0],len(payload)])
  elif kind=='NARC_New':
   pointer=event['result'];need(args[:2]==[185,11] and pointer==event['pointer']==next_pointer and pointer not in live and not handles,'capsule SDK opaque handle lifetime');next_pointer+=32;handles[pointer]=185;events.append(['narc_new',185,11,pointer])
  elif kind=='NARC_ReadFromMember':
   need(handles.get(args[0])==185 and args[1:]==[0,312,24] and event['destination']==event['output_pointer']==event['sp']+8 and event['output_sha256']==sha(data['archives'][185][0][312:336]),'raw capsule14 slice/handle/destination');events.append(['narc_read',185,0,312,24,event['destination']])
  elif kind=='NARC_Delete':need(args[0] in handles,'single live NARC delete');handles.pop(args[0]);events.append(['narc_delete',args[0]])
  else:raise ValueError('unknown constructor SDK model event')
 need(not live and not handles,'reconstructed complete constructor SDK lifetime');need([list(e) for e in body['events']]==events and [list(e) for e in r['events']]==[['read',55,31,Q.LOCAL,20]]+events,'original SDK backend events match reconstructed ledger')
 string=B.pack_species_string(all_data['preparation']['name']['words']);msg=struct.pack('<HHHHI',1,11,27,729,Q.OPAQUE_NARC);need(r['outer_models']==[dict(address=Q.MSG,bytes=12,sha256=sha(msg),reason='MsgData with opaque lazy NARC'),dict(address=Q.STRING,bytes=len(string),sha256=sha(string),reason='raw packed trainer31 String')],'outer exact model image writes');expected_writes=copy_stores+[dict(pc='0x20e5aec',address=Q.NAME+i,bytes=1,value=v if v<128 else v|0xFFFFFF00) for i,v in enumerate(name_payload)]+[dict(pc='0x2026398',address=Q.STRING+4,bytes=4,value=0xB6F8D2ED),dict(pc='0x207345e',address=B.SETUP,bytes=4,value=1)];need(r['caller_writes']==expected_writes,'native caller structure/name/deletion/OR writes');need(prefix['services']==r['services'][:4],'prefix service evidence retained through suffix')
 specs=((0x200BAF8,[1,27,729,11],INNER,0x20733D7),(0x2007508,[Q.LOCAL,55,31],INNER,0x20733FD),(0x200BBA0,[Q.MSG,31],INNER,0x207342B),(0x201AB0C,[Q.STRING],INNER-8,0x20263A1),(0x200BB44,[Q.MSG],INNER,0x2073467))
 for event,(pc,args,sp,lr) in zip(r['services'],specs):need(event['pc']==hex(pc) and event['args'][:len(args)]==args and event['sp']==sp and event['lr']==hex(lr),'outer modeled service source ABI')

def require_off_pair(observed,off):
 need(observed['observe'] is True and off['observe'] is False and off['body'] is None and off['variant']==observed['variant']=='current','paired full caller OFF domain')
 fields=('language','cpu_model','plus','seed','poison','api_calls','ctor_entry','ctor_return','prefix','caller_pcs','caller_calls','or_writes','services','outer_models','msg_live','string_live','outer_frees','destroy_calls','instructions','max_stack','end','seed_after','mon_hex','decoded','header','plus_hits','stack_canary','functional_ram_sha256','unrelated_ram_sha256','events','overlay')
 need(all(json.dumps(observed[k],sort_keys=True)==json.dumps(off[k],sort_keys=True) for k in fields),'full caller OFF/ON functional state or backend event difference')
 need([x['stage'] for x in observed['transitions']]==[x['stage'] for x in off['transitions']]==['ctor','suffix'] and all(a['regs']==b['regs'] and a['neutral'] and b['neutral'] for a,b in zip(observed['transitions'],off['transitions'])),'OFF/ON neutral phase context')
 return dict(neutral=True,scope='complete caller API registers,prepared Trainer,6whole packets,RNG,global RAM and actual SDK events; declared constructor temporary heap/stack scratch excluded',functional_ram_sha256=observed['functional_ram_sha256'],party_sha256=sha(b''.join(bytes.fromhex(x) for x in observed['mon_hex'])),seed_after=observed['seed_after'],events_sha256=sha(json.dumps(observed['events'],sort_keys=True).encode()))

def source_identities():
 files=(__file__,A.__file__,Q.__file__,N.__file__,T.__file__,T.S.__file__,T.F.__file__,T.M.__file__,T.C.__file__,B.__file__)
 return {str(Path(p).resolve().relative_to(P.SOURCE)):sha(Path(p).read_bytes()) for p in files}

def partial_counter(error,variant):
 driver=Driver.latest;need(B.STACK_TOP==OUTER,'observer stack scope must restore after counter exception');need(driver is not None and hasattr(driver,'u'),'counter must reach initialized sandbox CPU');cap,count=struct.unpack('<II',driver.read_bytes(B.PARTIES+0x1000,8));need(0<=count<=6,'partial counter party bound');packets=[driver.read_bytes(B.PARTIES+0x1000+8+236*i,236) for i in range(count)]
 return dict(variant=variant,rejection=str(error),completed=False,stage=driver.stage,pc=hex(driver.u.reg_read(UC_ARM_REG_PC)),sp=driver.u.reg_read(UC_ARM_REG_SP),constructor_entered=driver.ctor_entry is not None,constructor_native_started=driver.audit.started,party_count=count,party_sha256=sha(b''.join(packets)),seed=driver.word(0x21D15A8),constructor_live={hex(p):n for p,n in driver.audit.live.items()},msg_live=driver.msg_live,string_live=driver.string_live,top_after_exception=hex(B.STACK_TOP))

def analyze(rom,language,objects,strategy_object):
 need(sys.flags.optimize==0,'run without Python -O');sources=source_identities();model=P.G.S.SHARED.read_current(rom,language)
 with rom.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:
  qualified,proof=qualify(model,raw,language,objects,strategy_object);data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31));positives=[];guards=[];off_cases=[];counters=[]
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    case=run_case(model,raw,language,qualified,data,plus,seed);require_case(case,data,qualified);positives.append(case);print(language,'caller',plus,hex(seed),'verified',flush=True)
   need(positives[-1]['mon_hex']==positives[-2]['mon_hex'] and positives[-1]['seed_after']!=positives[-2]['seed_after'],'caller preserves source reseed determinism and independent original seed')
   off=run_case(model,raw,language,qualified,data,plus,observe=False);neutral=require_off_pair(positives[-2],off);off_cases.append(dict(result=off,proof=neutral))
  normal=next(r for r in positives if r['plus']==1 and r['seed']==0x12345678);guard=run_case(model,raw,language,qualified,data,poison=0x39);require_case(guard,data,qualified);need(guard['mon_hex']==normal['mon_hex'] and guard['seed_after']==normal['seed_after'],'caller stack poison cannot alter any complete Pokemon packet');guards.append(guard)
  for variant in ('omit_or','leak_msg','wrong_restore_seed','omit_prefix_free','wrong_last_move','wrong_ctor_sp','phase_mutation'):
   try:case=run_case(model,raw,language,qualified,data,variant=variant)
   except ValueError as error:
    need(variant in ('omit_prefix_free','wrong_ctor_sp','phase_mutation'),'unexpected early counter failure');counter=partial_counter(error,variant)
    if variant=='omit_prefix_free':need(counter['party_count']==6 and counter['party_sha256']==sha(b''.join(bytes.fromhex(x) for x in normal['mon_hex'])) and counter['constructor_live']=={hex(B.ARENA):108} and counter['seed']==normal['seed_after'],'partial exact108B leak with same complete party')
    else:need(not counter['constructor_native_started'] and counter['party_count']==0,'entry/phase counter must reject before constructor execution')
    counters.append(counter);continue
   need(variant in ('omit_or','leak_msg','wrong_restore_seed','wrong_last_move'),'counter unexpectedly completed without runtime rejection')
   if variant in ('omit_or','leak_msg','wrong_restore_seed'):need(case['mon_hex']==normal['mon_hex'],'same-whole-party counter premise')
   if variant=='omit_or':need(case['or_writes']==[] and case['functional_ram_sha256']==normal['functional_ram_sha256'],'skipped OR must retain same final value/RAM yet lack native store')
   if variant=='leak_msg':need(case['msg_live'] and case['destroy_calls']==1 and case['functional_ram_sha256']==normal['functional_ram_sha256'],'same-data message leak after actual destructor boundary call')
   if variant=='wrong_last_move':need([i for i,(a,b) in enumerate(zip(case['mon_hex'],normal['mon_hex'])) if a!=b]==[5] and case['body']['buffer_before_free']==normal['body']['buffer_before_free'],'wrong-callee counter preserves five packets and actual edited buffer')
   disguised=copy.deepcopy(case);disguised['variant']='current';disguised['body']['game_shadows']=[]
   try:require_case(disguised,data,qualified)
   except ValueError as error:rejection=str(error)
   else:raise ValueError('full caller counter accepted: '+variant)
   counters.append(dict(variant=variant,completed=True,rejection=rejection,disguise='counter label and declared shadow metadata removed only; actual bytes/events unchanged',result=case))
  summary=T.resource_summary(data['constructor'],[r['body'] for r in positives+guards]);need(source_identities()==sources,'source drift during full caller campaign')
 from importlib.metadata import version
 return dict(schema='trainer31-complete-caller-v1',coverage='finite-full-caller-campaign',language=language,input=model['record'],source_sha256=sources,proof=proof,resources=dict(preparation=data['preparation'],constructor=summary),positives=positives,guards=guards,observer_off=off_cases,counters=counters,native_compiler_invoked=False,environment=dict(python=sys.version,unicorn=version('unicorn'),capstone_distribution=version('capstone'),ndspy=version('ndspy'),cpu_model=17,cpu_name='original constructor-bench default Cortex-A15',instruction_contract='fixed ARM/Thumb windows; explicit ARM946 1KiB split-BL hook model not qualified for full constructor'),conclusions=dict(same_cpu_context_for_entire_caller=True,native_preparation_constructor_suffix_return=True,all_six_native_pokemon=True,original_seed_restored=True,outer_message_lifetime_closed=True,natural_encounter_observed=False),limits=['Initialized caller API IDs[0,31,0,0],battleType1,heap11,Plus0/1,cap100,2seeds and2stackpoisons only','Message allocation/loading/destruction,raw archive reads,heap/NARC/overlay FS use declared host boundaries; their native bodies do not execute','Sparse SaveData array9 table is a readonly synthetic fixture; no save file/Continue/SAVE/hardware validation','The composed guest stack bound608 includes native caller96 plus qualified constructor512; excludes real allocator/FS bodies and hardware WCET','Inherited species-name model remains the qualified decoded species String boundary; trainer names are raw packed729 words','Original native MW and old Plus compiler/object reconstruction remain unavailable; source correspondence and retained project ELF readback have separate proofs','No natural upstream encounter,othertrainerID/rival/multi-ID/doubleBattle/failure path,whole battle or UI rendering qualification'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'caller inputs must exist');result=analyze(args.rom,args.language,args.objects,args.strategy_object);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024*1024,'expanded caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024*1024,'stored caller report budget');args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as file:file.write(blob)
 except ValueError as error:parser.exit(2,str(error)+'\n')
 print(args.language,'complete native caller31,6Pokemon,lifetime/seed/ABI and OFF/ON verified; natural encounter remains outside coverage')

if __name__=='__main__':main()
