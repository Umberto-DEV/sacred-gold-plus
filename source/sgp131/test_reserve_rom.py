"""Class B: exact canonical V4 resident audit/readback and RAM-only mutants.

SGP131_BASE_EN/IT identify originals; SGP_RESERVE_REQUIRE_INPUTS=1 makes missing
inputs fail. Nothing is extracted or written. The identity bypass in targeted
mutants is an explicit test-only seam to exercise diagnostics behind full pins.
"""
import hashlib
import json
import os
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from . import baseline, reserve
from sgp12.rom import valida_layout_arm9

REQUEST = {'training.ui': 1360, 'physical.code': 904, 'physical.slot': 48,
           'narrative.spawn_table': 540, 'settings.descriptor': 80, 'settings.generation': 16}


def _hash_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def _offset(data, address):
    off, _, ram, size = struct.unpack_from('<4I', data, 0x20)
    _t0, _t1, _d0, _rows, segments = valida_layout_arm9(data, off, ram, size)
    for start, position, length in segments:
        if start <= address < start + length:
            return position + address - start
    raise AssertionError('targeted guard must be in initialized ARM9')


class RealReserveTests(unittest.TestCase):
    def _input(self, language):
        key = 'SGP131_BASE_' + language
        value = os.environ.get(key)
        if not value:
            message = key + ' required for readonly V4 resident audit'
            if os.environ.get('SGP_RESERVE_REQUIRE_INPUTS') == '1':
                self.fail(message)
            self.skipTest(message + '; SGP_RESERVE_REQUIRE_INPUTS=1 forbids this skip')
        path = Path(value)
        self.assertTrue(path.is_file(), key + ' must identify an existing original')
        before = _hash_file(path)
        data = path.read_bytes()
        self.assertEqual(baseline.identify(data), language)
        self.assertEqual(hashlib.sha256(data).hexdigest(), before)
        self.addCleanup(lambda: self.assertEqual(_hash_file(path), before, 'original changed'))
        return data

    def _audit_and_apply(self, language):
        data = self._input(language)
        report = reserve.audit(data)
        allocation = reserve.allocate(data, REQUEST)
        after, receipt = reserve.apply(data, allocation)
        self.assertEqual(after, data)
        readback = reserve.audit(after)
        self.assertEqual(hashlib.sha256(after).hexdigest(), {
            'EN': '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
            'IT': '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'}[language])
        self.assertEqual(readback['overlays'], report['overlays'])
        self.assertEqual([x['id'] for x in readback['overlays']], list(range(129)))
        self.assertEqual(readback['preservation'], report['preservation'])
        self.assertEqual(readback['owner_sha256'], report['owner_sha256'])
        old_guide_hash = '2f19c042588a613ab26cca40609909a4b7620d3b9fdfed412599dcad5813556e'
        self.assertEqual(readback['guard_sha256'][str(0x023D4000)], old_guide_hash)
        self.assertEqual(readback['owner_sha256']['field-guide.code'], old_guide_hash)
        self.assertEqual(report['overlay_count'], 129)
        self.assertEqual(report['preservation']['file_count'], 513)
        self.assertEqual(report['preservation']['arm7_sha256'], '746355ed51b324933542a7c4fcf109a5f83755a97c95b834ffd08caf6d4fafea')
        self.assertEqual(report['arena'], reserve.ARENA)
        self.assertEqual(report['owned_bytes'], 98304)
        self.assertEqual(report['free_bytes'], 0)
        self.assertEqual({e['parent'] for e in report['conditional_reservations']},
                         {'plus-ui.extended', 'field-guide.code', 'plus-ui.shiny-text', 'field-guide.config-state'})
        for name in ('ui.bridge.code', 'ui.bridge.tail', 'fieldbook.code', 'guide.template', 'ui.bootstrap',
                     'ui.control', 'ui.module.seed', 'ui.resource.seed', 'ui.guide.seed'):
            with self.subTest(conditional=name), self.assertRaisesRegex(ValueError, 'conditional.*installer'):
                reserve.allocate(data, {name: 4})
        self.assertIn('conditional_images', report)
        self.assertEqual(report['conditional_images'], [
            {'name': 'ui.bridge', 'start': 0x023CB800, 'bytes': 12272,
             'parts': ['ui.bridge.code', 'ui.bridge.tail'], 'guard': 'ui.bridge.guard'}])
        guide = next(e for e in report['conditional_reservations'] if e['parent'] == 'field-guide.code')
        self.assertEqual([(x['name'], x['start'], x['bytes'], x['kind']) for x in guide['parts']], [
            ('fieldbook.code', 0x023D4000, 3072, 'payload'),
            ('fieldbook.guard', 0x023D4C00, 16, 'guard'),
            ('summary-controls.runtime', 0x023D4C10, 512, 'payload'),
            ('portable-box.runtime', 0x023D4E10, 3024, 'payload'),
            ('c8.module-stubs', 0x023D59E0, 192, 'payload'),
            ('modern-accuracy.code', 0x023D5AA0, 32, 'payload'),
            ('field-guide.code.preserved', 0x023D5AC0, 1344, 'preserved')])
        self.assertTrue(allocation['address_reserved'])
        self.assertEqual(allocation['policy_version'], 'sgp131-resident-12')
        slots = {slot['name']: slot for slot in allocation['assignments']}
        self.assertEqual(slots['training.ui']['capacity'], 1536)
        self.assertEqual((slots['physical.code']['start'], slots['physical.code']['capacity']), (0x023D6E10, 1024))
        self.assertEqual((slots['physical.slot']['start'], slots['narrative.spawn_table']['start']), (0x023D7210, 0x023D7240))
        self.assertFalse(receipt['installed'])
        self.assertFalse(receipt['installation_authorized'])
        self.assertEqual(receipt['preservation'], report['preservation'])
        print(json.dumps({'language': language, 'input_sha256': report['input_sha256'],
                          'policy_sha256': report['policy_sha256'], 'policy_version': report['policy_version'],
                          'address_reserved': allocation['address_reserved'], 'assignments': allocation['assignments'],
                          'sections': report['sections'],
                          'preservation': report['preservation'], 'arena': report['arena'],
                          'guard_sha256': report['guard_sha256'], 'overlay_count': 129,
                          'legacy_owner_count': report['legacy_owner_count'],
                          'allocation_sha256': receipt['allocation_sha256'],
                          'byte_identical': receipt['byte_identical'], 'installed': False}, sort_keys=True))

    def _guard_mutants(self, language):
        data = self._input(language)
        reserve.audit(data)  # A recognized green baseline precedes all mutants.
        policy, _ = reserve._policy()
        targets = [(row['address'], 'arena') for row in policy['arena']]
        targets += [(row['start'], 'guard|preimage') for row in policy['guards']]
        # Exercise every new whole-parent hash at its end and at surviving old
        # label/state and preserved suffix offsets, beyond the first byte.
        targets += [(address, 'guard|preimage') for address in
                    (0x023CB804, 0x023CC800, 0x023CD7FF, 0x023D5FFF, 0x023CE7FF,
                     0x023CE210, 0x023D4BFF, 0x023D4C00, 0x023D4C10, 0x023D7B10,
                     0x023D7B20, 0x023D7C40, 0x023D7E00, 0x023D7EFF)]
        with patch('sgp131.reserve.baseline.identify', return_value=language):
            for address, diagnostic in targets:
                mutant = bytearray(data)
                mutant[_offset(data, address)] ^= 1
                with self.subTest(address=hex(address)), self.assertRaisesRegex(ValueError, diagnostic):
                    reserve.audit(bytes(mutant))
            y9 = struct.unpack_from('<I', data, 0x50)[0]
            mutant = bytearray(data)
            struct.pack_into('<3I', mutant, y9 + 4, reserve.BASE - 4, 4, 8)
            with self.assertRaisesRegex(ValueError, 'overlay.*BSS|overlap'):
                reserve.audit(bytes(mutant))
            mutant = bytearray(data)
            off9 = struct.unpack_from('<I', data, 0x20)[0]
            struct.pack_into('<I', mutant, off9 + 0xBA0 + 16, 0x021E5904)
            with self.assertRaisesRegex(ValueError, 'static.*BSS'):
                reserve.audit(bytes(mutant))
        self.assertEqual(baseline.identify(data), language)

    def test_en_readonly_audit_and_byte_preserving_policy_apply(self):
        self._audit_and_apply('EN')

    def test_it_readonly_audit_and_byte_preserving_policy_apply(self):
        self._audit_and_apply('IT')

    def test_en_targeted_guard_and_bss_mutants_in_memory(self):
        self._guard_mutants('EN')

    def test_it_targeted_guard_and_bss_mutants_in_memory(self):
        self._guard_mutants('IT')
