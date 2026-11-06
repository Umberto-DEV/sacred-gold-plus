"""Class B: genuine-policy EN/IT full-chain inert -> active composition.

Proof-shaped records below are SYNTHETIC UNIT-TEST inputs, not captures or Android
validation. They exercise the existing measured-proof schema without a synthetic
production bypass, policy override, substituted allocator or forged reserve grant.
Original V4 inputs are SHA-checked; ROMs stay in memory and no save is accessed.

Inputs: SGP131_BASE_EN/IT, SGP131_UI_CHARMAP. Missing inputs fail when either
SGP131_ACTIVATION_REQUIRE_INPUTS=1 or SGP131_MECHANICS_REQUIRE_INPUTS=1.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

from . import activation, baseline, build, controls, evidence, portable, rematches, ui_verify
from .test_activation import document as synthetic_document
from .test_ui import CONFIG

LANGUAGES = ('EN', 'IT')
_CACHE = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _inert_options(language):
    return activation.StageOptions.parse(json.dumps({
        'schema': 1, 'language': language, 'stage_options': {
            'controls': {'mode': 'inert', 'geometry': dict(controls.PROPOSAL), 'variant': 'compact'},
            'portable': {'mode': 'inert', 'activation': {
                'bridge': 0, 'input': 0, 'prompt': 0, 'travel_mask': 3}},
            'rematches': {'mode': 'inert'}}}).encode())


def _active_options(base, language, candidate_sha256):
    """Synthetic UNIT-TEST records explicitly naming every overlapping native window.

    This is byte/receipt coverage, not a claim those windows were measured hidden.
    The parent must collect and validate actual runtime evidence separately.
    """
    doc = synthetic_document(candidate_sha256)
    doc['language'] = language
    for owner, entry in doc['stage_options'].items():
        proof = entry['evidence' if owner == 'controls' else 'context_proof']
        proof['language'] = language
        proof['build_id'] = 'SYNTHETIC-UNIT-TEST-NOT-A-CAPTURE-' + language
    inventory = controls.check_geometry(dict(controls.PROPOSAL), controls.inventory(base))
    doc['stage_options']['controls']['evidence']['hidden_windows'] = inventory['overlapping_windows']
    return activation.StageOptions.parse(json.dumps(doc).encode())


class CompleteActivation(unittest.TestCase):
    def candidate(self, language):
        if language in _CACHE:
            return _CACHE[language]
        path = os.environ.get('SGP131_BASE_' + language)
        charmap = os.environ.get('SGP131_UI_CHARMAP')
        if not path or not charmap:
            reason = 'missing canonical %s V4 input or pinned UI charmap' % language
            if any(os.environ.get(name) == '1' for name in
                   ('SGP131_ACTIVATION_REQUIRE_INPUTS', 'SGP131_MECHANICS_REQUIRE_INPUTS')):
                self.fail(reason)
            self.skipTest(reason)
        base = Path(path).read_bytes()
        self.assertEqual(baseline.identify(base), language)
        directory = tempfile.TemporaryDirectory(prefix='activation-production-chain-')
        unittest.addModuleCleanup(directory.cleanup)
        top = Path(directory.name).resolve()
        config = top / 'ui-candidate.json'
        config.write_text(json.dumps(CONFIG))
        charmap = Path(charmap).resolve()
        sources = build.source_snapshot()
        inert_options = _inert_options(language)
        inert, inert_report = build.compose(base, 'identity', charmap, top / 'inert',
                                           ui_config=config, stage_options=inert_options)
        root = sha(inert)
        active_options = _active_options(base, language, root)
        self.assertEqual(len(active_options.document()['stage_options']['controls']['evidence']['hidden_windows']), 4)
        active, active_report = build.compose(base, 'identity', charmap, top / 'active',
                                             ui_config=config, stage_options=active_options)
        self.assertEqual(build.source_snapshot(), sources)
        self.assertEqual(inert_report['source_sha256'], sources)
        self.assertEqual(active_report['source_sha256'], sources)
        self.assertFalse((top / 'inert').exists())
        self.assertFalse((top / 'active').exists())
        inputs = build.snapshot_ui_inputs(charmap, config)
        result = (base, inert, active, inert_report, active_report, active_options, inputs, top)
        _CACHE[language] = result
        print(json.dumps({'scope': 'SYNTHETIC UNIT-TEST PROOFS; NO ANDROID/CAPTURE PASS',
                          'language': language, 'input_sha256': sha(base),
                          'inert_fixture_sha256': root, 'active_fixture_sha256': sha(active),
                          'through': 'identity', 'allocation_policy': 'genuine production Guide verifier'}), flush=True)
        return result

    def replay(self, language, *, options):
        base, _, active, _, report, _, inputs, top = self.candidate(language)
        return build.verify_composition(
            base, active, report['receipts'], through='identity', ui_inputs=inputs,
            scratch=top / 'replay', allocation=report['reserve_allocation']['receipt'],
            stage_options=options)

    def test_all_owners_rebuild_and_replay_under_real_policy_with_one_inert_root(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, inert, active, inert_report, report, options, _, top = self.candidate(language)
                self.assertEqual(report['through'], 'identity')
                self.assertEqual([r['stage'] for r in report['receipts']],
                                 ['ui', 'moves', 'ai', 'ai-immunities', 'abilities',
                                  'legacy', 'legendary-scene-version', 'trainer-fixes', 'pokeathlon',
                                  'traded-egg', 'bag-foreign', 'bag-view-position',
                                  'lottery-id', 'battle-tower-wrap', 'battle-animation-facade', 'battle-animation-dynamicpunch', 'battle-animation-helping-hand', 'battle-animation-strength', 'battle-animation-spit-up', 'giratina-pc-form', 'invisible-grass', 'waterfall-facing', 'follower-menu-jump', 'controls', 'portable', 'rematches',
                                  'uturn-flinch', 'identity'])
                self.assertEqual(report['reserve_allocation']['source'], 'reserve.allocate')
                grant = report['reserve_allocation']['receipt']
                self.assertEqual(grant['schema'], 2)
                self.assertEqual(grant['input_sha256'], sha(base))
                self.assertEqual(grant, inert_report['reserve_allocation']['receipt'])
                self.assertEqual(
                    {row['name']: row['parent'] for row in grant['assignments']},
                    {'fairy-ai.code': 'training.extension',
                     'modern-accuracy.code': 'field-guide.code',
                     'summary-controls.runtime': 'field-guide.code',
                     'portable-box.runtime': 'field-guide.code',
                     'c8.module-stubs': 'field-guide.code'})
                self.assertEqual(grant['installer_verification']['kind'], 'cold-ui-guide-retirement-v1')
                evidence.validate_provenance(inert_report)
                evidence.validate_provenance(report)
                owners = build.owner_receipts(report['receipts'])
                self.assertEqual(set(owners), set(activation.OWNERS))
                self.assertTrue(all(owner['function_state'] == 'active' for owner in owners.values()))
                self.assertEqual(report['activation']['active_owners'], list(activation.OWNERS))
                self.assertEqual(report['activation']['candidate_sha256'], sha(inert))
                self.assertEqual(report['activation']['all_inert_sha256'], sha(inert))
                self.assertEqual(options.candidate_sha256, sha(inert))
                locations = activation._locations(active, owners)
                self.assertEqual(len(locations), 6)
                self.assertTrue(all(int.from_bytes(active[at:at + size], 'little') == 1
                                    for at, size, _ in locations))
                self.assertEqual(activation._clear(active, locations), inert)
                view = ui_verify.Image(active)
                self.assertEqual(struct.unpack('<I', view.arm(owners['controls']['slot']['start'] +
                                                             controls.STATE_ENABLED, 4))[0], 1)
                self.assertEqual(owners['portable']['config']['values'],
                                 {'bridge': 1, 'input': 1, 'prompt': 1, 'travel_mask': 3, 'context_proof': 1})
                self.assertEqual(view.file(126)[rematches.DEFAULT_CODE_SIZE + rematches.ACTIVE_BYTE], 1)
                self.assertEqual(inert_report['activation']['active_owners'], [])
                self.assertEqual(self.replay(language, options=options), report['composition'])
                self.assertFalse((top / 'replay').exists())

    def test_omitted_wrong_language_and_wrong_root_options_are_refused(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, inert, active, _, report, options, _, top = self.candidate(language)
                with self.assertRaises(ValueError):
                    self.replay(language, options=None)
                self.assertFalse((top / 'replay').exists())
                other_language = 'IT' if language == 'EN' else 'EN'
                wrong_language = _active_options(base, other_language, sha(inert))
                with self.assertRaisesRegex(ValueError, 'language'):
                    self.replay(language, options=wrong_language)
                self.assertFalse((top / 'replay').exists())
                wrong_root = _active_options(base, language, '0' * 64)
                with self.assertRaises(ValueError):
                    activation.final_gate(active, wrong_root, build.owner_receipts(report['receipts']), language=language)
                self.assertEqual(build.source_snapshot(), report['source_sha256'])


if __name__ == '__main__':
    unittest.main()
