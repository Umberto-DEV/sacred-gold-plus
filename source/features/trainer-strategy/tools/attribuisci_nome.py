#!/usr/bin/env python3
"""Verify packed trainer messages through two native String copy APIs.

Requires private exact ROMs. NARC/decryption and String allocation are explicit
host boundaries. Neither the lazy message loader nor the full caller executes.
"""
from pathlib import Path
import importlib.util,json,mmap,struct,sys,gc
s=importlib.util.spec_from_file_location('name_constructor_dependency',Path(__file__).with_name('attribuisci_costruttore.py'));T=importlib.util.module_from_spec(s);s.loader.exec_module(T)
P,B,need,sha=T.P,T.B,T.need,T.P.sha
sys.path.insert(0,str(P.SOURCE/'translation'));import message_codec
sys.path.insert(0,str(P.SOURCE/'quality-audit'));import hgss_text
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_CPU_ARM_946,UC_ARM_REG_CPSR,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_ARM

# Instruction starts only: error paths for invalid pointer/magic, no-EOS
# fallback and live communication are deliberately outside this domain.
WINDOWS=(
 (0x2026A04,0x2026A10,True,'6ee06c539987ea8a011be2e3f2d90115c41b90e4530e04417eab226399b612b8'),
 (0x2026A14,0x2026A1C,True,'2fcdd3ebf23b9abf1fa47e68055f2378ac2ae7fcce7d8f9f8c23e475a103035c'),
 (0x2026A20,0x2026A52,True,'0e48f8d521b40d3c17dfee40e911f138ea6cab8a1360f8b95d9d54013f439524'),
 (0x2026A5E,0x2026A60,True,'0d4542e69834fdd98d546c52551d295d1465ce1e0870def994e76e97d60d4736'),
 (0x2026A68,0x2026A74,True,'4c39d04bd0f2e202566e8e260f005475dfd1d30aa2ccb188f81fe72a2275c16d'),
 (0x2026A78,0x2026A80,True,'f08c3c1a97ec11dba5c66b2b6fb9b65856e89e90802a6352273b45e4228a0296'),
 (0x2026A84,0x2026A9A,True,'91e927ff894eb3221d9c6e810ba88fe9cbe795acc2c00b35c4bf3ca285edd0a7'),
 (0x2026A9A,0x2026AA0,True,'1d148c57dc648f32e59ea02a0641d27362bed7193c67a3002513949b699e2a64'),
 (0x20E5AD8,0x20E5AF8,False,'8fd01d1c34cea90e2fc0641e85ce43990925b400ab509dc5529ae4ef8bf48e28'),
)+tuple(x for x in P.NATIVE_BLOCKS if x[0] in (0x202551C,0x2025532,0x2037D78,0x2037D84))
POOLS=((0x2026A60,8,'f12ebc53cab774353058cae7db0e28bd9cc52bc7da742bf964e4adcf5012554b'),(0x2026AA0,4,'e1e8c8c4de8c785c8363f887ebab1c5116193a2101a00ec9ec1fca5b515794b4'),(0x2037D88,4,'c3cf71835285850270561a3a4b6af56223772e7b4224fbbe9ddfb8186ad1692e'))
STRING,SOURCE,DEST,COMM=0x2200000,0x2200100,0x2380070,0x21D4150
TOP,STOP=B.STACK_TOP,B.SENTINEL
COOKIES=(0x44444405,0x55555506,0x66666607,0x77777708,0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04)
MAGIC=0xB6F8D2EC

def words_bytes(words):
 need(type(words)in(list,tuple) and 2<=len(words)<=11 and all(type(w)is int and 0<=w<=65535 for w in words) and words[-1]==65535 and 65535 not in words[:-1],'finite EOS-terminated words')
 return struct.pack('<'+'H'*len(words),*words)

