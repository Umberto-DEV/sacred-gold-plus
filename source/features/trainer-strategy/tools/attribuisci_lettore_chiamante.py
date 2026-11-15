#!/usr/bin/env python3
"""Compose the native header NARC parser with the complete trainer31 caller.

The header selects its own raw member through five FS models. Constructor
member reads retain their original model backend under a separate owner.
"""
from pathlib import Path
import importlib.util,types,copy,json,mmap,gzip,gc,sys,struct,collections

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
X=load('header_species_caller_parent',Path(__file__).with_name('attribuisci_nomi_chiamante.py'))
R=load('header_narc_reader_parent',Path(__file__).with_name('attribuisci_lettore_narc.py'))
A=load('header_caller_adapter',Path(__file__).parents[1]/'test/caller_narc_bench.py')
V,U,B,T,P,Q,N,need,sha=X.V,X.U,X.B,X.T,X.P,X.Q,X.N,X.need,X.sha
OUTER,INNER=X.OUTER,X.INNER
HEADER_RETURN=0x20733FC
HEADER_COOKIES=[B.SETUP+4,Q.NAME,N.COOKIES[2],1]+list(N.COOKIES[4:])
A.bind(X,R)
from unicorn.arm_const import UC_ARM_REG_PC

def qualify(model,raw,language,objects,strategy_object):
 qualified,proof=X.qualify(model,raw,language,objects,strategy_object);code,locations=R.qualify(model,raw);qualified['header_code']=code;proof['native_header']=locations
 for pc,shape in code.items():
  for old in ('body_code','caller_code','message_code'):
   need(pc not in qualified[old] or qualified[old][pc]==shape,'header shared instruction shape drift')
 return qualified,proof

def canaries_equal_before(reader):
 for address in (Q.LOCAL-16,Q.LOCAL+20):
  offset=address-0x2000000
  if reader.read_bytes(address,16)!=reader.before[offset:offset+16]:return False
 return True

def bind_reader(driver):
 namespace=dict(vars(R));bound=type('HeaderReader',(R.Reader,),{});namespace.update(TOP=INNER,DEST=Q.LOCAL,STOP=HEADER_RETURN,Reader=bound)
 for name,method in vars(R.Reader).items():
  if isinstance(method,types.FunctionType):
   fn=types.FunctionType(method.__code__,namespace,method.__name__,method.__defaults__,method.__closure__);fn.__kwdefaults__=method.__kwdefaults__;setattr(bound,name,fn)
 need({k for k in namespace if namespace[k]is not vars(R).get(k)}=={'TOP','DEST','STOP','Reader'},'header reader observer binding outside exact namespace')
 reader=bound(dict(segments=driver.bench.segments),driver.qualified['header_code'],{'55':driver.data['header']['55']},55,fill=driver.poison,observe=driver.observe,clobber=driver.header_clobber,variant={'header_skip_close':'skip_close','header_short_read':'short_payload'}.get(driver.header_variant,'current'));reader.u=driver.u;reader.before=driver.read_bytes(0x2000000,0x400000);reader.entry=reader.regs();reader.caller_frame_before=driver.read_bytes(INNER,96).hex();return reader

