"""Class B: run the real post-KO replacement function from the V4 EN/IT ROMs.

The native function ov12_02258800 (0x02258800..0x02258BA0) is executed from its
entry in Unicorn, original and patched, with the real overlay 12 image and the
real ARM9. Only calls that leave the function's own concerns are replaced by
Python stubs at their native entry addresses (all other instructions, including
the real type helper CalculateTypeEffectiveness 0x0225264C, its signed-division
helper 0x020F2998 and MaskOfFlagNo 0x020726C0, are executed natively):

    0x0223A7E4 BattleSystem_GetBattleContext   0x0223A7E0 BattleSystem_GetBattleType
    0x0223AB6C BattleSystem_GetBattlerIdPartner 0x02253DA0 Battler_GetRandomOpposingBattlerId
    0x0223A834 BattleSystem_GetPartySize       0x0223A880 BattleSystem_GetPartyMon
    0x0206E540 GetMonData (species/egg 0xAE, HP 0xA3, types 0xB1/0xB2, moves 0x36+n, 0x0A)
    0x0224EDE0 GetBattlerVar (types 0x1B/0x1C of the target)
    0x02258BB4 ov12_02258BB4 (move type)       0x022527CC GetBattlerAbility
    0x02255830 GetBattlerHeldItemEffect        0x02252054 ov12_02252054 (super-effective flag)
    0x0223AB1C BattleSystem_GetFieldSide       0x02256FF8 CalcMoveDamage
    0x02251D28 ov12_02251D28 (damage modifiers / immunity flags)

The scenarios are synthetic and say nothing about natural encounters; they are
CPU coverage of the selected instructions, not Android gameplay.

Inputs: SGP_AI_ROM_EN / SGP_AI_ROM_IT (defaults: the immutable V4 candidates in
local/experiments/balance493-2026-10-28). Their SHA-256 is checked before use.
Missing inputs skip with a reason, unless SGP_AI_REQUIRE_INPUTS=1: then they fail.
Nothing is written to disk.
"""
import hashlib
import os
from pathlib import Path
import random
import struct
import unittest
import ndspy.narc
import ndspy.rom
from sgp12.blz import ndspy_decomprimi_sicuro

from . import ai_scoring as ai

try:
    from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_MODE_THUMB, UC_HOOK_CODE
    from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                                   UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                                   UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
                                   UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR)
    UNICORN_ERROR = None
except ImportError as error:  # reported by inputs(), failing under SGP_AI_REQUIRE_INPUTS=1
    UNICORN_ERROR = str(error)

from sgp12.rom import Arm9, Rom, crc16

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}
OVERLAY_SHA256 = 'c426e8176612f5b9f5cd8d24099b1be57e1f3ce71f90dbf5a718cfe87092b982'
BASE = ai.OVERLAY_BASE
FUNCTION = 0x02258800
HELPER = 0x0225264C
TYPE_TABLE_POINTER = 0x02252694  # literal pool word read by the helper
COMPARE = 0x02258942             # bhs after cmp r1,r0 in the stage-one loop
CONTEXT_ADDRESS = 0x02258934     # 20 guard bytes, written out independently of the module under test
CONTEXT = bytes.fromhex('1399 0818 0006 000e 1390 1299 8142 0dd2 1398 1290'.replace(' ', ''))
# lsls r1,r0,#24; lsrs r1,r1,#24; str r1,[sp,#0x4c]  and  nop where [sp,#0x4c] used to be reloaded into r0
SITES = ((0x02258938, bytes.fromhex('0006000e1390'), bytes.fromhex('0106090e1391')),
         (0x02258944, bytes.fromhex('1398'), bytes.fromhex('c046')))
CHANGED = [0x02258938, 0x0225893A, 0x0225893D, 0x02258944, 0x02258945]  # bytes whose value differs
EFFECTIVENESS_SITE = (0x02252202, bytes.fromhex('0420'), bytes.fromhex('0c20'))
ALL_CHANGED = [0x02252202, *CHANGED]

# Native entries replaced by Python (name, ABI used by the function under test).
STUBS = {
    0x0223A7E4: 'GetBattleContext', 0x0223A7E0: 'GetBattleType', 0x0223AB6C: 'GetBattlerIdPartner',
    0x02253DA0: 'GetRandomOpposingBattlerId', 0x0223A834: 'GetPartySize', 0x0223A880: 'GetPartyMon',
    0x0206E540: 'GetMonData', 0x0224EDE0: 'GetBattlerVar', 0x02258BB4: 'GetMoveType',
    0x022527CC: 'GetBattlerAbility', 0x02255830: 'GetBattlerHeldItemEffect',
    0x02252054: 'CheckSuperEffective', 0x0223AB1C: 'GetFieldSide', 0x02256FF8: 'CalcMoveDamage',
    0x02251D28: 'ApplyDamageModifiers',
}
CTX, BS, MON, STACK_TOP, STOP = 0x02380000, 0x02390000, 0x02391000, 0x023B8000, 0x023F0000
CANARY = b'\xA5' * 0x100
SENTINEL = 0xA5A5A5A5
TYPES = range(18)
REQUIRE = 'SGP_AI_REQUIRE_INPUTS'

_INPUTS = {}


# ----------------------------------------------------------------- inputs

class Inputs:
    def __init__(self, language, path):
        self.language, self.path = language, path
        self.data = path.read_bytes()
        self.rom = Rom(self.data)
        self.arm9 = Arm9(path)
        self.entry, self.crudo, self.image = self.rom.immagine_overlay(12)
        self._patched = self._applied = None

    @property
    def patched(self):
        if self._patched is None:
            self._patched = ai.patch_overlay(self.image)
        return self._patched

    @property
    def applied(self):
        if self._applied is None:
            self._applied = ai.apply(self.data, self.language)
        return self._applied


def inputs(case, language):
    if UNICORN_ERROR:
        message = 'unicorn is required for the native execution tests: ' + UNICORN_ERROR
        if os.environ.get(REQUIRE) == '1':
            case.fail(message)
        case.skipTest(message)
    if language in _INPUTS:
        return _INPUTS[language]
    variable = 'SGP_AI_ROM_' + language
    path = Path(os.environ.get(variable) or EXPERIMENT / f'candidate-v4-{language}.nds')
    if not path.is_file():
        message = f'{variable} (default {path}) is required; set {REQUIRE}=1 to fail instead of skip'
        if os.environ.get(REQUIRE) == '1':
            case.fail(message)
        case.skipTest(message)
    expected, size = V4[language]
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    case.assertEqual(digest.hexdigest(), expected, 'only the immutable V4 input is admitted')
    case.assertEqual(path.stat().st_size, size)
    _INPUTS[language] = Inputs(language, path)
    return _INPUTS[language]


# ------------------------------------------------- what the game's loader accepts

LOADER_DECODE, LOADER_DECODE_END = 0x02000970, 0x020009F4  # MIi_UncompressBackward and the cache maintenance after its loop


def loader_image(data, rom):
    """Overlay 12 as FS_LoadOverlayImage + MIi_UncompressBackward leave it in RAM, or None if the load fails.

    The ARM code is the game's own (read from the ARM9 and executed). Only the file-system glue is modelled:
    the binary size is the y9 size when the compressed flag (bit 0) is set, and FS_ReadFile stops at the FAT
    end, so a size beyond the file fails (FSi_ReadFileCore clamps, FS_LoadOverlayImage compares). Flag bit 1
    (digest) only matters when the boot type is 2 (multiboot download), never on a cartridge or in melonDS."""
    fat, y9 = struct.unpack_from('<II', rom, 0x48)[0], struct.unpack_from('<I', rom, 0x50)[0]
    _, ram, ram_size, _, _, _, file_id, word = struct.unpack_from('<8I', rom, y9 + 32 * 12)
    start, end = struct.unpack_from('<II', rom, fat + 8 * file_id)
    size = word & 0xFFFFFF if word >> 24 & 1 else ram_size
    if size > end - start:
        return None
    if not word >> 24 & 1:
        return bytes(rom[start:start + size])
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(0x02000000, 0x400000)
    uc.mem_write(LOADER_DECODE, data.arm9.leggi(LOADER_DECODE, LOADER_DECODE_END - LOADER_DECODE))
    uc.mem_write(ram, bytes(rom[start:start + size]))
    uc.reg_write(UC_ARM_REG_R0, ram + size)
    uc.reg_write(UC_ARM_REG_SP, 0x023F0000)
    try:
        uc.emu_start(LOADER_DECODE, LOADER_DECODE_END, count=5_000_000)
    except UcError:
        return None
    return bytes(uc.mem_read(ram, ram_size))


