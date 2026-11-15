"""Owned geometry/ABI/activation guards; no ROM, compiler or CPU."""
from pathlib import Path
import importlib.util
import unittest


p=Path(__file__).with_name('reset_c_bench.py');s=importlib.util.spec_from_file_location('C_Reset_context_test',p)
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


class ResetCContextTest(unittest.TestCase):
    def test_CPU_instruction_subset_needs_no_inactive_Reset_or_data_parts(self):
        parts={name:('owned-'+name).encode()for name in B.F.THUMB}
        selected=B.F.instruction_parts(parts)
        self.assertEqual(selected,parts);self.assertNotIn('reset',selected)
        self.assertEqual(B.F.instruction_parts({**parts,'reset':b'owned inactive reference','data':b'owned data'}),parts)
        missing=dict(parts);missing.pop(next(iter(missing)))
        with self.assertRaises(ValueError):B.F.instruction_parts(missing)
    def test_code_admission_excludes_the_original_Reset(self):
        self.assertNotIn('reset',B.F.THUMB)
        self.assertEqual(sum(x[1]for x in B.F.C_THUMB.values()),64)
        self.assertEqual(sum(x[2]for x in B.F.C_THUMB.values()),28)
        for pc in range(0x20714b0,0x20714e8,2):
            self.assertFalse(B.read_owner(pc,B.F.ZERO_VALUE,4));self.assertFalse(B.write_owner(pc,B.F.ZERO_VALUE,4))
    def test_live_frame_is32_bytes_and_only_C_POP_reads_saved_words(self):
        for a in range(B.F.CHILD_TOP,B.R.TOP,4):
            self.assertTrue(B.write_owner(B.F.ENTRY,a,4));self.assertTrue(B.read_owner(B.F.BASE+74,a,4))
            self.assertFalse(B.read_owner(0x20714e6,a,4))
            for pc,width in B.BOX.MAX.WRITE_SITES:
                if width==4:self.assertFalse(B.write_owner(pc,a,4))
    def test_zero_and_PP_are_int_guest_publications_with_byte_consumers(self):
        for pc,a in((B.F.BASE+38,B.F.ZERO_VALUE),(B.F.BASE+60,B.F.RESET_PP_VALUE)):
            self.assertTrue(B.write_owner(pc,a,4))
            for n in(1,2):self.assertFalse(B.write_owner(pc,a,n))
        self.assertTrue(B.read_owner(0x206f106,B.F.ZERO_VALUE,1))
        self.assertTrue(B.read_owner(0x206f0f6,B.F.RESET_PP_VALUE,1))
        self.assertFalse(B.read_owner(0x206f0f6,B.F.ZERO_VALUE,1))
        self.assertFalse(B.read_owner(0x206f106,B.F.ZERO_VALUE,4))
    def test_guest_thunks_only_read_their_own_literal(self):
        for i in(0,8,16):
            self.assertTrue(B.read_owner(B.F.BASE+i,B.F.BASE+i+4,4))
            self.assertFalse(B.read_owner(B.F.BASE+i,B.F.BASE+((i+8)%24)+4,4))
            self.assertFalse(B.read_owner(B.F.BASE+i,B.F.BASE+i+4,2))
    def test_native_cipher_depths_and_two_PP_epilogues_remain_distinct(self):
        for a in(B.R.TOP-88,B.R.TOP-56):self.assertTrue(B.write_owner(0x201ff84,a,4))
        self.assertFalse(B.write_owner(0x201ff84,B.R.TOP-32,4))
        for a in(B.R.TOP-104,B.R.TOP-80):self.assertTrue(B.read_owner(0x206f102,a,4))
        self.assertFalse(B.read_owner(0x206f102,B.F.ZERO_VALUE,4))
    def test_retained_math_requires_all_intermediate_states(self):
        stages,plains,keys,party=B.source_stages(3)
        self.assertEqual(keys,[0x2ab,0x2b4,0x2b1,0x2a8]);self.assertEqual([(x[72],x[76])for x in plains],[(15,3),(24,3),(24,0),(15,0)])
        self.assertNotEqual(stages[2],stages[-1]);self.assertEqual(stages[-1],B.F.OLD.MON.owned_mon(0)[0])


if __name__=='__main__':unittest.main()