class Driver(X.Driver):
 latest=None
 def __init__(self,*args,header_clobber=False,**kwargs):
  variant=kwargs.pop('variant','current');need(variant in ('current','header_skip_close','header_short_read') and type(header_clobber)is bool,'finite native header caller variant/control');super().__init__(*args,variant='current',**kwargs);Driver.latest=self;self.header_variant=variant;self.header_clobber=header_clobber;self.header_reader=None;self.header_active=False;self.header_result=None;self.header_binding=None;self.header_code_live=False;self.ctor_read_dispatch=[];self.original_ctor_read=None;self.ctor_start_steps=None
 def transition(self,stage):
  super().transition(stage)
  if stage=='ctor':self.ctor_start_steps=self.steps
 def configure(self,cpu,implementations,events,state,handles):
  self.original_ctor_read=implementations['ReadWholeNarcMemberByIdPair'];return super().configure(cpu,implementations,events,state,handles)
 def prepare(self,cpu):
  super().prepare(cpu)
  for pc,(size,thumb) in self.qualified['header_code'].items():need(self.read_bytes(pc,size)==P.G.piece(self.bench.segments,pc,size),'native header code overwritten before caller entry')
  self.header_code_live=True
 def start_header(self):
  regs=self.regs();need(self.stage=='prefix' and self.header_reader is None and not self.message_active and regs[:4]==[Q.LOCAL,55,31,0x2007509] and regs[4:12]==HEADER_COOKIES and regs[12]==0 and regs[13]==INNER and regs[14]==HEADER_RETURN|1 and regs[15]==0x3F,'actual native header caller activation/ABI');digest=sha(self.read_bytes(0x2000000,0x400000));self.header_reader=bind_reader(self);need(self.header_reader.u is self.u and self.regs()==regs and sha(self.read_bytes(0x2000000,0x400000))==digest,'header binding changed CPU/RAM');self.header_binding=dict(regs=regs,ram_sha256=digest,neutral=True);self.header_active=True
 def finish_header(self):
  reader=self.header_reader;self.header_result=header_snapshot(reader);self.header_result.update(same_cpu=reader.u is self.u,caller_frame_before=reader.caller_frame_before,caller_frame_after=self.read_bytes(INNER,96).hex(),destination_before=reader.before[Q.LOCAL-0x2000000:Q.LOCAL-0x2000000+20].hex());self.header_active=False
 def step(self,u,pc,n,user):
  if self.header_active and pc==HEADER_RETURN:self.finish_header()
  if self.stage=='prefix' and pc==R.ENTRY:self.start_header()
  if self.header_active:
   self.steps+=1;sp=self.regs()[13];need(self.steps<=3000000 and OUTER-608<=sp<=INNER,'header/caller instruction and frame bound');self.max_stack=max(self.max_stack,OUTER-sp);self.header_reader.step(u,pc,n,user);return
  if self.stage=='ctor' and pc==R.ENTRY:
   need(not self.message_active and not self.name_active and self.original_ctor_read is not None,'constructor read exclusive model owner');before=self.regs();position=len(self.events);super().step(u,pc,n,user);self.original_ctor_read(u);after=self.regs();need(before[13]==after[13] and before[4:12]==after[4:12] and len(self.events)==position+1,'single original constructor read backend/ABI');u.reg_write(UC_ARM_REG_PC,before[14]);self.ctor_read_dispatch.append(dict(owner='constructor_model',stage=self.stage,entry=hex(pc),before=before,after=after,event_index=position,event=list(self.events[-1]),return_pc=hex(u.reg_read(UC_ARM_REG_PC))));return
  super().step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.header_active:self.header_reader.read(u,access,address,n,value,user);return
  super().read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  if self.header_active:self.header_reader.write(u,access,address,n,value,user);return
  super().write(u,access,address,n,value,user)

