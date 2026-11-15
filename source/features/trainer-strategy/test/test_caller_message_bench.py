"""CPU-free checks for exact adapter edits and copied oracle authentication."""
from pathlib import Path
import ast,importlib.util,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class Adapter(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.u=load(ROOT/'tools/attribuisci_chiamante.py','caller_parent');cls.a=load(ROOT/'test/caller_message_bench.py','message_adapter')
 def test_exact_namespace_removes_only_three_high_level_stubs(self):
  u,a=self.u,self.a;before=dict(u.B.STUBS);driver=type('Driver',(),dict(parent=u,factory=None))();run,proof=a.adapt(u.B,driver)
  self.assertEqual(run.__globals__['STUBS'],before);self.assertIsNot(run.__globals__['STUBS'],u.B.STUBS);self.assertEqual(u.B.STUBS,before)
  self.assertEqual(set(proof['removed_high_level_sdk']),{'0x200baf8','0x200bba0','0x200bb44'});self.assertTrue(proof['constructor_oracle']['complete_wrappers_authenticated'])
 def test_whole_function_guards_reject_bypass_and_body_drift(self):
  a,u=self.a,self.u;original=Path.read_text;path=Path(a.__file__).resolve();text=original(path)
  for target,position in (('constructor_result',0),('constructor_result',1),('constructor_evidence',0),('constructor_evidence',1)):
   tree=ast.parse(text);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==target);f.body[position]=ast.Return(ast.Constant(True));forged=ast.unparse(tree)
   def read(p,*args,**kwargs):return forged if p.resolve()==path else original(p,*args,**kwargs)
   with self.subTest(target=target,position=position),patch.object(Path,'read_text',autospec=True,side_effect=read),self.assertRaises(ValueError):a.bind(u)
  self.assertTrue(a.bind(u)['all_copied_AST_unchanged'])
 def test_parent_drift_is_rejected_before_global_binding(self):
  a,u=self.a,self.u;a.bind(u);before=a.U;original=Path.read_bytes
  def read(p,*args,**kwargs):return b'drift' if p.resolve()==Path(u.__file__).resolve() else original(p,*args,**kwargs)
  with patch.object(Path,'read_bytes',autospec=True,side_effect=read),self.assertRaises(ValueError):a.bind(u)
  self.assertIs(a.U,before)
if __name__=='__main__':unittest.main()
