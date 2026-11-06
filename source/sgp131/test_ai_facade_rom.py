"""Class B reproducer for the Expert Facade trainer-AI battler bug.

The test authenticates the exact EN/IT V4 candidates and executes their real
overlay-10 trainer-AI interpreter against the command sequence stored in
member 0 of ``a/0/9/9``.  The isolated sequence is the same one reached by
Expert_CheckPower for Facade; no Python reimplementation decides its score.
"""
import struct
import unittest

import ndspy.narc
import ndspy.rom

from . import ai_scoring as ai
from . import rematches
from .test_ai_water_spout_rom import (
    WaterSpoutBench,
    artifacts,
    exact_input,
    unicorn_works,
)


FACADE = 263
POISON = 0x08
BURN = 0x10
PARALYSIS = 0x40
BAD_POISON = 0x80
SLEEP = 0x01
FREEZE = 0x20


class FacadeReachabilityTests(unittest.TestCase):
    def test_plus_falkner_variants_give_expert_ai_facade_and_flame_orb(self):
        for language in ('EN', 'IT'):
            raw = exact_input(self, language)
            rom = ndspy.rom.NintendoDSRom(raw)
            headers = ndspy.narc.NARC(rom.getFileByName('a/0/5/5')).files
            header = bytes(headers[712])
            self.assertEqual(struct.unpack_from('<I', header, 12)[0], 7)

            config = rematches.configuration(raw)
            trainer, kind, _base, variant_a, variant_b = struct.unpack_from(
                '<5H', config, 20)
            self.assertEqual((trainer, kind), (712, 0x0306))
            for label, offset in (('A', variant_a), ('B', variant_b)):
                with self.subTest(language=language, variant=label):
                    swellow = rematches.decode_party(config[offset:offset + 108])[2]
                    self.assertEqual((swellow['species'], swellow['item']), (277, 273))
                    self.assertIn(FACADE, swellow['moves'])


class FacadeRomTests(unittest.TestCase):
    def setUp(self):
        if not unicorn_works():
            self.skipTest('local Unicorn engine SIGILLs before guest execution')

    def bench(self, language, member=None):
        raw, overlay, original = artifacts(self, language)
        self.assertEqual(
            struct.unpack_from('<7i', original, ai.FACADE_CONTEXT_OFFSET),
            (10, 0, 0xD8, 2, 4, 1, 77))
        return WaterSpoutBench(
            raw, overlay, original if member is None else member,
            faster=False, script_offset=ai.FACADE_CONTEXT_OFFSET)

    def test_current_sequence_wrongly_follows_the_target_status(self):
        for language in ('EN', 'IT'):
            bench = self.bench(language)
            for status in (POISON, BAD_POISON, BURN, PARALYSIS):
                with self.subTest(language=language, status=status,
                                  affected='attacker'):
                    self.assertEqual(bench.run(
                        attacker_hp=100, target_hp=100,
                        attacker_status=status, target_status=0,
                        move=FACADE)['score'], 100)
                with self.subTest(language=language, status=status,
                                  affected='target'):
                    self.assertEqual(bench.run(
                        attacker_hp=100, target_hp=100,
                        attacker_status=0, target_status=status,
                        move=FACADE)['score'], 101)

    def test_single_token_fix_follows_the_move_user(self):
        for language in ('EN', 'IT'):
            raw, overlay, original = artifacts(self, language)
            fixed, report = ai.patch_facade_member(original)
            self.assertEqual(report['changed_offsets'], [ai.FACADE_SITE])
            bench = WaterSpoutBench(
                raw, overlay, fixed, faster=False,
                script_offset=ai.FACADE_CONTEXT_OFFSET)
            for status in (POISON, BAD_POISON, BURN, PARALYSIS):
                with self.subTest(language=language, status=status,
                                  affected='attacker'):
                    self.assertEqual(bench.run(
                        attacker_hp=100, target_hp=100,
                        attacker_status=status, target_status=0,
                        move=FACADE)['score'], 101)
                with self.subTest(language=language, status=status,
                                  affected='target'):
                    self.assertEqual(bench.run(
                        attacker_hp=100, target_hp=100,
                        attacker_status=0, target_status=status,
                        move=FACADE)['score'], 100)

    def test_status_mask_still_excludes_sleep_and_freeze(self):
        raw, overlay, original = artifacts(self, 'EN')
        fixed, _ = ai.patch_facade_member(original)
        bench = WaterSpoutBench(
            raw, overlay, fixed, faster=False,
            script_offset=ai.FACADE_CONTEXT_OFFSET)
        for status in (SLEEP, FREEZE):
            with self.subTest(status=status):
                result = bench.run(
                    attacker_hp=100, target_hp=100,
                    attacker_status=status, target_status=0,
                    move=FACADE)
                self.assertEqual(result['score'], 100)
                self.assertEqual(result['state'], 2)
                self.assertEqual(result['slot'], 4)


if __name__ == '__main__':
    unittest.main()
