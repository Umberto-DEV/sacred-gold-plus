"""The installed wrapper inside the real constructor: contexts, inertness, legacy trainers.

Oracle for every case: the same ROM before installation (native code only), run with the
same BattleSetup, seed and Plus state. Class B: real candidate ROMs, in memory only.
"""
import json
from pathlib import Path
import struct
import unittest

import rom_fixture as fx
import constructor_bench as bench

LEGACY = Path(__file__).resolve().parents[3] / 'sgp13' / 'data' / 'strategic-teams.json'
CONTEXTS = [  # (battleType, enemy index): every one must leave the native party untouched
    (1, 0), (1, 2), (1, 3), (0, 1), (2, 1), (3, 1), (4, 1), (5, 1), (8, 1), (9, 1), (16, 1), (17, 1),
    (128, 1), (129, 1), (0x100, 1), (0x101, 1), (0x80000001, 1), (0xFFFFFFFF, 1),
    # next to the two whitelisted values (phone 0x1, Dojo sequence 0x801): every other bit stays native
    (0x800, 1), (0x803, 1), (0x805, 1), (0x809, 1), (0x811, 1), (0x821, 1), (0x841, 1), (0x881, 1), (0x901, 1), (0xC01, 1),
    (0x1001, 1), (0x1801, 1), (0x2001, 1), (0x2801, 1), (0x80000801, 1), (0x13, 1), (0x4B, 1), (0x401, 1)]


class RomCase(unittest.TestCase):
    def need(self, language):
        try:
            fx.rom(language)
        except fx.MissingInput as exc:
            if fx.REQUIRE_INPUTS:
                self.fail(str(exc))
            self.skipTest(str(exc))

    def pair(self, language, mode='active'):
        self.need(language)
        patched, receipt = fx.installed(language, mode)
        return fx.native_bench(language), patched, receipt


class BothEntryFamilies(RomCase):
    """B1: the phone entry builds battleType 0x1, the inherited Dojo sequence 0x801 (SetupAndStartTrainerBattle adds
    BATTLE_TYPE_11 when its argument a4 is set). Both families receive the variants; any other value stays native."""

    def test_phone_and_dojo_sequence_both_apply_the_same_variant(self):
        for language in ('EN', 'IT'):
            native, patched, receipt = self.pair(language)
            skip = fx.skip_ranges()
            for trainer in (712, 713):
                for outcome, label in ((0, 'A'), (1, 'B')):
                    seed = fx.seed_for(trainer, outcome)
                    reference = native.run(trainer, plus=1, seed=seed)
                    results = {}
                    for family, battle_type in (('phone', 0x1), ('dojo-sequence', 0x801)):
                        with self.subTest(language=language, trainer=trainer, family=family, label=label):
                            result = patched.run(trainer, plus=1, battle_type=battle_type, seed=seed)
                            results[family] = [m['moves'] for m in result['decoded']]
                            self.assertNotEqual(results[family], [m['moves'] for m in reference['decoded']], 'the variant applies')
                    self.assertEqual(results['phone'], results['dojo-sequence'], 'one selector, one variant per construction')

    def test_plus_off_keeps_both_families_native(self):
        for language in ('EN', 'IT'):
            native, patched, receipt = self.pair(language)
            skip = fx.skip_ranges()
            for trainer in (712, 713):
                for battle_type in (0x1, 0x801):
                    seed = fx.seed_for(trainer, 1)
                    with self.subTest(language=language, trainer=trainer, battle_type=hex(battle_type)):
                        self.assertEqual(bench.compare_runs(patched.run(trainer, plus=0, battle_type=battle_type, seed=seed),
                                                            native.run(trainer, plus=0, battle_type=battle_type, seed=seed), skip), [])


