#!/usr/bin/env python3
"""Verify the native whole-NARC-member reader with explicit raw-file FS models.

The native parser selects the member. FS services expose only a whole archive
and cursor; native SDK internals and natural caller activation remain separate.
"""
from pathlib import Path
import importlib.util,struct,json,mmap,gzip,sys,gc,copy
s=importlib.util.spec_from_file_location('narc_reader_species_parent',Path(__file__).with_name('attribuisci_nome_specie.py'));W=importlib.util.module_from_spec(s);s.loader.exec_module(W)
P,B,N,need,sha=W.P,W.B,W.N,W.need,W.sha
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
import ndspy.rom,ndspy.narc
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_CPSR
ENTRY,HELPER,TOP,STOP,DEST=0x2007508,0x200732C,0x23BF000,0x23BE000,0x2360000
SDK={0x20D7F98:'FS_InitFile',0x20D8278:'FS_OpenFile',0x20D83DC:'FS_SeekFile',0x20D83CC:'FS_ReadFile',0x20D82C0:'FS_CloseFile'}
SPANS=((0x2007508,22,10,'35f4ac50be98a10b0c0ebd562ed4d45e5bdffa88ca7ff0134f0c09090a8df196'),(0x200732C,98,42,'0f2890f6d5c533785bd464399a496a780ab21162dabc4829f3c878c5049f379c'),(0x2007392,98,43,'5353169e22ee79de93dfe32d757e89feea1ef586b9fba01e30fdf6dc2fdbbf47'),(0x20073F8,20,8,'7740a174f812ba014226329d5680a4a9cff0cb216fc4c37180ab3392adba6262'))
DATA=((0x2007520,4,'ee48acbcb107da0b1d1af8eda167ab79e113683b28f1f143aa88b068a82806e4'),(0x210F2EC,8,'a70dd44ae4c2080468c44e922263dba23a8956b3134e59c5ee374fca489e7470'),(0x210F030,16,'eb05238953807b3f06e9a7f850f6b6f9b5668284de59fa7a876652fcb7803c3f'))
FS_SHA='85827bd31be4e7418e46bf4715e60ca1d4287b4243ff129973febadeac343b0c'

def qualify(model,raw):
 view=P.G.S.SHARED.gifts_audit.Arm9View(raw);code={};proof=[]
 for address,size,count,digest in SPANS:
  blob=view.read(address,size);need(blob==P.G.piece(model['segments'],address,size) and sha(blob)==digest,'native NARC parser raw/section/span identity');instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,address));need(len(instructions)==count and sum(i.size for i in instructions)==size,'native NARC parser ordinary decoding')
  for i in instructions:need(i.address not in code,'native NARC code span overlap');code[i.address]=(i.size,True)
  proof.append(dict(ram=hex(address),bytes=size,rom_offset=hex(view.offset(address,size)),sha256=digest,starts=count,kind='ordinary Thumb code'))
 for address,size,digest in DATA:
  blob=view.read(address,size);need(blob==P.G.piece(model['segments'],address,size) and sha(blob)==digest,'native NARC data/pool/path identity');need(not any(address<=pc<address+size for pc in code),'NARC data admitted as code');proof.append(dict(ram=hex(address),bytes=size,rom_offset=hex(view.offset(address,size)),sha256=digest,kind='data only'))
 need(len(code)==103 and code.get(0x20073FE)==(4,True) and 0x2007400 not in code,'qualified whole BLX across 1KiB boundary')
 fs=view.read(0x20D7F98,0x4B0);need(fs==P.G.piece(model['segments'],0x20D7F98,len(fs)) and sha(fs)==FS_SHA,'modeled FS SDK body identity');proof.append(dict(ram='0x20d7f98',bytes=0x4B0,rom_offset=hex(view.offset(0x20D7F98,0x4B0)),sha256=FS_SHA,kind='SDK identity only; five ARM services modeled'))
 return code,proof

