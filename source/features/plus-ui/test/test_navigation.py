"""Actual Plus controller with synthetic native UI calls; touch is not a mock.

The shared bench supplies allocation/render APIs. Navigation and save staging run
as compiled ARM. Runtime screenshots separately verify the native button pixels.
"""
import importlib.util
import json
import os
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unicorn.arm_const import (UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR,
    UC_ARM_REG_CPSR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
    UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5)

SOURCE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SOURCE))
from sgp13 import plus_ui

class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.main, cls.symbols, cls.context = plus_ui.compile_native(out)
        cls.nav, cls.nav_symbols = (plus_ui.compile_navigation(out, cls.symbols)
            if hasattr(plus_ui, 'compile_navigation') else (b'', {}))
        for f in (SOURCE/'features/options/prove/testi').iterdir():
            if f.is_file(): shutil.copy2(f, out/f.name)
        old = os.environ.get('SGP_UI_BUILD')
        os.environ['SGP_UI_BUILD'] = str(out)
        spec = importlib.util.spec_from_file_location('plus_navigation_bench', SOURCE/'features/options/test/banco.py')
        cls.bench = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.bench)
        if old is None: os.environ.pop('SGP_UI_BUILD')
        else: os.environ['SGP_UI_BUILD'] = old

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def make(self):
        b = self.bench.Banco(); b.stato_npc(); b.stato_anim(); b.stato_wifi()
        b.uc.mem_write(plus_ui.BASE, self.context)
        if self.nav: b.uc.mem_write(plus_ui.NAV_BASE, self.nav)
        return b

    def frame(self, b, keys=0, touch=None):
        if touch is None: b.tasti(keys)
        else: b.tocco(*touch)
        entry = self.nav_symbols.get('plus_navigation', self.symbols['sgp_ui_frame'])
        r, regs = b.chiama(entry, self.bench.APP)
        self.assertEqual(b.uc.reg_read(UC_ARM_REG_PC), 0x0230F000)
        self.assertEqual(b.uc.reg_read(UC_ARM_REG_SP), self.bench.SP0)
        self.assertEqual(regs, self.bench.CANARINI)
        return r

    def test_visible_button_touch_opens_without_changing_native_options_or_settings(self):
        for xy in ((4,172),(111,191),(56,181)):
            with self.subTest(xy=xy):
                b=self.make(); before=b.leggi_d1(); native=bytes(b.uc.mem_read(self.bench.APP,0x34))
                self.assertEqual(self.frame(b,touch=xy),1)
                self.assertEqual(b.leggi_ui()['aperta'],1)
                self.assertEqual(b.leggi_ui()['aperture'],1)
                self.assertEqual(b.leggi_d1(),before)
                self.assertEqual(bytes(b.uc.mem_read(self.bench.APP,0x34)),native)

    def test_outside_button_and_held_touch_are_passed_to_native_menu(self):
        for xy in ((3,180),(112,180),(50,171),(50,192),(130,181),(220,181),(120,30)):
            with self.subTest(xy=xy):
                b=self.make();self.assertEqual(self.frame(b,touch=xy),0)
                self.assertEqual(b.leggi_ui()['aperta'],0)
        b=self.make(); b.tocco(56,181); b.tasti(0,0)
        r,_=b.chiama(self.nav_symbols.get('plus_navigation',self.symbols['sgp_ui_frame']),self.bench.APP)
        self.assertEqual(r,0);self.assertEqual(b.leggi_ui()['aperta'],0)

    def test_select_and_cancel_apply_keep_existing_transaction_semantics(self):
        b=self.make(); before=b.leggi_d1()
        self.frame(b,keys=4);self.frame(b,keys=0x10);self.frame(b,keys=2)
        self.assertEqual(b.leggi_ui()['aperta'],0);self.assertEqual(b.leggi_d1(),before)
        self.frame(b,touch=(56,181));self.frame(b,keys=0x10);self.frame(b,keys=1)
        self.assertEqual(b.leggi_ui()['aperta'],0)
        expected={**before,'plus':1,'active_plus':1};self.assertEqual(b.leggi_d1(),expected)

    def test_button_is_redrawn_after_native_app_reuses_same_address(self):
        b=self.make();self.frame(b)
        before=[x for x in b.chiamate if x['f']=='AddWindowParameterized']
        self.assertEqual(len(before),1)
        self.assertEqual((before[0]['r'][3],*before[0]['sp'][:3]),(0,21,14,3))
        self.frame(b);self.assertNotIn('AddWindowParameterized',b.nomi_chiamate())
        b.ospite_rinasce();self.frame(b)
        self.assertIn('CopyWindowToVram',b.nomi_chiamate())

    def test_button_pixels_stay_inside_owned_window_and_native_footer_columns(self):
        b=self.make(); p=self.bench.FINTO_PIXEL; size=14*3*32
        b.uc.mem_write(p-16,b'G'*16);b.uc.mem_write(p+size,b'H'*16)
        self.frame(b)
        pixels=bytes(b.uc.mem_read(p,size))
        def pixel(x,y):
            off=((y//8)*14+x//8)*32+(y%8)*4+x//2%4
            return (pixels[off]>>(4*(x%2)))&15
        self.assertEqual(pixel(4,4),1)
        self.assertEqual(pixel(5,5),8)
        self.assertEqual(pixel(8,8),7)
        self.assertEqual(bytes(b.uc.mem_read(p-16,16)),b'G'*16)
        self.assertEqual(bytes(b.uc.mem_read(p+size,16)),b'H'*16)
        self.assertEqual(b.cella(14,21),0)

    def test_native_hook_preserves_both_caller_return_paths(self):
        for consumed in (False,True):
            b=self.make();u=b.uc;sp=self.bench.SP0
            continuation,stop=0x0230e000,0x0230f000
            b.tocco(56 if consumed else 130,181)
            u.mem_write(sp-16,struct.pack('<4I',0xc3c3c3c3,0xc4c4c4c4,0xc5c5c5c5,stop|1))
            for reg,value in ((UC_ARM_REG_SP,sp-16),(UC_ARM_REG_LR,continuation|1),
                              (UC_ARM_REG_R0,self.bench.APP),(UC_ARM_REG_R1,self.bench.GSYS+0x40),
                              (UC_ARM_REG_R2,0xc2c2c2c2),(UC_ARM_REG_CPSR,0x33)):
                u.reg_write(reg,value)
            end=stop if consumed else continuation
            u.emu_start(self.nav_symbols['plus_navigation_hook'],end,count=200000)
            self.assertEqual(u.reg_read(UC_ARM_REG_PC),end)
            self.assertEqual(u.reg_read(UC_ARM_REG_SP),sp if consumed else sp-16)
            if consumed:
                for reg,value in ((UC_ARM_REG_R3,0xc3c3c3c3),(UC_ARM_REG_R4,0xc4c4c4c4),(UC_ARM_REG_R5,0xc5c5c5c5)):
                    self.assertEqual(u.reg_read(reg),value)
            else:
                self.assertEqual(u.reg_read(UC_ARM_REG_R0),self.bench.APP)
                self.assertEqual(u.reg_read(UC_ARM_REG_R1),1)
                self.assertEqual(u.reg_read(UC_ARM_REG_R2),0xc2c2c2c2)

if __name__ == '__main__': unittest.main()
