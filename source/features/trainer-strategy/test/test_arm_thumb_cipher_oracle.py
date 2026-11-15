"""Owned finite cipher instruction contracts, standard library only."""
from pathlib import Path
import importlib.util
import struct
import unittest


def module():
    p=Path(__file__).with_name('arm_thumb_cipher_oracle.py')
    s=importlib.util.spec_from_file_location('cipher_arithmetic_test',p)
    a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a


class CipherArithmeticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.A=module()

    def fixture(self,flags=0x3000003f):
        return [0]*13+[0x4000,0x1101,flags],{0x3000:bytearray(b'\xa5'*4096)}

    def step(self,op,r,p,**guards):
        reads=[];stores=[]
        pc=self.A.thumb_step(0x1000,struct.pack('<H',op),r,p,reads,stores,**guards)
        return pc,reads,stores

    def test_eor_nz_and_cv_for_all_entry_flags(self):
        for flags in range(16):
            r,p=self.fixture((flags<<28)|0x3f);r[0]=0x80000000;r[1]=1
            pc,rd,wr=self.step(0x4048,r,p)
            self.assertEqual((r[0],r[15],pc,rd,wr),(0x80000001,((flags&3)<<28)|0x8000003f,0x1002,[],[]))

    def test_eor_same_register_is_defined_zero(self):
        r,p=self.fixture();r[3]=0x12345678;self.step(0x405b,r,p)
        self.assertEqual((r[3],r[15]),(0,0x7000003f))

    def test_word_load_scaled_offset_and_flags(self):
        r,p=self.fixture();r[1]=0x3000;p[0x3000][12:16]=bytes.fromhex('78563412')
        pc,rd,wr=self.step(0x68c8,r,p)
        self.assertEqual((r[0],r[15],rd,wr),(0x12345678,0x3000003f,[dict(pc=0x1000,address=0x300c,bytes=4,hex='78563412')],[]))

    def test_word_store_scaled_offset_preimage_and_flags(self):
        r,p=self.fixture();r[1]=0x3000;r[0]=0xdeadbeef
        _,rd,wr=self.step(0x60c8,r,p)
        self.assertEqual((rd,wr,p[0x3000][12:16],r[15]),([],[dict(pc=0x1000,address=0x300c,bytes=4,before='a5a5a5a5',value=0xdeadbeef)],bytes.fromhex('efbeadde'),0x3000003f))

    def test_word_load_base_equals_destination_reads_before_register_update(self):
        r,p=self.fixture();r[0]=0x3000;p[0x3000][:4]=struct.pack('<I',17);self.step(0x6800,r,p);self.assertEqual(r[0],17)

    def test_word_unaligned_rejected_before_effect(self):
        for op in (0x6008,0x6808):
            r,p=self.fixture();r[1]=0x3001;old=list(r);before=bytes(p[0x3000]);rd=[];wr=[]
            with self.assertRaisesRegex(ValueError,'aligned cipher word'):
                self.A.thumb_step(0x1000,struct.pack('<H',op),r,p,rd,wr)
            self.assertEqual((r,rd,wr,bytes(p[0x3000])),(old,[],[],before))

    def test_word_guards_run_before_access(self):
        for op,guard in ((0x6008,'write_guard'),(0x6808,'read_guard')):
            r,p=self.fixture();r[1]=0x3000;old=list(r);before=bytes(p[0x3000])
            with self.assertRaisesRegex(ValueError,'cipher word owner'):
                self.step(op,r,p,**{guard:lambda *args:False})
            self.assertEqual((r,bytes(p[0x3000])),(old,before))

    def test_eq_and_lo_take_and_skip_without_side_effect(self):
        for op,flags,taken in ((0xd001,0x4000003f,True),(0xd001,0x3f,False),(0xd301,0x3f,True),(0xd301,0x2000003f,False)):
            r,p=self.fixture(flags);before=list(r);pc,rd,wr=self.step(op,r,p)
            self.assertEqual((pc,r,rd,wr),(0x1006 if taken else 0x1002,before,[],[]))

    def test_signed_backward_lo(self):
        r,p=self.fixture(0x3f);self.assertEqual(self.step(0xd3f5,r,p)[0],0x0fee)

    def test_unsupported_byte_store_signed_load_and_svc_rejected(self):
        for op in (0x7008,0x5608,0xdf00,0xde00):
            with self.assertRaises(ValueError):self.A.validate_thumb(struct.pack('<H',op))

    def test_bound_run_preserves_parent_bytecode_defaults_and_effective_namespace(self):
        self.assertIs(self.A.run.__code__,self.A.P.run.__code__)
        self.assertEqual(self.A.run.__defaults__,self.A.P.run.__defaults__)
        self.assertIs(self.A.run.__globals__['thumb_step'],self.A.thumb_step)
        self.assertIs(self.A.run.__globals__['validate_thumb'],self.A.validate_thumb)
        self.assertIs(self.A.run.__globals__['source_identity_guard'],self.A.source_identity_guard)
        self.A.source_identity_guard()

    def test_parent_mul_and_lsr_and_stack_still_delegated(self):
        r,p=self.fixture();r[0]=0xffffffff;r[4]=2;self.step(0x4360,r,p)
        self.assertEqual((r[0],r[15]),(0xfffffffe,0xb000003f))
        r[0]=0x80000000;self.step(0x0804,r,p);self.assertEqual((r[4],r[15]),(0,0x7000003f))
        self.step(0xb40f,r,p);self.assertEqual(r[13],0x3ff0)
        self.step(0xbc0f,r,p);self.assertEqual(r[13],0x4000)


if __name__=='__main__':unittest.main()
