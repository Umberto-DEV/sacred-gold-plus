#!/usr/bin/env python3
"""Execute trainer31 caller preparation until the first constructor entry fetch.

Exact private r4 only. Message allocation/loading, raw archive I/O and Heap_Free
are declared models. The constructor instruction and caller return do not run.
"""
from pathlib import Path
import importlib.util,json,mmap,struct,sys
s=importlib.util.spec_from_file_location('packed_name_dependency',Path(__file__).with_name('attribuisci_nome.py'));N=importlib.util.module_from_spec(s);s.loader.exec_module(N)
P,B,need,sha=N.P,N.B,N.need,N.sha
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_CPU_ARM_946,UC_ARM_REG_CPSR,UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_LR
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
import ndspy.rom,ndspy.narc
WINDOWS=(
 (0x20733C0,0x2073418,True,'3f2ce1b634948b7c9fa854efbd133f579f3b0feec157a79af59581bd4bd9066d'),
 (0x2073422,0x2073454,True,'0877a9b930140e5a3bf0e694b15ce22be56830bb16d95524c83563d327adc218'),
 (0x20735D8,0x20735E2,True,'1bb0ec374a927128d9cd04b2309888f257fd5b391b25750c3f281fcecbdf653d'),
 (0x2026380,0x2026386,True,'afcaf4d6d1ea4ccb9ae9d2953c18e61fced83add52e6362c2e1b67d89284d2ba'),
 (0x202638A,0x2026392,True,'cc95c6e51b54e2fe53871efac88a1881bdba86631820f6e1ddae821b420e1be6'),
 (0x2026396,0x20263A2,True,'409c3bb118b74d32ae034ac718f4f63050d8ccf3d6e6c7111c4784cbf88e48bc'),
 (0x202A960,0x202A966,True,'bafbd8cb6b6a3bab1496e10ce9d5e0a70c2e1d3caf7ba44fc19b3805d197205a'),
 (0x202A9A8,0x202A9B0,True,'65dbdd275961231b0109218a8c7234e4e430023dd9fd590b4114c6aac84915f6'),
 (0x20272C8,0x20272D2,True,'3cd34cebb6739f17e068ad5900c7e22bbaf773e650abb5a81d9416045d1a589e'),
 (0x20272D6,0x20272E6,True,'7a3ced079796b9cec4b38e04152a8a849a13d96356b035f12f6958330abc47d3'),
 (0x20272EC,0x20272F0,True,'8bdadb00ad3389fd9d10292c291d2b47f6d30d0531c80bbc0dbfbd0813d70c8c'),
)
POOLS=(
 (0x207346C,4,'72159a5f017c7dd531c8cda5a1a616e5ac9eaf818b744631d40f38a80e6039ae'),
 (0x20735E4,4,'7c077a9160f0ef35be4dc9f35a6450fb911be9ed8fab707af0a24c5859bdfabc'),
 (0x20263A4,8,'43c04cdda6388c5ce5701804eff430a687a868b9d21dd2770147d7c4d1674e7e'),
 (0x202A968,4,'396e86e1d7539973bbcf742b42809e6aca2256fd10f5da32f8eb55121ea65370'),
 (0x20272E8,4,'a17cbf070a171a38e284fce3ee116cba9209de090c3ee013a0871ce3f7dffbda'),
 (0x20272F0,4,'74fadac4e0ed089705b56239c7e1b1bfb589d3fd315dcbd09eca976d41be007f'),
)
ENTRY,END=0x20733C0,0x2073604
TOP,SETUP=B.STACK_TOP,B.SETUP
SAVE,TABLE,MISC=0x2320000,0x23430AC,0x2320110
MSG,STRING,OPAQUE_NARC=0x2360000,0x2360100,0x2360080
LOCAL,TRAINER,NAME=TOP-76,SETUP+0x5C,SETUP+0x70
SERVICES={0x200BAF8:'NewMsgDataFromNarc',0x200BBA0:'NewString_ReadMsgData',0x2007508:'ReadWholeNarcMemberByIdPair',0x201AB0C:'Heap_Free'}

