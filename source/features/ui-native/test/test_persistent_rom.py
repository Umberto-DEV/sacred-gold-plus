"""Class B: actual pinned native NNS and GF control on prepared heap11.
The heap11 ABI matches the captured native topology; this is not game boot.
"""
import hashlib,os,tempfile,unittest
from pathlib import Path
from persistent_bench import *
class PersistentRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ndspy.code
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        cls.sections={}
        for lang,pin in ROM_PINS.items():
            path=Path(os.environ.get('SGP_UI_HEAP_'+lang,str(canonical/f'candidate-v4-{lang}.nds')))
            if not path.is_file():
                if os.environ.get('SGP_UI_PERSISTENT_REQUIRE_INPUTS')=='1':raise AssertionError('missing canonical '+lang)
                raise unittest.SkipTest('missing canonical '+lang)
            digest=hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda:f.read(1<<20),b''):digest.update(chunk)
            assert (path.stat().st_size,digest.hexdigest())==pin
            # Stream the whole-file identity, then read only the ARM9 member.
            # No150MiB cartridge object or extracted copy is needed.
            with path.open('rb') as f:
                header=f.read(0x200)
                offset,entry,ram,length=struct.unpack_from('<4I',header,0x20)
                settings=struct.unpack_from('<I',header,0x70)[0]
                assert length<=0x400000 and offset+length<=path.stat().st_size
                f.seek(offset);arm9=f.read(length);assert len(arm9)==length
            sections=ndspy.code.MainCodeFile(arm9,ram,settings).sections
            for p,n,want in (*PINS,*EXTRA_PINS):
                s=next(s for s in sections if s.ramAddress<=p<p+n<=s.ramAddress+len(s.data))
                assert hashlib.sha256(s.data[p-s.ramAddress:p-s.ramAddress+n]).hexdigest()==want
            cls.sections[lang]=[(s.ramAddress,bytes(s.data)) for s in sections if 0x02000000<=s.ramAddress<0x02400000]
            del arm9,sections
        cls.temp=tempfile.TemporaryDirectory(prefix='persistent-b-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_persistent(Path(cls.temp.name))
        # Real ordinary C return frames around the standalone primitive; these
        # are test callers, not future Bridge or installation implementations.
        cls.configured=compile_persistent(Path(cls.temp.name),full_heap=False,resident=0x023d7b20,extra="""
unsigned bootstrap_callback_probe(unsigned action,unsigned generation) {
    UiPersistent *t=(UiPersistent *)0x023D7B20u;
    if(!action)return (unsigned)ui_persistent_alloc(t,5000,generation);
    if(action==1)return ui_persistent_free(t,generation);
    return ui_persistent_move((UiPersistent *)0x027E3000u,t,generation);
}
""")
    def benches(self):
        for lang,sections in self.sections.items():
            yield PersistentBench(self.compiled,sections)
    def test_native_allocate_headers_zero_count_maximum_and_full_restore(self):
        for b in self.benches():
            before=b.totals();count=b.get(b.counts+22,2)
            for g,n in enumerate((1,31,4624,5001,0x4000),1):
                p=b.alloc(n,g);self.assertTrue(p);rounded=(n+3)&~3
                self.assertEqual(b.get(p-32,2),0x5544)
                self.assertEqual(b.get(p-28),rounded+16)
                self.assertEqual(bytes(b.u.mem_read(p-16,16)),bytes(12)+b'\x0b\0\0\0')
                self.assertEqual(bytes(b.u.mem_read(p,rounded)),bytes(rounded))
                self.assertEqual(before[0]-b.totals()[0],rounded+32)
                self.assertEqual(b.get(b.counts+22,2),count+1)
                self.assertEqual(b.free(g),RELEASED);self.assertEqual(b.totals(),before)
                self.assertEqual(b.get(b.counts+22,2),count)
    def test_native_exhaustion_and_fragmentation_null_preserve_metadata_and_token(self):
        for b in self.benches():
            before=b.totals();blocks=[]
            while True:
                p=b.address(ALLOC,b.heap,0x3000,4)
                if not p:break
                blocks.append(p)
            self.assertGreater(len(blocks),2);old=b.snapshot();self.assertEqual(b.alloc(0x4000),0);self.assertEqual(b.snapshot(),old)
            for p in blocks[::2]:b.address(FREE,b.heap,p)
            self.assertGreater(b.totals()[0],0x4000);self.assertLess(b.totals()[1],0x4000)
            old=b.snapshot();self.assertEqual(b.alloc(0x4000),0);self.assertEqual(b.snapshot(),old)
            for p in reversed(blocks[1::2]):b.address(FREE,b.heap,p)
            self.assertEqual(b.totals(),before);self.assertTrue(b.alloc());self.assertEqual(b.free(),RELEASED)
            self.assertEqual(b.totals(),before)
    def test_native_root_survives_stack_poison_and_unrelated_allocations_after_move(self):
        for b in self.benches():
            before=b.totals();p=b.alloc();self.assertTrue(p);self.assertEqual(b.move(p),RELEASED)
            b.u.mem_write(TOKEN,b'\xa5'*SIZE);b.u.mem_write(p+SIZE,b'\x6c'*(5000-SIZE))
            others=[b.address(ALLOC,b.heap,n,4) for n in (13,703,1164)];self.assertTrue(all(others))
            self.assertEqual(bytes(b.u.mem_read(p+SIZE,5000-SIZE)),b'\x6c'*(5000-SIZE))
            old=b.snapshot();self.assertEqual(b.free(t=p),HOLD);self.assertEqual(b.snapshot(),old)
            b.u.mem_write(TOKEN,bytes(SIZE));self.assertEqual(b.move(TOKEN,p),RELEASED)
            for q in reversed(others):b.address(FREE,b.heap,q)
            self.assertEqual(b.free(),RELEASED);self.assertEqual(b.totals(),before)
            old=b.snapshot();self.assertEqual(b.free(),REFUSED);self.assertEqual(b.snapshot(),old)
    def test_native_bad_headers_tables_counts_and_generation_never_free(self):
        for b in self.benches():
            p=b.alloc();self.assertTrue(p)
            targets=((p-32,0,2),(p-28,0xffffffff,4),(p-28,5017,4),(p-4,38,4),(b.idxs+11,5,1),(b.parents+b.slot*4,PARENT+4,4),(b.counts+22,0,2),(b.heap+0x1c,b.heap+0x200000,4))
            for address,value,width in targets:
                original=b.get(address,width);b.put(address,value,width);old=b.snapshot();start=len(b.calls)
                self.assertEqual(b.free(),HOLD);self.assertEqual(b.snapshot(),old)
                self.assertFalse(any(a==FREE for a,args in b.calls[start:]));b.put(address,original,width)
            old=b.snapshot();self.assertEqual(b.free(2),REFUSED);self.assertEqual(b.snapshot(),old)
            self.assertEqual(b.free(),RELEASED)
    def test_native_move_rejects_full_allocation_header_and_suffix_aliases(self):
        for b in self.benches():
            p=b.alloc(128);self.assertTrue(p)
            for dst in (p-36,p-32,p-28,p-16,p-4,p+92,TOKEN+4,BASE,b.heap):
                old=b.snapshot();self.assertEqual(b.move(dst),REFUSED);self.assertEqual(b.snapshot(),old)
            self.assertEqual(b.move(p+64),RELEASED)
            self.assertEqual(b.free(t=p+64),HOLD);self.assertEqual(b.move(TOKEN,p+64),RELEASED)
            self.assertEqual(b.free(),RELEASED)
    def test_native_admission_limits_count_overflow_ime_and_irq(self):
        for b in self.benches():
            for n,g in ((0,1),(0x4001,1),(0xffffffff,1),(1,0)):
                old=b.snapshot();start=len(b.calls);self.assertEqual(b.alloc(n,g),0);self.assertEqual(b.snapshot(),old)
                self.assertFalse(any(a==ALLOC for a,args in b.calls[start:]))
            for mask,ime in ((128,1),(0,0),(128,0)):
                b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime);old=b.snapshot()
                self.assertEqual(b.alloc(),0);self.assertEqual(b.snapshot(),old)
            b.u.reg_write(UC_ARM_REG_CPSR,0x5f);b.put(IME,1);b.put(b.counts+22,65535,2);old=b.snapshot()
            self.assertEqual(b.alloc(),0);self.assertEqual(b.snapshot(),old)
            b.put(b.counts+22,0,2);self.assertTrue(b.alloc());self.assertEqual(b.free(),RELEASED)
    def test_native_successful_heap_alloc_control_matches_footprint_and_count(self):
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                owned=PersistentBench(self.compiled,sections);normal=PersistentBench(self.compiled,sections)
                before=owned.totals();p=owned.alloc(5001)
                normal.normal_control=True;q=normal.address(0x0201aa8d,11,5001);normal.normal_control=False
                self.assertTrue(p and q);self.assertEqual(p,q)
                self.assertEqual(owned.totals(),normal.totals())
                self.assertEqual(owned.get(p-28),normal.get(q-28))
                self.assertEqual(owned.get(p-4,1),normal.get(q-4,1))
                self.assertEqual(owned.get(owned.counts+22,2),normal.get(normal.counts+22,2))
                self.assertEqual(owned.free(),RELEASED);normal.normal_control=True;normal.address(0x0201ab0d,q);normal.normal_control=False
                self.assertEqual(owned.totals(),before);self.assertEqual(normal.totals(),before)
    def test_native_absorbed_slack_is_owned_and_released_with_exact_header_extent(self):
        for b in self.benches():
            before=b.totals()
            for generation,slack in enumerate((0,4,8,12,16),1):
                # NNS does not split a trailing remainder smaller than20B.
                filler=b.address(ALLOC,b.heap,before[0]-(128+16+slack)-16,4)
                self.assertTrue(filler);p=b.alloc(128,generation);self.assertTrue(p)
                self.assertEqual(b.get(p-28),144+slack);self.assertEqual(b.totals(),(0,0,0))
                old=b.snapshot();self.assertEqual(b.move(p+128),REFUSED);self.assertEqual(b.snapshot(),old)
                self.assertEqual(b.free(generation),RELEASED);b.address(FREE,b.heap,filler)
                self.assertEqual(b.totals(),before)
    def test_native_publication_mask_payload_restore_and_count_highwater(self):
        for b in self.benches():
            b.put(b.counts+22,0x1234,2);start=len(b.store_contexts);p=b.alloc(65);self.assertTrue(p)
            stores=b.store_contexts[start:]
            payload=[c for c in stores if p<=c[0]<p+68]
            native=[c for c in stores if b.heap<=c[0]<p or c[0]==b.counts+22]
            self.assertTrue(payload and native)
            self.assertTrue(all(not c[4]&128 for c in payload))
            self.assertTrue(all(c[4]&128 for c in native))
            self.assertEqual(b.get(b.counts+22,2),0x1235);self.assertEqual(b.free(),RELEASED)
            self.assertEqual(b.get(b.counts+22,2),0x1234)
    def test_actual_native_semantics_kill_eight_compile_valid_omissions(self):
        mutants=(
            ('w[3]=11;','w[3]=38;','GF heap ID'),
            ('++HINFO->counts[11];','++HINFO->counts[6];','count by ID'),
            ('*(HWord *)(result+j)=0;','(void)(result+j);','payload zero'),
            ('HRESTORE(irq);\n    if(result)','(void)irq;\n    if(result)','restore I'),
            ('s[j]=0;','(void)s[j];','retire move source'),
            ('HFREE((void *)t->handle,(void *)(p-16));','(void)p;','native free'),
            ('if(pover((HWord)t,sizeof(*t),p-32,n+16))goto done;','(void)n;','token before free'),
            ('t->generation==g;','t->generation!=0;','generation identity'))
        for old,new,label in mutants:
            with tempfile.TemporaryDirectory(prefix='persistent-mutant-') as d:
                candidate=compile_persistent(Path(d),(old,new))
                for lang,sections in self.sections.items():
                    with self.subTest(mutant=label,lang=lang):
                        b=PersistentBench(candidate,sections);before=b.totals()
                        # Preserve the free-node header, poison available payload.
                        b.u.mem_write(b.heap+0x48,b'\x5a'*0x4000)
                        def scenario():
                            p=b.alloc();self.assertTrue(p)
                            self.assertEqual(bytes(b.u.mem_read(p,5000)),bytes(5000))
                            self.assertEqual(b.get(p-4,4),11);self.assertEqual(b.get(b.counts+22,2),1)
                            self.assertEqual(b.free(g=2),REFUSED)
                            self.assertEqual(b.move(p),RELEASED);self.assertEqual(b.token(),bytes(SIZE))
                            self.assertEqual(b.free(t=p),HOLD);self.assertEqual(b.move(TOKEN,p),RELEASED)
                            self.assertEqual(b.free(),RELEASED);self.assertEqual(b.totals(),before)
                        with self.assertRaises(AssertionError):scenario()
    def test_configured_native_durable_owner_whole_lifetime_and_explicit_moves(self):
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                b=PersistentBench(self.configured,sections,token=0x023d7b20)
                before=b.totals();metadata=b.metadata()
                b.u.mem_write(0x023d7b10,b'\x91'*16);b.u.mem_write(0x023d7b48,b'\x39'*16)
                for g,n in enumerate((1,5001,0x4000),1):
                    p=b.alloc(n,g);self.assertTrue(p);rounded=(n+3)&~3
                    self.assertEqual(b.get(p-32,2),0x5544)
                    self.assertEqual(bytes(b.u.mem_read(p-16,16)),bytes(12)+b'\x0b\0\0\0')
                    self.assertEqual(bytes(b.u.mem_read(p,rounded)),bytes(rounded))
                    self.assertEqual(b.get(b.counts+22,2),1)
                    self.assertEqual(b.free(g),RELEASED);self.assertEqual(b.totals(),before)
                    self.assertEqual(b.metadata(),metadata)
                # Existing MOVE remains valid for this exact configured source
                # and destination, including root ownership and free refusal.
                p=b.alloc(5000,4);self.assertTrue(p);self.assertEqual(b.move(p,g=4),RELEASED)
                self.assertEqual(b.token(),bytes(40));self.assertEqual(b.free(4,t=p),HOLD)
                self.assertEqual(b.move(0x023d7b20,p,4),RELEASED)
                self.assertEqual(b.free(4),RELEASED);self.assertEqual(b.totals(),before)
                old=b.snapshot();self.assertEqual(b.alloc(g=4),0);self.assertEqual(b.snapshot(),old)
                self.assertEqual(bytes(b.u.mem_read(0x023d7b10,16)),b'\x91'*16)
                self.assertEqual(bytes(b.u.mem_read(0x023d7b48,16)),b'\x39'*16)
    def test_configured_native_ordinary_null_and_impossible_hold_outlive_callback_stack(self):
        for lang,sections in self.sections.items():
            for returned in (None,0xfffffff0,0x02200000):
                with self.subTest(lang=lang,returned=returned):
                    b=PersistentBench(self.configured,sections,token=0x023d7b20)
                    before=b.totals();blocks=[]
                    if returned is None:
                        # A real lower NULL from actual exhausted native NNS.
                        while True:
                            p=b.address(ALLOC,b.heap,0x3000,4)
                            if not p:break
                            blocks.append(p)
                        # Ensure the smaller callback request cannot fit.
                        if b.totals()[1]>=5016:
                            blocks.append(b.address(ALLOC,b.heap,b.totals()[1],4))
                        self.assertLess(b.totals()[1],5016)
                    else:b.return_fault=returned # explicitly impossible lower-output seam
                    old=b.snapshot();self.assertEqual(b.call('bootstrap_callback_probe',0,1),0)
                    retained=b.token();self.assertEqual(b.metadata(),old[1]);self.assertEqual(b.snapshot()[2],old[2])
                    self.assertEqual(retained==old[0],returned is None)
                    if returned is not None:
                        self.assertEqual((b.get(0x023d7b20),b.get(0x023d7b24),b.get(0x023d7b28)),(0x48504955,0x023d7b20,1))
                    # Overwrite all former caller stack storage, including the
                    # ordinary bootstrap SYS slot. The authoritative token is
                    # still outside it and repeated C callbacks return safely.
                    b.u.mem_write(0x027e0080,b'\x6c'*(STACK-0x027e0080))
                    for _ in range(4):
                        self.assertEqual(b.call('bootstrap_callback_probe',1,1),REFUSED if returned is None else HOLD)
                        self.assertEqual(b.call('bootstrap_callback_probe',2,1),REFUSED if returned is None else HOLD)
                        self.assertEqual(b.call('bootstrap_callback_probe',0,2),0)
                        self.assertEqual(b.snapshot(),(retained,old[1],old[2]))
                    self.assertFalse(any(a in (FREE,DESTROY) for a,args in b.calls))
                    if returned is None:
                        for q in reversed(blocks):self.assertTrue(q);b.address(FREE,b.heap,q)
                        self.assertEqual(b.totals(),before)
    def test_configured_native_slot_keeps_validation_and_count_guards(self):
        for lang,sections in self.sections.items():
            with self.subTest(lang=lang):
                b=PersistentBench(self.configured,sections,token=0x023d7b20)
                before=b.totals();p=b.alloc();self.assertTrue(p)
                for address,value,width in ((p-32,0,2),(p-28,5017,4),(p-4,38,4),
                    (b.idxs+11,5,1),(b.parents+b.slot*4,PARENT+4,4),(b.counts+22,0,2)):
                    original=b.get(address,width);b.put(address,value,width);old=b.snapshot();start=len(b.calls)
                    self.assertEqual(b.free(),HOLD);self.assertEqual(b.move(TOKEN),HOLD)
                    self.assertEqual(b.snapshot(),old);self.assertFalse(any(a==FREE for a,args in b.calls[start:]))
                    b.put(address,original,width)
                self.assertEqual(b.free(),RELEASED);self.assertEqual(b.totals(),before)
    def test_retained_en_capture_heap11_preserves_all_preexisting_owned_blocks(self):
        path=SOURCE.parent/'local/notes/ui-1.3.1-validation/native-heap-before/field-mainram.bin'
        if not path.is_file():
            if os.environ.get('SGP_UI_PERSISTENT_REQUIRE_INPUTS')=='1':self.fail('missing retained EN heap capture')
            self.skipTest('retained EN heap capture unavailable')
        data=path.read_bytes()
        self.assertEqual(len(data),0x400000)
        self.assertEqual(hashlib.sha256(data).hexdigest(),'689456c6699c06a773837f1c673eaa6e5f264fb54708513b4e67484723232c5c')
        b=PersistentBench(self.compiled,self.sections['EN'])
        b.u.mem_write(0x0226ec40,data[0x26ec40:0x3c0000]);b.u.mem_write(META,data[META-0x02000000:META-0x02000000+28])
        b.handles,b.parents,b.raws,b.counts,b.idxs=struct.unpack_from('<5I',data,META-0x02000000)
        b.slot=b.get(b.idxs+11,1);b.heap=b.get(b.handles+4*b.slot)
        b.allowed=[(b.handles,b.handles+824),(TOKEN,TOKEN+SIZE),(b.heap,b.heap+HEAP11_BYTES)]
        self.assertEqual((b.slot,b.heap,b.get(b.counts+22,2),b.totals()),(4,0x022a01ec,12,(87640,87640,1)))
        # Preserve every old used block including its GF wrapper/payload; links
        # in the native NNS headers necessarily change while the new root lives.
        node=b.get(b.heap+0x2c);owned=[]
        while node:
            self.assertLess(len(owned),128);n=b.get(node+4)
            owned.append((node+16,bytes(b.u.mem_read(node+16,n))));node=b.get(node+12)
        self.assertEqual(len(owned),12)
        self.assertEqual(b.get(b.counts+150,2),1);metadata=b.metadata()
        before=b.totals();p=b.alloc(0x4000);self.assertTrue(p)
        self.assertEqual(b.get(b.counts+22,2),13);self.assertEqual(before[0]-b.totals()[0],0x4020)
        for a,expected in owned:self.assertEqual(bytes(b.u.mem_read(a,len(expected))),expected)
        self.assertEqual(b.move(p),RELEASED);self.assertEqual(b.move(TOKEN,p),RELEASED)
        self.assertEqual(b.free(),RELEASED);self.assertEqual(b.totals(),before);self.assertEqual(b.get(b.counts+22,2),12)
        for a,expected in owned:self.assertEqual(bytes(b.u.mem_read(a,len(expected))),expected)
        self.assertEqual(b.metadata(),metadata);self.assertEqual(b.get(b.counts+150,2),1)
if __name__=='__main__':unittest.main()
