"""Owned linked prefix/veneer/target and excluded-gate lineage fixtures."""
from pathlib import Path
import importlib.util
import struct
import types
import unittest


class PrefixLineageTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).parents[1]/'tools/rileggi_trainer_move_lineage.py';s=importlib.util.spec_from_file_location('owned_prefix_lineage',p);cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)
 def fixture(self):
  entry,veneer,box=0x1000,0x1100,0x1200;prefix=bytearray(range(30));delta=veneer-(entry+16+4)
  prefix[16:20]=struct.pack('<HH',0xf000|((delta>>12)&0x7ff),0xf800|((delta>>1)&0x7ff))
  current=dict(trainer_prefix=bytes(prefix),mon_veneer=bytes.fromhex('004b1847'),mon_target=struct.pack('<I',box|1),prefix_gate=bytes.fromhex('f2db'),box_caller=bytes(range(66)))
  data=bytearray(b'\xa5'*4096)
  for name,a in(('trainer_prefix',entry),('prefix_gate',entry+30),('mon_veneer',veneer),('mon_target',veneer+4),('box_caller',box)):data[a-entry:a-entry+len(current[name])]=current[name]
  return types.SimpleNamespace(ramAddress=entry,data=data),current
 def test_linked_bounded_components_and_actual_targets(self):
  section,current=self.fixture();result=self.L.components([section],current)
  self.assertEqual(result['prefix'],0x1000);self.assertEqual(result['veneer'],0x1100);self.assertEqual(result['box_caller'],0x1200)
  self.assertEqual(sum(len(b)for a,b,o in result['parts'].values()),106)
  self.assertEqual(result['gate_target'],0x1006)
 def test_unique_even_prefix_missing_odd_duplicate(self):
  section,current=self.fixture();self.assertEqual(self.L.locate_prefix([section],current['trainer_prefix']),0x1000)
  for sections in([], [types.SimpleNamespace(ramAddress=0x1001,data=current['trainer_prefix'])], [section,section]):
   with self.assertRaises(ValueError):self.L.locate_prefix(sections,current['trainer_prefix'])
 def test_real_thumb_target_bit_is_required(self):
  section,current=self.fixture();section.data[0x104:0x108]=struct.pack('<I',0x1200)
  with self.assertRaisesRegex(ValueError,'Thumb veneer literal'):self.L.components([section],current)
 def test_changed_target_bytes_are_preserved_as_difference(self):
  section,current=self.fixture();section.data[0x200]^=1
  result=self.L.components([section],current);self.assertNotEqual(result['parts']['box_caller'][1],current['box_caller'])
  self.assertEqual(result['parts']['mon_target'][1],current['mon_target'])
 def test_gate_layout_change_and_overlapping_owner_rejected(self):
  section,current=self.fixture();section.data[30:32]=bytes.fromhex('00e0')
  with self.assertRaisesRegex(ValueError,'excluded LT branch gate'):self.L.components([section],current)
  section,current=self.fixture();other=types.SimpleNamespace(ramAddress=0x1100,data=bytes(section.data[0x100:0x108]))
  with self.assertRaises(ValueError):self.L.components([section,other],current)


if __name__=='__main__':unittest.main()
