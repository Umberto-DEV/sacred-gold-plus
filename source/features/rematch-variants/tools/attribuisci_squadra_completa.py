#!/usr/bin/env python3
"""Continue the same rematch CPU through all six Pokemon and constructor return."""
from pathlib import Path
import importlib.util,json,mmap,struct,copy
s=importlib.util.spec_from_file_location('rematch_firstmon_dependency',Path(__file__).with_name('attribuisci_primo_mon.py'));M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
P,C,B,A=M.P,M.C,M.B,M.A;need=M.need
QUALIFICATION=Path(__file__).parents[1]/'test/complete-qualification.json'


RECIPE_SOURCES={'sgp13/teams.py': 'ee8c4ef77e5dc5b87cc6d434296b42e822aeacf9c5a8aa4723c5ebfad47380df', 'features/trainer-strategy/native.c': '52eb1c41912adf99f0a60bfb395e462f1ef7cacb79c648ba21d8a17accbc5fef', 'features/trainer-strategy/strategy.c': 'b60505eb767479a11084663f60cdc36ab04a4706d11b02e72b395b5347288e7d', 'features/trainer-strategy/strategy.h': 'a140c6d1896fe030f3a1b10bf36540eb45ace5912afe09ba057e8733d6bd74e5', 'sgp13/data/strategic-teams.json': '3d582d65d518bb24d32287d7cfdbe487018d166633aec77431970a03ad77cb2b', 'features/native-core/sorgenti-v-finale/plus_party.c': 'c7d64f83baff3d7dc343e905b2fec2e7a0312c048d2769b6c59998b3d74d2e2f'}

def attest_recipe_sources():
 for name,digest in RECIPE_SOURCES.items():need(P.sha((P.SOURCE/name).read_bytes())==digest,'retained recipe source drift: '+name)
 return dict(RECIPE_SOURCES)


def qualify(model,language):
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_ARM
 manifest=json.loads(QUALIFICATION.read_text());code={};data=[];spans=[]
 for row in manifest['code']:
  a,b=int(row['start'],16),int(row['end'],16);thumb=row['thumb'];blob=C.bench_bytes(model,a,b-a);need(P.sha(blob)==row['sha256'],'full constructor code drift '+hex(a));ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB if thumb else CS_MODE_ARM).disasm(blob,a));need(sum(i.size for i in ins)==len(blob) and len(ins)==row['instructions'],'full constructor code decoding')
  for i in ins:need(i.address not in code,'full constructor code overlap');code[i.address]=(i.size,thumb)
  spans.append((a,b))
 for row in manifest['data']:
  a,b=int(row['start'],16),int(row['end'],16);need(P.sha(C.bench_bytes(model,a,b-a))==row['sha256'][language],'full constructor data drift '+hex(a));need(all(b<=x or y<=a for x,y in spans),'full constructor code/data overlap');data.append((a,b))
 need(len(code)==2771 and len(data)==76,'full constructor qualification coverage');return code,data


ENTRY_COOKIES=(0x44444405,0x55555506,0x66666607,0x77777708)

