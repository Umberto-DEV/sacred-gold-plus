#!/usr/bin/env python3
"""Attribute qualified trainers from native constructor entry through six Pokemon and return.

Private exact ROMs and retained project ELF objects only. SDK boundaries remain
explicit models; no copied Pokemon or post-entry constructor-frame bridge exists.
"""
from pathlib import Path
import importlib.util,mmap,json,struct,copy,gzip,sys,collections
s=importlib.util.spec_from_file_location('strategy_dependency',Path(__file__).with_name('attribuisci.py'));S=importlib.util.module_from_spec(s);s.loader.exec_module(S)
F,M,P,C,B=S.F,S.M,S.P,S.C,S.B;need=S.need
VARIANTS=('current','wrong_restore_seed','omit_prefix_free','wrong_last_move')
PROFILES={
 21:dict(trainer=21,class_id=67,gender_byte=1,maximum=21,anchor=23,species=(12,15,127,193,214,123),ivs=(24,24,24,24,24,31),overrides=(0,0,32,0,0,32),capsules=(0,0,0,0,0,12),delta=dict(offset=100,before=206,after=450),delta_pp=(40,20)),
 31:dict(trainer=31,class_id=72,gender_byte=0,maximum=29,anchor=31,species=(355,353,93,200,302,94),ivs=(31,31,31,31,31,31),overrides=(0,0,0,0,0,0),capsules=(0,0,0,0,0,14),delta=dict(offset=102,before=325,after=247),delta_pp=(20,15)),
 32:dict(trainer=32,class_id=73,gender_byte=0,maximum=44,anchor=48,species=(460,87,131,478,362,473),ivs=(31,31,31,31,31,31),overrides=(0,0,0,0,32,32),capsules=(0,0,0,0,0,24),delta=dict(offset=26,before=329,after=156),delta_pp=(5,10)),
 33:dict(trainer=33,class_id=74,gender_byte=1,maximum=40,anchor=44,species=(375,82,205,227,437,208),ivs=(31,31,31,31,31,31),overrides=(0,0,0,32,0,17),capsules=(0,0,0,0,0,11),deltas=(dict(offset=26,before=209,after=435),dict(offset=98,before=21,after=89),dict(offset=100,before=397,after=360)),delta_pps=((20,15),(20,10),(20,5))),
 34:dict(trainer=34,class_id=75,gender_byte=0,maximum=35,anchor=38,species=(57,286,106,107,297,62),ivs=(31,31,31,31,31,31),overrides=(32,0,32,32,0,0),capsules=(0,0,0,0,0,8),delta=dict(offset=8,before=99,after=280),delta_pp=(20,15)),
 244:dict(trainer=244,class_id=86,gender_byte=0,maximum=60,anchor=67,species=(130,445,142,149,6,149),ivs=(31,31,31,31,31,31),overrides=(0,0,0,0,0,0),capsules=(0,0,0,0,0,0),delta=dict(offset=10,before=63,after=127),delta_pp=(5,15)),
 245:dict(trainer=245,class_id=87,gender_byte=1,maximum=55,anchor=61,species=(124,337,282,80,338,178),ivs=(31,31,31,31,31,31),overrides=(0,0,0,0,0,0),capsules=(0,0,0,0,0,0),delta=dict(offset=102,before=384,after=94),delta_pp=(10,10)),
}


def profile_for(trainer):
 need(type(trainer)is int and trainer in PROFILES,'only qualified trainer profiles21/31/32/33/34/244/245 are admitted');return PROFILES[trainer]


