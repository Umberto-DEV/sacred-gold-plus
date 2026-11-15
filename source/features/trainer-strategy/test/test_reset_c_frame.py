"""Pure counterexamples for the owned volatile-slot frame; never invokes CPU."""
from pathlib import Path
import copy
import importlib.util
import unittest


class ResetCFrameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/qualifica_reset_c_frame.py';s=importlib.util.spec_from_file_location('Reset_C_frame_test',p)
        cls.T=importlib.util.module_from_spec(s);s.loader.exec_module(cls.T)
    def test_hard_scalar_frame_and_full16_match_retained_source(self):
        k=self.T.kernel();hard=self.T.hard_forecast(k);p=self.T.source_forecast(k)
        self.assertEqual(p,hard);self.assertEqual((len(p['flow']),len(p['reads']),len(p['stores']),p['native_peak']),(9,8,10,32))
        self.assertEqual(p['returned'][1:4],[310,0,15]);self.assertEqual(p['returned'][15],0x2000003f)
    def test_zero_word_is_required_even_when_idempotent(self):
        p=self.T.source_forecast(self.T.kernel());self.assertEqual(p['stores'][8]['before'],'00000000')
        raw=self.T.synthetic_raw(p,True);del raw['stores'][8]
        with self.assertRaises(ValueError):self.T.check_raw(raw,p,True)
    def test_preimages_and_volatile_POP_are_not_normalized(self):
        p=self.T.source_forecast(self.T.kernel());self.assertEqual(p['stores'][9]['before'],(0xa0030303).to_bytes(4,'little').hex())
        for key,value in(('before','a5a5a5a5'),('bytes',1)):
            raw=self.T.synthetic_raw(p,True);raw['stores'][9][key]=value
            with self.assertRaises(ValueError):self.T.check_raw(raw,p,True)
        raw=self.T.synthetic_raw(p,True);raw['returned'][3]=0xa0030303
        with self.assertRaises(ValueError):self.T.check_raw(raw,p,True)
    def test_OFF_needs_actual_counts_full16_pages_and_gate(self):
        p=self.T.source_forecast(self.T.kernel());raw=self.T.synthetic_raw(p,False);self.T.check_raw(raw,p,False)
        for field,value in(('stopped',False),('callback_count',9),('store_count',9),('flow',p['flow']),('stack_peak',24)):
            bad=copy.deepcopy(raw);bad[field]=value
            with self.assertRaises(ValueError):self.T.check_raw(bad,p,False)
        bad=copy.deepcopy(raw);bad['final_pages'][1]['hex']='00'+bad['final_pages'][1]['hex'][2:]
        with self.assertRaises(ValueError):self.T.check_raw(bad,p,False)


if __name__=='__main__':unittest.main()