class Full(M.First):
 inject_entry_cookies=False
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.full=False;self.full_variant='current';self.full_shadows=[];self.full_globals=[];self.capsule_calls=[];self.additions=[];self.restores=[];self.creation_inputs=[];self.pid_overrides=[];self.pid_pending=None;self.pid_reset=False
 def step(self,u,a,n,unused):
  if not self.full:
   if a==B.ENTRY and self.inject_entry_cookies:
    need([self.reg(i) for i in range(4,8)]==[0]*4,'initial constructor caller-cookie fixture')
    for i,value in enumerate(ENTRY_COOKIES,4):u.reg_write(B.R[i],value)
   return super().step(u,a,n,unused)
  lr=u.reg_read(C.UC_ARM_REG_LR)
  if self.pid_pending is not None and a==self.pid_pending['return_pc']:
   self.pid_pending['after_gender']=self.word(self.pid_pending['args'][3]);self.pid_pending=None
  if a==0x207397C and self.full_variant=='reset_pid_gender' and not self.pid_reset:
   target=self.sp()+0x7C;old=self.word(target);need(old==0x79 and self.trainer==713,'PID reset counter original persistent state');u.mem_write(target,struct.pack('<I',0x78));self.pid_reset=True;self.full_shadows.append(dict(kind='RAM',pc=hex(a),address=hex(target),before=old,after=0x78))
  if a==0x2073A98:
   args=[self.reg(i) for i in range(4)];e=dict(entry=hex(a),lr=hex(lr),return_pc=lr&~1,args=args,sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],before_seed=self.word(0x21D15A8),before_gender=self.word(args[3]));self.pid_overrides.append(e);self.pending_native.append(e);self.pid_pending=e
  if a==0x2073A84 and self.full_variant=='omit_prefix_free':
   need(P.G.S.SHARED.branch(bytes(u.mem_read(a,4)),a,'bl')==0x201AB0C and self.reg(0)==B.ARENA,'omit prefix free original call/argument');self.full_shadows.append(dict(kind='pc',before=hex(a),after='0x2073a88',reason='skip exactly first prefix free call'));u.reg_write(P.UC_ARM_REG_PC,0x2073A89);return
  if a==0x206DE38:self.creation_inputs.append(dict(args=[self.reg(i) for i in range(4)],stack=[self.word(self.sp()+4*i) for i in range(4)],sp=self.sp(),lr=hex(lr)))
  if a==0x201FD38:
   if lr==0x2073A95 and self.full_variant=='wrong_restore_seed':
    old=self.reg(0);u.reg_write(B.R[0],old^1);self.full_shadows.append(dict(kind='register',pc=hex(a),register='r0',before=old,after=old^1))
   e=dict(entry=hex(a),lr=hex(lr),return_pc=lr&~1,args=[self.reg(i) for i in range(4)],sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],before_seed=self.word(0x21D15A8));self.restores.append(e);self.pending_native.append(e)
  if self.pending_native and self.pending_native[-1]['entry']=='0x2072a44' and a==0x206EC40:
   size=4 if self.reg(1)==162 else 24;need(self.reg(1) in (162,171),'capsule native attribute domain');e=dict(entry=hex(a),lr=hex(lr),return_pc=lr&~1,args=[self.reg(i) for i in range(4)],sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],before_seed=self.word(0x21D15A8),value_hex=bytes(u.mem_read(self.reg(2),size)).hex());self.capsule_calls.append(e);self.pending_native.append(e)
  if a in B.STUBS and B.STUBS[a] in ('NARC_New','NARC_ReadFromMember','NARC_Delete'):
   self.instructions+=1;need(self.instructions<=self.instruction_limit and self.sp()%8==0 and self.pending_service is None,'capsule SDK entry budgets/ABI');name=B.STUBS[a];args=[self.reg(i) for i in range(4)];e=dict(name=name,args=args,sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],return_pc=lr&~1)
   if name=='NARC_New':
    need(args[:2]==[185,11] and lr==0x2072A5F,'capsule archive/heap/caller ABI');ptr=self.next_arena;self.next_arena+=32;need(self.next_arena<=B.ARENA_END and not self.handles,'opaque NARC token bounds/lifetime');self.handles[ptr]=185;e.update(pointer=ptr,opaque_token=True,native_object_layout_modeled=False)
   elif name=='NARC_ReadFromMember':
    handle,member,offset,size=args;dest=self.word(self.sp());need(self.handles.get(handle)==185 and member==0 and size==24 and offset in (240,264) and lr==0x2072A77 and dest==self.sp()+8,'capsule slice ABI')
    if self.full_variant=='wrong_capsule_slice':
     old=offset;offset=264 if offset==240 else 240;u.reg_write(B.R[2],offset);e['args'][2]=offset;self.full_shadows.append(dict(kind='register',pc=hex(a),register='r2',before=old,after=offset))
    payload=self.bench.archives.files('a/1/8/5')[0];need(len(payload)==3072 and offset+size<=len(payload) and B.STACK_TOP-512<=dest and dest+size<=B.STACK_TOP,'capsule slice exact member/destination bounds');e.update(destination=dest,bytes=size,output_pointer=dest,output_sha256=P.sha(payload[offset:offset+size]))
   else:need(args[0] in self.handles and lr==0x2072A91,'NARC delete unknown/dead handle/caller');self.handles.pop(args[0])
   self.mon_models.append(e);self.pending_service=e;return
  super().step(u,a,n,unused)
  if a==0x2073A68:
   count=self.word(B.PARTIES+0x1000+4);need(1<=count<=6,'actual subsequent PartyAdd count');mon=bytes(u.mem_read(B.ARENA+128,236));slot=bytes(u.mem_read(B.PARTIES+0x1000+8+236*(count-1),236));need(mon==slot and self.reg(0)==1,'actual subsequent PartyAdd copy/BOOL');
   if count>1:self.additions.append(dict(count=count,sp=self.sp(),mon_sha256=P.sha(mon),slot_sha256=P.sha(slot)))
 def write(self,u,access,a,n,value,unused):
  if not self.full:return super().write(u,access,a,n,value,unused)
  pc=u.reg_read(P.UC_ARM_REG_PC);party=B.PARTIES+0x1000;spans=[(B.STACK_TOP-512,B.STACK_TOP),(B.ARENA+128,B.ARENA+128+236),(party+4,party+0x5B0)]+[(p,p+size) for p,size in self.live.items()]
  need(any(x<=a and a+n<=y for x,y in spans) or(a,n,pc) in ((0x21D15A8,4,0x201FD52),(0x21D15A8,4,0x201FD3A),(0x23D8708,4,0x23D813E)),'full constructor write outside ownership')
  if a==0x21D15A8:need(value==(((self.word(a)*0x41C64E6D+0x6073)&0xFFFFFFFF) if pc==0x201FD52 else self.reg(0)),'full native seed exact store')
  if a==0x23D8708:need(value==self.word(a)+1,'full Plus hit increment')
  self.mon_writes[(pc,a,n)]+=1
  if a in (0x21D15A8,0x23D8708):self.full_globals.append(dict(pc=hex(pc),address=hex(a),bytes=n,value=value))
 def read(self,u,access,a,n,value,unused):
  if not self.full:return super().read(u,access,a,n,value,unused)
  pc=u.reg_read(P.UC_ARM_REG_PC);party=B.PARTIES+0x1000;spans=[(B.STACK_TOP-512,B.STACK_TOP),(B.SETUP,B.SETUP+0x80),(B.ARENA,B.ARENA_END),(party,party+0x5B0),(0x21D15A8,0x21D15AC),(0x21D421C,0x21D421C+404),(0x23D8700,0x23D8720)]
  need(any(x<=a and a+n<=y for x,y in spans+self.mon_data),'full constructor read outside resources '+hex(a))
  if max(a,B.ARENA)<min(a+n,B.ARENA_END):need(any(p<=a and a+n<=p+size for p,size in self.live.items()),'full read from freed/nonexistent allocation or canary')