def qualify(model,raw):
 base,locations=N.qualify(model,raw);code={a:shape for a,shape in base.items() if 0x2026A68<=a<0x2026A74 or 0x2026A78<=a<0x2026A80 or 0x2026A84<=a<0x2026A9A or 0x20E5AD8<=a<0x20E5AF8};view=P.G.S.SHARED.gifts_audit.Arm9View(raw)
 for a,b,thumb,digest in WINDOWS:
  blob=view.read(a,b-a);need(blob==P.G.piece(model['segments'],a,b-a) and sha(blob)==digest,'caller native code/readback drift');ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(blob,a));need(sum(i.size for i in ins)==len(blob),'caller complete disassembly')
  for i in ins:need(i.address not in code,'caller code overlap');code[i.address]=(i.size,True)
  locations.append(dict(ram=hex(a),bytes=b-a,rom_offset=hex(view.offset(a,b-a)),sha256=digest,kind='executed code domain'))
 for a,n,digest in POOLS:
  need(sha(view.read(a,n))==digest and view.read(a,n)==P.G.piece(model['segments'],a,n),'caller pool/readback drift');need(all(pc+size<=a or pc>=a+n for pc,(size,_) in code.items()),'caller code/data overlap');locations.append(dict(ram=hex(a),bytes=n,rom_offset=hex(view.offset(a,n)),sha256=digest,kind='data'))
 need(view.read(END,2)==bytes.fromhex('f8b5'),'constructor first fetch identity')
 return code,locations

def resources(raw):
 files,receipt=P.RAW.raw_archive(raw,'a/0/5/5');header=bytes(files[31]);need(len(header)==20 and sha(header)=='db2e0fa9e4d0b97a0d1721e878001bcddafe1e379827adccc37844cdbce13fff','raw trainer31 header identity');bank=N.resources(raw);rom=ndspy.rom.NintendoDSRom(raw)
 need(bytes(ndspy.narc.NARC(rom.getFileByName('a/0/5/5')).files[31])==header,'independent trainer header readback');need(sha(bytes(ndspy.narc.NARC(rom.getFileByName('a/0/2/7')).files[729]))==bank['bank_sha256'],'independent name bank readback')
 return dict(header_hex=header.hex(),header_sha256=sha(header),header_rom_offset=receipt['member_rom_offsets'][31],name=bank['records']['31'],name_bank_sha256=bank['bank_sha256'],name_bank_rom_offset=bank['bank_rom_offset'])

