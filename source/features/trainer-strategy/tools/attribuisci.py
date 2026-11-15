#!/usr/bin/env python3
"""Attribute the installed trainer-strategy type3 hook, buffer writes and native return.

Six sequential hook invocations are initialized at a documented ABI boundary.
This does not execute CreateMon or establish natural trainer activation.
"""
from pathlib import Path
import importlib.util,struct,json,mmap,collections,gzip
SOURCE=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('strategy_full_dependency',SOURCE/'features/rematch-variants/tools/attribuisci_squadra_completa.py');F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
P,C,M,B=F.P,F.C,F.M,F.B;need=F.need
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR
SITE,END,OLD=0x2073A0C,0x2073A12,0x23D8194
CONFIG,BUFFER,MON,SETUP,STACK=0x23D6600,B.ARENA,B.ARENA+128,B.SETUP,B.STACK_TOP
IDS=(21,31,32,33,34,244,245)
VARIANTS=('current','preapplied','late_delta','changed_preimage','unknown','plus2','wrong_count')


def fnv(payload):
 h=2166136261
 for byte in payload:h=((h^byte)*16777619)&0xFFFFFFFF
 return h


def resources(raw,model):
 spec=json.loads((SOURCE/'sgp13/data/strategic-teams.json').read_text());need(tuple(t['trainer_id'] for t in spec['teams'])==IDS,'seven strategy IDs');headers,hr=P.RAW.raw_archive(raw,'a/0/5/5');parties,pr=P.RAW.raw_archive(raw,'a/0/5/6');records={}
 for t in spec['teams']:
  tid=t['trainer_id'];before=bytes(parties[tid]);header=bytes(headers[tid]);need(len(before)==108 and P.sha(before)==t['source_sha256'] and header[0]==3 and header[3]==6,'strategy canonical raw member/header preimages');after=bytearray(before)
  for move in t['moves']:
   off=move['offset'];need(off%18 in (8,10,12,14) and off%2==0 and 0<=off<107 and struct.unpack_from('<H',before,off)[0]==move['before'],'strategy specification move preimage');struct.pack_into('<H',after,off,move['after'])
  records[str(tid)]=dict(spec=t,header=header.hex(),header_sha256=P.sha(header),member_sha256=P.sha(before),before=before.hex(),after=bytes(after).hex(),before_fnv=fnv(before),after_fnv=fnv(after),header_offset=hex(hr['member_rom_offsets'][tid]),member_offset=hex(pr['member_rom_offsets'][tid]))
 return dict(records=records,archives={name:{k:v for k,v in receipt.items() if k!='member_rom_offsets'} for name,receipt in (('headers',hr),('parties',pr))})


def qualify(model,proof):
 need(P.sha(C.bench_bytes(model,0x23D6000,580))=='09e88a137b006e8ba638770ba57e1a6e5fe9960787e05ec7c253cb230da04436','strategy exact qualified code580')
 code=C.qualify_code(model,proof)
 need(C.bench_bytes(model,0x23D6244,1536-580)==bytes(1536-580),'strategy code allocation zero padding')
 for site in (0x2073718,0x2073802,0x207390C,SITE):need(P.G.S.SHARED.branch(C.bench_bytes(model,site,4),site,'bl')==0x23D6228,'four installed strategy call sites')
 need(C.bench_bytes(model,SITE,4) and P.G.S.SHARED.branch(C.bench_bytes(model,SITE,4),SITE,'bl')==0x23D6228,'actual native type3 strategy caller BL')
 need(C.bench_bytes(model,0x2073A10,2)==bytes.fromhex('1b0e') and P.G.S.SHARED.branch(C.bench_bytes(model,END,4),END,'bl')==0x206DE38,'native LSRS and following CreateMon BL boundary')
 need(code.get(0x2073A10)==(2,True) and code.get(END)==(4,True),'caller instruction boundaries')
 return code


