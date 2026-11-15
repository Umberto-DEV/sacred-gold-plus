#!/usr/bin/env python3
"""Continue the real rematch constructor to the first native CreateMon entry."""
from pathlib import Path
import importlib.util,mmap,json,struct
s=importlib.util.spec_from_file_location('rematch_active_dependency',Path(__file__).with_name('attribuisci_attivo.py'));A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
P,B=A.P,A.B;need=A.need
def bench_bytes(model,a,n):return P.G.piece(model['segments'],a,n)
from unicorn.arm_const import UC_ARM_REG_LR
NATIVE_BLOCKS=(
 (0x201fd38,0x201fd3e,True,'5cb6a8729e95cc248a0c7ad68108c00e2564e96a9bea977932ae9018be8da215'),
 (0x201fd44,0x201fd5c,True,'9f5fee4701ddd8666fdb72f459c6df8622eef57d586a57819a98a36efe367a83'),
 (0x20735f8,0x20735fe,True,'4a480a9427d8f840cf0960ace989d55a5d08c0724f39941bede03f7dfc2577dc'),
 (0x207363e,0x2073672,True,'ca828134707c22d0b9ee9cb3359c83df618685d7c9cf692b9bab7e8a28f0632a'),
 (0x2073964,0x2073972,True,'f5305cbe286ce83a958ddbd2e0f80052821680e541e22c50f12d3b4b4fcea6b4'),
 (0x2073974,0x2073992,True,'dd1f310a4ee2806304609d8f2c4e6d9b8e8ffba3cb1d1c85a1e1ba95ddc4c56a'),
 (0x2073998,0x2073a16,True,'c6afbf781a99c13e21c5fbc8f54fcf004819301859b261d5461fa0a09db8cc3c'),
 (0x2073a98,0x2073ab0,True,'92492a340f5737d748ea0feac9de85de8116a91a7a89e21137790a7d27eec675'),
 (0x2073ac8,0x2073acc,True,'0f91d374b913a32e942cfabcd38e03115fe71c22b216c5923db0ffa66785d096'),
 (0x2073ad6,0x2073ae4,True,'c3bc88bca7e12e094b10ac29dfbb00a3d82b8c1abcfb1b5011a26648b1a0d571'),
 (0x20f2998,0x20f2a08,False,'d82dd7c5dbcc4f1c41d775a8c9d4f219bdcfb039a332f83030a34f16a34adf5b'),
 (0x20f2b2c,0x20f2ba4,False,'5acebbeabc1624fb07a1a909b554f2e8b6bd8fcbf1370f566e6e553aa36e4b00'),
)
class Consumer(A.Active):
 latest=None
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);Consumer.latest=self;self.context=None;self.consume=False;self.nextcode=set();self.nextwrites=[];self.calls=[];self.create=None;self.consumer_variant='current';self.shadows_next=[];self.helpers=[];self.pending_helpers=[];self.record_reads=[];self.dependency_reads=[];self.next_allowed={}
 def step(self,u,a,n,_):
  if not self.consume:
   if a==B.SEAM_RESUME:self.context=u.context_save();self.ram_at_seam=P.sha(bytes(u.mem_read(0x02000000,0x400000)))
   return super().step(u,a,n,_)
  if a==0x207397C and self.consumer_variant=='wrong_record':
   target=self.sp()+0x64;old=self.word(target);u.mem_write(target,struct.pack('<I',B.ARENA+18));self.shadows_next.append(dict(pc=hex(a),address=hex(target),before=old,after=B.ARENA+18))
  self.instructions+=1;need(self.instructions<200000,'continuation budget');self.max_stack=max(self.max_stack,B.STACK_TOP-self.sp())
  thumb=bool(u.reg_read(P.UC_ARM_REG_CPSR)&32)
  if a==0x206DE38:
   need(thumb and n==2 and bytes(u.mem_read(a,32))==self.bench.segment_bytes(a,32),'actual CreateMon entry identity/mode')
   need(not self.pending_helpers,'native helper return incomplete')
   self.create=dict(live=[self.reg(i) for i in range(4,12)],nzcv=u.reg_read(P.UC_ARM_REG_CPSR)>>28,args=[self.reg(i) for i in range(4)],stack=[self.word(self.sp()+4*i) for i in range(4)],sp=self.sp(),lr=u.reg_read(UC_ARM_REG_LR),buffer_sha256=P.sha(bytes(u.mem_read(B.ARENA,108))),seed=self.word(0x21D15A8),plus_counter=self.word(0x23D8708));u.emu_stop();return
  need(a not in B.STUBS and a not in (B.FS_INFO,B.FS_IMAGE,B.FS_START,B.FS_UNLOAD),'unexpected continuation SDK model')
  need(self.next_allowed.get(a)==(n,thumb),'consumer instruction outside qualified code: '+hex(a))
  expected=self.bench.segment_bytes(a,n);need(bytes(u.mem_read(a,n))==expected,'continuation bytes differ')
  self.nextcode.add((a,n,thumb))
  while self.pending_helpers and a==self.pending_helpers[-1]['return_pc']:
   c=self.pending_helpers.pop();need(self.sp()==c['sp'] and [self.reg(i) for i in range(4,12)]==c['saved'],'native helper SP/r4-r11 return ABI')
   c.update(result=[self.reg(i) for i in range(4)],return_sp=self.sp(),return_saved=[self.reg(i) for i in range(4,12)],after_seed=self.word(0x21D15A8),nzcv=u.reg_read(P.UC_ARM_REG_CPSR)>>28)
   if c['entry']=='0x2073a98':c['pid_gender']=self.word(c['args'][3])
   self.helpers.append(c)
  if a in (0x20735F8,0x2073A98,0x201FD38,0x201FD44,0x20F2998,0x23D6228,0x23D61C4,0x23D602C,0x23D8134,0x23D8100):
   c=dict(ordinal=len(self.calls),entry=hex(a),args=[self.reg(i) for i in range(4)],stack=[self.word(self.sp()+4*i) for i in range(4)],sp=self.sp(),return_pc=u.reg_read(UC_ARM_REG_LR)&~1,saved=[self.reg(i) for i in range(4,12)],before_seed=self.word(0x21D15A8));self.pending_helpers.append(c);self.calls.append(c)
   if a==0x20F2998:need(not thumb and c['args'][:2]==[7905,255],'native positive signed IV division ABI')
 def write(self,u,access,a,n,value,_):
  if not self.consume:return super().write(u,access,a,n,value,_)
  pc=u.reg_read(P.UC_ARM_REG_PC)
  need((B.STACK_TOP-4096<=a and a+n<=B.STACK_TOP) or(a,n,pc)==(0x21D15A8,4,0x201FD3A) or(a,n,pc)==(0x21D15A8,4,0x201FD52) or(a,n,pc)==(0x23D8708,4,0x23D813E),'unexpected continuation write '+hex(a)+' PC='+hex(pc))
  if a==0x21D15A8:
   need(value==(((self.word(a)*0x41C64E6D+0x6073)&0xFFFFFFFF) if pc==0x201FD52 else self.reg(0)),'native exact RNG state store')
  if a==0x23D8708:need(value==self.word(a)+1,'native Plus hit counter increment')
  self.nextwrites.append(dict(pc=hex(pc),address=hex(a),bytes=n,value=value))
 def read(self,u,access,a,n,value,_):
  if not self.consume:return super().read(u,access,a,n,value,_)
  spans=[(B.STACK_TOP-4096,B.STACK_TOP),(B.SETUP,B.SETUP+0x400),(B.ARENA,B.ARENA+108),(0x21D15A8,0x21D15AC),(0x23D6000,0x23D6244),(0x23D6600,0x23D6800),(0x23D8100,0x23D8200),(0x23D8500,0x23D8600),(0x23D8700,0x23D8720),(0x2073672,0x207367A),(0x2073994,0x2073998),(0x2073600,0x2073604),(self.gender_table+66,self.gender_table+68),(0x201FD40,0x201FD44),(0x201FD5C,0x201FD68)]
  need(any(lo<=a and a+n<=hi for lo,hi in spans),'consumer read outside qualified resources: '+hex(a))
  if (0x23D8500<=a<0x23D8600) or (self.gender_table+66<=a<self.gender_table+68) or (0x23D6608<=a<0x23D6678 and (a-0x23D6608)%16==0):self.dependency_reads.append(dict(pc=hex(u.reg_read(P.UC_ARM_REG_PC)),address=hex(a),bytes=n,value=int.from_bytes(u.mem_read(a,n),'little')))
  if B.ARENA<=a and a+n<=B.ARENA+108:self.record_reads.append(dict(pc=hex(u.reg_read(P.UC_ARM_REG_PC)),address=hex(a),bytes=n,value=int.from_bytes(u.mem_read(a,n),'little')))

