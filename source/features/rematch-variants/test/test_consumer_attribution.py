"""First native CreateMon entry after the actual rematch RAM path; no body execution."""
from pathlib import Path
import copy,importlib.util,mmap,os,sys,tempfile,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]

def tool():
 spec=importlib.util.spec_from_file_location('rematch_consumer_attribution',SOURCE/'features/rematch-variants/tools/attribuisci_consumo.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class ConsumerCLI(unittest.TestCase):
 def test_outputs_cannot_replace_inputs_aliases_or_retained_artifacts(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);objects=root/'objects';objects.mkdir();inputs=[root/'r4.nds',objects/'rematch-variants.o',objects/'rematch-stub.o']
   for p in inputs:p.write_bytes(b'preserve')
   def argv(work,out):return ['consumer','--rom',str(inputs[0]),'--language','EN','--objects',str(objects),'--work',str(work),'--json',str(out)]
   for i,p in enumerate(inputs):
    sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard)
    for out in (p,sym,hard):
     with self.subTest(out=out.name),patch.object(sys,'argv',argv(root/'fresh',out)),patch.object(m,'analyze') as analyze:
      with self.assertRaises(SystemExit) as e:m.main()
      self.assertEqual(e.exception.code,2);analyze.assert_not_called();self.assertEqual(p.read_bytes(),b'preserve')
   for work,out in ((root,root/'new.json'),(root/'fresh',root/'fresh/new.json'),(SOURCE/'new',root/'new.json'),(root/'fresh',objects/'new.json'),(objects/'fresh',root/'new.json')):
    with patch.object(sys,'argv',argv(work,out)),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()


 def test_lineage_json_preserves_each_exact_input_and_its_aliases(self):
  spec=importlib.util.spec_from_file_location('rematch_consumer_lineage',SOURCE/'features/rematch-variants/tools/rileggi_stadi.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);inputs=[root/(n+'.nds') for n in ('rom','v4','base','retail')]
   for p in inputs:p.write_bytes(b'preserve')
   targets=[]
   for i,p in enumerate(inputs):
    sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);targets.extend((p,sym,hard))
   targets.append(SOURCE/'new.json')
   for out in targets:
    argv=['lineage','--language','EN','--json',str(out)]
    for name,p in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(p)))
    with self.subTest(out=out.name),patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
    for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')


