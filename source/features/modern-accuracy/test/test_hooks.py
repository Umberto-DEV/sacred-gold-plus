"""The installed seam inside the real accuracy check, before and after.

Each case runs BattleSystem_CheckMoveHit from its entry (boundaries listed in
accuracy_bench). Oracle: with an effective Keen Eye attacker, the patched hit
chance equals the unpatched one with the target's evasion stage at neutral;
every other case is identical to the unpatched function. Explicit counts from
the plan (33/100, 100/100, 75/100) pin absolute behaviour. Mutants must be
caught by the same checks after a green baseline.
"""
import itertools
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import accuracy_bench as bench
from unicorn import UcError
from test_native import TEST_ADDRESSES, load
from sgp131 import modern_abilities

STAGES = range(13)
KEEN_EYE, UNAWARE, SIMPLE = 51, 109, 86


def differential(baseline, patched, cases):
    """Return the first case violating the oracle, or None."""
    for case in cases:
        before = baseline.run(case, 0)[1]
        after = patched.run(case, 0)[1]
        attacker, target = case['attacker'], case['target']
        ability = case.get('abilities', {}).get(attacker, 0)
        suppressed = case.get('effect_flags', {}).get(attacker, 0) & bench.SUPPRESSED
        expected = before
        if ability == KEEN_EYE and not suppressed:
            neutral = dict(case, eva={**case.get('eva', {}), target: 6})
            expected = baseline.run(neutral, 0)[1]
        if not after['preserved'] or after['hit_chance'] != expected['hit_chance']:
            return case, expected['hit_chance'], after['hit_chance']
        rng = [c for c in after['calls'] if c[0] == 'random']
        if rng != [c for c in expected['calls'] if c[0] == 'random']:
            return case, 'rng', rng
    return None


def stage_cases():
    for attacker in range(4):
        target = attacker ^ 1
        for ability, suppressed in itertools.product((0, KEEN_EYE, UNAWARE), (0, bench.SUPPRESSED)):
            for acc, eva in itertools.product(STAGES, STAGES):
                yield {'attacker': attacker, 'target': target, 'accuracy': 70,
                       'abilities': {attacker: ability}, 'effect_flags': {attacker: suppressed},
                       'acc': {attacker: acc}, 'eva': {target: eva}}


def interaction_cases():
    base = {'attacker': 0, 'target': 1, 'accuracy': 80, 'abilities': {0: KEEN_EYE}}
    variants = [
        {'abilities': {0: KEEN_EYE, 1: UNAWARE}},                       # target Unaware
        {'abilities': {0: KEEN_EYE, 1: SIMPLE}},                        # target Simple
        {'abilities': {0: SIMPLE}},                                     # Simple attacker, control
        {'abilities': {0: 14}},                                         # Compound Eyes, control
        {'abilities': {0: KEEN_EYE, 1: 8}, 'field': 0x0C, 'active_abilities': ()},   # Sand Veil
        {'abilities': {0: KEEN_EYE, 1: 81}, 'field': 0xC0},             # Snow Cloak in hail
        {'abilities': {0: KEEN_EYE, 1: 8}, 'field': 0x0C, 'active_abilities': (13,)},  # Cloud Nine
        {'field': 1 << 15},                                             # fog
        {'field': 0x7000},                                              # gravity
        {'items': {1: (48, 10)}},                                       # target Bright Powder
        {'items': {0: (93, 10)}},                                       # Wide Lens
        {'items': {0: (104, 20)}, 'moved_first': True},                 # Zoom Lens
        {'micle': (0,)},
        {'status2': {1: bench.FORESIGHT}},
        {'effect_flags': {1: bench.MIRACLE_EYE}},
        {'abilities': {0: KEEN_EYE, 1: 77}, 'status2': {1: 1}},         # Tangled Feet confused
        {'abilities': {0: 55}, 'category': 0},                          # Hustle physical, control
        {'battle_status': 1 << 10},                                     # flat hit rate (No Guard path)
        {'battle_status': 1 << 5},                                      # charge turn
        {'accuracy': 0},                                                # bypass move
        {'effect': 0x98, 'field': 0x30, 'accuracy': 70},                # Thunder in sun
        {'battle_type': 1 << 10},                                       # tutorial
    ]
    for variant, (acc, eva), (attacker, target) in itertools.product(
            variants, ((6, 0), (6, 12), (0, 6), (12, 6), (3, 9), (9, 3)),
            ((0, 1), (0, 3), (2, 1), (3, 2))):
        case = dict(base, **variant)
        abilities = dict(case['abilities'])
        if attacker != 0:
            abilities[attacker] = abilities.pop(0, 0)
        if target != 1 and 1 in abilities:
            abilities[target] = abilities.pop(1)
        remap = lambda d: {({0: attacker, 1: target}.get(k, k)): v for k, v in d.items()}
        case.update(attacker=attacker, target=target, abilities=abilities,
                    acc={attacker: acc}, eva={target: eva})
        for key in ('items', 'status2', 'effect_flags'):
            if key in case:
                case[key] = remap(case[key])
        if 'micle' in case:
            case['micle'] = (attacker,)
        yield case


