"""Pure replay/falsifiers for private Read+Wait+IRQ reports; no CPU execution."""
from pathlib import Path
import copy,gzip,importlib.util,json,os,unittest
ENV=('SGP_FS_WAIT_ROM_DIR','SGP_FS_WAIT_REPORT_DIR','SGP_FS_WAIT_PARENT_DIR','SGP_FS_WAIT_SEEK_DIR',
     'SGP_FS_WAIT_RECIPE_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k)for k in ENV),'requires private exact ROMs, objects, recipes and Wait/Read/Seek reports')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).resolve().parents[1]/'tools/attribuisci_fs_wait.py'
        s=importlib.util.spec_from_file_location('wait_replay',path);cls.W=W=importlib.util.module_from_spec(s);s.loader.exec_module(W)
        cls.reports={};cls.bodies={};cls.prepared={}
        for lang in('EN','IT'):
            receipt,cls.bodies[lang]=W.prepare(Path(os.environ[ENV[0]])/('r4-'+lang+'.nds'),lang,
                Path(os.environ[ENV[2]])/('fs-read-'+lang+'.json.gz'),Path(os.environ[ENV[3]])/('fs-seek-'+lang+'.json.gz'),
                Path(os.environ[ENV[5]])/('public-build-'+lang),Path(os.environ[ENV[6]])/('build-'+lang)/'teams.o',Path(os.environ[ENV[4]]))
            cls.prepared[lang]=json.loads(json.dumps(receipt))
            cls.reports[lang]=json.loads(gzip.decompress((Path(os.environ[ENV[1]])/('fs-wait-'+lang+'.json.gz')).read_bytes()))

    def base(self):
        lang=next(iter(self.reports));return lang,copy.deepcopy(self.reports[lang]['runs'][0]['result'])

    def test_public_irq32_leaf_capability_and_control_mutants(self):
        language='EN';path=Path(os.environ[ENV[1]])/'irq-public-EN.json.gz'
        report=json.loads(gzip.decompress(path.read_bytes()))
        self.assertEqual(report['source_sha256'],self.W.source_identities())
        self.assertEqual(report['unicorn'],'2.1.4');self.assertEqual(report['cpu_model'],17)
        self.assertEqual(report['cpu_name'],'UC_CPU_ARM_CORTEX_A15')
        self.assertEqual(report['input'],self.reports[language]['input']);self.assertTrue(report['passed'])
        bodies={a:self.bodies[language][a] for a in(self.W.B.DISABLE,self.W.B.RESTORE)}
        self.W.B.require_irq_rows(report['rows'],bodies)
        for flag in(128,64,1,1<<29):
            rows=copy.deepcopy(report['rows']);rows[0]['after_restore'][15]^=flag
            with self.assertRaises(ValueError):self.W.B.require_irq_rows(rows,bodies)
        rows=copy.deepcopy(report['rows']);rows[0]['flow'][0]['regs'][15]|=1<<32
        with self.assertRaises(ValueError):self.W.B.require_irq_rows(rows,bodies)

    def test_full_matrix55_sources_three_recipes_and_current_input_proof(self):
        for lang,report in self.reports.items():
            self.assertEqual(report['source_sha256'],self.W.source_identities());self.assertEqual(len(report['source_sha256']),55)
            self.assertEqual(report['recipes'],self.W.B.RECIPES);self.assertEqual(report['unicorn'],'2.1.4')
            self.assertEqual(report['cpu_model'],17);self.assertEqual(report['cpu_name'],'UC_CPU_ARM_CORTEX_A15')
            for k,v in self.prepared[lang].items():self.assertEqual(report[k],v)
            self.W.require_matrix(report,self.bodies[lang])

    def test_full_irq_and_return_abi_falsifiers(self):
        for field in('I','F','mode','NZCV','R1','R2','LR','SP','wide','falseNE','order'):
            lang,r=self.base()
            if field in('I','F','mode','NZCV'):r['returned'][15]^={'I':128,'F':64,'mode':1,'NZCV':1<<29}[field]
            elif field in('R1','R2','LR','SP'):r['returned'][{'R1':1,'R2':2,'LR':14,'SP':13}[field]]^=1
            elif field=='wide':r['flow'][0]['regs'][15]|=1<<32
            elif field=='falseNE':r['flow']=[e for e in r['flow']if e['pc']!='0x20d8318'];r['steps']-=1
            else:r['flow'][0],r['flow'][1]=r['flow'][1],r['flow'][0]
            with self.subTest(field=field),self.assertRaises(ValueError):self.W.B.require_result(r,self.bodies[lang])

    def test_completion_projection_and_model_registers_cannot_be_forged(self):
        for field in('command','error','stat','frameBefore','fieldWidth','regs','nativeStore'):
            lang,r=self.base();p=r['completion'][0]
            if field in('command','error','stat'):
                memory=bytearray.fromhex(p['frame_after']);a=self.W.B.FILE-self.W.B.FRAME+{'stat':12,'command':16,'error':20}[field]
                memory[a]^=1;p['frame_after']=memory.hex()
            elif field=='frameBefore':p['frame_before']=p['frame_after']
            elif field=='fieldWidth':p['bytes']=16
            elif field=='regs':p['regs'][8]^=1
            else:r['stores'][-1]['value']^=1
            with self.subTest(field=field),self.assertRaises(ValueError):self.W.B.require_result(r,self.bodies[lang])

    def test_native_read_owners_and_fault_capture_reject_mutants(self):
        for field in('WaitRead','WaitPOP','ReadValue','SDK','RAM','fault','halt','OFFstep'):
            lang,r=self.base()
            if field=='WaitRead':next(e for e in r['reads']if e['pc']=='0x20d830c')['address']+=4
            elif field=='WaitPOP':next(e for e in r['reads']if e['pc']=='0x20d83b8')['address']+=4
            elif field=='ReadValue':r['reads'][0]['hex']='00000000'
            elif field=='SDK':r['services'][0]['entry'][1]=1
            elif field=='RAM':r['whole_ram_sha256']='0'*64
            elif field=='fault':r['fault']=dict(type='UcError',message='synthetic falsifier')
            elif field=='halt':r['halt_pc']='0x2000000'
            else:r.update(observe=False,flow=[],stores=[],reads=[],steps=66)
            with self.subTest(field=field),self.assertRaises(ValueError):self.W.B.require_result(r,self.bodies[lang])

    def test_error_counter_preserves_payload_but_cannot_be_resealed_success(self):
        for lang,report in self.reports.items():
            normal=report['runs'][0]['result'];error=copy.deepcopy(next(x['result']for x in report['runs']if x['kind']=='error1'))
            self.assertEqual(error['destination_after'],normal['destination_after'])
            self.assertNotEqual(error['whole_ram_sha256'],normal['whole_ram_sha256'])
            error['policy']['error']=0
            with self.assertRaises(ValueError):self.W.B.require_result(error,self.bodies[lang])

    def test_irq1_memory_equality_does_not_attribute_irq0_and_grid_is_exact(self):
        for lang,report in self.reports.items():
            normal=report['runs'][0]['result'];irq=next(x['result']for x in report['runs']if x['kind']=='irq1')
            self.assertEqual(irq['whole_ram_sha256'],normal['whole_ram_sha256'])
            for mode in('I','fixture','duplicate'):
                bad=copy.deepcopy(report)
                if mode=='I':next(x['result']for x in bad['runs']if x['kind']=='irq1')['returned'][15]&=~128
                elif mode=='fixture':next(x['result']for x in bad['runs']if x['kind']=='irq1')['fixture']['entry'][15]&=~128
                else:bad['runs'][1]=copy.deepcopy(bad['runs'][0])
                with self.subTest(mode=mode),self.assertRaises(ValueError):self.W.require_matrix(bad,self.bodies[lang])


if __name__=='__main__':unittest.main()
