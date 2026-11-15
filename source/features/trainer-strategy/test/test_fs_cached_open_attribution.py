"""ROM-free CLI/observer controls; not a claimed native execution."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest


class AttributionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).parents[1]/'tools/attribuisci_fs_cached_open.py'
        spec=importlib.util.spec_from_file_location('cached_open_cli_test',path)
        cls.C=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.C);cls.path=path

    def command(self,mode='prepare',extra=()):
        argv=[sys.executable,'-B',str(self.path),'--mode',mode,'--out-dir',str(self.C.SOURCE/'must-not-create-private-fixtures')]
        for name in('rom','objects','recipe-dir','reference','input-contract'):argv+=['--'+name,'missing']
        return subprocess.run(argv+list(extra),capture_output=True,text=True,timeout=10)

    def test_output_guard_runs_before_private_inputs_are_read(self):
        run=self.command();self.assertEqual(run.returncode,2);self.assertIn('outside source',run.stderr)
        self.assertFalse((self.C.SOURCE/'must-not-create-private-fixtures').exists())

    def test_raw_dir_is_required_only_for_cpu_free_verification(self):
        for mode,extra in(('verify',()),('probe',('--raw-dir','ignored-must-fail'))):
            with self.subTest(mode=mode):
                run=self.command(mode,extra);self.assertEqual(run.returncode,2)
                self.assertIn('--raw-dir required only in verify mode',run.stderr)

    def test_cli_describes_verification_and_named_elf_input(self):
        run=subprocess.run([sys.executable,'-B',str(self.path),'--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)
        for arg in('prepare','probe','matrix','verify','--raw-dir','--objects','--input-contract'):
            self.assertIn(arg,run.stdout)

    def test_enforcement_policy_cannot_supply_predicted_memory_or_registers(self):
        predicted=dict(flow=[{'pc':0x1000,'regs':[99]*16}],reads=[dict(pc=0x1000,address=0x2000,bytes=2)],
            stores=[dict(pc=0x1004,address=0x3000,bytes=1,value=99,before='a5')],pages={123:b'not a producer input'},returned=[99]*16)
        policy=self.C.B.observation_policy(predicted)
        self.assertEqual(set(policy),{'code_starts','read_sites','write_sites'})
        self.assertEqual(policy['read_sites'],frozenset({(0x1000,0x2000,2)}))
        self.assertEqual(policy['write_sites'],frozenset({(0x1004,0x3000,1)}))

    def test_duplicate_observed_run_is_rejected_as_off_before_judging_state(self):
        raw={name:dict(observed=True)for name in('normal','normal_OFF','precompleted_prop','fat_size_equal')}
        with self.assertRaisesRegex(ValueError,'OFF observation binding'):self.C.controls(raw,{})

    def test_verification_requires_the_native_report_schema(self):
        report=dict(schema='unrelated-report-v99',mode='probe',CPU_executed=True,resources={},bindings={},
                    raw=[dict(name='normal',file='../escape.json',sha256='0'*64)])
        with tempfile.TemporaryDirectory()as d:
            path=Path(d);(path/'report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'native report schema'):self.C.verify_existing(path,{},{},{})

    def test_verification_rejects_nonlocal_raw_manifest_paths(self):
        report=dict(schema='native-fs-cached-open-report-v1',mode='matrix',CPU_executed=True,resources={},bindings={},raw=[
            dict(name=name,file='../escape.json',sha256='0'*64)for name in('normal','normal_OFF','precompleted_prop','fat_size_equal')])
        with tempfile.TemporaryDirectory()as d:
            path=Path(d);(path/'report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'local raw filename'):self.C.verify_existing(path,{},{},{})


if __name__=='__main__':unittest.main()
