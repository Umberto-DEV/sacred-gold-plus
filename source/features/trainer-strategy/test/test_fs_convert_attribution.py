"""Pure replay of exact-ROM Convert receipts; no guest CPU is run by tests."""
from pathlib import Path
import copy,gc,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
ENV=('SGP_FS_CONVERT_ROM_DIR','SGP_FS_CONVERT_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact ROMs, objects and Convert reports')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=SOURCE/'features/trainer-strategy/tools/attribuisci_fs_convert.py'
        s=importlib.util.spec_from_file_location('fs_convert_replay',p);cls.z=z=importlib.util.module_from_spec(s);s.loader.exec_module(z)
        cls.reports,cls.data,cls.q={},{},{}
        for language in os.environ.get('SGP_FS_CONVERT_LANGUAGES','EN,IT').split(','):
            rom=Path(os.environ[ENV[0]])/('r4-'+language+'.nds');model=z.P.G.S.SHARED.read_current(rom,language)
            with rom.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as raw:
                cls.q[language],_=z.qualify(model,raw,language,
                    Path(os.environ[ENV[2]])/('public-build-'+language),Path(os.environ[ENV[3]])/('build-'+language)/'teams.o')
                cls.data[language]=z.H.O.resources(model,raw,language)
            p=Path(os.environ[ENV[1]])/('fs-convert-'+language+'.json.gz')
            cls.reports[language]=json.loads(gzip.decompress(p.read_bytes()));del model;gc.collect()

    def base(self):
        language=next(iter(self.reports));return language,copy.deepcopy(self.reports[language]['positives'][0])

    def require(self,language,r):self.z.require_case(r,self.data[language],self.q[language])

    def test_all_positive_guard_and_model_policy_receipts(self):
        for language,report in self.reports.items():
            self.assertEqual(report['source_sha256'],self.z.source_identities());self.assertEqual(len(report['recipes']),11)
            self.assertIs(report['conditional_policy']['false_EQ_hook'],True)
            self.assertEqual(sum(len(report[k])for k in('positives','guards','volatile_controls','observer_off','counters')),10)
            for r in report['positives']+report['guards']+report['volatile_controls']:self.require(language,r)

    def test_two_init_invocations_and_real_arm_return(self):
        for key in('inner_lr','thumb','r3','find_pointer','outer_alias','initmissing'):
            lang,r=self.base();out=r['convert'];inner=out['inner_init']
            if key=='inner_lr':inner['entry'][14]=0x200734B
            elif key=='thumb':inner['returned'][15]|=32
            elif key=='r3':out['returned'][3]=0xA5000003
            elif key=='find_pointer':r['pp_reader']['models'][0]['args'][2]=self.z.DIR
            elif key=='outer_alias':inner['entry'][0]=self.z.FILE
            else:inner['flow']=inner['flow'][:-1]
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_directory_native_stores_and_preserved_fields(self):
        for key in('push','innerstore','padding','id','hostledger'):
            lang,r=self.base();out=r['convert'];inner=out['inner_init']
            if key=='push':out['stores'][0]['value']^=1
            elif key=='innerstore':inner['stores']=inner['stores'][:-1]
            elif key=='padding':
                a=bytearray.fromhex(inner['after']);a[36]^=1;inner['after']=a.hex()
            elif key=='id':r['pp_reader']['models'][0]['destination']=self.z.DIR
            else:out['ledger_after']['file']=self.z.DIR
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_frame_guard_and_global8_are_coupled(self):
        for key in('frame','legacy','guard','global8','range','peak','count'):
            lang,r=self.base();p=r['pp_reader']
            if key=='frame':p['stack240_after']='00'*240
            elif key=='legacy':p['stack152_after']='00'*152
            elif key=='guard':p['stack_guard_after']='ff'*56
            elif key=='global8':r['guard8_global_after']='ff'*8
            elif key=='range':p['stack_guard_range'][0]+=8
            elif key=='peak':p['max_stack']=152
            else:p['instructions']=143
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_truthy_two_and_false_eq_has_no_effect(self):
        for lang,report in self.reports.items():
            r=next(r for r in report['volatile_controls']if r['find_value']==2)
            self.assertEqual(r['pp_reader']['models'][0]['result_r0'],2)
            self.assertEqual(r['convert']['returned'][0],1)
            f={e['pc']:e['regs']for e in r['convert']['flow']}
            self.assertEqual(f['0x20d81b4'],f['0x20d81b8'])
            for value in(True,0,3):
                bad=copy.deepcopy(r);bad['find_value']=value
                with self.subTest(value=value),self.assertRaises(ValueError):self.require(lang,bad)

    def test_off_and_counter_full_replay(self):
        for lang,report in self.reports.items():
            data,q=self.data[lang],self.q[lang]
            for e in report['observer_off']:
                off=e['result'];on=next(r for r in report['positives']if(r['plus'],r['seed'])==(off['plus'],off['seed']))
                self.assertEqual(self.z.require_off_pair(on,off,data),e['proof'])
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678))
            self.z.require_counter(report['counters'][0],normal,data,q)

    def test_counter_scope_and_prestate_mutants_rejected(self):
        for lang,report in self.reports.items():
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678))
            for key in('shadow','outer','before','finddir','final','names','tag'):
                bad=copy.deepcopy(report['counters'][0]);r=bad['result']
                if key=='shadow':r['convert']['inner_init']['shadows'][0]['after'][2]^=1
                elif key=='outer':r['fs_init']['returned'][1]=0
                elif key=='before':r['pp_reader']['stack240_before']='00'*240
                elif key=='finddir':r['pp_reader']['models'][0]['dir_before_hex']=normal['pp_reader']['models'][0]['dir_before_hex']
                elif key=='final':r['raw_ram_sha256']='0'*64
                elif key=='names':r['names'][0]['transitions'][0]['ram_sha256']='0'*64
                else:bad['tag_disguised']=False
                with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])


if __name__=='__main__':unittest.main()
