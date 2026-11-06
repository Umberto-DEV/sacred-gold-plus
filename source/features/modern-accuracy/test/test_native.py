"""Compiled Keen Eye predicate against the real ability getter (overlay 12).

The production compiler path (sgp131.modern_abilities.compile_native) builds
the payload at two emulator-only addresses; neither is a reserve assignment.
Inputs are the private V4 ROMs; without them the suite skips with a reason,
and SGP_ACCURACY_REQUIRE_INPUTS=1 turns that skip into a failure.
"""
import hashlib
import os
import tempfile
import unittest
from pathlib import Path

import accuracy_bench as bench
from sgp131 import modern_abilities

# Emulator-only placements: 4-byte aligned, inside BL range of the seam, and not
# claimed in any reserve. Production uses the address Codex assigns.
TEST_ADDRESSES = (0x023DF000, 0x02390000)
SUPPRESSION = (
    ('none', 0, 0),
    ('gastro_acid', bench.SUPPRESSED, 0),
    ('gravity_levitate', 0, 0x7000),
    ('ingrain_levitate', bench.INGRAIN, 0),
)


def load(test):
    rows = {}
    for language in ('EN', 'IT'):
        path, digest = bench.input_path(language)
        if path is None:
            if os.environ.get(bench.REQUIRE) == '1':
                test.fail('missing required V4 %s input' % language)
            test.skipTest('private V4 %s ROM not available' % language)
        data = path.read_bytes()
        test.assertEqual(hashlib.sha256(data).hexdigest(), digest, language + ' input identity')
        rows[language] = (path, data)
    return rows


class NativePredicate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='modern-accuracy-native-')

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def setUp(self):
        self.inputs = load(self)

    def compiled(self, address):
        payload, receipt = modern_abilities.compile_native(Path(self.work.name), address)
        self.assertTrue(0 < len(payload) <= 128, 'payload must be compiled and fit the 128-byte budget')
        return payload, receipt

    def test_predicate_uses_effective_native_ability_once(self):
        for language, (path, data) in self.inputs.items():
            image = bench.overlay_image(data)
            for address in TEST_ADDRESSES:
                payload, _ = self.compiled(address)
                b = bench.Bench(path, image, [(address, payload)])
                for battler in range(4):
                    for ability in range(256):
                        for name, flags, field in SUPPRESSION:
                            case = {'abilities': {battler: ability}, 'effect_flags': {battler: flags},
                                    'field': field}
                            result, preserved = b.call(address, bench.CTX, battler, prepare=case)
                            effective = ability
                            if name == 'gastro_acid' and ability != 121:
                                effective = 0
                            if name in ('gravity_levitate', 'ingrain_levitate') and ability == 26:
                                effective = 0
                            self.assertEqual(result, int(effective in (51, 109)),
                                             (language, hex(address), battler, ability, name))
                            self.assertTrue(preserved, 'AAPCS r4-r11/SP/stack canary')
                            self.assertEqual(b.getter_calls, [battler], 'one native getter call')

    def test_suppressed_keen_eye_and_unaware_lose_effect(self):
        for language, (path, data) in self.inputs.items():
            address = TEST_ADDRESSES[0]
            payload, _ = self.compiled(address)
            b = bench.Bench(path, bench.overlay_image(data), [(address, payload)])
            for ability in (51, 109):
                active = b.call(address, bench.CTX, 0, prepare={'abilities': {0: ability}})[0]
                gastro = b.call(address, bench.CTX, 0, prepare={'abilities': {0: ability},
                                                               'effect_flags': {0: bench.SUPPRESSED}})[0]
                self.assertEqual((active, gastro), (1, 0), (language, ability))

    def test_payload_is_position_independent_except_getter_literal(self):
        first, a = self.compiled(TEST_ADDRESSES[0])
        second, b = self.compiled(TEST_ADDRESSES[1])
        self.assertEqual(first, second)
        self.assertEqual(a['payload_sha256'], b['payload_sha256'])
        self.assertIn((bench.GETTER | 1).to_bytes(4, 'little'), first)
        self.assertEqual(a['entry'], TEST_ADDRESSES[0] | 1)
        self.assertLessEqual(a['stack_bytes'], 8)

    def test_unaligned_or_out_of_range_address_is_refused(self):
        for address in (TEST_ADDRESSES[0] + 2, 0x02800000, 0x01000000):
            with self.assertRaises(ValueError):
                modern_abilities.compile_native(Path(self.work.name), address)


if __name__ == '__main__':
    unittest.main()
