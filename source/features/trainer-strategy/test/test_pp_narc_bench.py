"""Portable stack-reader/source guards and synthetic PP packet prediction."""
from pathlib import Path
import importlib.util,types,unittest,struct
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_pp_chiamante.py';s=importlib.util.spec_from_file_location('pp_portable',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.z=tool()
 def test_complete_parent_source_and_adapter_pins(self):
  z=self.z
  with patch.object(z.A,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'PP parent source drift'):z.A.bind(z.H)
 def test_recipe_occurrence_drift_refused(self):
  z=self.z
  with self.assertRaisesRegex(ValueError,'recipe occurrence'):z.A.rewrite(z.R,'Reader.run',[('missing_PP_source','x',1)],{},'narc_reader')
 def test_finite_narc11_without_service_cap_extension(self):
  z=self.z;self.assertEqual(len(z.RECIPES),8);self.assertEqual(z.RECIPES[0]['edits'],[dict(before='narc in (55,56)',after='narc==11',count=1)]);self.assertFalse(any(e['before']=='0<size<=108' for r in z.RECIPES for e in r['edits']))
 def test_stack_payload_and_upper_frame_do_not_enter_off_projection(self):
  z=self.z;self.assertEqual(z.TOP,z.DEST);self.assertEqual(z.TOP,z.INNER-224);self.assertEqual(z.OUTER-(z.TOP-136),456);self.assertEqual(z.OUTER-(z.TOP-192),512);self.assertEqual(len(z.ALLOCATIONS),14);self.assertEqual(sum(n for a,n in z.CANARIES),224);self.assertEqual(sum(n for a,n in z.DEAD),900);self.assertEqual(sum(b-a for a,b in z.PROJECTION),1124);self.assertTrue(all(b<=z.TOP-192 or a>=z.TOP+32 for a,b in z.PROJECTION))
 def test_snapshot_never_initializes_or_executes_a_standalone_cpu(self):
  self.assertFalse({'setup','emu_start','reg_write','mem_write','Uc'}&set(self.z.pp_snapshot.__code__.co_names))
 def test_borrows_existing_cpu_and_keeps_parent_constants(self):
  z=self.z;u=types.SimpleNamespace(reg_read=lambda register:0,mem_read=lambda address,n:bytes(n));d=types.SimpleNamespace(u=u,bench=types.SimpleNamespace(segments=[]),qualified={'header_code':{},'pp_data':()},data={'pp_reader':{'11':{}}},poison=0xC7,observe=True,pp_clobber=False,pp_variant='current')
  with patch.object(z.R,'Uc') as factory:r=z.bind_reader(d)
  factory.assert_not_called();self.assertIs(r.u,u);self.assertEqual((r.narc,r.service.__globals__['TOP'],r.service.__globals__['DEST'],r.service.__globals__['STOP']),(11,z.INNER-224,z.INNER-224,0x2073320));self.assertEqual(z.R.TOP,0x23BF000)
 def test_effective_sdk_stubs_and_complete_constructor_bytecode(self):
  z=self.z;before=dict(z.B.STUBS);original_expected=z.T.expected;run,proof=z.A.adapt(z.B,types.SimpleNamespace(parent=z.U,composition=z.V,factory=None));fn=z.A.counter_result_oracle();old=z.V.A.constructor_result
  self.assertEqual(z.B.STUBS,before);self.assertEqual(run.__globals__['STUBS'],{k:v for k,v in before.items() if k not in (z.R.ENTRY,z.X.W.ENTRY)});self.assertIs(fn.__code__,old.__code__);self.assertIs(fn.__defaults__,old.__defaults__);self.assertIs(fn.__closure__,old.__closure__);self.assertEqual([k for k,v in old.__globals__.items() if fn.__globals__[k]is not v],['T']);self.assertIs(fn.__globals__['T'].M,z.T.M);self.assertIs(z.T.expected,original_expected)
 def test_counter_complete_result_source_drift_refused(self):
  z=self.z
  with patch.object(z.A,'RESULT_SOURCE_SHA256','0'*64),self.assertRaisesRegex(ValueError,'result source drift'):z.A.counter_result_oracle()
 def test_invalid_driver_controls_refused_before_parent(self):
  z=self.z
  for kwargs in (dict(variant='other'),dict(pp_clobber=1)):
   with patch.object(z.H.Driver,'__init__') as parent,self.assertRaisesRegex(ValueError,'finite custom PP controls'):z.Driver(None,None,None,1,0,**kwargs)
   parent.assert_not_called()
 def test_positive_refuses_any_counter_expectation_flag(self):
  z=self.z
  for value in (None,False,0,True,1,2):
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,'no value shadow or counter expectation'):z.require_case({},dict(pp_expected_slot0=value),{})
 def test_counter_flag_is_strict_integer_one(self):
  z=self.z
  for value in (None,False,0,True,2):
   with self.subTest(value=value),self.assertRaisesRegex(ValueError,'finite PP semantic expectation flag'):z.A.constructor_result({},dict(pp_expected_slot0=value),{})
 def test_synthetic_packet_changes_only_pp_and_checksum_ciphertext(self):
  z=self.z;raw=bytearray(236);plain=bytearray(128);plain[32+8]=15;struct.pack_into('<IHH',raw,0,0,0,15);raw[8:136]=z.B._decrypt(plain,15);raw[136:]=z.B._decrypt(bytes(range(100)),0);changed=bytes.fromhex(z.expected_pp_packet(raw.hex(),1));decoded=z.B._decrypt(changed[8:136],struct.unpack_from('<H',changed,6)[0]);want=bytearray(plain);want[32+8]=1;self.assertEqual(decoded,bytes(want));self.assertEqual(changed[:6],raw[:6]);self.assertEqual(changed[136:],raw[136:]);self.assertEqual(struct.unpack_from('<H',changed,6)[0],1)
if __name__=='__main__':unittest.main()
