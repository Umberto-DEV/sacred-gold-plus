"""Class B: mechanical stages composed after the real UI stage, entirely in memory.

Inputs: SGP131_BASE_EN / SGP131_BASE_IT (the immutable V4 originals) and SGP131_UI_CHARMAP
(the pret charmap pinned by guide_content). Set SGP131_MECHANICS_REQUIRE_INPUTS=1 to make
missing inputs failures. Nothing is written to disk except a temporary UI scratch directory
that build.compose removes itself; no ROM leaves memory.

Invariants are asserted here from independent struct reads, not from mechanics_stages.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from sgp12.rom import Rom
from . import build, mechanics_stages as ms
from .test_ui import CONFIG

_CACHE = {}
# Mutation runs set SGP131_MECHANICS_LANGS=EN to halve the time; the default and every acceptance run cover both.
LANGUAGES = tuple(os.environ.get('SGP131_MECHANICS_LANGS', 'EN,IT').split(','))


def read(rom, offset, n):
    return struct.unpack_from('<%dI' % n, rom, offset)


def tables(rom):
    fat, fat_bytes, y9, y9_bytes = read(rom, 0x48, 4)
    return fat, fat_bytes, y9, y9_bytes


def fat_entry(rom, fid):
    fat = tables(rom)[0]
    return struct.unpack_from('<II', rom, fat + 8 * fid)


def y9_crc(rom):
    _, _, y9, y9_bytes = tables(rom)
    return zlib.crc32(rom[y9:y9 + y9_bytes])


class RealUiBase(unittest.TestCase):
    def fairy_row(self):
        parent, part = ms.reserve_slot(ms.FAIRY_AI_SLOT)
        return {'name': part['name'], 'parent': parent, 'start': part['start'],
                'bytes': ms.FAIRY_AI_PAYLOAD_BYTES, 'capacity': part['bytes']}

    def inputs(self, language):
        path, charmap = os.environ.get('SGP131_BASE_' + language), os.environ.get('SGP131_UI_CHARMAP')
        if not path or not charmap:
            message = 'missing V4 %s input or UI charmap' % language
            if os.environ.get('SGP131_MECHANICS_REQUIRE_INPUTS') == '1':
                self.fail(message)
            self.skipTest(message)
        return Path(path), Path(charmap)

    def ui(self, language):
        """V4 -> real UI stage (cached per language): base, UI image, UI report, consumed inputs."""
        if language in _CACHE:
            return _CACHE[language]
        path, charmap = self.inputs(language)
        base = path.read_bytes()
        self.assertEqual(hashlib.sha256(base).hexdigest(), next(h for h, l in build.baseline.INPUT_HASHES.items()
                                                                if l == language))
        directory = tempfile.TemporaryDirectory(prefix='mechanics-ui-')
        unittest.addModuleCleanup(directory.cleanup)
        top = Path(directory.name).resolve()
        config = top / 'ui-candidate.json'
        config.write_text(json.dumps(CONFIG))
        image, report = build.compose(base, 'ui', charmap, top / 'scratch', ui_config=config)
        inputs = build.snapshot_ui_inputs(charmap, config)
        _CACHE[language] = (base, image, report, inputs, top)
        return _CACHE[language]

    def verify_ui(self, language):
        base, _, report, inputs, top = self.ui(language)
        counter = []

        def verify(image):
            counter.append(1)
            return build.verify_composition(base, image, report['receipts'], through='ui', ui_inputs=inputs,
                                            scratch=top / ('verify-%d' % len(counter)))
        return verify


class PostUiChain(RealUiBase):
    def chain(self, language, order=('moves', 'ai')):
        _, image, _, _, _ = self.ui(language)
        data, receipts = image, []
        for name in order:
            data, receipt = ms.run_stage(name, data, language,
                                         allocation=[self.fairy_row()])
            receipts.append(receipt)
        return image, data, receipts

    def test_stages_reconcile_only_overlay12_y9_and_its_derived_ui_seed(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                before_sources = build.source_snapshot()
                image, final, receipts = self.chain(language)
                # independent struct reads; expected values come from the UI image itself
                self.assertEqual(len(final), len(image))
                self.assertNotEqual(y9_crc(final), y9_crc(image))
                self.assertEqual(final[:0x200], image[:0x200])
                for fid in (27, 54, 156, 167):
                    self.assertEqual(fat_entry(final, fid), fat_entry(image, fid))
                self.assertEqual(struct.unpack_from('<I', final, 0x80)[0], len(final))
                self.assertEqual(struct.unpack_from('<H', final, 0x15E)[0],
                                 struct.unpack_from('<H', image, 0x15E)[0])
                self.assertEqual([r['stage'] for r in receipts], ['moves', 'ai'])
                old12, new12 = fat_entry(image, 12), fat_entry(final, 12)
                self.assertEqual(old12[0], new12[0])
                # The exact shared writer now also owns the 340-byte HG-B08
                # reload replacement; the canonical BLZ stream grows by 28.
                self.assertEqual(new12[1] - old12[1], 28)
                self.assertEqual(ms.check_ui_seeds(final)['y9_crc32'], '%08x' % y9_crc(final))
                self.assertEqual(before_sources, build.source_snapshot())

    def test_moves_changes_one_byte_and_ai_changes_only_its_declared_regions(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                image, final, receipts = self.chain(language)
                m_start, m_end = fat_entry(image, 140)
                ranges = ms.changed_ranges(image, final)
                in_moves = [r for r in ranges if m_start <= r[0] and r[1] <= m_end]
                self.assertEqual(len(in_moves), 1)
                self.assertEqual(in_moves[0][1] - in_moves[0][0], 1)
                offset = in_moves[0][0]
                self.assertEqual((image[offset], final[offset]), (75, 85))     # Will-O-Wisp accuracy
                allowed = [(region['start'], region['end']) for receipt in receipts
                           for region in receipt['regions']]
                self.assertTrue(all(any(a <= start and end <= b for a, b in allowed)
                                    for start, end in ranges))
                y9 = tables(image)[2]
                self.assertEqual(final[y9 + 12 * 32:y9 + 12 * 32 + 28],
                                 image[y9 + 12 * 32:y9 + 12 * 32 + 28])
                self.assertNotEqual(final[y9 + 12 * 32 + 28:y9 + 13 * 32],
                                    image[y9 + 12 * 32 + 28:y9 + 13 * 32])

    def test_either_order_gives_the_same_rom_and_both_replay(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base = self.ui(language)[0]
                _, a, ra = self.chain(language, ('moves', 'ai'))
                _, b, rb = self.chain(language, ('ai', 'moves'))
                self.assertEqual(a, b)
                verify_ui = self.verify_ui(language)
                ms.verify_chain(base, a, ['moves', 'ai'], ra, verify_ui,
                                allocation=[self.fairy_row()])
                ms.verify_chain(base, b, ['ai', 'moves'], rb, verify_ui,
                                allocation=[self.fairy_row()])

    def test_chain_reconstruction_is_the_exact_ui_image_and_the_old_verifier_rejects_the_final(self):
        language = 'EN'
        base, image, report, inputs, top = self.ui(language)
        _, final, receipts = self.chain(language)
        seen = []

        def verify_ui(candidate):
            seen.append(candidate)
            return self.verify_ui(language)(candidate)
        result = ms.verify_chain(base, final, ['moves', 'ai'], receipts, verify_ui,
                                 allocation=[self.fairy_row()])
        self.assertEqual(seen, [image])
        self.assertEqual(result['ui_image_sha256'], hashlib.sha256(image).hexdigest())
        # Measured on both languages: handing the mechanics output straight to the UI verifier fails.
        with self.assertRaisesRegex(ValueError, 'foreign overlay table record|foreign active file'):
            build.verify_composition(base, final, report['receipts'], through='ui', ui_inputs=inputs,
                                     scratch=top / 'direct')

    def test_dedicated_ui_receipt_and_stage_receipts_survive_json_replay(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base = self.ui(language)[0]
                _, final, receipts = self.chain(language)
                replay = json.loads(json.dumps(receipts))
                ms.verify_chain(base, final, ['moves', 'ai'], replay, self.verify_ui(language),
                                allocation=[self.fairy_row()])


class BuilderChain(RealUiBase):
    """The builder patch wired to the real stages: compose, independent replay, provenance."""

    def test_compose_through_ai_equals_the_manual_chain_and_replays_independently(self):
        from . import evidence
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, image, _, inputs, top = self.ui(language)
                path, charmap = self.inputs(language)
                config = top / 'ui-candidate.json'
                data, report = build.compose(base, 'ai', charmap, top / ('scratch-' + language), ui_config=config)
                manual = image
                for name in ('moves', 'ai'):
                    manual, _ = ms.run_stage(name, manual, language,
                                             allocation=[self.fairy_row()])
                self.assertEqual(data, manual)
                self.assertEqual([r['stage'] for r in report['receipts']], ['ui', 'moves', 'ai'])
                self.assertEqual(report['required_cases'], list(build.REQUIRED_CASES['ai']))
                self.assertLessEqual(len(build.canonical(report)), build.RECEIPT_LIMIT)
                json.loads(json.dumps(report))
                evidence.validate_provenance(report)
                replayed = build.verify_composition(base, data, report['receipts'], through='ai', ui_inputs=inputs,
                                                    scratch=top / ('replay-' + language))
                self.assertEqual(replayed, report['composition'])
                for forged in (self.flip(data, 0x80), self.flip(data, ms.ui_seed_state(data)[0].fat + 156 * 8)):
                    with self.assertRaises(ValueError):
                        build.verify_composition(base, forged, report['receipts'], through='ai', ui_inputs=inputs,
                                                 scratch=top / ('forged-' + language))

    def assert_compose_through_traded_egg(self, language):
        base, _, _, inputs, top = self.ui(language)
        _, charmap = self.inputs(language)
        config = top / 'ui-candidate.json'
        data, report = build.compose(
            base, 'traded-egg', charmap,
            top / ('traded-egg-' + language), ui_config=config)
        self.assertEqual([row['stage'] for row in report['receipts']],
                         ['ui', 'moves', 'ai', 'ai-immunities',
                          'abilities', 'legacy', 'legendary-scene-version', 'trainer-fixes',
                          'pokeathlon', 'traded-egg'])
        self.assertEqual(report['required_cases'],
                         list(build.REQUIRED_CASES['traded-egg']))
        replayed = build.verify_composition(
            base, data, report['receipts'], through='traded-egg',
            ui_inputs=inputs, scratch=top / ('traded-egg-replay-' + language))
        self.assertEqual(replayed, report['composition'])

    def test_compose_through_traded_egg_replays_the_complete_prefix_en(self):
        self.assert_compose_through_traded_egg('EN')

    def test_compose_through_traded_egg_replays_the_complete_prefix_it(self):
        self.assert_compose_through_traded_egg('IT')

    def test_compose_through_bag_foreign_replays_training_successor(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, _, _, inputs, top = self.ui(language)
                _, charmap = self.inputs(language)
                config = top / 'ui-candidate.json'
                data, report = build.compose(
                    base, 'bag-foreign', charmap,
                    top / ('bag-foreign-' + language), ui_config=config)
                self.assertEqual([row['stage'] for row in report['receipts']],
                                 ['ui', 'moves', 'ai', 'ai-immunities',
                                  'abilities', 'legacy', 'legendary-scene-version', 'trainer-fixes',
                                  'pokeathlon', 'traded-egg', 'bag-foreign'])
                self.assertEqual(report['required_cases'],
                                 list(build.REQUIRED_CASES['bag-foreign']))
                replayed = build.verify_composition(
                    base, data, report['receipts'], through='bag-foreign',
                    ui_inputs=inputs,
                    scratch=top / ('bag-foreign-replay-' + language))
                self.assertEqual(replayed, report['composition'])

    def flip(self, rom, offset):
        out = bytearray(rom)
        out[offset] ^= 1
        return bytes(out)

    def test_through_ui_is_unchanged_by_the_chain_support(self):
        for language in LANGUAGES:
            base, image, report, inputs, top = self.ui(language)
            self.assertEqual([r['stage'] for r in report['receipts']], ['ui'])
            self.assertEqual(report['composition']['stage'], 'ui')
            self.assertEqual(report['required_cases'], list(build.UI_CASES))


def forge_receipts(base, mutated, names, honest):
    """Receipts an attacker could produce for `mutated`: every step hash, range and stage-receipt hash recomputed.

    The independent re-derivation is written here with plain slicing, not taken from mechanics_stages.
    """
    stages = [ms.require_stage(name) for name in names]
    declared = [list(stage.regions(base)) for stage in stages]
    images = ms.intermediate_images(base, mutated, stages, declared)
    forged = []
    for index, (name, receipt) in enumerate(zip(names, honest)):
        previous, step = images[index], images[index + 1]
        new = copy.deepcopy(receipt)
        new['input_sha256'], new['output_sha256'] = hashlib.sha256(previous).hexdigest(), hashlib.sha256(step).hexdigest()
        new['changed_ranges'] = [list(pair) for pair in ms.changed_ranges(previous, step)]
        raw = new['stage_receipt']
        for key in ('input_sha256', 'output_sha256'):
            if key in raw:
                raw[key] = new[key]
        new['stage_receipt_sha256'] = hashlib.sha256(ms.canonical(raw)).hexdigest()
        forged.append(new)
    return forged


class FalsifiedReceipts(RealUiBase):
    """Receipts forged for the mutated ROM must still be refused by the independent verifiers.

    With the UI verifier skipped (mutant O) the bytes outside the declared regions are no longer seen by
    anything but `verify_ui`, so these cases kill that mutant in Class B.
    """

    def chain_final(self, language):
        base, image, _, _, _ = self.ui(language)
        data, receipts = image, []
        for name in ('moves', 'ai'):
            data, receipt = ms.run_stage(name, data, language,
                                         allocation=[self.fairy_row()])
            receipts.append(receipt)
        return base, data, receipts

    def mutate(self, rom, offset):
        out = bytearray(rom)
        out[offset] ^= 0x5A
        return bytes(out)

    def test_foreign_bytes_outside_the_declared_regions_are_refused_with_forged_receipts(self):
        for language in LANGUAGES:
            base, final, honest = self.chain_final(language)
            view = self.layout(final)
            verify_ui = self.verify_ui(language)
            cases = [
                ('Guide archive file 156', view.files[156][0] + 100, 'Guide member table/names'),
                ('overlay 27 file', view.files[27][0] + 60, 'foreign overlay27 hook'),
                ('UIR resource file 167', view.files[167][0] + 20, 'archive block bounds'),
                ('module seed', view.offset(0x023D7B60 + 68, 4),
                 'postimage Module96 final seed|ui.module.seed|crc32'),
                ('reserve training slot', view.offset(0x023D746C, 4),
                 'protected cartridge bytes|combined AI/damage replay differs'),
                ('ARM9 static byte', view.offset(0x02000000 + 0x2000, 1), 'protected cartridge bytes'),
                ('neighbour file 141', view.files[141][0] + 8, 'foreign active file 141'),
                ('neighbour file 11', view.files[11][0] + 8, 'foreign active file 11'),
                ('last byte of the ROM', len(final) - 1, 'text glyph/EOS'),
            ]
            for label, offset, reason in cases:
                mutated = self.mutate(final, offset)
                forged = forge_receipts(base, mutated, ['moves', 'ai'], honest)
                with self.subTest(language=language, case=label), self.assertRaisesRegex(ValueError, reason):
                    ms.verify_chain(base, mutated, ['moves', 'ai'], forged, verify_ui,
                                    allocation=[self.fairy_row()])

    def test_extra_bytes_inside_the_declared_regions_are_refused_by_the_4a_readers(self):
        for language in LANGUAGES:
            base, final, honest = self.chain_final(language)
            view = self.layout(final)
            verify_ui = self.verify_ui(language)
            moves_start, moves_end = view.files[140]
            ai_start, ai_end = view.files[12]
            cases = [('file 140 NARC BTAF magic', moves_start + 0x10, 'not a NARC archive'),
                     ('file 140 last byte', moves_end - 1, 'archive member 470 changed'),
                     ('file 12 middle of the stream', ai_start + 5000,
                      'logical bytes differ outside the declared delta|combined AI/damage replay differs'),
                     ('file 12 stream tail', ai_end - 20,
                      'logical bytes differ outside the declared delta|combined AI/damage replay differs')]
            for label, offset, reason in cases:
                mutated = self.mutate(final, offset)
                forged = forge_receipts(base, mutated, ['moves', 'ai'], honest)
                with self.subTest(language=language, case=label), self.assertRaisesRegex(ValueError, reason):
                    ms.verify_chain(base, mutated, ['moves', 'ai'], forged, verify_ui,
                                    allocation=[self.fairy_row()])

    def test_control_the_forging_helper_reproduces_the_honest_receipts_exactly(self):
        base, final, honest = self.chain_final('EN')
        again = forge_receipts(base, final, ['moves', 'ai'], honest)
        self.assertEqual(again, honest)
        ms.verify_chain(base, final, ['moves', 'ai'], again, self.verify_ui('EN'),
                        allocation=[self.fairy_row()])

    def layout(self, rom):
        from . import ui_verify
        return ui_verify.Image(rom)



class UiHooksAndFailClosed(RealUiBase):
    HOOKS = (('Options template', 0x020FA354, 16), ('physical hook', 0x0201A556, 4),
             ('physical lid hook', 0x02000DB0, 4), ('Fieldbook task hook', 0x0203BFE4, 4))

    def layout(self, rom):
        from . import ui_verify
        return ui_verify.Image(rom)

    def test_arm9_hooks_and_templates_outside_the_reserve_are_protected(self):
        for language in LANGUAGES:
            image = self.ui(language)[1]
            view = self.layout(image)
            regions = ms.require_stage('moves').regions(image)
            for label, address, size in self.HOOKS:
                at = view.offset(address, size)
                self.assertFalse(0x023C8000 <= address < 0x023E0000)            # the hooks live outside the reserve
                for index in (0, size - 1):
                    changed = bytearray(image)
                    changed[at + index] ^= 0xFF
                    with self.subTest(language=language, hook=label, index=index), \
                            self.assertRaisesRegex(ms.CompositionError, 'UI hook'):
                        ms.check_ui_invariants(image, bytes(changed), regions)
                with self.subTest(language=language, hook=label, case='declared'), \
                        self.assertRaisesRegex(ms.CompositionError, 'protected'):
                    ms.check_ui_invariants(image, image, [ms.Region(at, at + size, 'x')])

    def test_mutated_name_table_cannot_crash_the_readers(self):
        image = self.ui('EN')[1]
        view = self.layout(image)
        regions = ms.require_stage('moves').regions(image)
        raw_types = set()
        for offset, value in ((0, 0xFF), (4, 0xFF), (8, 0xFF), (12, 0xFF), (0x20, 0xFF), (view.fnt_bytes // 2, 0xFF)):
            for width in (1, 4):
                changed = bytearray(image)
                changed[view.fnt + offset:view.fnt + offset + width] = bytes([value]) * width
                changed = bytes(changed)
                try:
                    self.layout(changed)
                except Exception as error:      # what the raw reader does with this mutation
                    raw_types.add(type(error))
                with self.subTest(offset=offset, width=width):
                    try:
                        ms.check_ui_invariants(image, changed, regions)
                        ms.check_confined(image, changed, regions, 'moves')
                    except ValueError:           # CompositionError included: a refusal with an explanation
                        pass
                    else:
                        self.fail('mutated FNT accepted')
        # the point of the guard: at least one mutation makes the raw reader raise something that is not a ValueError
        self.assertTrue(any(not issubclass(t, ValueError) for t in raw_types), raw_types)

    def test_ui_verifier_crashing_with_a_foreign_exception_type_is_a_refusal(self):
        base, image, _, _, _ = self.ui('EN')
        final, receipts = image, []
        for name in ('moves', 'ai'):
            final, receipt = ms.run_stage(name, final, 'EN',
                                          allocation=[self.fairy_row()])
            receipts.append(receipt)
        def crashing(candidate):
            import struct as _s
            raise _s.error('truncated FNT')
        with self.assertRaisesRegex(ms.CompositionError, 'fail-closed'):
            ms.verify_chain(base, final, ['moves', 'ai'], receipts, crashing,
                            allocation=[self.fairy_row()])


class AppendAfterUi(RealUiBase):
    """A stage that appends a file after the UI (sgp13.resources.append_file: the pattern the archive deltas replace)."""

    def test_self_consistent_append_is_refused_because_the_ui_seeds_pin_length_and_fat(self):
        from sgp13.resources import append_file
        from ndspy import fnt
        for language in LANGUAGES:
            image = self.ui(language)[1]
            view = self.layout_of(image)
            file_id = fnt.load(view.chunk(view.fnt, view.fnt_bytes)).idOf('a/0/1/2')   # the script archive of the gift fixes
            appended = append_file(image, file_id, bytes(range(256)) * 8)
            # the append helper keeps the cartridge self-consistent: header length and CRC are updated
            self.assertEqual(struct.unpack_from('<I', appended, 0x80)[0], len(appended))
            self.assertGreater(len(appended), len(image))
            with self.subTest(language=language, check='invariants'), \
                    self.assertRaisesRegex(ms.CompositionError, r'ROM length changed \('):
                ms.check_ui_invariants(image, appended, [])
            with self.subTest(language=language, check='seeds'), \
                    self.assertRaisesRegex(ms.CompositionError, 'ui.module.seed ROM length'):
                ms.check_ui_seeds(appended)
            fake = ms.MechanicalStage('appender', lambda data, lang: (append_file(data, file_id, bytes(range(256)) * 8),
                                                                    {'appended': True}),
                                      lambda before, after, receipt: {},
                                      lambda rom: [ms.Region(*self.layout_of(rom).files[file_id], 'a/0/1/2 slot')])
            with self.subTest(language=language, check='run_stage'), \
                    self.assertRaisesRegex(ms.CompositionError, r'ROM length changed \('):
                ms.run_stage('appender', image, language, registry={'appender': fake})

    def layout_of(self, rom):
        from . import ui_verify
        return ui_verify.Image(rom)


class ReserveGrants(RealUiBase):
    """Reserve bytes may change only inside a grant derived from an allocation row, for the stage that owns it.

    The Sguardofermo slot is read from the real reserve map (`reserve.MAP`, resident-6: parent `field-guide.code`), never
    hard-wired here. `reserve.allocate` refuses conditional parents, so the row is built from the map entry as a stand-in
    for the row Codex's final installer verifier will produce.
    """
    SLOT = 'modern-accuracy.code'

    def layout(self, rom):
        from . import ui_verify
        return ui_verify.Image(rom)

    def slot(self):
        from . import reserve
        policy = json.loads(reserve.MAP.read_text())
        parents = [(e['parent'], p) for e in policy['subdivisions'] for p in e['parts'] if p['name'] == self.SLOT]
        self.assertEqual(len(parents), 1, 'the real map must define the slot exactly once')
        parent, part = parents[0]
        self.assertEqual(part['kind'], 'payload')
        self.assertEqual(part['start'] % 4, 0)
        self.start, self.capacity, self.parent = part['start'], part['bytes'], parent
        self.assertGreaterEqual(self.capacity, 28)                       # the 28 B payload (MEMORY.md) must fit
        return part

    def row(self, nbytes=28, **changes):
        part = self.slot()
        row = {'name': self.SLOT, 'start': part['start'], 'bytes': nbytes, 'capacity': part['bytes']}
        row.update(changes)
        return row

    def stage(self, name='abilities-like', slot=SLOT, size=28, address=None, value=0xAA):
        self.slot()
        address = self.start if address is None else address

        def apply(data, language):
            out = bytearray(data)
            at = self.layout(data).offset(address, size)
            out[at:at + size] = bytes([value]) * size
            return bytes(out), {'size': size}

        def regions(rom):
            at = self.layout(rom).offset(address, size)
            return [ms.Region(at, at + size, 'reserve:' + (slot or 'none'))]
        return ms.MechanicalStage(name, apply, lambda before, after, receipt: {}, regions, slot=slot,
                                  cold_preimages=lambda before, final, declared: {
                                      (r.start, r.end): bytes(r.end-r.start) for r in declared})

    def test_the_real_map_defines_the_slot_outside_everything_the_ui_writes(self):
        self.slot()
        for label, address, length in ms.UI_RESERVE_SPANS:
            self.assertFalse(self.start < address + length and address < self.start + self.capacity, label)
        self.assertLessEqual(self.start + self.capacity, 0x023E0000)
        self.assertGreaterEqual(self.start, 0x023C8000)

    def test_grant_allows_exactly_the_slot_bytes_for_the_owning_stage(self):
        for language in LANGUAGES:
            image = self.ui(language)[1]
            stage = self.stage()
            out, receipt = ms.run_stage('abilities-like', image, language, registry={'abilities-like': stage},
                                        allocation=[self.row()])
            at = self.layout(out).offset(self.start, self.capacity)
            self.assertEqual(out[at:at + 28], bytes([0xAA]) * 28)
            self.assertEqual(ms.changed_ranges(image, out), [(at, at + 28)])
            self.assertEqual(receipt['changed_ranges'], [[at, at + 28]])

    def test_refusals_without_or_beyond_the_grant(self):
        image = self.ui('EN')[1]
        self.slot()
        def run(stage, allocation, stage_name='abilities-like'):
            return ms.run_stage(stage_name, image, 'EN', registry={stage_name: stage}, allocation=allocation)
        with self.assertRaisesRegex(ms.CompositionError, 'resident reserve'):       # no allocation at all
            run(self.stage(), None)
        with self.assertRaisesRegex(ms.CompositionError, 'resident reserve'):       # allocation row for another slot
            run(self.stage(), [self.row(name='training.ui')])
        with self.assertRaisesRegex(ms.CompositionError, 'resident reserve'):       # stage without a slot name
            run(self.stage(slot=None), [self.row()])
        with self.assertRaisesRegex(ms.CompositionError, 'outside|resident reserve'):   # one byte past the slot capacity
            run(self.stage(size=self.capacity + 1), [self.row()])
        with self.assertRaisesRegex(ms.CompositionError, 'outside|resident reserve'):   # the bytes right after the slot
            run(self.stage(address=self.start + self.capacity), [self.row()])
        with self.assertRaisesRegex(ms.CompositionError, 'outside|resident reserve'):   # the bytes right before the slot
            run(self.stage(address=self.start - 4, size=4), [self.row()])

    def test_invalid_or_hostile_grants_are_refused(self):
        image = self.ui('EN')[1]
        self.slot()
        for label, rows, reason in (
                ('over the UI seeds', [self.row(start=0x023D7B60, capacity=96)], 'overlaps UI-written'),
                ('over a UI payload', [self.row(start=0x023D6800, capacity=32)], 'overlaps UI-written'),
                ('over the Fieldbook code', [self.row(start=0x023D4000, capacity=32)], 'overlaps UI-written'),
                ('outside the reserve', [self.row(start=0x023E0000 - 16, nbytes=16, capacity=32)], 'outside the reserve'),
                ('below the reserve', [self.row(start=0x023C7FF0, nbytes=16, capacity=32)], 'outside the reserve'),
                ('bytes above capacity', [self.row(nbytes=self.capacity + 1)], 'invalid reserve grant'),
                ('zero capacity', [self.row(nbytes=0, capacity=0)], 'invalid reserve grant'),
                ('bool start', [self.row(start=True)], 'invalid reserve grant'),
                ('two rows for one slot', [self.row(), self.row(start=self.start + self.capacity)], 'invalid reserve grant')):
            with self.subTest(case=label), self.assertRaisesRegex(ms.CompositionError, reason):
                ms.run_stage('abilities-like', image, 'EN', registry={'abilities-like': self.stage()}, allocation=rows)

    def test_chain_replay_applies_the_same_grant(self):
        base, image, _, _, _ = self.ui('EN')
        stage = self.stage()
        registry = {'abilities-like': stage}
        out, receipt = ms.run_stage('abilities-like', image, 'EN', registry=registry, allocation=[self.row()])
        ok = lambda candidate: {}
        ms.verify_chain(base, out, ['abilities-like'], [receipt], ok, registry=registry, allocation=[self.row()])
        with self.assertRaisesRegex(ms.CompositionError, 'resident reserve'):
            ms.verify_chain(base, out, ['abilities-like'], [receipt], ok, registry=registry, allocation=None)
        wider = bytearray(out)
        wider[self.layout(out).offset(self.start + self.capacity, 1)] = 1      # one byte beyond the slot
        wider = bytes(wider)
        forged = copy.deepcopy(receipt)
        forged['output_sha256'] = hashlib.sha256(wider).hexdigest()
        with self.assertRaises(ValueError):
            ms.verify_chain(base, wider, ['abilities-like'], [forged], ok, registry=registry, allocation=[self.row()])


class PostUiMutations(RealUiBase):
    """Controlled in-memory mutations; each must be refused, with the named reason."""

    def mutated(self, rom, offset, delta=1):
        out = bytearray(rom)
        out[offset] ^= delta
        return bytes(out)

    def layout(self, rom):
        from . import ui_verify
        return ui_verify.Image(rom)

    def test_container_and_seed_mutations_are_refused_by_name(self):
        for language in LANGUAGES:
            image = self.ui(language)[1]
            view = self.layout(image)
            regions = ms.require_stage('moves').regions(image)
            cases = [
                ('y9 size word of overlay 12', view.y9 + 12 * 32 + 28, 'y9 table changed'),
                ('FAT 156 start', view.fat + 156 * 8, 'FAT entry 156'),
                ('FAT 54 end', view.fat + 54 * 8 + 4, 'FAT entry 54'),
                ('FAT 140', view.fat + 140 * 8, 'FAT table changed'),
                ('header ROM length', 0x80, 'ROM header changed'),
                ('header CRC16', 0x15E, 'ROM header changed'),
                ('module seed crc', view.offset(0x023D7B60 + 68, 4), 'ui.module.seed changed'),
                ('resource seed', view.offset(0x023D7BC0 + 8, 4), 'ui.resource.seed changed'),
                ('guide seed fat', view.offset(0x023D7C00 + 20, 4), 'ui.guide.seed changed'),
                ('Guide archive file 156', view.files[156][0] + 100, 'UI-owned file 156'),
                ('dynamic overlay 54 file', view.files[54][0] + 40, 'UI-owned file 54'),
                ('ungranted reserve slot (fairy-ai.code)', view.offset(0x023D746C, 4),
                 'resident reserve modified'),
            ]
            for label, offset, reason in cases:
                with self.subTest(language=language, case=label), self.assertRaisesRegex(ms.CompositionError, reason):
                    ms.check_ui_invariants(image, self.mutated(image, offset), regions)

    def test_length_change_and_foreign_arm9_and_foreign_file_are_refused(self):
        for language in LANGUAGES:
            image = self.ui(language)[1]
            view = self.layout(image)
            regions = ms.require_stage('moves').regions(image)
            with self.subTest(language=language, case='append'), self.assertRaisesRegex(ms.CompositionError, 'length'):
                ms.check_ui_invariants(image, image + b'\0', regions)
            # byte outside every declared region and outside the protected set: generic confinement
            arm9_byte = view.offset(0x02000000 + 0x2000, 1)
            foreign = self.mutated(image, arm9_byte)
            ms.check_ui_invariants(image, foreign, regions)  # named invariants alone do not see it ...
            with self.subTest(language=language, case='arm9'), self.assertRaisesRegex(ms.CompositionError, 'outside declared'):
                ms.check_confined(image, foreign, regions, 'moves')  # ... confinement does
            file12 = view.files[12][0] + 500
            with self.subTest(language=language, case='ai bytes under moves'), \
                    self.assertRaisesRegex(ms.CompositionError, 'outside declared'):
                ms.check_confined(image, self.mutated(image, file12), regions, 'moves')

    def test_declarations_reaching_protected_bytes_are_refused(self):
        image = self.ui('EN')[1]
        view = self.layout(image)
        for label, region in (('FAT', ms.Region(view.fat, view.fat + 8, 'x')),
                              ('y9', ms.Region(view.y9, view.y9 + 4, 'x')),
                              ('header', ms.Region(0x1F0, 0x200, 'x')),
                              ('guide', ms.Region(view.files[156][0], view.files[156][0] + 1, 'x')),
                              ('reserve', ms.Region(view.offset(0x023D746C, 4), view.offset(0x023D746C, 4) + 4, 'x'))):
            with self.subTest(case=label), self.assertRaisesRegex(ms.CompositionError, 'protected'):
                ms.check_ui_invariants(image, image, [region])

    def test_end_to_end_chain_rejects_foreign_changes_in_the_final_rom(self):
        language = 'EN'
        base, image, _, _, _ = self.ui(language)
        final = image
        receipts = []
        for name in ('moves', 'ai'):
            final, receipt = ms.run_stage(name, final, language,
                                          allocation=[self.fairy_row()])
            receipts.append(receipt)
        view = self.layout(final)
        verify_ui = self.verify_ui(language)
        for label, offset in (('y9', view.y9 + 3 * 32 + 4), ('FAT 156', view.fat + 156 * 8),
                              ('header', 0x80), ('reserve', view.offset(0x023D746C, 4)),
                              ('Guide file', view.files[156][0] + 77)):
            with self.subTest(case=label), self.assertRaises(ValueError):
                ms.verify_chain(base, self.mutated(final, offset), ['moves', 'ai'], receipts, verify_ui,
                                allocation=[self.fairy_row()])
        with self.assertRaises(ValueError):
            ms.verify_chain(base, final + b'\0' * 4, ['moves', 'ai'], receipts, verify_ui,
                            allocation=[self.fairy_row()])
        ms.verify_chain(base, final, ['moves', 'ai'], receipts, verify_ui,
                        allocation=[self.fairy_row()])  # control: untouched passes


class AbilitiesAfterUi(RealUiBase):
    """Why the description travels as an archive delta and never as an appended archive."""

    def test_measured_hazard_text_stage_after_ui_desynchronises_the_seeds(self):
        """Why the text is an archive delta: the 4a append-style stage accepts its own result but breaks the UI Guide.

        The slot is TEST-ONLY (0x023D746C/128, as in the 4a tests): not a reservation.
        """
        from . import modern_abilities
        for language in LANGUAGES:
            _, image, _, _, top = self.ui(language)
            _, charmap = self.inputs(language)
            at = modern_abilities._arm9_locate(modern_abilities._arm9_map(image), 0x023D746C, 128)
            slot = {'name': 'TEST-ONLY-not-a-reservation', 'start': 0x023D746C, 'bytes': 128,
                    'preimage_sha256': hashlib.sha256(image[at:at + 128]).hexdigest()}
            try:
                after, _ = modern_abilities.apply(image, language, top, slot=slot, charmap=charmap)
            except ValueError as error:
                if 'compiler' in str(error) or 'clang' in str(error):
                    self.skipTest('pinned compiler unavailable: %s' % error)
                raise
            with self.subTest(language=language):
                self.assertNotEqual(len(after), len(image))                       # the archive was re-appended
                self.assertNotEqual(fat_entry(after, 156), fat_entry(image, 156))  # FAT 156 relocated
                with self.assertRaisesRegex(ms.CompositionError, 'ROM length|FAT 156'):
                    ms.check_ui_seeds(after)
                with self.assertRaisesRegex(ms.CompositionError, 'length'):
                    ms.check_ui_invariants(image, after, [])


KEEN_EYE_PAYLOAD_SHA256 = '9370a52456cd303a935e69a033224d00f8a18d03c6d70a4032839efa2ef43cdd'   # restated, not imported
KEEN_EYE_MEMBER_SHA256 = {'EN': 'fa9a207b90c820fe8e3efbe968d50173ef2ac559985b4f7d10a5f374208bdb1e',
                          'IT': '6ad68cad754f4b7174cf6556d40330150c34ad5d18354c2e110c5d4b939ade1f'}


class AbilitiesBase(RealUiBase):
    """The Sguardofermo stage on the real UI image.

    The reserve row is a DECLARED SUBSTITUTE used by these lower-level confinement tests:
    it is built from the real map entry, exactly like the
    `ReserveGrants` stand-in. It is used only through explicit `allocation=`. Production grants
    and the full integrated chain are tested separately without a substituted policy or allocator.
    """
    ORDER = ('moves', 'ai', 'ai-immunities', 'abilities')

    def row(self):
        _, part = ms.reserve_slot('modern-accuracy.code')
        return {'name': part['name'], 'parent': 'field-guide.code', 'start': part['start'], 'bytes': 28,
                'capacity': part['bytes']}

    def allocation(self):
        return [self.fairy_row(), self.row()]

    def layout(self, rom):
        from . import ui_verify
        return ui_verify.Image(rom)

    def stage(self, name, data, language, directory=None, **kwargs):
        try:
            return ms.run_stage(name, data, language, allocation=self.allocation(),
                                work_dir=directory, **kwargs)
        except ValueError as error:
            if name == 'abilities' and ('compiler' in str(error) or 'clang' in str(error)):
                if os.environ.get('SGP_CI') == '1':
                    self.fail('pinned compiler unavailable: %s' % error)
                self.skipTest('pinned compiler unavailable: %s' % error)
            raise

    def chain(self, language, order=ORDER):
        _, image, _, _, top = self.ui(language)
        directory = top / ('abilities-work-' + language)
        directory.mkdir(exist_ok=True)
        data, receipts = image, []
        for name in order:
            data, receipt = self.stage(name, data, language, directory)
            receipts.append(receipt)
        return image, data, receipts


class AbilitiesChain(AbilitiesBase):
    def test_the_chain_with_abilities_reconciles_y9_and_changes_only_declared_bytes(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                image, final, receipts = self.chain(language)
                self.assertEqual([r['stage'] for r in receipts], ['moves', 'ai', 'ai-immunities', 'abilities'])
                self.assertEqual(len(final), len(image))
                self.assertNotEqual(y9_crc(final), y9_crc(image))
                self.assertEqual(final[:0x200], image[:0x200])
                for fid in (10, 27, 54, 140, 156, 167, 228):
                    self.assertEqual(fat_entry(final, fid), fat_entry(image, fid))
                self.assertEqual(fat_entry(final, 12)[0], fat_entry(image, 12)[0])
                self.assertEqual(fat_entry(final, 12)[1] - fat_entry(image, 12)[1], 28)
                self.assertEqual(struct.unpack_from('<I', final, 0x80)[0], len(final))
                # independent partition of the changed bytes: moves slot (file 140), overlay 12 slot, the 32 byte reserve slot
                view = self.layout(image)
                slot_at = view.offset(0x023D5AA0, 32)
                allowed = [(region['start'], region['end']) for receipt in receipts
                           for region in receipt['regions']]
                for start, end in ms.changed_ranges(image, final):
                    self.assertTrue(any(a <= start and end <= b for a, b in allowed), (hex(start), hex(end)))
                payload_ranges = [r for r in ms.changed_ranges(image, final) if slot_at <= r[0] < slot_at + 32]
                self.assertTrue(payload_ranges)
                self.assertEqual(hashlib.sha256(final[slot_at:slot_at + 28]).hexdigest(), KEEN_EYE_PAYLOAD_SHA256)
                self.assertEqual(final[slot_at + 28:slot_at + 32], bytes(4))       # the 4 byte tail stays what it was
                ms.check_ui_seeds(final)

    def test_the_abilities_receipt_names_the_exact_slot_and_the_independent_reader_accepts_it(self):
        language = LANGUAGES[0]
        image, final, receipts = self.chain(language)
        before_abilities = self.chain_prefix(language)
        raw = receipts[3]['stage_receipt']
        slot_at = self.layout(image).offset(0x023D5AA0, 32)
        self.assertEqual(raw['slot'], {'name': 'modern-accuracy.code', 'start': 0x023D5AA0, 'bytes': 32,
                                       'preimage_sha256': hashlib.sha256(image[slot_at:slot_at + 32]).hexdigest()})
        self.assertEqual((raw['schema'], raw['stage'], raw['language']), (1, 'keen-eye-code', language))
        self.assertEqual(raw['input_sha256'], hashlib.sha256(before_abilities).hexdigest())
        self.assertEqual(raw['output_sha256'], hashlib.sha256(final).hexdigest())
        self.assertEqual([r['label'] for r in receipts[3]['regions']], ['reserve:modern-accuracy.code', 'overlay 12 slot (file 12)'])
        self.assertEqual(receipts[3]['regions'][0]['end'] - receipts[3]['regions'][0]['start'], 32)

    def chain_prefix(self, language):
        _, image, _, _, top = self.ui(language)
        data = image
        for name in ('moves', 'ai', 'ai-immunities'):
            data, _ = self.stage(name, data, language)
        return data

    def test_replay_accepts_the_chain_and_the_grant_is_exactly_the_slot(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                base = self.ui(language)[0]
                image, final, receipts = self.chain(language)
                replay = json.loads(json.dumps(receipts))
                result = ms.verify_chain(base, final, list(self.ORDER), replay, self.verify_ui(language),
                                         allocation=self.allocation())
                self.assertEqual(result['stages'], list(self.ORDER))
                self.assertEqual(result['ui_image_sha256'], hashlib.sha256(image).hexdigest())
                with self.assertRaisesRegex(ms.CompositionError, 'reserve condition not proven'):
                    ms.verify_chain(base, final, list(self.ORDER), replay, self.verify_ui(language), allocation=None)

    def test_peeling_abilities_out_of_the_final_gives_the_exact_output_of_ai(self):
        from . import type_consumers
        for language in LANGUAGES:
            with self.subTest(language=language):
                base = self.ui(language)[0]
                _, final, _ = self.chain(language)
                after_ai = self.chain_prefix(language)
                stage = ms.require_stage('abilities')
                peeled = stage.peel(final, base, stage.regions(base))
                self.assertEqual(peeled, after_ai)
                at = type_consumers.FIRE_FANG_SITE - type_consumers.OVERLAY_BASE
                rage = type_consumers.RAGE_SITE - type_consumers.OVERLAY_BASE
                for label, image in (('ai', after_ai), ('abilities', final),
                                     ('abilities peeled', peeled)):
                    logical = Rom(image).immagine_overlay(12)[2]
                    self.assertEqual(
                        logical[at:at + len(type_consumers.FIRE_FANG_REPLACEMENT)],
                        type_consumers.FIRE_FANG_REPLACEMENT,
                        label + ' lost the HG-B01 effect correction')
                    self.assertEqual(
                        logical[rage:rage + len(type_consumers.RAGE_REPLACEMENT)],
                        type_consumers.RAGE_REPLACEMENT,
                        label + ' lost the HG-B02 Rage correction')

    def test_ai_and_abilities_share_overlay_12_and_either_order_gives_the_same_rom(self):
        for language in LANGUAGES:
            with self.subTest(language=language):
                _, image, _, _, top = self.ui(language)
                directory = top / ('order-' + language)
                directory.mkdir(exist_ok=True)
                data = image
                for name in ('ai', 'abilities'):
                    data, _ = self.stage(name, data, language, directory)
                reverse = image
                for name in ('abilities', 'ai'):
                    reverse, receipt = self.stage(name, reverse, language, directory)
                self.assertEqual(data, reverse)

    def test_the_reverse_order_is_refused_because_ai_peel_cannot_erase_an_earlier_shared_owner(self):
        language = LANGUAGES[0]
        base, image, _, _, top = self.ui(language)
        directory = top / 'reverse'
        directory.mkdir(exist_ok=True)
        data, receipts = image, []
        for name in ('abilities', 'ai'):
            data, receipt = self.stage(name, data, language, directory)
            receipts.append(receipt)
        with self.assertRaisesRegex(ms.CompositionError, 'peel|seam|chain'):
            ms.verify_chain(base, data, ['abilities', 'ai'], receipts, self.verify_ui(language),
                            allocation=self.allocation())


def forge_chain(base, mutated, names, honest, allocation):
    """Receipts an attacker could write for `mutated`: every step hash, range and receipt hash recomputed.

    The intermediates come from `ms.intermediate_images`, the same reconstruction the replay uses, so the only things
    left to refuse the mutation are the independent readers and the UI verifier.
    """
    stages = [ms.require_stage(n) for n in names]
    declared = [list(s.regions(base)) for s in stages]
    images = ms.intermediate_images(base, mutated, stages, declared)
    forged = []
    for index, (name, receipt) in enumerate(zip(names, honest)):
        previous, step = images[index], images[index + 1]
        new = copy.deepcopy(receipt)
        new['input_sha256'], new['output_sha256'] = hashlib.sha256(previous).hexdigest(), hashlib.sha256(step).hexdigest()
        new['changed_ranges'] = [list(pair) for pair in ms.changed_ranges(previous, step)]
        raw = new['stage_receipt']
        for key in ('input_sha256', 'output_sha256'):
            if key in raw:
                raw[key] = new[key]
        new['stage_receipt_sha256'] = hashlib.sha256(ms.canonical(raw)).hexdigest()
        forged.append(new)
    return forged


class AbilitiesForgeries(AbilitiesBase):
    """Mutations of the final ROM, with receipts forged to match, must still be refused by the independent readers."""

    def mutate(self, rom, offset):
        out = bytearray(rom)
        out[offset] ^= 0x5A
        return bytes(out)

    def test_control_the_forging_helper_reproduces_the_honest_receipts_exactly(self):
        language = LANGUAGES[0]
        base = self.ui(language)[0]
        _, final, honest = self.chain(language)
        again = forge_chain(base, final, list(AbilitiesBase.ORDER), honest, self.allocation())
        self.assertEqual(again, honest)
        ms.verify_chain(base, final, list(AbilitiesBase.ORDER), again, self.verify_ui(language),
                        allocation=self.allocation())

    def test_changes_in_or_around_the_slot_and_in_overlay_12_are_refused_even_with_forged_receipts(self):
        for language in LANGUAGES:
            base = self.ui(language)[0]
            _, final, honest = self.chain(language)
            view = self.layout(final)
            slot = view.offset(0x023D5AA0, 32)
            o_start, o_end = view.files[12]
            cases = [('payload byte', slot + 3, 'installed payload identity|payload'),
                     ('slot tail byte', slot + 30, 'ROM bytes differ outside the declared zones|tail|slot'),
                     ('first byte after the slot', slot + 32, 'resident reserve|protected cartridge bytes'),
                    ('last byte before the slot', slot - 1,
                     'resident reserve|protected|outside|differs|postimage|Guide suffix'),
                     ('overlay 12 stream middle', o_start + 5000, 'canonical|logical|decoder|differ|BLZ'),
                     ('overlay 12 stream tail', o_end - 20, 'canonical|logical|decoder|differ|BLZ|tail')]
            for label, offset, reason in cases:
                mutated = self.mutate(final, offset)
                try:
                    forged = forge_chain(base, mutated, list(AbilitiesBase.ORDER), honest, self.allocation())
                except ValueError:       # the reconstruction itself refuses: also a refusal, with a named reason
                    continue
                with self.subTest(language=language, case=label), self.assertRaisesRegex(ValueError, reason):
                    ms.verify_chain(base, mutated, list(AbilitiesBase.ORDER), forged, self.verify_ui(language),
                                    allocation=self.allocation())

    def test_a_receipt_slot_that_is_not_the_map_assignment_over_the_input_bytes_is_refused(self):
        language = LANGUAGES[0]
        base = self.ui(language)[0]
        _, final, honest = self.chain(language)
        for label, change in (('slot moved', dict(start=0x023D5AA4)), ('slot shortened', dict(bytes=28)),
                              ('wrong preimage', dict(preimage_sha256='0' * 64)), ('renamed', dict(name='training.ui'))):
            forged = copy.deepcopy(honest)
            raw = forged[3]['stage_receipt']
            raw['slot'] = dict(raw['slot'], **change)
            forged[3]['stage_receipt_sha256'] = hashlib.sha256(ms.canonical(raw)).hexdigest()
            with self.subTest(case=label), self.assertRaises(ValueError):
                ms.verify_chain(base, final, list(AbilitiesBase.ORDER), forged, self.verify_ui(language),
                                allocation=self.allocation())

    def test_a_widened_grant_or_a_foreign_row_is_refused(self):
        language = LANGUAGES[0]
        base = self.ui(language)[0]
        _, final, honest = self.chain(language)
        verify_ui = self.verify_ui(language)
        for label, change in (('start moved', dict(start=0x023D5AA4, capacity=28)), ('capacity widened', dict(capacity=64)),
                              ('other slot', dict(name='training.ui'))):
            row = dict(self.row(), **change)
            with self.subTest(case=label), self.assertRaises(ms.CompositionError):
                ms.verify_chain(base, final, list(AbilitiesBase.ORDER), honest, verify_ui,
                                allocation=[self.fairy_row(), row])


class AbilitiesBuilder(AbilitiesBase):
    """build.compose/verify_composition through='abilities': code in place, text as the keen-eye archive delta."""

    def compose(self, language, allocation=True):
        base, image, _, inputs, top = self.ui(language)
        _, charmap = self.inputs(language)
        config = top / 'ui-candidate.json'
        extra = {'allocation': self.allocation()} if allocation else {}
        try:
            return build.compose(base, 'abilities', charmap, top / ('scratch-abilities-' + language), ui_config=config, **extra)
        except ValueError as error:
            if 'compiler' in str(error) or 'clang' in str(error):
                if os.environ.get('SGP_CI') == '1':
                    self.fail('pinned compiler unavailable: %s' % error)
                self.skipTest('pinned compiler unavailable: %s' % error)
            raise

    def test_compose_through_abilities_ships_the_text_as_a_delta_with_no_appended_archive(self):
        from . import archives, evidence
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, image, _, inputs, top = self.ui(language)
                data, report = self.compose(language)
                self.assertEqual([r['stage'] for r in report['receipts']], ['ui', 'moves', 'ai', 'ai-immunities', 'abilities'])
                self.assertEqual(report['required_cases'], list(build.REQUIRED_CASES['abilities']))
                self.assertEqual(report['reserve_allocation'],
                                 {'source': 'caller-supplied', 'assignments': self.allocation()})
                delta = report['receipts'][0]['archive_deltas']
                self.assertEqual([(d['archive'], d['producers'], [m['index'] for m in d['members']]) for d in delta],
                                 [('a/0/2/7', ['keen-eye-text'], [722])])
                # growth over the plain UI image is the delta's few bytes, not a second 4.5 MB archive
                self.assertTrue(0 < len(data) - len(image) <= 64, len(data) - len(image))
                ms.check_ui_seeds(data)
                view = self.layout(data)
                guide = archives.members(data[view.files[156][0]:view.files[156][1]])
                self.assertEqual(hashlib.sha256(guide[722]).hexdigest(), KEEN_EYE_MEMBER_SHA256[language])
                json.loads(json.dumps(report))
                self.assertLessEqual(len(build.canonical(report)), build.RECEIPT_LIMIT)
                evidence.validate_provenance(report)
                replayed = build.verify_composition(base, data, report['receipts'], through='abilities', ui_inputs=inputs,
                                                    scratch=top / ('replay-abilities-' + language),
                                                    allocation=self.allocation())
                self.assertEqual(replayed, report['composition'])
                self.assertEqual([m['stage'] for m in replayed['mechanics']], ['moves', 'ai', 'ai-immunities', 'abilities'])

    def test_the_composed_rom_equals_ui_with_the_delta_then_the_three_stages_by_hand(self):
        from . import archives
        language = LANGUAGES[0]
        base, _, _, inputs, top = self.ui(language)
        _, charmap = self.inputs(language)
        data, report = self.compose(language)
        delta = archives.derive_keen_eye(base, language, charmap)
        image, _ = build.compose(base, 'ui', charmap, top / 'scratch-ui-delta', ui_config=top / 'ui-candidate.json',
                                 archive_deltas=(delta,))
        directory = top / 'by-hand'
        directory.mkdir(exist_ok=True)
        manual = image
        for name in ('moves', 'ai', 'ai-immunities', 'abilities'):
            manual, _ = self.stage(name, manual, language, directory)
        self.assertEqual(data, manual)

    def test_production_abilities_build_issues_a_bound_grant_after_ui_and_cleans_scratch(self):
        language = LANGUAGES[0]
        base, _, _, inputs, top = self.ui(language)
        data, report = self.compose(language, allocation=False)
        grant = report['reserve_allocation']['receipt']
        self.assertEqual(report['reserve_allocation']['source'], 'reserve.allocate')
        self.assertEqual(grant['schema'], 2)
        self.assertEqual(grant['input_sha256'], hashlib.sha256(base).hexdigest())
        self.assertEqual(grant['requested'], {'fairy-ai.code': 148,
                                              'modern-accuracy.code': 28})
        self.assertEqual(grant['installer_verification']['ui_sha256'], report['receipts'][0]['output_sha256'])
        self.assertFalse((top / ('scratch-abilities-' + language)).exists())
        replayed = build.verify_composition(base, data, report['receipts'], through='abilities', ui_inputs=inputs,
                                            scratch=top / 'replay-production-abilities', allocation=grant)
        self.assertEqual(replayed, report['composition'])
        self.assertFalse((top / 'replay-production-abilities').exists())

    def test_replay_can_reissue_a_real_grant_for_the_legacy_explicit_row_build(self):
        language = LANGUAGES[0]
        base, _, _, inputs, top = self.ui(language)
        data, report = self.compose(language)
        replayed = build.verify_composition(base, data, report['receipts'], through='abilities', ui_inputs=inputs,
                                            scratch=top / 'replay-production')
        self.assertEqual(replayed, report['composition'])
        self.assertFalse((top / 'replay-production').exists())

    def test_a_final_that_has_the_code_but_no_text_delta_is_refused(self):
        """Code stages applied to a UI image built without the keen-eye-text delta: provenance says the text is missing."""
        language = LANGUAGES[0]
        base, image, report, inputs, top = self.ui(language)
        directory = top / 'no-text'
        directory.mkdir(exist_ok=True)
        data, receipts = image, [report['receipts'][0]]
        for name in self.ORDER:
            data, receipt = self.stage(name, data, language, directory)
            receipts.append(receipt)
        with self.assertRaisesRegex(ValueError, 'keen-eye-text'):
            build.verify_composition(base, data, receipts, through='abilities', ui_inputs=inputs,
                                     scratch=top / 'replay-no-text', allocation=self.allocation())

    def test_a_caller_delta_for_the_same_producer_is_a_duplicate_not_a_second_text(self):
        from . import archives
        language = LANGUAGES[0]
        base, _, _, inputs, top = self.ui(language)
        _, charmap = self.inputs(language)
        delta = archives.derive_keen_eye(base, language, charmap)
        data, report = build.compose(base, 'abilities', charmap, top / 'scratch-dup', ui_config=top / 'ui-candidate.json',
                                     archive_deltas=(delta,), allocation=self.allocation())
        self.assertEqual([d['producers'] for d in report['receipts'][0]['archive_deltas']], [['keen-eye-text']])


_GIFTS = {}
GIFT_MEMBERS = [225, 227, 232, 243, 246, 938, 962]      # a/0/1/2: six ribbon tails + the Eevee gift (the declared delta)


class GiftsBuilder(AbilitiesBase):
    """build.compose/verify_composition through='gifts': the script fixes are the `gifts-scripts` archive delta, nothing else.

    `gifts` is the archive-only stage: it has no post-UI writer and no receipt of its own. The UI stage applies the delta in its
    single append (as for the keen-eye text); the chain is ui -> moves -> ai -> abilities, and the independent admission is the
    producer re-run on the V4 (`archives.rederive`) plus the member checkers of gifts_archives. `abilities` precedes it in the
    order, so the reserve row is the same declared substitute and the keen-eye text travels in the same append.
    """

    def compose(self, language):
        if language in _GIFTS:
            return _GIFTS[language]
        base, image, _, inputs, top = self.ui(language)
        _, charmap = self.inputs(language)
        try:
            result = build.compose(base, 'gifts', charmap, top / ('scratch-gifts-' + language),
                                   ui_config=top / 'ui-candidate.json', allocation=self.allocation())
        except ValueError as error:
            if 'compiler' in str(error) or 'clang' in str(error) or 'pret script command table' in str(error):
                if os.environ.get('SGP_CI') == '1' or os.environ.get('SGP131_MECHANICS_REQUIRE_INPUTS') == '1':
                    self.fail('input unavailable: %s' % error)
                self.skipTest('input unavailable: %s' % error)
            raise
        _GIFTS[language] = result
        return result

    def members_of(self, rom, archive='a/0/1/2'):
        from . import archives
        resolve, file = archives.from_cartridge(rom)
        return archives.members(file(resolve(archive)))

    def test_compose_through_gifts_ships_the_script_fixes_as_a_delta_with_no_extra_receipt(self):
        from . import archives, evidence, gifts_archives
        for language in LANGUAGES:
            with self.subTest(language=language):
                base, image, _, inputs, top = self.ui(language)
                data, report = self.compose(language)
                self.assertEqual([r['stage'] for r in report['receipts']], ['ui', 'moves', 'ai', 'ai-immunities', 'abilities'])
                self.assertEqual(report['through'], 'gifts')
                self.assertEqual(report['required_cases'], list(build.REQUIRED_CASES['gifts']))
                deltas = report['receipts'][0]['archive_deltas']
                self.assertEqual([(d['archive'], d['producers'], [m['index'] for m in d['members']]) for d in deltas],
                                 [('a/0/1/2', ['gifts-scripts'], GIFT_MEMBERS), ('a/0/2/7', ['keen-eye-text'], [722])])
                # growth over the plain UI image: one appended a/0/1/2 body (not a second 4.5 MB Guide) and a few bytes of text
                self.assertGreater(len(data), len(image))
                ms.check_ui_seeds(data)                                  # the seeds describe the FINAL image
                self.assertEqual(struct.unpack_from('<I', data, 0x80)[0], len(data))
                # independent partition: exactly the declared members of a/0/1/2 differ from the V4, the rest is byte-equal
                old, new = self.members_of(base), self.members_of(data)
                self.assertEqual(len(old), len(new))
                self.assertEqual([i for i, (a, b) in enumerate(zip(old, new)) if a != b], GIFT_MEMBERS)
                record = next(d for d in deltas if d['archive'] == 'a/0/1/2')
                for row in record['members']:
                    self.assertEqual(hashlib.sha256(old[row['index']]).hexdigest(), row['before_sha256'])
                    self.assertEqual(hashlib.sha256(new[row['index']]).hexdigest(), row['after_sha256'])
                    gifts_archives.check_scripts(row['index'], old[row['index']], new[row['index']], language)
                self.assertTrue(set(GIFT_MEMBERS).isdisjoint(archives.GUIDE_SCRIPT_MEMBERS))
                json.loads(json.dumps(report))
                self.assertLessEqual(len(build.canonical(report)), build.RECEIPT_LIMIT)
                evidence.validate_provenance(report)
                replayed = build.verify_composition(base, data, report['receipts'], through='gifts', ui_inputs=inputs,
                                                    scratch=top / ('replay-gifts-' + language),
                                                    allocation=self.allocation())
                self.assertEqual(replayed, report['composition'])
                self.assertEqual([m['stage'] for m in replayed['mechanics']], ['moves', 'ai', 'ai-immunities', 'abilities'])

    def test_the_composed_rom_equals_ui_with_both_deltas_then_the_writers_by_hand(self):
        from . import archives
        language = LANGUAGES[0]
        base, _, _, inputs, top = self.ui(language)
        _, charmap = self.inputs(language)
        data, _ = self.compose(language)
        archives.register_owner_producers()
        deltas = (archives.derive_keen_eye(base, language, charmap),
                  archives.PRODUCERS['gifts-scripts'](base, language, charmap))
        image, _ = build.compose(base, 'ui', charmap, top / 'scratch-ui-gifts-deltas', ui_config=top / 'ui-candidate.json',
                                 archive_deltas=deltas)
        directory = top / 'by-hand-gifts'
        directory.mkdir(exist_ok=True)
        manual = image
        for name in ('moves', 'ai', 'ai-immunities', 'abilities'):
            manual, _ = self.stage(name, manual, language, directory)
        self.assertEqual(data, manual)

    def test_a_receipt_that_drops_the_gifts_delta_is_refused(self):
        language = LANGUAGES[0]
        base, _, _, inputs, top = self.ui(language)
        data, report = self.compose(language)
        receipts = copy.deepcopy(report['receipts'])
        receipts[0]['archive_deltas'] = [d for d in receipts[0]['archive_deltas'] if d['producers'] != ['gifts-scripts']]
        with self.assertRaisesRegex(ValueError, 'gifts-scripts'):
            build.verify_composition(base, data, receipts, through='gifts', ui_inputs=inputs,
                                     scratch=top / 'replay-gifts-dropped', allocation=self.allocation())

    def test_a_script_member_changed_in_the_final_rom_is_refused(self):
        language = LANGUAGES[0]
        base, _, _, inputs, top = self.ui(language)
        data, report = self.compose(language)
        from . import archives
        resolve, _ = archives.from_cartridge(data)
        fid = resolve('a/0/1/2')
        start = struct.unpack_from('<II', data, tables(data)[0] + 8 * fid)[0]
        at = data.index(self.members_of(data)[227], start)           # inside the appended a/0/1/2 body
        forged = bytearray(data)
        forged[at + 40] ^= 0x01
        with self.assertRaisesRegex(ValueError, 'archive member 227 differs from its declaration'):
            build.verify_composition(base, bytes(forged), report['receipts'], through='gifts', ui_inputs=inputs,
                                     scratch=top / 'replay-gifts-forged', allocation=self.allocation())

    def test_production_gifts_build_issues_a_real_bound_grant_and_cleans_scratch(self):
        language = LANGUAGES[0]
        base, _, _, inputs, top = self.ui(language)
        _, charmap = self.inputs(language)
        scratch = top / 'scratch-gifts-production'
        data, report = build.compose(base, 'gifts', charmap, scratch, ui_config=top / 'ui-candidate.json')
        grant = report['reserve_allocation']['receipt']
        self.assertEqual(grant['schema'], 2)
        self.assertEqual(grant['requested'], {'fairy-ai.code': 148,
                                              'modern-accuracy.code': 28})
        self.assertEqual(grant['installer_verification']['ui_sha256'], report['receipts'][0]['output_sha256'])
        self.assertEqual([p for d in report['receipts'][0]['archive_deltas'] for p in d['producers']],
                         ['gifts-scripts', 'keen-eye-text'])
        self.assertFalse(scratch.exists())


class LegacyEventsBuilder(AbilitiesBase):
    """The real legacy composition carries H1 event repairs in the one UI archive pass."""

    def test_en_it_composition_replays_two_event_halfwords_without_touching_hidden_items(self):
        from . import (archives, evolution_fixes, gs_cup_guard, legacy_archives,
                       pressure_switch_scripts, pursuit_script,
                       safari_archives, status_icon_script, ui_compile)
        for language in ('EN', 'IT'):
            with self.subTest(language=language):
                base, _, _, inputs, top = self.ui(language)
                _, charmap = self.inputs(language)
                try:
                    data, report = build.compose(
                        base, 'legacy', charmap, top / 'scratch-legacy-events',
                        ui_config=top / 'ui-candidate.json', allocation=self.allocation())
                except ValueError as error:
                    if ('compiler' in str(error) or 'clang' in str(error)
                            or 'pret script command table' in str(error)):
                        if (os.environ.get('SGP_CI') == '1'
                                or os.environ.get('SGP131_MECHANICS_REQUIRE_INPUTS') == '1'):
                            self.fail('input unavailable: %s' % error)
                        self.skipTest('input unavailable: %s' % error)
                    raise
                self.assertEqual([r['stage'] for r in report['receipts']],
                                 ['ui', 'moves', 'ai', 'ai-immunities', 'abilities', 'legacy'])
                records = report['receipts'][0]['archive_deltas']
                battle_subscripts = next(record for record in records
                                         if record['archive'] == 'a/0/0/1')
                self.assertEqual(
                    (battle_subscripts['producers'],
                     [row['index'] for row in battle_subscripts['members']]),
                    (['pressure-switch-subscripts', 'pursuit-script',
                      'status-icon-script'], [139, 146, 153, 221]))
                pressure_effects = next(record for record in records
                                        if record['archive'] == 'a/0/3/0')
                self.assertEqual(
                    (pressure_effects['producers'],
                     [row['index'] for row in pressure_effects['members']]),
                    (['pressure-switch-effects'], [89, 144, 227]))
                scripts = next(record for record in records
                               if record['archive'] == 'a/0/1/2')
                self.assertEqual(scripts['producers'],
                                 ['gifts-scripts', 'gs-cup-guard', 'legacy-scripts',
                                  'poison-follower-script', 'safari-scripts'])
                self.assertEqual([row['index'] for row in scripts['members']],
                                 [3, 4, 93, 141, 225, 227, 232, 237, 243, 246, 260,
                                  757, 874, 932, 938, 962])
                event = next(record for record in records if record['archive'] == 'a/0/3/2')
                self.assertEqual((event['producers'], [row['index'] for row in event['members']]),
                                 (['legacy-events'], [71, 440]))
                evolution = next(record for record in records if record['archive'] == 'a/0/3/4')
                self.assertEqual((evolution['producers'], [row['index'] for row in evolution['members']]),
                                 (['evolution-fixes'], [349, 412, 415, 458]))
                resolve_base, file_base = archives.from_cartridge(base)
                resolve_new, file_new = archives.from_cartridge(data)
                battle_old = archives.members(file_base(resolve_base('a/0/0/1')))
                battle_new = archives.members(file_new(resolve_new('a/0/0/1')))
                self.assertEqual([i for i, pair in enumerate(zip(battle_old, battle_new))
                                  if pair[0] != pair[1]], [139, 146, 153, 221])
                pursuit_script.check(153, battle_old[153], battle_new[153], language)
                status_icon_script.check(221, battle_old[221], battle_new[221], language)
                for member in (139, 146):
                    pressure_switch_scripts.check(
                        member, battle_old[member], battle_new[member], language)
                effect_old = archives.members(file_base(resolve_base('a/0/3/0')))
                effect_new = archives.members(file_new(resolve_new('a/0/3/0')))
                self.assertEqual([i for i, pair in enumerate(zip(effect_old, effect_new))
                                  if pair[0] != pair[1]], [89, 144, 227])
                for member in (89, 144, 227):
                    pressure_switch_scripts.check(
                        member, effect_old[member], effect_new[member], language)
                self.assertEqual(resolve_base('a/0/3/2'), resolve_new('a/0/3/2'))
                old = archives.members(file_base(resolve_base('a/0/3/2')))
                new = archives.members(file_new(resolve_new('a/0/3/2')))
                self.assertEqual([i for i, pair in enumerate(zip(old, new)) if pair[0] != pair[1]],
                                 [71, 440])
                for member, (row, script, x, z, _, _) in legacy_archives.EVENT_CASES.items():
                    self.assertEqual(legacy_archives._background(old[member], row),
                                     (script, 2, x, z, 0, 0))
                    self.assertEqual(legacy_archives._background(new[member], row),
                                     (script, 1, x, z, 0, 0))
                # Independent negative control: the neighbouring retail hidden
                # item remains script 8006/type 2 in both languages.
                self.assertEqual(legacy_archives._background(old[71], 6),
                                 (8006, 2, 421, 469, 0, 4))
                self.assertEqual(legacy_archives._background(new[71], 6),
                                 (8006, 2, 421, 469, 0, 4))
                evo_old = archives.members(file_base(resolve_base('a/0/3/4')))
                evo_new = archives.members(file_new(resolve_new('a/0/3/4')))
                self.assertEqual([i for i, pair in enumerate(zip(evo_old, evo_new))
                                  if pair[0] != pair[1]], [349, 412, 415, 458])
                self.assertEqual({i: struct.unpack_from('<3H', evo_new[i])
                                  for i in evolution_fixes.CASES},
                                 {349: (15, 170, 350), 412: (23, 20, 413),
                                  415: (23, 21, 416), 458: (21, 223, 226)})
                # The Guide member must be built from the same repaired evolution delta.
                delta = evolution_fixes.derive(base, language)
                expected_guide = ui_compile.resources(base, language, charmap, (delta,))['guide']
                self.assertEqual(archives.members(file_new(resolve_new('a/0/2/7')))[829],
                                 expected_guide)
                old_scripts = archives.members(file_base(resolve_base('a/0/1/2')))
                new_scripts = archives.members(file_new(resolve_new('a/0/1/2')))
                gs_cup_guard.check(4, old_scripts[4], new_scripts[4], language)
                safari_archives.check_scripts(260, old_scripts[260],
                                              new_scripts[260], language)
                replayed = build.verify_composition(
                    base, data, report['receipts'], through='legacy', ui_inputs=inputs,
                    scratch=top / 'replay-legacy-events', allocation=self.allocation())
                self.assertEqual(replayed, report['composition'])


if __name__ == '__main__':
    unittest.main()
