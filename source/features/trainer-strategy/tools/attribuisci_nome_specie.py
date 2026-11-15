#!/usr/bin/env python3
"""Verify native GetSpeciesName and its borrowed String consumer on exact ROMs.

Only heap/NARC services are models. The constructor remains a separate caller
qualification; this finite standalone chain owns one CPU and all its objects.
"""
from pathlib import Path
import importlib.util,json,mmap,struct,sys,copy,gzip,gc
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
M=load('species_message_parent',Path(__file__).with_name('attribuisci_messaggi.py'))
A=load('species_message_profile',Path(__file__).parents[1]/'test/species_name_bench.py')
P,N,B,need,sha=M.P,M.N,M.B,M.need,M.sha
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_CPSR
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
import ndspy.rom,ndspy.narc
SPECIES=A.SPECIES
ENTRY,END=0x200BCDC,0x200BD02
WRAPPER_SHA256='ebd9e75544b5604322265445535b367d06926905f6a741b762746cb27e59e93e'
CALLER,CALLER_BYTES,CALLER_SHA256=0x206F4AE,28,'d86015b43ee5d6fc684af1db99217d61f2a812d5bfdb7bb69e16fb9d1f36d870'
TOP,INNER,STOP,DEST=M.TOP,M.TOP-16,M.STOP,M.DEST
INTERNAL=(('new_msg',0x200BAF8,0x200BCED),('new_string',0x200BBA0,0x200BCF7),('destroy_msg',0x200BB44,0x200BCFF))

def resources(raw,*,strict=True):
 files,receipt=P.RAW.raw_archive(raw,'a/0/2/7');bank=bytes(files[237]);rom=ndspy.rom.NintendoDSRom(raw);need(bank==bytes(ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[237]),'independent raw species bank readback');one=N.hgss_text.read_bank_raw(bank);two=N.message_codec.Bank(bank);need(one==two.words,'independent species bank decryption');count,key=struct.unpack_from('<HH',bank);need(count>max(SPECIES),'species bank bounds for selected IDs');need(not strict or count==496 and key==0xD00E,'finite current species bank header');rows={}
 for species in SPECIES:
  words=one[species];expanded,packed=N.hgss_text.unpack_name(words);need(expanded==N.message_codec.unpack_name(words),'independent species expanded vector');need(not strict or expanded==words and not packed,'finite current species raw/unpacked representation');payload=N.words_bytes(words);mask=(key*765*(species+1))&65535;mask|=mask<<16;offset,length=struct.unpack_from('<II',bank,4+8*species);offset^=mask;length^=mask;need(length==len(words) and offset+len(payload)<=len(bank),'species MAT independent length/bounds');model=B.pack_species_string(expanded);matches=model==struct.pack('<HHI',len(words),len(words)-1,N.MAGIC)+payload+b'\0\0';need(not strict or matches,'existing current species model source correspondence');rows[str(species)]=dict(words=words,expanded=expanded,packed=packed,raw_words=len(words),raw_sha256=sha(payload),entry_bank_offset=offset,entry_rom_offset=receipt['member_rom_offsets'][237]+offset,model_sha256=sha(model),model_bytes=len(model),model_matches_raw=matches)
 return dict(bank=bank,oracle=dict(bank_bytes=len(bank),bank_sha256=sha(bank),bank_rom_offset=receipt['member_rom_offsets'][237],count=count,key=key,records=rows))

def qualify(model,raw):
 core,locations=M.qualify(model,raw);view=P.G.S.SHARED.gifts_audit.Arm9View(raw);blob=view.read(ENTRY,END-ENTRY);need(blob==P.G.piece(model['segments'],ENTRY,len(blob)) and sha(blob)==WRAPPER_SHA256,'native species wrapper independent readback');instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,ENTRY));need(sum(i.size for i in instructions)==38 and len(instructions)==16,'species wrapper exact ordinary decoding');wrapper={i.address:(i.size,True) for i in instructions};need(not set(core)&set(wrapper),'species wrapper/core code overlap');need(sha(view.read(CALLER,CALLER_BYTES))==CALLER_SHA256 and view.read(CALLER,CALLER_BYTES)==P.G.piece(model['segments'],CALLER,CALLER_BYTES),'native species caller heap0/copy11 independent readback')
 locations+= [dict(ram=hex(ENTRY),bytes=38,rom_offset=hex(view.offset(ENTRY,38)),sha256=WRAPPER_SHA256,kind='native success wrapper'),dict(ram=hex(CALLER),bytes=CALLER_BYTES,rom_offset=hex(view.offset(CALLER,CALLER_BYTES)),sha256=CALLER_SHA256,kind='constructor caller correspondence only; not executed here')];return dict(core=core,wrapper=wrapper,all={**core,**wrapper}),locations

