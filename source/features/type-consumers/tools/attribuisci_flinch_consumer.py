#!/usr/bin/env python3
"""Follow the produced flinch bit into native status failure and command39."""
import importlib.util,json,mmap,struct
from pathlib import Path
spec=importlib.util.spec_from_file_location('consumer_effect_native',Path(__file__).with_name('attribuisci_flinch_effect.py'))
E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
A,H,F=E.A,E.H,E.F
need,sha=F.need,F.sha
CTX,BS,STACK,STOP=E.CTX,E.BS,E.STACK,E.STOP
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
TRY,STATUS=0x0224C38C,0x0224B528
KEYS,TOUCH=0x021D1154,0x021D1170
SCRIPTS={15:'cf4783da2e5bfc50a35612dddc858f08a8794f1438101066cbea823bf49efcc3',278:'417cdf4b035ca0285e17692524f68d5953835af6c985da4045b0eb3a6be86d52'}
WINDOWS=(
 (0x0224C38C,332,'8cfd1e4ea518dc9290ebefbd2f73aaf82f3b03473efe1efd7e5547079c1bc8c5'),
 (0x0224B528,1796,'776e220bc6b9d460f11553621766c13b8c17e734a005c05b68bd889098770b79'),
 (0x0224BCA4,32,'8e75807b4a40bacc0d5856412b12e3e6e4d1769fdf13c70d983a26353c1cd83d'),
 (0x02252C40,52,'f2d50b88239d78fe503cfe930460bb21dac2de9d5089942f57916b56e6fb086b'),
 (0x02252C74,116,'16b6284748872f64d981c9419675effdf98b12313694814558a9803ae6b1515a'),
 (0x02252DC4,52,'90bf556b84779874ba07b87083575edccefa3981000af19c92c767789b72efef'),
 (0x02252DF8,56,'5c4953746d9c4efd5f3dfdc3895c148437ffdd6db7aa9a851be5e58ed57c359f'),
 (0x0223A7F0,4,'2640d5fd1ca49974c06fbe29394309f3a9b27280ff43b5c43bf5c93a93e4b1f7'),
 (0x0223DEF0,52,'d7685ad8fc82d74f4a4eb8465f5a40bbd45f025d9753ec5ce96d385437476807'),
 (0x0223E2F0,156,'233a3d7c1e202aecede2cd48d5e6d75518ee420edc223367f917aed284c3bf84'),
 (0x0223F524,192,'3034720a5dd88f2ef69927879450d0201571c4e81cc68d0ae207d1a233ea7351'),
 (0x0223FA98,44,'8b12a88875c06ce9ac0e0f16f639abc2e4776eb80a2bcb51d7fc604d3deb0e86'),
 (0x02250CA0,92,'bb987a5544b0688fad217a80813ffbf3772998c2af157e3d2447adba9ae99c1c'),
 (0x022478F4,204,'ab1129a745a1b821d90e87220cdd7fb4a8685bc791fc2f2f7f45135a17919349'),
 (0x02025358,12,'774efb31fbac9c8b7cd20e324d7e78ccb444e33ba366dcbdc4b4d0b8bbc19bf0'),
 (0x0224F0F0,10,'951ade9a7dcb1208df35b93e50b5d1527fcdacc627fa13b6204c02de118e10bc'),
 (0x0224F0FA,10,'0f02fabb27851cf55f261cb56593c83d63063f452dbaeac5e8ad87359f178c79'),
)
COMMANDS={**E.COMMANDS,18:0x0223DEF0,30:0x0223E2F0,55:0x0223F524,65:0x0223FA98}


