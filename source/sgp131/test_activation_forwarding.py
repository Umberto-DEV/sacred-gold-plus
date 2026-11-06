"""Build/publication boundaries for immutable activation options."""
import hashlib
import inspect
import json
import unittest
from unittest.mock import patch
from . import activation, build
from . import test_build as fixtures

class ActivationBuild(unittest.TestCase):
    setUp = fixtures.MechanicsBuildTests.setUp
    mechanics = fixtures.MechanicsBuildTests.mechanics

    def options(self):
        return activation.StageOptions.parse(json.dumps({'schema': 1, 'language': 'EN', 'stage_options': {}}).encode())

    def compose_with_options(self, options):
        original = build.compose
        with patch('sgp131.build.compose', side_effect=lambda *args, **kwargs: original(*args, **kwargs, stage_options=options)):
            return self.mechanics()

    def test_builder_accepts_only_explicit_immutable_options(self):
        self.assertIn('stage_options', inspect.signature(build.compose).parameters)
        payload, report = self.compose_with_options(self.options())
        self.assertEqual(report['activation']['all_inert_sha256'], hashlib.sha256(payload).hexdigest())
        self.assertEqual(report['mechanics_options_sha256'], hashlib.sha256(self.options().wire).hexdigest())
        with self.assertRaisesRegex(ValueError, 'StageOptions'):
            self.compose_with_options({})

    def test_final_root_refusal_prevents_return_and_cleans_scratch(self):
        self.assertIn('stage_options', inspect.signature(build.compose).parameters)
        with patch('sgp131.activation.final_gate', side_effect=ValueError('final inert root refused')):
            with self.assertRaisesRegex(ValueError, 'final inert root refused'):
                self.compose_with_options(self.options())
        self.assertFalse((self.top / 'scratch').exists())


from . import test_workbench as bench_fixtures, workbench

class ActivationPublication(unittest.TestCase):
    setUp = bench_fixtures.WorkbenchTests.setUp
    init = bench_fixtures.WorkbenchTests.init
    ui_setup = bench_fixtures.UIWorkbenchTests.ui_setup

    def test_mechanics_config_requires_explicit_reviewed_hash(self):
        self.ui_setup()
        path = self.top / 'mechanics.json'
        path.write_text(json.dumps({'schema': 1, 'language': 'EN', 'stage_options': {}}))
        with self.assertRaisesRegex(ValueError, 'reviewed mechanics'):
            workbench.build_candidate(self.config, 'EN', 'ui', charmap=self.charmap,
                                      ui_config=self.ui_config, mechanics_config=path)
        with self.assertRaisesRegex(ValueError, 'differs'):
            workbench.build_candidate(self.config, 'EN', 'ui', charmap=self.charmap,
                                      ui_config=self.ui_config, mechanics_config=path,
                                      mechanics_config_sha256='0' * 64)
        self.assertFalse((self.root / 'EN/pending.nds').exists())

    def test_recorded_activation_provenance_rejects_partial_or_forged_metadata(self):
        from . import evidence
        import copy
        self.ui_setup()
        path = self.top / 'mechanics.json'
        path.write_text(json.dumps({'schema': 1, 'language': 'EN', 'stage_options': {}}))
        report = workbench.build_candidate(self.config, 'EN', 'ui', charmap=self.charmap,
                                           ui_config=self.ui_config, mechanics_config=path,
                                           mechanics_config_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        evidence.validate_provenance(report)
        for mutate in (lambda item: item.pop('activation'),
                       lambda item: item.update(mechanics_options_sha256='wrong'),
                       lambda item: item.update(mechanics_inputs=True),
                       lambda item: item['activation'].update(candidate_sha256='a' * 64),
                       lambda item: item['mechanics_inputs'].update(options_sha256='b' * 64)):
            forged = copy.deepcopy(report)
            mutate(forged)
            with self.assertRaises(ValueError):
                evidence.validate_provenance(forged)

    def test_config_snapshot_drift_blocks_consumer_admission(self):
        self.assertIn('mechanics_config', inspect.signature(workbench.build_candidate).parameters)
        self.ui_setup()
        path = self.top / 'mechanics.json'
        path.write_text(json.dumps({'schema': 1, 'language': 'EN', 'stage_options': {}}))
        report = workbench.build_candidate(self.config, 'EN', 'ui', charmap=self.charmap,
                                           ui_config=self.ui_config, mechanics_config=path,
                                           mechanics_config_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(report['mechanics_inputs']['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        original = (self.root / 'EN/pending.nds').read_bytes()
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'mechanics|config'):
            workbench.claim_consumer(self.config, 'EN', 'pending', __import__('os').getpid())
        self.assertEqual((self.root / 'EN/pending.nds').read_bytes(), original)
        self.assertFalse((self.root / 'consumers.json').exists())


if __name__ == '__main__':
    unittest.main()