def qualify(model,raw):
 view=P.G.S.SHARED.gifts_audit.Arm9View(raw);code={};locations=[]
 for a,b,thumb,digest in WINDOWS:
  blob=view.read(a,b-a);need(blob==P.G.piece(model['segments'],a,b-a) and sha(blob)==digest,'native name code/readback drift');ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB if thumb else CS_MODE_ARM).disasm(blob,a));need(sum(x.size for x in ins)==len(blob),'native name complete disassembly')
  for i in ins:need(i.address not in code,'native name code overlap');code[i.address]=(i.size,thumb)
  locations.append(dict(ram=hex(a),bytes=b-a,rom_offset=hex(view.offset(a,b-a)),sha256=digest,kind='Thumb' if thumb else 'ARM'))
 for a,n,digest in POOLS:
  blob=view.read(a,n);need(blob==P.G.piece(model['segments'],a,n) and sha(blob)==digest,'native name pool drift');need(all(pc+size<=a or pc>=a+n for pc,(size,_) in code.items()),'code/pool overlap');locations.append(dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=digest,kind='data'))
 for a,n,digest in ((0x20733C0,176,'76912054c0a5f1183697cc83d7fa853fffd712b1620b9b6054e06314968e867b'),(0x200BBA0,44,'85ca94426c04a3e028b59484052523979a84e1931cf4edc03e4a1e872dcdfc22'),(0x200B9F8,192,'9ca72a3eea702b68766d169a362246ad8da2dd7d04be61e68e0b0130e3c5a165')):
  need(sha(view.read(a,n))==digest,'source-corresponding caller/producer drift');locations.append(dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=digest,kind='source correspondence only; not executed'))
 return code,locations

def resources(raw):
 files,receipt=P.RAW.raw_archive(raw,'a/0/2/7');bank=bytes(files[729]);one=hgss_text.read_bank_raw(bank);two=message_codec.Bank(bank);need(one==two.words,'independent decrypted message vectors');count,key=struct.unpack_from('<HH',bank);rows={}
 for trainer in (21,31):
  words=one[trainer];expanded,packed=hgss_text.unpack_name(words);need(expanded==message_codec.unpack_name(words),'independent expanded vector');words_bytes(words);mask=(key*765*(trainer+1))&65535;mask|=mask<<16;offset,length=struct.unpack_from('<II',bank,4+8*trainer);offset^=mask;length^=mask;need(length==len(words) and offset+2*length<=len(bank),'MAT length/raw EOS agreement')
  rows[str(trainer)]=dict(words=words,expanded=expanded,packed=packed,raw_words=len(words),expanded_words=len(expanded),raw_sha256=sha(words_bytes(words)),expanded_sha256=sha(words_bytes(expanded)),entry_bank_offset=offset,entry_rom_offset=receipt['member_rom_offsets'][729]+offset)
 return dict(bank_bytes=len(bank),bank_sha256=sha(bank),bank_rom_offset=receipt['member_rom_offsets'][729],count=count,key=key,records=rows)

