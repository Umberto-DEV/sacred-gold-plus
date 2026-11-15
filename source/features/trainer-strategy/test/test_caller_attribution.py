"""Complete caller receipt replay, metadata counterproofs and CPU hook calibration."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,struct,sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 s=importlib.util.spec_from_file_location('complete_caller',SOURCE/'features/trainer-strategy/tools/attribuisci_chiamante.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class Portable(unittest.TestCase):
 def test_native_caller_lineage_has_no_retail_it_address_alias(self):
  s=importlib.util.spec_from_file_location('caller_lineage',SOURCE/'features/trainer-strategy/tools/rileggi_provenienza.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with patch.object(m.P.G,'piece') as read:
   result=m.native_caller({},None,'IT','retail');self.assertFalse(result['attributed']);read.assert_not_called()
 def test_native_caller_lineage_separates_logical_physical_and_unknown_bytes(self):
  s=importlib.util.spec_from_file_location('caller_lineage',SOURCE/'features/trainer-strategy/tools/rileggi_provenienza.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);payload=b'own synthetic fixture'.ljust(176,b'.');view=SimpleNamespace(read=lambda a,n:payload,offset=lambda a,n:0x773C0)
  with patch.object(m.P.G,'piece',return_value=payload),patch.object(m.P.G.S.SHARED.gifts_audit,'Arm9View',return_value=view),patch.object(m,'CALLER_SHA256',m.P.sha(payload)):
   for role in ('retail','base11','v4','r4'):
    result=m.native_caller(dict(segments=[]),None,'EN',role);self.assertTrue(result['attributed']);self.assertEqual(result['rom_offset'],None if role in ('retail','base11') else '0x773c0')
   view.read=lambda a,n:b'X'*176
   with self.assertRaisesRegex(ValueError,'raw caller readback'):m.native_caller(dict(segments=[]),None,'EN','r4')
  with patch.object(m.P.G,'piece',return_value=payload):self.assertFalse(m.native_caller(dict(segments=[]),None,'EN','base11')['attributed'])
 def test_source_output_alias_and_retained_object_directory_protection(self):
  m=tool()
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);objects=root/'objects';objects.mkdir();strategy=root/'strategy';strategy.mkdir();rom=root/'own.nds';elf=strategy/'teams.o';inputs=(rom,elf,objects/'rematch-variants.o',objects/'rematch-stub.o')
   for p in inputs:p.write_bytes(b'untouched')
   outputs=[SOURCE/'new.json',objects/'new.json',strategy/'new.json']
   for i,p in enumerate(inputs):
    sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);outputs.extend((p,sym,hard))
   for out in outputs:
    argv=['caller','--rom',str(rom),'--objects',str(objects),'--strategy-object',str(elf),'--language','EN','--json',str(out)]
    with patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze,self.assertRaises(SystemExit) as e:m.main()
    self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'untouched')
 def test_optimized_python_is_refused_before_inherited_sdk_assertions(self):
  m=tool()
  with patch.object(m.sys,'flags',type('Flags',(),dict(optimize=1))()),patch.object(m.T,'bench_image') as image,self.assertRaisesRegex(ValueError,'without Python -O'):m.run_case(None,None,None,None,None)
  image.assert_not_called()
 def test_synthetic_bl_boundary_has_equal_semantics_and_distinct_hook_granularity(self):
  from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_HOOK_CODE
  from unicorn.arm_const import UC_CPU_ARM_946,UC_CPU_ARM_CORTEX_A15,UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_R4,UC_ARM_REG_CPSR
  streams={}
  for model in (UC_CPU_ARM_CORTEX_A15,UC_CPU_ARM_946):
   for address in (0x20003FC,0x20003FE):
    u=Uc(UC_ARCH_ARM,UC_MODE_THUMB);u.ctl_set_cpu_model(model);u.mem_map(0x2000000,4096);delta=0x2000800-address-4;u.mem_write(address,struct.pack('<HH',0xF000|((delta>>12)&2047),0xF800|((delta>>1)&2047)));u.mem_write(0x2000800,b'\x70\x47');u.reg_write(UC_ARM_REG_CPSR,0x3F);u.reg_write(UC_ARM_REG_SP,0x2000F00);u.reg_write(UC_ARM_REG_LR,0x2000E01);u.reg_write(UC_ARM_REG_R4,0x44444405);stream=[];u.hook_add(UC_HOOK_CODE,lambda cpu,a,n,_:stream.append((a,n)))
    u.emu_start(address|1,address+4,count=10);self.assertEqual((u.reg_read(UC_ARM_REG_PC),u.reg_read(UC_ARM_REG_LR),u.reg_read(UC_ARM_REG_SP),u.reg_read(UC_ARM_REG_R4),u.reg_read(UC_ARM_REG_CPSR)),(address+4,(address+4)|1,0x2000F00,0x44444405,0x3F));streams[(model,address)]=stream
  self.assertEqual([n for a,n in streams[(UC_CPU_ARM_CORTEX_A15,0x20003FE)]],[4,2]);self.assertEqual(streams[(UC_CPU_ARM_946,0x20003FE)],[(0x20003FE,2),(0x2000400,2),(0x2000800,2)]);self.assertEqual([n for a,n in streams[(UC_CPU_ARM_946,0x20003FC)]],[4,2])

@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_CALLER_ROM_DIR','SGP_CALLER_OBJECTS_DIR','SGP_CALLER_STRATEGY_DIR','SGP_CALLER_REPORT_DIR')),'requires private exact ROMs,retained objects and caller reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=tool();m=cls.m;cls.reports={};cls.data={};cls.qualified={};cls.cases={}
  for language in os.environ.get('SGP_CALLER_LANGUAGES','EN,IT').split(','):
   path=Path(os.environ['SGP_CALLER_ROM_DIR'])/('r4-'+language+'.nds');model=m.P.G.S.SHARED.read_current(path,language);objects=Path(os.environ['SGP_CALLER_OBJECTS_DIR'])/('public-build-'+language);strategy=Path(os.environ['SGP_CALLER_STRATEGY_DIR'])/('build-'+language)/'teams.o'
   with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:qualified,_=m.qualify(model,raw,language,objects,strategy);data=dict(preparation=m.Q.resources(raw),constructor=m.T.resources(model,raw,language,trainer=31))
   report_path=Path(os.environ['SGP_CALLER_REPORT_DIR'])/(os.environ.get('SGP_CALLER_REPORT_NAME','caller-%s.json.gz')%language)
   with gzip.open(report_path,'rb') as f:payload=f.read(32*1024*1024+1)
   assert len(payload)<=32*1024*1024;report=json.loads(payload);assert report['input']==json.loads(json.dumps(model['record']));cls.reports[language]=report;cls.data[language]=data;cls.qualified[language]=qualified;cls.cases[language]=[report['result']] if 'result'in report else report['positives']+report['guards']
 def base(self):return copy.deepcopy(next(iter(self.cases.values()))[0])
 def require(self,r):language=r['language'];self.m.require_case(r,self.data[language],self.qualified[language])
 def test_all_native_caller_cases_and_campaign_cardinality(self):
  for language,cases in self.cases.items():
   report=self.reports[language]
   if 'result'not in report:self.assertEqual((len(report['positives']),len(report['guards']),len(report['observer_off']),len(report['counters'])),(4,1,2,7));self.assertEqual(report['coverage'],'finite-full-caller-campaign')
   for case in cases:self.require(case)
 def test_twelve_previously_accepted_metadata_mutations_are_rejected(self):
  for key in ('extra_calls','code','models','prefix_models','events'):
   r=self.base();r['body'][key]=[]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
  for key in ('outer_models','caller_writes'):
   r=self.base();r[key]=[]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
  mutations=(lambda r:r['body']['post_form_calls'][0]['args'].__setitem__(0,0),lambda r:r['body']['capsule_calls'][0]['args'].__setitem__(1,0),lambda r:r['body']['pid_overrides'][0].__setitem__('before_gender',0),lambda r:r['services'][0]['args'].__setitem__(0,0),lambda r:r['prefix'].__setitem__('services',[]))
  for mutate in mutations:
   r=self.base();mutate(r)
   with self.assertRaises(ValueError):self.require(r)
 def test_equal_final_or_value_requires_actual_native_store(self):
  r=self.base();r['or_writes']=[]
  with self.assertRaisesRegex(ValueError,'OR store'):self.require(r)
 def test_message_lifetime_is_independent_of_identical_party_bytes(self):
  for key,value in (('msg_live',True),('string_live',True),('destroy_calls',0),('outer_frees',0)):
   r=self.base();r[key]=value
   with self.assertRaises(ValueError):self.require(r)
 def test_outer_and_nested_api_contexts_cannot_be_swapped(self):
  r=self.base();r['api_calls'][1]['begin']='0x2073605'
  with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['ctor_entry'][13]=self.m.OUTER
  with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['ctor_entry'][4:8]=list(self.m.N.COOKIES[:4])
  with self.assertRaises(ValueError):self.require(r)
 def test_adapter_cpu_and_transition_proofs_are_required(self):
  r=self.base();r['adapter']={}
  with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['cpu_model']=1
  with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['transitions'][0]['neutral']=False
  with self.assertRaises(ValueError):self.require(r)
 def test_complete_packets_and_raw_sdk_read_destinations_are_bound(self):
  r=self.base();r['mon_hex'][0]=r['mon_hex'][0][:-2]
  with self.assertRaises(ValueError):self.require(r)
  r=self.base();event=next(e for e in r['body']['models'] if e['name']=='ReadWholeNarcMemberByIdPair');event['output_pointer']^=4
  with self.assertRaises(ValueError):self.require(r)
 def test_campaign_off_pairs_and_disguised_counter_evidence(self):
  for language,report in self.reports.items():
   if 'result'in report:continue
   for pair in report['observer_off']:
    off=pair['result'];observed=next(r for r in report['positives'] if r['plus']==off['plus'] and r['seed']==off['seed']);self.assertEqual(self.m.require_off_pair(observed,off),pair['proof'])
    bad=copy.deepcopy(off);bad['mon_hex'][0]=bad['mon_hex'][0][:-2]
    with self.assertRaises(ValueError):self.m.require_off_pair(observed,bad)
   for counter in report['counters']:
    if counter['completed']:
     r=copy.deepcopy(counter['result']);r['variant']='current';r['body']['game_shadows']=[]
     with self.assertRaises(ValueError):self.require(r)
    else:self.assertEqual(counter['top_after_exception'],hex(self.m.OUTER));self.assertIn(counter['variant'],('omit_prefix_free','wrong_ctor_sp','phase_mutation'))

if __name__=='__main__':unittest.main()
