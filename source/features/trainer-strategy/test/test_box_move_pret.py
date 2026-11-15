"""Owned C-definition extraction counterexamples; no ROM/CPU/compiler."""
from pathlib import Path
import importlib.util
import unittest


class DefinitionTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).parents[1]/'tools/confronta_box_move_pret.py';s=importlib.util.spec_from_file_location('owned_C_definition',p);cls.C=importlib.util.module_from_spec(s);s.loader.exec_module(cls.C)
 def test_skips_earlier_prototype_and_nested_callsite(self):
  definition='void Target(int x) {\n if(x){x++;}\n}'
  text='void Target(int x);\nvoid Caller(void) {Target(1); if(1){Target(2);}}\n'+definition+'\n'
  self.assertEqual(self.C.definition(text,'Target')['text'],definition)
 def test_comment_string_and_character_braces_do_not_end_body(self):
  definition='const char *Target(void) {\n /* } */ char x=\'}\'; // }\n return "} { \\\"";\n}'
  text='/* void Target(void) { } */\n'+definition+'\n'
  self.assertEqual(self.C.definition(text,'Target')['text'],definition)
 def test_nested_callback_parameters_and_exact_final_newline_convention(self):
  text='static unsigned int Target(int (*f)(int))\n{\nreturn f(1);\n}\n\n'
  r=self.C.definition(text,'Target');self.assertEqual(r['text'],text[:-2]);self.assertEqual(r['bytes'],len(text[:-2].encode()));self.assertEqual(r['line'],1)
 def test_duplicate_definitions_rejected(self):
  with self.assertRaisesRegex(ValueError,'unique accepted global definition'):self.C.definition('void Target(void) {}\nvoid Target(int x) {}\n','Target')
 def test_missing_definition_and_only_calls_prototypes_rejected(self):
  for text in('void Target(void);\n','void Caller(void) {Target(); if(1){Target();}}\n','char *x="void Target(void) {}";\n'):
   with self.assertRaisesRegex(ValueError,'unique accepted global definition'):self.C.definition(text,'Target')
 def test_unterminated_comments_strings_and_braces_rejected(self):
  for text in('void Target(void) { /* missing','void Target(void) { "missing','void Target(void) {'):
   with self.assertRaises(ValueError):self.C.definition(text,'Target')
 def test_name_is_exact_identifier_and_input_types_are_strict(self):
  for text,name in((b'void X(void){}','X'),('void X(void){}','X('),('void X(void){}',''),('void XXX(void){}','X')):
   with self.assertRaises(ValueError):self.C.definition(text,name)
 def test_lines_offsets_and_raw_whitespace_are_preserved(self):
  text='// header\n\nvoid Target( int x )\n{\n  return;\n}\n';r=self.C.definition(text,'Target')
  self.assertEqual((r['line'],r['text']),(3,text[text.index('void'): -1]));self.assertEqual(text[r['start']:r['end']],r['text'])


if __name__=='__main__':unittest.main()
