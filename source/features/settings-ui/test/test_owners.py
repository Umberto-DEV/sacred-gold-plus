"""Coordinator TDD against compiled C and actual accepted Training/Shiny."""
from pathlib import Path
import tempfile
import unittest
from unicorn import UC_HOOK_CODE
from owners_bench import *

class OwnersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='settings-owners-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_all(Path(cls.temp.name))
    def bench(self):return Bench(self.compiled)
    def test_capture_does_not_initialize_or_admit_owners(self):
        b=self.bench(); before=b.owner()
        self.assertEqual(b.capture(),0)
        self.assertEqual(b.owner(),before); self.assertEqual(b.owner_writes,[])
        self.assertEqual(b.read_owners().plus_load,1)
        self.assertEqual(bytes(b.u.mem_read(0x023D8710,3)),bytes(3))
    def test_native_only_skips_missing_plus_shiny_and_preserves_raw_bits(self):
        b=self.bench(); b.put(DESCRIPTOR,0); b.u.mem_write(0x023D8704,b'\0')
        self.assertEqual(b.init(),0)
        b.key(model.RIGHT,0); self.assertEqual(b.request(),2); b.reset_trace()
        self.assertEqual(b.apply(),4)
        self.assertEqual(b.get(OPTIONS),0x8002); self.assertEqual(b.reads,[])
    def test_audio_preview_precedes_apply_and_exact_rollback(self):
        b=self.bench(); b.put(MONO,0xffffffff)
        self.assertEqual(b.init(),0); b.key(model.RIGHT,3)
        self.assertEqual(b.preview(),0)
        self.assertEqual(b.get(MONO),1)
        self.assertEqual(b.rollback(),0)
        self.assertEqual(b.get(MONO),0xffffffff)
    def test_all_groups_use_real_shiny_commit_and_actual_gate(self):
        b=self.bench(); self.assertEqual(b.init(),0)
        b.key(model.RIGHT,0); b.key(model.RIGHT,6); b.key(model.LEFT,11)
        self.assertEqual(b.request(),2); b.reset_trace()
        self.assertEqual(b.apply(),4)
        self.assertEqual(b.get(OPTIONS),0x8002)
        self.assertEqual(bytes(b.u.mem_read(0x023D8713,1)),b'\1')
        self.assertEqual(b.get(RT+8),8)
        self.assertEqual(b.gate_calls,[(30,0)])


    def no_store(self,b,before):
        self.assertEqual(b.owner(),before)
        self.assertEqual(b.owner_writes,[])
        self.assertEqual(b.flash_writes,[])
        self.assertEqual(b.masked_io,[])
        self.assertEqual(b.gate_writes,[]);self.assertEqual(b.calls_after_store,[])
        self.assertEqual(b.bad_refusal_writes,[]);self.assertEqual(b.bad_capture_writes,[])
        for p,n in b.canaries:self.assertEqual(bytes(b.u.mem_read(p,n)),b'\x5a'*n)
    def test_audio_equal_raw_still_requires_new_queue_acceptance(self):
        b=self.bench(); b.put(MONO,1)
        self.assertEqual(b.init(),0); b.key(model.RIGHT,3)
        self.assertEqual(b.preview(),0)
        self.assertEqual(b.get(POOL+8),NODES)
        self.assertEqual(b.read_owners().audio.accepted_generation,1)
        self.assertEqual(b.request(),2); self.assertEqual(b.apply(),4)
    def test_plus_only_unavailable_shiny_preserves_header_clean_wifi_and_metadata(self):
        b=self.bench(); b.put(DESCRIPTOR,0)
        b.u.mem_write(0x023D8719,b'\xab\xcd\xef')
        self.assertEqual(b.init(),0); b.key(model.RIGHT,6)
        b.key(model.RIGHT,10); b.key(model.LEFT,10) # logical1=>2=>1, raw1 retained
        self.assertEqual(b.request(),2); before=bytes(b.u.mem_read(0x023D8710,16)); b.reset_trace()
        self.assertEqual(b.apply(),4); self.assertEqual(b.reads,[])
        want=bytearray(before); want[3]=1
        self.assertEqual(bytes(b.u.mem_read(0x023D8710,16)),bytes(want))
        self.assertEqual(bytes(b.u.mem_read(0x023D8700,2)),b'\1\1')
    def test_dirty_field_capabilities_domains_masks_and_pending_request(self):
        for row in range(11):
            b=self.bench(); self.assertEqual(b.init(),0)
            st=b.read_model()
            target=st.draft.native if row<6 else st.draft.plus
            names=('text','scene','style','audio','button','frame') if row<6 else ('difficulty','wild','animation','npc','wifi')
            setattr(target,names[row if row<6 else row-6],20 if row==5 else 3 if row in (0,10) else 2)
            st.dirty_fields=1<<row; st.dirty_groups=1 if row<6 else 2;st.awaiting_apply=1
            st.view=model.CONFIRM;st.choice=0;st.release_gate=1
            b.u.mem_write(MODEL,bytes(st)); before=b.owner(); b.reset_trace()
            self.assertEqual(b.apply(),1); self.no_store(b,before)
        for kind in ('fields','groups','caps','snapshot','unavailable'):
            b=self.bench(); self.assertEqual(b.init(),0); b.key(model.RIGHT,0);self.assertEqual(b.request(),2)
            st=b.read_model()
            if kind=='fields':st.dirty_fields=0
            elif kind=='groups':st.dirty_groups=0
            elif kind=='caps':st.snapshot.editable_rows=0
            elif kind=='snapshot':st.snapshot.native.text=0
            else:
                # Disabled row cannot be forged by changing the draft/mask.
                st.snapshot.editable_rows&=~1
            b.u.mem_write(MODEL,bytes(st));before=b.owner();b.reset_trace()
            self.assertEqual(b.apply(),1);self.no_store(b,before)
        b=self.bench();self.assertEqual(b.init(),0); b.key(model.RIGHT,0)
        before=b.owner();b.reset_trace();self.assertEqual(b.apply(),0);self.no_store(b,before)
    def test_capture_invalid_rows_are_disabled_without_normalization(self):
        for row,mask,shift,value in ((0,15,0,15),(1,128,7,1),(2,64,6,1),(3,48,4,3),(4,768,8,3),(5,31744,10,31)):
            b=self.bench();b.put(OPTIONS,0x8000|(value<<shift));before=b.owner()
            self.assertEqual(b.capture(),0);self.no_store(b,before)
            snap=model.Snapshot.from_buffer_copy(bytes(b.u.mem_read(SNAPSHOT,C.sizeof(model.Snapshot))))
            self.assertEqual(bool(snap.editable_rows&(1<<row)),row in (1,2))
        for row in range(5):
            b=self.bench();b.u.mem_write((0x023D8713,0x023D8714,0x023D8716,0x023D8717,0x023D8718)[row],b'\xff');before=b.owner()
            self.assertEqual(b.capture(),0);self.no_store(b,before)
            self.assertFalse(b.read_owners().opened.editable_rows&(1<<(row+6)))
    def test_dirty_native_plus_stale_each_last_read_and_caller_edits(self):
        mutations=[(OPTIONS,0x8003,2),(0x023D8713,1,1),(0x023D8700,1,1),(0x023D8704,0,1),
                   (0x023D8703,0,1),(APP+0x28,10,4),(MONO,1,4),
                   (MODEL+model.State.dirty_fields.offset,0,4),
                   (OWNERS+Owners.audio.offset+Audio.accepted_generation.offset,123,4),
                   (OWNERS+Owners.audio.offset+Audio.pending_changed.offset,1,4)]
        for seam in range(1,11):
            for a,v,n in mutations:
                with self.subTest(seam=seam,address=hex(a)):
                    b=self.bench();self.assertEqual(b.init(),0)
                    b.key(model.RIGHT,0);b.key(model.RIGHT,6);b.key(model.LEFT,11)
                    self.assertEqual(b.request(),2);b.put(sh.ADMITTED,1);b.reset_trace();post=[]
                    def mutate(x,count):
                        # prepare and commit's recomputation skip READ when admitted;
                        # these ten are the final storage validation cycle.
                        if count==seam:x.u.mem_write(a,v.to_bytes(n,'little'));post.append(x.owner())
                    b.on_read=mutate
                    self.assertEqual(b.apply(),1);self.assertTrue(post);self.no_store(b,post[-1])
    def test_clean_native_bits_and_clean_plus_changes_are_preserved(self):
        b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,0);b.key(model.LEFT,11);self.assertEqual(b.request(),2)
        b.put(sh.ADMITTED,1);b.reset_trace()
        def mutate(x,n):
            if n==10:
                x.put(OPTIONS,0xc081);x.u.mem_write(0x023D8718,b'\3')
        b.on_read=mutate
        self.assertEqual(b.apply(),4);self.assertEqual(b.get(OPTIONS),0xc082)
        self.assertEqual(bytes(b.u.mem_read(0x023D8718,1)),b'\3')
    def test_dirty_shiny_storage_refusal_preserves_all_other_groups_and_preview(self):
        for bank in (0x31000,0x71000):
            for kind in ('foreign','future','unreadable'):
                b=self.bench();self.assertEqual(b.init(),0)
                b.key(model.RIGHT,0);b.key(model.RIGHT,6);b.key(model.LEFT,11);b.key(model.RIGHT,3)
                self.assertEqual(b.preview(),0);self.assertEqual(b.request(),2)
                if kind=='foreign':b.flash[bank+0x400:bank+0x404]=b'BAD!'
                elif kind=='future':b.flash[bank:bank+8]=struct.pack('<IHH',0x31524e54,65535,256)
                else:b.fail_address=bank+0x400
                before=b.owner();preview=bytes(b.u.mem_read(OWNERS,C.sizeof(Owners)));b.reset_trace()
                self.assertEqual(b.apply(),1);self.no_store(b,before)
                self.assertEqual(bytes(b.u.mem_read(OWNERS,C.sizeof(Owners))),preview)
    def test_audio_busy_coalesces_blocks_apply_and_retries_exact_rollback(self):
        b=self.bench();b.put(MONO,2);self.assertEqual(b.init(),0);b.pool(0)
        b.key(model.RIGHT,3);before=b.owner()
        for _ in range(4):self.assertEqual(b.preview(),6)
        self.assertEqual(b.get(MONO),2);self.assertEqual(b.get(POOL+8),0)
        self.assertEqual(b.request(),2);b.reset_trace();self.assertEqual(b.apply(),1);self.no_store(b,before)
        # Return from error, original draft remains; obtain one returned node.
        b.pool(1);self.assertEqual(b.preview(),0);self.assertEqual(b.get(MONO),1)
        b.pool(0)
        for _ in range(5):self.assertEqual(b.rollback(),6)
        self.assertEqual(b.get(MONO),1);self.assertEqual(b.get(POOL+8),0)
        b.pool(1);self.assertEqual(b.rollback(),0);self.assertEqual(b.get(MONO),2)
        self.assertEqual(b.get(NODES+4),0x18);self.assertEqual(b.get(NODES+8),0x40)
        calls=sum(a==0x020D5714 for a,x,y in b.native_calls);self.assertEqual(b.rollback(),0);self.assertEqual(sum(a==0x020D5714 for a,x,y in b.native_calls),calls)
    def test_audio_selector_B_rolls_back_and_unrelated_apply_waits(self):
        b=self.bench();b.put(MONO,0xffffffff);self.assertEqual(b.init(),0)
        b.key(model.A,3);b.key(model.RIGHT);self.assertEqual(b.preview(),0);self.assertEqual(b.get(MONO),1)
        b.key(model.B);b.pool(0);self.assertEqual(b.preview(),6)
        b.key(model.RIGHT,0);self.assertEqual(b.request(),2);before=b.owner();b.reset_trace()
        self.assertEqual(b.apply(),1);self.no_store(b,before)
        b.pool(1);self.assertEqual(b.preview(),0);self.assertEqual(b.get(MONO),0xffffffff)
    def test_audio_stale_raw_app_and_latest_generation_cannot_reuse_old_acceptance(self):
        b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,3);self.assertEqual(b.preview(),0)
        b.pool(0);b.key(model.LEFT,3);self.assertEqual(b.preview(),6)
        b.key(model.RIGHT,3);self.assertEqual(b.preview(),6)
        self.assertEqual(b.read_owners().audio.pending_generation,3)
        self.assertEqual(b.request(),2);before=b.owner();b.reset_trace();self.assertEqual(b.apply(),1);self.no_store(b,before)
        for address,value in ((MONO,7),(APP+0x28,10)):
            b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,3);b.put(address,value)
            before=b.owner();b.reset_trace();self.assertNotEqual(b.preview(),0);self.no_store(b,before)
    def test_controls_are_local_until_apply_and_masked_entry_refuses(self):
        b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,4)
        self.assertEqual(b.get(BUTTON),0);self.assertEqual(b.preview(),0);self.assertEqual(b.get(BUTTON),0)
        self.assertEqual(b.request(),2);b.reset_trace();self.assertEqual(b.apply(),4)
        self.assertEqual(b.get(BUTTON),3);self.assertEqual(b.get(OPTIONS),0x8101)
        for cpsr_mask,ime in ((0,0),(128,1)):
            b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,0);self.assertEqual(b.request(),2)
            b.put(IME,ime);b.u.reg_write(UC_ARM_REG_CPSR,b.u.reg_read(UC_ARM_REG_CPSR)|cpsr_mask)
            before=b.owner();incoming=b.u.reg_read(UC_ARM_REG_CPSR)&128;b.reset_trace()
            self.assertEqual(b.apply(),1);self.assertEqual(b.read_model().owner_status,6)
            self.no_store(b,before);self.assertEqual(b.get(IME),ime);self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR)&128,incoming)
    def test_capture_output_aliases_bounds_and_failure_publication(self):
        invalid=(0,1,0xfffffffc,FS,SAVE,APP,APP+0x2c,OPTIONS,RT,0x023c0000,0x027e007c,0x027e3770,0x027e3780,0x0226ec3c)
        for p in invalid:
            b=self.bench();before=b.owner();b.reset_trace()
            self.assertNotEqual(b.capture(owners=p),0);self.no_store(b,before)
            self.assertNotEqual(b.capture(out=p),0);self.no_store(b,before)
        b=self.bench();self.assertNotEqual(b.capture(out=OWNERS+4),0)
        b=self.bench();self.assertEqual(b.capture(owners=0x027e3400,out=0x027e3500),0)
    def test_gate_invalid_context_is_pure_and_full_extent_checked(self):
        b=self.bench();self.assertEqual(b.init(),0)
        for p in (0,1,0xfffffffc,APP,FS,SAVE,RT,0x023bfff0,0x027e3770,0x027e3780):
            before=b.owner();b.reset_trace();self.assertEqual(b.call(b.os['settings_final_check'],p),0);self.no_store(b,before)
            self.assertTrue(all(0x027e0080<=a<a+n<=b.stack for a,n,v in b.all_writes))

    def test_irq_masked_capture_and_preview_refuse_before_io_or_ledger_updates(self):
        b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,3)
        b.u.reg_write(UC_ARM_REG_CPSR,b.u.reg_read(UC_ARM_REG_CPSR)|128)
        before=b.owner();wire=bytes(b.u.mem_read(OWNERS,C.sizeof(Owners)));b.reset_trace()
        self.assertEqual(b.capture(),6);self.assertEqual(b.reads,[])
        self.assertEqual(b.preview(),6);self.assertEqual(b.rollback(),6)
        self.assertEqual(bytes(b.u.mem_read(OWNERS,C.sizeof(Owners))),wire);self.no_store(b,before)

    def test_native_accessor_offset_mutation_rejects_capture_and_native_apply(self):
        b=self.bench();b.on_read=lambda x,n:x.put(SAVE+0x2302c,0x104) if n==10 else None
        self.assertNotEqual(b.capture(),0)
        self.assertEqual(b.owner_writes,[])
        b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,0);self.assertEqual(b.request(),2)
        b.put(SAVE+0x2302c,0x104);before=b.owner();b.reset_trace()
        self.assertEqual(b.apply(),1);self.no_store(b,before)

    def test_every_scalar_valid_domain_maps_only_its_exact_raw_field(self):
        rows=[(0,2,0x000f,0),(1,1,0x0080,7),(2,1,0x0040,6),(3,1,0x0030,4),(4,1,0x0300,8),(5,19,0x7c00,10)]
        for row,value,mask,shift in rows:
            b=self.bench();self.assertEqual(b.init(),0)
            for _ in range(value):b.key(model.RIGHT,row)
            if row==0:b.key(model.LEFT,row);b.key(model.RIGHT,row)
            if row==3:self.assertEqual(b.preview(),0)
            self.assertEqual(b.request(),2);b.reset_trace();self.assertEqual(b.apply(),4)
            want=(0x8001&~mask)|(value<<shift)
            self.assertEqual(b.get(OPTIONS),want)
            self.assertEqual(b.calls_after_store,[]);self.assertEqual(b.gate_writes,[])
        for row,key,value,raw in ((6,model.RIGHT,1,1),(7,model.LEFT,0,0),(8,model.LEFT,0,0),(9,model.RIGHT,1,1),
                                 (10,model.LEFT,0,0),(10,model.RIGHT,2,3)):
            b=self.bench();self.assertEqual(b.init(),0);b.key(key,row);self.assertEqual(b.request(),2)
            before=bytearray(b.u.mem_read(0x023D8710,16));b.reset_trace();self.assertEqual(b.apply(),4)
            before[(3,4,6,7,8)[row-6]]=raw
            self.assertEqual(bytes(b.u.mem_read(0x023D8710,16)),bytes(before))
        for initial,key,want in ((0,model.RIGHT,2),(3,model.LEFT,2)):
            b=self.bench();b.u.mem_write(0x023D8718,bytes([initial]));self.assertEqual(b.init(),0)
            b.key(key,10);self.assertEqual(b.request(),2);self.assertEqual(b.apply(),4)
            self.assertEqual(bytes(b.u.mem_read(0x023D8718,1)),bytes([want]))
    def test_empty_cache_mode_target_clear_information_and_search_queue(self):
        b=self.bench();b.put(RT+28,0);b.u.mem_write(RT+52,bytes(5));self.assertEqual(b.init(),0)
        b.key(model.Y,12);self.assertEqual(b.read_model().view,model.INFO)
        b.key(model.B);b.key(model.A,12);self.assertEqual(b.read_model().notice,2)
        b.key(model.A);self.assertEqual(b.read_model().draft.shiny.target,0)
        self.assertEqual(b.request(),2);b.reset_trace();self.assertEqual(b.apply(),4)
        self.assertEqual(bytes(b.u.mem_read(sh.SHINY+4,2)),bytes(2))
        b=self.bench();b.put(RT+28,0);b.u.mem_write(RT+52,bytes(5));self.assertEqual(b.init(),0)
        b.key(model.LEFT,11);self.assertEqual(b.request(),2);self.assertEqual(b.apply(),4)
        b=self.bench();self.assertEqual(b.init(),0)
        b.key(model.A,13);b.key(model.DOWN);b.key(model.DOWN);b.key(model.A)
        self.assertEqual(b.read_model().draft.shiny.search,1);self.assertEqual(bytes(b.u.mem_read(RT+51,1)),b'\0')
        b.key(model.RIGHT,0);b.key(model.RIGHT,6);self.assertEqual(b.request(),2);b.reset_trace()
        self.assertEqual(b.apply(),4);self.assertEqual(bytes(b.u.mem_read(RT+51,1)),b'\1')
        self.assertEqual(b.get(RT+668),11);self.assertEqual(b.get(RT+672),8)
        self.assertEqual(b.calls_after_store,[]);self.assertEqual(b.gate_writes,[])
    def test_actual_erased_storage_both_banks_and_full_context_gate_are_bounded(self):
        b=Bench(self.compiled,leased=False);self.assertEqual(b.init(),0);b.key(model.LEFT,11)
        self.assertEqual(b.request(),2);b.reset_trace();self.assertEqual(b.apply(),4)
        self.assertEqual(len(b.reads),792);self.assertEqual(b.gate_calls,[(792,0)])
        self.assertEqual(b.gate_writes,[]);self.assertEqual(b.calls_after_store,[])
        self.assertEqual(b.bad_refusal_writes,[]);self.assertEqual(b.bad_capture_writes,[])
        context,wire=b.gate_contexts[-1]
        self.assertEqual(struct.unpack_from('<II',wire),(0x31585453,492))
        self.assertTrue(0x027e0080<=context<context+492<=b.stack)
        self.assertLess(b.stack-b.low_sp,3000)
    def test_feature_guards_native_audio_and_owner_model_each_last_read(self):
        mutations=[(0x023D8E41,0,1),(0x023D89E2,0,1),(0x023DA240,0,1),(0x023D8716,0,1),
                   (0x023D8717,1,1),(0x023D8718,3,1),(BUTTON,3,4),(SAVE+0x2302c,0x104,4)]
        for seam in range(1,11):
            for address,value,size in mutations:
                with self.subTest(seam=seam,address=hex(address)):
                    b=self.bench();self.assertEqual(b.init(),0)
                    for row,key in ((4,model.RIGHT),(8,model.LEFT),(9,model.RIGHT),(10,model.RIGHT),(11,model.LEFT)):
                        b.key(key,row)
                    self.assertEqual(b.request(),2);b.put(sh.ADMITTED,1);b.reset_trace();post=[]
                    def mutate(x,n):
                        if n==seam:x.u.mem_write(address,value.to_bytes(size,'little'));post.append(x.owner())
                    b.on_read=mutate;self.assertEqual(b.apply(),1);self.assertTrue(post);self.no_store(b,post[-1])

    def test_invalid_clean_audio_does_not_block_text_preview_or_apply(self):
        b=self.bench();b.put(OPTIONS,0x8031);self.assertEqual(b.init(),0);b.key(model.RIGHT,0)
        self.assertEqual(b.preview(),0);self.assertEqual(b.get(MONO),0)
        self.assertEqual(b.request(),2);self.assertEqual(b.apply(),4);self.assertEqual(b.get(OPTIONS),0x8032)

    def test_forged_apply_marker_without_confirmation_cannot_commit(self):
        for field,value in (('awaiting_apply',2),('view',model.ROOT_VIEW),('choice',1),('release_gate',0)):
            b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,0);self.assertEqual(b.request(),2)
            st=b.read_model();setattr(st,field,value);b.u.mem_write(MODEL,bytes(st));before=b.owner();b.reset_trace()
            self.assertEqual(b.apply(),1);self.no_store(b,before)

    def test_forged_unavailable_method_cannot_bypass_selector_capability(self):
        b=self.bench();self.assertEqual(b.init(),0)
        st=b.read_model();st.draft.shiny.method=4;st.dirty_fields=1<<14;st.dirty_groups=4
        st.awaiting_apply=1;st.view=model.CONFIRM;st.choice=0;st.release_gate=1
        b.u.mem_write(MODEL,bytes(st));before=b.owner();b.reset_trace()
        self.assertEqual(b.apply(),1);self.no_store(b,before)

    def test_unaccepted_first_audio_intent_can_cancel_without_queue_or_acceptance(self):
        b=self.bench();b.put(MONO,2);self.assertEqual(b.init(),0);b.pool(0)
        b.key(model.RIGHT,3);self.assertEqual(b.preview(),6)
        history=b.read_owners().audio.accepted_generation
        self.assertEqual(b.rollback(),0);self.assertEqual(b.get(MONO),2);self.assertEqual(b.get(POOL+8),0)
        ledger=b.read_owners().audio
        self.assertEqual((ledger.ever_previewed,ledger.accepted_generation,ledger.accepted_target),(0,history,2))
        self.assertEqual((ledger.pending_target,ledger.pending_generation),(2,2))
        b.key(model.LEFT,3);self.assertEqual(b.preview(),0);b.key(model.RIGHT,0)
        self.assertEqual(b.request(),2);b.reset_trace();self.assertEqual(b.apply(),4)
        self.assertEqual(b.get(OPTIONS),0x8002);self.assertEqual(b.get(MONO),2)
        for address,value in ((MONO,7),(APP+0x28,10)):
            b=self.bench();self.assertEqual(b.init(),0);b.pool(0);b.key(model.RIGHT,3);self.assertEqual(b.preview(),6)
            b.put(address,value);before=b.owner();wire=bytes(b.u.mem_read(OWNERS,C.sizeof(Owners)));b.reset_trace()
            self.assertNotEqual(b.rollback(),0);self.no_store(b,before)
            self.assertEqual(bytes(b.u.mem_read(OWNERS,C.sizeof(Owners))),wire)

    def test_raw_equal_audio_intents_do_not_reuse_cancelled_generation(self):
        b=self.bench();b.put(MONO,1);self.assertEqual(b.init(),0);b.pool(0)
        b.key(model.RIGHT,3);self.assertEqual(b.preview(),6);self.assertEqual(b.read_owners().audio.pending_generation,1)
        self.assertEqual(b.rollback(),0);self.assertEqual(b.read_owners().audio.pending_generation,2)
        b.key(model.LEFT,3);self.assertEqual(b.preview(),0)
        b.key(model.RIGHT,3);self.assertEqual(b.preview(),6);self.assertEqual(b.read_owners().audio.pending_generation,3)

    def test_forged_owner_identity_cannot_publish_error_into_live_field_system(self):
        for state_address in (FS,SAVE,OPTIONS):
            b=self.bench();self.assertEqual(b.init(),0)
            owner=b.read_owners();owner.fs=FS+0x200;owner.save=SAVE+0x40000;b.u.mem_write(OWNERS,bytes(owner))
            for field,value in (('awaiting_apply',1),('view',model.CONFIRM),('choice',0),('release_gate',1)):
                b.u.mem_write(state_address+getattr(model.State,field).offset,bytes([value]))
            before=bytes(b.u.mem_read(state_address,C.sizeof(model.State)));b.reset_trace()
            self.assertEqual(b.call(b.os['settings_apply'],state_address,OWNERS),0)
            self.assertEqual(bytes(b.u.mem_read(state_address,C.sizeof(model.State))),before)
            self.assertTrue(all(a==IME or 0x027e0080<=a<a+n<=b.stack for a,n,v in b.all_writes))

    def test_apply_preview_rollback_inputs_reject_all_invalid_extents_and_aliases(self):
        b=self.bench();self.assertEqual(b.init(),0);b.key(model.RIGHT,0);self.assertEqual(b.request(),2)
        invalid=(0,1,0xfffffffc,FS,SAVE,OPTIONS,APP,APP+0x2c,RT,0x023bfff0,0x027e007c,0x027e3770,0x027e3780)
        for p in invalid:
            before=b.owner();model_wire=bytes(b.u.mem_read(MODEL,C.sizeof(model.State)));b.reset_trace()
            self.assertEqual(b.call(b.os['settings_apply'],p,OWNERS),0)
            self.assertEqual(b.call(b.os['settings_apply'],MODEL,p),0)
            self.assertNotEqual(b.call(b.os['settings_owner_preview'],OWNERS,p),0)
            self.assertNotEqual(b.call(b.os['settings_owner_preview'],p,MODEL),0)
            self.assertNotEqual(b.call(b.os['settings_owner_rollback'],p),0)
            self.no_store(b,before);self.assertEqual(bytes(b.u.mem_read(MODEL,C.sizeof(model.State))),model_wire)
            self.assertTrue(all(a==IME or 0x027e0080<=a<a+n<=b.stack for a,n,v in b.all_writes))
        b.reset_trace();before=b.owner()
        self.assertEqual(b.call(b.os['settings_apply'],OWNERS,OWNERS),0)
        self.assertNotEqual(b.call(b.os['settings_owner_preview'],OWNERS,OWNERS),0);self.no_store(b,before)

    def watch_transaction_entries(self,b):
        calls=[]
        entries={b.symbols['sgp_shiny_ui_'+name]&~1:name for name in ('prepare','commit')}
        def observe(u,address,size,data):
            if address in entries:calls.append(entries[address])
        b.u.hook_add(UC_HOOK_CODE,observe,begin=sh.EXT,end=sh.EXT+0xfff)
        return calls

    def test_late_live_extent_alias_refusal_does_not_publish_after_prepare_or_commit(self):
        # Removing a post-I/O refusal check would write six reducer bytes into
        # a newly live SaveData, or publish through a caller extent overlapping
        # a newly live FieldSystem/owner record. Both complete inputs must stay safe.
        for phase in ('prepare','commit'):
            for live_kind in ('fs','save'):
                for victim in ('state','owners','invalid'):
                    with self.subTest(phase=phase,live=live_kind,victim=victim):
                        b=self.bench();self.assertEqual(b.init(),0)
                        b.key(model.RIGHT,0);b.key(model.LEFT,11);self.assertEqual(b.request(),2)
                        # Keep state outside a new SaveData which covers only owners.
                        state=0x022f8000 if live_kind=='save' and victim=='owners' else MODEL
                        b.u.mem_write(state,bytes(b.u.mem_read(MODEL,C.sizeof(model.State))))
                        if phase=='commit':b.put(sh.ADMITTED,1)
                        target=0 if victim=='invalid' else (state if victim=='state' else OWNERS)-0x10
                        if live_kind=='fs' and target:b.put(target+12,SAVE)
                        state_before=bytes(b.u.mem_read(state,C.sizeof(model.State)))
                        owners_before=bytes(b.u.mem_read(OWNERS,C.sizeof(Owners)));post=[];b.reset_trace()
                        entries=self.watch_transaction_entries(b)
                        def mutate(x,n):
                            if n==10:
                                x.put(0x021d4158 if live_kind=='fs' else FS+12,target)
                                post.append(x.owner())
                        b.on_read=mutate
                        self.assertEqual(b.call(b.os['settings_apply'],state,OWNERS),0)
                        self.assertEqual(entries,['prepare'] if phase=='prepare' else ['prepare','commit'])
                        self.assertEqual(len(b.reads),10);self.assertEqual(len(post),1)
                        self.assertEqual(bytes(b.u.mem_read(state,C.sizeof(model.State))),state_before)
                        self.assertEqual(bytes(b.u.mem_read(OWNERS,C.sizeof(Owners))),owners_before)
                        self.no_store(b,post[-1])
                        self.assertTrue(all(a==IME or 0x027e0080<=a<a+n<=b.stack for a,n,v in b.all_writes))

    def test_late_captured_extent_changes_are_readmitted_before_error_publication(self):
        for phase in ('prepare','commit'):
            for field in ('app','fs','save'):
                with self.subTest(phase=phase,captured=field):
                    b=self.bench();self.assertEqual(b.init(),0)
                    b.key(model.RIGHT,0);b.key(model.LEFT,11);self.assertEqual(b.request(),2)
                    if phase=='commit':b.put(sh.ADMITTED,1)
                    before=bytes(b.u.mem_read(MODEL,C.sizeof(model.State)));post=[];owners_after=[];b.reset_trace()
                    entries=self.watch_transaction_entries(b)
                    def mutate(x,n):
                        if n==10:
                            x.put(OWNERS+getattr(Owners,field).offset,MODEL)
                            x.put(APP+0x28,10) # Actual Shiny refuses at this same IO boundary.
                            post.append(x.owner());owners_after.append(bytes(x.u.mem_read(OWNERS,C.sizeof(Owners))))
                    b.on_read=mutate
                    self.assertEqual(b.apply(),0);self.assertEqual(len(b.reads),10);self.assertEqual(len(post),1)
                    self.assertEqual(entries,['prepare'] if phase=='prepare' else ['prepare','commit'])
                    self.assertEqual(bytes(b.u.mem_read(MODEL,C.sizeof(model.State))),before)
                    self.assertEqual(bytes(b.u.mem_read(OWNERS,C.sizeof(Owners))),owners_after[0]);self.no_store(b,post[0])
                    self.assertTrue(all(a==IME or 0x027e0080<=a<a+n<=b.stack for a,n,v in b.all_writes))

    def test_late_safe_identity_refusal_still_reports_error_after_prepare_or_commit(self):
        for phase in ('prepare','commit'):
            for live_kind in ('fs','save'):
                with self.subTest(phase=phase,live=live_kind):
                    b=self.bench();self.assertEqual(b.init(),0)
                    b.key(model.RIGHT,0);b.key(model.LEFT,11);self.assertEqual(b.request(),2)
                    if phase=='commit':b.put(sh.ADMITTED,1)
                    target=0x022f0000 if live_kind=='fs' else 0x02300000
                    if live_kind=='fs':b.put(target+12,SAVE)
                    draft=bytes(b.read_model().draft);snapshot=bytes(b.read_model().snapshot)
                    owners_before=bytes(b.u.mem_read(OWNERS,C.sizeof(Owners)));post=[];b.reset_trace()
                    entries=self.watch_transaction_entries(b)
                    def mutate(x,n):
                        if n==10:
                            x.put(0x021d4158 if live_kind=='fs' else FS+12,target)
                            post.append(x.owner())
                    b.on_read=mutate
                    self.assertEqual(b.apply(),1);self.assertEqual(len(b.reads),10);self.assertEqual(len(post),1)
                    self.assertEqual(entries,['prepare'] if phase=='prepare' else ['prepare','commit'])
                    self.assertEqual(b.read_model().view,model.ERROR);self.assertEqual(b.read_model().owner_status,2)
                    self.assertEqual(bytes(b.read_model().draft),draft);self.assertEqual(bytes(b.read_model().snapshot),snapshot)
                    self.assertEqual(bytes(b.u.mem_read(OWNERS,C.sizeof(Owners))),owners_before);self.no_store(b,post[-1])

if __name__=='__main__':unittest.main()
