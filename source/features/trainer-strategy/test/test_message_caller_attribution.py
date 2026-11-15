"""CPU-free routing guards for native message/caller composition."""
from pathlib import Path
import importlib.util,types,unittest,tempfile,os,sys,copy,gzip,json,mmap
from unittest.mock import Mock,patch
def tool():
 p=Path(__file__).resolve().parents[1]/'tools/attribuisci_messaggi_chiamante.py';s=importlib.util.spec_from_file_location('message_caller',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.v=tool()
 def test_bound_message_changes_only_observer_stack_origin(self):
  v=self.v;bound=v.bind_message()
  self.assertEqual(v.M.TOP,v.OUTER);self.assertEqual(bound.step.__globals__['TOP'],v.INNER)
  for name,method in vars(v.M.Message).items():
   if isinstance(method,types.FunctionType):self.assertIs(getattr(bound,name).__code__,method.__code__)
 def test_constructor_shared_string_apis_delegate_to_parent(self):
  v=self.v;driver=v.Driver.__new__(v.Driver);driver.message_active=False;driver.message_api=[None]*4;driver.stage='ctor'
  for pc in (0x2026A68,0x2026380):
   with patch.object(v.U.Driver,'step') as parent:driver.step(None,pc,2,None);parent.assert_called_once_with(None,pc,2,None)
 def test_message_sdk_dispatch_exactly_once_and_constructor_backend_unchanged(self):
  v=self.v;driver=v.Driver.__new__(v.Driver);cpu=object();driver.u=cpu;driver.message=types.SimpleNamespace(u=cpu,service=Mock());driver.message_active=True;driver.regs=lambda:list(range(16));driver.pending_sdk=(0x201AA8C,list(range(16)));driver.sync_lifetime=Mock();driver.dispatch=[]
  backends={name:Mock() for name in v.M.SDK.values()};wrapped=driver.configure(cpu,backends,[],{},{});wrapped['Heap_Alloc'](cpu);driver.message.service.assert_called_once_with(0x201AA8C);backends['Heap_Alloc'].assert_not_called()
  with self.assertRaises(ValueError):wrapped['Heap_Alloc'](cpu)
  driver.message_active=False;driver.stage='ctor';wrapped['Heap_Alloc'](cpu);backends['Heap_Alloc'].assert_called_once_with(cpu)
  driver.stage='prefix'
  with self.assertRaises(ValueError):wrapped['Heap_Alloc'](cpu)
 def test_invalid_variant_rejected_before_parent_or_cpu(self):
  v=self.v
  with patch.object(v.U.Driver,'__init__') as parent,self.assertRaises(ValueError):v.Driver(None,None,None,1,0x12345678,variant='other')
  parent.assert_not_called()
 def test_cli_output_alias_source_and_object_protection(self):
  v=self.v
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);rom=root/'own.nds';rom.write_bytes(b'unchanged');objects=root/'objects';objects.mkdir();strategy=root/'strategy';strategy.mkdir();obj=strategy/'teams.o';obj.write_bytes(b'own-object');sym=root/'link';sym.symlink_to(rom);hard=root/'hard';os.link(rom,hard)
   for output in (rom,sym,hard,v.P.SOURCE/'new-caller-message.json',objects/'output.json',strategy/'output.json'):
    args=['caller-message','--language','EN','--rom',str(rom),'--objects',str(objects),'--strategy-object',str(obj),'--json',str(output)]
    with self.subTest(output=str(output)),patch.object(sys,'argv',args),patch.object(v,'analyze') as analyze,self.assertRaises(SystemExit) as e:v.main()
    self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   self.assertEqual(rom.read_bytes(),b'unchanged');self.assertEqual(obj.read_bytes(),b'own-object')
