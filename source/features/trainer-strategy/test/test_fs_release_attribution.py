"""CPU-free CLI/config guards and optional authenticated Release replay."""
from pathlib import Path
import contextlib,copy,gc,importlib.util,io,json,os,sys,tempfile,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('release_public_cli',Path(__file__).parents[1]/'tools/attribuisci_fs_release.py')
Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)


class Dispatch(unittest.TestCase):
    def test_prepare_only_never_calls_guest(self):
        with patch.object(Z.H.H.H.R.W,'require_host_budget'),patch.object(Z,'prepare',return_value=([],{},{})),patch.object(Z.B,'run',side_effect=AssertionError('forbidden guest'))as run:
            self.assertIs(Z.analyze(Path('unused'),'EN',Path('unused'),Path('unused'),Path('unused'),prepare_only=True)['cpu_executed'],False)
        run.assert_not_called()

    def test_exclusive_modes_fail_before_analysis(self):
        argv=['release']
        for name in('rom','parent-report','parent-config','recipe-dir','json'):argv+=['--'+name,'unused']
        argv+=['--language','EN','--prepare-only','--probe']
        with patch.object(sys,'argv',argv),patch.object(Z,'analyze',side_effect=AssertionError('forbidden analysis'))as call:
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit)as error:Z.main()
        self.assertEqual(error.exception.code,2);call.assert_not_called()

    def test_parent_config_rejects_wrong_identity_extra_keys_and_aliases(self):
        config={k:'unused'for k in Z.PREPARE_KEYS};config.update(language='EN',capture_source=None)
        with tempfile.TemporaryDirectory()as name:
            path=Path(name)/'config.json'
            path.write_text(json.dumps(dict(EN=dict(prepare=config))))
            got=Z.read_parent_config(path,Path('unused'),'EN');self.assertEqual(got['language'],'EN');self.assertEqual(got['rom'],Path('unused'))
            for kind in('language','rom','extra','path_bool','capture_bool'):
                x=copy.deepcopy(config)
                if kind=='language':x['language']='IT'
                elif kind=='rom':x['rom']='another-ROM'
                elif kind=='extra':x['extra']='unused'
                elif kind=='path_bool':x['objects']=True
                else:x['capture_source']=False
                path.write_text(json.dumps(dict(EN=dict(prepare=x))))
                with self.subTest(kind=kind),self.assertRaises(ValueError):Z.read_parent_config(path,Path('unused'),'EN')


