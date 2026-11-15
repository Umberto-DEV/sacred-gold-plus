#!/usr/bin/env python3
"""Follow the exact first rematch Pokemon through native creation and PartyAdd.

Private ROM inputs only; SDK heap/archive/name boundaries are explicit models.
No ROM, save, activation byte or game source is changed.
"""
from pathlib import Path
import importlib.util,json,mmap,struct,collections,copy
s=importlib.util.spec_from_file_location('rematch_consumer_dependency',Path(__file__).with_name('attribuisci_consumo.py'));C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
P,A,B=C.P,C.A,C.B;need=C.need
class First(C.Consumer):
 latest=None
 instruction_limit=500000
 stop_after_add=True
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);First.latest=self;self.mon=False;self.mon_code=set();self.mon_models=[];self.mon_writes=collections.Counter();self.mon_stop=None;self.post_form_calls=[];self.pending_service=None;self.live={};self.handles={};self.next_arena=None;self.alloc_canaries=[];self.poison=False;self.mon_variant='current';self.native_calls=[];self.move_changed=False;self.code_shadow=[]
 def regs(self):return [self.reg(i) for i in range(13)]+[self.sp(),self.uc.reg_read(C.UC_ARM_REG_LR),self.uc.reg_read(P.UC_ARM_REG_CPSR)]
 def step(self,u,a,n,_):
  if not self.mon:
   if self.consume and a==0x206DE38:self.at_create_regs=self.regs();self.at_create_ram=P.sha(bytes(u.mem_read(0x02000000,0x400000)))
   return super().step(u,a,n,_)
  self.instructions+=1;need(self.instructions<=self.instruction_limit,'firstmon instruction budget');self.max_stack=max(self.max_stack,B.STACK_TOP-self.sp());need(self.max_stack<=512,'firstmon stack budget')
  if self.pending_service and a==self.pending_service['return_pc']:
   event=self.pending_service;self.pending_service=None;event['result']=self.reg(0);event['return_sp']=self.sp();event['return_saved']=[self.reg(i) for i in range(4,12)];need(event['sp']==event['return_sp'] and event['saved']==event['return_saved'],'firstmon SDK return ABI')
   if 'output_sha256' in event:need(P.sha(bytes(u.mem_read(event['output_pointer'],event['bytes'])))==event['output_sha256'],'firstmon SDK exact output copy')
   if 'pointer' in event:need(event['result']==event['pointer'],'model allocation return pointer drift')
   if self.poison:
    for i in (1,2,3,12):u.reg_write(B.R[i],0xA5000000+i)
    u.reg_write(P.UC_ARM_REG_CPSR,(u.reg_read(P.UC_ARM_REG_CPSR)&0x0FFFFFFF)|(0xA<<28))
  if a==0x20714E8 and self.mon_variant=='wrong_fourth_move' and self.reg(2)==3:
   need(not self.move_changed,'fourthmove counter repeated');old=self.reg(1);new=33 if old!=33 else 1;u.reg_write(B.R[1],new);self.move_changed=True;self.code_shadow.append(dict(kind='register',pc=hex(a),register='r1',before=old,after=new))
  if not hasattr(self,'pending_native'):self.pending_native=[];self.extra_reads=set()
  while self.pending_native and a==self.pending_native[-1]['return_pc']:
   e=self.pending_native.pop();e.update(result=[self.reg(i) for i in range(4)],return_sp=self.sp(),return_saved=[self.reg(i) for i in range(4,12)],after_seed=self.word(0x21D15A8))
   need(e['return_sp']==e['sp'] and e['return_saved']==e['saved'],'firstmon native return ABI')
  lr=u.reg_read(C.UC_ARM_REG_LR)
  if (a==0x206DE38 and lr==0x2073A17) or (a==0x206EC40 and lr in (0x2073A23,0x2073A59)) or (a==0x20714E8 and lr==0x2073A37) or (a==0x2074524 and lr==0x2073A69) or (a==0x2072A44 and lr==0x2073A4F) or (a==0x2073AE4 and lr==0x2073A5F) or a==0x201FD44:
   e=dict(entry=hex(a),lr=hex(lr),return_pc=lr&~1,args=[self.reg(i) for i in range(4)],sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],before_seed=self.word(0x21D15A8));self.native_calls.append(e);self.pending_native.append(e)
  if self.pending_native and self.pending_native[-1]['entry']=='0x2073ae4' and a in (0x20722D4,0x206E250,0x2071754,0x206EC40):
   e=dict(entry=hex(a),lr=hex(lr),return_pc=lr&~1,args=[self.reg(i) for i in range(4)],sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],before_seed=self.word(0x21D15A8))
   if a==0x206EC40:e['value_byte']=u.mem_read(self.reg(2),1)[0]
   self.post_form_calls.append(e);self.pending_native.append(e)
  if a==0x2073A68 and self.stop_after_add:
   need(not self.pending_native,'firstmon native return incomplete')
   mon=bytes(u.mem_read(B.ARENA+128,236));dest=B.PARTIES+0x1000
   self.mon_stop=dict(r0=self.reg(0),sp=self.sp(),party_header=list(struct.unpack('<II',u.mem_read(dest,8))),workspace_hex=mon.hex(),party_hex=bytes(u.mem_read(dest+8,236)).hex(),decoded=B.decode_mon(mon),seed=self.word(0x21D15A8),buffer_sha256=P.sha(bytes(u.mem_read(B.ARENA,108))))
   u.emu_stop();return
  if a in B.STUBS:
   name=B.STUBS[a];args=[self.reg(i) for i in range(4)];need(self.sp()%8==0,'SDK service stack alignment');e=dict(name=name,args=args,sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],return_pc=u.reg_read(C.UC_ARM_REG_LR)&~1)
   if name.startswith('Heap_Alloc'):
    heap,size=args[:2];need(heap in (0,11) and 0<size<=4096,'firstmon heap request bounds');ptr=self.next_arena;self.next_arena+=(size+23)&~7;need(self.next_arena<=B.ARENA_END,'firstmon arena exhausted');self.live[ptr]=size;e.update(pointer=ptr,bytes=size,output_pointer=ptr,output_sha256=P.sha(bytes(size)))
    u.mem_write(ptr-8,b'\xA5'*8);u.mem_write(ptr+size,b'\xA5'*8);self.alloc_canaries.append((ptr,size))
   elif name=='Heap_Free':
    need(args[0] in self.live,'free unknown or dead model allocation');size=self.live.pop(args[0]);e['bytes']=size;u.mem_write(args[0],b'\xDD'*size)
   elif name=='ReadWholeNarcMemberByIdPair':
    ptr,narc,member=args[:3];payload=self.bench.archives.files(B.narc_path(narc))[member];need(0<len(payload)<=4096 and (any(p<=ptr and ptr+len(payload)<=p+sz for p,sz in self.live.items()) or B.STACK_TOP-512<=ptr and ptr+len(payload)<=B.STACK_TOP or (ptr==0x21D421C and narc==3 and len(payload)==404)),'whole archive destination bounds');e.update(bytes=len(payload),sha256=P.sha(payload),output_pointer=ptr,output_sha256=P.sha(payload))
   elif name=='GetSpeciesName':
    need(args[1] in (0,11),'name heap ABI');words=self.bench.species_name(args[0]);size=len(B.pack_species_string(words));need(0<size<128,'name result bounds');ptr=self.next_arena;self.next_arena+=(size+23)&~7;need(self.next_arena<=B.ARENA_END,'firstmon name arena exhausted');self.live[ptr]=size;e.update(pointer=ptr,bytes=size,output_pointer=ptr,output_sha256=P.sha(B.pack_species_string(words)),words_sha256=P.sha(struct.pack('<%dH'%len(words),*words)))
    u.mem_write(ptr-8,b'\xA5'*8);u.mem_write(ptr+size,b'\xA5'*8);self.alloc_canaries.append((ptr,size))
   else:raise ValueError('unqualified SDK service')
   self.mon_models.append(e);need(self.pending_service is None,'service reentry');self.pending_service=e;return
  need(a not in (B.FS_INFO,B.FS_IMAGE,B.FS_START,B.FS_UNLOAD),'unexpected overlay FS during mon')
  need(self.mon_allowed.get(a)==(n,bool(u.reg_read(P.UC_ARM_REG_CPSR)&32)) or (self.mon_variant in ('skip_party_add','skip_held_zero') and a in ((0x2073A64,0x2073A66) if self.mon_variant=='skip_party_add' else (0x2073A1E,0x2073A20)) and n==2 and bool(u.reg_read(P.UC_ARM_REG_CPSR)&32)),'firstmon instruction outside qualified code '+hex(a))
  expected=self.bench.segment_bytes(a,n)
  if self.mon_variant in ('skip_party_add','skip_held_zero') and a in ((0x2073A64,0x2073A66) if self.mon_variant=='skip_party_add' else (0x2073A1E,0x2073A20)):expected=bytes.fromhex('c046')
  need(bytes(u.mem_read(a,n))==expected,'native mon bytes drift');self.mon_code.add((a,n,bool(u.reg_read(P.UC_ARM_REG_CPSR)&32)))
 def write(self,u,access,a,n,value,_):
  if not self.mon:return super().write(u,access,a,n,value,_)
  pc=u.reg_read(P.UC_ARM_REG_PC)
  spans=[(B.STACK_TOP-512,B.STACK_TOP),(B.ARENA+128,B.ARENA+128+236),(B.PARTIES+0x1000+4,B.PARTIES+0x1000+8+236),(B.PARTIES+0x1000+0x590,B.PARTIES+0x1000+0x596)]+[(p,p+sz) for p,sz in self.live.items()]
  need(any(x<=a and a+n<=y for x,y in spans) or(a,n,pc)==(0x21D15A8,4,0x201FD52),'unexpected firstmon write '+hex(a)+' PC='+hex(pc))
  self.mon_writes[(pc,a,n)]+=1
 def read(self,u,access,a,n,value,_):
  if not self.mon:return super().read(u,access,a,n,value,_)
  pc=u.reg_read(P.UC_ARM_REG_PC)
  if not hasattr(self,'extra_reads'):self.extra_reads=set()
  spans=[(B.STACK_TOP-512,B.STACK_TOP),(B.ARENA,B.ARENA_END),(B.PARTIES+0x1000,B.PARTIES+0x1000+8+236),(B.PARTIES+0x1000+0x590,B.PARTIES+0x1000+0x596),(0x21D15A8,0x21D15AC),(0x21D421C,0x21D421C+404)]
  if not any(x<=a and a+n<=y for x,y in spans):
   need(any(x<=a and a+n<=y for x,y in self.mon_data) or(a,n,pc)==(B.SETUP+8,4,0x2073A62),'firstmon read outside qualified resources '+hex(a));self.extra_reads.add((a,n,pc))
  if max(a,B.ARENA)<min(a+n,B.ARENA_END):
   spans=[(B.ARENA,B.ARENA+108),(B.ARENA+128,B.ARENA+128+236)]+[(p,p+sz) for p,sz in self.live.items()]
   need(any(x<=a and a+n<=y for x,y in spans),'read from non-live heap/canary '+hex(a)+' PC='+hex(u.reg_read(P.UC_ARM_REG_PC)))

