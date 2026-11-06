"""Prepared actual V4 loader/FS/cache/manager execution; no native boot.
Only CARD transport/arbitration, declared scheduler and CP15 effects are seamed.
Authored test modules and virtual cartridge data are never written into a ROM.
"""
import os,tempfile,unittest
from module_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
from test_heap_rom import NativeHeapBench,ROM_PINS,PINS
from heap_bench import BASE as HEAP_META,PARENT,TEMPLATES,META,CREATE,ALLOC,FREE,DESTROY
from test_resource_rom import FS_PINS,TRANSPORT,LOCK,UNLOCK,PULLED,SLEEP,CALLBACK
LOADER_PINS=((0x020d4a20,0x30,'5639273b1631a6cc4111d1b551684112f9bac7b3c374183457b2e24fca8e852b'),
 (0x02000010,0x60,'0a15dd72bccb740cbe352c3a1b3436bd1a5483d90fdc1f29ba67cd71166d05a3'),
 (0x02000300,0x2c,'a592fde83daca563cdbf5986dd4f42d86cf1ac19a90f3891e31e825592912b68'),
 (0x02000970,0xac,'407d3c7be83d55aecfbe0c48d7a300890efded6c731b3d49364c34be375899e1'),
 (0x020d3a38,0x64,'a07251e67ddd2cafd3d1ece5d8059478e06096aa6a889ac9bc4ef29fcabed197'),
 (0x02006f58,0x3d4,'ef47c79d4c0b931114c6daa57446deceac9464883f1f5ba62e96b37d507ada05'),(0x020d8748,0x6b8,'aa1af88d8f77de60bf35f75d2cb5181f27487e2867912c94754f25a576b8bb9e'),(0x020d285c,0xb4,'f21d605724b0221da4c2ba63f4223a104458bdcbb3bebb144024efc3e08e1d8f'),
 (0x023da250,572,'d275bc783f587c382d7ffd71bc7488241b3199fed2fc68861c5edcfb1e9f1153'),
 (0x020d4994,0x8c,'32b03cfe980e0ad0a93146c009916dd8a48227a21bb12cc1021e49085109969b'),(0x020e5b44,0x34,'c689a1df0550721ec10fc6b151166fe1088f25d64ef6cb547b3d592278c07c05'))
