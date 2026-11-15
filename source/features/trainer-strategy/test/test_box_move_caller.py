"""Owned caller Box/fixture boundaries; no ROM or CPU backend."""
from pathlib import Path
import importlib.util
import struct
import unittest


class CallerFixtureTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).parents[1]/'tools/congela_box_move_caller.py';s=importlib.util.spec_from_file_location('caller_fixture_test',p);cls.F=importlib.util.module_from_spec(s);s.loader.exec_module(cls.F)
 def test_own_box_zero_does_not_compensate_held_item(self):
  for ups,key in((0,0x2a8),(3,0x2ab)):
   box,plain=self.F.owned_box(ups);self.assertEqual(len(box),136);self.assertEqual(len(plain),128)
   self.assertEqual(struct.unpack_from('<HH',plain),(355,0));self.assertEqual(struct.unpack_from('<H',box,6)[0],key)
   self.assertEqual((struct.unpack_from('<H',plain,64)[0],plain[72],plain[76]),(310,15,ups))
 def test_only_PPUp_semantic_input_changes(self):
  a=self.F.owned_box(3)[1];b=self.F.owned_box(0)[1]
  self.assertEqual([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y],[(76,3,0)])
 def test_strict_owned_domain(self):
  for v in(True,False,None,1,2,4,3.0):
   with self.assertRaises(ValueError):self.F.owned_box(v)
 def test_independent_cipher_roundtrip_and_checksum(self):
  for ups in(0,3):
   box,plain=self.F.owned_box(ups);key=struct.unpack_from('<H',box,6)[0];seed=key;out=bytearray()
   for value, in struct.iter_unpack('<H',box[8:]):
    seed=(seed*1103515245+24691)&0xffffffff;out.extend(struct.pack('<H',value^(seed>>16)))
   self.assertEqual(bytes(out),plain);self.assertEqual(sum(x[0]for x in struct.iter_unpack('<H',plain))&65535,key)
 def test_real_stack_slots_and_no_shadow_value(self):
  self.assertEqual((self.F.ENTRY,self.F.FRAME,self.F.GUARD),(0x20714f0,688,56))
  self.assertEqual((self.F.MOVE_VALUE,self.F.PP_VALUE,self.F.FILE,self.F.LOCAL,self.F.DEST),tuple(self.F.R.TOP-n for n in(12,32,184,208,72)))
  self.assertFalse(hasattr(self.F,'VALUE'))


if __name__=='__main__':unittest.main()
