"""Owned synthetic ARM programs for the finite arithmetic oracle; no guest."""
from pathlib import Path
import importlib.util
import struct
import unittest


def dp(op,rn,rd,operand,*,immediate=True,S=False,condition=14):
    return condition<<28|int(immediate)<<25|op<<21|int(S)<<20|rn<<16|rd<<12|operand


class ArithmeticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).with_name('arm32_cached_oracle.py')
        spec=importlib.util.spec_from_file_location('arm32_cached_test',path)
        cls.A=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.A)

    def execute(self,words,values=None,memory=None,cpsr=0x6000001f):
        pages={0x1000:bytearray(4096),0x2000:bytearray(b'\xa5'*4096),0x3000:bytearray(b'\xa5'*4096)}
        pages[0x1000][:4*len(words)]=struct.pack('<'+'I'*len(words),*words)
        if memory:
            for address,blob in memory.items():pages[address&~4095][address&4095:(address&4095)+len(blob)]=blob
        regs=[0]*13+[0x4000,0x1000+4*len(words),cpsr]
        for index,value in (values or {}).items():regs[index]=value
        return self.A.run(dict(entry_pc=0x1000,entry_regs=regs,pages=pages),((0x1000,4*len(words)),),0x1000+4*len(words),cap=32)

    def test_subtraction_underflow_carry_and_signed_overflow(self):
        word=dp(2,0,0,2,S=True)
        for value,result,flags in ((2,0,0x6000001f),(0,0xfffffffe,0x8000001f),(0x80000000,0x7ffffffe,0x3000001f)):
            p=self.execute([word],{0:value});self.assertEqual((p['returned'][0],p['returned'][15]),(result,flags))
        p=self.execute([dp(4,0,0,1,S=True)],{0:0x7fffffff})
        self.assertEqual((p['returned'][0],p['returned'][15]),(0x80000000,0x9000001f))

    def test_unsigned_letter_fold_does_not_treat_negative_u32_as_small(self):
        words=[dp(2,0,12,65),dp(10,12,0,25,S=True),dp(4,12,12,32,condition=9)]
        p=self.execute(words,{0:48});self.assertEqual(p['returned'][12],0xffffffef)
        self.assertEqual(p['returned'][15],0xa000001f)

    def test_rotated_immediate_carry_and_zero_shift_preservation(self):
        p=self.execute([dp(8,0,0,0x480,S=True)],{0:0xffffffff},cpsr=0x1f) # ROR(80,8)=80000000
        self.assertEqual(p['returned'][15],0xa000001f)
        p=self.execute([dp(13,0,1,0,immediate=False,S=True)],{0:0},cpsr=0x2000001f)
        self.assertEqual(p['returned'][15],0x6000001f)

    def test_register_shift_and_arithmetic_sign_extension(self):
        p=self.execute([dp(13,0,1,0x202,immediate=False)],{2:3}) # LSL #4
        self.assertEqual(p['returned'][1],48)
        p=self.execute([dp(13,0,1,0x842,immediate=False)],{2:0x80000001}) # ASR #16
        self.assertEqual(p['returned'][1],0xffff8000)
        p=self.execute([dp(13,0,1,0x312,immediate=False)],{2:3,3:4}) # LSL r3
        self.assertEqual(p['returned'][1],48)

    def test_postindexed_halfword_and_full_register_before_strh_truncation(self):
        words=[0xe0d0c0b2,dp(12,3,12,0x40c,immediate=False),0xe1c1c0b0]
        p=self.execute(words,{0:0x2000,1:0x3000,3:2},memory={0x2000:b'\xf0\x81'})
        self.assertEqual(p['returned'][0],0x2002)
        self.assertEqual(p['returned'][12],0x0081f002)
        self.assertEqual(p['pages'][0x3000][:3],b'\x02\xf0\xa5')
        self.assertEqual((p['reads'][0]['bytes'],p['stores'][0]['bytes']),(2,2))

    def test_ldm_base_in_list_without_writeback_and_preindexed_ldrb(self):
        p=self.execute([0xe8900007],{0:0x2000},memory={0x2000:struct.pack('<III',7,8,9)})
        self.assertEqual(p['returned'][:3],[7,8,9])
        self.assertEqual([x['address']for x in p['reads']],[0x2000,0x2004,0x2008])
        p=self.execute([0xe7f50000],{5:0x2000,0:1},memory={0x2000:b'AZ'})
        self.assertEqual((p['returned'][0],p['returned'][5]),(ord('Z'),0x2001))

    def test_condition_false_does_not_read_or_writeback(self):
        p=self.execute([0x07f50000],{5:0x2000,0:1},cpsr=0x1f)
        self.assertEqual((p['reads'],p['returned'][5]),([],0x2000))

    def test_predicate_false_still_rejects_unqualified_encoding(self):
        words=(0x00000090,0x06000010,dp(8,0,0,0,S=False,condition=0))
        for word in words:
            with self.subTest(word=hex(word)),self.assertRaisesRegex(ValueError,'unsupported'):
                self.execute([word],cpsr=0x1f)

    def test_branch_link_pop_pc_and_instruction_budget(self):
        p=self.execute([0xe92d4000,0xe3a0e001,0xe8bd8000]) # PUSH LR;MOV LR1;POP PC
        self.assertEqual((p['stop_pc'],p['returned'][14],p['returned'][13]),(0x100c,1,0x4000))
        with self.assertRaisesRegex(ValueError,'instruction budget'):self.execute([0xeafffffe])
        with self.assertRaisesRegex(ValueError,'unsupported'):self.execute([0xe0000090]) # MUL outside scope


if __name__=='__main__':unittest.main()