def run_case(model,raw,lang,prefix_code,consumer_code,mon_code,mon_data,trainer=712,seed=0x12345678,poison=False,mon_variant='current',neighbor_guard=False):
 need(mon_variant in ('current','wrong_fourth_move','skip_party_add','skip_held_zero'),'firstmon fixture domain')
 with P.patch.object(C,'Consumer',First):prefix=C.run_case(model,raw,lang,prefix_code,consumer_code,trainer,seed)
 C.require_consumer(prefix,C.input_data(raw,model));prefix=copy.deepcopy(prefix);cpu=First.latest;need(cpu.regs()==cpu.at_create_regs and P.sha(bytes(cpu.uc.mem_read(0x02000000,0x400000)))==cpu.at_create_ram,'P29 observer changed CPU/RAM')
 cpu.mon_allowed=mon_code;cpu.mon_data=mon_data;cpu.mon=True;cpu.poison=poison;cpu.mon_variant=mon_variant;
 if neighbor_guard:cpu.uc.mem_write(B.PARTIES+0x1000+0x595,b'\x7B')
 phase_before=bytes(cpu.uc.mem_read(0x02000000,0x400000))
 cpu.next_arena=B.ARENA+sum((n+23)&~7 for p,n in cpu.allocs);start_arena=cpu.next_arena
 if mon_variant in ('skip_party_add','skip_held_zero'):
  pc,target=(0x2073A64,0x2074524) if mon_variant=='skip_party_add' else (0x2073A1E,0x206EC40);before=bytes(cpu.uc.mem_read(pc,4));need(P.G.S.SHARED.branch(before,pc,'bl')==target,'named skipped call preimage');cpu.uc.mem_write(pc,bytes.fromhex('c046c046'));cpu.code_shadow.append(dict(kind='instruction',pc=hex(pc),before=before.hex(),after='c046c046'))
 cpu.uc.emu_start(0x206DE39,B.SENTINEL,count=500000);need(cpu.mon_stop is not None,'first PartyAdd return not reached')
 need(not cpu.live and not cpu.handles,'firstmon live resource leak');canaries=all(bytes(cpu.uc.mem_read(p-8,8))==b'\xA5'*8 and bytes(cpu.uc.mem_read(p+n,8))==b'\xA5'*8 for p,n in cpu.alloc_canaries+cpu.allocs)
 need(canaries,'firstmon allocation canary drift')
 ignored=[(B.STACK_TOP-512,B.STACK_TOP),(B.ARENA+128,B.ARENA+128+236),(B.PARTIES+0x1000+4,B.PARTIES+0x1000+8+236),(B.PARTIES+0x1000+0x590,B.PARTIES+0x1000+0x595),(0x21D15A8,0x21D15AC),(0x21D421C,0x21D421C+404),(start_arena-8,cpu.next_arena)]
 if mon_variant in ('skip_party_add','skip_held_zero'):
  pc=0x2073A64 if mon_variant=='skip_party_add' else 0x2073A1E;ignored.append((pc,pc+4))
 need(P.masked_hash(phase_before,ignored)==P.masked_hash(bytes(cpu.uc.mem_read(0x02000000,0x400000)),ignored),'unrelated firstmon RAM changed')
 return dict(post_form_calls=cpu.post_form_calls,neighbor_guard=neighbor_guard,neighbor_after=int.from_bytes(cpu.uc.mem_read(B.PARTIES+0x1000+0x595,1),'little'),extra_reads=[dict(address=hex(a),bytes=n,pc=hex(pc)) for a,n,pc in sorted(cpu.extra_reads)],unrelated_ram_unchanged=True,trainer=trainer,seed=seed,poison=poison,mon_variant=mon_variant,native_calls=cpu.native_calls,shadows=cpu.code_shadow,prefix=prefix,mon=cpu.mon_stop,models=cpu.mon_models,live_allocations=cpu.live,live_handles=cpu.handles,canaries=canaries,max_stack=cpu.max_stack,instructions=cpu.instructions,code=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(cpu.mon_code)],writes=[dict(pc=hex(pc),address=hex(a),bytes=n,count=k) for (pc,a,n),k in sorted(cpu.mon_writes.items())])

