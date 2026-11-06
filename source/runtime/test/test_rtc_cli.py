"""ROM-free rejection/argument tests for an explicitly supplied public runtime."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

BINARY = None


class RtcCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if BINARY is None:
            raise unittest.SkipTest('supply the public runtime binary as the script argument')

    def invoke(self, arguments):
        return subprocess.run([str(BINARY), *arguments], text=True,
                              capture_output=True, timeout=10)

    def test_valid_clock_reaches_required_argument_check(self):
        # Catches a CLI that never recognizes --rtc, without starting a guest.
        for value in ('2000-02-29T00:00:00', '2026-09-05T12:00:00',
                      '2099-12-31T23:59:59'):
            with self.subTest(value=value):
                result = self.invoke(['--rtc', value])
                self.assertEqual(result.returncode, 1)
                self.assertIn('Usage:', result.stderr)
                self.assertNotIn('Unknown option', result.stderr)

    def test_invalid_clock_precedes_output_and_input_reads(self):
        # A misplaced validation after Harness construction would create out
        # or fail while reading the nonexistent ROM instead of rejecting RTC.
        cases = [(['--rtc', '2026-02-29T12:00:00'], 'Invalid --rtc'),
                 (['--rtc', '2100-01-01T00:00:00'], 'Invalid --rtc'),
                 (['--rtc', '2026-09-05T24:00:00'], 'Invalid --rtc'),
                 (['--rtc', '2026-09-05T12:00:00Z'], 'Invalid --rtc'),
                 (['--rtc', ''], 'Invalid --rtc'),
                 (['--rtc'], 'Missing value for --rtc'),
                 (['--rtc', '2026-09-05T12:00:00', '--rtc',
                   '2026-09-05T12:00:00'], 'Duplicate --rtc')]
        with tempfile.TemporaryDirectory(prefix='rtc-cli-') as temporary:
            parent = pathlib.Path(temporary)
            for index, (arguments, error) in enumerate(cases):
                with self.subTest(arguments=arguments):
                    out = parent / str(index) / 'output'
                    result = self.invoke(['--rom', str(parent / 'absent.nds'),
                                          '--sram', str(parent / 'absent.sav'),
                                          '--out', str(out), *arguments])
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(error, result.stderr)
                    self.assertFalse(out.parent.exists())

    def test_usage_and_unrelated_option_rejection_remain(self):
        self.assertIn('Usage:', self.invoke([]).stderr)
        self.assertIn('Unknown option --not-an-option',
                      self.invoke(['--not-an-option']).stderr)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('Usage: test_rtc_cli.py /path/to/built/hg_runtime')
    BINARY = pathlib.Path(sys.argv.pop(1)).resolve()
    unittest.main()
