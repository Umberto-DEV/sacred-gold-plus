"""Pure replay of exact-ROM Seek receipts; no guest CPU is run by tests."""
from pathlib import Path
import copy,gc,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
ENV=('SGP_FS_SEEK_ROM_DIR','SGP_FS_SEEK_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact ROMs, objects and Seek reports')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=SOURCE/'features/trainer-strategy/tools/attribuisci_fs_seek.py'
        s=importlib.util.spec_from_file_location('fs_seek_replay',p);cls.z=z=importlib.util.module_from_spec(s);s.loader.exec_module(z)
        cls.reports,cls.data,cls.q={},{},{}
        for language in os.environ.get('SGP_FS_SEEK_LANGUAGES','EN,IT').split(','):
            rom=Path(os.environ[ENV[0]])/('r4-'+language+'.nds');model=z.P.G.S.SHARED.read_current(rom,language)
            with rom.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as raw:
                cls.q[language],_=z.qualify(model,raw,language,
                    Path(os.environ[ENV[2]])/('public-build-'+language),Path(os.environ[ENV[3]])/('build-'+language)/'teams.o')
                cls.data[language]=z.resources(model,raw,language)
            p=Path(os.environ[ENV[1]])/('fs-seek-'+language+'.json.gz')
            cls.reports[language]=json.loads(gzip.decompress(p.read_bytes()));del model;gc.collect()

    def base(self):
        language=next(iter(self.reports));return language,copy.deepcopy(self.reports[language]['positives'][0])

    def require(self,language,r):self.z.require_case(r,self.data[language],self.q[language])




    def test_all_positive_guard_and_backend_control_receipts(self):
        for lang,report in self.reports.items():
            self.assertEqual(report['source_sha256'],self.z.source_identities())
            self.assertEqual(len(report['recipes']),7);self.assertEqual(len(report['namespace_bindings']),5)
            self.assertEqual(report['conditional_policy']['seek_false_MOV_hooks_per_SET'],2)
            self.assertEqual(sum(len(report[k])for k in('positives','guards','volatile_controls','observer_off','counters')),10)
            for r in report['positives']+report['guards']+report['volatile_controls']:self.require(lang,r)

    def test_native_seek_uses_physical_geometry_and_preserves_abi(self):
        for key in('origin','relative','bottom','saved','sp','width','Q','flags'):
            lang,r=self.base();call=r['seek'][0]
            if key=='origin':call['entry'][2]=1
            elif key=='relative':call['returned'][1]=12
            elif key=='bottom':call['returned'][2]=11356
            elif key=='saved':call['returned'][4]^=1
            elif key=='sp':call['entry'][13]-=8
            elif key=='width':call['entry'][15]|=1<<32
            elif key=='Q':call['entry'][15]|=1<<27
            else:call['flow'][1]['regs'][15]^=1<<30
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_complete_frame_timeline_binds_projected_and_native_writes(self):
        for key in('geometry','nativeStore','nativeRead','projection','modelCount','frame','cursor','outside'):
            lang,r=self.base();call=r['seek'][0]
            if key=='geometry':r['fs_projection']['geometry']['top']=0
            elif key=='nativeStore':call['stores']=[]
            elif key=='nativeRead':call['reads'][0]['address']=self.z.FILE+44
            elif key=='projection':r['fs_projection']['events']=r['fs_projection']['events'][:-1]
            elif key=='modelCount':r['pp_reader']['models'].append(r['pp_reader']['models'][0])
            elif key=='frame':call['frame_after']=call['frame_before']
            elif key=='cursor':r['pp_reader']['models'][2]['cursor_before']=0
            else:
                for field in('frame_before','frame_after'):
                    a=bytearray.fromhex(r['fs_projection']['events'][0][field]);a[0]^=1;r['fs_projection']['events'][0][field]=a.hex()
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_projection_width_and_actual_read_close_bridge_cannot_be_resealed(self):
        for key in('wide','negative','bool','bridgeFlags','bridgeR12'):
            lang,r=self.base();event=r['fs_projection']['events'][-1];copy_event=r['pp_reader']['models'][-2]['property_projection']
            if key in('wide','negative','bool','bridgeFlags'):
                value={'wide':0x10000003F,'negative':-1,'bool':True,'bridgeFlags':0xF000003F}[key]
                event['regs'][15]=copy_event['regs'][15]=value
            else:event['regs'][12]^=1;copy_event['regs'][12]=event['regs'][12]
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(lang,r)

    def test_two_false_moves_do_not_prove_clamp_effects_or_all27_starts_seen(self):
        for lang,report in self.reports.items():
            r=report['positives'][0]
            self.assertEqual(len(r['pp_reader']['observed_pcs']),201)
            for call in r['seek']:
                self.assertEqual(len(call['flow']),14);flow={e['pc']:e['regs']for e in call['flow']}
                self.assertEqual(flow['0x20d842c'],flow['0x20d8430']);self.assertEqual(flow['0x20d8438'],flow['0x20d843c'])
            bad=copy.deepcopy(r);bad['pp_reader']['observed_pcs'].append(0x20D83EC)
            with self.assertRaises(ValueError):self.require(lang,bad)

    def test_clobber_and_close2_keep_seek_native_return_policy(self):
        for lang,report in self.reports.items():
            r=next(r for r in report['volatile_controls']if r['pp_clobber'])
            for call in r['seek']:
                self.assertEqual(call['returned'][3],0xA5000003);self.assertEqual(call['returned'][12],0xA500000C)
                self.assertEqual(call['returned'][15],0x8000003F)
            r=next(r for r in report['volatile_controls']if r['close_value']==2)
            self.assertEqual(r['pp_reader']['models'][1]['result_r0'],1);self.assertEqual(r['pp_reader']['models'][-1]['result_r0'],2)
            self.assertTrue(all(call['returned'][0]==1 for call in r['seek']))

    def test_off_and_first_cur_counter_full_replay(self):
        for lang,report in self.reports.items():
            data,q=self.data[lang],self.q[lang]
            for e in report['observer_off']:
                off=e['result'];on=next(r for r in report['positives']if(r['plus'],r['seed'])==(off['plus'],off['seed']))
                self.assertEqual(self.z.require_off_pair(on,off,data),e['proof'])
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678));counter=report['counters'][0]
            self.z.require_counter(counter,normal,data,q)
            self.assertEqual(counter['result']['instructions'],normal['instructions']+2)
            self.assertEqual(counter['result']['pp_reader']['ram_sha256'],normal['pp_reader']['ram_sha256'])

    def test_cur_counter_preshadow_and_equivalent_output_do_not_attribute_set(self):
        for lang,report in self.reports.items():
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678))
            for key in('original','actual','shadow','load','second','prestate','output','tag'):
                bad=copy.deepcopy(report['counters'][0]);r=bad['result'];call=r['seek'][0]
                if key=='original':call['original_entry'][2]=1
                elif key=='actual':call['entry'][2]=0
                elif key=='shadow':call['shadows'][0]['after'][1]^=1
                elif key=='load':call['reads'][0]['address']=self.z.FILE+36
                elif key=='second':r['seek'][1]['entry'][2]=1
                elif key=='prestate':call['frame_before']='00'*240
                elif key=='output':r['raw_ram_sha256']='0'*64
                else:bad['tag_disguised']=False
                with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])


if __name__=='__main__':unittest.main()
