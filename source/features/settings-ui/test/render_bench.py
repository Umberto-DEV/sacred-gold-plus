"""Real freestanding Thumb planner; synthetic Class A text is not native proof."""
import ctypes as C
import importlib.util
from pathlib import Path
import struct, subprocess, tempfile, hashlib, sys
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
SOURCE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).parent))
from test_state import State,Snapshot
CODE,STOP,STACK=0x02200000,0x021fff00,0x027e3ff8
STATE,CAT,REQ,OUT,POOL,DATA,WIDTHS,PREVIOUS,FULL=0x02300000,0x02301000,0x02301100,0x02302000,0x02303000,0x02310000,0x02308000,0x02305000,0x02307000
FLAGS=['--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-Oz','-std=c11','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-jump-tables','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror']
class Op(C.LittleEndianStructure):
 _fields_=[('a',C.c_uint),('b',C.c_uint)]+[(n,C.c_ushort) for n in ('id','offset','units','flags')]+[(n,C.c_ubyte) for n in ('x','y','w','h','kind','row','choice','reserved')]
class Plan(C.LittleEndianStructure):
 _fields_=[(n,C.c_uint) for n in ('magic','identity','pool_epoch','pool_used','view','first','count','frame')]+[('ops',Op*48)]
def compile_render(directory):
 src=directory/'unit.c';obj=directory/'render.o'
 src.write_text('#include "state.c"\n#include "render.c"\n')
 cp=subprocess.run(['clang',*FLAGS,'-I',str(SOURCE/'features/settings-ui'),'-fstack-usage','-c',str(src),'-o',str(obj)],capture_output=True,text=True)
 if cp.returncode:raise AssertionError(cp.stderr)
 spec=importlib.util.spec_from_file_location('render_loader',SOURCE/'features/options/tools/carica_text.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod.load_text(obj.read_bytes(),CODE)
def synthetic():
 # Unique short native glyph sequences, explicit alphabet contract.
 words={i:(1+(i%200),65535) for i in range(1,134)}
 words[130]=tuple(range(300,318))+(65535,)
 import json
 catalogue=json.loads((SOURCE/'sgp131/data/ui-copy.json').read_text())
 for e in catalogue['entries']:
  if e['name'].startswith('FOOTER_'):
   words[e['id']]=tuple(313 if c==' ' else 314+'ABXY'.index(c) if c in 'ABXY' else 1+ord(c)%200 for c in e['text']['EN'])+(65535,)
 words.update({4096+i:(100,101,102,65535) for i in range(1,494)})
 return words,bytes([4]*509)
class RenderBench:
 def __init__(self,compiled,fixture=None):
  self.code,self.symbols=compiled;self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
  for p,n in ((0x02000000,0x400000),(0x027e0000,0x4000)):self.u.mem_map(p,n)
  self.u.mem_write(CODE,self.code);self.u.reg_write(UC_ARM_REG_CPSR,0x5f)
  self.allowed=[];self.metrics=[];self.writes=[];self.low=STACK;self.steps=0
  self.entries={v&~1 for k,v in self.symbols.items() if k.startswith('settings_')}
  self.u.hook_add(UC_HOOK_CODE,self.hook);self.u.hook_add(UC_HOOK_MEM_WRITE,self.write)
  self.words,self.widths=fixture or synthetic();directory=bytearray();payload=bytearray()
  offset=len(self.words)*8
  for id,words in sorted(self.words.items()):
   directory+=struct.pack('<HHI',id,len(words),offset+len(payload));payload+=struct.pack('<%dH'%len(words),*words)
  self.data=bytes(directory+payload);self.u.mem_write(DATA,self.data);self.u.mem_write(WIDTHS,self.widths)
  self.u.mem_write(CAT,struct.pack('<7I',DATA,len(self.data),0,len(self.words),WIDTHS,509,7))
  self.u.mem_write(REQ,struct.pack('<10I',STATE,CAT,OUT,C.sizeof(Plan),POOL,4096,9,0,0,0xffffffff))
  self.s=State();self.s.snapshot.editable_rows=16383;self.s.snapshot.shiny.available=1
  self.s.snapshot.shiny.mode=self.s.draft.shiny.mode=1
  self.s.snapshot.shiny.target=self.s.draft.shiny.target=493
  self.s.snapshot.shiny.denominator=4096;self.s.snapshot.shiny.charge=40
  self.s.snapshot.shiny.method_mask=21
  for m in (0,2,4):
   self.s.snapshot.shiny.counts[m]=2;self.s.snapshot.candidates[m][0]=25;self.s.snapshot.candidates[m][1]=493
 def put(self,p,v,n=4):self.u.mem_write(p,int(v).to_bytes(n,'little'))
 def get(self,p,n=4):return int.from_bytes(self.u.mem_read(p,n),'little')
 def write(self,u,a,p,n,v,d):
  self.writes.append((p,n));assert any(lo<=p<p+n<=hi for lo,hi in self.allowed) or STACK-4096<=p<p+n<=STACK,hex(p)
 def hook(self,u,p,n,d):
  self.steps+=1;self.low=min(self.low,u.reg_read(UC_ARM_REG_SP))
  assert STACK-4096<=self.low<=STACK
  if p==STOP:u.emu_stop();return
  assert CODE<=p<CODE+len(self.code),hex(p)
  if p in self.entries:assert u.reg_read(UC_ARM_REG_SP)%8==0,'public ABI stack alignment'
 def call(self,name,*args):
  regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
  seed=list(range(0x11220000,0x11220008))
  for reg,v in zip(regs,seed):self.u.reg_write(reg,v)
  for i,reg in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):self.u.reg_write(reg,args[i] if i<len(args) else 0)
  self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP|1);self.steps=0;self.low=STACK
  self.u.mem_write(STACK-4096,b'\xa5'*64)
  self.u.emu_start(self.symbols[name],STOP,count=2000000)
  assert self.u.reg_read(UC_ARM_REG_PC)==STOP,'finite budget'
  assert self.u.reg_read(UC_ARM_REG_SP)==STACK
  assert bytes(self.u.mem_read(STACK-4096,64))==b'\xa5'*64
  assert [self.u.reg_read(r) for r in regs]==seed
  self.metrics.append((name,self.steps,STACK-self.low));return self.u.reg_read(UC_ARM_REG_R0)
 def build(self,expect=1):
  self.u.mem_write(STATE,bytes(self.s));before=bytes(self.u.mem_read(STATE,C.sizeof(State)))
  self.allowed=[(OUT,OUT+C.sizeof(Plan)),(POOL,POOL+4096)]
  result=self.call('settings_render_build',REQ)
  assert result==expect,(result,expect,self.s.view,self.s.row)
  assert bytes(self.u.mem_read(STATE,C.sizeof(State)))==before
  return Plan.from_buffer_copy(bytes(self.u.mem_read(OUT,C.sizeof(Plan))))
 def dirty(self,previous,desired,invalid=0):
  if previous:self.u.mem_write(PREVIOUS,bytes(previous))
  self.u.mem_write(OUT,bytes(desired));self.allowed=[(FULL,FULL+4)]
  mask=self.call('settings_render_dirty',PREVIOUS if previous else 0,OUT,invalid,FULL)
  return mask,self.get(FULL)
