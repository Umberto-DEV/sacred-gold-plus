"""HG-F13 exact-ROM regression for the follower/menu ledge-jump race.

The private runtime gate opens X during the follower's real command-21 ledge
jump, completes zero/one/two/three Pokemon-page returns, closes the outer menu,
and then repeats the page loop while stationary.  Inputs are immutable and all
ROM/save/output copies are temporary.
"""
from __future__ import annotations

import hashlib
import importlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from sgp12.blz import blz_comprimi_ottimo
from sgp12.rom import Arm9, Rom, bl_decode, bl_thumb


ROOT = Path(__file__).resolve().parents[2]
ACTIVE = ROOT / "local/notes/ds-campaign-2026-11-04/final-gates/active"
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
RUNTIME = Path(os.environ.get("SGP_HG_F13_RUNTIME") or
               ROOT / "local/tools/hg-runtime/hg_runtime-gdb")
FIXTURE = Path(os.environ.get("SGP_HG_F13_FIXTURE") or ROOT /
               "local/notes/ds-campaign-2026-11-04/open-family-audit/hg-f13/"
               "route45-ledge-copied-fixture.sav")
FIXTURE_SHA256 = "7c4c480fc5bb18d27c89f19250a97bceb121b555a7620786a1da352fcdbbf746"

RAM_BASE = 0x02000000
RAM_SIZE = 0x00400000
FIELDSYS_PTR = 0x0203E304
OBJECT_SIZE = 0x12C


