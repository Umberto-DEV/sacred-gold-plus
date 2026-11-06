"""Host tests for the Summary controls legend (no ROM, no emulator).

Class A: pure functions and the JSON pin file. ARM9 bytes, Unicorn runs and the
installer on the real V4 ROMs live in test_controls_rom.py (Class B) and
features/summary-controls/test (compiled payload on Unicorn).
"""
import copy
import hashlib
import json
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from sgp13 import event_flags
from sgp131 import controls, mechanics_stages

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / 'features/summary-controls/test'))
import bench  # noqa: E402

# A synthetic charmap in pret's TSV-compatible shape: just the glyphs the legend needs.
CHARMAP_TEXT = '\n'.join([
    '01DE= ', '0145=a', '0146=b', '0147=c', '0148=d', '0149=e', '014A=f', '014B=g', '014C=h',
    '014D=i', '014E=j', '014F=k', '0150=l', '0151=m', '0152=n', '0153=o', '0154=p', '0155=q',
    '0156=r', '0157=s', '0158=t', '0159=u', '015A=v', '015B=w', '015C=x', '015D=y', '015E=z',
    '012B=A', '012C=B', '012D=C', '012E=D', '012F=E', '0130=F', '0131=G', '0132=H', '0133=I',
    '0134=J', '0135=K', '0136=L', '0137=M', '0138=N', '0139=O', '013A=P', '013B=Q', '013C=R',
    '013D=S', '013E=T', '013F=U', '0140=V', '0141=W', '0142=X', '0143=Y', '0144=Z',
    '01AE=.', '01AC=:',
]) + '\n'


def inventory():
    """A tiny synthetic bg4 inventory: one occupied tile range and one rectangle."""
    return {'bg': 4, 'tile_limit': 1024,
            'tiles': [{'name': 'shared.0', 'lo': 1, 'hi': 22}, {'name': 'skills.15', 'lo': 775, 'hi': 924},
                      {'name': 'skills.17', 'lo': 925, 'hi': 944}],
            'rects': [{'name': 'skills.17', 'left': 1, 'top': 17, 'width': 10, 'height': 2},
                      {'name': 'shared.29', 'left': 1, 'top': 17, 'width': 12, 'height': 2}]}


GEOMETRY = {'bgId': 4, 'left': 1, 'top': 18, 'width': 16, 'height': 2, 'palette': 13, 'baseTile': 955}
CANDIDATE = 'a' * 64      # the inert candidate ROM the capture was made on (declared fixture)
CAPTURE = {'name': 'IT-stats-normal-field.png', 'sha256': 'b' * 64}   # fixture reference, not a capture


def make_evidence(**over):
    """Fixture evidence for the synthetic inventory: a test double, never a runtime measurement."""
    record = {'kind': 'summary-window-inventory', 'capture_rom_sha256': CANDIDATE, 'build_id': 'fixture-not-a-build',
              'language': 'EN', 'geometry': dict(GEOMETRY),
              'views': ['stats', 'ev', 'iv'], 'button_modes': ['normal', 'L=A'], 'contexts': ['field', 'pc'],
              'captures': [CAPTURE], 'free_tiles': [955, 1023], 'hidden_windows': ['skills.17', 'shared.29']}
    record.update(over)
    return record


EVIDENCE = make_evidence()
BOUND = {'candidate_sha256': CANDIDATE, 'language': 'EN'}


