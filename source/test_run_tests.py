"""ROM-free contracts for the Class A runner's counts, verdict and timings."""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
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
        self.assertEqual(actual, (True, 3, 1, 2.125, 3))
        args, kwargs = child.call_args
        self.assertEqual(args[0], [sys.executable, '-m', 'unittest', '-v', 'fixture'])
        self.assertEqual(kwargs['cwd'], str(run_tests.SOURCE))
        self.assertEqual(kwargs['env']['EXTRA'], '1')
        self.assertEqual(kwargs['env']['PYTHONDONTWRITEBYTECODE'], '1')
        self.assertIn('3 methods ran,  1 skip events   ok   2.125s', output.getvalue())

    def test_failed_child_keeps_failure_and_available_counts(self):
        result = subprocess.CompletedProcess([], 1, '',
                                             'Ran 2 tests in 0.1s\n\nFAILED (failures=1)\n')
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[3.0, 3.75]), \
                patch.object(sys, 'stdout', _CapturedOutput()):
            self.assertEqual(run_tests.esegui('failed', run_tests.SOURCE, ['-m', 'unittest']),
                             (False, 2, 0, 0.75, 2))

    def test_long_failure_retains_early_error_and_summary(self):
        failure = 'ERROR: early diagnostic\n' + 'x' * 5000 + '\nRan 2 tests in 0.1s\nFAILED (errors=1)\n'
        result = subprocess.CompletedProcess([], 1, '', failure)
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[3.0, 3.75]), \
                patch.object(sys, 'stdout', _CapturedOutput()) as output:
            self.assertEqual(run_tests.esegui('failed', run_tests.SOURCE, ['-m', 'unittest']),
                             (False, 2, 0, 0.75, 2))
        self.assertIn('ERROR: early diagnostic', output.getvalue())
        self.assertIn('FAILED (errors=1)', output.getvalue())

    def test_empty_class_a_still_fails_while_class_b_can_skip(self):
        result = subprocess.CompletedProcess([], 0, '', 'Ran 0 tests in 0.0s\n\nOK\n')
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[1, 2, 3, 4]), \
                patch.object(sys, 'stdout', _CapturedOutput()):
            self.assertEqual(run_tests.esegui('empty A', run_tests.SOURCE,
                                               ['-m', 'unittest']), (False, 0, 0, 1, 0))
            self.assertEqual(run_tests.esegui('empty B', run_tests.SOURCE,
                                               ['-m', 'unittest'], classe_b=True),
                             (True, 0, 0, 1, 0))

    def test_all_skipped_class_a_fails_and_reports_reasons(self):
        result = subprocess.CompletedProcess([], 0, '',
            "test_case (fixture.Case) ... skipped 'private ROM absent'\n"
            "Ran 1 test in 0.0s\n\nOK (skipped=1)\n")
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[1, 2]), \
                patch.object(sys, 'stdout', _CapturedOutput()) as output:
            self.assertEqual(run_tests.esegui('all skipped A', run_tests.SOURCE,
                                               ['-m', 'unittest', 'fixture']),
                             (False, 1, 1, 1, 0))
        self.assertIn('all collected Class A tests skipped', output.getvalue())
        self.assertIn('skip reason (1): private ROM absent', output.getvalue())

    def test_discovery_keeps_its_subcommand_before_verbose_flag(self):
        result = subprocess.CompletedProcess([], 0, '', 'Ran 1 test in 0.0s\n\nOK\n')
        with patch.object(run_tests.subprocess, 'run', return_value=result) as child, \
                patch.object(run_tests.time, 'perf_counter', side_effect=[1, 2]), \
                patch.object(sys, 'stdout', _CapturedOutput()):
            self.assertTrue(run_tests.esegui('discovery', run_tests.SOURCE,
                ['-m', 'unittest', 'discover', '-p', 'test_*.py'])[0])
        self.assertEqual(child.call_args.args[0],
            [sys.executable, '-m', 'unittest', 'discover', '-v', '-p', 'test_*.py'])

    def test_skipped_subtests_do_not_hide_a_successful_class_a_test(self):
        result = subprocess.CompletedProcess([], 0, '',
            "test_one (fixture.Case) ... \n"
            "  test_one (fixture.Case) (case=2) ... skipped 'optional ROM'\n"
            "Ran 1 test in 0.0s\n\nOK (skipped=1)\n")
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[1, 2]), \
                patch.object(sys, 'stdout', _CapturedOutput()):
            self.assertEqual(run_tests.esegui('mixed', run_tests.SOURCE,
                                               ['-m', 'unittest', 'fixture']),
                             (True, 1, 1, 1, 1))

    def test_module_level_skip_is_not_a_class_a_pass(self):
        result = subprocess.CompletedProcess([], 0, '',
            "setUpClass (fixture.Case) ... skipped 'private input'\n"
            "Ran 0 tests in 0.0s\n\nOK (skipped=1)\n")
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[1, 2]), \
                patch.object(sys, 'stdout', _CapturedOutput()):
            self.assertFalse(run_tests.esegui('module skipped', run_tests.SOURCE,
                                               ['-m', 'unittest', 'fixture'])[0])

    def test_double_quoted_skip_reason_is_visible(self):
        result = subprocess.CompletedProcess([], 0, '',
            'test_one (fixture.Case) ... ok\n'
            'test_two (fixture.Case) ... skipped "can\'t load private ROM"\n'
            'Ran 2 tests in 0.0s\n\nOK (skipped=1)\n')
        with patch.object(run_tests.subprocess, 'run', return_value=result), \
                patch.object(run_tests.time, 'perf_counter', side_effect=[1, 2]), \
                patch.object(sys, 'stdout', _CapturedOutput()) as output:
            self.assertTrue(run_tests.esegui('mixed', run_tests.SOURCE,
                                              ['-m', 'unittest', 'fixture'])[0])
        self.assertIn("skip reason (1): can't load private ROM", output.getvalue())


    def test_json_has_each_duration_and_class_b_failure_controls_final_verdict(self):
        with tempfile.TemporaryDirectory(prefix='runner-timing-test-') as folder:
            report = Path(folder) / 'result.json'
            outcomes = [(True, 3, 1, 1.25, 2), (True, 2, 0, 2.5, 2),
                        (True, 4, 0, 3.75, 4), (False, 1, 0, 0.5, 1)]
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
        self.assertEqual(data['executed_methods'], 8)
        self.assertEqual((data['collected_classe_b'], data['classe_b_ok'], data['ok']),
                         (1, False, False))
        self.assertEqual(data['executed_methods_classe_b'], 1)
        self.assertIs(data.get('complete'), True)
        self.assertIsNone(data['active_suite'])
        self.assertTrue(child.call_args.kwargs['classe_b'])
        self.assertIn('Class A 9 + Class B 1) — FAIL', output.getvalue())

    def test_missing_compiler_keeps_ci_failure_and_separate_collection_time(self):
        with tempfile.TemporaryDirectory(prefix='runner-timing-test-') as folder:
            report = Path(folder) / 'result.json'
            with patch.object(run_tests, 'SUITE', []), \
                    patch.object(run_tests, 'SUITE_CLASSE_B', []), \
                    patch.object(run_tests, 'esegui', return_value=(True, 2, 0, 0.25, 2)), \
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
        self.assertEqual(options['executed_methods'], 0)
        self.assertEqual((options['elapsed_seconds'], options['compile_seconds'],
                          options['collection_seconds']), (0.0, 1, 1))
        self.assertFalse(data['ok'])
        self.assertIs(data.get('complete'), True)
        self.assertIsNone(data['active_suite'])


