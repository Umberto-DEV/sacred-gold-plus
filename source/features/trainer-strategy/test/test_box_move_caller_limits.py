"""Owned strict limits and source deltas; no ROM or CPU execution."""
from pathlib import Path
import importlib.util
import inspect
import unittest


def load(name):
 p=Path(__file__).with_name(name+'.py');s=importlib.util.spec_from_file_location('limits_'+name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class CallerLimitTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.A=load('arm_thumb_box_caller_oracle');cls.C=load('box_move_caller_cpu')
 def fixture(self):
  pages={0x1000:bytearray(b'\xa5'*4096)};pages[0x1000][:2]=bytes.fromhex('7047')
  return dict(entry_pc=0x1000,entry_regs=[0]*13+[0x4000,0x1101,0x3f],pages={a:bytes(b)for a,b in pages.items()})
 def test_caps_strict_integer_domain(self):
  for cap in(True,False,0,-1,32769,32768.0,None):
   with self.assertRaisesRegex(ValueError,'finite mixed instruction cap'):self.A.run(self.fixture(),(),0x1100,cap,thumb_code={0x1000:bytes.fromhex('7047')})
 def test_default_32768_smallcap_and_no_input_mutation(self):
  f=self.fixture();before=repr(f);r=self.A.run(f,(),0x1100,1,thumb_code={0x1000:bytes.fromhex('7047')})
  self.assertEqual((len(r['flow']),r['stop_pc'],repr(f)),(1,0x1100,before));self.assertEqual(inspect.signature(self.A.run).parameters['cap'].default,32768)
 def test_source_guard_and_exact_three_AST_changes(self):
  self.A.source_identity_guard();self.assertEqual(self.A.audit_source_delta(),3)
  old=self.A.P.run.__globals__;new=self.A.run.__globals__
  self.assertEqual(old.keys(),new.keys());self.assertEqual({k for k in old if new[k]is not old[k]},{'source_identity_guard'})
  self.assertIs(new['select_arm'],old['select_arm']);self.assertIs(new['thumb_step'],old['thumb_step'])
 def test_source_cap_loop_rejects(self):
  f=self.fixture();p=bytearray(f['pages'][0x1000]);p[:2]=bytes.fromhex('fee7');f['pages']={0x1000:bytes(p)}
  with self.assertRaisesRegex(ValueError,'mixed instruction budget'):self.A.run(f,(),0x1100,cap=2,thumb_code={0x1000:bytes.fromhex('fee7')})
 def test_producer_exact_two_literals_and_fixed_single_start(self):
  self.C.source_identity_guard();self.assertEqual(self.C.audit_source_delta(),2)
  text=inspect.getsource(self.C._run_cpu);self.assertEqual(text.count('emu_start('),1);self.assertIn('count=32768',text);self.assertIn('timeout=1000000',text)
 def test_completion_requires_observed_gate_and_spare_callback(self):
  for steps,raw in((32768,dict(stopped=True,executed_count=32768,callback_count=32769)),(32767,dict(stopped=False,executed_count=32767,callback_count=32767)),(True,dict(stopped=True,executed_count=1,callback_count=2))):
   with self.assertRaises(ValueError):self.C.require_completion(raw,steps)
  self.C.require_completion(dict(stopped=True,executed_count=32767,callback_count=32768),32767)


if __name__=='__main__':unittest.main()
