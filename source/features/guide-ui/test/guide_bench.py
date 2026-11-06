"""Finite compiled Guide UI bench. Native service seams are declared by the
reused foundation benches; pure controller/planner execute real checked SGG1.
No ROM/save/assets are emitted. Temporary objects clean up with their context.
"""
import ctypes as C
import hashlib,importlib.util,json,os,struct,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE/'features/ui-native/test'))
sys.path.insert(0,str(SOURCE/'features/settings-ui/test'))
import guide_resource_bench as gb
from heap_bench import *
from bg_bench import object_details
STATE,INPUT,SAMPLE,PLAN,POOL,DIRTY,OLD=0x02350000,0x02350100,0x02350200,0x02351000,0x02352000,0x02353000,0x02354000
class View(C.LittleEndianStructure):
 _fields_=[(n,C.c_ushort) for n in ('depth','category','row','scroll','page')]
class State(C.LittleEndianStructure):
 _fields_=[('cursor',View),('back',View*8),('back_count',C.c_ushort)]+[(n,C.c_uint) for n in ('release_gate','sample_ready','touch_armed','touch_target','touch_down','notice')]
class Slice(C.LittleEndianStructure):
 _fields_=[(n,C.c_uint) for n in ('owner','offset','units','policy')]
class Op(C.LittleEndianStructure):
 _fields_=[('text',Slice)]+[(n,C.c_ubyte) for n in ('x','y','w','h','screen','kind','flags','color')]
class Plan(C.LittleEndianStructure):
 _fields_=[(n,C.c_uint) for n in ('magic','epoch','pool_epoch','pool_used','view','count','entry','page')]+[('ops',Op*32)]

def compile_ui(directory,stage='controller',red=False,extra=''):
 files=['ui-native/heap.c','ui-native/resource.c','ui-native/guide_resource.c','settings-ui/state.c','settings-ui/owners.c']
 if stage!='controller':files += ['ui-native/font.c','ui-native/bg.c','settings-ui/render.c','settings-ui/painter.c']
 content=''.join('#include "'+str(SOURCE/'features'/f)+'"\n' for f in files)
 if red and stage=='controller':
  content+='#include "'+str(SOURCE/'features/guide-ui/controller.h')+'"\nvoid guide_ui_init(GuideState *s){unsigned *p=(unsigned*)s;for(unsigned i=0;i<sizeof(*s)/4;++i)p[i]=0;s->release_gate=1;}\nunsigned guide_ui_step(GuideState*s,const UiGuideLease*l,unsigned c){(void)s;(void)l;(void)c;return 0;}\n'
 else:
  content+='#include "'+str(SOURCE/'features/guide-ui/controller.c')+'"\n'
  if stage!='controller':content+='#include "'+str(SOURCE/'features/guide-ui/render.c')+'"\n'
  if stage=='painter':
   if red:content+='#include "'+str(SOURCE/'features/guide-ui/painter.h')+'"\nunsigned guide_paint_init(GuidePainter*p,unsigned n,unsigned g){(void)p;(void)n;(void)g;return 0;}\n'
   else:content+='#include "'+str(SOURCE/'features/guide-ui/painter.c')+'"\n'
 content+=extra
 src=directory/'guide_unit.c';obj=directory/'guide.o';src.write_text(content)
 flags=FLAGS+['-std=c11','-fno-jump-tables','-fstack-usage']
 if red:flags+=['-Wno-unused-function']
 r=subprocess.run(['clang',*flags,'-c',str(src),'-o',str(obj)],capture_output=True,text=True)
 if r.returncode:raise AssertionError(r.stderr)
 spec=importlib.util.spec_from_file_location('guide_ui_loader',SOURCE/'features/options/tools/carica_text.py');loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
 compiled=loader.load_text(obj.read_bytes(),CODE)
 detail=object_details(obj.read_bytes(),compiled[0]);detail['stack_usage']=(directory/'guide.su').read_text();detail['flags']=flags
 return compiled,detail

