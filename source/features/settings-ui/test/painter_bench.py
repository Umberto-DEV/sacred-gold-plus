"""Actual compiled complete Settings pixel TU. Test addresses assign no placement.
Class A native boundaries are declared seams; Class B executes pinned native
NNS/BG/font. No files from a cartridge are extracted or made public.
"""
import ctypes as C
import importlib.util,struct,subprocess,tempfile,hashlib,sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE/'features/ui-native/test'))
sys.path.insert(0,str(HERE))
import bg_bench as bb
import test_bg_rom as nb
import font_bench as fb
import resource_bench as rb
import heap_bench as hb
import test_heap_rom as nh
import test_font_rom as nf
from heap_bench import *
from render_bench import Plan,Op,State,ops,synthetic as render_synthetic
from bg_bench import object_details,check_compiled
from contextlib import contextmanager
STACK=0x027e2778 # Below token3000: render build uses1880B, no ledger overlap.
P_SIZE=3320
PCTX,PBG,PCAT,PDES,PUIR,PBUF,PREQ,PSREQ,PSTATE=0x02350000,0x0234d000,0x02352000,0x02352200,0x02352700,0x02352720,0x02352800,0x02352900,0x02352a00
REFUSE,MORE,PREPARED,UNCHANGED,FAILED,HOLD=range(6)
FULL=0x3fffff
PALETTE=(0,0x7bdf,0x2508,0x51a4,0x6f19,0x45ac,0x56b5,0x35ad,0x1cbb,0x63b8,0x7fff,0x564c,0x3adf,0x6b7a,0x28f6,0x5ef5)
@contextmanager
def bg_state():
 old=bb.STATE,nb.STATE
 modules=(bb,nb,fb,rb,hb,nh,nf);stacks=[m.STACK for m in modules]
 bb.STATE=nb.STATE=PBG
 for m in modules:m.STACK=STACK
 try:yield
 finally:
  bb.STATE,nb.STATE=old
  for m,v in zip(modules,stacks):m.STACK=v

