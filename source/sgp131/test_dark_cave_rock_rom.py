"""Read-only HG-F12 applicability proof on exact 1.3.1 EN/IT trials.

The test authenticates both private candidates, the matrix/land archives and
all four Dark Cave Route-45-side land members. ``ROCK_FOOTPRINTS`` is a
literal independent decode of every connected triangle component whose native
material name contains ``rock``. Full land/model hashes bind that geometry to
the tested bytes; the assertions then read the real 32x32 permission grids.

No ROM, save or extracted model is written. Paths can be overridden with
SGP_HG_F12_ROM_EN/IT; SGP_HG_F12_REQUIRE_INPUTS=1 makes missing inputs fail.
"""
import hashlib
import os
from pathlib import Path
import struct
import unittest

import ndspy.narc
import ndspy.rom


ROOT = Path(__file__).resolve().parents[2]
ACTIVE_ROOT = ROOT / "local/notes/ds-campaign-2026-11-04/final-gates/active"
CANDIDATES = {
    "EN": (
        "Sacred-Gold-Plus-1.3.1-EN-active-trial.nds",
        "618f0501d1355f5c7ee6d0301847222fd23a3d67701027190424bf28225fb13d",
        152786376,
    ),
    "IT": (
        "Sacred-Gold-Plus-1.3.1-IT-active-trial.nds",
        "171b53b6c47555d54cb82c724569f26e9dfd92f51aa064545dd44b09179d64a0",
        159029292,
    ),
}
ARCHIVES = {
    "matrix": ("a/0/4/1", "f5cab013a865338d88231ec970784b43618c0863309f0a10178f34cdabdd848a"),
    "land": ("a/0/6/5", "120594d49680ed216487d40bc68b5af23b11882eac76f5ecafa992c278d4b4ab"),
}
MATRIX_MEMBER = 98
MATRIX_SHA256 = "334f0f7bee29337f5f78ef734250a1d4a28c299440002a4199086ece76d897a5"
LANDS = {
    594: (
        "ce96667e66c5e859fcd294b71a5d5f5272eb2d4d477f149cbb1b18391508f265",
        "79f19e13832078e4370026404c0f5dc1e41829debc5ed0d8c84012c20dc7ac0c",
        "caf2cae28e9942ac3b19bf4b24f80bc11db1680936b92d96b480f918370820e2",
    ),
    595: (
        "4945a07ebe7485eb092e85d7a004173b9d079c1fdb6a1521ccc2d1b6d0c5d106",
        "00d76e1e1fcfb9431b3bc421ca22e399dd80137f4b9166bf03649a37d0f875d9",
        "1e96db4fc37172638ff893a6692bd172358fb0a4aac9338f3968684af2881f4c",
    ),
    596: (
        "aeead00e3c4c9bd3fb39d29d9f04dd4826026f8394dc8cc13380bf34157eab23",
        "a4d41f8a3a4a90b2c87e82c1a088f27f9db08ca4aa1718f135e8b4862a3562dd",
        "ca51861db1c28f73178aaaf65be78234d67a49f58d335f02f5653fcc8461b527",
    ),
    597: (
        "8bac73545c9f020ccdb6a6b5d48902a650544ddc0495ee4eed87c863ff829619",
        "9160f5a9e62cccdb01e7411405d35045f8b5ca255097525ea8aa56991a530c43",
        "da13fe3016e3a7169c56dfb4255cbb2f3f0edb8fa60b9671a052798d73977539",
    ),
}
CELL_ORIGINS = {594: (0, 0), 595: (32, 0), 596: (0, 32), 597: (32, 32)}
SURFABLE_BEHAVIORS = frozenset({16, 17, 18, 19, 20, 21, 25, 42,
                                80, 81, 82, 83, 115, 120, 124})

