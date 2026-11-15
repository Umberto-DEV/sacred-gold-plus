#!/usr/bin/env python3
"""Run named active rematch RAM shadows; never activate or write a ROM."""
from pathlib import Path
import importlib.util,json,mmap,struct
s=importlib.util.spec_from_file_location('active_rematch_inert_dependency',Path(__file__).with_name('attribuisci.py'));P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
B=P.B;need=P.need
GATES=('current','inactive','active2','host_index','host_buffer','setup_trainer','format','count','baseline_last','magic','size','reserved','layout','unselected_hash','unselected_illegal')
OBJECT_PINS={'native': 'cfc4dce49574df18f3064fb66c2f8d75b66f5e6ed63e26d36e97893e2168817a', 'stub': '43848467a67b11f1fec275a63e89f861c8641f325c86af38df03320a10d7c68a'}
OWN_SOURCE_PINS={'features/rematch-variants/stub.S': '19bfa3466cef90b6428719586b391ed24a61ffdba6ca3f40aa1a8ba2c357bbf6', 'features/rematch-variants/native.c': '927dc09acc7343a826f5e338a06415cc6e1f6fe1b5f129e5042ea2b662247f8b', 'features/rematch-variants/variants.c': '64920e94829fe136a15f6394b0e3c51528b9427adf8cb6856a0e7c46305b0faf', 'features/rematch-variants/variants.h': '1291727fb5dc3f5a9295d2a1172e30263d66afc57840373e9cc89f32cd3826c9', 'sgp131/data/rematch-variants.json': '696d708a888a9170effcf46972f02fb3040a24d05391caa9beea8ae1949c04ea'}

def authored(trainer,label):
 t=next(t for t in P.R.load_spec()['trainers'] if t['trainer_id']==trainer)
 slots=[dict(x,moves=list(x['moves'])) for x in t['baseline']]
 for letter in ('A','B'):
  if label=='baseline':break
  for change in t['variants'][letter]['changes']:
   slot=slots[change['slot']]
   for field,transition in change.items():
    if field in ('slot','why'):continue
    need(slot[field]==transition['before'],'independent authored preimage');slot[field]=transition['after']
  if label==letter:break
 blob=b''.join(struct.pack('<BBHHH4HH',x['difficulty'],x['override'],x['level'],x['species']|(x['form']<<10),x['item'],*x['moves'],x['capsule']) for x in slots)
 need(P.sha(blob)==(t['party_sha256'] if label=='baseline' else t['variants'][label]['sha256']),'independent authored encoding/hash')
 return blob

