"""HG-T10 exact scene-version repair in compressed overlay 2.

Class A proves the selector and instruction postimages without a ROM.  Class B
authenticates the formal EN/IT preimages, applies the producer in memory and
checks confinement, replay and the exact Lugia/Ho-Oh decisions.  No file is
written.
"""
import hashlib
import os
from pathlib import Path
import unittest

from sgp12.rom import bl_decode
from . import legendary_scene_version as stage


ROOT = Path(__file__).resolve().parents[2]
ACTIVE = ROOT / "local/notes/ds-campaign-2026-11-05/final-gates/active"
CANDIDATES = {
    "EN": ("Sacred-Gold-Plus-1.3.1-EN-portable-trial.nds",
           "5c5611844678d26bdc5677855da3aacbc1dd1700f97afec249b24532f2362f15",
           152786376),
    "IT": ("Sacred-Gold-Plus-1.3.1-IT-portable-trial.nds",
           "c5a45d169e04fd85f17889f201ba7c6fe6f5d4ad43243b6a043a5ab848777f97",
           159029292),
}


def digest(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def candidate(case, language):
    filename, expected, size = CANDIDATES[language]
    path = Path(os.environ.get("SGP_HG_T10_ROM_" + language) or ACTIVE / filename)
    if not path.is_file():
        message = "private HG-T10 %s candidate unavailable: %s" % (language, path)
        if os.environ.get("SGP_HG_T10_REQUIRE_INPUTS") == "1":
            case.fail(message)
        case.skipTest(message)
    data = path.read_bytes()
    case.assertEqual((digest(data), len(data)), (expected, size))
    return data


class SelectorUnitTests(unittest.TestCase):
    def test_only_lugia_map_selects_soulsilver_scene_assets(self):
        self.assertEqual(stage.select_scene_version(244), 8)
        for map_id in (0, 1, 243, 245, 340, 0xFFFF):
            with self.subTest(map_id=map_id):
                self.assertEqual(stage.select_scene_version(map_id), 7)

    def test_postimages_preserve_calls_and_encode_exact_map_selector(self):
        self.assertTrue(stage.check_clear_postimage(stage.CLEAR_POSTIMAGE))
        self.assertTrue(stage.check_bird_postimage(stage.BIRD_POSTIMAGE))
        self.assertTrue(stage.check_lugia_postimage(stage.LUGIA_POSTIMAGE))
        self.assertEqual(stage.decode_clear_calls(stage.CLEAR_POSTIMAGE),
                         stage.CLEAR_CALL_TARGETS)
        self.assertEqual(stage.decode_bird_calls(stage.BIRD_POSTIMAGE),
                         stage.BIRD_CALL_TARGETS)
        self.assertEqual(
            bl_decode(stage.BIRD_FUNCTION + stage.BIRD_TASK_CALL_OFFSET,
                      stage.BIRD_POSTIMAGE[stage.BIRD_TASK_CALL_OFFSET:
                                           stage.BIRD_TASK_CALL_OFFSET + 4]),
            stage.TASK_MANAGER_CALL,
        )

    def test_selector_mutants_are_rejected(self):
        rows = ((stage.CLEAR_POSTIMAGE, stage.CLEAR_SELECTOR_OFFSET,
                 stage.check_clear_postimage),
                (stage.BIRD_POSTIMAGE, stage.BIRD_SELECTOR_OFFSET,
                 stage.check_bird_postimage))
        for code, offset, checker in rows:
            for label, mutation in (("map", bytes.fromhex("f32b")),
                                    ("lugia-version", bytes.fromhex("0231")),
                                    ("default-version", bytes.fromhex("0821"))):
                mutant = bytearray(code)
                if label == "map":
                    mutant[offset + 6:offset + 8] = mutation
                elif label == "lugia-version":
                    mutant[offset + 10:offset + 12] = mutation
                else:
                    mutant[offset:offset + 2] = mutation
                with self.subTest(function=len(code), mutant=label):
                    self.assertFalse(checker(bytes(mutant)))


class ExactRomTests(unittest.TestCase):
    def test_en_it_apply_verify_and_peel_are_exact(self):
        for language in CANDIDATES:
            before = candidate(self, language)
            after, receipt = stage.apply(before, language)
            with self.subTest(language=language):
                self.assertEqual(stage.verify(before, after, receipt),
                                 receipt["verification"])
                self.assertEqual(len(after), len(before))
                self.assertEqual(after[:0x200], before[:0x200])
                self.assertEqual(stage.peel(after), before)
                self.assertEqual(stage.changed_regions(before),
                                 (tuple(receipt["rom_slot"]),))
                self.assertTrue(receipt["save_layout_unchanged"])
                self.assertTrue(receipt["rom_geometry_unchanged"])

    def test_reapplication_foreign_preimage_and_receipt_forgery_are_refused(self):
        before = candidate(self, "EN")
        after, receipt = stage.apply(before, "EN")
        with self.assertRaises(ValueError):
            stage.apply(after, "EN")
        foreign = bytearray(before)
        foreign[stage.overlay_file_span(before)[0]] ^= 1
        with self.assertRaises(ValueError):
            stage.apply(bytes(foreign), "EN")
        forged = dict(receipt)
        forged["output_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            stage.verify(before, after, forged)


if __name__ == "__main__":
    unittest.main()
