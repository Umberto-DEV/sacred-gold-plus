"""Class B reproducer for the unreachable Expert_Thunder trainer-AI branch."""
import struct
import unittest

import ndspy.narc
import ndspy.rom

from . import ai_scoring as ai
from .test_ai_water_spout_rom import (
    WaterSpoutBench,
    artifacts,
    exact_input,
    unicorn_works,
)


EXPERT_MAIN = 0x27C8
THUNDER_ROUTINE = 0x58A4
THUNDER, THUNDER_EFFECT = 87, 152
SOLAR_BEAM, SOLAR_BEAM_EFFECT = 76, 151
THUNDERBOLT, THUNDERBOLT_EFFECT = 85, 6
CLEAR, RAIN, SUN = 0, 1, 1 << 4
EXPERT_THUNDER_TRAINERS = (255, 260, 526, 532, 604, 695, 722)


class ThunderReachabilityTests(unittest.TestCase):
    def test_seven_real_trainers_have_expert_ai_and_thunder(self):
        sizes = (8, 16, 10, 18)
        move_offsets = (None, 6, None, 8)
        for language in ('EN', 'IT'):
            raw = exact_input(self, language)
            rom = ndspy.rom.NintendoDSRom(raw)
            headers = ndspy.narc.NARC(rom.getFileByName('a/0/5/5')).files
            parties = ndspy.narc.NARC(rom.getFileByName('a/0/5/6')).files
            for trainer in EXPERT_THUNDER_TRAINERS:
                header = bytes(headers[trainer])
                kind, count = header[0], header[3]
                self.assertEqual(struct.unpack_from('<I', header, 12)[0] & 4, 4)
                self.assertIn(kind, (1, 3))
                record_size, move_offset = sizes[kind], move_offsets[kind]
                party = bytes(parties[trainer])
                self.assertEqual(len(party), record_size * count)
                moves = [struct.unpack_from('<4H', party,
                         slot * record_size + move_offset)
                         for slot in range(count)]
                self.assertTrue(any(THUNDER in row for row in moves),
                                (language, trainer))


class ThunderRomTests(unittest.TestCase):
    def setUp(self):
        if not unicorn_works():
            self.skipTest('local Unicorn engine SIGILLs before guest execution')

    def bench(self, language, member=None):
        raw, overlay, original = artifacts(self, language)
        self.assertEqual(
            struct.unpack_from('<15i', original,
                               ai.THUNDER_DISPATCH_CONTEXT_OFFSET),
            (47, 144, 2721, 47, 145, 2814, 47, 151, 2811,
             47, 151, 2855, 47, 155, 2878))
        self.assertEqual(
            struct.unpack_from('<25i', original, ai.THUNDER_ROUTINE_OFFSET),
            (43, 0, 17, 43, 20, 14, 43, 10, 11, 46, 19, 1, 7,
             20, 2, 9, 4, 1, 76, 5, 0, 50, 2, 4, -3))
        return WaterSpoutBench(raw, overlay,
                               original if member is None else member,
                               faster=False, script_offset=EXPERT_MAIN)

    @staticmethod
    def exercise(bench, move, effect, weather=CLEAR, random_value=50):
        result = bench.run(
            attacker_hp=100, target_hp=100, move=move,
            move_effect=effect, field_condition=weather,
            random_value=random_value)
        result['reached_thunder'] = any(
            offset == THUNDER_ROUTINE for offset, _ in result['script_reads'])
        return result

    def test_current_dispatch_never_reaches_the_intact_thunder_routine(self):
        for language in ('EN', 'IT'):
            result = self.exercise(self.bench(language), THUNDER,
                                   THUNDER_EFFECT, RAIN)
            with self.subTest(language=language):
                self.assertFalse(result['reached_thunder'])
                self.assertEqual((result['score'], result['state'],
                                  result['slot']), (100, 2, 4))

    def test_single_effect_fix_reaches_thunder_and_preserves_controls(self):
        cases = (
            ('Thunder clear', THUNDER, THUNDER_EFFECT, CLEAR, 50, 100),
            ('Thunder rain', THUNDER, THUNDER_EFFECT, RAIN, 50, 101),
            ('Thunder sun rng49', THUNDER, THUNDER_EFFECT, SUN, 49, 100),
            ('Thunder sun rng50', THUNDER, THUNDER_EFFECT, SUN, 50, 97),
            ('SolarBeam sun', SOLAR_BEAM, SOLAR_BEAM_EFFECT, SUN, 50, 102),
            ('Thunderbolt rain', THUNDERBOLT, THUNDERBOLT_EFFECT, RAIN, 50, 100),
        )
        for language in ('EN', 'IT'):
            raw, overlay, original = artifacts(self, language)
            fixed, report = ai.patch_thunder_member(original)
            self.assertEqual(report['changed_offsets'],
                             [ai.THUNDER_DISPATCH_SITE])
            bench = WaterSpoutBench(raw, overlay, fixed, faster=False,
                                    script_offset=EXPERT_MAIN)
            for name, move, effect, weather, random_value, score in cases:
                result = self.exercise(bench, move, effect, weather,
                                       random_value)
                with self.subTest(language=language, case=name):
                    self.assertEqual(result['score'], score)
                    self.assertEqual((result['state'], result['slot']), (2, 4))
                    self.assertEqual(result['reached_thunder'], move == THUNDER)


if __name__ == '__main__':
    unittest.main()
