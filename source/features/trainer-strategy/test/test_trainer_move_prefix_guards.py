"""Owned contextual owner and effective-namespace regressions, no ROM/CPU."""
from pathlib import Path
import importlib.util
import unittest


class PrefixGuardTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).with_name('trainer_move_prefix_bench.py');s=importlib.util.spec_from_file_location('owned_prefix_owner_guards',p);cls.B=importlib.util.module_from_spec(s);s.loader.exec_module(cls.B)
 def test_old_SDK_upper_frame_admission_is_blocked(self):
  b=self.B;a=b.F.SP+0x64
  self.assertTrue(b.parent_read(0x20d4b78,a,4))
  self.assertFalse(b.read_owner(0x20d4b78,a,4))
  self.assertFalse(b.read_owner(0x20d4b78,b.F.SP-2,4))
 def test_only_explicit_prefix_reads_own_upper_frame_and_record(self):
  b=self.B
  for pc,a,n in((0x2073a22,b.F.SP+0x64,4),(0x2073a28,b.F.SP+0x5c,4),(0x2073a36,b.F.SP+0x5c,4),(0x2073a2c,b.F.RECORD+8,2)):
   self.assertTrue(b.read_owner(pc,a,n));self.assertFalse(b.read_owner(pc,a+2,n));self.assertFalse(b.read_owner(pc,a,1))
  self.assertFalse(b.read_owner(0x2073a22,b.F.SP+0x50,4));self.assertFalse(b.read_owner(0x2073a2c,b.F.RECORD+6,2))
 def test_cursor_writes_and_veneer_literal_are_exact(self):
  b=self.B
  for pc in(0x2073a26,0x2073a3c):
   self.assertTrue(b.write_owner(pc,b.F.SP+0x5c,4));self.assertFalse(b.write_owner(pc,b.F.SP+0x64,4))
  self.assertFalse(b.write_owner(0x20d4b7c,b.F.SP+0x5c,4))
  self.assertTrue(b.read_owner(0x20714e8,0x20714ec,4));self.assertFalse(b.read_owner(0x20714e8,0x20725dc,4))
 def test_effective_parent_namespaces_preserve_all_other_bindings(self):
  b=self.B
  for old,new,changed in((b.P.read_owner,b.parent_read,{'R','F','BOX_GUARDS'}),(b.P.write_owner,b.parent_write,{'R','F','BOX_GUARDS'}),(b.P.causal_checks,b.child_checks,{'R','F','require_memory_delta'})):
   self.assertIs(old.__code__,new.__code__);self.assertEqual(old.__globals__.keys(),new.__globals__.keys())
   self.assertEqual({k for k in old.__globals__ if old.__globals__[k]is not new.__globals__[k]},changed)
  self.assertEqual(b.child_fixture.RETURN,0x2073a36);self.assertNotEqual(b.child_fixture.RETURN,b.F.RETURN)
  b.source_identity_guard()


if __name__=='__main__':unittest.main()
