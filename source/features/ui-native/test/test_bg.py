"""Compiled Class A storage/state contract with declared native seams."""
import tempfile
import unittest
from pathlib import Path
from bg_bench import *
class BgTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='bg-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_bg(Path(cls.temp.name))
    def test_retirement_keeps_both_displays_black_for_the_native_field_fade(self):
        b=BgBench(self.compiled);b.create();b.bgcreate();b.prepared_display()
        self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1)
        self.assertEqual((b.get(0x0400006c,2),b.get(0x0400106c,2)),(0x8010,0x8010))
        self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_static_native_ball_admission_refuses_unverified_source_without_writes(self):
        self.assertIn('ui_bg_install_ball',self.compiled[1])
        b=BgBench(self.compiled);b.create();b.bgcreate();b.prepared_display()
        b.put(0x0400006c,0x8010,2)
        source=0x02370000;b.u.mem_write(source,bytes(3552))
        before=bytes(b.u.mem_read(STATE,176)),len(b.calls)
        self.assertEqual(b.call('ui_bg_install_ball',TOKEN,STATE,1,source,3552),0)
        self.assertEqual((bytes(b.u.mem_read(STATE,176)),len(b.calls)),before)
    def test_guide_owns_nine_roots_and_unwinds_every_acquisition(self):
        for failure in (None, *range(1,10)):
            b=BgBench(self.compiled);self.assertEqual(b.create(0x40000),1);b.fail_at=failure
            self.assertEqual(b.call('ui_bg_create_guide',TOKEN,STATE,1),int(failure is None))
            if failure is None:
                self.assertEqual(b.get(b.counts+76,2),9)
                self.assertEqual(b.get(STATE+172),1)
                roots=[b.get(STATE+16+4*i) for i in range(5)]+[b.get(STATE+120+4*i) for i in range(4)]
                start=len(b.calls);self.assertEqual(b.bgdestroy(),1)
                self.assertEqual([args[1]+16 for p,args in b.calls[start:] if p==FREE],roots[::-1])
            self.assertEqual(b.get(b.counts+76,2),0);self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
    def test_explicit_unframed_decision_is_once_only_and_requires_complete_rows(self):
        b=BgBench(self.compiled);b.create();b.bgcreate();b.prepared_display()
        self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),STATE+36)
        start=len(b.calls)
        self.assertEqual(b.call('ui_bg_unframed',TOKEN,STATE,1),1)
        self.assertEqual(len(b.calls),start)
        self.assertEqual(b.call('ui_bg_unframed',TOKEN,STATE,1),0)
        self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),0)
        b.put(STATE+92,0x3fffff)
        self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),1)
        self.assertEqual(b.call('ui_bg_unframed',TOKEN,STATE,1),0)
    def test_retained_begin_preserves_map_and_invalidation_requires_fresh_rows(self):
        b=BgBench(self.compiled);b.create();b.bgcreate();b.prepared_display()
        b.put(STATE+68,1);b.put(STATE+96,1);b.put(STATE+92,0x3fffff)
        pixels=b.get(STATE+28);mapping=b.get(STATE+20)
        b.u.mem_write(pixels,b'P'*21120);b.u.mem_write(mapping,b'M'*2048)
        self.assertEqual(b.call('ui_bg_begin_retained',TOKEN,STATE,1,0,1,0x200001),STATE+36)
        self.assertEqual(b.get(STATE+92),0x1ffffe)
        self.assertEqual(bytes(b.u.mem_read(pixels,21120)),b'P'*21120)
        self.assertEqual(bytes(b.u.mem_read(mapping,2048)),b'M'*2048)
        self.assertEqual(b.call('ui_bg_invalidate_rows',TOKEN,STATE,1,2),1)
        self.assertEqual(b.get(STATE+92),0x1ffffc)
        self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,2),0)
    def test_storage_phase_cannot_bypass_live_display_ownership(self):
        b=BgBench(self.compiled);b.create();b.bgcreate();b.prepared_display();b.put(STATE+12,1)
        self.assertEqual(b.bgdestroy(),0)
        self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),0)
        self.assertEqual(b.get(b.counts+76,2),5)
    def test_malformed_inactive_state_is_not_reported_retired(self):
        b=BgBench(self.compiled);b.create();b.put(STATE+16,0x02290000)
        self.assertEqual(b.bgdestroy(),0)
        self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),0)
    def test_front_pending_version_and_deadline_with_declared_native_boundaries(self):
        b=BgBench(self.compiled);b.create();b.bgcreate();b.prepared_display()
        self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),STATE+36)
        b.put(STATE+92,0x3fffff);b.put(STATE+96,1)
        self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),1)
        self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,1),0)
        for line,want in ((191,0),(241,0),(192,1)):
            b.put(0x04000006,line,2);self.assertEqual(b.call('ui_bg_publish',STATE,1,240),want)
        self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),0)
        self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,1),STATE+52)
        self.assertEqual(b.call('ui_bg_ready',TOKEN,STATE,1,1),0)
        self.assertEqual(b.call('ui_bg_retire',TOKEN,STATE,1),1);self.assertEqual(b.bgdestroy(),1)
    def test_free_refusal_retains_owned_roots_and_ledger(self):
        b=BgBench(self.compiled);b.create();b.bgcreate();before=bytes(b.u.mem_read(STATE,120)),b.token()
        b.free_refuse=True;self.assertEqual(b.bgdestroy(),0)
        self.assertEqual((bytes(b.u.mem_read(STATE,120)),b.token()),before)
        b.free_refuse=False;self.assertEqual(b.bgdestroy(),1)
    def test_generation_geometry_and_alias_refuse_before_native_boundary(self):
        b=BgBench(self.compiled);b.create();b.bgcreate();b.prepared_display()
        for offset,value,width in ((43,0,1),(44,23,1),(48,b.get(STATE+32),4),(20,0xfffffffc,4)):
            old=b.get(STATE+offset,width);b.put(STATE+offset,value,width);start=len(b.calls)
            self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,1,0),0);self.assertEqual(len(b.calls),start)
            b.put(STATE+offset,old,width)
        self.assertEqual(b.call('ui_bg_begin',TOKEN,STATE,2,0),0)
    def test_all_five_fault_positions_release_only_acquired_roots(self):
        for failure in range(1,6):
            b=BgBench(self.compiled);self.assertEqual(b.create(),1)
            b.fail_at=failure
            self.assertEqual(b.bgcreate(),0)
            self.assertEqual(b.get(b.counts+76,2),0)
            self.assertEqual(b.bgdestroy(),1)
            self.assertEqual(b.destroy(),1)
    def test_owned_pointer_mutation_holds_every_allocation(self):
        b=BgBench(self.compiled);b.create();self.assertEqual(b.bgcreate(),1)
        root=b.get(STATE+16);b.put(STATE+16,root+4)
        self.assertEqual(b.bgdestroy(),0)
        self.assertEqual(b.get(b.counts+76,2),5)
        b.put(STATE+16,root);self.assertEqual(b.bgdestroy(),1)
    def test_five_checked_roots_and_reverse_unwind(self):
        b=BgBench(self.compiled);self.assertEqual(b.create(),1)
        self.assertEqual(b.bgcreate(),1)
        roots=[b.get(STATE+16+4*i) for i in range(5)]
        self.assertTrue(all(roots));self.assertEqual(b.get(b.counts+76,2),5)
        start=len(b.calls);self.assertEqual(b.bgdestroy(),1)
        freed=[args[1]+16 for p,args in b.calls[start:] if p==FREE]
        self.assertEqual(freed,roots[::-1]);self.assertEqual(b.get(b.counts+76,2),0)
        self.assertEqual(b.bgdestroy(),1);self.assertEqual(b.destroy(),1)
if __name__=='__main__':unittest.main()
