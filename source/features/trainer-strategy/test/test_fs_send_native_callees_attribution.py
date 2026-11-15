"""Source-only CLI gates and opt-in replay of complete Send raw evidence."""
from pathlib import Path
import copy,importlib.util,os,sys,tempfile,unittest
from unittest.mock import patch

path=Path(__file__).parents[1]/'tools/attribuisci_fs_send_native_callees.py'
spec=importlib.util.spec_from_file_location('native_send_cli_tests',path)
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


class Gates(unittest.TestCase):
    def test_modes_rejected_before_heavy_prepare(self):
        with patch.object(M,'prepare',side_effect=AssertionError('no heavy preparation')):
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'))
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'),prepare_only=True,probe=True)

    def test_nested_report_rejected_before_analysis(self):
        with tempfile.TemporaryDirectory()as directory:
            raw=Path(directory)/'raw'
            for output in(raw,raw/'report.json'):
                args=['tool','--parent-config','unused','--field-contract','unused','--raw-dir',str(raw),'--json',str(output)]
                with patch.object(sys,'argv',args),patch.object(M,'analyze',side_effect=AssertionError('no heavy preparation')):
                    with self.assertRaises(SystemExit)as error:M.main()
                    self.assertEqual(error.exception.code,2)

    def test_parent_requires_complete_normal_off_counter_grid(self):
        r=dict(schema='native-fs-exec-sync-native-callees-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
            fixtures=[{}]*16,groups=[{}]*4,cases=[{}]*12,field_holdout=[{}]*32,observer_off=[{}]*4,counters=[{}]*16)
        M.require_complete_parent(r)
        for key,value in(('probe_only',True),('cpu_executed',False),('compiler_invoked',True),('cases',[]),
                          ('field_holdout',[]),('observer_off',[]),('counters',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):M.require_complete_parent(bad)

    def test_grouping_checks_literal_cpu_ram_and_external_policy(self):
        fs=[dict(language='EN',ordinal=i,entry=[0]*16,translated_result=v)for i,v in enumerate((0,1,0,0,0))]
        fs[4]['entry'][0]=1
        with patch.object(M.B,'initial_memory',side_effect=[b'a',b'a',b'b',b'a',b'a']),patch.object(M,'sha',return_value='collision'):
            groups=M.share_groups(fs,{})
        self.assertEqual(len(groups),4)
        self.assertEqual(groups[0]['members'],[dict(language='EN',ordinal=0),dict(language='EN',ordinal=3)])


class PrivateReplay(unittest.TestCase):
    def test_exact_raw_and_predecessor_guard_forgery_without_cpu(self):
        value=os.environ.get('SGP_FS_SEND_NATIVE_REPLAY_CONFIG')
        if not value:self.skipTest('own exact inputs, ancestors and complete Send raw required')
        c=M.E.J.read_config(Path(value));fs,bs,proof,groups,paths=M.prepare(c['parent_config'])
        cells=M.check_contract(c['field_contract'],fs,paths);report=M.read_report(c['report']);self.assertIs(report['probe_only'],False)
        with patch.object(M.B,'run',side_effect=AssertionError('replay must not execute CPU')):
            M.require_report(report,fs,bs,proof,groups,c['field_contract'],c['raw_dir'])
        for group in groups:
            row=next(x['result']for x in report['cases']if x['group']==group['ordinal']and x['label']=='normal')
            for index in(0,1,2,3,4,5,6,7,13,14,15):
                bad=copy.deepcopy(row);bad['returned'][index]^=1;bad['halt_regs']=bad['returned']
                with self.subTest(register=index),self.assertRaisesRegex(ValueError,'Send native source-derived returned'):
                    M.B.require_result(bad,bs)
            for key in('flow','stores','reads','model_stores'):
                bad=copy.deepcopy(row);bad[key]=bad[key][:-1]
                with self.subTest(field=key),self.assertRaises(ValueError):M.B.require_result(bad,bs)
            # A source-consistent alternate dead preimage may converge after
            # the first PUSH; it must still fail exact input provenance.
            bad=copy.deepcopy(row);f=bad['fixture'];raw=bytearray.fromhex(f['frame']);raw[0]^=1;f['frame']=raw.hex()
            original=M.B.S.initial_memory(f,{a:bs[a]for a in M.B.S.BODIES},0xA5)
            f['parent_whole_ram_sha256']=M.sha(original)
            p=M.B.predict(f);bad['frame_before']=p['frame_before'];bad['stores']=p['stores']
            bad['before_whole_ram_sha256']=M.sha(M.B.initial_memory(f,bs))
            M.B.require_result(bad,bs)
            for member in group['members']:
                original_fixture=next(f for f in fs if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                alternate=copy.deepcopy(original_fixture);alternate['frame']=f['frame'];alternate['parent_whole_ram_sha256']=f['parent_whole_ram_sha256']
                with self.assertRaisesRegex(ValueError,'frozen actual BEFORE provenance'):M.field_contract(cell,alternate,bad)
                other=copy.deepcopy(row);other['checkpoints']['final']['regs'][14]=0x20D7928
                with self.assertRaisesRegex(ValueError,'frozen final'):M.field_contract(cell,original_fixture,other)


if __name__=='__main__':unittest.main()