def resources(raw):
 result={};rom=ndspy.rom.NintendoDSRom(raw);fat=struct.unpack_from('<I',raw,0x48)[0]
 for narc in (55,56):
  path='a/0/5/'+str(narc-50);members,receipt=P.RAW.raw_archive(raw,path);start,end=struct.unpack_from('<II',raw,fat+8*receipt['file_id']);archive=bytes(raw[start:end]);need(archive==rom.getFileByName(path) and sha(archive)==receipt['archive_sha256'],'whole raw NARC independent FAT/FNT/ndspy readback');need(len(members)==738 and len(members[31])==(20 if narc==55 else 108),'finite reader selected member domain')
  btaf=struct.unpack_from('<H',archive,12)[0];btaf_size=struct.unpack_from('<I',archive,btaf+4)[0];btnf=btaf+btaf_size;btnf_size=struct.unpack_from('<I',archive,btnf+4)[0];gmif=btnf+btnf_size;lo,hi=struct.unpack_from('<II',archive,btaf+12+31*8);position=gmif+8+lo;need(archive[position:position+hi-lo]==members[31] and start+position==receipt['member_rom_offsets'][31],'selected NARC arithmetic independent readback')
  result[str(narc)]=dict(raw=archive,path=path,member=bytes(members[31]),oracle=dict(narc=narc,path=path,file_id=receipt['file_id'],archive_rom_offset=start,archive_bytes=len(archive),archive_sha256=sha(archive),member=31,member_bytes=hi-lo,member_sha256=sha(members[31]),member_archive_offset=position,member_rom_offset=start+position,btaf=btaf,btaf_bytes=btaf_size,btnf=btnf,btnf_bytes=btnf_size,gmif=gmif,count=738,start=lo,end=hi))
 return result