def run_case(model,raw,language,prefix_code,consumer_code,first_code,first_data,full_code,full_data,trainer=712,seed=0x12345678,variant='current',poison=False,entry_cookies=False):
 need(variant in ('current','wrong_restore_seed','omit_prefix_free','wrong_capsule_slice','reset_pid_gender'),'full fixture domain')
 class Configured(Full):inject_entry_cookies=entry_cookies
 with P.patch.object(M,'First',Configured):first=M.run_case(model,raw,language,prefix_code,consumer_code,first_code,first_data,trainer=trainer,seed=seed,poison=poison)
 M.require_firstmon(first,M.resources(raw,model));cpu=Configured.latest;observer_regs=cpu.regs();observer_ram=P.sha(bytes(cpu.uc.mem_read(0x02000000,0x400000)));first=copy.deepcopy(first);need(cpu.regs()==observer_regs and P.sha(bytes(cpu.uc.mem_read(0x02000000,0x400000)))==observer_ram,'full first receipt observer changed CPU/RAM');first_hash=P.sha(json.dumps(first,sort_keys=True).encode());cpu.full=True;cpu.stop_after_add=False;cpu.instruction_limit=3000000;cpu.full_variant=variant;cpu.mon_allowed=full_code;cpu.mon_data=list(full_data);
 if variant=='reset_pid_gender':
  table=C.bench_bytes(model,0x20FF639,125);expected_table=bytes(0 if n//5==n%5 or j not in (n//5,n%5) else 1 if j==n//5 else 255 for n in range(25) for j in range(5));need(table==expected_table and struct.unpack('<I',C.bench_bytes(model,0x206FE8C,4))[0]==0x20FF639,'PID reset counter full nature table binding/formula');cpu.mon_data.append((0x20FF639,0x20FF639+125))
 cpu.live.update(dict(cpu.allocs));before=bytes(cpu.uc.mem_read(0x02000000,0x400000));start=cpu.next_arena
 cpu.uc.emu_start(0x2073A69,B.SENTINEL,count=3000000);need(cpu.uc.reg_read(P.UC_ARM_REG_PC)==B.SENTINEL and not cpu.pending_native and cpu.pending_service is None,'full constructor return/helper completion')
 need(P.sha(json.dumps(first,sort_keys=True).encode())==first_hash,'earlier first receipt changed after continuation')
 party=B.PARTIES+0x1000;mons=[bytes(cpu.uc.mem_read(party+8+236*i,236)) for i in range(6)];end=cpu.regs();canaries=all(bytes(cpu.uc.mem_read(p-8,8))==b'\xA5'*8 and bytes(cpu.uc.mem_read(p+size,8))==b'\xA5'*8 for p,size in cpu.alloc_canaries+cpu.allocs)
 ignored=[(B.STACK_TOP-512,B.STACK_TOP),(B.ARENA,B.ARENA+108),(B.ARENA+128,B.ARENA+128+236),(party+4,party+0x5AE),(0x21D15A8,0x21D15AC),(0x21D421C,0x21D421C+404),(0x23D8708,0x23D870C),(start-8,cpu.next_arena)]
 need(P.masked_hash(before,ignored)==P.masked_hash(bytes(cpu.uc.mem_read(0x02000000,0x400000)),ignored),'unrelated full constructor RAM changed')
 return dict(entry_cookies=entry_cookies,first_receipt_observer_neutral=True,first_receipt_sha256=first_hash,pid_overrides=cpu.pid_overrides,first=first,trainer=trainer,seed=seed,variant=variant,poison=poison,party_extra_hex=bytes(cpu.uc.mem_read(party+0x590,30)).hex(),party_tail_hex=bytes(cpu.uc.mem_read(party+0x5AE,2)).hex(),header=list(struct.unpack('<II',cpu.uc.mem_read(party,8))),mon_hex=[x.hex() for x in mons],decoded=[dict(M.decode(x),capsule_hex=B._decrypt(x[136:],struct.unpack_from('<I',x)[0])[76:100].hex()) for x in mons],seed_after=cpu.word(0x21D15A8),plus_hits=cpu.word(0x23D8708),end=end,native_calls=copy.deepcopy(cpu.native_calls),post_form_calls=copy.deepcopy(cpu.post_form_calls),capsule_calls=cpu.capsule_calls,creation_inputs=cpu.creation_inputs,seed_calls=cpu.restores,additions=cpu.additions,models=copy.deepcopy(cpu.mon_models),global_writes=cpu.full_globals,live_allocations=cpu.live,live_handles=cpu.handles,canaries=canaries,unrelated_ram_unchanged=True,shadows=cpu.full_shadows,max_stack=cpu.max_stack,instructions=cpu.instructions,code=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(cpu.mon_code)])


