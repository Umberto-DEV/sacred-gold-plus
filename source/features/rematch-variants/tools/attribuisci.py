#!/usr/bin/env python3
"""Attribute the inert rematch overlay, resident stub and initialized loader paths.

Reads exact local ROMs through mmap. Reuses ConstructorBench only up to its first
reader seam return; its broad full-party claims and assert/WFC models do not apply.
No ROM is written. See docs/validation/rematch-source-rom-1.3.2.md.
"""
from pathlib import Path
import importlib.util,json,mmap,struct,sys
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SOURCE))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
G=load('rematch_shared_mapping',SOURCE/'features/type-consumers/tools/attribuisci.py')
RAW=load('rematch_raw_archive',SOURCE/'features/borsa/tools/attribuisci.py')
B=load('rematch_constructor_bench',SOURCE/'features/rematch-variants/test/constructor_bench.py')
from sgp131 import rematches as R
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB,CS_MODE_ARM
from unicorn import Uc,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_CPSR
need,sha=G.need,R.sha
MODULE,CONFIG,STUB,SEAM=0x0226B000,0x0226B500,0x023D59E0,0x0207363A
MODULE_SHA='1777e2caab05aa3dbc1afcff721d72c394aee4a50322e2b38d8d820c5a6b0258'
STUB_SHA='77844c84762bcdf84e64503a1e0996c871c8ca1027846b8059e5b5b86a8688ce'
# Qualified instruction blocks for the initialized paths, NOT inferred function extents.
# Pools/alignment/unexercised branches are excluded. ELF maps qualify own C separately.
NATIVE_BLOCKS=(
 (0x2006f58,0x2006f62,True,'d5a8fc89d1bf60faacac0aa78027d723dfc8db6ebd2d0a7270f85b43219e54de'),
 (0x2006f66,0x2006f72,True,'decf5e9110364b28d3f6a8b8a5160c2e91790b719f6a238a729ff792171187e6'),
 (0x2006f76,0x2006fbe,True,'e4a21bde89a80b0dbb2eb3bee0a99e339514107765bd3c152d04f39d9492be9a'),
 (0x2006fc2,0x2006fcc,True,'0a65cec570a49daf5618df16da7af9b258bff706eb152d55edfe3c64ff14e459'),
 (0x2006fd8,0x2006fe8,True,'62b0580c17efcbff3c11328b213efbdec172dc3d5b0dd064be7314029587f846'),
 (0x2006fee,0x2006ff4,True,'c72a9db76e5aa4a07b952e74188b63646c22bd58dd15dfba692aaca3826066d9'),
 (0x2006ff8,0x2007034,True,'cab322bf7147e8336e27c3b5985c1bee69ebdec31b91116ef1b15c88cf646394'),
 (0x200703c,0x2007040,True,'246ed5171cf8a436a2d2b9b310b9eebcfef5e6a51444aec84835a095f0ea9567'),
 (0x2007048,0x200704e,True,'8cd43f741fa21af5cb18615a0c5c64858b5e0a76fce67fe10e2ba23772f31439'),
 (0x2007058,0x200705c,True,'0ccde29f18cdff4faf18542c48f63d6101621d89485c5ddd6d4609c1b64caad8'),
 (0x2007066,0x2007072,True,'4ecf2b05d5975ab5ada949bdc7150e19b460195c350503a088da4e53957172b9'),
 (0x2007092,0x2007096,True,'e3c65960d0b3ed42a8eec9094fb66ae4df4bf16c2fb5acfcd3392759f06ccbdb'),
 (0x200709c,0x20070be,True,'3f455874848efa196710ee8515ef6b17effe7e50305ac1da778b7a3c7e99ef82'),
 (0x20070c4,0x20070f8,True,'d21b5a390645c64231ccd5103df8ddb26aae83042df08e2636e1ef3b8bebc356'),
 (0x200710e,0x2007122,True,'98650e3b8100bf4edc70d4735fccf306acb2beb362ceb0ac12bdf214ba407220'),
 (0x2007124,0x2007128,True,'abeb3cb1532c6abb80bd968638325ea4afe5f151db02a8dbd5af9fe3c0b9f150'),
 (0x2007130,0x2007134,True,'2152630f850a126935d03832426f20261cdf368f9af333d74a29a73eb3a14929'),
 (0x2007148,0x2007160,True,'7f80e4cac2b9b0e9903834680152324bd08860f0673d36ca8f0e9ca950322e97'),
 (0x200716a,0x200717e,True,'e16a58984471c70a8f77963368fb4f100090a229b71409e46652dbde2e287018'),
 (0x2007180,0x2007184,True,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c'),
 (0x201fd2c,0x201fd32,True,'0719e9572025682a72853d11d794ab4bf6ab4df0153470c259ebbf437cd6e011'),
 (0x201fd38,0x201fd3e,True,'5cb6a8729e95cc248a0c7ad68108c00e2564e96a9bea977932ae9018be8da215'),
 (0x201ff44,0x201ff6e,True,'389a3db4659cbf730872a30ec4eeb8f15ae258996b4ce043a334c380ead71f4e'),
 (0x201ff78,0x201ff8e,True,'9c5bf64dc199aee1c4481c4aec6d3bf09ef61fa500f29bd47075fcc4b89070f4'),
 (0x202551c,0x2025526,True,'0cb7be5af483034cb1cf3e3bad504df73d5c3195161f6bc340c6da493706efb4'),
 (0x2025532,0x2025534,True,'91b15f150f8fb14a74b772cf2d08022ca1a7130ab8e6143fd8e1744a8d7a5a55'),
 (0x2037d78,0x2037d80,True,'698214878ed5d96744ae25f2fd5640ebaede5e4f5acd3570e31d4eec18eddb09'),
 (0x2037d84,0x2037d88,True,'a7ddd513d149ea16fdd4db3f82267f83087aeaddd06b5dde5468adb704205fc4'),
 (0x206dce4,0x206dd0c,True,'803d43350d39bfcf5eb100abe3e97e305aeb56c6ebb9101d802f724298c2ca05'),
 (0x206dd2c,0x206dd3e,True,'43452961da16fba54871f53e2f16eb5a72ce677071ce3d458882dad8a4959727'),
 (0x20725d8,0x20725dc,True,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c'),
 (0x20735e8,0x20735f2,True,'3b0eb71095effb5e0ba0964c3b0da2807ab12123466b0b5917ab6ece530f549a'),
 (0x2073604,0x207363e,True,'85771fd49fa2b95216bcd874d8b82a99fc34ec51508d58d6f57572cd52dd3a26'),
 (0x20744dc,0x20744e6,True,'26a85c98d594d65571ede42910f0ec72c8316239d4bf8b3da166ed10b27fc8ee'),
 (0x20744ea,0x2074522,True,'2a1c1bf2b4a6d067df398958f3f20986a289df1f5bb56b6726328ffb4fa84d11'),
 (0x20d4858,0x20d48b4,False,'10577c29bdbc6913eba507a029157099a73f377ee8d0e6617ff2cc72def5f8a5'),
 (0x20d4994,0x20d49a0,False,'3d27f76e57b241ffbe9d447d4db7913280a2a2e1cf1d347dbca7d0fb17cfed68'),
 (0x20d49a4,0x20d49ac,False,'7a583e83de1e6bd840b7ad86c5d67104d21d6494716b587b75bd981f71e36769'),
 (0x20d49d0,0x20d49e4,False,'b92565eb55077304f9779b437928d8e2b286d7609b260d46aafc2a72ba95ac14'),
 (0x20d49f8,0x20d4a20,False,'153cdcf2aae94fff6b4195a3ad221b852405c55ab3c3ddac849d0c5fd09fcf8b'),
 (0x20d4a24,0x20d4a30,False,'1ec3ce4ef0adc4f3bd451219bef57b887aea2fc5b0d85dd22d13b2aa8c2eee0d'),
 (0x20d4a34,0x20d4a38,False,'379bec29dccd0a93c94826144d7ef6e42fab64ef195a3b8313a16926f66f388f'),
 (0x20d8d60,0x20d8db4,False,'d25ccb2b2dbe753039cd32e8f2f81b3790720d9751b10a76eb99afb0e298dd17'),
 (0x20e5b44,0x20e5b58,False,'1bd80632456971c08c1131ba63a0a0951f613e94bb6074310a7ab050d15f3e07'),
 (0x20e5bf0,0x20e5c08,False,'d5e758e1ba4428abb30f7b7b8d5655be37c29c0ac60c3867201fcfdff33a134b'),
 (0x20e5c1c,0x20e5c24,False,'f07265e231c019d166d2d3b8397a39b41faed16aca1c98d0dbe2baa7d3397f2a'),
 (0x20e5c34,0x20e5c8c,False,'5da0fc454c1ed5ba27e512e01426d586a9b03c2b707582bc4f3ab4f7fcfbe110'),
 (0x23d59e0,0x23d5a0a,True,'560d26ca502d409649131e229650941c87a29cebd5d9df89abb2ae88579bfef5'),
 (0x23da3cc,0x23da3ec,True,'3c2a024613d5f0280accb6373439e717b34fba8c1e8ba5c705fc9a2ad1106090'),
 (0x23da458,0x23da45a,True,'0d4542e69834fdd98d546c52551d295d1465ce1e0870def994e76e97d60d4736'),
 (0x23da47c,0x23da48c,True,'cbe3f3926b84ab23ce67827208f946f7b81d42e4dd8ca49fa22d9536bfe33e59'),
)

def masked_hash(ram,ranges):
 image=bytearray(ram)
 for a,b in ranges:image[a-0x02000000:b-0x02000000]=bytes(b-a)
 return sha(image)

class Archives:
 def __init__(self,raw):self.raw=raw;self.cache={}
 def files(self,path):
  if path not in self.cache:self.cache[path]=RAW.raw_archive(self.raw,path)[0]
  return self.cache[path]
class Adapter(B.Bench):
 def __init__(self,model,raw,language):
  self.segments=model['segments'];self.archives=Archives(raw);self.language=language;self.watch=(0x226B000,0x226B500);self.overlay=True;self.rom=raw;self.names=None

class Audit:
 initial_seed=0x12345678
 def __init__(self,bench,trainer,variant,plus):
  self.bench=bench;self.trainer=trainer;self.variant=variant;self.plus=plus;self.instructions=0;self.code=set();self.models=[];self.allocs=[];self.reader=0;self.unloads=0;self.wfc=0;self.asserts=0;self.critical=[];self.seam=None;self.resume=None;self.started=False;self.max_stack=0;self.native_writes=0;self.module=bench.module_image()[1];self.allowed={};self.config_reads=[];self.before=None
  for start,end,thumb,digest in NATIVE_BLOCKS:
   blob=bench.segment_bytes(start,end-start);need(sha(blob)==digest,'native instruction block '+hex(start))
   decoded=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB if thumb else CS_MODE_ARM).disasm(blob,start))
   need(sum(i.size for i in decoded)==len(blob),'native block decoding')
   for ins in decoded:self.allowed[ins.address]=(ins.size,thumb)
  self.allowed.update(bench.module_code)
 def factory(self,*args):
  u=Uc(*args);self.uc=u;u.hook_add(UC_HOOK_CODE,self.step);u.hook_add(UC_HOOK_MEM_WRITE,self.write);u.hook_add(UC_HOOK_MEM_READ,self.read);return u
 def reg(self,n):return self.uc.reg_read(B.R[n])
 def sp(self):return self.uc.reg_read(UC_ARM_REG_SP)
 def word(self,a):return struct.unpack('<I',self.uc.mem_read(a,4))[0]
 def step(self,u,a,size,_):
  self.instructions+=1;need(self.instructions<=200000,'prefix instruction budget');self.max_stack=max(self.max_stack,B.STACK_TOP-self.sp())
  if a==B.ENTRY:
   self.started=True
   if self.variant=='native':u.mem_write(0x207363A,bytes.fromhex('fff7d5ff'))
   elif self.variant=='skip_unload':u.mem_write(0x23D5A06,bytes.fromhex('c046'))
   elif self.variant=='wrong_args':u.mem_write(0x23D59FA,bytes.fromhex('0299'))
   elif self.variant=='pool_entry':u.mem_write(0x23D5A10,struct.pack('<I',0x23D5A11))
   self.before=bytes(u.mem_read(0x02000000,0x400000))
  if a==SEAM:
   self.seam=dict(r=[self.reg(i) for i in range(13)],sp=self.sp(),saved_seed=self.word(self.sp()+0x68))
   need(self.reg(0)==self.trainer and self.reg(1)==B.ARENA and self.reg(4)==B.SETUP and self.reg(6)==B.ARENA+128 and self.reg(7)==4 and self.sp()==B.STACK_TOP-152,'actual constructor seam ABI')
   need(self.word(self.sp()+0x10)==1 and self.word(self.sp()+0x74)==B.ARENA and self.seam['saved_seed']==self.initial_seed,'actual host frame')
  if a==B.SEAM_RESUME:
   self.resume=dict(r=[self.reg(i) for i in range(13)],sp=self.sp(),flags=u.reg_read(UC_ARM_REG_CPSR)>>28);u.emu_stop();return
  if a in B.STUBS:
   name=B.STUBS[a];args=[self.reg(i) for i in range(4)];need(self.sp()%8==0,'SDK model SP alignment')
   if name.startswith('Heap_Alloc'):
    need(args[:2] in ([11,108],[11,236]),'prefix allocation ABI')
    ptr=B.ARENA+sum((n+0x17)&~7 for _,n in self.allocs);self.allocs.append((ptr,args[1]));u.mem_write(ptr-8,b'\xA5'*8);u.mem_write(ptr+args[1],b'\xA5'*8)
   elif name=='ReadWholeNarcMemberByIdPair':need(args[:3]==[B.ARENA,56,self.trainer] and len(self.bench.archives.files('a/0/5/6')[self.trainer])==108,'native archive forward ABI/buffer extent')
   else:raise ValueError('unexpected prefix SDK model '+name)
   self.models.append(dict(name=name,args=args,sp=self.sp()));return
  if a in (B.FS_INFO,B.FS_IMAGE,B.FS_START,B.FS_UNLOAD):
   args=[self.reg(i) for i in range(4)];need(self.sp()%8==0,'FS model SP alignment')
   if a==B.FS_INFO:need(B.STACK_TOP-4096<=args[0] and args[0]+44<=B.STACK_TOP and args[1]==0 and args[2] in (12,126),'FS info ABI')
   elif a in (B.FS_IMAGE,B.FS_START):need(B.STACK_TOP-4096<=args[0] and args[0]+44<=B.STACK_TOP,'FS image/start ABI')
   else:need(args[:2]==[0,126],'FS unload ABI')
   self.models.append(dict(name=hex(a),args=args,sp=self.sp()));return
  if a==0x20735E8:self.reader+=1
  if a==0x2006F7C:need(self.reg(0)==126,'native Unload126 ABI');self.unloads+=1
  if a==0x202551C:need(self.word(0x21D4150)==0,'only native assertion return with absent CommState is qualified');self.asserts+=1
  if a==0x23DA3CC:need(self.reg(0)==126,'only irrelevant126 WFC path qualified');self.wfc+=1
  thumb=bool(u.reg_read(UC_ARM_REG_CPSR)&32);need(self.allowed.get(a)==(size,thumb),'instruction PC/width/mode outside qualified code: '+hex(a))
  if a==0x226B4A0:need(self.sp()==self.seam['sp']-16 and [self.reg(i) for i in (0,1,4,6,7)]==[self.trainer,B.ARENA,B.SETUP,B.ARENA+128,4],'stub to module ABI')
  if a==0x226B3DC:need([self.reg(i) for i in range(4)]==[B.SETUP,self.seam['sp'],self.trainer,B.ARENA],'module host SP+48/native ABI')
  if 0x226B000<=a<0x226B800:
   expected=self.module[a-0x226B000:a-0x226B000+size];need(a+size<=0x226B4C0,'module code bound')
  else:
   expected=self.bench.segment_bytes(a,size)
   for pc,old,new in ((0x207363A,bytes.fromhex('62f3d1f9'),bytes.fromhex('fff7d5ff')),(0x23D5A06,bytes.fromhex('9847'),bytes.fromhex('c046')),(0x23D59FA,bytes.fromhex('0199'),bytes.fromhex('0299'))):
    if a==pc and ((self.variant=='native' and pc==0x207363A) or (self.variant=='skip_unload' and pc==0x23D5A06) or (self.variant=='wrong_args' and pc==0x23D59FA)):expected=new
  need(bytes(u.mem_read(a,size))==expected,'executed bytes differ at '+hex(a))
  self.code.add((a,size,thumb))
 def read(self,u,access,a,n,value,_):
  if CONFIG<=a and a+n<=CONFIG+768:self.config_reads.append(dict(pc=hex(u.reg_read(UC_ARM_REG_PC)),address=hex(a),bytes=n))
 def write(self,u,access,a,n,value,_):
  pc=u.reg_read(UC_ARM_REG_PC);self.native_writes+=1
  if B.STACK_TOP-4096<=a and a+n<=B.STACK_TOP:return
  if not self.seam and (B.PARTIES+0x1000<=a and a+n<=B.PARTIES+0x1000+0x5B0 or any(p<=a and a+n<=p+sz for p,sz in self.allocs)):return
  if not self.started and pc==0x201FD3A and a==0x21D15A8 and n==4:return
  if pc in (0x200702E,0x2007030,0x2006F78):
   need((a,n,value)=={0x200702E:(B.REGISTRY+4,4,1),0x2007030:(B.REGISTRY,4,126),0x2006F78:(B.REGISTRY+4,4,0)}[pc],'native registry PC-specific field');self.critical.append(dict(pc=hex(pc),address=hex(a),bytes=n,value=value));return
  if pc==0x23DA3E2:
   need((a,n,value)==(0x23DA044,4,1),'native WFC overlay-count store');self.critical.append(dict(pc=hex(pc),address=hex(a),bytes=n,value=value));return
  raise ValueError('unexpected native write '+hex(a)+' PC='+hex(pc))

