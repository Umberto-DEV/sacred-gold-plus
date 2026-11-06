"""HG-F20-SU immutable V4, BLZ and native-component regression tests."""
from pathlib import Path
import hashlib
import struct
import unittest

import ndspy.rom

from sgp12.blz import ndspy_load_arm9_sicuro, ndspy_load_overlays_sicuri
from sgp131 import battle_animation_spit_up as spit_up


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           '6bf20779aa39b7be3ce7534fcf8f0501c999a06c293513f1c30a30cec0916781'),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           '3601192c21ffbe5a1b792b8b1ac12da887b9cd4b5712cc8263294dc2e22a6c62'),
}


def candidate(language):
    path = V4_ROOT / f'candidate-v4-{language}.nds'
    if not path.is_file():
        raise unittest.SkipTest('immutable V4 candidate unavailable: ' + str(path))
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == V4[language][0]
    return path, raw


class NativeSpitUp:
    CTX = 0x03000000
    SPRITE = 0x03001000
    DUMMY = 0x03002000
    STACK = 0x03810000
    SENTINEL = 0x03F00000

    def __init__(self, raw, cleanup):
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC,
                                       UC_ARM_REG_R0, UC_ARM_REG_R1,
                                       UC_ARM_REG_SP)

        self.reg = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_PC,
                    UC_ARM_REG_LR, UC_ARM_REG_SP)
        rom = ndspy.rom.NintendoDSRom(raw)
        arm9 = ndspy_load_arm9_sicuro(rom)
        overlay = ndspy_load_overlays_sicuri(rom, [spit_up.OVERLAY_ID])[
            spit_up.OVERLAY_ID]
        image = bytearray(overlay.data)
        self.assert_preimage(image)
        image[spit_up.CLEANUP_OFFSET:
              spit_up.CLEANUP_OFFSET + spit_up.CLEANUP_SIZE] = cleanup

        cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        cpu.mem_map(0x01FF0000, 0x10000)
        cpu.mem_map(0x02000000, 0x800000)
        cpu.mem_map(0x03000000, 0x10000)
        cpu.mem_map(0x03800000, 0x20000)
        cpu.mem_map(self.SENTINEL, 0x1000)
        for section in arm9.sections:
            cpu.mem_write(section.ramAddress, bytes(section.data))
        cpu.mem_write(overlay.ramAddress, bytes(image))
        cpu.hook_add(UC_HOOK_CODE, self._hook)
        self.cpu = cpu

    @staticmethod
    def assert_preimage(image):
        assert bytes(image[spit_up.CLEANUP_OFFSET:
                           spit_up.CLEANUP_OFFSET + spit_up.CLEANUP_SIZE]) \
            == spit_up.CLEANUP_BEFORE

    def _return(self):
        _r0, _r1, pc, lr, _sp = self.reg
        self.cpu.reg_write(pc, self.cpu.reg_read(lr))

    def _hook(self, cpu, address, _size, _user):
        r0, r1, _pc, _lr, _sp = self.reg
        if address == spit_up.GET_SCRIPT_VAR:
            index = cpu.reg_read(r1)
            cpu.reg_write(r0, {0: 70, 1: 120, 3: 5}.get(index, 0))
            self._return()
        elif address == spit_up.SCALE_INIT:
            context = cpu.reg_read(r0)
            start = 179
            cpu.mem_write(context, struct.pack(
                '<hhiiiii', start, start, 5, 104857, 0,
                start << 12, start << 12))
            self._return()
        elif address == spit_up.GROUND_OFFSET:
            cpu.reg_write(r0, 0)
            self._return()

    def run(self, initial_x):
        r0, r1, _pc, lr, sp = self.reg
        context = bytearray(0x5C)
        struct.pack_into('<h', context, 0x02, 80)
        struct.pack_into('<I', context, 0x04, self.DUMMY)
        context[0x0A] = 15
        struct.pack_into('<I', context, 0x0C, self.DUMMY)
        struct.pack_into('<I', context, 0x10, self.SPRITE)
        struct.pack_into('<hhii', context, 0x14, 0x100, 0x100, 10, -31539)
        struct.pack_into('<ii', context, 0x24, 0x100 << 12, 0x100 << 12)
        struct.pack_into('<hhiiiiiiii', context, 0x38,
                         0, 0, 0, 0, 10, 0, 2, 0, -2, 0)
        self.cpu.mem_write(self.CTX, bytes(context))

        sprite = bytearray(0xAC)
        struct.pack_into('<hh', sprite, 0x24, initial_x, 80)
        struct.pack_into('<hh', sprite, 0x34, 0x100, 0x100)
        self.cpu.mem_write(self.SPRITE, bytes(sprite))

        trace = []
        for tick in range(100):
            before = self.cpu.mem_read(self.CTX, 1)[0]
            self.cpu.reg_write(r0, self.DUMMY)
            self.cpu.reg_write(r1, self.CTX)
            self.cpu.reg_write(sp, self.STACK)
            self.cpu.reg_write(lr, self.SENTINEL | 1)
            self.cpu.emu_start(spit_up.TASK | 1, self.SENTINEL)
            after = self.cpu.mem_read(self.CTX, 1)[0]
            x, y = struct.unpack('<hh', self.cpu.mem_read(self.SPRITE + 0x24, 4))
            sx, sy = struct.unpack('<hh', self.cpu.mem_read(self.SPRITE + 0x34, 4))
            trace.append((tick, before, after, x, y, sx, sy))
            if after == 4:
                break
        return tuple(trace)


