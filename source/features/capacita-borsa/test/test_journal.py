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
        # A damaged record never reaches the Bag. A flip inside the magic makes
        # the sector unrecognisable, so it reads as ABSENT (0); anywhere else the
        # record is still ours and reads as INVALID (-1). Neither is fatal.
        _,r=self.record();target=Bag();target.slots[251]=Slot(7,9);before=bytes(target)
        raw=bytes(r)
        for i in range(len(raw)):
            changed=bytearray(raw);changed[i]^=1;bad=Record.from_buffer_copy(changed)
            self.assertEqual(self.lib.cap_record_restore(C.byref(bad),C.byref(target),7,0x1234),0 if i<4 else -1,i)
            self.assertEqual(self.lib.cap_record_owned_prefix(C.byref(bad)),0 if i<4 else 1,i)
            self.assertEqual(bytes(target),before)

    def test_zeroed_or_foreign_sectors_read_as_absent_never_invalid(self):
        """F1: sectors that are not ours degrade to ABSENT, never to a fatal -1."""
        for fill in (b'\xff',b'\x00',b'\xaa',b'\x5a'):
            with self.subTest(fill=fill):
                r=Record.from_buffer_copy(fill*452);b=Bag();b.slots[251]=Slot(7,9);before=bytes(b)
                self.assertEqual(self.lib.cap_record_owned_prefix(C.byref(r)),0)
                self.assertEqual(self.lib.cap_record_erased(C.byref(r)),1 if fill==b'\xff' else 0)
                self.assertEqual(self.lib.cap_record_restore(C.byref(r),C.byref(b),7,0x1234),0)
                self.assertEqual(bytes(b),before)

    def test_our_magic_with_broken_checksum_is_invalid_but_not_foreign(self):
        _,r=self.record()
        raw=bytearray(bytes(r));raw[20]^=1
        bad=Record.from_buffer_copy(bytes(raw));b=Bag();before=bytes(b)
        self.assertEqual(self.lib.cap_record_owned_prefix(C.byref(bad)),1)
        self.assertEqual(self.lib.cap_record_erased(C.byref(bad)),0)
        self.assertEqual(self.lib.cap_record_restore(C.byref(bad),C.byref(b),7,0x1234),-1)
        self.assertEqual(bytes(b),before)

    def test_create_sanitises_zero_quantity_and_out_of_range_slots(self):
        """F2: {id,0} and id>536 in the extension must not poison the record."""
        b=Bag();p0=self.lib.cap_pocket(C.byref(b),0)
        p0[165]=Slot(30,7)    # valid, first extension cell
        p0[249]=Slot(10,5)    # valid
        p0[250]=Slot(20,0)    # quantity 0: what native PocketCompaction leaves behind
        p0[251]=Slot(600,1)   # id beyond ITEM_MAX
        p3=self.lib.cap_pocket(C.byref(b),3)
        p3[101]=Slot(4,200)   # quantity beyond the TM/HM limit of 99
        r=Record();self.lib.cap_record_create(C.byref(r),C.byref(b),7,0x1234)
        self.assertEqual(self.lib.cap_record_restore(C.byref(r),None,7,0x1234),1)
        extras=[(r.extra[i].id,r.extra[i].quantity) for i in range(87)]
        self.assertEqual(extras[0],(30,7))      # pocket 0 extension starts at 165
        self.assertEqual(extras[84],(10,5))     # slot 249: it does NOT move
        self.assertTrue(all(s==(0,0) for i,s in enumerate(extras) if i not in (0,84)))
        self.assertEqual((r.extra[95].id,r.extra[95].quantity),(0,0))  # TM/HM cell
        target=Bag()
        self.assertEqual(self.lib.cap_record_restore(C.byref(r),C.byref(target),7,0x1234),1)
        t=self.lib.cap_pocket(C.byref(target),0)
        self.assertEqual([(t[i].id,t[i].quantity) for i in (165,249,250,251)],
                         [(30,7),(10,5),(0,0),(0,0)])
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