def rewrite(rom, *, stream=None, fat_end=None, y9_word=None, edits=()):
    """Copy of ``rom`` with overlay 12's stream, FAT end and y9 word replaced, plus (offset, byte) edits."""
    out = bytearray(rom)
    fat, y9 = struct.unpack_from('<II', out, 0x48)[0], struct.unpack_from('<I', out, 0x50)[0]
    file_id = struct.unpack_from('<I', out, y9 + 32 * 12 + 24)[0]
    start = struct.unpack_from('<I', out, fat + 8 * file_id)[0]
    if stream is not None:
        out[start:start + len(stream)] = stream
    if fat_end is not None:
        struct.pack_into('<I', out, fat + 8 * file_id + 4, fat_end)
    if y9_word is not None:
        struct.pack_into('<I', out, y9 + 32 * 12 + 28, y9_word)
    for offset, value in edits:
        out[offset] = value
    return bytes(out)


def with_hashes(receipt, before, forged):
    """The best receipt a forger can produce: both hashes recomputed for the forged ROM."""
    return {**receipt, 'writer': {**receipt['writer'], 'ingresso_sha256': hashlib.sha256(before).hexdigest(),
                                  'uscita_sha256': hashlib.sha256(forged).hexdigest()}}


# --------------------------------------------------------------- scenarios

class Slot:
    def __init__(self, species, types, hp=100, moves=(0, 0, 0, 0)):
        self.species, self.types, self.hp, self.moves = species, tuple(types), hp, tuple(moves)


class Scenario:
    """One post-KO decision: the opposing trainer's party against one visible target."""

    def __init__(self, slots, target_types=(5, 8), battler=1, partner=3, battle_type=0,
                 current=None, pending=None, superefficient=(), move_type=None, damage=None,
                 immune=(), no_score=(), target=0):
        self.slots, self.target_types = list(slots), tuple(target_types)
        self.battler, self.partner, self.battle_type, self.target = battler, partner, battle_type, target
        self.current = {battler: 0} if current is None else dict(current)
        self.pending = {} if pending is None else dict(pending)
        self.superefficient, self.immune, self.no_score = set(superefficient), set(immune), set(no_score)
        self.move_type, self.damage = dict(move_type or {}), dict(damage or {})


def full_moves(slot):
    return tuple(1 + slot * 4 + k for k in range(4))


# ------------------------------------------------------------ the emulator

class Native:
    """Unicorn execution of one overlay image with stubs at the declared entries."""

    def __init__(self, arm9, overlay_image, *, execute_effectiveness=False):
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        uc.mem_map(0x02000000, 0x400000)
        uc.mem_map(0x01FF8000, 0x4000)
        uc.mem_map(0x027E0000, 0x20000)
        for start, offset, size in arm9.segmenti:
            uc.mem_write(start, bytes(arm9.raw[offset:offset + size]))
        uc.mem_write(BASE, overlay_image)
        for address in STUBS:
            if execute_effectiveness and address == 0x02252054:
                continue
            uc.hook_add(UC_HOOK_CODE, self._stub, None, address, address)
        uc.hook_add(UC_HOOK_CODE, self._compare, None, COMPARE, COMPARE)
        self.execute_effectiveness = execute_effectiveness
        self.scn, self.error, self.log, self.compares, self.stored, self.seed = None, None, [], [], [], 0

    # -- helpers
    def reg(self, name):
        return self.uc.reg_read(name)

    def stack(self, k):
        return struct.unpack('<I', bytes(self.uc.mem_read(self.reg(UC_ARM_REG_SP) + 4 * k, 4)))[0]

    def put(self, address, value):
        self.uc.mem_write(address, struct.pack('<I', value))

    def _compare(self, uc, address, size, user):
        sp = self.reg(UC_ARM_REG_SP)
        best, stored = struct.unpack('<I', bytes(uc.mem_read(sp + 0x48, 4)))[0], struct.unpack('<I', bytes(uc.mem_read(sp + 0x4C, 4)))[0]
        self.compares.append((best, self.reg(UC_ARM_REG_R0), bool(self.reg(UC_ARM_REG_CPSR) >> 29 & 1)))
        self.stored.append(stored)

    def _stub(self, uc, address, size, user):
        try:
            result = self._dispatch(STUBS[address])
        except Exception as error:  # a hook must not raise through Unicorn
            self.error = error
            uc.emu_stop()
            return
        uc.reg_write(UC_ARM_REG_R0, result & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_PC, self.reg(UC_ARM_REG_LR))

    def _dispatch(self, name):
        s, r0, r1, r2, r3 = self.scn, *(self.reg(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        slot = lambda: (r0 - MON) // 0x100
        if name == 'GetBattleContext':
            return CTX
        if name == 'GetBattleType':
            return s.battle_type
        if name == 'GetBattlerIdPartner':
            self.log.append((name, r1))
            return s.partner
        if name == 'GetRandomOpposingBattlerId':
            assert r1 == CTX
            self.log.append((name, r2))
            self.seed = (self.seed * 1103515245 + 12345) & 0xFFFFFFFF
            return s.target
        if name == 'GetPartySize':
            return len(s.slots)
        if name == 'GetPartyMon':
            self.log.append((name, r1, r2))
            return MON + r2 * 0x100
        if name == 'GetMonData':
            mon, ident = s.slots[slot()], r1
            self.log.append((name, slot(), ident))
            if ident == 0xAE:
                return mon.species
            if ident == 0xA3:
                return mon.hp
            if ident in (0xB1, 0xB2):
                return mon.types[ident - 0xB1]
            if 0x36 <= ident <= 0x39:
                return mon.moves[ident - 0x36]
            if ident == 0x0A:
                return 0x1000 + slot()
            raise AssertionError('unexpected GetMonData id %#x' % ident)
        if name == 'GetBattlerVar':
            assert r0 == CTX and r1 == s.target and r2 in (0x1B, 0x1C) and r3 == 0, (r0, r1, r2, r3)
            self.log.append((name, r1, r2))
            return s.target_types[r2 - 0x1B]
        if name == 'GetMoveType':
            self.log.append((name, slot_of(r2), r3))
            return s.move_type.get(r3, 0)
        if name in ('GetBattlerAbility', 'GetBattlerHeldItemEffect'):
            self.log.append((name, r1))
            return 0
        if name == 'CheckSuperEffective':
            self.log.append((name, r1, r2))
            self.put(self.stack(4), 2 if r1 in s.superefficient else 0)
            return 0
        if name == 'GetFieldSide':
            self.log.append((name, r1))
            return 0
        if name == 'CalcMoveDamage':
            self.log.append((name, r2))
            return s.damage.get(r2, 0)
        if name == 'ApplyDamageModifiers':
            self.log.append((name, r2, self.stack(2)))
            self.put(self.stack(3), 0x00140808 if r2 in s.immune else 0)
            return self.stack(2)
        raise AssertionError(name)

    # -- running
    def _start(self, entry, args, scn):
        uc = self.uc
        self.scn, self.error, self.log, self.compares, self.stored = scn, None, [], [], []
        uc.mem_write(CTX, bytes(0x4000))
        uc.mem_write(STACK_TOP - 0x1000, bytes(0x1000))
        uc.mem_write(STACK_TOP, CANARY)
        if scn is not None:
            for k in range(4):
                uc.mem_write(CTX + 0x219C + k, bytes([scn.current.get(k, 6)]))
                uc.mem_write(CTX + 0x21A4 + k, bytes([scn.pending.get(k, 6)]))
            for move in scn.no_score:
                uc.mem_write(CTX + 0x3E1 + 16 * move, b'\x01')
        self.before = bytes(uc.mem_read(CTX, 0x4000))
        for register, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            uc.reg_write(register, value)
        for register in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                         UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11):
            uc.reg_write(register, SENTINEL)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        uc.emu_start(entry | 1, STOP, count=3_000_000)
        if self.error:
            raise self.error
        assert self.reg(UC_ARM_REG_PC) & ~1 == STOP, 'the routine did not return'

    def run(self, scn, strict=True):
        """Execute the native decision; return (slot, observations). ``strict`` also asserts the stored word."""
        self.seed = 0
        self._start(FUNCTION, (BS, scn.battler), scn)
        uc = self.uc
        for register in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8,
                         UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11):
            assert self.reg(register) == SENTINEL, 'callee-saved registers changed'
        assert self.reg(UC_ARM_REG_SP) == STACK_TOP, 'stack pointer changed'
        assert bytes(uc.mem_read(STACK_TOP, 0x100)) == CANARY, 'caller frame canary changed'
        assert bytes(uc.mem_read(CTX, 0x4000)) == self.before, 'the function modified the battle context'
        for (best, score, carry), stored in zip(self.compares, self.stored):
            assert carry == (best >= score), ('carry flag differs from the unsigned best >= score', best, score, carry)
            assert not strict or stored == score & 0xFF, ('stage-two word [sp+0x4c] must stay the native 8-bit value', stored, score)
        return self.reg(UC_ARM_REG_R0), list(self.compares)

    def helper(self, attack, first, second):
        self.scn = None
        self.seed = 0
        self._start(HELPER, (attack, first, second), None)
        assert self.reg(UC_ARM_REG_SP) == STACK_TOP
        assert all(self.reg(r) == SENTINEL for r in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7))
        return self.reg(UC_ARM_REG_R0)

    def effectiveness_flags(self, move_type, first, second, initial=0):
        """Execute ov12_02252054 itself; requires its entry not to be stubbed."""
        assert self.execute_effectiveness
        flag = CTX + 0x3000
        uc = self.uc
        uc.mem_write(CTX, bytes(0x4000))
        uc.mem_write(STACK_TOP - 0x1000, bytes(0x1000))
        uc.mem_write(flag, struct.pack('<I', initial))
        uc.mem_write(STACK_TOP, struct.pack('<5I', 0, 0, first, second, flag))
        for register, value in zip(
                (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3),
                (CTX, 1, move_type, 0)):
            uc.reg_write(register, value)
        for register in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                         UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                         UC_ARM_REG_R10, UC_ARM_REG_R11):
            uc.reg_write(register, SENTINEL)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, STOP | 1)
        uc.emu_start(0x02252054 | 1, STOP, count=100_000)
        assert self.reg(UC_ARM_REG_PC) & ~1 == STOP
        assert self.reg(UC_ARM_REG_SP) == STACK_TOP
        assert all(self.reg(register) == SENTINEL for register in (
            UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
            UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11))
        return struct.unpack('<I', bytes(uc.mem_read(flag, 4)))[0]

    def instruction_count(self, scn):
        counter = [0]
        handle = self.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: counter.__setitem__(0, counter[0] + 1), None, FUNCTION, 0x02258BA0)
        try:
            self.run(scn)
        finally:
            self.uc.hook_del(handle)
        return counter[0]


