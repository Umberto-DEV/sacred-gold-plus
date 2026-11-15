#!/usr/bin/env python3
"""Follow native HP and AfterDamage states0..6 through their neutral scripts."""
import importlib.util,json,mmap,struct
from pathlib import Path
spec=importlib.util.spec_from_file_location('after_native_vm',Path(__file__).with_name('attribuisci_hp_flinch.py'))
H=importlib.util.module_from_spec(spec);spec.loader.exec_module(H)
F=H.F
need,sha=F.need,F.sha
CTX,BS,STACK,STOP=H.CTX,H.BS,H.STACK,H.STOP
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3
SCRIPTS={16:'fe5396d502582ed49c1f9ed85f9fb65851b12e0bed6a877c779b573a66dbdb61',293:'ab0c96cc5eea84c41088214cbc3460414ac0d149d3fd6aa85fac26ee7f383726'}
WINDOWS=((0x0224DF7C,28,'47a7120edad4162d1f1323f99faab50f32c325a0af943c00e0570dcc13289a80'),
 (0x0224DF98,84,'42a8ff76d3263ac9fd533ee370c91f0573237c60d7148d5fb017cea4251802b4'),
 (0x0224DFEC,140,'a95b16b3bffa4443735c3c0511fa50579a43e831117004fd1a0d680f26a68364'),
 (0x02250490,580,'04e26daa7254c777164a204e743eda1c963548d3a51218d74dcb9a1a051559a7'),
 (0x02253E04,1436,'5f68175c69152510cdfaeeeba5829cad5db5c6bcb05d74d24dd8dca9dcc4f7c6'),
 (0x02256838,28,'96c893ddba715b7502c1e980db04e6182653ee505a8eeed3d49fd849f562d8fe'))

EXTRA_WINDOWS=(
 (0x0223E474,184,'d48dd4e853af3612bc415a5b7da4454fab91c51fac7412f50a28a806e357a429'),
 (0x0224EDE0,34,'278a8b42e6ab6f44a2b9877f91b4168888ab037d7152ed73ff0d1ad8fd2404e7'),
 (0x0224EECC,4,'b89baf883cf81a447626e21049d45806b104c0a779a7bb6d7821ebd7f967c931'),
)


