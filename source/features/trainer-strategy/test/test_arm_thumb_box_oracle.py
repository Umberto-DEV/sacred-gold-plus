"""Owned arithmetic/branch boundaries for the full Box getter; no ROM or CPU."""
from pathlib import Path
import importlib.util
import struct
import unittest


class BoxArithmeticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('arm_thumb_box_oracle.py');s=importlib.util.spec_from_file_location('box_test_arithmetic',p)
        cls.A=importlib.util.module_from_spec(s);s.loader.exec_module(cls.A)

    def step(self,word,value=0,pc=0x1000,flags=0xf800003f):
        regs=[0]*13+[0x4000,0x1101,flags];regs[0]=value;before=list(regs);reads=[];stores=[]
        target=self.A.thumb_step(pc,struct.pack('<H',word),regs,{},reads,stores)
        self.assertEqual((reads,stores),([],[]));self.assertEqual(regs[1:15],before[1:15])
        return target,regs

    def test_subs_borrow_zero_negative_and_signed_overflow(self):
        for x,y,result,flags in ((62,62,0,0x6000003f),(0,1,0xffffffff,0x8000003f),
                (0x80000000,1,0x7fffffff,0x3000003f),(0x7fffffff,255,0x7fffff00,0x2000003f),
                (0xffffffff,255,0xffffff00,0xa000003f)):
            pc,r=self.step(0x3800|y,x,flags=0xf000003f)
            self.assertEqual((pc,r[0],r[15]),(0x1002,result,flags))

    def test_subs_all_low_destinations_and_non_nzcv_bits_preserved(self):
        for rd in range(8):
            regs=[62]*13+[0x4000,0x1101,0xf800003f];before=list(regs)
            pc=self.A.thumb_step(0x1000,struct.pack('<H',0x3800|(rd<<8)|62),regs,{},[],[])
            before[rd]=0;before[15]=0x6800003f
            self.assertEqual((regs,pc),(before,0x1002))

    def test_subs_ignores_old_flags(self):
        for flags in range(16):
            _,r=self.step(0x383e,62,flags=(flags<<28)|0x3f)
            self.assertEqual(r[15],0x6000003f)

    def test_branch_sign_extension_full_domain_and_flags(self):
        for imm in range(2048):
            pc,r=self.step(0xe000|imm)
            signed=imm if imm<1024 else imm-2048
            self.assertEqual((pc,r[15]),((0x1004+2*signed)&0xffffffff,0xf800003f))

    def test_branch_pc_wrap_and_halfword_unaligned_to_word(self):
        for pc,word,expected in ((0xfffffffe,0xe000,2),(0,0xe7fd,0xfffffffe),
                (0x1002,0xe000,0x1006),(0x206e988,0xe155,0x206ec36)):
            got,_=self.step(word,pc=pc);self.assertEqual(got,expected)

    def test_box_dispatch_high_add_uses_actual_operands_and_unrounded_pc(self):
        regs=[124]+[0]*12+[0x4000,0x1101,0xb000003f]
        pc=self.A.thumb_step(0x206e6ec,bytes.fromhex('7844'),regs,{},[],[])
        self.assertEqual((pc,regs[0],regs[15]),(0x206e6ee,0x206e76c,0xb000003f))
        regs[0]=0x286
        pc=self.A.thumb_step(0x206e6f4,bytes.fromhex('8744'),regs,{},[],[])
        self.assertEqual((pc,regs[0],regs[14],regs[15]),(0x206e97e,0x286,0x1101,0xb000003f))

    def test_new_masks_do_not_admit_swi_or_undefined_or_bl_suffix(self):
        for word in (0xdf00,0xde00,0xe800,0xf800):
            with self.assertRaises(ValueError):self.A.validate_thumb(struct.pack('<H',word))

    def test_run_preserves_complete_effective_namespace_and_defaults(self):
        old=self.A.P.run;new=self.A.run
        self.assertIs(old.__code__,new.__code__);self.assertEqual(old.__defaults__,new.__defaults__)
        self.assertEqual(old.__kwdefaults__,new.__kwdefaults__)
        self.assertEqual(old.__globals__.keys(),new.__globals__.keys())
        self.assertEqual({k for k,v in old.__globals__.items()if new.__globals__[k]is not v},
                         {'source_identity_guard','validate_thumb','thumb_step'})
        self.A.source_identity_guard()


if __name__=='__main__':unittest.main()
