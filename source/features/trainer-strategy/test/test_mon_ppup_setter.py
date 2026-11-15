"""Owned Mon geometry, cipher false greens and contextual access boundaries."""
from pathlib import Path
import importlib.util
import unittest

p=Path(__file__).with_name('mon_ppup_setter_bench.py');s=importlib.util.spec_from_file_location('Mon_contract_tests',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class MonSetterContractTest(unittest.TestCase):
    def test_owned_input_has_two_distinct_keys_and_only_PPUp_plaintext_delta(self):
        a,plain,party,final,updated=B.source_result(3)
        self.assertEqual((len(a),len(party),int.from_bytes(a[6:8],'little')),(236,100,0x2ab))
        self.assertEqual(B.crypt(a[8:136],0x2ab)[0],plain)
        self.assertEqual(B.crypt(a[136:],0x4000)[0],party)
        self.assertEqual([i for i,(x,y)in enumerate(zip(plain,updated))if x!=y],[76])
        self.assertEqual(a[136:],final[136:]);self.assertEqual(B.source_result(0)[0],final)
    def test_finite_input_domain_rejects_bool_and_other_Up(self):
        for ups in(True,False,1,2,4,-1,3.0):
            with self.assertRaises(ValueError):B.source_result(ups)
    def test_wrong_key_twice_and_no_cipher_both_have_same_endpoint(self):
        mon,_,party=B.F.owned_mon(3);cipher=mon[136:]
        wrongplain=B.crypt(cipher,0x2ab)[0]
        self.assertNotEqual(wrongplain,party)
        self.assertEqual(B.crypt(wrongplain,0x2ab)[0],cipher)
        self.assertEqual(B.crypt(B.crypt(cipher,0x4000)[0],0x4000)[0],cipher)
        # Therefore final equality alone cannot establish either correct key
        # or execution; the verifier requires each read/store/preimage/seed.
    def test_mon_leaf_is_byte_PPUp_and_Value_is_low_byte_read_only(self):
        self.assertTrue(B.write_owner(0x206f10e,B.F.BOX+84,1))
        self.assertTrue(B.read_owner(0x206f106,B.F.VALUE,1))
        for a,n in((B.F.BOX+80,1),(B.F.BOX+84,2),(B.F.VALUE,1),(B.F.BOX+236,1)):
            self.assertFalse(B.write_owner(0x206f10e,a,n))
        self.assertFalse(B.read_owner(0x206f106,B.F.VALUE,4))
    def test_party_cipher_can_access_all100_but_not_guards_or_checksum(self):
        for a in range(B.F.BOX+136,B.F.BOX+236,2):
            self.assertTrue(B.read_owner(0x201ff58,a,2));self.assertTrue(B.write_owner(0x201ff5e,a,2))
            self.assertFalse(B.read_owner(0x20725f2,a,2))
        for a in(B.F.BOX+6,B.F.BOX+236,B.F.BOX-2):
            self.assertFalse(B.write_owner(0x201ff5e,a,2))
    def test_extra_bridge_changes_internal_stack_but_not_outer_seed_slot(self):
        self.assertTrue(B.write_owner(0x2072608,B.R.TOP-144,4))
        self.assertFalse(B.write_owner(0x2072608,B.R.TOP-128,4))
        self.assertTrue(B.read_owner(0x206f104,B.R.TOP-124,4))
        self.assertFalse(B.read_owner(0x206f104,B.R.TOP-116,4))
        self.assertTrue(B.write_owner(0x201ff84,B.R.TOP-24,4))
        self.assertFalse(B.write_owner(0x201ff84,B.R.TOP-32,4))
    def test_header_PID_checksum_and_table_row_are_distinct_owners(self):
        self.assertTrue(B.read_owner(0x206ec52,B.F.BOX,4))
        self.assertTrue(B.read_owner(0x206ecc2,B.F.BOX+6,2))
        self.assertTrue(B.read_owner(0x206ee34,0x206eeb8,2))
        self.assertFalse(B.read_owner(0x206ee34,0x206eeb0,2))
        self.assertFalse(B.write_owner(0x206ecbe,B.F.BOX+4,2))
    def test_replay_requires_preimage_even_for_idempotent_store(self):
        base=B.F.BOX&~4095;page=bytearray(b'\xa5'*4096);B.M.put({base:page},B.F.BOX+84,b'\0');initial={base:bytes(page)}
        store=dict(pc=0x206f10e,address=B.F.BOX+84,bytes=1,before='00',value=0)
        B.require_memory_delta(initial,initial,[store])
        with self.assertRaisesRegex(ValueError,'preimage'):B.require_memory_delta(initial,initial,[{**store,'before':'03'}])
        with self.assertRaisesRegex(ValueError,'owner'):B.require_memory_delta(initial,initial,[{**store,'address':B.F.VALUE}])


if __name__=='__main__':unittest.main()
