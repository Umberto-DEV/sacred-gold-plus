#!/usr/bin/env python3
"""Continue native flinch cancellation through history and action completion."""
import importlib.util,struct
from pathlib import Path
spec=importlib.util.spec_from_file_location('action_consumer_native',Path(__file__).with_name('attribuisci_flinch_consumer.py'))
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
E,A,H,F=C.E,C.A,C.H,C.F
need,sha=C.need,C.sha
CTX,BS,STACK,STOP=C.CTX,C.BS,C.STACK,C.STOP
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_CPSR,UC_ARM_REG_LR
HISTORY,END=0x0224D23C,0x0224D368
WINDOWS=(
 (0x0224D23C,300,'7a0f6b67eb736c852a87ece8e6d6d3cea720ec4cc0b5634799184d16459d4b9e'),
 (0x0224D368,224,'b62b821962ed2e8b3fcc2adc27bceda9b04e2b455fa4642e68540d0e4fe02f07'),
 (0x0224DD74,520,'721f0203b3bfe14a8d01c13412bf319bccd7892257722abd2cf6b16aa4311701'),
 (0x02256694,180,'e04ac9910f62ac218df74a2c2e92c437ceafc22c0db94ea9b39b01e553e1ddfc'),
 (0x022543A0,392,'6521676583b196bbbaff9b115dade26f51cdea5113dc5f2eaa0481fefa97466b'),
 (0x0224DD18,92,'cd7d390dfa853a382fb90b229f7f4904ded4564360a477b8f685df2787e69af7'),
 (0x0224D7EC,888,'7814a0310e3ccb2f872b6ba7511427c4f24923fec64258e6d216ca15f4400e91'),
 (0x0224DC0C,104,'90cd885069a9c4a79857e8010a4182c6230c5b7d0ca4d9b7d11416129e159105'),
 (0x0224E130,140,'4e79bb8a60ed07e9dd1786dbeb9e21b5e317586fa59f9cff09b1ebb88c3eb10b'),
 (0x02250F44,244,'5691ad9d19cd638e138fc3843d5695dde3e51ebf419c2b9832fa1c527f6b3512'),
 (0x02253194,3084,'4cdb3d613846c0c40f4a81ad854bd7085649dc2be69b0b3ae712f47f383d857d'),
 (0x02256914,1556,'3413f8e76c2d32420dd124e3d01462ae5fd42542f6c82b8d87451cd69c281ef3'),
 (0x02254E7C,1696,'ed4c90028c605a4b9589a5076f242e11de41ecba92b292e65d0f472caaeb7631'),
 (0x022585B8,164,'94b39f0b3bfc838fa5c4896b109ad045656bcdfa16ecd91def384d8a3448dd10'),
 (0x0223BAF8,12,'e866add2de3b57686fe0fe7ab95185c89167a57165dfa1aadc9f55ba29d4ef25'),
 (0x0223ABB8,104,'c7abedbaff66691730623dc90ecdefcd738051d05870398593b4a800593054ee'),
 (0x020D4858,92,'10577c29bdbc6913eba507a029157099a73f377ee8d0e6617ff2cc72def5f8a5'),
)
RANGES=(
 (0x0224D23C,0x0224D350),
 (0x0224D368,0x0224D442),
 (0x0224DD74,0x0224DF54),
 (0x02256694,0x02256736),
 (0x022543A0,0x022543D4),
 (0x022543E6,0x0225450A),
 (0x0224DD18,0x0224DD72),
 (0x0224D7EC,0x0224DAB2),
 (0x0224DB10,0x0224DB24),
 (0x0224DB38,0x0224DB64),
 (0x0224DC0C,0x0224DC66),
 (0x0224E130,0x0224E1AC),
 (0x02250F44,0x02251022),
 (0x02253194,0x022531BE),
 (0x022531DE,0x02253204),
 (0x0225321A,0x022534CE),
 (0x02253500,0x02253804),
 (0x0225383C,0x02253C2A),
 (0x02253C44,0x02253D90),
 (0x02256914,0x02256C2C),
 (0x02256C4C,0x02256EEA),
 (0x02254E7C,0x02254ECA),
 (0x02254F38,0x0225519E),
 (0x022551C8,0x022554B6),
 (0x022554DC,0x0225551C),
 (0x022585B8,0x02258652),
 (0x0223BAF8,0x0223BAFE),
 (0x0223ABB8,0x0223AC1E),
)

