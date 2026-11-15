#!/usr/bin/env python3
"""Dispatch the remaining native action after actual flinch completion."""
import importlib.util,struct
from pathlib import Path
spec=importlib.util.spec_from_file_location('next_action_end_native',Path(__file__).with_name('attribuisci_actionend.py'))
D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
F,H=D.F,D.H
need,sha=D.need,D.sha
CTX,BS,STACK,STOP=D.CTX,D.BS,D.STACK,D.STOP
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_CPSR,UC_ARM_REG_PC
NEXT,FIGHT,SORT,CHECK_SPEED,CHECK_ABILITY,TARGET=0x02249460,0x0224A9B0,0x02252D3C,0x0224FC48,0x02252324,0x022506D4
WINDOWS=(
 (0x02249460,124,'0dd689792e6a99f35fee48d56c77e1a9dd92837e53e473bc6e5683d897b1b966'),
 (0x0224A9B0,320,'ba093f320b0f4918e53aa4aa25ee66038882ad18ed589145cfaffaba3381aaa1'),
 (0x022581BC,24,'6db96417a1b38dc8a5657cad02a276e971c99ea10e5812e6f7932c6664ebbf11'),
 (0x0223BFEC,16,'ac54c831a5fc842ab09919d25d2c459e5d7fe13f3636cc1dd65b4f4f4dbea1ad'),
 (0x02252D3C,136,'9c9ca856665009d53483dda8bda62218ad0dfbc7419db9e7a6ba0849e6d30440'),
 (0x0224FC48,1832,'3859dc7f8f2258104909a74601ac968a664ca2564c170a2d2d8c3cd48e494e16'),
 (0x02252324,648,'7886cea0c0d7f036c78710e08812c2823d1d5a71d2707db07c1deb27ed0b54f5'),
 (0x022567A0,52,'0f8545eeee2142e708cf66f82a2a0599be82e974c92787e4226563ffe4cb8a09'),
 (0x022506D4,836,'81d167500d54356571af52cfe704664b24598f63f0087b5dd6573a916005679d'),
)
RANGES=(
 (0x02249460,0x022494CE),
 (0x0224A9B0,0x0224AAD8),
 (0x022581BC,0x022581D4),
 (0x0223BFEC,0x0223BFF6),
 (0x02252D3C,0x02252DC0),
 (0x0224FC48,0x0224FF44),
 (0x0224FF74,0x0225026A),
 (0x02250294,0x02250360),
 (0x02252324,0x0225234C),
 (0x02252360,0x022525A6),
 (0x022567A0,0x022567D0),
 (0x022506D4,0x0225099C),
 (0x022509B0,0x02250A12),
)

