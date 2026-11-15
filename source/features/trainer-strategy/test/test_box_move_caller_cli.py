"""Owned cached qualification and completed-report guards; no ROM/CPU."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
import subprocess

p=Path(__file__).parents[1]/'tools/attribuisci_box_move_caller.py'
s=importlib.util.spec_from_file_location('caller_receipt_contracts',p);D=importlib.util.module_from_spec(s);s.loader.exec_module(D)


class CallerReceiptTest(unittest.TestCase):
 def fixture(self):return json.loads(Path(__file__).with_name('box-caller-limit-qualification.json').read_bytes())
 def verify(self,data):
  with tempfile.TemporaryDirectory()as directory:
   p=Path(directory)/'owned.json';p.write_text(json.dumps(data));return D.verify_qualification(p)
 def test_qualified_own_receipt_no_CPU_import(self):
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
assert result['cases'] == 6
assert not any(k.split('.')[0] in ('unicorn', 'keystone') for k in sys.modules)
"""
  child = subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code, str(p),
                          str(Path(__file__).with_name('box-caller-limit-qualification.json')), str(Path(__file__).parents[3])],
                         text=True, capture_output=True, timeout=30)
  self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
 def test_false_boundary_typed_flow_source_or_map_rejected(self):
  edits=(lambda x:x['cases'][4].__setitem__('stopped',True),lambda x:x['cases'][0].__setitem__('flow_sha256','0'*64),
   lambda x:x['cases'][0].__setitem__('final_map_sha256','0'*64),lambda x:x['cases'][0].__setitem__('all_pages',1),
   lambda x:x['cases'][0]['returned'].__setitem__(0,1),lambda x:x['source_sha256'].__setitem__(next(iter(x['source_sha256'])),'0'*64))
  for edit in edits:
   d=self.fixture();edit(d)
   with self.assertRaisesRegex(ValueError,'exact completed owned caller'):self.verify(d)
 def receipt(self):
  records=[dict(name='Up3',file='Up3.json',sha256='0'*64)];bindings=dict(compiler_invoked=False);controls=dict(OFF_pairs=1)
  return dict(schema=D.REPORT_SCHEMA,mode='matrix',CPU_executed=True,verdict=D.VERDICT,raw=records,bindings=bindings,controls=controls),records,bindings,controls
 def test_only_completed_matrix_receipt(self):
  r,*args=self.receipt();D.require_completed_report(r,*args)
  for k,v in(('mode','verify'),('CPU_executed',1),('CPU_executed',False),('verdict','PASS')):
   with self.assertRaisesRegex(ValueError,'completed original caller'):D.require_completed_report({**r,k:v},*args)
 def test_completed_hashes_controls_types_bound(self):
  r,*args=self.receipt();bad=copy.deepcopy(r);bad['raw'][0]['sha256']='1'*64
  with self.assertRaisesRegex(ValueError,'caller original raw hashes'):D.require_completed_report(bad,*args)
  with self.assertRaisesRegex(ValueError,'caller original raw hashes'):D.require_completed_report({**r,'controls':dict(OFF_pairs=True)},*args)


if __name__=='__main__':unittest.main()
