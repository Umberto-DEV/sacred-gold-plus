"""Class B reproducer for the Water Spout/Eruption trainer-AI HP bug.

The exact EN/IT V4 inputs are read without modification.  The test executes
the real overlay-10 trainer-AI interpreter and the exact command sequence in
member 0 of ``a/0/9/9`` at offset ``0x6450``.  Only three dependencies outside
that command sequence are made deterministic: type effectiveness, speed order
and unsigned division.  The command dispatcher, battler-token resolver, HP
reader, branches and score mutation all execute from the ROM.

The reproducer intentionally describes the current defect; it is not a fix.
It proves that token 0 makes the score follow the target's HP while the user's
HP is ignored, at both native thresholds (50/51 and 70/71).
"""
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys
import unittest

import ndspy.narc
import ndspy.rom
from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_HOOK_CODE,
    UC_HOOK_MEM_INVALID,
    UC_HOOK_MEM_READ,
    UC_MODE_THUMB,
)
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_SP,
)

from sgp12.rom import Arm9, Rom
from . import ai_scoring as ai


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
INPUTS = {
    'EN': (os.environ.get('SGP_AI_WATER_SPOUT_ROM_EN') or V4_ROOT / 'candidate-v4-EN.nds',
           '179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90'),
    'IT': (os.environ.get('SGP_AI_WATER_SPOUT_ROM_IT') or V4_ROOT / 'candidate-v4-IT.nds',
           '2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156'),
}
REQUIRE = os.environ.get('SGP_AI_WATER_SPOUT_REQUIRE_INPUTS') == '1'

OVERLAY_BASE = ai.DRY_SKIN_OVERLAY_BASE
OVERLAY_SIZE = ai.DRY_SKIN_OVERLAY_SIZE
OVERLAY_SHA256 = ai.DRY_SKIN_OVERLAY_SHA256
ARCHIVE = ai.DRY_SKIN_ARCHIVE
MEMBER_SIZE = ai.DRY_SKIN_MEMBER_SIZE
MEMBER_SHA256 = ai.DRY_SKIN_MEMBER_SHA256
SCRIPT_OFFSET = 0x6450
SCRIPT_WORD = SCRIPT_OFFSET // 4
SCRIPT_WORDS = (
    43, 0, 19,
    43, 10, 16,
    43, 20, 13,
    36, 1, 6,
    6, 0, 50, 8,
    76, 4,
    6, 0, 70, 2,
    4, -1,
    77,
)

INTERPRETER = 0x0221C278
TYPE_HELPER = 0x0221F47C
TYPE_EFFECTIVENESS = 0x02251D28
SPEED_ORDER = 0x0224FC48
UNSIGNED_DIVIDE = 0x020F2BA4
BATTLE_SYSTEM_RANDOM = 0x0223BD98

MEMORY_BASE = 0x02000000
SCRIPT = 0x02340000
CTX = 0x02360000
BS = 0x02390000
STACK = 0x023B0000
STOP = 0x023F0000
MEMORY_SIZE = 0x400000

STATE = 0x354
MOVE_SLOT = 0x355
CURRENT_MOVE = 0x356
SCORES = 0x358
FLAGS = 0x364
SCRIPT_SELECTOR = 0x365
ATTACKER = 0x3CF
TARGET = 0x3D0
SCRIPT_BASE = 0x2134
SCRIPT_CURSOR = 0x2138
MOVES = 0x2D4C
MOVE_PRESENT = 0x2D6C
HP = 0x2D8C
MAX_HP = 0x2D90
STATUS = 0x2DAC
BATTLER_STRIDE = 0xC0
FIELD_CONDITION = 0x180
KNOWN_ABILITIES = 0x390
KNOWN_ITEMS = 0x394
MOVE_DATA = 0x3DE
MOVE_DATA_STRIDE = 16
ABILITY = 0x2D67
HELD_ITEM = 0x2DB8