class Active(P.Audit):
 def __init__(self,bench,trainer,*,seed=0x12345678,plus=1,gate='current'):
  super().__init__(bench,trainer,'current',plus);self.initial_seed=seed;self.gate=gate;self.shadows=[];self.copy=[];self.apply=None;self.pending=None;self.selected=None;self.baseline_reads=[];self.native_seen=False;self.module_seen=False
 def shadow(self,a,b,why):
  old=bytes(self.uc.mem_read(a,len(b)));self.uc.mem_write(a,b);self.shadows.append(dict(address=hex(a),before=old.hex(),after=b.hex(),reason=why))
 def step(self,u,a,n,_):
  if a==0x226B4A0:
   need(not self.module_seen,'module reentry');self.module_seen=True
   self.shadow(P.CONFIG+6,bytes([0 if self.gate=='inactive' else 2 if self.gate=='active2' else 1]),'named active config RAM shadow; installed byte remains0')
   if self.gate=='partial_copy':
    self.shadow(0x226B184,bytes.fromhex('6b29'),'named counter copy loop107 instead108')
    image=bytearray(self.module);image[0x184:0x186]=bytes.fromhex('6b29');self.module=bytes(image)
  if a==0x226B3DC:
   self.native_seen=True;need(bytes(u.mem_read(B.ARENA,108))==authored(self.trainer,'baseline'),'actual native-reader baseline before gate shadows')
   sp=self.seam['sp'];desc=P.CONFIG+20+(0 if self.trainer==712 else 24);other=1-((self.initial_seed^(self.initial_seed>>16)^self.trainer)&1);partyoff=struct.unpack('<H',u.mem_read(desc+6+2*other,2))[0]
   if self.gate=='host_index':self.shadow(sp+0x10,struct.pack('<I',0),'enemy index not allowed')
   elif self.gate=='host_buffer':self.shadow(sp+0x74,struct.pack('<I',B.ARENA+1),'host buffer mismatch')
   elif self.gate=='setup_trainer':self.shadow(B.SETUP+0x1C,struct.pack('<I',self.trainer^1),'setup trainer mismatch')
   elif self.gate=='format':self.shadow(B.SETUP+0x28+52,b'\x02','wrong trainer format')
   elif self.gate=='count':self.shadow(B.SETUP+0x28+52+3,b'\x05','wrong trainer count')
   elif self.gate=='baseline_last':self.shadow(B.ARENA+107,b'\x01','last native baseline byte mismatch')
   elif self.gate=='magic':self.shadow(P.CONFIG,b'BAD!','config magic')
   elif self.gate=='size':self.shadow(P.CONFIG+4,struct.pack('<H',769),'config exceeds768 allocation')
   elif self.gate=='reserved':self.shadow(P.CONFIG+10,b'\x01\x00','reserved config')
   elif self.gate=='layout':self.shadow(P.CONFIG+20+6,struct.pack('<H',68),'A overlaps baseline')
   elif self.gate=='unselected_hash':self.shadow(P.CONFIG+partyoff+107,b'\x01','unselected party hash mismatch')
   elif self.gate=='unselected_illegal':
    party=bytearray(u.mem_read(P.CONFIG+partyoff,108));party[2]^=1
    self.shadow(P.CONFIG+partyoff,bytes(party),'unselected party changes protected level')
    self.shadow(desc+16+4*other,struct.pack('<I',P.R.fnv(party)),'updated unselected FNV does not repair legality')
   elif self.gate=='wrong_seed':self.shadow(sp+0x68,struct.pack('<I',self.initial_seed^1),'named opposite selector seed counter')
  if a==0x226B00C:
   need(self.pending is None,'apply reentry');self.pending=dict(args=[self.reg(i) for i in range(4)],stack=[self.word(self.sp()+4*i) for i in range(3)],sp=self.sp(),saved=[self.reg(i) for i in range(4,12)])
  if a==0x226B15E:
   need(self.selected is None,'selector repeated');self.selected=self.reg(0)
  if a==0x226B490 and self.pending:
   need(self.sp()==self.pending['sp'] and [self.reg(i) for i in range(4,12)]==self.pending['saved'],'apply return SP/r4-r11 ABI')
   self.apply=dict(self.pending,value=self.reg(0),return_sp=self.sp(),return_saved=[self.reg(i) for i in range(4,12)]);self.pending=None
  super().step(u,a,n,_)
 def write(self,u,access,a,n,value,_):
  if u.reg_read(P.UC_ARM_REG_PC)==0x226B180:
   i=self.reg(1);need(self.native_seen and self.apply is None and 0<=i<108 and i==len(self.copy) and n==1 and a==B.ARENA+i,'native 108B copy loop/index/store bounds')
   need(value==bytes(u.mem_read(self.reg(3)+i,1))[0],'copy value differs from real selected source')
   self.copy.append(dict(pc='0x226b180',address=hex(a),index=i,value=value));self.native_writes+=1;return
  super().write(u,access,a,n,value,_)
 def read(self,u,access,a,n,value,_):
  pc=u.reg_read(P.UC_ARM_REG_PC)
  if P.MODULE<=pc<P.MODULE+1216:
   spans=[(P.MODULE,P.MODULE+2048),(B.STACK_TOP-4096,B.STACK_TOP),(B.SETUP,B.SETUP+0x400),(B.ARENA,B.ARENA+108),(B.PLUS_STATE,B.PLUS_STATE+1)]
   need(any(x<=a and a+n<=y for x,y in spans),'module read outside declared buffers/config/stack')
   if pc==0x226B16E:self.baseline_reads.append(a-B.ARENA)
  super().read(u,access,a,n,value,_)

