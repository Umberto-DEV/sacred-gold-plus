#!/usr/bin/env python3
"""Independently reread SDK-return windows, instructions and caller bindings from ROM."""
from pathlib import Path
import importlib.util,json,mmap,gzip,collections
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from capstone.arm_const import ARM_REG_R0,ARM_CC_AL,ARM_CC_INVALID
s=importlib.util.spec_from_file_location('sdk_reread_full_dependency',Path(__file__).with_name('attribuisci_squadra_completa.py'));F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
P,B,C=F.P,F.B,F.C;need=F.need
WINDOWS=Path(__file__).parents[1]/'test/sdk-return-windows.json'
VOID=('Heap_Free','ReadWholeNarcMemberByIdPair','NARC_ReadFromMember','NARC_Delete')
RETURN_FUNCTIONS={0x20263A0:0x2026380,0x206F4C8:0x206EDE8,0x206FBC0:0x206FBB0,0x206FD2C:0x206FD14,0x2071FDA:0x2071FC8,0x20725C6:0x20725B4}


def window_key(service,rpc,steps):return service,rpc,tuple(x.get('pc',x.get('ram')) for x in steps)


def raw_templates(raw,model,language):
 """This reader has no Unicorn instance and never calls Observer.instruction."""
 q=json.loads(WINDOWS.read_text());need(q['schema']==1 and len(q['windows'])==19,'SDK return window schema/count');view=P.G.S.SHARED.gifts_audit.Arm9View(raw);qualified,_=F.qualify(model,language);cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB);cs.detail=True;decoded={};templates={};locations={}
 def decode(step):
  a=int(step['ram'],16);n=step['bytes'];need(step['thumb'] and qualified.get(a)==(n,True),'SDK window qualified mode/PC');blob=view.read(a,n);need(blob==C.bench_bytes(model,a,n) and P.sha(blob)==step['sha256'],'independent SDK raw section bytes');ins=list(cs.disasm(blob,a));need(len(ins)==1 and ins[0].size==n and ins[0].cc in (ARM_CC_AL,ARM_CC_INVALID),'SDK window unconditional Thumb decode');reads,writes=ins[0].regs_access();d=dict(pc=hex(a),bytes=n,thumb=True,sha256=P.sha(blob),mnemonic=ins[0].mnemonic,operands=ins[0].op_str,executed=True,reads_r0=ARM_REG_R0 in reads,writes_r0=ARM_REG_R0 in writes);decoded[a]=d;locations[a]=dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=P.sha(blob));return d
 for row in q['windows']:
  need(row['service'] in VOID and row['return_pc']==row['steps'][0]['ram'],'SDK window service/return');steps=[decode(x) for x in row['steps']];need(1<=len(steps)<=4,'SDK qualified window bound');need(all(not x['reads_r0'] and not x['writes_r0'] for x in steps[:-1]) and not steps[-1]['reads_r0'] and steps[-1]['writes_r0'],'SDK raw read-before-write proof')
  need(row['overwrite_pc']==steps[-1]['pc'] and int(row['post_instruction_pc'],16)==int(steps[-1]['pc'],16)+steps[-1]['bytes'],'SDK raw clobber endpoint')
  edges={int(x['pop'],16):x for x in row['return_bindings']};used=set()
  for first,second in zip(steps,steps[1:]):
   a=int(first['pc'],16);dest=int(second['pc'],16)
   if first['mnemonic']=='pop' and 'pc' in first['operands']:
    need(a in RETURN_FUNCTIONS and a in edges,'unattributed SDK return POP');e=edges[a];need(e==dict(pop=hex(a),caller_return=hex(dest),caller_bl=hex(dest-4),function_entry=hex(RETURN_FUNCTIONS[a])),'SDK return binding geometry');call=view.read(dest-4,4);need(qualified.get(dest-4)==(4,True) and P.G.S.SHARED.branch(call,dest-4,'bl')==RETURN_FUNCTIONS[a],'independent SDK POP/caller BL binding');used.add(a)
   else:need(dest==a+first['bytes'],'SDK straight-line window flow')
  need(used==set(edges),'unused SDK return binding');key=window_key(row['service'],row['return_pc'],row['steps']);need(key not in templates,'duplicate SDK window');templates[key]=dict(row=row,decoded=steps)
 diag=q['diagnostic'];diag_decoded=[decode(x) for x in diag['steps']];need(len(diag_decoded)==1 and diag['read_pc']=='0x206de38' and diag_decoded[0]['reads_r0'],'SDK live-R0 diagnostic source');return templates,diag_decoded,list(locations.values())


def neutrality_signature(full):
 import copy
 record=copy.deepcopy(full)
 for container in (record,record['first']):
  for event in container['models']:
   if event['name'] in VOID:event['result']='unspecified void-service R0'
 record['first_receipt_sha256']=P.sha(json.dumps(record['first'],sort_keys=True).encode())
 return P.sha(json.dumps(record,sort_keys=True).encode())


