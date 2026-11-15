#!/usr/bin/env python3
"""Observe R0 liveness after four modeled void SDK services in native rematch bodies.

The loader/reader prefix is outside this case. No code or original input is written.
"""
from pathlib import Path
import importlib.util,mmap,json,gzip,collections
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_ARM
from capstone.arm_const import ARM_REG_R0
import capstone.arm_const as ARM
s=importlib.util.spec_from_file_location('sdk_return_full_dependency',Path(__file__).with_name('attribuisci_squadra_completa.py'));F=importlib.util.module_from_spec(s);s.loader.exec_module(F);P,M,B,C=F.P,F.M,F.B,F.C;need=F.need
VOID=('Heap_Free','ReadWholeNarcMemberByIdPair','NARC_ReadFromMember','NARC_Delete')

def condition(cc,cpsr):
 n,z,c,v=[bool(cpsr&(1<<b)) for b in (31,30,29,28)]
 predicates={ARM.ARM_CC_EQ:z,ARM.ARM_CC_NE:not z,ARM.ARM_CC_HS:c,ARM.ARM_CC_LO:not c,ARM.ARM_CC_MI:n,ARM.ARM_CC_PL:not n,ARM.ARM_CC_VS:v,ARM.ARM_CC_VC:not v,ARM.ARM_CC_HI:c and not z,ARM.ARM_CC_LS:not c or z,ARM.ARM_CC_GE:n==v,ARM.ARM_CC_LT:n!=v,ARM.ARM_CC_GT:not z and n==v,ARM.ARM_CC_LE:z or n!=v,ARM.ARM_CC_AL:True,ARM.ARM_CC_INVALID:True}
 need(cc in predicates,'unqualified ARM predicate');return predicates[cc]

class Observer(F.Full):
 latest=None;return_mode='observe'
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);Observer.latest=self;self.taint=None;self.events=[];self.diagnostic=False;self.pending_confirmation=None;self.decode_cache={};self.decoders={}
  for thumb in (False,True):
   decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB if thumb else CS_MODE_ARM);decoder.detail=True;self.decoders[thumb]=decoder
 def instruction(self,u,a,n):
  thumb=bool(u.reg_read(P.UC_ARM_REG_CPSR)&32);blob=bytes(u.mem_read(a,n));key=(a,n,thumb,blob)
  if key not in self.decode_cache:
   instructions=list(self.decoders[thumb].disasm(blob,a));need(len(instructions)==1 and instructions[0].size==n,'P32 instruction/mode decode');ins=instructions[0];reads,writes=ins.regs_access();need(ins.mnemonic not in ('svc','hvc','smc','it','itt','ite'),'unqualified implicit argument/ThumbIT use');self.decode_cache[key]=(ins,tuple(reads),tuple(writes))
  ins,reads,writes=self.decode_cache[key];return dict(pc=hex(a),bytes=n,thumb=thumb,sha256=P.sha(blob),mnemonic=ins.mnemonic,operands=ins.op_str,executed=condition(ins.cc,u.reg_read(P.UC_ARM_REG_CPSR)),reads_r0=ARM_REG_R0 in reads,writes_r0=ARM_REG_R0 in writes)
 def finish(self,result,pc):
  self.taint.update(outcome=result,end_pc=hex(pc),r0_before_final_instruction=self.reg(0));
  if result=='overwritten_before_read':self.pending_confirmation=self.taint
  self.events.append(self.taint);self.taint=None
 def step(self,u,a,n,unused):
  if self.pending_confirmation is not None:
   event=self.pending_confirmation;previous=event['path'][-1];need(a==int(previous['pc'],16)+previous['bytes'],'clobber instruction did not execute sequentially');event.update(overwrite_confirmed=True,post_instruction_pc=hex(a),r0_after_overwrite=self.reg(0));self.pending_confirmation=None
  if self.mon:
   need(not self.poison,'R0 observer requires other SDK volatile poisoning OFF')
   e=self.pending_service
   if e is not None and a==e['return_pc'] and e['name'] in VOID:
    need(self.taint is None,'unclosed previous R0 taint at another service return');before=self.regs();old=self.reg(0)
    if self.return_mode in ('zero','ones'):u.reg_write(B.R[0],0 if self.return_mode=='zero' else 0xFFFFFFFF)
    after=self.regs();need(before[1:]==after[1:],'R0 probe changed another register');self.taint=dict(service=e['name'],rpc=hex(a),sp=self.sp(),before_r0=old,injected_r0=self.reg(0),mode=self.return_mode,non_r0_regs_unchanged=True,path=[])
   if self.return_mode=='diagnostic' and a==0x206DE38 and not self.diagnostic:
    need(self.taint is None,'diagnostic reentry');self.diagnostic=True;self.taint=dict(service='diagnostic_live_constructor_r0',rpc=hex(a),sp=self.sp(),before_r0=self.reg(0),injected_r0=self.reg(0),mode=self.return_mode,non_r0_regs_unchanged=True,path=[])
   if self.taint is not None:
    if a in B.STUBS:self.finish('read_at_modeled_sdk_argument',a)
    else:
     detail=self.instruction(u,a,n);self.taint['path'].append(detail);need(len(self.taint['path'])<=64,'R0 window instruction budget')
     if detail['executed'] and detail['reads_r0']:self.finish('read_before_write',a)
     elif detail['executed'] and detail['writes_r0']:self.finish('overwritten_before_read',a)
  return super().step(u,a,n,unused)