def synthetic():
 cats=[]
 for ci,identity in enumerate((4,1,3,2)):
  entries=[dict(id=1+ci*10+i,title='A B',pages=[dict(lines=['C']*7,reference=(11 if ci==0 else 1)),dict(lines=['D'],reference=0)]) for i in range(8)]
  cats.append(dict(id=identity,title='CATEGORY',entries=entries))
 data=gb.guide_content.build_content(cats,lambda s:[1 if c==' ' else ord(c)-63 for c in s]+[65535],lambda s:len(s)*4)
 return data,gb.guide_content.read_content(data)
class ControllerBench(gb.GuideBench):
 def __init__(self,compiled,data=None):
  if data is None:data,_=synthetic()
  prior_cfg=gb.CFG;gb.CFG=0x0235e000
  try:
   super().__init__(compiled,data)
   self.allowed.extend(((STATE,STATE+116),(PLAN,PLAN+800),(POOL,POOL+1024),(DIRTY,DIRTY+12)))
   assert self.start()==gb.MORE and self.finish()==gb.READY
  finally:gb.CFG=prior_cfg
  assert self.call('ui_guide_acquire',self.reader,self.lease)==1
  self.call('guide_ui_init',STATE)
 def state(self):return State.from_buffer_copy(bytes(self.u.mem_read(STATE,116)))
 def set_state(self,s):self.u.mem_write(STATE,bytes(s))
 def action(self,key):return self.call('guide_ui_step',STATE,self.lease,key)
 def input(self,pressed=0,repeated=0,held=0,fresh=1,mapped=None,mode=0,x=0,y=0,down=0,busy=0,flags=0):
  self.u.mem_write(SAMPLE,struct.pack('<II4H',1,0,held,pressed,repeated,flags))
  self.u.mem_write(INPUT,struct.pack('<9I',SAMPLE,fresh,pressed if mapped is None else mapped,repeated,mode,x,y,down,busy))
  return self.call('guide_ui_input',STATE,self.lease,INPUT)

# Enlarged guarded SYS frame for the transactional800B plan+1024B staging pool.
# This test stack stays below the persistent heap token at0x027e3000.
import heap_bench as hb
import resource_bench as rb
from contextlib import contextmanager
SSTACK=0x027e2778
@contextmanager
def ui_stack():
 old=hb.STACK,gb.STACK,rb.STACK
 hb.STACK=gb.STACK=rb.STACK=SSTACK
 try:yield
 finally:hb.STACK,gb.STACK,rb.STACK=old

_old_hook=ControllerBench.hook
def _ui_address(self,p,*args):
 with ui_stack():
  seed=[0x44440000+i for i in range(8)]
  for r,v in zip(REGS,seed):self.u.reg_write(r,v)
  for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):self.u.reg_write(r,args[i] if i<len(args) else 0)
  self.u.mem_write(SSTACK,struct.pack('<8I',*(list(args[4:])+[0]*(8-len(args[4:])))))
  self.adapter_entry=True;self.u.reg_write(UC_ARM_REG_SP,SSTACK);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
  before=self.u.reg_read(UC_ARM_REG_CPSR)&0xdf;ime=self.get(IME);self.low=SSTACK;start=self.instructions
  self.u.mem_write(SSTACK-4096,b'\xa5'*64)
  self.u.emu_start(p,STOP,count=2500000)
  assert self.u.reg_read(UC_ARM_REG_PC)==STOP,'finite call'
  assert self.u.reg_read(UC_ARM_REG_SP)==SSTACK and [self.u.reg_read(r) for r in REGS]==seed
  assert self.u.reg_read(UC_ARM_REG_CPSR)&0xdf==before and self.get(IME)==ime
  assert bytes(self.u.mem_read(SSTACK-4096,64))==b'\xa5'*64
  self.metrics.append((p,SSTACK-self.low,self.instructions-start));return self.u.reg_read(UC_ARM_REG_R0)