class ContextFilter(RomCase):
    def test_non_single_link_multi_facility_contexts_noop(self):
        for language in ('EN', 'IT'):
            native, patched, receipt = self.pair(language)
            skip = fx.skip_ranges()
            for trainer in (712, 713):
                for battle_type, index in CONTEXTS:
                    for outcome in (0, 1):
                        seed = fx.seed_for(trainer, outcome)
                        with self.subTest(language=language, trainer=trainer, battle_type=hex(battle_type),
                                          index=index, outcome=outcome):
                            args = dict(plus=1, battle_type=battle_type, index=index, seed=seed)
                            before = native.run(trainer, **args)
                            after = patched.run(trainer, **args)
                            self.assertEqual(bench.compare_runs(after, before, skip), [])
                            reads = [e for e in after['events'] if e[0] == 'read' and e[1] == 56]
                            self.assertEqual(len(reads), 1, 'native reader called exactly once')
                            # the party really is the native one, not an authored variant
                            self.assertEqual([m['moves'] for m in after['decoded']],
                                             [m['moves'] for m in before['decoded']])

    def test_header_variants_noop_and_only_exact_context_applies(self):
        for language in ('EN', 'IT'):
            native, patched, receipt = self.pair(language)
            skip = fx.skip_ranges()
            archives = fx.archives(language)
            header = bytearray(archives.files('a/0/5/5')[712])
            header[3] = 5                                    # five members: not the supported 0x0306
            seed = fx.seed_for(712, 1)
            args = dict(plus=1, seed=seed, trainer_data=bytes(header))
            before, after = native.run(712, **args), patched.run(712, **args)
            self.assertEqual(len(after['mons']), 5)
            self.assertEqual(bench.compare_runs(after, before, skip), [])
            # control: the exact context does change the party (guards against a vacuous filter)
            exact = patched.run(712, plus=1, seed=seed)
            self.assertNotEqual([m['moves'] for m in exact['decoded']],
                                [m['moves'] for m in native.run(712, plus=1, seed=seed)['decoded']])


class DirectGate(RomCase):
    """rematch_native called directly with a crafted host frame: every gate on its own."""
    HOST, BUFFER = 0x023BC000, 0x02200000

    def attempt(self, language, trainer, *, mode='active', plus=1, battle_type=1, index=1, seed=None, outcome=0,
                arg_trainer=None, frame_buffer=None, frame_index=None, header=None, setup_null=False,
                host_null=False, buffer_null=False):
        self.need(language)
        patched, receipt = fx.installed(language, mode)
        archives = fx.archives(language)
        target = receipt['symbols']['rematch_native'] & ~1
        seed = fx.seed_for(trainer, outcome) if seed is None else seed
        baseline = bytes(archives.files('a/0/5/6')[trainer])
        header = bytes(archives.files('a/0/5/5')[trainer]) if header is None else header
        host = bytearray(0x80)
        struct.pack_into('<I', host, 0x10, index if frame_index is None else frame_index)
        struct.pack_into('<I', host, 0x68, seed)
        struct.pack_into('<I', host, 0x74, self.BUFFER if frame_buffer is None else frame_buffer)
        setup = bytearray(0x400)
        struct.pack_into('<I', setup, 0, battle_type)
        struct.pack_into('<I', setup, 0x18 + index * 4, trainer)
        setup[0x28 + index * 52:0x28 + index * 52 + len(header)] = header
        state = bytearray(32); state[0] = plus
        args = (0 if setup_null else bench.SETUP, 0 if host_null else self.HOST,
                trainer if arg_trainer is None else arg_trainer, 0 if buffer_null else self.BUFFER)
        cpu = patched.call_function(target, args, writes=[(bench.SETUP, setup), (self.HOST, host),
                                                           (self.BUFFER, baseline), (bench.PLUS_STATE, state)])
        return bytes(cpu.mem_read(self.BUFFER, 108)), baseline, receipt

    def test_each_gate_alone_keeps_the_native_buffer(self):
        for language in ('EN', 'IT'):
            self.need(language)
            for trainer in (712, 713):
                for outcome, label in ((0, 'A'), (1, 'B')):
                    with self.subTest(language=language, trainer=trainer, label=label):
                        after, baseline, receipt = self.attempt(language, trainer, outcome=outcome)
                        self.assertEqual(after, fx.variant_buffer(receipt, trainer, label))     # control: all gates open
                        bad_header = bytearray(fx.archives(language).files('a/0/5/5')[trainer]); bad_header[3] = 5
                        for name, kwargs in (('plus off', dict(plus=0)), ('inert config', dict(mode='inert')),
                                             ('battle type 2', dict(battle_type=2)), ('battle type 0', dict(battle_type=0)),
                                             ('battle type 0x101', dict(battle_type=0x101)),
                                             ('enemy index 2', dict(index=2)), ('enemy index 0', dict(index=0)),
                                             ('enemy index 4 in frame', dict(frame_index=4)), ('enemy index 7 in frame', dict(frame_index=7)),
                                             ('enemy index 8 in frame', dict(frame_index=8)),
                                             ('frame buffer differs', dict(frame_buffer=0x02201000)),
                                             ('loader trainer differs', dict(arg_trainer=trainer ^ 1)),
                                             ('count 5 header', dict(header=bytes(bad_header))),
                                             ('null setup', dict(setup_null=True)), ('null host', dict(host_null=True)),
                                             ('null buffer', dict(buffer_null=True))):
                            result, base, _ = self.attempt(language, trainer, outcome=outcome, **kwargs)
                            if kwargs.get('buffer_null'):
                                continue                                       # nothing to compare: it must simply return
                            self.assertEqual(result, base, name)


