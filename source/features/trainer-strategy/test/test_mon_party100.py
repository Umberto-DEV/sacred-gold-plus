"""Owned100B/50-step math and qualification schema, no ROM or CPU."""
from pathlib import Path
import importlib.util
import unittest


class Party100MathTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).parents[1]/'tools/qualifica_mon_party100.py';s=importlib.util.spec_from_file_location('own100_math',p);cls.Q=importlib.util.module_from_spec(s);s.loader.exec_module(cls.Q)
 def test_plaintext_exact100_and_math50_seed_key_dependence(self):
  q=self.Q;p=q.owned_plaintext();self.assertEqual(len(p),100)
  cipher,seeds=q.crypt100(p,0x4000);self.assertEqual(len(seeds),50);self.assertEqual(q.crypt100(cipher,0x4000)[0],p)
  self.assertNotEqual(q.crypt100(p,0x2ab)[0],cipher)
 def test_owned_math_rejects_wrong_extent_seed_types(self):
  for blob,key in((bytes(98),0x4000),(bytes(102),0x4000),(bytearray(100),0x4000),(bytes(100),True),(bytes(100),-1),(bytes(100),2**32)):
   with self.assertRaises(ValueError):self.Q.crypt100(blob,key)
 def test_hard_loop_predicts_exact_flow_access_and_guard_owners(self):
  q=self.Q;f,code,stop=q.kernel(q.owned_plaintext(),0x4000);p=q.hard_prediction(f)
  self.assertEqual((len(code),len(p['flow']),len(p['reads']),len(p['stores'])),(10,451,50,50))
  self.assertEqual((p['returned'][0],p['returned'][15],p['stop_pc']),(q.BUFFER+100,0x6000003f,stop))
  self.assertEqual([x['address']for x in p['stores']],list(range(q.BUFFER,q.BUFFER+100,2)))
  for a,n in((q.BUFFER-16,16),(q.BUFFER+100,16)):
   self.assertEqual(q.M.read(p['pages'],a,n),q.M.read(f['pages'],a,n))
 def test_completed_expected_receipt_has_four_owned_cells_and_no_ROM(self):
  r=self.Q.expected_receipt();self.assertEqual(len(r['cases']),4);self.assertIs(r['ROM_loaded'],False)
  self.assertEqual([c['observed']for c in r['cases']],[True,True,True,False]);self.assertEqual({c['instructions']for c in r['cases']},{451})


if __name__=='__main__':unittest.main()
