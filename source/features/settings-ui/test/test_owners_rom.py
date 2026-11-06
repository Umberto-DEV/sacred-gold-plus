"""Class B: guarded canonical V4 native CPU code, prepared SDK pool, no ROM writes.

This executes native accessors/IRQ/Alloc0/Push on a true SYSTEM DTCM stack.
The pool is a guarded prepared fixture; PXI/ARM7 initialization and audible
acknowledgment are intentionally not claimed. Hardware flash READ stays the
explicit Class A boundary beneath actual Training storage predicates.
"""
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest
from owners_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC

PINS=(
 (0x0200597c,0x14,'951043abf643b6f95933125dc075c1a6289b87b6ea2d8137d715422a35c77f34'),
 (0x020c7958,0x5c,'e91cd149fccd9cefd6572c94eac418ab646a4c2ba8f28b1c5fe9ef42ea47e12b'),
 (0x020d53dc,0xf4,'f7881e640637cd5f1934dd7263fb6a396c3b244b214d4ea2cce1c4b5eeee99a2'),
 (0x020d5530,0xd4,'d6463d52ecba0a83528a5f4d6c319bb0f600b4a62517c777d2b9e8c12e4eafa4'),
 (0x020d5714,0xc0,'49d948ce696fb303c8719ae142cc21c20ef38f0be30fa5d8c4b23b28ed3a3f7f'),
 (0x020d5bb8,0x88,'2a6f8afe8525191b5c810a191d0d1cfe5d3bc7b5280de6d29e6af9e1a38099ac'),
 (0x020d2368,8,'6dcd5e75586fe6683156c0d559d4827b73bd48d501fa5781a1c6099aacd7c877'),
 (0x0202acf4,248,'20763e0b335dca9b2e5cd751f849af108a33416854cbdaaa75ad4cd151180bb2'),
 (0x02028ea8,12,'e53aa60fe290a49618a1b8cffa2be5bc1be32cdf80999c6445c9aef2e7562285'),
 (0x020272c8,36,'78ad31b1f418961744eff139edca0dfd04048cc9fd3f44b410566e79d39aec3f'),
 (0x020d3a38,44,'47d3f86f499866bc409a71ca4afd60b0d3b659d1e1561c525183293fdc44d858'),
 (0x020d3a90,12,'9c3668b7089a9adbfd85879f1c4689241aea4f8bd7af68fb26cdf12657eda6ee'),
)
ROM_PINS={'EN':('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',147345256),
          'IT':('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',153228136)}
class NativeBoundaryTrap(RuntimeError):pass
class NativeBench(Bench):
    def __init__(self,compiled,code,leased=True):
        self.traps=[]
        super().__init__(compiled,leased,real_native=True)
        # Keep synthetic owner fixture/compiled owners while loading complete
        # canonical ARM9 sections, including every SDK counter/IRQ callee.
        resident=bytes(self.u.mem_read(0x023c0000,0x20000))
        for address,data in code:
            if address==0x01ff8000:self.u.mem_map(0x01ff8000,0x8000)
            self.u.mem_write(address,data)
        self.u.mem_write(0x023c0000,resident)
        # CommandInit establishes this native shared-work pointer; prepared
        # finished tag0 allows real RecvReply(0), cache invalidate and counters.
        self.put(0x021e35a0,0x021e1ac0);self.u.mem_write(0x021e1ac0,bytes(0x280))
        for p,n in self.canaries:self.u.mem_write(p,b'\x5a'*n)
        self.u.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.io_hook,begin=0x04000000,end=0x04000fff)
        self.reset_trace()
    def hook(self,u,address,size,data):
        if address in (0x020d57d4,0x020d5b90,0x0202551c):
            self.traps.append(address);raise NativeBoundaryTrap(hex(address))
        super().hook(u,address,size,data)
    def io_hook(self,u,access,address,size,value,data):
        if address!=IME:raise NativeBoundaryTrap('native I/O '+hex(address))
    def native_call(self,address,*args):
        for i,r in enumerate((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)):
            self.u.reg_write(r,args[i] if i<len(args) else 0)
        self.u.reg_write(UC_ARM_REG_SP,self.stack);self.u.reg_write(UC_ARM_REG_LR,base.STOP|1)
        self.u.emu_start(address,base.STOP,count=100000)
        assert self.u.reg_read(UC_ARM_REG_PC)==base.STOP,'native instruction bound'
        assert self.u.reg_read(UC_ARM_REG_SP)==self.stack,'native balanced stack'
        return self.u.reg_read(UC_ARM_REG_R0)

class OwnersRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        paths={lang:Path(os.environ.get('SGP_SETTINGS_OWNER_'+lang,str(canonical/f'candidate-v4-{lang}.nds'))) for lang in ROM_PINS}
        missing=[lang for lang,p in paths.items() if not p.is_file()]
        if missing:
            message='canonical V4 native owner inputs missing: '+','.join(missing)
            if os.environ.get('SGP_SETTINGS_OWNER_REQUIRE_INPUTS')=='1':raise AssertionError(message)
            raise unittest.SkipTest(message)
        import ndspy.rom
        cls.codes={}
        for lang,p in paths.items():
            digest=hashlib.sha256()
            with p.open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
            if (digest.hexdigest(),p.stat().st_size)!=ROM_PINS[lang]:raise AssertionError('wrong V4 '+lang)
            # Read canonical inputs directly; no copy, output or extraction file.
            rom=ndspy.rom.NintendoDSRom.fromFile(p);sections=ndspy_load_arm9_sicuro(rom).sections
            code=[]
            for address,size,want in PINS:
                matches=[s for s in sections if s.ramAddress<=address<address+size<=s.ramAddress+len(s.data)]
                if len(matches)!=1:raise AssertionError('native pin extent '+hex(address))
                s=matches[0];raw=bytes(s.data[address-s.ramAddress:address-s.ramAddress+size])
                if hashlib.sha256(raw).hexdigest()!=want:raise AssertionError('native pin '+lang+' '+hex(address))
                code.append((address,raw))
            cls.codes[lang]=[(s.ramAddress,bytes(s.data)) for s in sections]
            del rom,sections
        # Complete native images contain unrelated language data; pinned service
        # ranges above must match their shared exact hashes independently.
        cls.temp=tempfile.TemporaryDirectory(prefix='settings-owners-rom-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_all(Path(cls.temp.name))
    def bench(self,lang):return NativeBench(self.compiled,self.codes[lang])
    def canaries(self,b):
        for p,n in b.canaries:self.assertEqual(bytes(b.u.mem_read(p,n)),b'\x5a'*n)
        self.assertLess(b.stack-b.low_sp,3000)
        self.assertEqual(b.masked_io,[]);self.assertEqual(b.flash_writes,[])
        self.assertEqual(b.gate_writes,[]);self.assertEqual(b.calls_after_store,[])
    def test_real_native_getter_setters_and_null_button_ABI(self):
        for lang in self.codes:
            b=self.bench(lang)
            self.assertEqual(b.native_call(0x02028ea9,SAVE),OPTIONS)
            for getter,setter,value,want in ((0x0202ad20,0x0202ad28,2,0x8002),(0x0202ad74,0x0202ad7c,1,0x8082),
                 (0x0202ad90,0x0202ad98,1,0x80c2),(0x0202ad58,0x0202ad60,1,0x80d2),
                 (0x0202adac,0x0202adb4,1,0x81d2),(0x0202adcc,0x0202add4,19,0xcdd2)):
                b.native_call(setter|1,OPTIONS,value);self.assertEqual(b.get(OPTIONS),want)
                self.assertEqual(b.native_call(getter|1,OPTIONS),value)
            for ui,raw in ((1,3),(0,0),(3,0)):
                b.native_call(0x0202acf5,0,ui);self.assertEqual(b.get(BUTTON),raw)
            self.assertEqual(b.traps,[]);self.canaries(b)
    def test_real_preview_pool_pan_order_and_exact_noncanonical_rollback(self):
        for lang in self.codes:
            for original in (0,2,0xffffffff):
                for pending in (0,1):
                    b=self.bench(lang);b.put(MONO,original);self.assertEqual(b.init(),0);b.pool(2,pending)
                    incoming=b.u.reg_read(UC_ARM_REG_CPSR)&255;ime=b.get(IME);b.key(model.RIGHT,3);b.reset_trace()
                    self.assertEqual(b.preview(),0);self.assertEqual(b.get(MONO),1)
                    self.assertEqual(b.get(POOL),NODES+24);self.assertEqual(b.get(POOL+16),NODES+24)
                    self.assertEqual(b.get(POOL+12),NODES)
                    self.assertEqual(b.get(POOL+8),NODES+24*255 if pending else NODES)
                    if pending:self.assertEqual(b.get(NODES+24*255),NODES)
                    self.assertEqual(bytes(b.u.mem_read(NODES+4,20)),struct.pack('<5I',0x18,0x40,0,0,0))
                    allowed=set(range(POOL,POOL+4))|set(range(POOL+8,POOL+20))|set(range(NODES,NODES+24))|set(range(MONO,MONO+4))
                    if pending:allowed|=set(range(NODES+24*255,NODES+24*255+4))
                    for a,n,v in b.owner_writes:self.assertTrue(set(range(a,a+n))<=allowed,(hex(a),n))
                    self.assertEqual(b.rollback(),0);self.assertEqual(b.get(MONO),original)
                    self.assertEqual(b.get(NODES+24+8),0x40 if original else 0xffffffff)
                    self.assertEqual(b.get(NODES),NODES+24);self.assertEqual(b.get(POOL+12),NODES+24)
                    self.assertEqual(b.get(POOL),0);self.assertEqual(b.get(POOL+16),0)
                    self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR)&255,incoming);self.assertEqual(b.get(IME),ime)
                    self.assertEqual(b.traps,[]);self.canaries(b)
    def test_real_empty_pool_is_nonblocking_and_legacy_GF_reaches_wait_trap(self):
        for lang in self.codes:
            b=self.bench(lang);self.assertEqual(b.init(),0);b.pool(0);b.key(model.RIGHT,3)
            before=b.owner();pool=bytes(b.u.mem_read(POOL,36));b.reset_trace()
            for _ in range(4):self.assertEqual(b.preview(),6)
            self.assertEqual(b.get(MONO),0);self.assertEqual(bytes(b.u.mem_read(POOL,36)),pool)
            self.assertEqual(b.owner(),before);self.assertEqual(b.owner_writes,[]);self.assertEqual(b.traps,[])
            self.assertEqual(b.native_call(0x020d5714,0),0)
            with self.assertRaises(NativeBoundaryTrap):b.native_call(0x0200597d,1)
            self.assertEqual(b.traps,[0x020d5b90]);self.assertEqual(b.get(MONO),0)
    def test_actual_coordinator_all_groups_audio_and_DTCM_gate(self):
        for lang in self.codes:
            b=self.bench(lang);self.assertEqual(b.init(),0)
            b.key(model.RIGHT,0);b.key(model.RIGHT,6);b.key(model.LEFT,11);b.key(model.RIGHT,3);b.key(model.RIGHT,4)
            self.assertEqual(b.preview(),0);self.assertEqual(b.request(),2);b.reset_trace()
            before=[(p,bytes(b.u.mem_read(p,n))) for p,n in ((0x023c0000,0x20000),(SAVE,0x2330c),(0x021d110c,0x100))]
            ledger=bytes(b.u.mem_read(OWNERS,C.sizeof(Owners)))
            store_masks=[];b.on_store=lambda x:store_masks.append(x.get(IME))
            self.assertEqual(b.apply(),4);self.assertEqual(b.get(OPTIONS),0x8112)
            allowed=set(range(OPTIONS,OPTIONS+2))|set(range(BUTTON,BUTTON+4))|{0x023d8713,0x023d8700}
            allowed|=set(range(sh.SHINY,sh.SHINY+16))|set(range(sh.ADMITTED,sh.ADMITTED+4))|set(range(sh.FLAGS_OFFSET,sh.FLAGS_OFFSET+2))
            allowed|=set(range(RT+8,RT+12))|{RT+48,RT+49,RT+50}|set(range(RT+680,RT+684))
            for a,n,v in b.owner_writes:self.assertTrue(set(range(a,a+n))<=allowed,(hex(a),n))
            for p,wire in before:
                after=bytes(b.u.mem_read(p,len(wire)))
                for i,(x,y) in enumerate(zip(wire,after)):
                    if x!=y:self.assertIn(p+i,allowed)
            self.assertEqual(bytes(b.u.mem_read(OWNERS,C.sizeof(Owners))),ledger)
            self.assertTrue(store_masks);self.assertEqual(set(store_masks),{0})
            self.assertEqual(b.get(BUTTON),3);self.assertEqual(b.get(MONO),1)
            self.assertEqual(b.get(RT+8),8);self.assertEqual(b.gate_calls,[(30,0)])
            self.assertFalse(any(a in (0x020d5714,0x020d579c,0x0200597c) for a,x,y in b.native_calls[-2:]))
            self.assertEqual(b.traps,[]);self.canaries(b)
    def test_prepared_full_pool_and_malformed_list_fail_before_alloc(self):
        for lang in self.codes:
            b=self.bench(lang);self.assertEqual(b.init(),0);b.pool(256);b.key(model.RIGHT,3)
            self.assertEqual(b.preview(),0);self.assertEqual(b.get(POOL),NODES+24)
            for bad in ('init','cycle','unaligned','tail','shared'):
                b=self.bench(lang);self.assertEqual(b.init(),0);b.key(model.RIGHT,3)
                if bad=='init':b.put(0x021e1a40,0)
                elif bad=='cycle':b.put(NODES,NODES)
                elif bad=='unaligned':b.put(POOL,NODES+4)
                elif bad=='tail':b.put(POOL+16,0)
                else:b.put(POOL+8,NODES);b.put(POOL+12,NODES+72)
                before=b.owner();b.reset_trace();calls=len(b.native_calls)
                self.assertNotEqual(b.preview(),0);self.assertEqual(b.owner(),before);self.assertEqual(b.owner_writes,[])
                self.assertFalse(any(a==0x020d5714 for a,x,y in b.native_calls[calls:]))
    def test_full_pending_pool_legacy_GF_reaches_flush_with_actual_counters(self):
        for lang in self.codes:
            b=self.bench(lang);b.pool(0)
            for i in range(256):b.u.mem_write(NODES+24*i,struct.pack('<6I',NODES+24*(i+1) if i<255 else 0,0x18,0,0,0,0))
            b.put(POOL+8,NODES);b.put(POOL+12,NODES+24*255)
            self.assertEqual(b.native_call(0x020d5af0),0)
            with self.assertRaises(NativeBoundaryTrap):b.native_call(0x0200597d,1)
            self.assertEqual(b.traps,[0x020d57d4]);self.assertEqual(b.get(MONO),0)
    def test_native_IRQ_helpers_and_masked_entry_preserve_control_bits(self):
        for lang in self.codes:
            for masked in (0,128):
                b=self.bench(lang)
                b.u.reg_write(UC_ARM_REG_CPSR,(b.u.reg_read(UC_ARM_REG_CPSR)&~128)|masked)
                control=b.u.reg_read(UC_ARM_REG_CPSR)&255
                self.assertEqual(b.native_call(0x020d3a90),masked)
                saved=b.native_call(0x020d3a38);self.assertEqual(saved,masked)
                self.assertEqual(b.native_call(0x020d3a90),128)
                b.native_call(0x020d3a4c,saved)
                self.assertEqual(b.u.reg_read(UC_ARM_REG_CPSR)&255,control);self.assertEqual(b.get(IME),1)
            b=self.bench(lang);self.assertEqual(b.init(),0);b.key(model.RIGHT,0);self.assertEqual(b.request(),2)
            b.u.reg_write(UC_ARM_REG_CPSR,b.u.reg_read(UC_ARM_REG_CPSR)|128)
            before=b.owner();b.reset_trace();self.assertEqual(b.capture(),6);self.assertEqual(b.preview(),6)
            self.assertEqual(b.rollback(),6);self.assertEqual(b.apply(),1);self.assertEqual(b.read_model().owner_status,6)
            self.assertEqual(b.owner(),before);self.assertEqual(b.owner_writes,[]);self.assertEqual(b.reads,[])
            self.assertEqual(b.bad_capture_writes,[]);self.assertEqual(b.bad_refusal_writes,[])
    def test_opcode_and_flag1_mutants_are_detected_by_native_boundary(self):
        baseline=self.bench('EN');self.assertEqual(baseline.init(),0);baseline.key(model.RIGHT,3)
        self.assertEqual(baseline.preview(),0);self.assertEqual(baseline.get(NODES+4),0x18);self.assertEqual(baseline.traps,[])
        empty=self.bench('EN');self.assertEqual(empty.init(),0);empty.pool(0);empty.key(model.RIGHT,3)
        self.assertEqual(empty.preview(),6);self.assertEqual(empty.traps,[])
        source=(SOURCE/'features/settings-ui/owners.c').read_text()
        for kind,mutated in (('opcode',source.replace('WORD(node+4)=0x18;','WORD(node+4)=18;')),
                            ('flag1',source.replace('0x020D5714u)(0);','0x020D5714u)(1);'))):
            self.assertNotEqual(mutated,source)
            with tempfile.TemporaryDirectory(prefix='owners-native-mutant-') as tmp:
                compiled=compile_all(Path(tmp),mutated)
                b=NativeBench(compiled,self.codes['EN']);self.assertEqual(b.init(),0);b.key(model.RIGHT,3)
                if kind=='opcode':
                    self.assertEqual(b.preview(),0);self.assertNotEqual(b.get(NODES+4),0x18)
                else:
                    b.pool(0)
                    with self.assertRaises(NativeBoundaryTrap):b.preview()
                    self.assertEqual(b.traps,[0x020d5b90])

if __name__=='__main__':unittest.main()
