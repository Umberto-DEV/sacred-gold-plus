"""Private input replay and semantic/metadata falsifiers; no CPU execution."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_personale_chiamante.py';s=importlib.util.spec_from_file_location('personal_replay',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_PERSONAL_CALLER_ROM_DIR','SGP_PERSONAL_CALLER_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')),'requires private exact ROMs, objects and reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.z=z=tool();cls.reports={};cls.data={};cls.q={}
  for lang in os.environ.get('SGP_PERSONAL_CALLER_LANGUAGES','EN,IT').split(','):
   rom=Path(os.environ['SGP_PERSONAL_CALLER_ROM_DIR'])/('r4-'+lang+'.nds');model=z.P.G.S.SHARED.read_current(rom,lang)
   with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
    q,proof=z.qualify(model,raw,lang,Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+lang),Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+lang)/'teams.o');data=dict(preparation=z.Q.resources(raw),constructor=z.T.resources(model,raw,lang,trainer=31),message=z.V.M.resources(raw),names=z.X.W.resources(raw),header=z.R.resources(raw),personal_reader=z.resources(raw))
   with gzip.open(Path(os.environ['SGP_PERSONAL_CALLER_REPORT_DIR'])/('personal-caller-'+lang+'.json.gz'),'rb') as f:payload=f.read(32*1024**2+1)
   assert len(payload)<=32*1024**2;r=json.loads(payload);assert r['schema']=='trainer31-native-personal-caller-v1' and r['input']==json.loads(json.dumps(model['record'])) and r['source_sha256']==z.source_identities() and r['proof']==json.loads(json.dumps(proof)) and r['recipes']==z.RECIPES and r['close_recipe']==z.CLOSE_RECIPE;assert r['prefix_hook_source_contract']==z.Y.prefix_hook_contract(data,q) and r['resources']['personal_reader']==data['personal_reader']['2']['oracle'];cls.reports[lang]=r;cls.data[lang]=data;cls.q[lang]=q
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['positives'][0])
 def require(self,r):
  lang=next(iter(self.reports));self.z.require_case(r,self.data[lang],self.q[lang])
 def test_all_positive_matrices_and_remaining_readers(self):
  for lang,r in self.reports.items():
   self.assertEqual(tuple(len(r[k]) for k in ('positives','guards','volatile_controls','observer_off','counters')),(4,1,1,2,2))
   for p in r['positives']+r['guards']+r['volatile_controls']:self.z.require_case(p,self.data[lang],self.q[lang]);self.assertEqual(len(p['ctor_read_dispatch']),186+2*p['plus']);self.assertEqual(p['personal_reader']['instructions'],118)
 def test_actual_reader_abi_preimage_and_entire_transcripts(self):
  for key in ('entry','models','native_writes','stack_frame_hex','stack_frame_before','same_cpu','destination_before','rng_after'):
   r=self.base();p=r['personal_reader']
   if key=='entry':p[key][12]^=1
   elif key in ('models','native_writes'):p[key]=p[key][:-1]
   elif key in ('stack_frame_hex','stack_frame_before'):p[key]='00'*136
   elif key=='same_cpu':p[key]=False
   elif key=='destination_before':p[key]='a5'*44
   else:p[key]^=1
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_actual_growth_lookup_registers_not_just_metadata(self):
  for key in ('table','offset','word','r0','r4','r5','r6','sp','lr'):
   r=self.base();e=next(e for e in r['personal_flow'] if e['pc']=='0x206fd5c')
   if key in ('table','offset','word'):e[key]^=4
   else:e['regs'][dict(r0=0,r4=4,r5=5,r6=6,sp=13,lr=14)[key]]^=4
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_field_dispatch_getter_and_setter_chain(self):
  for key in ('field','loaded','getter','setpointer','setvalue','drop','duplicate'):
   r=self.base();f=r['personal_flow'];by={e['pc']:e for e in f}
   if key=='field':by['0x206fb74']['field_byte']=3
   elif key=='loaded':by['0x206fb76']['regs'][5]=2
   elif key=='getter':by['0x206fd0a']['regs'][0]=2
   elif key=='setpointer':by['0x206df82']['regs'][2]+=4
   elif key=='setvalue':by['0x206df82']['value']+=1
   elif key=='drop':r['personal_flow']=f[:-1]
   else:f.append(f[-1])
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_no_fake_first_read_model_or_event(self):
  for key in ('events','models','dispatch'):
   r=self.base()
   if key=='events':r['events'].insert(3,['read',2,355,self.z.DEST,44])
   elif key=='models':
    fake=copy.deepcopy(next(e for e in r['body']['models'] if e['name']=='ReadWholeNarcMemberByIdPair'));fake['args'][:3]=[self.z.DEST,2,355];fake['bytes']=44;fake['output_pointer']=self.z.DEST;r['body']['models'].insert(1,fake)
   else:r['ctor_read_dispatch'].append(r['ctor_read_dispatch'][0])
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_off_and_all_executed_counters(self):
  for lang,r in self.reports.items():
   for off in r['observer_off']:
    on=next(p for p in r['positives'] if p['plus']==off['result']['plus'] and p['seed']==off['result']['seed']);self.assertEqual(self.z.require_off_pair(on,off['result']),off['proof'])
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:self.z.require_counter(c,normal,self.data[lang],self.q[lang])
 def test_off_binding_and_projection_forgery_refused(self):
  report=next(iter(self.reports.values()));off=report['observer_off'][0]['result'];on=next(p for p in report['positives'] if p['plus']==off['plus'] and p['seed']==off['seed'])
  for key in ('neutral','regs','canary_preimages','ram_sha256','personal_clobber','projected'):
   bad=copy.deepcopy(off)
   if key=='neutral':bad['personal_binding'][key]=False
   elif key=='regs':bad['personal_binding'][key][0]^=1
   elif key=='canary_preimages':bad['personal_binding'][key]=[]
   elif key=='ram_sha256':bad['personal_binding'][key]='0'*64
   elif key=='personal_clobber':bad[key]=True
   else:bad['personal_reader']['projected_ram_sha256']='0'*64
   with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_off_pair(on,bad)
 def test_curve_counter_needs_exact_exp_only_packet_and_real_shadow(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678);c=next(c for c in r['counters'] if c['variant']=='personal_curve2')
   for key in ('shadow','packet','getter','table','namewrite','scope','firstscope','cookie','ldr_pair'):
    bad=copy.deepcopy(c);p=bad['result']
    if key=='shadow':p['personal_shadows'][0]['after'][4]^=1
    elif key=='packet':p['mon_hex'][0]=normal['mon_hex'][0]
    elif key=='getter':next(e for e in p['personal_flow'] if e['pc']=='0x206fd0a')['regs'][0]=4
    elif key=='table':next(e for e in p['personal_flow'] if e['pc']=='0x206fd5c')['word']+=1
    elif key=='namewrite':p['names'][-1]['native_writes']=p['names'][-1]['native_writes'][:-1]
    elif key=='firstscope':p['names'][0]['transitions'][0]['ram_sha256']='0'*64
    elif key=='cookie':
     next(e for e in p['personal_flow'] if e['pc']=='0x206fb76')['regs'][8]^=1;p['personal_shadows'][0]['before'][8]^=1;p['personal_shadows'][0]['after'][8]^=1
    elif key=='ldr_pair':next(e for e in p['personal_flow'] if e['pc']=='0x206fb74')['regs'][6]=22
    else:p['names'][-1]['transitions'][0]['neutral']=False
    with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
 def test_close_counter_cannot_drop_native_or_full_execution_evidence(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678);c=next(c for c in r['counters'] if c['variant']=='personal_skip_close')
   for key in ('models','native_writes','flow','dispatch','names','steps'):
    bad=copy.deepcopy(c);p=bad['result']
    if key in ('models','native_writes'):p['personal_reader'][key]=p['personal_reader'][key][:-1]
    elif key=='flow':p['personal_flow']=p['personal_flow'][:-1]
    elif key=='dispatch':p['ctor_read_dispatch']=p['ctor_read_dispatch'][:-1]
    elif key=='names':p['names']=p['names'][:-1]
    else:p['instructions']+=1
    with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
if __name__=='__main__':unittest.main()
