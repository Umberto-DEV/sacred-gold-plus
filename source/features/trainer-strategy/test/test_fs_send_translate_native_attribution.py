"""CLI gates and optional actual raw replay without a new guest."""
from pathlib import Path
import copy,importlib.util,json,os,sys,tempfile,unittest
from unittest.mock import patch

path=Path(__file__).parents[1]/'tools/attribuisci_fs_send_translate_native.py'
s=importlib.util.spec_from_file_location('send_translate_cli_tests',path)
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class Gates(unittest.TestCase):
    def test_invalid_modes_precede_heavy_preparation(self):
        with patch.object(M,'prepare',side_effect=AssertionError('no heavy preparation')):
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'))
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'),prepare_only=True,probe=True)

    def test_nested_output_is_rejected_before_preparation(self):
        with tempfile.TemporaryDirectory()as name:
            raw=Path(name)/'raw'
            args=['tool','--parent-config','unused','--field-contract','unused','--raw-dir',str(raw),'--json',str(raw/'report.json')]
            with patch.object(sys,'argv',args),patch.object(M,'analyze',side_effect=AssertionError('no preparation')):
                with self.assertRaises(SystemExit)as error:M.main()
                self.assertEqual(error.exception.code,2)

    def test_strict_parent_and_configuration(self):
        r=dict(schema='native-fs-translate-isolated-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
            groups=[{}]*4,fixtures=[{}]*16,cases=[{}]*12,observer_off=[{}]*4,field_holdout=[{}]*48,counters=[{}]*4)
        M.require_complete_parent(r)
        for key,value in(('probe_only',True),('compiler_invoked',True),('cases',[]),('counters',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.assertRaises(ValueError):M.require_complete_parent(bad)
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'replay.json';valid={k:'relative-private-path'for k in M.CONFIG_KEYS}
            p.write_text(json.dumps(valid));self.assertEqual(set(M.read_config(p)),M.CONFIG_KEYS)
            for bad in({},dict(valid,extra='x'),dict(valid,parent_config=False)):
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):M.read_config(p)

    def test_grouping_uses_literal_input_and_default_policy_under_hash_collision(self):
        fs=[dict(language='EN',ordinal=i,entry=[0]*16,translated_result=v)for i,v in enumerate((0,1,0,0,0))];fs[4]['entry'][0]=1
        with patch.object(M.B,'initial_memory',side_effect=[b'a',b'a',b'b',b'a',b'a']),patch.object(M,'sha',return_value='collision'):
            groups=M.share_groups(fs,{})
        self.assertEqual(len(groups),4);self.assertEqual(groups[0]['members'],[dict(language='EN',ordinal=0),dict(language='EN',ordinal=3)])


class PrivateReplay(unittest.TestCase):
    def test_exact_actual_raw_and_frozen_boundaries_reject_forgeries(self):
        value=os.environ.get('SGP_FS_SEND_TRANSLATE_REPLAY_CONFIG')
        if not value:self.skipTest('own exact inputs, recovered object/reference and combined raw required')
        c=M.read_config(Path(value));fs,bs,proof,groups,sp,tp=M.prepare(c['parent_config'])
        M.check_contract(c['field_contract'],fs,sp,tp,bs);r=M.read_report(c['report']);self.assertIs(r['probe_only'],False)
        with patch.object(M.B,'run',side_effect=AssertionError('replay cannot execute CPU')):
            M.require_report(r,fs,bs,proof,groups,c['field_contract'],c['raw_dir'])
        for g in groups:
            row=next(x['result']for x in r['cases']if x['group']==g['ordinal']and x['label']=='normal')
            for phase in('translate_entry','translate_return'):
                bad=copy.deepcopy(row);bad['checkpoints'][phase]['whole_ram_sha256']='0'*64
                with self.assertRaisesRegex(ValueError,'source-derived checkpoints'):M.B.require_result(bad,bs)
            bad=copy.deepcopy(row);bad['stores'][26]['before']='a5'*4
            with self.assertRaisesRegex(ValueError,'source-derived stores'):M.B.require_result(bad,bs)
            bad=copy.deepcopy(row);bad['stores'][25]['before']=row['fixture']['translated_result'].to_bytes(4,'little').hex()
            with self.assertRaisesRegex(ValueError,'source-derived stores'):M.B.require_result(bad,bs)


if __name__=='__main__':unittest.main()