def _sha256(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _required(case, path, label):
    if path.is_file():
        return
    message = "private HG-F13 %s unavailable: %s" % (label, path)
    if os.environ.get("SGP_HG_F13_REQUIRE_INPUTS") == "1":
        case.fail(message)
    case.skipTest(message)


def _candidate(case, language):
    filename, digest, size = CANDIDATES[language]
    path = Path(os.environ.get("SGP_HG_F13_ROM_" + language) or ACTIVE / filename)
    _required(case, path, language + " candidate")
    raw = path.read_bytes()
    case.assertEqual((_sha256(raw), len(raw)), (digest, size))
    return raw


def _stage_or_identity(data, language):
    """Identity is intentional only for the first TDD RED."""
    try:
        stage = importlib.import_module("sgp131.follower_menu_jump")
    except ModuleNotFoundError as error:
        if error.name != "sgp131.follower_menu_jump":
            raise
        return bytes(data), {"stage": "identity-tdd-red", "language": language}
    return stage.apply(bytes(data), language)


def _u32(raw, address):
    return struct.unpack_from("<I", raw, address - RAM_BASE)[0]


def _objects(raw):
    if len(raw) != RAM_SIZE:
        raise AssertionError("HG-F13 RAM dump length differs")
    field_system = _u32(raw, _u32(raw, FIELDSYS_PTR))
    manager = _u32(raw, field_system + 0x3C)
    count = _u32(raw, manager + 0x04)
    objects = _u32(raw, manager + 0x124)
    if not 0 < count <= 64:
        raise AssertionError("HG-F13 map-object count differs")
    result = {}
    for index in range(count):
        address = objects + index * OBJECT_SIZE
        blob = raw[address - RAM_BASE:address - RAM_BASE + OBJECT_SIZE]
        if len(blob) != OBJECT_SIZE:
            continue
        flags, object_id = struct.unpack_from("<II", blob, 0)[0], struct.unpack_from("<I", blob, 8)[0]
        if not flags & 1 or object_id not in (253, 255):
            continue
        vector = lambda offset: list(struct.unpack_from("<iii", blob, offset))
        render_pointer = struct.unpack_from("<I", blob, 0x108)[0]
        render = None
        if RAM_BASE <= render_pointer <= RAM_BASE + len(raw) - 12:
            render = list(struct.unpack_from("<iii", raw, render_pointer - RAM_BASE))
        result[object_id] = {
            "current": vector(0x64),
            "position": vector(0x70),
            "facing": vector(0x7C),
            "render": render,
            "command": struct.unpack_from("<I", blob, 0xA4)[0],
            "step": struct.unpack_from("<I", blob, 0xA8)[0],
        }
    if set(result) != {253, 255}:
        raise AssertionError("HG-F13 player/follower objects absent")
    return result


def _run(runtime, rom, save, directory):
    commands = [
        "run 1800", "tap A 2 180", "tap A 2 360", "tap A 2 1200",
        "tap DOWN 4 0", "run 40", "tap DOWN 4 0", "run 5",
        "tap X 2 60", "dump positive0.bin",
    ]
    for index in range(1, 4):
        commands.extend([
            "touch 45 75 4", "run 180", "tap B 2 180",
            "dump positive%d.bin" % index,
        ])
    commands.extend(["tap B 2 180", "dump reset.bin", "tap X 2 60", "dump stationary0.bin"])
    for index in range(1, 4):
        commands.extend([
            "touch 45 75 4", "run 180", "tap B 2 180",
            "dump stationary%d.bin" % index,
        ])
    commands.extend(["tap B 2 180", "quit"])
    script = directory / "commands.script"
    script.write_text("\n".join(commands) + "\n", encoding="utf-8")
    output = directory / "out"
    completed = subprocess.run(
        [str(runtime), "--rom", str(rom), "--sram", str(save),
         "--out", str(output), "--script", str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode:
        raise AssertionError("HG-F13 runtime failed %d:\n%s" %
                             (completed.returncode, completed.stdout[-4000:]))
    return {
        name: _objects((output / (name + ".bin")).read_bytes())
        for name in (["positive%d" % index for index in range(4)] +
                     ["reset"] + ["stationary%d" % index for index in range(4)])
    }


def _assert_fixed_rows(case, rows):
    positive = [rows["positive%d" % index][253] for index in range(4)]
    case.assertEqual((positive[0]["command"], positive[0]["step"]), (21, 1))
    case.assertEqual([row["position"][1] for row in positive], [458752] * 4)
    case.assertEqual([row["facing"][1] for row in positive], [24576] * 4)
    case.assertEqual([row["render"][1] for row in positive], [483328] * 4)

    reset = rows["reset"][253]
    case.assertIn(reset["facing"][1], (-8192, 0))
    case.assertEqual(reset["render"][1], 458752 + reset["facing"][1])
    stationary = [rows["stationary%d" % index][253] for index in range(4)]
    case.assertEqual(len({row["facing"][1] for row in stationary[1:]}), 1)
    case.assertLessEqual(abs(stationary[-1]["facing"][1]), 8192)


class FollowerMenuJumpRuntimeTests(unittest.TestCase):
    maxDiff = None

    def test_command21_menu_returns_do_not_reapply_the_frozen_jump_height(self):
        """Catches field-overlay recreation adding +0x8000 on every page return."""
        _required(self, RUNTIME, "runtime")
        _required(self, FIXTURE, "copied-save fixture")
        self.assertEqual(_sha256(FIXTURE.read_bytes()), FIXTURE_SHA256)

        for language in CANDIDATES:
            before = _candidate(self, language)
            after, _receipt = _stage_or_identity(before, language)
            with self.subTest(language=language), tempfile.TemporaryDirectory(
                    prefix="sgp-hg-f13-%s-" % language.lower()) as temporary:
                directory = Path(temporary)
                rom = directory / "candidate.nds"
                rom.write_bytes(after)
                save = directory / "input-copy.sav"
                shutil.copyfile(FIXTURE, save)
                rows = _run(RUNTIME, rom, save, directory)
                self.assertEqual(_sha256(save.read_bytes()), FIXTURE_SHA256)
                _assert_fixed_rows(self, rows)

    def test_runtime_composes_after_waterfall_facing(self):
        """Catches a composed overlay-1 stream that verifies statically but regresses at runtime."""
        try:
            waterfall = importlib.import_module("sgp131.waterfall_facing")
        except ModuleNotFoundError:
            self.skipTest("HG-F02 producer is not present yet")
        stage = importlib.import_module("sgp131.follower_menu_jump")
        _required(self, RUNTIME, "runtime")
        _required(self, FIXTURE, "copied-save fixture")
        original = _candidate(self, "EN")
        after_waterfall, _ = waterfall.apply(original, "EN")
        after, receipt = stage.apply(after_waterfall, "EN")
        self.assertEqual(receipt["profile"], "after-waterfall-facing")

        with tempfile.TemporaryDirectory(prefix="sgp-hg-f13-composed-") as temporary:
            directory = Path(temporary)
            rom = directory / "candidate.nds"
            rom.write_bytes(after)
            save = directory / "input-copy.sav"
            shutil.copyfile(FIXTURE, save)
            rows = _run(RUNTIME, rom, save, directory)
            self.assertEqual(_sha256(save.read_bytes()), FIXTURE_SHA256)
            _assert_fixed_rows(self, rows)


class FollowerMenuJumpStageTests(unittest.TestCase):
    def test_postimage_semantics_preserve_phase_path_and_abi(self):
        """Proves pause is the only new early exit and all live calls keep aligned SP."""
        stage = importlib.import_module("sgp131.follower_menu_jump")
        table = struct.pack("<48i", *[index * 0x800 for index in range(48)])
        initial_sp = 0x03000000
        self.assertTrue(stage.check_height_helper(stage.FUNCTION_POSTIMAGE, table))

        paused = stage.evaluate_height_helper(
            stage.FUNCTION_POSTIMAGE, paused=1, mode_guard=0,
            phase=3, frame=15, table=table, initial_sp=initial_sp)
        self.assertEqual(paused["result"], 0)
        self.assertEqual([call["target"] for call in paused["calls"]],
                         [stage.PAUSE_CHECK])

        guarded = stage.evaluate_height_helper(
            stage.FUNCTION_POSTIMAGE, paused=0, mode_guard=1,
            phase=3, frame=15, table=table, initial_sp=initial_sp)
        self.assertEqual(guarded["result"], 0)
        self.assertEqual([call["target"] for call in guarded["calls"]],
                         [stage.PAUSE_CHECK, stage.FOLLOWER_MODE_CHECK])

        no_phase = stage.evaluate_height_helper(
            stage.FUNCTION_POSTIMAGE, paused=0, mode_guard=0,
            phase=0, frame=15, table=table, initial_sp=initial_sp)
        self.assertEqual(no_phase["result"], 0)
        self.assertEqual([call["target"] for call in no_phase["calls"]],
                         [stage.PAUSE_CHECK, stage.FOLLOWER_MODE_CHECK,
                          stage.PHASE_GETTER])

        for phase, frame in ((1, 0), (1, 15), (2, 7), (3, 15)):
            with self.subTest(phase=phase, frame=frame):
                actual = stage.evaluate_height_helper(
                    stage.FUNCTION_POSTIMAGE, paused=0, mode_guard=0,
                    phase=phase, frame=frame, table=table,
                    initial_sp=initial_sp)
                self.assertEqual(actual["result"],
                                 (phase - 1) * 16 * 0x800 + frame * 0x800)
                self.assertEqual([call["target"] for call in actual["calls"]],
                                 [stage.PAUSE_CHECK, stage.FOLLOWER_MODE_CHECK,
                                  stage.PHASE_GETTER, stage.FRAME_GETTER])
                self.assertEqual({call["r0"] for call in actual["calls"]},
                                 {stage.MODEL_OBJECT})
                self.assertEqual({call["sp"] % 8 for call in actual["calls"]},
                                 {0})
                self.assertEqual(actual["returned_sp"], initial_sp)

        branch_mutant = bytearray(stage.FUNCTION_POSTIMAGE)
        branch_mutant[12:14] = b"\x00\x20"  # movs r0,#0 replaces paused bne
        call_mutant = bytearray(stage.FUNCTION_POSTIMAGE)
        call_mutant[6:10] = bl_thumb(stage.FUNCTION + 6,
                                     stage.FOLLOWER_MODE_CHECK)
        for label, mutant in (("pause-branch", branch_mutant),
                              ("pause-call", call_mutant)):
            with self.subTest(mutant=label):
                self.assertFalse(stage.check_height_helper(bytes(mutant), table))

    def test_exact_en_it_stage_is_confined_to_the_height_helper_and_overlay_slot(self):
        """Catches the wrong helper, ROM relocation, or physical edits outside overlay 1."""
        stage = importlib.import_module("sgp131.follower_menu_jump")
        for language in CANDIDATES:
            before = _candidate(self, language)
            after, receipt = stage.apply(before, language)
            with self.subTest(language=language):
                self.assertEqual(stage.verify(before, after, receipt),
                                 receipt["verification"])
                self.assertEqual(len(after), len(before))
                self.assertEqual(after[:0x200], before[:0x200])
                self.assertEqual(stage.changed_regions(before),
                                 (tuple(receipt["rom_slot"]),))
                self.assertEqual(stage.spans(before),
                                 (tuple(receipt["rom_slot"]) +
                                  ("overlay 1 follower/menu height helper",),))

                old_entry, old_stream, old_image = Rom(before).immagine_overlay(1)
                new_entry, new_stream, new_image = Rom(after).immagine_overlay(1)
                self.assertEqual(old_entry, new_entry)
                at = stage.FUNCTION - stage.OVERLAY_RAM
                self.assertEqual(bytes(old_image[at:at + stage.FUNCTION_BYTES]),
                                 stage.FUNCTION_PREIMAGE)
                self.assertEqual(bytes(new_image[at:at + stage.FUNCTION_BYTES]),
                                 stage.FUNCTION_POSTIMAGE)
                changed = [index for index, (old, new) in enumerate(
                    zip(old_image, new_image)) if old != new]
                self.assertEqual(len(changed), 28)
                self.assertGreaterEqual(min(changed), at)
                self.assertLess(max(changed), at + stage.FUNCTION_BYTES)
                start, end = receipt["rom_slot"]
                restored = after[:start] + bytes(old_stream) + after[end:]
                self.assertEqual(restored, before)
                self.assertNotEqual(bytes(old_stream), bytes(new_stream))

                first = stage.FUNCTION + 6
                second = stage.FUNCTION + 16
                self.assertEqual(bl_decode(
                    first, bytes(new_image[first - stage.OVERLAY_RAM:
                                           first - stage.OVERLAY_RAM + 4])),
                    stage.PAUSE_CHECK)
                self.assertEqual(bl_decode(
                    second, bytes(new_image[second - stage.OVERLAY_RAM:
                                            second - stage.OVERLAY_RAM + 4])),
                    stage.FOLLOWER_MODE_CHECK)
                self.assertEqual(bytes(new_image[
                    stage.PHASE_TABLE - stage.OVERLAY_RAM:
                    stage.PHASE_TABLE - stage.OVERLAY_RAM + 192]),
                    bytes(old_image[
                        stage.PHASE_TABLE - stage.OVERLAY_RAM:
                        stage.PHASE_TABLE - stage.OVERLAY_RAM + 192]))

    def test_after_waterfall_profile_preserves_the_f02_hook_and_resident_wrapper(self):
        """Catches an integration order/profile that overwrites HG-F02's overlay-1 work."""
        try:
            waterfall = importlib.import_module("sgp131.waterfall_facing")
        except ModuleNotFoundError:
            self.skipTest("HG-F02 producer is not present yet")
        stage = importlib.import_module("sgp131.follower_menu_jump")
        for language in CANDIDATES:
            with self.subTest(language=language):
                original = _candidate(self, language)
                before, _waterfall_receipt = waterfall.apply(original, language)
                after, receipt = stage.apply(before, language)
                self.assertEqual(receipt["profile"], "after-waterfall-facing")
                self.assertEqual(stage.verify(before, after, receipt),
                                 receipt["verification"])
                self.assertEqual(stage.peel(after), before)

                old_entry, _old_stream, old_image = Rom(before).immagine_overlay(1)
                new_entry, _new_stream, new_image = Rom(after).immagine_overlay(1)
                self.assertEqual(old_entry, new_entry)
                hook = waterfall.HOOK - old_entry["ram"]
                self.assertEqual(bytes(new_image[hook:hook + 4]),
                                 bytes(old_image[hook:hook + 4]))
                self.assertEqual(Arm9.from_bytes(after).leggi(
                    waterfall.SLOT, waterfall.SLOT_BYTES),
                    waterfall.SLOT_POSTIMAGE)

    def test_registered_chain_replays_waterfall_then_follower_menu_jump(self):
        """Catches a shared overlay declaration that cannot reconstruct its intermediate."""
        from sgp131 import mechanics_stages as stages

        invariant = lambda *_args: {"confined": True}
        for language in CANDIDATES:
            with self.subTest(language=language):
                original = _candidate(self, language)
                after_waterfall, waterfall_receipt = stages.run_stage(
                    "waterfall-facing", original, language,
                    invariants=invariant)
                final, follower_receipt = stages.run_stage(
                    "follower-menu-jump", after_waterfall, language,
                    invariants=invariant)
                replay = stages.verify_chain(
                    original, final,
                    ["waterfall-facing", "follower-menu-jump"],
                    [waterfall_receipt, follower_receipt],
                    lambda image: {"sha256": _sha256(image)},
                    invariants=invariant)
                self.assertEqual(replay["stages"],
                                 ["waterfall-facing", "follower-menu-jump"])
                self.assertEqual(replay["ui"]["sha256"], _sha256(original))

    def test_checker_rejects_receipt_stream_and_pause_branch_mutants(self):
        """Catches a permissive checker accepting metadata or executable drift."""
        stage = importlib.import_module("sgp131.follower_menu_jump")
        before = _candidate(self, "EN")
        after, receipt = stage.apply(before, "EN")

        forged = dict(receipt)
        forged["profile"] = "forged"
        with self.assertRaisesRegex(ValueError, "receipt identity"):
            stage.verify(before, after, forged)

        start, end = receipt["rom_slot"]
        outside = bytearray(after)
        outside[start - 1] ^= 1
        with self.assertRaisesRegex(ValueError, "outside compressed overlay 1"):
            stage.verify(before, bytes(outside), receipt)

        corrupt = bytearray(after)
        corrupt[start + (end - start) // 2] ^= 1
        with self.assertRaises(ValueError):
            stage.verify(before, bytes(corrupt), receipt)

        entry, _stream, image = Rom(after).immagine_overlay(1)
        mutant = bytearray(image)
        branch = stage.FUNCTION - entry["ram"] + 12
        mutant[branch:branch + 2] = b"\x00\x20"  # movs r0,#0, not bne zero
        encoded = blz_comprimi_ottimo(bytes(mutant),
                                      bersaglio=stage.COMPRESSED_BYTES)
        mutated = after[:start] + encoded + after[end:]
        with self.assertRaises(ValueError):
            stage.verify(before, mutated, receipt)

        with self.assertRaisesRegex(ValueError, "language anchor mismatch"):
            stage.apply(before, "IT")
        with self.assertRaisesRegex(ValueError, "overlay preimage differs"):
            stage.apply(after, "EN")


if __name__ == "__main__":
    unittest.main()