class Species:
 latest=None
 def __init__(self,model,qualified,data,species,*,fill=0,observe=True,void_return=None,variant='current'):
  need(sys.flags.optimize==0,'run without Python -O');need(type(species)is int and species in SPECIES and type(fill)is int and fill in (0,0xC7,0x39) and type(observe)is bool and (void_return is None or type(void_return)is int and void_return in (0,0xFFFFFFFF)) and variant in ('current','wrong_heap','wrong_bank','skip_destroy','omit_string_free','short_capacity','wrong_return') and (observe or variant=='current'),'finite species API fixture domain');Species.latest=self
  need(variant!='short_capacity' or species==200,'capacity counter requires the eleven-word species boundary')
  self.model,self.qualified,self.data,self.species=model,qualified,data,species;self.fill,self.observe,self.void_return,self.variant=fill,observe,void_return,variant;bound,self.namespace,self.profile=A.profile(M);self.core=bound(model,qualified['core'],data,species,heap_fill=fill,observe=observe,void_return=void_return);self.steps=0;self.max_stack=0;self.wrapper_seen=set();self.wrapper_writes=[];self.writes=[];self.api=[];self.internal=[];self.current_internal=None;self.outer_phase=None;self.shadows=[];self.transitions=[];self.snapshots={}
 def regs(self):return self.core.regs()
 def read_bytes(self,a,n):return self.core.read_bytes(a,n)
 def setup(self):
  # A profile class owns its observer namespace and latest-instance ledger.
  # Collect preceding sandbox cycles before allocating another native CPU.
  gc.collect()
  self.u=u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);need(u.ctl_get_cpu_model()==17,'qualified species CPU model17');self.core.u=u;u.mem_map(0x1FF8000,0x8000);u.mem_map(0x2000000,0x400000);u.mem_map(0x27E0000,0x1000)
  for address,blob in self.model['segments']:u.mem_write(address,blob)
  u.mem_write(M.ARENA,b'\xD3'*(M.ARENA_END-M.ARENA));u.mem_write(TOP-128,b'\x6B'*128);u.mem_write(DEST-16,b'\xA5'*54);u.mem_write(0x21D15A8,struct.pack('<I',0x12345678));u.reg_write(UC_ARM_REG_CPSR,0x3F);u.reg_write(UC_ARM_REG_SP,TOP);u.reg_write(B.R[3],0x33333303)
  for i,value in enumerate(N.COOKIES,4):u.reg_write(B.R[i],value)
  self.before=self.read_bytes(0x2000000,0x400000);u.hook_add(UC_HOOK_CODE,self.step);u.hook_add(UC_HOOK_MEM_READ,self.read);u.hook_add(UC_HOOK_MEM_WRITE,self.write)
 def scope(self,top,phase):
  before=self.regs();digest=sha(self.read_bytes(0x2000000,0x400000));self.namespace['TOP']=top;self.core.phase=phase;need(before==self.regs() and digest==sha(self.read_bytes(0x2000000,0x400000)),'species observer scope changed CPU/RAM');self.transitions.append(dict(top=top,phase=phase,regs=before,ram_sha256=digest,neutral=True))
 def step(self,u,pc,n,user):
  self.steps+=1;regs=self.regs();sp=regs[13];need(self.steps<=20000 and TOP-128<=sp<=TOP and sp%4==0,'species native instruction/stack bound');self.max_stack=max(self.max_stack,TOP-sp)
  if self.current_internal is not None and pc==int(self.current_internal['lr'],16)&~1:
   before=self.current_internal['before'];need(sp==before[13]==INNER and regs[4:12]==before[4:12] and not self.core.pending,'species internal message return ABI');self.current_internal.update(after=regs,live={hex(p):dict(row) for p,row in self.core.live.items()},handle_live=self.core.handle_live);self.internal.append(self.current_internal);phase=self.current_internal['phase']
   if phase=='new_msg':self.snapshots['msg']=self.read_bytes(self.core.pointer['msg'],12).hex()
   if phase=='new_string':self.snapshots['string']=self.read_bytes(self.core.pointer['string'],len(self.core.payload)+10).hex()
   self.current_internal=None
  if self.outer_phase=='get_species' and self.current_internal is None and pc in {x[1] for x in INTERNAL}:
   index=len(self.internal);need(index<3 and pc==INTERNAL[index][1],'species internal native message API order');phase,entry,lr=INTERNAL[index];need(sp==INNER and regs[14]==lr,'species native wrapper internal frame/LR');self.scope(INNER,phase);self.current_internal=dict(phase=phase,entry=hex(entry),lr=hex(lr),before=regs)
  if self.outer_phase=='get_species' and self.current_internal is None:
   need(self.qualified['wrapper'].get(pc)==(n,bool(regs[15]&32)),'species wrapper fetch outside qualified code/ISA');self.wrapper_seen.add(pc)
   if self.variant=='wrong_bank' and pc==0x200BCE8:self.shadows.append(dict(pc=hex(pc),kind='native bank argument shadow',before=regs[2],after=729));u.reg_write(B.R[2],729)
   if self.variant=='skip_destroy' and pc==0x200BCFA:self.shadows.append(dict(pc=hex(pc),kind='skip native MsgData destruction BL'));u.reg_write(UC_ARM_REG_PC,0x200BCFF)
   return
  if self.variant=='omit_string_free' and self.outer_phase=='delete' and pc==0x202639C:self.shadows.append(dict(pc=hex(pc),kind='skip native String free BL'));u.reg_write(UC_ARM_REG_PC,0x20263A1)
  self.core.step(u,pc,n,user)
 def read(self,u,access,address,n,value,user):
  if self.outer_phase=='get_species' and self.current_internal is None:need(TOP-16<=address and address+n<=TOP,'native species wrapper stack read');return
  self.core.read(u,access,address,n,value,user)
 def write(self,u,access,address,n,value,user):
  pc=u.reg_read(UC_ARM_REG_PC)
  if self.outer_phase=='get_species' and self.current_internal is None:
   need(pc==ENTRY and TOP-16<=address and address+n<=TOP and n==4,'native species wrapper stack write')
   if self.observe:self.wrapper_writes.append(dict(pc=hex(pc),address=address,bytes=n,value=value));self.writes.append(dict(pc=hex(pc),address=address,bytes=n,value=value,phase='get_species'))
  else:
   self.core.write(u,access,address,n,value,user)
   if self.observe:self.writes.append(dict(self.core.writes[-1]))
 def call(self,phase,entry,args):
  self.outer_phase=phase;need(self.regs()[13]==TOP and self.regs()[4:12]==list(N.COOKIES),'species outer context preserved without restore')
  if phase in ('copy','delete'):self.scope(TOP,'copy' if phase=='copy' else 'delete_string')
  for i,value in enumerate(args):self.u.reg_write(B.R[i],value)
  self.u.reg_write(UC_ARM_REG_LR,(STOP+2 if self.variant=='wrong_return' and phase=='get_species' else STOP)|1);before=self.regs();self.u.emu_start(entry|1,STOP,count=20001);after=self.regs();need(self.u.reg_read(UC_ARM_REG_PC)==STOP and after[13]==TOP and after[4:12]==list(N.COOKIES) and after[15]&32 and self.current_internal is None and not self.core.pending,'species actual outer API return ABI');self.api.append(dict(phase=phase,entry=hex(entry),args=list(args),before=before,after=after,live={hex(p):dict(row) for p,row in self.core.live.items()},handle_live=self.core.handle_live));return after[0]
 def run(self):
  self.setup();string=self.call('get_species',ENTRY,(self.species,11 if self.variant=='wrong_heap' else 0));need(string==self.core.pointer['string'],'native GetSpeciesName String pointer result');self.snapshots['returned_string']=self.read_bytes(string,len(self.core.payload)+10).hex();self.call('copy',0x2026A68,(string,DEST,10 if self.variant=='short_capacity' else 11));destination=self.read_bytes(DEST,22);self.call('delete',0x2026380,(string,));after=self.read_bytes(0x2000000,0x400000);masked=bytearray(after)
  for address,n in [(TOP-128,128),(DEST,22)]+[(p-8,size+16) for p,size,label in self.core.allocs]:masked[address-0x2000000:address-0x2000000+n]=self.before[address-0x2000000:address-0x2000000+n]
  need(bytes(masked)==self.before,'species native unrelated RAM frozen');canaries=all(self.read_bytes(p-8,8)==b'\xA5'*8 and self.read_bytes(p+size,8)==b'\xA5'*8 for p,size,label in self.core.allocs)
  return dict(species=self.species,heap=0,bank=237,fill=self.fill,observe=self.observe,void_return=self.void_return,variant=self.variant,cpu_model=self.u.ctl_get_cpu_model(),profile=self.profile,api=self.api,internal=self.internal,snapshots=self.snapshots,models=self.core.models,native_helpers=self.core.helpers,native_writes=self.core.writes,wrapper_writes=self.wrapper_writes,writes=self.writes,observed_pcs=sorted(self.wrapper_seen|self.core.seen),allocations=[dict(pointer=p,bytes=size,label=label) for p,size,label in self.core.allocs],live={hex(p):dict(row) for p,row in self.core.live.items()},handle_live=self.core.handle_live,temp_deleted=self.core.temp_deleted,dead_store=self.core.dead_store,reads=self.core.reads,canaries=canaries,destination_hex=destination.hex(),destination_sha256=sha(destination),transitions=self.transitions,shadows=self.shadows,instructions=self.steps,max_stack=self.max_stack,ram_sha256=sha(after),unrelated_ram_sha256=sha(bytes(masked)),rng_after=self.core.word(0x21D15A8),unrelated_ram_unchanged=True)

