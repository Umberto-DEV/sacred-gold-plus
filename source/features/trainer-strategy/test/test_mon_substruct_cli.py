"""Regression: CPU-free verifier must require a completed, typed matrix receipt."""
import sys
from pathlib import Path
import copy
import importlib.util
import unittest
import subprocess
import json
import tempfile

p=Path(__file__).parents[1]/'tools/attribuisci_mon_substruct.py'
s=importlib.util.spec_from_file_location('substruct_receipt_test',p);D=importlib.util.module_from_spec(s);s.loader.exec_module(D)


class SubstructReceiptTest(unittest.TestCase):
    def receipt(self):
        records=[dict(name='owned',file='owned.json',sha256='0'*64)]
        bindings=dict(compiler_invoked=False);checks=dict(OFF_pairs=1)
        report=dict(schema='native-mon-substructure-report-v1',mode='matrix',CPU_executed=True,
            verdict='PASS within full32x4 selectors/one ignored-PID alias/native GetSubstruct scope',raw=records,bindings=bindings,controls=checks)
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


class OwnedQualificationReceiptTest(unittest.TestCase):
    def fixture(self):
        return json.loads(Path(__file__).with_name('substruct-instruction-qualification.json').read_bytes())

    def verify_copy(self,value):
        with tempfile.TemporaryDirectory()as directory:
            path=Path(directory)/'owned-instruction-receipt.json';path.write_text(json.dumps(value))
            return D.verify_qualification(path)

    def test_actual_owned_fixture_is_verified_without_cpu(self):
        code = r"""
import importlib.abc, importlib.util, sys
from pathlib import Path
assert not any(k.split('.')[0] in ('unicorn', 'keystone') for k in sys.modules)
class BlockBackend(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('unicorn', 'keystone'):
            raise ImportError('backend blocked: ' + fullname)
sys.meta_path.insert(0, BlockBackend())
try:
    __import__('unicorn')
except ImportError as error:
    assert 'backend blocked' in str(error)
else:
    raise AssertionError('backend blocker did not reject import')
sys.path.insert(0, sys.argv[3])
spec = importlib.util.spec_from_file_location('owned_receipt_verifier', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.verify_qualification(Path(sys.argv[2]))
assert result is not None
assert not any(k.split('.')[0] in ('unicorn', 'keystone') for k in sys.modules)
"""
        child = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code, str(p),
                                str(Path(__file__).with_name('substruct-instruction-qualification.json')), str(Path(__file__).parents[3])],
                               text=True, capture_output=True, timeout=30)
        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)

    def test_wrong_returned_word_with_correct_shape_and_metadata_is_rejected(self):
        report=self.fixture();report['cases'][0]['returned'][0]=17
        with self.assertRaisesRegex(ValueError,'expected full16'):self.verify_copy(report)

    def test_wrong_valid_hex_flow_digest_is_rejected(self):
        report=self.fixture();report['cases'][0]['flow_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'two-step full16 flow digest'):self.verify_copy(report)

    def test_source_identity_and_metadata_types_are_bound(self):
        report=self.fixture();report['source_sha256'][next(iter(report['source_sha256']))]='0'*64
        with self.assertRaisesRegex(ValueError,'source drift'):self.verify_copy(report)
        report=self.fixture();report['cases'][0]['all_pages']=1
        with self.assertRaisesRegex(ValueError,'completed owned instruction checks'):self.verify_copy(report)


if __name__=='__main__':unittest.main()
