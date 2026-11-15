"""Parent completeness and private configuration are checked before heavy work."""
from pathlib import Path
import copy,importlib.util,json,os,struct,tempfile,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('next_attribution',Path(__file__).parents[1]/'tools/attribuisci_fs_next.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class Prepare(unittest.TestCase):
    def test_execution_modes_fail_before_any_parent_preparation(self):
        with patch.object(M,'prepare',side_effect=AssertionError('heavy preparation forbidden')):
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'),Path('unused'))
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'),Path('unused'),prepare_only=True,probe=True)

    def test_complete_native_parent_requires_full_counter_off_and_field_grid(self):
        r=dict(schema='native-release-wakeup-composed-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
            fixtures=[{}]*16,groups=[{}]*4,cases=[{}]*16,field_holdout=[{}]*64,observer_off=[{}]*4,counters=[{}]*4)
        M.require_complete_parent(r)
        for key,value in(('probe_only',True),('cpu_executed',False),('compiler_invoked',True),('cases',[{}]),('counters',[]),('observer_off',[]),('field_holdout',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.assertRaises(ValueError):M.require_complete_parent(bad)

    def test_valid_probe_parent_rejected_before_prior_model_preparation(self):
        with tempfile.TemporaryDirectory()as name:
            root=Path(name);report=root/'probe.json';report.write_text(json.dumps(dict(schema='native-release-wakeup-composed-v1',cpu_executed=True,compiler_invoked=False,probe_only=True)))
            c={k:'unused'for k in M.CONFIG_KEYS};c['report']=str(report);config=root/'config.json';config.write_text(json.dumps(c))
            with patch.object(M.H,'prepare',side_effect=AssertionError('heavy preparation forbidden')):
                with self.assertRaisesRegex(ValueError,'not a probe'):M.prepare(config,Path('unused'))

    def test_config_exact_keys_and_path_types(self):
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'config.json';valid={k:'private-relative-path'for k in M.CONFIG_KEYS}
            p.write_text(json.dumps(valid));self.assertEqual(set(M.read_config(p)),M.CONFIG_KEYS)
            for bad in({},dict(valid,unknown='x'),dict(valid,report=False)):
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):M.read_config(p)


class PrivateReplay(unittest.TestCase):
    def test_full_raw_replay_inactive_branch_and_wrong_postflag_without_guest(self):
        path=os.environ.get('SGP_FS_NEXT_REPLAY_CONFIG')
        if not path:self.skipTest('own exact ROMs, recipes, ancestors and Next raw report required')
        c=json.loads(Path(path).read_bytes());fixtures,bodies,proof,groups=M.prepare(Path(c['parent_config']),Path(c['recipe_dir']))
        contract=Path(c['field_contract']);cells=M.check_contract(contract,fixtures);r=M.read_report(Path(c['report']))
        self.assertIs(r['probe_only'],False);M.require_report(r,fixtures,bodies,proof,groups,contract,Path(c['raw_dir']))
        for key,value in(('probe_only',True),('cpu_executed',False),('compiler_invoked',True),('field_contract_sha256','0'*64),
                          ('cases',[]),('observer_off',[]),('counters',[]),('field_holdout',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.assertRaises(ValueError):M.require_report(bad,fixtures,bodies,proof,groups,contract,Path(c['raw_dir']))
        for g in groups:
            rows=r['cases'][g['ordinal']*4:g['ordinal']*4+4];normal=rows[0]['result'];counter=rows[3]['result']
            self.assertEqual(M.counter_rejection(counter,normal,bodies)['rejection'],'Next source-derived steps')
            for field in('flow','stores','reads','observed_pcs'):
                bad=copy.deepcopy(normal);bad[field]=[]
                with self.assertRaises(ValueError):M.B.require_result(bad,bodies)
            # A coherent wrong postimage still has NULL. It must fail the archive
            # state invariant, rather than passing on the return value or hash alone.
            bad=copy.deepcopy(normal);arc=bytearray.fromhex(bad['archive_after']);struct.pack_into('<I',arc,28,0x13);bad['archive_after']=arc.hex()
            image=bytearray(M.B.initial_memory(bad['fixture'],bodies,bad['fill']))
            image[M.B.FRAME-M.B.BASE:M.B.TOP-M.B.BASE]=bytes.fromhex(bad['frame_after']);image[M.B.ARC-M.B.BASE:M.B.ARC-M.B.BASE+92]=arc
            bad['whole_ram_sha256']=M.sha(bytes(image));self.assertEqual(bad['returned'][0],0)
            with self.assertRaisesRegex(ValueError,'Next source-derived archive_after'):M.B.require_result(bad,bodies)
            f=g['representative'];cell=next(x for x in cells if(x['language'],x['ordinal'])==(f['language'],f['ordinal']))
            with self.assertRaisesRegex(ValueError,'archive92'):M.field_contract(cell,f,bad)


if __name__=='__main__':unittest.main()
