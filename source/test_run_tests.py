"""ROM-free contracts for the Class A runner's counts, verdict and timings."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_tests


class _CapturedOutput(io.StringIO):
    def reconfigure(self, **kwargs):
        pass


class RunnerTimingTests(unittest.TestCase):
    def test_success_preserves_invocation_counts_and_skips(self):
        result = subprocess.CompletedProcess([], 0, '',
                                             'Ran 3 tests in 0.1s\n\nOK (skipped=1)\n')
        with patch.object(run_tests.subprocess, 'run', return_value=result) as child, \
                patch.object(run_tests.time, 'perf_counter', side_effect=[10.0, 12.125]), \
                patch.object(sys, 'stdout', _CapturedOutput()) as output:
            actual = run_tests.esegui('synthetic', run_tests.SOURCE,
                                      ['-m', 'unittest', 'fixture'], env={'EXTRA': '1'})
        self.assertEqual(actual, (True, 3, 1, 2.125))
        args, kwargs = child.call_args
        self.assertEqual(args[0], [sys.executable, '-m', 'unittest', 'fixture'])
        self.assertEqual(kwargs['cwd'], str(run_tests.SOURCE))
        self.assertEqual(kwargs['env']['EXTRA'], '1')
        self.assertEqual(kwargs['env']['PYTHONDONTWRITEBYTECODE'], '1')
        self.assertIn('2 run,  1 skipped   ok   2.125s', output.getvalue())

    def test_failed_child_keeps_failure_and_available_counts(self):
        result = subprocess.CompletedProcess([], 1, '',
                                             'Ran 2 tests in 0.1s\n\nFAILED (failures=1)\n')
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[3.0, 3.75]), \
                patch.object(sys, 'stdout', _CapturedOutput()):
            self.assertEqual(run_tests.esegui('failed', run_tests.SOURCE, ['-m', 'unittest']),
                             (False, 2, 0, 0.75))

    def test_empty_class_a_still_fails_while_class_b_can_skip(self):
        result = subprocess.CompletedProcess([], 0, '', 'Ran 0 tests in 0.0s\n\nOK\n')
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[1, 2, 3, 4]), \
                patch.object(sys, 'stdout', _CapturedOutput()):
            self.assertEqual(run_tests.esegui('empty A', run_tests.SOURCE,
                                               ['-m', 'unittest']), (False, 0, 0, 1))
            self.assertEqual(run_tests.esegui('empty B', run_tests.SOURCE,
                                               ['-m', 'unittest'], classe_b=True),
                             (True, 0, 0, 1))

    def test_json_has_each_duration_and_class_b_failure_controls_final_verdict(self):
        with tempfile.TemporaryDirectory(prefix='runner-timing-test-') as folder:
            report = Path(folder) / 'result.json'
            outcomes = [(True, 3, 1, 1.25), (True, 2, 0, 2.5),
                        (True, 4, 0, 3.75), (False, 1, 0, 0.5)]
            with patch.object(run_tests, 'SUITE', [('synthetic A', run_tests.SOURCE,
                                                    ['-m', 'unittest', 'fixture'])]), \
                    patch.object(run_tests, 'SUITE_CLASSE_B', [('synthetic B', run_tests.SOURCE,
                                                                 ['-m', 'unittest', 'fixture_b'])]), \
                    patch.object(run_tests, 'esegui', side_effect=outcomes) as child, \
                    patch.object(run_tests, 'compila_opzioni', return_value=(Path(folder), None, False)), \
                    patch.object(run_tests.time, 'perf_counter', side_effect=[8, 9.5]), \
                    patch.object(sys, 'argv', ['run_tests.py', '--json', str(report)]), \
                    patch.object(sys, 'stdout', _CapturedOutput()) as output:
                self.assertEqual(run_tests.main(), 1)
            data = json.loads(report.read_text())
        self.assertEqual([x['elapsed_seconds'] for x in data['suites']],
                         [1.25, 2.5, 3.75])
        self.assertEqual(data['suites'][-1]['compile_seconds'], 1.5)
        self.assertEqual(data['classe_b'][0]['elapsed_seconds'], 0.5)
        self.assertEqual((data['collected'], data['skipped'], data['classe_a_ok']),
                         (9, 1, True))
        self.assertEqual((data['collected_classe_b'], data['classe_b_ok'], data['ok']),
                         (1, False, False))
        self.assertTrue(child.call_args.kwargs['classe_b'])
        self.assertIn('Class A 9 + Class B 1) — FAIL', output.getvalue())

    def test_missing_compiler_keeps_ci_failure_and_separate_collection_time(self):
        with tempfile.TemporaryDirectory(prefix='runner-timing-test-') as folder:
            report = Path(folder) / 'result.json'
            with patch.object(run_tests, 'SUITE', []), \
                    patch.object(run_tests, 'SUITE_CLASSE_B', []), \
                    patch.object(run_tests, 'esegui', return_value=(True, 2, 0, 0.25)), \
                    patch.object(run_tests, 'compila_opzioni',
                                 return_value=(None, 'compiler missing', True)), \
                    patch.object(run_tests, 'conta_soltanto', return_value=7), \
                    patch.object(run_tests.time, 'perf_counter', side_effect=[1, 2, 3, 4]), \
                    patch.dict(run_tests.os.environ, {'SGP_CI': '1'}), \
                    patch.object(sys, 'argv', ['run_tests.py', '--json', str(report)]), \
                    patch.object(sys, 'stdout', _CapturedOutput()):
                self.assertEqual(run_tests.main(), 1)
            data = json.loads(report.read_text())
        options = data['suites'][-1]
        self.assertEqual((options['collected'], options['skipped'], options['ok']),
                         (7, 7, False))
        self.assertEqual((options['elapsed_seconds'], options['compile_seconds'],
                          options['collection_seconds']), (0.0, 1, 1))
        self.assertFalse(data['ok'])


if __name__ == '__main__':
    unittest.main()
