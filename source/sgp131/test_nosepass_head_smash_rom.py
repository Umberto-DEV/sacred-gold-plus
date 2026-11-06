"""Read-only HG-D01 applicability proof on the exact 1.3.1 EN/IT trials.

The test authenticates each private candidate and the three data archives it
reads.  It decodes the Nosepass egg moves and every Gen-IV personal/level-up
record, without writing a ROM or save.  Paths can be overridden with
SGP_HG_D01_ROM_EN/IT; SGP_HG_D01_REQUIRE_INPUTS=1 turns a missing input into a
failure.
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
    "personal": (
        "a/0/0/2",
        "91cd5b2bbd5d161f66aeec5b1b2122ee18946557fea1415c3ed433755960e3db",
    ),
    "learnsets": (
        "a/0/3/3",
        "811667c3f47eeb9d2c247010b97eed2942544b13230001e8600fefd4deadd27f",
    ),
    "egg_moves": (
        "a/2/2/9",
        "dae7d12bc41dc176ac30700e53dd03ea42da4a20d61745d8b02b80ab2e62a3a2",
    ),
}

NOSEPASS = 299
ARON = 304
GLALIE = 362
FROSLASS = 478
HEAD_SMASH = 457
LAST_GEN_IV_SPECIES = 493


def _sha256(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def input_archives(case, language):
    filename, expected_sha, expected_size = CANDIDATES[language]
    path = Path(os.environ.get("SGP_HG_D01_ROM_" + language)
                or ACTIVE_ROOT / filename)
    if not path.is_file():
        message = f"private {language} 1.3.1 trial missing: {path}"
        if os.environ.get("SGP_HG_D01_REQUIRE_INPUTS") == "1":
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
    case.assertGreaterEqual(len(result["personal"]), LAST_GEN_IV_SPECIES + 1)
    case.assertGreaterEqual(len(result["learnsets"]), LAST_GEN_IV_SPECIES + 1)
    case.assertEqual(len(result["egg_moves"]), 1)
    return result


def decode_egg_moves(member):
    if len(member) % 2:
        raise ValueError("odd egg-move table length")
    words = struct.unpack(f"<{len(member) // 2}H", member)
    result = {}
    species = None
    for word in words:
        if word == 0xFFFF:
            return result
        if word > 20000:
            species = word - 20000
            result[species] = []
        elif species is None:
            raise ValueError("egg move before first species marker")
        else:
            result[species].append(word)
    raise ValueError("egg-move table has no terminator")


def decode_learnset(member):
    if len(member) % 2:
        raise ValueError("odd learnset length")
    result = []
    for word in struct.unpack(f"<{len(member) // 2}H", member):
        if word in (0, 0xFFFF):
            break
        result.append((word >> 9, word & 0x1FF))
    return result


def egg_groups(personal_record):
    return frozenset(personal_record[0x14:0x16])


def can_be_father(personal_record):
    return personal_record[0x10] < 254


def compatible_fathers(personal, learnsets, child, move):
    """Return male-capable species sharing a group and learning ``move``."""
    child_groups = egg_groups(personal[child])
    return tuple(
        species
        for species in range(1, LAST_GEN_IV_SPECIES + 1)
        if can_be_father(personal[species])
        and not child_groups.isdisjoint(egg_groups(personal[species]))
        and any(learned_move == move
                for _level, learned_move in learnsets[species])
    )


class NosepassHeadSmashRomTests(unittest.TestCase):
    def test_exact_trials_have_only_glalie_as_direct_head_smash_father(self):
        for language in CANDIDATES:
            with self.subTest(language=language):
                archives = input_archives(self, language)
                personal = archives["personal"]
                learnsets = {
                    species: decode_learnset(archives["learnsets"][species])
                    for species in range(1, LAST_GEN_IV_SPECIES + 1)
                }
                egg_moves = decode_egg_moves(archives["egg_moves"][0])

                self.assertEqual(tuple(egg_moves[NOSEPASS]),
                                 (222, 205, 153, 38, 335, HEAD_SMASH))
                self.assertEqual((personal[NOSEPASS][0x10],
                                  egg_groups(personal[NOSEPASS])),
                                 (127, frozenset({10})))
                self.assertEqual((personal[ARON][0x10],
                                  egg_groups(personal[ARON]),
                                  (49, HEAD_SMASH) in learnsets[ARON]),
                                 (127, frozenset({1}), True))
                self.assertEqual((personal[GLALIE][0x10],
                                  egg_groups(personal[GLALIE]),
                                  (42, HEAD_SMASH) in learnsets[GLALIE]),
                                 (127, frozenset({6, 10}), True))
                self.assertEqual((personal[FROSLASS][0x10],
                                  egg_groups(personal[FROSLASS]),
                                  any(move == HEAD_SMASH
                                      for _level, move in learnsets[FROSLASS])),
                                 (254, frozenset({6, 10}), False))
                self.assertEqual(
                    compatible_fathers(personal, learnsets, NOSEPASS, HEAD_SMASH),
                    (GLALIE,),
                )
                self.assertTrue(can_be_father(personal[ARON]))
                self.assertTrue(egg_groups(personal[NOSEPASS]).isdisjoint(
                    egg_groups(personal[ARON])))
                self.assertFalse(can_be_father(personal[FROSLASS]))

                without_glalie_head_smash = dict(learnsets)
                without_glalie_head_smash[GLALIE] = [
                    entry for entry in learnsets[GLALIE]
                    if entry[1] != HEAD_SMASH
                ]
                self.assertEqual(
                    compatible_fathers(
                        personal,
                        without_glalie_head_smash,
                        NOSEPASS,
                        HEAD_SMASH,
                    ),
                    (),
                )


if __name__ == "__main__":
    unittest.main()