class AbiFile(unittest.TestCase):
    def setUp(self):
        self.abi = controls.load_abi()

    def test_required_sections_and_hex_fields(self):
        for key in ('schema', 'rom', 'keys', 'spans', 'hooks', 'edges', 'natives', 'tables', 'bg', 'summary'):
            self.assertIn(key, self.abi)
        for name in ('viewer.payload', 'viewer.reader', 'viewer.reset_header', 'viewer.entries',
                     'summary.teardown', 'summary.alloc_pages', 'summary.exit', 'summary.dispatch',
                     'summary.stats_draw', 'summary.init_windows'):
            self.assertIn(name, self.abi['spans'], name)
            span = self.abi['spans'][name]
            self.assertRegex(span['sha256'], r'^[0-9a-f]{64}$')
            self.assertEqual(controls.hex_int(span['address']) % 2, 0)
            self.assertGreater(span['bytes'], 0)
        self.assertEqual(controls.hex_int(self.abi['keys']['raw_new']), 0x021D1148)
        self.assertEqual(sorted(self.abi['hooks']), ['input', 'redraw'])

    def test_inherited_label_wrapper_used_by_the_reader_is_pinned(self):
        self.assertIn('viewer.label_wrapper', self.abi['spans'])
        self.assertEqual(self.abi['spans']['viewer.label_wrapper']['address'], '0x01FF9348')

    def test_native_pins_cover_every_callee_of_the_runtime(self):
        header = (SOURCE / 'features/summary-controls/abi.h').read_text()
        self.assertIn('natives', self.abi)
        for name in ('heap_alloc', 'add_window', 'fill_window', 'copy_window', 'clear_window',
                     'delete_windows', 'print', 'get_mon', 'get_box_data'):
            self.assertIn(name, self.abi['natives'], name)
            address = controls.hex_int(self.abi['natives'][name]['address'])
            self.assertIn('0x%08Xu' % (address | 1), header, name)


class PinComparison(unittest.TestCase):
    def test_equal_pins_are_accepted(self):
        pins = {'spans': {'a': {'address': '0x1', 'sha256': 'x'}}}
        controls.compare_pins(copy.deepcopy(pins), pins)

    def test_changed_preimage_is_rejected_with_its_path(self):
        expected = {'spans': {'viewer.reader': {'address': '0x01FF8658', 'bytes': 448, 'sha256': 'aa'}}}
        actual = copy.deepcopy(expected)
        actual['spans']['viewer.reader']['sha256'] = 'bb'
        with self.assertRaisesRegex(ValueError, r'spans\.viewer\.reader\.sha256'):
            controls.compare_pins(actual, expected)

    def test_missing_and_extra_keys_are_rejected(self):
        expected = {'spans': {'a': {'sha256': 'x'}}}
        with self.assertRaisesRegex(ValueError, 'spans.a'):
            controls.compare_pins({'spans': {}}, expected)
        with self.assertRaisesRegex(ValueError, 'spans.b'):
            controls.compare_pins({'spans': {'a': {'sha256': 'x'}, 'b': {}}}, expected)


class Branches(unittest.TestCase):
    def test_bl_roundtrip_and_range(self):
        site, target = 0x0208C4E0, 0x0208C801
        raw = controls.encode_bl(site, target)
        self.assertEqual(len(raw), 4)
        self.assertEqual(controls.decode_bl(site, raw), target)
        with self.assertRaises(ValueError):
            controls.encode_bl(site, 0x027E0000 | 1)  # 7.7 MB away: out of Thumb BL range
        with self.assertRaises(ValueError):
            controls.encode_bl(site, 0x0208C800)      # ARM-mode target

    def test_literal_hook_roundtrip(self):
        raw = controls.encode_literal_hook(0x023C8101)
        self.assertEqual(raw.hex(), '004b18470181 3c02'.replace(' ', ''))
        self.assertEqual(controls.decode_literal_hook(raw), 0x023C8101)
        for broken in (raw[:3] + b'\x00' + raw[4:], raw[:6]):
            with self.assertRaises(ValueError):
                controls.decode_literal_hook(broken)