QUALIFICATION=Path(__file__).parents[1]/'test/firstmon-qualification.json'


def qualify(model,language):
 """Pin sparse native ranges, independently decode code and exclude data overlap."""
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_ARM
 q=json.loads(QUALIFICATION.read_text());need(q['schema']==1,'firstmon qualification schema');allowed={};data=[];codes=[]
 for row in q['code']:
  a,b=int(row['start'],16),int(row['end'],16);thumb=row['thumb'];blob=C.bench_bytes(model,a,b-a)
  need(P.sha(blob)==row['sha256'],'firstmon native code drift '+hex(a));ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB if thumb else CS_MODE_ARM).disasm(blob,a))
  need(sum(i.size for i in ins)==len(blob) and len(ins)==row['instructions'],'firstmon independent code decoding')
  for i in ins:need(i.address not in allowed,'firstmon code overlap');allowed[i.address]=(i.size,thumb)
  codes.append((a,b))
 for row in q['data']:
  a,b=int(row['start'],16),int(row['end'],16);need(P.sha(C.bench_bytes(model,a,b-a))==row['sha256'][language],'firstmon readonly data drift '+hex(a));need(all(b<=x or y<=a for x,y in codes),'firstmon code/data overlap');data.append((a,b))
 need(len(allowed)==2425 and len(data)==58,'firstmon qualification coverage');return allowed,data


