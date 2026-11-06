"""Exact-candidate regression tests for HG-B09 Battle Tower round truncation."""
import hashlib
from pathlib import Path
import unittest

from sgp12.rom import Arm9
from . import battle_tower_wrap as B, mechanics_stages as stages


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), V4[language])
    return data


class BattleTowerWrapTests(unittest.TestCase):
    def test_four_narrowing_halfwords_are_replaced_and_nothing_else(self):
        for language in V4:
            before = candidate(self, language)
            after, receipt = B.apply(before, language)
            old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
            with self.subTest(language=language, seam='multi'):
                self.assertEqual(old.leggi(B.MULTI_TRUNCATE, 4), B.MULTI_PREIMAGE)
                self.assertEqual(new.leggi(B.MULTI_TRUNCATE, 4), B.MULTI_POSTIMAGE)
            with self.subTest(language=language, seam='single'):
                self.assertEqual(old.leggi(B.SINGLE_SPAN, 6), B.SINGLE_PREIMAGE)
                self.assertEqual(new.leggi(B.SINGLE_SPAN, 6), B.SINGLE_POSTIMAGE)
            expected = bytearray(before)
            for address, _preimage, postimage in B.PATCHES:
                at = old.off(address, len(postimage))
                expected[at:at + len(postimage)] = postimage
            self.assertEqual(after, bytes(expected))
            self.assertEqual(B.verify(before, after, receipt), receipt['verification'])
            self.assertEqual(B.spans(before), tuple((old.off(address, len(post)),
                                                     old.off(address, len(post)) + len(post))
                                                    for address, _pre, post in B.PATCHES))

    def test_repair_passes_full_width_rounds_and_preserves_low_rounds(self):
        def multi_argument(round_value, fixed):
            return round_value if fixed else round_value & 0xFF

        def single_argument(round_value, fixed):
            return round_value if fixed else round_value & 0xFF

        for round_value in (0, 1, 2, 6, 7, 255, 256, 257, 258, 262,
                            263, 511, 512, 65534):
            with self.subTest(round=round_value):
                self.assertEqual(multi_argument(round_value, True), round_value)
                self.assertEqual(single_argument(round_value, True), round_value)
                self.assertEqual(multi_argument(round_value, False), round_value & 0xFF)
                self.assertEqual(single_argument(round_value, False), round_value & 0xFF)
                if round_value <= 255:
                    self.assertEqual(multi_argument(round_value, False),
                                     multi_argument(round_value, True))
                else:
                    self.assertNotEqual(multi_argument(round_value, False),
                                        multi_argument(round_value, True))

    def test_receipt_reapply_language_and_mutants_fail_closed(self):
        before = candidate(self, 'EN')
        after, receipt = B.apply(before, 'EN')
        self.assertEqual(receipt['stage'], 'battle-tower-wrap')
        self.assertEqual(receipt['changed_halfwords'], 4)
        self.assertEqual(receipt['save_layout_unchanged'], True)
        with self.assertRaisesRegex(ValueError, 'preimage differs'):
            B.apply(after, 'EN')
        with self.assertRaisesRegex(ValueError, 'language anchor'):
            B.apply(before, 'IT')
        for address, _preimage, _postimage in B.PATCHES:
            mutant = bytearray(before)
            arm = Arm9.from_bytes(before)
            mutant[arm.off(address, 1)] ^= 1
            with self.subTest(mutant=hex(address)), self.assertRaisesRegex(
                    ValueError, 'preimage differs'):
                B.apply(bytes(mutant), 'EN')
        forged = dict(receipt)
        forged['changed_halfwords'] = 3
        with self.assertRaisesRegex(ValueError, 'receipt identity'):
            B.verify(before, after, forged)

    def test_registered_stage_composes_after_lottery_on_real_en_it(self):
        for language in V4:
            before = candidate(self, language)
            after_lottery, lottery_receipt = stages.run_stage(
                'lottery-id', before, language, invariants=lambda *_args: None)
            final, tower_receipt = stages.run_stage(
                'battle-tower-wrap', after_lottery, language,
                invariants=lambda *_args: None)
            with self.subTest(language=language):
                self.assertEqual(lottery_receipt['stage'], 'lottery-id')
                self.assertEqual(tower_receipt['stage'], 'battle-tower-wrap')
                self.assertEqual(tower_receipt['stage_receipt']['stage'],
                                 'battle-tower-wrap')
                self.assertEqual(tower_receipt['changed_ranges'],
                                 [list(span) for span in
                                  stages.changed_ranges(after_lottery, final)])
                self.assertEqual(
                    B.verify(after_lottery, final, tower_receipt['stage_receipt']),
                    tower_receipt['stage_receipt']['verification'])


if __name__ == '__main__':
    unittest.main()
