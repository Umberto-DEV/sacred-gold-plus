#!/usr/bin/env python3
"""Trace installed HP damage writers through HP script dispatch to item flinch."""
import importlib.util,json,mmap,struct
from pathlib import Path
spec=importlib.util.spec_from_file_location('hp_flinch_parent',Path(__file__).with_name('attribuisci_uturn.py'))
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_CPSR
need,sha=F.need,F.sha
CTX,BS,STACK,STOP=F.CTX,F.BS,F.STACK,F.STOP
HP,AFTER,RUN=0x0224C690,0x0224CAA4,0x0224C370
OPP=0x02390000
# Full windows are authenticated separately; executable subsets exclude data.
RANGES=((HP,0x0224C9BA),(0x0224C9E8,0x0224CA98),(AFTER,0x0224CACC),
 (0x0224CADA,0x0224CBA8),(0x0224CBB6,0x0224CC78),(RUN,0x0224C38A),
 (0x0223CF68,0x0223CFB0),(0x0223A7E0,0x0223A7E4),
 (0x0223DCAC,0x0223DCDC),(0x0223E12C,0x0223E15A),(0x0223E160,0x0223E1F2),
 (0x0223E200,0x0223E22C),(0x0223E22C,0x0223E25A),(0x0223E282,0x0223E286),
 (0x0223E3C4,0x0223E40E),(0x0223E41C,0x0223E474),
 (0x0223EC84,0x0223ECC6),(0x0223ECF0,0x0223ED78),
 (0x0223F61C,0x0223F66A),(0x0223F694,0x0223F734),
 (0x02245288,0x022452B4),(0x022454CC,0x022454E0),(0x022454E8,0x02245516),
 (0x02245528,0x0224553E),(0x022455CC,0x02245830),
 (0x0224768C,0x02247698),(0x022476D6,0x022476DC),(0x022478DC,0x022478F0),
 (0x0224EC74,0x0224EC82),(0x0224ECBE,0x0224ECC2),
 (0x02250C40,0x02250C6C),(0x02263B4C,0x02263C86),
 (0x0223AB1C,0x0223AB32),(0x02261258,0x0226125E),(0x022585A8,0x022585B6),
 (0x020726C0,0x020726E0))
WINDOWS=(
 (0x0224C690,1044,'851df7b044230b4d44656d2e35e3397c3427cdce5bac3596cc8a43fe73f6677d'),
 (0x0224CAA4,484,'894ff2f35859c45cf47fe0b3aa5219d2e49476c0520ef56c84b8e0e91a9c3ce0'),
 (0x0224C370,28,'e4d52c6eb6ac15976865d8d40d176a55b83146e331fe53d209b9a975544687a6'),
 (0x0223CF68,80,'8d9efd635e8881a0fa1d2dd3b215385189cbc1ae355f5f625675dad1eb043e24'),
 (0x0223A7E0,4,'891d3cdc1477795938fe6e206d0ccdafe27c04209f269b75fb1b1bae8bac2576'),
 (0x0223DCAC,52,'28aa63e6836d323aa1415f2b6d41a598fa6a1f4f6c7395202ad2262bf22051d6'),
 (0x0223E12C,52,'42688bb8f9f87eb5d71510070d1bca059dc27df1400c3a5056b73f9122a285a2'),
 (0x0223E160,160,'bff86419aa253a18fe5b644ecfb5c9368b544fcd550f9730e5c133132a0b1022'),
 (0x0223E200,44,'65412c32f380c4f93f9b3eed76700a172b22bc7c90b6a12e64fc8135a20cf90e'),
 (0x0223E22C,100,'d60c735a052a80ccc52110065e9f6ae7a33a33b30b7fc69ac8a7a2ae73ffe6c5'),
 (0x0223E3C4,176,'714ea25b09af1d51b4a59c2d6d0f76cad277a64350f73dacb6f8de5330cd5fa4'),
 (0x0223EC84,244,'040e66c2a107b90cd22c4f5348a1c68a04299463cf0bbe1305a477745ce5252e'),
 (0x0223F61C,280,'a7f12bf8f32501d420efbda71d72aefe7fc6ec7a0101f5df4c0d5dfe79695959'),
 (0x02245288,44,'6fad36264d0559c72610ca55a664478e1dd798b2ba5500161a4bedcbeb53b6bd'),
 (0x022454CC,28,'a011a588223980d418db69d854fa8d6e3f74df9cc64ba9f222fda3e1fe573820'),
 (0x022454E8,32,'c1fc0d9e631df66c579cad0dfc10878dcd1e80c9f316748723ecb63f59bdd116'),
 (0x02245508,16,'fb36e314d3ab7ecf20c16f366929554b0350f8fd94fc5850e17fd41a324e3bc8'),
 (0x02245528,880,'d9a24f35580eb26dce857d486003461899e97caeb095fc9de510fd7b61311609'),
 (0x0224768C,616,'3b906d1354a9766abf0902705ee7abb127ba5f624bfb988361cc930471fb9100'),
 (0x0224EC74,80,'252a44a70f4c6901f272fc03c99ba0496c072d8ba2ba0c3870055bebd166851a'),
 (0x02250C40,48,'1417bf4618b5bfb876a0e3af5a3a59b527869372c6ff951cc120d0289b3f57a2'),
 (0x02263B4C,356,'22f11a4696c951b40371c2918e4f31d8fe32726e77684e8f2e25aebaac5c7c2c'),
 (0x0223AB1C,22,'e5a2331c0fb343e525df7140120f041292275375185f6426a3d2bf29d76fad24'),
 (0x02261258,12,'158546468068659cba962ecbdf8708d22430c713db8e6a0141674534e80c86d4'),
 (0x022585A8,16,'86c393333854d2c8b21f6f5036deeb84b4b3db83569e64341118c336ee634fa2'),
 (0x020726C0,32,'da266f8eefce9cbb52a195196c3e0897cbc84b5af29871c7bd834fa3e8992a78'),
)
COMMANDS={14:0x0223DCAC,25:0x0223E12C,26:0x0223E160,27:0x0223E200,28:0x0223E22C,
 32:0x0223E3C4,50:0x0223EC84,57:0x0223F61C,215:0x02245288,224:0x022454CC}