# (land member, tuple of every local tile overlapped by one connected rock).
# Boundary-crossing components intentionally retain every touched tile.
ROCK_FOOTPRINTS = (
    (594, ((4, 18),)),
    (594, ((5, 17),)),
    (594, ((5, 25),)),
    (594, ((5, 25), (5, 26), (5, 27))),
    (594, ((13, 8), (13, 9), (13, 10))),
    (594, ((13, 12),)),
    (594, ((14, 9),)),
    (594, ((15, 9),)),
    (594, ((16, 8), (16, 9), (16, 10))),
    (594, ((17, 8), (17, 9), (17, 10))),
    (594, ((17, 10),)),
    (594, ((17, 13), (17, 14), (17, 15))),
    (594, ((17, 15),)),
    (594, ((17, 18),)),
    (594, ((19, 16), (19, 17), (19, 18))),
    (594, ((21, 17),)),
    (594, ((27, 8), (27, 9), (27, 10))),
    (594, ((29, 19),)),
    (595, ((4, 19), (5, 19), (4, 20), (5, 20))),
    (595, ((5, 21), (5, 22), (5, 23))),
    (595, ((5, 29),)),
    (595, ((6, 27), (6, 28), (6, 29))),
    (595, ((6, 29),)),
    (595, ((7, 20),)),
    (595, ((7, 21),)),
    (595, ((8, 19), (8, 20), (8, 21))),
    (595, ((9, 1), (9, 2), (9, 3))),
    (595, ((9, 4),)),
    (595, ((11, 22), (11, 23), (11, 24))),
    (595, ((14, 16),)),
    (595, ((16, 6),)),
    (595, ((16, 14), (16, 15), (16, 16))),
    (595, ((19, 4),)),
    (595, ((20, 4),)),
    (595, ((22, 4),)),
    (595, ((24, 2),)),
    (595, ((25, 2),)),
    (595, ((29, 1), (29, 2), (29, 3))),
    (596, ((9, 20),)),
    (596, ((12, 17),)),
    (596, ((15, 16), (15, 17), (15, 18))),
    (596, ((15, 21),)),
    (596, ((16, 17),)),
    (596, ((17, 0),)),
    (596, ((18, 0),)),
    (596, ((19, 20),)),
    (596, ((20, 0), (20, 1))),
    (596, ((20, 20), (20, 21), (20, 22))),
    (596, ((21, 12),)),
    (596, ((21, 14),)),
    (596, ((23, 18),)),
    (596, ((23, 18), (23, 19), (23, 20))),
    (596, ((29, 6),)),
    (596, ((29, 7),)),
    (596, ((3, 0), (4, 0), (3, 1), (4, 1))),
    (596, ((4, 15), (5, 15), (4, 16), (5, 16))),
    (596, ((7, 19), (8, 19), (7, 20), (8, 20))),
    (596, ((22, 20), (23, 20), (22, 21), (23, 21))),
    (597, ((1, 15), (1, 16), (1, 17))),
    (597, ((4, 11), (4, 12), (4, 13))),
    (597, ((4, 13),)),
    (597, ((19, 8), (19, 9), (19, 10))),
)


