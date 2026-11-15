"""Portable source/dispatch qualification; no ROM or CPU required."""
from pathlib import Path
import importlib.util,types,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_nomi_chiamante.py';s=importlib.util.spec_from_file_location('species_composed_portable',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.x=tool()
 def test_exact_inherited_recipes_and_original_parent_unchanged(self):
  x=self.x;before=x.sha(Path(x.U.__file__).read_bytes());a,b,c,recipes=x.bindings();self.assertEqual(len(recipes),4);self.assertEqual([r['function'] for r in recipes],['Driver.collect_body','Driver.collect_body','run_case','require_case']);self.assertEqual(x.sha(Path(x.U.__file__).read_bytes()),before)
 def test_full_parent_hash_drift_rejected_before_derivation(self):
  x=self.x
  with patch.object(x.A,'PINS',dict(x.A.PINS,caller='0'*64)),self.assertRaisesRegex(ValueError,'parent source drift'):x.bindings()
 def test_unexpected_recipe_site_count_rejected(self):
  x=self.x
  with self.assertRaisesRegex(ValueError,'recipe occurrence'):x.A.rewrite(x.U,'Driver.collect_body',[('absent_marker','change',1)],{'__source_kind__':'caller'})
 def test_only_species_high_level_sdk_removed_in_isolated_namespace(self):
  x=self.x;old=dict(x.B.STUBS);d=types.SimpleNamespace(composition=x.V,parent=x.U,factory=None);run,receipt=x.A.adapt(x.B,d);self.assertEqual(x.B.STUBS,old);self.assertNotIn(x.W.ENTRY,run.__globals__['STUBS']);self.assertEqual(run.__globals__['STUBS'],{k:v for k,v in old.items() if k!=x.W.ENTRY});self.assertEqual(receipt['removed_high_level_sdk'],{'0x200bcdc':'GetSpeciesName'})
 def test_precise_name_span_union_keeps_holes_and_opaque_handle_frozen(self):
  x=self.x;d=x.Driver.__new__(x.Driver);d.name_results=[dict(allocations=[dict(pointer=x.NAME_ARENA+32,bytes=12),dict(pointer=x.NAME_ARENA+64,bytes=26)]),dict(allocations=[dict(pointer=x.NAME_ARENA+64,bytes=32)])];self.assertEqual(d.name_spans(),[(x.NAME_ARENA+24,x.NAME_ARENA+52),(x.NAME_ARENA+56,x.NAME_ARENA+98),(x.NAME_ARENA+56,x.NAME_ARENA+104)]);self.assertTrue(all(end<x.NAME_HANDLE for start,end in d.name_spans()))
 def test_unknown_composition_variant_refused_before_parent_or_cpu(self):
  x=self.x
  with patch.object(x.V.Driver,'__init__') as parent,self.assertRaisesRegex(ValueError,'finite species'):x.Driver(None,None,None,1,0,variant='unknown')
  parent.assert_not_called()
if __name__=='__main__':unittest.main()
