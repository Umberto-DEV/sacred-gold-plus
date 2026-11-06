"""HG-F09 exact Route 43/44 permission and visual-material regression.

The private active candidates are optional inputs.  When present, this test
authenticates both images, matrix 0, the shared land archive, lands 87/102 and
their decoded native model surfaces.  It then runs the production stage (or
an identity fallback during the first TDD RED) and requires the six invisible
grass cells to become ordinary ground while adjacent visible grass, water and
ordinary ground remain unchanged.

No ROM, save or extracted model is retained.  SGP_HG_F09_REQUIRE_INPUTS=1
makes absent private inputs/toolchain fail rather than skip.
"""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

import ndspy.narc
import ndspy.rom

from .map_resources import LandData, Matrix


ROOT = Path(__file__).resolve().parents[2]
ACTIVE = ROOT / "local/notes/ds-campaign-2026-11-04/final-gates/active"
CANDIDATES = {
    "EN": ("Sacred-Gold-Plus-1.3.1-EN-active-trial.nds",
           "618f0501d1355f5c7ee6d0301847222fd23a3d67701027190424bf28225fb13d",
           152786376),
    "IT": ("Sacred-Gold-Plus-1.3.1-IT-active-trial.nds",
           "171b53b6c47555d54cb82c724569f26e9dfd92f51aa064545dd44b09179d64a0",
           159029292),
}
LAND_ARCHIVE = "a/0/6/5"
LAND_ARCHIVE_SHA256 = "120594d49680ed216487d40bc68b5af23b11882eac76f5ecafa992c278d4b4ab"
MATRIX_ARCHIVE = "a/0/4/1"
MATRIX0_SHA256 = "a6012ac34ae879b5f85f21642a78afcff617112813c4cf1e6327054735c56d2d"
LANDS = {
    87: {
        "origin": (16, 3), "map": 45, "targets": ((11, 16), (12, 16), (13, 16)),
        "land_sha256": "10174f6a0cfdeae637639949cbfbab63c3b77071dbcc2893e1276512d74c6cb2",
        "permission_sha256": "1b5556cccb70bcbff752ae7569600becd48d15a1e5e7207c622bdbef10a652c2",
        "model_sha256": "a6125265f5fb814bee1090e3e9e738e09ee4818c2f44531dd13935809dceb5fc",
        "collision_sha256": "ad1d40926fa3cf3f4a105256f5e944c6fa0358b6a07db86a7252c377b05705e1",
        "target_materials": ((('egrass_u', 'egrass_u'),),
                             (('egrass_u', 'egrass_u'),),
                             (('egrass_ri', 'egrass_ri'),
                              ('egrass_u', 'egrass_u'),
                              ('egrass_v', 'egrass_v'))),
        "visible": ((11, 17), (12, 17), (13, 17)),
        "ordinary": ((8, 17), (9, 17), (10, 17)),
        "ordinary_materials": ((('grass01', 'grass01gs'),),
                               (('grass01', 'grass01gs'),),
                               (('egrass_v', 'egrass_v'),)),
        "same_material_ordinary": ((16, 7), (17, 7), (22, 11), (23, 11),
                                   (24, 11), (17, 26), (18, 26)),
        "water": ((11, 15), (12, 15)),
    },
    102: {
        "origin": (18, 5), "map": 46, "targets": ((17, 12), (18, 12), (19, 12)),
        "land_sha256": "b55a1fce3a18a7a226ec851977555dbd1e0dc6872f94f918dd8ee815f4a1b1ec",
        "permission_sha256": "d002ad91ed7c1101a6b757cbb1a12f63efae9597b3ce10521149f09016d60b0b",
        "model_sha256": "2afdeda4f6dd8b6fee473e06b3e2297068ef1ec3e8ba942f917bbbd4f23abfed",
        "collision_sha256": "6adc0aadede32d1636059483006641d1e805eeb1187f1ebde9bae5b370f91a74",
        "target_materials": ((('egrass_u', 'egrass_u'),),) * 3,
        "visible": ((17, 13), (18, 13), (19, 13)),
        "ordinary": (),
        "ordinary_materials": (),
        "same_material_ordinary": (),
        "water": ((18, 11), (19, 11)),
    },
}
JAVA = Path(os.environ["SGP_HG_F09_JAVA"]) if os.environ.get("SGP_HG_F09_JAVA") else None
JAR = Path(os.environ["SGP_HG_F09_JAR"]) if os.environ.get("SGP_HG_F09_JAR") else None
JAVA_SHA256 = "0f642542ea1f0be6957557c0db96653ec128113bb5a4aaa7c2534d1d72ddb51f"
JAR_SHA256 = "f77a878f027b327eba85f5afdd13299ca066901f7d78fe3dfd89a00e9bba6ff4"


