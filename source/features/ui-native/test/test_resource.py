"""Class A: compiled reader/parser/checked heap; explicitly seamed FS calls."""
import tempfile,unittest
from resource_bench import *
class ResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='resource-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_resource(Path(cls.temp.name))
    def test_supported_locale_ids_load_and_unknown_ids_refuse_before_io(self):
        for locale in range(5):
            with self.subTest(locale=locale):
                raw,cfg=synthetic();raw=bytearray(raw);cfg=bytearray(cfg)
                struct.pack_into('<I',raw,35380+12,locale)
                struct.pack_into('<I',cfg,8,locale)
                struct.pack_into('<I',cfg,40,zlib.crc32(raw[35380:]))
                b=ResourceBench(self.compiled,bytes(raw),bytes(cfg))
                self.assertEqual(b.start(),MORE)
                self.assertEqual(b.finish(),OK)
        for locale in (5,0xffffffff):
            raw,cfg=synthetic();cfg=bytearray(cfg);struct.pack_into('<I',cfg,8,locale)
            b=ResourceBench(self.compiled,raw,bytes(cfg))
            self.assertEqual(b.start(),ERROR)
            self.assertEqual(b.fs_calls,[])
    def test_verify_pump_preserves_output_and_stops_on_failed_close_or_deferral(self):
        self.assertIn('ui_res_pump',self.compiled[1])
        results=[]
        for cap in (1,4):
            b=ResourceBench(self.compiled);self.assertEqual(b.start(),MORE);count=0
            while True:
                count+=1;r=b.call('ui_res_pump',READER,cap)
                if r!=MORE:break
                self.assertLess(count,100)
            self.assertEqual(r,OK)
            results.append((count,bytes(b.u.mem_read(b.root(),b.get(CONFIG+28))),b.fs_calls))
        self.assertLess(results[1][0],results[0][0]);self.assertEqual(results[0][1:],results[1][1:])
        b=ResourceBench(self.compiled);b.start()
        while b.phase()!=P_CLOSE:self.assertEqual(b.step(),MORE)
        b.close_failures=3;before=len(b.fs_calls)
        self.assertEqual(b.call('ui_res_pump',READER,4),MORE)
        self.assertEqual(len(b.fs_calls)-before,1,'failed close is retried on a later callback')
        b.put(IME,0);before=bytes(b.u.mem_read(READER,R_SIZE))
        self.assertEqual(b.call('ui_res_pump',READER,4),MORE)
        self.assertEqual(bytes(b.u.mem_read(READER,R_SIZE)),before)
    def test_valid_resource_is_closed_before_views_and_released_through_checked_heap(self):
        b=ResourceBench(self.compiled)
        self.assertEqual(b.start(),MORE)
        self.assertEqual(b.finish(),OK)
        self.assertEqual(b.phase(),READY)
        self.assertEqual(b.get(READER+8),0)
        self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),1)
        self.assertEqual(b.call('ui_res_text',LEASE,0x1001,SLICE),1)
        self.assertEqual(b.get(SLICE+4),4)
        self.assertEqual(b.call('ui_res_release',READER),0)
        self.assertEqual(b.call('ui_res_drop',LEASE),1)
        self.assertEqual(b.call('ui_res_release',READER),1)
        self.assertEqual(b.root(),0)
        self.assertEqual(b.destroy(),1)
    def test_static_ball_slice_is_bounded_leased_and_mixed_versions_refuse(self):
        b=ResourceBench(self.compiled);b.start();self.assertEqual(b.finish(),OK)
        self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),1)
        self.assertEqual(b.call('ui_res_ball',LEASE,SLICE),1)
        self.assertEqual((b.get(SLICE),b.get(SLICE+4)),(b.root()+44896,3552))
        self.assertEqual(b.call('ui_res_release',READER),0)
        self.assertEqual(b.call('ui_res_drop',LEASE),1)
        self.assertEqual(b.call('ui_res_ball',LEASE,SLICE),0)
        for index,value in ((0,0x31435255),(1,1)):
            b=ResourceBench(self.compiled);b.put(CONFIG+4*index,value)
            self.assertEqual(b.start(),ERROR);self.assertFalse(b.fs_calls)
    def test_prefix_and_io_failures_never_publish_and_always_close_successful_open(self):
        for fault in ('open','length','prefix','member','seek','alloc','prefixcrc'):
            with self.subTest(fault=fault):
                b=ResourceBench(self.compiled);b.fs_fault=fault
                if fault=='length':b.open_length=len(b.raw)+4
                if fault=='prefixcrc':b.raw=b.raw[:28]+bytes([b.raw[28]^1])+b.raw[29:]
                self.assertEqual(b.start(),MORE)
                if fault=='alloc':b.fail=ALLOC
                self.assertEqual(b.finish(),ERROR);self.assertEqual(b.phase(),P_FAILED)
                self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),0)
                self.assertEqual(sum(a==CLOSE for a,*_ in b.fs_calls),0 if fault=='open' else 1)
                if fault=='seek':self.assertEqual(sum(a==READ for a,*_ in b.fs_calls),1)
                self.assertEqual(b.call('ui_res_release',READER),1)
                self.assertEqual(b.destroy(),1)
    def test_config_fields_masks_aliases_and_duplicate_begin_refuse_before_fs(self):
        for index in range(16):
            if index in (9,10):continue
            b=ResourceBench(self.compiled);b.call('ui_res_init',READER)
            b.put(CONFIG+index*4,b.get(CONFIG+index*4)^0xffffffff)
            before=bytes(b.u.mem_read(READER,R_SIZE)),b.token(),b.metadata()
            self.assertEqual(b.call('ui_res_begin',READER,CONFIG,TOKEN),ERROR)
            self.assertEqual((bytes(b.u.mem_read(READER,R_SIZE)),b.token(),b.metadata()),before)
            self.assertFalse(b.fs_calls)
        for mask,ime in ((128,1),(0,0)):
            b=ResourceBench(self.compiled);b.call('ui_res_init',READER)
            b.u.reg_write(UC_ARM_REG_CPSR,0x5f|mask);b.put(IME,ime)
            self.assertEqual(b.call('ui_res_begin',READER,CONFIG,TOKEN),ERROR);self.assertFalse(b.fs_calls)
        b=ResourceBench(self.compiled);self.assertEqual(b.start(),MORE)
        before=bytes(b.u.mem_read(READER,R_SIZE));self.assertEqual(b.start_duplicate(),ERROR)
        self.assertEqual(bytes(b.u.mem_read(READER,R_SIZE)),before)
        b.u.mem_write(CONFIG,bytes(64));self.assertEqual(b.finish(),OK,'copied config owns lifetime')
    def test_close_false_retains_exact_root_handle_and_cancel_until_recovery(self):
        for retries in (4,5):
            b=ResourceBench(self.compiled);b.start()
            for _ in range(3):self.assertEqual(b.step(),MORE)
            root=b.root();fs=bytes(b.u.mem_read(READER,80));b.close_failures=retries
            for _ in range(retries):
                count=len(b.fs_calls);self.assertEqual(b.step(),MORE)
                self.assertEqual(len(b.fs_calls),count+1)
                self.assertEqual((b.root(),bytes(b.u.mem_read(READER,80))),(root,fs))
                self.assertEqual(b.call('ui_res_release',READER),0)
                self.assertFalse(any(a==FREE for a,_ in b.calls))
            b.call('ui_res_cancel',READER);self.assertEqual(b.step(),ERROR)
            self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
    def test_busy_queue_and_changed_archive_hold_without_retry_or_free(self):
        for address,value in ((READER+12,0x11),(READER,READER),(READER+24,READER),(ARC+0x54,0)):
            b=ResourceBench(self.compiled);b.start();b.step();b.step();b.step()
            root=b.root();b.put(address,value);count=len(b.fs_calls)
            self.assertEqual(b.step(),HELD);b.call('ui_res_cancel',READER)
            self.assertEqual(b.step(),HELD);self.assertEqual(len(b.fs_calls),count)
            self.assertEqual(b.call('ui_res_release',READER),0);self.assertEqual(b.root(),root)
    def test_cancel_at_every_phase_and_generation_do_not_publish_or_double_free(self):
        for phase in (P_OPEN,P_PREFIX,P_MEMBER,P_CLOSE,P_VERIFY,READY):
            b=ResourceBench(self.compiled);b.start()
            while b.phase()!=phase:self.assertIn(b.step(),(MORE,OK))
            b.call('ui_res_cancel',READER)
            if b.get(READER+OWN):self.assertEqual(b.step(),ERROR)
            self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),0)
            self.assertEqual(b.call('ui_res_release',READER),1)
            self.assertEqual(b.call('ui_res_release',READER),0)
            self.assertEqual(b.call('ui_res_begin',READER,CONFIG,TOKEN),MORE)
            self.assertEqual(b.get(READER+GEN),2)
            b.call('ui_res_cancel',READER);self.assertEqual(b.call('ui_res_release',READER),1)
            b.put(READER+GEN,0xffffffff);self.assertEqual(b.start_duplicate(),ERROR)
            self.assertEqual(b.destroy(),1)
    def test_trusted_whole_crc_rejects_changed_valid_text_despite_asset_identity(self):
        b=ResourceBench(self.compiled);raw=bytearray(b.raw);raw[-4]^=1;b.raw=bytes(raw)
        b.start();self.assertEqual(b.finish(),ERROR)
        self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),0)
        self.assertEqual(b.call('ui_res_release',READER),1)
    def test_fixed_header_and_text_semantics_reject_even_with_recomputed_config_crc(self):
        # The parser must reject semantic corruption independently of CRC.
        cases=[(0,0,4),(4,1,2),(6,96,2),(8,0xffffffff,4),(12,1,4),(16,0,4),(20,21,4),
               (40,0xfffffffc,4),(56,0,4),(64,0,4),(96,0,4),(100,1025,4),(104,0,4),
               (108,128,4),(112,3,4),(116,0,4),(120,16,4),(124,1,4),
               (48448,0,2),(48450,0,2),(48450,2049,2),(48452,128,4),
               (48456,1,2),(48456,0x1002,2)]
        for off,value,size in cases:
            with self.subTest(offset=off,value=value):
                b=ResourceBench(self.compiled);raw=bytearray(b.raw)
                raw[35380+off:35380+off+size]=value.to_bytes(size,'little');b.raw=bytes(raw)
                b.put(CONFIG+40,zlib.crc32(raw[35380:]));b.start()
                self.assertEqual(b.finish(),ERROR);self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),0)
                self.assertEqual(b.call('ui_res_release',READER),1)
        for value in (0,0xffff,0xf100,0xfffe,0xf0fd,0x25bc,510):
            b=ResourceBench(self.compiled);raw=bytearray(b.raw);start=struct.unpack_from('<I',raw,35380+108)[0]
            struct.pack_into('<H',raw,35380+start,value);b.raw=bytes(raw);b.put(CONFIG+40,zlib.crc32(raw[35380:]))
            b.start();self.assertEqual(b.finish(),ERROR)
    def test_init_refuses_native_heap_metadata_storage(self):
        b=ResourceBench(self.compiled);before=b.metadata()
        self.assertEqual(b.call('ui_res_init',BASE),0)
        self.assertEqual(b.metadata(),before)
    def test_output_records_cannot_alias_code_heap_tables_or_native_headers(self):
        b=ResourceBench(self.compiled);b.start();self.assertEqual(b.finish(),OK)
        self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),1)
        for target in (CONFIG,BASE,PARENT,b.get(TOKEN+16),TOKEN,READER,b.root()):
            with self.subTest(target=target):
                before=bytes(b.u.mem_read(target,8))
                self.assertEqual(b.call('ui_res_text',LEASE,1,target),0)
                self.assertEqual(bytes(b.u.mem_read(target,8)),before)
        self.assertEqual(b.call('ui_res_drop',LEASE),1)
        self.assertEqual(b.call('ui_res_release',READER),1);self.assertEqual(b.destroy(),1)
        class HeaderAliasBench(ResourceBench):
            # Diagnostic-only permission for exactly the attempted output span:
            # observe the compiled refusal instead of counting a store trap as
            # RED. All other resource/heap/store/ABI guards remain unchanged.
            def store(self,u,access,p,n,v,data):
                span=getattr(self,'diagnostic_alias',None)
                if span and span[0]<=p<p+n<=span[1]:
                    return HeapBench.store(self,u,access,p,n,v,data)
                return super().store(u,access,p,n,v,data)
        for offset in (-36,-32,-20,-16,-8,-4):
            with self.subTest(resource_allocation_prefix_offset=offset):
                b=HeaderAliasBench(self.compiled);b.start();self.assertEqual(b.finish(),OK)
                self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),1)
                root=b.root();target=root+offset;b.diagnostic_alias=(target,target+8)
                before=bytes(b.u.mem_read(root-36,40)),b.token(),b.metadata()
                writes=len(b.writes)
                self.assertEqual(b.call('ui_res_font_palette',LEASE,target),0,
                                 'known allocation prefix must reject slice output')
                self.assertEqual((bytes(b.u.mem_read(root-36,40)),b.token(),b.metadata()),before)
                self.assertFalse(any(p<root and root-32<p+n for p,n,v in b.writes[writes:]))
                self.assertEqual(b.get(root-4),38)
                b.diagnostic_alias=None
                self.assertEqual(b.call('ui_res_font_palette',LEASE,SLICE),1)
                self.assertEqual((b.get(SLICE),b.get(SLICE+4)),(root+44864,32))
                self.assertEqual(b.call('ui_res_drop',LEASE),1)
                self.assertEqual(b.call('ui_res_release',READER),1)
                self.assertEqual(b.root(),0);self.assertEqual(b.destroy(),1)
    def test_lazy_font_unused_cache_word_does_not_block_resource_release(self):
        b=ResourceBench(self.compiled);b.start();self.assertEqual(b.finish(),OK)
        self.assertEqual(b.call('ui_res_acquire',READER,LEASE,1),1)
        b.put(0x0211188c,0x02111890);b.put(0x0211192c,0x02361000)
        b.put(0x02361000,1);b.put(0x02361004,0x02026111)
        b.put(0x02361010,b.root()+12288)
        self.assertEqual(b.call('ui_res_drop',LEASE),1)
        self.assertEqual(b.call('ui_res_release',READER),1)

    def test_leases_immutable_bounds_font_cache_barrier_survives_cancel(self):
        b=ResourceBench(self.compiled);b.start();self.assertEqual(b.finish(),OK)
        root=b.root();self.assertEqual(b.call('ui_res_acquire',READER,LEASE,1),1)
        self.assertEqual(b.call('ui_res_acquire',READER,LEASE,1),0)
        for frame in (0,19):
            self.assertEqual(b.call('ui_res_frame',LEASE,frame,0,SLICE),1)
            self.assertEqual((b.get(SLICE),b.get(SLICE+4)),(root+128+608*frame,576))
        self.assertEqual(b.call('ui_res_frame',LEASE,20,0,SLICE),0)
        self.assertEqual(b.call('ui_res_font_palette',LEASE,SLICE),1)
        self.assertEqual((b.get(SLICE),b.get(SLICE+4)),(root+44864,32))
        self.assertEqual(b.call('ui_res_text',LEASE,0x11ed,SLICE),1)
        self.assertEqual(b.call('ui_res_text',LEASE,0x1000,SLICE),0)
        self.assertEqual(b.call('ui_res_text',LEASE,1,root),0)
        b.put(0x0211188c,0x02111890);b.put(0x02111890+0x9c,0x02361000);b.put(0x02361010,root+12288)
        b.call('ui_res_cancel',READER);self.assertEqual(b.call('ui_res_glyphs',LEASE,SLICE),0)
        self.assertEqual(b.call('ui_res_release',READER),0)
        self.assertEqual(b.call('ui_res_drop',LEASE),1);self.assertEqual(b.call('ui_res_drop',LEASE),0)
        self.assertEqual(b.call('ui_res_release',READER),0)
        b.put(0x02361010,0);self.assertEqual(b.call('ui_res_release',READER),1)
        self.assertEqual(b.call('ui_res_text',LEASE,1,SLICE),0)
        self.assertEqual(b.destroy(),1)
    def test_prefix_structure_checked_independently_of_crc_before_allocation(self):
        for off,val in ((0,0),(4,0),(8,0xffffffff),(12,0),(16,0),(20,420),(24,51),(28,5),
                        (436,34916),(440,0xffffffff),(444,0),(448,20),(452,0),(456,0),(460,0),(464,0)):
            b=ResourceBench(self.compiled);raw=bytearray(b.raw);struct.pack_into('<I',raw,off,val);b.raw=bytes(raw)
            b.put(CONFIG+36,zlib.crc32(raw[:468]));b.start();self.assertEqual(b.finish(),ERROR)
            self.assertEqual(b.root(),0);self.assertEqual(b.call('ui_res_release',READER),1)
    def test_zero_padding_sole_final_eos_species_lf_and_refcount_overflow(self):
        for fault in ('padding','finaleos','specieslf'):
            raw,config=synthetic(authored={1:(1,2,65535)});b=ResourceBench(self.compiled,raw,config);raw=bytearray(raw)
            if fault=='padding':raw[-1]=1
            elif fault=='finaleos':raw[-4]=1;raw[-3]=0
            else:
                off=struct.unpack_from('<I',raw,35380+48460)[0];struct.pack_into('<H',raw,35380+off,0xe000)
            b.raw=bytes(raw);b.put(CONFIG+40,zlib.crc32(raw[35380:]));b.start();self.assertEqual(b.finish(),ERROR)
            self.assertEqual(b.call('ui_res_release',READER),1)
        b=ResourceBench(self.compiled);b.start();self.assertEqual(b.finish(),OK)
        b.put(READER+676,65535);before=bytes(b.u.mem_read(LEASE,12))
        self.assertEqual(b.call('ui_res_acquire',READER,LEASE,1),0)
        self.assertEqual(bytes(b.u.mem_read(LEASE,12)),before);b.put(READER+676,0)
        self.assertEqual(b.call('ui_res_release',READER),1)
    def test_file_flag_is_independent_release_barrier_even_without_owned_bit(self):
        b=ResourceBench(self.compiled);b.start();b.step();b.step();b.step()
        b.put(READER+OWN,0)
        self.assertEqual(b.call('ui_res_release',READER),0)
    def test_maximum_member_and_long_entry_validation_is_bounded_without_early_views(self):
        authored={i:tuple([1]*(n-1)+[65535]) for i,n in enumerate((2048,2048,2048,1474),1)}
        raw,config=synthetic(authored=authored);self.assertEqual(len(raw)-35380,69632)
        b=ResourceBench(self.compiled,raw,config);b.start();steps=0
        while b.phase()!=READY:
            self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),0)
            self.assertIn(b.step(),(MORE,OK));steps+=1;self.assertLessEqual(steps,22)
        self.assertEqual(steps,22)
        self.assertEqual(b.call('ui_res_acquire',READER,LEASE,0),1)
        self.assertEqual(b.call('ui_res_text',LEASE,1,SLICE),1);self.assertEqual(b.get(SLICE+4),4096)
        self.assertEqual(b.call('ui_res_drop',LEASE),1);self.assertEqual(b.call('ui_res_release',READER),1)
        self.assertEqual(b.destroy(),1)
    def test_behavior_kills_crc_length_clamp_close_and_eager_free_mutants(self):
        mutants=(
          ('(rcrc(~0u,(const RByte *)p,468)^~0u)==c[9]','r->magic==0x55525231u','prefixcrc'),
          ('if((r->crc^~0u)!=r->config.word[10])','if(0 && (r->crc^~0u)!=r->config.word[10])','wholecrc'),
          ('if(ok!=(int)n)r->failed=1;','if(0 && ok!=(int)n)r->failed=1;','readlength'),
          ('if(!ok || r->fs[11]<r->fs[9] || r->fs[11]-r->fs[9]!=off)','if(!ok)','seek'),
          ('return UI_RES_MORE;\n        }\n        if(r->fs[2]','r->owned=0;return UI_RES_MORE;\n        }\n        if(r->fs[2]','closeowner'),
          ('!r->owned && !(r->fs[3]&0x30) && rquiet(r)','rquiet(r)','eagerfree'),
          ('r->owned=0;r->phase=r->failed?UI_RES_FAILED:UI_RES_VERIFY;','r->owned=0;r->phase=r->failed?UI_RES_FAILED:UI_RES_READY;','earlyready'))
        for old,new,kind in mutants:
            with self.subTest(mutant=kind),tempfile.TemporaryDirectory(prefix='resource-mutant-') as d:
                compiled=compile_resource(Path(d),(old,new));b=ResourceBench(compiled)
                def scenario():
                    if kind=='prefixcrc':b.raw=b.raw[:28]+bytes([b.raw[28]^1])+b.raw[29:]
                    if kind in ('wholecrc','earlyready'):
                        raw=bytearray(b.raw);raw[-4]^=1;b.raw=bytes(raw)
                    if kind=='readlength':b.fs_fault='member'
                    if kind=='seek':b.fs_fault='seek'
                    b.start()
                    if kind in ('closeowner','eagerfree'):
                        for _ in range(3):b.step()
                        b.close_failures=5;self.assertEqual(b.step(),MORE)
                        self.assertEqual(b.get(READER+OWN),1,'file ownership survives FALSE')
                        self.assertEqual(b.call('ui_res_release',READER),0,'file still owns root')
                    else:
                        self.assertEqual(b.finish(),ERROR,'validation precedes READY')
                        if kind=='seek':self.assertEqual(sum(a==READ for a,*_ in b.fs_calls),1,'clamped seek never reads root')
                with self.assertRaisesRegex(AssertionError,'validation precedes READY|clamped seek never reads root|file ownership survives FALSE|file still owns root'):scenario()
if __name__=='__main__':unittest.main()