s=importlib.util.spec_from_file_location('sdk_return_independent_reader',Path(__file__).with_name('rileggi_sdk_void.py'));R=importlib.util.module_from_spec(s);s.loader.exec_module(R)


def neutrality_signature(full):
 """Ignore only deliberately varied void-result logs; retain all guest evidence."""
 import copy
 projection=copy.deepcopy(full)
 for record in (projection,projection['first']):
  for event in record['models']:
   if event['name'] in VOID:event['result']='unspecified void-service R0'
 projection['first_receipt_sha256']=P.sha(json.dumps(projection['first'],sort_keys=True).encode())
 return P.sha(json.dumps(projection,sort_keys=True).encode())


def run_case(model,raw,language,codes,trainer=713,seed=0x12345678,mode='observe'):
 need(mode in ('observe','zero','ones','diagnostic'),'SDK R0 probe mode domain')
 class Selected(Observer):return_mode=mode
 with P.patch.object(F,'Full',Selected):full=F.run_case(model,raw,language,*codes,trainer=trainer,seed=seed,poison=False)
 audit=Observer.latest;need(audit.taint is None and audit.pending_confirmation is None,'SDK R0 observation unfinished at constructor return');counts=dict(collections.Counter(e['outcome'] for e in audit.events));return dict(language=language,trainer=trainer,seed=seed,mode=mode,counts=counts,events=audit.events,full=full,neutrality_signature=neutrality_signature(full))


def analyze(rom,language,objects,strategy_object,trainer=713,seed=0x12345678,mode='observe'):
 recipe=F.attest_recipe_sources();model=P.G.S.SHARED.read_current(rom,language);post_form=M.attest_post_form(model)
 with rom.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
  prefix,proof=F.A.attest_objects(raw,model,objects);strategy=M.attest_strategy_object(model,raw,strategy_object);codes=(prefix,C.qualify_code(model,strategy),*M.qualify(model,language),*F.qualify(model,language));templates,diagnostic,locations=R.raw_templates(raw,model,language);data=F.resources(raw,model);capture=run_case(model,raw,language,codes,trainer,seed,mode);R.require_capture(capture,data,templates,diagnostic,allow_diagnostic=True)
 return dict(schema='sdk-void-r0-v1',language=language,input=model['record'],mode=mode,recipe_sources=recipe,prefix_proof=proof,strategy_elf=strategy,post_form_recipe=post_form,capture=capture,locations=locations,
  source_sha256={str(p.relative_to(P.SOURCE)):P.sha(p.read_bytes()) for p in (Path(__file__),Path(R.__file__),Path(F.__file__),Path(M.__file__),R.WINDOWS)},
  conclusions=dict(body_teardown_scope_only=True,void_return_first_write_observed=True,diagnostic_live_read=mode=='diagnostic',installed_activation=0,natural_activation_observed=False),
  limits=['Four modeled void services only during CreateMon bodies and constructor teardown,not overlay-loader/native-reader seam prefix','Actual windows are unconditional Thumb,1..4 instructions; ARM predicates are guarded/unit-tested but no tainted ARM execution is qualified','Instruction/return evidence reuses exact Full pipeline admission; no native SDK implementation/allocator/FS failure execution','Zero/ones vary only void R0,all other register-poisoning is OFF; no code,ROM,save or gameplay change'])


def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('rom','objects','strategy-object','json'):p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--language',choices=('EN','IT'),required=True);p.add_argument('--trainer',type=int,choices=(712,713),default=713);p.add_argument('--seed',type=lambda x:int(x,0),choices=(0x12345678,0x12345679),default=0x12345678);p.add_argument('--mode',choices=('observe','zero','ones','diagnostic'),default='observe');a=p.parse_args()
 try:
  need(not a.json.exists() and not a.json.is_symlink(),'output must be fresh');need(P.SOURCE not in a.json.resolve().parents and a.json.resolve()!=P.SOURCE,'output must be outside source');need(a.objects.resolve() not in a.json.resolve().parents,'output must be outside retained objects')
  for path in (a.rom,a.objects/'rematch-variants.o',a.objects/'rematch-stub.o',a.strategy_object):need(path.is_file() and path.resolve()!=a.json.resolve(),'SDK input/output identity')
  r=analyze(a.rom,a.language,a.objects,a.strategy_object,a.trainer,a.seed,a.mode);payload=(json.dumps(r,separators=(',',':'))+'\n').encode();need(len(payload)<=16*1024*1024,'SDK return output budget');a.json.parent.mkdir(parents=True,exist_ok=True)
  with a.json.open('xb') as output:
   if a.json.suffix=='.gz':
    with gzip.GzipFile(fileobj=output,mode='wb',filename='',mtime=0) as g:g.write(payload)
   else:output.write(payload)
 except ValueError as e:p.exit(2,str(e)+'\n')
 print(a.language,a.trainer,a.mode,'SDK R0 windows verified against raw instructions; prefix/native SDK internals remain outside coverage')


if __name__=='__main__':main()