def execute(model,code,data,*,poison=0xC7,observe=True,variant='current'):
 need(type(poison)is int and poison in (0xC7,0x39) and type(observe)is bool and variant in ('current','expanded_name','short_header','omit_free','skip_delete','skip_structure_copy','wrong_name_destination','wrong_capacity','wrong_ctor_lr'),'finite caller fixture domain')
 header=bytes.fromhex(data['header_hex']);words=data['name']['words'];name=N.words_bytes(words);string=B.pack_species_string(words);msg=struct.pack('<HHHHI',1,11,27,729,OPAQUE_NARC)
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_946);u.mem_map(0x2000000,0x400000)
 for a,blob in model['segments']:
  if 0x2000000<=a and a+len(blob)<=0x2400000:u.mem_write(a,blob)
 setup=bytearray([0xA5])*0x200;struct.pack_into('<I',setup,0,1)
 for i in range(4):struct.pack_into('<I',setup,4+4*i,B.PARTIES+0x1000*i);struct.pack_into('<I',setup,0x18+4*i,31 if i==1 else 0)
 u.mem_write(SETUP,bytes(setup));u.mem_write(TOP-128,bytes([poison])*128);u.mem_write(TABLE,struct.pack('<I',0x100));u.mem_write(MSG-16,bytes([0xD3])*0x140);before=bytes(u.mem_read(0x2000000,0x400000));stack_tail=before[LOCAL+20-0x2000000:LOCAL+52-0x2000000]
 services=[];native_calls=[];writes=[];models=[];seen=set();steps=0;low=TOP;msg_live=False;string_live=False;string_created=False;frees=0;endpoint=None;source52=None;copy52=[];pending=[]
 reg=lambda i:u.reg_read(B.R[i]);sp=lambda:u.reg_read(UC_ARM_REG_SP);read=lambda a,n:bytes(u.mem_read(a,n))
 def inside(a,n,start,size):return start<=a and a+n<=start+size
 def hostwrite(a,blob,why):u.mem_write(a,blob);models.append(dict(address=a,bytes=len(blob),sha256=sha(blob),reason=why))
 def on_code(uc,a,n,_):
  nonlocal steps,low,msg_live,string_live,string_created,frees,endpoint,source52
  steps+=1;need(steps<=10000 and TOP-128<=sp()<=TOP and sp()%4==0,'caller stack/instruction bound');low=min(low,sp());lr=uc.reg_read(UC_ARM_REG_LR)
  while pending and a==int(pending[-1]['lr'],16)&~1:
   event=pending.pop();event.update(return_sp=sp(),return_saved=[reg(i) for i in range(4,12)],result_r0=reg(0));need(event['sp']==event['return_sp'] and event['saved']==event['return_saved'],'native preparation helper return ABI')
  if a==END:
   if variant=='wrong_ctor_lr':uc.reg_write(UC_ARM_REG_LR,lr+2);lr+=2
   need([reg(i) for i in range(3)]==[SETUP,1,11] and lr==0x2073445 and sp()==TOP-96 and uc.reg_read(UC_ARM_REG_CPSR)&32,'actual constructor entry ABI');endpoint=dict(pc=hex(a),regs=[reg(i) for i in range(13)],sp=sp(),lr=hex(lr),cpsr=uc.reg_read(UC_ARM_REG_CPSR));uc.emu_stop();return
  if a in SERVICES:
   need(uc.reg_read(UC_ARM_REG_CPSR)&32 and sp()%8==0,'caller model entry ABI');args=[reg(i) for i in range(4)];event=dict(name=SERVICES[a],pc=hex(a),args=args,sp=sp(),lr=hex(lr));services.append(event)
   if a==0x200BAF8:
    need(args==[1,27,729,11] and lr==0x20733D7 and not msg_live,'MsgData allocation ABI/lifetime');hostwrite(MSG,msg,'modeled MsgData allocation with opaque lazy NARC');msg_live=True;result=MSG
   elif a==0x2007508:
    need(args[:3]==[LOCAL,55,31] and lr==0x20733FD,'header reader native forward ABI');need(read(LOCAL+20,32)==stack_tail,'stack tail before header read');hostwrite(LOCAL,header[:-1] if variant=='short_header' else header,'modeled raw header20 read only');result=0xBAD00002
   elif a==0x200BBA0:
    need(args[:2]==[MSG,31] and lr==0x207342B and msg_live and read(MSG,12)==msg and not string_created,'packed name loader ABI/lifetime');output=B.pack_species_string(data['name']['expanded']) if variant=='expanded_name' else string;hostwrite(STRING,output,'modeled lazy raw packed String producer');string_created=string_live=True;result=STRING
   else:
    need(args[0]==STRING and lr==0x20263A1 and string_live and read(STRING+4,4)==struct.pack('<I',0xB6F8D2ED),'native String_Delete invalidation/free ABI');frees+=int(variant!='omit_free');string_live=variant=='omit_free';result=0xBAD00001
   event['result']=result;uc.reg_write(B.R[0],result);uc.reg_write(UC_ARM_REG_PC,lr);return
  need(code.get(a)==(n,bool(uc.reg_read(UC_ARM_REG_CPSR)&32)),'caller outside qualified code/ISA');seen.add(a)
  if a==0x2073404 and source52 is None:
   source52=read(LOCAL,52).hex()
   if variant=='skip_structure_copy':uc.reg_write(UC_ARM_REG_PC,0x2073411);return
  if a in (0x202A960,0x202A9A8,0x20735D8,0x2026A68,0x2026380,0x20E5AD8):
   if a==0x2026A68:
    if variant=='wrong_name_destination':uc.reg_write(B.R[1],SETUP+0x3C)
    if variant=='wrong_capacity':uc.reg_write(B.R[2],7)
    need([reg(i) for i in range(3)]==[STRING,NAME,8] and lr==0x2073435 and string_live,'native packed name copy ABI')
   if a==0x2026380 and variant=='skip_delete':uc.reg_write(UC_ARM_REG_PC,lr);return
   event=dict(pc=hex(a),args=[reg(i) for i in range(4)],sp=sp(),lr=hex(lr),saved=[reg(i) for i in range(4,12)]);native_calls.append(event);pending.append(event)
 def on_read(uc,access,a,n,value,_):
  allowed=inside(a,n,TOP-128,128) or inside(a,n,SETUP,0x200) or inside(a,n,TABLE,4) or string_live and inside(a,n,STRING,len(string)) or any(inside(a,n,x,size) for x,size,_ in POOLS+N.POOLS)
  need(allowed,'caller read outside owned stack/setup/save/string/pools')
 def on_write(uc,access,a,n,value,_):
  pc=uc.reg_read(UC_ARM_REG_PC);stack=inside(a,n,TOP-128,128);structure=pc in (0x2073406,0x207340E) and inside(a,n,TRAINER,52) and n==4;copied=pc==0x20E5AEC and inside(a,n,NAME,len(name)) and n==1;dead=pc==0x2026398 and a==STRING+4 and n==4 and value==0xB6F8D2ED
  need(stack or structure or copied or dead,'caller write outside native owned destination/stack')
  if structure:copy52.append(dict(pc=hex(pc),address=a,bytes=n,value=value))
  if observe and not stack:writes.append(dict(pc=hex(pc),address=a,bytes=n,value=value))
 u.hook_add(UC_HOOK_CODE,on_code);u.hook_add(UC_HOOK_MEM_READ,on_read);u.hook_add(UC_HOOK_MEM_WRITE,on_write);u.reg_write(UC_ARM_REG_CPSR,0x3F);u.reg_write(UC_ARM_REG_SP,TOP);u.reg_write(UC_ARM_REG_LR,N.STOP|1)
 for i,v in enumerate(N.COOKIES,4):u.reg_write(B.R[i],v)
 for i,v in enumerate((SETUP,SAVE,11,0x33333303)):u.reg_write(B.R[i],v)
 u.emu_start(ENTRY|1,N.STOP,count=10001);need(endpoint is not None,'actual constructor entry not reached');expected=bytearray(header+stack_tail);expected[20:20+len(name)]=name
 need(source52==header.hex()+stack_tail.hex() and read(LOCAL,52)==header+stack_tail,'native caller source52/header20/stack32 provenance');need(read(TRAINER,52)==bytes(expected),'native prepared Trainer52 mismatch');need(len(copy52)==13 and [e['address'] for e in copy52]==list(range(TRAINER,TRAINER+52,4)),'native copy52 store coverage');need(msg_live and string_created and not string_live and frees==1 and read(MSG,12)==msg,'endpoint Msg live/String freed lifetime');need(read(STRING,len(string))==string[:4]+struct.pack('<I',0xB6F8D2ED)+string[8:],'native String invalidation/payload');need(endpoint['regs'][4:8]==[SETUP+4,NAME,STRING,1] and endpoint['regs'][8:12]==list(N.COOKIES[4:]),'caller live registers at nested constructor entry')
 need(not pending,'all nested preparation helpers must return before constructor');after=bytes(u.mem_read(0x2000000,0x400000));masked=bytearray(after)
 for a,n in ((TOP-128,128),(TRAINER,52),(MSG,12),(STRING,len(string))):masked[a-0x2000000:a-0x2000000+n]=before[a-0x2000000:a-0x2000000+n]
 need(bytes(masked)==before,'caller unrelated RAM frozen');need([e['name'] for e in services]==['NewMsgDataFromNarc','ReadWholeNarcMemberByIdPair','NewString_ReadMsgData','Heap_Free'],'caller modeled service order');need(set(code)==seen,'complete finite caller instruction coverage')
 return dict(poison=poison,endpoint=endpoint,trainer_hex=read(TRAINER,52).hex(),local_source52=source52,initial_stack_tail_hex=stack_tail.hex(),services=services,models=models,native_calls=native_calls,copy52=copy52,observed_pcs=sorted(seen),writes=writes if observe else [],msg_live=msg_live,string_live=string_live,string_created=string_created,frees=frees,string_dead_sha256=sha(read(STRING,len(string))),functional_ram_sha256=sha(after),instructions=steps,stack_bytes=TOP-low,constructor_instruction_executed=False)

