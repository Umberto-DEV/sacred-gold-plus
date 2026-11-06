"""The compiled legend runtime against the real V4 window engine on Unicorn.

Class B: reads the private V4 ROMs in memory. Without them the suite skips with
a reason; SGP_CONTROLS_REQUIRE_INPUTS=1 turns a missing input into a failure.
The payload is compiled for declared TEST placements (bench.TEST_BASE) and a
declared TEST geometry; neither is a reserve or window assignment.
"""
import hashlib
import os
import struct
import tempfile
import unittest
from pathlib import Path

import bench
from sgp131 import controls

CHARMAP = Path(os.environ.get('SGP_CONTROLS_CHARMAP') or
               bench.REPOSITORY / 'local/tools/pokeheartgold/charmap.txt')
GEOMETRY = {'bgId': 4, 'left': 1, 'top': 18, 'width': 16, 'height': 2, 'palette': 13, 'baseTile': 955}
STATS_DRAW = 0x0208D179     # sub_0208D178, hooked by the inherited viewer (called, never replaced)
TEARDOWN = 0x0208C4E1       # sub_0208C4E0
_ROMS, _PAYLOADS = {}, {}


def rom(test, language):
    if language not in _ROMS:
        path, digest = bench.input_path(language)
        if path is None or not CHARMAP.is_file():
            reason = 'private V4 %s ROM or charmap not available' % language
            if os.environ.get(bench.REQUIRE) == '1':
                test.fail(reason)
            test.skipTest(reason)
        data = path.read_bytes()
        test.assertEqual(hashlib.sha256(data).hexdigest(), digest, language + ' input identity')
        _ROMS[language] = data
    return _ROMS[language]


def payload(test, language, geometry=GEOMETRY, enabled=1, base=bench.TEST_BASE):
    key = (language, tuple(sorted(geometry.items())), enabled, base)
    if key not in _PAYLOADS:
        with tempfile.TemporaryDirectory(prefix='summary-controls-') as work:
            _PAYLOADS[key] = controls.compile_payload(Path(work), base, language, CHARMAP, geometry, enabled)
    return _PAYLOADS[key]


class RuntimeCase(unittest.TestCase):
    language = 'EN'

    def make(self, language=None, geometry=GEOMETRY, enabled=1, base=bench.TEST_BASE, **summary):
        language = language or self.language
        data = rom(self, language)
        image, info = payload(self, language, geometry, enabled, base)
        test = bench.Bench(data, image, base)
        test.info = info
        test.stub(STATS_DRAW & ~1, lambda args, sp: test.log.append(('stats_draw', args[0])))
        test.stub(TEARDOWN & ~1, lambda args, sp: test.log.append(('native_teardown', args[0])))
        test.build_summary(**summary)
        test.update = lambda value=bench.SUMMARY: test.call(info['symbols']['sgp_summary_controls_update'] & ~1, value)
        test.destroy = lambda value=bench.SUMMARY: test.call(info['symbols']['sgp_summary_controls_destroy'] & ~1, value)
        test.entry = lambda name, value=bench.SUMMARY: test.call(info['symbols'][name] & ~1, value)
        return test

    def prints(self, test):
        return [entry for entry in test.log if entry[0] == 'print']


