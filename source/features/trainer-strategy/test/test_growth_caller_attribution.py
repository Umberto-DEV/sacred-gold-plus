"""Private exact-ROM replay and growth404 transport/causality falsifiers."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_crescita_chiamante.py';s=importlib.util.spec_from_file_location('growth_replay',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_GROWTH_CALLER_ROM_DIR','SGP_GROWTH_CALLER_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')),'requires private exact ROMs, objects and reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.z=z=tool();cls.reports={};cls.data={};cls.q={}
  for lang in os.environ.get('SGP_GROWTH_CALLER_LANGUAGES','EN,IT').split(','):
   rom=Path(os.environ['SGP_GROWTH_CALLER_ROM_DIR'])/('r4-'+lang+'.nds');model=z.P.G.S.SHARED.read_current(rom,lang)
   with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
    q,proof=z.qualify(model,raw,lang,Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+lang),Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+lang)/'teams.o');data=dict(preparation=z.Q.resources(raw),constructor=z.T.resources(model,raw,lang,trainer=31),message=z.V.M.resources(raw),names=z.X.W.resources(raw),header=z.R.resources(raw),personal_reader=z.J.resources(raw),growth_reader=z.resources(raw),growth_counter=z.resources(raw,2))
   with gzip.open(Path(os.environ['SGP_GROWTH_CALLER_REPORT_DIR'])/('growth-caller-'+lang+'.json.gz'),'rb') as f:payload=f.read(32*1024**2+1)
   assert len(payload)<=32*1024**2;r=json.loads(payload);assert r['schema']=='trainer31-native-growth-caller-v1' and r['input']==json.loads(json.dumps(model['record'])) and r['source_sha256']==z.source_identities() and r['proof']==json.loads(json.dumps(proof)) and r['recipes']==z.RECIPES and r['close_recipe']==z.CLOSE_RECIPE;assert r['resources']['growth_reader']==data['growth_reader']['3']['oracle'] and r['resources']['growth_counter']==data['growth_counter']['3']['oracle'];cls.reports[lang]=r;cls.data[lang]=data;cls.q[lang]=q
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['positives'][0])
 def require(self,r):
  lang=next(iter(self.reports));self.z.require_case(r,self.data[lang],self.q[lang])
 def test_complete_matrices_and_original_remaining_dispatch(self):
  for lang,r in self.reports.items():
   self.assertEqual(tuple(len(r[k]) for k in ('positives','guards','volatile_controls','observer_off','counters')),(4,1,1,2,2))
   for p in r['positives']+r['guards']+r['volatile_controls']:self.z.require_case(p,self.data[lang],self.q[lang]);self.assertEqual(len(p['ctor_read_dispatch']),185+2*p['plus']);self.assertEqual(p['growth_reader']['instructions'],118)
 def test_actual_reader_abi404_and_preimage_transcript(self):
  for key in ('entry','models','native_writes','stack_frame_hex','stack_frame_before','same_cpu','destination_before','rng_after'):
   r=self.base();p=r['growth_reader']
   if key=='entry':p[key][3]=0x2007509
   elif key in ('models','native_writes'):p[key]=p[key][:-1]
   elif key in ('stack_frame_hex','stack_frame_before'):p[key]='00'*136
   elif key=='same_cpu':p[key]=False
   elif key=='destination_before':p[key]='dd'*404
   else:p[key]^=1
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_reader_residues_must_reach_actual_lookup(self):
  for key,value in ((1,3),(2,4),(14,0x206FD2D)):
   r=self.base();lookup=next(e for e in r['personal_flow'] if e['pc']=='0x206fd5c');lookup['regs'][key]=value
   with self.subTest(register=key),self.assertRaises(ValueError):self.require(r)
 def test_dead_personal_free_and_alloc_canaries_source_bound(self):
  for key in ('deadbefore','deadafter','canaries','events','neutral','phase'):
   r=self.base();b=r['growth_binding']
   if key=='deadbefore':b['dead_personal_before']='00'*44
   elif key=='deadafter':r['growth_reader']['dead_personal_after']='00'*44
   elif key=='canaries':b['canary_preimages']=b['canary_preimages'][:-1]
   elif key=='events':r['events'][3]=['free',self.z.DEST]
   elif key=='neutral':b['neutral']=False
   else:b['ram_sha256']='0'*64
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_no_fabricated_first_growth_callback_or_event(self):
  for key in ('event','model','dispatch'):
   r=self.base()
   if key=='event':r['events'].insert(5,['read',3,4,self.z.DEST,404])
   elif key=='model':
    fake=copy.deepcopy(next(e for e in r['body']['models'] if e['name']=='ReadWholeNarcMemberByIdPair'));r['body']['models'].insert(3,fake)
   else:r['ctor_read_dispatch'].append(r['ctor_read_dispatch'][0])
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_off_pairs_and_executed_counters(self):
  for lang,r in self.reports.items():
   for off in r['observer_off']:
    on=next(p for p in r['positives'] if p['plus']==off['result']['plus'] and p['seed']==off['result']['seed']);self.assertEqual(self.z.require_off_pair(on,off['result']),off['proof'])
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:self.z.require_counter(c,normal,self.data[lang],self.q[lang])
 def test_off_binding_dead44_and_exact_projection_cannot_be_forged(self):
  r=next(iter(self.reports.values()));off=r['observer_off'][0]['result'];on=next(p for p in r['positives'] if p['plus']==off['plus'] and p['seed']==off['seed'])
  for key in ('neutral','regs','canaries','dead','phase','projection','control'):
   bad=copy.deepcopy(off)
   if key=='neutral':bad['growth_binding']['neutral']=False
   elif key=='regs':bad['growth_binding']['regs'][2]^=1
   elif key=='canaries':bad['growth_binding']['canary_preimages']=[]
   elif key=='dead':bad['growth_binding']['dead_personal_before']=bad['growth_reader']['dead_personal_after']='dd'*44
   elif key=='phase':bad['growth_binding']['ram_sha256']='0'*64
   elif key=='projection':bad['growth_reader']['projected_ram_sha256']='0'*64
   else:bad['growth_clobber']=True
   with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_off_pair(on,bad)
 def test_counter_initial_ram_and_frame_same_as_actual_baseline(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:
    for key in ('hash','frame','guard','projection'):
     bad=copy.deepcopy(c);p=bad['result'];reader=p['growth_reader']
     if key=='hash':p['growth_binding']['ram_sha256']=reader['unrelated_ram_sha256']='0'*64
     elif key=='frame':
      for field in ('stack_frame_before','stack_frame_hex'):
       v=bytearray.fromhex(reader[field]);v[40]^=1;reader[field]=v.hex()
     elif key=='guard':reader['stack_guard_before']='00'*56
     else:p['growth_binding']['projected_ram_sha256']='0'*64
     with self.subTest(variant=c['variant'],key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
 def test_wrong_member_retains_getter4_and_exact_packet_shadow(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678);c=next(c for c in r['counters'] if c['variant']=='growth_wrong_member')
   for key in ('shadow','getter','r6','cursor','delivery','packet','first_name','later_write'):
    bad=copy.deepcopy(c);p=bad['result']
    if key=='shadow':p['growth_shadows'][0]['after'][5]=2
    elif key=='getter':next(e for e in p['personal_flow'] if e['pc']=='0x206fd0a')['regs'][0]=2
    elif key=='r6':next(e for e in p['personal_flow'] if e['pc']=='0x206fd5c')['regs'][6]=2
    elif key=='cursor':p['growth_reader']['cursor']=normal['growth_reader']['cursor']
    elif key=='delivery':p['growth_reader']['models'][13]['delivered_bytes']=108
    elif key=='packet':p['mon_hex'][0]=normal['mon_hex'][0]
    elif key=='first_name':p['names'][0]['transitions'][0]['ram_sha256']='0'*64
    else:p['names'][-1]['native_writes']=p['names'][-1]['native_writes'][:-1]
    with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
if __name__=='__main__':unittest.main()
