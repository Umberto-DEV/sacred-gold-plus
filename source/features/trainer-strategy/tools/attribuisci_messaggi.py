#!/usr/bin/env python3
"""Verify native lazy-message production, packed copy and destruction.

One initialized CPU executes five native APIs on exact private r4 inputs.
Only six heap/NARC services are host models; no host serializes MsgData/String.
"""
from pathlib import Path
import importlib.util,json,mmap,struct,sys,copy,gzip
s=importlib.util.spec_from_file_location('message_copy_dependency',Path(__file__).with_name('attribuisci_preparazione.py'));Q=importlib.util.module_from_spec(s);s.loader.exec_module(Q)
N,P,B=Q.N,Q.P,Q.B;need,sha=Q.need,Q.sha
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_CPU_ARM_CORTEX_A15,UC_ARM_REG_CPSR,UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_LR
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_ARM
import ndspy.rom,ndspy.narc
NEW_WINDOWS=(
 (0x200BAF8,0x200BB12,True,'0d6203911e9d59f81448fd0218fd258b0f01831951c826688873b6e0096b8f35'),
 (0x200BB2C,0x200BB44,True,'a42f817cc131aecc284bbd092f5103588b177002b005f81f8f9800f2e85fd84c'),
 (0x200BB44,0x200BB54,True,'9c531f66e104eeb2e123322ba8d0c3380b509a8211b9726ba22ccba9fad16df2'),
 (0x200BB5E,0x200BB6C,True,'9decbbf003145f403881386b9a7f29938958e17d3c44d461b537fbb6f5a4acd7'),
 (0x200BBA0,0x200BBB0,True,'50810dd21169f7293e8188da7ac946f9ec97e5e2b0e15c43c714a2e83e06d9a6'),
 (0x200BBBC,0x200BBC8,True,'92bc4a9c65078c250be43a2e32f939e0e749e48ff0b991150ed6545174e25bef'),
 (0x200B9F8,0x200BAB6,True,'8987637dfbe1b0a7bb776ecf8ab7a2523806f672460e2188adc75ad6e1836210'),
 (0x2026354,0x2026376,True,'8c4a4e12fbe406567756f25b6c0ebee2d0fbc62c98594395a895c8c8f837424a'),
)
WINDOWS=NEW_WINDOWS+tuple(x for x in N.WINDOWS if x[0] in (0x2026A04,0x2026A14,0x2026A20,0x2026A5E,0x2026A68,0x2026A78,0x2026A84,0x20E5AD8))+tuple(x for x in Q.WINDOWS if x[0] in (0x2026380,0x202638A,0x2026396))
POOLS=((0x200BAC8,12,'1c0f42bdea3c6f1c9df39ccddc5952e37cc1debdfee39a01c995562bba595de8'),(0x2026378,8,'f12ebc53cab774353058cae7db0e28bd9cc52bc7da742bf964e4adcf5012554b'))+tuple(x for x in N.POOLS if x[0] in (0x2026A60,0x2026AA0))+tuple(x for x in Q.POOLS if x[0]==0x20263A4)
SDK={0x201AA8C:'Heap_Alloc',0x201AACC:'Heap_AllocAtEnd',0x201AB0C:'Heap_Free',0x2007688:'NARC_New',0x200782C:'NARC_ReadFromMember',0x200770C:'NARC_Delete'}
SDK_IDENTITIES=((0x2007688,128,'35a98d5803ee3482ff17562eb950031014be696e56f042386220bf42316cc156'),(0x200770C,16,'c2ee7656fd53141d0d69ca81754b2a586d746765b3981122865e5bbe52bbee40'),(0x200782C,78,'b3a62e4b13d1a8217e86c7e7418bf6a67a01c316b8525e6af034aa1fd8f7072d'))
ARENA,ARENA_END,HANDLE=0x2360000,0x2361000,0x2360800
TOP,STOP,DEST=B.STACK_TOP,B.SENTINEL,B.SETUP+0x70
HELPERS={0x200B9F8:'lazy producer',0x2026354:'String_New',0x2026A04:'CopyU16ArrayToStringN',0x20E5AD8:'ARM memcpy'}

def qualify(model,raw):
 view=P.G.S.SHARED.gifts_audit.Arm9View(raw);code={};locations=[]
 for a,b,thumb,digest in WINDOWS:
  blob=view.read(a,b-a);need(blob==P.G.piece(model['segments'],a,b-a) and sha(blob)==digest,'native message code/readback drift');ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB if thumb else CS_MODE_ARM).disasm(blob,a));need(sum(i.size for i in ins)==len(blob),'native message complete static decoding')
  for i in ins:need(i.address not in code,'message code overlap');code[i.address]=(i.size,thumb)
  locations.append(dict(ram=hex(a),bytes=b-a,rom_offset=hex(view.offset(a,b-a)),sha256=digest,kind='native code'))
 need(len(code)==228,'ordinary native message instruction map')
 for a,n,digest in POOLS:
  blob=view.read(a,n);need(blob==P.G.piece(model['segments'],a,n) and sha(blob)==digest and all(pc+size<=a or pc>=a+n for pc,(size,_) in code.items()),'message pool/readback/overlap');locations.append(dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=digest,kind='data'))
 for a,n,digest in SDK_IDENTITIES:
  need(sha(view.read(a,n))==digest and view.read(a,n)==P.G.piece(model['segments'],a,n),'message modeled SDK identity');locations.append(dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=digest,kind='modeled service identity; body not executed'))
 for a,n,expected in ((0x2007708,4,struct.pack('<I',0x210F210)),(0x210F27C,4,struct.pack('<I',0x210F118)),(0x210F118,8,b'a/0/2/7\0')):
  blob=view.read(a,n);need(blob==expected and blob==P.G.piece(model['segments'],a,n),'native NARC27 path table identity');locations.append(dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=sha(blob),kind='SDK path table data; no object layout claim'))
 return code,locations

