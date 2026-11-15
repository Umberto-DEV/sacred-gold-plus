"""Controlled pre-writer input contracts; no retail fixture, CPU or compiler."""
from pathlib import Path
import importlib.util
import struct
import unittest


def module():
    path = Path(__file__).parents[1] / 'tools/prepara_shellbell_ordinary.py'
    spec = importlib.util.spec_from_file_location('ordinary_input_test', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class OrdinaryInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.T = module()
        # Authored markers, not copies of game resources.
        cls.items = b''.join(bytes((i % 251,)) * 34 + bytes(2) for i in range(516))
        cls.moves = bytes((i % 251 for i in range(7488)))

    def build(self, **kwargs):
        return self.T.make_arenas(self.items, self.moves, **kwargs)

    def context(self, value):
        return bytes.fromhex(next(a['hex'] for a in value['arenas'] if a['name'] == 'CTX'))

    def test_success_damage_and_hp_are_before_the_native_writer(self):
        value = self.build(); ctx = self.context(value)
        self.assertEqual(struct.unpack_from('<i', ctx, 0x2144)[0], -100)
        for offset in (0x213C, 0x2140, 0x215C, 0x2EC, 0x30, 0x3C, 0x40, 0x44, 0x58):
            self.assertEqual(struct.unpack_from('<I', ctx, offset)[0], 0)
        self.assertEqual(struct.unpack_from('<I', ctx, 8)[0], 28)
        self.assertEqual(struct.unpack_from('<iI', ctx, 0x2D8C), (150, 300))
        self.assertEqual(struct.unpack_from('<iI', ctx, 0x2E4C), (300, 300))
        self.assertFalse(value['CPU_executed'])
        self.assertFalse(value['forecast_produced'])

    def test_storage_widths_keep_move_words_distinct_from_battlemon_halfwords(self):
        value = self.build(); ctx = self.context(value)
        self.assertEqual(struct.unpack_from('<3I', ctx, 0x3040), (33, 33, 0))
        for name in ('moveNoTemp', 'moveNoCur', 'moveNoPrev'):
            f = next(f for f in value['fields'] if f['name'] == name)
            self.assertEqual((f['storage'], len(bytes.fromhex(f['hex']))), ('u32', 4))
        self.assertEqual(struct.unpack_from('<4H', ctx, 0x2D4C), (33, 0, 0, 0))
        self.assertEqual(ctx[0x2D58:0x2D60], bytes([6] * 8))
        self.assertEqual(ctx[0x2E18:0x2E20], bytes([6] * 8))
        item = next(f for f in value['fields'] if f['name'] == 'battleMons[0].item')
        self.assertEqual((item['storage'], item['hex']), ('u16', 'fd00'))

    def test_full_hp_control_changes_only_attacker_hp_bytes(self):
        low, high = self.context(self.build()), self.context(self.build(full_hp=True))
        changed = [i for i, (a, b) in enumerate(zip(low, high)) if a != b]
        self.assertTrue(changed)
        self.assertTrue(all(0x2D8C <= i < 0x2D90 for i in changed))
        self.assertEqual(struct.unpack_from('<i', high, 0x2D8C)[0], 300)

    def test_seed_reaches_declared_first_roll_without_injecting_it(self):
        seed = self.T.seed_before_99()
        self.assertEqual(((seed * 1103515245 + 24691) & 0xffffffff) >> 16, 99)
        bs = next(a for a in self.build()['arenas'] if a['name'] == 'BS')
        self.assertEqual(struct.unpack_from('<I', bytes.fromhex(bs['hex']), 0x2448)[0], seed)

    def test_resources_keep_raw_stride_and_cache_boundaries(self):
        value = self.build(); ctx = self.context(value)
        self.assertEqual(ctx[0x3DE:0x211E], self.moves)
        self.assertEqual(ctx[0x211E:0x2120], bytes(2))
        self.assertEqual(struct.unpack_from('<I', ctx, 0x2120)[0], self.T.CACHE)
        self.assertEqual(bytes.fromhex(next(a['hex'] for a in value['arenas'] if a['name'] == 'CACHE')), self.items)

    def test_wrong_geometry_padding_or_boolean_aliases_are_rejected(self):
        for items, moves in ((self.items[:-1], self.moves), (self.items, self.moves[:-1])):
            with self.assertRaises(ValueError): self.T.make_arenas(items, moves)
        malformed = bytearray(self.items); malformed[35] = 1
        with self.assertRaises(ValueError): self.T.make_arenas(bytes(malformed), self.moves)
        for value in (0, 1, 'false', None):
            with self.assertRaises(ValueError): self.build(full_hp=value)
        with self.assertRaises(ValueError): self.T.make_arenas(bytearray(self.items), self.moves)

    def test_independent_arena_and_declared_field_intervals_do_not_overlap(self):
        value = self.build(); occupied = set()
        for arena in value['arenas']:
            block = bytes.fromhex(arena['hex'])
            self.assertEqual((len(block), self.T.sha(block)), (arena['bytes'], arena['sha256']))
            addresses = set(range(arena['ram'], arena['ram'] + len(block)))
            self.assertFalse(occupied & addresses); occupied.update(addresses)
        declared = set()
        for f in value['fields']:
            addresses = set(range(f['ram'], f['ram'] + len(bytes.fromhex(f['hex']))))
            self.assertFalse(declared & addresses); declared.update(addresses)
        self.assertTrue(declared <= occupied)


if __name__ == '__main__':
    unittest.main()
