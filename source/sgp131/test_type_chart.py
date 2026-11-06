import hashlib
import struct
import tempfile
import unittest

from .test_legacy_scripts import inputs
from . import mechanics_stages as M, type_chart as T
from sgp12.rom import Arm9, Rom

try:
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
    from unicorn.arm_const import (
        UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
    )
    UNICORN_ERROR = None
except ImportError as error:
    UNICORN_ERROR = str(error)


# Independent modern 18-type oracle.  Missing pairs are neutral (10).
EFFECTS = {
    0: {5: 5, 7: 0, 8: 5},
    1: {0: 20, 2: 5, 3: 5, 5: 20, 6: 5, 7: 0, 8: 20, 9: 5, 14: 5, 15: 20, 17: 20},
    2: {1: 20, 5: 5, 6: 20, 8: 5, 12: 20, 13: 5},
    3: {3: 5, 4: 5, 5: 5, 7: 5, 8: 0, 9: 20, 12: 20},
    4: {2: 0, 3: 20, 5: 20, 6: 5, 8: 20, 10: 20, 12: 5, 13: 20},
    5: {1: 5, 2: 20, 4: 5, 6: 20, 8: 5, 10: 20, 15: 20},
    6: {1: 5, 2: 5, 3: 5, 7: 5, 8: 5, 9: 5, 10: 5, 12: 20, 14: 20, 17: 20},
    7: {0: 0, 7: 20, 14: 20, 17: 5},
    8: {5: 20, 8: 5, 9: 20, 10: 5, 11: 5, 13: 5, 15: 20},
    9: {1: 20, 3: 5, 8: 5, 10: 5, 16: 20, 17: 20},
    10: {5: 5, 6: 20, 8: 20, 10: 5, 11: 5, 12: 20, 15: 20, 16: 5},
    11: {4: 20, 5: 20, 10: 20, 11: 5, 12: 5, 16: 5},
    12: {2: 5, 3: 5, 4: 20, 5: 20, 6: 5, 8: 5, 10: 5, 11: 20, 12: 5, 16: 5},
    13: {2: 20, 4: 0, 11: 20, 12: 5, 13: 5, 16: 5},
    14: {1: 20, 3: 20, 8: 5, 14: 5, 17: 0},
    15: {2: 20, 4: 20, 8: 5, 10: 5, 11: 5, 12: 20, 15: 5, 16: 20},
    16: {8: 5, 9: 0, 16: 20},
    17: {1: 5, 7: 20, 9: 5, 14: 20, 17: 5},
}


# Native SG-DM01 reproducer.  The function and its grounding helper execute
# from overlay 12; only services outside that pair are modelled at their real
# entry addresses.  The modern chart itself executes from overlay 18.
OVERLAY12_BASE = 0x022378C0
DAMAGE_FUNCTION = 0x02251D28
GROUNDING_HELPER = 0x02251C74
APPLY_EFFECT = 0x022583B4
MODERN_CHART = 0x021FBE60
RETAIL_DEFENDER_LITERAL = 0x02251D20
RETAIL_EFFECT_LITERAL = 0x02251D24
CTX, STACK, STOP = 0x02380000, 0x023B8000, 0x023F0000
FLAG = CTX + 0x3800
SENTINEL = 0xA5A5A5A5
CALLER_CANARY = b'\xA5' * 0xF0
IRON_BALL_EFFECT = 106
GRAVITY = 7 << 12
NO_EFFECT = 1 << 3


class DamageScenario:
    def __init__(self, move_type, target_type, *, item=0, gravity=False):
        self.move_type = move_type
        self.target_type = target_type
        self.item = item
        self.gravity = gravity


