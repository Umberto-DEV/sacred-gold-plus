"""CLI admission and cached qualification checks, no ROM/CPU/compiler."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest

p=Path(__file__).parents[1]/'tools/attribuisci_mon_ppup_setter.py';s=importlib.util.spec_from_file_location('Mon_CLI_tests',p)
T=importlib.util.module_from_spec(s);s.loader.exec_module(T)


class MonCLITest(unittest.TestCase):
    def test_qualification_rejects_false_true_alias(self):
        with tempfile.TemporaryDirectory()as d:
            path=Path(d)/'q.json';expected=T.Q.expected_receipt();path.write_text(json.dumps(expected))
            self.assertEqual(T.verify_qualification(path)['cases'],4)
            expected['ROM_loaded']=0;path.write_text(json.dumps(expected))
            with self.assertRaises(ValueError):T.verify_qualification(path)
    def test_OFF_qualification_does_not_claim_native_trace(self):
        r=T.Q.expected_receipt()['cases'][-1]
        self.assertIs(r['native_full16_every_pc'],False);self.assertIsNone(r['native_projection_sha256'])
        self.assertIs(r['source_full16_every_pc'],True)
    def test_verify_requires_raw_directory_before_ROM_access(self):
        with tempfile.TemporaryDirectory()as d:
            args=[sys.executable,'-B',str(p),'--mode','verify','--rom','MISSING','--reference','MISSING','--input-contract','MISSING','--qualification','MISSING','--out-dir',str(Path(d)/'fresh')]
            r=subprocess.run(args,capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,2);self.assertIn('raw-dir only and required',r.stderr)
    def test_unknown_mode_rejected(self):
        r=subprocess.run([sys.executable,'-B',str(p),'--mode','observe'],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,2);self.assertIn('invalid choice',r.stderr)


if __name__=='__main__':unittest.main()