INIT_STORES={
 0x02250F4E:(0x2144,4),
 0x02250F54:(0x2150,4),
 0x02250F5A:(0x214C,4),
 0x02250F60:(0x2154,4),
 0x02250F68:(0x2158,4),
 0x02250F6E:(0x2160,4),
 0x02250F74:(0x2164,4),
 0x02250F7A:(0x216C,4),
 0x02250F80:(0x74,4),
 0x02250F84:(0x2170,4),
 0x02250F8A:(0x2174,4),
 0x02250F90:(0x2178,4),
 0x02250F96:(0x88,4),
 0x02250F9C:(0x8C,4),
 0x02250FA2:(0x94,4),
 0x02250FA8:(0x217C,1),
 0x02250FAE:(0x217D,1),
 0x02250FB4:(0x217E,1),
 0x02250FBA:(0x2180,4),
 0x02250FBE:(0x38,4),
 0x02250FC2:(0x2184,4),
 0x02250FC8:(0x2188,4),
 0x02250FCA:(0x10,4),
 0x02250FCC:(0x18,4),
 0x02250FCE:(0x20,4),
 0x02250FD0:(0x28,4),
 0x02250FD2:(0x30,4),
 0x02250FD4:(0x3C,4),
 0x02250FD6:(0x40,4),
 0x02250FD8:(0x48,4),
 0x02250FDA:(0x4C,4),
 0x02250FDC:(0x50,4),
 0x02250FE0:(0x54,4),
 0x02250FF0:(0x213C,4),
 0x02250FFC:(0x2140,4),
 0x02251000:(0x3120,1),
 0x0225101A:(0x21A4,1),
}
ENTRY_STATE_STORES=(
 0x0225326E,
 0x02253332,
 0x02253442,
 0x022534B8,
 0x02253620,
 0x02253760,
 0x02253970,
 0x02253AC8,
 0x02253BA0,
 0x02253C14,
 0x02253CA2,
 0x02253CBE,
 0x02253CF8,
 0x02253D34,
 0x02253D74,
 0x02253D7A,
)

