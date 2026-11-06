"""Exact-candidate regression for the custom-rules Soul Dew mask.

HGSS stores the Soul Dew flag in bit 15 of ``totalLevel``.  The retail getter
returns the whole field for rule 13, while every consumer compares it with
exactly ``0x8000``.  A custom total-level limit therefore disables the clause.
This bench executes the real ARM9 getter before and after the confined repair;
no Wonder Card, link peer or save is involved.
"""
import hashlib
from pathlib import Path
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                               UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                               UC_ARM_REG_SP)

from sgp12.rom import Arm9


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           153228136),
}

GETTER = 0x020290FC
GETTER_BYTES = 0xA8
GETTER_SHA256 = '97f7a4ea5da6db18d5620b28ce1ab63973fd6da599970d28df6d3d06b97f74ec'
RULESET = 0x02701000
STACK = 0x02710000
STOP = 0x0271F000
CALLEE_SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                UC_ARM_REG_R10, UC_ARM_REG_R11)


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), V4[language])
    return data


def implementation(case):
    try:
        from . import soul_dew
    except ImportError as error:
        case.fail('Soul Dew producer is not implemented: ' + str(error))
    return soul_dew


class GetterBench:
    def __init__(self, rom):
        self.arm = Arm9.from_bytes(rom)
        if hashlib.sha256(self.arm.leggi(GETTER, GETTER_BYTES)).hexdigest() not in {
                GETTER_SHA256,
                # The producer publishes the exact repaired getter identity.
                getattr(self._implementation_or_none(), 'GETTER_POST_SHA256', None)}:
            raise AssertionError('unexpected Soul Dew getter identity')
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.cpu.mem_map(0x01FF8000, 0x4000)
        self.cpu.mem_map(0x02000000, 0x400000)
        self.cpu.mem_map(0x02700000, 0x20000)
        self.cpu.mem_map(0x027E0000, 0x20000)
        for address, offset, size in self.arm.segmenti:
            self.cpu.mem_write(address, bytes(self.arm.raw[offset:offset + size]))

    @staticmethod
    def _implementation_or_none():
        try:
            from . import soul_dew
            return soul_dew
        except ImportError:
            return None

    def run(self, rule, total_level):
        cpu = self.cpu
        raw = bytearray(0x40)
        raw[0x18:0x1A] = int(total_level).to_bytes(2, 'little')
        cpu.mem_write(RULESET - 16, b'\xA5' * 16 + raw + b'\x5A' * 16)
        cpu.mem_write(STACK - 32, b'\xC3' * 64)
        for index, register in enumerate(CALLEE_SAVED):
            cpu.reg_write(register, 0xB0000000 + index)
        cpu.reg_write(UC_ARM_REG_R0, RULESET)
        cpu.reg_write(UC_ARM_REG_R1, rule)
        cpu.reg_write(UC_ARM_REG_SP, STACK)
        cpu.reg_write(UC_ARM_REG_LR, STOP | 1)
        cpu.emu_start(GETTER | 1, STOP, count=256)
        if cpu.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError('Soul Dew getter did not return')
        if cpu.reg_read(UC_ARM_REG_SP) != STACK:
            raise AssertionError('Soul Dew getter changed SP')
        if [cpu.reg_read(r) for r in CALLEE_SAVED] != [0xB0000000 + i for i in range(8)]:
            raise AssertionError('Soul Dew getter changed a callee-saved register')
        if bytes(cpu.mem_read(RULESET - 16, 16)) != b'\xA5' * 16 \
                or bytes(cpu.mem_read(RULESET + 0x40, 16)) != b'\x5A' * 16:
            raise AssertionError('Soul Dew getter changed ruleset canaries')
        return cpu.reg_read(UC_ARM_REG_R0)


class SoulDewCandidateTests(unittest.TestCase):
    def test_v4_returns_the_unmasked_field_but_ordinary_rules_are_healthy(self):
        for language in V4:
            bench = GetterBench(candidate(self, language))
            with self.subTest(language=language):
                self.assertEqual(bench.run(13, 0x8000), 0x8000)
                self.assertEqual(bench.run(13, 0x8032), 0x8032)
                self.assertEqual(bench.run(13, 0x0032), 0x0032)
                self.assertEqual(bench.run(3, 0x8032), 0x0032)
                self.assertEqual(bench.run(14, 0xFFFF), 0)

    def test_repair_masks_only_rule_13_and_preserves_the_full_dispatch(self):
        fix = implementation(self)
        totals = (0x0000, 0x0032, 0x0FFF, 0x8000, 0x8032, 0x8FFF, 0xFFFF)
        for language in V4:
            before = candidate(self, language)
            after, receipt = fix.apply(before, language)
            old, new = GetterBench(before), GetterBench(after)
            with self.subTest(language=language):
                for rule in range(13):
                    for total in totals:
                        self.assertEqual(new.run(rule, total), old.run(rule, total),
                                         (rule, total))
                for total in totals:
                    self.assertEqual(new.run(13, total), total & 0x8000, total)
                self.assertEqual(new.run(14, 0xFFFF), 0)
                self.assertEqual(new.run(255, 0xFFFF), 0)
                self.assertEqual(fix.verify(before, after, receipt),
                                 receipt['verification'])

    def test_repair_is_confined_and_refuses_foreign_inputs(self):
        fix = implementation(self)
        before = candidate(self, 'EN')
        after, receipt = fix.apply(before, 'EN')
        changed = [index for index, (old, new) in enumerate(zip(before, after))
                   if old != new]
        allowed = set()
        for start, end in fix.spans(before):
            allowed.update(range(start, end))
        self.assertTrue(changed)
        self.assertTrue(set(changed) <= allowed)
        self.assertEqual(len(before), len(after))
        self.assertTrue(receipt['save_layout_unchanged'])
        self.assertTrue(receipt['rom_geometry_unchanged'])
        with self.assertRaises(ValueError):
            fix.apply(after, 'EN')
        with self.assertRaises(ValueError):
            fix.apply(before, 'IT')


if __name__ == '__main__':
    unittest.main()
