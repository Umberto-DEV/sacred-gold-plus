"""ROM-free contracts for declared archive member deltas (single-append composition).

The synthetic archives use the real NARC layout (ndspy writer) with members of
awkward sizes, so every padding/alignment rule is exercised without a cartridge.
"""
import hashlib
import json
import struct
import types
import unittest
from unittest.mock import patch

from ndspy.narc import NARC

from . import archives


def narc(members):
    value = NARC()
    value.endiannessOfBeginning = '>'      # the byte order of the retail archives
    value.files = [bytes(m) for m in members]
    return value.save()


MEMBERS = [bytes([i + 1]) * n for i, n in enumerate((5, 8, 13, 1, 22, 6))]


def sha(value):
    return hashlib.sha256(value).hexdigest()


class Fake:
    """Name/file view of a synthetic cartridge: only what `check_against` consumes."""
    def __init__(self, **files):
        self.names = {'a/0/2/7': 156, 'a/0/1/2': 141, 'a/0/1/1': 140, 'a/0/3/8': 167}
        self.raw = {156: narc(MEMBERS + [b'G' * 9]), 141: narc(MEMBERS), 140: narc(MEMBERS),
                    167: narc(MEMBERS)}
        self.raw.update(files)

    def resolve(self, name):
        return self.names[name]

    def file(self, fid):
        return self.raw[fid]