def execute(model,code,words,capacity=8,*,observe=True,variant='current',destination_words=None):
 payload=words_bytes(words);need(type(capacity)is int and 1<=capacity<=11 and type(observe)is bool and variant in ('current','skip_copy','wrong_return','comm_live','pool_entry'),'finite helper fixture domain');destination_words=capacity if destination_words is None else destination_words;need(type(destination_words)is int and 1<=destination_words<=11,'finite destination allocation')
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_946);u.mem_map(0x2000000,0x400000)
 for a,blob in model['segments']:
  if 0x2000000<=a and a+len(blob)<=0x2400000:u.mem_write(a,blob)
 # Explicit String_New ABI fixture: allocation/body are not executed.
 initial=struct.pack('<HHI',len(words),0,MAGIC)+struct.pack('<H',65535)+bytes(2*len(words));u.mem_write(STRING,initial);u.mem_write(SOURCE,payload);u.mem_write(DEST-16,bytes([0xA5])*(destination_words*2+32));u.mem_write(TOP-128,bytes([0xC7])*128);u.mem_write(COMM,struct.pack('<I',int(variant=='comm_live')))
 before=bytes(u.mem_read(0x2000000,0x400000));phase=0;steps=0;low=TOP;events=[];writes=[];seen=set();assertions=0;copies=[0,0];apis=[]
 reg=lambda i:u.reg_read(B.R[i])
 def inside(a,n,start,size):return start<=a and a+n<=start+size
 def on_code(uc,a,n,_):
  nonlocal steps,low,assertions
  need(a in code and code[a]==(n,bool(uc.reg_read(UC_ARM_REG_CPSR)&32)),'execution outside qualified code/ISA');steps+=1;need(steps<=10000,'helper instruction budget');sp=uc.reg_read(UC_ARM_REG_SP);need(TOP-128<=sp<=TOP and sp%4==0,'helper stack bound');low=min(low,sp);seen.add(a)
  if a==0x202551C:assertions+=1
  if a==0x20E5AD8:
   copies[phase]+=1
   if observe:events.append(dict(api=phase,pc=hex(a),destination=reg(0),source=reg(1),bytes=reg(2),lr=hex(uc.reg_read(UC_ARM_REG_LR))))
   if variant=='skip_copy' and phase==1:uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
 def on_read(uc,access,a,n,value,_):
  allowed=inside(a,n,SOURCE,len(payload)) or inside(a,n,STRING,len(initial)) or inside(a,n,TOP-128,128) or inside(a,n,COMM,4) or any(inside(a,n,x,size) for x,size,_ in POOLS)
  need(allowed,'helper read outside owned inputs/pools/stack')
 def on_write(uc,access,a,n,value,_):
  pc=uc.reg_read(UC_ARM_REG_PC);stack=inside(a,n,TOP-128,128)
  body=phase==0 and ((pc==0x20E5AEC and inside(a,n,STRING+8,len(payload))) or (pc==0x2026A4C and a==STRING+2 and n==2))
  destination=phase==1 and pc==0x20E5AEC and inside(a,n,DEST,2*destination_words)
  need(stack or body or destination,'helper write outside owned object/destination/stack')
  if observe and not stack:writes.append(dict(api=phase,pc=hex(pc),address=a,bytes=n,value=value))
 u.hook_add(UC_HOOK_CODE,on_code);u.hook_add(UC_HOOK_MEM_READ,on_read);u.hook_add(UC_HOOK_MEM_WRITE,on_write)
 for phase,(entry,args) in enumerate(((0x2026A04,(STRING,SOURCE,len(words))),(0x2026A68,(STRING,DEST,capacity)))):
  u.reg_write(UC_ARM_REG_CPSR,0x3F);u.reg_write(UC_ARM_REG_SP,TOP)
  for i,value in enumerate(COOKIES,4):u.reg_write(B.R[i],value)
  for i,value in enumerate(args):u.reg_write(B.R[i],value)
  u.reg_write(B.R[3],0x33333303);u.reg_write(UC_ARM_REG_LR,(STOP+2 if variant=='wrong_return' and phase==1 else STOP)|1)
  begin=0x2026AA1 if variant=='pool_entry' and phase==1 else entry|1
  u.emu_start(begin,STOP,count=10001);need(u.reg_read(UC_ARM_REG_PC)==STOP and u.reg_read(UC_ARM_REG_CPSR)&32 and u.reg_read(UC_ARM_REG_SP)==TOP and tuple(reg(i) for i in range(4,12))==COOKIES,'helper return ABI');apis.append(dict(entry=hex(entry),args=args,end=[reg(i) for i in range(13)]+[u.reg_read(UC_ARM_REG_SP),u.reg_read(UC_ARM_REG_LR),u.reg_read(UC_ARM_REG_PC),u.reg_read(UC_ARM_REG_CPSR)]))
  need(bytes(u.mem_read(STRING,len(initial)))==struct.pack('<HHI',len(words),len(words)-1,MAGIC)+payload+b'\0\0','native CopyN String layout/payload')
 after=bytes(u.mem_read(0x2000000,0x400000));mutable=((STRING+2,2),(STRING+8,len(payload)),(DEST,2*destination_words),(TOP-128,128));frozen=bytearray(after)
 for a,n in mutable:frozen[a-0x2000000:a-0x2000000+n]=before[a-0x2000000:a-0x2000000+n]
 need(bytes(frozen)==before,'helper unrelated RAM frozen');fit=len(words)<=capacity;expected=payload+bytes([0xA5])*(2*destination_words-len(payload)) if fit else bytes([0xA5])*(2*destination_words)
 actual=bytes(u.mem_read(DEST,2*destination_words));need(actual==expected,'native copy destination mismatch');need(copies==[1,int(fit)] and assertions==int(not fit),'native copy/assert path coverage');need((0x2026A9A in seen)==(not fit),'capacity branch coverage')
 return dict(words=len(words),size=len(words)-1,capacity=capacity,destination_words=destination_words,fit=fit,assertions=assertions,copies=copies,instructions=steps,stack_bytes=TOP-low,apis=apis,string_sha256=sha(bytes(u.mem_read(STRING,len(initial)))),destination_sha256=sha(actual),destination_hex=actual.hex(),functional_ram_sha256=sha(after),observed_pcs=sorted(seen),events=events,writes=writes)