class Reader:
 latest=None
 def __init__(self,model,code,data,narc,*,fill=0xC7,observe=True,clobber=False,variant='current'):
  need(sys.flags.optimize==0,'run without Python -O');need(type(narc)is int and narc in (55,56) and type(fill)is int and fill in (0xC7,0x39) and type(observe)is bool and type(clobber)is bool and variant in ('current','skip_close','short_payload') and (observe or variant=='current'),'finite native NARC reader fixture domain');Reader.latest=self;self.model,self.code,self.data,self.narc=model,code,data,narc;self.fill,self.observe,self.clobber,self.variant=fill,observe,clobber,variant;self.steps=0;self.max_stack=0;self.seen=set();self.models=[];self.writes=[];self.shadows=[];self.file=None;self.open=False;self.initialized=False;self.cursor=None;self.archive=None;self.path=None;self.read_count=0;self.helper=None;self.helper_return=None
 def regs(self):return [self.u.reg_read(r) for r in B.R]+[self.u.reg_read(UC_ARM_REG_SP),self.u.reg_read(UC_ARM_REG_LR),self.u.reg_read(UC_ARM_REG_CPSR)]
 def read_bytes(self,a,n):return bytes(self.u.mem_read(a,n))
 def setup(self):
  gc.collect();self.u=u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);need(u.ctl_get_cpu_model()==17,'qualified native reader CPU17');u.mem_map(0x1FF8000,0x8000);u.mem_map(0x2000000,0x400000);u.mem_map(0x27E0000,0x1000)
  for a,blob in self.model['segments']:u.mem_write(a,blob)
  u.mem_write(TOP-192,bytes([self.fill])*192);u.mem_write(DEST-16,b'\xA5'*140);u.mem_write(0x21D15A8,struct.pack('<I',0x12345678));u.reg_write(UC_ARM_REG_CPSR,0x3F);u.reg_write(UC_ARM_REG_SP,TOP)
  for i,value in enumerate(N.COOKIES,4):u.reg_write(B.R[i],value)
  u.reg_write(B.R[3],0x33333303);u.reg_write(B.R[12],0xCCCC000C)
  for i,value in enumerate((DEST,self.narc,31)):u.reg_write(B.R[i],value)
  u.reg_write(UC_ARM_REG_LR,STOP|1);self.entry=self.regs();self.before=self.read_bytes(0x2000000,0x400000);u.hook_add(UC_HOOK_CODE,self.step);u.hook_add(UC_HOOK_MEM_READ,self.read);u.hook_add(UC_HOOK_MEM_WRITE,self.write)
 def service(self,pc):
  u=self.u;before=self.regs();args=before[:4];sp,lr=before[13:15];kind=SDK[pc];need(sp==TOP-136 and sp%8==0 and not before[15]&32,'FS ARM boundary frame/ISA');file=TOP-112;need(args[0]==file,'FS single actual stack file address');event=dict(name=kind,pc=hex(pc),args=args,sp=sp,lr=hex(lr),saved=before[4:12],cursor_before=self.cursor,open_before=self.open)
  if kind=='FS_InitFile':need(not self.initialized and self.file is None,'single opaque FS initialization');self.initialized=True;self.file=file;result=file
  else:
   need(self.initialized and self.file==file,'FS initialized handle identity')
   if kind=='FS_OpenFile':
    need(not self.open and self.archive is None,'single FS open');path=bytearray()
    for i in range(16):
     byte=self.read_bytes(args[1]+i,1)[0]
     if not byte:break
     path.append(byte)
    else:raise ValueError('bounded FS path terminator')
    name=path.decode('ascii');matches=[v for v in self.data.values() if v['path']==name];need(len(matches)==1,'FS permitted raw archive path');self.archive=matches[0]['raw'];self.path=name;self.open=True;self.cursor=0;event.update(path=name,archive_bytes=len(self.archive),archive_sha256=sha(self.archive),native_FSFile_layout_modeled=False);result=1
   else:
    need(self.open and self.cursor is not None,'FS operation requires open handle')
    if kind=='FS_SeekFile':need(args[2]==0 and 0<=args[1]<=len(self.archive),'FS SET seek whole archive bounds');self.cursor=args[1];result=1
    elif kind=='FS_ReadFile':
     dest,size=args[1:3];need(type(size)is int and 0<size<=108 and self.cursor+size<=len(self.archive),'FS raw read bounds');need(TOP-136<=dest and dest+size<=TOP-16 or DEST<=dest and dest+size<=DEST+len(self.data[str(self.narc)]['member']),'FS model write destination outside caller locals/fixture');position=self.cursor;self.read_count+=1;delivered=size-1 if self.variant=='short_payload' and self.read_count==7 else size;blob=self.archive[position:position+delivered];u.mem_write(dest,blob);self.cursor+=delivered;result=delivered;event.update(position=position,destination=dest,requested_bytes=size,delivered_bytes=delivered,delivered_sha256=sha(blob))
    else:need(kind=='FS_CloseFile','unknown FS model');self.open=False;result=1
  if self.clobber:
   for i in (1,2,3,12):u.reg_write(B.R[i],0xA5000000+i)
   u.reg_write(UC_ARM_REG_CPSR,(u.reg_read(UC_ARM_REG_CPSR)&0x0FFFFFFF)|(0xA<<28))
  u.reg_write(B.R[0],result);u.reg_write(UC_ARM_REG_PC,lr);after=self.regs();need(after[13]==sp and after[4:12]==before[4:12] and after[15]&32,'FS modeled ABI/ARM-to-Thumb return');event.update(result_r0=result,return_sp=after[13],return_saved=after[4:12],return_volatile=[after[i] for i in (1,2,3,12)],cursor_after=self.cursor,open_after=self.open);self.models.append(event)
 def step(self,u,pc,n,user):
  self.steps+=1;regs=self.regs();sp=regs[13];need(self.steps<=20000 and TOP-192<=sp<=TOP and sp%4==0,'native reader instruction/stack budget');self.max_stack=max(self.max_stack,TOP-sp)
  if pc in SDK:need(n==4 and not regs[15]&32,'FS modeled ARM instruction width/ISA');self.service(pc);return
  need(self.code.get(pc)==(n,bool(regs[15]&32)),'native reader fetch outside qualified width/ISA');need(self.read_bytes(pc,n)==P.G.piece(self.model['segments'],pc,n),'native reader live code bytes drift');self.seen.add(pc)
  if pc==HELPER:need(self.helper is None,'single native parser entry');self.helper=dict(entry=hex(pc),before=regs,fifth=struct.unpack('<I',self.read_bytes(sp,4))[0])
  if pc==0x200751A:need(self.helper is not None and self.helper_return is None,'single native parser return');self.helper_return=regs
  if self.variant=='skip_close' and pc==0x2007404:self.shadows.append(dict(pc=hex(pc),kind='skip native FS_CloseFile BLX',next_pc='0x2007408'));u.reg_write(UC_ARM_REG_PC,0x2007409)
 def read(self,u,access,address,n,value,user):
  need(TOP-192<=address and address+n<=TOP or any(a<=address and address+n<=a+size for a,size,digest in DATA),'native reader read outside stack/pool/path table')
 def write(self,u,access,address,n,value,user):
  pc=u.reg_read(UC_ARM_REG_PC);need(TOP-136<=address and address+n<=TOP,'native reader store outside owned stack')
  if self.observe:self.writes.append(dict(pc=hex(pc),address=address,bytes=n,value=value))
 def run(self):
  self.setup();self.u.emu_start(ENTRY|1,STOP,count=20001);end=self.regs();need(self.u.reg_read(UC_ARM_REG_PC)==STOP and end[13]==TOP and end[4:12]==list(N.COOKIES) and end[15]&32 and self.helper_return is not None,'native reader actual return ABI/context');size=len(self.data[str(self.narc)]['member']);after=self.read_bytes(0x2000000,0x400000);masked=bytearray(after)
  for a,n in ((TOP-192,192),(DEST,size)):masked[a-0x2000000:a-0x2000000+n]=self.before[a-0x2000000:a-0x2000000+n]
  need(bytes(masked)==self.before,'native reader unrelated RAM changed');canaries=self.read_bytes(DEST-16,16)==b'\xA5'*16 and self.read_bytes(DEST+size,124-size)==b'\xA5'*(124-size)
  return dict(narc=self.narc,member=31,fill=self.fill,observe=self.observe,clobber=self.clobber,variant=self.variant,cpu_model=self.u.ctl_get_cpu_model(),entry=self.entry,end=end,helper=self.helper,helper_return=self.helper_return,models=self.models,native_writes=self.writes,observed_pcs=sorted(self.seen),instructions=self.steps,max_stack=self.max_stack,initialized=self.initialized,open=self.open,file=self.file,path=self.path,cursor=self.cursor,reads=self.read_count,shadows=self.shadows,destination_hex=self.read_bytes(DEST,size).hex(),destination_sha256=sha(self.read_bytes(DEST,size)),canaries=canaries,stack_canary=self.read_bytes(TOP-192,56)==bytes([self.fill])*56,stack_frame_hex=self.read_bytes(TOP-136,136).hex(),unrelated_ram_unchanged=True,unrelated_ram_sha256=sha(bytes(masked)),ram_sha256=sha(after),rng_after=struct.unpack('<I',self.read_bytes(0x21D15A8,4))[0])

