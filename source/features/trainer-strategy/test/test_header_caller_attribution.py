"""Private exact-input replay and falsifiers for native header caller ownership."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_lettore_chiamante.py';s=importlib.util.spec_from_file_location('native_header_replay',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@unittest.skipUnless(os.environ.get('SGP_HEADER_CALLER_ROM_DIR') and os.environ.get('SGP_HEADER_CALLER_REPORT_DIR') and os.environ.get('SGP_REMATCH_OBJECT_DIR') and os.environ.get('SGP_STRATEGY_OBJECT_DIR'),'requires private ROMs, retained objects and header-caller reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.y=y=tool();cls.reports={};cls.data={};cls.q={}
  for lang in os.environ.get('SGP_HEADER_CALLER_LANGUAGES','EN,IT').split(','):
   rom=Path(os.environ['SGP_HEADER_CALLER_ROM_DIR'])/('r4-'+lang+'.nds');model=y.P.G.S.SHARED.read_current(rom,lang)
   with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
    q,proof=y.qualify(model,raw,lang,Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+lang),Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+lang)/'teams.o');data=dict(preparation=y.Q.resources(raw),constructor=y.T.resources(model,raw,lang,trainer=31),message=y.V.M.resources(raw),names=y.X.W.resources(raw),header=y.R.resources(raw))
   with gzip.open(Path(os.environ['SGP_HEADER_CALLER_REPORT_DIR'])/('header-caller-'+lang+'.json.gz'),'rb') as f:payload=f.read(32*1024**2+1)
   assert len(payload)<=32*1024**2;report=json.loads(payload);assert report['schema']=='trainer31-native-header-caller-v1' and report['input']==json.loads(json.dumps(model['record'])) and report['source_sha256']==y.source_identities() and report['proof']==json.loads(json.dumps(proof)) and report['recipes']==y.RECIPES and report['prefix_hook_source_contract']==y.prefix_hook_contract(data,q);assert report['resources']['header']==data['header']['55']['oracle'];cls.reports[lang]=report;cls.data[lang]=data;cls.q[lang]=q
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['positives'][0])
 def require(self,r,lang=None):
  lang=lang or next(iter(self.reports));self.y.require_case(r,self.data[lang],self.q[lang])
 def test_matrix_actual_prefix_counts_and_original_model_dispatch(self):
  for lang,r in self.reports.items():
   self.assertEqual((len(r['positives']),len(r['guards']),len(r['volatile_controls']),len(r['observer_off']),len(r['counters'])),(4,1,1,2,2))
   for p in r['positives']+r['guards']+r['volatile_controls']:self.require(p,lang);self.assertEqual(p['ctor_start_steps'],604 if lang=='EN' else 638);self.assertEqual(len(p['ctor_read_dispatch']),188+2*p['plus'])
 def test_header_actual_caller_context_and_frame_provenance(self):
  for key in ('same_cpu','entry','before','after','destination_before','phasehash','rng'):
   r=self.base();h=r['header_reader']
   if key=='same_cpu':h['same_cpu']=False
   elif key=='entry':h['entry'][3]=0x33333303
   elif key=='before':h['caller_frame_before']='00'*96
   elif key=='after':h['caller_frame_after']='00'*96
   elif key=='destination_before':h['destination_before']='a5'*20
   elif key=='rng':h['rng_after']^=1
   else:r['header_binding']['ram_sha256']='0'*64
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_native_header_transcripts_and_full_frame_cannot_be_removed(self):
  for key in ('models','native_writes','observed_pcs'):
   r=self.base();r['header_reader'][key]=r['header_reader'][key][:-1]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
  r=self.base();r['header_reader']['stack_frame_hex']='00'*136
  with self.assertRaises(ValueError):self.require(r)
 def test_every_original_constructor_callback_is_owned_and_bound(self):
  for key in ('owner','stage','args','after','index','return','drop','duplicate'):
   r=self.base();d=r['ctor_read_dispatch'][0]
   if key=='owner':d['owner']='native_header'
   elif key=='stage':d['stage']='prefix'
   elif key=='args':d['before'][2]^=1
   elif key=='after':d['after'][1]^=1
   elif key=='index':d['event_index']+=1
   elif key=='return':d['return_pc']='0x200750a'
   elif key=='drop':r['ctor_read_dispatch']=r['ctor_read_dispatch'][1:]
   else:r['ctor_read_dispatch'].append(d)
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_no_synthetic_old_header_backend_event_or_status(self):
  for key in ('events','services','result'):
   r=self.base()
   if key=='events':r['events'].insert(0,['read',55,31,self.y.Q.LOCAL,20])
   elif key=='services':r['services'].append(dict(name='ReadWholeNarcMemberByIdPair'))
   else:r['caller_calls'][2]['result_r0']=self.y.B.LOADER_RESULT
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_off_and_executed_counter_causes(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for off in r['observer_off']:
    on=next(p for p in r['positives'] if p['plus']==off['result']['plus'] and p['seed']==off['result']['seed']);self.assertEqual(self.y.require_off_pair(on,off['result']),off['proof'])
   for c in r['counters']:self.y.require_counter(c,normal,self.data[lang],self.q[lang])
 def test_coordinated_checkpoint_forgery_rejected_by_source_contract(self):
  lang=next(iter(self.reports));r=self.reports[lang];normal=copy.deepcopy(next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678));counter=copy.deepcopy(next(c for c in r['counters'] if not c['completed']));normal['ctor_start_steps']+=1;counter['instructions']+=1
  with self.assertRaisesRegex(ValueError,'source-bound'):self.y.require_counter(counter,normal,self.data[lang],self.q[lang])
 def test_short_counter_has_actual_cpu_frame_and_incoming_poison(self):
  lang=next(iter(self.reports));r=self.reports[lang];normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
  for key in ('cpu','frame','poison','entry','phase'):
   c=copy.deepcopy(next(c for c in r['counters'] if not c['completed']));h=c['header_reader'];sub=c['header_counter']['result']
   if key=='cpu':h['same_cpu']=sub['same_cpu']=False
   elif key=='frame':h['caller_frame_after']=sub['caller_frame_after']='00'*96
   elif key=='poison':h['destination_before']=sub['destination_before']='a5'*20
   elif key=='entry':c['header_binding']['regs'][3]^=1
   else:c['header_binding']['ram_sha256']='0'*64
   with self.subTest(key=key),self.assertRaises(ValueError):self.y.require_counter(c,normal,self.data[lang],self.q[lang])
 def test_completed_counter_requires_whole_original_execution(self):
  lang=next(iter(self.reports));r=self.reports[lang];normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
  for key in ('dispatch','ram','packet','body','steps'):
   c=copy.deepcopy(next(c for c in r['counters'] if c['completed']));p=c['result']
   if key=='dispatch':p['ctor_read_dispatch']=[]
   elif key=='ram':p['raw_ram_sha256']='0'*64
   elif key=='packet':p['mon_hex'][0]='00'*236
   elif key=='body':p['body']['models']=[]
   else:p['ctor_start_steps']+=1
   with self.subTest(key=key),self.assertRaises(ValueError):self.y.require_counter(c,normal,self.data[lang],self.q[lang])
if __name__=='__main__':unittest.main()
