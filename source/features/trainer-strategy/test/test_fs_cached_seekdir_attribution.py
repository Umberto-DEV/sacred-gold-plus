"""Falsifiers for native attribution verdicts, not a claimed CPU execution."""
from pathlib import Path
import copy
import subprocess
import sys
import unittest

from test_fs_cached_seekdir import load,fixture


class AttributionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.B=load(Path(__file__).with_name('fs_cached_seekdir_bench.py'),'cached_attribution_test_bench')

    def record(self,f):
        B=self.B;p=B.predict(f)
        return dict(initial=B.F.input_record(f),fault=None,stopped=True,stop_pc=p['stop_pc'],
            returned=p['returned'],models=[],runtime_host_writes=[],native_count=100,
            unique_native_starts=96,callback_count=101,read_count=35,store_count=27,native_peak=72,
            backend=dict(unicorn='2.1.4',CPU_model=17,scope='CortexA15 backend executing ARMv5 code; not ARM946 timing/cache/IRQ'),
            observed=True,flow=p['flow'],reads=p['reads'],stores=p['stores'],
            final_map_sha256=B.F.map_digest(p['pages']),
            final_pages=[dict(ram=a,hex=b.hex())for a,b in sorted(p['pages'].items())])

    def test_checker_rejects_deleted_writers_despite_unchanged_final_pages(self):
        B=self.B;f=fixture(B);record=self.record(f);B.require_run(f,record)
        for index in range(21,27):
            altered=copy.deepcopy(record);del altered['stores'][index]
            with self.subTest(index=index),self.assertRaisesRegex(ValueError,'source native stores'):
                B.require_run(f,altered)

    def test_camouflage_final_match_cannot_hide_four_preimages(self):
        B=self.B;f=fixture(B);normal=self.record(f)
        forged=self.record(fixture(B,precompleted=True));forged['initial']=normal['initial']
        self.assertEqual(normal['final_pages'],forged['final_pages'])
        with self.assertRaisesRegex(ValueError,'source native stores'):B.require_run(f,forged)
        altered=copy.deepcopy(normal);altered['returned'][14]=0x20d6ad0
        with self.assertRaisesRegex(ValueError,'returned ABI'):B.require_run(f,altered)

    def test_exact_site_width_and_readonly_resource_enforcement(self):
        B=self.B
        self.assertTrue(B.write_allowed(0x20d6c50,B.R.FILE+38,2))
        self.assertFalse(B.write_allowed(0x20d6c50,B.R.FILE+38,4))
        for pc in B.SELECTED:
            self.assertFalse(B.write_allowed(pc,B.R.FNT,4))
            self.assertFalse(B.write_allowed(pc,B.R.FAT,4))
        self.assertTrue(B.read_allowed(0x20d4b78,B.R.FNT+8,4,1))
        self.assertFalse(B.read_allowed(0x20d4b78,B.R.FNT+8,4,0))

    def test_duplicate_ON_is_not_an_OFF_measurement(self):
        B=self.B;A=load(Path(__file__).parents[1]/'tools/attribuisci_fs_cached_seekdir.py','cached_control_test_cli')
        inputs={'root':fixture(B),'root_precompleted':fixture(B,precompleted=True),'directory1':fixture(B,own_id=1)}
        records={name:self.record(f)for name,f in inputs.items()}
        records['root_OFF']=copy.deepcopy(records['root'])
        with self.assertRaisesRegex(ValueError,'OFF observation binding'):A.require_controls(records,inputs)

    def test_backend_metadata_is_qualified_separately(self):
        B=self.B;f=fixture(B);record=self.record(f)
        record['backend']['unicorn']='0.0.0'
        with self.assertRaisesRegex(ValueError,'backend identity'):B.require_run(f,record)

    def test_cli_rejects_public_raw_output_before_reading_inputs(self):
        cli=Path(__file__).parents[1]/'tools/attribuisci_fs_cached_seekdir.py'
        output=Path(__file__).parents[3]/'private-fixture-must-not-be-created'
        argv=[sys.executable,'-B',str(cli),'--mode','prepare','--out-dir',str(output)]
        for name in ('rom','recipe-dir','reference','input-contract'):argv+=['--'+name,'missing']
        run=subprocess.run(argv,capture_output=True,text=True,timeout=10)
        self.assertEqual(run.returncode,2)
        self.assertIn('outside source',run.stderr)
        self.assertFalse(output.exists())

    def test_cli_help_has_owned_input_modes_and_no_cpu_requirement(self):
        cli=Path(__file__).parents[1]/'tools/attribuisci_fs_cached_seekdir.py'
        run=subprocess.run([sys.executable,'-B',str(cli),'--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)
        for value in ('prepare','probe','matrix','--input-contract','--snapshot','--recipe-dir'):
            self.assertIn(value,run.stdout)


if __name__=='__main__':unittest.main()
