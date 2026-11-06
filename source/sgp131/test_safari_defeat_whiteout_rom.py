"""Exact RED/GREEN regression for the SG-01b Route 47 defeat edge."""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

import ndspy.narc
import ndspy.rom

from sgp131 import gifts_audit, gifts_scripts, safari_archives, safari_lifetime
from sgp131 import safari_defeat_whiteout as whiteout


ROOT = Path(__file__).resolve().parents[2]
ROMS = {
    "EN": (
        ROOT / "local/notes/ds-campaign-2026-11-04/final-gates/active/"
        "Sacred-Gold-Plus-1.3.1-EN-active-trial.nds",
        "618f0501d1355f5c7ee6d0301847222fd23a3d67701027190424bf28225fb13d",
    ),
    "IT": (
        ROOT / "local/notes/ds-campaign-2026-11-04/final-gates/active/"
        "Sacred-Gold-Plus-1.3.1-IT-active-trial.nds",
        "171b53b6c47555d54cb82c724569f26e9dfd92f51aa064545dd44b09179d64a0",
    ),
}
METADATA = ROOT / "local/tools/pokeheartgold/tools/py_scripts/scrcmd.json"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def script_member(path):
    rom = ndspy.rom.NintendoDSRom(path.read_bytes())
    archive = ndspy.narc.NARC(rom.getFileByName("a/0/1/2"))
    return bytes(archive.files[260])


def script_archive(path):
    rom = ndspy.rom.NintendoDSRom(path.read_bytes())
    return bytes(rom.getFileByName("a/0/1/2"))


def target(parsed, offset):
    return [destination for _operand, destination, kind
            in parsed.istruzioni[offset].rami if kind != "movement"]


def reachable_names(parsed, start):
    pending = [start]
    seen = set()
    while pending:
        pc = pending.pop()
        if pc in seen:
            continue
        seen.add(pc)
        row = parsed.istruzioni[pc]
        if row.nome in ("End", "Return", "WhiteOut"):
            continue
        pending.extend(destination for _operand, destination, kind in row.rami
                       if kind != "movement")
        if row.nome != "GoTo":
            pending.append(row.fine)
    return [parsed.istruzioni[pc].nome for pc in sorted(seen)]


class SafariDefeatWhiteoutRedGreenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [str(path) for path, _digest in ROMS.values()
                   if not path.is_file()]
        if not METADATA.is_file():
            missing.append(str(METADATA))
        if missing:
            raise unittest.SkipTest(
                "authenticated Safari defeat inputs unavailable: " +
                ", ".join(missing))
        cls.commands = gifts_audit.load_commands(METADATA)

    def test_exact_en_it_red_is_retargeted_to_the_shared_whiteout(self):
        for language, (path, expected_rom_sha) in ROMS.items():
            with self.subTest(language=language):
                data = path.read_bytes()
                self.assertEqual(sha256(data), expected_rom_sha)
                before = script_member(path)
                self.assertEqual(sha256(before),
                                 "bcc71c8ce50440b37fc253f04897ef30e765508162d999c057a7bbe6b7ad01b2")
                parsed_before = gifts_scripts.decode(before, self.commands, 260)
                self.assertEqual(target(parsed_before, 0x61C), [0x6C4])
                broken_names = reachable_names(parsed_before, 0x6C4)
                self.assertNotIn("WhiteOut", broken_names)
                self.assertNotIn("ReleaseAll", broken_names)

                after = whiteout.repair_member(before, self.commands)
                parsed_after = gifts_scripts.decode(after, self.commands, 260)
                self.assertEqual(target(parsed_after, 0x61C), [0x7A4])
                self.assertEqual(parsed_after.istruzioni[0x7A4].nome, "WhiteOut")

    def test_independent_checker_proves_cfg_controls_and_exact_confinement(self):
        before = script_member(ROMS["EN"][0])
        after = whiteout.repair_member(before, self.commands)
        receipt = whiteout.verify_repair(before, after, self.commands)
        self.assertEqual(receipt["before_sha256"],
                         "bcc71c8ce50440b37fc253f04897ef30e765508162d999c057a7bbe6b7ad01b2")
        self.assertEqual(receipt["after_sha256"],
                         "b2570f3e37fd9f3dcbcb2b102f9c2fae2b1db2c1a41a54a755931cf2025cb4d7")
        self.assertEqual(receipt["changed_offsets"], [0x61F, 0x620])
        self.assertEqual(receipt["admitted_window"], [0x61F, 0x623])
        self.assertEqual(receipt["red"], {
            "target": 0x6C4,
            "whiteout_reachable": False,
            "release_all_reachable": False,
        })
        self.assertEqual(receipt["green"]["target"], 0x7A4)
        self.assertEqual(receipt["green"]["tail"],
                         ["WhiteOut", "ReleaseAll", "End"])
        self.assertEqual(receipt["win_control"], {
            "start": 0x623,
            "release_all": 0x65D,
            "end": 0x65F,
        })
        self.assertEqual(receipt["partner_loss_targets"], [0x7A4] * 4)

    def test_member_checker_rejects_reapply_wrong_target_and_outside_mutants(self):
        before = script_member(ROMS["EN"][0])
        after = whiteout.repair_member(before, self.commands)
        with self.assertRaisesRegex(ValueError, "preimage"):
            whiteout.repair_member(after, self.commands)

        wrong_target = bytearray(after)
        struct.pack_into("<i", wrong_target, 0x61F, 0x7A6 - 0x623)
        with self.assertRaisesRegex(ValueError, "postimage|repair"):
            whiteout.verify_repair(before, bytes(wrong_target), self.commands)

        outside = bytearray(after)
        outside[0x600] ^= 1
        with self.assertRaisesRegex(ValueError, "postimage|repair"):
            whiteout.verify_repair(before, bytes(outside), self.commands)

        changed_preimage = bytearray(before)
        changed_preimage[0x600] ^= 1
        with self.assertRaisesRegex(ValueError, "preimage"):
            whiteout.repair_member(bytes(changed_preimage), self.commands)

    def test_exact_archive_geometry_replays_for_en_it_and_rejects_mutants(self):
        expected_archive_before = "c4d17626516dc22d436fb823b0678b19707c2833d3c22cebcec4570bb419dcf8"
        expected_archive_after = "7ffe2ae30e8ce42e12fbfc0842c6cb6c1b743ed3692c14dbec249600b64ab813"
        for language, (path, _rom_sha) in ROMS.items():
            with self.subTest(language=language):
                rom_before = sha256(path.read_bytes())
                before = script_archive(path)
                self.assertEqual(sha256(before), expected_archive_before)
                after = whiteout.repair_archive(before, self.commands)
                self.assertEqual(sha256(after), expected_archive_after)
                self.assertEqual(len(after), len(before))
                old_files = [bytes(member) for member in ndspy.narc.NARC(before).files]
                new_files = [bytes(member) for member in ndspy.narc.NARC(after).files]
                self.assertEqual(len(old_files), 965)
                self.assertEqual([i for i, pair in enumerate(zip(old_files, new_files))
                                  if pair[0] != pair[1]], [260])
                self.assertEqual([i for i, pair in enumerate(zip(before, after))
                                  if pair[0] != pair[1]], [0x3DF77, 0x3DF78])
                archive_receipt = whiteout.verify_archive(
                    before, after, self.commands)
                self.assertEqual(archive_receipt["changed_members"], [260])
                self.assertEqual(archive_receipt["changed_archive_offsets"],
                                 [0x3DF77, 0x3DF78])
                self.assertEqual(whiteout.repair_archive(before, self.commands), after)
                with self.assertRaisesRegex(ValueError, "archive preimage"):
                    whiteout.repair_archive(after, self.commands)
                forged = bytearray(after)
                forged[-1] ^= 1
                with self.assertRaisesRegex(ValueError, "archive postimage|archive repair"):
                    whiteout.verify_archive(before, bytes(forged), self.commands)
                self.assertEqual(sha256(path.read_bytes()), rom_before)

    def test_shared_owner_composes_after_sg01a_without_changing_its_closemsg(self):
        """The one member-260 producer must own SG-01a, SG-02 and SG-01b."""
        for language in ("EN", "IT"):
            path = (ROOT / "local/roms/1.3.1-ui-update-test" /
                    f"Sacred-Gold-Plus-1.3.1-{language}.nds")
            if not path.is_file():
                self.skipTest("authenticated V4 candidate unavailable")
            base = path.read_bytes()
            original = script_member(path)
            sg01a = safari_lifetime.repair_member(original, self.commands)
            delta = safari_archives.derive_safari_scripts(base, language)
            self.assertEqual(delta.producers(), [safari_archives.SCRIPTS])
            self.assertEqual([member.index for member in delta.members], [260])
            final = delta.members[0].after

            with self.subTest(language=language):
                self.assertEqual(sha256(sg01a), whiteout.BEFORE_SHA256)
                self.assertEqual(sha256(final), whiteout.AFTER_SHA256)
                self.assertEqual([index for index, pair in enumerate(zip(sg01a, final))
                                  if pair[0] != pair[1]], [0x61F, 0x620])
                before_rows = gifts_scripts.decode(sg01a, self.commands, 260).istruzioni
                after_rows = gifts_scripts.decode(final, self.commands, 260).istruzioni
                close_offsets = sorted(offset for offset, row in before_rows.items()
                                       if row.nome == "CloseMsg")
                self.assertEqual(close_offsets, sorted(
                    offset for offset, row in after_rows.items()
                    if row.nome == "CloseMsg"))
                self.assertTrue(close_offsets)
                for offset in close_offsets:
                    self.assertEqual(sg01a[offset:before_rows[offset].fine],
                                     final[offset:after_rows[offset].fine])
                safari_lifetime.verify_repair(original, sg01a, self.commands)
                whiteout.verify_repair(sg01a, final, self.commands)
                safari_archives.check_scripts(260, original, final, language)


if __name__ == "__main__":
    unittest.main()
