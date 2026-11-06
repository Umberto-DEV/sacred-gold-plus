"""Independent growth-curve oracle and fail-closed generator tests."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest


FEATURE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("growth_tables", FEATURE / "growth_tables.py")
growth = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(growth)

PINS = (
    "a33f5a043396120d4d42a807a240d87d144ca800c4b41cfdd848951c662909b6",
    "98781feea113d8d2e3e3f578d98d0a7f76bd0d008e79dd3942cb0ed490ebd7ee",
    "f3a821d7e60596706c3194766b2f9e87795d45450712432a8a8399b41c5ee1e7",
    "ce0722560af1b3f820abbc165685ca922edcf99c4e808815f17d05fc20956590",
    "d57547b2a55109f3b92e6c4214dc79c8f92688205f7460e7fe868c3c363012af",
    "bfd0fd42601e0c68de3ed54272ae341e207bea9a89c2d8c57efe1ac8a22799f5",
    "a33f5a043396120d4d42a807a240d87d144ca800c4b41cfdd848951c662909b6",
    "a33f5a043396120d4d42a807a240d87d144ca800c4b41cfdd848951c662909b6",
)

VECTORS = (
    (970299, 1000000, 1030301, 2048383, 2097152, 3307949, 3375000),
    (591882, 600000, 618180, 1229029, 1258291, 1984769, 2025000),
    (1571884, 1640000, 1689693, 3359348, 3439329, 5425036, 5535000),
    (1027103, 1059860, 1091974, 2170999, 2222687, 3505962, 3577027),
    (776239, 800000, 824240, 1638706, 1677721, 2646359, 2700000),
    (1212873, 1250000, 1287876, 2560478, 2621440, 4134936, 4218750),
    (970299, 1000000, 1030301, 2048383, 2097152, 3307949, 3375000),
    (970299, 1000000, 1030301, 2048383, 2097152, 3307949, 3375000),
)


def oracle(curve: int, level: int) -> int:
    if level <= 1:
        return 0
    q = level ** 3
    if curve in (0, 6, 7):
        return q
    if curve == 1:
        if level <= 50:
            return q * (100 - level) // 50
        if level <= 68:
            return q * (150 - level) // 100
        if level <= 98:
            return q * ((1911 - 10 * level) // 3) // 500
        return q * (160 - level) // 100
    if curve == 2:
        if level <= 15:
            return q * (((level + 1) // 3) + 24) // 50
        if level <= 35:
            return q * (level + 14) // 50
        return q * ((level // 2) + 32) // 50
    if curve == 3:
        return max(0, 6 * q // 5 - 15 * level * level + 100 * level - 140)
    if curve == 4:
        return 4 * q // 5
    if curve == 5:
        return 5 * q // 4
    raise AssertionError(curve)


def canonical_members() -> tuple[bytes, ...]:
    return tuple(struct.pack("<101I", *(oracle(curve, level) for level in range(101)))
                 for curve in range(8))


class GrowthTableTests(unittest.TestCase):
    def test_independent_original_formula_matches_candidate_pins(self):
        members = canonical_members()
        self.assertEqual(tuple(hashlib.sha256(member).hexdigest() for member in members), PINS)
        self.assertTrue(all(len(member) == 404 for member in members))

    def test_extension_preserves_every_original_byte_and_matches_vectors(self):
        old = canonical_members()
        new = growth.extend_members(old)
        self.assertEqual(len(new), 8)
        for curve, member in enumerate(new):
            self.assertEqual(member[:404], old[curve])
            values = struct.unpack("<151I", member)
            self.assertEqual(tuple(values[level] for level in (99, 100, 101, 127, 128, 149, 150)),
                             VECTORS[curve])
            self.assertEqual(values[0:2], (0, 0))
            self.assertTrue(all(values[level] > values[level - 1]
                                for level in range(2, 151)))

    def test_level_inversion_boundaries_and_terminal_cap(self):
        for curve, raw in enumerate(growth.extend_members(canonical_members())):
            table = struct.unpack("<151I", raw)
            for level in (2, 100, 101, 127, 128, 149, 150):
                with self.subTest(curve=curve, level=level):
                    self.assertEqual(growth.level_from_exp(table, table[level] - 1, 150), level - 1)
                    self.assertEqual(growth.level_from_exp(table, table[level], 150), level)
            self.assertEqual(growth.level_from_exp(table, 0xFFFFFFFF, 150), 150)

    def test_level_150_product_cannot_be_computed_in_32_bits(self):
        numerator = 1_640_000 * 150 ** 3
        self.assertGreater(numerator, 0xFFFFFFFF)
        self.assertEqual(numerator // 1_000_000, 5_535_000)
        self.assertEqual((numerator & 0xFFFFFFFF) // 1_000_000, 3_082)

    def test_rejects_wrong_identity_shape_and_nonmonotone_data(self):
        members = list(canonical_members())
        for broken in (members[:7], members + [members[0]]):
            with self.assertRaises(ValueError):
                growth.extend_members(broken)
        broken = members.copy()
        broken[0] = broken[0][:-4]
        with self.assertRaises(ValueError):
            growth.extend_members(broken)
        broken = members.copy()
        broken[1] = bytes([broken[1][0] ^ 1]) + broken[1][1:]
        with self.assertRaises(ValueError):
            growth.extend_members(broken)
        table = list(struct.unpack("<101I", members[0]))
        table[50] = table[49]
        broken = members.copy()
        broken[0] = struct.pack("<101I", *table)
        with self.assertRaises(ValueError):
            growth.extend_members(broken)
        with self.assertRaises(ValueError):
            growth.level_from_exp(range(151), 10, 151)

    def test_bundle_is_small_deterministic_and_refuses_nonempty_destination(self):
        with tempfile.TemporaryDirectory(prefix="sgp-growth-") as root:
            out = Path(root) / "out"
            manifest = growth.write_bundle(canonical_members(), out)
            self.assertEqual(manifest["schema"], 1)
            self.assertEqual(manifest["cap"], 150)
            self.assertEqual(len(manifest["members"]), 8)
            self.assertLess(sum(path.stat().st_size for path in out.iterdir()), 50 * 1024)
            on_disk = json.loads((out / "manifest.json").read_text())
            self.assertEqual(on_disk, manifest)
            with self.assertRaises(FileExistsError):
                growth.write_bundle(canonical_members(), out)

    @unittest.skipUnless(os.environ.get("SGP_CAP150_ROM"), "set SGP_CAP150_ROM for real candidate proof")
    def test_real_candidate_archive_matches_all_eight_pins(self):
        members = growth.extract_growth_members(Path(os.environ["SGP_CAP150_ROM"]))
        self.assertEqual(tuple(hashlib.sha256(member).hexdigest() for member in members), PINS)
        growth.extend_members(members)


if __name__ == "__main__":
    unittest.main()
