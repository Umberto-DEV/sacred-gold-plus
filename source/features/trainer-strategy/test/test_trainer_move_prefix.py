"""Owned prefix entry/frame/tail contracts; no ROM or backend."""
from pathlib import Path
import importlib.util
import struct
import unittest


class PrefixFixtureTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).parents[1]/'tools/congela_trainer_move_prefix.py';s=importlib.util.spec_from_file_location('owned_prefix_fixture',p);cls.F=importlib.util.module_from_spec(s);s.loader.exec_module(cls.F)
 def test_actual_caller_geometry_is_relative_to_entry_inside_frame(self):
  f=self.F;self.assertEqual((f.TOP,f.SP,f.CALLER_FRAME,f.FRAME,f.GUARD),(0x23fd000,0x23fcf68,152,688,56))
  self.assertEqual((f.MOVE_VALUE,f.PP_VALUE,f.FILE,f.LOCAL,f.DEST),(0x23fcf5c,0x23fcf48,0x23fceb0,0x23fce98,0x23fcf20))
  self.assertEqual(f.TOP-(f.SP-f.FRAME-f.GUARD),896)
 def test_frame_pointer_and_distinct_cursor_not_precompleted(self):
  frame=self.F.caller_frame();self.assertEqual(len(frame),152)
  self.assertEqual(struct.unpack_from('<I',frame,0x64)[0],self.F.RECORD)
  self.assertEqual(struct.unpack_from('<I',frame,0x5c)[0],0xdeadc0de)
  self.assertNotEqual(0xdeadc0de,self.F.RECORD)
  self.assertEqual([i for i,b in enumerate(frame)if b!=0xa5],list(range(0x5c,0x60))+list(range(0x64,0x68)))
 def test_entry_has_real_mon_register_slot_cookie_and_non_gate_LR(self):
  r=self.F.entry_regs();self.assertEqual((len(r),r[6],r[13],r[15]),(16,self.F.BOX,self.F.SP,0x6000003f))
  self.assertNotEqual(r[7],0);self.assertNotEqual(r[14],self.F.RETURN|1)
  self.assertNotEqual(r[:3],[self.F.BOX,310,0])
 def test_tail100_is_owned_nonaccess_pattern_and_after_mon_guard(self):
  tail=self.F.owned_tail();self.assertEqual(len(tail),100);self.assertEqual(len(set(tail)),100)
  self.assertEqual((self.F.BOX+136,self.F.BOX+236),(0x22f0088,0x22f00ec))
  self.assertNotEqual(tail[:16],b'\xd3'*16)
 def test_box_fixture_reuses_exact_plain_PPUp_domain_without_compensation(self):
  for ups,key in((3,0x2ab),(0,0x2a8)):
   box,plain=self.F.P.owned_box(ups);self.assertEqual(struct.unpack_from('<H',box,6)[0],key)
   self.assertEqual(struct.unpack_from('<HH',plain),(355,0));self.assertEqual(plain[76],ups)


if __name__=='__main__':unittest.main()
