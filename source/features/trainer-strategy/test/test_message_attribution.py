"""Portable guards and CPU-free replay of private native-message receipts."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,sys,tempfile,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 spec=importlib.util.spec_from_file_location('native_messages',SOURCE/'features/trainer-strategy/tools/attribuisci_messaggi.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Portable(unittest.TestCase):
 def test_domain_before_cpu(self):
  m=tool()
  for trainer,kwargs in ((True,{}),(0,{}),(21,dict(heap_fill=True)),(21,dict(heap_fill=1)),(21,dict(void_return=True)),(21,dict(observe=1)),(21,dict(variant='other'))):
   with patch.object(m,'Uc') as cpu,self.assertRaises(ValueError):m.Message(None,None,None,trainer,**kwargs)
   cpu.assert_not_called()
 def test_existing_alias_and_source_outputs_refused(self):
  m=tool()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);rom=root/'own.nds';rom.write_bytes(b'unchanged');sym=root/'link';sym.symlink_to(rom);hard=root/'hard';os.link(rom,hard)
   for out in (rom,sym,hard,SOURCE/'new-message.json'):
    args=['message','--rom',str(rom),'--retail',str(rom),'--base',str(rom),'--v4',str(rom),'--language','EN','--json',str(out)]
    with patch.object(sys,'argv',args),patch.object(m,'analyze') as analyze,self.assertRaises(SystemExit) as e:m.main()
    self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   self.assertEqual(rom.read_bytes(),b'unchanged')

@unittest.skipUnless(os.environ.get('SGP_MESSAGE_ROM_DIR') and os.environ.get('SGP_MESSAGE_REPORT_DIR'),'requires private exact ROMs and native-message reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=m=tool();cls.reports={};cls.data={};cls.code={}
  for lang in ('EN','IT'):
   path=Path(os.environ['SGP_MESSAGE_ROM_DIR'])/('r4-'+lang+'.nds');model=m.P.G.S.SHARED.read_image(path,lang,'r4')
   with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:cls.code[lang],_=m.qualify(model,raw);cls.data[lang]=m.resources(raw)
   raw=(Path(os.environ['SGP_MESSAGE_REPORT_DIR'])/('messages-'+lang+'.json.gz')).read_bytes();r=json.loads(gzip.decompress(raw));assert r['schema']=='trainer-native-message-v1' and r['input']==json.loads(json.dumps(model['record'])) and r['resources']==cls.data[lang]['oracle'];cls.reports[lang]=r
 def base(self,lang='EN'):return copy.deepcopy(self.reports[lang]['cases'][0]['result'])
 def require(self,r,lang='EN'):self.m.require_case(r,self.data[lang],self.code[lang])
 def test_matrix_and_void_controls(self):
  for lang,r in self.reports.items():
   self.assertEqual([(c['result']['trainer'],c['result']['heap_fill']) for c in r['cases']],[(t,f) for t in (21,31) for f in (0,0xC7,0x39)])
   for c in r['cases']:
    self.require(c['result'],lang)
    if c['result']['heap_fill']==0:self.assertEqual(c['off_neutral']['native_write_records'],0)
   self.assertEqual([c['void_return'] for c in r['void_controls']],[0,0xFFFFFFFF])
   for c in r['void_controls']:self.require(c,lang)
 def test_spare_is_heap_fill_but_output_stable(self):
  for r in self.reports.values():
   for offset in (0,3):
    cells=[x['result'] for x in r['cases'][offset:offset+3]];self.assertEqual(len({x['destination_hex'] for x in cells}),1)
    self.assertEqual([x['string_snapshot'][-4:] for x in cells],['0000','c7c7','3939'])
 def test_missing_native_or_modeled_evidence_rejected(self):
  for key in ('api','models','native_helpers','native_writes','observed_pcs','allocations'):
   r=self.base();r[key]=r[key][:-1]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_forged_stack_writes_and_interleaving_rejected(self):
  for mode in ('unqualified','cross_top','duplicate','interleave','stack_value'):
   r=self.base();w=copy.deepcopy(r['native_writes'][0])
   if mode=='unqualified':w['pc']='0xdeadbeef'
   if mode=='cross_top':w['address']=self.m.TOP-1
   if mode=='stack_value':r['native_writes'][0]['value']^=1
   elif mode=='interleave':r['native_writes'][6],r['native_writes'][7]=r['native_writes'][7],r['native_writes'][6]
   else:r['native_writes'].append(w)
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.require(r)
 def test_cipher_read_abi_and_hash_bound_to_raw(self):
  for field,value in (('destination',0),('offset',1),('bytes',1),('delivered_sha256','0'*64),('lr','0x200ba13')):
   r=self.base();r['models'][2][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.require(r)
 def test_native_pointer_results_and_callee_saved(self):
  for i in range(5):
   r=self.base();r['native_helpers'][i]['return_saved'][0]^=1
   with self.assertRaises(ValueError):self.require(r)
   r=self.base();r['native_helpers'][i]['return_saved'][0]^=1;r['native_helpers'][i]['saved'][0]^=1
   with self.assertRaises(ValueError):self.require(r)
  for i in (0,1,3,4):
   r=self.base();r['native_helpers'][i]['result_r0']^=1
   with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['native_helpers'][2]['result_r0']=0;self.require(r)
 def test_no_void_r0_status_inference(self):
  r=self.base()
  for i in (2,3,6,7,8,9,10):r['models'][i]['result_r0']=0xFFFFFFFF
  for i in (2,3,4):r['api'][i]['after'][0]=0xFFFFFFFF
  self.require(r)
 def test_lifetime_and_return_checkpoints(self):
  for key,value in (('canaries',False),('temp_deleted',False),('dead_store',False),('handle_live',True),('rng_after',0)):
   r=self.base();r[key]=value
   with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['api'][1]['live']={}
  with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['api'][3]['after'][13]-=8
  with self.assertRaises(ValueError):self.require(r)
 def test_executed_counters_and_expected_failure_cause(self):
  for lang,r in self.reports.items():
   self.m.require_counters(r['counters'],self.data[lang],self.code[lang])
   for i in range(9):
    counters=copy.deepcopy(r['counters']);counters[i]['rejection']='unrelated preflight failure'
    with self.subTest(lang=lang,index=i),self.assertRaises(ValueError):self.m.require_counters(counters,self.data[lang],self.code[lang])

if __name__=='__main__':unittest.main()