# Store-site/field contracts for attacker0,target1. No other battler is admitted.
STORES={
 'hp':{0x224C710:(0x30F8,4),0x224C8F2:(0x30E8,4),0x224C908:(0x2E7C,1),
  0x224C930:(0x218,4),0x224C93C:(0x228,4),0x224C952:(0x22C,4),0x224C966:(0x2F4,4),
  0x224C974:(0x2F8,4),0x224CA44:(0x2EC,4),0x224CA54:(0x248,4),0x224CA60:(0x24C,4),
  0x224CA66:(0x118,4),0x224CA6C:(0x215C,4),0x224CA7A:(8,4),0x224CA7E:(12,4),0x224CA8C:(0x213C,4),0x224CA92:(8,4)},
 'script':{0x2245512:(0xB4,4),0x2245502:(0xB4,4),0x223DCD6:(0x3154,4),0x223CFAA:(0x3154,4),
  0x223ED16:(0x213C,4),0x223E1A0:(0x2148,4),0x223E1B6:(0x168,4),0x223E1CA:(0x2E4C,4),
  0x22585B2:(0x396,2),0x223F696:(0x250,4),0x22454D8:(0x3154,4),0x224C382:(0xB4,4),0x224C386:(8,4)},
 'after':{0x224CB86:(0x3C,4),0x224CC60:(0x3C,4),0x23D5A54:(0x2EC,4),0x224E0F8:(0x94,4),
  0x224E100:(0x88,4),0x224E110:(12,4),0x224E114:(8,4),0x224CC6E:(0x3C,4),0x224CC72:(8,4)}}


def resources(rom,model):
 r=F.read_resources(rom,model)
 spec=importlib.util.spec_from_file_location('hp_raw_archive',F.G.SOURCE/'features/borsa/tools/attribuisci.py')
 reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
 with Path(rom).open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:scripts,record=reader.raw_archive(raw,'a/0/0/1')
 need(sha(scripts[2])=='bf7ad08c8f82d1b33126bf3b11cddcf34f4e7fbd49beb2fe45d90b9f65bafe70' and len(scripts[2])==152,'whole HP subscript2 identity')
 r.update(hp_script=scripts[2]);r['record'].update(hp_script=dict(member=2,bytes=152,sha256=sha(scripts[2])))
 return r


