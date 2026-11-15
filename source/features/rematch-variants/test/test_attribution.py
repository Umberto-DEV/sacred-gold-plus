"""Exact-current attribution; raw ROM inputs are supplied through SGP_R4_ROM_DIR.

Class A checks object retention and output hygiene without a ROM. Class B uses
mmap and small initialized CPU paths; it never installs or composes a ROM.
"""
from pathlib import Path
import copy,importlib.util,mmap,os,sys,tempfile,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SOURCE))
from sgp131 import rematches as R

def tool():
 spec=importlib.util.spec_from_file_location('exact_rematch_attribution',SOURCE/'features/rematch-variants/tools/attribuisci.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class RetainedObjects(unittest.TestCase):
 def test_native_object_opt_in_preserves_default_output_and_cleanup(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);a=R.compile_native(p/'default',0x226B000,0x226B500,768)
   self.assertFalse((p/'default/rematch-variants.o').exists())
   b=R.compile_native(p/'retain',0x226B000,0x226B500,768,retain_object=True)
   self.assertEqual(a,b);self.assertEqual((p/'retain/rematch-variants.o').read_bytes()[:4],b'\x7fELF')
   for invalid in (0,1,None):
    with self.assertRaises(ValueError):R.compile_native(p/'invalid',0,0,0,retain_object=invalid)
   self.assertFalse((p/'invalid').exists())
 def test_stub_object_opt_in_preserves_default_output_and_cleanup(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td);a=R.compile_stub(p/'default',0x23D59E0,0x226B4A1)
   self.assertFalse((p/'default/rematch-stub.o').exists())
   b=R.compile_stub(p/'retain',0x23D59E0,0x226B4A1,retain_object=True)
   self.assertEqual(a,b);self.assertEqual((p/'retain/rematch-stub.o').read_bytes()[:4],b'\x7fELF')
   for invalid in (0,1,None):
    with self.assertRaises(ValueError):R.compile_stub(p/'invalid',0,0,retain_object=invalid)
   self.assertFalse((p/'invalid').exists())


class AttributionCLI(unittest.TestCase):
 def test_each_input_alias_and_existing_artifact_is_preserved(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);inputs=[root/(n+'.nds') for n in ('rom','v4','base','retail')]
   for p in inputs:p.write_bytes(b'preserved')
   for p in inputs:
    symlink=p.with_suffix('.symlink');symlink.symlink_to(p)
    hard=p.with_suffix('.hard');os.link(p,hard)
    for output in (p,symlink,hard):
     argv=['rematch','--language','EN','--json',str(output),'--work',str(root/'fresh')]
     for name,value in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(value)))
     with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
      with self.assertRaises(SystemExit) as e:m.main()
      self.assertEqual(e.exception.code,2);analyze.assert_not_called();self.assertEqual(p.read_bytes(),b'preserved')
   for work,output in ((root,root/'new.json'),(root/'fresh',root/'fresh/report.json'),(SOURCE/'new',root/'new.json'),(root/'fresh',SOURCE/'new.json')):
    with self.assertRaises(ValueError):m.validate_outputs(inputs,work,output)