def run_case(model,raw,lang,code,consumer_code,trainer=712,seed=0x12345678,consumer_variant='current'):
 need(consumer_variant in ('current','wrong_record','low_cap'),'consumer fixture domain')
 def factory(*args,**kwargs):
  audit=Consumer(*args,**kwargs);audit.consumer_variant=consumer_variant;audit.next_allowed=consumer_code;audit.gender_table=struct.unpack('<I',bench_bytes(model,0x2073600,4))[0];return audit
 with P.patch.object(A,'Active',factory):prefix=A.run(model,raw,lang,code,trainer=trainer,seed=seed)
 A.require_active(prefix);cpu=Consumer.latest
 need(P.sha(bytes(cpu.uc.mem_read(0x02000000,0x400000)))==cpu.ram_at_seam,'postgetter changed RAM')
 cpu.uc.context_restore(cpu.context);cpu.consume=True;phase_before=bytes(cpu.uc.mem_read(0x02000000,0x400000))
 if consumer_variant=='low_cap':
  cpu.uc.mem_write(0x23D8702,b'\x4b');cpu.shadows_next.append(dict(pc=hex(B.SEAM_RESUME),address='0x23d8702',before=100,after=75))
 cpu.uc.emu_start(B.SEAM_RESUME|1,B.SENTINEL,count=200000)
 need(cpu.create is not None,'first CreateMon not reached')
 ignored=[(B.STACK_TOP-4096,B.STACK_TOP),(0x21D15A8,0x21D15AC),(0x23D8708,0x23D870C)]
 if consumer_variant=='low_cap':ignored.append((0x23D8702,0x23D8703))
 frozen_before=P.masked_hash(phase_before,ignored);frozen_after=P.masked_hash(bytes(cpu.uc.mem_read(0x02000000,0x400000)),ignored);need(frozen_before==frozen_after,'unrelated consumer RAM changed')
 return dict(unrelated_ram_sha256=frozen_after,helpers=cpu.helpers,record_reads=cpu.record_reads,dependency_reads=cpu.dependency_reads,prefix=prefix,consumer_variant=consumer_variant,create=cpu.create,writes=cpu.nextwrites,shadows=cpu.shadows_next,code=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(cpu.nextcode)],instructions=cpu.instructions,max_stack=cpu.max_stack,ram_unchanged_postgetter=True)