def lineage(paths,language):
 """Candidate-address checks only; a differing revision is not auto-attributed."""
 rows=[]
 for role,path in paths.items():
  model=P.G.S.SHARED.read_current(path,language) if role=='r4' else P.G.S.SHARED.read_image(path,language,role);windows=[];archives={}
  with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
   for address,size,*rest in SPANS+DATA:
    digest=rest[-1];blob=P.G.piece(model['segments'],address,size);windows.append(dict(candidate_ram=hex(address),bytes=size,sha256=sha(blob),current_sha256=digest,exact_current_match=sha(blob)==digest,attributed=not(role=='retail' and language=='IT') and sha(blob)==digest))
   fat=struct.unpack_from('<I',raw,0x48)[0]
   for narc in (55,56):
    members,receipt=P.RAW.raw_archive(raw,'a/0/5/'+str(narc-50));start,end=struct.unpack_from('<II',raw,fat+8*receipt['file_id']);archives[str(narc)]=dict(archive_bytes=end-start,archive_sha256=sha(raw[start:end]),archive_rom_offset=start,count=len(members),member31_bytes=len(members[31]),member31_sha256=sha(members[31]),member31_rom_offset=receipt['member_rom_offsets'][31])
  table=struct.unpack('<I',P.G.piece(model['segments'],0x2007520,4))[0];routes=[]
  for narc in (55,56):
   row=table+4*narc;pointer=struct.unpack('<I',P.G.piece(model['segments'],row,4))[0];name=bytearray()
   for offset in range(16):
    byte=P.G.piece(model['segments'],pointer+offset,1)[0]
    if not byte:break
    name.append(byte)
   else:raise ValueError('historical native path route unterminated')
   need(bytes(name)==('a/0/5/'+str(narc-50)).encode(),'historical native path source correspondence');routes.append(dict(narc=narc,table_ram=hex(table),row_ram=hex(row),row_sha256=sha(struct.pack('<I',pointer)),path_ram=hex(pointer),path=name.decode(),path_bytes_sha256=sha(bytes(name)+b'\0')))
  code_match=all(w['exact_current_match'] for w in windows[:4])
  for window in windows[:4]:window['attributed']=code_match
  fs_sha=sha(P.G.piece(model['segments'],0x20D7F98,0x4B0))
  rows.append(dict(role=role,input=model['record'],candidate_windows=windows,archives=archives,native_path_routes=routes,code_and_path_correspondence=code_match,fs_identity_only=dict(sha256=fs_sha,exact_current_match=fs_sha==FS_SHA),limits=['Candidate code spans and actual-image literal/table/path route; no historical execution or native compiler reconstruction; legacy compressed sections have no inferred direct physical offset']))
  del model;gc.collect();W.require_host_budget()
 return rows

