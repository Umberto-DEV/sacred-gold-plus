"""Execute real compiled Guide hooks against explicit current/stale native menus."""
import struct, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from sgp13.guide import compile_native,build_content,BASE,STATE,CANARY
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3

class HookOwnershipTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  probe=subprocess.run([sys.executable,'-c',"from unicorn import *;u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(4096,4096);u.mem_write(4096,bytes.fromhex('00bf'));u.emu_start(4097,4098)"],capture_output=True)
  if probe.returncode:raise unittest.SkipTest('Unicorn JIT unavailable: %d'%probe.returncode)
  with tempfile.TemporaryDirectory() as d:cls.blob,cls.symbols=compile_native(d)
 def setUp(self):
  self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);self.u.mem_map(0x02000000,0x400000);self.u.mem_map(0x05000000,0x1000);self.u.mem_write(BASE,self.blob)
  self.fs=0x02280000;self.env=0x02281000;self.task=0x02282000;self.control=0x02283000;self.child=0x02284000;self.menu=0x02290000
  self.write(self.fs+0xd8,self.task);self.write(self.control+4,self.child);self.u.mem_write(self.control,b'\0\1')
  self.write(self.menu+8,self.child);self.write(self.menu+0x10,self.fs);self.u.mem_write(self.fs+0xd2,b'\2')
  self.write(STATE+4,self.menu);self.write(STATE+8,1);self.write(STATE+12,1)
  self.write(STATE+212,self.child) # appended owner task; existing cursor/layout stays stable
  self.write(0x021d1154,1);self.calls=[]
  def native(uc,addr,size,_):
   if addr==0x02001000:uc.emu_stop();return
   returns={0x0205064c:self.fs,0x02050650:self.env,0x021f6b00:0,0x021f6b10:1,0x0203c47c:1,0x02026354:0,0x0200fb5c:1,0x0205c6d4:0,0x0225c170:0}
   voids=(0x0203c460,0x0203df64,0x021f6b50,0x021e636c,0x0200604c,0x0225a320,0x0225b404,0x0225bc84,0x0225b4d8,0x0201d40c,0x0225b398)
   if addr==0x0201f988:
    arg=uc.reg_read(UC_ARM_REG_R0)
    self.assertIn(arg,(self.task,self.child),'must traverse current task ownership only')
    result=self.control if arg==self.task else self.menu
   elif addr in returns:result=returns[addr]
   elif addr in voids:result=1
   else:return
   if addr==0x0225a320:self.frame_selection=(self.read(STATE+8),self.read(STATE+12))
   if addr==0x0201d40c:self.icon_bg=uc.reg_read(UC_ARM_REG_R2)
   self.calls.append(addr);uc.reg_write(UC_ARM_REG_R0,result);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  self.u.hook_add(UC_HOOK_CODE,native)
 def write(self,addr,value):self.u.mem_write(addr,struct.pack('<I',value))
 def read(self,addr):return struct.unpack('<I',self.u.mem_read(addr,4))[0]
 def invoke(self,name,a=0,b=0):
  self.assertIn(name,self.symbols)
  self.u.reg_write(UC_ARM_REG_SP,0x02300000);self.u.reg_write(UC_ARM_REG_LR,0x02001001)
  self.u.reg_write(UC_ARM_REG_R0,a);self.u.reg_write(UC_ARM_REG_R1,b)
  self.u.emu_start(self.symbols[name],0,count=100000)
 def assert_rejected(self):
  self.assertNotIn(0x021e636c,self.calls,'stale Guide request must not start fade/launch')
  self.assertEqual(self.read(STATE+8),0);self.assertEqual(self.read(STATE+12),0)
 def test_excluded_current_menu_rejects_stale_selected_and_pending(self):
  self.write(self.menu+0x51c,6<<1);self.invoke('guide_task_input');self.assert_rejected()
  self.assertIn(0x0203c47c,self.calls)
 def test_different_instance_rejects_without_reading_unmapped_old_pointer(self):
  self.write(STATE+4,0xdeadbeec);self.invoke('guide_task_input');self.assert_rejected()
 def test_different_owner_task_rejects_reused_menu_address(self):
  self.write(STATE+212,self.child+0x100);self.invoke('guide_task_input');self.assert_rejected()
 def test_x_closure_wins_over_pending_request(self):
  self.write(0x021d1154,1024);self.invoke('guide_task_input');self.assert_rejected()
 def test_excluded_frame_clears_stale_state_before_native_dispatch(self):
  self.write(self.menu+0x51c,4<<1);self.invoke('guide_field_frame',self.child,self.menu);self.assert_rejected()
  self.assertEqual(self.frame_selection,(0,0))
 def test_different_dpad_menu_clears_state_and_delegates(self):
  self.write(STATE+4,0xdeadbeec);self.write(0x021d1154,0);self.invoke('guide_dpad',self.menu)
  self.assert_rejected();self.assertIn(0x0225b404,self.calls)
 def test_constructor_resets_reused_pointer_selection(self):
  self.invoke('guide_field_create',self.menu);self.assert_rejected()
  self.assertEqual(self.read(STATE+4),self.menu)
 def test_x_frame_clears_before_dispatch_and_cannot_relaunch_on_next_a(self):
  self.write(0x021d1154,1024);self.invoke('guide_field_frame',self.child,self.menu)
  self.assertEqual(self.frame_selection,(0,0));self.assert_rejected()
  self.write(0x021d1154,1);self.invoke('guide_task_input');self.assert_rejected()
 def test_excluded_controller_type_rejects_before_resolving_child_menu(self):
  self.u.mem_write(self.control,b'\6');self.invoke('guide_task_input');self.assert_rejected()
  self.assertEqual(self.calls.count(0x0201f988),1)
 def test_current_normal_menu_still_launches(self):
  self.invoke('guide_task_input');self.assertIn(0x021e636c,self.calls)
  self.assertEqual(struct.unpack('<H',self.u.mem_read(self.env+0x26,2))[0],4)
 def test_touch_confirmation_is_visible_before_launch_and_never_dispatches_old_item(self):
  self.write(STATE+12,0);self.write(0x021d1154,0)
  self.write(self.menu+12,self.menu+0x600)
  self.u.mem_write(0x021d116c,struct.pack('<HHH',120,154,1))
  self.invoke('guide_touch_input',self.menu)
  self.assertEqual(self.read(STATE+220),9,'native-length confirmation feedback is missing')
  self.u.mem_write(0x021d1170,b'\0\0')
  for frame in range(9):
   self.invoke('guide_task_input')
   self.assertNotIn(0x0203c47c,self.calls,'pending Guide must not open the old native item')
   self.assertNotIn(0x021e636c,self.calls,'launch must wait for confirmation feedback')
   self.invoke('guide_field_frame',self.child,self.menu)
  self.invoke('guide_task_input')
  self.assertEqual(self.calls.count(0x021e636c),1)
 def test_button_confirmation_uses_the_same_bounded_feedback(self):
  self.write(STATE+12,0);self.invoke('guide_task_input')
  self.assertEqual(self.read(STATE+220),9)
  self.assertNotIn(0x0203c47c,self.calls);self.assertNotIn(0x021e636c,self.calls)
 def test_cancel_during_confirmation_clears_animation_and_pending_launch(self):
  self.write(STATE+220,9);self.write(0x021d1154,2)
  self.invoke('guide_task_input');self.assert_rejected()
  self.assertEqual(self.read(STATE+220),0)
 def test_arrows_during_confirmation_do_not_move_the_native_focus(self):
  self.write(STATE+220,9);self.write(0x021d1154,64);self.write(self.menu+0x14,2)
  self.u.mem_write(self.menu+0x470+6*8,b'\1')
  self.invoke('guide_dpad',self.menu)
  self.assertEqual(self.read(self.menu+0x14),2)
  self.assertEqual(self.read(STATE+8),1)
  self.assertNotIn(0x0225b398,self.calls)
 def test_icon_stays_below_native_labels_in_the_shared_tile_row(self):
  # Options occupies BG5 rows16..17; Guide's frame begins inside row17.
  # A second BG5 Window replaces those label tiles even with transparent ink.
  self.write(STATE+16,1);self.write(STATE+220,9);self.write(0x021d1154,0)
  self.u.mem_write(0x05000406,struct.pack('<H',15139))
  self.invoke('guide_field_frame',self.child,self.menu)
  self.assertEqual(self.icon_bg,4,'Guide must not replace native BG5 label tiles')
  self.assertEqual(struct.unpack('<H',self.u.mem_read(0x050004a2,2))[0],15139)
 def test_cancel_releases_only_the_owned_native_touch_command_in_every_dispatch_order(self):
  for name in ('guide_task_input','guide_field_frame','guide_dpad'):
   for key in (2,1024):
    for command in (32,7):
     with self.subTest(hook=name,key=key,command=command):
      self.setUp();self.write(STATE+220,9);self.write(0x021d1154,key)
      self.u.mem_write(self.fs+0xd0,struct.pack('<H',command))
      self.invoke(name,self.child if name=='guide_field_frame' else self.menu,self.menu)
      self.assertEqual(struct.unpack('<H',self.u.mem_read(self.fs+0xd0,2))[0],0 if command==32 else command)
      self.assertEqual(self.read(STATE+12),0);self.assertEqual(self.read(STATE+220),0)
 def test_rejected_or_replaced_menu_releases_its_owned_touch_command(self):
  for case in ('excluded-frame','replaced-frame','rejected-task'):
   with self.subTest(case=case):
    self.setUp();self.write(0x021d1154,0);self.write(STATE+220,9)
    self.u.mem_write(self.fs+0xd0,struct.pack('<H',32))
    if case=='excluded-frame':self.write(self.menu+0x51c,6<<1)
    else:self.write(STATE+212,self.child+0x100)
    self.invoke('guide_task_input' if case=='rejected-task' else 'guide_field_frame',self.child,self.menu)
    self.assertEqual(struct.unpack('<H',self.u.mem_read(self.fs+0xd0,2))[0],0)
    self.assertEqual(self.read(STATE+12),0)
