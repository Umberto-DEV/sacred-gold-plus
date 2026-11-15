"""Portable source/owner/borrowed-CPU qualification, without private inputs."""
from pathlib import Path
import importlib.util,types,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_lettore_prefisso.py';s=importlib.util.spec_from_file_location('prefix_portable',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.z=tool()
 def test_full_parent_source_pins(self):
  z=self.z;self.assertEqual(len(z.RECIPES),7)
  with patch.object(z.A,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'parent source drift'):z.A.bind(z.Y)
 def test_occurrence_drift_rejected(self):
  z=self.z
  with self.assertRaisesRegex(ValueError,'recipe occurrence'):z.A.rewrite(z.R,'require_case',[('missing_source','x',1)],{},'narc_reader')
 def test_no_standalone_execution_or_frame_initialization_in_snapshot(self):
  self.assertFalse({'setup','emu_start','reg_write','mem_write','Uc'}&set(self.z.prefix_snapshot.__code__.co_names))
 def test_borrow_existing_cpu_and_exact_three_context_constants(self):
  z=self.z;u=types.SimpleNamespace(reg_read=lambda register:0,mem_read=lambda address,n:bytes(n));d=types.SimpleNamespace(u=u,bench=types.SimpleNamespace(segments=[]),qualified={'header_code':{}},data={'header':{'56':{}}},poison=0xC7,observe=True,prefix_clobber=False,prefix_variant='current')
  with patch.object(z.R,'Uc') as factory:r=z.bind_reader(d)
  factory.assert_not_called();self.assertIs(r.u,u);self.assertEqual((r.service.__globals__['TOP'],r.service.__globals__['DEST'],r.service.__globals__['STOP']),(z.INNER-200,z.B.ARENA,0x226B4A6));self.assertEqual(z.R.TOP,0x23BF000)
 def test_effective_stubs_unchanged_from_header_composition(self):
  z=self.z;before=dict(z.B.STUBS);run,proof=z.A.adapt(z.B,types.SimpleNamespace(parent=z.U,composition=z.V,factory=None));self.assertEqual(z.B.STUBS,before);self.assertEqual(run.__globals__['STUBS'],{k:v for k,v in before.items() if k not in (z.R.ENTRY,z.X.W.ENTRY)});self.assertEqual(proof['inherited']['schema'],'native-header-caller-adapter-v1')
 def test_invalid_controls_refused_before_parent_setup(self):
  z=self.z
  for kwargs in (dict(variant='other'),dict(prefix_clobber=1)):
   with patch.object(z.Y.Driver,'__init__') as parent,self.assertRaisesRegex(ValueError,'finite native prefix'):z.Driver(None,None,None,1,0,**kwargs)
   parent.assert_not_called()
 def test_preimage_recipe_and_no_fake_prefix_event(self):
  z=self.z;edits=z.RECIPES[0]['edits'];self.assertEqual(len(edits),4);self.assertEqual(edits[-1]['after'],"[['alloc', 11, 108, B.ARENA], ['alloc', 11, 236, B.ARENA + 128]]");self.assertIn('stack_frame_before',z.require_prefix_native.__code__.co_consts);self.assertEqual(z.IP,z.B.ARENA+352)
 def test_short_read_counter_requires_same_payload_and_cursor_not_a5(self):
  edits=self.z.COUNTER_RECIPE['edits'];self.assertTrue(any("image==data['56']['member']"==e['after'] for e in edits));self.assertTrue(any("destination_before" in e['after'] for e in edits));self.assertEqual(sum(n for a,n in self.z.CANARIES),32)
if __name__=='__main__':unittest.main()