def bindings():
 evidence,p1=A.rewrite(V.A,'constructor_evidence',[("[['read', 55, 31, Q.LOCAL, 20]] + events","events",1)],{},'constructor_oracle');A.constructor_evidence=evidence;A.CONSTRUCTOR_RECIPE=p1
 snapshot,p2=A.rewrite(R,'Reader.run',[("self.setup();self.u.emu_start(ENTRY|1,STOP,count=20001);","",1),("list(N.COOKIES)","list(HEADER_COOKIES)",1),("self.read_bytes(DEST-16,16)==b'\\xA5'*16 and self.read_bytes(DEST+size,124-size)==b'\\xA5'*(124-size)","canaries_equal_before(self)",1)],dict(TOP=INNER,DEST=Q.LOCAL,STOP=HEADER_RETURN,HEADER_COOKIES=HEADER_COOKIES,canaries_equal_before=canaries_equal_before),'narc_reader')
 header_require,p3=A.rewrite(R,'require_case',[("def require_case(r,data,code):","def require_case(r,data,code,expected_seed):",1),("r['rng_after']==0x12345678","r['rng_after']==expected_seed",1),("cookies=list(N.COOKIES)","cookies=list(HEADER_COOKIES)",1),("cookie3=0x33333303","cookie3=0x2007509",1),("0xCCCC000C","0",3)],dict(TOP=INNER,DEST=Q.LOCAL,STOP=HEADER_RETURN,HEADER_COOKIES=HEADER_COOKIES),'narc_reader')
 run,p4=A.rewrite(V,'run_case',[("*,poison=0xC7,observe=True,variant='current'):","*,poison=0xC7,observe=True,variant='current',header_clobber=False):",1),("poison=poison,observe=observe,variant=variant)","poison=poison,observe=observe,variant=variant,header_clobber=header_clobber)",1),("]+[(p-8,p+size+8) for p,size,label in message.allocs]","]+[(p-8,p+size+8) for p,size,label in message.allocs]+driver.name_spans()",1),("(M.ARENA,M.ARENA_END)]","(M.ARENA,M.ARENA_END),(NAME_ARENA,NAME_END)]",1),("return dict(language=language,plus=plus","return dict(ctor_start_steps=driver.ctor_start_steps,header_reader=driver.header_result,header_binding=driver.header_binding,header_code_live=driver.header_code_live,header_clobber=driver.header_clobber,ctor_read_dispatch=driver.ctor_read_dispatch,raw_ram_sha256=sha(ram),names=driver.name_results,name_dispatch=driver.name_dispatch,names_code_live=driver.names_code_live,language=language,plus=plus",1)],dict(Driver=Driver,A=A,NAME_ARENA=X.NAME_ARENA,NAME_END=X.NAME_END),'message_caller')
 parent,p5=A.rewrite(V,'require_case',[("dict(parent=U,factory=None)","dict(parent=U,composition=V,factory=None)",1),("r['body']['instructions']+r['message']['instructions']+158","r['body']['instructions']+r['message']['instructions']+sum(x['instructions'] for x in r['names'])+r['header_reader']['instructions']+157",1),("calls[2]['result_r0']==B.LOADER_RESULT","calls[2]['result_r0']==r['header_reader']['end'][0]",1),("need(len(r['services'])==1 and r['services'][0]['name']=='ReadWholeNarcMemberByIdPair' and r['services'][0]['pc']=='0x2007508' and r['services'][0]['args'][:3]==[Q.LOCAL,55,31] and r['services'][0]['sp']==INNER and r['services'][0]['lr']=='0x20733fd','sole outer raw header SDK model')","need(r['services']==[],'no high-level header SDK model')",1)],dict(A=A,V=V),'message_caller')
 names,p6=A.rewrite(X,'require_case',[],dict(require_parent=parent),'species_caller')
 counter,p7=A.rewrite(R,'require_counter',[("normal['narc']==56","normal['narc']==55",1),("data['56']","data['55']",3),("b'\\xA5'","bytes([r['fill']])",1)],dict(TOP=INNER,DEST=Q.LOCAL,require_case=lambda receipt,data,code:header_require(receipt,data,code,0x12345678)),'narc_reader')
 return snapshot,header_require,run,names,counter,[p1,p2,p3,p4,p5,p6,p7]
header_snapshot,require_header_native,run_case,require_names,require_header_counter,RECIPES=bindings()

