import unittest
from guide_bench import *
class ControllerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(prefix='guide-controller-');cls.compiled,cls.detail=compile_ui(Path(cls.tmp.name),red=os.environ.get('GUIDE_RED')=='1')
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_open_category_and_list_preserves_five_row_jump(self):
  b=ControllerBench(self.compiled)
  self.assertEqual(b.action(1),1);self.assertEqual(b.state().cursor.depth,1)
  self.assertEqual(b.action(256),1);s=b.state();self.assertEqual((s.cursor.row,s.cursor.scroll),(5,3))
  self.assertEqual(b.action(1),1);self.assertEqual(b.state().cursor.depth,2)
  self.assertEqual(b.action(16),1);self.assertEqual(b.state().cursor.page,1)
 def test_reference_stack_eight_exact_returns(self):
  b=ControllerBench(self.compiled);b.action(1);b.action(128);b.action(1)
  original=bytes(b.state().cursor)
  for depth in range(8):
   self.assertEqual(b.action(1),1);self.assertEqual(b.state().back_count,depth+1)
  frozen=bytes(b.state());self.assertEqual(b.action(1),0);self.assertEqual(bytes(b.state()),frozen)
  for depth in reversed(range(8)):
   self.assertEqual(b.action(2),1);self.assertEqual(b.state().back_count,depth)
  self.assertEqual(bytes(b.state().cursor),original)
 def test_fresh_release_l_equals_a_opposites_and_busy(self):
  b=ControllerBench(self.compiled)
  self.assertEqual(b.input(1,held=1),0);self.assertEqual(b.input(fresh=0),0)
  self.assertEqual(b.state().release_gate,1)
  b.input();self.assertEqual(b.state().release_gate,0)
  b.input(1,held=1);self.assertEqual(b.state().cursor.depth,1)
  b.input(512,held=512,mapped=1,mode=3);self.assertEqual(b.state().cursor.depth,1)
  self.assertEqual(b.input(64|128,repeated=128),0)
  before=bytes(b.state().cursor);b.input(1,busy=1);b.input();self.assertEqual(bytes(b.state().cursor),before)
  b.input(512|1,held=513,mapped=1,mode=3);self.assertEqual(b.state().cursor.depth,2)
 def _second_detail_page_l_equals_a(self):
  b=ControllerBench(self.compiled)
  self.assertEqual(b.input(mode=3),0)
  self.assertEqual(b.state().release_gate,0)
  for depth in (1,2):
   self.assertEqual(b.input(1,held=1,mapped=1,mode=3),1)
   self.assertEqual(b.state().cursor.depth,depth)
   self.assertEqual(b.input(mode=3),0)
  self.assertEqual(b.state().cursor.page,0)
  # Native L=A hides mapped R, but its real physical identity advances a page.
  self.assertEqual(b.input(256,held=256,mapped=0,mode=3),1)
  self.assertEqual(b.state().cursor.page,1)
  self.assertEqual(b.input(mode=3),0)
  self.assertEqual(b.state().release_gate,0)
  return b
 def test_raw_l_previous_page_under_l_equals_a(self):
  b=self._second_detail_page_l_equals_a()
  # Literal external contract: real L returns 2/2 -> 1/2 despite mapped A.
  self.assertEqual(b.input(512,held=512,mapped=1,mode=3),1)
  self.assertEqual((b.state().cursor.depth,b.state().cursor.page,b.state().back_count),(2,0,0))
 def test_busy_l_is_not_queued_and_requires_neutral_then_new_press(self):
  b=self._second_detail_page_l_equals_a();cursor=bytes(b.state().cursor)
  self.assertEqual(b.input(512,held=512,mapped=1,mode=3,busy=1),0)
  self.assertEqual(b.state().release_gate,1)
  self.assertEqual(bytes(b.state().cursor),cursor)
  # A neutral sample while still busy does not rearm the consumer.
  self.assertEqual(b.input(mode=3,busy=1),0)
  self.assertEqual(b.state().release_gate,1)
  # Neither a pressed L nor held/repeated L can cross the release fence.
  for pressed,repeated in ((512,0),(0,512)):
   self.assertEqual(b.input(pressed,repeated=repeated,held=512,mapped=1 if pressed else 0,mode=3),0)
   self.assertEqual(b.state().release_gate,1)
   self.assertEqual(bytes(b.state().cursor),cursor)
  self.assertEqual(b.input(mode=3),0)
  self.assertEqual(b.state().release_gate,0)
  self.assertEqual(bytes(b.state().cursor),cursor)
  self.assertEqual(b.state().back_count,0)
  self.assertEqual(b.input(512,held=512,mapped=1,mode=3),1)
  self.assertEqual((b.state().cursor.depth,b.state().cursor.page,b.state().back_count),(2,0,0))
 def test_lower_touch_inert_at_all_depths_drag_hold_reentry_and_real_keys(self):
  for depth in range(3):
   b=ControllerBench(self.compiled)
   for _ in range(depth):b.action(1)
   before=bytes(b.state().cursor)
   # Touch held on entry must not block the physical release fence.
   self.assertEqual(b.input(x=150,y=140,down=1),0)
   self.assertEqual(b.state().release_gate,0)
   for x,y in ((20,60),(150,60),(20,100),(150,100),(20,140),(150,140),(0,0),(255,191)):
    self.assertEqual(b.call('guide_ui_target',x,y),0)
    for xx,yy,down in ((x,y,1),(x,y,1),(239,155,1),(x,y,0)):
     self.assertEqual(b.input(x=xx,y=yy,down=down),0)
     self.assertEqual(bytes(b.state().cursor),before)
     self.assertEqual((b.state().touch_target,b.state().touch_armed,b.state().touch_down),(0,0,0))
   key=256 if depth==2 else 128
   self.assertEqual(b.input(key,held=key,x=150,y=140,down=1),1)
   for fresh in (2,3):
    self.assertEqual(b.input(fresh=fresh,down=1),0)
    self.assertEqual(b.state().release_gate,1)
    b.input(down=1);self.assertEqual(b.state().release_gate,0)
   b.input(busy=1,down=1);self.assertEqual(b.state().release_gate,1)
   b.input(down=1);self.assertEqual(b.state().release_gate,0)
 def test_invalid_reference_or_cursor_refuses_without_change(self):
  b=ControllerBench(self.compiled);b.action(1)
  for ignored in (1024,2048):
   before=bytes(b.state());self.assertEqual(b.action(ignored),0);self.assertEqual(bytes(b.state()),before)
  b.action(1)
  for ignored in (1024,2048):
   before=bytes(b.state());self.assertEqual(b.action(ignored),0);self.assertEqual(bytes(b.state()),before)
  s=b.state();s.cursor.page=20;b.set_state(s);before=bytes(s)
  self.assertEqual(b.action(1),0);self.assertEqual(bytes(b.state()),before)
 def test_missing_destination_page_refuses_before_cursor_or_history_write(self):
  original,_=synthetic()
  for global_entry,page,reference in ((0,0,False),(0,1,False),(8,0,True)):
   data=bytearray(original);table=struct.unpack_from('<I',data,12+4*12+16*global_entry+12)[0]
   offset=struct.unpack_from('<I',data,table+4*page)[0];struct.pack_into('<H',data,offset,0)
   b=ControllerBench(self.compiled,bytes(data));b.action(1)
   if reference or page:b.action(1)
   before=bytes(b.state());self.assertEqual(b.action(16 if page else 1),0)
   self.assertEqual(bytes(b.state()),before)
if __name__=='__main__':unittest.main()
