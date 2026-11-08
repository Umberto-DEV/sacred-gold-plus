import unittest,tempfile
from font_bench import *
class FontTests(unittest.TestCase):
    def test_lazy_fonts_ignore_unused_cache_words_and_restore_the_owned_word(self):
        # Native lazy initialization sets mode/decoder but leaves cache untouched.
        # Reused font managers can retain glyph bytes or an old allocation word.
        for residue in (0x06060505, 0x43484152, FJ, None):
            with self.subTest(stale=residue):
                b=FontBench(self.compiled)
                stale=b.root()+12288 if residue is None else residue
                for slot in (1,3,4):
                    other=FM+0x800+slot*0x100
                    b.u.mem_write(other,bytes(b.u.mem_read(FM,124)))
                    b.put(other+16,stale);b.put(WORK+0x9c+slot*4,other)
                b.put(FM+16,stale)
                self.assertEqual(b.acquire(),F_READY)
                self.assertEqual(b.begin(),F_ACTIVE)
                self.assertEqual(b.step(),F_DONE)
                self.assertEqual(b.release(),F_DONE)
                self.assertEqual((b.get(FM),b.get(FM+4),b.get(FM+16)),
                                 (1,0x02026111,stale))
                self.assertEqual(b.call('ui_res_release',READER),1)

    def test_other_direct_font_cache_still_protects_outputs(self):
        b=FontBench(self.compiled);other=FM+0x800
        b.u.mem_write(other,bytes(b.u.mem_read(FM,124)))
        b.put(other,0);b.put(other+4,0x02026069)
        b.put(other+16,FJ);b.put(WORK+0xa0,other)
        self.assertEqual(b.acquire(),F_READY)
        self.assertEqual(b.begin(),F_REFUSE)

    def test_grouped_parts_reject_all_output_aliases_and_recheck_late_topology(self):
        b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
        self.assertEqual(b.begin(),F_ACTIVE);self.assertEqual(b.cancel(),F_CANCEL)
        request=bytes(b.u.mem_read(REQ,40));window=bytes(b.u.mem_read(WIN,16))
        pixels=b.pixels();calls=len(b.font_calls)
        self.assertEqual(b.call('fparts',FL,FJ,REQ),1)
        for job in (FL,READER,TOKEN,b.root()-32,b.handles,b.get(b.handles+12)):
            self.assertEqual(b.call('fparts',FL,job,REQ),0,hex(job))
        for field in (4,28):
            for pointer in (FL,READER,TOKEN,b.root()-32,b.get(b.handles+12)):
                b.u.mem_write(REQ,request);b.put(REQ+field,pointer)
                self.assertEqual(b.call('fparts',FL,FJ,REQ),0,(field,hex(pointer)))
        b.u.mem_write(REQ,request);b.put(WIN+12,b.root()-32)
        self.assertEqual(b.call('fparts',FL,FJ,REQ),0)
        b.u.mem_write(WIN,window)
        self.assertEqual(b.call('fparts',FL,FJ,REQ),1)
        b.put(b.idxs+9,3,1);self.assertEqual(b.call('fparts',FL,FJ,REQ),0)
        b.put(b.idxs+9,28,1);self.assertEqual(b.call('fparts',FL,FJ,REQ),1)
        self.assertEqual(b.pixels(),pixels);self.assertEqual(len(b.font_calls),calls)

    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='font-a-');cls.addClassCleanup(cls.tmp.cleanup)
        cls.compiled=compile_font(Path(cls.tmp.name))
    def test_output_guard_checks_topology_once_and_rejects_late_duplicate_slot(self):
        b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
        scans=[]
        def count(u,p,n,d):
            if p==b.symbols['hmeta']&~1:scans.append(p)
        b.u.hook_add(UC_HOOK_CODE,count)
        before=b.pixels()
        self.assertEqual(b.call('foutput',FL,WIN,16),1)
        self.assertEqual(len(scans),1,'one complete topology census per output guard')
        b.put(b.idxs+160,3,1)
        self.assertEqual(b.call('foutput',FL,WIN,16),0)
        self.assertEqual(b.pixels(),before)
    def test_tracked_buffer_one_job_multiple_batches_and_lifecycle(self):
        # A missing BUFFER route refuses a real allocated immutable text root.
        b=FontBench(self.compiled);pool=b.allocate_pool()
        self.assertEqual(b.acquire(),F_READY)
        b.buffer_request(pool,(299,)*25+(65535,))
        self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_ACTIVE,'tracked buffer must publish one job')
        calls=len(b.calls);fs=len(b.fs_calls);before=b.globals()
        self.assertEqual([b.step() for _ in range(4)],[F_ACTIVE,F_ACTIVE,F_ACTIVE,F_DONE])
        self.assertEqual((b.get(FJ+60),b.get(FJ+12,2)),(26,150))
        self.assertEqual(b.globals(),before);self.assertEqual(len(b.fs_calls),fs)
        self.assertFalse(any(p in (ALLOC,FREE) for p,args in b.calls[calls:]))
        self.assertEqual(b.release(),F_DONE)
        self.assertEqual(b.call('ui_free38',TOKEN,pool),1)
        self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_buffer_allocation_headers_bounds_aliases_and_immutable_owner(self):
        # Removing the ledger/header/whole-allocation barriers admits these roots.
        b=FontBench(self.compiled);pool=b.allocate_pool();self.assertEqual(b.acquire(),F_READY)
        b.buffer_request(pool,(299,)*9+(65535,))
        baseline=bytes(b.u.mem_read(0x02000000,0x400000));token=b.token()
        def reset():
            b.u.mem_write(0x02000000,baseline);b.u.mem_write(TOKEN,token)
        faults=((TO+4,pool+4,4),(TO+4,SGG,4),(TO+4,b.root(),4),
          (TO+8,0,4),(TO+8,2,4),(TO+8,258,4),(TO+8,4100,4),(TO+8,260,4),
          (TO+12,0,4),(TO+16,0,4),(REQ+20,129,4),(REQ+16,1,4),(REQ+16,256,4),
          (pool-32,0,2),(pool-28,16,4),(pool-16,1,4),(pool-12,1,4),
          (pool-8,1,4),(pool-4,39,4),(TOKEN+36,pool,4),(TOKEN+32,0,4),
          (REQ+28,pool-32,4),(REQ+4,pool-32,4),(WIN+12,pool-32,4))
        for addr,val,n in faults:
            with self.subTest(address=hex(addr),value=val):
                reset();b.put(addr,val,n);before=b.pixels();calls=len(b.font_calls)
                self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_REFUSE)
                self.assertEqual(b.pixels(),before);self.assertEqual(len(b.font_calls),calls)
        # An understated extent cannot hide a lease/job/scratch/owner/Window/BG
        # in the actual allocation's tail (text itself still occupies four bytes).
        for source,size in ((FL,88),(FJ,152),(SC,652),(TO,20),(WIN,16),(BG,360)):
            reset();b.put(TO+8,4);b.put(REQ+20,2);b.put(pool+2,65535,2)
            target=pool+64;b.u.mem_write(target,bytes(b.u.mem_read(source,size)))
            lease,job=FL,FJ
            if source==FL:lease=target
            elif source==FJ:job=target
            elif source==SC:b.put(REQ+28,target)
            elif source==TO:b.put(REQ+12,target)
            elif source==WIN:b.put(REQ,target)
            else:b.put(WIN,target)
            self.assertEqual(b.call('ui_font_begin',lease,job,REQ),F_REFUSE,hex(source))
        # Put each output/owner inside the real pool, including its native prefix.
        for ptr in (pool-32,pool-16,pool,pool+64):
            reset();self.assertEqual(b.call('ui_font_begin',FL,ptr,REQ),F_REFUSE)
        for addr,val,n in ((TO+12,2,4),(TO+16,0,4),(pool-4,37,4),(TOKEN+32,0,4)):
            reset();self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_ACTIVE)
            self.assertEqual(b.step(),F_ACTIVE);b.put(addr,val,n)
            before=b.pixels();calls=len(b.font_calls)
            self.assertEqual(b.step(),F_INVALID);self.assertEqual(b.pixels(),before)
            self.assertEqual(len(b.font_calls),calls);self.assertEqual(b.get(FL+84),0)
        reset();self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_ACTIVE)
        self.assertEqual(b.call('ui_free38',TOKEN,pool),1)
        self.assertEqual(b.step(),F_INVALID)
        reset();self.assertEqual(b.call('ui_free38',TOKEN,pool),1)
        self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_REFUSE)
    def test_buffer_extents_final_eos_lines_and_retired_reformat(self):
        b=FontBench(self.compiled);pool=b.allocate_pool(4096);self.assertEqual(b.acquire(),F_READY)
        for words,offset,size,cap in (((65535,),4094,4096,1),((509,)*127+(65535,),0,4096,1),
                                     ((0xe000,)*10+(65535,),0,4096,11)):
            b.buffer_request(pool,words,size=size,offset=offset,cap=cap)
            self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_ACTIVE)
            self.assertEqual(b.cancel(),F_CANCEL)
        for words,cap in (((299,),1),((299,65535,299),1),((0xe000,65535),1),((0,65535),1),
                          ((510,65535),1),((65535,),0),((65535,),12)):
            b.buffer_request(pool,words,size=4096,cap=cap)
            self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_REFUSE)
        b.buffer_request(pool,(299,65535),size=4);self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_ACTIVE)
        self.assertEqual(b.step(),F_DONE)
        b.buffer_request(pool,(333,65535),size=4);b.put(TO+12,2)
        self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_ACTIVE);self.assertEqual(b.step(),F_DONE)
    def test_lazy_acquire_owns_one_real_reader_lease_and_native_ref(self):
        b=FontBench(self.compiled)
        self.assertEqual(b.acquire(),F_READY)
        self.assertEqual(b.get(READER+676),1)
        self.assertEqual(b.get(READER+680),1)
        self.assertEqual(b.get(WORK+0xb4,1),2)
        self.assertEqual((b.get(FM),b.get(FM+4),b.get(FM+16)),(0,0x02026069,b.root()+12288))
    def test_masked_entry_defers_without_changing_fresh_or_live_owners(self):
        b=FontBench(self.compiled)
        for mask,ime in ((128,1),(0,0)):
            b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
            before=bytes(b.u.mem_read(FL,128)),b.get(READER+676),b.globals()
            self.assertEqual(b.acquire(),F_DEFER)
            self.assertEqual((bytes(b.u.mem_read(FL,128)),b.get(READER+676),b.globals()),before)
        b.u.reg_write(UC_ARM_REG_CPSR,0x5f);b.put(IME,1)
        self.assertEqual(b.acquire(),F_READY);self.assertEqual(b.begin(),F_ACTIVE)
        for mask,ime in ((128,1),(0,0)):
            b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
            before=bytes(b.u.mem_read(FL,128)),bytes(b.u.mem_read(FJ,160)),b.pixels(),b.globals()
            self.assertEqual(b.step(),F_DEFER)
            self.assertEqual((bytes(b.u.mem_read(FL,128)),bytes(b.u.mem_read(FJ,160)),b.pixels(),b.globals()),before)
    def test_preflight_two_roots_width_zero_and_exact_edges_then_cancel(self):
        b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
        for kw in ({'kind':1},{'words':(509,65535),'x':240,'y':160},
                   {'words':(299,65535),'x':234,'y':160},
                   {'words':(0xe000,)*10+(65535,)}):
            self.assertEqual(b.begin(**kw),F_ACTIVE);self.assertEqual(b.cancel(),F_CANCEL)
        for kw in ({'words':(0,65535)},{'words':(299,65535),'x':235},
                   {'y':161},{'words':(65535,299,65535)},{'words':(299,)},
                   {'words':(0xe000,)*11+(65535,)},{'cap':0}, {'colors':(16,0,0)}):
            before=b.pixels();self.assertEqual(b.begin(**kw),F_REFUSE);self.assertEqual(b.pixels(),before)
        self.assertEqual(b.release(),F_DONE);self.assertEqual(b.get(WORK+0xb4,1),1)
        self.assertEqual((b.get(FM),b.get(FM+4),b.get(FM+16)),(1,0x02026111,0))
        self.assertEqual(b.get(READER+676),0);self.assertEqual(b.release(),F_REFUSE)
    def test_tuple_loss_holds_real_resource_and_does_not_touch_replacement(self):
        for addr,val,width in ((WORKPTR,0,4),(WORK+0x9c,FM+4,4),(FM+16,SGG,4),(WORK+0xb4,1,1),(FW,0,1)):
            b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
            self.assertEqual(b.begin(),F_ACTIVE);b.put(addr,val,width)
            before=b.pixels(),b.get(READER+676),b.get(WORK+0xb4,1)
            self.assertEqual(b.step(),F_HOLD);self.assertEqual(b.cancel(),F_CANCEL)
            self.assertEqual(b.release(),F_HOLD)
            self.assertEqual((b.pixels(),b.get(READER+676),b.get(WORK+0xb4,1)),before)
    def test_mutated_printer_cursor_or_speed_state_invalidates_before_paint(self):
        b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
        for offset,value,size in ((12,1,2),(10,1,1),(32,16,1),(41,128,1),(40,1,1),(24,1,2),(48,SGG,4)):
            self.assertEqual(b.begin(),F_ACTIVE);b.put(FJ+offset,value,size)
            calls=len(b.font_calls)
            self.assertEqual(b.step(),F_INVALID, 'mutated native printer must invalidate')
            self.assertEqual(len(b.font_calls),calls)
    def test_bounded_zero_width_progress_done_and_anomaly_restoration(self):
        b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
        for anomaly in (None,'update','noadvance','speed'):
            self.assertEqual(b.begin(words=(509,)*9+(65535,)),F_ACTIVE)
            b.anomaly=anomaly;before=b.globals()
            self.assertEqual(b.step(),F_INVALID if anomaly else F_ACTIVE)
            self.assertEqual(b.globals(),before)
            if not anomaly:
                self.assertEqual(b.get(FJ+60),8)
                self.assertEqual(b.step(),F_DONE)
                self.assertEqual(b.get(FJ+60),10)
                calls=len(b.font_calls);self.assertEqual(b.step(),F_DONE);self.assertEqual(len(b.font_calls),calls)
    def test_known_allocation_prefixes_and_native_objects_cannot_host_outputs(self):
        b=FontBench(self.compiled);before_acquire=bytes(b.u.mem_read(0x02000000,0x400000))
        for ptr in (b.root()-36,b.root()-32,b.root()-20,b.root()-16,b.root()-8,b.root()-4,FM-32,FW-32,FN-32,READER,TOKEN):
            self.assertEqual(b.call('ui_font_acquire',ptr,READER,0),F_REFUSE)
            self.assertEqual(bytes(b.u.mem_read(0x02000000,0x400000)),before_acquire)
        self.assertEqual(b.acquire(),F_READY);baseline=bytes(b.u.mem_read(0x02000000,0x400000))
        for ptr in (b.root()-36,b.root()-32,b.root()-20,b.root()-16,b.root()-8,b.root()-4,FM-32,FW-32,FN-32,SGG-32,PIX-32,FRONT-32,TO,SC,FL,BG):
            b.u.mem_write(0x02000000,baseline);b.request()
            before=bytes(b.u.mem_read(0x02000000,0x400000))
            self.assertEqual(b.call('ui_font_begin',FL,ptr,REQ),F_REFUSE,hex(ptr))
            self.assertEqual(bytes(b.u.mem_read(0x02000000,0x400000)),before)
        for off,ptr in ((28,b.root()-32),(28,SGG-32),(28,FJ),(0,FW-32),(12,b.root()-32),(4,PIX)):
            b.u.mem_write(0x02000000,baseline);b.request();b.put(REQ+off,ptr)
            before=bytes(b.u.mem_read(0x02000000,0x400000))
            self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_REFUSE)
            self.assertEqual(bytes(b.u.mem_read(0x02000000,0x400000)),before)
    def test_native_admission_fields_and_resource_generation_refuse_without_publication(self):
        b=FontBench(self.compiled);baseline=bytes(b.u.mem_read(0x02000000,0x400000))
        faults=((FM,2,4),(FM+4,0x02026069,4),(FM+8,2,4),(FM+12,32,4),(FM+0x54,0,4),(FM+0x58,1,4),
          (FM+0x5c,20,4),(FM+0x60,0,4),(FM+0x64,510,4),(FM+0x68,0,4),(FM+0x6c,1,4),
          (FM+0x70,0x020262c1,4),(FM+0x74,0,4),(FW,17,1),(WORK+0xb4,127,1),
          (WORK+0xb4,0,1),(WORK+0xb4,255,1),(READER+616,7,4),(READER+676,65535,4))
        for addr,val,n in faults:
            b.u.mem_write(0x02000000,baseline);b.put(addr,val,n)
            before=bytes(b.u.mem_read(0x02000000,0x400000))
            self.assertEqual(b.acquire(),F_REFUSE,(hex(addr),val))
            self.assertEqual(bytes(b.u.mem_read(0x02000000,0x400000)),before)
    def test_text_owner_window_span_spacing_and_lifetime_mutations(self):
        b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
        baseline=bytes(b.u.mem_read(0x02000000,0x400000))
        faults=((REQ+36,16,1),(REQ+38,1,1),(REQ+39,1,1),(REQ+20,0,4),(REQ+20,2049,4),
          (REQ+16,119999,4),(REQ+24,2,4),(TO,3,4),(TO+8,0x20004,4),(TO+12,0,4),(TO+16,0,4),
          (WIN+10,0x8000,2),(WIN+7,0,1),(WIN+12,SGG,4),(REQ+8,21119,4),(BG+8+22,1,1))
        for addr,val,n in faults:
            b.u.mem_write(0x02000000,baseline);b.request();b.put(addr,val,n)
            before=b.pixels();self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_REFUSE,(hex(addr),val))
            self.assertEqual(b.pixels(),before)
        for addr,val,n in ((TO+12,2,4),(TO+16,0,4),(WIN+12,FRONT,4),(FJ+124,b.root()-32,4)):
            b.u.mem_write(0x02000000,baseline);self.assertEqual(b.begin(),F_ACTIVE);b.put(addr,val,n)
            before=b.pixels();calls=len(b.font_calls);self.assertEqual(b.step(),F_INVALID)
            self.assertEqual(b.pixels(),before);self.assertEqual(len(b.font_calls),calls)
    def test_root_extent_change_at_publication_drops_only_unpublished_token(self):
        b=FontBench(self.compiled)
        b.publication_injection=lambda:b.put(READER+548+7*4,b.get(READER+548+7*4)+4)
        self.assertEqual(b.acquire(),F_REFUSE,'changed root extent must refuse publication')
        self.assertEqual(b.get(READER+676),0);self.assertEqual(b.get(WORK+0xb4,1),1)
        self.assertEqual((b.get(FM),b.get(FM+4),b.get(FM+16)),(1,0x02026111,0))
    def test_failed_acquire_drop_holds_unpublished_token_without_native_ownership(self):
        # Ignoring either post-acquisition drop hides a live token as REFUSE.
        for fault in ('publication_generation', 'glyph_generation'):
            with self.subTest(fault=fault):
                b=FontBench(self.compiled);b.request()
                before=bytes(b.u.mem_read(FM,124)),b.get(WORK+0xb4,1),b.pixels(),b.globals()
                if fault=='publication_generation':
                    b.publication_injection=lambda:b.put(READER+620,2)
                else:
                    # Fault after the real acquire has copied generation1, at
                    # its font-ref increment; real glyph/drop validation follows.
                    def stale_generation(u,access,p,n,v,data):
                        if p==READER+680:b.put(READER+620,2)
                    b.u.hook_add(UC_HOOK_MEM_WRITE,stale_generation)
                self.assertEqual(b.acquire(),F_HOLD,'unretired acquisition token must HOLD')
                self.assertEqual((b.get(FL),b.get(FL+4),b.get(FL+28),b.get(FL+84)),(F_HOLD,0,0,0))
                self.assertEqual((b.get(FL+8),b.get(FL+12),b.get(FL+16)),(READER,1,1))
                self.assertEqual((b.get(READER+620),b.get(READER+676),b.get(READER+680)),(2,1,1))
                held=bytes(b.u.mem_read(FL,88)),bytes(b.u.mem_read(FJ,152))
                for _ in range(2):
                    self.assertEqual(b.call('ui_font_check',FL),F_HOLD)
                    self.assertEqual(b.release(),F_HOLD)
                    self.assertEqual(b.call('ui_font_begin',FL,FJ,REQ),F_HOLD)
                    self.assertEqual(b.step(),F_HOLD)
                    self.assertEqual(b.acquire(),F_REFUSE)
                    self.assertEqual(b.cancel(),F_REFUSE)
                    self.assertEqual((bytes(b.u.mem_read(FL,88)),bytes(b.u.mem_read(FJ,152))),held)
                    self.assertEqual((b.get(READER+620),b.get(READER+676),b.get(READER+680)),(2,1,1))
                    self.assertEqual((bytes(b.u.mem_read(FM,124)),b.get(WORK+0xb4,1),b.pixels(),b.globals()),before)
                    self.assertEqual(b.font_calls,[])
    def test_other_native_font_allocation_cannot_host_job(self):
        b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
        other=FM+0x800;b.u.mem_write(other,bytes(b.u.mem_read(FM,124)))
        b.put(other,1);b.put(other+4,0x02026111)
        b.put(other+16,0x43484152);b.put(WORK+0xa0,other)
        self.assertEqual(b.call('fnative',FM,FJ,152),1)
        b.put(other+0x74,FJ)
        self.assertEqual(b.begin(),F_REFUSE,'other font widths are protected outputs')
    def test_real_reader_crc_failure_cannot_publish_font_reference(self):
        raw,config=synthetic();bad=bytearray(raw);bad[35380+12300]^=1
        b=FontBench(self.compiled,bytes(bad),config,ERROR)
        before=b.pixels(),b.globals(),bytes(b.u.mem_read(FM,124)),b.get(WORK+0xb4,1)
        self.assertEqual(b.acquire(),F_REFUSE);self.assertEqual(b.get(READER+676),0)
        self.assertEqual((b.pixels(),b.globals(),bytes(b.u.mem_read(FM,124)),b.get(WORK+0xb4,1)),before)
        self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_current_ref_count_duplicate_operations_and_job_release_barrier(self):
        b=FontBench(self.compiled);b.put(WORK+0xb4,126,1)
        self.assertEqual(b.acquire(),F_READY);self.assertEqual(b.get(WORK+0xb4,1),127)
        self.assertEqual(b.acquire(),F_REFUSE);self.assertEqual(b.get(WORK+0xb4,1),127)
        self.assertEqual(b.begin(),F_ACTIVE);self.assertEqual(b.release(),F_REFUSE)
        self.assertEqual(b.cancel(),F_CANCEL);self.assertEqual(b.cancel(),F_REFUSE)
        self.assertEqual(b.release(),F_DONE);self.assertEqual(b.get(WORK+0xb4,1),126)
        self.assertEqual(b.release(),F_REFUSE);self.assertEqual(b.get(WORK+0xb4,1),126)
    def test_all_forbidden_controls_request_copy_and_bounded_budget(self):
        b=FontBench(self.compiled);self.assertEqual(b.acquire(),F_READY)
        for word in (0,510,0xe001,0xf100,0xf0fd,0xfffe,0x25bc,0x25bd):
            before=b.pixels();self.assertEqual(b.begin(words=(word,65535)),F_REFUSE)
            self.assertEqual(b.pixels(),before)
        self.assertEqual(b.begin(words=(509,)*9+(65535,)),F_ACTIVE)
        b.u.mem_write(REQ,bytes([255])*40)
        for budget in (0,9,0xffffffff):
            before=bytes(b.u.mem_read(FJ,152));self.assertEqual(b.step(budget),F_REFUSE)
            self.assertEqual(bytes(b.u.mem_read(FJ,152)),before)
        self.assertEqual(b.step(),F_ACTIVE);self.assertEqual(b.step(),F_DONE)
        self.assertEqual(b.release(),F_DONE)
    def test_full_2048_unit_uir1_preflight_and_bounded_step(self):
        raw,config=synthetic(authored={1:(509,)*2047+(65535,)})
        b=FontBench(self.compiled,raw,config);self.assertEqual(b.acquire(),F_READY)
        self.assertEqual(b.begin(kind=1),F_ACTIVE);self.assertEqual(b.get(FJ+56),2048)
        self.assertEqual(b.step(),F_ACTIVE);self.assertEqual(b.get(FJ+60),8)
        self.assertEqual(b.cancel(),F_CANCEL);self.assertEqual(b.release(),F_DONE)
if __name__=='__main__':unittest.main()