def decode(mon):
 need(len(mon)==236,'firstmon encrypted record extent');d=B.decode_mon(mon)
 pid,flags,checksum=struct.unpack_from('<IHH',mon);blocks=B._decrypt(mon[8:136],checksum);order=B.PERMUTATIONS[((pid>>13)&31)%24];a=blocks[order.index(0)*32:order.index(0)*32+32];party=B._decrypt(mon[136:],pid)
 d.update(otid=struct.unpack_from('<I',a,4)[0],exp=struct.unpack_from('<I',a,8)[0],language=a[15],stats=list(struct.unpack_from('<5H',party,10)),flags=flags)
 return d


def resources(raw,model):
 """Read raw NARC members independently and retain receipts, never export fixtures."""
 archives={};receipts={}
 for narc in (2,3,11,33):
  files,r=P.RAW.raw_archive(raw,B.narc_path(narc));archives[narc]=files;receipts[str(narc)]=dict(archive={k:v for k,v in r.items() if k!='member_rom_offsets'},members={})
  # The full archive is authenticated by the exact input identity; receipts for
  # every member actually used are added by analyze, including default moves.
 names,_=P.RAW.raw_archive(raw,'a/0/2/7');bench=P.Adapter(model,raw,'unused')
 personal={str(s):bytes(archives[2][s]) for s in (22,169,469)}
 need(all(len(p)==44 for p in personal.values()),'firstmon personal record extent')
 return dict(classes=C.input_data(raw,model),personal=personal,growth=archives[3],moves=archives[11],learnset=archives[33],names={str(s):bench.species_name(s) for s in (22,169,469)},language=C.bench_bytes(model,0x20F5670,1)[0],archives=archives,receipts=receipts,name_bank_sha256=P.sha(bytes(names[237])))


