"""Class B: install and independently read SG-AI01 on exact V4 EN/IT bytes.

All work is in memory.  The authenticated source ROMs are read-only and no
patched ROM or save is written.
"""
import copy
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from sgp12.rom import Arm9, Rom
from sgp131 import baseline
from sgp131 import fairy_ai as stage
from sgp131 import transform_reload
from sgp131 import type_consumers


ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    'EN': ROOT / 'local/experiments/balance493-2026-10-28/candidate-v4-EN.nds',
    'IT': ROOT / 'local/experiments/balance493-2026-10-28/candidate-v4-IT.nds',
}
_CACHE = {}


def source(language):
    path = INPUTS[language]
    if not path.is_file():
        raise unittest.SkipTest('private V4 %s input unavailable' % language)
    data = path.read_bytes()
    if baseline.identify(data) != language:
        raise AssertionError('private V4 %s identity differs' % language)
    return data


def slot(data):
    row = stage.slot_contract(stage.DEFAULT_SLOT, stage.PAYLOAD_BYTES)
    at = stage._arm9_locate(stage._arm9_map(data), row['start'], row['bytes'])
    if data[at:at + row['bytes']] != bytes(row['bytes']):
        raise AssertionError('V4 Fairy slot is not the pinned zero preimage')
    return row


class InstalledFairyAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='fairy-ai-rom-')

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def installed(self, language):
        if language not in _CACHE:
            data = source(language)
            _CACHE[language] = (data, *stage.apply_code(
                data, language, Path(self.work.name), slot=slot(data)))
        return _CACHE[language]

    def test_en_it_install_is_in_place_and_verified(self):
        logical = []
        for language in ('EN', 'IT'):
            before, after, receipt = self.installed(language)
            self.assertEqual(len(before), len(after))
            checked = stage.verify_code(before, after, receipt)
            self.assertEqual(checked['payload_sha256'], stage.PAYLOAD_SHA256)
            self.assertEqual(
                checked['logical_changed_bytes'],
                9 + len(receipt['type_consumers']['logical']['changed_offsets'])
                + len(receipt['transform_reload']['logical']['changed_offsets']))
            self.assertTrue(checked['type_consumers']['ok'])
            self.assertTrue(checked['transform_reload']['ok'])
            self.assertTrue(checked['arm9_changed_only_in_slot'])
            logical.append(Rom(after).immagine_overlay(12)[2])
        self.assertEqual(logical[0], logical[1], 'overlay 12 is language-neutral')

    def test_receipt_and_out_of_region_mutants_are_refused(self):
        before, after, receipt = self.installed('EN')
        for mutant in (
                dict(receipt, input_sha256='0' * 64),
                dict(receipt, output_sha256='0' * 64),
                dict(receipt, slot=dict(receipt['slot'], start=stage.DEFAULT_SLOT + 4))):
            with self.assertRaises(ValueError):
                stage.verify_code(before, after, mutant)
        segments = stage._arm9_map(after)
        at = stage._arm9_locate(segments, stage.DEFAULT_SLOT - 1, 1)
        changed = bytearray(after)
        changed[at] ^= 1
        rewritten = copy.deepcopy(receipt)
        rewritten['output_sha256'] = hashlib.sha256(changed).hexdigest()
        with self.assertRaises(ValueError):
            stage.verify_code(before, bytes(changed), rewritten)

    def test_payload_and_both_overlay_seams_are_real_readback(self):
        for language in ('EN', 'IT'):
            before, after, receipt = self.installed(language)
            at = stage._arm9_locate(stage._arm9_map(after), stage.DEFAULT_SLOT,
                                    stage.PAYLOAD_BYTES)
            self.assertEqual(hashlib.sha256(after[at:at + stage.PAYLOAD_BYTES]).hexdigest(),
                             stage.PAYLOAD_SHA256)
            old = Rom(before).immagine_overlay(12)[2]
            new = Rom(after).immagine_overlay(12)[2]
            typed, _ = type_consumers.patch_overlay(
                old, new[type_consumers.CONVERSION_SITE - stage.OVERLAY_BASE:
                         type_consumers.CONVERSION_SITE - stage.OVERLAY_BASE +
                         type_consumers.CONVERSION_BYTES])
            reload_at = transform_reload.RELOAD_ADDRESS - stage.OVERLAY_BASE
            reloaded, _ = transform_reload.patch_overlay(
                typed, new[reload_at:reload_at + transform_reload.RELOAD_BYTES])
            expected, _ = stage.patch_overlay(reloaded, stage.DEFAULT_SLOT)
            self.assertEqual(new, expected)
            self.assertEqual(receipt['native']['bytes'], stage.PAYLOAD_BYTES)
            self.assertEqual(receipt['transform_reload']['native']['bytes'],
                             transform_reload.RELOAD_BYTES)

    def test_verifier_rejects_restored_branch_into_the_bl_suffix(self):
        from sgp12.overlay import applica

        before, after, receipt = self.installed('EN')
        mutant, _writer = applica(
            after, 12, [(0x02252138, bytes.fromhex('c8d1'))],
            [{'addr': 0x02252138, 'pre': bytes.fromhex('c8d1'),
              'post': bytes.fromhex('c6d1')}])
        rewritten = copy.deepcopy(receipt)
        rewritten['output_sha256'] = hashlib.sha256(mutant).hexdigest()
        with self.assertRaisesRegex(ValueError, 'decoded overlay differs'):
            stage.verify_code(before, mutant, rewritten)

    def test_transform_reload_is_installed_in_both_languages(self):
        for language in ('EN', 'IT'):
            before, after, receipt = self.installed(language)
            old = Rom(before).immagine_overlay(12)[2]
            new = Rom(after).immagine_overlay(12)[2]
            at = transform_reload.RELOAD_ADDRESS - stage.OVERLAY_BASE
            self.assertEqual(old[at:at + transform_reload.RELOAD_BYTES],
                             transform_reload.RELOAD_PREIMAGE)
            self.assertEqual(
                hashlib.sha256(new[at:at + transform_reload.RELOAD_BYTES]).hexdigest(),
                transform_reload.PAYLOAD_SHA256)
            self.assertEqual(
                receipt['transform_reload']['logical']['preserved_while_transformed'],
                ['atk', 'def', 'speed', 'sp_atk', 'sp_def'])

    def test_fire_fang_shadow_force_effect_is_installed_in_both_languages(self):
        for language in ('EN', 'IT'):
            before, after, _receipt = self.installed(language)
            old = Rom(before).immagine_overlay(12)[2]
            new = Rom(after).immagine_overlay(12)[2]
            at = type_consumers.FIRE_FANG_SITE - stage.OVERLAY_BASE
            self.assertEqual(old[at:at + 2], type_consumers.FIRE_FANG_PREIMAGE)
            self.assertEqual(new[at:at + 2], type_consumers.FIRE_FANG_REPLACEMENT)
            branch = type_consumers.FIRE_FANG_BRANCH_SITE - stage.OVERLAY_BASE
            self.assertEqual(old[branch:branch + 2],
                             type_consumers.FIRE_FANG_BRANCH_PREIMAGE)
            self.assertEqual(new[branch:branch + 2],
                             type_consumers.FIRE_FANG_BRANCH_PREIMAGE)
            context = type_consumers.FIRE_FANG_CONTEXT_ADDRESS - stage.OVERLAY_BASE
            expected = bytearray(type_consumers.FIRE_FANG_CONTEXT)
            relative = type_consumers.FIRE_FANG_SITE - type_consumers.FIRE_FANG_CONTEXT_ADDRESS
            expected[relative:relative + 2] = type_consumers.FIRE_FANG_REPLACEMENT
            self.assertEqual(new[context:context + len(expected)], bytes(expected))

    def test_rage_clears_only_its_own_status2_bit_in_both_languages(self):
        for language in ('EN', 'IT'):
            before, after, receipt = self.installed(language)
            old = Rom(before).immagine_overlay(12)[2]
            new = Rom(after).immagine_overlay(12)[2]
            function = type_consumers.RAGE_FUNCTION_ADDRESS - stage.OVERLAY_BASE
            self.assertEqual(
                hashlib.sha256(old[
                    function:function + type_consumers.RAGE_FUNCTION_BYTES
                ]).hexdigest(),
                type_consumers.RAGE_FUNCTION_SHA256)
            at = type_consumers.RAGE_SITE - stage.OVERLAY_BASE
            self.assertEqual(old[at:at + 2], type_consumers.RAGE_PREIMAGE)
            self.assertEqual(new[at:at + 2], type_consumers.RAGE_REPLACEMENT)
            self.assertEqual(
                receipt['type_consumers']['logical']['rage_status2'],
                {'address': type_consumers.RAGE_SITE,
                 'before': type_consumers.RAGE_PREIMAGE.hex(),
                 'after': type_consumers.RAGE_REPLACEMENT.hex(),
                 'rage_mask': 1 << 23,
                 'operation_before': 'status2 &= STATUS2_RAGE',
                 'operation_after': 'status2 &= ~STATUS2_RAGE'})
            context = type_consumers.RAGE_CONTEXT_ADDRESS - stage.OVERLAY_BASE
            expected = bytearray(type_consumers.RAGE_CONTEXT)
            relative = type_consumers.RAGE_SITE - type_consumers.RAGE_CONTEXT_ADDRESS
            expected[relative:relative + 2] = type_consumers.RAGE_REPLACEMENT
            self.assertEqual(new[context:context + len(expected)], bytes(expected))

    def test_conversion2_and_grounding_consumers_execute_the_fixed_bytes(self):
        from sgp131.test_type_chart import (DamageScenario, NativeDamage,
                                            IRON_BALL_EFFECT)
        # Fairy row 9*18+3 minus the two marker-owned Ghost cells = 163.
        fairy_poison_row = 163
        for language in ('EN', 'IT'):
            _before, after, _receipt = self.installed(language)
            conversion = Conversion2Native.Bench(after)
            changed, retail_rows = conversion.run(
                9, random_value=fairy_poison_row)
            damage = NativeDamage(after)
            with self.subTest(language=language, consumer='Conversion2'):
                self.assertEqual(changed, (3, 3))
                self.assertEqual(retail_rows, set(),
                                 'fixed Conversion2 must not read the retail chart')
            with self.subTest(language=language, consumer='Iron Ball'):
                self.assertEqual(
                    damage.run(DamageScenario(4, 2, item=IRON_BALL_EFFECT)),
                    (100, 0, (72,), ()))
            with self.subTest(language=language, consumer='Gravity'):
                self.assertEqual(
                    damage.run(DamageScenario(4, 2, gravity=True)),
                    (100, 0, (72,), ()))

    def test_verifier_rejects_noncanonical_overlay_footer(self):
        before, after, receipt = self.installed('IT')
        fat = struct.unpack_from('<I', after, 0x48)[0]
        y9 = struct.unpack_from('<I', after, 0x50)[0] + 32 * 12
        fid = struct.unpack_from('<8I', after, y9)[6]
        _start, end = struct.unpack_from('<II', after, fat + 8 * fid)
        changed = bytearray(after)
        changed[end - 8] ^= 1
        rewritten = copy.deepcopy(receipt)
        rewritten['output_sha256'] = hashlib.sha256(changed).hexdigest()
        with self.assertRaises(ValueError) as caught:
            stage.verify_code(before, bytes(changed), rewritten)
        self.assertNotIn('receipt', str(caught.exception))

    def test_composes_after_existing_ai_and_rejects_the_unsafe_reverse_order(self):
        from sgp131 import ai_scoring, type_chart

        before = source('EN')
        scored, scored_receipt = ai_scoring.apply(before, 'EN')
        ai_scoring.verify(before, scored, scored_receipt)
        charted, chart_receipt = type_chart.apply(scored, 'EN')
        type_chart.verify(scored, charted, chart_receipt)
        first, fairy_receipt = stage.apply_code(
            charted, 'EN', Path(self.work.name), slot=slot(charted))
        stage.verify_code(charted, first, fairy_receipt)

        fairy, fairy_first_receipt = stage.apply_code(
            before, 'EN', Path(self.work.name), slot=slot(before))
        stage.verify_code(before, fairy, fairy_first_receipt)
        with self.assertRaisesRegex(ValueError, '02252054'):
            ai_scoring.apply(fairy, 'EN')
        self.assertNotEqual(first, fairy, 'forward composition includes all three fixes')