def functional(r):return {k:v for k,v in r.items() if k!='writes'}

def require_result(r,data,code):
 """Independently replay header/name provenance, ABI and native stores."""
 header=bytes.fromhex(data['header_hex']);words=data['name']['words'];payload=N.words_bytes(words);tail=bytes([r['poison']])*32;source=header+tail;expected=bytearray(source);expected[20:20+len(payload)]=payload;string=B.pack_species_string(words);msg=struct.pack('<HHHHI',1,11,27,729,OPAQUE_NARC)
 need(r['poison'] in (0xC7,0x39) and r['initial_stack_tail_hex']==tail.hex() and r['local_source52']==source.hex() and r['trainer_hex']==expected.hex(),'receipt raw20/stack32/native52/name provenance')
 endpoint=r['endpoint'];need(endpoint['pc']==hex(END) and endpoint['sp']==TOP-96 and endpoint['lr']=='0x2073445' and endpoint['cpsr']&32 and len(endpoint['regs'])==13 and endpoint['regs'][:3]==[SETUP,1,11] and endpoint['regs'][4:12]==[SETUP+4,NAME,STRING,1]+list(N.COOKIES[4:]),'receipt actual nested constructor entry ABI')
 need(r['constructor_instruction_executed'] is False and r['msg_live'] is True and r['string_created'] is True and r['string_live'] is False and r['frees']==1,'receipt endpoint scope and lifetime');need(r['string_dead_sha256']==sha(string[:4]+struct.pack('<I',0xB6F8D2ED)+string[8:]),'receipt native String invalidation')
 need(type(r['observed_pcs'])is list and len(r['observed_pcs'])==len(code) and set(r['observed_pcs'])==set(code) and 0<r['instructions']<=10000 and r['stack_bytes']==112,'receipt complete caller instruction coverage/bounds')
 expected_copy=[dict(pc='0x2073406' if i<12 else '0x207340e',address=TRAINER+4*i,bytes=4,value=v) for i,v in enumerate(struct.unpack('<13I',source))];need(r['copy52']==expected_copy,'receipt native 52-byte store provenance')
 expected_writes=expected_copy+[dict(pc='0x20e5aec',address=NAME+i,bytes=1,value=v if v<128 else v|0xFFFFFF00) for i,v in enumerate(payload)]+[dict(pc='0x2026398',address=STRING+4,bytes=4,value=0xB6F8D2ED)];need(r['writes']==expected_writes,'receipt native stores/order')
 models=[(MSG,msg,'modeled MsgData allocation with opaque lazy NARC'),(LOCAL,header,'modeled raw header20 read only'),(STRING,string,'modeled lazy raw packed String producer')];need(r['models']==[dict(address=a,bytes=len(blob),sha256=sha(blob),reason=reason) for a,blob,reason in models],'receipt exact modeled writes/source boundaries')
 services=r['services'];need(len(services)==4,'receipt four modeled services');specs=((0x200BAF8,[1,27,729,11],TOP-96,0x20733D7,MSG),(0x2007508,[LOCAL,55,31],TOP-96,0x20733FD,0xBAD00002),(0x200BBA0,[MSG,31],TOP-96,0x207342B,STRING),(0x201AB0C,[STRING],TOP-104,0x20263A1,0xBAD00001))
 for event,(pc,args,stack,lr,result) in zip(services,specs):need(event['name']==SERVICES[pc] and event['pc']==hex(pc) and event['args'][:len(args)]==args and event['sp']==stack and event['lr']==hex(lr) and event['result']==result,'receipt modeled service ABI/order')
 high=list(N.COOKIES[4:]);initial=[SAVE,N.COOKIES[1],N.COOKIES[2],N.COOKIES[3]]+high;body=[SETUP+4,NAME,STRING,1]+high
 specs=((0x202A960,[SAVE],TOP-96,0x20733DF,initial,MISC),(0x202A9A8,[MISC],TOP-96,0x20733E3,initial,MISC+0x270),(0x20735D8,[31,LOCAL],TOP-96,0x20733FD,[SETUP+4,NAME,N.COOKIES[2],1]+high,None),(0x2026A68,[STRING,NAME,8],TOP-96,0x2073435,body,None),(0x20E5AD8,[NAME,STRING+8,len(payload)],TOP-112,0x2026A99,[8,STRING+8,NAME,1]+high,NAME),(0x2026380,[STRING],TOP-96,0x207343B,body,None));calls=r['native_calls'];need(len(calls)==6,'receipt six native preparation calls')
 for event,(pc,args,stack,lr,saved,result) in zip(calls,specs):
  need(event['pc']==hex(pc) and event['args'][:len(args)]==args and event['sp']==event['return_sp']==stack and event['lr']==hex(lr) and event['saved']==event['return_saved']==saved,'receipt native helper ABI/order')
  if result is not None:need(event['result_r0']==result,'receipt native pointer-return helper')

