"""Class A compiled ownership and restricted views, declared fake lowerFS."""
import unittest
from guide_resource_bench import *
class GuideResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);cls.compiled=compile_guide(Path(cls.temp.name))
    def test_bounded_pump_keeps_reads_and_output_and_does_not_spin_on_wait(self):
        self.assertIn('ui_guide_pump',self.compiled[1])
        results=[]
        for cap in (1,4):
            b=GuideBench(self.compiled);b.start();calls=0
            while True:
                calls+=1;r=b.call('ui_guide_pump',b.reader,4096,cap)
                if r!=MORE:break
                self.assertLess(calls,100)
            self.assertEqual(r,READY)
            results.append((calls,bytes(b.u.mem_read(b.get(b.reader+236),len(b.data))),b.fs_calls))
        self.assertLess(results[1][0],results[0][0]);self.assertEqual(results[0][1:],results[1][1:])
        b=GuideBench(self.compiled);b.start()
        while b.get(b.reader+220)!=5:self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
        # Exact persistent native pending tuple. No producer completes it.
        for off,value in ((0,ARC+32),(12,0x59),(20,2)):b.put(b.reader+off,value)
        b.put(ARC+28,0x117);b.put(ARC+36,b.reader)
        before=bytes(b.u.mem_read(b.reader,292));events=len(b.fs_calls)
        self.assertEqual(b.call('ui_guide_pump',b.reader,4096,4),MORE)
        self.assertEqual(bytes(b.u.mem_read(b.reader,292)),before)
        self.assertEqual(len(b.fs_calls),events)
    def test_pump_failed_close_cancellation_and_bad_budget_retain_native_owner(self):
        b=GuideBench(self.compiled);b.start()
        for budget,cap in ((0,4),(4097,4),(4096,0),(4096,17)):
            before=bytes(b.u.mem_read(b.reader,292)),list(b.fs_calls)
            self.assertEqual(b.call('ui_guide_pump',b.reader,budget,cap),0)
            self.assertEqual((bytes(b.u.mem_read(b.reader,292)),b.fs_calls),before)
        while b.get(b.reader+220)!=6:self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
        b.close_failures=2;root=b.get(b.reader+236);count=len(b.fs_calls)
        self.assertEqual(b.call('ui_guide_pump',b.reader,4096,4),MORE)
        self.assertEqual(len(b.fs_calls)-count,1)
        self.assertEqual(b.call('ui_guide_cancel',b.reader),MORE)
        self.assertEqual(b.call('ui_guide_pump',b.reader,4096,4),MORE)
        self.assertEqual(b.get(b.reader+236),root);self.assertEqual(b.call('ui_guide_release',b.reader),0)
        self.assertEqual(b.call('ui_guide_pump',b.reader,4096,4),MORE,'one cancelled close retry per callback')
        self.assertEqual(b.get(b.reader+236),root);self.assertEqual(b.call('ui_guide_release',b.reader),0)
        self.assertEqual(b.call('ui_guide_pump',b.reader,4096,4),FAILED)
        self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
    def test_native_cache_extent_bounds_alignment_alias_and_identity(self):
        # The upper bound is native main RAM, not the game heap's ceiling.
        for raw in (FAT,0x023be564,0x02400000-7040):
            with self.subTest(valid_raw=hex(raw)):
                b=GuideBench(self.compiled);b.relocate_archive_cache(raw)
                self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),READY)
                self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
        for kind in ('low','high','overflow','misaligned','app','config','heap','fat','mapping','callback','association','queue'):
            with self.subTest(refusal=kind):
                b=GuideBench(self.compiled);fat=b.relocate_archive_cache(0x023be564)
                cfg,heap=CFG,TOKEN
                if kind in ('low','high','overflow','misaligned','app'):
                    raw={'low':0x0226ec3c,'high':0x02400000-7040+4,
                         'overflow':0xfffffffc,'misaligned':0x023be565,'app':b.app-32}[kind]
                    b.put(ARC+68,raw);b.put(ARC+44,(raw+31)&~31);b.put(ARC+52,((raw+31)&~31)+4104)
                if kind=='config':cfg=0x023be600;b.u.mem_write(cfg,b.cfg)
                if kind=='heap':heap=0x023be600;b.u.mem_write(heap,bytes(b.u.mem_read(TOKEN,92)))
                if kind=='fat':b.put(fat+8*b.get(CFG+16),b.get(CFG+20)+4)
                if kind=='mapping':b.put(ARC+52,b.get(ARC+52)+4)
                if kind=='callback':b.put(ARC+72,0)
                self.assertEqual(b.call('ui_guide_init',b.reader),1)
                if kind=='association':b.put(b.reader+8,ARC)
                if kind=='queue':b.put(ARC+36,b.reader)
                before=bytes(b.u.mem_read(ARC,92));calls=len(b.fs_calls)
                self.assertEqual(b.call('ui_guide_begin',b.reader,cfg,heap),HOLD)
                self.assertEqual(len(b.fs_calls),calls)
                self.assertEqual(bytes(b.u.mem_read(ARC,92)),before)
    def test_load_then_lease_pins_root_and_exposes_compiled_order(self):
        b=GuideBench(self.compiled)
        self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),READY)
        self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),1)
        self.assertEqual(b.call('ui_guide_release',b.reader),0)
        self.assertEqual(b.call('ui_guide_category',b.lease,0,OUT),1)
        self.assertEqual(b.get(OUT),4)
        self.assertEqual(b.call('ui_guide_drop',b.lease),1)
        self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
    def loaded(self):
        b=GuideBench(self.compiled);self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),READY)
        self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),1);return b
    def test_unsorted_ids_cyclic_refs_and_readonly_views(self):
        b=self.loaded()
        for identity,want in ((9,0),(2,1)):
            self.assertEqual(b.call('ui_guide_find',b.lease,identity,OUT),1);self.assertEqual(b.get(OUT),want)
            self.assertEqual(b.call('ui_guide_page',b.lease,want,0,OUT),1);self.assertEqual(b.get(OUT+12),2 if identity==9 else 9)
            self.assertEqual(b.call('ui_guide_line',b.lease,want,0,0,OUT),1)
        before=bytes(b.u.mem_read(OUT,64));calls=len(b.fs_calls)
        for api,args in (('ui_guide_category',(2,OUT)),('ui_guide_entry',(0,1,OUT)),('ui_guide_find',(0,OUT)),('ui_guide_find',(65535,OUT)),('ui_guide_page',(0,1,OUT)),('ui_guide_line',(0,0,1,OUT))):
            self.assertEqual(b.call(api,b.lease,*args),0);self.assertEqual(bytes(b.u.mem_read(OUT,64)),before)
        self.assertEqual(len(b.fs_calls),calls)
    def test_moved_duplicate_or_changed_owner_cannot_drop_or_free_text(self):
        b=self.loaded();copy=b.app+420;b.u.mem_write(copy,bytes(b.u.mem_read(b.lease,36)))
        self.assertEqual(b.call('ui_guide_drop',copy),0);self.assertEqual(b.call('ui_guide_acquire',b.reader,copy),0)
        for off,value in ((0,0),(4,0),(8,2),(12,0),(16,1),(32,0)):
            old=b.get(b.lease+off);b.put(b.lease+off,value)
            self.assertEqual(b.call('ui_guide_drop',b.lease),0);self.assertEqual(b.call('ui_guide_release',b.reader),0)
            b.put(b.lease+off,old)
        self.assertEqual(b.call('ui_guide_drop',b.lease),1);self.assertEqual(b.call('ui_guide_drop',b.lease),0)
        self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED);self.assertEqual(b.call('ui_guide_release',b.reader),0)
    def test_outputs_and_lease_cannot_alias_persistent_allocations_or_prefixes(self):
        b=self.loaded();root=b.get(b.reader+236)
        for out in (b.reader,b.lease,b.app,root-32,root,CFG,TOKEN,0xfffffff0,OUT+1):
            before=bytes(b.u.mem_read(b.reader,292));calls=len(b.fs_calls)
            self.assertEqual(b.call('ui_guide_category',b.lease,0,out),0)
            self.assertEqual(bytes(b.u.mem_read(b.reader,292)),before);self.assertEqual(len(b.fs_calls),calls)
        self.assertEqual(b.call('ui_guide_drop',b.lease),1)
        for lease in (b.reader,root,root-32,TOKEN,OUT,b.app+1008):self.assertEqual(b.call('ui_guide_acquire',b.reader,lease),0)
    def test_native_close_failures_keep_same_file_and_root_until_true(self):
        b=GuideBench(self.compiled);b.start()
        while b.get(b.reader+220)!=6:self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
        root=b.get(b.reader+236);b.close_failures=5
        for _ in range(5):
            self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
            self.assertEqual(b.get(b.reader+236),root);self.assertEqual(b.call('ui_guide_release',b.reader),0)
        self.assertEqual(b.finish(),READY)
        self.assertEqual([a for p,a,x,y in b.fs_calls if p==CLOSE],[b.reader]*6)
    def test_cancel_at_each_loading_phase_preserves_owner_until_detachment(self):
        for phase in range(1,9):
            b=GuideBench(self.compiled);b.start()
            while b.get(b.reader+220)!=phase:self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
            result=b.call('ui_guide_cancel',b.reader)
            if result==MORE:self.assertEqual(b.finish(),FAILED)
            else:self.assertEqual(result,FAILED)
            self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
            self.assertEqual(b.get(b.counts+76,2),1)
    def test_short_read_bad_crc_and_bad_typed_title_never_publish(self):
        for kind in ('short','crc','title'):
            b=GuideBench(self.compiled)
            if kind=='short':b.short=True
            if kind=='crc':b.put(CFG+44,b.get(CFG+44)^1)
            if kind=='title':
                data=bytearray(b.data);title=struct.unpack_from('<I',data,20)[0];struct.pack_into('<H',data,title,0xe000)
                b.data=bytes(data);b.cfg=config(b.data);b.u.mem_write(CFG,b.cfg)
            self.assertEqual(b.start(),MORE);self.assertEqual(b.finish(),FAILED)
            self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),0)
            self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
    def test_source_or_prefix_change_holds_without_native_cleanup(self):
        for kind in ('source','prefix','app'):
            b=GuideBench(self.compiled);b.start()
            while b.get(b.reader+220)!=4:b.call('ui_guide_step',b.reader,4096)
            root=b.get(b.reader+236)
            if kind=='source':b.put(ARC+72,0)
            elif kind=='prefix':b.put(root-4,0)
            else:b.put(b.app-28,16)
            calls=len(b.fs_calls);self.assertEqual(b.call('ui_guide_step',b.reader,4096),HOLD)
            self.assertEqual(b.call('ui_guide_release',b.reader),HOLD);self.assertEqual(len(b.fs_calls),calls)
            self.assertEqual(b.get(b.reader+236),root)
    def test_fresh_or_released_record_never_reinitializes_or_releases_unknown_file(self):
        for operation in ('begin','release'):
            for offset,value in ((8,ARC),(12,16),(0,ARC+32),(72,0)):
                b=GuideBench(self.compiled);self.assertEqual(b.call('ui_guide_init',b.reader),1)
                b.put(b.reader+offset,value);calls=len(b.fs_calls)
                result=b.call('ui_guide_begin',b.reader,CFG,TOKEN) if operation=='begin' else b.call('ui_guide_release',b.reader)
                self.assertEqual(result,HOLD)
                self.assertEqual(len(b.fs_calls),calls);self.assertEqual(b.get(b.reader+offset),value)
    def test_malformed_page_line_reference_views_refuse_without_changing_output(self):
        for kind in ('lines','reference','glyph','offset'):
            b=self.loaded();root=b.get(b.reader+236);entry=root+12+24
            table=b.get(entry+12);page=b.get(root+table);line=b.get(root+page+4)
            if kind=='lines':b.put(root+page,8,2)
            elif kind=='reference':b.put(root+page+2,65535,2)
            elif kind=='glyph':b.put(root+line,0xe000,2)
            else:b.put(root+table,page+2)
            b.u.mem_write(OUT,b'Q'*64);before=bytes(b.u.mem_read(OUT,64))
            self.assertEqual(b.call('ui_guide_page',b.lease,0,0,OUT),0)
            self.assertEqual(b.call('ui_guide_line',b.lease,0,0,0,OUT),0)
            self.assertEqual(bytes(b.u.mem_read(OUT,64)),before)
    def test_invalid_config_bounds_refuse_before_native_fs_and_preserve_record(self):
        for offset,value in ((16,513),(28,0),(32,0),(36,0xffffffff),(40,131074),(48,0),(52,4097),(56,1)):
            b=GuideBench(self.compiled);self.assertEqual(b.call('ui_guide_init',b.reader),1)
            b.put(CFG+offset,value);before=bytes(b.u.mem_read(b.reader,292));calls=len(b.fs_calls)
            self.assertEqual(b.call('ui_guide_begin',b.reader,CFG,TOKEN),0)
            self.assertEqual(bytes(b.u.mem_read(b.reader,292)),before);self.assertEqual(len(b.fs_calls),calls)
    def test_semantic_mutants_cannot_skip_crc_or_lease_or_forget_close_owner(self):
        cases=[
          ('crc','(r->crc^~0u)!=r->config.member_crc||!ggr_header(r)','!ggr_header(r)'),
          ('lease','if(r->lease_address||r->file_bound||','if(r->file_bound||'),
          ('close','unsigned ok=RCLOSE(r->fs);ggr_snapshot(r,&s);','unsigned ok=RCLOSE(r->fs);ggr_snapshot(r,&s);r->file_bound=0;')]
        def check(compiled,kind):
            b=GuideBench(compiled)
            if kind=='crc':b.put(CFG+44,b.get(CFG+44)^1)
            self.assertEqual(b.start(),MORE)
            if kind=='close':
                while b.get(b.reader+220)!=6:self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE)
                b.close_failures=1;self.assertEqual(b.call('ui_guide_step',b.reader,4096),MORE,'close-false retains owner')
                self.assertEqual(b.get(b.reader+248),1,'close-false retains bound file')
            elif kind=='crc':self.assertEqual(b.finish(),FAILED,'bad CRC never READY')
            else:
                self.assertEqual(b.finish(),READY);self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),1)
                self.assertEqual(b.call('ui_guide_release',b.reader),0,'lease pins root')
        for kind,old,new in cases:
            check(self.compiled,kind)
            with tempfile.TemporaryDirectory() as d:
                compiled=compile_guide(Path(d),(old,new))
                with self.assertRaises(AssertionError):check(compiled,kind)
    def test_masked_begin_defer_generation_reuse_and_epoch_wrap(self):
        b=GuideBench(self.compiled);self.assertEqual(b.call('ui_guide_init',b.reader),1)
        before=bytes(b.u.mem_read(b.reader,292));b.u.reg_write(UC_ARM_REG_CPSR,b.u.reg_read(UC_ARM_REG_CPSR)|128)
        self.assertEqual(b.call('ui_guide_begin',b.reader,CFG,TOKEN),MORE);self.assertEqual(bytes(b.u.mem_read(b.reader,292)),before)
        b.u.reg_write(UC_ARM_REG_CPSR,b.u.reg_read(UC_ARM_REG_CPSR)&~128)
        self.assertEqual(b.call('ui_guide_begin',b.reader,CFG,TOKEN),MORE);self.assertEqual(b.finish(),READY)
        b.put(b.reader+284,0xffffffff);self.assertEqual(b.call('ui_guide_acquire',b.reader,b.lease),0)
        self.assertEqual(b.call('ui_guide_release',b.reader),RELEASED)
        self.assertEqual(b.call('ui_guide_begin',b.reader,CFG,TOKEN),0)
        b.put(CFG+12,2);self.assertEqual(b.call('ui_guide_begin',b.reader,CFG,TOKEN),MORE)
