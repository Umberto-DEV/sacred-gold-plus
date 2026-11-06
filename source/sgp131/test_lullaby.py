"""Native Thumb regression for the Lullaby arithmetic; no game file needed."""
import hashlib
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4

from . import lullaby as L


def run_tail(raw, rate, *, offset=0):
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    cpu.mem_map(0x02240000, 0x10000)
    cpu.mem_write(L.SITE + offset, raw)
    cpu.reg_write(UC_ARM_REG_R0, 2)
    cpu.reg_write(UC_ARM_REG_R4, rate)
    cpu.emu_start((L.SITE + offset) | 1, L.SITE + 20, count=16)
    return cpu.reg_read(UC_ARM_REG_R4)


class Arithmetic(unittest.TestCase):
    def test_original_wrap_is_reproduced_and_corrected_for_every_u8_input(self):
        for rate in range(256):
            with self.subTest(rate=rate):
                self.assertEqual(run_tail(L.BEFORE[8:], rate, offset=8), min((rate - 25) & 255, 100))
                self.assertEqual(run_tail(L.AFTER, rate), min(max(rate - 25, 0), 100))

    def test_other_radio_paths_enter_the_unchanged_cap(self):
        for rate in range(256):
            self.assertEqual(self.cap(L.BEFORE, rate), self.cap(L.AFTER, rate))

    @staticmethod
    def cap(raw, rate):
        cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        cpu.mem_map(0x02240000, 0x10000)
        cpu.mem_write(L.SITE, raw)
        cpu.reg_write(UC_ARM_REG_R4, rate)
        cpu.emu_start((L.SITE + 14) | 1, L.SITE + 20, count=8)
        return cpu.reg_read(UC_ARM_REG_R4)

    def test_guard_and_complement(self):
        image = bytearray(L.SIZE)
        offset = L.SITE - L.BASE
        image[offset:offset + 20] = L.BEFORE
        pin = hashlib.sha256(image[L.START-L.BASE:L.END-L.BASE]).hexdigest()
        patched = L.patch_overlay(image, function_sha256=pin)
        L.verify_images(bytes(image), patched, function_sha256=pin)
        for index in (0, offset - 2, offset, offset + 3, offset + 20, L.SIZE - 1):
            altered = bytearray(patched)
            altered[index] ^= 1
            with self.assertRaises(ValueError):
                L.verify_images(bytes(image), bytes(altered), function_sha256=pin)
        with self.assertRaises(ValueError):
            L.patch_overlay(patched, function_sha256=pin)


if __name__ == '__main__':
    unittest.main()
