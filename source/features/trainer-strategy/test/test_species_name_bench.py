"""CPU-free checks of the finite species SDK profile transformation."""
from pathlib import Path
import importlib.util,types,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Profile(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.m=load('message_parent',ROOT/'tools/attribuisci_messaggi.py');cls.a=load('species_profile',ROOT/'test/species_name_bench.py')
 def test_finite_species_domain_and_other_code_unchanged(self):
  m,a=self.m,self.a;bound,namespace,proof=a.profile(m);data=dict(oracle=dict(records={str(s):dict(words=[0x120,65535]) for s in a.SPECIES}))
  for species in a.SPECIES:self.assertEqual(bound(None,{},data,species).trainer,species)
  for species in (True,21,31,0,493):
   with self.assertRaises(ValueError):bound(None,{},data,species)
  for name,method in vars(m.Message).items():
   if isinstance(method,types.FunctionType) and name not in ('__init__','service'):self.assertIs(getattr(bound,name).__code__,method.__code__)
  self.assertEqual(proof['edits'],dict(fixture_domain=1,heap_constants=2,bank_constant=1));self.assertTrue(proof['all_other_AST_unchanged']);self.assertEqual(namespace['TOP'],m.TOP)
 def test_context_stack_binding_is_local(self):
  m=self.m;bound,namespace,_=self.a.profile(m);namespace['TOP']=m.TOP-16;self.assertEqual(bound.step.__globals__['TOP'],m.TOP-16);self.assertEqual(m.TOP,0x23BF000)
 def test_parent_drift_is_rejected(self):
  m,a=self.m,self.a;original=Path.read_bytes
  def read(p,*args,**kwargs):return b'drift' if p.resolve()==Path(m.__file__).resolve() else original(p,*args,**kwargs)
  with patch.object(Path,'read_bytes',autospec=True,side_effect=read),self.assertRaises(ValueError):a.profile(m)
if __name__=='__main__':unittest.main()
