"""Class B: the exact V4 EN/IT candidates, read and patched in memory only.

Inputs default to the balance493 candidates under local/experiments; a missing
input skips with a reason, and SGP_CONTROLS_REQUIRE_INPUTS=1 turns that into a
failure. A present input with the wrong sha256 always fails. Nothing is written
to disk. The installer takes its base from a reserve.allocate receipt; the real
policy cannot grant the legend slot yet, so these tests run under a DECLARED
test policy (bench.declared_reserve: slot name/start/size copied from
reserve-map.json, own version and digest, refused by the real policy). Unicorn
executes the real ARM9 bytes of the Summary and of the installed EV/IV viewer.
"""
import copy
import hashlib
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

from sgp131 import controls
from sgp131.test_controls import Intervals

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/features/summary-controls/test'))
import bench  # noqa: E402

CHARMAP = Path(os.environ.get('SGP_CONTROLS_CHARMAP') or ROOT / 'local/tools/pokeheartgold/charmap.txt')
REQUIRE_INPUTS = os.environ.get(bench.REQUIRE) == '1'
GEOMETRY = {'bgId': 4, 'left': 1, 'top': 18, 'width': 16, 'height': 2, 'palette': 13, 'baseTile': 955}
EVIDENCE = {'kind': 'summary-window-inventory', 'free_tiles': [955, 1023],
            'hidden_windows': None}  # filled per ROM from the inventory: test fixture, not a measurement
SLOT_BYTES = bench.SLOT_BYTES
_CACHE = {}


def rom_bytes(test, language):
    if language not in _CACHE:
        path, digest = bench.input_path(language)
        if path is None or not CHARMAP.is_file():
            reason = '%s V4 ROM or charmap not present' % language
            if REQUIRE_INPUTS:
                test.fail(reason)
            test.skipTest(reason)
        data = path.read_bytes()
        test.assertEqual(hashlib.sha256(data).hexdigest(), digest, language + ' input sha256 mismatch')
        _CACHE[language] = data
    return _CACHE[language]


def diff_offsets(before, after, chunk=1 << 20):
    changed = []
    for base in range(0, len(before), chunk):
        end = min(base + chunk, len(before))
        if before[base:end] != after[base:end]:
            changed.extend(i for i in range(base, end) if before[i] != after[i])
    return changed


def slot_args(v4, language, **allocation_override):
    """The installer's base arguments under the declared test policy: a fixture, not a product assignment. The expected
    preimage comes from the V4 image (independent of the stage input), the recipe the builder must follow (I5)."""
    return {'allocation': bench.declared_allocation(language, **allocation_override),
            'preimage_sha256': hashlib.sha256(controls.read(v4, bench.INSTALL_BASE, bench.SLOT_BYTES)).hexdigest()}


def candidate_for(data, label='inert candidate'):
    """The sha256 of a (fixture) candidate ROM; the real one is whatever Codex captured on."""
    return hashlib.sha256(data + label.encode()).hexdigest()


def evidence_for(data, language, geometry=GEOMETRY, **over):
    """TEST evidence naming every overlapped window hidden: a fixture bound to `candidate_for(data)`, NOT a measurement."""
    check = controls.check_geometry(geometry, controls.inventory(data), None, active=False)
    record = {'kind': 'summary-window-inventory', 'capture_rom_sha256': candidate_for(data), 'build_id': 'fixture-not-a-build',
              'language': language, 'geometry': dict(geometry), 'views': ['stats', 'ev', 'iv'], 'button_modes': ['normal', 'L=A'],
              'contexts': ['field', 'pc'], 'captures': [{'name': 'fixture-not-a-capture', 'sha256': '0' * 64}],
              'free_tiles': [geometry['baseTile'], geometry['baseTile'] + 33],
              'hidden_windows': check['overlapping_windows']}
    record.update(over)
    return record


class Candidate(unittest.TestCase):
    def setUp(self):
        self.enterContext(bench.declared_reserve())

    def data(self, language):
        return rom_bytes(self, language)

    def prepare(self, data, language, work, *, active=False, geometry=None, evidence=None, **kwargs):
        """controls.prepare with the declared test slot; activation gets its candidate sha256 and evidence."""
        if active:
            geometry = geometry or GEOMETRY
            evidence = evidence if evidence is not None else evidence_for(data, language, geometry)
            kwargs.setdefault('candidate_sha256', candidate_for(data))
        return controls.prepare(data, language, CHARMAP, Path(work), geometry=geometry, active=active, evidence=evidence,
                                **{**slot_args(self.data(language), language), **kwargs})

    def install(self, language, active=False, geometry=GEOMETRY):
        data = self.data(language)
        with tempfile.TemporaryDirectory(prefix='summary-controls-') as work:
            out, receipt = self.prepare(data, language, work, active=active, geometry=geometry)
        return data, out, receipt