def qualify_code(model,strategy_proof):
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_ARM
 allowed={}
 for start,end,thumb,digest in NATIVE_BLOCKS:
  blob=bench_bytes(model,start,end-start);need(P.sha(blob)==digest,'consumer native code block '+hex(start))
  instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB if thumb else CS_MODE_ARM).disasm(blob,start))
  need(sum(i.size for i in instructions)==len(blob),'consumer instruction block decode')
  for i in instructions:allowed[i.address]=(i.size,thumb)
 strategy=bench_bytes(model,0x23D6000,580);allowed.update(P.mapped_code(strategy_proof,strategy,0x23D6000))
 blob=bench_bytes(model,0x23D8100,256);table=bench_bytes(model,0x23D8500,256)
 need(P.sha(blob)=='6392b5b8a1e67727ec4ea2af7ea8ee4f29219fb3161f8f9b8b0fae2d96216b56' and blob==(P.SOURCE/'sgp12/build/plus/blob.bin').read_bytes(),'archived Plus code correspondence')
 need(P.sha(table)=='dcbcaf243fbe29c5b8eced0b0102bddf034fde66977912d32da28484fc42144e' and table==(P.SOURCE/'sgp12/build/plus/tab_trainer.bin').read_bytes(),'archived trainer level table correspondence')
 for start,end in ((0x23D8100,0x23D8134),(0x23D8134,0x23D818C),(0x23D8194,0x23D81B4)):
  code=bench_bytes(model,start,end-start);ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(code,start));need(sum(i.size for i in ins)==len(code),'Plus code/pool extent')
  for i in ins:allowed[i.address]=(i.size,True)
 need(P.sha(bench_bytes(model,0x20F2998,524))=='e8183a62ffe6a54210cd7d025b01431ff792025c1b45a0e8537abd8cec16ccfb','full native signed IV divider')
 need(P.sha(bench_bytes(model,0x201FD44,36))=='f65ef9021357e9f6bf6f7b5332b0554ea7b689b2ef3062267cc6f1d6af7b0281','native LCRNG code/literals')
 need(P.sha(bench_bytes(model,0x20735F8,12))=='e545ca571108e7d051ea83b12593ae464707b9a8dd38954d912237f8f5c703b4','native trainer-class getter/literal')
 need(P.sha(bench_bytes(model,0x201FD38,12))=='d437fa4257d8547556364b6059fcaa2037c359bc3731db3c761729a5d50f43ae','native seed setter/literal')
 need(P.sha(bench_bytes(model,0x206DE38,32))=='3bcde63b7ff701af7654117913c232cc4a2b57c3343a0af75aa86a2da882f5d3','first CreateMon entry pin')
 return allowed


