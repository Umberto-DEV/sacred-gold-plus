"""Completed owned-cache and CLI admission tests, no ROM or CPU."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

p=Path(__file__).parents[1]/'tools/attribuisci_mon_reset.py';s=importlib.util.spec_from_file_location('Reset_CLI_tests',p)
T=importlib.util.module_from_spec(s);s.loader.exec_module(T)


class MonResetCLITest(unittest.TestCase):
    def test_actual_completed_cache_authenticates_all_six_cells(self):
        proof=T.verify_qualification(T.CACHE);self.assertEqual(proof['cases'],6)
        cache=json.loads(T.CACHE.read_bytes())
        self.assertEqual([x['instructions']for x in cache['cases']],[40001,40001,5,65535,65536,65536])
        self.assertIs(cache['ROM_loaded'],False);self.assertEqual(cache['unchanged_ARM_cap'],8192)
    def test_bool_alias_and_changed_source_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            path=Path(d)/'q.json';cache=json.loads(T.CACHE.read_bytes());cache['ROM_loaded']=0;path.write_text(json.dumps(cache))
            with self.assertRaises(ValueError):T.verify_qualification(path)
            cache=json.loads(T.CACHE.read_bytes());first=next(iter(cache['source_sha256']));cache['source_sha256'][first]='0'*64;path.write_text(json.dumps(cache))
            with self.assertRaises(ValueError):T.verify_qualification(path)
    def test_verify_requires_raw_directory_before_opening_missing_inputs(self):
        with tempfile.TemporaryDirectory()as d:
            args=[sys.executable,'-B',str(p),'--mode','verify']
            for flag in('rom','reference','objects','recipe-dir','div-recipe','input-contract','qualification'):args+=['--'+flag,'MISSING']
            args+=['--out-dir',str(Path(d)/'fresh')]
            r=subprocess.run(args,capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,2);self.assertIn('raw-dir only and required',r.stderr)
    def test_unknown_mode_rejected_before_any_producer(self):
        r=subprocess.run([sys.executable,'-B',str(p),'--mode','resume'],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,2);self.assertIn('invalid choice',r.stderr)


if __name__=='__main__':unittest.main()
