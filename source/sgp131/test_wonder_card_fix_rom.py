"""Red/green contract for the HG-SEC01 decoration-domain repair.

The independent reproducer remains in ``test_wonder_card_seal_rom``.  This
bench describes the required successor: reject malformed tag-6 data before a
leaf is called and make every affected writer fail closed when called directly.
All execution is RAM-only on authenticated EN/IT candidates.
"""
import hashlib
from pathlib import Path
import struct
import unittest

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB, Uc
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP)

from sgp12.rom import Arm9
from .test_wonder_card_seal_rom import V4, V4_ROOT


MG_CHECK = 0x0204C550
MG_GIVE = 0x0204C588
FIELD_GET_DATA = 0x0204BD8C
SEAL_GET = 0x0202CBE8
FASHION_ROOT_GET = 0x0202C028
FASHION_GET = 0x0202B9E0
COUNT_SEAL = 0x0202CC7C
ASSERT = 0x0202551C
LEAVES = {1: (0x0202CD3C, 0x0202CCAC),
          2: (None, 0x0202BB08),
          3: (None, 0x0202BBD8)}

SCRATCH = 0x02700000
FIELD = SCRATCH + 0x1000
DATA = SCRATCH + 0x2000
SAVE = SCRATCH + 0x3000
OBJECT = SCRATCH + 0x10000
STOP = SCRATCH + 0x30000
STACK = SCRATCH + 0x3F000


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), V4[language])
    return data


def implementation(case):
    try:
        from . import wonder_card
    except ImportError as error:
        case.fail('Wonder Card producer is not implemented: ' + str(error))
    return wonder_card


class ThumbCall:
    def __init__(self, rom, entry, *, kind=0, item_id=0, delta=1):
        self.entry = entry
        self.calls = []
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.cpu.mem_map(0x01FF8000, 0x4000)
        self.cpu.mem_map(0x02000000, 0x400000)
        self.cpu.mem_map(0x02700000, 0x40000)
        self.cpu.mem_map(0x027E0000, 0x20000)
        arm = Arm9.from_bytes(rom)
        for address, offset, size in arm.segmenti:
            self.cpu.mem_write(address, bytes(arm.raw[offset:offset + size]))
        self.cpu.mem_write(FIELD, bytes(0x100))
        self.cpu.mem_write(FIELD + 0x0C, struct.pack('<I', SAVE))
        self.cpu.mem_write(DATA, struct.pack('<II', kind, item_id))
        self.cpu.mem_write(OBJECT, bytes([0xA5]) * 0x12000)
        self.cpu.mem_write(OBJECT + 288, bytes(80))
        self.cpu.mem_write(STOP, b'\x00\xBE')
        self.kind, self.item_id, self.delta = kind, item_id, delta
        self.cpu.hook_add(UC_HOOK_CODE, self._hook)

    def _return(self, value=0):
        self.cpu.reg_write(UC_ARM_REG_R0, value)
        self.cpu.reg_write(UC_ARM_REG_PC, self.cpu.reg_read(UC_ARM_REG_LR))

    def _hook(self, cpu, address, _size, _user):
        if address == FIELD_GET_DATA:
            self.calls.append(('get_data',))
            self._return(DATA)
        elif address == SEAL_GET:
            self.calls.append(('seal_get',))
            self._return(OBJECT)
        elif address == FASHION_ROOT_GET:
            self.calls.append(('fashion_root_get',))
            self._return(OBJECT)
        elif address == FASHION_GET:
            self.calls.append(('fashion_get',))
            self._return(OBJECT)
        elif address == COUNT_SEAL:
            self.calls.append(('count_seal', cpu.reg_read(UC_ARM_REG_R1)))
            self._return(0)
        elif address == ASSERT:
            self.calls.append(('assert',))
            self._return(0)
        else:
            for kind, (check, give) in LEAVES.items():
                if address == check or address == give:
                    self.calls.append(('leaf', kind, address,
                                       cpu.reg_read(UC_ARM_REG_R1),
                                       cpu.reg_read(UC_ARM_REG_R2)))
                    return

    def run(self):
        before = bytes(self.cpu.mem_read(OBJECT, 0x12000))
        if self.entry in (MG_CHECK, MG_GIVE):
            args = (FIELD, DATA, 0)
        else:
            args = (OBJECT, self.item_id, self.delta)
        for register, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2), args):
            self.cpu.reg_write(register, value)
        self.cpu.reg_write(UC_ARM_REG_SP, STACK)
        self.cpu.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.cpu.emu_start(self.entry | 1, STOP, count=512)
        if self.cpu.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError('Thumb call did not return')
        after = bytes(self.cpu.mem_read(OBJECT, 0x12000))
        return self.cpu.reg_read(UC_ARM_REG_R0), list(self.calls), before, after