class GuideInputAdmissionTests(unittest.TestCase):
    def setUp(self):
        import importlib
        from unittest.mock import patch
        self.native=importlib.import_module('test_guide_resource_rom')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.paths={'EN':self.root/'explicit-EN.nds','IT':self.root/'explicit-IT.nds'}
        self.charmap=self.root/'explicit-charmap.txt'
        self.env={'SGP_UI_GUIDE_RESOURCE_EN':str(self.paths['EN']),'SGP_UI_GUIDE_RESOURCE_IT':str(self.paths['IT']),'SGP_UI_GUIDE_CHARMAP':str(self.charmap),'SGP_UI_GUIDE_RESOURCE_REQUIRE_INPUTS':'0'}
        self.patch=patch
    def setup_probe(self,required=False):
        # A subclass object stays local: no imported native TestCase is exposed
        # to Class A discovery. Missing/corrupt inputs must stop before compile.
        class Probe(self.native.GuideResourceRomTests):pass
        env=dict(self.env);env['SGP_UI_GUIDE_RESOURCE_REQUIRE_INPUTS']='1' if required else '0'
        with self.patch.dict(self.native.os.environ,env),self.patch.object(self.native,'SOURCE',self.root/'source'):
            try:Probe.setUpClass()
            finally:Probe.doClassCleanups()
    def test_default_missing_private_inputs_skip_without_opening_canonical_files(self):
        with self.assertRaisesRegex(unittest.SkipTest,'explicit-EN|SGP_UI_GUIDE_RESOURCE_EN'):
            self.setup_probe()
    def test_required_missing_private_inputs_fail(self):
        with self.assertRaises(AssertionError):self.setup_probe(required=True)
    def test_existing_corrupt_rom_fails_even_when_other_private_inputs_are_missing(self):
        for lang in ('EN','IT'):
            self.paths[lang].write_bytes(b'original synthetic bad ROM, not game data')
            for required in (False,True):
                with self.subTest(lang=lang,required=required),self.assertRaisesRegex(AssertionError,'ROM identity'):
                    self.setup_probe(required)
            self.paths[lang].unlink()
    def test_existing_corrupt_charmap_fails_even_when_roms_are_missing(self):
        self.charmap.write_bytes(b'original synthetic bad mapping')
        for required in (False,True):
            with self.subTest(required=required),self.assertRaisesRegex(AssertionError,'charmap identity'):
                self.setup_probe(required)
    def test_existing_nonfile_input_fails_instead_of_skipping(self):
        self.paths['EN'].mkdir()
        with self.assertRaisesRegex(AssertionError,'not a file'):self.setup_probe()
if __name__=='__main__':unittest.main()