def expected_record(r,data):
 create=r['prefix']['create'];_,species,level,iv=create['args'];pid=create['stack'][1];personal=data['personal'][str(species)]
 seed=create['seed'];draws=[]
 while True:
  pair=[]
  for _ in range(2):seed=(seed*0x41C64E6D+0x6073)&0xFFFFFFFF;draws.append(seed);pair.append(seed>>16)
  otid=pair[0]|pair[1]<<16
  if pair[0]^pair[1]^(pid&0xFFFF)^(pid>>16)>=8:break
  need(len(draws)<64,'finite anti-shiny oracle budget')
 selected=(r['seed']^(r['seed']>>16)^r['trainer'])&1;chosen=A.authored(r['trainer'],'B' if selected else 'A');moves=list(struct.unpack_from('<4H',chosen,8));ratio=personal[16];gender=2 if ratio==255 else 1 if ratio==254 else 0 if ratio==0 else int((pid&255)<ratio)
 nature=pid%25;stats=[]
 for i,base in enumerate(personal[1:6]):
  value=(2*base+iv)*level//100+5
  if nature//5!=nature%5 and i in (nature//5,nature%5):value=((value*(110 if i==nature//5 else 90))&0xFFFF)//100
  stats.append(value)
 hp=1 if species==292 else (2*personal[0]+iv)*level//100+level+10
 exp=struct.unpack_from('<I',data['growth'][personal[19]],4*level)[0]
 return dict(pid=pid,species=species,item=struct.unpack_from('<H',chosen,6)[0],friendship=0 if 218 in moves else 255,ability=personal[23] if personal[23] and pid&1 else personal[22],evs=[0]*6,moves=moves,pp=[data['moves'][m][6] for m in moves],pp_ups=[0]*4,ivs=[iv]*6,gender=gender,form=struct.unpack_from('<H',chosen,4)[0]>>10,nature=nature,level=level,hp=hp,max_hp=hp,status=0,ball_capsule=0,nickname=data['names'][str(species)]+[0]*(11-len(data['names'][str(species)])),otid=otid,exp=exp,language=data['language'],stats=stats),draws


