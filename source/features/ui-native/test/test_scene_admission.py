"""Authored behavioral admission contract; native counterparts declare seams."""
import os
import tempfile
import unittest
from scene_admission_bench import *


class AdmissionTests(unittest.TestCase):
    def test_retired_wvr_d_residue_requires_idle_allocated_identity_and_no_vram_owners(self):
        b=self.bench()
        for lock_id in (0x40,0x43,0x60,0x6f):
            prepare_retired_wvr(b,lock_id);before=retired_wvr_snapshot(b)
            self.assertEqual(b.admit(),(READY,NONE))
            self.assertEqual(retired_wvr_snapshot(b),before)
        prepare_retired_wvr(b)
        cases=((0x021d43bc,0,2),(0x021d43bc,0x70,2),(0x021d43bc,0x42,2),
               (0x021d43be,8,2),(0x021d43c0,1,4),(0x021d43c4,0x0209e400,4),
               (0x021d4138,1,4),(0x021d4138,2,4),(0x021e1a08,8,4),
               (0x021e1a12,0x43,2),(0x021e1a0c,0x44,2),
               (0x027fffb0,0xffffffff,4),(0x04000243,0x8a,1),
               (0x04000242,0x82,1),(0x021e15c0,8,2))
        for p,v,n in cases:
            old=b.get(p,n);b.put(p,v,n);before=retired_wvr_snapshot(b)
            with self.subTest(address=hex(p),value=v):self.assertEqual(b.admit(),(REFUSE,DISPLAY))
            self.assertEqual(retired_wvr_snapshot(b),before);b.put(p,old,n)
        b.put(0x04000243,0,1)
        self.assertEqual(b.admit(),(READY,NONE),'historical disabled-D predecessor')

    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='scene-admission-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled,cls.receipt=compile_admission(Path(cls.temp.name),scaffold=os.environ.get('SGP_UI_ADMISSION_RED')=='1')
    def bench(self,**kw):return AdmissionBench(self.compiled,**kw)
    def test_post_parent_role_bottom_and_input_bindings_before_app_allocation(self):
        for role,bottom,domain in ((1,1,0),(1,3,1),(2,1,1),(2,3,0)):
            with self.subTest(role=role,bottom=bottom,domain=domain):
                b=self.bench(role=role,bottom=bottom,domain=domain)
                self.assertEqual(b.admit(),(READY,NONE));self.assertEqual(b.get(b.context+28),0)
                self.assertEqual(b.get(b.context+52),b.heap)
    def test_current_field_parent_child_and_supported_bottom_are_required(self):
        b=self.bench()
        cases=((0x021D4158,b.field+4),(b.field+4,1),(b.field+0x6C,1),(b.field+0x18,2),
               (b.process,b.manager),(b.process+4,b.manager+4),(b.manager+16,2),(b.manager+12,54),
               (b.manager+28,b.root+4))
        for p,v in cases:
            old=b.get(p);b.put(p,v)
            with self.subTest(address=hex(p)):self.assertEqual(b.admit()[0],REFUSE)
            b.put(p,old)
        self.assertEqual(b.admit(),(READY,NONE))
    def test_context_generation_role_root_and_borrowed_identity_refuse(self):
        b=self.bench()
        cases=((b.context,0x31435355),(b.context+4,3),(b.context+8,0),(b.context+12,b.field+4),
               (b.context+16,b.options+4),(b.context+20,b.get(b.field+0x10C)),
               (b.context+24,b.args+4),(b.context+52,b.heap+4),(b.context+56,1),
               (b.save+0x2302C,0xFFFFFFFC),(b.field+0x10C,2),
               (b.args+4,b.options+4),(b.args+8,0),(b.root+4624+12,8))
        for p,v in cases:
            old=b.get(p);b.put(p,v)
            with self.subTest(address=hex(p)):self.assertEqual(b.admit()[0],REFUSE)
            b.put(p,old)
        g=self.bench(role=2);g.put(g.manager+24,g.root)
        self.assertEqual(g.admit()[0],REFUSE)
        self.assertEqual(b.admit(),(READY,NONE))
    def test_borrowed_save_cannot_alias_resident_root_and_empty_template_is_not_identity(self):
        b=self.bench();b.put(b.field+12,b.root);b.put(b.root+0x2302C,0xF0)
        b.put(b.context+16,b.root+0x100);b.put(b.args+4,b.root+0x100);b.options=b.root+0x100;b.save=b.root
        self.assertEqual(b.admit()[0],REFUSE)
        b=self.bench();b.put(b.manager,0);b.put(b.template,0)
        self.assertEqual(b.admit(),(REFUSE,FIELD_ERROR))
    def test_reason_requires_live_sys_mode_and_never_writes_an_irq_frame(self):
        b=self.bench();b.u.reg_write(UC_ARM_REG_CPSR,0xD2)
        self.assertEqual(b.admit(),(REFUSE,0xA5A59696))
        self.assertFalse(any(p==REASON for p,n,*_ in b.writes))
    def test_lazy_font_unused_cache_word_allows_both_scene_roles(self):
        for role in (1,2):
            b=self.bench(role=role)
            for stale in (0x06060505,0x43484152,b.widths):
                b.put(b.font+16,stale)
                self.assertEqual(b.admit(),(READY,NONE))
                self.assertEqual(b.get(b.font+16),stale)

    def test_boot_font_tuple_and_real_heap3_allocation_headers_are_required(self):
        b=self.bench()
        cases=((0x0211188C,0),(0x0211192C,0),(0x02111944,2,1),(b.font,0),
               (b.font+4,0x02026069),(b.font,2),(b.font+12,60),
               (b.font+0x54,b.narc+4),(b.font+0x74,b.widths+4),(b.font+0x78,0),
               (b.font-4,11),(b.narc-32,0),(b.widths-28,16),(b.widths,b.get(b.widths)^1))
        for row in cases:
            p,v=row[:2];n=row[2] if len(row)>2 else 4;old=b.get(p,n);b.put(p,v,n)
            with self.subTest(address=hex(p)):self.assertEqual(b.admit(),(REFUSE,FONT_ERROR))
            b.put(p,old,n)
        self.assertEqual(b.admit(),(READY,NONE))
    def test_every_callback_word_and_all_eight_printers_refuse(self):
        b=self.bench()
        for p in range(0x021D110C,0x021D111C,4):
            b.put(p,0x023CB801)
            with self.subTest(callback=hex(p)):self.assertEqual(b.admit(),(REFUSE,CALLBACK))
            b.put(p,0)
        for i in range(8):
            p=0x021D1F74+4*i;b.put(p,b.font)
            with self.subTest(printer=i):self.assertEqual(b.admit(),(REFUSE,PRINTER))
            b.put(p,0)
        self.assertEqual(b.admit(),(READY,NONE))
    def test_dma_capture_power_sdk_policy_and_gx_refuse_without_clearing(self):
        b=self.bench()
        cases=[(0x040000B8+12*i,0x80000000,DMA) for i in range(4)]
        cases.extend(((0x04000064,0x80000000,DISPLAY),(0x04000304,0x201,DISPLAY),
                      (0x02110C7C,0,DISPLAY),(0x02110C80,0,DISPLAY),
                      (0x021E15C0,1,DISPLAY),(0x04000240,0,DISPLAY)))
        for p,v,reason in cases:
            old=b.get(p);b.put(p,v)
            with self.subTest(address=hex(p)):self.assertEqual(b.admit(),(REFUSE,reason))
            b.put(p,old)
        b.put(0x02110C80,0xFFFFFFFF);self.assertEqual(b.admit(),(READY,NONE))
    def test_unknown_transition_owners_refuse_even_when_queries_look_bounded(self):
        b=self.bench();b.fade_finished=0
        self.assertEqual(b.admit(),(REFUSE,FADE));b.fade_finished=1;b.brightness_inactive=0
        self.assertEqual(b.admit(),(REFUSE,BRIGHTNESS));b.brightness_inactive=1
        self.assertEqual(b.admit(),(READY,NONE))
    def test_known_execution_boundary_waits_then_rechecks_on_next_call(self):
        b=self.bench()
        for cpsr,ime in ((0xDF,1),(0x5F,0)):
            b.u.reg_write(UC_ARM_REG_CPSR,cpsr);b.put(IME,ime);b.getter_calls.clear()
            self.assertEqual(b.admit(),(WAIT,EXECUTION));self.assertEqual(b.getter_calls,[])
            b.u.reg_write(UC_ARM_REG_CPSR,0x5F);b.put(IME,1)
            self.assertEqual(b.admit(),(READY,NONE))
    def test_invalid_or_stale_output_refuses_atomically_before_native_calls(self):
        b=self.bench()
        for output in (0,REASON+1,b.context,b.font,b.field,b.save,IME,STACK-512,0x027E3780):
            b.getter_calls.clear();before=bytes(b.u.mem_read(0x027E0000,0x4000))
            self.assertEqual(b.admit(reason=output)[0],REFUSE)
            self.assertEqual(b.getter_calls,[])
            after=bytes(b.u.mem_read(0x027E0000,0x4000))
            self.assertEqual(before[STACK-0x027E0000:],after[STACK-0x027E0000:])
            self.assertFalse(any(p==output for p,n,*_ in b.writes))
        self.assertEqual(b.admit(context=0),(REFUSE,CONTEXT_ERROR))
    def test_strict_loader_accepts_complete_dependency_closure_and_delta_is_bounded(self):
        with tempfile.TemporaryDirectory(prefix='scene-admission-baseline-') as d:
            baseline,receipt=compile_admission(Path(d),baseline=True)
        self.assertEqual(self.receipt['undefined'],[])
        self.assertLessEqual(len(self.compiled[0])-len(baseline[0]),20912)
        self.assertGreater(len(self.compiled[0]),len(baseline[0]))

if __name__=='__main__':unittest.main()
