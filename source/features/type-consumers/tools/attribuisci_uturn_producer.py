#!/usr/bin/env python3
"""Execute the installed U-turn snapshot commands in a bounded native VM fixture."""
import importlib.util,json,struct
from pathlib import Path
spec=importlib.util.spec_from_file_location('producer_native_vm',Path(__file__).with_name('attribuisci_hp_flinch.py'))
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
F=H.F
need,sha=F.need,F.sha
CTX,BS,STACK,STOP=H.CTX,H.BS,H.STACK,H.STOP
resources=H.resources
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP
PRODUCER_COMMANDS={50:0x0223EC84,57:0x0223F61C,59:0x0223F894,166:0x0224428C,168:0x02244344,224:0x022454CC}
PRODUCER_WINDOWS=((0x0224428C,108,'0c4f06f4eb9797ff72d01c3005445fa219c41459cdb3ea27cd7bb088b062dc7a'),
 (0x02244344,76,'b007656dca26bd28b6100c88067ea07bc91d4d07c72d74f975a37baf243c281d'),
 (0x0223F894,32,'69f5a232eaef629793d981c254a7370de6188abe36e58a0c3afff95dd138c3ec'))
SENTINEL=0x5A5A5A5A


def script_fixture(raw,variant='current'):
 need(type(raw) is bytes and len(raw)==800 and sha(raw)==F.SCRIPT.AFTER_SHA256,'whole pivot member identity')
 need(raw[0x3C:0xA4]==F.SCRIPT.INSERT and variant in ('current','wrong_shift'),'explicit pivot fixture variant/prefix')
 result=bytearray(raw);struct.pack_into('<I',result,41*4,224)
 if variant=='wrong_shift':
  need(struct.unpack_from('<I',result,0x3C+21*4)[0]==8,'wrong-shift preimage');struct.pack_into('<I',result,0x3C+21*4,9)
 need(all(a==b for i,(a,b) in enumerate(zip(raw,result)) if not (164<=i<168 or variant=='wrong_shift' and 144<=i<148)),'pivot fixture changed complement')
 return bytes(result)


