"""Replay actual caller preparation with private exact inputs and counterproofs."""
from pathlib import Path
import copy,importlib.util,json,mmap,os,sys,tempfile,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 s=importlib.util.spec_from_file_location('trainer_preparation',SOURCE/'features/trainer-strategy/tools/attribuisci_preparazione.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class Portable(unittest.TestCase):
 def test_domain_is_checked_before_cpu_creation(self):
  m=tool()
  for kwargs in (dict(poison=True),dict(poison=0),dict(observe=1),dict(variant='other')):
   with patch.object(m,'Uc') as cpu,self.assertRaises(ValueError):m.execute(None,None,None,**kwargs)
   cpu.assert_not_called()
 def test_output_alias_and_source_protection(self):
  m=tool()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);rom=root/'own.nds';rom.write_bytes(b'untouched');sym=root/'link';sym.symlink_to(rom);hard=root/'hard';os.link(rom,hard)
   for out in (rom,sym,hard,SOURCE/'new.json'):
    with patch.object(sys,'argv',['prepare','--rom',str(rom),'--language','EN','--json',str(out)]),patch.object(m,'analyze') as analyze,self.assertRaises(SystemExit) as e:m.main()
    self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   self.assertEqual(rom.read_bytes(),b'untouched')

@unittest.skipUnless(os.environ.get('SGP_PREP_ROM_DIR') and os.environ.get('SGP_PREP_REPORT_DIR'),'requires private exact ROMs and caller preparation CLI reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=tool();m=cls.m;cls.reports={};cls.data={};cls.code={}
  for language in ('EN','IT'):
   path=Path(os.environ['SGP_PREP_ROM_DIR'])/('r4-'+language+'.nds');model=m.P.G.S.SHARED.read_current(path,language)
   with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:data=m.resources(raw);code,_=m.qualify(model,raw)
   name=os.environ.get('SGP_PREP_REPORT_NAME','prep-%s.json')%language;report=json.loads((Path(os.environ['SGP_PREP_REPORT_DIR'])/name).read_text());assert report['schema']=='trainer31-caller-preparation-v1' and report['input']==json.loads(json.dumps(model['record'])) and report['resources']==data
   cls.reports[language]=report;cls.data[language]=data;cls.code[language]=code
 def require(self,r,language='EN'):self.m.require_result(r,self.data[language],self.code[language])
 def base(self,language='EN'):return copy.deepcopy(self.reports[language]['cases'][0]['result'])
 def test_all_exact_input_receipts_and_endpoint_scope(self):
  for language,report in self.reports.items():
   self.assertEqual(report['qualified_code_pcs'],128);self.assertEqual(len(report['cases']),2);self.assertEqual(len(report['counters']),8)
   for c in report['cases']:self.assertTrue(c['off_neutral']);self.require(c['result'],language)
 def test_poison_changes_only_declared_stack_derived_fields_in_trainer(self):
  for report in self.reports.values():
   a,b=(bytes.fromhex(c['result']['trainer_hex']) for c in report['cases']);n=2*report['resources']['name']['raw_words'];self.assertEqual(a[:20+n],b[:20+n]);self.assertEqual(a[20+n:],bytes([0xC7])*(32-n));self.assertEqual(b[20+n:],bytes([0x39])*(32-n))
 def test_same_prepared_bytes_require_actual_native_copy_delete_and_service_order(self):
  for field in ('native_calls','copy52','writes','models','services','observed_pcs'):
   r=self.base();r[field]=r[field][:-1]
   with self.subTest(field=field),self.assertRaises(ValueError):self.require(r)
 def test_constructor_entry_is_not_an_api_return_or_body_execution(self):
  for key,value in (('sp',self.m.TOP),('lr',hex(self.m.N.STOP|1)),('pc',hex(self.m.END+2))):
   r=self.base();r['endpoint'][key]=value
   with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['constructor_instruction_executed']=True
  with self.assertRaises(ValueError):self.require(r)
 def test_header_tail_and_name_cannot_be_replaced_by_host_zero_fill(self):
  for field in ('trainer_hex','local_source52','initial_stack_tail_hex'):
   r=self.base();r[field]=r[field][:40]+'00'*32
   with self.subTest(field=field),self.assertRaises(ValueError):self.require(r)
  r=self.base('IT');r['models'][1]['bytes']=52
  with self.assertRaises(ValueError):self.require(r,'IT')
 def test_native_helper_saved_registers_and_pointer_returns(self):
  for index in range(6):
   r=self.base();r['native_calls'][index]['return_saved'][0]^=1
   with self.assertRaises(ValueError):self.require(r)
  for index in (0,1,4):
   r=self.base();r['native_calls'][index]['result_r0']^=1
   with self.assertRaises(ValueError):self.require(r)
  for index in (2,3,5):
   r=self.base();r['native_calls'][index]['result_r0']=0;self.require(r)
 def test_message_is_still_live_and_string_is_dead_before_constructor(self):
  for key,value in (('msg_live',False),('string_live',True),('frees',0),('string_created',False)):
   r=self.base();r[key]=value
   with self.assertRaises(ValueError):self.require(r)

if __name__=='__main__':unittest.main()
