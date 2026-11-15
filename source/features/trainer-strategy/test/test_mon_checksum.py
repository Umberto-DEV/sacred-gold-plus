"""Owned native-checksum semantics and exact access contracts, no ROM or CPU."""
from pathlib import Path
import importlib.util
import struct
import unittest


p=Path(__file__).with_name('mon_checksum_bench.py');s=importlib.util.spec_from_file_location('checksum_contracts',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class ChecksumContractTest(unittest.TestCase):
    def test_pattern_little_endian_halfwords_not_bytes_or_big_endian(self):
        b=bytes(range(128))+b'\x5a'
        self.assertEqual(B.source_math(b,128),0xfc0)
        self.assertNotEqual(B.source_math(b,128),sum(b[:128])&65535)
        self.assertNotEqual(B.source_math(b,128),sum(x for x, in struct.iter_unpack('>H',b[:128]))&65535)

    def test_odd_size_ignores_tail(self):
        for tail in (0,90,255):
            b=bytes(range(128))+bytes([tail]);self.assertEqual(B.source_math(b,129),B.source_math(b,128))

    def test_overflow_is_unsigned16_zero_extended(self):
        value=B.source_math(b'\xff'*128+b'\x5a',128)
        self.assertEqual(value,0xffc0);self.assertNotIn(value,(0x3fffc0,-64))

    def test_zero_size_has_no_sum(self):
        self.assertEqual(B.source_math(bytes(range(129)),0),0)

    def test_typed_domain_rejects_bool_size_and_unsupported_storage(self):
        for data,size in ((bytes(129),True),(bytes(128),128),(bytes(129),1),(bytearray(129),128)):
            with self.assertRaises(ValueError):B.source_math(data,size)
        with self.assertRaises(ValueError):B.F.make_input({},True,False)
        with self.assertRaises(ValueError):B.F.make_input({},128,1)

    def test_data_access_never_includes_tail_or_zero_size(self):
        for size in (128,129):
            for a in range(B.F.BUF,B.F.BUF+128,2):self.assertTrue(B.read_owner(0x20725f2,a,2,halfwords=size//2))
            self.assertFalse(B.read_owner(0x20725f2,B.F.BUF+128,2,halfwords=size//2))
        self.assertFalse(B.read_owner(0x20725f2,B.F.BUF,2,halfwords=0))
        self.assertFalse(B.read_owner(0x20725f2,B.F.BUF,4))

    def test_stack_access_has_one_site_two_exact_words(self):
        for a in (B.R.TOP-8,B.R.TOP-4):
            self.assertTrue(B.write_owner(0x20725e8,a,4));self.assertTrue(B.read_owner(0x2072604,a,4))
        for a,n in ((B.R.TOP-12,4),(B.R.TOP-8,2),(B.F.BUF,4),(0x21d15a8,4)):
            self.assertFalse(B.write_owner(0x20725e8,a,n));self.assertFalse(B.read_owner(0x2072604,a,n))
        self.assertFalse(B.write_owner(0x20725ea,B.R.TOP-8,4))

    def test_cipher_pools_and_payload_are_never_writable(self):
        for pc in (0x20725e8,0x20725f2,0x2072604,0x201ff84):
            for a in (B.F.BUF,0x201ff90,0x20725dc,0x21d15a8):
                self.assertFalse(B.write_owner(pc,a,4));self.assertFalse(B.read_owner(pc,a,4))

    def test_replay_reuses_full_parent_logic_with_effective_checksum_owners(self):
        self.assertIs(B.require_memory_delta.__code__,B.C.require_memory_delta.__code__)
        self.assertIs(B.require_memory_delta.__globals__['write_owner'],B.write_owner)
        a=B.R.TOP-8;base=a&~4095;initial={base:bytes([165])*4096};final={base:bytearray(initial[base])}
        B.M.put(final,a,struct.pack('<I',17));final={k:bytes(v)for k,v in final.items()}
        x=dict(pc=0x20725e8,address=a,bytes=4,before='a5a5a5a5',value=17)
        B.require_memory_delta(initial,final,[x])
        with self.assertRaisesRegex(ValueError,'preimage'):B.require_memory_delta(initial,final,[{**x,'before':'00000000'}])
        with self.assertRaisesRegex(ValueError,'owner'):B.require_memory_delta(initial,final,[{**x,'address':B.F.BUF}])
        with self.assertRaisesRegex(ValueError,'replay'):B.require_memory_delta(initial,final,[])

    def test_parent_sources_remain_exact_and_no_arm_is_admitted(self):
        B.source_identity_guard();self.assertEqual(B.CODE_SPANS,());self.assertEqual((B.F.FRAME,B.F.GUARD),(8,56))


if __name__=='__main__':unittest.main()