def _ui_hook(self,u,p,n,d):
 self.low=min(self.low,u.reg_read(UC_ARM_REG_SP));assert SSTACK-4096<=self.low<=SSTACK
 if p==STOP:u.emu_stop();return
 if CODE<=p<CODE+len(self.code):self.instructions+=1;return
 if p in (rb.INIT,rb.OPEN,rb.READ,rb.CLOSE,rb.SEEK) and u.reg_read(UC_ARM_REG_R0)==rb.READER:
  return rb.ResourceBench.hook(self,u,p,n,d)
 return _old_hook(self,u,p,n,d)
def _ui_store(self,u,a,p,n,v,d):
 self.writes.append((p,n,v));assert any(lo<=p<p+n<=hi for lo,hi in self.allowed) or SSTACK-4096<=p<p+n<=SSTACK,f'unexpected UI store{p:08x}/{n}'
ControllerBench.address=_ui_address
ControllerBench.hook=_ui_hook
ControllerBench.store=_ui_store
UCFG,ULEASE,WIDTHS=0x0235f000,0x0235f100,0x0235f200
class RenderBench(ControllerBench):
 def __init__(self,compiled,data=None,uir=None):
  super().__init__(compiled,data)
  self.allowed.extend(((rb.READER,rb.READER+744),(ULEASE,ULEASE+12)))
  self.fs_fault=None;self.open_length=None;self.close_failures=0
  if uir is None:
   authored={e['id']:tuple(0xe000 if c=='\n' else ord(c)%400+1 for c in e['text']['EN'])+(65535,) for e in json.loads((SOURCE/'sgp131/data/ui-copy.json').read_text())['entries']}
   uir=rb.synthetic(authored=authored)+(bytes([4]*509),)
  self.raw,self.config,self.widths=uir
  self.u.mem_write(UCFG,self.config);self.u.mem_write(WIDTHS,self.widths)
  assert self.call('ui_res_init',rb.READER)==1
  assert self.call('ui_res_begin',rb.READER,UCFG,TOKEN)==rb.MORE
  for _ in range(100):
   result=self.call('ui_res_step',rb.READER)
   if result!=rb.MORE:break
  assert result==rb.OK,result
  assert self.call('ui_res_acquire',rb.READER,ULEASE,0)==1
  self.epoch=0
 def build(self,expect=1):
  self.epoch+=1
  before=bytes(self.u.mem_read(STATE,116));poison=bytes(self.u.mem_read(POOL,1024));out=bytes(self.u.mem_read(PLAN,800))
  result=self.call('guide_ui_build',STATE,self.lease,ULEASE,WIDTHS,PLAN,POOL,self.epoch)
  assert result==expect,(result,expect)
  assert bytes(self.u.mem_read(STATE,116))==before
  if not expect:assert bytes(self.u.mem_read(POOL,1024))==poison and bytes(self.u.mem_read(PLAN,800))==out
  return Plan.from_buffer_copy(bytes(self.u.mem_read(PLAN,800)))
 def dirty(self,previous,desired,upper=0,lower=0):
  if previous:self.u.mem_write(OLD,bytes(previous))
  self.u.mem_write(PLAN,bytes(desired))
  assert self.call('guide_ui_dirty',OLD if previous else 0,PLAN,upper,lower,DIRTY)==1
  return struct.unpack('<3I',bytes(self.u.mem_read(DIRTY,12)))