def require_case(r,data,code):
 narc=r['narc'];need(type(narc)is int and narc in (55,56) and r['member']==31 and type(r['fill'])is int and r['fill']in (0xC7,0x39) and r['observe']is True and type(r['clobber'])is bool and r['variant']=='current' and not r['shadows'] and r['cpu_model']==17,'native reader accepted receipt domain');raw=data[str(narc)]['raw'];o=data[str(narc)]['oracle'];size=o['member_bytes'];local=TOP-136;file=TOP-112;path=0x210F038 if narc==55 else 0x210F030;cookies=list(N.COOKIES);cookie3=0x33333303;c4,c5,c6,c7=cookies[:4];tail=cookies[4:];volatile=[0xA5000000+i for i in (1,2,3,12)];clobber=r['clobber']
 payload=data[str(narc)]['member'];need(r['destination_hex']==payload.hex() and r['destination_sha256']==sha(payload),'native parser exact independently selected payload')
 need(r['instructions']==118 and r['max_stack']==136 and r['observed_pcs']==sorted(code) and len(code)==103 and r['initialized']is True and r['open']is False and r['file']==file and r['path']==o['path'] and r['cursor']==o['member_archive_offset']+size and r['reads']==7 and r['canaries']is True and r['stack_canary']is True and r['unrelated_ram_unchanged']is True and r['rng_after']==0x12345678,'native reader complete path/ownership/stack/frozen state')
 entry,end=r['entry'],r['end'];need(len(entry)==len(end)==16 and entry[:4]==[DEST,narc,31,cookie3] and entry[4:12]==end[4:12]==cookies and entry[12]==0xCCCC000C and entry[13]==end[13]==TOP and entry[14]==STOP|1 and entry[15]==0x3F and end[14]==0x2007409,'native reader actual outer ABI/saved registers')
 need(end[:4]==[1,volatile[0] if clobber else DEST,volatile[1] if clobber else size,cookie3] and end[12]==(volatile[3] if clobber else 0xCCCC000C) and end[15]==(0xA000003F if clobber else 0x2000003F),'native reader declared SDK result policy/void residual registers')
 helper=r['helper'];before,after=helper['before'],r['helper_return'];need(helper['entry']==hex(HELPER) and helper['fifth']==0 and before[:4]==[DEST,path,31,0] and before[4:12]==after[4:12]==[narc*4,c5,c6,c7]+tail and before[13]==after[13]==TOP-16 and before[14]==0x200751B and after[:3]==end[:3] and after[3]==0 and after[14:]==end[14:] and before[15]&32,'actual native parser fifth argument and return context')
 # Tuple: API, return LR, arguments R1/R2, saved R4..R7, and optional
 # file-read position/destination/size. R3 is offset0 until volatile controls.
 specs=(
 ('FS_InitFile',0x200734B,[0,31],[path,31,c6,c7],None),
 ('FS_OpenFile',0x2007353,[path,volatile[1] if clobber else 31],[path,31,c6,c7],None),
 ('FS_SeekFile',0x200735D,[12,0],[path,31,c6,c7],None),
 ('FS_ReadFile',0x2007367,[local+20,2],[path,31,c6,c7],(12,local+20,2)),
 ('FS_SeekFile',0x2007373,[o['btaf']+4,0],[o['btaf'],31,c6,c7],None),
 ('FS_ReadFile',0x200737D,[local+20,4],[o['btaf'],31,c6,c7],(o['btaf']+4,local+20,4)),
 ('FS_ReadFile',0x2007387,[local+8,2],[o['btaf'],31,c6,c7],(o['btaf']+8,local+8,2)),
 ('FS_SeekFile',0x20073A1,[o['btnf']+4,0],[o['btaf'],31,o['btnf'],c7],None),
 ('FS_ReadFile',0x20073AB,[local+20,4],[o['btaf'],31,o['btnf'],c7],(o['btnf']+4,local+20,4)),
 ('FS_SeekFile',0x20073BB,[o['btaf']+12+31*8,0],[o['btaf']+12,31,o['btnf'],o['btnf_bytes']],None),
 ('FS_ReadFile',0x20073C5,[local+16,4],[o['btaf']+12,31,o['btnf'],o['btnf_bytes']],(o['btaf']+12+31*8,local+16,4)),
 ('FS_ReadFile',0x20073CF,[local+12,4],[o['btaf']+12,31,o['btnf'],o['btnf_bytes']],(o['btaf']+16+31*8,local+12,4)),
 ('FS_SeekFile',0x20073E3,[o['member_archive_offset'],0],[o['btaf']+12,31,o['btnf'],o['btnf_bytes']],None),
 ('FS_ReadFile',0x2007403,[DEST,size],[o['btaf']+12,31,o['btnf'],o['btnf_bytes']],(o['member_archive_offset'],DEST,size)),
 ('FS_CloseFile',0x2007409,volatile[:2] if clobber else [DEST,size],[o['btaf']+12,31,o['btnf'],o['btnf_bytes']],None))
 need(len(r['models'])==15,'fifteen native FS boundary calls');cursor=None;opened=False;model_writes=[]
 for index,(event,(name,lr,args12,saved,read)) in enumerate(zip(r['models'],specs)):
  pc=next(a for a,v in SDK.items() if v==name);args=[file]+args12+[volatile[2] if clobber and index else 0];result=file if index==0 else read[2] if read else 1;need(event['name']==name and event['pc']==hex(pc) and event['lr']==hex(lr) and event['args']==args and event['sp']==event['return_sp']==local and event['saved']==event['return_saved']==saved+tail and event['result_r0']==result and event['cursor_before']==cursor and event['open_before']is opened,'source-derived exact FS entry/return ABI and previous cursor/lifetime')
  need(event['return_volatile']==(volatile if clobber else args12+[0,0xCCCC000C]),'explicit FS volatile preservation/clobber policy')
  if name=='FS_OpenFile':need(event['path']==o['path'] and event['archive_bytes']==len(raw) and event['archive_sha256']==sha(raw) and event['native_FSFile_layout_modeled']is False,'opaque FS open selects whole raw archive');cursor=0;opened=True
  elif name=='FS_SeekFile':cursor=args12[0]
  elif read:
   pos,dest,n=read;blob=raw[pos:pos+n];need(cursor==pos and event['position']==pos and event['destination']==dest and event['requested_bytes']==event['delivered_bytes']==n and event['delivered_sha256']==sha(blob),'native requested raw slices and model copy provenance');cursor+=n
   if dest!=DEST:model_writes.append((dest,blob))
  elif name=='FS_CloseFile':opened=False
  need(event['cursor_after']==cursor and event['open_after']is opened,'FS cursor advancement and single closure')
 expected=[]
 def store(pc,address,n,value):expected.append(dict(pc=hex(pc),address=address,bytes=n,value=value))
 def push(pc,address,values):
  for i,value in enumerate(values):store(pc,address+4*i,4,value)
 push(ENTRY,TOP-12,[cookie3,c4,STOP|1]);store(0x2007512,TOP-16,4,0);push(HELPER,TOP-40,[0,narc*4,c5,c6,c7,0x200751B])
 for pc,offset,n,value in ((0x2007334,0,4,DEST),(0x2007336,20,4,0),(0x2007338,16,4,0),(0x200733A,12,4,0),(0x200733E,8,2,0),(0x2007344,4,4,0),(0x20073EE,20,4,size)):store(pc,local+offset,n,value)
 need(len(expected)==17 and r['native_writes']==expected,'native reader entire ordered stack/store transcript')
 stack=bytearray([r['fill']])*136
 for e in expected:stack[e['address']-local:e['address']-local+e['bytes']]=e['value'].to_bytes(e['bytes'],'little')
 for dest,blob in model_writes:stack[dest-local:dest-local+len(blob)]=blob
 # Final chunk size native store follows all six model header reads.
 struct.pack_into('<I',stack,20,size)
 need(r['stack_frame_hex']==stack.hex(),'complete native stack/model-read/saved frame provenance')
 return True

