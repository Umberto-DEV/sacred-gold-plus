"""ROM-free regression tests for the candidate-derived move reference."""
import copy
import hashlib
import struct
import unittest
from unittest.mock import patch

from distribution import move_changes as moves


def archive():
    # Synthetic values, deliberately unrelated to a cartridge move table.
    return [struct.pack('<H6BHb3BH', 0, 1, 40, 12, 100, 15, 0,
                        0, 0, 0x12, 3, 2, 0) for _ in range(471)]


class MoveChangesTests(unittest.TestCase):
    def test_full_record_has_signed_priority_and_lossless_trailing_fields(self):
        records = archive()
        records[7] = struct.pack('<H6BHb3BH', 257, 2, 0, 9, 0, 30, 100,
                                 0x0201, -6, 0xF3, 19, 4, 0x4321)
        row = moves.parse_moves(records)[7]
        self.assertEqual(row['effect'], 257)
        self.assertEqual(row['priority'], -6)
        self.assertEqual(row['target'], 0x0201)
        self.assertEqual(row['reserved'], 0x4321)
        self.assertEqual(row['record_hex'], records[7].hex())

    def test_wrong_member_count_and_truncated_member_are_rejected(self):
        for records in (archive()[:-1], archive() + [bytes(16)]):
            with self.assertRaisesRegex(ValueError, '471'):
                moves.parse_moves(records)
        records = archive(); records[450] = bytes(15)
        with self.assertRaisesRegex(ValueError, '450.*16'):
            moves.parse_moves(records)

    def test_every_changed_byte_survives_comparison_including_nonbattle_fields(self):
        before = archive(); after = archive()
        for offset in range(16):
            changed = bytearray(after[offset + 1]); changed[offset] ^= 1
            after[offset + 1] = bytes(changed)
        rows = moves.compare_moves(moves.parse_moves(before), moves.parse_moves(after))
        self.assertEqual([row['id'] for row in rows], list(range(1, 17)))
        self.assertEqual(sum(len(row['changed_bytes']) for row in rows), 16)
        self.assertEqual(set(d['field'] for row in rows for d in row['deltas']),
                         set(moves.FIELDS))

    def test_names_can_change_without_a_numeric_delta(self):
        before = moves.parse_moves(archive()); after = copy.deepcopy(before)
        before[12]['name'] = 'Original'; after[12]['name'] = 'Replacement'
        rows = moves.compare_moves(before, after)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['deltas'], [dict(field='name', before='Original', after='Replacement')])

    def test_nonplayable_members_are_reported_separately(self):
        before = moves.parse_moves(archive()); after = copy.deepcopy(before)
        after[469]['pp'] = 40
        self.assertEqual(moves.compare_moves(before, after), [])
        self.assertEqual(moves.compare_moves(before, after, playable_only=False)[0]['id'], 469)

    def test_accuracy_zero_and_effect_bypass_are_distinct(self):
        self.assertIn('no ordinary accuracy check', moves.describe_value('accuracy', 0))
        self.assertIn('bypasses', moves.describe_value('effect', 17))
        self.assertEqual(moves.describe_value('accuracy', 85), '85%')

    def test_plus_fairy_label_is_not_taken_from_the_unmodified_mystery_text_slot(self):
        names = ['type'] * 18; names[9] = '???'
        self.assertEqual(moves.type_names_for(names, 'EN', plus=True)[9], 'Fairy')
        self.assertEqual(moves.type_names_for(names, 'EN', plus=False)[9], '???')
        self.assertEqual(names[9], '???')

    def test_flags_preserve_unknown_bits_without_fabricated_meanings(self):
        self.assertIn('contact', moves.describe_value('flags', 1))
        self.assertIn('unclassified 0x40', moves.describe_value('flags', 0x40))
        self.assertIn('single selected', moves.describe_value('target', 0))
        self.assertIn('unclassified', moves.describe_value('target', 0x8000))

    def test_table_equality_requires_every_member_and_each_locale(self):
        facts = {locale: dict(moves=moves.parse_moves(archive())) for locale in moves.LOCALES}
        self.assertTrue(moves.verify_shared_move_tables(facts)['equal'])
        facts['DE']['moves'][470]['reserved'] = 1
        with self.assertRaisesRegex(ValueError, 'DE.*470'):
            moves.verify_shared_move_tables(facts)
        del facts['DE']
        with self.assertRaisesRegex(ValueError, 'five'):
            moves.verify_shared_move_tables(facts)

    def test_ancestry_is_observation_not_an_invented_original_sacred_gold_attribution(self):
        before = moves.parse_moves(archive()); after = copy.deepcopy(before)
        after[15]['type'] = 9
        row = moves.compare_moves(before, after)[0]
        historical = [dict(id='plus-early', moves=copy.deepcopy(after))]
        result = moves.add_provenance([row], historical)[0]['provenance']
        self.assertEqual(result['matching_supplied_versions'], ['plus-early'])
        self.assertIn('not established', result['original_sacred_gold_attribution'])

    def test_foreign_candidate_or_old_plus_reference_is_rejected_before_reading_tables(self):
        candidate, retail = b'candidate', b'retail'
        sha = lambda data: hashlib.sha256(data).hexdigest()
        contract = dict(version='1.3.2', targets=dict(EN=dict(sha256=sha(candidate), bytes=len(candidate))),
                        sources=[dict(id='clean-us', label='Retail', sha256=sha(retail), bytes=len(retail))],
                        routes_by_target=dict(EN=['clean-us']))
        with patch.object(moves, 'read_move_facts') as read:
            with self.assertRaisesRegex(ValueError, 'candidate identity'):
                moves.audit_moves(b'foreign', retail, None, contract, 'EN')
            with self.assertRaisesRegex(ValueError, 'clean retail baseline'):
                moves.audit_moves(candidate, b'old-plus', None, contract, 'EN')
            read.assert_not_called()


if __name__ == '__main__':
    unittest.main()
