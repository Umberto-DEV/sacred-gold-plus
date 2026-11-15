"""Receipt serialization preserves integer/boolean distinctions at JSON boundaries."""
from pathlib import Path
import importlib.util,unittest,sys,tempfile,contextlib,io,os,gzip,json,copy,struct
from unittest.mock import patch
s=importlib.util.spec_from_file_location('find_attribution',Path(__file__).parents[1]/'tools/attribuisci_fs_find.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class ReceiptWire(unittest.TestCase):
    def test_prepare_mode_rejects_a_cpu_mode_before_any_action(self):
        with tempfile.TemporaryDirectory()as name:
            raw=Path(name)/'raw';out=Path(name)/'report.json'
            argv=['find','--prepare-only','--conditional-capability','--raw-dir',str(raw),'--json',str(out)]
            with patch.object(sys,'argv',argv),patch.object(M.B,'collect_conditional_capability',side_effect=AssertionError('CPU forbidden'))as collector,contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit)as error:M.main()
                self.assertEqual(error.exception.code,2);collector.assert_not_called()
            self.assertFalse(raw.exists());self.assertFalse(out.exists())

    def test_json_footer_arrays_match_python_tuples_without_coercing_scalars(self):
        self.assertEqual(M.wire(dict(footer=[8,4,0])),M.wire(dict(footer=(8,4,0))))
        self.assertNotEqual(M.wire(dict(footer=[8,4,False])),M.wire(dict(footer=(8,4,0))))
        self.assertNotEqual(M.wire(dict(footer=[8,4,0.0])),M.wire(dict(footer=(8,4,0))))


@unittest.skipUnless(all(os.environ.get(k)for k in('SGP_FS_FIND_RAW_DIR','SGP_FS_FIND_ROM_DIR','SGP_FS_FIND_RECIPE_DIR')),'requires private observed Find record/ROM/object')
class ObservedRegisters(unittest.TestCase):
    def test_boolean_observed_entry_is_rejected(self):
        raw=Path(os.environ['SGP_FS_FIND_RAW_DIR'])/'raw-EN/0-normal.json.gz'
        result=json.loads(gzip.decompress(raw.read_bytes()));body=M.L.object_text(Path(os.environ['SGP_FS_FIND_RECIPE_DIR'])/'fs-find-path.o',324,M.L.C.BODIES['path'][2])
        with(Path(os.environ['SGP_FS_FIND_ROM_DIR'])/'r4-EN.nds').open('rb')as fd:
            header=fd.read(0x50);off,n=struct.unpack_from('<2I',header,0x40);fd.seek(off);fnt=fd.read(n)
        self.assertTrue(M.B.require_result(result,body,fnt))
        result['entry'][3]=False
        with self.assertRaises(ValueError):M.B.require_result(result,body,fnt)



