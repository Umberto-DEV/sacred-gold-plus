from pathlib import Path
import os
import subprocess
import tempfile
import unittest


RUNTIME = Path(__file__).resolve().parents[1]


class FrameObservationTests(unittest.TestCase):
    def test_cpp_frame_timing_and_scene_reader(self):
        with tempfile.TemporaryDirectory() as temp:
            binary = Path(temp) / "frame-observation"
            compiler = os.environ.get("CXX", "c++")
            build = subprocess.run(
                [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-I", str(RUNTIME), str(Path(__file__).with_name("frame_observation_test.cpp")),
                 "-o", str(binary)],
                text=True, capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stderr)
            run = subprocess.run([str(binary)], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)

    def test_session_labels_trace_state_as_initial(self):
        source = (RUNTIME / "main.cpp").read_text()
        self.assertIn("TracePCInitial=", source)
        self.assertNotIn('\\nTracePC=', source)


if __name__ == "__main__":
    unittest.main()
