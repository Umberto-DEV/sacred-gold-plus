"""Portable finite404-byte profile and borrowed-CPU source guards."""
from pathlib import Path
import importlib.util,types,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_crescita_chiamante.py';s=importlib.util.spec_from_file_location('growth_portable',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.z=tool()
 def test_full_parent_source_and_adapter_pins(self):
  z=self.z
  with patch.object(z.A,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'parent source drift'):z.A.bind(z.J)
 def test_exact_recipe_occurrence_drift_rejected(self):
  z=self.z
  with self.assertRaisesRegex(ValueError,'recipe occurrence'):z.A.rewrite(z.R,'Reader.service',[('missing_growth_source','x',1)],{},'narc_reader')
 def test_finite_narc3_and404_cap_are_separate_authenticated_edits(self):
  z=self.z;self.assertEqual(len(z.RECIPES),9);self.assertEqual(z.RECIPES[0]['edits'],[dict(before='narc in (55,56)',after='narc==3',count=1)]);self.assertEqual(z.RECIPES[1]['edits'],[dict(before='0<size<=108',after='0<size<=404',count=1)])
 def test_exact108_byte_off_projection_and_immutable_gaps(self):
  z=self.z;self.assertEqual(sum(n for a,n in z.CANARIES),64);self.assertEqual(z.PROJECTION[-1],(z.J.DEST,z.J.DEST+44));self.assertEqual(sum(b-a for a,b in z.PROJECTION),108);self.assertEqual(z.TOP,z.INNER-320)
 def test_snapshot_has_no_standalone_execution_or_memory_initialization(self):
  self.assertFalse({'setup','emu_start','reg_write','mem_write','Uc'}&set(self.z.growth_snapshot.__code__.co_names))
 def test_existing_cpu_borrowed_without_factory(self):
  z=self.z;u=types.SimpleNamespace(reg_read=lambda register:0,mem_read=lambda address,n:bytes(n));d=types.SimpleNamespace(u=u,bench=types.SimpleNamespace(segments=[]),qualified={'header_code':{},'growth_data':()},data={'growth_reader':{'3':{}}},poison=0xC7,observe=True,growth_clobber=False,growth_variant='current')
  with patch.object(z.R,'Uc') as factory:r=z.bind_reader(d)
  factory.assert_not_called();self.assertIs(r.u,u);self.assertEqual((r.narc,r.service.__globals__['TOP'],r.service.__globals__['DEST'],r.service.__globals__['STOP']),(3,z.INNER-320,z.B.ARENA+448,0x206FD2C));self.assertEqual(z.R.TOP,0x23BF000)
 def test_effective_stubs_unchanged_from_personal_composition(self):
  z=self.z;before=dict(z.B.STUBS);run,proof=z.A.adapt(z.B,types.SimpleNamespace(parent=z.U,composition=z.V,factory=None));self.assertEqual(z.B.STUBS,before);self.assertEqual(run.__globals__['STUBS'],{k:v for k,v in before.items() if k not in (z.R.ENTRY,z.X.W.ENTRY)});self.assertEqual(proof['inherited']['schema'],'native-personal-caller-adapter-v1')
 def test_invalid_controls_refused_before_parent(self):
  z=self.z
  for kwargs in (dict(variant='other'),dict(growth_clobber=1)):
   with patch.object(z.J.Driver,'__init__') as parent,self.assertRaisesRegex(ValueError,'finite growth caller'):z.Driver(None,None,None,1,0,**kwargs)
   parent.assert_not_called()
if __name__=='__main__':unittest.main()