def analyze(path,language):
 need(sys.flags.optimize==0,'run without Python -O');model=P.G.S.SHARED.read_current(path,language)
 with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:code,locations=qualify(model,raw);data=resources(raw)
 cases=[];counters=[]
 for poison in (0xC7,0x39):
  r=execute(model,code,data,poison=poison);require_result(r,data,code);off=execute(model,code,data,poison=poison,observe=False);need(functional(r)==functional(off),'caller OFF/ON differs');cases.append(dict(result=r,off_neutral=True))
 for variant in ('expanded_name','short_header','omit_free','skip_delete','skip_structure_copy','wrong_name_destination','wrong_capacity','wrong_ctor_lr'):
  try:execute(model,code,data,variant=variant)
  except ValueError as e:counters.append(dict(variant=variant,rejection=str(e)))
  else:raise ValueError('caller counter accepted: '+variant)
 return dict(schema='trainer31-caller-preparation-v1',language=language,input=model['record'],resources=data,locations=locations,qualified_code_pcs=len(code),cases=cases,counters=counters,source_sha256={str(Path(p).relative_to(P.SOURCE)):sha(Path(p).read_bytes()) for p in (__file__,N.__file__)},compiler_invoked=False,limits=['Stop at first constructor entry fetch; no constructor instruction or caller return executed','Raw NARC/header I/O, MsgData and raw packed String creation,Heap_Free are explicit models','MsgData/opaque lazy NARC remain live at endpoint; String invalidation native and Heap_Free modeled','Sparse SaveData table fixture is readonly,not an original save or save-system test','Fixed slot1 trainer31 ordinary path; no rival/multi-ID/final doubleBattle OR/natural encounter/UI claim'])

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','json'):parser.add_argument('--'+name,type=Path,required=True)
 parser.add_argument('--language',choices=('EN','IT'),required=True);a=parser.parse_args()
 try:
  need(not a.json.exists() and not a.json.is_symlink(),'output must be fresh');need(P.SOURCE not in a.json.resolve().parents and a.json.resolve()!=P.SOURCE,'output must be outside source');result=analyze(a.rom,a.language);blob=(json.dumps(result,indent=2)+'\n').encode();need(len(blob)<=2*1024*1024,'caller report budget');a.json.parent.mkdir(parents=True,exist_ok=True)
  with a.json.open('xb') as f:f.write(blob)
 except ValueError as e:parser.exit(2,str(e)+'\n')
 print(a.language,'native caller preparation verified up to constructor entry; caller has not returned')

if __name__=='__main__':main()