def resources(raw):
 oracle=N.resources(raw);files,receipt=P.RAW.raw_archive(raw,'a/0/2/7');bank=bytes(files[729]);rom=ndspy.rom.NintendoDSRom(raw);need(bytes(ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[729])==bank,'independent message bank readback');need(sha(bank)==oracle['bank_sha256'],'raw/decoder bank identity');return dict(bank=bank,oracle=oracle)

class Message:
 latest=None
 def __init__(self,model,code,data,trainer,*,heap_fill=0,void_return=None,observe=True,variant='current'):
  need(sys.flags.optimize==0,'run without Python -O');need(type(trainer)is int and trainer in (21,31) and type(heap_fill)is int and heap_fill in (0,0xC7,0x39) and (void_return is None or type(void_return)is int and void_return in (0,0xFFFFFFFF)) and type(observe)is bool and variant in ('current','payload_flip','skip_xor','skip_copy','omit_temp_free','omit_narc_delete','skip_magic_store','wrong_read_destination','pool_entry','wrong_return') and (observe or variant=='current'),'finite native message fixture domain');Message.latest=self
  self.model,self.code,self.data,self.trainer=model,code,data,trainer;self.fill,self.void_return,self.observe,self.variant=heap_fill,void_return,observe,variant;self.record=data['oracle']['records'][str(trainer)];self.words=self.record['words'];self.payload=N.words_bytes(self.words);self.steps=0;self.max_stack=0;self.seen=set();self.models=[];self.writes=[];self.helpers=[];self.pending=[];self.allocs=[];self.live={};self.handle_live=False;self.pointer={};self.cursor=ARENA+32;self.reads=0;self.api=[];self.phase=None;self.shadows=[];self.msg_snapshot=None;self.string_snapshot=None;self.temp_deleted=False;self.copied=False;self.dead_store=False
 def regs(self):return [self.u.reg_read(r) for r in B.R]+[self.u.reg_read(UC_ARM_REG_SP),self.u.reg_read(UC_ARM_REG_LR),self.u.reg_read(UC_ARM_REG_CPSR)]
 def read_bytes(self,a,n):return bytes(self.u.mem_read(a,n))
 def word(self,a):return struct.unpack('<I',self.read_bytes(a,4))[0]
 def owned(self,a,n):return any(ptr<=a and a+n<=ptr+row['bytes'] for ptr,row in self.live.items())
 def setup(self):
  self.u=u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);need(u.ctl_get_cpu_model()==UC_CPU_ARM_CORTEX_A15,'qualified native message CPU model17');u.mem_map(0x1FF8000,0x8000);u.mem_map(0x2000000,0x400000);u.mem_map(0x27E0000,0x1000)
  for a,blob in self.model['segments']:u.mem_write(a,blob)
  u.mem_write(ARENA,bytes([0xD3])*(ARENA_END-ARENA));u.mem_write(TOP-128,bytes([0x6B])*128);u.mem_write(DEST-16,bytes([0xA5])*48);u.mem_write(0x21D15A8,struct.pack('<I',0x12345678));u.reg_write(UC_ARM_REG_CPSR,0x3F);u.reg_write(UC_ARM_REG_SP,TOP)
  for i,v in enumerate(N.COOKIES,4):u.reg_write(B.R[i],v)
  self.before=self.read_bytes(0x2000000,0x400000);u.hook_add(UC_HOOK_CODE,self.step);u.hook_add(UC_HOOK_MEM_READ,self.read);u.hook_add(UC_HOOK_MEM_WRITE,self.write)
 def service(self,pc):
  u=self.u;regs=self.regs();args=regs[:4];sp,lr=regs[13:15];need(sp%8==0 and regs[15]&32,'message host boundary SP/Thumb ABI');kind=SDK[pc];event=dict(name=kind,pc=hex(pc),args=args,sp=sp,lr=hex(lr),saved=regs[4:12]);result=None
  if kind in ('Heap_Alloc','Heap_AllocAtEnd'):
   label='msg' if self.phase=='new_msg' else 'string' if kind=='Heap_Alloc' else 'temp';size={'msg':12,'string':2*len(self.words)+10,'temp':len(self.payload)}[label];need(args[:2]==[11,size] and label not in self.pointer and len(self.allocs)<3,'native heap request/source length');ptr=self.cursor;self.cursor+=(size+23)&~7;need(self.cursor<HANDLE-16,'message bounded heap arena');self.pointer[label]=ptr;self.live[ptr]=dict(label=label,bytes=size);self.allocs.append((ptr,size,label));image=bytes([self.fill])*size;u.mem_write(ptr-8,b'\xA5'*8);u.mem_write(ptr,image);u.mem_write(ptr+size,b'\xA5'*8);result=ptr;event.update(label=label,pointer=ptr,bytes=size,output_sha256=sha(image))
  elif kind=='NARC_New':need(self.phase=='new_msg' and args[:2]==[27,11] and not self.handle_live,'native lazy NARC allocation ABI');self.handle_live=True;result=HANDLE;event.update(opaque_handle=HANDLE,native_object_layout_modeled=False)
  elif kind=='NARC_ReadFromMember':
   need(self.phase=='new_string' and self.handle_live and self.reads<3,'native encrypted read lifetime/count');dest=self.word(sp)
   if self.variant=='wrong_read_destination' and self.reads==2:old=dest;dest+=2;u.mem_write(sp,struct.pack('<I',dest));self.shadows.append(dict(pc=hex(pc),kind='stack argument',before=old,after=dest))
   expected=((0,4,TOP-56+0x14),(4+8*self.trainer,8,TOP-56+0x0C),(self.record['entry_bank_offset'],len(self.payload),self.pointer.get('temp')))[self.reads];need(args==[HANDLE,729,expected[0],expected[1]] and sp==TOP-56 and dest==expected[2],'native NARC encrypted-slice ABI/destination');offset,size,_=expected;need(0<=offset and offset+size<=len(self.data['bank']) and (TOP-128<=dest and dest+size<=TOP or self.owned(dest,size)),'encrypted slice/model write bounds');blob=self.data['bank'][offset:offset+size];need(len(blob)==size,'no short encrypted slice');delivered=blob
   if self.variant=='payload_flip' and self.reads==2:delivered=bytes([blob[0]^1])+blob[1:];self.shadows.append(dict(pc=hex(pc),kind='encrypted payload scratch shadow',before_sha256=sha(blob),after_sha256=sha(delivered)))
   u.mem_write(dest,delivered);event.update(read_index=self.reads,offset=offset,bytes=size,destination=dest,raw_sha256=sha(blob),delivered_sha256=sha(delivered));self.reads+=1
  elif kind=='Heap_Free':
   ptr=args[0];need(ptr in self.live,'free unknown/dead message allocation');row=self.live[ptr];need(row['label'] in ('temp','string','msg'),'message allocation type')
   if row['label']=='string':need(self.phase=='delete_string' and self.dead_store and self.word(ptr+4)==0xB6F8D2ED,'native String invalidation before free')
   if row['label']=='temp':need(self.phase=='new_string','temporary lifetime phase');self.temp_deleted=True
   if row['label']=='msg':need(self.phase=='destroy_msg' and not self.handle_live,'MsgData free follows NARC delete')
   self.live.pop(ptr);u.mem_write(ptr,b'\xDD'*row['bytes']);event.update(label=row['label'],pointer=ptr,bytes=row['bytes'])
  else:need(self.phase=='destroy_msg' and args[0]==HANDLE and self.handle_live,'single native NARC_Delete ABI');self.handle_live=False;event.update(opaque_handle=HANDLE)
  if result is not None:u.reg_write(B.R[0],result)
  elif self.void_return is not None:u.reg_write(B.R[0],self.void_return)
  event.update(result_r0=u.reg_read(B.R[0]),return_sp=u.reg_read(UC_ARM_REG_SP),return_saved=self.regs()[4:12]);need(event['sp']==event['return_sp'] and event['saved']==event['return_saved'],'modeled SDK preserved ABI');self.models.append(event);u.reg_write(UC_ARM_REG_PC,lr)
 def step(self,u,pc,n,_):
  self.steps+=1;regs=self.regs();sp=regs[13];need(self.steps<=20000 and TOP-128<=sp<=TOP and sp%4==0,'message instruction/stack budget');self.max_stack=max(self.max_stack,TOP-sp)
  while self.pending and pc==int(self.pending[-1]['lr'],16)&~1:
   event=self.pending.pop();event.update(return_sp=sp,return_saved=regs[4:12],result_r0=regs[0]);need(event['sp']==sp and event['saved']==regs[4:12],'native message helper return ABI')
  if pc in SDK:
   need(n==2 and regs[15]&32,'message host boundary encoding');self.service(pc);return
  need(self.code.get(pc)==(n,bool(regs[15]&32)),'message execution outside qualified code/width/ISA');self.seen.add(pc)
  if pc in HELPERS:
   event=dict(name=HELPERS[pc],entry=hex(pc),args=regs[:4],sp=sp,lr=hex(regs[14]),saved=regs[4:12]);self.helpers.append(event);self.pending.append(event)
  # The normal variant does not change guest state at any observer point.
  if (self.variant=='omit_temp_free' and pc==0x200BAAC) or (self.variant=='omit_narc_delete' and pc==0x200BB60):self.shadows.append(dict(pc=hex(pc),kind='skip native free/delete BL',next_pc=hex(pc+4)));u.reg_write(UC_ARM_REG_PC,(pc+4)|1)
  if self.variant=='skip_xor' and pc==0x200BA8C and not self.shadows:self.shadows.append(dict(pc=hex(pc),kind='skip first payload XOR'));u.reg_write(UC_ARM_REG_PC,(pc+2)|1)
  if self.variant=='skip_copy' and pc==0x20E5AD8 and self.phase=='copy':self.pending.pop();self.shadows.append(dict(pc=hex(pc),kind='skip destination memcpy body'));u.reg_write(UC_ARM_REG_PC,regs[14])
  if self.variant=='skip_magic_store' and pc==0x2026398:self.shadows.append(dict(pc=hex(pc),kind='skip native invalidation'));u.reg_write(UC_ARM_REG_PC,0x202639B)
 def read(self,u,access,a,n,value,_):
  inside=lambda start,size:start<=a and a+n<=start+size
  need(inside(TOP-128,128) or self.owned(a,n) or any(inside(start,size) for start,size,_ in POOLS),'native message read outside live allocation/stack/pools')
 def write(self,u,access,a,n,value,_):
  pc=u.reg_read(UC_ARM_REG_PC);stack=TOP-128<=a and a+n<=TOP;destination=self.phase=='copy' and pc==0x20E5AEC and DEST<=a and a+n<=DEST+len(self.payload);need(stack or self.owned(a,n) or destination,'native message write outside live object/stack/destination')
  if pc==0x2026398:need(a==self.pointer.get('string',-8)+4 and n==4 and value==0xB6F8D2ED,'native String dead-magic store');self.dead_store=True
  if self.observe:self.writes.append(dict(pc=hex(pc),address=a,bytes=n,value=value,phase=self.phase))
 def call(self,phase,entry,args):
  self.phase=phase;u=self.u;need(u.reg_read(UC_ARM_REG_SP)==TOP and self.regs()[4:12]==list(N.COOKIES),'API context must be preserved without restore')
  for i,v in enumerate(args):u.reg_write(B.R[i],v)
  u.reg_write(UC_ARM_REG_LR,(STOP+2 if self.variant=='wrong_return' and phase=='copy' else STOP)|1);before=self.regs();start=0x200BAC9 if self.variant=='pool_entry' and phase=='new_string' else entry|1;u.emu_start(start,STOP,count=20001);after=self.regs();need(u.reg_read(UC_ARM_REG_PC)==STOP and after[13]==TOP and after[4:12]==list(N.COOKIES) and after[15]&32 and not self.pending,'native message API return ABI/helper closure');self.api.append(dict(phase=phase,entry=hex(entry),args=list(args),before=before,after=after,pc=hex(u.reg_read(UC_ARM_REG_PC)),live={hex(p):dict(row) for p,row in self.live.items()},handle_live=self.handle_live));return after[0]
 def run(self):
  self.setup();msg=self.call('new_msg',0x200BAF8,(1,27,729,11));need(msg==self.pointer['msg'],'native MsgData return pointer');self.msg_snapshot=self.read_bytes(msg,12).hex();string=self.call('new_string',0x200BBA0,(msg,self.trainer));need(string==self.pointer['string'],'native String return pointer');self.string_snapshot=self.read_bytes(string,2*len(self.words)+10).hex();self.call('copy',0x2026A68,(string,DEST,8));self.copied=True;output=self.read_bytes(DEST,16);self.call('delete_string',0x2026380,(string,));self.call('destroy_msg',0x200BB44,(msg,));after=self.read_bytes(0x2000000,0x400000);masked=bytearray(after)
  for a,n in [(TOP-128,128),(DEST,16)]+[(p-8,size+16) for p,size,label in self.allocs]:masked[a-0x2000000:a-0x2000000+n]=self.before[a-0x2000000:a-0x2000000+n]
  need(bytes(masked)==self.before,'native message unrelated RAM frozen');canaries=all(self.read_bytes(p-8,8)==b'\xA5'*8 and self.read_bytes(p+size,8)==b'\xA5'*8 for p,size,label in self.allocs)
  return dict(trainer=self.trainer,heap_fill=self.fill,void_return=self.void_return,observe=self.observe,variant=self.variant,cpu_model=self.u.ctl_get_cpu_model(),api=self.api,msg_pointer=msg,string_pointer=string,msg_snapshot=self.msg_snapshot,string_snapshot=self.string_snapshot,destination_hex=output.hex(),destination_sha256=sha(output),models=self.models,native_helpers=self.helpers,native_writes=self.writes,observed_pcs=sorted(self.seen),allocations=[dict(pointer=p,bytes=size,label=label) for p,size,label in self.allocs],live={hex(p):row for p,row in self.live.items()},handle_live=self.handle_live,reads=self.reads,temp_deleted=self.temp_deleted,dead_store=self.dead_store,canaries=canaries,shadows=self.shadows,instructions=self.steps,max_stack=self.max_stack,ram_sha256=sha(after),rng_after=self.word(0x21D15A8),unrelated_ram_unchanged=True)