class DeltaShape(unittest.TestCase):
    def setUp(self):
        self.fake = Fake()

    def make(self, index=2, after=b'new-member-bytes', archive='a/0/1/2', fid=141, producer='test'):
        return archives.ArchiveDelta.make(archive, fid, producer, self.fake.file(fid), {index: after})

    def test_record_is_hash_only_and_canonical(self):
        delta = self.make()
        record = delta.record()
        self.assertEqual(record['schema'], 2)
        self.assertEqual(record['producers'], ['test'])
        self.assertEqual(record['members'], [{'index': 2, 'before_sha256': sha(MEMBERS[2]),
                                              'after_sha256': sha(b'new-member-bytes'),
                                              'after_bytes': 16, 'producer': 'test'}])
        self.assertNotIn(b'new-member-bytes'.hex(), repr(record))
        self.assertEqual(delta.sha256(), hashlib.sha256(archives.canonical(record)).hexdigest())
        self.assertEqual(delta.replacements(), {2: b'new-member-bytes'})

    def test_make_rejects_noop_empty_and_out_of_range(self):
        for replacements in ({}, {2: MEMBERS[2]}, {99: b'x'}, {2: b''}, {-1: b'x'}, {True: b'x'}):
            with self.assertRaises(ValueError, msg=repr(replacements)):
                archives.ArchiveDelta.make('a/0/1/2', 141, 'test', self.fake.file(141), replacements)

    def test_normalize_orders_by_file_and_rejects_foreign_types(self):
        a, b = self.make(), self.make(index=1, archive='a/0/2/7', fid=156)
        self.assertEqual([d.file_id for d in archives.normalize([a, b])], [141, 156])
        with self.assertRaises(ValueError):
            archives.normalize([a, 'not a delta'])
        self.assertEqual(archives.normalize(()), ())

    def test_two_producers_on_disjoint_members_of_one_archive_merge_in_any_order(self):
        ribbons = self.make(index=2, producer='ribbons')
        sites = self.make(index=4, after=b'site-bytes', producer='sites')
        forward, backward = archives.normalize([ribbons, sites]), archives.normalize([sites, ribbons])
        self.assertEqual(len(forward), 1)
        self.assertEqual(forward, backward)
        record = forward[0].record()
        self.assertEqual([(m['index'], m['producer']) for m in record['members']], [(2, 'ribbons'), (4, 'sites')])
        self.assertEqual(record['producers'], ['ribbons', 'sites'])
        self.assertEqual(sorted(record['evidence']), ['ribbons', 'sites'] if record['evidence'] else [])
        self.assertEqual(forward[0].replacements(), {2: b'new-member-bytes', 4: b'site-bytes'})

    def test_overlapping_members_the_same_producer_twice_and_mixed_identities_are_refused(self):
        a = self.make(index=2, producer='ribbons')
        with self.assertRaises(ValueError):
            archives.normalize([a, self.make(index=2, after=b'other', producer='sites')])      # overlap
        with self.assertRaises(ValueError):
            archives.normalize([a, self.make(index=2, producer='ribbons')])                    # overlap, same bytes
        with self.assertRaises(ValueError):
            archives.normalize([a, self.make(index=4, producer='ribbons')])                    # producer twice
        other_name = archives.ArchiveDelta.make('a/0/2/7', 141, 'sites', self.fake.file(141), {4: b'x'})
        with self.assertRaises(ValueError):
            archives.normalize([a, other_name])                                                # one file id, two names

    def test_check_against_binds_name_id_and_before_hash(self):
        deltas = archives.normalize([self.make(), self.make(index=1, archive='a/0/2/7', fid=156)])
        archives.check_against(deltas, self.fake.resolve, self.fake.file)
        wrong_id = self.make(fid=141)
        object.__setattr__(wrong_id, 'file_id', 140)
        with self.assertRaises(ValueError):
            archives.check_against((wrong_id,), self.fake.resolve, self.fake.file)
        other = Fake()
        other.raw[141] = narc(MEMBERS[:2] + [b'z' * 13] + MEMBERS[3:])   # member 2 is not the hashed one
        with self.assertRaises(ValueError):
            archives.check_against((self.make(),), other.resolve, other.file)

    def test_check_against_refuses_a_declaration_equal_to_the_original_member(self):
        # A real Member row (not a plain tuple, which is refused by its type) whose bytes equal the V4 member.
        hand = archives.ArchiveDelta('a/0/1/2', 141, (archives.Member(2, sha(MEMBERS[2]), MEMBERS[2], 'test'),))
        with self.assertRaisesRegex(ValueError, 'empty, oversized or unchanged'):
            archives.check_against((hand,), self.fake.resolve, self.fake.file)

    def test_check_against_refuses_plain_tuples_in_place_of_member_rows(self):
        hand = archives.ArchiveDelta('a/0/1/2', 141, ((2, sha(MEMBERS[2]), b'changed-bytes', 'test'),))
        with self.assertRaises(ValueError):
            archives.check_against((hand,), self.fake.resolve, self.fake.file)

    def test_policy_denies_unlisted_archives_ui_files_and_the_guide_member(self):
        for delta in (self.make(archive='a/0/1/1', fid=140), self.make(archive='a/0/3/8', fid=167)):
            with self.assertRaises(ValueError):
                archives.check_against((delta,), self.fake.resolve, self.fake.file)
        guide = archives.ArchiveDelta.make('a/0/2/7', 156, 'test', self.fake.file(156), {6: b'evil'})
        with self.assertRaises(ValueError):
            archives.check_against((guide,), self.fake.resolve, self.fake.file)


