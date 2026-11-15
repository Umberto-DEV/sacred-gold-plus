#!/usr/bin/env python3
"""Execute native flinch script14 after the actual AfterDamage request."""
import importlib.util,json,mmap,struct
from pathlib import Path
spec=importlib.util.spec_from_file_location('effect_after_native',Path(__file__).with_name('attribuisci_afterdamage.py'))
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
H,F=A.H,A.F
need,sha=F.need,F.sha
CTX,BS,STACK,STOP=A.CTX,A.BS,A.STACK,A.STOP
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_CPSR
SCRIPT_SHA='8cd5d72da2f91298d0c14a1e5fb816bfeafbf71a2b382c8c23430868d1ec544a'
WINDOWS=((0x0224424C,64,'0765895ccb2e66d8802464e44c60514c838ad2e49ae5148ea610066bae5528e3'),
 (0x0224514C,92,'aab8ea753da6bcda70bf670b4f23b68b56ac34f1d7c74994005b8023df80c2e5'),
 (0x02243F18,296,'3de36b1bf860dcae3d55644b9ff4c378015dc46267788db9f4540948c045bf2f'),
 (0x0223F38C,292,'4a90032db69d8197adbf83556e685e3c22c91b7dbe0ab3fefe7e98b826658f45'),
 (0x022527CC,104,'07b2a41710a1dfe99de465ea1be3ea9f735993ea683e63c348692aaaa2191198'),
 (0x02252834,92,'836d84899d905d841cd0615d758205afa6fc25908f7780e0229dd92d9802cffd'),
 (0x0225561C,24,'eb413562c7acc3e7399439746c34b7b48f97c4d9e0f57d327309faeaf2985082'))
COMMANDS={**A.AfterCPU.script_commands,165:0x0224424C,210:0x0224514C,161:0x02243F18,52:0x0223F38C}

EXTRA_WINDOWS=(
 (0x0224EFD2,4,'50b668dc63f7ae34db1b74f23964766b8a5df5809a0f74cb280d338875c45bac'),
 (0x0224F168,36,'bbd38701513502e2643947d484dea3da30549d154070e3be90fa921c78441966'),
 (0x0224F3DE,6,'e00442a2b6261382c2badf0c2276d9cc23fc62494a8997ca8d28884b65eee8e6'),
)