def run_case(model,raw,language,module_code,trainer=712,scenario='success',variant='current',plus=1,reader_result=B.LOADER_RESULT):
 need(sys.flags.optimize==0,'run without Python -O: inherited bench assertions are required')
 need(trainer in (712,713) and scenario in ('success','refused','failed') and variant in ('current','native','skip_unload','wrong_args','pool_entry') and type(plus) is int and plus in (0,1) and reader_result in (B.LOADER_RESULT,0,0xFFFFFFFF),'initialized fixture domain')
 bench=Adapter(model,raw,language);bench.module_code=module_code;audit=Audit(bench,trainer,variant,plus)
 with patch.object(B,'LOADER_RESULT',reader_result),patch.object(B,'Uc',audit.factory),patch.object(B,'GF_ASSERT',0x23BE100),patch.object(B,'WFC_HOOK',0x23BE104):
  r=bench.run(trainer,plus=plus,load_ok=scenario!='failed',busy=(12,) if scenario=='refused' else (),max_instructions=200000)
 need(audit.seam is not None and audit.resume is not None,'seam/return not reached')
 need(not r['misalign'],'native SDK model alignment')
 buf=bytes(audit.uc.mem_read(B.ARENA,108));canaries=all(bytes(audit.uc.mem_read(p-8,8))==b'\xA5'*8 and bytes(audit.uc.mem_read(p+n,8))==b'\xA5'*8 for p,n in audit.allocs)
 ignored=[(B.STACK_TOP-4096,B.STACK_TOP),(B.REGISTRY,B.REGISTRY+64),(0x23DA044,0x23DA048),(MODULE,MODULE+2048),(B.PARTIES+0x1000,B.PARTIES+0x1000+0x5B0)]+[(p-8,p+n+8) for p,n in audit.allocs]
 frozen_before=masked_hash(audit.before,ignored);frozen_after=masked_hash(r['ram'],ignored);need(frozen_before==frozen_after,'unrelated main RAM changed')
 neutral=masked_hash(r['ram'],[(B.STACK_TOP-4096,B.STACK_TOP),(B.REGISTRY,B.REGISTRY+64),(0x23DA044,0x23DA048),(MODULE,MODULE+2048),(SEAM,SEAM+4)])
 return dict(reader_result=reader_result,unrelated_ram_sha256=frozen_after,neutral_ram_sha256=neutral,party_header=r['party_header'],config_reads=audit.config_reads,trainer=trainer,scenario=scenario,variant=variant,plus=plus,buffer_sha256=R.sha(buf),buffer_expected_sha256=R.sha(bench.archives.files('a/0/5/6')[trainer]),resume=audit.resume,seam=audit.seam,reader_calls=audit.reader,unload_calls=audit.unloads,assert_calls=audit.asserts,wfc_calls=audit.wfc,wfc_counter=audit.word(0x23DA044),registry=r['overlay']['registry'],events=r['events'],overlay=r['overlay'],seed_before=r['seed_before'],seed_after=r['seed_after'],canaries=canaries,stack_canary=r['stack_canary'],instructions=audit.instructions,max_stack=audit.max_stack,native_writes=audit.native_writes,critical=audit.critical,models=audit.models,code=[dict(ram=hex(a),bytes=n,thumb=t) for a,n,t in sorted(audit.code)])