class ProducerCPU(H.HPPathCPU):
 code_ranges=H.RANGES+((0x0223F894,0x0223F8B2),(0x0224428C,0x022442F8),(0x02244344,0x0224438E),
  (0x02247698,0x022476A8),(0x022476DC,0x022476E0))
 script_commands=PRODUCER_COMMANDS
 script_variables=(9,68)
 script_words=200
 side_categories=(1,)

 def __init__(self,model,data,*,fixture_variant='current'):
  super().__init__(model,data)
  for a,n,d in PRODUCER_WINDOWS:need(sha(F.take(model['overlay'],a,n))==d,'native producer whole handler')
  for op,a in PRODUCER_COMMANDS.items():need(F.take(model['overlay'],0x0226C6C8+op*4,4)==struct.pack('<I',a|1),'native producer dispatch')
  for var,entry in ((9,0x02245602),(68,0x02245810)):
   relative=struct.unpack('<h',F.take(model['overlay'],0x0224553E+var*2,2))[0];need(0x02245540+relative==entry,'native producer variable case')
  need(struct.unpack('<h',F.take(model['overlay'],0x022476AA,2))[0]+0x022476AA==0x022476DC,'native producer side1 case')
  self.fixture_variant=fixture_variant;self.script=script_fixture(data['script'],fixture_variant)

 def store_contract(self,phase):
  if phase!='script':return super().store_contract(phase)
  word=0x2EC+28*self.attacker
  return {0x2245512:(0xB4,4),0x2245502:(0xB4,4),0x223ECF0:(word,4),0x223ED08:(word,4),
   0x2244388:(0x134,4),0x223ED34:(0x134,4),0x223F6B4:(word,4),
   0x22454D8:(0x3154,4),0x223CFAA:(0x3154,4),0x224C382:(0xB4,4),0x224C386:(8,4)}

 def _seam(self,u,address,size,unused):
  if self.phase is None:return F.NativeFlinch._seam(self,u,address,size,unused)
  return super()._seam(u,address,size,unused)

 def _write(self,u,access,address,size,value,unused):
  if self.phase is None:return F.NativeFlinch._write(self,u,access,address,size,value,unused)
  return super()._write(u,access,address,size,value,unused)

 def _code(self,u,address,size,unused):
  if self.phase is None:return F.NativeFlinch._code(self,u,address,size,unused)
  call=self.current.get('pending_item')
  if call and address==call['return_pc'] and address==0x02244388:
   need(self.reg(UC_ARM_REG_SP)==call['sp'] and [self.reg(v) for v in F.G.SAVED]==call.pop('saved'),'native producer item return ABI')
   call['value']=self.reg(UC_ARM_REG_R0)
   need(call['value']==self.cache[36*call['member']+call['attribute']+1],'native producer item parameter result')
   self.current['item_queries'].append(call);self.current['pending_item']=None
  if address==F.ABILITY:
   need([self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1)]==[CTX,self.attacker],'producer ability ABI')
   self.current['models'].append(dict(name='ability',result=self.active_ability));self._return(u,self.active_ability);return
  if address in (0x022454E8,0x02245508):need(15<=self.word(CTX+0xB4)<=41,'producer cursor left bounded insertion')
  return super()._code(u,address,size,unused)

 def observe(self,*,outgoing=221,incoming=0,klutz=False,embargo=False,attacker=0,roll=9,calc_temp=SENTINEL):
  need(type(outgoing) is int and outgoing in (0,221,327) and type(incoming) is int and incoming in (0,221,327),'producer item fixture domain')
  need(type(klutz) is bool and type(embargo) is bool and type(attacker) is int and 0<=attacker<4 and type(roll) is int and 0<=roll<100,'producer state fixture domain')
  need(type(calc_temp) is int and 0<=calc_temp<=0xFFFFFFFF,'producer CalcTemp fixture domain')
  u=self.uc;u.mem_write(CTX,bytes(0x4000));u.mem_write(BS,bytes(0x3000));self.attacker=attacker;self.target=(attacker+1)%4
  u.mem_write(CTX+0x3DE,self.resources['move_cache']);self._word(CTX+0x2120,F.CACHE);self._word(CTX+0x64,attacker);self._word(CTX+0x6C,self.target)
  self._word(CTX+8,22);self._word(CTX+12,29);self._word(CTX+0x3044,33);self._word(CTX+0x2D8+28*self.target,1);self._word(CTX+0x2D8C+192*self.target,100)
  self._word(CTX+0x2DB8+192*attacker,outgoing);self._word(CTX+0x2DCC+192*attacker,(1<<19) if embargo else 0);self.active_ability=103 if klutz else 0
  self._word(CTX+0x134,calc_temp);self._word(CTX+0x2EC+28*attacker,-200)
  u.mem_write(CTX+0x2700,self.script);self._word(CTX+0xB4,15)
  seed=((roll<<16)-24691)*pow(1103515245,-1,1<<32)&0xFFFFFFFF;self._word(BS+F.G.SEED_OFFSET,seed)
  producer=self.execute_path(H.RUN,'script');snapshot=self.word(CTX+0x2EC+28*attacker);temp_after=self.word(CTX+0x134)
  need(bytes(u.mem_read(CTX+0x2700,800))==self.script,'producer mutated bounded script fixture')
  need(self.word(BS+F.G.SEED_OFFSET)==seed and not producer['rng_calls'],'producer RNG neutrality')
  need(self.word(CTX+8)==29 and self.word(CTX+0xB4)==0,'producer native VM return')
  self._word(CTX+0x2DB8+192*attacker,incoming);self._word(CTX+0x2DCC+192*attacker,0);self.active_ability=0
  consumer=self.repeat_parent();repeat=self.repeat_parent()
  return dict(outgoing=outgoing,incoming=incoming,klutz=klutz,embargo=embargo,attacker=attacker,roll=roll,calc_temp_before=calc_temp,calc_temp_after=temp_after,
   fixture_variant=self.fixture_variant,raw_member_sha256=sha(self.resources['script']),fixture_sha256=sha(self.script),snapshot=snapshot,producer=producer,consumer=consumer,repeat=repeat)