class WonderCardFixTests(unittest.TestCase):
    def test_check_rejects_each_invalid_domain_and_give_cannot_mutate_it(self):
        fix = implementation(self)
        domains = {1: ((1, 80), (0, 81, 0xFFFF)),
                   2: ((0, 99), (100, 0xFFFF)),
                   3: ((0, 17), (18, 0xFFFF))}
        for language in V4:
            repaired, _receipt = fix.apply(candidate(self, language), language)
            for kind, (valid, invalid) in domains.items():
                for item_id in valid:
                    with self.subTest(language=language, kind=kind, item_id=item_id,
                                      action='check-valid'):
                        result, calls, _before, _after = ThumbCall(
                            repaired, MG_CHECK, kind=kind, item_id=item_id).run()
                        self.assertEqual(result, 1)
                        if kind == 1:
                            self.assertTrue(any(call[:2] == ('leaf', 1) for call in calls))
                for item_id in invalid:
                    with self.subTest(language=language, kind=kind, item_id=item_id,
                                      action='check-invalid'):
                        result, calls, before, after = ThumbCall(
                            repaired, MG_CHECK, kind=kind, item_id=item_id).run()
                        self.assertEqual(result, 0)
                        self.assertEqual(after, before)
                    with self.subTest(language=language, kind=kind, item_id=item_id,
                                      action='give-invalid'):
                        _result, calls, before, after = ThumbCall(
                            repaired, MG_GIVE, kind=kind, item_id=item_id).run()
                        self.assertEqual(after, before)

    def test_direct_writers_fail_closed_for_out_of_domain_ids(self):
        fix = implementation(self)
        cases = ((1, 0), (1, 81), (1, 0xFFFF),
                 (2, 100), (2, 0xFFFF), (3, 18), (3, 0xFFFF))
        for language in V4:
            repaired, _receipt = fix.apply(candidate(self, language), language)
            for kind, item_id in cases:
                with self.subTest(language=language, kind=kind, item_id=item_id):
                    entry = LEAVES[kind][1]
                    result, calls, before, after = ThumbCall(
                        repaired, entry, kind=kind, item_id=item_id).run()
                    self.assertEqual(after, before)
                    self.assertFalse(any(call[0] in ('count_seal', 'assert') for call in calls))
                    if kind == 1:
                        self.assertEqual(result, 0)

    def test_repair_is_confined_verified_and_rejects_foreign_inputs(self):
        fix = implementation(self)
        before = candidate(self, 'EN')
        after, receipt = fix.apply(before, 'EN')
        allowed = set()
        for start, end in fix.spans(before):
            allowed.update(range(start, end))
        changed = {index for index, pair in enumerate(zip(before, after))
                   if pair[0] != pair[1]}
        self.assertTrue(changed)
        self.assertTrue(changed <= allowed)
        self.assertEqual(len(after), len(before))
        self.assertTrue(receipt['save_layout_unchanged'])
        self.assertTrue(receipt['rom_geometry_unchanged'])
        self.assertEqual(fix.verify(before, after, receipt), receipt['verification'])
        with self.assertRaises(ValueError):
            fix.apply(after, 'EN')
        with self.assertRaises(ValueError):
            fix.apply(before, 'IT')


if __name__ == '__main__':
    unittest.main()
