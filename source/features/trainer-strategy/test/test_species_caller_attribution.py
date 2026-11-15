"""Replay composed native species lifetimes against the developer's own ROMs."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_nomi_chiamante.py';s=importlib.util.spec_from_file_location('species_composed_replay',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@unittest.skipUnless(os.environ.get('SGP_SPECIES_CALLER_ROM_DIR') and os.environ.get('SGP_SPECIES_CALLER_REPORT_DIR') and os.environ.get('SGP_REMATCH_OBJECT_DIR') and os.environ.get('SGP_STRATEGY_OBJECT_DIR'),'requires private exact ROMs, retained objects and composed species reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.x=x=tool();cls.reports={};cls.data={};cls.qualified={}
  for lang in os.environ.get('SGP_SPECIES_CALLER_LANGUAGES','EN,IT').split(','):
   rom=Path(os.environ['SGP_SPECIES_CALLER_ROM_DIR'])/('r4-'+lang+'.nds');model=x.P.G.S.SHARED.read_current(rom,lang)
   with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
    q,proof=x.qualify(model,raw,lang,Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+lang),Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+lang)/'teams.o');data=dict(preparation=x.Q.resources(raw),constructor=x.T.resources(model,raw,lang,trainer=31),message=x.M.resources(raw),names=x.W.resources(raw))
   with gzip.open(Path(os.environ['SGP_SPECIES_CALLER_REPORT_DIR'])/('species-caller-'+lang+'.json.gz'),'rb') as f:payload=f.read(32*1024**2+1)
   assert len(payload)<=32*1024**2;report=json.loads(payload);assert report['schema']=='trainer31-native-species-caller-v1' and report['input']==json.loads(json.dumps(model['record']));assert report['source_sha256']==x.source_identities() and report['recipes']==x.RECIPES and report['proof']==json.loads(json.dumps(proof));assert report['resources']['preparation']==data['preparation'] and report['resources']['names']==data['names']['oracle'] and report['resources']['message']==data['message']['oracle'];cls.reports[lang]=report;cls.data[lang]=data;cls.qualified[lang]=q
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['positives'][0])
 def require(self,r,lang=None):
  lang=lang or next(iter(self.reports));return self.x.require_case(r,self.data[lang],self.qualified[lang])
 def test_complete_matrix_exact_frames_and_instructions(self):
  for lang,r in self.reports.items():
   self.assertEqual((len(r['positives']),len(r['guards']),len(r['observer_off']),len(r['counters'])),(4,1,2,4));self.assertEqual([(p['plus'],p['seed']) for p in r['positives']],[(p,s) for p in (0,1) for s in (0x12345678,0x12345679)])
   for p in r['positives']+r['guards']:self.require(p,lang);self.assertEqual(sum(n['instructions'] for n in p['names']),3098);self.assertEqual(p['max_stack'],608)
 def test_source_bound_species_context_and_destination(self):
  for kind in ('species','heap','saved','r2','otid','destination','prefix'):
   r=self.base();n=r['names'][0]
   if kind in ('species','heap'):n[kind]^=1
   elif kind=='saved':n['api'][0]['before'][5]^=32;n['api'][0]['after'][5]^=32
   elif kind=='r2':n['api'][0]['before'][2]^=1
   elif kind=='otid':n['api'][0]['before'][3]^=1
   elif kind=='destination':n['destination']+=32
   else:n['destination_before']='a5'*22
   with self.subTest(kind=kind),self.assertRaises(ValueError):self.require(r)
 def test_native_api_lifetime_not_only_output(self):
  for key in ('live','handle','native_store','snapshot','return_lr'):
   r=self.base();n=r['names'][0]
   if key=='live':n['api'][0]['live']={}
   elif key=='handle':n['api'][0]['handle_live']=True
   elif key=='native_store':n['writes'][0]['value']^=1
   elif key=='snapshot':n['snapshots']['returned_string']='00'*26
   else:n['api'][0]['before'][14]^=2
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_all_nested_transcripts_are_required(self):
  for key in ('api','internal','models','native_helpers','writes','native_writes','wrapper_writes','observed_pcs','allocations','transitions'):
   r=self.base();r['names'][0][key]=r['names'][0][key][:-1]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_separate_dispatch_and_no_phantom_name_sdk(self):
  for kind in ('dispatch','duplicate','phantom'):
   r=self.base()
   if kind=='dispatch':r['name_dispatch'][0]['owner']='constructor'
   elif kind=='duplicate':r['name_dispatch'].append(r['name_dispatch'][0])
   else:
    phantom=copy.deepcopy(r['body']['models'][0]);phantom.update(name='GetSpeciesName',args=[355,0,0,0]);r['body']['models'].append(phantom)
   with self.subTest(kind=kind),self.assertRaises(ValueError):self.require(r)
 def test_helpers_and_cipher_read_cannot_be_changed(self):
  for key in ('args','saved','return_sp','destination','raw_sha256'):
   r=self.base();n=r['names'][0]
   if key in ('args','saved'):n['native_helpers'][0][key][0]^=1
   elif key=='return_sp':n['native_helpers'][0][key]-=8
   elif key=='destination':n['models'][2][key]+=2
   else:n['models'][2][key]='0'*64
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_off_on_and_executed_counter_causes(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for off in r['observer_off']:
    on=next(p for p in r['positives'] if p['plus']==off['result']['plus'] and p['seed']==off['result']['seed']);self.assertEqual(self.x.require_off_pair(on,off['result']),off['proof'])
   for counter in r['counters']:self.x.require_counter(counter,normal,self.data[lang],self.qualified[lang])
 def test_off_projection_does_not_hide_semantic_context_changes(self):
  lang=next(iter(self.reports));r=self.reports[lang];on=r['positives'][0];off=copy.deepcopy(r['observer_off'][0]['result']);off['names'][0]['api'][0]['before'][3]^=1
  with self.assertRaises(ValueError):self.x.require_off_pair(on,off)
 def test_completed_counter_must_retain_all_names_dispatch_and_step_delta(self):
  lang=next(iter(self.reports));report=self.reports[lang];normal=next(r for r in report['positives'] if r['plus']==1 and r['seed']==0x12345678)
  for kind in ('truncated_names','dispatch','global_steps','models'):
   counter=copy.deepcopy(next(c for c in report['counters'] if c['variant']=='omit_name_free'));r=counter['result']
   if kind=='truncated_names':r['names']=r['names'][-1:]
   elif kind=='dispatch':r['name_dispatch'].append(normal['name_dispatch'][-1])
   elif kind=='global_steps':r['instructions']+=1
   else:r['names'][-1]['models'][0]['args'][0]=11
   with self.subTest(kind=kind),self.assertRaises(ValueError):self.x.require_counter(counter,normal,self.data[lang],self.qualified[lang])
 def test_parent_recipe_and_adapter_receipts_cannot_be_removed(self):
  r=self.base();r['adapter']['effective_sdk']['0x200bcdc']='GetSpeciesName'
  with self.assertRaises(ValueError):self.require(r)
if __name__=='__main__':unittest.main()