@unittest.skipUnless(os.environ.get('SGP_R4_ROM_DIR'),'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentInertRematch(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=tool();cls.paths={lang:Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%lang) for lang in ('EN','IT')}
  cls.models={lang:cls.m.G.S.SHARED.read_current(path,lang) for lang,path in cls.paths.items()}
  cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup);cls.work=Path(cls.tmp.name)
  with cls.paths['EN'].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:res,_=cls.m.resources(raw,cls.models['EN'])
  cls.code,cls.build=cls.m.compile_exact(cls.work,cls.m.config_from(res))
 def run_cpu(self,language,**kwargs):
  with self.paths[language].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   return self.m.run_case(self.models[language],raw,language,self.code,**kwargs)
 def test_native_prefix_inert_paths_restore_abi_buffer_rng_and_lifetime(self):
  for lang in ('EN','IT'):
   native=self.run_cpu(lang,variant='native');self.m.require_run(native,native=True)
   for scenario in ('success','refused','failed'):
    r=self.run_cpu(lang,scenario=scenario);self.m.require_run(r)
    self.assertEqual(r['neutral_ram_sha256'],native['neutral_ram_sha256'])
   for result in (0,0xFFFFFFFF):self.m.require_run(self.run_cpu(lang,reader_result=result))
 def test_same_output_cannot_hide_missing_unload_or_unsafe_abi_code(self):
  for lang in ('EN','IT'):
   for scenario in ('success','failed'):
    r=self.run_cpu(lang,scenario=scenario,variant='skip_unload')
    self.assertEqual(r['resume']['r'][0],r['reader_result']);self.assertEqual(r['buffer_sha256'],r['buffer_expected_sha256']);self.assertEqual(r['registry'][0],(126,1))
    r['variant']='current'
    with self.assertRaises(ValueError):self.m.require_run(r)
   for variant,scenario,reason in (('wrong_args','refused','archive forward ABI'),('pool_entry','success','outside qualified code')):
    with self.assertRaisesRegex(ValueError,reason):self.run_cpu(lang,variant=variant,scenario=scenario)
 def test_result_oracle_rejects_abi_registry_trace_and_config_mutations(self):
  r=self.run_cpu('EN');self.m.require_run(r);mutations=[]
  for field in ('reader_calls','unload_calls','assert_calls','wfc_calls','wfc_counter','seed_after','instructions','max_stack'):
   x=copy.deepcopy(r);x[field]=(300001 if field in ('instructions','max_stack') else x[field]^1);mutations.append((field,x))
  for reg in (0,1,2,4,8,11):
   x=copy.deepcopy(r);x['resume']['r'][reg]^=1;mutations.append(('r'+str(reg),x))
  for field in ('canaries','stack_canary'):
   x=copy.deepcopy(r);x[field]=False;mutations.append((field,x))
  for field in ('buffer_sha256','registry','critical','config_reads','code'):
   x=copy.deepcopy(r);x[field]='invalid' if field=='buffer_sha256' else [];mutations.append((field,x))
  x=copy.deepcopy(r);x['resume']['sp']+=8;mutations.append(('sp',x))
  for name,x in mutations:
   with self.subTest(name=name),self.assertRaises(ValueError):self.m.require_run(x)
 def test_elf_relocation_nonrelocation_and_native_instruction_drift_refused(self):
  m=self.m;obj=(self.work/'rematch-variants.o').read_bytes();payload=(self.work/'module.bin').read_bytes()[:1216]
  proof=m.audit_elf(obj,payload,m.MODULE);self.assertEqual(len(proof['relocations']),2)
  for at in (0,int(proof['relocations'][0]['offset'],16)):
   changed=bytearray(payload);changed[at]^=1
   with self.subTest(offset=at),self.assertRaises(ValueError):m.audit_elf(obj,bytes(changed),m.MODULE)
  with self.assertRaises(ValueError):m.audit_elf(b'NOT ELF',payload,m.MODULE)
  self.assertNotIn(0x226B494,self.code);self.assertNotIn(0x226B4BC,self.code)
  model=self.models['EN']
  with self.paths['EN'].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   for address,_,_,_ in m.NATIVE_BLOCKS:
    changed=dict(model);segments=[]
    for a,b in model['segments']:
     c=bytearray(b)
     if a<=address<a+len(b):c[address-a]^=1
     segments.append((a,bytes(c)))
    changed['segments']=segments;bench=m.Adapter(changed,raw,'EN');bench.module_code=self.code
    with self.subTest(address=hex(address)),self.assertRaisesRegex(ValueError,'native instruction block'):m.Audit(bench,712,'current',1)
 def test_invalid_fixture_domain_and_optimized_python_refused(self):
  for kw in (dict(trainer=0),dict(scenario='maybe'),dict(variant='arbitrary'),dict(plus=2),dict(reader_result=42)):
   with self.subTest(kw=kw),self.assertRaises(ValueError):self.run_cpu('EN',**kw)
  from types import SimpleNamespace
  with patch.object(self.m.sys,'flags',SimpleNamespace(optimize=1)):
   with self.assertRaisesRegex(ValueError,'without Python -O'):self.run_cpu('EN')


if __name__=='__main__':unittest.main()