def unicorn_works():
    """Probe in a child: Unicorn 2.1.4 can SIGILL in mem_map on macOS arm64."""
    probe = subprocess.run(
        [sys.executable, '-c',
         'from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB; '
         'u=Uc(UC_ARCH_ARM,UC_MODE_THUMB); u.mem_map(0x2000000,0x1000)'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    return probe.returncode == 0


def exact_input(case, language):
    path, expected = INPUTS[language]
    path = Path(path)
    if not path.is_file():
        reason = 'private %s V4 input missing: %s' % (language, path)
        if REQUIRE:
            case.fail(reason)
        case.skipTest(reason)
    raw = path.read_bytes()
    case.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
    return raw


def artifacts(case, language):
    raw = exact_input(case, language)
    entry, _, overlay = Rom(raw).immagine_overlay(10)
    case.assertEqual((entry['ram'], entry['ram_size']), (OVERLAY_BASE, OVERLAY_SIZE))
    case.assertEqual(hashlib.sha256(overlay).hexdigest(), OVERLAY_SHA256)

    rom = ndspy.rom.NintendoDSRom(raw)
    file_id = rom.filenames.idOf(ARCHIVE)
    case.assertEqual(file_id, ai.DRY_SKIN_ARCHIVE_FILE_ID)
    member = bytes(ndspy.narc.NARC(rom.files[file_id]).files[0])
    case.assertEqual(len(member), MEMBER_SIZE)
    case.assertEqual(hashlib.sha256(member).hexdigest(), MEMBER_SHA256)
    case.assertEqual(struct.unpack_from('<25i', member, SCRIPT_OFFSET), SCRIPT_WORDS)
    return raw, overlay, member


class WaterSpoutBench:
    """One deterministic execution of the real trainer-AI command sequence."""

    def __init__(self, raw, overlay, member, *, faster,
                 script_offset=SCRIPT_OFFSET):
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.mu.mem_map(MEMORY_BASE, MEMORY_SIZE)
        arm9 = Arm9.from_bytes(raw)
        for base, offset, size in arm9.segmenti:
            if MEMORY_BASE <= base and base + size <= MEMORY_BASE + MEMORY_SIZE:
                self.mu.mem_write(base, bytes(arm9.raw[offset:offset + size]))
        self.mu.mem_write(OVERLAY_BASE, overlay)

        # Preserve every script word except table entry zero, which selects the
        # authenticated command sequence requested for this isolated run.
        script = bytearray(member)
        struct.pack_into('<I', script, 0, script_offset // 4)
        self.mu.mem_write(SCRIPT, bytes(script))
        self.mu.mem_write(STOP, b'\x00\xbe')
        self.faster = int(bool(faster))
        self.random_value = 50
        self.script_reads = []
        self.invalid_access = None
        for address in (TYPE_HELPER, TYPE_EFFECTIVENESS, SPEED_ORDER,
                        UNSIGNED_DIVIDE, BATTLE_SYSTEM_RANDOM, STOP):
            self.mu.hook_add(UC_HOOK_CODE, self._hook, begin=address, end=address)
        self.mu.hook_add(UC_HOOK_MEM_READ, self._script_read,
                         begin=SCRIPT, end=SCRIPT + len(member) - 1)
        self.mu.hook_add(UC_HOOK_MEM_INVALID, self._invalid_memory)

    def _return(self, value):
        self.mu.reg_write(UC_ARM_REG_R0, value)
        self.mu.reg_write(UC_ARM_REG_PC, self.mu.reg_read(UC_ARM_REG_LR))

    def _hook(self, uc, address, size, user):
        if address == STOP:
            uc.emu_stop()
        elif address == TYPE_HELPER:
            self._return(11)  # arbitrary move type; the next stub is neutral
        elif address == TYPE_EFFECTIVENESS:
            self._return(40)  # neutral: none of the three early exits matches
        elif address == SPEED_ORDER:
            self._return(self.faster)
        elif address == UNSIGNED_DIVIDE:
            numerator = uc.reg_read(UC_ARM_REG_R0)
            denominator = uc.reg_read(UC_ARM_REG_R1)
            if denominator == 0:
                raise AssertionError('AI HP percentage attempted division by zero')
            self._return(numerator // denominator)
        elif address == BATTLE_SYSTEM_RANDOM:
            self._return(self.random_value)

    def _script_read(self, uc, access, address, size, value, user):
        self.script_reads.append((address - SCRIPT, size))

    def _invalid_memory(self, uc, access, address, size, value, user):
        pc = uc.reg_read(UC_ARM_REG_PC)
        lr = uc.reg_read(UC_ARM_REG_LR)
        registers = tuple(uc.reg_read(register) for register in
                          (UC_ARM_REG_R0, UC_ARM_REG_R1,
                           UC_ARM_REG_R2, UC_ARM_REG_R3))
        self.invalid_access = (address, size, pc, lr, registers)
        return False

    def run(self, *, attacker_hp, target_hp, attacker_status=0,
            target_status=0, move=323, move_effect=None,
            field_condition=0, random_value=50,
            attacker_item=0, target_known_item=0,
            attacker_ability=0, target_known_ability=0):
        context = bytearray(0x30000)
        self.random_value = random_value
        self.script_reads = []
        self.invalid_access = None
        context[STATE] = 0
        context[MOVE_SLOT] = 0
        context[SCORES:SCORES + 4] = bytes((100, 100, 100, 100))
        context[FLAGS] = 0
        context[SCRIPT_SELECTOR] = 0
        context[ATTACKER] = 1
        context[TARGET] = 0
        struct.pack_into('<I', context, SCRIPT_BASE, SCRIPT)
        struct.pack_into('<I', context, SCRIPT_CURSOR, 0)
        struct.pack_into('<I', context, FIELD_CONDITION, field_condition)
        context[KNOWN_ABILITIES] = target_known_ability
        struct.pack_into('<H', context, KNOWN_ITEMS, target_known_item)

        attacker = BATTLER_STRIDE
        struct.pack_into('<H', context, attacker + MOVES, move)
        context[attacker + MOVE_PRESENT] = 1
        context[attacker + ABILITY] = attacker_ability
        struct.pack_into('<H', context, attacker + HELD_ITEM, attacker_item)
        if move_effect is not None:
            struct.pack_into('<H', context,
                             MOVE_DATA + move * MOVE_DATA_STRIDE,
                             move_effect)
        for battler, hp, status in (
                (0, target_hp, target_status),
                (1, attacker_hp, attacker_status)):
            at = battler * BATTLER_STRIDE
            struct.pack_into('<II', context, at + HP, hp, 100)
            struct.pack_into('<I', context, at + STATUS, status)

        self.mu.mem_write(CTX, bytes(context))
        self.mu.reg_write(UC_ARM_REG_R0, BS)
        self.mu.reg_write(UC_ARM_REG_R1, CTX)
        self.mu.reg_write(UC_ARM_REG_SP, STACK)
        self.mu.reg_write(UC_ARM_REG_LR, STOP | 1)
        try:
            self.mu.emu_start(INTERPRETER | 1, STOP, count=1_000_000)
        except Exception as error:
            if self.invalid_access is not None:
                address, size, pc, lr, registers = self.invalid_access
                raise AssertionError(
                    'unmapped guest access at %#x (size %d) from PC %#x; '
                    'LR=%#x r0-r3=%r script_reads=%r' %
                    (address, size, pc, lr, registers,
                     self.script_reads[-12:])) from error
            raise
        return {
            'score': self.mu.mem_read(CTX + SCORES, 1)[0],
            'state': self.mu.mem_read(CTX + STATE, 1)[0],
            'slot': self.mu.mem_read(CTX + MOVE_SLOT, 1)[0],
            'move': struct.unpack('<H', self.mu.mem_read(CTX + CURRENT_MOVE, 2))[0],
            'script_reads': tuple(self.script_reads),
        }


class WaterSpoutRomTests(unittest.TestCase):
    def setUp(self):
        if not unicorn_works():
            self.skipTest('local Unicorn engine SIGILLs before guest execution')

    def test_score_wrongly_follows_target_at_50_51_boundary(self):
        for language in ('EN', 'IT'):
            raw, overlay, member = artifacts(self, language)
            bench = WaterSpoutBench(raw, overlay, member, faster=False)
            with self.subTest(language=language):
                self.assertEqual(bench.run(attacker_hp=100, target_hp=50)['score'], 99)
                self.assertEqual(bench.run(attacker_hp=100, target_hp=51)['score'], 100)
                self.assertEqual(bench.run(attacker_hp=25, target_hp=51)['score'], 100)

    def test_score_wrongly_follows_target_at_70_71_boundary(self):
        for language in ('EN', 'IT'):
            raw, overlay, member = artifacts(self, language)
            bench = WaterSpoutBench(raw, overlay, member, faster=True)
            with self.subTest(language=language):
                self.assertEqual(bench.run(attacker_hp=100, target_hp=70)['score'], 99)
                self.assertEqual(bench.run(attacker_hp=100, target_hp=71)['score'], 100)
                self.assertEqual(bench.run(attacker_hp=25, target_hp=71)['score'], 100)

    def test_attacker_hp_is_ignored_when_target_is_fixed(self):
        raw, overlay, member = artifacts(self, 'EN')
        bench = WaterSpoutBench(raw, overlay, member, faster=False)
        low = bench.run(attacker_hp=25, target_hp=100)
        high = bench.run(attacker_hp=100, target_hp=100)
        self.assertEqual(low['score'], 100)
        self.assertEqual(high['score'], 100)
        self.assertEqual(low['state'], 2)
        self.assertEqual(low['slot'], 4)
        # The interpreter clears CURRENT_MOVE again while skipping the three
        # empty slots; reaching slot 4 and state 2 proves normal completion.
        self.assertEqual(low['move'], 0)

    def test_two_token_fix_makes_both_thresholds_follow_the_user(self):
        for language in ('EN', 'IT'):
            raw, overlay, member = artifacts(self, language)
            fixed, report = ai.patch_water_spout_member(member)
            self.assertEqual(report['changed_offsets'], [0x6484, 0x649C])
            with self.subTest(language=language, threshold=50):
                bench = WaterSpoutBench(raw, overlay, fixed, faster=False)
                self.assertEqual(bench.run(attacker_hp=50, target_hp=100)['score'], 99)
                self.assertEqual(bench.run(attacker_hp=51, target_hp=25)['score'], 100)
            with self.subTest(language=language, threshold=70):
                bench = WaterSpoutBench(raw, overlay, fixed, faster=True)
                self.assertEqual(bench.run(attacker_hp=70, target_hp=100)['score'], 99)
                self.assertEqual(bench.run(attacker_hp=71, target_hp=25)['score'], 100)


if __name__ == '__main__':
    unittest.main()
