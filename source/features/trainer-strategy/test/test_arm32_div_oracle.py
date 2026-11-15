"""RSB/ADC arithmetic and exact AST delta from the pinned synchronous parent."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import unittest
import test_arm32_sync_oracle as S
from test_arm32_cached_oracle import dp


class DivArithmeticTest(S.SyncArithmeticTest):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('arm32_div_oracle.py');s=importlib.util.spec_from_file_location('finite_div_arithmetic_test',p)
        cls.A=importlib.util.module_from_spec(s);s.loader.exec_module(cls.A)

    def test_parent_implementation_remains_pinned(self):
        p=Path(__file__).with_name('arm32_sync_oracle.py')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.A.PARENT_SHA)

    def test_only_two_arithmetic_opcodes_and_source_guard_change_the_parent_ast(self):
        here=Path(__file__).parent;old=ast.parse((here/'arm32_sync_oracle.py').read_text());new=ast.parse((here/'arm32_div_oracle.py').read_text())
        for tree in(old,new):tree.body=[n for n in tree.body if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Constant)and type(n.value.value)is str)]
        new.body=[n for n in new.body if not(isinstance(n,ast.Import)and [a.name for a in n.names]==['hashlib'])and not(isinstance(n,ast.FunctionDef)and n.name=='source_identity_guard')]
        original_pin=next(n.value for n in old.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PARENT_SHA'for t in n.targets))
        next(n for n in new.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PARENT_SHA'for t in n.targets)).value=original_pin
        run=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='run')
        self.assertEqual(ast.unparse(run.body[0]),'source_identity_guard()');del run.body[0]
        class Reverse(ast.NodeTransformer):
            tuples=0;handlers=0;carry=0
            def visit_Tuple(self,node):
                if all(isinstance(x,ast.Constant)for x in node.elts)and [x.value for x in node.elts]==[0,1,2,3,4,5,8,10,12,13,14,15]:
                    self.tuples+=1;node.elts=[ast.Constant(x)for x in(0,1,2,4,8,10,12,13,14,15)]
                return self.generic_visit(node)
            def visit_Assign(self,node):
                if any(isinstance(t,ast.Name)and t.id=='carry_in'for t in node.targets):self.carry+=1;return None
                return self.generic_visit(node)
            def visit_If(self,node):
                if ast.unparse(node.test)in('op == 3','op == 5'):
                    self.handlers+=1;assert len(node.orelse)==1;return self.visit(node.orelse[0])
                return self.generic_visit(node)
        reverse=Reverse();new=reverse.visit(new)
        self.assertEqual((reverse.tuples,reverse.handlers,reverse.carry),(2,2,1))
        self.assertEqual(ast.dump(new,include_attributes=False),ast.dump(old,include_attributes=False))

    def test_rsb_order_unsigned_carry_and_signed_overflow(self):
        for a,b,result,flags in((2,5,3,0x2000001f),(1,0,0xffffffff,0x8000001f),(0,0,0,0x6000001f),(0x80000000,0,0x80000000,0x9000001f)):
            p=self.execute([dp(3,0,1,b,S=True)],{0:a})
            self.assertEqual((p['returned'][1],p['returned'][15]),(result,flags))

    def test_adc_uses_cpsr_carry_in_when_shifter_carry_is_zero(self):
        p=self.execute([dp(5,1,0,0x82,immediate=False,S=True)],{1:1,2:1},cpsr=0x2000001f)
        self.assertEqual((p['returned'][0],p['returned'][15]),(4,0x1f))

    def test_adc_does_not_use_shifter_carry_when_cpsr_carry_is_zero(self):
        p=self.execute([dp(5,1,0,0x82,immediate=False,S=True)],{1:0,2:0x80000000},cpsr=0x1f)
        self.assertEqual((p['returned'][0],p['returned'][15]),(0,0x4000001f))

    def test_adc_wrap_and_positive_signed_overflow(self):
        for value,result,flags in((0xffffffff,0,0x6000001f),(0x7fffffff,0x80000000,0x9000001f)):
            p=self.execute([dp(5,0,0,0,S=True)],{0:value},cpsr=0x2000001f)
            self.assertEqual((p['returned'][0],p['returned'][15]),(result,flags))

    def test_false_rsb_adc_are_valid_but_have_no_effect(self):
        for op in(3,5):
            p=self.execute([dp(op,0,1,0,S=True,condition=0)],{0:123,1:456},cpsr=0x2000001f)
            self.assertEqual((p['returned'][:2],p['returned'][15]),([123,456],0x2000001f))

    def test_sfalse_rsb_adc_preserve_all_flags(self):
        p=self.execute([dp(3,0,1,0),dp(5,1,2,0)],{0:1},cpsr=0xf000001f)
        self.assertEqual((p['returned'][1:3],p['returned'][15]),([0xffffffff,0],0xf000001f))

    def test_rotate_ands_then_small_ands_preserves_current_carry(self):
        p=self.execute([dp(0,12,3,0x102,S=True),dp(0,12,3,1,S=True)],{12:0},cpsr=0x1f)
        self.assertEqual((p['returned'][3],p['returned'][15]),(0,0x6000001f))


if __name__=='__main__':unittest.main()