def with_posts(image, posts):
    """Image with the given post bytes at the two declared sites (default: the real delta)."""
    result = bytearray(image)
    for (address, _, _), post in zip(SITES, posts):
        result[address - BASE:address - BASE + len(post)] = post
    return bytes(result)


def with_effectiveness(image, post=EFFECTIVENESS_SITE[2]):
    result = bytearray(image)
    address = EFFECTIVENESS_SITE[0]
    result[address - BASE:address - BASE + len(post)] = post
    return bytes(result)


def slot_of(mon):
    return (mon - MON) // 0x100


# --------------------------------------------------------------- oracles

def type_chart(image):
    pointer = struct.unpack_from('<I', image, TYPE_TABLE_POINTER - BASE)[0]
    entries, offset = [], pointer - BASE
    while image[offset] != 0xFF:
        entries.append(tuple(image[offset:offset + 3]))
        offset += 3
    return pointer, entries


def effectiveness(entries, attack, first, second):
    """Scalar oracle of the native helper: 40 neutral, 160 for 4x."""
    value = 40
    for kind, defending, percent in entries:
        if kind != attack:
            continue
        if defending == first:
            value = value * percent // 10
        if defending == second and first != second:
            value = value * percent // 10
    return value


def wide_score(entries, types, target):
    """Stage-one sum exactly as the code builds it, before any narrowing."""
    return (effectiveness(entries, types[0], *target) & 0xFF) + effectiveness(entries, types[1], *target)


def model(scn, entries, wide, stale_wide=False):
    """Independent re-statement of the decision.

    ``wide``: stage one compares the full sum (the fix); otherwise its low byte (native).
    ``stale_wide``: the superseded fix, which also stored the full sum in [sp+0x4c]."""
    partner = scn.battler if scn.battle_type & 0x18 else scn.partner
    barred = {scn.current.get(scn.battler, 6), scn.current.get(partner, 6),
              scn.pending.get(scn.battler, 6), scn.pending.get(partner, 6)}
    size = len(scn.slots)
    usable = lambda i: scn.slots[i].species not in (0, 0x1EE) and scn.slots[i].hp != 0
    mask, stale = 0, 0
    while True:
        best, pick = 0, 6
        for i in range(size):
            if not usable(i) or mask >> i & 1 or i in barred:
                mask |= 1 << i
                continue
            score = wide_score(entries, scn.slots[i].types, scn.target_types)
            value = score if wide else score & 0xFF
            stale = score if stale_wide else score & 0xFF
            if best < value:
                best, pick = value, i
        if pick != 6:
            if any(m and m in scn.superefficient for m in scn.slots[pick].moves):
                return pick
            mask |= 1 << pick
        else:
            mask = 0x3F
        if mask == 0x3F:
            break
    best, pick = 0, 6
    for i in range(size):
        if not usable(i) or i in barred:
            continue
        for m in scn.slots[i].moves:
            if m and m not in scn.no_score:
                damage = scn.damage.get(m, 0) & 0xFF
                stale = 0 if m in scn.immune else damage
            if best < stale:
                best, pick = stale, i
    return pick


# ------------------------------------------------------------ the tests

def pair(case, language):
    """(inputs, original emulator, patched emulator) with one emulator per variant per language."""
    data = inputs(case, language)
    if not hasattr(data, 'emulators'):
        data.emulators = (Native(data.arm9, data.image), Native(data.arm9, data.patched[0]))
    return (data, *data.emulators)


def rhyperior_machamp(language_data):
    """Trainer 261 shape: slot 2 Rhyperior (Ground/Rock), slot 4 Machamp, target Bastiodon (Rock/Steel).

    Species types are read from the ROM personal NARC; slot 0 is the fainted/current mon."""
    import ndspy.narc
    import ndspy.rom
    narc = ndspy.narc.NARC(ndspy.rom.NintendoDSRom(language_data.data).getFileByName('a/0/0/2'))
    types = lambda species: tuple(narc.files[species][6:8])
    rhyperior, machamp, bastiodon = types(464), types(68), types(411)
    scenario = Scenario(
        [Slot(1, (0, 0), hp=0, moves=full_moves(0)), Slot(2, (0, 0), hp=0, moves=full_moves(1)),
         Slot(464, rhyperior, moves=full_moves(2)), Slot(0x1EE, machamp, moves=full_moves(3)),
         Slot(68, machamp, moves=full_moves(4)), Slot(0, (0, 0))],
        target_types=bastiodon, superefficient=set(full_moves(2)) | set(full_moves(4)))
    return scenario, rhyperior, machamp, bastiodon


def both_320():
    machamp = (1, 1)
    scenario = Scenario(
        [Slot(1, (0, 0), hp=0, moves=full_moves(0)), Slot(2, (0, 0), hp=0, moves=full_moves(1)),
         Slot(68, machamp, moves=full_moves(2)), Slot(0x1EE, machamp, moves=full_moves(3)),
         Slot(68, machamp, moves=full_moves(4)), Slot(0, (0, 0))],
        target_types=(5, 8), no_score={full_moves(2)[0]},
        damage={**{m: 50 for m in full_moves(2)[1:]}, **{m: 70 for m in full_moves(4)}})
    return scenario