class HPPathCPU(F.NativeFlinch):
 code_ranges=RANGES
 script_commands=COMMANDS
 script_variables=(6,32,66,69)
 script_words=38
 side_categories=(255,)

 def store_contract(self,phase):return STORES[phase]

 def model_context_ranges(self,phase):
  return ((0x2700,0x2798),(0xB4,0xB8)) if phase=='hp' else ()

 def __init__(self,model,data,*,variant='current'):
  need(variant in ('current','old_hooks'),'explicit HP path variant')
  super().__init__(model,data,variant=variant)
  need(sha(data['hp_script'])=='bf7ad08c8f82d1b33126bf3b11cddcf34f4e7fbd49beb2fe45d90b9f65bafe70','HP script fixture drift')
  for addr,n,digest in WINDOWS:
   raw=F.take(model['overlay'],addr,n) if addr>=F.U.OVERLAY_BASE else F.G.piece(model['segments'],addr,n)
   need(sha(raw)==digest,'HP path native window '+hex(addr))
  for op,addr in COMMANDS.items():need(F.take(model['overlay'],0x0226C6C8+4*op,4)==struct.pack('<I',addr|1),'HP native script dispatch')
  for slot,addr in ((22,RUN),(28,HP),(29,AFTER)):need(F.take(model['overlay'],0x0226CA90+4*slot,4)==struct.pack('<I',addr|1),'HP native controller dispatch')
  self.phase=None;self.all_runs=[]

 def _seam(self,u,address,size,unused):
  if address==STOP:u.emu_stop();return
  if address==F.C.READ_BATTLE_SCRIPT:
   args=[self.reg(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
   need(args[:2]==[CTX,1] and args[2] in (2,14),'HP script loader ABI/domain')
   if args[2]==2:
    need(self.phase=='hp','HP script load phase');u.mem_write(CTX+0x2700,self.resources['hp_script']);self._word(CTX+0xB4,0)
   else:need(self.phase=='after','flinch script load phase')
   self.current['models'].append(dict(name='NARC script loader',args=args));self._return(u,0);return
  # Real getters, RNG and division execute. Their inherited seam is disabled.

 def _code(self,u,address,size,unused):
  r=self.current
  if r is None:return
  args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
  models={0x0224ED48:'transport ready',0x0226346C:'flicker emit',0x02263488:'HP bar emit',0x02264228:'hit sound emit',0x02262240:'Party packet emit'}
  if address in models:
   name=models[address]
   if name=='transport ready':need(args[0]==CTX,'HP ready ABI')
   elif name=='Party packet emit':
    need(args[:3]==[BS,1,self.target] and self.word(self.reg(UC_ARM_REG_SP))==44,'HP Party packet ABI');r['packets'].append(sha(bytes(u.mem_read(args[3],44))))
    need(STACK-4096<=args[3] and args[3]+44<=STACK,'HP Party packet stack bounds')
    need(int.from_bytes(u.mem_read(args[3]+2,2),'little')==self.word(CTX+0x2D8C+192*self.target),'HP Party packet carries current HP')
   elif name=='flicker emit':need(args[:3]==[BS,self.target,0],'HP flicker ABI')
   else:need(args[:3]==[BS,CTX,self.target],'HP UI service ABI')
   r['models'].append(dict(name=name,args=args));self._return(u,1 if name=='transport ready' else 0);return
  if address==F.ABILITY:
   need(args[0]==CTX and args[1] in (self.attacker,self.target),'HP ability service ABI');r['models'].append(dict(name='ability',args=args,result=0));self._return(u,0);return
  if address==F.C.READ_BATTLE_SCRIPT:return
  extra=any(a<=address and address+size<=b for a,b in self.code_ranges)
  if extra:
   need(self.reg(UC_ARM_REG_CPSR)&32 and size in (2,4),'HP path Thumb ISA')
   r['instructions']+=1;need(r['instructions']<=20000,'HP path instruction budget');r['stack_depth']=max(r['stack_depth'],STACK-self.reg(UC_ARM_REG_SP));r['code'].add((address,size,True))
   if address==0x02245528:need(args[:2]==[BS,CTX] and args[2] in self.script_variables,'HP native variable pointer domain')
   if address in (0x022454E8,0x02245508):need(args[0]==CTX and 0<=self.word(CTX+0xB4)<self.script_words,'HP script cursor domain')
   if address==0x0224768C:need(args[:2]==[BS,CTX] and args[2] in self.side_categories,'HP native side selector domain')
   if address in self.script_commands.values():r['script_commands'].append(dict(pc=hex(address),cursor=self.word(CTX+0xB4),word=self.word(CTX+0x2EC+28*self.attacker)))
   if address==0x02250C40:need(args[:3]==[BS,CTX,self.target],'HP Party copy ABI')
   return
  # NativeFlinch checks a single getter battler; HpCalc queries its target.
  saved=self.attacker
  if self.phase=='hp':self.attacker=self.target
  try:super()._code(u,address,size,unused)
  finally:self.attacker=saved

 def _write(self,u,access,address,size,value,unused):
  if self.current is None:return
  stack=STACK-4096<=address and address+size<=STACK
  pc=self.reg(UC_ARM_REG_PC);field=self.store_contract(self.phase).get(pc)
  state=field is not None and (address,size)==(CTX+field[0],field[1])
  seed=self.rng_write_allowed(self.phase) and pc==0x0223BDA8 and address==BS+F.G.SEED_OFFSET and size==4
  need(stack or state or seed,'HP path write outside declared arenas '+hex(address))
  if not stack:self.current['writes'].append(dict(pc=hex(self.reg(UC_ARM_REG_PC)),address=hex(address),bytes=size,value=value))

 def guest_context_ranges(self,phase):
  return ()

 def rng_write_allowed(self,phase):
  return phase=='after'

 def execute_path(self,entry,phase):
  u=self.uc;u.mem_write(STACK-4104,b'\xA5'*8+bytes(4096)+b'\xA5'*256)
  for reg,value in zip(F.G.SAVED,F.G.COOKIES):u.reg_write(reg,value)
  for reg,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),(BS,CTX,0,0)):u.reg_write(reg,value)
  u.reg_write(UC_ARM_REG_SP,STACK);u.reg_write(UC_ARM_REG_LR,STOP|1)
  self.calls=dict(effect=0,modifier=0,rng=0,script=[])
  before_ctx=bytes(u.mem_read(CTX,0x4000));before_bs=bytes(u.mem_read(BS,0x3000));before_opp=bytes(u.mem_read(OPP,0x600))
  r=dict(phase=phase,instructions=0,stack_depth=0,item_queries=[],modifier_abi_issues=[],rng_calls=[],division_calls=[],cache_reads=[],models=[],code=set(),writes=[],packets=[],script_commands=[])
  self.phase=phase;self.current=r
  try:u.emu_start(entry|1,STOP,count=20001)
  finally:self.current=None;self.phase=None
  need(self.reg(UC_ARM_REG_PC)==STOP and self.reg(UC_ARM_REG_SP)==STACK and self.reg(UC_ARM_REG_CPSR)&32 and [self.reg(v) for v in F.G.SAVED]==F.G.COOKIES,'HP path outer return ABI')
  need(all(r.get(k) is None for k in ('pending_item','pending_rng','pending_div')),'HP unfinished native leaf')
  need(bytes(u.mem_read(STACK-4104,8))==b'\xA5'*8 and bytes(u.mem_read(STACK,256))==b'\xA5'*256,'HP stack/caller canary')
  need(all(bytes(u.mem_read(a,len(b)))==b for a,b in self.frozen),'HP path immutable code/data')
  need(bytes(u.mem_read(F.CACHE,len(self.cache)+8))==self.cache+b'\xA5'*8,'HP immutable item cache')
  allowed={i for off,n in self.store_contract(phase).values() for i in range(off,off+n)}
  for lo,hi in (*self.model_context_ranges(phase),*self.guest_context_ranges(phase)):allowed.update(range(lo,hi))
  need(all(a==b for i,(a,b) in enumerate(zip(before_ctx,bytes(u.mem_read(CTX,0x4000)))) if i not in allowed),'HP unrelated context changed')
  need(all(a==b for i,(a,b) in enumerate(zip(before_bs,bytes(u.mem_read(BS,0x3000)))) if not (self.rng_write_allowed(phase) and F.G.SEED_OFFSET<=i<F.G.SEED_OFFSET+4)),'HP unrelated battle system changed')
  need(bytes(u.mem_read(OPP,0x600))==before_opp,'HP opponent fixture changed')
  r.update(result=self.reg(UC_ARM_REG_R0),calls=dict(self.calls));r['code']=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(r['code'])];self.all_runs.append(r);return r

 def checkpoint(self):return dict(word=self.word(CTX+0x2EC),hp=self.word(CTX+0x2D8C+192*self.target),command=self.word(CTX+8),next=self.word(CTX+12),cursor=self.word(CTX+0xB4),physical_damage=self.word(CTX+0x2D8+28*self.target),seed=self.word(BS+F.G.SEED_OFFSET))

 def observe(self,*,damage=-200,eligible=True,message_type=0):
  need(type(damage) is int and -299<=damage<=0 and type(eligible) is bool and type(message_type) is int and message_type in (0,1),'HP path fixture domain')
  u=self.uc;u.mem_write(CTX,bytes(0x4000));u.mem_write(BS,bytes(0x3000));self.attacker=0;self.target=1
  u.mem_write(CTX+0x3DE,self.resources['move_cache']);self._word(CTX+0x2120,F.CACHE);self._word(CTX+0x64,0);self._word(CTX+0x6C,1)
  self._word(CTX+8,28);self._word(CTX+0x2144,damage);self._word(CTX+0x3044,33 if eligible else 44)
  self._word(CTX+0x2D8C+192,300);self._word(CTX+0x2D90+192,300)
  for b in (0,1):self._word(BS+0x34+4*b,OPP+0x300*b);u.mem_write(OPP+0x300*b+0x195,bytes((b,)))
  seed=((99<<16)-24691)*pow(1103515245,-1,1<<32)&0xFFFFFFFF;self._word(BS+F.G.SEED_OFFSET,seed)
  before=self.checkpoint();hp=self.execute_path(HP,'hp');after_hp=self.checkpoint();script_runs=[]
  while self.word(CTX+8)==22:
   need(len(script_runs)<8,'HP script return budget');script_runs.append(self.execute_path(RUN,'script'))
  after_script=self.checkpoint();need(after_script['command']==29,'HP native return to AfterDamage')
  # State6 is explicit input: states0..5 and their scripts are outside this case.
  self._word(CTX+0x38,message_type);self._word(CTX+0x3C,6)
  after=self.execute_path(AFTER,'after');end=self.checkpoint()
  return dict(before=before,after_hp=after_hp,after_script=after_script,after_damage=end,hp_run=hp,script_runs=script_runs,after_run=after,flinch=end['command']==22 and end['next']==29,variant=self.variant,damage=damage,eligible=eligible,message_type=message_type)


