"""Portable guards and private receipt replay for native species-name APIs."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,sys,tempfile,types,unittest
from unittest.mock import Mock,patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_nome_specie.py';s=importlib.util.spec_from_file_location('native_species',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.v=tool()
 def test_finite_domain_before_cpu_or_profile_data(self):
  v=self.v
  for species,kwargs in ((True,{}),(21,{}),(493,{}),(200,dict(fill=True)),(200,dict(observe=1)),(200,dict(void_return=True)),(200,dict(variant='other')),(355,dict(variant='short_capacity'))):
   with patch.object(v,'Uc') as cpu,self.assertRaises(ValueError):v.Species(None,None,None,species,**kwargs)
   cpu.assert_not_called()
 def test_optimized_python_refused_before_cpu(self):
  v=self.v
  with patch.object(v.sys,'flags',types.SimpleNamespace(optimize=1)),patch.object(v,'Uc') as cpu,self.assertRaises(ValueError):v.Species(None,None,None,200)
  cpu.assert_not_called()
 def test_cli_existing_alias_and_source_output_protection(self):
  v=self.v
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);rom=root/'own.nds';rom.write_bytes(b'unchanged');sym=root/'link';sym.symlink_to(rom);hard=root/'hard';os.link(rom,hard)
   for output in (rom,sym,hard,SOURCE/'new-species.json'):
    argv=['species','--rom',str(rom),'--retail',str(rom),'--base',str(rom),'--v4',str(rom),'--language','EN','--json',str(output)]
    with patch.object(sys,'argv',argv),patch.object(v,'analyze') as analyze,self.assertRaises(SystemExit) as e:v.main()
    self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   self.assertEqual(rom.read_bytes(),b'unchanged')
 def test_wrapper_pop_reads_use_outer_stack_not_nested_message_top(self):
  v=self.v;d=v.Species.__new__(v.Species);d.outer_phase='get_species';d.current_internal=None;d.core=types.SimpleNamespace(read=Mock());d.read(None,0,v.TOP-8,4,0,None);d.core.read.assert_not_called()
  with self.assertRaises(ValueError):d.read(None,0,v.INNER-4,4,0,None)
 def test_scope_changes_metadata_without_guest_mutation(self):
  v=self.v;d=v.Species.__new__(v.Species);regs=list(range(16));d.regs=lambda:list(regs);d.read_bytes=lambda a,n:b'own synthetic RAM';d.namespace={'TOP':v.TOP};d.core=types.SimpleNamespace(phase=None);d.transitions=[];d.scope(v.INNER,'new_msg');self.assertEqual(d.regs(),regs);self.assertEqual(d.namespace['TOP'],v.INNER);self.assertTrue(d.transitions[0]['neutral'])
 def test_os_peak_rss_units_and_observed_over_budget_calibration(self):
  import resource
  v=self.v
  for platform,value,expected in (('darwin',777928704,777928704),('linux',759696,777928704)):
   with patch.object(v.sys,'platform',platform),patch.object(resource,'getrusage',return_value=types.SimpleNamespace(ru_maxrss=value)):self.assertEqual(v.require_host_budget(),expected)
  with patch.object(v.sys,'platform','darwin'),patch.object(resource,'getrusage',return_value=types.SimpleNamespace(ru_maxrss=1102741504)),self.assertRaisesRegex(ValueError,'exceeds'):v.require_host_budget()

@unittest.skipUnless(os.environ.get('SGP_SPECIES_ROM_DIR') and os.environ.get('SGP_SPECIES_REPORT_DIR'),'requires private exact ROMs and species-name reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.v=v=tool();cls.reports={};cls.data={};cls.qualified={}
  for lang in os.environ.get('SGP_SPECIES_LANGUAGES','EN,IT').split(','):
   path=Path(os.environ['SGP_SPECIES_ROM_DIR'])/('r4-'+lang+'.nds');model=v.P.G.S.SHARED.read_current(path,lang)
   with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:qualified,_=v.qualify(model,raw);data=v.resources(raw)
   with gzip.open(Path(os.environ['SGP_SPECIES_REPORT_DIR'])/('species-'+lang+'.json.gz'),'rb') as f:payload=f.read(4*1024**2+1)
   assert len(payload)<=4*1024**2;report=json.loads(payload);assert report['schema']=='native-species-name-v1' and report['input']==json.loads(json.dumps(model['record'])) and report['resources']==data['oracle'];cls.reports[lang]=report;cls.data[lang]=data;cls.qualified[lang]=qualified
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['cases'][0])
 def require(self,r,lang='EN'):self.v.require_case(r,self.data[lang],self.qualified[lang])
 def test_complete_matrix_and_defined_pointer_void_controls(self):
  for lang,r in self.reports.items():
   self.assertEqual((len(r['cases']),len(r['observer_off']),len(r['void_controls']),len(r['counters'])),(18,3,2,6));self.assertEqual([(x['species'],x['fill']) for x in r['cases']],[(s,f) for s in self.v.SPECIES for f in (0,0xC7,0x39)])
   for case in r['cases']+r['void_controls']:self.require(case,lang)
   self.assertEqual([x['void_return'] for x in r['void_controls']],[0,0xFFFFFFFF])
 def test_native_heap_zero_bytes_match_existing_model_and_spare_tracks_fill(self):
  for lang,r in self.reports.items():
   for i,species in enumerate(self.v.SPECIES):
    a,b,c=r['cases'][3*i:3*i+3];self.assertEqual(self.v.sha(bytes.fromhex(a['snapshots']['returned_string'])),self.data[lang]['oracle']['records'][str(species)]['model_sha256']);self.assertEqual([x['snapshots']['returned_string'][-4:] for x in (a,b,c)],['0000','c7c7','3939']);self.assertEqual(len({x['destination_hex'] for x in (a,b,c)}),1)
 def test_actual_lifetime_is_string_only_after_getter_then_empty(self):
  for change in ('live','handle','snapshot','internal_order'):
   r=self.base()
   if change=='live':r['api'][0]['live']={}
   elif change=='handle':r['api'][0]['handle_live']=True
   elif change=='snapshot':r['snapshots']['returned_string']='00'*len(bytes.fromhex(r['snapshots']['returned_string']))
   else:r['internal'][1],r['internal'][2]=r['internal'][2],r['internal'][1]
   with self.subTest(change=change),self.assertRaises(ValueError):self.require(r)
 def test_native_transcripts_helpers_and_contexts_cannot_be_stripped(self):
  for key in ('api','internal','models','native_helpers','native_writes','wrapper_writes','writes','observed_pcs','transitions','allocations'):
   r=self.base();r[key]=r[key][:-1]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
  r=self.base();r['writes'][0]['value']^=1
  with self.assertRaises(ValueError):self.require(r)
 def test_internal_top_and_outer_return_lr_are_real_not_standalone_message_contexts(self):
  for index in range(3):
   r=self.base();r['internal'][index]['before'][13]=self.v.TOP
   with self.assertRaises(ValueError):self.require(r)
  r=self.base();r['api'][0]['after'][14]=0x200BCFF
  with self.assertRaises(ValueError):self.require(r)
 def test_off_and_executed_counters_have_expected_causes(self):
  for lang,r in self.reports.items():
   normal=next(x for x in r['cases'] if x['species']==200 and x['fill']==0)
   for off in r['observer_off']:
    on=next(x for x in r['cases'] if x['species']==off['result']['species'] and x['fill']==0);self.assertEqual(self.v.require_off_pair(on,off['result']),off['proof'])
   for counter in r['counters']:
    self.v.require_counter(counter,normal,self.data[lang],self.qualified[lang]);bad=copy.deepcopy(counter);bad['rejection']='unrelated preflight error'
    with self.assertRaises(ValueError):self.v.require_counter(bad,normal,self.data[lang],self.qualified[lang])
 def test_historical_retail_key_is_not_replaced_by_current_plus_key(self):
  for r in self.reports.values():
   self.assertEqual([h['resources']['key'] for h in r['history']],[0x782C,0xD00E,0xD00E,0xD00E]);self.assertEqual([h['native_address_attributed'] for h in r['history']],[r['language']=='EN',True,True,True])
 def test_cipher_bytes_and_pointer_return_evidence_bound_to_raw(self):
  for index in (2,3,6):
   r=self.base();r['models'][index]['delivered_sha256']='0'*64
   with self.assertRaises(ValueError):self.require(r)
  for index in (0,1,3,4):
   r=self.base();r['native_helpers'][index]['result_r0']^=1
   with self.assertRaises(ValueError):self.require(r)
if __name__=='__main__':unittest.main()