def audit_elf(data,payload,base):
 """Independent ELF32 reader: verify relocations against the supplied readback.

 Does not call the production loader. Preserve repeated mapping symbols: a dict
 keyed by '$t'/'$d' would lose the earlier code and pool islands.
 """
 need(len(data)>=52 and data[:7]==b'\x7fELF\x01\x01\x01','ELF32 little-endian identity')
 h=struct.unpack_from('<HHIIIIIHHHHHH',data,16);need(h[:2]==(1,40),'ELF relocatable ARM')
 off,ents,count,names=h[5],h[10],h[11],h[12]
 need(ents==40 and 0<count<256 and names<count and 52<=off and off+40*count<=len(data),'ELF section table')
 sections=[struct.unpack_from('<10I',data,off+40*i) for i in range(count)]
 def content(i):
  s=sections[i];a,n=s[4:6];need(a+n<=len(data),'ELF section bounds');return data[a:a+n]
 def string(table,i):
  need(0<=i<len(table),'ELF string bounds');j=table.find(b'\0',i);need(j>=i,'ELF unterminated string');return table[i:j].decode('ascii')
 labels=[string(content(names),s[0]) for s in sections];need(labels.count('.text')==1,'ELF .text uniqueness');text=labels.index('.text');original=content(text)
 need(len(original)==len(payload),'ELF text/payload length')
 for i,s in enumerate(sections):need(not(s[2]&2 and s[5] and i!=text and labels[i]!='.ARM.exidx'),'ELF unexpected allocated section')
 tables={};mapping=[];symbols={}
 for i,s in enumerate(sections):
  if s[1]!=2:continue
  need(s[9]==16 and s[5]%16==0 and s[6]<count,'ELF symbol table')
  tables[i]=list(struct.iter_unpack('<IIIBBH',content(i)))
  for sym in tables[i]:
   name=string(content(s[6]),sym[0]);need(not(name and sym[5]==0 and sym[3]&0xF0),'ELF external symbol')
   if sym[5]!=text:continue
   need(sym[1]<=len(original),'ELF text symbol bounds')
   if name.startswith(('$t','$d','$a')):mapping.append((sym[1],name[:2]))
   elif name:symbols[name]=base+sym[1]
 changed=set();relocations=[]
 for i,s in enumerate(sections):
  need(not(s[1]==4 and s[7]==text),'ELF RELA unsupported')
  if s[1]!=9 or s[7]!=text:continue
  need(s[9]==8 and s[5]%8==0 and s[6] in tables,'ELF relocation table')
  for at,info in struct.iter_unpack('<II',content(i)):
   need(info>>8<len(tables[s[6]]) and at+4<=len(original),'ELF relocation bounds')
   sym=tables[s[6]][info>>8];kind=info&255;need(sym[5]==text and kind in (2,10),'ELF internal relocation kind')
   need(not changed.intersection(range(at,at+4)),'ELF overlapping relocations');changed.update(range(at,at+4))
   if kind==10:
    hi,lo=struct.unpack_from('<HH',original,at);need(hi&0xF800==0xF000 and lo&0xF800==0xF800,'ELF Thumb1 BL encoding')
    addend=((hi&2047)<<12)|((lo&2047)<<1)
    if addend&(1<<22):addend-=1<<23
    target=base+(sym[1]&~1)+addend+4
    need(G.S.SHARED.branch(payload[at:at+4],base+at,'bl')==target,'ELF independently decoded relocated BL target')
   else:
    addend=struct.unpack_from('<I',original,at)[0];target=(base+sym[1]+addend)&0xFFFFFFFF
    need(struct.unpack_from('<I',payload,at)[0]==target,'ELF internal ABS32 literal')
   relocations.append(dict(offset=hex(at),kind=kind,target=hex(target)))
 need(all(a==b for i,(a,b) in enumerate(zip(original,payload)) if i not in changed),'ELF non-relocation byte drift')
 mapping=sorted(set(mapping));need(mapping and mapping[0][0]==0 and len({a for a,k in mapping})==len(mapping),'ELF mapping symbols ambiguous')
 ranges=[]
 for j,(a,kind) in enumerate(mapping):
  b=mapping[j+1][0] if j+1<len(mapping) else len(payload);need(a<=b<=len(payload),'ELF mapping extent')
  need(kind in ('$t','$d'),'ELF unexpected ARM code mapping')
  if a<b:ranges.append(dict(start=hex(base+a),end=hex(base+b),kind=kind))
 return dict(object_sha256=sha(data),text_bytes=len(payload),text_sha256=sha(payload),symbols={k:hex(v) for k,v in symbols.items()},relocations=relocations,mapping_ranges=ranges,ignored_exidx=True)