def _sha256(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def decode_matrix(member):
    if len(member) < 5:
        raise ValueError("truncated matrix")
    width, height, has_headers, has_altitudes, name_length = member[:5]
    if has_headers not in (0, 1) or has_altitudes not in (0, 1):
        raise ValueError("noncanonical matrix flags")
    count = width * height
    cursor = 5 + name_length
    name = bytes(member[5:cursor])
    cursor += count * 2 * has_headers + count * has_altitudes
    if cursor + count * 2 != len(member):
        raise ValueError("matrix length mismatch")
    lands = struct.unpack_from(f"<{count}H", member, cursor)
    return width, height, name, lands


def decode_land(member):
    if len(member) < 20:
        raise ValueError("truncated land")
    sizes = struct.unpack_from("<4I", member)
    signature, bgs_length = struct.unpack_from("<HH", member, 16)
    if signature != 0x1234 or 20 + bgs_length + sum(sizes) != len(member):
        raise ValueError("invalid land envelope")
    cursor = 20 + bgs_length
    sections = []
    for size in sizes:
        sections.append(bytes(member[cursor:cursor + size]))
        cursor += size
    permissions, buildings, model, collision = sections
    if len(permissions) != 2048:
        raise ValueError("invalid permission grid")
    values = struct.unpack("<1024H", permissions)
    grid = {(x, z): values[z * 32 + x] for z in range(32) for x in range(32)}
    return {"permissions": permissions, "grid": grid, "buildings": buildings,
            "model": model, "collision": collision}


def input_assets(case, language):
    filename, expected_sha, expected_size = CANDIDATES[language]
    path = Path(os.environ.get("SGP_HG_F12_ROM_" + language)
                or ACTIVE_ROOT / filename)
    if not path.is_file():
        message = f"private {language} 1.3.1 trial missing: {path}"
        if os.environ.get("SGP_HG_F12_REQUIRE_INPUTS") == "1":
            case.fail(message)
        case.skipTest(message)
    raw = path.read_bytes()
    case.assertEqual((_sha256(raw), len(raw)), (expected_sha, expected_size))
    rom = ndspy.rom.NintendoDSRom(raw)
    result = {}
    for label, (name, digest) in ARCHIVES.items():
        blob = rom.getFileByName(name)
        case.assertEqual(_sha256(blob), digest)
        result[label] = ndspy.narc.NARC(blob).files
    return result


def surfable_rock_overlaps(permissions, footprints):
    """Return decoded rock cells whose low-byte behavior permits Surf."""
    result = []
    for member, cells in footprints:
        for x, z in cells:
            behavior = permissions[member][x, z] & 0xFF
            if behavior in SURFABLE_BEHAVIORS:
                result.append((member, x, z, behavior))
    return tuple(result)


def map_coords(member, x, z):
    origin_x, origin_z = CELL_ORIGINS[member]
    return origin_x + x, origin_z + z


class DarkCaveRockRomTests(unittest.TestCase):
    def test_overlap_detector_rejects_a_water_coded_rock(self):
        """Catches a zero-overlap check that ignores behavior 21."""
        permissions = {596: {(29, 6): 0x0015, (29, 7): 0x8000}}
        footprints = ((596, ((29, 6),)), (596, ((29, 7),)))
        self.assertEqual(
            surfable_rock_overlaps(permissions, footprints),
            ((596, 29, 6, 21),),
        )

    def test_exact_trials_keep_all_rocks_off_surfable_behaviors(self):
        """Catches a rock permission becoming any native Surf-capable behavior."""
        self.assertEqual(len(ROCK_FOOTPRINTS), 62)
        self.assertEqual(sum(len(cells) for _member, cells in ROCK_FOOTPRINTS), 118)
        self.assertEqual(len({(member, x, z) for member, cells in ROCK_FOOTPRINTS
                              for x, z in cells}), 111)

        language_permissions = {}
        for language in CANDIDATES:
            with self.subTest(language=language):
                archives = input_assets(self, language)
                matrix = bytes(archives["matrix"][MATRIX_MEMBER])
                self.assertEqual(_sha256(matrix), MATRIX_SHA256)
                self.assertEqual(decode_matrix(matrix),
                                 (2, 2, b"m_dun4201_", (594, 595, 596, 597)))

                permissions = {}
                for member, (land_sha, permission_sha, model_sha) in LANDS.items():
                    raw_land = bytes(archives["land"][member])
                    self.assertEqual(_sha256(raw_land), land_sha)
                    land = decode_land(raw_land)
                    self.assertEqual(_sha256(land["permissions"]), permission_sha)
                    self.assertEqual(_sha256(land["model"]), model_sha)
                    permissions[member] = land["grid"]
                language_permissions[language] = permissions

                self.assertEqual(surfable_rock_overlaps(permissions, ROCK_FOOTPRINTS), ())
                mutant = {member: dict(grid) for member, grid in permissions.items()}
                mutant[596][29, 6] = 0x0015
                self.assertEqual(
                    surfable_rock_overlaps(mutant, ROCK_FOOTPRINTS),
                    ((596, 29, 6, 21),),
                )
                target = permissions[596]
                self.assertEqual(
                    (map_coords(596, 29, 6), target[29, 6],
                     map_coords(596, 29, 7), target[29, 7]),
                    ((29, 38), 0x8000, (29, 39), 0x8000),
                )
                self.assertEqual(
                    (map_coords(596, 29, 5), target[29, 5],
                     map_coords(596, 30, 5), target[30, 5],
                     map_coords(596, 30, 6), target[30, 6]),
                    ((29, 37), 0x0015, (30, 37), 0x0A08, (30, 38), 0x0A08),
                )
                model = decode_land(bytes(archives["land"][596]))["model"]
                self.assertIn(b"drock01s", model)
                self.assertIn(b"d_rock01s", model)
                self.assertIn(b"dpond_line", model)

        if set(language_permissions) == set(CANDIDATES):
            self.assertEqual(language_permissions["EN"], language_permissions["IT"])


if __name__ == "__main__":
    unittest.main()
