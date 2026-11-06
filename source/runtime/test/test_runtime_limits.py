from pathlib import Path
import os
import subprocess
import tempfile
import unittest


RUNTIME = Path(__file__).resolve().parents[1]


class RuntimeLimitsTests(unittest.TestCase):
    def test_cpp_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            binary = Path(temp) / "runtime-limits"
            compiler = os.environ.get("CXX", "c++")
            build = subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-I", str(RUNTIME), str(Path(__file__).with_suffix(".cpp")),
                 "-o", str(binary)],
                text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            run = subprocess.run([str(binary), temp], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)


if __name__ == "__main__":
    unittest.main()
