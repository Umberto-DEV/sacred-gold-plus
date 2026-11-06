"""Class B: the UI stage appends every changed archive exactly once, on the real V4 EN and IT.

Inputs: SGP131_BASE_EN / SGP131_BASE_IT (immutable V4) and SGP131_UI_CHARMAP. Set
SGP131_ARCHIVES_REQUIRE_INPUTS=1 to make missing inputs failures. Everything stays in memory;
only a temporary UI scratch directory is written (removed by the builder and by the tests).
SGP131_ARCHIVES_REFERENCE names a JSON {lang: sha256} produced by the frozen e14d77d writer/reader plus an independently applied
3776-byte Guide suffix retirement transformation; with REQUIRE_INPUTS it is mandatory and replaces self-comparison as the delta-free oracle.

Seeds are re-read here with plain struct reads, not with archives.py or the UI writer.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

from . import archives, build, ui_verify
from .test_ui import CONFIG

# Independent frozen e14d77d UI output, then the reviewed cold retirement transformation.
# The external reference remains required; these explicit hashes supplement that independent oracle.
PRISTINE_UI_SHA256 = {'EN': '682a1ab06d5940950334d01ad2adea8ff93968aae622402e1bb7a95058d1d8d3',
                      'IT': '3aac2971de18a3af59f2391bf075a126726432d5ffaf7264d4c4f05d3b93aabf'}
RIBBON = (225, 232, 243, 246, 938, 962)
SITES = (300, 301)                 # a/0/1/2: single-site members of the synthetic second producer (not Guide-pinned)
MESSAGES = (100, 101)              # a/0/2/7: message banks of the synthetic gift-messages producer (not Guide sources)
LANGUAGES = ('EN', 'IT')
_CACHE = {}


def words(rom, offset, n):
    return struct.unpack_from('<%dI' % n, rom, offset)


def fat_entry(rom, fid):
    return struct.unpack_from('<II', rom, words(rom, 0x48, 1)[0] + 8 * fid)


def seed_state(rom):
    image = ui_verify.Image(rom)
    return image, words(image.arm(0x023D7B60, 96), 0, 24), words(image.arm(0x023D7C00, 64), 0, 16)


def synthetic(name, archive, indices, suffix=b'\x01\x02\x03'):
    """A synthetic producer + checker pair with the shape of a gift stage: longer members, new bytes."""
    def derive(base, language, charmap):
        resolve, file = archives.from_cartridge(base)
        fid = resolve(archive)
        old = archives.members(file(fid))
        return archives.ArchiveDelta.make(archive, fid, name, file(fid),
                                          {i: old[i] + suffix + bytes([i % 251]) for i in indices},
                                          evidence={'synthetic': name})

    def check(index, before, after, language):
        if index not in indices or after != before + suffix + bytes([index % 251]):
            raise ValueError('synthetic checker ' + name)
    return derive, check


@contextmanager
def registered(*specs):
    producers, checkers = {}, {}
    for spec in specs:
        derive, check = synthetic(*spec)
        producers[spec[0]], checkers[spec[0]] = derive, check
    with patch.dict(archives.PRODUCERS, producers), patch.dict(archives.CHECKERS, checkers):
        yield


GIFTS = (('gifts-ribbons-test', 'a/0/1/2', RIBBON), ('gifts-sites-test', 'a/0/1/2', SITES),
         ('gifts-messages-test', 'a/0/2/7', MESSAGES))


def derive_all(base, names):
    return tuple(archives.PRODUCERS[n](base, None, None) for n in names)


class Real(unittest.TestCase):
    def inputs(self, language):
        path, charmap = os.environ.get('SGP131_BASE_' + language), os.environ.get('SGP131_UI_CHARMAP')
        if not path or not charmap:
            message = 'missing V4 %s input or UI charmap' % language
            if os.environ.get('SGP131_ARCHIVES_REQUIRE_INPUTS') == '1':
                self.fail(message)
            self.skipTest(message)
        return Path(path), Path(charmap)

    def base(self, language):
        key = ('base', language)
        if key not in _CACHE:
            path, _ = self.inputs(language)
            data = path.read_bytes()
            expected = next(h for h, l in build.baseline.INPUT_HASHES.items() if l == language)
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
            _CACHE[key] = data
        return _CACHE[key]

    def workspace(self):
        directory = tempfile.TemporaryDirectory(prefix='archives-ui-')
        self.addCleanup(directory.cleanup)
        top = Path(directory.name).resolve()
        (top / 'ui-candidate.json').write_text(json.dumps(CONFIG))
        return top

    def keen_eye(self, language):
        key = ('keen', language)
        if key not in _CACHE:
            _, charmap = self.inputs(language)
            _CACHE[key] = archives.derive_keen_eye(self.base(language), language, charmap)
        return _CACHE[key]

    def compose(self, language, name, deltas=(), through='ui'):
        """V4 -> real UI stage with declared deltas (cached): image, report, consumed inputs, top."""
        key = (name, language, through)
        if key not in _CACHE:
            base = self.base(language)
            _, charmap = self.inputs(language)
            directory = tempfile.TemporaryDirectory(prefix='archives-compose-')
            unittest.addModuleCleanup(directory.cleanup)
            top = Path(directory.name).resolve()
            config = top / 'ui-candidate.json'
            config.write_text(json.dumps(CONFIG))
            image, report = build.compose(base, through, charmap, top / 'scratch', ui_config=config,
                                          archive_deltas=tuple(deltas))
            _CACHE[key] = (image, report, build.snapshot_ui_inputs(charmap, config), top)
        return _CACHE[key]

    def gifts(self, language):
        """Keen Eye + three synthetic producers: two on a/0/1/2 (disjoint members), one more on a/0/2/7."""
        names = ('gifts-ribbons-test', 'gifts-sites-test', 'gifts-messages-test')
        with registered(*GIFTS):
            deltas = (self.keen_eye(language),) + derive_all(self.base(language), names)
            return self.compose(language, 'all', deltas), deltas

    def verify(self, language, image, deltas=()):
        _, charmap = self.inputs(language)
        top = self.workspace()
        return ui_verify.verify(self.base(language), image, language, charmap, top, archive_deltas=tuple(deltas))


class Producer(Real):
    def test_keen_eye_delta_is_derived_from_the_owner_stage_on_the_v4(self):
        for language in LANGUAGES:
            with self.subTest(language):
                delta = self.keen_eye(language)
                record = delta.record()
                self.assertEqual((delta.archive, delta.file_id, record['producers']), ('a/0/2/7', 156, ['keen-eye-text']))
                self.assertEqual([m['index'] for m in record['members']], [722])
                self.assertEqual(sorted(record['evidence']['keen-eye-text']),
                                 ['owner_input_sha256', 'owner_output_sha256', 'owner_receipt_sha256'])
                self.assertEqual(record['evidence']['keen-eye-text']['owner_input_sha256'],
                                 hashlib.sha256(self.base(language)).hexdigest())
                text = archives._text_module()
                member = delta.replacements()[722]
                self.assertEqual(text.row_sha256(text.decode_row(member, text.ROW)), text.NEW_SHA256[language])
                self.assertEqual(hashlib.sha256(member).hexdigest(), archives.KEEN_EYE_MEMBER_SHA256[language])

    def test_the_text_stage_run_after_the_ui_is_the_measured_hazard(self):
        """Control: what the delta avoids. text.apply on the UI image appends a second copy of 156."""
        image, _, _, _ = self.compose('EN', 'none')
        text = archives._text_module()
        _, charmap = self.inputs('EN')
        late, _ = text.apply(image, 'EN', charmap)
        self.assertGreater(len(late) - len(image), 4_000_000)
        self.assertNotEqual(fat_entry(late, 156), fat_entry(image, 156))
        _, module, guide = seed_state(late)
        self.assertNotEqual(module[20], len(late))
        self.assertNotEqual(tuple(guide[5:7]), tuple(fat_entry(late, 156)))


class SingleAppend(Real):
    def reference(self, language):
        path = os.environ.get('SGP131_ARCHIVES_REFERENCE')
        if not path:
            if os.environ.get('SGP131_ARCHIVES_REQUIRE_INPUTS') == '1':
                self.fail('SGP131_ARCHIVES_REFERENCE (independently retired frozen builder output) is required')
            self.skipTest('no independent reference')
        return json.loads(Path(path).read_text())[language]

    def test_without_deltas_matches_the_independently_retired_frozen_builder(self):
        from . import ui
        for language in LANGUAGES:
            with self.subTest(language):
                image, report, _, _ = self.compose(language, 'none')
                base = self.base(language)
                self.assertEqual(hashlib.sha256(image).hexdigest(), self.reference(language))
                self.assertNotIn('archive_deltas', report['receipts'][0])      # archive declarations remain absent for delta-free images
                guide = archives.members(image[slice(*fat_entry(image, 156))])[829]
                rebuilt, _ = ui._replace_guide(base[slice(*fat_entry(base, 156))], guide)
                self.assertEqual(image[slice(*fat_entry(image, 156))], rebuilt)
                if os.environ.get('SGP131_ARCHIVES_HEAD_PINS') == '1':        # independently measured retired frozen UI hashes
                    self.assertEqual(hashlib.sha256(image).hexdigest(), PRISTINE_UI_SHA256[language])

    def test_seeds_describe_the_final_image_when_text_is_declared(self):
        for language in LANGUAGES:
            with self.subTest(language):
                image, report, _, _ = self.compose(language, 'text', (self.keen_eye(language),))
                plain, _, _, _ = self.compose(language, 'none')
                view, module, guide = seed_state(image)
                self.assertEqual(module[20], len(image))
                self.assertEqual(struct.unpack_from('<I', image, 0x80)[0], len(image))
                self.assertEqual(module[17], zlib.crc32(image[view.y9:view.y9 + view.y9_bytes]))
                self.assertEqual(tuple(module[21:23]), fat_entry(image, 54))
                self.assertEqual((guide[4], tuple(guide[5:7]), guide[7]), (156, fat_entry(image, 156), len(image)))
                start, end = fat_entry(image, 156)
                self.assertEqual(guide[8], end - start)
                spans, _, member_image, base = archives._geometry(image[start:end])
                a, b = spans[829]
                self.assertEqual((guide[9], guide[10]), (base + a, b - a))
                self.assertEqual(guide[11], zlib.crc32(member_image[a:b]))
                self.assertLess(len(image) - len(plain), 64)
                self.assertEqual(report['receipts'][0]['archive_deltas'][0]['members'][0]['index'], 722)

    def test_row_51_is_the_text_stage_row_and_every_other_member_is_untouched(self):
        for language in LANGUAGES:
            with self.subTest(language):
                image, _, _, _ = self.compose(language, 'text', (self.keen_eye(language),))
                plain, _, _, _ = self.compose(language, 'none')
                base = self.base(language)
                final = archives.members(image[slice(*fat_entry(image, 156))])
                original = archives.members(base[slice(*fat_entry(base, 156))])
                plain_members = archives.members(plain[slice(*fat_entry(plain, 156))])
                self.assertEqual(len(final), 830)
                text = archives._text_module()
                self.assertEqual(text.row_sha256(text.decode_row(final[722], text.ROW)), text.NEW_SHA256[language])
                for index in range(829):
                    if index != 722:
                        self.assertEqual(final[index], original[index], index)
                self.assertEqual(final[829], plain_members[829])
                for fid in range(513):
                    if fid not in (27, 54, 156, 167):
                        self.assertEqual(fat_entry(image, fid), fat_entry(base, fid), fid)

    def test_verify_composition_always_re_derives_the_recorded_deltas(self):
        for language in LANGUAGES:
            with self.subTest(language):
                base = self.base(language)
                image, report, inputs, top = self.compose(language, 'text', (self.keen_eye(language),))
                genuine = build.verify_composition(base, image, report['receipts'], through='ui', ui_inputs=inputs,
                                                   scratch=top / 'replay')
                self.assertTrue(genuine['static_verified'])
                same = build.verify_composition(base, image, report['receipts'], through='ui', ui_inputs=inputs,
                                                scratch=top / 'replay-same', archive_deltas=(self.keen_eye(language),))
                self.assertEqual(same, genuine)
                forged = json.loads(json.dumps(report['receipts']))
                forged[0]['archive_deltas'][0]['members'][0]['after_sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    build.verify_composition(base, image, forged, through='ui', ui_inputs=inputs, scratch=top / 'replay-forged')
                real = self.keen_eye(language)
                stripped = json.loads(json.dumps(report['receipts']))
                del stripped[0]['archive_deltas']
                with self.assertRaises(ValueError):
                    build.verify_composition(base, image, stripped, through='ui', ui_inputs=inputs,
                                             scratch=top / 'replay-stripped', archive_deltas=(real,))


class ReplayIsNotOptional(Real):
    def test_a_consistent_but_non_reproducible_declaration_is_refused_even_when_passed_explicitly(self):
        """I2: image, receipt and passed deltas agree with each other and satisfy the checker, but the registered producer
        does not produce them (it would change all six ribbon members, not one)."""
        base = self.base('EN')
        resolve, file = archives.from_cartridge(base)
        old = archives.members(file(141))
        index = RIBBON[0]
        partial = archives.ArchiveDelta.make('a/0/1/2', 141, 'gifts-ribbons-test', file(141),
                                             {index: old[index] + b'\x01\x02\x03' + bytes([index % 251])})
        with registered(*GIFTS):
            image, report, inputs, top = self.compose('EN', 'partial-ribbon', (partial,))
            self.verify('EN', image, (partial,))                       # the member-level checks alone accept it
            with self.assertRaises(ValueError):
                build.verify_composition(base, image, report['receipts'], through='ui', ui_inputs=inputs,
                                         scratch=top / 'replay-partial', archive_deltas=(partial,))
            with self.assertRaises(ValueError):
                build.verify_composition(base, image, report['receipts'], through='ui', ui_inputs=inputs,
                                         scratch=top / 'replay-partial-default')


class Negative(Real):
    def test_undeclared_text_in_the_image_is_rejected(self):
        image, _, _, _ = self.compose('EN', 'text', (self.keen_eye('EN'),))
        with self.assertRaises(ValueError):
            self.verify('EN', image)

    def test_declared_delta_that_was_not_applied_is_rejected(self):
        plain, _, _, _ = self.compose('EN', 'none')
        with self.assertRaises(ValueError):
            self.verify('EN', plain, (self.keen_eye('EN'),))

    def test_declaration_with_other_bytes_than_the_image_is_rejected(self):
        image, _, _, _ = self.compose('EN', 'text', (self.keen_eye('EN'),))
        real = self.keen_eye('EN')
        member = bytearray(real.replacements()[722])
        member[-1] ^= 1
        resolve, file = archives.from_cartridge(self.base('EN'))
        other = archives.ArchiveDelta.make('a/0/2/7', 156, 'keen-eye-text', file(156), {722: bytes(member)})
        with self.assertRaises(ValueError):
            self.verify('EN', image, (other,))

    def test_a_forged_member_722_that_keeps_every_row_is_refused_by_compose_and_by_the_verifier(self):
        """I1: the whole member is pinned, not only the rows: trailing bytes after the last row are rejected."""
        for language in LANGUAGES:
            with self.subTest(language):
                base = self.base(language)
                _, charmap = self.inputs(language)
                resolve, file = archives.from_cartridge(base)
                real = self.keen_eye(language).replacements()[722]
                top = self.workspace()
                for label, member in (('trailing bytes', real + b'\xAA\x55' * 4), ('padding byte', real + b'\0'),
                                      ('flipped last byte', real[:-1] + bytes([real[-1] ^ 1]))):
                    forged = archives.ArchiveDelta.make('a/0/2/7', 156, 'keen-eye-text', file(156), {722: member})
                    with self.subTest(label):
                        with self.assertRaises(ValueError):
                            build.compose(base, 'ui', charmap, top / ('s-' + label.replace(' ', '-')),
                                          ui_config=top / 'ui-candidate.json', archive_deltas=(forged,))
                # the genuine image rejects the forged declaration in the independent verifier too
                image, _, _, _ = self.compose(language, 'text', (self.keen_eye(language),))
                forged = archives.ArchiveDelta.make('a/0/2/7', 156, 'keen-eye-text', file(156), {722: real + b'\xAA\x55' * 4})
                with self.assertRaises(ValueError):
                    self.verify(language, image, (forged,))

    def test_a_stage_appending_after_the_ui_is_rejected_by_the_verifier_and_the_seed_check(self):
        image, _, _, _ = self.compose('EN', 'text', (self.keen_eye('EN'),))
        from sgp13.resources import append_file
        resolve, file = archives.from_cartridge(image)
        gifts = archives.apply_members(file(141), {RIBBON[0]: archives.members(file(141))[RIBBON[0]] + b'1234'})
        late = append_file(image, 141, gifts)
        self.assertNotEqual(late, image)
        with self.assertRaises(ValueError):
            self.verify('EN', late, (self.keen_eye('EN'),))
        _, module, guide = seed_state(late)
        self.assertNotEqual(module[20], len(late))

    def test_a_tiny_late_append_is_rejected_by_policy_not_by_the_size_bound(self):
        image, _, _, _ = self.compose('EN', 'text', (self.keen_eye('EN'),))
        from sgp13.resources import append_file
        late = append_file(image, 200, b'\x01' * 64)
        self.assertLess(len(late) - len(image), 1024)
        with self.assertRaises(ValueError) as caught:
            self.verify('EN', late, (self.keen_eye('EN'),))
        self.assertNotIn('bounded', str(caught.exception))
        _, module, _ = seed_state(late)
        self.assertNotEqual(module[20], len(late))

    def test_an_in_place_change_of_a_foreign_file_is_named_as_such(self):
        """M6 is an equivalent mutant of the protected-suffix comparison; this pins the earlier, named refusal."""
        image, _, _, _ = self.compose('EN', 'text', (self.keen_eye('EN'),))
        start, end = fat_entry(image, 200)
        tampered = bytearray(image)
        tampered[start + (end - start) // 2] ^= 0x10
        with self.assertRaisesRegex(ValueError, 'foreign active file 200'):
            self.verify('EN', bytes(tampered), (self.keen_eye('EN'),))

    def test_an_undeclared_member_alteration_is_rejected(self):
        image, _, _, _ = self.compose('EN', 'text', (self.keen_eye('EN'),))
        start, end = fat_entry(image, 156)
        spans, _, _, base = archives._geometry(image[start:end])
        for index in (100, 722, 828):
            with self.subTest(index):
                tampered = bytearray(image)
                tampered[start + base + spans[index][0] + 1] ^= 0x40
                with self.assertRaises(ValueError):
                    self.verify('EN', bytes(tampered), (self.keen_eye('EN'),))

    def test_unregistered_producer_and_unlisted_archive_are_denied_at_install(self):
        base = self.base('EN')
        resolve, file = archives.from_cartridge(base)
        _, charmap = self.inputs('EN')
        top = self.workspace()
        stranger = archives.ArchiveDelta.make('a/0/1/2', resolve('a/0/1/2'), 'nobody', file(141), {3: b'x'})
        unlisted = archives.ArchiveDelta.make('a/0/1/1', resolve('a/0/1/1'), 'keen-eye-text', file(140), {3: b'x'})
        for n, delta in enumerate((stranger, unlisted)):
            with self.subTest(delta.record()['producers']):
                with self.assertRaises(ValueError):
                    build.compose(base, 'ui', charmap, top / ('s%d' % n), ui_config=top / 'ui-candidate.json',
                                  archive_deltas=(delta,))

    def test_overlapping_producers_on_one_member_are_refused_at_install(self):
        base = self.base('EN')
        _, charmap = self.inputs('EN')
        top = self.workspace()
        resolve, file = archives.from_cartridge(base)
        clash = archives.ArchiveDelta.make('a/0/2/7', 156, 'gifts-messages-test', file(156), {722: b'collides'})
        with registered(*GIFTS):
            with self.assertRaises(ValueError):
                build.compose(base, 'ui', charmap, top / 'clash', ui_config=top / 'ui-candidate.json',
                              archive_deltas=(self.keen_eye('EN'), clash))


class MultiProducer(Real):
    def test_producers_on_disjoint_members_compose_once_and_the_seeds_follow(self):
        for language in LANGUAGES:
            with self.subTest(language):
                (image, report, _, _), deltas = self.gifts(language)
                plain, _, _, _ = self.compose(language, 'none')
                base = self.base(language)
                order = [fat_entry(image, f)[0] for f in (27, 54, 156, 167, 141)]
                self.assertEqual(order, sorted(order))
                self.assertEqual(fat_entry(image, 141)[1], len(image))
                _, module, guide = seed_state(image)
                self.assertEqual((module[20], guide[7]), (len(image), len(image)))
                records = {r['archive']: r for r in report['receipts'][0]['archive_deltas']}
                self.assertEqual(sorted(records), ['a/0/1/2', 'a/0/2/7'])
                self.assertEqual(records['a/0/2/7']['producers'], ['gifts-messages-test', 'keen-eye-text'])
                self.assertEqual(records['a/0/1/2']['producers'], ['gifts-ribbons-test', 'gifts-sites-test'])
                self.assertEqual([m['index'] for m in records['a/0/1/2']['members']], sorted(RIBBON + SITES))
                old141 = archives.members(base[slice(*fat_entry(base, 141))])
                new141 = archives.members(image[slice(*fat_entry(image, 141))])
                self.assertEqual([i for i, (a, b) in enumerate(zip(old141, new141)) if a != b], sorted(RIBBON + SITES))
                old156 = archives.members(base[slice(*fat_entry(base, 156))])
                new156 = archives.members(image[slice(*fat_entry(image, 156))])
                self.assertEqual([i for i, (a, b) in enumerate(zip(old156[:829], new156[:829])) if a != b],
                                 sorted((722,) + MESSAGES))
                self.assertLess(len(image) - len(plain), len(base[slice(*fat_entry(base, 141))]) + 4096)
                for fid in range(513):
                    if fid not in (27, 54, 156, 167, 141):
                        self.assertEqual(fat_entry(image, fid), fat_entry(base, fid), fid)

    def test_the_order_of_independent_producers_does_not_change_the_image(self):
        (image, _, _, _), deltas = self.gifts('EN')
        with registered(*GIFTS):
            self.assertEqual(archives.normalize(deltas), archives.normalize(tuple(reversed(deltas))))
            reverse, _, _, _ = self.compose('EN', 'all-reversed', tuple(reversed(deltas)))
        self.assertEqual(hashlib.sha256(reverse).hexdigest(), hashlib.sha256(image).hexdigest())

    def test_the_verifier_needs_every_declaration_and_every_checker(self):
        (image, _, _, _), deltas = self.gifts('EN')
        with registered(*GIFTS):
            self.verify('EN', image, deltas)
            with self.assertRaises(ValueError):
                self.verify('EN', image, deltas[:1])                      # gift producers undeclared
            partial = archives.normalize(deltas[:1] + deltas[1:2])        # sites missing from a/0/1/2 + messages undeclared
            with self.assertRaises(ValueError):
                self.verify('EN', image, partial)
        with self.assertRaises(ValueError):
            self.verify('EN', image, deltas)                               # checkers no longer registered

    def test_replay_runs_every_producer_and_compares_the_merged_record(self):
        for language in LANGUAGES:
            with self.subTest(language):
                (image, report, inputs, top), deltas = self.gifts(language)
                with registered(*GIFTS):
                    result = build.verify_composition(self.base(language), image, report['receipts'], through='ui',
                                                      ui_inputs=inputs, scratch=top / 'replay-multi')
                    self.assertTrue(result['static_verified'])
                    forged = json.loads(json.dumps(report['receipts']))
                    forged[0]['archive_deltas'][0]['members'][1]['producer'] = 'gifts-sites-test'
                    with self.assertRaises(ValueError):
                        build.verify_composition(self.base(language), image, forged, through='ui', ui_inputs=inputs,
                                                 scratch=top / 'replay-multi-forged')
                with self.assertRaises(ValueError):                          # producers unregistered: no replay
                    build.verify_composition(self.base(language), image, report['receipts'], through='ui',
                                             ui_inputs=inputs, scratch=top / 'replay-multi-bare')

    def test_an_undeclared_change_in_the_appended_archive_is_rejected(self):
        (image, _, _, _), deltas = self.gifts('EN')
        start, end = fat_entry(image, 141)
        spans, _, _, base = archives._geometry(image[start:end])
        tampered = bytearray(image)
        tampered[start + base + spans[10][0]] ^= 0x01
        with registered(*GIFTS):
            with self.assertRaises(ValueError):
                self.verify('EN', bytes(tampered), deltas)

    def test_downstream_in_place_stage_still_composes_after_the_single_append(self):
        from . import mechanics_stages as ms
        for language in LANGUAGES:
            with self.subTest(language):
                (image, _, _, _), _ = self.gifts(language)
                out, receipt = ms.run_stage('moves', image, language)
                self.assertEqual(len(out), len(image))
                self.assertEqual(ms.check_ui_seeds(out)['rom_bytes'], len(image))


@unittest.skipUnless(hasattr(build, 'UI_CHAIN'), 'mechanical chain (mechanics_stages) not in build.py')
class ChainWithDeltas(Real):
    def test_deltas_then_moves_and_ai_compose_and_replay_from_one_report(self):
        for language in LANGUAGES:
            with self.subTest(language):
                base = self.base(language)
                _, charmap = self.inputs(language)
                with registered(*GIFTS):
                    deltas = (self.keen_eye(language),) + derive_all(base, ('gifts-ribbons-test', 'gifts-messages-test'))
                    top = self.workspace()
                    image, report = build.compose(base, 'ai', charmap, top / 'scratch', ui_config=top / 'ui-candidate.json',
                                                  archive_deltas=deltas)
                    self.assertEqual([r['stage'] for r in report['receipts']], ['ui', 'moves', 'ai'])
                    self.assertEqual(len(report['receipts'][0]['archive_deltas']), 2)
                    _, module, guide = seed_state(image)
                    self.assertEqual((module[20], guide[7]), (len(image), len(image)))
                    inputs = build.snapshot_ui_inputs(charmap, top / 'ui-candidate.json')
                    result = build.verify_composition(base, image, report['receipts'], through='ai', ui_inputs=inputs,
                                                      scratch=top / 'replay')
                    self.assertTrue(result['static_verified'] if 'static_verified' in result else result)
                    forged = json.loads(json.dumps(report['receipts']))
                    forged[0]['archive_deltas'][0]['members'][0]['after_sha256'] = '0' * 64
                    with self.assertRaises(ValueError):
                        build.verify_composition(base, image, forged, through='ai', ui_inputs=inputs,
                                                 scratch=top / 'replay-forged')


if __name__ == '__main__':
    unittest.main()
