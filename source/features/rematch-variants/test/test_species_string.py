"""SDK name-string ABI: size excludes EOS and native copy must not consume spare data."""
from pathlib import Path
import importlib.util,mmap,os,struct,sys,unittest
SOURCE=Path(__file__).resolve().parents[3]


def bench_module():
 spec=importlib.util.spec_from_file_location('rematch_name_bench',Path(__file__).with_name('constructor_bench.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class SpeciesStringABI(unittest.TestCase):
 def test_logical_length_excludes_eos_and_matches_native_allocation_shape(self):
  b=bench_module()
  for length in (0,6,10):
   words=list(range(0x121,0x121+length))+[0xFFFF];blob=b.pack_species_string(words)
   self.assertEqual(struct.unpack_from('<HHI',blob),(length+1,length,0xB6F8D2EC));self.assertEqual(len(blob),10+2*len(words));self.assertEqual(blob[8:8+2*len(words)],struct.pack('<%dH'%len(words),*words))
 def test_incomplete_or_ambiguous_name_fixture_is_refused(self):
  b=bench_module()
  for words in ([],[1],[0xFFFF,0xFFFF],[1]*11+[0xFFFF],[True,0xFFFF],[65536,0xFFFF]):
   with self.subTest(words=words),self.assertRaises(ValueError):b.pack_species_string(words)


@unittest.skipUnless(os.environ.get('SGP_R4_ROM_DIR'),'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class NativeSpeciesStringCopy(unittest.TestCase):
 def test_native_copy_reads_only_logical_characters_and_eos_for_both_languages(self):
  spec=importlib.util.spec_from_file_location('name_string_attribution',SOURCE/'features/rematch-variants/tools/attribuisci.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
  from unicorn import UC_HOOK_MEM_READ
  for language in ('EN','IT'):
   path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language);model=p.G.S.SHARED.read_current(path,language)
   with path.open('rb') as h,mmap.mmap(h.fileno(),0,access=mmap.ACCESS_READ) as raw:
    bench=p.Adapter(model,raw,language)
    for length in (0,6,10):
     words=list(range(0x121,0x121+length))+[0xFFFF];blob=bytearray(p.B.pack_species_string(words));blob[-2:]=b'\xEF\xBE'
     src,dest=0x23B8000,0x23B9000;tail=b'\x77\x77'*(11-len(words));reads=[]
     def factory(*args):
      u=p.Uc(*args)
      def read(uc,access,a,n,v,unused):
       if src+8+2*len(words)<=a<src+len(blob)+8:reads.append((a,n))
      u.hook_add(UC_HOOK_MEM_READ,read);return u
     with p.patch.object(p.B,'Uc',factory):u=bench.call_function(0x2026A68,(src,dest,11),writes=((src,blob+b'\xA5'*8),(dest,b'\x77'*22)))
     self.assertEqual(bytes(u.mem_read(dest,22)),struct.pack('<%dH'%len(words),*words)+tail);self.assertEqual(reads,[])
     if length==6:
      bad=bytearray(blob);struct.pack_into('<H',bad,2,len(words));u=bench.call_function(0x2026A68,(src,dest,11),writes=((src,bad+b'\xA5'*8),(dest,b'\x77'*22)))
      self.assertEqual(bytes(u.mem_read(dest+14,2)),b'\xEF\xBE','old EOS-inclusive size copies the non-name spare word')


if __name__=='__main__':unittest.main()