class LifetimeAndDrawing(RuntimeCase):
    def test_owner_create_redraw_destroy_once(self):
        test = self.make()
        expected = controls.encode_legend('EN', CHARMAP)
        for _ in range(3):
            result, preserved = test.update()
            self.assertTrue(preserved, 'AAPCS: r4-r11, SP and the canary line')
        owner, generation, window, redraws, enabled = test.state()[:5]
        self.assertEqual((owner, generation, redraws, enabled), (bench.SUMMARY, 1, 3, 1))
        self.assertEqual(len(test.allocs), 2, 'one Window object and one pixel buffer, created once')
        self.assertEqual([a[1:] for a in test.allocs], [(19, 16), (19, 1024)], 'both on Summary heap 19')
        raw = test.window_bytes(window)
        self.assertEqual(struct.unpack('<I6BHI', raw)[:8], (bench.BGCONFIG, 4, 1, 18, 16, 2, 13, 955))
        self.assertEqual(struct.unpack('<I', raw[12:])[0], test.allocs[1][0])
        buffer = struct.unpack('<I', raw[12:])[0]
        self.assertEqual(bytes(test.uc.mem_read(buffer, 1024)), bytes(1024),
                         'the pixel buffer is cleared by the legend itself (fresh heap memory is poisoned)')
        prints = self.prints(test)
        self.assertEqual(len(prints), 3, 'one print per redraw')
        for entry in prints:
            name, win, font, x, y, speed, color, callback, magic, codes = entry
            self.assertEqual((win, font, x, y, speed, color, callback), (window, 0, 0, 0, 0xFF, 0x000E0F00, 0))
            self.assertEqual(magic, 0xB6F8D2EC)
            self.assertEqual(list(codes), expected)
        self.assertEqual(test.destroy()[1], True)
        self.assertEqual(sorted(test.frees), sorted(a[0] for a in test.allocs), 'both blocks freed')
        self.assertEqual((test.state()[0], test.state()[2]), (0, 0))
        self.assertEqual(test.state()[1], 1, 'generation is kept: it only grows')
        frees = len(test.frees)
        test.destroy()
        test.destroy(0x12345678)
        self.assertEqual((len(test.frees), test.errors, test.live_allocations()), (frees, [], {}))
        self.assertTrue(all(value == 0 for value in test.tilemap()), 'legend tilemap cells removed')

    def test_redraw_restores_cells_cleared_by_the_native_page_draw(self):
        test = self.make()
        test.update()
        cells = {i: v for i, v in enumerate(test.tilemap()) if v}
        self.assertEqual(sorted(cells), [row * 32 + col for row in (18, 19) for col in range(1, 17)])
        self.assertEqual(sorted(cells.values()), [0xD000 | n for n in range(955, 987)])
        for index in cells:
            test.poke_tilemap(index, 0)        # sub_0208CBD4 clears bg4 columns 0..17 before each page draw
        test.update()
        self.assertEqual({i: v for i, v in enumerate(test.tilemap()) if v}, cells)
        self.assertEqual(test.state()[1], 1, 'same generation: the window is reused, not recreated')

    def test_nothing_outside_the_rectangle_and_the_summary_object_is_unchanged(self):
        test = self.make()
        before = bytes(test.uc.mem_read(bench.SUMMARY, 0x7D8))
        sentinel = {i: 0x1111 + i for i in (0, 31, 32, 577 - 1, 577 + 16, 18 * 32, 20 * 32 + 1, 767)}
        for index, value in sentinel.items():
            test.poke_tilemap(index, value)
        test.update()
        test.update()
        self.assertEqual(bytes(test.uc.mem_read(bench.SUMMARY, 0x7D8)), before, 'no scratch in native padding')
        for index, value in sentinel.items():
            self.assertEqual(test.tilemap()[index], value, 'tilemap cell %d outside the rectangle' % index)

    def test_geometry_is_a_parameter_not_a_constant(self):
        geometry = dict(GEOMETRY, left=2, top=19, width=12, palette=11, baseTile=960)
        test = self.make(geometry=geometry)
        test.update()
        self.assertNotEqual(test.state()[2], 0, 'a window was created')
        raw = test.window_bytes(test.state()[2])
        self.assertEqual(struct.unpack('<I6BH', raw[:12]), (bench.BGCONFIG, 4, 2, 19, 12, 2, 11, 960))
        self.assertEqual(sorted(i for i, v in enumerate(test.tilemap()) if v),
                         [row * 32 + col for row in (19, 20) for col in range(2, 14)])

    def test_italian_payload_prints_the_italian_legend(self):
        test = self.make('IT')
        test.update()
        self.assertEqual(len(self.prints(test)), 1)
        self.assertEqual(list(self.prints(test)[0][9]), controls.encode_legend('IT', CHARMAP))

    def test_legend_never_reads_the_keys_so_L_equals_A_cannot_change_it(self):
        test = self.make()
        test.update()
        test.update()
        test.destroy()
        self.assertEqual(test.gsystem_reads, [], 'gSystem is never touched: button mode is irrelevant')