def read_consumer_scripts(rom):
 spec=importlib.util.spec_from_file_location('consumer_raw_archive',F.G.SOURCE/'features/borsa/tools/attribuisci.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
 with Path(rom).open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:members,record=reader.raw_archive(raw,'a/0/0/1')
 need(record['file_id']==130 and len(members)==297,'consumer script archive geometry')
 for i,d in SCRIPTS.items():need(sha(members[i])==d,'consumer raw script identity')
 return {i:members[i] for i in SCRIPTS}


def resources(rom,model):
 data=E.resources(rom,model);members=read_consumer_scripts(rom);data['subscripts'].update(members)
 data['record']['consumer_scripts']=[dict(member=i,bytes=len(members[i]),sha256=d) for i,d in SCRIPTS.items()]
 return data


class ConsumerCPU(E.EffectCPU):
 code_ranges=E.EffectCPU.code_ranges+((TRY,0x0224C3A4),(0x0224C3B2,0x0224C4C6),
  (STATUS,0x0224B56A),(0x0224B58C,0x0224B852),(0x0224B87C,0x0224BBDA),(0x0224BC04,0x0224BC2C),
  (0x0224BCA4,0x0224BCBE),(0x02252C40,0x02252C6E),(0x02252C74,0x02252CE4),
  (0x02252DC4,0x02252DF2),(0x02252DF8,0x02252E28),(0x0223A7F0,0x0223A7F4),
  (0x0223DEF0,0x0223DF24),(0x0223E2F0,0x0223E37A),(0x0223F524,0x0223F5E2),
  (0x0223FA98,0x0223FAC4),(0x02250CA0,0x02250CE2),
  (0x022478F4,0x0224791A),(0x02247994,0x022479C0),(0x02025358,0x0202535E),
  (0x0224F0F0,0x0224F104),(0x022476DC,0x022476E0))
 script_commands=COMMANDS
 side_categories=(*E.EffectCPU.side_categories,1)

 def __init__(self,model,data,*,variant='current'):
  self.consumer_phase=False
  super().__init__(model,data,variant=variant)
  need(WINDOWS,'consumer fixed pins not configured')
  for a,n,d in WINDOWS:
   raw=F.take(model['overlay'],a,n) if a>=F.U.OVERLAY_BASE else F.G.piece(model['segments'],a,n)
   need(sha(raw)==d,'consumer native dependency '+hex(a))
  for i,d in SCRIPTS.items():need(sha(data['subscripts'][i])==d,'consumer script fixture drift')
  need(F.take(model['overlay'],0x0226CA90+23*4,4)==struct.pack('<I',TRY|1),'native TryMove controller slot23')
  need(F.G.S.SHARED.branch(F.take(model['overlay'],0x0224C3C8,4),0x0224C3C8,'bl')==STATUS,'native TryMove→status BL')
  for var,target in ((85,0x0224F0F0),(86,0x0224F0FA)):
   need(struct.unpack('<h',F.take(model['overlay'],0x0224EE02+2*var,2))[0]+0x0224EE04==target,'native Quick Claw activation-flag case')
  need(struct.unpack('<h',F.take(model['overlay'],0x0224791A+2*2,2))[0]+0x0224791C==0x02247996,'native message tag2 parser case')
  self.consumer_requests=[];self.pending_status=None;self.last_message=None

 def model_context_ranges(self,phase):
  return ((0x2700,0x288C),(0xB4,0xB8)) if phase=='consume' else super().model_context_ranges(phase)

 def store_contract(self,phase):
  if phase!='consume':return super().store_contract(phase)
  result={0x02245512:(0xB4,4),0x02245502:(0xB4,4),0x0223DCD6:(0x3154,4),0x0223CFAA:(0x3154,4),
   0x022454D8:(0x3154,4),0x0224C382:(0xB4,4),0x0224C386:(8,4),
   0x0224C3BA:(0x48,4),0x0224BCB4:(12,4),0x0224BCB8:(8,4),
   0x0224B59E:(0x2DB0+192*self.attacker,4),0x0224B5B6:(0x2DC0+192*self.attacker,4),
   0x0224B7A0:(0x2DB0+192*self.attacker,4),0x0224B7AC:(0x344+4*self.attacker,4),
   0x0224B7BA:(8,4),0x0224B7BE:(12,4),0x0224BC0A:(0x213C,4),0x0224BC1A:(0x216C,4),
   0x022585B2:(0x394+2*self.attacker,2),0x0223E366:(0xF0,4),0x0223E374:(0x3154,4),0x0223F5DA:(0x80,4),
   0x02250CB2:(0x2DB0+192*self.attacker,4),0x02250CBA:(0x2DB0+192*self.attacker,4),
   0x02250CCA:(0x2DC0+192*self.attacker,4),0x02250CD4:(0x2DC8+192*self.attacker,4),0x02250CDC:(0x2DC8+192*self.attacker,4)}
  for pc in (0x0224B5BC,0x0224B6B6,0x0224B71C,0x0224B744,0x0224B780,0x0224B7C6,0x0224B802,0x0224B84A,
             0x0224B8B0,0x0224B8EC,0x0224B928,0x0224B930,0x0224BA68,0x0224BAD0,0x0224BAD8,0x0224BBB8,0x0224BBBE):result[pc]=(0x50,4)
  return result

 def _seam(self,u,address,size,unused):
  if not self.consumer_phase or address!=F.C.READ_BATTLE_SCRIPT:return super()._seam(u,address,size,unused)
  args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
  need(args[:2]==[CTX,1] and args[2] in SCRIPTS,'consumer script load ABI/domain')
  self.current_script=args[2];u.mem_write(CTX+0x2700,self.resources['subscripts'][args[2]]);self._word(CTX+0xB4,0)
  self.consumer_requests.append(args[2]);self.current['models'].append(dict(name='consumer NARC loader',args=args));self._return(u,0)

 def _code(self,u,address,size,unused):
  if not self.consumer_phase:return super()._code(u,address,size,unused)
  r=self.current
  if r is None:return
  args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
  if self.pending_status and address==self.pending_status['return_pc']:
   call=self.pending_status;need(self.reg(UC_ARM_REG_SP)==call['sp'] and [self.reg(v) for v in F.G.SAVED]==call.pop('saved'),'native status return ABI')
   call['value']=self.reg(UC_ARM_REG_R0);r.setdefault('status_calls',[]).append(call);self.pending_status=None
  if address==STATUS:
   need(args[:2]==[BS,CTX] and self.word(CTX+0x50)==0,'native status entry ABI/state0')
   if self.reg(UC_ARM_REG_LR)&~1==0x0224C3CC:self.pending_status=dict(return_pc=0x0224C3CC,sp=self.reg(UC_ARM_REG_SP),saved=[self.reg(v) for v in F.G.SAVED])
  if address in (0x022479C0,0x022633F0):
   need(args[:2]==[BS,CTX],'consumer UI ABI')
   if address==0x022479C0:
    need(all(STACK-4096<=v and v+32<=STACK for v in args[2:4]),'message formatter stack pointers')
    values=struct.unpack('<3I',bytes(u.mem_read(args[2],12)));need(values==(181,2,1),'native parsed flinch message data')
    self.last_message=values;name='message formatter omitted'
   else:
    need(self.last_message==(181,2,1) and STACK-4096<=args[2] and args[2]+36<=STACK,'message emit ABI/parsed data');name='message emit omitted'
   r['models'].append(dict(name=name,args=args));self._return(u,0);return
  if address==0x02025358:need(self.word(KEYS)==0 and int.from_bytes(u.mem_read(TOUCH,2),'little')==0,'declared no-input fixture')
  if address==0x0224EDE0 and args[2] in (85,86):
   need(args==[CTX,self.attacker,args[2],0] and not self.word(CTX+0x2DCC+192*self.attacker)&0x30000000,'native activation-flag getter ABI/neutral flags');return H.HPPathCPU._code(self,u,address,size,unused)
  return super()._code(u,address,size,unused)

 def _write(self,u,access,address,size,value,unused):
  if self.consumer_phase:
   try:return super()._write(u,access,address,size,value,unused)
   except ValueError as error:raise ValueError(str(error)+' consumer PC='+hex(self.reg(UC_ARM_REG_PC))) from error
  return super()._write(u,access,address,size,value,unused)

 def boundary(self,actor):
  before=[self.word(CTX+0x2DB0+192*b) for b in (0,1)];self.attacker=actor;self.target=actor
  for off,value in ((0x64,actor),(0x6C,1-actor),(8,23),(12,23),(0x48,0),(0x50,0),(0x3044,33),(0x3040,33),(0x2184,0)):
   self._word(CTX+off,value)
  self._word(BS+0x44,2)
  need(before==[self.word(CTX+0x2DB0+192*b) for b in (0,1)],'next-action boundary changed a status word')
  return dict(actor=actor,move=33,status_words_preserved=before,selection='controlled host boundary; natural execution-order selection not executed')

 def observe_action(self,*,actor=1,direct_status=False):
  need(type(actor) is int and actor in (0,1) and type(direct_status) is bool,'consumer fixture domain')
  effect=super().observe(base_status=0);E.require_effect(effect)
  boundary=self.boundary(actor);self.consumer_phase=True;self.consumer_requests=[];self.pending_status=None;self.last_message=None
  status_before=self.word(CTX+0x2DB0+192*actor);seed=self.word(BS+F.G.SEED_OFFSET);runs=[]
  try:
   if direct_status:
    run=self.execute_path(STATUS,'consume');runs.append(dict(entry='status_direct',run=run))
   else:
    for _ in range(64):
     command=self.word(CTX+8)
     if command==39:break
     need(command in (22,23),'consumer caller command')
     entry=TRY if command==23 else H.RUN;run=self.execute_path(entry,'consume');runs.append(dict(entry='try_move' if command==23 else 'script',run=run))
    else:raise ValueError('consumer resume budget')
  finally:self.consumer_phase=False
  return dict(effect=effect,boundary=boundary,direct_status=direct_status,actor_status_before=status_before,actor_status_after=self.word(CTX+0x2DB0+192*actor),target1_status_after=self.word(CTX+0x2DB0+192),
   move_fail_after=self.word(CTX+0x344+4*actor),move_status_after=self.word(CTX+0x216C),battle_status_after=self.word(CTX+0x213C),final_command=self.word(CTX+8),status_check_state=self.word(CTX+0x50),try_move_state=self.word(CTX+0x48),
   consumer_requests=list(self.consumer_requests),seed_before=seed,seed_after=self.word(BS+F.G.SEED_OFFSET),runs=runs,
   no_input=dict(keys=self.word(KEYS),touch=int.from_bytes(self.uc.mem_read(TOUCH,2),'little')))


def require_consumer(result):
 E.require_effect(result['effect']);actor=result['boundary']['actor']
 need(type(actor) is int and actor in (0,1) and result['boundary']['move']==33 and type(result['direct_status']) is bool,'consumer reported fixture domain')
 before=result['effect']['status_after'] if actor==1 else 0
 need(result['boundary']['status_words_preserved']==[0,result['effect']['status_after']] and result['actor_status_before']==before,'consumer boundary changed produced bit')
 need(result['actor_status_after']==0 and result['seed_after']==result['seed_before']==result['effect']['seed_after'],'consumer status clear/RNG neutrality')
 need(result['no_input']==dict(keys=0,touch=0),'consumer input fixture drift')
 runs=result['runs'];writes=[w for row in runs for w in row['run']['writes']]
 states=[w['value'] for w in writes if w['address']==hex(CTX+0x50)]
 if not before&8:
  need(result['direct_status'] and len(runs)==1 and runs[0]['run']['result']==0,'absent-bit native status return')
  need(result['consumer_requests']==[] and result['final_command']==23 and result['move_fail_after']==0 and not result['move_status_after']&0x80000000,'absent-bit falsely canceled action')
  need(states==list(range(1,17))+[0] and result['status_check_state']==0,'absent-bit full status loop')
  need(result['target1_status_after']==result['effect']['status_after'],'another actor consumed target bit');return
 need(result['target1_status_after']==0,'consumer target summary drift')
 need(not result['direct_status'] and result['consumer_requests']==[278,15] and result['final_command']==39,'native cancellation caller/script route')
 need(result['move_fail_after']==0x40 and result['move_status_after']==0x80000000 and result['battle_status_after']&2,'native flinch failure flags')
 need(states==list(range(1,7)) and result['status_check_state']==6 and result['try_move_state']==1,'native status state0→5 / early TryMove return')
 calls=[call for row in runs for call in row['run'].get('status_calls',[])]
 need(len(calls)==1 and calls[0]['value']==1 and calls[0]['return_pc']==0x0224C3CC,'native caller status BOOL/ABI')
 need(len(runs)==36 and [row['entry'] for row in runs[:3]]==['try_move','script','try_move'],'native caller resumption sequence')
 quick=runs[1]['run']['script_commands'];need([(x['pc'],x['cursor']) for x in quick]==[(hex(COMMANDS[o]),p) for o,p in ((33,0),(33,6),(224,64))],'neutral native Quick Claw script path')
 flinch=[(x['pc'],x['cursor']) for row in runs[3:] for x in row['run']['script_commands']]
 expected=[(hex(COMMANDS[18]),0),(hex(COMMANDS[14]),4)]+[(hex(COMMANDS[30]),5)]*31+[(hex(COMMANDS[o]),p) for o,p in ((65,7),(55,9),(224,28))]
 need(flinch==expected,'native flinched script/31 wait polls path')
 counter=[w['value'] for w in writes if w['pc']=='0x223e366'];need(counter==list(range(1,31))+[0],'native wait counter rewind/reset')
 clears=[w for w in writes if w['pc']=='0x224b7a0']
 fails=[w for w in writes if w['pc']=='0x224b7ac']
 need(fails==[dict(pc='0x224b7ac',address=hex(CTX+0x344+4*actor),bytes=4,value=0x40)],'native flinch failure store')
 need(clears==[dict(pc='0x224b7a0',address=hex(CTX+0x2DB0+192*actor),bytes=4,value=0)],'native flinch-bit clear store')
 need(not any(0x0224C3D0<=int(code['ram'],16)<0x0224C4C4 for row in runs for code in row['run']['code']),'TryMove reached PP/disobedience/attack stages after cancellation')


def compare_native(model,current,role):
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 shift=int(model['record']['overlays'][1]['ram'],16)-F.U.OVERLAY_BASE;records=[];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 for a,n,digest in WINDOWS:
  if a<F.U.OVERLAY_BASE:
   raw=F.G.piece(model['segments'],a,n);normal=bytearray(raw);actual=a
  else:raw=F.take(model['overlay'],a,n);normal=bytearray(raw);actual=a+shift
  fields=[]
  if shift and a>=F.U.OVERLAY_BASE:
   ref=F.take(current['overlay'],a,n)
   for lo,hi in ConsumerCPU.code_ranges[len(E.EffectCPU.code_ranges):]:
    lo=max(lo,a);hi=min(hi,a+n)
    if lo>=hi:continue
    for ins in md.disasm(ref[lo-a:hi-a],lo):
     if ins.mnemonic in ('bl','blx') and ins.op_str.startswith('#'):
      target=int(ins.op_str[1:],0)
      if target<F.U.OVERLAY_BASE:
       at=ins.address-a;need(F.G.S.SHARED.branch(raw[at:at+4],ins.address+shift,ins.mnemonic)==target,'consumer regional native call')
       length=6 if target==0x02025358 else 32
       need(F.G.piece(model['segments'],target,length)==F.G.piece(current['segments'],target,length),'consumer regional ARM9 target entry')
       normal[at:at+4]=ref[at:at+4];fields.append(dict(offset=hex(at),target=hex(target)))
   for owner,literal,load,target,length in ((0x02252DC4,0x02252DF4,0x02252DD6,0x0226CB7C,12),(0x02252DF8,0x02252E2C,0x02252E0C,0x0226CBA2,28)):
    if a!=owner:continue
    at=literal-a;pc=load-a
    need(ref[pc:pc+2]==raw[pc:pc+2]==bytes.fromhex('074c'),'consumer regional table LDR')
    need(struct.unpack_from('<I',raw,at)[0]==target+shift and struct.unpack_from('<I',ref,at)[0]==target,'consumer regional table pointer')
    table=F.take(current['overlay'],target,length)
    need(F.take(model['overlay'],target,length)==table,'consumer regional table bytes')
    normal[at:at+4]=ref[at:at+4];fields.append(dict(offset=hex(at),target=hex(target+shift),table_bytes=length,table_sha256=sha(table)))
  if shift and a in (0x02025358,0x0223E2F0):
   # The two native readers address the same System input fields through bases
   # separated by0x40. Admit these exact pointer fields only, never execute a
   # normalized historical image or infer a general RAM relocation.
   for address,base in ((0x02025360,0x021D114C),(0x0223E37C,0x021D110C)):
    old=F.G.piece(model['segments'],address,4) if address<F.U.OVERLAY_BASE else F.take(model['overlay'],address,4)
    refword=F.G.piece(current['segments'],address,4) if address<F.U.OVERLAY_BASE else F.take(current['overlay'],address,4)
    need(struct.unpack('<I',old)[0]==base+shift and struct.unpack('<I',refword)[0]==base,'consumer regional input pointer pair')
   literal=0x02025360 if a==0x02025358 else 0x0223E37C;at=literal-a
   normal[at:at+4]=struct.pack('<I',0x021D114C if a==0x02025358 else 0x021D110C)
   fields.append(dict(offset=hex(at),regional_input_pointer=True,shift=shift))
  need(sha(normal)==digest,'consumer native full window '+role+' '+hex(a));records.append(dict(ram=hex(actual),bytes=n,sha256=sha(raw),comparison_only_fields=fields))
 return records


def analyze(rom,v4,base,retail,language):
 import gc
 current=F.G.S.SHARED.read_current(rom,language);data=resources(rom,current);inputs=[];windows=[];lineage=[]
 for role,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom)):
  model=current if role=='r4' else F.G.S.SHARED.read_image(path,language,role)
  windows.append(dict(input=role,vm=H.compare_windows(model,current,role),after=A.compare_native(model,current,role),effect=E.compare_native(model,current,role),consumer=compare_native(model,current,role)))
  scripts=read_consumer_scripts(path);lineage.append(dict(input=role,scripts=[dict(member=i,bytes=len(b),sha256=sha(b)) for i,b in scripts.items()]));inputs.append(model['record']);del model;gc.collect()
 runs=[]
 for name,model,variant,opts in (('caller_cancellation',current,'current',{}),('other_actor_status',current,'current',dict(actor=0,direct_status=True)),('old_hooks_status',F.counter_image(current,'old_hooks'),'old_hooks',dict(direct_status=True))):
  result=ConsumerCPU(model,data,variant=variant).observe_action(**opts);require_consumer(result);runs.append(dict(name=name,result=result));gc.collect()
 return dict(schema='flinch-native-consumer-v1',language=language,inputs=inputs,windows=windows,script_lineage=lineage,resources=data['record'],runs=runs,compilation_performed=False,
  compatibility_gates=dict(native_status_consumption=True,native_caller_cancellation=True,no_item_cancellation=False),
  source_sha256={str(p.relative_to(F.G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(E.__file__),Path(A.__file__),F.U.NATIVE)},
  limits=['P23 actual bit is preserved across a controlled host next-action selection boundary; natural execution-order selection is not executed',
   'Positive native TryMove0→QuickClaw278→TryMove1→CheckAttackerStatus0..5→Flinched15→command39; UpdateMoveHistory39/ActionEnd40/action-done writes are not executed',
   'Absent-bit and other-actor controls execute full CheckAttackerStatus directly and return false; this is not successful PP/disobedience/target/move execution',
   'Native no-input wait runs31 VM polls; polls are not measured rendering frames or wall-clock timing',
   'Native message parser executes; formatter and message emission are explicit omitted UI models, NARC/Ready/cache/Party transport retain preceding models',
   'No Steadfast/other statuses/whole pivot/SAVE/cold restart/hardware/timing/game repair claim'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 for path in (args.rom,args.v4,args.base,args.retail):
  if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input')
 result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
 args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
 print(args.language,'native flinch consumer/cancellation to39 verified; no-item compatibility FAIL; action-end40 not executed')
 raise SystemExit(1)


if __name__=='__main__':main()
