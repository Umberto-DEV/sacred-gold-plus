import copy
import unittest
from . import evidence, build


def report_for(digest, stage='baseline'):
    return {'schema': 1, 'candidate_sha256': digest, 'through': stage,
            'cases': [{'id': case, 'status': 'pass', 'candidate_sha256': digest,
                       'evidence': 'synthetic fixture assertion'}
                      for case in build.REQUIRED_CASES.get(stage, ())]}


class EvidenceTests(unittest.TestCase):
    def test_valid_complete_evidence(self):
        self.assertIsNone(evidence.validate_acceptance(report_for('a' * 64), 'a' * 64))

    def test_accept_requires_exact_evidence_hash(self):
        with self.assertRaisesRegex(ValueError, 'hash'):
            evidence.validate_acceptance(report_for('a' * 64), 'b' * 64)

    def test_builder_cases_cannot_be_omitted(self):
        report = report_for('a' * 64)
        report['required_cases'] = []
        report['cases'] = []
        with self.assertRaisesRegex(ValueError, 'case'):
            evidence.validate_acceptance(report, 'a' * 64)

    def test_fail_skip_duplicate_and_wrong_case_identity_are_refused(self):
        for change in ('fail', 'skip', 'duplicate', 'hash', 'empty'):
            report = report_for('a' * 64)
            if change == 'duplicate':
                report['cases'].append(copy.deepcopy(report['cases'][0]))
            elif change == 'hash':
                report['cases'][0]['candidate_sha256'] = 'b' * 64
            elif change == 'empty':
                report['cases'][0]['evidence'] = ''
            else:
                report['cases'][0]['status'] = change
            with self.subTest(change=change), self.assertRaises(ValueError):
                evidence.validate_acceptance(report, 'a' * 64)

    def test_invalid_schema_and_future_stage_refused(self):
        for report in ({}, report_for('a' * 64, 'portable')):
            with self.assertRaises(ValueError):
                evidence.validate_acceptance(report, 'a' * 64)

    def test_receipt_provenance_requires_complete_well_formed_baseline(self):
        validate = getattr(evidence, 'validate_provenance', None)
        self.assertTrue(callable(validate), 'receipt provenance needs one shared schema validator')
        valid = {'schema': 1, 'through': 'baseline', 'source_sha256': {'fixture.py': 'a' * 64},
                 'receipts': [], 'composition': {
                     'byte_identical': True, 'changed_file_ids': [], 'changed_regions': [],
                     'arm7_unchanged': True, 'file_ids_unchanged': True,
                     'hooks_and_reserve_unchanged': True}}
        self.assertIsNone(validate(valid))
        invalid = []
        for field in ('source_sha256', 'receipts', 'composition'):
            report = copy.deepcopy(valid)
            del report[field]
            invalid.append(report)
        for field, value in (('source_sha256', {}), ('source_sha256', []),
                             ('source_sha256', {'fixture.py': 'bad'}),
                             ('source_sha256', {'../foreign.py': 'a' * 64}),
                             ('receipts', [{'stage': 'controls'}]),
                             ('composition', {'byte_identical': True}),
                             ('through', 'portable')):
            report = copy.deepcopy(valid)
            report[field] = value
            invalid.append(report)
        report = copy.deepcopy(valid)
        report['composition']['byte_identical'] = 1
        invalid.append(report)
        for index, report in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(ValueError):
                validate(report)


def ui_report_for(provenance):
    digest = provenance['output_sha256']
    result = report_for(digest, 'ui')
    result.update(schema=2, language=provenance['language'], input_sha256=provenance['input_sha256'],
                  config_sha256=provenance['ui_inputs']['ui_config']['sha256'],
                  charmap_sha256=provenance['ui_inputs']['charmap']['sha256'],
                  observer_apk_sha256='d' * 64,
                  campaign={'reference': 'private/campaign.json', 'sha256': 'e' * 64})
    result['observer'] = {'device': 'synthetic-device', 'settings': 'private/settings.json',
                          'method': 'synthetic-test-record',
                          'before': {'sha256': result['input_sha256'], 'apk_sha256': 'd' * 64,
                                     'capture': 'private/before.json'},
                          'after': {'sha256': digest, 'apk_sha256': 'd' * 64,
                                    'capture': 'private/after.json'}}
    for case in result['cases']:
        case['record_key'] = case['id']
    return result


class UIEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.provenance = {'through': 'ui', 'language': 'IT', 'input_sha256': 'a' * 64,
                           'output_sha256': 'b' * 64,
                           'ui_inputs': {'ui_config': {'sha256': 'c' * 64},
                                         'charmap': {'sha256': 'f' * 64}}}

    def test_ui_requires_exact_provenance_and_sixteen_runtime_cases(self):
        report = ui_report_for(self.provenance)
        self.assertEqual(len(report['cases']), 16)
        evidence.validate_acceptance(report, 'b' * 64, provenance=self.provenance)
        for key in ('language', 'input_sha256', 'config_sha256', 'charmap_sha256', 'observer_apk_sha256'):
            changed = copy.deepcopy(report)
            changed[key] = 'EN' if key == 'language' else 'wrong'
            with self.subTest(key=key), self.assertRaises(ValueError):
                evidence.validate_acceptance(changed, 'b' * 64, provenance=self.provenance)
        with self.assertRaises(ValueError):
            evidence.validate_acceptance(report, 'b' * 64)

    def test_ui_campaign_and_case_record_references_are_bounded(self):
        report = ui_report_for(self.provenance)
        for value in ({}, {'reference': '../escape', 'sha256': 'e' * 64},
                      {'reference': 'x' * 4097, 'sha256': 'e' * 64},
                      {'reference': 'campaign.json', 'sha256': 'bad'}):
            changed = copy.deepcopy(report); changed['campaign'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                evidence.validate_acceptance(changed, 'b' * 64, provenance=self.provenance)
        for field, value in (('record_key', ''), ('record_key', 'x' * 257), ('status', 'skip'),
                             ('candidate_sha256', 'c' * 64), ('evidence', '')):
            changed = copy.deepcopy(report); changed['cases'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                evidence.validate_acceptance(changed, 'b' * 64, provenance=self.provenance)
        for change in ('omit', 'duplicate'):
            changed = copy.deepcopy(report); changed['required_cases'] = []
            if change == 'omit': changed['cases'].pop()
            else: changed['cases'].append(changed['cases'][0])
            with self.subTest(change=change), self.assertRaises(ValueError):
                evidence.validate_acceptance(changed, 'b' * 64, provenance=self.provenance)


    def test_ui_before_after_requires_same_apk_and_exact_image_identity(self):
        report = ui_report_for(self.provenance)
        for phase, field, value in (('before', 'sha256', 'f' * 64), ('after', 'sha256', 'a' * 64),
                                     ('before', 'apk_sha256', 'f' * 64), ('after', 'apk_sha256', 'f' * 64),
                                     ('before', 'capture', ''), ('after', 'capture', '../escape')):
            changed = copy.deepcopy(report); changed['observer'][phase][field] = value
            with self.subTest(phase=phase, field=field), self.assertRaises(ValueError):
                evidence.validate_acceptance(changed, 'b' * 64, provenance=self.provenance)
        for field in ('device', 'settings', 'method'):
            changed = copy.deepcopy(report); del changed['observer'][field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                evidence.validate_acceptance(changed, 'b' * 64, provenance=self.provenance)
