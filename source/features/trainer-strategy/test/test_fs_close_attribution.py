"""Pure replay of exact-ROM Close receipts; no guest CPU is run by tests."""
from pathlib import Path
import copy,gc,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
ENV=('SGP_FS_CLOSE_ROM_DIR','SGP_FS_CLOSE_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact ROMs, objects and Close reports')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=SOURCE/'features/trainer-strategy/tools/attribuisci_fs_close.py'
        s=importlib.util.spec_from_file_location('fs_close_replay',p);cls.z=z=importlib.util.module_from_spec(s);s.loader.exec_module(z)
        cls.reports,cls.data,cls.q={},{},{}
        for language in os.environ.get('SGP_FS_CLOSE_LANGUAGES','EN,IT').split(','):
            rom=Path(os.environ[ENV[0]])/('r4-'+language+'.nds');model=z.P.G.S.SHARED.read_current(rom,language)
            with rom.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as raw:
                cls.q[language],_=z.qualify(model,raw,language,
                    Path(os.environ[ENV[2]])/('public-build-'+language),Path(os.environ[ENV[3]])/('build-'+language)/'teams.o')
                cls.data[language]=z.H.H.H.O.resources(model,raw,language)
            p=Path(os.environ[ENV[1]])/('fs-close-'+language+'.json.gz')
            cls.reports[language]=json.loads(gzip.decompress(p.read_bytes()));del model;gc.collect()

    def base(self):
        language=next(iter(self.reports));return language,copy.deepcopy(self.reports[language]['positives'][0])

    def require(self,language,r):self.z.require_case(r,self.data[language],self.q[language])



    def test_all_positive_guard_and_backend_control_receipts(self):
        for language,report in self.reports.items():
            self.assertEqual(report['source_sha256'],self.z.source_identities())
            self.assertEqual(len(report['recipes']),3);self.assertEqual(len(report['namespace_bindings']),2)
            self.assertEqual(report['conditional_policy']['close_false_EQ_hooks'],1)
            self.assertEqual(sum(len(report[k])for k in('positives','guards','volatile_controls','observer_off','counters')),10)
            for r in report['positives']+report['guards']+report['volatile_controls']:self.require(language,r)

    def test_residual_lr_r1_flags_reach_real_pp_checkpoint(self):
        for key in('endLR','returnLR','endR1','endFlags','sendThumb','savedR4'):
            lang,r=self.base();out=r['fs_close'];p=r['pp_reader']
            if key=='endLR':p['end'][14]=0x2007409
            elif key=='returnLR':out['returned'][14]=0x2007409
            elif key=='endR1':p['end'][1]=self.z.DEST
            elif key=='endFlags':p['end'][15]=0xA000003F
            elif key=='sendThumb':p['models'][-1]['returned'][15]|=32
            else:out['returned'][4]=self.z.FILE
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_two_send_roles_and_complete_close_lifetime(self):
        for key in('command','openrole','sp','model','cursor','ledger','argument'):
            lang,r=self.base();event=r['pp_reader']['models'][-1]
            if key=='command':event['command']=7
            elif key=='openrole':event['entry'][1]=6
            elif key=='sp':event['sp']=event['return_sp']=self.z.H.SP
            elif key=='model':event['name']='FS_CloseFile'
            elif key=='cursor':event['cursor_before']=0
            elif key=='ledger':r['fs_close']['ledger_after']['open']=True
            else:
                a=bytearray.fromhex(r['fs_close']['file_after']);a[52]^=1;r['fs_close']['file_after']=a.hex()
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_dead_open_pair_three_cleanup_words_and_idempotent_store(self):
        for key in('oldpair','missingcommand','before','oldphase','legacy','guard','count'):
            lang,r=self.base();out=r['fs_close'];p=r['pp_reader']
            if key=='oldpair':out['stores'][0]['value']=0x210F198
            elif key=='missingcommand':out['stores']=[e for e in out['stores']if e['pc']!='0x20d82e4']
            elif key=='before':out['frame_before']=r['fs_fast']['frame_after']
            elif key=='oldphase':p['stack240_after']=r['fs_fast']['frame_after']
            elif key=='legacy':p['stack152_after']='00'*152
            elif key=='guard':r['guard8_global_after']='ff'*8
            else:p['instructions']=197
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_zero_r0_does_not_make_false_pop_eq_execute(self):
        for lang,report in self.reports.items():
            r=report['positives'][0];flow={e['pc']:e['regs']for e in r['fs_close']['flow']}
            self.assertEqual(flow['0x20d82d8'][0],0);self.assertFalse(flow['0x20d82d8'][15]&(1<<30))
            self.assertEqual(flow['0x20d82d8'],flow['0x20d82dc'])
            for value in(True,0,3):
                bad=copy.deepcopy(r);bad['close_value']=value
                with self.subTest(value=value),self.assertRaises(ValueError):self.require(lang,bad)
            control=next(x for x in report['volatile_controls']if x['close_value']==2)
            self.assertEqual(control['pp_reader']['models'][1]['result_r0'],1)
            self.assertEqual(control['pp_reader']['models'][-1]['result_r0'],2)
            self.assertEqual(control['fs_close']['returned'][0],1)

    def test_off_and_arc_counter_full_replay(self):
        for lang,report in self.reports.items():
            data,q=self.data[lang],self.q[lang]
            for e in report['observer_off']:
                off=e['result'];on=next(r for r in report['positives']if(r['plus'],r['seed'])==(off['plus'],off['seed']))
                self.assertEqual(self.z.require_off_pair(on,off,data),e['proof'])
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678))
            self.z.require_counter(report['counters'][0],normal,data,q)
            self.assertEqual(report['counters'][0]['result']['names'],normal['names'])
            self.assertEqual(report['counters'][0]['result']['pp_flow'],normal['pp_flow'])

    def test_arc_counter_scope_and_same_output_cannot_hide_cleanup(self):
        for lang,report in self.reports.items():
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678))
            for key in('shadow','prestate','fast','model','frame','name','final','tag'):
                bad=copy.deepcopy(report['counters'][0]);r=bad['result']
                if key=='shadow':r['fs_close']['shadows'][0]['after'][1]^=1
                elif key=='prestate':r['fs_close']['frame_before']='00'*240
                elif key=='fast':r['fs_fast']['returned'][1]=0
                elif key=='model':r['pp_reader']['models'][-1]['open_after']=True
                elif key=='frame':r['pp_reader']['stack152_after']=normal['pp_reader']['stack152_after']
                elif key=='name':r['names'][1]['transitions'][0]['ram_sha256']='0'*64
                elif key=='final':r['raw_ram_sha256']='0'*64
                else:bad['tag_disguised']=False
                with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])


if __name__=='__main__':unittest.main()
