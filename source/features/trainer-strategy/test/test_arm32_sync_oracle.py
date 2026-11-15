"""Finite IRQ extension regressions; synthetic owned programs, no guest."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import unittest
import test_arm32_cached_oracle as parent


class SyncArithmeticTest(parent.ArithmeticTest):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).with_name('arm32_sync_oracle.py')
        spec=importlib.util.spec_from_file_location('sync_arm32_test',path)
        cls.A=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.A)

    def test_parent_implementation_remains_pinned(self):
        path=Path(__file__).with_name('arm32_cached_oracle.py')
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),self.A.PARENT_SHA)

    def test_derivative_has_no_unreviewed_changes_outside_the_two_psr_handlers(self):
        here=Path(__file__).parent
        old=ast.parse((here/'arm32_cached_oracle.py').read_text())
        new=ast.parse((here/'arm32_sync_oracle.py').read_text())
        for tree in(old,new):
            tree.body=[n for n in tree.body if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Constant)and type(n.value.value)is str)]
        new.body=[n for n in new.body if not(isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PARENT_SHA'for t in n.targets))]
        validate=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='validate_word')
        self.assertEqual([ast.unparse(n.body[0].value)for n in validate.body[2:4]],["'mrs'","'msr'"])
        del validate.body[2:4]
        run=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='run')
        loop=next(n for n in run.body if isinstance(n,ast.While))
        index=next(i for i,n in enumerate(loop.body)if isinstance(n,ast.If)and ast.unparse(n.test)=="group == 'mrs'")
        loop.body[index]=copy.deepcopy(loop.body[index].orelse[0].orelse[0])
        self.assertEqual(ast.dump(new,include_attributes=False),ast.dump(old,include_attributes=False))

    def test_mrs_reads_entire_cpsr_not_prefetched_pc(self):
        for cpsr in(0x1f,0x6000001f,0xf000009f,0xa00000df):
            p=self.execute([0xe10f0000,0xe10f1000],cpsr=cpsr)
            self.assertEqual(p['returned'][:2],[cpsr,cpsr]);self.assertEqual(p['returned'][15],cpsr)

    def test_msr_only_changes_control_and_preserves_live_flags(self):
        p=self.execute([0xe121f001],{1:0xf000009f},cpsr=0x6000001f)
        self.assertEqual(p['returned'][15],0x6000009f)
        p=self.execute([0xe121f002],{2:0x1f},cpsr=0xa000009f)
        self.assertEqual(p['returned'][15],0xa000001f)

    def test_forbidden_banked_mode_thumb_fiq_and_spsr_fail_closed(self):
        for value in(0x13,0x3f,0x5f):
            with self.assertRaisesRegex(ValueError,'IRQ control domain'):
                self.execute([0xe121f001],{1:value},cpsr=0x1f)
        for word in(0x014f0000,0x0128f001,0x010f2000,0x0321f080):
            with self.assertRaisesRegex(ValueError,'unsupported'):
                self.execute([word],cpsr=0x1f) # Even false EQ encodings.

    def test_false_allowed_psr_instruction_has_no_effect(self):
        p=self.execute([0x0121f001,0x010f0000],{0:0x1234,1:0x13},cpsr=0x1f)
        self.assertEqual((p['returned'][0],p['returned'][15]),(0x1234,0x1f))

    def test_disable_cmp_restore_keeps_current_flags(self):
        # Native disable; CMP changes NZCV while I set; native restore with saved I.
        words=[0xe10f1000,0xe3812080,0xe121f002,0xe2010080,
               0xe3530001,0xe10f1000,0xe3c12080,0xe1822000,0xe121f002,0xe2010080]
        for initial in(0x6000001f,0x6000009f,0x6000005f,0x600000df):
            p=self.execute(words,{3:2},cpsr=initial)
            self.assertEqual(p['returned'][15],0x20000000|(initial&255))
            self.assertEqual(p['returned'][0],0x80) # Restore returns previous disabled I.
            self.assertEqual(p['returned'][1],0x20000000|(initial&255)|0x80)


if __name__=='__main__':unittest.main()