def require_header_context(r,data):
 header=r['header_reader'];binding=r['header_binding'];need(header is not None and header['narc']==55 and header['same_cpu']is True and r['header_code_live']is True and type(r['header_clobber'])is bool and header['clobber']is r['header_clobber'] and header['fill']==r['poison'] and header['rng_after']==r['seed'],'actual header owner/same CPU/code/fixture/RNG bindings')
 need(binding['neutral']is True and binding['regs']==header['entry'] and binding['ram_sha256']==header['unrelated_ram_sha256'],'actual header observer entry and phase frozen baseline')
 words=[B.SETUP,11,B.SETUP+52,Q.MISC+0x270,V.M.ARENA+32]+[r['poison']*0x01010101]*13+[r['api_calls'][1]['entry'][3]]+list(N.COOKIES[:4])+[B.SENTINEL|1];before=struct.pack('<24I',*words);after=bytearray(before);after[20:40]=data['header']['55']['member']
 # Keep the expression explicit: source-prologue spills/Trainer52 poison and
 # PUSH provenance are independent of the native reader's output receipt.
 need(header['caller_frame_before']==before.hex() and header['caller_frame_after']==bytes(after).hex() and header['destination_before']==(bytes([r['poison']])*20).hex(),'caller frame actual provenance and only twenty header bytes changed')
 calls=r['caller_calls'];need(len(calls)==3 and calls[2]['pc']=='0x20735d8' and calls[2]['sp']==calls[2]['return_sp']==header['entry'][13]==header['end'][13]==INNER and calls[2]['saved']==calls[2]['return_saved']==header['entry'][4:12]==header['end'][4:12] and calls[2]['result_r0']==header['end'][0] and calls[2]['lr']=='0x20733fd','tail header helper actual context and void residual result')
 return True

def require_ctor_dispatch(r,data):
 records=r['ctor_read_dispatch'];events=[(i,list(e)) for i,e in enumerate(r['events']) if e[0]=='read'];prefix=[e for e in r['body']['prefix_models'] if e['name']=='ReadWholeNarcMemberByIdPair'];body=[e for e in r['body']['models'] if e['name']=='ReadWholeNarcMemberByIdPair'];expected_count=188+2*r['plus'];need(len(prefix)==1 and len(records)==len(events)==1+len(body)==expected_count,'every original constructor read dispatched exactly once')
 counts=collections.Counter(event[1] for _,event in events);need(dict(counts)=={56:1,2:78,3:24,33:6,11:79+2*r['plus']},'selected Normal/Plus constructor read resource counts')
 for position,(record,(index,event),model) in enumerate(zip(records,events,prefix+body)):
  before,after=record['before'],record['after'];need(record['owner']=='constructor_model' and record['stage']=='ctor' and record['entry']==hex(R.ENTRY) and record['event_index']==index and record['event']==event and len(before)==len(after)==16 and before[:4]==model['args'] and before[13]==after[13]==model['sp'] and before[13]%8==0 and before[15]&32,'original constructor reader actual entry/owner/order/ABI/event')
  expected=list(before);expected[0]=B.LOADER_RESULT;need(after==expected and record['return_pc']==hex(before[14]&~1) and before[14]&1,'original constructor callback result and explicit BXLR-equivalent return')
  destination,narc,member=before[:3];payload=data['constructor']['party'] if narc==56 else data['constructor']['archives'][narc][member];need(event==['read',narc,member,destination,len(payload)],'single original backend copies the actual raw member')
  if position==0:need(before[14]==0x226B4A7 and before[4:12]==[B.SETUP,Q.NAME,B.ARENA+128,4]+list(N.COOKIES[4:]),'qualified inherited prefix reader loop actual caller context')
  else:need(before[4:12]==model['saved']==model['return_saved'] and before[14]==model['return_pc']|1 and after[0]==model['result'],'constructor model observer and original callback agree at actual return')
 return True