def random_scenario(rng, entries, heavy=False):
    size = rng.randint(0, 6)
    target = rng.choice(TYPES)
    second = target if rng.random() < 0.4 else rng.choice(TYPES)
    hot = [a for a in TYPES if effectiveness(entries, a, target, second) >= 80]  # 2x or better
    slots = []
    for i in range(size):
        species = rng.choice([0, 0x1EE, 25, 68, 464, 411, 150])
        types = (rng.choice(TYPES), rng.choice(TYPES))
        if hot and rng.random() < (0.9 if heavy else 0.6):
            types = (rng.choice(hot), rng.choice(hot))
        if rng.random() < 0.4:
            types = (types[0], types[0])
        moves = tuple(0 if rng.random() < 0.15 else m for m in full_moves(i))
        slots.append(Slot(species, types, hp=rng.choice([0, 1, 50, 200]) if rng.random() < 0.2 else 100, moves=moves))
    ids = [m for s in slots for m in s.moves if m]
    pick = lambda p: {m for m in ids if rng.random() < p}
    if heavy:  # reach the damage stage often, with stale-score reads
        return Scenario(
            slots, target_types=(target, second), battler=1, partner=3, battle_type=rng.choice([0, 8]),
            current={1: rng.choice([0, 6])}, superefficient=pick(rng.choice([0.0, 0.0, 0.1])),
            damage={m: rng.randint(0, 255) for m in ids}, immune=pick(0.1), no_score=pick(0.5))
    return Scenario(
        slots, target_types=(target, second),
        battler=rng.choice([1, 3]), partner=rng.choice([0, 2, 3]), battle_type=rng.choice([0, 8, 0x10, 0x18]),
        current={rng.choice([0, 1, 2, 3]): rng.choice([0, 1, 2, 3, 4, 5, 6]) for _ in range(2)},
        pending={rng.choice([0, 1, 2, 3]): rng.choice([0, 1, 2, 3, 4, 5, 6]) for _ in range(rng.randint(0, 2))},
        superefficient=pick(rng.choice([0.0, 0.3, 0.6, 1.0])), damage={m: rng.randint(0, 300) for m in ids},
        immune=pick(0.15), no_score=pick(0.2))


class NativeFunctionTests(unittest.TestCase):
    def test_native_baseline_wraps_the_320_score_to_64(self):
        """Characterisation of the unpatched game: this holds before and after the fix."""
        for language in V4:
            data, original, _ = pair(self, language)
            scenario, rhyperior, machamp, bastiodon = rhyperior_machamp(data)
            self.assertEqual((rhyperior, machamp, bastiodon), ((4, 5), (1, 1), (5, 8)))
            _, entries = type_chart(data.image)
            self.assertEqual(wide_score(entries, rhyperior, bastiodon), 180)
            self.assertEqual(wide_score(entries, machamp, bastiodon), 320)
            result, compares = original.run(scenario)
            self.assertEqual([score for _, score, _ in compares], [180, 64])
            self.assertEqual(result, 2, language)

    def test_native_sum_160_plus_160_does_not_wrap(self):
        for language in V4:
            data, _, patched = pair(self, language)
            scenario, _, machamp, bastiodon = rhyperior_machamp(data)
            result, compares = patched.run(scenario)
            self.assertEqual([score for _, score, _ in compares], [180, 320], language)
            self.assertEqual(result, 4, language)
            self.assertEqual(model(scenario, type_chart(data.image)[1], wide=True), 4)

    def test_full_replacement_prefers_native_wide_score(self):
        """Wide model == patched function, narrow model == original function, on random decisions."""
        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            rng, differing = random.Random(0x5A1D + len(language)), 0
            for index in range(400):
                scenario = random_scenario(rng, entries)
                old, _ = original.run(scenario)
                new, _ = patched.run(scenario)
                self.assertEqual(old, model(scenario, entries, wide=False), (language, index, 'original'))
                self.assertEqual(new, model(scenario, entries, wide=True), (language, index, 'patched'))
                differing += old != new
            self.assertGreater(differing, 5, 'the random campaign must reach the overflow case')

    def test_nonoverflow_and_ties_unchanged(self):
        """Scores up to 255: identical decision, calls, arguments, RNG state and observations."""
        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            rng, compared = random.Random(0xC0FFEE), 0
            for _ in range(400):
                scenario = random_scenario(rng, entries)
                if any(wide_score(entries, s.types, scenario.target_types) > 255 for s in scenario.slots):
                    continue
                old = original.run(scenario)
                old_log, old_seed = list(original.log), original.seed
                new = patched.run(scenario)
                self.assertEqual(old, new)
                self.assertEqual(old_log, patched.log)
                self.assertEqual(old_seed, patched.seed)
                self.assertEqual(sum(call[0] == 'GetRandomOpposingBattlerId' for call in patched.log), 1)
                compared += 1
            self.assertGreater(compared, 100)
            # explicit tie: two equal 160 scores must keep the first candidate.
            tie = Scenario([Slot(1, (0, 0), hp=0), Slot(25, (1, 1), moves=full_moves(1)), Slot(26, (1, 1), moves=full_moves(2))],
                           target_types=(5, 5), superefficient=set(full_moves(1)) | set(full_moves(2)))
            self.assertEqual((original.run(tie)[0], patched.run(tie)[0]), (1, 1))
            self.assertEqual(wide_score(entries, (1, 1), (5, 5)), 160)

    def test_instruction_count_per_decision_unchanged(self):
        """Same control flow (no overflow): the two NOPs replace the two shifts one for one."""
        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            rng, compared = random.Random(7), 0
            while compared < 40:
                scenario = random_scenario(rng, entries)
                if any(wide_score(entries, s.types, scenario.target_types) > 255 for s in scenario.slots):
                    continue
                self.assertEqual(original.instruction_count(scenario), patched.instruction_count(scenario))
                compared += 1

    def test_registers_stack_and_context_preserved_in_every_battle_shape(self):
        """run() asserts r4-r11, SP, caller canary, context bytes and carry-flag correctness."""
        for language in V4:
            data, original, patched = pair(self, language)
            scenario, *_ = rhyperior_machamp(data)
            for battle_type in (0, 8, 0x10, 0x18):  # single, double, multi/partner shapes
                scenario.battle_type = battle_type
                for emulator in (original, patched):
                    emulator.run(scenario)
                    self.assertTrue(emulator.compares)

    def test_barred_slots_are_never_selected(self):
        """KO, egg, empty, current and pending (ctx 0x219C/0x21A4) slots, for battler and partner."""
        def build(battle_type, current_partner=6, pending_partner=6):
            bad = [Slot(1, (1, 1), hp=0), Slot(0x1EE, (1, 1)), Slot(0, (1, 1)), Slot(25, (1, 1)), Slot(26, (1, 1))]
            slots = bad + [Slot(27, (0, 0))]
            for i, slot in enumerate(slots):
                slot.moves = full_moves(i)
            return Scenario(slots, target_types=(5, 8), battle_type=battle_type, partner=3,
                            current={1: 3, 3: current_partner}, pending={1: 4, 3: pending_partner},
                            superefficient={m for s in slots for m in s.moves})

        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            self.assertEqual(wide_score(entries, (1, 1), (5, 8)), 320)
            for battle_type in (0, 8, 0x10, 0x18):
                partner_counts = battle_type & 0x18 == 0  # otherwise the partner argument is the battler itself
                for emulator in (original, patched):
                    self.assertEqual(emulator.run(build(battle_type))[0], 5, (language, battle_type))
                    self.assertEqual(emulator.run(build(battle_type, current_partner=5))[0], 6 if partner_counts else 5)
                    self.assertEqual(emulator.run(build(battle_type, pending_partner=5))[0], 6 if partner_counts else 5)
                    self.assertEqual(emulator.run(build(battle_type, current_partner=3, pending_partner=4))[0], 5)

    def test_zero_and_one_replacement(self):
        for language in V4:
            data, original, patched = pair(self, language)
            for emulator in (original, patched):
                self.assertEqual(emulator.run(Scenario([]))[0], 6)
                self.assertEqual(emulator.run(Scenario([Slot(1, (0, 0))]))[0], 6)  # only the current mon
                two = Scenario([Slot(1, (0, 0), moves=full_moves(0)), Slot(25, (1, 1), moves=full_moves(1))],
                               superefficient=set(full_moves(1)))
                self.assertEqual(emulator.run(two)[0], 1)

    def test_high_candidate_without_super_effective_move_falls_through(self):
        """320 is excluded without a super-effective move; the next candidate then the damage stage decide."""
        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            # first the 320 mon (slot 4) has none, so slot 2 (180) wins by the second pass.
            scenario, *_ = rhyperior_machamp(data)
            scenario.superefficient = set(full_moves(2))
            self.assertEqual(patched.run(scenario)[0], 2)
            self.assertEqual(model(scenario, entries, wide=True), 2)
            # nobody has one: the stage-two damage choice (highest strict damage, first on ties).
            scenario.superefficient = set()
            scenario.damage = {m: 10 for m in full_moves(2)}
            scenario.damage.update({m: 90 for m in full_moves(4)})
            self.assertEqual(patched.run(scenario)[0], 4)
            self.assertEqual(original.run(scenario)[0], 4)
            scenario.damage = {full_moves(2)[1]: 200, full_moves(4)[2]: 200}
            self.assertEqual((original.run(scenario)[0], patched.run(scenario)[0]), (2, 2))
            # immune result zeroes the damage; all zero keeps "no replacement" (6).
            scenario.damage, scenario.immune = {m: 99 for m in full_moves(2) + full_moves(4)}, set(full_moves(2) + full_moves(4))
            self.assertEqual((original.run(scenario)[0], patched.run(scenario)[0]), (6, 6))

    def test_stage_two_damage_conversion_is_not_part_of_the_fix(self):
        """CalcMoveDamage values above 255 still go through the same byte conversion."""
        for language in V4:
            data, original, patched = pair(self, language)
            scenario, *_ = rhyperior_machamp(data)
            scenario.superefficient = set()
            scenario.damage = {full_moves(2)[0]: 300, full_moves(4)[0]: 100}  # 300 -> 44 in stage two
            self.assertEqual((original.run(scenario)[0], patched.run(scenario)[0]), (4, 4))

    def test_stage_two_stale_word_and_choice_stay_native(self):
        """Two 320 candidates, nobody super-effective; slot 2's first stage-two move reads [sp+0x4c].

        Native stores 64 there, so Machamp #2 (damage 70) beats the stale 64 held by slot 2. The
        superseded 2-NOP fix stored 320 and kept slot 2; run() also asserts the stored word is
        always the low byte of the compared sum."""
        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            scenario = both_320()
            self.assertEqual(original.run(scenario)[0], 4)
            result, compares = patched.run(scenario)
            self.assertEqual(result, 4)
            self.assertEqual([score for _, score, _ in compares], [320, 320, 320])
            self.assertEqual(patched.stored, [64, 64, 64])
            self.assertEqual(model(scenario, entries, True), 4)
            self.assertEqual(model(scenario, entries, True, stale_wide=True), 2)  # what the 2-NOP variant did

    def test_stage_two_inherits_the_new_stage_one_elimination_order(self):
        """Declared consequence, not a defect of the delta: the stale word holds the LAST candidate scored.

        With Rhyperior 180 / Machamp 320, native eliminates 2 then 4 (stale 64), the fix eliminates 4
        then 2 (stale 180). The word is still the low byte of a score, but of a different candidate."""
        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            scenario, *_ = rhyperior_machamp(data)
            scenario.superefficient = set()
            scenario.no_score = {full_moves(2)[0]}
            scenario.damage = {m: 100 for m in full_moves(4)} | {m: 90 for m in full_moves(2)}
            self.assertEqual((original.run(scenario)[0], patched.run(scenario)[0]), (4, 2))
            self.assertEqual((model(scenario, entries, False), model(scenario, entries, True)), (4, 2))
            # the same data without an overflow keeps the native order and the native result.
            scenario.target_types = (0, 0)
            self.assertEqual(original.run(scenario)[0], patched.run(scenario)[0])

    def test_differential_stage_one_wide_stage_two_native(self):
        """Random decisions incl. empty move slots and ctx flag 1: patched == "wide stage one, 8-bit [sp+0x4c]"."""
        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            rng = random.Random(0xD1FF + len(language))
            differs = discriminates = 0
            for index in range(1500):
                scenario = random_scenario(rng, entries, heavy=index % 2 == 1)
                old, new = original.run(scenario)[0], patched.run(scenario)[0]
                self.assertEqual(old, model(scenario, entries, False), (language, index, 'original'))
                self.assertEqual(new, model(scenario, entries, True), (language, index, 'patched'))
                differs += old != new
                discriminates += model(scenario, entries, True) != model(scenario, entries, True, stale_wide=True)
            self.assertGreater(differs, 10)
            self.assertGreater(discriminates, 0, 'the campaign must be able to tell the superseded fix apart')

    def test_overlay_image_is_not_self_modified(self):
        data, original, patched = pair(self, 'EN')
        scenario, *_ = rhyperior_machamp(data)
        for emulator, image in ((original, data.image), (patched, data.patched[0])):
            emulator.run(scenario)
            self.assertEqual(bytes(emulator.uc.mem_read(BASE, len(image))), image)


