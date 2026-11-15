"""Owned dispatcher source/ELF and raw counterexamples; no compiler or CPU."""
from pathlib import Path
import copy
import importlib.util
import struct
import unittest


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class DispatchBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.T=load(Path(__file__).parents[1]/'tools/compila_shellbell_dispatch.py','owned_dispatch_build_test')
    def test_exact_authored_source_and_code_pool_boundaries(self):
        t=self.T;self.assertEqual(t.sha(t.ASM.read_bytes()),t.ASM_SHA)
        symbols={name:t.BASE+value for name,value,_ in t.FUNCTIONS}
        profile=t.validate_text(t.own_text(),symbols);self.assertEqual((profile['bytes'],profile['driver_starts'],profile['frame_bytes']),(44,14,16))
        self.assertEqual(struct.unpack_from('<I',t.own_text(),28)[0],t.TABLE)
    def test_wrong_BLX_pool_branch_and_entry_state_are_rejected(self):
        t=self.T;symbols={name:t.BASE+value for name,value,_ in t.FUNCTIONS}
        for offset,word in((22,0x4718),(12,0xd004),(28,0x1234)):
            raw=bytearray(t.own_text());struct.pack_into('<H',raw,offset,word)
            with self.assertRaises(ValueError):t.validate_text(bytes(raw),symbols)
        symbols['shellbell_dispatch']-=1
        with self.assertRaises(ValueError):t.validate_text(t.own_text(),symbols)
    def test_truncated_or_foreign_ELF_is_refused_before_section_use(self):
        for data in(b'',b'\x7fELF'+bytes(48),bytes(52)):
            with self.assertRaises(ValueError):self.T.inspect_object(data)


class DispatchForecastTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.B=load(Path(__file__).with_name('shellbell_dispatch_bench.py'),'owned_dispatch_forecast_test')
    def test_full_source_prediction_and_independent_hard_ledger(self):
        p=self.B.forecast(self.B.kernel());self.assertEqual((len(p['flow']),len(p['reads']),len(p['stores']),p['native_peak']),(32,10,6,16))
        self.assertEqual([x['value']for x in p['stores'][-2:]],[29,39])
    def test_only_register_BLX_r3_and_odd_Thumb_target_are_admitted(self):
        b=self.B;k=b.kernel();regs=list(k[0]['entry_regs']);regs[3]=b.BUILD.BASE+32
        with self.assertRaises(ValueError):b.thumb_step(b.BUILD.BASE+22,bytes.fromhex('9847'),regs,{},[],[])
        with self.assertRaises(ValueError):b.validate_thumb(bytes.fromhex('9047'))
    def test_raw_with_same_endpoint_wrong_LR_or_missing_store_is_rejected(self):
        b=self.B;p=b.forecast(b.kernel());raw=b.synthetic_raw(p,True);b.check_raw(raw,p,True)
        altered=copy.deepcopy(raw);altered['flow'][12]['regs'][14]^=2
        with self.assertRaises(ValueError):b.check_raw(altered,p,True)
        altered=copy.deepcopy(raw);del altered['stores'][-1]
        with self.assertRaises(ValueError):b.check_raw(altered,p,True)
    def test_initial_schema_and_backend_cannot_be_forged(self):
        b=self.B;p=b.forecast(b.kernel());raw=b.synthetic_raw(p,True)
        for key,value in(('initial',{}),('schema','different'),('backend',{})):
            altered=copy.deepcopy(raw);altered[key]=value
            with self.assertRaises(ValueError):b.check_raw(altered,p,True)

    def test_OFF_still_requires_full_return_and_all_pages(self):
        b=self.B;p=b.forecast(b.kernel());raw=b.synthetic_raw(p,False);b.check_raw(raw,p,False)
        for field,value in(('callback_count',32),('flow',p['flow']),('stack_peak',12)):
            altered=copy.deepcopy(raw);altered[field]=value
            with self.assertRaises(ValueError):b.check_raw(altered,p,False)
        altered=copy.deepcopy(raw);altered['final_pages'][0]['hex']='00'+altered['final_pages'][0]['hex'][2:]
        with self.assertRaises(ValueError):b.check_raw(altered,p,False)

    def test_boolean_aliases_and_missing_none_fields_are_not_valid_raw(self):
        b=self.B;p=b.forecast(b.kernel());raw=b.synthetic_raw(p,True)
        for key,value in(('ARM_count',False),('observed',1)):
            altered=copy.deepcopy(raw);altered[key]=value
            with self.assertRaises(ValueError):b.check_raw(altered,p,True)
        altered=copy.deepcopy(raw);del altered['fault']
        with self.assertRaises(ValueError):b.check_raw(altered,p,True)

    def test_receipt_comparison_preserves_recursive_scalar_and_key_types(self):
        equal=self.B.BUILD.exact
        self.assertFalse(equal({'CPU_executed':False},{'CPU_executed':0}))
        self.assertFalse(equal({'calls':[1]},{'calls':[True]}))
        self.assertFalse(equal({1:'owned'},{True:'owned'}))
        self.assertTrue(equal({'a':[1,False,None]},{'a':[1,False,None]}))


if __name__=='__main__':unittest.main()