def prefix_hook_contract(data,qualified):
 # Slot0 is inactive, slot1 is trainer31/class72. Follow only the selected
 # non-rival path. The thirteen-word assignment runs its two-word loop six
 # times. All starts are authenticated by the unchanged caller qualifier.
 code=qualified['caller_code'];spans=((0x20733C0,0x20733F4),(0x2073444,0x2073452),(0x20733F0,0x20733F4),(0x20733F6,0x2073416),(0x2073422,0x2073440));groups=[[pc for pc in sorted(code) if a<=pc<=b] for a,b in spans];need(list(map(len,groups))==[24,8,3,16,13] and data['constructor']['header'][1]==72,'source caller prefix selected branch domain')
 copy_loop=[0x2073404,0x2073406,0x2073408,0x207340A]*6;route=sum(groups[:3],[])+[pc for pc in groups[3] if pc<0x2073404]+copy_loop+[pc for pc in groups[3] if pc>0x207340A]+groups[4];need(len(route)==84 and all(pc in code for pc in route),'source prefix whole instruction route and six-copy-loop count')
 helpers=((0x202A960,0x202A966),(0x202A9A8,0x202A9B0),(0x20272C8,0x20272D2),(0x20272D6,0x20272E6),(0x20272EC,0x20272F0),(0x20735D8,0x20735E2));helper_counts=[sum(a<=pc<b for pc in code) for a,b in helpers];need(helper_counts==[3,4,5,8,2,5],'source save/header straight helper count')
 n=len(data['message']['oracle']['records']['31']['words']);message_prefix=202+34*n;total=84+3+27+118+message_prefix
 return dict(caller_route=route,caller_hooks=84,seed_setter_hooks=3,save_header_helper_hooks=27,helper_counts=helper_counts,header_reader_hooks=118,message_words=n,message_prefix_hooks=message_prefix,total_before_constructor=total,scope='source-selected slot0/slot1/class72 paths; message217+34*N minus15 destruction, native reader118, no constructor fetch included')

def require_case(r,data,qualified):
 require_names(r,data,qualified);require_header_context(r,data);require_header_native(r['header_reader'],data['header'],qualified['header_code'],r['seed']);require_ctor_dispatch(r,data)
 need(type(r['ctor_start_steps'])is int and r['ctor_start_steps']==prefix_hook_contract(data,qualified)['total_before_constructor'],'source-bound caller constructor transition step checkpoint')
 return True

def require_off_pair(on,off):
 parent=X.require_off_pair(on,off);header=R.require_off_pair(on['header_reader'],off['header_reader']);need(on['header_binding']==off['header_binding'] and on['header_code_live']is off['header_code_live']is True and on['header_clobber']is off['header_clobber']is False and on['ctor_read_dispatch']==off['ctor_read_dispatch'] and on['ctor_start_steps']==off['ctor_start_steps'],'native header/constructor dispatch observer OFF/ON neutral')
 return dict(neutral=True,parent=parent,header=header,scope='header phase entire RAM/context/model/stack identical; all constructor model dispatches identical; inherited constructor scratch projection still applies to final whole-RAM hashes')

def header_counter_record(header,data,code,seed):
 disguised=copy.deepcopy(header);disguised['variant']='current';disguised['shadows']=[]
 try:require_header_native(disguised,data,code,seed)
 except ValueError as e:return dict(variant=header['variant'],result=header,tag_disguised=True,rejection=str(e))
 raise ValueError('native header counter accepted')

