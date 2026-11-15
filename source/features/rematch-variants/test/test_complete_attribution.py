"""Six native Pokemon, source state lifetime and actual constructor return."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,sys,tempfile,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]


def tool():
 s=importlib.util.spec_from_file_location('complete_rematch_attribution',SOURCE/'features/rematch-variants/tools/attribuisci_squadra_completa.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class CompleteCLI(unittest.TestCase):
 def test_existing_inputs_aliases_and_public_outputs_are_preserved(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);obj=root/'objects';obj.mkdir();inputs=[root/'r4.nds',obj/'rematch-variants.o',obj/'rematch-stub.o',root/'teams.o'];targets=[SOURCE/'forbidden-new.json',obj/'forbidden-new.json']
   for i,p in enumerate(inputs):
    p.write_bytes(b'preserve');sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);targets.extend((p,sym,hard))
   for target in targets:
    argv=['complete','--rom',str(inputs[0]),'--objects',str(obj),'--strategy-object',str(inputs[-1]),'--language','IT','--json',str(target)]
    with patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')
 def test_retained_object_does_not_hide_current_recipe_source_drift(self):
  m=tool();self.assertEqual(len(m.attest_recipe_sources()),6);original=Path.read_bytes
  for name in m.RECIPE_SOURCES:
   target=m.P.SOURCE/name
   def changed(path):return original(path)+(b' changed source' if path==target else b'')
   with self.subTest(source=name),patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'recipe source drift'):m.attest_recipe_sources()
 def test_new_gzip_is_deterministic_and_oversized_output_is_refused(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);obj=root/'objects';obj.mkdir();inputs=[root/'r4.nds',obj/'rematch-variants.o',obj/'rematch-stub.o',root/'teams.o']
   for p in inputs:p.write_bytes(b'input')
   out=root/'private-name.json.gz';argv=['complete','--rom',str(inputs[0]),'--objects',str(obj),'--strategy-object',str(inputs[-1]),'--language','EN','--json',str(out)]
   with patch.object(sys,'argv',argv),patch.object(m,'analyze',return_value={'schema':'test'}):m.main()
   payload=out.read_bytes();self.assertEqual(payload[3:8],bytes(5));self.assertNotIn(b'private-name',payload);self.assertEqual(json.loads(gzip.decompress(payload)),{'schema':'test'})
   argv[-1]=str(root/'oversized.json.gz')
   with patch.object(sys,'argv',argv),patch.object(m,'analyze',return_value={'data':'x'*(16*1024*1024)}):
    with self.assertRaises(SystemExit) as e:m.main()
    self.assertEqual(e.exception.code,2);self.assertFalse(Path(argv[-1]).exists())
 def test_complete_lineage_preserves_inputs_and_rejects_incompatible_case_flags(self):
  s=importlib.util.spec_from_file_location('complete_lineage',SOURCE/'features/rematch-variants/tools/rileggi_stadi.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);inputs=[root/(str(i)+'.nds') for i in range(4)];targets=[SOURCE/'forbidden-new.json']
   for i,p in enumerate(inputs):
    p.write_bytes(b'preserve');sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);targets.extend((p,sym,hard))
   for target in targets+[root/'both-flags.json']:
    argv=['lineage','--complete','--language','EN','--json',str(target)]
    for name,p in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(p)))
    if target.name=='both-flags.json':argv.append('--firstmon')
    with patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')


@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_R4_ROM_DIR','SGP_REMATCH_OBJECTS_DIR','SGP_STRATEGY_OBJECT')),'requires exact r4 EN/IT and qualified rematch/strategy objects')
class CompleteNativeConstructor(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  m=cls.m=tool();cls.paths={};cls.models={};cls.codes={};cls.data={};cls.cache={}
  for lang in ('EN','IT'):
   p=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%lang);model=m.P.G.S.SHARED.read_current(p,lang);cls.paths[lang]=p;cls.models[lang]=model;m.M.attest_post_form(model)
   with p.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
    prefix,_=m.A.attest_objects(raw,model,Path(os.environ['SGP_REMATCH_OBJECTS_DIR']));proof=m.M.attest_strategy_object(model,raw,Path(os.environ['SGP_STRATEGY_OBJECT']));cls.codes[lang]=(prefix,m.C.qualify_code(model,proof),*m.M.qualify(model,lang),*m.qualify(model,lang));cls.data[lang]=m.resources(raw,model)
 def cpu(self,lang='EN',trainer=713,seed=0x12345678,variant='current',poison=False,entry_cookies=False):
  key=(lang,trainer,seed,variant,poison,entry_cookies)
  if key not in self.cache:
   with self.paths[lang].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:self.cache[key]=self.m.run_case(self.models[lang],raw,lang,*self.codes[lang],trainer=trainer,seed=seed,variant=variant,poison=poison,entry_cookies=entry_cookies)
  return self.cache[key]
 def test_eight_complete_parties_match_raw_resources_and_restore_seed_and_lifetime(self):
  for lang in ('EN','IT'):
   for trainer in (712,713):
    for seed in (0x12345678,0x12345679):
     r=self.cpu(lang,trainer,seed);self.m.require_complete(r,self.data[lang]);self.assertEqual(r['max_stack'],512);self.assertEqual(len(r['additions']),5)
 def test_counterproofs_preserve_orthogonal_results_but_cannot_pass_as_normal(self):
  normal=self.cpu()
  for variant in ('wrong_restore_seed','omit_prefix_free','wrong_capsule_slice','reset_pid_gender'):
   r=self.cpu(variant=variant);self.assertEqual(r['header'],[6,6])
   if variant in ('wrong_restore_seed','omit_prefix_free'):self.assertEqual(r['mon_hex'],normal['mon_hex'])
   if variant!='wrong_restore_seed':self.assertEqual(r['seed_after'],normal['seed_after'])
   if variant=='reset_pid_gender':self.assertEqual(r['mon_hex'][0],normal['mon_hex'][0]);self.assertEqual(r['decoded'][1]['pid']&255,0x78);self.assertEqual(normal['decoded'][1]['pid']&255,0x79)
   with self.subTest(variant=variant),self.assertRaises(ValueError):self.m.require_complete(dict(r,variant='current'),self.data['EN'])
 def test_sdk_volatile_poison_and_nonzero_constructor_caller_registers_are_neutral(self):
  normal=self.cpu()
  for kw in ({'poison':True},{'entry_cookies':True}):
   r=self.cpu(**kw);self.m.require_complete(r,self.data['EN']);self.assertEqual(r['mon_hex'],normal['mon_hex']);self.assertEqual(r['seed_after'],normal['seed_after'])
 def test_oracle_rejects_validly_resealed_later_members_extra_state_and_false_receipts(self):
  m=self.m;r=self.cpu();mutants=[]
  for field,value in (('header',[6,5]),('seed_after',r['seed_after']^1),('plus_hits',5),('party_extra_hex','01'+'00'*29),('party_tail_hex','0100'),('additions',[]),('capsule_calls',[]),('creation_inputs',[]),('post_form_calls',[]),('pid_overrides',[]),('models',[]),('seed_calls',[]),('global_writes',[]),('native_calls',[]),('live_allocations',{m.B.ARENA:108}),('canaries',False),('first_receipt_observer_neutral',False),('max_stack',513),('instructions',3000001)):
   x=copy.deepcopy(r);x[field]=value;mutants.append((field,x))
  for path in [('end',4),('end',8),('end',13),('seed_calls',-1,'args',0),('seed_calls',-1,'return_sp'),('capsule_calls',1,'return_saved',0),('pid_overrides',0,'after_gender'),('post_form_calls',4,'args',0),('post_form_calls',4,'lr'),('models',-1,'return_sp')]:
   x=copy.deepcopy(r);v=x
   for k in path[:-1]:v=v[k]
   if isinstance(v[path[-1]],str):v[path[-1]]='0x0'
   else:v[path[-1]]^=1
   mutants.append((str(path),x))
  # Modify later members, reseal boxed checksum and keep the independent reported
  # decoder consistent. Correct slot0, six-count and final seed must not suffice.
  for slot,block,offset in ((1,0,2),(2,1,6),(4,0,4),(5,0,8)):
   x=copy.deepcopy(r);blob=bytearray.fromhex(x['mon_hex'][slot]);pid,flags,checksum=m.struct.unpack_from('<IHH',blob);clear=bytearray(m.B._decrypt(blob[8:136],checksum));order=m.B.PERMUTATIONS[((pid>>13)&31)%24];clear[order.index(block)*32+offset]^=1;checksum=sum(m.struct.unpack('<64H',clear))&65535;m.struct.pack_into('<H',blob,6,checksum);blob[8:136]=m.B._decrypt(clear,checksum);x['mon_hex'][slot]=blob.hex();x['decoded'][slot]=dict(m.M.decode(blob),capsule_hex=m.B._decrypt(blob[136:],pid)[76:100].hex());mutants.append(('resealed slot'+str(slot),x))
  for offset in (6,10,76):
   x=copy.deepcopy(r);blob=bytearray.fromhex(x['mon_hex'][1]);pid=m.struct.unpack_from('<I',blob)[0];blob[136+offset]^=1;x['mon_hex'][1]=blob.hex();x['decoded'][1]=dict(m.M.decode(blob),capsule_hex=m.B._decrypt(blob[136:],pid)[76:100].hex());mutants.append(('party field'+str(offset),x))
  x=copy.deepcopy(r);blob=bytearray.fromhex(x['mon_hex'][1]);blob[4]^=1;pid=m.struct.unpack_from('<I',blob)[0];x['mon_hex'][1]=blob.hex();x['decoded'][1]=dict(m.M.decode(blob),capsule_hex=m.B._decrypt(blob[136:],pid)[76:100].hex());self.assertTrue(x['decoded'][1]['checksum_ok']);digest=m.P.sha(blob);x['additions'][0]['mon_sha256']=x['additions'][0]['slot_sha256']=digest
  expected_function=m.expectations
  def omit_flag_oracle(record,data):
   expected=expected_function(record,data)
   for member in expected:member['fields'].pop('flags')
   return expected
  with patch.object(m,'expectations',side_effect=omit_flag_oracle):self.assertTrue(m.require_complete(x,self.data['EN']))
  mutants.append(('quiescent header lock flag with valid checksum/copy receipts',x))
  for name,x in mutants:
   with self.subTest(name=name),self.assertRaises(ValueError):m.require_complete(x,self.data['EN'])
 def test_code_data_sdk_binding_and_recipe_padding_drift_are_refused(self):
  m=self.m;model=self.models['EN']
  for pc,shape in self.codes['EN'][-2].items():
   if pc>=0x23D6000:self.assertEqual(self.codes['EN'][1].get(pc),shape,'full sparse PC must be code in independent strategy ELF/Plus mapping')
  q=m.json.loads(m.QUALIFICATION.read_text());targets=[int(x['start'],16) for x in q['code'][::19]+q['data'][::11]]+[0x2007688,0x2007708,0x210F4F4,0x210EC28,0x2073B15]
  for a in targets:
   changed=dict(model);segments=[]
   for base,blob in model['segments']:
    b=bytearray(blob)
    if base<=a<base+len(b):b[a-base]^=1
    segments.append((base,bytes(b)))
   changed['segments']=segments
   with self.subTest(address=hex(a)),self.assertRaises(ValueError):
    if a in (0x2007688,0x2007708,0x210F4F4,0x210EC28):m.capsule_binding(changed)
    elif a==0x2073B15:m.M.attest_post_form(changed)
    else:m.qualify(changed,'EN')
 def test_new_memory_and_capsule_sdk_guards_reject_invalid_access(self):
  m=self.m
  with self.paths['EN'].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   b=m.P.Adapter(self.models['EN'],raw,'EN');b.module_code=self.codes['EN'][0];cpu=m.Full(b,713);u=cpu.factory(m.B.UC_ARCH_ARM,m.B.UC_MODE_THUMB);u.mem_map(0x02000000,0x400000);u.reg_write(m.P.UC_ARM_REG_SP,m.B.STACK_TOP-64);cpu.full=cpu.mon=True;cpu.pending_native=[];cpu.mon_allowed=self.codes['EN'][-2];cpu.mon_data=self.codes['EN'][-1];cpu.next_arena=m.B.ARENA+0x1000
   for pc,a,n,value in ((0,m.B.PARTIES+0x1000,4,0),(0,m.B.PARTIES+0x1000+0x5B0,1,0),(0x201FD52,0x21D15A8,2,0),(0x201FD52,0x21D15A8,4,0)):
    u.reg_write(m.P.UC_ARM_REG_PC,pc)
    with self.assertRaises(ValueError):cpu.write(u,0,a,n,value,None)
   for a in (m.B.ARENA+500,m.B.STACK_TOP-516,0x2390000):
    with self.assertRaises(ValueError):cpu.read(u,0,a,4,0,None)
   with self.assertRaises(ValueError):cpu.step(u,0x201FD5C,4,None)
   for idx,(args,lr,entry) in enumerate((([184,11,0,0],0x2072A5F,0x2007688),([0xBAD,0,264,24],0x2072A77,0x200782C),([0xBAD,0,264,23],0x2072A77,0x200782C),([0xBAD,0,3050,24],0x2072A77,0x200782C),([0xBAD,0,264,24],0x2072A77,0x200782C),([0xBAD,0,0,0],0x2072A91,0x200770C))):
    cpu.handles={0xBAD:185} if idx in (2,3,4) else {}
    for i,value in enumerate(args):u.reg_write(m.B.R[i],value)
    u.reg_write(m.C.UC_ARM_REG_LR,lr)
    with self.assertRaises(ValueError):cpu.step(u,entry,2,None)


if __name__=='__main__':unittest.main()
