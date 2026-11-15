"""Owned STRB immediate contracts for the finite Box PP setter; no ROM/CPU."""
from pathlib import Path
import importlib.util
import struct
import unittest


class BoxSetterArithmeticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('arm_thumb_box_setter_oracle.py');s=importlib.util.spec_from_file_location('box_setter_arithmetic_test',p)
        cls.A=importlib.util.module_from_spec(s);s.loader.exec_module(cls.A)

    def fixture(self,flags=0xb000003f):
        return [0]*13+[0x4000,0x1101,flags],{0x3000:bytearray(b'\xa5'*4096)}

    def step(self,op,r,p,**guards):
        reads=[];stores=[];pc=self.A.thumb_step(0x1000,struct.pack('<H',op),r,p,reads,stores,**guards)
        self.assertEqual(reads,[]);return pc,stores

    def test_strb_actual_word_stores_low8_at_unscaled_offset(self):
        r,p=self.fixture();r[0]=0x3001;r[1]=0x87654318;before=list(r)
        pc,stores=self.step(0x7201,r,p)
        self.assertEqual((pc,r),(0x1002,before))
        self.assertEqual(stores,[dict(pc=0x1000,address=0x3009,bytes=1,before='a5',value=24)])
        self.assertEqual(p[0x3000],bytearray(b'\xa5'*9+b'\x18'+b'\xa5'*(4096-10)))

    def test_strb_all_imm5_offsets_and_low_register_fields(self):
        for imm in range(32):
            for rb,rd in((0,1),(7,3)):
                r,p=self.fixture();r[rb]=0x3001;r[rd]=0x12345680+imm
                pc,stores=self.step(0x7000|(imm<<6)|(rb<<3)|rd,r,p)
                self.assertEqual((pc,stores[0]['address'],stores[0]['value']),(0x1002,0x3001+imm,0x80+imm))

    def test_strb_preserves_all_flags_and_all_registers(self):
        for flags in range(16):
            r,p=self.fixture((flags<<28)|0x800003f);r[0]=0x3000;r[1]=255;before=list(r)
            self.step(0x7201,r,p);self.assertEqual(r,before)

    def test_strb_base_and_source_alias_use_old_register(self):
        r,p=self.fixture();r[1]=0x3003;before=list(r)
        _,stores=self.step(0x7049,r,p)
        self.assertEqual((r,stores[0]['address'],stores[0]['value']),(before,0x3004,3))

    def test_strb_address_wrap_is_u32(self):
        r,p=self.fixture();r[0]=0xfffffff8;r[1]=0x123456fe;p[0]=bytearray(b'\xa5'*4096)
        _,stores=self.step(0x7201,r,p);self.assertEqual((stores[0]['address'],stores[0]['value']),(0,254))

    def test_store_guard_runs_before_preimage_or_mutation(self):
        r,p=self.fixture();r[0]=0xdead0000;r[1]=17;before=list(r);old={a:bytes(b)for a,b in p.items()}
        with self.assertRaisesRegex(ValueError,'Box setter byte owner'):
            self.step(0x7201,r,p,write_guard=lambda *args:False)
        self.assertEqual((r,{a:bytes(b)for a,b in p.items()}),(before,old))

    def test_new_mask_does_not_admit_register_byte_store_or_halfword_register_store(self):
        for word in(0x5401,0x5201,0x5601):
            with self.assertRaises(ValueError):self.A.validate_thumb(struct.pack('<H',word))

    def test_run_keeps_effective_namespace_bytecode_and_defaults(self):
        old=self.A.P.run;new=self.A.run
        self.assertIs(old.__code__,new.__code__);self.assertEqual(old.__defaults__,new.__defaults__)
        self.assertEqual(old.__kwdefaults__,new.__kwdefaults__);self.assertEqual(old.__globals__.keys(),new.__globals__.keys())
        self.assertEqual({k for k,v in old.__globals__.items()if new.__globals__[k]is not v},
                         {'source_identity_guard','validate_thumb','thumb_step'})
        self.A.source_identity_guard()


if __name__=='__main__':unittest.main()