def mapped_code(proof,payload,base):
 allowed={}
 for r in proof['mapping_ranges']:
  if r['kind']!='$t':continue
  a,b=int(r['start'],16),int(r['end'],16);blob=payload[a-base:b-base];ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,a))
  need(sum(i.size for i in ins)==len(blob),'ELF mapped Thumb instruction coverage')
  for i in ins:allowed[i.address]=(i.size,True)
 return allowed


def resources(raw,model):
 res=R.Resources.__new__(R.Resources);res.digests={};records={}
 for name,path in (('headers','a/0/5/5'),('parties','a/0/5/6'),('personal','a/0/0/2'),('moves','a/0/1/1'),('wotbl','a/0/3/3'),('eggs','a/2/2/9'),('items','a/0/1/7')):
  files,record=RAW.raw_archive(raw,path);setattr(res,name,files);res.digests[path]=record['archive_sha256'];records[path]=record
 tm=R.load_abi()['tm_table'];table=G.piece(model['segments'],int(tm['address'],16),2*tm['count']);need(sha(table)==tm['sha256'],'TM/HM table preimage');res.machines=list(struct.unpack('<100H',table))
 return res,records


def config_from(res):
 spec=R.load_spec();ids=[t['trainer_id'] for t in spec['trainers']]
 return R.materialize(spec,{i:res.parties[i] for i in ids},{i:res.headers[i] for i in ids},active=0,battle_types=tuple(R.load_abi()['gate']['context']['battle_types']),enemy_indexes=(1,))