def run(model,raw,lang,code,*,trainer=712,seed=0x12345678,plus=1,context=1,gate='current'):
 need(__import__('sys').flags.optimize==0,'run without Python -O')
 need(trainer in (712,713) and seed in (0x12345678,0x12345679) and type(plus) is int and plus in (0,1,2) and context in (0,1,2049,0x803) and gate in GATES+('wrong_seed','partial_copy'),'active initialized fixture domain')
 bench=P.Adapter(model,raw,lang);bench.module_code=code;a=Active(bench,trainer,seed=seed,plus=plus,gate=gate)
 with P.patch.object(B,'Uc',a.factory),P.patch.object(B,'GF_ASSERT',0x23BE100),P.patch.object(B,'WFC_HOOK',0x23BE104):
  r=bench.run(trainer,plus=plus,seed=seed,battle_type=context,max_instructions=200000)
 need(a.resume is not None and a.pending is None,'active caller/helper incomplete')
 canaries=all(bytes(a.uc.mem_read(p-8,8))==b'\xA5'*8 and bytes(a.uc.mem_read(p+n,8))==b'\xA5'*8 for p,n in a.allocs)
 ignored=[(B.STACK_TOP-4096,B.STACK_TOP),(B.REGISTRY,B.REGISTRY+64),(0x23DA044,0x23DA048),(P.MODULE,P.MODULE+2048),(B.PARTIES+0x1000,B.PARTIES+0x1000+0x5B0)]+[(p-8,p+n+8) for p,n in a.allocs]+[(int(x['address'],16),int(x['address'],16)+len(bytes.fromhex(x['after']))) for x in a.shadows]
 before=P.masked_hash(a.before,ignored);after=P.masked_hash(r['ram'],ignored);need(before==after,'unrelated active RAM changed')
 return dict(trainer=trainer,seed=seed,plus=plus,context=context,gate=gate,buffer_sha256=P.sha(bytes(a.uc.mem_read(B.ARENA,108))),resume=a.resume,seam=a.seam,reader_calls=a.reader,unload_calls=a.unloads,registry=r['overlay']['registry'],seed_after=r['seed_after'],stack_canary=r['stack_canary'],canaries=canaries,party_header=r['party_header'],overlay=r['overlay'],wfc_counter=a.word(0x23DA044),models=a.models,events=r['events'],instructions=a.instructions,max_stack=a.max_stack,apply=a.apply,selected=a.selected,copy=a.copy,baseline_reads=a.baseline_reads,shadows=a.shadows,config_reads=a.config_reads,critical=a.critical,unrelated_ram_sha256=after,code=[dict(ram=hex(pc),bytes=n,thumb=t) for pc,n,t in sorted(a.code)])