def require_counter(c,normal,data,qualified):
 require_case(normal,data,qualified);need(normal['plus']==1 and normal['seed']==0x12345678 and normal['poison']==0xC7 and normal['header_clobber']is False,'header counter baseline fixture');variant=c['variant'];need(variant in ('header_skip_close','header_short_read'),'finite native header caller counter');header=c['result']['header_reader'] if c['completed'] else c['header_reader'];sub=c['header_counter'];need(sub['result']==header and sub['variant']==('skip_close' if variant=='header_skip_close' else 'short_payload'),'actual header subcounter identity');require_header_counter(sub,normal['header_reader'],data['header'],qualified['header_code'])
 if c['completed']:
  need(variant=='header_skip_close' and c['tag_disguised']is True,'completed header caller counter domain');r=c['result'];need(r['plus']==normal['plus']==1 and r['seed']==normal['seed']==0x12345678 and r['poison']==normal['poison']==0xC7 and r['header_clobber']is False and r['instructions']==normal['instructions']-1 and r['ctor_start_steps']==normal['ctor_start_steps']-1 and r['mon_hex']==normal['mon_hex'] and r['prefix']['trainer_hex']==normal['prefix']['trainer_hex'] and r['seed_after']==normal['seed_after'] and r['raw_ram_sha256']==normal['raw_ram_sha256'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['unrelated_ram_sha256']==normal['unrelated_ram_sha256'] and r['end']==normal['end'] and r['header_binding']==normal['header_binding'] and r['ctor_entry']==normal['ctor_entry'] and r['ctor_return']==normal['ctor_return'] and r['body']==normal['body'] and r['names']==normal['names'] and r['message']==normal['message'] and r['ctor_read_dispatch']==normal['ctor_read_dispatch'],'same complete party/Trainer/seed/whole RAM and original constructor execution despite header close leak')
  require_header_context(r,data);disguised=copy.deepcopy(r);disguised['variant']='current';disguised['header_reader']['variant']='current';disguised['header_reader']['shadows']=[]
  try:require_case(disguised,data,qualified)
  except ValueError as e:need(str(e)==c['rejection']=='native reader complete path/ownership/stack/frozen state','complete caller header leak expected rejection identity')
  else:raise ValueError('same-game-output header leak accepted')
 else:
  need(variant=='header_short_read' and c['stage']=='prefix' and c['pc']==hex(B.ENTRY) and c['constructor_entered']is False and c['constructor_instruction_executed']is False and c['ctor_read_dispatch']==[] and c['events']==[] and c['services']==[] and c['names_completed']==0 and c['party_count']==0 and c['top_after_exception']==hex(OUTER) and c['instructions']==normal['ctor_start_steps'],'short header actual pre-constructor stage/context and original backend not invoked')
  need(c['rejection']=='native-message caller local20/untouched32/packed name provenance' and c['message_api']==normal['message']['api'][:4] and c['message_models']==normal['message']['models'][:9] and c['message_snapshots']==normal['message']['snapshots'] and c['message_live']==normal['prefix']['message_live'] and c['message_handle_live']is True and c['header_binding']==normal['header_binding'],'native reader returned, packed trainer name completed and canonical source20 prefix guard refused')
  raw=data['header']['55']['member'];corrupt=raw[:-1]+bytes([normal['poison']]);local=corrupt+bytes([normal['poison']])*32;trainer=bytearray(local);payload=N.words_bytes(data['message']['oracle']['records']['31']['words']);trainer[20:20+len(payload)]=payload;need(c['local52_hex']==local.hex() and c['trainer52_hex']==bytes(trainer).hex() and header['caller_frame_before']==normal['header_reader']['caller_frame_before'],'actual truncated header leaves original caller poison; no fixture reset')
  frame=bytearray.fromhex(normal['header_reader']['caller_frame_before']);frame[20:40]=corrupt;need(header['same_cpu']is True and header['fill']==normal['poison'] and header['clobber']is False and header['destination_before']==(bytes([normal['poison']])*20).hex() and header['caller_frame_after']==frame.hex() and c['header_binding']['neutral']is True and c['header_binding']['regs']==header['entry'] and c['header_binding']['ram_sha256']==header['unrelated_ram_sha256'],'short header actual CPU/fixture/phase-frame and neutral context binding')
 return True

def source_identities():
 result={**X.source_identities(),**R.source_identities()}
 for path in (__file__,A.__file__):result[str(Path(path).resolve().relative_to(P.SOURCE))]=sha(Path(path).read_bytes())
 return result

def analyze(rom,language,objects,strategy_object):
 R.W.require_host_budget();sources=source_identities();model=P.G.S.SHARED.read_current(rom,language);positive=[];guards=[];controls=[];off=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  qualified,proof=qualify(model,raw,language,objects,strategy_object);data=dict(preparation=Q.resources(raw),constructor=T.resources(model,raw,language,trainer=31),message=V.M.resources(raw),names=X.W.resources(raw),header=R.resources(raw))
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,qualified,data,plus,seed);require_case(r,data,qualified);positive.append(r);print(language,'native header full caller',plus,hex(seed),'verified',flush=True)
   r=run_case(model,raw,language,qualified,data,plus,observe=False);off.append(dict(result=r,proof=require_off_pair(positive[-2],r)))
  normal=next(r for r in positive if r['plus']==1 and r['seed']==0x12345678);r=run_case(model,raw,language,qualified,data,poison=0x39);require_case(r,data,qualified);need(r['mon_hex']==normal['mon_hex'],'native header caller stack poison independence');guards.append(r)
  r=run_case(model,raw,language,qualified,data,header_clobber=True);require_case(r,data,qualified);need(r['mon_hex']==normal['mon_hex'] and r['prefix']['trainer_hex']==normal['prefix']['trainer_hex'] and r['seed_after']==normal['seed_after'] and r['functional_ram_sha256']==normal['functional_ram_sha256'] and r['header_reader']['ram_sha256']==normal['header_reader']['ram_sha256'],'native header FS volatile clobber preserves selected game state and whole header-phase RAM');controls.append(r)
  for variant in ('header_skip_close','header_short_read'):
   try:r=run_case(model,raw,language,qualified,data,variant=variant)
   except ValueError as e:
    d=Driver.latest;need(d.header_result is not None and B.STACK_TOP==OUTER,'header counter snapshot actual native return and restored observer scope');sub=header_counter_record(d.header_result,data['header'],qualified['header_code'],normal['seed']);counter=dict(variant=variant,completed=False,rejection=str(e),stage=d.stage,pc=hex(d.u.reg_read(UC_ARM_REG_PC)),constructor_entered=d.ctor_entry is not None,constructor_instruction_executed=d.audit.call_entry is not None,ctor_read_dispatch=d.ctor_read_dispatch,events=copy.deepcopy(d.events),services=d.services,names_completed=len(d.name_results),party_count=d.word(B.PARTIES+0x1000+4),top_after_exception=hex(B.STACK_TOP),instructions=d.steps,header_reader=d.header_result,header_counter=sub,header_binding=d.header_binding,message_api=d.message_api,message_models=d.message.models,message_snapshots=d.message_snapshots,message_live={hex(p):dict(row) for p,row in d.message.live.items()},message_handle_live=d.message.handle_live,local52_hex=d.read_bytes(Q.LOCAL,52).hex(),trainer52_hex=d.read_bytes(Q.TRAINER,52).hex())
   else:
    sub=header_counter_record(r['header_reader'],data['header'],qualified['header_code'],normal['seed']);disguised=copy.deepcopy(r);disguised['variant']='current';disguised['header_reader']['variant']='current';disguised['header_reader']['shadows']=[]
    try:require_case(disguised,data,qualified)
    except ValueError as e:counter=dict(variant=variant,completed=True,rejection=str(e),result=r,tag_disguised=True,header_counter=sub)
    else:raise ValueError('native header full caller counter accepted '+variant)
   require_counter(counter,normal,data,qualified);counters.append(counter)
  need(source_identities()==sources,'native header caller source drift during campaign');summary=T.resource_summary(data['constructor'],[r['body'] for r in positive+guards+controls]);R.W.require_host_budget()
 return dict(schema='trainer31-native-header-caller-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,recipes=RECIPES,prefix_hook_source_contract=prefix_hook_contract(data,qualified),resources=dict(preparation=data['preparation'],constructor=summary,message=data['message']['oracle'],names=data['names']['oracle'],header=data['header']['55']['oracle']),positives=positive,guards=guards,volatile_controls=controls,observer_off=off,counters=counters,compiler_invoked=False,limits=['One initialized trainer31 caller/Plus0,1/two seeds/two stack poisons, actual native header55/31 only','Constructor ReadWhole remains original model under separate owner:188 Normal/190 Plus; no native constructor parser claim','Native header fiveFS SDK opaque models, original heap/NARC/overlay backends and other native SDK boundaries remain','No original native compiler/FSFile layout reconstruction, natural encounter, raw-save, UI or hardware validation','Header frame and phase frozen state captured at real33FC before constructor reuse; no standalone CPU/frame/packet bridge'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in output.parents and args.strategy_object.resolve().parent not in output.parents,'output must be outside retained object directories');need(all(p.is_file() for p in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'native header caller inputs must exist');result=analyze(args.rom,args.language,args.objects,args.strategy_object);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=32*1024**2,'expanded header caller report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=8*1024**2,'stored header caller report budget');R.W.require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'native header/caller composition verified; constructor read and FS SDK models remain explicit')
if __name__=='__main__':main()