def compile_painter(directory,mutation=None):
 content=(SOURCE/'features/settings-ui/painter.c').read_text()
 if mutation:
  a,b=mutation;assert content.count(a)==1,(a,content.count(a));content=content.replace(a,b,1)
 src=directory/'painter_unit.c';obj=directory/'painter.o'
 src.write_text(''.join('#include "'+s+'"\n' for s in ('heap.c','resource.c','font.c','bg.c','state.c','render.c'))+content)
 flags=FLAGS+['-std=c11','-fno-jump-tables','-fstack-usage']
 cp=subprocess.run(['clang',*flags,'-I',str(SOURCE/'features/ui-native'),'-I',str(SOURCE/'features/settings-ui'),'-c',str(src),'-o',str(obj)],capture_output=True,text=True)
 if cp.returncode:raise AssertionError(cp.stderr)
 spec=importlib.util.spec_from_file_location('painter_loader',SOURCE/'features/options/tools/carica_text.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 compiled=m.load_text(obj.read_bytes(),CODE);detail=object_details(obj.read_bytes(),compiled[0]);detail['stack_usage']=(directory/'painter_unit.su').read_text() if (directory/'painter_unit.su').is_file() else (directory/'painter.su').read_text()
 detail['flags']=flags;detail['compiler']=subprocess.check_output(['clang','--version'],text=True).strip()
 detail['allocated_sections']=allocated_sections(obj.read_bytes())
 return compiled,detail

def allocated_sections(obj):
 h=struct.unpack_from('<HHIIIIIHHHHHH',obj,16);s=[struct.unpack_from('<10I',obj,h[5]+i*h[10]) for i in range(h[11])];names=obj[s[h[12]][4]:s[h[12]][4]+s[h[12]][5]]
 return [(names[t[0]:names.index(b'\0',t[0])].decode(),t[5]) for t in s if t[2]&2 and t[5]]

class PainterAPI:
 def address(self,p,*args):
  with bg_state():
   seed=[0x44440000+i for i in range(8)]
   for r,v in zip(REGS,seed):self.u.reg_write(r,v)
   for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):self.u.reg_write(r,args[i] if i<len(args) else 0)
   self.u.mem_write(STACK,struct.pack('<8I',*(list(args[4:])+[0]*(8-len(args[4:])))))
   self.adapter_entry=CODE<=p<CODE+len(self.code)
   self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
   before=self.u.reg_read(UC_ARM_REG_CPSR)&0xdf;ime=self.get(IME);start=self.instructions;self.low=STACK
   self.u.mem_write(STACK-4096,b'\xa5'*64)
   self.u.emu_start(p,STOP,count=2500000)
   assert self.u.reg_read(UC_ARM_REG_PC)==STOP,'finite invocation'
   assert self.u.reg_read(UC_ARM_REG_SP)==STACK and [self.u.reg_read(r) for r in REGS]==seed,'EABI registers/stack'
   assert self.u.reg_read(UC_ARM_REG_CPSR)&0xdf==before and self.get(IME)==ime,'IRQ/IME restore'
   assert bytes(self.u.mem_read(STACK-4096,64))==b'\xa5'*64,'stack canary'
   self.metrics.append((p,STACK-self.low,self.instructions-start));return self.u.reg_read(UC_ARM_REG_R0)
 def call(self,name,*args):
  old=getattr(self,'operation',None),getattr(self,'operation_args',())
  self.operation,self.operation_args=name,args
  try:return self.address(self.symbols[name],*args)
  finally:self.operation,self.operation_args=old
 def init_painter(self):return self.call('settings_paint_init',PCTX,P_SIZE,1)
 def setup(self,raw,config,widths):
  self.raw,self.config,self.widths=raw,config,widths;self.paint_jobs=0;self.font_calls=[];self.fs_calls=[];self.fs_fault=None;self.close_failures=0;self.open_length=None
  self.allowed.extend(((PCTX,PCTX+P_SIZE),(PBG,PBG+176),(PCAT,PCAT+28),(PDES,PDES+1184),(PUIR,PUIR+20),(PBUF,PBUF+20),(PREQ,PREQ+40),(PSREQ,PSREQ+40),(PSTATE,PSTATE+224),
    (rb.READER,rb.READER+744),(fb.FL,fb.FL+88),(fb.FM-32,fb.FM+0x800),*[(p,p+n) for p,n in ((fb.FFLAGS,2),(fb.COLORS,6),(fb.LOOKUP,512),(fb.WORK,130),(fb.WORK+0xb4,1))]))
  self.u.mem_write(rb.CONFIG,config);rb.ResourceBench.archive_fixture(self)
  assert self.create()==1
  fb.FontBench.prepare_font(self)
  self.u.mem_write(fb.FW,widths)
  assert rb.ResourceBench.start(self)==rb.MORE
  for _ in range(200):
   value=self.call('ui_res_step',rb.READER)
   if value!=rb.MORE:break
  assert value==rb.OK,value
  assert self.call('ui_font_acquire',fb.FL,rb.READER,0)==fb.F_READY
  self.pool=self.alloc(256);assert self.pool
  assert self.call('ui_bg_create',TOKEN,PBG,1)==1
  assert self.init_painter()==1
  self.root=self.get(rb.READER+rb.ROOT);self.root_bytes=len(raw)-35380
  self.u.mem_write(PCAT,struct.pack('<7I',self.root,self.root_bytes,48448,self.get(self.root+100),fb.FW,509,7))
  self.u.mem_write(PUIR,struct.pack('<5I',1,self.root,self.root_bytes,self.get(rb.READER+rb.GEN),1))
  self.epoch=0;self.s=State();self.s.snapshot.editable_rows=16383;self.s.snapshot.shiny.available=1
  self.s.snapshot.shiny.mode=self.s.draft.shiny.mode=1;self.s.snapshot.shiny.target=self.s.draft.shiny.target=493
  self.s.snapshot.shiny.denominator=4096;self.s.snapshot.shiny.charge=40;self.s.snapshot.shiny.method_mask=21
  for m in (0,2,4):self.s.snapshot.shiny.counts[m]=2;self.s.snapshot.candidates[m][0]=25;self.s.snapshot.candidates[m][1]=493
  self.version=0;self.preparing_test=False;self.enforce=True
 def build(self,first=0,prefix=0xffffffff):
  assert not self.get(fb.FL+84),'pool cannot change under active job'
  self.epoch+=1;self.u.mem_write(PSTATE,bytes(self.s))
  self.u.mem_write(PSREQ,struct.pack('<10I',PSTATE,PCAT,PDES,1184,self.pool,256,self.epoch,first,0,prefix))
  assert self.call('settings_render_build',PSREQ)==1
  self.u.mem_write(PBUF,struct.pack('<5I',3,self.pool,256,self.epoch,1))
  return Plan.from_buffer_copy(bytes(self.u.mem_read(PDES,1184)))
 def begin(self,index=None):
  if index is None:index=0 if self.get(PBG+76)!=0 else 1
  self.version+=1;self.u.mem_write(PREQ,struct.pack('<10I',TOKEN,PBG,fb.FL,PCAT,PDES,PUIR,PBUF,1,index,self.version))
  return self.call('settings_paint_begin',PCTX,PREQ)
 def step(self,budget=8):
  phase=self.get(PCTX+12);result=self.call('settings_paint_step',PCTX,budget)
  if phase==5 and self.get(PCTX+12)==6:self.paint_jobs+=1
  return result
 def finish_paint(self,index=None):
  result=self.begin(index);assert result in (MORE,UNCHANGED),result
  for _ in range(1800):
   if result!=MORE:break
   result=self.step()
  assert result in (PREPARED,UNCHANGED),(result,self.get(PCTX+12),self.get(PCTX+56))
  return result
 def publish(self):
  self.put(0x04000006,192,2);assert self.call('ui_bg_publish',PBG,1,240)==1
 def pixels(self,index=None):
  if index is None:index=self.get(PBG+88) if self.get(PBG+88)<2 else self.get(PBG+80)
  return bytes(self.u.mem_read(self.get(PBG+28+4*index),21120))
 def globals(self):return tuple(bytes(self.u.mem_read(p,n)) for p,n in ((fb.FFLAGS,2),(fb.COLORS,6),(fb.LOOKUP,512),(fb.WORK,130)))