class NextCPU(D.ActionCPU):
 code_ranges=D.ActionCPU.code_ranges+RANGES
 def __init__(self,model,data,*,fixture_variant='current'):
  need(fixture_variant in ('current','reverse_speed','late_pending'),'next-action fixture domain')
  self.next_variant=fixture_variant;self.select_phase=False;self.pending_speed_div=None;self.pending_sort=None
  super().__init__(model,data)
  need(WINDOWS,'next-action fixed pins missing')
  for a,n,d in WINDOWS:need(sha(F.take(model['overlay'],a,n))==d,'next-action native dependency '+hex(a))
  for slot,entry in ((8,NEXT),(13,FIGHT)):
   need(F.take(model['overlay'],0x0226CA90+4*slot,4)==struct.pack('<I',entry|1),'next-action controller slot')
 @property
 def pending_command(self):return 23 if self.next_variant=='late_pending' else 13
 @property
 def speeds(self):return [200,100] if self.next_variant=='reverse_speed' else [100,200]
 def prepare_fixture(self):
  super().prepare_fixture()
  for b in (0,1):
   self._word(CTX+0x21A8+16*b,self.pending_command);self._word(CTX+0x21AC+16*b,1-b)
   self.uc.mem_write(CTX+0x2D46+192*b,struct.pack('<H',self.speeds[b]));self.uc.mem_write(CTX+0x2D58+192*b,bytes([6]*8))
   self.uc.mem_write(CTX+0x30B4+2*b,struct.pack('<H',33));self.uc.mem_write(CTX+0x30BC+2*b,bytes(2))
 def guest_context_ranges(self,phase):
  return ((0x21EC,0x21EE),) if phase=='select' else super().guest_context_ranges(phase)
 def store_contract(self,phase):
  if phase!='select':return super().store_contract(phase)
  return {0x0224947C:(0x3150,4),0x02249492:(0x3150,4),0x022494CA:(8,4),
   0x02252DA4:(0x21EC,1),0x02252DA6:(0x21ED,1),0x02250132:(0x21F0,4),0x0225013A:(0x21F4,4),
   0x0224A9CC:(0x64,4),0x0224AAA6:(0x3040,4),0x0224AAB0:(0x3044,4),0x0224AAB4:(8,4),0x0224AACC:(0x6C,4)}
 def _write(self,u,access,address,size,value,unused):
  if self.select_phase and self.reg(UC_ARM_REG_PC)==0x02252D56:
   b=self.reg(UC_ARM_REG_R2);need(b in (0,1) and address==CTX+0x21EC+b and size==1 and value==b,'native turn-order initialization store')
   self.current['writes'].append(dict(pc='0x2252d56',address=hex(address),bytes=size,value=value));return
  return super()._write(u,access,address,size,value,unused)
 def _code(self,u,address,size,unused):
  if self.select_phase and self.current:
   r=self.current;args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
   if self.pending_sort and address==0x02252D9C:
    call=self.pending_sort;need(self.reg(UC_ARM_REG_SP)==call['sp'] and [self.reg(v) for v in F.G.SAVED]==call.pop('saved'),'native speed-sort return ABI')
    call['value']=self.reg(UC_ARM_REG_R0);need(call['value']==int(self.speeds[0]<self.speeds[1]),'native speed-sort result');r.setdefault('sort_calls',[]).append(call);self.pending_sort=None
   if self.pending_speed_div and address==self.pending_speed_div['return_pc']:
    call=self.pending_speed_div;need(self.reg(UC_ARM_REG_SP)==call['sp'] and [self.reg(v) for v in F.G.SAVED]==call.pop('saved'),'native speed division return ABI')
    call.update(quotient=args[0],remainder=args[1]);need((args[0],args[1])==divmod(call['numerator'],10),'native actual speed division result');r['division_calls'].append(call);self.pending_speed_div=None
   if address==F.G.S.DIV:
    need(not self.reg(UC_ARM_REG_CPSR)&32 and size==4 and self.pending_speed_div is None and args[0] in (1000,2000) and args[1]==10,'native speed division ARM ABI/domain')
    self.pending_speed_div=dict(numerator=args[0],denominator=args[1],return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=self.reg(UC_ARM_REG_SP),saved=[self.reg(v) for v in F.G.SAVED])
    r['instructions']+=1;r['stack_depth']=max(r['stack_depth'],STACK-self.reg(UC_ARM_REG_SP));r['code'].add((address,size,False));return
   if address==CHECK_SPEED:
    need(args==[BS,CTX,0,1] and self.word(self.reg(UC_ARM_REG_SP))==1 and self.pending_sort is None,'native sort flag1 ABI')
    self.pending_sort=dict(return_pc=self.reg(UC_ARM_REG_LR)&~1,sp=self.reg(UC_ARM_REG_SP),saved=[self.reg(v) for v in F.G.SAVED])
   if address==CHECK_ABILITY:need(args==[BS,CTX,8,0] and self.word(self.reg(UC_ARM_REG_SP)) in (13,76),'native weather-ability scan ABI')
   if address==TARGET:need(args==[BS,CTX,0,33] and self.word(self.reg(UC_ARM_REG_SP))==self.word(self.reg(UC_ARM_REG_SP)+4)==0,'native chosen move target ABI')
   if address==0x022642F0:
    need(args[0]==BS,'native blank-message UI boundary ABI');r['models'].append(dict(name='blank-message emit omitted',args=args));self._return(u,0);return
  return super()._code(u,address,size,unused)
 def execute_path(self,entry,phase):
  result=super().execute_path(entry,phase);need(self.pending_speed_div is None and self.pending_sort is None,'unfinished native speed helper');return result
 def next_snapshot(self):
  return dict(**self.snapshot(),action_failures=[self.word(CTX+0x344+4*b) for b in (0,1)],recording_paused=self.word(BS+0x2478)&1,attacker=self.word(CTX+0x64),target=self.word(CTX+0x6C),move=self.word(CTX+0x3044),move_temp=self.word(CTX+0x3040),turn_order=list(self.uc.mem_read(CTX+0x21EC,4)),effective_speeds=[self.word(CTX+0x21F0+4*b) for b in (0,1)],battlers_on_field=self.word(CTX+0x3150))
 def observe_next(self):
  completion=super().observe_end();D.require_end(completion,pending_command=self.pending_command);before=self.next_snapshot();self.select_phase=self.end_phase=True
  try:
   selection=self.execute_path(NEXT,'select');selected=self.next_snapshot();fight=None
   if self.word(CTX+8)==13:fight=self.execute_path(FIGHT,'select')
   final=self.next_snapshot()
  finally:self.select_phase=self.end_phase=False
  return dict(fixture_variant=self.next_variant,pending_command=self.pending_command,speeds=self.speeds,completion=completion,before=before,selection=selection,selected=selected,fight=fight,final=final)