def deltas_for(trainer):
 profile=profile_for(trainer)
 if trainer==33:need(len(profile['deltas'])==len(profile['delta_pps'])==3,'three complete source delta/PP pairs');pairs=tuple(zip(profile['deltas'],profile['delta_pps']))
 else:pairs=((profile['delta'],profile['delta_pp']),)
 need(len(pairs)==(3 if trainer==33 else 1) and len({delta['offset'] for delta,pp in pairs})==len(pairs),'finite distinct source deltas')
 for delta,pp in pairs:need(type(delta['offset'])is int and delta['offset']//18 in range(6) and delta['offset']%18 in (8,10,12,14) and len(pp)==2,'finite move-offset/PP domain')
 return pairs


def variants_for(trainer):
 profile_for(trainer);return VARIANTS if trainer!=33 else VARIANTS[:3]+('wrong_move_0','wrong_move_1','wrong_move_2')


def counter_delta(trainer,variant):
 if variant=='wrong_last_move' and trainer!=33:return deltas_for(trainer)[0][0]
 if trainer==33 and variant in ('wrong_move_0','wrong_move_1','wrong_move_2'):return deltas_for(trainer)[int(variant[-1])][0]
 return None


EXTRA_CODE_33=((0x2073AB0,0x2073AC4,'e8f6ccc6dcbb1828177c0d2b265ac03033499dbc5e4b729185a4dcff5f5c43df',9),(0x2073ACC,0x2073AD6,'f953adc99736cfcf1944feb09088338a7b797b9628b9b2039d102710eea615ad',5),(0x207000E,0x2070012,'512215349f12a0b3c1b5527cf3939457e9f8577aea66c2e6fbe4dee2a23f68da',2))


EXTRA_CODE_34=((0x2070006,0x207000A,'78e48386a8c4b5d6db45a5d1f5db617019b0d50a52ee01c8c9ccacdd129eb2f5',2),)
EXTRA_CODE_245=(EXTRA_CODE_33[2],)
REQUIRED_PROFILE_PCS={33:(0x2073AB0,0x2073AB2,0x2073AB6,0x2073AB8,0x2073ABA,0x2073ABC,0x2073ABE,0x2073AC0,0x2073AC2,0x2073ACC,0x2073ACE,0x2073AD0,0x2073AD2,0x2073AD4,0x207000E,0x2070010),34:(0x2070006,0x2070008),244:(0x2072A50,0x2072A52,0x2072A54),245:(0x207000E,0x2070010,0x2072A50,0x2072A52,0x2072A54)}


C_POOLS=((0x2073600,0x2073604),(0x2073672,0x207367A),(0x2073994,0x2073998),(0x20FFBD2,0x20FFBD4),(0x201FD40,0x201FD44),(0x201FD5C,0x201FD68))


def qualify(model,raw,language,objects,strategy_object,*,trainer=21):
 profile=profile_for(trainer);need(sys.flags.optimize==0,'run without Python -O: inherited bench assertions are required');recipe=F.attest_recipe_sources();module_code,module_proof=F.A.attest_objects(raw,model,objects);proof=M.attest_strategy_object(model,raw,strategy_object);S.qualify(model,proof);code,data=F.qualify(model,language)
 for a,shape in C.qualify_code(model,proof).items():need(a not in code or code[a]==shape,'constructor code mapping conflict');code[a]=shape
 profile_windows=EXTRA_CODE_33 if trainer==33 else EXTRA_CODE_34 if trainer==34 else EXTRA_CODE_245 if trainer==245 else ();base_code_pcs=set(code)
 if profile_windows:
  from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
  decoded_pcs=set()
  for start,end,digest,count in profile_windows:
   blob=C.bench_bytes(model,start,end-start);instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,start));need(P.sha(blob)==digest and sum(i.size for i in instructions)==end-start and len(instructions)==count,'finite-profile static native code/ISA drift')
   for instruction in instructions:need(instruction.address not in code,'finite-profile code admission overlap');code[instruction.address]=(instruction.size,True);decoded_pcs.add(instruction.address)
  need(decoded_pcs==set(REQUIRED_PROFILE_PCS[trainer])-base_code_pcs,'profile-specific static instruction starts')
 need(all(pc in code and code[pc][1] for pc in REQUIRED_PROFILE_PCS.get(trainer,())),'profile-specific required starts must be qualified Thumb code')
 getter=C.bench_bytes(model,0x201FD2C,12);need(P.sha(getter)=='8f303c720384de46eb4b512915a6cd3f65c0ca4cd09622ea94ec8e65323bf3db' and struct.unpack_from('<I',getter,8)[0]+4==0x21D15A8,'native GetSeed code/alignment/pool binding');code.update({a:(2,True) for a in (0x201FD2C,0x201FD2E,0x201FD30)});data+=list(C_POOLS)+[(0x201FD34,0x201FD38),(0x23D6600,0x23D6800),(0x23D8500,0x23D8600),(0x20FF639,0x20FF639+125),(0x20FF733,0x20FF7B3)]
 need(C.bench_bytes(model,0x20FF639,125)==bytes(0 if n//5==n%5 or j not in (n//5,n%5) else 1 if j==n//5 else 255 for n in range(25) for j in range(5)) and struct.unpack('<I',C.bench_bytes(model,0x206FE8C,4))[0]==0x20FF639,'full nature formula/pointer')
 need(struct.unpack('<I',C.bench_bytes(model,0x2072630,4))[0]==0x20FF733 and C.bench_bytes(model,0x20FF733,128)==bytes(32*B.PERMUTATIONS[i%24].index(block) for i in range(32) for block in range(4)),'full32-row substructure permutation formula/pointer')
 class_address=0x20FFB90+profile['class_id'];need(C.bench_bytes(model,class_address,1)==bytes([profile['gender_byte']]) and struct.unpack('<I',C.bench_bytes(model,0x2073600,4))[0]==0x20FFB90,'profile class-table byte/pointer')
 if not any(a<=class_address and class_address+1<=b for a,b in data):data.append((class_address,class_address+1))
 for row in proof['mapping_ranges']:
  if row['kind']=='$d':data.append((int(row['start'],16),int(row['end'],16)))
 for start,end in data:need(all(a+n<=start or a>=end for a,(n,_) in code.items()),'constructor readonly/code overlap')
 view=P.G.S.SHARED.gifts_audit.Arm9View(raw);locations=[]
 for a,n in ((0x201FD2C,12),(0x20FF639,125),(0x20FF733,128),(0x2072630,4),(0x23D6000,2048),(0x23D8100,256),(0x23D8500,256),(class_address,1))+tuple((a,b-a) for a,b,_,_ in profile_windows):
  payload=view.read(a,n);need(payload==C.bench_bytes(model,a,n),'constructor independent raw ARM9 readback');locations.append(dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=P.sha(payload)))
 return code,data,module_code,dict(recipe_sources=recipe,strategy_elf=proof,module=module_proof,locations=locations,qualified_code_pcs=len(code),readonly_ranges=len(data),compiler_invoked=False)


def resources(model,raw,language,*,trainer=21):
 profile=profile_for(trainer);canonical=S.resources(raw,model);record=canonical['records'][str(trainer)];header=bytes.fromhex(record['header']);archives={};receipts={}
 for narc in (2,3,11,33,185):archives[narc],receipts[str(narc)]=P.RAW.raw_archive(raw,B.narc_path(narc))
 party=bytes.fromhex(record['before']);species=sorted(set(struct.unpack_from('<H',party,18*i+4)[0]&1023 for i in range(6)));bench=P.Adapter(model,raw,language);table=C.bench_bytes(model,0x23D8500,256);rows=[struct.unpack_from('<BBHHH4HH',party,18*i) for i in range(6)];maximum=max(row[2] for row in rows);need(header[0]==3 and header[3]==6 and header[1]==profile['class_id'] and maximum==profile['maximum'] and table[maximum]==profile['anchor'] and tuple(row[3]&1023 for row in rows)==profile['species'] and tuple(row[0]*31//255 for row in rows)==profile['ivs'] and tuple(row[1] for row in rows)==profile['overrides'] and tuple(row[-1] for row in rows)==profile['capsules'] and record['spec']['moves']==[delta for delta,pp in deltas_for(trainer)],'authenticated finite trainer profile/header/roster/level/capsule/delta')
 for delta,pp in deltas_for(trainer):need(tuple(archives[11][delta[key]][6] for key in ('before','after'))==pp,'profile raw PP before/after identity')
 return dict(trainer=trainer,profile=profile,maximum=maximum,canonical=canonical,record=record,header=header,party=party,archives=archives,receipts=receipts,personal={str(x):bytes(archives[2][x]) for x in species},names={str(x):bench.species_name(x) for x in species},class_id=header[1],gender_byte=C.bench_bytes(model,0x20FFB90+header[1],1)[0],table=table,language=C.bench_bytes(model,0x20F5670,1)[0],capsule_binding=F.capsule_binding(model))


def expected(data,plus,*,strategy=True):
 party=bytes.fromhex(data['record']['after']) if plus and strategy else data['party'];maximum=max(struct.unpack_from('<H',party,18*i+2)[0] for i in range(6));low=0x78 if data['gender_byte']==1 else 0x88;records=[]
 for slot in range(6):
  difficulty,override,base,packed,item,*rest=struct.unpack_from('<BBHHH4HH',party,18*slot);species=packed&1023;form=packed>>10;moves=rest[:4];capsule=rest[4];need(form==0 and (override&15==0 or data['trainer']==33 and slot==5 and override==17),'finite form0/gender override domain');iv=difficulty*31//255;personal=data['personal'][str(species)]
  if override&15:need(personal[16]==127,'profile33 raw Steelix gender ratio');low=personal[16]+2
  if override>>4==1:low&=~1
  elif override>>4==2:low|=1
  initial=difficulty+base+species+data['trainer'];state=initial;draws=[]
  for _ in range(data['class_id']):state=(state*0x41C64E6D+0x6073)&0xFFFFFFFF;draws.append(state)
  pid=((state>>16)<<8)+low;ot=[]
  while True:
   pair=[]
   for _ in range(2):state=(state*0x41C64E6D+0x6073)&0xFFFFFFFF;ot.append(state);pair.append(state>>16)
   if pair[0]^pair[1]^(pid&65535)^(pid>>16)>=8:break
   need(len(ot)<64,'finite anti-shiny oracle')
  level=base if not plus else max(base,min(100,data['table'][maximum]-(maximum-base)));nature=pid%25;stats=[]
  for index,b in enumerate(personal[1:6]):
   value=(2*b+iv)*level//100+5
   if nature//5!=nature%5 and index in (nature//5,nature%5):value=((value*(110 if index==nature//5 else 90))&65535)//100
   stats.append(value)
  hp=(2*personal[0]+iv)*level//100+level+10;ratio=personal[16];gender=2 if ratio==255 else 1 if ratio==254 else 0 if ratio==0 else int((pid&255)<ratio);name=data['names'][str(species)];seals=bytes(24) if capsule==0 else bytes(data['archives'][185][0])[(capsule-1)*24:capsule*24]
  fields=dict(flags=0,pid=pid,species=species,item=item,friendship=0 if 218 in moves else 255,ability=personal[23] if personal[23] and pid&1 else personal[22],evs=[0]*6,moves=moves,pp=[data['archives'][11][x][6] for x in moves],pp_ups=[0]*4,ivs=[iv]*6,gender=gender,form=form,nature=nature,level=level,hp=hp,max_hp=hp,status=0,ball_capsule=int(capsule!=0),nickname=name+[0]*(11-len(name)),otid=pair[0]|(pair[1]<<16),exp=struct.unpack_from('<I',data['archives'][3][personal[19]],4*level)[0],language=data['language'],stats=stats,capsule_hex=seals.hex())
  records.append(dict(slot=slot,fields=fields,pid_gender=low,class_seed=initial,class_draws=draws,ot_draws=ot,iv=iv,base=base,capsule=capsule))
 return records


def bench_image(model,raw,language,module_code,*,strategy=True):
 bench=P.Adapter(model,raw,language);bench.module_code=module_code;shadows=[]
 if not strategy:
  from sgp13 import teams
  segments=[]
  for base,blob in bench.segments:
   output=bytearray(blob)
   for site in teams.SITES:
    if base<=site and site+4<=base+len(blob):
     before=bytes(output[site-base:site-base+4]);need(P.G.S.SHARED.branch(before,site,'bl')==0x23D6228,'old-recipe RAM shadow current BL preimage');after=teams.bl_thumb(site,teams.ORIGINAL_HOOK);need(P.G.S.SHARED.branch(after,site,'bl')==0x23D8194,'old-recipe RAM shadow target');output[site-base:site-base+4]=after;shadows.append(dict(ram=hex(site),bytes=4,before_sha256=P.sha(before),after_sha256=P.sha(after),target='0x23d8194',reason='named virtual old-hook recipe baseline; exact input ROM unchanged'))
   segments.append((base,bytes(output)))
  need(len(shadows)==4,'four old-recipe virtual hook sites');bench.segments=segments
 return bench,shadows


class Actual(F.Full):
 latest=None
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);Actual.latest=self;self.body=False;self.pending_native=[];self.extra_reads=set();self.prefix_transition=None;self.additions_all=[];self.api_calls=[];self.extra_pending=[];self.extra_calls=[];self.buffer_writes=[];self.buffer_reads=[];self.call_entry=None;self.cookies=False;self.game_variant='current';self.game_shadows=[];self.last_move_changed=False;self.buffer_before_free=None
 def factory(self,*args):
  u=super().factory(*args);original=u.emu_start
  def tracked(begin,end,*positional,**keywords):
   entry=self.regs();original(begin,end,*positional,**keywords);self.api_calls.append(dict(begin=hex(begin),requested_end=hex(end),actual_end=hex(u.reg_read(P.UC_ARM_REG_PC)),entry=entry,end=self.regs(),ram_sha256=P.sha(bytes(u.mem_read(0x2000000,0x400000)))))
  u.emu_start=tracked;return u
 def step(self,u,a,n,unused):
  if not self.body:
   if a==B.ENTRY:
    original=self.regs()
    if self.cookies:
     need(original[4:8]==[0]*4,'caller-cookie initial context')
     for i,value in enumerate(F.ENTRY_COOKIES,4):u.reg_write(B.R[i],value)
    self.call_entry=dict(pc=hex(a),before=original,actual=self.regs(),cookie_fixture=self.cookies)
   if a==B.SEAM_RESUME:
    self.resume=dict(r=[self.reg(i) for i in range(13)],sp=self.sp(),flags=u.reg_read(P.UC_ARM_REG_CPSR)>>28);state=self.regs();ram=P.sha(bytes(u.mem_read(0x2000000,0x400000)));self.prefix_transition=dict(pc=hex(a),regs=state,ram_sha256=ram,buffer_hex=bytes(u.mem_read(B.ARENA,108)).hex(),seed=self.word(0x21D15A8),prefix_instructions=self.instructions,registry=bytes(u.mem_read(B.REGISTRY,64)).hex());self.body=self.mon=self.full=True;self.stop_after_add=False;self.instruction_limit=3000000;self.live.update(dict(self.allocs));self.next_arena=B.ARENA+sum((size+23)&~7 for p,size in self.allocs);self.prefix_transition['observer_neutral']=state==self.regs() and ram==P.sha(bytes(u.mem_read(0x2000000,0x400000)));need(self.prefix_transition['observer_neutral'],'prefix phase observer changed registers/RAM')
   else:return P.Audit.step(self,u,a,n,unused)
  while self.extra_pending and a==self.extra_pending[-1]['return_pc']:
   event=self.extra_pending.pop();event.update(result=[self.reg(i) for i in range(4)],return_sp=self.sp(),return_saved=[self.reg(i) for i in range(4,12)],after_seed=self.word(0x21D15A8),nzcv=u.reg_read(P.UC_ARM_REG_CPSR)>>28);need(event['sp']==event['return_sp'] and event['saved']==event['return_saved'],'native constructor extra helper return ABI');self.extra_calls.append(event)
  lr=u.reg_read(C.UC_ARM_REG_LR)
  if a in (0x20735F8,0x23D6228,0x23D61C4,0x23D602C,0x23D8134,0x23D8100) or(a==0x20F2998 and lr==0x20739F7) or(self.trainer==33 and a==0x206FBC4 and lr==0x2073AB7):
   self.extra_pending.append(dict(entry=hex(a),lr=hex(lr),return_pc=lr&~1,args=[self.reg(i) for i in range(4)],stack0=self.word(self.sp()),sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],before_seed=self.word(0x21D15A8),slot=self.word(B.PARTIES+0x1000+4)))
  if a==0x2073A32 and counter_delta(self.trainer,self.game_variant) is not None:
   delta=counter_delta(self.trainer,self.game_variant);delta_slot=delta['offset']//18;move_slot=(delta['offset']%18-8)//2
   if self.word(B.PARTIES+0x1000+4)==delta_slot and self.reg(2)==move_slot:
    need(not self.last_move_changed and self.reg(1)==delta['after'],'native selected move counter preimage');self.last_move_changed=True;u.reg_write(B.R[1],delta['before']);self.game_shadows.append(dict(kind='register',pc=hex(a),register='r1',before=delta['after'],after=delta['before'],reason='selected native constructor move slot only'))
  if a==0x2073A84:self.buffer_before_free=bytes(u.mem_read(B.ARENA,108)).hex()
  if self.trainer in (31,32,34) and a==0x200782C:
   self.instructions+=1;need(self.instructions<=self.instruction_limit and self.sp()%8==0 and self.pending_service is None,'finite-profile capsule SDK budget/entry ABI');args=[self.reg(i) for i in range(4)];handle,member,offset,size=args;dest=self.word(self.sp());capsule=profile_for(self.trainer)['capsules'][-1];need(self.handles.get(handle)==185 and member==0 and offset==(capsule-1)*24 and size==24 and lr==0x2072A77 and dest==self.sp()+8,'finite-profile exact capsule slice ABI');payload=self.bench.archives.files('a/1/8/5')[0];need(len(payload)==3072 and offset+size<=len(payload) and B.STACK_TOP-512<=dest and dest+size<=B.STACK_TOP,'finite-profile capsule raw member/destination bound');event=dict(name='NARC_ReadFromMember',args=args,sp=self.sp(),saved=[self.reg(i) for i in range(4,12)],return_pc=lr&~1,destination=dest,bytes=size,output_pointer=dest,output_sha256=P.sha(payload[offset:offset+size]));self.mon_models.append(event);self.pending_service=event;return
  F.Full.step(self,u,a,n,unused)
  if a==0x2073A68:self.additions_all.append(dict(count=self.word(B.PARTIES+0x1000+4),sp=self.sp(),mon_hex=bytes(u.mem_read(B.ARENA+128,236)).hex(),party_slot_sha256=P.sha(bytes(u.mem_read(B.PARTIES+0x1000+8+236*(self.word(B.PARTIES+0x1000+4)-1),236)))))
 def write(self,u,access,a,n,value,unused):
  (F.Full.write if self.body else P.Audit.write)(self,u,access,a,n,value,unused)
  pc=u.reg_read(P.UC_ARM_REG_PC)
  if self.trainer==33 and pc in (0x2073AB6,0x2073AC0,0x2073AD2):
   need(self.pid_pending is not None and a==self.pid_pending['args'][3] and n==4,'profile33 ratio/PID store destination');self.pid_pending.setdefault('ratio_stores',[]).append(dict(pc=hex(pc),address=a,bytes=n,before=self.word(a),value=value,sp=self.sp()))
  if self.body and B.ARENA<=a and a+n<=B.ARENA+108:
   need(u.reg_read(P.UC_ARM_REG_PC)==0x23D619A and n==1,'only declared strategy output may write raw party buffer');self.buffer_writes.append(dict(pc='0x23d619a',offset=a-B.ARENA,bytes=n,value=value))
 def read(self,u,access,a,n,value,unused):
  (F.Full.read if self.body else P.Audit.read)(self,u,access,a,n,value,unused)
  if self.body and B.ARENA<=a and a+n<=B.ARENA+108:self.buffer_reads.append(dict(pc=hex(u.reg_read(P.UC_ARM_REG_PC)),offset=a-B.ARENA,bytes=n,value=int.from_bytes(u.mem_read(a,n),'little')))


def run_case(model,raw,language,qualified,plus=1,seed=0x12345678,variant='current',poison=False,cookies=False,strategy=True,*,trainer=21):
 profile_for(trainer);need(type(plus)is int and plus in (0,1) and seed in (0x12345678,0x12345679) and variant in variants_for(trainer) and all(type(x)is bool for x in (poison,cookies,strategy)),'native21 fixture domain');need(variant=='current' or plus==1 and strategy and not poison and not cookies,'native21 counter domain');code,data,module_code=qualified;bench,recipe_shadows=bench_image(model,raw,language,module_code,strategy=strategy);audit=Actual(bench,trainer,plus=plus,seed=seed);audit.mon_allowed=code;audit.mon_data=data;audit.poison=poison;audit.cookies=cookies;audit.game_variant=variant;audit.full_variant=variant
 with P.patch.object(B,'Uc',audit.factory),P.patch.object(B,'GF_ASSERT',0x23BE100),P.patch.object(B,'WFC_HOOK',0x23BE104):result=bench.run(trainer,plus=plus,seed=seed,max_instructions=3000000)
 need(audit.prefix_transition is not None and not audit.pending_native and audit.pending_service is None and not audit.extra_pending,'actual native21 helper closure');need(len(audit.api_calls)==3 and [x['begin'] for x in audit.api_calls]==['0x201fd39','0x2073605','0x201fd2d'] and all(x['actual_end']==hex(B.SENTINEL) for x in audit.api_calls),'native constructor entry/full return and separate seed getter API calls')
 ignored=[(B.STACK_TOP-512,B.STACK_TOP),(B.REGISTRY,B.REGISTRY+64),(0x23DA044,0x23DA048),(P.MODULE,P.MODULE+2048),(B.PARTIES+0x1000,B.PARTIES+0x1000+0x5B0),(B.ARENA-8,audit.next_arena),(0x21D15A8,0x21D15AC),(0x21D421C,0x21D421C+404),(0x23D8708,0x23D870C)];frozen=P.masked_hash(audit.before,ignored);need(frozen==P.masked_hash(result['ram'],ignored),'native21 unrelated initialized RAM changed');canaries=all(bytes(audit.uc.mem_read(p-8,8))==b'\xA5'*8 and bytes(audit.uc.mem_read(p+size,8))==b'\xA5'*8 for p,size in audit.allocs+audit.alloc_canaries)
 return dict(trainer=trainer,language=language,plus=plus,seed=seed,variant=variant,poison=poison,cookies=cookies,strategy=strategy,recipe_shadows=recipe_shadows,game_shadows=audit.game_shadows+audit.full_shadows,call_entry=audit.call_entry,api_calls=audit.api_calls,prefix_transition=audit.prefix_transition,seam=audit.seam,reader_calls=audit.reader,unloads=audit.unloads,prefix_models=audit.models,models=audit.mon_models,mon_hex=[x.hex() for x in result['mons']],decoded=[M.decode(x) for x in result['mons']],end=result['end'],seed_after=result['seed_after'],header=list(result['party_header']),native_calls=audit.native_calls,creation_inputs=audit.creation_inputs,pid_overrides=audit.pid_overrides,seed_calls=audit.restores,additions=audit.additions_all,capsule_calls=audit.capsule_calls,post_form_calls=audit.post_form_calls,extra_calls=audit.extra_calls,buffer_writes=audit.buffer_writes,buffer_reads=audit.buffer_reads,buffer_before_free=audit.buffer_before_free,globals=audit.full_globals,instructions=audit.instructions,max_stack=audit.max_stack,live=audit.live,handles=audit.handles,overlay=result['overlay'],stack_canary=result['stack_canary'],canaries=canaries,party_extra_hex=bytes(audit.uc.mem_read(B.PARTIES+0x1000+0x590,32)).hex(),plus_hits=audit.word(0x23D8708),critical=audit.critical,code=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(audit.mon_code)],unrelated_ram_unchanged=True,unrelated_ram_sha256=frozen,events=result['events'])


