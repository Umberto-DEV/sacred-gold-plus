"""Current type3 strategy caller, exact writes and same-output counterproofs."""
from pathlib import Path
import importlib.util,os,sys,mmap,tempfile,unittest,copy,collections
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]

def tool():
 s=importlib.util.spec_from_file_location('strategy_attribution',SOURCE/'features/trainer-strategy/tools/attribuisci.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class Portable(unittest.TestCase):
 def test_output_cannot_replace_inputs_aliases_or_source(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);objects=root/'objects';objects.mkdir();rom=root/'r4.nds';obj=objects/'teams.o';inputs=(rom,obj)
   for p in inputs:p.write_bytes(b'preserve')
   outputs=[]
   for i,p in enumerate(inputs):
    sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);outputs.extend((p,sym,hard))
   outputs.extend((SOURCE/'new.json',objects/'new.json',root))
   for output in outputs:
    argv=['strategy','--rom',str(rom),'--language','EN','--strategy-object',str(obj),'--json',str(output)]
    with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')


@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_R4_ROM_DIR','SGP_STRATEGY_OBJECT')),'requires exact r4 EN/IT ROMs and retained qualified strategy ELF')
class Current(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  m=cls.m=tool();cls.models={};cls.data={};cls.codes={};cls.paths={};cls.cache={};m.F.attest_recipe_sources()
  for lang in ('EN','IT'):
   p=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%lang);model=m.P.G.S.SHARED.read_current(p,lang);cls.paths[lang]=p;cls.models[lang]=model
   with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
    proof=m.M.attest_strategy_object(model,raw,Path(os.environ['SGP_STRATEGY_OBJECT']));cls.proof=proof;cls.codes[lang]=m.qualify(model,proof);cls.data[lang]=m.resources(raw,model)
 def case(self,lang='EN',trainer=33,plus=1,variant='current',old=False):
  key=lang,trainer,plus,variant,old
  if key not in self.cache:self.cache[key]=self.m.run_group(self.models[lang],self.codes[lang],self.data[lang],trainer,plus,variant,old=old)
  return self.cache[key]
 def test_seven_plus_normal_buffers_and_old_hook_abi(self):
  for lang in ('EN','IT'):
   for tid in self.m.IDS:
    for plus in (0,1):
     r=self.case(lang,tid,plus);old=self.case(lang,tid,plus,old=True);self.m.require_group(r,self.data[lang]);self.m.require_group(old,self.data[lang]);self.assertEqual([c['regs'] for c in r['calls']],[c['regs'] for c in old['calls']]);self.assertTrue(all(c['sp']==self.m.STACK for c in r['calls']))
 def test_repeats_and_preapplied_counter_keep_same_final_output(self):
  for lang in ('EN','IT'):
   r=self.case(lang);pre=self.case(lang,variant='preapplied');self.m.require_group(pre,self.data[lang]);self.assertEqual(r['final'],pre['final']);self.assertEqual([len(c['output_stores']) for c in r['calls']],[108,0,0,0,0,0]);self.assertEqual([len(c['output_stores']) for c in pre['calls']],[0]*6)
   with self.assertRaises(ValueError):self.m.require_group(dict(pre,variant='current'),self.data[lang])
 def test_late_invalid_delta_is_atomic_and_guards_preserve_buffer(self):
  for lang in ('EN','IT'):
   for variant in ('late_delta','changed_preimage','unknown','plus2','wrong_count'):
    r=self.case(lang,variant=variant);self.m.require_group(r,self.data[lang]);self.assertEqual(r['entry_buffer'],r['final']);self.assertTrue(all(not c['output_stores'] for c in r['calls']))
    if variant=='late_delta':self.assertEqual([len(c['local_delta_stores']) for c in r['calls']],[4]*6)
 def test_result_oracle_rejects_wrong_identity_abi_trace_and_lifetime(self):
  r=self.case();mutants=[]
  for field in ('entry_buffer','final','header'):
   x=copy.deepcopy(r);x[field]='00';mutants.append(x)
  for field in ('pc','sp','nzcv','seed_after','counter_after','slot'):
   x=copy.deepcopy(r);x['calls'][0][field]^=1;mutants.append(x)
  for field in ('regs','entry_regs'):
   x=copy.deepcopy(r);x['calls'][0][field][0]^=1;mutants.append(x)
  for field in ('output_stores','local_delta_stores','helpers','code'):
   x=copy.deepcopy(r);x['calls'][0][field]=[];mutants.append(x)
  for field in ('before','after'):
   x=copy.deepcopy(r);x['calls'][1][field]=r['calls'][0]['before'];mutants.append(x)
  x=copy.deepcopy(r);next(e for e in x['calls'][1]['helpers'] if e['entry']=='0x23d602c')['result'][0]=3;mutants.append(x)
  for entry in ('0x23d6228','0x23d61c4','0x23d8134','0x23d8100'):
   x=copy.deepcopy(r);x['calls'][0]['helpers']=[e for e in x['calls'][0]['helpers'] if e['entry']!=entry];mutants.append(x)
  x=copy.deepcopy(r);x['calls'][0]['local_delta_stores'][0]['address']='0x0';mutants.append(x)
  for x in mutants:
   with self.assertRaises(ValueError):self.m.require_group(x,self.data['EN'])
 def test_code_padding_call_boundary_and_config_drift_are_refused(self):
  m=self.m
  def changed(a):
   out=dict(self.models['EN']);segments=[]
   for base,blob in out['segments']:
    b=bytearray(blob)
    if base<=a<base+len(b):b[a-base]^=1
    segments.append((base,bytes(b)))
   out['segments']=segments;return out
  for address in (0x23D6000,0x23D6244,0x2073718,0x2073802,0x207390C,0x2073A0C,0x2073A10,0x2073A12):
   with self.subTest(address=hex(address)),self.assertRaises(ValueError):m.qualify(changed(address),self.proof)
  with self.paths['EN'].open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
   for a in (0x23D6600,0x23D66A6,0x23D67FF):
    with self.assertRaises(ValueError):m.M.attest_strategy_object(changed(a),raw,Path(os.environ['SGP_STRATEGY_OBJECT']))
 def test_readback_authenticates_inputs_without_instantiating_runtime(self):
  m=self.m
  for lang in ('EN','IT'):
   with patch.object(m,'Hook',side_effect=AssertionError('readback must not construct CPU')):
    r=m.readback(self.paths[lang],lang,Path(os.environ['SGP_STRATEGY_OBJECT']))
   self.assertFalse(r['cpu_executed']);self.assertEqual(len(r['locations']),8);self.assertEqual(r['locations'][0]['bytes'],2048)
   for tid in m.IDS:
    rec=r['resources']['records'][str(tid)];self.assertEqual(rec['header_sha256'],m.P.sha(bytes.fromhex(rec['header'])));self.assertEqual(rec['member_sha256'],rec['spec']['source_sha256'])
 def test_owned_memory_bounds_reject_code_config_and_end_overflow(self):
  m=self.m;h=m.Hook(self.models['EN'],self.codes['EN']);h.output=[];h.local_delta=[];h.write_pcs=collections.Counter();h.read_pcs=collections.Counter();h.cpu.reg_write(m.UC_ARM_REG_PC,0x23D619A)
  for a,n in ((m.BUFFER+107,2),(m.BUFFER-1,1),(m.CONFIG,1),(0x23D6000,2),(m.STACK-513,1),(m.STACK,1)):
   with self.assertRaises(ValueError):h.write(h.cpu,0,a,n,0,None)
  for a,n in ((m.BUFFER+107,2),(m.STACK+127,2),(m.SETUP+1024,1),(0x21D15A8,4)):
   with self.assertRaises(ValueError):h.read(h.cpu,0,a,n,0,None)


if __name__=='__main__':unittest.main()
