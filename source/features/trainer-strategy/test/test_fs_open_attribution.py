"""Pure replay and counterfalsifiers for developer-owned exact Open reports."""
from pathlib import Path
import copy,gc,gzip,importlib.util,json,mmap,os,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
ENV=('SGP_FS_OPEN_ROM_DIR','SGP_FS_OPEN_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact ROMs, objects and Open reports')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=SOURCE/'features/trainer-strategy/tools/attribuisci_fs_open.py'
        s=importlib.util.spec_from_file_location('fs_open_replay',p);cls.z=z=importlib.util.module_from_spec(s);s.loader.exec_module(z)
        cls.reports,cls.data,cls.q={},{},{}
        for language in os.environ.get('SGP_FS_OPEN_LANGUAGES','EN,IT').split(','):
            rom=Path(os.environ[ENV[0]])/('r4-'+language+'.nds');model=z.P.G.S.SHARED.read_current(rom,language)
            with rom.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as raw:
                cls.q[language],_=z.qualify(model,raw,language,
                    Path(os.environ[ENV[2]])/('public-build-'+language),Path(os.environ[ENV[3]])/('build-'+language)/'teams.o')
                cls.data[language]=z.O.resources(model,raw,language)
            p=Path(os.environ[ENV[1]])/('fs-open-'+language+'.json.gz')
            cls.reports[language]=json.loads(gzip.decompress(p.read_bytes()));del model;gc.collect()

    def base(self):
        language=next(iter(self.reports));return language,copy.deepcopy(self.reports[language]['positives'][0])

    def require(self,language,r):self.z.require_case(r,self.data[language],self.q[language])

    def test_all_positive_guard_and_model_policy_receipts(self):
        for language,report in self.reports.items():
            self.assertEqual(report['source_sha256'],self.z.source_identities())
            self.assertEqual(len(report['recipes']),6)
            self.assertEqual(report['conditional_policy']['unicorn_version'],'2.1.4')
            self.assertIs(report['conditional_policy']['false_NE_hooks'],True)
            self.assertEqual(sum(len(report[k])for k in('positives','guards','volatile_controls','observer_off','counters')),10)
            for r in report['positives']+report['guards']+report['volatile_controls']:self.require(language,r)

    def test_lower_aggregate_abi_arm_returns_and_void_residues(self):
        for key in('pointer','byvalue','sp','lr','thumb','r12','saved','returnflags','fake_open'):
            language,r=self.base();first,fast=r['pp_reader']['models'][:2]
            if key=='pointer':first['args'][0]=self.z.FILE
            elif key=='byvalue':fast['args'][2]=self.z.ID
            elif key=='sp':first['sp']=first['return_sp']=self.z.TOP-136
            elif key=='lr':first['lr']='0x20d828d'
            elif key=='thumb':fast['returned'][15]|=32
            elif key=='r12':first['entry'][12]^=1
            elif key=='saved':fast['return_saved'][0]^=1
            elif key=='returnflags':r['fs_open']['returned'][15]=0x3F
            else:first['name']='FS_OpenFile'
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(language,r)

    def test_native_push_ldm_and_model_delivery_have_separate_provenance(self):
        for key in('push','width','address','before','ldm','output','delivery','guestfield'):
            language,r=self.base();out=r['fs_open'];first=r['pp_reader']['models'][0]
            if key=='push':out['stores']=out['stores'][:-1]
            elif key=='width':out['stores'][0]['bytes']=8
            elif key=='address':out['stores'][0]['address']-=8
            elif key=='before':
                a=bytearray.fromhex(out['stores'][0]['before']);a[0]^=1;out['stores'][0]['before']=a.hex()
            elif key=='ldm':out['id_reads'][1]['address']+=4
            elif key=='output':first['destination']=self.z.FILE
            elif key=='delivery':first['delivered_hex']='00'*8;first['delivered_sha256']=self.z.sha(bytes(8))
            else:
                a=bytearray.fromhex(out['frame_after']);a[16+24+20]^=1;out['frame_after']=a.hex()
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(language,r)

    def test_frame152_legacy136_and_new_guard_cannot_diverge(self):
        for key in('before','after','legacy_before','legacy_after','pair','guard','range','peak','count'):
            language,r=self.base();p=r['pp_reader'];out=r['fs_open']
            if key=='before':p['stack152_before']='00'*152
            elif key=='after':p['stack152_after']='00'*152
            elif key=='legacy_before':p['stack_frame_before']='00'*136
            elif key=='legacy_after':p['stack_frame_hex']='00'*136
            elif key=='pair':
                for field in('frame_before','frame_after'):
                    a=bytearray.fromhex(out[field]);a[26]^=1;out[field]=a.hex()
            elif key=='guard':p['stack_guard_after']='00'*56
            elif key=='range':p['stack_guard_range']=[self.z.TOP-192,self.z.TOP-136]
            elif key=='peak':p['max_stack']=136
            else:p['instructions']=127
            with self.subTest(key=key),self.assertRaises(ValueError):self.require(language,r)

    def test_truthy_two_is_normalized_by_native_instructions(self):
        for language,report in self.reports.items():
            r=next(r for r in report['volatile_controls']if r['open_fast_value']==2)
            self.assertEqual(r['pp_reader']['models'][1]['result_r0'],2)
            self.assertEqual(r['fs_open']['returned'][0],1)
            for value in(True,0,3):
                bad=copy.deepcopy(r);bad['open_fast_value']=value
                with self.subTest(value=value),self.assertRaises(ValueError):self.require(language,bad)
            bad=copy.deepcopy(r);bad['fs_open']['returned'][0]=2
            with self.assertRaises(ValueError):self.require(language,bad)

    def test_executed_off_and_false_status_counter(self):
        for language,report in self.reports.items():
            data,q=self.data[language],self.q[language]
            for entry in report['observer_off']:
                off=entry['result'];on=next(r for r in report['positives']if(r['plus'],r['seed'])==(off['plus'],off['seed']))
                self.assertEqual(self.z.require_off_pair(on,off,data),entry['proof'])
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678))
            self.z.require_counter(report['counters'][0],normal,data,q)

    def test_false_ne_hooks_do_not_prove_conditional_effects(self):
        for language,report in self.reports.items():
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678));counter=report['counters'][0]
            for key in('movne','addne','shadow','prestate','ledger','count','missingpc','packet'):
                bad=copy.deepcopy(counter);r=bad['result'];out=r['fs_open'];flow={e['pc']:e for e in out['flow']}
                if key=='movne':flow['0x20d82b0']['regs'][0]=1
                elif key=='addne':flow['0x20d82ac']['regs'][13]+=8
                elif key=='shadow':out['shadows'][0]['after'][12]^=1
                elif key=='prestate':r['pp_binding']['ram_sha256']=r['pp_reader']['unrelated_ram_sha256']='0'*64
                elif key=='ledger':out['ledger_after']['open']=False
                elif key=='count':r['pp_reader']['instructions']=143
                elif key=='missingpc':out['flow']=out['flow'][:-1]
                else:r['mon_hex'][0]='00'*236
                with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[language],self.q[language])

    def test_false_policy_runtime_identity_is_finite(self):
        import unicorn
        for language,report in self.reports.items():
            normal=next(r for r in report['positives']if(r['plus'],r['seed'])==(1,0x12345678));counter=report['counters'][0]
            for key in('version','cpu','unqualified'):
                bad=copy.deepcopy(counter)
                if key=='version':context=patch.object(unicorn,'__version__','2.1.3')
                elif key=='unqualified':context=patch.object(self.z,'FALSE_CONDITIONAL_HOOKS',None)
                else:bad['result']['pp_reader']['cpu_model']=0;context=patch.object(self.z,'FALSE_CONDITIONAL_HOOKS',True)
                with self.subTest(key=key),context,self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[language],self.q[language])


if __name__=='__main__':unittest.main()