def level(before,header,slot,plus,cap=100):
 base=struct.unpack_from('<H',before,18*slot+2)[0];kind=header[0];count=header[3];stride=8+((kind&1)<<3)+(kind&2)
 if not plus or not cap or not 1<=base<=255 or not 1<=count<=6:return base
 maximum=max(struct.unpack_from('<H',before,i*stride+2)[0] for i in range(count))
 if maximum>255 or maximum<base:return base
 anchor=min(100,(maximum*(100+min(12,6+maximum//10))+50)//100)
 return max(base,min(cap,anchor-(maximum-base)))


class Hook:
 def __init__(self,model,code):
  self.model=model;self.allowed=code;self.cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u=self.cpu;u.mem_map(0x01FF8000,0x8000);u.mem_map(0x02000000,0x400000);u.mem_map(0x027E0000,0x1000)
  for a,blob in model['segments']:u.mem_write(a,blob)
  u.hook_add(UC_HOOK_CODE,self.step);u.hook_add(UC_HOOK_MEM_WRITE,self.write);u.hook_add(UC_HOOK_MEM_READ,self.read)
 def reg(self,i):return self.cpu.reg_read(B.R[i])
 def word(self,a):return int.from_bytes(self.cpu.mem_read(a,4),'little')
 def step(self,u,a,n,_):
  self.instructions+=1;need(self.instructions<=100000,'strategy hook instruction budget');sp=u.reg_read(UC_ARM_REG_SP);self.max_stack=max(self.max_stack,STACK-sp);need(0<=STACK-sp<=512,'strategy hook stack budget');thumb=bool(u.reg_read(UC_ARM_REG_CPSR)&32);need(self.allowed.get(a)==(n,thumb),'strategy instruction outside qualified mapping '+hex(a));need(bytes(u.mem_read(a,n))==C.bench_bytes(self.model,a,n),'strategy installed instruction bytes');self.code.add((a,n,thumb))
  while self.pending and a==self.pending[-1]['return_pc']:
   e=self.pending.pop();e.update(result=[self.reg(i) for i in range(4)],return_sp=sp,return_saved=[self.reg(i) for i in range(4,12)],nzcv=u.reg_read(UC_ARM_REG_CPSR)>>28);need(sp==e['sp'] and e['saved']==e['return_saved'],'strategy helper SP/r4-r11 return ABI');self.helpers.append(e)
  if a in (0x23D6228,0x23D61C4,0x23D602C,0x23D8134,0x23D8100):
   self.pending.append(dict(entry=hex(a),args=[self.reg(i) for i in range(4)],stack0=self.word(sp),sp=sp,return_pc=u.reg_read(UC_ARM_REG_LR)&~1,saved=[self.reg(i) for i in range(4,12)]))
 def write(self,u,access,a,n,value,_):
  pc=u.reg_read(UC_ARM_REG_PC);need((STACK-512<=a and a+n<=STACK) or(BUFFER<=a and a+n<=BUFFER+108) or(a,n,pc)==(0x23D8708,4,0x23D813E),'strategy write outside owned stack/buffer/counter '+hex(a));self.write_pcs[(pc,n)]+=1
  if BUFFER<=a<BUFFER+108:self.output.append(dict(pc=hex(pc),offset=a-BUFFER,bytes=n,value=value))
  if pc in (0x23D6164,0x23D6168):self.local_delta.append(dict(pc=hex(pc),address=hex(a),bytes=n,value=value&255))
  if a==0x23D8708:need(value==self.word(a)+1,'strategy inherited Plus counter store')
 def read(self,u,access,a,n,value,_):
  spans=((STACK-512,STACK+128),(BUFFER,BUFFER+108),(SETUP,SETUP+0x400),(0x23D6000,0x23D6800),(0x23D8100,0x23D8200),(0x23D8500,0x23D8600),(0x23D8700,0x23D8720))
  need(any(lo<=a and a+n<=hi for lo,hi in spans),'strategy read outside admitted resources '+hex(a));self.read_pcs[(u.reg_read(UC_ARM_REG_PC),n)]+=1
 def invoke(self,slot,original,header,plus,*,old=False):
  u=self.cpu;self.instructions=0;self.max_stack=0;self.code=set();self.helpers=[];self.pending=[];self.output=[];self.local_delta=[];self.read_pcs=collections.Counter();self.write_pcs=collections.Counter();before=bytes(u.mem_read(BUFFER,108));species=struct.unpack_from('<H',original,18*slot+4)[0]&1023;iv=original[18*slot]*31//255
  initial=[0x12345679,species,BUFFER+18*slot,iv<<24,SETUP,52,MON,0x77777708,*[B.SENTINEL_REGS[i] for i in range(8,12)],0xCCCCCC0D]
  u.reg_write(UC_ARM_REG_CPSR,0xB000003F)
  for r,v in zip(B.R,initial):u.reg_write(r,v)
  u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,0xDDDDDDDD)
  if old:u.reg_write(UC_ARM_REG_LR,SITE+5)
  memory=bytes(u.mem_read(0x2000000,0x400000));counter=self.word(0x23D8708);seed=self.word(0x21D15A8)
  u.emu_start((OLD if old else SITE)|1,END,count=100000)
  need(u.reg_read(UC_ARM_REG_PC)==END and not self.pending,'strategy hook actual caller boundary/complete helper return');after=bytes(u.mem_read(BUFFER,108));ignored=((STACK-512,STACK),(BUFFER,BUFFER+108),(0x23D8708,0x23D870C));frozen=P.masked_hash(memory,ignored);need(frozen==P.masked_hash(bytes(u.mem_read(0x2000000,0x400000)),ignored),'unrelated strategy RAM changed')
  return dict(slot=slot,old_hook=old,before=before.hex(),after=after.hex(),entry_regs=initial,regs=[self.reg(i) for i in range(12)],sp=u.reg_read(UC_ARM_REG_SP),pc=u.reg_read(UC_ARM_REG_PC),nzcv=u.reg_read(UC_ARM_REG_CPSR)>>28,seed_before=seed,seed_after=self.word(0x21D15A8),counter_before=counter,counter_after=self.word(0x23D8708),helpers=self.helpers,output_stores=self.output,local_delta_stores=self.local_delta,instructions=self.instructions,max_stack=self.max_stack,frozen_sha256=frozen,code=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(self.code)],read_counts=[dict(pc=hex(a),bytes=n,count=c) for (a,n),c in sorted(self.read_pcs.items())],write_counts=[dict(pc=hex(a),bytes=n,count=c) for (a,n),c in sorted(self.write_pcs.items())])


def run_group(model,code,data,trainer=21,plus=1,variant='current',*,old=False):
 need(trainer in IDS and plus in (0,1) and variant in VARIANTS,'strategy fixture domain');record=data['records'][str(trainer)];original=bytes.fromhex(record['before']);header=bytearray.fromhex(record['header']);before=original;actual_id=trainer;active=plus;shadows=[];h=Hook(model,code);u=h.cpu
 def shadow(a,payload,why):
  oldbytes=bytes(u.mem_read(a,len(payload)));u.mem_write(a,payload);shadows.append(dict(address=hex(a),before=oldbytes.hex(),after=payload.hex(),reason=why))
 if variant=='preapplied':before=bytes.fromhex(record['after'])
 if variant=='changed_preimage':before=bytes([original[0]^1])+original[1:]
 if variant=='unknown':actual_id=999
 if variant=='plus2':active=2
 if variant=='wrong_count':header[3]=5
 if variant=='late_delta':
  need(trainer==33,'late-delta fixture is the three-change trainer');cfg=C.bench_bytes(model,CONFIG,192);team_index=IDS.index(trainer);first=struct.unpack_from('<H',cfg,8+16*team_index+2)[0];address=CONFIG+8+16*7+8*(first+2)+6;need(bytes(u.mem_read(address,2))==b'\0\0','late delta reserved preimage');shadow(address,b'\1\0','last of three deltas invalid only in RAM')
 u.mem_write(SETUP,bytes(0x400));u.mem_write(SETUP+0x18+4,struct.pack('<I',actual_id));u.mem_write(SETUP+0x28+52,bytes(header));u.mem_write(BUFFER,before);u.mem_write(STACK-512,b'\xA5'*512);u.mem_write(STACK,bytes(128));u.mem_write(STACK+0x74,struct.pack('<I',BUFFER));u.mem_write(0x23D8700,bytes([active,0,100])+bytes(29));u.mem_write(0x21D15A8,struct.pack('<I',0x12345678))
 calls=[h.invoke(slot,original,header,active,old=old) for slot in range(6)]
 return dict(trainer=trainer,plus=plus,variant=variant,active=active,actual_id=actual_id,header=bytes(header).hex(),entry_buffer=before.hex(),shadows=shadows,calls=calls,final=bytes(u.mem_read(BUFFER,108)).hex(),old_hook=old)


def require_group(r,data):
 trainer=r['trainer'];need(trainer in IDS and r['plus'] in (0,1) and r['variant'] in VARIANTS,'strategy report fixture domain');rec=data['records'][str(trainer)];original=bytes.fromhex(rec['before']);updated=bytes.fromhex(rec['after']);variant=r['variant'];old=r['old_hook'];header=bytearray.fromhex(rec['header']);active=2 if variant=='plus2' else r['plus'];actual=999 if variant=='unknown' else trainer
 if variant=='wrong_count':header[3]=5
 expected_shadows=[dict(address='0x23d66a6',before='0000',after='0100',reason='last of three deltas invalid only in RAM')] if variant=='late_delta' else []
 need(r['shadows']==expected_shadows,'strategy exact named configuration shadow')
 before=updated if variant=='preapplied' else bytes([original[0]^1])+original[1:] if variant=='changed_preimage' else original
 need(r['active']==active and r['actual_id']==actual and r['header']==bytes(header).hex() and r['entry_buffer']==before.hex(),'strategy exact source/fixture entry');apply=variant=='current' and r['plus']==1 and not old;expected=updated if apply else before;need(len(r['calls'])==6 and r['final']==expected.hex(),'strategy six sequential calls/final buffer')
 for slot,c in enumerate(r['calls']):
  prior=before if slot==0 else expected;species=struct.unpack_from('<H',original,18*slot+4)[0]&1023;iv=original[18*slot]*31//255;effective=level(original,header,slot,active);expected_regs=[MON,species,effective,iv,SETUP,52,MON,0x77777708,*[B.SENTINEL_REGS[i] for i in range(8,12)]]
  need(c['entry_regs']==[0x12345679,species,BUFFER+18*slot,iv<<24,SETUP,52,MON,0x77777708,*[B.SENTINEL_REGS[i] for i in range(8,12)],0xCCCCCC0D],'strategy exact initialized ABI')
  need(c['slot']==slot and c['before']==prior.hex() and c['after']==expected.hex() and c['old_hook']==old,'strategy per-slot buffer/lifetime');need(c['regs']==expected_regs and c['sp']==STACK and c['pc']==END and c['nzcv']==0,'strategy actual native caller arguments/SP/registers/flags');need(c['seed_before']==c['seed_after']==0x12345678 and c['counter_before']==slot and c['counter_after']==slot+1,'strategy no RNG mutation and inherited Plus accounting');need(0<c['instructions']<=100000 and c['max_stack']<=512,'strategy instruction/stack bounds')
  core=[e for e in c['helpers'] if e['entry']=='0x23d602c'];need(len(core)==int(not old),'strategy core entry count')
  if core:
   e=core[0];need(e['args']==[BUFFER,actual,header[0]|(header[3]<<8),active] and e['stack0']==CONFIG,'strategy actual core ABI/config');need(e['result'][0]==(len(rec['spec']['moves']) if apply and slot==0 else 0),'strategy changes applied exactly once')
  if core:
   count=len(rec['spec']['moves']) if apply and slot==0 else 2 if variant=='late_delta' and not old else 0;local=[]
   for move in rec['spec']['moves'][:count]:
    for part,pc in ((0,0x23D6164),(1,0x23D6168)):local.append(dict(pc=hex(pc),address=hex(core[0]['sp']-128+move['offset']+part),bytes=1,value=(move['after']>>(8*part))&255))
   need(c['local_delta_stores']==local,'strategy exact local deltas before atomic output')
  else:need(c['local_delta_stores']==[],'old hook must not apply local deltas')
  expected_entries={'0x23d8134'}|({'0x23d8100'} if active else set())|(set() if old else {'0x23d6228','0x23d61c4','0x23d602c'})
  order=([] if old else ['0x23d602c','0x23d61c4'])+(['0x23d8100'] if active else [])+['0x23d8134']+([] if old else ['0x23d6228'])
  need([e['entry'] for e in c['helpers']]==order and set(order)==expected_entries,'strategy complete ordered helper chain')
  expected_code={OLD,0x23D8134,0x2073A10}|({0x23D8100} if active else set())|(set() if old else {SITE,0x23D6228,0x23D61C4,0x23D602C});actual_code={int(e['ram'],16):(e['bytes'],e['thumb']) for e in c['code']}
  need(len(actual_code)==len(c['code']) and all(actual_code.get(a)==(4 if a==SITE else 2,True) for a in expected_code) and END not in actual_code,'strategy actual caller/helper instruction coverage')
  by={e['entry']:e for e in c['helpers']}
  if not old:
   need(by['0x23d6228']['args']==c['entry_regs'][:4] and by['0x23d6228']['return_pc']==SITE+4 and by['0x23d6228']['result']==[MON,species,effective,iv<<24] and by['0x23d6228']['nzcv']==0,'strategy actual hook return ABI')
   need(by['0x23d61c4']['args']==[SETUP,52,BUFFER,iv<<24] and by['0x23d61c4']['return_pc']==0x23D6234 and by['0x23d602c']['return_pc']==0x23D621C,'strategy wrapper and core caller bindings')
  base=struct.unpack_from('<H',original,18*slot+2)[0];kind=header[0];count=header[3];stride=8+((kind&1)<<3)+(kind&2)
  need(by['0x23d8134']['args']==[base,BUFFER,kind|(count<<8),iv<<24] and by['0x23d8134']['result'][0]==effective and by['0x23d8134']['return_pc']==0x23D81AC,'strategy inherited level arguments/result/return')
  if active:
   maximum=max(struct.unpack_from('<H',original,i*stride+2)[0] for i in range(count));need(by['0x23d8100']['args'][:3]==[BUFFER,stride,count] and by['0x23d8100']['result'][0]==maximum and by['0x23d8100']['return_pc']==0x23D816A,'strategy actual native group maximum')
  for e in c['helpers']:need(e['sp']==e['return_sp'] and e['saved']==e['return_saved'],'strategy completed helper ABI')
  stores=c['output_stores']
  if apply and slot==0:need(len(stores)==108 and [x['offset'] for x in stores]==list(range(108)) and all(x['bytes']==1 and x['value']==expected[x['offset']] for x in stores) and {x['pc'] for x in stores}=={'0x23d619a'},'strategy exact complete output copy trace')
  else:need(stores==[],'strategy fallback/repeat must not write buffer')
 return True


def raw_locations(model,raw):
 view=P.G.S.SHARED.gifts_audit.Arm9View(raw);result=[]
 for a,n in ((0x23D6000,2048),(0x2073718,4),(0x2073802,4),(0x207390C,4),(SITE,10),(OLD,32),(0x23D8100,256),(0x23D8500,256)):
  blob=view.read(a,n);need(blob==C.bench_bytes(model,a,n),'independent strategy raw ARM9 readback');result.append(dict(ram=hex(a),rom_offset=hex(view.offset(a,n)),bytes=n,sha256=P.sha(blob)))
 return result


def readback(rom,language,object_path):
 """Raw section/FAT/NARC/ELF verification only; no CPU or runtime observer."""
 recipe=F.attest_recipe_sources();model=P.G.S.SHARED.read_current(rom,language)
 with rom.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as raw:
  proof=M.attest_strategy_object(model,raw,object_path);qualify(model,proof);data=resources(raw,model);locations=raw_locations(model,raw)
 return dict(schema='trainer-strategy-readback-v1',language=language,input=model['record'],recipe_sources=recipe,strategy_elf=proof,resources=data,locations=locations,cpu_executed=False,source_sha256=P.sha(Path(__file__).read_bytes()))


def analyze(rom,language,object_path):
 recipe=F.attest_recipe_sources();model=P.G.S.SHARED.read_current(rom,language)
 with rom.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as raw:
  proof=M.attest_strategy_object(model,raw,object_path);code=qualify(model,proof);data=resources(raw,model);groups=[];old_groups=[]
  for trainer in IDS:
   for plus in (0,1):
    r=run_group(model,code,data,trainer,plus);require_group(r,data);groups.append(r);baseline=run_group(model,code,data,trainer,plus,old=True);require_group(baseline,data);need([c['regs'] for c in r['calls']]==[c['regs'] for c in baseline['calls']],'strategy old-hook ABI/level comparison');old_groups.append(baseline)
  controls=[]
  for variant in VARIANTS[1:]:
   r=run_group(model,code,data,33,1,variant);require_group(r,data);controls.append(r)
  pre=next(r for r in controls if r['variant']=='preapplied');positive=next(r for r in groups if r['trainer']==33 and r['plus']==1);need(pre['final']==positive['final'],'preapplied same-output counter premise');forged=dict(pre,variant='current')
  try:require_group(forged,data)
  except ValueError as e:pre['normal_rejection']=str(e)
  else:raise ValueError('preapplied same-output false success')
  locations=raw_locations(model,raw)
 return dict(schema='trainer-strategy-type3-v1',language=language,input=model['record'],recipe_sources=recipe,strategy_elf=proof,resources=data,locations=locations,groups=groups,old_groups=old_groups,controls=controls,source_sha256={str(p.relative_to(SOURCE)):P.sha(p.read_bytes()) for p in (Path(__file__),Path(F.__file__),Path(M.__file__),Path(C.__file__))},conclusions=dict(exact_strategy_code_config_readback=True,native_type3_hook_observed=True,full_constructor_executed=False,natural_activation_observed=False),limits=['Entry state is initialized at the documented native type3 hook ABI,not produced by a natural encounter','Only02073A0C and native LSRS02073A10 to stop before BL02073A12; other three format sites not executed','Six sequential hook invocations on one persistent buffer are not a complete native constructor loop','No CreateMon body,final move/PP setter or complete Pokemon in this case','Strategy ELF reattested from exact prior reconstruction; archived Plus/native original compilers unavailable; no new compilation','No SDK models or RNG call executes in this hook path; no hardware timing/save/balance claim'])


def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('rom','strategy-object','json'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--readback-only',action='store_true',help='read raw sections/members and ELF without CPU execution');a=p.parse_args()
 try:
  need(not a.json.exists() and not a.json.is_symlink(),'output must be fresh');need(SOURCE not in a.json.resolve().parents and a.json.resolve()!=SOURCE,'output must be outside source');need(a.strategy_object.resolve().parent not in a.json.resolve().parents,'output must be outside retained object directory');need(a.rom.is_file() and a.strategy_object.is_file(),'strategy inputs must exist');r=(readback if a.readback_only else analyze)(a.rom,a.language,a.strategy_object);payload=(json.dumps(r,separators=(',',':'))+'\n').encode();need(len(payload)<=16*1024*1024,'strategy report budget');a.json.parent.mkdir(parents=True,exist_ok=True)
  with a.json.open('xb') as f:
   if a.json.suffix=='.gz':
    with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0) as g:g.write(payload)
   else:f.write(payload)
 except ValueError as e:p.exit(2,str(e)+'\n')
 print(a.language,'raw/ELF readback only; CPU not executed' if a.readback_only else 'seven strategy configurations,type3 caller/once-only writes and Normal fallback verified; CreateMon unexecuted')


if __name__=='__main__':main()
