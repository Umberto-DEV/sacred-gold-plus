import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from . import baseline, reserve

DATA = b'authored tiny resident-policy fixture'
MAP = Path(__file__).parent / 'data/reserve-map.json'
REQUEST = {'training.ui': 1360, 'physical.code': 904, 'physical.slot': 48,
           'narrative.spawn_table': 540, 'settings.descriptor': 80, 'settings.generation': 16}


# Independent literal expectations: these are conditional metadata, never grants.
B5_PARTS = {
    'plus-ui.extended': (
        ('ui.bridge.code', 0x023CB800, 8192, 'payload'),),
    'plus-ui.shiny-text': (
        ('ui.bridge.tail', 0x023CD800, 4080, 'payload'),
        ('ui.bridge.guard', 0x023CE7F0, 16, 'guard')),
    'field-guide.code': (
        ('fieldbook.code', 0x023D4000, 3072, 'payload'),
        ('fieldbook.guard', 0x023D4C00, 16, 'guard'),
        ('summary-controls.runtime', 0x023D4C10, 512, 'payload'),
        ('portable-box.runtime', 0x023D4E10, 3024, 'payload'),
        ('c8.module-stubs', 0x023D59E0, 192, 'payload'),
        ('modern-accuracy.code', 0x023D5AA0, 32, 'payload'),
        ('field-guide.code.preserved', 0x023D5AC0, 1344, 'preserved')),
    'field-guide.config-state': (
        ('guide.metadata.retained', 0x023D7B00, 16, 'retained'),
        ('guide.template', 0x023D7B10, 16, 'payload'),
        ('ui.bootstrap', 0x023D7B20, 40, 'payload'),
        ('ui.control', 0x023D7B48, 16, 'payload'),
        ('ui.bootstrap.guard', 0x023D7B58, 8, 'guard'),
        ('ui.module.seed', 0x023D7B60, 96, 'payload'),
        ('ui.resource.seed', 0x023D7BC0, 64, 'payload'),
        ('ui.guide.seed', 0x023D7C00, 64, 'payload'),
        ('guide.labels.retained', 0x023D7C40, 448, 'retained'),
        ('guide.field-state.retained', 0x023D7E00, 240, 'retained'),
        ('guide.canary.retained', 0x023D7EF0, 16, 'retained')),
}


def policy():
    return json.loads(MAP.read_text())


def b6_policy():
    """Independent proposed fixture; no production constants construct it."""
    p = policy()
    p['version'] = 'sgp131-resident-12'
    entry = next(e for e in p['subdivisions'] if e['parent'] == 'field-guide.code')
    entry['parts'] = [
        {'name': 'fieldbook.code', 'start': 0x023D4000, 'bytes': 3072, 'kind': 'payload'},
        {'name': 'fieldbook.guard', 'start': 0x023D4C00, 'bytes': 16, 'kind': 'guard'},
        {'name': 'summary-controls.runtime', 'start': 0x023D4C10, 'bytes': 512, 'kind': 'payload'},
        {'name': 'portable-box.runtime', 'start': 0x023D4E10, 'bytes': 3024, 'kind': 'payload'},
        {'name': 'c8.module-stubs', 'start': 0x023D59E0, 'bytes': 192, 'kind': 'payload'},
        {'name': 'modern-accuracy.code', 'start': 0x023D5AA0, 'bytes': 32, 'kind': 'payload'},
        {'name': 'field-guide.code.preserved', 'start': 0x023D5AC0, 'bytes': 1344, 'kind': 'preserved'}]
    return p


def metadata():
    p = policy()
    return {'sections': [{'start': 0x02000000, 'bytes': 1120352, 'bss': 868512}, *copy.deepcopy(p['native']['autoloads'])],
            'overlays': [{'id': i, 'file_id': i, 'start': 0x021E5900, 'bytes': 4, 'bss': 0} for i in range(129)],
            'arena': copy.deepcopy(p['arena']),
            'guard_sha256': {str(g['start']): g['sha256']['EN'] for g in p['guards']},
            'owner_sha256': {g['name']: hashlib.sha256(bytes(g['bytes'])).hexdigest() for g in p['roots']},
            'preservation': {'arm7_sha256': 'a'*64, 'fnt_sha256': 'b'*64, 'fat_sha256': 'c'*64,
                             'files_sha256': 'd'*64, 'file_count': 513, 'arm7_overlay_bytes': 0}}