def input_data(raw,model):
 headers,receipt=P.RAW.raw_archive(raw,'a/0/5/5');classes={};records=[]
 pointer=struct.unpack('<I',bench_bytes(model,0x2073600,4))[0]
 need(pointer==0x20FFB90 and bench_bytes(model,pointer+66,2)==b'\x00\x01','native class table binding/covered entries')
 for t in P.R.load_spec()['trainers']:
  trainer=t['trainer_id'];header=bytes(headers[trainer]);need(P.sha(header)==t['header_sha256'] and header[0]==3 and header[3]==6,'native trainer header provenance')
  cls=header[1];need(cls in (66,67),'covered native trainer class');classes[str(trainer)]=dict(cls=cls,gender=bench_bytes(model,pointer+cls,1)[0])
  records.append(dict(trainer=trainer,header_sha256=P.sha(header),rom_offset=hex(receipt['member_rom_offsets'][trainer]),trainer_class=cls,gender_table_address=hex(pointer+cls),gender_byte=classes[str(trainer)]['gender']))
 return dict(classes=classes,records=records,header_archive={k:v for k,v in receipt.items() if k!='member_rom_offsets'})


def require_consumer(r,data):
 A.require_active(r['prefix']);need(r['consumer_variant']=='current','consumer normal fixture domain')
 prefix=r['prefix'];trainer,seed=prefix['trainer'],prefix['seed'];selected=(seed^(seed>>16)^trainer)&1;party=A.authored(trainer,'B' if selected else 'A')
 difficulty,override,base,species=struct.unpack_from('<BBHH',party);form=species>>10;species&=1023
 cls=data['classes'][str(trainer)]['cls'];gender=data['classes'][str(trainer)]['gender'];pid_gender=0x78 if gender==1 else 0x88
 need(override&15==0,'covered no gender-ratio override path')
 if override>>4==1:pid_gender&=~1
 elif override>>4==2:pid_gender|=1
 initial=difficulty+base+species+trainer;state=initial;chain=[]
 for _ in range(cls):
  state=(state*0x41C64E6D+0x6073)&0xFFFFFFFF;chain.append(state)
 pid=((state>>16)<<8)+pid_gender;maximum=max(struct.unpack_from('<H',party,18*i+2)[0] for i in range(6));anchor=min(100,(maximum*(100+min(12,6+maximum//10))+50)//100);level=max(base,min(100,anchor-(maximum-base)));iv=difficulty*31//255
 create=r['create'];sp=prefix['seam']['sp']
 need(create==dict(live=[B.SETUP,52,B.ARENA+128,pid,*[B.SENTINEL_REGS[i] for i in range(8,12)]],nzcv=0,args=[B.ARENA+128,species,level,iv],stack=[1,pid,2,0],sp=sp,lr=0x2073A17,buffer_sha256=P.sha(party),seed=state,plus_counter=1),'native first CreateMon exact arguments/live state/seed/buffer')
 need(r['ram_unchanged_postgetter'] is True and r['instructions']<200000 and r['max_stack']<=512,'native continuation/memory/instruction/stack boundary')
 helpers=r['helpers'];need(len(helpers)==cls+9,'native helper complete call count')
 def one(entry):
  matches=[c for c in helpers if c['entry']==hex(entry)];need(len(matches)==1,'native helper count '+hex(entry));return matches[0]
 need(sorted(c['ordinal'] for c in helpers)==list(range(len(helpers))),'native helper entry/completion ordering')
 for c in helpers:
  need(c['sp']==c['return_sp'] and c['saved']==c['return_saved'],'all completed helper ABI')
  if c['entry'] in ('0x20735f8','0x2073a98'):need(c['before_seed']==c['after_seed']==seed,'native pre-personality seed preservation')
  elif c['entry'] not in ('0x201fd38','0x201fd44'):need(c['before_seed']==c['after_seed']==state,'native post-personality seed preservation')
 gender_call=one(0x20735F8);need(gender_call['args'][0]==cls and gender_call['result'][0]==gender and gender_call['return_pc']==0x2073650,'native class getter/data return')
 override_call=one(0x2073A98);need(override_call['args']==[species,form,override,sp+0x7C] and override_call['pid_gender']==pid_gender and override_call['return_pc']==0x20739AA,'native PID override path')
 setter=one(0x201FD38);need(setter['args'][0]==initial and setter['before_seed']==seed and setter['after_seed']==initial and setter['return_pc']==0x20739C2,'native personality reseed')
 rng=[c for c in helpers if c['entry']=='0x201fd44'];need(len(rng)==cls,'native RNG trainer-class count')
 before=initial
 for call,after in zip(rng,chain):
  need(call['before_seed']==before and call['after_seed']==after and call['result'][0]==after>>16 and call['return_pc']==0x20739D2 and call['sp']==sp,'native RNG full chain/high16/return');before=after
 divider=one(0x20F2998);need(divider['args'][:2]==[difficulty*31,255] and divider['result'][:2]==list(divmod(difficulty*31,255)) and divider['return_pc']==0x20739F6,'native signed IV quotient/remainder')
 strategy=one(0x23D61C4);need(strategy['args'][:3]==[B.SETUP,52,B.ARENA] and strategy['result'][0]==0 and strategy['return_pc']==0x23D6234,'native strategy wrapper no-effect')
 apply=one(0x23D602C);need(apply['args']==[B.ARENA,trainer,0x603,1] and apply['stack'][0]==0x23D6600 and apply['result'][0]==0,'native strategy core/config no-effect')
 group=one(0x23D8100);need(group['args'][:3]==[B.ARENA,18,6] and group['result'][0]==maximum and group['return_pc']==0x23D816A,'native six-opponent group maximum')
 plus=one(0x23D8134);need(plus['args'][:3]==[base,B.ARENA,0x603] and plus['result'][0]==level and plus['return_pc']==0x23D81AC,'native Plus level/whole group dependency')
 hook=one(0x23D6228);need(hook['args']==[0,species,B.ARENA,iv<<24] and hook['result']==[B.ARENA+128,species,level,iv<<24] and hook['return_pc']==0x2073A10 and hook['nzcv']==0,'actual chained level hook register/flag ABI')
 stores=[w for w in r['writes'] if w['address']=='0x21d15a8'];expected=[dict(pc='0x201fd3a',address='0x21d15a8',bytes=4,value=initial)]+[dict(pc='0x201fd52',address='0x21d15a8',bytes=4,value=x) for x in chain]
 need(stores==expected,'actual native seed/RNG store sequence')
 need([w for w in r['writes'] if w['address']=='0x23d8708']==[dict(pc='0x23d813e',address='0x23d8708',bytes=4,value=1)],'actual Plus counter store')
 reads=r['record_reads'];first=[dict(pc=hex(pc),address=hex(B.ARENA+off),bytes=n,value=int.from_bytes(party[off:off+n],'little')) for pc,off,n in ((0x2073980,4,2),(0x20739A2,1,1),(0x20739AE,0,1),(0x20739B0,2,2),(0x20739EA,0,1),(0x23D8194,2,2))]
 group_reads=[dict(pc=hex(pc),address=hex(B.ARENA+18*i+off),bytes=1,value=party[18*i+off]) for i in range(6) for pc,off in ((0x23D811C,2),(0x23D811E,3))]
 need(reads==first+group_reads,'actual first-record and all six opponent-level reads')
 deps=r['dependency_reads'];need(len(deps)==9,'native gender/strategy/trainer-table resource consumption')
 need(deps[0]==dict(pc='0x20735fa',address=hex(0x20FFB90+cls),bytes=1,value=gender),'actual native class table byte')
 need(deps[1:8]==[dict(pc='0x23d6086',address=hex(0x23D6608+16*i),bytes=2,value=tid) for i,tid in enumerate((21,31,32,33,34,244,245))],'actual strategy seven-ID exclusion scan')
 need(deps[-1]==dict(pc='0x23d8174',address=hex(0x23D8500+maximum),bytes=1,value=anchor),'actual trainer level table lookup')
 need({B.SEAM_RESUME,0x207366A,0x2073964,0x2073A12,0x23D6228}<=set(int(c['ram'],16) for c in r['code']),'native first-record caller/dispatch complete coverage')
 return True


def attest_strategy(model,raw,work):
 """Rebuild the exact dependency using its existing owner, without composing a ROM."""
 from sgp13 import teams
 need(not work.exists() and not work.is_symlink(),'strategy work must be fresh')
 compiler=P.R._compiler();code,symbols=teams.compile_native(work)
 need(len(code)==580 and P.sha(code)=='09e88a137b006e8ba638770ba57e1a6e5fe9960787e05ec7c253cb230da04436' and code==bench_bytes(model,0x23D6000,580),'recompiled strategy code readback')
 proof=P.audit_elf((work/'teams.o').read_bytes(),code,0x23D6000)
 need(proof['symbols']['strategy_hook']=='0x23d6229' and proof['symbols']['strategy_apply']=='0x23d602d','independent strategy ELF entries')
 parties,_=P.RAW.raw_archive(raw,'a/0/5/6');headers,_=P.RAW.raw_archive(raw,'a/0/5/5');spec=json.loads((P.SOURCE/'sgp13/data/strategic-teams.json').read_text());records=bytearray();moves=bytearray()
 for team in spec['teams']:
  tid=team['trainer_id'];before=bytes(parties[tid]);need(len(before)==team['bytes'] and P.sha(before)==team['source_sha256'] and headers[tid][0]==team['type'] and headers[tid][3]==team['count'],'strategy raw source-member preimages')
  after=bytearray(before);first=len(moves)//8
  for move in team['moves']:
   at=move['offset'];need(struct.unpack_from('<H',after,at)[0]==move['before'],'strategy move preimage');struct.pack_into('<H',after,at,move['after']);moves+=struct.pack('<4H',at,move['before'],move['after'],0)
  records+=struct.pack('<HHIIBBBB',tid,first,teams.fnv(before),teams.fnv(after),team['type'],team['count'],len(before),len(team['moves']))
 config=struct.pack('<IHH',0x31544753,len(records)//16,len(moves)//8)+records+moves;stored=bench_bytes(model,0x23D6600,512)
 ids=[t['trainer_id'] for t in spec['teams']]
 need(ids==[21,31,32,33,34,244,245] and len(config)==192 and stored==config+bytes(512-len(config)) and P.sha(stored)=='003ec5b4372e8b0070f2521d1676a8038d19b4b472218aadedb4735c0bb27114','strategy config192/pad512 exact readback/seven IDs')
 return dict(elf=proof,code_bytes=len(code),code_sha256=P.sha(code),config_bytes=len(config),config512_sha256=P.sha(stored),trainers=ids,compiler_version=P.R.COMPILER_VERSION,compiler_sha256=P.R.COMPILER_SHA256,object='teams.o',symbols={k:hex(v) for k,v in symbols.items() if not k.startswith('$')})


def analyze(rom,language,objects,work):
 model=P.G.S.SHARED.read_current(rom,language)
 with rom.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
  prefix_code,prefix_proof=A.attest_objects(raw,model,objects);strategy=attest_strategy(model,raw,work);code=qualify_code(model,strategy['elf']);data=input_data(raw,model);positives=[];counters=[]
  for trainer in (712,713):
   for seed in (0x12345678,0x12345679):
    r=run_case(model,raw,language,prefix_code,code,trainer,seed);require_consumer(r,data);positives.append(r)
    for variant in ('wrong_record','low_cap'):
     r=run_case(model,raw,language,prefix_code,code,trainer,seed,variant)
     need(r['create']['buffer_sha256']==r['prefix']['buffer_sha256'] and r['prefix']['registry'][0]==(126,0),'counter premise must preserve chosen buffer/registry')
     try:require_consumer(dict(r,consumer_variant='current'),data)
     except ValueError as e:r['rejection']=str(e)
     else:raise ValueError('native consumer counter accepted')
     counters.append(r)
  view=P.G.S.SHARED.gifts_audit.Arm9View(raw);locations=[]
  for a,n in ((0x207363E,2),(0x2073A0C,4),(0x206DE38,32),(0x201FD44,36),(0x20F2998,524),(0x23D6000,580),(0x23D6600,512),(0x23D8100,256),(0x23D8500,256),(0x20FFBD2,2)):
   need(view.read(a,n)==bench_bytes(model,a,n),'independent consumer ARM9 readback');locations.append(dict(ram=hex(a),rom_offset=hex(view.offset(a,n)),bytes=n,sha256=P.sha(view.read(a,n))))
 return dict(schema='rematch-first-native-consumer-v1',language=language,input=model['record'],prefix_proof=prefix_proof,strategy=strategy,resources=data,locations=locations,positives=positives,counters=counters,
  source_sha256={str(p.relative_to(P.SOURCE)):P.sha(p.read_bytes()) for p in (Path(__file__),Path(A.__file__),Path(P.__file__),Path(B.__file__),P.SOURCE/'sgp13/teams.py',P.SOURCE/'features/trainer-strategy/native.c',P.SOURCE/'features/trainer-strategy/strategy.c',P.SOURCE/'features/trainer-strategy/strategy.h',P.SOURCE/'sgp13/data/strategic-teams.json',P.SOURCE/'features/native-core/sorgenti-v-finale/plus_party.c')},
  conclusions=dict(owned_source_binary_correspondence=True,native_first_record_consumption_observed=True,first_create_mon_entry_only=True,installed_activation=0,natural_activation_observed=False),
  limits=['Starts from actual P28 RAM/copy108/unload and continues the same CPU after restoring only a saved CPU context; all main RAM is unchanged by the bench post-getter',
   'Stops before executing CreateMon at0206DE38: item/move/PP writes,complete Pokemon/party,constructor return and original RNG restoration are outside coverage',
   'Plus level uses six opponent records/max72,not player party; cap100 and fixture seeds are initialized inputs',
   'Actual native trainer-class RNG,override0/32,signed division7905/255,seven-ID strategy exclusion and archived Plus level run without new SDK models',
   'Strategy source recompiles exactly; Plus blob/table are archived binary/source correspondence with historical compiler unavailable,not a fresh Plus or native MW build',
   'Named active1/consumer counters exist only in emulated RAM after installed active0 identity admission; no ROM/save/device/timing/natural activation claim'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','work','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  P.validate_outputs((args.rom,args.objects/'rematch-variants.o',args.objects/'rematch-stub.o'),args.work,args.json)
  for path in (args.work,args.json):need(args.objects.resolve() not in path.resolve().parents and path.resolve()!=args.objects.resolve(),'outputs must be outside retained input objects')
  result=analyze(args.rom,args.language,args.objects,args.work)
  args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'4 native first-record/CreateMon entries and8 counterproofs verified; body/full party unexecuted; installed active0')


if __name__=='__main__':main()
