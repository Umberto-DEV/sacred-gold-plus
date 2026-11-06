"""Class A contracts for shared overlay-12 type and battle-state edits."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP)

from sgp12.rom import bl_decode
from . import type_consumers as T
from . import uturn_flinch as U


FIRE_FANG_EFFECT_SITE = 0x0225848C
FIRE_FANG_PREIMAGE = bytes.fromhex('1132')
FIRE_FANG_REPLACEMENT = bytes.fromhex('1032')
FIRE_FANG_BRANCH = 0x02258490
FIRE_FANG_BRANCH_PREIMAGE = bytes.fromhex('05d1')
FIRE_FANG_CONTEXT_ADDRESS = 0x0225848C
FIRE_FANG_CONTEXT = bytes.fromhex(
    '1132934205d105494158022000020840704701207047c046')
RAGE_SITE = 0x022493FC
RAGE_PREIMAGE = bytes.fromhex('0140')
RAGE_REPLACEMENT = bytes.fromhex('8143')
RAGE_CONTEXT_ADDRESS = 0x022493EC
RAGE_CONTEXT = bytes.fromhex(
    '08f080ff632806d01848295802208005014016482950761cc035be42e8dba06a')
TRY_ITEM_FLINCH = 0x0224E078
TRY_ITEM_FLINCH_END = 0x0224E130
TRY_ITEM_FLINCH_PREIMAGE = bytes.fromhex(
    'f8b50d1c696e0090281c002407f0d4fb071c696e281c221c07f0d8fb061ce86e'
    'ff283cd0382f3ad11e496a581e49114235d11c214143b6206a1880001158002903'
    'd108301058002829d00098edf768fe6421a4f666ecb14221da1448285800012918'
    '1348095c2020084218d0e86ec02141436a180f495158002910d0291c9431086028'
    '1c022188300160281c01210e2200f048fda8680124e8601620a860201cf8bdc046'
    '6c21000049da1f8044300000e90300008c2d0000')

GET_ITEM_EFFECT = 0x02255830
GET_ITEM_MODIFIER = 0x02255844
BATTLE_RANDOM = 0x0223BD98
DIVMOD = 0x020F2998
READ_BATTLE_SCRIPT = 0x0224EB9C
STOP = 0x02239000
CTX = 0x02380000
BATTLE_SYSTEM = 0x02370000
STACK = 0x023FF000
SNAPSHOT_MARKER = 1 << 16
HOLD_EFFECT_FLINCH = 56


def synthetic_overlay():
    image = bytearray(T.OVERLAY_SIZE)
    at = T.CONVERSION_SITE - T.OVERLAY_BASE
    image[at:at + T.CONVERSION_BYTES] = T.CONVERSION_PREIMAGE
    at = T.GROUNDING_SITE - T.OVERLAY_BASE
    image[at:at + len(T.GROUNDING_PREIMAGE)] = T.GROUNDING_PREIMAGE
    at = FIRE_FANG_CONTEXT_ADDRESS - T.OVERLAY_BASE
    image[at:at + len(FIRE_FANG_CONTEXT)] = FIRE_FANG_CONTEXT
    at = RAGE_CONTEXT_ADDRESS - T.OVERLAY_BASE
    image[at:at + len(RAGE_CONTEXT)] = RAGE_CONTEXT
    at = TRY_ITEM_FLINCH - T.OVERLAY_BASE
    image[at:at + len(TRY_ITEM_FLINCH_PREIMAGE)] = TRY_ITEM_FLINCH_PREIMAGE
    return bytes(image)


class FlinchBench:
    """Execute the real late item consumer with only its four seams stubbed."""

    def __init__(self, overlay, *, helper=None, snapshot=0, live=(0, 0), roll=0,
                 move_status=0, damage=1, eligible=True, target_hp=1,
                 target=1, attacker=0):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x00400000)
        self.uc.mem_write(T.OVERLAY_BASE, bytes(overlay))
        if helper is not None:
            self.uc.mem_write(U.HELPER_ADDRESS, bytes(helper))
        self.calls = {'effect': 0, 'modifier': 0, 'rng': 0, 'script': []}
        self.live, self.roll = tuple(live), roll
        self._word(CTX + 0x64, attacker)
        self._word(CTX + 0x6C, target)
        self._word(CTX + 0x216C, move_status)
        self._word(CTX + 0x2D8 + target * 0x1C, damage)
        self._word(CTX + 0x2E0 + target * 0x1C, 0)
        self._word(CTX + 0x3044, 1)
        self.uc.mem_write(CTX + 0x3E9 + 0x10,
                          bytes((0x20 if eligible else 0,)))
        self._word(CTX + 0x2D8C + target * 0xC0, target_hp)
        self._word(CTX + 0x2EC + attacker * 0x1C, snapshot)
        for address in (GET_ITEM_EFFECT, GET_ITEM_MODIFIER, BATTLE_RANDOM,
                        DIVMOD, READ_BATTLE_SCRIPT, STOP):
            self.uc.hook_add(UC_HOOK_CODE, self._seam, begin=address, end=address)

    def _word(self, address, value):
        self.uc.mem_write(address, int(value & 0xFFFFFFFF).to_bytes(4, 'little'))

    def word(self, address):
        return int.from_bytes(self.uc.mem_read(address, 4), 'little')

    @staticmethod
    def _return(uc, value=None):
        if value is not None:
            uc.reg_write(UC_ARM_REG_R0, value)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    def _seam(self, uc, address, _size, _user):
        if address == STOP:
            uc.emu_stop()
        elif address == GET_ITEM_EFFECT:
            self.calls['effect'] += 1
            self._return(uc, self.live[0])
        elif address == GET_ITEM_MODIFIER:
            self.calls['modifier'] += 1
            self._return(uc, self.live[1])
        elif address == BATTLE_RANDOM:
            self.calls['rng'] += 1
            self._return(uc, self.roll)
        elif address == DIVMOD:
            denominator = uc.reg_read(UC_ARM_REG_R1)
            uc.reg_write(UC_ARM_REG_R1, uc.reg_read(UC_ARM_REG_R0) % denominator)
            self._return(uc)
        elif address == READ_BATTLE_SCRIPT:
            self.calls['script'].append(tuple(
                uc.reg_read(register) for register in
                (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2)))
            self._return(uc)

    def run(self):
        self.uc.reg_write(UC_ARM_REG_R0, BATTLE_SYSTEM)
        self.uc.reg_write(UC_ARM_REG_R1, CTX)
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.uc.emu_start(TRY_ITEM_FLINCH | 1, STOP, count=500)
        return {
            'result': self.uc.reg_read(UC_ARM_REG_R0),
            'snapshot': self.word(CTX + 0x2EC),
            'command': self.word(CTX + 0x08),
            'command_next': self.word(CTX + 0x0C),
            'stat_change_type': self.word(CTX + 0x88),
            'stat_change_battler': self.word(CTX + 0x94),
            'calls': self.calls,
        }


class TypeConsumerCompiler(unittest.TestCase):
    def test_exact_in_place_helper_and_native_targets(self):
        with tempfile.TemporaryDirectory() as work:
            payload, receipt = T.compile_native(Path(work))
        self.assertEqual(len(payload), T.CONVERSION_BYTES)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), T.PAYLOAD_SHA256)
        self.assertEqual(receipt['entry'], T.CONVERSION_SITE | 1)
        self.assertEqual(receipt['row_count'], 325)
        call = receipt['random_call_offset']
        self.assertEqual(call, T.RANDOM_CALL_OFFSET)
        self.assertEqual(bl_decode(T.CONVERSION_SITE + call,
                                   payload[call:call + 4]), T.RANDOM)


class TypeConsumerOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='type-consumers-test-')
        cls.payload, cls.compiled = T.compile_native(Path(cls.work.name))

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_patch_is_exact_and_reader_rejects_mutants(self):
        before = synthetic_overlay()
        after, receipt = T.patch_overlay(before, self.payload)
        checked = T.verify_overlay(before, after, self.payload, receipt)
        self.assertTrue(checked['ok'])
        self.assertEqual(after[T.CONVERSION_SITE - T.OVERLAY_BASE:
                               T.CONVERSION_SITE - T.OVERLAY_BASE + 64],
                         self.payload)
        self.assertEqual(after[T.GROUNDING_SITE - T.OVERLAY_BASE:
                               T.GROUNDING_SITE - T.OVERLAY_BASE + 8],
                         T.GROUNDING_REPLACEMENT)
        self.assertEqual(after[FIRE_FANG_EFFECT_SITE - T.OVERLAY_BASE:
                               FIRE_FANG_EFFECT_SITE - T.OVERLAY_BASE + 2],
                         FIRE_FANG_REPLACEMENT)
        self.assertEqual(after[FIRE_FANG_BRANCH - T.OVERLAY_BASE:
                               FIRE_FANG_BRANCH - T.OVERLAY_BASE + 2],
                         FIRE_FANG_BRANCH_PREIMAGE)
        self.assertEqual(after[RAGE_SITE - T.OVERLAY_BASE:
                               RAGE_SITE - T.OVERLAY_BASE + 2],
                         RAGE_REPLACEMENT)
        allowed = set(range(T.CONVERSION_SITE - T.OVERLAY_BASE,
                            T.CONVERSION_SITE - T.OVERLAY_BASE + 64))
        allowed |= set(range(T.GROUNDING_SITE - T.OVERLAY_BASE,
                             T.GROUNDING_SITE - T.OVERLAY_BASE + 8))
        allowed |= set(range(FIRE_FANG_EFFECT_SITE - T.OVERLAY_BASE,
                             FIRE_FANG_EFFECT_SITE - T.OVERLAY_BASE + 2))
        allowed |= set(range(RAGE_SITE - T.OVERLAY_BASE,
                             RAGE_SITE - T.OVERLAY_BASE + 2))
        self.assertTrue(set(receipt['changed_offsets']) <= allowed)
        self.assertEqual(
            set(receipt['changed_offsets'])
            & set(range(FIRE_FANG_EFFECT_SITE - T.OVERLAY_BASE,
                        FIRE_FANG_EFFECT_SITE - T.OVERLAY_BASE + 2)),
            {FIRE_FANG_EFFECT_SITE - T.OVERLAY_BASE})
        self.assertEqual(
            set(receipt['changed_offsets'])
            & set(range(RAGE_SITE - T.OVERLAY_BASE,
                        RAGE_SITE - T.OVERLAY_BASE + 2)),
            {RAGE_SITE - T.OVERLAY_BASE, RAGE_SITE - T.OVERLAY_BASE + 1})
        mutant = bytearray(after); mutant[0] ^= 1
        with self.assertRaises(ValueError):
            T.verify_overlay(before, bytes(mutant), self.payload, receipt)
        forged = dict(receipt, changed_offsets=[])
        with self.assertRaises(ValueError):
            T.verify_overlay(before, after, self.payload, forged)

    def test_preimage_and_payload_mutants_are_refused(self):
        bad = bytearray(synthetic_overlay())
        bad[T.GROUNDING_SITE - T.OVERLAY_BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage'):
            T.patch_overlay(bytes(bad), self.payload)
        bad = bytearray(synthetic_overlay())
        bad[FIRE_FANG_EFFECT_SITE - T.OVERLAY_BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'Fire Fang|preimage'):
            T.patch_overlay(bytes(bad), self.payload)
        bad = bytearray(synthetic_overlay())
        bad[FIRE_FANG_BRANCH - T.OVERLAY_BASE + 1] = 0xE0
        with self.assertRaisesRegex(ValueError, 'Fire Fang|context'):
            T.patch_overlay(bytes(bad), self.payload)
        bad = bytearray(synthetic_overlay())
        bad[RAGE_SITE - T.OVERLAY_BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'Rage|preimage'):
            T.patch_overlay(bytes(bad), self.payload)
        wrong = bytearray(self.payload); wrong[0] ^= 1
        with self.assertRaisesRegex(ValueError, 'identity'):
            T.patch_overlay(synthetic_overlay(), bytes(wrong))


class UTurnFlinchConsumer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='uturn-flinch-test-')
        payload, _ = T.compile_native(Path(cls.work.name))
        typed, _ = T.patch_overlay(synthetic_overlay(), payload)
        cls.overlay, cls.logical = U.patch_overlay(typed)
        cls.helper, cls.compiled = U.compile_native(Path(cls.work.name))

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_exact_helper_and_two_seams(self):
        self.assertEqual((len(self.helper), hashlib.sha256(self.helper).hexdigest()),
                         (U.HELPER_BYTES, U.HELPER_SHA256))
        self.assertEqual(self.compiled['entries'],
                         {'effect': U.EFFECT_ENTRY,
                          'modifier': U.MODIFIER_ENTRY})
        self.assertEqual(bl_decode(U.EFFECT_SITE, U.EFFECT_POSTIMAGE),
                         U.EFFECT_ENTRY & ~1)
        self.assertEqual(bl_decode(U.MODIFIER_SITE, U.MODIFIER_POSTIMAGE),
                         U.MODIFIER_ENTRY & ~1)
        self.assertTrue(U.verify_overlay(
            T.patch_overlay(synthetic_overlay(),
                            T.compile_native(Path(self.work.name))[0])[0],
            self.overlay, self.logical)['ok'])

    def test_overlay_verifier_rejects_mutated_seams_and_receipt(self):
        before = T.patch_overlay(
            synthetic_overlay(), T.compile_native(Path(self.work.name))[0])[0]
        for address in (U.EFFECT_SITE, U.MODIFIER_SITE):
            changed = bytearray(self.overlay)
            changed[address - U.OVERLAY_BASE] ^= 1
            with self.subTest(address=hex(address)), self.assertRaises(ValueError):
                U.verify_overlay(before, bytes(changed), self.logical)
        forged = copy.deepcopy(self.logical)
        forged['changed_offsets'] = forged['changed_offsets'][:-1]
        with self.assertRaises(ValueError):
            U.verify_overlay(before, self.overlay, forged)

    def test_pivot_uses_and_consumes_outgoing_snapshot_not_incoming_item(self):
        rock = SNAPSHOT_MARKER | HOLD_EFFECT_FLINCH | (10 << 8)
        empty = SNAPSHOT_MARKER
        cases = (
            (rock, (0, 0), True),
            (empty, (HOLD_EFFECT_FLINCH, 10), False),
        )
        for snapshot, incoming, expected in cases:
            with self.subTest(snapshot=hex(snapshot), incoming=incoming):
                result = FlinchBench(
                    self.overlay, helper=self.helper, snapshot=snapshot,
                    live=incoming, roll=9).run()
                self.assertEqual(bool(result['result']), expected)
                self.assertEqual(result['snapshot'], 0)
                self.assertEqual((result['calls']['effect'],
                                  result['calls']['modifier']), (0, 0))
                self.assertEqual(result['calls']['rng'], int(expected))
                self.assertEqual(result['calls']['script'],
                                 [(CTX, 1, 14)] if expected else [])
                if expected:
                    self.assertEqual(
                        (result['stat_change_type'],
                         result['stat_change_battler'], result['command']),
                        (2, 1, 22))

    def test_snapshot_preserves_rng_and_late_gate_order(self):
        rock = SNAPSHOT_MARKER | HOLD_EFFECT_FLINCH | (10 << 8)
        matrix = (
            ({'roll': 9}, True, 1),
            ({'roll': 10}, False, 1),
            ({'move_status': 1}, False, 0),
            ({'damage': 0}, False, 0),
            ({'eligible': False}, False, 1),
            ({'target_hp': 0}, False, 1),
        )
        for kwargs, expected, rng_calls in matrix:
            with self.subTest(**kwargs):
                result = FlinchBench(
                    self.overlay, helper=self.helper, snapshot=rock,
                    **kwargs).run()
                self.assertEqual(bool(result['result']), expected)
                self.assertEqual(result['calls']['rng'], rng_calls)
                self.assertEqual(result['snapshot'], 0)

    def test_no_snapshot_keeps_the_ordinary_live_item_path(self):
        for live, roll, expected in (((HOLD_EFFECT_FLINCH, 10), 9, True),
                                     ((HOLD_EFFECT_FLINCH, 10), 10, False),
                                     ((0, 0), 0, False)):
            with self.subTest(live=live, roll=roll):
                result = FlinchBench(
                    self.overlay, helper=self.helper, snapshot=0,
                    live=live, roll=roll).run()
                self.assertEqual(bool(result['result']), expected)
                self.assertEqual((result['calls']['effect'],
                                  result['calls']['modifier']), (1, 1))
                self.assertEqual(result['calls']['rng'], int(live[0] == HOLD_EFFECT_FLINCH))


if __name__ == '__main__':
    unittest.main()