class ActionCPU(C.ConsumerCPU):
 code_ranges=C.ConsumerCPU.code_ranges+RANGES
 def __init__(self,model,data,*,variant='current',order_variant='current'):
  need(order_variant in ('current','wrong_order'),'action order fixture domain');self.order_variant=order_variant
  self.end_phase=False;self.pending_clear=None;self.clear_calls=[]
  super().__init__(model,data,variant=variant)
  need(WINDOWS,'action-end fixed pins missing')
  for a,n,d in WINDOWS:need(sha(F.take(model['overlay'],a,n) if a>=F.U.OVERLAY_BASE else F.G.piece(model['segments'],a,n))==d,'action-end native dependency '+hex(a))
  for slot,entry in ((39,HISTORY),(40,END)):
   need(F.take(model['overlay'],0x0226CA90+4*slot,4)==struct.pack('<I',entry|1),'action-end controller slot')
 def prepare_fixture(self):
  super().prepare_fixture()
  # Declared before any guest instruction; no action-done value is injected.
  self.uc.mem_write(CTX+0x21E8,bytes((1,0,2,3) if self.order_variant=='current' else (0,1,2,3)))
  self.uc.mem_write(CTX+0x21EC,bytes((0,1,2,3)))
  self._word(CTX+0xEC,0)
  for b in (0,1):self._word(CTX+0x21A8+16*b,23)
  self._word(CTX+0x2D8C,300);self._word(CTX+0x2D90,300)
  for b in (0,1):
   self.uc.mem_write(CTX+0x2D4C+192*b,struct.pack('<H',33));self.uc.mem_write(CTX+0x2D6C+192*b,bytes((35,0,0,0)))
  for off,value in ((0x305E,33),(0x3048,33),(0x307E,33),(0x3064,33),(0x306C,1),(0x3074,0),(0x30C4,33),(0x30CC,1),(0x30D4,0)):
   self.uc.mem_write(CTX+off,struct.pack('<I' if off==0x3048 else '<H',value))
 def guest_context_ranges(self,phase):
  return ((0x2D4,0x344),(0x2DB0,0x2DB4),(0x2E70,0x2E74),(0x218C,0x2194),(0x21A4,0x21A8),(0x21A8,0x21AC),(0x21B8,0x21BC)) if phase=='end' else super().guest_context_ranges(phase)
 def rng_write_allowed(self,phase):
  return phase=='end' or super().rng_write_allowed(phase)
 def store_contract(self,phase):
  if phase!='end':return super().store_contract(phase)
  return {**INIT_STORES,**{pc:(0x58,4) for pc in ENTRY_STATE_STORES},0x022532AE:(0x120,4),0x0225693A:(0x118,4),0x0224E18E:(0x5C,4),0x0224E1A6:(0x5C,4),0x0224DC54:(0x3064+2*self.attacker,2),0x0224DC62:(0x30C4+2*self.attacker,2),0x0224D3FE:(0x21A8+16*self.uc.mem_read(CTX+0x21E8+self.word(CTX+0xEC),1)[0],4),0x0224D434:(0xEC,4),0x0224D43E:(8,4),0x0224D2EE:(0x305C+2*self.attacker,2),0x0224D2F2:(0x3048,4),0x0224D31C:(0x307C+2*self.attacker,2),
   0x0224D34C:(8,4),0x0224DD6C:(8,4),0x0224DE7A:(0x3064+2*(1-self.attacker),2),0x0224DE88:(0x306C+2*(1-self.attacker),2),0x0224DE94:(0x3074+2*(1-self.attacker),2),0x0224DE98:(0x3048,4),
   0x0224DF38:(0x30C4+2*(1-self.attacker),2),0x0224DF46:(0x30CC+2*(1-self.attacker),2),0x0224DF50:(0x30D4+2*(1-self.attacker),2),0x02256732:(0x2DCC+192*self.attacker,4)}
 def _code(self,u,address,size,unused):
  if self.end_phase and self.current:
   if self.pending_clear and address==0x02251012:
    call=self.pending_clear;need(self.reg(UC_ARM_REG_SP)==call['sp'] and [self.reg(v) for v in F.G.SAVED]==call.pop('saved'),'native clear return ABI')
    need(bytes(u.mem_read(call['destination'],28))==bytes(28),'native clear buffer result');self.clear_calls.append(call);self.pending_clear=None
   if 0x020D4858<=address<0x020D48B4:
    need(not self.reg(UC_ARM_REG_CPSR)&32 and size==4,'native CpuClearFast ARM ISA')
    if address==0x020D4858:
     dest=self.reg(UC_ARM_REG_R1);need(self.pending_clear is None and [self.reg(UC_ARM_REG_R0),self.reg(UC_ARM_REG_R2),self.reg(UC_ARM_REG_LR)]==[0,28,0x02251013] and dest==CTX+0x2D4+28*len(self.clear_calls),'native clear exact four-buffer ABI')
     self.pending_clear=dict(destination=dest,sp=self.reg(UC_ARM_REG_SP),saved=[self.reg(v) for v in F.G.SAVED])
    self.current['instructions']+=1;need(self.current['instructions']<=20000,'action instruction budget');self.current['stack_depth']=max(self.current['stack_depth'],STACK-self.reg(UC_ARM_REG_SP));self.current['code'].add((address,size,False));return
   r=self.current
   item=r.get('pending_item')
   if item and address==item['return_pc']:
    need(self.reg(UC_ARM_REG_SP)==item['sp'] and [self.reg(v) for v in F.G.SAVED]==item.pop('saved'),'action native item return ABI')
    item['value']=self.reg(UC_ARM_REG_R0);need(item['value']==self.cache[36*item['member']+item['attribute']+1],'action actual native item attribute value')
    r['item_queries'].append(item);r['pending_item']=None
   call=r.get('pending_rng')
   if call and address==call['return_pc']:
    need(address==0x02258606 and self.reg(UC_ARM_REG_SP)==call['sp'] and [self.reg(v) for v in F.G.SAVED]==call.pop('saved'),'action native RNG return ABI')
    call.update(after=self.word(BS+F.G.SEED_OFFSET),value=self.reg(UC_ARM_REG_R0))
    need(call['after']==F.G.next_seed(call['before']) and call['value']==call['after']>>16,'action actual RNG transition')
    r['rng_calls'].append(call);r['pending_rng']=None
  if self.end_phase and address in (F.U.GET_EFFECT,F.U.GET_MODIFIER):
   battler=self.reg(UC_ARM_REG_R1);need(self.reg(UC_ARM_REG_R0)==CTX and battler in (0,1),'action native held-effect getter ABI')
   saved=self.attacker
   try:
    self.attacker=battler
    return super()._code(u,address,size,unused)
   finally:self.attacker=saved
  return super()._code(u,address,size,unused)
 def _write(self,u,access,address,size,value,unused):
  if self.end_phase and self.current:
   pc=self.reg(UC_ARM_REG_PC)
   if pc==0x0225101A:
    b=self.reg(UC_ARM_REG_R4)-1;need(b in range(4) and address==CTX+0x21A4+b and size==1 and value==6,'native AI switched-slot reset')
    self.current['writes'].append(dict(pc=hex(pc),address=hex(address),bytes=size,value=value));return
   if pc==0x020D48A4:
    call=self.pending_clear;need(call is not None and size==4 and value==0 and call['destination']<=address<=call['destination']+24 and (address-call['destination'])%4==0,'native CpuClearFast store extent')
    self.current['writes'].append(dict(pc=hex(pc),address=hex(address),bytes=size,value=value));return
   if pc in (0x0224DC38,0x0224DC3E):
    b=self.reg(UC_ARM_REG_R3)-1;need(b in (0,1) and size==4,'native action-reset loop domain')
    off=0x2DB0+192*b if pc==0x0224DC38 else 0x218C+4*b
    expected=self.word(CTX+off)&(~self.word(CTX+0x218C+4*b)&0xFFFFFFFF) if pc==0x0224DC38 else 0
    need(address==CTX+off and value==expected,'native action-reset precise store')
    self.current['writes'].append(dict(pc=hex(pc),address=hex(address),bytes=size,value=value));return
  try:return super()._write(u,access,address,size,value,unused)
  except ValueError as error:raise ValueError(str(error)+' action PC='+hex(self.reg(UC_ARM_REG_PC))) from error
 def snapshot(self):
  return dict(pp=[list(self.uc.mem_read(CTX+0x2D6C+192*b,4)) for b in (0,1)],history_fields=[int.from_bytes(self.uc.mem_read(CTX+off,4 if off==0x3048 else 2),'little') for off in (0x305E,0x3048,0x307E,0x3064,0x306C,0x3074,0x30C4,0x30CC,0x30D4)],self_turn_zero=bytes(self.uc.mem_read(CTX+0x2D4,112))==bytes(112),status_state=self.word(CTX+0x50),try_state=self.word(CTX+0x48),move_fail=self.word(CTX+0x348),battle_type=self.word(BS+0x2C),command=self.word(CTX+8),execution_index=self.word(CTX+0xEC),order=list(self.uc.mem_read(CTX+0x21E8,4)),actions=[self.word(CTX+0x21A8+16*b) for b in (0,1)],statuses=[self.word(CTX+0x2DB0+192*b) for b in (0,1)],hp=[self.word(CTX+0x2D8C+192*b) for b in (0,1)],move_status=self.word(CTX+0x216C),battle_status=self.word(CTX+0x213C),seed=self.word(BS+F.G.SEED_OFFSET))
 def observe_end(self):
  self.clear_calls=[];need(self.pending_clear is None,'unfinished clear before action')
  consumer=super().observe_action();C.require_consumer(consumer);before=self.snapshot();self.end_phase=True
  try:
   history=self.execute_path(HISTORY,'end');after_history=self.snapshot()
   end=self.execute_path(END,'end');need(self.pending_clear is None,'unfinished native clear');final=self.snapshot()
  finally:self.end_phase=False
  return dict(order_variant=self.order_variant,consumer=consumer,before=before,history=history,after_history=after_history,end=end,final=final,clear_calls=self.clear_calls)