@unittest.skipUnless(os.environ.get('SGP_FS_RELEASE_REPLAY_CONFIG'),'requires private exact Release reports/parents/ROMs/recipes')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config=json.loads(Path(os.environ['SGP_FS_RELEASE_REPLAY_CONFIG']).read_bytes());cls.rows=[]
        for lang in('EN','IT'):
            c=config[lang];kwargs={k:v if k=='language'else Path(v)for k,v in c['prepare'].items()}
            fixtures,bodies,proof=Z.prepare(**kwargs);report=Z.H.H.H.N.read_report(Path(c['report']))
            cls.rows.append((lang,report,fixtures,bodies,proof,Path(c['raw_dir'])));gc.collect()

    def test_authenticated_source_grid_and_all_native_oracles(self):
        for lang,r,fixtures,bodies,proof,raw in self.rows:
            self.assertEqual(r['schema'],'native-fs-release-isolated-v1');self.assertEqual(r['language'],lang)
            self.assertEqual(Z.wire(r['source_sha256']),Z.wire(Z.source_identities()))
            self.assertEqual(Z.wire(r['fixtures']),Z.wire(fixtures));self.assertEqual(Z.wire(r['proof']),Z.wire(proof))
            self.assertIs(r['cpu_executed'],True);self.assertIs(r['probe_only'],False);self.assertIs(r['compiler_invoked'],False)
            self.assertEqual(len(r['cases']),48);self.assertEqual(len(fixtures),8)
            for i,cell in enumerate(r['cases']):
                ordinal,pi=divmod(i,6);label,options=Z.POLICIES[pi];x=cell['result']
                self.assertEqual(cell['label'],label);self.assertEqual(Z.wire(x['fixture']),Z.wire(fixtures[ordinal]))
                p=dict(wake_value=0,clobber=False,stale_error=False);p.update({k:v for k,v in options.items()if k in p})
                self.assertEqual(Z.wire((x['policy'],x['observe'],x['fill'])),Z.wire((p,options.get('observe',True),options.get('fill',0xA5))))
                self.assertTrue(Z.B.require_result(x,bodies))

    def test_raw_report_equality_before_semantic_replay(self):
        for lang,r,fixtures,bodies,proof,raw in self.rows:
            paths=sorted(raw.glob('[0-9][0-9]-*.json.gz'));self.assertEqual(len(paths),48)
            for path,cell in zip(paths,r['cases']):self.assertEqual(Z.H.H.H.N.read_report(path),cell['result'])

    def test_typed_and_native_forged_receipts_rejected(self):
        for lang,r,fixtures,bodies,proof,raw in self.rows:
            original=r['cases'][0]['result']
            for kind in('return_bool','LR','R3','flags','flow','read_float','store_bool','model_write','steps_float','pc_missing','whole','guard','frame_before','frame_after','archive','policy_bool'):
                x=copy.deepcopy(original)
                if kind=='return_bool':x['returned'][0]=1
                elif kind=='LR':x['returned'][14]=Z.B.RETURN
                elif kind=='R3':x['returned'][3]=0
                elif kind=='flags':x['returned'][15]^=1<<29
                elif kind=='flow':x['flow'][8]['regs'][0]^=1
                elif kind=='read_float':x['reads'][0]['bytes']=4.0
                elif kind=='store_bool':next(e for e in x['stores']if e['value']==0)['value']=False
                elif kind=='model_write':x['services'][0]['writes']=[dict(address=Z.B.FILE+20,value=0)]
                elif kind=='steps_float':x['steps']=36.0
                elif kind=='pc_missing':x['observed_pcs'].pop()
                elif kind=='whole':x['whole_ram_sha256']='0'*64
                elif kind in('guard','frame_before','frame_after','archive'):
                    key={'guard':'guard_after','archive':'archive_after'}.get(kind,kind);b=bytearray.fromhex(x[key]);b[0]^=1;x[key]=b.hex()
                else:x['policy']['wake_value']=False
                self.assertNotEqual(Z.wire(x),Z.wire(original),kind+' must change typed receipt')
                with self.subTest(lang=lang,kind=kind),self.assertRaises(ValueError):Z.B.require_result(x,bodies)

    def test_stale_causal_control_off_and_void_clobber(self):
        for lang,r,fixtures,bodies,proof,raw in self.rows:
            self.assertEqual(len(r['observer_off']),8);self.assertEqual(len(r['counters']),8)
            for i in range(8):
                group=[c['result']for c in r['cases'][i*6:(i+1)*6]];normal,off,stale,void,clobber,fill=group
                self.assertEqual(r['observer_off'][i],dict(ordinal=i,proof=Z.require_off_pair(normal,off,bodies)))
                self.assertEqual(r['counters'][i],dict(ordinal=i,rejection=Z.counter_rejection(stale,normal,bodies),policy_disguised=True))
                self.assertEqual(r['counters'][i]['rejection'],'Release source-derived stores')
                for x in group:self.assertEqual(x['returned'][0],0x80)
                self.assertEqual(stale['whole_ram_sha256'],normal['whole_ram_sha256']);self.assertNotEqual(stale['before_whole_ram_sha256'],normal['before_whole_ram_sha256'])
                self.assertEqual(stale['stores'][8]['before'],'02000000');self.assertEqual(stale['stores'][8]['value'],fixtures[i]['translated_result'])
                self.assertEqual(void['returned'],normal['returned']);self.assertEqual(void['whole_ram_sha256'],normal['whole_ram_sha256'])
                self.assertEqual([a['pc']for a,b in zip(void['flow'],normal['flow'])if a!=b],['0x20d68b4'])
                self.assertEqual(clobber['whole_ram_sha256'],normal['whole_ram_sha256']);self.assertEqual(clobber['returned'][3],0xA5000003)
                self.assertEqual(clobber['returned'][15],0xA000001F)
                self.assertEqual(fill['frame_after'],normal['frame_after']);self.assertEqual(fill['archive_after'],normal['archive_after'])
                self.assertNotEqual(fill['whole_ram_sha256'],normal['whole_ram_sha256'])
                forged=copy.deepcopy(stale);b=bytearray.fromhex(forged['fixture']['frame']);b[0]^=1;forged['fixture']['frame']=b.hex()
                # A different base fixture cannot establish the same-input control.
                self.assertNotEqual(Z.wire(forged['fixture']),Z.wire(stale['fixture']))
                with self.assertRaises(ValueError):Z.counter_rejection(forged,normal,bodies)


if __name__=='__main__':unittest.main()
