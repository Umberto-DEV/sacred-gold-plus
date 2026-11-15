"""Owned Box fixture/layout, contextual memory admission and replay contracts."""
from pathlib import Path
import importlib.util
import struct
import unittest

p=Path(__file__).with_name('box_ppup_bench.py');s=importlib.util.spec_from_file_location('box_contracts',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class BoxContractTest(unittest.TestCase):
    def test_owned_pair_changes_only_two_ciphertext_bytes_with_constant_checksum(self):
        a,plain=B.F.owned_box(3);b,counter=B.F.owned_box(1)
        self.assertEqual([i for i,(x,y)in enumerate(zip(a,b))if x!=y],[10,84])
        self.assertEqual(a[:8],struct.pack('<IHH',0x4000,0,0x2ab));self.assertEqual(a[:8],b[:8])
        self.assertTrue(all(a[i]^b[i]==2 for i in(10,84)))
        self.assertEqual((plain[72],counter[72],plain[76],counter[76]),(15,15,3,1))
        self.assertEqual((struct.unpack_from('<H',counter,2)[0],plain[2]),(2,0))

    def test_fixture_typed_finite_scope(self):
        for value in(True,False,0,2,4,255,-1,1.0):
            with self.assertRaises(ValueError):B.F.owned_box(value)

    def test_cipher_math_is_reversible_and_constant_key_restarts(self):
        for ups in(1,3):
            box,plain=B.F.owned_box(ups);cipher,seeds=B.crypt(plain,0x2ab)
            self.assertEqual(cipher,box[8:]);self.assertEqual(B.crypt(cipher,0x2ab)[0],plain)
            self.assertEqual((len(seeds),seeds[-2],seeds[-1]),(64,0x85732c58,0x8d9d11eb))

    def test_full_getter_entry_and_finite_matrix(self):
        self.assertEqual((B.F.ENTRY,B.F.FRAME,B.F.GUARD),(0x206e640,64,56))
        self.assertEqual(B.F.MATRIX,(('PPUp3','PPUp3',True),('PPUp1','PPUp1',True),('PPUp3_OFF','PPUp3',False)))
        self.assertEqual((len(B.L.THUMB),len(B.L.DATA)),(14,7))
        self.assertEqual((sum(v[1]for v in B.L.THUMB.values()),sum(v[1]for v in B.L.DATA.values())),(324,528))

    def test_header_is_readonly_and_currentPP_is_not_field_read(self):
        self.assertTrue(B.read_owner(0x206e986,B.F.BOX+84,1))
        self.assertFalse(B.read_owner(0x206e986,B.F.BOX+80,1))
        for pc in(0x206e640,0x206e982,0x201ff5e):
            for address in range(B.F.BOX,B.F.BOX+8):
                self.assertFalse(B.write_owner(pc,address,2));self.assertFalse(B.write_owner(pc,address,4))

    def test_crypto_seed_lifetime_is_TOPminus24_not_standalone_parent_slot(self):
        for pc,owner in((0x201ff78,B.read_owner),(0x201ff84,B.write_owner)):
            self.assertTrue(owner(pc,B.R.TOP-24,4));self.assertFalse(owner(pc,B.R.TOP-8,4))

    def test_substructure_table_row2_and_dispatch_row62_exact(self):
        for address in range(0x20ff73b,0x20ff73f):self.assertTrue(B.read_owner(0x2072626,address,1))
        self.assertFalse(B.read_owner(0x2072626,0x20ff733,1))
        self.assertTrue(B.read_owner(0x206e6ee,0x206e772,2))
        self.assertFalse(B.read_owner(0x206e6ee,0x206e770,2))

    def test_transient_normalized_attribute_has_its_own_writer(self):
        self.assertTrue(B.write_owner(0x206e982,B.R.TOP-44,4))
        self.assertFalse(B.write_owner(0x206e982,B.R.TOP-40,4))
        self.assertFalse(B.write_owner(0x206e982,B.R.TOP-44,2))

    def test_replay_checks_preimage_inverse_and_all_pages(self):
        base=(B.R.TOP-44)&~4095;initial={base:bytes([165])*4096};target={base:bytearray(initial[base])}
        B.M.put(target,B.R.TOP-44,struct.pack('<I',0));final={a:bytes(b)for a,b in target.items()}
        x=dict(pc=0x206e982,address=B.R.TOP-44,bytes=4,before='a5a5a5a5',value=0)
        B.require_memory_delta(initial,final,[x])
        with self.assertRaisesRegex(ValueError,'preimage'):B.require_memory_delta(initial,final,[{**x,'before':'3e000000'}])
        with self.assertRaisesRegex(ValueError,'owner'):B.require_memory_delta(initial,final,[{**x,'address':B.F.BOX}])
        with self.assertRaisesRegex(ValueError,'replay'):B.require_memory_delta(initial,final,[])

    def test_parents_are_pinned_and_no_ARM_corpus_is_added(self):
        B.source_identity_guard();self.assertEqual(B.CODE_SPANS,())
        self.assertIs(B.require_memory_delta.__code__,B.C.require_memory_delta.__code__)


if __name__=='__main__':unittest.main()
