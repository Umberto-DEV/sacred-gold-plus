"""Prepare/CLI dispatch guards: pure control tests, no guest CPU or compiler."""
from pathlib import Path
import contextlib,copy,gc,gzip,importlib.util,io,json,os,sys,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('send_public_cli',Path(__file__).parents[1]/'tools/attribuisci_fs_send.py')
Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)


class Dispatch(unittest.TestCase):
    def test_prepare_only_never_calls_cpu_collector(self):
        args=[Path('unused'),'EN',Path('unused'),None]+[Path('unused')]*6
        with patch.object(Z.H.R.W,'require_host_budget'),patch.object(Z,'prepare',return_value=([],{},{})),patch.object(Z.B,'run',side_effect=AssertionError('forbidden guest'))as run:
            result=Z.analyze(*args,prepare_only=True)
        self.assertIs(result['cpu_executed'],False);run.assert_not_called()

    def test_cpu_and_prepare_modes_are_rejected_before_analysis(self):
        argv=['send']
        for name in('rom','parent-report','objects','strategy-object','read-recipe','wait-recipe','find-recipe','recipe-dir','json'):
            argv+=['--'+name,'unused']
        argv+=['--language','EN','--prepare-only','--probe']
        with patch.object(sys,'argv',argv),patch.object(Z,'analyze',side_effect=AssertionError('forbidden analysis'))as call:
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit)as error:Z.main()
        self.assertEqual(error.exception.code,2);call.assert_not_called()

    def test_historical_parent_needs_exact_retained_source(self):
        current=Z.H.source_identities();parent=dict(source_sha256=current)
        self.assertEqual(Z.require_parent_sources(parent,None),dict(exact_current=True,oracle_only_revision=False))
        parent=copy.deepcopy(parent);key=str(Path(Z.H.__file__).resolve().relative_to(Z.P.SOURCE))
        parent['source_sha256'][key]=Z.CAPTURE_SHA
        with self.assertRaises(ValueError):Z.require_parent_sources(parent,None)

    def test_duplicate_or_bool_parent_cells_fail_before_rom_model(self):
        grid=[dict(plus=p,seed=s)for p in(0,1)for s in(0x12345678,0x12345679)]
        parent=dict(source_sha256=Z.H.source_identities(),schema='trainer31-native-fs-find-caller-v1',language='EN',
            cpu_executed=True,probe_only=False,recipes=Z.H.RECIPES,namespace_bindings=Z.H.BINDINGS,positives=grid)
        for kind in('duplicate','bool'):
            r=copy.deepcopy(parent)
            if kind=='duplicate':r['positives'][3]=copy.deepcopy(r['positives'][2])
            else:r['positives'][2]['plus']=True
            with patch.object(Z.H.N,'read_report',return_value=r),patch.object(Z.P.G.S.SHARED,'read_current',side_effect=AssertionError('forbidden ROM model')):
                with self.subTest(kind=kind),self.assertRaises(ValueError):
                    Z.prepare(Path('unused'),'EN',Path('unused'),None,*([Path('unused')]*6))


ENV=('SGP_FS_SEND_REPORT_DIR','SGP_FS_SEND_RAW_DIR','SGP_FS_SEND_ROM_DIR','SGP_FS_SEND_PARENT_DIR',
     'SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR','SGP_FS_SEND_READ_RECIPE','SGP_FS_SEND_WAIT_RECIPE',
     'SGP_FS_SEND_FIND_RECIPE','SGP_FS_SEND_RECIPE_DIR')
POLICIES=[('normal',1,False,True,0xA5),('off',1,False,False,0xA5),('false',0,False,True,0xA5),
          ('truthy2',2,False,True,0xA5),('clobber',1,True,True,0xA5),('fill39',1,False,True,0x39)]