class GuideSources(unittest.TestCase):
    def test_members_the_guide_is_built_from_cannot_be_declared(self):
        """item 222, pokemon 237, map 279 and move 750 names feed the Guide at UI compile time: a delta there
        would leave the Guide describing the V4 names, so the policy refuses it until the Guide is rebuilt from them."""
        many = [bytes([i % 251 + 1]) * (i % 7 + 1) for i in range(830)]
        fake = Fake()
        fake.raw[156] = narc(many)
        for index in archives.GUIDE_SOURCE_MEMBERS:
            with self.subTest(index):
                delta = archives.ArchiveDelta.make('a/0/2/7', 156, 'test', fake.file(156), {index: b'new'})
                with self.assertRaises(ValueError):
                    archives.check_against((delta,), fake.resolve, fake.file)
        allowed = archives.ArchiveDelta.make('a/0/2/7', 156, 'test', fake.file(156), {722: b'new'})
        archives.check_against((allowed,), fake.resolve, fake.file)


    def test_script_members_the_guide_pins_cannot_be_declared_in_the_scripts_archive(self):
        """guide_content.SCRIPT_PINS audits a/0/1/2 members 131, 132, 152, 196, 890 at compile time."""
        self.assertEqual(sorted(archives.GUIDE_SCRIPT_MEMBERS), [131, 132, 152, 196, 890])
        many = [bytes([i % 251 + 1]) * (i % 5 + 1) for i in range(965)]
        fake = Fake()
        fake.raw[141] = narc(many)
        for index in archives.GUIDE_SCRIPT_MEMBERS:
            with self.subTest(index):
                delta = archives.ArchiveDelta.make('a/0/1/2', 141, 'test', fake.file(141), {index: b'new'})
                with self.assertRaises(ValueError):
                    archives.check_against((delta,), fake.resolve, fake.file)
        for index in (225, 232, 243, 246, 938, 962):        # the ribbon members stay declarable
            delta = archives.ArchiveDelta.make('a/0/1/2', 141, 'test', fake.file(141), {index: b'new'})
            archives.check_against((delta,), fake.resolve, fake.file)


class Rebuild(unittest.TestCase):
    def test_apply_members_changes_only_declared_members(self):
        raw = narc(MEMBERS)
        out = archives.apply_members(raw, {2: b'0123456789abcdefghi', 4: b'q'})
        expected = list(MEMBERS)
        expected[2], expected[4] = b'0123456789abcdefghi', b'q'
        self.assertEqual(archives.members(out), expected)
        self.assertEqual(out, narc(expected))
        archives.verify_members(raw, out, {2: expected[2], 4: expected[4]})

    def test_empty_replacement_is_identity(self):
        raw = narc(MEMBERS)
        self.assertEqual(archives.apply_members(raw, {}), raw)

    def test_noncanonical_input_is_refused_never_normalised(self):
        raw = bytearray(narc(MEMBERS))
        raw.extend(b'\0\0\0\0')
        struct.pack_into('<I', raw, 8, len(raw))
        with self.assertRaises(ValueError):
            archives.apply_members(bytes(raw), {1: b'x'})


class IndependentReadback(unittest.TestCase):
    def setUp(self):
        self.old = narc(MEMBERS)
        self.new = archives.apply_members(self.old, {2: b'0123456789abcdefghi'})
        self.declared = {2: b'0123456789abcdefghi'}

    def test_accepts_the_exact_declaration(self):
        result = archives.verify_members(self.old, self.new, self.declared)
        self.assertEqual(result['changed'], [2])
        self.assertEqual(result['members'], len(MEMBERS))

    def test_rejects_an_undeclared_member_change(self):
        tampered = archives.apply_members(self.new, {0: b'\x09' * 5})
        with self.assertRaises(ValueError):
            archives.verify_members(self.old, tampered, self.declared)

    def test_rejects_a_declared_member_that_was_not_applied(self):
        with self.assertRaises(ValueError):
            archives.verify_members(self.old, self.old, self.declared)

    def test_rejects_a_declaration_equal_to_the_original_member(self):
        with self.assertRaises(ValueError):
            archives.verify_members(self.old, self.old, {2: MEMBERS[2]})

    def test_rejects_a_declared_member_with_other_bytes(self):
        with self.assertRaises(ValueError):
            archives.verify_members(self.old, self.new, {2: b'0123456789abcdefghX'})

    def test_rejects_member_count_name_table_and_hidden_tail(self):
        grown = narc(MEMBERS + [b'x'])
        with self.assertRaises(ValueError):
            archives.verify_members(self.old, grown, self.declared)
        tail = bytearray(self.new)
        tail.extend(b'\0\0\0\0')
        struct.pack_into('<I', tail, 8, len(tail))
        with self.assertRaises(ValueError):
            archives.verify_members(self.old, bytes(tail), self.declared)

    def test_rejects_nonzero_alignment_padding(self):
        bad = bytearray(self.new)
        base = archives._geometry(bytes(bad))[3]
        spans = archives._geometry(bytes(bad))[0]
        gap = base + spans[2][1]                        # member 2 is 19 bytes -> one padding byte
        self.assertEqual(spans[3][0] - spans[2][1], 1)
        bad[gap] = 0x5A
        with self.assertRaises(ValueError):
            archives.verify_members(self.old, bytes(bad), self.declared)


