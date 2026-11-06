"""Class A: compiled owner transitions with explicit lower native service seams."""
import tempfile,unittest
from module_bench import *
class ModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='module-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_module(Path(cls.temp.name))
    def bench(self,size=0x400):return ModuleBench(self.compiled,size)
    def test_crc_pump_matches_single_steps_and_yields_on_pending_or_masked_calls(self):
        self.assertIn('ui_module_pump',self.compiled[1])
        results=[]
        for cap in (1,4):
            b=self.bench(0x8000);b.init();b.begin();count=0
            while True:
                count+=1;r=b.call('ui_module_pump',STATE,1,1,4096,cap)
                if r!=MORE:break
                self.assertLess(count,100)
            self.assertEqual(r,READY)
            results.append((count,b.state(),b.calls,bytes(b.u.mem_read(IMAGE,len(b.raw)))))
        self.assertLess(results[1][0],results[0][0]);self.assertEqual(results[0][1:],results[1][1:])
        b=self.bench();b.init();b.begin();b.delay=True
        while b.phase!=META_WAIT:self.assertEqual(b.step(),MORE)
        before=b.state();self.assertEqual(b.call('ui_module_pump',STATE,1,1,4096,4),MORE)
        self.assertEqual(b.state(),before);self.assertLess(b.metrics[-1][2],2000)
        b.put(IME,0);self.assertEqual(b.call('ui_module_pump',STATE,1,1,4096,4),MORE)
        self.assertEqual(b.state(),before);self.assertLess(b.metrics[-1][2],200)
    def test_pump_invalid_arguments_leave_live_owner_unchanged(self):
        b=self.bench();b.init();b.begin()
        for role,generation,budget,cap in ((0,1,4096,4),(1,2,4096,4),(1,1,0,4),
                                            (1,1,4097,4),(1,1,4096,0),(1,1,4096,17)):
            before=b.state(),list(b.calls)
            self.assertEqual(b.call('ui_module_pump',STATE,role,generation,budget,cap),REFUSED)
            self.assertEqual((b.state(),b.calls),before)
    def test_entry_pump_batches_setup_but_yields_on_submission_and_lifecycle_boundaries(self):
        b=self.bench(0x8000);b.init();b.begin();b.delay=True
        self.assertEqual(b.call('ui_module_pump',STATE,1,1,4096,16),MORE)
        self.assertEqual(b.phase,META_WAIT,'submit metadata in one bounded callback')
        self.assertFalse(any(row[0]==CLOSE for row in b.calls))
        b.complete();b.delay=False
        self.assertEqual(b.call('ui_module_pump',STATE,1,1,4096,16),MORE)
        self.assertEqual(b.phase,RESERVE,'yield before registry ownership changes')
        self.assertEqual(b.call('ui_module_pump',STATE,1,1,4096,16),MORE)
        self.assertEqual(b.phase,IMAGE_OPEN,'reserve only, no second lifecycle operation')
        while b.phase!=START:self.assertEqual(b.call('ui_module_pump',STATE,1,1,4096,16),MORE)
        self.assertEqual(b.call('ui_module_pump',STATE,1,1,4096,16),MORE)
        self.assertEqual(b.phase,DECODED_VERIFY,'decompression ends this callback')
    def test_zero_identity_release_keeps_fresh_owner_untouched(self):
        b=self.bench();self.assertEqual(b.init(),1);before=b.state()
        self.assertEqual(b.release(0,0),REFUSED);self.assertEqual(b.state(),before)
    def test_begin_returns_owned_pending_before_any_dynamic_entry(self):
        b=self.bench();self.assertEqual(b.init(),1)
        self.assertEqual(b.begin(),MORE);self.assertEqual(b.check(),0)
        self.assertEqual(b.get(REGISTRY+4),0)
    def test_owned_success_release_and_no_duplicate_end(self):
        b=self.bench();b.init();self.assertEqual(b.open(),READY)
        for i,want in enumerate((IMAGE+1,IMAGE+5,IMAGE+9)):self.assertEqual(b.check(selector=i),want)
        self.assertEqual(b.cancel(),REFUSED);self.assertEqual(b.close(),RELEASED)
        before=b.state();self.assertEqual(b.release(),REFUSED);self.assertEqual(b.state(),before);self.assertEqual(b.check(),0)
        for p in (STARTFN,WIFIFN,END):self.assertEqual(sum(c[0]==p for c in b.calls),1)
        self.assertEqual(b.get(REGISTRY+4),0)
    def test_irq_deferral_and_invalid_identity_do_not_mutate(self):
        b=self.bench();b.init()
        for mask,ime in ((128,1),(0,0),(128,0)):
            before=b.state();b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
            self.assertEqual(b.begin(),MORE);self.assertEqual(b.state(),before);self.assertFalse(b.calls)
        b.u.reg_write(UC_ARM_REG_CPSR,0x5f);b.put(IME,1);b.begin();before=b.state()
        for role,gen in ((0,0),(2,1),(1,0),(1,2)):
            self.assertEqual(b.step(role,gen),REFUSED);self.assertEqual(b.cancel(role,gen),REFUSED);self.assertEqual(b.release(role,gen),REFUSED);self.assertEqual(b.state(),before)
        for budget in (0,4097,0xffffffff):self.assertEqual(b.step(budget=budget),REFUSED);self.assertEqual(b.state(),before)
    def test_invalid_configs_aliases_and_abi1_refuse_unchanged(self):
        bad={0:0,1:1,2:0,3:0,4:53,5:55,6:IMAGE+4,7:0xffffffff,8:4,9:IMAGE-4,10:IMAGE+0x404,11:0,13:0,14:0x401,15:5,18:0xffffffff,19:32,20:0x10000001,21:0,22:0xffffffff,23:128}
        for word,value in bad.items():
            b=self.bench();b.init();before=b.state();b.put(CONFIG+4*word,value)
            self.assertEqual(b.begin(),REFUSED,(word,value));self.assertEqual(b.state(),before);self.assertFalse(b.calls)
        b=self.bench();b.init();before=b.state()
        for p in (STATE,CONFIG+1,IMAGE,0xffffffff):self.assertEqual(b.call('ui_module_begin',STATE,p,1,1),REFUSED);self.assertEqual(b.state(),before)
    def test_persistent_metadata_read_and_close_retry_prevent_reuse(self):
        b=self.bench();b.init();b.delay=True;b.begin()
        while b.phase!=META_WAIT:self.assertEqual(b.step(),MORE)
        self.assertEqual(b.get(ARC+36),b.file);self.assertEqual(b.get(b.file+48),b.table)
        for _ in range(5):
            b.poison_stack();self.assertEqual(b.step(),MORE);self.assertEqual(b.get(ARC+36),b.file);self.assertEqual(b.check(),0)
        b.complete();b.close_failures=5
        while b.phase!=META_CLOSE:self.assertEqual(b.step(),MORE)
        for _ in range(5):
            self.assertEqual(b.step(),MORE);self.assertEqual(b.get(b.file+8),ARC);self.assertEqual(b.get(REGISTRY+4),0)
        self.assertEqual(b.step(),MORE);self.assertEqual(b.get(b.file+8),0)
        b.delay=False;self.assertEqual(b.drive(),READY)
    def test_cancel_pending_drains_then_same_file_closes_without_start(self):
        for target in (META_WAIT,IMAGE_WAIT):
            b=self.bench();b.init();b.begin()
            while b.phase!=target:
                if b.phase in (META_READ,IMAGE_READ):b.delay=b.phase==(META_READ if target==META_WAIT else IMAGE_READ)
                self.assertEqual(b.step(),MORE)
            self.assertEqual(b.cancel(),MORE);b.poison_stack()
            for _ in range(8):self.assertEqual(b.step(),MORE);self.assertEqual(b.get(ARC+36),b.file)
            b.complete();b.close_failures=4;self.assertEqual(b.drive(),FAILED)
            self.assertEqual(b.get(b.file+8),0);self.assertEqual(b.get(REGISTRY+4),0)
            self.assertFalse(any(c[0] in (STARTFN,WIFIFN,END) for c in b.calls));self.assertEqual(b.close(),RELEASED)
    def test_corrupt_packed_bytes_refuse_before_decompress(self):
        b=self.bench();b.init();b.begin()
        while b.phase!=PACKED_VERIFY:self.assertEqual(b.step(),MORE)
        b.put(IMAGE+len(b.encoded)-1,b.get(IMAGE+len(b.encoded)-1,1)^1,1)
        self.assertEqual(b.drive(),FAILED);self.assertEqual(b.get(REGISTRY+4),0)
        self.assertFalse(any(c[0] in (STARTFN,WIFIFN) for c in b.calls))
    def test_metadata_corruption_read_errors_and_failed_open_close_cleanly(self):
        for kind in ('crc','cache','error','open'):
            b=self.bench();b.init()
            if kind=='crc':b.table_rom=b.table_rom[:-4]+b'bad!'
            if kind=='cache':b.put(TABLE+64,b.get(TABLE+64)^1)
            if kind=='error':b.read_error=1
            if kind=='open':b.open_failure=True;b.close_failures=5
            self.assertEqual(b.open(),FAILED,kind);self.assertEqual(b.get(b.file+8),0)
            self.assertEqual(b.get(REGISTRY+4),0);self.assertEqual(b.close(),RELEASED)
    def test_registry_conflicts_and_foreign_identity_hold(self):
        for id_,lo,n in ((54,IMAGE,0x400),(1,IMAGE,0x60000),(52,IMAGE+0x200,0x100)):
            b=self.bench();b.init();b.u.mem_write(TABLE+id_*32,struct.pack('<8I',id_,lo,n,0,0,0,id_,0));b.bind_config()
            b.put(REGISTRY,id_);b.put(REGISTRY+4,1)
            self.assertEqual(b.open(),FAILED);self.assertEqual(b.get(REGISTRY+4),1);self.assertFalse(any(c[0]==FAST for c in b.calls))
        for at in (CONFIG+12,0x021e3644,REGISTRY+4):
            b=self.bench();b.init();self.assertEqual(b.open(),READY);b.put(at,b.get(at)^4)
            self.assertEqual(b.check(),0);self.assertEqual(b.phase,HELD);before=b.state();self.assertEqual(b.release(),HOLD);self.assertEqual(b.state(),before)
    def test_cancel_every_phase_never_releases_live_native_owner(self):
        for target in range(META_OPEN,WIFI+1):
            b=self.bench();b.init();b.begin()
            while b.phase!=target:self.assertEqual(b.step(),MORE)
            self.assertEqual(b.cancel(),MORE);self.assertEqual(b.drive(),FAILED,target)
            self.assertEqual(b.get(b.file+8),0);self.assertEqual(b.get(REGISTRY+4),0)
            self.assertEqual(sum(c[0]==END for c in b.calls),int(target>START))
    def test_four_aligned_record_owns_entire_metadata_cache_extent(self):
        for offset in range(0,32,4):
            b=self.bench();b.state_address=STATE+offset
            b.u.mem_write(STATE-16,bytes(SIZE+64));b.u.mem_write(b.state_address-16,b'\x96'*16);b.u.mem_write(b.state_address+SIZE,b'\x69'*16)
            b.allowed.append((b.state_address,b.state_address+SIZE))
            self.assertEqual(b.init(),1);self.assertEqual(b.open(),READY)
            self.assertEqual(b.table%32,0);self.assertGreaterEqual(b.table,b.state_address+464)
            self.assertLessEqual(b.table+4128,b.state_address+SIZE);self.assertEqual(b.close(),RELEASED)
    def test_metadata_full_registry_and_rounding_reject_before_reserve(self):
        for kind in ('duplicate','full','active','rounding'):
            b=self.bench(0x404);b.init()
            if kind in ('duplicate','full'):
                for i in range(8 if kind=='full' else 2):
                    id_=i+60 if kind=='full' else 60;b.put(REGISTRY+8*i,id_);b.put(REGISTRY+8*i+4,1)
            if kind=='active':b.put(REGISTRY+4,2)
            if kind=='rounding':
                b.u.mem_write(TABLE+32,struct.pack('<8I',1,IMAGE+0x404,4,0,0,0,1,0));b.bind_config();b.put(REGISTRY,1);b.put(REGISTRY+4,1)
            before=bytes(b.u.mem_read(REGISTRY,64));self.assertEqual(b.open(),FAILED,kind)
            self.assertEqual(bytes(b.u.mem_read(REGISTRY,64)),before);self.assertNotIn(FAST,[c[0] for c in b.calls])
    def test_foreign_association_and_boot_change_retain_or_unwind(self):
        b=self.bench();b.init();b.begin();b.step();b.put(b.file+8,ARC+4)
        self.assertEqual(b.step(),HOLD);before=b.state();self.assertEqual(b.release(),HOLD);self.assertEqual(b.state(),before)
        b=self.bench();b.init();b.begin()
        while b.phase!=START:self.assertEqual(b.step(),MORE)
        b.put(0x27ffc40,2,2);self.assertEqual(b.drive(),FAILED);self.assertNotIn(STARTFN,[c[0] for c in b.calls]);self.assertEqual(b.get(REGISTRY+4),0)
    def test_compile_valid_semantic_mutants_fail_lifetime_effect_assertions(self):
        mutations=[
          ('r>=1&&r<=2&&g&&',''),
          ('m->phase!=P(READY)&&m->phase!=P(FAILED)','m->phase!=P(READY)&&m->phase!=P(FAILED)&&m->phase!=P(ZERO)'),
          ('if(!ok){if(shape(m,&s)>2)', 'if(!ok){m->file_bound=0;if(shape(m,&s)>2)'),
          ('m->phase=m->read_kind?P(IMAGE_CLOSE):P(META_CLOSE);','m->phase=m->read_kind?P(START):P(META_CLOSE);'),
          ('if(s.f[4]||s.f[5]||m->read_return', 'if(s.f[4]||m->read_return'),
          ('(m->crc_acc^~0u)!=m->config.packed_crc','0'),
          ('WIFI(54);m->wifi_done=1;', 'WIFI(54);WIFI(54);m->wifi_done=1;'),
          ('REG[i+1]=reserve;m->registry[i+1]=reserve;', 'REG[1]=reserve;m->registry[i+1]=reserve;'),
          ('if(sh==1)break;\n  m->phase=P(ABORT_CLOSE);','m->file_bound=0;m->phase=P(FAILED);return UI_MODULE_FAILED;'),
        ]
        for index,mutation in enumerate(mutations):
            with self.subTest(index=index),tempfile.TemporaryDirectory(prefix='module-mutant-') as d:
                compiled=compile_module(Path(d),mutation)
                b=ModuleBench(compiled,0x400);b.init()
                if index in (0,1):
                    # Both mutations together would reproduce old zero-release;
                    # each individually also admits invalid behavior below.
                    if index==0:
                        b.begin();b.put(STATE+12,0);b.put(STATE+16,0)
                        observed=b.cancel(0,0);self.assertNotEqual(observed,REFUSED)
                    else:
                        b.put(STATE+12,1);b.put(STATE+16,1)
                        observed=b.release();self.assertNotEqual(observed,REFUSED)
                elif index==2:
                    b.begin();b.close_failures=2
                    self.assertEqual(b.drive(),HOLD) # expected normal owner recovers to READY
                elif index==3:
                    b.begin();self.assertEqual(b.drive(),HOLD);self.assertEqual(b.get(b.file+8),ARC)
                elif index==4:
                    b.read_error=1;self.assertEqual(b.open(),READY) # native error was swallowed
                elif index==5:
                    b.begin()
                    while b.phase!=PACKED_VERIFY:b.step()
                    b.put(CONFIG+64,b.get(CONFIG+64)^1);b.put(STATE+96+64,b.get(CONFIG+64))
                    self.assertEqual(b.drive(),READY) # packed identity mismatch accepted
                elif index==6:
                    self.assertEqual(b.open(),READY);self.assertEqual(sum(c[0]==WIFIFN for c in b.calls),2)
                elif index==7:
                    b.put(REGISTRY,60);b.put(REGISTRY+4,1);self.assertEqual(b.open(),HOLD)
                else:
                    b.begin();b.delay=True
                    while b.phase!=META_WAIT:b.step()
                    b.cancel();b.step();self.assertEqual(b.step(),FAILED);self.assertEqual(b.get(ARC+36),b.file)
    def test_new_generation_requires_retirement_and_never_wraps(self):
        b=self.bench();b.init();self.assertEqual(b.open(),READY);self.assertEqual(b.close(),RELEASED)
        before=b.state();self.assertEqual(b.begin(),REFUSED);self.assertEqual(b.state(),before)
        b.bind_config(2,0xffffffff);self.assertEqual(b.open(2,0xffffffff),READY);self.assertEqual(b.close(2,0xffffffff),RELEASED)
        b.bind_config(2,1);self.assertEqual(b.begin(2,1),REFUSED);self.assertEqual(b.init(),0)
if __name__=='__main__':unittest.main()