read=lambda p:json.loads(gzip.decompress(p.read_bytes()))


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact Send reports/parents/ROMs/objects')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[]
        for language in('EN','IT'):
            report=read(Path(os.environ[ENV[0]])/('send-'+language+'.json.gz'))
            source=os.environ.get('SGP_FS_SEND_PARENT_SOURCE')
            fixtures,bodies,proof=Z.prepare(Path(os.environ[ENV[2]])/('r4-'+language+'.nds'),language,
                Path(os.environ[ENV[3]])/('find-caller-'+language+'.json.gz'),None if source is None else Path(source),
                Path(os.environ[ENV[4]])/('public-build-'+language),Path(os.environ[ENV[5]])/('build-'+language)/'teams.o',
                *(Path(os.environ[k])for k in ENV[6:10]))
            cls.rows.append((language,report,fixtures,bodies,proof));gc.collect()

    def test_identity_provenance_distinct_cells_and_all_source_oracles(self):
        for language,r,fixtures,bodies,proof in self.rows:
            self.assertEqual(r['schema'],'native-fs-send-isolated-v1');self.assertEqual(r['source_sha256'],Z.source_identities())
            self.assertEqual(Z.wire(r['proof']),Z.wire(proof));self.assertEqual(Z.wire(r['fixtures']),Z.wire(fixtures))
            self.assertIs(r['cpu_executed'],True);self.assertIs(r['probe_only'],False)
            self.assertEqual(len(r['cases']),24);self.assertEqual(len(r['observer_off']),4);self.assertEqual(len(r['counters']),4)
            for index,(cell,(ordinal,policy))in enumerate(zip(r['cases'],[(i,p)for i in range(4)for p in POLICIES])):
                label,value,clobber,observe,fill=policy;row=cell['result']
                self.assertEqual(cell['label'],label);self.assertEqual(Z.wire(row['fixture']),Z.wire(fixtures[ordinal]))
                self.assertEqual(Z.wire((row['policy'],row['observe'],row['fill'])),Z.wire((dict(execute=value,clobber=clobber),observe,fill)))
                self.assertTrue(Z.B.require_result(row,bodies))
            for ordinal in range(4):
                normal,off,false=r['cases'][ordinal*6]['result'],r['cases'][ordinal*6+1]['result'],r['cases'][ordinal*6+2]['result']
                self.assertEqual(r['observer_off'][ordinal],dict(ordinal=ordinal,proof=Z.require_off_pair(normal,off,bodies)))
                self.assertEqual(r['counters'][ordinal],dict(ordinal=ordinal,rejection=Z.counter_rejection(false,normal,bodies),policy_disguised=True))

    def test_all_raw_cells_match_report_before_semantic_evaluation(self):
        for language,r,fixtures,bodies,proof in self.rows:
            paths=sorted((Path(os.environ[ENV[1]])/('raw-'+language)).glob('[0-9][0-9]-*.json.gz'))
            self.assertEqual(len(paths),24)
            for path,cell in zip(paths,r['cases']):self.assertEqual(read(path),cell['result'])

    def test_forged_native_and_typed_evidence_is_rejected(self):
        for language,r,fixtures,bodies,proof in self.rows:
            for kind in('register_bool','return','LR','flow','store_bool','read_float','service_bool','whole','guard','steps_float','frame','archive','policy_bool'):
                x=copy.deepcopy(r['cases'][0]['result'])
                if kind=='register_bool':x['entry'][2]=False
                elif kind=='return':x['returned'][0]=0
                elif kind=='LR':x['returned'][14]=0x20D80F8
                elif kind=='flow':x['flow'][10]['regs'][15]^=1<<29
                elif kind=='store_bool':next(e for e in x['stores']if e['value']==0)['value']=False
                elif kind=='read_float':x['reads'][0]['bytes']=4.0
                elif kind=='service_bool':x['services'][0]['result']=True
                elif kind=='whole':x['whole_ram_sha256']='0'*64
                elif kind=='guard':x['guard_after']='00'+x['guard_after'][2:]
                elif kind=='steps_float':x['steps']=92.0
                elif kind=='frame':
                    frame=bytearray.fromhex(x['frame_after']);frame[0]^=1;x['frame_after']=frame.hex()
                elif kind=='archive':x['archive_after']='01'+x['archive_after'][2:]
                else:x['policy']['execute']=True
                with self.subTest(language=language,kind=kind),self.assertRaises(ValueError):Z.B.require_result(x,bodies)

    def test_counter_and_controls_preserve_only_the_claimed_state(self):
        for language,r,fixtures,bodies,proof in self.rows:
            for ordinal in range(4):
                group=[c['result']for c in r['cases'][6*ordinal:6*ordinal+6]];normal=group[0]
                self.assertEqual([x['returned'][0]for x in group[:4]],[1,1,0,2])
                for x in group[1:5]:
                    self.assertEqual(x['whole_ram_sha256'],normal['whole_ram_sha256']);self.assertEqual(x['frame_after'],normal['frame_after'])
                    self.assertEqual(x['archive_after'],normal['archive_after'])
                self.assertEqual(group[4]['returned'][3],normal['returned'][3]);self.assertNotEqual(group[4]['returned'][12],normal['returned'][12])
                self.assertEqual(group[5]['frame_after'],normal['frame_after']);self.assertEqual(group[5]['archive_after'],normal['archive_after'])
                self.assertNotEqual(group[5]['whole_ram_sha256'],normal['whole_ram_sha256'])


if __name__=='__main__':unittest.main()
