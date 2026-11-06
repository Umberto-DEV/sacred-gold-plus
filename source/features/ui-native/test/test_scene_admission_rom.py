"""Finite canonical V4 EN/IT prepared post-parent admission proof.

Native NNS/GF heap allocation, Options getter, fade/brightness queries and CPSR
queries execute original pinned bytes. Font widths and GMIF offsets come from
the actual language's font NARC. The boot font tuple, retired Field parent and
authenticated Bridge context/template handoff are PREPARED seams. No parent
teardown, future producer exclusion, real boot, FS/CARD transport, IRQ/DMA
scheduling, complete Scene, timing, emulator or installation is inferred.
"""
import os
import tempfile
import unittest
import zlib
from scene_admission_bench import *
from sgp12.blz import ndspy_load_arm9_sicuro
from test_heap_rom import NativeRetiredHeapBench,ROM_PINS,PINS
import test_scene_admission as authored

ADMISSION_PINS=(
 (0x0209E00C,0x3F8,'6de14145bd25ba854940e23c7ec295b4806a1773b5c0f74b731a314ef96d602e'),
 (0x020D3D30,0x148,'d7e39df2685b8a2e8a4dfa4c57cfcaf4e496777124cc2703986be0cea63069f3'),
 (0x0203DE8C,0x290,'a9272cb0636b8e07f1ddb7b7b5dd0348edc7b750e4827ef7f598dcf0b66a4900'),
 (0x02028EA8,12,'e53aa60fe290a49618a1b8cffa2be5bc1be32cdf80999c6445c9aef2e7562285'),
 (0x020272C8,64,'22c36f526e2de23e382807e9e3afb967cdff6384b1a2f69a53e14282d6d3ac7c'),
 (0x0200FA24,0x1E8,'69f48e05abff1fc795a973645fd50f239cdbd707931bdccd701745b4690dcd06'),
 (0x0200B578,0x8C,'d6a7463d754177a1ca0b6f18270f6552cbdd508ab6317b1ed74bed70989fcb77'),
 (0x0201A0FC,0xB8,'1da318c8da165154e00aae289a3aa1df1bf9209316c9bdccca7a452688f6dae0'),
 (0x02020000,0xFC,'76e3b738539ff263fae69abf33b55167090a5d75ed21fcd1e54540cb2d02492e'),
 (0x02025E88,0x3CC,'4c4e13dd685080bb10abdd88e19db3d1aeee75cc083932108321693a215eef38'),
 (0x02110C7C,8,'30656bde983020b4a04d4fb8027463ad8cd15d89d4b953f961654b1d6579b9b9'),
 (0x020D3A90,24,'df0fcaa0e5aad641260041edb6a5688cb9a43de0bfeeff2bfcb54ef8c8cc54b8'))
FADE_STATE=0x021D1034+12
BRIGHT_MAIN,BRIGHT_SUB=0x021D0EB4+0x3C,0x021D0EB4+0x1C


