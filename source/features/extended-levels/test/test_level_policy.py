"""Exhaustive host tests for the extended-level persistent latch model."""
from __future__ import annotations

import ctypes as C
from pathlib import Path
import subprocess
import tempfile
import unittest


FEATURE = Path(__file__).resolve().parents[1]
INVALID, UNCHANGED, CHANGED = 0, 1, 2
PERMANENT, EGG = 1, 2


class State(C.Structure):
    _fields_ = [("over100", C.c_ubyte), ("peak", C.c_ubyte)]


def pair(value: State) -> tuple[int, int]:
    return value.over100, value.peak


def normalized_oracle(over100: int, peak: int) -> tuple[int, int] | None:
    if over100 not in (0, 1) or peak < 1:
        return None
    if (over100 == 0 and peak > 100) or (over100 == 1 and peak > 150):
        return None
    if over100 or peak >= 100:
        return 1, max(100, peak)
    return 0, peak


class LevelPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="sgp-level-policy-")
        cls.addClassCleanup(cls.temp.cleanup)
        library = Path(cls.temp.name) / "level_policy.dylib"
        subprocess.run(
            [
                "clang", "-shared", "-fPIC", "-std=c99", "-Wall", "-Wextra",
                "-Werror", "-O2", str(FEATURE / "level_policy.c"), "-o", str(library),
            ],
            check=True, capture_output=True, text=True,
        )
        cls.c = C.CDLL(str(library))
        cls.c.sgp_level_normalize.argtypes = [State, C.POINTER(State)]
        cls.c.sgp_level_normalize.restype = C.c_int
        cls.c.sgp_level_observe.argtypes = [State, C.c_uint, C.c_uint, C.POINTER(State)]
        cls.c.sgp_level_observe.restype = C.c_int
        cls.c.sgp_level_cap.argtypes = [State]
        cls.c.sgp_level_cap.restype = C.c_uint

    def normalize(self, state: State) -> tuple[int, State]:
        out = State(0xA5, 0x5A)
        result = self.c.sgp_level_normalize(state, C.byref(out))
        return result, out

    def observe(self, state: State, level: int, flags: int) -> tuple[int, State]:
        out = State(0xA5, 0x5A)
        result = self.c.sgp_level_observe(state, level, flags, C.byref(out))
        return result, out

    def test_normalization_exhausts_every_byte_pair(self):
        for over100 in range(256):
            for peak in range(256):
                expected = normalized_oracle(over100, peak)
                result, out = self.normalize(State(over100, peak))
                if expected is None:
                    self.assertEqual(result, INVALID, (over100, peak))
                    self.assertEqual(pair(out), (0xA5, 0x5A), (over100, peak))
                else:
                    self.assertEqual(result, CHANGED if expected != (over100, peak) else UNCHANGED)
                    self.assertEqual(pair(out), expected)

    def test_unlock_boundary_and_peak_are_monotonic(self):
        state = State(0, 98)
        for level, expected_result, expected in (
            (99, CHANGED, (0, 99)),
            (100, CHANGED, (1, 100)),
            (101, CHANGED, (1, 101)),
            (127, CHANGED, (1, 127)),
            (128, CHANGED, (1, 128)),
            (149, CHANGED, (1, 149)),
            (150, CHANGED, (1, 150)),
            (149, UNCHANGED, (1, 150)),
            (1, UNCHANGED, (1, 150)),
        ):
            result, out = self.observe(state, level, PERMANENT)
            self.assertEqual((result, pair(out)), (expected_result, expected))
            state = out

    def test_acquiring_level_100_or_higher_unlocks_directly(self):
        for level in (100, 101, 127, 128, 149, 150):
            with self.subTest(level=level):
                result, out = self.observe(State(0, 17), level, PERMANENT)
                self.assertEqual(result, CHANGED)
                self.assertEqual(pair(out), (1, level))
                self.assertEqual(self.c.sgp_level_cap(out), 150)

    def test_eggs_and_nonpersistent_copies_are_noops(self):
        for state in (State(0, 99), State(1, 120)):
            for level in (1, 99, 100, 150):
                for flags in (0, EGG, PERMANENT | EGG):
                    with self.subTest(state=pair(state), level=level, flags=flags):
                        result, out = self.observe(state, level, flags)
                        self.assertEqual(result, UNCHANGED)
                        self.assertEqual(pair(out), pair(state))

    def test_invalid_inputs_leave_output_untouched(self):
        cases = (
            (State(0, 0), 1, PERMANENT),
            (State(2, 1), 1, PERMANENT),
            (State(0, 100), 100, PERMANENT),
            (State(0, 101), 1, PERMANENT),
            (State(1, 99), 1, PERMANENT),
            (State(1, 151), 1, PERMANENT),
            (State(0, 1), 0, PERMANENT),
            (State(0, 1), 151, PERMANENT),
            (State(0, 1), 1, 4),
        )
        for state, level, flags in cases:
            with self.subTest(state=pair(state), level=level, flags=flags):
                result, out = self.observe(state, level, flags)
                self.assertEqual(result, INVALID)
                self.assertEqual(pair(out), (0xA5, 0x5A))
        self.assertEqual(self.c.sgp_level_observe(State(0, 1), 1, PERMANENT, None), INVALID)
        self.assertEqual(self.c.sgp_level_normalize(State(0, 1), None), INVALID)

    def test_exhaustive_canonical_transition_properties(self):
        states = [State(0, peak) for peak in range(1, 100)]
        states += [State(1, peak) for peak in range(100, 151)]
        for state in states:
            self.assertEqual(self.c.sgp_level_cap(state), 150 if state.over100 else 100)
            for level in range(1, 151):
                for flags in range(4):
                    result, out = self.observe(state, level, flags)
                    self.assertIn(result, (UNCHANGED, CHANGED))
                    self.assertGreaterEqual(out.peak, state.peak)
                    self.assertGreaterEqual(out.over100, state.over100)
                    self.assertIn(self.c.sgp_level_cap(out), (100, 150))
                    again_result, again = self.observe(out, level, flags)
                    self.assertEqual(again_result, UNCHANGED)
                    self.assertEqual(pair(again), pair(out))

    def test_public_contract_has_no_new_game_or_phase_101_switch(self):
        header = (FEATURE / "level_policy.h").read_text()
        self.assertIn("SGP_LEVEL_UNLOCK 100u", header)
        self.assertNotIn("phase", header.lower())
        self.assertNotIn("new_game", header.lower())


if __name__ == "__main__":
    unittest.main()
