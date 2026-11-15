"""Regression: CPU-free verifier must require a completed, typed matrix receipt."""
from pathlib import Path
import copy
import importlib.util
import unittest

p=Path(__file__).parents[1]/'tools/attribuisci_mon_checksum.py'
s=importlib.util.spec_from_file_location('checksum_receipt_test',p);D=importlib.util.module_from_spec(s);s.loader.exec_module(D)


class ChecksumReceiptTest(unittest.TestCase):
    def receipt(self):
        records=[dict(name='owned',file='owned.json',sha256='0'*64)]
        bindings=dict(compiler_invoked=False);checks=dict(OFF_pairs=1)
        report=dict(schema='native-mon-checksum-report-v1',mode='matrix',CPU_executed=True,
            verdict='PASS within owned129byte/four size-data profiles/native checksum scope',raw=records,bindings=bindings,controls=checks)
        return report,records,bindings,checks

    def test_completed_original_receipt_is_required(self):
        report,*expected=self.receipt();D.require_completed_report(report,*expected)
        for key,value in (('schema','wrong'),('mode','prepare'),('CPU_executed',False),('CPU_executed',1),('verdict','PASS')):
            with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'completed original'):
                D.require_completed_report({**report,key:value},*expected)

    def test_exact_json_types_required_for_binding_and_controls(self):
        report,*expected=self.receipt()
        for key,value in (('bindings',dict(compiler_invoked=0)),('controls',dict(OFF_pairs=True))):
            with self.assertRaisesRegex(ValueError,'raw hashes/bindings/controls'):
                D.require_completed_report({**report,key:value},*expected)

    def test_raw_hash_and_name_are_bound_to_original_file(self):
        report,*expected=self.receipt();forged=copy.deepcopy(report);forged['raw'][0]['sha256']='1'*64
        with self.assertRaisesRegex(ValueError,'raw hashes/bindings/controls'):D.require_completed_report(forged,*expected)


if __name__=='__main__':unittest.main()
