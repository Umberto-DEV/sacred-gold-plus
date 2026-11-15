"""Owned setter source math, data ownership and exact replay contracts."""
from pathlib import Path
import importlib.util
import struct
import unittest

p=Path(__file__).with_name('box_pp_setter_bench.py');s=importlib.util.spec_from_file_location('setter_contracts',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class BoxSetterContractTest(unittest.TestCase):
    def test_new_checksum_and_key_follow_only_currentPP_change(self):
        for value,checksum,seed63,seed64 in((24,0x2b4,0x35ec47e5,0xb3a0c2f4),(23,0x2b3,0x77a5ef80,0x3da059f3)):
            initial,plain,final,updated,key,seeds=B.source_result(value)
            self.assertEqual([i for i,(a,b)in enumerate(zip(plain,updated))if a!=b],[72])
            self.assertEqual((key,seeds[-2],seeds[-1]),(checksum,seed63,seed64))
            self.assertEqual(B.crypt(final[8:],key)[0],updated)
            self.assertNotEqual(B.crypt(final[8:],0x2ab)[0],updated)
            self.assertEqual(initial[:6],final[:6]);self.assertEqual(final[6:8],struct.pack('<H',checksum))
            self.assertEqual((updated[72],updated[76]),(value,3))

    def test_source_math_typed_finite_domain(self):
        for value in(True,False,22,25,24.0,-1):
            with self.assertRaises(ValueError):B.source_result(value)
            with self.assertRaises(ValueError):B.F.make_input({},value)

    def test_two_profiles_three_calls_and_exact_stack_budget(self):
        self.assertEqual(B.F.MATRIX,(('PP24','PP24',True),('PP23','PP23',True),('PP24_OFF','PP24',False)))
        self.assertEqual((B.F.ENTRY,B.F.FRAME,B.F.GUARD),(0x206ed70,136,56))
        self.assertEqual((sum(v[1]for v in B.L.THUMB.values()),sum(v[1]for v in B.L.DATA.values())),(328,528))
        self.assertNotIn('static_caller',B.L.THUMB);self.assertNotIn('static_caller',B.L.DATA)
        self.assertEqual((B.L.CALLER[0],B.L.CALLER[1]),(0x2071512,26))

    def test_PP_writer_is_one_byte_at_currentPP_not_PPUp(self):
        self.assertTrue(B.write_owner(0x206f0fe,B.F.BOX+80,1))
        for a,n in((B.F.BOX+84,1),(B.F.BOX+80,2),(B.F.BOX+80,4),(B.F.VALUE,1)):
            self.assertFalse(B.write_owner(0x206f0fe,a,n))

    def test_header_only_checksum_word_can_be_written(self):
        self.assertTrue(B.write_owner(0x206edd6,B.F.BOX+6,2))
        for pc in(0x206edd6,0x206f0fe,0x201ff5e):
            for a,n in((B.F.BOX,4),(B.F.BOX+4,2),(B.F.BOX+6,4),(B.F.BOX+6,1)):
                self.assertFalse(B.write_owner(pc,a,n))

    def test_Value_load_and_new_header_key_load_are_precise(self):
        self.assertTrue(B.read_owner(0x206f0f6,B.F.VALUE,1))
        self.assertFalse(B.read_owner(0x206f0f6,B.F.BOX+80,1))
        self.assertTrue(B.read_owner(0x206edda,B.F.BOX+6,2))
        self.assertFalse(B.read_owner(0x206edda,B.F.BOX+4,2))

    def test_selector_frame_and_local_attribute_are_not_old_getter_offsets(self):
        self.assertTrue(B.write_owner(0x2072608,B.R.TOP-136,4))
        self.assertFalse(B.write_owner(0x2072608,B.R.TOP-64,4))
        self.assertTrue(B.read_owner(0x207262c,B.R.TOP-124,4))
        self.assertTrue(B.write_owner(0x206f0fa,B.R.TOP-116,4))
        self.assertFalse(B.write_owner(0x206f0fa,B.R.TOP-44,4))

    def test_retained_crypto_seed_slot_remains_TOPminus24(self):
        self.assertTrue(B.write_owner(0x201ff84,B.R.TOP-24,4))
        self.assertTrue(B.read_owner(0x201ff78,B.R.TOP-24,4))
        self.assertFalse(B.write_owner(0x201ff84,B.R.TOP-8,4))

    def test_replay_checks_byte_preimage_whole_map_and_inverse(self):
        base=B.F.BOX&~4095;initial={base:bytes([165])*4096};p={base:bytearray(initial[base])}
        B.M.put(p,B.F.BOX+80,b'\x18');final={a:bytes(b)for a,b in p.items()}
        x=dict(pc=0x206f0fe,address=B.F.BOX+80,bytes=1,before='a5',value=24)
        B.require_memory_delta(initial,final,[x])
        with self.assertRaisesRegex(ValueError,'preimage'):B.require_memory_delta(initial,final,[{**x,'before':'0f'}])
        with self.assertRaisesRegex(ValueError,'owner'):B.require_memory_delta(initial,final,[{**x,'bytes':2}])
        with self.assertRaisesRegex(ValueError,'replay'):B.require_memory_delta(initial,final,[])

    def test_parent_primitives_pinned_no_ARM_or_producer_bytecode_changes(self):
        B.source_identity_guard();self.assertEqual(B.CODE_SPANS,())
        self.assertIs(B.require_memory_delta.__code__,B.G.require_memory_delta.__code__)
        self.assertIs(B.crypt,B.G.crypt)


if __name__=='__main__':unittest.main()
