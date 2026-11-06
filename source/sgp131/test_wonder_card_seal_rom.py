"""Deterministic, RAM-only reproducer for HG-SEC01.

The bench authenticates the immutable V4 EN/IT candidates and then executes
their real Thumb dispatcher, tag-6 action-table entry, decoration handler and
seal leaf.  Only cartridge-environment helpers are seamed.  The input is an
eight-byte ``(kind, id)`` object in scratch RAM: this file never constructs a
Wonder Card or payload and never writes a ROM, save, or temporary file.

This is a reproducer, not a repair.  In the V4 code, seal IDs 1..80 address the
80-byte inventory at SealCase+288.  ID 81 is therefore the first byte beyond
the object.  The isolated RAM arena makes that boundary observable without
placing any real save data at risk.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import struct
import unittest

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB, Uc
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_SP)


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / "local/experiments/balance493-2026-10-28"
V4 = {
    "EN": ("179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90",
           147345256),
    "IT": ("2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156",
           153228136),
}

ARM9_FILE_OFFSET = 0x4000
ARM9_RAM = 0x02000000
ARM9_SIZE = 0x12B8E4

# Exact V4 anchors.  The hashes cover complete functions, not sampled bytes.
ANCHORS = {
    "ScrCmd_MysteryGift": (0x0204BDA4, 500,
                            "e11565259383216c05af81782231fe585c776ddd270f940a1277484fefd7d60a"),
    "MGCheck_MonDeco": (0x0204C550, 54,
                         "bd710bd718c640c829ec006bc7f1b3ea769ae5e9f8658f31b4b0c42789753551"),
    "MGGive_MonDeco": (0x0204C588, 80,
                        "19e3fa0d24e52efba9cd02e0ce6dbef3ebe0193393518b2bd64b94b08f2a062e"),
    "GiveOrTakeSeal": (0x0202CCAC, 62,
                        "f4a1a78d0d2003f2038eee08f71cafd51e5422414adace599070d785790630a3"),
    "SealCase_CheckSealQuantity": (
        0x0202CD3C, 56,
        "c5a9ab1d64119b27e45843e603ff893d48e2ef64421983293b70a4297ea7d09c"),
    "sScriptMysteryGiftActionTable": (
        0x020FC0E8, 240,
        "cd13b47252033174aa7625c8934e8f5dd034082aaa1e3db122af0bed396e0097"),
}

ACTION_TABLE = 0x020FC0E8
TAG_ENTRIES = {
    1: ((0x0204BF99, 0x0204BFF1, 0x0204C331, 0x0204C36D),
        "da2c7a19e743a7227a62693dc9ca0ce71aa2ac13d8f6a2df3b78e1785812ac63"),
    3: ((0x0204C3BD, 0x0204C3E5, 0x0204C421, 0x0204C45D),
        "365b669e763a6fb77817bdb180f566ad0269fa5180c24b1c1fcc9cc9329035ad"),
    6: ((0x0204C551, 0x0204C589, 0x0204C5D9, 0x0204C631),
        "d91dd8c63355c5170bfaaa3917913be520155602fc42c4e0317e416a1246207e"),
}

DISPATCH = 0x0204BDA4
CHECK = 0x0204C550
GIVE = 0x0204C588
LEAF_WRITE = 0x0202CCAC
LEAF_CHECK = 0x0202CD3C

# Declared seams: script VM and save-container services outside the path under
# test.  The dispatch, table lookup, tag-6 handlers and leaf routines execute
# directly from the authenticated candidate.
SCRIPT_READ_HALFWORD = 0x0203FE2C
SCRIPT_GET_VAR_POINTER = 0x02040374
FIELD_GET_TAG = 0x0204BD80
FIELD_GET_DATA = 0x0204BD8C
FIELD_QUEUE_RECEIVED = 0x0204BD98
SAVE_SEAL_CASE_GET = 0x0202CBE8
COUNT_SEAL_IN_USE = 0x0202CC7C

SCRATCH = 0x02700000
CTX = SCRATCH + 0x1000
FIELD = SCRATCH + 0x2000
DATA = SCRATCH + 0x3000
RESULT = SCRATCH + 0x4000
SEAL_CASE = SCRATCH + 0x10000
ARENA_START = SEAL_CASE - 0x1000
ARENA_SIZE = 0x12000
STOP = SCRATCH + 0x30000
STACK = SCRATCH + 0x3F000
CANARY = 0xA5

SEAL_INVENTORY_OFFSET = 288
SEAL_COUNT = 80
CASES = {
    1: 288,
    80: 367,
    81: 368,
    0xFFFF: 65822,
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _candidate_path(language: str) -> Path:
    override = os.environ.get("SGP_WONDER_CARD_ROM_" + language)
    return Path(override) if override else V4_ROOT / f"candidate-v4-{language}.nds"


def _load_candidate(case: unittest.TestCase, language: str) -> bytes:
    """Authenticate a candidate and retain only its ARM9 image in memory."""
    path = _candidate_path(language)
    if not path.is_file():
        case.skipTest("immutable V4 candidate unavailable: " + str(path))
    expected_hash, expected_size = V4[language]
    case.assertEqual(path.stat().st_size, expected_size,
                     f"{language} V4 candidate size")
    case.assertEqual(_file_sha256(path), expected_hash,
                     f"{language} V4 candidate SHA-256")
    with path.open("rb") as handle:
        header = handle.read(0x30)
        case.assertEqual(struct.unpack_from("<III", header, 0x20),
                         (ARM9_FILE_OFFSET, 0x02000800, ARM9_RAM))
        # The three header words above are file offset, entry point and RAM
        # load address; size is the following independent word.
        case.assertEqual(struct.unpack_from("<I", header, 0x2C)[0], ARM9_SIZE)
        handle.seek(ARM9_FILE_OFFSET)
        arm9 = handle.read(ARM9_SIZE)
    case.assertEqual(len(arm9), ARM9_SIZE)
    return arm9


def _read_arm9(arm9: bytes, address: int, size: int) -> bytes:
    offset = address - ARM9_RAM
    if offset < 0 or offset + size > len(arm9):
        raise AssertionError(f"ARM9 address outside image: 0x{address:08X}+{size}")
    return arm9[offset:offset + size]


class SealReplay:
    """One fresh execution of the authenticated V4 path in isolated RAM."""

    REAL_ENTRIES = {
        DISPATCH: "dispatch",
        CHECK: "check",
        GIVE: "give",
        LEAF_CHECK: "leaf_check",
        LEAF_WRITE: "leaf_write",
    }

    def __init__(self, arm9: bytes, subcommand: int, seal_id: int):
        self.subcommand = subcommand
        self.seal_id = seal_id
        self.script_words = [subcommand] + ([0x8000] if subcommand == 3 else [])
        self.real_path = []
        self.helper_calls = []
        self.queue_calls = 0

        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.cpu.mem_map(ARM9_RAM, 0x200000)
        self.cpu.mem_write(ARM9_RAM, arm9)
        self.cpu.mem_map(SCRATCH, 0x40000)
        self.cpu.mem_write(STOP, b"\x00\xBE")
        self.cpu.mem_write(CTX, bytes(0x100))
        self.cpu.mem_write(FIELD, bytes(0x100))
        self.cpu.mem_write(CTX + 0x80, struct.pack("<I", FIELD))
        self.cpu.mem_write(FIELD + 0x0C, struct.pack("<I", SCRATCH + 0x8000))
        self.cpu.mem_write(DATA, struct.pack("<II", 1, seal_id))
        self.cpu.mem_write(RESULT, b"\xCC\xCC")

        target = SEAL_CASE + SEAL_INVENTORY_OFFSET + seal_id - 1
        if not ARENA_START < target < ARENA_START + ARENA_SIZE - 1:
            raise AssertionError("test target does not fit the isolated arena")
        self.target = target
        self.cpu.mem_write(ARENA_START, bytes([CANARY]) * ARENA_SIZE)
        self.cpu.mem_write(target, b"\x00")
        self.before = bytes(self.cpu.mem_read(ARENA_START, ARENA_SIZE))
        self.cpu.hook_add(UC_HOOK_CODE, self._hook)

    def _return(self, value: int = 0) -> None:
        self.cpu.reg_write(UC_ARM_REG_R0, value)
        self.cpu.reg_write(UC_ARM_REG_PC, self.cpu.reg_read(UC_ARM_REG_LR))

    def _hook(self, cpu, address, _size, _user) -> None:
        if address in self.REAL_ENTRIES:
            self.real_path.append(self.REAL_ENTRIES[address])

        if address == SCRIPT_READ_HALFWORD:
            self.helper_calls.append("script_read")
            if not self.script_words:
                raise AssertionError("dispatcher consumed an unexpected script halfword")
            self._return(self.script_words.pop(0))
        elif address == SCRIPT_GET_VAR_POINTER:
            self.helper_calls.append("var_pointer")
            if cpu.reg_read(UC_ARM_REG_R1) != 0x8000:
                raise AssertionError("dispatcher requested an unexpected variable")
            self._return(RESULT)
        elif address == FIELD_GET_TAG:
            self.helper_calls.append("get_tag")
            self._return(6)
        elif address == FIELD_GET_DATA:
            self.helper_calls.append("get_data")
            self._return(DATA)
        elif address == SAVE_SEAL_CASE_GET:
            self.helper_calls.append("seal_case_get")
            self._return(SEAL_CASE)
        elif address == COUNT_SEAL_IN_USE:
            self.helper_calls.append("count_in_use")
            self._return(0)
        elif address == FIELD_QUEUE_RECEIVED:
            self.helper_calls.append("queue_received")
            self.queue_calls += 1
            self._return(0)

    def run(self) -> dict:
        self.cpu.reg_write(UC_ARM_REG_R0, CTX)
        self.cpu.reg_write(UC_ARM_REG_SP, STACK)
        self.cpu.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.cpu.emu_start(DISPATCH | 1, STOP, count=4096)
        if self.cpu.reg_read(UC_ARM_REG_PC) != STOP:
            raise AssertionError("Mystery Gift dispatcher did not return")
        if self.script_words:
            raise AssertionError("dispatcher left script operands unread")
        after = bytes(self.cpu.mem_read(ARENA_START, ARENA_SIZE))
        differences = [ARENA_START + index
                       for index, pair in enumerate(zip(self.before, after))
                       if pair[0] != pair[1]]
        return {
            "dispatcher_return": self.cpu.reg_read(UC_ARM_REG_R0),
            "result": struct.unpack("<H", bytes(self.cpu.mem_read(RESULT, 2)))[0],
            "target_offset": self.target - SEAL_CASE,
            "target_value": bytes(self.cpu.mem_read(self.target, 1))[0],
            "left_canary": bytes(self.cpu.mem_read(self.target - 1, 1))[0],
            "right_canary": bytes(self.cpu.mem_read(self.target + 1, 1))[0],
            "differences": differences,
            "real_path": list(self.real_path),
            "helper_calls": list(self.helper_calls),
            "queue_calls": self.queue_calls,
        }


class WonderCardSealCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arm9 = {language: _load_candidate(cls(methodName="runTest"), language)
                    for language in V4}

    def test_candidates_pin_every_real_anchor_and_tag6_entry(self):
        reference = self.arm9["EN"]
        for language, arm9 in self.arm9.items():
            with self.subTest(language=language):
                for name, (address, size, expected) in ANCHORS.items():
                    preimage = _read_arm9(arm9, address, size)
                    self.assertEqual(_sha256(preimage), expected, name)
                    self.assertEqual(preimage, _read_arm9(reference, address, size), name)
                for tag, (pointers, expected) in TAG_ENTRIES.items():
                    entry = _read_arm9(arm9, ACTION_TABLE + (tag - 1) * 16, 16)
                    self.assertEqual(struct.unpack("<4I", entry), pointers)
                    self.assertEqual(_sha256(entry), expected)

    def test_real_tag6_check_accepts_invalid_ids_without_mutating_the_canary(self):
        for language, arm9 in self.arm9.items():
            for seal_id, expected_offset in CASES.items():
                with self.subTest(language=language, seal_id=seal_id):
                    result = SealReplay(arm9, 3, seal_id).run()
                    self.assertEqual(result["dispatcher_return"], 0)
                    self.assertEqual(result["result"], 1)
                    self.assertEqual(result["target_offset"], expected_offset)
                    self.assertEqual(result["target_value"], 0)
                    self.assertEqual(result["differences"], [])
                    self.assertEqual(result["real_path"],
                                     ["dispatch", "check", "leaf_check"])
                    self.assertEqual(result["queue_calls"], 0)
                    self.assertEqual(result["helper_calls"].count("get_tag"), 1)
                    self.assertEqual(result["helper_calls"].count("get_data"), 2)

    def test_real_tag6_writer_crosses_the_seal_boundary_one_byte_only(self):
        for language, arm9 in self.arm9.items():
            for seal_id, expected_offset in CASES.items():
                with self.subTest(language=language, seal_id=seal_id):
                    result = SealReplay(arm9, 4, seal_id).run()
                    self.assertEqual(result["dispatcher_return"], 0)
                    self.assertEqual(result["target_offset"], expected_offset)
                    self.assertEqual(result["target_value"], 1)
                    self.assertEqual(result["differences"],
                                     [SEAL_CASE + expected_offset])
                    self.assertEqual(result["left_canary"], CANARY)
                    self.assertEqual(result["right_canary"], CANARY)
                    self.assertEqual(result["real_path"],
                                     ["dispatch", "give", "leaf_write"])
                    self.assertEqual(result["queue_calls"], 1)
                    self.assertEqual(result["helper_calls"].count("get_tag"), 1)
                    self.assertEqual(result["helper_calls"].count("get_data"), 2)

        self.assertEqual(CASES[80], SEAL_INVENTORY_OFFSET + SEAL_COUNT - 1)
        self.assertEqual(CASES[81], SEAL_INVENTORY_OFFSET + SEAL_COUNT)

    def test_non_seal_tags_do_not_alias_the_tag6_check_or_writer(self):
        tag6 = TAG_ENTRIES[6][0]
        for tag in (1, 3):
            with self.subTest(tag=tag):
                self.assertNotEqual(TAG_ENTRIES[tag][0][0], tag6[0])
                self.assertNotEqual(TAG_ENTRIES[tag][0][1], tag6[1])


if __name__ == "__main__":
    unittest.main()