def capsule_binding(model):
 need(P.sha(C.bench_bytes(model,0x2007688,132))=='98505a660741af0913067b1dcb9a7baad8ee8b5168fd8ec0d7ccfaac1571a530','native modeled NARC_New code/pool identity')
 table=struct.unpack('<I',C.bench_bytes(model,0x2007708,4))[0];need(table==0x210F210,'NARC path table binding');pointer=struct.unpack('<I',C.bench_bytes(model,table+185*4,4))[0];need(pointer==0x210EC28 and C.bench_bytes(model,pointer,8)==b'a/1/8/5\0','actual NARC185 path binding')
 return dict(narc=185,path='a/1/8/5',table=hex(table),row=hex(table+185*4),pointer=hex(pointer),native_allocation_bytes=84,model='opaque32-byte token,not native NARC object layout or SDK FS execution')


def resources(raw,model):
 data=M.resources(raw,model);personal=data['archives'][2];species=sorted(set(struct.unpack_from('<H',A.authored(t,v),18*i+4)[0]&1023 for t in (712,713) for v in ('A','B') for i in range(6)));bench=P.Adapter(model,raw,'unused')
 data['personal']={str(s):bytes(personal[s]) for s in species};need(all(len(p)==44 for p in data['personal'].values()),'full raw personal extents');data['names']={str(s):bench.species_name(s) for s in species};files,receipt=P.RAW.raw_archive(raw,'a/1/8/5');need(len(files)==1 and len(files[0])==3072,'full capsule member extent');data['capsule']=bytes(files[0]);data['capsule_receipt']=receipt;data['capsule_binding']=capsule_binding(model);data['anchor']=C.bench_bytes(model,0x23D8500+72,1)[0];return data