def sha256(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def native_model_readback(java, jar, model):
    """Use the public read-only bridge with the original external tool pins."""
    if sha256(Path(jar).read_bytes()) != JAR_SHA256:
        raise ValueError("pinned Java library required")
    if sha256(Path(java).read_bytes()) != JAVA_SHA256:
        raise ValueError("pinned Java executable required")
    bridge = Path(__file__).with_name("tools") / "NativeModelReadback.java"
    command = [str(java), "-Xmx256m", "-Djava.awt.headless=true", "--class-path",
               str(jar), str(bridge), "readback", str(model)]
    run = subprocess.run(command, capture_output=True, text=True, timeout=45)
    if run.returncode != 0:
        raise ValueError("Java native readback failed: " + run.stderr[-3000:])
    if len(run.stdout) >= 4 * 1024 ** 2:
        raise ValueError("Java diagnostics oversized")
    return json.loads(run.stdout)


def permission(land, x, z):
    return struct.unpack_from("<H", land.permissions, 2 * (z * 32 + x))[0]


def _surface_y(px, pz, a, b, c):
    denominator = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
    if abs(denominator) < 1e-8:
        return None
    u = ((b[2] - c[2]) * (px - c[0]) + (c[0] - b[0]) * (pz - c[2])) / denominator
    v = ((c[2] - a[2]) * (px - c[0]) + (a[0] - c[0]) * (pz - c[2])) / denominator
    w = 1 - u - v
    return None if min(u, v, w) < -1e-7 else u * a[1] + v * b[1] + w * c[1]


def top_materials(model, x, z):
    px, pz = 16 * x - 248, 16 * z - 248
    hits = []
    for mesh in model["meshes"]:
        positions = mesh["positions"]
        indices = mesh["triangles"]
        for offset in range(0, len(indices), 3):
            points = [positions[3 * index:3 * index + 3]
                      for index in indices[offset:offset + 3]]
            y = _surface_y(px, pz, *points)
            if y is not None:
                hits.append((y, mesh["material"], mesh["texture"]))
    if not hits:
        raise AssertionError("no decoded surface at land cell")
    top = max(y for y, _material, _texture in hits)
    return tuple(sorted({(material, texture) for y, material, texture in hits
                         if abs(y - top) < 1e-5}))


def _stage_or_identity(data, language):
    """Keep the first TDD failure semantic: current 0x0002 != wanted 0x0400."""
    try:
        stage = importlib.import_module("sgp131.invisible_grass")
    except ModuleNotFoundError as error:
        if error.name != "sgp131.invisible_grass":
            raise
        return bytes(data), {"stage": "identity-tdd-red", "language": language}
    return stage.apply(data, language)


def _required_asset(case, path, label):
    if path is not None and path.is_file():
        return
    message = f"private {label} missing: {path}"
    if os.environ.get("SGP_HG_F09_REQUIRE_INPUTS") == "1":
        case.fail(message)
    case.skipTest(message)


class InvisibleGrassExactRomTests(unittest.TestCase):
    def _exact_en(self):
        filename, digest, size = CANDIDATES["EN"]
        path = Path(os.environ.get("SGP_HG_F09_ROM_EN") or ACTIVE / filename)
        _required_asset(self, path, "EN active trial")
        raw = path.read_bytes()
        self.assertEqual((sha256(raw), len(raw)), (digest, size))
        return raw

    def test_exact_en_it_visual_permission_mismatch_is_repaired_only_at_six_words(self):
        """Catches any missed/extra permission edit or a target that is visually grass."""
        for path, label in ((JAVA, "pinned Java"), (JAR, "pinned Nds4j")):
            _required_asset(self, path, label)

        images = {}
        archives = {}
        lands_by_language = {}
        matrix0_by_language = {}
        for language, (filename, digest, size) in CANDIDATES.items():
            path = Path(os.environ.get("SGP_HG_F09_ROM_" + language) or ACTIVE / filename)
            _required_asset(self, path, language + " active trial")
            raw = path.read_bytes()
            self.assertEqual((sha256(raw), len(raw)), (digest, size))
            rom = ndspy.rom.NintendoDSRom(raw)
            land_archive = bytes(rom.getFileByName(LAND_ARCHIVE))
            self.assertEqual((sha256(land_archive), len(land_archive)),
                             (LAND_ARCHIVE_SHA256, 19536658))
            matrix_archive = ndspy.narc.NARC(rom.getFileByName(MATRIX_ARCHIVE))
            matrix0 = bytes(matrix_archive.files[0])
            self.assertEqual(sha256(matrix0), MATRIX0_SHA256)
            images[language] = raw
            archives[language] = land_archive
            matrix0_by_language[language] = matrix0
            narc = ndspy.narc.NARC(land_archive)
            lands_by_language[language] = {
                member: bytes(narc.files[member]) for member in LANDS
            }

        self.assertEqual(archives["EN"], archives["IT"])
        self.assertEqual(matrix0_by_language["EN"], matrix0_by_language["IT"])
        self.assertEqual(lands_by_language["EN"], lands_by_language["IT"])
        matrix = Matrix.parse(matrix0_by_language["EN"])
        self.assertEqual((matrix.width, matrix.height), (47, 17))

        parsed = {}
        decoded = {}
        with tempfile.TemporaryDirectory(prefix="sgp-hg-f09-") as temporary:
            temporary = Path(temporary)
            for member, identity in LANDS.items():
                index = identity["origin"][1] * matrix.width + identity["origin"][0]
                self.assertEqual((matrix.headers[index], matrix.lands[index]),
                                 (identity["map"], member))
                raw_land = lands_by_language["EN"][member]
                self.assertEqual(sha256(raw_land), identity["land_sha256"])
                land = LandData.parse(raw_land)
                parsed[member] = land
                self.assertEqual(sha256(land.permissions), identity["permission_sha256"])
                self.assertEqual(sha256(land.model), identity["model_sha256"])
                self.assertEqual(sha256(land.collision), identity["collision_sha256"])
                model_path = temporary / f"land-{member}.nsbmd"
                model_path.write_bytes(land.model)
                decoded[member] = native_model_readback(JAVA, JAR, model_path)

        for member, identity in LANDS.items():
            land = parsed[member]
            self.assertEqual(tuple(permission(land, *cell) for cell in identity["targets"]),
                             (0x0002, 0x0002, 0x0002))
            self.assertEqual(tuple(top_materials(decoded[member], *cell)
                                   for cell in identity["targets"]),
                             identity["target_materials"])
            self.assertEqual(tuple(permission(land, *cell) for cell in identity["visible"]),
                             (0x0002, 0x0002, 0x0002))
            self.assertEqual(tuple(top_materials(decoded[member], *cell)
                                   for cell in identity["visible"]),
                             ((('egrass', 'egrass'),),) * 3)
            self.assertEqual(tuple(permission(land, *cell) for cell in identity["ordinary"]),
                             (0x0400,) * len(identity["ordinary"]))
            self.assertEqual(tuple(top_materials(decoded[member], *cell)
                                   for cell in identity["ordinary"]),
                             identity["ordinary_materials"])
            self.assertEqual(tuple(permission(land, *cell)
                                   for cell in identity["same_material_ordinary"]),
                             (0x0400,) * len(identity["same_material_ordinary"]))
            self.assertEqual(tuple(top_materials(decoded[member], *cell)
                                   for cell in identity["same_material_ordinary"]),
                             ((('egrass_u', 'egrass_u'),),) *
                             len(identity["same_material_ordinary"]))
            self.assertEqual(tuple(permission(land, *cell) for cell in identity["water"]),
                             (0x0010,) * len(identity["water"]))
            self.assertEqual(tuple(top_materials(decoded[member], *cell)
                                   for cell in identity["water"]),
                             ((('pond_on', 'pond_on'),),) * len(identity["water"]))

        for language, before in images.items():
            with self.subTest(language=language):
                after, receipt = _stage_or_identity(before, language)
                fixed_rom = ndspy.rom.NintendoDSRom(after)
                fixed_archive = bytes(fixed_rom.getFileByName(LAND_ARCHIVE))
                fixed_narc = ndspy.narc.NARC(fixed_archive)
                changed_members = []
                for index, (old, new) in enumerate(zip(
                        ndspy.narc.NARC(archives[language]).files, fixed_narc.files)):
                    if old != new:
                        changed_members.append(index)
                for member, identity in LANDS.items():
                    old_land = LandData.parse(lands_by_language[language][member])
                    new_land = LandData.parse(bytes(fixed_narc.files[member]))
                    self.assertEqual(tuple(permission(new_land, *cell)
                                           for cell in identity["targets"]),
                                     (0x0400, 0x0400, 0x0400))
                    self.assertEqual((new_land.bgs, new_land.buildings, new_land.model,
                                      new_land.collision),
                                     (old_land.bgs, old_land.buildings, old_land.model,
                                      old_land.collision))
                    self.assertEqual(tuple(permission(new_land, *cell)
                                           for cell in identity["visible"]),
                                     (0x0002, 0x0002, 0x0002))
                    self.assertEqual(tuple(permission(new_land, *cell)
                                           for cell in identity["ordinary"]),
                                     (0x0400,) * len(identity["ordinary"]))
                    self.assertEqual(tuple(permission(new_land, *cell)
                                           for cell in identity["water"]),
                                     (0x0010,) * len(identity["water"]))
                self.assertEqual(changed_members, [87, 102])
                self.assertEqual(receipt["stage"], "invisible-grass")

    def test_archive_replay_checker_and_mutants_are_fail_closed(self):
        """Catches normalization, reapplication, receipt forgery and a reverted word."""
        from sgp131 import invisible_grass as stage

        before = self._exact_en()
        after, receipt = stage.apply(before, "EN")
        old_archive = bytes(ndspy.rom.NintendoDSRom(before).getFileByName(LAND_ARCHIVE))
        new_archive = bytes(ndspy.rom.NintendoDSRom(after).getFileByName(LAND_ARCHIVE))
        self.assertEqual(stage.patch_archive(old_archive), new_archive)
        self.assertEqual(stage.verify(before, after, receipt)["changed_words"], 6)
        self.assertEqual(stage.verify(before, after, receipt)["changed_rom_bytes"], 12)
        self.assertEqual(stage.changed_regions(before),
                         ((receipt["edits"][0]["rom_offset"],
                           receipt["edits"][2]["rom_offset"] + 2),
                          (receipt["edits"][3]["rom_offset"],
                           receipt["edits"][5]["rom_offset"] + 2)))
        with self.assertRaisesRegex(ValueError, "already patched"):
            stage.apply(after, "EN")

        reverted = bytearray(after)
        target = receipt["edits"][0]["rom_offset"]
        struct.pack_into("<H", reverted, target, 0x0002)
        reverted_receipt = copy.deepcopy(receipt)
        reverted_receipt["output_sha256"] = sha256(reverted)
        with self.assertRaisesRegex(ValueError, "postimage"):
            stage.verify(before, bytes(reverted), reverted_receipt)

        forged = copy.deepcopy(receipt)
        forged["edits"][0]["x"] += 1
        with self.assertRaisesRegex(ValueError, "edit receipt"):
            stage.verify(before, after, forged)

    def test_registered_stage_composes_and_replays_for_en_it(self):
        """Catches a producer that works directly but is not admitted by the chain."""
        from sgp131 import mechanics_stages

        for language, (filename, digest, size) in CANDIDATES.items():
            with self.subTest(language=language):
                path = Path(os.environ.get("SGP_HG_F09_ROM_" + language)
                            or ACTIVE / filename)
                _required_asset(self, path, language + " active trial")
                before = path.read_bytes()
                self.assertEqual((sha256(before), len(before)), (digest, size))
                after, receipt = mechanics_stages.run_stage(
                    "invisible-grass", before, language,
                    invariants=lambda *_args: {"confined": True})
                result = mechanics_stages.verify_chain(
                    before, after, ["invisible-grass"], [receipt],
                    lambda image: {"sha256": sha256(image)},
                    invariants=lambda *_args: {"confined": True})
                self.assertEqual(result["stages"], ["invisible-grass"])
                self.assertEqual(result["ui"]["sha256"], sha256(before))
                self.assertEqual(result["output_sha256"], sha256(after))


if __name__ == "__main__":
    unittest.main()
