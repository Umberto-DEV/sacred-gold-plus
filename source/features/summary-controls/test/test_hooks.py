"""The installed hooks on the real V4 bytes: control flow through the Summary and the inherited viewer.

Class B (private ROMs in memory). The ROM is patched in memory by controls.prepare for a declared TEST
slot (bench.INSTALL_BASE, copied from the reserve map under a declared test policy); Unicorn then runs the real ARM9 from the dispatcher (sub_0208CBD4) and from the
Summary exit (sub_0208C560). Stubbed boundaries: the Label call, the native page teardown, and VRAM
transfers. The same flows run on the unpatched ROM as the oracle.
"""
import hashlib
import os
import struct
import tempfile
import unittest
from pathlib import Path

import bench
from sgp131 import controls

CHARMAP = Path(os.environ.get('SGP_CONTROLS_CHARMAP') or bench.REPOSITORY / 'local/tools/pokeheartgold/charmap.txt')
GEOMETRY = {'bgId': 4, 'left': 1, 'top': 18, 'width': 16, 'height': 2, 'palette': 13, 'baseTile': 955}
DISPATCH, EXIT = 0x0208CBD4, 0x0208C560
STATS_BODY = 0x0208D180          # first byte of sub_0208D178 after the inherited 8-byte hook
LABEL = 0x0208C850               # native Label (called by the inherited reset_header)
TEARDOWN = 0x0208C4E0
_ROMS, _PATCHED = {}, {}


def rom(test, language):
    if language not in _ROMS:
        path, digest = bench.input_path(language)
        if path is None or not CHARMAP.is_file():
            reason = 'private V4 %s ROM or charmap not available' % language
            if os.environ.get(bench.REQUIRE) == '1':
                test.fail(reason)
            test.skipTest(reason)
        data = path.read_bytes()
        test.assertEqual(hashlib.sha256(data).hexdigest(), digest)
        _ROMS[language] = data
    return _ROMS[language]


def patched(test, language, active):
    key = (language, active)
    if key not in _PATCHED:
        data = rom(test, language)
        slot = {'allocation': bench.declared_allocation(language),
                'preimage_sha256': hashlib.sha256(controls.read(data, bench.INSTALL_BASE, bench.SLOT_BYTES)).hexdigest()}
        evidence, candidate = None, None
        if active:
            check = controls.check_geometry(GEOMETRY, controls.inventory(data), None)
            candidate = hashlib.sha256(b'fixture: the inert candidate ROM of the hooks test').hexdigest()
            evidence = {'kind': 'summary-window-inventory', 'capture_rom_sha256': candidate, 'build_id': 'fixture-not-a-build',
                        'language': language, 'geometry': dict(GEOMETRY), 'views': ['stats', 'ev', 'iv'],
                        'button_modes': ['normal', 'L=A'], 'contexts': ['field', 'pc'],
                        'captures': [{'name': 'fixture-not-a-capture', 'sha256': '0' * 64}],
                        'free_tiles': [955, 988], 'hidden_windows': check['overlapping_windows']}  # fixture, not a measurement
        with tempfile.TemporaryDirectory(prefix='summary-hooks-') as work, bench.declared_reserve():
            _PATCHED[key] = controls.prepare(data, language, CHARMAP, Path(work), geometry=GEOMETRY, active=active,
                                             evidence=evidence, candidate_sha256=candidate, **slot)
    return _PATCHED[key]


def is_legend(entry):
    """Boundary calls made by the legend itself: its predicate, its two allocations, its print, its transfer."""
    kind = entry[0]
    if kind in ('print', 'get_mon', 'get_box_data'):
        return True
    if kind == 'heap_alloc':
        return entry[2] in (16, 1024)
    return kind == 'load_char_tiles' and entry[1] == 4


class Flow(unittest.TestCase):
    def machine(self, image, **summary):
        test = bench.Bench(image)
        test.build_summary(**summary)
        test.add_shared_window(2, (1, 20, 1, 11, 2, 13, 23))  # reset_header's target window
        test.stub(LABEL, lambda args, sp: test.log.append(('label', args[1], args[2], args[3])))
        test.stub(TEARDOWN, lambda args, sp: test.log.append(('native_teardown', args[0])))
        return test

    def dispatch(self, image, **summary):
        test = self.machine(image, **summary)
        test.call(DISPATCH, bench.SUMMARY, until=STATS_BODY)
        return test