def require_active(r):
 trainer,seed,plus,context,gate=(r[k] for k in ('trainer','seed','plus','context','gate'))
 need(trainer in (712,713) and seed in (0x12345678,0x12345679) and plus in (0,1,2) and context in (0,1,2049,0x803) and gate in GATES,'active result domain')
 eligible=plus==1 and context in (1,2049) and gate=='current'
 wrapper=plus==1 and context in (1,2049) and gate not in ('inactive','active2','host_index','host_buffer','setup_trainer','magic')
 index=(seed^(seed>>16)^trainer)&1;expected=authored(trainer,('B' if index else 'A') if eligible else 'baseline')
 if gate=='baseline_last':expected=expected[:107]+b'\x01'
 need(r['buffer_sha256']==P.sha(expected),'active exact authored or declared pre-apply buffer')
 need(r['reader_calls']==r['unload_calls']==1 and r['resume']['r'][0]==B.LOADER_RESULT,'actual native reader result/once/unload')
 need(r['resume']['sp']==r['seam']['sp'] and r['resume']['r'][1:3]==r['seam']['r'][1:3] and r['resume']['r'][4:12]==r['seam']['r'][4:12],'active caller ABI')
 need(r['seam']['saved_seed']==r['seed_after']==seed and r['stack_canary'] and r['canaries'] and list(r['party_header'])==[6,0],'active seed/canaries/empty party')
 need([list(x) for x in r['registry']]==[[126,0]]+[[0,0]]*7 and r['wfc_counter']==1,'active registry/WFC lifetime')
 need(r['overlay']['image'] in ([(126,True)],[[126,True]]) and r['overlay']['unload']==[126],'active actual FS model outcomes')
 need([e[0] for e in r['events']]==['alloc','alloc','read'] and [x['name'] for x in r['models']]==['Heap_Alloc','Heap_Alloc']+['0x20d88c0']*4+['0x20d8a48','0x20d8b6c','ReadWholeNarcMemberByIdPair','0x20d88c0','0x20d8db4'],'active SDK service sequence/extent')
 need(r['instructions']<=200000 and r['max_stack']<=512,'active instruction/stack budget')
 apply=r['apply'];need((apply is not None)==wrapper,'native wrapper gate/call reachability')
 if apply:
  typecount=0x206 if gate=='format' else 0x305 if gate=='count' else 0x306
  need(apply['args']==[B.ARENA,trainer,typecount,plus] and apply['stack']==[seed,P.CONFIG,768],'actual apply register/stack ABI incl saved seed')
  need(apply['sp']==r['seam']['sp']-104 and apply['sp']==apply['return_sp'] and apply['saved']==apply['return_saved'],'actual apply full return ABI')
  need(apply['value']==(1+index if eligible else 0),'native apply outcome distinct from forwarded reader result')
 chosen=index if eligible or gate=='baseline_last' else None
 need(r['selected']==chosen,'inlined native selector result or early gate')
 need(r['baseline_reads']==(list(range(108)) if chosen is not None else []),'whole baseline check before copy')
 writes=r['copy'];need(len(writes)==(108 if eligible else 0),'native copy must execute all108 stores or none')
 if eligible:
  need(writes==[dict(pc='0x226b180',address=hex(B.ARENA+i),index=i,value=v) for i,v in enumerate(expected)],'actual complete ordered108 byte-store trace')
 need(r['critical']==[dict(pc=hex(pc),address=hex(a),bytes=4,value=v) for pc,a,v in ((0x200702E,B.REGISTRY+4,1),(0x2007030,B.REGISTRY,126),(0x23DA3E2,0x23DA044,1),(0x2006F78,B.REGISTRY+4,0))],'active exact registry/WFC stores')
 pcs={int(c['ram'],16) for c in r['code']}
 need({B.ENTRY,0x20735E8,0x226B4A0,0x226B3DC,0x2006F7C}<=pcs and (0x226B00C in pcs)==wrapper and (0x226B180 in pcs)==eligible,'native active full execution coverage')
 return True


