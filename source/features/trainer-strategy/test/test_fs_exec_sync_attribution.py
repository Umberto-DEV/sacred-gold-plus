"""CPU-free dispatch, replay and falsification; private inputs supplied by config."""
from pathlib import Path
import contextlib,copy,gc,importlib.util,io,json,os,sys,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('exec_sync_public_cli',Path(__file__).parents[1]/'tools/attribuisci_fs_exec_sync.py')
Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)


class Dispatch(unittest.TestCase):
    def test_prepare_does_not_call_guest(self):
        args=[Path('unused'),'EN']+[Path('unused')]*10
        with patch.object(Z.H.H.R.W,'require_host_budget'),patch.object(Z,'prepare',return_value=([],{},{})),patch.object(Z.B,'run',side_effect=AssertionError('forbidden guest'))as run:
            self.assertIs(Z.analyze(*args,prepare_only=True)['cpu_executed'],False)
        run.assert_not_called()

    def test_exclusive_cli_modes_rejected_before_analysis(self):
        argv=['exec']
        for name in('rom','parent-report','find-parent-report','objects','strategy-object','read-recipe','wait-recipe','find-recipe','send-recipe','recipe-dir','json'):
            argv+=['--'+name,'unused']
        argv+=['--language','EN','--probe','--prepare-only']
        with patch.object(sys,'argv',argv),patch.object(Z,'analyze',side_effect=AssertionError('forbidden analysis'))as call:
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit)as error:Z.main()
        self.assertEqual(error.exception.code,2);call.assert_not_called()

    def test_parent_must_have_actual_cpu_and_exact_source(self):
        parent=dict(schema='native-fs-send-isolated-v1',language='EN',cpu_executed=False,probe_only=False,
            source_sha256=Z.H.source_identities(),proof={},fixtures=[])
        with self.assertRaises(ValueError):Z.check_parent(parent,'EN',[],{},{})
        parent['cpu_executed']=True;parent['source_sha256']={}
        with self.assertRaises(ValueError):Z.check_parent(parent,'EN',[],{},{})

    def test_counter_pair_rejects_different_fill_or_push_preimage(self):
        normal=dict(policy=dict(result=0,void_value=0,clobber=False,release_error=None),observe=True,fill=0xA5,
            fixture=dict(frame='39'*312),entry=[0]*16,before_whole_ram_sha256='a'*64,
            returned=[1],services=[dict(entry=[0]),dict(entry=[0])])
        for kind in('fill','preimage'):
            counter=copy.deepcopy(normal);counter['policy']['release_error']=1;counter['returned']=[0]
            if kind=='fill':counter['fill']=0x39;counter['before_whole_ram_sha256']='b'*64
            else:counter['fixture']['frame']='00'+counter['fixture']['frame'][2:]
            with patch.object(Z.B,'require_result',side_effect=[True,True,ValueError('ExecuteSync source-derived returned')]):
                with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'same prestate'):
                    Z.counter_rejection(counter,normal,{})

    def test_native_ownership_rejects_model_fields_and_async(self):
        B=Z.B
        for address in(B.FRAME,B.FRAME+4):self.assertTrue(B.write_allowed(B.ENTRY,address,4))
        for pc,address,n in((B.TRANSLATE,B.FILE+20,4),(B.ENTRY,B.FRAME+8,4),(B.ENTRY,B.FRAME,8),(0x20D7770,B.FRAME,4)):
            self.assertFalse(B.write_allowed(pc,address,n))
        self.assertTrue(B.read_allowed(0x20D7774,B.FILE+20,4))
        self.assertFalse(B.read_allowed(0x20D7774,B.FILE+16,4))