class RedrawSite(Flow):
    def test_update_runs_before_the_inherited_reset_header_and_the_native_body(self):
        for language in controls.LANGUAGES:
            with self.subTest(language):
                image, receipt = patched(self, language, True)
                test = self.dispatch(image)
                kinds = [entry[0] for entry in test.log if entry[0] in ('print', 'label')]
                self.assertEqual(kinds, ['print', 'label'], 'legend print, then the viewer header reset')
                self.assertEqual([e for e in test.log if e[0] == 'label'], [('label', 2, 109, 0x000E0F00)])
                self.assertEqual(test.uc.reg_read(bench.UC_ARM_REG_PC) & ~1, STATS_BODY, 'native body reached')
                self.assertEqual(test.state(bench.INSTALL_BASE)[:2], (bench.SUMMARY, 1))

    def test_inert_install_is_observably_the_native_flow(self):
        for language in controls.LANGUAGES:
            with self.subTest(language):
                original = self.dispatch(rom(self, language))
                inert = self.dispatch(patched(self, language, False)[0])
                self.assertEqual(inert.log, original.log)
                self.assertEqual(inert.tilemap(), original.tilemap())
                self.assertEqual(inert.allocs, original.allocs)

    def test_active_install_differs_from_native_only_by_the_legend(self):
        for language in controls.LANGUAGES:
            with self.subTest(language):
                original = self.dispatch(rom(self, language))
                active = self.dispatch(patched(self, language, True)[0])
                self.assertEqual([e for e in active.log if not is_legend(e)], original.log)
                legend = {i for row in (18, 19) for i in range(row * 32 + 1, row * 32 + 17)}
                changed = {i for i, (a, b) in enumerate(zip(active.tilemap(), original.tilemap())) if a != b}
                self.assertEqual(changed, legend, 'only the legend cells differ from the native tilemap')
                self.assertEqual(len(active.allocs) - len(original.allocs), 2)

    def test_other_pages_and_eggs_stay_native(self):
        image, _ = patched(self, 'IT', True)
        for summary, egg in ((dict(page=0), 0), (dict(page=2), 0)):
            native = self.machine(rom(self, 'IT'), **summary)
            hooked = self.machine(image, **summary)
            for machine in (native, hooked):
                machine.egg = egg
                try:
                    machine.call(DISPATCH, bench.SUMMARY, until=0x0208D180)
                except AssertionError:
                    pass
            self.assertEqual([e for e in hooked.log if e[0] == 'print'], [])
            self.assertEqual(hooked.log, native.log)


class TeardownSite(Flow):
    def test_legend_is_released_before_the_native_page_teardown(self):
        image, receipt = patched(self, 'EN', True)
        test = self.machine(image)
        test.call(DISPATCH, bench.SUMMARY, until=STATS_BODY)       # creates the legend
        self.assertEqual(len(test.live_allocations()), 2 + len(test.pre_existing), 'legend window and buffer live')
        test.log.clear()
        test.call(EXIT, bench.SUMMARY)
        order = [e[0] for e in test.log if e[0] in ('heap_free', 'native_teardown')]
        self.assertEqual(order[:3], ['heap_free', 'heap_free', 'native_teardown'])
        self.assertEqual(test.state(bench.INSTALL_BASE)[0], 0)
        self.assertEqual(test.errors, [])

    def test_exit_without_a_legend_only_adds_the_native_call(self):
        for language in controls.LANGUAGES:
            original = self.machine(rom(self, language))
            hooked = self.machine(patched(self, language, True)[0])
            for machine in (original, hooked):
                machine.call(EXIT, bench.SUMMARY)
            self.assertEqual(hooked.log, original.log)
            self.assertEqual(hooked.frees, original.frees)

    def test_all_three_call_sites_reach_the_wrappers(self):
        image, receipt = patched(self, 'IT', True)
        symbols = receipt['payload']['symbols']
        for site, name in (('0x0208CC5A', 'sgp_sc_redraw'), ('0x02089D78', 'sgp_sc_teardown'),
                           ('0x0208C564', 'sgp_sc_teardown')):
            raw = controls.read(image, controls.hex_int(site), 4)
            self.assertEqual(controls.decode_bl(controls.hex_int(site), raw), symbols[name], site)


if __name__ == '__main__':
    unittest.main()
