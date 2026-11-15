"""Composition requires a complete earlier campaign, not its valid probe."""
from pathlib import Path
import copy,importlib.util,json,os,tempfile,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('release_wakeup_cli',Path(__file__).parents[1]/'tools/attribuisci_release_wakeup.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class Preparation(unittest.TestCase):
    def test_probe_parent_rejected_before_heavy_prepare(self):
        with tempfile.TemporaryDirectory()as d:
            root=Path(d);report=root/'probe.json';report.write_text(json.dumps(dict(schema='native-os-wakeup-isolated-v1',
                cpu_executed=True,compiler_invoked=False,probe_only=True)))
            c={k:'unused'for k in M.CONFIG_KEYS};c['report']=str(report);config=root/'config.json';config.write_text(json.dumps(c))
            with patch.object(M.J,'prepare',side_effect=AssertionError('heavy prepare forbidden')):
                with self.assertRaisesRegex(ValueError,'not a probe'):M.prepare(config)

    def test_execution_modes_rejected_before_preparation(self):
        with patch.object(M,'prepare',side_effect=AssertionError('heavy prepare forbidden')):
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'))
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'),prepare_only=True,probe=True)

    def test_complete_parent_gate_rejects_probe_and_partial_grid(self):
        full=dict(schema='native-os-wakeup-isolated-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
            groups=[{}]*4,cases=[{}]*12,fixtures=[{}]*16,field_holdout=[{}]*48,observer_off=[{}]*4)
        # Metadata gate only: full source/raw authentication is a separate obligation.
        M.require_complete_wakeup(full)
        for key,value in(('probe_only',True),('cpu_executed',False),('compiler_invoked',True),
                          ('cases',[{}]),('field_holdout',[]),('observer_off',[])):
            bad=copy.deepcopy(full);bad[key]=value
            with self.assertRaises(ValueError):M.require_complete_wakeup(bad)

    def test_replay_config_requires_exact_string_paths(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'config.json';valid={k:'relative-own-path'for k in M.CONFIG_KEYS};p.write_text(json.dumps(valid))
            self.assertEqual(set(M.read_config(p)),M.CONFIG_KEYS)
            for bad in({},dict(valid,unknown='x'),dict(valid,report=True)):
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):M.read_config(p)


class PrivateReplay(unittest.TestCase):
    def test_complete_raw_and_independent_contract_replayed_without_guest(self):
        path=os.environ.get('SGP_RELEASE_WAKEUP_REPLAY_CONFIG')
        if not path:self.skipTest('own exact ROMs, qualified ancestors and composed raw report required')
        c=json.loads(Path(path).read_bytes());fixtures,bodies,proof,groups,baselines=M.prepare(Path(c['parent_config']))
        contract=Path(c['field_contract']);M.check_contract(contract,fixtures,baselines);r=M.read_report(Path(c['report']))
        self.assertIs(r['probe_only'],False)
        M.require_report(r,fixtures,bodies,proof,groups,contract,Path(c['raw_dir']))
        for key,value in(('probe_only',True),('cpu_executed',False),('compiler_invoked',True),('field_contract_sha256','0'*64),
                          ('cases',[]),('observer_off',[]),('counters',[]),('field_holdout',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.assertRaises(ValueError):M.require_report(bad,fixtures,bodies,proof,groups,contract,Path(c['raw_dir']))
        for g in groups:
            rows=r['cases'][g['ordinal']*4:g['ordinal']*4+4];normal=rows[0]['result'];counter=rows[3]['result']
            proof=M.counter_rejection(counter,normal,bodies)
            self.assertEqual(proof['rejection'],'Composition source-derived steps')
            for field in('flow','stores','reads','observed_pcs'):
                bad=copy.deepcopy(normal);bad[field]=[]
                with self.assertRaises(ValueError):M.B.require_result(bad,bodies)
        original=json.loads(contract.read_bytes())
        with tempfile.TemporaryDirectory()as d:
            bad=copy.deepcopy(original);bad['cells'][0]['native_stack24_words'][3]=False
            path=Path(d)/'contract.json';path.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):M.check_contract(path,fixtures,baselines)


if __name__=='__main__':unittest.main()
