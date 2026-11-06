"""Reject-before-store Shiny transactions through actual compiled owner code."""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unicorn.arm_const import UC_ARM_REG_CPSR, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_R0
from ui_transaction_bench import (SOURCE, FLAGS, base, compile_all, Bench, FS, SAVE,
    APP, OPTIONS, STATE, GENERATION, DESCRIPTOR, SHINY, ADMITTED, FLAGS_OFFSET,
    RT, EXT, GATE_CODE, STACK, SNAP, DRAFT, TOKEN, GATE, CONTEXT, IME, PLUS, NATIVE, IRQ_QUERY)


class ShinyUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='shiny-ui-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = Path(cls.temp.name)
        cls.compiled = compile_all(cls.directory)

    def bench(self, leased=True):
        return Bench(self.compiled, leased)

    def ready(self, **draft):
        b = self.bench()
        self.assertEqual(b.peek(), 0)
        b.draft(**draft)
        self.assertEqual(b.prepare(), 0)
        b.reset_trace()
        return b

    def no_store(self, b, before=None):
        if before is not None:
            self.assertEqual(b.owner(), before)
        self.assertEqual(b.owner_writes, [])
        self.assertEqual(b.flash_writes, [])
        self.assertEqual(b.masked_io, [])
        for p,n in b.canaries:
            self.assertEqual(bytes(b.u.mem_read(p,n)), b'\x5A'*n)

    def refusal(self, b, token=TOKEN, gate=GATE):
        before, wire, ime = b.owner(), bytes(b.u.mem_read(token,152)), b.get(IME)
        self.assertNotEqual(b.commit(token, gate), 0)
        self.no_store(b, before)
        self.assertEqual(bytes(b.u.mem_read(token,152)), wire)
        self.assertEqual(b.get(IME), ime)
        self.no_publication(b)

    def no_publication(self,b):
        for address,size,value in b.all_writes:
            self.assertTrue(address==IME or 0x027E0080<=address<address+size<=b.stack,
                            ('refusal wrote outside callee stack/IME',hex(address),size))

    def test_peek_exact_snapshot_no_admission_and_prepare_cancel(self):
        for admitted in (0,1):
            b = self.bench(); b.put(ADMITTED,admitted); before = b.owner()
            control=b.u.reg_read(UC_ARM_REG_CPSR)&0xFF
            self.assertEqual(b.peek(),0)
            self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR)&0xFF,control)
            expected = struct.pack('<IIIHH8B5B3s',3,11,7,25,1024,1,1,20,40,3,0,0,0,1,1,0,0,0,bytes(3))
            self.assertEqual(bytes(b.u.mem_read(SNAP,32)),expected)
            b.draft(mode=0)
            self.assertEqual(b.prepare(),0)
            self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR)&0xFF,control)
            self.assertEqual(bytes(b.u.mem_read(TOKEN+24,32)), expected)
            self.assertEqual(bytes(b.u.mem_read(TOKEN+128,16)),struct.pack('<IHBBB7s',123,25,0,0,1,bytes(7)))
            self.no_store(b,before)
            self.assertEqual(b.get(ADMITTED),admitted)

    def test_mode_only_without_cache_and_changed_target_reset_charge(self):
        for no_cache in (False, True):
            b=self.bench(); b.put(RT+28,not no_cache)
            if no_cache:b.u.mem_write(RT+52,bytes(5))
            self.assertEqual(b.peek(),0); b.draft(mode=0)
            self.assertEqual(b.prepare(),0); b.reset_trace()
            self.assertEqual(b.commit(),0)
            self.assertEqual(bytes(b.u.mem_read(SHINY,16)),struct.pack('<IHBBB7s',123,25,0,0,1,bytes(7)))
            self.assertEqual(bytes(b.u.mem_read(RT+48,4)),bytes(4))
            self.assertEqual(b.get(RT+8),8)
        b=self.ready(target=0)
        self.assertEqual(b.commit(),0)
        self.assertEqual(bytes(b.u.mem_read(SHINY+4,4)),b'\0\0\0\1')
        self.assertEqual(bytes(b.u.mem_read(RT+48,1)),b'\0')

    def test_success_only_declared_stores_revision_replay_and_no_dispatch(self):
        for search in (0,1):
            for enabled in (0,1):
                b=self.ready(method=1,search=search)
                b.put(STATE+8,enabled); b.u.mem_write(FLAGS_OFFSET,struct.pack('<H',0 if enabled else 1))
                # Reprepare proof after changing Training enabled state.
                b.reset_trace(); self.assertEqual(b.prepare(),0); b.reset_trace()
                original=bytes(b.u.mem_read(TOKEN,152)); copy=TOKEN+0x180
                b.u.mem_write(copy,original)
                before=bytearray(b.owner()); saved=bytes(b.u.mem_read(SHINY,16))
                control=b.u.reg_read(UC_ARM_REG_CPSR)&0xFF
                self.assertEqual(b.commit(),0)
                self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR)&0xFF,control)
                self.assertEqual(bytes(b.u.mem_read(SHINY,16)),saved)
                self.assertEqual(b.get(RT+8),8); self.assertEqual(b.get(TOKEN),0)
                self.assertEqual(bytes(b.u.mem_read(RT+48,4)),bytes([40,0,1,search]))
                self.assertEqual(b.get(ADMITTED),1)
                if search:
                    self.assertEqual(b.get(RT+668),11); self.assertEqual(b.get(RT+672),8)
                allowed=set(range(SHINY,SHINY+16))|set(range(ADMITTED,ADMITTED+4))|set(range(RT+8,RT+12))|{RT+49,RT+50}
                if not enabled:allowed |= set(range(FLAGS_OFFSET,FLAGS_OFFSET+2))
                if search:allowed |= {RT+51}|set(range(RT+668,RT+676))
                for a,n,v in b.owner_writes:self.assertTrue(set(range(a,a+n))<=allowed,(hex(a),n))
                after=b.owner()
                # Entire resident/save/gSystem image differs only at allowed bytes.
                for i,(x,y) in enumerate(zip(before,after)):
                    if x!=y:self.assertIn(0x023C0000+i,allowed)
                for a,n,v in b.all_writes:
                    self.assertTrue(a==IME or 0x027E0080<=a<a+n<=b.stack or set(range(a,a+n))<=allowed or (a==TOKEN and n==4),(hex(a),n))
                self.assertEqual(b.ime_writes,[0,1]); self.assertEqual(b.gate_calls,[(len(b.reads),0)])
                self.assertEqual(b.flash_writes,[]); self.assertEqual(b.masked_io,[])
                b.reset_trace(); self.refusal(b)
                b.reset_trace(); self.refusal(b,copy)

    def test_draft_domains_search_rules_and_busy_are_readonly(self):
        cases=[({'mode':2},2),({'target':494},2),({'method':5},2),({'search':2},2),
               ({'target':26},3),({'search':1,'mode':0},4),({'search':1,'target':0},3)]
        for values,want in cases:
            b=self.bench(); self.assertEqual(b.peek(),0); b.draft(**values); before=b.owner()
            self.assertEqual(b.prepare(),want); self.no_store(b,before)
            self.assertEqual(bytes(b.u.mem_read(TOKEN,152)),b'\xA5'*152)
        for address,value,size in [(DRAFT,4,4),(DRAFT+17,1,1),(DRAFT+18,1,1),(DRAFT+19,1,1),
                                   (RT+51,1,1),(RT+680,1,4),(RT+704,1,4)]:
            b=self.bench(); self.assertEqual(b.peek(),0); b.draft()
            b.u.mem_write(address,value.to_bytes(size,'little')); before=b.owner()
            self.assertNotEqual(b.prepare(),0); self.no_store(b,before)
        for charge in (0,39,40):
            b=self.bench(); b.u.mem_write(RT+48,bytes([charge])); self.assertEqual(b.peek(),0)
            b.draft(search=1); self.assertEqual(b.prepare(),0 if charge==40 else 5)
            self.no_store(b)

    def test_invalid_owner_domains_and_cache_counts_fail_without_publish(self):
        for address,value,size in [(RT,0,4),(RT+4,0,4),(RT+48,41,1),(RT+49,8,1),
            (RT+50,5,1),(RT+28,2,4),(APP+0x28,0,4),(APP+0x2c,0,4),
            (STATE,0,4),(GENERATION+4,0,4),(SAVE+0x2330A,2,2)]+[(RT+52+i,13,1) for i in range(5)]:
            b=self.bench(); b.u.mem_write(address,value.to_bytes(size,'little')); before=b.owner()
            self.assertNotEqual(b.peek(),0); self.no_store(b,before)
            self.assertEqual(bytes(b.u.mem_read(SNAP,32)),b'\xA5'*32)

    def test_token_every_byte_corruption_and_revision_overflow(self):
        b=self.ready(); pristine=bytes(b.u.mem_read(TOKEN,152))
        for i in range(152):
            with self.subTest(byte=i):
                b.u.mem_write(TOKEN,pristine[:i]+bytes([pristine[i]^0x80])+pristine[i+1:])
                b.reset_trace(); self.refusal(b)
        b=self.bench(); b.put(RT+8,0xffffffff); self.assertEqual(b.peek(),0)
        b.draft(); b.put(DRAFT+8,0xffffffff); before=b.owner()
        self.assertNotEqual(b.prepare(),0); self.no_store(b,before)

    def test_pointer_extent_aliases_and_record_overlap(self):
        b=self.ready(); pristine=bytes(b.u.mem_read(TOKEN,152))
        for p in (0,1,0xfffffffc,0x023ffff0,0x027e007c,0x027e3770,0x027e3780,
                  0x0226ec3c,0x023c0000,FS,FS+0x20,SAVE,OPTIONS,APP,APP+0x2c,RT,GENERATION,DESCRIPTOR,PLUS):
            with self.subTest(pointer=hex(p)):
                b.reset_trace(); before=b.owner()
                self.assertNotEqual(b.peek(p),0); self.no_store(b,before)
                self.assertNotEqual(b.shiny_ui('prepare',APP,SNAP,DRAFT,p),0); self.no_store(b,before)
                self.assertEqual(bytes(b.u.mem_read(TOKEN,152)),pristine)
        for opened,draft,out in ((SNAP,SNAP,TOKEN),(SNAP,DRAFT,SNAP),(SNAP,DRAFT,DRAFT),(SNAP+1,DRAFT,TOKEN),(SNAP,DRAFT+1,TOKEN)):
            b.reset_trace(); self.assertNotEqual(b.shiny_ui('prepare',APP,opened,draft,out),0); self.no_store(b)
        for app in (0,APP+1,0x023fffd4,STATE,SAVE,FS):
            b.reset_trace(); self.assertNotEqual(b.shiny_ui('peek',app,SNAP),0); self.no_store(b)
        for gate in (0,GATE+1,TOKEN,TOKEN+148,APP,RT):
            b.reset_trace(); self.refusal(b,gate=gate)

    def test_gate_required_exact_identity_full_context_and_false_preserves_token(self):
        for offset,value,size in [(0,0,2),(2,16,2),(4,0,4),(4,GATE_CODE+3,4),(4,0x023d1b1d,4),
                                  (8,0,4),(8,APP,4),(8,TOKEN,4),(8,0x027e377c,4)]:
            b=self.ready(); b.u.mem_write(GATE+offset,value.to_bytes(size,'little')); self.refusal(b)
        for address in (CONTEXT+4,CONTEXT+8,CONTEXT+12):
            b=self.ready(); b.put(address,b.get(address)^1); self.refusal(b)
            self.assertEqual(b.ime_writes,[0,1]); self.assertEqual(len(b.gate_calls),1)

    def test_current_runtime_app_and_training_proof_stale_before_commit(self):
        mutations=[(APP+0x28,10,4),(APP+0x24,OPTIONS+4,4),(RT+4,4,4),(RT+8,8,4),(RT+12,12,4),
            (RT+28,0,4),(RT+32,61,4),(FS+0x100,61,4),(RT+48,39,1),(RT+49,1,1),(RT+50,1,1),
            (RT+51,1,1),(RT+52,2,1),(RT+60,26,2),(RT+680,1,4),(RT+704,1,4),
            (GENERATION+4,2,4),(SAVE+0x23010,18,4),(SAVE+0x2330A,1,2),(SHINY,124,4)]
        for a,v,n in mutations:
            with self.subTest(address=hex(a)):
                b=self.ready(search=1); b.u.mem_write(a,v.to_bytes(n,'little')); self.refusal(b)
        for action in ('bind','load'):
            b=self.ready(); b.ui(action,SAVE,1); b.reset_trace(); self.refusal(b)

    def test_real_storage_both_banks_erased_leased_foreign_future_unreadable(self):
        for leased in (False,True):
            b=self.bench(leased); self.assertEqual(b.peek(),0); b.draft(); self.assertEqual(b.prepare(),0)
            b.reset_trace(); self.assertEqual(b.commit(),0)
            self.assertEqual(len(b.reads),20 if leased else 528)
        for bank in (0x31000,0x71000):
            for kind in ('foreign','future','unreadable'):
                b=self.ready(); b.put(ADMITTED,1); self.assertEqual(b.prepare(),0); b.reset_trace()
                if kind=='foreign':b.flash[bank+0x400:bank+0x404]=b'BAD!'
                elif kind=='future':
                    # Real primary future-format guard: valid family magic/version.
                    b.flash[bank:bank+8]=struct.pack('<IHH',0x31524e54,0xffff,256)
                else:b.fail_address=bank+0x400
                self.refusal(b)

    def test_storage_refusals_do_not_publish_peek_or_prepared_token(self):
        for operation in ('peek','prepare'):
            for bank in (0x31000,0x71000):
                for kind in ('foreign','future','unreadable'):
                    b=self.bench()
                    if operation=='prepare':self.assertEqual(b.peek(),0); b.draft()
                    if kind=='foreign':b.flash[bank+0x400:bank+0x404]=b'BAD!'
                    elif kind=='future':b.flash[bank+0x200:bank+0x208]=struct.pack('<IHH',0x31524e54,3,256)
                    else:b.fail_address=bank+0x400
                    before=b.owner(); wire=bytes(b.u.mem_read(SNAP,32))+bytes(b.u.mem_read(TOKEN,152))
                    self.assertNotEqual(getattr(b,operation)(),0); self.no_store(b,before)
                    self.assertEqual(bytes(b.u.mem_read(SNAP,32))+bytes(b.u.mem_read(TOKEN,152)),wire)

    def test_each_read_mutation_rechecks_all_owner_and_cache_identities(self):
        mutations=[(STATE,0),(STATE+4,SAVE+4),(STATE+8,1),(STATE+12,0),(STATE+16,1),
            (ADMITTED,1),(FLAGS_OFFSET,0),(SHINY,124),(GENERATION,0),(GENERATION+4,2),
            (GENERATION+8,SAVE+4),(GENERATION+12,1),(SAVE+0x23010,18),(SAVE+0x2330A,1),
            (FS+12,SAVE+4),(0x021d4158,FS+4),(APP+0x28,10),(RT+4,4),(RT+8,8),
            (RT+12,12),(RT+28,0),(RT+32,61),(FS+0x100,61),(RT+680,1),(RT+704,1)]
        for operation in ('peek','prepare','commit'):
            for seam in range(1,11):
                for address,value in mutations:
                    with self.subTest(operation=operation,seam=seam,address=hex(address)):
                        b=self.ready() if operation=='commit' else self.bench()
                        if operation=='prepare':self.assertEqual(b.peek(),0); b.draft()
                        # Commit's first peek READ cycle is also covered. The
                        # last validation cycle is exercised separately below.
                        b.reset_trace(); post=[]
                        def mutate(x,count):
                            if count==seam:x.put(address,value); post.append(x.owner())
                        b.on_read=mutate
                        before_output=bytes(b.u.mem_read(SNAP if operation=='peek' else TOKEN,32 if operation=='peek' else 152))
                        self.assertNotEqual(getattr(b,operation)(),0)
                        self.assertTrue(post,"expected real hardware READ/mutation seam"); self.no_store(b,post[-1]); self.no_publication(b); self.assertEqual(bytes(b.u.mem_read(SNAP if operation=='peek' else TOKEN,len(before_output))),before_output)

    def test_each_last_storage_read_and_final_gate_catch_dirty_native_plus(self):
        for seam in range(1,11):
            for address in (STATE,STATE+4,STATE+8,STATE+12,STATE+16,ADMITTED,FLAGS_OFFSET,SHINY,
                            GENERATION,GENERATION+4,GENERATION+8,GENERATION+12,SAVE+0x23010,
                            SAVE+0x2330A,FS+12,0x021d4158,APP+0x28,NATIVE,PLUS,
                            RT+4,RT+8,RT+12,RT+28,RT+32,FS+0x100,RT+60,RT+680,RT+704):
                b=self.ready(search=1); b.put(ADMITTED,1); self.assertEqual(b.prepare(),0); b.reset_trace(); post=[]
                def mutate(x,count):
                    if count==seam:x.put(address,x.get(address)^1); post.append(x.owner())
                b.on_read=mutate; wire=bytes(b.u.mem_read(TOKEN,152))
                self.assertNotEqual(b.commit(),0); self.assertTrue(post,"expected real hardware READ/mutation seam"); self.no_store(b,post[-1]); self.no_publication(b)
                self.assertEqual(bytes(b.u.mem_read(TOKEN,152)),wire); self.assertEqual(b.get(IME),1)
                if address in (NATIVE,PLUS):self.assertEqual(b.gate_calls,[(10,0)])

    def test_irq_before_lock_store_suppression_and_exact_ime_restore(self):
        for initial in (1,):
            for address in (GENERATION+4,APP+0x28,RT+12,RT+28,RT+60,NATIVE,PLUS):
                b=self.ready(search=1); b.put(IME,initial); post=[]
                def mutate(x):x.put(address,x.get(address)^1); post.append(x.owner())
                b.before_lock=mutate; wire=bytes(b.u.mem_read(TOKEN,152))
                self.assertNotEqual(b.commit(),0); self.assertTrue(post,"expected real hardware READ/mutation seam"); self.no_store(b,post[-1]); self.no_publication(b)
                self.assertEqual(bytes(b.u.mem_read(TOKEN,152)),wire); self.assertEqual(b.get(IME),initial)
            b=self.ready(search=1); b.put(ADMITTED,1); self.assertEqual(b.prepare(),0)
            b.reset_trace(); attempts=[]
            def irq(x):
                attempts.append((x.get(IME),x.u.reg_read(UC_ARM_REG_CPSR)&0x9F))
                if x.get(IME) and not (x.u.reg_read(UC_ARM_REG_CPSR)&0x80):x.put(PLUS,x.get(PLUS)^1)
            b.on_store=irq; self.assertEqual(b.commit(),0)
            self.assertTrue(attempts); self.assertEqual(set(attempts),{(0,0x1F)})

    def test_either_irq_mask_refuses_all_apis_before_io_and_publication(self):
        for operation in ('peek','prepare','commit'):
            for ime,cpu_mask in ((1,0x80),(0,0),(0,0x80)):
                with self.subTest(operation=operation,ime=ime,cpu_mask=cpu_mask):
                    b=self.ready(); b.put(IME,ime)
                    cpsr=(b.u.reg_read(UC_ARM_REG_CPSR)&~0x80)|cpu_mask
                    b.u.reg_write(UC_ARM_REG_CPSR,cpsr)
                    before=b.owner(); caller=bytes(b.u.mem_read(SNAP,0x110))
                    self.assertEqual(getattr(b,operation)(),6)
                    self.no_store(b,before); self.no_publication(b)
                    self.assertEqual(b.reads,[]); self.assertEqual(b.ime_writes,[])
                    self.assertEqual(b.get(IME),ime)
                    # AAPCS permits NZCV condition flags to change, not the
                    # CPU mode, execution-state or interrupt control bits.
                    self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR)&0xFF,cpsr&0xFF)
                    self.assertEqual(bytes(b.u.mem_read(SNAP,0x110)),caller)

    def test_io_observer_records_either_mask_at_hardware_seam(self):
        # Deliberately call the trusted LOW-LEVEL Training API: it permits
        # masked memory-only use and has no Shiny entry policy. These synthetic
        # READs test instrumentation, not native flash progress while masked.
        for ime,cpu_mask in ((1,0),(1,0x80),(0,0),(0,0x80)):
            b=self.bench(); b.put(IME,ime)
            b.u.reg_write(UC_ARM_REG_CPSR,(b.u.reg_read(UC_ARM_REG_CPSR)&~0x80)|cpu_mask)
            before=b.owner()
            self.assertEqual(b.ui('peek',FS,base.OUT,base.PROOF),0)
            self.assertEqual(len(b.reads),10)
            self.assertEqual(b.masked_io,[] if ime and not cpu_mask else [0x0202877C]*10)
            self.assertEqual(b.owner(),before); self.assertEqual(b.owner_writes,[])
            self.assertEqual(b.flash_writes,[])

    def test_system_irq_enabled_default_and_pure_arm_query_boundary(self):
        b=self.bench()
        self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR)&0x9F,0x1F)
        for masked in (0,0x80):
            for fiq_mask in (0,0x40):
                cpsr=(b.u.reg_read(UC_ARM_REG_CPSR)&~0xC0)|masked|fiq_mask
                b.u.reg_write(UC_ARM_REG_CPSR,cpsr)
                b.u.reg_write(UC_ARM_REG_SP,b.stack)
                b.u.reg_write(UC_ARM_REG_LR,base.STOP|1)
                b.reset_trace()
                b.u.emu_start(IRQ_QUERY,base.STOP,count=4)
                self.assertEqual(b.u.reg_read(UC_ARM_REG_R0),masked)
                self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR),cpsr)
                self.assertEqual(b.u.reg_read(UC_ARM_REG_SP),b.stack)
                self.assertEqual(b.all_writes,[])
                self.assertEqual(b.reads,[])

    def test_masked_entry_refuses_without_reads_or_outputs_and_preserves_ime0(self):
        for operation in ('peek','prepare','commit'):
            b=self.ready(); b.put(IME,0); before=b.owner()
            snap,token=bytes(b.u.mem_read(SNAP,32)),bytes(b.u.mem_read(TOKEN,152))
            self.assertEqual(getattr(b,operation)(),6)
            self.no_store(b,before)
            self.assertEqual(b.reads,[]); self.assertEqual(b.ime_writes,[])
            self.assertEqual(b.get(IME),0)
            self.assertEqual(bytes(b.u.mem_read(SNAP,32)),snap)
            self.assertEqual(bytes(b.u.mem_read(TOKEN,152)),token)

    def test_native_heap_and_true_system_stack_buffers_canaries(self):
        for out in (0x0226EC40,0x023BFFE0,SNAP):
            b=self.bench(); self.assertEqual(b.peek(out),0); self.no_store(b)
        b=self.ready(search=1); self.assertEqual(b.commit(),0)
        for p,n in b.canaries:self.assertEqual(bytes(b.u.mem_read(p,n)),b'\x5A'*n)
        self.assertLess(STACK-b.low_sp,1600)

    def test_compile_requires_successor_and_known_odd_gate(self):
        path=SOURCE/'features/shiny/ui_transaction.c'
        for flags in ([],['-DSGP_SETTINGS_UI_SUCCESSOR=0'],['-DSGP_SETTINGS_UI_SUCCESSOR=1'],
                      ['-DSGP_SETTINGS_UI_SUCCESSOR=1','-DSGP_SETTINGS_UI_FINAL_CHECK=0'],
                      ['-DSGP_SETTINGS_UI_SUCCESSOR=1','-DSGP_SETTINGS_UI_FINAL_CHECK=0x02206000'],
                      ['-DSGP_SETTINGS_UI_SUCCESSOR=1','-DSGP_SETTINGS_UI_FINAL_CHECK=0x027e0101']):
            p=subprocess.run(['clang',*FLAGS,*flags,'-c',str(path),'-o',str(self.directory/'bad.o')],capture_output=True)
            self.assertNotEqual(p.returncode,0)


if __name__=='__main__':unittest.main()