def functional(r):return {key:value for key,value in r.items() if key not in ('events','writes')}

def require_result(r,words,capacity):
 """Replay the finite ABI and byte-copy evidence without executing the CPU."""
 payload=words_bytes(words);fit=len(words)<=capacity;expected=payload+bytes([0xA5])*(2*capacity-len(payload)) if fit else bytes([0xA5])*(2*capacity)
 need((r['words'],r['size'],r['capacity'],r['destination_words'],r['fit'])==(len(words),len(words)-1,capacity,capacity,fit),'receipt representation/size/capacity')
 need(r['destination_hex']==expected.hex() and r['destination_sha256']==sha(expected) and r['string_sha256']==sha(struct.pack('<HHI',len(words),len(words)-1,MAGIC)+payload+b'\0\0'),'receipt full destination/String bytes')
 need(r['copies']==[1,int(fit)] and r['assertions']==int(not fit) and 0<r['instructions']<=10000 and 0<r['stack_bytes']<=128,'receipt native path/budget')
 need(len(r['apis'])==2,'receipt two native API calls')
 for call,(entry,args) in zip(r['apis'],((0x2026A04,[STRING,SOURCE,len(words)]),(0x2026A68,[STRING,DEST,capacity]))):
  end=call['end'];need(call['entry']==hex(entry) and list(call['args'])==args and len(end)==17 and end[4:12]==list(COOKIES) and end[13]==TOP and end[15]==STOP and end[16]&32,'receipt return ABI')
 expected_events=[dict(api=0,pc='0x20e5ad8',destination=STRING+8,source=SOURCE,bytes=len(payload),lr='0x2026a35')]
 if fit:expected_events.append(dict(api=1,pc='0x20e5ad8',destination=DEST,source=STRING+8,bytes=len(payload),lr='0x2026a99'))
 need(r['events']==expected_events,'receipt native memcpy ABI/order')
 expected_writes=[dict(api=0,pc='0x20e5aec',address=STRING+8+i,bytes=1,value=v if v<128 else v|0xFFFFFF00) for i,v in enumerate(payload)]+[dict(api=0,pc='0x2026a4c',address=STRING+2,bytes=2,value=len(words)-1)]
 if fit:expected_writes.extend(dict(api=1,pc='0x20e5aec',address=DEST+i,bytes=1,value=v if v<128 else v|0xFFFFFF00) for i,v in enumerate(payload))
 need(r['writes']==expected_writes,'receipt actual native writes/order')
 pcs=r['observed_pcs'];need(type(pcs)is list and len(set(pcs))==len(pcs) and all(type(pc)is int for pc in pcs),'receipt distinct instruction starts');required={0x2026A04,0x2026A30,0x2026A4C,0x2026A5E,0x2026A68,0x2026A8A,0x20E5AEC}|({0x2026A94,0x2026A98} if fit else {0x2026A9A,0x2026A9E,0x202551C,0x2025524,0x2025532,0x2037D78,0x2037D84})
 common=set(range(0x2026A04,0x2026A10,2))|set(range(0x2026A14,0x2026A1C,2))|set(range(0x2026A20,0x2026A32,2))|set(range(0x2026A34,0x2026A52,2))|{0x2026A5E}|set(range(0x2026A68,0x2026A74,2))|set(range(0x2026A78,0x2026A80,2))|set(range(0x2026A84,0x2026A8C,2))|set(range(0x20E5AD8,0x20E5AF8,4))
 tail=set(range(0x2026A8C,0x2026A96,2))|{0x2026A98} if fit else {0x2026A9A,0x2026A9E,0x202551C,0x202551E,0x2025522,0x2025524,0x2025532,0x2037D78,0x2037D7A,0x2037D7C,0x2037D7E,0x2037D84,0x2037D86}
 need(required<=set(pcs) and set(pcs)==common|tail,'receipt complete native path coverage')