def ops(plan,kind=None):return [o for o in plan.ops[:plan.count] if kind is None or o.kind==kind]

def receipt(directory):
 code,symbols=compile_render(directory);obj=(directory/'render.o').read_bytes()
 header=struct.unpack_from('<HHIIIIIHHHHHH',obj,16)
 sections=[struct.unpack_from('<10I',obj,header[5]+i*header[10]) for i in range(header[11])]
 def content(s):return obj[s[4]:s[4]+s[5]]
 def name(table,index):return table[index:table.index(b'\0',index)].decode()
 names=content(sections[header[12]]);labels=[name(names,s[0]) for s in sections];text_index=labels.index('.text')
 undefined=[];relocations={};allocated=[];functions={}
 for label,section in zip(labels,sections):
  if section[2]&2 and section[5]:allocated.append((label,section[5]))
  if section[1]==2:
   strings=content(sections[section[6]])
   for index,value,size,info,other,si in struct.iter_unpack('<IIIBBH',content(section)):
    label=name(strings,index)
    if label and not si and info&0xf0:undefined.append(label)
    if si==text_index and info&15==2:functions[label]=size
  if section[1]==9 and section[7]==text_index:
   for offset,info in struct.iter_unpack('<II',content(section)):relocations[info&255]=relocations.get(info&255,0)+1
 pins={str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
       [SOURCE/'features/settings-ui'/f for f in ('state.c','controller.h','catalog.h','render.h','render.c')]+[SOURCE/'features/options/tools/carica_text.py']}
 return dict(flags=FLAGS,compiler=subprocess.check_output(['clang','--version'],text=True).strip(),text_bytes=len(code),
  object_sha256=hashlib.sha256(obj).hexdigest(),payload_sha256=hashlib.sha256(code).hexdigest(),
  plan_bytes=C.sizeof(Plan),op_bytes=C.sizeof(Op),source_pins=pins,undefined=undefined,allocated_sections=allocated,
  relocations=relocations,function_bytes=functions,stack_usage=(directory/'render.su').read_text().strip())
if __name__=='__main__':
 import json
 with tempfile.TemporaryDirectory(prefix='settings-render-receipt-') as d:print(json.dumps(receipt(Path(d)),indent=2))