@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_R4_ROM_DIR','SGP_REMATCH_OBJECTS_DIR','SGP_STRATEGY_OBJECT')),'requires exact r4 EN/IT,rematch objects and strategy teams.o')
class CurrentNativeConsumer(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=tool();cls.objects=Path(os.environ['SGP_REMATCH_OBJECTS_DIR']);cls.object_data=Path(os.environ['SGP_STRATEGY_OBJECT']).read_bytes();cls.models={};cls.paths={};cls.codes={};cls.data={}
  for lang in ('EN','IT'):
   p=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%lang);cls.paths[lang]=p;model=cls.m.P.G.S.SHARED.read_current(p,lang);cls.models[lang]=model
   with p.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
    code,_=cls.m.A.attest_objects(raw,model,cls.objects);proof=cls.m.P.audit_elf(cls.object_data,cls.m.bench_bytes(model,0x23D6000,580),0x23D6000);cls.proof=proof
    cls.codes[lang]=(code,cls.m.qualify_code(model,proof));cls.data[lang]=cls.m.input_data(raw,model)
 def cpu(self,lang='EN',**kw):
  with self.paths[lang].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:return self.m.run_case(self.models[lang],raw,lang,*self.codes[lang],**kw)
 def test_actual_chosen_first_record_native_math_level_and_create_entry(self):
  for lang in ('EN','IT'):
   for trainer in (712,713):
    for seed in (0x12345678,0x12345679):
     r=self.cpu(lang,trainer=trainer,seed=seed);self.m.require_consumer(r,self.data[lang]);self.assertEqual(r['create']['lr'],0x2073A17)
     self.assertEqual(r['create']['buffer_sha256'],r['prefix']['buffer_sha256']);self.assertTrue(r['ram_unchanged_postgetter']);self.assertNotEqual(r['create']['seed'],r['prefix']['seed'])
 def test_same_buffer_wrong_record_or_cap_cannot_pass_as_normal(self):
  for lang in ('EN','IT'):
   baseline=self.cpu(lang)
   for variant in ('wrong_record','low_cap'):
    r=self.cpu(lang,consumer_variant=variant);self.assertEqual(r['create']['buffer_sha256'],baseline['create']['buffer_sha256']);self.assertEqual(r['create']['args'][0],baseline['create']['args'][0])
    if variant=='low_cap':
     self.assertEqual(r['create']['stack'],baseline['create']['stack']);self.assertEqual(r['create']['seed'],baseline['create']['seed']);self.assertEqual(r['create']['args'][2],75)
    r['consumer_variant']='current'
    with self.assertRaises(ValueError):self.m.require_consumer(r,self.data[lang])
 def test_result_oracle_rejects_wrong_arguments_math_helper_return_and_resource_reads(self):
  m=self.m;r=self.cpu();m.require_consumer(r,self.data['EN']);mutants=[]
  for path in [('create','args',i) for i in range(4)]+[('create','stack',i) for i in range(4)]+[('create',k) for k in ('sp','lr','seed','plus_counter','nzcv')]+[('create','live',3),('instructions',),('max_stack',)]:
   x=copy.deepcopy(r);v=x
   for k in path[:-1]:v=v[k]
   v[path[-1]]=300001 if path[-1] in ('instructions','max_stack') else v[path[-1]]^1;mutants.append((str(path),x))
  for entry,path in (('0x201fd44',('before_seed',)),('0x201fd44',('after_seed',)),('0x201fd44',('result',0)),('0x201fd44',('return_pc',)),('0x201fd44',('return_sp',)),('0x20f2998',('result',1)),('0x23d8100',('args',2)),('0x23d8100',('result',0)),('0x23d8134',('result',0)),('0x23d602c',('result',0)),('0x23d6228',('nzcv',)),('0x2073a98',('pid_gender',))):
   x=copy.deepcopy(r);v=next(c for c in x['helpers'] if c['entry']==entry)
   for k in path[:-1]:v=v[k]
   v[path[-1]]^=1;mutants.append((entry+str(path),x))
  for field in ('helpers','record_reads','dependency_reads','writes','code'):
   x=copy.deepcopy(r);x[field]=[];mutants.append((field,x))
  for field,index in (('record_reads',0),('record_reads',-1),('dependency_reads',1),('dependency_reads',-1)):
   x=copy.deepcopy(r);x[field][index]['value']^=1;mutants.append((field+str(index),x))
  x=copy.deepcopy(r);x['ram_unchanged_postgetter']=False;mutants.append(('postgetter',x))
  for label,x in mutants:
   with self.subTest(label=label),self.assertRaises(ValueError):m.require_consumer(x,self.data['EN'])
 def test_native_data_code_and_strategy_config_drift_are_refused_at_their_admission(self):
  m=self.m;model=self.models['EN']
  def changed(address):
   result=dict(model);segments=[]
   for base,blob in model['segments']:
    raw=bytearray(blob)
    if base<=address<base+len(blob):raw[address-base]^=1
    segments.append((base,bytes(raw)))
   result['segments']=segments;return result
  for address in [a for a,_,_,_ in m.NATIVE_BLOCKS]+[0x201FD60,0x201FD40,0x2073600,0x206DE38,0x23D8100,0x23D8500]:
   with self.subTest(address=hex(address)),self.assertRaises(ValueError):m.qualify_code(changed(address),self.proof)
  payload=bytearray(m.bench_bytes(model,0x23D6000,580));payload[0]^=1
  with self.assertRaises(ValueError):m.P.audit_elf(self.object_data,bytes(payload),0x23D6000)
  from sgp13 import teams
  with tempfile.TemporaryDirectory() as td,self.paths['EN'].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   def compile_existing(work):
    work.mkdir();(work/'teams.o').write_bytes(self.object_data);return m.bench_bytes(model,0x23D6000,580),{k:int(v,16) for k,v in self.proof['symbols'].items()}
   with patch.object(m.P.R,'_compiler',return_value='/qualified/compiler'),patch.object(teams,'compile_native',side_effect=compile_existing):
    with self.assertRaisesRegex(ValueError,'strategy config192'):m.attest_strategy(changed(0x23D6608),raw,Path(td)/'fresh')
 def test_new_store_read_and_pool_guards_refuse_invalid_observations(self):
  m=self.m
  with self.paths['EN'].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   b=m.P.Adapter(self.models['EN'],raw,'EN');b.module_code=self.codes['EN'][0];a=m.Consumer(b,712);a.next_allowed=self.codes['EN'][1];a.gender_table=0x20FFB90
   u=a.factory(m.B.UC_ARCH_ARM,m.B.UC_MODE_THUMB);u.mem_map(0x02000000,0x400000);a.consume=True;u.reg_write(m.P.UC_ARM_REG_SP,m.B.STACK_TOP)
   for pc,address,width,value in ((0x201FD52,0x21D15A8,4,0),(0x201FD52,0x21D15AC,4,0),(0x201FD52,0x21D15A8,1,0),(0x23D813E,0x23D8708,4,99)):
    u.reg_write(m.P.UC_ARM_REG_PC,pc)
    with self.assertRaises(ValueError):a.write(u,0,address,width,value,None)
   with self.assertRaisesRegex(ValueError,'read outside'):a.read(u,0,0x2390000,4,0,None)
   for pc in (0x2073672,0x2073994,0x23D6240,0x23D818C):
    with self.subTest(pool=hex(pc)),self.assertRaisesRegex(ValueError,'outside qualified code'):a.step(u,pc,2,None)
  with self.assertRaises(ValueError):self.cpu(consumer_variant='ambiguous')


if __name__=='__main__':unittest.main()