class Geometry(unittest.TestCase):
    def test_accepts_free_tiles_with_proven_hidden_windows(self):
        result = controls.check_geometry(GEOMETRY, inventory(), EVIDENCE, active=True, **BOUND)
        self.assertEqual(result['tiles'], [955, 986])
        self.assertEqual(result['overlapping_windows'], ['shared.29', 'skills.17'])

    def test_tile_overlap_rejected(self):
        for base in (944 - 31, 925, 1, 770, 775, 1000):  # last: runs past tile 1023
            geometry = dict(GEOMETRY, baseTile=base)
            with self.assertRaisesRegex(ValueError, 'tile'):
                controls.check_geometry(geometry, inventory(), make_evidence(geometry=geometry), active=True, **BOUND)

    def test_tile_overlap_is_rejected_even_when_inactive(self):
        with self.assertRaisesRegex(ValueError, 'tile'):
            controls.check_geometry(dict(GEOMETRY, baseTile=800), inventory(), None, active=False)

    def test_a_rectangle_over_a_native_window_needs_proof(self):
        with self.assertRaisesRegex(ValueError, 'window'):
            controls.check_geometry(GEOMETRY, inventory(), make_evidence(hidden_windows=['skills.17']), active=True, **BOUND)
        with self.assertRaisesRegex(ValueError, 'evidence'):
            controls.check_geometry(GEOMETRY, inventory(), None, active=True)

    def test_inactive_does_not_need_evidence_but_is_marked_unproven(self):
        result = controls.check_geometry(GEOMETRY, inventory(), None, active=False)
        self.assertFalse(result['proven'])

    def test_evidence_must_cover_the_tile_range(self):
        with self.assertRaisesRegex(ValueError, 'free tiles'):
            controls.check_geometry(GEOMETRY, inventory(), make_evidence(free_tiles=[960, 1023]), active=True, **BOUND)

    def test_shape_limits(self):
        for broken in (dict(GEOMETRY, bgId=1), dict(GEOMETRY, width=0), dict(GEOMETRY, left=20, width=16),
                       dict(GEOMETRY, top=23), dict(GEOMETRY, palette=16), dict(GEOMETRY, height=3)):
            with self.assertRaises(ValueError, msg=broken):
                controls.check_geometry(broken, inventory(), make_evidence(geometry=broken), active=True, **BOUND)


class EvidenceBinding(unittest.TestCase):
    def reject(self, pattern, **over):
        with self.assertRaisesRegex(ValueError, pattern):
            controls.check_geometry(GEOMETRY, inventory(), make_evidence(**over), active=True, **BOUND)

    def test_evidence_of_another_rom_or_language_is_refused(self):
        self.reject('another ROM', capture_rom_sha256='c' * 64)
        self.reject('another language', language='IT')

    def test_evidence_for_another_geometry_is_refused(self):
        self.reject('different geometry', geometry=dict(GEOMETRY, width=17))
        self.reject('different geometry', geometry=dict(GEOMETRY, baseTile=956))

    def test_every_view_key_mode_and_context_must_be_covered(self):
        self.reject('views', views=['stats', 'ev'])
        self.reject('button_modes', button_modes=['normal'])
        self.reject('button_modes', button_modes=['L=A'])
        self.reject('contexts', contexts=['field'])

    def test_captures_must_be_cited_by_hash(self):
        self.reject('capture references', captures=[])
        self.reject('capture references', captures=[{'name': 'x.png'}])
        self.reject('capture references', captures=[{'name': 'x.png', 'sha256': 'zz'}])

    def test_unknown_fields_and_wrong_kind_are_refused(self):
        self.reject('exactly', note='free text')
        self.reject('summary-window-inventory', kind='probe')

    def test_without_the_binding_arguments_the_evidence_cannot_match(self):
        with self.assertRaisesRegex(ValueError, 'candidate_sha256'):
            controls.check_geometry(GEOMETRY, inventory(), EVIDENCE, active=True)
        for bad in (None, '', 'A' * 64, 'a' * 63, 7):
            with self.subTest(candidate=bad), self.assertRaisesRegex(ValueError, 'candidate_sha256'):
                controls.check_geometry(GEOMETRY, inventory(), EVIDENCE, active=True, candidate_sha256=bad, language='EN')

    def test_capture_identity_fields_are_mandatory_and_well_formed(self):
        for missing in ('capture_rom_sha256', 'build_id'):
            record = make_evidence()
            del record[missing]
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'exactly'):
                controls.check_geometry(GEOMETRY, inventory(), record, active=True, **BOUND)
        self.reject('capture_rom_sha256 must be', capture_rom_sha256='ABC')
        self.reject('build_id', build_id=' ')
        self.reject('build_id', build_id=3)
        # the old key (the sha of the stage input) is no longer a field
        record = make_evidence()
        record['rom_sha256'] = record.pop('capture_rom_sha256')
        with self.assertRaisesRegex(ValueError, 'exactly'):
            controls.check_geometry(GEOMETRY, inventory(), record, active=True, **BOUND)

    def test_reserve_range_is_imported_not_duplicated(self):
        from sgp131 import reserve
        self.assertEqual((reserve.BASE, reserve.END), (0x023C8000, 0x023E0000))
        source = (SOURCE / 'sgp131/controls.py').read_text()
        self.assertNotIn('0x023C8000', source)
        self.assertNotIn('0x023E0000', source)