import painter_bench as pb
import font_bench as fb
from module_bench import instruction_set
GCTX,GDES,GSTATE,GREQ,GUIR,GBUF=pb.PCTX,pb.PDES,pb.PSTATE,pb.PREQ,pb.PUIR,pb.PBUF
GCFG=0x02352c00
class NativeGuidePainter(pb.NativePainterBench):
 """Actual pinned NNS/BG/Window/font decode/copy and native String reference.
 FS service/ROM transport, initial native scene globals, DMA/cache completion
 are prepared seams inherited from accepted benches. No Scene/Android proof.
 """
 def __init__(self,compiled,fixture,data):
  self.enforce=False;self.reference=False;self.font_fetch=set();self.font_calls=[];self.fs_calls=[]
  self.raw,self.config,self.widths,self.glyphs,self.native_sections=fixture
  with pb.bg_state():pb.nb.NativeBgBench.__init__(self,compiled,self.native_sections)
  # Native BG fixture seeds its old palette descriptor at02210000. Load the
  # larger combined payload AFTER that preparation, before any adapter call.
  self.u.mem_write(CODE,self.code)
  roots=(fb.RENDER|1,fb.GENERATE|1,0x02026069,0x020262b5,rb.CPSR,0x02026355,0x02026381,0x020269a1,0x02026aa5,0x020200fd,0x020204b9,0x02020549,0x0201aa8d,0x0201ab0d)
  self.font_fetch=instruction_set(self.u,roots,[(a,a+n) for a,n,d in pb.nf.FONT_PINS+pb.nh.PINS])
  self.paint_jobs=0;self.fs_fault=None;self.open_length=None;self.close_failures=0
  self.allowed.extend(((GCTX,GCTX+2552),(pb.PBG,pb.PBG+176),(GDES,GDES+800),(GSTATE,GSTATE+116),(GUIR,GUIR+20),(GBUF,GBUF+20),(GREQ,GREQ+40),(GCFG,GCFG+64),
   (rb.READER,rb.READER+744),(fb.FL,fb.FL+88),(fb.FM-32,fb.FM+0x800),*[(p,p+n) for p,n in ((fb.FFLAGS,2),(fb.COLORS,6),(fb.LOOKUP,512),(fb.WORK,130),(fb.WORK+0xb4,1),(0x021d1f6c,2))]))
  self.u.mem_write(UCFG,self.config);rb.ResourceBench.archive_fixture(self);assert self.create(0x40000)==1
  fb.FontBench.prepare_font(self);self.u.mem_write(fb.FW,self.widths)
  assert self.call('ui_res_init',rb.READER)==1
  assert self.call('ui_res_begin',rb.READER,UCFG,TOKEN)==rb.MORE
  for _ in range(200):
   result=self.call('ui_res_step',rb.READER)
   if result!=rb.MORE:break
  assert result==rb.OK and self.call('ui_font_acquire',fb.FL,rb.READER,0)==fb.F_READY
  self.root=self.get(rb.READER+rb.ROOT);self.root_bytes=len(self.raw)-35380
  self.app=self.alloc(4980);assert self.app
  self.reader=self.app+32;self.lease=self.app+352
  self.data=data;self.cfg=gb.config(data);self.short=False;self.open_fault=False
  self.u.mem_write(GCFG,self.cfg);self.put(rb.FAT+5*8,0x100000);self.put(rb.FAT+5*8+4,0x100000+100+len(data))
  assert self.call('ui_guide_init',self.reader)==1
  assert self.call('ui_guide_begin',self.reader,GCFG,TOKEN)==gb.MORE
  for _ in range(250):
   result=self.call('ui_guide_step',self.reader,4096)
   if result!=gb.MORE:break
  assert result==gb.READY,result
  assert self.call('ui_guide_acquire',self.reader,self.lease)==1
  self.pool=self.alloc(1024);assert self.pool
  assert self.call('ui_bg_create',TOKEN,pb.PBG,1)==1
  assert self.call('guide_paint_init',GCTX,2552,1)==1
  self.put(0x0210f6d8,0x020f56d8)
  self.u.mem_write(GUIR,struct.pack('<5I',1,self.root,self.root_bytes,self.get(rb.READER+rb.GEN),1))
  assert self.call('ui_bg_enter_backdrop',TOKEN,pb.PBG,1,GCTX+2520,0x564c)==1
  assert self.call('ui_bg_install_ball',TOKEN,pb.PBG,1,self.root+44896,3552)==1
  self.call('guide_ui_init',GSTATE);self.s=State();self.epoch=0;self.version=0;self.enforce=True
  assert bytes(self.u.mem_read(CODE,len(self.code)))==self.code,'whole compiled payload immutable after setup'
 def hook(self,u,p,n,d):
  if p in (gb.INIT,gb.FAST,gb.ASYNC,gb.CLOSE,gb.SEEK) and hasattr(self,'reader') and u.reg_read(UC_ARM_REG_R0)==self.reader:
   assert not self.enforce,'no Guide FS while painting';return gb.GuideBench.hook(self,u,p,n,d)
  if self.enforce and self.operation and self.operation.startswith('guide_paint'):
   assert p not in (CREATE,ALLOC,FREE,DESTROY,0x0201aa8c,0x0201ab0c),'no allocation while painting'
  return pb.NativePainterBench.hook(self,u,p,n,d)
 def store(self,u,a,p,n,v,d):
  if self.enforce and self.operation and self.operation.startswith('guide_paint'):
   for screen in (0,):
    pixelbase=128 if screen else 28;mapbase=120 if screen else 20
    front=self.get(pb.PBG+76);pending=self.get(pb.PBG+80);index=self.get(pb.PBG+88)
    for immutable in (front,pending):
     if immutable<2:
      for off,size in ((pixelbase,21120),(mapbase,2048)):
       root=self.get(pb.PBG+off+4*immutable);assert not (root<=p<root+size or p<root<p+n),'front/pending write'
    if index<2:
     root=self.get(pb.PBG+pixelbase+4*index)
     if root<=p<p+n<=root+21120:
      mask=self.get(GCTX+(28 if screen else 24));rows=range((p-root)//960,(p+n-1-root)//960+1)
      copy=self.symbols.get('ui_bg_begin_copy',0)&~1
      end=min((a&~1 for name,a in self.symbols.items() if not name.startswith('$') and a&~1>copy),default=copy)
      seeding=self.get(GCTX+12)==3 and self.get(GCTX+48)==2 and copy<=u.reg_read(UC_ARM_REG_PC)<end
      assert seeding or all(mask>>row&1 for row in rows),'write outside admitted Guide rows'
  return pb.NativePainterBench.store(self,u,a,p,n,v,d)
 def state(self):return State.from_buffer_copy(bytes(self.u.mem_read(GSTATE,116)))
 def action(self,key):return self.call('guide_ui_step',GSTATE,self.lease,key)
 def build(self):
  assert not self.get(fb.FL+84);self.epoch+=1
  assert self.call('guide_ui_build',GSTATE,self.lease,fb.FL+8,fb.FW,GDES,self.pool,self.epoch)==1
  self.u.mem_write(GBUF,struct.pack('<5I',3,self.pool,1024,self.epoch,1))
  return Plan.from_buffer_copy(bytes(self.u.mem_read(GDES,800)))
 def begin(self,index=None):
  if index is None:index=0 if self.get(pb.PBG+76)!=0 else 1
  self.version+=1;self.u.mem_write(GREQ,struct.pack('<10I',TOKEN,pb.PBG,fb.FL,self.lease,GDES,GUIR,GBUF,1,index,self.version))
  return self.call('guide_paint_begin',GCTX,GREQ)
 def finish_paint(self,index=None):
  result=self.begin(index)
  for _ in range(2000):
   if result!=1:break
   result=self.call('guide_paint_step',GCTX,8)
  assert result==2,(result,self.get(GCTX+12),self.get(GCTX+52))
  return result
 def pair_pixels(self,index):
  return (bytes(self.u.mem_read(self.get(pb.PBG+28+4*index),21120)),
          bytes(self.u.mem_read(0x06200000,1472))+bytes(self.u.mem_read(0x0620f000,2048))+bytes(self.u.mem_read(0x05000400,32)))

def independent_scene(b):
 """Model+accepted SGG content → complete canvases/native text runs. No plan,
 production planner, dirty closure, painter/history or restricted font jobs.
 Geometric shapes use explicit independent point sets at native resolution.
 """
 state=b.state();v=state.cursor;graph=gb.guide_content.read_content(b.data)
 c=graph[v.category];entry=c['entries'][v.row] if v.depth else None
 count=b.get(b.root+100);directory=struct.iter_unpack('<HHI',bytes(b.u.mem_read(b.root+48448,count*8)))
 text={i:struct.unpack('<%dH'%n,bytes(b.u.mem_read(b.root+off,2*n))) for i,n,off in directory}
 alpha=text[130];space=alpha[13];width=lambda words:sum(b.widths[g-1] for g in words if g!=65535)
 canvases=[bytearray(21120),bytearray(21120)];runs=[]
 canvas=canvases[0]
 pb.reference_rect(canvas,0,0,240,176,3)
 pb.reference_rect(canvas,0,0,1,176,2);pb.reference_rect(canvas,239,0,1,176,2)
 pb.reference_rect(canvas,4,32,232,112,1)
 pb.reference_rect(canvas,4,144,232,32,2)
 if v.depth<2:
  pb.reference_rect(canvas,4,36,232,100,3)
  for y in (55,75,95,115,135):pb.reference_rect(canvas,6,y,228,1,11)
 title=text[134] if not v.depth else c['title'] if v.depth==1 else entry['title']
 titles=[title]
 if width(title)>160:
  permitted=[i for i in range(1,len(title)) if width(title[:i])<=160]
  last=max(permitted);spaces=[i for i in permitted if title[i-1]==space]
  split=max(spaces) if spaces else last;titles=[title[:split]+(65535,),title[split:]]
 for row,words in enumerate(titles):runs.append((0,words,8,row*16,(10,3)))
 def counter(a,total,screen):
  words=tuple(alpha[int(c)] if c.isdigit() else alpha[10] for c in f'{a}/{total}')+(65535,)
  runs.append((screen,words,232-width(words),12 if screen else 0,(2,13) if screen else (10,3)))
 pos=v.page+1 if v.depth==2 else v.row+1 if v.depth else v.category+1
 total=len(entry['pages']) if v.depth==2 else len(c['entries']) if v.depth else len(graph)
 counter(pos,total,0)
 if v.depth==2:
  for row,words in enumerate(entry['pages'][v.page]['lines']):runs.append((0,words,16,32+16*row,(2,1)))
 else:
  source=c['entries'] if v.depth else graph;selected=v.row if v.depth else v.category
  first=v.scroll if v.depth else 0
  for slot,item in enumerate(source[first:first+5]):
   chosen=first+slot==selected;y=36+20*slot
   if chosen:
    pb.reference_rect(canvases[0],4,y,232,20,1,8)
    points=((0,),(0,1),(0,1,2),(0,1,2,3),(0,1,2),(0,1),(0,))
    for yy,row in enumerate(points):
     for xx in row:pb.pixel_set(canvases[0],9+xx,y+8+yy,2)
   runs.append((0,item['title'],16,y+4,(2,1) if chosen else (10,3)))
 footer=text[127];slash=footer.index(alpha[10]);keyleft,keyright=footer[slash-1],footer[slash+1]
 if v.depth==2:
  ids=(139,140,141,136)
  enabled=(v.page>0,v.page+1<len(entry['pages']),bool(entry['pages'][v.page]['reference']) and state.back_count<8,True)
  keys=((keyleft,),(keyright,),(alpha[-5],),(alpha[-4],))
 else:
  row=v.row if v.depth else v.category;n=len(c['entries']) if v.depth else len(graph)
  ids=(143,144,135,136 if v.depth else 142)
  enabled=(n>1,bool(v.depth) and n>5,True,True)
  keys=((0x11c,0x11d),(keyleft,alpha[10],keyright),(alpha[-5],),(alpha[-4],))
 for slot,(identity,key,active) in enumerate(zip(ids,keys,enabled)):
  x=120 if slot%2 else 8;y=144 if slot<2 else 160;fg=10 if active else 5
  runs.append((0,key+(65535,),x,y,(fg,2)))
  runs.append((0,text[identity],x+28,y,(fg,2)))
 return canvases,runs

def native_pair_reference(b,index):
 before=b.snapshot();globals_before=b.globals();b.reference=True
 topology=pb.nf.NativeFontBench.topology;heap=b.get(TOKEN+16)
 allocbefore=topology(b,heap),b.get(b.counts+76,2)
 try:
  canvases,runs=independent_scene(b)
  assert b.call('ui_bg_begin',TOKEN,pb.PBG,1,index)
  upper=pb.PBG+36+16*index
  b.u.mem_write(b.get(upper+12),bytes(canvases[0]))
  for screen,words,x,y,colors in runs:
   assert screen==0
   b.reference_text(upper,words,x,y,colors)
  # Final visual contract: uninterrupted list contours, preserving native ink.
  # Derive the selected row from the model, not painter operations or history.
  v=b.state().cursor
  if v.depth<2:
   canvas=bytearray(b.u.mem_read(b.get(upper+12),21120))
   selected=v.category if not v.depth else v.row-v.scroll
   for row,y in enumerate((55,75,95,115,135)):
    chosen=row==selected
    for x in range(4 if chosen else 6,236 if chosen else 234):
     offset=(y//8*30+x//8)*32+y%8*4+x%8//2
     ink=canvas[offset]>>(4*(x%2))&15
     if ink not in (2,5,10):pb.pixel_set(canvas,x,y,8 if chosen else 11)
   b.u.mem_write(b.get(upper+12),bytes(canvas))
  assert b.call('ui_bg_unframed',TOKEN,pb.PBG,1)==1
  for screen in (0,):
   for row in range(22):
    b.u.mem_write(GREQ,struct.pack('<2I',row,1));assert b.call('ui_bg_lower_rows' if screen else 'ui_bg_rows',TOKEN,pb.PBG,1,GREQ)==1
  assert b.call('ui_bg_ready',TOKEN,pb.PBG,1,max(b.get(pb.PBG+68),b.get(pb.PBG+72))+1)==1
  result=b.pair_pixels(index)
  assert (topology(b,heap),b.get(b.counts+76,2))==allocbefore,'native reference allocation topology restored'
 finally:b.reference=False;b.restore(before)
 assert b.globals()==globals_before,'font globals restored by synchronous reference'
 return result

def native_pair_image(b,index,path):
 """Independent map/tile/palette readback after actual paired publication.
 This prepared native CPU fixture is not a game/Android screen capture.
 """
 from PIL import Image
 image=Image.new('RGB',(256,400),(0,0,0))
 for screen,(vram,palette) in enumerate(((0x06000000,0x05000000),(0x06200000,0x05000400))):
  mapping=struct.unpack('<1024H',b.u.mem_read(vram+0xf000+(index*2048 if screen==0 else 0),2048))
  chars=bytes(b.u.mem_read(vram+(index*0x10000 if screen==0 else 0),0x8000));pal=struct.unpack('<256H',b.u.mem_read(palette,512))
  for y in range(192):
   for x in range(256):
    entry=mapping[y//8*32+x//8];xx=x%8;yy=y%8
    if entry&1024:xx=7-xx
    if entry&2048:yy=7-yy
    value=(chars[(entry&1023)*32+yy*4+xx//2]>>(4*(xx%2)))&15
    rgb=pal[(entry>>12)*16+value if value else 0]&32767
    image.putpixel((x,y+screen*208),tuple((rgb>>shift&31)*255//31 for shift in (0,5,10)))
 image.save(path)
