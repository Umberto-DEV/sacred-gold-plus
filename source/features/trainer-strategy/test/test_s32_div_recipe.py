"""ROM-free source/recipe selection and compiler CLI contracts."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import unittest


class S32RecipeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/compila_s32_div.py';s=importlib.util.spec_from_file_location('s32_recipe_contract_test',p)
        cls.C=importlib.util.module_from_spec(s);s.loader.exec_module(cls.C)

    def test_repeat_expands_exactly_32_groups_and_keeps_sign_tail(self):
        lines=self.C.recipe_body(self.C.RECIPE.read_text())
        self.assertEqual(len(lines),132)
        self.assertEqual(lines.count('adcs r3, r1, r3, lsl #1'),32)
        self.assertEqual(lines.count('sublo r3, r3, r1'),32)
        self.assertEqual(lines.count('adcs r0, r0, r0'),32)
        self.assertEqual(lines[-6:],['.L020F2B90:','ands r3, r12, #0x80000000','rsbne r0, r0, #0','ands r3, r12, #1','rsbne r1, r1, #0','bx lr'])

    def test_source_selector_preserves_last_instruction_and_excludes_neighbor(self):
        body='\n'.join(self.C.recipe_body(self.C.RECIPE.read_text())).replace('.L020F2B90','@020F2B90')
        source='prefix\n@s32_div_f:\n'+body+'\n@u32_div_f:\n    cmp r1, #0\n'
        selected=self.C.source_body(source)
        self.assertEqual(selected,self.C.recipe_body(self.C.RECIPE.read_text()))
        self.assertEqual(selected[-1],'bx lr')
        with self.assertRaisesRegex(ValueError,'unique bounded MSL'):
            self.C.source_body(source+'@s32_div_f:\n')

    def test_wrong_repeat_or_extra_body_directive_fails_closed(self):
        text=self.C.RECIPE.read_text()
        for changed in(text.replace('.rept 32','.rept 31'),text.replace('.endr','.endr\n .word 0'),text.replace('.endr','.endr\n .rept 32\n .endr')):
            with self.assertRaises(ValueError):self.C.recipe_body(changed)

    def test_missing_source_tail_cannot_appear_as_complete_131_instructions(self):
        body='\n'.join(self.C.recipe_body(self.C.RECIPE.read_text())[:-1]).replace('.L020F2B90','@020F2B90')
        with self.assertRaisesRegex(ValueError,'131 MSL'):
            self.C.source_body('@s32_div_f:\n'+body+'\n@u32_div_f:\n')

    def test_recipe_cli_help_and_required_args_have_no_compiler_effect(self):
        p=Path(self.C.__file__)
        r=subprocess.run([sys.executable,'-I','-S','-B',str(p),'--help'],capture_output=True,timeout=15)
        self.assertEqual(r.returncode,0,r.stderr.decode())
        r=subprocess.run([sys.executable,'-I','-S','-B',str(p)],capture_output=True,timeout=15)
        self.assertEqual(r.returncode,2,r.stderr.decode());self.assertIn(b'required',r.stderr)


if __name__=='__main__':unittest.main()