def compare_windows(model,current,role):
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 shift=int(model['record']['overlays'][1]['ram'],16)-F.U.OVERLAY_BASE
 records=[];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 for address,n,digest in WINDOWS:
  if address<F.U.OVERLAY_BASE:
   raw=F.G.piece(model['segments'],address,n);fields=[];actual=address;normal=raw
  else:
   actual=address+shift;raw=F.take(model['overlay'],address,n);normal=bytearray(raw);fields=[]
   if shift:
    reference=F.take(current['overlay'],address,n)
    for lo,hi in (*RANGES,(0x0223E25A,0x0223E282)):
     lo=max(lo,address);hi=min(hi,address+n)
     if lo>=hi:continue
     for ins in md.disasm(reference[lo-address:hi-address],lo):
      if ins.mnemonic in ('bl','blx') and ins.op_str.startswith('#'):
       target=int(ins.op_str.lstrip('#'),0)
       if target<F.U.OVERLAY_BASE:
        at=ins.address-address;field=raw[at:at+4]
        need(F.G.S.SHARED.branch(field,ins.address+shift,ins.mnemonic)==target,'regional native call target')
        need(F.G.piece(model['segments'],target,32)==F.G.piece(current['segments'],target,32),'regional ARM9 target entry identity')
        normal[at:at+4]=reference[at:at+4];fields.append(dict(offset=hex(at),target=hex(target),kind=ins.mnemonic))
    for site,target in ((0x0223CFB0,0x0226C6C8),(0x022454E4,0x0224EC75)):
     if address<=site and site+4<=address+n:
      at=site-address;need(struct.unpack_from('<I',raw,at)[0]==target+shift,'regional script pointer literal')
      if target==0x0226C6C8:
       for op,entry in COMMANDS.items():need(F.take(model['overlay'],target+4*op,4)==struct.pack('<I',(entry+shift)|1),'regional script dispatch target')
      else:need(F.take(model['overlay'],target&~1,8)==F.take(current['overlay'],target&~1,8),'regional script return entry signature')
      normal[at:at+4]=reference[at:at+4];fields.append(dict(offset=hex(at),target=hex(target+shift),kind='verified pointer literal'))
  need(sha(normal)==digest,'HP complete native correspondence '+role+' '+hex(address))
  records.append(dict(ram=hex(actual),bytes=n,sha256=sha(raw),comparison_only_fields=fields))
 return records