def require_firstmon(r,data):
 C.require_consumer(r['prefix'],data['classes']);need(r['mon_variant']=='current','firstmon normal fixture domain');expected,draws=expected_record(r,data);mon=r['mon'];raw=bytes.fromhex(mon['workspace_hex']);actual=decode(raw)
 need(mon['decoded']==B.decode_mon(raw),'firstmon reported decoder drift')
 need(actual['checksum_ok'] and all(actual[k]==v for k,v in expected.items()),'firstmon decoded source/resource oracle')
 need(mon['party_header']==[6,1] and mon['party_hex']==mon['workspace_hex'] and mon['r0']==1,'firstmon PartyAdd count/copy/BOOL')
 need(mon['sp']==r['prefix']['create']['sp'] and mon['seed']==draws[-1],'firstmon return SP/final RNG')
 need(r['neighbor_after']==(0x7B if r['neighbor_guard'] else 0),'firstmon adjacent PartyExtra byte preserved')
 need(mon['buffer_sha256']==r['prefix']['create']['buffer_sha256'] and r['unrelated_ram_unchanged'] and r['canaries'] and not r['live_allocations'] and not r['live_handles'],'firstmon lifetime/unrelated RAM')
 need(0<r['instructions']<=500000 and 0<r['max_stack']<=512,'firstmon execution budgets')
 calls=r['native_calls'];sequence=['0x206de38']+['0x201fd44']*len(draws)+['0x206ec40']+['0x20714e8']*4+['0x2072a44','0x206ec40','0x2073ae4','0x2074524']
 need([e['entry'] for e in calls]==sequence,'firstmon complete native caller chain')
 for e in calls:
  need(e['sp']==e['return_sp'] and e['saved']==e['return_saved'] and e['return_pc']==int(e['lr'],16)&~1,'firstmon helper return ABI')
 rng=calls[1:1+len(draws)];state=r['prefix']['create']['seed']
 for i,(e,seed) in enumerate(zip(rng,draws)):
  need(e['before_seed']==state and e['after_seed']==seed and e['result'][0]==seed>>16 and e['lr']==('0x206df13' if i%2==0 else '0x206df19'),'firstmon native OTID draw order');state=seed
 at=1+len(draws);held=calls[at];need(held['args'][:3]==[B.ARENA+128,6,B.ARENA+6] and held['lr']=='0x2073a23','firstmon held-item setter activation even for zero')
 for slot,e in enumerate(calls[at+1:at+5]):need(e['args'][:3]==[B.ARENA+128,expected['moves'][slot],slot] and e['lr']=='0x2073a37','firstmon four move/slot calls')
 need(calls[-4]['args'][:2]==[0,B.ARENA+128] and calls[-4]['lr']=='0x2073a4f','firstmon capsule0 early-return ABI')
 need(calls[-3]['args'][:2]==[B.ARENA+128,112] and calls[-3]['lr']=='0x2073a59','firstmon form setter')
 post=r['post_form_calls'];need([e['entry'] for e in post]==['0x20722d4','0x206e250','0x2071754','0x206ec40'],'post-form exact source recipe helper chain')
 for e,lr in zip(post,('0x2073aed','0x2073af3','0x2073afb','0x2073b11')):
  need(e['args'][0]==B.ARENA+128 and e['lr']==lr and e['return_pc']==int(lr,16)&~1 and e['sp']==e['return_sp'] and e['saved']==e['return_saved'],'post-form complete helper ABI')
 need(post[2]['args'][1]==218 and post[2]['result'][0]==int(218 in expected['moves']) and post[3]['args'][1]==9 and post[3]['value_byte']==expected['friendship'],'post-form move check/friendship attribute9')
 need(calls[-2]['args'][0]==B.ARENA+128 and calls[-2]['lr']=='0x2073a5f','firstmon owned post-form helper caller')
 need(calls[-1]['args'][:2]==[B.PARTIES+0x1000,B.ARENA+128] and calls[-1]['result'][0]==1 and calls[-1]['lr']=='0x2073a69','firstmon PartyAdd caller/return')
 need(sum(x['count'] for x in r['writes'] if x['address']=='0x21d15a8' and x['pc']=='0x201fd52' and x['bytes']==4)==len(draws),'firstmon actual native RNG stores')
 need([x for x in r['writes'] if x['address']=='0x2311004']==[dict(pc='0x2074566',address='0x2311004',bytes=4,count=1)],'firstmon PartyAdd actual count store')
 need(sum(e['bytes']*e['count'] for e in r['writes'] if e['pc'] in ('0x2074542','0x207454a') and 0x2311008<=int(e['address'],16)<0x23110F4)==236,'firstmon actual PartyAdd copy236')
 need(r['models'] and all(e['name'] in ('Heap_Alloc','Heap_AllocAtEnd','Heap_Free','ReadWholeNarcMemberByIdPair','GetSpeciesName') for e in r['models']),'firstmon explicit SDK coverage')
 for e in r['models']:
  need('result' in e and e['sp']==e['return_sp'] and e['saved']==e['return_saved'],'firstmon SDK complete return ABI')
  if e['name']=='ReadWholeNarcMemberByIdPair':
   _,narc,member,_=e['args'];need(narc in data['archives'],'firstmon SDK archive domain');payload=data['archives'][narc][member];need(len(payload)==e['bytes'] and P.sha(payload)==e['sha256'],'firstmon SDK raw member identity')
 need({0x206DE38,0x2073A1E,0x2073A32,0x2073A64,0x2074524}<=set(int(e['ram'],16) for e in r['code']),'firstmon native code coverage')
 return True