class Pins(Candidate):
    def test_installed_rom_matches_the_pin_file(self):
        for language in controls.LANGUAGES:
            with self.subTest(language):
                measured = controls.audit(self.data(language), language)
                self.assertEqual(measured['spans']['viewer.reader']['sha256'],
                                 'c4d207486d46e1da5ceec1a96226e3fd18d7cae7e0a2357479dc50b30b0e2558')
                self.assertEqual(measured['spans']['viewer.payload']['bytes'], 592)

    def test_en_and_it_pins_are_identical(self):
        self.assertEqual(controls.measure(self.data('EN')), controls.measure(self.data('IT')))

    def test_every_pinned_range_rejects_a_changed_byte_with_its_address(self):
        abi = controls.load_abi()
        for language in controls.LANGUAGES:
            data = self.data(language)
            ranges = [(name, controls.hex_int(item['address']), item['bytes'], 'spans.%s' % name)
                      for name, item in abi['spans'].items()]
            ranges += [('hooks.%s' % name, controls.hex_int(item['address']), 8, 'hooks.%s' % name)
                       for name, item in abi['hooks'].items()]
            ranges += [('natives.%s' % name, controls.hex_int(item['address']), item['bytes'], 'natives.%s' % name)
                       for name, item in abi['natives'].items()]
            ranges += [('tables.%s' % name, controls.hex_int(item['address']), 8 * item['entries'], 'tables.%s' % name)
                       for name, item in abi['tables'].items()]
            ranges += [('bg.%s' % name, controls.hex_int(item['address']), 28, 'bg.%s' % name)
                       for name, item in abi['bg'].items()]
            ranges += [('literals.%s' % name, controls.hex_int(item['address']), 4, 'literals.%s' % name)
                       for name, item in abi['literals'].items()]
            names = {row['name'] for row in controls.intervals(abi)}
            self.assertEqual({r[0] for r in ranges} - names, set(), 'every range tested is a declared interval')
            self.assertEqual({n for n in names if not n.startswith('site.')} - {r[0] for r in ranges}, set(),
                             'every declared read interval is tested')
            for name, address, size, path in ranges:
                for position in (address, address + size - 1):
                    with self.subTest(language=language, name=name, at=hex(position)):
                        mutated = bytearray(data)
                        mutated[controls.rom_offset(data, position)] ^= 0x01
                        with self.assertRaises(ValueError) as caught:
                            controls.compare_pins(controls.measure(mutated), controls.expected_pins(abi))
                        message = str(caught.exception)
                        self.assertRegex(message, r'^(spans|hooks|edges|natives|tables|bg|literals)\b|literal-pool hook', message)
                if name == ranges[0][0]:
                    with self.assertRaises(ValueError):
                        controls.audit(bytes(mutated), language)  # and so does the installer's audit

    def test_audit_checks_intervals_not_the_whole_rom(self):
        """No whole-ROM identity: an image whose pinned intervals are intact is accepted whatever the rest holds."""
        data = self.data('EN')
        tail = bytearray(data)
        tail[-16:] = bytes(16)                                   # outside the ARM9: not an interval
        self.assertEqual(controls.audit(bytes(tail), 'EN'), controls.audit(data, 'EN'))
        with self.assertRaisesRegex(ValueError, 'language'):
            controls.audit(data, 'FR')
        # the pins are identical in EN and IT: the language is the caller's declaration, bound to the evidence
        self.assertEqual(controls.audit(data, 'IT'), controls.audit(data, 'EN'))

    def test_incoming_edges_are_complete_not_just_the_ones_we_patch(self):
        abi = controls.load_abi()
        self.assertEqual(abi['edges']['teardown_callers'], ['0x02089D78', '0x0208C564'])
        self.assertEqual(abi['edges']['redraw_callers'], ['0x0208CC5A'])
        data = self.data('IT')
        cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for site, target in (('0x0208CC5A', 0x0208D178), ('0x02089D78', 0x0208C4E0), ('0x0208C564', 0x0208C4E0)):
            raw = controls.read(data, controls.hex_int(site), 4)
            insn = next(cs.disasm(raw, controls.hex_int(site)))
            self.assertEqual((insn.mnemonic, int(insn.op_str[1:], 16)), ('bl', target), site)

    def test_installed_viewer_reads_raw_keys_and_hooks_route_to_it(self):
        data = self.data('EN')
        reader = controls.read(data, 0x01FF8658, 448)
        cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        first = list(cs.disasm(reader[:12], 0x01FF8658))
        self.assertEqual([i.mnemonic for i in first[:3]], ['push', 'sub', 'movs'])
        self.assertEqual(struct.unpack('<I', controls.read(data, 0x01FF87F8, 4))[0], 0x021D1148)
        for address, entry in ((0x02088B40, 0x01FF883D), (0x0208D178, 0x01FF881D)):
            self.assertEqual(controls.decode_literal_hook(controls.read(data, address, 8)), entry)

    def test_inventory_covers_the_known_native_windows_and_tile_limits(self):
        data = self.data('IT')
        inventory = controls.inventory(data)
        names = {w['name']: w for w in inventory['rects']}
        self.assertEqual(names['page_skills.17'], {'name': 'page_skills.17', 'left': 1, 'top': 17, 'width': 10, 'height': 2})
        self.assertEqual(names['shared.29']['top'], 17)
        highest = max(t['hi'] for t in inventory['tiles'])
        self.assertEqual(highest, 954, 'native windows on the lower screen end at tile 954')
        # The proposed (8,144) strip overlaps native rectangles: it needs hidden-window proof.
        proposal = controls.check_geometry(GEOMETRY, inventory, None, active=False)
        self.assertEqual(proposal['overlapping_windows'],
                         ['page_skills.12', 'page_skills.17', 'shared.14', 'shared.29'])
        self.assertFalse(proposal['proven'])

    def test_tile_overlap_rejected(self):
        inventory = controls.inventory(self.data('EN'))
        for base in (925, 944, 900, 940, 600, 100):
            with self.subTest(base=base), self.assertRaisesRegex(ValueError, 'tile'):
                controls.check_geometry(dict(GEOMETRY, baseTile=base), inventory, None)
        controls.check_geometry(dict(GEOMETRY, baseTile=955), inventory, None)

    def test_background_pins_match_the_tile_ownership_argument(self):
        bg = controls.load_abi()['bg']
        self.assertEqual((bg['bg4']['screen_base'], bg['bg4']['char_base']), (31, 4))
        self.assertEqual(bg['bg1']['screen_base'], 31)


class ViewerKeys(Candidate):
    """Run the installed reader (0x01FF8658) with raw and processed keys, original and patched ROM."""

    EV, IV, STATS = 0xC3, 0xC4, 0x6D
    L, R, SELECT, A = 0x200, 0x100, 0x4, 0x1

    def run_reader(self, rom, raw_new, processed_new=0, raw_repeat=0, page=1, egg=0, literal=None):
        test = bench.Bench(rom)
        if literal is not None:
            test.uc.mem_write(0x01FF87F8, struct.pack('<I', literal))
        test.build_summary(page=page)
        test.egg = egg
        # The reader prints its title through the inherited label wrapper (ITCM 0x01FF9348), which
        # forwards ordinary messages to the native Label: the wrapper is the observed boundary.
        for name, address in (('label', 0x01FF9349), ('print', 0x0208C779), ('number', 0x0208C87D),
                              ('fill', 0x0201D979), ('copy', 0x0201D5C9), ('width', 0x0201EE91),
                              ('ratio', 0x0208C8C9)):
            test.stub(address - 1 if address & 1 else address, (lambda n: lambda a, sp: test.log.append((n,) + tuple(a)))(name))
        test.uc.mem_write(0x021D1148, struct.pack('<II', raw_new, raw_repeat))
        test.uc.mem_write(0x021D1154, struct.pack('<I', processed_new))
        result, preserved = test.call(0x01FF8658, bench.SUMMARY)
        labels = [entry[3] for entry in test.log if entry[0] == 'label' and entry[2] == 2]
        return result, labels, test

    def test_reader_payload_and_raw_keys_preserved(self):
        for language in controls.LANGUAGES:
            with self.subTest(language):
                before, after, receipt = self.install(language, active=False)
                for name in ('viewer.payload', 'viewer.reader', 'viewer.reset_header', 'viewer.entries', 'viewer.label_wrapper'):
                    item = receipt['pins_after']['spans'][name]
                    self.assertEqual(item, controls.load_abi()['spans'][name], name)
                for hook in ('input', 'redraw'):
                    address = controls.hex_int(controls.load_abi()['hooks'][hook]['address'])
                    self.assertEqual(controls.read(before, address, 8), controls.read(after, address, 8), hook)
                self.assertEqual(controls.read(after, 0x01FF87F8, 4), struct.pack('<I', 0x021D1148))
                changed = diff_offsets(before, after)
                viewer = controls.rom_offset(before, 0x01FF8620)
                self.assertFalse([c for c in changed if viewer <= c < viewer + 592], 'viewer bytes untouched')

    def test_LA_keeps_L_EV_R_IV_SELECT_stats(self):
        """With L=A the processed keys carry A (never L/R); the raw physical keys still drive the viewer."""
        for language in controls.LANGUAGES:
            _before, patched, _receipt = self.install(language, active=True)
            for label, rom in (('original', self.data(language)), ('patched', patched)):
                for button_mode in ('normal', 'L=A'):
                    cases = ((self.L, self.EV), (self.R, self.IV), (self.SELECT, self.STATS))
                    for key, message in cases:
                        with self.subTest(language=language, rom=label, mode=button_mode, key=hex(key)):
                            processed = self.A if (button_mode == 'L=A' and key == self.L) else (0 if button_mode == 'L=A' and key == self.R else key)
                            result, labels, _ = self.run_reader(rom, key, processed_new=processed)
                            self.assertEqual((result, labels), (1, [message]))
                # A and B (raw) suppress the viewer; a direction repeat suppresses it too.
                self.assertEqual(self.run_reader(rom, self.L | self.A, processed_new=self.A)[:2], (0, []))
                self.assertEqual(self.run_reader(rom, self.L, raw_repeat=0x20)[:2], (0, []))
                self.assertEqual(self.run_reader(rom, 0)[:2], (0, []))
                self.assertEqual(self.run_reader(rom, self.L, page=0)[:2], (0, []))
                self.assertEqual(self.run_reader(rom, self.L, egg=1)[:2], (0, []))
                # SELECT works on an egg page too (restores the stats title); only L/R need a real mon.

    BUTTON_MODES = ('normal', 'start=X', 'swap X/Y', 'L=A')   # gSystem.buttonMode 0..3 (pret system.h)

    @staticmethod
    def processed(mode, raw):
        """The processed key word ApplyButtonModeToInput (pret system.c) derives from raw keys."""
        L, R, A, X, Y, START = 0x200, 0x100, 0x1, 0x400, 0x800, 0x8
        keys = raw
        if mode == 'start=X' and keys & START:
            keys |= X
        if mode == 'swap X/Y':
            keys = (keys & ~(X | Y)) | (Y if raw & X else 0) | (X if raw & Y else 0)
        if mode == 'L=A':
            keys = (keys | A) if keys & L else keys
            keys &= ~(L | R)
        return keys

    def test_all_four_native_button_modes_leave_the_raw_viewer_alone(self):
        data = self.data('IT')
        for mode in self.BUTTON_MODES:
            for key, message in ((self.L, self.EV), (self.R, self.IV), (self.SELECT, self.STATS)):
                with self.subTest(mode=mode, key=hex(key)):
                    result, labels, _ = self.run_reader(data, key, processed_new=self.processed(mode, key))
                    self.assertEqual((result, labels), (1, [message]))
        self.assertEqual(self.processed('L=A', self.L) & (self.L | self.R), 0)
        self.assertEqual(self.processed('L=A', self.R) & (self.L | self.R), 0)

    def test_a_processed_key_reader_would_lose_L_under_L_equals_A(self):
        """Mutant: repoint the reader literal at the processed keys (the historical C). It must fail."""
        data = self.data('IT')
        result, labels, _ = self.run_reader(data, self.L, processed_new=self.A, literal=0x021D1154)
        self.assertEqual((result, labels), (0, []), 'the processed-key reader ignores L under L=A: why it is not rebuilt')

    def test_the_legend_never_changes_what_the_keys_do(self):
        _b, patched, _r = self.install('EN', active=True)
        original_trace = self.run_reader(self.data('EN'), self.L)[2].log
        patched_trace = self.run_reader(patched, self.L)[2].log
        self.assertEqual(patched_trace, original_trace)


