"""Owned cache/semantic/CLI admission checks; no ROM, compiler or CPU."""
from pathlib import Path
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest


p=Path(__file__).parents[1]/'tools/attribuisci_reset_c.py';s=importlib.util.spec_from_file_location('Reset_C_CLI_test',p)
T=importlib.util.module_from_spec(s);s.loader.exec_module(T)


class ResetCCLITest(unittest.TestCase):
    def test_completed_owned_frame_cache_binds_actual_two_cells_and_sources(self):
        proof=T.frame_qualification(T.CACHE);self.assertEqual((proof['CPU_runs'],proof['owned_instructions']),(2,18))
        cache=json.loads(T.CACHE.read_bytes());self.assertFalse(cache['ROM_loaded'])
        self.assertEqual([x['observed']for x in cache['cases']],[True,False]);self.assertEqual(cache['source_sha256'],T.Q.source_ids())
    def test_qualification_bool_alias_or_source_edit_is_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'q.json';q=json.loads(T.CACHE.read_bytes());q['ROM_loaded']=0;p.write_text(json.dumps(q))
            with self.assertRaises(ValueError):T.frame_qualification(p)
            q=json.loads(T.CACHE.read_bytes());q['source_sha256'][next(iter(q['source_sha256']))]='0'*64;p.write_text(json.dumps(q))
            with self.assertRaises(ValueError):T.frame_qualification(p)
    def test_semantic_comparison_checks_both_profiles_and_typed_metadata(self):
        before={k:dict(input_Up=v,Mon_boundaries=[dict(checksum=680)],native_calls=['Box','Mon62','Max0','Mon58'])for k,v in(('Up3',3),('Up0',0))}
        T.E.require_equal(T.need,T.B.wire,before,copy.deepcopy(before))
        for profile in('Up3','Up0'):
            after=copy.deepcopy(before);after[profile]['Mon_boundaries'][0]['checksum']^=1
            with self.assertRaises(ValueError):T.E.require_equal(T.need,T.B.wire,before,after)
        after=copy.deepcopy(before);after['Up0']['input_Up']=False
        with self.assertRaises(ValueError):T.E.require_equal(T.need,T.B.wire,before,after)
        with self.assertRaises(ValueError):T.E.require_equal(T.need,T.B.wire,before,{'Up3':before['Up3']})
    def test_retained_native_report_controls_cannot_be_missing_or_modified(self):
        checks=dict(OFF_pairs=1,forgeries=[dict(name='owned',reason='rejected')])
        T.require_native_controls(dict(controls=copy.deepcopy(checks)),checks)
        for report in({},dict(controls={}),dict(controls=dict(OFF_pairs=True,forgeries=checks['forgeries']))):
            with self.assertRaises(ValueError):T.require_native_controls(report,checks)
    def test_verify_requires_raw_directory_before_reading_inputs(self):
        with tempfile.TemporaryDirectory()as d:
            args=[sys.executable,'-B',str(p),'--mode','verify']
            for flag in('rom','reference','heartgold-ref','build-dir','objects','recipe-dir','div-recipe','input-contract','qualification','native-input-contract','native-raw-dir'):
                args+=['--'+flag,'MISSING']
            args+=['--out-dir',str(Path(d)/'fresh')];r=subprocess.run(args,capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,2);self.assertIn('C raw-dir only and required',r.stderr)
    def test_unknown_mode_is_rejected_without_a_producer(self):
        r=subprocess.run([sys.executable,'-B',str(p),'--mode','resume'],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,2);self.assertIn('invalid choice',r.stderr)
    def test_runtime_binding_includes_recipe_ELF_fixture_math_projection_and_producer(self):
        names=T.source_identities()
        for name in('tools/compila_reset_c.py','tools/rileggi_reset_c.py','tools/congela_reset_c.py','test/reset_c_bench.py','test/reset_c_equivalence.py','test/mon_reset_cpu.py'):
            self.assertIn('features/trainer-strategy/'+name,names)


if __name__=='__main__':unittest.main()
