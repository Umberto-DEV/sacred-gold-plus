"""Class B: actual encrypted accessors, recalc, item gates and journal faults.
Requires SGP_TRAINING_ROM and SGP_TRAINING_REPORT; inputs stay private.
Synthetic ARM machine tests are not native gameplay compatibility evidence.
"""
import os,struct,unittest
from native_bench import Bench,MON,SAVE,ARGS
ROM=os.environ.get('SGP_TRAINING_ROM');REPORT=os.environ.get('SGP_TRAINING_REPORT')
@unittest.skipUnless(ROM and REPORT,'private training candidate/report not supplied')
class Native(unittest.TestCase):
 def setUp(self):self.b=Bench(ROM,REPORT)
 def transaction(self,kind=0,iv_kind=1,stat=0,value=31,target=None):
  b=self.b;b.mu.mem_write(ARGS+0x100,struct.pack('<4I',b.symbols['training_read'],0x0206EC41,0x0206E251,0x023EEC01))
  expected=[b.get((13 if kind else 70)+i)for i in range(6)]
  request=struct.pack('<IIH6B6B6B',b.get(0),b.get(7),b.get(5),kind,2,iv_kind,stat,value,0,*expected,*(target or [0]*6))
  b.mu.mem_write(ARGS+0x200,request)
  return b.call(b.symbols['sgp_training_transaction'],ARGS+0x100,SAVE,MON,ARGS+0x200,ARGS+0x300)
 def test_real_encrypted_iv_change_recalc_and_unrelated_fields(self):
  b=self.b;b.make_mon();fields=(0,7,5,8,6,54,55,56,57,13,14,15,16,17,18,161)
  before=[b.get(i)for i in fields];hp=b.get(164)
  self.assertEqual(self.transaction(),0);self.assertEqual(b.get(70),31);self.assertGreater(b.get(164),hp)
  self.assertEqual([b.get(i)for i in fields],before);self.assertEqual(b.get(3),0);self.assertEqual(b.charges,[(0,1)])
 def test_fainted_shedinja_exact_zero_noop_and_payment_failure(self):
  b=self.b;b.make_mon();b.set(163,0);self.assertEqual(self.transaction(),0);self.assertEqual(b.get(163),0)
  self.assertEqual(self.transaction(),3);self.assertEqual(len(b.charges),1)
  before=bytes(b.mu.mem_read(MON,236));b.pay_ok=False
  self.assertEqual(self.transaction(iv_kind=0,value=0),4);self.assertEqual(bytes(b.mu.mem_read(MON,236)),before)
  b.pay_ok=True;self.assertEqual(self.transaction(iv_kind=0,value=0),0);self.assertEqual(b.get(70),0)
  b.make_mon(292);self.assertEqual(self.transaction(),0);self.assertEqual(b.get(164),1)
 def test_corrupt_checksum_and_egg_never_change_original(self):
  b=self.b;b.make_mon();b.set(76,1);before=bytes(b.mu.mem_read(MON,236));self.assertEqual(self.transaction(),2);self.assertEqual(bytes(b.mu.mem_read(MON,236)),before)
  b.make_mon();buf=bytearray(b.mu.mem_read(MON,236));buf[20]^=1;b.mu.mem_write(MON,bytes(buf))
  # Build expected request without invoking a getter on the original corruption.
  b.mu.mem_write(ARGS+0x100,struct.pack('<4I',b.symbols['training_read'],0x0206EC41,0x0206E251,0x023EEC01));b.mu.mem_write(ARGS+0x200,struct.pack('<IIH6B6B6B',12345,87654,25,0,2,1,0,31,0,*([10]*6),*([0]*6)))
  self.assertEqual(b.call(b.symbols['sgp_training_transaction'],ARGS+0x100,SAVE,MON,ARGS+0x200,ARGS+0x300),1);self.assertEqual(bytes(b.mu.mem_read(MON,236)),bytes(buf));self.assertEqual(b.assertions,0)
 def test_unlimited_ev_transaction_money_cost_and_real_stats(self):
  b=self.b;b.make_mon();self.assertEqual(self.transaction(kind=1,target=[252]*6),0);self.assertEqual([b.get(13+i)for i in range(6)],[252]*6);self.assertEqual(b.charges,[(2,151200)])
  self.assertEqual(self.transaction(kind=1,target=[0]*6),0);self.assertEqual(len(b.charges),1)
 def test_scalar_negative_all_policies_and_vitamin_entry_gates(self):
  b=self.b;b.make_mon();state=0x023D3000;b.put(state,0x31544e52);b.put(state+8,1)
  # TrainingState journal starts32, policy at journal+8.
  for policy in range(3):
   b.mu.mem_write(state+40,bytes([policy]))
   self.assertEqual(b.call(0x02090A84,252,1260,(-10)&0xffffffff),242)
   for stat,item in enumerate((45,46,47,48,49,52)):
    for i in range(6):b.set(13+i,0)
    b.set(13+stat,100)
    self.assertEqual(b.call(0x0208FD9C,MON,item,0,4),int(policy!=0))
    b.set(13+stat,252);self.assertEqual(b.call(0x0208FD9C,MON,item,0,4),0)
 def test_bulk_item_loader_includes_both_caps_and_old_last_record(self):
  b=self.b;array=b.call(0x02078138,4)
  for item,index in ((113,514),(114,515),(536,513),(135,113)):
   single=b.call(0x02077CE8,item,0,4);mapped=b.call(0x02077C18,item,0);self.assertEqual(mapped,index)
   pointer=b.call(0x02078160,array,mapped);self.assertEqual(bytes(b.mu.mem_read(pointer,34)),bytes(b.mu.mem_read(single,34)))
  self.assertEqual(b.call(0x02077D88,113,1,4),0);self.assertEqual(b.call(0x02077D88,114,5,4),0)
 def prepare_save(self):
  b=self.b;s=0x023D3000;b.put(s,0x31544e52);b.put(s+4,SAVE);b.put(s+8,1);b.put(s+12,1)
  b.call(b.symbols['sgp_train_defaults'],s+32);b.put(SAVE+0x23010,17);b.put(SAVE+0x232B8,0);b.put(SAVE+0x232BC,0x1000)
  b.put(0x023DD700,0x43415042);b.put(0x023DD700+0x12C4,1);b.mu.mem_write(ARGS,bytes(36));return s
 def test_save_lease_records_and_foreign_sector_veto(self):
  b=self.b;self.prepare_save();b.flash[0x71420]=0x42
  self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),3);self.assertEqual(b.native_saves,0);self.assertEqual(b.writes,[])
  b.flash[0x71420]=255;self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2);self.assertEqual(b.native_saves,1)
  self.assertEqual(bytes(b.flash[0x71000:0x71100]),bytes(b.flash[0x71200:0x71300]));self.assertEqual(b.flash[0x71400:0x71404],b'TNO1')
 def test_torn_journal_retry_is_recoverable_without_native_commit(self):
  b=self.b;self.prepare_save();b.call(b.symbols['training_save'],SAVE,ARGS);b.native_saves=0
  for cut in (0,1,7,8,40,100,255):
   b.put(SAVE+0x23010,18+cut);b.cut=cut;self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),3);self.assertEqual(b.native_saves,0)
   b.cut=None;self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2);b.native_saves=0
 def test_torn_first_lease_retry_and_future_header_protection(self):
  b=self.b;self.prepare_save();b.cut=7;self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),3);self.assertEqual(b.native_saves,0)
  b.cut=None;self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2)
  # v2 is supported; v3 is an unknown future format that must veto overwrite.
  b.flash[0x71004]=3;b.writes.clear();b.native_saves=0;self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),3);self.assertEqual(b.native_saves,0);self.assertEqual(b.writes,[])
 def test_cold_reload_matching_generation_torn_sibling_and_rollback(self):
  b=self.b;s=self.prepare_save();b.mu.mem_write(s+40,b'\2');self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2)
  record=bytes(b.flash[0x71000:0x71100]);crc=struct.unpack_from('<H',record,12)[0]
  b.mu.mem_write(SAVE+0x2330A,b'\1\0');b.mu.mem_write(SAVE+0x100E,struct.pack('<H',crc))
  before=bytes(b.flash);b.writes.clear();self.assertEqual(b.call(b.symbols['training_load'],SAVE),1)
  self.assertEqual((b.u32(s+8),b.u32(s+12)),(1,1));self.assertEqual(bytes(b.flash),before);self.assertEqual(b.writes,[])
  b.flash[0x71020]^=1;b.call(b.symbols['training_load'],SAVE)
  self.assertEqual((b.u32(s+8),b.u32(s+12)),(1,1)) # valid mirror plus durable owned lease
  b.put(SAVE+0x23010,16);b.call(b.symbols['training_load'],SAVE);self.assertEqual(b.u32(s+8),0)
  b.writes.clear();self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2);self.assertEqual(b.writes,[])
 def test_torn_first_payload_header_with_durable_lease_can_retry(self):
  b=self.b;self.prepare_save();self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2)
  for cut in range(4,9):
   with self.subTest(cut=cut):
    b.flash[0x71000:0x71100]=b'\xff'*256;b.flash[0x71200:0x71300]=b'\xff'*256;b.cut=cut;b.native_saves=0
    self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),3);self.assertEqual(b.native_saves,0)
    b.cut=None;self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2)
 def test_inactive_foreign_metadata_allows_ordinary_native_save_without_writes(self):
  b=self.b;s=self.prepare_save();b.flash[0x31000:0x31008]=b'FOREIGN!';b.call(b.symbols['training_load'],SAVE)
  self.assertEqual(b.u32(s+8),0);self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2);self.assertEqual(b.writes,[])
 def test_cold_reload_after_each_initialization_failure_has_no_training_side_effect(self):
  for sector in (0x31000,0x71000):
   for cut in (0,1,7,16,31,40,255):
    with self.subTest(sector=hex(sector),cut=cut):
     self.b=Bench(ROM,REPORT);b=self.b;s=self.prepare_save();b.mu.mem_write(SAVE+0x2330A,struct.pack('<H',sector==0x31000));b.cut=cut
     self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),3);self.assertEqual(b.native_saves,0)
     b.cut=None;b.call(b.symbols['training_load'],SAVE);self.assertEqual(b.u32(s+8),0)
     b.writes.clear();self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2);self.assertEqual(b.writes,[])
     # Explicit activation can repair a demonstrably owned torn first write.
     self.assertEqual(b.service(1,arg=0),0);self.assertEqual(b.call(b.symbols['training_save'],SAVE,ARGS),2)


