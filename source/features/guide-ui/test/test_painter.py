import unittest
from guide_bench import *
PAINTER=0x02355000
class PainterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='guide-painter-');cls.compiled,cls.detail=compile_ui(Path(cls.tmp.name),'painter',red=os.environ.get('GUIDE_RED')=='1',extra='' if os.environ.get('GUIDE_RED')=='1' else '\nvoid guide_test_geometry(GuidePainter*p,const GuideDrawOp*o){gp_geometry(p,o); }\n')
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_init_exact_fresh_storage_palette_and_refuse_live_reset(self):
  b=ControllerBench(self.compiled);b.allowed.append((PAINTER,PAINTER+2552))
  self.assertEqual(b.call('guide_paint_init',PAINTER,2552,1),1)
  self.assertEqual(b.get(PAINTER+2520+6,2),0x51a4)
  before=bytes(b.u.mem_read(PAINTER,2552));self.assertEqual(b.call('guide_paint_init',PAINTER,2552,2),0)
  self.assertEqual(bytes(b.u.mem_read(PAINTER,2552)),before)

 def test_rectangle_matches_pixel_oracle_with_bounded_work_and_untouched_nibbles(self):
  b=ControllerBench(self.compiled);window,pixels=0x0234d000,0x02310000
  b.allowed.append((pixels,pixels+21120))
  b.u.mem_write(window,struct.pack('<I6BHI',0,1,1,1,30,22,13,1,pixels))
  initial=bytes((i*29+7)&255 for i in range(21120))
  for x,width,y,height in ((0,1,0,1),(1,1,7,9),(1,2,6,3),(6,9,155,18),
                           (7,17,8,8),(8,9,175,1),(231,9,7,9),(239,1,175,1),(4,232,36,8)):
   for edge,mask in ((0,0x3fffff),(8,0x3fffff),(8,0x155555)):
    expected=bytearray(initial)
    for yy in range(y,y+height):
     if mask>>(yy//8)&1:
      for xx in range(x,x+width):
       color=edge if edge and (xx in (x,x+width-1) or yy in (y,y+height-1)) else 13
       off=(yy//8*30+xx//8)*32+yy%8*4+xx%8//2;shift=4*(xx%2)
       expected[off]=(expected[off]&~(15<<shift))|(color<<shift)
    b.u.mem_write(pixels,initial)
    b.call('gp_rect',window,x,y,width,height,13,edge,mask)
    self.assertEqual(bytes(b.u.mem_read(pixels,21120)),bytes(expected),(x,width,y,height,edge,mask))
  b.call('gp_rect',window,4,36,232,8,3,8,0x3fffff)
  self.assertLess(b.metrics[-1][2],60000,'baseline pixel-at-a-time path used103015 ARM instructions')

 def test_focus_triangle_is_bounded_inside_twenty_pixel_upper_band(self):
  b=ControllerBench(self.compiled);bg,pixels=0x0234d000,0x02310000
  b.allowed.extend(((PAINTER,PAINTER+2552),(pixels,pixels+21120)))
  b.u.mem_write(PAINTER,b'\0'*2552);b.put(PAINTER+60,bg);b.put(PAINTER+24,0x3fffff)
  b.u.mem_write(bg+36,struct.pack('<I6BHI',0,1,1,1,30,22,13,1,pixels))
  o=Op();o.kind=2;o.x=4;o.y=116;o.w=232;o.h=20
  b.u.mem_write(PLAN,bytes(o));b.call('guide_test_geometry',PAINTER,PLAN)
  points=set()
  for y in range(176):
   for x in range(240):
    offset=(y//8*30+x//8)*32+(y%8)*4+(x%8)//2
    if b.get(pixels+offset,1)>>(4*(x%2))&15:points.add((x,y))
  self.assertEqual(points,{(9+x,124+y) for y,row in enumerate(((0,),(0,1),(0,1,2),(0,1,2,3),(0,1,2),(0,1),(0,))) for x in row})


# Regression: native font cells must not break list contours.
PAINTER=0x02355000;BG=0x0234d000;PIX=(0x02310000,0x02316000)
EXTRA='''
void t_chrome(GuidePainter*p,unsigned row){gp_chrome(p,0,row);}
void t_contour(GuidePainter*p){%s}
void t_mask(GuidePainter*p,unsigned mask){p->upper_rows=mask;}
void t_setup(GuidePainter*p,UiBg*b,const GuidePlan*d,unsigned i){p->bg=b;p->desired=d;p->index=i;p->upper_rows=0x3fffff;}
'''
class BorderTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();red=os.environ.get('GUIDE_BORDER_RED')=='1'
  cls.c,_=compile_ui(Path(cls.tmp.name),'painter',extra=EXTRA%('(void)p;' if red else 'gp_contour(p);'))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def run_case(self,index,view=0,mask=0x3fffff):
  b=ControllerBench(self.c);b.allowed.extend(((PAINTER,PAINTER+2552),(PIX[0],PIX[0]+21120),(PIX[1],PIX[1]+21120)))
  b.u.mem_write(PAINTER,b'\0'*2552)
  for i in range(2):b.u.mem_write(BG+36+16*i,struct.pack('<I6BHI',0,1,1,1,30,22,13,1,PIX[i]))
  pl=Plan();pl.view=view;pl.count=2;o=pl.ops[0];o.kind=2;o.x=4;o.y=36;o.w=232;o.h=20;o.color=1
  t=pl.ops[1];t.kind=1;t.x=40;t.y=60;t.w=120;t.h=16;t.color=3
  b.u.mem_write(PLAN,bytes(pl));b.call('t_setup',PAINTER,BG,PLAN,index);px=PIX[index]
  for r in range(22):b.call('t_chrome',PAINTER,r)
  def at(x,y):return ((y//8*30+x//8)*32+(y%8)*4+(x%8)//2,4*(x%2))
  def put(x,y,c):
   a,s=at(x,y);v=b.get(px+a,1);b.u.mem_write(px+a,bytes([(v&~(15<<s))|(c<<s)]))
  def get(x,y):a,s=at(x,y);return b.get(px+a,1)>>s&15
  before=[[get(x,y) for x in range(240)] for y in range(176)]
  # native printer cell semantics: whole 16-row cell cleared to background, then ink
  for y in range(40,56):
   for x in range(10,200):put(x,y,1)
  for y in range(60,76):
   for x in range(40,160):put(x,y,3)
  put(50,55,10);put(51,55,2);put(52,55,5);put(60,75,10)   # glyph ink reaching the cell bottom
  other=bytes(b.u.mem_read(PIX[1-index],21120));before_contour=bytes(b.u.mem_read(px,21120));b.call('t_mask',PAINTER,mask);b.call('t_contour',PAINTER)
  self.assertEqual(bytes(b.u.mem_read(PIX[1-index],21120)),other)
  if view==2:self.assertEqual(bytes(b.u.mem_read(px,21120)),before_contour)
  for yy in range(176):
   if not(mask&(1<<(yy//8))):
    for xx in range(240):
     off,sh=at(xx,yy);self.assertEqual(get(xx,yy),before_contour[off]>>sh&15)
  return get,before
 def test_selected_border_and_separator_continuous_both_buffers(self):
  for idx in (0,1):
   get,before=self.run_case(idx)
   self.assertEqual([x for x in range(4,236) if get(x,55)!=8 and x not in (50,51,52)],[],idx)
   self.assertEqual((get(50,55),get(51,55),get(52,55)),(10,2,5))
   self.assertEqual([x for x in range(6,234) if get(x,75)!=11 and x!=60],[],idx)
   self.assertEqual(get(60,75),10)
   for y in (95,115,135):self.assertEqual({get(x,y) for x in range(6,234)},{11})
 def test_partial_dirty_selected_row_leaves_other_rows_and_buffer_unchanged(self):
  for idx in (0,1):
   get,before=self.run_case(idx,mask=1<<(55//8))
   self.assertEqual(get(100,55),8)
   self.assertEqual(get(100,75),3)
 def test_detail_view_untouched(self):
  get,before=self.run_case(0,view=2)
  self.assertEqual(get(100,55),1);self.assertEqual(get(100,75),3)