def read_after_scripts(rom):
 spec=importlib.util.spec_from_file_location('after_raw_archive',F.G.SOURCE/'features/borsa/tools/attribuisci.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
 with Path(rom).open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:members,record=reader.raw_archive(raw,'a/0/0/1')
 need(record['file_id']==130 and len(members)==297,'AfterDamage script archive geometry')
 subs={}
 for i,digest in SCRIPTS.items():need(sha(members[i])==digest,'AfterDamage subscript identity');subs[i]=members[i]
 return subs


def resources(rom,model):
 data=H.resources(rom,model);subs={2:data['hp_script'],**read_after_scripts(rom)}
 data.update(subscripts=subs);data['record']['after_scripts']=[dict(member=i,bytes=len(subs[i]),sha256=sha(subs[i])) for i in SCRIPTS]
 return data


class AfterCPU(H.HPPathCPU):
 code_ranges=H.RANGES+((0x0224DF7C,0x0224DF96),(0x0224DF98,0x0224DFE6),(0x0224DFEC,0x0224E06A),
  (0x02250490,0x022506AE),(0x02253E04,0x02254386),(0x02256838,0x02256852),
  (0x0223E474,0x0223E4D2),(0x0223E4E0,0x0223E52A),
  (0x02247698,0x022476A8),(0x022476E0,0x022476E4),
  (0x0224EDE0,0x0224EE02),(0x0224EECC,0x0224EED0))
 script_commands={**H.COMMANDS,33:0x0223E474}
 script_variables=(*H.HPPathCPU.script_variables,16,44)
 side_categories=(255,2)

 @property
 def script_words(self):return len(self.resources['subscripts'][self.current_script])//4

 def __init__(self,model,data,*,variant='current'):
  super().__init__(model,data,variant=variant)
  for a,n,d in (*WINDOWS,*EXTRA_WINDOWS):need(sha(F.take(model['overlay'],a,n))==d,'AfterDamage whole native helper')
  for i,d in SCRIPTS.items():need(sha(data['subscripts'][i])==d,'AfterDamage script fixture drift')
  need(F.take(model['overlay'],0x0226C6C8+4*33,4)==struct.pack('<I',0x0223E475),'native mon comparison dispatch')
  need(struct.unpack('<h',F.take(model['overlay'],0x0224EE02,2))[0]+0x0224EE04==0x0224EECC,'native species getter table case0')
  self.current_script=2;self.script_requests=[]

 def model_context_ranges(self,phase):
  return ((0x2700,0x288C),(0xB4,0xB8)) if phase=='after' else super().model_context_ranges(phase)

 def store_contract(self,phase):
  result=dict(super().store_contract(phase))
  if phase=='after':
   for pc in (0x0224CADC,0x0224CAEC,0x0224CAFE,0x0224CB32,0x0224CB4A,0x0224CB5C,
              0x0224CBB8,0x0224CBC8,0x0224CBFC,0x0224CC14,0x0224CC24,0x0224CC4E):result[pc]=(0x3C,4)
   for pc in (0x0224DF8C,0x0224CB40,0x0224CC0A):result[pc]=(12,4)
   for pc in (0x0224DF90,0x0224CB44,0x0224CC0E):result[pc]=(8,4)
  return result

 def _seam(self,u,address,size,unused):
  if address!=F.C.READ_BATTLE_SCRIPT:return super()._seam(u,address,size,unused)
  args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)];script=args[2]
  need(args[:2]==[CTX,1] and script in (2,16,293,14),'AfterDamage native script loader ABI')
  need(self.phase==('hp' if script==2 else 'after'),'AfterDamage loader phase')
  if script!=14:
   self.current_script=script;u.mem_write(CTX+0x2700,self.resources['subscripts'][script]);self._word(CTX+0xB4,0)
  self.script_requests.append(script);self.current['models'].append(dict(name='NARC script loader',args=args,shared_word=self.word(CTX+0x2EC)))
  self._return(u,0)

 def _code(self,u,address,size,unused):
  if self.current is None:return
  args=[self.reg(v) for v in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]
  if address in (0x02250490,0x02253E04):need(args[:2]==[BS,CTX] and STACK-4096<=args[2]<=STACK-4 and args[2]%4==0,'AfterDamage helper ABI/output pointer')
  if address==0x02250490:need(self.word(CTX+0x2174)==self.word(CTX+0x2178)==0,'neutral indirect-side-effect fixture')
  if address==0x0224DFEC:need(not self.word(CTX+0x2DB0+192*self.target)&(1<<23),'neutral Rage fixture')
  if address==0x02256838:need(args[:2]==[CTX,self.target] and not self.word(CTX+0x2E8+28*self.target)&8,'native substitute ABI/domain')
  if address==0x0224EDE0:need(args==[CTX,self.target,0] and self.reg(UC_ARM_REG_R3)==0,'native species getter ABI/null output pointer')
  return super()._code(u,address,size,unused)

 def checkpoint_after(self):return dict(**self.checkpoint(),state=self.word(CTX+0x3C),current_script=self.current_script)

 def prepare_fixture(self):
  """Extend declared input fields before executing any guest instruction."""
  pass

 def observe(self,*,damage=-200,eligible=True,message_type=0):
  need(type(damage) is int and -299<=damage<=0 and type(eligible) is bool and type(message_type) is int and message_type in (0,1),'AfterDamage fixture domain')
  u=self.uc;u.mem_write(CTX,bytes(0x4000));u.mem_write(BS,bytes(0x3000));self.attacker=0;self.target=1
  u.mem_write(CTX+0x3DE,self.resources['move_cache']);self._word(CTX+0x2120,F.CACHE);self._word(CTX+0x64,0);self._word(CTX+0x6C,1)
  self._word(CTX+8,28);self._word(CTX+0x2144,damage);self._word(CTX+0x3044,33 if eligible else 44);self._word(CTX+0x2150,1);self._word(CTX+0x38,message_type)
  for b,species in ((0,1),(1,7)):
   self._word(CTX+0x2D40+192*b,species);self._word(CTX+0x2D8C+192*b,300);self._word(CTX+0x2D90+192*b,300)
   self._word(BS+0x34+4*b,H.OPP+0x300*b);u.mem_write(H.OPP+0x300*b+0x195,bytes((b,)))
  seed=((99<<16)-24691)*pow(1103515245,-1,1<<32)&0xFFFFFFFF;self._word(BS+F.G.SEED_OFFSET,seed)
  self.prepare_fixture()
  self.script_requests=[];self.current_script=2;before=self.checkpoint_after();runs=[]
  runs.append(dict(entry='hp',before=before,run=self.execute_path(H.HP,'hp'),after=self.checkpoint_after()))
  before_after=None
  for _ in range(16):
   command=self.word(CTX+8)
   if self.script_requests and self.script_requests[-1]==14 or command==31:break
   need(command in (22,29),'AfterDamage controller continuation command')
   if command==29 and before_after is None:before_after=self.word(CTX+0x3C)
   phase='script' if command==22 else 'after';entry=H.RUN if command==22 else H.AFTER
   start=self.checkpoint_after();run=self.execute_path(entry,phase);runs.append(dict(entry=phase,before=start,run=run,after=self.checkpoint_after()))
  else:raise ValueError('AfterDamage continuation budget')
  return dict(damage=damage,eligible=eligible,message_type=message_type,variant=self.variant,before=before,before_after_state=before_after,script_requests=list(self.script_requests),runs=runs,
   flinch=self.script_requests[-1:]==[14],final_word=self.word(CTX+0x2EC),final=self.checkpoint_after())


