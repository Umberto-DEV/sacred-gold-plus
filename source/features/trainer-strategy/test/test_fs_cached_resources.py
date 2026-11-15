"""ROM-free falsifiers for cached filesystem resource validation."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import struct
import tempfile
import unittest

PATH = Path(__file__).parents[1] / 'tools/rileggi_fs_cached_resources.py'


def fixture():
    header = bytearray(512)
    header[12:16] = b'TEST'
    for offset, value in ((0x20,512),(0x28,0x02000000),(0x2c,4096),
                          (0x40,5000),(0x44,32),(0x48,5040),(0x4c,16),
                          (0x50,5080),(0x54,32),(0x58,5112),(0x5c,0)):
        struct.pack_into('<I',header,offset,value)
    arc = bytearray(92)
    arc[:4] = b'rom\0'
    values = {28:7,40:0,44:0x02300000,48:16,52:0x02300010,56:32,
              60:5040,64:5000,68:0x022fffe1,72:0x02000004,
              76:0x02000008,80:0x020D7484,84:0x0200000c,88:0x602}
    for offset,value in values.items():struct.pack_into('<I',arc,offset,value)
    fat = struct.pack('<IIII',5200,5204,5204,5208)
    fnt = struct.pack('<IHH',8,1,1) + bytes(24)
    return bytes(header),bytes(arc),fat,fnt


class ResourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('cached_resource_reader',PATH)
        cls.R = importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.R)

    def test_root_parent_is_count_and_overlay_first_file(self):
        h,a,f,n=fixture();r=self.R.inspect_tables(h,a,f,n,6000)
        self.assertEqual(r['root'],{'start':8,'first_file':1,'directory_count':1})
        self.assertEqual(r['load_alignment'],0x02300000)
        bad=bytearray(n);struct.pack_into('<H',bad,6,0)
        with self.assertRaisesRegex(ValueError,'root directory count'):
            self.R.inspect_tables(h,a,f,bytes(bad),6000)
        bad=bytearray(n);struct.pack_into('<H',bad,4,0)
        with self.assertRaisesRegex(ValueError,'overlay'):
            self.R.inspect_tables(h,a,f,bytes(bad),6000)

    def test_arc_cache_link_and_absolute_callback(self):
        h,a,f,n=fixture()
        for offset,value,label in ((52,0x02300014,'contiguous'),(60,5044,'backup'),
                                   (80,0x020D84C4,'callback'),(28,3,'cached')):
            altered=bytearray(a);struct.pack_into('<I',altered,offset,value)
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,label):
                self.R.inspect_tables(h,bytes(altered),f,n,6000)

    def test_fat_bounds_and_fnt_size_are_validated(self):
        h,a,f,n=fixture()
        bad=struct.pack('<IIII',5200,6001,5204,5208)
        with self.assertRaisesRegex(ValueError,'FAT'):
            self.R.inspect_tables(h,a,bad,n,6000)
        with self.assertRaisesRegex(ValueError,'size'):
            self.R.inspect_tables(h,a,f,n[:-1],6000)

    def test_legacy_stack_overlap_rejected_but_adjacent_allowed(self):
        check=self.R.require_disjoint
        check({'fat':(0x23be580,4104),'fnt':(0x23bf588,2902),
               'file':(0x22f0000,72),'stack':(0x23fcf80,128)})
        with self.assertRaisesRegex(ValueError,'overlap'):
            check({'fat':(0x23be580,4104),'legacy_file':(0x23bedd0,72)})
        with self.assertRaisesRegex(ValueError,'range'):
            check({'invalid':(0xffffffff,2)})

    def test_compressed_input_budget_rejects_padding_before_read(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'padded.gz'
            with path.open('wb') as out:out.truncate(8*1024**2+1)
            with self.assertRaisesRegex(ValueError,'compressed input budget'):
                self.R.extract_snapshot(path,{'one':(0,1)},1,'0'*64,base=0)

    def test_streamed_gzip_requires_exact_size_digest_and_ranges(self):
        raw=bytes(range(256))*600
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'input.gz';path.write_bytes(gzip.compress(raw))
            sha=hashlib.sha256(raw).hexdigest()
            parts=self.R.extract_snapshot(path,{'cross':(65530,20)},len(raw),sha,base=0)
            self.assertEqual(parts,{'cross':raw[65530:65550]})
            for n,digest in ((len(raw)-1,sha),(len(raw)+1,sha),(len(raw),'0'*64)):
                with self.subTest(n=n,digest=digest),self.assertRaises(ValueError):
                    self.R.extract_snapshot(path,{'cross':(65530,20)},n,digest,base=0)
            with self.assertRaisesRegex(ValueError,'range'):
                self.R.extract_snapshot(path,{'outside':(len(raw),1)},len(raw),sha,base=0)


if __name__=='__main__':unittest.main()
