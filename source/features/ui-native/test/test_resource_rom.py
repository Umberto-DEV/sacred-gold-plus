"""Class B PREPARED native FS/heap execution, not a boot or hardware proof.
Canonical FAT/FNT in RAM, file167 points to an in-memory compiler replacement.
Only CARD transport/arbitration and explicitly requested SleepThread scheduling
are seamed; callback, Notify, path lookup, dispatch and Close are actual ARM9.
"""
import hashlib,os,tempfile,unittest
from resource_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
from test_heap_rom import NativeHeapBench,ROM_PINS,PINS
FS_PINS=((0x020d6864,0x1e74,'a9bfe583c461b861898dc3c616cd6efe4b4f33822813ed291789861d2614a834'),
 (INIT,0x4b0,'85827bd31be4e7418e46bf4715e60ca1d4287b4243ff129973febadeac343b0c'),
 (0x020d6864,0x1ac,'43ea8c47ceb4209672b66ec1e12c4a1634e460b0ea35fabd6039568d41dbefaa'),
 (0x0210e124,0x24,'a2a3fe2a981c9967141752f3228d54c59d73c639339443bbe0ef04f13319d287'),
 (0x020d4a50,0x180,'369b6f2e559f13da0a9ba7a741ebf8ca3213db866a8f4eb97460809d8b54b86e'),
 (0x020d1ecc,0x68,'25c7d621d6b4d855be6828b9ec8d98162df8ecdda5a22db405caf344aa4102db'),
 (0x020d1e7c,0x50,'de1ca8ee4bb90cf3b34dfd1ec03e32970669ffb5db5ea6338df02598dd4e137c'),
 (CPSR,12,'9c3668b7089a9adbfd85879f1c4689241aea4f8bd7af68fb26cdf12657eda6ee'),
 (0x0200e398,0x1340,'0ef36980ab5842567f38a3ac14237764bca7380a13c09ea5893e654a0e8b831b'))
