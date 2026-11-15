"""Portable guards and private replay for the installed native NARC parser."""
from pathlib import Path
import copy,gzip,importlib.util,json,mmap,os,sys,tempfile,types,unittest
from unittest.mock import Mock,patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 p=SOURCE/'features/trainer-strategy/tools/attribuisci_lettore_narc.py';s=importlib.util.spec_from_file_location('native_narc_reader_test',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Portable(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.x=tool()
 def test_invalid_fixture_domain_refused_before_cpu(self):
  x=self.x
  for narc,kwargs in ((True,{}),(54,{}),(55,dict(fill=True)),(55,dict(fill=0)),(55,dict(observe=1)),(55,dict(clobber=1)),(55,dict(variant='other')),(55,dict(observe=False,variant='skip_close'))):
   with patch.object(x,'Uc') as cpu,self.assertRaises(ValueError):x.Reader(None,None,None,narc,**kwargs)
   cpu.assert_not_called()
 def test_optimized_python_refused(self):
  x=self.x
  with patch.object(x.sys,'flags',types.SimpleNamespace(optimize=1)),patch.object(x,'Uc') as cpu,self.assertRaises(ValueError):x.Reader(None,None,None,55)
  cpu.assert_not_called()
 def test_arm_fs_boundary_refuses_thumb_or_halfword_before_model(self):
  x=self.x
  for n,cpsr in ((2,0x1F),(4,0x3F)):
   d=x.Reader.__new__(x.Reader);d.steps=0;d.max_stack=0;d.regs=lambda:[0]*13+[x.TOP-136,0x200734B,cpsr];d.service=Mock()
   with self.assertRaisesRegex(ValueError,'ARM instruction'):d.step(None,0x20D7F98,n,None)
   d.service.assert_not_called()
 def test_native_reads_cannot_borrow_destination_or_external_heap(self):
  x=self.x;d=x.Reader.__new__(x.Reader)
  for a in (x.DEST,0x2370040,x.TOP-196):
   with self.assertRaisesRegex(ValueError,'outside stack'):d.read(None,0,a,4,0,None)
  d.read(None,0,x.TOP-136,4,0,None)
 def test_cli_existing_alias_source_outputs_and_partial_history_refused(self):
  x=self.x
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);rom=root/'own.nds';rom.write_bytes(b'own unchanged');alias=root/'alias';alias.symlink_to(rom);hard=root/'hard';os.link(rom,hard)
   for out,extra in ((rom,[]),(alias,[]),(hard,[]),(SOURCE/'new-reader.json',[]),(root/'fresh.json',['--retail',str(rom)])):
    argv=['reader','--rom',str(rom),'--language','EN','--json',str(out)]+extra
    with patch.object(sys,'argv',argv),patch.object(x,'analyze') as analyze,self.assertRaises(SystemExit) as e:x.main()
    self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   self.assertEqual(rom.read_bytes(),b'own unchanged')
 def test_narc_falsifier_unknown_variant_rejected(self):
  x=self.x
  with patch.object(x,'require_case'),self.assertRaisesRegex(ValueError,'finite domain'):x.require_counter(dict(variant='other'),{},None,None)

@unittest.skipUnless(os.environ.get('SGP_NARC_READER_ROM_DIR') and os.environ.get('SGP_NARC_READER_REPORT_DIR'),'requires private exact ROMs and native reader reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.x=x=tool();cls.reports={};cls.data={};cls.code={}
  for lang in os.environ.get('SGP_NARC_READER_LANGUAGES','EN,IT').split(','):
   rom=Path(os.environ['SGP_NARC_READER_ROM_DIR'])/('r4-'+lang+'.nds');model=x.P.G.S.SHARED.read_current(rom,lang)
   with rom.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:code,proof=x.qualify(model,raw);data=x.resources(raw)
   with gzip.open(Path(os.environ['SGP_NARC_READER_REPORT_DIR'])/('narc-reader-'+lang+'.json.gz'),'rb') as f:payload=f.read(4*1024**2+1)
   assert len(payload)<=4*1024**2;report=json.loads(payload);assert report['schema']=='native-narc-reader-v1' and report['input']==json.loads(json.dumps(model['record'])) and report['proof']==proof and report['source_sha256']==x.source_identities() and report['resources']=={k:v['oracle'] for k,v in data.items()};cls.reports[lang]=report;cls.data[lang]=data;cls.code[lang]=code
 def base(self):return copy.deepcopy(next(iter(self.reports.values()))['cases'][0])
 def require(self,r,lang=None):
  lang=lang or next(iter(self.reports));self.x.require_case(r,self.data[lang],self.code[lang])
 def test_complete_matrix_and_volatile_abi_controls(self):
  for lang,r in self.reports.items():
   self.assertEqual((len(r['cases']),len(r['volatile_controls']),len(r['observer_off']),len(r['counters'])),(4,2,2,2));self.assertEqual([(p['narc'],p['fill']) for p in r['cases']],[(n,f) for n in (55,56) for f in (0xC7,0x39)])
   for p in r['cases']+r['volatile_controls']:self.require(p,lang)
 def test_all_native_and_model_ledgers_required(self):
  for key in ('models','native_writes','observed_pcs'):
   r=self.base();r[key]=r[key][:-1]
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_header_and_payload_cursor_offsets_are_guest_bound(self):
  for key in ('position','destination','requested_bytes','delivered_bytes','delivered_sha256','cursor_after'):
   r=self.base();event=r['models'][3];event[key]='0'*64 if key=='delivered_sha256' else event[key]+1
   with self.subTest(key=key),self.assertRaises(ValueError):self.require(r)
 def test_actual_api_helper_and_arm_sdk_abi_cannot_be_forged(self):
  for change in ('endT','helperSP','modelLR','modelSP','saved','volatile'):
   r=self.base()
   if change=='endT':r['end'][15]&=~32
   elif change=='helperSP':r['helper_return'][13]-=8
   elif change=='modelLR':r['models'][0]['lr']='0x200734a'
   elif change=='modelSP':r['models'][0]['return_sp']-=8
   elif change=='saved':r['models'][0]['saved'][0]^=1
   else:r['models'][0]['return_volatile'][0]^=1
   with self.subTest(change=change),self.assertRaises(ValueError):self.require(r)
 def test_full_stack_frame_and_every_native_store_value_are_required(self):
  for change in ('stack','value','address','width'):
   r=self.base()
   if change=='stack':r['stack_frame_hex']='00'*136
   elif change=='value':r['native_writes'][0]['value']^=1
   elif change=='address':r['native_writes'][0]['address']-=4
   else:r['native_writes'][0]['bytes']=2
   with self.subTest(change=change),self.assertRaises(ValueError):self.require(r)
 def test_file_lifetime_and_payload_are_independent(self):
  for change in ('open','cursor','payload','path','canary'):
   r=self.base()
   if change=='open':r['open']=True
   elif change=='cursor':r['cursor']-=1
   elif change=='payload':r['destination_hex']='a5'*20
   elif change=='path':r['path']='a/0/5/6'
   else:r['canaries']=False
   with self.subTest(change=change),self.assertRaises(ValueError):self.require(r)
 def test_off_and_executed_causal_counters(self):
  for lang,r in self.reports.items():
   for off in r['observer_off']:
    on=next(p for p in r['cases'] if p['narc']==off['result']['narc'] and p['fill']==off['result']['fill']);self.assertEqual(self.x.require_off_pair(on,off['result']),off['proof'])
   normal=next(p for p in r['cases'] if p['narc']==56 and p['fill']==0xC7)
   for counter in r['counters']:self.x.require_counter(counter,normal,self.data[lang],self.code[lang])
 def test_counter_return_isa_helper_context_and_full_trace_are_required(self):
  lang=next(iter(self.reports));report=self.reports[lang];normal=next(p for p in report['cases'] if p['narc']==56 and p['fill']==0xC7)
  for change in ('endT','helperSP','cpu','model','stores','payload'):
   counter=copy.deepcopy(report['counters'][0]);r=counter['result']
   if change=='endT':r['end'][15]&=~32
   elif change=='helperSP':r['helper_return'][13]-=8
   elif change=='cpu':r['cpu_model']=18
   elif change=='model':r['models']=r['models'][-1:]
   elif change=='stores':r['native_writes']=[]
   else:r['destination_hex']='a5'*108
   with self.subTest(change=change),self.assertRaises(ValueError):self.x.require_counter(counter,normal,self.data[lang],self.code[lang])
 def test_off_does_not_hide_frozen_state_or_models(self):
  lang=next(iter(self.reports));r=self.reports[lang];on=r['cases'][0];off=copy.deepcopy(r['observer_off'][0]['result']);off['models'][0]['return_sp']-=8
  with self.assertRaises(ValueError):self.x.require_off_pair(on,off)
if __name__=='__main__':unittest.main()
