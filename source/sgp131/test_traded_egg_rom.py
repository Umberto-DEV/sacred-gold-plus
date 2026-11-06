"""Real-code and real-ROM checks for HG-T12."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R4,
                               UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                               UC_ARM_REG_SP)

from sgp12.rom import Arm9, Rom
from . import mechanics_stages as stages, traded_egg as t


ROOT = Path(__file__).resolve().parents[2]
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           '1dcb12d23097c4180611942a11087ddd6a54b3688550f0776dc7a1b9dbdea208'),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           '3462bd0a8b447fc93353a1fde46e37e633884ba3864abec8130dd886758ebebe'),
}
CURRENT = {
    'EN': ('90435d3c3a140774fea773ba16039a7eed8aa262bb5b2377217714b6f8d5fc18',
           'a7da215939d51c22756d1818779380f40e9cc9601376719ede9fe72702b5c999'),
    'IT': ('420ec8b8d5dbf30d209849bf18a439046a666a710656e01966a1f217d70f059a',
           'c5cda9cb590fe98b76296edd6abac28bc8076c281eceb7bbef3fdef868d69ce8'),
}
CASES = (
    (0, 0x100, 0, True, False),
    (0, 0x100, 0x100, False, True),
    (0, 0x100, 0x200, False, False),
    (0, 0, 0, True, True),
)


class NativePaletteBench:
    BASE = 0x02000000
    SIZE = 0x00400000
    STATE = 0x023E0000
    ARGS = 0x023E0100
    PROFILE = 0x023E0200
    MON = 0x023E0300
    STACK = 0x023F0000
    STOP = 0x02001000

    def __init__(self, rom):
        with tempfile.TemporaryDirectory(prefix='traded-egg-bench-') as scratch:
            self.payload, _ = t.compile_native(Path(scratch))
        self.classifier = Arm9.from_bytes(rom).leggi(t.IS_SHINY, 44)

    def run(self, breeder_ot, hatcher_ot, pid):
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(self.BASE, self.SIZE)
        uc.mem_write(t.HELPER_ADDRESS, self.payload)
        uc.mem_write(t.IS_SHINY, self.classifier)
        uc.mem_write(self.STATE, self.ARGS.to_bytes(4, 'little'))
        uc.mem_write(self.ARGS + 0x14, self.PROFILE.to_bytes(4, 'little'))
        uc.mem_write(self.PROFILE + 0x10, hatcher_ot.to_bytes(4, 'little'))
        template = self.STACK + 0x3C
        uc.mem_write(template + 4, (0x104).to_bytes(2, 'little'))
        calls = []

        def stub(machine, address, _size, _user):
            calls.append(address)
            if address == t.GET_SPRITE_IDS:
                self.assert_call(machine.reg_read(UC_ARM_REG_R0) == template,
                                 'sprite template argument')
                palette = 0x104 | int(t.plus_is_shiny(breeder_ot, pid))
                machine.mem_write(template + 4, palette.to_bytes(2, 'little'))
            elif address == t.GET_MON_DATA:
                self.assert_call(machine.reg_read(UC_ARM_REG_R0) == self.MON,
                                 'GetMonData mon argument')
                self.assert_call(machine.reg_read(UC_ARM_REG_R1) == 0
                                 and machine.reg_read(UC_ARM_REG_R2) == 0,
                                 'GetMonData PID ABI')
                machine.reg_write(UC_ARM_REG_R0, pid)
            elif address == self.STOP:
                machine.emu_stop()
                return
            machine.reg_write(UC_ARM_REG_PC,
                              machine.reg_read(UC_ARM_REG_LR) | 1)

        self.assert_call = lambda condition, label: (
            None if condition else (_ for _ in ()).throw(AssertionError(label)))
        for address in (t.GET_SPRITE_IDS, t.GET_MON_DATA, self.STOP):
            uc.hook_add(UC_HOOK_CODE, stub, begin=address, end=address)
        sentinels = (self.MON, self.STATE, 0x66666666, 0x77777777)
        for register, value in zip((UC_ARM_REG_R4, UC_ARM_REG_R5,
                                    UC_ARM_REG_R6, UC_ARM_REG_R7), sentinels):
            uc.reg_write(register, value)
        uc.reg_write(UC_ARM_REG_R0, template)
        uc.reg_write(UC_ARM_REG_R1, self.MON)
        uc.reg_write(UC_ARM_REG_R2, 2)
        uc.reg_write(UC_ARM_REG_SP, self.STACK)
        uc.reg_write(UC_ARM_REG_LR, self.STOP | 1)
        uc.emu_start(t.HELPER_ADDRESS | 1, self.STOP + 2, count=200)
        palette = int.from_bytes(uc.mem_read(template + 4, 2), 'little')
        registers = tuple(uc.reg_read(register) for register in
                          (UC_ARM_REG_R4, UC_ARM_REG_R5,
                           UC_ARM_REG_R6, UC_ARM_REG_R7))
        return palette, calls, registers, uc.reg_read(UC_ARM_REG_SP)


class TradedEggNativeRomTests(unittest.TestCase):
    def fixture(self, language='EN'):
        path = ROOT / f'local/experiments/balance493-2026-10-28/candidate-v4-{language}.nds'
        if not path.is_file():
            self.skipTest('immutable V4 candidate unavailable: ' + str(path))
        data = path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), V4[language][0])
        return data

    def current_fixture(self, language):
        path = ROOT / ('local/roms/1.3.1-bugfix-manual-test/'
                       f'Sacred-Gold-Plus-1.3.1-{language}.nds')
        if not path.is_file():
            self.skipTest('current candidate unavailable: ' + str(path))
        data = path.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), CURRENT[language][0])
        return data

    def test_real_helper_and_real_plus_classifier_cover_four_cases_and_abi(self):
        bench = NativePaletteBench(self.fixture())
        for breeder, hatcher, pid, before, expected in CASES:
            with self.subTest(breeder=breeder, hatcher=hatcher, pid=pid):
                palette, calls, registers, stack = bench.run(
                    breeder, hatcher, pid)
                self.assertEqual(palette, 0x104 | int(expected))
                self.assertEqual(calls, [t.GET_SPRITE_IDS, t.GET_MON_DATA,
                                         NativePaletteBench.STOP])
                self.assertEqual(registers,
                                 (NativePaletteBench.MON,
                                  NativePaletteBench.STATE,
                                  0x66666666, 0x77777777))
                self.assertEqual(stack, NativePaletteBench.STACK)
                self.assertEqual(bool((0x104 | int(before)) & 1), before)

    def test_real_v4_en_it_apply_verify_replay_and_exact_output(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                before = self.fixture(language)
                after, receipt = t.apply(before, language)
                self.assertEqual(hashlib.sha256(after).hexdigest(), V4[language][1])
                self.assertTrue(t.verify(before, after, receipt)['ok'])
                old = Rom(before).immagine_overlay(t.OVERLAY_ID)
                new = Rom(after).immagine_overlay(t.OVERLAY_ID)
                self.assertEqual((len(old[1]), len(new[1])), (5964, 5988))
                self.assertEqual((len(old[2]), len(new[2])), (8128, 8172))
                with self.assertRaisesRegex(ValueError, 'identity|size|preimage'):
                    t.apply(after, language)

    def test_registered_stage_matches_direct_writer_and_declares_all_regions(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                before = self.current_fixture(language)
                direct, _ = t.apply(before, language)
                after, receipt = stages.run_stage('traded-egg', before, language)
                self.assertEqual(after, direct)
                self.assertEqual(receipt['stage'], 'traded-egg')
                self.assertEqual(receipt['regions'], [
                    {'start': start, 'end': end, 'label': label}
                    for start, end, label in t.spans(before)
                ])

    def test_current_en_it_reconcile_the_real_ui_y9_seed(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                before = self.current_fixture(language)
                after, receipt = t.apply(before, language)
                self.assertEqual(hashlib.sha256(after).hexdigest(),
                                 CURRENT[language][1])
                self.assertIsNotNone(receipt['ui_seed'])
                self.assertTrue(t.verify(before, after, receipt)
                                ['ui_y9_seed_reconciled'])

    def test_global_peel_reconstructs_the_exact_cold_ui_from_v4(self):
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                base = self.fixture(language)
                cold_ui = self.current_fixture(language)
                final, _ = stages.run_stage('traded-egg', cold_ui, language)
                stage = stages.require_stage('traded-egg')
                declared = list(stage.regions(base))
                peeled = stage.peel(final, base, declared)
                self.assertTrue(peeled == cold_ui,
                                'peel did not reconstruct the cold UI')

    def test_receipt_helper_y9_and_unrelated_mutants_are_rejected(self):
        before = self.fixture()
        after, receipt = t.apply(before, 'EN')
        forged = {**receipt, 'output_sha256': '0' * 64}
        with self.assertRaisesRegex(ValueError, 'receipt'):
            t.verify(before, after, forged)
        for offset in (0x201, Rom(after).voce_overlay(t.OVERLAY_ID)['offset_voce'] + 8,
                       Rom(after).voce_fat(t.OVERLAY_ID)['inizio'] + 2):
            damaged = bytearray(after)
            damaged[offset] ^= 1
            forged = {**receipt, 'output_sha256': hashlib.sha256(damaged).hexdigest()}
            with self.assertRaises(ValueError):
                t.verify(before, bytes(damaged), forged)


if __name__ == '__main__':
    unittest.main()