class GuideMainNavigationTests(unittest.TestCase):
 """Actual ARM main/draw; only native text, upload and sound APIs are seams.

 The SGG1 fixture and Window tile buffers are real. Guide stepping, reference
 history, borders/arrows and input arbitration all execute production code.
 """
 @classmethod
 def setUpClass(cls):
  probe=subprocess.run([sys.executable,'-c',"from unicorn import *;u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.mem_map(4096,4096);u.mem_write(4096,bytes.fromhex('00bf'));u.emu_start(4097,4098)"],capture_output=True)
  if probe.returncode:raise unittest.SkipTest('Unicorn JIT unavailable: %d'%probe.returncode)
  with tempfile.TemporaryDirectory() as d:cls.blob,cls.symbols=compile_native(d)
  cls.content=build_content([
   dict(id=1,title='Long category',entries=[dict(id=100+i,title='Long '+str(i),pages=[['First'],dict(lines=['Reference'],reference=202)]) for i in range(20)]),
   dict(id=2,title='Short category',entries=[dict(id=200+i,title='Short '+str(i),pages=[['Short page']]) for i in range(5)])],
   lambda text:[ord(c) for c in text]+[65535],lambda text:len(text)*6)
 def setUp(self):
  self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);self.u.mem_map(0x02000000,0x400000)
  self.u.mem_write(BASE,self.blob);self.u.mem_write(STATE+240,CANARY)
  self.write(STATE+24,0x02200000);self.write(STATE+28,0x02201000)
  self.u.mem_write(0x02201000,self.content)
  # ARM Window: bg*, id/x/y/w/h/pal bytes, tile u16, pixels*.
  for offset,height,pixels in ((148,3,0x02210000),(164,15,0x02214000),(180,3,0x02218000),(196,18,0x0221c000)):
   self.u.mem_write(STATE+offset,struct.pack('<I6BHI',0,1,2,0,28,height,13,1,pixels))
  labels=['Guide','B Back','A Open','L Page R','Choose','X Reference','X Link','Page','Entry','L','R','L/R: 5 entries']
  text=bytearray(2*len(labels))
  for i,label in enumerate(labels):
   struct.pack_into('<H',text,i*2,len(text));text.extend(struct.pack('<%dH'%(len(label)+1),*[ord(c) for c in label],65535))
  self.u.mem_write(0x023d7c40,bytes(text))
  self.copies=[];self.sounds=[];self.prints=[];self.returned=False
  def native(uc,address,size,_):
   if address==0x02001000:self.returned=True;uc.emu_stop();return
   if BASE<=address<BASE+len(self.blob):return
   if address==0x0201d578:self.copies.append(uc.reg_read(UC_ARM_REG_R0))
   elif address==0x0200604c:self.sounds.append(uc.reg_read(UC_ARM_REG_R0))
   elif address==0x0201d978:
    w=uc.reg_read(UC_ARM_REG_R0);color=uc.reg_read(UC_ARM_REG_R1)&255
    width,height=uc.mem_read(w+7,2);uc.mem_write(self.read(w+12),bytes([color])*(width*height*32))
   elif address in (0x020200fc,0x02002f30):
    string=uc.reg_read(UC_ARM_REG_R2 if address==0x020200fc else UC_ARM_REG_R1)
    length=struct.unpack('<H',uc.mem_read(string+2,2))[0]
    if address==0x02002f30:uc.reg_write(UC_ARM_REG_R0,length*6)
    else:
     value=struct.unpack('<%dH'%length,uc.mem_read(string+8,length*2))
     self.prints.append((uc.reg_read(UC_ARM_REG_R0),''.join(chr(c) for c in value),uc.reg_read(UC_ARM_REG_R3)))
   else:self.fail('unexpected native API seam '+hex(address))
   uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  self.u.hook_add(UC_HOOK_CODE,native);self.cursor(1,0,8,4,0)
 def write(self,address,value):self.u.mem_write(address,struct.pack('<I',value))
 def read(self,address):return struct.unpack('<I',self.u.mem_read(address,4))[0]
 def cursor(self,depth,category,row,scroll,page):self.u.mem_write(STATE+52,struct.pack('<5H',depth,category,row,scroll,page))
 def position(self):return struct.unpack('<5H',self.u.mem_read(STATE+52,10))
 def invoke(self,key=0,touch=None):
  self.write(0x021d1154,key)
  self.u.mem_write(0x021d116c,struct.pack('<HHH',*(touch or (0,0)),int(touch is not None)))
  self.u.reg_write(UC_ARM_REG_SP,0x02300000);self.u.reg_write(UC_ARM_REG_LR,0x02001001)
  self.u.reg_write(UC_ARM_REG_R0,0);self.u.reg_write(UC_ARM_REG_R1,0x02300100)
  self.returned=False;self.u.emu_start(self.symbols['guide_main'],0,count=3000000)
  self.assertTrue(self.returned,'guide_main must finish within the instruction bound')
  self.assertEqual(bytes(self.u.mem_read(STATE+240,16)),CANARY)
 def test_header_touch_matches_physical_jumps_and_keeps_visible_slot(self):
  for key,touch in ((256,None),(0,(208,0)),(0,(239,23))):
   with self.subTest(key=key,touch=touch):
    self.cursor(1,0,8,4,0);self.invoke(key,touch)
    self.assertEqual(self.position(),(1,0,13,9,0))
  for key,touch in ((512,None),(0,(16,0)),(0,(47,23))):
   with self.subTest(key=key,touch=touch):
    self.cursor(1,0,13,9,0);self.invoke(key,touch)
    self.assertEqual(self.position(),(1,0,8,4,0))
 def test_non_controls_and_short_or_category_headers_are_noops(self):
  for position in ((1,0,8,4,0),(1,1,2,0,0),(0,0,0,0,0)):
   touches=((15,0),(48,0),(207,23),(240,0)) if position[0]==1 and position[1]==0 else ((16,0),(208,23))
   for touch in touches:
    with self.subTest(position=position,touch=touch):
     self.cursor(*position);self.invoke(touch=touch);self.assertEqual(self.position(),position)
  self.assertEqual(self.copies,[]);self.assertEqual(self.sounds,[])
 def test_detail_header_link_and_b_restore_exact_origin(self):
  self.cursor(2,0,8,4,1);self.invoke(touch=(100,0))
  self.assertEqual(self.position(),(2,1,2,4,0));self.assertEqual(self.read(STATE+144),1)
  self.invoke(2);self.assertEqual(self.position(),(2,0,8,4,1));self.assertEqual(self.read(STATE+144),0)
 def test_b_wins_over_x_and_header_touch_before_following_or_jumping(self):
  for key,touch in ((2|1024,None),(2,(208,0))):
   with self.subTest(key=key,touch=touch):
    self.cursor(2,0,8,4,1);self.invoke(key,touch)
    self.assertEqual(self.position(),(1,0,8,4,1));self.assertEqual(self.read(STATE+144),0)
  self.cursor(2,0,8,4,1);self.invoke(1024);self.invoke(2|1024)
  self.assertEqual(self.position(),(2,0,8,4,1));self.assertEqual(self.read(STATE+144),0)
  self.cursor(1,0,8,4,0);self.invoke(2,touch=(208,0))
  self.assertEqual(self.position(),(0,0,8,4,0))
 def test_header_controls_dim_at_endpoints_and_title_uses_center_space(self):
  def pixel(x,y):
   offset=((y//8)*28+x//8)*32+(y%8)*4+(x%8)//2
   value=self.u.mem_read(0x02210000+offset,1)[0]
   return (value>>4) if x%2 else (value&15)
  # Down reaches row 0 and draws; the clamped left action then stays idle.
  self.cursor(1,0,1,0,0);self.invoke(64)
  self.assertEqual((pixel(1,2),pixel(193,2)),(2,1))
  self.assertEqual((pixel(8,6),pixel(214,6)),(1,15))
  self.assertIn((STATE+148,'Long category',73),self.prints)
  self.cursor(1,0,18,14,0);self.invoke(128)
  self.assertEqual((pixel(1,2),pixel(193,2)),(1,2))
  self.assertEqual((pixel(8,6),pixel(214,6)),(15,1))
 def test_page_plus_a_moves_without_opening_and_opposites_do_nothing(self):
  self.invoke(1|256);self.assertEqual(self.position(),(1,0,13,9,0))
  self.copies.clear();self.sounds.clear();self.invoke(1|256|512)
  self.assertEqual(self.position(),(1,0,13,9,0));self.assertEqual(self.copies,[]);self.assertEqual(self.sounds,[])
 def test_idle_and_clamped_input_do_not_upload_but_one_jump_uploads_four_windows(self):
  saved=bytes(range(80));self.u.mem_write(STATE+62,saved)
  for _ in range(32):self.invoke()
  self.cursor(1,0,0,0,0);self.invoke(512);self.invoke(touch=(16,0))
  self.cursor(1,0,19,15,0);self.invoke(256);self.invoke(touch=(239,0))
  self.assertEqual(self.copies,[]);self.assertEqual(self.sounds,[])
  self.invoke(512);self.assertEqual(self.position(),(1,0,14,10,0))
  self.assertEqual(self.copies,[STATE+148,STATE+164,STATE+180,STATE+196])
  self.assertEqual(len(self.sounds),1);self.assertEqual(bytes(self.u.mem_read(STATE+62,80)),saved)
  self.assertIn((STATE+196,'L/R: 5 entries',8),self.prints)

if __name__=='__main__':unittest.main()
