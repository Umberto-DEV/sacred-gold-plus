"""ROM-free contracts of the gift-script audit: published recipes, pinned guards and the admission gate."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from sgp131 import gifts_audit as audit


def good_receipt():
    return {
        'native': {k: True for k in ('count_matches', 'dispatcher_matches', 'reader_matches',
                                     'fanfare_entry_matches', 'fanfare_handler_matches', 'script_api_matches')}
        | {'handlers': {'137': {'name': 'GiveMon', 'entry': 1, 'matches': True, 'prologue_matches': True}}},
        'native_probe': {'reader': {'value': 78, 'advance': 2},
                         'fanfare_handler': {'advance': 2, 'operand_resolved': [20], 'sound_calls': 1},
                         'defective_tail': {'returned': 0, 'mode_after': 0, 'asserts': 1,
                                            'consumed_bytes': 6, 'reached_close_msg': False}},
        'decode_errors': [], 'overlapping_instructions': [{'member': 131, 'first': 1, 'second': 2,
                                                           'accepted': True}],
        'members': {'unrecognized': []},
        'ribbon_tails': {'225': {'errors': [], 'trace_ok': True}},
    }


class PublishedData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claims = audit.load_claims()
        cls.guards = audit.load_guards()

    def test_the_recipe_file_holds_exactly_the_two_fixes_and_the_accepted_overlap(self):
        self.assertEqual(set(self.claims), {'schema', 'purpose', 'pret_commit', 'metadata_sha256', 'archive', 'stage',
                                            'ribbon_tails', 'accepted_overlaps', 'party_guard'})
        self.assertEqual(sorted(self.claims['ribbon_tails']['members'], key=int),
                         ['225', '232', '243', '246', '938', '962'])
        text = (audit.DATA / 'gifts-claims.json').read_text()
        self.assertLess(len(text), 8000, 'hashes and numbers only: no census, no game bytes')

    def test_the_party_guard_recipe_is_the_pinned_eevee_site_with_the_retail_limit(self):
        guard = self.claims['party_guard']
        self.assertEqual((guard['member'], guard['species'], guard['level'], guard['limit']), (227, 133, 5, 6))
        self.assertEqual(guard['preimage_sha256']['EN'], guard['preimage_sha256']['IT'])
        self.assertEqual(guard['lead_in'], ['PlaySE', 'LockAll', 'FacePlayer'])
        self.assertLess(guard['insert_at'], guard['party_count_site'])
        self.assertEqual(guard['party_count_site'] + 4, guard['give_site'])
        self.assertEqual((guard['party_var'], guard['effects']), (0x8005, {'flag': 16220, 'hide_person': 15}))
        self.assertEqual(set(guard['message']['bank_sha256']), {'EN', 'IT'})
        self.assertTrue(all(len(h) == 64 for h in guard['message']['bank_sha256'].values()))
        self.assertEqual((guard['message']['bank'], guard['message']['index']), (25, 39))

    def test_guards_pin_the_native_dispatch_facts(self):
        guards = self.guards
        self.assertEqual(guards['command_table']['count'], 853)
        self.assertEqual(guards['command_table']['address'], '0x020FAD00')
        self.assertEqual(guards['fanfare']['halfword_reads'], 1)
        self.assertEqual(guards['fanfare']['operand_bytes'], 2)
        self.assertEqual(guards['rejected_opcode']['value'], 2009)
        self.assertEqual(guards['dispatcher']['address'], '0x0203FD6C')
        self.assertEqual(sorted(guards['handlers']), ['137'])
        for handler in guards['handlers'].values():
            self.assertRegex(handler['entry'], r'^0x[0-9A-F]{8}$')

    def test_the_guards_file_keeps_only_what_the_audit_reads(self):
        self.assertEqual(set(self.guards), {'schema', 'stage', 'sources', 'command_table', 'dispatcher',
                                            'script_read_halfword', 'fanfare', 'script_api', 'rejected_opcode',
                                            'handlers'})

    def test_accepted_overlap_is_pinned_to_one_member_hash(self):
        allowance, = self.claims['accepted_overlaps']
        self.assertEqual(allowance['member'], 131)
        self.assertEqual(len(allowance['pairs']), 3)
        self.assertEqual(len(set(allowance['preimage_sha256'].values())), 1)
        digest = list(allowance['preimage_sha256'].values())[0]
        self.assertTrue(audit._overlap_accepted(self.claims, 131, digest, 0x12db, 0x12df))
        self.assertFalse(audit._overlap_accepted(self.claims, 131, '0' * 64, 0x12db, 0x12df))
        self.assertFalse(audit._overlap_accepted(self.claims, 132, digest, 0x12db, 0x12df))
        self.assertFalse(audit._overlap_accepted(self.claims, 131, digest, 0x12db, 0x12e0))

    def test_metadata_loader_rejects_a_foreign_command_table(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scrcmd.json'
            path.write_text(json.dumps({'commands': [{'name': 'X', 'args': []}] * 853}))
            with self.assertRaisesRegex(ValueError, 'metadata SHA-256'):
                audit.load_commands(path)
            with self.assertRaises(FileNotFoundError):
                audit.load_commands(Path(directory) / 'missing.json')


class ProbeClassification(unittest.TestCase):
    def test_close_msg_is_reached_exactly_when_the_dispatcher_read_past_the_refused_halfword(self):
        self.assertFalse(audit.reached_close_msg(6))
        self.assertFalse(audit.reached_close_msg(7))
        self.assertTrue(audit.reached_close_msg(8))
        self.assertTrue(audit.reached_close_msg(12))


class Gate(unittest.TestCase):
    def test_a_complete_receipt_passes(self):
        self.assertIsNone(audit.require_complete_audit(good_receipt()))

    def test_each_blocker_is_refused_by_name(self):
        cases = {
            'native count': (lambda r: r['native'].update(count_matches=False), 'count_matches'),
            'script api': (lambda r: r['native'].update(script_api_matches=False), 'script_api_matches'),
            'dispatcher': (lambda r: r['native'].update(dispatcher_matches=False), 'dispatcher_matches'),
            'handler': (lambda r: r['native']['handlers']['137'].update(matches=False), 'GiveMon'),
            'handler body': (lambda r: r['native']['handlers']['137'].update(prologue_matches=False),
                             'different body at the pinned entry'),
            'reader value': (lambda r: r['native_probe']['reader'].update(value=79), 'exactly one halfword'),
            'operand': (lambda r: r['native_probe']['fanfare_handler'].update(operand_resolved=[21]),
                        'exactly one halfword'),
            'consumed': (lambda r: r['native_probe']['defective_tail'].update(consumed_bytes=8),
                         'does not reject opcode 2009'),
            'dispatch returned': (lambda r: r['native_probe']['defective_tail'].update(returned=1),
                                  'does not reject opcode 2009'),
            'decode error': (lambda r: r['decode_errors'].append({'member': 225, 'error': 'opcode illegale 2009 a 886'}),
                             'member 225: opcode illegale 2009'),
            'unaccepted overlap': (lambda r: r['overlapping_instructions'].append(
                {'member': 7, 'first': 4, 'second': 6, 'accepted': False}), 'overlapping instructions'),
            'unrecognized member': (lambda r: r['members'].update(unrecognized=[3]), 'unrecognized'),
            'ribbon': (lambda r: r['ribbon_tails']['225'].update(trace_ok=False), 'ribbon tail of member 225'),
            'no probe': (lambda r: r.pop('native_probe'), 'probe was not executed'),
            'wide fanfare': (lambda r: r['native_probe']['fanfare_handler'].update(advance=4), 'exactly one halfword'),
            'accepted 2009': (lambda r: r['native_probe']['defective_tail'].update(asserts=0), 'does not reject opcode 2009'),
            'ran past 2009': (lambda r: r['native_probe']['defective_tail'].update(reached_close_msg=True),
                              'does not reject opcode 2009'),
        }
        for name, (mutate, message) in cases.items():
            receipt = copy.deepcopy(good_receipt())
            mutate(receipt)
            with self.subTest(name):
                with self.assertRaisesRegex(ValueError, message):
                    audit.require_complete_audit(receipt)

    def test_blockers_are_all_reported_not_just_the_first(self):
        receipt = good_receipt()
        receipt['decode_errors'] = [{'member': m, 'error': 'opcode illegale 2009 a 1'} for m in (225, 232, 243)]
        with self.assertRaises(ValueError) as caught:
            audit.require_complete_audit(receipt)
        for member in ('225', '232', '243'):
            self.assertIn(f'member {member}:', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