class AllTrainersSweep(RomCase):
    """The wrapper sits on the path of EVERY trainer party: one trainer per (format, member count) pair found in
    the trainer archive, Plus off and on, both selector outcomes, active wrapper against native code."""

    def test_active_wrapper_matches_native_for_every_format_and_count(self):
        for language in ('EN', 'IT'):
            native, patched, receipt = self.pair(language)
            skip = fx.skip_ranges()
            headers = fx.archives(language).files('a/0/5/5')
            chosen = {}
            for trainer, header in enumerate(headers):
                if len(header) >= 4 and header[3] and trainer not in (712, 713):
                    chosen.setdefault((header[0], header[3]), trainer)
            self.assertGreaterEqual(len(chosen), 4)
            runs = 0
            for (kind, count), trainer in sorted(chosen.items()):
                for plus in (0, 1):
                    for outcome in (0, 1):
                        with self.subTest(language=language, format=kind, count=count, trainer=trainer,
                                          plus=plus, outcome=outcome):
                            args = dict(plus=plus, seed=fx.seed_for(trainer, outcome))
                            before, after = native.run(trainer, **args), patched.run(trainer, **args)
                            self.assertEqual(bench.compare_runs(after, before, skip), [])
                            runs += 1
            self.assertEqual(runs, 4 * len(chosen))


class InertWrapper(RomCase):
    def test_inactive_config_is_pure_delegation_in_every_context(self):
        for language in ('EN', 'IT'):
            native, patched, receipt = self.pair(language, 'inert')
            self.assertEqual(receipt['active'], 0)
            skip = fx.skip_ranges()
            for trainer in (712, 713):
                for plus in (0, 1):
                    for outcome in (0, 1):
                        with self.subTest(language=language, trainer=trainer, plus=plus, outcome=outcome):
                            args = dict(plus=plus, seed=fx.seed_for(trainer, outcome))
                            before, after = native.run(trainer, **args), patched.run(trainer, **args)
                            self.assertEqual(bench.compare_runs(after, before, skip), [])


class LegacyStrategies(RomCase):
    def test_existing_seven_strategies_unchanged(self):
        spec = json.loads(LEGACY.read_text())
        for language in ('EN', 'IT'):
            native, patched, receipt = self.pair(language)
            skip = fx.skip_ranges()
            for team in spec['teams']:
                trainer = team['trainer_id']
                for plus in (0, 1):
                    for outcome in (0, 1):
                        with self.subTest(language=language, trainer=trainer, plus=plus, outcome=outcome):
                            args = dict(plus=plus, seed=fx.seed_for(trainer, outcome))
                            before, after = native.run(trainer, **args), patched.run(trainer, **args)
                            self.assertEqual(bench.compare_runs(after, before, skip), [])
                            for move in team['moves']:       # the 1.3 effect is still there (Plus) or absent (Normal)
                                slot, field = divmod(move['offset'], 18)
                                got = after['decoded'][slot]['moves'][(field - 8) // 2]
                                self.assertEqual(got, move['after'] if plus else move['before'])


if __name__ == '__main__':
    unittest.main()