def attest_objects(raw,model,objects):
 for name,digest in OWN_SOURCE_PINS.items():need(P.sha((P.SOURCE/name).read_bytes())==digest,'rematch own source drift: '+name)
 module,record=P.G.S.SHARED.overlay(raw,126);view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
 need(P.sha(module)==P.MODULE_SHA and module[1286]==0 and record['y9_words']==[126,P.MODULE,2048,0,P.MODULE,P.MODULE,126,0],'installed inert126 identity before shadows')
 stub=view.read(P.STUB,64);need(P.sha(stub)==P.STUB_SHA and view.read(P.SEAM,4)==bytes.fromhex('62f3d1f9'),'installed resident stub/seam')
 proofs={}
 for name,file,payload,base in (('native','rematch-variants.o',module[:1216],P.MODULE),('stub','rematch-stub.o',stub[:60],P.STUB)):
  path=objects/file;need(path.is_file() and path.stat().st_size<=1024**2,'retained ELF input bounds');data=path.read_bytes();need(P.sha(data)==OBJECT_PINS[name],'retained ELF input identity')
  proofs[name]=P.audit_elf(data,payload,base)
 return P.mapped_code(proofs['native'],module[:1216],P.MODULE),dict(overlay126=record,elf=proofs,installed_activation=0,compiler_invoked=False)


def analyze(rom,language,objects):
 model=P.G.S.SHARED.read_current(rom,language)
 with rom.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
  code,proof=attest_objects(raw,model,objects);positives=[];negatives=[];counters=[]
  for trainer in (712,713):
   for seed in (0x12345678,0x12345679):
    for context in (1,2049):
     r=run(model,raw,language,code,trainer=trainer,seed=seed,context=context);require_active(r);positives.append(r)
  for gate in GATES[1:]:
   r=run(model,raw,language,code,gate=gate);require_active(r);negatives.append(r)
  for args in (dict(plus=0),dict(plus=2),dict(context=0),dict(context=0x803),dict(gate='unselected_hash',seed=0x12345679),dict(gate='unselected_illegal',seed=0x12345679)):
   r=run(model,raw,language,code,**args);require_active(r);negatives.append(r)
  for seed in (0x12345678,0x12345679):
   for gate in ('wrong_seed','partial_copy'):
    r=run(model,raw,language,code,seed=seed,gate=gate)
    if gate=='partial_copy':need(r['buffer_sha256']==P.sha(authored(712,'B' if (seed^(seed>>16)^712)&1 else 'A')) and len(r['copy'])==107,'same-output partial-copy counter premise')
    need(r['resume']['r'][0]==B.LOADER_RESULT and r['registry'][0]==(126,0),'counter must preserve reader R0/free registry')
    disguised=dict(r,gate='current')
    try:require_active(disguised)
    except ValueError as e:r['rejection']=str(e)
    else:raise ValueError('active same-output/seed counter accepted')
    counters.append(r)
 return dict(schema='rematch-active-shadow-v1',language=language,input=model['record'],proof=proof,positives=positives,negative_gates=negatives,counters=counters,
  source_sha256={str(p.relative_to(P.SOURCE)):P.sha(p.read_bytes()) for p in (Path(__file__),Path(P.__file__),Path(B.__file__))},
  conclusions=dict(owned_source_binary_reused=True,initialized_active_gate_selector_copy_observed=True,installed_activation=0,natural_activation_observed=False),
  limits=['Only named RAM active1/config/frame/buffer/code shadows after exact installed0 admission; no ROM writes or activation authorization',
   'Real constructor prefix stops before0207363E; no complete party/level-hook/natural phone/Dojo/battle/SAVE/hardware/timing claim',
   'SDK heap/archive/FS models and initialized CommStateNULL/WFC126 qualification are inherited from the inert case',
   'Eight positive and twenty negative fixtures per language exercise finite states, not every possible gate/config/buffer input',
   'Partial copy107 counter has same output because byte107 is already0; an exact108 native-store trace is required'])


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','objects','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'--json must be a fresh nonexistent file')
  need(P.SOURCE not in args.json.resolve().parents and args.json.resolve()!=P.SOURCE and args.objects.resolve() not in args.json.resolve().parents and args.json.resolve()!=args.objects.resolve(),'--json must be outside source and retained objects')
  result=analyze(args.rom,args.language,args.objects)
  args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'8 active RAM paths,20 gate controls,4 counterproofs verified; installed activation remains0; natural activation unobserved')


if __name__=='__main__':main()