def staging(v4,final):
 spec=R.load_spec();R.verify_semantics(spec,v4)
 need(config_from(v4)==config_from(final),'config source members changed after rematch stage')
 changed={}
 for name in ('headers','parties','personal','moves','wotbl','eggs','items'):
  a,b=getattr(v4,name),getattr(final,name);need(len(a)==len(b),'resource member count changed');changed[name]=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
 need(changed['parties']==[460,461] and final.parties[460]==v4.parties[461] and final.parties[461]==v4.parties[460],'later trainer-fixes swap preimage')
 need(not any(changed[n] for n in ('headers','personal','wotbl','eggs','items')),'foreign relevant resource changed')
 need(all(int(k) not in changed['moves'] for k in spec['moves']),'declared move record changed')
 need(v4.machines==final.machines,'TM/HM entries changed')
 try:R.verify_semantics(spec,final)
 except ValueError as e:need(str(e)=='archive preimage differs: a/0/5/6','unexpected final global guard failure');message=str(e)
 else:raise ValueError('expected final pre-stage guard refusal missing')
 return dict(pre_stage_full_semantics=True,final_full_guard=False,final_guard_reason=message,member_changes=changed,declared_move_item_records_preserved=True,configuration_sha256=sha(config_from(v4)))


def require_run(r,*,native=False):
 need(r['variant']==('native' if native else 'current'),'execution result variant')
 need(r['reader_calls']==1 and r['resume']['r'][0]==r['reader_result'],'native reader once/exact return value')
 need(r['resume']['sp']==r['seam']['sp'] and r['resume']['r'][4:12]==r['seam']['r'][4:12],'seam SP/r4-r11 ABI')
 if not native:need(r['resume']['r'][1:3]==r['seam']['r'][1:3],'resident stub r1/r2 restoration')
 need(r['buffer_sha256']==r['buffer_expected_sha256'] and r['canaries'] and r['stack_canary'],'native buffer bounds/readback')
 need(r['seed_before']==r['seed_after']==r['seam']['saved_seed']==0x12345678,'global RNG preservation')
 need(list(r['party_header'])==[6,0] and r['max_stack']<=320 and r['instructions']<=200000,'prefix empty party/stack/instruction scope')
 need([x[0] for x in r['events']]==['alloc','alloc','read'],'prefix SDK event sequence')
 reg=[[0,0] for _ in range(8)];scenario=r['scenario']
 if scenario=='refused':reg[0]=[12,1]
 elif not native:reg[0]=[126,0]
 need([list(x) for x in r['registry']]==reg,'native registry lifetime')
 success=not native and scenario=='success';failed=not native and scenario=='failed';loaded=success or failed
 need((r['unload_calls'],r['assert_calls'],r['wfc_calls'],r['wfc_counter'])==(int(not native),int(failed),int(success),int(success)),'native unload/assert/WFC branches')
 ov=r['overlay'];need(ov['image']==([[126,scenario!='failed']] if loaded else [] ) or ov['image']==([(126,scenario!='failed')] if loaded else []),'SDK image declared branch')
 need(ov['unload']==([126] if loaded else []),'SDK unload transport')
 expected_critical=[]
 if loaded:expected_critical=[(0x200702E,B.REGISTRY+4,1),(0x2007030,B.REGISTRY,126)]
 if success:expected_critical.append((0x23DA3E2,0x23DA044,1))
 if loaded:expected_critical.append((0x2006F78,B.REGISTRY+4,0))
 need(r['critical']==[dict(pc=hex(pc),address=hex(a),bytes=4,value=v) for pc,a,v in expected_critical],'native PC-specific registry/WFC stores')
 reads=r['config_reads'];need([(int(x['address'],16),x['bytes']) for x in reads]==([(CONFIG,4),(CONFIG+6,1)] if success else []),'inactive config short-circuit reads')
 pcs={int(x['ram'],16) for x in r['code']};need({B.ENTRY,0x20735E8}<=pcs and B.SEAM_RESUME not in pcs,'actual prefix/reader only through seam boundary')
 need((0x226B4A0 in pcs)==success and (0x202551C in pcs)==failed and (0x23DA47C in pcs)==success,'actual module/assert/WFC execution coverage')
 return True


