"""Exact-input replay and counter-receipt falsifiers; no CPU execution."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_lettore_prefisso.py';s=importlib.util.spec_from_file_location('prefix_replay',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_PREFIX_CALLER_ROM_DIR','SGP_PREFIX_CALLER_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')),'requires private exact ROMs, objects and reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.z=z=tool();cls.reports={};cls.data={};cls.q={}
  for lang in os.environ.get('SGP_PREFIX_CALLER_LANGUAGES','EN,IT').split(','):
   rom=Path(os.environ['SGP_PREFIX_CALLER_ROM_DIR'])/('r4-'+lang+'.nds');model=z.P.G.S.SHARED.read_current(rom,lang)
   with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
    q,proof=z.qualify(model,raw,lang,Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+lang),Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+lang)/'teams.o');data=dict(preparation=z.Q.resources(raw),constructor=z.T.resources(model,raw,lang,trainer=31),message=z.V.M.resources(raw),names=z.X.W.resources(raw),header=z.R.resources(raw))
   with gzip.open(Path(os.environ['SGP_PREFIX_CALLER_REPORT_DIR'])/('prefix-caller-'+lang+'.json.gz'),'rb') as f:payload=f.read(32*1024**2+1)
   assert len(payload)<=32*1024**2;r=json.loads(payload);assert r['schema']=='trainer31-native-prefix-caller-v1' and r['input']==json.loads(json.dumps(model['record'])) and r['source_sha256']==z.source_identities() and r['proof']==json.loads(json.dumps(proof)) and r['recipes']==z.RECIPES and r['counter_recipe']==z.COUNTER_RECIPE;assert r['prefix_hook_source_contract']==z.Y.prefix_hook_contract(data,q) and r['resources']['party_reader']==data['header']['56']['oracle'];cls.reports[lang]=r;cls.data[lang]=data;cls.q[lang]=q
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['positives'][0])
 def require(self,r):
  lang=next(iter(self.reports));self.z.require_case(r,self.data[lang],self.q[lang])
 def test_all_positive_matrices(self):
  for lang,r in self.reports.items():
   self.assertEqual(tuple(len(r[k]) for k in ('positives','guards','volatile_controls','observer_off','counters')),(4,1,1,2,2))
   for p in r['positives']+r['guards']+r['volatile_controls']:self.z.require_case(p,self.data[lang],self.q[lang]);self.assertEqual(len(p['ctor_read_dispatch']),187+2*p['plus']);self.assertEqual(p['prefix_reader']['instructions'],118)
 def test_actual_prefix_abi_and_frame_transcript(self):
  for key in ('entry','models','native_writes','stack_frame_hex','stack_frame_before','same_cpu','destination_before','rng_after'):
   r=self.base();p=r['prefix_reader']
   if key=='entry':p[key][12]^=1
   elif key in ('models','native_writes'):p[key]=p[key][:-1]
   elif key in ('stack_frame_hex','stack_frame_before'):p[key]='00'*136
   elif key=='same_cpu':p[key]=False
   elif key=='destination_before':p[key]='a5'*108
   else:p[key]^=1
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_binding_and_actual_seam_handback(self):
  for key in ('neutral','regs','ram','canaries','seam'):
   r=self.base();b=r['prefix_binding']
   if key=='neutral':b[key]=False
   elif key=='regs':b[key][14]^=2
   elif key=='ram':b['ram_sha256']='0'*64
   elif key=='canaries':b['canary_preimages']=[]
   else:r['prefix_handback']['regs'][0]=self.z.B.LOADER_RESULT
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_no_fake_high_level_party_read(self):
  for key in ('events','prefix_models','dispatch'):
   r=self.base()
   if key=='events':r['events'].insert(2,['read',56,31,self.z.DEST,108])
   elif key=='prefix_models':r['body'][key].insert(8,dict(name='ReadWholeNarcMemberByIdPair'))
   else:r['ctor_read_dispatch'].append(r['ctor_read_dispatch'][0])
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_off_and_counters(self):
  for lang,r in self.reports.items():
   for off in r['observer_off']:
    on=next(p for p in r['positives'] if p['plus']==off['result']['plus'] and p['seed']==off['result']['seed']);self.assertEqual(self.z.require_off_pair(on,off['result']),off['proof'])
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:self.z.require_counter(c,normal,self.data[lang],self.q[lang])
 def test_off_binding_forgery_rejected(self):
  report=next(iter(self.reports.values()));off=report['observer_off'][0]['result'];on=next(p for p in report['positives'] if p['plus']==off['plus'] and p['seed']==off['seed'])
  for key in ('neutral','regs','canary_preimages','ram_sha256','prefix_clobber','projected'):
   bad=copy.deepcopy(off)
   if key=='neutral':bad['prefix_binding'][key]=False
   elif key=='regs':bad['prefix_binding'][key][0]^=1
   elif key=='canary_preimages':bad['prefix_binding'][key]=[]
   elif key=='ram_sha256':bad['prefix_binding'][key]='0'*64
   elif key=='prefix_clobber':bad[key]=True
   else:bad['prefix_reader']['projected_ram_sha256']='0'*64
   with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_off_pair(on,bad)
 def test_same_payload_short_read_still_rejected(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678);c=next(c for c in r['counters'] if c['variant']=='prefix_short_read');p=c['result']['prefix_reader'];self.assertEqual(p['destination_hex'],normal['prefix_reader']['destination_hex']);self.assertEqual(p['models'][13]['delivered_bytes'],107);self.assertEqual(c['result']['mon_hex'],normal['mon_hex']);bad=copy.deepcopy(c);bad['result']['prefix_reader']['models'][13]['delivered_bytes']=108
   with self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
 def test_counter_missing_execution_evidence_rejected(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:
    for field in ('names','ctor_read_dispatch','message','instructions'):
     bad=copy.deepcopy(c);p=bad['result']
     if field=='message':p['message']['models']=p['message']['models'][:-1]
     else:p[field]=p[field][:-1] if isinstance(p[field],list) else p[field]+1
     with self.subTest(variant=c['variant'],field=field),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
if __name__=='__main__':unittest.main()
