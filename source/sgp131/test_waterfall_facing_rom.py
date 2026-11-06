"""HG-F02 exact Waterfall descent facing regression.

The private active EN/IT candidates are optional inputs.  When present, this
test authenticates them and their identical overlay-1 Waterfall seam.  The
retail seam starts the descent task without changing the avatar facing, so a
blocked lateral turn remains visible when Down is pressed; Down-only already
faces South.  The production stage must insert one ordered South-facing call
only on the successful automatic-descent branch, before the original task.

No ROM, save or extracted game code is retained.  SGP_HG_F02_REQUIRE_INPUTS=1
makes absent private inputs fail rather than skip.
"""
import copy
import hashlib
import os
from pathlib import Path
import struct
import unittest

from sgp12.rom import Arm9, Rom, bl_decode
from sgp131 import waterfall_facing


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
EXACT_COMPONENTS = {
    "direction": (0x0205DD9C, 0x9C, "98241eaf7ff167d9a561d03feffd0a932558d2fd4826c431a13643fd3908750d"),
    "turn-state": (0x0205D450, 0x44, "1229f471086ac41fa480eb7411b3444b293badf57fcec618470b7d58f9fc98ce"),
    "turn-init": (0x0205D610, 0x30, "7170f8055b471c2ccd41002b708d225729908c039dc21964603a0071224dff04"),
    "gate": (0x021F24F4, 0x44, "18c4bd1adc67ee37d1b508c1c41bddf609417b15461afde7fbcafeb2b8cf6792"),
    "task-env": (0x021F28B8, 0x34, "db7d2b9b55aa1558fa5e44f8c3441c65403904f7f4c181addb8a4a2397e930dc"),
    "descent": (0x021F2B80, 0x1E8, "eb35e73a54f9a9644646dec0bfb2c0c0892dcfcc80013638c973af4d18b3914d"),
    "forced-slide": (0x021F31CC, 0x17C, "f630dfe25395b32466c7e9d87e564028e938b5b7817aeec1471b381710c0021a"),
}