def functional(r):
 """Observer OFF omits only the native write transcript."""
 return {k:v for k,v in r.items() if k not in ('native_writes','observe')}

def require_case(r,data,code):
 """Independent finite source/ABI oracle; never executes or repairs a CPU."""
 trainer,fill=r['trainer'],r['heap_fill'];need(type(trainer)is int and trainer in (21,31) and type(fill)is int and fill in (0,0xC7,0x39),'receipt fixture domain');record=data['oracle']['records'][str(trainer)];words=record['words'];payload=N.words_bytes(words);n=len(words);m=ARENA+32;s=m+32;t=s+((2*n+33)&~7)
 allocations=[dict(pointer=m,bytes=12,label='msg'),dict(pointer=s,bytes=2*n+10,label='string'),dict(pointer=t,bytes=2*n,label='temp')]
 need(r['observe']is True and r['variant']=='current' and not r['shadows'] and r['cpu_model']==17,'receipt native observer/CPU/shadow contract')
 need(r['allocations']==allocations and r['msg_pointer']==m and r['string_pointer']==s,'receipt bounded allocation sequence')
 need(r['msg_snapshot']==struct.pack('<HHHHI',1,11,27,729,HANDLE).hex(),'receipt native MsgData fields')
 need(r['string_snapshot']==(struct.pack('<HHI',n,n-1,N.MAGIC)+payload+bytes([fill])*2).hex(),'receipt native String header/payload/untouched spare')
 destination=payload+b'\xA5'*(16-2*n);need(r['destination_hex']==destination.hex() and r['destination_sha256']==sha(destination),'receipt exact copied prefix/untouched destination tail')
 need(r['live']=={} and r['handle_live']is False and r['reads']==3 and r['temp_deleted']is True and r['dead_store']is True and r['canaries']is True and r['unrelated_ram_unchanged']is True and r['rng_after']==0x12345678,'receipt lifetime/bounds/global invariants')
 need(type(r['instructions'])is int and r['instructions']==217+34*n and r['instructions']<=20000 and r['max_stack']==80,'receipt native finite path count/frame maximum')
 need(r['observed_pcs']==sorted(code) and len(code)==228,'receipt complete ordinary native PC coverage')
 live=lambda *labels:{hex(x['pointer']):dict(label=x['label'],bytes=x['bytes']) for x in allocations if x['label'] in labels}
 expected_api=(('new_msg',0x200BAF8,[1,27,729,11],live('msg'),True),('new_string',0x200BBA0,[m,trainer],live('msg','string'),True),('copy',0x2026A68,[s,DEST,8],live('msg','string'),True),('delete_string',0x2026380,[s],live('msg'),True),('destroy_msg',0x200BB44,[m],{},False))
 need(len(r['api'])==5,'receipt five native API checkpoints')
 for call,(phase,entry,args,alive,handle) in zip(r['api'],expected_api):
  before,after=call['before'],call['after'];need(len(before)==len(after)==16 and call['phase']==phase and call['entry']==hex(entry) and call['args']==args and before[:len(args)]==args and before[13]==after[13]==TOP and before[4:12]==after[4:12]==list(N.COOKIES) and before[14]==STOP|1 and before[15]&32 and after[15]&32 and call['pc']==hex(STOP) and call['live']==alive and call['handle_live']is handle,'receipt API ABI/activation/lifetime')
  if phase in ('new_msg','new_string'):need(after[0]==(m if phase=='new_msg' else s),'receipt native pointer result')
 # Only declared argument registers are semantic at void service boundaries.
 specs=(('Heap_AllocAtEnd',0x200BB0B,24,[11,12],'msg',m),('NARC_New',0x200BB35,24,[27,11],None,HANDLE),('NARC_ReadFromMember',0x200BA11,56,[HANDLE,729,0,4],None,None),('NARC_ReadFromMember',0x200BA2B,56,[HANDLE,729,4+8*trainer,8],None,None),('Heap_Alloc',0x2026363,64,[11,2*n+10],'string',s),('Heap_AllocAtEnd',0x200BA63,56,[11,2*n],'temp',t),('NARC_ReadFromMember',0x200BA75,56,[HANDLE,729,record['entry_bank_offset'],2*n],None,None),('Heap_Free',0x200BAB1,56,[t],'temp',None),('Heap_Free',0x20263A1,8,[s],'string',None),('NARC_Delete',0x200BB65,8,[HANDLE],None,None),('Heap_Free',0x200BB6B,8,[m],'msg',None))
 cookies=list(N.COOKIES);tail=cookies[4:];c4,c5,c6,c7=cookies[:4];key_end=((trainer+1)*596947+n*18749)&65535
 saved_services=([c4,1,27,729],[m,1,27,729],[trainer,11,c6,HANDLE],[trainer,11,c6,HANDLE],[n,11,c6,HANDLE],[trainer,11,2*n,HANDLE],[trainer,t,2*n,HANDLE],[0,t,2*n,HANDLE],[s,c5,c6,c7],[m,c5,c6,c7],[m,c5,c6,c7])
 need(len(r['models'])==len(specs),'receipt exact modeled service count');read_index=0
 for event,(name,lr,depth,args,label,pointer_result),saved in zip(r['models'],specs,saved_services):
  need(event['name']==name and event['pc']==hex(next(pc for pc,v in SDK.items() if v==name)) and event['lr']==hex(lr) and event['sp']==event['return_sp']==TOP-depth and event['saved']==event['return_saved'] and len(event['saved'])==8 and event['args'][:len(args)]==args,'receipt SDK ABI/order/return preservation')
  need(event['saved']==saved+tail,'receipt SDK actual caller saved context')
  if pointer_result is not None:need(event['result_r0']==pointer_result,'receipt modeled pointer result')
  elif r['void_return']is not None:need(event['result_r0']==r['void_return'],'receipt declared void R0 control')
  if label:
   alloc=next(x for x in allocations if x['label']==label);need(event['label']==label and event['pointer']==alloc['pointer'] and event['bytes']==alloc['bytes'],'receipt allocation/free owner')
   if name!='Heap_Free':need(event['output_sha256']==sha(bytes([fill])*alloc['bytes']),'receipt modeled heap fill')
  if name=='NARC_New':need(event['opaque_handle']==HANDLE and event['native_object_layout_modeled']is False,'receipt opaque NARC boundary')
  if name=='NARC_Delete':need(event['opaque_handle']==HANDLE,'receipt NARC closure handle')
  if name=='NARC_ReadFromMember':
   offset,size=args[2:];dest=(TOP-36,TOP-44,t)[read_index];digest=sha(data['bank'][offset:offset+size]);need(event['read_index']==read_index and event['offset']==offset and event['bytes']==size and event['destination']==dest and event['raw_sha256']==event['delivered_sha256']==digest,'receipt three exact encrypted slices');read_index+=1
 helpers=(('lazy producer',0x200B9F8,0x200BBC7,8,[HANDLE,729,trainer,11],s),('String_New',0x2026354,0x200BA51,56,[n,11],s),('CopyU16ArrayToStringN',0x2026A04,0x200BAAB,56,[s,t,n],None),('ARM memcpy',0x20E5AD8,0x2026A35,80,[s+8,t,2*n],s+8),('ARM memcpy',0x20E5AD8,0x2026A99,16,[DEST,s+8,2*n],DEST))
 need(len(r['native_helpers'])==5,'receipt native nested helper count')
 saved_helpers=([c4,c5,c6,c7],[trainer,11,c6,HANDLE],[0,t,2*n,HANDLE],[n,s,2*n,t],[8,s+8,DEST,c7])
 for event,(name,entry,lr,depth,args,result),saved in zip(r['native_helpers'],helpers,saved_helpers):
  need(event['name']==name and event['entry']==hex(entry) and event['lr']==hex(lr) and event['sp']==event['return_sp']==TOP-depth and event['args'][:len(args)]==args and len(event['saved'])==8 and event['saved']==event['return_saved'],'receipt native helper ABI/order/return')
  need(event['saved']==saved+tail,'receipt native helper actual saved context')
  if result is not None:need(event['result_r0']==result,'receipt native helper pointer result')
 expected=[]
 def write(pc,a,size,value,phase):expected.append(dict(pc=hex(pc),address=a,bytes=size,value=value,phase=phase))
 for pc,a,size,v in ((0x200BB34,m+8,4,HANDLE),(0x200BB36,m,2,1),(0x200BB38,m+4,2,27),(0x200BB3C,m+6,2,729),(0x200BB3E,m+2,2,11)):write(pc,a,size,v,'new_msg')
 for pc,a,size,v in ((0x2026368,s+4,4,N.MAGIC),(0x202636A,s,2,n),(0x202636E,s+2,2,0),(0x2026372,s+8,2,65535)):write(pc,a,size,v,'new_string')
 for i,w in enumerate(words):write(0x200BA8E,t+2*i,2,w,'new_string')
 for i,b in enumerate(payload):write(0x20E5AEC,s+8+i,1,b if b<128 else b|0xFFFFFF00,'new_string')
 write(0x2026A4C,s+2,2,n-1,'new_string')
 for i,b in enumerate(payload):write(0x20E5AEC,DEST+i,1,b if b<128 else b|0xFFFFFF00,'copy')
 write(0x2026398,s+4,4,N.MAGIC+1,'delete_string')
 for w in r['native_writes']:
  need(set(w)=={'pc','address','bytes','value','phase'} and type(w['address'])is int and type(w['bytes'])is int and w['bytes'] in (1,2,4) and type(w['value'])is int and 0<=w['value']<=0xFFFFFFFF and int(w['pc'],16) in code and w['phase'] in ('new_msg','new_string','copy','delete_string','destroy_msg'),'receipt every native write record domain')
 actual=[w for w in r['native_writes'] if not TOP-128<=w['address']<TOP];need(actual==expected,'receipt exact native object/decrypt/copy/invalidation writes')
 # PUSH register lists and fixed STR [SP,#offset] from authenticated code.
 shape=[]
 def stack(pc,offsets,phase):shape.extend((hex(pc),TOP+offset,4,phase) for offset in offsets)
 stack(0x200BAF8,range(-24,0,4),'new_msg');stack(0x200BB04,(-24,),'new_msg')
 stack(0x200BBA0,(-8,-4),'new_string');stack(0x200B9F8,range(-32,-8,4),'new_string')
 for pc,offset in ((0x200BA02,-56),(0x200BA0A,-52),(0x200BA1C,-56),(0x200BA42,-44),(0x200BA4A,-40)):stack(pc,(offset,),'new_string')
 stack(0x2026354,(-64,-60),'new_string');stack(0x200BA50,(-48,),'new_string');stack(0x200BA66,(-56,),'new_string');stack(0x2026A04,range(-80,-56,4),'new_string')
 stack(0x2026A68,range(-16,0,4),'copy');stack(0x2026380,(-8,-4),'delete_string');stack(0x200BB44,(-8,-4),'destroy_msg')
 actual_stack=[(w['pc'],w['address'],w['bytes'],w['phase']) for w in r['native_writes'] if TOP-128<=w['address']<TOP];need(actual_stack==shape,'receipt entire native stack write shape/order')
 stack_values=[11,c4,c5,c6,c7,STOP|1,11,11,STOP|1,11,c4,c5,c6,c7,0x200BBC7,TOP-36,729,TOP-44,record['entry_bank_offset'],n,trainer,0x200BA51,s,t,key_end,0,t,2*n,HANDLE,0x200BAAB,c4,c5,c6,STOP|1,c4,STOP|1,c4,STOP|1]
 need([w['value'] for w in r['native_writes'] if TOP-128<=w['address']<TOP]==stack_values,'receipt every native stack value/source context')
 obj_shape=[(w['pc'],w['address'],w['bytes'],w['phase']) for w in expected]
 # Preserve cross-object/stack ordering as well as each separate transcript.
 merged=shape[:7]+obj_shape[:5]+shape[7:22]+obj_shape[5:9]+shape[22:24]+obj_shape[9:9+n]+shape[24:30]+obj_shape[9+n:10+3*n]+shape[30:34]+obj_shape[10+3*n:10+5*n]+shape[34:36]+obj_shape[10+5*n:]+shape[36:]
 need([(w['pc'],w['address'],w['bytes'],w['phase']) for w in r['native_writes']]==merged,'receipt complete native write interleaving')
 table=[w for w in r['native_writes'] if w['pc'] in ('0x200ba42','0x200ba4a')]
 need(table==[dict(pc='0x200ba42',address=TOP-44,bytes=4,value=record['entry_bank_offset'],phase='new_string'),dict(pc='0x200ba4a',address=TOP-40,bytes=4,value=n,phase='new_string')],'receipt native MAT table decryption writes')