def functional(r):return {k:v for k,v in r.items() if k not in ('observe','native_writes')}

def require_off_pair(on,off):
 need(on['observe']is True and off['observe']is False and on['variant']==off['variant']=='current' and off['native_writes']==[],'native reader paired OFF receipt domain');need(functional(on)==functional(off),'native reader all functional OFF/ON state differs');return dict(neutral=True,ram_sha256=on['ram_sha256'],scope='all API/helper/model/cursor/lifetime/stack/payload/frozen state and whole final RAM; only native store log disabled')

def require_counter(c,normal,data,code):
 require_case(normal,data,code);variant=c['variant'];need(variant in ('skip_close','short_payload') and c['tag_disguised']is True,'native NARC counter finite domain');r=c['result'];need(r['narc']==normal['narc']==56 and r['member']==normal['member']==31 and r['fill']==normal['fill']==0xC7 and r['observe']is True and r['clobber']is normal['clobber']is False and r['variant']==variant and r['cpu_model']==17 and len(r['end'])==len(r['helper_return'])==16,'counter actual same fixture inputs/CPU/return shape');need(r['native_writes']==normal['native_writes'] and r['stack_frame_hex']==normal['stack_frame_hex'] and r['observed_pcs']==normal['observed_pcs']==sorted(code) and r['max_stack']==136 and r['canaries']is r['stack_canary']is r['unrelated_ram_unchanged']is True and r['unrelated_ram_sha256']==normal['unrelated_ram_sha256'] and r['rng_after']==normal['rng_after'],'counter source-path/store/stack/frozen state premises')
 if variant=='skip_close':
  need(r['instructions']==117 and len(r['models'])==14 and r['models']==normal['models'][:-1] and r['open']is True and r['initialized']is True and r['file']==normal['file'] and r['cursor']==normal['cursor'] and r['reads']==7 and r['path']==normal['path'] and r['destination_hex']==normal['destination_hex'] and r['destination_sha256']==normal['destination_sha256'] and r['ram_sha256']==normal['ram_sha256'] and r['shadows']==[dict(pc='0x2007404',kind='skip native FS_CloseFile BLX',next_pc='0x2007408')],'same-payload/whole-RAM counter native skipped close and open ledger')
  expected_end=list(normal['end']);expected_helper=list(normal['helper_return'])
  for regs in (expected_end,expected_helper):regs[0]=TOP-112;regs[14]=0x2007403
  need(r['entry']==normal['entry'] and r['helper']==normal['helper'] and r['end']==expected_end and r['helper_return']==expected_helper,'native close skip complete actual return ABI and void residuals');reason='native reader complete path/ownership/stack/frozen state'
 else:
  n=len(data['56']['member']);payload=data['56']['member'][:-1];expected=copy.deepcopy(normal['models']);read=expected[13];read.update(delivered_bytes=n-1,delivered_sha256=sha(payload),result_r0=n-1,cursor_after=read['cursor_after']-1);expected[14]['cursor_before']-=1;expected[14]['cursor_after']-=1
  need(r['instructions']==118 and len(r['models'])==15 and r['models']==expected and r['open']is False and r['initialized']is True and r['file']==normal['file'] and r['path']==normal['path'] and r['reads']==7 and r['cursor']==normal['cursor']-1 and r['end']==normal['end'] and r['entry']==normal['entry'] and r['helper']==normal['helper'] and r['helper_return']==normal['helper_return'] and r['shadows']==[],'native short-read returns normally with expected partial cursor and no guest-state shadow')
  image=payload+b'\xA5';need(r['destination_hex']==image.hex() and r['destination_sha256']==sha(image) and image!=data['56']['member'] and r['ram_sha256']!=normal['ram_sha256'],'native short-read exact partial payload/untouched last byte');reason='native parser exact independently selected payload'
 disguised=copy.deepcopy(r);disguised['variant']='current';disguised['shadows']=[]
 try:require_case(disguised,data,code)
 except ValueError as e:need(str(e)==c['rejection']==reason,'counter expected source-bound rejection identity')
 else:raise ValueError('native NARC output/lifetime counter accepted')