def require_end(result,*,pending_command=23):
 need(type(pending_command) is int and pending_command in (13,23),'action pending-command oracle domain')
 C.require_consumer(result['consumer']);before=result['before'];history=result['after_history'];final=result['final']
 need(before['command']==result['consumer']['final_command']==39 and before['execution_index']==0 and before['order']==[1,0,2,3] and before['actions']==[pending_command,pending_command],'action initial cancellation/order boundary')
 need(before['seed']==result['consumer']['seed_after'] and before['status_state']==6 and before['try_state']==1 and before['move_fail']==64,'action cancellation state continuity')
 need(before['history_fields']==[33,33,33,33,1,0,33,1,0] and not before['self_turn_zero'],'action history/reset initial fixture')
 expected=dict(before,command=40,history_fields=[0,0,0,0,255,0,0,255,0]);need(history==expected,'native history exact changes')
 expected=dict(history,command=8,actions=[pending_command,40],execution_index=1,self_turn_zero=True,status_state=0,try_state=0,move_status=0,battle_status=0,seed=F.G.next_seed(F.G.next_seed(history['seed'])))
 need(final==expected,'native action completion/reset/order/RNG summary')
 need(before['pp']==[[35,0,0,0],[35,0,0,0]] and before['hp']==[300,100] and before['statuses']==[0,0] and before['battle_type']==0 and before['move_status']==0x80000000 and before['battle_status']&2,'ordinary canceled-action input domain')
 first,last=result['history'],result['end']
 need(not first['models'] and not last['models'] and not first['modifier_abi_issues'] and not last['modifier_abi_issues'],'action native closure unexpectedly modeled or invalid ABI')
 need(not first['rng_calls'] and len(last['rng_calls'])==2,'native ability-entry RNG count')
 seed=before['seed']
 for call in last['rng_calls']:
  need(call['before']==seed and call['after']==F.G.next_seed(seed) and call['value']==call['after']>>16 and call['return_pc']==0x02258606,'native ability-entry RNG chain');seed=call['after']
 need(seed==final['seed'],'native final RNG continuity')
 states=[w['value'] for w in last['writes'] if w['address']==hex(CTX+0x58)]
 need(states==list(range(1,16))+[0],'native full ability-entry state progression')
 for run,pc,offset,value in ((first,0x0224D34C,8,40),(last,0x0224D3FE,0x21B8,40),(last,0x0224D434,0xEC,1),(last,0x0224D43E,8,8)):
  need([w for w in run['writes'] if w['pc']==hex(pc)]==[dict(pc=hex(pc),address=hex(CTX+offset),bytes=4,value=value)],'native action exact controller/selected-row/index store')
 need([call['destination'] for call in result['clear_calls']]==[CTX+0x2D4+28*b for b in range(4)],'native four clear calls')
 clears=[w for w in last['writes'] if w['pc']=='0x20d48a4']
 need(clears==[dict(pc='0x20d48a4',address=hex(CTX+0x2D4+4*i),bytes=4,value=0) for i in range(28)],'native four SelfTurnData buffer clears')
 code={int(row['ram'],16) for row in last['code']}
 need({END,0x022543A0,0x0224DD18,0x0224D7EC,0x02253194,0x02256914,0x02254E7C,0x0224E130,0x0224DC0C,0x02250F44,0x020D4858}<=code,'ordinary native action-end closure missing')
 need(not any(0x02249460<=pc<0x022494DC for pc in code),'command8 was unexpectedly executed')