class WholeEffectivenessLoop(unittest.TestCase):
    """Execute the outer type walk, including its backedge after the BL hook.

    Calling the resident helper in isolation misses branches into the second
    half of the replaced instruction pair. No game service is stubbed here.
    """

    def test_full_flags_walk_returns_once_with_correct_types_and_preserved_abi(self):
        try:
            from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
            from unicorn.arm_const import (
                UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)
        except ImportError as error:
            self.skipTest('unicorn is required: %s' % error)
        # Literal oracles from the ordinary and Fairy type chart. Flags are
        # SUPER_EFFECTIVE=2, NOT_VERY_EFFECTIVE=4, NO_EFFECT=8.
        cases = ((10, 10, 17, 4), (10, 15, 15, 2),
                 (11, 10, 10, 2), (10, 11, 11, 4),
                 (0, 7, 7, 8), (10, 15, 11, 0),
                 (9, 16, 16, 2), (17, 9, 9, 4),
                 (0, 0, 0, 0), (9, 17, 1, 2))
        regs = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)
        ctx, flags, stack, stop = 0x02350000, 0x02390000, 0x023B7000, 0x023FF000
        self.work = tempfile.TemporaryDirectory(prefix='fairy-loop-')
        with self.work:
            for language in ('EN', 'IT'):
                _before, after, _receipt = InstalledFairyAI.installed(self, language)
                for attack, type1, type2, expected in cases:
                    with self.subTest(language=language, types=(attack, type1, type2)):
                        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
                        uc.mem_map(0x02000000, 0x400000)
                        uc.mem_map(0x01FF8000, 0x8000)
                        uc.mem_map(0x027E0000, 0x20000)
                        arm = Arm9.from_bytes(after)
                        for address, offset, size in arm.segmenti:
                            uc.mem_write(address, bytes(arm.raw[offset:offset + size]))
                        uc.mem_write(stage.OVERLAY_BASE, Rom(after).immagine_overlay(12)[2])
                        # moveNo=1; Normal uses the zero-initialized move-data
                        # type when moveTypeDefault is zero. No abilities/items.
                        uc.mem_write(stack, struct.pack('<5I', 0, 0, type1, type2, flags))
                        values = [ctx, 1, attack, 0] + [0x44440000 + i for i in range(8)]
                        for reg, value in zip(regs, values):
                            uc.reg_write(reg, value)
                        uc.reg_write(UC_ARM_REG_SP, stack)
                        uc.reg_write(UC_ARM_REG_LR, stop | 1)
                        entries, split_entries = [], []

                        def observe(machine, address, size, unused):
                            if address == 0x023D746C:
                                entries.append(address)
                            if address == 0x022520C8:
                                split_entries.append(address)
                                machine.emu_stop()

                        uc.hook_add(UC_HOOK_CODE, observe)
                        uc.emu_start(0x02252055, stop, count=30000)
                        self.assertEqual(split_entries, [],
                                         'type loop entered the BL suffix at 022520C8')
                        self.assertEqual(uc.reg_read(UC_ARM_REG_PC), stop)
                        self.assertEqual(entries, [0x023D746C], 'hook must run only once')
                        self.assertEqual(struct.unpack('<I', uc.mem_read(flags, 4))[0], expected)
                        self.assertEqual(uc.reg_read(UC_ARM_REG_SP), stack)
                        self.assertEqual([uc.reg_read(reg) for reg in regs[4:12]], values[4:12])