def require_case(r,data,qualified):
 species,fill,control=r['species'],r['fill'],r['void_return'];need(type(species)is int and species in SPECIES and type(fill)is int and fill in (0,0xC7,0x39) and (control is None or type(control)is int and control in (0,0xFFFFFFFF)) and r['observe']is True and r['variant']=='current' and not r['shadows'] and r['heap']==0 and r['bank']==237 and r['cpu_model']==17,'species accepted receipt fixture domain');need(r['profile']==A.profile(M)[2],'species authenticated finite SDK profile')
 record=data['oracle']['records'][str(species)];words=record['words'];payload=N.words_bytes(words);n=len(words);length=2*n;k=((species+1)*596947+n*18749)&65535;offset=record['entry_bank_offset'];m,s=M.ARENA+32,M.ARENA+64;t=s+((length+33)&~7);h=M.HANDLE;cookies=list(N.COOKIES);c4,c5,c6,c7=cookies[:4];tail=cookies[4:];cookie3=0x33333303
 allocs=[dict(pointer=m,bytes=12,label='msg'),dict(pointer=s,bytes=length+10,label='string'),dict(pointer=t,bytes=length,label='temp')];need(r['allocations']==allocs and r['live']=={} and r['handle_live']is False and r['reads']==3 and r['temp_deleted']is True and r['dead_store']is True and r['canaries']is True and r['unrelated_ram_unchanged']is True and r['rng_after']==0x12345678,'species object ownership/canary/frozen global state')
 string=struct.pack('<HHI',n,n-1,N.MAGIC)+payload+bytes([fill])*2;need(r['snapshots']==dict(msg=struct.pack('<HHHHI',1,0,27,237,h).hex(),string=string.hex(),returned_string=string.hex()),'native species Msg/String fields and unchanged returned String')
 dest=payload+b'\xA5'*(22-length);need(r['destination_hex']==dest.hex() and r['destination_sha256']==sha(dest),'species native copy exact EOS/prefix/untouched destination tail')
 need(r['instructions']==233+34*n and r['instructions']<=20000 and r['max_stack']==96 and r['observed_pcs']==sorted(qualified['all']) and len(r['observed_pcs'])==244,'species exact native PC/hook/frame coverage')
 live=lambda *labels:{hex(a['pointer']):dict(label=a['label'],bytes=a['bytes']) for a in allocs if a['label']in labels}
 api_specs=(('get_species',ENTRY,[species,0],[species,0,0,cookie3],[s,65535,n-1,cookie3],0x200BB6B,live('string')),('copy',0x2026A68,[s,DEST,11],[s,DEST,11,cookie3],[None,s+8+length,0,0xFFFFFFFF],0x2026A99,live('string')),('delete',0x2026380,[s],[s,s+8+length,0,0xFFFFFFFF],[None,N.MAGIC,0,0xFFFFFFFF],0x20263A1,{}))
 need(len(r['api'])==3,'three native species/borrowed copy/delete API returns')
 for event,(phase,entry,args,before4,after4,last_lr,alive) in zip(r['api'],api_specs):
  before,after=event['before'],event['after'];need(event['phase']==phase and event['entry']==hex(entry) and event['args']==args and len(before)==len(after)==16 and before[:4]==before4 and before[4:12]==after[4:12]==cookies and before[13]==after[13]==TOP and before[14]==STOP|1 and after[14]==last_lr and before[15]&32 and after[15]&32 and event['live']==alive and event['handle_live']is False,'actual species outer ABI and only-String-live return')
  need(all(value is None or after[i]==value for i,value in enumerate(after4)),'species defined pointer/residual register source binding')
 internal_specs=(('new_msg',0x200BAF8,0x200BCED,[1,27,237,0],[species,c5,c6,c7],[m,0,237,0],0x200BB35,live('msg'),True),('new_string',0x200BBA0,0x200BCF7,[m,species,237,0],[species,m,c6,c7],[s,65535,n-1,0],0x200BAB1,live('msg','string'),True),('destroy_msg',0x200BB44,0x200BCFF,[m,65535,n-1,0],[s,m,c6,c7],[None,65535,n-1,0],0x200BB6B,live('string'),False))
 need(len(r['internal'])==3,'species three actual internal message APIs')
 for event,(phase,entry,lr,args,context,after4,last_lr,alive,handle) in zip(r['internal'],internal_specs):
  before,after=event['before'],event['after'];need(event['phase']==phase and event['entry']==hex(entry) and event['lr']==hex(lr) and len(before)==len(after)==16 and before[:4]==args and before[4:12]==after[4:12]==context+tail and before[13]==after[13]==INNER and before[14]==lr and after[14]==last_lr and before[15]&32 and after[15]&32 and event['live']==alive and event['handle_live']is handle,'species native wrapper internal ABI/lifetime order')
  need(all(value is None or after[i]==value for i,value in enumerate(after4)),'species internal defined pointer/register source binding')
 transitions=r['transitions'];need(len(transitions)==5 and [(x['top'],x['phase']) for x in transitions]==[(INNER,'new_msg'),(INNER,'new_string'),(INNER,'destroy_msg'),(TOP,'copy'),(TOP,'delete_string')] and all(x['neutral']is True for x in transitions),'species observer nested/outer stack scopes')
 need([x['regs'] for x in transitions]==[x['before'] for x in r['internal']]+[r['api'][0]['after'],r['api'][1]['after']],'species scope transition uses actual untouched CPU context')
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
 push(ENTRY,TOP-16,[cookie3,c4,c5,STOP|1],'get_species')
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
 store(0x2026A4C,s+2,2,n-1,'new_string');push(0x200BB44,INNER-8,[s,0x200BCFF],'destroy_msg');push(0x2026A68,TOP-16,[c4,c5,c6,STOP|1],'copy')
 for i,value in enumerate(payload):store(0x20E5AEC,DEST+i,1,value if value<128 else value|0xFFFFFF00,'copy')
 push(0x2026380,TOP-8,[c4,STOP|1],'delete_string');store(0x2026398,s+4,4,N.MAGIC+1,'delete_string')
 need(r['writes']==expected,'species entire ordered native wrapper/stack/decrypt/object/copy/destructor writes')
 need(r['wrapper_writes']==[{k:v for k,v in e.items() if k!='phase'} for e in expected[:4]] and r['native_writes']==expected[4:],'species retained component write transcripts')

