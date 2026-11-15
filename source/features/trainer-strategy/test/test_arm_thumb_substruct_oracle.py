"""Owned ANDS/LDRB-register contracts; no ROM, CPU or private fixture."""
from pathlib import Path
import importlib.util
import struct
import unittest


def module():
    p=Path(__file__).with_name('arm_thumb_substruct_oracle.py');s=importlib.util.spec_from_file_location('substruct_arithmetic_test',p)
    a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a


class SubstructArithmeticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.A=module()

    def fixture(self,flags=0x3000003f):
        return [0]*13+[0x4000,0x1101,flags],{0x3000:bytearray((i%256 for i in range(4096)))}

    def step(self,op,r,p,**guards):
        rd=[];wr=[];pc=self.A.thumb_step(0x1000,struct.pack('<H',op),r,p,rd,wr,**guards)
        return pc,rd,wr

    def test_ands_nz_and_cv_for_all_entry_flags(self):
        for flags in range(16):
            for x,y,result,nz in ((0x80000003,0x80000001,0x80000001,0x80000000),(0x80000000,1,0,0x40000000)):
                r,p=self.fixture((flags<<28)|0x3f);r[0]=x;r[4]=y;pc,rd,wr=self.step(0x4020,r,p)
                self.assertEqual((r[0],r[15],pc,rd,wr),(result,((flags&3)<<28)|nz|0x3f,0x1002,[],[]))

    def test_ands_same_register_remains_defined(self):
        r,p=self.fixture();r[3]=17;self.step(0x401b,r,p);self.assertEqual((r[3],r[15]),(17,0x3000003f))

    def test_ldrb_keeps_every_low_address_bit_and_zero_extends(self):
        for offset in range(16):
            r,p=self.fixture();r[6]=0x3000;r[0]=offset;p[0x3000][offset]=0x80+offset
            pc,rd,wr=self.step(0x5c30,r,p)
            self.assertEqual((r[0],r[15],pc,rd,wr),(0x80+offset,0x3000003f,0x1002,[dict(pc=0x1000,address=0x3000+offset,bytes=1,hex=bytes([0x80+offset]).hex())],[]))

    def test_ldrb_preserves_all_flags(self):
        for flags in range(16):
            r,p=self.fixture((flags<<28)|0x3f);r[6]=0x3000;r[0]=0;self.step(0x5c30,r,p)
            self.assertEqual((r[0],r[15]),(0,(flags<<28)|0x3f))

    def test_ldrb_destination_base_alias_reads_before_update(self):
        r,p=self.fixture();r[0]=0x3000;r[1]=3;self.step(0x5c40,r,p);self.assertEqual(r[0],3)

    def test_ldrb_all_register_aliases_use_old_operand_values(self):
        r,p=self.fixture();r[1]=0x1801;self.step(0x5c49,r,p);self.assertEqual(r[1],2)

    def test_ldrb_address_addition_wraps_u32(self):
        r,p=self.fixture();r[6]=0xffffffff;r[0]=0x3002;self.step(0x5c30,r,p);self.assertEqual(r[0],1)

    def test_ldrb_owner_guard_runs_before_access(self):
        r,p=self.fixture();r[6]=0x3000;r[0]=1;before=list(r)
        with self.assertRaisesRegex(ValueError,'substructure byte owner'):
            self.step(0x5c30,r,p,read_guard=lambda *args:False)
        self.assertEqual(r,before)

    def test_new_masks_do_not_admit_signed_halfword_load_or_byte_store(self):
        for op in (0x5630,0x5a30,0x5430):
            with self.assertRaises(ValueError):self.A.validate_thumb(struct.pack('<H',op))

    def test_run_reuses_parent_bytecode_defaults_and_complete_effective_namespace(self):
        parent=self.A.P.run;new=self.A.run
        self.assertIs(new.__code__,parent.__code__);self.assertEqual(new.__defaults__,parent.__defaults__)
        self.assertEqual(new.__globals__.keys(),parent.__globals__.keys())
        changed={k for k,v in parent.__globals__.items()if new.__globals__[k]is not v}
        self.assertEqual(changed,{'source_identity_guard','validate_thumb','thumb_step'})
        self.assertIs(new.__globals__['thumb_step'],self.A.thumb_step);self.A.source_identity_guard()


if __name__=='__main__':unittest.main()
