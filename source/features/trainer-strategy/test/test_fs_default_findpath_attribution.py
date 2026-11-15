"""CLI gates and private raw replay, never a second prefix guest."""
from pathlib import Path
import copy,importlib.util,json,os,sys,tempfile,unittest
from unittest.mock import patch

path=Path(__file__).parents[1]/'tools/attribuisci_fs_default_findpath.py'
s=importlib.util.spec_from_file_location('default_findpath_cli_test',path)
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class Gates(unittest.TestCase):
    def test_mode_gates_precede_heavy_preparation(self):
        with patch.object(M,'prepare',side_effect=AssertionError('no heavy preparation')):
            with self.assertRaises(ValueError):M.analyze(*([Path('unused')]*5))
            with self.assertRaises(ValueError):M.analyze(*([Path('unused')]*5),prepare_only=True,probe=True)

    def test_nested_report_rejected_before_export_or_preparation(self):
        with tempfile.TemporaryDirectory()as name:
            raw=Path(name)/'raw'
            for mode in([],['--export-components']):
                args=['tool','--parent-config','unused','--raw-dir',str(raw),'--json',str(raw/'report.json')]+mode
                with patch.object(sys,'argv',args),patch.object(M,'read_components',side_effect=AssertionError('no readback')),patch.object(M,'analyze',side_effect=AssertionError('no prepare')):
                    with self.assertRaises(SystemExit)as error:M.main()
                    self.assertEqual(error.exception.code,2)

    def test_strict_config_and_complete_parent(self):
        r=dict(schema='native-fs-send-translate-native-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
            fixtures=[{}]*16,groups=[{}]*4,cases=[{}]*12,field_holdout=[{}]*48,observer_off=[{}]*4,counters=[{}]*4)
        M.require_complete_parent(r)
        for key,value in(('probe_only',True),('compiler_invoked',True),('cases',[]),('counters',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.assertRaises(ValueError):M.require_complete_parent(bad)
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'replay.json';good={k:'relative-private-path'for k in M.CONFIG_KEYS}
            p.write_text(json.dumps(good));self.assertEqual(set(M.read_config(p)),M.CONFIG_KEYS)
            for bad in({},dict(good,extra='x'),dict(good,reference=False)):
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):M.read_config(p)

    def test_literal_grouping_ignores_removed_default_result_policy_under_hash_collision(self):
        fs=[dict(language='EN',ordinal=i,entry=[0]*16,parent_send_fixture=dict(translated_result=v))for i,v in enumerate((0,1,0,0,0))]
        fs[4]['entry'][0]=1
        with patch.object(M.B,'initial_memory',side_effect=[b'a',b'a',b'b',b'a',b'a']),patch.object(M,'sha',return_value='collision'):
            groups=M.share_groups(fs,{})
        self.assertEqual(len(groups),3);self.assertEqual(groups[0]['members'],[dict(language='EN',ordinal=i)for i in(0,1,3)])
        self.assertTrue(all(g['models']==0 for g in groups))


class PrivateReplay(unittest.TestCase):
    def test_exact_raw_and_full_oracle_reject_writer_fill_and_abi_forgeries(self):
        value=os.environ.get('SGP_FS_DEFAULT_FINDPATH_REPLAY_CONFIG')
        if not value:self.skipTest('own exact inputs, prefix object/reference and new raw required')
        c=M.read_config(Path(value));fs,bs,proof,groups,parent=M.prepare(c['parent_config'],c['recipe_dir'],c['reference'],c['component_receipt'])
        M.check_contract(c['field_contract'],fs,parent);r=M.read_report(c['report']);self.assertIs(r['probe_only'],False)
        with patch.object(M.B,'run',side_effect=AssertionError('raw replay must not execute CPU')):
            M.require_report(r,fs,bs,proof,groups,c['field_contract'],c['raw_dir'])
        for group in groups:
            row=next(x['result']for x in r['cases']if x['group']==group['ordinal']and x['label']=='normal')
            for index in(0,1,5,6,9,13,14,15):
                bad=copy.deepcopy(row);bad['returned'][index]^=1;bad['halt_regs']=bad['returned']
                with self.assertRaisesRegex(ValueError,'source-derived returned'):M.B.require_result(bad,bs)
            bad=copy.deepcopy(row);bad['stores'][0]['before']=bad['stores'][0]['value'].to_bytes(4,'little').hex()
            with self.assertRaisesRegex(ValueError,'source-derived stores'):M.B.require_result(bad,bs)
            bad=copy.deepcopy(row);raw=bytearray.fromhex(bad['frame_after']);raw[0]^=1;bad['frame_after']=raw.hex()
            with self.assertRaisesRegex(ValueError,'source-derived frame_after'):M.B.require_result(bad,bs)
            f=copy.deepcopy(row['fixture']);raw=bytearray.fromhex(f['frame']);raw[0]^=1;f['frame']=raw.hex()
            with self.assertRaisesRegex(ValueError,'forward-derived whole checkpoint'):M.B.initial_memory(f,bs)


if __name__=='__main__':unittest.main()
