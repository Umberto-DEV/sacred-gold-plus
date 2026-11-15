"""Owned metadata contracts for full Mon setter62, no ROM or CPU."""
from pathlib import Path
import importlib.util
import unittest


class MonSetterReaderTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).parents[1]/'tools/rileggi_mon_ppup_setter.py';s=importlib.util.spec_from_file_location('owned_mon_setter_reader',p);cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)
 def test_complete_selected_code_counts(self):
  self.assertEqual((sum(x[1]for x in self.L.THUMB.values()),sum(x[2]for x in self.L.THUMB.values())),(372,173))
  self.assertEqual((sum(x[1]for x in self.L.NEW_THUMB.values()),sum(x[2]for x in self.L.NEW_THUMB.values())),(148,66))
 def test_outer_Box_wrapper_and_old_leaf_are_excluded(self):
  self.assertNotIn('setter_before_check',self.L.THUMB);self.assertNotIn('setter_valid',self.L.THUMB);self.assertNotIn('internal_leaf54_return',self.L.THUMB)
  starts=[a for a,n,count,d in self.L.THUMB.values()];self.assertIn(0x206ec40,starts);self.assertIn(0x206ede8,starts);self.assertIn(0x206f104,starts)
 def test_internal_switch_table_and_error_gap_not_admitted(self):
  for address in(0x206ec78,0x206ece8,0x206ed00,0x206ed70):
   self.assertFalse(any(a<=address<a+n for a,n,count,d in self.L.THUMB.values()))
  self.assertEqual(self.L.DATA['attribute_table'][:2],(0x206ee3c,376))
 def test_read_namespace_preserves_cipher_literal_postconditions(self):
  data=self.L.read.__globals__['DATA'];self.assertIn('wrapper_pool',data);self.assertIn('lcg_pool',data)
  self.assertIs(self.L.read.__code__,self.L.P.read.__code__)
 def test_code_data_are_disjoint(self):
  self.L.R.require_disjoint({name:item[:2]for name,item in{**self.L.THUMB,**self.L.DATA}.items()})


if __name__=='__main__':unittest.main()
