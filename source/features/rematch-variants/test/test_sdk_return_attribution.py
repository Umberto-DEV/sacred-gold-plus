"""R0 liveness at modeled void boundaries, independent reread and calibrated observation."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,struct,sys,tempfile,unittest
from unittest.mock import patch,Mock
SOURCE=Path(__file__).resolve().parents[3]


def tool():
 s=importlib.util.spec_from_file_location('sdk_return_attribution',SOURCE/'features/rematch-variants/tools/attribuisci_sdk_void.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class SDKReturnPortable(unittest.TestCase):
 def test_capture_output_preserves_inputs_aliases_and_source(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);obj=root/'objects';obj.mkdir();inputs=[root/'r4.nds',obj/'rematch-variants.o',obj/'rematch-stub.o',root/'teams.o'];targets=[SOURCE/'forbidden-new.json',obj/'forbidden-new.json']
   for i,p in enumerate(inputs):
    p.write_bytes(b'preserve');sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);targets.extend((p,sym,hard))
   for out in targets:
    argv=['sdk','--rom',str(inputs[0]),'--objects',str(obj),'--strategy-object',str(inputs[-1]),'--language','EN','--json',str(out)]
    with patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')
 def test_readback_output_preserves_inputs_and_expanded_gzip_is_bounded(self):
  m=tool();r=m.R
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);inputs=[root/'r4.nds',root/'record.json.gz'];targets=[SOURCE/'forbidden-new.json']
   for i,p in enumerate(inputs):
    p.write_bytes(b'preserve');sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);targets.extend((p,sym,hard))
   for out in targets:
    argv=['reader','--rom',str(inputs[0]),'--report',str(inputs[1]),'--language','EN','--json',str(out)]
    with patch.object(sys,'argv',argv),patch.object(r,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:r.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   bomb=root/'expanded.json.gz';bomb.write_bytes(gzip.compress(b'x'*(16*1024*1024+1)))
   with patch.object(r.P.G.S.SHARED,'read_current',return_value={'record':{}}),self.assertRaisesRegex(ValueError,'expanded input budget'):r.analyze(inputs[0],'EN',bomb)
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')
 def test_projection_ignores_only_void_r0_logs(self):
  m=tool();base=dict(mon_hex=['same encrypted guest record'],models=[dict(name='Heap_Free',result=12),dict(name='GetSpeciesName',result=34)],first=dict(models=[dict(name='Heap_Free',result=12)],guest='unchanged'),first_receipt_sha256='original')
  a=m.neutrality_signature(base);b=copy.deepcopy(base);b['models'][0]['result']=0;b['first']['models'][0]['result']=0;self.assertEqual(a,m.neutrality_signature(b));self.assertEqual(a,m.R.neutrality_signature(b))
  b['models'][1]['result']^=1;self.assertNotEqual(a,m.neutrality_signature(b));b=copy.deepcopy(base);b['mon_hex'][0]='changed';self.assertNotEqual(a,m.neutrality_signature(b))
 def test_arm_predicates_match_actual_isolated_instruction_execution(self):
  m=tool();from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
  from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_CPSR
  from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
  u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x1000,0x1000);cs=Cs(CS_ARCH_ARM,CS_MODE_ARM);cs.detail=True
  for condition in range(15):
   # ARMv5 ADD{condition} r0,r1,#1: writes r0 only if its predicate executes.
   blob=struct.pack('<I',(condition<<28)|0x02810001);u.mem_write(0x1000,blob);u.ctl_remove_cache(0x1000,0x1004);ins=next(cs.disasm(blob,0x1000))
   for flags in range(16):
    u.reg_write(UC_ARM_REG_R0,7);u.reg_write(UC_ARM_REG_R1,123);u.reg_write(UC_ARM_REG_CPSR,(u.reg_read(UC_ARM_REG_CPSR)&0x0FFFFFFF)|(flags<<28));status=u.reg_read(UC_ARM_REG_CPSR);predicted=m.condition(ins.cc,status);u.emu_start(0x1000,0x1004,count=1)
    self.assertEqual(u.reg_read(UC_ARM_REG_R0),124 if predicted else 7,(condition,flags))
  with self.assertRaises(ValueError):m.condition(999,0)
 def test_defined_returns_are_not_poisoned_and_other_poisoning_is_refused(self):
  m=tool();o=m.Observer.__new__(m.Observer);o.pending_confirmation=None;o.mon=True;o.poison=True
  with self.assertRaisesRegex(ValueError,'poisoning OFF'):o.step(None,0x1234,2,None)
  o.poison=False;o.pending_service=dict(name='Heap_Alloc',return_pc=0x1234);o.return_mode='zero';o.taint=None;o.diagnostic=False;u=Mock()
  with patch.object(m.F.Full,'step',return_value=None):o.step(u,0x1234,2,None)
  u.reg_write.assert_not_called()


@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_R4_ROM_DIR','SGP_REMATCH_OBJECTS_DIR','SGP_STRATEGY_OBJECT','SGP_COMPLETE_REPORT_DIR')),'requires exact ROMs,objects and preceding complete-constructor reports')
class SDKReturnCurrent(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  m=cls.m=tool();cls.paths={};cls.models={};cls.codes={};cls.data={};cls.templates={};cls.baselines={};cls.cache={}
  for lang in ('EN','IT'):
   p=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%lang);model=m.P.G.S.SHARED.read_current(p,lang);cls.paths[lang]=p;cls.models[lang]=model;m.F.attest_recipe_sources();m.M.attest_post_form(model)
   report=Path(os.environ['SGP_COMPLETE_REPORT_DIR'])/(os.environ.get('SGP_COMPLETE_REPORT_NOME','complete-%s.json.gz')%lang);content=gzip.decompress(report.read_bytes()) if report.suffix=='.gz' else report.read_bytes();baseline=json.loads(content);assert baseline['schema']=='rematch-complete-constructor-v1' and baseline['input']==json.loads(json.dumps(model['record']));cls.baselines[lang]=baseline['positives']
   with p.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
    prefix,_=m.F.A.attest_objects(raw,model,Path(os.environ['SGP_REMATCH_OBJECTS_DIR']));proof=m.M.attest_strategy_object(model,raw,Path(os.environ['SGP_STRATEGY_OBJECT']));cls.codes[lang]=(prefix,m.C.qualify_code(model,proof),*m.M.qualify(model,lang),*m.F.qualify(model,lang));cls.data[lang]=m.F.resources(raw,model);templates,diag,_=m.R.raw_templates(raw,model,lang);cls.templates[lang]=(templates,diag)
    for r in baseline['positives']:m.F.require_complete(r,cls.data[lang])
 def cpu(self,lang='EN',trainer=713,seed=0x12345678,mode='observe'):
  key=lang,trainer,seed,mode
  if key not in self.cache:
   with self.paths[lang].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:self.cache[key]=self.m.run_case(self.models[lang],raw,lang,self.codes[lang],trainer,seed,mode)
  return self.cache[key]
 def require(self,r,lang='EN',diagnostic=False):return self.m.R.require_capture(r,self.data[lang],*self.templates[lang],allow_diagnostic=diagnostic)
 def test_observer_off_is_identical_to_all_eight_prior_complete_receipts(self):
  for lang in ('EN','IT'):
   index=0
   for trainer in (712,713):
    for seed in (0x12345678,0x12345679):
     r=self.cpu(lang,trainer,seed);self.require(r,lang);self.assertEqual(json.loads(json.dumps(r['full'])),self.baselines[lang][index]);index+=1
 def test_zero_and_ones_change_only_unspecified_void_return_logs(self):
  for lang in ('EN','IT'):
   normal=self.cpu(lang)
   for mode in ('zero','ones'):
    r=self.cpu(lang,mode=mode);self.require(r,lang);self.assertEqual(r['neutrality_signature'],normal['neutrality_signature']);self.assertEqual(r['full']['mon_hex'],normal['full']['mon_hex']);self.assertEqual(r['full']['end'],normal['full']['end'])
    self.assertTrue(all(e['overwrite_confirmed'] for e in r['events']))
 def test_actual_live_r0_calibrates_read_detection_with_identical_guest_output(self):
  r=self.cpu(mode='diagnostic');self.require(r,diagnostic=True);self.assertEqual(r['counts']['read_before_write'],1);self.assertEqual(json.loads(json.dumps(r['full'])),json.loads(json.dumps(self.cpu()['full'])))
  with self.assertRaises(ValueError):self.require(dict(r,mode='observe'))
 def test_independent_reader_refuses_missing_events_false_paths_and_wrong_return_bindings(self):
  m=self.m;r=self.cpu();mutants=[]
  for field,value in (('events',[]),('counts',{}),('neutrality_signature','wrong'),('mode','ones')):
   x=copy.deepcopy(r);x[field]=value;mutants.append((field,x))
  for key,value in (('rpc','0x2073a88'),('sp',0),('injected_r0',0),('outcome','overwritten_before_read_but_unverified'),('overwrite_confirmed',False),('post_instruction_pc','0x0'),('non_r0_regs_unchanged',False),('r0_before_final_instruction',0)):
   x=copy.deepcopy(r);x['events'][0][key]=value;mutants.append((key,x))
  x=copy.deepcopy(r);x['events'][0]['path'][0]['reads_r0']=True;mutants.append(('instruction reads',x));x=copy.deepcopy(r);x['events'][0]['path'][-1]['writes_r0']=False;mutants.append(('instruction kill',x));x=copy.deepcopy(r);x['events'][0]['path']=[];mutants.append(('missing path',x));x=copy.deepcopy(r);x['events'].pop();mutants.append(('missing last service',x))
  for name,x in mutants:
   with self.subTest(name=name),self.assertRaises(ValueError):self.require(x)
  with tempfile.TemporaryDirectory() as td,self.paths['EN'].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   original=json.loads(m.R.WINDOWS.read_text())
   for label in ('bytes','return','diagnostic'):
    q=copy.deepcopy(original)
    if label=='bytes':q['windows'][0]['steps'][0]['sha256']='0'*64
    elif label=='return':next(x for x in q['windows'] if x['return_bindings'])['return_bindings'][0]['function_entry']='0x0'
    else:q['diagnostic']['read_pc']='0x206de3a'
    path=Path(td)/(label+'.json');path.write_text(json.dumps(q))
    with patch.object(m.R,'WINDOWS',path),self.assertRaises(ValueError):m.R.raw_templates(raw,self.models['EN'],'EN')


if __name__=='__main__':unittest.main()
