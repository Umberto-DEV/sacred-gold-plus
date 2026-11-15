"""Runtime gates reject frozen execution and incomplete Repel visual evidence."""
import csv
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from verifiche.rileva_crash import esamina, main


class RuntimeGateTests(unittest.TestCase):
    def run_case(self, samples):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'frames.csv'
            with p.open('w') as f:
                writer = csv.writer(f)
                writer.writerow(('frame', 'arm9_pc', 'game_vblank_counter'))
                writer.writerows((i + 1, hex(pc), hex(vb))
                                 for i, (pc, vb) in enumerate(samples))
            result = esamina(p)
            with redirect_stdout(StringIO()):
                code = main([p])
            return result[0], code

    def test_exception_after_changing_pcs_with_already_stopped_vblank(self):
        # Actual failure shape: a transition stops vblank before the exception.
        transition = [(0x02004000 + i * 2, 123) for i in range(9)]
        self.assertEqual(self.run_case(transition + [(0xffff0108, 123)] * 100),
                         ('CRASH', 1))

    def test_non_exception_frozen_loop_also_fails_the_gate(self):
        transition = [(0x02004000 + i * 2, 123) for i in range(9)]
        self.assertEqual(self.run_case(transition + [(0x02008000, 123)] * 100),
                         ('BLOCCATO', 1))

    def test_brief_vector_visit_is_not_a_crash(self):
        self.assertEqual(self.run_case([(0xffff0108, 123)] * 59), ('VIVO', 0))

    def test_vector_samples_with_advancing_vblank_are_not_a_crash(self):
        self.assertEqual(self.run_case([(0xffff0108, i) for i in range(100)]),
                         ('VIVO', 0))

    def test_changing_pc_blocking_load_stays_inconclusive(self):
        self.assertEqual(self.run_case([(0x02004000 + i % 4 * 2, 123)
                                       for i in range(100)]), ('STALLO', 0))

    def test_empty_trace_is_never_success(self):
        self.assertEqual(self.run_case([]), ('VUOTO', 1))


class RepelVisualGateTests(unittest.TestCase):
    def run_gate(self, captures, steps=(3, 1, 0, 100)):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            with (directory / 'frames.csv').open('w') as handle:
                writer = csv.writer(handle)
                writer.writerow(('frame', 'arm9_pc', 'game_vblank_counter', 'repelSteps'))
                writer.writerows((frame, '0x02004000', frame, value)
                                 for frame, value in enumerate(steps, 1))
            for name, pixel in captures:
                (directory / name).write_bytes(b'P6\n1 1\n255\n' + pixel)
            return subprocess.run(
                [sys.executable, '-B', str(Path(__file__).with_name('collauda_repellente.py')),
                 '--corsa', str(directory)], capture_output=True, text=True, timeout=10)

    def test_missing_captures_cannot_pass_the_visual_gate(self):
        result = self.run_gate([])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('CADUTO  C3', result.stdout)

    def test_one_capture_cannot_establish_a_visual_change(self):
        result = self.run_gate([('before.ppm', b'\x00\x00\x00')])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('CADUTO  C3', result.stdout)

    def test_latest_alias_does_not_supply_a_second_capture(self):
        result = self.run_gate([('before.ppm', b'\x00\x00\x00'),
                                ('latest.ppm', b'\xff\xff\xff')])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('CADUTO  C3', result.stdout)

    def test_unchanged_captures_fail_even_when_rearming_is_recorded(self):
        result = self.run_gate([('before.ppm', b'\x00\x00\x00'),
                                ('after.ppm', b'\x00\x00\x00')])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('CADUTO  C3', result.stdout)

    def test_distinct_captures_and_rearming_pass_the_bounded_gate(self):
        result = self.run_gate([('before.ppm', b'\x00\x00\x00'),
                                ('after.ppm', b'\xff\xff\xff')])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('passato C3', result.stdout)
        self.assertIn('TUTTI I CANCELLI PASSATI', result.stdout)

    def test_visual_changes_do_not_replace_rearming(self):
        result = self.run_gate([('before.ppm', b'\x00\x00\x00'),
                                ('after.ppm', b'\xff\xff\xff')], steps=(3, 1, 0, 0))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('CADUTO  C4', result.stdout)


if __name__ == '__main__':
    unittest.main()