def expectations(r,data):
 chosen=A.authored(r['trainer'],'B' if (r['seed']^(r['seed']>>16)^r['trainer'])&1 else 'A');maximum=max(struct.unpack_from('<H',chosen,18*i+2)[0] for i in range(6));need(maximum==72 and data['anchor']==81,'full six-opponent level source domain');cls=data['classes']['classes'][str(r['trainer'])];records=[];low=0x78 if cls['gender']==1 else 0x88
 for slot in range(6):
  difficulty,override,base,packed,item,*rest=struct.unpack_from('<BBHHH4HH',chosen,18*slot);species=packed&1023;form=packed>>10;moves=rest[:4];capsule=rest[4];need(override&15==0 and form==0,'full covered no-ratio-override/form0 domain');iv=difficulty*31//255;personal=data['personal'][str(species)];initial=difficulty+base+species+r['trainer'];state=initial;class_draws=[]
  for _ in range(cls['cls']):state=(state*0x41C64E6D+0x6073)&0xFFFFFFFF;class_draws.append(state)
  if override>>4==1:low&=~1
  elif override>>4==2:low|=1
  pid=((state>>16)<<8)+low;ot_draws=[]
  while True:
   pair=[]
   for _ in range(2):state=(state*0x41C64E6D+0x6073)&0xFFFFFFFF;ot_draws.append(state);pair.append(state>>16)
   if pair[0]^pair[1]^(pid&65535)^(pid>>16)>=8:break
   need(len(ot_draws)<64,'full finite OTID loop oracle')
  otid=pair[0]|pair[1]<<16;level=max(base,min(100,data['anchor']-(maximum-base)));ratio=personal[16];gender=2 if ratio==255 else 1 if ratio==254 else 0 if ratio==0 else int((pid&255)<ratio);nature=pid%25;stats=[]
  for i,b in enumerate(personal[1:6]):
   value=(2*b+iv)*level//100+5
   if nature//5!=nature%5 and i in (nature//5,nature%5):value=((value*(110 if i==nature//5 else 90))&65535)//100
   stats.append(value)
  hp=(2*personal[0]+iv)*level//100+level+10;name=data['names'][str(species)];seals=bytes(24) if capsule==0 else data['capsule'][(capsule-1)*24:capsule*24]
  fields=dict(flags=0,pid=pid,species=species,item=item,friendship=0 if 218 in moves else 255,ability=personal[23] if personal[23] and pid&1 else personal[22],evs=[0]*6,moves=moves,pp=[data['moves'][m][6] for m in moves],pp_ups=[0]*4,ivs=[iv]*6,gender=gender,form=form,nature=nature,level=level,hp=hp,max_hp=hp,status=0,ball_capsule=int(capsule!=0),nickname=name+[0]*(11-len(name)),otid=otid,exp=struct.unpack_from('<I',data['growth'][personal[19]],level*4)[0],language=data['language'],stats=stats,capsule_hex=seals.hex())
  records.append(dict(slot=slot,pid_gender=low,fields=fields,class_seed=initial,class_draws=class_draws,ot_draws=ot_draws,capsule=capsule))
 return records