def compare_native(model,current,role):
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 shift=int(model['record']['overlays'][1]['ram'],16)-F.U.OVERLAY_BASE;records=[];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 for a,n,digest in WINDOWS:
  raw=F.G.piece(model['segments'],a,n) if a<F.U.OVERLAY_BASE else F.take(model['overlay'],a,n)
  normal=bytearray(raw);fields=[]
  if shift and a>=F.U.OVERLAY_BASE:
   ref=F.take(current['overlay'],a,n)
   for lo,hi in RANGES:
    lo=max(lo,a);hi=min(hi,a+n)
    if lo>=hi:continue
    for ins in md.disasm(ref[lo-a:hi-a],lo):
     if ins.mnemonic in ('bl','blx') and ins.op_str.startswith('#'):
      target=int(ins.op_str[1:],0)
      if target<F.U.OVERLAY_BASE:
       at=ins.address-a;need(F.G.S.SHARED.branch(raw[at:at+4],ins.address+shift,ins.mnemonic)==target,'action regional native call')
       # The20-byte nature-stat reader body ends before its regional data pool.
       length=20 if target==0x020718E8 else 32
       need(F.G.piece(model['segments'],target,length)==F.G.piece(current['segments'],target,length),'action regional native call target body')
       normal[at:at+4]=ref[at:at+4];fields.append(dict(offset=hex(at),target=hex(target),signature_bytes=length))
   if a==0x02253194:
    at=0x02253814-a;target=0x0226CB88
    need(struct.unpack_from('<I',raw,at)[0]==target+shift and struct.unpack_from('<I',ref,at)[0]==target,'action regional stat-table pointer')
    for pc,opcode in ((0x02253576,'a748'),(0x02253580,'a448'),(0x02253596,'9f48'),(0x022535A0,'9c48')):
     need(raw[pc-a:pc-a+2]==ref[pc-a:pc-a+2]==bytes.fromhex(opcode),'action stat-table LDR binding')
    table=F.take(current['overlay'],target,26);need(F.take(model['overlay'],target,26)==table,'action regional stat-table bytes')
    normal[at:at+4]=ref[at:at+4];fields.append(dict(offset=hex(at),target=hex(target+shift),table_bytes=26,table_sha256=sha(table)))
  need(sha(normal)==digest,'action native full window '+role+' '+hex(a));records.append(dict(ram=hex(a+shift if a>=F.U.OVERLAY_BASE else a),bytes=n,sha256=sha(raw),comparison_only_fields=fields))
 return records


