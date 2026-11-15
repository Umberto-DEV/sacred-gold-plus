"""Packed-name fixture boundaries and exact-input receipt counterproofs."""
from pathlib import Path
import copy,importlib.util,json,mmap,os,sys,tempfile,unittest
from unittest.mock import patch
SOURCE=Path(__file__).resolve().parents[3]
def tool():
 s=importlib.util.spec_from_file_location('trainer_name',SOURCE/'features/trainer-strategy/tools/attribuisci_nome.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

class Portable(unittest.TestCase):
 def test_words_reject_wrong_width_early_eos_and_absent_terminator(self):
  m=tool()
  for words in ([],[65535],[1,2],[1,65535,65535],[True,65535],[65536,65535],[-1,65535],[1]*11+[65535]):
   with self.subTest(words=words),self.assertRaises(ValueError):m.words_bytes(words)
  self.assertEqual(m.words_bytes([0xF100,0x7FFF,65535]),bytes.fromhex('00f1ff7fffff'))
 def test_two_independent_codecs_preserve_packed_vectors_before_expansion(self):
  m=tool();expanded=[0x120+i for i in range(9)]+[65535];packed=m.message_codec.pack_name(expanded);raw=m.message_codec.Bank.from_words([packed]).save()
  self.assertEqual(m.hgss_text.read_bank_raw(raw),[packed]);self.assertEqual(m.message_codec.Bank(raw).words,[packed]);self.assertEqual(m.hgss_text.unpack_name(packed),(expanded,True));self.assertNotEqual(len(packed),len(expanded))
 def test_output_aliases_and_source_are_refused_before_reading_roms(self):
  m=tool()
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);rom=root/'own.nds';rom.write_bytes(b'untouched');sym=root/'link';sym.symlink_to(rom);hard=root/'hard';os.link(rom,hard)
   for out in (rom,sym,hard,SOURCE/'new.json'):
    args=['names','--rom',str(rom),'--retail',str(rom),'--base',str(rom),'--v4',str(rom),'--language','EN','--json',str(out)]
    with patch.object(sys,'argv',args),patch.object(m,'analyze') as analyze,self.assertRaises(SystemExit) as e:m.main()
    self.assertEqual(e.exception.code,2);analyze.assert_not_called()
   self.assertEqual(rom.read_bytes(),b'untouched')

@unittest.skipUnless(os.environ.get('SGP_NAME_ROM_DIR') and os.environ.get('SGP_NAME_REPORT_DIR'),'requires private exact ROMs and name CLI reports')
class Replay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=tool();m=cls.m;cls.reports={};cls.words={};cls.code={}
  for language in ('EN','IT'):
   path=Path(os.environ['SGP_NAME_ROM_DIR'])/('r4-'+language+'.nds');model=m.P.G.S.SHARED.read_current(path,language)
   with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:data=m.resources(raw);code,_=m.qualify(model,raw)
   report=json.loads((Path(os.environ['SGP_NAME_REPORT_DIR'])/('name-'+language+'.json')).read_text());assert report['schema']=='trainer-packed-name-v1' and report['input']==json.loads(json.dumps(model['record'])) and report['history'][-1]['resources']==data
   cls.reports[language]=report;cls.words[language]=data['records'];cls.code[language]=code
 def expected(self,language,c):
  r=c['result'];encoding=c['encoding'];trainer=c['trainer']
  return self.words[language][str(trainer)][encoding] if encoding in ('words','expanded') else self.words[language]['21']['expanded' if encoding.startswith('expanded') else 'words'] if trainer else [0x120+i for i in range(r['words']-1)]+[65535]
 def require(self,language,c):
  r=c['result'];self.m.require_result(r,self.expected(language,c),r['capacity']);self.assertTrue(set(r['observed_pcs'])<=set(self.code[language]))
 def test_all_cases_bind_fresh_raw_and_native_qualified_starts(self):
  for language,report in self.reports.items():
   self.assertEqual(len(report['cases']),8);self.assertEqual(len(report['counters']),5)
   for c in report['cases']:self.require(language,c)
   self.assertTrue(all(c['off_neutral'] for c in report['cases'][:6]))
 def test_packed_and_expanded_italian_are_different_input_contracts(self):
  raw=self.reports['IT']['cases'][0];expanded=self.reports['IT']['cases'][1];self.assertEqual((raw['result']['words'],raw['result']['size'],raw['result']['fit']),(8,7,True));self.assertEqual((expanded['result']['words'],expanded['result']['size'],expanded['result']['fit']),(10,9,False))
  with self.assertRaises(ValueError):self.m.require_result(raw['result'],self.words['IT']['21']['expanded'],8)
 def test_equal_output_cannot_replace_native_copy_writes_and_call_order(self):
  base=self.reports['IT']['cases'][0]
  for field in ('events','writes','apis','observed_pcs'):
   c=copy.deepcopy(base);c['result'][field]=c['result'][field][:-1]
   with self.subTest(field=field),self.assertRaises((ValueError,AssertionError)):self.require('IT',c)
  for field in ('destination_hex','destination_sha256','string_sha256'):
   c=copy.deepcopy(base);c['result'][field]+='00'
   with self.subTest(field=field),self.assertRaises(ValueError):self.require('IT',c)
 def test_void_r0_is_not_a_result_code_and_saved_registers_are_required(self):
  c=copy.deepcopy(self.reports['IT']['cases'][0]);c['result']['apis'][1]['end'][0]=0xBAD00000;self.require('IT',c)
  for i in range(4,12):
   c=copy.deepcopy(self.reports['IT']['cases'][0]);c['result']['apis'][1]['end'][i]^=1
   with self.assertRaises(ValueError):self.require('IT',c)
 def test_missing_assert_and_sign_extended_store_values_are_detected(self):
  c=copy.deepcopy(self.reports['IT']['cases'][1]);c['result']['assertions']=0
  with self.assertRaises(ValueError):self.require('IT',c)
  c=copy.deepcopy(self.reports['IT']['cases'][0]);next(w for w in c['result']['writes'] if w['value']>65535)['value']&=255
  with self.assertRaises(ValueError):self.require('IT',c)

if __name__=='__main__':unittest.main()