def analyze(paths,language):
 import gc
 need(sys.flags.optimize==0,'run without Python -O');history=[]
 for role in ('retail','base11','v4','r4'):
  model=P.G.S.SHARED.read_image(paths[role],language,role)
  with paths[role].open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
   data=resources(raw);identity=[]
   if role!='retail' or language=='EN':
    for a,b,thumb,digest in WINDOWS:identity.append(dict(ram=hex(a),bytes=b-a,sha256=sha(P.G.piece(model['segments'],a,b-a)),expected_sha256=digest))
    need(all(x['sha256']==x['expected_sha256'] for x in identity),'historical native message code identity')
   if role in ('v4','r4'):code,locations=qualify(model,raw)
   history.append(dict(role=role,input=model['record'],resources=data['oracle'],native_code=identity,native_address_attributed=not(role=='retail' and language=='IT')))
  if role!='r4':del model;gc.collect()
 cases=[];controls=[];counters=[]
 for trainer in (21,31):
  for fill in (0,0xC7,0x39):
   result=Message(model,code,data,trainer,heap_fill=fill).run();require_case(result,data,code);neutral=None
   if fill==0:
    off=Message(model,code,data,trainer,heap_fill=fill,observe=False).run();need(functional(off)==functional(result),'message OFF/ON functional state differs');neutral=dict(functional_sha256=sha(json.dumps(functional(off),sort_keys=True).encode()),native_write_records=len(off['native_writes']))
   cases.append(dict(result=result,off_neutral=neutral))
 for value in (0,0xFFFFFFFF):
  result=Message(model,code,data,21,heap_fill=0xC7,void_return=value).run();require_case(result,data,code);controls.append(result)
 for variant in ('payload_flip','skip_xor','skip_copy','omit_temp_free','omit_narc_delete','skip_magic_store','wrong_read_destination','pool_entry','wrong_return'):
  try:
   result=Message(model,code,data,21,variant=variant).run();disguised=copy.deepcopy(result);disguised['variant']='current';disguised['shadows']=[]
   try:require_case(disguised,data,code)
   except ValueError as e:counters.append(dict(variant=variant,completed=True,result=result,rejection=str(e),tag_disguised=True))
   else:raise RuntimeError('negative message evidence accepted after hiding variant: '+variant)
  except ValueError as e:
   instance=Message.latest;counters.append(dict(variant=variant,completed=False,rejection=str(e),instructions=instance.steps,pc=hex(instance.u.reg_read(UC_ARM_REG_PC)),shadows=instance.shadows))
 require_counters(counters,data,code)
 return dict(schema='trainer-native-message-v1',language=language,input=history[-1]['input'],history=history,resources=data['oracle'],locations=locations,qualified_code_pcs=len(code),cpu_model=17,cases=cases,void_controls=controls,counters=counters,source_sha256={str(Path(p).relative_to(P.SOURCE)):sha(Path(p).read_bytes()) for p in (__file__,Q.__file__,N.__file__,N.T.__file__,B.__file__,N.hgss_text.__file__,N.message_codec.__file__)},compiler_invoked=False,limits=['Only lazy heap11 bank729 IDs21/31 and success/capacity8 paths execute','Six heap/NARC SDK services are models; NARC object handle has no native filesystem layout','Native reference compiler and original objects unavailable; source correspondence is not original binary reconstruction','Standalone five-API same CPU/RAM; not composed with P44 full caller or natural activation','No allocation failure, DIRECT, fallback, invalid pointer, live communication, renderer, save or physical hardware coverage'])