def functional(r):return {key:value for key,value in r.items() if key not in ('observe','writes','native_writes','wrapper_writes')}

def require_off_pair(on,off):
 need(on['observe']is True and off['observe']is False and on['variant']==off['variant']=='current' and off['writes']==off['native_writes']==off['wrapper_writes']==[],'species paired OFF receipt domain');need(json.dumps(functional(on),sort_keys=True)==json.dumps(functional(off),sort_keys=True),'species entire functional OFF/ON state differs');return dict(neutral=True,ram_sha256=on['ram_sha256'],scope='all API/internal/register/heap/model/transition/frozen state and whole final RAM; only native write logs disabled')

def require_counter(c,normal,data,qualified):
 variant=c['variant'];need(variant in ('skip_destroy','omit_string_free','wrong_heap','wrong_bank','short_capacity','wrong_return'),'species counter finite domain');record=data['oracle']['records']['200'];n=record['raw_words'];length=2*n;s=M.ARENA+64;m=M.ARENA+32
 if c['completed']:
  need(variant in ('skip_destroy','omit_string_free') and c['tag_disguised']is True,'species completed counter domain');r=c['result'];need(r['species']==200 and r['fill']==0 and r['variant']==variant and r['snapshots']['returned_string']==normal['snapshots']['returned_string'] and r['destination_hex']==normal['destination_hex'] and r['unrelated_ram_sha256']==normal['unrelated_ram_sha256'] and r['rng_after']==normal['rng_after'] and r['canaries']is True and len(r['api'])==3,'species same-native-String/copy/frozen state counter premise')
  if variant=='skip_destroy':need(r['live']=={hex(m):dict(label='msg',bytes=12)} and r['handle_live']is True and len(r['internal'])==2 and len(r['models'])==9 and r['instructions']==normal['instructions']-15 and r['shadows']==[dict(pc='0x200bcfa',kind='skip native MsgData destruction BL')],'counter actual skipped whole native Msg/H destruction')
  else:need(r['live']=={hex(s):dict(label='string',bytes=length+10)} and r['handle_live']is False and r['dead_store']is True and len(r['internal'])==3 and len(r['models'])==10 and r['instructions']==normal['instructions']-1 and r['shadows']==[dict(pc='0x202639c',kind='skip native String free BL')],'counter actual dead-magic String allocation leak')
  disguised=copy.deepcopy(r);disguised['variant']='current';disguised['shadows']=[]
  try:require_case(disguised,data,qualified)
  except ValueError as e:need(str(e)==c['rejection'],'species counter expected replay rejection identity')
  else:raise ValueError('species same-output counter accepted')
 else:
  need(variant in ('wrong_heap','wrong_bank','short_capacity','wrong_return') and c['species']==200,'species partial counter finite premise')
  expected={'wrong_heap':('native heap request/source length',0x201AACC,16,40,'get_species',0,0,0),'wrong_bank':('native NARC encrypted-slice ABI/destination',0x200782C,60,72,'get_species',0,1,2),'short_capacity':('message execution outside qualified code/width/ISA',0x2026A9A,497,96,'copy',1,3,10),'wrong_return':('species wrapper fetch outside qualified code/ISA',STOP+2,483,96,'get_species',0,3,10)};reason,pc,steps,stack,phase,api_count,internal_count,models=expected[variant]
  need(c['rejection']==reason and c['pc']==hex(pc) and c['instructions']==steps and c['max_stack']==stack and c['phase']==phase and c['api_completed']==api_count and c['internal_completed']==internal_count and len(c['models'])==models,'species expected early failure cause/site/progress')
  if variant=='wrong_heap':need(c['live']=={} and c['handle_live']is False and c['shadows']==[],'wrong heap profile refused before allocation')
  elif variant=='wrong_bank':need(c['live']=={hex(m):dict(label='msg',bytes=12)} and c['handle_live']is True and c['reads']==0 and c['shadows']==[dict(pc='0x200bce8',kind='native bank argument shadow',before=237,after=729)],'wrong native bank refused before ciphertext delivery')
  else:need(c['live']=={hex(s):dict(label='string',bytes=length+10)} and c['handle_live']is False and c['reads']==3 and c['destination_hex']==(b'\xA5'*22).hex(),'capacity/return guard preserves only-live String and untouched destination')

