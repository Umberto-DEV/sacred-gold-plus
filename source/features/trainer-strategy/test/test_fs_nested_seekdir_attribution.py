"""CLI admission and optional actual replay; input rejection is not masked."""
from pathlib import Path
import copy,importlib.util,json,os,sys,tempfile,unittest
from unittest.mock import patch

path=Path(__file__).parents[1]/'tools/attribuisci_fs_nested_seekdir.py'
s=importlib.util.spec_from_file_location('nested_seekdir_cli_test',path)
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class Gates(unittest.TestCase):
    def test_invalid_modes_precede_heavy_preparation(self):
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

    def test_config_and_parent_are_exact(self):
        r=dict(schema='native-fs-default-findpath-prefix-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
            fixtures=[{}]*16,groups=[{}]*2,cases=[{}]*7,field_holdout=[{}]*56,observer_off=[{}]*2,counters=[{}]*2,lower_fill_controls=[{}])
        M.require_complete_parent(r)
        for key,value in(('probe_only',True),('compiler_invoked',True),('cases',[]),('lower_fill_controls',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.assertRaises(ValueError):M.require_complete_parent(bad)
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'replay.json';good={k:'relative-private-path'for k in M.CONFIG_KEYS}
            p.write_text(json.dumps(good));self.assertEqual(set(M.read_config(p)),M.CONFIG_KEYS)
            for bad in({},dict(good,extra='x'),dict(good,reference=False)):
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):M.read_config(p)

    def test_literal_grouping_does_not_use_reporting_hashes_or_ancestral_result(self):
        fs=[dict(language='EN',ordinal=i,entry=[0]*16,ancestral_result=v)for i,v in enumerate((0,1,0,0,0))];fs[4]['entry'][0]=1
        with patch.object(M.B,'initial_memory',side_effect=[b'a',b'a',b'b',b'a',b'a']),patch.object(M,'sha',return_value='collision'):
            groups=M.share_groups(fs,{})
        self.assertEqual(len(groups),3);self.assertEqual(groups[0]['members'],[dict(language='EN',ordinal=i)for i in(0,1,3)])
        self.assertTrue(all(g['models']==0 for g in groups))


class PrivateReplay(unittest.TestCase):
    def test_exact_raw_projection_and_native_temporal_forgeries(self):
        value=os.environ.get('SGP_FS_NESTED_SEEKDIR_REPLAY_CONFIG')
        if not value:self.skipTest('own exact inputs, retained ELF/reference and new raw required')
        c=M.read_config(Path(value));fs,bs,proof,groups,parent=M.prepare(c['parent_config'],c['recipe_dir'],c['reference'],c['component_receipt'])
        cells=M.check_contract(c['field_contract'],fs,parent);r=M.read_report(c['report']);self.assertIs(r['probe_only'],False)
        with patch.object(M.B,'run',side_effect=AssertionError('raw replay must not execute CPU')):
            M.require_report(r,fs,bs,proof,groups,c['field_contract'],c['raw_dir'])
        self.assertEqual((len(r['field_holdout']),len(r['projected_input_rejections'])),(32,16))
        for group in groups:
            normal=next(x['result']for x in r['cases']if x['group']==group['ordinal']and x['label']=='normal')
            projected=next(x['result']for x in r['cases']if x['group']==group['ordinal']and x['label']=='clear_sync')
            for index in(0,1,5,6,7,13,14,15):
                bad=copy.deepcopy(normal);bad['returned'][index]^=1;bad['halt_regs']=bad['returned']
                with self.assertRaisesRegex(ValueError,'source-derived returned'):M.B.require_result(bad,bs)
            bad=copy.deepcopy(normal);bad['stores'][6]['before']='13000000'
            with self.assertRaisesRegex(ValueError,'source-derived stores'):M.B.require_result(bad,bs)
            f=copy.deepcopy(normal['fixture']);guard=bytearray.fromhex(f['guard']);guard[0]^=1;f['guard']=guard.hex()
            with self.assertRaisesRegex(ValueError,'reconstructed observed AFTER'):M.B.initial_memory(f,bs)
            for member in group['members']:
                f=next(f for f in fs if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                with self.assertRaisesRegex(ValueError,'actual captured archive'):M.F.compare_input(cell,f,projected)
                self.assertFalse(M.F.compare_projection(cell,f,projected)['actual_parent_input'])


if __name__=='__main__':unittest.main()
