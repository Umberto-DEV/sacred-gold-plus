"""Private exact-ROM replay: custom occurrence, stack buffer, PP consumer and counters."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,unittest
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_pp_chiamante.py';s=importlib.util.spec_from_file_location('pp_replay',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_PP_CALLER_ROM_DIR','SGP_PP_CALLER_REPORT_DIR','SGP_REMATCH_OBJECT_DIR','SGP_STRATEGY_OBJECT_DIR')),'requires private exact ROMs, objects and reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.z=z=tool();cls.reports={};cls.data={};cls.q={}
  for lang in os.environ.get('SGP_PP_CALLER_LANGUAGES','EN,IT').split(','):
   rom=Path(os.environ['SGP_PP_CALLER_ROM_DIR'])/('r4-'+lang+'.nds');model=z.P.G.S.SHARED.read_current(rom,lang)
   with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
    q,proof=z.qualify(model,raw,lang,Path(os.environ['SGP_REMATCH_OBJECT_DIR'])/('public-build-'+lang),Path(os.environ['SGP_STRATEGY_OBJECT_DIR'])/('build-'+lang)/'teams.o');data=dict(preparation=z.Q.resources(raw),constructor=z.T.resources(model,raw,lang,trainer=31),message=z.V.M.resources(raw),names=z.X.W.resources(raw),header=z.R.resources(raw),personal_reader=z.J.resources(raw),growth_reader=z.G.resources(raw),growth_counter=z.G.resources(raw,2),pp_reader=z.resources(raw))
   with gzip.open(Path(os.environ['SGP_PP_CALLER_REPORT_DIR'])/('pp-caller-'+lang+'.json.gz'),'rb') as f:payload=f.read(32*1024**2+1)
   assert len(payload)<=32*1024**2;r=json.loads(payload);assert r['schema']=='trainer31-native-pp-caller-v1' and r['input']==json.loads(json.dumps(model['record'])) and r['source_sha256']==z.source_identities() and r['proof']==json.loads(json.dumps(proof)) and r['recipes']==z.RECIPES and r['close_recipe']==z.CLOSE_RECIPE;assert r['resources']['pp_reader']==data['pp_reader']['11']['oracle'] and r['semantic_counter']['result_source_sha256']==z.A.RESULT_SOURCE_SHA256;cls.reports[lang]=r;cls.data[lang]=data;cls.q[lang]=q
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['positives'][0])
 def require(self,r):
  lang=next(iter(self.reports));self.z.require_case(r,self.data[lang],self.q[lang])
 def test_complete_matrices_and_original_remaining_dispatch(self):
  for lang,r in self.reports.items():
   self.assertEqual(tuple(len(r[k]) for k in ('positives','guards','volatile_controls','observer_off','counters')),(4,1,1,2,2))
   for p in r['positives']+r['guards']+r['volatile_controls']:self.z.require_case(p,self.data[lang],self.q[lang]);self.assertEqual(len(p['ctor_read_dispatch']),183+2*p['plus']);self.assertEqual(p['pp_reader']['instructions'],118);self.assertEqual(p['max_stack'],608)
 def test_default_learnset_occurrence_cannot_replace_custom_owner(self):
  for key in ('stack','caller','events','slot','thunk'):
   r=self.base()
   if key=='stack':r['pp_reader']['entry'][0]=r['pp_reader']['entry'][13]=self.z.INNER-392
   elif key=='caller':r['pp_binding']['native_caller']['lr']='0x2073123'
   elif key=='events':r['pp_binding']['events_before']=r['pp_binding']['events_before'][:30]
   elif key=='slot':r['pp_flow'][0]['regs'][2]=1
   else:r['pp_flow'][1]['regs'][3]=0
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_actual_reader_frame_preimages_and_borrowed_upper16(self):
  for key in ('entry','models','native_writes','frame','before','guard','guard_after','payload','upper','truncate','same_cpu','rng'):
   r=self.base();p=r['pp_reader']
   if key=='entry':p['entry'][3]=0
   elif key in ('models','native_writes'):p[key]=p[key][:-1]
   elif key=='frame':p['stack_frame_hex']='00'*136
   elif key=='before':p['stack_frame_before']='00'*136
   elif key=='guard':p['stack_guard_before']='00'*56
   elif key=='guard_after':p['stack_guard_after']='00'*56
   elif key=='payload':p['destination_hex']='00'*16
   elif key=='upper':p['upper_after']='00'*16
   elif key=='truncate':r['pp_binding']['upper_before']=p['upper_after']=p['upper_after'][:16]
   elif key=='same_cpu':p[key]=False
   else:p['rng_after']^=1
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_pp_field_getter_full_registers_ppups_and_divide(self):
  for key in ('field','ldr','attr','restore','ppups','numerator','quotient','local'):
   r=self.base();flow={e['pc']:e for e in r['pp_flow']}
   if key=='field':flow['0x2073390']['field_byte']=1
   elif key=='ldr':flow['0x2073392']['regs'][2]^=1
   elif key=='attr':flow['0x2073354']['regs'][1]=6
   elif key=='restore':flow['0x207333c']['regs'][4]=5
   elif key=='ppups':flow['0x207150e']['regs'][0]=1
   elif key=='numerator':flow['0x2073348']['regs'][0]=300
   elif key=='quotient':flow['0x207334c']['regs'][0]=1
   else:flow['0x2071526']['value_byte']=1
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_pp_actual_store_and_quiescent_packet_cannot_be_forged(self):
  for key in ('before','value','r3','sp','flags','address','packet'):
   r=self.base();store=r['pp_stores'][0]
   if key=='before':store[key]=0
   elif key=='value':store[key]=1
   elif key=='r3':store['regs'][3]=0
   elif key=='sp':store['regs'][13]+=80
   elif key=='flags':store['header_flags']=2
   elif key=='address':store[key]+=1
   else:
    point=r['pp_checkpoint'];point['mon_hex']=self.z.expected_pp_packet(point['mon_hex'],1);point['decoded']=self.z.T.M.decode(bytes.fromhex(point['mon_hex']))
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_exact_dead1124_and_mail_copy_provenance(self):
  for key in ('dead','canaries','free','hash','mail'):
   r=self.base()
   if key=='dead':r['pp_binding']['dead_before']=r['pp_reader']['dead_after']=[]
   elif key=='canaries':r['pp_binding']['canary_preimages']=r['pp_binding']['canary_preimages'][:-1]
   elif key=='free':r['pp_binding']['events_before'][3]=['free',self.z.DEST]
   elif key=='hash':r['pp_binding']['ram_sha256']='0'*64
   else:r['friendship_checkpoints'][0]['mon_hex']='00'*236
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_off_pairs_and_executed_counters(self):
  for lang,r in self.reports.items():
   for off in r['observer_off']:
    on=next(p for p in r['positives'] if p['plus']==off['result']['plus'] and p['seed']==off['result']['seed']);self.assertEqual(self.z.require_off_pair(on,off['result'],self.data[lang]),off['proof'])
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:self.z.require_counter(c,normal,self.data[lang],self.q[lang])
 def test_off_exact_projection_and_borrowed_upper_cannot_be_forged(self):
  lang=next(iter(self.reports));r=self.reports[lang];off=r['observer_off'][0]['result'];on=next(p for p in r['positives'] if p['plus']==off['plus'] and p['seed']==off['seed'])
  for key in ('dead','canary','mail','neutral','hash','projection','upper','truncate','control'):
   bad=copy.deepcopy(off);binding=bad['pp_binding'];reader=bad['pp_reader']
   if key=='dead':binding['dead_before']=reader['dead_after']=[]
   elif key=='canary':binding['canary_preimages']=[]
   elif key=='mail':
    next(e for e in binding['dead_before'] if e['bytes']==56)['hex']='00'*56;next(e for e in reader['dead_after'] if e['bytes']==56)['hex']='00'*56
   elif key=='neutral':binding[key]=False
   elif key=='hash':binding['ram_sha256']='0'*64
   elif key=='projection':reader['projected_ram_sha256']='0'*64
   elif key=='upper':reader['upper_after']='00'*16
   elif key=='truncate':binding['upper_before']=reader['upper_after']=reader['upper_after'][:16]
   else:bad['pp_clobber']=True
   with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_off_pair(on,bad,self.data[lang])
 def test_counter_exact_shared_prestate_and_first_name_before_mutation(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678)
   for c in r['counters']:
    for key in ('hash','frame','guard','projection','first_name','create'):
     bad=copy.deepcopy(c);p=bad['result'];reader=p['pp_reader']
     if key=='hash':p['pp_binding']['ram_sha256']=reader['unrelated_ram_sha256']='0'*64
     elif key=='frame':
      for field in ('stack_frame_before','stack_frame_hex'):
       v=bytearray.fromhex(reader[field]);v[40]^=1;reader[field]=v.hex()
     elif key=='guard':reader['stack_guard_before']='00'*56
     elif key=='projection':p['pp_binding']['projected_ram_sha256']='0'*64
     elif key=='first_name':p['names'][0]['transitions'][0]['ram_sha256']='0'*64
     else:p['friendship_checkpoints'][0]['mon_hex']='00'*236
     with self.subTest(variant=c['variant'],key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
 def test_pp1_shadow_and_later_real_writes_remain_bound(self):
  for lang,r in self.reports.items():
   normal=next(p for p in r['positives'] if p['plus']==1 and p['seed']==0x12345678);c=next(c for c in r['counters'] if c['variant']=='pp_one')
   for key in ('missing','extra_register','raw','packet','later_write'):
    bad=copy.deepcopy(c);p=bad['result']
    if key=='missing':p['pp_shadows']=[]
    elif key=='extra_register':p['pp_shadows'][0]['after'][1]^=1
    elif key=='raw':p['pp_reader']['destination_hex']='00'*16
    elif key=='packet':p['mon_hex'][0]=normal['mon_hex'][0]
    else:p['names'][-1]['native_writes']=p['names'][-1]['native_writes'][:-1]
    with self.subTest(key=key),self.assertRaises(ValueError):self.z.require_counter(bad,normal,self.data[lang],self.q[lang])
 def test_counter_semantic_expected_changes_one_field_without_touching_raw(self):
  z=self.z
  for lang,data in self.data.items():
   before=copy.deepcopy(data);original=z.T.expected(data['constructor'],1);z.A.adapt(z.B,type('ProofOnly',(),dict(parent=z.U,composition=z.V,factory=None))());fn=z.A.counter_result_oracle();new=fn.__globals__['T'].expected(data['constructor'],1);want=copy.deepcopy(original);want[0]['fields']['pp'][0]=1;self.assertEqual(new,want);self.assertEqual(data,before);self.assertEqual(data['constructor']['archives'][11][310][6],15)
if __name__=='__main__':unittest.main()
