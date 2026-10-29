"""The runtime gate must reject a frozen suffix after a changing transition."""
import csv
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


if __name__ == '__main__':
    unittest.main()