def read_effect(rom):
 spec=importlib.util.spec_from_file_location('effect_raw_archive',F.G.SOURCE/'features/borsa/tools/attribuisci.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
 with Path(rom).open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:members,record=reader.raw_archive(raw,'a/0/0/1')
 need(record['file_id']==130 and len(members)==297 and len(members[14])==224 and sha(members[14])==SCRIPT_SHA,'flinch raw script identity/geometry')
 return members[14]


def resources(rom,model):
 data=A.resources(rom,model);data['subscripts'][14]=read_effect(rom);data['record']['flinch_script']=dict(member=14,bytes=224,sha256=SCRIPT_SHA)
 return data


class EffectCPU(A.AfterCPU):
 code_ranges=A.AfterCPU.code_ranges+((0x0224424C,0x0224428C),(0x0224514C,0x022451A4),
  (0x02243F18,0x02244036),(0x0223F38C,0x0223F3E6),(0x0223F410,0x0223F4AE),
  (0x022527CC,0x02252830),(0x02252834,0x0225288A),(0x0225561C,0x02255630),
  (0x022476EC,0x022476F2),(0x0224EFD2,0x0224EFD6),(0x0224F168,0x0224F18C),(0x0224F3DE,0x0224F3E4))
 script_commands=COMMANDS
 script_variables=(*A.AfterCPU.script_variables,5,10,24)
 side_categories=(*A.AfterCPU.side_categories,7)

 def __init__(self,model,data,*,variant='current',fixture_variant='current'):
  super().__init__(model,data,variant=variant)
  for a,n,d in (*WINDOWS,*EXTRA_WINDOWS):need(sha(F.take(model['overlay'],a,n))==d,'flinch effect whole native dependency')
  need(sha(data['subscripts'][14])==SCRIPT_SHA and fixture_variant in ('current','wrong_mask'),'flinch effect fixture identity/variant')
  for op,a in COMMANDS.items():need(F.take(model['overlay'],0x0226C6C8+4*op,4)==struct.pack('<I',a|1),'flinch effect command dispatch')
  need(struct.unpack('<h',F.take(model['overlay'],0x0224EE02+2*53,2))[0]+0x0224EE04==0x0224EFD2,'native status getter case53')
  need(struct.unpack('<h',F.take(model['overlay'],0x0224F18C+2*53,2))[0]+0x0224F18E==0x0224F3DE,'native status setter case53')
  need(struct.unpack('<h',F.take(model['overlay'],0x022476A8+2*7,2))[0]+0x022476AA==0x022476EC,'native side7 case')
  need(struct.unpack('<h',F.take(model['overlay'],0x0224553E+2*5,2))[0]+0x02245540==0x022455E8,'native effect-type variable case5')
  self.pending_abilities=[];self.fixture_variant=fixture_variant

 def prepare_fixture(self):
  self.uc.mem_write(CTX+0x2D67,bytes((65,)));self.uc.mem_write(CTX+0x2D67+192,bytes((self.target_ability,)))
  self._word(CTX+0x2DB0+192,self.base_status);self._word(CTX+0x21A8+16,40 if self.already_acted else 0)
  self._word(CTX+0x2E8+28,8 if self.substitute_hit else 0)

 def store_contract(self,phase):
  result=dict(super().store_contract(phase))
  if phase=='script':
   result[0x0224F3E0]=(0x2DB0+192*self.target,4)
   result[0x02244002]=(0x80,4)
  return result

 def _seam(self,u,address,size,unused):
  script=self.reg(UC_ARM_REG_R2) if address==F.C.READ_BATTLE_SCRIPT else None
  super()._seam(u,address,size,unused)
  if script==14:
   data=bytearray(self.resources['subscripts'][14])
   if self.fixture_variant=='wrong_mask':
    need(struct.unpack_from('<I',data,100)[0]==8,'flinch mask counter preimage');struct.pack_into('<I',data,100,16)
   self.current_script=14;u.mem_write(CTX+0x2700,bytes(data));self._word(CTX+0xB4,0)

 def _code(self,u,address,size,unused):
  r=self.current
  if r is None:return
  if self.pending_abilities and address==self.pending_abilities[-1]['return_pc']:
   call=self.pending_abilities.pop();need(self.reg(UC_ARM_REG_SP)==call['sp'] and [self.reg(v) for v in F.G.SAVED]==call.pop('saved'),'native ability return ABI')
   call['value']=self.reg(UC_ARM_REG_R0)
   expected=call['expected'];need(call['value']==expected,'native ability result in bounded fixture')
   r.setdefault('native_ability_calls',[]).append(call)
  args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
  if address in (0x022527CC,0x02252834):
   need(self.reg(UC_ARM_REG_CPSR)&32 and size in (2,4),'native ability Thumb entry')
   if address==0x022527CC:
    need(args[0]==CTX and args[1] in (0,1),'native ability lookup ABI')
    expected=65 if args[1]==0 else self.target_ability
   else:
    need(args[:3]==[CTX,0,1] and args[3] in (19,39),'native ignorable ability ABI')
    expected=int(self.target_ability==args[3])
   self.pending_abilities.append(dict(ram=hex(address),args=args,expected=expected,return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=self.reg(UC_ARM_REG_SP),saved=[self.reg(v) for v in F.G.SAVED]))
   r['instructions']+=1;r['stack_depth']=max(r['stack_depth'],STACK-self.reg(UC_ARM_REG_SP));r['code'].add((address,size,True));return
  if address==0x0224EDE0 and args[2]==53:
   need(args==[CTX,self.target,53,0],'native status getter ABI/null pointer');return H.HPPathCPU._code(self,u,address,size,unused)
  if address==0x02256838:
   need(args[:2]==[CTX,self.target],'native substitute lookup ABI');return H.HPPathCPU._code(self,u,address,size,unused)
  if address==0x0224F168:
   need(args[:3]==[CTX,self.target,53] and STACK-4096<=args[3]<=STACK-4 and args[3]%4==0,'native status setter ABI/stack pointer')
  return super()._code(u,address,size,unused)

 def execute_path(self,entry,phase):
  result=super().execute_path(entry,phase);need(not self.pending_abilities,'unfinished native ability call');return result

 def observe(self,*,target_ability=67,already_acted=False,substitute_hit=False,base_status=0x400,damage=-200,eligible=True,message_type=0):
  need(type(target_ability) is int and target_ability in (67,39,19) and type(already_acted) is bool and type(substitute_hit) is bool,'effect ability/action fixture domain')
  need(type(base_status) is int and base_status in (0,0x400),'effect unrelated-status fixture domain')
  self.target_ability=target_ability;self.already_acted=already_acted;self.substitute_hit=substitute_hit;self.base_status=base_status
  continuation=super().observe(damage=damage,eligible=eligible,message_type=message_type);A.require_continuation(continuation)
  before=self.word(CTX+0x2DB0+192);attacker_before=self.word(CTX+0x2DB0);seed_before=self.word(BS+F.G.SEED_OFFSET);effects=[]
  if continuation['flinch']:
   need(self.word(CTX+0x94)==1 and self.word(CTX+0x88)==2 and self.current_script==14,'actual parent effect target/type continuity')
   for _ in range(8):
    if self.word(CTX+8)!=22:break
    effects.append(self.execute_path(H.RUN,'script'))
   else:raise ValueError('flinch effect script resume budget')
  return dict(continuation=continuation,target_ability=target_ability,already_acted=already_acted,substitute_hit=substitute_hit,base_status=base_status,status_before=before,status_after=self.word(CTX+0x2DB0+192),attacker_before=attacker_before,attacker_after=self.word(CTX+0x2DB0),
   seed_before=seed_before,seed_after=self.word(BS+F.G.SEED_OFFSET),effects=effects,fixture_variant=self.fixture_variant,final_command=self.word(CTX+8),shared_word=self.word(CTX+0x2EC),effect_script_sha256=sha(bytes(self.uc.mem_read(CTX+0x2700,224))) if effects else None)


def require_effect(result):
 continuation=result['continuation'];A.require_continuation(continuation)
 requested=continuation['flinch'];allowed=requested and result['target_ability']==67 and not result['already_acted'] and not result['substitute_hit']
 need(result['status_before']==result['base_status'] and result['status_after']==(result['base_status']|8 if allowed else result['base_status']),'native flinch bit/preserved status differs')
 need(result['attacker_before']==result['attacker_after']==0,'effect changed wrong battler')
 need(result['seed_before']==result['seed_after']==continuation['final']['seed'],'effect script unexpectedly consumed RNG')
 need(result['shared_word']==continuation['final_word'],'effect script changed consumed native damage word')
 runs=[x['run'] for x in continuation['runs']]+result['effects']
 need(not any(m['name']=='ability' for r in runs for m in r['models']),'native ability lookup replaced with model')
 need(any(r.get('native_ability_calls') for r in runs),'native ability closure was not executed')
 if not requested:
  need(not result['effects'] and result['final_command']==31,'effect ran without script14 request');return
 need(len(result['effects'])==1 and result['final_command']==29,'native effect script return/resume')
 need(result['effect_script_sha256']==SCRIPT_SHA,'effect script RAM fixture drift')
 if result['already_acted']:path=((165,0),(224,26))
 elif result['substitute_hit']:path=((165,0),(210,3),(32,46),(224,55))
 elif result['target_ability']==39:path=((165,0),(210,3),(161,6),(32,27),(32,32),(224,45))
 elif result['target_ability']==19:path=((165,0),(210,3),(161,6),(32,11),(161,16),(224,26))
 else:path=((165,0),(210,3),(161,6),(32,11),(161,16),(52,21),(224,26))
 need([(c['pc'],c['cursor']) for r in result['effects'] for c in r['script_commands']]==[(hex(COMMANDS[op]),cursor) for op,cursor in path],'native effect script gate path')
 writes=[w for r in result['effects'] for w in r['writes'] if w['pc']=='0x224f3e0']
 need(writes==([dict(pc='0x224f3e0',address=hex(CTX+0x2DB0+192),bytes=4,value=result['base_status']|8)] if allowed else []),'native status setter store/value')


def compare_native(model,current,role):
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 shift=int(model['record']['overlays'][1]['ram'],16)-F.U.OVERLAY_BASE;records=[];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 for a,n,digest in (*WINDOWS,*EXTRA_WINDOWS):
  raw=F.take(model['overlay'],a,n);normal=bytearray(raw);fields=[]
  if shift:
   ref=F.take(current['overlay'],a,n)
   for lo,hi in EffectCPU.code_ranges[len(A.AfterCPU.code_ranges):]:
    lo=max(lo,a);hi=min(hi,a+n)
    if lo>=hi:continue
    for ins in md.disasm(ref[lo-a:hi-a],lo):
     if ins.mnemonic in ('bl','blx') and ins.op_str.startswith('#'):
      target=int(ins.op_str[1:],0)
      if target<F.U.OVERLAY_BASE:
       at=ins.address-a;need(F.G.S.SHARED.branch(raw[at:at+4],ins.address+shift,ins.mnemonic)==target,'effect regional native call')
       need(F.G.piece(model['segments'],target,32)==F.G.piece(current['segments'],target,32),'effect regional ARM9 target entry')
       normal[at:at+4]=ref[at:at+4];fields.append(dict(offset=hex(at),target=hex(target)))
  need(sha(normal)==digest,'effect native full window '+role+' '+hex(a));records.append(dict(ram=hex(a+shift),bytes=n,sha256=sha(raw),comparison_only_fields=fields))
 return records


def analyze(rom,v4,base,retail,language):
 import gc
 current=F.G.S.SHARED.read_current(rom,language);data=resources(rom,current);inputs=[];windows=[];lineage=[]
 for role,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom)):
  model=current if role=='r4' else F.G.S.SHARED.read_image(path,language,role)
  windows.append(dict(input=role,vm=H.compare_windows(model,current,role),after=A.compare_native(model,current,role),effect=compare_native(model,current,role)))
  script=read_effect(path);lineage.append(dict(input=role,member=14,bytes=224,sha256=sha(script)));inputs.append(model['record']);del model;gc.collect()
 runs=[]
 for name,options in (('torrent',{}),('zero_other_status',dict(base_status=0)),('inner_focus',dict(target_ability=39)),('shield_dust',dict(target_ability=19)),('already_acted',dict(already_acted=True)),('substitute_hit',dict(substitute_hit=True)),('Bite_ineligible',dict(eligible=False))):
  result=EffectCPU(current,data).observe(**options);require_effect(result);runs.append(dict(name=name,result=result));gc.collect()
 old=EffectCPU(F.counter_image(current,'old_hooks'),data,variant='old_hooks').observe();require_effect(old)
 counter=EffectCPU(current,data,fixture_variant='wrong_mask').observe();need(counter['continuation']['flinch'] and counter['final_command']==29,'same-request/completed-script mask counter')
 try:require_effect(counter)
 except ValueError as e:counter['oracle_rejected']=str(e)
 else:raise ValueError('false native flinch effect success')
 return dict(schema='flinch-native-effect-v1',language=language,inputs=inputs,windows=windows,script_lineage=lineage,resources=data['record'],runs=runs,native_baseline=old,wrong_mask_counter=counter,
  compilation_performed=False,compatibility_gates=dict(native_effect_application=True,native_effect_guards=True,no_item_flinch_bit=False),
  source_sha256={str(p.relative_to(F.G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(A.__file__),Path(H.__file__),F.U.NATIVE)},
  limits=['Initialized HpCalc/AfterDamage→script14→BMonstatus2 bit3 is executed, not a naturally played move or observed lost turn',
   'Native GetBattlerAbility and CheckIgnorableAbility execute for attacker65/target67,39,19; MoldBreaker/suppression/gravity/ingrain/other abilities remain outside this fixture',
   'NARC loading, UI/Ready, item-cache preparation and asynchronous Party packet transport remain models; actual BMon setter/wrapper/emitter execute, PartyMon encrypted consumer does not',
   'Substitute-hit is an explicit initial SelfTurnData flag fixture, not a claim that a naturally played Tackle produced it',
   'No full pivot, native turn-loss consumer, SAVE, cold restart, hardware, timing or game repair claim'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 for path in (args.rom,args.v4,args.base,args.retail):
  if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input')
 result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
 args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
 print(args.language,'native flinch script/ability gates/status bit verified; no-item status compatibility FAIL; turn loss not executed')
 raise SystemExit(1)


if __name__=='__main__':main()