TRANSPORT,LOCK,UNLOCK,PULLED,SLEEP,CALLBACK=0x020dd754,0x020dc96c,0x020dc988,0x020ddb24,0x020d1e7c,0x020d84a0
CALLBACK_RETURN=STOP+0x40
VIRTUAL_ROM=0x10000000
class NativeResourceBench(ResourceBench,NativeHeapBench):
    def __init__(self,compiled,fixture):
        self.fs_calls=[];self.visited=set();self.fs_active=[];self.fs_metrics=[];self.callback_pending=None;self.callback_return=None
        self.shorten_member=False;self.return_fault=None;self.return_injection=None;self.fail_openfast=False;self.delayed=False;self.never=False;self.pulled=False;self.partial=False;self.sleeps=0;self.transports=[]
        self.raw,self.config,self.fat,self.fnt,sections=fixture
        NativeHeapBench.__init__(self,compiled,sections)
        self.allowed.extend(((READER,READER+R_SIZE),(LEASE,LEASE+12),(SLICE,SLICE+8),(ARC+12,ARC+40)))
        self.u.mem_write(CONFIG,self.config);self.archive_fixture()
        self.u.mem_write(FAT,self.fat);self.u.mem_write(FNT,self.fnt)
        self.put(FAT+167*8,VIRTUAL_ROM);self.put(FAT+167*8+4,VIRTUAL_ROM+len(self.raw))
        self.put(0x021e3628,ARC);self.put(0x021e362c,ARC);self.put(0x021e3630,0);self.put(0x021e3634,0)
        self.put(0x021e363c,0x42);self.put(0x021e3640,0)
        self.u.mem_write(0x0211188c,bytes(0xb0))
        assert self.create()==1
        self.guarded_memory();self.guards_ready=True
    def native_allowed(self,p):
        return HeapBench.native_allowed(self,p) or 0x020d6864<=p<0x020d86d8 or 0x020d4a50<=p<0x020d4bd0 or 0x020d1ecc<=p<0x020d1f34 or CPSR<=p<CPSR+12
    def begin_callback(self,callback,arg,ret):
        assert callback==CALLBACK and arg==ARC
        assert self.callback_return is None
        self.callback_return=ret;self.u.reg_write(UC_ARM_REG_R0,arg)
        self.u.reg_write(UC_ARM_REG_LR,CALLBACK_RETURN);self.u.reg_write(UC_ARM_REG_PC,callback)
    def hook(self,u,p,n,data):
        self.visited.add(p)
        if self.return_injection and p==self.return_injection[0]:
            kind=self.return_injection[1];self.return_injection=None
            if kind=='busy':self.put(READER+12,self.get(READER+12)|1)
            elif kind=='queue':self.put(READER,READER)
            else:self.put(ARC+0x54,0)
        sp=u.reg_read(UC_ARM_REG_SP)
        for record in self.fs_active:record[4]=min(record[4],sp)
        if self.fs_active and p==self.fs_active[-1][1]:
            a,ret,start,entry,low=self.fs_active.pop();self.fs_metrics.append((a,self.instructions-start,entry-low))
        if p==0x020d8208 and self.fail_openfast:self.put(ARC+0x1c,self.get(ARC+0x1c)|0x80)
        if p==CALLBACK_RETURN:
            assert self.callback_return is not None
            ret=self.callback_return;self.callback_return=None;self.ret(0);u.reg_write(UC_ARM_REG_PC,ret);return
        if p in (LOCK,UNLOCK,PULLED):
            self.instructions+=1;self.ret(int(self.pulled) if p==PULLED else 0);return
        if p==TRANSPORT:
            self.instructions+=1
            dma,pos,dst,length=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            sp=u.reg_read(UC_ARM_REG_SP);cb,arg,async_=struct.unpack('<3I',bytes(u.mem_read(sp,12)))
            assert dma==0 and async_==1 and VIRTUAL_ROM<=pos<=pos+length<=VIRTUAL_ROM+len(self.raw)
            assert (dst==READER+80 and length<=468) or (dst==self.root() and length<=len(self.raw)-35380)
            assert self.get(ARC+0x1c)&0x200 and self.get(ARC+0x24)==READER
            self.transports.append((pos,dst,length));count=max(0,length-8) if self.partial else length
            u.mem_write(dst,self.raw[pos-VIRTUAL_ROM:pos-VIRTUAL_ROM+count])
            if self.delayed or self.never:self.callback_pending=(cb,arg);self.ret(0)
            else:self.begin_callback(cb,arg,u.reg_read(UC_ARM_REG_LR))
            return
        if p==SLEEP:
            self.instructions+=1;self.sleeps+=1
            assert self.delayed or self.never,'undeclared scheduler seam'
            assert self.callback_pending is not None and self.get(READER+12)&1
            assert self.get(ARC+0x24)==READER and self.get(ARC+0x1c)&0x200
            if self.never:
                # Finite watchdog for an externally never-completing synchronous
                # call. Leave native stack/ownership intact; it is NOT an error.
                if self.sleeps==3:u.emu_stop();return
                self.ret(0);return
            cb,arg=self.callback_pending;self.callback_pending=None
            self.begin_callback(cb,arg,u.reg_read(UC_ARM_REG_LR));return
        if p in (INIT,OPEN,READ,CLOSE,SEEK) and u.reg_read(UC_ARM_REG_R0)==READER:
            if p==READ and self.shorten_member and u.reg_read(UC_ARM_REG_R2)>468:
                self.put(READER+40,self.get(READER+44)+u.reg_read(UC_ARM_REG_R2)-4)
            if p==READ and self.return_fault:self.return_injection=(u.reg_read(UC_ARM_REG_LR)&~1,self.return_fault)
            assert self.get(IME)==1 and not u.reg_read(UC_ARM_REG_CPSR)&128, f'FS boundary {p:08x} CPSR={u.reg_read(UC_ARM_REG_CPSR):08x}'
            assert not u.reg_read(UC_ARM_REG_CPSR)&32
            self.fs_calls.append((p,*[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]))
            self.fs_active.append([p,u.reg_read(UC_ARM_REG_LR)&~1,self.instructions,sp,sp])
        HeapBench.hook(self,u,p,n,data)
    def address(self,p,*args):
        result=super().address(p,*args)
        if self.fs_active and self.fs_active[-1][1]==STOP:
            a,ret,start,entry,low=self.fs_active.pop();self.fs_metrics.append((a,self.instructions-start,entry-low))
        return result
    def queues_clear(self):
        return all(self.get(READER+o)==0 for o in (0,4,24,28)) and not self.get(READER+12)&0x4f and self.get(ARC+0x24)==0 and not self.get(ARC+0x1c)&0x310
class ResourceRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        paths={l:Path(os.environ.get('SGP_UI_RESOURCE_READER_'+l,str(canonical/f'candidate-v4-{l}.nds'))) for l in ROM_PINS}
        missing=[l for l,p in paths.items() if not p.is_file()]
        if missing:
            msg='canonical V4 resource-reader native inputs missing: '+','.join(missing)
            if os.environ.get('SGP_UI_RESOURCE_READER_REQUIRE_INPUTS')=='1':raise AssertionError(msg)
            raise unittest.SkipTest(msg)
        from ndspy.rom import NintendoDSRom
        cls.fixtures={}
        for lang,path in paths.items():
            v4=path.read_bytes();assert (len(v4),hashlib.sha256(v4).hexdigest())==ROM_PINS[lang]
            rom=NintendoDSRom(v4);sections=ndspy_load_arm9_sicuro(rom).sections
            for a,n,want in (*PINS,*FS_PINS):
                s=next(s for s in sections if s.ramAddress<=a<a+n<=s.ramAddress+len(s.data))
                assert hashlib.sha256(bytes(s.data[a-s.ramAddress:a-s.ramAddress+n])).hexdigest()==want,f'{lang} guard {a:08x}'
            fnt_at,fnt_n,fat_at,fat_n=struct.unpack_from('<4I',v4,0x40)
            raw,receipt=ui_resource.compile_resource(v4,{1:(1,0xe000,2,65535)})
            cls.fixtures[lang]=(raw,bytes.fromhex(receipt['config_hex']),v4[fat_at:fat_at+fat_n],v4[fnt_at:fnt_at+fnt_n],[(s.ramAddress,bytes(s.data)) for s in sections if 0x02000000<=s.ramAddress<0x02400000])
            del v4,rom,sections
        cls.temp=tempfile.TemporaryDirectory(prefix='resource-b-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_resource(Path(cls.temp.name))
    def benches(self):
        for lang,f in self.fixtures.items():yield lang,NativeResourceBench(self.compiled,f)
    def test_actual_open_path_fat_dispatch_read_callback_close_and_views_both_languages(self):
        for lang,b in self.benches():
            self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),OK)
            self.assertTrue(b.queues_clear());self.assertEqual(b.get(READER+8),0)
            for address in (INIT,OPEN,READ,SEEK,CLOSE,0x020d7fc0,0x020d7788,0x020d68c0,0x020d6864,0x020d7340,0x020d73c0,CALLBACK,0x020d7edc,0x020d4a50,0x020d1ecc):self.assertIn(address,b.visited)
            self.assertEqual(b.get(READER+72),0);self.assertEqual(b.get(READER+76),0)
            self.assertEqual(bytes(b.u.mem_read(b.root(),len(b.raw)-35380)),b.raw[35380:])
            self.assertEqual(b.call('ui_res_acquire',READER,LEASE,1),1)
            self.assertEqual(b.call('ui_res_glyphs',LEASE,SLICE),1)
            self.assertEqual(b.get(SLICE+4),32576)
            self.assertEqual(b.call('ui_res_release',READER),0)
            b.put(0x0211188c,0x02111890);b.put(0x02111890+0x9c,0x02361000);b.put(0x02361010,b.root()+12288)
            self.assertEqual(b.call('ui_res_drop',LEASE),1)
            self.assertEqual(b.call('ui_res_release',READER),0)
            b.put(0x02361010,0)
            self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_actual_unloading_close_refusal_four_and_five_steps_then_recovery(self):
        for lang,f in self.fixtures.items():
            for attempts in (4,5):
                b=NativeResourceBench(self.compiled,f);b.start()
                for _ in range(3):self.assertEqual(b.step(),MORE)
                root=b.root();b.put(ARC+0x1c,b.get(ARC+0x1c)|0x80)
                for _ in range(attempts):
                    count=len(b.fs_calls);self.assertEqual(b.step(),MORE)
                    self.assertEqual(len(b.fs_calls),count+1)
                    self.assertEqual(b.phase(),P_CLOSE);self.assertEqual(b.root(),root)
                    self.assertEqual(b.get(READER+8),ARC);self.assertEqual(b.get(READER+12),0x10)
                    self.assertEqual(b.get(READER+20),3);self.assertTrue(b.queues_clear())
                    self.assertEqual(b.call('ui_res_release',READER),0)
                    self.assertFalse(any(a==FREE for a,_ in b.calls))
                b.call('ui_res_cancel',READER);self.assertEqual(b.step(),MORE)
                b.put(ARC+0x1c,b.get(ARC+0x1c)&~0x80)
                self.assertEqual(b.step(),ERROR);self.assertTrue(b.queues_clear())
                self.assertEqual(b.get(READER+8),0);self.assertEqual(b.call('ui_res_release',READER),1)
                self.assertEqual(b.destroy(),1)
    def test_actual_pulled_read_error_advances_position_and_close_still_succeeds(self):
        for lang,f in self.fixtures.items():
            for member in (False,True):
                b=NativeResourceBench(self.compiled,f);b.start();b.step()
                if member:b.step()
                b.pulled=True;self.assertEqual(b.step(),MORE);self.assertEqual(b.phase(),P_CLOSE)
                self.assertEqual(b.get(READER+20),5)
                self.assertGreater(b.get(READER+44),b.get(READER+36))
                self.assertEqual(b.step(),ERROR);self.assertTrue(b.queues_clear())
                self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_actual_missing_archive_bad_fat_and_eof_and_seek_clamp(self):
        for lang,f in self.fixtures.items():
            for fault in ('missing','path','openfast','fat','eof','membereof','seek'):
                b=NativeResourceBench(self.compiled,f);b.start()
                if fault=='missing':b.put(0x021e3628,0)
                if fault=='path':
                    at=b.fnt.find(b'\x81a');self.assertGreaterEqual(at,0);b.u.mem_write(FNT+at+1,b'z')
                if fault=='openfast':b.fail_openfast=True
                if fault=='fat':b.put(FAT+167*8+4,VIRTUAL_ROM+len(b.raw)+4)
                b.step()
                if fault in ('missing','path','openfast'):
                    self.assertEqual(b.phase(),P_FAILED);self.assertEqual(b.get(READER+8),ARC if fault=='openfast' else 0)
                    self.assertTrue(b.queues_clear())
                    self.assertFalse(any(p==CLOSE for p,*_ in b.fs_calls))
                elif fault=='fat':self.assertEqual(b.phase(),P_CLOSE);self.assertEqual(b.step(),ERROR)
                elif fault=='eof':
                    b.put(READER+40,b.get(READER+36)+464)
                    self.assertEqual(b.step(),MORE);self.assertEqual(b.phase(),P_CLOSE);self.assertEqual(b.step(),ERROR)
                elif fault=='membereof':
                    b.step();b.shorten_member=True;b.step();self.assertEqual(b.phase(),P_CLOSE);self.assertEqual(b.step(),ERROR)
                else:
                    self.assertEqual(b.address(SEEK,READER,len(b.raw)+4,0),1)
                    self.assertEqual(b.get(READER+44),b.get(READER+40),'actual Seek TRUE clamps')
                    self.assertEqual(b.address(SEEK,READER,0,0),1)
                    b.step();b.put(READER+40,b.get(READER+36)+35379)
                    before=len(b.fs_calls);b.step();self.assertEqual(b.phase(),P_CLOSE)
                    self.assertEqual(len(b.fs_calls),before,'checked span rejects before seek/read')
                    self.assertEqual(b.step(),ERROR)
                self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_actual_delayed_callback_with_declared_sleep_scheduler_seam(self):
        for lang,b in self.benches():
            b.delayed=True;self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),OK)
            self.assertEqual(b.sleeps,2);self.assertTrue(b.queues_clear());self.assertIsNone(b.callback_pending)
            self.assertIn(CALLBACK,b.visited);self.assertIn(0x020d7edc,b.visited)
            self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_never_completing_transport_is_expected_native_hang_not_returned_failure(self):
        for lang,b in self.benches():
            b.start();b.step();b.never=True
            with self.assertRaisesRegex(AssertionError,'finite instruction limit'):b.step()
            self.assertEqual(b.sleeps,3);self.assertIsNotNone(b.callback_pending)
            self.assertEqual(b.phase(),P_PREFIX);self.assertEqual(b.get(READER+OWN),1)
            self.assertTrue(b.get(READER+12)&1);self.assertNotEqual(b.u.reg_read(UC_ARM_REG_SP),STACK)
            self.assertFalse(any(p==CLOSE for p,*_ in b.fs_calls));self.assertFalse(any(p==FREE for p,a in b.calls))
            # The entire in-process Unicorn fixture is discarded here; never
            # call another entry or pretend to cancel a native call's stack.
    def test_actual_partial_success_transport_rejected_by_whole_member_crc(self):
        for lang,b in self.benches():
            b.start();b.step();b.step();b.partial=True;b.step();self.assertEqual(b.phase(),P_CLOSE)
            self.assertEqual(b.step(),MORE);self.assertEqual(b.finish(),ERROR)
            self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),0)
            self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_native_loaded_table_admission_and_entry_masks_preserve_state(self):
        for lang,f in self.fixtures.items():
            for off,val in ((0x1c,3),(0x48,0x020d8580),(0x50,0x020d84c4),(0x54,0),(0x58,0)):
                b=NativeResourceBench(self.compiled,f);b.call('ui_res_init',READER);b.put(ARC+off,val)
                self.assertEqual(b.start_duplicate(),ERROR);self.assertFalse(b.fs_calls)
            for mask,ime in ((128,1),(0,0)):
                b=NativeResourceBench(self.compiled,f);b.call('ui_res_init',READER)
                b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
                self.assertEqual(b.start_duplicate(),ERROR);self.assertFalse(b.fs_calls)
    def test_observed_fs_table_arena_can_cross_caller_output_ceiling(self):
        for lang,b in self.benches():
            fat=0x023be580;fnt=fat+4104
            b.u.mem_write(fat,bytes(b.u.mem_read(FAT,4104)))
            b.u.mem_write(fnt,bytes(b.u.mem_read(FNT,2902)))
            b.put(ARC+0x2c,fat);b.put(ARC+0x34,fnt);b.put(ARC+0x44,0x023be564)
            self.assertEqual(b.start(),MORE)
            self.assertEqual(b.finish(),OK)
            self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_actual_native_returns_then_busy_queue_and_changed_tuple_hold_owners(self):
        for lang,f in self.fixtures.items():
            for address,value in ((READER+12,0x11),(READER,READER),(READER+24,READER),(ARC+0x54,0)):
                b=NativeResourceBench(self.compiled,f);b.start();b.step();b.step();b.step()
                root=b.root();b.put(address,value);calls=len(b.fs_calls)
                self.assertEqual(b.step(),HELD);b.call('ui_res_cancel',READER)
                self.assertEqual(b.step(),HELD);self.assertEqual(len(b.fs_calls),calls)
                self.assertEqual(b.call('ui_res_release',READER),0);self.assertEqual(b.root(),root)
                self.assertFalse(any(a==FREE for a,_ in b.calls))
        for lang,f in self.fixtures.items():
            for fault in ('busy','queue','tuple'):
                b=NativeResourceBench(self.compiled,f);b.start();b.step();b.return_fault=fault
                self.assertEqual(b.step(),HELD,'post-native-return fault retains ownership')
                self.assertEqual(b.root(),0,'no allocation after uncertain return')
                self.assertEqual(b.call('ui_res_release',READER),0)
                self.assertFalse(any(a==FREE for a,_ in b.calls))
    def test_actual_native_behavior_kills_stack_file_and_failed_close_reinit_mutants(self):
        mutants=(('ok=ROPEN(r->fs,(const char *)full);',
                  'RWord local[20];for(RWord i=0;i<20;++i)local[i]=r->fs[i];ok=ROPEN(local,(const char *)full);','stackfile'),
                 ('return UI_RES_MORE;\n        }\n        if(r->fs[2]',
                  'RINIT(r->fs);return UI_RES_MORE;\n        }\n        if(r->fs[2]','reinit'))
        for old,new,kind in mutants:
            with tempfile.TemporaryDirectory(prefix='resource-native-mutant-') as d:
                compiled=compile_resource(Path(d),(old,new))
                for lang,f in self.fixtures.items():
                    with self.subTest(mutant=kind,lang=lang):
                        b=NativeResourceBench(compiled,f);b.start()
                        def scenario():
                            self.assertEqual(b.step(),MORE,'open remains owned in app record')
                            self.assertEqual(b.phase(),P_PREFIX)
                            if kind=='reinit':
                                b.step();b.step();b.put(ARC+0x1c,b.get(ARC+0x1c)|0x80)
                                self.assertEqual(b.step(),MORE)
                                self.assertEqual(b.get(READER+8),ARC,'failed close retains archive')
                                self.assertEqual(b.get(READER+12),0x10,'failed close retains IS_FILE')
                        with self.assertRaisesRegex(AssertionError,'open remains owned in app record|failed close retains archive|failed close retains IS_FILE'):scenario()
if __name__=='__main__':
    import json
    stats={'calls':0,'max_combined_stack':0,'max_call_instructions':0,'crc_step_max_instructions':0,'text_step_max_instructions':0,'fs':{}}
    original=NativeResourceBench.address
    def measured(self,p,*args):
        before=len(self.fs_metrics);phase=self.get(READER+PHASE);verify=self.get(READER+652)
        result=original(self,p,*args)
        if self.code!=ResourceRomTests.compiled[0]:return result
        _,stack,cost=self.metrics[-1];stats['calls']+=1
        stats['max_combined_stack']=max(stats['max_combined_stack'],stack)
        stats['max_call_instructions']=max(stats['max_call_instructions'],cost)
        if p==self.symbols.get('ui_res_step') and phase==P_VERIFY:
            key='text_step_max_instructions' if verify==2 else 'crc_step_max_instructions'
            stats[key]=max(stats[key],cost)
        for a,n,depth in self.fs_metrics[before:]:
            row=stats['fs'].setdefault(f'{a:08x}',[0,0,0]);row[0]+=1;row[1]=max(row[1],n);row[2]=max(row[2],depth)
        return result
    NativeResourceBench.address=measured
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ResourceRomTests))
    print(json.dumps(stats,indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