def analyze(paths,language):
 need(sys.flags.optimize==0,'run without Python -O');history=[]
 for role in ('retail','base11','v4','r4'):
  model=P.G.S.SHARED.read_image(paths[role],language,role)
  with paths[role].open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
   data=resources(raw);history.append(dict(role=role,input=model['record'],resources=data))
   if role=='r4':code,locations=qualify(model,raw)
  if role!='r4':del model;gc.collect()
 data=history[-1]['resources'];cases=[];counters=[]
 for trainer in (21,31):
  for encoding in ('words','expanded'):
   words=data['records'][str(trainer)][encoding];r=execute(model,code,words);require_result(r,words,8);off=execute(model,code,words,observe=False);need(functional(r)==functional(off),'OFF/ON functional state differs');cases.append(dict(trainer=trainer,encoding=encoding,result=r,off_neutral=True))
 for length in (8,9):
  words=[0x120+i for i in range(length-1)]+[65535];r=execute(model,code,words);require_result(r,words,8);off=execute(model,code,words,observe=False);need(functional(r)==functional(off),'synthetic OFF/ON differs');cases.append(dict(trainer=None,encoding='synthetic-boundary',result=r,off_neutral=True))
 expanded=data['records']['21']['expanded'];r=execute(model,code,expanded,capacity=len(expanded));require_result(r,expanded,len(expanded));cases.append(dict(trainer=21,encoding='expanded-capacity-counterfactual',result=r,off_neutral=None))
 rawwords=data['records']['21']['words'];r=execute(model,code,rawwords,capacity=len(rawwords)-1);require_result(r,rawwords,len(rawwords)-1);cases.append(dict(trainer=21,encoding='raw-short-capacity-counterfactual',result=r,off_neutral=None))
 for variant in ('skip_copy','wrong_return','comm_live','pool_entry','destination_overflow'):
  words=[0x120+i for i in range(8)]+[65535] if variant in ('comm_live','destination_overflow') else rawwords
  try:execute(model,code,words,variant=variant if variant!='destination_overflow' else 'current',capacity=9 if variant=='destination_overflow' else 8,destination_words=8)
  except ValueError as e:counters.append(dict(variant=variant,rejection=str(e)))
  else:raise ValueError('negative helper calibration accepted: '+variant)
 return dict(schema='trainer-packed-name-v1',language=language,input=history[-1]['input'],history=history,locations=locations,cases=cases,counters=counters,source_sha256={str(Path(p).relative_to(P.SOURCE)):sha(Path(p).read_bytes()) for p in (__file__,hgss_text.__file__,message_codec.__file__)},qualified_code_pcs=len(code),compiler_invoked=False,limits=['Raw NARC/decryption and initial String_New allocation/header are host boundaries','Only CopyU16ArrayToStringN and CopyStringToU16Array execute natively,with native ARM memcpy and quiescent GF_ASSERT','Source lazy-loader correspondence is not observed producer execution or original compiler reconstruction','Expanded fixture differs from packed producer; no natural/UI bug or full caller activation demonstrated','No String free belongs to these borrowed-pointer APIs; caller deletion/lifetime is not executed'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','retail','base','v4','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);a=parser.parse_args();paths=dict(r4=a.rom,retail=a.retail,base11=a.base,v4=a.v4)
 try:
  need(not a.json.exists() and not a.json.is_symlink(),'output must be fresh');need(P.SOURCE not in a.json.resolve().parents and a.json.resolve()!=P.SOURCE,'output must be outside source');result=analyze(paths,a.language);payload=(json.dumps(result,indent=2)+'\n').encode();need(len(payload)<=2*1024*1024,'name report budget');a.json.parent.mkdir(parents=True,exist_ok=True)
  with a.json.open('xb') as f:f.write(payload)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(a.language,'packed trainer name copies verified; lazy loader and full caller remain outside runtime coverage')

if __name__=='__main__':main()