def require_capture(r,data,templates,diagnostic_steps,*,allow_diagnostic=False):
 F.require_complete(r['full'],data);need(not r['full']['poison'] and r['neutrality_signature']==neutrality_signature(r['full']),'SDK isolated R0 mode/neutrality projection');mode=r['mode'];need(mode in ('observe','zero','ones') or(allow_diagnostic and mode=='diagnostic'),'SDK probe accepted mode');need(r['language'] in ('EN','IT') and (r['trainer'],r['seed'])==(r['full']['trainer'],r['full']['seed']),'SDK probe fixture identity')
 model_events=[e for e in r['full']['models'] if e['name'] in VOID];events=r['events'];live=[e for e in events if e['service']=='diagnostic_live_constructor_r0'];actual=[e for e in events if e['service']!='diagnostic_live_constructor_r0']
 need(len(actual)==len(model_events),'complete SDK void return observation count');need(len(live)==int(mode=='diagnostic'),'SDK live control count')
 for event,model in zip(actual,model_events):
  need(event['service']==model['name'] and event['rpc']==hex(model['return_pc']) and event['mode']==mode and event['sp']==model['return_sp'],'SDK exact service/return/stack correlation');before=B.LOADER_RESULT if model['name']=='ReadWholeNarcMemberByIdPair' else model['args'][0];expected=0 if mode=='zero' else 0xFFFFFFFF if mode=='ones' else before
  need(event['before_r0']==before and event['injected_r0']==expected and model['result']==expected and event['non_r0_regs_unchanged'],'SDK exact modeled R0 intervention/other-register neutrality');key=window_key(event['service'],event['rpc'],event['path']);need(key in templates,'SDK unknown actual continuation window');template=templates[key]
  need(event['path']==template['decoded'],'SDK actual path differs from independent raw instruction/register reread');need(event['outcome']=='overwritten_before_read' and event['end_pc']==template['row']['overwrite_pc'] and event['overwrite_confirmed'] and event['post_instruction_pc']==template['row']['post_instruction_pc'] and type(event['r0_after_overwrite']) is int and 0<=event['r0_after_overwrite']<=0xFFFFFFFF,'SDK overwrite actual execution confirmation');need(event['r0_before_final_instruction']==expected,'SDK R0 value before first kill')
 if live:
  e=live[0];need(e['mode']=='diagnostic' and e['path']==diagnostic_steps and e['outcome']=='read_before_write' and e['end_pc']=='0x206de38' and e['before_r0']==e['injected_r0']==B.ARENA+128 and e['non_r0_regs_unchanged'],'SDK live-source calibration')
 counts=dict(collections.Counter(e['outcome'] for e in events));need(r['counts']==counts and counts.get('overwritten_before_read')==len(model_events) and counts.get('read_before_write',0)==int(mode=='diagnostic'),'SDK summary/capture event consistency');return True


def analyze(rom,language,report):
 model=P.G.S.SHARED.read_current(rom,language);need(report.stat().st_size<=16*1024*1024,'SDK readback compressed input budget')
 with (gzip.open(report,'rb') if report.suffix=='.gz' else report.open('rb')) as source:payload=source.read(16*1024*1024+1)
 need(len(payload)<=16*1024*1024,'SDK readback expanded input budget');result=json.loads(payload);need(result['schema']=='sdk-void-r0-v1' and result['language']==language and result['input']==json.loads(json.dumps(model['record'])),'SDK readback exact ROM/report identity')
 with rom.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
  templates,diagnostic,locations=raw_templates(raw,model,language);need(result['capture']['language']==language,'SDK capture language identity');data=F.resources(raw,model);require_capture(result['capture'],data,templates,diagnostic,allow_diagnostic=True)
 return dict(schema='sdk-void-r0-readback-v1',language=language,input=model['record'],report_sha256=P.sha(report.read_bytes()),windows_sha256=P.sha(WINDOWS.read_bytes()),events=len(result['capture']['events']),locations=locations,qualified=True,native_sdk_internals_executed=False)


def main():
 import argparse
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('rom','report','json'):p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--language',choices=('EN','IT'),required=True);a=p.parse_args()
 try:
  need(not a.json.exists() and not a.json.is_symlink(),'output must be fresh');need(P.SOURCE not in a.json.resolve().parents and a.json.resolve()!=P.SOURCE,'output must be outside source');need(a.rom.is_file() and a.report.is_file(),'SDK readback inputs must exist');r=analyze(a.rom,a.language,a.report);a.json.parent.mkdir(parents=True,exist_ok=True)
  with a.json.open('x') as f:json.dump(r,f,indent=2);f.write('\n')
 except ValueError as e:p.exit(2,str(e)+'\n')
 print(a.language,'SDK windows reread independently; caller bindings and first R0 overwrite verified')


if __name__=='__main__':main()
