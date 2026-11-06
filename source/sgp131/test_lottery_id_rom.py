"""Exact-candidate reproduction of the HGSS persisted Lottery Number defect."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

from sgp12.rom import Arm9, bl_decode
from . import lottery_id as L, mechanics_stages as stages


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}
SETTER = 0x02066CAC
SET_VAR = 0x02066A7C
ROLL = 0x02066CF4
RANDOM = 0x0201FD44
LO, HI = 0x403C, 0x403D


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), V4[language])
    return data


class SetterBench:
    """Bounded Thumb-1 executor for the exact 30-byte retail setter."""
    def __init__(self, rom):
        self.arm = Arm9.from_bytes(rom)

    def run(self, value, lo=0xA5A5, hi=0x5A5A):
        registers = [0] * 16
        registers[0], registers[1] = 0x02200000, value
        variables = {LO: lo, HI: hi}
        pc = SETTER
        for _ in range(24):
            op = int.from_bytes(self.arm.leggi(pc, 2), 'little')
            if op & 0xFF00 == 0xBD00:  # pop {...,pc}: bounded return
                return variables
            if op & 0xFF00 == 0xB500:  # push: no callee observes this stack
                pc += 2
                continue
            if op & 0xFE00 == 0x1C00:  # adds Rd,Rn,#imm3
                rd, rn, imm = op & 7, (op >> 3) & 7, (op >> 6) & 7
                registers[rd] = (registers[rn] + imm) & 0xFFFFFFFF
                pc += 2
                continue
            if op & 0xF800 in (0x0000, 0x0800):  # lsls/lsrs immediate
                rd, rs, amount = op & 7, (op >> 3) & 7, (op >> 6) & 0x1F
                registers[rd] = ((registers[rs] << amount) if op & 0x0800 == 0
                                 else (registers[rs] >> (amount or 32))) & 0xFFFFFFFF
                pc += 2
                continue
            if op & 0xF800 == 0x4800:  # ldr literal
                rd, offset = (op >> 8) & 7, (op & 0xFF) * 4
                literal = ((pc + 4) & ~3) + offset
                registers[rd] = int.from_bytes(self.arm.leggi(literal, 4), 'little')
                pc += 2
                continue
            if op & 0xF800 == 0xF000:
                encoded = self.arm.leggi(pc, 4)
                target = bl_decode(pc, encoded)
                if target != SET_VAR:
                    raise AssertionError('unexpected BL target %#x at %#x' % (target, pc))
                if registers[1] not in variables:
                    raise AssertionError('setter wrote unexpected variable %#x' % registers[1])
                variables[registers[1]] = registers[2] & 0xFFFF
                pc += 4
                continue
            raise AssertionError('unsupported Thumb opcode %#06x at %#x' % (op, pc))
        raise AssertionError('setter did not return within the instruction budget')


class RollBench:
    """Execute the real daily two-roll composition and delegate its real setter bytes."""
    def __init__(self, rom):
        self.rom = rom
        self.arm = Arm9.from_bytes(rom)

    def run(self, low_roll, high_roll, lo=0xA5A5, hi=0x5A5A):
        registers = [0] * 16
        registers[0] = 0x02200000
        rolls = [low_roll, high_roll]
        pc = ROLL
        for _ in range(20):
            op = int.from_bytes(self.arm.leggi(pc, 2), 'little')
            if op & 0xFF00 == 0xBD00:
                self.assertEqual(rolls, [])
                raise AssertionError('daily roll returned before calling the setter')
            if op & 0xFF00 == 0xB500:
                pc += 2
                continue
            if op & 0xFE00 == 0x1C00:
                rd, rn, imm = op & 7, (op >> 3) & 7, (op >> 6) & 7
                registers[rd] = (registers[rn] + imm) & 0xFFFFFFFF
                pc += 2
                continue
            if op & 0xF800 == 0x0000:
                rd, rs, amount = op & 7, (op >> 3) & 7, (op >> 6) & 0x1F
                registers[rd] = (registers[rs] << amount) & 0xFFFFFFFF
                pc += 2
                continue
            if op & 0xFFC0 == 0x4300:
                rdn, rm = op & 7, (op >> 3) & 7
                registers[rdn] = (registers[rdn] | registers[rm]) & 0xFFFFFFFF
                pc += 2
                continue
            if op & 0xF800 == 0xF000:
                target = bl_decode(pc, self.arm.leggi(pc, 4))
                if target == RANDOM:
                    if not rolls:
                        raise AssertionError('daily roll consumed more than two RNG values')
                    registers[0] = rolls.pop(0)
                elif target == SETTER:
                    if rolls:
                        raise AssertionError('daily roll called setter before consuming both RNG values')
                    return SetterBench(self.rom).run(registers[1], lo, hi)
                else:
                    raise AssertionError('unexpected daily-roll BL target %#x' % target)
                pc += 4
                continue
            raise AssertionError('unsupported daily-roll opcode %#06x at %#x' % (op, pc))
        raise AssertionError('daily roll did not reach setter within the instruction budget')

    @staticmethod
    def assertEqual(left, right):
        if left != right:
            raise AssertionError('%r != %r' % (left, right))


class LotteryIdCandidate(unittest.TestCase):
    def test_retail_overwrites_lo_twice_and_repair_writes_both_halves(self):
        cases = (
            (0x00000000, 0x0000, 0x0000),
            (0x00000001, 0x0001, 0x0000),
            (0x00010000, 0x0000, 0x0001),
            (0x12345678, 0x5678, 0x1234),
            (0xFFFF0000, 0x0000, 0xFFFF),
            (0xFFFFFFFF, 0xFFFF, 0xFFFF),
        )
        for language in V4:
            before = candidate(self, language)
            retail = SetterBench(before)
            for value, _low, high in cases:
                with self.subTest(language=language, phase='retail', value=hex(value)):
                    self.assertEqual(retail.run(value), {LO: high, HI: 0x5A5A})
            try:
                after, _receipt = L.apply(before, language)
            except NotImplementedError as error:
                self.fail(str(error))
            repaired = SetterBench(after)
            for value, low, high in cases:
                with self.subTest(language=language, phase='repaired', value=hex(value)):
                    self.assertEqual(repaired.run(value), {LO: low, HI: high})

    def test_daily_roll_preserves_both_rng_halves_after_repair(self):
        cases = ((0x1357, 0x2468), (0x0000, 0xFFFF), (0xFFFF, 0x0000))
        for language in V4:
            before = candidate(self, language)
            after, _receipt = L.apply(before, language)
            for low, high in cases:
                with self.subTest(language=language, phase='retail', low=low, high=high):
                    self.assertEqual(RollBench(before).run(low, high),
                                     {LO: high, HI: 0x5A5A})
                with self.subTest(language=language, phase='repaired', low=low, high=high):
                    self.assertEqual(RollBench(after).run(low, high),
                                     {LO: low, HI: high})

    def test_patch_is_one_halfword_and_receipt_is_exact(self):
        expected_keys = {
            'schema', 'stage', 'language', 'input_sha256', 'output_sha256',
            'setter_address', 'patch_address', 'preimage_sha256',
            'postimage_sha256', 'old_literal_address', 'high_literal_address',
            'low_variable', 'high_variable', 'save_layout_unchanged',
            'rom_geometry_unchanged', 'verification',
        }
        for language in V4:
            before = candidate(self, language)
            after, receipt = L.apply(before, language)
            changed = [index for index, pair in enumerate(zip(before, after))
                       if pair[0] != pair[1]]
            arm = Arm9.from_bytes(before)
            offset = arm.off(L.PATCH, 2)
            self.assertEqual(changed, [offset])
            self.assertEqual(before[offset:offset + 2], L.PATCH_PREIMAGE)
            self.assertEqual(after[offset:offset + 2], L.PATCH_POSTIMAGE)
            self.assertEqual(L.spans(before), ((offset, offset + 2),))
            self.assertEqual(set(receipt), expected_keys)
            self.assertEqual(receipt['verification']['patch_bytes'], 2)
            self.assertEqual(receipt['verification']['changed_bytes'], 1)
            self.assertEqual(L.verify(before, after, receipt), receipt['verification'])
            self.assertEqual(len(after), len(before))

    def test_foreign_preimages_reapplication_and_wrong_language_are_refused(self):
        before = candidate(self, 'EN')
        after, _receipt = L.apply(before, 'EN')
        with self.assertRaisesRegex(ValueError, 'preimage differs'):
            L.apply(after, 'EN')
        with self.assertRaisesRegex(ValueError, 'language anchor'):
            L.apply(before, 'IT')
        mutated = bytearray(before)
        mutated[Arm9.from_bytes(before).off(L.SETTER, 1)] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage differs'):
            L.apply(bytes(mutated), 'EN')

        after_bag, _receipt = stages.run_stage(
            'bag-view-position', before, 'EN', invariants=lambda *_args: None)
        out_of_context = bytearray(after_bag)
        out_of_context[0x200] ^= 1
        with self.assertRaisesRegex(ValueError, 'language anchor'):
            L.apply(bytes(out_of_context), 'IT')
        anchor = bytearray(after_bag)
        fat = struct.unpack_from('<I', anchor, 0x48)[0]
        start, _end = struct.unpack_from('<II', anchor, fat + 8 * 137)
        anchor[start] ^= 1
        with self.assertRaisesRegex(ValueError, 'language anchor'):
            L.apply(bytes(anchor), 'EN')

    def test_verifier_rejects_out_of_span_bytes_and_receipt_mutants(self):
        before = candidate(self, 'IT')
        after, receipt = L.apply(before, 'IT')
        outside = bytearray(after)
        outside[0x200] ^= 1
        with self.assertRaisesRegex(ValueError, 'outside declared'):
            L.verify(before, bytes(outside), receipt)
        extra = dict(receipt)
        extra['untrusted'] = True
        with self.assertRaisesRegex(ValueError, 'receipt identity'):
            L.verify(before, after, extra)
        missing = dict(receipt)
        missing.pop('high_variable')
        with self.assertRaisesRegex(ValueError, 'receipt identity'):
            L.verify(before, after, missing)
        unsealed = dict(receipt)
        unsealed.pop('verification')
        with self.assertRaisesRegex(ValueError, 'receipt identity'):
            L.verify(before, after, unsealed)

    def test_mechanics_wrapper_declares_the_halfword_and_one_changed_byte(self):
        for language in V4:
            before = candidate(self, language)
            after, receipt = stages.run_stage(
                'lottery-id', before, language, invariants=lambda *_args: None)
            offset = Arm9.from_bytes(before).off(L.PATCH, 2)
            self.assertEqual(receipt['regions'], [{
                'start': offset, 'end': offset + 2,
                'label': 'Lottery Number high-half destination'}])
            self.assertEqual(receipt['changed_ranges'], [[offset, offset + 1]])
            self.assertEqual(receipt['stage_receipt']['verification']['patch_bytes'], 2)
            self.assertEqual(receipt['stage_receipt']['verification']['changed_bytes'], 1)
            self.assertEqual(after[offset:offset + 2], L.PATCH_POSTIMAGE)

    def test_stage_composes_after_the_bag_view_repair_in_both_languages(self):
        for language in V4:
            base = candidate(self, language)
            after_bag, _bag_receipt = stages.run_stage(
                'bag-view-position', base, language, invariants=lambda *_args: None)
            final, receipt = stages.run_stage(
                'lottery-id', after_bag, language, invariants=lambda *_args: None)
            offset = Arm9.from_bytes(base).off(L.PATCH, 2)
            self.assertEqual(receipt['changed_ranges'], [[offset, offset + 1]])
            restored = bytearray(final)
            restored[offset:offset + 2] = after_bag[offset:offset + 2]
            self.assertEqual(bytes(restored), after_bag)

    def test_chain_replay_binds_lottery_receipts_to_the_baseline_language(self):
        base = candidate(self, 'EN')
        after_bag, bag_receipt = stages.run_stage(
            'bag-view-position', base, 'EN', invariants=lambda *_args: None)
        final, lottery_receipt = stages.run_stage(
            'lottery-id', after_bag, 'EN', invariants=lambda *_args: None)
        for mutation in ('wrapper', 'nested', 'both'):
            forged = json.loads(json.dumps([bag_receipt, lottery_receipt]))
            if mutation in ('wrapper', 'both'):
                forged[1]['language'] = 'IT'
            if mutation in ('nested', 'both'):
                forged[1]['stage_receipt']['language'] = 'IT'
                forged[1]['stage_receipt_sha256'] = stages._sha(
                    stages.canonical(forged[1]['stage_receipt']))
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'language'):
                stages.verify_chain(
                    base, final, ['bag-view-position', 'lottery-id'], forged,
                    lambda _image: {}, invariants=lambda *_args: None)


if __name__ == '__main__':
    unittest.main()
