"""Owned move-u16 fixture, idempotent replay and contextual memory contracts."""
from pathlib import Path
import importlib.util
import struct
import unittest

p=Path(__file__).with_name('box_move_setter_bench.py');s=importlib.util.spec_from_file_location('move_setter_contracts',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class MoveSetterContractTest(unittest.TestCase):
    def test_idempotent_and_causal_move_outputs_follow_two_native_keys(self):
        for value,key,seed63,seed64 in((310,0x2ab,0x85732c58,0x8d9d11eb),(311,0x2ac,0x43b984bd,0x039d7aec)):
            initial,plain,final,updated,checksum,seeds=B.source_result(value)
            self.assertEqual((checksum,seeds[-2],seeds[-1]),(key,seed63,seed64))
            self.assertEqual(B.crypt(final[8:],key)[0],updated)
            self.assertEqual(struct.unpack_from('<H',updated,64)[0],value)
            self.assertEqual((updated[72],updated[76]),(15,3))
            self.assertEqual(initial==final,value==310)
            self.assertEqual([i for i,(a,b)in enumerate(zip(plain,updated))if a!=b],[]if value==310 else[64])
            self.assertEqual((plain[65],updated[65]),(1,1))

    def test_source_math_typed_finite_move_domain(self):
        for value in(True,False,309,312,310.0,-1):
            with self.assertRaises(ValueError):B.source_result(value)
            with self.assertRaises(ValueError):B.F.make_input({},value)

    def test_profile_counts_fullcaller_static_only_and_stack_budget(self):
        self.assertEqual(B.F.MATRIX,(('Move310','Move310',True),('Move311','Move311',True),('Move310_OFF','Move310',False)))
        self.assertEqual((B.F.ENTRY,B.F.FRAME,B.F.GUARD),(0x206ed70,136,56))
        self.assertEqual((sum(v[1]for v in B.L.THUMB.values()),sum(v[1]for v in B.L.DATA.values())),(328,528))
        self.assertEqual((B.L.CALLER[0],B.L.CALLER[1]),(0x20714f0,66))
        self.assertNotIn('static_caller',B.L.THUMB);self.assertNotIn('static_caller',B.L.DATA)

    def test_move_writer_is_halfword_not_byte_or_PP_field(self):
        self.assertTrue(B.write_owner(0x206f0f0,B.F.BOX+72,2))
        for address,size in((B.F.BOX+72,1),(B.F.BOX+72,4),(B.F.BOX+80,2),(B.F.BOX+84,2)):
            self.assertFalse(B.write_owner(0x206f0f0,address,size))

    def test_header_checksum_only_halfword_write(self):
        self.assertTrue(B.write_owner(0x206edd6,B.F.BOX+6,2))
        for address,size in((B.F.BOX,4),(B.F.BOX+4,2),(B.F.BOX+6,1),(B.F.BOX+6,4)):
            self.assertFalse(B.write_owner(0x206edd6,address,size))

    def test_Value_read_requires_both_bytes_at_its_own_address(self):
        self.assertTrue(B.read_owner(0x206f0e6,B.F.VALUE,2))
        self.assertFalse(B.read_owner(0x206f0e6,B.F.VALUE,1))
        self.assertFalse(B.read_owner(0x206f0e6,B.F.BOX+72,2))
        self.assertTrue(B.read_owner(0x206edda,B.F.BOX+6,2))

    def test_leaf_epilogue_and_normalized_local_are_new_sites(self):
        self.assertTrue(B.read_owner(0x206f0f2,B.R.TOP-40,4))
        self.assertFalse(B.read_owner(0x206f102,B.R.TOP-40,4))
        self.assertTrue(B.write_owner(0x206f0ea,B.R.TOP-116,4))
        self.assertFalse(B.write_owner(0x206f0fa,B.R.TOP-116,4))

    def test_seed_slot_retains_actual_outer_frame_depth(self):
        self.assertTrue(B.write_owner(0x201ff84,B.R.TOP-24,4))
        self.assertTrue(B.read_owner(0x201ff78,B.R.TOP-24,4))
        self.assertFalse(B.write_owner(0x201ff84,B.R.TOP-8,4))

    def test_idempotent_replay_does_not_replace_native_store_evidence(self):
        base=B.F.BOX&~4095;page=bytearray(b'\xa5'*4096);B.M.put({base:page},B.F.BOX+72,struct.pack('<H',310));initial={base:bytes(page)}
        x=dict(pc=0x206f0f0,address=B.F.BOX+72,bytes=2,before='3601',value=310)
        B.require_memory_delta(initial,initial,[x])
        # An unchanged endpoint also admits an empty replay. The completed raw
        # verifier separately requires the source store transcript and count.
        B.require_memory_delta(initial,initial,[])
        with self.assertRaisesRegex(ValueError,'preimage'):B.require_memory_delta(initial,initial,[{**x,'before':'3600'}])
        with self.assertRaisesRegex(ValueError,'owner'):B.require_memory_delta(initial,initial,[{**x,'bytes':1,'before':'36','value':0x36}])

    def test_parent_chain_remains_pinned_and_no_ARM_corpus_added(self):
        B.source_identity_guard();self.assertEqual(B.CODE_SPANS,())
        self.assertIs(B.crypt,B.G.crypt);self.assertIs(B.require_memory_delta.__code__,B.G.require_memory_delta.__code__)


if __name__=='__main__':unittest.main()