class ActualSpitUpCandidates(unittest.TestCase):
    def test_exact_candidates_apply_canonical_overlay_and_verify_receipt(self):
        for language, (input_sha, output_sha) in V4.items():
            with self.subTest(language=language):
                path, before = candidate(language)
                after, receipt = spit_up.apply(before, language)
                report = spit_up.verify(before, after, receipt)

                self.assertEqual(hashlib.sha256(before).hexdigest(), input_sha)
                self.assertEqual(hashlib.sha256(after).hexdigest(), output_sha)
                self.assertEqual(receipt['output_sha256'], output_sha)
                self.assertEqual(receipt['rom_slot'], [0x1B0400, 0x1C36E8])
                self.assertEqual(report['logical_changed_bytes'], 24)
                self.assertEqual(report['compressed_changed_bytes'], 23365)
                self.assertTrue(report['loader_agrees'])
                self.assertTrue(report['postimage_in_place_decode'])
                self.assertTrue(report['arm9_accessors_pinned'])
                self.assertEqual(spit_up.changed_regions(before),
                                 ((0x1B0400, 0x1C36E8),))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), input_sha)

                with self.assertRaisesRegex(ValueError, 'already patched'):
                    spit_up.apply(after, language)
                with self.assertRaisesRegex(ValueError, 'receipt correction'):
                    spit_up.verify(before, after,
                                   dict(receipt, cleanup_delta=1))

                mutant = bytearray(after)
                mutant[0x300] ^= 1
                mutant = bytes(mutant)
                bad_receipt = dict(
                    receipt, output_sha256=hashlib.sha256(mutant).hexdigest())
                with self.assertRaisesRegex(ValueError, 'outside overlay 7'):
                    spit_up.verify(before, mutant, bad_receipt)

    def test_real_task_reproduces_drift_fix_and_live_mutants_in_both_languages(self):
        variants = {
            'retail': spit_up.CLEANUP_BEFORE,
            'fixed': spit_up.CLEANUP_AFTER,
            'subtract-one': spit_up.cleanup_postimage(1),
            'subtract-three': spit_up.cleanup_postimage(3),
        }
        expected_delta = {'retail': 2, 'fixed': 0,
                          'subtract-one': 1, 'subtract-three': -1}
        transitions = ((10, 0, 1), (26, 1, 2),
                       (32, 2, 3), (33, 3, 4))

        for language in V4:
            _path, raw = candidate(language)
            for name, cleanup in variants.items():
                for initial_x in (0, 1, 100, 253):
                    with self.subTest(language=language, variant=name,
                                      initial_x=initial_x):
                        trace = NativeSpitUp(raw, cleanup).run(initial_x)
                        self.assertEqual(len(trace), 34)
                        self.assertEqual(
                            tuple((tick, before, after)
                                  for tick, before, after, *_ in trace
                                  if before != after), transitions)
                        self.assertEqual(trace[-1][3:],
                                         (initial_x + expected_delta[name],
                                          80, 0x100, 0x100))
                        self.assertEqual(
                            tuple(row[3] - initial_x for row in trace[:10]),
                            (2, 2, 0, 0, 2, 2, 0, 0, 2, 2))


if __name__ == '__main__':
    unittest.main()