def require_chain(result):
 damage=result['damage'];word=damage&0xFFFFFFFF
 need(result['before']['word']==0 and result['before']['physical_damage']==0,'HP writer initial state')
 need(result['after_hp']['word']==word and result['after_hp']['physical_damage']==word,'native HP writer outputs')
 need(result['after_script']['hp']==300+damage and result['after_script']['word']==word,'native HP script changed shared damage word')
 need(result['after_script']['command']==29 and result['after_script']['seed']==result['before']['seed'],'native HP return/RNG neutrality')
 if damage:
  commands=[(x['pc'],x['cursor']) for run in result['script_runs'] for x in run['script_commands']]
  expected=[(hex(COMMANDS[op]),cursor) for op,cursor in ((32,0),(215,5),(25,7),(14,9),(32,10),(50,17),(27,21),(14,23),(26,24),(28,26),(32,28),(57,33),(224,37))]
  need(commands==expected and len(result['script_runs'])==3,'HP actual script path/dispatch')
  need(sum(len(run['packets']) for run in result['script_runs'])==1,'HP actual Party packet emission')
 else:need(not result['script_runs'],'zero damage unexpectedly ran HP script')
 expected=result['variant']=='current' and damage==-200 and result['eligible']
 rng_expected=result['variant']=='current' and damage==-200
 need(result['flinch']==expected and result['after_run']['calls']['rng']==int(rng_expected),'native HP→flinch outcome')
 need(result['after_damage']['word']==(0 if result['variant']=='current' and damage else word),'HP final shared word lifetime')
 need(result['after_damage']['seed']==(F.G.next_seed(result['before']['seed']) if rng_expected else result['before']['seed']),'HP complete RNG transition')
 need(result['after_damage']['command']==(22 if expected else 31),'HP AfterDamage final command')


