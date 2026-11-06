"""Read-only HG-F07/HG-F14 RTC contract proof for exact 1.3.1 trials.

The source-only tests pin the retail reference checkout and characterize the
daily-event branches relevant to the Bug-Catching Contest, haircuts and
Buena's Password. The candidate test additionally authenticates the private
EN/IT trials and decodes their scripts and executable slices without writing a
ROM or save.

Set ``SGP_PRET_SOURCE`` to the pinned pokeheartgold checkout. Candidate paths
can be overridden with ``SGP_HG_RTC_ROM_EN/IT``;
``SGP_HG_RTC_REQUIRE_INPUTS=1`` turns a missing input into a failure, and
``SGP_HG_RTC_SOURCE_ONLY=1`` explicitly skips the candidate-only test.
"""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import subprocess
import unittest


HAIRCUT = 0xAA0
BUENA_ANSWERED = 0xAA3
BUG_CONTEST = 0xAA7
BUENA_HEARD = 0xAB6

ROOT = Path(__file__).resolve().parents[2]
PRET = Path(os.environ.get("SGP_PRET_SOURCE")
            or ROOT / "local/tools/pokeheartgold")
PRET_COMMIT = "0985e8718df4f25e64d6507d89c0c97c0d288981"
SOURCE_PINS = {
    "src/unk_02055418.c": "79b402dd1725b089827b991cec0133d8a590da06352f5a84915c10f23044c67b",
    "src/sav_system_info.c": "0a814338a75bf4d7c639ab8b27d781c15ff8038c9bcd75b06a09cd52bdf9be92",
    "src/sys_vars.c": "40ffedeaaeccd974a95195ed001bc776851e0871ef4ab438b262389f37c4170b",
    "src/overlay_36.c": "29009c40b9ec4c7e3e91971430db5004095bbde3950ca10dd456d95f26b38887",
    "src/script_manager.c": "8397db7d5bae3a4e60e52b470342b9d2dd375fc0a7c985937113b607cd6e7c4d",
    "src/field/scrcmd_pokemon_misc.c": "daa96a99436821c7b7330374423e7a34d7772cfb98dd421319af1cd3a15e3cd3",
    "src/application/pokegear/radio/shows/buenas_password.c": "aa1a561da39efb877c5b9f2deb43412fb824f466c548d6f1bd7cc4177cbf0c16",
    "asm/overlay_01_021F3F50.s": "272981aaec20c6bce32837d0ac46162ffe93fea5005c2b532344d52ae63273b2",
    "files/fielddata/script/scr_seq/scr_seq_0151.s": "93aa7c7ee2df382124df4bed48c79812096b4afa77272c80ba189fdff3c4e0b7",
    "files/fielddata/script/scr_seq/scr_seq_0094_D37R0102.s": "432a5010eafb2895eac23bf76dd9fc6b3df71bf15d630da77aa82b4f6418ccd3",
    "files/fielddata/script/scr_seq/scr_seq_0030_D23R0102.s": "4a059c0b94757286195ec2370b9b0d5fd5e89611f26acf56701faa99847a6b5c",
    "tools/py_scripts/scrcmd.json": "fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a",
}
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
SCRIPT_ARCHIVE_SHA = "c4d17626516dc22d436fb823b0678b19707c2833d3c22cebcec4570bb419dcf8"
SCRIPT_MEMBER_SHA = {
    30: "7a6de8fb2fc9bcd972fd9dd9d96f74282e158ff9fc035bc02c2e085019342ba0",
    94: "73475cd8166e074e4c0758d4d6ab0eef9dd27bd49125cff42e2fa1073d80e419",
    151: "9d8aed18b95372a42968252673c321e90b5bdcaa9b3c2007a1070fc65ad8aa40",
}
ARM9_PINS = {
    (0x02055418, 0x19C): "90d1f748343e9451a665946add89bd55ead0a62ba435005daa536824074c1127",
    (0x02055450, 0x28): "da08065ad8d2f5bccb566fbf2a0fb08bc811cefece14a0f6bbd1ecb80654dded",
    (0x02055478, 0x90): "00d70580b9958c9f7f58e03f42ce506638fa707610aa5180fba94cba772fc129",
    (0x02055508, 0xAC): "829fc19d03052f025d677d94df28b879795c9c0589c937e7042ba163d3caacb0",
    (0x02040470, 0x18): "908419a219b957cf78de311b4d0222e19f5bddd99994fea09e39ec8fb6f1112b",
    (0x02066E94, 0x2C): "20017e88d6a9f3e681c81e891da1d08fe242d250ff539c81a86b890c24ce9596",
}
OVERLAY_PINS = {
    1: (0x021E5900, 148064,
        "06e85ab93f575bb98578bbed46376847300d71eed7b20f9396aa4d5a2737af7e"),
    101: (0x021E7740, 80832,
          "4ad17ca990cb750938203d2e4a368fd418cf9fb9d9d83ed22328678fc3d552bb"),
}
SAVE_SLICE_SHA = "e4f3e32f677201c28f458a94e1123d6e103397b79f7e69617c580fa63a9cb8d4"


