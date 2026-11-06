"""Class B: the expanded-Bag constructor must tolerate Heap_Alloc failure.

The exact EN/IT V4 inputs are patched only in memory.  Unicorn substitutes the
allocator and executes the installed Thumb function, including its real
``cap_clear`` success path.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP

from sgp12.rom import Arm9
from . import bag_alloc


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
INPUTS = {
    'EN': (os.environ.get('SGP_BAG_ALLOC_ROM_EN') or V4_ROOT / 'candidate-v4-EN.nds',
           '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
    'IT': (os.environ.get('SGP_BAG_ALLOC_ROM_IT') or V4_ROOT / 'candidate-v4-IT.nds',
           '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'),
}
REQUIRE = os.environ.get('SGP_BAG_ALLOC_REQUIRE_INPUTS') == '1'
BASE = 0x02000000
ALLOC = 0x0201AA8C
HEAP = 0x02240000
STOP = 0x023AF000
STACK = 0x023B0000


def unicorn_works():
    """Probe in a child: Unicorn 2.1.4 may SIGILL in mem_map on macOS arm64."""
    probe = subprocess.run(
        [sys.executable, '-c',
         'from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB; '
         'u=Uc(UC_ARCH_ARM,UC_MODE_THUMB); u.mem_map(0x2000000,0x1000)'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    return probe.returncode == 0


def image(case, language):
    path, digest = INPUTS[language]
    path = Path(path)
    if not path.is_file():
        reason = 'private %s V4 input missing: %s' % (language, path)
        if REQUIRE:
            case.fail(reason)
        case.skipTest(reason)
    raw = path.read_bytes()
    case.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
    return raw


class ConstructorBench:
    def __init__(self, rom, fail):
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.mu.mem_map(BASE, 0x400000)
        arm = Arm9.from_bytes(rom)
        for base, offset, size in arm.segmenti:
            if BASE <= base and base + size <= BASE + 0x400000:
                self.mu.mem_write(base, bytes(arm.raw[offset:offset + size]))
        self.mu.mem_write(STOP, b'\x00\xbe')
        self.fail = fail
        self.calls = 0
        self.mu.hook_add(UC_HOOK_CODE, self._hook, begin=ALLOC, end=ALLOC)
        self.mu.hook_add(UC_HOOK_CODE, self._hook, begin=STOP, end=STOP)

    def _hook(self, uc, address, size, user):
        if address == STOP:
            uc.emu_stop()
            return
        self.calls += 1
        assert uc.reg_read(UC_ARM_REG_R1) == bag_alloc.BAG_BYTES
        uc.reg_write(UC_ARM_REG_R0, 0 if self.fail else HEAP)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def call(self):
        self.mu.reg_write(UC_ARM_REG_R0, 4)
        self.mu.reg_write(UC_ARM_REG_SP, STACK)
        self.mu.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.mu.emu_start(bag_alloc.ENTRY | 1, STOP, count=100000)
        return self.mu.reg_read(UC_ARM_REG_R0)


class BagAllocRomTests(unittest.TestCase):
    def test_exact_en_it_failure_returns_null_without_touching_zero(self):
        if not unicorn_works():
            self.skipTest('local Unicorn engine SIGILLs before guest execution')
        for language in ('EN', 'IT'):
            before = image(self, language)
            after, receipt = bag_alloc.apply(before, language)
            with self.subTest(language=language):
                self.assertTrue(bag_alloc.verify(before, after, receipt)['null_safe'])
                bench = ConstructorBench(after, fail=True)
                self.assertEqual(bench.call(), 0)
                self.assertEqual(bench.calls, 1)

    def test_success_still_clears_the_entire_private_bag(self):
        if not unicorn_works():
            self.skipTest('local Unicorn engine SIGILLs before guest execution')
        before = image(self, 'EN')
        after, _ = bag_alloc.apply(before, 'EN')
        bench = ConstructorBench(after, fail=False)
        pattern = bytes([0xA5]) * bag_alloc.BAG_BYTES
        bench.mu.mem_write(HEAP, pattern)
        self.assertEqual(bench.call(), HEAP)
        self.assertEqual(bytes(bench.mu.mem_read(HEAP, bag_alloc.BAG_BYTES)),
                         bytes(bag_alloc.BAG_BYTES))
        self.assertEqual(bench.calls, 1)

    def test_reader_refuses_missing_guard_and_any_extra_change(self):
        before = image(self, 'EN')
        after, receipt = bag_alloc.apply(before, 'EN')
        damaged = bytearray(after)
        at = Arm9.from_bytes(after).off(bag_alloc.ENTRY, len(bag_alloc.POSTIMAGE))
        damaged[at + 12] ^= 1
        with self.assertRaises(ValueError):
            bag_alloc.verify(before, bytes(damaged), receipt)
        damaged = bytearray(after)
        damaged[0x300] ^= 1
        with self.assertRaisesRegex(ValueError, 'outside'):
            bag_alloc.verify(before, bytes(damaged), receipt)


if __name__ == '__main__':
    unittest.main()