class Conversion2Native(unittest.TestCase):
    """SG-AI02 preimage: execute the real Conversion2 command and row helper.

    Only services outside the command's concern are modelled.  The command at
    0x02240C98, GetTypeEffectivnessData at 0x0225260C, its ARM division helper
    and every retail table load execute from the authenticated V4 image.
    """

    BASE = 0x022378C0
    FUNCTION = 0x02240C98
    TABLE = 0x0226CC7C
    CTX = 0x02360000
    BS = 0x02350000
    STACK = 0x023B7000
    STOP = 0x023FF000
    SENTINEL = 0xA5A5A5A5
    STUBS = (0x0223BD98, 0x02245508, 0x022454E8,
             0x022527CC, 0x022525AC, 0x0224EDE0)

    class Bench:
        def __init__(self, data):
            try:
                from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_HOOK_MEM_READ
                from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                               UC_ARM_REG_R2, UC_ARM_REG_R3,
                                               UC_ARM_REG_R4, UC_ARM_REG_R5,
                                               UC_ARM_REG_R6, UC_ARM_REG_R7,
                                               UC_ARM_REG_R8, UC_ARM_REG_R9,
                                               UC_ARM_REG_R10, UC_ARM_REG_R11,
                                               UC_ARM_REG_SP, UC_ARM_REG_LR,
                                               UC_ARM_REG_PC)
            except ImportError as error:
                raise unittest.SkipTest('unicorn is required: %s' % error)
            self.regs = (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                         UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                         UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                         UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                         UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)
            (self.R0, self.R1, self.R2, self.R3, self.R4, self.R5,
             self.R6, self.R7, self.R8, self.R9, self.R10, self.R11,
             self.SP, self.LR, self.PC) = self.regs
            self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
            self.uc.mem_map(0x02000000, 0x400000)
            self.uc.mem_map(0x01FF8000, 0x4000)
            self.uc.mem_map(0x027E0000, 0x20000)
            arm = Arm9.from_bytes(data)
            for address, offset, size in arm.segmenti:
                self.uc.mem_write(address, bytes(arm.raw[offset:offset + size]))
            self.overlay = Rom(data).immagine_overlay(12)[2]
            self.uc.mem_write(Conversion2Native.BASE, self.overlay)
            self.uc.mem_write(0x021E5900, Rom(data).immagine_overlay(18)[2])
            for address in Conversion2Native.STUBS:
                self.uc.hook_add(UC_HOOK_CODE, self._stub, None, address, address)
            self.uc.hook_add(UC_HOOK_MEM_READ, self._table_read, None,
                             Conversion2Native.TABLE,
                             Conversion2Native.TABLE + 112 * 3 - 1)
            self.error = None

        def reg(self, register):
            return self.uc.reg_read(register)

        def ret(self, value=0):
            self.uc.reg_write(self.R0, value & 0xFFFFFFFF)
            self.uc.reg_write(self.PC, self.reg(self.LR))

        def _stub(self, uc, address, size, unused):
            try:
                if address == 0x0223BD98:              # BattleSystem_Random
                    self.ret(self.random_value)
                elif address == 0x0224EDE0:            # GetBattlerVar type1/type2
                    variable = self.reg(self.R2)
                    if (self.reg(self.R0), self.reg(self.R1), variable,
                            self.reg(self.R3)) != (Conversion2Native.CTX, 0, variable, 0) \
                            or variable not in (0x1B, 0x1C):
                        raise AssertionError('unexpected GetBattlerVar ABI')
                    self.ret(self.current_types[variable - 0x1B])
                else:
                    # State getter/setter, Multitype/ability and the unrelated
                    # precondition check are controls, not type-table logic.
                    self.ret(0)
            except Exception as error:
                self.error = error
                uc.emu_stop()

        def _table_read(self, uc, access, address, size, value, unused):
            self.rows.append((address - Conversion2Native.TABLE) // 3)

        def run(self, last_move_type, current_types=(0, 0), random_value=2):
            import struct
            self.current_types = tuple(current_types)
            self.random_value = random_value
            self.rows = []
            self.error = None
            c, u = Conversion2Native, self.uc
            u.mem_write(c.CTX, bytes(0x4000))
            u.mem_write(c.STACK - 0x1000, bytes(0x2000))
            u.mem_write(c.CTX + 0x64, struct.pack('<I', 0))
            u.mem_write(c.CTX + 0x30C4, struct.pack('<H', 1))
            u.mem_write(c.CTX + 0x30CC, struct.pack('<H', 0))
            u.mem_write(c.CTX + 0x30D4, struct.pack('<H', last_move_type))
            u.mem_write(c.CTX + 0x2DB0, struct.pack('<I', 0x1000))
            for register, value in ((self.R0, c.BS), (self.R1, c.CTX),
                                    (self.SP, c.STACK), (self.LR, c.STOP | 1)):
                u.reg_write(register, value)
            for register in (self.R4, self.R5, self.R6, self.R7,
                             self.R8, self.R9, self.R10, self.R11):
                u.reg_write(register, c.SENTINEL)
            u.emu_start(c.FUNCTION | 1, c.STOP, count=2_000_000)
            if self.error:
                raise self.error
            if self.reg(self.PC) & ~1 != c.STOP or self.reg(self.SP) != c.STACK:
                raise AssertionError('Conversion2 did not return with its ABI')
            if any(self.reg(register) != c.SENTINEL for register in
                   (self.R4, self.R5, self.R6, self.R7,
                    self.R8, self.R9, self.R10, self.R11)):
                raise AssertionError('Conversion2 changed a callee-saved register')
            return tuple(u.mem_read(c.CTX + 0x2D64, 2)), set(self.rows)

    def test_real_command_exhausts_retail_rows_but_cannot_choose_fairy_resistance(self):
        from sgp131 import type_chart

        logical = []
        for language in ('EN', 'IT'):
            data = source(language)
            bench = self.Bench(data)
            table_at = self.TABLE - self.BASE
            retail = [tuple(bench.overlay[table_at + 3 * i:table_at + 3 * i + 3])
                      for i in range(112)]
            modern, _trailer = type_chart.rows(type_chart.overlay(data))
            fairy_resists = sorted(defend for attack, defend, multiplier in modern
                                   if attack == 9 and multiplier <= 5)
            with self.subTest(language=language):
                self.assertEqual(fairy_resists, [3, 8, 10])
                self.assertFalse(any(attack == 9 for attack, _defend, _effect in retail),
                                 'retail helper unexpectedly contains a Fairy attack row')
                changed, rows = bench.run(9, random_value=2)
                self.assertEqual(changed, (0, 0),
                                 'current Conversion2 must expose the missing Fairy result')
                self.assertEqual(rows, set(range(112)),
                                 'the real command did not exhaust its retail domain')
                control, control_rows = bench.run(10, random_value=2)
                self.assertEqual(control, (10, 10),
                                 'Fire control must choose the row-2 resistance')
                self.assertEqual(control_rows, {2})
                logical.append(retail)
        self.assertEqual(logical[0], logical[1], 'Conversion2 retail table differs EN/IT')


if __name__ == '__main__':
    unittest.main()