def require_complete(r,data):
 M.require_firstmon(r['first'],data);need(r['variant']=='current','full normal fixture domain');expected=expectations(r,data);need(r['party_extra_hex']=='00'*30 and r['party_tail_hex']=='0000','full PartyExtra30 and unowned tail padding')
 need(r['header']==[6,6] and len(r['mon_hex'])==6 and len(r['decoded'])==6,'full actual party count/extents')
 for i,(raw_hex,reported,want) in enumerate(zip(r['mon_hex'],r['decoded'],expected)):
  raw=bytes.fromhex(raw_hex);actual=dict(M.decode(raw),capsule_hex=B._decrypt(raw[136:],struct.unpack_from('<I',raw)[0])[76:100].hex());need(actual==reported and actual['checksum_ok'] and all(actual[k]==v for k,v in want['fields'].items()),'full independent decoded record '+str(i))
 need(r['mon_hex'][0]==r['first']['mon']['workspace_hex'],'full actual first slot unchanged');need(r['seed_after']==r['seed'] and r['plus_hits']==6,'full final original seed/Plus six hits');need(r['end'][13]==B.STACK_TOP and r['end'][4:8]==(list(ENTRY_COOKIES) if r['entry_cookies'] else [0]*4) and r['end'][8:12]==[B.SENTINEL_REGS[i] for i in range(8,12)],'full constructor caller SP/r4-r11 return')
 need(r['first_receipt_observer_neutral'] and P.sha(json.dumps(r['first'],sort_keys=True).encode())==r['first_receipt_sha256'],'full earlier receipt observer/evidence integrity')
 need(r['unrelated_ram_unchanged'] and r['canaries'] and not r['live_allocations'] and not r['live_handles'],'full final resource lifetime/freeze');need(0<r['instructions']<=3000000 and 0<r['max_stack']<=512,'full execution budgets')
 for e in r['native_calls']+r['post_form_calls']+r['capsule_calls']+r['seed_calls']+r['pid_overrides']:
  need(e['sp']==e['return_sp'] and e['saved']==e['return_saved'] and e['return_pc']==int(e['lr'],16)&~1,'full native helper completed ABI')
 for e in r['models']:need('result' in e and e['sp']==e['return_sp'] and e['saved']==e['return_saved'],'full SDK completed ABI')
 live={B.ARENA:108,B.ARENA+128:236};handles={}
 for e in r['models']:
  name=e['name'];args=e['args']
  if name in ('Heap_Alloc','Heap_AllocAtEnd','GetSpeciesName'):
   pointer=e['result'];need(pointer==e['pointer'] and pointer not in live and pointer not in handles,'full reconstructed allocation ledger')
   if name=='GetSpeciesName':
    need(str(args[0]) in data['names'],'full source name species domain');image=B.pack_species_string(data['names'][str(args[0])]);need(e['bytes']==len(image) and e['output_sha256']==P.sha(image),'full source name model image')
   else:need(e['bytes']==args[1] and e['output_sha256']==P.sha(bytes(args[1])),'full zeroed heap allocation image')
   live[pointer]=e['bytes']
  elif name=='Heap_Free':need(args[0] in live and live.pop(args[0])==e['bytes'],'full reconstructed single free/lifetime')
  elif name=='ReadWholeNarcMemberByIdPair':
   _,narc,member,_=args;need(narc in data['archives'] and 0<=member<len(data['archives'][narc]),'full raw archive model domain');payload=data['archives'][narc][member];need(e['bytes']==len(payload) and e['sha256']==e['output_sha256']==P.sha(payload),'full exact raw member read model')
  elif name=='NARC_New':need(e['result'] not in handles and not handles,'full reconstructed NARC handle uniqueness');handles[e['result']]=args[0]
  elif name=='NARC_ReadFromMember':need(handles.get(args[0])==185,'full reconstructed live NARC read')
  elif name=='NARC_Delete':need(args[0] in handles,'full reconstructed NARC single delete');handles.pop(args[0])
  else:raise ValueError('full unknown SDK model event')
 need(not live and not handles,'full reconstructed resource ledger not closed')
 need(len(r['creation_inputs'])==5 and len(r['additions'])==5,'full five subsequent native creations/additions')
 for i,(e,addition) in enumerate(zip(r['creation_inputs'],r['additions']),1):
  want=expected[i]['fields'];need(e['args']==[B.ARENA+128,want['species'],want['level'],31] and e['stack']==[1,want['pid'],2,0] and e['sp']==r['first']['mon']['sp'] and e['lr']=='0x2073a17','full actual subsequent CreateMon ABI')
  need(addition==dict(count=i+1,sp=r['first']['mon']['sp'],mon_sha256=P.sha(bytes.fromhex(r['mon_hex'][i])),slot_sha256=P.sha(bytes.fromhex(r['mon_hex'][i]))),'full actual subsequent PartyAdd copy/count/return')
 need(len(r['pid_overrides'])==5,'full actual per-record PID override calls')
 for slot,e in enumerate(r['pid_overrides'],1):
  need(e['args'][3]==r['first']['mon']['sp']+0x7C and e['before_gender']==expected[slot-1]['pid_gender'] and e['after_gender']==expected[slot]['pid_gender'],'full PID gender field lifetime/carry')
 seeds=r['seed_calls'];need(len(seeds)==6,'full native setters5 plus finalrestore')
 for e,want in zip(seeds,[x['class_seed'] for x in expected[1:]]+[r['seed']]):need(e['args'][0]==want and e['result'][0]==want and e['after_seed']==want,'full native setter exact source seed')
 need([e['lr'] for e in seeds]==['0x20739c3']*5+['0x2073a95'],'full native setters/final restore callers')
 calls=r['native_calls'];need(calls,'full native call trace empty');index=0;state=r['first']['prefix']['create']['seed']
 for slot,want in enumerate(expected):
  if slot:
   state=want['class_seed']
   for seed in want['class_draws']:
    e=calls[index];need(e['entry']=='0x201fd44' and e['before_seed']==state and e['after_seed']==seed and e['result'][0]==seed>>16,'full class RNG chain');state=seed;index+=1
  e=calls[index];need(e['entry']=='0x206de38' and e['args']==[B.ARENA+128,want['fields']['species'],want['fields']['level'],31] and e['lr']=='0x2073a17','full native CreateMon chain');index+=1
  for j,seed in enumerate(want['ot_draws']):
   e=calls[index];need(e['entry']=='0x201fd44' and e['before_seed']==state and e['after_seed']==seed and e['result'][0]==seed>>16 and e['lr']==('0x206df13' if j%2==0 else '0x206df19'),'full OTID RNG chain');state=seed;index+=1
  e=calls[index];need(e['entry']=='0x206ec40' and e['args'][:3]==[B.ARENA+128,6,B.ARENA+18*slot+6] and e['lr']=='0x2073a23','full held-item setter/source record');index+=1
  for move_slot,move in enumerate(want['fields']['moves']):
   e=calls[index];need(e['entry']=='0x20714e8' and e['args'][:3]==[B.ARENA+128,move,move_slot] and e['lr']=='0x2073a37','full four actual move setters');index+=1
  tail=calls[index:index+4];need([e['entry'] for e in tail]==['0x2072a44','0x206ec40','0x2073ae4','0x2074524'] and tail[0]['args'][:2]==[want['capsule'],B.ARENA+128] and tail[0]['result'][0]==int(want['capsule']!=0) and tail[1]['args'][:2]==[B.ARENA+128,112] and tail[2]['args'][0]==B.ARENA+128 and tail[3]['args'][:2]==[B.PARTIES+0x1000,B.ARENA+128] and tail[3]['result'][0]==1,'full capsule/form/postform/add caller chain');index+=4
 need(index==len(calls) and len(r['post_form_calls'])==24,'full complete helper chain extent')
 for slot in range(6):
  post=r['post_form_calls'][slot*4:slot*4+4];need([e['entry'] for e in post]==['0x20722d4','0x206e250','0x2071754','0x206ec40'] and all(e['args'][0]==B.ARENA+128 for e in post) and [e['lr'] for e in post]==['0x2073aed','0x2073af3','0x2073afb','0x2073b11'] and post[2]['args'][1]==218 and post[2]['result'][0]==0 and post[3]['args'][1]==9 and post[3]['value_byte']==255,'full six post-form repairs')
 capsule=[x for x in expected if x['capsule']];need(len(capsule)==1,'full one capsule fixture domain');want=capsule[0];need(len(r['capsule_calls'])==2,'full actual capsule two native setters');a,b=r['capsule_calls'];need(a['args'][:2]==[B.ARENA+128,162] and a['value_hex']=='01000000' and a['lr']=='0x2072a81' and b['args'][:2]==[B.ARENA+128,171] and b['value_hex']==want['fields']['capsule_hex'] and b['lr']=='0x2072a8b','full actual capsule flag/seals24 setters')
 narc=[e for e in r['models'] if e['name'].startswith('NARC')];need([e['name'] for e in narc]==['NARC_New','NARC_ReadFromMember','NARC_Delete'],'full NARC handle lifetime calls');new,read,delete=narc;need(new['args'][:2]==[185,11] and read['args']==[new['result'],0,(want['capsule']-1)*24,24] and read['destination']==read['sp']+8 and read['output_sha256']==P.sha(bytes.fromhex(want['fields']['capsule_hex'])) and delete['args'][0]==new['result'],'full exact capsule archive slice/handle/destination')
 frees=[e for e in r['models'] if e['name']=='Heap_Free' and e['args'][0] in (B.ARENA,B.ARENA+128)];need([(e['args'][0],e['return_pc']) for e in frees]==[(B.ARENA,0x2073A88),(B.ARENA+128,0x2073A8E)],'full two original prefix frees exact callers')
 need(r['global_writes'] and r['global_writes'][-1]==dict(pc='0x201fd3a',address='0x21d15a8',bytes=4,value=r['seed']),'full last native seed store original backup')
 need({0x2073A84,0x2073A8A,0x2073A90,0x2073A96}<=set(int(e['ram'],16) for e in r['code']),'full final return instruction coverage');return True


