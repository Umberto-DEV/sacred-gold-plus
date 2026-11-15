"""Optional exact-ROM replay: raw evidence only, no guest CPU or compiler."""
from pathlib import Path
import ast,copy,gc,gzip,importlib.util,json,mmap,os,unittest
s=importlib.util.spec_from_file_location('find_caller_replay',Path(__file__).parents[1]/'tools/attribuisci_fs_find_chiamante.py')
Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)
ENV=('SGP_FS_FIND_CALLER_REPORT_DIR','SGP_FS_FIND_CALLER_RAW_DIR','SGP_FS_FIND_CALLER_ROM_DIR',
     'SGP_FS_FIND_CALLER_READ_RECIPE','SGP_FS_FIND_CALLER_WAIT_RECIPE','SGP_FS_FIND_CALLER_FIND_RECIPE',
     'SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')
load=lambda p:json.loads(gzip.decompress(p.read_bytes()))


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact Find caller reports/ROMs/objects/recipes')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[]
        for language in('EN','IT'):
            report=load(Path(os.environ[ENV[0]])/('find-caller-'+language+'.json.gz'))
            rom=Path(os.environ[ENV[2]])/('r4-'+language+'.nds');model=Z.P.G.S.SHARED.read_current(rom,language)
            with rom.open('rb')as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ)as raw:
                q,proof=Z.qualify(model,raw,language,Path(os.environ[ENV[6]])/('public-build-'+language),
                    Path(os.environ[ENV[7]])/('build-'+language)/'teams.o',
                    Path(os.environ[ENV[3]]),Path(os.environ[ENV[4]]),Path(os.environ[ENV[5]]))
                data=Z.resources(model,raw,language)
            cls.rows.append((language,report,data,q,proof));del model;gc.collect()

    def require_capture_sources(self,report):
        current=Z.source_identities();captured=report['source_sha256']
        if current==captured:return
        key=str(Path(Z.__file__).resolve().relative_to(Z.P.SOURCE))
        self.assertEqual(set(current),set(captured));self.assertEqual([k for k in current if current[k]!=captured[k]],[key])
        # Historical captures may be rechecked after this oracle-only correction.
        # Require their exact producer source, not a rewritten receipt.
        path=os.environ.get('SGP_FS_FIND_CALLER_CAPTURE_SOURCE')
        self.assertTrue(path,'historical capture needs its exact retained runtime source')
        old=Path(path).read_bytes();new=Path(Z.__file__).read_bytes()
        self.assertEqual(Z.sha(old),captured[key]);self.assertEqual(Z.sha(new),current[key])
        def split(blob):
            tree=ast.parse(blob);oracle=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='require_find']
            self.assertEqual(len(oracle),1)
            tree.body.remove(oracle[0]);return ast.dump(tree,include_attributes=False)
        self.assertEqual(split(old),split(new),'only require_find oracle may differ; producer and recipes must be unchanged')

    def test_identity_distinct_grid_and_all_oracles_are_receipt_neutral(self):
        bindings=copy.deepcopy(Z.BINDINGS)
        for language,r,data,q,proof in self.rows:
            self.require_capture_sources(r);self.assertEqual(r['recipes'],Z.RECIPES)
            self.assertEqual(r['namespace_bindings'],bindings);self.assertEqual(Z.N.wire(r['proof']),Z.N.wire(proof))
            self.assertIs(r['cpu_executed'],True);self.assertIs(r['probe_only'],False)
            self.assertEqual([(p['plus'],p['seed'])for p in r['positives']],[(p,s)for p in(0,1)for s in(0x12345678,0x12345679)])
            self.assertEqual([x['result']['plus']for x in r['observer_off']],[0,1])
            self.assertEqual((len(r['guards']),len(r['volatile_controls']),len(r['counters'])),(1,3,2))
            self.assertEqual([(x['pp_clobber'],x['close_value'],x['read_send_value'])for x in r['volatile_controls']],
                             [(True,1,1),(False,2,1),(False,1,0)])
            normal=r['positives'][2]
            for p in r['positives']+r['guards']+r['volatile_controls']:self.assertTrue(Z.require_case(p,data,q))
            for off in r['observer_off']:
                self.assertEqual(off['proof'],Z.require_off_pair(r['positives'][2*off['result']['plus']],off['result'],data,q))
            self.assertTrue(Z.require_counter(r['counters'][0],normal,data,q))
            self.assertEqual(r['counters'][1],Z.find2_counter(r['counters'][1]['result'],normal,data,q))
            self.assertEqual(Z.BINDINGS,bindings,'semantic replay must never append source namespace binding receipts')

    def test_all_thirteen_raw_records_precede_checks_and_match_report(self):
        for language,r,data,q,proof in self.rows:
            expected=[*r['positives'],r['matched_baseline']['result'],*(x['result']for x in r['observer_off']),
                      *r['guards'],*r['volatile_controls'],*(x['result']for x in r['counters'])]
            paths=sorted((Path(os.environ[ENV[1]])/('raw-'+language)).glob('[0-9][0-9]-*.json.gz'))
            self.assertEqual(len(paths),13)
            for path,want in zip(paths,expected):
                raw=load(path);self.assertIs(raw['completed'],True);self.assertEqual(raw['result'],want)

    def test_final_full_ram_pair_is_independently_compared_without_masks(self):
        for language,r,data,q,proof in self.rows:
            raw=Path(os.environ[ENV[1]])/('raw-'+language)
            first=gzip.decompress((raw/'matched-model-final.bin.gz').read_bytes())
            second=gzip.decompress((raw/'positive-1-12345678-final.bin.gz').read_bytes())
            self.assertEqual(len(first),0x400000);self.assertEqual(len(second),0x400000)
            paired=Z.require_baseline(r['positives'][2],r['matched_baseline']['result'],data,q,first,second)
            self.assertEqual(paired,r['matched_baseline']['proof']);self.assertEqual(first,second)
            changed=bytearray(second);changed[100]^=1
            with self.assertRaises(ValueError):Z.require_baseline(r['positives'][2],r['matched_baseline']['result'],data,q,first,bytes(changed))

    def test_forged_actual_find_and_root_witnesses_are_rejected(self):
        for language,r,data,q,proof in self.rows:
            base=r['positives'][2]
            for kind in('return_bool','return','flow','read','store','model','page','outside','guard','pre0','pre1','pre2','root_after','policy_bool','clobber_int','service_bool','model_bool','index_bool','store_bool','read_bool'):
                mutant=copy.deepcopy(base)
                if kind=='return_bool':mutant['find']['returned'][0]=True
                elif kind=='return':mutant['find']['returned'][0]=2
                elif kind=='flow':mutant['find']['flow'][10]['regs'][12]^=4
                elif kind=='read':mutant['find']['reads'][0]['address']+=1
                elif kind=='store':mutant['find']['stores'][0]['value']^=4
                elif kind=='model':mutant['pp_reader']['models'][0]['entry'][2]=Z.ID
                elif kind=='page':
                    page=bytearray.fromhex(mutant['find']['page_after']);page[100]^=1;mutant['find']['page_after']=page.hex()
                elif kind=='outside':mutant['find']['outside_unchanged']=False
                elif kind=='guard':mutant['pp_reader']['stack_guard_after']='01'+mutant['pp_reader']['stack_guard_after'][2:]
                elif kind.startswith('pre'):mutant['root_fences'][int(kind[-1])]['regs_before'][0]^=4
                elif kind=='root_after':mutant['root_fences'][1]['root_after']=bytes(12).hex()
                elif kind=='policy_bool':mutant['find']['policy']['send']=True
                elif kind=='clobber_int':mutant['find']['policy']['clobber']=0
                elif kind=='service_bool':mutant['find']['services'][0]['result']=True
                elif kind=='model_bool':mutant['pp_reader']['models'][0]['result_r0']=True
                elif kind=='index_bool':mutant['find']['model_index']=False
                elif kind=='store_bool':next(e for e in mutant['find']['stores']if e['value']==0)['value']=False
                else:mutant['find']['reads'][0]['bytes']=True
                with self.subTest(language=language,kind=kind):
                    with self.assertRaises(ValueError):Z.require_case(mutant,data,q)


if __name__=='__main__':unittest.main()
