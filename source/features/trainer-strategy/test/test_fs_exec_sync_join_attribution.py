"""Preparation/replay gates for the native NextNULL result consumer."""
from pathlib import Path
import copy,importlib.util,json,os,tempfile,unittest
from unittest.mock import patch


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('sync_join_cli',Path(__file__).parents[1]/'tools/attribuisci_fs_exec_sync_join.py')


class Gates(unittest.TestCase):
    def test_no_missing_raw_or_mixed_modes_before_heavy_preparation(self):
        with patch.object(M,'prepare',side_effect=AssertionError('heavy preparation forbidden')):
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'))
            with self.assertRaises(ValueError):M.analyze(Path('unused'),Path('unused'),prepare_only=True,probe=True)

    def test_parent_complete_grid_and_probe_rejected_before_preparation(self):
        r=dict(schema='native-fs-next-isolated-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
               fixtures=[{}]*16,groups=[{}]*4,cases=[{}]*16,field_holdout=[{}]*64,observer_off=[{}]*4,counters=[{}]*4)
        M.require_complete_parent(r)
        for key,value in(('probe_only',True),('cpu_executed',False),('compiler_invoked',True),('cases',[]),('field_holdout',[]),('observer_off',[]),('counters',[])):
            bad=copy.deepcopy(r);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):M.require_complete_parent(bad)
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);report=root/'probe.json';report.write_text(json.dumps(dict(r,probe_only=True)))
            c={key:'unused'for key in M.PARENT_CONFIG_KEYS};c['report']=str(report)
            config=root/'config.json';config.write_text(json.dumps(c))
            with patch.object(M.N,'prepare',side_effect=AssertionError('heavy preparation forbidden')):
                with self.assertRaisesRegex(ValueError,'not a probe'):M.prepare(config)

    def test_replay_config_rejects_unknown_keys_and_non_paths(self):
        with tempfile.TemporaryDirectory()as directory:
            p=Path(directory)/'config.json';valid={k:'private-relative-path'for k in M.CONFIG_KEYS}
            p.write_text(json.dumps(valid));self.assertEqual(set(M.read_config(p)),M.CONFIG_KEYS)
            for bad in({},dict(valid,extra='x'),dict(valid,report=False)):
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):M.read_config(p)

    def test_grouping_compares_literal_images_even_if_digests_collide(self):
        fixtures=[dict(language='EN',ordinal=i,entry=[0]*16)for i in range(3)]
        with patch.object(M.B,'initial_memory',side_effect=[b'first',b'second',b'first']),patch.object(M,'sha',return_value='same-digest'):
            groups=M.share_groups(fixtures,{})
        self.assertEqual(len(groups),2)
        self.assertEqual(groups[0]['members'],[dict(language='EN',ordinal=0),dict(language='EN',ordinal=2)])
        self.assertEqual(groups[1]['members'],[dict(language='EN',ordinal=1)])


class PrivateReplay(unittest.TestCase):
    def test_native_suffix_raw_replay_without_guest_and_output_mutants(self):
        value=os.environ.get('SGP_FS_EXEC_SYNC_JOIN_REPLAY_CONFIG')
        if not value:self.skipTest('own exact ROMs, ancestors and join raw campaign required')
        c=M.read_config(Path(value));fixtures,bodies,proof,groups=M.prepare(c['parent_config'])
        cells=M.check_contract(c['field_contract'],fixtures,proof)
        report=M.read_report(c['report']);self.assertIs(report['probe_only'],False)
        M.require_report(report,fixtures,bodies,proof,groups,c['field_contract'],c['raw_dir'])
        for g in groups:
            row=report['cases'][g['ordinal']*2]['result'];M.B.require_result(row,bodies)
            for field,index in(('BOOL',0),('R4',4),('SP',13),('LR',14),('CPSR',15)):
                bad=copy.deepcopy(row);bad['returned'][index]^=(1<<30 if index==15 else 4 if index in(4,13,14)else 1)
                bad['halt_regs']=bad['returned']
                with self.subTest(group=g['ordinal'],field=field),self.assertRaisesRegex(ValueError,'source-derived returned'):
                    M.B.require_result(bad,bodies)
            for key in('flow','reads'):
                bad=copy.deepcopy(row)
                if key=='flow':
                    skipped=5 if row['fixture']['translated_result']==0 else 4
                    bad[key]=[v for i,v in enumerate(bad[key])if i!=skipped]
                else:bad[key]=bad[key][:-1]
                with self.assertRaises(ValueError):M.B.require_result(bad,bodies)
            bad=copy.deepcopy(row);bad['fixture']['guard']='39'*56;bad['guard_before']=bad['guard_after']='39'*56
            with self.assertRaisesRegex(ValueError,'guard.*image'):M.B.require_result(bad,bodies)
            for area,address in(('frame',M.B.FRAME),('archive',M.B.ARC)):
                bad=copy.deepcopy(row);changed=bytearray.fromhex(bad[area+'_after']);changed[0]^=1
                bad[area+'_after']=changed.hex();memory=bytearray(M.B.initial_memory(row['fixture'],bodies))
                memory[address-M.B.BASE:address-M.B.BASE+len(changed)]=changed
                bad['whole_ram_sha256']=M.sha(bytes(memory))
                with self.assertRaisesRegex(ValueError,'source-derived '+area+'_after'):M.B.require_result(bad,bodies)
                member=g['members'][0]
                f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                with self.assertRaisesRegex(ValueError,'frozen unchanged '+area):M.field_contract(cell,f,bad)
            for member in g['members']:
                f=next(f for f in fixtures if(f['language'],f['ordinal'])==(member['language'],member['ordinal']))
                cell=next(x for x in cells if(x['language'],x['ordinal'])==(member['language'],member['ordinal']))
                M.field_contract(cell,f,row)
                bad=copy.deepcopy(row);bad['returned'][0]^=1
                with self.assertRaisesRegex(ValueError,'frozen actual entry/returned'):
                    M.field_contract(cell,f,bad)


if __name__=='__main__':unittest.main()