class Installer(Candidate):
    def test_prepare_verify_changes_exactly_the_slot_and_three_call_sites(self):
        for language in controls.LANGUAGES:
            for active in (False, True):
                with self.subTest(language=language, active=active):
                    before, after, receipt = self.install(language, active=active)
                    self.assertEqual(len(before), len(after))
                    self.assertEqual(before[:0x200], after[:0x200], 'NDS header untouched')
                    slot = receipt['slot']
                    inside = controls.rom_offset(before, slot['start'])
                    sites = [controls.rom_offset(before, controls.hex_int(s)) for s in receipt['sites']]
                    allowed = set(range(inside, inside + receipt['payload']['bytes']))
                    for site in sites:
                        allowed.update(range(site, site + 4))
                    changed = diff_offsets(before, after)
                    self.assertTrue(set(changed) <= allowed)
                    self.assertTrue(all(c in changed for c in sites), 'every site changed')
                    proof = controls.verify(before, after, receipt)
                    self.assertEqual(proof['enabled'], int(active))
                    self.assertEqual(proof['function_state'], 'active' if active else 'inert')
                    self.assertEqual(sorted(receipt['sites']), ['0x02089D78', '0x0208C564', '0x0208CC5A'])
                    self.assertEqual(proof['arm9_changed_outside_assignment'], 0)

    def test_inert_by_default_and_active_only_with_geometry_evidence_and_candidate(self):
        data = self.data('EN')
        with tempfile.TemporaryDirectory() as work:
            _out, receipt = self.prepare(data, 'EN', work)
        self.assertEqual((receipt['enabled'], receipt['function_state'], receipt['geometry_source']), (0, 'inert', 'proposal'))
        self.assertEqual((receipt['candidate_sha256'], receipt['capture_rom_sha256'], receipt['candidate_relation']),
                         (None, None, None))
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'activation'):
                controls.prepare(data, 'EN', CHARMAP, Path(work), active=True, **slot_args(data, 'EN'))
            with self.assertRaisesRegex(ValueError, 'hidden proof'):
                self.prepare(data, 'EN', work, active=True, evidence=evidence_for(data, 'EN', hidden_windows=[]))
            with self.assertRaisesRegex(ValueError, 'candidate_sha256'):
                controls.prepare(data, 'EN', CHARMAP, Path(work), geometry=GEOMETRY, active=True,
                                 evidence=evidence_for(data, 'EN'), **slot_args(data, 'EN'))

    def test_evidence_must_be_bound_to_the_declared_candidate_and_language(self):
        """C3: the proof is tied to the inert candidate ROM that was captured (candidate_sha256), not to the stage input."""
        en, it = self.data('EN'), self.data('IT')
        candidate = candidate_for(en)
        with tempfile.TemporaryDirectory() as work:
            kwargs = dict(active=True, geometry=GEOMETRY)
            with self.assertRaisesRegex(ValueError, 'another ROM'):
                self.prepare(en, 'EN', work, evidence=evidence_for(en, 'EN', capture_rom_sha256=candidate_for(it)), **kwargs)
            with self.assertRaisesRegex(ValueError, 'another ROM'):
                self.prepare(en, 'EN', work, candidate_sha256=candidate_for(it), **kwargs)
            with self.assertRaisesRegex(ValueError, 'another language'):
                self.prepare(en, 'EN', work, evidence=evidence_for(en, 'IT'), **kwargs)
            with self.assertRaisesRegex(ValueError, 'different geometry'):
                self.prepare(en, 'EN', work, evidence=evidence_for(en, 'EN', dict(GEOMETRY, baseTile=960)), **kwargs)
            with self.assertRaisesRegex(ValueError, 'views'):
                self.prepare(en, 'EN', work, evidence=evidence_for(en, 'EN', views=['stats']), **kwargs)
            for missing in ('capture_rom_sha256', 'build_id', 'captures'):
                record = evidence_for(en, 'EN')
                del record[missing]
                with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'exactly'):
                    self.prepare(en, 'EN', work, evidence=record, **kwargs)
            synthetic = evidence_for(en, 'EN', captures=[])
            with self.assertRaisesRegex(ValueError, 'capture references'):
                self.prepare(en, 'EN', work, evidence=synthetic, **kwargs)
            out, receipt = self.prepare(en, 'EN', work, **kwargs)
        # the receipt records both and the input hash is NOT what the evidence is bound to
        self.assertEqual((receipt['candidate_sha256'], receipt['capture_rom_sha256']), (candidate, candidate))
        self.assertNotEqual(receipt['input_sha256'], receipt['capture_rom_sha256'])
        self.assertEqual(receipt['evidence']['captures'][0]['name'], 'fixture-not-a-capture')
        self.assertEqual(receipt['candidate_relation'], 'composed-candidate')
        self.assertEqual(controls.verify(en, out, receipt)['candidate_sha256'], candidate)

    def test_a_candidate_that_is_the_stage_inert_output_is_recognised_from_the_bytes(self):
        en = self.data('EN')
        with tempfile.TemporaryDirectory() as work:
            inert, _r = self.prepare(en, 'EN', work, geometry=GEOMETRY)
            stage_candidate = hashlib.sha256(inert).hexdigest()
            out, receipt = self.prepare(en, 'EN', work, active=True, geometry=GEOMETRY, candidate_sha256=stage_candidate,
                                        evidence=evidence_for(en, 'EN', capture_rom_sha256=stage_candidate))
        self.assertEqual(receipt['candidate_relation'], 'stage-inert-output')
        self.assertEqual(controls.verify(en, out, receipt)['candidate_relation'], 'stage-inert-output')
        forged = dict(receipt, candidate_relation='composed-candidate')
        with self.assertRaisesRegex(ValueError, 'candidate relation'):
            controls.verify(en, out, forged)

    def test_function_state_is_explicit_and_recomputed_from_the_installed_bytes(self):
        for active in (False, True):
            before, after, receipt = self.install('EN', active=active)
            self.assertEqual(receipt['function_state'], 'active' if active else 'inert')
            for forged in (dict(receipt, function_state='inert' if active else 'active'), dict(receipt, function_state=None),
                           {k: v for k, v in receipt.items() if k != 'function_state'}):
                with self.assertRaisesRegex(ValueError, 'activation flag'):
                    controls.verify(before, after, forged)
            # bytes flipped to the other state, receipt and hashes made consistent: the flag word itself is the proof
            slot = controls.rom_offset(before, receipt['slot']['start'])
            flipped = bytearray(after)
            struct.pack_into('<I', flipped, slot + controls.STATE_ENABLED, 0 if active else 1)
            flipped = bytes(flipped)
            image_sha = hashlib.sha256(flipped[slot:slot + receipt['payload']['bytes']]).hexdigest()
            forged = dict(receipt, output_sha256=hashlib.sha256(flipped).hexdigest(),
                          payload=dict(receipt['payload'], image_sha256=image_sha))
            with self.assertRaisesRegex(ValueError, 'activation flag'):
                controls.verify(before, flipped, forged)

    def test_verify_rechecks_the_reserve_allocation_of_the_receipt(self):
        before, after, receipt = self.install('EN')
        allocation = receipt['allocation']
        cases = {'no allocation': {k: v for k, v in receipt.items() if k != 'allocation'},
                 'other policy digest': dict(receipt, allocation=dict(allocation, policy_sha256='1' * 64)),
                 'other language': dict(receipt, allocation=bench.declared_allocation('IT')),
                 'slot moved': dict(receipt, slot=dict(receipt['slot'], start=receipt['slot']['start'] + 4)),
                 'slot grown': dict(receipt, slot=dict(receipt['slot'], bytes=receipt['slot']['bytes'] + 4))}
        for name, forged in cases.items():
            with self.subTest(name), self.assertRaises((ValueError, KeyError, TypeError)):
                controls.verify(before, after, forged)
        with bench.real_reserve(), self.assertRaisesRegex(ValueError, 'policy in force'):
            controls.verify(before, after, receipt)      # a receipt made under the test double is refused by the real policy

    def test_receipts_carry_no_process_state(self):
        for active in (False, True):
            _b, _a, receipt = self.install('IT', active=active)
            blob = json.dumps(receipt, sort_keys=True)
            for word in ('SOURCE_READY', 'ANDROID', 'android', 'not run', 'status', 'note'):
                self.assertNotIn(word, blob, word)

    def test_receipt_symbols_must_match_the_installed_entry_bytes(self):
        before, after, receipt = self.install('EN', active=True)
        for name in ('sgp_summary_controls_update', 'sgp_summary_controls_destroy'):
            forged = dict(receipt, payload=dict(receipt['payload'], symbols=dict(receipt['payload']['symbols'],
                                                                                  **{name: receipt['payload']['symbols'][name] + 2})))
            with self.assertRaisesRegex(ValueError, 'symbols'):
                controls.verify(before, after, forged)

    def test_base_comes_only_from_a_reserve_receipt_and_the_preimage_is_enforced(self):
        data = self.data('EN')
        good = slot_args(data, 'EN')
        cases = {'preimage': dict(good, preimage_sha256='0' * 64),
                 'receipt for another slot size': dict(good, allocation=bench.declared_allocation('EN', size=bench.SLOT_BYTES - 4)),
                 'receipt moved': dict(good, allocation=bench.declared_allocation(
                     'EN', assignments=[dict(bench.declared_allocation('EN')['assignments'][0],
                                             start=bench.INSTALL_BASE + 4)])),
                 'receipt of the other language': dict(good, allocation=bench.declared_allocation('IT')),
                 'no receipt': dict(good, allocation=None), 'free-form base': dict(good, allocation={
                     'name': 'x', 'start': bench.INSTALL_BASE, 'bytes': bench.SLOT_BYTES, 'preimage_sha256': good['preimage_sha256']})}
        for name, kwargs in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as work, self.assertRaises(ValueError):
                controls.prepare(data, 'EN', CHARMAP, Path(work), **kwargs)
        # a payload that cannot fit the receipt's byte count is refused, not truncated
        with tempfile.TemporaryDirectory() as work, self.assertRaisesRegex(ValueError, 'exceeds the assigned slot'):
            controls.prepare(data, 'EN', CHARMAP, Path(work), allocation=bench.declared_allocation(
                'EN', requested={controls.SLOT_NAME: 128},
                assignments=[dict(bench.declared_allocation('EN')['assignments'][0], bytes=128)]),
                preimage_sha256=hashlib.sha256(controls.read(data, bench.INSTALL_BASE, 128)).hexdigest())

    def test_the_real_policy_refuses_the_installer_today(self):
        """No test double: the product map cannot grant summary-controls.runtime, and a genuine receipt of another
        owner does not help. This is the fail-closed state until Codex lifts the conditional owner (INTEGRATION.md)."""
        from sgp131 import reserve
        data = self.data('EN')
        with bench.real_reserve():
            with self.assertRaisesRegex(ValueError, 'conditional'):
                reserve.allocate(data, {controls.SLOT_NAME: 512})            # the allocator itself refuses
            genuine = reserve.allocate(data, {'training.ui': 1536})           # a real receipt, for somebody else
            self.assertEqual(controls.check_allocation(genuine, 'EN', 'training.ui')['start'], 0x023D6800)
            with tempfile.TemporaryDirectory() as work:
                for allocation in (genuine, bench.declared_allocation('EN')):
                    with self.subTest(requested=sorted(allocation['requested'])), self.assertRaises(ValueError):
                        controls.prepare(data, 'EN', CHARMAP, Path(work), allocation=allocation,
                                         preimage_sha256=slot_args(data, 'EN')['preimage_sha256'])

    def test_prepare_never_picks_a_base(self):
        data = self.data('EN')
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'allocation'):
                controls.prepare(data, 'EN', CHARMAP, Path(work))

    def test_verify_rejects_tampering(self):
        """Each tamper keeps the receipt's output hash consistent, so the structural checks are what reject it."""
        before, after, receipt = self.install('IT', active=True)
        slot = controls.rom_offset(before, receipt['slot']['start'])
        sites = [controls.rom_offset(before, controls.hex_int(s)) for s in receipt['sites']]
        size = receipt['payload']['bytes']
        words = struct.unpack('<%dI' % (size // 4), after[slot:slot + size])
        self.assertIn(0xB6F8D2EC, words)
        magic = slot + 4 * words.index(0xB6F8D2EC)
        mutations = {'payload byte': (slot + 40, 1), 'enabled flag': (slot + controls.STATE_ENABLED, 1),
                     'site byte': (sites[0] + 1, 1), 'second site': (sites[1], 1), 'third site': (sites[2] + 2, 1),
                     'unrelated arm9 byte': (controls.rom_offset(before, 0x0208C600), 1),
                     'viewer byte': (controls.rom_offset(before, 0x01FF8700), 1),
                     'viewer hook word': (controls.rom_offset(before, 0x02088B44), 1),
                     'viewer label wrapper': (controls.rom_offset(before, 0x01FF9350), 1),
                     'slot tail': (slot + size + 8, 1), 'gSystem literal in the payload': (magic, None)}
        for name, (position, flip) in mutations.items():
            with self.subTest(name):
                bad = bytearray(after)
                if flip is None:
                    bad[position:position + 4] = struct.pack('<I', 0x021D1148)
                else:
                    bad[position] ^= flip
                bad = bytes(bad)
                tampered = dict(receipt, output_sha256=hashlib.sha256(bad).hexdigest())
                if flip is None:   # a forged payload with a consistent identity: only the semantic scan can reject it
                    tampered['payload'] = dict(receipt['payload'], image_sha256=hashlib.sha256(bad[slot:slot + size]).hexdigest())
                with self.assertRaises(ValueError):
                    controls.verify(before, bad, tampered)
        # A call site redirected to a function that is not a legend wrapper, with every hash made consistent.
        forged = bytearray(after)
        site = controls.hex_int(receipt['sites'][0])
        forged[sites[0]:sites[0] + 4] = controls.encode_bl(site, receipt['payload']['symbols']['sgp_summary_controls_update'])
        forged = bytes(forged)
        with self.assertRaisesRegex(ValueError, 'legend wrapper'):
            controls.verify(before, forged, dict(receipt, output_sha256=hashlib.sha256(forged).hexdigest()))
        with self.assertRaises(ValueError):
            controls.verify(before, after, dict(receipt, enabled=1 - receipt['enabled']))
        with self.assertRaises(ValueError):
            controls.verify(before, after[:-1] + bytes([after[-1] ^ 1]), receipt)  # stale receipt hash

    def test_payload_contains_only_pinned_natives_and_never_touches_the_keys(self):
        _before, after, receipt = self.install('EN', active=True)
        start = receipt['slot']['start']
        words = struct.unpack('<%dI' % (receipt['payload']['bytes'] // 4), controls.read(after, start, receipt['payload']['bytes']))
        abi = controls.load_abi()
        natives = {controls.hex_int(item['address']) | 1 for item in abi['natives'].values()}
        natives |= {0x0208D179, 0x0208C4E1}
        literals = {w for w in words if 0x01FF8000 <= w < 0x02400000 and w & 1}
        absolute = {w for w in literals if w < start or w >= start + receipt['payload']['bytes']}
        self.assertTrue(absolute <= natives, sorted(hex(x) for x in absolute - natives))
        self.assertFalse([w for w in words if 0x021D1100 <= w < 0x021D1180], 'no gSystem literal')

    def test_text_fits_the_window_in_both_languages_and_variants(self):
        for language in controls.LANGUAGES:
            data = self.data(language)
            widths = controls.font_widths(data)
            for variant, expected, tiles in (('compact', 124, 16), ('spaced', 132, 17)):
                with self.subTest(language=language, variant=variant):
                    codes = controls.encode_legend(language, CHARMAP, variant)
                    self.assertEqual(controls.measure_advance(widths, codes), expected)
                    geometry = dict(GEOMETRY, width=tiles)
                    with tempfile.TemporaryDirectory() as work:
                        _out, receipt = self.prepare(data, language, work, geometry=geometry, variant=variant)
                    self.assertEqual((receipt['text_advance_px'], receipt['window_px']), (expected, 8 * tiles))
                    with tempfile.TemporaryDirectory() as work, self.assertRaisesRegex(ValueError, 'truncated'):
                        self.prepare(data, language, work, geometry=dict(GEOMETRY, width=tiles - 1), variant=variant)

    def test_stack_and_size_budget_is_reported(self):
        _b, _a, receipt = self.install('EN')
        self.assertLessEqual(receipt['payload']['bytes'], bench.SLOT_BYTES)
        self.assertLessEqual(max(receipt['payload']['stack_bytes'].values()), 64)

    def test_rebuild_is_deterministic(self):
        _b, first, a = self.install('IT', active=True)
        _b, second, b = self.install('IT', active=True)
        self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())
        self.assertEqual(a['payload']['image_sha256'], b['payload']['image_sha256'])

    def test_the_proposal_from_the_plan_needs_proof_before_it_can_be_activated(self):
        data = self.data('EN')
        inventory = controls.inventory(data)
        report = controls.check_geometry(GEOMETRY, inventory, None, active=False)
        self.assertIn('shared.29', report['overlapping_windows'])
        with self.assertRaisesRegex(ValueError, 'hidden proof'):
            controls.check_geometry(GEOMETRY, inventory, evidence_for(data, 'EN', hidden_windows=['shared.29']), active=True,
                                    candidate_sha256=candidate_for(data), language='EN')


class Composition(Candidate):
    """C2: the legend composes after any stage that leaves its byte intervals alone, and refuses one that does not."""

    @staticmethod
    def earlier_stage(data):
        """A synthetic earlier stage (the UI's footprint, byte-for-byte as written by sgp131/ui.py): arbitrary bytes at
        every ARM9 address and length the UI writes, the cartridge extended at its end, the header untouched. A
        declared test double, not the UI."""
        out = bytearray(data)
        segments = controls._arm9_segments(data)
        for name, start, size in Intervals.UI_WRITES:
            at = controls.rom_offset(data, start, size, segments)
            out[at:at + size] = hashlib.shake_128(name.encode()).digest(size)
        out += hashlib.shake_128(b'appended cartridge tail').digest(4096)
        return bytes(out)

    def composed(self, language):
        data = self.data(language)
        stage = self.earlier_stage(data)
        self.assertNotEqual(stage, data)
        return data, stage

    def test_accepted_after_a_stage_that_changes_bytes_outside_its_intervals(self):
        for language in controls.LANGUAGES:
            data, stage = self.composed(language)
            with self.subTest(language=language):
                controls.audit(stage, language)
                with tempfile.TemporaryDirectory() as work:
                    inert, receipt = self.prepare(stage, language, work)
                    self.assertEqual(controls.verify(stage, inert, receipt)['function_state'], 'inert')
                    active, receipt_active = self.prepare(stage, language, work, active=True)
                    self.assertEqual(controls.verify(stage, active, receipt_active)['function_state'], 'active')
                self.assertEqual(receipt['input_sha256'], hashlib.sha256(stage).hexdigest())
                self.assertNotEqual(receipt['input_sha256'], hashlib.sha256(data).hexdigest(), 'not the bare V4')
                # the stage's own bytes survive: only the slot and the three call sites differ from the composed input
                allowed = set(range(controls.rom_offset(stage, receipt['slot']['start']),
                                    controls.rom_offset(stage, receipt['slot']['start']) + receipt['payload']['bytes']))
                for site in receipt['sites']:
                    at = controls.rom_offset(stage, controls.hex_int(site))
                    allowed.update(range(at, at + 4))
                self.assertTrue(set(diff_offsets(stage, inert)) <= allowed)

    def test_order_independence_with_a_stage_that_runs_after_the_legend(self):
        """The same stage applied before or after the legend gives the same bytes when it avoids the legend's intervals."""
        data = self.data('EN')
        stage = self.earlier_stage(data)
        with tempfile.TemporaryDirectory() as work:
            first, _ = self.prepare(stage, 'EN', work)
            legend_first, _ = self.prepare(data, 'EN', work)
        later = bytearray(legend_first)
        segments = controls._arm9_segments(data)
        for name, start, size in Intervals.UI_WRITES:
            at = controls.rom_offset(data, start, size, segments)
            later[at:at + size] = hashlib.shake_128(name.encode()).digest(size)
        later += hashlib.shake_128(b'appended cartridge tail').digest(4096)
        self.assertEqual(bytes(later), first)

    def test_rejected_when_a_stage_touches_any_declared_interval(self):
        abi = controls.load_abi()
        rows = [row for row in controls.intervals(abi) if row['role'] == 'read']
        for language in ('EN',):
            data = self.data(language)
            for row in rows:
                for position in (row['start'], row['end'] - 1):
                    with self.subTest(interval=row['name'], at=hex(position)):
                        touched = bytearray(self.earlier_stage(data))
                        touched[controls.rom_offset(data, position)] ^= 0x01
                        with self.assertRaisesRegex(ValueError, 'pinned interval|literal-pool'):
                            controls.audit(bytes(touched), language)

    def test_prepare_refuses_a_touched_interval_of_every_class_before_compiling(self):
        classes = {'span': 0x02088B48, 'hook': 0x02088B40, 'native': 0x0201D4F8, 'table': 0x02104D04,
                   'background': 0x021038E8, 'literal': 0x02088414, 'viewer': 0x01FF8700}
        data = self.data('EN')
        stage = self.earlier_stage(data)
        for name, address in classes.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as work:
                touched = bytearray(stage)
                touched[controls.rom_offset(data, address)] ^= 0x10
                with self.assertRaises(ValueError):
                    controls.prepare(bytes(touched), 'EN', CHARMAP, Path(work),
                                     **slot_args(data, 'EN'))
                self.assertEqual(list(Path(work).iterdir()), [], 'nothing was compiled or written')

    def test_a_new_caller_of_a_hooked_function_is_refused(self):
        """Another stage that calls sub_0208C4E0 would bypass the legend's teardown: the complete edge list differs."""
        data = self.data('EN')
        stage = bytearray(self.earlier_stage(data))
        site = 0x02000100                                    # a spare word in the static image, outside every interval
        at = controls.rom_offset(data, site)
        stage[at:at + 4] = controls.encode_bl(site, 0x0208C4E1)
        with self.assertRaisesRegex(ValueError, r'edges\.teardown_callers'):
            controls.audit(bytes(stage), 'EN')

    def test_a_stage_that_rewrote_the_slot_is_refused_unless_its_residue_is_pinned_independently(self):
        data = self.data('EN')
        stage = bytearray(self.earlier_stage(data))
        stale = slot_args(data, 'EN')['preimage_sha256']
        at = controls.rom_offset(data, bench.INSTALL_BASE)
        stage[at + 8:at + 16] = b'\xAA' * 8                    # the stage left different bytes in the slot
        stage = bytes(stage)
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'preimage mismatch'):
                controls.prepare(stage, 'EN', CHARMAP, Path(work), allocation=bench.declared_allocation('EN'), preimage_sha256=stale)
            fresh = hashlib.sha256(controls.read(stage, bench.INSTALL_BASE, bench.SLOT_BYTES)).hexdigest()
            out, receipt = controls.prepare(stage, 'EN', CHARMAP, Path(work), allocation=bench.declared_allocation('EN'),
                                            preimage_sha256=fresh)
        controls.verify(stage, out, receipt)

    def test_the_legend_intervals_do_not_collide_with_the_other_c8_hook_sites(self):
        """Read-only composition check against the sites of portable box and rematches (disjoint by address)."""
        sites = {'portable.state1': 0x0207909C, 'portable.launch': 0x0203E572, 'portable.print32': 0x0207DAD2,
                 'portable.callback': 0x0203CA9C, 'rematches.seam': 0x0207363A}
        for row in controls.intervals():
            for name, site in sites.items():
                width = 12 if name == 'portable.callback' else 4
                self.assertTrue(row['end'] <= site or site + width <= row['start'], (row['name'], name))


def thumb_extent(data, start):
    """Independent (capstone) extent of a Thumb function: first return past every forward branch, plus its literal pool."""
    segments = controls._arm9_segments(data)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    forward, pool, end = start, 0, None
    for insn in md.disasm(controls.read(data, start, 0x3000, segments), start):
        pc = insn.address
        if insn.mnemonic == 'ldr' and 'pc' in insn.op_str and '#' in insn.op_str:
            pool = max(pool, ((pc + 4) & ~3) + int(insn.op_str.split('#')[-1].rstrip(']'), 0) + 4)
        branch = insn.mnemonic.startswith('b') and insn.mnemonic not in ('bl', 'blx', 'bx', 'bic', 'bics') and insn.op_str.startswith('#')
        target = int(insn.op_str[1:], 0) if branch else None
        if branch and target > pc:
            forward = max(forward, target)
        back = branch and insn.mnemonic == 'b' and target <= pc
        if (back or (insn.mnemonic == 'pop' and 'pc' in insn.op_str) or insn.mnemonic == 'bx') and pc + insn.size > forward:
            end = pc + insn.size
            break
    return start, (max(end or 0, pool) + 3) & ~3


def thumb_closure(data, roots):
    """Every static Thumb function reachable by BL from `roots` (an over-approximation; ARM and indirect calls not followed)."""
    segments = controls._arm9_segments(data)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    todo, seen = list(roots), {}
    while todo:
        start = todo.pop()
        if start in seen:
            continue
        _a, end = thumb_extent(data, start)
        seen[start] = end
        for insn in md.disasm(controls.read(data, start, end - start, segments), start):
            if insn.mnemonic == 'bl':
                target = int(insn.op_str[1:], 0)
                if 0x01FF8000 <= target < 0x02100000:
                    todo.append(target)
    return seen


class PostReview(Candidate):
    """Corrections after the independent review K-review: I1 whole bodies, I2 recompile in verify, I3 candidate gate,
    I5 independent preimage, M1 forged receipt fields, M5 charmap pin."""

    def mutate(self, data, address):
        broken = bytearray(data)
        broken[controls.rom_offset(data, address)] ^= 0xFF
        return bytes(broken)

    # --- I1 -----------------------------------------------------------------------------------------------
    def test_the_whole_body_of_every_native_function_and_of_the_page_change_function_is_pinned(self):
        abi = controls.load_abi()
        data = self.data('EN')
        points = {'get_box_data+0x40': 0x0206E680, 'copy_window+0x40': 0x0201D608, 'get_mon+0x30': 0x0208A550,
                  'heap_alloc+0x30': 0x0201AABC, 'code around the page-change site': 0x02089D70}
        for name, item in abi['natives'].items():
            self.assertIn('bytes', item, name)
            start, size = controls.hex_int(item['address']), item['bytes']
            self.assertEqual(thumb_extent(data, start)[1] - start, size, name + ': the pinned size is the function extent')
            points[name + ' first'], points[name + ' middle'], points[name + ' last'] = start, start + size // 2, start + size - 1
        function = abi['spans']['summary.page_change']
        start, size = controls.hex_int(function['address']), function['bytes']
        self.assertTrue(start < 0x02089D78 < start + size, 'the span holds the BL site')
        self.assertEqual(thumb_extent(data, start)[1] - start, size)
        points['page_change first'], points['page_change last'] = start, start + size - 1
        for name, address in points.items():
            with self.subTest(name, address=hex(address)), self.assertRaisesRegex(ValueError, 'pinned interval'):
                controls.audit(self.mutate(data, address), 'EN')

    def test_the_bytes_just_outside_a_pinned_body_are_not_pinned(self):
        """Exact boundaries: a neighbouring function is another stage's business and does not refuse the legend."""
        abi = controls.load_abi()
        data = self.data('EN')
        for name in ('fill_window', 'heap_free', 'add_window'):
            item = abi['natives'][name]
            after = controls.hex_int(item['address']) + item['bytes']
            controls.audit(self.mutate(data, after), 'EN')
            controls.audit(self.mutate(data, after + 2), 'EN')

    def test_callees_of_the_natives_are_outside_the_guarantee_but_the_ui_never_writes_them(self):
        """print+0x100 and fill_window+0x38 (reviewer gap.py) are callees: audit does not pin them. What holds the
        composition there is the closed list of writes of the other stages: the UI's 19 ARM9 writes miss every
        function statically reachable by BL from the natives."""
        abi = controls.load_abi()
        data = self.data('EN')
        for name, address in (('print+0x100', 0x020200FC + 0x100), ('fill_window+0x38', 0x0201D978 + 0x38)):
            controls.audit(self.mutate(data, address), 'EN')
        roots = [controls.hex_int(item['address']) for item in abi['natives'].values()]
        closure = thumb_closure(data, roots)
        self.assertGreater(len(closure), 100)
        self.assertGreater(sum(end - start for start, end in closure.items()), 10000)
        for start, end in closure.items():
            for name, ui_start, ui_size in Intervals.UI_WRITES:
                self.assertTrue(end <= ui_start or ui_start + ui_size <= start, '%#x..%#x vs UI write %s' % (start, end, name))

    # --- I2 -----------------------------------------------------------------------------------------------
    def test_verify_recompiles_the_payload_with_the_geometry_and_variant_of_the_receipt(self):
        en = self.data('EN')
        with tempfile.TemporaryDirectory() as work:
            out, receipt = self.prepare(en, 'EN', work, active=True, geometry=GEOMETRY)
        for charmap in (None, CHARMAP):
            self.assertEqual(controls.verify(en, out, receipt, charmap=charmap)['function_state'], 'active')
        g2 = dict(GEOMETRY, left=2, baseTile=960)
        swapped = copy.deepcopy(receipt)
        swapped['geometry'] = g2
        swapped['evidence'] = evidence_for(en, 'EN', g2, capture_rom_sha256=receipt['candidate_sha256'])
        swapped['evidence_sha256'] = hashlib.sha256(json.dumps(swapped['evidence'], sort_keys=True).encode()).hexdigest()
        spaced = copy.deepcopy(receipt)
        spaced['variant'] = 'spaced'
        for name, forged in (('geometry+evidence swapped', swapped), ('variant', spaced)):
            for charmap in (None, CHARMAP):
                with self.subTest(name, charmap=charmap is not None), self.assertRaisesRegex(ValueError, 'recompiled payload|legend variant'):
                    controls.verify(en, out, forged, charmap=charmap)
        # a different legend text, hashes made consistent: only the charmap-based check can tell
        slot = controls.rom_offset(en, receipt['slot']['start'])
        size = receipt['payload']['bytes']
        words = struct.unpack('<%dI' % (size // 4), out[slot:slot + size])
        string_at = slot + 4 * words.index(controls.STRING_MAGIC) + 4          # first glyph code follows the magic
        retext = bytearray(out)
        retext[string_at] ^= 0x01
        retext = bytes(retext)
        forged = copy.deepcopy(receipt)
        forged['output_sha256'] = hashlib.sha256(retext).hexdigest()
        forged['payload']['image_sha256'] = hashlib.sha256(retext[slot:slot + size]).hexdigest()
        controls.verify(en, retext, forged)                                      # without the charmap the text is not checked
        with self.assertRaisesRegex(ValueError, 'legend text'):
            controls.verify(en, retext, forged, charmap=CHARMAP)

    def test_the_evidence_hash_of_the_receipt_is_checked(self):
        en = self.data('EN')
        with tempfile.TemporaryDirectory() as work:
            out, receipt = self.prepare(en, 'EN', work, active=True, geometry=GEOMETRY)
        forged = dict(receipt, evidence_sha256='1' * 64)
        with self.assertRaisesRegex(ValueError, 'evidence hash'):
            controls.verify(en, out, forged)

    # --- I3 -----------------------------------------------------------------------------------------------
    def test_the_final_candidate_gate_refuses_an_invented_candidate(self):
        en = self.data('EN')
        invented = 'ab' * 32
        with tempfile.TemporaryDirectory() as work:
            out, receipt = self.prepare(en, 'EN', work, active=True, geometry=GEOMETRY, candidate_sha256=invented,
                                        evidence=evidence_for(en, 'EN', GEOMETRY, capture_rom_sha256=invented))
        self.assertEqual(receipt['candidate_relation'], 'composed-candidate', 'the installer alone cannot tell')
        with self.assertRaisesRegex(ValueError, 'not the candidate'):
            controls.candidate_gate(out, receipt)
        # the genuine candidate: the same final ROM with the activation word cleared
        view = controls.inert_view(out, receipt)
        genuine = hashlib.sha256(view).hexdigest()
        with tempfile.TemporaryDirectory() as work:
            out2, receipt2 = self.prepare(en, 'EN', work, active=True, geometry=GEOMETRY, candidate_sha256=genuine,
                                          evidence=evidence_for(en, 'EN', GEOMETRY, capture_rom_sha256=genuine))
        self.assertEqual(out2, out)
        controls.candidate_gate(out2, receipt2)
        # a receipt with no candidate cannot pass the gate
        with self.assertRaisesRegex(ValueError, 'no candidate'):
            controls.candidate_gate(out2, dict(receipt2, candidate_sha256=None))

    def test_inert_view_clears_only_the_activation_word_and_is_pure(self):
        en = self.data('EN')
        before, after, receipt = self.install('EN', active=True)
        snapshot = bytes(after)
        view = controls.inert_view(after, receipt)
        self.assertEqual(after, snapshot)
        self.assertEqual(len(view), len(after))
        changed = diff_offsets(after, view)
        at = controls.rom_offset(after, receipt['slot']['start'] + controls.STATE_ENABLED)
        self.assertEqual(changed, [at])
        self.assertEqual(controls.inert_view(view, receipt), view, 'idempotent')
        _b, inert, inert_receipt = self.install('EN', active=False)
        self.assertEqual(controls.inert_view(inert, inert_receipt), inert, 'an inert image is its own view')
        self.assertEqual(hashlib.sha256(view).hexdigest(), hashlib.sha256(inert).hexdigest(),
                         'same geometry: the inert view of the active image is the inert candidate')

    # --- I5 -----------------------------------------------------------------------------------------------
    def test_the_expected_preimage_comes_from_the_v4_not_from_the_stage_input(self):
        v4 = self.data('EN')
        allocation = bench.declared_allocation('EN')
        expected = controls.slot_preimage_from_v4(v4, 'EN', allocation)
        self.assertEqual(expected, slot_args(v4, 'EN')['preimage_sha256'])
        with self.assertRaisesRegex(ValueError, 'exact V4'):
            controls.slot_preimage_from_v4(self.earlier(v4), 'EN', allocation)
        stage = bytearray(self.earlier(v4))
        stage[controls.rom_offset(v4, bench.INSTALL_BASE) + 8] ^= 0x55           # a stage left residue in the slot
        stage = bytes(stage)
        with tempfile.TemporaryDirectory() as work:
            with self.assertRaisesRegex(ValueError, 'preimage mismatch'):
                controls.prepare(stage, 'EN', CHARMAP, Path(work), allocation=allocation, preimage_sha256=expected)
            tautology = hashlib.sha256(controls.read(stage, bench.INSTALL_BASE, bench.SLOT_BYTES)).hexdigest()
            self.assertNotEqual(tautology, expected, 'sha(rom[slot]) of the stage input is what the review called tautological')

    @staticmethod
    def earlier(v4):
        return Composition.earlier_stage(v4)

    # --- M1 -----------------------------------------------------------------------------------------------
    def test_verify_refuses_forged_candidate_and_capture_fields(self):
        en = self.data('EN')
        before, after, receipt = self.install('EN', active=True)
        other = hashlib.sha256(b'another candidate').hexdigest()
        cases = {
            'top-level capture differs (X2)': dict(receipt, capture_rom_sha256=other),
            'top-level capture dropped': dict(receipt, capture_rom_sha256=None),
            'candidate differs from the evidence': dict(receipt, candidate_sha256=other),
            'evidence of another candidate (X5)': dict(receipt, evidence=dict(receipt['evidence'], capture_rom_sha256=other),
                                                       evidence_sha256=hashlib.sha256(json.dumps(
                                                           dict(receipt['evidence'], capture_rom_sha256=other), sort_keys=True).encode()).hexdigest()),
            'evidence language (X5)': dict(receipt, evidence=dict(receipt['evidence'], language='IT'),
                                           evidence_sha256=hashlib.sha256(json.dumps(
                                               dict(receipt['evidence'], language='IT'), sort_keys=True).encode()).hexdigest()),
            'evidence without captures (X5)': dict(receipt, evidence=dict(receipt['evidence'], captures=[]),
                                                   evidence_sha256=hashlib.sha256(json.dumps(
                                                       dict(receipt['evidence'], captures=[]), sort_keys=True).encode()).hexdigest()),
            'evidence dropped from an active receipt': dict(receipt, evidence=None, evidence_sha256=None),
        }
        for name, forged in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                controls.verify(before, after, forged)

    # --- M5 -----------------------------------------------------------------------------------------------
    def test_the_charmap_is_pinned_and_recorded(self):
        en = self.data('EN')
        _b, _a, receipt = self.install('EN')
        self.assertEqual(receipt['charmap_sha256'], hashlib.sha256(CHARMAP.read_bytes()).hexdigest())
        self.assertEqual(receipt['charmap_sha256'], controls.CHARMAP_SHA256)
        with tempfile.TemporaryDirectory() as work:
            other = Path(work) / 'charmap.txt'
            other.write_text(CHARMAP.read_text(encoding='utf8') + '\n', encoding='utf8')
            with self.assertRaisesRegex(ValueError, 'charmap'):
                controls.prepare(en, 'EN', other, Path(work), **slot_args(en, 'EN'))


_UI = {}


def ui_output(test, language):
    """The REAL sgp131.ui.install output for a V4 input (read-only use of the UI stage, in memory, ~5 s)."""
    if language not in _UI:
        from sgp131 import ui
        from sgp131.test_ui import CONFIG
        data = rom_bytes(test, language)
        with tempfile.TemporaryDirectory(prefix='controls-ui-') as work:
            (Path(work) / 'ui-candidate.json').write_text(json.dumps(CONFIG))
            _UI[language] = (data, ui.install(data, language, CHARMAP, Path(work))[0])
    return _UI[language]


class RealUiComposition(Candidate):
    """C2 with the real UI stage instead of a synthetic one: the legend installs, verifies and leaves the UI alone."""

    def test_the_legend_composes_after_the_real_ui(self):
        for language in controls.LANGUAGES:
            v4, after_ui = ui_output(self, language)
            self.assertNotEqual(len(after_ui), len(v4), 'the UI extends the cartridge')
            with self.subTest(language=language), tempfile.TemporaryDirectory() as work:
                controls.audit(after_ui, language)
                cleared = bytes(bench.SLOT_BYTES)
                self.assertEqual(controls.read(after_ui, bench.INSTALL_BASE, bench.SLOT_BYTES),
                                 cleared, 'the real UI retires the old Guide slot')
                preimage = hashlib.sha256(cleared).hexdigest()
                for active in (False, True):
                    out, receipt = self.prepare(after_ui, language, work, active=active,
                                                preimage_sha256=preimage)
                    proof = controls.verify(after_ui, out, receipt)
                    self.assertEqual((proof['function_state'], receipt['input_sha256']),
                                     ('active' if active else 'inert', hashlib.sha256(after_ui).hexdigest()))
                    self.assertEqual(len(out), len(after_ui), 'no cartridge growth from this stage')
                    allowed = set(range(controls.rom_offset(after_ui, receipt['slot']['start']),
                                        controls.rom_offset(after_ui, receipt['slot']['start']) + receipt['payload']['bytes']))
                    for site in receipt['sites']:
                        at = controls.rom_offset(after_ui, controls.hex_int(site))
                        allowed.update(range(at, at + 4))
                    self.assertTrue(set(diff_offsets(after_ui, out)) <= allowed, 'only the slot and the three sites changed')

                residue = bytearray(after_ui)
                residue[controls.rom_offset(after_ui, bench.INSTALL_BASE)] = 1
                with self.assertRaisesRegex(ValueError, 'assigned slot preimage mismatch'):
                    self.prepare(bytes(residue), language, work,
                                 preimage_sha256=preimage)

    def test_the_ui_stage_refuses_the_legend_output_so_the_legend_must_run_second(self):
        """The other half of C2 lives in sgp131.ui (exact V4 required): documented, not fixed here."""
        from sgp131 import ui
        from sgp131.test_ui import CONFIG
        for language in ('EN',):
            data = self.data(language)
            legend, _ = self.install(language)[1:]
            with tempfile.TemporaryDirectory() as work:
                (Path(work) / 'ui-candidate.json').write_text(json.dumps(CONFIG))
                with self.assertRaises(ValueError):
                    ui.install(legend, language, CHARMAP, Path(work))


if __name__ == '__main__':
    unittest.main()