class DualImmunityNativeTests(unittest.TestCase):
    POSITIVES = ((13, 4, 2), (4, 5, 2), (4, 8, 2), (7, 0, 14))
    CONTROLS = ((13, 11, 4), (4, 13, 2), (7, 0, 11))

    def test_real_helper_loses_the_false_super_effective_flag_after_the_patch(self):
        for language in V4:
            data = inputs(self, language)
            original = Native(data.arm9, data.image, execute_effectiveness=True)
            patched = Native(data.arm9, data.patched[0], execute_effectiveness=True)
            for move_type, first, second in self.POSITIVES:
                with self.subTest(language=language, types=(move_type, first, second)):
                    self.assertEqual(original.effectiveness_flags(move_type, first, second), 0x0A)
                    self.assertEqual(patched.effectiveness_flags(move_type, first, second), 0x08)
            for move_type, first, second in self.CONTROLS:
                with self.subTest(language=language, control=(move_type, first, second)):
                    self.assertEqual(original.effectiveness_flags(move_type, first, second), 0x08)
                    self.assertEqual(patched.effectiveness_flags(move_type, first, second), 0x08)

    def test_nonimmune_effectiveness_and_unrelated_status_bits_are_unchanged(self):
        for language in V4:
            data = inputs(self, language)
            original = Native(data.arm9, data.image, execute_effectiveness=True)
            patched = Native(data.arm9, data.patched[0], execute_effectiveness=True)
            for move_type, first, second in ((10, 12, 11), (13, 11, 2), (4, 5, 8)):
                before = original.effectiveness_flags(move_type, first, second, 0x400)
                after = patched.effectiveness_flags(move_type, first, second, 0x400)
                self.assertEqual(after, before, (language, move_type, first, second))
                self.assertTrue(after & 0x400)


class TypeHelperTests(unittest.TestCase):
    def test_every_current_type_pair_matches_the_scalar_oracle_through_the_real_helper(self):
        for language in V4:
            data, original, patched = pair(self, language)
            pointer, entries = type_chart(data.image)
            self.assertEqual(pointer, 0x0226CC7C)
            self.assertEqual(len(entries), 111)  # rows up to the 0xFF terminator, including the 0xFE separator
            for attack in TYPES:
                for first in TYPES:
                    for second in TYPES:
                        expected = effectiveness(entries, attack, first, second)
                        self.assertEqual(original.helper(attack, first, second), expected, (attack, first, second))
                        self.assertEqual(patched.helper(attack, first, second), expected)
            self.assertEqual(max(effectiveness(entries, a, f, s) for a in TYPES for f in TYPES for s in TYPES), 160)

    def test_every_candidate_and_target_type_pair_scores_widely_in_the_real_function(self):
        """All 324 candidate pairs against all 324 target pairs: the sum is observed in the real compare."""
        for language in V4:
            data, original, patched = pair(self, language)
            entries = type_chart(data.image)[1]
            pairs = [(a, b) for a in TYPES for b in TYPES]
            overflowing = 0
            for first in TYPES:
                for second in TYPES:
                    for start in range(0, len(pairs), 6):
                        chunk = pairs[start:start + 6]
                        scenario = Scenario([Slot(25 + i, types, moves=full_moves(i)) for i, types in enumerate(chunk)],
                                            target_types=(first, second), current={1: 6},
                                            superefficient={m for i in range(6) for m in full_moves(i)})
                        wide = [wide_score(entries, types, (first, second)) for types in chunk]
                        _, observed = patched.run(scenario)
                        self.assertEqual([score for _, score, _ in observed], wide, (language, first, second, start))
                        _, observed = original.run(scenario)
                        self.assertEqual([score for _, score, _ in observed], [w & 0xFF for w in wide])
                        overflowing += sum(w > 255 for w in wide)
                        self.assertTrue(all(w == 320 for w in wide if w > 255))
            self.assertEqual(overflowing, 142, language)  # of 324 x 324 = 104976 pairs