def require_case(r,data):
 need(r.get('trainer',21)==data['trainer'],'native report profile identity');need(r['variant']=='current' and not r['game_shadows'] and r['plus'] in (0,1) and r['seed'] in (0x12345678,0x12345679),'native21 accepted fixture domain');plus,seed,strategy=r['plus'],r['seed'],r['strategy'];want=expected(data,plus,strategy=strategy);party=bytes.fromhex(data['record']['after']) if plus and strategy else data['party'];need(r['header']==[6,6] and len(r['mon_hex'])==len(r['decoded'])==6,'native21 complete party')
 for raw_hex,reported,record in zip(r['mon_hex'],r['decoded'],want):
  raw=bytes.fromhex(raw_hex);actual=M.decode(raw);need(actual==reported and actual['checksum_ok'],'independently decoded21 record/checksum');actual['capsule_hex']=B._decrypt(raw[136:],struct.unpack_from('<I',raw)[0])[76:100].hex();need(all(actual[key]==value for key,value in record['fields'].items()),'native21 source/IV/PID/OTID/level/stats/moves/PP/capsule '+str(record['slot']))
 need(r['seed_after']==seed and r['plus_hits']==6 and r['stack_canary'] and r['canaries'] and not r['live'] and not r['handles'] and r['party_extra_hex']=='00'*32 and r['unrelated_ram_unchanged'],'native21 final seed/lifetime/extra/freeze');need(r['reader_calls']==r['unloads']==1 and r['prefix_transition']['buffer_hex']==data['record']['before'] and r['prefix_transition']['seed']==seed and r['prefix_transition']['observer_neutral'] and r['prefix_transition']['pc']=='0x207363e','native21 original buffer and neutral straight-line phase transition')
 need(r['buffer_before_free']==party.hex(),'native21 actual complete buffer before free');stores=r['buffer_writes'];need(stores==([dict(pc='0x23d619a',offset=i,bytes=1,value=x) for i,x in enumerate(party)] if plus and strategy else []),'native21 once-only exact108 byte copy')
 if strategy:need(r['recipe_shadows']==[],'installed strategy code must be unchanged')
 else:
  from sgp13 import teams
  need(r['recipe_shadows']==[dict(ram=hex(site),bytes=4,before_sha256=P.sha(teams.bl_thumb(site,0x23D6228)),after_sha256=P.sha(teams.bl_thumb(site,0x23D8194)),target='0x23d8194',reason='named virtual old-hook recipe baseline; exact input ROM unchanged') for site in teams.SITES],'four authenticated old-recipe RAM baseline sites')
 api=r['api_calls'];need(len(api)==3 and [x['begin'] for x in api]==['0x201fd39','0x2073605','0x201fd2d'] and all(x['actual_end']==x['requested_end']==hex(B.SENTINEL) for x in api),'constructor single entry/full return and separate observing getter');need(api[1]['end'][:13]==r['end']['r'] and api[1]['end'][13]==r['end']['sp']==B.STACK_TOP and api[2]['end'][0]==seed,'constructor return snapshot must precede getter');need(api[1]['entry'][:3]==[B.SETUP,1,11] and r['call_entry']['pc']==hex(B.ENTRY) and r['call_entry']['actual'][:3]==[B.SETUP,1,11] and r['call_entry']['actual'][13]==B.STACK_TOP and r['call_entry']['cookie_fixture']==r['cookies'],'public native constructor entry context');need(r['end']['r'][4:8]==(list(F.ENTRY_COOKIES) if r['cookies'] else [0]*4) and r['end']['r'][8:12]==[B.SENTINEL_REGS[i] for i in range(8,12)],'native21 caller saved registers')
 before=list(api[1]['entry']);actual=list(before)
 if r['cookies']:actual[4:8]=list(F.ENTRY_COOKIES)
 need(r['call_entry']['before']==before and r['call_entry']['actual']==actual,'only declared caller-cookie initialization at actual API entry');transition=r['prefix_transition'];need(transition['regs'][13]==r['seam']['sp']==B.STACK_TOP-152 and r['seam']['saved_seed']==seed and transition['regs'][0]==B.LOADER_RESULT and transition['regs'][1:3]==r['seam']['r'][1:3] and transition['regs'][4:12]==r['seam']['r'][4:12],'native21 reader/seam ABI before first real Mon')
 need([x['name'] for x in r['prefix_models']]==['Heap_Alloc','Heap_Alloc']+['0x20d88c0']*4+['0x20d8a48','0x20d8b6c','ReadWholeNarcMemberByIdPair','0x20d88c0','0x20d8db4'] and r['prefix_models'][0]['args'][:2]==[11,108] and r['prefix_models'][1]['args'][:2]==[11,236] and r['prefix_models'][8]['args'][:3]==[B.ARENA,56,data['trainer']],'native21 original prefix allocation/raw-reader service chain')
 need(r['critical']==[dict(pc=hex(pc),address=hex(address),bytes=4,value=value) for pc,address,value in ((0x200702E,B.REGISTRY+4,1),(0x2007030,B.REGISTRY,126),(0x23DA3E2,0x23DA044,1),(0x2006F78,B.REGISTRY+4,0))] and [list(x) for x in r['overlay']['registry']]==[[126,0]]+[[0,0]]*7,'native21 module load/unload registry and WFC lifetime')
 need(len(r['post_form_calls'])==24,'native21 complete owned post-form chain')
 for index,record in enumerate(want):
  for event,entry,lr in zip(r['post_form_calls'][4*index:4*index+4],('0x20722d4','0x206e250','0x2071754','0x206ec40'),('0x2073aed','0x2073af3','0x2073afb','0x2073b11')):need(event['entry']==entry and event['lr']==lr and event['args'][0]==B.ARENA+128,'native21 exact post-form helper/caller')
  has=r['post_form_calls'][4*index+2];setter=r['post_form_calls'][4*index+3];need(has['args'][1]==218 and has['result'][0]==int(218 in record['fields']['moves']) and setter['args'][1]==9 and setter['value_byte']==record['fields']['friendship'],'native21 post-form move/friendship source semantics')
 capsule_records=[record for record in want if record['capsule']]
 if not capsule_records:need(r['capsule_calls']==[] and not any(event['name'] in ('NARC_New','NARC_ReadFromMember','NARC_Delete') for event in r['models']),'zero-capsule profile must execute no capsule services/setters')
 else:need(len(capsule_records)==1 and capsule_records[0]['slot']==5 and len(r['capsule_calls'])==2 and [x['lr'] for x in r['capsule_calls']]==['0x2072a81','0x2072a8b'] and [x['args'][1] for x in r['capsule_calls']]==[162,171] and r['capsule_calls'][0]['value_hex']=='01000000' and r['capsule_calls'][1]['value_hex']==want[-1]['fields']['capsule_hex'],'native capsule setters/data')
 need(len(r['creation_inputs'])==len(r['pid_overrides'])==len(r['additions'])==6 and len(r['seed_calls'])==7,'native21 six creations/PID/copies and7setters')
 for record,create,pid,addition in zip(want,r['creation_inputs'],r['pid_overrides'],r['additions']):
  fields=record['fields'];slot=record['slot'];need(create['args']==[B.ARENA+128,fields['species'],fields['level'],record['iv']] and create['stack']==[1,fields['pid'],2,0] and create['lr']=='0x2073a17' and create['sp']==B.STACK_TOP-152,'actual21 CreateMon arguments')
  need(pid['before_gender']==((0x78 if data['gender_byte']==1 else 0x88) if slot==0 else want[slot-1]['pid_gender']) and pid['after_gender']==record['pid_gender'] and pid['args'][3]==B.STACK_TOP-152+0x7C,'native21 persistent PID override state')
  if data['trainer']==33 and slot==5:need(pid['ratio_stores']==[dict(pc=hex(pc),address=B.STACK_TOP-28,bytes=4,before=before,value=value,sp=B.STACK_TOP-168) for pc,before,value in ((0x2073AB6,0x79,127),(0x2073AC0,127,129),(0x2073AD2,129,128))],'profile33 native ratio/add2/ability1 store sequence')
  need(addition==dict(count=slot+1,sp=B.STACK_TOP-152,mon_hex=r['mon_hex'][slot],party_slot_sha256=P.sha(bytes.fromhex(r['mon_hex'][slot]))),'native21 copied236-byte slot/count/return')
 for event,value in zip(r['seed_calls'],[x['class_seed'] for x in want]+[seed]):need(event['args'][0]==event['result'][0]==event['after_seed']==value,'native21 exact setters and original restore')
 need([x['lr'] for x in r['seed_calls']]==['0x20739c3']*6+['0x2073a95'],'native21 actual reseed/final restoration callers')
 for event in r['native_calls']+r['post_form_calls']+r['capsule_calls']+r['pid_overrides']+r['seed_calls']+r['extra_calls']:need(event['sp']==event['return_sp'] and event['saved']==event['return_saved'] and event['return_pc']==int(event['lr'],16)&~1,'all native21 helper return ABI')
 # Validate every class RNG draw and nested OTID draw in execution order.
 calls=r['native_calls'];at=0
 for record in want:
  state=record['class_seed']
  for after in record['class_draws']:
   event=calls[at];at+=1;need(event['entry']=='0x201fd44' and event['lr']=='0x20739d3' and event['before_seed']==state and event['after_seed']==after and event['result'][0]==after>>16,'native21 full class RNG chain');state=after
  fields=record['fields'];event=calls[at];at+=1;need(event['entry']=='0x206de38' and event['args']==[B.ARENA+128,fields['species'],fields['level'],record['iv']] and event['lr']=='0x2073a17','native21 actual CreateMon entry chain')
  for draw,after in enumerate(record['ot_draws']):
   event=calls[at];at+=1;need(event['entry']=='0x201fd44' and event['lr']==('0x206df13' if draw%2==0 else '0x206df19') and event['before_seed']==state and event['after_seed']==after and event['result'][0]==after>>16,'native21 exact anti-shiny OTID chain');state=after
  event=calls[at];at+=1;need(event['entry']=='0x206ec40' and event['args'][:3]==[B.ARENA+128,6,B.ARENA+18*record['slot']+6] and event['lr']=='0x2073a23','native21 held item input')
  for move_slot,move in enumerate(fields['moves']):
   event=calls[at];at+=1;need(event['entry']=='0x20714e8' and event['args'][:3]==[B.ARENA+128,move,move_slot] and event['lr']=='0x2073a37','native21 exact four moves/slots')
  for entry,lr in (('0x2072a44','0x2073a4f'),('0x206ec40','0x2073a59'),('0x2073ae4','0x2073a5f'),('0x2074524','0x2073a69')):
   event=calls[at];at+=1;need(event['entry']==entry and event['lr']==lr,'native21 capsule/form/owned postform/PartyAdd chain')
   if entry=='0x2072a44':need(event['args'][:3]==[record['capsule'],B.ARENA+128,11] and event['result'][0]==int(record['capsule']!=0),'native capsule ID/heap/BOOL result')
   if entry=='0x206ec40':need(event['args'][:2]==[B.ARENA+128,112],'native21 form attribute')
   if entry=='0x2074524':need(event['args'][:2]==[B.PARTIES+0x1000,B.ARENA+128] and event['result'][0]==1,'native21 actual PartyAdd BOOL')
 need(at==len(calls),'native21 complete call ordering/no extra calls')
 # The independent extra observer binds core, native level calculation and IV math.
 extra=r['extra_calls'];position=0;event=extra[position];position+=1;need(event['entry']=='0x20735f8' and event['args'][0]==data['class_id'] and event['result'][0]==data['gender_byte'] and event['return_pc']==0x2073650,'native21 class table consumer')
 for record in want:
  slot=record['slot']
  if data['trainer']==33 and slot==5:
   event=extra[position];position+=1;need(event['entry']=='0x206fbc4' and event['args'][:3]==[208,0,18] and event['result'][0]==data['personal']['208'][16]==127 and event['return_pc']==0x2073AB6 and event['slot']==5 and event['sp']==B.STACK_TOP-168,'profile33 native raw gender-ratio getter/ABI')
  event=extra[position];position+=1;need(event['entry']=='0x20f2998' and event['args'][:2]==[data['party'][18*slot]*31,255] and event['result'][:2]==list(divmod(data['party'][18*slot]*31,255)) and event['return_pc']==0x20739F6,'native21 actual signed IV division')
  if strategy:
   for entry in ('0x23d602c','0x23d61c4'):
    event=extra[position];position+=1;need(event['entry']==entry and event['slot']==slot,'native21 strategy completion ordering')
    if entry=='0x23d602c':need(event['args']==[B.ARENA,data['trainer'],0x603,plus] and event['stack0']==0x23D6600 and event['result'][0]==(len(deltas_for(data['trainer'])) if plus and slot==0 else 0) and event['return_pc']==0x23D621C,'native21 core/source/config/once-only result')
    else:need(event['args'][:3]==[B.SETUP,52,B.ARENA] and event['return_pc']==0x23D6234,'native21 wrapper arguments/caller')
  if plus:
   event=extra[position];position+=1;need(event['entry']=='0x23d8100' and event['args'][:3]==[B.ARENA,18,6] and event['result'][0]==data['maximum'] and event['return_pc']==0x23D816A,'native21 real six-opponent max')
  event=extra[position];position+=1;need(event['entry']=='0x23d8134' and event['args'][:3]==[record['base'],B.ARENA,0x603] and event['result'][0]==record['fields']['level'] and event['return_pc']==0x23D81AC,'native21 inherited level/body/table result')
  if strategy:
   event=extra[position];position+=1;need(event['entry']=='0x23d6228' and event['result']==[B.ARENA+128,record['fields']['species'],record['fields']['level'],record['iv']<<24] and event['return_pc']==0x2073A10 and event['nzcv']==0,'native21 strategy hook actual live ABI/flags')
 need(position==len(extra),'native21 no missing/extra observed helper')
 move_reads=[x for x in r['buffer_reads'] if x['pc']=='0x2073a2c'];need(move_reads==[dict(pc='0x2073a2c',offset=18*i+8+2*j,bytes=2,value=record['fields']['moves'][j]) for i,record in enumerate(want) for j in range(4)],'native21 all24 actual move loads')
 # Reconstruct the SDK lifetime from independent raw member bytes,not reported live maps.
 live={B.ARENA:108,B.ARENA+128:236};handles={}
 for event in r['models']:
  name=event['name'];args=event['args'];need(event['sp']==event['return_sp'] and event['saved']==event['return_saved'] and 'result'in event,'native21 SDK return ABI')
  if name in ('Heap_Alloc','Heap_AllocAtEnd','GetSpeciesName'):
   pointer=event['result'];need(pointer==event['pointer'] and pointer not in live and pointer not in handles,'native21 unique allocation')
   image=B.pack_species_string(data['names'][str(args[0])]) if name=='GetSpeciesName' else bytes(args[1]);need(event['bytes']==len(image) and event['output_sha256']==P.sha(image),'native21 model allocation/string image');live[pointer]=len(image)
  elif name=='Heap_Free':need(args[0] in live and live.pop(args[0])==event['bytes'],'native21 single exact free')
  elif name=='ReadWholeNarcMemberByIdPair':
   need(args[1] in data['archives'],'native21 raw member domain');payload=data['archives'][args[1]][args[2]];need(event['bytes']==len(payload) and event['sha256']==event['output_sha256']==P.sha(payload),'native21 independently read raw member')
  elif name=='NARC_New':need(args[:2]==[185,11] and event['result'] not in handles and not handles,'native21 opaque capsule handle');handles[event['result']]=185
  elif name=='NARC_ReadFromMember':need(handles.get(args[0])==185 and args[1:]==[0,(want[-1]['capsule']-1)*24,24] and event['output_sha256']==P.sha(data['archives'][185][0][(want[-1]['capsule']-1)*24:want[-1]['capsule']*24]),'native21 raw capsule12 slice')
  elif name=='NARC_Delete':need(args[0] in handles,'native21 live capsule delete');handles.pop(args[0])
  else:raise ValueError('native21 unknown SDK model event')
 need(not live and not handles,'native21 reconstructed closed lifetime');need(0<r['instructions']<=3000000 and 0<r['max_stack']<=512,'native21 instruction/stack bounds')
 pcs={int(x['ram'],16) for x in r['code']};need({0x207363E,0x2073A0C,0x206DE38,0x2073A32,0x2074524,0x2073A90,0x2073A96,0x201FD2C}<=pcs and (0x23D602C in pcs)==strategy,'native21 first body/strategy/last return/getter instruction coverage');need(set(REQUIRED_PROFILE_PCS.get(data['trainer'],()))<=pcs,'profile-specific executed instruction coverage');return True


