"""Owned source/prototype/guest-linkage counterexamples; no references or CC."""
from pathlib import Path
import importlib.util
import unittest


class ResetCSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/compila_reset_c.py';s=importlib.util.spec_from_file_location('Reset_C_source_tests',p)
        cls.T=importlib.util.module_from_spec(s);s.loader.exec_module(cls.T)
    def test_only_global_declaration_not_comment_or_local(self):
        line='u8 GetMoveMaxPP(u16 moveId, u8 ppUps);'
        text='/*\n'+line+'\n*/\nvoid f(void) {\n'+line+'\n}\n'+line+'\n'
        self.assertEqual(self.T.exact_global(text,line),line)
        with self.assertRaises(ValueError):self.T.exact_global(text+line+'\n',line)
        with self.assertRaises(ValueError):self.T.exact_global('void f(void) {\n'+line+'\n}\n',line)
    def test_GetMoveMaxPP_int_return_cannot_replace_u8_ABI(self):
        with self.assertRaises(ValueError):self.T.exact_global('int GetMoveMaxPP(u16 moveId, u8 ppUps);\n',self.T.PROTOTYPES['GetMoveMaxPP'][1])
    def test_body_drift_is_rejected_before_codegen(self):
        for body in('void other(void) {}','x'*290,'x'*291):
            with self.assertRaises(ValueError):self.T.validate_body(body)
    def test_wrapper_preserves_owned_body_literally_and_no_function_macro(self):
        body='void own_example(Pokemon *mon, u16 move, u8 slot) { (void)mon; (void)move; (void)slot; }'
        tu=self.T.make_tu(body)
        self.assertEqual(tu.count(body),1)
        self.assertIn('typedef unsigned short int u16;',tu)
        self.assertIn('typedef struct Pokemon Pokemon;',tu)
        for symbol in self.T.TARGETS:self.assertNotIn('#define '+symbol,tu)
    def test_thunk_targets_are_exact_odd_native_entries(self):
        self.T.validate_targets(dict(self.T.TARGETS))
        for name in self.T.TARGETS:
            bad=dict(self.T.TARGETS);bad[name]&=~1
            with self.assertRaises(ValueError):self.T.validate_targets(bad)
        bad=dict(self.T.TARGETS);bad['MonSetMoveInSlot']=0x20714b1
        with self.assertRaises(ValueError):self.T.validate_targets(bad)
    def test_fixed_recipe_disables_sibling_calls_and_uses_ARM946_Thumb(self):
        for flag in('--target=armv5te-none-eabi','-mcpu=arm946e-s','-mthumb','-fno-optimize-sibling-calls','-fsigned-char','-std=c11'):
            self.assertIn(flag,self.T.FLAGS)
        self.assertNotIn('-flto',self.T.FLAGS)


if __name__=='__main__':unittest.main()
