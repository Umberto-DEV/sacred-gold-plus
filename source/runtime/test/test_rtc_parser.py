"""Run the real C++ RTC parser/default regression checks in Class A."""
from pathlib import Path
import subprocess
import sys
import unittest


class RtcParserTests(unittest.TestCase):
    def test_compiled_default_and_calendar_checks(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name('run_rtc_tests.py'))],
            capture_output=True, text=True, timeout=80)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertRegex(result.stdout, r'^PASS [1-9][0-9]* RTC checks\s*$')


if __name__ == '__main__':
    unittest.main()