class InstalledSeam(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='modern-accuracy-hooks-')

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def setUp(self):
        self.inputs = load(self)

    def benches(self, address=TEST_ADDRESSES[0]):
        for language, (path, data) in self.inputs.items():
            image = bench.overlay_image(data)
            payload, _ = modern_abilities.compile_native(Path(self.work.name), address)
            patched, _ = modern_abilities.patch_overlay(image, address)
            yield language, bench.Bench(path, image), bench.Bench(path, patched, [(address, payload)])

    def test_plan_counts_before_and_after(self):
        rows = [  # ability, target evasion stage, move accuracy, before, after
            (KEEN_EYE, 12, 100, 33, 100), (UNAWARE, 12, 100, 100, 100), (0, 12, 100, 33, 33),
            (KEEN_EYE, 0, 75, 100, 75), (UNAWARE, 0, 75, 75, 75), (0, 0, 75, 100, 100),
            (KEEN_EYE, 6, 75, 75, 75)]
        for language, baseline, patched in self.benches():
            for ability, eva, accuracy, before, after in rows:
                case = {'abilities': {0: ability}, 'eva': {1: eva}, 'accuracy': accuracy}
                old, new = baseline.enumerate(case), patched.enumerate(case)
                self.assertEqual(old['hits'], before, (language, ability, eva, 'baseline'))
                self.assertEqual(new['hits'], after, (language, ability, eva, 'patched'))
                self.assertEqual(old['rng_calls'], [1])
                self.assertEqual(new['rng_calls'], [1])
                self.assertTrue(new['preserved'])
            suppressed = {'abilities': {0: KEEN_EYE}, 'eva': {1: 12}, 'accuracy': 100,
                          'effect_flags': {0: bench.SUPPRESSED}}
            self.assertEqual(patched.enumerate(suppressed)['hits'], 33, language + ' suppressed Keen Eye')

    def test_all_stage_deltas_four_battlers_and_suppression(self):
        for language, baseline, patched in self.benches():
            self.assertIsNone(differential(baseline, patched, stage_cases()), language)

    def test_interactions_keep_native_semantics(self):
        for language, baseline, patched in self.benches(TEST_ADDRESSES[1]):
            self.assertIsNone(differential(baseline, patched, interaction_cases()), language)

    def test_only_seam_bytes_change(self):
        for language, (path, data) in self.inputs.items():
            image = bench.overlay_image(data)
            patched, receipt = modern_abilities.patch_overlay(image, TEST_ADDRESSES[0])
            changed = [i for i in range(len(image)) if image[i] != patched[i]]
            self.assertTrue(changed, 'the seam must change')
            self.assertTrue(set(changed) <= set(range(modern_abilities.SITE - bench.OV12_BASE,
                                                       modern_abilities.SITE - bench.OV12_BASE + 6)))
            self.assertEqual(len(image), len(patched))
            self.assertEqual(patched[modern_abilities.SITE + 4 - bench.OV12_BASE:][:2], b'\x01\x28')


