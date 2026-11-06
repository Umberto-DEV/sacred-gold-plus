"""Class A compiled adapter tests with explicit NNS/IRQ boundary seams."""
import tempfile
import unittest
from pathlib import Path
from heap_bench import *
class HeapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='heap-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_heap(Path(cls.temp.name))
    def bench(self):return HeapBench(self.compiled)
    def test_inactive_word_scan_checks_every_lane_and_tail_on_each_call(self):
        for ident in (*range(6,10),*range(154,161)):
            for value in (3,29,255):
                b=self.bench();self.assertEqual(b.call('hmeta'),1)
                b.put(b.idxs+ident,value,1)
                self.assertEqual(b.call('hmeta'),0,(ident,value))
                b.put(b.idxs+ident,28,1);self.assertEqual(b.call('hmeta'),1)
    def test_topology_scan_has_linear_cost_with_late_ids_and_rechecks_mutations(self):
        b=self.bench()
        for slot in range(4,28):
            child=PARENT+0x10000+slot*0x1000;b.header(child,0x200)
            b.put(b.handles+4*slot,child);b.put(b.parents+4*slot,PARENT)
            b.put(b.raws+4*slot,child);b.put(b.idxs+160-(slot-4),slot,1)
        self.assertEqual(b.call('hmeta'),1)
        # All 161 IDs and 28 slots are checked without rescanning the ID
        # table per live heap. ARM instruction count, not hardware cycles.
        self.assertLess(b.metrics[-1][2],10000)
        b.put(b.idxs+4,27,1)  # duplicate of late ID137
        self.assertEqual(b.call('hmeta'),0)
        b.put(b.idxs+4,28,1);b.put(b.idxs+137,28,1)  # orphan live handle27
        self.assertEqual(b.call('hmeta'),0)
        b.put(b.idxs+137,27,1)
        self.assertEqual(b.call('hmeta'),1,'no cached topology across calls')
    def test_create_publishes_native_child_and_exact_backing(self):
        for n in (0x30000,0x40000):
            b=self.bench();self.assertEqual(b.create(n),1)
            self.assertEqual(b.get(b.idxs+38,1),4)
            self.assertEqual((b.get(TOKEN+20),b.get(b.parents+16)),(n,PARENT))
            self.assertEqual(b.get(b.counts+6,2),0)
    def refusal(self,b,action):
        old=b.token(),b.metadata();calls=len(b.calls);writes=len(b.writes)
        self.assertEqual(action(),0);self.assertEqual((b.token(),b.metadata()),old)
        self.assertFalse(any(p not in (DISABLE,RESTORE) for p,a in b.calls[calls:]))
        self.assertFalse(any(not STACK-1024<=p<STACK for p,n,v in b.writes[writes:]))
    def test_create_rejects_bad_sizes_generation_topology_extents_and_busy(self):
        for n in (0,0x30001,0x40001,0xffffffff):
            b=self.bench();self.refusal(b,lambda:b.create(n))
        cases=[(META,0xfffffff0,4),(META+0x14,38,2),(META+0x16,3,2),(META+0x18,256,2),(META+0x1a,27,2),(META+4,BASE,4),(BASE+662+38,3,1),(BASE+340+76,1,2),(BASE+12,0,4),(PARENT+0x1c,0xffffffff,4)]
        for p,v,n in cases:
            b=self.bench();b.put(p,v,n);self.refusal(b,b.create)
        b=self.bench();self.refusal(b,lambda:b.create(g=0))
        b=self.bench();b.create();self.refusal(b,b.create)
        b=self.bench()
        for i in range(4,28):
            child=PARENT+0x10000+i*0x1000;b.header(child,0x200)
            b.put(b.handles+4*i,child);b.put(b.parents+4*i,PARENT)
            b.put(b.raws+4*i,child);b.put(b.idxs+i,i,1)
        self.refusal(b,b.create) # Well-formed topology, no dynamic handle slot.
    def test_create_alloc_failures_and_constructor_unwind_preserve_token_metadata(self):
        for n in (0x30000,0x40000):
            for boundary in (ALLOC,CREATE):
                b=self.bench();b.u.mem_write(TOKEN,b'\x5a'*92);old=b.token(),b.metadata();b.fail=boundary
                self.assertEqual(b.create(n),0);self.assertEqual((b.token(),b.metadata()),old)
                if boundary==CREATE:self.assertEqual([p for p,a in b.calls].count(FREE),1)
    def test_alloc_header_zero_count_tracking_and_free_once(self):
        b=self.bench();self.assertEqual(b.create(),1)
        for tail in (0,1):
            p=b.alloc(33,tail);self.assertNotEqual(p,0);self.assertEqual(p%4,0)
            self.assertEqual(b.get(p-4,1),38);self.assertEqual(b.get(b.counts+76,2),1)
            self.assertEqual(bytes(b.u.mem_read(p,33)),bytes(33));self.assertEqual(b.get(p-32,2),0x5544)
            self.assertEqual(b.calls[-2][1][2]&0xffffffff,0xfffffffc if tail else 4)
            self.assertEqual(b.destroy(),0);self.refusal(b,lambda:b.free(p+4))
            self.assertEqual(b.free(p),1);self.assertEqual(b.get(b.counts+76,2),0);self.refusal(b,lambda:b.free(p))
        self.assertEqual(b.destroy(),1);self.assertEqual(b.token(),bytes(92));self.refusal(b,b.destroy)
        self.assertEqual(b.get(b.idxs+38,1),28)
        self.assertEqual([b.get(p+16) for p in (b.handles,b.parents,b.raws)],[0,0,0])
    def test_alloc_refuses_overflow_count_full_ledger_bad_token_and_native_failure(self):
        for n in (0,0xffffffed,0xffffffff):
            b=self.bench();b.create();self.refusal(b,lambda:b.alloc(n))
        b=self.bench();b.create();b.put(b.counts+76,65535,2);self.refusal(b,lambda:b.alloc(1))
        b=self.bench();b.create();self.refusal(b,lambda:b.alloc(1,2))
        b=self.bench();b.create();b.put(TOKEN+12,0xffffffff);self.refusal(b,lambda:b.alloc(1))
        b=self.bench();b.create();b.fail=ALLOC;old=b.token(),b.metadata();self.assertEqual(b.alloc(8),0);self.assertEqual((b.token(),b.metadata()),old)
        b=self.bench();b.create()
        for i in range(16):self.assertNotEqual(b.alloc(1),0)
        self.refusal(b,lambda:b.alloc(1))
    def test_free_refuses_wrong_header_count_and_null_without_native_call(self):
        for offset,value,n in ((-4,37,1),(0,0,2)):
            b=self.bench();b.create();p=b.alloc(8)
            b.put(p+offset if offset else b.counts+76,value,n);self.refusal(b,lambda:b.free(p))
        b=self.bench();b.create();self.refusal(b,lambda:b.free(0))
    def test_irq_mask_and_ime_preserved_for_every_lifecycle_step(self):
        for mask in (0,128):
            for ime in (0,1):
                b=self.bench();b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
                self.assertEqual(b.create(),1);p=b.alloc(8);self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
    def test_token_can_move_to_another_live_caller_object(self):
        b=self.bench();b.create();target=TOKEN+128;b.allowed.append((target,target+92))
        b.u.mem_write(target,b.token());b.u.mem_write(TOKEN,bytes(92))
        self.refusal(b,lambda:b.alloc(8));self.assertNotEqual(b.call('ui_alloc38',target,8,0),0)
    def test_token_must_not_alias_metadata_or_live_native_header(self):
        for target in (BASE,BASE+340,PARENT):
            b=self.bench();old=b.metadata();calls=len(b.calls)
            self.assertEqual(b.call('ui_heap38_create',target,0x30000,1),0)
            self.assertEqual(b.metadata(),old)
            self.assertFalse(any(p not in (DISABLE,RESTORE) for p,a in b.calls[calls:]))
    def test_each_allocation_failure_leaves_prior_acquisitions_usable(self):
        for k in range(16):
            b=self.bench();b.create();ps=[b.alloc(7) for _ in range(k)]
            b.fail=ALLOC;old=b.token(),b.metadata();self.assertEqual(b.alloc(7),0)
            self.assertEqual((b.token(),b.metadata()),old);b.fail=None
            for p in reversed(ps):self.assertEqual(b.free(p),1)
            self.assertEqual(b.destroy(),1)
    def test_success_stores_only_the_expected_native_metadata_fields(self):
        b=self.bench()
        def stores(action,want):
            b.writes=[];self.assertTrue(action())
            got={(p,n) for p,n,v in b.writes if BASE<=p<BASE+824}
            self.assertEqual(got,want)
        stores(b.create,{(BASE+16,4),(BASE+132,4),(BASE+244,4),(BASE+416,2),(BASE+700,1)})
        stores(lambda:b.alloc(9),{(BASE+416,2)})
        p=b.get(TOKEN+28);b.put(b.counts+76,0,2)
        self.refusal(b,b.destroy) # Empty count alone never authorizes destruction.
        b.put(b.counts+76,1,2)
        stores(lambda:b.free(p),{(BASE+416,2)})
        stores(b.destroy,{(BASE+16,4),(BASE+132,4),(BASE+244,4),(BASE+700,1)})

    def test_native_template2_null_handle_allows_both_backing_lifecycles(self):
        for n in (0x30000,0x40000):
            with self.subTest(backing=n):
                b=self.bench()
                self.assertEqual(tuple(b.get(b.idxs+j,1) for j in range(4)),(0,1,2,3))
                self.assertEqual(b.create(n),1)
                p=b.alloc(21);self.assertTrue(p)
                self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
                self.assertEqual((b.get(b.idxs+2,1),b.get(b.handles+8),b.get(b.counts+4,2)),(2,0,0))

    def test_only_native_template2_null_zero_count_mapping_is_admitted(self):
        for n in (0x30000,0x40000):
            for target,value,width in ((BASE+662+4,5,1),(BASE+662+2,28,1),(BASE+340+4,1,2),(BASE+662+4,2,1),(BASE+662,28,1)):
                with self.subTest(backing=n,target=target,value=value):
                    b=self.bench();self.assertEqual(b.create(n),1);p=b.alloc(21)
                    original=b.get(target,width);b.put(target,value,width)
                    self.refusal(b,lambda:b.alloc(8));self.refusal(b,lambda:b.free(p));self.refusal(b,b.destroy)
                    b.put(target,original,width);self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
                    b=self.bench();b.put(target,value,width);self.refusal(b,lambda:b.create(n))

    def test_unrelated_retired_counts_are_history_but_owned38_count_must_be_zero(self):
        for count in (1,65535):
            b=self.bench();b.put(b.counts+150,count,2)
            self.assertEqual(b.get(b.idxs+75,1),28)
            self.assertEqual(b.create(),1);p=b.alloc(21);self.assertTrue(p)
            self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
            self.assertEqual(b.get(b.counts+150,2),count)
        b=self.bench();b.put(b.counts+76,1,2);self.refusal(b,b.create)
    def test_retired_count_admission_preserves_index_alias_and_null_template_guards(self):
        for target,value,width in ((BASE+662+75,29,1),(BASE+662+75,3,1),(BASE+662+75,2,1),(BASE+340+4,1,2),(BASE+662+2,28,1)):
            b=self.bench();b.put(b.counts+150,1,2);b.put(target,value,width)
            self.refusal(b,b.create)

    def test_odd_native_used_size_refuses_free_without_retiring_owner(self):
        b=self.bench();self.assertEqual(b.create(),1);p=b.alloc(8);self.assertTrue(p)
        b.put(p-28,b.get(p-28)+1)
        self.refusal(b,lambda:b.free(p))
