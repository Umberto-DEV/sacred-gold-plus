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
        from banco import SAVE,S_STATO_SCRITTURA
        b=self.b;b.bag();manager=0x02234000
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        writes=len(b.writes);original=b.original_saves;b.read_fail=True
        # No cached record is written, and the vanilla save still runs: the
        # extension reports the failure, it does not veto the save.
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(len(b.writes),writes)
        self.assertEqual(b.original_saves,original+1)
        self.assertEqual(b.read32(S_STATO_SCRITTURA),4)
    def test_foreign_primary_or_mirror_is_never_overwritten(self):
        from banco import SAVE,S_STATO_SCRITTURA
        for offset in (0,0x200):
            with self.subTest(offset=offset):
                self.setUp();b=self.b;b.bag();manager=0x02234000
                # Establish ownership of some extension; it must not authorize other bytes.
                self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
                b.flash[0x70000+offset:0x70000+offset+452]=b'FOREIGN!'+b'\x11'*444
                before=bytes(b.flash);writes=len(b.writes);native=b.original_saves
                self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
                self.assertEqual(bytes(b.flash),before)
                self.assertEqual(len(b.writes),writes)
                self.assertEqual(b.original_saves,native+1)
                self.assertEqual(b.read32(S_STATO_SCRITTURA),2)
    def test_retry_after_torn_inactive_record(self):
        from banco import SAVE,S_STATO_SCRITTURA
        b=self.b;b.bag();manager=0x02234000
        b.write_cut=19
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(b.read32(S_STATO_SCRITTURA),3)
        b.write_cut=None
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(b.read32(S_STATO_SCRITTURA),1)
        self.assertEqual(b.original_saves,2)
    def test_each_torn_first_record_can_restart_and_retry(self):
        from banco import SAVE,S,S_STATO_SCRITTURA
        b=self.b;manager=0x02234000
        for cut in range(452):
            b.flash[:]=b'\xff'*len(b.flash);b.store(S,0);b.bag()
            b.write_cut=cut
            self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2,cut)
            self.assertEqual(b.read32(S_STATO_SCRITTURA),3,cut)
            b.store(S,0) # restart from the old committed bank
            b.write_cut=None;b.bag()
            self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2,cut)
            self.assertEqual(b.read32(S_STATO_SCRITTURA),1,cut)
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
    def test_second_copy_readback_failure_leaves_one_good_copy(self):
        from banco import SAVE,S_STATO_SCRITTURA,OWNERSHIP_READS,READBACK_READS
        # One ownership read per destination, then ceil(452/64) chunked readback
        # reads per copy: fail the first readback chunk of the mirror.
        b=self.b;b.bag();manager=0x02234000
        b.fail_on_read=b.reads+OWNERSHIP_READS+READBACK_READS+1
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(b.original_saves,1)
        self.assertEqual(len(b.writes),2)
        self.assertEqual(b.read32(S_STATO_SCRITTURA),5)
        b.fail_on_read=0
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(b.read32(S_STATO_SCRITTURA),1)
    # ---- F1 / F3: the extension must never stop the native save from loading ----
    def _committed(self):
        """Save once, then make that bank the one the next load reads."""
        import struct
        from banco import SAVE,S
        b=self.b;bag=b.bag();manager=0x02234000
        b.mu.mem_write(bag+250*4,struct.pack('<HH',251,7))
        b.mu.mem_write(bag+251*4,struct.pack('<HH',252,3))
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        committed=bytes(b.flash)
        b.mu.mem_write(SAVE+0x2330A,b'\1\0')
        crc=struct.unpack_from('<H',committed,0x70000+12)[0]
        b.mu.mem_write(SAVE+0x10000+14,struct.pack('<H',crc))
        return committed[0x70000:0x70000+452]

    @staticmethod
    def _variants(valid):
        import struct,zlib
        invalid=bytearray(valid);invalid[20]^=1            # our magic, broken CRC32
        stale=bytearray(valid);struct.pack_into('<I',stale,8,99)
        struct.pack_into('<I',stale,448,zlib.crc32(bytes(stale[:448])))
        return {'valida':bytes(valid),'vuota':b'\xff'*452,
                'estranea':b'\x00'*452,'invalida':bytes(invalid),'stale':bytes(stale)}

    def test_zero_filled_sram_loads_as_absent_extension_without_error(self):
        """F1: sectors 48/112 full of 0x00 (or 0xAA) must not stop the load."""
        import struct
        from banco import SAVE,S,S_REJECTED,S_MAGIC,S_STATO_CARICAMENTO
        for fill in (0x00,0xAA):
            with self.subTest(fill=fill):
                self.setUp();b=self.b
                b.flash=bytearray([fill])*0x80000
                b.store(S,0)
                bag=b.bag()
                self.assertEqual(b.errors,0)
                self.assertEqual(b.read32(S_MAGIC),0x43415042)
                self.assertEqual(b.read32(S_REJECTED),0)
                # 6 = not ours at all, told apart from 4 = ours but damaged.
                self.assertEqual(b.read32(S_STATO_CARICAMENTO),6)
                # 486 native slots: the extension is simply absent, the Bag works.
                self.assertEqual(b.slot(bag,0,251),(0,0))
                for i in range(1,253):self.assertEqual(b.call(0x02078398,bag,i,2,4),1,i)
                self.assertEqual(b.slot(bag,0,251),(252,2))

    def test_uniform_destination_is_claimed_by_the_next_save(self):
        """A2: a .sav normalised to 0x00 (or wiped to 0xAA) holds no data in
        sectors 48/112. Such a destination is claimable: the extension must be
        written there, otherwise every extra slot is lost at every reload."""
        import struct
        from banco import SAVE,S,S_STATO_SCRITTURA,S_OWNED,RECORD_BYTES
        for fill in (0x00,0xAA):
            with self.subTest(fill=fill):
                self.setUp();b=self.b
                b.flash=bytearray([fill])*0x80000
                b.store(S,0);bag=b.bag();manager=0x02234000
                b.mu.mem_write(bag+251*4,struct.pack('<HH',252,3))
                self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
                self.assertEqual(b.original_saves,1)
                self.assertEqual(b.read32(S_STATO_SCRITTURA),1)
                self.assertEqual(b.read32(S_OWNED),1)
                primary=bytes(b.flash[0x70000:0x70000+RECORD_BYTES])
                self.assertEqual(primary,bytes(b.flash[0x70200:0x70200+RECORD_BYTES]))
                # and the extension comes back on the next load of that bank
                crc=struct.unpack_from('<H',primary,12)[0]
                b.mu.mem_write(SAVE+0x2330A,b'\1\0')
                b.mu.mem_write(SAVE+0x10000+14,struct.pack('<H',crc))
                b.store(S,0);bag=b.bag()
                self.assertEqual(b.slot(bag,0,251),(252,3))

    def test_load_truth_table_primary_by_mirror(self):
        """F3: every primary x mirror combination loads; none is fatal.
        `noflash` is a destination the flash itself refuses to read."""
        from banco import SAVE,S,S_REJECTED,S_OWNED,S_STATO_CARICAMENTO
        kinds=('invalida','vuota','valida','stale','estranea','noflash')
        for first in kinds:
            for second in kinds:
                with self.subTest(primaria=first,specchio=second):
                    self.setUp();b=self.b;v=self._variants(self._committed())
                    for offset,kind in ((0,first),(0x200,second)):
                        if kind!='noflash':b.flash[0x70000+offset:0x70000+offset+452]=v[kind]
                    b.store(S,0)
                    if first=='noflash' and second=='noflash':b.read_fail=True
                    elif first=='noflash':b.fail_on_read=b.reads+1
                    elif second=='noflash':b.fail_on_read=b.reads+2
                    bag=b.bag()
                    if first=='valida':stato,restored=1,True
                    elif second=='valida':stato,restored=2,True
                    elif 'noflash' in (first,second):stato,restored=5,False
                    elif 'stale' in (first,second):stato,restored=3,False
                    elif 'invalida' in (first,second):stato,restored=4,False
                    elif 'estranea' in (first,second):stato,restored=6,False
                    else:stato,restored=0,False
                    rejected=1 if first=='noflash' or (second=='noflash' and first!='valida') else 0
                    self.assertEqual(b.errors,0)
                    self.assertEqual(b.read32(S_STATO_CARICAMENTO),stato)
                    self.assertEqual(b.read32(S_REJECTED),rejected)
                    self.assertEqual(b.read32(S_OWNED),1 if stato in (1,2,3) else 0)
                    self.assertEqual(b.slot(bag,0,251),(252,3) if restored else (0,0))

    def test_unreadable_load_never_vetoes_the_following_save(self):
        """A1: the load reads the ACTIVE bank and the save writes the INACTIVE
        one. A read failure on the first must not forbid writing the second:
        that turned one unreadable sector into a silent loss of every extra
        slot, for the whole session."""
        import struct
        from banco import SAVE,S,S_REJECTED,S_STATO_CARICAMENTO,S_STATO_SCRITTURA,RECORD_BYTES
        b=self.b;manager=0x02234000
        b.store(S,0);b.fail_on_read=b.reads+1          # the active bank is unreadable
        bag=b.bag()
        self.assertEqual(b.read32(S_STATO_CARICAMENTO),5)
        self.assertEqual(b.read32(S_REJECTED),1)
        b.fail_on_read=0
        b.mu.mem_write(bag+251*4,struct.pack('<HH',252,3))
        writes=len(b.writes)
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(b.read32(S_STATO_SCRITTURA),1)
        self.assertEqual([a for a,_ in b.writes[writes:]],[0x70000,0x70200])
        primary=bytes(b.flash[0x70000:0x70000+RECORD_BYTES])
        crc=struct.unpack_from('<H',primary,12)[0]
        b.mu.mem_write(SAVE+0x2330A,b'\1\0')
        b.mu.mem_write(SAVE+0x10000+14,struct.pack('<H',crc))
        b.store(S,0);bag=b.bag()
        self.assertEqual(b.read32(S_STATO_CARICAMENTO),1)
        self.assertEqual(b.slot(bag,0,251),(252,3))

    def test_readback_of_a_different_valid_record_is_refused(self):
        """M4: the readback is a byte comparison of what was just written. A
        destination that hands back a record which is perfectly valid, but not
        the one written, is a failed copy -- not an accepted one."""
        import struct
        from banco import SAVE,S_STATO_SCRITTURA,OWNERSHIP_READS,RECORD_BYTES
        for copies,stato in (((0,),5),((0,1),3)):
            with self.subTest(copie_guaste=copies):
                self.setUp();b=self.b;bag=b.bag();manager=0x02234000
                b.mu.mem_write(bag+251*4,struct.pack('<HH',252,3))
                self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
                self.assertEqual(b.read32(S_STATO_SCRITTURA),1)
                other=bytes(b.flash[0x70000:0x70000+RECORD_BYTES])
                b.mu.mem_write(bag+251*4,struct.pack('<HH',100,1))
                start=b.reads
                def filtro(index,address,size,data,start=start,copies=copies):
                    # Only the readback: the ownership reads come first and are
                    # left alone. verify_copy stops at the first mismatching
                    # chunk, so the substitution is by address, not by count.
                    if index<=start+OWNERSHIP_READS:return data
                    for c in copies:
                        off=address-(0x70000+c*0x200)
                        if 0<=off<RECORD_BYTES:return other[off:off+size]
                    return data
                b.read_filter=filtro
                self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
                self.assertEqual(b.read32(S_STATO_SCRITTURA),stato)
                self.assertEqual(b.original_saves,2)

    # ---- F2: a slot the native compaction leaves behind must not block saving ----
    def test_zero_quantity_or_out_of_range_slot_still_saves(self):
        import struct,zlib
        from banco import SAVE,S,S_STATO_SCRITTURA,S_OWNED,NATIVE
        for item,quantity in ((1,0),(600,1)):
            with self.subTest(slot=(item,quantity)):
                self.setUp();b=self.b;bag=b.bag();manager=0x02234000
                b.mu.mem_write(bag+250*4,struct.pack('<HH',7,5))
                b.mu.mem_write(bag+251*4,struct.pack('<HH',item,quantity))
                native=bytes(b.mu.mem_read(NATIVE,1948))
                self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
                # M2: the sanitised record is the truth. The poisoned cell must
                # be gone from RAM as well, or the pocket still counts as
                # non-empty and the UI can ask the item table about id 600.
                self.assertEqual(b.slot(bag,0,250),(7,5))
                self.assertEqual(b.slot(bag,0,251),(0,0))
                # The 486 native slots are never touched by the sanitation.
                self.assertEqual(bytes(b.mu.mem_read(NATIVE,1948)),native)
                self.assertEqual(b.original_saves,1)
                self.assertEqual(b.read32(S_STATO_SCRITTURA),1)
                self.assertEqual(b.read32(S_OWNED),1)
                primary=bytes(b.flash[0x70000:0x70000+452])
                self.assertEqual(primary,bytes(b.flash[0x70200:0x70200+452]))
                self.assertEqual(struct.unpack_from('<I',primary,448)[0],zlib.crc32(primary[:448]))
                # slot 250 is extension cell 85; the poisoned 251 becomes {0,0}
                self.assertEqual(struct.unpack_from('<4H',primary,16+4*85),(7,5,0,0))
                # The readback is a memcmp of the 452 written bytes, and the
                # sanitised record reloads without the poisoned slot.
                crc=struct.unpack_from('<H',primary,12)[0]
                b.mu.mem_write(SAVE+0x2330A,b'\1\0')
                b.mu.mem_write(SAVE+0x10000+14,struct.pack('<H',crc))
                b.store(S,0);bag=b.bag()
                self.assertEqual(b.slot(bag,0,250),(7,5))
                self.assertEqual(b.slot(bag,0,251),(0,0))

    def test_extension_failure_never_stops_the_native_save(self):
        """F2/F6: foreign sectors, torn writes and read failures all let the
        vanilla save through; only the diagnostic field records the problem."""
        from banco import SAVE,S_STATO_SCRITTURA
        b=self.b;b.bag();manager=0x02234000
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        b.flash[0x70000:0x70000+452]=b'FOREIGN!'+b'\x11'*444
        before=bytes(b.flash);writes=len(b.writes)
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(bytes(b.flash),before)
        self.assertEqual(len(b.writes),writes)
        self.assertEqual(b.original_saves,2)
        self.assertEqual(b.read32(S_STATO_SCRITTURA),2)
        self.setUp()
        b=self.b;b.bag();b.write_cut=19
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(b.original_saves,1)
        self.assertEqual(b.read32(S_STATO_SCRITTURA),3)
        self.setUp()
        b=self.b;b.bag();b.read_fail=True
        self.assertEqual(b.call('sgp_cap_save',SAVE,manager),2)
        self.assertEqual(b.original_saves,1)
        self.assertEqual(b.writes,[])
        self.assertEqual(b.read32(S_STATO_SCRITTURA),4)
if __name__=='__main__':unittest.main()