def lineage(model,role,raw):
 abi=R.load_abi();windows=[]
 for a,n in ((0x2073604,1172),(0x20735E8,28),(0x2006FF8,300),(0x2006F7C,48),(STUB,192),(0x23DA250,572)):
  try:b=G.piece(model['segments'],a,n)
  except ValueError:
   need(role in ('retail','base11') and a in (STUB,0x23DA250),'unexpected missing resident mapping');windows.append(dict(ram=hex(a),bytes=n,mapped=False));continue
  record=dict(ram=hex(a),bytes=n,sha256=sha(b),mapped=True)
  if a==0x2073604:
   normalized=bytearray(b)
   if role=='r4':need(b[0x36:0x3A]==bytes.fromhex('62f3d1f9'),'current reader seam');normalized[0x36:0x3A]=bytes.fromhex('fff7d5ff')
   else:need(b[0x36:0x3A]==bytes.fromhex('fff7d5ff'),'native reader seam preimage')
   if role in ('retail','base11'):
    for site in (0x2073718,0x2073802,0x207390C,0x2073A0C):
     at=site-a;need(b[at:at+4]==bytes.fromhex('5288301c'),'native level read preimage')
     normalized[at:at+4]=R.bl_thumb(site,0x23D6228)
   need(sha(normalized)==abi['constructor']['sha256'],'constructor lineage differs beyond exact seams');record['comparison_only_normalized_sha256']=sha(normalized)
  elif a==0x20735E8:
   need(sha(b[:16])=='27dcad0b12e4eeded8920981ba4b613bfba9e9342429c89a40555c4702b2a2f7','native party-reader extent')
   # The 28-byte historical pin includes the adjacent 12-byte trainer-header thunk.
  elif a==0x2006FF8:
   normalized=bytearray(b)
   if role in ('retail','base11'):
    need(b[176:180]==bytes.fromhex('0120f8bd'),'retail loader return preimage');normalized[176:180]=R.bl_thumb(0x20070A8,0x23DA47C)
   need(sha(normalized)==abi['overlay']['loader']['HandleLoadOverlay']['sha256'],'overlay loader lineage beyond WFC return')
  elif a==0x2006F7C:need(sha(b)==abi['overlay']['loader']['UnloadOverlayByID']['sha256'],'native unload lineage')
  elif a==STUB:
   if role=='v4':need(b==bytes(192),'V4 reserve zero preimage')
   elif role=='r4':need(sha(b[:64])==STUB_SHA and sha(b[64:])=='c9c1a097c7e0a73ff6e38d7e2756d1fe3206958ac9fe7ddcccc7b9f11d664c8c','shared rematch64/Uturn128 ownership')
  elif a==0x23DA250:
   need(sha(b)=='d275bc783f587c382d7ffd71bc7488241b3199fed2fc68861c5edcfb1e9f1153','inherited WFC bundle exact readback')
   bundle=SOURCE/'sgp12/build/wifi/vfinale/blob.bin';need(b==bundle.read_bytes(),'WFC archived artifact readback')
  windows.append(record)
 module,overlay=G.S.SHARED.overlay(raw,126)
 if role=='r4':need(overlay['y9_words']==[126,MODULE,2048,0,MODULE,MODULE,126,0] and sha(module)==MODULE_SHA,'current overlay126 row/image')
 else:need(overlay['stored_bytes']==20 and overlay['decoded_bytes']==32 and overlay['stored_sha256']==abi['overlay']['placeholder_file_sha256'],'historical placeholder126')
 return dict(input=role,identity=model['record'],windows=windows,overlay126=overlay)