def require_producer(result):
 effective=result['outgoing'] in (221,327) and not result['klutz'] and not result['embargo']
 need(result['snapshot']==(0x10A38 if effective else 0x10000),'native producer snapshot differs from exact packing')
 need(result['calc_temp_after']==(0xA00 if effective else result['calc_temp_before']),'native producer CalcTemp lifetime')
 command_path=((50,15),(166,19),(50,26),(168,30),(50,33),(57,37),(224,41)) if effective else ((50,15),(166,19),(59,24),(224,41))
 need([(c['pc'],c['cursor']) for c in result['producer']['script_commands']]==[(hex(PRODUCER_COMMANDS[op]),cursor) for op,cursor in command_path],'actual native snapshot command path')
 need(result['producer']['calls']['modifier']==0 and result['producer']['calls']['effect']==1,'producer native callgraph, not semantic modifier substitution')
 need(not result['producer']['modifier_abi_issues'] and not result['producer']['rng_calls'],'producer introduced ABI/RNG change')
 consumer=result['consumer'];repeat=result['repeat'];flinch=effective and result['roll']<10
 need(consumer['snapshot_before']==result['snapshot'] and consumer['snapshot_after']==0 and consumer['flinch']==flinch,'native producer→consumer outcome/lifetime')
 need(not consumer['modifier_abi_issues'] and consumer['calls']['effect']==consumer['calls']['modifier']==0,'marked consumer unexpectedly used live item')
 need(consumer['calls']['rng']==int(effective),'marked consumer RNG count')
 need(repeat['snapshot_before']==repeat['snapshot_after']==0 and not repeat['flinch'] and repeat['modifier_abi_issues'],'repeat did not expose recorded unmarked fallback ABI defect')
 need(repeat['calls']['rng']==int(result['incoming'] in (221,327)),'repeat native fallback RNG count')


def compare_producer_windows(model,current,role):
 shift=int(model['record']['overlays'][1]['ram'],16)-F.U.OVERLAY_BASE
 records=[]
 for a,n,digest in PRODUCER_WINDOWS:
  raw=F.take(model['overlay'],a,n);need(sha(raw)==digest,'native producer inherited handler '+role)
  records.append(dict(ram=hex(a+shift),bytes=n,sha256=digest))
 for op,a in PRODUCER_COMMANDS.items():need(F.take(model['overlay'],0x0226C6C8+4*op,4)==struct.pack('<I',(a+shift)|1),'native producer regional command table')
 return records


def analyze(rom,v4,base,retail,language):
 import gc
 current=F.G.S.SHARED.read_current(rom,language);data=resources(rom,current);inputs=[];windows=[]
 for role,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom)):
  model=current if role=='r4' else F.G.S.SHARED.read_image(path,language,role)
  windows.append(dict(input=role,vm_windows=H.compare_windows(model,current,role),producer_windows=compare_producer_windows(model,current,role)))
  inputs.append(model['record']);del model;gc.collect()
 runs=[]
 cases=(('rock',{}),('fang',dict(outgoing=327)),('empty_incoming_rock',dict(outgoing=0,incoming=221)),
  ('klutz',dict(klutz=True)),('embargo',dict(embargo=True)),('attacker3',dict(attacker=3)),('roll10',dict(roll=10)))
 for name,options in cases:
  result=ProducerCPU(current,data).observe(**options);require_producer(result);runs.append(dict(name=name,result=result));gc.collect()
 counter=ProducerCPU(current,data,fixture_variant='wrong_shift').observe()
 need(counter['consumer']['flinch']==runs[0]['result']['consumer']['flinch'],'wrong-shift same-output counter')
 try:require_producer(counter)
 except ValueError as e:counter['oracle_rejected']=str(e)
 else:raise ValueError('false producer packing success')
 return dict(schema='uturn-native-producer-v1',language=language,inputs=inputs,windows=windows,resources=data['record'],runs=runs,wrong_shift_counter=counter,
  compilation_performed=False,producer_attribution=True,compatibility_gates=dict(producer_exact_packing=True,producer_rng_neutral=True,repeat_fallback_abi=False),
  source_sha256={str(p.relative_to(F.G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(H.__file__),Path(F.__file__),Path(F.SCRIPT.__file__),F.U.NATIVE)},
  limits=['Native VM fixture starts at word15 of raw800-byte member175; only word41 is replaced with synthetic End224 in private RAM; original prefix/switch continuation is not executed',
   'Ability query and item-cache preparation are explicit models, raw item/move data and native item getter/decoder code execute',
   'Native producer→consumer is separated by a controlled item/ability replacement, not the actual pivot switch/callback transport',
   'Repeat records the installed fallback ABI failure; both preceding compatibility defects remain unfixed',
   'No natural battle, earlier AfterDamage0..5, asynchronous PartyMon write, SAVE, cold restart, hardware or timing claim'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 for path in (args.rom,args.v4,args.base,args.retail):
  if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input')
 result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
 args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
 print(args.language,'native producer packing verified; repeat fallback ABI compatibility FAIL; no game fix')
 raise SystemExit(1)


if __name__=='__main__':main()
