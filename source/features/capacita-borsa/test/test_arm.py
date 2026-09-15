import os
from pathlib import Path
import unittest

@unittest.skipUnless(os.environ.get('SGP_CAPACITY_ROM') and os.environ.get('SGP_CAPACITY_BUILD'),'requires private patched ROM and compiled Bag build')
class ArmTests(unittest.TestCase):
    def setUp(self):
        from banco import Bench
        self.b=Bench(os.environ['SGP_CAPACITY_ROM'],os.environ['SGP_CAPACITY_BUILD'])
    def test_original_add_take_quantity_reach_slot252(self):
        b=self.b;bag=b.bag()
        for i in range(1,253):self.assertEqual(b.call(0x02078398,bag,i,2,4),1,i)
        self.assertEqual(b.call(0x02078398,bag,253,1,4),0)
        self.assertEqual(b.slot(bag,0,251),(252,2))
        self.assertEqual(b.call(0x02078550,bag,252,4),2)
        self.assertEqual(b.call(0x02078434,bag,1,2,4),1)
        self.assertEqual(b.slot(bag,0,250),(252,2))
        self.assertEqual(b.slot(bag,0,251),(0,0))
    def test_real_private_copy_retains_overflow_and_registered_items(self):
        b=self.b;bag=b.bag()
        for i in range(1,253):b.call(0x02078398,bag,i,2,4)
        b.call('sgp_cap_register',bag,500)
        private=b.call('sgp_cap_new',4)
        b.call('sgp_cap_copy',bag,private)
        self.assertEqual(b.slot(private,0,251),(252,2))
        self.assertEqual(b.call('sgp_cap_registered1',private),500)
        b.call(0x02078434,private,252,1,4)
        b.call('sgp_cap_copy',private,bag)
        self.assertEqual(b.slot(bag,0,251),(252,1))
    def test_flash_read_failure_before_save_never_uses_cached_valid_record(self):
        from banco import SAVE
        b=self.b;b.bag();manager=0x02234000
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        writes=len(b.writes);original=b.original_saves;b.read_fail=True
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),3)
        self.assertEqual(len(b.writes),writes)
        self.assertEqual(b.original_saves,original)
    def test_foreign_primary_or_mirror_is_never_overwritten(self):
        from banco import SAVE
        for offset in (0,0x200):
            with self.subTest(offset=offset):
                b=self.b;b.bag();manager=0x02234000
                # Establish ownership of some extension; it must not authorize other bytes.
                self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
                b.flash[0x70000+offset:0x70000+offset+452]=b'FOREIGN!'+b'\x11'*444
                before=bytes(b.flash);writes=len(b.writes);native=b.original_saves
                self.assertEqual(b.call('sgp_cap_save',SAVE,manager),3)
                self.assertEqual(bytes(b.flash),before)
                self.assertEqual(len(b.writes),writes)
                self.assertEqual(b.original_saves,native)
                self.setUp()
    def test_retry_after_torn_inactive_record(self):
        from banco import SAVE
        b=self.b;b.bag();manager=0x02234000
        b.write_cut=19
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),3)
        b.write_cut=None
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(b.original_saves,1)
    def test_each_torn_first_record_can_restart_and_retry(self):
        from banco import SAVE,S
        b=self.b;manager=0x02234000
        for cut in range(452):
            b.flash[:]=b'\xff'*len(b.flash);b.store(S,0);b.bag()
            b.write_cut=cut
            self.assertEqual(b.call('sgp_cap_save',SAVE,manager),3,cut)
            b.store(S,0) # restart from the old committed bank
            b.write_cut=None;b.bag()
            self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2,cut)
    def test_active_mirror_recovers_erased_or_corrupt_primary(self):
        from banco import SAVE,S
        import struct
        b=self.b;bag=b.bag();manager=0x02234000
        b.mu.mem_write(bag+251*4,struct.pack('<HH',252,3))
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        committed=bytes(b.flash)
        b.mu.mem_write(SAVE+0x2330A,b'\1\0')
        crc=struct.unpack_from('<H',committed,0x70000+12)[0]
        b.mu.mem_write(SAVE+0x10000+14,struct.pack('<H',crc))
        for erased in (False,True):
            b.flash[:]=committed
            if erased:b.flash[0x70000:0x70000+452]=b'\xff'*452
            else:b.flash[0x70000+20]^=1
            b.store(S,0);bag=b.bag()
            self.assertEqual(b.slot(bag,0,251),(252,3))
    def test_second_copy_readback_failure_does_not_start_native_save(self):
        from banco import SAVE
        b=self.b;b.bag();manager=0x02234000;b.fail_on_read=b.reads+4
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),3)
        self.assertEqual(b.original_saves,0)
        self.assertEqual(len(b.writes),2)
        b.fail_on_read=0
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
if __name__=='__main__':unittest.main()
