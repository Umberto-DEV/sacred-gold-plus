"""Dedicated consultant graphics preserve native sprites and lookup behavior."""
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import unittest

from sgp13 import consultant
from sgp13.training import compile_native, entry_hook, BASE, CONFIG


class ConsultantNativeTests(unittest.TestCase):
    def test_unknown_texture_is_rejected_before_editing(self):
        with self.assertRaisesRegex(ValueError, 'texture preimage'):
            consultant.orange_delivery(bytes(6760))


@unittest.skipUnless(os.environ.get('SGP13_BASE_DIR'),
                     'needs private 1.2.5 inputs and executable Unicorn JIT')
class NativeConsultantRegression(unittest.TestCase):
    def test_only_the_cloned_uniform_changes_and_conflicting_ids_fail_closed(self):
        import ndspy.narc
        import ndspy.rom
        from sgp12.rom import Arm9
        for language in ('EN', 'IT'):
            path = Path(os.environ['SGP13_BASE_DIR']) / f'sgp-1.2.5-{language}.nds'
            arm = Arm9(path)
            rom = ndspy.rom.NintendoDSRom(bytes(arm.raw))
            models = ndspy.narc.NARC(rom.getFileByName(consultant.MODEL_ARCHIVE))
            events = ndspy.narc.NARC(rom.getFileByName('a/0/3/2'))
            original = list(models.files)
            report = consultant.prepare(arm, models, events)
            self.assertEqual(models.files[:-1], original)
            self.assertEqual(report['sprite'], 194)
            self.assertEqual(report['member'], len(original))
            before, after = original[consultant.SOURCE_MEMBER], models.files[-1]
            self.assertEqual(len(before), len(after))
            # Packed texture data, names, directions and animation frames must
            # remain exact; only two colors in the appended palette may differ.
            allowed = {len(before)-32+i*2+j for i in (2, 4) for j in (0, 1)}
            self.assertEqual({i for i, (a, b) in enumerate(zip(before, after)) if a != b}, allowed)
            self.assertEqual(hashlib.sha256(before).hexdigest(), consultant.SOURCE_SHA)
            models.files[:] = original
            conflicting = bytearray(struct.pack('<2I', 0, 1) + bytes(32))
            struct.pack_into('<H', conflicting, 10, 194)
            events.files.append(bytes(conflicting))
            with self.assertRaisesRegex(ValueError, 'already used in an event'):
                consultant.prepare(arm, models, events)
            self.assertEqual(models.files, original)

    def test_every_native_sprite_and_category_keeps_its_lookup_and_abi(self):
        from sgp12.rom import Arm9, Rom
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R4,
            UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
            UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_SP,
            UC_ARM_REG_LR, UC_ARM_REG_PC)
        with tempfile.TemporaryDirectory() as out:
            blob, symbols = compile_native(out)
        self.assertLessEqual(len(blob), CONFIG - BASE)
        preserved = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                     UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
        stack, stop = 0x023BF000, 0x023F0000
        for language in ('EN', 'IT'):
            path = Path(os.environ['SGP13_BASE_DIR']) / f'sgp-1.2.5-{language}.nds'
            arm = Arm9(path)
            meta, _, overlay = Rom(arm.raw).immagine_overlay(1)
            offset = consultant.TABLE_ADDRESS-meta['ram']
            table = overlay[offset:offset+consultant.TABLE_SIZE]
            self.assertEqual(hashlib.sha256(table).hexdigest(), consultant.TABLE_SHA)
            records = list(struct.iter_unpack('<3H', table))[:-1]
            machines = []
            for changed in (False, True):
                cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
                cpu.mem_map(0x02000000, 0x400000)
                for start, off, size in arm.segmenti:
                    if 0x02000000 <= start and start+size <= 0x02400000:
                        cpu.mem_write(start, bytes(arm.raw[off:off+size]))
                cpu.mem_write(meta['ram'], overlay)
                if changed:
                    cpu.mem_write(BASE, blob)
                    cpu.mem_write(CONFIG+16, struct.pack('<4H', 194, 863, 0, 0))
                    for site, _, name in consultant.HOOKS:
                        cpu.mem_write(site, entry_hook(site, symbols[name]))
                assertions = []
                def intercept(uc, address, size, calls):
                    if address == 0x0202551C:
                        calls.append(address)
                        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
                cpu.hook_add(UC_HOOK_CODE, intercept, assertions)
                machines.append((cpu, assertions))

            def invoke(machine, site, sprite):
                cpu, assertions = machine
                assertions.clear()
                cpu.reg_write(UC_ARM_REG_R0, sprite)
                cpu.reg_write(UC_ARM_REG_SP, stack)
                cpu.reg_write(UC_ARM_REG_LR, stop|1)
                for register in preserved:
                    cpu.reg_write(register, 0xA5A5A5A5)
                cpu.emu_start(site|1, stop, count=50000)
                self.assertEqual(cpu.reg_read(UC_ARM_REG_PC), stop)
                self.assertEqual(cpu.reg_read(UC_ARM_REG_SP), stack)
                self.assertEqual([cpu.reg_read(r) for r in preserved], [0xA5A5A5A5]*8)
                return cpu.reg_read(UC_ARM_REG_R0), len(assertions)

            for index, (sprite, model, properties) in enumerate(records):
                for site, _, name in consultant.HOOKS:
                    with self.subTest(language=language, sprite=sprite, lookup=name):
                        expected = (consultant.TABLE_ADDRESS+index*6 if name == 'training_sprite'
                                    else 0x02207318+(properties>>10)*8)
                        self.assertEqual(invoke(machines[0], site, sprite), (expected, 0))
                        self.assertEqual(invoke(machines[1], site, sprite), (expected, 0))
            for site, _, name in consultant.HOOKS:
                # Dedicated ID previously had no native entry. It must become
                # valid without changing any other ID or suppressing assertions.
                self.assertEqual(invoke(machines[0], site, 194)[1], 1)
                expected = CONFIG+16 if name == 'training_sprite' else 0x02207318
                self.assertEqual(invoke(machines[1], site, 194), (expected, 0))
                self.assertEqual(invoke(machines[1], site, 65534), (0, 1))


if __name__ == '__main__':
    unittest.main()
