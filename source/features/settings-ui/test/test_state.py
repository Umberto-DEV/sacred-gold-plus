"""Pure C reducer tests; no emulator, game data, owner mocks or extra dependencies."""
import ctypes as C
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
U8, U16, U32 = C.c_ubyte, C.c_ushort, C.c_uint
A, B, RIGHT, LEFT, UP, DOWN, R, L, X, Y = 1, 2, 16, 32, 64, 128, 256, 512, 1024, 2048
NOOP, CHANGED, APPLY, DISCARD, APPLIED = range(5)
ROOT_VIEW, SELECTOR, INFO, SEARCH, EXIT, CONFIRM, ERROR = range(7)

class Native(C.Structure):
    _fields_ = [(n, U8) for n in ('text', 'scene', 'style', 'audio', 'button', 'frame')]
class Plus(C.Structure):
    _fields_ = [(n, U8) for n in ('difficulty', 'wild', 'animation', 'npc', 'wifi')]
class ShinySnapshot(C.Structure):
    _fields_ = [(n, U32) for n in ('epoch', 'context', 'revision')] + [
        ('target', U16), ('denominator', U16)] + [(n, U8) for n in (
        'available', 'mode', 'chain', 'charge', 'method_mask', 'status', 'method', 'reserved')
        ] + [('counts', U8 * 5), ('padding', U8 * 3)]
class ShinyDraft(C.Structure):
    _fields_ = [(n, U32) for n in ('epoch', 'context', 'revision')] + [
        ('target', U16), ('mode', U8), ('method', U8), ('search', U8), ('reserved', U8 * 3)]
class Draft(C.Structure):
    _fields_ = [('native', Native), ('plus', Plus), ('shiny', ShinyDraft)]
class Snapshot(C.Structure):
    _fields_ = [('native', Native), ('plus', Plus), ('shiny', ShinySnapshot),
                ('candidates', (U16 * 12) * 5), ('editable_rows', U32)]
class State(C.Structure):
    _fields_ = [('snapshot', Snapshot), ('draft', Draft), ('dirty_fields', U32)] + [
        (n, U16) for n in ('row', 'selector_cursor', 'selector_pending', 'selector_origin')] + [
        (n, U8) for n in ('view', 'return_view', 'info_origin', 'selector_row',
                          'search_row', 'choice', 'dirty_groups', 'notice', 'owner_status',
                          'release_gate', 'sample_ready', 'awaiting_apply')]

class ModelCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='sgp-settings-test-')
        lib = Path(cls.tmp.name) / 'settings.dylib'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared',
                        '-fPIC', '-O2', str(ROOT / 'state.c'), '-o', str(lib)], check=True)
        cls.lib = C.CDLL(str(lib))
        cls.lib.settings_init.argtypes = [C.POINTER(State), C.POINTER(Snapshot)]
        cls.lib.settings_sample.argtypes = [C.POINTER(State), U32, U32, U32]
        cls.lib.settings_step.argtypes = [C.POINTER(State), U32, U32]
        cls.lib.settings_apply_result.argtypes = [C.POINTER(State), U32]
        cls.lib.settings_keys.argtypes = [U32, U32, U32]
        cls.lib.settings_keys.restype = U32
        for name in ('visible_rows', 'effective_charge', 'can_prepare', 'selector_count'):
            getattr(cls.lib, 'settings_' + name).argtypes = [C.POINTER(State)]
        cls.lib.settings_row_enabled.argtypes = [C.POINTER(State), U32]
        cls.lib.settings_selector_value.argtypes = [C.POINTER(State), U32]
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
    def make(self, mode=1, charge=40, editable=(1 << 14) - 1):
        p = Snapshot()
        p.editable_rows = editable
        p.shiny.available = 1
        p.shiny.mode = mode
        p.shiny.target = 493
        p.shiny.epoch, p.shiny.context, p.shiny.revision = 11, 12, 13
        p.shiny.method_mask = 0b10101
        p.shiny.charge = charge
        for method in (0, 2, 4):
            p.shiny.counts[method] = 2
            p.candidates[method][0], p.candidates[method][1] = 25, 493
        s = State()
        self.lib.settings_init(C.byref(s), C.byref(p))
        self.lib.settings_sample(C.byref(s), 0, 1, 0)
        self.lib.settings_step(C.byref(s), 0, 0)
        return s
    def key(self, s, new=0, repeat=0, held=None, fresh=1, lid=0):
        self.lib.settings_sample(C.byref(s), new if held is None else held, fresh, lid)
        return self.lib.settings_step(C.byref(s), new, repeat)
    def press(self, s, key):
        self.key(s)  # release after transition
        return self.key(s, key)
    def prepare(self, s):
        s.row = 13
        self.press(s, A)
        self.press(s, DOWN)
        self.press(s, DOWN)
        return self.press(s, A)

