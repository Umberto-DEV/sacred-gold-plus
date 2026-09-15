"""Power cuts select inventory from the same committed vanilla generation."""
import ctypes as C
from pathlib import Path
import shutil,subprocess,tempfile,unittest,zlib,struct
from test_core import Bag,Slot,NEW,OLD
ROOT=Path(__file__).resolve().parents[1]
class Record(C.Structure):
    _fields_=[('magic',C.c_uint32),('version',C.c_uint16),('size',C.c_uint16),('generation',C.c_uint32),('main_crc',C.c_uint16),('reserved',C.c_uint16),('extra',Slot*108),('crc',C.c_uint32)]
class JournalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();out=Path(cls.tmp.name)/'journal.so'
        subprocess.run([shutil.which('clang') or 'cc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(ROOT/'sorgenti/core.c'),str(ROOT/'sorgenti/journal.c'),'-o',str(out)],check=True,capture_output=True)
        cls.lib=C.CDLL(str(out));cls.lib.cap_pocket.restype=C.POINTER(Slot)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def record(self,generation=7,crc=0x1234):
        b=Bag()
        for p,n in enumerate(NEW):
            v=self.lib.cap_pocket(C.byref(b),p)
            for i in range(OLD[p],n):v[i]=Slot(i+1,3)
        r=Record();self.lib.cap_record_create(C.byref(r),C.byref(b),generation,crc)
        return b,r
    def test_roundtrip_all_extra_pockets_and_crc_independently(self):
        source,r=self.record();self.assertEqual(C.sizeof(r),452)
        self.assertEqual(r.crc,zlib.crc32(bytes(r)[:-4]));self.assertEqual(r.size,452)
        restored=Bag();self.assertEqual(self.lib.cap_record_restore(C.byref(r),C.byref(restored),7,0x1234),1)
        self.assertEqual(bytes(source),bytes(restored))
    def test_corruption_never_silently_restores_or_clears(self):
        _,r=self.record();target=Bag();target.slots[251]=Slot(7,9);before=bytes(target)
        raw=bytes(r)
        for i in range(len(raw)):
            changed=bytearray(raw);changed[i]^=1;bad=Record.from_buffer_copy(changed)
            self.assertEqual(self.lib.cap_record_restore(C.byref(bad),C.byref(target),7,0x1234),-1,i)
            self.assertEqual(bytes(target),before)
    def test_absent_old_save_and_stale_generation(self):
        r=Record.from_buffer_copy(b'\xff'*452);b=Bag()
        self.assertEqual(self.lib.cap_record_restore(C.byref(r),C.byref(b),1,10),0)
        _,r=self.record();before=bytes(b)
        self.assertEqual(self.lib.cap_record_restore(C.byref(r),C.byref(b),6,0x1234),2)
        self.assertEqual(self.lib.cap_record_restore(C.byref(r),C.byref(b),7,0x5678),2)
        self.assertEqual(bytes(b),before)
    def test_every_torn_write_leaves_previous_committed_bank_recoverable(self):
        oldbag,old=self.record(6,0x1111);newbag,new=self.record(7,0x2222)
        # The extension is verified in the inactive bank BEFORE any vanilla write.
        # A cut before the vanilla commit loads bank A; after it loads bank B.
        for cut in range(453):
            raw=bytes(new)[:cut]+b'\xff'*(452-cut)
            candidate=Record.from_buffer_copy(raw);loaded=Bag()
            verified=self.lib.cap_record_restore(C.byref(candidate),C.byref(loaded),7,0x2222)==1
            selected=candidate if verified else old
            gen,crc=(7,0x2222) if verified else (6,0x1111)
            final=Bag();self.assertEqual(self.lib.cap_record_restore(C.byref(selected),C.byref(final),gen,crc),1)
            self.assertEqual(bytes(final),bytes(newbag if verified else oldbag))
if __name__=='__main__':unittest.main()