def require_next(result):
 completion=result['completion'];D.require_end(completion,pending_command=13)
 speeds=result['speeds'];need(speeds in ([100,200],[200,100]),'next-action initialized speed domain')
 before=result['before'];selected=result['selected'];final=result['final']
 expected=dict(completion['final'],action_failures=[0,64],recording_paused=0,attacker=1,target=0,move=33,move_temp=33,turn_order=[0,1,2,3],effective_speeds=[0,0],battlers_on_field=0)
 need(before==expected,'next-action completion-to-dispatch continuity')
 order=([1,0] if speeds==[100,200] else [0,1])+[2,3]
 expected=dict(before,command=13,turn_order=order,effective_speeds=speeds,battlers_on_field=1)
 need(selected==expected,'native selected action/speed order/count')
 need(final==dict(selected,command=23,attacker=0,target=1),'native full FightInput actor/target/command result')
 selection=result['selection'];fight=result['fight'];need(fight is not None,'native FightInput was skipped')
 need(not selection['models'] and len(fight['models'])==1 and fight['models'][0]['name']=='blank-message emit omitted' and fight['models'][0]['args'][0]==BS,'next-action UI model boundary')
 need(not selection['rng_calls'] and not fight['rng_calls'] and not selection['modifier_abi_issues'] and not fight['modifier_abi_issues'],'next-action unexpected RNG or item ABI')
 calls=selection.get('sort_calls',[]);need(len(calls)==1 and calls[0]['return_pc']==0x02252D9C and calls[0]['value']==int(speeds[0]<speeds[1]),'native full speed-sort BOOL/ABI')
 divisions=selection['division_calls'];need(len(divisions)==2,'native speed division count')
 for call,speed,pc in zip(divisions,speeds,(0x0224FD72,0x0224FD8C)):
  need((call['numerator'],call['denominator'],call['quotient'],call['remainder'],call['return_pc'])==(speed*10,10,speed,0,pc),'native exact speed division chain')
 for run,pc,offset,width,value in ((selection,0x022494CA,8,4,13),(selection,0x02250132,0x21F0,4,speeds[0]),(selection,0x0225013A,0x21F4,4,speeds[1]),
  (fight,0x0224A9CC,0x64,4,0),(fight,0x0224AAA6,0x3040,4,33),(fight,0x0224AAB0,0x3044,4,33),(fight,0x0224AAB4,8,4,23),(fight,0x0224AACC,0x6C,4,1)):
  need([w for w in run['writes'] if w['pc']==hex(pc)]==[dict(pc=hex(pc),address=hex(CTX+offset),bytes=width,value=value)],'next-action exact native store '+hex(pc))
 count=[w['value'] for w in selection['writes'] if w['address']==hex(CTX+0x3150)];need(count==[0,1],'native unfinished-action count')
 swaps=[w for w in selection['writes'] if w['pc'] in ('0x2252da4','0x2252da6')]
 expected_swaps=([dict(pc='0x2252da4',address=hex(CTX+0x21EC),bytes=1,value=1),dict(pc='0x2252da6',address=hex(CTX+0x21ED),bytes=1,value=0)] if speeds==[100,200] else [])
 need(swaps==expected_swaps,'native speed-order swap path')
 pcs=[w['pc'] for w in fight['writes']];need(pcs.index('0x224aab4')<pcs.index('0x224aacc'),'FightInput command write must precede actual target store')
 code={int(x['ram'],16) for x in fight['code']};need({FIGHT,0x022567A0,TARGET,0x0224AAD6}<=code,'native FightInput complete path/return coverage')
 need(final['seed']==before['seed'] and final['order']==[1,0,2,3] and final['actions']==[13,40],'native RNG/execution-order/action completion preserved')


