"""Native move/PP consumer at an explicit copied-Mon fixture boundary."""
from pathlib import Path
import importlib.util,tempfile,os,sys,json,gzip,mmap,struct,unittest,copy
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 s=importlib.util.spec_from_file_location('strategy_move_attribution',SOURCE/'features/trainer-strategy/tools/attribuisci_mosse.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class Portable(unittest.TestCase):
 def test_outputs_preserve_all_inputs_aliases_source_and_objects(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);objects=root/'objects';objects.mkdir();rom=root/'r4.nds';obj=objects/'teams.o';report=root/'prior.json.gz';inputs=(rom,obj,report)
   for p in inputs:p.write_bytes(b'preserve')
   outputs=[]
   for i,p in enumerate(inputs):
    sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);outputs.extend((p,sym,hard))
   outputs.extend((SOURCE/'new.json',objects/'new.json',root))
   for out in outputs:
    args=['move','--rom',str(rom),'--language','EN','--strategy-object',str(obj),'--fixture-report',str(report),'--json',str(out)]
    with self.subTest(out=out.name),patch.object(sys,'argv',args),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')
 def test_expanded_fixture_budget_and_candidate_identity_precede_fixture_oracle(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'fixture.gz'
   for payload in (b'x'*(16*1024*1024+1),json.dumps(dict(schema='wrong')).encode(),json.dumps(dict(schema='rematch-complete-constructor-v1',input='foreign')).encode()):
    p.write_bytes(gzip.compress(payload))
    with patch.object(m.F,'require_complete') as oracle,self.assertRaises(ValueError):m.load_fixture(p,dict(record='expected'),None)
    oracle.assert_not_called()
 def test_pp_up_named_transform_reseals_synthetic_data_and_preserves_other_fields(self):
  m=tool();pid=0x12345678;fixture=struct.pack('<IHH',pid,0,0)+m.B._decrypt(bytes(128),0)+m.B._decrypt(bytes(100),pid);before=m.M.decode(fixture);after=m.M.decode(m.with_pp_up(fixture));self.assertTrue(after['checksum_ok']);self.assertEqual(after['pp_ups'],[0,2,0,0])
  for key in before:
   if key not in ('checksum','pp_ups'):self.assertEqual(before[key],after[key])


@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_R4_ROM_DIR','SGP_STRATEGY_OBJECT','SGP_COMPLETE_REPORT_DIR')),'requires exact ROMs,strategy ELF and preceding complete-constructor fixture reports')
class Current(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  m=cls.m=tool();cls.models={};cls.paths={};cls.data={};cls.moves={};cls.code={};cls.fixture={};cls.cache={};m.F.attest_recipe_sources()
  for lang in ('EN','IT'):
   p=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%lang);cls.paths[lang]=p;model=m.P.G.S.SHARED.read_current(p,lang);cls.models[lang]=model;report=Path(os.environ['SGP_COMPLETE_REPORT_DIR'])/(os.environ.get('SGP_COMPLETE_REPORT_NOME','complete-%s.json.gz')%lang)
   with p.open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:
    proof=m.M.attest_strategy_object(model,raw,Path(os.environ['SGP_STRATEGY_OBJECT']));cls.code[lang]=m.S.qualify(model,proof);cls.data[lang]=m.S.resources(raw,model);cls.moves[lang]=m.P.RAW.raw_archive(raw,'a/0/1/1')[0];cls.fixture[lang],_=m.load_fixture(report,model,raw)
 def case(self,lang='EN',plus=1,variant='current',poison=False,pp_up=False):
  key=lang,plus,variant,poison,pp_up
  if key not in self.cache:
   preapplied=bytes.fromhex(self.case(lang)['after']) if variant=='preapplied_skip' else None
   with self.paths[lang].open('rb') as file,mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as raw:self.cache[key]=self.m.run_case(self.models[lang],raw,lang,self.code[lang],self.data[lang],self.fixture[lang],plus,variant,poison,pp_up,preapplied)
  return self.cache[key]
 def require(self,r,lang='EN'):return self.m.require_case(r,self.data[lang],self.moves[lang],self.fixture[lang])
 def test_actual_normal_and_plus_loads_setters_pp_and_untouched_fields(self):
  for lang in ('EN','IT'):
   for plus in (0,1):
    r=self.case(lang,plus);self.require(r,lang);self.assertEqual(r['decoded_after']['moves'],[228,450 if plus else 206,97,17]);self.assertEqual(r['decoded_after']['pp'],[20,20 if plus else 40,30,35]);self.assertEqual(len(r['calls']),4)
 def test_sdk_volatile_poison_is_neutral_and_native_setter_preserves_pp_ups(self):
  for lang in ('EN','IT'):
   r=self.case(lang,poison=True);self.require(r,lang);self.assertEqual(r['after'],self.case(lang)['after'])
   for plus in (0,1):
    r=self.case(lang,plus,pp_up=True);self.require(r,lang);self.assertEqual(r['decoded_after']['pp_ups'],[0,2,0,0]);self.assertEqual(r['decoded_after']['pp'][1],28 if plus else 56)
 def test_wrong_move_wrong_pp_and_identical_output_missing_call_are_rejected(self):
  for lang in ('EN','IT'):
   baseline=self.case(lang)
   for variant in ('wrong_move','wrong_pp','preapplied_skip'):
    r=self.case(lang,variant=variant);self.assertTrue(r['decoded_after']['checksum_ok'])
    if variant=='wrong_pp':self.assertEqual(r['decoded_after']['moves'],baseline['decoded_after']['moves']);self.assertEqual(r['decoded_after']['pp'][1],21)
    if variant=='preapplied_skip':
     self.assertEqual(r['after'],baseline['after']);self.assertEqual(len(r['calls']),3)
     x=copy.deepcopy(r);x['variant']='current';x['shadows']=[];x['source_fixture_sha256']=self.m.P.sha(bytes.fromhex(x['before']));x['bridge'][0]['reason']='checked copied Mon fixture'
     with self.assertRaisesRegex(ValueError,'four actual native move calls'):self.m.require_case(x,self.data[lang],self.moves[lang],bytes.fromhex(x['before']))
    with self.assertRaises(ValueError):self.require(dict(r,variant='current',shadows=[]),lang)
 def test_pure_oracle_rejects_missing_boundary_initializer_caller_and_resource_evidence(self):
  r=self.case();mutants=[]
  for field,value in (('bridge',[]),('register_initialization',{}),('prefix_checkpoint',{}),('calls',[]),('reads',[]),('models',[]),('code',[]),('prefix_observer_neutral',False),('source_fixture_sha256','wrong'),('unrelated_ram_unchanged',False)):
   x=copy.deepcopy(r);x[field]=value;mutants.append(x)
  for path in (('bridge',0,'after_sha256'),('bridge',1,'after_sha256'),('prefix_checkpoint','frame64_hex'),('register_initialization','new_sp'),('entry',4),('end',7),('calls',0,'return_sp'),('models',0,'sha256'),('reads',0,'value')):
   x=copy.deepcopy(r);v=x
   for key in path[:-1]:v=v[key]
   old=v[path[-1]];v[path[-1]]=old^1 if type(old)is int else '00';mutants.append(x)
  for x in mutants:
   with self.assertRaises((ValueError,KeyError)):self.require(x)
 def test_same_decoded_fields_cannot_hide_other_decrypted_block_or_party_data_changes(self):
  m=self.m;r=self.case();raw=bytes.fromhex(r['after']);pid,flags,checksum=struct.unpack_from('<IHH',raw);order=m.B.PERMUTATIONS[((pid>>13)&31)%24]
  for block,offset in ((1,31),(3,31)):
   x=copy.deepcopy(r);plain=bytearray(m.B._decrypt(raw[8:136],checksum));plain[32*order.index(block)+offset]^=1;new=sum(struct.unpack('<64H',plain))&65535;mut=bytearray(raw);struct.pack_into('<H',mut,6,new);mut[8:136]=m.B._decrypt(bytes(plain),new);x['after']=bytes(mut).hex();x['decoded_after']=m.M.decode(mut)
   with self.assertRaises(ValueError):self.require(x)
  x=copy.deepcopy(r);mut=bytearray(raw);mut[-1]^=1;x['after']=bytes(mut).hex();x['decoded_after']=m.M.decode(mut)
  with self.assertRaises(ValueError):self.require(x)


if __name__=='__main__':unittest.main()
