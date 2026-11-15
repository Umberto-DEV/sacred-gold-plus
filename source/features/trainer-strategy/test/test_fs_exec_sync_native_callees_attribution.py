"""Source-only CLI gates and opt-in exact-input raw replay; no guest in tests."""
from pathlib import Path
import copy,importlib.util,json,os,sys,tempfile,unittest
from unittest.mock import patch


path=Path(__file__).parents[1]/'tools/attribuisci_fs_exec_sync_native_callees.py'
spec=importlib.util.spec_from_file_location('native_sync_cli_tests',path)
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


class Gates(unittest.TestCase):
    def test_output_report_inside_raw_rejected_before_preparation(self):
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);raw=root/'raw'
            args=['tool','--parent-config','unused','--field-contract','unused','--raw-dir',str(raw),'--json',str(raw/'report.json')]
            with patch.object(sys,'argv',args),patch.object(M,'analyze',side_effect=AssertionError('no heavy preparation')):
                with self.assertRaises(SystemExit)as error:M.main()
                self.assertEqual(error.exception.code,2)

    def test_modes_rejected_before_heavy_prepare(self):
        with patch.object(M,'prepare',side_effect=AssertionError('no heavy preparation')):
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'))
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'),prepare_only=True,probe=True)

    def test_complete_parent_requires_actual_grid_and_no_probe(self):
        r=dict(schema='native-fs-exec-sync-join-isolated-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
            fixtures=[{}]*16,groups=[{}]*4,cases=[{}]*8,field_holdout=[{}]*32,observer_off=[{}]*4,error_pairs=[{}]*2)
        M.require_complete_parent(r)
        for key,value in(('probe_only',True),('cpu_executed',False),('compiler_invoked',True),('cases',[]),
                          ('field_holdout',[]),('observer_off',[]),('error_pairs',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):M.require_complete_parent(bad)

    def test_grouping_uses_literal_memory_registers_and_external_model_policy(self):
        fs=[dict(language='EN',ordinal=i,entry=[0]*16,translated_result=v)for i,v in enumerate((0,1,0,0,0))]
        fs[4]['entry'][0]=1
        with patch.object(M.B,'initial_memory',side_effect=[b'a',b'a',b'b',b'a',b'a']),patch.object(M,'sha',return_value='collision'):
            groups=M.share_groups(fs,{})
        self.assertEqual(len(groups),4)
        self.assertEqual(groups[0]['members'],[dict(language='EN',ordinal=0),dict(language='EN',ordinal=3)])


class PrivateReplay(unittest.TestCase):
    def test_actual_raw_and_coherent_forgery_rejection_without_guest(self):
        value=os.environ.get('SGP_FS_EXEC_SYNC_NATIVE_REPLAY_CONFIG')
        if not value:self.skipTest('own exact inputs, ancestors, and composed raw campaign required')
        c=M.J.read_config(Path(value));fs,bs,proof,groups,paths=M.prepare(c['parent_config'])
        cells=M.check_contract(c['field_contract'],fs,paths);report=M.read_report(c['report'])
        self.assertIs(report['probe_only'],False)
        with patch.object(M.B,'run',side_effect=AssertionError('replay must not execute CPU')):
            M.require_report(report,fs,bs,proof,groups,c['field_contract'],c['raw_dir'])
        for group in groups:
            row=next(x['result']for x in report['cases']if x['group']==group['ordinal']and x['label']=='normal')
            for name,index in(('BOOL',0),('R4',4),('SP',13),('LR',14),('CPSR',15)):
                bad=copy.deepcopy(row);bad['returned'][index]^=1;bad['halt_regs']=bad['returned']
                with self.subTest(group=group['ordinal'],name=name),self.assertRaisesRegex(ValueError,'source-derived returned'):
                    M.B.require_result(bad,bs)
            for key in('flow','stores','reads','model_stores'):
                bad=copy.deepcopy(row);bad[key]=bad[key][:-1]
                with self.subTest(key=key),self.assertRaises(ValueError):M.B.require_result(bad,bs)
            for member in group['members']:
                f=next(f for f in fs if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                bad=copy.deepcopy(row);raw=bytearray.fromhex(bad['checkpoints']['wake_return']['frame']);raw[64]^=1
                bad['checkpoints']['wake_return']['frame']=raw.hex()
                with self.assertRaisesRegex(ValueError,'frozen wake_return'):M.field_contract(cell,f,bad)
            # Release overwrites the model field with the same value. That does
            # not permit pretending that Translate never wrote it beforehand.
            bad=copy.deepcopy(row);event=next(e for e in bad['stores']if e['pc']=='0x20d68ac');event['before']='02000000'
            with self.assertRaisesRegex(ValueError,'source-derived stores'):M.B.require_result(bad,bs)


if __name__=='__main__':unittest.main()
