"""Class A tests: checked ownership, wrapper ABI, admissions and MOVE."""
import tempfile,unittest
from pathlib import Path
from persistent_bench import *
class PersistentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='persistent-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_persistent(Path(cls.temp.name))
    def bench(self):return PersistentBench(self.compiled)
    def test_alloc_zeroes_payload_uses_id11_count_and_releases_once(self):
        b=self.bench();p=b.alloc(5001);self.assertTrue(p)
        self.assertEqual(p%4,0);self.assertEqual(b.get(p-32,2),0x5544)
        self.assertEqual(bytes(b.u.mem_read(p-16,16)),bytes(12)+b'\x0b\0\0\0')
        self.assertEqual(bytes(b.u.mem_read(p,5004)),bytes(5004))
        self.assertEqual((b.get(b.counts+22,2),b.get(b.counts+b.slot*2,2)),(1,0))
        old=b.snapshot();self.assertEqual(b.alloc(),0);self.assertEqual(b.snapshot(),old)
        self.assertEqual(b.free(),RELEASED);self.assertEqual(b.get(b.counts+22,2),0)
        old=b.snapshot();self.assertEqual(b.free(),REFUSED);self.assertEqual(b.snapshot(),old)
    def test_explicit_move_transfers_self_and_must_exit_root_before_free(self):
        b=self.bench();p=b.alloc();self.assertTrue(p)
        self.assertEqual(b.move(p),RELEASED);self.assertEqual(b.token(),bytes(SIZE))
        old=b.snapshot();self.assertEqual(b.free(t=p),HOLD);self.assertEqual(b.snapshot(),old)
        self.assertEqual(b.move(TOKEN,p),RELEASED);self.assertEqual(b.token(p),bytes(SIZE))
        self.assertEqual(b.free(),RELEASED)
    def test_copy_wrong_generation_and_alias_moves_refuse_without_writes(self):
        b=self.bench();p=b.alloc();self.assertTrue(p);other=TOKEN+128;b.allowed.append((other,other+SIZE))
        b.u.mem_write(other,b.token());old=b.snapshot()
        self.assertEqual(b.free(t=other),REFUSED);self.assertEqual(b.free(g=2),REFUSED)
        for dst in (TOKEN,TOKEN+4,p-32,p-28,p-16,p-4,b.heap,BASE):
            self.assertEqual(b.move(dst),REFUSED)
        self.assertEqual(b.snapshot(),old)
    def test_sizes_generations_count_irq_and_ime_refuse_before_native_alloc(self):
        for n,g in ((0,1),(0x4001,1),(0xffffffff,1),(5000,0)):
            b=self.bench();old=b.snapshot();self.assertEqual(b.alloc(n,g),0);self.assertEqual(b.snapshot(),old)
            self.assertFalse(any(a==ALLOC for a,args in b.calls))
        for mask,ime in ((128,1),(0,0),(128,0)):
            b=self.bench();b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
            old=b.snapshot();self.assertEqual(b.alloc(),0);self.assertEqual(b.snapshot(),old)
        b=self.bench();b.put(b.counts+22,65535,2);old=b.snapshot()
        self.assertEqual(b.alloc(),0);self.assertEqual(b.snapshot(),old)
    def test_native_null_preserves_owner_count_and_heap(self):
        b=self.bench();b.fail=ALLOC;old=b.snapshot()
        self.assertEqual(b.alloc(),0);self.assertEqual(b.snapshot(),old)
    def test_uncertain_header_topology_or_count_holds_owned_root(self):
        for where,value,width in ((-32,0,2),(-28,0xffffffff,4),(-28,5017,4),(-4,38,4)):
            b=self.bench();p=b.alloc();self.assertTrue(p);b.put(p+where,value,width);old=b.snapshot()
            self.assertEqual(b.free(),HOLD);self.assertEqual(b.snapshot(),old)
        for target,value,width in ((BASE+662+11,7,1),(BASE+340+22,0,2),(BASE+116+24,PARENT+4,4)):
            b=self.bench();self.assertTrue(b.alloc());b.put(target,value,width);old=b.snapshot()
            self.assertEqual(b.free(),HOLD);self.assertEqual(b.snapshot(),old)
    def test_released_record_rejects_reused_generation_and_accepts_fresh(self):
        b=self.bench();self.assertTrue(b.alloc());self.assertEqual(b.free(),RELEASED)
        old=b.snapshot();self.assertEqual(b.alloc(g=1),0);self.assertEqual(b.snapshot(),old)
        self.assertTrue(b.alloc(g=2));self.assertEqual(b.free(g=2),RELEASED)
    def test_uncertain_native_return_remains_held_even_when_user_pointer_wraps(self):
        # Fault injection at the lower boundary: immutable native code is not
        # expected to produce this. The retained owner must still be observable.
        for returned in (0xfffffff0,0x02200000):
            b=self.bench()
            # Explicit lower boundary return fault; production C is unchanged.
            b.return_fault=returned
            old=b.metadata();self.assertEqual(b.alloc(),0)
            self.assertNotEqual(b.token(),bytes(SIZE));self.assertEqual(b.metadata(),old)
            self.assertEqual(b.free(),HOLD);self.assertEqual(b.move(TOKEN+128),HOLD);old=b.token()
            self.assertEqual(b.alloc(g=2),0);self.assertEqual(b.token(),old)
    def test_return_whose_full_extent_intersects_native_child_header_is_held(self):
        b=self.bench();child=b.heap+0x2000;b.header(child,0x200)
        b.put(b.handles+28,child);b.put(b.parents+28,b.heap);b.put(b.raws+28,child);b.put(b.idxs+12,7,1)
        b.put(child-32,0x5544,2);b.put(child-28,32);b.return_fault=child-16
        old=b.metadata(),bytes(b.u.mem_read(b.heap,HEAP11_BYTES))
        self.assertEqual(b.alloc(16),0)
        self.assertEqual((b.metadata(),bytes(b.u.mem_read(b.heap,HEAP11_BYTES))),old)
        self.assertEqual(b.free(),HOLD)
class PersistentBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='persistent-bootstrap-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.directory=Path(cls.temp.name)
        cls.default=compile_persistent(cls.directory)
        cls.configured=compile_persistent(cls.directory,resident=0x023d7b20)
    def test_configured_exact_resident_slot_allocates_and_releases(self):
        # Missing/widened configured predicate loses the durable owner or
        # grants a neighboring address; existing heap38 admission stays bounded.
        b=PersistentBench(self.configured,token=0x023d7b20)
        self.assertTrue(b.alloc());self.assertEqual(b.free(),RELEASED)
        old=b.snapshot();self.assertEqual(b.call('ui_heap38_create',0x023d7b20,0x30000,1),0)
        self.assertEqual(b.snapshot(),old)
    def test_standalone_composition_runs_without_heap38_bodies(self):
        try:compiled=compile_persistent(self.directory,full_heap=False)
        except subprocess.CalledProcessError as e:self.fail('standalone persistent must compile: '+e.stderr.decode())
        self.assertFalse({'ui_heap38_create','ui_alloc38','ui_free38','ui_heap38_destroy'}&compiled[1].keys())
        b=PersistentBench(compiled);self.assertTrue(b.alloc());self.assertEqual(b.free(),RELEASED)
    def test_default_reserved_and_configured_neighbors_refuse_before_native_calls(self):
        for compiled,addresses in ((self.default,(0x023d7b20,)),(self.configured,(
            0x0226ec3c,0x023bffe0,0x023c0000,0x027e377c,0x023d7afc,0x023d7b00,0x023d7b10,0x023d7b1c,0x023d7b21,0x023d7b24,
            0x023d7b44,0x023d7b48,0x023d7b58,0x023d7b60,0x023d7c40,0x023d7e00))):
            for address in addresses:
                with self.subTest(address=hex(address)):
                    b=PersistentBench(compiled,token=address);old=b.snapshot()
                    self.assertEqual(b.alloc(),0);self.assertEqual(b.free(),REFUSED)
                    self.assertEqual(b.move(TOKEN),REFUSED)
                    self.assertEqual(b.snapshot(),old);self.assertFalse(b.calls)
    def test_configured_resident_copy_and_island_neighbors_are_not_authoritative(self):
        b=PersistentBench(self.configured,token=0x023d7b20);self.assertTrue(b.alloc())
        for address in (0x023d7b48,0x023d7b60,0x023d7c00):
            b.u.mem_write(address,b.token());old=b.snapshot();copy=bytes(b.u.mem_read(address,40))
            self.assertEqual(b.free(t=address),REFUSED);self.assertEqual(b.move(TOKEN,address),REFUSED)
            self.assertEqual(b.snapshot(),old);self.assertEqual(bytes(b.u.mem_read(address,40)),copy)
        self.assertEqual(b.free(),RELEASED)
    def test_standalone_module_composition_has_no_heap38_exports(self):
        with tempfile.TemporaryDirectory(prefix='persistent-module-a-') as d:
            receipt=build_receipt(Path(d),full_heap=False,resident=0x023d7b20,module=True)
            self.assertFalse(receipt['undefined']);self.assertFalse(receipt['mutable_sections'])
            self.assertTrue(set(receipt['relocations'])<={2,10})
            compiled=compile_persistent(Path(d),full_heap=False,resident=0x023d7b20,
                prefix=(SOURCE/'features/ui-native/module.c').read_text())
            self.assertTrue({'ui_module_begin','ui_persistent_alloc'}<=compiled[1].keys())
            self.assertFalse({'ui_heap38_create','ui_alloc38','ui_free38','ui_heap38_destroy'}&compiled[1].keys())
    def test_wrong_unaligned_outside_and_unknown_configuration_do_not_compile(self):
        for value in ('0x023d7b1c','0x023d7b21','0x023d7b48','0x027e3000','0x02270000','UNKNOWN_SLOT'):
            with self.subTest(value=value):
                with self.assertRaises(subprocess.CalledProcessError):
                    compile_persistent(self.directory,resident=value)
    def test_configured_null_and_hold_survive_stack_overwrite_and_callback_returns(self):
        for returned in (None,0xfffffff0,0x02200000):
            b=PersistentBench(self.configured,token=0x023d7b20)
            if returned is None:b.fail=ALLOC
            else:b.return_fault=returned
            old=b.snapshot();self.assertEqual(b.alloc(),0)
            held=b.token();self.assertEqual(b.metadata(),old[1])
            self.assertEqual(held==old[0],returned is None)
            if returned is not None:self.assertEqual(b.get(0x023d7b20),0x48504955)
            b.u.mem_write(STACK-960,b'\x6c'*960)
            for _ in range(4):
                self.assertEqual(b.free(),REFUSED if returned is None else HOLD)
                self.assertEqual(b.move(TOKEN),REFUSED if returned is None else HOLD)
                self.assertEqual(b.alloc(g=2),0);self.assertEqual(b.token(),held)
            self.assertFalse(any(a in (FREE,DESTROY) for a,args in b.calls))
if __name__=='__main__':unittest.main()