def source_identities():
 result=W.source_identities();result[str(Path(__file__).resolve().relative_to(P.SOURCE))]=sha(Path(__file__).read_bytes());return result

def analyze(rom,language,history=None):
 W.require_host_budget();sources=source_identities();hist=lineage(history,language) if history else None;model=P.G.S.SHARED.read_current(rom,language);cases=[];controls=[];off=[];counters=[]
 with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  code,proof=qualify(model,raw);data=resources(raw)
  for narc in (55,56):
   for fill in (0xC7,0x39):
    r=Reader(model,code,data,narc,fill=fill).run();require_case(r,data,code);cases.append(r)
   r=Reader(model,code,data,narc,observe=False).run();off.append(dict(result=r,proof=require_off_pair(cases[-2],r)))
   r=Reader(model,code,data,narc,clobber=True).run();require_case(r,data,code);need(r['destination_hex']==cases[-2]['destination_hex'] and r['ram_sha256']==cases[-2]['ram_sha256'],'FS volatile clobber cannot change native selection/stack/RAM');controls.append(r)
  normal=next(r for r in cases if r['narc']==56 and r['fill']==0xC7)
  for variant in ('skip_close','short_payload'):
   r=Reader(model,code,data,56,variant=variant).run();disguised=copy.deepcopy(r);disguised['variant']='current';disguised['shadows']=[]
   try:require_case(disguised,data,code)
   except ValueError as e:counter=dict(variant=variant,result=r,tag_disguised=True,rejection=str(e))
   else:raise ValueError('native NARC counter accepted: '+variant)
   require_counter(counter,normal,data,code);counters.append(counter)
  need(source_identities()==sources,'native NARC reader sources changed during campaign');W.require_host_budget()
 return dict(schema='native-narc-reader-v1',language=language,input=model['record'],source_sha256=sources,proof=proof,resources={k:v['oracle'] for k,v in data.items()},history=hist,cases=cases,volatile_controls=controls,observer_off=off,counters=counters,compiler_invoked=False,limits=['Native whole-member APIs for55/31 and56/31 only; same code does not prove all archive/size/error branches','Five FS ARM services model opaque handle/whole raw archive/cursor; native FSFile struct layout and SDK internals are not reconstructed','Reference FSFile sizeof80 differs from apparent72 native local bytes; no guest FSFile layout/clear is fabricated','Initialized standalone API, not native caller composition, natural encounter, raw-save or hardware proof','Original native compiler/objects unavailable; candidate historical addresses and mismatches retain their limits'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--rom',type=Path,required=True);parser.add_argument('--language',choices=('EN','IT'),required=True);parser.add_argument('--json',type=Path,required=True)
 for name in ('retail','base','v4'):parser.add_argument('--'+name,type=Path)
 args=parser.parse_args()
 try:
  need(not args.json.exists() and not args.json.is_symlink(),'output must be fresh');output=args.json.resolve();need(P.SOURCE not in output.parents and output!=P.SOURCE,'output must be outside source');need(args.rom.is_file(),'exact ROM input must exist');extra=(args.retail,args.base,args.v4);need(not any(extra) or all(extra),'provide all three optional historical inputs');history=dict(retail=args.retail,base11=args.base,v4=args.v4,r4=args.rom) if all(extra) else None;result=analyze(args.rom,args.language,history);payload=(json.dumps(result,separators=(',',':'))+'\n').encode();need(len(payload)<=4*1024**2,'expanded NARC reader report budget');blob=gzip.compress(payload,mtime=0) if args.json.suffix=='.gz' else payload;need(len(blob)<=2*1024**2,'stored NARC reader report budget');W.require_host_budget();args.json.parent.mkdir(parents=True,exist_ok=True)
  with args.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(args.language,'finite native NARC parser verified; five FS services remain explicit models')
if __name__=='__main__':main()