def source_identities():
 paths=(__file__,A.__file__,M.__file__,N.__file__,M.Q.__file__,N.T.__file__,B.__file__,P.RAW.__file__,P.G.S.SHARED.__file__,N.hgss_text.__file__,N.message_codec.__file__)
 return {str(Path(p).resolve().relative_to(P.SOURCE)):sha(Path(p).read_bytes()) for p in paths}

def require_host_budget():
 """Audit OS high-water RSS, which short polling can underestimate."""
 import resource
 need(sys.platform=='darwin' or sys.platform.startswith('linux'),'OS peak RSS units require a qualified macOS/Linux host');value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;need(type(value)is int and value>=0,'OS peak RSS value');peak=value if sys.platform=='darwin' else value*1024;need(peak<=1024**3,'OS peak RSS exceeds the one-GiB case budget');return peak

def analyze(paths,language):
 sources=source_identities();history=[]
 for role in ('retail','base11','v4','r4'):
  model=P.G.S.SHARED.read_current(paths[role],language) if role=='r4' else P.G.S.SHARED.read_image(paths[role],language,role)
  with paths[role].open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
   data=resources(raw,strict=role in ('v4','r4'));spans=[];known=not(role=='retail' and language=='IT')
   if known:
    for start,end,thumb,digest in M.WINDOWS+((ENTRY,END,True,WRAPPER_SHA256),(CALLER,CALLER+CALLER_BYTES,True,CALLER_SHA256)):
     actual=sha(P.G.piece(model['segments'],start,end-start));need(actual==digest,'historical species native-code drift');spans.append(dict(ram=hex(start),bytes=end-start,sha256=actual))
   history.append(dict(role=role,input=model['record'],resources=data['oracle'],native_address_attributed=known,native_spans=spans))
   if role=='r4':qualified,proof=qualify(model,raw)
  if role!='r4':del model;gc.collect()
 cases=[];off_pairs=[];controls=[];counters=[]
 for species in SPECIES:
  for fill in (0,0xC7,0x39):
   result=Species(model,qualified,data,species,fill=fill).run();require_case(result,data,qualified);cases.append(result)
   if fill==0:
    need(sha(bytes.fromhex(result['snapshots']['returned_string']))==data['oracle']['records'][str(species)]['model_sha256'],'native heap-zero String equals existing constructor model')
    if species in (355,200,94):
     off=Species(model,qualified,data,species,observe=False).run();off_pairs.append(dict(result=off,proof=require_off_pair(result,off)))
 for value in (0,0xFFFFFFFF):
  result=Species(model,qualified,data,200,fill=0xC7,void_return=value).run();require_case(result,data,qualified);controls.append(result)
 normal=next(r for r in cases if r['species']==200 and r['fill']==0)
 for variant in ('skip_destroy','omit_string_free','wrong_heap','wrong_bank','short_capacity','wrong_return'):
  try:result=Species(model,qualified,data,200,variant=variant).run()
  except ValueError as e:
   d=Species.latest;c=dict(variant=variant,completed=False,rejection=str(e),species=d.species,pc=hex(d.u.reg_read(UC_ARM_REG_PC)),instructions=d.steps,max_stack=d.max_stack,phase=d.outer_phase,api_completed=len(d.api),internal_completed=len(d.internal),models=d.core.models,live={hex(p):dict(row) for p,row in d.core.live.items()},handle_live=d.core.handle_live,reads=d.core.reads,destination_hex=d.read_bytes(DEST,22).hex(),shadows=d.shadows)
  else:
   disguised=copy.deepcopy(result);disguised['variant']='current';disguised['shadows']=[]
   try:require_case(disguised,data,qualified)
   except ValueError as e:c=dict(variant=variant,completed=True,rejection=str(e),tag_disguised=True,result=result)
   else:raise ValueError('species negative evidence accepted: '+variant)
  require_counter(c,normal,data,qualified);counters.append(c)
 need(source_identities()==sources,'species source drift during campaign');return dict(schema='native-species-name-v1',language=language,input=history[-1]['input'],history=history,resources=data['oracle'],locations=proof,profile=A.profile(M)[2],qualified_code_pcs=len(qualified['all']),cases=cases,observer_off=off_pairs,void_controls=controls,counters=counters,source_sha256=sources,compiler_invoked=False,limits=['Only six selected species on exact r4/heap0/bank237,success,copy capacity11 paths execute','Six heap/NARC services remain models with an opaque handle,not native allocator/FS bodies','Standalone three-API chain is not constructor integration or natural activation','Historical retail key/layout/resource differences are recorded separately; retail IT native addresses remain unattributed','Original native compiler/object reconstruction,other species/eggs/failure/UI/SAVE/hardware remain outside coverage'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','retail','base','v4','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');need(P.SOURCE not in args.json.resolve().parents and args.json.resolve()!=P.SOURCE,'output must be outside source');require_host_budget();result=analyze(dict(r4=args.rom,retail=args.retail,base11=args.base,v4=args.v4),args.language);result['host_peak_rss_after_analysis_bytes']=require_host_budget();payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=4*1024**2,'expanded species report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=2*1024**2,'stored species report budget');require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'finite native species-name chain verified; native heap/FS and constructor integration remain separate')

if __name__=='__main__':main()
