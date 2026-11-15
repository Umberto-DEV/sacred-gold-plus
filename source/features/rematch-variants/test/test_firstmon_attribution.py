"""Finite native first-Pokemon continuation and meaningful same-output counterproofs."""
from pathlib import Path
import copy,gzip,importlib.util,mmap,os,sys,tempfile,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]


def tool():
 s=importlib.util.spec_from_file_location('rematch_firstmon_attribution',SOURCE/'features/rematch-variants/tools/attribuisci_primo_mon.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class FirstMonCLI(unittest.TestCase):
 def test_existing_inputs_aliases_and_public_outputs_are_preserved(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);objects=root/'objects';objects.mkdir();inputs=[root/'r4.nds',objects/'rematch-variants.o',objects/'rematch-stub.o',root/'teams.o']
   for p in inputs:p.write_bytes(b'preserve')
   targets=[SOURCE/'forbidden-new.json',objects/'forbidden-new.json']
   for i,p in enumerate(inputs):
    sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);targets.extend((p,sym,hard))
   for target in targets:
    argv=['firstmon','--rom',str(inputs[0]),'--objects',str(objects),'--strategy-object',str(inputs[-1]),'--language','EN','--json',str(target)]
    with self.subTest(target=target.name),patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')
 def test_firstmon_lineage_cli_preserves_all_four_inputs_and_aliases(self):
  s=importlib.util.spec_from_file_location('firstmon_stage_reader',SOURCE/'features/rematch-variants/tools/rileggi_stadi.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);inputs=[root/(str(i)+'.nds') for i in range(4)];targets=[SOURCE/'forbidden-new.json']
   for i,p in enumerate(inputs):
    p.write_bytes(b'preserve');sym=root/(str(i)+'.sym');sym.symlink_to(p);hard=root/(str(i)+'.hard');os.link(p,hard);targets.extend((p,sym,hard))
   for target in targets:
    argv=['lineage','--firstmon','--language','IT','--json',str(target)]
    for name,p in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(p)))
    with patch.object(sys,'argv',argv),patch.object(m,'analyze') as analyze:
     with self.assertRaises(SystemExit) as e:m.main()
     self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   for p in inputs:self.assertEqual(p.read_bytes(),b'preserve')
 def test_gzip_report_has_no_personal_filename_and_no_timestamp(self):
  m=tool()
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);obj=root/'objects';obj.mkdir();inputs=[root/'r4.nds',obj/'rematch-variants.o',obj/'rematch-stub.o',root/'teams.o']
   for p in inputs:p.write_bytes(b'input')
   argv=['firstmon','--rom',str(inputs[0]),'--objects',str(obj),'--strategy-object',str(inputs[-1]),'--language','EN','--json',str(root/'private-name.json.gz')]
   with patch.object(sys,'argv',argv),patch.object(m,'analyze',return_value={'schema':'test'}):m.main()
   payload=(root/'private-name.json.gz').read_bytes();self.assertEqual(payload[3:8],bytes(5));self.assertNotIn(b'private-name',payload);self.assertIn(b'"schema": "test"',gzip.decompress(payload))


