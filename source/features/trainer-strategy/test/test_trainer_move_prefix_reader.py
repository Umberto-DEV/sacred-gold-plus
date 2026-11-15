"""Owned metadata gates for the first type3 move prefix; no ROM or CPU."""
from pathlib import Path
import importlib.util
import struct
import unittest


class PrefixReaderTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).parents[1]/'tools/rileggi_trainer_move_prefix.py';s=importlib.util.spec_from_file_location('owned_type3_prefix_reader',p);cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)
 def test_code_data_and_gate_stay_separate(self):
  self.assertEqual((sum(x[1]for x in self.L.THUMB.values()),sum(x[2]for x in self.L.THUMB.values())),(958,436))
  self.assertEqual(self.L.NEW_THUMB['trainer_prefix'][:3],(0x2073a22,30,14))
  self.assertEqual(self.L.NEW_THUMB['mon_veneer'][:3],(0x20714e8,4,2))
  self.assertEqual(self.L.NEW_DATA['mon_target'][:2],(0x20714ec,4));self.assertEqual(self.L.GATE[:2],(0x2073a40,2))
  self.assertTrue(all(not(a<=0x2073a40<a+n)for a,n,*rest in self.L.THUMB.values()))
 def test_typed_member_header_and_first_move(self):
  header=bytearray(20);header[0]=3;header[1]=72;header[3]=6
  record=bytearray(108);struct.pack_into('<HHHHH',record,2,27,355,0,310,109)
  info=self.L.record_layout(bytes(header),bytes(record),authenticate=False)
  self.assertEqual((info['stride'],info['count'],info['first_species'],info['first_level'],info['first_move'],info['move_offset']),(18,6,355,27,310,8))
 def test_no_type1_stride_or_trailer_silently_accepted(self):
  h=bytearray(20);h[0]=3;h[1]=72;h[3]=6;p=bytes(108)
  for header,member in((bytes([1])+bytes(h[1:]),p),(bytes(h),p+b'\0'),(bytes(h),p[:-1])):
   with self.assertRaises(ValueError):self.L.record_layout(header,member,authenticate=False)
 def test_record_types_hash_gate_and_bool_auth_mode(self):
  h=bytearray(20);h[0]=3;h[1]=72;h[3]=6
  for header,member in((h,bytes(108)),(bytes(h),bytearray(108))):
   with self.assertRaises(ValueError):self.L.record_layout(header,member,authenticate=False)
  with self.assertRaises(ValueError):self.L.record_layout(bytes(h),bytes(108))
  with self.assertRaises(ValueError):self.L.record_layout(bytes(h),bytes(108),authenticate=1)
 def test_fragment_disjointness_includes_literal_and_gate(self):
  regions={name:item[:2]for name,item in{**self.L.THUMB,**self.L.DATA}.items()};regions['gate']=self.L.GATE[:2]
  self.L.R.require_disjoint(regions)


if __name__=='__main__':unittest.main()