def analyze(rom,language,objects,strategy_object):
 recipe_sources=attest_recipe_sources();model=P.G.S.SHARED.read_current(rom,language);post_form=M.attest_post_form(model)
 with rom.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
  prefix,proof=A.attest_objects(raw,model,objects);strategy=M.attest_strategy_object(model,raw,strategy_object);codes=(prefix,C.qualify_code(model,strategy),*M.qualify(model,language),*qualify(model,language));data=resources(raw,model);positives=[];counters=[];guards=[]
  for trainer in (712,713):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,*codes,trainer=trainer,seed=seed);require_complete(r,data);positives.append(r)
  for variant in ('wrong_restore_seed','omit_prefix_free','wrong_capsule_slice','reset_pid_gender'):
   r=run_case(model,raw,language,*codes,trainer=713,variant=variant)
   try:require_complete(dict(r,variant='current'),data)
   except ValueError as e:r['rejection']=str(e)
   else:raise ValueError('full constructor counter accepted as normal')
   normal=positives[2];need(r['header']==normal['header'],'full counter must reach six actual slots')
   if variant in ('wrong_restore_seed','omit_prefix_free'):need(r['mon_hex']==normal['mon_hex'],'full return/lifetime counter must preserve exact party')
   if variant in ('omit_prefix_free','wrong_capsule_slice','reset_pid_gender'):need(r['seed_after']==normal['seed_after'],'full orthogonal counter must preserve original final seed')
   counters.append(r)
  for kw in ({'poison':True},{'entry_cookies':True}):
   r=run_case(model,raw,language,*codes,trainer=713,**kw);require_complete(r,data);need(r['mon_hex']==positives[2]['mon_hex'] and r['seed_after']==positives[2]['seed_after'],'SDK poison/caller-cookie guard must preserve exact party/seed');guards.append(r)
  manifest=json.loads(QUALIFICATION.read_text());view=P.G.S.SHARED.gifts_audit.Arm9View(raw);locations=[]
  extras=[(0x2073AE4,50),(0x2007688,132),(0x2007708,4),(0x210F4F4,4),(0x210EC28,8),(0x20FF639,125)]
  for a,size in [(int(row['start'],16),int(row['end'],16)-int(row['start'],16)) for row in manifest['code']+manifest['data']]+extras:
   payload=view.read(a,size);need(payload==C.bench_bytes(model,a,size),'full independent raw ARM9 section readback');locations.append(dict(ram=hex(a),bytes=size,rom_offset=hex(view.offset(a,size)),sha256=P.sha(payload)))
  archive_cache={};receipts={}
  for r in positives+counters+guards:
   for e in r['models']:
    if e['name']!='ReadWholeNarcMemberByIdPair':continue
    narc,member=e['args'][1:3]
    if narc not in archive_cache:
     files,receipt=P.RAW.raw_archive(raw,B.narc_path(narc));archive_cache[narc]=(files,receipt);receipts[str(narc)]=dict(archive={k:v for k,v in receipt.items() if k!='member_rom_offsets'},members={})
    files,receipt=archive_cache[narc];receipts[str(narc)]['members'][str(member)]=dict(bytes=len(files[member]),sha256=P.sha(bytes(files[member])),rom_offset=hex(receipt['member_rom_offsets'][member]))
  capsule=data['capsule_receipt'];receipts['185']=dict(archive={k:v for k,v in capsule.items() if k!='member_rom_offsets'},member0=dict(bytes=len(data['capsule']),sha256=P.sha(data['capsule']),rom_offset=hex(capsule['member_rom_offsets'][0])),slices=[dict(capsule=i,offset=(i-1)*24,bytes=24,sha256=P.sha(data['capsule'][(i-1)*24:i*24])) for i in (11,12)])
 return dict(schema='rematch-complete-constructor-v1',recipe_sources=recipe_sources,language=language,input=model['record'],prefix_proof=proof,strategy_elf=strategy,post_form_recipe=post_form,capsule_binding=data['capsule_binding'],resources=receipts,name_bank_sha256=data['name_bank_sha256'],locations=locations,positives=positives,counters=counters,guards=guards,
  source_sha256={str(p.relative_to(P.SOURCE)):P.sha(p.read_bytes()) for p in (Path(__file__),Path(M.__file__),Path(C.__file__),Path(A.__file__),Path(P.__file__),Path(B.__file__),QUALIFICATION,M.QUALIFICATION)},
  conclusions=dict(six_native_pokemon_observed=True,constructor_return_observed=True,original_seed_restoration_observed=True,resource_lifetime_closed=True,installed_activation=0,natural_activation_observed=False),
  limits=['Same CPU/RAM after qualified first Pokemon; evidence deepcopy changes no guest state','Eight selected parties across exact EN/IT; all form0,IV31,Pluscap100; no general species/state equivalence','NARC185 handled as opaque32-byte token; native object allocates84B and native SDK FS internals are not executed','155 sparse code blocks/2771PC,76 data ranges; reset-PID counter additionally admits the independently verified125-byte nature table','Native entry r4-r7 are zero normally,nonzero caller-cookie guard verifies preservation; SDK volatile poison covers model dependence','Installed active0 unchanged; active1 only named RAM; no natural phone/Dojo,battle progress,SAVE,cold restart,device,timing or game repair claim'])


def main():
 import argparse,gzip
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','strategy-object','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  out=args.json;inputs=(args.rom,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o',args.strategy_object)
  need(not out.exists() and not out.is_symlink(),'--json must be a fresh nonexistent file');need(P.SOURCE not in out.resolve().parents and out.resolve()!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in out.resolve().parents,'output must be outside retained objects')
  for p in inputs:need(p.is_file() and p.resolve()!=out.resolve(),'input/output identity')
  result=analyze(args.rom,args.language,args.objects,args.strategy_object);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=16*1024*1024,'full report output budget');out.parent.mkdir(parents=True,exist_ok=True)
  with out.open('xb') as f:
   if out.suffix=='.gz':
    with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0) as g:g.write(payload)
   else:f.write(payload)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'4 complete constructors,4 counterproofs,SDK poison and caller-cookie guard verified; original seed/frees qualified; installed active0/natural unobserved')


if __name__=='__main__':main()