class NativeDamage:
    """Execute ov12_02251D28 and ov12_02251C74 from authenticated V4 bytes."""

    STUBS = {
        0x02255830: 'held_item',
        0x02255844: 'item_modifier',
        0x022527CC: 'ability',
        0x0224EDE0: 'battler_var',
        0x02252834: 'ability_if_not_ignored',
        0x02253178: 'damage_divide',
    }

    def __init__(self, rom_data, *, coherent_grounding_columns=False):
        if UNICORN_ERROR:
            raise unittest.SkipTest('unicorn is required for SG-DM01: ' + UNICORN_ERROR)
        rom = Rom(rom_data)
        overlay12 = bytearray(rom.immagine_overlay(12)[2])
        overlay18 = rom.immagine_overlay(18)[2]
        if coherent_grounding_columns:
            struct.pack_into('<I', overlay12,
                             RETAIL_DEFENDER_LITERAL - OVERLAY12_BASE,
                             MODERN_CHART + 1)
            struct.pack_into('<I', overlay12,
                             RETAIL_EFFECT_LITERAL - OVERLAY12_BASE,
                             MODERN_CHART + 2)

        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x02000000, 0x400000)
        uc.mem_map(0x01FF8000, 0x4000)
        uc.mem_map(0x027E0000, 0x20000)
        arm9 = Arm9.from_bytes(rom_data)
        for start, offset, size in arm9.segmenti:
            uc.mem_write(start, bytes(arm9.raw[offset:offset + size]))
        uc.mem_write(T.OVERLAY_BASE, overlay18)
        uc.mem_write(OVERLAY12_BASE, bytes(overlay12))
        for address in self.STUBS:
            uc.hook_add(UC_HOOK_CODE, self._stub, None, address, address)
        uc.hook_add(UC_HOOK_CODE, self._observe_helper, None,
                    GROUNDING_HELPER, GROUNDING_HELPER)
        uc.hook_add(UC_HOOK_CODE, self._observe_effect, None,
                    APPLY_EFFECT, APPLY_EFFECT)
        self.scenario = None
        self.error = None
        self.indices = []
        self.effects = []

    def reg(self, register):
        return self.uc.reg_read(register)

    def word(self, address):
        return struct.unpack('<I', bytes(self.uc.mem_read(address, 4)))[0]

    def _observe_helper(self, uc, address, size, user):
        self.indices.append(self.reg(UC_ARM_REG_R3))

    def _observe_effect(self, uc, address, size, user):
        self.effects.append(self.reg(UC_ARM_REG_R2))

    def _stub(self, uc, address, size, user):
        try:
            result = self._dispatch(self.STUBS[address])
        except Exception as error:
            self.error = error
            uc.emu_stop()
            return
        uc.reg_write(UC_ARM_REG_R0, result & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_PC, self.reg(UC_ARM_REG_LR))

    def _dispatch(self, name):
        r0, r1, r2, r3 = (self.reg(register) for register in (
            UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        if name == 'held_item':
            if r0 != CTX:
                raise AssertionError('held-item context differs')
            return self.scenario.item if r1 == 1 else 0
        if name in ('item_modifier', 'ability', 'ability_if_not_ignored'):
            return 0
        if name == 'battler_var':
            if r0 != CTX or r2 not in (0x1B, 0x1C) or r3 != 0:
                raise AssertionError('unexpected GetBattlerVar ABI')
            return self.scenario.target_type if r1 == 1 else 0
        if name == 'damage_divide':
            if not r1:
                raise AssertionError('division by zero')
            return r0 // r1
        raise AssertionError(name)

    def run(self, scenario):
        self.scenario, self.error, self.indices, self.effects = scenario, None, [], []
        uc = self.uc
        uc.mem_write(CTX, bytes(0x4000))
        uc.mem_write(STACK - 0x1000, bytes(0x1100))
        if scenario.gravity:
            uc.mem_write(CTX + 0x180, struct.pack('<I', GRAVITY))
        uc.mem_write(FLAG, bytes(4))
        # AAPCS: the first four arguments are in r0-r3; the remaining four
        # begin at the caller's SP (attacker, target, damage, status pointer).
        uc.mem_write(STACK, struct.pack('<4I', 0, 1, 100, FLAG))
        uc.mem_write(STACK + 0x10, CALLER_CANARY)
        for register, value in zip(
                (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3),
                (0x02390000, CTX, 1, scenario.move_type)):
            uc.reg_write(register, value)
        for register in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                         UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                         UC_ARM_REG_R10, UC_ARM_REG_R11):
            uc.reg_write(register, SENTINEL)
        uc.reg_write(UC_ARM_REG_SP, STACK)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        uc.emu_start(DAMAGE_FUNCTION | 1, STOP, count=300_000)
        if self.error:
            raise self.error
        if self.reg(UC_ARM_REG_PC) & ~1 != STOP:
            raise AssertionError('damage consumer did not return')
        if self.reg(UC_ARM_REG_SP) != STACK:
            raise AssertionError('damage consumer changed caller SP')
        if bytes(uc.mem_read(STACK + 0x10, len(CALLER_CANARY))) != CALLER_CANARY:
            raise AssertionError('damage consumer changed the caller frame canary')
        if any(self.reg(register) != SENTINEL for register in (
                UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)):
            raise AssertionError('damage consumer changed a callee-saved register')
        return self.reg(UC_ARM_REG_R0), self.word(FLAG), tuple(self.indices), tuple(self.effects)


def damage_oracle(scenario):
    """Independent scalar oracle for the single-type, 100-damage scenarios."""
    effect = EFFECTS.get(scenario.move_type, {}).get(scenario.target_type, 10)
    grounded_flying = (scenario.move_type == 4 and scenario.target_type == 2
                       and (scenario.item == IRON_BALL_EFFECT or scenario.gravity))
    if grounded_flying:
        effect = 10
    return 100 * effect // 10, NO_EFFECT if effect == 0 else 0


class ModernDamageChart(unittest.TestCase):
    def expected(self):
        return [(attack, defend, EFFECTS.get(attack, {}).get(defend, 10))
                for attack in range(18) for defend in range(18)
                if (attack, defend) not in ((0, 7), (1, 7))]

    def test_red_table_has_exactly_the_two_reported_ghost_cells(self):
        for language in ('EN', 'IT'):
            image = T.overlay(inputs(language)[0])
            rows, trailer = T.rows(image)
            expected = self.expected()
            divergences = [(i, rows[i], expected[i]) for i in range(len(expected))
                           if rows[i] != expected[i]]
            with self.subTest(language=language):
                self.assertEqual(divergences, [
                    (140, (7, 16, 5), (7, 16, 10)),
                    (141, (7, 17, 10), (7, 17, 5)),
                ])
                self.assertEqual(trailer, [(0xFE, 0xFE, 0), (0, 7, 0), (1, 7, 0)])

    def test_green_patch_changes_only_two_multipliers_and_matches_oracle(self):
        for language in ('EN', 'IT'):
            before = T.overlay(inputs(language)[0])
            after, receipt = T.patch_overlay(before)
            rows, trailer = T.rows(after)
            changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
            with self.subTest(language=language):
                self.assertEqual(rows, self.expected())
                self.assertEqual(trailer, [(0xFE, 0xFE, 0), (0, 7, 0), (1, 7, 0)])
                self.assertEqual(changed, [T.GHOST_DRAGON + 2, T.GHOST_DARK + 2])
                self.assertEqual(receipt['changed_offsets'], changed)

    def test_real_rom_apply_verify_is_confined_and_rejects_mutants(self):
        for language in ('EN', 'IT'):
            before = inputs(language)[0]
            after, receipt = T.apply(before, language)
            with self.subTest(language=language):
                self.assertEqual(T.verify(before, after, receipt)['logical_changed_bytes'], 2)
                self.assertNotEqual(hashlib.sha256(before).digest(), hashlib.sha256(after).digest())
                mutant = bytearray(after)
                mutant[-1] ^= 1
                with self.assertRaises(ValueError):
                    T.verify(before, bytes(mutant), receipt)

    def test_damage_repair_is_composed_with_the_existing_ai_stage(self):
        for language in ('EN', 'IT'):
            before = inputs(language)[0]
            parent, part = M.reserve_slot(M.FAIRY_AI_SLOT)
            row = {'name': M.FAIRY_AI_SLOT, 'parent': parent, 'start': part['start'],
                   'bytes': M.FAIRY_AI_PAYLOAD_BYTES, 'capacity': part['bytes']}
            with tempfile.TemporaryDirectory() as work:
                after, receipt = M._ai_apply(before, language, row=row, work_dir=work)
            matrix, _ = T.rows(T.overlay(after))
            by_pair = {(attack, defend): multiplier
                       for attack, defend, multiplier in matrix}
            regions = M._ai_regions(before)
            with self.subTest(language=language):
                self.assertEqual(by_pair[(7, 16)], 10)
                self.assertEqual(by_pair[(7, 17)], 5)
                self.assertEqual([r.label for r in regions],
                                 ['reserve:fairy-ai.code',
                                  'overlay 12 slot (file 12)',
                                  'overlay 18 slot (file 18)',
                                  'overlay 12 FAT entry',
                                  'overlay 12 y9 size word',
                                  'ui.module.seed derived y9 crc32'])
                self.assertTrue(M._ai_verify(before, after, receipt)['ok'])

    def test_combined_verifier_accepts_the_json_receipt_used_by_run_stage(self):
        before = inputs('EN')[0]
        parent, part = M.reserve_slot(M.FAIRY_AI_SLOT)
        row = {'name': M.FAIRY_AI_SLOT, 'parent': parent, 'start': part['start'],
               'bytes': M.FAIRY_AI_PAYLOAD_BYTES, 'capacity': part['bytes']}
        with tempfile.TemporaryDirectory() as work:
            after, receipt = M._ai_apply(before, 'EN', row=row, work_dir=work)
        # run_stage canonicalises tuples in nested writer receipts before replay.
        self.assertTrue(M._ai_verify(before, after, M._jsonable(receipt))['ok'])

    def test_native_damage_grounding_reproduces_the_mixed_index_bug(self):
        scenarios = {
            'retail_ground_flying': DamageScenario(4, 2),
            'iron_ball_ground_flying': DamageScenario(4, 2, item=IRON_BALL_EFFECT),
            'gravity_ground_flying': DamageScenario(4, 2, gravity=True),
            'iron_ball_ground_poison': DamageScenario(4, 3, item=IRON_BALL_EFFECT),
            'fairy_dragon': DamageScenario(9, 16),
            'fairy_dragon_gravity': DamageScenario(9, 16, gravity=True),
        }
        for language in ('EN', 'IT'):
            data = inputs(language)[0]
            rom = Rom(data)
            overlay12 = rom.immagine_overlay(12)[2]
            overlay18 = rom.immagine_overlay(18)[2]
            defender = struct.unpack_from(
                '<I', overlay12, RETAIL_DEFENDER_LITERAL - OVERLAY12_BASE)[0]
            effect = struct.unpack_from(
                '<I', overlay12, RETAIL_EFFECT_LITERAL - OVERLAY12_BASE)[0]
            modern_row = tuple(overlay18[
                MODERN_CHART - T.OVERLAY_BASE + 72 * 3:
                MODERN_CHART - T.OVERLAY_BASE + 72 * 3 + 3])
            retail_row = tuple(overlay12[
                defender - 1 - OVERLAY12_BASE + 72 * 3:
                defender - 1 - OVERLAY12_BASE + 72 * 3 + 3])
            self.assertEqual((defender, effect), (0x0226CC7D, 0x0226CC7E))
            self.assertEqual(modern_row, (4, 2, 0))
            self.assertEqual(retail_row, (14, 17, 0))

            native = NativeDamage(data)
            coherent = NativeDamage(data, coherent_grounding_columns=True)
            observed, corrected = {}, {}
            for name, scenario in scenarios.items():
                observed[name] = native.run(scenario)
                corrected[name] = coherent.run(scenario)
                with self.subTest(language=language, scenario=name):
                    self.assertEqual(corrected[name][:2], damage_oracle(scenario))

            # The real vulnerable consumer applies modern row 72's immunity in
            # both grounded cases.  Pointing only the helper's two read-only
            # columns at the same modern table suppresses exactly that call.
            self.assertEqual(observed['retail_ground_flying'], (0, 8, (72,), (0,)))
            self.assertEqual(observed['iron_ball_ground_flying'], (0, 8, (72,), (0,)))
            self.assertEqual(observed['gravity_ground_flying'], (0, 8, (72,), (0,)))
            self.assertEqual(corrected['iron_ball_ground_flying'], (100, 0, (72,), ()))
            self.assertEqual(corrected['gravity_ground_flying'], (100, 0, (72,), ()))

            # Retail and Fairy controls are invariant under the one-variable
            # in-memory experiment and agree with the independent oracle.
            for name in ('retail_ground_flying', 'iron_ball_ground_poison',
                         'fairy_dragon', 'fairy_dragon_gravity'):
                with self.subTest(language=language, control=name):
                    self.assertEqual(observed[name], corrected[name])
                    self.assertEqual(observed[name][:2], damage_oracle(scenarios[name]))


if __name__ == '__main__':
    unittest.main()
