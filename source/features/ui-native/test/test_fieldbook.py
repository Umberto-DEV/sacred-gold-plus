"""Finite field-menu behavior gates; source compilation is not installation."""
import os
import tempfile
import unittest
from fieldbook_bench import *

class FieldbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='fieldbook-a-');cls.addClassCleanup(cls.temp.cleanup)
        cls.compiled=compile_fieldbook(cls.temp.name,scaffold=os.environ.get('SGP_FIELDBOOK_SCAFFOLD')=='1')
    def closed_touch(self):
        b=FieldbookTouchFrameBench(self.compiled);b.put(FIELD+0xd2,0,1)
        b.call('fieldbook_create',MENU)
        b.put(SYS+0x60,125,2);b.put(SYS+0x62,155,2)
        b.put(SYS+0x64,1,2);b.put(SYS+0x66,1,2)
        return b
    def test_closed_menu_frame_preserves_fresh_touch_arm_for_native_mailbox(self):
        b=self.closed_touch();self.assertEqual(b.get(STATE+20),12)
        b.call('fieldbook_frame',TASK,MENU)
        self.assertEqual(b.get(FIELD+0xd0,2),32)
        self.assertEqual(b.get(STATE+20),11);self.assertEqual(b.get(STATE+28),8)
        self.assertEqual(b.get(FIELD+0xd2,1),0) # No fabricated wake state.
    def test_passive_deselection_preserves_release_arm(self):
        b=FieldbookBench(self.compiled);self.select(b);b.put(FIELD+0xd2,0,1)
        b.put(SYS+0x48,0);b.put(SYS+0x64,1,2)
        b.call('fieldbook_frame',TASK,MENU)
        self.assertEqual(b.get(STATE+20),12)
    def test_closed_touch_retains_cancel_and_admission_refusals(self):
        for refusal in ('b','x','foreign','moving','fade','direction','owner'):
            with self.subTest(refusal=refusal):
                b=self.closed_touch()
                if refusal in ('b','x','direction'):b.put(SYS+0x48,{'b':2,'x':1024,'direction':16}[refusal])
                if refusal=='foreign':b.put(FIELD+0xd0,7,2)
                if refusal=='moving':b.moving=True
                if refusal=='fade':b.fade_done=False
                if refusal=='owner':b.put(CONTROL+8,FIELD+4)
                b.call('fieldbook_frame',TASK,MENU)
                self.assertEqual(b.get(FIELD+0xd0,2),7 if refusal=='foreign' else 0)
                self.assertEqual(b.get(STATE+28),0)
    def test_closed_touch_held_does_not_restart_feedback_and_release_repress_arms(self):
        b=self.closed_touch();b.call('fieldbook_frame',TASK,MENU)
        self.assertEqual(b.get(FIELD+0xd0,2),32)
        b.put(SYS+0x64,0,2)
        for expected in (7,6,5):
            b.call('fieldbook_frame',TASK,MENU)
            self.assertEqual(b.get(STATE+28),expected)
        # Explicit cancel then held (no new edge) must not queue another command.
        b.put(SYS+0x48,2);b.call('fieldbook_frame',TASK,MENU)
        b.put(SYS+0x48,0);b.call('fieldbook_frame',TASK,MENU)
        self.assertEqual(b.get(FIELD+0xd0,2),0)
        b.put(SYS+0x66,0,2);b.call('fieldbook_frame',TASK,MENU)
        b.put(SYS+0x64,1,2);b.put(SYS+0x66,1,2)
        b.call('fieldbook_frame',TASK,MENU)
        self.assertEqual(b.get(FIELD+0xd0,2),32);self.assertEqual(b.get(STATE+28),8)
    def test_select_guide_retires_all_native_focus_without_invalid_index(self):
        b=FieldbookBench(self.compiled);b.call('fieldbook_create',MENU);b.put(SYS+0x48,16)
        b.call('fieldbook_dpad',MENU)
        modes=[args[:2] for a,args in b.events if a==0x02024B78]
        self.assertEqual(modes,[(0x022B0000+i*0x100,1) for i in range(9)])
        self.assertEqual(b.get(MENU+20),3)
    def test_cancel_preserves_unowned_foreign_command32(self):
        b=FieldbookBench(self.compiled);b.put(FIELD+0xD0,32,2);b.put(SYS+0x48,2)
        self.assertEqual(b.call('fieldbook_task_input',TM),7)
        self.assertEqual(b.get(FIELD+0xD0,2),32)
    def select(self,b):
        b.call('fieldbook_create',MENU);b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
        b.events.clear()
    def test_held_a_rearm_cannot_dispatch_previous_native_item(self):
        b=FieldbookBench(self.compiled);b.put(SYS+0x44,1);self.select(b)
        b.put(SYS+0x48,1)
        self.assertEqual(b.call('fieldbook_task_input',TM),0)
        self.assertNotIn(0x0203C47C,[a for a,_ in b.events])
        self.assertEqual(b.get(FIELD+0xD0,2),0)
    def test_pending_a_and_touch_share_nine_frames_and_omit_native_confirmation(self):
        for touch in (False,True):
            b=FieldbookBench(self.compiled);self.select(b)
            if touch:
                b.put(SYS+0x48,0);b.put(SYS+0x60,120,2);b.put(SYS+0x62,150,2);b.put(SYS+0x64,1,2)
                self.assertEqual(b.call('fieldbook_touch',MENU),0)
            else:
                b.put(SYS+0x48,1);self.assertEqual(b.call('fieldbook_task_input',TM),0)
            self.assertEqual(b.get(FIELD+0xD0,2),32)
            b.put(SYS+0x48,0);b.put(SYS+0x64,0,2)
            for _ in range(9):
                self.assertEqual(b.call('fieldbook_task_input',TM),0)
                b.call('fieldbook_frame',TASK,MENU)
            self.assertEqual(b.call('fieldbook_task_input',TM),1)
            self.assertEqual(b.get(ENV+0x354),b.symbols['fieldbook_launch'])
            self.assertEqual(b.get(ENV+0x26,2),4)
            self.assertEqual(b.get(FIELD+0xD0,2),0)
            self.assertEqual(b.get(STATE+4),0)
            self.assertNotIn(0x021F6B50,[a for a,_ in b.events])
            self.assertNotIn(0x0203C47C,[a for a,_ in b.events])
    def test_b_or_x_releases_only_owned_command_before_native_delegate(self):
        for key in (2,1024):
            b=FieldbookBench(self.compiled);self.select(b);b.put(SYS+0x48,1)
            b.call('fieldbook_task_input',TM);b.put(SYS+0x48,key)
            self.assertEqual(b.call('fieldbook_task_input',TM),7)
            self.assertEqual(b.get(FIELD+0xD0,2),0)
            self.assertEqual(b.get(STATE+28),0)
    def test_lost_live_task_never_clears_new_owners_command(self):
        b=FieldbookBench(self.compiled);self.select(b);b.put(SYS+0x48,1);b.call('fieldbook_task_input',TM)
        b.put(CONTROL+4,0x023D7B20);b.put(SYS+0x48,2)
        self.assertEqual(b.call('fieldbook_task_input',TM),7)
        self.assertEqual(b.get(FIELD+0xD0,2),32)
    def test_arrow_exit_uses_available_native_slot(self):
        b=FieldbookBench(self.compiled);self.select(b)
        b.put(MENU+0x470+6*8,0,1);b.put(SYS+0x48,64);b.call('fieldbook_dpad',MENU)
        self.assertEqual(b.get(MENU+20),0)
        self.assertEqual(b.get(FIELD+0xD3,1),0)
        self.assertFalse(b.get(STATE+20)&1)
    def test_foreign_confirmation_is_preserved_and_blocks_selection(self):
        b=FieldbookBench(self.compiled);b.call('fieldbook_create',MENU);b.put(MENU+0x51C,32)
        b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
        self.assertFalse(b.get(STATE+20)&1);self.assertEqual(b.get(MENU+0x51C),32)
    def test_constructor_reuse_and_special_type_refuse_old_owner(self):
        b=FieldbookBench(self.compiled);self.select(b);before=b.get(STATE+16)
        b.put(MENU+0x51C,2);b.call('fieldbook_create',MENU)
        self.assertEqual(b.get(STATE+16),before+1);self.assertEqual(b.get(STATE+4),0)
        b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
        self.assertFalse(b.get(STATE+20)&1)
    def test_draw_preserves_label_metadata_and_foreign_palette_banks(self):
        b=FieldbookBench(self.compiled);b.call('fieldbook_create',MENU)
        label=bytes(b.u.mem_read(MENU+0x450,32));b.u.mem_write(0x05000400,b'\x45\x12'*256)
        for i in range(32):b.put(MENU+0x4CC+2*i,(i*311)&32767,2)
        before=bytes(b.u.mem_read(0x05000400,512));b.put(SYS+0x48,0)
        b.call('fieldbook_frame',TASK,MENU)
        after=bytes(b.u.mem_read(0x05000400,512))
        self.assertEqual(after[:160],before[:160]);self.assertEqual(after[192:],before[192:])
        self.assertEqual(bytes(b.u.mem_read(MENU+0x450,32)),label)
        self.assertEqual(b.get(0x050004A2,2),0x1245)
        self.assertEqual(len([a for a,_ in b.events if a==0x02026354]),1)
        b.call('fieldbook_frame',TASK,MENU)
        self.assertEqual(len([a for a,_ in b.events if a==0x0201D40C]),1)
    def test_native_window_null_alloc_has_no_free_or_pixels_write(self):
        b=FieldbookBench(self.compiled);b.call('fieldbook_create',MENU);b.events.clear();b.allocation_failure=True
        b.put(STATE+24,0);b.call('fieldbook_frame',TASK,MENU)
        self.assertNotIn(0x0201D520,[a for a,_ in b.events]);self.assertEqual(b.get(STATE+24),0)
    def test_template_launch_and_resident_return_use_null_args(self):
        b=FieldbookBench(self.compiled);b.call('fieldbook_launch',TM)
        self.assertIn((FIELD,TEMPLATE,0),[args[:3] for a,args in b.events if a==0x0203DFB4])
        self.assertEqual(b.get(ENV+0x354),b.symbols['fieldbook_return'])
        b.call('fieldbook_return',TM);self.assertEqual(b.get(ENV+0x26,2),15)
    def test_constructor_book_allocation_failure_refuses_feature(self):
        b=FieldbookBench(self.compiled);b.allocation_failure=True;b.call('fieldbook_create',MENU)
        b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
        self.assertEqual(b.get(STATE+4),0)
        self.assertNotIn(0x02024B78,[a for a,_ in b.events])
    def test_constructor_exhausted_generation_invalidates_old_identity_without_foreign_clear(self):
        b=FieldbookBench(self.compiled);self.select(b)
        b.put(STATE+16,0xffffffff);b.put(FIELD+0xD0,32,2)
        b.call('fieldbook_create',MENU)
        self.assertEqual(b.get(STATE+16),0xffffffff)
        self.assertEqual(b.get(STATE+4),0)
        self.assertEqual(b.get(STATE+20),0)
        self.assertEqual(b.get(FIELD+0xD0,2),32)
        b.events.clear();b.put(SYS+0x48,16);b.call('fieldbook_dpad',MENU)
        self.assertNotIn(0x02024B78,[a for a,_ in b.events])
    def test_failed_pressed_redraw_does_not_advance_feedback(self):
        b=FieldbookBench(self.compiled);self.select(b);b.put(SYS+0x48,1);b.call('fieldbook_task_input',TM)
        b.put(SYS+0x48,0);b.allocation_failure=True;b.call('fieldbook_frame',TASK,MENU)
        self.assertEqual(b.get(STATE+28),9)
    def test_live_task_reuse_prevents_old_focus_and_dpad_ownership(self):
        b=FieldbookBench(self.compiled);self.select(b);b.put(TASK+20,0x0225A321)
        b.events.clear();b.put(SYS+0x48,64);b.call('fieldbook_dpad',MENU)
        self.assertNotIn(0x02024B78,[a for a,_ in b.events])
        self.assertEqual(b.get(MENU+20),3)
    def test_each_live_traversal_domain_and_self_check_refuses_ownership(self):
        corruptions=((0x021D4158,FIELD+4),(FIELD+0xd8,0x023D7B20),
            (CONTROL_TASK+16,CONTROL+1),(CONTROL,0x101),(CONTROL+8,FIELD+4),
            (CONTROL+4,TASK+1),(TASK+16,MENU+1),(TASK+20,0x0225a321),
            (MENU+8,TASK+4),(MENU+16,FIELD+4),(MENU+0x51c,2))
        for p,v in corruptions:
            with self.subTest(address=hex(p)):
                b=FieldbookBench(self.compiled);self.select(b);b.put(p,v);b.events.clear()
                b.call('fieldbook_focus',MENU+0x390,3)
                self.assertNotIn(0x02024B78,[a for a,_ in b.events])
                self.assertIn(0x0225B4AC,[a for a,_ in b.events])
    def test_two_effect_omission_mutants_are_killed_after_green_control(self):
        def cancel(compiled):
            b=FieldbookBench(compiled);self.select(b);b.put(SYS+0x48,1)
            b.call('fieldbook_task_input',TM);b.put(SYS+0x48,2);b.call('fieldbook_task_input',TM)
            return b.get(FIELD+0xd0,2)
        # Select clears the constructor events: measure a fresh focus callback.
        def focus(compiled):
            b=FieldbookBench(compiled);self.select(b);b.call('fieldbook_focus',MENU+0x390,3)
            return len([a for a,_ in b.events if a==0x02024b78])
        self.assertEqual(focus(self.compiled),9);self.assertEqual(cancel(self.compiled),0)
        for mutation,probe,wrong in ((('if(s)Mode(s,1);','(void)s;'),focus,0),
            (('U16(fs,0xd0)=0;','(void)fs;'),cancel,32)):
            with tempfile.TemporaryDirectory(prefix='fieldbook-mutant-') as directory:
                mutated=compile_fieldbook(directory,mutation=mutation)
                self.assertEqual(probe(mutated),wrong)