class RunnerCheckpointTests(unittest.TestCase):
    @contextmanager
    def small_run(self, folder, *, json_report=True):
        """Run real tiny child suites instead of the repository's full matrix."""
        root = Path(folder)
        source = root / 'source'
        fixture = ("import unittest\n"
                   "class Case(unittest.TestCase):\n"
                   "    def test_pass(self): pass\n"
                   "    @unittest.skip('fixture skip')\n"
                   "    def test_skip(self): pass\n")
        for cwd in (source, source / 'features/native-core/test',
                    source / 'features/options/test'):
            cwd.mkdir(parents=True, exist_ok=True)
            (cwd / 'test_fixture.py').write_text(fixture)
        report = root / 'result.json'
        command = ['-m', 'unittest', 'test_fixture']
        with ExitStack() as stack:
            stack.enter_context(patch.object(run_tests, 'SOURCE', source))
            stack.enter_context(patch.object(run_tests, 'SUITE', [
                ('first', source, command), ('second', source, command)]))
            stack.enter_context(patch.object(run_tests, 'SUITE_CLASSE_B', [
                ('synthetic B', source, command)]))
            stack.enter_context(patch.object(run_tests, 'compila_opzioni',
                return_value=(source / 'features/options/test', None, False)))
            stack.enter_context(patch.object(sys, 'argv', ['run_tests.py'] +
                (['--json', str(report)] if json_report else [])))
            output = stack.enter_context(patch.object(sys, 'stdout', _CapturedOutput()))
            yield report, output

    def test_new_run_invalidates_stale_pass_before_first_suite(self):
        with tempfile.TemporaryDirectory(prefix='runner-checkpoint-test-') as folder:
            with self.small_run(folder) as (report, output):
                report.write_text('{"complete": true, "ok": true}\n')
                with patch.object(run_tests, 'esegui', side_effect=KeyboardInterrupt), \
                        self.assertRaises(KeyboardInterrupt):
                    run_tests.main()
                data = json.loads(report.read_text())
            self.assertEqual((data.get('complete'), data.get('ok')), (False, False))
            self.assertEqual(data['active_suite'], 'first')
            self.assertEqual((data['suites'], data['classe_b']), ([], []))
            self.assertEqual((data['collected'], data['collected_classe_b']), (0, 0))
            self.assertNotIn('— PASS', output.getvalue())

    def test_interruption_retains_finished_suites_and_identifies_active_phase(self):
        phases = [
            ('second', ['first']),
            ('native code (Unicorn)', ['first', 'second']),
            ('options payload compilation', ['first', 'second', 'native code (Unicorn)']),
            ('options page (Unicorn)', ['first', 'second', 'native code (Unicorn)']),
            ('synthetic B', ['first', 'second', 'native code (Unicorn)', 'options page (Unicorn)']),
        ]
        real_execute = run_tests.esegui
        for phase, finished in phases:
            with self.subTest(phase=phase), \
                    tempfile.TemporaryDirectory(prefix='runner-checkpoint-test-') as folder:
                with self.small_run(folder) as (report, output):
                    def execute(name, *args, **kwargs):
                        if name == phase:
                            raise KeyboardInterrupt
                        return real_execute(name, *args, **kwargs)
                    with ExitStack() as stack:
                        stack.enter_context(patch.object(run_tests, 'esegui', side_effect=execute))
                        if phase == 'options payload compilation':
                            stack.enter_context(patch.object(run_tests, 'compila_opzioni',
                                                             side_effect=KeyboardInterrupt))
                        with self.assertRaises(KeyboardInterrupt):
                            run_tests.main()
                    self.assertTrue(report.is_file(), 'interruption must leave a checkpoint')
                    data = json.loads(report.read_text())
                self.assertEqual((data['complete'], data['ok']), (False, False))
                self.assertEqual(data['active_suite'], phase)
                self.assertEqual([row['suite'] for row in data['suites']], finished)
                self.assertEqual((data['collected'], data['skipped'], data['executed_methods']),
                                 (2 * len(finished), len(finished), len(finished)))
                self.assertEqual((data['classe_b'], data['collected_classe_b']), ([], 0))
                self.assertNotIn('— PASS', output.getvalue())

    def test_interrupted_missing_compiler_collection_keeps_prior_counts(self):
        with tempfile.TemporaryDirectory(prefix='runner-checkpoint-test-') as folder:
            with self.small_run(folder) as (report, output):
                with patch.object(run_tests, 'compila_opzioni',
                                  return_value=(None, 'compiler missing', True)), \
                        patch.object(run_tests, 'conta_soltanto', side_effect=KeyboardInterrupt), \
                        self.assertRaises(KeyboardInterrupt):
                    run_tests.main()
                self.assertTrue(report.is_file(), 'collection must leave a checkpoint')
                data = json.loads(report.read_text())
            self.assertEqual((data['complete'], data['ok']), (False, False))
            self.assertEqual(data['active_suite'], 'options page (Unicorn)')
            self.assertEqual((data['collected'], data['skipped'], data['executed_methods']),
                             (6, 3, 3))
            self.assertEqual(len(data['suites']), 3)
            self.assertNotIn('— PASS', output.getvalue())

    def test_complete_pass_preserves_counts_and_clears_active_suite(self):
        with tempfile.TemporaryDirectory(prefix='runner-checkpoint-test-') as folder:
            with self.small_run(folder) as (report, output):
                self.assertEqual(run_tests.main(), 0)
                data = json.loads(report.read_text())
            self.assertEqual((data.get('complete'), data['ok']), (True, True))
            self.assertIsNone(data['active_suite'])
            self.assertEqual((data['collected'], data['skipped'], data['executed_methods']),
                             (8, 4, 4))
            self.assertEqual((data['collected_classe_b'], data['skipped_classe_b'],
                              data['executed_methods_classe_b']), (2, 1, 1))
            self.assertTrue(data['classe_a_ok'])
            self.assertTrue(data['classe_b_ok'])
            self.assertIn('Class A 8 + Class B 2) — PASS', output.getvalue())
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()),
                             ['result.json', 'source'])

    def test_failed_initial_replace_preserves_stale_report_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory(prefix='runner-checkpoint-test-') as folder:
            with self.small_run(folder) as (report, output):
                previous = '{"complete": true, "ok": true}\n'
                report.write_text(previous)
                with patch.object(run_tests.os, 'replace', side_effect=OSError('replace denied')), \
                        self.assertRaisesRegex(OSError, 'replace denied'):
                    run_tests.main()
                self.assertEqual(report.read_text(), previous)
            self.assertNotIn('— PASS', output.getvalue())
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()),
                             ['result.json', 'source'])

    def test_failed_later_replace_preserves_last_readable_checkpoint(self):
        real_replace = run_tests.os.replace
        with tempfile.TemporaryDirectory(prefix='runner-checkpoint-test-') as folder:
            with self.small_run(folder) as (report, output):
                def replace(source, destination):
                    pending = json.loads(Path(source).read_text())
                    if pending['active_suite'] == 'second':
                        raise OSError('replace denied')
                    return real_replace(source, destination)
                with patch.object(run_tests.os, 'replace', side_effect=replace), \
                        self.assertRaisesRegex(OSError, 'replace denied'):
                    run_tests.main()
                data = json.loads(report.read_text())
            self.assertEqual((data['complete'], data['ok'], data['active_suite']),
                             (False, False, None))
            self.assertEqual([row['suite'] for row in data['suites']], ['first'])
            self.assertEqual((data['collected'], data['skipped'], data['executed_methods']),
                             (2, 1, 1))
            self.assertNotIn('— PASS', output.getvalue())
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()),
                             ['result.json', 'source'])

    def test_failed_final_replace_never_prints_pass(self):
        real_replace = run_tests.os.replace
        with tempfile.TemporaryDirectory(prefix='runner-checkpoint-test-') as folder:
            with self.small_run(folder) as (report, output):
                def replace(source, destination):
                    if json.loads(Path(source).read_text())['complete']:
                        raise OSError('final replace denied')
                    return real_replace(source, destination)
                with patch.object(run_tests.os, 'replace', side_effect=replace), \
                        self.assertRaisesRegex(OSError, 'final replace denied'):
                    run_tests.main()
                data = json.loads(report.read_text())
            self.assertEqual((data['complete'], data['ok'], data['active_suite']),
                             (False, False, None))
            self.assertEqual((data['collected'], data['collected_classe_b']), (8, 2))
            self.assertNotIn('— PASS', output.getvalue())
            self.assertEqual(sorted(p.name for p in Path(folder).iterdir()),
                             ['result.json', 'source'])

    def test_without_json_keeps_verdict_and_creates_no_report_files(self):
        with tempfile.TemporaryDirectory(prefix='runner-checkpoint-test-') as folder:
            with self.small_run(folder, json_report=False) as (report, output):
                before = {p.relative_to(folder) for p in Path(folder).rglob('*')}
                self.assertEqual(run_tests.main(), 0)
                self.assertFalse(report.exists())
                self.assertEqual({p.relative_to(folder) for p in Path(folder).rglob('*')}, before)
            self.assertIn('Class A 8 + Class B 2) — PASS', output.getvalue())