@unittest.skipUnless(os.environ.get('SGP_FS_EXEC_SYNC_REPLAY_CONFIG'),'requires private exact reports/ROMs/ancestors/recipes')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config=json.loads(Path(os.environ['SGP_FS_EXEC_SYNC_REPLAY_CONFIG']).read_bytes());cls.rows=[]
        for language in('EN','IT'):
            c=config[language];kwargs={k:(v if k=='language'else None if v is None else Path(v))for k,v in c['prepare'].items()}
            fixtures,bodies,proof=Z.prepare(**kwargs);report=Z.H.H.N.read_report(Path(c['report']))
            cls.rows.append((language,report,fixtures,bodies,proof,Path(c['raw_dir'])));gc.collect()

    def test_all_cells_are_authenticated_and_source_verified(self):
        for language,r,fixtures,bodies,proof,raw in self.rows:
            self.assertEqual(r['schema'],'native-fs-exec-sync-isolated-v1');self.assertEqual(r['language'],language)
            self.assertEqual(Z.wire(r['source_sha256']),Z.wire(Z.source_identities()))
            self.assertEqual(Z.wire(r['fixtures']),Z.wire(fixtures));self.assertEqual(Z.wire(r['proof']),Z.wire(proof))
            self.assertIs(r['cpu_executed'],True);self.assertIs(r['probe_only'],False);self.assertIs(r['compiler_invoked'],False)
            self.assertEqual(len(r['cases']),32)
            for i,cell in enumerate(r['cases']):
                ordinal,pi=divmod(i,8);label,options=Z.POLICIES[pi];x=cell['result']
                self.assertEqual(cell['label'],label);self.assertEqual(Z.wire(x['fixture']),Z.wire(fixtures[ordinal]))
                p=dict(result=0,void_value=0,clobber=False,release_error=None);p.update({k:v for k,v in options.items()if k in p})
                self.assertEqual(Z.wire((x['policy'],x['observe'],x['fill'])),Z.wire((p,options.get('observe',True),options.get('fill',0xA5))))
                self.assertTrue(Z.B.require_result(x,bodies))

    def test_raw_is_preserved_before_evaluation(self):
        for language,r,fixtures,bodies,proof,raw in self.rows:
            paths=sorted(raw.glob('[0-9][0-9]-*.json.gz'));self.assertEqual(len(paths),32)
            for path,cell in zip(paths,r['cases']):self.assertEqual(Z.H.H.N.read_report(path),cell['result'])

    def test_forged_native_and_typed_receipts_are_rejected(self):
        for language,r,fixtures,bodies,proof,raw in self.rows:
            for kind in('return','LR','R3','flags','flow','read_float','store_float','service_bool','model_write_bool','steps_float','whole','guard','frame','archive','policy_bool','extra_policy'):
                x=copy.deepcopy(r['cases'][0]['result'])
                if kind=='return':x['returned'][0]=0
                elif kind=='LR':x['returned'][14]=Z.B.RETURN
                elif kind=='R3':x['returned'][3]=0
                elif kind=='flags':x['returned'][15]^=1<<29
                elif kind=='flow':x['flow'][7]['regs'][0]^=1
                elif kind=='read_float':x['reads'][0]['bytes']=4.0
                elif kind=='store_float':x['stores'][0]['bytes']=4.0
                elif kind=='service_bool':x['services'][0]['result_r0']=False
                elif kind=='model_write_bool':x['services'][0]['writes'][0]['value']=False
                elif kind=='steps_float':x['steps']=20.0
                elif kind=='whole':x['whole_ram_sha256']='0'*64
                elif kind=='guard':x['guard_after']=('01'if x['guard_after'][:2]!='01'else'00')+x['guard_after'][2:]
                elif kind=='frame':x['frame_after']=('01'if x['frame_after'][:2]!='01'else'00')+x['frame_after'][2:]
                elif kind=='archive':
                    image=bytearray.fromhex(x['archive_after']);image[0]^=1;x['archive_after']=image.hex()
                elif kind=='policy_bool':x['policy']['result']=False
                else:x['policy']['extra']=1
                self.assertNotEqual(Z.wire(x),Z.wire(r['cases'][0]['result']),kind+' must actually change typed evidence')
                with self.subTest(language=language,kind=kind),self.assertRaises((ValueError,TypeError)):Z.B.require_result(x,bodies)

    def test_off_and_error_counter_receipts(self):
        for language,r,fixtures,bodies,proof,raw in self.rows:
            self.assertEqual(len(r['observer_off']),4);self.assertEqual(len(r['counters']),4)
            for i in range(4):
                group=[c['result']for c in r['cases'][i*8:(i+1)*8]];normal=group[0]
                self.assertEqual(r['observer_off'][i],dict(ordinal=i,proof=Z.require_off_pair(normal,group[1],bodies)))
                self.assertEqual(r['counters'][i],dict(ordinal=i,rejection=Z.counter_rejection(group[3],normal,bodies),policy_disguised=True))
                self.assertEqual([x['returned'][0]for x in group[:4]],[1,1,0,0])
                for x in group[2:4]:
                    a=bytes.fromhex(normal['frame_after']);b=bytes.fromhex(x['frame_after'])
                    self.assertEqual([j for j,(v,w)in enumerate(zip(a,b))if v!=w],[92])
                    self.assertNotEqual(x['whole_ram_sha256'],normal['whole_ram_sha256'])
                for x in group[4:7]:self.assertEqual(x['whole_ram_sha256'],normal['whole_ram_sha256'])
                self.assertNotEqual(group[6]['returned'][3],normal['returned'][3])
                self.assertEqual(group[6]['returned'][15],normal['returned'][15])
                for x in group[4:6]:self.assertEqual(x['flow'][8:],normal['flow'][8:])
                self.assertEqual(group[7]['frame_after'],normal['frame_after']);self.assertNotEqual(group[7]['whole_ram_sha256'],normal['whole_ram_sha256'])


if __name__=='__main__':unittest.main()
