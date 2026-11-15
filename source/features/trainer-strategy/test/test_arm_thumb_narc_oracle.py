"""Owned finite Thumb/interworking programs; no ROM or CPU dependency."""
from pathlib import Path
import hashlib
import importlib.util
import struct
import unittest


class MixedNarcArithmeticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('arm_thumb_narc_oracle.py')
        s=importlib.util.spec_from_file_location('mixed_narc_arithmetic_test',p)
        cls.A=importlib.util.module_from_spec(s);s.loader.exec_module(cls.A)

    def fixture(self,pc=0x1000,cpsr=0x6000003f):
        regs=[0]*13+[0x4000,0x1101,cpsr]
        return regs,{0x1000:bytearray(4096),0x3000:bytearray(b'\xa5'*4096)}

    def step(self,blob,regs=None,pages=None,pc=0x1000):
        if regs is None:regs,pages=self.fixture(pc)
        self.A.A.F.put(pages,pc,blob)
        reads=[];stores=[]
        nxt=self.A.thumb_step(pc,blob,regs,pages,reads,stores)
        return nxt,regs,pages,reads,stores

    def test_existing_arm_oracle_remains_byte_identical(self):
        p=Path(__file__).with_name('arm32_sync_oracle.py')
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),self.A.PARENT_SHA)

    def test_blx_at_two_mod_four_has_aligned_base_odd_lr_and_clears_only_t(self):
        pc=0x20073fe;r,p=self.fixture(pc);p[pc&~4095]=bytearray(4096)
        nxt,r,_,rd,wr=self.step(bytes.fromhex('d0f0e6ef'),r,p,pc)
        self.assertEqual((nxt,r[14],r[15]),(0x20d83cc,0x2007403,0x6000001f))
        self.assertEqual((rd,wr),([],[]))

    def test_thumb_bl_negative_offset_keeps_thumb_and_links_after_whole_pair(self):
        pc=0x2007516;r,p=self.fixture(pc);p[pc&~4095]=bytearray(4096)
        nxt,r,_,_,_=self.step(bytes.fromhex('fff709ff'),r,p,pc)
        self.assertEqual((nxt,r[14],r[15]),(0x200732c,0x200751b,0x6000003f))

    def test_literal_uses_word_aligned_pc_plus_four(self):
        r,p=self.fixture();self.A.A.F.put(p,0x1010,struct.pack('<I',0x210f210))
        _,r,_,rd,_=self.step(bytes.fromhex('0349'),r,p,0x1002)
        self.assertEqual((r[1],rd[0]['address']),(0x210f210,0x1010))

    def test_adds_zero_recomputes_carry_overflow_unlike_mov(self):
        r,p=self.fixture(cpsr=0xf000003f);r[1]=0x80000000
        _,r,_,_,_=self.step(bytes.fromhex('0c1c'),r,p)
        self.assertEqual((r[4],r[15]),(0x80000000,0x8000003f))

    def test_movs_and_zero_lsl_preserve_carry_overflow(self):
        r,p=self.fixture(cpsr=0x3000003f)
        _,r,_,_,_=self.step(bytes.fromhex('0023'),r,p)
        self.assertEqual(r[15],0x7000003f)
        r[1]=0x80000001
        _,r,_,_,_=self.step(bytes.fromhex('0c00'),r,p)
        self.assertEqual((r[4],r[15]),(0x80000001,0xb000003f))

    def test_signed_gt_uses_n_equals_v_and_ne_uses_z(self):
        for cpsr,take in ((0x9000003f,True),(0x8000003f,False),(0x4000003f,False),(0x3f,True)):
            r,p=self.fixture(cpsr=cpsr)
            nxt,*_=self.step(bytes.fromhex('01dc'),r,p)
            self.assertEqual(nxt,0x1006 if take else 0x1002)

    def test_push_pop_reads_actual_frame_and_restores_saved_lr_as_pc(self):
        r,p=self.fixture();r[3]=0x33333333;r[4]=0x44444444;r[14]=0x1101
        _,r,p,_,wr=self.step(bytes.fromhex('18b5'),r,p)
        self.assertEqual([x['address']for x in wr],[0x3ff4,0x3ff8,0x3ffc])
        self.assertTrue(all(x['before']=='a5'*4 for x in wr))
        r[3]=r[4]=0
        nxt,r,_,rd,_=self.step(bytes.fromhex('18bd'),r,p)
        self.assertEqual((nxt,r[3],r[4],r[13],r[15]),(0x1100,0x33333333,0x44444444,0x4000,0x6000003f))
        self.assertEqual([x['hex']for x in rd],['33333333','44444444','01110000'])

    def test_halfword_truncates_and_preserves_adjacent_bytes(self):
        r,p=self.fixture();r[0]=0x3000;r[1]=0x12345678
        _,_,p,_,wr=self.step(bytes.fromhex('0180'),r,p)
        self.assertEqual(bytes(p[0x3000][:4]),bytes.fromhex('7856a5a5'))
        self.assertEqual((wr[0]['bytes'],wr[0]['value']),(2,0x5678))

    def test_arm_bx_and_native_pop_exchange_preserve_flags_and_restore_real_registers(self):
        for pc,word,indices in ((0x20d7fbc,0xe12fff1e,()),(0x20d82b0,0x18bd8010,(4,15)),(0x20d817c,0xe8bd80f8,(3,4,5,6,7,15)),(0x20d82f8,0xe8bd8010,(4,15))):
            r,p=self.fixture(cpsr=0xa000001f);r[13]=0x3f00;r[14]=0x1101
            vals=[0x11111111+i for i in range(len(indices))]
            if vals:vals[-1]=0x1101;self.A.A.F.put(p,0x3f00,struct.pack('<'+'I'*len(vals),*vals))
            reads=[]
            nxt=self.A.arm_return(pc,word,r,p,reads)
            self.assertEqual((nxt,r[15],r[13]),(0x1100,0xa000003f,0x3f00+4*len(vals)))
            self.assertEqual(len(reads),len(vals))
            for i,value in zip(indices,vals):
                if i!=15:self.assertEqual(r[i],value)

    def test_arm_false_pop_condition_cannot_fake_a_thumb_return(self):
        r,p=self.fixture(cpsr=0x4000001f)
        with self.assertRaisesRegex(ValueError,'return condition'):
            self.A.arm_return(0x20d82b0,0x18bd8010,r,p,[])

    def test_truncated_blx_assert_encoding_and_empty_push_fail_closed(self):
        for blob in (bytes.fromhex('d0f0'),bytes.fromhex('d0f0e7ef'),bytes.fromhex('00b4'),bytes.fromhex('00df'),bytes.fromhex('00bf')):
            with self.subTest(blob=blob.hex()),self.assertRaises(ValueError):self.step(blob)

    def test_even_half_aligned_arm_target_and_disabled_load_tbit_rejected(self):
        r,_=self.fixture()
        with self.assertRaisesRegex(ValueError,'aligned ARM'):self.A.exchange(0x1002,r)
        with self.assertRaisesRegex(ValueError,'TBIT'):self.A.exchange(0x1001,r,load_tbit_enabled=False)

    def test_actual_code_identity_and_second_half_entry_are_enforced(self):
        r,p=self.fixture();f=dict(entry_pc=0x1002,entry_regs=r,pages=p)
        with self.assertRaisesRegex(ValueError,'qualified Thumb'):
            self.A.run(f,(),0x1100,thumb_code={0x1000:bytes.fromhex('fff709ff')})

    def test_register_halfword_byte_signed_loads_rejected_before_access(self):
        for op in (0x5a00,0x5c00,0x5e00):
            r,p=self.fixture();reads=[];stores=[]
            with self.assertRaisesRegex(ValueError,'unsupported finite Thumb'):
                self.A.thumb_step(0x1000,struct.pack('<H',op),r,p,reads,stores)
            self.assertEqual((reads,stores),([],[]))

    def test_admitted_start_with_wrong_live_bytes_fails_closed(self):
        r,p=self.fixture();f=dict(entry_pc=0x1000,entry_regs=r,pages=p)
        with self.assertRaisesRegex(ValueError,'qualified Thumb byte identity'):
            self.A.run(f,(),0x1100,thumb_code={0x1000:bytes.fromhex('0023')})


if __name__=='__main__':unittest.main()