class ReserveTests(unittest.TestCase):
    def setUp(self):
        self.meta = metadata()
        self.decode = patch('sgp131.reserve._decode', side_effect=lambda data, policy: copy.deepcopy(self.meta))
        self.decode.start(); self.addCleanup(self.decode.stop)
        self.identity = patch.dict(baseline.INPUT_HASHES, {hashlib.sha256(DATA).hexdigest(): 'EN'}, clear=True)
        self.identity.start(); self.addCleanup(self.identity.stop)

    def test_audit_has_complete_coverage_and_no_default_arena_reduction(self):
        result = reserve.audit(DATA)
        self.assertIsInstance(result, dict)
        self.assertEqual((result['base'], result['end']), (0x023C8000, 0x023E0000))
        self.assertEqual(result['owned_bytes'], 98304)
        self.assertEqual(result['free_bytes'], 0)
        self.assertEqual(result['overlay_count'], 129)
        self.assertEqual(result['arena'], self.meta['arena'])
        self.assertEqual(result['preservation'], self.meta['preservation'])

    def test_owned_zero_padding_is_not_free(self):
        for name in ('training.extension', 'plus-ui.extended', 'legacy.1.2',
                     'field-guide.code', 'shiny.native', 'training.ui.guard'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'payload|owner|assign'):
                reserve.allocate(DATA, {name: 4})

    def test_public_addresses_and_files_preserved(self):
        allocation = reserve.allocate(DATA, REQUEST)
        self.assertIsInstance(allocation, dict)
        result = reserve.apply(DATA, allocation)
        self.assertIsInstance(result, tuple)
        after, receipt = result
        self.assertEqual(after, DATA)
        self.assertTrue(receipt['byte_identical'])
        self.assertFalse(receipt['installation_authorized'])
        self.assertFalse(receipt['installed'])
        self.assertEqual(receipt['preservation'], self.meta['preservation'])

    def test_combined_payload_overflow_refused(self):
        request = {**REQUEST, 'training.ui': 1540, 'narrative.spawn_table': 544}
        with self.assertRaisesRegex(ValueError, 'capacity|overflow'):
            reserve.allocate(DATA, request)

    def test_overlay_bss_collision_refused(self):
        self.meta['overlays'][0].update(start=0x023C7FF0, bytes=4, bss=32)
        with self.assertRaisesRegex(ValueError, 'overlay|overlap'):
            reserve.audit(DATA)

    def test_autoload_bss_collision_refused(self):
        self.meta['sections'][1].update(start=0x023C7FF0, bytes=4, bss=32)
        with self.assertRaisesRegex(ValueError, 'autoload|section|overlap'):
            reserve.audit(DATA)

    def test_arena_preimage_required(self):
        self.meta['arena'][0]['value'] -= 8192
        with self.assertRaisesRegex(ValueError, 'arena'):
            reserve.audit(DATA)

    def test_guard_and_original_abi2_prefix_required(self):
        for guard in policy()['guards']:
            original = self.meta['guard_sha256'][str(guard['start'])]
            self.meta['guard_sha256'][str(guard['start'])] = '0'*64
            with self.subTest(start=guard['start']), self.assertRaisesRegex(ValueError, 'guard|preimage'):
                reserve.audit(DATA)
            self.meta['guard_sha256'][str(guard['start'])] = original

    def test_fixed_narrative_reservation_and_config_split_do_not_install(self):
        a = reserve.allocate(DATA, REQUEST)
        self.assertIsInstance(a, dict)
        slots = {s['name']: s for s in a['assignments']}
        self.assertEqual((slots['narrative.spawn_table']['start'], slots['narrative.spawn_table']['capacity']), (0x023D7240, 540))
        self.assertEqual(slots['narrative.spawn_table']['start'] % 4, 0)
        self.assertEqual((slots['settings.descriptor']['start'], slots['settings.descriptor']['capacity']), (0x023CB1A0, 80))
        self.assertEqual((slots['settings.generation']['start'], slots['settings.generation']['capacity']), (0x023CB1F0, 16))
        self.assertTrue(a['address_reserved'])
        self.assertFalse(a['installed'])
        self.assertFalse(a['installation_authorized'])
        self.assertEqual(reserve.allocate(DATA, {'narrative.spawn_table': 4})['assignments'][0]['start'], 0x023D7240)

    def test_numeric_types_and_unknown_duplicate_payloads_refused(self):
        class Duplicates(dict):
            def items(self):
                return [('training.ui', 4), ('training.ui', 4)]
        for requests in ({'training.ui': -1}, {'training.ui': 0}, {'training.ui': True},
                         {'training.ui': 1.0}, {'training.ui': '4'}, {'training.ui': 2**32},
                         {'unknown': 4}, Duplicates(), []):
            with self.subTest(requests=requests), self.assertRaises(ValueError):
                reserve.allocate(DATA, requests)

    def test_forged_partial_allocation_and_foreign_input_refused(self):
        allocation = reserve.allocate(DATA, REQUEST)
        self.assertIsInstance(allocation, dict)
        for key in ('input_sha256', 'policy_sha256', 'assignments', 'requested'):
            forged = copy.deepcopy(allocation); del forged[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                reserve.apply(DATA, forged)
        forged = copy.deepcopy(allocation); forged['assignments'][0]['start'] += 4
        with self.assertRaises(ValueError): reserve.apply(DATA, forged)
        forged = copy.deepcopy(allocation); forged['address_reserved'] = not allocation['address_reserved']
        with self.assertRaises(ValueError): reserve.apply(DATA, forged)
        with self.assertRaisesRegex(ValueError, 'exact supported'):
            reserve.apply(DATA + b'foreign', allocation)

    def test_policy_rejects_retirement_wrong_donor_and_incomplete_coverage(self):
        for change in ('retirement', 'donor', 'root', 'gap', 'overlap', 'duplicate', 'bool', 'wrapped', 'reorder'):
            p = policy()
            if change == 'retirement': p['roots'][6]['owner'] = 'successor'
            elif change == 'donor': p['subdivisions'][1]['parent'] = 'plus-ui.extended'
            elif change == 'root': p['base'] -= 4
            elif change == 'gap': p['roots'][0]['bytes'] -= 4
            elif change == 'overlap': p['subdivisions'][1]['parts'][1]['start'] -= 4
            elif change == 'duplicate': p['subdivisions'][1]['parts'][2]['name'] = 'training.ui'
            elif change == 'bool': p['subdivisions'][0]['parts'][2]['bytes'] = True
            elif change == 'wrapped': p['subdivisions'][1]['parts'][0]['bytes'] = 2**32
            else: p['roots'].reverse()
            with self.subTest(change=change), self.assertRaises(ValueError): reserve.validate_policy(p)

    def test_malformed_metadata_and_duplicate_overlay_ids_refused(self):
        for change in ('bss_type', 'wrapped', 'duplicate', 'file_id', 'reserve_size', 'static_bss'):
            self.meta = metadata()
            if change == 'bss_type': self.meta['overlays'][0]['bss'] = True
            elif change == 'wrapped': self.meta['overlays'][0]['start'] = 2**32 - 4
            elif change == 'duplicate': self.meta['overlays'][1]['id'] = 0
            elif change == 'file_id': self.meta['overlays'][1]['file_id'] = 0
            elif change == 'reserve_size': self.meta['sections'][-1]['bytes'] -= 4
            else: self.meta['sections'][0]['bss'] -= 4
            if change == 'wrapped': self.meta['overlays'][0]['bss'] = 16
            with self.subTest(change=change), self.assertRaises(ValueError): reserve.audit(DATA)

    def assert_schema_refused(self, operation):
        try:
            operation()
        except Exception as error:
            self.assertIsInstance(error, ValueError, 'schema rejection must be an intentional ValueError')
        else:
            self.fail('malformed schema was admitted')

    def test_malformed_policy_and_metadata_types_fail_closed(self):
        for key, value in (('extra', 1), ('subdivisions', [{'parent': {}, 'parts': []}, {}])):
            p = policy(); p[key] = value
            with self.subTest(key=key): self.assert_schema_refused(lambda: reserve.validate_policy(p))
        for change in ('guard_map', 'missing', 'preserve_bool', 'extra'):
            self.meta = metadata()
            if change == 'guard_map': self.meta['guard_sha256'] = []
            elif change == 'missing': del self.meta['sections']
            elif change == 'preserve_bool': self.meta['preservation']['arm7_overlay_bytes'] = False
            else: self.meta['unexpected'] = 1
            with self.subTest(change=change): self.assert_schema_refused(lambda: reserve.audit(DATA))

    def test_duplicate_policy_fields_and_non_json_forgery_refused(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            reserve._read_json('{"schema":1,"schema":1}')
        allocation = reserve.allocate(DATA, REQUEST)
        self.assertIsInstance(allocation, dict)
        allocation['unexpected'] = {object()}
        self.assert_schema_refused(lambda: reserve.apply(DATA, allocation))

    def test_overlay_must_remain_in_native_pre_arena_ram_and_record_shapes_exact(self):
        for change in ('above_ram', 'static_alias', 'end_wrap', 'overlay_extra', 'static_extra'):
            self.meta = metadata()
            if change == 'above_ram': self.meta['overlays'][0]['start'] = 0x02400000
            elif change == 'static_alias': self.meta['overlays'][0]['start'] = 0x02000000
            elif change == 'end_wrap': self.meta['overlays'][0]['start'] = 0xFFFFFFFC
            elif change == 'overlay_extra': self.meta['overlays'][0]['extra'] = 1
            else: self.meta['sections'][0]['extra'] = 1
            with self.subTest(change=change): self.assert_schema_refused(lambda: reserve.audit(DATA))

    def test_submitted_legacy_owners_require_exact_integer_spans_and_record_shapes(self):
        class Owner(dict):
            pass
        for change in ('bytes_float', 'start_float', 'record_subclass', 'extra_field'):
            p = policy()
            if change == 'bytes_float': p['legacy_owners'][0]['bytes'] = float(p['legacy_owners'][0]['bytes'])
            elif change == 'start_float': p['legacy_owners'][0]['start'] = float(p['legacy_owners'][0]['start'])
            elif change == 'record_subclass': p['legacy_owners'][0] = Owner(p['legacy_owners'][0])
            else: p['legacy_owners'][0]['extra'] = 1
            with self.subTest(change=change): self.assert_schema_refused(lambda: reserve.validate_policy(p))
        self.assertIsNone(reserve.validate_policy(policy()))

    def test_allocation_tree_rejects_tuple_and_nested_non_builtin_json_shapes(self):
        class Record(dict):
            pass
        class Records(list):
            pass
        class Name(str):
            pass
        class Number(int):
            pass
        for change in ('assignments_tuple', 'nested_record', 'list_subclass', 'nested_map',
                       'string_subclass', 'integer_subclass', 'nested_tuple', 'cycle'):
            allocation = reserve.allocate(DATA, REQUEST)
            if change == 'assignments_tuple': allocation['assignments'] = tuple(allocation['assignments'])
            elif change == 'nested_record': allocation['assignments'][0] = Record(allocation['assignments'][0])
            elif change == 'list_subclass': allocation['assignments'] = Records(allocation['assignments'])
            elif change == 'nested_map': allocation['preservation'] = Record(allocation['preservation'])
            elif change == 'string_subclass': allocation['assignments'][0]['name'] = Name(allocation['assignments'][0]['name'])
            elif change == 'integer_subclass': allocation['assignments'][0]['capacity'] = Number(allocation['assignments'][0]['capacity'])
            elif change == 'nested_tuple': allocation['assignments'][0]['name'] = (allocation['assignments'][0]['name'],)
            else: allocation['assignments'].append(allocation['assignments'])
            with self.subTest(change=change): self.assert_schema_refused(lambda: reserve.apply(DATA, allocation))

    def test_retained_b3_code_headroom_and_capacity_boundaries(self):
        a = reserve.allocate(DATA, REQUEST)
        slots = {slot['name']: slot for slot in a['assignments']}
        self.assertEqual(a['policy_version'], 'sgp131-resident-12')
        self.assertTrue(a['address_reserved'])
        self.assertEqual((slots['training.ui']['start'], slots['training.ui']['bytes'], slots['training.ui']['capacity']),
                         (0x023D6800, 1360, 1536))
        self.assertEqual((slots['physical.code']['start'], slots['physical.code']['bytes'], slots['physical.code']['capacity']),
                         (0x023D6E10, 904, 1024))
        self.assertEqual((slots['physical.slot']['start'], slots['physical.slot']['capacity']), (0x023D7210, 48))
        after, receipt = reserve.apply(DATA, a)
        self.assertEqual(after, DATA)
        self.assertTrue(receipt['address_reserved'])
        self.assertFalse(receipt['installed'])
        self.assertFalse(receipt['installation_authorized'])
        for name, capacity in (('training.ui', 1536), ('physical.code', 1024)):
            self.assertEqual(reserve.allocate(DATA, {name: capacity})['assignments'][0]['bytes'], capacity)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'capacity|overflow'):
                reserve.allocate(DATA, {name: capacity + 1})

    def test_resident1_policy_and_receipts_and_old_addresses_refused(self):
        old = policy()
        old['version'], old['status'] = 'sgp131-resident-1', 'proposed'
        old_layout = (
            ('training.ui', 0x023D6800, 1360, 'payload'),
            ('training.ui.guard', 0x023D6D50, 16, 'guard'),
            ('physical.code', 0x023D6D60, 904, 'payload'),
            ('physical.slot', 0x023D70E8, 48, 'payload'),
            ('narrative.spawn_table', 0x023D7118, 540, 'payload'),
            ('successor.guard', 0x023D7334, 16, 'guard'),
            ('training.extension.unassigned', 0x023D7344, 444, 'unassigned'))
        old['subdivisions'][1]['parts'] = [dict(zip(('name', 'start', 'bytes', 'kind'), row)) for row in old_layout]
        self.assert_schema_refused(lambda: reserve.validate_policy(old))
        allocation = reserve.allocate(DATA, REQUEST)
        legacy = copy.deepcopy(allocation)
        legacy['policy_version'] = 'sgp131-resident-1'
        legacy['policy_sha256'] = 'e8b7331c44ea34d84c4642c935c83ff5fd41e8d7add14e607cc673d85501ae87'
        legacy['address_reserved'] = False
        old_slots = {name: (start, size) for name, start, size, kind in old_layout if kind == 'payload'}
        for row in legacy['assignments']:
            if row['name'] in old_slots:
                row['start'], row['capacity'] = old_slots[row['name']]
        self.assert_schema_refused(lambda: reserve.apply(DATA, legacy))
        forged = copy.deepcopy(allocation)
        next(row for row in forged['assignments'] if row['name'] == 'narrative.spawn_table')['start'] = 0x023D7118
        self.assert_schema_refused(lambda: reserve.apply(DATA, forged))

    def test_resident2_guards_remainder_and_config_remain_protected(self):
        p = policy()
        parts = p['subdivisions'][1]['parts']
        self.assertEqual([(row['start'], row['bytes']) for row in parts if row['kind'] != 'payload'],
                         [(0x023D6E00, 16), (0x023D745C, 16)])
        self.assertEqual(next(row for row in parts if row['name'] == 'fairy-ai.code'),
                         {'name': 'fairy-ai.code', 'start': 0x023D746C,
                          'bytes': 148, 'kind': 'payload'})
        self.assertEqual(sum(row['bytes'] for row in parts), 3328)
        self.assertEqual(p['status'], 'reserved')
        self.assertFalse(p['dynamic54']['address_reserved'])
        for name in ('training.ui.guard', 'successor.guard', 'shiny.abi2.retained', 'shiny.abi2.gap'):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'payload|owner|assign'):
                reserve.allocate(DATA, {name: 4})
        self.assertEqual(reserve.allocate(DATA, {'fairy-ai.code': 148})['assignments'][0],
                         {'name': 'fairy-ai.code', 'parent': 'training.extension',
                          'start': 0x023D746C, 'bytes': 148, 'capacity': 148})


    def test_reconciled_suffix_keeps_ability_within_guide_and_legacy_untouched(self):
        p = policy()
        leaves = {x['name']: x for e in p['subdivisions'] for x in e['parts']}
        self.assertEqual(leaves['modern-accuracy.code'],
                         {'name': 'modern-accuracy.code', 'start': 0x023D5AA0,
                          'bytes': 32, 'kind': 'payload'})
        self.assertEqual(leaves['field-guide.code.preserved']['bytes'], 1344)
        self.assertNotIn('legacy.1.2', {e['parent'] for e in p['subdivisions']})
        self.assertNotIn('modern-accuracy.guard', leaves)
        self.assertEqual(next(x for x in p['legacy_owners']
                              if x['name'] == 'sgp.soul_dew'),
                         {'name': 'sgp.soul_dew', 'start': 0x023DEB00,
                          'bytes': 32,
                          'owner': 'Sacred Gold Plus 1.3.1 — Soul Dew custom-rule mask'})
        self.assertEqual(next(x for x in p['legacy_owners']
                              if x['name'] == 'sgp.wonder_card'),
                         {'name': 'sgp.wonder_card', 'start': 0x023DEB20,
                          'bytes': 32,
                          'owner': 'Sacred Gold Plus 1.3.1 — Wonder Card decoration guard'})
        self.assertEqual(next(x for x in p['legacy_owners']
                              if x['name'] == 'sgp.gb_sounds_evolution'),
                         {'name': 'sgp.gb_sounds_evolution', 'start': 0x023D8AA8,
                          'bytes': 32,
                          'owner': 'Sacred Gold Plus 1.3.1 — GB evolution audio reload'})
        self.assertEqual(next(x for x in p['legacy_owners']
                              if x['name'] == 'sgp.pokegear_autocull'),
                         {'name': 'sgp.pokegear_autocull', 'start': 0x023D8AC8,
                          'bytes': 36,
                          'owner': 'Sacred Gold Plus 1.3.1 — Pokégear signed marker culling'})
        self.assertEqual(next(x for x in p['legacy_owners']
                              if x['name'] == 'sgp.waterfall_facing'),
                         {'name': 'sgp.waterfall_facing', 'start': 0x023D8AEC,
                          'bytes': 20,
                          'owner': 'Sacred Gold Plus 1.3.1 — Waterfall descent facing'})
        self.assertNotIn('libero.1.2',
                         {x['name'] for x in p['legacy_owners']})
        self.assertNotIn('libero.1.2.finale',
                         {x['name'] for x in p['legacy_owners']})
        with self.assertRaisesRegex(ValueError, 'conditional.*installer'):
            reserve.allocate(DATA, {'modern-accuracy.code': 32})

    def test_reconciled_suffix_slot_mutations_and_guard_borrowing_refused(self):
        for name in ('summary-controls.runtime', 'portable-box.runtime',
                     'c8.module-stubs', 'modern-accuracy.code'):
            for mutation in ('move_back', 'grow', 'wrong_kind', 'rename', 'coherent_boundary'):
                p = policy()
                parts = next(e for e in p['subdivisions']
                             if e['parent'] == 'field-guide.code')['parts']
                i = next(i for i, x in enumerate(parts) if x['name'] == name)
                slot = parts[i]
                if mutation == 'move_back': slot['start'] -= 16
                elif mutation == 'grow': slot['bytes'] += 16
                elif mutation == 'wrong_kind': slot['kind'] = 'retained'
                elif mutation == 'rename': slot['name'] = 'other.runtime'
                else:
                    slot['bytes'] += 16
                    parts[i + 1]['start'] += 16
                    parts[i + 1]['bytes'] -= 16
                with self.subTest(slot=name, mutation=mutation):
                    self.assert_schema_refused(lambda: reserve.validate_policy(p))

    def test_resident5_or_c8_only_layout_cannot_masquerade_as_reconciled_policy(self):
        p = policy()
        p['version'] = 'sgp131-resident-5'
        self.assert_schema_refused(lambda: reserve.validate_policy(p))
        p = policy()
        parts = next(e for e in p['subdivisions'] if e['parent'] == 'field-guide.code')['parts']
        parts[-2:] = [{'name': 'field-guide.code.preserved', 'start': 0x023D5AA0,
                       'bytes': 1376, 'kind': 'preserved'}]
        self.assert_schema_refused(lambda: reserve.validate_policy(p))
        allocation = reserve.allocate(DATA, REQUEST)
        allocation['policy_version'] = 'sgp131-resident-5'
        self.assert_schema_refused(lambda: reserve.apply(DATA, allocation))

    def test_c8_guide_suffix_cession_is_metadata_only_and_fails_closed(self):
        # CONDITIONAL (memory-c8): literali indipendenti, non derivati da reserve.py.
        p = policy()
        entry = next(e for e in p['subdivisions'] if e['parent'] == 'field-guide.code')
        got = [(x['name'], x['start'], x['bytes'], x['kind']) for x in entry['parts']]
        self.assertEqual(got[2:], [('summary-controls.runtime', 37571600, 512, 'payload'), ('portable-box.runtime', 37572112, 3024, 'payload'), ('c8.module-stubs', 37575136, 192, 'payload'), ('modern-accuracy.code', 37575328, 32, 'payload'), ('field-guide.code.preserved', 37575360, 1344, 'preserved')])
        self.assertEqual(sum(b for _, _, b, _ in got), 8192)
        self.assertEqual(got[2][1] + 5104, 0x023D6000)
        for name, start, size, kind in got[2:]:
            self.assertEqual(start % 16, 0)
            self.assertEqual(size % 16, 0)
        self.assertEqual(got[-1][3], 'preserved')
        for name, _, size, _ in got[2:2 + 4]:
            with self.assertRaisesRegex(ValueError, 'conditional|separately reviewed'):
                reserve.allocate(DATA, {name: size})
        for flag in ('retired', 'installed', 'authorized'):
            q = policy()
            next(e for e in q['subdivisions'] if e['parent'] == 'field-guide.code')[flag] = True
            self.assert_schema_refused(lambda: reserve.validate_policy(q))

    def test_b5_conditional_metadata_covers_only_the_four_complete_parents(self):
        p = policy()
        self.assertEqual(p['version'], 'sgp131-resident-12')
        self.assertIsNone(reserve.validate_policy(p))
        conditional = {e['parent']: e for e in p['subdivisions'] if 'requires' in e}
        self.assertEqual(set(conditional), set(B5_PARTS))
        for parent, expected in B5_PARTS.items():
            with self.subTest(parent=parent):
                entry = conditional[parent]
                self.assertEqual(tuple((x['name'], x['start'], x['bytes'], x['kind'])
                                       for x in entry['parts']), expected)
                self.assertTrue(entry['requires'])
        self.assertEqual(sum(x[2] for x in B5_PARTS['field-guide.config-state']), 1024)
        result = reserve.audit(DATA)
        self.assertEqual(result['conditional_reservations'], list(conditional.values()))
        self.assertTrue(result['address_reserved'])
        self.assertFalse(result['installed'])
        self.assertFalse(result['installation_authorized'])
        # Legacy snapshots and the B3 narrative slot retain their old contracts.
        self.assertEqual(reserve.allocate(DATA, {'narrative.spawn_table': 540})['assignments'][0],
                         {'name': 'narrative.spawn_table', 'parent': 'training.extension',
                          'start': 0x023D7240, 'bytes': 540, 'capacity': 540})

    def test_b5_payload_requests_fail_closed_including_forged_apply_receipts(self):
        for parts in B5_PARTS.values():
            for name, start, capacity, kind in parts:
                with self.subTest(name=name):
                    if kind == 'payload':
                        for size in (1, capacity, capacity + 1):
                            verified_children = {'summary-controls.runtime', 'portable-box.runtime',
                                                 'c8.module-stubs', 'modern-accuracy.code'}
                            refusal = ('payload capacity overflow' if name in verified_children and size > capacity
                                       else 'conditional.*installer')
                            with self.assertRaisesRegex(ValueError, refusal):
                                reserve.allocate(DATA, {**REQUEST, name: size})
                    else:
                        with self.assertRaisesRegex(ValueError, 'payload|owner|assign'):
                            reserve.allocate(DATA, {name: 4})
        a = reserve.allocate(DATA, REQUEST)
        for parts in B5_PARTS.values():
            for name, start, capacity, kind in parts:
                if kind != 'payload':
                    continue
                forged = copy.deepcopy(a)
                forged['requested'][name] = capacity
                # Self-reported runtime flags cannot unlock a conditional owner.
                forged['retired'] = True
                forged['old54_replaced'] = True
                forged['incoming_edges_verified'] = True
                with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'conditional.*installer'):
                    reserve.apply(DATA, forged)

    def test_b6_fixture_admits_only_the_new_version_and_fieldbook_partition(self):
        old = b6_policy()
        old['version'] = 'sgp131-resident-10'
        with self.assertRaisesRegex(ValueError, 'policy status'):
            reserve.validate_policy(old)
        self.assertIsNone(reserve.validate_policy(b6_policy()))

    def test_b6_fieldbook_partition_covers_exactly_the_unchanged_old_guide_parent(self):
        p = policy()
        root = next(r for r in p['roots'] if r['name'] == 'field-guide.code')
        self.assertEqual((root['start'], root['bytes']), (0x023D4000, 8192))
        entry = next(e for e in p['subdivisions'] if e['parent'] == 'field-guide.code')
        parts = entry['parts']
        self.assertEqual(parts, next(e for e in b6_policy()['subdivisions']
                                     if e['parent'] == 'field-guide.code')['parts'])
        # Hand-derived half-open bounds prove no gap/overlap or suffix borrowing.
        self.assertEqual([(x['start'], x['start'] + x['bytes']) for x in parts],
                         [(0x023D4000, 0x023D4C00), (0x023D4C00, 0x023D4C10),
                          (0x023D4C10, 0x023D4E10), (0x023D4E10, 0x023D59E0), (0x023D59E0, 0x023D5AA0), (0x023D5AA0, 0x023D5AC0), (0x023D5AC0, 0x023D6000)])
        self.assertEqual(sum(x['bytes'] for x in parts), 8192)
        self.assertEqual({address for x in parts for address in range(x['start'], x['start'] + x['bytes'])},
                         set(range(0x023D4000, 0x023D6000)))
        self.assertEqual(p['conditional_images'][0]['bytes'], 12272)
        self.assertIn((0x023D4000, 8192), [(g['start'], g['bytes']) for g in p['guards']])

    def test_b6_old_b5_policy_layout_and_receipts_cannot_gain_authority(self):
        for version in ('sgp131-resident-4', 'sgp131-resident-5', 'sgp131-resident-6'):
            old = policy()
            old['version'] = version
            entry = next(e for e in old['subdivisions'] if e['parent'] == 'field-guide.code')
            entry['parts'] = [
                {'name': 'fieldbook.code', 'start': 0x023D4000, 'bytes': 2560, 'kind': 'payload'},
                {'name': 'fieldbook.guard', 'start': 0x023D4A00, 'bytes': 16, 'kind': 'guard'},
                {'name': 'field-guide.code.preserved', 'start': 0x023D4A10, 'bytes': 5616, 'kind': 'preserved'}]
            with self.subTest(version=version):
                self.assert_schema_refused(lambda: reserve.validate_policy(old))
            entry['retired'] = entry['incoming_edges_verified'] = True
            with self.subTest(version=version, flags=True):
                self.assert_schema_refused(lambda: reserve.validate_policy(old))
        old = b6_policy()
        old['version'] = 'sgp131-resident-4'
        self.assert_schema_refused(lambda: reserve.validate_policy(old))
        a = reserve.allocate(DATA, REQUEST)
        a['policy_version'] = 'sgp131-resident-4'
        self.assert_schema_refused(lambda: reserve.apply(DATA, a))

    def test_b6_fieldbook_capacity_and_obsolete_guard_mutants_are_refused(self):
        for change in ('unmatched_capacity', 'old_guard', 'old_payload_suffix',
                       'guard_overlap', 'suffix_shrink', 'coherent_capacity_3076'):
            p = b6_policy()
            code, guard, *_, suffix = next(e for e in p['subdivisions']
                                           if e['parent'] == 'field-guide.code')['parts']
            if change == 'unmatched_capacity': code['bytes'] = 3076
            elif change == 'old_guard':
                code['bytes'] = 2560
                guard['start'] = 0x023D4A00
                suffix.update(start=0x023D4A10, bytes=5616)
            elif change == 'old_payload_suffix':
                code['bytes'] = 2560
                guard.update(start=0x023D4A00, kind='payload')
                suffix.update(start=0x023D4A10, bytes=5616, kind='payload')
            elif change == 'guard_overlap': guard['start'] = 0x023D4BFC
            elif change == 'suffix_shrink': suffix['bytes'] = 5100
            else:
                code['bytes'] = 3076
                guard['start'] = 0x023D4C04
                suffix.update(start=0x023D4C14, bytes=5100)
            with self.subTest(change=change):
                self.assert_schema_refused(lambda: reserve.validate_policy(p))

    def test_b5_policy_rejects_partial_retirement_and_forged_proof_flags(self):
        for parent in B5_PARTS:
            for change in ('missing', 'duplicate', 'condition_missing', 'condition_bool',
                           'condition_partial', 'condition_extra', 'self_reported', 'fallback'):
                p = policy()
                entry = next((e for e in p['subdivisions'] if e['parent'] == parent), None)
                self.assertIsNotNone(entry, 'B5 parent must be present before mutation')
                if change == 'missing': p['subdivisions'].remove(entry)
                elif change == 'duplicate': p['subdivisions'].append(copy.deepcopy(entry))
                elif change == 'condition_missing': del entry['requires']
                elif change == 'condition_bool': entry['requires'] = True
                elif change == 'condition_partial': entry['requires'].pop()
                elif change == 'condition_extra': entry['requires'].append('pointer-scan-only')
                elif change == 'self_reported': entry['retired'] = True
                else: entry['old54_fallback'] = True
                with self.subTest(parent=parent, change=change):
                    self.assert_schema_refused(lambda: reserve.validate_policy(p))

    def test_b5_policy_rejects_partition_alias_gap_overlap_and_guard_borrowing(self):
        for parent in B5_PARTS:
            for change in ('gap', 'overlap', 'kind', 'name', 'bool', 'float', 'bss', 'extra'):
                p = policy()
                e = next((e for e in p['subdivisions'] if e['parent'] == parent), None)
                self.assertIsNotNone(e, 'B5 parent must be present before mutation')
                part = e['parts'][0]
                if change == 'gap': part['bytes'] -= 4
                elif change == 'overlap': part['bytes'] += 4
                elif change == 'kind': part['kind'] = 'payload' if part['kind'] == 'retained' else 'retained'
                elif change == 'name': part['name'] = 'training.ui'
                elif change == 'bool': part['bytes'] = True
                elif change == 'float': part['start'] = float(part['start'])
                elif change == 'bss': part['bss'] = 0
                else: part['extra'] = 1
                with self.subTest(parent=parent, change=change):
                    self.assert_schema_refused(lambda: reserve.validate_policy(p))
        for victim in ('ui.bridge.guard', 'fieldbook.guard', 'field-guide.code.preserved', 'ui.bootstrap.guard',
                       'guide.labels.retained', 'guide.field-state.retained', 'guide.canary.retained'):
            p = policy()
            part = next((x for e in p['subdivisions'] for x in e['parts'] if x['name'] == victim), None)
            self.assertIsNotNone(part, 'protected B5 leaf must exist before mutation')
            part['kind'] = 'payload'
            with self.subTest(victim=victim):
                self.assert_schema_refused(lambda: reserve.validate_policy(p))

    def test_b5_complete_native_parent_preimages_are_mandatory(self):
        p = policy()
        guards = {(g['start'], g['bytes']): g for g in p['guards']}
        for address, size in ((0x023CB800, 8192), (0x023D4000, 8192), (0x023CD800, 4096), (0x023D7B00, 1024)):
            self.assertIn((address, size), guards)
            changed = copy.deepcopy(p)
            changed['guards'].remove(guards[address, size])
            with self.subTest(address=hex(address)):
                self.assert_schema_refused(lambda: reserve.validate_policy(changed))
                self.meta = metadata()
                self.meta['guard_sha256'][str(address)] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'guard|preimage'):
                    reserve.audit(DATA)

    def test_resident2_policy_and_receipts_cannot_masquerade_as_b5(self):
        old = policy()
        old['version'] = 'sgp131-resident-2'
        self.assert_schema_refused(lambda: reserve.validate_policy(old))
        a = reserve.allocate(DATA, REQUEST)
        a['policy_version'] = 'sgp131-resident-2'
        self.assert_schema_refused(lambda: reserve.apply(DATA, a))


    def test_b5_contiguous_image_reports_one_authored_span_and_protects_xstate(self):
        p = policy()
        self.assertIn('conditional_images', p, 'one authored Bridge image must be explicit')
        self.assertEqual(p['conditional_images'], [
            {'name': 'ui.bridge', 'start': 0x023CB800, 'bytes': 12272,
             'parts': ['ui.bridge.code', 'ui.bridge.tail'], 'guard': 'ui.bridge.guard'}])
        leaves = {x['name']: x for e in p['subdivisions'] for x in e['parts']}
        self.assertEqual(leaves['ui.bridge.code']['start'] + leaves['ui.bridge.code']['bytes'],
                         leaves['ui.bridge.tail']['start'])
        self.assertEqual(leaves['ui.bridge.tail']['start'] + leaves['ui.bridge.tail']['bytes'], 0x023CE7F0)
        self.assertEqual(leaves['ui.bridge.guard']['start'] + leaves['ui.bridge.guard']['bytes'], 0x023CE800)
        state = next(r for r in p['roots'] if r['name'] == 'plus-ui.shiny-state')
        self.assertEqual((state['start'], state['bytes']), (0x023CE800, 256))
        result = reserve.audit(DATA)
        self.assertEqual(result['conditional_images'], p['conditional_images'])
        # Same complete Options replacement conditions apply to BOTH donors.
        donors = {e['parent']: e for e in p['subdivisions'] if 'requires' in e}
        self.assertEqual(donors['plus-ui.extended']['requires'], donors['plus-ui.shiny-text']['requires'])
        self.assertIn('old-navigation-dispatch-entry-paths-excluded', donors['plus-ui.extended']['requires'])

    def test_b5_contiguous_image_schema_and_partition_mutants_refused(self):
        for change in ('missing', 'empty', 'duplicate', 'bool_start', 'float_size', 'extra',
                       'old_base', 'too_large', 'part_gap', 'part_guard', 'part_order', 'wrong_guard'):
            p = policy()
            self.assertIn('conditional_images', p)
            image = p['conditional_images'][0]
            if change == 'missing': del p['conditional_images']
            elif change == 'empty': p['conditional_images'] = []
            elif change == 'duplicate': p['conditional_images'].append(copy.deepcopy(image))
            elif change == 'bool_start': image['start'] = True
            elif change == 'float_size': image['bytes'] = 12272.0
            elif change == 'extra': image['retired'] = True
            elif change == 'old_base': image['start'] = 0x023D4000
            elif change == 'too_large': image['bytes'] = 12288
            elif change == 'part_gap': image['parts'] = ['ui.bridge.code']
            elif change == 'part_guard': image['parts'].append('ui.bridge.guard')
            elif change == 'part_order': image['parts'].reverse()
            else: image['guard'] = 'fieldbook.guard'
            with self.subTest(change=change):
                self.assert_schema_refused(lambda: reserve.validate_policy(p))
        for change in ('tail_gap', 'tail_overlap', 'tail_wrong_end', 'guard_borrow', 'xstate_overlap',
                       'fieldbook_old_address', 'fieldbook_suffix_capacity'):
            p = policy()
            leaves = {x['name']: x for e in p['subdivisions'] for x in e['parts']}
            self.assertIn('ui.bridge.tail', leaves)
            if change == 'tail_gap': leaves['ui.bridge.tail']['start'] += 4
            elif change == 'tail_overlap': leaves['ui.bridge.tail']['start'] -= 4
            elif change == 'tail_wrong_end': leaves['ui.bridge.tail']['bytes'] -= 4
            elif change == 'guard_borrow':
                leaves['ui.bridge.tail']['bytes'] += 4
                leaves['ui.bridge.guard']['start'] += 4
                leaves['ui.bridge.guard']['bytes'] -= 4
            elif change == 'xstate_overlap': leaves['ui.bridge.tail']['bytes'] = 4352
            elif change == 'fieldbook_old_address': leaves['fieldbook.code']['start'] = 0x023CD800
            else:
                leaves['fieldbook.code']['bytes'] += 4
                leaves['fieldbook.guard']['start'] += 4
                leaves['field-guide.code.preserved']['start'] += 4
                leaves['field-guide.code.preserved']['bytes'] -= 4
            with self.subTest(change=change):
                self.assert_schema_refused(lambda: reserve.validate_policy(p))

    def test_b5_old_v3_policy_and_receipts_refused(self):
        old = policy()
        old['version'] = 'sgp131-resident-3'
        self.assert_schema_refused(lambda: reserve.validate_policy(old))
        a = reserve.allocate(DATA, REQUEST)
        a['policy_version'] = 'sgp131-resident-3'
        self.assert_schema_refused(lambda: reserve.apply(DATA, a))
