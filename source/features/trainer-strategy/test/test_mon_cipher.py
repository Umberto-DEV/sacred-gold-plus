"""Owned cipher source/owner/ABI contracts without ROM or CPU dependencies."""
from pathlib import Path
import importlib.util
import struct
import unittest


p=Path(__file__).with_name('mon_cipher_bench.py');s=importlib.util.spec_from_file_location('cipher_contracts',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class CipherContractTest(unittest.TestCase):
    def test_owned_cipher_digest_and_seed63_vs64(self):
        for seed,a,b in ((0xfc0,0xb3b58da1,0x40fabc00),(0xfc1,0x71fbe606,0xb6fb2501)):
            out,seeds=B.source_math(bytes(range(128)),seed)
            self.assertEqual((len(out),len(seeds),seeds[-2:]),(128,64,[a,b]))
            self.assertEqual(B.R.sha(out),B.CIPHER_SHA[seed])

    def test_advance_then_high16_little_endian_has_independent_first_words(self):
        self.assertEqual(B.source_math(bytes(range(128)),0xfc0)[0][:8].hex(),'53f27c69c90b041f')
        self.assertEqual(B.source_math(bytes(range(128)),0xfc1)[0][:8].hex(),'1934232e4f8a0e01')

    def test_math_domain_rejects_bool_short_and_unqualified_seed(self):
        for data,seed in ((bytes(128),True),(bytes(126),0xfc0),(bytes(128),0),(bytearray(128),0xfc0)):
            with self.assertRaises(ValueError):B.source_math(data,seed)

    def test_synthetic_pattern_checksum_is_only_host_math(self):
        self.assertEqual(sum(v for v, in struct.iter_unpack('<H',bytes(range(128))))&65535,0xfc0)

    def test_seed_owner_is_one_local_word_at_one_site(self):
        self.assertTrue(B.read_owner(0x201ff78,B.R.TOP-8,4));self.assertTrue(B.write_owner(0x201ff84,B.R.TOP-8,4))
        for a,n in ((B.R.TOP-4,4),(B.R.TOP-8,2),(B.F.GLOBAL,4),(B.F.BUF,4)):
            self.assertFalse(B.read_owner(0x201ff78,a,n));self.assertFalse(B.write_owner(0x201ff84,a,n))

    def test_saved_argument_and_return_owners_are_exact(self):
        self.assertEqual([B.write_owner(0x201ff44,B.R.TOP-d,4)for d in range(4,44,4)],[True]*4+[False]*6)
        self.assertEqual([B.read_owner(0x201ff68,B.R.TOP-d,4)for d in(16,20,24)],[False,True,False])
        self.assertTrue(all(B.write_owner(0x201ff46,a,4)for a in range(B.R.TOP-40,B.R.TOP-16,4)))

    def test_buffer_halfword_ownership_excludes_guards_and_byte_aliases(self):
        for pc,fn in ((0x201ff58,B.read_owner),(0x201ff5e,B.write_owner)):
            self.assertTrue(all(fn(pc,a,2)for a in range(B.F.BUF,B.F.BUF+128,2)))
            self.assertFalse(fn(pc,B.F.BUF-2,2));self.assertFalse(fn(pc,B.F.BUF+128,2));self.assertFalse(fn(pc,B.F.BUF,4))

    def test_pool_read_sites_do_not_authorize_pool_writes_or_other_addresses(self):
        for pc,a in ((0x20725d8,0x20725dc),(0x201ff7a,0x201ff90),(0x201ff80,0x201ff94)):
            self.assertTrue(B.read_owner(pc,a,4));self.assertFalse(B.read_owner(pc,a+4,4));self.assertFalse(B.write_owner(pc,a,4))

    def test_global_rng_is_never_an_allowed_access(self):
        for pc in (0x201ff44,0x201ff46,0x201ff58,0x201ff78,0x201ff84,0x201ff5e):
            self.assertFalse(B.read_owner(pc,B.F.GLOBAL,4));self.assertFalse(B.write_owner(pc,B.F.GLOBAL,4))

    def test_whole_map_replay_and_inverse_reject_wrong_preimage_and_unowned_write(self):
        a=B.R.TOP-8;base=a&~4095;initial={base:bytes([165])*4096};final={base:bytearray(initial[base])}
        B.M.put(final,a,struct.pack('<I',17));final={k:bytes(v)for k,v in final.items()}
        x=dict(pc=0x201ff84,address=a,bytes=4,before='a5a5a5a5',value=17)
        B.require_memory_delta(initial,final,[x])
        with self.assertRaisesRegex(ValueError,'preimage'):B.require_memory_delta(initial,final,[{**x,'before':'00000000'}])
        with self.assertRaisesRegex(ValueError,'owner'):B.require_memory_delta(initial,final,[{**x,'pc':0x201ff86}])
        with self.assertRaisesRegex(ValueError,'replay'):B.require_memory_delta(initial,final,[])

    def test_replay_rejects_bool_value_and_extra_page(self):
        a=B.R.TOP-8;base=a&~4095;pages={base:bytes(4096)}
        with self.assertRaisesRegex(ValueError,'owner'):B.require_memory_delta(pages,pages,[dict(pc=0x201ff84,address=a,bytes=4,before='00000000',value=True)])
        with self.assertRaisesRegex(ValueError,'mapped owners'):B.require_memory_delta(pages,{**pages,0x1000:bytes(4096)},[])

    def test_no_arm_spans_and_unchanged_producer_source(self):
        self.assertEqual(B.CODE_SPANS,())
        self.assertEqual(B.R.sha(Path(B.P.__file__).read_bytes()),B.PRODUCER_SHA)
        self.assertEqual(B.F.FRAME,40);self.assertEqual(B.F.GUARD,56)
        with self.assertRaises(ValueError):B.F.make_input({},True)


if __name__=='__main__':unittest.main()
