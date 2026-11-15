"""Private exact-ROM replay, without re-running any guest CPU or compiler."""
from pathlib import Path
import copy,gzip,hashlib,importlib.util,json,mmap,os,unittest
s=importlib.util.spec_from_file_location('read_caller_replay',Path(__file__).parents[1]/'tools/attribuisci_fs_read_chiamante.py')
Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)
ENV=('SGP_FS_READ_CALLER_REPORT_DIR','SGP_FS_READ_CALLER_RAW_DIR','SGP_FS_READ_CALLER_ROM_DIR',
     'SGP_FS_READ_CALLER_READ_RECIPE','SGP_FS_READ_CALLER_WAIT_RECIPE','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')
load=lambda p:json.loads(gzip.decompress(p.read_bytes()))


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact caller reports/ROMs/objects/recipes')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[]
        for language in('EN','IT'):
            report=load(Path(os.environ[ENV[0]])/('read-caller-'+language+'.json.gz'))
            rom=Path(os.environ[ENV[2]])/('r4-'+language+'.nds');model=Z.P.G.S.SHARED.read_current(rom,language)
            with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
                q,proof=Z.qualify(model,raw,language,Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+language),
                    Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+language)/'teams.o',
                    Path(os.environ[ENV[3]]),Path(os.environ[ENV[4]]))
                data=Z.H.resources(model,raw,language)
            cls.rows.append((language,report,data,q,proof))
            del model

    def test_identity_and_complete_distinct_grid(self):
        for language,r,data,q,proof in self.rows:
            self.assertEqual(r['source_sha256'],Z.source_identities());self.assertEqual(r['recipes'],Z.RECIPES)
            self.assertEqual(r['namespace_bindings'],Z.BINDINGS);self.assertEqual(r['proof'],json.loads(json.dumps(proof)))
            self.assertIs(r['cpu_executed'],True);self.assertIs(r['probe_only'],False)
            self.assertEqual([(p['plus'],p['seed'])for p in r['positives']],[(p,s)for p in(0,1)for s in(0x12345678,0x12345679)])
            self.assertEqual([p['result']['plus']for p in r['observer_off']],[0,1])
            self.assertEqual((len(r['guards']),len(r['volatile_controls']),len(r['counters'])),(1,3,1))
            self.assertEqual([(x['pp_clobber'],x['close_value'],x['read_send_value'])for x in r['volatile_controls']],
                             [(True,1,1),(False,2,1),(False,1,0)])
            normal=r['positives'][2]
            for p in r['positives']+r['guards']+r['volatile_controls']:self.assertTrue(Z.require_case(p,data,q))
            for off in r['observer_off']:
                baseline=r['positives'][2*off['result']['plus']]
                self.assertEqual(off['proof'],Z.require_off_pair(baseline,off['result'],data,q))
            self.assertTrue(Z.require_counter(r['counters'][0],normal,data,q))

    def test_raw_records_precede_checks_and_match_every_cell(self):
        for language,r,data,q,proof in self.rows:
            expected=[*r['positives'],*(x['result']for x in r['observer_off']),*r['guards'],*r['volatile_controls'],r['counters'][0]['result']]
            paths=sorted((Path(os.environ[ENV[1]])/('raw-'+language)).glob('[0-9][0-9]-*.json.gz'))
            self.assertEqual(len(paths),11)
            for path,want in zip(paths,expected):
                raw=load(path);self.assertIs(raw['completed'],True);self.assertEqual(raw['result'],want)

    def test_first_read_full_ram_pair_independently_matches_witness(self):
        for language,r,data,q,proof in self.rows:
            raw=Path(os.environ[ENV[1]])/('raw-'+language);label='positive-0-12345678'
            before=gzip.decompress((raw/(label+'-first-read-before.bin.gz')).read_bytes())
            after=gzip.decompress((raw/(label+'-first-read-after.bin.gz')).read_bytes());self.assertEqual(len(before),0x400000)
            self.assertEqual(len(after),len(before));call=r['positives'][0]['read_calls'][0]
            self.assertEqual(Z.sha(before),call['before_ram_sha256']);self.assertEqual(Z.sha(after),call['after_ram_sha256'])
            a=Z.PAGE-0x2000000;b=a+4096
            self.assertEqual(before[:a]+before[b:],after[:a]+after[b:])
            self.assertEqual(Z.sha(before[:a]+before[b:]),call['outside_before_sha256'])
            self.assertEqual(before[a:b].hex(),call['page_before']);self.assertEqual(after[a:b].hex(),call['page_after'])
            Z.A.require_page(before[a:b],after[a:b],bytes.fromhex(call['frame_after']),call['entry'][1],bytes.fromhex(call['fixture']['payload']))

    def test_forged_positive_evidence_is_rejected(self):
        for language,r,data,q,proof in self.rows:
            base=r['positives'][2]
            for kind in('register_bool','native_flow','completion','page','outside','store','duplicate_model','duplicate_cell'):
                mutant=copy.deepcopy(base)
                if kind=='register_bool':mutant['read_calls'][0]['returned'][3]=False
                elif kind=='native_flow':mutant['read_calls'][0]['flow'][9]['regs'][12]^=4
                elif kind=='completion':mutant['read_calls'][0]['completion']=[]
                elif kind=='page':
                    page=bytearray.fromhex(mutant['read_calls'][0]['page_after']);page[100]^=1;mutant['read_calls'][0]['page_after']=page.hex()
                elif kind=='outside':mutant['read_calls'][0]['outside_unchanged']=False
                elif kind=='store':mutant['pp_reader']['native_writes'][-1]['value']^=1
                elif kind=='duplicate_model':mutant['pp_reader']['models'][3]=copy.deepcopy(mutant['pp_reader']['models'][2])
                else:mutant['read_calls'][1]=copy.deepcopy(mutant['read_calls'][0])
                with self.subTest(language=language,kind=kind):
                    with self.assertRaises(ValueError):Z.require_case(mutant,data,q)


if __name__=='__main__':unittest.main()