def attest_post_form(model):
 from sgp131 import trainer_fixes as T
 payload=C.bench_bytes(model,T.FORM_STATS_HELPER,T.FORM_STATS_BYTES)
 need(len(payload)==50 and payload==T.FORM_STATS_AFTER,'post-form source recipe50 readback')
 for offset,target in ((4,T.UPDATE_MON_ABILITY),(10,T.CALC_MON_STATS),(18,T.MON_HAS_MOVE),(40,T.SET_MON_DATA)):
  need(P.G.S.SHARED.branch(payload[offset:offset+4],T.FORM_STATS_HELPER+offset,'bl')==target,'post-form recipe BL binding')
 for pc in T.FORM_SETTERS:need(P.G.S.SHARED.branch(C.bench_bytes(model,pc,4),pc,'bl')==T.SET_MON_DATA,'post-form four preceding form setters')
 for pc in T.FRIENDSHIP_CALLERS:need(P.G.S.SHARED.branch(C.bench_bytes(model,pc,4),pc,'bl')==T.FORM_STATS_HELPER,'post-form four callers')
 return dict(kind='Plus fixed-byte in-place recipe, not native original',bytes=50,ram=hex(T.FORM_STATS_HELPER),sha256=P.sha(payload),source_sha256=P.sha(Path(T.__file__).read_bytes()),before_sha256=P.sha(T.FORM_STATS_BEFORE),compiler=None)