class Semantics(unittest.TestCase):
    def delta(self, producer):
        raw = narc(MEMBERS)
        return archives.ArchiveDelta.make('a/0/1/2', 141, producer, raw, {2: b'new'}), raw, \
            archives.apply_members(raw, {2: b'new'})

    def test_unknown_producer_is_denied(self):
        delta, old, new = self.delta('nobody')
        with self.assertRaises(ValueError):
            archives.check_semantics(delta, old, new, 'EN')

    def test_registered_checker_is_called_with_member_bytes_and_may_reject(self):
        delta, old, new = self.delta('probe')
        calls = []

        def accept(index, before, after, language):
            calls.append((index, before, after, language))

        with patch.dict(archives.CHECKERS, {'probe': accept}):
            archives.check_semantics(delta, old, new, 'IT')
        self.assertEqual(calls, [(2, MEMBERS[2], b'new', 'IT')])

        def reject(index, before, after, language):
            raise ValueError('semantic reject')

        with patch.dict(archives.CHECKERS, {'probe': reject}):
            with self.assertRaises(ValueError):
                archives.check_semantics(delta, old, new, 'IT')


    def test_each_member_is_checked_by_its_own_producer(self):
        raw = narc(MEMBERS)
        a = archives.ArchiveDelta.make('a/0/1/2', 141, 'p-one', raw, {1: b'one'})
        b = archives.ArchiveDelta.make('a/0/1/2', 141, 'p-two', raw, {3: b'two'})
        merged = archives.normalize([a, b])[0]
        new = archives.apply_members(raw, merged.replacements())
        seen = []
        with patch.dict(archives.CHECKERS, {'p-one': lambda i, b, a, l: seen.append(('one', i)),
                                            'p-two': lambda i, b, a, l: seen.append(('two', i))}):
            archives.check_semantics(merged, raw, new, 'EN')
        self.assertEqual(seen, [('one', 1), ('two', 3)])
        with patch.dict(archives.CHECKERS, {'p-one': lambda i, b, a, l: None}):               # p-two has no checker
            with self.assertRaises(ValueError):
                archives.check_semantics(merged, raw, new, 'EN')

    def test_a_checker_failing_with_a_foreign_exception_is_a_refusal(self):
        raw = narc(MEMBERS)
        delta = archives.ArchiveDelta.make('a/0/1/2', 141, 'probe', raw, {2: b'new'})
        new = archives.apply_members(raw, delta.replacements())
        for error in (TypeError('x'), IndexError('x'), KeyError('x'), struct.error('x'), OverflowError('x')):
            def checker(i, b, a, l, error=error):
                raise error
            with patch.dict(archives.CHECKERS, {'probe': checker}):
                with self.assertRaises(ValueError, msg=repr(error)):
                    archives.check_semantics(delta, raw, new, 'EN')

    def test_the_keen_eye_checker_refuses_short_or_hostile_members_with_a_value_error(self):
        for before, after in ((b'', b''), (b'abc', b'x'), (b'\0\0\0\0', b'\x7c\0\0\0'), (b'\xff' * 4, b'\xff' * 4)):
            for language in ('EN', 'IT', 'XX', None, 5):
                with self.assertRaises(ValueError, msg=(before, after, language)):
                    archives._keen_eye_text(722, before, after, language)
        with self.assertRaises(ValueError):
            archives._keen_eye_text('722', b'\0' * 8, b'\0' * 8, 'EN')

    def test_the_keen_eye_checker_turns_a_foreign_exception_of_the_text_module_into_a_refusal(self):
        """With the pinned text.py no input reaches a foreign exception (60 000 fuzz calls, none), so the guard
        is exercised by a stub text module whose reader fails the way a changed library could."""
        header = struct.pack('<HH', 124, 0)
        for error in (IndexError('x'), struct.error('x'), KeyError('x'), TypeError('x'), OverflowError('x'), UnicodeError('x')):
            def broken(raw, row, error=error):
                raise error
            stub = types.SimpleNamespace(DESCRIPTIONS={'EN': 0}, BANK=722, ROWS=124, ROW=51, decode_row=broken)
            with patch.object(archives, '_text_module', lambda stub=stub: stub):
                with self.assertRaises(ValueError, msg=repr(error)):
                    archives._keen_eye_text(722, header + b'\0' * 8, header + b'\1' * 8, 'EN')


