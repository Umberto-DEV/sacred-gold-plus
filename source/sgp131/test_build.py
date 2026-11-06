import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import baseline, build
from .test_baseline import EN, PINS


class BuildTests(unittest.TestCase):
    def test_baseline_is_identical_and_declares_required_cases(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(baseline.INPUT_HASHES, PINS, clear=True):
            scratch = Path(d) / 'unused'
            result = build.compose(EN, 'baseline', Path(d) / 'missing', scratch)
            self.assertIsInstance(result, tuple)
            data, report = result
            self.assertEqual(data, EN)
            self.assertEqual(report['required_cases'], list(build.REQUIRED_CASES['baseline']))
            self.assertEqual(report['output_sha256'], hashlib.sha256(EN).hexdigest())
            self.assertFalse(scratch.exists())

    def test_rejects_foreign_base_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            scratch = Path(d) / 'scratch'
            with self.assertRaisesRegex(ValueError, 'exact supported'):
                build.compose(b'foreign', 'baseline', Path(d) / 'map', scratch)
            self.assertFalse(scratch.exists())

    def test_rejects_unimplemented_and_unknown_stages(self):
        with patch.dict(baseline.INPUT_HASHES, PINS, clear=True):
            for stage in ('future-stage', 'typo'):
                with self.subTest(stage=stage), self.assertRaisesRegex(ValueError, 'stage'):
                    build.compose(EN, stage, Path('unused'), Path('unused'))

    def test_composition_rejects_any_change_or_unrecognized_receipt(self):
        self.assertIsInstance(build.verify_composition(EN, EN, []), dict)
        for before, after, receipts in ((EN, EN + b'x', []), (EN, EN, [{'stage': 'portable'}])):
            with self.assertRaisesRegex(ValueError, 'composition|receipt'):
                build.verify_composition(before, after, receipts)

    def test_source_snapshot_contains_sources_not_generated_cache(self):
        snapshot = build.source_snapshot()
        self.assertIn('sgp131/workbench.py', snapshot)
        self.assertIn('sgp13/build.py', snapshot)
        self.assertTrue(all(len(v) == 64 for v in snapshot.values()))
        self.assertFalse(any('__pycache__' in p for p in snapshot))

# Synthetic policy seam: transaction/dispatch tests, never native ROM evidence.
UI_CONFIG = {'schema': 1, 'kind': 'test-candidate', 'scene_work_calls': 37,
             'scene_glyph_budget': 2, 'scene_last_start_line': 240}
UI_MAP = b'synthetic pinned charmap\n'

def synthetic_ui(before, after, language, charmap, work_dir, receipt=None):
    import json
    if after != before + b'fixed authored UI':
        raise ValueError('synthetic independent UI byte policy')
    config = json.loads((Path(work_dir) / 'ui-candidate.json').read_text())
    result = {'schema': 1, 'stage': 'ui', 'language': language,
              'input_sha256': hashlib.sha256(before).hexdigest(),
              'output_sha256': hashlib.sha256(after).hexdigest(),
              'input_bytes': len(before), 'output_bytes': len(after),
              'config': config, 'config_sha256': hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
              'charmap_sha256': hashlib.sha256(Path(charmap).read_bytes()).hexdigest(),
              'policy_sha256': 'c' * 64, 'source_sha256': {'fixture.c': 'a' * 64},
              'payloads': {'scene': {'sources': {'fixture.c': 'a' * 64},
                                      'toolchain': {'executable_sha256': 'b' * 64}}},
              'file_count': 513, 'all_other_bytes_preserved': True}
    if receipt is not None and receipt != result:
        raise ValueError('receipt differs from independent readback')
    return result

def synthetic_install(before, language, charmap, work_dir):
    after = before + b'fixed authored UI'
    return after, synthetic_ui(before, after, language, charmap, work_dir)


class UIBuildTests(unittest.TestCase):
    def setUp(self):
        import json
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.top = Path(self.temp.name).resolve()
        self.charmap = self.top / 'map.txt'
        self.config = self.top / 'candidate.json'
        self.charmap.write_bytes(UI_MAP)
        self.config.write_text(json.dumps(UI_CONFIG))
        for target, value in [('sgp131.baseline.INPUT_HASHES', PINS)]:
            context = patch.dict(target, value, clear=True)
            context.start(); self.addCleanup(context.stop)
        for target, value in [('sgp131.guide_content.CHARMAP_SHA256', hashlib.sha256(UI_MAP).hexdigest())]:
            context = patch(target, value)
            context.start(); self.addCleanup(context.stop)
        for target, value in [('sgp131.ui.install', synthetic_install), ('sgp131.ui_verify.verify', synthetic_ui)]:
            context = patch(target, side_effect=value)
            context.start(); self.addCleanup(context.stop)

    def compose(self):
        return build.compose(EN, 'ui', self.charmap, self.top / 'scratch', ui_config=self.config)

    def test_explicit_ui_composes_and_binds_consumed_inputs(self):
        data, report = self.compose()
        self.assertEqual(data, EN + b'fixed authored UI')
        self.assertEqual(report['schema'], 2)
        self.assertEqual(report['ui_inputs']['charmap']['sha256'], hashlib.sha256(UI_MAP).hexdigest())
        self.assertEqual(report['ui_inputs']['ui_config']['sha256'], hashlib.sha256(self.config.read_bytes()).hexdigest())
        self.assertEqual(report['receipts'][0]['config'], UI_CONFIG)
        self.assertFalse((self.top / 'scratch').exists())

    def test_ui_requires_explicit_inputs_and_rejects_silent_defaults(self):
        for charmap, config in ((None, self.config), (self.charmap, None)):
            with self.subTest(charmap=charmap, config=config), self.assertRaisesRegex(ValueError, 'explicit'):
                build.compose(EN, 'ui', charmap, self.top / 'scratch', ui_config=config)
        self.config.write_text('{"schema":1}')
        with self.assertRaisesRegex(ValueError, 'configuration'):
            self.compose()
        self.assertFalse((self.top / 'scratch').exists())

    def test_ui_independent_policy_rejects_forged_output_and_receipt(self):
        def forged(before, language, charmap, work_dir):
            output, receipt = synthetic_install(before, language, charmap, work_dir)
            receipt['writes'] = ['anything']
            return output + b'outside policy', receipt
        with patch('sgp131.ui.install', side_effect=forged):
            with self.assertRaisesRegex(ValueError, 'policy'):
                self.compose()
        with patch('sgp131.ui.install', side_effect=lambda *a: (EN + b'fixed authored UI', {'stage': 'ui'})):
            with self.assertRaises(ValueError):
                self.compose()

    def test_ui_input_drift_and_symlink_are_refused_without_scratch_leak(self):
        real = synthetic_install
        def mutate(*args):
            result = real(*args)
            self.config.write_text('{}')
            return result
        with patch('sgp131.ui.install', side_effect=mutate):
            with self.assertRaisesRegex(ValueError, 'input|changed|configuration'):
                self.compose()
        self.assertFalse((self.top / 'scratch').exists())
        self.config.unlink()
        self.config.symlink_to(self.charmap)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.compose()

    def test_nonempty_ui_receipt_never_implicitly_selects_stage(self):
        with self.assertRaisesRegex(ValueError, 'receipt'):
            build.verify_composition(EN, EN + b'fixed authored UI', [{'stage': 'ui'}])

    def test_recorded_ui_provenance_rejects_forged_dependency_metadata(self):
        import copy
        from . import evidence
        _, valid = self.compose()
        evidence.validate_provenance(valid)
        for field, value in (('source_sha256', {'../escape.c': 'a' * 64}),
                             ('source_sha256', {'fixture.c': 'bad'}),
                             ('sources', {'fixture.c': 'bad'}),
                             ('toolchain', {'executable_sha256': 'bad'})):
            changed = copy.deepcopy(valid)
            if field == 'source_sha256': changed['receipts'][0][field] = value
            else: changed['receipts'][0]['payloads']['scene'][field] = value
            changed['composition'] = build.ui_composition(changed['receipts'][0])
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                evidence.validate_provenance(changed)

    def test_preexisting_scratch_is_never_adopted_or_pruned(self):
        scratch = self.top / 'scratch'; scratch.mkdir(); (scratch / 'unique').write_text('preserve')
        with self.assertRaises(FileExistsError): self.compose()
        self.assertEqual((scratch / 'unique').read_text(), 'preserve')

    def test_config_duplicate_fields_and_oversized_inputs_refused_before_installer(self):
        self.config.write_text('{"schema":1,"schema":1}')
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.compose()
        self.config.write_bytes(b' ' * (64 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, 'size'): self.compose()
        self.assertFalse((self.top / 'scratch').exists())

    def test_consumed_snapshot_mutation_cannot_relabel_config_or_charmap(self):
        import json
        for name in ('ui-candidate.json', 'charmap.txt'):
            def mutate(before, language, charmap, work_dir):
                path = Path(work_dir) / name
                if name == 'ui-candidate.json':
                    changed = dict(UI_CONFIG, scene_work_calls=38); path.write_text(json.dumps(changed))
                else: path.write_bytes(b'changed snapshot')
                return synthetic_install(before, language, charmap, work_dir)
            with self.subTest(name=name), patch('sgp131.ui.install', side_effect=mutate):
                with self.assertRaisesRegex(ValueError, 'snapshot|input|configuration'):
                    self.compose()
            self.assertFalse((self.top / 'scratch').exists())

    def test_ui_source_drift_during_composition_prevents_result(self):
        with patch('sgp131.build.source_snapshot', side_effect=[{'fixture.py': 'a' * 64}, {'changed.py': 'b' * 64}]):
            with self.assertRaisesRegex(ValueError, 'source'): self.compose()
        self.assertFalse((self.top / 'scratch').exists())


# Mechanical stages after the synthetic UI seam: fake registry entries prove wiring, receipt
# chaining and refusals. They are never ROM evidence; real-image proofs are Class B
# (test_mechanics_stages_rom.py).
class MechanicsBuildTests(unittest.TestCase):
    setUp = UIBuildTests.setUp

    def mechanics(self, through='ai'):
        from . import mechanics_stages
        from .test_mechanics_stages import FakeStage
        fakes = {'moves': FakeStage('moves', 3, 6, 0x41), 'ai': FakeStage('ai', 10, 14, 0x42)}
        for context in (patch.dict(mechanics_stages.REGISTRY, fakes, clear=True),
                        patch('sgp131.mechanics_stages.check_ui_invariants', side_effect=lambda *a: {})):
            context.start(); self.addCleanup(context.stop)
        return build.compose(EN, through, self.charmap, self.top / 'scratch', ui_config=self.config)

    def expected(self, *edits):
        value = bytearray(EN + b'fixed authored UI')
        for index, byte in edits:
            value[index] = byte
        return bytes(value)

    def test_chain_composes_after_ui_and_records_cumulative_cases(self):
        data, report = self.mechanics('ai')
        self.assertEqual(data, self.expected((3, 0x41), (10, 0x42)))
        self.assertEqual([r['stage'] for r in report['receipts']], ['ui', 'moves', 'ai'])
        self.assertEqual(report['through'], 'ai')
        self.assertEqual(report['required_cases'], list(build.REQUIRED_CASES['ai']))
        self.assertTrue(set(build.UI_CASES) < set(build.REQUIRED_CASES['moves']) < set(build.REQUIRED_CASES['ai']))
        ui_output = hashlib.sha256(EN + b'fixed authored UI').hexdigest()
        self.assertEqual(report['receipts'][0]['output_sha256'], ui_output)
        self.assertEqual(report['receipts'][1]['input_sha256'], ui_output)
        self.assertEqual(report['receipts'][1]['output_sha256'], report['receipts'][2]['input_sha256'])
        self.assertEqual(report['output_sha256'], hashlib.sha256(data).hexdigest())
        self.assertEqual(report['composition'], build.composition_for(report['receipts']))
        self.assertEqual([m['stage'] for m in report['composition']['mechanics']], ['moves', 'ai'])
        self.assertFalse((self.top / 'scratch').exists())

    def test_stage_lists_agree_with_the_mechanics_registry(self):
        from . import mechanics_stages
        # literal expectations, independent of the derivation in build.py
        self.assertEqual(build.STAGES, ('baseline', 'ui', 'moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable',
                                        'rematches', 'uturn-flinch', 'identity'))
        self.assertEqual(build.IMPLEMENTED, ('baseline', 'ui', 'moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity'))
        self.assertEqual(build.UI_CHAIN, ('ui', 'moves', 'ai', 'ai-immunities', 'abilities', 'gifts', 'legacy', 'legendary-scenes', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon', 'traded-egg', 'bag-foreign', 'bag-view-position', 'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches', 'uturn-flinch', 'identity'))
        self.assertEqual(build.STAGES[2:], mechanics_stages.ORDER)
        self.assertEqual(build.UI_CHAIN[1:], mechanics_stages.IMPLEMENTED)
        self.assertEqual(set(build.REQUIRED_CASES), set(build.IMPLEMENTED))
        for name in mechanics_stages.PENDING:
            self.assertNotIn(name, build.IMPLEMENTED)
            self.assertNotIn(name, build.REQUIRED_CASES)
        previous = ()
        for name in build.UI_CHAIN:                     # acceptance cases accumulate along the chain
            self.assertEqual(build.REQUIRED_CASES[name][:len(previous)], previous)
            self.assertGreaterEqual(len(build.REQUIRED_CASES[name]), len(previous))
            previous = build.REQUIRED_CASES[name]

    def test_through_moves_does_not_run_ai(self):
        data, report = self.mechanics('moves')
        self.assertEqual(data, self.expected((3, 0x41)))
        self.assertEqual([r['stage'] for r in report['receipts']], ['ui', 'moves'])
        self.assertEqual(report['required_cases'], list(build.REQUIRED_CASES['moves']))

    def test_future_pending_stage_refuses_before_ui_without_a_vacuous_pending_loop(self):
        from . import mechanics_stages
        future = 'future-stage'
        with patch.object(build, 'STAGES', (*build.STAGES, future)), \
                patch.dict(mechanics_stages.PENDING, {future: ('missing reviewed installer',)}, clear=True), \
                patch('sgp131.ui.install', side_effect=AssertionError('pending stage reached UI')):
            with self.assertRaises(mechanics_stages.StagePending) as caught:
                build.compose(EN, future, self.charmap, self.top / 'scratch', ui_config=self.config)
        self.assertEqual(caught.exception.stage, future)
        self.assertEqual(caught.exception.reasons, ('missing reviewed installer',))
        self.assertFalse((self.top / 'scratch').exists())

    def test_abilities_cases_extend_the_ai_cases(self):
        self.assertEqual(build.REQUIRED_CASES['abilities'][:len(build.REQUIRED_CASES['ai'])], build.REQUIRED_CASES['ai'])
        self.assertGreater(len(build.REQUIRED_CASES['abilities']), len(build.REQUIRED_CASES['ai']))
        self.assertTrue(all(name.startswith('abilities_') for name in build.ABILITIES_CASES))
        self.assertEqual(len(set(build.REQUIRED_CASES['abilities'])), len(build.REQUIRED_CASES['abilities']))

    def test_ai_cases_include_the_dual_immunity_switch_regression(self):
        self.assertIn('ai_dual_immunity_switch_choice', build.AI_CASES)
        self.assertIn('ai_dual_immunity_order_and_single_immunity_controls', build.AI_CASES)

    def test_damage_cases_cover_both_ghost_cells_and_all_other_pairs(self):
        self.assertEqual(build.DAMAGE_CASES,
                         ('damage_ghost_dragon_neutral',
                          'damage_ghost_dark_resisted',
                          'damage_ghost_chart_322_other_pairs_unchanged'))
        self.assertTrue(set(build.DAMAGE_CASES) < set(build.REQUIRED_CASES['ai']))

    def test_ai_immunity_cases_include_the_complete_switch_trap_contract(self):
        self.assertIn('ai_arena_trap_airborne_switch', build.AI_IMMUNITY_CASES)
        self.assertIn('ai_arena_trap_grounded_iron_ball_gravity_controls',
                      build.AI_IMMUNITY_CASES)
        self.assertIn('ai_trapping_shed_shell_contract', build.AI_IMMUNITY_CASES)
        self.assertIn('ai_absorb_switch_dry_skin_motor_drive',
                      build.AI_IMMUNITY_CASES)
        self.assertIn('ai_absorb_switch_active_ability_and_rng_controls',
                      build.AI_IMMUNITY_CASES)

    def test_gifts_cases_extend_the_abilities_cases(self):
        self.assertEqual(build.REQUIRED_CASES['gifts'][:len(build.REQUIRED_CASES['abilities'])],
                         build.REQUIRED_CASES['abilities'])
        self.assertGreater(len(build.REQUIRED_CASES['gifts']), len(build.REQUIRED_CASES['abilities']))
        self.assertTrue(all(name.startswith('gifts_') for name in build.GIFTS_CASES))
        self.assertEqual(len(set(build.REQUIRED_CASES['gifts'])), len(build.REQUIRED_CASES['gifts']))

    def test_safari_final_admin_loss_cases_are_required_by_legacy(self):
        cases = {
            'legacy_safari_final_admin_loss_whiteout_en_it',
            'legacy_safari_final_admin_loss_save_cold_en_it',
        }
        self.assertTrue(cases <= set(build.LEGACY_CASES))
        self.assertTrue(cases <= set(build.REQUIRED_CASES['legacy']))
        self.assertEqual(len(set(build.REQUIRED_CASES['legacy'])),
                         len(build.REQUIRED_CASES['legacy']))

    def test_pokeathlon_cases_are_required_before_controls(self):
        prior = build.REQUIRED_CASES['legendary-scenes']
        scene_version = build.REQUIRED_CASES['legendary-scene-version']
        self.assertEqual(scene_version[:len(prior)], prior)
        self.assertTrue(all(name.startswith('legendary_scene_version_')
                            for name in build.LEGENDARY_SCENE_VERSION_CASES))
        self.assertEqual(build.REQUIRED_CASES['trainer-fixes'][:len(scene_version)],
                         scene_version)
        self.assertEqual(build.REQUIRED_CASES['pokeathlon'][:len(build.REQUIRED_CASES['trainer-fixes'])],
                         build.REQUIRED_CASES['trainer-fixes'])
        self.assertTrue(all(name.startswith('pokeathlon_') for name in build.POKEATHLON_CASES))
        self.assertEqual(build.REQUIRED_CASES['traded-egg'][:len(build.REQUIRED_CASES['pokeathlon'])],
                         build.REQUIRED_CASES['pokeathlon'])
        self.assertTrue(all(name.startswith('traded_egg_') for name in build.TRADED_EGG_CASES))
        self.assertEqual(build.REQUIRED_CASES['bag-foreign'][:len(build.REQUIRED_CASES['traded-egg'])],
                         build.REQUIRED_CASES['traded-egg'])
        self.assertTrue(all(name.startswith('bag_foreign_') for name in build.BAG_FOREIGN_CASES))
        self.assertEqual(build.REQUIRED_CASES['controls'][:len(build.REQUIRED_CASES['bag-foreign'])],
                         build.REQUIRED_CASES['bag-foreign'])

    def test_follower_menu_jump_cases_follow_waterfall_before_controls(self):
        predecessor = build.REQUIRED_CASES['waterfall-facing']
        actual = build.REQUIRED_CASES['follower-menu-jump']
        self.assertEqual(actual[:len(predecessor)], predecessor)
        self.assertEqual(actual[-len(build.FOLLOWER_MENU_JUMP_CASES):],
                         build.FOLLOWER_MENU_JUMP_CASES)
        self.assertTrue(all(name.startswith('follower_menu_jump_')
                            for name in build.FOLLOWER_MENU_JUMP_CASES))
        self.assertEqual(build.REQUIRED_CASES['controls'][:len(actual)], actual)
        self.assertEqual(len(set(actual)), len(actual))

    def test_production_allocation_follows_independent_ui_and_refusal_cleans_scratch(self):
        from . import mechanics_stages
        events = []
        def install(*args):
            events.append('ui')
            return synthetic_install(*args)
        def verify(*args, **kwargs):
            events.append('verified')
            return synthetic_ui(*args, **kwargs)
        def allocate(base, requested, **kwargs):
            events.append('allocate')
            self.assertEqual(base, EN)
            self.assertEqual(requested, {'fairy-ai.code': 148,
                                         'modern-accuracy.code': 28})
            self.assertEqual(kwargs['installed_ui'], EN + b'fixed authored UI')
            self.assertEqual(Path(kwargs['charmap']).read_bytes(), UI_MAP)
            self.assertEqual(kwargs['archive_deltas'], ())
            self.assertEqual(kwargs['overlay_deltas'], ())
            raise ValueError('independent retirement verifier refused')
        with patch('sgp131.build.complete_deltas', return_value=()), \
                patch('sgp131.ui.install', side_effect=install), \
                patch('sgp131.ui_verify.verify', side_effect=verify), \
                patch('sgp131.reserve.allocate', side_effect=allocate):
            with self.assertRaisesRegex(mechanics_stages.CompositionError, 'retirement verifier refused'):
                build.compose(EN, 'abilities', self.charmap, self.top / 'scratch', ui_config=self.config)
        self.assertEqual(events, ['ui', 'verified', 'allocate'])
        self.assertFalse((self.top / 'scratch').exists())

    def test_an_allocation_nobody_consumes_is_refused(self):
        with patch('sgp131.ui.install', side_effect=AssertionError('UI must not start')):
            with self.assertRaisesRegex(ValueError, 'no stage'):
                build.compose(EN, 'moves', self.charmap, self.top / 'scratch', ui_config=self.config, allocation=[{}])
        self.assertFalse((self.top / 'scratch').exists())

    def test_failing_mechanical_stage_leaves_no_result_and_no_scratch(self):
        from . import mechanics_stages
        def boom(data, language):
            raise ValueError('mechanical writer refused')
        broken = mechanics_stages.MechanicalStage('moves', boom, lambda *a: {}, lambda rom: [])
        with patch.dict(mechanics_stages.REGISTRY, {'moves': broken}, clear=True):
            with self.assertRaisesRegex(ValueError, 'writer refused'):
                build.compose(EN, 'moves', self.charmap, self.top / 'scratch', ui_config=self.config)
        self.assertFalse((self.top / 'scratch').exists())

    def test_replay_inside_compose_refuses_a_stage_declaring_bytes_of_the_ui_output(self):
        from . import mechanics_stages
        from .test_mechanics_stages import FakeStage
        suffix = FakeStage('moves', 25, 30, 0x43)    # bytes appended by the UI stage, not part of the pristine input
        with patch.dict(mechanics_stages.REGISTRY, {'moves': suffix}, clear=True),                 patch('sgp131.mechanics_stages.check_ui_invariants', side_effect=lambda *a: {}):
            with self.assertRaisesRegex(ValueError, 'invalid declared region|pristine'):
                build.compose(EN, 'moves', self.charmap, self.top / 'scratch', ui_config=self.config)
        self.assertFalse((self.top / 'scratch').exists())

    def test_ui_composition_still_requires_exactly_one_receipt(self):
        _, report = self.compose_ui()
        inputs = build.snapshot_ui_inputs(self.charmap, self.config)
        receipt = report['receipts'][0]
        for given in ([receipt, receipt], []):
            with self.subTest(count=len(given)), self.assertRaisesRegex(ValueError, 'exactly one receipt'):
                build.verify_composition(EN, EN + b'fixed authored UI', given, through='ui', ui_inputs=inputs,
                                         scratch=self.top / 'verify')

    def compose_ui(self):
        return build.compose(EN, 'ui', self.charmap, self.top / 'scratch', ui_config=self.config)

    def test_chain_replay_matches_and_refuses_forged_finals_or_receipts(self):
        data, report = self.mechanics('ai')
        inputs = build.snapshot_ui_inputs(self.charmap, self.config)
        def replay(after, receipts, through='ai'):
            return build.verify_composition(EN, after, receipts, through=through, ui_inputs=inputs,
                                            scratch=self.top / 'verify')
        self.assertEqual(replay(data, report['receipts']), report['composition'])
        foreign = bytearray(data); foreign[30] ^= 1          # inside the UI-owned suffix
        declared = bytearray(data); declared[3] ^= 1         # inside a declared region, not what the receipt says
        receipts = report['receipts']
        for label, after, given in (('foreign byte', bytes(foreign), receipts),
                                    ('declared byte', bytes(declared), receipts),
                                    ('order', data, [receipts[0], receipts[2], receipts[1]]),
                                    ('missing', data, receipts[:2]),
                                    ('extra', data, receipts + [receipts[2]])):
            with self.subTest(case=label), self.assertRaises(ValueError):
                replay(after, given)
        with self.assertRaisesRegex(ValueError, 'receipt'):
            replay(data, receipts, through='moves')
        self.assertFalse((self.top / 'verify').exists())

    def test_chain_provenance_and_acceptance_require_every_mechanical_receipt_and_case(self):
        import copy
        from . import evidence
        from .test_evidence import ui_report_for
        _, report = self.mechanics('ai')
        evidence.validate_provenance(report)
        def forged(mutate):
            changed = copy.deepcopy(report); mutate(changed)
            if mutate.__name__ != 'composition':   # keep composition consistent so the chain checks are what refuse
                try:
                    changed['composition'] = build.composition_for(changed['receipts'])
                except (KeyError, IndexError, TypeError):
                    pass
            return changed
        def swap(r): r['receipts'][1], r['receipts'][2] = r['receipts'][2], r['receipts'][1]
        def drop(r): del r['receipts'][2]
        def chain_break(r): r['receipts'][2]['input_sha256'] = 'f' * 64
        def wrong_end(r): r['output_sha256'] = 'e' * 64
        def composition(r): r['composition']['mechanics'][0]['receipt_sha256'] = '0' * 64
        def embedded(r): r['receipts'][1]['stage_receipt']['offset'] = 99
        def stage_name(r): r['receipts'][1]['stage'] = 'ai'
        def ranges(r): r['receipts'][1]['changed_ranges'] = [[0, 1]]
        for mutate in (swap, drop, chain_break, wrong_end, composition, embedded, stage_name, ranges):
            with self.subTest(mutate=mutate.__name__), self.assertRaises(ValueError):
                evidence.validate_provenance(forged(mutate))
        acceptance = ui_report_for(report)
        template = acceptance['cases'][0]
        acceptance['through'] = 'ai'
        acceptance['cases'] = [dict(template, id=name, record_key=name) for name in build.REQUIRED_CASES['ai']]
        evidence.validate_acceptance(acceptance, report['output_sha256'], provenance=report)
        short = copy.deepcopy(acceptance); short['cases'].pop()
        ui_only = copy.deepcopy(acceptance)
        ui_only['cases'] = [c for c in ui_only['cases'] if c['id'] in build.UI_CASES]
        for label, changed, provenance in (('missing case', short, report), ('ui cases only', ui_only, report),
                                           ('stage mismatch', acceptance, dict(report, through='ui'))):
            with self.subTest(case=label), self.assertRaises(ValueError):
                evidence.validate_acceptance(changed, report['output_sha256'], provenance=provenance)