@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_MSG_CALLER_ROM_DIR','SGP_MSG_CALLER_OBJECTS_DIR','SGP_MSG_CALLER_STRATEGY_DIR','SGP_MSG_CALLER_REPORT_DIR')),'requires private exact inputs,retained objects and native-message caller reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.v=v=tool();cls.reports={};cls.data={};cls.qualified={}
  for lang in os.environ.get('SGP_MSG_CALLER_LANGUAGES','EN,IT').split(','):
   path=Path(os.environ['SGP_MSG_CALLER_ROM_DIR'])/('r4-'+lang+'.nds');model=v.P.G.S.SHARED.read_current(path,lang);objects=Path(os.environ['SGP_MSG_CALLER_OBJECTS_DIR'])/('public-build-'+lang);strategy=Path(os.environ['SGP_MSG_CALLER_STRATEGY_DIR'])/('build-'+lang)/'teams.o'
   with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:qualified,_=v.qualify(model,raw,lang,objects,strategy);data=dict(preparation=v.Q.resources(raw),constructor=v.T.resources(model,raw,lang,trainer=31),message=v.M.resources(raw))
   with gzip.open(Path(os.environ['SGP_MSG_CALLER_REPORT_DIR'])/('messages-caller-'+lang+'.json.gz'),'rb') as f:payload=f.read(32*1024**2+1)
   assert len(payload)<=32*1024**2;report=json.loads(payload);assert report['schema']=='trainer31-native-message-caller-v1' and report['input']==json.loads(json.dumps(model['record'])) and report['resources']['message']==data['message']['oracle'];cls.reports[lang]=report;cls.data[lang]=data;cls.qualified[lang]=qualified
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['positives'][0])
 def require(self,r):self.v.require_case(r,self.data[r['language']],self.qualified[r['language']])
 def test_all_campaign_cells_and_native_body_checkpoints(self):
  for r in self.reports.values():
   self.assertEqual((len(r['positives']),len(r['guards']),len(r['observer_off']),len(r['counters'])),(4,1,2,4));self.assertEqual([(x['plus'],x['seed']) for x in r['positives']],[(p,s) for p in (0,1) for s in (0x12345678,0x12345679)])
   for x in r['positives']+r['guards']:self.require(x)
 def test_off_neutrality_and_causal_executed_counter_evidence(self):
  for lang,r in self.reports.items():
   normal=next(x for x in r['positives'] if x['plus']==1 and x['seed']==0x12345678)
   for c in r['observer_off']:
    on=next(x for x in r['positives'] if x['plus']==c['result']['plus'] and x['seed']==c['result']['seed']);self.assertEqual(self.v.require_off_pair(on,c['result']),c['proof'])
   for counter in r['counters']:
    self.v.require_counter(counter,normal,self.data[lang],self.qualified[lang]);bad=copy.deepcopy(counter);bad['rejection']='unrelated preflight error'
    with self.assertRaises(ValueError):self.v.require_counter(bad,normal,self.data[lang],self.qualified[lang])
 def test_message_metadata_and_native_stack_rows_cannot_be_removed(self):
  for key in ('api','models','native_helpers','native_writes','observed_pcs','allocations','dispatch'):
   r=self.base();r['message'][key]=r['message'][key][:-1]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
  r=self.base();r['message']['native_writes'].append(copy.deepcopy(r['message']['native_writes'][0]))
  with self.assertRaises(ValueError):self.require(r)
 def test_native_message_lifetime_through_constructor_not_just_final_name(self):
  for key in ('before','after','string_freed_sha256','temporary_sha256'):
   r=self.base();r['message']['across_constructor'][key]='0'*64
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
  r=self.base();r['message']['across_constructor']['live']={}
  with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['message']['canaries']=False
  with self.assertRaises(ValueError):self.require(r)
 def test_actual_nested_context_is_not_old_modeled_string_or_standalone_cookies(self):
  r=self.base();r['ctor_entry'][6]=self.v.Q.STRING
  with self.assertRaises(ValueError):self.require(r)
  for i in range(5):
   r=self.base();r['message']['api'][i]['before'][4:12]=list(self.v.N.COOKIES)
   with self.subTest(api=i),self.assertRaises(ValueError):self.require(r)
 def test_constructor_only_copied_checks_still_reject_missing_evidence(self):
  for key in ('extra_calls','code','models','prefix_models','events','native_calls','post_form_calls'):
   r=self.base();r['body'][key]=[]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_native_header_stores_or_and_service_must_be_present(self):
  for key in ('caller_writes','or_writes','services','caller_calls','caller_pcs','api_calls','transitions'):
   r=self.base();r[key]=r[key][:-1]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_stack_poison_and_heap_spare_have_distinct_provenance(self):
  for r in self.reports.values():
   normal=next(x for x in r['positives'] if x['plus']==1 and x['seed']==0x12345678);guard=r['guards'][0];self.assertEqual(guard['mon_hex'],normal['mon_hex']);self.assertEqual(guard['message']['snapshots']['string'],normal['message']['snapshots']['string']);self.assertTrue(guard['message']['snapshots']['string'].endswith('c7c7'));self.assertNotEqual(guard['message']['snapshots']['destination'],normal['message']['snapshots']['destination'])
if __name__=='__main__':unittest.main()
