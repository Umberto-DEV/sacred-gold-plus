"""CLI admission and opt-in raw replay without another guest execution."""
from pathlib import Path
import copy,importlib.util,json,os,struct,sys,tempfile,unittest
from unittest.mock import patch

path=Path(__file__).parents[1]/'tools/attribuisci_fs_translate.py'
spec=importlib.util.spec_from_file_location('translate_cli_tests',path)
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


class Gates(unittest.TestCase):
    def test_mode_gates_precede_heavy_preparation(self):
        with patch.object(M,'prepare',side_effect=AssertionError('no heavy preparation')):
            with self.assertRaises(ValueError):M.analyze(*([Path('unused')]*5))
            with self.assertRaises(ValueError):M.analyze(*([Path('unused')]*5),prepare_only=True,probe=True)

    def test_nested_report_is_rejected_before_export_or_execution(self):
        with tempfile.TemporaryDirectory()as name:
            raw=Path(name)/'raw'
            for export in(False,True):
                args=['tool','--parent-config','unused','--raw-dir',str(raw),'--json',str(raw/'report.json')]+(['--export-components']if export else[])
                with (patch.object(sys,'argv',args),patch.object(M,'read_components',side_effect=AssertionError('no readback')),
                      patch.object(M,'analyze',side_effect=AssertionError('no preparation'))):
                    with self.assertRaises(SystemExit)as error:M.main()
                    self.assertEqual(error.exception.code,2)

    def test_complete_parent_and_strict_config(self):
        r=dict(schema='native-fs-send-native-callees-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
            groups=[{}]*4,fixtures=[{}]*16,cases=[{}]*12,field_holdout=[{}]*32,observer_off=[{}]*4,counters=[{}]*16)
        M.require_complete_parent(r)
        for key,value in(('probe_only',True),('compiler_invoked',True),('cpu_executed',False),('cases',[]),('counters',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):M.require_complete_parent(bad)
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'replay.json';valid={k:'private-relative-path'for k in M.CONFIG_KEYS}
            p.write_text(json.dumps(valid));self.assertEqual(set(M.read_config(p)),M.CONFIG_KEYS)
            for bad in({},dict(valid,extra='x'),dict(valid,reference=False)):
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):M.read_config(p)

    def test_literal_grouping_includes_default_policy_even_on_sha_collision(self):
        fs=[dict(language='EN',ordinal=i,entry=[0]*16,default_result=v)for i,v in enumerate((0,1,0,0,0))];fs[4]['entry'][0]=1
        with patch.object(M.B,'initial_memory',side_effect=[b'a',b'a',b'b',b'a',b'a']),patch.object(M,'sha',return_value='collision'):
            groups=M.share_groups(fs,{})
        self.assertEqual(len(groups),4);self.assertEqual(groups[0]['members'],[dict(language='EN',ordinal=0),dict(language='EN',ordinal=3)])

    def test_literal_table_are_readonly_and_tied_to_their_native_pcs(self):
        self.assertTrue(M.B.read_allowed(0x20D6974,M.B.POOL,4));self.assertTrue(M.B.read_allowed(0x20D697C,M.B.TABLE+16,4))
        self.assertFalse(M.B.read_allowed(0x20D6974,M.B.TABLE+16,4));self.assertFalse(M.B.read_allowed(0x20D697C,M.B.TABLE+12,4))
        for address in(M.B.POOL,M.B.TABLE,M.B.TABLE+16):self.assertFalse(M.B.write_allowed(0x20D6A40,address,4))


class PrivateReplay(unittest.TestCase):
    def test_exact_raw_and_full_oracle_reject_old_model_abi_and_writer_forgeries(self):
        value=os.environ.get('SGP_FS_TRANSLATE_REPLAY_CONFIG')
        if not value:self.skipTest('own exact inputs, recovered object/reference and Translate raw required')
        c=M.read_config(Path(value));fs,bs,proof,groups,parent=M.prepare(c['parent_config'],c['recipe_dir'],c['reference'],c['component_receipt'])
        cells=M.check_contract(c['field_contract'],fs,parent,c['component_receipt']);r=M.read_report(c['report']);self.assertIs(r['probe_only'],False)
        with patch.object(M.B,'run',side_effect=AssertionError('raw replay must not execute CPU')):
            M.require_report(r,fs,bs,proof,groups,c['field_contract'],c['raw_dir'])
        for group in groups:
            row=next(x['result']for x in r['cases']if x['group']==group['ordinal']and x['label']=='normal')
            for index in(0,1,4,13,14,15):
                bad=copy.deepcopy(row);bad['returned'][index]^=1;bad['halt_regs']=bad['returned']
                with self.subTest(register=index),self.assertRaisesRegex(ValueError,'source-derived returned'):M.B.require_result(bad,bs)
            bad=copy.deepcopy(row);bad['stores'][-1]['before']=struct.pack('<I',row['fixture']['default_result']).hex()
            with self.assertRaisesRegex(ValueError,'source-derived stores'):M.B.require_result(bad,bs)
            for address in(M.B.ENTRY,M.B.TABLE):
                changed=dict(bs);raw=bytearray(changed[address]);raw[-1]^=1;changed[address]=bytes(raw)
                with self.assertRaisesRegex(ValueError,'authenticated component'):M.B.initial_memory(row['fixture'],changed)
            for member in group['members']:
                f=next(f for f in fs if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                old=copy.deepcopy(row);old['returned'][1]=4;old['returned'][14]=0x20D7754;old['halt_regs']=old['returned']
                M.field_contract(cell,f,old)
                with self.assertRaisesRegex(ValueError,'source-derived returned'):M.B.require_result(old,bs)


if __name__=='__main__':unittest.main()
