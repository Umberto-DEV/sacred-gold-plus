"""Owned qualification and completed raw report must be exact, without CPU."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
import subprocess

p=Path(__file__).parents[1]/'tools/attribuisci_box_ppup.py'
s=importlib.util.spec_from_file_location('box_receipt_contracts',p);D=importlib.util.module_from_spec(s);s.loader.exec_module(D)


class BoxReceiptTest(unittest.TestCase):
    def fixture(self):return json.loads(Path(__file__).with_name('box-instruction-qualification.json').read_bytes())

    def verify(self,data):
        with tempfile.TemporaryDirectory()as directory:
            p=Path(directory)/'owned.json';p.write_text(json.dumps(data));return D.verify_qualification(p)

    def test_actual_owned_receipt_is_verified_without_CPU_or_assembler(self):
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
assert result['cases'] == 7
assert not any(k.split('.')[0] in ('unicorn', 'keystone') for k in sys.modules)
"""
        child = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code, str(p),
                                str(Path(__file__).with_name('box-instruction-qualification.json')), str(Path(__file__).parents[3])],
                               text=True, capture_output=True, timeout=30)
        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)

    def test_return_flow_and_metadata_forgeries_rejected(self):
        edits=(lambda x:x['cases'][0]['returned'].__setitem__(0,17),
               lambda x:x['cases'][0].__setitem__('flow_sha256','0'*64),
               lambda x:x['cases'][0].__setitem__('all_pages',1),
               lambda x:x.__setitem__('CPU_model',True),lambda x:x['cases'].pop(),
               lambda x:x['source_sha256'].__setitem__(next(iter(x['source_sha256'])),'0'*64))
        for edit in edits:
            data=self.fixture();edit(data)
            with self.assertRaisesRegex(ValueError,'exact completed owned'):self.verify(data)

    def receipt(self):
        records=[dict(name='owned',file='owned.json',sha256='0'*64)];bindings=dict(compiler_invoked=False);checks=dict(OFF_pairs=1)
        return dict(schema='native-box-ppup-report-v1',mode='matrix',CPU_executed=True,
            verdict='PASS within encrypted Box136/attribute62/flags0/checksum02AB/PID4000 scope',raw=records,bindings=bindings,controls=checks),records,bindings,checks

    def test_completed_original_matrix_is_required(self):
        report,*args=self.receipt();D.require_completed_report(report,*args)
        for key,value in(('mode','prepare'),('CPU_executed',1),('CPU_executed',False),('verdict','PASS')):
            with self.assertRaisesRegex(ValueError,'completed original'):D.require_completed_report({**report,key:value},*args)

    def test_raw_hashes_and_exact_types_bound(self):
        report,*args=self.receipt();forged=copy.deepcopy(report);forged['raw'][0]['sha256']='1'*64
        with self.assertRaisesRegex(ValueError,'raw hashes'):D.require_completed_report(forged,*args)
        with self.assertRaisesRegex(ValueError,'raw hashes'):D.require_completed_report({**report,'controls':dict(OFF_pairs=True)},*args)


if __name__=='__main__':unittest.main()
