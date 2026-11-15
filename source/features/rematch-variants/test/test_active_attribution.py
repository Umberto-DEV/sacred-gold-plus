"""Named active RAM shadows: no ROM installation or write, no compiler invocation."""
from pathlib import Path
import copy,importlib.util,mmap,os,sys,tempfile,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]

def tool():
 spec=importlib.util.spec_from_file_location('rematch_active_attribution',SOURCE/'features/rematch-variants/tools/attribuisci_attivo.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class ActiveAttributionCLI(unittest.TestCase):
 def test_json_cannot_replace_rom_objects_or_input_aliases(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);objects=root/'objects';objects.mkdir();rom=root/'rom.nds'
   inputs=[rom,objects/'rematch-variants.o',objects/'rematch-stub.o']
   for p in inputs:p.write_bytes(b'preserve')
   for i,p in enumerate(inputs):
    sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard)
    for out in (p,sym,hard):
     argv=['active','--rom',str(rom),'--language','EN','--objects',str(objects),'--json',str(out)]
     with self.subTest(output=out.name),patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
      with self.assertRaises(SystemExit) as e:m.main()
      self.assertEqual(e.exception.code,2);analyze.assert_not_called();self.assertEqual(p.read_bytes(),b'preserve')
   for out in (objects/'new.json',SOURCE/'new.json'):
    argv=['active','--rom',str(rom),'--language','EN','--objects',str(objects),'--json',str(out)]
    with patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()


@unittest.skipUnless(os.environ.get('SGP_R4_ROM_DIR') and os.environ.get('SGP_REMATCH_OBJECTS_DIR'),'requires exact r4 EN/IT and retained objects from the inert attribution')
class CurrentActiveRematch(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=tool();cls.objects=Path(os.environ['SGP_REMATCH_OBJECTS_DIR']);cls.paths={l:Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%l) for l in ('EN','IT')}
  cls.models={l:cls.m.P.G.S.SHARED.read_current(p,l) for l,p in cls.paths.items()};cls.codes={}
  for l,p in cls.paths.items():
   with p.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:cls.codes[l]=cls.m.attest_objects(raw,cls.models[l],cls.objects)[0]
 def cpu(self,lang='EN',**kw):
  with self.paths[lang].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:return self.m.run(self.models[lang],raw,lang,self.codes[lang],**kw)
 def test_active_native_calls_select_both_authored_parties_and_complete108stores(self):
  for lang in ('EN','IT'):
   for trainer in (712,713):
    for seed in (0x12345678,0x12345679):
     r=self.cpu(lang,trainer=trainer,seed=seed,context=2049);self.m.require_active(r)
     self.assertEqual(r['selected'],(seed^(seed>>16)^trainer)&1);self.assertEqual(len(r['copy']),108)
     self.assertEqual(r['apply']['value'],1+r['selected']);self.assertNotEqual(r['resume']['r'][0],r['apply']['value'])
 def test_gates_and_unselected_corruption_refuse_without_partial_copy(self):
  for gate in self.m.GATES[1:]:
   r=self.cpu(gate=gate);self.m.require_active(r);self.assertEqual(r['copy'],[])
  for seed in (0x12345678,0x12345679):
   for gate in ('unselected_hash','unselected_illegal'):
    r=self.cpu('IT',seed=seed,gate=gate);self.m.require_active(r);self.assertEqual(r['apply']['value'],0)
 def test_equal_output_cannot_hide_copy107_and_seed_cannot_hide_other_variant(self):
  for lang in ('EN','IT'):
   for gate in ('partial_copy','wrong_seed'):
    r=self.cpu(lang,gate=gate)
    if gate=='partial_copy':
     self.assertEqual(r['buffer_sha256'],self.m.P.sha(self.m.authored(712,'A')));self.assertEqual(len(r['copy']),107)
    self.assertEqual(r['resume']['r'][0],self.m.B.LOADER_RESULT);self.assertEqual(r['registry'][0],(126,0));r['gate']='current'
    with self.assertRaises(ValueError):self.m.require_active(r)
 def test_oracle_rejects_missing_store_wrong_byte_seed_callee_return_and_lifetime(self):
  r=self.cpu();self.m.require_active(r);mutants=[]
  for path in (('reader_calls',),('unload_calls',),('seed_after',),('wfc_counter',),('resume','sp'),('resume','r',0),('resume','r',1),('resume','r',2),('resume','r',4),('resume','r',11),('apply','value'),('apply','stack',0),('apply','return_sp'),('apply','return_saved',0),('copy',3,'index'),('copy',3,'value')):
   x=copy.deepcopy(r);v=x
   for k in path[:-1]:v=v[k]
   v[path[-1]]^=1;mutants.append((str(path),x))
  for field in ('copy','baseline_reads','code','critical','models','registry'):
   x=copy.deepcopy(r);x[field]=x[field][:-1] if field in ('copy','baseline_reads') else [];mutants.append((field,x))
  x=copy.deepcopy(r);x['buffer_sha256']='wrong';mutants.append(('buffer',x))
  x=copy.deepcopy(r);x['selected']^=1;mutants.append(('selector',x))
  for field in ('canaries','stack_canary'):
   x=copy.deepcopy(r);x[field]=False;mutants.append((field,x))
  for field in ('instructions','max_stack'):
   x=copy.deepcopy(r);x[field]=300001;mutants.append((field,x))
  for label,x in mutants:
   with self.subTest(label=label),self.assertRaises(ValueError):self.m.require_active(x)
 def test_read_write_bounds_invalid_domains_and_retained_object_drift_refused(self):
  m=self.m
  with self.paths['EN'].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   b=m.P.Adapter(self.models['EN'],raw,'EN');b.module_code=self.codes['EN'];a=m.Active(b,712)
   u=a.factory(1,16);u.mem_map(0x02000000,0x400000);a.native_seen=True;u.reg_write(m.P.UC_ARM_REG_PC,0x226B180)
   for index,address,width in ((108,m.B.ARENA+108,1),(2,m.B.ARENA+2,1),(0,m.B.ARENA+1,1),(0,m.B.ARENA,4)):
    u.reg_write(m.B.R[1],index)
    with self.assertRaises(ValueError):a.write(u,0,address,width,0,None)
   u.reg_write(m.P.UC_ARM_REG_PC,0x226B00C)
   with self.assertRaisesRegex(ValueError,'module read outside'):a.read(u,0,0x2390000,4,0,None)
   with tempfile.TemporaryDirectory() as td:
    p=Path(td)
    for n in ('rematch-variants.o','rematch-stub.o'):(p/n).write_bytes((self.objects/n).read_bytes())
    q=p/'rematch-variants.o';data=bytearray(q.read_bytes());data[-1]^=1;q.write_bytes(data)
    with self.assertRaisesRegex(ValueError,'ELF input identity'):m.attest_objects(raw,self.models['EN'],p)
  for kw in (dict(trainer=0),dict(seed=0),dict(plus=3),dict(context=2),dict(gate='ambiguous')):
   with self.subTest(kw=kw),self.assertRaises(ValueError):self.cpu(**kw)


if __name__=='__main__':unittest.main()