class UnsupportedViews(RuntimeCase):
    CASES = (('egg', dict(), 'egg'), ('page memo', dict(page=0), None), ('page moves', dict(page=2), None),
             ('page contest', dict(page=3), None), ('learn mode 3', dict(mode=3), None),
             ('learn mode 4', dict(mode=4), None), ('move to learn', dict(move_to_learn=33), None),
             ('leaving', dict(state=0x10), None), ('no mon', dict(), 'nomon'))

    def configure(self, test, flag):
        if flag == 'egg':
            test.egg = 1
        if flag == 'nomon':
            test.mon_present = False

    def test_eggs_pages_and_learning_do_not_draw(self):
        for label, summary, flag in self.CASES:
            with self.subTest(label):
                test = self.make(**summary)
                self.configure(test, flag)
                test.update()
                self.assertEqual((test.allocs, self.prints(test), test.state()[:3]), ([], [], (0, 0, 0)))
                tile_cells = [v for v in test.tilemap() if v]
                self.assertEqual(tile_cells, [])

    def test_null_summary_and_null_args_never_draw(self):
        test = self.make()
        test.update(0)
        test.uc.mem_write(bench.SUMMARY + 0x22C, bytes(4))
        test.update()
        self.assertEqual((test.allocs, self.prints(test)), ([], []))

    def test_an_existing_window_is_removed_when_the_view_stops_being_supported(self):
        for label, summary, flag in self.CASES:
            with self.subTest(label):
                test = self.make()
                test.update()
                self.assertEqual(len(test.allocs), 2)
                test.build_summary(**summary)
                self.configure(test, flag)
                test.set_state(owner=bench.SUMMARY, window=test.state()[2], generation=1)
                test.update()
                self.assertEqual((test.state()[0], test.state()[2]), (0, 0), label)
                self.assertEqual(test.live_allocations(), {}, label)
                self.assertEqual(test.errors, [])
                self.assertTrue(all(v == 0 for v in test.tilemap()))

    def test_disabled_payload_is_completely_inert(self):
        test = self.make(enabled=0)
        for _ in range(2):
            test.update()
            test.destroy()
        self.assertEqual((test.log, test.allocs, test.frees, test.state()[:4]), ([], [], [], (0, 0, 0, 0)))
        self.assertEqual(test.state()[4], 0)


class Failure(RuntimeCase):
    def test_allocation_failure_leaves_no_state_and_retries_cleanly(self):
        for fail_after in (0, 1):  # the Window array, then its pixel buffer
            with self.subTest(fail_after=fail_after):
                test = self.make()
                test.fail_alloc_after = fail_after
                test.update()
                self.assertEqual(test.state()[:3], (0, 0, 0))
                self.assertEqual(test.live_allocations(), {}, 'a half-built window is released')
                self.assertEqual(self.prints(test), [])
                self.assertEqual(test.errors, [])
                test.fail_alloc_after = None
                test.update()
                self.assertEqual((test.state()[0], test.state()[1]), (bench.SUMMARY, 1))
                self.assertEqual(len(test.live_allocations()), 2)

    def test_a_record_of_another_owner_is_dropped_without_touching_its_memory(self):
        test = self.make()
        foreign = 0x02394000
        test.set_state(owner=0x02390800, window=foreign, generation=7)
        test.update()
        self.assertEqual(test.errors, [], 'the foreign window was not freed')
        self.assertNotIn(foreign, test.frees)
        self.assertEqual((test.state()[0], test.state()[1]), (bench.SUMMARY, 8))
        self.assertEqual(len(test.live_allocations()), 2)

    def test_destroy_for_a_summary_that_does_not_own_the_window_is_a_noop(self):
        test = self.make()
        test.update()
        window = test.state()[2]
        test.destroy(0x02390800)
        self.assertEqual((test.state()[0], test.state()[2], test.frees), (bench.SUMMARY, window, []))


class Wrappers(RuntimeCase):
    def test_redraw_wrapper_updates_then_calls_the_native_page_draw_once(self):
        test = self.make()
        result, preserved = test.entry('sgp_sc_redraw')
        self.assertTrue(preserved)
        kinds = [entry[0] for entry in test.log if entry[0] in ('print', 'stats_draw')]
        self.assertEqual(kinds, ['print', 'stats_draw'])
        self.assertEqual([e for e in test.log if e[0] == 'stats_draw'], [('stats_draw', bench.SUMMARY)])

    def test_teardown_wrapper_destroys_before_the_native_teardown_and_only_once(self):
        test = self.make()
        test.update()
        test.log.clear()
        result, preserved = test.entry('sgp_sc_teardown')
        self.assertTrue(preserved)
        order = [entry[0] for entry in test.log if entry[0] in ('heap_free', 'native_teardown')]
        self.assertEqual(order, ['heap_free', 'heap_free', 'native_teardown'])
        self.assertEqual(test.state()[0], 0)
        test.log.clear()
        test.entry('sgp_sc_teardown')
        self.assertEqual([e[0] for e in test.log], ['native_teardown'])

    def test_wrappers_pass_through_when_inert(self):
        test = self.make(enabled=0)
        test.entry('sgp_sc_redraw')
        test.entry('sgp_sc_teardown')
        self.assertEqual(test.log, [('stats_draw', bench.SUMMARY), ('native_teardown', bench.SUMMARY)])

    def test_stack_depth_is_measured_and_small(self):
        test = self.make()
        test.update()
        self.assertLessEqual(test.last_stack_bytes, 256)
        self.assertIn('sgp_summary_controls_update', test.info['stack_bytes'])


if __name__ == '__main__':
    unittest.main()
