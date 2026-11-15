"""Private exact-ROM replay: initial friendship, transient lifetime and owned override."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_amicizia_chiamante.py';s=importlib.util.spec_from_file_location('friendship_replay',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_FRIENDSHIP_CALLER_ROM_DIR','SGP_FRIENDSHIP_CALLER_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')),'requires private exact ROMs, objects and reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.z=z=tool();cls.reports={};cls.data={};cls.q={}
  for lang in os.environ.get('SGP_FRIENDSHIP_CALLER_LANGUAGES','EN,IT').split(','):
   rom=Path(os.environ['SGP_FRIENDSHIP_CALLER_ROM_DIR'])/('r4-'+lang+'.nds');model=z.P.G.S.SHARED.read_current(rom,lang)
   with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
    q,proof=z.qualify(model,raw,lang,Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+lang),Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+lang)/'teams.o');data=dict(preparation=z.Q.resources(raw),constructor=z.T.resources(model,raw,lang,trainer=31),message=z.V.M.resources(raw),names=z.X.W.resources(raw),header=z.R.resources(raw),personal_reader=z.J.resources(raw),growth_reader=z.G.resources(raw),growth_counter=z.G.resources(raw,2))
   with gzip.open(Path(os.environ['SGP_FRIENDSHIP_CALLER_REPORT_DIR'])/('friendship-caller-'+lang+'.json.gz'),'rb') as f:payload=f.read(32*1024**2+1)
   assert len(payload)<=32*1024**2;r=json.loads(payload);assert r['schema']=='trainer31-native-friendship-caller-v1' and r['input']==json.loads(json.dumps(model['record'])) and r['source_sha256']==z.source_identities() and r['proof']==json.loads(json.dumps(proof)) and r['recipes']==z.RECIPES and r['close_recipe']==z.CLOSE_RECIPE;assert r['resources']['personal_reader']==data['personal_reader']['2']['oracle'];cls.reports[lang]=r;cls.data[lang]=data;cls.q[lang]=q
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['positives'][0])
 def require(self,r):
  lang=next(iter(self.reports));self.z.require_case(r,self.data[lang],self.q[lang])
 def test_complete_matrices_and_original_remaining_dispatch(self):
  for lang,r in self.reports.items():
   self.assertEqual(tuple(len(r[k]) for k in ('positives','guards','volatile_controls','observer_off','counters')),(4,1,1,2,2))
   for p in r['positives']+r['guards']+r['volatile_controls']:self.z.require_case(p,self.data[lang],self.q[lang]);self.assertEqual(len(p['ctor_read_dispatch']),184+2*p['plus']);self.assertEqual(p['friendship_reader']['instructions'],118)
 def test_actual_reader_abi_and_preimage_transcript(self):
  for key in ('entry','models','native_writes','stack_frame_hex','stack_frame_before','same_cpu','destination_before','rng_after'):
   r=self.base();p=r['friendship_reader']
   if key=='entry':p[key][3]=0
   elif key in ('models','native_writes'):p[key]=p[key][:-1]
   elif key in ('stack_frame_hex','stack_frame_before'):p[key]='00'*136
   elif key=='same_cpu':p[key]=False
   elif key=='destination_before':p[key]='dd'*44
   else:p[key]^=1
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_native_byte18_full_ldr_and_getter_setter_flow(self):
  for key in ('field','ldr','getter','local','frame','flags'):
   r=self.base();flow={e['pc']:e for e in r['friendship_flow']}
   if key=='field':flow['0x206fb70']['field_byte']=0
   elif key=='ldr':flow['0x206fb72']['regs'][3]^=1
   elif key=='getter':flow['0x206df8e']['regs'][0]=0
   elif key=='local':flow['0x206df96']['value']=0
   elif key=='frame':flow['0x206ed70']['regs'][13]-=8
   else:flow['0x206df9a']['header_flags']=0
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_transient_and_owned_stores_are_distinct_actual_transactions(self):
  for key in ('owner','initial_sp','override_sp','flags','address','value'):
   r=self.base();stores=r['friendship_stores']
   if key=='owner':stores[1]['owner']='initial'
   elif key=='initial_sp':stores[0]['regs'][13]+=8
   elif key=='override_sp':stores[1]['regs'][13]=stores[0]['regs'][13]
   elif key=='flags':stores[1]['header_flags']=2
   elif key=='address':stores[0]['address']+=1
   else:stores[0]['value']=255
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_store_prestates_full_context_and_create_buffer_register(self):
  for key in ('initial_before','override_before','r1','r2','r3','r5','r6','ip','flags','create','length','return','entry_mon','party_bool'):
   r=self.base()
   if key=='initial_before':r['friendship_stores'][0]['before']=35
   elif key=='override_before':r['friendship_stores'][1]['before']=0
   elif key in ('r1','r2','r3','r5','r6','ip'):r['friendship_stores'][1]['regs'][{'r1':1,'r2':2,'r3':3,'r5':5,'r6':6,'ip':12}[key]]^=1
   elif key=='flags':r['friendship_stores'][0]['regs'][15]^=0x60000000
   elif key=='create':r['friendship_checkpoints'][0]['regs'][6]=0
   elif key=='length':r['friendship_stores'][0]['regs'].append(0)
   elif key=='entry_mon':r['friendship_checkpoints'][1]['regs'][0]=0
   elif key=='party_bool':r['friendship_checkpoints'][-1]['regs'][0]=0
   else:r['friendship_flow'][-1]['regs'][15]^=0x60000000
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_six_full_packets_cannot_hide_transient_with_final_output(self):
  for index in range(6):
   r=self.base();point=r['friendship_checkpoints'][index];point['mon_hex']=self.z.expected_friendship_packet(point['mon_hex'],0);point['decoded']=self.z.T.M.decode(bytes.fromhex(point['mon_hex']))
   with self.subTest(index=index),self.assertRaises(ValueError):self.require(r)
  r=self.base();r['friendship_checkpoints'][-1]['party_slot_hex']='00'*236
  with self.assertRaises(ValueError):self.require(r)
 def test_off_pairs_and_executed_counters(self):
  for lang,r in self.reports.items():
   for off in r['observer_off']:
    on=next(p for p in r['positives'] if p['plus']==off['result']['plus'] and p['seed']==off['result']['seed']);self.assertEqual(self.z.require_off_pair(on,off['result']),off['proof'])
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:self.z.require_counter(c,normal,self.data[lang],self.q[lang])
 def test_off_exact528_projection_cannot_hide_live44(self):
  r=next(iter(self.reports.values()));off=r['observer_off'][0]['result'];on=next(p for p in r['positives'] if p['plus']==off['plus'] and p['seed']==off['seed'])
  for key in ('neutral','regs','canaries','dead','phase','projection','control'):
   bad=copy.deepcopy(off)
   if key=='neutral':bad['friendship_binding']['neutral']=False
   elif key=='regs':bad['friendship_binding']['regs'][2]^=1
   elif key=='canaries':bad['friendship_binding']['canary_preimages']=[]
   elif key=='dead':bad['friendship_binding']['dead_before']=bad['friendship_reader']['dead_after']=[]
   elif key=='phase':bad['friendship_binding']['ram_sha256']='0'*64
   elif key=='projection':bad['friendship_reader']['projected_ram_sha256']='0'*64
   else:bad['friendship_clobber']=True
   with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_off_pair(on,bad)
 def test_counter_prestate_shadow_transient_and_final_evidence(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:
    for key in ('hash','frame','guard','projection','last_name','final_ram'):
     bad=copy.deepcopy(c);p=bad['result'];reader=p['friendship_reader']
     if key=='hash':p['friendship_binding']['ram_sha256']=reader['unrelated_ram_sha256']='0'*64
     elif key=='frame':
      for field in ('stack_frame_before','stack_frame_hex'):
       v=bytearray.fromhex(reader[field]);v[40]^=1;reader[field]=v.hex()
     elif key=='guard':reader['stack_guard_before']='00'*56
     elif key=='projection':p['friendship_binding']['projected_ram_sha256']='0'*64
     elif key=='last_name':p['names'][-1]['transitions'][-1]['ram_sha256']='0'*64
     else:p['raw_ram_sha256']='0'*64
     with self.subTest(variant=c['variant'],key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
if __name__=='__main__':unittest.main()