def _sha256(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _require_path(case, path, label):
    if path.is_file() or path.is_dir():
        return
    message = f"{label} missing: {path}"
    if os.environ.get("SGP_HG_RTC_REQUIRE_INPUTS") == "1":
        case.fail(message)
    case.skipTest(message)


@dataclass(frozen=True)
class RtcState:
    day: int
    penalty_minutes: int
    daily_flags: frozenset
    buena_set: int


def continue_after_clock_change(state, current_day):
    """Model the pinned ``SysInfoRTC_HandleContinueOnNewConsole`` contract."""
    return RtcState(
        day=current_day,
        penalty_minutes=1440,
        daily_flags=state.daily_flags,
        buena_set=state.buena_set,
    )


def natural_day_advance(state, current_day, rng_value):
    """Model the daily subset relevant to HG-F07 and HG-F14."""
    if current_day < state.day:
        return RtcState(
            day=current_day,
            penalty_minutes=state.penalty_minutes,
            daily_flags=state.daily_flags,
            buena_set=state.buena_set,
        )
    if current_day == state.day:
        return state
    buena_set = rng_value % 30
    if buena_set == state.buena_set:
        buena_set = (buena_set + 1) % 30
    return RtcState(
        day=current_day,
        penalty_minutes=state.penalty_minutes,
        daily_flags=frozenset(),
        buena_set=buena_set,
    )


def bug_contest_entry_available(weekday, daily_done, penalty_minutes):
    """Return the script-level decision; the RTC penalty is deliberately inert."""
    del penalty_minutes
    return not daily_done and weekday in (2, 4, 6)


class RtcSourceContractTests(unittest.TestCase):
    def test_reference_checkout_and_inputs_are_exactly_pinned(self):
        _require_path(self, PRET, "pinned pokeheartgold checkout")
        commit = subprocess.run(
            ["git", "-C", str(PRET), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual(commit, PRET_COMMIT)
        self.assertEqual(
            {name: _sha256((PRET / name).read_bytes()) for name in SOURCE_PINS},
            SOURCE_PINS,
        )

    def test_clock_change_reanchors_without_consuming_daily_flags(self):
        before = RtcState(
            day=100,
            penalty_minutes=0,
            daily_flags=frozenset({HAIRCUT, BUENA_ANSWERED,
                                   BUG_CONTEST, BUENA_HEARD}),
            buena_set=17,
        )
        self.assertEqual(
            continue_after_clock_change(before, current_day=103),
            RtcState(
                day=103,
                penalty_minutes=1440,
                daily_flags=before.daily_flags,
                buena_set=17,
            ),
        )

    def test_natural_rollover_clears_daily_flags_and_rotates_buena(self):
        before = RtcState(
            day=103,
            penalty_minutes=720,
            daily_flags=frozenset({HAIRCUT, BUENA_ANSWERED,
                                   BUG_CONTEST, BUENA_HEARD}),
            buena_set=17,
        )
        self.assertEqual(
            natural_day_advance(before, current_day=104, rng_value=17),
            RtcState(
                day=104,
                penalty_minutes=720,
                daily_flags=frozenset(),
                buena_set=18,
            ),
        )

    def test_bug_contest_weekday_gate_is_not_an_rtc_penalty_gate(self):
        observed = tuple(
            bug_contest_entry_available(day, done, penalty)
            for day, done, penalty in (
                (2, False, 1440),
                (4, False, 720),
                (6, False, 1),
                (2, True, 0),
                (1, False, 0),
            )
        )
        self.assertEqual(observed, (True, True, True, False, False))

    def test_backward_day_reanchors_without_daily_rollover(self):
        before = RtcState(
            day=103,
            penalty_minutes=1440,
            daily_flags=frozenset({BUG_CONTEST, BUENA_HEARD}),
            buena_set=17,
        )
        self.assertEqual(
            natural_day_advance(before, current_day=99, rng_value=4),
            RtcState(
                day=99,
                penalty_minutes=1440,
                daily_flags=before.daily_flags,
                buena_set=17,
            ),
        )

    def test_same_day_save_is_a_negative_control_for_buena_rotation(self):
        before = RtcState(
            day=103,
            penalty_minutes=0,
            daily_flags=frozenset({BUENA_HEARD}),
            buena_set=17,
        )
        self.assertEqual(
            natural_day_advance(before, current_day=103, rng_value=4),
            before,
        )


class ExactCandidateContractTests(unittest.TestCase):
    def test_en_it_preserve_the_pinned_rtc_and_daily_script_contract(self):
        if os.environ.get("SGP_HG_RTC_SOURCE_ONLY") == "1":
            self.skipTest("exact candidates disabled by SGP_HG_RTC_SOURCE_ONLY=1")

        import ndspy.narc
        import ndspy.rom
        from sgp12.rom import Arm9, Rom
        from sgp13.mew import load_commands
        from sgp131.gifts_scripts import decode

        _require_path(self, PRET, "pinned pokeheartgold checkout")
        commands, metadata_sha = load_commands(PRET / "tools/py_scripts/scrcmd.json")
        self.assertEqual(metadata_sha, SOURCE_PINS["tools/py_scripts/scrcmd.json"])
        for language, (filename, digest, size) in CANDIDATES.items():
            with self.subTest(language=language):
                path = Path(os.environ.get("SGP_HG_RTC_ROM_" + language)
                            or ACTIVE_ROOT / filename)
                _require_path(self, path, f"private {language} 1.3.1 trial")
                raw = path.read_bytes()
                self.assertEqual((_sha256(raw), len(raw)), (digest, size))
                rom = ndspy.rom.NintendoDSRom(raw)
                script_blob = rom.getFileByName("a/0/1/2")
                self.assertEqual(_sha256(script_blob), SCRIPT_ARCHIVE_SHA)
                scripts = ndspy.narc.NARC(script_blob).files
                self.assertEqual(len(scripts), 965)
                self.assertEqual(
                    {member: _sha256(scripts[member])
                     for member in SCRIPT_MEMBER_SHA},
                    SCRIPT_MEMBER_SHA,
                )

                haircut = decode(bytes(scripts[94]), commands, 94)
                contest = decode(bytes(scripts[151]), commands, 151)
                buena = decode(bytes(scripts[30]), commands, 30)
                self.assertEqual(
                    [(haircut.istruzioni[offset].nome,
                      haircut.istruzioni[offset].args)
                     for offset in (0xA1, 0x1C4, 0x344)],
                    [("GetWeekday", [0x4000]),
                     ("CheckFlag", [HAIRCUT]),
                     ("CheckFlag", [HAIRCUT])],
                )
                self.assertEqual(
                    [(contest.istruzioni[offset].nome,
                      contest.istruzioni[offset].args)
                     for offset in (0x114, 0x11F, 0x4D1)],
                    [("CheckFlag", [BUG_CONTEST]),
                     ("GetWeekday", [0x4000]),
                     ("SetFlag", [BUG_CONTEST])],
                )
                self.assertEqual(
                    [(buena.istruzioni[offset].nome,
                      buena.istruzioni[offset].args)
                     for offset in (0x1D4, 0x1EA, 0x2BA)],
                    [("CheckFlag", [BUENA_HEARD]),
                     ("CheckFlag", [BUENA_ANSWERED]),
                     ("GetBuenasPassword", [0x8000, 0x8001])],
                )

                arm9 = Arm9.from_bytes(raw)
                self.assertEqual(
                    {(address, length): _sha256(arm9.leggi(address, length))
                     for address, length in ARM9_PINS},
                    ARM9_PINS,
                )
                image_reader = Rom(raw)
                overlays = {}
                for overlay_id, expected in OVERLAY_PINS.items():
                    entry, _stream, image = image_reader.immagine_overlay(overlay_id)
                    overlays[overlay_id] = (entry, image)
                    self.assertEqual(
                        (entry["ram"], len(image), _sha256(image)),
                        expected,
                    )
                entry, overlay1 = overlays[1]
                offset = 0x021F43E8 - entry["ram"]
                self.assertEqual(
                    _sha256(overlay1[offset:offset + 0x2C]),
                    SAVE_SLICE_SHA,
                )


if __name__ == "__main__":
    unittest.main()