ASM = {
    'no_keen_eye': 'cmp r0, #109\n beq 1f\n movs r0, #0\n pop {r7, pc}\n1: movs r0, #1\n pop {r7, pc}',
    'no_unaware': 'cmp r0, #51\n beq 1f\n movs r0, #0\n pop {r7, pc}\n1: movs r0, #1\n pop {r7, pc}',
    'always': 'movs r0, #1\n pop {r7, pc}',
    # Ignores only evasion boosts: r4 (caller's evasion delta) negative.
    'positive_only': ('cmp r0, #109\n beq 1f\n cmp r0, #51\n bne 2f\n cmp r4, #0\n blt 1f\n'
                      '2: movs r0, #0\n pop {r7, pc}\n1: movs r0, #1\n pop {r7, pc}'),
    'sp_damage': 'sub sp, #8\n movs r0, #0\n pop {r7, pc}',
}


def assemble(work, name, body, address):
    getter = 'push {r7, lr}\n ldr r2, =0x%08X\n blx r2\n' % (bench.GETTER | 1)
    if name == 'raw_byte':
        getter = 'push {r7, lr}\n movs r2, #0xC0\n muls r1, r2\n adds r0, r0, r1\n ldr r2, =0x2D67\n ldrb r0, [r0, r2]\n'
        body = 'cmp r0, #51\n beq 1f\n cmp r0, #109\n beq 1f\n movs r0, #0\n pop {r7, pc}\n1: movs r0, #1\n pop {r7, pc}'
    source = Path(work) / (name + '.s')
    source.write_text('.syntax unified\n.thumb\n.text\n.global m\n.thumb_func\nm:\n ' + getter + ' ' + body + '\n.ltorg\n')
    obj = source.with_suffix('.o')
    subprocess.run([shutil.which('clang'), '--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-c',
                    str(source), '-o', str(obj)], check=True, capture_output=True)
    import sys
    sys.path.insert(0, str(bench.SOURCE / 'features/options/tools'))
    from carica_text import load_text
    return load_text(obj.read_bytes(), address, ('m',))[0]


class Mutants(unittest.TestCase):
    """Each mutant must fail the oracle; the real build must pass it first."""

    def setUp(self):
        self.inputs = load(self)
        self.work = tempfile.TemporaryDirectory(prefix='modern-accuracy-mutants-')
        self.addCleanup(self.work.cleanup)

    def verdict(self, path, image, patched, payload, address):
        baseline = bench.Bench(path, image)
        candidate = bench.Bench(path, patched, [(address, payload)])
        cases = list(itertools.islice(stage_cases(), 0, None, 7)) + list(interaction_cases())
        cases += [{'attacker': 0, 'target': 1, 'accuracy': 100, 'abilities': {0: a}, 'eva': {1: e},
                   'effect_flags': {0: f}} for a in (KEEN_EYE, UNAWARE) for e in (0, 12)
                  for f in (0, bench.SUPPRESSED)]
        try:
            return differential(baseline, candidate, cases)
        except (UcError, AssertionError) as exc:  # emulated crash or no return
            return ('crash', repr(exc))

    def test_mutants_killed_after_green_baseline(self):
        address = TEST_ADDRESSES[0]
        for language, (path, data) in self.inputs.items():
            image = bench.overlay_image(data)
            payload, _ = modern_abilities.compile_native(Path(self.work.name), address)
            patched, _ = modern_abilities.patch_overlay(image, address)
            self.assertIsNone(self.verdict(path, image, patched, payload, address), 'baseline must be green')
            still_109 = bytearray(patched)
            at = modern_abilities.SITE + 4 - bench.OV12_BASE
            still_109[at:at + 2] = b'\x6d\x28'
            mutants = {'cmp_still_109': (bytes(still_109), payload)}
            for name in list(ASM) + ['raw_byte']:
                mutants[name] = (patched, assemble(self.work.name, name, ASM.get(name, ''), address))
            for name, (mutant_image, mutant_payload) in mutants.items():
                with self.subTest(language=language, mutant=name):
                    self.assertIsNotNone(self.verdict(path, image, mutant_image, mutant_payload, address),
                                         'mutant survived: ' + name)


if __name__ == '__main__':
    unittest.main()
