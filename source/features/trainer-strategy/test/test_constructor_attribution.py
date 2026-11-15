"""Replay exact-input native constructor receipts and calibrate their independent oracle.

Generate receipts with attribuisci_costruttore.py. Replay tests do not claim a new
CPU run or replace the original capture's recorded source identity.
"""
from pathlib import Path
import importlib.util,json,gzip,mmap,os,sys,copy,tempfile,unittest,struct
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 s=importlib.util.spec_from_file_location('native_constructor',SOURCE/'features/trainer-strategy/tools/attribuisci_costruttore.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def require_off_replay(m,proof,capture):
 expected=dict(party_sha256=m.P.sha(b''.join(bytes.fromhex(x) for x in capture['mon_hex'])),seed=capture['seed_after'],end=capture['end'],events_sha256=m.P.sha(json.dumps(capture['events'],sort_keys=True).encode()),qualified=True,scope='functional native outputs/SDK events; declared canary/free-poison scratch differs')
 m.need(proof==expected,'OFF receipt must bind to the complete paired native capture')


class Portable(unittest.TestCase):
 def test_history_record_bounds_and_padding_candidates_are_distinct(self):
  spec=importlib.util.spec_from_file_location('history_layout',SOURCE/'features/trainer-strategy/tools/rileggi_provenienza.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  for kind,stride in ((0,8),(1,16),(2,10),(3,18)):
   header=bytearray(20);header[0]=kind;header[3]=5;body=b'R'*(stride*5);r=m.party_layout(header,body);self.assertEqual(r['declared_bytes'],len(body));self.assertEqual(r['trailing_bytes'],0);self.assertIsNone(r['trailing_sha256']);self.assertFalse(r['alignment4_padding_candidate'])
   for tail in (b'\0'*2,b'XY',b'\0'*6):
    r=m.party_layout(header,body+tail);self.assertEqual(r['declared_sha256'],m.P.sha(body));self.assertEqual(r['trailing_sha256'],m.P.sha(tail));self.assertEqual(r['alignment4_padding_candidate'],tail==b'\0'*2 and len(body)%4==2)
   with self.assertRaisesRegex(ValueError,'shorter'):m.party_layout(header,body[:-1])
  for header in (bytes(19),bytes(20),bytes([4,0,0,1])+bytes(16),bytes([3,0,0,7])+bytes(16)):
   with self.assertRaises(ValueError):m.party_layout(header,bytes(108))
 def test_history_reader_preserves_aliases_and_refuses_unidentified_roms(self):
  spec=importlib.util.spec_from_file_location('history_reader',SOURCE/'features/trainer-strategy/tools/rileggi_provenienza.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);raw=root/'input.nds';raw.write_bytes(b'preserve');sym=root/'alias';sym.symlink_to(raw);hard=root/'hard';os.link(raw,hard)
   for out in (raw,sym,hard,SOURCE/'new.json'):
    args=['history','--rom',str(raw),'--retail',str(raw),'--base',str(raw),'--v4',str(raw),'--language','EN','--trainer','31','--json',str(out)]
    with patch.object(sys,'argv',args),patch.object(m,'analyze') as analyze,self.assertRaises(SystemExit) as caught:m.main()
    self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
   out=root/'new.json';args[-1]=str(out)
   with patch.object(sys,'argv',args),self.assertRaises(SystemExit) as caught:m.main()
   self.assertEqual(caught.exception.code,2);self.assertFalse(out.exists());self.assertEqual(raw.read_bytes(),b'preserve')
 def test_plural_delta_pairs_and_counter_domain_are_bounded(self):
  m=tool()
  for trainer in (21,31,32,33,34,244,245):self.assertEqual(len(m.deltas_for(trainer)),3 if trainer==33 else 1)
  for pp in (((20,15),(20,10)),((20,15),(20,10),(20,5),(1,1))):
   profile=copy.deepcopy(m.PROFILES[33]);profile['delta_pps']=pp
   with patch.dict(m.PROFILES,{33:profile}),self.assertRaisesRegex(ValueError,'three complete'):m.deltas_for(33)
  for offset in (26,27,108):
   profile=copy.deepcopy(m.PROFILES[33]);profile['deltas'][-1]['offset']=offset
   with patch.dict(m.PROFILES,{33:profile}),self.assertRaises(ValueError):m.deltas_for(33)
  self.assertEqual([m.counter_delta(33,v)['offset'] for v in m.variants_for(33)[3:]],[26,98,100])
  for variant in ('wrong_last_move','wrong_move_3','wrong_move_-1'):
   with self.assertRaises(ValueError):m.run_case(None,None,'EN',None,trainer=33,variant=variant)
 def test_only_finite_integer_profiles_are_admitted(self):
  m=tool()
  for trainer in (21,31,32,33,34,244,245):self.assertEqual(m.profile_for(trainer)['trainer'],trainer)
  for trainer in (True,False,21.0,'31',0,22,999):
   with self.subTest(trainer=trainer),self.assertRaises(ValueError):m.profile_for(trainer)
  with patch.object(sys,'argv',['constructor','--trainer','999']),patch.object(m,'analyze') as analyze,self.assertRaises(SystemExit) as caught:m.main()
  self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
 def test_outputs_preserve_each_input_alias_and_retained_directory(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);objects=root/'rematch';objects.mkdir();other=root/'strategy';other.mkdir();rom=root/'r4.nds';obj=other/'teams.o';inputs=(rom,obj,objects/'rematch-variants.o',objects/'rematch-stub.o')
   for p in inputs:p.write_bytes(b'preserve')
   outputs=[]
   for i,p in enumerate(inputs):
    sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);outputs.extend((p,sym,hard))
   outputs.extend((SOURCE/'new.json',objects/'new.json',other/'new.json',root))
   for out in outputs:
    args=['constructor','--rom',str(rom),'--language','EN','--objects',str(objects),'--strategy-object',str(obj),'--json',str(out)]
    with self.subTest(out=out.name),patch.object(sys,'argv',args),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')
 def test_optimized_python_is_refused_before_legacy_assertions_are_used(self):
  m=tool()
  with patch.object(m.sys,'flags',type('Flags',(),dict(optimize=1))()),self.assertRaisesRegex(ValueError,'without Python -O'):m.qualify(None,None,None,None,None)


@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_R4_ROM_DIR','SGP_REMATCH_OBJECTS_DIR','SGP_STRATEGY_OBJECT','SGP_CONSTRUCTOR_REPORT_DIR')),'requires exact ROMs,retained project objects and private CLI constructor receipts')
class CurrentReplay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  m=cls.m=tool();cls.trainer=int(os.environ.get('SGP_CONSTRUCTOR_TRAINER','21'));m.profile_for(cls.trainer);cls.reports={};cls.data={};cls.code={};cls.models={};cls.paths={}
  for lang in ('EN','IT'):
   p=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%lang);model=m.P.G.S.SHARED.read_current(p,lang);cls.paths[lang]=p;cls.models[lang]=model
   report=Path(os.environ['SGP_CONSTRUCTOR_REPORT_DIR'])/(os.environ.get('SGP_CONSTRUCTOR_REPORT_NOME','constructor-%s.json.gz')%lang)
   assert report.stat().st_size<=16*1024*1024
   with (gzip.open(report,'rb') if report.suffix=='.gz' else report.open('rb')) as file:payload=file.read(16*1024*1024+1)
   assert len(payload)<=16*1024*1024;r=json.loads(payload);assert r['schema']==f'trainer{cls.trainer}-native-constructor-v1' and r['input']==json.loads(json.dumps(model['record']));cls.reports[lang]=r
   for source in (Path(m.S.__file__),Path(m.F.__file__),Path(m.M.__file__),Path(m.C.__file__),Path(m.B.__file__)):assert r['source_sha256'][str(source.relative_to(SOURCE))]==m.P.sha(source.read_bytes())
   with p.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:
    code,ranges,module,proof=m.qualify(model,raw,lang,Path(os.environ['SGP_REMATCH_OBJECTS_DIR']),Path(os.environ['SGP_STRATEGY_OBJECT']),trainer=cls.trainer);cls.code[lang]=code;cls.data[lang]=m.resources(model,raw,lang,trainer=cls.trainer)
   assert [len(r[key]) for key in ('positives','old_recipe_baselines','guards','counters')]==[4,2,2,5 if cls.trainer==33 else 3]
 def normal(self,lang='EN'):return next(r for r in self.reports[lang]['positives'] if r['plus']==1 and r['seed']==0x12345678)
 def require(self,r,lang='EN'):return self.m.require_case(r,self.data[lang])
 def test_all_current_baseline_and_guard_receipts_match_fresh_raw_input_proofs(self):
  for lang,report in self.reports.items():
   for r in report['positives']+report['old_recipe_baselines']+report['guards']:
    self.require(r,lang)
    for row in r['code']:self.assertEqual(self.code[lang].get(int(row['ram'],16)),(row['bytes'],row['thumb']))
 def test_whole_packet_strategy_delta_and_independent_original_seed_restoration(self):
  for lang,report in self.reports.items():
   for plus in (0,1):
    selected=[r for r in report['positives'] if r['plus']==plus];baseline=next(r for r in report['old_recipe_baselines'] if r['plus']==plus);self.m.compare_strategy_delta(selected[0],baseline);self.assertEqual(selected[0]['mon_hex'],selected[1]['mon_hex']);self.assertNotEqual(selected[0]['seed_after'],selected[1]['seed_after'])
   expected=self.m.expected(self.data[lang],1);self.assertEqual([r['iv'] for r in expected],list(self.m.profile_for(self.trainer)['ivs']));self.assertEqual([r['pid_gender'] for r in expected],[0x78,0x78,0x79,0x79,0x79,0x79] if self.trainer==21 else [0x88]*6 if self.trainer==31 else [0x88]*4+[0x89]*2 if self.trainer==32 else [0x78]*3+[0x79]*2+[0x80] if self.trainer==33 else [0x89]*6 if self.trainer==34 else [0x88]*6 if self.trainer==244 else [0x78]*6)
 def test_observer_off_receipts_sdk_poison_and_nonzero_caller_cookies(self):
  for lang,report in self.reports.items():
   self.assertEqual(len(report['observer_neutrality']),2);normal=self.normal(lang)
   for plus,proof in enumerate(report['observer_neutrality']):
    paired=next(r for r in report['positives'] if r['plus']==plus and r['seed']==0x12345678);require_off_replay(self.m,proof,paired)
   for r in report['guards']:self.assertEqual(r['mon_hex'],normal['mon_hex']);self.assertEqual(r['seed_after'],normal['seed_after'])
 def test_whole_packet_comparison_refuses_truncated_vectors(self):
  for lang,report in self.reports.items():
   for plus in (0,1):
    current=next(r for r in report['positives'] if r['plus']==plus);old=next(r for r in report['old_recipe_baselines'] if r['plus']==plus)
    for which in ('current','baseline','both'):
     left,right=copy.deepcopy(current),copy.deepcopy(old)
     if which in ('current','both'):left['mon_hex'].pop()
     if which in ('baseline','both'):right['mon_hex'].pop()
     with self.subTest(language=lang,plus=plus,which=which),self.assertRaisesRegex(ValueError,'all six complete packets'):self.m.compare_strategy_delta(left,right)
 def test_whole_packet_comparison_refuses_empty_short_and_long_packets(self):
  for lang,report in self.reports.items():
   for plus in (0,1):
    current=next(r for r in report['positives'] if r['plus']==plus);old=next(r for r in report['old_recipe_baselines'] if r['plus']==plus)
    for size in (0,136,235,237):
     left,right=copy.deepcopy(current),copy.deepcopy(old);left['mon_hex'][0]=right['mon_hex'][0]='00'*size
     with self.subTest(language=lang,plus=plus,size=size),self.assertRaisesRegex(ValueError,'all six complete packets'):self.m.compare_strategy_delta(left,right)
 def test_off_proof_hash_state_and_scope_forgery_are_refused(self):
  for lang,report in self.reports.items():
   proof=report['observer_neutrality'][1];paired=self.normal(lang)
   for field in ('party_sha256','events_sha256','seed','end','qualified','scope'):
    x=copy.deepcopy(proof);x[field]=False if field=='qualified' else proof[field]^1 if field=='seed' else {} if field=='end' else 'wrong'
    with self.subTest(language=lang,field=field),self.assertRaises(ValueError):require_off_replay(self.m,x,paired)
 def test_same_party_lifetime_and_wrong_callee_counters_remain_refused(self):
  for lang,report in self.reports.items():
   normal=self.normal(lang)
   for r in report['counters']:
    if r['variant'] in ('wrong_restore_seed','omit_prefix_free'):self.assertEqual(r['mon_hex'],normal['mon_hex'])
    if r['variant']=='omit_prefix_free':self.assertEqual(r['seed_after'],normal['seed_after']);self.assertEqual(r['live'],{str(self.m.B.ARENA):108})
    delta=self.m.counter_delta(self.trainer,r['variant'])
    if delta is not None:
     self.assertEqual(r['buffer_before_free'],normal['buffer_before_free']);self.assertEqual(r['decoded'][delta['offset']//18]['moves'][(delta['offset']%18-8)//2],delta['before'])
     if self.trainer==245:self.assertEqual(r['decoded'][5]['pp'][2],normal['decoded'][5]['pp'][2]);self.assertEqual(r['decoded'][5]['pp'][2],10);self.assertNotEqual(r['mon_hex'][5],normal['mon_hex'][5])
    with self.assertRaises(ValueError):self.require(dict(r,variant='current',game_shadows=[]),lang)
 def test_oracle_refuses_missing_return_helper_rng_resource_copy_and_abi_evidence(self):
  r=self.normal();mutants=[]
  for field,value in (('api_calls',[]),('prefix_models',[]),('critical',[]),('post_form_calls',[]),('capsule_calls',[]),('extra_calls',[]),('buffer_reads',[]),('buffer_writes',[]),('native_calls',[]),('models',[]),('creation_inputs',[]),('pid_overrides',[]),('seed_calls',[]),('additions',[]),('code',[]),('canaries',False),('unrelated_ram_unchanged',False)):
   x=copy.deepcopy(r);x[field]=[{}] if field=='capsule_calls' and self.trainer in (244,245) else value;mutants.append(x)
  for path in (('seed_after',),('plus_hits',),('header',1),('end','sp'),('end','r',4),('prefix_transition','seed'),('prefix_transition','observer_neutral'),('api_calls',1,'end',4),('extra_calls',0,'result',0),('extra_calls',1,'result',0),('buffer_writes',0,'value'),('models',0,'return_sp'),('native_calls',0,'after_seed'),('seed_calls',-1,'args',0),('post_form_calls',3,'value_byte')):
   x=copy.deepcopy(r);value=x
   for key in path[:-1]:value=value[key]
   old=value[path[-1]];value[path[-1]]=not old if type(old)is bool else old^1;mutants.append(x)
  for x in mutants:
   with self.assertRaises((ValueError,IndexError,KeyError)):self.require(x)
 def test_profile_identity_capsule_slice_and_non_target_packets_are_bound(self):
  m=self.m
  for lang in ('EN','IT'):
   normal=self.normal(lang);x=copy.deepcopy(normal);x['trainer']=31 if self.trainer==21 else 21
   with self.assertRaisesRegex(ValueError,'profile identity'):self.require(x,lang)
   x=copy.deepcopy(normal)
   if self.trainer in (244,245):
    self.assertEqual(normal['capsule_calls'],[]);self.assertNotIn('185',self.reports[lang]['resources']['archives']);self.assertTrue(all(v['result'][0]==0 for v in normal['native_calls'] if v['entry']=='0x2072a44'))
    for name in ('NARC_New','NARC_ReadFromMember','NARC_Delete'):
     x=copy.deepcopy(normal);x['models'].append(dict(name=name))
     with self.subTest(injected_capsule_service=name),self.assertRaisesRegex(ValueError,'no capsule services'):self.require(x,lang)
    x=copy.deepcopy(normal);next(v for v in x['native_calls'] if v['entry']=='0x2072a44')['result'][0]=1
    with self.assertRaisesRegex(ValueError,'BOOL result'):self.require(x,lang)
   else:
    self.assertIn('185',self.reports[lang]['resources']['archives']);event=next(v for v in x['models'] if v['name']=='NARC_ReadFromMember');event['args'][2]=264 if self.trainer==31 else 312
    with self.assertRaisesRegex(ValueError,'raw capsule'):self.require(x,lang)
   if self.trainer in (31,32,34,244,245):
    baseline=next(v for v in self.reports[lang]['old_recipe_baselines'] if v['plus']==1);slot,move_slot,before,after,pp=(2,2,325,247,15) if self.trainer==31 else (5,0,423,156,10) if self.trainer==32 else (5,0,3,280,15) if self.trainer==34 else (5,0,407,127,15) if self.trainer==244 else (3,3,94,384,10);self.assertEqual(normal['mon_hex'][slot],baseline['mon_hex'][slot]);self.assertEqual(normal['decoded'][slot]['moves'][move_slot],before)
    # A valid-checksum wrong non-target packet: duplicate325 for31, lastMon for32.
    x=copy.deepcopy(normal);raw=bytearray.fromhex(x['mon_hex'][slot]);pid,checksum=struct.unpack_from('<I',raw)[0],struct.unpack_from('<H',raw,6)[0];plain=bytearray(m.B._decrypt(raw[8:136],checksum));offset=32*m.B.PERMUTATIONS[((pid>>13)&31)%24].index(1);struct.pack_into('<H',plain,offset+2*move_slot,after);plain[offset+8+move_slot]=pp;checksum=sum(struct.unpack('<64H',plain))&65535;struct.pack_into('<H',raw,6,checksum);raw[8:136]=m.B._decrypt(plain,checksum);x['mon_hex'][slot]=raw.hex();x['decoded'][slot]=m.M.decode(raw);self.assertTrue(x['decoded'][slot]['checksum_ok'])
    with self.assertRaisesRegex(ValueError,'source/IV'):self.require(x,lang)
    with self.assertRaisesRegex(ValueError,'changes no other'):m.compare_strategy_delta(x,baseline)
   if self.trainer==33:
    baseline=next(v for v in self.reports[lang]['old_recipe_baselines'] if v['plus']==1);self.assertEqual(normal['decoded'][4]['moves'][3],360);self.assertEqual(normal['mon_hex'][4],baseline['mon_hex'][4])
    for delta,pp in m.deltas_for(33):
     x=copy.deepcopy(normal);slot=delta['offset']//18;move_slot=(delta['offset']%18-8)//2;raw=bytearray.fromhex(x['mon_hex'][slot]);pid,checksum=struct.unpack_from('<I',raw)[0],struct.unpack_from('<H',raw,6)[0];plain=bytearray(m.B._decrypt(raw[8:136],checksum));offset=32*m.B.PERMUTATIONS[((pid>>13)&31)%24].index(1);struct.pack_into('<H',plain,offset+2*move_slot,delta['before']);plain[offset+8+move_slot]=pp[0];checksum=sum(struct.unpack('<64H',plain))&65535;struct.pack_into('<H',raw,6,checksum);raw[8:136]=m.B._decrypt(plain,checksum);x['mon_hex'][slot]=raw.hex();x['decoded'][slot]=m.M.decode(raw);self.assertTrue(x['decoded'][slot]['checksum_ok'])
     with self.assertRaisesRegex(ValueError,'source/IV'):self.require(x,lang)
     with self.assertRaises(ValueError):m.compare_strategy_delta(x,baseline)
    for field in ('ratio_stores','getter-result','getter-args','core-count'):
     x=copy.deepcopy(normal)
     if field=='ratio_stores':x['pid_overrides'][-1]['ratio_stores']=[]
     elif field=='core-count':next(v for v in x['extra_calls'] if v['entry']=='0x23d602c')['result'][0]=1
     else:
      event=next(v for v in x['extra_calls'] if v['entry']=='0x206fbc4');event['result' if field=='getter-result' else 'args'][0]^=1
     with self.assertRaises(ValueError):self.require(x,lang)
 def test_new_getter_permutation_and_parent_source_admission_refuse_drift(self):
  m=self.m
  for address in m.REQUIRED_PROFILE_PCS.get(self.trainer,()):
   r=copy.deepcopy(self.normal());r['code']=[row for row in r['code'] if int(row['ram'],16)!=address]
   with self.subTest(missing_executed_pc=hex(address)),self.assertRaisesRegex(ValueError,'profile-specific executed'):self.require(r)
  def changed(address):
   model=dict(self.models['EN']);segments=[]
   for base,blob in model['segments']:
    data=bytearray(blob)
    if base<=address<base+len(data):data[address-base]^=1
    segments.append((base,bytes(data)))
   model['segments']=segments;return model
  with self.paths['EN'].open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:
   for address in (0x201FD2C,0x201FD34,0x2072630,0x20FF733,0x20FF787,0x20FF7B2,0x20FF639,0x23D6000,0x23D6244,0x23D66A6,0x20FFB90+self.m.profile_for(self.trainer)['class_id'])+((0x2073AB0,0x2073AB2,0x2073ACC,0x207000E) if self.trainer==33 else (0x2070006,0x2070008) if self.trainer==34 else (0x207000E,0x2070010) if self.trainer==245 else ()):
    with self.subTest(address=hex(address)),self.assertRaises(ValueError):m.qualify(changed(address),raw,'EN',Path(os.environ['SGP_REMATCH_OBJECTS_DIR']),Path(os.environ['SGP_STRATEGY_OBJECT']),trainer=self.trainer)


if __name__=='__main__':unittest.main()
