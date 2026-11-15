"""Portable finitefriendship44-byte profile and borrowed-CPU source guards."""
from pathlib import Path
import importlib.util,types,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_amicizia_chiamante.py';s=importlib.util.spec_from_file_location('friendship_portable',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.z=tool()
 def test_full_parent_source_and_adapter_pins(self):
  z=self.z
  with patch.object(z.A,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'parent source drift'):z.A.bind(z.G)
 def test_exact_recipe_occurrence_drift_rejected(self):
  z=self.z
  with self.assertRaisesRegex(ValueError,'recipe occurrence'):z.A.rewrite(z.R,'Reader.service',[('missing_growth_source','x',1)],{},'narc_reader')
 def test_finite_personal44_and_independent_owned_recipe(self):
  z=self.z;self.assertEqual(len(z.RECIPES),7);self.assertEqual(z.RECIPES[0]['edits'],[dict(before='narc in (55,56)',after='narc==2',count=1)]);payload=z.emit_postform();self.assertEqual(len(payload),50);self.assertEqual(z.sha(payload),'219412a0140b9076f367d53bb22bc0a80ddc1806d68d99f3a9a8f1b9e89de2e3');self.assertEqual(payload[46:],bytes.fromhex('c046c046'))
 def test_exact528_byte_off_projection_and_live44_not_masked(self):
  z=self.z;self.assertEqual(sum(n for a,n in z.CANARIES),80);self.assertEqual(sum(b-a for a,b in z.PROJECTION),528);self.assertEqual(z.TOP,z.INNER-312);self.assertTrue(all(b<=z.DEST or a>=z.DEST+44 for a,b in z.PROJECTION));self.assertEqual(z.DEAD,((z.J.DEST,44),(z.G.DEST,404)))
 def test_snapshot_has_no_standalone_execution_or_memory_initialization(self):
  self.assertFalse({'setup','emu_start','reg_write','mem_write','Uc'}&set(self.z.friendship_snapshot.__code__.co_names))
 def test_existing_cpu_borrowed_without_factory(self):
  z=self.z;u=types.SimpleNamespace(reg_read=lambda register:0,mem_read=lambda address,n:bytes(n));d=types.SimpleNamespace(u=u,bench=types.SimpleNamespace(segments=[]),qualified={'header_code':{},'personal_data':()},data={'personal_reader':{'2':{}}},poison=0xC7,observe=True,friendship_clobber=False,friendship_variant='current')
  with patch.object(z.R,'Uc') as factory:r=z.bind_reader(d)
  factory.assert_not_called();self.assertIs(r.u,u);self.assertEqual((r.narc,r.service.__globals__['TOP'],r.service.__globals__['DEST'],r.service.__globals__['STOP']),(2,z.INNER-312,z.B.ARENA+872,0x206FAA2));self.assertEqual(z.R.TOP,0x23BF000)
 def test_effective_stubs_unchanged_from_personal_composition(self):
  z=self.z;before=dict(z.B.STUBS);run,proof=z.A.adapt(z.B,types.SimpleNamespace(parent=z.U,composition=z.V,factory=None));self.assertEqual(z.B.STUBS,before);self.assertEqual(run.__globals__['STUBS'],{k:v for k,v in before.items() if k not in (z.R.ENTRY,z.X.W.ENTRY)});self.assertEqual(proof['inherited']['schema'],'native-growth-caller-adapter-v1')
 def test_invalid_controls_refused_before_parent(self):
  z=self.z
  for kwargs in (dict(variant='other'),dict(friendship_clobber=1)):
   with patch.object(z.G.Driver,'__init__') as parent,self.assertRaisesRegex(ValueError,'finite friendship controls'):z.Driver(None,None,None,1,0,**kwargs)
   parent.assert_not_called()
 def test_lineage_full50_includes_previous_uncovered_padding(self):
  import struct
  p=SOURCE/'features/trainer-strategy/tools/rileggi_helper_amicizia.py';spec=importlib.util.spec_from_file_location('helper_portable',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);recipe=m.recipe;rows={recipe.FORM_STATS_HELPER:recipe.FORM_STATS_BEFORE}
  for sites,target in ((recipe.FORM_SETTERS,recipe.SET_MON_DATA),(recipe.FRIENDSHIP_CALLERS,recipe.FORM_STATS_HELPER)):
   for pc in sites:
    delta=(target-pc-4)//2;rows[pc]=struct.pack('<HH',0xF000|((delta>>11)&0x7FF),0xF800|(delta&0x7FF))
  with patch.object(m.P.G,'piece',side_effect=lambda segments,address,n:rows[address]):
   result=m.component({'segments':[]},None,'base11');self.assertEqual(result['read_bytes'],82);self.assertEqual(len(result['callers']),8);self.assertIsNone(result['helper']['rom_offset']);self.assertFalse(result['cpu_executed']);changed=bytearray(rows[recipe.FORM_STATS_HELPER]);changed[-1]^=1;rows[recipe.FORM_STATS_HELPER]=bytes(changed)
   with self.assertRaisesRegex(ValueError,'full50'):m.component({'segments':[]},None,'base11')
 def test_lineage_rejects_valid_bl_to_wrong_callee(self):
  import struct
  p=SOURCE/'features/trainer-strategy/tools/rileggi_helper_amicizia.py';spec=importlib.util.spec_from_file_location('helper_branch_portable',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);recipe=m.recipe;rows={recipe.FORM_STATS_HELPER:recipe.FORM_STATS_BEFORE}
  for sites,target in ((recipe.FORM_SETTERS,recipe.SET_MON_DATA),(recipe.FRIENDSHIP_CALLERS,recipe.FORM_STATS_HELPER)):
   for pc in sites:
    delta=(target-pc-4)//2;rows[pc]=struct.pack('<HH',0xF000|((delta>>11)&0x7FF),0xF800|(delta&0x7FF))
  rows[recipe.FORM_SETTERS[0]]=rows[recipe.FORM_SETTERS[1]]
  with patch.object(m.P.G,'piece',side_effect=lambda segments,address,n:rows[address]),self.assertRaisesRegex(ValueError,'BL target'):m.component({'segments':[]},None,'retail')
if __name__=='__main__':unittest.main()