@unittest.skipUnless(all(os.environ.get(k) for k in ('SGP_R4_ROM_DIR','SGP_REMATCH_OBJECTS_DIR','SGP_STRATEGY_OBJECT')),'requires exact r4 EN/IT and qualified rematch/strategy objects')
class NativeFirstMon(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  m=cls.m=tool();cls.paths={};cls.models={};cls.codes={};cls.data={}
  for lang in ('EN','IT'):
   p=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%lang);cls.paths[lang]=p;model=cls.models[lang]=m.P.G.S.SHARED.read_current(p,lang);m.attest_post_form(model)
   with p.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
    prefix,_=m.A.attest_objects(raw,model,Path(os.environ['SGP_REMATCH_OBJECTS_DIR']));proof=m.attest_strategy_object(model,raw,Path(os.environ['SGP_STRATEGY_OBJECT']));cls.codes[lang]=(prefix,m.C.qualify_code(model,proof),*m.qualify(model,lang));cls.data[lang]=m.resources(raw,model)
 def cpu(self,lang='EN',**kwargs):
  with self.paths[lang].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:return self.m.run_case(self.models[lang],raw,lang,*self.codes[lang],**kwargs)
 def test_four_first_records_create_encrypted_mon_and_insert_actual_party_slot(self):
  for lang in ('EN','IT'):
   for trainer in (712,713):
    for seed in (0x12345678,0x12345679):
     r=self.cpu(lang,trainer=trainer,seed=seed);self.m.require_firstmon(r,self.data[lang]);self.assertEqual(r['max_stack'],512)
 def test_wrong_fourth_move_missing_add_and_identical_zero_held_output_are_rejected(self):
  for lang in ('EN','IT'):
   baseline=self.cpu(lang)
   for variant in ('wrong_fourth_move','skip_party_add','skip_held_zero'):
    r=self.cpu(lang,mon_variant=variant);self.assertEqual(r['mon']['buffer_sha256'],baseline['mon']['buffer_sha256'])
    if variant=='skip_held_zero':self.assertEqual(r['mon'],baseline['mon'])
    if variant=='skip_party_add':self.assertEqual(r['mon']['workspace_hex'],baseline['mon']['workspace_hex']);self.assertEqual(r['mon']['party_header'],[6,0])
    with self.assertRaises(ValueError):self.m.require_firstmon(dict(r,mon_variant='current'),self.data[lang])
 def test_sdk_volatile_poison_and_adjacent_nonzero_party_byte_preserve_outputs(self):
  base=self.cpu()
  for kw in ({'poison':True},{'neighbor_guard':True}):
   r=self.cpu(**kw);self.m.require_firstmon(r,self.data['EN']);self.assertEqual(r['mon'],base['mon'])
 def test_oracle_rejects_forged_semantics_and_incomplete_execution(self):
  m=self.m;r=self.cpu();mutants=[]
  for key in ('workspace_hex','party_hex'):
   x=copy.deepcopy(r);blob=bytearray.fromhex(x['mon'][key]);blob[12]^=1;x['mon'][key]=blob.hex();mutants.append((key,x))
  for path in [('mon','r0'),('mon','sp'),('mon','seed'),('mon','party_header',1),('mon','decoded','pp',3),('native_calls',1,'after_seed'),('native_calls',1,'result',0),('native_calls',3,'args',1),('native_calls',3,'return_sp'),('native_calls',3,'return_saved',1),('models',0,'return_sp'),('models',0,'return_saved',1),('post_form_calls',0,'return_sp'),('post_form_calls',2,'args',1),('post_form_calls',3,'value_byte'),('neighbor_after',)]:
   x=copy.deepcopy(r);v=x
   for key in path[:-1]:v=v[key]
   v[path[-1]]^=1;mutants.append((str(path),x))
  for field,value in (('code',[]),('native_calls',[]),('post_form_calls',[]),('models',[]),('writes',[]),('canaries',False),('unrelated_ram_unchanged',False),('live_allocations',{1:4}),('instructions',500001),('max_stack',513)):
   x=copy.deepcopy(r);x[field]=value;mutants.append((field,x))
  # Re-seal genuine encrypted records, keeping checksum, party copy and reported
  # decoder internally consistent: these must fail the resource/semantic oracle.
  for block,offset in ((0,4),(0,8),(0,15),(1,8),(1,16),(2,0)):
   x=copy.deepcopy(r);blob=bytearray.fromhex(x['mon']['workspace_hex']);pid,flags,checksum=m.struct.unpack_from('<IHH',blob);clear=bytearray(m.B._decrypt(blob[8:136],checksum));order=m.B.PERMUTATIONS[((pid>>13)&31)%24];clear[order.index(block)*32+offset]^=1;checksum=sum(m.struct.unpack('<64H',clear))&65535;m.struct.pack_into('<H',blob,6,checksum);blob[8:136]=m.B._decrypt(clear,checksum);x['mon']['workspace_hex']=x['mon']['party_hex']=blob.hex();x['mon']['decoded']=m.B.decode_mon(blob);mutants.append(('resealed '+str((block,offset)),x))
  for offset in (6,10):
   x=copy.deepcopy(r);blob=bytearray.fromhex(x['mon']['workspace_hex']);blob[136+offset]^=1;x['mon']['workspace_hex']=x['mon']['party_hex']=blob.hex();x['mon']['decoded']=m.B.decode_mon(blob);mutants.append(('party stat '+str(offset),x))
  for name,x in mutants:
   with self.subTest(name=name),self.assertRaises(ValueError):m.require_firstmon(x,self.data['EN'])
 def test_raw_code_pools_and_data_drift_fail_admission(self):
  m=self.m;model=self.models['EN'];q=m.json.loads(m.QUALIFICATION.read_text())
  for row in q['code'][::17]+q['data'][::9]+[dict(start='0x2073b15')]:
   a=int(row['start'],16);changed=dict(model);segments=[]
   for base,blob in model['segments']:
    b=bytearray(blob)
    if base<=a<base+len(b):b[a-base]^=1
    segments.append((base,bytes(b)))
   changed['segments']=segments
   with self.subTest(address=hex(a)),self.assertRaises(ValueError):
    if a==0x2073B15:m.attest_post_form(changed)
    else:m.qualify(changed,'EN')
 def test_new_instruction_read_write_and_lifetime_guards_refuse_invalid_access(self):
  m=self.m;model=self.models['EN']
  with self.paths['EN'].open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
   b=m.P.Adapter(model,raw,'EN');b.module_code=self.codes['EN'][0];cpu=m.First(b,712);u=cpu.factory(m.B.UC_ARCH_ARM,m.B.UC_MODE_THUMB);u.mem_map(0x02000000,0x400000);u.reg_write(m.P.UC_ARM_REG_SP,m.B.STACK_TOP);cpu.mon=True;cpu.mon_allowed=self.codes['EN'][2];cpu.mon_data=self.codes['EN'][3]
   for a,n in ((m.B.PARTIES+0x1000+244,4),(m.B.ARENA+500,4),(0x21D15A8,2)):
    with self.subTest(address=hex(a)),self.assertRaises(ValueError):cpu.write(u,0,a,n,0,None)
   for a in (m.B.ARENA+500,m.B.ARENA+108,0x2390000):
    with self.subTest(address=hex(a)),self.assertRaises(ValueError):cpu.read(u,0,a,4,0,None)
   # A real literal pool is never an executable entry.
   with self.assertRaises(ValueError):cpu.step(u,0x201FD5C,4,None)


if __name__=='__main__':unittest.main()