REPLAY_ENV=('SGP_FS_FIND_REPORT_DIR','SGP_FS_FIND_RAW_DIR','SGP_FS_FIND_ROM_DIR','SGP_FS_FIND_PARENT_DIR',
    'SGP_FS_FIND_RECIPE_DIR','SGP_FS_READ_CALLER_READ_RECIPE','SGP_FS_READ_CALLER_WAIT_RECIPE',
    'SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k)for k in REPLAY_ENV),'requires private exact Find/parent reports, ROMs and project objects')
class FullReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[]
        for language in('EN','IT'):
            report=json.loads(gzip.decompress((Path(os.environ['SGP_FS_FIND_REPORT_DIR'])/('fs-find-'+language+'.json.gz')).read_bytes()))
            with patch.object(M.B,'run',side_effect=AssertionError('Replay must not run guest CPU')),patch.object(M.H,'run_case',side_effect=AssertionError('Replay must not run parent CPU')):
                fixtures,body,fnt,proof=M.prepare(Path(os.environ['SGP_FS_FIND_ROM_DIR'])/('r4-'+language+'.nds'),language,
                    Path(os.environ['SGP_FS_FIND_PARENT_DIR'])/('read-caller-'+language+'.json.gz'),
                    Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+language),
                    Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+language)/'teams.o',
                    Path(os.environ['SGP_FS_READ_CALLER_READ_RECIPE']),Path(os.environ['SGP_FS_READ_CALLER_WAIT_RECIPE']),
                    Path(os.environ['SGP_FS_FIND_RECIPE_DIR']))
            cls.rows.append((language,report,fixtures,body,fnt,proof))

    def test_exact_source_inputs_and_distinct_full_grid(self):
        for language,r,fixtures,body,fnt,proof in self.rows:
            self.assertEqual(r['source_sha256'],M.source_identities());self.assertEqual(M.wire(r['proof']),M.wire(proof))
            self.assertEqual(M.wire(r['fixtures']),M.wire(fixtures));self.assertIs(r['cpu_executed'],True)
            self.assertIs(r['parent_integration'],False);self.assertIs(r['root_fixture_is_declared'],True)
            self.assertIs(r['probe_only'],False)
            self.assertEqual(M.wire([(x['ordinal'],x['label'])for x in r['cases']]),M.wire([(i,label)for i in range(4)for label in('normal','off','send0','send2','clobber','fill39')]))
            for case in r['cases']:
                self.assertEqual(M.wire(case['result']['fixture']),M.wire(fixtures[case['ordinal']]))
                self.assertTrue(M.B.require_result(case['result'],body,fnt))

    def test_raw_cells_and_counter_off_controls(self):
        for language,r,fixtures,body,fnt,proof in self.rows:
            indexed={(x['ordinal'],x['label']):x['result']for x in r['cases']}
            raw=Path(os.environ['SGP_FS_FIND_RAW_DIR'])/('raw-'+language)
            self.assertEqual(len(list(raw.glob('[0-3]-*.json.gz'))),24)
            self.assertEqual([x['ordinal']for x in r['counters']],[0,1,2,3])
            for cell in range(4):
                normal=indexed[cell,'normal']
                for label in('normal','off','send0','send2','clobber','fill39'):
                    actual=indexed[cell,label];self.assertEqual(json.loads(gzip.decompress((raw/('%d-%s.json.gz'%(cell,label))).read_bytes())),actual)
                self.assertTrue(M.require_off_pair(normal,indexed[cell,'off'],body,fnt))
                rejection=M.counter_rejection(indexed[cell,'send0'],normal,body,fnt)
                self.assertEqual(r['counters'][cell],dict(ordinal=cell,rejection=rejection,policy_disguised=True))
                self.assertEqual(rejection,'Find source-derived returned')
                for label in('send0','send2','clobber'):
                    self.assertEqual(indexed[cell,label]['whole_ram_sha256'],normal['whole_ram_sha256'])
                self.assertNotEqual(indexed[cell,'fill39']['whole_ram_sha256'],normal['whole_ram_sha256'])

    def test_forged_abi_trace_and_whole_memory_are_rejected(self):
        for language,r,fixtures,body,fnt,proof in self.rows:
            baseline=r['cases'][0]['result']
            for kind in('entry_bool','return_wide','flow_bool','false_cmpne','saved_store','provider_id','unowned_ram','missing_read','fault','stop'):
                mutant=copy.deepcopy(baseline)
                if kind=='entry_bool':mutant['entry'][3]=False
                elif kind=='return_wide':mutant['returned'][0]+=2**32
                elif kind=='flow_bool':mutant['flow'][0]['regs'][3]=False
                elif kind=='false_cmpne':
                    index=[i for i,x in enumerate(mutant['flow'])if x['pc']=='0x20d802c'][-1];mutant['flow'][index+1]['regs'][15]=0x8000001F
                elif kind=='saved_store':mutant['stores'][2]['value']^=4
                elif kind=='provider_id':mutant['services'][0]['delivered_hex']='00'*8
                elif kind=='unowned_ram':mutant['whole_ram_sha256']='0'*64
                elif kind=='missing_read':mutant['reads'].pop()
                elif kind=='fault':mutant['fault']=dict(type='forged',message='halted')
                else:mutant['halt_pc']='0x20d8100'
                with self.subTest(language=language,kind=kind):
                    with self.assertRaises(ValueError):M.B.require_result(mutant,body,fnt)

    def test_public_conditional_qualification_is_replayable(self):
        directory=Path(os.environ['SGP_FS_FIND_REPORT_DIR']);report=json.loads(gzip.decompress((directory/'conditional-public.json.gz').read_bytes()))
        raw=json.loads(gzip.decompress((Path(os.environ['SGP_FS_FIND_RAW_DIR'])/'conditional-public-raw/cmpne.json.gz').read_bytes()))
        self.assertEqual(report['rows'],raw);self.assertTrue(M.B.require_conditional(raw))
        self.assertEqual(report['source_sha256'],M.source_identities())
        for field in('skip','execute','hook','float'):
            rows=copy.deepcopy(raw)
            if field=='skip':rows[0]['returned'][15]=0x8000001F
            elif field=='execute':rows[1]['returned'][15]=0x2000001F
            elif field=='hook':rows[0]['flow'].pop(2)
            else:rows[0]['flow'][0]['regs'][0]=float(rows[0]['flow'][0]['regs'][0])
            with self.subTest(field=field):
                with self.assertRaises(ValueError):M.B.require_conditional(rows)


if __name__=='__main__':unittest.main()
