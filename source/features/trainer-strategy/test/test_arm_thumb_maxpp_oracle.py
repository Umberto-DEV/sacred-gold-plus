"""MaxPP Thumb additions and scoped arithmetic routing, no CPU or ROM."""
from pathlib import Path
import ast
import importlib.util
import struct
import unittest
import test_arm_thumb_pp_oracle as PP


class MaxPPArithmeticTest(PP.MixedPPArithmeticTest):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('arm_thumb_maxpp_oracle.py');s=importlib.util.spec_from_file_location('maxPP_arithmetic_test',p)
        cls.A=importlib.util.module_from_spec(s);s.loader.exec_module(cls.A)

    def test_lsr24_and_zero_encoding32_have_precise_carry(self):
        for word,value,result,flags in((0x0e04,0xff000000,255,0x1000003f),(0x0804,0x80000000,0,0x7000003f)):
            r,p=self.fixture(cpsr=0x1000003f);r[0]=value
            _,r,_,_,_=self.step(struct.pack('<H',word),r,p)
            self.assertEqual((r[4],r[15]),(result,flags))

    def test_muls_low32_updates_nz_and_preserves_cv(self):
        r,p=self.fixture(cpsr=0x3000003f);r[0]=0xffffffff;r[4]=2
        _,r,_,rd,wr=self.step(bytes.fromhex('6043'),r,p)
        self.assertEqual((r[0],r[15],rd,wr),(0xfffffffe,0xb000003f,[],[]))

    def test_muls_alias_is_rejected_before_effects_even_if_new_cpu_allows_it(self):
        for reg in range(8):
            r,p=self.fixture();before=list(r);rd=[];wr=[];op=0x4340|(reg<<3)|reg
            with self.assertRaisesRegex(ValueError,'ARMv5 MUL register alias'):
                self.A.thumb_step(0x1000,struct.pack('<H',op),r,p,rd,wr)
            self.assertEqual((r,rd,wr),(before,[],[]))

    def test_bls_is_unsigned_lower_or_same(self):
        for flags,take in((0x2000003f,False),(0x6000003f,True),(0x3f,True),(0x8000003f,True)):
            r,p=self.fixture(cpsr=flags);nxt,*_=self.step(bytes.fromhex('01d9'),r,p)
            self.assertEqual(nxt,0x1006 if take else 0x1002)

    def test_sixth_return_namespace_really_exchanges_the_division_bx(self):
        r,p=self.fixture(cpsr=0x6000001f);r[14]=0x207334d
        nxt=self.A.arm_return(0x20f2ba0,0xe12fff1e,r,p,[])
        self.assertEqual((nxt,r[15]),(0x207334c,0x6000003f))

    def test_interpreter_selector_keeps_sdk_on_original_arm_and_div_on_extension(self):
        sdk=((0x20d7f98,40),)
        self.assertEqual(self.A.select_arm(0x20d7f98,[0]*16,sdk),(self.A.A,sdk))
        regs=[0]*16;regs[0]=900;regs[1]=100
        self.assertEqual(self.A.select_arm(self.A.DIV_ENTRY,regs,sdk),(self.A.D,((self.A.DIV_ENTRY,524),)))
        for numerator,denominator in((1,100),(900,0),(-1,100)):
            regs[0]=numerator;regs[1]=denominator
            with self.assertRaisesRegex(ValueError,'finite native division arguments'):
                self.A.select_arm(self.A.DIV_ENTRY,regs,sdk)

    def test_router_loop_has_no_extra_changes_outside_guard_and_selector(self):
        here=Path(__file__).parent;old=ast.parse((here/'arm_thumb_narc_oracle.py').read_text());new=ast.parse((here/'arm_thumb_maxpp_oracle.py').read_text())
        oldrun=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name=='run')
        newrun=next(n for n in new.body if isinstance(n,ast.FunctionDef)and n.name=='run')
        self.assertEqual(ast.unparse(newrun.body[0]),'source_identity_guard()');newrun.body[0]=oldrun.body[0]
        loop=next(n for n in newrun.body if isinstance(n,ast.While))
        arm=loop.body[-1].orelse
        # Exact selector assignment is the sole additional operation inside
        # the parent ARM segment path; all observation/stack/return logic stays.
        i=next(i for i,n in enumerate(arm)if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Tuple)and
               [x.id for x in n.targets[0].elts]==['interpreter','selected_spans'])
        self.assertEqual(ast.unparse(arm[i].value),'select_arm(pc, regs, code_spans)');del arm[i]
        call=arm[i].value;self.assertEqual(ast.unparse(call.func),'interpreter.run');call.func.value=ast.Name(id='A',ctx=ast.Load())
        self.assertEqual(ast.unparse(call.args[1]),'selected_spans');call.args[1]=ast.Name(id='code_spans',ctx=ast.Load())
        self.assertEqual(ast.dump(newrun,include_attributes=False),ast.dump(oldrun,include_attributes=False))


if __name__=='__main__':unittest.main()
