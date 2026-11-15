"""Pure replay/falsification of private isolated Read reports; never runs a CPU."""
from pathlib import Path
import copy, gzip, importlib.util, json, os, unittest
ENV=('SGP_FS_READ_ROM_DIR','SGP_FS_READ_REPORT_DIR','SGP_FS_READ_PARENT_DIR',
     'SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')


@unittest.skipUnless(all(os.environ.get(k) for k in ENV),'requires private exact ROMs, objects and Read/Seek reports')
class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).resolve().parents[1]/'tools/attribuisci_fs_read.py'
        s=importlib.util.spec_from_file_location('read_replay',path);cls.Z=Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)
        cls.reports={};cls.bodies={};cls.prepared={}
        for lang in ('EN','IT'):
            parent=Path(os.environ[ENV[2]])/('fs-seek-'+lang+'.json.gz')
            cls.prepared[lang],cls.bodies[lang]=Z.prepare(Path(os.environ[ENV[0]])/('r4-'+lang+'.nds'),lang,parent,
                Path(os.environ[ENV[3]])/('public-build-'+lang),Path(os.environ[ENV[4]])/('build-'+lang)/'teams.o')
            cls.prepared[lang]=json.loads(json.dumps(cls.prepared[lang]))
            cls.reports[lang]=json.loads(gzip.decompress((Path(os.environ[ENV[1]])/('fs-read-'+lang+'.json.gz')).read_bytes()))

    def test_complete49_matrix_and_current_input_derivation(self):
        for lang,r in self.reports.items():
            self.assertEqual(r['source_sha256'],self.Z.source_identities())
            for k,v in self.prepared[lang].items():self.assertEqual(r[k],v)
            self.Z.require_matrix(r,self.bodies[lang])

    def base(self):
        lang=next(iter(self.reports));return lang,copy.deepcopy(self.reports[lang]['runs'][0]['result'])

    def test_full_abi_register_and_instruction_falsifiers(self):
        for field in ('R0','R3','IP','LR','SP','flags','wide','missing','optional','order','literal'):
            lang,r=self.base()
            if field in ('R0','R3','IP','LR','SP','flags'):
                index={'R0':0,'R3':3,'IP':12,'LR':14,'SP':13,'flags':15}[field];r['returned'][index]^=1
            elif field=='wide':r['flow'][0]['regs'][15]|=1<<32
            elif field=='missing':r['flow']=r['flow'][1:]
            elif field=='optional':r['flow']=[e for e in r['flow']if e['pc']!='0x20d8124'];r['steps']-=1
            elif field=='order':r['flow'][0],r['flow'][1]=r['flow'][1],r['flow'][0]
            else:r['flow'][0]['pc']='0x20d83d8'
            with self.subTest(field=field),self.assertRaises(ValueError):self.Z.B.require_result(r,self.bodies[lang])

    def test_native_fields_model_boundaries_and_memory_falsifiers(self):
        for field in ('nativeStore','literalRead','readValue','sendCommand','waitLR','frame','payload','RAM','fault','halt','OFFsteps'):
            lang,r=self.base()
            if field=='nativeStore':r['stores'][-1]['address']+=4
            elif field=='literalRead':r['reads'][0]['address']+=4
            elif field=='readValue':r['reads'][0]['hex']='00000000'
            elif field=='sendCommand':r['services'][0]['entry'][1]=1
            elif field=='waitLR':r['services'][1]['entry'][14]^=4
            elif field=='frame':r['frame_after']=r['fixture']['frame']
            elif field=='payload':r['destination_after']='00'*r['fixture']['entry'][2]
            elif field=='RAM':r['whole_ram_sha256']='0'*64
            elif field=='fault':r['fault']=dict(type='UcError',message='synthetic test')
            elif field=='halt':r['halt_pc']='0x2000000'
            else:r.update(observe=False,flow=[],stores=[],reads=[],steps=101)
            with self.subTest(field=field),self.assertRaises(ValueError):self.Z.B.require_result(r,self.bodies[lang])

    def test_wait_false_counter_same_memory_does_not_prove_native_success(self):
        for lang,r in self.reports.items():
            counter=copy.deepcopy(next(x['result'] for x in r['runs'] if x['kind']=='wait_false'))
            normal=r['runs'][0]['result'];self.assertEqual(counter['whole_ram_sha256'],normal['whole_ram_sha256'])
            counter['policy']['wait']=1
            with self.assertRaises(ValueError):self.Z.B.require_result(counter,self.bodies[lang])
            bad=copy.deepcopy(r);next(x for x in bad['runs'] if x['kind']=='wait_false')['kind']='normal'
            with self.assertRaises(ValueError):self.Z.require_matrix(bad,self.bodies[lang])

    def test_parent_preimage_and_fixture_rebinding_cannot_be_accepted(self):
        for lang,r in self.reports.items():
            for field in ('frame','entry','payload','ordinal'):
                bad=copy.deepcopy(r);f=bad['runs'][0]['result']['fixture']
                if field=='frame':f[field]='00'*240
                elif field=='entry':f[field][14]^=4
                elif field=='payload':f[field]='00'*f['entry'][2]
                else:f[field]=1
                with self.subTest(field=field),self.assertRaises(ValueError):self.Z.require_matrix(bad,self.bodies[lang])


if __name__=='__main__':unittest.main()