class Legend(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.charmap = Path(self.dir.name) / 'charmap.txt'
        self.charmap.write_text(CHARMAP_TEXT, encoding='utf-8')

    def tearDown(self):
        self.dir.cleanup()

    def test_text_per_language(self):
        self.assertEqual(controls.legend_text('EN'), 'L:EV SELECT:Stat. R:IV')
        self.assertEqual(controls.legend_text('IT'), 'L:EV SELECT:Stat. R:IV')
        self.assertEqual(controls.legend_text('IT', 'spaced'), 'L:EV  SELECT:Stat.  R:IV')
        with self.assertRaises(ValueError):
            controls.legend_text('FR')
        with self.assertRaises(ValueError):
            controls.legend_text('EN', 'loud')

    def test_encoding_uses_the_charmap_and_terminates(self):
        codes = controls.encode_legend('EN', self.charmap)
        self.assertEqual(codes[0], 0x0136)   # L
        self.assertEqual(codes[1], 0x01AC)   # :
        self.assertEqual(codes[-1], 0xFFFF)
        self.assertNotIn(0xE000, codes)       # one line only

    def test_unmapped_glyph_is_an_error_not_a_substitution(self):
        self.charmap.write_text(CHARMAP_TEXT.replace('01AC=:\n', ''), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'non mappati'):
            controls.encode_legend('EN', self.charmap)

    def test_string_object_has_the_native_header(self):
        codes = controls.encode_legend('EN', self.charmap)
        blob = controls.string_object(codes)
        self.assertGreaterEqual(len(blob), 8 + 2 * len(codes))
        maxsize, size, magic = struct.unpack_from('<HHI', blob, 0)
        self.assertEqual((maxsize, size, magic), (len(codes), len(codes), 0xB6F8D2EC))
        self.assertEqual(struct.unpack_from('<%dH' % len(codes), blob, 8), tuple(codes))
        self.assertEqual(len(blob) % 4, 0)

    def test_advance_measure_adds_glyph_widths_and_flags_unknown_codes(self):
        table = bytes([6] * 509)
        codes = [0x0136, 0x01AC, 0xFFFF]
        self.assertEqual(controls.measure_advance(table, codes), 12)
        with self.assertRaisesRegex(ValueError, 'width'):
            controls.measure_advance(table, [0x0300, 0xFFFF])


class PrepareContract(unittest.TestCase):
    NOWHERE = (Path('/nonexistent'), Path('/nonexistent'))

    def test_prepare_refuses_without_a_reserve_allocation(self):
        with self.assertRaisesRegex(ValueError, 'allocation'):
            controls.prepare(b'', 'EN', *self.NOWHERE, preimage_sha256='0' * 64)
        with self.assertRaises(TypeError):
            controls.prepare(b'', 'EN', *self.NOWHERE, base={'start': 0x023C8000})     # the old free-form base is gone

    def test_the_preimage_hash_of_the_slot_is_mandatory(self):
        with bench.declared_reserve():
            for bad in (None, '', 'zz' * 32, 'A' * 64, 'a' * 63):
                with self.subTest(preimage=bad), self.assertRaisesRegex(ValueError, 'sha256 of the bytes'):
                    controls.prepare(b'', 'EN', *self.NOWHERE, allocation=bench.declared_allocation('EN'), preimage_sha256=bad)

    def test_a_malformed_candidate_is_refused_even_when_inert(self):
        with bench.declared_reserve():
            for bad in ('ABC', 'a' * 63, 'A' * 64, 7):
                with self.subTest(candidate=bad), self.assertRaisesRegex(ValueError, 'candidate_sha256 must be'):
                    controls.prepare(b'', 'EN', *self.NOWHERE, allocation=bench.declared_allocation('EN'),
                                     preimage_sha256='0' * 64, candidate_sha256=bad)

    def test_prepare_refuses_activation_without_geometry_evidence_and_candidate(self):
        with bench.declared_reserve():
            kwargs = dict(allocation=bench.declared_allocation('EN'), preimage_sha256='0' * 64, active=True)
            with self.assertRaisesRegex(ValueError, 'geometry'):
                controls.prepare(b'', 'EN', *self.NOWHERE, **kwargs)
            with self.assertRaisesRegex(ValueError, 'candidate_sha256'):
                controls.prepare(b'', 'EN', *self.NOWHERE, geometry=GEOMETRY, evidence=EVIDENCE, **kwargs)
            with self.assertRaisesRegex(ValueError, 'candidate_sha256'):
                controls.prepare(b'', 'EN', *self.NOWHERE, geometry=GEOMETRY, evidence=EVIDENCE, candidate_sha256='X', **kwargs)


class AllocationReceipt(unittest.TestCase):
    """The base is accepted only from a reserve.allocate receipt checked against the policy in force."""

    def check(self, **override):
        return controls.check_allocation(bench.declared_allocation('EN', **override), 'EN')

    def test_the_declared_double_is_accepted_and_returns_the_assignment(self):
        with bench.declared_reserve():
            row = self.check()
        start, size = bench.real_slot()
        self.assertEqual(row, {'name': controls.SLOT_NAME, 'parent': 'test.declared-parent', 'start': start,
                               'bytes': size, 'capacity': size})

    def test_the_real_policy_refuses_a_receipt_made_under_the_double(self):
        with bench.real_reserve(), self.assertRaisesRegex(ValueError, 'policy in force'):
            self.check()

    def test_the_real_policy_has_no_grantable_slot_for_the_legend_yet(self):
        """summary-controls.runtime sits under field-guide.code, a conditional owner: a receipt that claims it is
        refused even when it carries the real policy digest. This is the delta Codex must lift (INTEGRATION.md)."""
        policy, digest = controls._reserve_policy()
        start, size = bench.real_slot()
        forged = bench.declared_allocation('EN', policy_version=policy['version'], policy_sha256=digest)
        forged['assignments'][0].update(parent='field-guide.code')
        with self.assertRaisesRegex(ValueError, 'conditional'):
            controls.check_allocation(forged, 'EN')

    def test_every_forgery_of_a_good_receipt_is_refused(self):
        start, size = bench.real_slot()
        base = bench.declared_allocation('EN')
        cases = {
            'wrong policy digest': dict(policy_sha256='1' * 64),
            'wrong policy version': dict(policy_version='sgp131-resident-5'),
            'schema': dict(schema=2),
            'language': dict(language='IT'),
            'input is not a V4': dict(input_sha256='2' * 64),
            'input of the other language': dict(input_sha256=next(h for h, l in bench.INPUT_HASHES.items() if l == 'IT')),
            'installed': dict(installed=True),
            'authorized': dict(installation_authorized=True),
            'not reserved': dict(address_reserved=False),
            'audit hash': dict(audit_sha256='zz'),
            'name not requested': dict(requested={'other.slot': size}),
            'unknown slot': dict(requested={controls.SLOT_NAME: size, 'nobody.slot': 4},
                                 assignments=base['assignments']),
            'size over capacity': dict(requested={controls.SLOT_NAME: size + 4},
                                       assignments=[dict(base['assignments'][0], bytes=size + 4)]),
            'start moved': dict(assignments=[dict(base['assignments'][0], start=start + 4)]),
            'start outside the slot': dict(assignments=[dict(base['assignments'][0], start=0x023C8000)]),
            'bytes differ from the request': dict(assignments=[dict(base['assignments'][0], bytes=size - 4)]),
            'capacity differs': dict(assignments=[dict(base['assignments'][0], capacity=size * 2)]),
            'parent differs': dict(assignments=[dict(base['assignments'][0], parent='someone.else')]),
            'extra assignment': dict(assignments=base['assignments'] + [dict(base['assignments'][0], name='x')]),
            'no assignment': dict(assignments=[]),
        }
        with bench.declared_reserve():
            for name, override in cases.items():
                with self.subTest(name):
                    with self.assertRaises(ValueError):
                        controls.check_allocation(dict(base, **override), 'EN')
            for field in list(base):
                broken = dict(base)
                del broken[field]
                with self.subTest(missing=field), self.assertRaises(ValueError):
                    controls.check_allocation(broken, 'EN')
            for junk in (None, [], 'receipt', {**base, 'extra': 1}):
                with self.subTest(junk=type(junk).__name__), self.assertRaises(ValueError):
                    controls.check_allocation(junk, 'EN')

    def test_a_receipt_for_another_owner_does_not_grant_this_slot(self):
        """A genuine-looking receipt for a different payload name is refused for the legend."""
        start, size = bench.real_slot()
        other = bench.declared_allocation('EN', requested={'training.ui': 1536},
                                          assignments=[{'name': 'training.ui', 'parent': 'training.extension',
                                                        'start': 0x023D6800, 'bytes': 1536, 'capacity': 1536}])
        with bench.declared_reserve(), self.assertRaises(ValueError):
            controls.check_allocation(other, 'EN')


class Intervals(unittest.TestCase):
    """Permanent UI payloads stay separate; cold retirement precedes verified grants."""

    # Every ARM9 write of sgp131/ui.py (static image and reserve), as (name, start, bytes). The test below
    # re-reads ui.py / ui_compile.py and fails if a write is added that this list does not know.
    UI_DIRECT_WRITES = (
        ('bridge payload', 0x023CB800, 12272), ('physical payload', 0x023D6E10, 1024),
        ('training payload', 0x023D6800, 1536), ('fieldbook payload', 0x023D4000, 3072),
        ('settings template', 0x020FA354, 16), ('guide template', 0x023D7B10, 16),
        ('bootstrap clear', 0x023D7B20, 40), ('control clear', 0x023D7B48, 16),
        ('physical slot clear', 0x023D7210, 48), ('shiny generation clear', 0x023CB1F0, 16),
        ('shiny descriptor', 0x023CB1A0, 80), ('training bind', 0x023CB130, 4),
        ('physical mapping site', 0x0201A556, 4), ('physical lid site', 0x02000DB0, 4),
        ('fieldbook input site', 0x0203BFE4, 4), ('module seed', 0x023D7B60, 96),
        ('resource seed', 0x023D7BC0, 64), ('guide seed', 0x023D7C00, 64))

    # ui.py delegates these writes to event_flags.prepare_upgrade.  CONFIG at
    # 0x023CFEF0 is inside the complete payload, not a standalone four-byte
    # write.  Keep all five spans in the overlap policy.
    UI_DELEGATED_WRITES = (
        ('event flags payload', 0x023CF900, 1536),
        ('event flags getter hook', 0x0205045C, 8),
        ('event flags loader hook', 0x02027AD4, 8),
        ('event variable getter hook', 0x020403AC, 8),
        ('event SetVar hook', 0x02040F14, 8),
    )
    UI_WRITES = UI_DIRECT_WRITES + UI_DELEGATED_WRITES

    # This cold clear intentionally includes the later controls/portable child
    # slots. It is not a live UI payload: fresh Guide retirement and schema-2
    # grants are verified before those owners install their code.
    UI_RETIREMENTS = (('retired Guide clear', 0x023D4C00, 3776),)

    # Literals of ui.py that are not ARM9 byte writes: the image base, the overlay-27/54 addresses (patched inside
    # the decompressed overlay, not in the static ARM9 or the reserve), descriptor values and the autoload id.
    UI_NON_WRITES = {0x01000000, 0x02000000, 0x021E5900, 0x0225A0C6, 0x0225A184, 0x0225A40E, 0x0225A856,
                     0x0225A860, 0x0225A96E, 0x023D1321, 0x023D1A45, 0x023D1B1D, 0x027E0000}

    def test_ui_write_list_matches_ui_py(self):
        ui = (SOURCE / 'sgp131/ui.py').read_text()
        literals = {int(m, 16) for m in re.findall(r'0x0[0-9A-Fa-f]{7}', ui)}
        known = {start for _n, start, _b in self.UI_DIRECT_WRITES + self.UI_RETIREMENTS}
        self.assertTrue(known <= literals | {0x023CB800, 0x023D6E10, 0x023D6800, 0x023D4000})
        self.assertEqual(literals - known - self.UI_NON_WRITES, set(),
                         'sgp131/ui.py names an ARM9 address that this test neither lists as a write nor as a non-write')
        compiled = (SOURCE / 'sgp131/ui_compile.py').read_text()
        bases = {(name, int(base, 16), int(cap)) for name, base, cap in re.findall(
            r"_compile\(directory, '(physical|bridge|training|fieldbook)',[^()]*?[,\s]\s*(0x0[0-9A-Fa-f]{7}), (\d+),", compiled, re.S)}
        self.assertEqual(bases, {('physical', 0x023D6E10, 1024), ('bridge', 0x023CB800, 12272),
                                 ('training', 0x023D6800, 1536), ('fieldbook', 0x023D4000, 3072)})

    def test_delegated_event_flag_writes_are_complete_and_protected(self):
        self.assertEqual((event_flags.BASE, event_flags.SIZE, event_flags.CONFIG),
                         (0x023CF900, 1536, 0x023CFEF0))
        self.assertEqual(
            {(event_flags.GETTER, 8), (event_flags.LOAD, 8),
             (event_flags.VAR_GET, 8), (event_flags.SET_VAR, 8)},
            {(0x0205045C, 8), (0x02027AD4, 8),
             (0x020403AC, 8), (0x02040F14, 8)})
        protected_hooks = {(address, size) for _name, address, size
                           in mechanics_stages.UI_HOOKS}
        self.assertTrue({(address, size) for _name, address, size
                         in self.UI_DELEGATED_WRITES[1:]} <= protected_hooks)
        self.assertIn(('event-flags.runtime', 0x023CF900, 1536),
                      mechanics_stages.UI_RESERVE_SPANS)

    def test_pinned_intervals_never_overlap_what_the_ui_writes(self):
        rows = controls.intervals()
        names = {row['name'] for row in rows}
        self.assertTrue({'viewer.payload', 'summary.dispatch', 'hooks.input', 'natives.heap_alloc', 'tables.shared',
                         'bg.bg4', 'literals.viewer_keys_raw',
                         'site.0x0208CC5A'} <= names)
        for row in rows:
            for name, start, size in self.UI_WRITES:
                with self.subTest(interval=row['name'], ui=name):
                    self.assertTrue(row['end'] <= start or start + size <= row['start'],
                                    '%s %#x..%#x overlaps the UI write %s' % (row['name'], row['start'], row['end'], name))

    def test_the_slot_of_the_reserve_policy_is_clear_of_the_ui_payloads(self):
        start, size = bench.real_slot()
        for name, ui_start, ui_size in self.UI_WRITES:
            self.assertTrue(start + size <= ui_start or ui_start + ui_size <= start, name)

    def test_write_intervals_are_exactly_the_three_sites(self):
        writes = [row for row in controls.intervals() if row['role'] == 'write']
        self.assertEqual(sorted(row['start'] for row in writes), [0x02089D78, 0x0208C564, 0x0208CC5A])
        self.assertTrue(all(row['end'] - row['start'] == 4 for row in writes))

    def test_intervals_follow_the_pin_file(self):
        abi = controls.load_abi()
        rows = {row['name']: row for row in controls.intervals(abi)}
        for name, span in abi['spans'].items():
            self.assertEqual((rows[name]['start'], rows[name]['end']),
                             (controls.hex_int(span['address']), controls.hex_int(span['address']) + span['bytes']))

    def test_no_code_path_hashes_the_whole_rom(self):
        source = (SOURCE / 'sgp131/controls.py').read_text()
        code = re.sub(r'#.*', '', source)
        self.assertNotIn("abi['rom']", code)
        self.assertIsNone(re.search(r"_sha\(data\) ==|_sha\(before\) == abi", code))


class ReceiptHygiene(unittest.TestCase):
    def test_no_process_state_is_written_by_the_code(self):
        source = (SOURCE / 'sgp131/controls.py').read_text()
        for word in ('SOURCE_READY_FOR_REVIEW', 'ANDROID_ACCEPTED', "'android'", 'not run', "'status'"):
            self.assertNotIn(word, source, word)


if __name__ == '__main__':
    unittest.main()