class CallerTests(unittest.TestCase):
    EXPECTED = [('ov010', 0x022205FE, 'bl-thumb'), ('ov012', 0x0225F8E8, 'bl-thumb')]

    def test_only_trainer_ai_and_opponent_controller_call_the_function_while_overlay_12_is_loaded(self):
        """Scan ARM9 and every overlay for BL/BLX and literal pointers to 0x02258800.

        Overlays whose RAM range overlaps overlay 12 are never resident with it, so their raw
        matches cannot reach this routine; the others must be exactly the two audited sites."""
        for language in V4:
            data = inputs(self, language)
            end = BASE + data.entry['ram_size']
            hits, exclusive = [], set()
            for label, base, blob in image_sources(data):
                if label != 'ov012' and label.startswith('ov') and base < end and base + len(blob) > BASE:
                    exclusive.add(label)
                for offset in range(0, len(blob) - 3, 2):
                    hits += [(label, base + offset, kind) for kind in references(blob, offset, base + offset)]
            resident = [hit for hit in hits if hit[0] not in exclusive]
            self.assertEqual(sorted(resident), self.EXPECTED, language)
            self.assertEqual(sorted({hit[0] for hit in hits} - {hit[0] for hit in resident}),
                             ['ov045', 'ov049', 'ov091', 'ov092', 'ov093'])


def image_sources(data):
    sources = [('arm9', start, bytes(data.arm9.raw[offset:offset + size])) for start, offset, size in data.arm9.segmenti]
    for index in range(data.rom.n_overlay):
        try:
            entry, _, image = data.rom.immagine_overlay(index)
        except Exception:  # overlay 7 is not decodable in place by sgp12.blz; use the independent ndspy decoder
            import ndspy.codeCompression as codec
            entry = data.rom.voce_overlay(index)
            raw = data.rom.file_bytes(entry['file_id'])
            image = codec.decompress(raw[:entry['dim_compressa']]) if entry['compresso'] else raw
        sources.append((f'ov{index:03d}', entry['ram'], image))
    return sources


def references(blob, offset, site):
    kinds = []
    high, low = struct.unpack_from('<HH', blob, offset)
    if high & 0xF800 == 0xF000 and low & 0xF800 in (0xF800, 0xE800):  # Thumb BL / BLX
        addend = ((high & 0x7FF) << 12) | ((low & 0x7FF) << 1)
        addend -= 0x800000 if addend & 0x400000 else 0
        destination = site + 4 + addend
        if low & 0xF800 == 0xE800:
            destination &= ~3
        if destination == FUNCTION:
            kinds.append('bl-thumb')
    if offset % 4 == 0:
        word = struct.unpack_from('<I', blob, offset)[0]
        if word >> 24 in (0xEB, 0xFA, 0xFB):  # ARM BL (always) and BLX immediate
            delta = (word & 0xFFFFFF) << 2
            delta -= 1 << 26 if delta & (1 << 25) else 0
            delta += 2 if word >> 24 == 0xFB else 0
            if site + 8 + delta == FUNCTION:
                kinds.append('bl-arm')
        if word in (FUNCTION, FUNCTION | 1):
            kinds.append('word')
    return kinds


class DrySkinRomPipelineTests(unittest.TestCase):
    def test_real_v4_candidates_patch_both_ai_copies_and_verify(self):
        self.assertTrue(hasattr(ai, 'apply_dry_skin'),
                        'whole-ROM Dry Skin patch is missing')
        self.assertTrue(hasattr(ai, 'verify_dry_skin'),
                        'whole-ROM Dry Skin verifier is missing')
        for language, (expected_hash, expected_size) in V4.items():
            with self.subTest(language=language):
                path = EXPERIMENT / f'candidate-v4-{language}.nds'
                if not path.is_file():
                    self.skipTest('immutable V4 candidate is unavailable: ' + str(path))
                before = path.read_bytes()
                self.assertEqual((hashlib.sha256(before).hexdigest(), len(before)),
                                 (expected_hash, expected_size))
                entry = Rom(before).immagine_overlay(10)[0]
                self.assertEqual(
                    (entry['static_init_start'], entry['static_init_end']),
                    (ai.ABSORB_SWITCH_STATIC_INIT_START,
                     ai.ABSORB_SWITCH_STATIC_INIT_END))
                self.assertEqual(entry['static_init_end'],
                                 ai.ABSORB_SWITCH_HELPER_ADDRESS)
                after, receipt = ai.apply_dry_skin(before, language)
                overlay = Rom(after).immagine_overlay(10)[2]
                site = ai.DRY_SKIN_SITE - ai.DRY_SKIN_OVERLAY_BASE
                self.assertEqual(struct.unpack_from('<I', overlay, site)[0], 87)
                gate = ai.ARENA_SWITCH_SITE - ai.DRY_SKIN_OVERLAY_BASE
                self.assertEqual(
                    overlay[gate:gate + len(ai.ARENA_SWITCH_REPLACEMENT)],
                    ai.ARENA_SWITCH_REPLACEMENT)
                absorb_active = ai.ABSORB_SWITCH_ACTIVE_SITE - ai.DRY_SKIN_OVERLAY_BASE
                absorb_party = ai.ABSORB_SWITCH_PARTY_SITE - ai.DRY_SKIN_OVERLAY_BASE
                absorb_helper = ai.ABSORB_SWITCH_HELPER_ADDRESS - ai.DRY_SKIN_OVERLAY_BASE
                self.assertEqual(
                    overlay[absorb_active:absorb_active + len(ai.ABSORB_SWITCH_ACTIVE_REPLACEMENT)],
                    ai.ABSORB_SWITCH_ACTIVE_REPLACEMENT)
                self.assertEqual(
                    overlay[absorb_party:absorb_party + len(ai.ABSORB_SWITCH_PARTY_REPLACEMENT)],
                    ai.ABSORB_SWITCH_PARTY_REPLACEMENT)
                self.assertEqual(
                    overlay[absorb_helper:absorb_helper + len(ai.ABSORB_SWITCH_HELPER)],
                    ai.ABSORB_SWITCH_HELPER)
                parsed = ndspy.rom.NintendoDSRom(after)
                file_id = parsed.filenames.idOf(ai.DRY_SKIN_ARCHIVE)
                self.assertEqual(file_id, 228)
                member = ndspy.narc.NARC(parsed.files[file_id]).files[0]
                self.assertEqual(struct.unpack_from('<I', member, ai.DRY_SKIN_MEMBER_SITE)[0], 87)
                for site in ai.WATER_SPOUT_SITES:
                    self.assertEqual(struct.unpack_from('<I', member, site)[0], 1)
                self.assertEqual(struct.unpack_from('<I', member, ai.FACADE_SITE)[0], 1)
                self.assertEqual(struct.unpack_from(
                    '<I', member, ai.THUNDER_DISPATCH_SITE)[0], 152)
                for site in ai.METAL_BURST_JUMP_SITES:
                    self.assertEqual(struct.unpack_from('<I', member, site)[0], 0)
                report = ai.verify_dry_skin(before, after, receipt)
                self.assertTrue(report['ok'])
                self.assertEqual(report['overlay_logical_changed_bytes'], 48)
                self.assertEqual(report['archive_changed_bytes'], 11)

    def test_absorb_helper_refuses_a_foreign_static_initializer_boundary(self):
        path = EXPERIMENT / 'candidate-v4-EN.nds'
        if not path.is_file():
            self.skipTest('immutable V4 candidate is unavailable: ' + str(path))
        before = bytearray(path.read_bytes())
        y9 = struct.unpack_from('<I', before, 0x50)[0]
        row = y9 + 32 * 10
        for field in (16, 20):
            with self.subTest(field=field):
                damaged = bytearray(before)
                value = struct.unpack_from('<I', damaged, row + field)[0]
                struct.pack_into('<I', damaged, row + field, value + 4)
                with self.assertRaisesRegex(ValueError, 'static-initializer'):
                    ai.apply_dry_skin(bytes(damaged), 'EN')

    def test_verifier_rejects_unrelated_and_second_archive_changes(self):
        path = EXPERIMENT / 'candidate-v4-EN.nds'
        if not path.is_file():
            self.skipTest('immutable V4 candidate is unavailable: ' + str(path))
        before = path.read_bytes()
        after, receipt = ai.apply_dry_skin(before, 'EN')

        unrelated = bytearray(after)
        unrelated[0x300] ^= 1
        with self.assertRaisesRegex(ValueError, 'outside|NitroFS'):
            ai.verify_dry_skin(before, bytes(unrelated), receipt)

        fat_offset = struct.unpack_from('<I', after, 0x48)[0]
        archive_start = struct.unpack_from('<I', after,
                                           fat_offset + 8 * ai.DRY_SKIN_ARCHIVE_FILE_ID)[0]
        archive_extra = bytearray(after)
        archive_extra[archive_start + 8] ^= 1
        with self.assertRaisesRegex(ValueError, 'archive|NARC'):
            ai.verify_dry_skin(before, bytes(archive_extra), receipt)