def compile_exact(work,config):
 code,symbols=R.compile_native(work,MODULE,CONFIG,768,retain_object=True)
 stub,stub_symbols=R.compile_stub(work,STUB,symbols['rematch_hook'],retain_object=True)
 need(len(code)==1216 and len(stub)==60 and len(config)==716,'exact build geometry')
 image=code+bytes(1280-len(code))+config+bytes(768-len(config))
 need(sha(image)==MODULE_SHA and sha(stub+bytes(4))==STUB_SHA,'recompiled exact module/stub pins')
 native_proof=audit_elf((work/'rematch-variants.o').read_bytes(),code,MODULE);stub_proof=audit_elf((work/'rematch-stub.o').read_bytes(),stub,STUB)
 need(native_proof['symbols']['rematch_hook']==hex(symbols['rematch_hook']) and stub_proof['symbols']['c8_stub']==hex(STUB|1),'independent ELF entries')
 for name,blob in (('module.bin',image),('stub.bin',stub),('config.bin',config)):(work/name).write_bytes(blob)
 return mapped_code(native_proof,code,MODULE),dict(native=native_proof,stub=stub_proof,module_sha256=sha(image),configuration_sha256=sha(config),compiler_version=R.COMPILER_VERSION,compiler_sha256=R.COMPILER_SHA256,code_allocation=1280,config_allocation=768,module_bytes=2048,stub_allocation=64)


