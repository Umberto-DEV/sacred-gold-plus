"""Pure replay of exact-ROM Fast receipts; no guest CPU is run by tests."""
from pathlib import Path
import copy,gc,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
ENV=('SGP_FS_FAST_ROM_DIR','SGP_FS_FAST_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact ROMs, objects and Fast reports')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=SOURCE/'features/trainer-strategy/tools/attribuisci_fs_fast.py'
        s=importlib.util.spec_from_file_location('fs_fast_replay',p);cls.z=z=importlib.util.module_from_spec(s);s.loader.exec_module(z)
        cls.reports,cls.data,cls.q={},{},{}
        for language in os.environ.get('SGP_FS_FAST_LANGUAGES','EN,IT').split(','):
            rom=Path(os.environ[ENV[0]])/('r4-'+language+'.nds');model=z.P.G.S.SHARED.read_current(rom,language)
            with rom.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as raw:
                cls.q[language],_=z.qualify(model,raw,language,
                    Path(os.environ[ENV[2]])/('public-build-'+language),Path(os.environ[ENV[3]])/('build-'+language)/'teams.o')
                cls.data[language]=z.H.H.O.resources(model,raw,language)
            p=Path(os.environ[ENV[1]])/('fs-fast-'+language+'.json.gz')
            cls.reports[language]=json.loads(gzip.decompress(p.read_bytes()));del model;gc.collect()

    def base(self):
        language=next(iter(self.reports));return language,copy.deepcopy(self.reports[language]['positives'][0])

    def require(self,language,r):self.z.require_case(r,self.data[language],self.q[language])


    def test_all_positive_guard_and_model_policy_receipts(self):
        for language,report in self.reports.items():
            self.assertEqual(report['source_sha256'],self.z.source_identities())
            self.assertEqual(len(report['recipes']),5);self.assertEqual(len(report['namespace_bindings']),4)
            self.assertEqual(report['conditional_policy']['fast_false_EQ_hooks'],8)
            self.assertEqual(sum(len(report[k])for k in('positives','guards','volatile_controls','observer_off','counters')),10)
            for r in report['positives']+report['guards']+report['volatile_controls']:self.require(language,r)

    def test_spilled_aggregate_send_command_and_restored_lr(self):
        for key in('spill','load','cmd','fid','sp','lr','volatile','field'):
            lang,r=self.base();out=r['fs_fast'];send=r['pp_reader']['models'][1]
            if key=='spill':out['stores'][0]['value']^=1
            elif key=='load':out['reads'][0]['address']=self.z.ID
            elif key=='cmd':send['args'][1]=14
            elif key=='fid':send['entry'][2]=self.z.ID
            elif key=='sp':send['sp']=send['return_sp']=self.z.ID
            elif key=='lr':out['returned'][14]=0x20D8244
            elif key=='volatile':out['returned'][1]=0xA5000001
            else:send['file_before_hex']='00'*72
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_dead_directory_reuse_and_live_file_preserved_bytes(self):
        for key in('lifetime','before','after','filepadding','legacy','guard','global8','count'):
            lang,r=self.base();out=r['fs_fast'];p=r['pp_reader']
            if key=='lifetime':p['stack240_after']=r['convert']['frame_after']
            elif key=='before':out['frame_before']=p['stack240_before']
            elif key=='after':out['frame_after']='00'*240
            elif key=='filepadding':
                a=bytearray.fromhex(out['file_after']);a[40]^=1;out['file_after']=a.hex()
            elif key=='legacy':p['stack_frame_hex']='00'*136
            elif key=='guard':p['stack_guard_after']='ff'*56
            elif key=='global8':r['guard8_global_after']='ff'*8
            else:p['instructions']=169
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_eight_false_eq_hooks_do_not_prove_effects(self):
        z=self.z
        for lang,report in self.reports.items():
            r=report['positives'][0];flow={e['pc']:e['regs']for e in r['fs_fast']['flow']}
            for pc in(0x20D821C,0x20D8220,0x20D8224,0x20D8228,0x20D8248,0x20D824C,0x20D8250,0x20D8254):
                self.assertEqual(flow[hex(pc)],flow[hex(pc+4)])
                bad=copy.deepcopy(r);next(e for e in bad['fs_fast']['flow']if e['pc']==hex(pc))['regs'][13]+=8
                with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):self.require(lang,bad)

    def test_send_truthy_two_normalized_and_r1_status_is_native(self):
        for lang,report in self.reports.items():
            r=next(r for r in report['volatile_controls']if r['send_value']==2)
            self.assertEqual(r['pp_reader']['models'][1]['result_r0'],2)
            self.assertEqual(r['fs_fast']['returned'][:2],[1,16])
            for value in(True,0,3):
                bad=copy.deepcopy(r);bad['send_value']=value
                with self.subTest(value=value),self.assertRaises(ValueError):self.require(lang,bad)
            r=next(r for r in report['volatile_controls']if r['pp_clobber'])
            self.assertEqual(r['fs_fast']['returned'][1:4],[16,0xA5000002,0xA5000003])

    def test_off_and_counter_full_replay(self):
        for lang,report in self.reports.items():
            data,q=self.data[lang],self.q[lang]
            for e in report['observer_off']:
                off=e['result'];on=next(r for r in report['positives']if(r['plus'],r['seed'])==(off['plus'],off['seed']))
                self.assertEqual(self.z.require_off_pair(on,off,data),e['proof'])
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678))
            self.z.require_counter(report['counters'][0],normal,data,q)
            self.assertEqual(report['counters'][0]['result']['names'],normal['names'])

    def test_status_counter_mutants_rejected_without_extra_name_projection(self):
        for lang,report in self.reports.items():
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678))
            for key in('shadow','prestate','outer','model','frame','name','final','tag'):
                bad=copy.deepcopy(report['counters'][0]);r=bad['result']
                if key=='shadow':r['fs_fast']['shadows'][0]['after'][0]=0
                elif key=='prestate':r['pp_reader']['stack240_before']='00'*240
                elif key=='outer':r['convert']['inner_init']['returned'][1]=0
                elif key=='model':r['pp_reader']['models'][1]['open_after']=False
                elif key=='frame':r['pp_reader']['stack152_after']=normal['pp_reader']['stack152_after']
                elif key=='name':r['names'][1]['transitions'][0]['ram_sha256']='0'*64
                elif key=='final':r['raw_ram_sha256']='0'*64
                else:bad['tag_disguised']=False
                with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])


if __name__=='__main__':unittest.main()