class NativeAdmissionBench(AdmissionChecks,NativeRetiredHeapBench):
    observed={'calls':0,'max_instructions':0,'max_stack':0}
    def __init__(self,compiled,fixture,role=1,bottom=1,domain=0):
        self.admitting=False;self.getter_calls=[]
        sections,widths,gmif=fixture
        super().__init__(compiled,sections)
        self.query_fetch=instruction_set(self.u,[OPTIONS_GET|1,FADE_GET|1,BRIGHTNESS_GET|1,0x020272C9,0x020D3A90,0x020D3A9C],
                                         [(a,a+n) for a,n,_ in ADMISSION_PINS])
        self.compiled_fetch=instruction_set(self.u,[v for k,v in self.symbols.items() if not k.startswith('$')],[(CODE,CODE+len(self.code))])
        assert self.control_call(0x0201A911,3,11,0x1C000)==1
        prepare_borrowed(self,lambda heap,n:self.control_call(0x0201AA8D,heap,n),widths,gmif,role,bottom,domain)
        self.put(FADE_STATE,0,2);self.put(BRIGHT_MAIN,0);self.put(BRIGHT_SUB,0)
        self.getter_calls.clear()
    def hook(self,u,p,n,data):
        if getattr(self,'admitting',False):
            self.instructions+=1;sp=u.reg_read(UC_ARM_REG_SP);self.low=min(self.low,sp)
            assert STACK-1024<=sp<=STACK
            if p==STOP:u.emu_stop();return
            assert p in self.compiled_fetch or p in self.query_fetch,f'unadmitted instruction {p:08x}/{n}'
            if p in self.compiled_fetch:
                assert u.reg_read(UC_ARM_REG_CPSR)&32
                check_compiled(self.code,p,n)
            else:
                arm=0x020D3A90<=p<0x020D3AA8
                assert bool(u.reg_read(UC_ARM_REG_CPSR)&32)!=arm
                assert n==(4 if arm else 2)
            if p in (OPTIONS_GET,FADE_GET,BRIGHTNESS_GET):
                self.getter_calls.append(p)
                assert sp%8==0
                if p==OPTIONS_GET:assert u.reg_read(UC_ARM_REG_R0)==self.save
                if p==BRIGHTNESS_GET:assert u.reg_read(UC_ARM_REG_R0)==3
            return
        super().hook(u,p,n,data)
    def admit(self,*args,**kw):
        before=self.instructions
        result=super().admit(*args,**kw)
        self.observed['calls']+=1
        self.observed['max_instructions']=max(self.observed['max_instructions'],self.instructions-before)
        self.observed['max_stack']=max(self.observed['max_stack'],STACK-self.low)
        return result


