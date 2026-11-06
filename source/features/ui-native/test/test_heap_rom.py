"""Class B PREPARED heap fixture; actual NNS constructor/registry/IRQ bodies.

Reads pinned canonical V4 ARM9 in RAM. No ROM/runtime copy or extracted asset.
This is a bounded synthetic caller heap, not the game's boot/lifecycle state.
"""
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from heap_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
ROM_PINS={'EN':(147345256,'179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
          'IT':(153228136,'2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156')}
PINS=((0x0201a7bc,0x12c,'cc68fc1435164ec9c5fee447e77fb660b9484465acd62d3a4d066b6ad5eaeeb1'),
      (0x020b4b68,0xa04,'9ca5403ea234f9f55995715b50776892dd5170ba180537ffc1351c76ac197120'),
      (0x020b4dd0,0x79c,'2fb45f2e28538167e936e5cc6e89326c12d4ec7a937f98750278d5c26006da7c'),
      (DISABLE,0x30,'8799c41ae2d67d6eb1339acba651c4cf9fb8a06ceae96794f5f1a7cd0256c552'),
      (0x0201a910,0x2dc,'5656bcdf13e3fb2a4483fea2412160fa4a7a815e445d2de22226b8cff7edf433'),
      (0x0201a8e8,0x304,'5d508dad995159bdd6138386ec2a5417e42ee5ea76b6ba42cdd5155128eb1285'),
      (0x020d3a9c,12,'0528e878357410ab14fe859cfd2b9c50d32a6916d00f23c08e44f3882139c53a'))
class NativeHeapBench(HeapBench):
    def __init__(self,compiled,sections):
        super().__init__(compiled)
        for p,data in sections:self.u.mem_write(p,data)
        self.u.mem_write(CODE,self.code);self.native=True
        self.u.mem_write(0x021d84b0,bytes(16))
        for slot,(raw,size) in enumerate(TEMPLATES):
            self.put(self.handles+4*slot,self.address(CREATE,raw,size,0))
            assert self.get(self.handles+4*slot)==(0 if slot==2 else raw)
        self.put(self.handles+12,0)
        assert self.address(CREATE,PARENT,0x100000,0)==PARENT
        self.put(self.handles+12,PARENT)
    def native_allowed(self,p):return super().native_allowed(p) or 0x0201ab0c<=p<0x0201ab80
    def totals(self):
        node=self.get(PARENT+0x24);total=largest=count=0;seen=set()
        while node:
            assert node not in seen and len(seen)<4096,'finite free list';seen.add(node)
            assert PARENT+0x38<=node<=PARENT+0x100000-16
            n=self.get(node+4);assert node+16+n<=PARENT+0x100000
            total+=n;largest=max(largest,n);count+=1;node=self.get(node+12)
        return total,largest,count
    def registry(self):return bytes(self.u.mem_read(0x021d84b0,16)),bytes(self.u.mem_read(PARENT+4,20))
class NativeRetiredHeapBench(NativeHeapBench):
    """Isolated successful native Create/Alloc/Destroy control; no failure seam."""
    def __init__(self,*args):
        self.control=False
        super().__init__(*args)
        from module_bench import instruction_set
        self.fetch=instruction_set(self.u,[CREATE,ALLOC,FREE,DESTROY,DISABLE,RESTORE,0x020b4e4c,
            0x0201a911,0x0201aa8d,0x0201a9c5,0x020d3a9c],[(a,a+n) for a,n,d in PINS])
    def native_allowed(self,p):
        return p in self.fetch if hasattr(self,'fetch') else super().native_allowed(p)
    def hook(self,u,p,n,data):
        if 0x0201a8e8<=p<0x0201abec:
            assert self.control and p in self.fetch and not 0x0201aa7c<=p<0x0201aa8c,'native control only, never AllocFail'
            self.instructions+=1;sp=u.reg_read(UC_ARM_REG_SP);self.low=min(self.low,sp)
            if self.active_service and p==self.active_service[1]:self.active_service=None
            assert STACK-1024<=sp<=STACK
            return
        return super().hook(u,p,n,data)
    def control_call(self,address,*args):
        self.control=True
        try:return self.address(address,*args)
        finally:self.control=False

class HeapRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        paths={l:Path(os.environ.get('SGP_UI_HEAP_'+l,str(canonical/f'candidate-v4-{l}.nds'))) for l in ROM_PINS}
        missing=[l for l,p in paths.items() if not p.is_file()]
        if missing:
            message='canonical V4 heap native inputs missing: '+','.join(missing)
            if os.environ.get('SGP_UI_HEAP_REQUIRE_INPUTS')=='1':raise AssertionError(message)
            raise unittest.SkipTest(message)
        import ndspy.rom
        cls.sections={}
        for lang,p in paths.items():
            digest=hashlib.sha256()
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
            assert (p.stat().st_size,digest.hexdigest())==ROM_PINS[lang],f'V4 {lang} identity'
            rom=ndspy.rom.NintendoDSRom.fromFile(p);ss=ndspy_load_arm9_sicuro(rom).sections
            for a,n,want in PINS:
                s=next(s for s in ss if s.ramAddress<=a<a+n<=s.ramAddress+len(s.data))
                assert hashlib.sha256(bytes(s.data[a-s.ramAddress:a-s.ramAddress+n])).hexdigest()==want,f'{lang} native pin {a:08x}'
            cls.sections[lang]=[(s.ramAddress,bytes(s.data)) for s in ss if 0x02000000<=s.ramAddress<0x02400000]
            del rom,ss
        cls.temp=tempfile.TemporaryDirectory(prefix='heap-b-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_heap(Path(cls.temp.name))
    def benches(self):
        for l,s in self.sections.items():yield NativeHeapBench(self.compiled,s)
    def test_actual_nns_both_backings_head_tail_wrapper_and_parent_registry_restore(self):
        for b in self.benches():
            for n in (0x30000,0x40000):
                before=b.totals(),b.registry(),b.get(b.counts+6,2)
                self.assertEqual(b.create(n),1)
                p,q=b.alloc(79),b.alloc(97,1);self.assertTrue(p and q and p<q)
                self.assertEqual(b.get(p-4,1),38);self.assertEqual(b.get(q-4,1),38)
                self.assertEqual(b.get(p-32,2),0x5544)
                self.assertEqual(b.free(p),1);self.assertEqual(b.free(q),1);self.assertEqual(b.destroy(),1)
                self.assertEqual((b.totals(),b.registry(),b.get(b.counts+6,2)),before)
    def test_actual_native_exhaustion_fragmentation_and_nested_unwind(self):
        for b in self.benches():
            before=b.totals(),b.registry()
            blocks=[b.address(ALLOC,PARENT,0x20000,4) for _ in range(7)]
            self.assertTrue(all(blocks))
            for n in (0x30000,0x40000):self.assertEqual(b.create(n),0)
            for p in blocks[1::2]:b.address(FREE,PARENT,p)
            self.assertGreater(b.totals()[0],0x40000);self.assertLess(b.totals()[1],0x30000)
            for n in (0x30000,0x40000):self.assertEqual(b.create(n),0)
            for p in blocks[::2]:b.address(FREE,PARENT,p)
            self.assertEqual((b.totals(),b.registry()),before)
            self.assertEqual(b.create(),1);p=b.alloc(0x2f000);self.assertTrue(p)
            old=b.token(),b.metadata();self.assertEqual(b.alloc(0x2000),0);self.assertEqual((b.token(),b.metadata()),old)
            b.free(p);b.destroy();self.assertEqual((b.totals(),b.registry()),before)
    def test_actual_constructor_small_extent_refuses_and_seamed_null_unwinds(self):
        for b in self.benches():
            before=b.totals(),b.registry();self.assertEqual(b.address(CREATE,PARENT+0x100,0x48,0),0)
            self.assertEqual((b.totals(),b.registry()),before)
            for n in (0x30000,0x40000):
                b.fail=CREATE;b.u.mem_write(TOKEN,b'\x5a'*92);old=b.token(),b.metadata()
                self.assertEqual(b.create(n),0);self.assertEqual((b.token(),b.metadata()),old)
                self.assertEqual((b.totals(),b.registry()),before)
    def test_actual_irq_mask_and_ime_all_lifecycle_paths(self):
        for b in self.benches():
            for mask in (0,128):
                for ime in (0,1):
                    b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
                    self.assertEqual(b.create(),1);start=len(b.store_contexts);p=b.alloc(21,1)
                    payload=[c for c in b.store_contexts[start:] if p<=c[0]<p+21]
                    self.assertTrue(payload)
                    self.assertTrue(all(c[4]&128==mask for c in payload),'zero payload after IRQ restoration')
                    self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
    def test_actual_native_heap_free_accepts_wrapper_with_explicit_probe_ledger_retirement(self):
        for b in self.benches():
            before=b.totals(),b.registry();self.assertEqual(b.create(),1);p=b.alloc(49)
            b.address(0x0201ab0d,p)
            self.assertEqual(b.get(b.counts+76,2),0)
            # Test-only retirement following an external ABI probe; production
            # permits only checked free and never silently retires stale entries.
            b.put(TOKEN+28,0);self.assertEqual(b.destroy(),1)
            self.assertEqual((b.totals(),b.registry()),before)
    def test_semantic_native_assertions_kill_five_omission_mutants(self):
        mutants=(
            ('wrapper[3]=38;','wrapper[3]=0;','heapID'),
            ('++HINFO->counts[38];','/* omitted count */','count'),
            ('HDESTROY((void *)t->handle);HFREE((void *)t->parent,(void *)t->raw);','HDESTROY((void *)t->handle);','parentfree'),
            ('HRESTORE(irq);return ok;','(void)irq;return ok;','IRQrestore'),
            ('HWord *wrapper=(HWord *)raw;','HWord *wrapper=(HWord *)(raw-16);','GFheader'))
        for old,new,label in mutants:
            with tempfile.TemporaryDirectory(prefix='heap-mutant-') as directory:
                compiled=compile_heap(Path(directory),(old,new))
                for lang,sections in self.sections.items():
                    with self.subTest(mutation=label,lang=lang):
                        b=NativeHeapBench(compiled,sections);before=b.totals(),b.registry()
                        def semantic_scenario():
                            self.assertEqual(b.create(),1)
                            p=b.alloc(31);self.assertTrue(p)
                            self.assertEqual(b.get(p-4,1),38,'heapID semantic')
                            self.assertEqual(b.get(b.counts+76,2),1,'count semantic')
                            self.assertEqual(b.get(p-32,2),0x5544,'separate native header')
                            self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
                            self.assertEqual((b.totals(),b.registry()),before,'parent free semantic')
                        with self.assertRaises(AssertionError):semantic_scenario()
    def test_actual_native_tracked_capacity_allocation_faults_and_refusals(self):
        for b in self.benches():
            before=b.totals(),b.registry();self.assertEqual(b.create(),1)
            ps=[]
            for k in range(16):
                b.fail=ALLOC;old=b.token(),b.metadata();self.assertEqual(b.alloc(8),0)
                self.assertEqual((b.token(),b.metadata()),old);b.fail=None
                ps.append(b.alloc(8,k%2));self.assertTrue(ps[-1])
            for n in (0,0xffffffff,8):
                start=len(b.calls);old=b.token(),b.metadata();self.assertEqual(b.alloc(n),0)
                self.assertEqual((b.token(),b.metadata()),old)
                self.assertFalse(any(p==ALLOC for p,a in b.calls[start:]))
            self.assertEqual(b.destroy(),0)
            for p in reversed(ps):self.assertEqual(b.free(p),1);self.assertEqual(b.free(p),0)
            self.assertEqual(b.destroy(),1);self.assertEqual(b.destroy(),0)
            self.assertEqual((b.totals(),b.registry()),before)
    def test_actual_native_count_and_stale_topology_preserve_owners(self):
        for b in self.benches():
            before=b.totals(),b.registry();self.assertEqual(b.create(),1)
            b.put(b.counts+76,65535,2);old=b.token(),b.metadata();start=len(b.calls)
            self.assertEqual(b.alloc(8),0);self.assertEqual((b.token(),b.metadata()),old)
            self.assertFalse(any(p==ALLOC for p,a in b.calls[start:]));b.put(b.counts+76,0,2)
            b.put(b.parents+16,PARENT+4);old=b.token(),b.metadata();self.assertEqual(b.destroy(),0)
            self.assertEqual((b.token(),b.metadata()),old);b.put(b.parents+16,PARENT)
            self.assertEqual(b.destroy(),1);self.assertEqual((b.totals(),b.registry()),before)


    def test_actual_native_well_formed_full_slots_refuse_before_allocation(self):
        for b in self.benches():
            before=b.totals(),b.registry();children=[]
            for slot in range(4,28):
                raw=b.address(ALLOC,PARENT,0x200,4);self.assertTrue(raw)
                self.assertEqual(b.address(CREATE,raw,0x200,0),raw);children.append(raw)
                b.put(b.handles+4*slot,raw);b.put(b.parents+4*slot,PARENT)
                b.put(b.raws+4*slot,raw);b.put(b.idxs+slot,slot,1)
            old=b.token(),b.metadata();start=len(b.calls)
            self.assertEqual(b.create(),0);self.assertEqual((b.token(),b.metadata()),old)
            self.assertFalse(any(p in (ALLOC,CREATE) for p,a in b.calls[start:]))
            for slot,raw in reversed(list(zip(range(4,28),children))):
                b.address(DESTROY,raw);b.address(FREE,PARENT,raw)
                b.put(b.handles+4*slot,0);b.put(b.parents+4*slot,0)
                b.put(b.raws+4*slot,0);b.put(b.idxs+slot,28,1)
            self.assertEqual((b.totals(),b.registry()),before)

    def test_actual_move_stack_to_app_back_before_free_and_destroy(self):
        for b in self.benches():
            before=b.totals(),b.registry();self.assertEqual(b.create(),1)
            app=b.alloc(256);self.assertTrue(app)
            b.u.mem_write(app,b.token());b.u.mem_write(TOKEN,bytes(92))
            self.assertEqual(b.alloc(8),0)
            q=b.call('ui_alloc38',app,32,0);self.assertTrue(q)
            self.assertEqual(b.call('ui_free38',app,q),1)
            old=bytes(b.u.mem_read(app,92)),b.metadata()
            self.assertEqual(b.call('ui_free38',app,app),0)
            self.assertEqual((bytes(b.u.mem_read(app,92)),b.metadata()),old)
            b.u.mem_write(TOKEN,bytes(b.u.mem_read(app,92)))
            b.u.mem_write(app,bytes(92))
            self.assertEqual(b.free(app),1);self.assertEqual(b.destroy(),1)
            self.assertEqual((b.totals(),b.registry()),before)

    def test_actual_native_template2_null_handle_allows_both_backing_lifecycles(self):
        for lang,sections in self.sections.items():
            for n in (0x30000,0x40000):
                with self.subTest(lang=lang,backing=n):
                    b=NativeHeapBench(self.compiled,sections)
                    self.assertEqual(tuple(b.get(b.idxs+j,1) for j in range(4)),(0,1,2,3))
                    before=b.totals(),b.registry(),b.get(b.counts+6,2)
                    self.assertEqual(b.create(n),1)
                    p=b.alloc(21);self.assertTrue(p)
                    self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
                    self.assertEqual((b.totals(),b.registry(),b.get(b.counts+6,2)),before)
                    self.assertEqual((b.get(b.idxs+2,1),b.get(b.handles+8),b.get(b.counts+4,2)),(2,0,0))

    def test_actual_only_template2_null_zero_count_mapping_is_admitted(self):
        for lang,sections in self.sections.items():
            for n in (0x30000,0x40000):
                for target,value,width in ((BASE+662+4,5,1),(BASE+662+2,28,1),(BASE+340+4,1,2),(BASE+662+4,2,1),(BASE+662,28,1)):
                    with self.subTest(lang=lang,backing=n,target=target,value=value):
                        b=NativeHeapBench(self.compiled,sections)
                        before=b.totals(),b.registry();original=b.get(target,width)
                        b.put(target,value,width);old=b.token(),b.metadata();calls,writes=len(b.calls),len(b.writes)
                        self.assertEqual(b.create(n),0);self.assertEqual((b.token(),b.metadata()),old)
                        self.assertEqual((b.totals(),b.registry()),before)
                        self.assertTrue(all(p in (DISABLE,RESTORE) for p,a in b.calls[calls:]))
                        self.assertTrue(all(STACK-1024<=p<p+size<=STACK for p,size,v in b.writes[writes:]))
                        b.put(target,original,width);self.assertEqual(b.create(n),1);p=b.alloc(21)
                        b.put(target,value,width);old=b.token(),b.metadata();calls,writes=len(b.calls),len(b.writes)
                        self.assertEqual(b.alloc(8),0);self.assertEqual(b.free(p),0);self.assertEqual(b.destroy(),0)
                        self.assertEqual((b.token(),b.metadata()),old)
                        self.assertTrue(all(p in (DISABLE,RESTORE) for p,a in b.calls[calls:]))
                        self.assertTrue(all(STACK-1024<=p<p+size<=STACK for p,size,v in b.writes[writes:]))
                        b.put(target,original,width);self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
                        self.assertEqual((b.totals(),b.registry()),before)

    def test_native_destroy_retains_count_for_unallocated75_without_blocking38(self):
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                b=NativeRetiredHeapBench(self.compiled,sections);before=b.totals(),b.registry()
                self.assertEqual(b.control_call(0x0201a911,3,75,0x4000),1)
                slot=b.get(b.idxs+75,1);self.assertGreaterEqual(slot,4);self.assertLess(slot,28)
                self.assertTrue(b.control_call(0x0201aa8d,75,64));self.assertEqual(b.get(b.counts+150,2),1)
                b.control_call(0x0201a9c5,75)
                self.assertEqual((b.get(b.idxs+75,1),b.get(b.counts+150,2)),(28,1))
                self.assertEqual(tuple(b.get(table+slot*4) for table in (b.handles,b.parents,b.raws)),(0,0,0))
                self.assertEqual((b.totals(),b.registry()),before)
                self.assertEqual(b.create(),1);p=b.alloc(25);self.assertTrue(p)
                self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)
                self.assertEqual((b.get(b.idxs+75,1),b.get(b.counts+150,2)),(28,1))
                self.assertEqual((b.totals(),b.registry()),before)

    def test_actual_odd_native_used_size_refuses_free_without_native_mutation(self):
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                b=NativeHeapBench(self.compiled,sections);self.assertEqual(b.create(),1)
                p=b.alloc(8);self.assertTrue(p);size=b.get(p-28);b.put(p-28,size+1)
                old=b.token(),b.metadata(),bytes(b.u.mem_read(PARENT,0x100000));calls=len(b.calls)
                self.assertEqual(b.free(p),0)
                self.assertEqual((b.token(),b.metadata(),bytes(b.u.mem_read(PARENT,0x100000))),old)
                self.assertFalse(any(a==FREE for a,args in b.calls[calls:]))
                b.put(p-28,size);self.assertEqual(b.free(p),1);self.assertEqual(b.destroy(),1)

if __name__=='__main__':
    # Reproduce observed maxima across the complete focused Class B suite.
    import json
    observed=[]
    original=NativeHeapBench.__init__
    def recorded(self,*args):
        original(self,*args)
        if args[0][0]==HeapRomTests.compiled[0]:observed.append(self)
    NativeHeapBench.__init__=recorded
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(HeapRomTests))
    if not result.wasSuccessful():raise SystemExit(1)
    by_service={}
    for b in observed:
        for address,instructions,stack in b.native_metrics:
            key=f'{address:08x}';old=by_service.setdefault(key,[0,0,0])
            old[0]+=1;old[1]=max(old[1],instructions);old[2]=max(old[2],stack)
    print(json.dumps({'prepared_native_benches':len(observed),
                     'max_combined_stack':max(stack for b in observed for address,stack,n in b.metrics),
                     'max_call_instructions':max(n for b in observed for address,stack,n in b.metrics),
                     'native_service_count_maxinstructions_maxstack':by_service},indent=2))