def analyze(rom,v4,base,retail,language,work):
 import gc
 need(sys.flags.optimize==0,'run without Python -O')
 current=G.S.SHARED.read_current(rom,language);records=[]
 for role,path in (('retail',retail),('base11',base),('v4',v4),('r4',rom)):
  model=current if role=='r4' else G.S.SHARED.read_image(path,language,role)
  with path.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   records.append(lineage(model,role,raw))
   if role=='v4':before,br=resources(raw,model)
   elif role=='r4':after,ar=resources(raw,model)
  del model;gc.collect()
 stage=staging(before,after);config=config_from(before)
 work.mkdir(parents=True,exist_ok=False);module_code,build=compile_exact(work,config)
 with rom.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
  view=G.S.SHARED.gifts_audit.Arm9View(raw)
  need(view.read(STUB,64)==(work/'stub.bin').read_bytes()+bytes(4),'independent ARM9 stub readback')
  need(view.read(SEAM,4)==R.bl_thumb(SEAM,STUB),'independent ARM9 reader seam')
  need(G.S.SHARED.overlay(raw,126)[0]==(work/'module.bin').read_bytes(),'independent FAT/y9 module readback')
  physical=dict(stub_rom_offset=hex(view.offset(STUB,64)),seam_rom_offset=hex(view.offset(SEAM,4)),reader_rom_offset=hex(view.offset(0x20735E8,16)))
  positives=[];controls=[];counters=[]
  for trainer in (712,713):
   for plus in (0,1):
    natives={}
    for scenario in ('success','refused'):
     r=run_case(current,raw,language,module_code,trainer,scenario,'native',plus);require_run(r,native=True);controls.append(r);natives[scenario]=r
    for scenario in ('success','refused','failed'):
     r=run_case(current,raw,language,module_code,trainer,scenario,'current',plus);require_run(r)
     control=natives['refused' if scenario=='refused' else 'success']
     need(r['neutral_ram_sha256']==control['neutral_ram_sha256'],'inert full unrelated RAM differs from native control');positives.append(r)
  for scenario in ('success','failed'):
   r=run_case(current,raw,language,module_code,scenario=scenario,variant='skip_unload')
   need(r['reader_calls']==1 and r['resume']['r'][0]==r['reader_result'] and r['buffer_sha256']==r['buffer_expected_sha256'] and r['registry'][0]==(126,1),'same-output missing-unload premise')
   disguised=dict(r,variant='current')
   try:require_run(disguised)
   except ValueError as e:r['rejection']=str(e)
   else:raise ValueError('same-output missing-unload counter accepted')
   counters.append(r)
  for variant,scenario,expected in (('wrong_args','refused','archive forward ABI'),('pool_entry','success','outside qualified code')):
   try:run_case(current,raw,language,module_code,scenario=scenario,variant=variant)
   except ValueError as e:need(expected in str(e),'wrong counter rejection');counters.append(dict(variant=variant,scenario=scenario,rejection=str(e),completed=False))
   else:raise ValueError('invalid ABI/code counter accepted')
  for value in (0,0xFFFFFFFF):
   r=run_case(current,raw,language,module_code,reader_result=value);require_run(r);controls.append(r)
 result=dict(schema='rematch-inert-attribution-v1',language=language,inputs=records,staging=stage,physical=physical,build=build,positives=positives,controls=controls,counters=counters,
  resources=dict(pre_stage=br,final=ar),source_sha256={str(p.relative_to(SOURCE)):sha(p.read_bytes()) for p in (Path(__file__),Path(R.__file__),Path(B.__file__),R.FEATURE/'stub.S',R.FEATURE/'native.c',R.FEATURE/'variants.c',R.FEATURE/'variants.h',R.DATA/'rematch-native-abi.json',R.DATA/'rematch-variants.json',SOURCE/'features/options/tools/carica_text.py')},
  conclusions=dict(documented_provenance=True,reconstructed_binary_correspondence=True,initialized_inert_semantics=True,natural_activation_observed=False,active_variants_qualified=False),
  limits=['Stops before first instruction at 0207363E: no party species interpretation, level-hook, battle, SAVE, hardware or timing claim',
   'Heap/archive/SDK FS are declared models; FS unload poison is diagnostic and the synthetic reader return exercises forwarding ABI',
   'Actual GF_AssertFail is qualified only with CommState pointer NULL; actual WFC path only for unrelated overlay126',
   'No native HGSS MW rebuild or WFC rebuild; archived inherited artifact/compiler version differ from the current rematch toolchain',
   'Pre-stage semantics pass on V4; final global trainer preimage refuses the independent Wade460/461 swap; relevant rematch inputs preserved',
   'Native code whitelist qualifies these initialized paths; overlay12 busy is registry metadata, not an observed naturally loaded battle'])
 return result


def validate_outputs(inputs,work,output):
 need(not work.exists() and not work.is_symlink(),'--work must be a fresh nonexistent directory')
 need(not output.exists() and not output.is_symlink(),'--json must be a fresh nonexistent file')
 need(work.resolve()!=output.resolve() and work.resolve() not in output.resolve().parents,'--json must be outside --work')
 for p in inputs:need(p.is_file() and p.resolve() not in (work.resolve(),output.resolve()),'input/output identity')
 for p in (work,output):need(SOURCE not in p.resolve().parents and p.resolve()!=SOURCE,'outputs must be outside source')


def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','v4','base','retail','work','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);args=parser.parse_args()
 try:
  validate_outputs((args.rom,args.v4,args.base,args.retail),args.work,args.json)
  result=analyze(args.rom,args.v4,args.base,args.retail,args.language,args.work)
  args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'exact rematch64/module126 reconstructed; 12 initialized inert paths + 10 controls + 4 counterproofs verified')


if __name__=='__main__':main()
