"""Portable finite personal profile and borrowed-CPU checks."""
from pathlib import Path
import importlib.util,types,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_personale_chiamante.py';s=importlib.util.spec_from_file_location('personal_portable',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.z=tool()
 def test_parent_full_source_and_adapter_pins(self):
  z=self.z
  with patch.object(z.A,'ADAPTER_SHA256','0'*64),self.assertRaisesRegex(ValueError,'parent source drift'):z.A.bind(z.Z)
 def test_recipe_occurrence_drift_refused(self):
  z=self.z
  with self.assertRaisesRegex(ValueError,'recipe occurrence'):z.A.rewrite(z.R,'require_case',[('missing_personal_source','x',1)],{},'narc_reader')
 def test_exact_finite_narc2_member355_profile(self):
  z=self.z;self.assertEqual(z.RECIPES[0]['edits'],[dict(before='narc in (55,56)',after='narc==2',count=1)]);self.assertIn(dict(before='31',after='355',count=23),z.RECIPES[2]['edits']);self.assertEqual(sum(n for a,n in z.CANARIES),48)
 def test_snapshot_has_no_standalone_execution_or_fixture_writes(self):
  self.assertFalse({'setup','emu_start','reg_write','mem_write','Uc'}&set(self.z.personal_snapshot.__code__.co_names))
 def test_borrowed_cpu_and_exact_namespace(self):
  z=self.z;u=types.SimpleNamespace(reg_read=lambda register:0,mem_read=lambda address,n:bytes(n));d=types.SimpleNamespace(u=u,bench=types.SimpleNamespace(segments=[]),qualified={'header_code':{},'personal_data':()},data={'personal_reader':{'2':{}}},poison=0xC7,observe=True,personal_clobber=False,personal_variant='current')
  with patch.object(z.R,'Uc') as factory:r=z.bind_reader(d)
  factory.assert_not_called();self.assertIs(r.u,u);self.assertEqual((r.narc,r.service.__globals__['TOP'],r.service.__globals__['DEST'],r.service.__globals__['STOP']),(2,z.INNER-320,z.B.ARENA+384,0x206FAA2));self.assertEqual(z.R.TOP,0x23BF000)
 def test_effective_stub_table_unchanged_from_prefix(self):
  z=self.z;before=dict(z.B.STUBS);run,proof=z.A.adapt(z.B,types.SimpleNamespace(parent=z.U,composition=z.V,factory=None));self.assertEqual(z.B.STUBS,before);self.assertEqual(run.__globals__['STUBS'],{k:v for k,v in before.items() if k not in (z.R.ENTRY,z.X.W.ENTRY)});self.assertEqual(proof['inherited']['schema'],'native-prefix-caller-adapter-v1')
 def test_invalid_controls_refused_before_parent(self):
  z=self.z
  for kwargs in (dict(variant='other'),dict(personal_clobber=1)):
   with patch.object(z.Z.Driver,'__init__') as parent,self.assertRaisesRegex(ValueError,'finite personal caller'):z.Driver(None,None,None,1,0,**kwargs)
   parent.assert_not_called()
 def test_name_counter_projection_removes_only_transition_hashes(self):
  z=self.z;names=[dict(writes=[1],native_writes=[2],models=[3],transitions=[dict(neutral=True,ram_sha256='x')]) for _ in range(2)];copy=z.names_without_scope_hashes(names);self.assertEqual(copy,[dict(writes=[1],native_writes=[2],models=[3],transitions=[dict(neutral=True,ram_sha256='x')]),dict(writes=[1],native_writes=[2],models=[3],transitions=[dict(neutral=True)])]);self.assertEqual(names[0]['transitions'][0]['ram_sha256'],'x')
if __name__=='__main__':unittest.main()