class StateTests(ModelCase):
    def test_snapshot_draft_types_and_exact_values(self):
        s = self.make()
        self.assertEqual((s.draft.shiny.target, s.draft.shiny.epoch), (493, 11))
        self.assertEqual(bytes(s.snapshot.shiny), bytes(self.make().snapshot.shiny))
        self.assertEqual((C.sizeof(ShinySnapshot), C.sizeof(ShinyDraft)), (32, 20))
        self.assertEqual(s.dirty_groups, 0)

    def test_section_jump_uses_previous_next_section_from_every_row(self):
        for row in range(14):
            for key in (L, R):
                s = self.make(); s.row = row
                self.key(s, key)
                expected = (0 if row < 11 else 6) if key == L else (6 if row < 6 else 11)
                if key == L and row < 6: expected = row
                if key == R and row >= 11: expected = row
                self.assertEqual(s.row, expected, (row, key))

    def test_arm_thumb_object_has_no_external_symbols_or_data(self):
        spec = importlib.util.spec_from_file_location(
            'settings_object_loader', ROOT.parent / 'options/tools/carica_text.py')
        loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loader)
        with tempfile.TemporaryDirectory(prefix='sgp-settings-arm-') as tmp:
            obj = Path(tmp) / 'state.o'
            flags = ['--target=armv5te-none-eabi', '-mcpu=arm946e-s', '-mthumb', '-Oz',
                     '-std=c11', '-ffreestanding', '-fno-builtin', '-fno-stack-protector',
                     '-fno-jump-tables', '-fno-unwind-tables', '-fno-asynchronous-unwind-tables',
                     '-Wall', '-Wextra', '-Werror']
            subprocess.run(['clang', *flags, '-c', str(ROOT / 'state.c'), '-o', str(obj)],
                           check=True, capture_output=True)
            try:
                blob, symbols = loader.load_text(obj.read_bytes(), 0x02300000)
            except ValueError as error:
                self.fail(str(error))
            self.assertGreater(len(blob), 0)
            self.assertTrue(all(v & 1 for k, v in symbols.items() if k.startswith('settings_')))

    def test_continuous_sections_and_scalar_clamps(self):
        s = self.make()
        for _ in range(20): self.key(s, DOWN)
        self.assertEqual(s.row, 13)
        for expected in (6, 0, 0, 0):
            self.key(s, L)
            self.assertEqual(s.row, expected)
        for expected in (6, 11, 11):
            self.key(s, R)
            self.assertEqual(s.row, expected)
        s.row = 0
        for _ in range(5): self.key(s, RIGHT)
        self.assertEqual((s.draft.native.text, s.row), (2, 0))
        for _ in range(5): self.key(s, LEFT)
        self.assertEqual(s.draft.native.text, 0)
        s.row = 5
        for _ in range(25): self.key(s, RIGHT)
        self.assertEqual(s.draft.native.frame, 19)
        s.row = 10
        for _ in range(4): self.key(s, RIGHT)
        self.assertEqual(s.draft.plus.wifi, 2)
        self.assertEqual(s.dirty_groups, 3)
        self.assertEqual(s.dirty_fields, (1 << 5) | (1 << 10))

    def test_each_logical_scalar_domain_clamps_and_reverts_dirty(self):
        fields = [(0, 'native', 'text', 2), (1, 'native', 'scene', 1),
                  (2, 'native', 'style', 1), (3, 'native', 'audio', 1),
                  (4, 'native', 'button', 1), (5, 'native', 'frame', 19),
                  (6, 'plus', 'difficulty', 1), (7, 'plus', 'wild', 1),
                  (8, 'plus', 'animation', 1), (9, 'plus', 'npc', 1),
                  (10, 'plus', 'wifi', 2), (11, 'shiny', 'mode', 1)]
        for row, group, field, maximum in fields:
            with self.subTest(row=row):
                s = self.make(mode=0); s.row = row
                for _ in range(maximum + 2): self.key(s, RIGHT)
                self.assertEqual(getattr(getattr(s.draft, group), field), maximum)
                self.assertEqual(s.dirty_fields, 1 << row)
                for _ in range(maximum + 2): self.key(s, LEFT)
                self.assertEqual(getattr(getattr(s.draft, group), field), 0)
                self.assertEqual((s.dirty_groups, s.dirty_fields), (0, 0))

    def test_classic_preserves_hidden_target_and_cursor_id(self):
        s = self.make()
        s.row = 11
        self.key(s, LEFT)
        self.assertEqual(self.lib.settings_visible_rows(C.byref(s)), 12)
        self.assertEqual(s.draft.shiny.target, 493)
        self.key(s, RIGHT)
        self.assertEqual((s.row, s.draft.shiny.target), (11, 493))
        self.assertEqual(self.lib.settings_visible_rows(C.byref(s)), 14)
        s.row = 13
        s.draft.shiny.mode = 0  # defensive clamp after visibility change
        self.key(s)
        self.assertEqual(s.row, 11)

    def test_a_target_selects_locally_and_b_restores_origin(self):
        s = self.make()
        s.row = 12
        self.assertEqual(self.press(s, A), CHANGED)
        self.assertEqual((s.view, s.selector_pending), (SELECTOR, 493))
        self.press(s, UP)
        self.assertEqual((s.selector_pending, s.draft.shiny.target), (25, 493))
        self.press(s, X)
        self.assertEqual(s.view, SELECTOR)
        self.press(s, B)
        self.assertEqual((s.view, s.row, s.draft.shiny.target), (ROOT_VIEW, 12, 493))
        self.assertEqual(s.selector_pending, s.selector_origin)
        self.press(s, A)
        self.press(s, UP)
        self.assertEqual(self.press(s, A), CHANGED)
        self.assertEqual((s.view, s.row, s.draft.shiny.target), (ROOT_VIEW, 12, 25))
        self.assertEqual(s.dirty_groups, 4)
        self.assertEqual(s.awaiting_apply, 0)

    def test_scalar_selector_cancel_preserves_earlier_global_draft(self):
        s = self.make()
        self.key(s, RIGHT)
        self.press(s, A)
        self.press(s, DOWN)
        self.press(s, B)
        self.assertEqual((s.view, s.draft.native.text), (ROOT_VIEW, 1))
        self.press(s, Y)
        self.press(s, X)
        self.press(s, B)
        self.assertEqual((s.view, s.row, s.draft.native.text), (ROOT_VIEW, 0, 1))

    def test_prepare_search_is_not_apply_or_encounter(self):
        for charge in (0, 39, 40):
            with self.subTest(charge=charge):
                s = self.make(charge=charge)
                original = bytes(s.snapshot)
                self.prepare(s)
                self.assertEqual(s.draft.shiny.search, int(charge == 40))
                self.assertEqual(s.view, ROOT_VIEW if charge == 40 else SEARCH)
                self.assertEqual(bytes(s.snapshot), original)
                self.assertEqual(s.awaiting_apply, 0)
        s = self.make()
        self.prepare(s)
        self.assertEqual((s.row, s.dirty_groups, s.dirty_fields), (13, 4, 1 << 15))

    def test_mode_target_method_invalidate_prepared_search(self):
        for field in ('mode', 'target', 'method'):
            with self.subTest(field=field):
                s = self.make()
                self.prepare(s)
                self.assertEqual(s.draft.shiny.search, 1)
                s.row = {'mode': 11, 'target': 12, 'method': 13}[field]
                if field == 'mode': self.press(s, LEFT)
                elif field == 'target':
                    self.press(s, A); self.press(s, UP); self.press(s, A)
                else:
                    self.press(s, A); self.press(s, DOWN); self.press(s, RIGHT)
                self.assertEqual(s.draft.shiny.search, 0)
                if field != 'method':
                    self.assertEqual(self.lib.settings_effective_charge(C.byref(s)), 0)

    def test_search_requires_pro_eligible_target_available_method_and_charge(self):
        for change in ('classic', 'target_none', 'target_absent', 'method', 'changed_target', 'changed_mode'):
            with self.subTest(change=change):
                s = self.make()
                if change == 'classic': s.draft.shiny.mode = 0
                if change == 'target_none': s.draft.shiny.target = 0
                if change == 'target_absent': s.draft.shiny.target = 150
                if change == 'method': s.draft.shiny.method = 1
                if change == 'changed_target': s.draft.shiny.target = 25
                if change == 'changed_mode': s.snapshot.shiny.mode = 0
                self.assertFalse(self.lib.settings_can_prepare(C.byref(s)))
        self.assertTrue(self.lib.settings_can_prepare(C.byref(self.make())))

    def test_empty_candidates_clear_and_recover(self):
        s = self.make()
        s.snapshot.shiny.counts[0] = 0
        s.row = 12
        self.press(s, A)
        self.assertEqual((s.view, s.selector_pending, s.notice), (SELECTOR, 0, 2))
        self.press(s, A)
        self.assertEqual((s.row, s.draft.shiny.target), (12, 0))
        self.assertEqual(self.lib.settings_can_prepare(C.byref(s)), 0)

    def test_exit_continue_default_and_apply_cancel_default(self):
        s = self.make()
        self.assertEqual(self.press(s, B), DISCARD)
        self.key(s, RIGHT)
        self.press(s, B)
        self.assertEqual((s.view, s.choice), (EXIT, 2))
        self.press(s, A)
        self.assertEqual((s.view, s.draft.native.text), (ROOT_VIEW, 1))
        self.press(s, X)
        self.assertEqual((s.view, s.choice), (CONFIRM, 1))
        self.press(s, A)
        self.assertEqual(s.view, ROOT_VIEW)
        self.press(s, X)
        self.press(s, LEFT)
        self.assertEqual(self.press(s, A), APPLY)
        self.assertEqual(s.awaiting_apply, 1)
        self.assertEqual(self.press(s, A), NOOP)

    def test_owner_failure_preserves_draft_and_success_is_only_status(self):
        s = self.make()
        self.key(s, RIGHT)
        draft, snapshot = bytes(s.draft), bytes(s.snapshot)
        self.press(s, X); self.press(s, LEFT); self.press(s, A)
        self.assertEqual(self.lib.settings_apply_result(C.byref(s), 2), CHANGED)
        self.assertEqual((s.view, s.owner_status), (ERROR, 2))
        self.assertEqual((bytes(s.draft), bytes(s.snapshot)), (draft, snapshot))
        self.press(s, B)
        self.assertEqual((s.view, s.row), (ROOT_VIEW, 0))
        self.press(s, X); self.press(s, LEFT); self.press(s, A)
        self.assertEqual(self.lib.settings_apply_result(C.byref(s), 0), APPLIED)
        self.assertEqual(bytes(s.snapshot), snapshot)

    def test_dirty_groups_and_native_with_unavailable_plus(self):
        s = self.make(editable=((1 << 6) - 1))
        s.row = 3
        self.key(s, RIGHT)
        self.assertEqual((s.dirty_groups, s.dirty_fields), (1, 1 << 3))
        for row in range(6, 14):
            s.row = row
            self.assertEqual(self.lib.settings_row_enabled(C.byref(s), row), 0)
            self.key(s, RIGHT)
            self.press(s, A)
            self.assertEqual(s.view, ROOT_VIEW)
        self.assertEqual(s.dirty_groups, 1)
        self.assertEqual(bytes(s.draft.plus), bytes(s.snapshot.plus))
        s.row = 3
        self.key(s, LEFT)
        self.assertEqual((s.dirty_groups, s.dirty_fields), (0, 0))

    def test_discard_restores_complete_draft_and_prepared_search(self):
        s = self.make()
        self.prepare(s)
        s.row = 0; self.press(s, RIGHT)
        s.row = 6; self.press(s, RIGHT)
        self.assertEqual(s.dirty_groups, 7)
        self.press(s, B); self.press(s, LEFT)
        self.assertEqual(self.press(s, A), DISCARD)
        self.assertEqual((s.dirty_fields, s.dirty_groups, s.draft.shiny.search), (0, 0, 0))
        self.assertEqual(bytes(s.draft.native), bytes(s.snapshot.native))
        self.assertEqual(bytes(s.draft.plus), bytes(s.snapshot.plus))

    def test_selector_queries_share_filtered_candidates_and_sparse_methods(self):
        s = self.make()
        self.assertEqual(self.lib.settings_selector_count(C.byref(s)), 0)
        s.row = 12; self.press(s, A)
        self.assertEqual(self.lib.settings_selector_count(C.byref(s)), 3)
        self.assertEqual([self.lib.settings_selector_value(C.byref(s), i) for i in range(4)],
                         [0, 25, 493, 0])
        self.press(s, B)
        s.row = 13; self.press(s, A); self.press(s, DOWN); self.press(s, A)
        self.assertEqual(self.lib.settings_selector_count(C.byref(s)), 3)
        self.assertEqual([self.lib.settings_selector_value(C.byref(s), i) for i in range(3)],
                         [0, 2, 4])

    def test_candidate_bounds_species_width_and_method_mask(self):
        s = self.make()
        s.snapshot.shiny.counts[0] = 255
        s.snapshot.candidates[0][1] = 65535
        s.snapshot.candidates[0][11] = 493
        s.row = 12; self.press(s, A)
        self.assertEqual(s.selector_pending, 493)
        self.press(s, UP)
        self.assertEqual(s.selector_pending, 25)
        for _ in range(20): self.press(s, DOWN)
        self.assertEqual((s.selector_cursor, s.selector_pending), (2, 493))
        self.press(s, B)
        s.row = 13; self.press(s, A); self.press(s, DOWN)
        self.press(s, A)
        for _ in range(9): self.press(s, DOWN)
        self.assertEqual(s.selector_pending, 4)
        self.press(s, B)
        self.assertEqual(s.draft.shiny.method, 0)

    def test_search_selector_returns_to_search_same_field(self):
        s = self.make(); s.row = 13
        self.press(s, A); self.press(s, A)
        self.press(s, UP); self.press(s, A)
        self.assertEqual((s.view, s.row, s.search_row, s.draft.shiny.target), (SEARCH, 13, 0, 25))
        self.press(s, DOWN); self.press(s, RIGHT)
        self.assertEqual(s.draft.shiny.method, 2)
        self.press(s, Y); self.press(s, B)
        self.assertEqual((s.view, s.search_row), (SEARCH, 1))
        self.press(s, B)
        self.assertEqual((s.view, s.row), (ROOT_VIEW, 13))

if __name__ == '__main__': unittest.main()