def compare_native(model,current,role):
 from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
 shift=int(model['record']['overlays'][1]['ram'],16)-F.U.OVERLAY_BASE;records=[];md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
 for a,n,d in (*WINDOWS,*EXTRA_WINDOWS):
  raw=F.take(model['overlay'],a,n);normal=bytearray(raw);fields=[]
  if shift:
   reference=F.take(current['overlay'],a,n)
   for lo,hi in AfterCPU.code_ranges[len(H.RANGES):]:
    lo=max(lo,a);hi=min(hi,a+n)
    if lo>=hi:continue
    for ins in md.disasm(reference[lo-a:hi-a],lo):
     if ins.mnemonic in ('bl','blx') and ins.op_str.startswith('#'):
      target=int(ins.op_str[1:],0)
      if target<F.U.OVERLAY_BASE:
       at=ins.address-a;need(F.G.S.SHARED.branch(raw[at:at+4],ins.address+shift,ins.mnemonic)==target,'AfterDamage regional call target')
       need(F.G.piece(model['segments'],target,32)==F.G.piece(current['segments'],target,32),'AfterDamage regional ARM9 entry signature')
       normal[at:at+4]=reference[at:at+4];fields.append(dict(offset=hex(at),target=hex(target)))
  need(sha(normal)==d,'AfterDamage native full window '+role+' '+hex(a))
  records.append(dict(ram=hex(a+shift),bytes=n,sha256=sha(raw),comparison_only_fields=fields))
 return records