def compare_native(model,current,role):
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 shift=int(model['record']['overlays'][1]['ram'],16)-F.U.OVERLAY_BASE;records=[];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 for a,n,digest in WINDOWS:
  raw=F.take(model['overlay'],a,n);normal=bytearray(raw);fields=[]
  if shift:
   ref=F.take(current['overlay'],a,n)
   for lo,hi in RANGES:
    lo=max(lo,a);hi=min(hi,a+n)
    if lo>=hi:continue
    for ins in md.disasm(ref[lo-a:hi-a],lo):
     if ins.mnemonic in ('bl','blx') and ins.op_str.startswith('#'):
      target=int(ins.op_str[1:],0)
      if target<F.U.OVERLAY_BASE:
       at=ins.address-a;need(F.G.S.SHARED.branch(raw[at:at+4],ins.address+shift,ins.mnemonic)==target,'next-action regional native call')
       need(F.G.piece(model['segments'],target,32)==F.G.piece(current['segments'],target,32),'next-action regional ARM9 target body')
       normal[at:at+4]=ref[at:at+4];fields.append(dict(offset=hex(at),target=hex(target)))
   if a==CHECK_SPEED:
    bindings=((0x0224FF50,0x0226CB88,0x0226CB88,26,((0x0224FD64,'7a48'),(0x0224FD7E,'7448'))),
     (0x0224FF54,0x0226CB89,0x0226CB88,26,((0x0224FD6A,'7a4a'),(0x0224FD84,'734a'))),
     (0x0224FF58,0x0226CB50,0x0226CB50,8,((0x0224FE08,'534f'),)),
     (0x02250270,0x0226CB50,0x0226CB50,8,((0x0224FFB4,'ae4f'),)))
    for literal,target,base,length,loads in bindings:
     at=literal-a;need(struct.unpack_from('<I',raw,at)[0]==target+shift and struct.unpack_from('<I',ref,at)[0]==target,'next-action regional table pointer')
     for pc,opcode in loads:need(raw[pc-a:pc-a+2]==ref[pc-a:pc-a+2]==bytes.fromhex(opcode),'next-action native table LDR binding')
     table=F.take(current['overlay'],base,length);need(F.take(model['overlay'],base,length)==table,'next-action regional table bytes')
     normal[at:at+4]=ref[at:at+4];fields.append(dict(offset=hex(at),target=hex(target+shift),table_bytes=length,table_sha256=sha(table)))
  need(sha(normal)==digest,'next-action native full window '+role+' '+hex(a));records.append(dict(ram=hex(a+shift),bytes=n,sha256=sha(raw),comparison_only_fields=fields))
 return records


def analyze(rom,v4,base,retail,language):
 import gc
 current=F.G.S.SHARED.read_current(rom,language);data=D.C.resources(rom,current);inputs=[];windows=[]
 for role,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom)):
  model=current if role=='r4' else F.G.S.SHARED.read_image(path,language,role)
  windows.append(dict(input=role,vm=H.compare_windows(model,current,role),after=D.A.compare_native(model,current,role),effect=D.E.compare_native(model,current,role),consumer=D.C.compare_native(model,current,role),action_end=D.compare_native(model,current,role),next_action=compare_native(model,current,role)))
  inputs.append(model['record']);del model;gc.collect()
 positives=[]
 for variant in ('current','reverse_speed'):
  result=NextCPU(current,data,fixture_variant=variant).observe_next();require_next(result);positives.append(result);gc.collect()
 counter=NextCPU(current,data,fixture_variant='late_pending').observe_next()
 need(counter['final']['command']==23 and counter['final']['attacker']==1 and counter['fight'] is None,'late-pending counter lost same-command/stale-actor premise')
 try:require_next(counter)
 except ValueError:counter_rejected=True
 else:raise ValueError('same-command stale-attacker counter accepted')
 return dict(schema='native-next-action-v1',language=language,inputs=inputs,windows=windows,resources=data['record'],positives=positives,counter=counter,counter_rejected=counter_rejected,compilation_performed=False,
  compatibility_gates=dict(native_next_actor_initialization=True,no_item_action_compatibility=False),
  source_sha256={str(p.relative_to(F.G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(D.__file__),Path(H.__file__),F.U.NATIVE)},
  limits=['Continues actual canceled-action history/completion through native8→13→23 with actor0/move33/target1; initial executionOrder remains a declared host input',
   'Initial live HP,abilities65/67,empty items,neutral stat stages6,speeds100/200 or200/100 and selected Tackle/target are explicit initialized fixtures',
   'Native speed sort changes turnOrder but preserves executionOrder; unequal-speed paths consume no RNG beyond preceding native action-end two calls',
   'Full FightInput return is required because command23 is written before target selection; blank-message UI emission is an omitted ABI-checked model',
   'Next TryMove23 body/PP use/attack,target alternatives/ties/other abilities/statuses/whole pivot/SAVE/cold/hardware/timing are unexecuted; prior NARC/UI/Ready/cache/transport models and both installed defects remain'])


def main():
 import argparse,json
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 for path in (args.rom,args.v4,args.base,args.retail):
  if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input')
 result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
 args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
 print(args.language,'native8/13 next actor0/move33/target1/command23 verified; no-item compatibility FAIL; next TryMove23 not executed')
 raise SystemExit(1)


if __name__=='__main__':main()
