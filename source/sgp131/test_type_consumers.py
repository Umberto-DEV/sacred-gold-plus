"""Class A contracts for shared overlay-12 type and battle-state edits."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP,
                               UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                               UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)

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
        self.attacker = attacker
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
            if (uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1)) != (CTX,self.attacker):
                raise ValueError('effect getter ABI differs')
            self.calls['effect'] += 1
            self._return(uc, self.live[0])
        elif address == GET_ITEM_MODIFIER:
            if (uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R2)) != (CTX,self.attacker,0):
                raise ValueError('modifier getter ABI differs')
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
        saved = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                 UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
        for i, register in enumerate(saved):
            self.uc.reg_write(register, 0xA5000000 + i)
        self.uc.reg_write(UC_ARM_REG_R0, BATTLE_SYSTEM)
        self.uc.reg_write(UC_ARM_REG_R1, CTX)
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.uc.emu_start(TRY_ITEM_FLINCH | 1, STOP, count=500)
        return {
            'result': self.uc.reg_read(UC_ARM_REG_R0),
            'callee_registers': [self.uc.reg_read(r) for r in saved],
            'sp': self.uc.reg_read(UC_ARM_REG_SP),
            'snapshot': self.word(CTX + 0x2EC + self.attacker * 0x1C),
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


    def test_object_retention_is_opt_in_and_refuses_collision(self):
        with tempfile.TemporaryDirectory() as work:
            work=Path(work)
            plain,old=T.compile_native(work)
            self.assertFalse(list(work.iterdir()))
            self.assertNotIn('retained_object',old)
            payload,receipt=T.compile_native(work,retain_object=True)
            obj=work/'type-consumers.o'
            self.assertTrue(obj.is_file())
            self.assertEqual(payload,plain)
            self.assertEqual(hashlib.sha256(obj.read_bytes()).hexdigest(),receipt['object_sha256'])
            self.assertEqual(receipt['retained_object'],obj.name)
            obj.write_bytes(b'preserve differing artifact')
            with self.assertRaisesRegex(ValueError,'retained object differs'):
                T.compile_native(work,retain_object=True)
            self.assertEqual(obj.read_bytes(),b'preserve differing artifact')

    def test_object_retention_requires_boolean(self):
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError,'boolean'):
                T.compile_native(Path(work),retain_object=1)


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

    def test_unmarked_fallback_preserves_arguments_and_signed_word(self):
        for attacker in range(4):
            for word in (0, 1, 0xFFFF, 0x20000, 0x7FFFFFFF,
                         0x30038, 0x80000000, 0x80010A38, 0xFFFF0A38,
                         0xFBFF0400, 0xFFFEFFFF, 0xFFFF0000,
                         0xFFFFFF37, 0xFFFFFF38, 0xFFFFFFFF):
                with self.subTest(attacker=attacker, word=hex(word)):
                    result = FlinchBench(self.overlay, helper=self.helper,
                                         snapshot=word, attacker=attacker,
                                         live=(HOLD_EFFECT_FLINCH, 10), roll=9).run()
                    self.assertTrue(result['result'])
                    self.assertEqual(result['snapshot'], word)
                    self.assertEqual((result['calls']['effect'],
                                      result['calls']['modifier'],
                                      result['calls']['rng']), (1, 1, 1))

    def test_ordinary_matches_native_full_observation_and_callee_abi(self):
        original = bytearray(U.OVERLAY_SIZE)
        at = U.FUNCTION - U.OVERLAY_BASE
        original[at:at + len(U.FUNCTION_PREIMAGE)] = U.FUNCTION_PREIMAGE
        for attacker in range(4):
            for live, roll in (((0, 0), 0), ((HOLD_EFFECT_FLINCH, 10), 9),
                               ((HOLD_EFFECT_FLINCH, 10), 10)):
                options = dict(snapshot=0xFFFFFF38, attacker=attacker,
                               target=(attacker + 1) % 4, live=live, roll=roll)
                native = FlinchBench(bytes(original), **options).run()
                current = FlinchBench(self.overlay, helper=self.helper, **options).run()
                self.assertEqual(current, native)
                self.assertEqual(current['callee_registers'], [0xA5000000 + i for i in range(8)])
                self.assertEqual(current['sp'], STACK)

    def test_negative_word_cannot_create_flinch_or_rng(self):
        result = FlinchBench(self.overlay, helper=self.helper,
                             snapshot=0xFFFFFF38, live=(0, 0), roll=99).run()
        self.assertFalse(result['result'])
        self.assertEqual(result['snapshot'], 0xFFFFFF38)
        self.assertEqual(result['calls']['rng'], 0)

    def test_snapshot_each_battler_consumes_once(self):
        for attacker in range(4):
            with self.subTest(attacker=attacker):
                result = FlinchBench(self.overlay, helper=self.helper,
                                     snapshot=SNAPSHOT_MARKER | HOLD_EFFECT_FLINCH | (10 << 8),
                                     attacker=attacker, live=(0, 0), roll=9).run()
                self.assertTrue(result['result'])
                self.assertEqual(result['snapshot'], 0)
                self.assertEqual((result['calls']['effect'], result['calls']['modifier'],
                                  result['calls']['rng']), (0, 0, 1))

    def test_consumption_preserves_other_battlers_and_is_one_shot(self):
        for attacker in range(4):
            bench = FlinchBench(self.overlay, helper=self.helper, attacker=attacker,
                                snapshot=SNAPSHOT_MARKER | HOLD_EFFECT_FLINCH | (10 << 8),
                                live=(0, 0), roll=9)
            for other in range(4):
                if other != attacker:
                    bench._word(CTX + 0x2EC + other * 0x1C, 0xA5A50000 | other)
            self.assertTrue(bench.run()['result'])
            for other in range(4):
                expected = 0 if other == attacker else 0xA5A50000 | other
                self.assertEqual(bench.word(CTX + 0x2EC + other * 0x1C), expected)
            self.assertFalse(bench.run()['result'])
            self.assertEqual(bench.calls['rng'], 1)
            self.assertEqual((bench.calls['effect'], bench.calls['modifier']), (1, 1))

    def test_mutations_are_detected_by_marker_abi_and_lifetime_observations(self):
        from sgp12.rom import bl_thumb
        bit = bytearray(self.helper)
        bit[14:20] = bytes.fromhex('d30300bf02d5')  # old bit16 check
        result = FlinchBench(self.overlay, helper=bit, snapshot=0xFFFFFF38,
                             live=(0, 0), roll=99).run()
        self.assertEqual(result['calls']['rng'], 1)
        for instruction in ('0321', '0122'):  # corrupt only r1 or only r2
            bad = bytearray(self.helper)
            bad[68:74] = bytes.fromhex(instruction + '00bf') + bl_thumb(
                U.HELPER_ADDRESS + 72, U.GET_MODIFIER | 1)
            bad += bytes.fromhex('10bd')
            with self.subTest(register=instruction), self.assertRaisesRegex(ValueError, 'modifier getter ABI'):
                FlinchBench(self.overlay, helper=bad, snapshot=0,
                            live=(HOLD_EFFECT_FLINCH, 10), roll=9).run()
        for store in ('00bf', 'dc61'):  # no clear / write next battler
            bad = bytearray(self.helper); bad[64:66] = bytes.fromhex(store)
            bench = FlinchBench(self.overlay, helper=bad,
                                 snapshot=SNAPSHOT_MARKER | HOLD_EFFECT_FLINCH | (10 << 8),
                                 live=(0, 0), roll=9)
            bench._word(CTX + 0x2EC + 0x1C, 0xA5A50001)
            self.assertTrue(bench.run()['result'])
            self.assertEqual(bench.word(CTX + 0x2EC), SNAPSHOT_MARKER | HOLD_EFFECT_FLINCH | (10 << 8))
            if store == 'dc61':
                self.assertEqual(bench.word(CTX + 0x2EC + 0x1C), 0)

    def test_historical_adapter_is_explicitly_pinned_to_r4(self):
        from . import uturn_flinch_r4 as old
        self.assertNotEqual(old.NATIVE, U.NATIVE)
        self.assertEqual(hashlib.sha256(old.NATIVE.read_bytes()).hexdigest(),
                         'e191b1c267282826beab3a20b18eb53375538b396dcdcbda2c6a12407e23422a')
        payload, receipt = old.compile_native(Path(self.work.name))
        self.assertEqual((len(payload), hashlib.sha256(payload).hexdigest()),
                         (68, '8dfc3389b012ba046fd81df9c4a79119d1ffa4bf044b2462720a1868e0ea7f02'))
        self.assertEqual(receipt['source_sha256'],
                         'e191b1c267282826beab3a20b18eb53375538b396dcdcbda2c6a12407e23422a')
        self.assertNotEqual(payload, self.helper)


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentCompositeRage(unittest.TestCase):
    """The real controller and all three reached leaf functions, without stubs."""
    @staticmethod
    def load(language):
        import importlib.util, os
        path=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_rage.py'
        spec=importlib.util.spec_from_file_location('current_rage',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        rom=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        return module,module.G.S.SHARED.read_current(rom,language)

    def test_all_other_bits_and_native_leaf_state(self):
        for language in ('EN','IT'):
            m,x=self.load(language);cpu=m.RageCPU(x['segments'],x['overlay'])
            for bit in range(32):
                status=m.RAGE|(1<<bit)
                result=cpu.observe((status,),(33,),positions=(1+bit%4,),seed=bit)
                m.require_statuses(result,(status&~m.RAGE,))
                self.assertEqual(result['selected_calls'][0]['move'],33)
                self.assertEqual(result['rng_calls'][-1]['after'],result['seed_after'])
                self.assertEqual(len(result['rng_calls']),4)

    def test_rage_selected_absent_and_mixed_battlers(self):
        for language in ('EN','IT'):
            m,x=self.load(language);cpu=m.RageCPU(x['segments'],x['overlay'])
            statuses=(m.RAGE|(1<<21),m.RAGE|0x80000001,1<<21,0xFFFFFFFF)
            result=cpu.observe(statuses,(33,99,33,33),positions=(1,2,3,4))
            m.require_statuses(result,(1<<21,statuses[1],1<<21,0xFF7FFFFF))
            self.assertEqual([x['battler'] for x in result['selected_calls']],[0,1,3])

    def test_old_and_wrong_mask_are_not_admitted_or_semantically_accepted(self):
        for language in ('EN','IT'):
            m,x=self.load(language)
            for variant in ('old','wrong_mask'):
                image=m.counter_image(x['overlay'],variant)
                with self.assertRaises(ValueError):m.RageCPU(x['segments'],image)
                result=m.RageCPU(x['segments'],image,variant=variant).observe((0xFFFFFFFF,),(33,))
                with self.assertRaises(ValueError):m.require_statuses(result,(0xFF7FFFFF,))


    def test_leaf_identity_and_embedded_data_cannot_be_executed(self):
        m,x=self.load('EN')
        for address in (m.ENTRY,m.MAX,m.SELECTED,m.G.RNG):
            changed=bytearray(x['overlay']);changed[address-m.G.T.OVERLAY_BASE]^=1
            with self.assertRaises(ValueError):m.RageCPU(x['segments'],changed)
        cpu=m.RageCPU(x['segments'],x['overlay']);cpu.observe((m.RAGE,),(33,))
        for address in (m.ENTRY+38,m.END-20,m.SELECTED+44,m.G.RNG+30):
            cpu.current=dict(instructions=0,stack_depth=0)
            try:
                with self.assertRaises(ValueError):cpu.uc.emu_start(address|1,m.STOP,count=1)
            finally:cpu.current=None


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentTransformTransport(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_transform.py'
        spec=importlib.util.spec_from_file_location('current_transform_transport',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        return module,module.R.G.S.SHARED.read_current(path,language)

    def test_preserved_transform_is_emitted_and_blocks_move_pp_requests(self):
        for language in ('EN','IT'):
            m,x=self.load(language)
            result=m.run_chain(x,m.R.RAGE|m.TRANSFORM|1<<24,33)
            self.assertEqual(result['emitter']['status2'],m.TRANSFORM|1<<24)
            self.assertEqual(result['consumer']['move_pp_requests'],[])
            self.assertEqual(result['consumer']['busy_after'],0)

    def test_old_and_is_a_downstream_counterexample(self):
        for language in ('EN','IT'):
            m,x=self.load(language)
            result=m.run_chain(x,m.R.RAGE|m.TRANSFORM|1<<24,33,variant='old')
            self.assertEqual(result['rage']['statuses'],[m.R.RAGE])
            self.assertEqual(result['emitter']['status2'],m.R.RAGE)
            self.assertEqual(len(result['consumer']['move_pp_requests']),8)
            self.assertTrue(result['consumer']['pokemon_canary_unchanged'])

    def test_mimic_slots_and_party_index_remain_independent(self):
        for language in ('EN','IT'):
            m,x=self.load(language)
            for mask in (1,2,4,8,15):
                result=m.run_chain(x,m.R.RAGE,33,mimic=mask,party_slot=5,side=1)
                calls=result['consumer']['move_pp_requests']
                self.assertEqual([c['field'] for c in calls],[field for i in range(4) if not mask&(1<<i) for field in (54+i,58+i)])
                self.assertEqual(result['emitter']['party_slot'],5)


    def test_packet_and_gate_counters_require_distinct_oracles(self):
        m,x=self.load('EN')
        for variant in ('wrong_field','wrong_gate'):
            changed=m.counter_image(x['overlay'],variant)
            with self.assertRaises(ValueError):m.TransportCPU(x['segments'],changed)
            result=m.run_chain(x,m.R.RAGE|m.TRANSFORM|1<<24,33,variant=variant)
            oracle=m.require_transport if variant=='wrong_field' else m.require_protection
            with self.assertRaises(ValueError):oracle(result)
            if variant=='wrong_field':self.assertEqual(result['consumer']['move_pp_requests'],[])


class UTurnRetainedCompiler(unittest.TestCase):
    def test_opt_in_retention_keeps_default_receipt_and_bytes(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);plain,default=U.compile_native(root)
            self.assertEqual(list(root.iterdir()),[])
            payload,receipt=U.compile_native(root,retain_object=True)
            self.assertEqual(payload,plain)
            self.assertEqual(default,{k:v for k,v in receipt.items() if k!='retained_object'})
            self.assertEqual(hashlib.sha256((root/receipt['retained_object']).read_bytes()).hexdigest(),receipt['object_sha256'])

    def test_retention_refuses_nonboolean_and_conflicting_artifact(self):
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);target=root/'uturn.o';target.write_bytes(b'preserve existing object')
            with self.assertRaisesRegex(ValueError,'retained object differs'):U.compile_native(root,retain_object=True)
            self.assertEqual(target.read_bytes(),b'preserve existing object')
            with self.assertRaisesRegex(ValueError,'boolean'):U.compile_native(root,retain_object=1)


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentCompositeUTurn(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_uturn.py'
        spec=importlib.util.spec_from_file_location('current_uturn_attribution',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        image=module.G.S.SHARED.read_current(path,language)
        resources=module.read_resources(path,image)
        return module,image,resources

    def test_actual_native_marked_path_uses_outgoing_data_and_consumes_once(self):
        for language in ('EN','IT'):
            m,x,resources=self.load(language);cpu=m.NativeFlinch(x,resources)
            result=cpu.observe(pivot=True,outgoing=221,incoming=0,roll=9,attacker=3)
            self.assertEqual(result['snapshot_before'],0x10A38)
            self.assertEqual(result['snapshot_after'],0)
            self.assertTrue(result['flinch'])
            self.assertFalse(result['modifier_abi_issues'])
            repeat=cpu.repeat_parent()
            self.assertFalse(repeat['flinch']);self.assertEqual(repeat['snapshot_after'],0)

    def test_current_unmarked_fallback_failure_is_observed_against_native_baseline(self):
        for language in ('EN','IT'):
            m,x,resources=self.load(language)
            result=m.NativeFlinch(x,resources).observe(pivot=False,incoming=221,roll=9)
            baseline=m.NativeFlinch(m.counter_image(x,'old_hooks'),resources,variant='old_hooks').observe(pivot=False,incoming=221,roll=9)
            self.assertTrue(baseline['flinch']);self.assertFalse(result['flinch'])
            self.assertEqual(result['modifier_abi_issues'][0]['args'][1:],[0,0x2EC])
            self.assertEqual(result['item_queries'][-1]['item'],0)
            self.assertEqual(result['item_queries'][-1]['value'],0)

    def test_negative_native_field_collides_with_the_bit16_marker(self):
        for language in ('EN','IT'):
            m,x,resources=self.load(language)
            options=dict(pivot=False,incoming=0,ordinary_word=-200,damage=0xFFFFFF38,roll=99)
            current=m.NativeFlinch(x,resources).observe(**options)
            native=m.NativeFlinch(m.counter_image(x,'old_hooks'),resources,variant='old_hooks').observe(**options)
            self.assertEqual(current['snapshot_before'],0xFFFFFF38)
            self.assertTrue(current['flinch']);self.assertEqual(current['snapshot_after'],0)
            self.assertFalse(native['flinch']);self.assertEqual(native['snapshot_after'],0xFFFFFF38)
            self.assertFalse(current['modifier_abi_issues'])

    def test_same_flinch_result_does_not_excuse_uncleared_snapshot(self):
        m,x,resources=self.load('EN');changed=m.counter_image(x,'no_clear')
        with self.assertRaises(ValueError):m.NativeFlinch(changed,resources)
        result=m.NativeFlinch(changed,resources,variant='no_clear').observe(pivot=True,outgoing=221,incoming=0,roll=9)
        self.assertTrue(result['flinch'])
        with self.assertRaises(ValueError):m.require_consumed(result)

    def test_native_effective_getter_inputs_suppress_snapshot_under_klutz_or_embargo(self):
        for language in ('EN','IT'):
            m,x,resources=self.load(language)
            for options in (dict(klutz=True),dict(embargo=True)):
                result=m.NativeFlinch(x,resources).observe(pivot=True,outgoing=221,incoming=221,**options)
                self.assertEqual(result['snapshot_before'],0x10000)
                self.assertFalse(result['flinch']);self.assertEqual(result['snapshot_after'],0)


class UTurnAttributionCLI(unittest.TestCase):
    def test_json_cannot_replace_retained_artifacts_or_aliases(self):
        import importlib.util,sys
        from unittest.mock import patch
        path=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_uturn.py'
        spec=importlib.util.spec_from_file_location('uturn_cli_guard',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as work:
            root=Path(work)
            for name in ('uturn.o','native.bin','compile-retained.json'):
                artifact=root/name;artifact.write_bytes(b'preserve artifact')
                alias=root/('alias-'+name);alias.symlink_to(artifact)
                hard=root/('hard-'+name);hard.hardlink_to(artifact)
                for mode in ('--build','--work'):
                    for output in (artifact,alias,hard):
                        argv=['uturn','--rom',str(root/'r4.nds'),'--v4',str(root/'v4.nds'),'--base',str(root/'base.nds'),'--retail',str(root/'retail.nds'),'--language','EN',mode,str(root),'--json',str(output)]
                        with self.subTest(name=name,mode=mode,output=output.name),patch.object(sys,'argv',argv),patch.object(module,'compile_object') as compile_call,patch.object(module,'verify_build') as reuse_call:
                            with self.assertRaises(SystemExit) as caught:module.main()
                            self.assertEqual(caught.exception.code,2);self.assertEqual(artifact.read_bytes(),b'preserve artifact')
                            compile_call.assert_not_called();reuse_call.assert_not_called()


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentHPFlinchPath(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_hp_flinch.py'
        spec=importlib.util.spec_from_file_location('current_hp_flinch_path',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        model=module.F.G.S.SHARED.read_current(path,language)
        return module,model,module.resources(path,model)

    def test_guest_writer_hp_script_and_both_caller_branches(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            for message in (0,1):
                result=m.HPPathCPU(x,data).observe(message_type=message);m.require_chain(result)
                self.assertEqual(result['before']['word'],0)
                self.assertEqual(result['after_hp']['word'],0xFFFFFF38)
                self.assertEqual(result['after_script']['hp'],100)
                self.assertEqual(result['after_script']['word'],0xFFFFFF38)
                self.assertTrue(result['flinch']);self.assertEqual(result['after_damage']['word'],0)

    def test_native_baseline_preserves_negative_word_without_flinch(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            result=m.HPPathCPU(m.F.counter_image(x,'old_hooks'),data,variant='old_hooks').observe();m.require_chain(result)
            self.assertFalse(result['flinch']);self.assertEqual(result['after_damage']['word'],0xFFFFFF38)
            self.assertEqual(result['after_run']['calls']['rng'],0)

    def test_damage_controls_and_rng_before_move_eligibility(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            for options in (dict(damage=-199),dict(damage=0),dict(eligible=False)):
                result=m.HPPathCPU(x,data).observe(**options);m.require_chain(result)
                self.assertFalse(result['flinch'])
                self.assertEqual(result['after_run']['calls']['rng'],int(options==dict(eligible=False)))

    def test_same_output_cannot_hide_wrong_intermediate_state(self):
        import copy
        m,x,data=self.load('EN');result=m.HPPathCPU(x,data).observe();m.require_chain(result)
        for checkpoint,field in (('before','word'),('after_hp','physical_damage'),('after_script','word'),('after_script','hp'),('after_damage','seed')):
            changed=copy.deepcopy(result);changed[checkpoint][field]^=1
            with self.assertRaises(ValueError):m.require_chain(changed)
        changed=copy.deepcopy(result);changed['script_runs'][0]['script_commands'][0]['cursor']=1
        with self.assertRaises(ValueError):m.require_chain(changed)

    def test_window_script_and_fixture_admission_is_strict(self):
        m,x,data=self.load('EN')
        changed=dict(x);image=bytearray(x['overlay']);image[m.HP-m.F.U.OVERLAY_BASE]^=1;changed['overlay']=bytes(image)
        with self.assertRaises(ValueError):m.HPPathCPU(changed,data)
        changed_data=dict(data);changed_data['hp_script']=bytes(152)
        with self.assertRaises(ValueError):m.HPPathCPU(x,changed_data)
        cpu=m.HPPathCPU(x,data)
        for options in (dict(damage=True),dict(damage=-300),dict(damage=1),dict(eligible=1),dict(message_type=2)):
            with self.assertRaises(ValueError):cpu.observe(**options)


class HPFlinchAttributionCLI(unittest.TestCase):
    def test_json_preserves_each_input_and_its_aliases(self):
        import importlib.util,sys
        from unittest.mock import patch
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_hp_flinch.py'
        spec=importlib.util.spec_from_file_location('hp_flinch_cli',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);inputs=[root/(name+'.nds') for name in ('rom','v4','base','retail')]
            for path in inputs:path.write_bytes(b'preserve input')
            for path in inputs:
                symbolic=root/(path.stem+'-symbolic.nds');symbolic.symlink_to(path)
                hard=root/(path.stem+'-hard.nds');__import__('os').link(path,hard)
                for output in (path,symbolic,hard):
                    argv=['hp-flinch','--language','EN','--json',str(output)]
                    for name,value in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(value)))
                    with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(module,'analyze') as analyze:
                        with self.assertRaises(SystemExit) as caught:module.main()
                        self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
                        self.assertEqual(path.read_bytes(),b'preserve input')


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentNativeUTurnProducer(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_uturn_producer.py'
        spec=importlib.util.spec_from_file_location('current_native_uturn_producer',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        model=module.F.G.S.SHARED.read_current(path,language)
        return module,model,module.resources(path,model)

    def test_native_producer_packs_real_items_for_both_attacker_slots(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            for item,actor in ((221,0),(327,3)):
                result=m.ProducerCPU(x,data).observe(outgoing=item,attacker=actor);m.require_producer(result)
                self.assertEqual(result['snapshot'],0x10A38);self.assertEqual(result['calc_temp_after'],0xA00)
                self.assertEqual([q['attribute'] for q in result['producer']['item_queries']],[1,2])
                self.assertEqual(result['producer']['calls']['modifier'],0)
                self.assertEqual(result['producer']['script_commands'][-1]['word'],0x10A38)

    def test_non_effective_branch_preserves_nonzero_calc_temp(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            for options in (dict(outgoing=0),dict(klutz=True),dict(embargo=True)):
                result=m.ProducerCPU(x,data).observe(attacker=3,calc_temp=0x12345678,**options);m.require_producer(result)
                self.assertEqual(result['calc_temp_after'],0x12345678);self.assertEqual(result['snapshot'],0x10000)
                self.assertFalse(result['consumer']['flinch'])
                self.assertEqual(len(result['producer']['item_queries']),1)

    def test_raw_script_copy_changes_only_the_stop_word(self):
        import struct
        m,x,data=self.load('EN');raw=data['script'];fixture=m.script_fixture(raw)
        self.assertEqual(fixture[:164],raw[:164]);self.assertEqual(fixture[168:],raw[168:])
        self.assertEqual(fixture[60:164],m.F.SCRIPT.INSERT)
        self.assertEqual(struct.unpack_from('<I',fixture,164)[0],224)
        changed=bytearray(raw);changed[60]^=1
        with self.assertRaises(ValueError):m.script_fixture(bytes(changed))

    def test_same_flinch_output_rejects_inexact_packing(self):
        m,x,data=self.load('EN')
        current=m.ProducerCPU(x,data).observe();m.require_producer(current)
        counter=m.ProducerCPU(x,data,fixture_variant='wrong_shift').observe()
        self.assertTrue(counter['consumer']['flinch']);self.assertTrue(current['consumer']['flinch'])
        self.assertEqual(counter['snapshot'],0x11438)
        with self.assertRaises(ValueError):m.require_producer(counter)

    def test_repeat_records_fallback_rng_and_preserves_fixture_domain(self):
        m,x,data=self.load('EN');cpu=m.ProducerCPU(x,data)
        result=cpu.observe(outgoing=0,incoming=221);m.require_producer(result)
        self.assertEqual(result['consumer']['calls']['rng'],0)
        self.assertEqual(result['repeat']['calls']['rng'],1)
        self.assertTrue(result['repeat']['modifier_abi_issues']);self.assertFalse(result['repeat']['flinch'])
        for options in (dict(attacker=True),dict(attacker=4),dict(roll=100),dict(outgoing=1),dict(calc_temp=-1),dict(klutz=1)):
            with self.assertRaises(ValueError):cpu.observe(**options)


class UTurnProducerAttributionCLI(unittest.TestCase):
    def test_json_preserves_each_input_and_its_aliases(self):
        import importlib.util,sys
        from unittest.mock import patch
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_uturn_producer.py'
        spec=importlib.util.spec_from_file_location('uturn_producer_cli',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);inputs=[root/(name+'.nds') for name in ('rom','v4','base','retail')]
            for path in inputs:path.write_bytes(b'preserve input')
            for path in inputs:
                symbolic=root/(path.stem+'-symbolic.nds');symbolic.symlink_to(path)
                hard=root/(path.stem+'-hard.nds');__import__('os').link(path,hard)
                for output in (path,symbolic,hard):
                    argv=['uturn-producer','--language','EN','--json',str(output)]
                    for name,value in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(value)))
                    with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(module,'analyze') as analyze:
                        with self.assertRaises(SystemExit) as caught:module.main()
                        self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
                        self.assertEqual(path.read_bytes(),b'preserve input')


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentAfterDamageContinuation(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_afterdamage.py'
        spec=importlib.util.spec_from_file_location('current_afterdamage_continuation',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        model=module.F.G.S.SHARED.read_current(path,language)
        return module,model,module.resources(path,model)

    def test_both_message_paths_reach_request_from_native_state_zero(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            for message in (0,1):
                result=m.AfterCPU(x,data).observe(message_type=message);m.require_continuation(result)
                self.assertEqual(result['before_after_state'],0)
                self.assertEqual(result['script_requests'],[2,16,293,14])
                self.assertEqual(result['final']['state'],7)
                self.assertEqual(result['final_word'],0)
                self.assertTrue(result['flinch'])

    def test_native_baseline_traverses_scripts_without_flinch_request(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            result=m.AfterCPU(m.F.counter_image(x,'old_hooks'),data,variant='old_hooks').observe();m.require_continuation(result)
            self.assertEqual(result['script_requests'],[2,16,293])
            self.assertEqual(result['final_word'],0xFFFFFF38)
            self.assertFalse(result['flinch']);self.assertEqual(result['final']['state'],0)

    def test_damage_and_eligibility_controls_keep_rng_distinct(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            for options in (dict(damage=-199),dict(damage=0),dict(eligible=False)):
                result=m.AfterCPU(x,data).observe(**options);m.require_continuation(result)
                self.assertFalse(result['flinch'])
                self.assertEqual(result['script_requests'],([2] if options.get('damage')!=0 else [])+[16,293])
                self.assertEqual(result['final']['seed']!=result['before']['seed'],options==dict(eligible=False))

    def test_same_request_cannot_hide_host_state_injection_or_wrong_script_path(self):
        import copy
        m,x,data=self.load('EN');result=m.AfterCPU(x,data).observe();m.require_continuation(result)
        changed=copy.deepcopy(result);changed['before_after_state']=6
        with self.assertRaises(ValueError):m.require_continuation(changed)
        changed=copy.deepcopy(result);changed['final']['state']=6
        with self.assertRaises(ValueError):m.require_continuation(changed)
        changed=copy.deepcopy(result);changed['runs'][4]['before']['word']^=1
        with self.assertRaises(ValueError):m.require_continuation(changed)
        changed=copy.deepcopy(result);changed['runs'][5]['run']['script_commands'][-1]['cursor']=49
        with self.assertRaises(ValueError):m.require_continuation(changed)

    def test_new_helper_and_script_pins_refuse_drift(self):
        m,x,data=self.load('EN')
        for address in (0x0224DF7C,0x0223E474,0x0224EDE0,0x0224EECC):
            changed=dict(x);image=bytearray(x['overlay']);image[address-m.F.U.OVERLAY_BASE]^=1;changed['overlay']=bytes(image)
            with self.assertRaises(ValueError):m.AfterCPU(changed,data)
        changed=dict(data);changed['subscripts']=dict(data['subscripts']);changed['subscripts'][16]=bytes(204)
        with self.assertRaises(ValueError):m.AfterCPU(x,changed)


class AfterDamageAttributionCLI(unittest.TestCase):
    def test_json_preserves_each_input_and_its_aliases(self):
        import importlib.util,sys
        from unittest.mock import patch
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_afterdamage.py'
        spec=importlib.util.spec_from_file_location('afterdamage_cli',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);inputs=[root/(name+'.nds') for name in ('rom','v4','base','retail')]
            for path in inputs:path.write_bytes(b'preserve input')
            for path in inputs:
                symbolic=root/(path.stem+'-symbolic.nds');symbolic.symlink_to(path)
                hard=root/(path.stem+'-hard.nds');__import__('os').link(path,hard)
                for output in (path,symbolic,hard):
                    argv=['afterdamage','--language','EN','--json',str(output)]
                    for name,value in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(value)))
                    with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(module,'analyze') as analyze:
                        with self.assertRaises(SystemExit) as caught:module.main()
                        self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
                        self.assertEqual(path.read_bytes(),b'preserve input')


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentNativeFlinchEffect(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_flinch_effect.py'
        spec=importlib.util.spec_from_file_location('current_native_flinch_effect',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        model=module.F.G.S.SHARED.read_current(path,language)
        return module,model,module.resources(path,model)

    def test_real_ability_and_status_setter_apply_only_target_bit(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language);result=m.EffectCPU(x,data).observe();m.require_effect(result)
            self.assertTrue(result['continuation']['flinch']);self.assertEqual(result['status_after'],0x408)
            self.assertEqual(result['attacker_after'],0)
            self.assertTrue(any(r.get('native_ability_calls') for r in result['effects']))
            self.assertFalse(any(v['name']=='ability' for r in result['effects'] for v in r['models']))
            stores=[w for r in result['effects'] for w in r['writes'] if w['pc']=='0x224f3e0']
            self.assertEqual(stores,[dict(pc='0x224f3e0',address=hex(m.CTX+0x2E70),bytes=4,value=0x408)])

    def test_ability_action_and_substitute_gates_block_after_a_real_request(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            for options in (dict(target_ability=39),dict(target_ability=19),dict(already_acted=True),dict(substitute_hit=True)):
                result=m.EffectCPU(x,data).observe(**options);m.require_effect(result)
                self.assertTrue(result['continuation']['flinch']);self.assertEqual(result['status_after'],0x400)
                self.assertFalse(any(w['pc']=='0x224f3e0' for r in result['effects'] for w in r['writes']))
                self.assertEqual(result['seed_after'],result['seed_before'])

    def test_old_hooks_and_ineligible_move_do_not_run_the_effect(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            old=m.EffectCPU(m.F.counter_image(x,'old_hooks'),data,variant='old_hooks').observe();m.require_effect(old)
            bite=m.EffectCPU(x,data).observe(eligible=False);m.require_effect(bite)
            for result in (old,bite):
                self.assertFalse(result['continuation']['flinch']);self.assertEqual(result['effects'],[])
                self.assertEqual(result['status_after'],0x400)

    def test_zero_status_and_same_completed_script_wrong_mask(self):
        m,x,data=self.load('EN');plain=m.EffectCPU(x,data).observe(base_status=0);m.require_effect(plain)
        self.assertEqual(plain['status_after'],8)
        counter=m.EffectCPU(x,data,fixture_variant='wrong_mask').observe()
        self.assertTrue(counter['continuation']['flinch']);self.assertEqual(counter['final_command'],29)
        self.assertEqual(counter['status_after'],0x410)
        with self.assertRaises(ValueError):m.require_effect(counter)

    def test_native_pins_and_raw_script_identity_refuse_mutation(self):
        m,x,data=self.load('EN')
        for address in (0x022527CC,0x02252834,0x0224EFD2,0x0224F168,0x0224F3DE):
            changed=dict(x);image=bytearray(x['overlay']);image[address-m.F.U.OVERLAY_BASE]^=1;changed['overlay']=bytes(image)
            with self.assertRaises(ValueError):m.EffectCPU(changed,data)
        changed=dict(data);changed['subscripts']=dict(data['subscripts']);raw=bytearray(changed['subscripts'][14]);raw[100]=16;changed['subscripts'][14]=bytes(raw)
        with self.assertRaises(ValueError):m.EffectCPU(x,changed)

    def test_fixture_domains_and_wrong_summary_are_rejected(self):
        import copy
        m,x,data=self.load('EN');cpu=m.EffectCPU(x,data)
        for options in (dict(target_ability=True),dict(target_ability=104),dict(base_status=8),dict(already_acted=1),dict(substitute_hit=1)):
            with self.assertRaises(ValueError):cpu.observe(**options)
        result=cpu.observe();m.require_effect(result)
        for field in ('status_after','attacker_after','seed_after','shared_word'):
            changed=copy.deepcopy(result);changed[field]^=1
            with self.assertRaises(ValueError):m.require_effect(changed)


class FlinchEffectAttributionCLI(unittest.TestCase):
    def test_json_preserves_each_input_and_its_aliases(self):
        import importlib.util,sys
        from unittest.mock import patch
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_flinch_effect.py'
        spec=importlib.util.spec_from_file_location('flinch_effect_cli',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);inputs=[root/(name+'.nds') for name in ('rom','v4','base','retail')]
            for path in inputs:path.write_bytes(b'preserve input')
            for path in inputs:
                symbolic=root/(path.stem+'-symbolic.nds');symbolic.symlink_to(path)
                hard=root/(path.stem+'-hard.nds');__import__('os').link(path,hard)
                for output in (path,symbolic,hard):
                    argv=['flinch-effect','--language','EN','--json',str(output)]
                    for name,value in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(value)))
                    with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(module,'analyze') as analyze:
                        with self.assertRaises(SystemExit) as caught:module.main()
                        self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
                        self.assertEqual(path.read_bytes(),b'preserve input')


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentNativeFlinchConsumer(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_flinch_consumer.py'
        spec=importlib.util.spec_from_file_location('current_native_flinch_consumer',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        model=module.F.G.S.SHARED.read_current(path,language)
        return module,model,module.resources(path,model)

    def test_produced_bit_is_cleared_by_native_caller_and_cancellation_script(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language);result=m.ConsumerCPU(x,data).observe_action();m.require_consumer(result)
            self.assertEqual(result['effect']['status_after'],8)
            self.assertEqual(result['actor_status_after'],0)
            self.assertEqual(result['move_fail_after'],0x40)
            self.assertEqual(result['consumer_requests'],[278,15])
            self.assertEqual(result['final_command'],39)
            self.assertEqual(len(result['runs']),36)

    def test_other_actor_preserves_the_bit_and_old_hooks_have_none(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            other=m.ConsumerCPU(x,data).observe_action(actor=0,direct_status=True);m.require_consumer(other)
            old=m.ConsumerCPU(m.F.counter_image(x,'old_hooks'),data,variant='old_hooks').observe_action(direct_status=True);m.require_consumer(old)
            self.assertEqual(other['target1_status_after'],8)
            for result in (other,old):
                self.assertEqual(result['runs'][0]['run']['result'],0)
                self.assertEqual(result['consumer_requests'],[])
                self.assertEqual(result['final_command'],23)

    def test_same_final_command_cannot_hide_wrong_flags_clear_or_wait(self):
        import copy
        m,x,data=self.load('EN');result=m.ConsumerCPU(x,data).observe_action();m.require_consumer(result)
        for field in ('actor_status_after','target1_status_after','move_fail_after','move_status_after','seed_after','status_check_state'):
            changed=copy.deepcopy(result);changed[field]^=1
            with self.subTest(field=field),self.assertRaises(ValueError):m.require_consumer(changed)
        for pc in ('0x224b7a0','0x224b7ac','0x223e366'):
            changed=copy.deepcopy(result)
            write=next(w for row in changed['runs'] for w in row['run']['writes'] if w['pc']==pc);write['value']^=1
            with self.subTest(pc=pc),self.assertRaises(ValueError):m.require_consumer(changed)
        changed=copy.deepcopy(result);changed['boundary']['status_words_preserved'][1]=0
        with self.assertRaises(ValueError):m.require_consumer(changed)
        changed=copy.deepcopy(result);changed['consumer_requests']=[15]
        with self.assertRaises(ValueError):m.require_consumer(changed)

    def test_new_native_windows_and_scripts_refuse_drift(self):
        m,x,data=self.load('EN')
        for address,_,_ in m.WINDOWS:
            changed=dict(x)
            if address<m.F.U.OVERLAY_BASE:
                segments=[]
                for base,raw in x['segments']:
                    image=bytearray(raw)
                    if base<=address<base+len(raw):image[address-base]^=1
                    segments.append((base,bytes(image)))
                changed['segments']=segments
            else:
                image=bytearray(x['overlay']);image[address-m.F.U.OVERLAY_BASE]^=1;changed['overlay']=bytes(image)
            with self.subTest(address=hex(address)),self.assertRaises(ValueError):m.ConsumerCPU(changed,data)
        for index in m.SCRIPTS:
            changed=dict(data);changed['subscripts']=dict(data['subscripts']);raw=bytearray(changed['subscripts'][index]);raw[0]^=1;changed['subscripts'][index]=bytes(raw)
            with self.subTest(script=index),self.assertRaises(ValueError):m.ConsumerCPU(x,changed)

    def test_fixture_domains_refuse_ambiguous_actors(self):
        m,x,data=self.load('EN');cpu=m.ConsumerCPU(x,data)
        for options in (dict(actor=True),dict(actor=2),dict(direct_status=1)):
            with self.assertRaises(ValueError):cpu.observe_action(**options)


class FlinchConsumerAttributionCLI(unittest.TestCase):
    def test_json_preserves_each_input_and_its_aliases(self):
        import importlib.util,sys
        from unittest.mock import patch
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_flinch_consumer.py'
        spec=importlib.util.spec_from_file_location('flinch_consumer_cli',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);inputs=[root/(name+'.nds') for name in ('rom','v4','base','retail')]
            for path in inputs:path.write_bytes(b'preserve input')
            for path in inputs:
                symbolic=root/(path.stem+'-symbolic.nds');symbolic.symlink_to(path)
                hard=root/(path.stem+'-hard.nds');__import__('os').link(path,hard)
                for output in (path,symbolic,hard):
                    argv=['flinch-consumer','--language','EN','--json',str(output)]
                    for name,value in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(value)))
                    with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(module,'analyze') as analyze:
                        with self.assertRaises(SystemExit) as caught:module.main()
                        self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
                        self.assertEqual(path.read_bytes(),b'preserve input')


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentNativeActionEnd(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_actionend.py'
        spec=importlib.util.spec_from_file_location('current_native_action_end',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        model=module.F.G.S.SHARED.read_current(path,language)
        return module,model,module.C.resources(path,model)

    def test_ordinary_native_completion_advances_selected_action_without_pp_use(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language);result=m.ActionCPU(x,data).observe_end();m.require_end(result)
            self.assertEqual(result['final']['actions'],[23,40])
            self.assertEqual(result['final']['execution_index'],1)
            self.assertEqual(result['final']['command'],8)
            self.assertEqual(result['final']['pp'],[[35,0,0,0],[35,0,0,0]])
            self.assertEqual(len(result['end']['rng_calls']),2)
            self.assertTrue(result['final']['self_turn_zero'])

    def test_wrong_order_same_command_completes_another_actor_and_is_rejected(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language);result=m.ActionCPU(x,data,order_variant='wrong_order').observe_end()
            self.assertEqual(result['final']['command'],8)
            self.assertEqual(result['final']['actions'],[40,23])
            result['order_variant']='current'
            with self.assertRaises(ValueError):m.require_end(result)

    def test_summary_rng_and_bulk_clear_mutations_cannot_hide_behind_command8(self):
        import copy
        m,x,data=self.load('EN');result=m.ActionCPU(x,data).observe_end();m.require_end(result)
        for field in ('execution_index','move_fail','move_status','battle_status','seed','status_state','try_state'):
            changed=copy.deepcopy(result);changed['final'][field]^=1
            with self.subTest(field=field),self.assertRaises(ValueError):m.require_end(changed)
        for pc in ('0x224d3fe','0x224d434','0x20d48a4'):
            changed=copy.deepcopy(result);next(w for w in changed['end']['writes'] if w['pc']==pc)['address']=hex(m.CTX)
            with self.subTest(pc=pc),self.assertRaises(ValueError):m.require_end(changed)
        changed=copy.deepcopy(result);changed['end']['rng_calls'][0]['after']^=1
        with self.assertRaises(ValueError):m.require_end(changed)
        changed=copy.deepcopy(result);changed['clear_calls'].pop()
        with self.assertRaises(ValueError):m.require_end(changed)
        changed=copy.deepcopy(result);changed['after_history']['history_fields'][0]=33
        with self.assertRaises(ValueError):m.require_end(changed)
        changed=copy.deepcopy(result);changed['final']['pp'][1][0]=34
        with self.assertRaises(ValueError):m.require_end(changed)

    def test_native_dependency_pins_refuse_overlay_and_arm_clear_drift(self):
        m,x,data=self.load('EN')
        for address,_,_ in m.WINDOWS:
            changed=dict(x)
            if address<m.F.U.OVERLAY_BASE:
                segments=[]
                for base,raw in x['segments']:
                    image=bytearray(raw)
                    if base<=address<base+len(raw):image[address-base]^=1
                    segments.append((base,bytes(image)))
                changed['segments']=segments
            else:
                image=bytearray(x['overlay']);image[address-m.F.U.OVERLAY_BASE]^=1;changed['overlay']=bytes(image)
            with self.subTest(address=hex(address)),self.assertRaises(ValueError):m.ActionCPU(changed,data)
        with self.assertRaises(ValueError):m.ActionCPU(x,data,order_variant='ambiguous')

    def test_native_bulk_clear_rejects_overflow_unaligned_width_and_value(self):
        m,x,data=self.load('EN');cpu=m.ActionCPU(x,data);cpu.end_phase=True;cpu.current=dict(writes=[])
        cpu.pending_clear=dict(destination=m.CTX+0x2D4)
        cpu.uc.reg_write(m.UC_ARM_REG_PC,0x020D48A4)
        for offset,width,value in ((28,4,0),(-4,4,0),(1,4,0),(0,1,0),(0,4,1)):
            with self.subTest(offset=offset,width=width,value=value),self.assertRaises(ValueError):
                cpu._write(cpu.uc,0,m.CTX+0x2D4+offset,width,value,None)


class ActionEndAttributionCLI(unittest.TestCase):
    def test_json_preserves_each_input_and_its_aliases(self):
        import importlib.util,sys
        from unittest.mock import patch
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_actionend.py'
        spec=importlib.util.spec_from_file_location('action_end_cli',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);inputs=[root/(name+'.nds') for name in ('rom','v4','base','retail')]
            for path in inputs:path.write_bytes(b'preserve input')
            for path in inputs:
                symbolic=root/(path.stem+'-symbolic.nds');symbolic.symlink_to(path)
                hard=root/(path.stem+'-hard.nds');__import__('os').link(path,hard)
                for output in (path,symbolic,hard):
                    argv=['action-end','--language','EN','--json',str(output)]
                    for name,value in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(value)))
                    with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(module,'analyze') as analyze:
                        with self.assertRaises(SystemExit) as caught:module.main()
                        self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
                        self.assertEqual(path.read_bytes(),b'preserve input')


@unittest.skipUnless(__import__('os').environ.get('SGP_R4_ROM_DIR'),
                     'requires exact r4 EN/IT through SGP_R4_ROM_DIR')
class CurrentNativeNextAction(unittest.TestCase):
    @staticmethod
    def load(language):
        import importlib.util,os
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_next_action.py'
        spec=importlib.util.spec_from_file_location('current_native_next_action',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        path=Path(os.environ['SGP_R4_ROM_DIR'])/(os.environ.get('SGP_R4_ROM_NOME','r4-%s.nds')%language)
        model=module.F.G.S.SHARED.read_current(path,language)
        return module,model,module.D.C.resources(path,model)

    def test_native_dispatch_and_full_fight_input_initialize_the_remaining_actor(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language)
            for variant,turn_order in (('current',[1,0,2,3]),('reverse_speed',[0,1,2,3])):
                result=m.NextCPU(x,data,fixture_variant=variant).observe_next();m.require_next(result)
                self.assertEqual(result['final']['attacker'],0);self.assertEqual(result['final']['target'],1)
                self.assertEqual(result['final']['turn_order'],turn_order)
                self.assertEqual(result['final']['order'],[1,0,2,3])
                self.assertEqual(result['final']['action_failures'],[0,64])
                self.assertEqual(result['final']['seed'],result['before']['seed'])

    def test_direct_late_handler_has_same_command_but_stale_attacker(self):
        for language in ('EN','IT'):
            m,x,data=self.load(language);result=m.NextCPU(x,data,fixture_variant='late_pending').observe_next()
            self.assertEqual(result['final']['command'],23)
            self.assertEqual(result['final']['attacker'],1);self.assertEqual(result['final']['target'],0)
            self.assertIsNone(result['fight'])
            result['fixture_variant']='current';result['pending_command']=13
            with self.assertRaises(ValueError):m.require_next(result)

    def test_command23_cannot_hide_missing_target_return_or_wrong_math(self):
        import copy
        m,x,data=self.load('EN');result=m.NextCPU(x,data).observe_next();m.require_next(result)
        for field in ('attacker','target','move','move_temp','battlers_on_field','seed'):
            changed=copy.deepcopy(result);changed['final'][field]^=1
            with self.subTest(field=field),self.assertRaises(ValueError):m.require_next(changed)
        for pc in ('0x224a9cc','0x224aacc'):
            changed=copy.deepcopy(result);next(w for w in changed['fight']['writes'] if w['pc']==pc)['value']^=1
            with self.subTest(pc=pc),self.assertRaises(ValueError):m.require_next(changed)
        changed=copy.deepcopy(result);changed['fight']['code']=[r for r in changed['fight']['code'] if r['ram']!='0x224aad6']
        with self.assertRaises(ValueError):m.require_next(changed)
        changed=copy.deepcopy(result);changed['selection']['division_calls'][0]['quotient']-=1
        with self.assertRaises(ValueError):m.require_next(changed)
        changed=copy.deepcopy(result);changed['selection']['sort_calls'][0]['value']=0
        with self.assertRaises(ValueError):m.require_next(changed)
        changed=copy.deepcopy(result);changed['selection']['writes']=[w for w in changed['selection']['writes'] if w['pc']!='0x2252da4']
        with self.assertRaises(ValueError):m.require_next(changed)
        changed=copy.deepcopy(result);changed['selected']['turn_order']=[0,1,2,3]
        with self.assertRaises(ValueError):m.require_next(changed)

    def test_new_native_pins_and_signed_divider_refuse_drift(self):
        m,x,data=self.load('EN')
        for address in [a for a,_,_ in m.WINDOWS]+[m.F.G.S.DIV]:
            changed=dict(x)
            if address<m.F.U.OVERLAY_BASE:
                segments=[]
                for base,raw in x['segments']:
                    image=bytearray(raw)
                    if base<=address<base+len(raw):image[address-base]^=1
                    segments.append((base,bytes(image)))
                changed['segments']=segments
            else:
                image=bytearray(x['overlay']);image[address-m.F.U.OVERLAY_BASE]^=1;changed['overlay']=bytes(image)
            with self.subTest(address=hex(address)),self.assertRaises(ValueError):m.NextCPU(changed,data)
        for variant in (True,0,'ambiguous'):
            with self.assertRaises(ValueError):m.NextCPU(x,data,fixture_variant=variant)

    def test_native_order_loop_guard_refuses_a_third_row_or_wrong_store(self):
        m,x,data=self.load('EN');cpu=m.NextCPU(x,data);cpu.select_phase=True;cpu.current=dict(writes=[])
        cpu.uc.reg_write(m.UC_ARM_REG_PC,0x02252D56)
        for index,offset,width,value in ((2,2,1,2),(0,-1,1,0),(0,0,4,0),(0,0,1,1)):
            cpu.uc.reg_write(m.UC_ARM_REG_R2,index)
            with self.subTest(index=index,offset=offset,width=width,value=value),self.assertRaises(ValueError):
                cpu._write(cpu.uc,0,m.CTX+0x21EC+offset,width,value,None)


class NextActionAttributionCLI(unittest.TestCase):
    def test_json_preserves_each_input_and_its_aliases(self):
        import importlib.util,sys
        from unittest.mock import patch
        p=Path(__file__).resolve().parents[1]/'features/type-consumers/tools/attribuisci_next_action.py'
        spec=importlib.util.spec_from_file_location('next_action_cli',p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as work:
            root=Path(work);inputs=[root/(name+'.nds') for name in ('rom','v4','base','retail')]
            for path in inputs:path.write_bytes(b'preserve input')
            for path in inputs:
                symbolic=root/(path.stem+'-symbolic.nds');symbolic.symlink_to(path)
                hard=root/(path.stem+'-hard.nds');__import__('os').link(path,hard)
                for output in (path,symbolic,hard):
                    argv=['next-action','--language','EN','--json',str(output)]
                    for name,value in zip(('rom','v4','base','retail'),inputs):argv.extend(('--'+name,str(value)))
                    with self.subTest(output=output.name),patch.object(sys,'argv',argv),patch.object(module,'analyze') as analyze:
                        with self.assertRaises(SystemExit) as caught:module.main()
                        self.assertEqual(caught.exception.code,2);analyze.assert_not_called()
                        self.assertEqual(path.read_bytes(),b'preserve input')


if __name__ == '__main__':
    unittest.main()