class AdmissionRomTests(unittest.TestCase):
    def test_native_retired_wvr_display_residue_and_invalid_owner_tuples(self):
        authored.AdmissionTests.test_retired_wvr_d_residue_requires_idle_allocated_identity_and_no_vram_owners(self)

    @classmethod
    def setUpClass(cls):
        import ndspy.rom,ndspy.narc
        canonical=SOURCE.parent/'local/experiments/balance493-2026-10-28'
        cls.fixtures={};cls.pins=[]
        for lang,pin in ROM_PINS.items():
            path=Path(os.environ.get('SGP_UI_ADMISSION_'+lang,str(canonical/f'candidate-v4-{lang}.nds')))
            if not path.is_file():
                message='missing canonical admission '+lang
                if os.environ.get('SGP_UI_ADMISSION_REQUIRE_INPUTS')=='1':raise AssertionError(message)
                raise unittest.SkipTest(message)
            sha=hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda:stream.read(1<<20),b''):sha.update(block)
            assert (path.stat().st_size,sha.hexdigest())==pin
            rom=ndspy.rom.NintendoDSRom.fromFile(path);ss=ndspy_load_arm9_sicuro(rom).sections
            for a,n,want in (*PINS,*ADMISSION_PINS):
                s=next(s for s in ss if s.ramAddress<=a<a+n<=s.ramAddress+len(s.data))
                assert hashlib.sha256(s.data[a-s.ramAddress:a-s.ramAddress+n]).hexdigest()==want,(lang,hex(a))
            archive=bytes(rom.files[145]);font=ndspy.narc.NARC(archive).files[0]
            widths=bytes(font[0x7F50:]);assert len(widths)==509 and zlib.crc32(widths)==0x885AB7FC
            # GMIF payload location differs by language; never hardcode EN8C.
            gmif=16
            while archive[gmif:gmif+4]!=b'GMIF':gmif+=struct.unpack_from('<I',archive,gmif+4)[0]
            gmif+=8
            assert gmif=={'EN':0x8C,'IT':0x90}[lang]
            cls.fixtures[lang]=([(s.ramAddress,bytes(s.data)) for s in ss if 0x02000000<=s.ramAddress<0x02400000],widths,gmif)
            cls.pins.append((lang,pin[1],gmif))
            del rom,ss,archive,font
        cls.temp=tempfile.TemporaryDirectory(prefix='scene-admission-b-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled,cls.receipt=compile_admission(Path(cls.temp.name))
    def bench(self,lang='EN',**kw):return NativeAdmissionBench(self.compiled,self.fixtures[lang],**kw)
    def test_native_both_languages_prepared_role_bottom_domain_and_font_allocations(self):
        for lang in self.fixtures:
            for role,bottom,domain in ((1,1,0),(1,3,1),(2,1,1),(2,3,0)):
                with self.subTest(lang=lang,role=role,bottom=bottom,domain=domain):
                    b=self.bench(lang,role=role,bottom=bottom,domain=domain)
                    self.assertEqual(b.admit(),(READY,NONE))
                    self.assertEqual(b.getter_calls,[OPTIONS_GET,FADE_GET,BRIGHTNESS_GET])
                    self.assertEqual(b.get(b.font+0x78),self.fixtures[lang][2])
                    self.assertEqual(b.get(b.context+28),0)
    def test_native_foreign_context_options_font_and_all_producer_slots(self):
        # EN/IT native queried bodies are independently equal-pinned above;
        # one language covers shared negative paths without a Cartesian rerun.
        for check in (authored.AdmissionTests.test_borrowed_save_cannot_alias_resident_root_and_empty_template_is_not_identity,
                      authored.AdmissionTests.test_reason_requires_live_sys_mode_and_never_writes_an_irq_frame,
                      authored.AdmissionTests.test_current_field_parent_child_and_supported_bottom_are_required,
                      authored.AdmissionTests.test_context_generation_role_root_and_borrowed_identity_refuse,
                      authored.AdmissionTests.test_boot_font_tuple_and_real_heap3_allocation_headers_are_required,
                      authored.AdmissionTests.test_every_callback_word_and_all_eight_printers_refuse,
                      authored.AdmissionTests.test_dma_capture_power_sdk_policy_and_gx_refuse_without_clearing):
            check(self)
    def test_native_fade_and_each_brightness_query_refuse_unknown_owner(self):
        for lang in self.fixtures:
            b=self.bench(lang)
            for p,n,reason in ((FADE_STATE,2,FADE),(BRIGHT_MAIN,4,BRIGHTNESS),(BRIGHT_SUB,4,BRIGHTNESS)):
                b.put(p,1,n);self.assertEqual(b.admit(),(REFUSE,reason));b.put(p,0,n)
                self.assertEqual(b.admit(),(READY,NONE))
    def test_native_execution_wait_then_ready_and_output_atomicity_abi_irq_canaries(self):
        authored.AdmissionTests.test_known_execution_boundary_waits_then_rechecks_on_next_call(self)
        authored.AdmissionTests.test_invalid_or_stale_output_refuses_atomically_before_native_calls(self)
    def test_native_meaningful_omission_mutants_fail_the_observed_contract(self):
        mutants=(('SB(0x02111944u)!=1','SB(0x02111944u)>127',lambda b:b.put(0x02111944,2,1),FONT_ERROR),
                 ('i<8;++i)if(SW(0x021D1F74u','i<7;++i)if(SW(0x021D1F74u',lambda b:b.put(0x021D1F90,b.font),PRINTER),
                 ('i<4;++i)if(SW(0x021D110Cu','i<3;++i)if(SW(0x021D110Cu',lambda b:b.put(0x021D1118,1),CALLBACK))
        for old,new,inject,reason in mutants:
            with self.subTest(omission=old),tempfile.TemporaryDirectory(prefix='scene-admission-mutant-') as temp:
                baseline=self.bench();inject(baseline);self.assertEqual(baseline.admit(),(REFUSE,reason))
                compiled,_=compile_admission(Path(temp),mutation=(old,new))
                mutant=NativeAdmissionBench(compiled,self.fixtures['EN']);inject(mutant)
                self.assertNotEqual(mutant.admit(),(REFUSE,reason))
    @classmethod
    def tearDownClass(cls):
        if os.environ.get('SGP_UI_ADMISSION_METRICS'):
            import json
            Path(os.environ['SGP_UI_ADMISSION_METRICS']).write_text(json.dumps(NativeAdmissionBench.observed,indent=2)+'\n')

if __name__=='__main__':unittest.main()
