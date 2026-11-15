"""Owned intermediate-state and live Reset-frame counterexamples, no ROM/CPU."""
from pathlib import Path
import importlib.util
import unittest

p=Path(__file__).with_name('mon_reset_bench.py');s=importlib.util.spec_from_file_location('Reset_context_tests',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class MonResetContextTest(unittest.TestCase):
    def test_transient_PP24_Up0_is_not_standalone_PP15_input(self):
        stages,plains,keys,party=B.source_stages(3)
        self.assertEqual(keys,[0x2ab,0x2b4,0x2b1,0x2a8])
        self.assertEqual([(p[72],p[76])for p in plains],[(15,3),(24,3),(24,0),(15,0)])
        self.assertEqual(len({p[136:]for p in stages}),1)
        self.assertNotEqual(stages[2],B.F.MON.owned_mon(0)[0])
        self.assertEqual(stages[3],B.F.MON.owned_mon(0)[0])
    def test_idempotent_counter_has_unchanged_Mon_but_calls_still_required(self):
        stages,plains,keys,party=B.source_stages(0)
        self.assertEqual(len(set(stages)),1);self.assertEqual(keys,[0x2a8]*4)
        for value in(True,1,4,-1):
            with self.assertRaises(ValueError):B.source_stages(value)
    def test_same_PP_read_PC_has_two_live_Value_owners_with_byte_width(self):
        for address in(B.F.PP_VALUE,B.F.RESET_PP_VALUE):self.assertTrue(B.read_owner(0x206f0f6,address,1))
        self.assertFalse(B.read_owner(0x206f0f6,B.F.ZERO_VALUE,1))
        self.assertFalse(B.read_owner(0x206f0f6,B.F.RESET_PP_VALUE,4))
        self.assertTrue(B.read_owner(0x206f106,B.F.ZERO_VALUE,1))
    def test_guest_Value_word_publications_cannot_be_byte_stores(self):
        for pc,address in((0x20714c2,B.F.ZERO_VALUE),(0x20714d8,B.F.RESET_PP_VALUE)):
            self.assertTrue(B.write_owner(pc,address,4))
            for width in(1,2):self.assertFalse(B.write_owner(pc,address,width))
        self.assertFalse(B.write_owner(0x207151c,B.F.RESET_PP_VALUE,1))
    def test_legacy_MAX_fallback_cannot_touch_live_Reset_frame(self):
        for pc,width in B.BOX.MAX.READ_SITES:
            if width==4:self.assertFalse(B.read_owner(pc,B.R.TOP-16,4))
        for pc,width in B.BOX.MAX.WRITE_SITES:
            if width==4:self.assertFalse(B.write_owner(pc,B.F.ZERO_VALUE,4))
    def test_two_cipher_seed_depths_and_PP_epilogues_are_distinct(self):
        for address in(B.R.TOP-80,B.R.TOP-48):self.assertTrue(B.write_owner(0x201ff84,address,4))
        self.assertFalse(B.write_owner(0x201ff84,B.R.TOP-24,4))
        for address in(B.R.TOP-96,B.R.TOP-72):self.assertTrue(B.read_owner(0x206f102,address,4))
        self.assertFalse(B.read_owner(0x206f102,B.R.TOP-40,4))


if __name__=='__main__':unittest.main()
