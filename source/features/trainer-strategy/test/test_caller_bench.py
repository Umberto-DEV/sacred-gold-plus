"""Qualify the bounded SDK-model adapter without creating a CPU."""
from pathlib import Path
import importlib.util,inspect,textwrap,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
def modules():
 s=importlib.util.spec_from_file_location('caller_adapter',HERE/'caller_bench.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
 s=importlib.util.spec_from_file_location('constructor_parent',HERE.parent/'tools/attribuisci_costruttore.py');t=importlib.util.module_from_spec(s);s.loader.exec_module(t);return a,t.B

class QualifiedAdapter(unittest.TestCase):
 def test_original_sdk_helpers_preserved_and_namespace_is_private(self):
  a,b=modules();factory=object();driver=type('Driver',(),dict(factory=factory))();before=(b.ENTRY,b.STACK_TOP,b.GF_ASSERT,b.WFC_HOOK,b.STUBS.copy(),b.Uc);run,proof=a.adapt(b,driver)
  self.assertEqual(proof['transformations'],dict(configure=1,prepare=1,argument=1));self.assertEqual(len(proof['nested_function_ast_sha256']),19);self.assertTrue(proof['all_other_ast_unchanged']);self.assertEqual(run.__globals__['ENTRY'],0x20733C0);self.assertEqual(run.__globals__['STACK_TOP'],0x23BF000);self.assertIs(run.__globals__['Uc'],factory);self.assertEqual((run.__globals__['GF_ASSERT'],run.__globals__['WFC_HOOK']),(0x23BE100,0x23BE104));self.assertEqual((b.ENTRY,b.STACK_TOP,b.GF_ASSERT,b.WFC_HOOK,b.STUBS,b.Uc),before)
 def test_adapter_is_reproducible_without_a_cpu_or_rom(self):
  a,b=modules();factory=lambda *args:(_ for _ in ()).throw(AssertionError('CPU must not be created'));driver=type('Driver',(),dict(factory=staticmethod(factory)))();first=a.adapt(b,driver)[1];second=a.adapt(b,driver)[1];self.assertEqual(first,second)
 def test_any_source_change_including_sdk_model_or_argument_is_refused(self):
  a,b=modules();source=textwrap.dedent(inspect.getsource(b.Bench.run));driver=type('Driver',(),dict(factory=None))()
  for mutant in (source+'\n',source.replace('member_data = buffer','member_data = b""'),source.replace('(SETUP, index, 11)','(SETUP, index, 12)'),source.replace("log(uc, 'free', reg(uc, 0))","log(uc, 'free', 0)"),source.replace('cpu.mem_write(STACK_TOP, STACK_CANARY)','pass')):
   self.assertNotEqual(mutant,source)
   with self.assertRaisesRegex(ValueError,'run source drift'):a.adapt(b,driver,source=mutant)
 def test_parent_file_and_runtime_constants_are_independently_checked(self):
  a,b=modules();driver=type('Driver',(),dict(factory=None))()
  with patch.object(a,'PARENT_SHA256','0'*64),self.assertRaisesRegex(ValueError,'parent source drift'):a.adapt(b,driver)
  for key,value in (('ENTRY',0x20733C0),('STACK_TOP',0x23BEFA0)):
   with patch.object(b,key,value),self.assertRaisesRegex(ValueError,'original constructor constants'):a.adapt(b,driver)
 def test_extra_sdk_collision_is_refused(self):
  a,b=modules();driver=type('Driver',(),dict(factory=None))()
  with patch.dict(b.STUBS,{0x200BBA0:'wrong'}),self.assertRaisesRegex(ValueError,'SDK address collision'):a.adapt(b,driver)

if __name__=='__main__':unittest.main()
