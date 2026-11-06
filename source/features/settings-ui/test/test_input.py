import ctypes as C
import unittest
from test_state import (ModelCase, A, B, R, L, X, Y, UP, DOWN, LEFT, RIGHT,
                        NOOP, ROOT_VIEW, SELECTOR, INFO, SEARCH, EXIT, CONFIRM, ERROR)

CANCELLED = 1 << 31  # documented software provenance, not a physical key

class InputTests(ModelCase):
    def test_real_a_survives_l_a_and_lr_cancel(self):
        keys = self.lib.settings_keys
        self.assertEqual(keys(A, L, 1), L)
        self.assertEqual(keys(0, R, 1), R)
        self.assertEqual(keys(A, A | L, 1), A | L)
        self.assertEqual(keys(A, L | R, 1), CANCELLED)
        self.assertEqual(keys(A, L, 3), L)
        self.assertEqual(keys(X | Y, 0, 1), X | Y)
        self.assertEqual(keys(UP | DOWN | LEFT | RIGHT, 0, 0), CANCELLED)
        s = self.make(); s.row = 6
        self.key(s, keys(A, A | L, 1))
        self.assertEqual((s.view, s.row), (SELECTOR, 6))

    def test_normalized_opposed_new_masks_cannot_revive_repeat(self):
        for new, repeat, row, mode in (
                (UP | DOWN, DOWN, 4, 0),
                (LEFT | RIGHT, RIGHT, 0, 0),
                (L | R, DOWN, 4, 0),
                (L | R, RIGHT, 0, 1)):
            with self.subTest(new=new, repeat=repeat, mode=mode):
                s = self.make(); s.row = row
                mapped = new | (A if mode else 0)
                nk = self.lib.settings_keys(mapped, new, mode)
                rk = self.lib.settings_keys(repeat, repeat, mode)
                before = (s.row, s.view, bytes(s.draft), bytes(s.snapshot))
                self.assertEqual(self.key(s, nk, repeat=rk, held=new), NOOP)
                self.assertEqual((s.row, s.view, bytes(s.draft), bytes(s.snapshot)), before)

    def test_normalized_real_a_beats_canceled_pairs_and_repeat(self):
        for pair in (UP | DOWN, LEFT | RIGHT, L | R):
            for mode in (0, 1):
                with self.subTest(pair=pair, mode=mode):
                    s = self.make(); s.row = 4
                    nk = self.lib.settings_keys(A | pair, A | pair, mode)
                    rk = self.lib.settings_keys(DOWN, DOWN, mode)
                    self.key(s, nk, repeat=rk, held=A | pair)
                    self.assertEqual((s.view, s.row), (SELECTOR, 4))

    def test_normalized_unknown_bits_do_not_create_cancellation_provenance(self):
        for unknown in (1 << 12, 1 << 30, 1 << 31):
            with self.subTest(unknown=unknown):
                s = self.make(); s.row = 4
                nk = self.lib.settings_keys(unknown, unknown, 0)
                rk = self.lib.settings_keys(DOWN, DOWN, 0)
                self.key(s, nk, repeat=rk, held=unknown)
                self.assertEqual((s.row, s.view), (5, ROOT_VIEW))
        s = self.make()
        rk = self.lib.settings_keys(UP | DOWN, UP | DOWN, 0)
        self.assertEqual(self.key(s, self.lib.settings_keys(0, 0, 0), repeat=rk), NOOP)
        self.assertEqual(s.row, 0)

    def test_held_confirm_and_lid_resume(self):
        s = self.make()
        self.key(s, A)
        self.assertEqual(s.view, SELECTOR)
        self.assertEqual(self.key(s, A, held=A), NOOP)
        self.assertEqual(self.key(s, B, held=A | B), NOOP)
        self.assertEqual(self.key(s, B, held=0, fresh=0), NOOP)
        self.assertEqual(s.view, SELECTOR)
        self.key(s, lid=1, fresh=0)
        self.key(s, B, held=0, fresh=0)
        self.assertEqual(s.view, SELECTOR)
        self.key(s)
        self.key(s, B)
        self.assertEqual(s.view, ROOT_VIEW)
        self.assertEqual(self.key(s, A, held=A), NOOP)
        self.key(s)
        self.key(s, A)
        self.assertEqual(s.view, SELECTOR)

    def test_sample_is_single_consumed_and_no_sample_cannot_release(self):
        s = self.make()
        self.key(s, DOWN)
        self.assertEqual(s.row, 1)
        self.assertEqual(self.lib.settings_step(C.byref(s), DOWN, 0), NOOP)
        self.assertEqual(s.row, 1)
        self.key(s, A)
        self.lib.settings_step(C.byref(s), 0, 0)
        self.assertTrue(s.release_gate)

    def test_repeated_directions_only_priorities_and_opposites(self):
        s = self.make()
        self.key(s, repeat=A | B | X | Y | L | R)
        self.assertEqual(s.view, ROOT_VIEW)
        self.key(s, repeat=DOWN)
        self.assertEqual(s.row, 1)
        self.key(s, UP, repeat=DOWN)
        self.assertEqual(s.row, 0)
        self.key(s, DOWN | UP | L | R)
        self.assertEqual(s.row, 0)
        self.key(s, X | Y | DOWN)
        self.assertEqual(s.view, CONFIRM)
        self.press(s, B | A)
        self.assertEqual(s.view, ROOT_VIEW)
        self.press(s, A | X)
        self.assertEqual(s.view, SELECTOR)

    def test_touch_is_noop_in_all_settings_states(self):
        s = self.make()
        for view in (ROOT_VIEW, SELECTOR, INFO, SEARCH, EXIT, CONFIRM, ERROR):
            s.view = view
            before = (bytes(s.draft), bytes(s.snapshot), s.row, s.view)
            self.assertEqual(self.key(s, 1 << 12, repeat=1 << 31), NOOP)
            self.assertEqual((bytes(s.draft), bytes(s.snapshot), s.row, s.view), before)

if __name__ == '__main__': unittest.main()
