"""Finite resident lifecycle tests; native services have explicit Class A seams."""
import os
import tempfile
import unittest
from pathlib import Path
from bridge_bench import *

class BridgeTests(unittest.TestCase):
    def test_lazy_font_bootstrap_preserves_unused_cache_word(self):
        for role in (1,2):
            b=BridgeBench(self.compiled,role)
            b.put(FONT+16,0x43484152)
            self.assertEqual(b.call('ui_bridge_settings_init' if role==1 else 'ui_bridge_guide_init'),0)
            self.assertEqual(b.events,[('allocate',1),('begin',role,1)])
            self.assertEqual(b.get(FONT+16),0x43484152)

    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='bridge-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_bridge(Path(cls.temp.name),scaffold=os.getenv('SGP_BRIDGE_RED')=='1')
    def test_first_native_init_owns_checked_root_with_original_borrowed_args(self):
        for role in (1,2):
            b=BridgeBench(self.compiled,role);before=bytes(b.u.mem_read(ARGS,12))
            b.call('ui_bridge_settings_init' if role==1 else 'ui_bridge_guide_init')
            self.assertEqual(b.get(MANAGER+28),ROOT,'missing checked root publication')
            self.assertEqual(b.events,[('allocate',1),('begin',role,1)])
            self.assertEqual(bytes(b.u.mem_read(ARGS,12)),before)
            self.assertEqual(b.get(CONTEXT+20),FIELD+0x10C)
            self.assertEqual(b.get(CONTEXT+24),ARGS if role==1 else 0)
            self.assertEqual(b.get(MANAGER+32),0xA6A6A6A6)
            self.assertEqual(b.get(MANAGER+36),0x69696969)
    def test_checked_root_supplies_immutable_resident_heap_authority(self):
        b=BridgeBench(self.compiled);b.call('ui_bridge_settings_init')
        self.assertEqual(b.get(CONTEXT+52),ROOT+4944,'Scene has no durable heap authority')
        self.assertEqual(bytes(b.u.mem_read(ROOT+4944,92)),bytes(92))
        self.assertEqual(b.get(CONTEXT),0x32435355)

    def test_changed_null_retains_manager_and_generation_across_stack_poison(self):
        b=BridgeBench(self.compiled);b.alloc_hold=True
        self.assertEqual(b.call('ui_bridge_settings_init'),0)
        self.assertEqual(b.get(BOOT),MANAGER)
        self.assertEqual(b.get(BOOT+4),1)
        for _ in range(3):
            b.u.mem_write(STACK-2048,b'\xA5'*2048)
            self.assertEqual(b.call('ui_bridge_settings_init'),0)
        self.assertEqual(b.events,[('allocate',1)])

    def test_invalid_native_entry_never_allocates_or_dispatches(self):
        cases=((FIELD+4,1),(FIELD+0x6C,1),(PROCESS,MANAGER),(PROCESS+4,MANAGER+4),
               (MANAGER,0),(MANAGER+12,54),(MANAGER+16,2),(ARGS+4,OPTIONS+4),
               (ARGS+8,0),(FIELD+0x10C,2),(0x02111944,2),(FONT,2),(FONT+4,0x02026069))
        for address,value in cases:
            with self.subTest(address=hex(address)):
                b=BridgeBench(self.compiled);b.put(address,value)
                self.assertEqual(b.call('ui_bridge_settings_init'),0)
                if address not in (0x02111944,FONT,FONT+4):self.assertEqual(b.events,[])
                else:self.assertFalse(any(e[0]=='begin' for e in b.events))
    def test_corrupt_bootstrap_and_exhausted_generation_never_allocate(self):
        for offset in range(0,40,4):
            b=BridgeBench(self.compiled);b.put(TOKEN+offset,1)
            self.assertEqual(b.call('ui_bridge_settings_init'),0);self.assertEqual(b.events,[])
            self.assertEqual(b.get(TOKEN+offset),1)
        b=BridgeBench(self.compiled);b.put(BOOT+4,0xFFFFFFFF)
        self.assertEqual(b.call('ui_bridge_settings_init'),0);self.assertEqual(b.events,[])
        self.assertEqual(b.get(BOOT+4),0xFFFFFFFF)
    def test_ordinary_null_closes_without_root_and_preserves_generation(self):
        b=BridgeBench(self.compiled);b.alloc_failure=True
        self.assertEqual(b.call('ui_bridge_settings_init'),1)
        self.assertEqual(b.get(MANAGER+28),0)
        b.put(MANAGER+16,2);self.assertEqual(b.call('ui_bridge_main'),1)
        b.put(MANAGER+16,3);self.assertEqual(b.call('ui_bridge_exit'),1)
        self.assertEqual(b.get(BOOT),0);self.assertEqual(b.get(BOOT+4),1)
        b.alloc_failure=False;b.put(MANAGER+16,1)
        b.call('ui_bridge_settings_init')
        self.assertEqual(b.get(MANAGER+28),ROOT)
        self.assertEqual(b.get(CONTEXT+8),2)
    def test_seed_and_context_identity_changes_hold_before_loading(self):
        for address in (ROOT+4624+16,ROOT+4784+16,ROOT+4720,CONTEXT,CONTEXT+4,
                        CONTEXT+8,CONTEXT+12,CONTEXT+16,CONTEXT+20,CONTEXT+24,
                        CONTEXT+36,CONTEXT+40,CONTEXT+52,CONTEXT+56,CONTEXT+60,TOKEN+4,TOKEN+8,BOOT+4):
            with self.subTest(address=hex(address)):
                b=BridgeBench(self.compiled);b.call('ui_bridge_settings_init')
                before=list(b.events);b.put(address,b.get(address)^4)
                self.assertEqual(b.call('ui_bridge_settings_init'),0)
                self.assertEqual(b.events,before)
    def test_real_composition_fits_b5_and_preserves_public_exports(self):
        code,symbols=self.compiled[0]
        self.assertLessEqual(len(code),12272)
        for name in ('ui_persistent_alloc','ui_persistent_move','ui_persistent_free',
                     'ui_module_init','ui_module_begin','ui_module_step','ui_module_cancel',
                     'ui_module_check','ui_module_release'):
            self.assertIn(name,symbols)

if __name__=='__main__':unittest.main()