class RunnerInventoryTests(unittest.TestCase):
    def test_sgp131_test_modules_have_an_explicit_runner_classification(self):
        actual = {p.stem for p in (run_tests.SOURCE / 'sgp131').glob('test_*.py')}
        selected = {arg.split('.')[1] for row in
                    (*run_tests.SUITE, *run_tests.SUITE_CLASSE_B)
                    for arg in row[2] if arg.startswith('sgp131.test_')}
        local_only = set(run_tests.LOCAL_ONLY_SGP131_TESTS)
        self.assertFalse(selected & local_only,
                         'a test cannot be both registered and local-only')
        self.assertEqual(actual, selected | local_only,
                         'classify each new sgp131 test module explicitly')
        self.assertTrue(all(run_tests.LOCAL_ONLY_SGP131_TESTS.values()))

    def test_split_synthetic_selection_is_registered_once(self):
        matches = [row for row in run_tests.SUITE
                   if row[0] == '1.3.1 audited synthetic regressions']
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][2][2:], run_tests.AUDITED_SYNTHETIC_SELECTORS)
        self.assertEqual(len(set(run_tests.AUDITED_SYNTHETIC_SELECTORS)),
                         len(run_tests.AUDITED_SYNTHETIC_SELECTORS))


if __name__ == '__main__':
    unittest.main()