def analyze(rom,v4,base,retail,language):
 import gc
 current=F.G.S.SHARED.read_current(rom,language);data=C.resources(rom,current);inputs=[];windows=[]
 for role,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom)):
  model=current if role=='r4' else F.G.S.SHARED.read_image(path,language,role)
  windows.append(dict(input=role,vm=H.compare_windows(model,current,role),after=A.compare_native(model,current,role),effect=E.compare_native(model,current,role),consumer=C.compare_native(model,current,role),action_end=compare_native(model,current,role)))
  inputs.append(model['record']);del model;gc.collect()
 positive=ActionCPU(current,data).observe_end();require_end(positive);gc.collect()
 counter=ActionCPU(current,data,order_variant='wrong_order').observe_end()
 need(counter['final']['command']==8 and counter['final']['actions']==[40,23],'action named order counter lost same-command premise')
 try:require_end(counter)
 except ValueError:counter_rejected=True
 else:raise ValueError('action wrong selected-row counter accepted')
 return dict(schema='flinch-native-action-end-v1',language=language,inputs=inputs,windows=windows,resources=data['record'],positive=positive,counter=counter,counter_rejected=counter_rejected,compilation_performed=False,
  compatibility_gates=dict(native_action_completion=True,no_item_action_completion=False),
  source_sha256={str(p.relative_to(F.G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(C.__file__),Path(H.__file__),F.U.NATIVE)},
  limits=['Continues actual P24 cancellation after an explicit controlled next-action boundary; execution order1,0,index0 and live battlers/PP/history are initialized before guest execution',
   'Native ordinary type0 UpdateMoveHistory39→ActionEnd40 executes full neutral heal/exp/battle-over/ability-entry/form/item/vanish/reset/init closure; no Safari shortcut or service decides completion',
   'Native TryAbilityOnEntry consumes2 RNG through unconditional Trace-target choices despite neutral65/67 abilities; other ability/status/battle-condition branches are not exercised',
   'Native selected action becomes40,index advances and command8 is reached; command8/natural turn selection/gameplay capture are not executed',
   'Earlier NARC/UI/Ready/cache/Party-transport models remain; SAVE/cold restart/hardware/timing/whole pivot and both installed game repairs remain outside scope'])


def main():
 import argparse,json
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 for path in (args.rom,args.v4,args.base,args.retail):
  if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input')
 result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
 args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
 print(args.language,'native action completion40/index advance/command8 verified; no-item compatibility FAIL; command8 not executed')
 raise SystemExit(1)


if __name__=='__main__':main()