CALLRETURN=STOP+0x40
NEW,RUN,DELETE=0x0200724d,0x020072a9,0x02007279
TEMPLATE,ARGS=CONFIG+0x100,CONFIG+0x200
WRAPPERS="""
typedef struct { unsigned cb[4],exec,proc;void *args,*data;unsigned a,b; } Manager;
typedef struct { UiModule *m;const UiModuleConfig *c;unsigned role,gen; } Args;
typedef unsigned (*Entry)(Manager *,unsigned *);
unsigned probe_init(Manager *man,unsigned *step) {
 Args *a=man->args;UiModuleResult r;
 if(a->m->phase==UI_MODULE_P_ZERO)r=ui_module_begin(a->m,a->c,a->role,a->gen);
 else r=ui_module_step(a->m,a->role,a->gen,4096);
 if(r==UI_MODULE_FAILED)return ui_module_release(a->m,a->role,a->gen)==UI_MODULE_RELEASED;
 if(r!=UI_MODULE_READY)return 0;
 Entry e=(Entry)ui_module_check(a->m,a->role,a->gen,0);return e?e(man,step):0;
}
unsigned probe_main(Manager *man,unsigned *step) {
 Args *a=man->args;if(a->m->phase==UI_MODULE_P_RELEASED)return 1;
 Entry e=(Entry)ui_module_check(a->m,a->role,a->gen,1);return e?e(man,step):0;
}
unsigned probe_exit(Manager *man,unsigned *step) {
 Args *a=man->args;if(a->m->phase==UI_MODULE_P_RELEASED)return 1;
 if(a->m->phase==UI_MODULE_P_READY) {
  Entry e=(Entry)ui_module_check(a->m,a->role,a->gen,2);
  if(!e||!e(man,step))return 0;
  ui_module_release(a->m,a->role,a->gen);return 0;
 }
 return ui_module_step(a->m,a->role,a->gen,4096)==UI_MODULE_RELEASED;
}
"""
FS_ROOTS=(0x20d6864,0x20d68c0,0x20d6a50,0x20d6aa0,0x20d6b60,0x20d6b94,0x20d6bc0,0x20d6bec,0x20d6c84,0x20d6db0,0x20d6f94,0x20d7340,0x20d73c0,0x20d73e8,0x20d73f0,0x20d7448,0x20d7464,0x20d7484,0x20d749c,0x20d76b0,0x20d7744,0x20d7788,0x20d792c,0x20d7958,0x20d7998,0x20d7a4c,0x20d7ad0,0x20d7b40,0x20d7c00,0x20d7d24,0x20d7db0,0x20d7e4c,0x20d7ebc,0x20d7edc,0x20d7f60,0x20d7f88,0x20d7f98,0x20d7fc0,0x20d8104,0x20d8180,0x20d81c0,0x20d8208,0x20d8278,0x20d82c0,0x20d82fc,0x20d83bc,0x20d83cc,0x20d83dc,0x20d8448,0x20d84a0,0x20d84c4,0x20d850c,0x20d8514,0x20d8580,0x20d8588,0x20d8590,0x20d86d8,0x20d8728,0x20d8748,0x20d8764,0x20d87a0,0x20d87c8,0x20d88c0,0x20d89bc,0x20d8a48,0x20d8ad8,0x20d8b6c,0x20d8c60,0x20d8d50,0x20d8d60,0x20d8db4)
class NativeModuleBench(ModuleBench):
    def __init__(self,compiled,fixture,size=0x8000):
        super().__init__(compiled,size);sections,fat,fnt,table=fixture;self.sections=sections
        self.native=True;self.events=[];self.cache_ops=[];self.callback_return=None;self.pending=None;self.delay=False;self.never=False;self.sleeps=0;self.partial=False;self.close_fault=False;self.image_read=False;self.production=True;self.open_fault=False;self.failure_return=None;self.close_failures=0
        for p,data in sections:self.u.mem_write(p,data)
        self.u.mem_write(CODE,self.code)
        self.u.mem_write(FAT,fat);self.u.mem_write(FNT,fnt);self.u.mem_write(TABLE,bytes(table));self.metadata()
        self.table_rom=bytes(self.u.mem_read(TABLE,4128))
        self.put(0x027ffe50,0x10020000);self.put(0x027ffe54,4128)
        self.put(0x021e3628,ARC);self.put(0x021e362c,ARC);self.put(0x021e3630,0);self.put(0x021e3634,0)
        self.put(0x021e363c,0x42);self.put(0x021e3640,0)
        self.put(0x021e3644,0);self.put(0x021e3648,0);self.bind_config()
        self.allowed.extend(((0x021e3628,0x021e3638),(0x023da040,0x023da080)))
        self.native_fetch=instruction_set(self.u,[*FS_ROOTS,INFO,LOAD|1,UNLOAD|1,NEW,RUN,DELETE,
          0x020072c7,0x020072db,0x020072f3,0x02007309,
          0x02000010,0x0200001c,0x02000300,0x02000970,0x023da47c|1,WIFIFN|1,
          0x020d285c,0x020d2894,0x020d28d0,0x020d4994,0x020d4a50,
          0x020d1ecc,0x020d3a38,0x020d3a4c,CPSR,0x0201aa8d,0x0201ab0d,
          CREATE,ALLOC,FREE,DESTROY],self.native_regions())
        self.native_fetch.discard(0x020d8c18) # Shipped raw-branch target is a trampoline literal, not code.
        self.native_sp=[];self.bad_alignment=[];self.cp15=[];self.closes=[];self.close_pending=[]
        self.allowed.append((0x0225f0a8,0x0225f0a9));self.allowed.append((0x0225f164,0x0225f165))
    def prepare_manager(self):
        preserved=bytes(self.u.mem_read(STATE-16,CONFIG+96-(STATE-16)))
        h=NativeHeapBench((b'',{}),self.sections)
        regions=[(META,28),(HEAP_META,824),(0x021d84b0,16),(PARENT,0x100000),*TEMPLATES]
        for p,n in regions:self.u.mem_write(p,bytes(h.u.mem_read(p,n)));self.allowed.append((p,p+n))
        self.u.mem_write(STATE-16,preserved)
        # Prepared heap11: actual NNS parent allocation/constructor; only the
        # registry seed is synthetic. Production checked bridge remains future.
        backing=self.address(ALLOC,PARENT,0x1c000,4);assert backing
        assert self.address(CREATE,backing,0x1c000,0)==backing
        self.put(HEAP_META+16,backing);self.put(HEAP_META+116+16,PARENT)
        self.put(HEAP_META+228+16,backing);self.put(HEAP_META+662+11,4,1)
        self.record_allocation=self.address(0x0201aa8d,11,SIZE+32)
        assert self.record_allocation and self.get(self.record_allocation-4,1)==11
        self.state_address=self.record_allocation+16
        self.u.mem_write(self.state_address,bytes(SIZE));self.u.mem_write(self.state_address-16,b'\x96'*16);self.u.mem_write(self.state_address+SIZE,b'\x69'*16)
        self.u.mem_write(TEMPLATE,struct.pack('<4I',*(self.symbols[x] for x in ('probe_init','probe_main','probe_exit')),0xffffffff))
        self.u.mem_write(ARGS,struct.pack('<4I',self.state_address,CONFIG,1,1))
        self.manager=self.address(NEW,TEMPLATE,ARGS,11)
        self.heap_backing=backing
        return self.manager
    def native_regions(self):
        return ((0x02000010,0x02000058),(0x0201a910,0x0201abec),(0x020b4b68,0x020b556c),(0x02000300,0x02000324),(0x02000970,0x02000a1c),(0x02006f58,0x0200732c),(0x020d6864,0x020d8e00),(0x020d285c,0x020d2910),
          (0x020d4994,0x020d4bd0),(0x020d1ecc,0x020d1f34),(0x020d3a38,0x020d3a9c),(0x023da250,0x023da48c))
    def native_allowed(self,p):return p in self.native_fetch
    def callback(self,cb,arg,ret):
        assert cb==CALLBACK and arg==ARC and self.callback_return is None
        self.callback_return=ret;self.u.reg_write(UC_ARM_REG_R0,arg);self.u.reg_write(UC_ARM_REG_LR,CALLRETURN);self.u.reg_write(UC_ARM_REG_PC,cb)
    def complete(self,error=0):
        assert self.pending is not None
        cb,arg,dst,data=self.pending;self.pending=None
        self.u.mem_write(dst,data)
        if error:self.address(0x020d7edc,ARC,error)
        else:self.address(CALLBACK,ARC)
    def hook(self,u,p,n,d):
        if self.failure_return is not None and p==self.failure_return:
            self.failure_return=None;self.put(ARC+0x1c,self.get(ARC+0x1c)&~0x80)
        if self.close_pending and p==self.close_pending[-1][0]:
            ret,file=self.close_pending.pop();self.closes.append((file,u.reg_read(UC_ARM_REG_R0),self.get(file+8),self.get(file+12),self.get(ARC+0x24)))
        if CODE<=p<CODE+len(self.code) or p==STOP:return super().hook(u,p,n,d)
        if IMAGE<=p<IMAGE+len(self.raw):
            assert self.phase==ACTIVE,'dynamic fetch outside READY'
            assert p<IMAGE+28,'fetch outside authored probe'
            assert u.reg_read(UC_ARM_REG_SP)%8==0,'dynamic entry stack alignment'
            self.instructions+=1;self.visited.add(p);return
        self.measure_irq();self.instructions+=1;self.visited.add(p);sp=u.reg_read(UC_ARM_REG_SP);self.low=min(self.low,sp)
        assert STACK-3072<=sp<=STACK
        if p==CALLRETURN:
            ret=self.callback_return;self.callback_return=None;self.ret(0);u.reg_write(UC_ARM_REG_PC,ret);return
        if p in (LOCK,UNLOCK,PULLED):self.ret(0);return
        if p==TRANSPORT:
            dma,pos,dst,length=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            cb,arg,async_=struct.unpack('<3I',bytes(u.mem_read(sp,12)))
            assert dma==0 and async_==1
            if 0x10000000<=pos<0x10010000:
                assert dst==IMAGE and length<=len(self.encoded);raw=self.encoded;offset=pos-0x10000000;self.image_read=True
            else:
                assert 0x10020000<=pos<0x10020000+4128 and (dst==self.table if self.production else STACK-3072<=dst<STACK)
                raw=self.table_rom;offset=pos-0x10020000
            assert offset+length<=len(raw)
            self.events.append(('transport',dst,length));count=length-4 if self.partial and dst==IMAGE else length
            data=raw[offset:offset+count]
            if self.delay or self.never:self.pending=(cb,arg,dst,data);self.ret(0)
            else:
                u.mem_write(dst,data);self.callback(cb,arg,u.reg_read(UC_ARM_REG_LR))
            return
        if p==SLEEP:
            assert self.pending is not None;self.sleeps+=1
            if self.never:
                if self.sleeps==3:u.emu_stop()
                else:self.ret(0)
                return
            cb,arg,dst,data=self.pending;self.pending=None;u.mem_write(dst,data);self.callback(cb,arg,u.reg_read(UC_ARM_REG_LR));return
        if self.production:
            assert p not in (INFO,LOAD,UNLOAD,0x20d87c8,0x20d8db4,0x23da47c,0x20d82fc),f'unsafe production helper {p:08x}'
        if self.production and p==INITFILE and u.reg_read(UC_ARM_REG_R0)==self.file:assert self.get(self.file+8)==0,'reinitialize bound native file'
        if self.production and p==CLOSE:assert u.reg_read(UC_ARM_REG_R0)==self.file and self.get(self.file+8)==ARC,'close lost persistent association'
        if self.production and p==STARTFN:assert self.get(self.file+8)==0,'Start before successful close'
        if p in (*LOWER,INFO,LOAD,UNLOAD):
            self.calls.append((p,*[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)]))
            assert sp%8==0,f'external native alignment {p:08x}'
        if p in (*FS_ROOTS,0x020d285c,0x020d2894,0x020d28d0):
            self.native_sp.append((p,sp))
            if sp%8:self.bad_alignment.append((p,sp))
            self.events.append(('native',p))
        if p in (0x020d285c,0x020d2894,0x020d28d0):
            a,length=u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)
            assert (a==IMAGE and length==len(self.raw)) or (p==INVALIDATE and a==self.table and length==4128),f'cache extent {a:08x}/{length:08x}'
            self.cache_ops.append((p,a,length))
        if p==CLOSE:
            file=u.reg_read(UC_ARM_REG_R0);self.close_pending.append((u.reg_read(UC_ARM_REG_LR)&~1,file))
            fail=self.close_failures>0 or (self.close_fault and self.image_read)
            if self.close_failures:self.close_failures-=1
            if fail:
                self.put(ARC+0x1c,self.get(ARC+0x1c)|0x80)
                if self.production:self.failure_return=u.reg_read(UC_ARM_REG_LR)&~1
        if p in (DIRECT,FAST) and self.open_fault:
            self.put(ARC+0x1c,self.get(ARC+0x1c)|0x80);self.failure_return=u.reg_read(UC_ARM_REG_LR)&~1
        assert p not in (0x0202551c,0x02096338,0x020d38b0,0x020d3f48),'native assertion/reset/terminate'
        assert self.native_allowed(p),f'unknown native fetch {p:08x}'
        assert any(a<=p<p+n<=a+length for a,length,digest in (*PINS,*FS_PINS,*LOADER_PINS)),f'unhashed native fetch {p:08x}'
        # Actual cache loops/rounding execute. Only individual CP15 maintenance
        # effects are substituted because Unicorn is not a DS cache controller.
        if not u.reg_read(UC_ARM_REG_CPSR)&32:
            word=self.get(p)
            if word&0x0f000010==0x0e000010 and (word>>8)&15==15:
                rt=(word>>12)&15;crm=word&15;op=(word>>5)&7
                if crm in (5,6,14) and op==1:
                    addr=u.reg_read(UC_ARM_REG_R0+rt)
                    assert IMAGE<=addr<IMAGE+((len(self.raw)+31)&~31) or self.table<=addr<self.table+4128,f'CP15 extent {addr:08x}'
                self.cp15.append((p,word));u.reg_write(UC_ARM_REG_PC,p+4)
class ModuleRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        paths={l:Path(os.environ.get('SGP_UI_MODULE_'+l,str(canonical/f'candidate-v4-{l}.nds'))) for l in ROM_PINS}
        missing=[l for l,p in paths.items() if not p.is_file()]
        if missing:
            msg='canonical V4 module inputs missing: '+','.join(missing)
            if os.environ.get('SGP_UI_MODULE_REQUIRE_INPUTS')=='1':raise AssertionError(msg)
            raise unittest.SkipTest(msg)
        import ndspy.rom
        cls.fixtures={}
        for lang,path in paths.items():
            data=path.read_bytes();assert (len(data),hashlib.sha256(data).hexdigest())==ROM_PINS[lang]
            r=ndspy.rom.NintendoDSRom(data);sections=ndspy_load_arm9_sicuro(r).sections
            for a,n,want in (*PINS,*FS_PINS,*LOADER_PINS):
                s=next(s for s in sections if s.ramAddress<=a<a+n<=s.ramAddress+len(s.data))
                got=hashlib.sha256(bytes(s.data[a-s.ramAddress:a-s.ramAddress+n])).hexdigest()
                assert got==want,f'{lang} guard {a:08x}: {got}'
            fnt,fn,fat,fa=struct.unpack_from('<4I',data,0x40)
            cls.fixtures[lang]=([(s.ramAddress,bytes(s.data)) for s in sections if 0x02000000<=s.ramAddress<0x02400000],data[fat:fat+fa],data[fnt:fnt+fn],r.arm9OverlayTable)
        cls.temp=tempfile.TemporaryDirectory(prefix='module-native-');cls.addClassCleanup(cls.temp.cleanup);cls.compiled=compile_module(Path(cls.temp.name),extra=WRAPPERS)
    def bench(self,lang='EN',size=0x400):return NativeModuleBench(self.compiled,self.fixtures[lang],size)
    def test_actual_heap11_manager_pending_and_exit_barrier(self):
        for lang in self.fixtures:
            for role in (1,2):
                b=self.bench(lang);m=b.prepare_manager();b.bind_config(role);b.put(ARGS+8,role)
                self.assertEqual(b.get(b.state_address-32+12,1),11)
                self.assertEqual(b.init(),1);b.delay=True
                while b.phase!=META_WAIT:self.assertEqual(b.address(RUN,m),0)
                before=b.get(HEAP_META+340+22,2)
                for _ in range(5):
                    b.poison_stack();self.assertEqual(b.address(RUN,m),0);self.assertEqual(b.get(ARC+36),b.file);self.assertEqual(b.get(HEAP_META+340+22,2),before)
                b.complete();b.delay=False
                for _ in range(100):
                    done=b.address(RUN,m)
                    if done:break
                else:self.fail('manager did not finish')
                self.assertEqual(b.phase,RETIRED);self.assertEqual(b.get(b.file+8),0);self.assertEqual(b.get(REGISTRY+4),0)
                b.u.mem_write(IMAGE,b'\xfe'*len(b.raw));self.assertEqual(b.check(role),0)
                b.address(DELETE,m);self.assertEqual(b.get(HEAP_META+340+22,2),1)
                b.address(0x0201ab0d,b.record_allocation);self.assertEqual(b.get(HEAP_META+340+22,2),0)
                self.assertEqual(b.sleeps,0)
                for p in (NEW&~1,RUN&~1,DELETE&~1,IMAGE,IMAGE+4,IMAGE+8):self.assertIn(p,b.visited)
                for p in (STARTFN,WIFIFN,END):self.assertEqual(sum(c[0]==p for c in b.calls),1)
    def test_actual_manager_clean_failure_retires_without_dynamic_fetch(self):
        b=self.bench();m=b.prepare_manager();b.init();b.partial=True
        for _ in range(100):
            if b.address(RUN,m):break
        else:self.fail('clean failure trapped manager forever')
        self.assertEqual(b.phase,RETIRED);self.assertEqual(b.get(REGISTRY+4),0);self.assertEqual(b.get(b.file+8),0)
        self.assertFalse(any(IMAGE<=p<IMAGE+len(b.raw) for p in b.visited));self.assertNotIn(STARTFN,b.visited)
        b.address(DELETE,m);b.address(0x0201ab0d,b.record_allocation);self.assertEqual(b.get(HEAP_META+340+22,2),0)
    def test_actual_lower_loader_uncached_and_cached_lifetime(self):
        for lang in self.fixtures:
            for cached in (False,True):
                b=self.bench(lang);b.init()
                if cached:b.put(0x21e3644,TABLE);b.put(0x21e3648,4128)
                self.assertEqual(b.open(),READY);self.assertEqual(b.check(),IMAGE+1);self.assertEqual(b.close(),RELEASED)
                for p in (DIRECT,FAST,READ,CLOSE,CLEAR,STARTFN,END,WIFIFN,0x20d8c60):self.assertIn(p,b.visited)
                for p in (INFO,LOAD,UNLOAD,0x20d82fc,0x20d8db4):self.assertNotIn(p,b.visited)
                self.assertEqual(b.cache_ops,[(INVALIDATE,b.table,4128),(0x20d28d0,IMAGE,0x400),(INVALIDATE,IMAGE,0x400),(0x20d2894,IMAGE,0x400)])
                self.assertTrue(all(c[0]==b.file for c in b.closes));self.assertFalse(b.bad_alignment,b.bad_alignment)
    def test_actual_delayed_metadata_and_image_close_failures_recover(self):
        for lang in self.fixtures:
            for target in (META_WAIT,IMAGE_WAIT):
                b=self.bench(lang);b.init();b.begin()
                while b.phase!=target:
                    if b.phase in (META_READ,IMAGE_READ):b.delay=b.phase==(META_READ if target==META_WAIT else IMAGE_READ)
                    self.assertEqual(b.step(),MORE)
                for _ in range(5):
                    b.poison_stack();self.assertEqual(b.step(),MORE);self.assertEqual(b.get(ARC+36),b.file)
                    self.assertEqual(b.get(b.file+48),b.table if target==META_WAIT else IMAGE)
                b.complete();self.assertEqual(b.step(),MORE);b.close_failures=5
                for _ in range(5):
                    b.poison_stack();self.assertEqual(b.step(),MORE);self.assertEqual(b.get(b.file+8),ARC)
                    self.assertNotIn(STARTFN,b.visited)
                b.delay=False;self.assertEqual(b.drive(),READY);self.assertEqual(b.close(),RELEASED)
                self.assertEqual(b.sleeps,0);self.assertEqual(sum(c[1]==0 for c in b.closes),5)
    def test_actual_failed_open_retains_bound_file_until_close(self):
        for target in (META_OPEN,IMAGE_OPEN):
            b=self.bench();b.init();b.begin()
            while b.phase!=target:self.assertEqual(b.step(),MORE)
            b.open_fault=True;self.assertEqual(b.step(),MORE);self.assertEqual(b.get(b.file+8),ARC);self.assertEqual(b.get(b.file+12)&16,0)
            b.open_fault=False;b.close_failures=5
            self.assertEqual(b.drive(),FAILED);self.assertEqual(b.get(b.file+8),0);self.assertEqual(b.get(REGISTRY+4),0)
            self.assertEqual(b.close(),RELEASED);self.assertNotIn(STARTFN,b.visited)
    def test_native_metadata_failures_and_disjoint_foreign_slot(self):
        for lang in self.fixtures:
            for kind in ('rom','cache','header'):
                b=self.bench(lang);b.init()
                if kind=='rom':b.table_rom=b.table_rom[:100]+bytes([b.table_rom[100]^1])+b.table_rom[101:]
                elif kind=='cache':b.put(0x21e3644,TABLE);b.put(0x21e3648,4128);b.put(TABLE+64,b.get(TABLE+64)^1)
                else:b.put(0x27ffe50,b.get(0x27ffe50)+4)
                self.assertEqual(b.open(),FAILED);self.assertEqual(b.get(b.file+8),0);self.assertEqual(b.get(REGISTRY+4),0);self.assertNotIn(STARTFN,b.visited)
            b=self.bench(lang);b.init();b.put(REGISTRY+8,52);b.put(REGISTRY+12,1)
            self.assertEqual(b.open(),READY);self.assertEqual(b.close(),RELEASED)
            self.assertEqual((b.get(REGISTRY+8),b.get(REGISTRY+12)),(52,1))
    def test_native_indefinite_close_and_foreign_source_keep_owner(self):
        b=self.bench();b.init();b.begin()
        while b.phase!=IMAGE_CLOSE:self.assertEqual(b.step(),MORE)
        b.close_failures=0xffffffff
        for _ in range(16):b.poison_stack();self.assertEqual(b.step(),MORE);self.assertEqual(b.get(b.file+8),ARC);self.assertEqual(b.get(REGISTRY+4),1)
        self.assertNotIn(STARTFN,b.visited)
        b.put(ARC+0x48,b.get(ARC+0x48)+4)
        self.assertEqual(b.step(),HOLD);before=b.state();self.assertEqual(b.release(),HOLD);self.assertEqual(b.state(),before)
        self.assertEqual(b.get(b.file+8),ARC);self.assertEqual(b.get(REGISTRY+4),1)
    def test_actual_pending_cancel_and_read_error_no_early_free(self):
        for target in (META_WAIT,IMAGE_WAIT):
            for error in (0,1):
                b=self.bench();b.init();b.begin()
                while b.phase!=target:
                    if b.phase in (META_READ,IMAGE_READ):b.delay=b.phase==(META_READ if target==META_WAIT else IMAGE_READ)
                    self.assertEqual(b.step(),MORE)
                if not error:self.assertEqual(b.cancel(),MORE)
                for _ in range(8):b.poison_stack();self.assertEqual(b.step(),MORE);self.assertEqual(b.get(ARC+36),b.file)
                b.complete(error);self.assertEqual(b.drive(),FAILED);self.assertEqual(b.get(b.file+8),0);self.assertEqual(b.get(REGISTRY+4),0)
                self.assertNotIn(STARTFN,b.visited);self.assertNotIn(0x20d82fc,b.visited)
    def test_actual_short_or_corrupted_packed_input_never_decompresses(self):
        for fault in ('short','footer','body'):
            b=self.bench();b.init();b.begin();b.partial=fault=='short'
            while b.phase!=PACKED_VERIFY:self.assertEqual(b.step(),MORE)
            if fault!='short':
                at=IMAGE+(len(b.encoded)-1 if fault=='footer' else 8);b.put(at,b.get(at,1)^1,1)
            self.assertEqual(b.drive(),FAILED);self.assertEqual(b.get(REGISTRY+4),0)
            self.assertNotIn(STARTFN,b.visited);self.assertNotIn(0x2000970,b.visited)
    def test_native_sizes_roles_independent_decode_and_wifi_control(self):
        import sys
        sys.path.insert(0,str(SOURCE));from sgp12.blz import blz_decomprimi
        for lang in self.fixtures:
            for size in (0x400,0x8000,0x10000):
                for role in (1,2):
                    b=self.bench(lang,size);b.bind_config(role);b.init()
                    b.put(0x23da240,0x0257);b.put(0x23da044,17)
                    self.assertEqual(blz_decomprimi(b.encoded),b.raw)
                    self.assertEqual(b.open(role),READY);self.assertEqual(bytes(b.u.mem_read(IMAGE,size)),b.raw)
                    self.assertEqual(b.close(role),RELEASED);self.assertFalse(b.bad_alignment,b.bad_alignment)
                    control=self.bench(lang,size);control.production=False;control.put(0x21e3644,TABLE);control.put(0x21e3648,4128)
                    control.put(0x23da240,0x0257);control.put(0x23da044,17)
                    self.assertEqual(control.address(LOAD|1,54,2),1)
                    self.assertEqual(b.get(0x23da044),18)
                    self.assertEqual(bytes(b.u.mem_read(0x23da040,64)),bytes(control.u.mem_read(0x23da040,64)))
                    self.assertEqual(bytes(b.u.mem_read(0x23da240,16)),bytes(control.u.mem_read(0x23da240,16)))
                    self.assertEqual(b.cache_ops[1:],control.cache_ops)
    def test_actual_native_hook_mutation_fails_decoded_crc_then_unwinds(self):
        for lang,fixture in self.fixtures.items():
            native=fixture[0][0][1];b=self.bench(lang);b.init()
            pointer,signature=struct.unpack_from('<2I',native,0x324);b.put(pointer,signature)
            self.assertEqual(b.open(),READY);self.assertEqual((b.get(pointer+8,1),b.get(pointer+0xc4,1)),(0x72,0x8e));self.assertEqual(b.close(),RELEASED)
            b=self.bench(lang);raw=bytearray(b.raw);raw[0x274:0x27c]=native[0x5c:0x64];b.raw=bytes(raw);b.encoded=packed_bytes(b.raw);b.metadata();b.bind_config();b.init()
            self.assertEqual(b.open(),FAILED);self.assertIn(END,b.visited);self.assertNotIn(WIFIFN,b.visited);self.assertEqual(b.get(REGISTRY+4),0)
    def test_native_semantic_mutants_expose_escaped_file_or_forbidden_boundary(self):
        # Each mutant compiles and runs actual native services until the named
        # ownership effect or forbidden service boundary is observed.
        open_old='INITFILE(m->file);m->file_bound=1;\n  U ok=m->read_kind?FAST(m->file,(U)ARC,54):DIRECT(m->file,(U)ARC,m->read_start,m->read_end,~0u);'
        open_bad='U stack_file[18];for(U i=0;i<18;++i)((volatile U *)stack_file)[i]=0;INITFILE(stack_file);m->file_bound=1;\n  U ok=m->read_kind?FAST(stack_file,(U)ARC,54):DIRECT(stack_file,(U)ARC,m->read_start,m->read_end,~0u);'
        mutants=[
          ((open_old,open_bad),'stack'),
          (('U ok=CLOSE(m->file);snapshot(m,&s);','INITFILE(m->file);U ok=CLOSE(m->file);snapshot(m,&s);'),'reinitialize bound native file'),
          (('if(sh==1)break;','if(sh==1){((U (*)(void *))0x020D82FCu)(m->file);break;}'),'unsafe production helper 020d82fc'),
          (('WIFI(54);m->wifi_done=1;','((void (*)(U))0x023DA47Du)(54);m->wifi_done=1;'),'unsafe production helper 023da47c'),
          (('if(!END(m->info))','if(!((U (*)(U,U))0x020D8DB4u)(0,54))'),'unsafe production helper 020d8db4'),
        ]
        for mutation,reason in mutants:
            with self.subTest(reason=reason),tempfile.TemporaryDirectory(prefix='module-native-mutant-') as d:
                b=NativeModuleBench(compile_module(Path(d),mutation),self.fixtures['EN'],0x400);b.init()
                if reason=='stack':
                    self.assertEqual(b.open(),HOLD)
                    file=next(c[1] for c in b.calls if c[0]==DIRECT)
                    self.assertTrue(STACK-3072<file<STACK);self.assertEqual(b.get(file+8),ARC);self.assertNotEqual(file,b.file)
                elif '82fc' in reason:
                    b.begin();b.delay=True
                    while b.phase!=META_WAIT:self.assertEqual(b.step(),MORE)
                    with self.assertRaisesRegex(AssertionError,reason):b.step()
                    self.assertEqual(b.get(ARC+36),b.file)
                elif '8db4' in reason:
                    self.assertEqual(b.open(),READY)
                    with self.assertRaisesRegex(AssertionError,reason):b.close()
                    self.assertEqual(b.get(REGISTRY+4),1)
                else:
                    with self.assertRaisesRegex(AssertionError,reason):b.open()
    def test_native_wifi_modes_match_control_counter_and_preserve_other_data(self):
        for state in (0,0x0157,0x0257,0x010257):
            b=self.bench();b.put(0x23da240,state);b.u.mem_write(0x23da040,bytes(range(64)));before=bytes(b.u.mem_read(0x23da040,64));b.init()
            self.assertEqual(b.open(),READY)
            expected=bytearray(before)
            if state&0xffff==0x0257:struct.pack_into('<I',expected,4,struct.unpack_from('<I',before,4)[0]+1)
            self.assertEqual(bytes(b.u.mem_read(0x23da040,64)),bytes(expected));self.assertEqual(b.close(),RELEASED)
    def test_unsafe_raw_digest_and_stack_file_controls_remain_visible(self):
        for lang in self.fixtures:
            b=self.bench(lang);b.init();b.put(0x27ffc40,2,2);self.assertEqual(b.begin(),REFUSED)
            b=self.bench(lang);b.production=False;b.put(0x21e3644,TABLE);b.put(0x21e3648,4128);b.put(0x27ffc40,2,2)
            with self.assertRaisesRegex(AssertionError,'native assertion/reset/terminate'):b.address(LOAD|1,54,2)
            b=self.bench(lang);b.production=False;b.put(0x21e3644,TABLE);b.put(0x21e3648,4128);b.encoded=b.raw;b.put(TABLE+54*32+28,0);b.put(FAT+54*8+4,0x10000000+len(b.raw))
            with self.assertRaisesRegex(AssertionError,'unknown native fetch 020d8c18'):b.address(LOAD|1,54,2)
            self.assertEqual(b.u.reg_read(UC_ARM_REG_R0),0);self.assertEqual(b.u.reg_read(UC_ARM_REG_R1),0x27ffc40)
            b=self.bench(lang);b.production=False;b.put(0x21e3644,TABLE);b.put(0x21e3648,4128);b.close_fault=True
            b.address(LOAD|1,54,2)
            failed=[c for c in b.closes if c[1]==0];self.assertTrue(failed)
            self.assertTrue(all(STACK-3072<c[0]<STACK and c[2]==ARC for c in failed))
if __name__=='__main__':unittest.main()
