"""Finite PP-dispatch extension, plus inherited NARC arithmetic regressions."""
from pathlib import Path
import hashlib
import importlib.util
import struct
import unittest
import test_arm_thumb_narc_oracle as N


class MixedPPArithmeticTest(N.MixedNarcArithmeticTest):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('arm_thumb_pp_oracle.py')
        s=importlib.util.spec_from_file_location('pp_mixed_arithmetic_test',p)
        cls.A=importlib.util.module_from_spec(s);s.loader.exec_module(cls.A)

    def test_parent_frontend_is_pinned_and_not_cloned(self):
        p=Path(__file__).with_name('arm_thumb_narc_oracle.py')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.A.FRONTEND_SHA)

    def test_high_add_reads_unrounded_thumb_pc_and_preserves_flags(self):
        r,p=self.fixture(cpsr=0xf000003f);r[1]=10
        nxt,r,_,rd,wr=self.step(bytes.fromhex('7944'),r,p,0x1002)
        self.assertEqual((nxt,r[1],r[15]),(0x1004,0x1010,0xf000003f))
        self.assertEqual((rd,wr),([],[]))

    def test_high_add_pc_destination_branches_with_thumb_preserved(self):
        r,p=self.fixture(cpsr=0xa000003f);r[1]=42
        nxt,r,_,_,_=self.step(bytes.fromhex('8f44'),r,p,0x1002)
        self.assertEqual((nxt,r[15]),(0x1030,0xa000003f))
        r[1]=43
        nxt,r,_,_,_=self.step(bytes.fromhex('8f44'),r,p,0x1002)
        self.assertEqual((nxt,r[15]),(0x1030,0xa000003f))

    def test_asr_sign_carry_zero_immediate_and_overflow_preservation(self):
        for value,op,result,cpsr in((0x80010000,0x1409,0xffff8001,0x9000003f),
                                   (0x00010000,0x1409,1,0x1000003f),
                                   (0x80000001,0x1009,0xffffffff,0xb000003f)):
            r,p=self.fixture(cpsr=0x1000003f);r[1]=value
            _,r,_,_,_=self.step(struct.pack('<H',op),r,p)
            self.assertEqual((r[1],r[15]),(result,cpsr))

    def test_bhi_requires_carry_and_not_zero(self):
        for psr,take in((0x2000003f,True),(0x6000003f,False),(0x3f,False),(0x8000003f,False)):
            r,p=self.fixture(cpsr=psr);nxt,*_=self.step(bytes.fromhex('01d8'),r,p)
            self.assertEqual(nxt,0x1006 if take else 0x1002)

    def test_ldrb_loads_byte_zero_extended_without_touching_neighbors_or_flags(self):
        r,p=self.fixture(cpsr=0xf000003f);r[0]=0x3000;p[0x3000][6:8]=b'\x81\x7f'
        _,r,_,rd,wr=self.step(bytes.fromhex('8079'),r,p)
        self.assertEqual((r[0],r[15],rd,wr),(0x81,0xf000003f,[dict(pc=0x1000,address=0x3006,bytes=1,hex='81')],[]))

    def test_thumb_bx_tail_preserves_lr_and_full_flags(self):
        for op,index in((0x4718,3),(0x4770,14)):
            r,p=self.fixture(cpsr=0xb000003f);r[index]=0x1103;lr=r[14]
            nxt,r,_,rd,wr=self.step(struct.pack('<H',op),r,p)
            self.assertEqual((nxt,r[14],r[15],rd,wr),(0x1102,lr,0xb000003f,[],[]))

    def test_new_families_do_not_admit_other_high_mov_pc_pc_or_blx_register(self):
        for op in(0x4400,0x447f,0x44ff,0x46c0,0x4798,0x4700,0x7000):
            r,p=self.fixture();rd=[];wr=[]
            with self.subTest(op=hex(op)),self.assertRaises(ValueError):
                self.A.thumb_step(0x1000,struct.pack('<H',op),r,p,rd,wr)
            self.assertEqual((rd,wr),([],[]))

    def test_bhi_negative_offset_is_sign_extended(self):
        r,p=self.fixture(cpsr=0x2000003f)
        nxt,*_=self.step(bytes.fromhex('fed8'),r,p)
        self.assertEqual(nxt,0x1000)

    def test_denied_byte_owner_is_rejected_before_read_or_register_change(self):
        r,p=self.fixture();r[0]=0x3000;before=list(r);rd=[];wr=[]
        with self.assertRaisesRegex(ValueError,'source read owner/site'):
            self.A.thumb_step(0x1000,bytes.fromhex('8079'),r,p,rd,wr,lambda pc,a,n:False)
        self.assertEqual((r,rd,wr),(before,[],[]))


if __name__=='__main__':unittest.main()