@unittest.skipUnless(ROM and REPORT,'private training candidate/report not supplied')
class NativeServices(unittest.TestCase):
 def setUp(self):self.b=Bench(ROM,REPORT);self.b.activate()
 def test_activation_checks_both_full_sectors_before_any_paid_edit(self):
  b=self.b;s=0x023D3000;b.put(s+8,0)
  for address in (0x31420,0x71420):
   b.flash[address]=42
   self.assertEqual(b.service(1,arg=0),8);self.assertEqual(b.u32(s+8),0);self.assertEqual(b.writes,[])
   self.assertEqual(b.service(5),7);b.flash[address]=255
  self.assertEqual(b.service(1,arg=0),0);self.assertEqual(b.writes,[])
 def active_admission_case(self):
  # Real native service/Bag/SAVE/load paths keep a valid ACTIVE journal in
  # both leased banks. A new fault must not be hidden by initial activation.
  b=Bench(ROM,REPORT);self.b=b
  # Match Bench's fake allocator/Heap_Free seam: its pointers have no native
  # heap manager/header for Heap_FreeExplicit. Item/Bag code stays native.
  from unicorn import UC_HOOK_CODE
  b.mu.hook_add(UC_HOOK_CODE,lambda *unused:b.ret(),begin=0x0201AB80,end=0x0201AB80)
  b.activate(2);party,dc=self.setup_daycare()
  self.assertEqual(b.service(8,arg=1,value=64),0)
  b.make_mon(1,20);b.mu.mem_write(dc+236,bytes(b.mu.mem_read(MON,136)))
  b.make_mon(92,20);b.set(13,19)
  self.assertEqual(b.call(0x02074524,party,MON),1)
  profile=b.call(0x02028E9C,SAVE)
  self.assertEqual(b.call(0x02029028,profile,207569),207569)
  b.league=1;bag=b.call(0x0207879C,SAVE)
  for item in (113,114):self.assertEqual(b.call(0x02078398,bag,item,999,4),1)
  self.assertEqual(b.service(6),3) # Actual first League reward queues4/2.
  for item in (113,114):self.assertEqual(b.call(0x02078434,bag,item,999,4),1)
  b.put(SAVE+4,1);b.put(SAVE+0x232B8,0);b.put(SAVE+0x232BC,0x10000)
  for generation,target in ((17,1),(18,0)):
   b.put(SAVE+0x23010,generation);b.mu.mem_write(ARGS,bytes(36))
   self.assertEqual(b.call(0x02027C18,SAVE,ARGS),2)
   record=bytes(b.flash[0x31000+target*0x40000:0x31100+target*0x40000])
   b.mu.mem_write(SAVE+0x2330A,struct.pack('<H',target))
   b.mu.mem_write(SAVE+0x1000E,record[12:14])
  self.assertEqual(b.call(b.symbols['training_load'],SAVE),1)
  self.assertEqual((b.u32(0x023D3008),b.u32(0x023D300C)),(1,1))
  self.assertEqual(b.service(0),0)
  self.assertEqual(struct.unpack('<2H',b.mu.mem_read(ARGS+0x1004,4)),(4,2))
  b.put(0x021D1048,1);b.rtc_now=100000;b.writes.clear();b.native_saves=0
  return b,party,dc,profile
 def admission_faults(self):
  bag=(0x30000,0x30200,0x70000,0x70200)
  records=(0x31000,0x31200,0x71000,0x71200);owners=(0x31400,0x71400)
  return [('foreign',a)for a in bag+owners]+[('future',a)for a in records]+[('read',a)for a in bag+records+owners]
 def admission_snapshot(self,b,party,dc,profile):
  return tuple(bytes(b.mu.mem_read(p,n))for p,n in
               ((0x023D3000,0x1000),(party,1460),(dc,480),(profile,32),(0x023DD700,0x1400),(b.u32(0x023DD708),1952)))
 def admission_restore(self,b,party,dc,profile,snapshot,flash,heap):
  # Isolate synthetic fault cases without repeating the two real native SAVEs.
  for pointer,data in zip((0x023D3000,party,dc,profile,0x023DD700,b.u32(0x023DD708)),snapshot):b.mu.mem_write(pointer,data)
  b.flash[:]=flash;b.heap=heap;b.fail_address=None;b.writes.clear();b.native_saves=0
 def test_active_commit_rechecks_every_destination_before_ev_or_cap_payment(self):
  # Removing the fresh commit admission must spend100/change EVs, or consume
  # a real cap/change IVs, despite a later SAVE being unable to commit.
  for preview,args in ((3,dict(arg=0,value=20)),(2,dict(arg=0,value=31,kind=1))):
   b,party,dc,profile=self.active_admission_case()
   if preview==2:
    bag=b.call(0x0207879C,SAVE);self.assertEqual(b.call(0x02078398,bag,113,1,4),1)
   baseline=self.admission_snapshot(b,party,dc,profile);baseflash=bytes(b.flash);heap=b.heap
   for fault,address in self.admission_faults():
    with self.subTest(preview=preview,fault=fault,address=hex(address)):
     self.admission_restore(b,party,dc,profile,baseline,baseflash,heap)
     self.assertEqual(b.service(preview,**args),0)
     if fault=='read':b.fail_address=address
     elif fault=='future':b.flash[address:address+8]=b'TNR1\3\0\0\1'
     else:b.flash[address:address+8]=b'FOREIGN!'
     before=self.admission_snapshot(b,party,dc,profile);flash=bytes(b.flash)
     self.assertEqual(b.service(4),8)
     after=self.admission_snapshot(b,party,dc,profile)
     expected=bytearray(before[0]);expected[24:28]=bytes(4) # consume rejected preview
     self.assertEqual(after,(bytes(expected),*before[1:]))
     self.assertEqual((b.u32(profile+0x14),b.writes,b.native_saves,b.assertions),(207569,[],0,0))
     self.assertEqual(bytes(b.flash),flash)
 def test_active_purchase_rewards_clock_and_enrollment_recheck_admission(self):
  # All four handlers mutate persistent service state; an active policy alone
  # must not authorize caps, delivered claims, changed clocks or a new job.
  operations=((5,dict(arg=1)),(6,{}),(7,dict(arg=1)),(8,dict(slot=1,arg=1,value=64)))
  b,party,dc,profile=self.active_admission_case()
  baseline=self.admission_snapshot(b,party,dc,profile);baseflash=bytes(b.flash);heap=b.heap
  for op,args in operations:
   for fault,address in self.admission_faults():
    with self.subTest(op=op,fault=fault,address=hex(address)):
     self.admission_restore(b,party,dc,profile,baseline,baseflash,heap)
     if fault=='read':b.fail_address=address
     elif fault=='future':b.flash[address:address+8]=b'TNR1\3\0\0\1'
     else:b.flash[address:address+8]=b'FOREIGN!'
     before=self.admission_snapshot(b,party,dc,profile);flash=bytes(b.flash)
     self.assertEqual(b.service(op,**args),8)
     self.assertEqual(self.admission_snapshot(b,party,dc,profile),before)
     self.assertEqual((b.writes,b.native_saves,b.assertions),([],0,0))
     self.assertEqual(bytes(b.flash),flash)
 def test_active_storage_io_retry_needs_new_preview_but_reads_cancel_and_gameplay_work(self):
  b,party,dc,profile=self.active_admission_case();b.fail_address=0x70200
  self.assertEqual(b.service(0),0);self.assertEqual(b.service(11,kind=1),0)
  self.assertEqual(struct.unpack('<H',b.mu.mem_read(ARGS+0x1000,2))[0],19)
  self.assertEqual(b.service(3,arg=0,value=20),0);self.assertEqual(b.service(10),0)
  self.assertEqual(b.service(9),0) # Existing course projection remains readable.
  self.assertEqual(b.call(0x02090A84,19,0,1),20) # Ordinary EV gameplay stays active.
  self.assertEqual(b.service(3,arg=0,value=20),0);self.assertEqual(b.service(4),8)
  self.assertEqual(b.call(0x0206E540,party+8,13,0),19)
  self.assertEqual(b.u32(profile+0x14),207569);self.assertEqual(b.writes,[])
  b.fail_address=None
  self.assertEqual(b.service(4),1) # Rejected confirmation cannot be replayed.
  self.assertEqual(b.call(0x0206E540,party+8,13,0),19)
  self.assertEqual(b.service(3,arg=0,value=20),0);self.assertEqual(b.service(4),0)
  self.assertEqual(b.call(0x0206E540,party+8,13,0),20)
  self.assertEqual(b.u32(profile+0x14),207469)
  self.assertEqual((b.writes,b.native_saves,b.assertions),([],0,0))
 def test_first_activation_anchors_historical_league_before_later_claim(self):
  b=self.b;s=0x023D3000;b.put(s+8,0);b.league=2
  self.assertEqual(b.service(1,arg=0),0);b.league=4
  self.assertEqual(b.service(6),0);bag=b.call(0x0207879C,SAVE)
  self.assertEqual(b.call(0x02078550,bag,113,4),12);self.assertEqual(b.call(0x02078550,bag,114,4),4)
  self.assertEqual(b.service(6),3)
 def test_zero_win_activation_counts_first_and_repeat_before_first_claim(self):
  b=self.b;b.put(0x023D3008,0);b.league=0;self.assertEqual(b.service(1,arg=0),0);b.league=2
  self.assertEqual(b.service(6),0);bag=b.call(0x0207879C,SAVE)
  self.assertEqual(b.call(0x02078550,bag,113,4),8);self.assertEqual(b.call(0x02078550,bag,114,4),3)
 def test_empty_zero_initialized_external_storage_does_not_block_policy(self):
  b=self.b;b.activate(0);party=SAVE+0x5000;b.call(0x020744DC,party,6)
  self.assertEqual(b.service(1,arg=1),0);self.assertEqual(b.assertions,0)
  pc=SAVE+0x1000+41*0x2000;box=b.call(0x02074058,pc,0,0);b.make_mon();bad=bytearray(b.mu.mem_read(MON,136));bad[20]^=1;b.mu.mem_write(box,bytes(bad))
  self.assertEqual(b.service(1,arg=2),7);self.assertEqual(b.assertions,0);self.assertEqual(bytes(b.mu.mem_read(box,136)),bytes(bad))
 def test_census_migration_checks_all_six_occupied_slots_without_rewriting_evs(self):
  # NativeBench's ARRAY seam maps array28 here, with six236-byte records.
  # Skipping any slot or checking the wrong stride must admit an unsafe policy.
  b=self.b;migrated=SAVE+0x1000+28*0x2000
  cases=((0,[253,0,0,0,0,0],7),(0,[252,0,0,0,0,0],0),
         (2,[252,252,7,0,0,0],7),(2,[252,252,6,0,0,0],0))
  for slot in range(6):
   for old_policy,evs,result in cases:
    with self.subTest(slot=slot,evs=evs):
     b.activate(old_policy);b.mu.mem_write(migrated,bytes(6*236));b.make_mon()
     for stat,value in enumerate(evs):b.set(13+stat,value)
     b.mu.mem_write(migrated+236*slot,bytes(b.mu.mem_read(MON,236)))
     owned=bytes(b.mu.mem_read(migrated,6*236));state=bytes(b.mu.mem_read(0x023D3000,0x1000))
     self.assertEqual(b.service(1,arg=1),result)
     self.assertEqual(bytes(b.mu.mem_read(migrated,6*236)),owned)
     if result:self.assertEqual(bytes(b.mu.mem_read(0x023D3000,0x1000)),state)
     self.assertEqual(b.service(0),0)
     self.assertEqual(struct.unpack('<H',b.mu.mem_read(ARGS+0x1000,2))[0],old_policy if result else 1)
     self.assertEqual((b.assertions,b.writes,b.charges),(0,[],[]))
 def test_census_pokewalker_requires_complete_empty_transfer_without_mutation(self):
  b=self.b;walker=SAVE+0x1000+39*0x2000;b.make_mon()
  occupied=bytes(b.mu.mem_read(MON,136));corrupt=bytearray(occupied);corrupt[20]^=1
  # Even a valid0-EV transferred Pokemon cannot establish a complete census.
  for record in (occupied,bytes(corrupt)):
   for target in (0,1,2):
    with self.subTest(corrupt=record!=occupied,target=target):
     b.activate(2);b.mu.mem_write(walker+4,record)
     state=bytes(b.mu.mem_read(0x023D3000,0x1000))
     self.assertEqual(b.service(1,arg=target),7)
     self.assertEqual(bytes(b.mu.mem_read(walker+4,136)),record)
     self.assertEqual(bytes(b.mu.mem_read(0x023D3000,0x1000)),state)
  for encrypted_empty in (False,True):
   b.mu.mem_write(walker+4,bytes(136))
   if encrypted_empty:b.call(0x0206DD0C,walker+4)
   empty=bytes(b.mu.mem_read(walker+4,136));b.activate(2)
   self.assertEqual(b.service(1,arg=1),0)
   self.assertEqual(bytes(b.mu.mem_read(walker+4,136)),empty)
  self.assertEqual((b.assertions,b.writes,b.charges),(0,[],[]))
 def test_census_pending_course_targets_block_tightening_for_either_daycare_slot(self):
  b=self.b
  for slot in (0,1):
   for target,result in ((1,7),(0,0)):
    with self.subTest(slot=slot,target_total=510+target):
     b.activate(2);party,dc=self.setup_daycare();b.make_mon()
     for stat,value in enumerate((252,252,6,0,0,0)):b.set(13+stat,value)
     b.mu.mem_write(dc+236*slot,bytes(b.mu.mem_read(MON,136)))
     # Deposited EVs total510 fit Classic; only its future Sp.Atk target
     # makes511. Use real enrollment rather than hand-written journal bytes.
     self.assertEqual(b.service(8,slot=slot,arg=4,value=target),0)
     owned=bytes(b.mu.mem_read(dc,480));state=bytes(b.mu.mem_read(0x023D3000,0x1000))
     self.assertEqual(b.service(1,arg=1),result)
     self.assertEqual(bytes(b.mu.mem_read(dc,480)),owned)
     if result:self.assertEqual(bytes(b.mu.mem_read(0x023D3000,0x1000)),state)
     self.assertEqual(b.service(0),0)
     self.assertEqual(struct.unpack('<H',b.mu.mem_read(ARGS+0x1000,2))[0],2 if result else 1)
     self.assertEqual((b.assertions,b.writes,b.charges),(0,[],[]))
 def test_actual_bag_cap_border_and_wallet_debit(self):
  b=self.b;bag=b.call(0x0207879C,SAVE);profile=SAVE+0x3004
  b.put(profile+0x14,10000);b.mu.mem_write(profile+0x1A,b'\1')
  self.assertEqual(b.call(0x02078398,bag,113,998,4),1)
  self.assertEqual(b.service(5,arg=0),0);self.assertEqual(b.call(0x02078550,bag,113,4),999);self.assertEqual(b.u32(profile+0x14),0)
  b.put(profile+0x14,10000);self.assertEqual(b.service(5,arg=0),4);self.assertEqual(b.u32(profile+0x14),10000)
  self.assertEqual(b.call(0x02078434,bag,113,999,4),1);self.assertEqual(b.call(0x02078550,bag,113,4),0)
  b.put(profile+0x14,9999);self.assertEqual(b.service(5,arg=0),4);self.assertEqual(b.u32(profile+0x14),9999)
 def test_full_cap_stacks_keep_rewards_pending_across_cold_until_real_bag_add(self):
  # Removing the ADD-success gate, pending acknowledgement, or saved claim bit
  # must fail: this is reward collection, not the separate cap purchase path.
  def pending(b):
   self.assertEqual(b.service(0),0)
   return struct.unpack('<2H',b.mu.mem_read(ARGS+0x1004,4))
  def quantities(b):
   bag=b.call(0x0207879C,SAVE)
   return tuple(b.call(0x02078550,bag,item,4)for item in (113,114))
  def save_cold(b,generation):
   b.put(SAVE+4,1);b.put(SAVE+0x23010,generation)
   b.put(SAVE+0x232B8,0);b.put(SAVE+0x232BC,0x10000)
   target=1-struct.unpack('<H',b.mu.mem_read(SAVE+0x2330A,2))[0]
   b.mu.mem_write(ARGS,bytes(36))
   # Real composed entry: Bag writer -> training coordinator -> native seam.
   self.assertEqual(b.call(0x02027C18,SAVE,ARGS),2)
   self.assertGreater(b.native_saves,0)
   address=0x31000+target*0x40000
   record=bytes(b.flash[address:address+256])
   self.assertEqual(record,bytes(b.flash[address+0x200:address+0x300]))
   self.assertEqual(struct.unpack_from('<I',record,40)[0],1<<16)
   # The final native commit is the existing bench seam. Carry its native
   # arrays/footer plus flash into a fresh ARM machine, never a savestate.
   native=bytes(b.mu.mem_read(SAVE,0x23400))
   cold=Bench(ROM,REPORT);cold.league=1;cold.flash[:]=b.flash
   cold.mu.mem_write(SAVE,native)
   cold.mu.mem_write(SAVE+0x2330A,struct.pack('<H',target))
   cold.mu.mem_write(SAVE+0x1000E,record[12:14])
   self.assertEqual(cold.call(cold.symbols['training_load'],SAVE),1)
   self.assertEqual(cold.assertions,0)
   return cold
  b=self.b;b.league=0;bag=b.call(0x0207879C,SAVE)
  for item in (113,114):self.assertEqual(b.call(0x02078398,bag,item,999,4),1)
  b.league=1  # First League reward is independently specified as 4 silver/2 gold.
  self.assertEqual(b.service(6),3)
  self.assertEqual((quantities(b),pending(b)),((999,999),(4,2)))
  b=save_cold(b,17)
  self.assertEqual((quantities(b),pending(b)),((999,999),(4,2)))
  self.assertEqual(b.service(6),3)
  self.assertEqual(pending(b),(4,2))
  bag=b.call(0x0207879C,SAVE)
  for item in (113,114):self.assertEqual(b.call(0x02078434,bag,item,1,4),1)
  self.assertEqual(b.service(6),0)
  self.assertEqual((quantities(b),pending(b)),((999,999),(3,1)))
  b=save_cold(b,18)
  self.assertEqual((quantities(b),pending(b)),((999,999),(3,1)))
  bag=b.call(0x0207879C,SAVE)
  for item,count in ((113,3),(114,1)):self.assertEqual(b.call(0x02078434,bag,item,count,4),1)
  self.assertEqual(b.service(6),0)
  self.assertEqual((quantities(b),pending(b)),((999,999),(0,0)))
  b=save_cold(b,19)
  self.assertEqual((quantities(b),pending(b)),((999,999),(0,0)))
  bag=b.call(0x0207879C,SAVE)
  for item in (113,114):self.assertEqual(b.call(0x02078434,bag,item,1,4),1)
  self.assertEqual(b.service(6),3)
  self.assertEqual((quantities(b),pending(b)),((998,998),(0,0)))
 def setup_daycare(self):
  b=self.b;b.make_mon();b.set(54,85);party=SAVE+0x5000;dc=SAVE+0xF000
  b.call(0x020744DC,party,6);b.mu.mem_write(dc,bytes(480));b.mu.mem_write(dc,bytes(b.mu.mem_read(MON,136)));b.put(dc+232,100)
  b.call(0x0206DD0C,dc+236);return party,dc
 def test_timed_daycare_native_withdraw_preserves_moves_and_steps_until_withdraw(self):
  b=self.b;party,dc=self.setup_daycare();original=bytes(b.mu.mem_read(dc,480));exp=b.get(8)
  self.assertEqual(b.service(8,slot=0,arg=1,value=64),0);self.assertEqual(bytes(b.mu.mem_read(dc,480)),original)
  b.put(0x023D3000+32+16,7200) # journal.played offset16
  self.assertEqual(b.call(0x0206C0E8,dc),1)
  self.assertEqual(b.call(0x0206C078,party,0,dc,0),25);self.assertEqual(b.u32(party+4),1)
  result=party+8
  self.assertEqual(b.call(0x0206E540,result,161,0),51);self.assertEqual(b.call(0x0206E540,result,14,0),64)
  self.assertEqual(b.call(0x0206E540,result,54,0),85)
  self.assertGreater(b.call(0x0206E540,result,8,0),exp+100)
  self.assertEqual(b.service(9,slot=0),1)
 def test_corrupt_box_enrollment_and_identity_never_assert_or_mutate(self):
  b=self.b;party,dc=self.setup_daycare();bad=bytearray(b.mu.mem_read(dc,136));bad[20]^=1;b.mu.mem_write(dc,bytes(bad))
  self.assertEqual(b.service(8,arg=255),1);self.assertEqual(b.assertions,0);self.assertEqual(bytes(b.mu.mem_read(dc,136)),bytes(bad))
  self.setup_daycare();self.assertEqual(b.service(8,arg=255),0);b.mu.mem_write(dc,bytes(bad))
  self.assertEqual(b.call(0x0206C078,party,0,dc,0),0);self.assertEqual(b.assertions,0);self.assertEqual(bytes(b.mu.mem_read(dc,136)),bytes(bad))
 def test_full_party_retrieval_never_removes_job_or_box(self):
  b=self.b;party,dc=self.setup_daycare();self.assertEqual(b.service(8,arg=255),0)
  before=bytes(b.mu.mem_read(dc,480));b.put(party+4,6)
  self.assertEqual(b.call(0x0206C078,party,0,dc,0),0);self.assertEqual(bytes(b.mu.mem_read(dc,480)),before);self.assertEqual(b.service(9),0)
 def test_two_slot_compaction_and_identity_rejection(self):
  b=self.b;party,dc=self.setup_daycare();b.make_mon(1,20);b.mu.mem_write(dc+236,bytes(b.mu.mem_read(MON,136)))
  self.assertEqual(b.service(8,slot=1,arg=255),0)
  self.assertEqual(b.call(0x0206C078,party,0,dc,0),25);self.assertEqual(b.service(9,slot=0),0);self.assertEqual(b.service(9,slot=1),1)
  b.put(ARGS,4);b.call(0x0206ED70,dc,5,ARGS);before=bytes(b.mu.mem_read(dc,480))
  self.assertEqual(b.call(0x0206C078,party,0,dc,0),0);self.assertEqual(bytes(b.mu.mem_read(dc,480)),before)
 def test_rtc_failure_and_clock_switch_do_not_credit_epoch(self):
  b=self.b;self.setup_daycare();self.assertEqual(b.service(8,arg=255),0)
  b.put(0x023D3000+48,7199);self.assertEqual(b.service(7,arg=1),7)
  self.assertEqual(b.service(9),0);self.assertEqual(struct.unpack('<H',b.mu.mem_read(ARGS+0x1000,2))[0],50)

 def test_battle_ev_yields_power_items_pokerus_and_policy_caps(self):
  b=self.b;party=SAVE+0x5000
  def gain(item,virus,evs,policy=2):
   b.activate(policy);b.make_mon();b.set(6,item);b.set(154,virus)
   for i,v in enumerate(evs):b.set(13+i,v)
   b.call(0x020744DC,party,6);self.assertEqual(b.call(0x02074524,party,MON),1)
   b.call(b.symbols['training_battle'],party,0,19,0) # Rattata gives1 Speed EV.
   return [b.call(0x0206E540,party+8,13+i,0) for i in range(6)]
  self.assertEqual(gain(0,0,[0]*6),[0,0,0,1,0,0])
  self.assertEqual(gain(215,0,[0]*6),[0,0,0,2,0,0])
  self.assertEqual(gain(215,0x11,[0]*6),[0,0,0,4,0,0])
  for item,stat in ((294,0),(289,1),(290,2),(293,3),(291,4),(292,5)):
   want=[0,0,0,2,0,0];want[stat]+=8
   self.assertEqual(gain(item,0x11,[0]*6),want)
  self.assertEqual(gain(0,0,[252]*6),[252]*6)
  self.assertEqual(gain(0,0,[252,252,6,0,0,0],1),[252,252,6,0,0,0])
  self.assertEqual(gain(0,0,[0,0,0,254,0,0],0),[0,0,0,255,0,0])

 def test_rtc_to_play_switch_keeps_fraction_and_phone_reports_ev_and_six_digit_time(self):
  b=self.b;party,dc=self.setup_daycare();b.put(0x021D1048,1);b.rtc_now=100000
  self.assertEqual(b.service(7,arg=1),0);self.assertEqual(b.service(8,arg=1,value=64),0)
  b.rtc_now+=3599;self.assertEqual(b.service(7,arg=0),0);b.put(0x023D3030,1)
  self.assertEqual(b.service(9),0);self.assertEqual(struct.unpack('<H',b.mu.mem_read(ARGS+0x1004,2))[0],32)
  ctx=ARGS+0x3000;b.put(ctx+0x50,ARGS+0x3500);b.phone_buffers=[]
  b.call(b.symbols['training_phone'],ctx,ARGS+0x3600,5)
  integers={entry[2]:(entry[3],entry[4])for entry in b.phone_buffers if entry[0]==0x0200BFCC}
  self.assertEqual(integers[0],(50,3));self.assertEqual(integers[2],(32,3));self.assertEqual(integers[3],(64,3))
  self.assertEqual(integers[4],(356400,6));self.assertEqual(b.phone_messages[-1][2],b.u32(0x023D2F08)+2)
  self.assertTrue(any(x[0]==0x0200C1D4 and x[2:4]==(1,1)for x in b.phone_buffers))
if __name__=='__main__':unittest.main()