def compare_strategy_delta(current,baseline):
 need(len(current['mon_hex'])==len(baseline['mon_hex'])==6 and all(len(bytes.fromhex(packet))==236 for case in (current,baseline) for packet in case['mon_hex']),'strategy comparison requires all six complete packets')
 need(current.get('trainer',21)==baseline.get('trainer',21),'strategy comparison trainer identity');deltas=deltas_for(current.get('trainer',21));need(current['strategy'] and not baseline['strategy'] and current['plus']==baseline['plus'] and current['seed']==baseline['seed'],'strategy contribution comparison domain');need(current['seed_after']==baseline['seed_after'] and current['end']['r'][4:12]==baseline['end']['r'][4:12] and current['end']['sp']==baseline['end']['sp'],'strategy contribution RNG/caller ABI')
 for slot,(left_hex,right_hex) in enumerate(zip(current['mon_hex'],baseline['mon_hex'])):
  left,right=bytes.fromhex(left_hex),bytes.fromhex(right_hex);edits=[(delta,pp) for delta,pp in deltas if delta['offset']//18==slot]
  if not current['plus'] or not edits:need(left==right,'strategy changes no other complete native Mon');continue
  need(left[:6]==right[:6] and left[136:]==right[136:],'strategy leaves identity/header/whole100-byte party tail unchanged');pid=struct.unpack_from('<I',left)[0];order=B.PERMUTATIONS[((pid>>13)&31)%24];a=B._decrypt(left[8:136],struct.unpack_from('<H',left,6)[0]);b=bytearray(B._decrypt(right[8:136],struct.unpack_from('<H',right,6)[0]));offset=32*order.index(1)
  for delta,pp in edits:
   move_slot=(delta['offset']%18-8)//2;need(struct.unpack_from('<H',b,offset+2*move_slot)[0]==delta['before'] and b[offset+8+move_slot]==pp[0] and current['decoded'][slot]['pp'][move_slot]==pp[1],'old-hook native move/PP preimage and exact source successor');struct.pack_into('<H',b,offset+2*move_slot,delta['after']);b[offset+8+move_slot]=pp[1]
  need(a==bytes(b),'strategy changes only the specified moves/PP in entire128-byte plaintext')
 return True


def compare_without_observer(model,raw,language,module_code,r):
 need(not r['poison'] and not r['cookies'] and r['variant']=='current','functional OFF comparison domain');bench,_=bench_image(model,raw,language,module_code,strategy=r['strategy'])
 with P.patch.object(B,'GF_ASSERT',0x23BE100),P.patch.object(B,'WFC_HOOK',0x23BE104):off=bench.run(r.get('trainer',21),plus=r['plus'],seed=r['seed'],max_instructions=3000000)
 need([x.hex() for x in off['mons']]==r['mon_hex'] and off['end']==r['end'] and off['seed_after']==r['seed_after'] and json.loads(json.dumps(off['events']))==json.loads(json.dumps(r['events'])),'functional observer OFF/ON native party/register/seed/all service events');return dict(party_sha256=P.sha(b''.join(off['mons'])),seed=off['seed_after'],end=off['end'],events_sha256=P.sha(json.dumps(off['events'],sort_keys=True).encode()),qualified=True,scope='functional native outputs/SDK events; declared canary/free-poison scratch differs')


def resource_summary(data,cases):
 members=collections.defaultdict(set)
 for r in cases:
  for event in r['models']:
   if event['name']=='ReadWholeNarcMemberByIdPair':members[event['args'][1]].add(event['args'][2])
   elif event['name']=='NARC_ReadFromMember':members[185].add(event['args'][1])
 receipts={}
 for narc,ids in sorted(members.items()):
  archive=data['receipts'][str(narc)];receipts[str(narc)]=dict(archive={k:v for k,v in archive.items() if k!='member_rom_offsets'},members={str(index):dict(bytes=len(data['archives'][narc][index]),sha256=P.sha(data['archives'][narc][index]),rom_offset=hex(archive['member_rom_offsets'][index])) for index in sorted(ids)})
 return dict(trainer=data['record'],class_id=data['class_id'],gender_byte=data['gender_byte'],maximum=data['maximum'],anchor=data['table'][data['maximum']],language_byte=data['language'],names={key:dict(words=len(value),words_sha256=P.sha(struct.pack('<%dH'%len(value),*value))) for key,value in data['names'].items()},archives=receipts,capsule_binding=data['capsule_binding'])


def analyze(rom,language,objects,strategy_object,*,trainer=21):
 profile=profile_for(trainer);model=P.G.S.SHARED.read_current(rom,language)
 with rom.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:
  code,ranges,module,proof=qualify(model,raw,language,objects,strategy_object,trainer=trainer);qualified=(code,ranges,module);data=resources(model,raw,language,trainer=trainer);positives=[];baselines=[];guards=[];counters=[];neutrality=[]
  for plus in (0,1):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,qualified,plus,seed,trainer=trainer);require_case(r,data);positives.append(r)
   need(positives[-1]['mon_hex']==positives[-2]['mon_hex'] and positives[-1]['seed_after']!=positives[-2]['seed_after'],'native21 source reseeds preserve party while original seed is restored independently')
   baseline=run_case(model,raw,language,qualified,plus,strategy=False,trainer=trainer);require_case(baseline,data);compare_strategy_delta(positives[-2],baseline);baselines.append(baseline);neutrality.append(compare_without_observer(model,raw,language,module,positives[-2]))
  normal=next(r for r in positives if r['plus']==1 and r['seed']==0x12345678)
  for options in (dict(poison=True),dict(cookies=True)):
   r=run_case(model,raw,language,qualified,trainer=trainer,**options);require_case(r,data);need(r['mon_hex']==normal['mon_hex'] and r['seed_after']==normal['seed_after'],'native21 SDK/caller guard output neutrality');guards.append(r)
  for variant in variants_for(trainer)[1:]:
   r=run_case(model,raw,language,qualified,variant=variant,trainer=trainer)
   if variant in ('wrong_restore_seed','omit_prefix_free'):need(r['mon_hex']==normal['mon_hex'],'native21 same-party counter premise')
   if variant=='omit_prefix_free':need(r['seed_after']==normal['seed_after'] and r['live']=={B.ARENA:108},'native21 exact108-byte leak premise')
   delta=counter_delta(trainer,variant)
   if delta is not None:need(r['buffer_before_free']==normal['buffer_before_free'] and r['decoded'][delta['offset']//18]['moves'][(delta['offset']%18-8)//2]==delta['before'] and r['seed_after']==normal['seed_after'],'unchanged-buffer wrong-callee counter premise')
   try:require_case(dict(r,variant='current',game_shadows=[]),data)
   except ValueError as e:r['rejection']=str(e)
   else:raise ValueError('native21 counter accepted')
   counters.append(r)
  summary=resource_summary(data,positives+baselines+guards+counters)
 return dict(schema=f'trainer{trainer}-native-constructor-v1',trainer=trainer,language=language,input=model['record'],proof=proof,resources=summary,positives=positives,old_recipe_baselines=baselines,guards=guards,counters=counters,observer_neutrality=neutrality,source_sha256={str(p.relative_to(P.SOURCE)):P.sha(p.read_bytes()) for p in (Path(__file__),Path(S.__file__),Path(F.__file__),Path(M.__file__),Path(C.__file__),Path(B.__file__))},conclusions=dict(native_constructor_entry_to_return=True,all_six_native_pokemon=True,no_post_entry_mon_or_frame_fixture=True,once_only_actual_strategy_copy=True,installed_rematch_activation=0,natural_encounter_observed=False),limits=['BattleSetup,index1,battleType1,Plus0/1,cap100 and initial seed are initialized API fixtures; no natural encounter or whole-battle qualification','SDK heap/name/raw archive/overlay FS boundaries reuse existing models; no native SDK allocator/FS/failure implementation execution','The old-hook comparison is the same exact ROM with four declared pre-entry RAM BL recipe shadows,not a historical whole-ROM equivalence claim','Strategy and rematch objects reattest earlier exact reconstruction; old Plus and original native MW compilers remain unavailable',f'Only trainer{trainer}/type3/form0 and its exact six records are covered by this receipt; other trainer IDs,formats,SAVE/device/timing remain separate'])


def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('rom','objects','strategy-object','json'):p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--trainer',type=int,choices=tuple(PROFILES),default=21);args=p.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');need(P.SOURCE not in args.json.resolve().parents and args.json.resolve()!=P.SOURCE,'output must be outside source');need(args.objects.resolve() not in args.json.resolve().parents and args.strategy_object.resolve().parent not in args.json.resolve().parents,'output must be outside retained object directories');need(all(x.is_file() for x in (args.rom,args.strategy_object,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o')),'constructor inputs must exist');r=analyze(args.rom,args.language,args.objects,args.strategy_object,trainer=args.trainer);payload=(json.dumps(r,separators=(',',':'))+'\n').encode();need(len(payload)<=16*1024*1024,'constructor expanded report budget');args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as output:
   if args.json.suffix=='.gz':
    with gzip.GzipFile(fileobj=output,mode='wb',filename='',mtime=0) as compressed:compressed.write(payload)
   else:output.write(payload)
 except ValueError as e:p.exit(2,str(e)+'\n')
 print(args.language,args.trainer,'native full constructor,source fields,old-recipe delta and lifetime verified; natural activation remains outside coverage')


if __name__=='__main__':main()