class PainterBench(PainterAPI,bb.BgBench):
 """Class A heap/FS/BG/font service seams; real painter/render/owners checked."""
 def __init__(self,compiled):
  self.alloc_next=0;self.operation=None;self.operation_args=();self.enforce=False
  bb.BgBench.__init__(self,compiled)
  authored,_=render_synthetic();authored={k:v for k,v in authored.items() if k<4096}
  raw,config=rb.synthetic(authored=authored)
  self.setup(raw,config,fb.synthetic_widths())
  with bg_state():self.prepared_display()
  self.u.mem_write(0x050001a0,struct.pack('<16H',*PALETTE))
 def store(self,u,access,p,n,v,data):
  assert any(a<=p<p+n<=b for a,b in self.allowed) or STACK-4096<=p<p+n<=STACK,f'unexpected store {p:08x}/{n}'
  self.writes.append((p,n,v))
  if getattr(self,'enforce',False) and self.operation and self.operation.startswith('settings_paint'):
   i=self.get(PBG+88)
   if i<2:
    root=self.get(PBG+28+4*i)
    if root<=p<p+n<=root+21120:
     copy=self.symbols.get('ui_bg_begin_copy',0)&~1
     end=min((a&~1 for name,a in self.symbols.items() if not name.startswith('$') and a&~1>copy),default=copy)
     seeding=self.get(PCTX+12)==3 and self.get(PCTX+60)&2 and copy<=u.reg_read(UC_ARM_REG_PC)<end
     rows=set(range((p-root)//960,(p+n-1-root)//960+1));assert seeding or all(self.get(PCTX+28)>>r&1 for r in rows),'write outside admitted rows'
   front=self.get(PBG+76)
   if front<2:
    for a,z in ((self.get(PBG+28+front*4),21120),(self.get(PBG+20+front*4),2048)):
     assert not (p<a+z and a<p+n),'front write'
 def hook(self,u,p,n,data):
  check_compiled(self.code,p,n);self.instructions+=1;self.low=min(self.low,u.reg_read(UC_ARM_REG_SP));assert STACK-4096<=self.low<=STACK
  if p==STOP:self.u.emu_stop();return
  if p==rb.CPSR:self.ret(u.reg_read(UC_ARM_REG_CPSR)&128);return
  if p in (rb.INIT,rb.OPEN,rb.READ,rb.CLOSE,rb.SEEK):
   assert not getattr(self,'enforce',False),'no FS during painter'
   rb.ResourceBench.hook(self,u,p,n,data);return
  if p==ALLOC and self.get(TOKEN+16)==u.reg_read(UC_ARM_REG_R0):
   assert not getattr(self,'preparing_test',False),'no per-frame allocation'
   size=u.reg_read(UC_ARM_REG_R1);raw=self.get(TOKEN+16)+0x100+self.alloc_next;self.alloc_next+=(size+35)&~3
   self.put(raw-16,0x5544,2);self.put(raw-12,(size+3)&~3);self.ret(raw);return
  if p in (fb.GENERATE,fb.RENDER):
   self.font_calls.append(p)
   assert u.reg_read(UC_ARM_REG_CPSR)&128
   if p==fb.GENERATE:self.ret();return
   j=u.reg_read(UC_ARM_REG_R0);pos=self.get(j);x=self.get(j+12,2);y=self.get(j+14,2)
   while True:
    c=self.get(pos,2);pos+=2
    if c!=0xe000:break
    x=self.get(j+10,1);y+=16
   if c!=65535:
    w=self.widths[c-1];window=self.get(j+4);pixels=self.get(window+12)
    for yy in range(y,y+16):
     for xx in range(x,x+w):
      color=self.get(j+21,1) if (xx+yy+c)%3 else self.get(j+22,1)
      off=((yy//8)*30+xx//8)*32+(yy%8)*4+(xx%8)//2;addr=pixels+off;old=self.get(addr,1);shift=(xx&1)*4
      self.store(u,0,addr,1,(old&~(15<<shift))|(color<<shift),None);self.put(addr,(old&~(15<<shift))|(color<<shift),1)
    x+=w
   self.put(j,pos);self.put(j+12,x,2);self.put(j+14,y,2);self.ret(int(c==65535));return
  # BG row transport only; production BG validation/row accounting is real.
  if p==0x0201c0c0:
   src=u.reg_read(UC_ARM_REG_R2);count=u.reg_read(UC_ARM_REG_R3);i=u.reg_read(UC_ARM_REG_R1)-1;tile=self.get(u.reg_read(UC_ARM_REG_SP));self.u.mem_write(0x06000000+i*0x10000+tile*32,bytes(self.u.mem_read(src,count)));self.ret();return
  if p==0x0200e948:self.ret();return
  # Borrow the explicit BG boundary seam without its1024-byte stack guard.
  if p in (0x0201d650,0x0201bf7c,0x02022c9c,0x02022d04,0x0201a0fc,0x020d28b8):
   bb.BgBench.hook(self,u,p,n,data);return
  if p in (DISABLE,RESTORE):
   old=u.reg_read(UC_ARM_REG_CPSR)
   if p==DISABLE:u.reg_write(UC_ARM_REG_CPSR,old|128);self.ret(old&128)
   else:u.reg_write(UC_ARM_REG_CPSR,(old&~128)|u.reg_read(UC_ARM_REG_R0));self.ret()
   return
  if p==ALLOC:
   raw=PARENT+0x100;size=u.reg_read(UC_ARM_REG_R1);self.put(raw-16,0x5544,2);self.put(raw-12,(size+3)&~3);self.ret(raw);return
  if p in (CREATE,FREE,DESTROY):
   if p==CREATE:self.header(u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1));self.ret(u.reg_read(UC_ARM_REG_R0))
   else:self.ret()
   return
  assert CODE<=p<CODE+len(self.code),hex(p)

def plan_words(b,o):
 if o.kind==1:
  root=b.get(PCAT);count=b.get(PCAT+12);directory=b.get(PCAT+8)
  entries=struct.iter_unpack('<HHI',bytes(b.u.mem_read(root+directory,count*8)))
  _,units,off=next(e for e in entries if e[0]==o.id)
  assert units==o.units
  return struct.unpack('<%dH'%units,bytes(b.u.mem_read(root+off,units*2)))
 return struct.unpack('<%dH'%o.units,bytes(b.u.mem_read(b.pool+o.offset,o.units*2)))

def pixel_set(canvas,x,y,c):
 off=(y//8*30+x//8)*32+4*(y%8)+x%8//2;shift=4*(x%2)
 canvas[off]=(canvas[off]&~(15<<shift))|(c<<shift)
def reference_rect(canvas,x,y,w,h,fill,edge=0):
 for yy in range(y,y+h):
  for xx in range(x,x+w):pixel_set(canvas,xx,yy,edge if edge and (xx in (x,x+w-1) or yy in (y,y+h-1)) else fill)
def reference_chrome(plan):
 canvas=bytearray(21120)
 reference_rect(canvas,0,0,240,176,3,2)
 reference_rect(canvas,2,2,236,1,4)
 reference_rect(canvas,4,4,232,168,1)
 reference_rect(canvas,4,4,232,16,3);reference_rect(canvas,4,20,232,16,13)
 reference_rect(canvas,4,156,232,16,2)
 if plan.view in (0,1,3):
  reference_rect(canvas,4,36,232,120,3)
  if plan.view==3:reference_rect(canvas,4,96,232,60,13)
 if plan.frame:reference_rect(canvas,0,104,240,48,1)
 for o in ops(plan):
  if o.row!=255 and 36<=o.y<156 and plan.view in (0,1,3):
   y=36+((o.y-36)//20)*20
   bg=13 if o.flags&8 else 1 if o.flags&1 else 13 if o.flags&4 else 3
   reference_rect(canvas,4,y,232,20,bg);reference_rect(canvas,6,y+19,228,1,11)
 for o in ops(plan):
  if o.kind==1 and o.flags&32:
   if plan.view in (0,1):reference_rect(canvas,4,o.y-2,232,20,2)
   else:reference_rect(canvas,o.x,o.y,o.w,o.h,2)
  if o.kind==3:reference_rect(canvas,o.x,o.y,o.w,o.h,1,8)
  if o.kind==1 and o.flags&2:reference_rect(canvas,o.x-3,o.y-1,o.w+7,18,13 if o.flags&4 else 3,5 if o.flags&4 else 4)
 return canvas

def reference_shapes(canvas,o):
 """Independent explicit integer point sets, no production helpers/masks."""
 def put(x,y,c):pixel_set(canvas,o.x+x,o.y+y,c)
 if o.kind==3 and o.w==232:
  for y,start in enumerate((3,2,1,0,1,2,3)):
   for x in range(4,9-start):put(x,y+6,2)
 elif o.kind in (4,5) and o.flags&1:
  for y,start in enumerate((3,2,1,0,1,2,3)):
   for d in range(start,5):
    if not o.flags&4 or d in (start,4):put(d if o.kind==4 else 4-d,y,5 if o.flags&4 else 2)
 elif o.kind in (7,8):
  if o.kind==8 or o.flags&4:
   for y,row in enumerate(((1,2,3,4),(1,4),(1,4),(0,1,2,3,4,5),(0,1,2,3,4,5),(0,1,2,3,4,5),(0,1,2,3,4,5),(0,1,2,3,4,5))):
    for x in row:put(x,y,5)
  else:
   for y,stop in enumerate((2,3,4,5,4,3,2)):
    for x in range(stop):put(x,y,2 if o.flags&1 else 10)
def text_colors(plan,o):
 bg=3 if o.y==4 else 13 if o.y==20 else 2 if o.flags&32 else (13 if o.flags&4 else 3) if o.flags&2 else 13 if o.flags&8 else 1 if o.flags&1 else 13 if o.flags&4 else 3 if o.row!=255 and plan.view in (0,1,3) else 1
 return (5 if o.flags&4 else 10 if bg in (2,3) else 2,bg)
def footer_runs(b,o):
 # Independent source metadata, no production descriptor or glyph parsing.
 catalog=json.loads((SOURCE/'sgp131/data/ui-copy.json').read_text());entry=next(e for e in catalog['entries'] if e['id']==o.id)
 words=plan_words(b,o);slices=[];at=0
 while at<len(words):
  end=words.index(65535,at);slices.append(words[at:end+1]);at=end+1
 variants=catalog['footer_runs'][entry['name']]
 runs=next(r for r in variants.values() if [len(z['text'])+1 for z in r]==[len(z) for z in slices])
 widths=[sum(b.widths[g-1] for g in words[:-1]) for words in slices]
 total=sum(widths)+sum(13 if r['key'] else 9 if i+1<len(runs) else 0 for i,r in enumerate(runs))
 x=4+(232-total)//2
 result=[]
 for i,(run,words,width) in enumerate(zip(runs,slices,widths)):
  key=run['key'];bg=1 if key else 2
  result.append((words,x+5 if key else x,156,(2 if key else 10,bg),width,key))
  x+=width+(13 if key else 9 if i+1<len(runs) else 0)
 return result

def reference_cap(canvas,x,y,width,surface):
 # Literal row patterns keep this oracle independent of packed production loops.
 rows=['..'+'e'*(width-4)+'..', '.e'+' '*(width-4)+'e.']
 rows+=['e'+' '*(width-2)+'e']*11
 rows+=['.e'+' '*(width-4)+'e.', '..'+'e'*(width-4)+'..', '...'+ 's'*(width-4)+'.']
 for yy,row in enumerate(rows):
  for xx,symbol in enumerate(row):
   if surface or symbol!=' ':pixel_set(canvas,x+xx,y+yy,{' ':1,'.':2,'e':6,'s':7}[symbol])

def synthetic_full_reference(b,plan):
 canvas=reference_chrome(plan)
 for o in ops(plan):
  if o.kind in (1,2,9,11):
   runs=footer_runs(b,o) if o.kind==11 else [(plan_words(b,o),o.x,o.y,text_colors(plan,o),0,'')]
   for words,x,y,(fg,bg),width,key in runs:
    if key:reference_cap(canvas,x-5,y,width+10,True)
    origin=x
    for g in words:
     if g==65535:break
     if g==0xe000:x=origin;y+=16;continue
     for yy in range(y,y+16):
      for xx in range(x,x+b.widths[g-1]):pixel_set(canvas,xx,yy,fg if (xx+yy+g)%3 else bg)
     x+=b.widths[g-1]
    if key:reference_cap(canvas,origin-5,156,width+10,False)
  else:reference_shapes(canvas,o)
 return bytes(canvas)

def independent_closure(plan,seed):
 rows={r for r in range(22) if seed>>r&1}
 while True:
  expanded=rows.copy()
  for o in ops(plan):
   y,h=(36+((o.y-36)//20)*20,20) if o.row!=255 and 36<=o.y<156 else (o.y,o.h)
   touched=set(range(y//8,(y+h-1)//8+1))
   if touched&rows:expanded.update(touched)
  if expanded==rows:return sum(1<<r for r in rows)
  rows=expanded

class NativePainterBench(PainterAPI,nb.NativeBgBench):
 """Prepared B: actual pinned NNS/BG/ring/glyph decode/copy and synchronous
 native String/printer reference. Only resource FS transport and cache/DMA
 effects use the existing declared prepared seams. No UI installation implied.
 """
 def __init__(self,compiled,fixture):
  self.enforce=False;self.reference=False;self.font_fetch=set();self.font_calls=[];self.fs_calls=[]
  self.raw,self.config,self.widths,self.glyphs,self.native_sections=fixture
  nb.NativeBgBench.__init__(self,compiled,self.native_sections)
  from module_bench import instruction_set
  roots=(fb.RENDER|1,fb.GENERATE|1,0x02026069,0x020262b5,rb.CPSR,0x02026355,0x02026381,0x020269a1,0x02026aa5,0x020200fd,0x020204b9,0x02020549,0x0201aa8d,0x0201ab0d)
  self.font_fetch=instruction_set(self.u,roots,[(a,a+n) for a,n,d in nf.FONT_PINS+nh.PINS])
  self.setup(self.raw,self.config,self.widths)
  self.put(0x0210f6d8,0x020f56d8) # Same prepared native font table as NativeFontBench.
  self.allowed.extend(((0x021d1f6c,0x021d1f6e),))
  assert self.call('ui_bg_enter_backdrop',TOKEN,PBG,1,PCTX+3288,0x564c)==1
  assert bytes(self.u.mem_read(0x050001a0,32))==struct.pack('<16H',*PALETTE)
 def native_allowed(self,p):return p in self.font_fetch or nb.NativeBgBench.native_allowed(self,p)
 def hook(self,u,p,n,data):
  if CODE<=p<CODE+len(self.code):
   check_compiled(self.code,p,n);self.instructions+=1;self.low=min(self.low,u.reg_read(UC_ARM_REG_SP));assert STACK-4096<=self.low<=STACK
   if self.active_service and p==self.active_service[1]:self.active_service=None
   return
  if p in (rb.INIT,rb.OPEN,rb.READ,rb.CLOSE,rb.SEEK):
   assert not self.enforce,'no FS during painter/reference';rb.ResourceBench.hook(self,u,p,n,data);return
  if p in (fb.RENDER,fb.GENERATE):
   self.font_calls.append(p);assert u.reg_read(UC_ARM_REG_SP)%8==0,'font EABI8'
   if not self.reference:assert u.reg_read(UC_ARM_REG_CPSR)&128,'restricted font masked'
  if self.enforce and self.operation and self.operation.startswith('settings_paint'):
   assert p not in (CREATE,ALLOC,FREE,DESTROY,0x0201aa8c,0x0201ab0c,rb.INIT,rb.OPEN,rb.READ,rb.CLOSE,rb.SEEK),'no per-frame service'
  font_body=any(a<=p<z for a,z in ((0x020021a0,0x02002c90),(0x02002e7c,0x02002ec8),(0x02002fac,0x02003030),
   (0x02020358,0x020204b8),(0x0202604c,0x02026110),(0x020262b4,0x020262d4),(0x0201dacc,0x0201ec48)))
  font_reference=self.reference and any(a<=p<z for a,z in ((0x020200fc,0x020202e8),(0x020204b8,0x020204c0),
   (0x02020548,0x02020560),(0x02026354,0x020263ac),(0x020269a0,0x02026a04),(0x02026aa4,0x02026ac4),(0x0201a910,0x0201abec)))
  if (p in self.font_fetch or font_body or font_reference) and (p not in nb.NATIVE_INSTRUCTIONS or 0x0201a8e8<=p<0x0201abec):
   self.instructions+=1;self.low=min(self.low,u.reg_read(UC_ARM_REG_SP));assert STACK-4096<=self.low<=STACK
   if 0x0201a8e8<=p<0x0201abec:assert self.reference,'native String/printer allocations reference only'
   return
  nb.NativeBgBench.hook(self,u,p,n,data)
 def store(self,u,access,p,n,v,data):
  if STACK-4096<=p<p+n<=STACK or PBG<=p<p+n<=PBG+176:
   self.store_contexts.append((p,n,v,u.reg_read(UC_ARM_REG_PC),u.reg_read(UC_ARM_REG_CPSR)));self.writes.append((p,n,v));return
  # Existing native BG guard enforces physical upload span/cache, immutable
  # front, MMIO and owned hidden roots. Extra actor writes are bounded below.
  nb.NativeBgBench.store(self,u,access,p,n,v,data)
  if self.enforce and self.operation and self.operation.startswith('settings_paint'):
   allowed=[(PCTX,P_SIZE),(PBG,176),(fb.FL,88),*[(a,z) for a,z in ((fb.FFLAGS,2),(fb.COLORS,6),(fb.LOOKUP,512),(fb.WORK,130))],
            (0x050001c0,64),(0x06000000,0x20000),(0x040000d4,12)]
   i=self.get(PBG+88)
   if i<2:allowed.extend(((self.get(PBG+20+4*i),2048),(self.get(PBG+28+4*i),21120)))
   assert any(a<=p<p+n<=a+z for a,z in allowed) or STACK-4096<=p<p+n<=STACK,f'paint actor store {p:08x}/{n}'
 def snapshot(self):
  return [(p,bytes(self.u.mem_read(p,n))) for p,n in ((0x02000000,0x400000),(0x027e0000,0x4000),(0x04000000,0x1000),(0x04001000,0x1000),(0x05000000,0x1000),(0x06000000,0x20000),(0x06200000,0x20000))]
 def restore(self,snapshot):
  for p,data in snapshot:self.u.mem_write(p,data)
  self.active_service=None;self.upload=None;self.dma_pending=None;self.clean=set()
 def reference_text(self,window,words,x,y,colors):
  staging=fb.SGG+0x200;self.u.mem_write(staging,struct.pack('<%dH'%len(words),*words))
  string=self.address(0x02026355,len(words),38);assert string
  self.address(0x020269a1,string,staging)
  assert self.address(0x020200fd,window,0,string,x,y,255,(colors[0]<<16)|(colors[1]<<8)|colors[1],0)==8
  self.address(0x02026381,string)
 def full_reference(self,plan,index):
  """AlwaysFULL native BG and native allocated synchronous text. It never
  calls painter, dirty, closure, restricted-font-begin or history helpers."""
  before=self.snapshot();globals_before=self.globals();self.reference=True
  heap38=self.get(TOKEN+16);topology=nf.NativeFontBench.topology
  allocation_before=topology(self,heap38),topology(self,TEMPLATES[0][0]),self.get(self.counts,2),self.get(self.counts+76,2)
  try:
   window=self.call('ui_bg_begin',TOKEN,PBG,1,index);assert window
   assert self.call('ui_bg_fill',TOKEN,PBG,1,1)==1
   pixels=self.get(window+12);self.u.mem_write(pixels,bytes(reference_chrome(plan)))
   for o in ops(plan):
    if o.kind==11:
     for words,x,y,colors,width,key in footer_runs(self,o):
      if key:
       canvas=bytearray(self.u.mem_read(pixels,21120));reference_cap(canvas,x-5,y,width+10,True);self.u.mem_write(pixels,bytes(canvas))
      self.reference_text(window,words,x,y,colors)
      if key:
       canvas=bytearray(self.u.mem_read(pixels,21120));reference_cap(canvas,x-5,y,width+10,False);self.u.mem_write(pixels,bytes(canvas))
    elif o.kind in (1,2,9):self.reference_text(window,plan_words(self,o),o.x,o.y,text_colors(plan,o))
    elif o.kind!=10:
     canvas=bytearray(self.u.mem_read(pixels,21120));reference_shapes(canvas,o);self.u.mem_write(pixels,bytes(canvas))
   if plan.frame:
    self.u.mem_write(PREQ,struct.pack('<8I',3,15,25,4,self.root+128+(plan.frame-1)*608,576,self.root+128+(plan.frame-1)*608+576,32))
    assert self.call('ui_bg_frame',TOKEN,PBG,1,PREQ)==1
   else:assert self.call('ui_bg_unframed',TOKEN,PBG,1)==1
   for row in range(22):
    self.u.mem_write(PREQ,struct.pack('<2I',row,1));assert self.call('ui_bg_rows',TOKEN,PBG,1,PREQ)==1
   assert self.call('ui_bg_ready',TOKEN,PBG,1,max(self.get(PBG+68),self.get(PBG+72))+1)==1
   result=self.frame_result(index)
   assert (topology(self,heap38),topology(self,TEMPLATES[0][0]),self.get(self.counts,2),self.get(self.counts+76,2))==allocation_before,'native reference allocator topology/count restored'
  finally:
   self.reference=False;self.restore(before)
  assert self.globals()==globals_before
  return result
 def frame_result(self,index):
  pixels=bytes(self.u.mem_read(self.get(PBG+28+4*index),21120));mapping=bytes(self.u.mem_read(self.get(PBG+20+4*index),2048))
  palette=bytes(self.u.mem_read(0x050001a0,32));frame_palette=bytes(self.u.mem_read(0x050001c0+32*index,32));frame_tiles=bytes(self.u.mem_read(0x06007b80+index*0x10000,576))
  rgb=visible_rgb(self,index)
  assert self.get(0x04001000)&0x1f00==0 and self.get(0x05000400,2)==0,'lower blank hardware'
  return dict(pixels=pixels,map=mapping,palette=palette,frame_palette=frame_palette,frame_tiles=frame_tiles,rgb555=rgb)

def visible_rgb(b,index):
 """Independent DS text-BG map/tile/palette interpretation at256x192.
 No native glyph decoder, source font data or production helpers are used."""
 mapping=struct.unpack('<1024H',b.u.mem_read(0x0600f000+index*2048,2048));chars=bytes(b.u.mem_read(0x06000000+index*0x10000,0x8000));pal=struct.unpack('<256H',b.u.mem_read(0x05000000,512))
 out=bytearray()
 for y in range(192):
  for x in range(256):
   entry=mapping[(y//8)*32+x//8];tile=entry&1023;xx=x%8;yy=y%8
   if entry&1024:xx=7-xx
   if entry&2048:yy=7-yy
   color=(chars[tile*32+yy*4+xx//2]>>(4*(xx%2)))&15
   value=pal[((entry>>12)*16+color) if color else 0]&32767
   out.extend(struct.pack('<H',value))
 return bytes(out)

def seed_completed(b,plan,index,version):
 """Independent full-canvas completed fixture for focused retained mutants.
 Uses actual BG ownership/row/ready APIs; no painter code builds the seed."""
 assert b.call('ui_bg_begin',TOKEN,PBG,1,index)
 root=b.get(PBG+28+4*index);b.u.mem_write(root,synthetic_full_reference(b,plan))
 assert b.call('ui_bg_unframed',TOKEN,PBG,1)==1
 for row in range(22):
  b.u.mem_write(PREQ,struct.pack('<2I',row,1));assert b.call('ui_bg_rows',TOKEN,PBG,1,PREQ)==1
 assert b.call('ui_bg_ready',TOKEN,PBG,1,version)==1
 b.u.mem_write(PCTX+92+index*1196,bytes(plan)+struct.pack('<3I',version,1,0));b.publish();b.version=version

def seeded_retained(b):
 p=b.build(first=1);seed_completed(b,p,0,1)
 b.s.row=1;p=b.build(first=1);seed_completed(b,p,1,2)
 b.s.row=2;p=b.build(first=1);expected=synthetic_full_reference(b,p)
 assert b.finish_paint()==PREPARED
 assert b.get(PCTX+28)==independent_closure(p,b.get(PCTX+24)),'row closure'
 assert b.pixels(0)==expected,'all intersecting ops replayed'
 assert b.get(PCTX+92+1188)==1,'completed history'
 return b

def active_job_at_ready(b):
 b.build();assert b.begin()==MORE
 for _ in range(1800):
  assert b.step()==MORE
  if b.get(PCTX+12)==9:break
 assert b.get(PCTX+12)==9
 root=b.root;count=b.get(root+100)
 identity,units,offset=next(e for e in struct.iter_unpack('<HHI',bytes(b.u.mem_read(root+48448,count*8))) if e[0]==1)
 index=b.get(PBG+88)
 b.u.mem_write(PSREQ,struct.pack('<8I8B',PBG+36+index*16,b.get(PBG+28+(1-index)*4),21120,PUIR,offset,units,0,PCTX+2636,0,0,1,2,1,1,0,0))
 assert b.call('ui_font_begin',fb.FL,PCTX+2484,PSREQ)==fb.F_ACTIVE
 assert b.step()==FAILED,'no job at Ready'
 assert b.get(PBG+80)==2,'no pending partial canvas'