class RomPipelineTests(unittest.TestCase):
    def test_receipt_requires_both_rom_hashes(self):
        data = inputs(self, 'EN')
        after, receipt = data.applied
        valid = receipt['writer']
        invalid = [None, {}, {'writer': {}}]
        for key in ('ingresso_sha256', 'uscita_sha256'):
            invalid.extend(({k: v for k, v in valid.items() if k != key},
                            {**valid, key: None}))
        for fake in invalid:
            with self.subTest(receipt=fake), self.assertRaisesRegex(ValueError, 'receipt'):
                ai.verify(data.data, after, fake)

    def test_noncanonical_blz_footer_refused_even_with_forged_receipt(self):
        from ndspy import codeCompression
        for language in V4:
            with self.subTest(language=language):
                data = inputs(self, language)
                after, receipt = data.applied
                fat = struct.unpack_from('<I', after, 0x48)[0]
                start, end = struct.unpack_from('<II', after, fat + 8 * data.entry['file_id'])
                forged = bytearray(after)
                forged[end - 8] ^= 1
                forged = bytes(forged)
                self.assertEqual(ndspy_decomprimi_sicuro(after[start:end]),
                                 ndspy_decomprimi_sicuro(forged[start:end]))
                fake = {**receipt, 'writer': {**receipt['writer'],
                        'uscita_sha256': hashlib.sha256(forged).hexdigest()}}
                with self.assertRaisesRegex(ValueError, 'canonical'):
                    ai.verify(data.data, forged, fake)

    def test_streams_the_loader_runs_but_the_writer_would_not_emit_are_refused(self):
        """Each forgery decodes, in the game's own MIi_UncompressBackward, to the exact patched overlay and keeps
        y9/FAT/CRC coherent: only the canonical-stream comparison can refuse it (the 4a verifier accepted all three)."""
        data = inputs(self, 'EN')
        before, (after, receipt) = data.data, data.applied
        fat = struct.unpack_from('<I', after, 0x48)[0]
        start, end = struct.unpack_from('<II', after, fat + 8 * data.entry['file_id'])
        self.assertEqual(loader_image(data, after), data.patched[0])
        self.assertEqual(set(before[end:end + 4]), {0xFF})  # slack the padded variant grows over
        stream = bytes(after[start:end])
        word0, word1 = struct.unpack_from('<II', stream, len(stream) - 8)
        from sgp131.blz_test_support import alternate_same_size_stream
        alternate = alternate_same_size_stream(stream)
        self.assertNotEqual(alternate, stream)
        self.assertEqual(len(alternate), len(stream))
        padded = stream[:-8] + b'\xFF' * 4 + struct.pack('<II', word0 + 4 + (4 << 24), (word1 - 4) & 0xFFFFFFFF)
        y9_word = struct.unpack_from('<I', after, struct.unpack_from('<I', after, 0x50)[0] + 32 * 12 + 28)[0]
        forgeries = {
            'enc_len low byte (split point of the raw prefix)': rewrite(after, edits=[(end - 8, after[end - 8] ^ 1)]),
            'alternate safe raw-prefix cut': rewrite(after, stream=alternate),
            'hdr_len 8 -> 12 with 4 padding bytes, y9 and FAT +4': rewrite(
                after, stream=padded, fat_end=start + len(padded), y9_word=y9_word + 4),
        }
        for name, forged in forgeries.items():
            with self.subTest(name):
                self.assertNotEqual(forged, after)
                self.assertEqual(loader_image(data, forged), data.patched[0], 'the loader must accept the forgery')
                with self.assertRaisesRegex(ValueError, 'canonical'):
                    ai.verify(before, forged, with_hashes(receipt, before, forged))

    def test_physical_fields_cannot_change_while_the_overlay_image_stays_the_same(self):
        data = inputs(self, 'EN')
        before, (after, receipt) = data.data, data.applied
        fat, y9 = struct.unpack_from('<I', after, 0x48)[0], struct.unpack_from('<I', after, 0x50)[0]
        start, end = struct.unpack_from('<II', after, fat + 8 * data.entry['file_id'])
        word = struct.unpack_from('<I', after, y9 + 32 * 12 + 28)[0]
        used = bytearray(after)
        struct.pack_into('<I', used, 0x80, struct.unpack_from('<I', used, 0x80)[0] + 512)
        struct.pack_into('<H', used, 0x15E, crc16(bytes(used[:0x15E])))
        self.assertEqual(set(before[end:end + 8]), {0xFF})
        # (name, ROM, expected refusal, does the game's loader still produce the patched overlay?)
        cases = (
            ('FAT end +4 over 0xFF slack, y9 size unchanged', rewrite(after, fat_end=end + 4), 'range/size', True),
            ('y9 size +4, FAT end unchanged', rewrite(after, y9_word=word + 4), 'range/size', False),
            ('y9 size -4, FAT end unchanged', rewrite(after, y9_word=word - 4), 'range/size', None),
            ('FAT end -4, y9 size unchanged', rewrite(after, fat_end=end - 4), 'range/size', False),
            ('y9 flag bit 1 (digest, boot type 2 only)', rewrite(after, y9_word=word | 2 << 24), 'flag byte', True),
            ('y9 flag bit 7 (ignored by the loader)', rewrite(after, y9_word=word | 0x80 << 24), 'flag byte', True),
            ('slack byte past the FAT end', rewrite(after, edits=[(end + 4, 0)]), 'outside the declared', True),
            ('header total-used word, CRC16 refreshed', bytes(used), 'outside the declared', True),
        )
        for name, forged, refusal, loads in cases:
            with self.subTest(name):
                image = loader_image(data, forged)
                if loads is True:
                    self.assertEqual(image, data.patched[0])
                elif loads is False:
                    self.assertIsNone(image)
                else:
                    self.assertNotEqual(image, data.patched[0])
                with self.assertRaisesRegex(ValueError, refusal):
                    ai.verify(before, forged, with_hashes(receipt, before, forged))

    def test_receipt_hashes_must_match_the_actual_roms(self):
        data = inputs(self, 'EN')
        after, receipt = data.applied
        # Both existing receipt shapes remain supported.
        self.assertTrue(ai.verify(data.data, after, receipt['writer'])['ok'])
        for key in ('ingresso_sha256', 'uscita_sha256'):
            with self.subTest(key=key):
                fake = {**receipt, 'writer': {**receipt['writer'], key: '0' * 64}}
                with self.assertRaisesRegex(ValueError, 'receipt'):
                    ai.verify(data.data, after, fake)

    def test_apply_changes_exactly_the_declared_logical_bytes_in_both_languages(self):
        for language in V4:
            data = inputs(self, language)
            after, receipt = data.applied
            self.assertEqual(len(after), len(data.data))
            decoded = Rom(after).immagine_overlay(12)[2]
            self.assertEqual(decoded, data.patched[0])
            self.assertEqual(
                decoded,
                with_effectiveness(with_posts(data.image, [post for _, _, post in SITES])))
            changed = [i for i in range(len(decoded)) if decoded[i] != data.image[i]]
            self.assertEqual(changed, [a - BASE for a in ALL_CHANGED])
            for address, pre, post in (*SITES, EFFECTIVENESS_SITE):
                self.assertEqual(data.image[address - BASE:address - BASE + len(pre)], pre)
                self.assertEqual(decoded[address - BASE:address - BASE + len(post)], post)
            report = ai.verify(data.data, after, receipt)
            self.assertTrue(report['ok'])
            self.assertEqual(report['logical_changed_bytes'], 6)
            self.assertEqual(report['declared_window_bytes'], 10)
            self.assertEqual(report['rom_sha256_before'], hashlib.sha256(data.data).hexdigest())
            self.assertEqual(report['rom_sha256_after'], hashlib.sha256(after).hexdigest())
            self.assertEqual(hashlib.sha256(data.image[ai.FUNCTION_START - BASE:ai.FUNCTION_END - BASE]).hexdigest(), ai.FUNCTION_SHA256)
            self.assertEqual(
                hashlib.sha256(data.image[
                    ai.EFFECTIVENESS_FUNCTION_START - BASE:
                    ai.EFFECTIVENESS_FUNCTION_END - BASE]).hexdigest(),
                ai.EFFECTIVENESS_FUNCTION_SHA256)

    def test_the_overlay_function_is_identical_in_english_and_italian(self):
        en, it = inputs(self, 'EN'), inputs(self, 'IT')
        self.assertEqual(hashlib.sha256(en.image).hexdigest(), OVERLAY_SHA256)
        self.assertEqual(en.image, it.image)
        self.assertEqual(en.patched[0], it.patched[0])

    def test_wrong_preimage_and_extra_changed_byte_refuse(self):
        for language in V4:
            data = inputs(self, language)
            for delta in range(len(CONTEXT)):  # every guard byte, incl. both declared windows
                image = bytearray(data.image)
                image[CONTEXT_ADDRESS - BASE + delta] ^= 0x01
                with self.assertRaisesRegex(ValueError, 'preimage', msg='guard byte %d' % delta):
                    ai.patch_overlay(bytes(image))
            for delta in range(len(ai.EFFECTIVENESS_CONTEXT)):
                image = bytearray(data.image)
                image[ai.EFFECTIVENESS_CONTEXT_ADDRESS - BASE + delta] ^= 1
                with self.assertRaisesRegex(ValueError, 'effectiveness preimage'):
                    ai.patch_overlay(bytes(image))
            image = bytearray(data.image)  # one extra byte in the pinned function, away from the delta
            image[ai.FUNCTION_START - BASE + 0x40] ^= 0x01
            with self.assertRaisesRegex(ValueError, 'function'):
                ai.patch_overlay(bytes(image))
            with self.assertRaises(ValueError):
                ai.patch_overlay(data.patched[0])  # already patched
            with self.assertRaises(Exception):
                ai.apply(data.applied[0], language)  # a second application is refused by the guard
            with self.assertRaisesRegex(ValueError, 'language'):
                ai.apply(data.data, 'ES')

    def test_verifier_rejects_extra_logical_and_container_changes(self):
        from sgp12.overlay import applica
        data = inputs(self, 'EN')
        before, (after, receipt) = data.data, data.applied
        all_sites = (*SITES, EFFECTIVENESS_SITE)
        patches = [{'addr': a, 'pre': pre, 'post': post} for a, pre, post in all_sites]
        extra, _ = applica(before, 12, [(CONTEXT_ADDRESS, CONTEXT),
                                       (ai.EFFECTIVENESS_CONTEXT_ADDRESS,
                                        ai.EFFECTIVENESS_CONTEXT)], patches + [
            {'addr': ai.FUNCTION_START + 0x40, 'pre': data.image[ai.FUNCTION_START - BASE + 0x40:ai.FUNCTION_START - BASE + 0x41], 'post': b'\xFF'}])
        with self.assertRaisesRegex(ValueError, 'logical'):
            ai.verify(before, extra, receipt)
        old_fix, _ = applica(before, 12, [(CONTEXT_ADDRESS, CONTEXT)], [
            {'addr': 0x02258938, 'pre': bytes.fromhex('0006000e'), 'post': bytes.fromhex('c046c046')}])
        with self.assertRaises(ValueError):  # the superseded 2-NOP fix is not the declared delta
            ai.verify(before, old_fix, receipt)
        entry = data.entry
        fat_offset, y9 = struct.unpack_from('<I', before, 0x48)[0], struct.unpack_from('<I', before, 0x50)[0] + 12 * 32
        for label, position in (('y9 size/flag word', y9 + 28), ('FAT end', fat_offset + entry['file_id'] * 8 + 4),
                                ('header', 0x20), ('another NitroFS/ARM9 byte', len(before) - 17), ('ARM9', 0x4100)):
            damaged = bytearray(after)
            damaged[position] ^= 0x01
            with self.assertRaises(ValueError, msg=label):
                ai.verify(before, bytes(damaged), receipt)
        end_old = struct.unpack_from('<I', before, fat_offset + entry['file_id'] * 8 + 4)[0]
        end_new = struct.unpack_from('<I', after, fat_offset + entry['file_id'] * 8 + 4)[0]
        if end_new > end_old:  # the longer stream grows over padding, which must be 0xFF
            grown = bytearray(before)
            grown[end_old] = 0x00
            with self.assertRaisesRegex(ValueError, 'padding'):
                ai.verify(bytes(grown), after, receipt)
        with self.assertRaises(ValueError):
            ai.verify(before, before, receipt)  # not applied
        with self.assertRaises(ValueError):
            ai.verify(after, after, receipt)  # no preimage