class HostileRecords(unittest.TestCase):
    CHARMAP = None

    def test_rederive_refuses_hostile_records_with_a_value_error(self):
        good_shape = {'schema': 2, 'archive': 'a/0/1/2', 'file_id': 141, 'producers': ['nobody'], 'members': [], 'evidence': {}}
        for records in (None, 5, 'text', {'a': 1}, [None], [5], ['x'], [[]], [{}], [{'producer': ['x']}],
                        [{'producer': {}}], [{'producer': None}], [{'producers': [['x']]}], [{'producers': [{}]}],
                        [{'producers': 'nobody'}], [dict(good_shape, producers=[None])], [dict(good_shape, producers=[])],
                        [dict(good_shape)], [dict(good_shape, schema=1)], [dict(good_shape, producers=['nobody', 'nobody'])],
                        [dict(good_shape, producers=[['x']])], [dict(good_shape, producers=[{}])],
                        [dict(good_shape, producers=[1])], [dict(good_shape, producers=[b'nobody'])]):
            with self.subTest(repr(records)[:60]):
                with self.assertRaises(ValueError):
                    archives.rederive(b'', 'EN', None, records)

    def test_rederive_with_no_records_is_empty(self):
        self.assertEqual(archives.rederive(b'', 'EN', None, []), ())

    def test_rederive_compares_the_merged_record_of_registered_producers(self):
        raw = narc(MEMBERS)

        def producer(name, index):
            def derive(base, language, charmap):
                return archives.ArchiveDelta.make('a/0/1/2', 141, name, raw, {index: name.encode()})
            return derive
        with patch.dict(archives.PRODUCERS, {'p-one': producer('p-one', 1), 'p-two': producer('p-two', 3)}):
            expected = [d.record() for d in archives.normalize([producer('p-one', 1)(0, 0, 0), producer('p-two', 3)(0, 0, 0)])]
            self.assertEqual(len(archives.rederive(b'', 'EN', None, expected)), 1)
            forged = json.loads(json.dumps(expected))
            forged[0]['members'][0]['after_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                archives.rederive(b'', 'EN', None, forged)


if __name__ == '__main__':
    unittest.main()


class OwnerProducers(unittest.TestCase):
    """Gift producers (c8) are registered lazily: either import order works, and nothing is overridden."""

    def test_either_import_order_registers_the_gift_producers(self):
        import subprocess, sys
        for first in ('sgp131.archives', 'sgp131.gifts_archives'):
            code = ('import importlib; importlib.import_module(%r); from sgp131 import archives, gifts_archives as g;'
                    'archives.register_owner_producers(); archives.register_owner_producers();'
                    'assert all(archives.PRODUCERS[k] is v for k, v in g.PRODUCERS.items());'
                    'assert all(archives.CHECKERS[k] is v for k, v in g.CHECKERS.items());'
                    "assert 'keen-eye-text' in archives.PRODUCERS" % first)
            with self.subTest(first=first):
                result = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_conflicting_registration_is_refused(self):
        archives.register_owner_producers()
        from . import gifts_archives
        name = next(iter(gifts_archives.PRODUCERS))
        with patch.dict(archives.PRODUCERS, {name: lambda *a: None}):
            with self.assertRaisesRegex(ValueError, 'registered twice'):
                archives.register_owner_producers()
