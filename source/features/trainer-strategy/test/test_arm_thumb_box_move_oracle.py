"""Owned STRH-register width/offset/alias contracts; no ROM or CPU backend."""
from pathlib import Path
import importlib.util
import struct
import unittest


class MoveSetterArithmeticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('arm_thumb_box_move_oracle.py');s=importlib.util.spec_from_file_location('move_halfword_arithmetic_test',p)
        cls.A=importlib.util.module_from_spec(s);s.loader.exec_module(cls.A)

    def fixture(self,flags=0xb800003f):return [0]*13+[0x4000,0x1101,flags],{0x3000:bytearray(b'\xa5'*4096)}

    def step(self,word,regs,pages,**guards):
        reads=[];stores=[];pc=self.A.thumb_step(0x1000,struct.pack('<H',word),regs,pages,reads,stores,**guards)
        self.assertEqual(reads,[]);return pc,stores

    def test_actual_word_unscaled_offset_low16_little_endian_and_neighbors(self):
        r,p=self.fixture();r[0]=6;r[5]=0x3002;r[1]=0x87654321;p[0x3000][8:10]=bytes.fromhex('d4c3');before=list(r)
        pc,stores=self.step(0x5229,r,p)
        self.assertEqual((pc,r),(0x1002,before))
        self.assertEqual(stores,[dict(pc=0x1000,address=0x3008,bytes=2,before='d4c3',value=0x4321)])
        self.assertEqual(p[0x3000],bytearray(b'\xa5'*8+b'\x21\x43'+b'\xa5'*(4096-10)))

    def test_register_offset_and_fields_are_not_an_immediate_or_scaled(self):
        for offset in range(0,64,2):
            for rb,rm,rd in((5,0,1),(7,6,3)):
                r,p=self.fixture();r[rb]=0x3002;r[rm]=offset;r[rd]=0x12345678
                _,stores=self.step(0x5200|(rm<<6)|(rb<<3)|rd,r,p)
                self.assertEqual((stores[0]['address'],stores[0]['value']),(0x3002+offset,0x5678))

    def test_store_preserves_all_flags_Q_and_registers(self):
        for flags in range(16):
            r,p=self.fixture((flags<<28)|0x800003f);r[5]=0x3000;r[0]=2;r[1]=65535;before=list(r)
            self.step(0x5229,r,p);self.assertEqual(r,before)

    def test_base_source_offset_aliases_use_old_operands(self):
        for word,values,address,value in((0x5209,{1:0x3002,0:6},0x3008,0x3002),
                 (0x5269,{1:6,5:0x3000},0x3006,6),(0x5249,{1:0x1802},0x3004,0x1802)):
            r,p=self.fixture()
            for i,v in values.items():r[i]=v
            before=list(r);_,stores=self.step(word,r,p)
            self.assertEqual((r,stores[0]['address'],stores[0]['value']),(before,address,value))

    def test_address_addition_wraps32(self):
        r,p=self.fixture();r[5]=0xfffffffe;r[0]=2;r[1]=0xffff1234;p[0]=bytearray(b'\xa5'*4096)
        _,stores=self.step(0x5229,r,p)
        self.assertEqual((stores[0]['address'],stores[0]['value'],p[0][:2]),(0,0x1234,b'\x34\x12'))

    def test_unaligned_domain_is_rejected_before_memory_or_mutation(self):
        r,p=self.fixture();r[5]=0xdead0000;r[0]=1;r[1]=17;before=list(r);old={a:bytes(b)for a,b in p.items()}
        with self.assertRaisesRegex(ValueError,'aligned Box move halfword'):
            self.step(0x5229,r,p)
        self.assertEqual((r,{a:bytes(b)for a,b in p.items()}),(before,old))

    def test_owner_guard_runs_before_preimage(self):
        r,p=self.fixture();r[5]=0xdead0000;r[0]=2;r[1]=17;before=list(r)
        with self.assertRaisesRegex(ValueError,'Box move halfword owner'):
            self.step(0x5229,r,p,write_guard=lambda *args:False)
        self.assertEqual(r,before)

    def test_finite_mask_excludes_other_register_memory_families(self):
        for word in(0x5000,0x5400,0x5600,0x5a00):
            with self.assertRaises(ValueError):self.A.validate_thumb(struct.pack('<H',word))
        self.assertNotEqual(self.A.validate_thumb(bytes.fromhex('0180')),'strh_register')

    def test_run_reuses_complete_effective_namespace_and_defaults(self):
        old=self.A.P.run;new=self.A.run
        self.assertIs(old.__code__,new.__code__);self.assertEqual(old.__defaults__,new.__defaults__)
        self.assertEqual(old.__kwdefaults__,new.__kwdefaults__);self.assertEqual(old.__globals__.keys(),new.__globals__.keys())
        self.assertEqual({k for k,v in old.__globals__.items()if new.__globals__[k]is not v},
                         {'source_identity_guard','validate_thumb','thumb_step'})
        self.A.source_identity_guard()


if __name__=='__main__':unittest.main()