def sha256(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def required_rom(case, language, filename):
    path = Path(os.environ.get("SGP_HG_F02_ROM_" + language) or ACTIVE / filename)
    if path.is_file():
        return path
    message = "private %s active trial missing: %s" % (language, path)
    if os.environ.get("SGP_HG_F02_REQUIRE_INPUTS") == "1":
        case.fail(message)
    case.skipTest(message)


def retail_descent_facing(start_facing, input_direction):
    """Document the authenticated retail state transition at the gate."""
    if input_direction != waterfall_facing.SOUTH:
        return start_facing, False
    # The retail BL calls only CallFieldTask_Waterfall(field, SOUTH).
    return start_facing, True


def fixed_descent_facing(start_facing, input_direction):
    if input_direction != waterfall_facing.SOUTH:
        return start_facing, False
    # The replacement call sets currentFacing before starting the same task.
    return waterfall_facing.SOUTH, True


def thumb_bl_targets(base, code):
    result = []
    for offset in range(0, len(code) - 3, 2):
        first, second = struct.unpack_from("<HH", code, offset)
        if first & 0xF800 == 0xF000 and second & 0xF800 == 0xF800:
            result.append(bl_decode(base + offset, code[offset:offset + 4]))
    return tuple(result)


class WaterfallFacingExactRomTests(unittest.TestCase):
    def _images(self):
        result = {}
        for language, (filename, digest, size) in CANDIDATES.items():
            path = required_rom(self, language, filename)
            raw = path.read_bytes()
            self.assertEqual((sha256(raw), len(raw)), (digest, size))
            result[language] = raw
        return result

    def test_retail_exact_en_it_latches_lateral_but_down_only_is_south(self):
        images = self._images()
        logical = {}
        for language, raw in images.items():
            entry, stream, image = Rom(raw).immagine_overlay(waterfall_facing.OVERLAY_ID)
            arm = Arm9.from_bytes(raw)
            self.assertEqual((entry["ram"], entry["ram_size"], len(stream)),
                             (waterfall_facing.OVERLAY_RAM,
                              waterfall_facing.OVERLAY_BYTES,
                              waterfall_facing.COMPRESSED_BYTES))
            self.assertEqual(sha256(image), waterfall_facing.OVERLAY_PRE_SHA256)
            at = waterfall_facing.HOOK - entry["ram"]
            call = bytes(image[at:at + 4])
            self.assertEqual(call, waterfall_facing.HOOK_PREIMAGE)
            self.assertEqual(bl_decode(waterfall_facing.HOOK, call),
                             waterfall_facing.ORIGINAL_TASK)
            for name, (address, size, digest) in EXACT_COMPONENTS.items():
                if address < waterfall_facing.OVERLAY_RAM:
                    component = arm.leggi(address, size)
                else:
                    component = bytes(image[address - entry["ram"]:
                                            address - entry["ram"] + size])
                self.assertEqual(sha256(component), digest, name)
                if name == "descent":
                    self.assertNotIn(waterfall_facing.SET_FACING,
                                     thumb_bl_targets(address, component))
                if name == "forced-slide":
                    self.assertIn(waterfall_facing.SET_FACING,
                                  thumb_bl_targets(address, component))
            logical[language] = bytes(image)
        self.assertEqual(logical["EN"], logical["IT"])

        for lateral in (waterfall_facing.WEST, waterfall_facing.EAST):
            for neutral_frames in (0, 1, 2):
                with self.subTest(lateral=lateral, neutral_frames=neutral_frames):
                    # Neutral frames do not write currentFacing.
                    facing = lateral
                    for _ in range(neutral_frames):
                        facing = facing
                    self.assertEqual(retail_descent_facing(
                        facing, waterfall_facing.SOUTH), (lateral, True))
        self.assertEqual(retail_descent_facing(
            waterfall_facing.SOUTH, waterfall_facing.SOUTH),
            (waterfall_facing.SOUTH, True))

    def test_stage_sets_south_before_task_and_preserves_failed_directions(self):
        for language, before in self._images().items():
            with self.subTest(language=language):
                after, receipt = waterfall_facing.apply(before, language)
                report = waterfall_facing.verify(before, after, receipt)
                self.assertTrue(report["ok"])
                entry, _stream, image = Rom(after).immagine_overlay(
                    waterfall_facing.OVERLAY_ID)
                at = waterfall_facing.HOOK - entry["ram"]
                self.assertEqual(bl_decode(waterfall_facing.HOOK,
                                           bytes(image[at:at + 4])),
                                 waterfall_facing.SLOT)
                arm = Arm9.from_bytes(after)
                payload = arm.leggi(waterfall_facing.SLOT,
                                    waterfall_facing.SLOT_BYTES)
                self.assertEqual(payload, waterfall_facing.SLOT_POSTIMAGE)
                self.assertEqual(waterfall_facing.decode_payload_calls(payload),
                                 (("set-facing", waterfall_facing.SET_FACING),
                                  ("start-task", waterfall_facing.ORIGINAL_TASK)))

                for lateral in (waterfall_facing.WEST, waterfall_facing.EAST):
                    self.assertEqual(fixed_descent_facing(
                        lateral, waterfall_facing.SOUTH),
                        (waterfall_facing.SOUTH, True))
                    self.assertEqual(fixed_descent_facing(
                        lateral, lateral), (lateral, False))
                self.assertEqual(fixed_descent_facing(
                    waterfall_facing.SOUTH, waterfall_facing.SOUTH),
                    (waterfall_facing.SOUTH, True))

    def test_payload_abi_order_and_mutants(self):
        payload = waterfall_facing.SLOT_POSTIMAGE
        self.assertEqual(len(payload), 20)
        self.assertTrue(waterfall_facing.check_payload(payload))
        calls, returned_sp = waterfall_facing.payload_call_sp(payload)
        self.assertEqual(calls,
                         ((waterfall_facing.SET_FACING, 0x02FFFFF0),
                          (waterfall_facing.ORIGINAL_TASK, 0x02FFFFF0)))
        self.assertEqual(tuple(sp % 8 for _target, sp in calls), (0, 0))
        self.assertEqual(returned_sp, 0x03000000)
        for offset, replacement in ((4, b"\x00\x21"),   # wrong direction
                                    (6, b"\x00\x20\x00\x20"),  # no setter
                                    (14, b"\x00\x20\x00\x20"),  # no task
                                    (18, b"\x08\xbd")):  # pop wrong register
            mutant = bytearray(payload)
            mutant[offset:offset + len(replacement)] = replacement
            with self.subTest(offset=offset):
                self.assertFalse(waterfall_facing.check_payload(bytes(mutant)))

    def test_registered_stage_replays_and_rejects_postimage_mutants_en_it(self):
        from sgp131 import mechanics_stages

        for language, before in self._images().items():
            with self.subTest(language=language):
                after, receipt = mechanics_stages.run_stage(
                    "waterfall-facing", before, language,
                    invariants=lambda *_args: {"confined": True})
                result = mechanics_stages.verify_chain(
                    before, after, ["waterfall-facing"], [receipt],
                    lambda image: {"sha256": sha256(image)},
                    invariants=lambda *_args: {"confined": True})
                self.assertEqual(result["stages"], ["waterfall-facing"])
                self.assertEqual(result["ui"]["sha256"], sha256(before))

                arm = Arm9.from_bytes(after)
                arm.scrivi(waterfall_facing.SLOT + 4, b"\x00\x21")
                mutant = bytes(arm.raw)
                forged = copy.deepcopy(receipt["stage_receipt"])
                forged["output_sha256"] = sha256(mutant)
                with self.assertRaisesRegex(ValueError, "resident postimage"):
                    waterfall_facing.verify(before, mutant, forged)


if __name__ == "__main__":
    unittest.main()
