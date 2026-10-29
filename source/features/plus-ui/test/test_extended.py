"""Execute the extended menu and legacy controller as Thumb, with UI/owner seams.

The owner seam exposes concrete snapshot/candidate/apply boundaries. Encounter
launch and persistence belong to separate native adapter and emulator tests.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_LR, UC_ARM_REG_PC
SOURCE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(SOURCE))
from sgp13 import plus_ui, shiny_core


class ExtendedMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.out=Path(cls.tmp.name)
        cls.old,cls.old_symbols,cls.context=plus_ui.compile_native(cls.out)
        cls.ext,cls.ext_symbols=(plus_ui.compile_extended(cls.out) if hasattr(plus_ui,'compile_extended') else (b'',{}))
        controller={**cls.old_symbols,'opz_apri':cls.ext_symbols.get('extended_open',0),'sgp_ui_frame':cls.ext_symbols.get('extended_frame',0)}
        cls.nav,cls.nav_symbols=plus_ui.compile_navigation(cls.out,controller)
        cls.core,cls.core_symbols=shiny_core.compile_native(cls.out/'core')
        for p in (SOURCE/'features/options/prove/testi').iterdir():
            if p.is_file():shutil.copy2(p,cls.out/p.name)
        old=os.environ.get('SGP_UI_BUILD');os.environ['SGP_UI_BUILD']=str(cls.out)
        spec=importlib.util.spec_from_file_location('extended_bench',SOURCE/'features/options/test/banco.py')
        cls.bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.bench)
        if old is None:os.environ.pop('SGP_UI_BUILD')
        else:os.environ['SGP_UI_BUILD']=old

    def make(self, available=True, reject=0, methods=1):
        self.assertIn('extended_frame',self.ext_symbols,'second-page controller is not implemented')
        b=self.bench.Banco();b.stato_npc();b.stato_anim();b.stato_wifi()
        b.uc.mem_write(0x023D7500,self.nav);b.uc.mem_write(0x023D7700,self.context)
        b.uc.mem_write(0x023CB800,self.ext);b.uc.mem_write(0x023C8100,self.core)
        cfg=bytearray(256);struct.pack_into('<IHH',cfg,0,0x594e4853,2,152)
        struct.pack_into('<3I',cfg,8,0x0230d001,0x0230d101,0x0230d201)
        struct.pack_into('<I',cfg,24,self.core_symbols['sgp_shiny_denominator'])
        struct.pack_into('<4I',cfg,64,*[self.old_symbols[n] for n in ('sgp_ui_frame','opz_apri','opz_chiudi','opz_disegna')])
        b.uc.mem_write(0x023CB100,bytes(cfg))
        rows=json.loads((SOURCE/'features/plus-ui/shiny-text.json').read_text())['EN']
        text=bytearray(len(rows)*2)
        for i,value in enumerate(rows.values()):
            struct.pack_into('<H',text,2*i,len(text));text+=struct.pack('<%dH'%(len(value)+1),*[ord(c) for c in value],65535)
        b.uc.mem_write(0x023CD800,bytes(text))
        species=[19,20,25,132,164,168,73,402]
        snapshot=struct.pack('<IIIHH8B5B3x',7,8,9,19,2048,int(available),1,10,40,methods,0,0,0,8,0,8 if methods&4 else 0,0,0)
        b.applied=[];b.printed=[]
        def owner(uc,addr,size,user):
            a,c,d,e=[uc.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
            ret=0
            if addr==0x0230d000:
                if available:uc.mem_write(c,snapshot);ret=1
            elif addr==0x0230d100:ret=species[e] if d in (0,2) and e<len(species) else 0
            elif addr==0x0230d200:
                draft=bytes(uc.mem_read(c,20));b.applied.append(draft);ret=reject
            elif addr==0x0200bcdc:
                p=0x02225000;name='SPECIES'+str(a)
                uc.mem_write(p,struct.pack('<HHI',64,len(name),0x1234)+struct.pack('<%dH'%(len(name)+1),*[ord(x) for x in name],65535));ret=p
            elif addr==0x020200fc:
                length=struct.unpack('<H',uc.mem_read(d+2,2))[0]
                b.printed.append(''.join(chr(n) for n in struct.unpack('<%dH'%length,uc.mem_read(d+8,length*2))))
                return
            else:return
            uc.reg_write(UC_ARM_REG_R0,ret);uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        b.uc.hook_add(UC_HOOK_CODE,owner)
        return b

    def frame(self,b,keys=0,touch=None):
        b.tasti(keys)
        if touch is not None:b.tocco(*touch);b.uc.mem_write(self.bench.NEWKEYS,struct.pack('<I',keys))
        r,regs=b.chiama(self.nav_symbols['plus_navigation'],self.bench.APP)
        self.assertEqual(regs,self.bench.CANARINI)
        return r

    def test_two_page_draft_cancel_preserves_old_settings_and_never_applies_owner(self):
        b=self.make();before=b.leggi_d1()
        self.frame(b,4);self.frame(b,0x10);self.frame(b,0x100);self.frame(b,0x10);self.frame(b,2)
        self.assertEqual(b.leggi_d1(),before);self.assertEqual(b.applied,[])
        self.assertEqual(b.leggi_ui()['aperta'],0)

    def test_apply_combines_pending_mode_with_original_settings_once(self):
        b=self.make();self.frame(b,4);self.frame(b,0x10);self.frame(b,0x100);self.frame(b,0x10);self.frame(b,1)
        self.assertEqual(b.leggi_d1()['plus'],1)
        self.assertEqual(len(b.applied),1)
        self.assertEqual(struct.unpack('<IIIHBBB3x',b.applied[0]),(7,8,9,19,0,0,0))
        self.frame(b,1);self.assertEqual(len(b.applied),1)

    def test_cancel_has_priority_over_apply_page_and_touch(self):
        b=self.make();self.frame(b,4);self.frame(b,0x100);self.frame(b,0x10)
        self.frame(b,1|2|0x100,touch=(40,165))
        self.assertEqual(b.applied,[]);self.assertEqual(b.leggi_ui()['aperta'],0)

    def test_target_list_scroll_cancel_and_choose_stage_species_id(self):
        b=self.make();self.frame(b,4);self.frame(b,0x100);self.frame(b,0x400)
        self.frame(b,1)  # Hunt choose target
        self.frame(b,0x100)  # advance five visible entries, including None
        self.frame(b,2)  # cancel selector, old target retained
        self.frame(b,1);self.frame(b,0x100);self.frame(b,1)  # choose list entry
        self.frame(b,2);self.frame(b,1)  # Hunt back; Plus apply
        self.assertEqual(len(b.applied),1)
        self.assertEqual(struct.unpack_from('<H',b.applied[0],12)[0],164)

    def test_hunt_queues_only_on_apply_and_draft_change_clears_it(self):
        b=self.make();self.frame(b,4);self.frame(b,0x100);self.frame(b,0x400)
        for _ in range(3):self.frame(b,0x80)
        self.frame(b,1)  # stage search; return to Plus
        self.assertEqual(b.applied,[])
        self.frame(b,1)
        self.assertEqual(len(b.applied),1);self.assertEqual(b.applied[0][16],1)
        b=self.make();self.frame(b,4);self.frame(b,0x100);self.frame(b,0x400)
        for _ in range(3):self.frame(b,0x80)
        self.frame(b,1);self.frame(b,0x10);self.frame(b,1)
        self.assertEqual(b.applied[0][16],0)

    def test_stale_owner_rejection_keeps_page_and_old_settings_uncommitted(self):
        b=self.make(reject=2);before=b.leggi_d1()
        self.frame(b,4);self.frame(b,0x10);self.frame(b,0x100);self.frame(b,0x10);self.frame(b,1)
        self.assertEqual(b.leggi_ui()['aperta'],1);self.assertEqual(b.leggi_d1(),before)
        self.frame(b,2);self.assertEqual(b.leggi_ui()['aperta'],0)

    def test_no_live_owner_keeps_old_settings_usable_and_new_controls_inactive(self):
        b=self.make(available=False);self.frame(b,4);self.frame(b,0x10);self.frame(b,0x100)
        self.frame(b,0x10);self.frame(b,0x400);self.frame(b,1)
        self.assertEqual(b.applied,[]);self.assertEqual(b.leggi_d1()['plus'],1)

    def test_header_touch_pages_and_footer_apply_obey_transaction(self):
        b=self.make();self.frame(b,4);self.frame(b,touch=(210,25));self.frame(b,0x10)
        self.frame(b,touch=(40,165));self.assertEqual(len(b.applied),1)

    def test_unavailable_page_does_not_advertise_default_odds_or_progress(self):
        b=self.make(available=False);self.frame(b,4);b.printed=[];self.frame(b,0x100)
        self.assertNotIn('1/512',b.printed)
        self.assertGreaterEqual(b.printed.count('Unavailable'),4)

    def test_idle_open_page_does_not_allocate_or_repaint_each_frame(self):
        b=self.make();self.frame(b,4);self.frame(b)
        self.assertNotIn('AddWindowParameterized',b.nomi_chiamate())
        self.assertNotIn('String_New',b.nomi_chiamate())

    def test_owner_error_from_first_page_returns_visible_shiny_feedback(self):
        b=self.make(reject=2);self.frame(b,4);self.frame(b,0x100);self.frame(b,0x10);self.frame(b,0x200)
        b.printed=[];self.frame(b,1)
        self.assertEqual(b.leggi_ui()['aperta'],1)
        self.assertIn('Shiny 2/2',b.printed)

    def test_short_legacy_page_footer_still_applies_shiny_draft_atomically(self):
        b=self.make();b.stato_anim(guardia=0)
        self.frame(b,4);self.assertEqual(b.leggi_ui()['n_vis'],4)
        self.frame(b,0x100);self.frame(b,0x10);self.frame(b,0x200)
        footer=(b.leggi_ui()['ycont']+3*(b.leggi_ui()['n_righe']-1))*8
        self.frame(b,touch=(40,footer+5))
        self.assertEqual(len(b.applied),1)
        self.assertEqual(b.leggi_ui()['aperta'],0)

    def test_page_window_failure_cancels_pending_changes_and_releases_string(self):
        b=self.make();before=b.leggi_d1();self.frame(b,4);self.frame(b,0x10)
        def fail_window(uc,address,size,user):
            if address==0x0201d40c:
                window=b.chiamate[-1]['r'][1]
                uc.mem_write(window+12,bytes(4))
        b.uc.hook_add(UC_HOOK_CODE,fail_window)
        self.frame(b,0x100)
        self.assertEqual(b.leggi_ui()['aperta'],0)
        self.assertEqual(b.leggi_d1(),before);self.assertEqual(b.applied,[])
        self.assertEqual(b.nomi_chiamate().count('String_Delete'),1)

    def test_fresh_touch_precedes_apply_and_page_keys(self):
        for keys,xy in ((1,(40,55)),(0x100,(190,165))):
            b=self.make();before=b.leggi_d1();self.frame(b,4);self.frame(b,0x10)
            self.frame(b,keys,touch=xy)
            self.assertEqual(b.applied,[]);self.assertEqual(b.leggi_d1(),before)
            self.assertEqual(b.leggi_ui()['aperta'],int(keys==1))

    def test_root_pages_clamp_and_retain_each_cursor(self):
        b=self.make();self.frame(b,4);self.frame(b,0x80);self.frame(b,0x200)
        b.printed=[];self.frame(b,0x100);self.frame(b,0x80);self.frame(b,0x80)
        self.frame(b,0x100);self.assertEqual(bytes(b.uc.mem_read(0x023CE800+56,3)),bytes([1,0,2]))
        self.frame(b,0x200);self.assertEqual(b.leggi_ui()['cursore'],1)
        self.frame(b,0x100);self.assertEqual(bytes(b.uc.mem_read(0x023CE800+56,3)),bytes([1,0,2]))

    def test_method_only_apply_reaches_owner_without_resetting_target(self):
        b=self.make(methods=5);self.frame(b,4);self.frame(b,0x100);self.frame(b,0x400)
        self.frame(b,0x80);self.frame(b,0x10);self.frame(b,2);self.frame(b,1)
        self.assertEqual(len(b.applied),1)
        self.assertEqual(struct.unpack('<IIIHBBB3x',b.applied[0]),(7,8,9,19,1,2,0))

    def test_toggle_revert_preserves_chain_and_does_not_apply_owner(self):
        b=self.make();self.frame(b,4);self.frame(b,0x100);self.frame(b,0x10);b.printed=[]
        self.frame(b,0x10);self.assertIn('1/2048',b.printed)
        self.frame(b,1);self.assertEqual(b.applied,[])

@unittest.skipUnless(os.environ.get('SGP13_BASE_DIR') and os.environ.get('SGP_PRET_SOURCE'),
                     'needs private ROM font and pinned charmap')
class ExtendedText(unittest.TestCase):
    def test_bilingual_text_and_all_species_names_fit_native_rows(self):
        self.assertTrue(hasattr(plus_ui,'shiny_labels'),'new native text bank is not implemented')
        for language in ('EN','IT'):
            rom=Path(os.environ['SGP13_BASE_DIR'])/('sgp-1.2.5-'+language+'.nds')
            payload,report=plus_ui.shiny_labels(rom,language,Path(os.environ['SGP_PRET_SOURCE'])/'charmap.txt')
            self.assertLessEqual(len(payload),4096)
            self.assertEqual(report['species_names_checked'],493)
            self.assertTrue(report['known_glyphs'])

    def test_overflowing_authored_copy_is_rejected(self):
        self.assertTrue(hasattr(plus_ui,'shiny_labels'),'new native text bank is not implemented')
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            original=json.loads((plus_ui.FEATURE/'shiny-text.json').read_text())
            original['EN']['RULE_0']='W'*50
            Path(d,'shiny-text.json').write_text(json.dumps(original))
            with patch.object(plus_ui,'FEATURE',Path(d)):
                with self.assertRaisesRegex(ValueError,'width'):
                    plus_ui.shiny_labels(Path(os.environ['SGP13_BASE_DIR'])/'sgp-1.2.5-EN.nds','EN',Path(os.environ['SGP_PRET_SOURCE'])/'charmap.txt')