MUTANTS = {  # each declared instruction left original, one at a time, and the superseded variant
    'lsls_original': (bytes.fromhex('0006090e1391'), bytes.fromhex('c046')),
    'lsrs_original': (bytes.fromhex('0106000e1391'), bytes.fromhex('c046')),
    'str_original': (bytes.fromhex('0106090e1390'), bytes.fromhex('c046')),
    'reload_not_nopped': (bytes.fromhex('0106090e1391'), bytes.fromhex('1398')),
    'superseded_two_nop': (bytes.fromhex('c046c0461390'), bytes.fromhex('1398')),
}


def battery(data, image):
    """Names of the behavioural checks an image fails (empty for the correct delta)."""
    emulator = Native(data.arm9, image)
    entries = type_chart(data.image)[1]
    failures = set()

    def attempt(name, check):
        try:
            check()
        except Exception:  # assertion, emulator fault or runaway: the image does not behave
            failures.add(name)

    def wide():
        scenario, *_ = rhyperior_machamp(data)
        result, compares = emulator.run(scenario, strict=False)
        assert result == 4 and [score for _, score, _ in compares] == [180, 320]

    def stale():
        assert emulator.run(both_320(), strict=False)[0] == 4  # decided by outcome alone

    def differential():
        rng = random.Random(0xB00)
        for index in range(300):
            scenario = random_scenario(rng, entries, heavy=index % 2 == 1)
            assert emulator.run(scenario)[0] == model(scenario, entries, True)

    attempt('wide_320', wide)
    attempt('stage_two_stale', stale)
    attempt('differential', differential)
    return failures


class MutantTests(unittest.TestCase):
    def test_each_instruction_of_the_delta_is_load_bearing(self):
        data = inputs(self, 'EN')  # overlay 12 is byte-identical in EN and IT
        self.assertEqual(battery(data, with_posts(data.image, [post for _, _, post in SITES])), set())
        for name, posts in MUTANTS.items():
            failures = battery(data, with_posts(data.image, posts))
            self.assertTrue(failures, name + ' must be caught')
        # the superseded fix computes a wide score correctly and is caught by the stage-two word
        self.assertEqual(battery(data, with_posts(data.image, MUTANTS['superseded_two_nop'])), {'stage_two_stale', 'differential'})

    def test_composes_with_keen_eye_seam_in_either_order(self):
        """Disjoint windows in overlay 12: the two guarded transforms commute and each verifier accepts the result."""
        from . import modern_abilities as ka
        owned = 0x023DF000  # test-only address, never installed
        for language in V4:
            data = inputs(self, language)
            image = data.image
            mine_first, _ = ai.patch_overlay(image)
            both_ab, _ = ka.patch_overlay(mine_first, owned)
            keen_first, _ = ka.patch_overlay(image, owned)
            both_ba, _ = ai.patch_overlay(keen_first)
            self.assertEqual(both_ab, both_ba)
            diff = lambda x, y: {i for i in range(len(x)) if x[i] != y[i]}
            mine, keen = diff(image, mine_first), diff(image, keen_first)
            self.assertTrue(mine and keen)
            self.assertFalse(mine & keen, 'changed byte sets must be disjoint')
            self.assertEqual(diff(image, both_ab), mine | keen)
            window = range(ka.SITE - BASE, ka.SITE - BASE + 6)
            self.assertTrue(keen <= set(window))
            self.assertEqual(keen_first[window.start:window.stop], ka.seam_bytes(owned))
            self.assertEqual(diff(mine_first, both_ab), keen)  # Keen Eye alone on top of mine
            self.assertEqual(both_ab[window.start:window.stop], ka.seam_bytes(owned))
            # each logical verifier accepts the composed image against its own input
            ai.verify_images(image, mine_first)
            ai.verify_images(keen_first, both_ba)
            self.assertEqual(diff(keen_first, both_ba), mine)
            self.assertEqual(diff(mine_first, both_ab) - set(window), set())


if __name__ == '__main__':
    unittest.main()