def require_counters(counters,data,code):
 """A random failure is not evidence that a named falsifier was exercised."""
 variants=('payload_flip','skip_xor','skip_copy','omit_temp_free','omit_narc_delete','skip_magic_store','wrong_read_destination','pool_entry','wrong_return');need([c['variant'] for c in counters]==list(variants),'counter finite order/count');record=data['oracle']['records']['21'];words=record['words'];n=len(words);payload=N.words_bytes(words);s=ARENA+64;t=s+((2*n+33)&~7);total=217+34*n
 for c in counters:
  variant=c['variant']
  if c['completed']:
   need(variant in variants[:4] and c['tag_disguised']is True,'counter completed domain');r=c['result'];need(r['variant']==variant and r['trainer']==21 and r['heap_fill']==0 and len(r['api'])==5 and r['canaries']is True and r['rng_after']==0x12345678 and r['unrelated_ram_unchanged']is True and len(r['shadows'])==1,'counter actual path/bounds premise')
   shadow=r['shadows'][0];need(shadow['pc']==dict(payload_flip='0x200782c',skip_xor='0x200ba8c',skip_copy='0x20e5ad8',omit_temp_free='0x200baac')[variant],'counter exercised exact mutation site')
   if variant in ('payload_flip','skip_xor'):
    altered=bytearray(payload)
    if variant=='payload_flip':altered[0]^=1
    else:altered[:2]=data['bank'][record['entry_bank_offset']:record['entry_bank_offset']+2]
    need(r['string_snapshot']==(struct.pack('<HHI',n,n-1,N.MAGIC)+altered+b'\0\0').hex() and r['destination_hex']==(altered+b'\xA5'*(16-2*n)).hex() and r['live']=={} and r['instructions']==total,'counter isolated changed decrypted output')
   elif variant=='skip_copy':need(r['destination_hex']==(b'\xA5'*16).hex() and r['string_snapshot']==(struct.pack('<HHI',n,n-1,N.MAGIC)+payload+b'\0\0').hex() and r['live']=={} and r['instructions']==total-(8*n+4-1),'counter skipped native output copy with intact producer')
   else:need(r['destination_hex']==(payload+b'\xA5'*(16-2*n)).hex() and r['live']=={hex(t):dict(label='temp',bytes=2*n)} and r['temp_deleted']is False and r['instructions']==total-1,'counter same output but leaked native temporary')
   disguised=copy.deepcopy(r);disguised['variant']='current';disguised['shadows']=[]
   try:require_case(disguised,data,code)
   except ValueError as e:need(str(e)==c['rejection'],'counter replay rejection identity')
   else:raise ValueError('counter evidence accepted after hiding mutation tag')
  else:
   need(variant in variants[4:],'counter partial domain');specs={'omit_narc_delete':('MsgData free follows NARC delete',0x201AB0C,total-2,0x200BB60),'skip_magic_store':('native String invalidation before free',0x201AB0C,total-16,0x2026398),'wrong_read_destination':('native NARC encrypted-slice ABI/destination',0x200782C,115,0x200782C),'pool_entry':('message execution outside qualified code/width/ISA',0x200BAC8,26,None),'wrong_return':('message execution outside qualified code/width/ISA',STOP+2,total-27,None)};reason,pc,steps,shadow=specs[variant]
   need(c['rejection']==reason and c['pc']==hex(pc) and c['instructions']==steps and len(c['shadows'])==int(shadow is not None) and (shadow is None or c['shadows'][0]['pc']==hex(shadow)),'counter expected partial stage/PC/count/mutation evidence')

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','retail','base','v4','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');need(P.SOURCE not in args.json.resolve().parents and args.json.resolve()!=P.SOURCE,'output must be outside source');result=analyze(dict(r4=args.rom,retail=args.retail,base11=args.base,v4=args.v4),args.language);payload=(json.dumps(result,indent=2)+'\n').encode();need(len(payload)<=2*1024**2,'message report budget');args.json.parent.mkdir(parents=True,exist_ok=True)
  payload=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload
  with args.json.open('xb') as f:f.write(payload)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'native message production/copy/destruction verified in the finite host contract; full caller/FS remain separate')

if __name__=='__main__':main()