def analyze(rom,v4,base,retail,language):
 import gc
 current=F.G.S.SHARED.read_current(rom,language);data=resources(rom,current)
 inputs=[];window_records=[]
 for role,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom)):
  model=current if role=='r4' else F.G.S.SHARED.read_image(path,language,role)
  window_records.append(dict(input=role,windows=compare_windows(model,current,role)))
  inputs.append(model['record']);del model;gc.collect()
 runs=[]
 for name,options in (('damage200',{}),('damage199',dict(damage=-199)),('zero_damage',dict(damage=0)),('Bite_ineligible',dict(eligible=False)),('message_type1',dict(message_type=1))):
  result=HPPathCPU(current,data).observe(**options);require_chain(result);runs.append(dict(name=name,result=result));gc.collect()
 old=HPPathCPU(F.counter_image(current,'old_hooks'),data,variant='old_hooks').observe();require_chain(old)
 return dict(schema='hp-flinch-source-rom-v1',language=language,inputs=inputs,window_records=window_records,resources=data['record'],runs=runs,native_baseline=old,
  compatibility_gates=dict(native_damage_writer=True,native_hp_script_preserves_word=True,current_no_item_flinch=False),compilation_performed=False,
  source_sha256={str(p.relative_to(F.G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(F.__file__),F.U.NATIVE)},
  limits=['Unicorn initialized fixtures: HpCalc full entry→RunScript/native script dispatch→AfterDamage full entry with explicit state6; not a naturally played battle',
   'AfterDamage states0..5, other scripts/callbacks and their lifetime are not executed; state6 is an explicit controlled continuation',
   'NARC script loading, ability0, UI emission, ready/queue success and Party packet transport are ABI checked service models; native wrapper/emitter execute, asynchronous consumer does not',
   'Native item cache preparation and source-word U-turn producer are outside this case; ordinary nonpivot fixture uses actual raw item0 and Tackle33/Bite44',
   'No original native compiler/object reconstruction; own U-turn source/object correspondence is provided by preceding case',
   'No ROM/save mutation, game repair, graphics, wall-clock timing, full battle, SAVE, cold restart or device claim'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 for path in (args.rom,args.v4,args.base,args.retail):
  if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input')
 result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
 args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
 print(args.language,'native HP writer/script→AfterDamage state6 verified; no-item flinch compatibility FAIL; no game fix')
 raise SystemExit(1)


if __name__=='__main__':main()
