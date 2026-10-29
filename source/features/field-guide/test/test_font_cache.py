"""Temporary font ownership; execute the compiled Guide on synthetic ARM RAM.

Only allocation, cartridge transport and free are seams. Native font layout
and glyph callbacks are guarded by the installer; rapid-input latency is checked
separately on melonDS with the actual cartridge.
"""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sgp13.guide import compile_native, BASE, STATE, CANARY
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

class FontCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as d:
            cls.blob, cls.symbols = compile_native(d)

    def setUp(self):
        self.assertIn('guide_font_acquire', self.symbols,
                      'Guide still reads each glyph from the cartridge on every redraw')
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.mem_map(0x02000000, 0x400000)
        self.u.mem_write(BASE, self.blob)
        self.u.mem_write(STATE + 240, CANARY)
        self.work, self.font, self.cache = 0x02200000, 0x02201000, 0x02210000
        self.put(0x0211188c, self.work)
        self.put(self.work + 0x9c, self.font)
        for off, value in ((0, 1), (4, 0x02026111), (12, 64), (0x54, 0x02230000),
                           (0x58, 0), (0x5c, 16), (0x64, 509)):
            self.put(self.font + off, value)
        self.calls = []
        self.fail_alloc = False
        self.u.hook_add(UC_HOOK_CODE, self.hook)

    def put(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def word(self, address):
        return struct.unpack('<I', self.u.mem_read(address, 4))[0]

    def hook(self, u, address, size, _):
        if address == 0x02001000:
            u.emu_stop()
        elif address in (0x0201aa8c, 0x0200782c, 0x0201ab0c):
            args = [u.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3)]
            self.calls.append((address, args))
            if address == 0x0201aa8c:
                self.assertEqual(args[:2], [38, 509 * 64])
                u.reg_write(UC_ARM_REG_R0, 0 if self.fail_alloc else self.cache)
            elif address == 0x0200782c:
                self.assertEqual(args, [0x02230000, 0, 16, 509 * 64])
                self.assertEqual(self.word(u.reg_read(UC_ARM_REG_SP)), self.cache)
            else:
                self.assertEqual(args[0], self.cache)
                # Restore the borrowed font BEFORE releasing its backing data.
                self.assertEqual([self.word(self.font + x) for x in (0, 4, 16)],
                                 [1, 0x02026111, 0])
            u.reg_write(UC_ARM_REG_PC, u.reg_read(UC_ARM_REG_LR))

    def call(self, name):
        u = self.u
        u.reg_write(UC_ARM_REG_SP, 0x02300000)
        u.reg_write(UC_ARM_REG_LR, 0x02001001)
        u.emu_start(self.symbols[name], 0, count=100000)
        self.assertEqual(u.reg_read(UC_ARM_REG_PC), 0x02001000)
        self.assertEqual(u.reg_read(UC_ARM_REG_SP), 0x02300000)
        self.assertEqual(bytes(u.mem_read(STATE + 240, 16)), CANARY)

    def test_lazy_font_is_cached_once_and_restored_before_free(self):
        before = bytes(self.u.mem_read(self.font, 0x7c))
        self.call('guide_font_acquire')
        self.assertEqual([self.word(self.font + x) for x in (0, 4, 16)],
                         [0, 0x02026069, self.cache])
        self.call('guide_font_acquire')
        self.assertEqual(len(self.calls), 2)
        self.call('guide_font_release')
        self.call('guide_font_release')
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(bytes(self.u.mem_read(self.font, 0x7c)), before)

    def test_allocation_failure_preserves_lazy_font_and_frees_nothing(self):
        self.fail_alloc = True
        before = bytes(self.u.mem_read(self.font, 0x7c))
        self.call('guide_font_acquire')
        self.call('guide_font_release')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(bytes(self.u.mem_read(self.font, 0x7c)), before)

    def test_existing_direct_font_is_borrowed_without_taking_ownership(self):
        self.put(self.font, 0)
        self.put(self.font + 4, 0x02026069)
        self.put(self.font + 16, self.cache)
        before = bytes(self.u.mem_read(self.font, 0x7c))
        self.call('guide_font_acquire')
        self.call('guide_font_release')
        self.assertEqual(self.calls, [])
        self.assertEqual(bytes(self.u.mem_read(self.font, 0x7c)), before)

    def test_missing_or_unexpected_font_layout_uses_native_fallback(self):
        for address, value in ((0x0211188c, 0), (self.work + 0x9c, 0),
                               (self.font + 12, 0), (self.font + 12, 0xffffffff),
                               (self.font + 0x64, 0), (self.font + 0x64, 513),
                               (self.font + 4, 0x02026069), (self.font + 16, self.cache)):
            original = self.word(address)
            self.put(address, value)
            before = bytes(self.u.mem_read(self.font, 0x7c))
            self.call('guide_font_acquire')
            self.call('guide_font_release')
            self.assertEqual(self.calls, [])
            self.assertEqual(bytes(self.u.mem_read(self.font, 0x7c)), before)
            self.put(address, original)

if __name__ == '__main__':
    unittest.main()