def require_continuation(result):
 damage=result['damage'];word=damage&0xFFFFFFFF;current=result['variant']=='current';rng=current and damage==-200;requested=rng and result['eligible']
 need(result['before']['word']==0 and result['before']['state']==0 and result['before_after_state']==0,'AfterDamage initial state was not0')
 need(result['flinch']==requested and result['script_requests']==([2] if damage else [])+[16,293]+([14] if requested else []),'native AfterDamage script sequence/outcome')
 runs=result['runs'];need(runs[0]['after']['word']==word and runs[0]['after']['physical_damage']==word,'native AfterDamage HP writer')
 need(result['before']==runs[0]['before'] and result['final']==runs[-1]['after'] and result['final_word']==result['final']['word'],'AfterDamage summary/checkpoint mismatch')
 for prior,nxt in zip(runs,runs[1:]):need(prior['after']==nxt['before'],'host changed continuation state between entries')
 for run in runs[:-1]:need(run['after']['word']==word and run['after']['seed']==result['before']['seed'],'native intermediate damage/RNG lifetime')
 need(result['final']['hp']==300+damage and result['final_word']==(0 if current else word),'native final HP/shared word')
 need(result['final']['seed']==(F.G.next_seed(result['before']['seed']) if rng else result['before']['seed']),'native AfterDamage RNG transition')
 states=[w['value'] for run in runs for w in run['run']['writes'] if w['address']==hex(CTX+0x3C)]
 expected=list(range(1,8))+([] if requested else [0])
 need(states==expected,'AfterDamage state transition not native0..6')
 need(result['final']['command']==(22 if requested else 31),'native AfterDamage return command')
 need(result['final']['state']==(7 if requested else 0),'native AfterDamage final state')
 script_paths={16:[(32,0),(224,50)],293:[(32,0),(33,5),(224,98)]}
 for script,path in script_paths.items():
  actual=[(c['pc'],c['cursor']) for run in runs if run['entry']=='script' and run['before']['current_script']==script for c in run['run']['script_commands']]
  need(actual==[(hex(AfterCPU.script_commands[op]),cursor) for op,cursor in path],'neutral native subscript path')


def analyze(rom,v4,base,retail,language):
 import gc
 current=F.G.S.SHARED.read_current(rom,language);data=resources(rom,current);inputs=[];windows=[];lineage=[]
 for role,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom)):
  model=current if role=='r4' else F.G.S.SHARED.read_image(path,language,role)
  windows.append(dict(input=role,vm=H.compare_windows(model,current,role),after=compare_native(model,current,role)))
  inherited=read_after_scripts(path);lineage.append(dict(input=role,subscripts=[dict(member=i,bytes=len(b),sha256=sha(b)) for i,b in inherited.items()]))
  inputs.append(model['record']);del model,inherited;gc.collect()
 runs=[]
 for name,options in (('damage200',{}),('damage199',dict(damage=-199)),('zero_damage',dict(damage=0)),('Bite_ineligible',dict(eligible=False)),('message_type1',dict(message_type=1))):
  result=AfterCPU(current,data).observe(**options);require_continuation(result);runs.append(dict(name=name,result=result));gc.collect()
 old=AfterCPU(F.counter_image(current,'old_hooks'),data,variant='old_hooks').observe();require_continuation(old)
 return dict(schema='afterdamage-native-continuation-v1',language=language,inputs=inputs,windows=windows,script_lineage=lineage,resources=data['record'],runs=runs,native_baseline=old,compilation_performed=False,
  compatibility_gates=dict(native_state0_continuation=True,native_hp_script_preserves_word=True,no_item_flinch_script_request=False),
  source_sha256={str(p.relative_to(F.G.SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(H.__file__),Path(F.__file__),F.U.NATIVE)},
  limits=['Initial native HP/AfterDamage fixture starts at state0; no host state6 injection, but not a naturally played battle or move-damage calculation',
   'Critical multiplier1, target species7/nonShaymin, neutral indirect effects/Rage/ability0 are explicit bounded inputs; alternate scripts/abilities/critical/secondary-effect branches are not executed',
   'NARC script loading, ability lookup, UI emission, Ready and asynchronous Party packet transport are models with ABI/write domains; native handlers and neutral helper paths execute',
   'Script14 is requested only: its status/ability gates and target flinch bit are not executed here',
   'No full pivot, arbitrary callbacks, PartyMon encrypted mutation, SAVE, cold restart, hardware, timing or game repair claim'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 for path in (args.rom,args.v4,args.base,args.retail):
  if args.json.resolve()==path.resolve() or (args.json.exists() and path.exists() and args.json.samefile(path)):parser.error('--json must not replace an input')
 result=analyze(args.rom,args.v4,args.base,args.retail,args.language)
 args.json.parent.mkdir(parents=True,exist_ok=True);args.json.write_text(json.dumps(result,indent=2)+'\n')
 print(args.language,'native AfterDamage0..6 continuation verified; no-item flinch SCRIPT REQUEST compatibility FAIL; effect script not executed')
 raise SystemExit(1)


if __name__=='__main__':main()
