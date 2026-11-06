"""Host tests of the rematch core (rematch_select / rematch_apply), no ROM needed.

The core is compiled for the host with the same warnings as the native build and
driven through ctypes. Configs are built here, independently of
sgp131.rematches, from synthetic parties so a shared layout bug cannot hide.
"""
import ctypes as C
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAGIC = 0x31564D52
HEADER, DESCRIPTOR, PARTY = 20, 24, 108


def fnv(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


def slot(difficulty=255, override=0, level=60, species=22, form=0, item=0,
         moves=(1, 2, 3, 4), capsule=0):
    return struct.pack('<BBHHH4HH', difficulty, override, level, species | (form << 10),
                       item, *moves, capsule)


BASE_SLOTS = [dict(level=68, species=22, moves=(355, 65, 366, 224)),
              dict(level=64, species=279, moves=(255, 403, 366, 56)),
              dict(level=68, species=277, item=273, moves=(283, 332, 97, 403)),
              dict(level=66, species=164, moves=(375, 355, 138, 417)),
              dict(level=70, species=398, moves=(370, 97, 413, 38)),
              dict(level=72, species=18, item=158, moves=(366, 119, 403, 413), capsule=11)]


def party(edits=None, slots=BASE_SLOTS):
    result = []
    for index, base in enumerate(slots):
        values = dict(base)
        values.update((edits or {}).get(index, {}))
        result.append(slot(**values))
    return b''.join(result)


VARIANT_A = {1: dict(moves=(58, 403, 366, 56)), 2: dict(moves=(283, 332, 97, 263)),
             5: dict(moves=(366, 355, 403, 413))}
VARIANT_B = {**VARIANT_A, 0: dict(species=169, moves=(355, 413, 369, 440)),
             4: dict(moves=(370, 369, 413, 38))}
BASE_SLOTS_2 = [dict(level=70, species=469, override=32, moves=(103, 369, 403, 405)),
                dict(level=72, species=212, item=158, moves=(442, 14, 364, 400), capsule=12),
                dict(level=68, species=214, item=285, moves=(179, 364, 224, 32)),
                dict(level=70, species=284, moves=(403, 18, 405, 56)),
                dict(level=68, species=416, moves=(92, 455, 194, 403)),
                dict(level=69, species=127, moves=(12, 276, 224, 370))]
VARIANT_A2 = {0: dict(moves=(182, 369, 403, 405)), 2: dict(item=0)}
VARIANT_B2 = {**VARIANT_A2, 3: dict(species=205, moves=(191, 229, 360, 89))}


def descriptor(trainer, type_count, offsets, hashes, reserved=0):
    return struct.pack('<6H3I', trainer, type_count, *offsets, reserved, *hashes)


def build(entries, active=1, types=(1,), mask=0b10, magic=MAGIC, bytes_=None,
          trainers=None, reserved=0, offsets=None, type_counts=None, hashes=None):
    """entries: list of (trainer, base, a, b) 108-byte parties."""
    count = len(entries) if trainers is None else trainers
    first = HEADER + DESCRIPTOR * len(entries)
    body, table = b'', b''
    for index, (trainer, base, a, b) in enumerate(entries):
        spots = [first + len(body) + PARTY * n for n in range(3)]
        body += base + a + b
        use = (offsets or {}).get(index, spots)
        digest = (hashes or {}).get(index, (fnv(base), fnv(a), fnv(b)))
        kind = (type_counts or {}).get(index, 0x0306)
        table += descriptor(trainer, kind, use, digest)
    total = first + len(body)
    padded = list(types) + [0] * (2 - len(types))
    head = struct.pack('<IHBBBBH2I', magic, total if bytes_ is None else bytes_, active,
                       count, len(types), mask, reserved, *padded)
    return head + table + body


def entries():
    return [(712, party(), party(VARIANT_A), party(VARIANT_B)),
            (713, party(slots=BASE_SLOTS_2), party(VARIANT_A2, BASE_SLOTS_2),
             party(VARIANT_B2, BASE_SLOTS_2))]


class RematchCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        target = Path(cls.temp.name) / 'variants.dylib'
        subprocess.run(['clang', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        str(ROOT / 'variants.c'), '-o', str(target)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(target))
        cls.lib.rematch_select.argtypes = [C.c_uint32, C.c_uint32]
        cls.lib.rematch_select.restype = C.c_uint32
        cls.lib.rematch_apply.argtypes = [C.c_void_p, C.c_uint32, C.c_uint32, C.c_uint32,
                                          C.c_uint32, C.c_void_p, C.c_uint32]
        cls.lib.rematch_apply.restype = C.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def apply(self, buffer, trainer, config, type_count=0x0306, plus=1, seed=0, size=None):
        """Run with canaries around the 108-byte buffer; return (result, buffer, config)."""
        guarded = C.create_string_buffer(b'\xA5' * 16 + buffer + b'\x5A' * 16, 16 + len(buffer) + 16)
        image = C.create_string_buffer(config, len(config))
        result = self.lib.rematch_apply(C.addressof(guarded) + 16, trainer, type_count, plus, seed,
                                        image, len(config) if size is None else size)
        raw = guarded.raw
        self.assertEqual(raw[:16], b'\xA5' * 16, 'underflow canary')
        self.assertEqual(raw[16 + len(buffer):], b'\x5A' * 16, 'overflow canary')
        self.assertEqual(image.raw, config, 'config is read-only')
        return result, raw[16:16 + len(buffer)]

    def seed_for(self, trainer, outcome):
        for seed in range(0x10000, 0x10100):
            if ((seed ^ (seed >> 16) ^ trainer) & 1) == outcome:   # independent oracle
                return seed
        self.fail('no seed')

    def test_selector_formula_matches_plan_on_both_outcomes(self):
        seen = set()
        for trainer in (712, 713, 0, 1):
            for seed in (0, 1, 2, 0xFFFF, 0x10000, 0x12345678, 0x80000001, 0xFFFFFFFF):
                expected = ((seed ^ (seed >> 16) ^ trainer) & 1)
                self.assertEqual(self.lib.rematch_select(seed, trainer), expected)
                seen.add(expected)
        self.assertEqual(seen, {0, 1})

    def test_normal_unknown_and_invalid_records_noop(self):
        config = build(entries())
        original = party()
        flipped = bytearray(original); flipped[40] ^= 1
        cases = [('Normal', original, 712, 0x0306, 0), ('unknown trainer', original, 21, 0x0306, 1),
                 ('count', original, 712, 0x0305, 1), ('format', original, 712, 0x0206, 1),
                 ('old order', original, 712, 0x0603, 1), ('zero', original, 712, 0, 1),
                 ('plus 2', original, 712, 0x0306, 2), ('changed record', bytes(flipped), 712, 0x0306, 1)]
        for name, buffer, trainer, kind, plus in cases:
            for outcome in (0, 1):
                with self.subTest(name=name, outcome=outcome):
                    result, after = self.apply(buffer, trainer, config, kind, plus,
                                               self.seed_for(trainer, outcome))
                    self.assertEqual(result, 0)
                    self.assertEqual(after, buffer)
        self.assertEqual(self.lib.rematch_apply(None, 712, 0x0306, 1, 0, C.c_char_p(config), len(config)), 0)
        self.assertEqual(self.lib.rematch_apply(C.create_string_buffer(original), 712, 0x0306, 1, 0, None, 0), 0)

    def test_both_selector_outcomes_and_seed_unchanged(self):
        config = build(entries())
        pairs = {712: (party(VARIANT_A), party(VARIANT_B)),
                 713: (party(VARIANT_A2, BASE_SLOTS_2), party(VARIANT_B2, BASE_SLOTS_2))}
        bases = {712: party(), 713: party(slots=BASE_SLOTS_2)}
        for trainer, (variant_a, variant_b) in pairs.items():
            for outcome, expected, code in ((0, variant_a, 1), (1, variant_b, 2)):
                seed = self.seed_for(trainer, outcome)
                with self.subTest(trainer=trainer, outcome=outcome):
                    result, after = self.apply(bases[trainer], trainer, config, seed=seed)
                    self.assertEqual((result, after), (code, expected))
                    # pure: same inputs, same answer, and the seed is only a value argument
                    self.assertEqual(self.lib.rematch_select(seed, trainer), outcome)
                    self.assertEqual(self.apply(bases[trainer], trainer, config, seed=seed), (code, expected))
            # the selector depends on the seed only through parity of seed ^ (seed >> 16) ^ trainer
            self.assertEqual(self.lib.rematch_select(0x2468ACE0, trainer), (0x2468ACE0 ^ 0x2468 ^ trainer) & 1)

    def test_four_complete_outputs_and_canaries(self):
        config = build(entries())
        seen = set()
        for trainer, base_slots, a_edits, b_edits in ((712, BASE_SLOTS, VARIANT_A, VARIANT_B),
                                                      (713, BASE_SLOTS_2, VARIANT_A2, VARIANT_B2)):
            for outcome, edits in ((0, a_edits), (1, b_edits)):
                expected = party(edits, base_slots)
                result, after = self.apply(party(slots=base_slots), trainer, config,
                                           seed=self.seed_for(trainer, outcome))
                self.assertEqual((result, len(after)), (1 + outcome, 108))
                self.assertEqual(after, expected)
                seen.add(after)
        self.assertEqual(len(seen), 4)

    def test_bad_config_offsets_counts_ids_hash_refuse(self):
        base, a, b = party(), party(VARIANT_A), party(VARIANT_B)
        good = entries()
        first = HEADER + 2 * DESCRIPTOR
        mutations = {
            'magic': build(good, magic=0x12345678),
            'size field larger': build(good, bytes_=len(build(good)) + 1),
            'size field smaller': build(good, bytes_=len(build(good)) - 1),
            'zero trainers': build(good, trainers=0),
            'five trainers': build(good, trainers=5),
            'more trainers than descriptors': build(good, trainers=3),
            'reserved header': build(good, reserved=1),
            'unaligned data before table': build(good, offsets={0: [HEADER, first + 108, first + 216]}),
            'offset beyond image': build(good, offsets={0: [first, first + 108, len(build(good))]}),
            'offset wraps': build(good, offsets={0: [first, first + 108, 0xFFFF]}),
            'overlapping parties': build(good, offsets={0: [first, first + 54, first + 216]}),
            'cross trainer': build(good, offsets={0: [first, first + 108, first + 108 * 4]}),
            'duplicate trainer': build([(712, base, a, b), (712, base, a, b)]),
            'descriptor type_count': build(good, type_counts={0: 0x0603}),
            'descriptor reserved': build(good, hashes=None),
            'baseline hash': build(good, hashes={0: (fnv(base) ^ 1, fnv(a), fnv(b))}),
            'variant A hash': build(good, hashes={0: (fnv(base), fnv(a) ^ 1, fnv(b))}),
            'variant B hash': build(good, hashes={0: (fnv(base), fnv(a), fnv(b) ^ 1)}),
            'identity variant': build([(712, base, base, b)]),
        }
        broken = bytearray(build(good)); struct.pack_into('<H', broken, HEADER + 10, 1)
        mutations['descriptor reserved'] = bytes(broken)
        for outcome in (0, 1):
            for name, config in mutations.items():
                with self.subTest(name=name, outcome=outcome):
                    result, after = self.apply(base, 712, config, seed=self.seed_for(712, outcome))
                    self.assertEqual((result, after), (0, base))
        # config shorter than its own header or declared size never reads past the supplied bytes
        full = build(good)
        for size in (0, 8, 19, 20, 43, len(full) - 1):
            with self.subTest(size=size):
                result, after = self.apply(base, 712, full[:size] if size else b'\0' * 4, size=size)
                self.assertEqual((result, after), (0, base))

    def test_levels_IV_capsules_and_aces_preserved(self):
        base = party()
        seed = self.seed_for(712, 0)
        def attempt(edits, expect_applied=False):
            variant = party(edits)
            # hashes are computed over the invalid content: structure, not integrity, must refuse
            config = build([(712, base, variant, party(VARIANT_B))])
            result, after = self.apply(base, 712, config, seed=seed)
            self.assertEqual((result, after), (1, variant) if expect_applied else (0, base))
        attempt({1: dict(moves=(58, 403, 366, 56))}, True)
        attempt({1: dict(level=65, moves=(58, 403, 366, 56))})            # level
        for index, _ in enumerate(BASE_SLOTS):
            attempt({index: dict(difficulty=254, moves=(58, 403, 366, 56))})   # IV byte
            attempt({index: dict(capsule=BASE_SLOTS[index].get('capsule', 0) + 1, moves=(58, 403, 366, 56))})
        attempt({0: dict(species=169, override=16, moves=(355, 413, 369, 440))})  # new species keeps no override
        attempt({0: dict(species=169, moves=(355, 413, 369, 440))}, True)
        attempt({0: dict(species=0)})
        attempt({0: dict(species=494)})
        attempt({0: dict(species=169, form=1, moves=(355, 413, 369, 440))})
        attempt({0: dict(species=279)})                                   # duplicate species
        attempt({1: dict(moves=(0, 403, 366, 56))})
        attempt({1: dict(moves=(468, 403, 366, 56))})
        attempt({1: dict(moves=(58, 58, 366, 56))})
        attempt({2: dict(item=516)})
        attempt({2: dict(item=515)}, True)
        attempt({2: dict(item=537)})
        attempt({2: dict(item=0xFFFF)})
        attempt({5: dict(species=18, level=72, item=158, capsule=11, moves=(366, 119, 403, 413))})  # same as base
        self.assertEqual(self.lib.rematch_select(seed, 712), 0)


if __name__ == '__main__':
    unittest.main()