def attest_strategy_object(model,raw,object_path):
 """Reuse a P29 object: verify its ELF/code; do not silently launch a compiler."""
 payload=object_path.read_bytes();need(P.sha(payload)=='e2429f61c7ee16071d303f7ca55cbb1553508720c6fe97b77aead9ce56e499e1','retained P29 strategy object identity')
 proof=P.audit_elf(payload,C.bench_bytes(model,0x23D6000,580),0x23D6000)
 # Reconstruct the recipe's data independently without invoking its compiler.
 from sgp13 import teams
 parties,_=P.RAW.raw_archive(raw,'a/0/5/6');headers,_=P.RAW.raw_archive(raw,'a/0/5/5');spec=json.loads((P.SOURCE/'sgp13/data/strategic-teams.json').read_text());records=bytearray();moves=bytearray()
 for team in spec['teams']:
  tid=team['trainer_id'];before=bytes(parties[tid]);need(len(before)==team['bytes'] and P.sha(before)==team['source_sha256'] and headers[tid][0]==team['type'] and headers[tid][3]==team['count'],'strategy raw recipe preimages');after=bytearray(before);first=len(moves)//8
  for move in team['moves']:
   at=move['offset'];need(struct.unpack_from('<H',after,at)[0]==move['before'],'strategy move preimage');struct.pack_into('<H',after,at,move['after']);moves+=struct.pack('<4H',at,move['before'],move['after'],0)
  records+=struct.pack('<HHIIBBBB',tid,first,teams.fnv(before),teams.fnv(after),team['type'],team['count'],len(before),len(team['moves']))
 cfg=struct.pack('<IHH',0x31544753,len(records)//16,len(moves)//8)+records+moves;need(len(cfg)==192 and C.bench_bytes(model,0x23D6600,512)==cfg+bytes(320),'retained strategy recipe config192/pad512')
 return proof


def analyze(rom,language,objects,strategy_object):
 model=P.G.S.SHARED.read_current(rom,language);post_form=attest_post_form(model)
 with rom.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
  prefix_code,prefix_proof=A.attest_objects(raw,model,objects);strategy=attest_strategy_object(model,raw,strategy_object);consumer=C.qualify_code(model,strategy);code,data_ranges=qualify(model,language);data=resources(raw,model);positives=[];counters=[];poisoned=[]
  for trainer in (712,713):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,prefix_code,consumer,code,data_ranges,trainer,seed);require_firstmon(r,data);positives.append(r)
  for variant in ('wrong_fourth_move','skip_party_add','skip_held_zero'):
   r=run_case(model,raw,language,prefix_code,consumer,code,data_ranges,mon_variant=variant)
   try:require_firstmon(dict(r,mon_variant='current'),data)
   except ValueError as e:r['rejection']=str(e)
   else:raise ValueError('firstmon counter accepted')
   if variant=='skip_held_zero':need(r['mon']==positives[0]['mon'],'zero-held counter must have identical final outputs')
   counters.append(r)
  r=run_case(model,raw,language,prefix_code,consumer,code,data_ranges,poison=True);require_firstmon(r,data);need(r['mon']==positives[0]['mon'],'SDK volatile poison must preserve exact mon/party/RNG');poisoned.append(r)
  r=run_case(model,raw,language,prefix_code,consumer,code,data_ranges,neighbor_guard=True);require_firstmon(r,data);need(r['mon']==positives[0]['mon'],'PartyExtra neighbor guard preserves exact mon/party/RNG');poisoned.append(r)
  view=P.G.S.SHARED.gifts_audit.Arm9View(raw);locations=[]
  q=json.loads(QUALIFICATION.read_text())
  for row in q['code']+q['data']+[dict(start='0x2073ae4',end='0x2073b16')]:
   a,b=int(row['start'],16),int(row['end'],16);payload=view.read(a,b-a);need(payload==C.bench_bytes(model,a,b-a),'independent firstmon ARM9 readback');locations.append(dict(ram=hex(a),rom_offset=hex(view.offset(a,b-a)),bytes=b-a,sha256=P.sha(payload)))
  for r in positives+counters+poisoned:
   for e in r['models']:
    if e['name']=='ReadWholeNarcMemberByIdPair':
     _,narc,member,_=e['args'];files,receipt=P.RAW.raw_archive(raw,B.narc_path(narc));data['receipts'][str(narc)]['members'][str(member)]=dict(bytes=e['bytes'],sha256=e['sha256'],rom_offset=hex(receipt['member_rom_offsets'][member]))
 return dict(schema='rematch-firstmon-v1',language=language,input=model['record'],post_form_recipe=post_form,prefix_proof=prefix_proof,strategy_elf=strategy,locations=locations,resources=dict(archives=data['receipts'],name_bank_sha256=data['name_bank_sha256'],native_language_byte=data['language']),positives=positives,counters=counters,poisoned=poisoned,
  source_sha256={str(p.relative_to(P.SOURCE)):P.sha(p.read_bytes()) for p in (Path(__file__),Path(C.__file__),Path(A.__file__),Path(P.__file__),Path(B.__file__),QUALIFICATION)},
  conclusions=dict(first_native_pokemon_observed=True,first_party_add_return_observed=True,installed_activation=0,natural_activation_observed=False,complete_party_observed=False),
  limits=['Same UC/RAM continuation after P29; named active1 exists only in emulated RAM; installed active0 unchanged','Heap/archive/name are bounded SDK models; no opaque NARC handle or nonzero capsule admitted','Four selected first records only; helditem0/form0/capsule0/friendship255, fixedPID/IV31, initialized setup/seed/Pluscap100','Sparse native code/data qualification; no fresh native MW compilation or general semantic equivalence claim','Stops before02073A68: no second Pokemon, complete party, constructor seed restore, SAVE, natural UI, device or performance claim'])


def main():
 import argparse,gzip
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  inputs=(args.rom,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o',args.strategy_object);out=args.json
  need(not out.exists() and not out.is_symlink(),'--json must be a fresh nonexistent file')
  need(P.SOURCE not in out.resolve().parents and out.resolve()!=P.SOURCE,'output must be outside source')
  for p in inputs:need(p.is_file() and p.resolve()!=out.resolve(),'input/output identity')
  need(args.objects.resolve() not in out.resolve().parents,'output must be outside retained objects')
  result=analyze(args.rom,args.language,args.objects,args.strategy_object);payload=(json.dumps(result,indent=2)+'\n').encode();need(len(payload)<=16*1024*1024,'firstmon report output budget');out.parent.mkdir(parents=True,exist_ok=True)
  with out.open('xb') as f:
   if out.suffix=='.gz':
    with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0) as g:g.write(payload)
   else:f.write(payload)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'4 first native Pokemon/PartyAdd returns,3 counterproofs and SDK poison verified; full party/natural activation unqualified; installed active0')


if __name__=='__main__':main()
